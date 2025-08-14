import os
import csv
import re

# 데이터 폴더 경로 (예: data/hydrogen/1)
data_root = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\1"
relaxed_dir = os.path.join(data_root, "relaxed_structures")
system_info_path = os.path.join(data_root, "system_info.csv")
output_csv = os.path.join(data_root, "research_area.csv")

# system_info.csv 읽기
data = []
with open(system_info_path, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        data.append(row)

# system_id에서 금속 조성 추출 함수 (예: Ni3Fe1_Cu2 → Ni3Fe1_Cu2)
def extract_composition(system_id):
    # system_id가 "조성_기타정보" 형태라면, 조성 부분만 추출
    # 예: Ni3Fe1_Cu2_001 → Ni3Fe1_Cu2
    return system_id.split("_")[0]

# relaxed_structures 파일 리스트
relaxed_files = set(os.listdir(relaxed_dir))

# 결과 저장
with open(output_csv, "w", newline='', encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["system_id", "composition", "relaxed_xyz_path"])
    for row in data:
        system_id = row["system_id"]
        composition = extract_composition(system_id)
        relaxed_name = f"{system_id}_relaxed.xyz"
        relaxed_path = os.path.join(relaxed_dir, relaxed_name)
        if relaxed_name in relaxed_files:
            writer.writerow([system_id, composition, relaxed_path])

print(f"{output_csv} 파일로 research area 정보를 저장 완료.")
