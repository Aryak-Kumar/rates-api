from fastapi import FastAPI, HTTPException
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path
from models import LoanDetails
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
    logger.info(f"Fetching SOFR rates from {start_date} to {end_date} from {DB_FILE.resolve()}")
    try:
        conn = sqlite3.connect(DB_FILE) # Initiate the connection
        query = "SELECT date, rate FROM sofr_rates WHERE date >= ? AND date <= ?"
        df = pd.read_sql_query(query, conn, params=(start_date, end_date)) # Run query with the parameters on the connection DB
        conn.close()
        logger.info(f"Query returned {len(df)} rows")
        if df.empty:
            raise ValueError("No rates found for the given range")
        df["date"] = pd.to_datetime(df["date"]) # Create a dataframe for the dates 
        df = df.sort_values("date").set_index("date") # Sort the dates 
        logger.info(f"Rates dictionary: {df.to_dict()['rate']}")
        return df
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}") # Raise error for Database error
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) # Raise error for Value Errors

@app.post("/calculate-rates", response_description="Reset dates and calculated rates")
async def calculate_rates(loan: LoanDetails):
    logger.info(f"Loan details: {loan}")
    
    today = datetime.today().date()
    maturity_date = loan.maturity_date
    logger.info(f"Today: {today}, Maturity date: {maturity_date}") # Log the dates for today and the maturity date provided
    
    if maturity_date <= today: # Raise Error if the Maturity date is before today
        raise HTTPException(status_code=422, detail="Maturity date must be in the future")
    
    start_date = today.replace(day=1).strftime("%Y-%m-%d") # Get the start Date
    end_date = maturity_date.strftime("%Y-%m-%d") # Get the maturity Date
    logger.info(f"Fetching rates from {start_date} to {end_date}")
    rates_df = get_sofr_rates(start_date, end_date) # Get the SOFR rates between the Dates
    
    reset_dates = rates_df.index.strftime("%Y-%m-%d").tolist() # Get the reset Dates 
    logger.info(f"Reset dates: {reset_dates}")
    
    reset_dates = [d for d in reset_dates if today.replace(day=1) <= pd.to_datetime(d).date() <= maturity_date]
    if not reset_dates:
        logger.error("No reset dates found within loan term")
        raise HTTPException(status_code=404, detail="No reset dates found within loan term")
    
    result = []
    for date_str in reset_dates:
        sofr_rate = rates_df.loc[date_str, "rate"]
        logger.info(f"Processing date {date_str}: SOFR rate = {sofr_rate}")
        final_rate = sofr_rate + loan.rate_spread 
        final_rate = max(loan.rate_floor, min(loan.rate_ceiling, final_rate)) # Calculate the final rate with parameters
        logger.info(f"Calculated final rate for {date_str}: {final_rate}")
        result.append({"date": date_str, "rate": final_rate}) # Append the Date and Rate in the Result
    
    logger.info(f"Returning result: {result}")
    return result