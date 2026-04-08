from fastapi import APIRouter
from fastapi.responses import Response

from app.core.config import get_settings
from app.utils.qr_generator import generate_qr_bytes

settings = get_settings()
router = APIRouter()


@router.get(
    "/qr",
    response_class=Response,
    responses={200: {"content": {"image/png": {}}}},
    summary="Download the NIRVIZ registration QR code",
)
def get_qr_code():
    """Returns a PNG QR code pointing to the customer registration page."""
    url = settings.next_public_api_url.replace(":8000", "") or "http://localhost"
    image_bytes = generate_qr_bytes(url)
    return Response(content=image_bytes, media_type="image/png")
