#!/usr/bin/env python3
"""
Convert hex pubkey to npub format and vice versa

This utility helps convert between hex public keys and npub (bech32) format.
Useful when working with Nostr events and needing to convert between formats.
"""
import sys
import argparse
from nostr_sdk import PublicKey

def hex_to_npub(hex_pubkey: str) -> str:
    """Convert hex public key to npub format"""
    try:
        pubkey = PublicKey.parse(hex_pubkey)
        return pubkey.to_bech32()
    except Exception as e:
        raise ValueError(f"Invalid hex public key: {e}")

def npub_to_hex(npub: str) -> str:
    """Convert npub to hex format"""
    try:
        pubkey = PublicKey.parse(npub)
        return pubkey.to_hex()
    except Exception as e:
        raise ValueError(f"Invalid npub: {e}")

def detect_and_convert(pubkey: str) -> dict:
    """Detect format and convert to the other format"""
    pubkey = pubkey.strip()
    
    if pubkey.startswith('npub1'):
        # Convert npub to hex
        try:
            hex_result = npub_to_hex(pubkey)
            return {
                'success': True,
                'input': pubkey,
                'input_format': 'npub',
                'output': hex_result,
                'output_format': 'hex'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    elif len(pubkey) == 64 and all(c in '0123456789abcdefABCDEF' for c in pubkey):
        # Convert hex to npub
        try:
            npub_result = hex_to_npub(pubkey)
            return {
                'success': True,
                'input': pubkey,
                'input_format': 'hex',
                'output': npub_result,
                'output_format': 'npub'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    else:
        return {
            'success': False,
            'error': 'Invalid format. Expected either npub1... or 64-character hex string'
        }

def main():
    parser = argparse.ArgumentParser(
        description='Convert between hex public keys and npub format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  scripts/hex_to_npub.py 805e3c98b42a2175a081666b4e077bab32136ea6cf4b9976a952569917d9e329
  scripts/hex_to_npub.py npub1sp0rex959gshtgypve45upmm4vepxm4ea9eja4f2ftfj97euv5s3rj02v
        """
    )
    parser.add_argument('pubkey', help='Public key in hex or npub format')
    parser.add_argument('--json', action='store_true', help='Output result as JSON')
    
    args = parser.parse_args()
    
    result = detect_and_convert(args.pubkey)
    
    if args.json:
        import json
        print(json.dumps(result, indent=2))
    else:
        if result['success']:
            print(f"✅ Converted {result['input_format']} to {result['output_format']}")
            print(f"Input:  {result['input']}")
            print(f"Output: {result['output']}")
        else:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)

if __name__ == "__main__":
    main()
