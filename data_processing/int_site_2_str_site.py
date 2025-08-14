import pandas as pd

def int_site_2_str_site(site):
    site_mapping = {
        1: 'top',
        2: 'bridge', 
        3: 'hollow',
        4: 'fcc',
        5: 'hcp',
        0: '~'
    }
    return site_mapping[site]

csv_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_L12.csv"

int_site_df = pd.read_csv(csv_path)

str_site_df = int_site_df.copy()
str_site_df["Site"] = int_site_df["Site"].apply(int_site_2_str_site)

print(str_site_df.head())

# Site가 '~'인 행 제거
filtered_df = str_site_df[str_site_df["Site"] != "~"]

# 각 Site별 개수 통계 출력
site_counts = filtered_df["Site"].value_counts()
print("\n[Site별 개수 통계] (~ 제외)")
print(site_counts)


str_site_df.to_csv(r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_MamunHighT2019.csv", index=False)



