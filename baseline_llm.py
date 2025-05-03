import base64

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.lib.env import ENV
from src.lib.logger import LOGGER
from src.usecase.edit_product_description import ProductDescriptionEditor
from src.usecase.generate_product_description import ProductDescriptionGenerator
from src.usecase.text_modification_types import TextState

app = FastAPI()

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを指定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = ENV.get("OPENAI_API_KEY")

# グローバルな状態管理
text_states: dict[str, TextState] = {}
image_data: dict[str, str] = {}

class EditRequest(BaseModel):
    prompt: str
    user_id: str
    current_text: str


@app.post("/api/generate-description")
async def generate_description(
    file: UploadFile = File(...),
    user_id: str = Form(...),
) -> dict:
    """画像から商品説明文を生成するエンドポイント.

    Args:
        file (UploadFile): アップロードされた画像ファイル
        user_id (str): ユーザーID

    Returns:
        dict: 生成された商品説明文とエラー情報（存在する場合）を含む辞書

    """
    try:
        LOGGER.info(f"Starting product description generation for user: {user_id}")

        # 画像データをBase64エンコード
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode()

        # 商品説明文を生成
        generator = ProductDescriptionGenerator()
        result = generator(base64_image)

        if result.error_message:
            LOGGER.error(f"Error generating description for user {user_id}: {result.error_message}")
            return {
                "success": False,
                "error": result.error_message,
            }

        LOGGER.info(f"Product description generated successfully for user: {user_id}")
        return {
            "success": True,
            "description": result.description,
        }

    except Exception as e:
        error_message = f"Error processing image: {e!s}"
        LOGGER.error(f"Error for user {user_id}: {error_message}")
        return {
            "success": False,
            "error": error_message,
        }


@app.post("/api/edit-description")
async def edit_description(request: EditRequest) -> dict:
    """商品説明文を編集するエンドポイント.

    Args:
        request (EditRequest): 編集リクエスト（プロンプト、ユーザーID、現在のテキスト）

    Returns:
        dict: 編集された商品説明文とエラー情報（存在する場合）を含む辞書

    """
    try:
        LOGGER.info(f"Starting product description edit for user: {request.user_id}")

        # ユーザーの画像データを取得（存在する場合）
        user_image = image_data.get(request.user_id)

        # 商品説明文を編集
        editor = ProductDescriptionEditor()
        result = editor(request.prompt, request.current_text, user_image)

        if result.error_message:
            LOGGER.error(
                f"Error editing description for user {request.user_id}: {result.error_message}",
            )
            return {
                "success": False,
                "error": result.error_message,
            }

        LOGGER.info(f"Product description edited successfully for user: {request.user_id}")
        return {
            "success": True,
            "edited_description": result.edited_description,
        }

    except Exception as e:
        error_message = f"Error editing description: {e!s}"
        LOGGER.error(f"Error for user {request.user_id}: {error_message}")
        return {
            "success": False,
            "error": error_message,
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "baseline_llm:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
