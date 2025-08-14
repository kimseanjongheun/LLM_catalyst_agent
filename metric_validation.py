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

RESULT_PATH = DEFAULT_SAVE_PATH
SAVE_PATH = fr"C:\Users\spark\Desktop\LLM_Catalyst_Agent\validation_results\main_{MAIN_AGENT_MODEL_NAME}_sub_{SUB_AGENT_MODEL_NAME}\repeat_{EXPERIMENT_REPEAT}"


OPTIMAL_ENERGY = validation_node.OPTIMAL_ENERGY
OPTIMAL_ENERGY_THRESHOLD = validation_node.OPTIMAL_ENERGY_THRESHOLD

reference_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv"
reference_data = pd.read_csv(reference_data_path)
reference_energies = reference_data["adsorption_energy"].values.tolist()

TOP_2_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.02)] - OPTIMAL_ENERGY)
TOP_3_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.03)] - OPTIMAL_ENERGY)
TOP_10_PERCENT_ENERGY_THRESHOLD = abs(sorted(reference_energies)[-int(len(reference_energies) * 0.1)] - OPTIMAL_ENERGY)


def best_catalyst_by_step():
    steps = []
    adsorption_energies = []

    for file in os.listdir(RESULT_PATH):
        if file.startswith("validation_result"):
            # step 번호 추출
            step_match = re.search(r'step_(\d+)', file)
            if step_match:
                step = int(step_match.group(1))
                
                with open(os.path.join(RESULT_PATH, file), "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-2].strip()
                        last_line = last_line.split(" ")[0]
                        try:
                            adsorption_energy = float(last_line)
                            steps.append(step)
                            adsorption_energies.append(adsorption_energy)
                        except ValueError:
                            print(f"Error parsing adsorption energy in {file}: {last_line}")

    # 데이터 정렬
    steps, adsorption_energies = zip(*sorted(zip(steps, adsorption_energies)))
    
    # DB에서의 순위 계산
    sorted_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\MamunHighT2019\sorted_adsorption_data_H_MamunHighT2019_abs.csv"
    sorted_data = pd.read_csv(sorted_data_path)
    catalyst_ranking = sorted_data["adsorption_energy"].values.tolist()
    catalyst_ranking = [abs(energy - OPTIMAL_ENERGY) for energy in catalyst_ranking]

    # 최종 DB 순위 계산 (마지막 step의 결과)
    final_energy = adsorption_energies[-1]
    final_rank = 1
    for db_energy in catalyst_ranking:
        if db_energy < abs(final_energy - OPTIMAL_ENERGY):
            final_rank += 1
        else:
            break
    
    final_percentage = (final_rank / len(catalyst_ranking)) * 100

    
    # 그래프 생성 1: 각 step별 최적 촉매 에너지 변화
    plt.figure(figsize=(10, 6))
    plt.plot(steps, adsorption_energies, 'bo-', linewidth=2, markersize=8)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Adsorption Energy (eV)', fontsize=12)
    plt.axhline(y=OPTIMAL_ENERGY + TOP_3_PERCENT_ENERGY_THRESHOLD, color='green', linestyle='--', linewidth=1, alpha=0.8, label=f"top 3% threshold: {OPTIMAL_ENERGY + TOP_3_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY - TOP_3_PERCENT_ENERGY_THRESHOLD, color='green', linestyle='--', linewidth=1, alpha=0.8, label=f"top 3% threshold: {OPTIMAL_ENERGY - TOP_3_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD, color='orange', linestyle='--', linewidth=1, alpha=0.8, label=f"top 10% threshold: {OPTIMAL_ENERGY + TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD, color='orange', linestyle='--', linewidth=1, alpha=0.8, label=f"top 10% threshold: {OPTIMAL_ENERGY - TOP_10_PERCENT_ENERGY_THRESHOLD:.3f} eV")
    plt.axhline(y=OPTIMAL_ENERGY, color='red', linestyle='--', linewidth=2, alpha=0.8, label=f"Optimal Energy: {OPTIMAL_ENERGY:.3f} eV")
    plt.title('Best Catalyst Adsorption Energy vs Step', fontsize=14)
    plt.legend(loc='upper right', bbox_to_anchor=(0.97, 0.97))
    plt.grid(True, alpha=0.3)
    plt.xticks(steps)

    # 데이터 포인트에 값 표시
    for i, (step, energy) in enumerate(zip(steps, adsorption_energies)):
        plt.annotate(f'{energy:.3f}', (step, energy), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)

    # 최종 DB 순위 텍스트 상자 추가 (왼쪽 위)
    text_box = f"Final DB Rank:\n{final_rank:,} / {len(catalyst_ranking):,}\nTop {final_percentage:.1f}%"
    plt.text(0.02, 0.98, text_box, transform=plt.gca().transAxes, 
             fontsize=11, verticalalignment='top', 
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))

    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'best_catalyst_energy_by_step.pdf'))
    plt.savefig(os.path.join(SAVE_PATH, 'best_catalyst_energy_by_step.png'))
    plt.close()

    # 그래프 생성 2: 각 step별 DB 순위 변화
    # 각 step별 DB 순위 변화를 보여주는 독립적인 그래프
    db_ranks = []
    for step, energy in zip(steps, adsorption_energies):
        # DB에서 현재 energy보다 좋은(낮은) 값의 개수 계산
        rank = 1
        for db_energy in catalyst_ranking:
            if db_energy < abs(energy - OPTIMAL_ENERGY):
                rank += 1
            else:
                break
        db_ranks.append(rank)
    
    # DB 순위 변화 그래프 생성
    plt.figure(figsize=(10, 6))
    plt.plot(steps, db_ranks, 'ro-', linewidth=2, markersize=8, label='DB Rank')
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Database Rank', fontsize=12)
    y_max = max([450] + db_ranks)  # 항상 최소 450 보장, 빈 리스트여도 동작
    plt.ylim(0, y_max)
    plt.title(f'Database Rank Progression by Step (Total: {len(catalyst_ranking)})', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.xticks(steps)
    plt.yticks(range(0, y_max + 1, 50))
    
    # 데이터 포인트에 순위 값 표시
    for i, (step, rank) in enumerate(zip(steps, db_ranks)):
        plt.annotate(f'{rank:,}', (step, rank), textcoords="offset points", 
                    xytext=(0,10), ha='center', fontsize=9)
    
    # 최종 순위 정보 텍스트 상자 추가 (왼쪽 위)
    final_rank_text = f"Final Rank:\n{db_ranks[-1]:,} / {len(catalyst_ranking):,}\nTop {final_percentage:.1f}%"
    plt.text(0.02, 0.98, final_rank_text, transform=plt.gca().transAxes, 
             fontsize=11, verticalalignment='top', 
             bbox=dict(boxstyle='round,pad=0.5', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'db_rank_progression_by_step.pdf'))
    plt.savefig(os.path.join(SAVE_PATH, 'db_rank_progression_by_step.png'))
    plt.close()
        

def success_ratio_by_step():
    df = pd.DataFrame(columns=["Step", "SimulationResult", "adsorption_energy_list"])
    for file in os.listdir(RESULT_PATH):
        if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
            step = int(file.split("_")[3])
            with open(os.path.join(RESULT_PATH, file), "rb") as f:
                unique_results = pickle.load(f)
                df.loc[step, "Step"] = step
                df.loc[step, "SimulationResult"] = unique_results
                adsorption_energy_list = []
                for r in unique_results:
                    if r.is_success:
                        adsorption_energy_list.append(r.adsorption_energy_eV)
                df.loc[step, "adsorption_energy_list"] = adsorption_energy_list

    df = df.sort_values(by="Step")

    plt.figure(figsize=(10, 6))
    plt.boxplot(
    df["adsorption_energy_list"],
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
    plt.title('Adsorption Energy vs Step', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right', bbox_to_anchor=(0.97, 0.97))
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'unique_investigation_by_step.pdf'), dpi=1200, bbox_inches='tight')
    plt.close()


def simulation_success_ratio_by_step():
    df = pd.DataFrame(columns=["Step", "SimulationResult", "success_count", "failed_count"])
    for file in os.listdir(RESULT_PATH):
        if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
            step = int(file.split("_")[3])
            with open(os.path.join(RESULT_PATH, file), "rb") as f:
                unique_results = pickle.load(f)
                df.loc[step, "Step"] = step
                df.loc[step, "SimulationResult"] = unique_results
                success_count = 0
                failed_count = 0
                for r in unique_results:
                    if r.is_success:
                        success_count += 1
                    else:
                        failed_count += 1
                df.loc[step, "success_count"] = success_count
                df.loc[step, "failed_count"] = failed_count

    df = df.sort_values(by="Step")
    steps = df["Step"].values.tolist()
    plt.figure(figsize=(10, 6))
    plt.bar(steps, df["success_count"], color="green", label="Success", alpha=0.9)
    plt.bar(steps, df["failed_count"], bottom=df["success_count"], color="red", label="Failed", alpha=0.6)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Number of Simulation', fontsize=12)
    plt.title('Number of Success vs Failed Simulation by Step', fontsize=14)
    plt.grid(True, alpha=0.3, axis='y')
    plt.legend(loc='upper right', bbox_to_anchor=(0.97, 0.97))
    # x, y축 눈금에 정수만 표기되도록 설정
    ax = plt.gca()    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune=None))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xticks(steps)
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'success_vs_failed_by_step.pdf'), dpi=1200)
    plt.savefig(os.path.join(SAVE_PATH, 'success_vs_failed_by_step.png'), dpi=1200)
    plt.close()


