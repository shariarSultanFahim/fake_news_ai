"""
backend/scripts/score_via_api.py:
Batch evaluation script that reads a test CSV, queries a live or test /predict API,
and computes evaluation metrics:
- Real recall, Fake recall
- ROC AUC score
- Bootstrap 95% confidence intervals
- Counts of 'too_short' and 'not_bangla'
Writes a CSV of individual row predictions and outputs a performance summary.
"""

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
import requests
from sklearn.metrics import roc_auc_score, recall_score, confusion_matrix


def parse_arguments():
    parser = argparse.ArgumentParser(description="Score a dataset via the /predict API.")
    parser.add_argument(
        "--input-csv",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "tests" / "golden.csv"),
        help="Path to input CSV (columns: headline, content, label or p_fake)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://127.0.0.1:8000/predict",
        help="URL of the /predict endpoint"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="",
        help="Optional API Key for X-API-Key header"
    )
    parser.add_argument(
        "--output-csv",
        type=str,
        default=str(Path(__file__).resolve().parent.parent / "tests" / "evaluation_results.csv"),
        help="Path to output CSV of predictions"
    )
    parser.add_argument(
        "--n-bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap iterations for 95% confidence intervals"
    )
    return parser.parse_args()


def bootstrap_ci(
    y_true: np.ndarray,
    y_pred_probs: np.ndarray,
    threshold: float = 0.40,
    n_bootstrap: int = 1000,
    rng_seed: int = 42
) -> Dict[str, Tuple[float, float, float]]:
    """
    Computes metric values and 95% bootstrap confidence intervals for:
    - fake_recall
    - authentic_recall
    - auc
    """
    rng = np.random.RandomState(rng_seed)
    n = len(y_true)

    # Base metrics
    y_pred_labels = (y_pred_probs >= threshold).astype(int)  # 1 for fake, 0 for authentic

    # Handle single-class cases gracefully
    classes_present = np.unique(y_true)
    has_both_classes = len(classes_present) > 1

    base_auc = roc_auc_score(y_true, y_pred_probs) if has_both_classes else np.nan
    base_fake_rec = recall_score(y_true, y_pred_labels, pos_label=1, zero_division=0)
    base_auth_rec = recall_score(y_true, y_pred_labels, pos_label=0, zero_division=0)

    if not has_both_classes or n < 10:
        return {
            "fake_recall": (base_fake_rec, base_fake_rec, base_fake_rec),
            "authentic_recall": (base_auth_rec, base_auth_rec, base_auth_rec),
            "auc": (base_auc, base_auc, base_auc)
        }

    boot_aucs = []
    boot_fake_recs = []
    boot_auth_recs = []

    for _ in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        sample_true = y_true[idx]
        sample_probs = y_pred_probs[idx]
        sample_preds = (sample_probs >= threshold).astype(int)

        if len(np.unique(sample_true)) > 1:
            boot_aucs.append(roc_auc_score(sample_true, sample_probs))

        boot_fake_recs.append(recall_score(sample_true, sample_preds, pos_label=1, zero_division=0))
        boot_auth_recs.append(recall_score(sample_true, sample_preds, pos_label=0, zero_division=0))

    def ci(arr, base_val):
        if not arr:
            return (base_val, np.nan, np.nan)
        return (base_val, float(np.percentile(arr, 2.5)), float(np.percentile(arr, 97.5)))

    return {
        "fake_recall": ci(boot_fake_recs, base_fake_rec),
        "authentic_recall": ci(boot_auth_recs, base_auth_rec),
        "auc": ci(boot_aucs, base_auc)
    }


