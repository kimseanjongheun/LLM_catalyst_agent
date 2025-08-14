import os
import matplotlib.pyplot as plt
import re
import ast
import pickle
import validation_node
import seaborn as sns
import pandas as pd
from hypothesis_node import MAIN_AGENT_MODEL_NAME
from sub_agent_node import SUB_AGENT_MODEL_NAME
from matplotlib.ticker import MaxNLocator
import numpy as np
from node_models import DEFAULT_SAVE_PATH, EXPERIMENT_REPEAT, MAIN_AGENT_MODEL_NAME, SUB_AGENT_MODEL_NAME


REPEAT_RESULT_PATH = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\results\main_{MAIN_AGENT_MODEL_NAME}_sub_{SUB_AGENT_MODEL_NAME}"
REPEAT_SAVE_PATH = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\validation_results\main_{MAIN_AGENT_MODEL_NAME}_sub_{SUB_AGENT_MODEL_NAME}\avg_repeat"


OPTIMAL_ENERGY = validation_node.OPTIMAL_ENERGY
OPTIMAL_ENERGY_THRESHOLD = validation_node.OPTIMAL_ENERGY_THRESHOLD

reference_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv"
reference_data = pd.read_csv(reference_data_path)
reference_energies = reference_data["adsorption_energy"].values.tolist()

TOP_2_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.02)] - OPTIMAL_ENERGY)
TOP_3_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.03)] - OPTIMAL_ENERGY)
TOP_10_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.1)] - OPTIMAL_ENERGY)

def avg_db_rank_progression_by_step():
    """
    각 step별로 DB rank를 계산하고 boxplot으로 시각화하는 함수
    """
    total_steps = {}
    total_adsorption_energies = {}
    total_db_ranks = {}

    # DB에서의 순위 계산을 위한 기준 데이터
    sorted_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv"
    sorted_data = pd.read_csv(sorted_data_path)
    catalyst_ranking = sorted_data["adsorption_energy"].values.tolist()
    catalyst_ranking = [abs(energy - OPTIMAL_ENERGY) for energy in catalyst_ranking]

    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            total_steps[repeat_num] = []
            total_adsorption_energies[repeat_num] = []
            total_db_ranks[repeat_num] = []
            
            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("validation_result"):
                    # step 번호 추출
                    step_match = re.search(r'step_(\d+)', file)
                    if step_match:
                        step = int(step_match.group(1))
                        
                        with open(os.path.join(REPEAT_RESULT_PATH, folder, file), "r", encoding="utf-8") as f:
                            lines = f.readlines()
                            if lines:
                                last_line = lines[-2].strip()
                                last_line = last_line.split(" ")[0]
                                try:
                                    adsorption_energy = float(last_line)
                                    total_steps[repeat_num].append(step)
                                    total_adsorption_energies[repeat_num].append(adsorption_energy)
                                    
                                    # DB rank 계산
                                    db_rank = 1
                                    for db_energy in catalyst_ranking:
                                        if db_energy < abs(adsorption_energy - OPTIMAL_ENERGY):
                                            db_rank += 1
                                        else:
                                            break
                                    total_db_ranks[repeat_num].append(db_rank)
                                    
                                except ValueError:
                                    print(f"Error parsing adsorption energy in {file}: {last_line}")

    # 모든 repeat에서 공통된 step들 찾기
    all_steps = set()
    for repeat_num in total_steps:
        all_steps.update(total_steps[repeat_num])
    common_steps = sorted(list(all_steps))
    
    # 각 step별로 DB rank 데이터 수집
    step_rank_data = {}
    for step in common_steps:
        step_ranks = []
        for repeat_num in total_db_ranks:
            if step in total_steps[repeat_num]:
                step_idx = total_steps[repeat_num].index(step)
                step_ranks.append(total_db_ranks[repeat_num][step_idx])
        step_rank_data[step] = step_ranks
    
    
    # Boxplot 생성
    plt.figure(figsize=(12, 8))
    
    # Boxplot 데이터 준비
    box_data = [step_rank_data[step] for step in common_steps]
    box_labels = [f'Step {step}' for step in common_steps]
    
    # Boxplot 그리기
    bp = plt.boxplot(box_data, labels=box_labels, patch_artist=True,
                    boxprops=dict(facecolor='lightblue', alpha=0.7),
                    medianprops=dict(color='red', linewidth=2),
                    flierprops=dict(marker='o', markerfacecolor='lightblue', markersize=5))
    
    # Top 5% 임계값 표시
    top_5_threshold = int(len(catalyst_ranking) * 0.05)
    plt.axhline(y=top_5_threshold, color='orange', linestyle='--', linewidth=2, 
                label=f'Top 5% Threshold ({top_5_threshold})', alpha=0.8)

    
    plt.xlabel('Step', fontsize=14)
    plt.ylabel('DB Rank', fontsize=14)
    plt.ylim(1, 450)
    title = f'DB Rank Progression by Step (Boxplot across {len(total_steps)} repeats)'
    # plt.title(f'DB Rank Progression by Step (Boxplot across {len(total_steps)} repeats)', fontsize=16)
    print(f"title: {title}")
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    
    # 통계 정보 추가
    final_ranks = step_rank_data[common_steps[-1]]
    if final_ranks:
        final_avg_rank = np.mean(final_ranks)
        final_std_rank = np.std(final_ranks)
        final_percentage = (final_avg_rank / len(catalyst_ranking)) * 100
        
        stats_text = f'Final Step ({common_steps[-1]}):\n'
        stats_text += f'Avg Rank: {final_avg_rank:.1f} ± {final_std_rank:.1f}\n'
        stats_text += f'Percentage: {final_percentage:.2f}%\n'
        stats_text += f'Min Rank: {min(final_ranks)}\n'
        stats_text += f'Max Rank: {max(final_ranks)}'
        
        plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, fontsize=11,
                 verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_db_rank_progression_by_step.pdf'), dpi=1200, bbox_inches='tight')
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_db_rank_progression_by_step.png'), dpi=1200, bbox_inches='tight')
    plt.close()
    
    return common_steps, step_rank_data


