#!/usr/bin/env python3
"""Report time-weighted errors from associated samples, not raw sensor data."""

import argparse
import csv
import json
import math
from pathlib import Path


def finite_number(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def evaluate(samples, metadata):
    """Weight held samples by valid duration; cap holds to expose data gaps."""
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    for name in ("run_id", "measurement_source", "data_kind"):
        if not isinstance(metadata.get(name), str) or not metadata[name].strip():
            raise ValueError(f"{name} must be a nonempty string")
    if metadata["data_kind"] not in ("synthetic", "measured", "simulation"):
        raise ValueError("data_kind must be synthetic, measured or simulation")
    start = finite_number(metadata.get("start_time_s"), "start_time_s")
    end = finite_number(metadata.get("end_time_s"), "end_time_s")
    tolerance = finite_number(metadata.get("tolerance_m"), "tolerance_m")
    max_hold = finite_number(metadata.get("max_sample_hold_s"), "max_sample_hold_s")
    if end <= start or tolerance < 0 or max_hold <= 0:
        raise ValueError("require end > start, tolerance >= 0 and max_sample_hold > 0")
    if type(metadata.get("completed")) is not bool:
        raise ValueError("completed must be a JSON boolean")
    branches = metadata.get("wrong_branch_events")
    if type(branches) is not int or branches < 0:
        raise ValueError("wrong_branch_events must be a nonnegative integer")

    parsed = []
    previous = None
    for index, row in enumerate(samples):
        time = finite_number(row.get("time_s"), f"sample {index} time_s")
        if not start <= time <= end:
            raise ValueError(f"sample {index} timestamp is outside the run interval")
        if previous is not None and time <= previous:
            raise ValueError("sample timestamps must be strictly increasing")
        valid = row.get("valid")
        if valid not in ("0", "1"):
            raise ValueError("valid must be the CSV token 0 or 1")
        error = finite_number(row.get("error_m"), f"sample {index} error_m") if valid == "1" else None
        parsed.append((time, error))
        previous = time

    weighted = []
    for index, (time, error) in enumerate(parsed):
        next_time = parsed[index + 1][0] if index + 1 < len(parsed) else end
        duration = min(next_time - time, max_hold, end - time)
        if error is not None and duration > 0:
            weighted.append((abs(error), duration))

    elapsed = end - start
    valid_duration = sum(duration for _, duration in weighted)
    p95 = None
    if valid_duration:
        cumulative = 0.0
        for error, duration in sorted(weighted):
            cumulative += duration
            if cumulative >= 0.95 * valid_duration:
                p95 = error
                break
    complete = metadata["completed"] and branches == 0
    return {
        "run_id": metadata["run_id"],
        "data_kind": metadata["data_kind"],
        "measurement_source": metadata["measurement_source"],
        "sample_count": len(parsed),
        "elapsed_time_s": elapsed,
        "completion_time_s": elapsed if complete else None,
        "completion_claim_valid": complete,
        "wrong_branch_events": branches,
        "valid_duration_s": valid_duration,
        "invalid_or_uncovered_duration_s": max(0.0, elapsed - valid_duration),
        "valid_time_coverage": min(1.0, valid_duration / elapsed),
        "rms_error_m": math.sqrt(sum(error * error * duration for error, duration in weighted) / valid_duration) if valid_duration else None,
        "mean_abs_error_m": sum(error * duration for error, duration in weighted) / valid_duration if valid_duration else None,
        "p95_abs_error_m": p95,
        "max_abs_error_m": max((error for error, _ in weighted), default=None),
        "time_above_tolerance_s": sum(duration for error, duration in weighted if error > tolerance),
        "tolerance_m": tolerance,
        "note": "Completion is supplied by the manifest; route order and ground truth are not independently verified by this tool.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("samples", type=Path)
    parser.add_argument("--metadata", required=True, type=Path)
    args = parser.parse_args()
    try:
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        with args.samples.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            required = {"time_s", "error_m", "valid"}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("CSV requires time_s,error_m,valid columns")
            result = evaluate(list(reader), metadata)
    except (OSError, ValueError, csv.Error) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