def main():
    args = parse_arguments()
    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    if not input_path.exists():
        print(f"Error: input file {input_path} not found.")
        sys.exit(1)

    print(f"Reading input from {input_path}")
    rows = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    print(f"Loaded {len(rows)} samples. Querying API at {args.api_url}...")

    headers = {"Content-Type": "application/json"}
    if args.api_key:
        headers["X-API-Key"] = args.api_key

    results = []
    scored_true_labels = []
    scored_probs = []

    counts = {
        "total": len(rows),
        "scored": 0,
        "not_bangla": 0,
        "too_short": 0,
        "error": 0
    }

    # If golden.csv has no explicit ground truth label, infer from p_fake >= 0.40 or label column
    for i, row in enumerate(rows):
        headline = row.get("headline", "")
        content = row.get("content", "")

        # Extract ground truth label: 1 = fake, 0 = authentic
        ground_truth = None
        if "label" in row:
            raw_label = str(row["label"]).strip().lower()
            ground_truth = 1 if raw_label in ("fake", "1") else 0
        elif "p_fake" in row:
            # When evaluating against golden set without explicit binary label
            prob = float(row["p_fake"])
            ground_truth = 1 if prob >= 0.40 else 0

        payload = {"headline": headline, "content": content}

        try:
            resp = requests.post(args.api_url, json=payload, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                band = data.get("band")
                p_fake = data.get("p_fake")

                if band == "not_bangla":
                    counts["not_bangla"] += 1
                elif band == "too_short":
                    counts["too_short"] += 1
                else:
                    counts["scored"] += 1
                    if ground_truth is not None and p_fake is not None:
                        scored_true_labels.append(ground_truth)
                        scored_probs.append(p_fake)

                results.append({
                    "headline": headline[:60],
                    "ground_truth": ground_truth,
                    "band": band,
                    "p_fake": p_fake,
                    "threshold": data.get("threshold"),
                    "latency_ms": data.get("latency_ms")
                })
            else:
                counts["error"] += 1
                results.append({
                    "headline": headline[:60],
                    "ground_truth": ground_truth,
                    "band": f"error_{resp.status_code}",
                    "p_fake": None,
                    "threshold": None,
                    "latency_ms": None
                })
        except Exception as e:
            counts["error"] += 1
            results.append({
                "headline": headline[:60],
                "ground_truth": ground_truth,
                "band": "error_connection",
                "p_fake": None,
                "threshold": None,
                "latency_ms": None
            })

    # Write output CSV
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["headline", "ground_truth", "band", "p_fake", "threshold", "latency_ms"]
        )
        writer.writeheader()
        writer.writerows(results)

    print(f"\nIndividual results written to {output_path}")

    # Compute metrics and bootstrap CIs
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total Samples: {counts['total']}")
    print(f"Scored Samples: {counts['scored']}")
    print(f"Excluded (not_bangla): {counts['not_bangla']}")
    print(f"Excluded (too_short): {counts['too_short']}")
    print(f"Errors: {counts['error']}")

    if len(scored_probs) > 0 and len(scored_true_labels) > 0:
        y_true = np.array(scored_true_labels)
        y_probs = np.array(scored_probs)

        metrics = bootstrap_ci(
            y_true=y_true,
            y_pred_probs=y_probs,
            threshold=0.40,
            n_bootstrap=args.n_bootstrap
        )

        fake_rec, f_low, f_high = metrics["fake_recall"]
        auth_rec, a_low, a_high = metrics["authentic_recall"]
        auc, auc_low, auc_high = metrics["auc"]

        print("\n--- Metric Performance (Threshold = 0.40) ---")
        print(f"Fake Recall:        {fake_rec:.4f}  [95% CI: {f_low:.4f} - {f_high:.4f}]")
        print(f"Authentic Recall:   {auth_rec:.4f}  [95% CI: {a_low:.4f} - {a_high:.4f}]")
        if not np.isnan(auc):
            print(f"ROC AUC:            {auc:.4f}  [95% CI: {auc_low:.4f} - {auc_high:.4f}]")
        else:
            print("ROC AUC:            N/A (Single class evaluated in sample)")
    else:
        print("No valid scores were returned to compute evaluation metrics.")
    print("=" * 60)


if __name__ == "__main__":
    main()
