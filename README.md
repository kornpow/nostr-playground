# Nostr Playground

A collection of Python scripts for interacting with the Nostr protocol. These tools help you explore, query, and manage Nostr relays and events.

## 🚀 Quick Start

All scripts use `uv` for dependency management. Run any script with:

```bash
uv run <script_name>.py [options]
```

## 📁 Scripts Overview

#### `hello.py` - Basic Nostr Connection & Event Monitoring
- **Purpose**: Basic connection to Nostr relays and real-time event monitoring
- **Usage**: `uv run hello.py`
- **Features**: 
  - Connects to multiple relays (damus.io, denver.space)
  - Monitors events from the last 24 hours
  - Displays event statistics by kind
  - Real-time event streaming with interrupt handling

#### `query_relay.py` - Advanced Relay Querying
- **Purpose**: Query relays with custom filters
- **Usage**: `uv run query_relay.py --relay wss://relay.damus.io --kinds 1 --limit 10`
- **Features**:
  - Custom filter creation (kinds, authors, time ranges, event IDs)
  - JSON output support
  - Count-only mode
  - Flexible timeout settings

#### `get_latest_posts.py` - Fetch Latest Posts from Relay
- **Purpose**: Get the latest posts from any relay
- **Usage**: `uv run get_latest_posts.py wss://nos.lol --limit 50`
- **Features**:
  - Fetch up to 200 latest posts (configurable)
  - Content preview or full content display
  - JSON export capability
  - Quiet mode for scripting

#### `decode_nevent.py` - Decode Nostr Event Identifiers
- **Purpose**: Decode nevent bech32 strings according to NIP-19
- **Usage**: `uv run decode_nevent.py nevent1abc...`
- **Features**:
  - Supports complex nevent formats with TLV encoding
  - Handles simple hex event IDs
  - Extracts relay URLs, authors, and event metadata
  - Detailed decoding information

#### `find_note_relays.py` - Find Notes Across Multiple Relays
- **Purpose**: Check if a specific note exists on multiple relays
- **Usage**: `uv run find_note_relays.py <event_id> --relays wss://relay1 wss://relay2`
- **Features**:
  - Search across multiple relays simultaneously
  - JSON output for integration
  - Detailed error reporting
  - Single relay or batch relay searching

#### `republish_note_to_relay.py` - Republish Notes to Relays
- **Purpose**: Republish notes to relays where they're missing
- **Usage**: `uv run republish_note_to_relay.py <event_id> --all-relays --relay-file relays.txt`
- **Features**:
  - Fetch notes from source relays
  - Publish to target relays where missing
  - Support for nevent strings and event IDs
  - Batch relay publishing with detailed results

#### `extract_relays_from_notes.py` - Extract Relay URLs from Notes
- **Purpose**: Extract unique relay URLs referenced in notes
- **Usage**: `uv run extract_relays_from_notes.py`
- **Features**:
  - Scans thousands of notes across multiple relays
  - Extracts 'r' tags containing relay URLs
  - Outputs unique relay list to `relays_extracted.txt`
  - Configurable note limits and timeouts

#### `debug_connection.py` - Simple Connection Test
- **Purpose**: Basic connection testing to relays
- **Usage**: `uv run debug_connection.py`
- **Features**:
  - Simple relay connection test
  - Fetch a few events to verify connectivity
  - Basic event display

#### `like_post.py` - Like Posts Using Nostr Protocol
- **Purpose**: Create kind 7 reaction events to like posts
- **Usage**: `uv run like_post.py <event_id> --keys keys.txt`
- **Features**:
  - Like posts with custom reaction content (default: "+")
  - Unlike posts by sending empty reactions
  - Automatic key generation and management
  - Publish to multiple relays with detailed results
  - Support for custom reaction emojis and text

#### `convert_nsec.py` - Convert NSEC to Hex Private Key
- **Purpose**: Convert nsec bech32 format to hex private key
- **Usage**: `uv run convert_nsec.py --output keys.txt`
- **Features**:
  - Interactive input with hidden nsec for security
  - Decode nsec bech32 strings according to NIP-19
  - Convert to hex format for use with other scripts
  - Automatic keys.txt file generation with proper formatting
  - Display both public and private key information
  - Support for custom output files

#### `generate_nsec.py` - Generate New NSEC Keys
- **Purpose**: Generate new nsec bech32 keys for Nostr
- **Usage**: `uv run generate_nsec.py --output keys.txt`
- **Features**:
  - Generate cryptographically secure key pairs
  - Output in both bech32 (nsec/npub) and hex formats
  - Automatic keys.txt file generation with proper formatting
  - Security warnings and best practices
  - Support for hex-only output mode

## 🛠️ **Common Use Cases**

### 1. **Explore a Relay**
```bash
# Get latest 50 posts from a relay
uv run get_latest_posts.py wss://nos.lol --limit 50

# Query specific content types
uv run query_relay.py --relay wss://relay.damus.io --kinds 1 --limit 20
```

### 2. **Find a Specific Note**
```bash
# Search for a note across multiple relays
uv run find_note_relays.py 33f97eceb1e962f06bd4faf93a00dcac3cd55e43074549708f4c157d5a8c0fbc

# Search on a single relay
uv run find_note_relays.py <event_id> --single-relay wss://nos.lol
```

### 3. **Republish Content**
```bash
# Republish a note to all relays in a file
uv run republish_note_to_relay.py <event_id> --all-relays --relay-file relays_extracted.txt

# Republish to specific relays
uv run republish_note_to_relay.py <event_id> --target-relays wss://relay1 wss://relay2
```

### 4. **Extract Relay Information**
```bash
# Extract relay URLs from notes
uv run extract_relays_from_notes.py

# Decode a nevent
uv run decode_nevent.py nevent1abc...
```

### 5. **Like Posts**
```bash
# Like a post with default "+" reaction
uv run like_post.py 33f97eceb1e962f06bd4faf93a00dcac3cd55e43074549708f4c157d5a8c0fbc

# Like with custom reaction
uv run like_post.py <event_id> --content "❤️"

# Unlike a post
uv run like_post.py <event_id> --unlike

# Use custom relays
uv run like_post.py <event_id> --relays wss://relay1 wss://relay2
```

### 6. **Generate and Convert NSEC Keys**
```bash
# Generate new nsec keys and save to keys.txt
uv run generate_nsec.py --output keys.txt

# Generate keys and display only (don't save)
uv run generate_nsec.py --no-save

# Generate keys in hex format only
uv run generate_nsec.py --hex-only

# Convert existing nsec to hex and save to keys.txt (interactive)
uv run convert_nsec.py --output keys.txt

# Convert nsec and display only (don't save)
uv run convert_nsec.py --no-save

# Convert nsec to custom filename
uv run convert_nsec.py --output my_keys.txt
```
