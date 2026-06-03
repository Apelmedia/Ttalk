"""슬라이스 1: 인증 + 계정/프로필 흐름 검증.

USE_FIREBASE_AUTH=false(기본)에서 dev 토큰으로 단독 검증한다.
"""

from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app


def auth(subject: str) -> dict:
    return {"Authorization": f"Bearer dev:{subject}"}


class AuthAccountTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_me_requires_auth(self):
        response = self.client.get("/v1/accounts/me")
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_is_rejected(self):
        response = self.client.get(
            "/v1/accounts/me", headers={"Authorization": "Bearer not-a-dev-token"}
        )
        self.assertEqual(response.status_code, 401)

    def test_account_autocreated_without_profile(self):
        response = self.client.get("/v1/accounts/me", headers=auth("newcomer"))
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsNone(body["profile"])
        self.assertFalse(body["is_adult_verified"])

    def test_profile_upsert_and_readback(self):
        headers = auth("profile-owner")
        created = self.client.put(
            "/v1/accounts/me/profile",
            headers=headers,
            json={
                "nickname": "테스트",
                "age": 28,
                "region_code": "SEOUL_MAPO",
                "identity_tags": ["여성"],
                "orientation_tags": ["레즈비언"],
                "bio": "안녕하세요",
            },
        )
        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["nickname"], "테스트")

        me = self.client.get("/v1/accounts/me", headers=headers)
        self.assertEqual(me.status_code, 200)
        profile = me.json()["profile"]
        self.assertIsNotNone(profile)
        self.assertEqual(profile["age"], 28)
        self.assertEqual(profile["identity_tags"], ["여성"])

        # 같은 계정의 두 번째 upsert는 새로 만들지 않고 갱신한다.
        updated = self.client.put(
            "/v1/accounts/me/profile",
            headers=headers,
            json={
                "nickname": "테스트2",
                "age": 30,
                "region_code": "SEOUL_YONGSAN",
            },
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["id"], profile["id"])
        self.assertEqual(updated.json()["nickname"], "테스트2")

    def test_underage_profile_rejected(self):
        response = self.client.put(
            "/v1/accounts/me/profile",
            headers=auth("minor"),
            json={"nickname": "x", "age": 17, "region_code": "SEOUL"},
        )
        self.assertEqual(response.status_code, 422)
