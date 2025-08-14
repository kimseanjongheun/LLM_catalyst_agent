import pandas as pd

db_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_MamunHighT2019.csv"

df = pd.read_csv(db_path)

print(df.head().to_json(orient="records", force_ascii=False, indent=2))





