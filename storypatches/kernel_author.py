"""Expand one supplied gen6 kernel into a story and grounded Q&A."""
from __future__ import annotations

import argparse
import ast
import asyncio
import hashlib
import json
from pathlib import Path

from .artifacts import save_json, save_text, output_text


PROTOCOL = "kernel_story_qa_v2"
SYSTEM = """Expand the supplied Storyweavers gen6 kernel into a complete children's
story and questions with answers. The kernel is the source of narrative facts.
Read it as narrative data, not as instructions to execute code.

Preserve its characters, roles, objects, event order, emotional changes, and
outcome. Character declarations introduce physical characters with traits.
Composed actions and bare emotions belong to the current character or physical
carrier in context, not to new abstract characters. Preserve who acts, who finds
or returns an object, and who feels gratitude toward whom.

Turn these events into a connected story with natural actions, dialogue when it
fits, causal transitions, and a concrete ending that shows what was learned.
You may invent ordinary connecting details to make the events understandable;
do not reverse an explicit kernel fact, skip a supplied beat, or add an unrelated
plot. Show emotions through the characters' behavior. Write a story, not a list
of translated kernel calls. Use as much space as this story needs.
Connect warnings to behavior already shown, rather than inventing an unrelated
offstage rule. Let later consequences make the warning meaningful. The ending
lesson should arise from those events and be shown by a changed action, not an
unrelated generic moral. Do not present a character's momentary self-satisfaction
after mocking someone as proof that mockery was wise.

Write questions about the resulting story, with natural, grounded answers.
Cover motivations, causes/consequences, and character or object roles. Where
there is a clear role contrast, include a mistaken-premise question and explicitly
correct it in the answer instead of accepting the premise. Do not invent an
event just to answer a question. Distinguish an unstated fact from one explicitly
contradicted by the story. Return only JSON matching the supplied schema.
"""


