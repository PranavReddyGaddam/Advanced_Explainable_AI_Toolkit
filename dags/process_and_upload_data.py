from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple
import logging
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook


# Paths are inside the Airflow containers per docker-compose volume
DATA_DIR = "/opt/airflow/data"
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# S3 details (ensure the connection exists in Airflow UI)
AWS_CONN_ID = "S3_access"
BUCKET_NAME = "finalprojectxai"


def _ensure_processed_dir() -> None:
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def _safe_get_hotpot_sentence(
    context_titles: List[str],
    context_sentences: List[List[str]],
    title: str,
    sent_id: int,
) -> Optional[Tuple[str, str]]:
    try:
        title_idx = context_titles.index(title)
    except ValueError:
        return None
    if title_idx < 0 or title_idx >= len(context_sentences):
        return None
    sentences_for_title = context_sentences[title_idx]
    if sent_id is None:
        return None
    if sent_id < 0 or sent_id >= len(sentences_for_title):
        return None
    sentence_text = sentences_for_title[sent_id]
    return title, sentence_text


def process_hotpot_jsonl() -> None:
    import pandas as pd
    _ensure_processed_dir()
    input_path = os.path.join(DATA_DIR, "hotpot_train.jsonl")
    output_path = os.path.join(PROCESSED_DIR, "hotpot_train_clean.csv")

    records: List[Dict[str, Any]] = []
    if not os.path.exists(input_path):
        # Graceful no-op if file is absent
        pd.DataFrame(records).to_csv(output_path, index=False)
        return

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            example_id = obj.get("id")
            question = obj.get("question")
            supporting_facts = obj.get("supporting_facts") or obj.get("supporting_facts", {})
            context = obj.get("context", {})

            if not example_id or not question:
                continue

            # supporting_facts may be either a dict with 'title' and 'sent_id' arrays as shown,
            # or a list of [title, sent_id] pairs (classic HotpotQA). Handle both.
            supp_pairs: List[Tuple[str, int]] = []
            if isinstance(supporting_facts, dict):
                titles = supporting_facts.get("title") or []
                sent_ids = supporting_facts.get("sent_id") or []
                for t, s in zip(titles, sent_ids):
                    if t is not None and s is not None:
                        supp_pairs.append((t, int(s)))
            elif isinstance(supporting_facts, list):
                for item in supporting_facts:
                    if isinstance(item, list) and len(item) >= 2:
                        t, s = item[0], item[1]
                        if t is not None and s is not None:
                            supp_pairs.append((t, int(s)))

            context_titles: List[str] = context.get("title") or []
            context_sentences: List[List[str]] = context.get("sentences") or []

            # Build output fields
            out: Dict[str, Any] = {
                "id": example_id,
                "question": str(question).strip(),
            }

            if supp_pairs:
                out["supporting_facts"] = "; ".join([f"{t}:{s}" for t, s in supp_pairs])
            else:
                out["supporting_facts"] = ""

            # Populate contexts+sentences from the entire context, sequentially, capped at 30 pairs
            pair_index = 1
            for ctx_idx, ctx_title in enumerate(context_titles or []):
                sentences_for_title: List[str] = []
                if ctx_idx < len(context_sentences):
                    maybe_list = context_sentences[ctx_idx]
                    if isinstance(maybe_list, list):
                        sentences_for_title = [str(s) for s in maybe_list]
                for sentence_text in sentences_for_title:
                    out[f"context{pair_index}"] = str(ctx_title)
                    out[f"sentence{pair_index}"] = str(sentence_text).strip()
                    pair_index += 1
                    if pair_index > 30:
                        break
                if pair_index > 30:
                    break

            # Ensure fixed schema up to 30 pairs
            for idx in range(1, 31):
                out.setdefault(f"context{idx}", "")
                out.setdefault(f"sentence{idx}", "")

            records.append(out)

    if not records:
        cols = ["id", "question", "supporting_facts"]
        for i in range(1, 31):
            cols.append(f"context{i}")
            cols.append(f"sentence{i}")
        pd.DataFrame([], columns=cols).to_csv(output_path, index=False)
        logging.info("Hotpot: no valid records found; wrote empty CSV to %s", output_path)
        return

    df = pd.DataFrame(records)
    # Metrics: duplicates and nulls
    initial_rows = len(df)
    dedup_df = df.drop_duplicates(subset=["id"])  # type: ignore[arg-type]
    dropped_dups = initial_rows - len(dedup_df)
    cleaned_df = dedup_df.dropna(subset=["id", "question"])  # type: ignore[arg-type]
    dropped_nulls = len(dedup_df) - len(cleaned_df)
    df = cleaned_df
    # Normalize whitespace on all string columns
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str).str.strip()

    df.to_csv(output_path, index=False)
    logging.info(
        "Hotpot: input=%d, dropped_duplicates=%d, dropped_null_rows=%d, output=%d, file=%s",
        initial_rows,
        dropped_dups,
        dropped_nulls,
        len(df),
        output_path,
    )


