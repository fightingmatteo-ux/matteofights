"""Cloudflare R2 (bucket matteofights-media) through its S3 API.

Keys: env R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY (locally read from secrets/control.env).
Bucket and endpoint: tools/cloud/cloud.json. Finished videos live at renders/<asset name>.

    import r2
    r2.put_file("renders/x.mp4", "media/.../x.mp4")
    r2.video("x.mp4")   # (size, presigned GET valid 6 h) or None when it isn't in R2
"""
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLOUD = REPO / "tools" / "cloud" / "cloud.json"
ENV_FILE = REPO / "secrets" / "control.env"
SIX_HOURS = 21600  # Instagram fetches the file minutes (sometimes longer) after we hand over the link


def _cfg():
    return json.loads(CLOUD.read_text(encoding="utf-8"))


def _keys():
    if not os.environ.get("R2_ACCESS_KEY_ID") and ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("R2_") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    return os.environ.get("R2_ACCESS_KEY_ID"), os.environ.get("R2_SECRET_ACCESS_KEY")


def configured():
    try:
        import boto3  # noqa: F401
    except ImportError:
        return False
    return all(_keys())


def _client():
    import boto3
    from botocore.config import Config
    key, secret = _keys()
    return boto3.client("s3", endpoint_url=_cfg()["r2_endpoint"], region_name="auto",
                        aws_access_key_id=key, aws_secret_access_key=secret,
                        config=Config(signature_version="s3v4"))


def _bucket():
    return _cfg()["r2_bucket"]


def put_file(key, path):
    _client().upload_file(str(path), _bucket(), key)


def get_file(key, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    _client().download_file(_bucket(), key, str(path))


def size(key):
    """Bytes, or None when the key doesn't exist."""
    from botocore.exceptions import ClientError
    try:
        return _client().head_object(Bucket=_bucket(), Key=key)["ContentLength"]
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
            return None
        raise


def exists(key):
    return size(key) is not None


def presign_get(key, expires=SIX_HOURS):
    return _client().generate_presigned_url("get_object", Params={"Bucket": _bucket(), "Key": key},
                                            ExpiresIn=expires)


def presign_put(key, expires=3600):
    return _client().generate_presigned_url("put_object", Params={"Bucket": _bucket(), "Key": key},
                                            ExpiresIn=expires)


def copy(src, dst):
    _client().copy_object(Bucket=_bucket(), Key=dst, CopySource={"Bucket": _bucket(), "Key": src})


def delete(key):
    _client().delete_object(Bucket=_bucket(), Key=key)


def video(asset):
    """(size, presigned URL) of renders/<asset> in R2, or None (not there, or R2 not set up here)."""
    if not configured():
        return None
    n = size(f"renders/{asset}")
    return (n, presign_get(f"renders/{asset}")) if n is not None else None


def video_url(asset, fallback):
    """Presigned R2 link when the render is in R2, else fallback(asset) (the media-release link)."""
    v = video(asset)
    return v[1] if v else fallback(asset)


if __name__ == "__main__":  # python3 -P tools/r2.py put KEY FILE | exists KEY | url KEY
    import sys
    cmd, key = sys.argv[1], sys.argv[2]
    if cmd == "put":
        put_file(key, sys.argv[3])
        print(f"r2: {key}")
    elif cmd == "exists":
        sys.exit(0 if exists(key) else 1)
    elif cmd == "url":
        print(presign_get(key))
