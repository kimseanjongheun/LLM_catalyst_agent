import os

def parse_last_system_composition(extxyz_path):
    """
    지정한 .extxyz 파일에서 마지막 system을 읽고, 해당 system을 구성하는 금속의 조성을 dictionary로 반환합니다.
    예시 반환: {'V': 20, 'Ge': 15, 'H': 2}
    """
    with open(extxyz_path, encoding="utf-8") as f:
        lines = f.readlines()

    # 파일을 뒤에서부터 system 블록을 찾음
    idx = len(lines) - 1
    while idx >= 0:
        try:
            n_atoms = int(lines[idx].strip())
            # system 블록의 시작점 발견
            break
        except ValueError:
            idx -= 1
    else:
        raise ValueError("system 블록을 찾을 수 없습니다.")

    # system 블록 추출
    start = idx
    end = start + n_atoms + 2  # 원자수 + 헤더2줄
    system_lines = lines[start:end]

    # 원소 카운트
    composition = {}
    for line in system_lines[2:]:  # 앞 2줄은 헤더
        symbol = line.split()[0]
        if symbol.isalpha():
            composition[symbol] = composition.get(symbol, 0) + 1
    return composition

# 사용 예시
if __name__ == "__main__":
    path = "data/hydrogen/1/random999855.extxyz"
    print(parse_last_system_composition(path)) 