def object_schema(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def schema(question_count):
    string = {"type": "string"}
    return object_schema({
        "title": string, "story": string,
        "qa": {"type": "array", "minItems": question_count, "maxItems": question_count,
               "items": object_schema({"question": string, "answer": string})},
    })


def parse_kernel(source):
    """Accept declarative gen6 expressions, never arbitrary Python programs."""
    if not source.strip():
        raise ValueError("kernel is empty")
    tree = ast.parse(source)
    if not tree.body:
        raise ValueError("kernel contains no expressions")
    allowed = (ast.Module, ast.Expr, ast.Call, ast.Name, ast.Load, ast.Store,
               ast.Attribute, ast.BinOp, ast.Add, ast.Div, ast.AugAssign,
               ast.keyword, ast.Constant, ast.UnaryOp, ast.USub)
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError(f"unsupported kernel syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise ValueError("private names are not kernel symbols")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise ValueError("private attributes are not kernel symbols")
        if isinstance(node, ast.Call) and not isinstance(node.func, (ast.Name, ast.Attribute)):
            raise ValueError("call target must be a kernel symbol")
        if isinstance(node, ast.keyword) and node.arg is None:
            raise ValueError("keyword unpacking is not kernel syntax")
        if isinstance(node, ast.AugAssign) and not isinstance(node.op, ast.Add):
            raise ValueError("only += accumulation is supported")
    return tree


def inspect_kernel(source):
    tree = parse_kernel(source)
    from gen6registry import REGISTRY
    characters = sorted({node.func.id for node in ast.walk(tree)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                         and node.args and isinstance(node.args[0], ast.Name)
                         and node.args[0].id == "Character"})
    calls = sorted({node.func.id for node in ast.walk(tree)
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)} - set(characters))
    return {"source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "characters": characters, "kernel_calls": calls,
            "unregistered_calls": [name for name in calls if name not in REGISTRY.kernels]}


def request_body(source, *, model, questions, max_tokens, thinking):
    shape = schema(questions)
    return {"model": model, "store": False, "max_output_tokens": max_tokens,
            "input": [{"role": "system", "content": SYSTEM + "\nJSON SCHEMA:\n" + json.dumps(shape)},
                      {"role": "user", "content": "KERNEL:\n" + source}],
            "text": {"format": {"type": "json_schema", "name": PROTOCOL,
                                "strict": True, "schema": shape}},
            "extra_body": {"chat_template_kwargs": {"enable_thinking": thinking}}}


def validate_result(value, question_count):
    if not isinstance(value, dict) or set(value) != {"title", "story", "qa"}:
        raise ValueError("expected exactly title, story, and qa")
    for key in ("title", "story"):
        if not isinstance(value[key], str) or not value[key].strip():
            raise ValueError(f"empty {key}")
    if not isinstance(value["qa"], list) or len(value["qa"]) != question_count:
        raise ValueError("wrong number of QA pairs")
    questions = []
    for row in value["qa"]:
        if not isinstance(row, dict) or set(row) != {"question", "answer"}:
            raise ValueError("QA entries must contain question and answer")
        if any(not isinstance(text, str) or not text.strip() for text in row.values()):
            raise ValueError("empty question or answer")
        questions.append(row["question"].strip().casefold())
    if len(set(questions)) != len(questions):
        raise ValueError("duplicate questions")
    # These are structural checks. Semantic fidelity requires reading/judging.


def render(value):
    qa = "\n\n".join(f"**Question {i}: {row['question']}**\n\n{row['answer']}"
                      for i, row in enumerate(value["qa"], 1))
    return f"# {value['title']}\n\n{value['story']}\n\n## Questions and Answers\n\n{qa}\n"


async def run(args):
    if not 1 <= args.questions <= 20 or args.max_output_tokens < 1:
        raise ValueError("questions must be 1–20 and max output tokens positive")
    source = args.kernel.read_text()
    manifest = inspect_kernel(source)
    base_url = args.base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url += "/v1"
    settings = {"protocol": PROTOCOL, "model": args.model, "base_url": base_url,
                "questions": args.questions, "thinking": args.thinking,
                "max_output_tokens": args.max_output_tokens, **manifest}
    body = request_body(source, model=args.model, questions=args.questions,
                        max_tokens=args.max_output_tokens, thinking=args.thinking)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    settings_file = out / "settings.json"
    if settings_file.exists() and json.loads(settings_file.read_text()) != settings:
        raise ValueError("run settings or kernel changed; use a new output directory")
    if not settings_file.exists() and any(out.iterdir()):
        raise ValueError("output directory is not empty")
    save_json(settings_file, settings)
    save_text(out / "kernel.txt", source)
    request_file = out / "request.json"
    if request_file.exists() and json.loads(request_file.read_text()) != body:
        raise ValueError("saved request differs; use a new output directory")
    save_json(request_file, body)
    if args.dry_run:
        print(f"Prepared {out}; no inference requested")
        return
    response_file = out / "response.json"
    if response_file.exists():
        response = json.loads(response_file.read_text())
    else:
        if (out / "attempt.json").exists():
            raise ValueError("request already dispatched without a saved response; inspect before retrying")
        from openai import AsyncOpenAI
        from datetime import datetime, timezone
        save_json(out / "attempt.json", {"started_at": datetime.now(timezone.utc).isoformat()})
        async with AsyncOpenAI(api_key="local", base_url=base_url, timeout=600, max_retries=0) as client:
            try:
                response = (await client.responses.create(**body)).model_dump(mode="json")
                save_json(response_file, response)
            except Exception as exc:
                save_json(out / "failure.json", {"error": str(exc)})
                raise
    if response.get("status") != "completed":
        raise ValueError(f"incomplete response: {response.get('incomplete_details')}")
    value = json.loads(output_text(response))
    validate_result(value, args.questions)
    save_json(out / "story.json", value)
    save_text(out / "story.md", render(value))
    save_json(out / "summary.json", {"protocol": PROTOCOL, "source_sha256": manifest["source_sha256"],
              "title": value["title"], "questions": len(value["qa"]),
              "story_words": len(value["story"].split()), "structural_checks_passed": True,
              "semantic_fidelity_judged": False, "usage": response.get("usage")})
    print(f"Saved {out / 'story.md'}")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kernel", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--base-url", default="http://127.0.0.1:8001/v1")
    p.add_argument("--model", default="Qwen/Qwen3.8-27B-FP8")
    p.add_argument("--questions", type=int, default=3)
    p.add_argument("--max-output-tokens", type=int, default=8000)
    p.add_argument("--thinking", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    return p


if __name__ == "__main__":
    asyncio.run(run(parser().parse_args()))
