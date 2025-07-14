#!/usr/bin/env python3
"""
Nostr Note Finder - Find a specific note on multiple relays

This script queries multiple Nostr relays to check if they have a specific note ID.
"""

import asyncio
from datetime import datetime, timedelta
from nostr_sdk import Client, Filter, EventId
from utils import format_timestamp

def print_note_details(event):
    """Print note details in a readable format."""
    print("\n" + "="*80)
    print(f"Note ID: {event.id()}")
    print(f"Time: {format_timestamp(event.created_at().as_secs())}")
    print(f"Kind: {event.kind()}")
    
    # Print content if present and not empty
    content = event.content()
    if content:
        print("\nContent:")
        print(f"{content[:500]}...")  # Limit content length
    
    print("="*80)

async def find_note_on_relay(note_id: str, relay_url: str, timeout: int = 10):
    """
    Search for a note ID on a single relay using proper ID filtering.
    
    Args:
        note_id: The note ID to search for (hex format)
        relay_url: The relay URL to search
        timeout: Timeout in seconds for the connection
    
    Returns:
        Dict with results: {'found': bool, 'event': Event or None, 'error': str or None}
    """
    print(f"Searching for note ID: {note_id}")
    print(f"Checking relay: {relay_url}")
    print("-" * 60)
    
    client = Client()
    
    try:
        # Add relay and connect
        await client.add_relay(relay_url)
        await client.connect()
        
        # Create filter with specific event ID
        try:
            event_id = EventId.parse(note_id)
            filter_obj = Filter().ids([event_id])
        except Exception as e:
            print(f"Error parsing event ID '{note_id}': {e}")
            return {'found': False, 'event': None, 'error': f"Invalid event ID: {e}"}
        
        # Fetch events with timeout
        events = await client.fetch_events(filter_obj, timedelta(seconds=timeout))
        events_list = events.to_vec()
        
        if events_list:
            found_event = events_list[0]  # Should only be one event with specific ID
            print(f"✅ FOUND on {relay_url}")
            print_note_details(found_event)
            return {'found': True, 'event': found_event, 'error': None}
        else:
            print(f"❌ Not found on {relay_url}")
            return {'found': False, 'event': None, 'error': None}
        
    except Exception as e:
        error_msg = f"Error connecting to {relay_url}: {str(e)}"
        print(f"⚠️  Error: {error_msg}")
        return {'found': False, 'event': None, 'error': error_msg}
    
    finally:
        try:
            await client.disconnect()
        except:
            pass

async def find_note_on_multiple_relays(note_id: str, relay_urls: list, timeout: int = 10):
    """
    Search for a note ID on multiple relays.
    
    Args:
        note_id: The note ID to search for (hex format)
        relay_urls: List of relay URLs to search
        timeout: Timeout in seconds for each connection
    
    Returns:
        Dict with results: {'found': bool, 'event': Event or None, 'relay': str or None, 'errors': list}
    """
    print(f"Searching for note ID: {note_id}")
    print(f"Checking {len(relay_urls)} relays...")
    print("=" * 80)
    
    found_event = None
    found_relay = None
    errors = []
    
    for i, relay_url in enumerate(relay_urls, 1):
        print(f"\n[{i}/{len(relay_urls)}] Checking {relay_url}")
        
        result = await find_note_on_relay(note_id, relay_url, timeout)
        
        if result['found']:
            found_event = result['event']
            found_relay = relay_url
            print(f"✅ Found on {relay_url}")
        elif result['error']:
            errors.append(f"{relay_url}: {result['error']}")
    
    # Continue searching all relays to see availability
    
    return {
        'found': found_event is not None,
        'event': found_event,
        'relay': found_relay,
        'errors': errors
    }

async def main():
    """Main function to run the note finder."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Find a specific note ID on multiple Nostr relays')
    parser.add_argument('note_id', help='The note ID to search for (hex format)')
    parser.add_argument('--relays', nargs='+', 
                       default=['wss://relay.damus.io', 'wss://nos.lol', 'wss://relay.snort.social'],
                       help='Relay URLs to check (default: damus.io, nos.lol, snort.social)')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds for each relay (default: 10)')
    parser.add_argument('--single-relay', help='Search only on a single relay (overrides --relays)')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Output file path for JSON results (requires --json)')
    
    args = parser.parse_args()
    
    # Validate note ID format (should be 64 character hex string)
    if len(args.note_id) != 64 or not all(c in '0123456789abcdef' for c in args.note_id.lower()):
        print("Error: Note ID should be a 64-character hexadecimal string")
        return
    
    # Determine which relays to check
    if args.single_relay:
        relay_urls = [args.single_relay]
    else:
        relay_urls = args.relays
    
    # Run the search
    found_relays = []
    not_found_relays = []
    all_errors = []
    
    if len(relay_urls) == 1:
        # Single relay search
        result = await find_note_on_relay(args.note_id, relay_urls[0], args.timeout)
        found = result['found']
        event = result['event']
        relay = relay_urls[0] if found else None
        errors = [result['error']] if result['error'] else []
        if found:
            found_relays.append(relay_urls[0])
        else:
            not_found_relays.append(relay_urls[0])
        if errors:
            all_errors.extend(errors)
    else:
        # Multiple relay search
        found = False
        event = None
        relay = None
        errors = []
        for relay_url in relay_urls:
            result = await find_note_on_relay(args.note_id, relay_url, args.timeout)
            if result['found']:
                found_relays.append(relay_url)
                if not found:
                    found = True
                    event = result['event']
                    relay = relay_url
            else:
                not_found_relays.append(relay_url)
            if result['error']:
                all_errors.append(f"{relay_url}: {result['error']}")
    
    # Print summary
    if args.json:
        import json as _json
        output = {
            'note_id': args.note_id,
            'found_relays': found_relays,
            'not_found_relays': not_found_relays,
            'errors': all_errors
        }
        if event:
            output['event'] = {
                'id': str(event.id()),
                'created_at': format_timestamp(event.created_at().as_secs()),
                'kind': str(event.kind()),
                'content': event.content()
            }
        
        json_output = _json.dumps(output, indent=2)
        
        if args.output:
            # Write to file
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"JSON results saved to: {args.output}")
        else:
            # Print to stdout
            print(json_output)
        return
    
    print("\n" + "="*80)
    print("SEARCH SUMMARY")
    print("="*80)
    
    if found:
        print(f"✅ Note found on {relay}")
        print(f"  ID: {event.id()}")
        print(f"  Created: {format_timestamp(event.created_at().as_secs())}")
        print(f"  Kind: {event.kind()}")
        content = event.content()
        if content:
            print(f"  Content preview: {content[:100]}...")
    else:
        print(f"❌ Note not found on any of the {len(relay_urls)} relays checked")
        if errors:
            print(f"  Errors encountered:")
            for error in errors:
                print(f"    - {error}")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main()) 