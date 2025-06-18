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



def test_mini_approach(
    text_state: TextState, utterance: str, image_data: str
) -> Tuple[float, TextState]:
    """gpt-4.1-miniを使ったアプローチをテスト"""
    usecase = TextModificationUseCase()
    # gpt-4.1-miniを指定してCombinedJudgePlanModifyインスタンスを作成
    from src.infra.gpt.combined_judge_plan_modify import CombinedJudgePlanModify
    usecase.combined_judge_plan_modify = CombinedJudgePlanModify(model="gpt-4.1-mini")
    
    start_time = time.time()
    
    # 判定・計画・修正を一度に実行
    result = usecase.judge_and_plan_and_modify(
        text_state.current_text,
        utterance,
        text_state.history_summary,
        image_data,
        text_state.history,
    )

    if result.should_edit and result.modified_text:
        # planを出力
        if result.plan:
            logger.info(f"Edit plan: {result.plan}")
        
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
    logger.info("=== Text Modification Test Environment (Mini Only) ===")

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

    # gpt-4.1-miniでテスト
    mini_state = initial_state
    total_mini_time = 0.0

    for i, utterance in enumerate(utterance_sequence, 1):
        logger.info("=" * 80)
        logger.info(f"User input {i}: '{utterance}'")
        logger.info("=" * 80)

        # gpt-4.1-miniでテスト
        logger.info("--- Testing with gpt-4.1-mini ---")
        mini_time, new_mini_state = test_mini_approach(mini_state, utterance, image_data)
        total_mini_time += mini_time
        logger.info(f"Processing time: {mini_time:.2f}s")
        logger.info(f"Result:\n{new_mini_state.current_text}")
        
        # 状態を更新
        mini_state = new_mini_state

    # 最終結果
    logger.info("=" * 80)
    logger.info("=== FINAL RESULT ===")
    logger.info("=" * 80)
    logger.info(f"Total processing time: {total_mini_time:.2f}s")
    logger.info("")
    logger.info("Final text:")
    logger.info(mini_state.current_text)


if __name__ == "__main__":
    utterances = [
        "こんにちは",
        "もう少し詳しく書きたい",
        "元に戻して",
        "もっと魅力的にしたい",
        "短くまとめたい",
        "まだ長すぎる",
    ]

    main(utterances)
