"""번역 분석 대시보드

번역 진행 상황, 비용, 품질 등을 시각화
"""
from pathlib import Path
from typing import Dict, List
import json
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없이 사용


class TranslationAnalytics:
    """번역 분석"""

    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.progress_file = self.project_dir / "translation_progress.json"
        self.tm_db = self.project_dir / "translation_memory.db"

    def load_progress(self) -> Dict:
        """진행 상황 로드"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def calculate_statistics(self) -> Dict:
        """통계 계산"""
        progress = self.load_progress()

        total_files = 0
        total_dialogues = 0
        total_cost = 0.0
        total_duration = 0.0

        completed = 0
        failed = 0

        for chapter, data in progress.items():
            total_files += data.get('file_count', 0)
            total_dialogues += data.get('dialogue_count', 0)
            total_cost += data.get('cost', 0)
            total_duration += data.get('duration', 0)

            if data.get('status') == '완료':
                completed += 1
            elif data.get('status') == '오류':
                failed += 1

        return {
            'total_chapters': len(progress),
            'completed_chapters': completed,
            'failed_chapters': failed,
            'total_files': total_files,
            'total_dialogues': total_dialogues,
            'total_cost': total_cost,
            'total_duration': total_duration,
            'avg_cost_per_dialogue': total_cost / total_dialogues if total_dialogues > 0 else 0,
            'dialogues_per_minute': total_dialogues / (total_duration / 60) if total_duration > 0 else 0
        }

    def generate_cost_report(self) -> str:
        """비용 리포트 생성"""
        stats = self.calculate_statistics()

        report = f"""# 번역 비용 리포트

## 📊 전체 통계

- **총 챕터**: {stats['total_chapters']}개
- **완료**: {stats['completed_chapters']}개
- **실패**: {stats['failed_chapters']}개
- **총 파일**: {stats['total_files']}개
- **총 대사**: {stats['total_dialogues']:,}개

## 💰 비용 분석

- **총 비용**: ${stats['total_cost']:.2f}
- **평균 비용/대사**: ${stats['avg_cost_per_dialogue']:.6f}
- **예상 전체 비용**: ${stats['total_cost'] * (stats['total_chapters'] / max(stats['completed_chapters'], 1)):.2f}

## ⏱️ 시간 분석

- **총 소요 시간**: {stats['total_duration'] / 60:.1f}분
- **번역 속도**: {stats['dialogues_per_minute']:.1f}개/분
- **예상 완료 시간**: {(stats['total_duration'] / 60) * (stats['total_chapters'] / max(stats['completed_chapters'], 1)):.1f}분

## 📈 효율성

