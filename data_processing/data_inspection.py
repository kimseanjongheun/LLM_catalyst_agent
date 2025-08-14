import os
import pandas as pd
from tqdm import tqdm
from ase.io import read

def get_energy(system_id):
    path = fr'C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\1\{system_id}.extxyz'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    try:
        traj = read(path, ":")
        # 실제 에너지 계산 로직을 여기에 작성
        # 예시: 마지막 프레임의 에너지 반환
        return traj[-1].get_potential_energy()
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return None

if __name__ == "__main__":
    data_root = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen"
    df = pd.read_csv(os.path.join(data_root, 'system_info.csv'))
    tqdm.pandas(desc="Calculating energies")
    df['get_energy'] = df['system_id'].progress_apply(get_energy)
    df['adsorp_energy'] = df['get_energy'] - df['reference_energy']
    output_path = os.path.join(data_root, 'system_info_with_adsorp.csv')
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"새로운 파일로 저장 완료: {output_path}")
