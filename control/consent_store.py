"""Store for user consent records."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ConsentRecord:
    """Record of user consent."""
    consent_id: str
    operation_type: str
    scope: str
    granted: bool
    granted_at: str
    expires_at: Optional[str] = None
    conditions: Optional[Dict] = None


class ConsentStore:
    """Persistent store for user consents."""
    
    def __init__(self, storage_path: Path):
        """Initialize consent store."""
        self.storage_path = storage_path
        self._consents: Dict[str, ConsentRecord] = {}
        self._load()
    
    def _load(self) -> None:
        """Load consents from file."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text())
                for cid, record in data.items():
                    self._consents[cid] = ConsentRecord(**record)
            except (json.JSONDecodeError, TypeError):
                self._consents = {}
    
    def _save(self) -> None:
        """Save consents to file."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {cid: asdict(record) for cid, record in self._consents.items()}
        self.storage_path.write_text(json.dumps(data, indent=2))
    
    def grant(
        self,
        consent_id: str,
        operation_type: str,
        scope: str,
        expires_at: Optional[datetime] = None,
        conditions: Optional[Dict] = None
    ) -> ConsentRecord:
        """Grant consent for an operation."""
        record = ConsentRecord(
            consent_id=consent_id,
            operation_type=operation_type,
            scope=scope,
            granted=True,
            granted_at=datetime.now().isoformat(),
            expires_at=expires_at.isoformat() if expires_at else None,
            conditions=conditions
        )
        
        self._consents[consent_id] = record
        self._save()
        return record
    
    def revoke(self, consent_id: str) -> bool:
        """Revoke a consent."""
        if consent_id in self._consents:
            del self._consents[consent_id]
            self._save()
            return True
        return False
    
    def check(self, operation_type: str, scope: str) -> bool:
        """Check if consent exists for operation."""
        now = datetime.now()
        
        for record in self._consents.values():
            if record.operation_type != operation_type:
                continue
            if record.scope != scope and record.scope != "*":
                continue
            if not record.granted:
                continue
            if record.expires_at:
                expires = datetime.fromisoformat(record.expires_at)
                if expires < now:
                    continue
            return True
        
        return False
    
    def list_consents(self) -> List[ConsentRecord]:
        """List all consents."""
        return list(self._consents.values())




