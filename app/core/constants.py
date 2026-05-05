from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class DocumentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class ErrorMessages:
    # Auth
    INVALID_CREDENTIALS = "Invalid email or password"
    EMAIL_ALREADY_EXISTS = "An account with this email already exists"
    INACTIVE_USER = "This account has been deactivated"
    INVALID_TOKEN = "Invalid or expired token"
    INSUFFICIENT_PERMISSIONS = "You do not have permission to perform this action"
    GOOGLE_AUTH_FAILED = "Google authentication failed"

    # Group
    GROUP_NOT_FOUND = "Group not found"
    GROUP_ACCESS_DENIED = "You do not have access to this group"

    # Document
    DOCUMENT_NOT_FOUND = "Document not found"
    DOCUMENT_LIMIT_EXCEEDED = "Maximum document limit reached for this group"
    UNSUPPORTED_FILE_TYPE = "File type not supported. Allowed types: PDF, TXT, DOCX"
    FILE_TOO_LARGE = "File size exceeds the maximum allowed limit"
    DOCUMENT_NOT_READY = "Document is still being processed. Please wait."

    # Chat
    NO_DOCUMENTS_IN_GROUP = "No documents found in this group. Please upload documents first."
    CHAT_FAILED = "Failed to generate an answer. Please try again."

    # General
    NOT_FOUND = "Resource not found"
    INTERNAL_ERROR = "An internal error occurred"


class SuccessMessages:
    GROUP_CREATED = "Group created successfully"
    GROUP_DELETED = "Group deleted successfully"
    DOCUMENT_UPLOADED = "Document uploaded and is being processed"
    DOCUMENT_DELETED = "Document deleted successfully"
    LOGOUT_SUCCESS = "Logged out successfully"


RAG_SYSTEM_PROMPT = """You are a helpful AI assistant. Answer the user's question based ONLY on the provided context from their documents.

Rules:
- Only use information from the provided context
- If the context doesn't contain enough information, clearly say so
- Be concise and accurate
- Cite which document the information came from when possible
- Do not make up information"""

RAG_USER_PROMPT_TEMPLATE = """Context from documents:
{context}

Question: {question}

Please answer based on the context above."""
