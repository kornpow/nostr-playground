#!/usr/bin/env python3
"""
Nostr NSEC Generator - Generate new nsec bech32 keys

This script generates new Nostr secret keys in nsec bech32 format.
"""

import argparse
import sys
from nostr_sdk import Keys

def generate_nsec():
    """
    Generate a new nsec key pair.
    
    Returns:
        Dict with generated key information
    """
    try:
        # Generate new keys
        keys = Keys.generate()
        
        # Get the private key in hex format
        private_key_hex = keys.secret_key().to_hex()
        
        # Get the public key in both formats
        public_key_hex = keys.public_key().to_hex()
        public_key_bech32 = keys.public_key().to_bech32()
        
        # Get the private key in bech32 format (nsec)
        private_key_bech32 = keys.secret_key().to_bech32()
        
        return {
            'success': True,
            'private_key_hex': private_key_hex,
            'private_key_bech32': private_key_bech32,
            'public_key_hex': public_key_hex,
            'public_key_bech32': public_key_bech32,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Error generating keys: {str(e)}'
        }

def save_to_keys_file(private_key_hex: str, filename: str = 'keys.txt'):
    """
    Save the private key to a keys.txt file with proper formatting.
    
    Args:
        private_key_hex: The private key in hex format
        filename: The filename to save to
    """
    try:
        with open(filename, 'w') as f:
            f.write("# Sample private key file for Nostr Playground\n")
            f.write("# \n")
            f.write("# This file should contain your private key in hex format.\n")
            f.write("# The private key should be 64 characters long (32 bytes).\n")
            f.write("# \n")
            f.write("# IMPORTANT: Keep this file secure and never share your private key!\n")
            f.write("# \n")
            f.write("# Example format (replace with your actual private key):\n")
            f.write("# 1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef\n")
            f.write("# \n")
            f.write("# To generate a new key pair, run:\n")
            f.write("# uv run like_post.py <any_event_id> --keys keys.txt\n")
            f.write("# \n")
            f.write("# This will automatically generate a new key pair and save it to keys.txt\n")
            f.write("# \n")
            f.write("# Your public key will be displayed when you first run the script.\n")
            f.write("# You can share your public key with others, but keep the private key secret.\n")
            f.write("# \n")
            f.write("# Replace this line with your actual private key:\n")
            f.write(f"{private_key_hex}\n")
        
        print(f"✅ Private key saved to {filename}")
        return True
    except Exception as e:
        print(f"❌ Error saving to {filename}: {e}")
        return False

def print_generated_info(result):
    """Print the generated key information."""
    if result['success']:
        print("✅ Successfully generated new nsec key pair")
        print("=" * 60)
        print("🔐 PRIVATE KEY (KEEP SECRET!)")
        print("=" * 60)
        print(f"NSEC: {result['private_key_bech32']}")
        print(f"Hex:  {result['private_key_hex']}")
        print()
        print("🔑 PUBLIC KEY (SAFE TO SHARE)")
        print("=" * 60)
        print(f"NPUB: {result['public_key_bech32']}")
        print(f"Hex:  {result['public_key_hex']}")
        print("=" * 60)
        print()
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("   • Keep your NSEC private key secret!")
        print("   • You can safely share your NPUB public key")
        print("   • Store your keys securely")
        print("   • Never share your private key with anyone")
        print("=" * 60)
    else:
        print("❌ Failed to generate keys")
        print("=" * 60)
        print(f"Error: {result['error']}")
        print("=" * 60)

def main():
    """Main function to run the nsec generator."""
    parser = argparse.ArgumentParser(description='Generate new nsec bech32 keys')
    parser.add_argument('--output', '-o', help='Output file for keys.txt (default: keys.txt)')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save to keys.txt file')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')
    parser.add_argument('--hex-only', action='store_true', help='Show only hex format (no bech32)')
    
    args = parser.parse_args()
    
    if not args.quiet:
        print("🔐 Nostr NSEC Key Generator")
        print("=" * 50)
        print("Generating new nsec key pair...")
        print()
    
    # Generate new keys
    result = generate_nsec()
    
    if not result['success']:
        print(f"❌ Generation failed: {result['error']}")
        sys.exit(1)
    
    if not args.quiet:
        if args.hex_only:
            print("✅ Successfully generated new key pair")
            print("=" * 60)
            print(f"Private Key (hex): {result['private_key_hex']}")
            print(f"Public Key (hex):  {result['public_key_hex']}")
            print("=" * 60)
        else:
            print_generated_info(result)
    
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
    
    if not args.quiet:
        print("✅ Key generation completed successfully!")

if __name__ == "__main__":
    main() 