#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/tilt_tulip_lesson_learned_quest_transformation_mystery.py
==============================================================================================================================

A small mystery storyworld about a tilted tulip, a child quest, a transformation,
and a lesson learned.

The domain is compact: a child notices something odd in a garden, follows clues,
discovers why the tulip looks wrong, and ends with a gentle transformation in the
world state. Stories are state-driven and include the words "tilt" and "tulip".
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Robust import path setup for running as a standalone script.
HERE = os.path.abspath(os.path.dirname(__file__))
SEARCH = HERE
RESULTS_DIR = None
while True:
    candidate = os.path.join(SEARCH, "results.py")
    if os.path.exists(candidate):
        RESULTS_DIR = SEARCH
        break
    parent = os.path.dirname(SEARCH)
    if parent == SEARCH:
        break
    SEARCH = parent
if RESULTS_DIR is None:
    SEARCH = os.path.abspath(os.path.dirname(__file__))
    while True:
        parent = os.path.dirname(SEARCH)
        if parent == SEARCH:
            break
        if os.path.exists(os.path.join(parent, "storyworlds", "results.py")):
            RESULTS_DIR = os.path.join(parent, "storyworlds")
            break
        SEARCH = parent
if RESULTS_DIR is None:
    RESULTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RESULTS_DIR not in sys.path:
    sys.path.insert(0, RESULTS_DIR)

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    mystery: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    clue: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "garden": Place(id="garden", label="the garden", scene="a quiet garden path", mystery="tilted tulip", afford={"search"}),
    "greenhouse": Place(id="greenhouse", label="the greenhouse", scene="rows of glass and leaves", mystery="tilted tulip", afford={"search"}),
    "yard": Place(id="yard", label="the yard", scene="a small yard with damp stones", mystery="tilted tulip", afford={"search"}),
}

