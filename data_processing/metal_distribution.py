import pandas as pd

data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_MamunHighT2019.csv"
df = pd.read_csv(data_path)

# Option 1: Using pandas value_counts on the concatenated Series
metal_counts = pd.concat([df['Metal1'], df['Metal2']]).value_counts()
print(metal_counts)

# If you want the result as a DataFrame:
metal_counts_df = (
    metal_counts
    .rename_axis('Metal')
    .reset_index(name='Count')
)
print(metal_counts_df)

# 모든 metal을 list 형식으로 출력
metal_list = metal_counts_df['Metal'].tolist()
print(metal_list)
