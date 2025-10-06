#db/databse.py

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "pyrometer.db")

class Database:
    """Class to handle database connection."""
    def __init__(self, db_file = DB_FILE):
        
        self.db_file = db_file
        self._ensure_tables()
    
    def get_connection(self):
        return sqlite3.connect(self.db_file)
    
    def _ensure_tables(self):
        """Create all tables if they don't exist."""
        conn = self.get_connection()
        cur = conn.cursor() #let us send the sql commands

        # Device configurations
        cur.execute("""
        CREATE TABLE IF NOT EXISTS device_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_name TEXT NOT NULL,
            device_id INTEGER NOT NULL,
            baud_rate INTEGER NOT NULL,
            com_port TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
        """)

        # Device readings
        cur.execute("""
        CREATE TABLE IF NOT EXISTS device_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            ts_utc TEXT NOT NULL,
            value REAL,
            status TEXT,
            raw_hex TEXT,
            FOREIGN KEY (device_id) REFERENCES device_config(device_id)
        )
        """)

        conn.commit() #saves the changes 
        conn.close() #closes file safely

class DeviceConfigDB(Database):
    """CRUD operations for device_config table."""

    def add(self, name, device_id, baud_rate, com_port, enabled=True):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO device_config (device_name, device_id, baud_rate, com_port, enabled)
            VALUES (?, ?, ?, ?, ?)
        """, (name, device_id, baud_rate, com_port, 1 if enabled else 0))
        conn.commit()
        conn.close()

    def get_all(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM device_config")
        rows = cur.fetchall()
        conn.close()
        return rows

    def clear(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM device_config")
        conn.commit()
        conn.close()


class DeviceReadingsDB(Database):
    """CRUD operations for device_readings table."""

    def add(self, device_id, ts_utc, value, status, raw_hex):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO device_readings (device_id, ts_utc, value, status, raw_hex)
            VALUES (?, ?, ?, ?, ?)
        """, (device_id, ts_utc, value, status, raw_hex))
        conn.commit()
        conn.close()

    def get_latest_for_device(self, device_id, limit=10):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT ts_utc, value, status FROM device_readings
            WHERE device_id = ?
            ORDER BY ts_utc DESC
            LIMIT ?
        """, (device_id, limit))
        rows = cur.fetchall()
        conn.close()
        return rows