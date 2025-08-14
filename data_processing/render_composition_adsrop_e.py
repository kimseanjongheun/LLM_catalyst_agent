import pandas as pd
import json
import ast

# CSV 파일 경로
csv_comp_frac_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_compositions_fraction.csv"
csv_adsorp_e_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_info_with_adsorp.csv"

# JSON 저장 경로
json_output_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\composition_with_adsorp_energy.json"

# CSV 파일 읽기
df_comp_frac = pd.read_csv(csv_comp_frac_path)
df_adsorp_e = pd.read_csv(csv_adsorp_e_path)[['system_id', 'adsorp_energy']]

# 문자열을 dict로 변환
df_comp_frac['composition_fraction'] = df_comp_frac['composition_fraction'].apply(ast.literal_eval)

# 병합
df_merged = pd.merge(
    df_comp_frac[['system_id', 'composition_fraction']],
    df_adsorp_e,
    on='system_id',
    how='inner'
)

records = [
    {
        "system_id": row["system_id"],
        "composition_fraction": row["composition_fraction"],
        "adsorp_energy": row["adsorp_energy"]
    }
    for _, row in df_merged.iterrows()
]

# JSON 저장
with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"✅ 저장 완료: {json_output_path} (총 {len(records)}개 시스템)")