"""Importa todos los modelos para que Alembic los vea."""

from app.models.agent import Approval, Recipe, ScheduledJob
from app.models.audit import AuditEvent
from app.models.auth import AuthToken, UserSession
from app.models.base import Base
from app.models.billing import Plan, PlanFeature, Subscription, UsageEvent
from app.models.channels import Channel, MessageTemplate
from app.models.conversations import Contact, Conversation, Message
from app.models.knowledge import Document, DocumentChunk
from app.models.tenancy import Membership, Role, RolePermission, Tenant, User

TENANT_SCOPED_TABLES = [
    "memberships",
    "channels",
    "message_templates",
    "contacts",
    "conversations",
    "messages",
    "documents",
    "document_chunks",
    "recipes",
    "scheduled_jobs",
    "approvals",
    "subscriptions",
    "usage_events",
    "audit_events",
]

__all__ = [
    "TENANT_SCOPED_TABLES",
    "Approval",
    "AuditEvent",
    "AuthToken",
    "Base",
    "Channel",
    "Contact",
    "Conversation",
    "Document",
    "DocumentChunk",
    "Membership",
    "Message",
    "MessageTemplate",
    "Plan",
    "PlanFeature",
    "Recipe",
    "Role",
    "RolePermission",
    "ScheduledJob",
    "Subscription",
    "Tenant",
    "UsageEvent",
    "User",
    "UserSession",
]
