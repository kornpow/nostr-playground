import argparse
import asyncio
import os
from nostr_sdk import Keys, Client, NostrSigner, ZapRequestData, ZapType, PublicKey

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
    parser = argparse.ArgumentParser()
    parser.add_argument("recipient", help="the npub of the recipient")
    parser.add_argument("amount", help="the amount to zap in sats", type=int)
    parser.add_argument("-m", "--message", help="a message to send with the zap")
    parser.add_argument("--keys", default="keys.txt", help="File containing private key (default: keys.txt)")
    args = parser.parse_args()

    keys = load_keys_from_file(args.keys)
    if not keys:
      return

    signer = NostrSigner.keys(keys)
    client = Client(signer)
    # TO DO: Is there a better way to get relays?
    await client.add_relay("wss://relay.damus.io")
    await client.connect()

    recipient_public_key = PublicKey.parse(args.recipient)

    zap_request_data = ZapRequestData(
        public_key=recipient_public_key,
        amount=args.amount * 1000, # convert to millisats
        message=args.message
    )

    await client.zap(zap_request_data, ZapType.PUBLIC)

    print(f"Zapped {args.amount} sats to {args.recipient}")

    await client.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
