from nostr_sdk import (
    Client,
    Event,
    EventBuilder,
    EventId,
    Filter,
    Keys,
    Metadata,
    NostrSigner,
    PublicKey,
    Tag,
    Timestamp,
    ZapRequestData,
    ZapType,
)

classes_to_introspect = {
    "Keys": Keys,
    "Client": Client,
    "Filter": Filter,
    "EventBuilder": EventBuilder,
    "NostrSigner": NostrSigner,
    "Event": Event,
    "EventId": EventId,
    "PublicKey": PublicKey,
    "Tag": Tag,
    "ZapRequestData": ZapRequestData,
    "ZapType": ZapType,
    "Metadata": Metadata,
    "Timestamp": Timestamp,
}

for name, cls in classes_to_introspect.items():
    print(f"--- {name} ---")
    print(dir(cls))
    print("\n")
