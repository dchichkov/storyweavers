"""Run an opt-in capability world offline, with trace-grounded narrative and QA."""
import argparse
import json
from pathlib import Path

from .api import registry
from .codec import dumps, loads
from .choices import competing_promise_story
from .core import CapabilityError, fingerprint, plain, replay, solve
from .examples import delayed_report_story, loan_story, promise_story
from .reading import Reader
from .realize import render
from .realize import render_story
from . import story_examples


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sources = parser.add_mutually_exclusive_group(required=True)
    sources.add_argument("--world", type=Path, help="Explicit capability-v1 JSON world")
    sources.add_argument("--example", choices=("library", "harbor", "observatory", "choice"))
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-nodes", type=int, default=6000)
    parser.add_argument("--demo-path", action="store_true", help="Replay the pinned example path instead of searching")
    parser.add_argument("--hide-event", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--diagnostic", action="store_true", help="Use permissive conformance fixtures and verbose event realization")
    parser.add_argument("--save-world", type=Path, help="Write the typed initial specification; refuses to overwrite")
    args = parser.parse_args(argv)
    if args.max_nodes < 1 or args.demo_path and args.world:
        parser.error("Positive search budget required; --demo-path needs --example")
    engine = registry()
    scenario = None
    if args.example:
        scenario = {"library": loan_story, "harbor": delayed_report_story, "observatory": promise_story,
                    "choice": competing_promise_story}[args.example]()
        story_builders = {"library": story_examples.loan_story, "harbor": story_examples.delayed_report_story,
                          "observatory": story_examples.promise_story}
        if not args.diagnostic and args.example in story_builders:
            scenario = story_builders[args.example]()
        spec = scenario.spec
    else:
        spec = loads(engine, args.world.read_text(encoding="utf-8"))
    state = replay(engine, spec, scenario.path) if args.demo_path else solve(engine, spec, args.seed, max_nodes=args.max_nodes)
    verified = replay(engine, spec, [e.action.id for e in state.events])
    if verified != state:
        raise CapabilityError("Replay mismatch")
    # Free authored example flourishes belong to the pinned path, not arbitrary
    # solver variants whose selected actions may support different endings.
    document = (render if args.diagnostic else render_story)(
        spec, state, visible={e.id for e in state.events} - set(args.hide_event),
        premise=scenario.premise if scenario and args.demo_path and args.diagnostic else None,
        ending=scenario.ending if scenario and args.demo_path and args.diagnostic else None)
    answers = Reader(document).questions() if args.qa else []
    if args.save_world:
        with args.save_world.open("x", encoding="utf-8") as handle:
            handle.write(dumps(spec))
    if args.json:
        print(json.dumps(dict(schema=spec.schema, title=spec.title, seed=args.seed,
                story=document.story, statements=plain(document.statements), spans=document.spans(),
                qa=plain(answers), trace=plain(state), trace_sha256=fingerprint(state)), ensure_ascii=False))
    else:
        print(f"{spec.title}\n\n{document.story}")
        for answer in answers:
            print(f"\nQ: {answer.question}\nA: {answer.answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
