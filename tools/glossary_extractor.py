"""용어집 자동 추출

게임 텍스트에서 고유명사, 전문용어 자동 추출 및 관리
"""
import re
from collections import Counter
from typing import List, Dict, Set
from pathlib import Path
import yaml
import MeCab  # 일본어 형태소 분석 (선택사항)


class GlossaryExtractor:
    """용어집 자동 추출기"""

    def __init__(self):
        self.proper_nouns = set()
        self.technical_terms = set()
        self.character_names = set()

        # MeCab 초기화 (일본어 분석)
        try:
            self.mecab = MeCab.Tagger()
        except:
            self.mecab = None
            print("⚠️ MeCab 없음 (일본어 분석 제한적)")

    def extract_from_text(self, text: str) -> Dict[str, Set[str]]:
        """텍스트에서 용어 추출"""
        results = {
            'proper_nouns': set(),
            'katakana_words': set(),
            'kanji_names': set(),
            'technical_terms': set()
        }

        # 1. 카타카나 단어 (외래어, 고유명사)
        katakana_pattern = r'[\u30A0-\u30FF]+'
        katakana_words = re.findall(katakana_pattern, text)
        results['katakana_words'].update(katakana_words)

        # 2. 한자 이름 (2-4글자)
        kanji_pattern = r'[\u4E00-\u9FFF]{2,4}'
        kanji_words = re.findall(kanji_pattern, text)
        results['kanji_names'].update(kanji_words)

        # 3. MeCab 형태소 분석
        if self.mecab:
            parsed = self.mecab.parse(text)
            for line in parsed.split('\n'):
                if '\t' in line:
                    surface, features = line.split('\t')
                    parts = features.split(',')

                    # 고유명사
                    if len(parts) > 0 and '名詞' in parts[0]:
                        if '固有名詞' in parts[1]:
                            results['proper_nouns'].add(surface)

                        # 인명
                        if len(parts) > 1 and '人名' in parts[1]:
                            self.character_names.add(surface)

        return results

    def extract_from_files(
        self,
        file_paths: List[str],
        min_frequency: int = 3
    ) -> Dict:
        """여러 파일에서 용어 추출

        Args:
            file_paths: 파일 경로 리스트
            min_frequency: 최소 출현 횟수

        Returns:
            추출된 용어 딕셔너리
        """
        all_terms = Counter()
        all_katakana = Counter()
        all_kanji = Counter()

        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            results = self.extract_from_text(text)

            all_terms.update(results['proper_nouns'])
            all_katakana.update(results['katakana_words'])
            all_kanji.update(results['kanji_names'])

        # 빈도 필터링
        glossary = {
            'character_names': [],
            'place_names': [],
            'item_names': [],
            'technical_terms': []
        }

        # 인명 (카타카나 + 한자)
        for term, freq in all_katakana.most_common():
            if freq >= min_frequency and len(term) >= 2:
                glossary['character_names'].append({
                    'jp': term,
                    'frequency': freq,
                    'type': 'katakana'
                })

        for term, freq in all_kanji.most_common():
            if freq >= min_frequency and 2 <= len(term) <= 4:
                glossary['character_names'].append({
                    'jp': term,
                    'frequency': freq,
                    'type': 'kanji'
                })

        return glossary

    def auto_categorize(self, terms: List[str]) -> Dict[str, List[str]]:
        """용어 자동 분류"""
        categories = {
            'character_names': [],
            'place_names': [],
            'item_names': [],
            'skill_names': [],
            'technical_terms': []
        }

        for term in terms:
            # 휴리스틱 분류
            if re.search(r'(スキル|魔法|技|術)', term):
                categories['skill_names'].append(term)
            elif re.search(r'(町|城|国|村|世界)', term):
                categories['place_names'].append(term)
            elif re.search(r'(剣|盾|鎧|薬|アイテム)', term):
                categories['item_names'].append(term)
            elif len(term) <= 6:  # 짧으면 인명으로 추정
                categories['character_names'].append(term)
            else:
                categories['technical_terms'].append(term)

        return categories

    def suggest_translations(
        self,
        term: str,
        existing_glossary: Dict = None
    ) -> List[str]:
        """번역 제안

        Args:
            term: 일본어 용어
            existing_glossary: 기존 용어집

        Returns:
            번역 후보 리스트
        """
        suggestions = []

        # 1. 기존 용어집 검색
        if existing_glossary and term in existing_glossary:
            suggestions.append(existing_glossary[term])

        # 2. 카타카나 → 한글 음차
        if re.match(r'^[\u30A0-\u30FF]+$', term):
            # 카타카나 음차표
            katakana_to_hangul = {
                'ア': '아', 'イ': '이', 'ウ': '우', 'エ': '에', 'オ': '오',
                'カ': '카', 'キ': '키', 'ク': '쿠', 'ケ': '케', 'コ': '코',
                'サ': '사', 'シ': '시', 'ス': '스', 'セ': '세', 'ソ': '소',
                'タ': '타', 'チ': '치', 'ツ': '츠', 'テ': '테', 'ト': '토',
                'ナ': '나', 'ニ': '니', 'ヌ': '누', 'ネ': '네', 'ノ': '노',
                'ハ': '하', 'ヒ': '히', 'フ': '후', 'ヘ': '헤', 'ホ': '호',
                'マ': '마', 'ミ': '미', 'ム': '무', 'メ': '메', 'モ': '모',
                'ヤ': '야', 'ユ': '유', 'ヨ': '요',
                'ラ': '라', 'リ': '리', 'ル': '루', 'レ': '레', 'ロ': '로',
                'ワ': '와', 'ヲ': '오', 'ン': 'ㅇ',
                'ガ': '가', 'ギ': '기', 'グ': '구', 'ゲ': '게', 'ゴ': '고',
                'ザ': '자', 'ジ': '지', 'ズ': '즈', 'ゼ': '제', 'ゾ': '조',
                'ダ': '다', 'ヂ': '지', 'ヅ': '즈', 'デ': '데', 'ド': '도',
                'バ': '바', 'ビ': '비', 'ブ': '부', 'ベ': '베', 'ボ': '보',
                'パ': '파', 'ピ': '피', 'プ': '푸', 'ペ': '페', 'ポ': '포',
                'ャ': '야', 'ュ': '유', 'ョ': '요',
                'ッ': '',  # 촉음
                'ー': '',  # 장음
            }

            hangul = ''
            for char in term:
                hangul += katakana_to_hangul.get(char, char)

            suggestions.append(hangul)

        return suggestions

    def export_to_yaml(
        self,
        glossary: Dict,
        output_path: str
    ):
        """YAML 용어집으로 내보내기"""
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(glossary, f, allow_unicode=True, sort_keys=False)

        print(f"✅ 용어집 내보내기: {output_path}")

    def interactive_review(self, terms: List[str]) -> Dict:
        """대화형 검수"""
        glossary = {}

        print("📝 용어집 검수 (Enter=건너뛰기, q=종료)")
        for i, term in enumerate(terms, 1):
            suggestions = self.suggest_translations(term)

            print(f"\n[{i}/{len(terms)}] {term}")
            if suggestions:
                print(f"  제안: {', '.join(suggestions)}")

            translation = input("  번역: ").strip()

            if translation.lower() == 'q':
                break
            elif translation:
                glossary[term] = translation

        return glossary


