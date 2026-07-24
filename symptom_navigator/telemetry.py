import os
import re
import json
import logging
import time
import functools
from typing import Any, Dict, Callable
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# ==========================================
# 1. PII Redaction Pipeline (Scrubber)
# ==========================================
class PIIScrubber:
    """Scrubs sensitive Personally Identifiable Information (PII) and PHI from logs and memory."""
    
    # Patterns for CPF, Email, Phone Number, Credit Card
    CPF_PATTERN = re.compile(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}\b')
    CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d[ -]*?){13,16}\b')

    @classmethod
    def redact(cls, text: str) -> str:
        if not isinstance(text, str):
            text = str(text)
        text = cls.CPF_PATTERN.sub("[REDACTED_CPF]", text)
        text = cls.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)
        text = cls.CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", text)
        return text

    @classmethod
    def redact_dict(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redact strings within a dictionary."""
        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = cls.redact(value)
            elif isinstance(value, dict):
                cleaned[key] = cls.redact_dict(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    cls.redact_dict(item) if isinstance(item, dict)
                    else cls.redact(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        return cleaned


# ==========================================
# 2. Structured JSON Logging
# ==========================================
class JSONFormatter(logging.Formatter):
    """Formats python log records into structured JSON strings with metadata."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": PIIScrubber.redact(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if hasattr(record, "intent_data"):
            log_obj["intent"] = PIIScrubber.redact_dict(getattr(record, "intent_data"))
        if hasattr(record, "outcome_data"):
            log_obj["outcome"] = PIIScrubber.redact_dict(getattr(record, "outcome_data"))
        if hasattr(record, "trace_id"):
            log_obj["trace_id"] = getattr(record, "trace_id")
            
        return json.dumps(log_obj, ensure_ascii=False)


def setup_logger(name: str = "symptom_navigator") -> logging.Logger:
    """Configures structured JSON logger for the agent."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger

logger = setup_logger()


# ==========================================
# 3. Intent vs Outcome Capture Decorator
# ==========================================
def log_intent_and_outcome(tool_name: str):
    """Decorator to explicitly log the agent's INTENT before execution and OUTCOME after."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            intent_info = {
                "action": tool_name,
                "input_args": kwargs if kwargs else (args[0] if args else {})
            }
            logger.info(
                f"[INTENT] Executing tool '{tool_name}'",
                extra={"intent_data": intent_info}
            )
            
            try:
                result = func(*args, **kwargs)
                duration_ms = round((time.time() - start_time) * 1000, 2)
                outcome_info = {
                    "action": tool_name,
                    "status": "success",
                    "duration_ms": duration_ms,
                    "result": result
                }
                logger.info(
                    f"[OUTCOME] Tool '{tool_name}' completed successfully in {duration_ms}ms",
                    extra={"outcome_data": outcome_info}
                )
                return result
            except Exception as e:
                duration_ms = round((time.time() - start_time) * 1000, 2)
                outcome_info = {
                    "action": tool_name,
                    "status": "error",
                    "duration_ms": duration_ms,
                    "error_message": str(e)
                }
                logger.error(
                    f"[OUTCOME] Tool '{tool_name}' failed after {duration_ms}ms: {str(e)}",
                    extra={"outcome_data": outcome_info}
                )
                raise e
        return wrapper
    return decorator


# ==========================================
# 4. OpenTelemetry Distributed Tracing
# ==========================================
def init_tracer(service_name: str = "symptom-navigator-agent") -> trace.Tracer:
    """Initializes OpenTelemetry distributed tracer provider."""
    provider = TracerProvider()
    processor = BatchSpanProcessor(ConsoleSpanExporter())
    provider.add_span_processor(processor)
    trace.set_tracer_provider(provider)
    return trace.get_tracer(service_name)

tracer = init_tracer()
