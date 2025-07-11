#!/usr/bin/env python3
"""
Extract unique relay URLs from a batch of notes on multiple relays

- Fetches several thousand notes from multiple popular relays
- Extracts all unique relay URLs referenced in the notes' tags (e.g., 'r' tags)
- Writes the unique relay URLs to relays_extracted.txt
"""

import asyncio
from nostr_sdk import Client, Filter, Kind, KindStandard
from datetime import timedelta

OUTPUT_FILE = 'relays_extracted.txt'
RELAYS = [
    'wss://relay.damus.io',
    'wss://nos.lol',
    'wss://relay.snort.social',
    'wss://relay.nostr.band',
    'wss://relay.nostr.wirednet.jp',
    'wss://nostr.wine',
    'wss://relay.nostr.info',
    'wss://relay.current.fyi',
    'wss://relay.nostr.bg',
    'wss://nostr.bitcoiner.social'
]
NOTE_LIMIT = 5000  # Increased from 2000
TIMEOUT_SECONDS = 120  # Increased timeout for more relays

async def extract_relays_from_relays():
    print(f"Connecting to {len(RELAYS)} relays and fetching up to {NOTE_LIMIT} notes from each...")
    client = Client()
    
    # Add all relays
    for relay in RELAYS:
        await client.add_relay(relay)
    
    await client.connect()
    print("Connected to all relays")

    kind_text_note = Kind.from_std(KindStandard.TEXT_NOTE)
    filter_obj = Filter().kinds([kind_text_note]).limit(NOTE_LIMIT)
    events = await client.fetch_events(filter_obj, timedelta(seconds=TIMEOUT_SECONDS))
    events_list = events.to_vec()
    print(f"Fetched {len(events_list)} notes total from all relays.")

    unique_relays = set()
    for idx, event in enumerate(events_list, 1):
        for tag in event.tags().to_vec():
            tag_vec = tag.as_vec()
            if tag_vec and tag_vec[0] == 'r' and len(tag_vec) > 1:
                relay_url = tag_vec[1]
                if relay_url.startswith('ws://') or relay_url.startswith('wss://'):
                    unique_relays.add(relay_url)
        if idx % 500 == 0:
            print(f"Processed {idx} notes...")

    print(f"Found {len(unique_relays)} unique relay URLs referenced in notes.")
    with open(OUTPUT_FILE, 'w') as f:
        for relay in sorted(unique_relays):
            f.write(relay + '\n')
    print(f"Relay list written to {OUTPUT_FILE}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(extract_relays_from_relays()) 