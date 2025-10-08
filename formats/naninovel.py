"""Naninovel 게임 포맷 파서

기존 naninovel_claude_translator를 범용 시스템에 통합
"""
from pathlib import Path
from typing import List, Dict, Optional
import re


class NaninovelParser:
    """Naninovel 스크립트 파서"""

    def __init__(self):
        pass

    def parse_file(self, file_path: str, max_dialogues: Optional[int] = None) -> List[Dict]:
        """Naninovel 파일 파싱

        Args:
            file_path: 파일 경로
            max_dialogues: 최대 대사 수 (디버깅용)

        Returns:
            대사 리스트 [{'id': str, 'japanese': str, 'line_number': int}, ...]
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        dialogues = []
        current_id = ""

        for i, line in enumerate(lines):
            if max_dialogues and len(dialogues) >= max_dialogues:
                break

            line_stripped = line.strip()

            # ID 라인 (#으로 시작)
            if line.startswith('#'):
                current_id = line_stripped

            # 일본어 원문 (;로 시작)
            elif line.startswith(';'):
                japanese = line[1:].strip()

                # 메타데이터 건너뛰기
                if '<ja>' in japanese or '<zh-Hans>' in japanese or 'localization document' in japanese:
                    continue

                # 스크립트 명령어 건너뛰기 (>로 시작)
                if japanese.startswith('>'):
                    continue

                # Ruby 태그 제거
                japanese = self.clean_ruby_tags(japanese)

                if japanese:
                    dialogues.append({
                        'id': current_id,
                        'japanese': japanese,
                        'line_number': i + 1  # 1-based
                    })

        return dialogues

    def clean_ruby_tags(self, text: str) -> str:
        """Ruby 태그 제거

        <ruby="reading">kanji</ruby> → kanji
        """
        text = re.sub(r'<ruby="[^"]*">([^<]+)</ruby>', r'\1', text)
        return text

    def save_translated(
        self,
        file_path: str,
        translations: List[Dict],
        output_path: str
    ):
        """번역 결과 저장

        Args:
            file_path: 원본 파일 경로
            translations: 번역 리스트 [{'japanese': str, 'korean': str, 'line_number': int}, ...]
            output_path: 출력 파일 경로
        """
        # 원본 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 번역 매핑 (줄번호 기반)
        translation_map = {t['line_number']: t['korean'] for t in translations}

        # 새 파일 생성
        output_lines = []
        for i, line in enumerate(lines):
            line_number = i + 1

            # ID나 원문 라인은 그대로 유지
            if line.startswith('#') or line.startswith(';'):
                output_lines.append(line)

            # 번역 추가 (해당 줄번호에 번역이 있으면)
            if line_number in translation_map:
                korean = translation_map[line_number]
                output_lines.append(korean + '\n')

            # 빈 줄 유지
            elif line.strip() == '':
                output_lines.append(line)

        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(output_lines)


class NaninovelTranslationAdapter:
    """Naninovel → 범용 시스템 어댑터"""

    def __init__(self, parser: NaninovelParser, translator):
        """
        Args:
            parser: NaninovelParser 인스턴스
            translator: UniversalTranslator 인스턴스
        """
        self.parser = parser
        self.translator = translator

    def translate_file(
        self,
        file_path: str,
        output_path: str,
        batch_size: int = 20,
        max_dialogues: Optional[int] = None
    ) -> List[Dict]:
        """파일 번역

        Args:
            file_path: 입력 파일
            output_path: 출력 파일
            batch_size: 배치 크기
            max_dialogues: 최대 대사 수

        Returns:
            번역 리스트
        """
        print(f"[1/3] 일본어 대사 추출 중...")

        # 1. 파싱
        dialogues = self.parser.parse_file(file_path, max_dialogues)
        print(f"  → {len(dialogues)}개 대사 발견")

        if not dialogues:
            print("  대사 없음")
            return []

        # 2. 번역
        print(f"[2/3] AI 번역 중 (배치 크기: {batch_size})...")
        translations = []

        for i in range(0, len(dialogues), batch_size):
            batch = dialogues[i:i + batch_size]
            texts = [d['japanese'] for d in batch]

            # 문맥 (이전 2개 대사)
            context = []
            if i > 0:
                prev_dialogues = dialogues[max(0, i - 2):i]
                context = [d['japanese'] for d in prev_dialogues]

            # 번역
            korean_batch = self.translator.translate_batch(texts, context)

            # 결과 저장
            for dialogue, korean in zip(batch, korean_batch):
                translations.append({
                    'japanese': dialogue['japanese'],
                    'korean': korean,
                    'line_number': dialogue['line_number']
                })

            # 진행률
            progress = min(i + batch_size, len(dialogues))
            print(f"  진행: {progress}/{len(dialogues)} ({progress * 100 // len(dialogues)}%)")

        # 3. 저장
        print(f"[3/3] 한국어 스크립트 생성 중...")
        self.parser.save_translated(file_path, translations, output_path)
        print(f"  → 저장: {output_path}")

        return translations


# 사용 예시
if __name__ == "__main__":
    from core.translator import UniversalTranslator

    # 1. 번역기 생성
    translator = UniversalTranslator()

    # 2. Naninovel 파서 & 어댑터
    parser = NaninovelParser()
    adapter = NaninovelTranslationAdapter(parser, translator)

    # 3. 파일 번역
    # translations = adapter.translate_file(
    #     "input.txt",
    #     "output_korean.txt",
    #     batch_size=20
    # )
