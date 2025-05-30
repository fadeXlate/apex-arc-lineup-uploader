import io
import logging
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import pandas as pd
from starlette.requests import Request
from starlette.responses import JSONResponse

app = FastAPI()
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Setup logging
logging.basicConfig(filename='api.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

# Mock player database (expand as needed)
player_db = {
    "Juan Soto": "NYY",
    "Mike Trout": "LAA",
    "Aaron Judge": "NYY",
    "Mookie Betts": "LAD",
}

security = HTTPBearer()
JWT_SECRET = "replace_with_your_secret"  # In production, use environment variables

def verify_jwt(token: str):
    if token != "valid-token":
        raise HTTPException(status_code=403, detail="Invalid or expired token")

async def get_current_user(token: str = Depends(security)):
    verify_jwt(token.credentials)
    return "brock"

@app.post("/upload-lineup")
@limiter.limit("5/minute")
async def upload_lineup(request: Request, file: UploadFile = File(...), user=Depends(get_current_user)):
    logging.info(f"Prediction requested by user '{user}' with file '{file.filename}'")
    content = await file.read()
    try:
        df = pd.read_csv(io.StringIO(content.decode()))
    except Exception as e:
        logging.error(f"Failed to parse CSV: {e}")
        raise HTTPException(status_code=400, detail="Invalid CSV format")

    required_cols = {"player", "team"}
    missing_cols = required_cols - set(df.columns.str.lower())
    if missing_cols:
        err = f"Missing columns: {missing_cols}"
        logging.warning(err)
        raise HTTPException(status_code=400, detail=err)

    df.columns = df.columns.str.lower()

    invalid_players = []
    team_mismatches = []

    for _, row in df.iterrows():
        player = row["player"]
        team = row["team"]
        if player not in player_db:
            invalid_players.append(player)
        elif player_db[player] != team:
            team_mismatches.append(f"{player} (expected {player_db[player]}, got {team})")

    if invalid_players or team_mismatches:
        errors = {}
        if invalid_players:
            errors["invalid_players"] = invalid_players
        if team_mismatches:
            errors["team_mismatches"] = team_mismatches
        logging.warning(f"Validation errors: {errors}")
        return JSONResponse(status_code=400, content={"detail": errors})

    # Mock prediction output
    predictions = [{"player": p, "hr_prob": 0.15} for p in df["player"]]

    logging.info(f"Validated lineup for user '{user}': {list(df['player'])}")

    return {
        "lineup": df.to_dict(orient="records"),
        "predictions": predictions
    }