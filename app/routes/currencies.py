from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/currencies")


@router.get("/rates")
async def get_exchange_rate(
    base: str = Query(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
    quote: str = Query(min_length=3, max_length=3, pattern=r"^[A-Za-z]{3}$"),
) -> dict:
    base_code = base.upper()
    quote_code = quote.upper()
    if base_code == quote_code:
        return {"base": base_code, "quote": quote_code, "rate": 1.0, "fetched_at": datetime.now(timezone.utc)}

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(f"https://open.er-api.com/v6/latest/{base_code}")
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Exchange rates are temporarily unavailable") from exc

    rate = payload.get("rates", {}).get(quote_code)
    if payload.get("result") != "success" or not isinstance(rate, (int, float)):
        raise HTTPException(status_code=422, detail="Unsupported currency code")
    return {
        "base": base_code,
        "quote": quote_code,
        "rate": rate,
        "fetched_at": payload.get("time_last_update_utc") or datetime.now(timezone.utc),
    }