### `nostr_sdk.Keys`

The `Keys` class is fundamental to interacting with the Nostr protocol, providing a comprehensive toolkit for cryptographic key management. It enables the generation, parsing, and utilization of key pairs, which are essential for identifying users and signing events. Below is a detailed breakdown of its methods.

#### Methods

*   **`generate()`**: Creates a new, cryptographically secure key pair. This is the standard method for generating a fresh identity on the Nostr network.
    *   **Usage**: `keys = Keys.generate()`

*   **`from_mnemonic(mnemonic)`**: Reconstructs a `Keys` object from a mnemonic phrase. This is useful for users who want to restore their identity from a backup phrase.
    *   **Usage**: `keys = Keys.from_mnemonic("...")`

*   **`parse(secret_key_string)`**: Creates a `Keys` object from a secret key string, which can be in either bech32 (`nsec...`) or hexadecimal format. This method is ideal for loading an existing identity from a stored secret key.
    *   **Usage**: `keys = Keys.parse("nsec1...")`

*   **`public_key()`**: Returns the public key associated with the `Keys` object. The public key is the shareable part of the identity and is used to verify signatures and receive messages.
    *   **Usage**: `public_key = keys.public_key()`
    *   The returned `PublicKey` object has its own methods, such as `to_hex()` and `to_bech32()`, for different representations.

*   **`secret_key()`**: Returns the secret key component of the `Keys` object. The secret key is the confidential part of the identity and must be kept secure.
    *   **Usage**: `secret_key = keys.secret_key()`
    *   Similar to `PublicKey`, the `SecretKey` object provides methods like `to_hex()` and `to_bech32()`.

*   **`sign_schnorr(message)`**: Signs a given message using the Schnorr signature scheme. This is the cryptographic basis for creating valid Nostr events.
    *   **Usage**: `signature = keys.sign_schnorr("message")`

### Interacting with Relays: The `Client` Class

The `Client` class is the primary interface for communicating with Nostr relays. It manages connections, sends and receives events, and handles subscriptions. Since `nostr-sdk` is an asynchronous library, most `Client` methods are coroutines and must be used with `await`.

#### Connection Management

These methods manage the client's connections to relays.

*   `add_relay(relay_url)`: Adds a new relay to the client for both reading and writing.
*   `add_read_relay(relay_url)`: Adds a relay for reading events only.
*   `add_write_relay(relay_url)`: Adds a relay for writing (publishing) events only.
*   `connect()`: Establishes a connection to all relays that have been added.
*   `disconnect()`: Disconnects from all relays.
*   `relays()`: Returns a dictionary of all relays the client is connected to.
*   `remove_relay(relay_url)`: Removes a relay from the client.

#### Fetching Events

These methods are used to query relays for events based on specific criteria.

*   `fetch_events(filter, timeout)`: Fetches a set of events from the connected relays that match the provided `Filter` object. A `timeout` (e.g., `timedelta(seconds=10)`) can be specified.
*   `fetch_events_from(relay_urls, filter, timeout)`: Fetches events that match the `Filter` from a specific list of relays, rather than all connected relays.
*   `fetch_metadata(public_key)`: A specialized method to fetch `kind:0` (metadata) events for a specific `PublicKey`.

#### Subscriptions & Streaming

For real-time event updates, the client uses a subscription model.

*   `subscribe(filter)`: Subscribes to a set of filters, receiving events in real-time as they are published.
*   `unsubscribe()`: Cancels a subscription.
*   `handle_notifications(handler)`: Sets up a handler function to process incoming notifications from relays, which can include events and other notices.

#### Publishing Events

These methods are for creating and publishing events to the network.

*   `send_event(event)`: Sends a signed `Event` to the connected write relays.
*   `send_private_msg(recipient_pubkey, message)`: A convenient way to create and send an encrypted direct message (`kind:4`).
*   `set_metadata(metadata)`: Creates and publishes a `kind:0` event to update the user's profile metadata.

### Filtering Events: The `Filter` Class

The `Filter` class is used to define which events you want to receive from a relay. You create a `Filter` object and then chain its methods to add criteria.

#### Creating a Filter

*   `Filter()`: Creates a new, empty `Filter` object.
    *   **Usage**: `my_filter = Filter()`

#### Filter Methods

You can chain these methods to build your query.

