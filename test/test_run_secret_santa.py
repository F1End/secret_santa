import unittest
import csv
import tempfile
import os
from pathlib import Path

# Import functions from your main script (assumed to be named secret_santa.py)
import run_secret_santa as secret_santa


class TestSecretSanta(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_dir_path = Path(self.test_dir.name)

    def tearDown(self):
        # Clean up temporary directory after tests
        self.test_dir.cleanup()

    def create_csv(self, filename, headers, rows):
        filepath = self.test_dir_path / filename
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return str(filepath)

    def test_load_participants_success(self):
        csv_path = self.create_csv(
            "participants.csv",
            ["Name", "Email"],
            [
                ["Alice", "alice@example.com"],
                ["Bob", "bob@example.com"],
                ["Charlie", "charlie@example.com"]
            ]
        )
        participants = secret_santa.load_participants(csv_path)
        self.assertEqual(len(participants), 3)
        self.assertEqual(participants[0].name, "Alice")
        self.assertEqual(participants[0].email, "alice@example.com")

    def test_load_participants_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            secret_santa.load_participants("non_existent_participants.csv")

    def test_load_constraints_success(self):
        csv_path = self.create_csv(
            "constraints.csv",
            ["Email1", "Email2"],
            [
                ["alice@example.com", "bob@example.com"]
            ]
        )
        forbidden = secret_santa.load_constraints(csv_path)
        # Check bidirectional symmetry
        self.assertIn(("alice@example.com", "bob@example.com"), forbidden)
        self.assertIn(("bob@example.com", "alice@example.com"), forbidden)

    def test_load_constraints_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            secret_santa.load_constraints("non_existent_constraints.csv")

    def test_assignment_validity_and_derangement(self):
        """Test that every participant gives and receives exactly one gift, with no self-assignments."""
        participants = [
            secret_santa.Participant("Alice", "alice@example.com"),
            secret_santa.Participant("Bob", "bob@example.com"),
            secret_santa.Participant("Charlie", "charlie@example.com"),
            secret_santa.Participant("Diana", "diana@example.com")
        ]
        
        secret_santa.generate_assignment(participants, set())

        givers = [p.email for p in participants]
        receivers = [p.assigned_to.email for p in participants]

        # Every person gives one
        self.assertEqual(len(set(givers)), len(participants))
        # Every person receives one (each person is someone's giftee)
        self.assertEqual(len(set(receivers)), len(participants))

        # No one gifts themselves
        for p in participants:
            self.assertNotEqual(p.email, p.assigned_to.email)

    def test_assignment_with_constraints(self):
        """Test that constraints are strictly obeyed across multiple runs."""
        participants = [
            secret_santa.Participant("Alice", "alice@example.com"),
            secret_santa.Participant("Bob", "bob@example.com"),
            secret_santa.Participant("Charlie", "charlie@example.com"),
            secret_santa.Participant("Diana", "diana@example.com")
        ]
        
        # Alice and Bob cannot gift each other
        forbidden = {
            ("alice@example.com", "bob@example.com"),
            ("bob@example.com", "alice@example.com")
        }

        # Run multiple iterations to ensure randomness doesn't violate constraints
        for _ in range(50):
            # Reset assignments
            for p in participants:
                p.assigned_to = None

            secret_santa.generate_assignment(participants, forbidden)

            for p in participants:
                pair = (p.email, p.assigned_to.email)
                self.assertNotIn(pair, forbidden)

    def test_iterative_stress_test_randomness(self):
        """Perform multiple iterative runs on the same input to ensure stability and verify validity."""
        participants_data = [
            ("Alice", "alice@example.com"),
            ("Bob", "bob@example.com"),
            ("Charlie", "charlie@example.com"),
            ("Diana", "diana@example.com"),
            ("Eve", "eve@example.com")
        ]
        
        forbidden = {
            ("alice@example.com", "bob@example.com"),
            ("bob@example.com", "alice@example.com"),
            ("charlie@example.com", "diana@example.com"),
            ("diana@example.com", "charlie@example.com")
        }

        # Stress test with 100 consecutive randomized rolls
        for run in range(100):
            participants = [secret_santa.Participant(name, email) for name, email in participants_data]
            secret_santa.generate_assignment(participants, forbidden)

            # Assert validity for this run
            emails = {p.email for p in participants}
            assigned_emails = {p.assigned_to.email for p in participants}
            
            self.assertEqual(emails, assigned_emails)
            for p in participants:
                self.assertNotEqual(p.email, p.assigned_to.email)
                self.assertNotIn((p.email, p.assigned_to.email), forbidden)

    def test_impossible_constraints_raises_error(self):
        """Test that an impossible configuration (e.g., 3 people where everyone is blocked from everyone) raises ValueError."""
        participants = [
            secret_santa.Participant("Alice", "alice@example.com"),
            secret_santa.Participant("Bob", "bob@example.com"),
            secret_santa.Participant("Charlie", "charlie@example.com")
        ]
        
        # Block everyone from everyone
        forbidden = set()
        emails = [p.email for p in participants]
        for i in range(len(emails)):
            for j in range(len(emails)):
                if i != j:
                    forbidden.add((emails[i], emails[j]))

        with self.assertRaises(ValueError):
            secret_santa.generate_assignment(participants, forbidden)

    def test_numeric_password_generation(self):
        """Ensure passwords are strictly numeric and of the requested length."""
        for _ in range(20):
            pwd = secret_santa.generate_numeric_password(6)
            self.assertEqual(len(pwd), 6)
            self.assertTrue(pwd.isdigit())


if __name__ == '__main__':
    unittest.main()
