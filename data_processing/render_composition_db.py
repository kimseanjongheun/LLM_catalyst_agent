import pandas as pd
import json
import ast

# CSV 파일 경로
csv_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_compositions_fraction.csv"

# JSON 저장 경로
json_output_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\composition_dicts.json"

# CSV 파일 읽기
df = pd.read_csv(csv_path)

# 문자열 형태의 dict를 실제 dict로 변환
df['composition_fraction'] = df['composition_fraction'].apply(ast.literal_eval)

# 필요한 열만 추출하여 딕셔너리 리스트로 구성
result = [
    {
        "system_id": row['system_id'],
        "composition_fraction": row['composition_fraction']
    }
    for _, row in df.iterrows()
]

# JSON 저장
with open(json_output_path, 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"✅ 저장 완료: {json_output_path}")
