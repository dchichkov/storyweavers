#!/usr/bin/env python3
"""Play, demonstrate, inspect, or replay The Last Place Setting."""
import argparse
import json
from pathlib import Path

from engine import Session, replay


DEMOS = {
    "repair": ["empathize mara", "ask letter", "ask letter", "empathize eli",
               "ask receipt", "ask receipt", "reflect mara", "reflect eli", "mediate"],
    "distrust": ["blame mara", "ask letter", "ask letter", "blame eli",
                 "ask receipt", "ask receipt", "reflect mara", "reflect eli", "mediate"],
    "space": ["listen", "ask receipt", "ask receipt", "support mara", "blame eli",
              "ask letter", "ask letter", "space"],
    "silent": [],
    "ejected": ["listen", "provoke", "provoke"],
    "leave": ["listen", "leave"],
    "initiative": ["empathize mara", "empathize eli", "open floor"],
    "private": ["empathize mara", "talk mara", "ask work", "ask fear", "promise privacy", "encourage honesty", "return",
                "empathize eli", "talk eli", "ask work", "ask fear", "promise privacy", "encourage honesty", "return", "open floor"],
    "practical": ["listen", "ask letter", "ask letter", "ask receipt", "ask receipt",
                  "ask time", "ask time", "ask money", "ask money", "plan refund", "plan visit"],
    "betrayal": ["empathize mara", "talk mara", "ask work", "promise privacy", "return", "tell mara", "apologize"],
    "separate": ["empathize mara", "ask letter", "ask letter", "empathize eli", "ask receipt", "ask receipt",
                 "reflect mara", "reflect eli", "ask future", "ask future", "ask future", "separate"],
}


def run_demo(name, seed=0):
    session = Session(seed)
    session.start()
    for command in DEMOS[name]:
        if session.outcome:
            break
        session.step(command)
    while not session.outcome:
        session.step("listen")
    return session


def print_lines(lines):
    print("\n" + "\n\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description="An original, turn-based miniature of a beat-driven domestic drama.")
    parser.add_argument("--seed", type=int, default=0, help="Reproducible tie-breaking between equally ranked beats")
    parser.add_argument("--demo", choices=DEMOS, help="Play an authored input script")
    parser.add_argument("--trace", type=Path, help="Save inputs, world events, beat scores, and final state as JSON")
    parser.add_argument("--replay", type=Path, help="Re-execute and verify a previously saved trace")
    parser.add_argument("--resume", type=Path, help="Verify a partial trace and continue playing it")
    parser.add_argument("--inspect", action="store_true", help="Print director decisions after a demo or replay")
    args = parser.parse_args()
    if args.replay:
        record = json.loads(args.replay.read_text(encoding="utf-8"))
        session = replay(record)
        if session.export() != record:
            parser.error("Replay differs from the saved trace; content or engine may have changed.")
        print_lines(session.transcript)
        print("\nReplay verified: all events, decisions, and final state match.")
    elif args.demo:
        session = run_demo(args.demo, args.seed)
        print_lines(session.transcript)
    else:
        if args.resume:
            record = json.loads(args.resume.read_text(encoding="utf-8"))
            session = replay(record)
            if session.export() != record:
                parser.error("Saved session no longer matches this version.")
            print_lines(session.transcript)
        else:
            session = Session(args.seed)
            print_lines(session.start())
        print("\nType help for moves; listen lets the scene continue. You can also enter a move's number.")
        while not session.outcome:
            try:
                command = input("\nYour move> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession paused at exit; use --trace to keep a replayable record.")
                break
            if command.lower() == "help":
                for i, (action, label) in enumerate(session.actions().items(), 1):
                    print("{:2}. {:18} {}".format(i, action, label))
                print("    look / state / why: inspect the room, world, or latest director choice (no turn).")
                continue
            if command.lower() == "look":
                for name, prop in session.state["props"].items():
                    print("{}: {} ({})".format(name, prop["location"], prop["state"]))
                continue
            if command.lower() == "state":
                print(json.dumps(session.snapshot(), indent=2))
                continue
            if command.lower() == "why":
                print(json.dumps(session.selections[-1] if session.selections else {}, indent=2))
                continue
            if command.isdigit() and 1 <= int(command) <= len(session.actions()):
                command = list(session.actions())[int(command) - 1]
            print_lines(session.step(command))
    if session.outcome:
        print("\n[Ending: {}]".format(session.outcome))
    if args.inspect:
        print(json.dumps(session.selections, indent=2))
    if args.trace:
        session.save(args.trace)
        print("\nSaved trace: " + str(args.trace))


if __name__ == "__main__":
    main()
