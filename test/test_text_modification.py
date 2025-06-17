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


def test_original_approach(
    text_state: TextState, utterance: str, image_data: str
) -> Tuple[float, TextState]:
    """元のアプローチ（judge_and_plan + apply_modification）をテスト"""
    usecase = TextModificationUseCase()
    
    start_time = time.time()
    
    # 判定と計画
    result = usecase.judge_and_plan(
        text_state.current_text,
        utterance,
        text_state.history_summary,
    )

    if result.should_edit and result.edit_plan:
        # planを出力
        if result.plan:
            logger.info(f"Edit plan (Original): {result.plan}")
        
        # 修正を適用
        modified_text = usecase.apply_modification(
            text_state.current_text,
            result.edit_plan,
            text_state.history_summary,
            image_data,
        )

        # 履歴を更新
        history = TextModificationHistory(
            utterance=utterance,
            edit_plan=result.edit_plan,
            original_text=text_state.current_text,
            modified_text=modified_text,
        )
        new_text_state = TextState(
            original_text=text_state.original_text,
            current_text=modified_text,
            history=text_state.history + [history],
            history_summary=usecase.update_history_summary(text_state.history + [history]),
        )
    else:
        new_text_state = text_state
    
    elapsed_time = time.time() - start_time
    return elapsed_time, new_text_state


def test_combined_approach(
    text_state: TextState, utterance: str, image_data: str
) -> Tuple[float, TextState]:
    """新しいアプローチ（judge_and_plan_and_modify）をテスト"""
    usecase = TextModificationUseCase()
    
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
            logger.info(f"Edit plan (Combined): {result.plan}")
        
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

    # 各発話を順番に処理して両方のアプローチを比較
    original_state = initial_state
    combined_state = initial_state
    
    total_original_time = 0.0
    total_combined_time = 0.0

    for i, utterance in enumerate(utterance_sequence, 1):
        logger.info("=" * 70)
        logger.info(f"User input {i}: '{utterance}'")
        logger.info("=" * 70)

        # 元のアプローチをテスト
        logger.info("--- Original Approach (judge_and_plan + apply_modification) ---")
        original_time, new_original_state = test_original_approach(original_state, utterance, image_data)
        total_original_time += original_time
        logger.info(f"Original approach time: {original_time:.2f}s")
        logger.info(f"Original result:\n{new_original_state.current_text}")

        # 新しいアプローチをテスト
        logger.info("--- Combined Approach (judge_and_plan_and_modify) ---")
        combined_time, new_combined_state = test_combined_approach(combined_state, utterance, image_data)
        total_combined_time += combined_time
        logger.info(f"Combined approach time: {combined_time:.2f}s")
        logger.info(f"Combined result:\n{new_combined_state.current_text}")

        # 比較結果を表示
        time_diff = original_time - combined_time
        logger.info("--- Comparison ---")
        logger.info(f"Time difference: {time_diff:.2f}s ({'Combined faster' if time_diff > 0 else 'Original faster'})")
        logger.info(f"Results match: {new_original_state.current_text == new_combined_state.current_text}")
        logger.info("")
        
        # 状態を更新
        original_state = new_original_state
        combined_state = new_combined_state

    # 最終的な比較結果
    logger.info("=" * 70)
    logger.info("=== FINAL COMPARISON ===")
    logger.info("=" * 70)
    logger.info(f"Total original approach time: {total_original_time:.2f}s")
    logger.info(f"Total combined approach time: {total_combined_time:.2f}s")
    logger.info(f"Time saved with combined approach: {total_original_time - total_combined_time:.2f}s")
    logger.info(f"Speed improvement: {((total_original_time - total_combined_time) / total_original_time * 100):.1f}%")
    logger.info("")
    logger.info("Final text (Original approach):")
    logger.info(original_state.current_text)
    logger.info("")
    logger.info("Final text (Combined approach):")
    logger.info(combined_state.current_text)


if __name__ == "__main__":
    utterances = [
        "こんにちは",
        "もう少し詳しく書きたい",
        "もっと魅力的にしたい",
        "短くまとめたい",
        "まだ長すぎる",
    ]

    main(utterances)
