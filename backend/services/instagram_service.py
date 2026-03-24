import requests
import os

INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN") or os.getenv("META_ACESS_TOKEN")
GRAPH_URL = "https://graph.facebook.com/v21.0"


def _get_image_public_url(image_path: str) -> str:
    """Get public URL for the image so Meta API can fetch it."""
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
    )

    data = response.json()
    if "id" not in data:
        # Extract detailed error from Meta API
        error_detail = data.get("error", {})
        error_msg = error_detail.get("message", str(data))
        error_type = error_detail.get("type", "")
        error_code = error_detail.get("code", "")
        full_error = f"Meta API error: [{error_code}] {error_type}: {error_msg} | image_url={image_url}"
        raise Exception(full_error)

    return data["id"]


def publish_media_container(creation_id: str) -> str:
    """Step 2: Publish the media container."""
    response = requests.post(
        f"{GRAPH_URL}/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN,
        },
    )

    data = response.json()
    if "id" not in data:
        raise Exception(f"Erro ao publicar midia: {data}")

    return data["id"]


def get_post_permalink(post_id: str) -> str:
    """Get the permanent link for a published post."""
    response = requests.get(
        f"{GRAPH_URL}/{post_id}",
        params={
            "fields": "permalink",
            "access_token": ACCESS_TOKEN,
        },
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
