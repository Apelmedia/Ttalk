"""슬라이스 4: 차단과 신고(인증·DB 기반)."""

from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app
from tests.test_chats import auth, make_match, make_profile


class SafetyTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_block_is_idempotent_and_stops_messages(self):
        a_id, b_id, conv = make_match(self.client, "s4-a", "s4-b")

        blocked = self.client.post(
            "/v1/safety/blocks",
            headers=auth("s4-a"),
            json={"blocked_profile_id": b_id},
        )
        self.assertEqual(blocked.status_code, 200, blocked.text)
        self.assertEqual(blocked.json()["blocked_profile_id"], b_id)

        # 멱등 — 같은 행을 반환한다.
        again = self.client.post(
            "/v1/safety/blocks",
            headers=auth("s4-a"),
            json={"blocked_profile_id": b_id},
        )
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.json()["id"], blocked.json()["id"])

        # 차단되면 양방향으로 메시지를 보낼 수 없다.
        msg = self.client.post(
            f"/v1/chats/{conv}/messages",
            headers=auth("s4-b"),
            json={"body": "차단 후 시도"},
        )
        self.assertEqual(msg.status_code, 403)

    def test_cannot_block_self(self):
        a_id = make_profile(self.client, "s4-self")
        res = self.client.post(
            "/v1/safety/blocks",
            headers=auth("s4-self"),
            json={"blocked_profile_id": a_id},
        )
        self.assertEqual(res.status_code, 400)

    def test_block_unknown_target_404(self):
        make_profile(self.client, "s4-c")
        res = self.client.post(
            "/v1/safety/blocks",
            headers=auth("s4-c"),
            json={"blocked_profile_id": "no-such-profile"},
        )
        self.assertEqual(res.status_code, 404)

    def test_report_is_recorded_each_time(self):
        make_profile(self.client, "s4-rep")
        target_id = make_profile(self.client, "s4-target")

        first = self.client.post(
            "/v1/safety/reports",
            headers=auth("s4-rep"),
            json={"target_profile_id": target_id, "category": "harassment"},
        )
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["status"], "queued")

        # 신고는 멱등이 아니다 — 같은 상대를 다시 신고하면 새 레코드가 생긴다.
        second = self.client.post(
            "/v1/safety/reports",
            headers=auth("s4-rep"),
            json={"target_profile_id": target_id, "category": "stalking"},
        )
        self.assertEqual(second.status_code, 200)
        self.assertNotEqual(second.json()["id"], first.json()["id"])

    def test_report_with_conversation_evidence(self):
        # 대화방 참가자가 그 대화방을 근거로 신고하면 저장된다.
        a_id, b_id, conv = make_match(self.client, "s4-rc-a", "s4-rc-b")
        res = self.client.post(
            "/v1/safety/reports",
            headers=auth("s4-rc-a"),
            json={
                "target_profile_id": b_id,
                "conversation_id": conv,
                "category": "harassment",
            },
        )
        self.assertEqual(res.status_code, 200, res.text)
        self.assertEqual(res.json()["conversation_id"], conv)

    def test_report_with_foreign_conversation_403(self):
        # 제3자가 자기 것이 아닌 대화방을 근거로 첨부하면 거부된다.
        a_id, b_id, conv = make_match(self.client, "s4-rf-a", "s4-rf-b")
        outsider_id = make_profile(self.client, "s4-rf-out")
        res = self.client.post(
            "/v1/safety/reports",
            headers=auth("s4-rf-out"),
            json={
                "target_profile_id": b_id,
                "conversation_id": conv,
                "category": "harassment",
            },
        )
        self.assertEqual(res.status_code, 403)

    def test_report_unknown_target_404(self):
        make_profile(self.client, "s4-rep2")
        res = self.client.post(
            "/v1/safety/reports",
            headers=auth("s4-rep2"),
            json={"target_profile_id": "no-such-profile", "category": "other"},
        )
        self.assertEqual(res.status_code, 404)
