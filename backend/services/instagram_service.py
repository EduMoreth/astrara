import requests
import os
import base64
import time

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
GRAPH_URL = "https://graph.facebook.com/v21.0"


def get_access_token() -> str:
    """Meta access token. Prefers system_config (renewable from the admin panel
    without a redeploy); falls back to the env var. Long-lived tokens expire in
    ~60 days — see refresh_meta_token()."""
    try:
        from database import get_connection
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM system_config WHERE key = 'meta_access_token'")
        row = cur.fetchone()
        cur.close()
        conn.close()
        if row and (row.get("value") or "").strip():
            return row["value"].strip()
    except Exception as e:
        print(f"meta token config read error: {e}")
    return os.getenv("META_ACCESS_TOKEN") or os.getenv("META_ACESS_TOKEN") or ""


def save_access_token(token: str) -> None:
    """Persist the Meta token in system_config (used by admin panel + refresh)."""
    from database import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO system_config (key, value, description)
        VALUES ('meta_access_token', %s, 'Token de acesso Meta/Instagram (renovavel)')
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
    """, (token,))
    conn.commit()
    cur.close()
    conn.close()


def refresh_meta_token() -> dict:
    """Exchange the current long-lived token for a fresh one (extends the ~60-day
    expiry). Requires META_APP_ID + META_APP_SECRET. Persists to system_config."""
    app_id = os.getenv("META_APP_ID", "")
    app_secret = os.getenv("META_APP_SECRET", "")
    current = get_access_token()
    if not app_id or not app_secret:
        return {"success": False, "error": "META_APP_ID/META_APP_SECRET nao configurados"}
    if not current:
        return {"success": False, "error": "Nenhum token atual para renovar"}
    try:
        resp = requests.get(
            f"{GRAPH_URL}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": current,
            },
            timeout=30,
        )
        data = resp.json()
        new_token = data.get("access_token")
        if not new_token:
            print(f"Meta token refresh failed: {data.get('error')}")
            return {"success": False, "error": "Meta recusou a renovacao (token pode estar expirado)"}
        save_access_token(new_token)
        return {"success": True, "expires_in": data.get("expires_in")}
    except Exception as e:
        print(f"Meta token refresh error: {e}")
        return {"success": False, "error": "Erro de rede ao renovar token"}


def _upload_image_to_imgur(image_path: str) -> str:
    """Upload image to Imgur anonymously and return the public URL.
    This is needed because Meta Graph API requires a publicly accessible URL
    and Railway URLs may not be accessible to Meta's servers."""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        "https://api.imgur.com/3/image",
        headers={"Authorization": f"Client-ID {os.getenv('IMGUR_CLIENT_ID', '')}"},
        data={"image": image_data, "type": "base64"},
        timeout=60,
    )

    data = response.json()
    if not data.get("success"):
        raise Exception(f"Imgur upload failed: {data}")

    return data["data"]["link"]


def _get_image_public_url(image_path: str) -> str:
    """Get a publicly accessible URL for the image.
    First tries Imgur upload, falls back to Railway static files."""
    try:
        url = _upload_image_to_imgur(image_path)
        print(f"[INSTAGRAM] Image uploaded to Imgur: {url}")
        return url
    except Exception as e:
        print(f"[INSTAGRAM] Imgur upload failed ({e}), falling back to Railway URL")
        filename = os.path.basename(image_path)
        backend_url = os.getenv("BACKEND_URL", "https://astrara-production.up.railway.app")
        return f"{backend_url}/media/temp/{filename}"


def upload_image_to_meta(image_path: str, caption: str) -> str:
    """Step 1: Create media container with image URL."""
    access_token = get_access_token()
    if not INSTAGRAM_ACCOUNT_ID or not access_token:
        raise Exception("Instagram credentials not configured (INSTAGRAM_ACCOUNT_ID / META_ACCESS_TOKEN)")

    image_url = _get_image_public_url(image_path)

    response = requests.post(
        f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        },
        timeout=30,
    )

    data = response.json()
    if "id" not in data:
        error_detail = data.get("error", {})
        error_msg = error_detail.get("message", str(data))
        error_type = error_detail.get("type", "")
        error_code = error_detail.get("code", "")
        full_error = f"Meta API error: [{error_code}] {error_type}: {error_msg} | image_url={image_url}"
        raise Exception(full_error)

    return data["id"]


def publish_media_container(creation_id: str) -> str:
    access_token = get_access_token()
    """Step 2: Publish the media container.
    May need to wait for Meta to process the image."""
    max_retries = 5
    for attempt in range(max_retries):
        response = requests.post(
            f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": access_token,
            },
            timeout=30,
        )

        data = response.json()
        if "id" in data:
            return data["id"]

        # If media is still processing, wait and retry
        error = data.get("error", {})
        if error.get("code") == 9007:  # Media not ready
            print(f"[INSTAGRAM] Media not ready, retrying in 5s (attempt {attempt + 1}/{max_retries})")
            time.sleep(5)
            continue

        raise Exception(f"Erro ao publicar midia: {data}")

    raise Exception("Media processing timeout after retries")


def get_post_permalink(post_id: str) -> str:
    access_token = get_access_token()
    """Get the permanent link for a published post."""
    response = requests.get(
        f"{GRAPH_URL}/{post_id}",
        params={
            "fields": "permalink",
            "access_token": access_token,
        },
        timeout=15,
    )
    data = response.json()
    return data.get("permalink", "")


def publish_daily_post(image_path: str, caption: str) -> dict:
    """Complete publication flow."""
    creation_id = upload_image_to_meta(image_path, caption)
    post_id = publish_media_container(creation_id)
    permalink = get_post_permalink(post_id)

    return {
        "media_id": post_id,
        "permalink": permalink,
    }
