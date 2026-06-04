from unittest import TestCase

from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.core.db import engine
from app.main import app


class SmokeTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_bootstrap_disables_gps(self):
        response = self.client.get("/v1/public/bootstrap")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["features"]["gps_nearby"])

    def test_static_prototype_is_served(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Warm Haven", response.text)

    def test_security_headers_are_set(self):
        response = self.client.get("/health")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertIn("geolocation=()", response.headers["permissions-policy"])

    def test_safety_audit_tables_exist(self):
        table_names = set(inspect(engine).get_table_names())
        self.assertTrue(
            {"consent_records", "moderation_actions", "private_photo_access_logs"}.issubset(
                table_names
            )
        )

    def test_people_requires_auth(self):
        # people는 이제 인증·DB 기반이다. 비인증 요청은 거부된다.
        response = self.client.get("/v1/people", params={"region": "마포"})
        self.assertEqual(response.status_code, 401)

    def test_report_requires_auth(self):
        # 신고는 이제 인증·DB 기반이다. 비인증 요청은 거부된다.
        response = self.client.post(
            "/v1/safety/reports",
            json={
                "target_profile_id": "profile-demo-target",
                "category": "stalking",
                "summary": "demo",
            },
        )
        self.assertEqual(response.status_code, 401)
