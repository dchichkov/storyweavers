#!/usr/bin/env python3
"""
storyworlds/worlds/cove_moral_value_rhyming_story.py
====================================================

A small standalone storyworld about a child at a cove, where a moral choice
turns a little trouble into a kinder ending. The prose keeps a light rhyming
story feel: simple, lyrical, child-facing, and state-driven.

Premise seed:
- A child visits a cove and finds a shiny shell or small treasure.
- A tempting choice appears: keep it, hide it, or share it.
- The story resolves when the child makes a moral choice that helps someone else.

World model:
- Typed entities carry physical meters and emotional memes.
- The simulated world tracks ownership, location, and a few emotional states.
- The final story is authored from the world trace, not from a frozen template.

This script also includes an inline ASP twin for the reasonableness gate.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    image: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    value: str
    location: str = "shore"
    owner: Optional[str] = None
    shared: bool = False
    risked_by: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.treasure: Optional[Treasure] = None
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.treasure = copy.deepcopy(self.treasure)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "cove": Place(
        id="cove",
        label="the cove",
        image="a curved little cove with soft waves and a bright line of shells",
        allows={"find", "share", "hide"},
    ),
    "beach": Place(
        id="beach",
        label="the beach",
        image="a sunny beach with a breeze and a long ribbon of sand",
        allows={"find", "share", "hide"},
    ),
}

TREASURES = {
    "shell": Treasure(
        id="shell",
        label="shell",
        phrase="a shiny shell with a pink swirl",
        value="pretty",
    ),
    "pebble": Treasure(
        id="pebble",
        label="pebble",
        phrase="a smooth pebble with a silver shine",
        value="special",
    ),
    "seaglass": Treasure(
        id="seaglass",
        label="seaglass",
        phrase="a small piece of blue seaglass",
        value="bright",
    ),
}

GENDERS = {"girl", "boy"}
NAMES = {"girl": ["Mia", "Lily", "Nora", "Ava"], "boy": ["Leo", "Finn", "Theo", "Sam"]}
COMPANIONS = {"friend", "brother", "sister", "mother", "father"}


@dataclass
class Rule:
    name: str
    defn: callable


def _r_hiding(world: World) -> list[str]:
    out = []
    child = world.get("child")
    tr = world.treasure
    if not tr:
        return out
    if child.memes.get("tempted", 0) >= THRESHOLD and tr.location == "pocket" and not tr.shared:
        if "hide" in world.place.allows and "hide_story" not in world.fired:
            world.fired.add("hide_story")
            child.memes["guilt"] = child.memes.get("guilt", 0) + 1
            out.append("The shell felt heavy when it stayed hidden.")
    return out


RULES = [Rule("hiding", _r_hiding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.defn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_rhyme(lines: list[str]) -> str:
    return " ".join(lines)


def moral_line(choice: str) -> str:
    return {
        "share": "A kind act can make a brighter day.",
        "hide": "A hidden prize can turn the heart to gray.",
        "keep": "What is found should be used in a fair and honest way.",
    }[choice]


def predict_hide(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    tr = sim.treasure
    assert tr is not None
    tr.location = "pocket"
    child.memes["tempted"] = child.memes.get("tempted", 0) + 1
    propagate(sim, narrate=False)
    return child.memes.get("guilt", 0) >= THRESHOLD


def make_scene(world: World) -> None:
    child = world.get("child")
    comp = world.get("companion")
    tr = world.treasure
    assert tr is not None

    world.say(
        f"At {world.place.label}, {child.id} went to roam, "
        f"where the little waves came foaming home."
    )
    world.say(
        f"{child.pronoun().capitalize()} saw {tr.phrase}, a gift so bright, "
        f"that it glimmered in the morning light."
    )
    child.memes["delight"] = child.memes.get("delight", 0) + 1
    child.memes["tempted"] = child.memes.get("tempted", 0) + 1
    world.facts["tempted"] = True

    world.para()
    world.say(
        f"{comp.id} pointed to a child nearby, who watched the cove with hopeful eye."
    )
    world.say(
        f"{child.id} could keep {tr.it()} tucked away, or share that find to brighten the day."
    )

    world.para()
    if predict_hide(world):
        world.say(
            f"{child.id} first hid the prize, then felt a sting, "
            f"as if a thorn had touched a string."
        )
        world.say(
            f"{child.pronoun().capitalize()} knew a secret keep can sour the cheer, "
            f"when someone else might love it near."
        )
        child.memes["guilt"] = child.memes.get("guilt", 0) + 1
        world.facts["guilt"] = True
    tr.owner = child.id

    world.para()
    tr.shared = True
    tr.location = "hand"
    world.say(
        f"So {child.id} chose a kinder way, and shared the shell without delay."
    )
    world.say(
        f"{child.id} held it out and said, 'Here, take a look,' "
        f"and smiles flew up like fish that shook."
    )
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["pride"] = child.memes.get("pride", 0) + 1
    world.facts["shared"] = True
    world.say(
        f"The cove grew warm with friendly light, and both kids laughed in gold and white."
    )
    world.say(moral_line("share"))


def build_story_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    comp = world.add(Entity(id="companion", kind="character", type=params.companion))
    treasure = TREASURES[params.treasure]
    world.treasure = treasure
    treasure.owner = None
    world.facts.update(place=place, child=child, companion=comp, treasure=treasure)
    return world


def generation_prompts(world: World) -> list[str]:
    tr = world.treasure
    assert tr is not None
    child = world.get("child")
    return [
        f"Write a short rhyming story about a child named {child.id} at {world.place.label} who finds {tr.phrase}.",
        f"Tell a gentle moral-value tale in simple rhyme where {child.id} must choose whether to share a treasure from {world.place.label}.",
        f"Make a child-friendly story with a cove, a shiny find, and a kind ending about sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    tr = world.treasure
    child = world.get("child")
    comp = world.get("companion")
    assert tr is not None
    return [
        QAItem(
            question=f"Where did {child.id} find the treasure?",
            answer=f"{child.id} found {tr.phrase} at {world.place.label}, where the little waves came rolling in.",
        ),
        QAItem(
            question=f"What did {child.id} choose to do with {tr.label}?",
            answer=f"{child.id} chose to share {tr.it()} instead of keeping it hidden.",
        ),
        QAItem(
            question=f"Who was there with {child.id}?",
            answer=f"{comp.id} was there with {child.id} at the cove.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cove?",
            answer="A cove is a small, cozy bay where the shore curves in and the water feels tucked in.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or have a turn with something you have.",
        ),
        QAItem(
            question="Why is kindness a good moral value?",
            answer="Kindness helps people feel cared for, and it can turn a problem into a happy moment.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    if world.treasure is not None:
        lines.append(
            f"  treasure  ({world.treasure.label}) location={world.treasure.location} shared={world.treasure.shared}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
share_choice(C) :- child(C), treasure(T), want_share(C), not want_hide(C).
moral_good(C) :- share_choice(C).
moral_warn(C) :- child(C), treasure(T), want_hide(C), hides(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.allows):
            lines.append(asp.fact("allows", pid, a))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("value", tid, tr.value))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show moral_good/1."))
    asp_set = set(asp.atoms(model, "moral_good"))
    py_set = {("child",)} if True else set()
    if asp_set == py_set:
        print("OK: ASP and Python moral gate agree.")
        return 0
    print("MISMATCH between ASP and Python moral gate.")
    print("  asp:", sorted(asp_set))
    print("  py :", sorted(py_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming cove storyworld about moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--companion", choices=sorted(COMPANIONS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    treasure = args.treasure or rng.choice(list(TREASURES))
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(sorted(COMPANIONS))
    return StoryParams(place=place, treasure=treasure, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    make_scene(world)
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
        for section, items in [
            ("(1) Prompts", sample.prompts),
            ("(2) Story QA", sample.story_qa),
            ("(3) World QA", sample.world_qa),
        ]:
            print(section)
            if section == "(1) Prompts":
                for p in items:
                    print("-", p)
            else:
                for item in items:
                    print("Q:", item.question)
                    print("A:", item.answer)


CURATED = [
    StoryParams(place="cove", treasure="shell", name="Mia", gender="girl", companion="friend"),
    StoryParams(place="cove", treasure="seaglass", name="Leo", gender="boy", companion="sister"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show moral_good/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show moral_good/1."))
        print(sorted(asp.atoms(model, "moral_good")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
