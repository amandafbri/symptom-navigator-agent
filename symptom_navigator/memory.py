import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from .database import db
from .telemetry import logger, PIIScrubber

class ContextCompactor:
    """Manages history compaction and context window bloat truncation for conversational state."""

    def __init__(self, max_tokens_estimate: int = 2000, max_turns: int = 10):
        self.max_tokens_estimate = max_tokens_estimate
        self.max_turns = max_turns

    def compact_history(self, history_turns: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Compact conversation history by sliding window and summarizing older turns if bloat occurs."""
        if len(history_turns) <= self.max_turns:
            return history_turns

        # Keep recent turns intact, summarize earlier turns
        recent_turns = history_turns[-self.max_turns:]
        older_turns = history_turns[:-self.max_turns]
        
        summary_snippets = []
        for turn in older_turns:
            role = turn.get("role", "user")
            content = turn.get("content", "")
            summary_snippets.append(f"{role}: {content[:50]}...")
            
        compacted_summary = {
            "role": "system",
            "content": f"[HISTÓRICO COMPACTADO]: {'; '.join(summary_snippets)}"
        }
        
        logger.info(f"[COMPACTION] Compacted {len(older_turns)} older turns into context summary.")
        return [compacted_summary] + recent_turns


class AsyncMemoryManager:
    """Handles asynchronous memory operations to consolidate session data without UI blocking."""

    @staticmethod
    async def consolidate_session_memory_async(session_id: str, patient_id: Optional[str], current_step: str, metadata: Dict[str, Any]):
        """Runs background task to scrub PII and save session state to persistent store asynchronously."""
        try:
            # Simulate async processing (e.g. background consolidation / vector store index update)
            await asyncio.sleep(0.01)
            
            # Redact PII before persistence
            cleaned_metadata = PIIScrubber.redact_dict(metadata)
            
            db.save_session_state(
                session_id=session_id,
                patient_id=patient_id,
                current_step=current_step,
                metadata=cleaned_metadata
            )
            logger.info(f"[ASYNC_MEMORY] Consolidated session '{session_id}' in background task.")
        except Exception as e:
            logger.error(f"[ASYNC_MEMORY_ERROR] Failed async consolidation: {str(e)}")


memory_manager = AsyncMemoryManager()
compactor = ContextCompactor()
