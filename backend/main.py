from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from database import init_db
from routers import auth, chart, user

load_dotenv()

app = FastAPI(
    title="Astrara API",
    description="API para geração de mapas astrais",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chart.router)
app.include_router(user.router)


@app.on_event("startup")
async def startup():
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Running without database connection.")


@app.get("/")
async def root():
    return {"message": "Astrara API", "status": "online"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
