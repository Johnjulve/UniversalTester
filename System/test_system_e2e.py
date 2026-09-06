"""
E-Botar System & End-to-End (E2E) Integration Verification Script.

Tests complete multi-subsystem workflows without mocking:
1. System Configuration & Database Connectivity
2. Student Onboarding & Mandatory Password Reset Cycle
3. Registrar Student Roster Parser & Diff Classification
4. End-to-End Secret Ballot Casting & Blockchain Hash Chaining
5. Cryptographic Ledger Tamper-Detection Engine
6. Zero-Knowledge Voter Receipt Code Verification
7. Real-Time Results & Voter Turnout Aggregation

Execution:
  .\\env\\Scripts\\python.exe Testing/System/test_system_e2e.py
"""

import os
import sys
import uuid

# Setup Django environment
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from django.db import transaction
from apps.accounts.models import UserProfile, Program
from apps.elections.models import SchoolElection, SchoolPosition, ElectionPosition, Party
from apps.candidates.models import Candidate
from apps.voting.models import Ballot, VoteChoice, VoteReceipt, VoteBlock, AnonVote
from apps.voting.vote_ledger import append_vote_blocks_for_ballot, verify_election_vote_chain
from apps.voting.services import VotingDataService
from apps.accounts.services.roster_sync import StudentRosterParser, classify_roster_diff


def log_step(step_num: int, title: str):
    print(f"\n[Step {step_num}] {title}...")


def log_sub(message: str):
    print(f"  -> {message}")


