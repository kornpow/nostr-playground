#!/usr/bin/env python3
"""
Nostr Note Republisher - Republish a note to relays where it's missing

This script takes a nevent or event ID, fetches the event details from relays where it exists,
and publishes it to relays where it's missing.
"""

import asyncio
import json
import argparse
from datetime import datetime, timedelta
from nostr_sdk import Client, Filter, EventId, Keys, Event, Kind, KindStandard

def format_timestamp(timestamp):
    """Convert unix timestamp to readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def load_relays_from_file(filename: str):
    """Load relay URLs from a text file."""
    try:
        with open(filename, 'r') as f:
            relays = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return relays
    except FileNotFoundError:
        print(f"❌ Relay file not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error reading relay file {filename}: {e}")
        return []

async def fetch_event_from_relays(event_id: str, relay_urls: list, timeout: int = 10):
    """
    Fetch an event from multiple relays and return the complete Event object.
    
    Args:
        event_id: The event ID to fetch
        relay_urls: List of relay URLs to try
        timeout: Timeout in seconds for each connection
    
    Returns:
        Event object or None if not found
    """
    print(f"Fetching event {event_id} from relays...")
    
    for relay_url in relay_urls:
        print(f"Trying {relay_url}...")
        
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
                
                await client.disconnect()
                return event
                
        except Exception as e:
            print(f"⚠️  Error on {relay_url}: {e}")
        finally:
            try:
                await client.disconnect()
            except:
                pass
    
    print("❌ Event not found on any of the provided relays")
    return None

async def publish_event_to_relays(event: Event, relay_urls: list, timeout: int = 10):
    """
    Publish an event to multiple relays, printing detailed relay responses and errors.
    
    Args:
        event: The Event object to publish
        relay_urls: List of relay URLs to publish to
        timeout: Timeout in seconds for each connection
    
    Returns:
        Dict with results: {'success': list, 'failed': list, 'errors': list}
    """
    print(f"Publishing event to {len(relay_urls)} relays...")
    print(f"Event ID: {event.id()}")
    print(f"Author: {event.author()}")
    
    success_relays = []
    failed_relays = []
    errors = []
    
    for i, relay_url in enumerate(relay_urls, 1):
        print(f"\n[{i}/{len(relay_urls)}] Publishing to {relay_url}")
        
        client = Client()
        try:
            await client.add_relay(relay_url)
            await client.connect()
            
            # Send the event as-is and capture the response
            try:
                response = await client.send_event(event)
                print(f"Relay response: {response}")
                # Try to parse the response for success/failed relays
                # The response is expected to have .success and .failed attributes (dicts or lists)
                relay_success = False
                relay_error = None
                if hasattr(response, 'success') and hasattr(response, 'failed'):
                    # response.success is a list of relays that accepted the event
                    # response.failed is a dict of relays to error messages
                    if relay_url in getattr(response, 'success', []):
                        relay_success = True
                    elif relay_url in getattr(response, 'failed', {}):
                        relay_error = getattr(response, 'failed')[relay_url]
                if relay_success:
                    print(f"✅ Published to {relay_url}")
                    success_relays.append(relay_url)
                else:
                    error_msg = relay_error or 'Relay did not accept event (no explicit error)'
                    print(f"❌ Failed to publish to {relay_url}: {error_msg}")
                    failed_relays.append(relay_url)
                    errors.append(f"{relay_url}: {error_msg}")
            except Exception as e:
                print(f"❌ Exception while sending event: {e}")
                failed_relays.append(relay_url)
                errors.append(f"{relay_url}: Exception - {e}")
            
        except Exception as e:
            error_msg = f"Error connecting to {relay_url}: {str(e)}"
            print(f"❌ {error_msg}")
            failed_relays.append(relay_url)
            errors.append(error_msg)
        finally:
            try:
                await client.disconnect()
            except Exception as e:
                print(f"Warning: Error disconnecting from {relay_url}: {e}")
    
    return {
        'success': success_relays,
        'failed': failed_relays,
        'errors': errors
    }

async def republish_from_json(json_file: str, timeout: int = 10):
    """
    Republish an event based on JSON results from find_note_relays.py.
    
    Args:
        json_file: Path to JSON file with relay results
        timeout: Timeout in seconds for each connection
    """
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        note_id = data['note_id']
        not_found_relays = data['not_found_relays']
        
        print(f"Fetching event {note_id} to republish to {len(not_found_relays)} relays")
        print(f"Target relays: {not_found_relays}")
        
        # First, fetch the event from a relay where it exists
        source_relays = ['wss://relay.damus.io', 'wss://nos.lol', 'wss://relay.snort.social']
        event = await fetch_event_from_relays(note_id, source_relays, timeout)
        
        if not event:
            print("❌ Could not fetch event from any source relay")
            return
        
        # Publish to missing relays
        result = await publish_event_to_relays(event, not_found_relays, timeout)
        
        # Print results
        print("\n" + "="*80)
        print("REPUBLISH RESULTS")
        print("="*80)
        
        if result['success']:
            print(f"✅ Successfully published to {len(result['success'])} relays:")
            for relay in result['success']:
                print(f"  - {relay}")
        
        if result['failed']:
            print(f"❌ Failed to publish to {len(result['failed'])} relays:")
            for relay in result['failed']:
                print(f"  - {relay}")
        
        if result['errors']:
            print(f"Errors:")
            for error in result['errors']:
                print(f"  - {error}")
        
        print("="*80)
        
    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_file}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON file: {json_file}")
    except Exception as e:
        print(f"❌ Error processing JSON file: {e}")

async def main():
    """Main function to run the note republisher."""
    parser = argparse.ArgumentParser(description='Republish a Nostr note to relays where it\'s missing')
    parser.add_argument('input', help='Event ID, nevent string, or JSON file path')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    parser.add_argument('--source-relays', nargs='+', 
                       default=['wss://relay.damus.io', 'wss://nos.lol', 'wss://relay.snort.social'],
                       help='Relays to fetch event from (default: damus.io, nos.lol, snort.social)')
    parser.add_argument('--target-relays', nargs='+', help='Specific relays to publish to (overrides JSON)')
    parser.add_argument('--all-relays', action='store_true', help='Publish to all relays in relays.txt file')
    parser.add_argument('--relay-file', default='relays.txt', help='File containing relay list (default: relays.txt)')
    
    args = parser.parse_args()
    
    # Check if input is a JSON file
    if args.input.endswith('.json'):
        await republish_from_json(args.input, args.timeout)
        return
    
    # Handle nevent or event ID
    event_id = args.input
    if event_id.startswith('nevent1'):
        # Decode nevent to get event ID
        from decode_nevent import decode_nevent
        result = decode_nevent(event_id)
        if result['success'] and 'event_id_hex' in result:
            event_id = result['event_id_hex']
        else:
            print(f"❌ Failed to decode nevent: {result.get('error', 'Unknown error')}")
            return
    
    # Fetch event
    event = await fetch_event_from_relays(event_id, args.source_relays, args.timeout)
    if not event:
        print("❌ Could not fetch event")
        return
    
    # Determine target relays
    if args.all_relays:
        # Load all relays from file
        target_relays = load_relays_from_file(args.relay_file)
        if not target_relays:
            print("❌ No relays loaded from file")
            return
        print(f"Loaded {len(target_relays)} relays from {args.relay_file}")
    elif args.target_relays:
        target_relays = args.target_relays
    else:
        # Use default relays for testing
        target_relays = ['wss://relay.current.fyi', 'wss://relay.plebstr.com']
        print(f"Using default target relays: {target_relays}")
    
    # Publish to target relays
    result = await publish_event_to_relays(event, target_relays, args.timeout)
    
    # Print results
    print("\n" + "="*80)
    print("PUBLISH RESULTS")
    print("="*80)
    
    if result['success']:
        print(f"✅ Successfully published to {len(result['success'])} relays:")
        for relay in result['success']:
            print(f"  - {relay}")
    
    if result['failed']:
        print(f"❌ Failed to publish to {len(result['failed'])} relays:")
        for relay in result['failed']:
            print(f"  - {relay}")
    
    if result['errors']:
        print(f"Errors:")
        for error in result['errors']:
            print(f"  - {error}")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main()) 