def avg_adsorption_energy_by_step():
    total_steps = {}
    total_adsorption_energies = {}


    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            total_steps[repeat_num] = []
            total_adsorption_energies[repeat_num] = {}
            
            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
                    step = int(file.split("_")[3])
                    total_steps[repeat_num].append(step)
                    with open(os.path.join(REPEAT_RESULT_PATH, folder, file), "rb") as f:
                        unique_results = pickle.load(f)
                        each_step_list = []
                        for result in unique_results:
                            if result.is_success:  # 성공한 시뮬레이션만 포함
                                energy_dict = {}
                                energy_dict[step] = result.adsorption_energy_eV
                                each_step_list.append(result.adsorption_energy_eV)
                        total_adsorption_energies[repeat_num][step] = each_step_list

    box_data = pd.DataFrame(columns=["Step", "Adsorption Energy List"])

    for repeat_num, energy_dict in total_adsorption_energies.items():
        for step, energy in energy_dict.items():
            # Step 값 설정
            box_data.loc[step, "Step"] = step
            
            # 기존 값이 리스트인지 확인
            if isinstance(box_data.loc[step, "Adsorption Energy List"], list):
                box_data.at[step, "Adsorption Energy List"].extend(list(energy))
            else:
                box_data.at[step, "Adsorption Energy List"] = list(energy)

    box_data = box_data.sort_values(by="Step")

    
    plt.figure(figsize=(10, 6))
    plt.boxplot(
    box_data["Adsorption Energy List"],
    patch_artist=True,
    boxprops=dict(linewidth=1, facecolor='orange', alpha=0.3),       # 박스 테두리 두께
    whiskerprops=dict(linewidth=1),   # 수염(whisker) 두께
    capprops=dict(linewidth=1),       # 끝 가로선(cap) 두께
    medianprops=dict(linewidth=1.5, color='black', alpha=1)     # 중앙선(median) 두께
    )
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Adsorption Energy (eV)', fontsize=12)
    plt.axhline(y=OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD, color='green', linestyle='--', linewidth=1, alpha=0.8, label=f"top 10% threshold: {OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD, color='green', linestyle='--', linewidth=1, alpha=0.8, label=f"top 10% threshold: {OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY, color='red', linestyle='--', linewidth=1, alpha=0.8, label=f"Optimal Energy: {OPTIMAL_ENERGY:.3f} eV")
    # plt.title('Adsorption Energy vs Step', fontsize=14)
    title = f'Adsorption Energy vs Step (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right', bbox_to_anchor=(0.97, 0.97))
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_unique_investigation_by_step.pdf'), dpi=1200, bbox_inches='tight')
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_unique_investigation_by_step.png'), dpi=1200, bbox_inches='tight')
    plt.close()


