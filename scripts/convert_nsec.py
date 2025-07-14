#!/usr/bin/env python3
"""
Nostr NSEC Converter - Convert nsec bech32 to hex private key

This script converts nsec (Nostr secret key) bech32 format to hex format
for use with the Nostr playground scripts.
"""

import argparse
import bech32
import sys
from nostr_sdk import Keys
from utils import save_to_keys_file, decode_bech32_proper

def decode_nsec(nsec_string: str):
    """
    Decode an nsec bech32 string to get the private key.
    
    Args:
        nsec_string: The nsec string to decode
    
    Returns:
        Dict with decoded information
    """
    try:
        # Validate nsec format
        if not nsec_string.startswith('nsec1'):
            return {
                'success': False,
                'error': 'Invalid nsec format. Must start with "nsec1"'
            }
        
        # Decode the bech32 string
        bech32_info = decode_bech32_proper(nsec_string)
        if not bech32_info:
            return {
                'success': False,
                'error': 'Failed to decode bech32 string'
            }
        
        # Validate it's an nsec (should have hrp 'nsec')
        if bech32_info['hrp'] != 'nsec':
            return {
                'success': False,
                'error': f'Invalid HRP. Expected "nsec", got "{bech32_info["hrp"]}"'
            }
        
        # Validate data length (should be 32 bytes for private key)
        if bech32_info['data_length'] != 32:
            return {
                'success': False,
                'error': f'Invalid data length. Expected 32 bytes, got {bech32_info["data_length"]}'
            }
        
        # Convert to hex
        private_key_hex = bech32_info['data'].hex()
        
        # Validate the private key using nostr-sdk
        try:
            keys = Keys.parse(private_key_hex)
            public_key_hex = keys.public_key().to_hex()
        except Exception as e:
            return {
                'success': False,
                'error': f'Invalid private key: {str(e)}'
            }
        
        return {
            'success': True,
            'nsec': nsec_string,
            'private_key_hex': private_key_hex,
            'public_key_hex': public_key_hex,
            'public_key_bech32': keys.public_key().to_bech32(),
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }

def print_decoded_info(result):
    """Print the decoded nsec information."""
    if result['success']:
        print("✅ Successfully decoded nsec")
        print("=" * 60)
        print(f"NSEC: {result['nsec']}")
        print(f"Private Key (hex): {result['private_key_hex']}")
        print(f"Public Key (hex): {result['public_key_hex']}")
        print(f"Public Key (bech32): {result['public_key_bech32']}")
        print("=" * 60)
    else:
        print("❌ Failed to decode nsec")
        print("=" * 60)
        print(f"Error: {result['error']}")
        print("=" * 60)

def main():
    """Main function to run the nsec converter."""
    parser = argparse.ArgumentParser(description='Convert nsec bech32 to hex private key')
    parser.add_argument('--output', '-o', help='Output file for keys.txt (default: keys.txt)')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save to keys.txt file')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    
    args = parser.parse_args()
    
    # Get nsec from user input
    print("🔐 NSEC to Hex Private Key Converter")
    print("=" * 50)
    print("Enter your nsec (Nostr secret key) below.")
    print("The input will be hidden for security.")
    print("Press Enter when done.")
    print()
    
    # Get nsec input (hidden for security)
    import getpass
    nsec_input = getpass.getpass("NSEC: ").strip()
    
    if not nsec_input:
        print("❌ No nsec provided")
        sys.exit(1)
    
    # Validate nsec format
    if not nsec_input.startswith('nsec1'):
        print("❌ Error: Input must be a valid nsec string starting with 'nsec1'")
        sys.exit(1)
    
    if not args.quiet:
        print(f"🔍 Converting nsec: {nsec_input[:20]}...")
    
    # Decode the nsec
    result = decode_nsec(nsec_input)
    
    if not args.quiet:
        print_decoded_info(result)
    
    if not result['success']:
        print(f"❌ Conversion failed: {result['error']}")
        sys.exit(1)
    
    # Save to file if requested
    if not args.no_save:
        output_file = args.output or 'keys.txt'
        if save_to_keys_file(result['private_key_hex'], output_file):
            if not args.quiet:
                print(f"📝 You can now use this key file with the Nostr playground scripts")
                print(f"   Example: uv run like_post.py <event_id> --keys {output_file}")
        else:
            print(f"❌ Failed to save key file")
            sys.exit(1)
    else:
        if not args.quiet:
            print(f"📋 Private key (for manual copy):")
            print(f"   {result['private_key_hex']}")
    
    if not args.quiet:
        print("✅ Conversion completed successfully!")

if __name__ == "__main__":
    main() 