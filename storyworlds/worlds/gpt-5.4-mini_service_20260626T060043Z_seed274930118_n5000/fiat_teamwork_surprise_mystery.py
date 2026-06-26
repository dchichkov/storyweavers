#!/usr/bin/env python3
"""
A standalone storyworld about a small mystery, a surprising clue, and a team
working together to solve it.

The seed word is "fiat", so the world centers on a small fiat car that has
vanished from a driveway and is found through careful teamwork.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    weather: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    helper: str
    name: str
    parent: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "driveway": "the driveway",
    "garage": "the garage",
    "garden": "the garden",
    "culdesac": "the little cul-de-sac",
    "shed": "the shed",
}

CLUES = {
    "mud": {
        "label": "muddy tire track",
        "phrase": "a muddy tire track",
        "smudge": "mud",
        "hiding": "behind the flower pots",
        "direction": "toward the shed",
    },
    "bell": {
        "label": "tiny bell",
        "phrase": "a tiny bell that jingled softly",
        "smudge": "shine",
        "hiding": "under a cloth",
        "direction": "near the garage door",
    },
    "string": {
        "label": "red string",
        "phrase": "a red string tied in a careful knot",
        "smudge": "dust",
        "hiding": "by the mailbox",
        "direction": "under a bench",
    },
}

HELPERS = {
    "flashlight": {
        "label": "flashlight",
        "phrase": "a small flashlight with a bright beam",
        "use": "shine the beam into dark corners",
    },
    "map": {
        "label": "map",
        "phrase": "a hand-drawn map",
        "use": "look at the marks and follow the arrows",
    },
    "magnifier": {
        "label": "magnifier",
        "phrase": "a little magnifier",
        "use": "study the clue closely",
    },
}

NAMES = ["Mina", "Leo", "Tia", "Ben", "Nora", "Sam", "Ivy", "Owen"]
PARENTS = ["mother", "father"]
TRAITS = ["curious", "careful", "brave", "quiet", "eager"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
class MysteryWorld(World):
    pass


def build_world(params: StoryParams) -> MysteryWorld:
    world = MysteryWorld(place=PLACES[params.place], weather="soft evening drizzle")
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Tia", "Nora", "Ivy"} else "boy"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    car = world.add(Entity(id="fiat", type="car", label="fiat", phrase="a little red fiat"))
    clue = world.add(Entity(id="clue", type="clue", label=CLUES[params.clue]["label"], phrase=CLUES[params.clue]["phrase"], owner=child.id))
    helper = world.add(Entity(id="helper", type="tool", label=HELPERS[params.helper]["label"], phrase=HELPERS[params.helper]["phrase"], owner=child.id))
    child.memes.update(curiosity=1.0, worry=0.0, surprise=0.0, teamwork=0.0)
    parent.memes.update(worry=1.0, teamwork=0.0)
    car.meters.update(hidden=1.0)
    clue.meters.update(found=0.0)
    helper.meters.update(ready=1.0)

    world.facts.update(child=child, parent=parent, car=car, clue=clue, helper=helper, params=params)
    return world


def tell(world: MysteryWorld) -> None:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    car: Entity = f["car"]
    clue: Entity = f["clue"]
    helper: Entity = f["helper"]
    clue_cfg = CLUES[f["params"].clue]
    helper_cfg = HELPERS[f["params"].helper]

    world.say(f"{child.id} and {parent.label} lived near {world.place}, where a little red fiat was usually parked.")
    world.say(f"One evening, the fiat was gone.")
    world.say(f"{child.id} felt a prickly mystery in the air, and {parent.pronoun('possessive')} brow wrinkled with worry.")

    world.para()
    child.memes["curiosity"] += 1
    parent.memes["worry"] += 1
    world.say(f"{child.id} spotted {clue.phrase} {clue_cfg['hiding']}.")
    world.say(f"{child.id} held up {helper.phrase} so they could {helper_cfg['use']}.")
    child.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1

    if f["params"].clue == "bell":
        child.memes["surprise"] += 1
        world.say("The tiny bell gave a surprise jingle when the beam touched it.")
    elif f["params"].clue == "mud":
        child.memes["surprise"] += 1
        world.say("The muddy track pointed in a direction nobody had expected.")
    else:
        child.memes["surprise"] += 1
        world.say("The red string looked ordinary, but the neat knot was too careful to ignore.")

    world.para()
    world.say(f"{child.id} and {parent.label} followed the clue together.")
    world.say(f"They searched near the garage, then the garden, then the shed.")
    world.say(f"At last, behind a quiet door, they found the fiat tucked safely away.")

    world.para()
    car.meters["hidden"] = 0.0
    car.meters["found"] = 1.0
    child.memes["joy"] = 1.0
    parent.memes["relief"] = 1.0
    world.say(f"It had not been stolen at all; it had rolled into a sheltered spot during the drizzle.")
    world.say(f"{child.id} laughed in surprise, and {parent.label} laughed too.")
    world.say(f"With teamwork and a careful clue, the little fiat was back where it belonged.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: MysteryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about a missing fiat, a surprising clue, and teamwork.',
        f"Tell a gentle story where {f['child'].id} and {f['parent'].label} search for a lost fiat by using a {f['helper'].label}.",
        f'Write a simple mystery that includes the word "fiat" and ends with the car being found through teamwork.',
    ]


def story_qa(world: MysteryWorld) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    helper: Entity = f["helper"]
    clue: Entity = f["clue"]
    return [
        QAItem(
            question=f"What was missing from the driveway at the start of the story?",
            answer="The little red fiat was missing from the driveway.",
        ),
        QAItem(
            question=f"Who looked for the fiat together?",
            answer=f"{child.id} and {parent.label} looked for the fiat together.",
        ),
        QAItem(
            question=f"What helpful tool did they use to follow the clue?",
            answer=f"They used {helper.phrase} so they could find the clue.",
        ),
        QAItem(
            question=f"What surprising thing did they learn in the end?",
            answer="They learned that the fiat had not been stolen; it had only rolled into a sheltered spot.",
        ),
        QAItem(
            question=f"What clue helped them solve the mystery?",
            answer=f"The clue was {clue.phrase}.",
        ),
    ]


def world_knowledge_qa(world: MysteryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight is for shining light into dark places so people can see better.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a sign or bit of information that helps someone solve a mystery.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people work together to do something that is easier or better with help.",
        ),
        QAItem(
            question="What is surprise?",
            answer="Surprise is the feeling you get when something happens that you did not expect.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(X) :- child_name(X).
parent(X) :- parent_type(X).
tool(X) :- helper_type(X).
clue(X) :- clue_type(X).
car(fiat).

teamwork_needed :- missing(fiat), clue(C), tool(T).
surprise_event :- found(fiat), missing(fiat), clue(C).

valid_story(Place, Clue, Helper) :- place(Place), clue_type(Clue), helper_type(Helper).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue_type", cid))
    for hid in HELPERS:
        lines.append(asp.fact("helper_type", hid))
    lines.append(asp.fact("missing", "fiat"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, c, h) for p in PLACES for c in CLUES for h in HELPERS}
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP-only:", sorted(asp_set - py_set))
    print("Python-only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, c, h) for p in PLACES for c in CLUES for h in HELPERS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.clue and args.clue not in CLUES:
        raise StoryError("Unknown clue.")
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")

    place = args.place or rng.choice(list(PLACES))
    clue = args.clue or rng.choice(list(CLUES))
    helper = args.helper or rng.choice(list(HELPERS))
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(place=place, clue=clue, helper=helper, name=name, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: MysteryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with teamwork and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in PLACES:
            for clue in CLUES:
                for helper in HELPERS:
                    params = StoryParams(place=place, clue=clue, helper=helper, name=NAMES[0], parent=PARENTS[0])
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(100, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
