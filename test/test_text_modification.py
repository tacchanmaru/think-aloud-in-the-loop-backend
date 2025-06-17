import base64
import os
import sys
import time
from typing import Tuple

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



def test_combined_approach(
    text_state: TextState, utterance: str, image_data: str, model: str = "gpt-4.1-nano"
) -> Tuple[float, TextState]:
    """新しいアプローチ（judge_and_plan_and_modify）をテスト"""
    usecase = TextModificationUseCase()
    # モデルを指定して新しいCombinedJudgePlanModifyインスタンスを作成
    from src.infra.gpt.combined_judge_plan_modify import CombinedJudgePlanModify
    usecase.combined_judge_plan_modify = CombinedJudgePlanModify(model=model)
    
    start_time = time.time()
    
    # 判定・計画・修正を一度に実行
    result = usecase.judge_and_plan_and_modify(
        text_state.current_text,
        utterance,
        text_state.history_summary,
        image_data,
    )

    if result.should_edit and result.modified_text:
        # planを出力
        if result.plan:
            logger.info(f"Edit plan (Combined-{model}): {result.plan}")
        
        # 履歴を更新
        history = TextModificationHistory(
            utterance=utterance,
            edit_plan=result.edit_plan or "Combined approach",
            original_text=text_state.current_text,
            modified_text=result.modified_text,
        )
        new_text_state = TextState(
            original_text=text_state.original_text,
            current_text=result.modified_text,
            history=text_state.history + [history],
            history_summary=usecase.update_history_summary(text_state.history + [history]),
        )
    else:
        new_text_state = text_state
    
    elapsed_time = time.time() - start_time
    return elapsed_time, new_text_state


def main(utterance_sequence: list[str]):
    logger.info("=== Text Modification Test Environment ===")

    # テストデータを読み込み
    original_text, image_data = load_test_data()
    logger.info(f"Original text:\n{original_text}")

    # 初期状態を設定
    initial_state = TextState(
        original_text=original_text,
        current_text=original_text,
        history=[],
        history_summary="",
    )

    # 各発話を順番に処理して2つのCombinedアプローチを比較
    combined_nano_state = initial_state
    combined_mini_state = initial_state
    
    total_combined_nano_time = 0.0
    total_combined_mini_time = 0.0

    for i, utterance in enumerate(utterance_sequence, 1):
        logger.info("=" * 80)
        logger.info(f"User input {i}: '{utterance}'")
        logger.info("=" * 80)

        # 統合アプローチ（nano）をテスト
        logger.info("--- Combined Approach with gpt-4.1-nano ---")
        combined_nano_time, new_combined_nano_state = test_combined_approach(combined_nano_state, utterance, image_data, "gpt-4.1-nano")
        total_combined_nano_time += combined_nano_time
        logger.info(f"Combined nano approach time: {combined_nano_time:.2f}s")
        logger.info(f"Combined nano result:\n{new_combined_nano_state.current_text}")

        # 統合アプローチ（mini）をテスト
        logger.info("--- Combined Approach with gpt-4.1-mini ---")
        combined_mini_time, new_combined_mini_state = test_combined_approach(combined_mini_state, utterance, image_data, "gpt-4.1-mini")
        total_combined_mini_time += combined_mini_time
        logger.info(f"Combined mini approach time: {combined_mini_time:.2f}s")
        logger.info(f"Combined mini result:\n{new_combined_mini_state.current_text}")

        
        # 状態を更新
        combined_nano_state = new_combined_nano_state
        combined_mini_state = new_combined_mini_state

    # 最終的な比較結果
    logger.info("=" * 80)
    logger.info("=== FINAL COMPARISON ===")
    logger.info("=" * 80)
    logger.info(f"Total combined nano approach time: {total_combined_nano_time:.2f}s")
    logger.info(f"Total combined mini approach time: {total_combined_mini_time:.2f}s")
    logger.info("")
    logger.info(f"Nano vs Mini time difference: {total_combined_nano_time - total_combined_mini_time:.2f}s")
    logger.info(f"{'Nano is faster' if total_combined_nano_time < total_combined_mini_time else 'Mini is faster'}")
    logger.info("")
    logger.info("Final text (Combined nano approach):")
    logger.info(combined_nano_state.current_text)
    logger.info("")
    logger.info("Final text (Combined mini approach):")
    logger.info(combined_mini_state.current_text)


if __name__ == "__main__":
    utterances = [
        "こんにちは",
        "もう少し詳しく書きたい",
        "もっと魅力的にしたい",
        "短くまとめたい",
        "まだ長すぎる",
    ]

    main(utterances)
