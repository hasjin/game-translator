#!/usr/bin/env python3
"""
한국어 조사 자동 교정
"""
import re


def has_final_consonant(char: str) -> bool:
    """
    한글 문자가 받침(종성)이 있는지 확인

    Args:
        char: 한글 문자 1자

    Returns:
        받침 있으면 True, 없으면 False
    """
    if not char or len(char) != 1:
        return False

    # 한글 유니코드 범위 체크
    if not ('가' <= char <= '힣'):
        return False

    # 유니코드 계산: (초성 * 588) + (중성 * 28) + 종성 + 0xAC00
    code = ord(char) - 0xAC00
    final_consonant = code % 28

    return final_consonant != 0


def fix_particle_이가(text: str) -> str:
    """이/가 조사 교정"""
    def replace(match):
        prev_char = match.group(1)

        if has_final_consonant(prev_char):
            return prev_char + '이'
        else:
            return prev_char + '가'

    # 받침 체크하여 이/가 교정
    return re.sub(r'([가-힣])[이가](?=\s|[,.]|$)', replace, text)


def fix_particle_을를(text: str) -> str:
    """을/를 조사 교정"""
    def replace(match):
        prev_char = match.group(1)

        if has_final_consonant(prev_char):
            return prev_char + '을'
        else:
            return prev_char + '를'

    return re.sub(r'([가-힣])[을를](?=\s|[,.]|$)', replace, text)


def fix_particle_과와(text: str) -> str:
    """과/와 조사 교정"""
    def replace(match):
        prev_char = match.group(1)

        if has_final_consonant(prev_char):
            return prev_char + '과'
        else:
            return prev_char + '와'

    return re.sub(r'([가-힣])[과와](?=\s|[,.]|$)', replace, text)


def fix_particle_은는(text: str) -> str:
    """은/는 조사 교정"""
    def replace(match):
        prev_char = match.group(1)

        if has_final_consonant(prev_char):
            return prev_char + '은'
        else:
            return prev_char + '는'

    return re.sub(r'([가-힣])[은는](?=\s|[,.]|$)', replace, text)


def fix_all_particles(text: str) -> str:
    """모든 조사 일괄 교정"""
    text = fix_particle_이가(text)
    text = fix_particle_을를(text)
    text = fix_particle_과와(text)
    text = fix_particle_은는(text)
    return text


def test():
    """테스트"""
    test_cases = [
        ("자지이 커요", "자지가 커요"),
        ("자지가 커요", "자지가 커요"),
        ("정액를 쏟아", "정액을 쏟아"),
        ("정액을 쏟아", "정액을 쏟아"),
        ("책이 있다", "책이 있다"),
        ("책가 있다", "책이 있다"),
        ("사과와 배", "사과와 배"),
        ("사과과 배", "사과와 배"),
        ("밥은 먹었니", "밥은 먹었니"),
        ("밥는 먹었니", "밥은 먹었니"),
    ]

    print("=== 조사 교정 테스트 ===\n")
    for original, expected in test_cases:
        fixed = fix_all_particles(original)
        status = "✅" if fixed == expected else "❌"
        print(f"{status} '{original}' → '{fixed}' (예상: '{expected}')")


if __name__ == "__main__":
    test()
