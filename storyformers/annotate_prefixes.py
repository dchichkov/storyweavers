"""Parallel Luna/Flex annotation: one last-word record per causal story prefix."""

import argparse
import asyncio
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import time
import uuid

from .annotation import MODEL, fingerprint, sdk_kwargs, story_tokens
from .annotate import freeze, load_stories, read, save
from .positions import POSITION_ENCODING
from . import prefix_annotation as legacy_contract, catalog_prefix_annotation as catalog_contract
from . import catalog_prefix_v3
from .prefix_annotation import (EXAMPLES, PROMPT, VERSION, assemble, prefix_request,
                                request_prefix, shared_prefix, validate_record)

CONTRACTS = {"legacy": legacy_contract, "catalog-v2": catalog_contract, "catalog": catalog_prefix_v3}


def contract_for(body):
    for contract in CONTRACTS.values():
        if body["prompt_cache_key"].startswith(contract.VERSION + ":"):
            return contract
    raise ValueError("unknown prefix annotation contract")


async def dispatch(directory, body, client, retries=5):
    """Journal each attempt; resume completed responses without resubmitting."""
    response_path = directory / "response.json"
    if response_path.exists():
        return read(response_path)
    attempts = directory / "attempts"
    attempts.mkdir(exist_ok=True)
    previous = sorted(attempts.iterdir())
    if previous:
        error_path = previous[-1] / "error.json"
        error = read(error_path) if error_path.exists() else {}
        if error.get("status") != 429 or error.get("code") != "flex_unavailable":
            raise RuntimeError("previous dispatch has no definite Flex rejection; inspect before resubmitting")
    for retry in range(retries + 1):
        attempt = attempts / f"{len(list(attempts.iterdir())) + 1:03d}"
        attempt.mkdir()
        identifier = str(uuid.uuid4())
        save(attempt / "dispatch.json", dict(started_at=time.time(), request_sha256=fingerprint(body),
                                            idempotency_key=identifier))
        started = time.monotonic()
        try:
            response = await client.responses.create(**sdk_kwargs(body),
                extra_headers={"Idempotency-Key": identifier})
            raw = response.model_dump(mode="json")
            save(response_path, raw)
            save(attempt / "completed.json", dict(elapsed_seconds=time.monotonic() - started))
            return raw
        except Exception as error:
            status, code = getattr(error, "status_code", None), getattr(error, "code", None)
            save(attempt / "error.json", dict(type=type(error).__name__, status=status, code=code,
                                              elapsed_seconds=time.monotonic() - started))
            if status != 429 or code != "flex_unavailable" or retry == retries:
                raise
            print(f"{directory.name}: Flex unavailable; retrying on Flex", file=sys.stderr, flush=True)
            await asyncio.sleep(min(10 * 2 ** retry, 60))


def response_text(raw):
    model = raw.get("model", "")
    if (model != MODEL and not model.startswith(MODEL + "-")) or raw.get("service_tier") != "flex":
        raise ValueError("expected Luna served on Flex; response retained")
    if raw.get("status") != "completed":
        raise ValueError("incomplete response; no partial record accepted")
    texts = []
    for item in raw.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "refusal":
                    raise ValueError("model refused the annotation")
                if part.get("type") == "output_text":
                    texts.append(part["text"])
    return "".join(texts)


def extract(body, raw):
    contract = contract_for(body)
    text = request_prefix(body)
    record = contract.validate_record(text, json.loads(response_text(raw)))
    usage = raw.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    metadata = dict(version=contract.VERSION, annotation_mode="prefix_last_word", model=raw["model"],
                    service_tier="flex", response_id=raw.get("id"), target_index=record["index"],
                    prefix_sha256=fingerprint(text), prefix_end=len(text),
                    request_sha256=fingerprint(body), prompt_cache_key=body["prompt_cache_key"],
                    prompt_cache_options=body["prompt_cache_options"], usage=usage,
                    cached_tokens=details.get("cached_tokens", 0),
                    cache_write_tokens=details.get("cache_write_tokens", 0))
    return record, metadata


