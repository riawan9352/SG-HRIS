import math

SERVICE_UNIT_STANDARD_RATIO: dict[tuple[str, str, str], int] = {
    ("nurse", "igd", "er"): 6,
    ("nurse", "icu", "icu"): 2,
    ("nurse", "rawat_inap", "general_ward"): 8,
    ("nurse", "ok", "operating_room"): 3,
    ("medic", "igd", "er"): 10,
    ("medic", "icu", "icu"): 4,
    ("medic", "rawat_jalan", "outpatient"): 18,
    ("non_medic", "farmasi", "pharmacy"): 20,
    ("support", "penunjang", "laboratory"): 22,
}


def calculate_recommended_staff(
    model_type: str,
    workforce_category: str,
    service_type: str,
    unit_type: str,
    service_volume: int,
    total_workload_hours: int,
    available_working_hours_per_staff: int,
    allowance_factor_percent: int,
) -> int:
    if available_working_hours_per_staff <= 0:
        raise ValueError("available_working_hours_per_staff must be greater than zero")

    allowance_multiplier = allowance_factor_percent / 100.0
    if allowance_multiplier <= 0:
        raise ValueError("allowance_factor_percent must be greater than zero")

    if model_type == "hours_based":
        base_staff = total_workload_hours / available_working_hours_per_staff
    elif model_type == "ratio_based":
        ratio = SERVICE_UNIT_STANDARD_RATIO.get(
            (workforce_category, service_type, unit_type),
            25,
        )
        base_staff = service_volume / ratio
    elif model_type == "wisn_simplified":
        # Simplified WISN-like approach using service + workload blend.
        base_staff = (
            (total_workload_hours / available_working_hours_per_staff) * 0.7
            + (service_volume / SERVICE_UNIT_STANDARD_RATIO.get((workforce_category, service_type, unit_type), 30)) * 0.3
        )
    else:
        raise ValueError("Unsupported model_type")

    return max(1, math.ceil(base_staff * allowance_multiplier))


def calculate_financial_pressure_index(
    ebitda_margin_percent: int | None,
    cashflow_coverage_months: int | None,
) -> int | None:
    if ebitda_margin_percent is None and cashflow_coverage_months is None:
        return None
    score = 0
    if ebitda_margin_percent is not None:
        if ebitda_margin_percent < 8:
            score += 60
        elif ebitda_margin_percent < 15:
            score += 35
        else:
            score += 10
    if cashflow_coverage_months is not None:
        if cashflow_coverage_months < 2:
            score += 40
        elif cashflow_coverage_months < 4:
            score += 20
        else:
            score += 5
    return min(100, score)


def calculate_optimum_staff_count(
    recommended_staff_count: int,
    min_regulatory_staffing: int | None,
    financial_pressure_index: int | None,
) -> int:
    if financial_pressure_index is None:
        return recommended_staff_count
    reduction_factor = 1.0
    if financial_pressure_index >= 80:
        reduction_factor = 0.9
    elif financial_pressure_index >= 60:
        reduction_factor = 0.94
    elif financial_pressure_index >= 40:
        reduction_factor = 0.97
    adjusted = max(1, math.ceil(recommended_staff_count * reduction_factor))
    if min_regulatory_staffing is not None:
        adjusted = max(adjusted, min_regulatory_staffing)
    return adjusted
