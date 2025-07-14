#!/usr/bin/env python3
"""
Nostr Post Liker - Like posts using Nostr protocol

This script creates kind 7 events (reactions) to like posts on Nostr relays.
According to NIP-25, reactions are kind 7 events that reference other events.
"""

import argparse
import asyncio
from datetime import timedelta

from nostr_sdk import Client, EventBuilder, EventId, Filter, Keys, NostrSigner
from utils import format_timestamp, load_keys_from_file


async def fetch_event_by_id(event_id: str, relay_url: str, timeout: int = 10):
    """
    Fetch a specific event by ID from a relay.

    Args:
        event_id: The event ID to fetch
        relay_url: The relay URL to query
        timeout: Timeout in seconds

    Returns:
        Event object or None if not found
    """
    print(f"Fetching event {event_id} from {relay_url}...")

    client = Client()
    try:
        await client.add_relay(relay_url)
        await client.connect()

        # Create filter for the specific event
        event_id_obj = EventId.parse(event_id)
        filter_obj = Filter().ids([event_id_obj])

        # Fetch the event
        events = await client.fetch_events(filter_obj, timedelta(seconds=timeout))
        events_list = events.to_vec()

        if events_list:
            event = events_list[0]
            print(f"✅ Found event on {relay_url}")
            print(f"Event ID: {event.id()}")
            print(f"Author: {event.author()}")
            print(f"Created: {format_timestamp(event.created_at().as_secs())}")
            print(f"Kind: {event.kind()}")
            print(f"Content preview: {event.content()[:100]}...")
            return event
        else:
            print(f"❌ Event not found on {relay_url}")
            return None

    except Exception as e:
        print(f"⚠️  Error on {relay_url}: {e}")
        return None
    finally:
        try:
            await client.disconnect()
        except Exception:
            pass


async def create_like_event(
    keys: Keys, target_event: any, content: str = "+", relay_urls: list = None
):
    """
    Create a like event (kind 7) that references the target event.

    Args:
        keys: The user's keys for signing
        target_event: The event to like
        content: The reaction content (default: "+" for like)
        relay_urls: List of relay URLs to publish to

    Returns:
        Dict with results: {'success': bool, 'event_id': str, 'errors': list}
    """
    if relay_urls is None:
        relay_urls = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.snort.social",
            "https://bostr.lightningspore.com/",
        ]

    print(f"Creating like event for {target_event.id()}")
    print(f"Reaction content: '{content}'")

    try:
        event_builder = EventBuilder.reaction(target_event, content)
        unsigned_event = event_builder.build(keys.public_key())
        signer = NostrSigner.keys(keys)
        event = await signer.sign_event(unsigned_event)

        print("✅ Created like event")
        print(f"Like event ID: {event.id()}")
        print(f"Author: {event.author()}")
        print(f"Created: {format_timestamp(event.created_at().as_secs())}")

        # Publish to relays
        client = Client()
        success_relays = []
        failed_relays = []
        errors = []

        for relay_url in relay_urls:
            try:
                await client.add_relay(relay_url)
                await client.connect()

                # Send the event
                await client.send_event(event)
                print(f"✅ Published like to {relay_url}")
                success_relays.append(relay_url)

            except Exception as e:
                error_msg = f"Error publishing to {relay_url}: {str(e)}"
                print(f"❌ {error_msg}")
                failed_relays.append(relay_url)
                errors.append(error_msg)
            finally:
                try:
                    await client.disconnect()
                except Exception:
                    pass

        return {
            "success": len(success_relays) > 0,
            "event_id": event.id().to_hex(),
            "success_relays": success_relays,
            "failed_relays": failed_relays,
            "errors": errors,
        }

    except Exception as e:
        error_msg = f"Error creating like event: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "event_id": None,
            "success_relays": [],
            "failed_relays": relay_urls,
            "errors": [error_msg],
        }


async def unlike_post(keys: Keys, target_event_id: str, relay_urls: list = None):
    """
    Unlike a post by creating a kind 7 event with empty content.

    Args:
        keys: The user's keys for signing
        target_event_id: The event ID to unlike
        relay_urls: List of relay URLs to publish to

    Returns:
        Dict with results
    """
    if relay_urls is None:
        relay_urls = [
            "wss://relay.damus.io",
            "wss://nos.lol",
            "wss://relay.snort.social",
        ]

    print(f"Creating unlike event for {target_event_id}")

    try:
        # First fetch the target event to get its author
        target_event = await fetch_event_by_id(target_event_id, relay_urls[0])
        if not target_event:
            return {
                "success": False,
                "event_id": None,
                "success_relays": [],
                "failed_relays": relay_urls,
                "errors": [f"Could not fetch target event {target_event_id}"],
            }

        # Create unlike event with empty content
        return await create_like_event(keys, target_event, "", relay_urls)

    except Exception as e:
        error_msg = f"Error creating unlike event: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "event_id": None,
            "success_relays": [],
            "failed_relays": relay_urls,
            "errors": [error_msg],
        }


async def main():
    """Main function to run the post liker."""
    parser = argparse.ArgumentParser(description="Like posts using Nostr protocol")
    parser.add_argument("event_id", help="Event ID to like (hex format)")
    parser.add_argument(
        "--keys",
        default="keys.txt",
        help="File containing private key (default: keys.txt)",
    )
    parser.add_argument("--content", default="+", help="Reaction content (default: +)")
    parser.add_argument(
        "--unlike", action="store_true", help="Unlike the post (send empty reaction)"
    )
    parser.add_argument(
        "--relays",
        nargs="+",
        default=["wss://relay.damus.io", "wss://nos.lol", "wss://relay.snort.social"],
        help="Relay URLs to publish to",
    )
    parser.add_argument("--timeout", type=int, default=10, help="Timeout in seconds (default: 10)")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")

    args = parser.parse_args()

    # Load or generate keys
    keys = load_keys_from_file(args.keys)
    if not keys:
        print("❌ Failed to load or generate keys")
        return

    if not args.quiet:
        print(f"🔑 Using public key: {keys.public_key().to_hex()}")
        print(f"🎯 Target event: {args.event_id}")
        print(f"📡 Publishing to {len(args.relays)} relays")

    # Validate event ID format
    try:
        EventId.parse(args.event_id)
    except Exception as e:
        print(f"❌ Invalid event ID format: {e}")
        return

    # Fetch the target event first
    target_event = await fetch_event_by_id(args.event_id, args.relays[0], args.timeout)
    if not target_event:
        print("❌ Could not fetch target event")
        return

    # Create like/unlike event
    if args.unlike:
        result = await unlike_post(keys, args.event_id, args.relays)
    else:
        result = await create_like_event(keys, target_event, args.content, args.relays)

    # Display results
    print("\n" + "=" * 60)
    print("LIKE OPERATION RESULTS")
    print("=" * 60)

    if result["success"]:
        print(f"✅ Successfully {'unliked' if args.unlike else 'liked'} post")
        print(f"Event ID: {result['event_id']}")
        print(f"Successful relays: {len(result['success_relays'])}")
        for relay in result["success_relays"]:
            print(f"  ✅ {relay}")

        if result["failed_relays"]:
            print(f"Failed relays: {len(result['failed_relays'])}")
            for relay in result["failed_relays"]:
                print(f"  ❌ {relay}")
    else:
        print(f"❌ Failed to {'unlike' if args.unlike else 'like'} post")
        for error in result["errors"]:
            print(f"  Error: {error}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
