#!/usr/bin/env python3
"""
Story world: Penny, Morsel, Kindness, and a bedtime share.

A small, child-facing world in which a little character named Penny has a
tiny snack called a morsel, meets a bedtime need, and learns that kindness
grows when sharing is gentle and fair.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("comfort", 0.0)
        self.meters.setdefault("hunger", 0.0)
        self.meters.setdefault("clean", 0.0)
        self.meters.setdefault("sleepiness", 0.0)
        self.meters.setdefault("tidiness", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("hurt", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "penny"}
        male = {"boy", "father", "dad", "man"}
        if self.type.lower() in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type.lower() in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Room:
    name: str
    cozy: bool = True
    bedtime_ready: bool = True


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Parameters and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    snack: str
    child_name: str
    sibling_name: str
    caregiver: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Room(name="the bedroom", cozy=True, bedtime_ready=True),
    "nursery": Room(name="the nursery", cozy=True, bedtime_ready=True),
    "hallway": Room(name="the hallway", cozy=False, bedtime_ready=False),
}

SNACKS = {
    "cookie": {"label": "cookie", "phrase": "one tiny cookie", "crumbs": 1.0},
    "cracker": {"label": "cracker", "phrase": "a little cracker", "crumbs": 0.6},
    "berry": {"label": "berry", "phrase": "one sweet berry", "crumbs": 0.0},
    "morsel": {"label": "morsel", "phrase": "a tiny morsel", "crumbs": 0.2},
}

CHILD_NAMES = ["Penny", "Mia", "Luna", "Nora", "Lily", "Ivy", "June", "Ada"]
SIBLING_NAMES = ["Milo", "Ben", "Finn", "Toby", "Otis", "Theo", "Sam"]
CAREGIVERS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(setting: str, snack: str) -> bool:
    if setting not in SETTINGS or snack not in SNACKS:
        return False
    # Hallway is too plain to host the bedtime comfort turn.
    if setting == "hallway":
        return False
    # Kindness story needs a snack with at least a little shareability.
    return True


def valid_combos() -> list[tuple[str, str]]:
    return [(s, n) for s in SETTINGS for n in SNACKS if valid_combo(s, n)]


def explain_rejection(setting: str, snack: str) -> str:
    if setting == "hallway":
        return "(No story: the hallway is too cold and plain for this bedtime kindness tale.)"
    return "(No story: that setting and snack do not make a gentle bedtime story.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _night_need(world: World, child: Entity) -> None:
    child.meters["hunger"] += 1.0
    child.meters["sleepiness"] += 1.0
    child.memes["worry"] += 1.0
    world.say(f"{child.id} felt sleepy, but a tiny hungry feeling kept peeking in.")


def _find_morsel(world: World, child: Entity, snack: Entity) -> None:
    world.say(f"On the little table sat {snack.phrase}.")
    child.memes["joy"] += 0.5
    world.say(f"{child.id} noticed the morsel and smiled as if it were a treasure.")


def _want_to_keep(world: World, child: Entity, snack: Entity) -> None:
    child.memes["worry"] += 0.5
    world.say(f"{child.id} wanted to keep the morsel close for herself.")


def _ask_kindly(world: World, sibling: Entity, child: Entity, snack: Entity) -> None:
    sibling.memes["kindness"] += 1.0
    child.memes["worry"] += 0.5
    world.say(f"{sibling.id} asked in a soft voice, \"Could I have a bite of the morsel too?\"")


def _hesitate(world: World, child: Entity) -> None:
    child.memes["hurt"] += 0.2
    world.say(f"{child.id} paused and held the morsel a little tighter.")


def _share(world: World, child: Entity, sibling: Entity, snack: Entity) -> None:
    sig = ("share", child.id, sibling.id, snack.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    snack.shared_with.add(sibling.id)
    child.memes["kindness"] += 1.0
    sibling.memes["kindness"] += 1.0
    child.memes["joy"] += 1.0
    sibling.memes["joy"] += 1.0
    child.meters["hunger"] = max(0.0, child.meters["hunger"] - 0.4)
    sibling.meters["hunger"] = max(0.0, sibling.meters["hunger"] - 0.2)
    world.say(f"{child.id} broke the morsel in half and gave {sibling.pronoun('object')} a piece.")
    world.say(f"That made the room feel warmer, and both children looked calmer.")


def _bedtime_settle(world: World, child: Entity, sibling: Entity, caregiver: Entity) -> None:
    child.meters["comfort"] += 1.0
    sibling.meters["comfort"] += 1.0
    child.meters["sleepiness"] += 0.8
    sibling.meters["sleepiness"] += 0.8
    world.say(f"Then {caregiver.id} tucked the blankets in just right.")
    world.say(f"{child.id} and {sibling.id} snuggled down, full of kindness and ready for sleep.")


def tell(setting: Room, snack_cfg: dict, child_name: str, sibling_name: str, caregiver_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="penny", label=child_name))
    sibling = world.add(Entity(id=sibling_name, kind="character", type="child", label=sibling_name))
    caregiver = world.add(Entity(id=caregiver_type.title(), kind="character", type=caregiver_type, label=caregiver_type))
    snack = world.add(Entity(
        id=snack_cfg["label"],
        kind="thing",
        type="snack",
        label=snack_cfg["label"],
        phrase=snack_cfg["phrase"],
        owner=child.id,
        caretaker=caregiver.id,
    ))

    world.say(f"{child.id} was a little one who loved soft blankets and sleepy stories.")
    world.say(f"At the edge of bedtime, {child.id} found {snack.phrase} waiting nearby.")
    world.para()

    _night_need(world, child)
    _find_morsel(world, child, snack)
    _want_to_keep(world, child, snack)
    _ask_kindly(world, sibling, child, snack)
    _hesitate(world, child)
    _share(world, child, sibling, snack)
    _bedtime_settle(world, child, sibling, caregiver)

    world.facts.update(
        child=child,
        sibling=sibling,
        caregiver=caregiver,
        snack=snack,
        setting=setting,
        snack_cfg=snack_cfg,
        shared=bool(snack.shared_with),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack_cfg = f["snack_cfg"]
    return [
        f'Write a bedtime story for a small child about {child.id}, a {snack_cfg["label"]}, and kindness.',
        f"Tell a gentle story where {child.id} learns to share a {snack_cfg['label']} before sleep.",
        f'Write a cozy story that includes the word "{snack_cfg["label"]}" and ends with children settling down kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    caregiver = f["caregiver"]
    snack_cfg = f["snack_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who wanted to keep the {snack_cfg['label']} at first?",
            answer=f"{child.id} wanted to keep the {snack_cfg['label']} close at first because bedtime made the snack feel special.",
        ),
        QAItem(
            question=f"Who asked for a bite of the {snack_cfg['label']}?",
            answer=f"{sibling.id} asked kindly for a bite, using a soft voice instead of grabbing.",
        ),
        QAItem(
            question=f"What did {child.id} do to show kindness?",
            answer=f"{child.id} broke the {snack_cfg['label']} in half and shared it, which made the room feel warmer.",
        ),
        QAItem(
            question=f"Where did the bedtime story happen?",
            answer=f"It happened in {setting.name}, which was cozy enough for blankets, snacks, and a gentle bedtime ending.",
        ),
        QAItem(
            question=f"Who tucked the children in at the end?",
            answer=f"The {caregiver.type} tucked the blankets in after the snack was shared and the children felt calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    snack_cfg = world.facts["snack_cfg"]
    out = [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring about how another person feels.",
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it helps everyone feel included and can turn a small worry into a happy moment.",
        ),
        QAItem(
            question="What is a morsel?",
            answer="A morsel is a very small piece of food, just enough for a little bite.",
        ),
    ]
    if snack_cfg["label"] == "morsel":
        out.append(QAItem(
            question="What is a morsel in this story?",
            answer="Here, the morsel is a tiny snack that becomes easier to enjoy when the children share it.",
        ))
    return out


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
valid_setting(S) :- setting(S), cozy(S).
valid_snack(N) :- snack(N).

valid_story(S,N) :- valid_setting(S), valid_snack(N), not blocked(S,N).

blocked(hallway,N) :- snack(N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, room in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if room.cozy:
            lines.append(asp.fact("cozy", sid))
        if room.bedtime_ready:
            lines.append(asp.fact("bedtime_ready", sid))
    for nid in SNACKS:
        lines.append(asp.fact("snack", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about Penny, a morsel, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--sibling-name", choices=SIBLING_NAMES)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)]
    if not combos:
        if args.setting and args.snack:
            raise StoryError(explain_rejection(args.setting, args.snack))
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    sibling_name = args.sibling_name or rng.choice(SIBLING_NAMES)
    caregiver = args.caregiver or rng.choice(CAREGIVERS)
    if sibling_name == child_name:
        sibling_name = rng.choice([n for n in SIBLING_NAMES if n != sibling_name])
    return StoryParams(setting=setting, snack=snack, child_name=child_name,
                       sibling_name=sibling_name, caregiver=caregiver)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SNACKS[params.snack],
                 params.child_name, params.sibling_name, params.caregiver)
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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "thing" and e.shared_with:
            bits.append(f"shared_with={sorted(e.shared_with)}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
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
    StoryParams(setting="bedroom", snack="morsel", child_name="Penny", sibling_name="Milo", caregiver="mother"),
    StoryParams(setting="nursery", snack="berry", child_name="Penny", sibling_name="Nora", caregiver="father"),
    StoryParams(setting="bedroom", snack="cookie", child_name="Lily", sibling_name="Finn", caregiver="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, snack) combos:\n")
        for setting, snack in combos:
            print(f"  {setting:10} {snack}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