def result_distribution_histogram():
    # 전체 시뮬레이션 결과 분포와 전체 DB 결과 분포를 비교하는 함수
    all_simulation_energies = []
    for file in os.listdir(RESULT_PATH):
        if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
            with open(os.path.join(RESULT_PATH, file), "rb") as f:
                unique_results = pickle.load(f)
                for result in unique_results:
                    if result.is_success:  # 성공한 시뮬레이션만 포함
                        all_simulation_energies.append(result.adsorption_energy_eV)
    
    db_energies = reference_data["adsorption_energy"].values.tolist()
    
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
    plt.title('Distribution Comparison: Database vs Simulation Results', fontsize=14)
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
    plt.savefig(os.path.join(SAVE_PATH, 'distribution_histogram_DB_vs_result.pdf'), dpi=1200, bbox_inches='tight')
    plt.savefig(os.path.join(SAVE_PATH, 'distribution_histogram_DB_vs_result.png'), dpi=1200, bbox_inches='tight')
    plt.close()
    

def token_usage_by_step():
    df = pd.DataFrame(columns=["Step", "Main Agent", "Sub Agent"])
    for file in os.listdir(RESULT_PATH):
        if file.startswith("token_usage_step_") and file.endswith(".csv"):
            step_num = int(file.split("_")[-1].split(".")[0])
            token_usage_df = pd.read_csv(os.path.join(RESULT_PATH, file))
            main_agent_token_usage = token_usage_df['main_agent_total_tokens'][0]
            sub_agent_token_usage = token_usage_df['sub_agent_total_tokens'][0]
            
            df.loc[step_num, "Step"] = step_num
            df.loc[step_num, "Main Agent"] = main_agent_token_usage
            df.loc[step_num, "Sub Agent"] = sub_agent_token_usage

    df = df.sort_values(by="Step")
    steps = df["Step"].values.tolist()
    plt.figure(figsize=(10, 6))
    plt.bar(steps, df["Main Agent"], color="blue", label="Main Agent", alpha=0.9, width=0.35)
    plt.bar(steps, df["Sub Agent"], bottom=df["Main Agent"], color="orange", label="Sub Agent", alpha=0.9, width=0.35)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Token Usage', fontsize=12)
    plt.title('Token Usage by Step', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'token_usage_by_step.pdf'), dpi=1200)
    plt.savefig(os.path.join(SAVE_PATH, 'token_usage_by_step.png'), dpi=1200)
    plt.close()


