"""슬라이스 2: people 목록과 좋아요/매치 성사 검증."""

from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app


def auth(subject: str) -> dict:
    return {"Authorization": f"Bearer dev:{subject}"}


def make_profile(client: TestClient, subject: str, **overrides) -> str:
    """dev 계정 + 프로필을 만들고 profile_id를 반환한다."""
    body = {
        "nickname": overrides.get("nickname", subject),
        "age": overrides.get("age", 25),
        "region_code": overrides.get("region_code", "SEOUL_MAPO"),
        "identity_tags": overrides.get("identity_tags", []),
        "orientation_tags": overrides.get("orientation_tags", []),
        "is_discoverable": overrides.get("is_discoverable", True),
    }
    res = client.put("/v1/accounts/me/profile", headers=auth(subject), json=body)
    assert res.status_code == 200, res.text
    return res.json()["id"]


class PeopleMatchesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_people_excludes_self_and_lists_others(self):
        alice = make_profile(self.client, "p2-alice", region_code="SEOUL_MAPO")
        bob = make_profile(self.client, "p2-bob", region_code="SEOUL_MAPO")

        res = self.client.get("/v1/people", headers=auth("p2-alice"))
        self.assertEqual(res.status_code, 200)
        ids = {p["id"] for p in res.json()}
        self.assertIn(bob, ids)
        self.assertNotIn(alice, ids)

    def test_region_and_tag_filter(self):
        make_profile(
            self.client,
            "p2-yongsan",
            region_code="SEOUL_YONGSAN",
            orientation_tags=["게이"],
        )
        res = self.client.get(
            "/v1/people",
            headers=auth("p2-alice"),
            params={"region": "YONGSAN", "tag": "게이"},
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json())
        self.assertTrue(all("YONGSAN" in p["region"] for p in res.json()))
        self.assertTrue(all("게이" in p["tags"] for p in res.json()))

    def test_profile_required_before_people(self):
        # 계정은 있지만 프로필이 없으면 409.
        res = self.client.get("/v1/people", headers=auth("p2-noprofile"))
        self.assertEqual(res.status_code, 409)

    def test_mutual_like_creates_match(self):
        make_profile(self.client, "p2-x")
        y = make_profile(self.client, "p2-y")
        x = make_profile(self.client, "p2-x")  # idempotent fetch of x's id

        # x → y: 아직 매치 아님
        first = self.client.post(
            "/v1/matches/likes", headers=auth("p2-x"), json={"target_profile_id": y}
        )
        self.assertEqual(first.status_code, 200)
        self.assertFalse(first.json()["is_match"])

        # y → x: 상호 좋아요 → 매치 + 대화방
        second = self.client.post(
            "/v1/matches/likes", headers=auth("p2-y"), json={"target_profile_id": x}
        )
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()["is_match"])
        self.assertIsNotNone(second.json()["conversation_id"])

    def test_self_like_rejected(self):
        x = make_profile(self.client, "p2-self")
        res = self.client.post(
            "/v1/matches/likes", headers=auth("p2-self"), json={"target_profile_id": x}
        )
        self.assertEqual(res.status_code, 400)

    def test_like_unknown_target_404(self):
        make_profile(self.client, "p2-x")
        res = self.client.post(
            "/v1/matches/likes",
            headers=auth("p2-x"),
            json={"target_profile_id": "does-not-exist"},
        )
        self.assertEqual(res.status_code, 404)
