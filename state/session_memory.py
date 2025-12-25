"""Session memory for chat history."""

import sqlite3
from typing import List, Dict
from datetime import datetime
from pathlib import Path
from state.state_store_sqlite import SQLiteStateStore


class SessionMemory:
    """Manages chat session history per mission."""
    
    def __init__(self, state_store: SQLiteStateStore, mission_id: str):
        """
        Initialize session memory.
        
        Args:
            state_store: State store instance
            mission_id: Mission identifier
        """
        self.state_store = state_store
        self.mission_id = mission_id
        self.db_path = state_store.db_path
        self._init_table()
    
    def _get_conn(self):
        """Get a database connection."""
        return sqlite3.connect(str(self.db_path))
    
    def _init_table(self):
        """Initialize session_history table."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mission_id TEXT NOT NULL,
                turn_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_query TEXT NOT NULL,
                ai_response TEXT NOT NULL
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_mission_id ON session_history(mission_id)")
        conn.commit()
        conn.close()
    
    def add_turn(self, user_query: str, ai_response: str):
        """
        Add a chat turn to history.
        
        Args:
            user_query: User's query
            ai_response: AI's response
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO session_history (mission_id, user_query, ai_response) VALUES (?, ?, ?)",
            (self.mission_id, user_query, ai_response)
        )
        conn.commit()
        conn.close()
    
    def get_last_n(self, n: int) -> List[Dict[str, str]]:
        """
        Get last N chat turns.
        
        Args:
            n: Number of turns to retrieve
            
        Returns:
            List of turn dictionaries
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_query, ai_response FROM session_history WHERE mission_id = ? ORDER BY turn_timestamp DESC LIMIT ?",
            (self.mission_id, n)
        )
        rows = cursor.fetchall()
        conn.close()
        # Reverse to get chronological order
        return [{"user": row[0], "ai": row[1]} for row in reversed(rows)]
    
    def clear(self):
        """Clear history for this mission."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM session_history WHERE mission_id = ?",
            (self.mission_id,)
        )
        conn.commit()
        conn.close()

