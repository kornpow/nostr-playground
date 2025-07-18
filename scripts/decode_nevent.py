#!/usr/bin/env python3
"""
Nostr Event Decoder - Decode nevent bech32 strings

This script decodes nevent (Nostr event) bech32 encoded strings according to NIP-19.
"""

import json
import re
import sys

from nostr_sdk import EventId, PublicKey
from utils import decode_bech32_proper


def decode_tlv(data_bytes):
    """
    Decode TLV (Type-Length-Value) data according to NIP-19.

    Args:
        data_bytes: The binary data to decode

    Returns:
        Dict with decoded TLV components
    """
    result = {}
    offset = 0

    while offset < len(data_bytes):
        if offset + 2 > len(data_bytes):
            break

        # Read type and length (1 byte each)
        tlv_type = data_bytes[offset]
        length = data_bytes[offset + 1]
        offset += 2

        if offset + length > len(data_bytes):
            break

        # Read value
        value = data_bytes[offset : offset + length]
        offset += length

        # Process based on type
        if tlv_type == 0:  # Special (event ID for nevent)
            if len(value) == 32:
                event_id_hex = value.hex()
                result["event_id"] = event_id_hex
        elif tlv_type == 1:  # Relay
            relay_url = value.decode("ascii", errors="ignore")
            if "relays" not in result:
                result["relays"] = []
            result["relays"].append(relay_url)
        elif tlv_type == 2:  # Author
            if len(value) == 32:
                author_hex = value.hex()
                result["author"] = author_hex
        elif tlv_type == 3:  # Kind
            if len(value) == 4:
                kind = int.from_bytes(value, byteorder="big")
                result["kind"] = kind

    return result


def decode_nevent(nevent_string: str):
    """
    Decode a nevent bech32 string according to NIP-19.

    Args:
        nevent_string: The nevent string to decode

    Returns:
        Dict with decoded components
    """
    try:
        # Remove nostr: prefix if present
        if nevent_string.startswith("nostr:"):
            nevent_string = nevent_string[6:]  # Remove 'nostr:' prefix

        # First, try to extract just the event ID part if it's a complex nevent
        if nevent_string.startswith("nevent1"):
            # This is a complex nevent format with TLV encoding
            hex_match = re.search(r"[0-9a-f]{64}", nevent_string)
            if hex_match:
                # Found a simple hex event ID embedded in the nevent
                event_id_hex = hex_match.group(0)
                event_id = EventId.parse(event_id_hex)

                result = {
                    "success": True,
                    "nevent": nevent_string,
                    "event_id_hex": event_id.to_hex(),
                    "event_id_bech32": event_id.to_bech32(),
                    "note_id": event_id.to_bech32(),  # This is the note ID
                    "format": "complex_nevent_with_hex_id",
                    "note": "Found embedded hex event ID in complex nevent",
                    "error": None,
                }
            else:
                # This is a proper NIP-19 nevent with TLV encoding
                bech32_info = decode_bech32_proper(nevent_string)
                if bech32_info and "error" not in bech32_info:
                    # Decode the TLV data to extract the event ID
                    tlv_data = decode_tlv(bytes(bech32_info["data"]))

                    if "event_id" in tlv_data:
                        # Successfully extracted event ID from TLV data
                        event_id = EventId.parse(tlv_data["event_id"])
                        result = {
                            "success": True,
                            "nevent": nevent_string,
                            "event_id_hex": event_id.to_hex(),
                            "event_id_bech32": event_id.to_bech32(),
                            "note_id": event_id.to_bech32(),  # This is the note ID
                            "format": "nip19_nevent",
                            "bech32_info": bech32_info,
                            "tlv_data": tlv_data,
                            "note": "Successfully decoded NIP-19 nevent with TLV data",
                            "error": None,
                        }
                    else:
                        result = {
                            "success": False,
                            "nevent": nevent_string,
                            "error": "No event ID found in TLV data",
                            "bech32_info": bech32_info,
                            "tlv_data": tlv_data,
                        }
                else:
                    # Try parsing the whole string as a simple event ID
                    event_id = EventId.parse(nevent_string)
                    result = {
                        "success": True,
                        "nevent": nevent_string,
                        "event_id_hex": event_id.to_hex(),
                        "event_id_bech32": event_id.to_bech32(),
                        "note_id": event_id.to_bech32(),  # This is the note ID
                        "format": "simple_nevent",
                        "error": None,
                    }
        else:
            # Try parsing as a simple event ID
            event_id = EventId.parse(nevent_string)
            result = {
                "success": True,
                "nevent": nevent_string,
                "event_id_hex": event_id.to_hex(),
                "event_id_bech32": event_id.to_bech32(),
                "note_id": event_id.to_bech32(),  # This is the note ID
                "format": "simple_event_id",
                "error": None,
            }

        return result

    except Exception as e:
        return {"success": False, "nevent": nevent_string, "error": str(e)}


