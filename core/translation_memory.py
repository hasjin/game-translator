"""번역 메모리 (Translation Memory) 시스템

동일한 문장은 재번역하지 않고 저장된 번역 재사용
→ 비용 절감 + 일관성 향상
"""
import sqlite3
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import json


class TranslationMemory:
    """번역 메모리 관리"""

    def __init__(self, db_path: str = "translation_memory.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.create_tables()

    def create_tables(self):
        """테이블 생성"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS translations (
                id TEXT PRIMARY KEY,
                source_text TEXT NOT NULL,
                target_text TEXT NOT NULL,
                source_lang TEXT DEFAULT 'ja',
                target_lang TEXT DEFAULT 'ko',
                engine TEXT,
                context TEXT,
                file_path TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
        ''')

        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS fuzzy_matches (
                source_hash TEXT,
                target_hash TEXT,
                similarity REAL,
                PRIMARY KEY (source_hash, target_hash)
            )
        ''')

        self.conn.execute('''
            CREATE INDEX IF NOT EXISTS idx_source_text
            ON translations(source_text)
        ''')

        self.conn.commit()

    def _generate_id(self, source_text: str, context: str = '') -> str:
        """고유 ID 생성"""
        raw = f"{source_text}:{context}"
        return hashlib.md5(raw.encode('utf-8')).hexdigest()

    def add(
        self,
        source_text: str,
        target_text: str,
        engine: str = 'unknown',
        context: str = '',
        file_path: str = ''
    ):
        """번역 추가"""
        tm_id = self._generate_id(source_text, context)

        self.conn.execute('''
            INSERT OR REPLACE INTO translations
            (id, source_text, target_text, engine, context, file_path, usage_count)
            VALUES (?, ?, ?, ?, ?, ?,
                COALESCE((SELECT usage_count + 1 FROM translations WHERE id = ?), 1))
        ''', (tm_id, source_text, target_text, engine, context, file_path, tm_id))

        self.conn.commit()

    def search(
        self,
        source_text: str,
        context: str = '',
        exact_match: bool = True
    ) -> Optional[Dict]:
        """번역 검색"""
        if exact_match:
            tm_id = self._generate_id(source_text, context)
            cursor = self.conn.execute('''
                SELECT target_text, engine, usage_count, created_at
                FROM translations
                WHERE id = ?
            ''', (tm_id,))
        else:
            # 유사 매치
            cursor = self.conn.execute('''
                SELECT target_text, engine, usage_count, created_at
                FROM translations
                WHERE source_text = ?
                ORDER BY usage_count DESC
                LIMIT 1
            ''', (source_text,))

        result = cursor.fetchone()
        if result:
            return {
                'target_text': result[0],
                'engine': result[1],
                'usage_count': result[2],
                'created_at': result[3]
            }
        return None

    def search_fuzzy(self, source_text: str, threshold: float = 0.8) -> List[Dict]:
        """유사 문장 검색"""
        from difflib import SequenceMatcher

        cursor = self.conn.execute('SELECT source_text, target_text FROM translations')
        results = []

        for row in cursor:
            similarity = SequenceMatcher(None, source_text, row[0]).ratio()
            if similarity >= threshold:
                results.append({
                    'source_text': row[0],
                    'target_text': row[1],
                    'similarity': similarity
                })

        return sorted(results, key=lambda x: x['similarity'], reverse=True)

    def batch_add(self, translations: List[Dict]):
        """배치 추가"""
        for trans in translations:
            self.add(
                source_text=trans['source'],
                target_text=trans['target'],
                engine=trans.get('engine', 'unknown'),
                context=trans.get('context', ''),
                file_path=trans.get('file_path', '')
            )

    def export_to_tmx(self, output_path: str):
        """TMX 형식으로 내보내기 (표준 TM 포맷)"""
        cursor = self.conn.execute('''
            SELECT source_text, target_text, created_at
            FROM translations
        ''')

        tmx = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE tmx SYSTEM "tmx14.dtd">
<tmx version="1.4">
<header creationtool="GameTranslator" creationtoolversion="1.0"
        datatype="plaintext" segtype="sentence"
        adminlang="ko" srclang="ja"/>
<body>
'''

        for row in cursor:
            source, target, created = row
            tmx += f'''
<tu creationdate="{created}">
    <tuv xml:lang="ja"><seg>{self._escape_xml(source)}</seg></tuv>
    <tuv xml:lang="ko"><seg>{self._escape_xml(target)}</seg></tuv>
</tu>'''

        tmx += '\n</body>\n</tmx>'

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(tmx)

        print(f"✅ TMX 내보내기 완료: {output_path}")

    def _escape_xml(self, text: str) -> str:
        """XML 이스케이프"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def get_statistics(self) -> Dict:
        """통계 정보"""
        cursor = self.conn.execute('SELECT COUNT(*), SUM(usage_count) FROM translations')
        total, total_usage = cursor.fetchone()

        cursor = self.conn.execute('SELECT engine, COUNT(*) FROM translations GROUP BY engine')
        by_engine = dict(cursor.fetchall())

        return {
            'total_entries': total or 0,
            'total_usage': total_usage or 0,
            'by_engine': by_engine,
            'savings': f"${(total_usage - total) * 0.000186:.2f}" if total_usage else "$0.00"
        }

    def cleanup_unused(self, min_usage: int = 1):
        """사용하지 않는 항목 정리"""
        self.conn.execute('DELETE FROM translations WHERE usage_count < ?', (min_usage,))
        self.conn.commit()

    def close(self):
        """연결 종료"""
        self.conn.close()


class TMIntegrationMixin:
    """번역기에 TM 통합"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tm = TranslationMemory()

    def translate_with_tm(self, text: str, context: str = '') -> str:
        """TM 우선 검색 → 없으면 AI 번역"""
        # 1. TM 검색
        cached = self.tm.search(text, context)
        if cached:
            print(f"  💾 TM 히트: {text[:30]}...")
            return cached['target_text']

        # 2. AI 번역
        translation = self.translate(text)

        # 3. TM 저장
        self.tm.add(text, translation, engine=self.__class__.__name__, context=context)

        return translation

    def translate_batch_with_tm(
        self,
        texts: List[str],
        context: str = ''
    ) -> List[str]:
        """배치 번역 with TM"""
        results = []
        to_translate = []
        indices = []

        # 1. TM 검색
        for i, text in enumerate(texts):
            cached = self.tm.search(text, context)
            if cached:
                results.append(cached['target_text'])
                print(f"  💾 TM 히트 [{i+1}/{len(texts)}]")
            else:
                results.append(None)
                to_translate.append(text)
                indices.append(i)

        # 2. 없는 것만 AI 번역
        if to_translate:
            print(f"  🤖 AI 번역: {len(to_translate)}개")
            translations = self.translate_batch(to_translate)

            # 3. 결과 병합 및 TM 저장
            for idx, trans in zip(indices, translations):
                results[idx] = trans
                self.tm.add(to_translate[indices.index(idx)], trans,
                           engine=self.__class__.__name__, context=context)

        return results


# 사용 예시
if __name__ == "__main__":
    tm = TranslationMemory()

    # 번역 추가
    tm.add("こんにちは", "안녕하세요", engine="claude_haiku")
    tm.add("ありがとう", "감사합니다", engine="claude_haiku")

    # 검색
    result = tm.search("こんにちは")
    print(f"번역: {result['target_text']}, 사용: {result['usage_count']}회")

    # 통계
    stats = tm.get_statistics()
    print(f"총 항목: {stats['total_entries']}")
    print(f"총 재사용: {stats['total_usage']}")
    print(f"절감 비용: {stats['savings']}")

    # TMX 내보내기
    tm.export_to_tmx("translation_memory.tmx")
