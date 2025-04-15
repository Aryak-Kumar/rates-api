from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path
from models import LoanDetails
from pydantic import ValidationError
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SOFR Rate Calculator API")

DB_FILE = Path("../data/rates.db")

def get_sofr_rates(start_date: str, end_date: str):
    """Fetch SOFR rates from the database for the given date range."""
    logger.info(f"Fetching SOFR rates from {start_date} to {end_date}")
    logger.info(f"Database path: {DB_FILE.resolve()}")
    try:
        conn = sqlite3.connect(DB_FILE)
        query = "SELECT date, rate FROM sofr_rates WHERE date >= ? AND date <= ?"
        logger.info(f"Executing query: {query} with params ({start_date}, {end_date})")
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        conn.close()
        logger.info(f"Query returned {len(df)} rows")
        if df.empty:
            logger.warning("No rates found for the given range")
            raise ValueError("No rates found for the given range")
        rates_dict = df.set_index("date")["rate"].to_dict()
        logger.info(f"Rates dictionary: {rates_dict}")
        return rates_dict
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/calculate-rates", response_description="Monthly dates and calculated rates")
def calculate_rates(loan: dict):
    """Calculate projected interest rates based on loan details."""
    logger.info(f"Received raw input: {loan}")
    try:
        loan_details = LoanDetails(**loan)
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=422, detail=e.errors())
    logger.info(f"Validated loan details: {loan_details}")
    
    today = datetime.today().date()
    maturity_date = loan_details.maturity_date
    logger.info(f"Today: {today}, Maturity date: {maturity_date}")
    
    if maturity_date <= today:
        logger.error("Maturity date is not in the future")
        raise HTTPException(status_code=422, detail="Maturity date must be in the future")
    
    # Generate monthly dates
    dates = pd.date_range(start=today, end=maturity_date, freq="MS").strftime("%Y-%m-%d").tolist()
    logger.info(f"Generated monthly dates: {dates}")
    
    # Set start_date to the first day of the current month
    start_date = today.replace(day=1).strftime("%Y-%m-%d")
    end_date = maturity_date.strftime("%Y-%m-%d")
    logger.info(f"Fetching rates from {start_date} to {end_date}")
    rates_dict = get_sofr_rates(start_date, end_date)
    
    # Create a sorted DataFrame for rates
    rates_df = pd.DataFrame(list(rates_dict.items()), columns=["date", "rate"])
    rates_df["date"] = pd.to_datetime(rates_df["date"])
    rates_df = rates_df.sort_values("date").set_index("date")
    
    # Forward-fill and back-fill rates for all dates
    all_dates = pd.date_range(start=start_date, end=end_date, freq="D")
    df_rates = pd.DataFrame(index=all_dates)
    df_rates["rate"] = rates_df["rate"].reindex(all_dates).ffill().bfill()
    df_rates.index = df_rates.index.strftime("%Y-%m-%d")
    logger.info(f"df_rates after fill (first 5 rows):\n{df_rates.head().to_string()}")
    
    # Select monthly rates
    monthly_rates = df_rates.loc[dates]["rate"].to_dict()
    logger.info(f"Monthly rates: {monthly_rates}")
    
    # Calculate final rates
    result = []
    for date_str, sofr_rate in monthly_rates.items():
        logger.info(f"Processing date {date_str}: SOFR rate = {sofr_rate}")
        if pd.isna(sofr_rate):
            logger.error(f"No SOFR rate for {date_str}")
            raise HTTPException(status_code=404, detail=f"No SOFR rate for {date_str}")
        final_rate = sofr_rate + loan_details.rate_spread
        final_rate = max(loan_details.rate_floor, min(loan_details.rate_ceiling, final_rate))
        logger.info(f"Calculated final rate for {date_str}: {final_rate}")
        result.append({"date": date_str, "rate": final_rate})
    
    logger.info(f"Returning result: {result}")
    return result