async def annotate_word(directory, client, *, validation_repairs=1):
    body = read(directory / "request.json")
    original_body = body
    current, usages = directory, []
    for attempt in range(validation_repairs + 1):
        raw = await dispatch(current, body, client)
        usages.append(raw.get("usage") or {})
        try:
            record, metadata = extract(body, raw)
        except ValueError as error:
            save(current / "validation.json", dict(ok=False, error=str(error)))
            if attempt == validation_repairs or contract_for(body) is legacy_contract:
                raise
            # Only completed Luna/Flex JSON gets bounded, journaled corrections.
            # Rebuild from the original prefix so failed drafts do not accumulate.
            rejected = response_text(raw)
            current = directory / "repairs" / f"{attempt + 1:03d}"
            current.mkdir(parents=True, exist_ok=True)
            body = deepcopy(original_body)
            anchors = [{"index": span["index"], "token": span["token"],
                        "entity": f"e{span['index'] + 1}", "event": f"ev{span['index'] + 1}",
                        "scope": f"s{span['index'] + 1}", "proposition": f"p{span['index'] + 1}"}
                       for span in story_tokens(request_prefix(body)) if span["kind"] == "word"]
            body["input"][1]["content"][-1]["text"] += (
                "\nYour previous JSON failed local validation. Return the corrected last-word JSON only. "
                "The supplied prefix is still the entire evidence; the rejected draft is not evidence. "
                "Reuse grounded values and fix the validation error.\n" +
                json.dumps(dict(error=str(error), allowed_span_anchors=anchors, rejected_draft=rejected), ensure_ascii=False))
            freeze(current / "request.json", body)
        else:
            save(current / "validation.json", dict(ok=True))
            break
    if len(usages) > 1:
        metadata.update(validation_repairs=len(usages) - 1, original_request_sha256=fingerprint(original_body))
        metadata["request_usages"] = usages
        for name in ("cached_tokens", "cache_write_tokens"):
            metadata[name] = sum((usage.get("input_tokens_details") or {}).get(name, 0)
                                 for usage in metadata["request_usages"])
    save(directory / "annotation.json", record)
    save(directory / "metadata.json", metadata)
    save(directory / "validation.json", dict(ok=True))
    return metadata


async def annotate_jobs(jobs, client, *, concurrency=8, validation_repairs=1):
    """Warm the shortest pending prefix, then use ordered, bounded parallel waves.

    Every wave completes before longer prefixes are dispatched, making its saved
    word-boundary caches eligible for the next wave. Outputs are never fed back.
    """
    if type(concurrency) is not int or concurrency < 1:
        raise ValueError("concurrency must be a positive integer")
    if type(validation_repairs) is not int or validation_repairs < 0:
        raise ValueError("validation_repairs must be a nonnegative integer")
    ordered = sorted(jobs, key=lambda job: (job["prefix_words"], job["prefix_end"], str(job["directory"])))
    summaries = []

    async def one(job):
        metadata = await annotate_word(job["directory"], client, validation_repairs=validation_repairs)
        print(f"{job['directory'].parent.parent.name}/{job['directory'].name}: "
              f"cached={metadata['cached_tokens']}, cache_write={metadata['cache_write_tokens']}", flush=True)
        return dict(directory=str(job["directory"]), **metadata)

    warm = next((job for job in ordered if not (job["directory"] / "response.json").exists()), None)
    if warm is not None:
        summaries.append(await one(warm))
        ordered.remove(warm)
    for offset in range(0, len(ordered), concurrency):
        # Wait for all already-dispatched tasks even if one fails; retain their
        # responses and avoid cancelling another request whose billing is unknown.
        results = await asyncio.gather(*(one(job) for job in ordered[offset:offset + concurrency]),
                                       return_exceptions=True)
        summaries.extend(result for result in results if not isinstance(result, BaseException))
        error = next((result for result in results if isinstance(result, BaseException)), None)
        if error is not None:
            raise error
    return summaries


def prepare(args):
    contract = CONTRACTS[getattr(args, "contract", "legacy")]
    prefix = contract.shared_prefix(args.prompt_file or contract.PROMPT, args.examples_file or contract.EXAMPLES)
    args.out.mkdir(parents=True, exist_ok=True)
    freeze(args.out / "prompt.json", dict(version=contract.VERSION, prefix=prefix))
    stories, jobs = [], []
    for index, story in enumerate(load_stories(args)):
        directory = args.out / f"{index:06d}_{fingerprint(story)[:12]}"
        directory.mkdir(exist_ok=True)
        freeze(directory / "story.json", dict(story=story))
        local_jobs = []
        for ordinal, span in enumerate(row for row in story_tokens(story) if row["kind"] == "word"):
            target = directory / "prefixes" / f"{span['index']:06d}"
            target.mkdir(parents=True, exist_ok=True)
            body = contract.prefix_request(story, span["index"], prefix=prefix, reasoning=args.reasoning,
                                  max_output_tokens=args.max_output_tokens)
            freeze(target / "request.json", body)
            job = dict(directory=target, prefix_end=span["end"], prefix_words=ordinal + 1,
                       target_index=span["index"])
            jobs.append(job)
            local_jobs.append(job)
        stories.append(dict(story=story, directory=directory, jobs=local_jobs))
    if not stories:
        raise ValueError("no stories selected")
    manifest = [dict(directory=str(item["directory"].relative_to(args.out)), story_sha256=fingerprint(item["story"]),
                     prefixes=[dict(directory=str(job["directory"].relative_to(args.out)),
                                    target_index=job["target_index"], prefix_end=job["prefix_end"],
                                    prefix_words=job["prefix_words"]) for job in item["jobs"]]) for item in stories]
    freeze(args.out / "manifest.json", manifest)
    return stories, jobs


