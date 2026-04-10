import requests
import os
import base64
import time

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN") or os.getenv("META_ACESS_TOKEN")
GRAPH_URL = "https://graph.facebook.com/v21.0"


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
    if not INSTAGRAM_ACCOUNT_ID or not ACCESS_TOKEN:
        raise Exception("Instagram credentials not configured (INSTAGRAM_ACCOUNT_ID / META_ACCESS_TOKEN)")

    image_url = _get_image_public_url(image_path)

    response = requests.post(
        f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": ACCESS_TOKEN,
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
    """Step 2: Publish the media container.
    May need to wait for Meta to process the image."""
    max_retries = 5
    for attempt in range(max_retries):
        response = requests.post(
            f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
            data={
                "creation_id": creation_id,
                "access_token": ACCESS_TOKEN,
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
    """Get the permanent link for a published post."""
    response = requests.get(
        f"{GRAPH_URL}/{post_id}",
        params={
            "fields": "permalink",
            "access_token": ACCESS_TOKEN,
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
