
# SOFR Rate Calculator API

This project implements a FastAPI-based API to calculate monthly SOFR-based loan rates using data from a local SQLite database (`rates.db`), which is updated by an ETL pipeline (`etl.py`), retrieving data from Pensford. The `/calculate-rates` endpoint accepts loan details (maturity date, reference rate, rate floor, ceiling, and spread) and returns rates for monthly reset dates.

## Prerequisites
- **Python**: 3.11+
- **Dependencies**: Listed in `api/requirements.txt` and `rates-api/requirements.txt`
- **Database**: `data/rates.db` (populated via `etl.py`)

## How to Run the Solution

### 1. Clone the Repository
```bash
git clone https://github.com/Aryak-Kumar/rates-api.git
cd rates-api
```

### 2. Install Dependencies
Install required packages for the ETL pipeline and API:
```bash
cd rates-api
pip install -r requirements.txt
cd ../api
pip install -r requirements.txt
```

### 3. Populate the Database
Run the ETL script to download and process the latest SOFR rates:
```bash
cd ../rates-api
python etl.py
```

### 4. Run the API Locally
Start the FastAPI server:
```bash
cd ../api
uvicorn main:app --reload
```
The API will be available at `http://localhost:8000`. 

### 6. Test the API
Use Postman or `curl` to test the `/calculate-rates` endpoint. Example:
```bash
curl -X POST "http://localhost:8000/calculate-rates" -H "Content-Type: application/json" -d '{"maturity_date": "2026-12-31", "reference_rate": "SOFR", "rate_floor": 0.02, "rate_ceiling": 0.10, "rate_spread": 0.02}'
```

## Time Spent
I spent approximately **4.5 hours** on this project, including:
- Analyzing Pensford’s website, confirm data availability, and creating the outline for the project (~15-20 minutes).
- Implement and test the ETL script, ensuring data is correctly extracted and stored. (~1.5 hour).
- Build the FastAPI service, including endpoint, validation, and rate calculation logic. (~1.5 hours).
- Write unit tests for the API and verify edge cases. (~1 hour).
- Write README, polish code, and push to GitHub. (~15-20 minutes).

## Areas for Improvement and Production Readiness
To make this project production-ready, consider the following enhancements:

1. **Database Management**:
   - **Cloud Database**: Replace SQLite with a managed database for scalability and concurrency.
   - **Backup and Recovery**: Implement automated backups of `rates.db` to prevent data loss.

2. **ETL Pipeline**:
   - **Scheduling**: Run `etl.py` on a schedule to keep rates current.
   - **Error Handling**: Add retry logic for network failures and validation for Excel data quality.

3. **API Enhancements**:
   - **Rate Limiting**: Implement throttling to prevent abuse.
   - **Input Validation**: Enhance `LoanDetails` with stricter checks.

4. **Performance**:
   - **Caching**: Cache `rates.db` queries in memory for faster responses.
   - **Async Database**: Use `databases` or `SQLAlchemy` with async support for better concurrency.

5. **Testing**:
   - **Integration Tests**: Test the full pipeline (ETL + API) with a mock database.
   - **Load Testing**: Simulate high traffic to ensure scalability.

6. **Security**:
   - **Data Validation**: Sanitize inputs to prevent attacks.
   - **Secrets Management**: Store sensitive URLs in environment variables.

7. **Rate Data**:
   - **Fallback Rates**: Handle missing reset dates by interpolating or using historical averages.
   - **Data Sources**: Validate multiple sources for SOFR rates to ensure reliability.