def cost_by_step():
    USD_TO_KRW = 1385

    print(f"main agent model name: {MAIN_AGENT_MODEL_NAME}")
    print(f"sub agent model name: {SUB_AGENT_MODEL_NAME}")
    price_data_path = r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\price_by_model.csv"
    price_data = pd.read_csv(price_data_path)
    main_agent_price_df = price_data[price_data["model_name"] == MAIN_AGENT_MODEL_NAME]
    sub_agent_price_df = price_data[price_data["model_name"] == SUB_AGENT_MODEL_NAME]
    
    df = pd.DataFrame(columns=["Step"])
    for file in os.listdir(RESULT_PATH):
        if file.startswith("token_usage_step_") and file.endswith(".csv"):
            step_num = int(file.split("_")[-1].split(".")[0])
            token_usage_df = pd.read_csv(os.path.join(RESULT_PATH, file))
            main_agent_input_tokens = token_usage_df['main_agent_input_tokens'][0]
            main_agent_output_tokens = token_usage_df['main_agent_output_tokens'][0]
            sub_agent_input_tokens = token_usage_df['sub_agent_input_tokens'][0]
            sub_agent_output_tokens = token_usage_df['sub_agent_output_tokens'][0]
            
            df.loc[step_num, "Step"] = step_num
            df.loc[step_num, "Main Agent Cost"] = (main_agent_input_tokens * main_agent_price_df["input_token_price"].values[0] + main_agent_output_tokens * main_agent_price_df["output_token_price"].values[0]) / 1000000
            df.loc[step_num, "Sub Agent Cost"] = (sub_agent_input_tokens * sub_agent_price_df["input_token_price"].values[0] + sub_agent_output_tokens * sub_agent_price_df["output_token_price"].values[0]) / 1000000

    df = df.sort_values(by="Step")
    steps = df["Step"].values.tolist()

    # USD 그래프
    plt.figure(figsize=(10, 6))
    plt.bar(steps, df["Main Agent Cost"], color="blue", label=f"Main Agent Cost ({MAIN_AGENT_MODEL_NAME})", alpha=0.9, width=0.35)
    plt.bar(steps, df["Sub Agent Cost"], bottom=df["Main Agent Cost"], color="orange", label=f"Sub Agent Cost ({SUB_AGENT_MODEL_NAME})", alpha=0.9, width=0.35)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Cost (USD)', fontsize=12)
    plt.title('Cost by Step', fontsize=14)
    total_cost_usd = df["Main Agent Cost"].sum() + df["Sub Agent Cost"].sum()
    total_cost_krw = total_cost_usd * USD_TO_KRW
    plt.text(
        0.99, 0.98,
        f"Total: ${total_cost_usd:,.2f} (₩{total_cost_krw:,.0f})",
        fontsize=13,
        color="black",
        ha="right",
        va="top",
        transform=plt.gca().transAxes,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray')
    )
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'cost_by_step_USD.pdf'), dpi=1200)
    plt.savefig(os.path.join(SAVE_PATH, 'cost_by_step_USD.png'), dpi=1200)
    plt.close()

    # KRW 그래프
    plt.figure(figsize=(10, 6))
    plt.bar(steps, df["Main Agent Cost"] * USD_TO_KRW, color="blue", label=f"Main Agent Cost ({MAIN_AGENT_MODEL_NAME})", alpha=0.9, width=0.35)
    plt.bar(steps, df["Sub Agent Cost"] * USD_TO_KRW, bottom=df["Main Agent Cost"] * USD_TO_KRW, color="orange", label=f"Sub Agent Cost ({SUB_AGENT_MODEL_NAME})", alpha=0.9, width=0.35)
    plt.xlabel('Step', fontsize=12)
    plt.ylabel('Cost (KRW)', fontsize=12)
    plt.title('Cost (KRW) by Step', fontsize=14)
    plt.text(
        0.99, 0.98,
        f"Total: ₩{total_cost_krw:,.0f}",
        fontsize=13,
        color="black",
        ha="right",
        va="top",
        transform=plt.gca().transAxes,
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray')
    )
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'cost_by_step_KRW.pdf'), dpi=1200)
    plt.savefig(os.path.join(SAVE_PATH, 'cost_by_step_KRW.png'), dpi=1200)
    plt.close()


