"""SQLite state store."""

import sqlite3
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from .mission_state import MissionState, MissionStatus
from .step_state import StepState, StepStatus


class SQLiteStateStore:
    """SQLite-based state store."""
    
    def __init__(self, db_path: Path):
        """Initialize state store."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS missions (
                mission_id TEXT PRIMARY KEY,
                status TEXT,
                description TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                total_steps INTEGER,
                completed_steps INTEGER,
                error TEXT,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS steps (
                step_id TEXT,
                mission_id TEXT,
                status TEXT,
                step_type TEXT,
                description TEXT,
                started_at TEXT,
                completed_at TEXT,
                error TEXT,
                inputs TEXT,
                outputs TEXT,
                PRIMARY KEY (step_id, mission_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_mission(self, mission: MissionState):
        """Save mission state."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO missions
            (mission_id, status, description, created_at, started_at, completed_at,
             total_steps, completed_steps, error, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            mission.mission_id,
            mission.status.value,
            mission.description,
            mission.created_at.isoformat() if mission.created_at else None,
            mission.started_at.isoformat() if mission.started_at else None,
            mission.completed_at.isoformat() if mission.completed_at else None,
            mission.total_steps,
            mission.completed_steps,
            mission.error,
            json.dumps(mission.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def load_mission(self, mission_id: str) -> Optional[MissionState]:
        """Load mission state."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM missions WHERE mission_id = ?", (mission_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return MissionState(
            mission_id=row[0],
            status=MissionStatus(row[1]),
            description=row[2],
            created_at=datetime.fromisoformat(row[3]) if row[3] else datetime.utcnow(),
            started_at=datetime.fromisoformat(row[4]) if row[4] else None,
            completed_at=datetime.fromisoformat(row[5]) if row[5] else None,
            total_steps=row[6] or 0,
            completed_steps=row[7] or 0,
            error=row[8],
            metadata=json.loads(row[9]) if row[9] else {}
        )
    
    def save_step(self, step: StepState):
        """Save step state."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO steps
            (step_id, mission_id, status, step_type, description, started_at,
             completed_at, error, inputs, outputs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            step.step_id,
            step.mission_id,
            step.status.value,
            step.step_type,
            step.description,
            step.started_at.isoformat() if step.started_at else None,
            step.completed_at.isoformat() if step.completed_at else None,
            step.error,
            json.dumps(step.inputs),
            json.dumps(step.outputs)
        ))
        
        conn.commit()
        conn.close()
    
    def list_missions(self) -> List[str]:
        """List all mission IDs."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT mission_id FROM missions")
        rows = cursor.fetchall()
        conn.close()
        
        return [row[0] for row in rows]


