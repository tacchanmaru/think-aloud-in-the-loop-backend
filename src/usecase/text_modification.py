import json
import re

from src.infra.gpt.edit_plan_generator import EditPlanGenerator
from src.infra.gpt.history_summarizer import HistorySummarizer
from src.infra.gpt.text_modifier import TextModifier
from src.lib.logger import LOGGER
from src.usecase.text_modification_types import (
    TextModificationHistory,
    TextModificationResult,
)


class TextModificationUseCase:
    def __init__(self) -> None:
        self.plan_generator = EditPlanGenerator(model="gpt-4.1-mini")
        self.modifier = TextModifier()
        self.history_summarizer = HistorySummarizer()
        self.logger = LOGGER

    def judge_and_plan(
        self,
        text: str,
        utterance: str,
        history_summary: str,
    ) -> TextModificationResult:
        """判定と修正計画の生成を行う."""
        result = self.plan_generator(text, utterance, history_summary)
        try:
            parsed_result = json.loads(result)
            # should_editの値に基づいて結果を返す
            return TextModificationResult(
                should_edit=parsed_result["should_edit"] == "yes",
                edit_plan=parsed_result["content"]
                if parsed_result["should_edit"] == "yes"
                else None,
            )
        except (json.JSONDecodeError, KeyError):
            # JSONパースに失敗した場合や必要なキーが存在しない場合は修正不要として扱う
            return TextModificationResult(should_edit=False)

    def apply_modification(
        self,
        text: str,
        edit_plan: str,
        history_context: str,
        image_base64: str | None = None,
    ) -> str:
        """修正計画に基づいてテキストを修正する."""
        # テキストに行番号を付与（空行はスキップ）
        lines = text.split("\n")
        numbered_lines = []
        for i, line in enumerate(lines):
            if line.strip():  # 空行でない場合のみ行番号を付与
                numbered_lines.append(f"{i + 1}: {line}")
        numbered_text = "\n".join(numbered_lines)

        # リトライ機能付きで修正指示を取得・適用
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                # 修正指示をGPTに送信
                modification_instructions = self.modifier(
                    numbered_text,
                    edit_plan,
                    history_context,
                    image_base64,
                )

                # 修正指示をパースして適用
                result = self._apply_line_modifications_with_empty_line_preservation(
                    text,
                    modification_instructions,
                )

                return result

            except Exception:
                if attempt < max_retries:
                    # リトライ時にはより具体的な指示を追加
                    retry_context = f"{history_context}\n\n前回の処理でエラーが発生しました。修正指示は「X行目をYに変更」の形式で出力してください。"
                    history_context = retry_context
                    continue
                # 最終的にエラーが続く場合は元のテキストを返す
                return text
        return text  # Ensure we always return a value

    def _apply_line_modifications_with_empty_line_preservation(
        self,
        original_text: str,
        instructions: str,
    ) -> str:
        """空行保持機能付きで行番号ベースの修正指示を適用する."""
        # 修正指示をパースして、追加処理が含まれているかチェック
        modifications = self._parse_modifications(instructions)
        has_insert_action = any(mod.get("action") == "insert_after" for mod in modifications)

        # 修正を適用
        result = self._apply_line_modifications(original_text, instructions)

        # 追加処理が含まれている場合は空行保持処理をスキップ
        if has_insert_action:
            return result

        # 空行の保持処理
        return self._preserve_empty_lines(original_text, result)

    def _apply_line_modifications(self, original_text: str, instructions: str) -> str:
        """行番号ベースの修正指示を適用する."""
        lines = original_text.split("\n")

        # 修正指示をパース
        modifications = self._parse_modifications(instructions)

        # パース結果をログ出力
        self.logger.debug("パースされた修正指示: %s", modifications)

        # 後ろから適用（行番号がずれないように）
        modifications.sort(key=lambda x: x["start_line"], reverse=True)

        for mod in modifications:
            action = mod.get("action", "modify")  # 後方互換性のためデフォルトはmodify
            start_line = mod["start_line"] - 1  # 0-indexedに変換
            end_line = mod["end_line"] - 1 if mod["end_line"] else start_line
            new_content = mod["content"]

            if action == "modify":
                # 行の修正
                if 0 <= start_line < len(lines):
                    new_lines = new_content.split("\n")
                    lines[start_line : start_line + 1] = new_lines

            elif action == "insert_after":
                # 行の後に追加
                if 0 <= start_line < len(lines):
                    new_lines = new_content.split("\n")
                    lines[start_line + 1 : start_line + 1] = new_lines
                elif start_line == len(lines):
                    # 最後の行の後に追加
                    new_lines = new_content.split("\n")
                    lines.extend(new_lines)

            elif action == "delete":  # noqa: SIM102
                # 行の削除
                if 0 <= start_line < len(lines) and 0 <= end_line < len(lines):
                    lines[start_line : end_line + 1] = []

        return "\n".join(lines)

    def _parse_modifications(self, instructions: str) -> list[dict]:
        """修正指示をパースして修正リストを生成する."""
        modifications = []

        # パターン1: "X行目をYに変更"
        pattern1 = r"(\d+)行目を(.+?)に変更"
        matches1 = re.findall(pattern1, instructions, re.DOTALL)

        for match in matches1:
            start_line = int(match[0])
            content = match[1].strip()

            modifications.append(
                {
                    "action": "modify",
                    "start_line": start_line,
                    "end_line": start_line,
                    "content": content,
                },
            )

        # パターン2: "X行目の後にYを追加"
        pattern2 = r"(\d+)行目の後に(.+?)を追加"
        matches2 = re.findall(pattern2, instructions, re.DOTALL)

        for match in matches2:
            target_line = int(match[0])
            content = match[1].strip()

            modifications.append(
                {
                    "action": "insert_after",
                    "start_line": target_line,
                    "end_line": target_line,
                    "content": content,
                },
            )

        # パターン3: "X-Y行目を削除" または "X行目を削除"
        pattern3 = r"(\d+)(?:-(\d+))?行目を削除"
        matches3 = re.findall(pattern3, instructions)

        for match in matches3:
            start_line = int(match[0])
            end_line = int(match[1]) if match[1] else start_line

            modifications.append(
                {
                    "action": "delete",
                    "start_line": start_line,
                    "end_line": end_line,
                    "content": "",
                },
            )

        # 修正指示が見つからない場合は元のテキストをそのまま返すため空のリストを返す
        return modifications

    def _preserve_empty_lines(self, original_text: str, modified_text: str) -> str:
        """元のテキストの空行パターンを修正後のテキストに適用する."""
        original_lines = original_text.split("\n")
        modified_lines = modified_text.split("\n")

        # 元のテキストの空行位置を記録
        empty_line_positions = []
        for i, line in enumerate(original_lines):
            if not line.strip():
                empty_line_positions.append(i)

        # 修正後のテキストが元の行数より少ない場合、空行を適切に挿入
        result_lines = modified_lines[:]

        # 各空行位置をチェックして、必要に応じて空行を追加
        for pos in empty_line_positions:
            if pos < len(result_lines):
                # その位置が空行でない場合、空行を挿入
                if pos < len(result_lines) and result_lines[pos].strip():
                    result_lines.insert(pos, "")
            elif pos == len(result_lines):
                # 末尾に空行を追加
                result_lines.append("")

        # 修正されたテキストの末尾が改行で終わっていない場合の処理
        if modified_text and not modified_text.endswith("\n") and original_text.endswith("\n"):
            # 元が改行で終わっていたら改行を保持
            return "\n".join(result_lines)

        return "\n".join(result_lines)

    def update_history_summary(self, history: list[TextModificationHistory]) -> str:
        """履歴のサマリーを生成する."""
        return self.history_summarizer(history)
