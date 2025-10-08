"""게임 번역 도구 GUI 실행 스크립트

범용 일→한 게임 번역 도구
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv()

# API 키 확인
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("❌ ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")
    print("   .env 파일을 생성하고 API 키를 추가하세요:")
    print("   ANTHROPIC_API_KEY=your-api-key-here")
    sys.exit(1)

# GUI 실행
from gui.main_window import main

if __name__ == "__main__":
    main()
