#!/usr/bin/env python3
"""
Nostr Relay Query Tool - Query a relay with custom filters

This script allows you to pass in a filter object to query a Nostr relay and get the results.
"""

import asyncio
import json
from datetime import datetime, timedelta
from nostr_sdk import Client, Filter, Kind, KindStandard, EventId

def format_timestamp(timestamp):
    """Convert unix timestamp to readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def print_event_details(event):
    """Print event details in a readable format."""
    print("\n" + "="*80)
    print(f"Event ID: {event.id()}")
    print(f"Time: {format_timestamp(event.created_at().as_secs())}")
    print(f"Kind: {event.kind()}")
    
    # Print content if present and not empty
    content = event.content()
    if content:
        print("\nContent:")
        print(f"{content[:500]}...")  # Limit content length
    
    print("="*80)

def create_filter_from_args(args):
    """Create a filter object from command line arguments."""
    filter_obj = Filter()
    
    if args.kinds:
        kinds = []
        for kind_str in args.kinds:
            try:
                kind_int = int(kind_str)
                if kind_int == 1:
                    kinds.append(Kind.from_std(KindStandard.TEXT_NOTE))
                else:
                    kinds.append(Kind(kind_int))
            except ValueError:
                print(f"Warning: Invalid kind '{kind_str}', skipping")
        if kinds:
            filter_obj = filter_obj.kinds(kinds)
    
    if args.limit:
        filter_obj = filter_obj.limit(args.limit)
    
    if args.since:
        filter_obj = filter_obj.since(args.since)
    
    if args.until:
        filter_obj = filter_obj.until(args.until)
    
    if args.authors:
        filter_obj = filter_obj.authors(args.authors)
    
    if args.ids:
        event_ids = []
        for id_str in args.ids:
            try:
                event_id = EventId.parse(id_str)
                event_ids.append(event_id)
            except Exception as e:
                print(f"Warning: Invalid event ID '{id_str}': {e}, skipping")
        if event_ids:
            filter_obj = filter_obj.ids(event_ids)
    
    return filter_obj

async def query_relay(relay_url: str, filter_obj: Filter, timeout: int = 10):
    """
    Query a relay with a specific filter.
    
    Args:
        relay_url: The relay URL to query
        filter_obj: The filter to apply
        timeout: Timeout in seconds for the connection
    
    Returns:
        Dict with results: {'success': bool, 'events': list, 'error': str or None}
    """
    print(f"Querying relay: {relay_url}")
    print(f"Filter: {filter_obj.as_json()}")
    print("-" * 60)
    
    client = Client()
    
    try:
        # Add relay and connect
        await client.add_relay(relay_url)
        await client.connect()
        
        # Fetch events with timeout
        events = await client.fetch_events(filter_obj, timedelta(seconds=timeout))
        events_list = events.to_vec()
        
        print(f"✅ Found {len(events_list)} events")
        
        # Print event details
        for i, event in enumerate(events_list, 1):
            print(f"\nEvent {i}:")
            print_event_details(event)
        
        return {'success': True, 'events': events_list, 'error': None}
        
    except Exception as e:
        error_msg = f"Error connecting to {relay_url}: {str(e)}"
        print(f"⚠️  Error: {error_msg}")
        return {'success': False, 'events': [], 'error': error_msg}
    
    finally:
        try:
            await client.disconnect()
        except:
            pass

async def main():
    """Main function to run the relay query tool."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Query a Nostr relay with custom filters')
    parser.add_argument('--relay', default='wss://relay.damus.io', help='Relay URL to query (default: wss://relay.damus.io)')
    parser.add_argument('--timeout', type=int, default=10, help='Timeout in seconds (default: 10)')
    
    # Filter options
    parser.add_argument('--kinds', nargs='+', help='Event kinds to filter (e.g., 1 for text notes)')
    parser.add_argument('--limit', type=int, help='Limit number of events returned')
    parser.add_argument('--since', type=int, help='Events since timestamp')
    parser.add_argument('--until', type=int, help='Events until timestamp')
    parser.add_argument('--authors', nargs='+', help='Author public keys to filter')
    parser.add_argument('--ids', nargs='+', help='Event IDs to filter')
    
    # Output options
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--count-only', action='store_true', help='Only show count of events, not details')
    
    args = parser.parse_args()
    
    # Create filter from arguments
    filter_obj = create_filter_from_args(args)
    
    # Run the query
    result = await query_relay(args.relay, filter_obj, args.timeout)
    
    # Print summary
    print("\n" + "="*80)
    print("QUERY SUMMARY")
    print("="*80)
    
    if result['success']:
        events = result['events']
        print(f"✅ Query successful on {args.relay}")
        print(f"  Events found: {len(events)}")
        
        if args.count_only:
            print(f"  Count: {len(events)}")
        elif args.json:
            # Output as JSON
            json_data = []
            for event in events:
                json_data.append({
                    'id': event.id().to_hex(),
                    'created_at': event.created_at().as_secs(),
                    'kind': event.kind().as_u16(),
                    'content': event.content()
                })
            print(json.dumps(json_data, indent=2))
        else:
            print(f"  Events displayed above")
    else:
        print(f"❌ Query failed: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main()) 