class ContextGlossary:
    """문맥 기반 용어집"""

    def __init__(self):
        self.context_map = {}  # {term: [(context, translation), ...]}

    def add_with_context(
        self,
        term: str,
        translation: str,
        context: str
    ):
        """문맥과 함께 추가"""
        if term not in self.context_map:
            self.context_map[term] = []

        self.context_map[term].append({
            'context': context,
            'translation': translation
        })

    def find_best_translation(
        self,
        term: str,
        current_context: str
    ) -> Optional[str]:
        """문맥에 가장 적합한 번역 찾기"""
        if term not in self.context_map:
            return None

        from difflib import SequenceMatcher

        best_match = None
        best_similarity = 0

        for entry in self.context_map[term]:
            similarity = SequenceMatcher(
                None,
                current_context,
                entry['context']
            ).ratio()

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = entry['translation']

        return best_match if best_similarity > 0.6 else None


# 사용 예시
if __name__ == "__main__":
    extractor = GlossaryExtractor()

    # 파일에서 추출
    files = list(Path("translation_work/extracted").glob("**/*.txt"))
    glossary = extractor.extract_from_files(files, min_frequency=5)

    print(f"추출된 용어: {len(glossary['character_names'])}개")

    # YAML 내보내기
    extractor.export_to_yaml(glossary, "auto_glossary.yaml")

    # 대화형 검수
    # reviewed = extractor.interactive_review(glossary['character_names'][:10])
