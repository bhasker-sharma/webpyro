from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.database import DeviceConfigDB, DeviceReadingsDB

app = FastAPI(title="Pyrometer Web API")

# Allow React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with http://localhost:3000
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DB instances ---
config_db = DeviceConfigDB()
readings_db = DeviceReadingsDB()

@app.get("/")
def home():
    return {"message": "✅ Pyrometer FastAPI backend is running!"}

# --- Device Endpoints ---
@app.get("/api/devices/")
def list_devices():
    return config_db.get_all()

@app.post("/api/devices/")
def add_device(name: str, device_id: int, baud_rate: int, com_port: str, enabled: bool = True):
    config_db.add(name, device_id, baud_rate, com_port, enabled)
    return {"status": "success"}

# --- Readings Endpoints ---
@app.get("/api/readings/{device_id}")
def latest_readings(device_id: int, limit: int = 20):
    return readings_db.get_latest_for_device(device_id, limit=limit)
