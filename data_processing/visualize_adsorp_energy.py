#!/usr/bin/env python3
"""visualize_adsorp_energy.py

data/hydrogen/system_info_with_adsorp.csv 파일을 불러와 adsorp_energy 값을 바탕으로
흡착 에너지 분포를 volcano plot으로 시각화합니다.

- 입력 파일: data/hydrogen/system_info_with_adsorp.csv
- 출력: data_processing/adsorp_energy_volcano.png
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# 파일 경로 설정
DATA_FILE = Path("data/hydrogen/system_info_with_adsorp.csv")
OUTPUT_PNG = Path("results/adsorp_energy_volcano.png")


def load_adsorp_data(path: Path) -> pd.DataFrame:
    """흡착 에너지 데이터를 로드합니다."""
    if not path.exists():
        raise FileNotFoundError(f"{path} 가 존재하지 않습니다.")
    
    df = pd.read_csv(path)
    print(f"[데이터 로드] {len(df)} 개의 시스템 데이터를 불러왔습니다.")
    print(f"흡착 에너지 범위: {df['adsorp_energy'].min():.3f} ~ {df['adsorp_energy'].max():.3f} eV")
    
    return df


def create_volcano_plot(df: pd.DataFrame, save_path: Path):
    """흡착 에너지 분포를 volcano plot으로 시각화합니다."""
    
    # 흡착 에너지 값 추출
    x_vals = df["adsorp_energy"].values
    
    # Volcano curve 생성 (eval_results.py와 동일한 방식)
    x_min, x_max = x_vals.min() - 0.2, x_vals.max() + 0.2
    x_curve = np.linspace(x_min, x_max, 400)
    c = max(abs(x_min), abs(x_max)) + 0.5  # height parameter
    y_curve = c - np.abs(x_curve)  # simple volcano
    
    # 각 점의 activity 계산
    activities = c - np.abs(x_vals)
    
    # 플롯 생성
    plt.figure(figsize=(12, 8))
    
    # Volcano curve 그리기
    plt.plot(x_curve, y_curve, label="Volcano curve", color="gray", linewidth=2, zorder=1)
    
    # 밀도 기반 점 크기 및 색상 조정을 위한 scatter plot
    # 1. 기본 scatter plot (투명도 효과)
    plt.scatter(x_vals, activities, alpha=0.3, s=25, color="blue", zorder=2, 
                label=f"Systems (n={len(df)})")
    
    # 2. 밀도 계산을 위해 2D histogram 사용
    hist, xedges, yedges = np.histogram2d(x_vals, activities, bins=30)
    
    # 각 점에 대해 해당하는 bin의 밀도 찾기
    x_indices = np.digitize(x_vals, xedges) - 1
    y_indices = np.digitize(activities, yedges) - 1
    
    # 인덱스 범위 조정
    x_indices = np.clip(x_indices, 0, hist.shape[0] - 1)
    y_indices = np.clip(y_indices, 0, hist.shape[1] - 1)
    
    # 각 점의 밀도 값 가져오기
    densities = hist[x_indices, y_indices]
    
    # 밀도에 따라 점 크기와 색상 조정
    # 밀도가 높은 점일수록 크고 진하게
    normalized_densities = densities / densities.max()
    point_sizes = 15 + normalized_densities * 40  # 15~55 크기 범위
    
    # 밀도가 높은 점들을 다시 그리기 (더 진하고 크게)
    high_density_mask = normalized_densities > 0.3
    if np.any(high_density_mask):
        plt.scatter(x_vals[high_density_mask], activities[high_density_mask], 
                   s=point_sizes[high_density_mask], 
                   c=normalized_densities[high_density_mask], 
                   cmap='Reds', alpha=0.7, zorder=3, 
                   edgecolors='darkred', linewidths=0.5)
    
    # 0 eV 지점에 수직선 표시
    plt.axvline(0, color="red", linestyle="--", linewidth=1.5, alpha=0.7, 
                label="Optimal binding (0 eV)", zorder=4)
    
    # 그래프 설정
    plt.xlabel("Adsorption Energy (eV)", fontsize=12)
    plt.ylabel("Relative Activity (arbitrary)", fontsize=12)
    plt.title(f"Volcano Plot with Density-based Point Sizing\n(system_info_with_adsorp.csv, n={len(df)})", 
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 파일 저장
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"[시각화 완료] {save_path} 저장")
    
    # 통계 정보 출력
    print(f"\n[통계 정보]")
    print(f"평균 흡착 에너지: {x_vals.mean():.3f} eV")
    print(f"표준 편차: {x_vals.std():.3f} eV")
    print(f"최적 바인딩(0 eV) 근처 (±0.1 eV) 시스템 수: {len(df[abs(df['adsorp_energy']) <= 0.1])}")
    print(f"고밀도 영역 점 개수: {np.sum(high_density_mask)}")


def create_histogram(df: pd.DataFrame, save_path: Path):
    """흡착 에너지 분포 히스토그램을 생성합니다."""
    
    plt.figure(figsize=(10, 6))
    
    # 히스토그램 생성
    n_bins = 50
    plt.hist(df['adsorp_energy'], bins=n_bins, alpha=0.7, color='skyblue', 
             edgecolor='black', linewidth=0.5)
    
    # 평균과 0 eV 지점 표시
    mean_energy = df['adsorp_energy'].mean()
    plt.axvline(mean_energy, color='orange', linestyle='-', linewidth=2, 
                label=f'Mean: {mean_energy:.3f} eV')
    plt.axvline(0, color='red', linestyle='--', linewidth=2, 
                label='Optimal binding (0 eV)')
    
    plt.xlabel("Adsorption Energy (eV)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.title("Distribution of Adsorption Energy\n(system_info_with_adsorp.csv)", 
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 히스토그램 저장
    hist_path = save_path.parent / (save_path.stem + "_histogram.png")
    plt.savefig(hist_path, dpi=150, bbox_inches='tight')
    print(f"[히스토그램 저장] {hist_path}")


def create_alpha_overlay_plot(df: pd.DataFrame, save_path: Path):
    """투명도만을 이용한 밀도 기반 흡착 에너지 분포 시각화"""
    
    # 흡착 에너지 값 추출
    x_vals = df["adsorp_energy"].values
    
    # Volcano curve 생성
    x_min, x_max = x_vals.min() - 0.2, x_vals.max() + 0.2
    x_curve = np.linspace(x_min, x_max, 400)
    c = max(abs(x_min), abs(x_max)) + 0.5
    y_curve = c - np.abs(x_curve)
    
    # 각 점의 activity 계산
    activities = c - np.abs(x_vals)
    
    # 플롯 생성
    plt.figure(figsize=(12, 8))
    
    # 밀도 계산을 위해 2D histogram 사용
    hist, xedges, yedges = np.histogram2d(x_vals, activities, bins=30)
    
    # 각 점에 대해 해당하는 bin의 밀도 찾기
    x_indices = np.digitize(x_vals, xedges) - 1
    y_indices = np.digitize(activities, yedges) - 1
    
    # 인덱스 범위 조정
    x_indices = np.clip(x_indices, 0, hist.shape[0] - 1)
    y_indices = np.clip(y_indices, 0, hist.shape[1] - 1)
    
    # 각 점의 밀도 값 가져오기
    densities = hist[x_indices, y_indices]
    
    # 밀도에 따라 점 투명도 조정
    # 밀도가 높은 점일수록 더 진하게
    normalized_densities = densities / densities.max()
    
    # 1. 먼저 모든 점을 기본 투명도로 그리기
    plt.scatter(x_vals, activities, alpha=0.15, s=8, color="blue", zorder=2, 
                label=f"Systems (n={len(df)})")
    
    # 2. 같은 점들을 여러 번 겹쳐서 그려서 자연스러운 밀도 효과 생성
    for i in range(3):
        plt.scatter(x_vals, activities, alpha=0.1, s=12, color="blue", zorder=2)
    
    # 3. 밀도가 높은 영역의 점들을 강조
    high_density_mask = normalized_densities > 0.4
    if np.any(high_density_mask):
        scatter = plt.scatter(x_vals[high_density_mask], activities[high_density_mask], 
                   c=normalized_densities[high_density_mask], 
                   cmap='Reds', 
                   s=25 + normalized_densities[high_density_mask] * 35,
                   alpha=0.8, zorder=4, 
                   edgecolors='darkred', linewidths=0.5,
                   label=f"High density areas (n={np.sum(high_density_mask)})")
        
        # 컬러바 추가
        sm = plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize(vmin=0, vmax=1))
        sm.set_array([])
        cb = plt.colorbar(sm, ax=plt.gca())
        cb.set_label('Normalized Density', fontsize=11)
    
    # Volcano curve 그리기 (투명도 효과)
    plt.plot(x_curve, y_curve, label="Volcano curve", color="navy", 
             linewidth=2.5, zorder=10, alpha=0.9)
    
    # 0 eV 지점에 수직선 표시
    plt.axvline(0, color="red", linestyle="--", linewidth=2, alpha=0.9, 
                label="Optimal binding (0 eV)", zorder=10)
    
    # 그래프 설정
    plt.xlabel("Adsorption Energy (eV)", fontsize=12)
    plt.ylabel("Relative Activity (arbitrary)", fontsize=12)
    plt.title(f"Density-based Adsorption Energy Distribution\n(system_info_with_adsorp.csv, n={len(df)})", 
              fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # 파일 저장
    alpha_path = save_path.parent / (save_path.stem + "_alpha_overlay.png")
    plt.savefig(alpha_path, dpi=150, bbox_inches='tight')
    print(f"[투명도 히트맵 저장] {alpha_path}")


def main():
    """메인 실행 함수"""
    try:
        # 데이터 로드
        df = load_adsorp_data(DATA_FILE)
        
        # 밀도 기반 크기 조정 Volcano plot 생성
        create_volcano_plot(df, OUTPUT_PNG)
        
        # 투명도 오버레이 Volcano plot 생성  
        create_alpha_overlay_plot(df, OUTPUT_PNG)
        
        # 히스토그램 생성
        create_histogram(df, OUTPUT_PNG)
        
        print("\n[완료] 모든 시각화가 완료되었습니다.")
        print("생성된 파일:")
        print("- results/adsorp_energy_volcano.png (밀도 기반 크기 조정)")
        print("- results/adsorp_energy_volcano_alpha_overlay.png (투명도 오버레이)")
        print("- results/adsorp_energy_volcano_histogram.png (분포 히스토그램)")
        
    except Exception as e:
        print(f"[오류] {e}")


if __name__ == "__main__":
    main() 