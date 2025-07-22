#!/usr/bin/env python3
"""eval_results.py

results/results_predicted.json 파일을 불러와 adsorp_energy 값을 바탕으로
모델의 예측 결과를 시각화합니다.

- 입력 파일 형식: {"step_{composition}": adsorp_energy, ...}
- 출력: results/predicted_energy.png (bar chart)
"""

import json
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

RESULT_FILE = Path("results/results_predicted.json")
OUTPUT_PNG = Path("results/predicted_energy.png")


def load_results(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"{path} 가 존재하지 않습니다.")
    data = json.loads(path.read_text(encoding="utf-8"))
    # key 예시: "1_{'Ti': 0.5, 'Ga': 0.5}"
    records = []
    for key, energy in data.items():
        try:
            step_part, comp_part = key.split("_", 1)
            step = int(step_part)
        except ValueError:
            step = None
            comp_part = key
        records.append({"step": step, "composition": comp_part, "adsorp_energy": energy})
    df = pd.DataFrame(records)
    return df


def visualize(df: pd.DataFrame, save_path: Path):
    import numpy as np
    # Volcano curve: peak at 0 eV, decrease linearly with |E|
    x_vals = df["adsorp_energy"].values
    x_min, x_max = x_vals.min() - 0.2, x_vals.max() + 0.2
    x_curve = np.linspace(x_min, x_max, 400)
    c = max(abs(x_min), abs(x_max)) + 0.5  # height parameter
    y_curve = c - np.abs(x_curve)  # simple volcano

    plt.figure(figsize=(8, 6))
    plt.plot(x_curve, y_curve, label="Volcano curve", color="gray")

    # Compute activity for points (for visualization, same function)
    activities = c - np.abs(x_vals)
    plt.scatter(x_vals, activities, color="blue", zorder=5)

    # Annotate each point with composition (shortened)
    for x, y, comp in zip(x_vals, activities, df["composition"]):
        plt.text(x, y, comp, fontsize=7, ha='center', va='bottom')

    plt.axvline(0, color="red", linestyle="--", linewidth=1)
    plt.xlabel("Adsorption Energy (eV)")
    plt.ylabel("Relative Activity (arbitrary)")
    plt.title("Volcano Plot of Predicted Adsorption Energy")
    plt.legend()
    plt.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path, dpi=150)
    print(f"[시각화 완료] {save_path} 저장")


def main():
    df = load_results(RESULT_FILE)
    visualize(df, OUTPUT_PNG)


if __name__ == "__main__":
    main()
