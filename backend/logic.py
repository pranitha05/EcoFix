def calculate_impact_and_recommendation(ai_result: dict) -> dict:
    """
    Takes raw AI output, evaluates the 5-R framework (Repair, Reuse, Resell, Recycle, Replace),
    and computes estimated financial & environmental savings.
    """
    item_name = ai_result.get("item_name", "Hardware Item")
    likely_fault = ai_result.get("likely_fault", "General component damage")
    confidence = ai_result.get("confidence", 0.85)

    repair_cost = float(ai_result.get("estimated_repair_cost", 1200))
    replace_cost = float(ai_result.get("estimated_replacement_cost", 5000))

    # Calculate financial savings (Cost difference between replacement and repair)
    money_saved = max(0.0, replace_cost - repair_cost)

    # Estimate e-waste saved (average device weight estimates in kg)
    category = ai_result.get("category", "electronics")
    ewaste_saved_kg = 0.5 if category == "electronics" else 1.2

    # Estimate carbon emissions prevented (approx. 20kg CO2e per kg of electronic waste extended)
    carbon_prevented_kg = round(ewaste_saved_kg * 20.0, 2)

    # Determine 5-R Actionable Guidance
    repair_viable = repair_cost < (replace_cost * 0.6)

    if repair_viable:
        rec_title = "RECOMMEND REPAIR"
        rec_text = f"Repairing costs ₹{repair_cost:,.0f}, saving you ₹{money_saved:,.0f} compared to buying a new unit."
    else:
        rec_title = "CONSIDER RECYCLING OR RESALE"
        rec_text = f"Repair cost (₹{repair_cost:,.0f}) is close to replacement cost (₹{replace_cost:,.0f}). Explore upcycling or component recycling."

    five_r = {
        "repair": f"Fix likely fault '{likely_fault}' at a local service center (~₹{repair_cost:,.0f}).",
        "reuse": f"Repurpose working components or chassis for secondary projects.",
        "resell": f"Sell 'as-is' or for parts on secondary markets (~₹{round(replace_cost * 0.15):,.0f}).",
        "recycle": f"Safely deposit unfixable boards at authorized e-waste collection points.",
        "replace": f"Buy new replacement unit (~₹{replace_cost:,.0f}). High environmental footprint."
    }

    return {
        "item_name": item_name,
        "likely_fault": likely_fault,
        "confidence": confidence,
        "recommendation_title": rec_title,
        "recommendation_text": rec_text,
        "estimated_repair_cost": f"₹{repair_cost:,.0f}",
        "estimated_replacement_cost": f"₹{replace_cost:,.0f}",
        "money_saved": f"₹{money_saved:,.0f}",
        "ewaste_saved": round(ewaste_saved_kg, 2),
        "carbon_prevented": carbon_prevented_kg,
        "five_r": five_r
    }