"""슬라이스 5~6: 공개 요청 사진 등록과 열람 권한(인증·DB 기반)."""

from unittest import TestCase

from fastapi.testclient import TestClient

from app.main import app
from tests.test_chats import auth, make_profile


def register_photo(client: TestClient, subject: str, object_key: str) -> str:
    res = client.post(
        "/v1/private-photos",
        headers=auth(subject),
        json={"object_key": object_key},
    )
    assert res.status_code == 200, res.text
    return res.json()["id"]


class PrivatePhotosTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = TestClient(app)
        cls.client = cls.context.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)

    def test_grant_and_revoke_then_regrant(self):
        make_profile(self.client, "p5-owner")
        viewer_id = make_profile(self.client, "p5-viewer")
        photo_id = register_photo(self.client, "p5-owner", "p5/owner/photo-1")

        granted = self.client.post(
            "/v1/private-photos/grants",
            headers=auth("p5-owner"),
            json={"photo_id": photo_id, "viewer_profile_id": viewer_id},
        )
        self.assertEqual(granted.status_code, 200, granted.text)
        grant_id = granted.json()["id"]
        self.assertIsNone(granted.json()["revoked_at"])

        revoked = self.client.delete(
            f"/v1/private-photos/grants/{grant_id}", headers=auth("p5-owner")
        )
        self.assertEqual(revoked.status_code, 200)
        self.assertIsNotNone(revoked.json()["revoked_at"])

        # uq_photo_viewer 충돌 없이 같은 행을 되살려 재부여한다.
        regranted = self.client.post(
            "/v1/private-photos/grants",
            headers=auth("p5-owner"),
            json={"photo_id": photo_id, "viewer_profile_id": viewer_id},
        )
        self.assertEqual(regranted.status_code, 200, regranted.text)
        self.assertEqual(regranted.json()["id"], grant_id)
        self.assertIsNone(regranted.json()["revoked_at"])

    def test_cannot_grant_on_others_photo(self):
        make_profile(self.client, "p5-owner2")
        make_profile(self.client, "p5-stranger")
        viewer_id = make_profile(self.client, "p5-viewer2")
        photo_id = register_photo(self.client, "p5-owner2", "p5/owner2/photo-1")

        res = self.client.post(
            "/v1/private-photos/grants",
            headers=auth("p5-stranger"),
            json={"photo_id": photo_id, "viewer_profile_id": viewer_id},
        )
        self.assertEqual(res.status_code, 403)

    def test_cannot_revoke_others_grant(self):
        make_profile(self.client, "p5-owner3")
        viewer_id = make_profile(self.client, "p5-viewer3")
        make_profile(self.client, "p5-outsider")
        photo_id = register_photo(self.client, "p5-owner3", "p5/owner3/photo-1")

        granted = self.client.post(
            "/v1/private-photos/grants",
            headers=auth("p5-owner3"),
            json={"photo_id": photo_id, "viewer_profile_id": viewer_id},
        )
        grant_id = granted.json()["id"]

        res = self.client.delete(
            f"/v1/private-photos/grants/{grant_id}", headers=auth("p5-outsider")
        )
        self.assertEqual(res.status_code, 403)

    def test_grant_unknown_photo_404(self):
        make_profile(self.client, "p5-owner4")
        viewer_id = make_profile(self.client, "p5-viewer4")
        res = self.client.post(
            "/v1/private-photos/grants",
            headers=auth("p5-owner4"),
            json={"photo_id": "no-such-photo", "viewer_profile_id": viewer_id},
        )
        self.assertEqual(res.status_code, 404)
