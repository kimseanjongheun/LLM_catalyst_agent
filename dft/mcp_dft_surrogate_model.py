# server_adsorp_api.py

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional
import csv
import ast

app = FastAPI()

# 입력 형식 정의
class CompositionRequest(BaseModel):
    composition: Dict[str, float]

# 기존 함수
def get_adsorp_energy_by_composition(
    composition_dict,
    comp_csv_path=r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_compositions_fraction.csv",
    info_csv_path=r"C:\Users\spark\Desktop\LLM_Catalyst_Agent\data\hydrogen\system_info_with_adsorp.csv"
) -> Optional[float]:
    tolerance = 1e-6
    with open(comp_csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                comp = ast.literal_eval(row["composition_fraction"])
                if set(comp.keys()) == set(composition_dict.keys()):
                    if all(abs(comp[k] - composition_dict[k]) < tolerance for k in comp):
                        system_id = row["system_id"]
                        break
            except Exception:
                continue
        else:
            return None
    with open(info_csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["system_id"] == system_id:
                return float(row["adsorp_energy"])
    return None

# 엔드포인트
@app.post("/get_adsorp_energy")
def get_energy(request: CompositionRequest):
    energy = get_adsorp_energy_by_composition(request.composition)
    if energy is None:
        return {"status": "error", "message": "No matching system found."}
    return {"status": "ok", "adsorp_energy": energy}