def avg_simulation_success_ratio_by_step():

    df = pd.DataFrame(columns=["Step", "success_count", "failed_count"])
    repeat_num_list = []

    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            repeat_num_list.append(repeat_num)
            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
                    step = int(file.split("_")[3])
                    with open(os.path.join(REPEAT_RESULT_PATH, folder, file), "rb") as f:
                        unique_results = pickle.load(f)
                        # Step, success_count, failed_count 초기화
                        if step not in df.index:
                            df.loc[step, "Step"] = step
                            df.loc[step, "success_count"] = 0
                            df.loc[step, "failed_count"] = 0

                        # 성공/실패 카운트
                        for r in unique_results:
                            if r.is_success:
                                df.loc[step, "success_count"] += 1
                            else:
                                df.loc[step, "failed_count"] += 1

    # Step 순으로 정렬
    df = df.sort_values(by="Step")
    df["success_count"] = df["success_count"].map(lambda x: x / max(repeat_num_list))
    df["failed_count"] = df["failed_count"].map(lambda x: x / max(repeat_num_list))

    steps = df["Step"].values.tolist()
    plt.figure(figsize=(10, 6))
    plt.bar(steps, df["success_count"], color="green", label="Success", alpha=0.9)
    plt.bar(steps, df["failed_count"], bottom=df["success_count"], color="red", label="Failed", alpha=0.6)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Number of Simulation', fontsize=12)
    # plt.title('Number of Success vs Failed Simulation by Step', fontsize=14)
    title = f'Number of Success vs Failed Simulation by Step (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.grid(True, alpha=0.3, axis='y')
    plt.legend(loc='upper right', bbox_to_anchor=(0.97, 0.97))
    # x, y축 눈금에 정수만 표기되도록 설정
    ax = plt.gca()    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune=None))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xticks(steps)
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_success_vs_failed_by_step.pdf'), dpi=1200)
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_success_vs_failed_by_step.png'), dpi=1200)
    plt.close()


