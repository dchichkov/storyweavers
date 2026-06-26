#!/usr/bin/env python3
"""
A small mystery storyworld about a missing salami snack, with foreshadowing
and a moral-value turn.
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
# Story model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    kept_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    light: str = "soft morning light"
    afford: set[str] = field(default_factory=lambda: {"snack", "hide", "search"})


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    caregiver: str
    snack: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.trace_notes: list[str] = []

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", light="soft morning light"),
    "pantry": Setting(place="the pantry", light="a dim yellow bulb"),
    "deli": Setting(place="the little deli", light="bright glass-case light"),
    "picnic": Setting(place="the picnic table", light="warm sunlight"),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Ivy", "Zoe"],
    "boy": ["Eli", "Theo", "Finn", "Ben", "Noah"],
}

CAREGIVERS = ["mother", "father", "grandma", "grandpa"]

SALAMI_VARIANTS = {
    "salami": {
        "label": "salami",
        "phrase": "a thick salami sandwich",
        "mystery_clue": "a red grease mark",
        "hide_place": "under the cloth napkin",
        "reason": "wanted to save it for later",
        "moral": "It is kind to ask before taking food that belongs to someone else.",
    },
    "salami_slices": {
        "label": "salami slices",
        "phrase": "a neat pile of salami slices",
        "mystery_clue": "a shiny round stain",
        "hide_place": "behind the juice box",
        "reason": "wanted to make the tray look secret",
        "moral": "Even small choices matter when you share food.",
    },
}

PLACES = ["kitchen", "pantry", "deli", "picnic"]


# ---------------------------------------------------------------------------
# Reasoning / state transitions
# ---------------------------------------------------------------------------

def mystery_risk(place: str, snack_key: str) -> bool:
    return place in {"kitchen", "pantry", "deli", "picnic"} and snack_key in SALAMI_VARIANTS


def explain_invalid(place: str, snack_key: str) -> str:
    return f"(No story: the mystery setup does not support {snack_key!r} at {place!r}.)"


def _foreshadow(world: World, child: Entity, snack: Entity) -> None:
    clue = world.facts["clue"]
    world.say(
        f"In the {world.setting.place.removeprefix('the ')}, {child.id} noticed {clue} near the table."
    )
    world.say(
        f"{child.pronoun().capitalize()} did not know what it meant yet, but it looked important."
    )


def _disappear(world: World, child: Entity, snack: Entity) -> None:
    if ("disappear", snack.id) in world.fired:
        return
    world.fired.add(("disappear", snack.id))
    snack.hidden = True
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"Then the {snack.label} was gone.")
    world.say(f"{child.id} looked around and felt a little worried.")


def _search(world: World, child: Entity, caregiver: Entity, snack: Entity) -> None:
    if ("search", snack.id) in world.fired:
        return
    world.fired.add(("search", snack.id))
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} and {caregiver.id} searched the room carefully, following the small clue."
    )
    world.say(f"They looked behind things, under things, and even inside a napkin fold.")


def _reveal(world: World, child: Entity, caregiver: Entity, snack: Entity) -> None:
    if ("reveal", snack.id) in world.fired:
        return
    world.fired.add(("reveal", snack.id))
    snack.hidden = False
    world.say(
        f"At last, they found the {snack.label} in {world.facts['hide_place']}."
    )


def _moral_turn(world: World, child: Entity, caregiver: Entity, snack: Entity) -> None:
    if ("moral", snack.id) in world.fired:
        return
    world.fired.add(("moral", snack.id))
    child.memes["regret"] = child.memes.get("regret", 0) + 1
    child.memes["respect"] = child.memes.get("respect", 0) + 1
    world.say(
        f"{child.id} admitted the truth: {world.facts['reason']}."
    )
    world.say(
        f"{caregiver.id} stayed calm and explained that {world.facts['moral']}"
    )
    world.say(
        f"{child.id} promised to ask first next time, and the mystery finally felt solved."
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, name: str, gender: str, caregiver_type: str, snack_key: str) -> World:
    cfg = SALAMI_VARIANTS[snack_key]
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    caregiver = world.add(Entity(id=caregiver_type.capitalize(), kind="character", type=caregiver_type))
    snack = world.add(Entity(
        id="snack",
        label=cfg["label"],
        type=cfg["label"],
        owner=caregiver.id,
        kept_by=caregiver.id,
        hidden=False,
        plural=cfg["label"].endswith("s"),
    ))

    world.facts.update(
        clue=cfg["mystery_clue"],
        hide_place=cfg["hide_place"],
        reason=cfg["reason"],
        moral=cfg["moral"],
    )

    # Act 1: setup and foreshadowing.
    world.say(
        f"{child.id} was a curious little {gender} who loved the smell of lunch time in {setting.place}."
    )
    world.say(
        f"That day, {caregiver.id} had brought {snack.label} from the deli."
    )
    world.say(
        f"It looked like {cfg['phrase']}, and {child.id} kept sneaking glances at it."
    )
    _foreshadow(world, child, snack)

    # Act 2: the mystery.
    world.para()
    _disappear(world, child, snack)
    _search(world, child, caregiver, snack)

    # Act 3: reveal and moral value.
    world.para()
    _reveal(world, child, caregiver, snack)
    _moral_turn(world, child, caregiver, snack)

    world.facts.update(child=child, caregiver=caregiver, snack=snack, setting=setting, snack_key=snack_key)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caregiver: Entity = f["caregiver"]  # type: ignore[assignment]
    snack: Entity = f["snack"]  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a young child that includes "{snack.label}" and a clue.',
        f"Tell a gentle story where {child.id} notices something missing in {world.setting.place} and {caregiver.id} helps solve it.",
        f"Write a story with foreshadowing and a moral value lesson about {snack.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    caregiver: Entity = f["caregiver"]  # type: ignore[assignment]
    snack: Entity = f["snack"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What clue did {child.id} notice before the {snack.label} went missing?",
            answer=f"{child.id} noticed {f['clue']} near the table. That was a small foreshadowing clue.",
        ),
        QAItem(
            question=f"Where did {child.id} and {caregiver.id} find the {snack.label}?",
            answer=f"They found it in {f['hide_place']}. That solved the mystery.",
        ),
        QAItem(
            question=f"What did {child.id} learn at the end of the story?",
            answer=f"{child.id} learned that {f['moral']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is salami?",
            answer="Salami is a kind of cured meat that people often put in sandwiches or serve in slices.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small clue early on that helps the reader guess what may happen later.",
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is a lesson about kindness, honesty, sharing, or another good way to behave.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_supported(P) :- setting(P).
snack_supported(S) :- snack(S), salami(S).
valid_story(P, S) :- place_supported(P), snack_supported(S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for sid in SALAMI_VARIANTS:
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("salami", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(p, s) for p in SETTINGS for s in SALAMI_VARIANTS if mystery_risk(p, s)}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# CLI / output
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with salami, foreshadowing, and a moral lesson.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--snack", choices=SALAMI_VARIANTS)
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
    place = args.place or rng.choice(PLACES)
    snack = args.snack or "salami"
    if not mystery_risk(place, snack):
        raise StoryError(explain_invalid(place, snack))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    return StoryParams(place=place, name=name, gender=gender, caregiver=caregiver, snack=snack)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.caregiver, params.snack)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
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


CURATED = [
    StoryParams(place="kitchen", name="Mina", gender="girl", caregiver="mother", snack="salami"),
    StoryParams(place="pantry", name="Eli", gender="boy", caregiver="father", snack="salami"),
    StoryParams(place="deli", name="Nora", gender="girl", caregiver="grandma", snack="salami_slices"),
    StoryParams(place="picnic", name="Theo", gender="boy", caregiver="grandpa", snack="salami_slices"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for place, snack in stories:
            print(f"  {place:8} {snack}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
