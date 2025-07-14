import argparse
import asyncio
import hashlib
import json
import traceback
from datetime import timedelta
from urllib.parse import quote
from urllib.request import Request, urlopen

from decode_nevent import get_zap_info
from nostr_sdk import (
    Client,
    EventBuilder,
    EventId,
    Filter,
    Kind,
    Metadata,
    NostrSigner,
    PublicKey,
    ZapRequestData,
)
from utils import load_keys_from_file


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


def get_browser_headers():
    """Return headers that make requests look like they come from a Mozilla browser."""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        # 'Accept-Language': 'en-US,en;q=0.5',
        # 'Accept-Encoding': 'gzip, deflate',
        # 'DNT': '1',
        # 'Connection': 'keep-alive',
        # 'Upgrade-Insecure-Requests': '1',
        # 'Sec-Fetch-Dest': 'document',
        # 'Sec-Fetch-Mode': 'navigate',
        # 'Sec-Fetch-Site': 'none',
        # 'Sec-Fetch-User': '?1',
        # 'Cache-Control': 'max-age=0'
    }


async def get_lnurl(client: Client, pubkey: PublicKey) -> str:
    """Fetch user'''s metadata and extract the LNURL."""
    print(f"🔎 Fetching metadata for {pubkey.to_bech32()}")
    metadata_filter = Filter().author(pubkey).kind(Kind(0)).limit(1)
    events = await client.fetch_events(metadata_filter, timedelta(seconds=10))

    events_list = events.to_vec()
    if not events_list:
        print("❌ Could not find metadata for the recipient.")
        return None

    metadata = Metadata.from_json(events_list[0].content())
    lud16 = metadata.get_lud16()
    lud06 = metadata.get_lud06()

    if lud16:
        ln_addr = lud16
        print(f"✅ Found Lightning Address: {ln_addr}")
        parts = ln_addr.split("@")
        return f"https://{parts[1]}/.well-known/lnurlp/{parts[0]}"
    elif lud06:
        print("✅ Found LNURL (lud06).")
        # Note: Add bech32 decoding for lud06 if needed. For now, we focus on lud16.
        return None
    else:
        print("❌ Recipient does not have a Lightning Address (lud16) or LNURL (lud06) set up.")
        return None


