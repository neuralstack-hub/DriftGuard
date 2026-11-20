"""CI entry point for DriftGuard training / drift-triggered retraining.

Runs in an ISOLATED workspace (a fresh directory), so it never depends on, or
modifies, the registries committed to the repository (which may point at files
from a developer's machine). The Beijing PM2.5 CSV must already be in data/raw/
(see scripts/download_dataset.py).

Steps:  bootstrap Model v1  ->  (optional) retrain candidate on labelled data
        -> compare with active model on the SAME fixed validation set
        -> promote or reject.  Writes result.json and a GitHub step summary.

Usage:
    python scripts/ci_retrain.py --out-dir ci-output                 # train v1 only
    python scripts/ci_retrain.py --out-dir ci-output --retrain \\
        --reason "github_actions_dispatch"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.monitoring_service import MonitoringService  # noqa: E402
from backend.app.services.pipeline_service import PipelineService  # noqa: E402
from backend.app.services.registry_service import RegistryService  # noqa: E402


def write_summary(lines: list[str]) -> None:
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
    print(text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default="ci-output", help="isolated workspace for models/registry/history")
    ap.add_argument("--retrain", action="store_true", help="after v1, train and evaluate a candidate")
    ap.add_argument("--reason", default="github_actions", help="trigger reason recorded in history")
    ap.add_argument("--simulate-worse-candidate", action="store_true",
                    help="train a deliberately weak candidate to exercise rejection")
    args = ap.parse_args()

    out = Path(args.out_dir).resolve()
    processed, models, monitoring = out / "processed", out / "models", out / "monitoring"
    registry = RegistryService(models)
    monitor = MonitoringService(monitoring, processed)
    pipeline = PipelineService(registry, monitor, processed_dir=processed, models_dir=models)

    boot = pipeline.bootstrap_v1()
    v1 = boot["model"]
    lines = ["## DriftGuard CI run", "", f"- Model **{v1['version']}** ({boot['status']}): "
             f"MAE {v1['metrics']['mae']}, RMSE {v1['metrics']['rmse']}, R² {v1['metrics']['r2']} "
             f"(fixed validation set, {v1['training_samples']} training rows)"]
    result = {"bootstrap": boot}

    if args.retrain:
        outcome = pipeline.trigger_retraining(
            simulate_worse_candidate=args.simulate_worse_candidate, trigger_reason=args.reason
        )
        result["retraining"] = outcome
        cand, act = outcome["candidate_metrics"], outcome["active_metrics_on_fixed_val"]
        lines += [
            "",
            f"### Candidate `{outcome['candidate_version']}` -> **{outcome['decision'].upper()}**",
            "",
            "| Model | MAE | RMSE | R² |",
            "|---|---|---|---|",
            f"| Active `{outcome['previous_active_version']}` | {act['mae']} | {act['rmse']} | {act['r2']} |",
            f"| Candidate `{outcome['candidate_version']}` | {cand['mae']} | {cand['rmse']} | {cand['r2']} |",
            "",
            f"Both models scored on the same fixed validation set. Active model after run: "
            f"`{registry.get_active_version_record()['version']}`.",
        ]

    out.mkdir(parents=True, exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    write_summary(lines)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
