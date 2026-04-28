import unittest

from fastapi.testclient import TestClient

from app.main import app


class SmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_app_import_and_docs(self):
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)

    def test_login_with_seeded_admin(self):
        response = self.client.post(
            "/auth/login",
            json={"username": "admin", "password": "Admin123!"},
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("access_token"))
        self.assertEqual(body.get("token_type"), "bearer")


if __name__ == "__main__":
    unittest.main()
