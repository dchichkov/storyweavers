"""Offline Luna/Flex annotation pipeline with frozen requests and cache evidence."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys
import time
import uuid

from .annotation import (EXAMPLES, MODEL, PROMPT, VERSION, annotation_request, fingerprint,
                         sdk_kwargs, shared_prefix, validate_annotations)
from .positions import POSITION_ENCODING, add_positions


def save(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def freeze(path: Path, value):
    if path.exists():
        if read(path) != value:
            raise ValueError(f"{path}: existing artifact differs; use a new output directory")
    else:
        save(path, value)


def prepare(story: str, directory: Path, *, prefix=None, reasoning="low", max_output_tokens=32000):
    body = annotation_request(story, prefix=prefix, reasoning=reasoning, max_output_tokens=max_output_tokens)
    directory.mkdir(parents=True, exist_ok=True)
    freeze(directory / "request.json", body)
    return body


def extract_response(story: str, body: dict, response: dict):
    served = response.get("model", "")
    if (served != MODEL and not served.startswith(MODEL + "-")) or response.get("service_tier") != "flex":
        raise ValueError("expected Luna served on Flex; response retained")
    if response.get("status") != "completed":
        raise ValueError("incomplete model output; response retained, no partial annotation accepted")
    texts = []
    for item in response.get("output", []):
        if item.get("type") == "message":
            for part in item.get("content", []):
                if part.get("type") == "refusal":
                    raise ValueError("model refused the annotation; response retained")
                if part.get("type") == "output_text":
                    texts.append(part["text"])
    result = add_positions(validate_annotations(story, json.loads("".join(texts))))
    usage = response.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    metadata = dict(version=VERSION, annotation_mode="full_story_offline", model=served,
                    service_tier="flex", response_id=response.get("id"),
                    prompt_cache_key=body["prompt_cache_key"],
                    prompt_cache_options=body["prompt_cache_options"],
                    request_sha256=fingerprint(body), story_sha256=fingerprint(story),
                    token_count=len(result), word_count=sum(row["kind"] == "word" for row in result),
                    position_encoding=dict(POSITION_ENCODING),
                    usage=usage, cached_tokens=details.get("cached_tokens", 0),
                    cache_write_tokens=details.get("cache_write_tokens", 0))
    return result, metadata


async def annotate_one(directory: Path, client, *, retries=2):
    """Reuse saved responses; retry only explicit uncharged capacity rejections."""
    body = read(directory / "request.json")
    story = json.loads(body["input"][1]["content"])["story"]
    response_path = directory / "response.json"
    if not response_path.exists():
        attempts = directory / "attempts"
        attempts.mkdir(exist_ok=True)
        prior = sorted(attempts.iterdir())
        if prior:
            error_path = prior[-1] / "error.json"
            error = read(error_path) if error_path.exists() else {}
            if error.get("status") != 429 or error.get("code") != "flex_unavailable":
                raise RuntimeError("previous dispatch has no definite Flex rejection; inspect before resubmitting")
        for retry in range(retries + 1):
            attempt = attempts / f"{len(list(attempts.iterdir())) + 1:03d}"
            attempt.mkdir()
            request_id = str(uuid.uuid4())
            save(attempt / "dispatch.json", dict(started_at=time.time(), request_sha256=fingerprint(body),
                                                idempotency_key=request_id))
            started = time.monotonic()
            try:
                response = await client.responses.create(**sdk_kwargs(body),
                    extra_headers={"Idempotency-Key": request_id})
                save(response_path, response.model_dump(mode="json"))
                save(attempt / "completed.json", dict(elapsed_seconds=time.monotonic() - started))
                break
            except Exception as error:
                # Do not save exception text: SDK/provider errors can echo inputs or headers.
                code = getattr(error, "code", None)
                status = getattr(error, "status_code", None)
                save(attempt / "error.json", dict(type=type(error).__name__, code=code,
                                                  status=status, elapsed_seconds=time.monotonic() - started))
                if status == 429 and code == "flex_unavailable" and retry < retries:
                    print(f"{directory.name}: Flex unavailable; retrying on Flex", file=sys.stderr, flush=True)
                    await asyncio.sleep(10 * 2 ** retry)
                else:
                    raise
    try:
        result, metadata = extract_response(story, body, read(response_path))
    except ValueError as error:
        save(directory / "validation.json", dict(ok=False, error=str(error)))
        raise
    save(directory / "annotations.json", result)
    save(directory / "metadata.json", metadata)
    save(directory / "validation.json", dict(ok=True))
    return metadata


def load_stories(args):
    if args.story is not None:
        yield args.story
    elif args.story_file:
        with args.story_file.open(encoding="utf-8", newline="") as source:
            yield source.read()
    else:
        with args.input.open(encoding="utf-8", newline="") as source:
            selected = 0
            for line in source:
                if not line.strip():
                    continue
                if args.limit is not None and selected >= args.limit:
                    break
                story = json.loads(line).get(args.text_key) if args.input.suffix == ".jsonl" else line.rstrip("\r\n")
                if not isinstance(story, str):
                    raise ValueError(f"expected a string in field {args.text_key!r}")
                selected += 1
                yield story


async def run(args):
    prefix = shared_prefix(args.prompt_file, args.examples_file)
    args.out.mkdir(parents=True, exist_ok=True)
    freeze(args.out / "prompt.json", dict(version=VERSION, prefix=prefix))
    jobs = []
    for i, story in enumerate(load_stories(args)):
        directory = args.out / f"{i:06d}_{fingerprint(story)[:12]}"
        body = prepare(story, directory, prefix=prefix, reasoning=args.reasoning,
                       max_output_tokens=args.max_output_tokens)
        jobs.append(dict(directory=directory.name, story_sha256=fingerprint(story),
                         prompt_cache_key=body["prompt_cache_key"]))
    if not jobs:
        raise ValueError("no stories selected")
    freeze(args.out / "manifest.json", jobs)
    if args.prepare_only:
        print(f"Prepared {len(jobs)} requests in {args.out}; no API calls made.")
        return
    from openai import AsyncOpenAI

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        key_file = args.api_key_file or Path(__file__).resolve().parents[1] / ".API_KEY"
        key = key_file.read_text().strip()
    # Sequential dispatch lets the first story populate the shared prefix cache.
    summaries = []
    async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1",
                           timeout=900, max_retries=0) as client:
        for job in jobs:
            metadata = await annotate_one(args.out / job["directory"], client)
            summaries.append(dict(directory=job["directory"], **metadata))
            save(args.out / "summary.json", summaries)
            print(f"{job['directory']}: {metadata['word_count']} words, "
                  f"cached={metadata['cached_tokens']}, cache_write={metadata['cache_write_tokens']}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--story", help="one story, preserving exact text")
    source.add_argument("--story-file", type=Path, help="one entire UTF-8 story file")
    source.add_argument("--input", type=Path, help="JSONL or one-document-per-line text corpus")
    parser.add_argument("--text-key", default="story")
    parser.add_argument("--limit", type=int, help="maximum documents from --input")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, default=PROMPT)
    parser.add_argument("--examples-file", type=Path, default=EXAMPLES)
    parser.add_argument("--reasoning", choices=["none", "low", "medium", "high"], default="low")
    parser.add_argument("--max-output-tokens", type=int, default=32000)
    parser.add_argument("--prepare-only", action="store_true", help="freeze requests without contacting Luna")
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    if (args.limit is not None and args.limit < 1) or args.max_output_tokens < 1:
        parser.error("limit and output cap must be positive")
    try:
        asyncio.run(run(args))
    except (ValueError, OSError) as error:
        print(f"Annotation failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as error:
        # Detailed transport errors are intentionally not printed with credentials.
        print(f"Annotation failed: {type(error).__name__}. Inspect saved artifacts in {args.out}.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
