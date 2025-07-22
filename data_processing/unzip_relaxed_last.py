import os
import lzma
from tqdm import tqdm
from ase.io import read, write

# 데이터 폴더 경로 (예: data/hydrogen/1)
data_root = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\1"
output_dir = os.path.join(data_root, "relaxed_structures")
os.makedirs(output_dir, exist_ok=True)

files = [f for f in os.listdir(data_root) if f.endswith(".extxyz.xz")]

for filename in tqdm(files, desc="Extracting Files", total=len(files)):
    file_path = os.path.join(data_root, filename)
    out_name = filename.replace(".extxyz.xz", "_relaxed.xyz")
    out_path = os.path.join(output_dir, out_name)
    try:
        with lzma.open(file_path, "rt") as f:
            atoms = read(f, index=-1, format='extxyz')  # 마지막 프레임만 읽기
            write(out_path, atoms, format='xyz')
    except Exception as e:
        print(f"{filename} 처리 중 오류 발생: {e}")

print(f"총 {len(files)}개 파일의 relaxed 구조를 추출 완료.")
