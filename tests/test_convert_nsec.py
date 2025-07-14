#!/usr/bin/env python3
"""
Pytest tests for convert_nsec.py
"""

import os
import sys
import tempfile

import pytest

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from convert_nsec import decode_nsec
from utils import save_to_keys_file


class TestDecodeNsec:
    """Test class for decode_nsec function."""

    def test_valid_nsec(self):
        """Test decoding a valid nsec."""
        valid_nsec = "nsec1rfm0pj9apnrpk9xzz7symsa2nh3xauer9e843qcpm3gaujr28xds6ujqmt"
        result = decode_nsec(valid_nsec)

        assert result["success"] is True
        assert result["nsec"] == valid_nsec
        assert (
            result["private_key_hex"]
            == "1a76f0c8bd0cc61b14c217a04dc3aa9de26ef3232e4f588301dc51de486a399b"
        )
        assert (
            result["public_key_hex"]
            == "7721efd05ff6608eba4887b05361acb7d241c6aa5d6919c86459d54c2a7c0d12"
        )
        assert (
            result["public_key_bech32"]
            == "npub1wus7l5zl7esgawjgs7c9xcdvklfyr342t453njryt825c2nup5fq2nn0fn"
        )
        assert result["error"] is None

    def test_invalid_nsec_format(self):
        """Test decoding an invalid nsec format."""
        invalid_nsec = "invalid_nsec"
        result = decode_nsec(invalid_nsec)

        assert result["success"] is False
        assert "Invalid nsec format" in result["error"]

    def test_npub_instead_of_nsec(self):
        """Test passing an npub instead of nsec."""
        npub = "npub1wus7l5zl7esgawjgs7c9xcdvklfyr342t453njryt825c2nup5fq2nn0fn"
        result = decode_nsec(npub)

        assert result["success"] is False
        assert "Invalid nsec format" in result["error"]

    def test_invalid_bech32(self):
        """Test decoding invalid bech32 string."""
        invalid_bech32 = "nsec1invalid"
        result = decode_nsec(invalid_bech32)

        assert result["success"] is False
        assert "Failed to decode bech32 string" in result["error"]

    def test_empty_string(self):
        """Test decoding empty string."""
        result = decode_nsec("")

        assert result["success"] is False
        assert "Invalid nsec format" in result["error"]

    def test_short_nsec(self):
        """Test decoding too short nsec."""
        short_nsec = "nsec1"
        result = decode_nsec(short_nsec)

        assert result["success"] is False
        assert "Failed to decode bech32 string" in result["error"]


class TestSaveToKeysFile:
    """Test class for save_to_keys_file function."""

    def test_save_valid_key(self):
        """Test saving a valid private key to file."""
        test_hex = "1a76f0c8bd0cc61b14c217a04dc3aa9de26ef3232e4f588301dc51de486a399b"

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
            temp_filename = temp_file.name

        try:
            result = save_to_keys_file(test_hex, temp_filename)

            assert result is True
            assert os.path.exists(temp_filename)

            # Verify file contents
            with open(temp_filename) as f:
                content = f.read()
                assert test_hex in content
                assert "# Sample private key file" in content
                assert "IMPORTANT: Keep this file secure" in content
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_save_to_invalid_path(self):
        """Test saving to an invalid file path."""
        test_hex = "1a76f0c8bd0cc61b14c217a04dc3aa9de26ef3232e4f588301dc51de486a399b"
        invalid_path = "/invalid/path/that/does/not/exist.txt"

        result = save_to_keys_file(test_hex, invalid_path)
        assert result is False


class TestFullWorkflow:
    """Test class for the complete workflow."""

    def test_nsec_to_keys_file_workflow(self):
        """Test the complete workflow from nsec to keys file."""
        test_nsec = "nsec1rfm0pj9apnrpk9xzz7symsa2nh3xauer9e843qcpm3gaujr28xds6ujqmt"

        # Step 1: Decode nsec
        decode_result = decode_nsec(test_nsec)
        assert decode_result["success"] is True

        # Step 2: Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as temp_file:
            temp_filename = temp_file.name

        try:
            save_result = save_to_keys_file(decode_result["private_key_hex"], temp_filename)
            assert save_result is True

            # Step 3: Verify file contents
            with open(temp_filename) as f:
                content = f.read()
                assert decode_result["private_key_hex"] in content

                # Find the actual key line (non-comment)
                lines = f.readlines()
                f.seek(0)  # Reset file pointer
                lines = f.readlines()

                key_lines = [
                    line.strip()
                    for line in lines
                    if not line.strip().startswith("#") and line.strip()
                ]
                assert len(key_lines) == 1
                assert key_lines[0] == decode_result["private_key_hex"]

        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)


# Test fixtures for reusable test data
@pytest.fixture
def valid_nsec():
    """Fixture providing a valid nsec for testing."""
    return "nsec1rfm0pj9apnrpk9xzz7symsa2nh3xauer9e843qcpm3gaujr28xds6ujqmt"


@pytest.fixture
def expected_private_key_hex():
    """Fixture providing the expected private key hex for the test nsec."""
    return "1a76f0c8bd0cc61b14c217a04dc3aa9de26ef3232e4f588301dc51de486a399b"


@pytest.fixture
def expected_public_key_hex():
    """Fixture providing the expected public key hex for the test nsec."""
    return "7721efd05ff6608eba4887b05361acb7d241c6aa5d6919c86459d54c2a7c0d12"


@pytest.fixture
def expected_npub():
    """Fixture providing the expected npub for the test nsec."""
    return "npub1wus7l5zl7esgawjgs7c9xcdvklfyr342t453njryt825c2nup5fq2nn0fn"


def test_decode_nsec_with_fixtures(
    valid_nsec, expected_private_key_hex, expected_public_key_hex, expected_npub
):
    """Test decode_nsec using fixtures."""
    result = decode_nsec(valid_nsec)

    assert result["success"] is True
    assert result["private_key_hex"] == expected_private_key_hex
    assert result["public_key_hex"] == expected_public_key_hex
    assert result["public_key_bech32"] == expected_npub
