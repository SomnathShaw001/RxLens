from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import List
from app.core.database import get_db
from app.models.prescriptions import Prescription, PrescriptionField
from app.models.medications import Medication
from app.models.chat import ChatMessage
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.embeddings import get_text_embedding, _pgvector_available
from app.core.config import settings
import logging

try:
    from google import genai
    _genai_available = True
except ImportError:
    _genai_available = False

router = APIRouter()
logger = logging.getLogger(__name__)


async def _retrieve_similar_context(
    db: AsyncSession,
    prescription_id: str,
    query_embedding: list,
    limit: int = 5,
) -> List[str]:
    """
    RAG retrieval: finds semantically similar past messages using pgvector cosine distance.
    Falls back to plain text field retrieval when pgvector is not available.
    """
    context_lines = []

    if _pgvector_available and query_embedding:
        try:
            vec_str = "[" + ",".join(str(x) for x in query_embedding) + "]"
            similar_msgs = await db.execute(
                text(
                    "SELECT content FROM chat_messages "
                    "WHERE prescription_id = :pid AND embedding IS NOT NULL "
                    "ORDER BY embedding <=> CAST(:vec AS vector) "
                    "LIMIT :limit"
                ),
                {"pid": prescription_id, "vec": vec_str, "limit": limit},
            )
            for row in similar_msgs.fetchall():
                context_lines.append(f"[Related context]: {row[0]}")
        except Exception as e:
            logger.warning(f"pgvector search failed, falling back to plain text: {e}")

    # Always include current prescription fields as grounding
    fields_result = await db.execute(
        select(PrescriptionField).where(PrescriptionField.prescription_id == prescription_id)
    )
    fields = fields_result.scalars().all()
    for f in fields:
        if f.value:
            context_lines.append(f"Medication record: {f.value}")

    # Include medication summary
    meds_result = await db.execute(
        select(Medication).where(Medication.prescription_id == prescription_id)
    )
    meds = meds_result.scalars().all()
    for m in meds:
        parts = [m.drug_name]
        if m.strength:
            parts.append(m.strength)
        if m.frequency:
            parts.append(m.frequency)
        if m.duration:
            parts.append(f"for {m.duration}")
        context_lines.append("Medication: " + " ".join(parts))

    return context_lines


@router.post("", response_model=ChatResponse)
async def chat_prescription(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/chat
    Full RAG pipeline:
    1. Embed the user query.
    2. Retrieve semantically similar past context from pgvector.
    3. Ground generation with prescription fields and medication records.
    4. Generate answer with Gemini (with clinical disclaimer).
    5. Persist assistant message and trigger background embedding.
    """
    # Verify prescription exists
    rx_result = await db.execute(
        select(Prescription).where(Prescription.id == payload.prescription_id)
    )
    prescription = rx_result.scalar_one_or_none()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription {payload.prescription_id} not found"
        )

    # Step 1: Embed query for RAG retrieval
    query_embedding = await get_text_embedding(payload.message)

    # Step 2: RAG retrieval
    context_items = await _retrieve_similar_context(
        db, payload.prescription_id, query_embedding
    )
    context_str = "\n".join(context_items) if context_items else "No medication records found."

    # Step 3: Save user message
    user_msg = ChatMessage(
        prescription_id=payload.prescription_id,
        role="user",
        content=payload.message,
        embedding=query_embedding,
    )
    db.add(user_msg)
    await db.flush()

    # Step 4: Generate answer
    sources = ["Prescription Records", "Medication Database"]
    answer_text = ""

    api_key = settings.GEMINI_API_KEY
    if api_key and api_key != "your-gemini-api-key-here" and _genai_available:
        try:
            client = genai.Client(api_key=api_key)
            system_prompt = (
                "You are RxLens AI, a helpful medication information assistant embedded in a prescription management app. "
                "Your responses are grounded strictly on the patient's prescription records provided. "
                "STRICT RULES:\n"
                "1. Never suggest changing a dosage without doctor approval.\n"
                "2. Never diagnose conditions.\n"
                "3. Always recommend consulting a physician or pharmacist for clinical decisions.\n"
                "4. Always end your response with the mandatory disclaimer."
            )
            prompt = (
                f"PATIENT PRESCRIPTION CONTEXT:\n{context_str}\n\n"
                f"PATIENT QUESTION: {payload.message}\n\n"
                f"Answer based only on the above context. Be concise and helpful."
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config={"system_instruction": system_prompt, "temperature": 0.2},
            )
            answer_text = response.text
        except Exception as e:
            logger.error(f"Gemini chat generation failed: {e}")
            answer_text = _grounded_fallback(context_items)
    else:
        answer_text = _grounded_fallback(context_items)

    # Step 5: Persist assistant message with embedding
    answer_embedding = await get_text_embedding(answer_text)
    asst_msg = ChatMessage(
        prescription_id=payload.prescription_id,
        role="assistant",
        content=answer_text,
        embedding=answer_embedding,
    )
    db.add(asst_msg)
    await db.commit()

    # Dispatch background embedding task via Celery (optional, non-blocking)
    try:
        from app.workers.tasks import generate_embedding_task
        generate_embedding_task.delay(asst_msg.id, answer_text)
    except Exception:
        pass  # Celery not running in dev is fine

    disclaimer = (
        "⚠️ This information is for reference only and does not constitute medical advice. "
        "Always consult your doctor or registered pharmacist before making any changes to your medication."
    )
    return ChatResponse(answer=answer_text, sources=sources, disclaimer=disclaimer)


def _grounded_fallback(context_items: List[str]) -> str:
    if not context_items:
        return "No medication records found for this prescription. Please ingest a prescription first."
    meds = [c for c in context_items if c.startswith("Medication:")]
    if meds:
        return (
            f"Based on your prescription, the following medications are recorded:\n"
            + "\n".join(f"• {m.replace('Medication: ', '')}" for m in meds)
            + "\nPlease consult your pharmacist for specific dosage or timing queries."
        )
    return "Your prescription records have been stored. Please consult your pharmacist for clinical queries."
