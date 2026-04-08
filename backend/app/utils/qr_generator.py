"""
Generates a QR code image pointing to the customer registration page.
Usage: docker compose run --rm backend python -m app.utils.qr_generator
"""
import io
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

from app.core.config import get_settings

settings = get_settings()


def generate_qr_bytes(url: str) -> bytes:
    """Return QR code as PNG bytes (for API response)."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
    )

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


def generate_qr_file(url: str, output_path: str = "nirviz_qr.png") -> str:
    """Save QR code as a PNG file and return the path."""
    data = generate_qr_bytes(url)
    with open(output_path, "wb") as f:
        f.write(data)
    print(f"✅ QR code saved to: {output_path}")
    print(f"   Points to: {url}")
    return output_path


if __name__ == "__main__":
    url = settings.next_public_api_url.replace(":8000", "") or "http://localhost"
    generate_qr_file(url, "nirviz_qr.png")
