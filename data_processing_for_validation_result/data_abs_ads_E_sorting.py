import pandas as pd
import sys
sys.path.append(r"C:\Users\spark\Desktop\LLM_Catalyst_Agent")
import validation_node 

OPTIMAL_ENERGY = validation_node.OPTIMAL_ENERGY


data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_MamunHighT2019.csv"
df = pd.read_csv(data_path)
sorted_df = df.loc[(df["adsorption_energy"] - OPTIMAL_ENERGY).abs().sort_values().index].reset_index(drop=True)

sorted_df.to_csv(r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv", index=False)
print(sorted_df.head())
print("정렬 완료")