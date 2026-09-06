"""
E-Botar Concurrent Load & Stress Testing Script
Simulates concurrent student voter traffic using Locust.

Prerequisites:
  pip install locust

Execution:
  # Web UI mode (interactive dashboard at http://localhost:8089)
  locust -f Testing/Performance/locustfile.py --host=http://localhost:8000

  # Headless CLI mode (run for 60s with 50 users spawning at 5 users/sec)
  locust -f Testing/Performance/locustfile.py --host=http://localhost:8000 --headless -u 50 -r 5 --run-time 60s
"""

from locust import HttpUser, task, between


class StudentVoterUser(HttpUser):
    """
    Simulates student voter behavior on the E-Botar platform:
    Browsing elections, checking system health, viewing election results,
    and verifying zero-knowledge receipt codes.
    """
    wait_time = between(1, 3)

    def on_start(self):
        """Authenticate test student user for endpoints requiring authorization"""
        try:
            res = self.client.post("/api/auth/token/", json={
                "username": "perf_test_user",
                "password": "testpass123"
            })
            if res.status_code == 200:
                token = res.json().get("access")
                self.client.headers["Authorization"] = f"Bearer {token}"
        except Exception:
            pass

    @task(4)

    def check_system_health(self):
        """Monitor API health endpoint"""
        self.client.get("/api/health/", name="[GET] /api/health/")

    @task(5)
    def browse_active_elections(self):
        """Voter views active election listings"""
        self.client.get("/api/elections/elections/", name="[GET] /api/elections/elections/")

    @task(2)
    def view_election_results(self):
        """Voter views public tally and election results breakdown"""
        self.client.get(
            "/api/voting/results/election_results/?election_id=1",
            name="[GET] /api/voting/results/election_results/"
        )

    @task(2)
    def view_election_statistics(self):
        """Voter queries election position turnout statistics"""
        self.client.get(
            "/api/voting/results/statistics/?election_id=1",
            name="[GET] /api/voting/results/statistics/"
        )

    @task(1)
    def audit_receipt_code(self):
        """Voter verifies blockchain ballot inclusion receipt"""
        self.client.post(
            "/api/voting/receipts/verify/",
            json={"receipt_code": "ABCD-EFGH"},
            name="[POST] /api/voting/receipts/verify/"
        )