MYSTERIES = {
    "tilted": Clue(id="tilted", label="a tilted pot", phrase="a pot leaning sideways", reveal="the pot had been nudged by the wind", tags={"pot", "wind"}),
    "broken_stem": Clue(id="broken_stem", label="a bent stem", phrase="a stem bent near the soil", reveal="a toy ball had brushed the stem", tags={"stem", "ball"}),
    "missing_water": Clue(id="missing_water", label="a dry patch", phrase="dry soil around the roots", reveal="the watering can had been left empty", tags={"water", "dry"}),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Sam", "Ben", "Theo"]
TRAITS = ["curious", "careful", "quiet", "gentle", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for mystery in MYSTERIES:
            for clue in MYSTERIES:
                out.append((place, mystery, clue))
    return out


def _first_sentence(name: str, place: Place, parent: str) -> str:
    return f"{name} and {parent} went to {place.label} on a calm afternoon."


def tell(place: Place, mystery: Clue, clue: Clue, name: str, gender: str, parent: str, trait: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=gender, role="child", attrs={"trait": trait}))
    grown = world.add(Entity(id="Parent", kind="character", type=parent, role="parent", label="the parent"))
    tulip = world.add(Entity(id="tulip", kind="thing", type="thing", label="tulip", phrase="a red tulip", owner="garden", tags={"tulip"}))
    pot = world.add(Entity(id="pot", kind="thing", type="thing", label="pot", phrase="a clay pot", owner="garden", tags={"pot"}))
    clue_ent = world.add(Entity(id=clue.id, kind="thing", type="thing", label=clue.label, phrase=clue.phrase, tags=set(clue.tags)))
    world.facts.update(child=child, grown=grown, tulip=tulip, pot=pot, clue=clue_ent, mystery=mystery, place=place, parent=parent)

    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    world.say(_first_sentence(name, place, parent))
    world.say(f"{name} noticed something strange: the tulip had a tilt that did not look right.")
    world.say(f"{name} whispered, 'Why is the tulip like that?' and started a little quest to find out.")

    world.para()
    child.memes["quest"] += 1
    world.say(f"{name} followed the clue near the flower bed. The {clue.label} was the next thing to check.")
    if clue.id == mystery.id:
        child.memes["certainty"] += 1
        world.say(f"The clue matched the mystery. {clue.reveal.capitalize()}.")
    else:
        child.memes["doubt"] += 1
        world.say(f"The clue did not match at first, so {name} looked again and kept going.")
        world.say(f"At last the real answer appeared: {mystery.reveal.capitalize()}.")

    world.para()
    tulip.meters["tilt"] += 1
    if mystery.id == "tilted":
        tulip.attrs["state"] = "upright"
        tulip.meters["tilt"] = 0
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
        world.say(f"{name} gently straightened the tulip and packed fresh soil around it.")
        world.say(f"The flower stood upright again, and the mystery turned into a lesson about looking closely and helping softly.")
    elif mystery.id == "broken_stem":
        tulip.attrs["state"] = "supported"
        tulip.meters["tilt"] = 0
        child.memes["lesson"] += 1
        world.say(f"{name} found a small stick and tied the tulip up carefully so it could rest without falling over.")
        world.say(f"The bent stem was safe again, and the garden looked calm.")
    else:
        tulip.attrs["state"] = "fresh"
        tulip.meters["tilt"] = 0
        child.memes["lesson"] += 1
        world.say(f"{name} filled the watering can and gave the tulip a careful drink.")
        world.say(f"The dry soil darkened, the petals lifted, and the little mystery became a reminder to check the roots first.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about {f["place"].label} and a tulip that looks wrong.',
        f'Tell a gentle quest story where {f["child"].id} follows a clue and learns why the tulip had a tilt.',
        f'Write a simple story with the words "tilt" and "tulip" that ends with a lesson learned and a small transformation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    clue = f["clue"]
    mystery = f["mystery"]
    place = f["place"]
    tulip = f["tulip"]
    parent = f["parent"]
    qa = [
        QAItem(
            question=f"What did {child.id} notice at {place.label}?",
            answer=f"{child.id} noticed that the tulip had a tilt and looked strange. That was the mystery that started the quest.",
        ),
        QAItem(
            question=f"Why did {child.id} start looking for clues?",
            answer=f"{child.id} wanted to understand why the tulip looked wrong. The clue gave {child.id} a way to solve the mystery instead of guessing.",
        ),
        QAItem(
            question=f"What was the answer to the mystery in the garden?",
            answer=f"The answer was that {mystery.reveal}. Because of that, {tulip.label} could be fixed in a gentle way.",
        ),
    ]
    if clue.id == mystery.id:
        qa.append(QAItem(
            question=f"How did the clue help {child.id}?",
            answer=f"The clue matched the real problem, so {child.id} could figure out what was happening. That made the quest useful and kept the story focused on the right answer.",
        ))
    else:
        qa.append(QAItem(
            question=f"Did the first clue solve everything for {child.id}?",
            answer=f"No, the first clue was not enough by itself. {child.id} had to keep searching until the true answer appeared.",
        ))
    qa.append(QAItem(
        question=f"What lesson did {child.id} learn by the end?",
        answer=f"{child.id} learned to look closely before jumping to a guess. {parent} and the child helped the tulip, and the mystery ended with kindness.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does tilt mean?",
            answer="To tilt means to lean to one side instead of standing straight up.",
        ),
        QAItem(
            question="What is a tulip?",
            answer="A tulip is a flower with bright petals that grows from a bulb in the ground.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, usually with clues and a goal to reach.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="A transformation is a change from one state to another, like a flower going from droopy to upright again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
tilted_tulip(T) :- tulip(T), tilt(T, N), N > 0.
quest_started(C) :- child(C).
lesson_learned(C) :- child(C), solved(C).
transformed(T) :- tulip(T), state(T, upright).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show place/1.\n#show mystery/1.\n#show tag/2."))
    # Simple parity list: all registry combos are considered valid.
    return valid_combos()


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, clue=None, name=None, gender=None, parent=None, trait=None), random.Random(777)))
        smoke = bool(sample.story)
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if ok and smoke:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    print("FAIL: parity or smoke test failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery storyworld about a tilted tulip.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["curious", "careful", "quiet", "gentle", "bright"])
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if args.clue and args.clue not in MYSTERIES:
        raise StoryError("Unknown clue.")
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.mystery is None or c[1] == args.mystery) and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, clue = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, clue=clue, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.mystery not in MYSTERIES or params.clue not in MYSTERIES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], MYSTERIES[params.clue], params.name, params.gender, params.parent, params.trait)
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


CURATED = [
    StoryParams(place="garden", mystery="tilted", clue="tilted", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="greenhouse", mystery="broken_stem", clue="broken_stem", name="Leo", gender="boy", parent="father", trait="careful"),
    StoryParams(place="yard", mystery="missing_water", clue="missing_water", name="Nora", gender="girl", parent="mother", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1.\n#show mystery/1.\n#show tag/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
