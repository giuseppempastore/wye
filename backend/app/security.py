import hmac, os
from fastapi import Header, HTTPException

def require_image_api_key(x_wye_image_key: str | None = Header(default=None)):
    expected=os.getenv("WYE_IMAGE_API_KEY")
    if not expected: raise HTTPException(503,"Image API is not configured")
    if not x_wye_image_key or not hmac.compare_digest(x_wye_image_key,expected): raise HTTPException(401,"Invalid image API credentials")
