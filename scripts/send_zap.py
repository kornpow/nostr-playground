import argparse
import asyncio
from nostr_sdk import Keys, Client, NostrSigner, ZapRequestData, ZapType

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("recipient", help="the npub of the recipient")
    parser.add_argument("amount", help="the amount to zap in sats", type=int)
    parser.add_argument("-m", "--message", help="a message to send with the zap")
    args = parser.parse_args()

    # TO DO: get keys from a secure location
    keys = Keys.generate()
    signer = NostrSigner.keys(keys)
    client = Client(signer)
    await client.add_relay("wss://relay.damus.io")
    await client.connect()

    zap_request_data = ZapRequestData(
        public_key=args.recipient,
        amount=args.amount * 1000, # convert to millisats
        message=args.message
    )

    await client.zap(zap_request_data, ZapType.PUBLIC)

    print(f"Zapped {args.amount} sats to {args.recipient}")

    await client.shutdown()

if __name__ == '__main__':
    asyncio.run(main())
