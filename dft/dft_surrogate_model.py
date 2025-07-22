import csv
import ast

def get_adsorp_energy_by_composition(
    composition_dict,
    comp_csv_path="data/hydrogen/system_compositions_fraction.csv",
    info_csv_path="data/hydrogen/system_info_with_adsorp.csv"
):
    """
    composition_dict (예: {'Pt': 0.5, 'Ru': 0.5})와 일치하는 system_id를 system_compositions_fraction.csv에서 찾고,
    system_info_with_adsorp.csv에서 해당 system_id의 adsorption energy를 반환합니다.
    (소수점 오차로 인해 완벽히 일치하지 않을 수 있으므로, tolerance를 둘 수 있음)
    """
    tolerance = 1e-6
    # 1. system_compositions_fraction.csv에서 composition_dict와 일치하는 system_id 찾기
    with open(comp_csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                comp = ast.literal_eval(row["composition_fraction"])
                # 키셋이 동일하고, 각 값이 tolerance 이내로 모두 일치하면 매칭
                if set(comp.keys()) == set(composition_dict.keys()):
                    if all(abs(comp[k] - composition_dict[k]) < tolerance for k in comp):
                        system_id = row["system_id"]
                        break
            except Exception:
                continue
        else:
            return None  # 일치하는 system_id 없음
    # 2. system_info_with_adsorp.csv에서 해당 system_id의 adsorption energy 찾기
    with open(info_csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["system_id"] == system_id:
                return float(row["adsorp_energy"])
    return None

# 사용 예시
if __name__ == "__main__":
    comp = {'Sc': 0.25, 'Pt': 0.75}
    energy = get_adsorp_energy_by_composition(comp)
    print("adsorption energy:", energy)