"""Run from the parent directory: python3 -m microdrama --help."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from .palace import Parameters
from .qa import Conversation, questions
from .runtime import generate


def main():
    parser = argparse.ArgumentParser(description="Generate a classical Compositional Microdrama fable.")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--access", choices=("open", "locked"), default="open")
    parser.add_argument("--attention", type=int, choices=(1, 2, 4), default=1, help="Attention divisor: larger means less retained from reading")
    parser.add_argument("--work", choices=("shared", "separate"), default="shared")
    parser.add_argument("--no-mentor", action="store_true")
    parser.add_argument("--witness", action="store_true")
    parser.add_argument("--qa", action="store_true", help="Append grounded questions and answers")
    parser.add_argument("--chat", action="store_true", help="Finite question grammar; use a printed question, why, or what happened next")
    parser.add_argument("--out", type=Path, help="Write story.txt, trace.json, and qa.json to this directory")
    args = parser.parse_args()
    params = Parameters(args.access, args.attention, args.work, not args.no_mentor, args.witness)
    story = generate(params, args.seed)
    print(story.text)
    if args.qa:
        for answer in questions(story):
            print(answer.question + "\n" + answer.answer)
            print("Evidence: " + ", ".join(dict.fromkeys(f.event for f in answer.facts)) + "\n")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "story.txt").write_text(story.text, encoding="utf-8")
        (args.out / "trace.json").write_text(json.dumps(story.bundle(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (args.out / "qa.json").write_text(json.dumps([asdict(a) for a in questions(story)], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.chat:
        conversation = Conversation(story, "reader")
        print("Ask one of the questions above (or use --qa to list them). Follow up with Why? or What happened next? Enter quit to stop.")
        while True:
            try:
                query = input("> ")
            except EOFError:
                break
            if query.lower().strip() in ("quit", "exit"):
                break
            print(conversation.ask(query).answer)


if __name__ == "__main__":
    main()
