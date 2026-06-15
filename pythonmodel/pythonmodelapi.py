import os
import io
import base64
import torch
import numpy as np
from PIL import Image
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from transformers import AutoImageProcessor, SiglipForImageClassification

# --- MEDIAPIPE SETUP ---
import mediapipe as mp

# Initialize hand detector globally so it doesn't reload on every frame
mp_hands = mp.solutions.hands
hands_detector = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5
)

# --- FASTAPI SETUP ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SIGLIP MODEL SETUP ---
local_model_path = os.path.dirname(os.path.abspath(__file__))
print(f"Loading model from: {local_model_path}")

processor = AutoImageProcessor.from_pretrained(
    local_model_path,
    local_files_only=True
)

model = SiglipForImageClassification.from_pretrained(
    local_model_path,
    local_files_only=True
)

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

model.to(device)
model.eval()

labels = [
    "A", "B", "C", "D", "E", "F", "G", "H",
    "I", "J", "K", "L", "M", "N", "O", "P",
    "Q", "R", "S", "T", "U", "V", "W", "X",
    "Y", "Z"
]


# --- ROUTES ---

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image = Image.open(io.BytesIO(await file.read())).convert("RGB")

    inputs = processor(images=image, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1).squeeze()

    idx = torch.argmax(probs).item()

    return {
        "prediction": labels[idx],
        "confidence": round(probs[idx].item(), 3)
    }


@app.websocket("/ws/detect")
async def detect(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established.")

    try:
        while True:
            # 1. Receive and Decode Data
            data = await websocket.receive_text()
            image_data = data.split(",")[1]
            image_bytes = base64.b64decode(image_data)

            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

            # 2. MediaPipe Hand Detection
            # Convert PIL image to numpy array for MediaPipe
            img_np = np.array(image)
            results = hands_detector.process(img_np)

            # If no hand is detected, send message and skip SigLIP inference
            if not results.multi_hand_landmarks:
                await websocket.send_json({"error": "No hand detected"})
                continue

            # 3. SigLIP Classification (runs only if hand is detected)
            inputs = processor(images=image, return_tensors="pt").to(device)

            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=1).squeeze()

            idx = torch.argmax(probs).item()
            prediction = labels[idx]
            confidence = round(probs[idx].item(), 3)

            # 4. Send successful result
            await websocket.send_json({
                "prediction": prediction,
                "confidence": confidence
            })

    except WebSocketDisconnect:
        # Expected behavior when the client closes the browser/connection
        print("Client disconnected normally.")

    except RuntimeError as e:
        # Handles ASGI errors if connection drops mid-process
        print(f"Runtime WebSocket Error: {e}")

    except Exception as e:
        # Catch-all for unexpected errors (e.g., base64 decoding issues)
        print(f"Unexpected Error: {e}")
        try:
            # Attempt to notify the client, but ignore if the socket is already dead
            await websocket.send_json({"error": str(e)})
        except RuntimeError:
            pass

    finally:
        # This ensures the server cleans up the connection state properly
        print("WebSocket loop exited cleanly.")