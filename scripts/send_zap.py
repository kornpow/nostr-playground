import argparse
import asyncio
import os
from nostr_sdk import (
    Keys, 
    Client, 
    NostrSigner, 
    ZapRequestData, 
    ZapType, 
    PublicKey,
    EventId
)

def load_keys_from_file(key_file: str) -> Keys:
    """Load private key from file or generate new one."""
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r') as f:
                # Read all lines and filter out comments and empty lines
                lines = [line.strip() for line in f.readlines()]
                # Remove comments (lines starting with #) and empty lines
                private_key_lines = [line for line in lines if line and not line.startswith('#')]
                
                if not private_key_lines:
                    raise ValueError("No private key found in file (only comments/empty lines)")
                
                # Use the first non-comment, non-empty line as the private key
                private_key_hex = private_key_lines[0]
            return Keys.parse(private_key_hex)
        except Exception as e:
            print(f"❌ Error loading keys from {key_file}: {e}")
            return None
    else:
        # Generate new keys
        keys = Keys.generate()
        try:
            with open(key_file, 'w') as f:
                f.write(keys.secret_key().to_hex())
            print(f"✅ Generated new keys and saved to {key_file}")
            print(f"Public key: {keys.public_key().to_hex()}")
            return keys
        except Exception as e:
            print(f"❌ Error saving keys to {key_file}: {e}")
            return None

async def main():
    parser = argparse.ArgumentParser(description="Send a Nostr zap and get a BOLT11 invoice.")
    parser.add_argument("recipient", help="The npub of the recipient to zap.")
    parser.add_argument("amount", help="The amount to zap in sats.", type=int)
    parser.add_argument("-m", "--message", help="An optional message to include with the zap.", default="")
    parser.add_argument("-e", "--event", help="Optional event ID (hex) to associate the zap with.")
    parser.add_argument("--keys", default="keys.txt", help="Path to the file containing your private key.")
    args = parser.parse_args()

    # --- Step 1: Load Keys ---
    # A signer is required to create the Kind 9734 Zap Request event.
    print("🔑 Loading keys...")
    keys = load_keys_from_file(args.keys)
    if not keys:
        return

    # --- Step 2: Initialize Client ---
    # The client will orchestrate the NIP-57 flow.
    print("📡 Initializing Nostr client...")
    signer = NostrSigner.keys(keys)
    client = Client(signer=signer)
    
    # We need to add and connect to at least one relay to discover the user'''s LNURL.
    await client.add_relay("wss://relay.damus.io")
    await client.add_relay("wss://nos.lol")
    await client.connect()

    # --- Step 3: Prepare Zap Request Data ---
    # This object contains the core information for the zap.
    print("🛠️ Preparing zap request data...")
    recipient_pubkey = PublicKey.parse(args.recipient)
    
    # The relays for the receipt are specified in the zap() call itself.
    zap_request = ZapRequestData(recipient_pubkey, [])
    zap_request.message = args.message
    
    # If an event_id is provided, add it to the request.
    if args.event:
        event_id = EventId.parse(args.event)
        zap_request.event_id = event_id

    # --- Step 4: Execute the Zap Workflow ---
    # The client.zap method handles the entire NIP-57 flow:
    # 1. Fetches the user'''s LNURL from their profile.
    # 2. Creates the Kind 9734 Zap Request event.
    # 3. Makes the HTTP callback to the LNURL server.
    # 4. Returns the BOLT11 invoice from the server'''s response.
    print(f"⚡️ Executing zap workflow for {args.amount} sats to {args.recipient}...")
    try:
        # The amount must be in **millisats**.
        amount_msats = args.amount * 1000
        
        # The zap method returns the bolt11 invoice string.
        bolt11_invoice = await client.zap(zap_request, amount_msats)

        print("\n" + "="*60)
        print("✅ SUCCESS! Got BOLT11 Invoice!")
        print("="*60)
        print(f"Invoice: {bolt11_invoice}")
        print("\n下一步 (Next Step):")
        print("You can now pay this invoice using any Lightning wallet.")
        print("Once paid, the recipient's server will broadcast a Kind 9735 (Zap Receipt) event to Nostr relays.")

    except Exception as e:
        print(f"\n❌ An error occurred during the zap process: {e}")
        print("Please check the recipient'''s npub and ensure they have a Lightning Address set up.")

    finally:
        print("\n🔌 Shutting down client...")
        await client.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
