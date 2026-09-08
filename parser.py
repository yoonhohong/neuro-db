"""
ALS 연구 텍스트 템플릿 파서.

입력 규칙:
- 단일 선택(Sex, Dx, Y/N): 해당 항목만 남기고 나머지 삭제
- BCTL: 해당하는 문자만 남김 (예: "BL" = Bulbar + Lumbar)
- 날짜: YYYY-MM (이벤트) 또는 YYYY-MM-DD (검사/시료)
- 시계열: "값 (YYYY-MM) > 값 (YYYY-MM)" 패턴
- Progression: 자유 기술 텍스트 (여러 줄 가능)
"""

import re


TEMPLATE = """\
Patient_name:
Hosp_ID:

Remarks: dx at entry (within 1 mo) / referred from [병원명], dx established before entry / dx at this institution after [N]mo follow-up 

Sex : M   F
Age (at Dx) :

Dx : ALS   PLS   BSMA   HSP   Others
Dx_others (specify) :
Date_onset : YYYY-MM
Date_entry : YYYY-MM
Date_Dx : YYYY-MM

Onset_region : BCTL
LMN (clinical at entry): BCTL   None
UMN (clinical at entry): BCTL   None
EMG (at entry): BCTL   None   NotChecked
Pseudobulbar affect (at entry): Y   N   Indeterminate
Dementia (at entry): Y   N   Indeterminate

Riluzole: YYYY-MM (start)   YYYY-MM (end)
Edaravone: YYYY-MM (start)   YYYY-MM (end)

Progression_onset2dx:
Progression_afterdx:

Bwt (kg) : (premorbid) > ...(YYYY-MM) > ...
Ht (cm) :
FVC (%) : ...(YYYY-MM) > ...
ALSFRS-R : ...(YYYY-MM) > ...
Gastrostomy : YYYY-MM
NIV : YYYY-MM
Tracheostomy : YYYY-MM
Death : YYYY-MM

Brain MRI : YYYY-MM-DD
Spine MRI : YYYY-MM-DD
Genetic test : YYYY-MM-DD
Cognitive test : YYYY-MM-DD
Chest CT : YYYY-MM-DD
Abdomen CT : YYYY-MM-DD

Buffy coat : YYYY-MM-DD
Plasma : YYYY-MM-DD
Serum : YYYY-MM-DD
CSF : YYYY-MM-DD
"""


def _line(text: str, key_pattern: str) -> str | None:
    """key_pattern 으로 시작하는 줄의 콜론 이후 값을 반환."""
    m = re.search(rf"^{key_pattern}[ \t]*:[ \t]*(.*)$", text, re.MULTILINE | re.IGNORECASE)
    return m.group(1).strip() if m else None


def _parse_bctl(value: str | None) -> dict:
    if not value:
        return {"b": 0, "c": 0, "t": 0, "l": 0, "none": 0}
    v = value.upper()
    return {
        "b": 1 if "B" in v else 0,
        "c": 1 if "C" in v else 0,
        "t": 1 if "T" in v else 0,
        "l": 1 if "L" in v else 0,
        "none": 1 if "NONE" in v else 0,
    }


BCTL_B_ALIASES = {"b", "bulbar"}
BCTL_C_ALIASES = {"c", "cervical"}
BCTL_T_ALIASES = {"t", "thoracic", "respiratory"}
BCTL_L_ALIASES = {"l", "lumbosacral", "lumbar"}

NONE_ALIASES = {"none", "no"}
NOT_CHECKED_ALIASES = {"not checked", "notchecked", "nc"}

YES_ALIASES = {"yes", "y", "present"}
NO_ALIASES = {"no", "n", "absent"}
INDETERMINATE_ALIASES = {"indeterminate", "unknown", "uk", "not determined"}


