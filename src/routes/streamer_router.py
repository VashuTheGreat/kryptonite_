# # main.py
# from fastapi import  WebSocket
# from fastapi.responses import JSONResponse
# import base64
# import shutil
# import fastapi
# from ultralytics import YOLO
# from pathlib import Path
# import os
# router=fastapi.APIRouter()

# model = YOLO("saved_model/fire_detector.pt")

# async def draw_boxes(image_path, save_dir="outputs"):
#     results = model(
#         image_path,
#         conf=0.25,
#         save=True,
#         project=save_dir,
#         name="fires",
#     )

#     r = results[0]
#     save_path = Path(r.save_dir)

#     images = list(save_path.glob("*.jpg")) + list(save_path.glob("*.png"))
#     if not images:
#         raise FileNotFoundError("YOLO output image not found")

#     return str(images[0])
# @router.websocket("/ws_fire_image")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         print(data)
#         os.makedirs("public", exist_ok=True)

#         if not data:
#             return JSONResponse(status_code=400, content={"error": "byte file not found"})

#         file_path = f"public/streamFile.jpg"

#         # save uploaded file
#         with open(file_path, "wb") as f:
#             f.write(base64.b64decode(data))

#         # run YOLO inference
#         output_image_path = await draw_boxes(image_path=file_path)

#         # read output image
#         with open(output_image_path, "rb") as f:
#             image_bytes = f.read()

#         # cleanup
#         os.remove(file_path)
#         shutil.rmtree(os.path.dirname(output_image_path), ignore_errors=True)

#         encoded_image = base64.b64encode(image_bytes).decode("utf-8")
#         save_path = f"public/saved_streamFile.jpg"  # e.g., public/saved_input.jpg
#         with open(save_path, "wb") as f:
#             f.write(base64.b64decode(encoded_image))
#         await websocket.send_text(encoded_image)



# main.py
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import base64
import shutil
import fastapi
from ultralytics import YOLO
from pathlib import Path
import os
from typing import Dict, List

router = fastapi.APIRouter()

# Load YOLO model
model = YOLO("saved_model/fire_detector.pt")

# Store active WebSocket connections per room
# Format: {"room123": [websocket1, websocket2, ...]}
active_connections: Dict[str, List[WebSocket]] = {}


async def draw_boxes(image_path, save_dir="outputs"):
    """Run YOLO fire detection on image and return path to annotated image"""
    results = model(
        image_path,
        conf=0.25,
        save=True,
        project=save_dir,
        name="fires",
    )

    r = results[0]
    save_path = Path(r.save_dir)

    images = list(save_path.glob("*.jpg")) + list(save_path.glob("*.png"))
    if not images:
        raise FileNotFoundError("YOLO output image not found")

    return str(images[0])


@router.websocket("/ws_fire_image/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    """
    WebSocket endpoint with room-based broadcasting.
    - Streamers send base64 image frames
    - All viewers in the same room receive processed frames
    """
    await websocket.accept()
    
    # Add connection to room
    if room_id not in active_connections:
        active_connections[room_id] = []
    active_connections[room_id].append(websocket)
    
    print(f"Client connected to room: {room_id}. Total in room: {len(active_connections[room_id])}")
    
    try:
        while True:
            # Receive base64 image data
            data = await websocket.receive_text()
            
            # Skip if data is too short (likely not an image)
            if len(data) < 100:
                print(f"Received short message in room {room_id}, skipping...")
                continue
            
            try:
                # Create directory for temporary files
                os.makedirs("public", exist_ok=True)
                file_path = f"public/streamFile_{room_id}.jpg"

                # Decode and save uploaded image
                with open(file_path, "wb") as f:
                    f.write(base64.b64decode(data))

                # Run YOLO fire detection
                output_image_path = await draw_boxes(image_path=file_path)

                # Read processed image
                with open(output_image_path, "rb") as f:
                    image_bytes = f.read()

                # Cleanup temporary files
                os.remove(file_path)
                shutil.rmtree(os.path.dirname(output_image_path), ignore_errors=True)

                # Encode processed image to base64
                encoded_image = base64.b64encode(image_bytes).decode("utf-8")
                
                # Save a copy (optional)
                save_path = f"public/saved_streamFile_{room_id}.jpg"
                with open(save_path, "wb") as f:
                    f.write(base64.b64decode(encoded_image))
                
                # BROADCAST to all connections in this room
                disconnected = []
                for connection in active_connections[room_id]:
                    try:
                        await connection.send_text(encoded_image)
                    except Exception as e:
                        print(f"Failed to send to a connection: {e}")
                        disconnected.append(connection)
                
                # Remove dead connections
                for conn in disconnected:
                    if conn in active_connections[room_id]:
                        active_connections[room_id].remove(conn)
                        
            except Exception as e:
                print(f"Error processing image in room {room_id}: {e}")
                # Send error back to sender
                try:
                    await websocket.send_text(f'{{"error": "{str(e)}"}}')
                except:
                    pass
                    
    except WebSocketDisconnect:
        print(f"Client disconnected from room: {room_id}")
    except Exception as e:
        print(f"WebSocket error in room {room_id}: {e}")
    finally:
        # Remove connection from room
        if room_id in active_connections:
            if websocket in active_connections[room_id]:
                active_connections[room_id].remove(websocket)
            
            # Clean up empty rooms
            if not active_connections[room_id]:
                del active_connections[room_id]
                print(f"Room {room_id} is now empty and removed")
            else:
                print(f"Room {room_id} now has {len(active_connections[room_id])} connections")