from pydantic import BaseModel, Field
from datetime import date

class LoanDetails(BaseModel):
    maturity_date: date
    reference_rate: str = Field(..., pattern="^SOFR$", description="Must be 'SOFR'")
    rate_floor: float = Field(..., ge=0, description="Minimum allowable rate")
    rate_ceiling: float = Field(..., ge=0, description="Maximum allowable rate")
    rate_spread: float = Field(..., ge=0, description="Spread added to SOFR rate")
    
    class Config:
        schema_extra = {
            "example": {
                "maturity_date": "2025-12-01",
                "reference_rate": "SOFR",
                "rate_floor": 0.02,
                "rate_ceiling": 0.10,
                "rate_spread": 0.02
            }
        }