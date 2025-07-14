import hashlib
import json
import os
from datetime import datetime

import bech32
from nostr_sdk import Keys


def format_timestamp(timestamp):
    """Convert unix timestamp to readable format."""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def load_keys_from_file(key_file: str) -> Keys:
    """Load private key from file or generate new one."""
    if os.path.exists(key_file):
        try:
            with open(key_file) as f:
                lines = [line.strip() for line in f.readlines()]
                private_key_lines = [line for line in lines if line and not line.startswith("#")]
                if not private_key_lines:
                    raise ValueError("No private key found in file (only comments/empty lines)")
                private_key_hex = private_key_lines[0]
            return Keys.parse(private_key_hex)
        except Exception as e:
            print(f"❌ Error loading keys from {key_file}: {e}")
            return None
    else:
        keys = Keys.generate()
        try:
            with open(key_file, "w") as f:
                f.write(keys.secret_key().to_hex())
            print(f"✅ Generated new keys and saved to {key_file}")
            print(f"Public key: {keys.public_key().to_hex()}")
            return keys
        except Exception as e:
            print(f"❌ Error saving keys to {key_file}: {e}")
            return None


def save_to_keys_file(private_key_hex: str, filename: str = "keys.txt"):
    """Save the private key to a keys.txt file with proper formatting."""
    try:
        with open(filename, "w") as f:
            f.write("# Sample private key file for Nostr Playground\n")
            f.write("# \n")
            f.write("# This file should contain your private key in hex format.\n")
            f.write("# The private key should be 64 characters long (32 bytes).\n")
            f.write("# \n")
            f.write("# IMPORTANT: Keep this file secure and never share your private key!\n")
            f.write("# \n")
            f.write("# Example format (replace with your actual private key):\n")
            f.write("# 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n")
            f.write("# \n")
            f.write("# To generate a new key pair, run:\n")
            f.write("# uv run like_post.py <any_event_id> --keys keys.txt\n")
            f.write("# \n")
            f.write("# This will automatically generate a new key pair and save it to keys.txt\n")
            f.write("# \n")
            f.write("# Your public key will be displayed when you first run the script.\n")
            f.write(
                "# You can share your public key with others, but keep the private key secret.\n"
            )
            f.write("# \n")
            f.write("# Replace this line with your actual private key:\n")
            f.write(f"{private_key_hex}\n")
        print(f"✅ Private key saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving to {filename}: {e}")
        return False


def decode_bech32_proper(bech32_string: str):
    """Decode a bech32 string properly according to NIP-19."""
    try:
        hrp, data = bech32.bech32_decode(bech32_string)
        if hrp is None or data is None:
            return None
        data_bytes = bech32.convertbits(data, 5, 8, False)
        if data_bytes is None:
            return None
        return {"hrp": hrp, "data": data_bytes, "data_length": len(data_bytes)}
    except Exception:
        return None


def calculate_event_id(event_data: dict) -> str:
    """
    Calculate the event ID according to Nostr specification.
    Canonical form: [0, pubkey, created_at, kind, tags, content]
    """
    # Create the canonical array for hashing
    canonical = [
        0,
        event_data["pubkey"],
        event_data["created_at"],
        event_data["kind"],
        event_data["tags"],
        event_data["content"],
    ]

    # Serialize to JSON string
    canonical_json = json.dumps(canonical, separators=(",", ":"), ensure_ascii=False)

    # Calculate SHA-256 hash
    event_id_bytes = hashlib.sha256(canonical_json.encode("utf-8")).digest()

    # Convert to lowercase hex string
    event_id = event_id_bytes.hex()

    return event_id
