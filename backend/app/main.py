from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RouteMind API",
    description="Backend routing API for RouteMind model selector",
    version="1.0.0"
)

# Configure CORS so your React frontend (typically on localhost:5173) can make requests to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to RouteMind API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}