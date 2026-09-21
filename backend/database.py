import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(__file__), "ecofix.db")

def get_connection():
    """Returns a SQLite connection with dict-like row output."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database schema if tables do not exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            item_name TEXT,
            fault TEXT,
            confidence REAL,
            recommendation_title TEXT,
            recommendation_text TEXT,
            estimated_repair_cost TEXT,
            estimated_replacement_cost TEXT,
            money_saved REAL,
            ewaste_saved REAL,
            carbon_prevented REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_assessment(data: dict):
    """Saves a new assessment record into the database."""
    conn = get_connection()
    cursor = conn.cursor()

    # Clean money string to store as float for aggregation
    raw_saved = str(data.get("money_saved", "0")).replace("₹", "").replace(",", "").strip()
    try:
        money_saved_val = float(raw_saved)
    except ValueError:
        money_saved_val = 0.0

    cursor.execute("""
        INSERT INTO assessments (
            id, item_name, fault, confidence, recommendation_title,
            recommendation_text, estimated_repair_cost, estimated_replacement_cost,
            money_saved, ewaste_saved, carbon_prevented, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("id"),
        data.get("item_name"),
        data.get("fault"),
        data.get("confidence"),
        data.get("recommendation_title"),
        data.get("recommendation_text"),
        data.get("estimated_repair_cost"),
        data.get("estimated_replacement_cost"),
        money_saved_val,
        float(data.get("ewaste_saved", 0.0)),
        float(data.get("carbon_prevented", 0.0)),
        data.get("status", "ASSESSED")
    ))

    conn.commit()
    conn.close()

def get_recent_assessments(limit: int = 5) -> list:
    """Retrieves the most recent assessment logs."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, item_name, fault, status, recommendation_title
        FROM assessments
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    result = []
    for row in rows:
        result.append({
            "id": row["id"],
            "item_name": row["item_name"],
            "fault": row["fault"],
            "status": row["status"],
            "status_type": "success" if "REPAIR" in str(row["recommendation_title"]) else "info"
        })
    return result

def get_user_statistics() -> dict:
    """Calculates aggregated metrics across all assessments."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_count,
            COALESCE(SUM(money_saved), 0) as total_money,
            COALESCE(SUM(carbon_prevented), 0) as total_carbon,
            COALESCE(SUM(ewaste_saved), 0) as total_ewaste
        FROM assessments
    """)

    row = cursor.fetchone()
    conn.close()

    total_count = row["total_count"]
    success_rate = "100%" if total_count > 0 else "0%"

    return {
        "money_saved": f"₹{row['total_money']:,.0f}",
        "carbon_prevented": f"{row['total_carbon']:.1f} kg CO2e",
        "ewaste_saved": f"{row['total_ewaste']:.1f} kg",
        "success_rate": success_rate
    }