def _parse_onset_region(value: str | None) -> dict:
    """B/C/T/L 문자 조합(예: 'BL') 또는 Bulbar/Cervical/Thoracic/Respiratory/
    Lumbosacral/Lumbar 등 단어(대소문자 무관)를 모두 인식."""
    flags = {"b": 0, "c": 0, "t": 0, "l": 0}
    if not value:
        return flags
    v = value.strip()

    # 순수 BCTL 문자 조합 (예: "BL", "bctl")
    if re.fullmatch(r"[BCTLbctl]+", v):
        upper = v.upper()
        flags["b"] = 1 if "B" in upper else 0
        flags["c"] = 1 if "C" in upper else 0
        flags["t"] = 1 if "T" in upper else 0
        flags["l"] = 1 if "L" in upper else 0
        return flags

    for token in re.split(r"[,\s/;+]+", v):
        t = token.strip().lower()
        if t in BCTL_B_ALIASES:
            flags["b"] = 1
        elif t in BCTL_C_ALIASES:
            flags["c"] = 1
        elif t in BCTL_T_ALIASES:
            flags["t"] = 1
        elif t in BCTL_L_ALIASES:
            flags["l"] = 1
    return flags


def _parse_clinical_bctl(value: str | None, allow_not_checked: bool = False) -> dict:
    """LMN/UMN/EMG 공용: BCTL 문자·단어 별칭에 더해 None 상태 별칭까지 인식한다
    (대소문자 무관).
    - None: None, none, no, No
    - Not checked(EMG만): Not checked, not checked, NC, nc
    """
    flags = {"b": 0, "c": 0, "t": 0, "l": 0, "none": 0}
    if allow_not_checked:
        flags["not_checked"] = 0
    if not value:
        return flags
    v = value.strip()
    v_norm = re.sub(r"\s+", " ", v.lower())

    if v_norm in NONE_ALIASES:
        flags["none"] = 1
        return flags
    if allow_not_checked and v_norm in NOT_CHECKED_ALIASES:
        flags["not_checked"] = 1
        return flags

    # 순수 BCTL 문자 조합 (예: "BL", "bctl")
    if re.fullmatch(r"[BCTLbctl]+", v):
        upper = v.upper()
        flags["b"] = 1 if "B" in upper else 0
        flags["c"] = 1 if "C" in upper else 0
        flags["t"] = 1 if "T" in upper else 0
        flags["l"] = 1 if "L" in upper else 0
        return flags

    for token in re.split(r"[,\s/;+]+", v):
        t = token.strip().lower()
        if t in BCTL_B_ALIASES:
            flags["b"] = 1
        elif t in BCTL_C_ALIASES:
            flags["c"] = 1
        elif t in BCTL_T_ALIASES:
            flags["t"] = 1
        elif t in BCTL_L_ALIASES:
            flags["l"] = 1
    return flags


def _parse_timeseries_float(line: str | None) -> list[dict]:
    """값 (YYYY-MM) 패턴을 모두 추출. 값 뒤에 kg/%같은 단위가 붙어도 무시한다."""
    if not line:
        return []
    return [
        {"value": float(m.group(1)), "date": m.group(2)}
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*[a-zA-Z%]*\s*\((\d{4}-\d{2})\)", line)
    ]


def _parse_date_field(line: str | None, fmt: str = "YYYY-MM") -> str:
    """날짜 형식에 맞는 값만 반환. 없으면 빈 문자열."""
    if not line:
        return ""
    if fmt == "YYYY-MM":
        m = re.search(r"\d{4}-\d{2}", line)
    else:  # YYYY-MM-DD
        m = re.search(r"\d{4}-\d{2}-\d{2}", line)
    return m.group(0) if m else ""


