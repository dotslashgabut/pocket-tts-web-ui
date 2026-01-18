import sys
import os
import io
import queue
import threading
import requests
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

# sys.path.append(str(Path(__file__).parent / "pocket-tts-src")) # Removed to use pip package

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import torch
import uvicorn

# Pocket TTS imports
import pocket_tts # Added for config path resolution
from pocket_tts.models.tts_model import TTSModel
from pocket_tts.utils.config import load_config
from pocket_tts.utils.utils import PREDEFINED_VOICES
import pocket_tts.utils.utils as utils_module
from pocket_tts.default_parameters import (
    DEFAULT_TEMPERATURE,
    DEFAULT_LSD_DECODE_STEPS,
    DEFAULT_NOISE_CLAMP,
    DEFAULT_EOS_THRESHOLD,
    DEFAULT_AUDIO_PROMPT
)
from pocket_tts.data.audio import stream_audio_chunks

MODELS_DIR = Path(__file__).parent / "models"

# Global model
tts_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts_model
    
    print("Initializing Pocket TTS Web UI...")
    
    print("Loading Model... using standard load_model")
    try:
        from pocket_tts.default_parameters import DEFAULT_VARIANT
        tts_model = TTSModel.load_model(DEFAULT_VARIANT)
        # tts_model.to("cpu")
        print("Model Loaded Successfully!")
        
    except Exception as e:
        print(f"Failed to load model: {e}")
        # We don't crash here so the UI can at least show an error
    
    yield
    
    print("Shutting down")

app = FastAPI(title="Pocket TTS Local", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

@app.get("/")
async def root():
    return FileResponse(Path(__file__).parent / "static/index.html")

@app.get("/api/voices")
async def get_voices():
    # Return available predefined voices
    # Use utils_module.PREDEFINED_VOICES keys
    return {"voices": list(utils_module.PREDEFINED_VOICES.keys())}
    
@app.get("/api/status")
async def status():
    return {
        "status": "ready" if tts_model else "model_not_loaded",
        "has_voice_cloning": tts_model.has_voice_cloning if tts_model else False
    }

def write_to_queue(q, text, model_state):
    """Bridge generator to queue for StreamingResponse"""
    print(f"Starting generation for text: {text[:20]}...")
    try:
        audio_chunks = tts_model.generate_audio_stream(
            model_state=model_state, text_to_generate=text
        )
        
        class QueueWriter(io.IOBase):
            def write(self, b):
                q.put(b)
                return len(b)
        
        stream_audio_chunks(QueueWriter(), audio_chunks, tts_model.config.mimi.sample_rate)
        print("Generation complete, signaling end of stream.")
        q.put(None) # Signal done
    except Exception as e:
        print(f"Generation error: {e}")
        import traceback
        traceback.print_exc()
        q.put(None)

def iter_audio(q):
    while True:
        data = q.get()
        if data is None:
            break
        yield data

@app.post("/api/generate")
async def generate(
    text: str = Form(...),
    voice: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None)
):
    if not tts_model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    model_state = None
    
    # Determine voice
    if file or url:
        # Load audio from file OR URL for cloning
        import tempfile
        
        tmp_path = None
        
        try:
            if file:
                suffix = Path(file.filename).suffix or ".wav"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    content = await file.read()
                    tmp.write(content)
                    tmp_path = Path(tmp.name)
                print(f"Received file: {file.filename}, size: {len(content)} bytes, saved to {tmp_path}")
                
            elif url:
                # Download from URL
                print(f"Downloading voice from URL: {url}")
                try:
                    response = requests.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Try to guess extension from url or content-type
                    import mimetypes
                    content_type = response.headers.get('content-type')
                    ext = mimetypes.guess_extension(content_type) or ".wav"
                    
                    if not ext:
                        if url.lower().endswith('.mp3'): ext = '.mp3'
                        elif url.lower().endswith('.wav'): ext = '.wav'
                        elif url.lower().endswith('.ogg'): ext = '.ogg'
                        else: ext = '.wav'

                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                        tmp.write(response.content)
                        tmp_path = Path(tmp.name)
                    print(f"Downloaded file from URL, size: {len(response.content)} bytes, saved to {tmp_path}")
                except Exception as e:
                     raise HTTPException(status_code=400, detail=f"Failed to download audio from URL: {str(e)}")

            # Use library truncate
            model_state = tts_model.get_state_for_audio_prompt(tmp_path, truncate=True)
            print("Successfully created model state from audio file")
            
        except HTTPException:
            raise
        except Exception as e:
             print(f"Error creating state from audio: {e}")
             import traceback
             traceback.print_exc()
             raise HTTPException(status_code=400, detail=f"Error processing voice file: {str(e)}")
        finally:
            # Best effort cleanup with GC for Windows file locks
            if tmp_path:
                try:
                    if tmp_path.exists():
                        import gc
                        gc.collect()
                        os.unlink(tmp_path) 
                except Exception as e:
                    print(f"Failed to delete temp file {tmp_path}: {e}")
                
                # Cleanup trunc file if it exists
                trunc_path = tmp_path.with_suffix('.trunc.wav')
                if trunc_path.exists():
                     try:
                         os.unlink(trunc_path)
                     except:
                         pass
    elif voice:
        # Predefined voice
        if voice not in utils_module.PREDEFINED_VOICES:
             raise HTTPException(status_code=400, detail="Unknown voice")
        # Ensure we pass the URL/path stored in PREDEFINED_VOICES
        voice_path = utils_module.PREDEFINED_VOICES[voice]
        # Pass the voice name directly so the model knows it's a predefined voice
        model_state = tts_model._cached_get_state_for_audio_prompt(voice, truncate=True)
    else:
        # Default voice
        model_state = tts_model._cached_get_state_for_audio_prompt('alba', truncate=True)

    # Buffer audio in memory to ensure correct WAV header
    # This avoids browser issues with streaming WAVs having incorrect duration in header
    import io
    import wave
    
    # We run generation in a thread to not block the event loop, 
    # but we wait for it to finish before sending response.
    # ideally we'd use run_in_executor
    
    output_buffer = io.BytesIO()
    
    def generate_to_buffer(model_state, text, buffer):
        try:
            # Generate all chunks
            chunks = []
            print(f"Generating for: {text[:20]}...")
            for chunk in tts_model.generate_audio_stream(
                model_state=model_state, text_to_generate=text
            ):
                chunks.append(chunk)
            
            print(f"Generated {len(chunks)} chunks.")
            
            # Write to buffer with correct header
            with wave.open(buffer, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2) # 16-bit
                wav_file.setframerate(tts_model.config.mimi.sample_rate)
                
                # Convert and write all chunks
                for chunk in chunks:
                    chunk_int16 = (chunk.clamp(-1, 1) * 32767).short()
                    chunk_bytes = chunk_int16.detach().cpu().numpy().tobytes()
                    wav_file.writeframes(chunk_bytes)
            
            print("Generation and write complete.")
            
        except Exception as e:
            print(f"Error in generation: {e}")
            import traceback
            traceback.print_exc()

    # Run in thread
    import asyncio
    await asyncio.to_thread(generate_to_buffer, model_state, text, output_buffer)
    
    output_buffer.seek(0)
    data = output_buffer.read()
    
    return StreamingResponse(
        io.BytesIO(data), 
        media_type="audio/wav",
        headers={
            "Content-Disposition": "attachment; filename=output.wav",
            "Content-Length": str(len(data))
        }
    )
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