def avg_result_distribution_histogram():
    total_steps = {}
    total_adsorption_energies = {}

    # DB에서의 순위 계산을 위한 기준 데이터
    sorted_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv"
    sorted_data = pd.read_csv(sorted_data_path)

    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            total_steps[repeat_num] = []
            total_adsorption_energies[repeat_num] = []
            
            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
                    step = int(file.split("_")[3])
                    total_steps[repeat_num].append(step)
                    with open(os.path.join(REPEAT_RESULT_PATH, folder, file), "rb") as f:
                        unique_results = pickle.load(f)
                        for result in unique_results:
                            if result.is_success:  # 성공한 시뮬레이션만 포함
                                total_adsorption_energies[repeat_num].append(result.adsorption_energy_eV)

    # 레퍼런스 DB 값 가져오기
    db_energies = reference_data["adsorption_energy"].values.tolist()

    all_simulation_energies = []
    for repeat_num, energy_list in total_adsorption_energies.items():
        all_simulation_energies.extend(energy_list)
    
    
    
    plt.figure(figsize=(12, 8))
    sns.kdeplot(db_energies, color='blue', label='Database Distribution', fill=True, alpha=0.5)
    sns.kdeplot(all_simulation_energies, color='red', label='Simulation Results', fill=True, alpha=0.5)
    
    plt.axvline(x=OPTIMAL_ENERGY, color='green', linestyle='--', linewidth=2, 
                label=f'Optimal Energy: {OPTIMAL_ENERGY:.3f} eV')
    
    plt.axvline(x=OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD, color='orange', linestyle=':', linewidth=1.5,
                label=f'Top 10% Threshold: {OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV')
    plt.axvline(x=OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD, color='orange', linestyle=':', linewidth=1.5,
                label=f'Top 10% Threshold: {OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV')
    
    plt.xlabel('Adsorption Energy (eV)', fontsize=12)
    plt.ylabel('Density', fontsize=12)
    # plt.title(f'Distribution Comparison: Database vs Simulation Results (Repeat {EXPERIMENT_REPEAT})', fontsize=14)
    title = f'Distribution Comparison: Database vs Simulation Results (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)
    
    # 통계 정보 추가
    db_mean = np.mean(db_energies)
    sim_mean = np.mean(all_simulation_energies)
    db_std = np.std(db_energies)
    sim_std = np.std(all_simulation_energies)
    
    stats_text = f'Database: μ={db_mean:.3f}, σ={db_std:.3f}, n={len(db_energies):,}\n'
    stats_text += f'Simulation: μ={sim_mean:.3f}, σ={sim_std:.3f}, n={len(all_simulation_energies):,}'
    
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_distribution_histogram_DB_vs_result.pdf'), dpi=1200, bbox_inches='tight')
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_distribution_histogram_DB_vs_result.png'), dpi=1200, bbox_inches='tight')
    plt.close()


