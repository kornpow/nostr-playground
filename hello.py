from nostr.filter import Filter
from nostr.relay_manager import RelayManager
from nostr.subscription import Subscription
import time
import json
from datetime import datetime

import json
import ssl
import time
from nostr.filter import Filter, Filters
from nostr.event import Event, EventKind
from nostr.relay_manager import RelayManager
from nostr.message_type import ClientMessageType

def get_event_kind_name(kind):
    """Return human readable names for common event kinds."""
    kinds = {
        0: "Metadata",
        1: "Text Note",
        2: "Recommend Relay",
        3: "Contacts",
        4: "Encrypted Direct Messages",
        5: "Event Deletion",
        6: "Repost",
        7: "Reaction",
        40: "Channel Creation",
        41: "Channel Metadata",
        42: "Channel Message",
        43: "Channel Hide Message",
        44: "Channel Mute User"
    }
    return kinds.get(kind, f"Unknown Kind {kind}")

def npub_to_hex(npub):
    """Convert an npub to hex format."""
    hrp, data = bech32_decode(npub)
    if hrp != "npub" or data is None:
        raise ValueError("Invalid npub format")
    decoded = convertbits(data, 5, 8, False)
    if decoded is None:
        raise ValueError("Invalid npub format")
    return bytes(decoded).hex()

def format_timestamp(timestamp):
    """Convert unix timestamp to readable format."""
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def print_event(event):
    """Print event details in a readable format."""
    event_dict = event.to_dict()
    print("\n" + "="*80)
    print(f"Event Kind: {get_event_kind_name(event_dict['kind'])}")
    print(f"Time: {format_timestamp(event_dict['created_at'])}")
    print(f"Author: {event_dict['pubkey']}")
    
    # Print tags if present
    if event_dict['tags']:
        print("\nTags:")
        for tag in event_dict['tags']:
            print(f"  {tag}")
    
    # Print content if present and not empty
    if event_dict['content']:
        print("\nContent:")
        print(f"{event_dict['content'][:500]}...")  # Limit content length
    
    print("="*80)

def main():
    # Create a relay manager
    relay_manager = RelayManager()
        
        # Add relay to connect to
    relay_manager.add_relay("wss://relay.denver.space")
    relay_manager.add_relay("wss://relay.damus.io")

        
        # Open the connection
    relay_manager.open_connections()
    time.sleep(1.25)  # Wait for connection to open
        
        # Create a filter for all events in the last 24 hours
    current_time = int(time.time())
    hours_24 = 24 * 60 * 60  # 24 hours in seconds
    since_time = current_time - hours_24

    filters = Filter(
        since=current_time - hours_24,  # Last 24 hours
        limit=1000  # Limit to prevent overwhelming output
    )
    
    # Subscribe to events
    relay_manager.add_subscription("test123", filters)
    
    # Track event counts by kind
    event_counts = {}
    total_events = 0
    
    print(f"Fetching events from the last 24 hours...")
    print(f"Start time: {format_timestamp(current_time - hours_24)}")
    print(f"End time: {format_timestamp(current_time)}")
    
    print(f"Fetching events from the last 24 hours...")
    print(f"Start time: {format_timestamp(current_time - hours_24)}")
    print(f"End time: {format_timestamp(current_time)}")
    
    try:
        while True:
            # Using the correct method to get messages
            while relay_manager.message_pool.has_notices():
                notice_msg = relay_manager.message_pool.get_notice()
                print(f"Notice: {notice_msg}")

            while relay_manager.message_pool.has_events():
                event_msg = relay_manager.message_pool.get_event()
                event = event_msg.event
                kind = event.kind
                
                event_counts[kind] = event_counts.get(kind, 0) + 1
                total_events += 1
                
                print_event(event)
                
                if total_events % 10 == 0:
                    print("\nCurrent Statistics:")
                    for kind in sorted(event_counts.keys()):
                        print(f"{get_event_kind_name(kind)}: {event_counts[kind]}")
                    print(f"Total events: {total_events}")
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning
                
    except KeyboardInterrupt:
        print("\nClosing connection...")
        relay_manager.close_connections()
        
        print("\nFinal Statistics:")
        for kind in sorted(event_counts.keys()):
            print(f"{get_event_kind_name(kind)}: {event_counts[kind]}")
        print(f"Total events: {total_events}")

def playground():
    current_time = int(time.time())
    hours_24 = 24 * 60 * 60  # 24 hours in seconds
    since_time = current_time - hours_24

    filters = Filters([Filter(kinds=[EventKind.TEXT_NOTE])])
    filters2 = Filters([Filter(since=since_time)])

    subscription_id = "bobaloo2"
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters2.to_json_array())

    relay_manager1 = RelayManager()
    # relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager1.add_relay("wss://relay.denver.space")
    relay_manager1.add_subscription(subscription_id, filters)
    relay_manager1.open_connections({"cert_reqs": ssl.CERT_NONE}) # NOTE: This disables ssl certificate verification
    time.sleep(1.25) # allow the connections to open

    message = json.dumps(request)
    relay_manager1.publish_message(message)
    time.sleep(1) # allow the messages to send

    while relay_manager1.message_pool.has_events():
    event_msg = relay_manager1.message_pool.get_event()
    print(f"Post Time: {datetime.fromtimestamp(event_msg.event.created_at)} --> Message: {event_msg.event.content}")



    relay_manager1.publish_event(send_event)

    vals_npub = "npub184cwc849sejs5pr566zcg4pqn53zzk85q70gmwqx7qt77h3suansvet30s"
    vals_npub_hex = npub_to_hex(vals_npub)
    filters3 = Filters([Filter(authors=[vals_npub])])

    filters3 = Filters([Filter(
        authors=[vals_npub_hex],
        since=current_time - hours_24,
        limit=50  # Limit to last 50 events
    )])

    relay_manager2 = RelayManager()
    # relay_manager.add_relay("wss://nostr-pub.wellorder.net")
    relay_manager2.add_relay("wss://relay.damus.io")

    subscription_id = "test1234"
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters3.to_json_array())
    relay_manager2.add_subscription(subscription_id, filters3)
    relay_manager2.open_connections({"cert_reqs": ssl.CERT_NONE}) # NOTE: This disables ssl certificate verification
    time.sleep(1.25) # allow the connections to open

    message = json.dumps(request)
    relay_manager2.publish_message(message)
    time.sleep(1) # allow the messages to send

    relay_manager1.publish_event(send_event)



    relay_manager1 = RelayManager()
    relay_manager1.add_relay("wss://relay.denver.space")
    relay_manager1.add_subscription("testborg123455", [])
    relay_manager1.open_connections({"cert_reqs": ssl.CERT_NONE}) # NOTE: This disables ssl certificate verification
    time.sleep(1.25) # allow the connections to open

    filters4 = Filters([Filter(
        since=current_time - hours_24,
        limit=50  # Limit to last 50 events
    )])
    request = [ClientMessageType.REQUEST, subscription_id]
    request.extend(filters4.to_json_array())
    message = json.dumps(request)
    relay_manager1.publish_message(message)
    time.sleep(1) # allow the messages to send

    while relay_manager1.message_pool.has_events():
    event_msg = relay_manager1.message_pool.get_event()
    print(f"Post Time: {datetime.fromtimestamp(event_msg.event.created_at)} --> Message: {event_msg.event.content}")


if __name__ == "__main__":
    main()