def top_candidates_by_step():
    df = pd.DataFrame(columns=["Step", "SimulationResult", "adsorption_energy_list",
    "top_3_count", "top_10_count", "top_2_count", "simulation_success_count", "estimated_random_success_count"])

    for file in os.listdir(RESULT_PATH):
        if file.startswith("simulation_result_step_") and file.endswith("_unique.pkl"):
            step = int(file.split("_")[3])
            with open(os.path.join(RESULT_PATH, file), "rb") as f:
                unique_results = pickle.load(f)
                df.loc[step, "Step"] = step
                df.loc[step, "SimulationResult"] = unique_results
                adsorption_energy_list = []
                for r in unique_results:
                    if r.is_success:
                        adsorption_energy_list.append(r.adsorption_energy_eV)
                df.loc[step, "adsorption_energy_list"] = adsorption_energy_list
                simulation_success_count = len(adsorption_energy_list)
                df.loc[step, "simulation_success_count"] = simulation_success_count
                # 랜덤 성공률 3%
                estimated_random_success_count = len(adsorption_energy_list) * 0.03
                df.loc[step, "estimated_random_success_count"] = estimated_random_success_count

    df = df.sort_values(by="Step")
    steps = df["Step"].values.tolist()
    for step in steps:
        adsorption_energy_list = df.loc[step, "adsorption_energy_list"]
        top_3_count = 0
        top_10_count = 0
        top_2_count = 0
        for energy in adsorption_energy_list:
            if abs(energy - OPTIMAL_ENERGY) < TOP_3_PERCENT_ENERGY_THRESHOLD:
                top_3_count += 1
            if abs(energy - OPTIMAL_ENERGY) < TOP_10_PERCENT_ENERGY_THRESHOLD:
                top_10_count += 1
            if abs(energy - OPTIMAL_ENERGY) < TOP_2_PERCENT_ENERGY_THRESHOLD:
                top_2_count += 1
        df.loc[step, "top_3_count"] = top_3_count
        df.loc[step, "top_10_count"] = top_10_count
        df.loc[step, "top_2_count"] = top_2_count

    # df["top_3_count"]의 값을 누적시켜서 step 별로 누적된 통과 후보군 개수를 꺾은선 그래프로 그려줘
    df["cumulative_top_3_count"] = df["top_3_count"].cumsum()
    df["cumulative_top_10_count"] = df["top_10_count"].cumsum()
    df["cumulative_top_2_count"] = df["top_2_count"].cumsum()
    df["cumulative_estimated_random_success_count"] = df["estimated_random_success_count"].cumsum()

    # Top 3% 후보군 누적 그래프 vs 랜덤 성공 그래프 비교
    plt.figure(figsize=(12, 8))
    plt.plot(steps, df["cumulative_top_3_count"], 
             marker='o', linewidth=2, markersize=8, linestyle='--',
             color='darkblue', label=f'Top 3% Candidates (≤{TOP_3_PERCENT_ENERGY_THRESHOLD:.3f} eV)')
    plt.plot(steps, df["cumulative_estimated_random_success_count"], 
             marker='s', linewidth=2, markersize=8, linestyle='--',
             color='darkred', label=f'Cumulative Random Selection Success (Top 3%)')

    for step in steps:
        plt.annotate(f'{df.loc[step, "cumulative_top_3_count"]:d}', 
                    (step, df.loc[step, "cumulative_top_3_count"]), 
                    textcoords="offset points", xytext=(0,10), ha='center', fontsize=9)
        plt.annotate(f'{df.loc[step, "cumulative_estimated_random_success_count"]:.2f}', 
                    (step, df.loc[step, "cumulative_estimated_random_success_count"]), 
                    textcoords="offset points", xytext=(0,-15), ha='center', fontsize=9)

    plt.xlabel('Step', fontsize=14)
    plt.ylabel('Cumulative Number of Candidates', fontsize=14)
    plt.title('Cumulative Top Candidates by Step', fontsize=16, fontweight='bold')
    # x, y축 눈금에 정수만 표기되도록 설정
    ax = plt.gca()    
    ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune=None))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xticks(steps)
    plt.legend(fontsize=12)
    plt.grid(True, alpha=0.3)
    
    
    # 최종 통계 정보 추가
    final_top_3 = df["cumulative_top_3_count"].iloc[-1]
    
    plt.text(0.02, 0.98, 
             f'Final Top 3%: {final_top_3}', 
             transform=plt.gca().transAxes, 
             fontsize=12, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(os.path.join(SAVE_PATH, 'cumulative_top_candidates_by_step.pdf'), dpi=1200, bbox_inches='tight')
    plt.savefig(os.path.join(SAVE_PATH, 'cumulative_top_candidates_by_step.png'), dpi=1200, bbox_inches='tight')
    plt.close()
    
    


if __name__ == "__main__":
    print(f"experiment repeat: {EXPERIMENT_REPEAT}")
    print(f"main agent model name: {MAIN_AGENT_MODEL_NAME}")
    print(f"sub agent model name: {SUB_AGENT_MODEL_NAME}")
    print(f"result path: {RESULT_PATH}")
    print(f"save path: {SAVE_PATH}")
    os.makedirs(SAVE_PATH, exist_ok=True)

    best_catalyst_by_step()
    success_ratio_by_step()
    simulation_success_ratio_by_step()
    result_distribution_histogram()
    token_usage_by_step()
    cost_by_step()
    top_candidates_by_step()



