
import argparse
import asyncio
import os
import json
import traceback
import hashlib
from urllib.parse import urlencode, quote
from urllib.request import urlopen, Request
from nostr_sdk import (
    Keys,
    Client,
    NostrSigner,
    ZapRequestData,
    ZapType,
    PublicKey,
    EventBuilder,
    Filter,
    Metadata,
    Kind,
    Timestamp,
    Tag,
    UnsignedEvent
)

def load_keys_from_file(key_file: str) -> Keys:
    """Load private key from file. This is the known-working function."""
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                lines = [line.strip() for line in f.readlines()]
                private_key_lines = [line for line in lines if line and not line.startswith('#')]
                if not private_key_lines:
                    raise ValueError("No private key found in file (only comments/empty lines)")
                private_key_hex = private_key_lines[0]
            return Keys.parse(private_key_hex)
        except Exception as e:
            print(f"❌ Error loading keys from {key_file}: {e}")
            return None
    else:
        print(f"❌ Key file not found at {key_file}. A key is required to sign the zap request.")
        return None


from datetime import timedelta

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
        event_data["content"]
    ]
    
    # Serialize to JSON string
    canonical_json = json.dumps(canonical, separators=(',', ':'), ensure_ascii=False)
    
    # Calculate SHA-256 hash
    event_id_bytes = hashlib.sha256(canonical_json.encode('utf-8')).digest()
    
    # Convert to lowercase hex string
    event_id = event_id_bytes.hex()
    
    return event_id

def get_browser_headers():
    """Return headers that make requests look like they come from a Mozilla browser."""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
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
        parts = ln_addr.split('@')
        return f"https://{parts[1]}/.well-known/lnurlp/{parts[0]}"
    elif lud06:
        print("✅ Found LNURL (lud06).")
        # Note: Add bech32 decoding for lud06 if needed. For now, we focus on lud16.
        return None
    else:
        print("❌ Recipient does not have a Lightning Address (lud16) or LNURL (lud06) set up.")
        return None


async def main():
    parser = argparse.ArgumentParser(description="Manually perform a NIP-57 zap to get a BOLT11 invoice.")
    parser.add_argument("recipient", help="The npub of the recipient to zap.")
    parser.add_argument("amount", help="The amount to zap in sats.", type=int)
    parser.add_argument("-m", "--message", help="An optional message to include with the zap.", default="")
    parser.add_argument("--keys", default="keys.txt", help="Path to the file containing your private key.")
    args = parser.parse_args()

    print("🔑 Loading keys...")
    keys = load_keys_from_file(args.keys)
    if not keys:
        return

    print("📡 Initializing Nostr client...")
    signer = NostrSigner.keys(keys)
    client = Client(signer=signer)
    # Define relays for the zap receipt
    receipt_relays = ["wss://relay.damus.io", "wss://nos.lol", "wss://relay.getalby.com/v1"]
    for r in receipt_relays:
        await client.add_relay(r)
    await client.connect()

    try:
        # --- NIP-57 MANUAL WORKFLOW ---
        recipient_pubkey = PublicKey.parse(args.recipient)
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
            
        import pprint
        zap_request_data = ZapRequestData(recipient_pubkey, receipt_relays)
        zap_request_data.message = args.message
        unsigned_event = EventBuilder.public_zap_request(zap_request_data).build(keys.public_key())
        # import code; code.interact(local=dict(globals(), **locals()))
        dir(unsigned_event)
        # unsigned_event.content = args.message
        signer = await client.signer()
        # zap_request = await signer.sign_event(unsigned_event)
        print("DEBUGGING!!!!\n\n\n")
        pprint.pprint(unsigned_event.as_json())
        workaround = unsigned_event.as_json()
        wrk = json.loads(workaround)
        wrk['content'] = args.message
        
        # Recalculate the event ID after updating content
        new_event_id = calculate_event_id(wrk)
        wrk['id'] = new_event_id
        print(f"🆔 Recalculated event ID: {new_event_id}")

        unsigned_event = UnsignedEvent.from_json(json.dumps(wrk))
        zap_request = await signer.sign_event(unsigned_event)

        pprint.pprint(zap_request.as_json())
        print("DEBUGGING!!!!\nEND\n\n")
        # Save event to file for debugging
        with open('zap_request-unsigned.json', 'w') as f:
            f.write(unsigned_event.as_json())
        with open('zap_request.json', 'w') as f:
            f.write(zap_request.as_json())
        
        # 4. Make second HTTP request (to callback)
        encoded_event = quote(zap_request.as_json())
        final_url = f"{callback_url}?amount={amount_msats}&nostr={encoded_event}"
        print(f"📞 Calling callback URL... ")
        request = Request(final_url, headers=get_browser_headers())
        with urlopen(request) as response:
            callback_data = json.loads(response.read())
        print(f"Zap Request Event: {zap_request.as_json()}")

        # 5. Extract and print the invoice!
        bolt11_invoice = callback_data.get("pr")
        if not bolt11_invoice:
            print(f"❌ Callback response did not contain a BOLT11 invoice. Response: {callback_data}")
            return
            
        print("\n" + "="*60)
        print("✅ SUCCESS! Got BOLT11 Invoice!")
        print("="*60)
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
