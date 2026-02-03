import json
import os
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping


class InferenceError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


def _ensure_dirs(*dirs: Path) -> None:
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)


def _sanitize_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    # Keep compatibility with historical payload key variants.
    payload_text = json.dumps(payload)
    payload_text = payload_text.replace('"5\\"Flank"', '"5pFlank"')
    return json.loads(payload_text)


def _run_command(command: list[str], cwd: Path, error_message: str) -> None:
    try:
        env = dict(os.environ)
        env.setdefault("MPLCONFIGDIR", str(cwd / "runtime" / ".matplotlib"))
        Path(env["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
        subprocess.run(command, check=True, cwd=str(cwd), capture_output=True, text=True, env=env)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() or exc.stdout.strip() or "subprocess failed"
        raise InferenceError(f"{error_message}: {detail}", status_code=500) from exc


def run_inference(
    version: str,
    payload: Mapping[str, Any] | None,
    features_file: Any,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    del version  # kept for API compatibility

    features_dir = Path(config["FEATURES_DIR"])
    predictions_dir = Path(config["PREDICTIONS_DIR"])
    classifier_script = Path(config["CLASSIFIER_SCRIPT"])
    parse_script = Path(config["PARSE_SCRIPT"])
    output_script = Path(config["OUTPUT_SCRIPT"])
    base_dir = Path(config["BASE_DIR"])

    _ensure_dirs(features_dir, predictions_dir)

    token = f"{_timestamp()}_{uuid.uuid4().hex[:8]}"
    feature_json = features_dir / f"features_{token}.json"
    feature_csv = features_dir / f"features_{token}.csv"
    feature_single_csv = features_dir / f"features_{token}_single_data.csv"
    prediction_csv = predictions_dir / f"predictions_{token}.csv"
    prediction_json = predictions_dir / f"predictions_{token}.json"

    if features_file is not None and getattr(features_file, "filename", ""):
        features_file.save(str(feature_csv))
    elif payload is not None:
        cleaned_payload = _sanitize_payload(payload)
        with feature_json.open("w", encoding="utf-8") as stream:
            json.dump(cleaned_payload, stream, indent=2)

        _run_command(
            [sys.executable, str(parse_script), str(feature_json), str(feature_csv)],
            cwd=base_dir,
            error_message="failed to parse JSON input into model features",
        )
    else:
        raise InferenceError("no input provided; send JSON body or upload a features file", status_code=400)

    _run_command(
        [
            sys.executable,
            str(classifier_script),
            str(feature_csv),
            str(feature_single_csv),
            str(prediction_csv),
        ],
        cwd=base_dir,
        error_message="failed to run classifier",
    )

    _run_command(
        [sys.executable, str(output_script), str(prediction_csv), str(prediction_json)],
        cwd=base_dir,
        error_message="failed to format classifier output",
    )

    with prediction_json.open("r", encoding="utf-8") as stream:
        return json.load(stream)
