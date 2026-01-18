import os
import shutil
from pathlib import Path
from huggingface_hub import hf_hub_download

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
EMBEDDINGS_DIR = MODELS_DIR / "embeddings"
EMBEDDINGS_DIR.mkdir(exist_ok=True)

# Defined voices
VOICES = ["alba", "marius", "javert", "jean", "fantine", "cosette", "eponine", "azelma"]

def download_and_copy(repo_id, filename, revision, target_filename=None):
    if target_filename is None:
        target_filename = filename
        
    print(f"Downloading {filename} from {repo_id}...")
    try:
        # Download to cache
        cached_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            revision=revision,
        )
        
        # Copy to local models dir
        target_path = MODELS_DIR / target_filename
        
        # Handle subdirectory (e.g. embeddings/)
        if "/" in target_filename:
             target_path.parent.mkdir(exist_ok=True, parents=True)
             
        shutil.copy(cached_path, target_path)
        print(f"Copied to {target_path}")
        return target_path
    except Exception as e:
        print(f"Failed to download {filename}: {e}")
        return None

def main():
    print("Setting up offline models in ./models ...")

    # 1. Tokenizer (from no-vc repo, same for both)
    download_and_copy(
        "kyutai/pocket-tts-without-voice-cloning",
        "tokenizer.model",
        "d4fdd22ae8c8e1cb3634e150ebeff1dab2d16df3"
    )

    # 2. Model WITHOUT Voice Cloning
    # IMPORTANT: We save this with a distinct name to avoid collision
    download_and_copy(
        "kyutai/pocket-tts-without-voice-cloning",
        "tts_b6369a24.safetensors",
        "d4fdd22ae8c8e1cb3634e150ebeff1dab2d16df3",
        target_filename="tts_b6369a24_no_vc.safetensors" # RENAME HERE
    )

    # 3. Model WITH Voice Cloning (Requires Auth)
    print("\nAttempting to download voice cloning model (requires HF access + login)...")
    res = download_and_copy(
        "kyutai/pocket-tts",
        "tts_b6369a24.safetensors",
        "427e3d61b276ed69fdd03de0d185fa8a8d97fc5b",
        target_filename="tts_b6369a24.safetensors" # KEEP ORIGINAL NAME
    )
    
    if not res:
        print("\nWARNING: Could not download voice cloning model.")
        print("Please ensure you accepted the license at https://huggingface.co/kyutai/pocket-tts")
        print("And run 'huggingface-cli login' locally.")
    
    # 4. Voices
    print("\nDownloading voices...")
    for voice in VOICES:
        download_and_copy(
            "kyutai/pocket-tts-without-voice-cloning",
            f"embeddings/{voice}.safetensors",
            "d4fdd22ae8c8e1cb3634e150ebeff1dab2d16df3",
            target_filename=f"embeddings/{voice}.safetensors"
        )

    print("\nOffline setup complete.")

if __name__ == "__main__":
    main()