def get_note_id(nevent_string: str) -> str:
    """
    Simple function to extract just the note ID from a nevent string.

    Args:
        nevent_string: The nevent string to decode

    Returns:
        The note ID (bech32 format) or None if failed
    """
    result = decode_nevent(nevent_string)
    if result["success"] and "note_id" in result:
        return result["note_id"]
    return None


def get_zap_info(nevent_string: str) -> tuple[PublicKey, EventId]:
    """
    Extract author and event ID from a nevent string for zapping.

    Args:
        nevent_string: The nevent string to decode

    Returns:
        Tuple of (author_public_key, event_id)

    Raises:
        Exception if decoding fails or author is not available
    """
    result = decode_nevent(nevent_string)

    if not result["success"]:
        raise Exception(f"Failed to decode nevent: {result['error']}")

    # Get the event ID
    event_id = EventId.parse(result["event_id_hex"])

    # Try to get the author from TLV data
    author = None
    if "tlv_data" in result and "author" in result["tlv_data"]:
        author_hex = result["tlv_data"]["author"]
        author = PublicKey.parse(author_hex)

    if author is None:
        raise Exception(
            "nevent does not contain author information - you'll need to provide the recipient manually"
        )

    return author, event_id


def print_decoded_event(result):
    """Print the decoded event information."""
    if result["success"]:
        print("✅ Successfully decoded nevent")
        print("=" * 60)
        print(f"Original nevent: {result['nevent']}")
        print(f"Format: {result.get('format', 'unknown')}")

        # Prominently display the note ID
        if "note_id" in result:
            print(f"🎯 NOTE ID: {result['note_id']}")

        if "event_id_hex" in result:
            print(f"Event ID (hex): {result['event_id_hex']}")
            print(f"Event ID (bech32): {result['event_id_bech32']}")

        if "bech32_info" in result:
            bech32_info = result["bech32_info"]
            print(f"Bech32 HRP: {bech32_info.get('hrp', 'unknown')}")
            print(f"Data length: {bech32_info.get('data_length', 'unknown')} bytes")

        # Display TLV data if available
        if "tlv_data" in result:
            tlv_data = result["tlv_data"]
            if "event_id" in tlv_data:
                print(f"Event ID from TLV: {tlv_data['event_id']}")
            if "relays" in tlv_data:
                print(f"Relays: {tlv_data['relays']}")
            if "author" in tlv_data:
                print(f"Author: {tlv_data['author']}")
            if "kind" in tlv_data:
                print(f"Kind: {tlv_data['kind']}")

        if "note" in result:
            print(f"Note: {result['note']}")

        print("=" * 60)
    else:
        print("❌ Failed to decode nevent")
        print("=" * 60)
        print(f"Input: {result['nevent']}")
        print(f"Error: {result['error']}")
        print("=" * 60)


def main():
    """Main function to run the nevent decoder."""
    import argparse

    parser = argparse.ArgumentParser(description="Decode a nevent (Nostr event) bech32 string")
    parser.add_argument("nevent", help="The nevent string to decode")
    parser.add_argument("--json", action="store_true", help="Output result as JSON")
    parser.add_argument("--note-id-only", action="store_true", help="Output only the note ID")

    args = parser.parse_args()

    # Decode the nevent
    result = decode_nevent(args.nevent)

    if args.note_id_only:
        # Output only the note ID
        note_id = get_note_id(args.nevent)
        if note_id:
            print(note_id)
        else:
            print("Failed to extract note ID", file=sys.stderr)
            exit(1)
    elif args.json:
        # Output as JSON
        print(json.dumps(result, indent=2))
    else:
        # Print formatted output
        print_decoded_event(result)


if __name__ == "__main__":
    main()