def _parse_multiline_field(text: str, key_pattern: str) -> str:
    """
    키 이후부터 다음 키(대문자로 시작하는 줄) 또는 빈 줄 전까지를 자유 텍스트로 반환.
    """
    m = re.search(
        rf"^{key_pattern}\s*:(.*?)(?=\n[A-Z]|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if not m:
        return ""
    return m.group(1).strip()


def parse_template(text: str) -> dict:
    result: dict = {}

    # --- 기본 정보 ---
    result["patient_name"] = _line(text, r"Patient_name") or ""
    result["hosp_id"] = _line(text, r"Hosp_ID") or ""
    result["remarks"] = _line(text, r"Remarks") or ""

    sex_val = _line(text, r"Sex")
    MALE_ALIASES = {"male", "m", "남자", "남", "남성"}
    FEMALE_ALIASES = {"female", "f", "여자", "여", "여성"}
    if sex_val and sex_val.strip().lower() in MALE_ALIASES:
        result["sex"] = "M"
    elif sex_val and sex_val.strip().lower() in FEMALE_ALIASES:
        result["sex"] = "F"
    else:
        result["sex"] = "M" if sex_val and re.search(r"\bM\b", sex_val) and not re.search(r"\bF\b", sex_val) else (
            "F" if sex_val and re.search(r"\bF\b", sex_val) and not re.search(r"\bM\b", sex_val) else (
                sex_val.strip() if sex_val else ""
            )
        )

    age_val = _line(text, r"Age\s*\(at\s*Dx\)")
    result["age_at_dx"] = int(age_val) if age_val and age_val.isdigit() else None

    # --- 진단 ---
    dx_val = _line(text, r"Dx")
    result["dx"] = dx_val.strip() if dx_val else ""
    result["dx_others"] = _line(text, r"Dx_others\s*\(specify\)") or ""

    result["date_onset"] = _parse_date_field(_line(text, r"Date_onset"))
    result["date_dx"] = _parse_date_field(_line(text, r"Date_Dx"))
    result["date_entry"] = _parse_date_field(_line(text, r"Date_entry"))

    # --- 임상 소견 ---
    onset = _parse_onset_region(_line(text, r"Onset_region"))
    result["onset_b"] = onset["b"]
    result["onset_c"] = onset["c"]
    result["onset_t"] = onset["t"]
    result["onset_l"] = onset["l"]

    lmn = _parse_clinical_bctl(_line(text, r"LMN\s*\(clinical at entry\)"))
    result["lmn_b"] = lmn["b"]
    result["lmn_c"] = lmn["c"]
    result["lmn_t"] = lmn["t"]
    result["lmn_l"] = lmn["l"]
    result["lmn_none"] = lmn["none"]

    umn = _parse_clinical_bctl(_line(text, r"UMN\s*\(clinical at entry\)"))
    result["umn_b"] = umn["b"]
    result["umn_c"] = umn["c"]
    result["umn_t"] = umn["t"]
    result["umn_l"] = umn["l"]
    result["umn_none"] = umn["none"]

    emg_val = _line(text, r"EMG\s*\(at entry\)")
    emg = _parse_clinical_bctl(emg_val, allow_not_checked=True)
    result["emg_b"] = emg["b"]
    result["emg_c"] = emg["c"]
    result["emg_t"] = emg["t"]
    result["emg_l"] = emg["l"]
    result["emg_none"] = emg["none"]
    result["emg_not_checked"] = emg["not_checked"]

    for field, pattern in [
        ("pseudobulbar_affect", r"Pseudobulbar affect\s*\(at entry\)"),
        ("dementia", r"Dementia\s*\(at entry\)"),
    ]:
        val = _line(text, pattern)
        v_norm = re.sub(r"\s+", " ", val.strip().lower()) if val else ""
        if v_norm in YES_ALIASES:
            result[field] = "Y"
        elif v_norm in NO_ALIASES:
            result[field] = "N"
        elif v_norm in INDETERMINATE_ALIASES:
            result[field] = "Indeterminate"
        else:
            result[field] = ""

    # --- 약물 ---
    for drug, pattern in [("riluzole", r"Riluzole"), ("edaravone", r"Edaravone")]:
        val = _line(text, pattern)
        if val:
            dates = re.findall(r"\d{4}-\d{2}", val)
            result[f"{drug}_start"] = dates[0] if len(dates) >= 1 else ""
            result[f"{drug}_end"] = dates[1] if len(dates) >= 2 else ""
        else:
            result[f"{drug}_start"] = ""
            result[f"{drug}_end"] = ""

    # --- Progression (여러 줄 자유 기술) ---
    result["progression_onset2dx"] = _parse_multiline_field(text, r"Progression_onset2dx")
    result["progression_afterdx"] = _parse_multiline_field(text, r"Progression_afterdx")

    # --- 체중 시계열 ---
    bwt_line = _line(text, r"Bwt\s*\(kg\)")
    body_weight = []
    if bwt_line:
        pm = re.search(r"(\d+(?:\.\d+)?)\s*[a-zA-Z%]*\s*\(premorbid\)", bwt_line, re.IGNORECASE)
        if pm:
            body_weight.append({"weight_kg": float(pm.group(1)), "date": None, "is_premorbid": 1})
        for entry in _parse_timeseries_float(bwt_line):
            body_weight.append({"weight_kg": entry["value"], "date": entry["date"], "is_premorbid": 0})
    result["body_weight"] = body_weight

    result["height_cm"] = None
    ht_val = _line(text, r"Ht\s*\(cm\)")
    if ht_val:
        m = re.search(r"\d+(?:\.\d+)?", ht_val)
        if m:
            result["height_cm"] = float(m.group(0))

    # --- FVC 시계열 ---
    fvc_line = _line(text, r"FVC\s*\(%\)")
    result["fvc_records"] = [
        {"fvc_percent": e["value"], "date": e["date"]}
        for e in _parse_timeseries_float(fvc_line)
    ]

    # --- ALSFRS-R 시계열 ---
    alsfrs_line = _line(text, r"ALSFRS-R")
    result["alsfrs_records"] = [
        {"score": int(e["value"]), "date": e["date"]}
        for e in _parse_timeseries_float(alsfrs_line)
    ]

    # --- 이벤트 날짜 ---
    for field, pattern in [
        ("gastrostomy_date", r"Gastrostomy"),
        ("niv_date", r"NIV"),
        ("tracheostomy_date", r"Tracheostomy"),
        ("death_date", r"Death"),
    ]:
        result[field] = _parse_date_field(_line(text, pattern))

    # --- 검사 / 시료 (YYYY-MM-DD) ---
    for field, pattern in [
        ("brain_mri", r"Brain MRI"),
        ("spine_mri", r"Spine MRI"),
        ("genetic_test", r"Genetic test"),
        ("cognitive_test", r"Cognitive test"),
        ("chest_ct", r"Chest CT"),
        ("abdomen_ct", r"Abdomen CT"),
        ("buffy_coat", r"Buffy coat"),
        ("plasma", r"Plasma"),
        ("serum", r"Serum"),
        ("csf", r"CSF"),
    ]:
        result[field] = _parse_date_field(_line(text, pattern), fmt="YYYY-MM-DD")

    return result


def _bctl_str(b, c, t, l, none=0, not_checked=0) -> str:
    parts = []
    if b:
        parts.append("B")
    if c:
        parts.append("C")
    if t:
        parts.append("T")
    if l:
        parts.append("L")
    if none:
        parts.append("None")
    if not_checked:
        parts.append("NotChecked")
    return "".join(parts) if parts else ""


def format_patient_as_template(p: dict) -> str:
    """DB에서 불러온 환자 dict를 편집 가능한 템플릿 텍스트로 변환."""

    def v(key, default=""):
        val = p.get(key)
        return val if val is not None and val != "" else default

    def date_or(key):
        return v(key, "YYYY-MM")

    def dated_or(key):
        return v(key, "YYYY-MM-DD")

    # 시계열 → 텍스트
    bwts = p.get("body_weight", [])
    bwt_parts = []
    for bw in bwts:
        if bw.get("is_premorbid"):
            bwt_parts.append(f"{bw['weight_kg']} (premorbid)")
        elif bw.get("date"):
            bwt_parts.append(f"{bw['weight_kg']} ({bw['date']})")
    bwt_str = " > ".join(bwt_parts) if bwt_parts else "(premorbid) > ...(YYYY-MM) > ..."

    fvcs = p.get("fvc_records", [])
    fvc_str = " > ".join(f"{f['fvc_percent']} ({f['date']})" for f in fvcs) if fvcs else "...(YYYY-MM) > ..."

    alsfrs = p.get("alsfrs_records", [])
    alsfrs_str = " > ".join(f"{a['score']} ({a['date']})" for a in alsfrs) if alsfrs else "...(YYYY-MM) > ..."

    # 약물
    ril = ""
    if v("riluzole_start"):
        ril = f"{v('riluzole_start')} (start)"
        if v("riluzole_end"):
            ril += f"   {v('riluzole_end')} (end)"
    else:
        ril = "YYYY-MM (start)   YYYY-MM (end)"

    eda = ""
    if v("edaravone_start"):
        eda = f"{v('edaravone_start')} (start)"
        if v("edaravone_end"):
            eda += f"   {v('edaravone_end')} (end)"
    else:
        eda = "YYYY-MM (start)   YYYY-MM (end)"

    onset_s = _bctl_str(p.get("onset_b"), p.get("onset_c"), p.get("onset_t"), p.get("onset_l")) or "BCTL"
    lmn_s = _bctl_str(
        p.get("lmn_b"), p.get("lmn_c"), p.get("lmn_t"), p.get("lmn_l"), p.get("lmn_none"),
    ) or "BCTL   None"
    umn_s = _bctl_str(
        p.get("umn_b"), p.get("umn_c"), p.get("umn_t"), p.get("umn_l"), p.get("umn_none"),
    ) or "BCTL   None"
    emg_s = _bctl_str(
        p.get("emg_b"), p.get("emg_c"), p.get("emg_t"), p.get("emg_l"),
        p.get("emg_none"), p.get("emg_not_checked"),
    ) or "BCTL   None   NotChecked"

    pba = v("pseudobulbar_affect") or "Y   N   Indeterminate"
    dem = v("dementia") or "Y   N   Indeterminate"

    lines = [
        f"Patient_name: {v('patient_name')}",
        f"Hosp_ID: {v('hosp_id')}",
        "",
        f"Remarks: {v('remarks')}",
        "",
        f"Sex : {v('sex', 'M   F')}",
        f"Age (at Dx) : {v('age_at_dx', '')}",
        "",
        f"Dx : {v('dx', 'ALS   PLS   BSMA   HSP   Others')}",
        f"Dx_others (specify) : {v('dx_others')}",
        f"Date_onset : {date_or('date_onset')}",
        f"Date_entry : {date_or('date_entry')}",
        f"Date_Dx : {date_or('date_dx')}",
        "",
        f"Onset_region : {onset_s}",
        f"LMN (clinical at entry): {lmn_s}",
        f"UMN (clinical at entry): {umn_s}",
        f"EMG (at entry): {emg_s}",
        f"Pseudobulbar affect (at entry): {pba}",
        f"Dementia (at entry): {dem}",
        "",
        f"Riluzole: {ril}",
        f"Edaravone: {eda}",
        "",
        f"Progression_onset2dx: {v('progression_onset2dx')}",
        f"Progression_afterdx: {v('progression_afterdx')}",
        "",
        f"Bwt (kg) : {bwt_str}",
        f"Ht (cm) : {v('height_cm', '')}",
        f"FVC (%) : {fvc_str}",
        f"ALSFRS-R : {alsfrs_str}",
        f"Gastrostomy : {date_or('gastrostomy_date')}",
        f"NIV : {date_or('niv_date')}",
        f"Tracheostomy : {date_or('tracheostomy_date')}",
        f"Death : {date_or('death_date')}",
        "",
        f"Brain MRI : {dated_or('brain_mri')}",
        f"Spine MRI : {dated_or('spine_mri')}",
        f"Genetic test : {dated_or('genetic_test')}",
        f"Cognitive test : {dated_or('cognitive_test')}",
        f"Chest CT : {dated_or('chest_ct')}",
        f"Abdomen CT : {dated_or('abdomen_ct')}",
        "",
        f"Buffy coat : {dated_or('buffy_coat')}",
        f"Plasma : {dated_or('plasma')}",
        f"Serum : {dated_or('serum')}",
        f"CSF : {dated_or('csf')}",
    ]
    return "\n".join(lines)