*   `id(event_id)` / `ids(list_of_event_ids)`: Filter by one or more event IDs.
*   `author(public_key)` / `authors(list_of_public_keys)`: Filter by the public key(s) of the event author(s).
*   `kind(kind_number)` / `kinds(list_of_kind_numbers)`: Filter by the event `Kind`.
*   `limit(number)`: Restrict the number of events returned.
*   `since(timestamp)`: Only return events published after a specific `Timestamp`.
*   `until(timestamp)`: Only return events published before a specific `Timestamp`.
*   `search(text)`: Request events that match a simple text search (relay-dependent).
*   `hashtag(tag)` / `hashtags(list_of_tags)`: Filter by `#t` tags.
*   `reference(reference)`/ `references(list_of_references)` Filter by `#e` or `#p` tags.

#### Utility Methods

*   `as_json()`: Returns a JSON representation of the filter, which is what is actually sent to the relay.
    *   **Usage**: `print(my_filter.as_json())`

### Creating and Signing Events: `EventBuilder` and `NostrSigner`

Creating events in `nostr-sdk` is a two-step process: first, an `EventBuilder` is used to construct the event with the correct content and structure (tags), and then a `NostrSigner` is used to sign the event with a user's private key.

### The `EventBuilder` Class

The `EventBuilder` class provides a set of constructor methods that simplify the creation of different event kinds, each corresponding to a specific NIP (Nostr Improvement Proposal).

#### Common Event Types

Here are some of the most common event types you can create:

*   `EventBuilder.text_note(content, tags)`: Creates a standard short text note (`kind:1`). The `tags` parameter is a list of `Tag` objects, which can be used to reference other events or users.
*   `EventBuilder.long_form_text_note(content, tags)`: Creates a long-form content event, or "article" (`kind:30023`). This is for content that wouldn't fit in a standard text note.
*   `EventBuilder.reaction(target_event, content)`: Creates a reaction to another event (`kind:7`), such as a "like" or an emoji response. `target_event` is the `Event` being reacted to.
*   `EventBuilder.repost(target_event)`: Creates a `kind:6` event, which is a "repost" of another user's note.
*   `EventBuilder.delete(list_of_events_to_delete)`: Creates a `kind:5` event, which is a request to relays to delete one or more of the user's past events.
*   `EventBuilder.metadata(metadata_dict)`: Creates a `kind:0` event to set or update a user's profile metadata (name, picture, about, etc.).
*   `EventBuilder.contact_list(list_of_contacts)`: Creates a `kind:3` event which contains a list of public keys that the user's client should follow.

#### Building and Signing

All of these constructor methods return an `EventBuilder` instance. To finalize the event, you must call the `build()` method, which returns an `UnsignedEvent`:

*   `build(public_key)`: Takes the author's `PublicKey` and returns an `UnsignedEvent`, which is ready to be signed.

### The `NostrSigner` Class

The `NostrSigner` is responsible for cryptographically signing an `UnsignedEvent`, which proves that the event was created by the owner of the private key.

#### Creating a Signer

*   `NostrSigner.keys(keys)`: Creates a new signer from a `Keys` object. This is the most common way to create a signer.
    *   **Usage**: `signer = NostrSigner.keys(my_keys)`

#### Signing Methods

*   `sign_event(unsigned_event)`: Takes an `UnsignedEvent` and returns a signed `Event`, which is now ready to be published to relays. This is an `async` method and must be awaited.
    *   **Usage**: `signed_event = await signer.sign_event(unsigned_event)`

### Nostr Data Primitives

These classes represent the fundamental data structures of the Nostr protocol.

### The `Event` Class

The `Event` class represents the core data object in Nostr. All user activities—such as text notes, reactions, and profile updates—are encapsulated in `Event` objects. You will typically receive these objects from relay queries.

*   `id()`: Returns the unique `EventId` of the event.
*   `author()`: Returns the `PublicKey` of the user who created the event.
*   `created_at()`: Returns the `Timestamp` when the event was created.
*   `kind()`: Returns the `Kind` of the event (e.g., `1` for a text note).
*   `tags()`: Returns a list of `Tag` objects associated with the event.
*   `content()`: Returns the content of the event as a string.
*   `signature()`: Returns the `Signature` of the event.
*   `verify()`: Verifies the event's signature and ID, ensuring its integrity.
*   `as_json()`: Returns a JSON representation of the event.

### The `EventId`, `PublicKey`, and `Tag` Classes

These classes represent the core components of an `Event`.

#### `EventId` and `PublicKey`