def avg_cost_by_step():
    USD_TO_KRW = 1385
    price_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\price_by_model.csv"
    price_data = pd.read_csv(price_data_path)
    main_agent_price_df = price_data[price_data["model_name"] == MAIN_AGENT_MODEL_NAME]
    sub_agent_price_df = price_data[price_data["model_name"] == SUB_AGENT_MODEL_NAME]
    
    repeated_results_df_dict = {}
    
    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            df = pd.DataFrame(columns=["Step", "Main Agent Cost", "Sub Agent Cost", "Total Agent Cost"])

            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("token_usage_step_"):
                    # step 번호 추출
                    step_match = re.search(r'step_(\d+)', file)
                    if step_match:
                        step = int(step_match.group(1))
                        
                        token_usage_df = pd.read_csv(os.path.join(REPEAT_RESULT_PATH, folder, file))
                        main_agent_input_tokens = token_usage_df['main_agent_input_tokens'][0]
                        main_agent_output_tokens = token_usage_df['main_agent_output_tokens'][0]
                        sub_agent_input_tokens = token_usage_df['sub_agent_input_tokens'][0]
                        sub_agent_output_tokens = token_usage_df['sub_agent_output_tokens'][0]
                        
                        df.loc[step, "Step"] = step
                        df.loc[step, "Main Agent Cost"] = (main_agent_input_tokens * main_agent_price_df["input_token_price"].values[0] + main_agent_output_tokens * main_agent_price_df["output_token_price"].values[0]) / 1000000
                        df.loc[step, "Sub Agent Cost"] = (sub_agent_input_tokens * sub_agent_price_df["input_token_price"].values[0] + sub_agent_output_tokens * sub_agent_price_df["output_token_price"].values[0]) / 1000000
                        df.loc[step, "Total Agent Cost"] = df.loc[step, "Main Agent Cost"] + df.loc[step, "Sub Agent Cost"]

            df = df.sort_values(by="Step")
            repeated_results_df_dict[repeat_num] = df
    
    # 각 repeat의 step별 값을 리스트로 저장하는 코드입니다.
    cost_by_repeat = {}
    for repeat_num, df in repeated_results_df_dict.items():
        temp_cost_dict = {}
        for index, row in df.iterrows():
            temp_cost_dict[row["Step"]] = row["Total Agent Cost"]
        cost_by_repeat[repeat_num] = temp_cost_dict

    # step별로 repeat마다 cost를 모아서 리스트로 저장
    cost_by_step = {}
    for repeat_num, cost_dict in cost_by_repeat.items():
        for step, cost in cost_dict.items():
            if step not in cost_by_step:
                cost_by_step[step] = []
            cost_by_step[step].append(cost)


    # boxplot 그리기
    plt.figure(figsize=(10, 6))
    plt.boxplot(list(cost_by_step.values()), patch_artist=True,
                boxprops=dict(facecolor='lightgreen', alpha=0.7),
                medianprops=dict(color='red', linewidth=2),
                flierprops=dict(marker='o', markerfacecolor='lightgreen', markersize=5))
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Cost (USD)', fontsize=12)
    # plt.title('Step-wise Cost Distribution', fontsize=14)
    title = f'Step-wise Cost Distribution (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.grid(True, alpha=0.3)
    # total cost 계산 및 text box로 그래프에 추가   
    total_cost = 0
    for step, cost_list in cost_by_step.items():
        total_cost += sum(cost_list)
    print(f"total cost (USD): {total_cost} (KRW {total_cost * USD_TO_KRW})")
    plt.text(0.02, 0.98, f'Total Cost: {total_cost:.3f} USD', transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_cost_by_step.pdf'), dpi=1200)
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_cost_by_step.png'), dpi=1200)
    plt.close()


def avg_time_usage():
    df = pd.DataFrame(columns=["Repeat", "Time Usage"])
    for folder in os.listdir(REPEAT_RESULT_PATH):
        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("time_usage") and file.endswith(".txt"):
                    with open(os.path.join(REPEAT_RESULT_PATH, folder, file), "r") as f:
                        time_usage = f.read()
                    df.loc[repeat_num, "Repeat"] = repeat_num
                    df.loc[repeat_num, "Time Usage"] = float(time_usage.split(" ")[0])

    df = df.sort_values(by="Repeat")
    plt.figure(figsize=(10, 6))
    plt.plot(df["Repeat"], df["Time Usage"], marker='o', linewidth=2, markersize=8, linestyle='--', color='darkblue')
    plt.xlabel('Repeat', fontsize=12)
    plt.ylabel('Time Usage (s)', fontsize=12)
    # plt.title('Time Usage by Repeat', fontsize=14)
    title = f'Time Usage by Repeat (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_time_usage_by_repeat_line.pdf'), dpi=1200)
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_time_usage_by_repeat_line.png'), dpi=1200)
    plt.close()


    # 숫자형 보정
    df["Time Usage"] = pd.to_numeric(df["Time Usage"], errors="coerce")
    df = df.dropna(subset=["Time Usage"])

    plt.figure(figsize=(10, 6))
    # 리스트 안에 넘겨서 '하나의 분포'로 처리
    plt.violinplot([df["Time Usage"].values], showmeans=True, showmedians=True)
    plt.xlabel('Repeat', fontsize=12)
    plt.ylabel('Time Usage (s)', fontsize=12)
    title = f'Time Usage by Repeat (Repeat {EXPERIMENT_REPEAT})'
    print(f"title: {title}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_time_usage_by_repeat_violin.pdf'), dpi=1200)
    plt.savefig(os.path.join(REPEAT_SAVE_PATH, 'avg_time_usage_by_repeat_violin.png'), dpi=1200)
    plt.close()

    # 숫자형 변환 (혹시 문자열이 섞여 있을 경우 대비)
    df["Time Usage"] = pd.to_numeric(df["Time Usage"], errors="coerce")

    # NaN 제거
    time_usage_clean = df["Time Usage"].dropna()

    # 평균과 표준편차 계산
    mean_val = time_usage_clean.mean()
    std_val = time_usage_clean.std()

    # 출력
    print(f"Time Usage 평균: {mean_val:.2f} s")
    print(f"Time Usage 표준편차: {std_val:.2f} s")


def total_cost_time_table():
    cost_result_path = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\results"
    time_result_path = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\results"

    USD_TO_KRW = 1385
    price_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\price_by_model.csv"
    price_data = pd.read_csv(price_data_path)
    model_name_list = ["gpt-4o", "gpt-4o-mini", "gpt-5", "gpt-5-mini","gpt-5-nano"]
    main_agent_price_df_list = []
    sub_agent_price_df_list = []
    for model_name in model_name_list:
        main_agent_price_df_list.append(price_data[price_data["model_name"] == model_name])
        sub_agent_price_df_list.append(price_data[price_data["model_name"] == model_name])
    
    repeated_results_df_dict = {}
    
    for folder in os.listdir(cost_result_path):
        if folder.startswith("main_"):
            




        if folder.startswith("repeat_"):
            repeat_num = int(folder.split("_")[1])
            df = pd.DataFrame(columns=["Step", "Main Agent Cost", "Sub Agent Cost", "Total Agent Cost"])

            for file in os.listdir(os.path.join(REPEAT_RESULT_PATH, folder)):
                if file.startswith("token_usage_step_"):
                    # step 번호 추출
                    step_match = re.search(r'step_(\d+)', file)
                    if step_match:
                        step = int(step_match.group(1))
                        
                        token_usage_df = pd.read_csv(os.path.join(REPEAT_RESULT_PATH, folder, file))
                        main_agent_input_tokens = token_usage_df['main_agent_input_tokens'][0]
                        main_agent_output_tokens = token_usage_df['main_agent_output_tokens'][0]
                        sub_agent_input_tokens = token_usage_df['sub_agent_input_tokens'][0]
                        sub_agent_output_tokens = token_usage_df['sub_agent_output_tokens'][0]
                        
                        df.loc[step, "Step"] = step
                        df.loc[step, "Main Agent Cost"] = (main_agent_input_tokens * main_agent_price_df["input_token_price"].values[0] + main_agent_output_tokens * main_agent_price_df["output_token_price"].values[0]) / 1000000
                        df.loc[step, "Sub Agent Cost"] = (sub_agent_input_tokens * sub_agent_price_df["input_token_price"].values[0] + sub_agent_output_tokens * sub_agent_price_df["output_token_price"].values[0]) / 1000000
                        df.loc[step, "Total Agent Cost"] = df.loc[step, "Main Agent Cost"] + df.loc[step, "Sub Agent Cost"]

            df = df.sort_values(by="Step")
            repeated_results_df_dict[repeat_num] = df
    
    # 각 repeat의 step별 값을 리스트로 저장하는 코드입니다.
    cost_by_repeat = {}
    for repeat_num, df in repeated_results_df_dict.items():
        temp_cost_dict = {}
        for index, row in df.iterrows():
            temp_cost_dict[row["Step"]] = row["Total Agent Cost"]
        cost_by_repeat[repeat_num] = temp_cost_dict

    # step별로 repeat마다 cost를 모아서 리스트로 저장
    cost_by_step = {}
    for repeat_num, cost_dict in cost_by_repeat.items():
        for step, cost in cost_dict.items():
            if step not in cost_by_step:
                cost_by_step[step] = []
            cost_by_step[step].append(cost)

    print(cost_by_step)





if __name__ == "__main__":
    print(f"experiment repeat: {EXPERIMENT_REPEAT}")
    print(f"main agent model name: {MAIN_AGENT_MODEL_NAME}")
    print(f"sub agent model name: {SUB_AGENT_MODEL_NAME}")
    print(f"result path: {REPEAT_RESULT_PATH}")
    print(f"save path: {REPEAT_SAVE_PATH}")
    os.makedirs(REPEAT_SAVE_PATH, exist_ok=True)

    avg_db_rank_progression_by_step()
    avg_adsorption_energy_by_step()
    avg_simulation_success_ratio_by_step()
    avg_result_distribution_histogram()
    avg_cost_by_step()
    avg_time_usage()



