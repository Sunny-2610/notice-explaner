"""Closed vocabularies and verified numeric limits (LLD §§2, 6, 7).

Importing this module must never pull in infrastructure or third-party SDKs —
domain stays pure so escalation logic is unit-testable in isolation.
"""
from enum import Enum


class DocumentType(str, Enum):
    PROPERTY_TAX_NOTICE = "property_tax_notice"
    TRAFFIC_CHALLAN_SUMMONS = "traffic_challan_summons"
    BANK_RECOVERY_NOTICE = "bank_recovery_notice"
    UNSUPPORTED = "unsupported"


class JobStatus(str, Enum):
    QUEUED = "queued"
    EXTRACTING = "extracting"
    CLASSIFYING = "classifying"
    EXTRACTING_FIELDS = "extracting_fields"
    CHECKING_ESCALATION = "checking_escalation"
    GENERATING_EXPLANATION = "generating_explanation"
    AWAITING_REVIEW = "awaiting_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewReason(str, Enum):
    LOW_EXTRACTION_CONFIDENCE = "low_extraction_confidence"
    LOW_CLASSIFICATION_CONFIDENCE = "low_classification_confidence"
    ESCALATION_FLAG_SET = "escalation_flag_set"
    UNSUPPORTED_DOCUMENT_TYPE = "unsupported_document_type"


class ErrorCode(str, Enum):
    INVALID_FILE = "E-101"          # bad type/size -> HTTP 400
    UNSUPPORTED_LANGUAGE = "E-102"  # bad targetLanguage -> HTTP 400
    LOW_EXTRACTION = "E-150"        # routed to review, client sees 'under review'
    UNSUPPORTED_DOCUMENT = "E-201"  # 'not yet supported', no further processing
    AI_TIMEOUT = "E-301"            # retries exhausted -> job failed
    VOICE_UNAVAILABLE = "E-302"     # text-only fallback, not a failure
    ESCALATION_SET = "E-401"        # not an error; routes to review queue


class EscalationStage(str, Enum):
    PRE_EXPLANATION = "pre_explanation"
    POST_EXPLANATION = "post_explanation"


# Launch + English (config-only extension; reasoning and escalation logic unchanged).
SUPPORTED_LANGUAGES = ("hi", "mr", "en")

# LLD-verified numeric limits. Do not retune without updating docs.
EXTRACTION_CONFIDENCE_THRESHOLD = 0.55
CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.6
MAX_IMAGE_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_TYPES = ("image/jpeg", "image/png")
EXTRACTION_MAX_ATTEMPTS = 3
AI_MAX_ATTEMPTS = 3
RETRY_BACKOFF_BASE_MS = 500
RETRY_BACKOFF_CAP_MS = 4000
VISION_REASONING_TIMEOUT_S = 8
VOICE_TIMEOUT_S = 8
VOICE_TTS_TIMEOUT_S = 5  # LLD §7: 5s for voice calls (endpoint uses VOICE_TIMEOUT_S)

# Raw images are kept for reviewer context; deleted on completed/failed.
# (LLD §7 retention window — no fixed duration specified yet.)
RETAIN_IMAGE_FOR_REVIEW = True