def process_fever_jsonl() -> None:
    import pandas as pd
    _ensure_processed_dir()
    input_path = os.path.join(DATA_DIR, "fever_train.jsonl")
    output_path = os.path.join(PROCESSED_DIR, "fever_train_clean.csv")

    if not os.path.exists(input_path):
        pd.DataFrame([], columns=["id", "verifiable", "label", "supports", "claims", "evidence"]).to_csv(output_path, index=False)
        logging.info("FEVER: source not found, wrote empty CSV to %s", output_path)
        return

    ids: List[Any] = []
    verifiables: List[str] = []
    labels: List[str] = []
    supports_flags: List[int] = []
    claims_out: List[str] = []
    evidences_out: List[str] = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            example_id = obj.get("id")
            claim = obj.get("claim")
            label = obj.get("label")
            verifiable = obj.get("verifiable")
            evidence = obj.get("evidence")

            if example_id is None or claim is None:
                continue

            ids.append(example_id)
            verifiables.append("" if verifiable is None else str(verifiable).strip())
            lab = "" if label is None else str(label).strip()
            labels.append(lab)
            supports_flags.append(1 if lab.upper() == "SUPPORTS" else 0)
            claims_out.append(str(claim).strip())
            # evidence may be nested list-of-lists; flatten to "title:sent_id" pairs
            flattened: List[str] = []
            if isinstance(evidence, list):
                for group in evidence:
                    if isinstance(group, list):
                        for item in group:
                            # FEVER format: [wiki_id, ann_id, title, sentence_index]
                            if isinstance(item, list) and len(item) >= 4:
                                title = item[2]
                                sent_idx = item[3]
                                try:
                                    flattened.append(f"{str(title)}:{int(sent_idx)}")
                                except Exception:
                                    continue
            evidences_out.append("; ".join(flattened))

    df = pd.DataFrame(
        {
            "id": ids,
            "verifiable": verifiables,
            "label": labels,
            "supports": supports_flags,
            "claims": claims_out,
            "evidence": evidences_out,
        }
    )
    initial_rows = len(df)
    dedup_df = df.drop_duplicates(subset=["id"])  # type: ignore[arg-type]
    dropped_dups = initial_rows - len(dedup_df)
    cleaned_df = dedup_df.dropna(subset=["id", "claims"])  # type: ignore[arg-type]
    dropped_nulls = len(dedup_df) - len(cleaned_df)
    df = cleaned_df
    df.to_csv(output_path, index=False)
    logging.info(
        "FEVER: input=%d, dropped_duplicates=%d, dropped_null_rows=%d, output=%d, file=%s",
        initial_rows,
        dropped_dups,
        dropped_nulls,
        len(df),
        output_path,
    )


def upload_processed_to_s3() -> None:
    hook = S3Hook(aws_conn_id=AWS_CONN_ID)
    uploaded_count = 0
    # Upload processed CSVs
    if os.path.exists(PROCESSED_DIR):
        for root, _dirs, files in os.walk(PROCESSED_DIR):
            for file_name in files:
                if not file_name.lower().endswith(".csv"):
                    continue
                local_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(local_path, DATA_DIR).replace("\\", "/")
                hook.load_file(
                    filename=local_path,
                    key=rel_path,
                    bucket_name=BUCKET_NAME,
                    replace=True,
                )
                uploaded_count += 1

    # Also upload source JSONL files under a raw/ prefix
    for src_name in ("hotpot_train.jsonl", "fever_train.jsonl"):
        local_src = os.path.join(DATA_DIR, src_name)
        if os.path.exists(local_src):
            hook.load_file(
                filename=local_src,
                key=f"raw/{src_name}",
                bucket_name=BUCKET_NAME,
                replace=True,
            )
            uploaded_count += 1
    logging.info("S3 upload complete. Files uploaded: %d to bucket=%s", uploaded_count, BUCKET_NAME)


with DAG(
    dag_id="process_and_upload_data",
    start_date=datetime(2023, 1, 1),
    schedule=None,
    catchup=False,
    tags=["processing", "s3", "upload"],
) as dag:
    t_hotpot = PythonOperator(
        task_id="process_hotpot",
        python_callable=process_hotpot_jsonl,
    )

    t_fever = PythonOperator(
        task_id="process_fever",
        python_callable=process_fever_jsonl,
    )

    t_upload = PythonOperator(
        task_id="upload_processed_to_s3",
        python_callable=upload_processed_to_s3,
    )

    [t_hotpot, t_fever] >> t_upload


