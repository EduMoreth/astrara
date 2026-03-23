import json
from fastapi import APIRouter, HTTPException
from models.chart import ChartRequest
from services.astro_service import generate_chart
from services.geocoding_service import geocode

router = APIRouter(prefix="/chart", tags=["chart"])


@router.post("/generate")
async def generate(data: ChartRequest):
    try:
        coords = geocode(data.city, data.country)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = generate_chart(
            data.name,
            data.year,
            data.month,
            data.day,
            data.hour,
            data.minute,
            coords["lat"],
            coords["lng"],
            coords["tz_str"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao calcular o mapa astral: {str(e)}",
        )

    return {
        "positions": result["positions"],
        "houses": result["houses"],
        "aspects": result.get("aspects", []),
        "location": {
            "lat": coords["lat"],
            "lng": coords["lng"],
            "tz_str": coords["tz_str"],
            "display_name": coords.get("display_name", ""),
        },
    }