These classes represent Nostr identifiers and share a similar set of methods for converting between different formats.

*   `parse(string)`: Creates an `EventId` or `PublicKey` object from a string. It can handle both hexadecimal and bech32 (`note...`/`npub...`) formats.
*   `to_hex()`: Returns the identifier as a 64-character hexadecimal string.
*   `to_bech32()`: Returns the identifier in its bech32 format (e.g., `note...` or `npub...`), which is more user-friendly.
*   `to_nostr_uri()`: Returns a full `nostr:` URI for the identifier, which can be used to create client-agnostic links.

#### `Tag`

The `Tag` class is used to add metadata and relationships to an event. A tag is essentially a list of strings, where the first element is the tag name (e.g., "e" for event, "p" for pubkey) and subsequent elements are the tag values.

*   `parse(list_of_strings)`: Creates a `Tag` object from a list of strings.
*   `as_vec()`: Returns the tag as a list of strings, which is its canonical representation.
*   `as_standardized()`: Tries to parse the tag into a more specific, standardized format (like `TagStandard.Event` or `TagStandard.PublicKey`), if it matches a known NIP.

### Zapping: Supporting Creators with Lightning

Zapping is a feature defined in NIP-57 that allows users to send Bitcoin over the Lightning Network to other users as a token of appreciation. The process involves a combination of Nostr events and communication with a Lightning wallet's LNURL service.

The workflow is as follows:

1.  **Fetch the Recipient's Metadata**: First, you must fetch the `kind:0` (metadata) event for the user you wish to zap. This event contains their Lightning Address (`lud16`), which is required to initiate the payment. The `Metadata` class helps parse this information.
    *   **Usage**: `metadata = Metadata.from_json(event.content())`, then access `metadata.get_lud16()`.

2.  **Make Initial LNURL Request**: With the Lightning Address, you make an HTTP GET request to the corresponding LNURL endpoint (e.g., `https://<domain>/.well-known/lnurlp/<user>`). The response from this server will provide a callback URL and confirm that the server supports Nostr zaps (`allowsNostr: true`).

3.  **Create a Zap Request Event**: You then create a `kind:9734` event, which is a formal request for a Lightning invoice. This event is not published to relays but is sent directly to the LNURL server in the next step.
    *   **`ZapRequestData`**: This class is used to structure the data for the zap request.
        *   **Usage**: `zap_data = ZapRequestData(recipient_public_key, list_of_relays)`
        *   You can also set optional fields: `zap_data.message = "..."`, `zap_data.amount = amount_in_millisats`, `zap_data.event_id = id_of_note_being_zapped`.
    *   **`EventBuilder.public_zap_request(zap_data)`**: This builder creates the unsigned `kind:9734` event.

4.  **Sign the Zap Request**: The `UnsignedEvent` from the builder is then signed using a `NostrSigner`, just like any other event.

5.  **Fetch the BOLT11 Invoice**: You make a final HTTP GET request to the `callback` URL from step 2. This request includes the desired amount and the signed, URL-encoded zap request event as query parameters.

6.  **Pay the Invoice**: The server will respond with a BOLT11 invoice (`pr`), which can then be paid by any Lightning wallet to complete the zap. After payment, the recipient's wallet will publish a `kind:9735` (zap receipt) event to the relays specified in the `ZapRequestData`.

### Helper Classes for Zapping

*   **`Metadata`**: A class for parsing and handling `kind:0` events.
    *   `from_json(json_string)`: Creates a `Metadata` object from the content of a `kind:0` event.
    *   `get_lud16()`: Returns the user's Lightning Address (e.g., `user@domain.com`).
    *   `get_lud06()`: Returns a bech32-encoded LNURL string.

*   **`ZapRequestData`**: Structures the information needed to request a zap.
    *   **`__init__(public_key, relays)`**: Creates a zap request for a given `PublicKey`, specifying which `relays` the final receipt should be published to.

*   **`ZapType`**: An enum representing the different types of zaps available.
    *   `PUBLIC`: A public zap, where the `kind:9734` request is a signed, public event. This is the most common type.
    *   `PRIVATE`: The zap request is encrypted.
    *   `ANONYMOUS`: The zap request is unsigned.

*   **`Timestamp`**: A class for working with Unix timestamps.
    *   `now()`: Returns the current time as a `Timestamp` object.
    *   `as_secs()`: Returns the timestamp as an integer number of seconds.