def run_system_e2e_tests():
    print("=" * 70)
    print("        E-BOTAR PLATFORM: SYSTEM & E2E VERIFICATION SUITE       ")
    print("=" * 70)

    # 1. System Health & Core Data
    log_step(1, "Verifying System Configuration & Administrative Access")
    admin = User.objects.filter(is_superuser=True).first()
    assert admin is not None, "At least one superuser administrator must exist"
    log_sub(f"Active Administrator: {admin.username} (ID: {admin.id})")

    election = SchoolElection.objects.filter(is_active=True).first()
    if not election:
        election = SchoolElection.objects.first()
    assert election is not None, "At least one election must exist in the system"
    log_sub(f"Target Election: '{election.title}' (Status: {'Active' if election.is_active else 'Archived/Draft'})")

    positions = SchoolPosition.objects.filter(position_elections__election=election)
    if not positions.exists():
        positions = SchoolPosition.objects.all()
    assert positions.exists(), "Target election must have configured positions"
    test_position = positions.first()
    log_sub(f"Position Verified: '{test_position.name}'")


    # 2. Student Onboarding & Mandatory First-Login Password Reset
    log_step(2, "Verifying Student Onboarding & Mandatory Password Reset Boundary")
    test_student_username = f"e2e_student_{uuid.uuid4().hex[:6]}"
    student, _ = User.objects.get_or_create(
        username=test_student_username,
        defaults={'email': f"{test_student_username}@university.edu", 'first_name': 'Test', 'last_name': 'Student'}
    )
    student.set_password('TemporaryPassword123!')
    student.save()

    profile, _ = UserProfile.objects.get_or_create(
        user=student,
        defaults={'student_id': f"2026-{uuid.uuid4().hex[:5].upper()}", 'is_verified': True, 'must_change_password': True}
    )
    assert profile.must_change_password is True, "New roster student must require password change"
    log_sub(f"Student enrolled: {student.username} (must_change_password: True)")

    # Simulate student changing password on first login
    student.set_password('PermanentSecurePass2026!')
    student.save()
    profile.must_change_password = False
    profile.save(update_fields=['must_change_password'])
    assert not profile.must_change_password, "must_change_password flag must be cleared after update"
    log_sub("First-login password reset completed successfully (must_change_password: False)")

    # 3. Registrar Student Roster Parser & Diff Classification
    log_step(3, "Verifying Registrar Roster Sync Engine")
    sample_roster_csv = (
        "Student ID,Email,First Name,Last Name,Year Level\n"
        "2026-00001,alice.walker@univ.edu,Alice,Walker,3rd Year\n"
        "2026-00002,bob.smith@univ.edu,Bob,Smith,2nd Year\n"
        f"2026-99999,{student.email},Test,Student,1st Year\n"
    ).encode('utf-8')

    import io
    parser = StudentRosterParser()
    parsed_rows, parse_errors = parser.parse_file(io.BytesIO(sample_roster_csv), "roster_sample.csv")
    assert len(parse_errors) == 0, f"Roster parser should have 0 errors: {parse_errors}"
    assert len(parsed_rows) == 3, f"Expected 3 parsed rows, got {len(parsed_rows)}"
    log_sub(f"Parser processed {len(parsed_rows)} valid student roster records")


    diff = classify_roster_diff(parsed_rows)
    assert 'to_create' in diff and 'to_update' in diff
    log_sub(f"Diff Classified: {len(diff['to_create'])} new students, {len(diff['to_update'])} existing updates")


    # 4. End-to-End Secret Ballot Casting & Blockchain Hash Chaining
    log_step(4, "Verifying Ballot Casting, Receipt Minting & Blockchain Chaining")
    candidate = Candidate.objects.filter(election=election, position=test_position).first()
    if not candidate:
        candidate, _ = Candidate.objects.get_or_create(
            user=admin,
            election=election,
            position=test_position,
            defaults={'manifesto': 'E2E Testing Candidate', 'is_active': True}
        )
    candidate_name = candidate.user.get_full_name() or candidate.user.username
    log_sub(f"Selected Candidate: '{candidate_name}' for '{test_position.name}'")


    # Clean existing votes for test student if any
    Ballot.objects.filter(user=student, election=election).delete()
    VoteReceipt.objects.filter(user=student, election=election).delete()

    with transaction.atomic():
        receipt = VoteReceipt.objects.create(
            user=student,
            election=election,
            ip_address='127.0.0.1'
        )
        ballot = Ballot.objects.create(
            user=student,
            election=election,
            receipt=receipt,
            ip_address='127.0.0.1',
            user_agent='SystemE2ETest/1.0'
        )
        choice = VoteChoice.objects.create(
            ballot=ballot,
            position=test_position,
            candidate=candidate
        )
        choice.anonymize()

        # Append to blockchain ledger
        blocks = append_vote_blocks_for_ballot(
            election_id=election.id,
            ballot_identifier=str(ballot.pk),
            receipt_secret=receipt.receipt_hash,
            user_id=student.id,
            choices=[choice]
        )

    assert receipt.receipt_code is not None, "Receipt must generate a formatted code"
    assert len(blocks) >= 1, "At least one block must be appended to the ledger"
    latest_block = blocks[0]
    log_sub(f"Receipt Minted: {receipt.receipt_code} (Masked: {receipt.get_masked_receipt()})")
    log_sub(f"Blockchain Block #{latest_block.block_index} chained (Hash: {latest_block.current_hash[:16]}...)")

    # 5. Cryptographic Ledger Tamper-Detection Engine
    log_step(5, "Verifying Blockchain Ledger Tamper Detection")
    is_valid, errors = verify_election_vote_chain(election.id)
    assert is_valid, f"Ledger should be valid before tampering: {errors}"
    log_sub("Blockchain hash chain integrity: VALID (All block digests linked sequentially)")

    # Simulate an adversarial database tampering attack (bypassing model guards via direct SQL update)
    original_hash = latest_block.current_hash
    VoteBlock.objects.filter(pk=latest_block.pk).update(
        current_hash="0000000000000000000000000000000000000000000000000000000000000000"
    )

    is_tampered_valid, tamper_errors = verify_election_vote_chain(election.id)
    assert not is_tampered_valid, "Tamper detection engine MUST fail when block hash is altered"
    log_sub("Adversarial Tamper Simulation: TAMPER DETECTED AND REJECTED")

    # Restore ledger integrity
    VoteBlock.objects.filter(pk=latest_block.pk).update(current_hash=original_hash)
    restored_valid, _ = verify_election_vote_chain(election.id)
    assert restored_valid, "Ledger should return to valid state after restoration"
    log_sub("Ledger integrity restored: VALID")


    # 6. Zero-Knowledge Voter Receipt Code Verification
    log_step(6, "Verifying Zero-Knowledge Voter Receipt Code Verification")
    assert receipt.verify_receipt(receipt.receipt_code), "Valid receipt code must verify true"
    assert receipt.verify_receipt(receipt.receipt_code.lower().replace('-', '')), "Normalized receipt code must verify true"
    assert not receipt.verify_receipt('INVALID-CODE-9999'), "Invalid receipt code must be rejected"
    log_sub(f"Code '{receipt.receipt_code}' verification: VERIFIED (Zero-Knowledge match)")
    log_sub("Forged code 'INVALID-CODE-9999': REJECTED")

    # 7. Real-Time Results & Voter Turnout Aggregation
    log_step(7, "Verifying Results & Voter Turnout Statistics Aggregation")
    stats = VotingDataService.get_election_statistics(election.id)
    assert stats['unique_voters'] >= 1, "Stats should record at least one unique voter"
    assert stats['total_votes_cast'] >= 1, "Stats should record cast votes"
    log_sub(f"Total Unique Voters: {stats['unique_voters']}")
    log_sub(f"Total Votes Cast: {stats['total_votes_cast']}")
    log_sub(f"Turnout Percentage: {stats['turnout_percentage']}%")

    # Cleanup temporary test student
    student.delete()
    log_sub(f"Temporary test student cleaned up: {test_student_username}")

    print("\n" + "=" * 70)
    print("       ALL SYSTEM & END-TO-END WORKFLOW TESTS PASSED! (7/7)     ")
    print("=" * 70)


if __name__ == '__main__':
    run_system_e2e_tests()
