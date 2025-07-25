from uuid import uuid4
from typing import List

from sqlalchemy import Column, String, Index

from .base import Base
from .mcp import JSONList  # Re-use existing JSONList type for lists stored as JSON


class Agent(Base):
    """Model representing an agent identity (client credentials + capability scoping).

    This table is the foundation for an "Agentic Identity" compatible with the
    OIDC-A proposal.  Each row maps a generated client_id / client_secret pair
    to a bounded set of capability IDs (tools, resources, prompts).
    """

    __tablename__ = "agents"

    # Primary key (internal identifier)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))

    # OAuth-style credentials --------------------------------------------------
    client_id = Column(String(48), unique=True, nullable=False, index=True)
    # Store a *hash* of the secret – never store plaintext.
    client_secret_hash = Column(String(128), nullable=False)

    # Human-readable meta -------------------------------------------------------
    name = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)

    # Capability scoping -------------------------------------------------------
    allowed_tool_ids = Column(JSONList, nullable=False, default=list)
    allowed_resource_ids = Column(JSONList, nullable=False, default=list)
    allowed_prompt_ids = Column(JSONList, nullable=False, default=list)

    # Indexes for efficient lookup
    __table_args__ = (
        Index("idx_agents_client_id", "client_id"),
    )

    # ---------------------------------------------------------------------
    def verify_secret(self, plaintext: str) -> bool:
        """Return True if *plaintext* matches the stored secret hash."""
        import hashlib, hmac

        candidate = hashlib.sha256(plaintext.encode()).hexdigest()
        return hmac.compare_digest(candidate, self.client_secret_hash)

    # Convenience helpers --------------------------------------------------
    @property
    def tools(self) -> List[str]:
        return self.allowed_tool_ids or []

    @property
    def resources(self) -> List[str]:
        return self.allowed_resource_ids or []

    @property
    def prompts(self) -> List[str]:
        return self.allowed_prompt_ids or []

    # ---------------------------------------------------------------------
    def __repr__(self) -> str:  # pragma: no cover
        return f"<Agent(id='{self.id}', client_id='{self.client_id}', name='{self.name}')>" 