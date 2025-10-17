"""배치 번역 비교 도구

여러 엔진의 번역 결과를 비교하여 최적 선택
"""
from typing import List, Dict
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


class BatchComparer:
    """배치 번역 비교기"""

    def __init__(self, translators: Dict[str, any]):
        """
        Args:
            translators: {'engine_name': translator_instance}
        """
        self.translators = translators

    def compare_translations(
        self,
        texts: List[str],
        parallel: bool = True
    ) -> pd.DataFrame:
        """여러 엔진으로 번역하고 비교

        Args:
            texts: 번역할 텍스트 리스트
            parallel: 병렬 처리 여부

        Returns:
            DataFrame with columns: [원문, engine1, engine2, ...]
        """
        results = {'원문': texts}

        if parallel:
            with ThreadPoolExecutor(max_workers=len(self.translators)) as executor:
                futures = {}
                for name, translator in self.translators.items():
                    future = executor.submit(translator.translate_batch, texts)
                    futures[name] = future

                for name, future in futures.items():
                    results[name] = future.result()
        else:
            for name, translator in self.translators.items():
                print(f"  번역 중: {name}")
                results[name] = translator.translate_batch(texts)

        return pd.DataFrame(results)

    def compare_and_export(
        self,
        texts: List[str],
        output_excel: str
    ):
        """비교 결과를 Excel로 내보내기"""
        df = self.compare_translations(texts)

        # Excel 저장 (스타일 포함)
        with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='비교')

            worksheet = writer.sheets['비교']

            # 열 너비 조정
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter

                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass

                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

            # 헤더 스타일
            from openpyxl.styles import Font, PatternFill, Alignment

            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            header_font = Font(color="FFFFFF", bold=True)

            for cell in worksheet[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center')

        print(f"✅ 비교 결과 저장: {output_excel}")

    def find_best_engine(
        self,
        texts: List[str],
        criteria: str = 'consistency'
    ) -> str:
        """최적 엔진 찾기

        Args:
            texts: 테스트 텍스트
            criteria: 'consistency' | 'diversity' | 'speed'

        Returns:
            최적 엔진 이름
        """
        df = self.compare_translations(texts)

        if criteria == 'consistency':
            # 번역 일관성 (같은 원문 → 같은 번역)
            scores = {}
            for engine in self.translators.keys():
                unique_ratio = len(df[engine].unique()) / len(df[engine])
                scores[engine] = 1 - unique_ratio  # 낮을수록 일관적

            best = max(scores, key=scores.get)
            print(f"일관성 최고: {best} ({scores[best]:.2%})")
            return best

        elif criteria == 'diversity':
            # 번역 다양성
            scores = {}
            for engine in self.translators.keys():
                unique_ratio = len(df[engine].unique()) / len(df[engine])
                scores[engine] = unique_ratio

            best = max(scores, key=scores.get)
            print(f"다양성 최고: {best} ({scores[best]:.2%})")
            return best

        return list(self.translators.keys())[0]

    def generate_comparison_report(
        self,
        texts: List[str],
        output_md: str
    ):
        """비교 리포트 생성"""
        df = self.compare_translations(texts)

        report = f"# 번역 엔진 비교 리포트\n\n"
        report += f"**테스트 대사 수**: {len(texts)}개\n\n"

        # 엔진별 통계
        report += "## 엔진별 통계\n\n"
        for engine in self.translators.keys():
            unique_count = len(df[engine].unique())
            avg_length = df[engine].str.len().mean()

            report += f"### {engine}\n"
            report += f"- 고유 번역: {unique_count}개\n"
            report += f"- 평균 길이: {avg_length:.1f}자\n\n"

        # 샘플 비교
        report += "## 샘플 비교 (처음 5개)\n\n"
        report += df.head(5).to_markdown(index=False)
        report += "\n"

        # 차이점 분석
        report += "\n## 주요 차이점\n\n"
        engines = list(self.translators.keys())
        if len(engines) >= 2:
            for i in range(min(10, len(df))):
                translations = [df[engines[j]][i] for j in range(len(engines))]
                if len(set(translations)) > 1:  # 다른 번역이 있으면
                    report += f"**원문**: {df['원문'][i]}\n\n"
                    for j, engine in enumerate(engines):
                        report += f"- {engine}: {translations[j]}\n"
                    report += "\n"

        with open(output_md, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 비교 리포트 생성: {output_md}")


class VotingTranslator:
    """투표 기반 번역 (여러 엔진 결과 중 다수결)"""

    def __init__(self, translators: Dict[str, any]):
        self.translators = translators

    def translate_with_voting(self, text: str) -> Dict:
        """투표로 번역 결정"""
        translations = {}

        for name, translator in self.translators.items():
            trans = translator.translate(text)
            translations[name] = trans

        # 투표
        from collections import Counter
        votes = Counter(translations.values())
        winner, count = votes.most_common(1)[0]

        return {
            'translation': winner,
            'votes': count,
            'total_engines': len(self.translators),
            'all_results': translations
        }

    def translate_batch_with_voting(
        self,
        texts: List[str]
    ) -> List[Dict]:
        """배치 투표 번역"""
        results = []

        for text in texts:
            result = self.translate_with_voting(text)
            results.append(result)

        return results


# 사용 예시
if __name__ == "__main__":
    from core.translation_engines import (
        ClaudeTranslator,
        GoogleTranslator,
        TranslationEngineFactory,
        TranslationEngine
    )

    # 여러 엔진 준비
    translators = {
        'Claude Haiku': TranslationEngineFactory.create(TranslationEngine.CLAUDE_HAIKU),
        'Google': TranslationEngineFactory.create(TranslationEngine.GOOGLE_TRANSLATE),
        # 'ChatGPT': TranslationEngineFactory.create(TranslationEngine.OPENAI_GPT4O),
    }

    # 비교기
    comparer = BatchComparer(translators)

    # 테스트 텍스트
    test_texts = [
        "こんにちは",
        "ありがとう",
        "さようなら"
    ]

    # 비교 결과 Excel
    comparer.compare_and_export(test_texts, "engine_comparison.xlsx")

    # 리포트 생성
    comparer.generate_comparison_report(test_texts, "comparison_report.md")

    # 최적 엔진 찾기
    best = comparer.find_best_engine(test_texts, criteria='consistency')