async def main():
    parser = argparse.ArgumentParser(
        description="""
Manually perform a NIP-57 zap to get a BOLT11 invoice. Can zap a user directly or zap a specific note using a nevent.

Examples:
  # Zap a note using nevent (automatic recipient and note detection):
  python send_zap.py --nevent nevent1abc123... 1000 -m "Great post!"

  # Traditional zapping - user only:
  python send_zap.py npub1abc123... 1000 -m "Thanks!"

  # Traditional zapping - specific note:
  python send_zap.py npub1abc123... 1000 -n note1def456... -m "Love this note!"
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create mutually exclusive group for nevent vs traditional args
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--nevent",
        help="A nevent string containing the note to zap and its author. This will automatically extract the recipient and note ID.",
    )
    group.add_argument(
        "recipient",
        nargs="?",
        help="The npub of the recipient to zap (when not using --nevent).",
    )

    parser.add_argument("amount", help="The amount to zap in sats.", type=int)
    parser.add_argument(
        "-m",
        "--message",
        help="An optional message to include with the zap.",
        default="",
    )
    parser.add_argument(
        "-n",
        "--note",
        help="The note ID (event ID in hex) to zap when using recipient. If provided, zaps the note instead of just the user. This adds an 'e' tag to the zap request. Can be provided as hex string or note1... bech32 format.",
        default=None,
    )
    parser.add_argument(
        "--keys",
        default="keys.txt",
        help="Path to the file containing your private key.",
    )
    args = parser.parse_args()

    # Validate argument combinations
    if not args.nevent and not args.recipient:
        parser.error("You must provide either --nevent or recipient")

    if args.nevent and args.note:
        parser.error(
            "Cannot use both --nevent and --note. The nevent already contains the note information."
        )

    print("🔑 Loading keys...")
    keys = load_keys_from_file(args.keys)
    if not keys:
        return

    print("📡 Initializing Nostr client...")
    signer = NostrSigner.keys(keys)
    client = Client(signer=signer)
    # Define relays for the zap receipt
    receipt_relays = [
        "wss://relay.damus.io",
        "wss://nos.lol",
        "wss://relay.getalby.com/v1",
    ]
    for r in receipt_relays:
        await client.add_relay(r)
    await client.connect()

    try:
        # --- DETERMINE RECIPIENT AND NOTE FROM ARGUMENTS ---
        if args.nevent:
            print(f"🔍 Decoding nevent: {args.nevent}")
            try:
                recipient_pubkey, note_event_id = get_zap_info(args.nevent)
                print("✅ Extracted from nevent:")
                print(f"   Recipient: {recipient_pubkey.to_bech32()}")
                print(f"   Note ID: {note_event_id.to_hex()}")
            except Exception as e:
                print(f"❌ Failed to decode nevent: {e}")
                return
        else:
            # Traditional mode: recipient and optional note
            recipient_pubkey = PublicKey.parse(args.recipient)
            note_event_id = None
            if args.note:
                try:
                    note_event_id = EventId.parse(args.note)
                    print(f"✅ Parsed note ID: {note_event_id.to_hex()}")
                except Exception as e:
                    print(f"❌ Error parsing note event ID: {e}")
                    return

        # --- NIP-57 MANUAL WORKFLOW ---
        amount_msats = args.amount * 1000

        # 1. Get LNURL from profile
        lnurl_endpoint = await get_lnurl(client, recipient_pubkey)
        if not lnurl_endpoint:
            return

        # 2. Make first HTTP request
        print(f"📞 Calling LNURL endpoint: {lnurl_endpoint}")
        request = Request(lnurl_endpoint, headers=get_browser_headers())
        with urlopen(request) as response:
            lnurl_data = json.loads(response.read())

        if not lnurl_data.get("allowsNostr"):
            print("❌ LNURL server does not support Nostr zaps.")
            return

        callback_url = lnurl_data["callback"]
        print(f"✅ Got callback URL: {callback_url}")

        # 3. Create Zap Request Event
        print("✍️  Creating and signing Zap Request (Kind 9734)...")
        if args.message:
            print(f"📝 Including message: '{args.message}'")

        if note_event_id:
            print(f"⚡ Zapping note: {note_event_id.to_hex()}")
        else:
            print(f"⚡ Zapping user: {recipient_pubkey.to_bech32()}")

        # Create the zap request data
        zap_request_data = ZapRequestData(recipient_pubkey, receipt_relays).message(args.message)

        # If zapping a note, we need to add the event ID to the zap request data
        if note_event_id:
            zap_request_data = zap_request_data.event_id(note_event_id)
            print(f"📌 Added 'e' tag for note: {note_event_id.to_hex()}")

        # Build the unsigned zap request event
        unsigned_zap_request = EventBuilder.public_zap_request(zap_request_data).build(
            keys.public_key()
        )

        signer = await client.signer()
        zap_request = await signer.sign_event(unsigned_zap_request)

        # Save event to file for debugging
        with open("zap-unsigned.json", "w") as f:
            f.write(unsigned_zap_request.as_json())
        with open("zap.json", "w") as f:
            f.write(zap_request.as_json())

        # Show zap request details
        zap_json = json.loads(zap_request.as_json())
        print("\n📋 Zap Request Details:")
        print(f"  Kind: {zap_json['kind']}")
        print(f"  Content: '{zap_json['content']}'")
        print("  Tags:")
        for tag in zap_json["tags"]:
            if tag[0] == "p":
                print(f"    - p tag (recipient): {tag[1][:16]}...")
            elif tag[0] == "e":
                print(f"    - e tag (note): {tag[1]}")
            elif tag[0] == "relays":
                print(f"    - relays tag: {len(tag)-1} relays")
            else:
                print(f"    - {tag[0]} tag: {tag[1:] if len(tag) > 1 else 'no value'}")

        if note_event_id:
            e_tags = [tag for tag in zap_json["tags"] if tag[0] == "e"]
            if e_tags:
                print("✅ Successfully created note zap with 'e' tag!")
            else:
                print("⚠️  Warning: Expected 'e' tag for note zap but none found!")
        else:
            print("✅ Successfully created user zap!")

        # 4. Make second HTTP request (to callback)
        encoded_event = quote(zap_request.as_json())
        final_url = f"{callback_url}?amount={amount_msats}&nostr={encoded_event}"
        print("\n📞 Calling callback URL... ")
        request = Request(final_url, headers=get_browser_headers())
        with urlopen(request) as response:
            callback_data = json.loads(response.read())

        # 5. Extract and print the invoice!
        bolt11_invoice = callback_data.get("pr")
        if not bolt11_invoice:
            print(
                f"❌ Callback response did not contain a BOLT11 invoice. Response: {callback_data}"
            )
            return

        print("\n" + "=" * 60)
        print("✅ SUCCESS! Got BOLT11 Invoice!")
        print("=" * 60)
        print(f"Invoice: {bolt11_invoice}")
        print("\nWith this invoice, you can now proceed to pay it.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        print("\n📋 Full traceback:")
        traceback.print_exc()
    finally:
        print("\n🔌 Shutting down client...")
        await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