- **시간당 대사**: {stats['dialogues_per_minute'] * 60:.0f}개
- **시간당 비용**: ${(stats['total_cost'] / (stats['total_duration'] / 3600)):.2f}
"""
        return report

    def plot_progress_chart(self, output_path: str = "progress_chart.png"):
        """진행 상황 차트"""
        progress = self.load_progress()

        chapters = list(progress.keys())
        dialogue_counts = [progress[ch].get('dialogue_count', 0) for ch in chapters]
        costs = [progress[ch].get('cost', 0) for ch in chapters]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

        # 대사 수 차트
        ax1.bar(range(len(chapters)), dialogue_counts, color='skyblue')
        ax1.set_title('챕터별 대사 수', fontsize=14, fontweight='bold')
        ax1.set_xlabel('챕터')
        ax1.set_ylabel('대사 수')
        ax1.set_xticks(range(len(chapters)))
        ax1.set_xticklabels([ch[:20] for ch in chapters], rotation=45, ha='right')

        # 비용 차트
        ax2.bar(range(len(chapters)), costs, color='coral')
        ax2.set_title('챕터별 번역 비용', fontsize=14, fontweight='bold')
        ax2.set_xlabel('챕터')
        ax2.set_ylabel('비용 ($)')
        ax2.set_xticks(range(len(chapters)))
        ax2.set_xticklabels([ch[:20] for ch in chapters], rotation=45, ha='right')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ 진행 차트 생성: {output_path}")

    def plot_quality_issues(self, output_path: str = "quality_chart.png"):
        """품질 이슈 차트"""
        progress = self.load_progress()

        issue_types = Counter()
        for chapter, data in progress.items():
            for issue in data.get('issues', []):
                issue_types[issue['issue']] += 1

        if not issue_types:
            print("이슈 없음")
            return

        # 파이 차트
        fig, ax = plt.subplots(figsize=(10, 8))

        labels = list(issue_types.keys())
        sizes = list(issue_types.values())

        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.set_title('품질 이슈 분포', fontsize=16, fontweight='bold')

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        print(f"✅ 품질 차트 생성: {output_path}")

    def generate_html_dashboard(self, output_path: str = "dashboard.html"):
        """HTML 대시보드 생성"""
        stats = self.calculate_statistics()
        cost_report = self.generate_cost_report()

        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>번역 분석 대시보드</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}
        .stat {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }}
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }}
        .stat-label {{
            font-size: 14px;
            color: #6c757d;
            margin-top: 5px;
        }}
        h1 {{ color: #333; }}
        h2 {{ color: #555; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #007bff, #0056b3);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎮 게임 번역 분석 대시보드</h1>

        <div class="card">
            <h2>📊 전체 통계</h2>
            <div class="stat-grid">
                <div class="stat">
                    <div class="stat-value">{stats['total_chapters']}</div>
                    <div class="stat-label">총 챕터</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats['completed_chapters']}</div>
                    <div class="stat-label">완료</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{stats['total_dialogues']:,}</div>
                    <div class="stat-label">총 대사</div>
                </div>
                <div class="stat">
                    <div class="stat-value">${stats['total_cost']:.2f}</div>
                    <div class="stat-label">총 비용</div>
                </div>
            </div>
        </div>

        <div class="card">
            <h2>📈 진행률</h2>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(stats['completed_chapters'] / stats['total_chapters'] * 100) if stats['total_chapters'] > 0 else 0:.1f}%">
                    {(stats['completed_chapters'] / stats['total_chapters'] * 100) if stats['total_chapters'] > 0 else 0:.1f}%
                </div>
            </div>
        </div>

        <div class="card">
            <h2>💰 비용 분석</h2>
            <ul>
                <li>평균 비용/대사: <strong>${stats['avg_cost_per_dialogue']:.6f}</strong></li>
                <li>번역 속도: <strong>{stats['dialogues_per_minute']:.1f}개/분</strong></li>
                <li>소요 시간: <strong>{stats['total_duration'] / 60:.1f}분</strong></li>
            </ul>
        </div>

        <div class="card">
            <h2>📉 차트</h2>
            <img src="progress_chart.png" style="width: 100%; max-width: 800px;">
        </div>

        <div class="card">
            <h2>📝 상세 리포트</h2>
            <pre style="background: #f8f9fa; padding: 15px; border-radius: 6px; overflow-x: auto;">{cost_report}</pre>
        </div>
    </div>
</body>
</html>"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ HTML 대시보드 생성: {output_path}")

    def export_full_report(self, output_dir: str = "reports"):
        """전체 리포트 내보내기"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. 비용 리포트 (MD)
        cost_report = self.generate_cost_report()
        with open(output_dir / "cost_report.md", 'w', encoding='utf-8') as f:
            f.write(cost_report)

        # 2. 진행 차트
        self.plot_progress_chart(str(output_dir / "progress_chart.png"))

        # 3. 품질 차트
        self.plot_quality_issues(str(output_dir / "quality_chart.png"))

        # 4. HTML 대시보드
        self.generate_html_dashboard(str(output_dir / "dashboard.html"))

        # 5. JSON 데이터
        stats = self.calculate_statistics()
        with open(output_dir / "statistics.json", 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)

        print(f"\n✅ 전체 리포트 생성 완료: {output_dir}/")
        print(f"   - cost_report.md")
        print(f"   - progress_chart.png")
        print(f"   - quality_chart.png")
        print(f"   - dashboard.html ← 브라우저로 열기")
        print(f"   - statistics.json")


# 사용 예시
if __name__ == "__main__":
    analytics = TranslationAnalytics(".")

    # 통계
    stats = analytics.calculate_statistics()
    print(f"총 대사: {stats['total_dialogues']:,}개")
    print(f"총 비용: ${stats['total_cost']:.2f}")

    # 전체 리포트
    analytics.export_full_report("reports")
