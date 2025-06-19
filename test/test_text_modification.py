import base64
import os
import sys
import time

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
) -> tuple[float, TextState]:
    """gpt-4.1-miniを使ったアプローチをテスト"""
    usecase = TextModificationUseCase()
    
    start_time = time.time()
    
    logger.info(f"Processing utterance: {utterance}")
    
    # 判定・計画・修正を一度に実行
    result = usecase.judge_and_plan_and_modify(
        text_state.current_text,
        utterance,
        text_state.history_summary,
        image_data,
        text_state.history,
    )

    if not result.should_edit:
        logger.info("No changes needed")
        new_text_state = text_state
    elif result.should_edit and result.modified_text:
        modified_text = result.modified_text
        plan = result.plan
        
        if not modified_text or not plan:
            logger.warning("No modified text generated")
            new_text_state = text_state
        else:
            # planを出力
            logger.info(f"Edit plan: {plan}")
            
            # 履歴を更新
            history = TextModificationHistory(
                utterance=utterance,
                edit_plan=plan,
                original_text=text_state.current_text,
                modified_text=modified_text,
            )
            text_state.history.append(history)
            text_state.current_text = modified_text
            
            # history_summaryを更新
            try:
                new_summary = usecase.update_history_summary(text_state.history)
                text_state.history_summary = new_summary
                logger.info(f"Updated history summary: {text_state.history_summary}")
            except Exception as e:
                logger.error(f"Error updating history summary: {e}")
            
            new_text_state = text_state
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
        "状態について詳しく教えて",
        "状態というか、どういうふうに使っていたかを書くべきかも",
        "状態も、種類などと合わせて箇条書きにして",
        "この文章で高く売れるかなー",
    ]

    main(utterances)
