import base64
import os
import sys

# テスト用のログディレクトリを設定（importの前に設定）
os.environ["LOG_DIR"] = "test/results"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.lib.logger import Logger
from src.usecase.text_modification import TextModificationUseCase
from src.usecase.text_modification_types import TextModificationHistory, TextState

# ロガーを初期化
logger = Logger()


def load_test_data():
    """テストデータを読み込む"""
    with open("test/ferret.txt", encoding="utf-8") as f:
        text = f.read()

    with open("test/ferret.jpeg", "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    return text, image_data


def main(utterance_sequence: list[str]):
    logger.info("=== Text Modification Test Environment ===")

    # テストデータを読み込み
    original_text, image_data = load_test_data()
    logger.info(f"Original text:\n{original_text}")

    # TextStateを初期化
    text_state = TextState(
        original_text=original_text,
        current_text=original_text,
        history=[],
        history_summary="",
    )

    # UseCaseを初期化
    usecase = TextModificationUseCase()

    # 各発話を順番に処理
    for i, utterance in enumerate(utterance_sequence, 1):
        logger.info("=" * 50)
        logger.info(f"User input {i}: '{utterance}'")
        logger.info("=" * 50)

        # 判定と計画
        result = usecase.judge_and_plan(
            text_state.current_text,
            utterance,
            text_state.history_summary,
        )

        logger.info(f"Should edit: {result.should_edit}")
        if result.edit_plan:
            logger.info(f"Edit plan: {result.edit_plan}")

            # 修正を適用
            modified_text = usecase.apply_modification(
                text_state.current_text,
                result.edit_plan,
                text_state.history_summary,
                image_data,
            )

            logger.info(f"Modified text:\n{modified_text}")

            # 履歴を更新
            history = TextModificationHistory(
                utterance=utterance,
                edit_plan=result.edit_plan,
                modified_text=modified_text,
            )
            text_state.history.append(history)
            text_state.current_text = modified_text
            text_state.history_summary = usecase.update_history_summary(text_state.history)

            logger.info(f"Updated history summary:\n{text_state.history_summary}")


if __name__ == "__main__":
    # デフォルトの発話シーケンス
    # utterances = [
    #     "もう少し詳しく書きたい",
    #     "もっと魅力的にしたい",
    # ]

    # 3つの発話を試したい場合は以下をコメントアウト
    utterances = [
        "もう少し詳しく書きたい",
        "もっと魅力的にしたい",
        "短くまとめたい"
    ]

    main(utterances)
