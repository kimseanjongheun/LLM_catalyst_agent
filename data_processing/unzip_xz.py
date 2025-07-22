import os
import lzma
from tqdm import tqdm

# Directory containing the txt.xz files
directory = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\1"

files = [f for f in os.listdir(directory) if f.endswith(".extxyz.xz")]

for filename in tqdm(files, desc="Extracting Files"):
    file_path = os.path.join(directory, filename)
    out_path = file_path[:-3]  # .xz 제거
    try:
        with lzma.open(file_path, "rb") as f_in, open(out_path, "wb") as f_out:
            f_out.write(f_in.read())
    except Exception as e:
        print(f"{filename} 처리 중 오류 발생: {e}")
        