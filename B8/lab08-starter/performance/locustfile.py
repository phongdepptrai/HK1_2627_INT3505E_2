"""Lab 4 load test script with weighted tasks and simulated 1% error on search_by_year.

Run scenarios (with Books API running on http://127.0.0.1:5000):
  locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 10 -r 2 -t 30s --html reports/A.html
  locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 50 -r 5 -t 60s --html reports/B.html
  locust -f performance/locustfile.py --headless -H http://127.0.0.1:5000 -u 200 -r 50 -t 30s --html reports/C.html
"""
import itertools
import random

from locust import HttpUser, between, task

_counter = itertools.count(1)


class BooksUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def list_books(self):
        self.client.get("/books", name="GET /books")

    @task(2)
    def read_book(self):
        book_id = random.randint(1, 50)
        with self.client.get(
            f"/books/{book_id}", name="GET /books/{id}", catch_response=True
        ) as response:
            # Expected 404 (random id absent) is not an operational failure.
            if response.status_code in (200, 404):
                response.success()
            else:
                response.failure(f"Unexpected status {response.status_code}")

    @task(1)
    def create_book(self):
        unique = next(_counter)
        self.client.post(
            "/books",
            json={"title": f"Load test {unique}", "author": "locust"},
            name="POST /books",
        )

    @task(2)
    def search_by_year(self, year=None):
        """Query books filtered by year with a 1% simulated error rate (client-side 500 injection)."""
        target_year = year if year is not None else random.choice([1996, 2017, 2020, 2021])
        with self.client.get(
            f"/books?year={target_year}",
            name="GET /books?year={year}",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"HTTP {response.status_code} from server")
            elif random.random() < 0.01:
                # Client-side artificial 1% failure simulating HTTP 500 (not emitted by Flask server).
                response.failure("Simulated 1% HTTP 500 error (client-side fault injection)")
            else:
                response.success()
