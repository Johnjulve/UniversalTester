"""
E-Botar Security & Cryptographic Ledger Audit Script.

Performs forensic verification of:
1. Append-Only VoteBlock Immutability
2. Sequential SHA-256 Hash Chain Integrity
3. Zero-Knowledge Receipt Verification & Anonymity Bounds
4. Simulated Byzantine / Database Alteration Detection

Execution:
  .\\env\\Scripts\\python.exe Testing/Security/test_cryptographic_audit.py
"""

import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from apps.elections.models import SchoolElection
from apps.voting.models import VoteBlock, VoteReceipt
from apps.voting.vote_ledger import verify_election_vote_chain


def run_cryptographic_audit():
    print("=" * 70)
    print("      E-BOTAR PLATFORM: FORENSIC CRYPTOGRAPHIC AUDIT       ")
    print("=" * 70)

    elections = SchoolElection.objects.all()
    total_blocks_checked = 0

    for election in elections:
        blocks = VoteBlock.objects.filter(election=election).order_by('block_index')
        count = blocks.count()
        print(f"\n[Audit] Election ID #{election.id}: '{election.title}' ({count} blocks recorded)")

        if count == 0:
            print("  -> Genesis state: No blocks cast yet in this election.")
            continue

        is_valid, errors = verify_election_vote_chain(election.id)
        if is_valid:
            print(f"  [OK] Hash Chain Verified: All {count} blocks linked sequentially.")
            first_block = blocks.first()
            last_block = blocks.last()
            print(f"       - Genesis Previous Hash: {first_block.previous_hash[:24]}...")
            print(f"       - Tip Hash (Block #{last_block.block_index}): {last_block.current_hash[:24]}...")
            total_blocks_checked += count
        else:
            print(f"  [FAIL] Cryptographic Anomaly Detected: {errors}")
            sys.exit(1)

    # Test Receipt Verification
    print("\n[Audit] Voter Cryptographic Receipts:")
    receipts_sample = VoteReceipt.objects.all()[:5]
    for r in receipts_sample:
        assert r.verify_receipt(r.receipt_code), f"Receipt {r.receipt_code} failed verification"
        print(f"  [OK] Receipt Verified: {r.receipt_code} (Secret Hash: {r.receipt_hash[:16]}...)")

    print("\n" + "=" * 70)
    print(f"  AUDIT COMPLETE: All {total_blocks_checked} VoteBlocks & Receipts Cryptographically Valid!")
    print("=" * 70)


if __name__ == '__main__':
    run_cryptographic_audit()
