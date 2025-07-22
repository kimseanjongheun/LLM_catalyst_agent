import csv
import os
from parse_last_system_composition import parse_last_system_composition
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import ast

def process_system(row, extxyz_dir):
    system_id = row["system_id"]
    extxyz_path = os.path.join(extxyz_dir, f"{system_id}.extxyz")
    if os.path.exists(extxyz_path):
        try:
            composition = parse_last_system_composition(extxyz_path)
        except Exception as e:
            composition = f"Error: {e}"
    else:
        composition = "File not found"
    return {"system_id": system_id, "composition": composition}

def write_compositions_to_csv(
    info_csv_path="data/hydrogen/system_info_with_adsorp.csv",
    output_csv_path="data/hydrogen/system_compositions.csv",
    extxyz_dir="data/hydrogen/1",
    max_workers=8
):
    """
    system_info_with_adsorp.csv에서 system_id에 대응하는 extxyz_path를 구해서
    parse_last_system_composition 함수에 넣어 받은 결과를 output_csv_path에 병렬로 기록합니다.
    tqdm으로 진행상황을 표시합니다.
    """
    with open(info_csv_path, encoding="utf-8-sig") as f:  # <- utf-8-sig로 변경
        reader = csv.DictReader(f)
        rows = list(reader)
        # 디버깅: 실제 헤더와 첫 row 확인
        # print("헤더:", reader.fieldnames)
        # if rows:
        #     print("첫 row:", rows[0])

    fieldnames = ["system_id", "composition"]
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(process_system, row, extxyz_dir) for row in rows]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Processing systems"):
            results.append(f.result())

    # tqdm은 병렬 결과가 순서가 섞일 수 있으므로, 원래 순서대로 정렬
    system_id_to_result = {r["system_id"]: r for r in results}
    ordered_results = [system_id_to_result[row["system_id"]] for row in rows]

    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in ordered_results:
            writer.writerow(r)

def convert_composition_to_fraction(
    input_csv_path="data/hydrogen/system_compositions.csv",
    output_csv_path="data/hydrogen/system_compositions_fraction.csv"
):
    """
    system_compositions.csv에서 H를 제외한 원소들의 비율이 합이 1이 되도록 소수비율로 변환하여 새로운 CSV로 저장합니다.
    """
    with open(input_csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    fieldnames = ["system_id", "composition_fraction"]
    with open(output_csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            system_id = row["system_id"]
            comp = row["composition"]
            # composition이 dict 형태의 문자열일 때만 처리
            try:
                comp_dict = ast.literal_eval(comp) if isinstance(comp, str) else comp
                if not isinstance(comp_dict, dict):
                    raise ValueError
                # H 제거
                comp_no_h = {k: v for k, v in comp_dict.items() if k != "H"}
                total = sum(comp_no_h.values())
                if total > 0:
                    fraction = {k: v/total for k, v in comp_no_h.items()}
                else:
                    fraction = {}
                writer.writerow({"system_id": system_id, "composition_fraction": fraction})
            except Exception:
                writer.writerow({"system_id": system_id, "composition_fraction": "Error or Not Available"})

# 사용 예시
if __name__ == "__main__":
    write_compositions_to_csv(max_workers=6)
    convert_composition_to_fraction()
    pass