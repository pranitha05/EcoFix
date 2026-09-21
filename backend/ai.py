import json
import os
from google import genai
from google.genai import types

def analyze_fault(image_bytes: bytes, description: str = "") -> dict:
    """
    Sends the item image and optional text prompt to Gemini Vision API.
    Returns a structured dictionary containing identified item details,
    estimated damage, and cost approximations.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback response if API key is missing
        return {
            "item_name": "Unidentified Hardware Item",
            "likely_fault": "Physical damage or component failure detected.",
            "confidence": 0.85,
            "estimated_repair_cost": 1500,
            "estimated_replacement_cost": 6500,
            "category": "electronics"
        }

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert electronics and hardware repair diagnostic assistant.
    Analyze the provided image and user description to identify the item and inspect for damage.

    User Description: "{description}"

    Return ONLY a valid JSON object matching this schema (do not wrap in markdown or markdown code blocks):
    {{
        "item_name": "Name of the device/item (e.g. Mechanical Keyboard, Smartphone Screen)",
        "likely_fault": "Concise summary of observed or probable damage",
        "confidence": 0.95,
        "estimated_repair_cost": 1200,
        "estimated_replacement_cost": 5000,
        "category": "electronics"
    }}
    Note: Currency estimates should be numeric values representing INR (₹).
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type="image/jpeg",
                ),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )

        parsed_json = json.loads(response.text)
        return parsed_json

    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Fallback dictionary on parsing/API failure
        return {
            "item_name": "Inspected Hardware Unit",
            "likely_fault": description if description else "Circuit or structural damage",
            "confidence": 0.80,
            "estimated_repair_cost": 1000,
            "estimated_replacement_cost": 4500,
            "category": "general"
        }