"""슬라이스 3: 채팅 목록과 메시지(참가자·차단 검증)."""

from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app


def auth(subject: str) -> dict:
    return {"Authorization": f"Bearer dev:{subject}"}


def make_profile(client: TestClient, subject: str, **overrides) -> str:
    body = {
        "nickname": overrides.get("nickname", subject),
        "age": overrides.get("age", 26),
        "region_code": overrides.get("region_code", "SEOUL_MAPO"),
    }
    res = client.put("/v1/accounts/me/profile", headers=auth(subject), json=body)
    assert res.status_code == 200, res.text
    return res.json()["id"]


def make_match(client: TestClient, a: str, b: str) -> tuple[str, str, str]:
    """a, b를 매칭시키고 (a_id, b_id, conversation_id)를 반환한다."""
    a_id = make_profile(client, a)
    b_id = make_profile(client, b)
    client.post("/v1/matches/likes", headers=auth(a), json={"target_profile_id": b_id})
    res = client.post(
        "/v1/matches/likes", headers=auth(b), json={"target_profile_id": a_id}
    )
    assert res.json()["is_match"], res.text
    return a_id, b_id, res.json()["conversation_id"]


class ChatsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_send_and_list_messages(self):
        _, _, conv = make_match(self.client, "c3-a", "c3-b")

        sent = self.client.post(
            f"/v1/chats/{conv}/messages",
            headers=auth("c3-a"),
            json={"body": "안녕하세요"},
        )
        self.assertEqual(sent.status_code, 200)
        self.assertEqual(sent.json()["body"], "안녕하세요")

        listed = self.client.get(f"/v1/chats/{conv}/messages", headers=auth("c3-b"))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.json()), 1)

        chats = self.client.get("/v1/chats", headers=auth("c3-a"))
        self.assertEqual(chats.status_code, 200)
        self.assertEqual(chats.json()[0]["last_message"], "안녕하세요")

    def test_non_member_cannot_access(self):
        _, _, conv = make_match(self.client, "c3-x", "c3-y")
        make_profile(self.client, "c3-stranger")
        res = self.client.post(
            f"/v1/chats/{conv}/messages",
            headers=auth("c3-stranger"),
            json={"body": "끼어들기"},
        )
        self.assertEqual(res.status_code, 403)

    def test_unknown_conversation_404(self):
        make_profile(self.client, "c3-a")
        res = self.client.get("/v1/chats/no-such-conv/messages", headers=auth("c3-a"))
        self.assertEqual(res.status_code, 404)
