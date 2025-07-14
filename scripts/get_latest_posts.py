#!/usr/bin/env python3
"""
Nostr Latest Posts Fetcher - Get the latest 200 posts from a specific relay

This script connects to a specified relay and fetches the most recent 200 text notes (kind 1).
"""

import asyncio
import argparse
import json
from datetime import datetime, timedelta
from nostr_sdk import Client, Filter, Kind
from utils import format_timestamp

def truncate_text(text, max_length=200):
    """Truncate text to max_length and add ellipsis if needed."""
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."

async def fetch_latest_posts(relay_url: str, kinds: list[int], limit: int = 200, timeout: int = 30):
    """
    Fetch the latest posts from a specific relay.
    
    Args:
        relay_url: The relay URL to connect to
        limit: Maximum number of posts to fetch (default: 200)
        timeout: Timeout in seconds for the connection
    
    Returns:
        List of event dictionaries with formatted data
    """
    print(f"Connecting to {relay_url}...")
    print(f"Fetching latest {limit} posts...")
    
    client = Client()
    try:
        # Add and connect to the relay
        await client.add_relay(relay_url)
        await client.connect()
        
        # Create filter for kind 1 events (text notes)
        # Order by creation time, newest first
        kinds_to_fetch = [Kind(k) for k in kinds]
        filter_obj = Filter().kinds(kinds_to_fetch).limit(limit)
        
        # Fetch events with timeout
        events = await client.fetch_events(filter_obj, timedelta(seconds=timeout))
        events_list = events.to_vec()
        
        print(f"✅ Found {len(events_list)} posts from {relay_url}")
        
        # Format events for display
        formatted_events = []
        for event in events_list:
            try:
                # Parse content as JSON if it's not a kind 1 event (text note)
                content = event.content()
                event_kind = event.kind().as_u16()
                if event_kind != 1:
                    try:
                        content = json.loads(content)
                    except (json.JSONDecodeError, TypeError):
                        # If it fails to parse, treat as plain text
                        pass

                # Handle tags properly
                try:
                    tags = []
                    event_tags = event.tags()
                    tags_vec = event_tags.to_vec()
                    for tag in tags_vec:
                        try:
                            # Convert tag to list format
                            tag_as_vec = tag.as_vec()
                            tags.append(tag_as_vec)
                        except Exception as e:
                            # Fallback to string representation
                            tags.append(str(tag))
                except Exception as e:
                    tags = []
                
                # Handle signature properly - skip for now to avoid API issues
                sig = "unknown"
                
                formatted_event = {
                    'id': event.id().to_hex(),
                    'author': event.author().to_hex(),
                    'created_at': format_timestamp(event.created_at().as_secs()),
                    'kind': event_kind,
                    'content': content,
                    'content_preview': truncate_text(str(content), 150),
                    'tags': tags,
                    'sig': sig
                }
                formatted_events.append(formatted_event)
                
            except Exception as e:
                print(f"⚠️  Error formatting event {event.id()}: {e}")
                continue
        
        return formatted_events
        
    except Exception as e:
        print(f"❌ Error connecting to {relay_url}: {e}")
        return []
    finally:
        try:
            await client.disconnect()
        except:
            pass

def display_posts(posts, args, show_full_content=False, show_tags=False):
    """
    Display posts in a formatted way.
    
    Args:
        posts: List of formatted post dictionaries
        show_full_content: Whether to show full content or just preview
        show_tags: Whether to show event tags
    """
    if not posts:
        print("No posts found.")
        return
    
    print(f"\n{'='*80}")
    print(f"LATEST {len(posts)} POSTS")
    print(f"\n{'='*80}\n")
    
    for i, post in enumerate(posts, 1):
        if args.raw:
            print(json.dumps(post, indent=2))
            continue
        print(f"[{i}] {post['created_at']}")
        print(f"Author: {post['author']}")
        print(f"Kind: {post['kind']}")
        print(f"ID: {post['id']}")

        if isinstance(post['content'], dict):
            # If content is a dictionary, pretty-print it
            print(json.dumps(post['content'], indent=2, sort_keys=True))
        else:
            # Otherwise, print the text content or its preview
            content_to_display = post['content'] if show_full_content else post['content_preview']
            print(f"Content: {content_to_display}")

        if show_tags and post['tags']:
            print(f"Tags: {post['tags']}")
        
        print("-" * 60)
        print()

def save_to_json(posts, filename):
    """Save posts to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(posts, f, indent=2)
        print(f"✅ Posts saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving to {filename}: {e}")

async def main():
    """Main function to run the latest posts fetcher."""
    parser = argparse.ArgumentParser(description='Fetch the latest posts from a Nostr relay')
    parser.add_argument('relay', help='Relay URL to connect to (e.g., wss://relay.damus.io)')
    parser.add_argument('--limit', type=int, default=200, help='Maximum number of posts to fetch (default: 200)')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout in seconds (default: 30)')
    parser.add_argument('--full-content', action='store_true', help='Show full content instead of preview')
    parser.add_argument('--show-tags', action='store_true', help='Show event tags')
    parser.add_argument('--save-json', help='Save posts to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    parser.add_argument('--kinds', nargs='+', type=int, default=[1], help='Event kinds to filter (default: 1 for text notes)')
    
    parser.add_argument('--raw', action='store_true', help='Print raw event JSON')

    args = parser.parse_args()
    
    # Validate relay URL
    if not args.relay.startswith('wss://'):
        print("❌ Error: Relay URL must start with 'wss://'")
        return
    
    if not args.quiet:
        print(f"🔍 Fetching latest {args.limit} posts from {args.relay}")
        print(f"⏱️  Timeout: {args.timeout} seconds")
    
    # Fetch posts
    posts = await fetch_latest_posts(args.relay, args.kinds, args.limit, args.timeout)
    
    if not posts:
        print("❌ No posts found or connection failed")
        return
    
    # Display posts
    display_posts(posts, args, args.full_content, args.show_tags)
    
    # Save to JSON if requested
    if args.save_json:
        save_to_json(posts, args.save_json)
    
    if not args.quiet:
        print(f"✅ Successfully fetched {len(posts)} posts from {args.relay}")

if __name__ == "__main__":
    asyncio.run(main()) 