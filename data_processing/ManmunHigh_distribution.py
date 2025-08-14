import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

csv_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\adsorption_data_H_L12.csv"

df = pd.read_csv(csv_path)
ads_list = df["ads_energy"].tolist()

threshold = 0.25
top_ads_list = [ads for ads in ads_list if np.abs(ads) < threshold]

print("total data number: ", len(ads_list))
print("top data number: ", len(top_ads_list))
print("top data ratio: ", len(top_ads_list)/len(ads_list))


plt.hist(ads_list, bins=100, color="skyblue", edgecolor="black")
plt.title("ManmunHigh Distribution")
plt.xlabel("ads_energy")
plt.ylabel("ads_count")
plt.show()

plt.savefig(r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data_processing\ManmunHigh_distribution.png")



