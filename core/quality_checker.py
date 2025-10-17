"""설정 가능한 품질 검증 시스템

YAML 설정 기반으로 품질 패턴을 관리
"""
import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """심각도"""
    INFO = "정보"
    WARNING = "경고"
    ERROR = "오류"
    CRITICAL = "치명적"


@dataclass
class QualityIssue:
    """품질 이슈"""
    file_path: str
    line_number: int
    text: str
    pattern: str
    description: str
    severity: Severity
    suggestion: Optional[str] = None


class QualityChecker:
    """품질 검사기"""

    def __init__(self, patterns_file: Optional[str] = None):
        """
        Args:
            patterns_file: 패턴 YAML 파일 경로
        """
        self.patterns = self._load_patterns(patterns_file)

    def _load_patterns(self, patterns_file: Optional[str]) -> List[Dict]:
        """패턴 로드"""
        if patterns_file and Path(patterns_file).exists():
            with open(patterns_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data.get('patterns', [])

        # 기본 패턴
        return [
            {
                'name': '인명_오역',
                'pattern': r'이치고',
                'description': '인명 오역 (二階堂 → 이치고)',
                'severity': 'ERROR',
                'suggestion': '니카이도'
            },
            {
                'name': '부자연스러운_표현',
                'pattern': r'싫어받',
                'description': '부자연스러운 표현 (싫어받다)',
                'severity': 'WARNING',
                'suggestion': '미움받다'
            },
            {
                'name': '전달_표현_오류',
                'pattern': r'[다라]래…',
                'description': '전달 표현 오류 (~래)',
                'severity': 'WARNING',
                'suggestion': '~라고, ~다고'
            },
            {
                'name': '의문사_오역',
                'pattern': r'뭐래',
                'description': '의문사 오역 (なんで → 뭐래)',
                'severity': 'ERROR',
                'suggestion': '왜, 어째서'
            }
        ]

    def check_text(self, text: str, file_path: str = "", line_number: int = 0) -> List[QualityIssue]:
        """텍스트 검증

        Args:
            text: 검증할 텍스트
            file_path: 파일 경로
            line_number: 줄번호

        Returns:
            발견된 이슈 리스트
        """
        issues = []

        for pattern_info in self.patterns:
            pattern = pattern_info['pattern']
            matches = re.finditer(pattern, text)

            for match in matches:
                severity = Severity[pattern_info.get('severity', 'WARNING')]

                issue = QualityIssue(
                    file_path=file_path,
                    line_number=line_number,
                    text=text[:100],  # 텍스트 일부만
                    pattern=pattern,
                    description=pattern_info['description'],
                    severity=severity,
                    suggestion=pattern_info.get('suggestion')
                )
                issues.append(issue)

        return issues

    def check_file(self, file_path: Path) -> List[QualityIssue]:
        """파일 검증

        Args:
            file_path: 검증할 파일 경로

        Returns:
            발견된 이슈 리스트
        """
        issues = []

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            # 주석이나 메타데이터 건너뛰기
            if line.strip().startswith(';') or line.strip().startswith('#'):
                continue

            line_issues = self.check_text(line, str(file_path), line_num)
            issues.extend(line_issues)

        return issues

    def check_directory(self, directory: Path, file_pattern: str = "*.txt") -> Dict[str, List[QualityIssue]]:
        """디렉토리 검증

        Args:
            directory: 검증할 디렉토리
            file_pattern: 파일 패턴 (예: "*_KO.txt")

        Returns:
            파일별 이슈 딕셔너리
        """
        results = {}

        for file_path in directory.glob(file_pattern):
            issues = self.check_file(file_path)
            if issues:
                results[str(file_path)] = issues

        return results

    def generate_report(self, issues: List[QualityIssue], output_path: Optional[str] = None) -> str:
        """리포트 생성

        Args:
            issues: 이슈 리스트
            output_path: 리포트 저장 경로 (옵션)

        Returns:
            리포트 마크다운 텍스트
        """
        # 심각도별 분류
        by_severity = {}
        for issue in issues:
            severity = issue.severity.name
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        # 마크다운 생성
        report = "# 번역 품질 검사 리포트\n\n"
        report += f"**총 이슈**: {len(issues)}개\n\n"

        # 심각도별 요약
        report += "## 심각도별 요약\n\n"
        for severity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
            count = len(by_severity.get(severity, []))
            report += f"- **{Severity[severity].value}**: {count}개\n"

        # 상세 내용
        report += "\n## 상세 내역\n\n"

        for severity in ['CRITICAL', 'ERROR', 'WARNING', 'INFO']:
            severity_issues = by_severity.get(severity, [])
            if not severity_issues:
                continue

            emoji = {'CRITICAL': '🔴', 'ERROR': '❌', 'WARNING': '⚠️', 'INFO': 'ℹ️'}
            report += f"\n### {emoji.get(severity, '')} {Severity[severity].value}\n\n"

            for i, issue in enumerate(severity_issues, 1):
                report += f"#### 이슈 #{i}\n"
                report += f"- **파일**: {Path(issue.file_path).name}:{issue.line_number}\n"
                report += f"- **패턴**: `{issue.pattern}`\n"
                report += f"- **설명**: {issue.description}\n"
                report += f"- **내용**: {issue.text}\n"
                if issue.suggestion:
                    report += f"- **제안**: {issue.suggestion}\n"
                report += "\n"

        # 저장
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✅ 품질 리포트 저장: {output_path}")

        return report

    def add_pattern(self, name: str, pattern: str, description: str, severity: str = "WARNING", suggestion: str = ""):
        """패턴 추가

        Args:
            name: 패턴 이름
            pattern: 정규표현식 패턴
            description: 설명
            severity: 심각도 (INFO, WARNING, ERROR, CRITICAL)
            suggestion: 제안 사항
        """
        self.patterns.append({
            'name': name,
            'pattern': pattern,
            'description': description,
            'severity': severity,
            'suggestion': suggestion
        })

    def save_patterns(self, output_path: str):
        """패턴을 YAML로 저장

        Args:
            output_path: 저장할 YAML 파일 경로
        """
        data = {'patterns': self.patterns}

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False)

        print(f"✅ 품질 패턴 저장: {output_path}")


# 사용 예시
if __name__ == "__main__":
    # 1. 품질 검사기 생성
    checker = QualityChecker()

    # 2. 텍스트 검증
    text = "뭐래……저건 대체 누구야?"
    issues = checker.check_text(text, "test.txt", 297)

    # 3. 리포트 생성
    if issues:
        report = checker.generate_report(issues, "quality_report.md")
        print(report)
