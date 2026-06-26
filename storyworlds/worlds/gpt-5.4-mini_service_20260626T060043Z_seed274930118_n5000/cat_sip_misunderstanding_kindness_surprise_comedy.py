#!/usr/bin/env python3
"""
A small standalone storyworld for a comedy about a cat, a sip, a misunderstanding,
kindness, and surprise.

Premise:
A curious cat wants a sip from a cup, but the human thinks the cat is causing
trouble. A gentle misunderstanding grows into a funny pause, then kindness fixes
it, and the story ends with a surprising, happy turn.

The world is intentionally small and constraint-checked:
- the cat must be able to want a sip from something
- the misunderstanding must be plausible
- kindness must be able to resolve it
- surprise must fit the final beat

The script supports text, JSON, QA, trace, and an inline ASP twin for parity checks.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    cat_name: str
    human_name: str
    human_type: str
    object_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", affords={"sip"}),
    "window": Setting(place="the sunny window nook", affords={"sip"}),
    "porch": Setting(place="the porch", affords={"sip"}),
}

OBJECTS = {
    "milk": ObjectCfg(label="milk", phrase="a small glass of milk", region="mouth"),
    "water": ObjectCfg(label="water", phrase="a tiny cup of water", region="mouth"),
    "soup": ObjectCfg(label="soup", phrase="a warm bowl of soup", region="mouth"),
}

CAT_NAMES = ["Milo", "Pip", "Nori", "Coco", "Mochi", "Luna", "Socks", "Tuna"]
HUMAN_NAMES = ["Ada", "Bea", "Maya", "Noah", "Iris", "Owen"]
HUMAN_TYPES = ["mother", "father", "girl", "boy"]
PLACES = list(SETTINGS.keys())


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show kind_turn/2.
#show surprising/2.

valid(P,O) :- place(P), object(O), place_affords(P,sip), sip_object(O).
kind_turn(P,O) :- valid(P,O).
surprising(P,O) :- valid(P,O), surprise_capable(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("sip_object", oid))
        lines.append(asp.fact("surprise_capable", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, o) for p in SETTINGS for o in OBJECTS if is_valid_combo(p, o))
    cl = asp_valid()
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def is_valid_combo(place: str, obj: str) -> bool:
    return place in SETTINGS and obj in OBJECTS and "sip" in SETTINGS[place].affords


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: {place} does not support a sip story with {obj}.)"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    cat = world.add(Entity(id=params.cat_name, kind="character", type="cat", label=params.cat_name))
    human = world.add(Entity(id=params.human_name, kind="character", type=params.human_type, label=params.human_name))
    obj_cfg = OBJECTS[params.object_name]
    cup = world.add(Entity(
        id=obj_cfg.label,
        type=obj_cfg.label,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=human.id,
        caretaker=human.id,
    ))

    # Setup
    world.say(f"{cat.id} was a curious cat who loved tiny adventures.")
    world.say(f"One day, {human.id} had {cup.phrase} at {setting.place}.")
    world.say(f"{cat.id} stared at {cup.label} and hoped for a little sip.")

    # Conflict: misunderstanding
    world.para()
    world.say(f"When {cat.id} leaned closer, {human.id} thought {cat.id} was about to make a mess.")
    world.say(f'"No, no," {human.id} said, scooping {cat.id} up gently. "That is not for paws."')
    cat.memes["confused"] = cat.memes.get("confused", 0.0) + 1
    human.memes["worry"] = human.memes.get("worry", 0.0) + 1
    world.facts["misunderstanding"] = True

    # Turn: kindness
    world.para()
    world.say(f"{cat.id} blinked, then gave the saddest tiny look.")
    world.say(f"{human.id} paused, smiled, and said, \"Oh! You want a sip, not a steal.\"")
    world.say(f"With a laugh, {human.id} poured a little into a clean dish just for {cat.id}.")
    cat.memes["joy"] = cat.memes.get("joy", 0.0) + 1
    human.memes["kindness"] = human.memes.get("kindness", 0.0) + 1
    world.facts["kindness"] = True

    # Resolution: surprise/comedy
    world.para()
    world.say(f"{cat.id} took the sip so daintily that even the spoon seemed impressed.")
    world.say(f"Then {cat.id} sneezed one tiny, dramatic sneeze and startled a napkin right off the table.")
    world.say(f"{human.id} laughed so hard that the whole room felt bright and silly.")
    world.say(f"In the end, {cat.id} got a sip, {human.id} got a grin, and the napkin flew like it wanted applause.")
    cat.memes["surprise"] = cat.memes.get("surprise", 0.0) + 1
    world.facts["surprise"] = True

    world.facts.update(
        cat=cat,
        human=human,
        cup=cup,
        setting=setting,
        object_cfg=obj_cfg,
        place=params.place,
        cat_name=params.cat_name,
        human_name=params.human_name,
        human_type=params.human_type,
        object_name=params.object_name,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a child about a cat named {f["cat_name"]} and a sip at {f["place"]}.',
        f'Tell a funny story where {f["human_name"]} misunderstands what {f["cat_name"]} wants, then shows kindness.',
        f'Write a gentle, silly story that ends with a surprising little moment after a cat gets a sip.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cat = f["cat"]
    human = f["human"]
    cup = f["cup"]
    return [
        QAItem(
            question=f"What did {cat.id} want at {f['place']}?",
            answer=f"{cat.id} wanted a little sip from {cup.label}.",
        ),
        QAItem(
            question=f"Why did {human.id} first stop {cat.id}?",
            answer=f"{human.id} misunderstood and thought {cat.id} was about to make a mess.",
        ),
        QAItem(
            question=f"How did {human.id} show kindness?",
            answer=f"{human.id} smiled, understood the mistake, and gave {cat.id} a tiny dish with a sip.",
        ),
        QAItem(
            question=f"What was surprising at the end?",
            answer=f"{cat.id} sneezed a tiny sneeze, and the napkin flew right off the table.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sip?",
            answer="A sip is a very small drink taken with care.",
        ),
        QAItem(
            question="Why can a misunderstanding be funny in a story?",
            answer="A misunderstanding can be funny when someone guesses wrong, then the truth makes everything make sense in a kind way.",
        ),
        QAItem(
            question="What does kindness look like?",
            answer="Kindness looks like being gentle, listening, and helping someone after a mistake.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes the moment and makes it feel fresh or funny.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small comedy storyworld about a cat, a sip, kindness, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cat-name", dest="cat_name")
    ap.add_argument("--human-name", dest="human_name")
    ap.add_argument("--human-type", dest="human_type", choices=HUMAN_TYPES)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    obj = args.object_name or rng.choice(list(OBJECTS))
    if not is_valid_combo(place, obj):
        raise StoryError(explain_rejection(place, obj))
    cat_name = args.cat_name or rng.choice(CAT_NAMES)
    human_name = args.human_name or rng.choice(HUMAN_NAMES)
    human_type = args.human_type or rng.choice(HUMAN_TYPES)
    return StoryParams(
        place=place,
        cat_name=cat_name,
        human_name=human_name,
        human_type=human_type,
        object_name=obj,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2.\n#show kind_turn/2.\n#show surprising/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2.\n#show kind_turn/2.\n#show surprising/2."))
        print("valid:", sorted(set(asp.atoms(model, "valid"))))
        print("kind_turn:", sorted(set(asp.atoms(model, "kind_turn"))))
        print("surprising:", sorted(set(asp.atoms(model, "surprising"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="kitchen", cat_name="Milo", human_name="Ada", human_type="mother", object_name="milk"),
            StoryParams(place="window", cat_name="Pip", human_name="Noah", human_type="father", object_name="water"),
            StoryParams(place="porch", cat_name="Coco", human_name="Iris", human_type="girl", object_name="soup"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
