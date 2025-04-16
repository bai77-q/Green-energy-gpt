import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from io import BytesIO
from PIL import Image
from starlette.responses import RedirectResponse

router = APIRouter()


@router.get("/proxy")
async def proxy_image(url: str):
    """通过图片的二进制流（解决跨域问题）"""
    async with httpx.AsyncClient() as client:
        try:
            # 从外部 URL 获取图片数据
            response = await client.get(url)
            media_type = response.headers["content-type"]
            if response.is_redirect:
                redirected_url = response.headers["location"]
                return await proxy_image(redirected_url)
            if response.status_code != 200 or not media_type.startswith("image/"):
                raise HTTPException(
                    status_code=response.status_code, detail="Failed to fetch image"
                )
            image_bytes = response.content
            image = Image.open(BytesIO(image_bytes)).convert("RGB")
            compress_bytes = BytesIO()
            image.save(compress_bytes, format="JPEG", quality=70)
            return Response(content=compress_bytes.getvalue(), media_type="image/jpeg")
        except Exception as e:
            print(e)
            return RedirectResponse("https://green-img.f2ee.com/system/placeholder.jpg")
