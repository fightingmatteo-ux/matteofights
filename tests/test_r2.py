from urllib.parse import parse_qs, urlparse

import pytest

import r2


class Stub:
    def __init__(self, keys):
        self.keys = keys

    def head_object(self, Bucket, Key):
        if Key not in self.keys:
            from botocore.exceptions import ClientError
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")
        return {"ContentLength": self.keys[Key]}

    def generate_presigned_url(self, op, Params, ExpiresIn):
        return f"https://r2.example/{Params['Key']}?X-Amz-Expires={ExpiresIn}"


@pytest.fixture
def keys(monkeypatch):
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "AKIDEXAMPLE")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")


def test_presign_default_expiry_at_least_6h(keys):
    url = r2.presign_get("renders/x.mp4")  # real boto3 signing, no network
    q = parse_qs(urlparse(url).query)
    assert int(q["X-Amz-Expires"][0]) >= 21600
    assert "matteofights-media" in url and "renders/x.mp4" in url


def test_video_url_prefers_r2(keys, monkeypatch):
    monkeypatch.setattr(r2, "_client", lambda: Stub({"renders/a.mp4": 123}))
    assert r2.video("a.mp4") == (123, "https://r2.example/renders/a.mp4?X-Amz-Expires=21600")
    assert r2.video_url("a.mp4", lambda a: "release") .startswith("https://r2.example/renders/a.mp4")


def test_video_url_falls_back_to_release(keys, monkeypatch):
    monkeypatch.setattr(r2, "_client", lambda: Stub({}))
    assert r2.video("b.mp4") is None
    assert r2.video_url("b.mp4", lambda a: f"release/{a}") == "release/b.mp4"


def test_video_falls_back_without_keys(monkeypatch):
    monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setattr(r2, "ENV_FILE", r2.ENV_FILE.with_name("does-not-exist.env"))
    assert r2.video("a.mp4") is None


def test_upload_render_mirrors_to_r2_when_configured(keys, monkeypatch, tmp_path):
    calls = []

    class Up:
        def upload_file(self, path, bucket, key):
            calls.append((key, path))

    monkeypatch.setattr(r2, "_client", lambda: Up())
    f = tmp_path / "x.mp4"
    f.write_bytes(b"0")
    assert r2.upload_render(f) is True
    assert calls == [("renders/x.mp4", str(f))]


def test_upload_render_skips_without_keys(monkeypatch, tmp_path):
    monkeypatch.delenv("R2_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("R2_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.setattr(r2, "ENV_FILE", r2.ENV_FILE.with_name("does-not-exist.env"))
    assert r2.upload_render(tmp_path / "x.mp4") is False
