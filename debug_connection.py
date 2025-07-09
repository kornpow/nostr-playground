#!/usr/bin/env python3
import asyncio
from datetime import timedelta
from nostr_sdk import Client, Filter, Kind, KindStandard

async def main():
    client = Client()
    await client.add_relay("wss://relay.damus.io")
    await client.connect()
    print("Connected to relay.damus.io")

    kind_text_note = Kind.from_std(KindStandard.TEXT_NOTE)
    filter_obj = Filter().kinds([kind_text_note]).limit(3)

    events = await client.fetch_events(filter_obj, timedelta(seconds=10))
    events_list = events.to_vec()
    print(f"Received {len(events_list)} events:")
    for event in events_list:
        print(f"ID: {event.id()}")
        print(f"Content: {event.content()[:100]}...")
        print("-" * 40)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main()) 