from fastapi import FastAPI
from app.routers.skateparks import router as skateparks_router

app = FastAPI(
    title="Skateparks API",
    version="1.0.0",
    description="Search skateparks of your favorite city"
)

app.include_router(skateparks_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}