def finish(stories, out, *, concurrency, elapsed_seconds, contract=legacy_contract):
    summaries = []
    for item in stories:
        directory, story = item["directory"], item["story"]
        records = [read(job["directory"] / "annotation.json") for job in item["jobs"]]
        try:
            result = contract.assemble(story, records)
        except ValueError as error:
            save(directory / "validation.json", dict(ok=False, error=str(error)))
            raise
        metadata = [read(job["directory"] / "metadata.json") for job in item["jobs"]]
        summary = dict(version=contract.VERSION, annotation_mode="prefix_last_word", directory=directory.name,
                       model=MODEL, service_tier="flex", story_sha256=fingerprint(story),
                       token_count=len(result), word_count=len(records),
                       local_records=len(result) - len(records), position_encoding=dict(POSITION_ENCODING),
                       entity_id_encoding="e(first_head_span_index+1)", event_id_encoding="ev(trigger_span_index+1)",
                       cached_tokens=sum(row["cached_tokens"] for row in metadata),
                       cache_write_tokens=sum(row["cache_write_tokens"] for row in metadata),
                       validation_repairs=sum(row.get("validation_repairs", 0) for row in metadata),
                       usage=[usage for row in metadata for usage in row.get("request_usages", [row["usage"]])])
        save(directory / "annotations.json", result)
        if contract is not legacy_contract:
            save(directory / "reference_snapshots.json", {
                str(row["index"]): {key: row[key] for key in contract.META if key in row}
                for row in records})
        save(directory / "metadata.json", summary)
        save(directory / "validation.json", dict(ok=True))
        summaries.append(summary)
    save(out / "summary.json", dict(version=contract.VERSION, concurrency=concurrency,
                                    schedule="shortest pending warmup, then ascending prefix-length waves",
                                    elapsed_seconds=elapsed_seconds, stories=summaries))
    return summaries


async def run(args, client=None):
    stories, jobs = prepare(args)
    if args.prepare_only:
        print(f"Prepared {len(jobs)} last-word requests; spaces/punctuation stay local. No API calls made.")
        return
    started = time.monotonic()
    validation_repairs = getattr(args, "validation_repairs", 1)
    def needs_dispatch(job):
        directory = job["directory"]
        catalog = contract_for(read(directory / "request.json")) is not legacy_contract
        candidates = [directory] + ([directory / "repairs" / f"{i:03d}" for i in range(1, validation_repairs + 1)] if catalog else [])
        for candidate in candidates:
            if not (candidate / "response.json").exists():
                return True
            try:
                extract(read(candidate / "request.json"), read(candidate / "response.json"))
            except ValueError:
                # Refusals, incomplete results and wrong tiers cannot be repaired.
                response_text(read(candidate / "response.json"))
            else:
                return False
        return False

    needs_network = any(needs_dispatch(job) for job in jobs)
    if client is not None or not needs_network:
        await annotate_jobs(jobs, client, concurrency=args.concurrency, validation_repairs=validation_repairs)
    else:
        from openai import AsyncOpenAI

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            key = (args.api_key_file or Path(__file__).resolve().parents[1] / ".API_KEY").read_text().strip()
        async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1",
                               timeout=900, max_retries=0) as connection:
            await annotate_jobs(jobs, connection, concurrency=args.concurrency, validation_repairs=validation_repairs)
    contract = CONTRACTS[getattr(args, "contract", "legacy")]
    result = finish(stories, args.out, concurrency=args.concurrency, elapsed_seconds=time.monotonic() - started,
                    contract=contract)
    print(f"Saved {sum(row['word_count'] for row in result)} prefix-only word records in {args.out}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--story")
    source.add_argument("--story-file", type=Path)
    source.add_argument("--input", type=Path, help="JSONL or one-story-per-line text")
    parser.add_argument("--text-key", default="story")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--contract", choices=list(CONTRACTS), default="catalog")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--examples-file", type=Path)
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--reasoning", choices=["none", "low", "medium", "high"], default="low")
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument("--validation-repairs", type=int, default=1, help="Maximum extra catalog correction calls per word")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    if args.concurrency < 1 or args.max_output_tokens < 1 or args.validation_repairs < 0 or (args.limit is not None and args.limit < 1):
        parser.error("concurrency, output cap and limit must be positive; validation repairs must be nonnegative")
    try:
        asyncio.run(run(args))
    except (ValueError, OSError) as error:
        print(f"Prefix annotation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as error:
        print(f"Prefix annotation failed: {type(error).__name__}. Inspect saved artifacts in {args.out}.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
