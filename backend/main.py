import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

import ai
import logic
import database
import places

# Load environment variables
load_dotenv()

app = FastAPI(
    title="EcoFix API & App",
    description="AI-powered repair-vs-replace diagnostics and sustainability tracking",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to frontend directory (one level up from backend)
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))

@app.on_event("startup")
def on_startup():
    database.init_db()

# API Endpoints MUST come before static files mounting
@app.post("/api/diagnose")
async def run_diagnosis(
    image: UploadFile = File(...),
    description: str = Form("")
):
    try:
        image_bytes = await image.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Empty image uploaded.")

        ai_result = ai.analyze_fault(image_bytes=image_bytes, description=description)
        processed_data = logic.calculate_impact_and_recommendation(ai_result)

        assessment_id = f"#EF-{uuid.uuid4().hex[:4].upper()}"
        record = {
            "id": assessment_id,
            "item_name": processed_data.get("item_name", "Unknown Item"),
            "fault": processed_data.get("likely_fault", "Unspecified Fault"),
            "confidence": processed_data.get("confidence", 0.90),
            "recommendation_title": processed_data.get("recommendation_title"),
            "recommendation_text": processed_data.get("recommendation_text"),
            "estimated_repair_cost": processed_data.get("estimated_repair_cost"),
            "estimated_replacement_cost": processed_data.get("estimated_replacement_cost"),
            "money_saved": processed_data.get("money_saved", "0"),
            "ewaste_saved": processed_data.get("ewaste_saved", 0.0),
            "carbon_prevented": processed_data.get("carbon_prevented", 0.0),
            "status": "ASSESSED",
            "five_r": processed_data.get("five_r", {})
        }

        database.save_assessment(record)

        record["assessment_id"] = assessment_id
        return record

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic error: {str(e)}")


@app.get("/api/dashboard")
def get_dashboard_metrics():
    return database.get_user_statistics()


@app.get("/api/shops")
def get_nearby_shops(lat: float = 12.9716, lng: float = 77.5946):
    return places.get_nearby_repair_shops(lat, lng)


@app.get("/api/history")
def get_assessment_history():
    return database.get_recent_assessments()


# Mount Static Files directly at root (serves index.html automatically and resolves style.css directly)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run("main:app", host=host, port=port, reload=True)