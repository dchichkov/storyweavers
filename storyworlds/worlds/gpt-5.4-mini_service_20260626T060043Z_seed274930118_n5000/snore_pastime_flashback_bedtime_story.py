#!/usr/bin/env python3
"""
A tiny bedtime story world about a child, a snore, a pastime, and a gentle
flashback that helps the night settle down.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]


@dataclass
class Place:
    id: str
    label: str
    quiet: bool = False


@dataclass
class Pastime:
    id: str
    label: str
    verb: str
    object_word: str
    flashback_hint: str


@dataclass
class StoryParams:
    place: str
    pastime: str
    child_name: str
    sibling_name: str
    seed: Optional[int] = None


PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", quiet=False),
    "nursery": Place(id="nursery", label="the nursery", quiet=False),
    "sleepy_room": Place(id="sleepy_room", label="the sleepy room", quiet=False),
}

PASTIMES = {
    "drawing": Pastime(
        id="drawing",
        label="drawing",
        verb="draw little moons",
        object_word="crayons",
        flashback_hint="the red crayon made a tiny comet on the page",
    ),
    "reading": Pastime(
        id="reading",
        label="reading",
        verb="read a picture book",
        object_word="storybook",
        flashback_hint="one page had a fox tucked under a quilt",
    ),
    "puzzles": Pastime(
        id="puzzles",
        label="puzzles",
        verb="finish a small puzzle",
        object_word="puzzle pieces",
        flashback_hint="a corner piece had clicked into place like a soft hello",
    ),
}


@dataclass
class World:
    place: Place
    pastime: Pastime
    child: Character
    sibling: Character
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    world_log: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.world_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a snore and a flashback pastime.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pastime", choices=PASTIMES)
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _seed_choice(rng: random.Random, options: list[str]) -> str:
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or _seed_choice(rng, list(PLACES))
    pastime = args.pastime or _seed_choice(rng, list(PASTIMES))
    child_name = args.name or _seed_choice(rng, ["Mina", "Lina", "Nora", "Ivy", "Tessa"])
    sibling = args.sibling or _seed_choice(rng, ["Pip", "Ben", "Milo", "June", "Theo"])
    return StoryParams(place=place, pastime=pastime, child_name=child_name, sibling_name=sibling)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.pastime not in PASTIMES:
        raise StoryError("Unknown pastime.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    place = PLACES[params.place]
    pastime = PASTIMES[params.pastime]
    child = Character(id=params.child_name, type="child", label=params.child_name)
    sibling = Character(id=params.sibling_name, type="child", label=params.sibling_name)

    child.memes["sleepy"] = 0
    child.memes["comfort"] = 0
    sibling.meters["snore"] = 1

    world = World(place=place, pastime=pastime, child=child, sibling=sibling)

    world.say(f"{child.id} lived in {place.label} with {sibling.id}, and bedtime had come.")
    world.say(f"{child.id} was sleepy, but {sibling.id} made a soft snore that went huff and puff in the dark.")
    world.para()
    world.say(f"At first, {child.id} stared at the ceiling and listened to the snore.")
    world.say(f"Then a flashback drifted in, gentle as a blanket: earlier that day, {child.id} had been {pastime.verb}.")
    world.say(f"{pastime.flashback_hint.capitalize()}. It had been a sweet pastime, and it made {child.id} smile again.")
    world.para()
    world.say(f"{child.id} quietly reached for {pastime.object_word} and remembered the fun, not the noise.")
    world.say(f"With a small breath and a calm heart, {child.id} tucked the memory away like a star.")
    world.say(f"The snore still went on, but it sounded far away now.")
    world.para()
    world.say(f"At last, {child.id} curled under the quilt, the room stayed cozy, and the night turned soft and still.")

    child.memes["sleepy"] = 1
    child.memes["comfort"] = 1
    world.facts = {
        "child": child,
        "sibling": sibling,
        "place": place,
        "pastime": pastime,
        "snore": True,
        "flashback": True,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child about a snore, a pastime, and a kind flashback in {f["place"].label}.',
        f'Tell a gentle story where {f["child"].id} hears a snore at night and remembers {f["pastime"].label} from earlier.',
        f'Write a cozy flashback story that uses the word "snore" and ends with the room growing quiet.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    place = f["place"]
    pastime = f["pastime"]
    return [
        QAItem(
            question=f"Who could not fall asleep right away in {place.label}?",
            answer=f"{child.id} could not fall asleep right away because {sibling.id}'s snore kept drifting through the room.",
        ),
        QAItem(
            question=f"What pastime did {child.id} remember in the flashback?",
            answer=f"{child.id} remembered {pastime.label}. Earlier, {child.id} had been {pastime.verb}.",
        ),
        QAItem(
            question=f"How did the flashback help {child.id} at bedtime?",
            answer=f"The flashback reminded {child.id} of a happy moment, so the snore felt smaller and bedtime felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a snore?",
            answer="A snore is a loud or sleepy sound someone makes while breathing in sleep.",
        ),
        QAItem(
            question="What is a pastime?",
            answer="A pastime is a pleasant thing someone likes to do for fun or rest, like reading or drawing.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that briefly goes back to something that happened earlier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.child, world.sibling]:
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id:10} meters={meters} memes={memes}")
    lines.append(f"  place={world.place.label}")
    lines.append(f"  pastime={world.pastime.label}")
    return "\n".join(lines)


ASP_RULES = r"""
snore_present :- snore(sibling).
flashback_used :- flashback.
valid_story :- snore_present, flashback_used, pastime(_).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("snore", "sibling"),
        asp.fact("flashback"),
    ]
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid in PASTIMES:
        lines.append(asp.fact("pastime", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    py_ok = True
    if ok == py_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


CURATED = [
    StoryParams(place="bedroom", pastime="drawing", child_name="Mina", sibling_name="Pip"),
    StoryParams(place="nursery", pastime="reading", child_name="Nora", sibling_name="Milo"),
    StoryParams(place="sleepy_room", pastime="puzzles", child_name="Ivy", sibling_name="June"),
]


def explain_rejection() -> str:
    return "(No story: the bedtime setup needs both a snore and a pastime with a flashback.)"


def asp_valid() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    return [sym.name for sym in model if sym.name == "valid_story"]


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} compatible bedtime story pattern(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.sibling_name}: {p.pastime} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
