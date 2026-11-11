"""Training-time neuron iteration: profile -> LLM proposal -> measured evaluation."""

import argparse
import asyncio
import json
import os
from pathlib import Path
import sys

from .annotation import MODEL, fingerprint
from .annotate import freeze, read, save
from .annotate_prefixes import dispatch
from .neuron_review import VERSION, collect, evaluate_proposal, proposal_template
from .neuron_spec import parse_neuron
from .transformer import Storyformer


PROMPT = Path(__file__).resolve().parent / "prompts" / "refine_neuron_v1.txt"


def load_documents(path):
    metadata = path.with_name("metadata.json")
    if path.name == "annotations.json" and metadata.exists() and read(metadata).get("annotation_mode") == "full_story_offline":
        raise ValueError("whole-story annotations can leak future labels; use prefix_last_word annotations for this workflow")
    if path.suffix == ".jsonl":
        documents = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    else:
        value = read(path)
        documents = [value] if isinstance(value, list) and value and isinstance(value[0], dict) else value
    if (not isinstance(documents, list) or not documents or any(not isinstance(document, list) or
            any(not isinstance(row, dict) or "token" not in row for row in document) for document in documents)):
        raise ValueError("expected annotated document arrays, as JSON or one document per JSONL line")
    return documents


def revision_request(packet, *, goal=None, reasoning="low", max_output_tokens=4096):
    prompt = PROMPT.read_text()
    # Free-form feature dictionaries and recursive grammar expressions are
    # parsed locally; JSON mode supplies a JSON object, not schema validation.
    body = dict(model=MODEL, service_tier="flex", store=False, reasoning={"effort": reasoning},
                max_output_tokens=max_output_tokens, text={"format": {"type": "json_object"}},
                prompt_cache_options={"mode": "explicit", "ttl": "30m"})
    body["prompt_cache_key"] = VERSION + ":" + fingerprint([prompt, MODEL, body["reasoning"], body["text"]])[:24]
    message = dict(profile=packet, proposal_template=proposal_template(packet))
    if goal is not None:
        message["goal"] = goal
    body["input"] = [dict(role="developer", content=[dict(type="input_text", text=prompt,
                        prompt_cache_breakpoint={"mode": "explicit"})]),
                     dict(role="user", content=json.dumps(message, ensure_ascii=False, separators=(",", ":")))]
    return body


async def propose(packet, directory, *, client=None, prepare_only=False, goal=None, reasoning="low", api_key_file=None):
    directory.mkdir(parents=True, exist_ok=True)
    body = revision_request(packet, goal=goal, reasoning=reasoning)
    freeze(directory / "request.json", body)
    if prepare_only:
        return None
    if client is not None or (directory / "response.json").exists():
        raw = await dispatch(directory, body, client)
    else:
        from openai import AsyncOpenAI

        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            key = (api_key_file or Path(__file__).resolve().parents[1] / ".API_KEY").read_text().strip()
        async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=900, max_retries=0) as connection:
            raw = await dispatch(directory, body, connection)
    try:
        served = raw.get("model", "")
        if ((served != MODEL and not served.startswith(MODEL + "-")) or raw.get("service_tier") != "flex"
                or raw.get("status") != "completed"):
            raise ValueError("expected a completed Luna/Flex response")
        texts = []
        for item in raw.get("output", []):
            if item.get("type") == "message":
                for part in item.get("content", []):
                    if part.get("type") == "refusal":
                        raise ValueError("model refused the revision")
                    if part.get("type") == "output_text":
                        texts.append(part["text"])
        payload = json.loads("".join(texts))
        if (not isinstance(payload, dict) or set(payload) != set(proposal_template(packet))
                or payload["base_model_sha256"] != packet["base_model_sha256"]
                or payload["address"] != packet["address"] or payload["format"] != VERSION):
            raise ValueError("proposal changed its base identity or revision contract")
        parse_neuron(payload["neuron"], context_size=packet["context_size"], max_states=packet["neuron"]["max_states"])
    except (ValueError, TypeError, KeyError) as error:
        save(directory / "validation.json", dict(ok=False, error=str(error)))
        raise
    freeze(directory / "proposal.json", payload)
    save(directory / "metadata.json", dict(model=served, service_tier="flex", usage=raw.get("usage"),
                                          prompt_cache_key=body["prompt_cache_key"], packet_sha256=packet["packet_sha256"]))
    save(directory / "validation.json", dict(ok=True, scope="syntax only; evaluation is a separate step"))
    return payload


def _save_model(model, path):
    if path.exists():
        from .neuron_review import model_fingerprint
        if model_fingerprint(Storyformer.load(path)) != model_fingerprint(model):
            raise ValueError("existing checkpoint differs; use a new output directory")
    else:
        model.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="step", required=True)
    profile = commands.add_parser("profile")
    profile.add_argument("--model", type=Path, required=True)
    profile.add_argument("--train", type=Path, required=True)
    address = profile.add_mutually_exclusive_group(required=True)
    address.add_argument("--head", type=int)
    address.add_argument("--token")
    profile.add_argument("--layer", type=int, default=0)
    profile.add_argument("--max-examples", type=int, default=4)
    profile.add_argument("--out", type=Path, required=True)
    proposal = commands.add_parser("propose")
    proposal.add_argument("--profile", type=Path, required=True)
    proposal.add_argument("--out", type=Path, required=True)
    proposal.add_argument("--prepare-only", action="store_true")
    proposal.add_argument("--goal", help="optional objective, e.g. canonicalize names while preserving predictions")
    proposal.add_argument("--reasoning", choices=["none", "low", "medium", "high"], default="low")
    proposal.add_argument("--api-key-file", type=Path)
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--model", type=Path, required=True)
    evaluate.add_argument("--proposal", type=Path, required=True)
    evaluate.add_argument("--train", type=Path, required=True)
    evaluate.add_argument("--validation", type=Path, required=True)
    evaluate.add_argument("--fit-epochs", type=int, default=0)
    evaluate.add_argument("--learning-rate", type=float, default=.1)
    evaluate.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        if args.step == "profile":
            target = (dict(kind="head", layer=args.layer, head=args.head) if args.head is not None
                      else dict(kind="output", token=args.token))
            packet = collect(Storyformer.load(args.model), load_documents(args.train), target, max_examples=args.max_examples)
            freeze(args.out / "profile.json", packet)
            print(f"Profiled {packet['neuron']['name']}: {packet['stats']['matched_targets']}/{packet['stats']['targets']} matched targets")
        elif args.step == "propose":
            packet = read(args.profile)
            asyncio.run(propose(packet, args.out, prepare_only=args.prepare_only,
                                goal=args.goal, reasoning=args.reasoning, api_key_file=args.api_key_file))
            print("Prepared request; no API call." if args.prepare_only else "Saved proposed neuron revision.")
        else:
            candidate, report = evaluate_proposal(Storyformer.load(args.model), read(args.proposal),
                load_documents(args.train), load_documents(args.validation),
                fit_epochs=args.fit_epochs, learning_rate=args.learning_rate)
            freeze(args.out / "evaluation.json", report)
            if candidate is not None:
                _save_model(candidate, args.out / "candidate_model.json")
            if report["accepted"]:
                _save_model(candidate, args.out / "accepted_model.json")
            print(json.dumps(report, indent=2))
    except (ValueError, OSError) as error:
        print(f"Neuron review failed: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    except Exception as error:
        print(f"Neuron review failed: {type(error).__name__}. Inspect {args.out}.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
