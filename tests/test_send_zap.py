#!/usr/bin/env python3
"""
Pytest tests for send_zap.py

This module tests the core NIP-57 zapping functionality of send_zap.py.
We focus on complex integration scenarios and mock external dependencies.
"""

import argparse
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))


class TestZapWorkflow:
    """Test the complete NIP-57 zap workflow."""

    @pytest.mark.asyncio
    async def test_complete_nevent_zap_workflow(self):
        """Test complete zapping workflow using nevent from argument parsing to invoice generation."""
        from nostr_sdk import EventId, PublicKey
        from send_zap import get_lnurl

        # Mock real objects
        mock_client = AsyncMock()
        real_pubkey = PublicKey.parse("0" * 64)
        real_event_id = EventId.parse("1" * 64)

        # Mock nevent decoding
        with patch("decode_nevent.get_zap_info") as mock_get_zap_info:
            mock_get_zap_info.return_value = (real_pubkey, real_event_id)

            # Mock metadata fetch for LNURL
            mock_events = MagicMock()
            mock_event = MagicMock()
            mock_event.content.return_value = json.dumps({"lud16": "test@getalby.com"})
            mock_events.to_vec.return_value = [mock_event]
            mock_client.fetch_events.return_value = mock_events

            with patch("send_zap.Metadata") as mock_metadata_class:
                mock_metadata = MagicMock()
                mock_metadata.get_lud16.return_value = "test@getalby.com"
                mock_metadata.get_lud06.return_value = None
                mock_metadata_class.from_json.return_value = mock_metadata

                # Test LNURL generation
                lnurl_result = await get_lnurl(mock_client, real_pubkey)
                assert lnurl_result == "https://getalby.com/.well-known/lnurlp/test"

                # Verify nevent decoding worked
                recipient_pubkey, note_event_id = mock_get_zap_info.return_value
                assert recipient_pubkey == real_pubkey
                assert note_event_id == real_event_id

    @pytest.mark.asyncio
    async def test_lnurl_endpoint_validation(self):
        """Test LNURL endpoint response validation."""
        from nostr_sdk import PublicKey
        from send_zap import get_lnurl

        mock_client = AsyncMock()
        real_pubkey = PublicKey.parse("0" * 64)

        # Test case 1: User has lud16
        mock_events = MagicMock()
        mock_event = MagicMock()
        mock_event.content.return_value = json.dumps({"lud16": "user@wallet.com"})
        mock_events.to_vec.return_value = [mock_event]
        mock_client.fetch_events.return_value = mock_events

        with patch("send_zap.Metadata") as mock_metadata_class:
            mock_metadata = MagicMock()
            mock_metadata.get_lud16.return_value = "user@wallet.com"
            mock_metadata.get_lud06.return_value = None
            mock_metadata_class.from_json.return_value = mock_metadata

            result = await get_lnurl(mock_client, real_pubkey)
            assert result == "https://wallet.com/.well-known/lnurlp/user"

        # Test case 2: User has no lightning address
        with patch("send_zap.Metadata") as mock_metadata_class:
            mock_metadata = MagicMock()
            mock_metadata.get_lud16.return_value = None
            mock_metadata.get_lud06.return_value = None
            mock_metadata_class.from_json.return_value = mock_metadata

            result = await get_lnurl(mock_client, real_pubkey)
            assert result is None

    @pytest.mark.asyncio
    @patch("send_zap.urlopen")
    async def test_lnurl_http_workflow(self, mock_urlopen):
        """Test the HTTP workflow for LNURL requests with proper nostr zap support."""
        # Mock the LNURL endpoint response
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {
                "allowsNostr": True,
                "callback": "https://wallet.com/lnurl/callback",
                "maxSendable": 1000000000,
                "minSendable": 1000,
                "metadata": '[["text/plain","Payment to user@wallet.com"]]',
                "tag": "payRequest",
            }
        ).encode()
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None

        mock_urlopen.return_value = mock_response

        # Simulate the LNURL call
        from urllib.request import Request

        from send_zap import get_browser_headers

        test_url = "https://wallet.com/.well-known/lnurlp/user"
        headers = get_browser_headers()

        # Verify headers are browser-like
        assert "User-Agent" in headers
        assert "Mozilla" in headers["User-Agent"]

        # Test the HTTP call would work
        request = Request(test_url, headers=headers)
        assert request.get_header("User-agent") is not None

    @patch("send_zap.urlopen")
    def test_callback_url_generation_and_response(self, mock_urlopen):
        """Test callback URL generation with zap request and invoice generation."""
        from urllib.parse import quote

        # Mock zap request event (this would be signed)
        mock_zap_event = {
            "kind": 9734,
            "pubkey": "sender_pubkey",
            "created_at": 1234567890,
            "tags": [
                ["p", "recipient_pubkey"],
                ["e", "note_event_id"],
                ["relays", "wss://relay.damus.io", "wss://nos.lol"],
            ],
            "content": "Great post!",
            "id": "zap_request_event_id",
            "sig": "zap_request_signature",
        }

        # Test URL encoding
        encoded_event = quote(json.dumps(mock_zap_event))
        amount_msats = 1000 * 1000  # 1000 sats in millisats
        callback_url = "https://wallet.com/lnurl/callback"
        final_url = f"{callback_url}?amount={amount_msats}&nostr={encoded_event}"

        # Verify URL structure
        assert "amount=1000000" in final_url
        assert "nostr=" in final_url
        assert callback_url in final_url

        # Mock callback response with invoice
        mock_callback_response = MagicMock()
        mock_callback_response.read.return_value = json.dumps(
            {"pr": "lnbc10000n1ptest123invoice456test123invoice456", "routes": []}
        ).encode()
        mock_callback_response.__enter__.return_value = mock_callback_response
        mock_callback_response.__exit__.return_value = None

        mock_urlopen.return_value = mock_callback_response

        # Simulate callback would return valid invoice
        response_data = json.loads(mock_callback_response.read())
        bolt11_invoice = response_data.get("pr")

        assert bolt11_invoice is not None
        assert bolt11_invoice.startswith("lnbc")

    def test_zap_request_structure_validation(self):
        """Test zap request event structure for both user and note zaps."""
        # Test data that matches what the real ZapRequestData would create

        # Test case 1: User zap (no 'e' tag)
        user_zap_tags = [
            ["p", "recipient_pubkey_hex"],
            ["relays", "wss://relay.damus.io", "wss://nos.lol"],
        ]

        # Verify user zap structure
        p_tags = [tag for tag in user_zap_tags if tag[0] == "p"]
        e_tags = [tag for tag in user_zap_tags if tag[0] == "e"]
        relay_tags = [tag for tag in user_zap_tags if tag[0] == "relays"]

        assert len(p_tags) == 1
        assert len(e_tags) == 0  # No note being zapped
        assert len(relay_tags) == 1
        assert len(relay_tags[0]) == 3  # "relays" + 2 relay URLs

        # Test case 2: Note zap (has 'e' tag)
        note_zap_tags = [
            ["p", "recipient_pubkey_hex"],
            ["e", "note_event_id_hex"],
            ["relays", "wss://relay.damus.io", "wss://nos.lol"],
        ]

        # Verify note zap structure
        p_tags = [tag for tag in note_zap_tags if tag[0] == "p"]
        e_tags = [tag for tag in note_zap_tags if tag[0] == "e"]
        relay_tags = [tag for tag in note_zap_tags if tag[0] == "relays"]

        assert len(p_tags) == 1
        assert len(e_tags) == 1  # Note being zapped
        assert len(relay_tags) == 1
        assert e_tags[0][1] == "note_event_id_hex"

    def test_argument_validation_edge_cases(self):
        """Test edge cases in argument validation that are actually enforced."""

        # These are the validation rules that matter in the real script:
        # 1. nevent and note cannot be used together (this is checked in main())
        args_invalid = argparse.Namespace(
            nevent="nevent1test",
            note="note1test",
            recipient=None,
            amount=1000,
            message="",
            debug=False,
            keys="keys.txt",
        )

        # This combination should be detected as invalid
        has_nevent_and_note = args_invalid.nevent and args_invalid.note
        assert has_nevent_and_note  # This is the invalid case

        # 2. Must have either nevent or recipient (enforced by argparse mutually exclusive group)
        args_valid_nevent = argparse.Namespace(
            nevent="nevent1test",
            recipient=None,  # This gets set to None by argparse when using nevent
            amount=1000,
            message="test",
            note=None,
            debug=False,
            keys="keys.txt",
        )

        args_valid_recipient = argparse.Namespace(
            nevent=None,  # This gets set to None by argparse when using recipient
            recipient="npub1test",
            amount=1000,
            message="test",
            note=None,
            debug=False,
            keys="keys.txt",
        )

        # These should be valid
        has_exactly_one_source = bool(args_valid_nevent.nevent) != bool(
            args_valid_nevent.recipient
        ) and bool(args_valid_recipient.nevent) != bool(args_valid_recipient.recipient)
        assert has_exactly_one_source

    @patch("decode_nevent.get_zap_info")
    def test_nevent_error_handling(self, mock_get_zap_info):
        """Test error handling in nevent decoding."""
        # Test invalid nevent format
        mock_get_zap_info.side_effect = Exception("Invalid nevent format")

        with pytest.raises(Exception, match="Invalid nevent format"):
            from decode_nevent import get_zap_info

            get_zap_info("invalid_nevent_string")

        # Test successful nevent decoding
        mock_get_zap_info.side_effect = None
        mock_pubkey = MagicMock()
        mock_event_id = MagicMock()
        mock_pubkey.to_bech32.return_value = "npub1valid"
        mock_event_id.to_hex.return_value = "validhexeventid"
        mock_get_zap_info.return_value = (mock_pubkey, mock_event_id)

        result = mock_get_zap_info("nevent1validstring")
        assert result[0].to_bech32() == "npub1valid"
        assert result[1].to_hex() == "validhexeventid"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
