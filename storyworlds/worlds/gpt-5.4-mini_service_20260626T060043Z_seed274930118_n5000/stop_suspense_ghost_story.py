#!/usr/bin/env python3
"""
storyworlds/worlds/stop_suspense_ghost_story.py
================================================

A small story world for a gentle ghost tale with suspense and a clear stop.

Premise:
- A child hears a spooky sound in an old house.
- Suspense builds as the child follows clues with a lantern and a brave helper.
- The tension stops when the "ghost" turns out to be a harmless, lonely helper.
- The ending image proves the change: fear becomes calm, and the house feels kind.

This world keeps the prose child-facing and concrete while modeling:
- physical meters: light, creak, chill, hidden, dust
- emotional memes: fear, curiosity, courage, relief, care

The ASP twin mirrors the Python reasonableness gate:
- a suspense story is valid only if there is a source of mystery,
  a safe helper, and a reveal that can reasonably stop the fear.
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
# Typed world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    portable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def meme(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    detail: str = "The hallway was long, and the floorboards liked to creak."


@dataclass
class Mystery:
    id: str
    clue: str
    source: str
    reveal: str
    source_kind: str = "thing"


@dataclass
class Helper:
    id: str
    label: str
    action: str
    reveal_action: str
    kind: str = "character"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "house": Setting(
        place="the old house",
        detail="The hallway was long, and the floorboards liked to creak.",
    ),
    "attic": Setting(
        place="the attic room",
        detail="The attic was dusty and small, with a round window and a crooked beam.",
    ),
    "hall": Setting(
        place="the front hall",
        detail="The front hall was dim, with coats hanging like quiet shadows.",
    ),
}

MYSTERIES = {
    "creak": Mystery(
        id="creak",
        clue="a slow creak from the stairs",
        source="the loose step",
        reveal="a loose step, rocked by the wind",
        source_kind="thing",
    ),
    "tap": Mystery(
        id="tap",
        clue="a tiny tap on the window",
        source="a branch brushing the glass",
        reveal="a branch tapping the window in the breeze",
        source_kind="thing",
    ),
    "glow": Mystery(
        id="glow",
        clue="a pale glow in the dark corner",
        source="a jar of fireflies",
        reveal="a jar of fireflies left by the helper",
        source_kind="thing",
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        label="Grandma",
        action="take a careful look with a warm lantern",
        reveal_action="smile and open the little door behind the cupboard",
    ),
    "neighbor": Helper(
        id="neighbor",
        label="Mr. Finch",
        action="listen closely and kneel by the floorboards",
        reveal_action="lift a loose board and show the hidden mouse toy",
    ),
    "cat": Helper(
        id="cat",
        label="Mina the cat",
        action="pad softly into the dark and sniff the corner",
        reveal_action="nudge aside a cloth and reveal the harmless glow",
    ),
}

# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting: Setting, mystery: Mystery, helper: Helper) -> bool:
    if setting.place == "the attic room" and mystery.id == "creak" and helper.id == "cat":
        return True
    if setting.place == "the old house" and mystery.id in {"creak", "tap"} and helper.id in {"grandma", "neighbor"}:
        return True
    if setting.place == "the front hall" and mystery.id in {"tap", "glow"} and helper.id in {"grandma", "cat"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for mid, m in MYSTERIES.items():
            for hid, h in HELPERS.items():
                if valid_combo(s, m, h):
                    out.append((sid, mid, hid))
    return out


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable if the setting can host the mystery,
% the helper can safely investigate it, and the reveal can stop the fear.
can_story(S, M, H) :- setting(S), mystery(M), helper(H),
                      setting_mystery(S, M), helper_safe(H, M), reveal_stops_fear(M, H).

#show can_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("setting_mystery", "house", mid) if mid in {"creak", "tap"} else asp.fact("setting_mystery", "hall", mid) if mid == "glow" else asp.fact("setting_mystery", "attic", mid))
        lines.append(asp.fact("mystery_source", mid, m.source_kind))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_safe", hid, "creak"))
        lines.append(asp.fact("helper_safe", hid, "tap"))
        lines.append(asp.fact("helper_safe", hid, "glow"))
        lines.append(asp.fact("reveal_stops_fear", "creak", hid))
        lines.append(asp.fact("reveal_stops_fear", "tap", hid))
        lines.append(asp.fact("reveal_stops_fear", "glow", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Theo", "Max", "Finn"]
TRAITS = ["curious", "brave", "quiet", "gentle", "sensitive"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, mystery, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, mystery, helper, name, gender, parent, trait)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with suspense and a stop.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def _meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meter(key) + delta


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    ghost = world.add(Entity(id="ghost", kind="thing", type="ghost", label="the ghost"))
    clue = world.add(Entity(id="clue", kind="thing", type="thing", label=mystery.clue, phrase=mystery.clue))
    helper_ent = world.add(Entity(id=helper.id, kind=helper.kind, type="adult", label=helper.label))
    source = world.add(Entity(id="source", kind="thing", type="thing", label=mystery.source, phrase=mystery.reveal))

    hero.memes["fear"] = 0
    hero.memes["curiosity"] = 0
    hero.memes["courage"] = 0
    hero.memes["relief"] = 0

    world.say(f"{hero.id} was a little {params.trait} child who lived in {setting.place}.")
    world.say(f"{hero.id} loved quiet nights, but {setting.detail}")
    world.say(f"One evening, {hero.id} heard {mystery.clue}, and the sound made the room feel cold.")

    world.para()
    _meter(ghost, "hidden", 1)
    _meter(hero, "chill", 1)
    hero.memes["fear"] += 1
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} stopped and listened. The dark felt bigger, and {hero.pronoun()} held very still.")
    world.say(f"{hero.id} took a tiny lantern and followed the clue toward the shadowy place.")

    world.para()
    world.say(f"Then {helper.label} arrived and said, \"Let's take a careful look.\"")
    world.say(f"{helper.label} chose to {helper.action}.")
    hero.memes["courage"] += 1
    _meter(clue, "visible", 1)
    _meter(source, "near", 1)

    world.para()
    world.say(f"At last, {helper.label} did not find a scary ghost at all.")
    world.say(f"{helper.label} {helper.reveal_action}, and the mystery was solved: it was {mystery.reveal}.")
    hero.memes["fear"] = 0
    hero.memes["relief"] += 2
    _meter(hero, "chill", -1)
    _meter(ghost, "hidden", -1)
    world.say(f"{hero.id} laughed softly because the spooky sound had a simple answer.")
    world.say(f"The fear stopped, the lantern looked warm, and {setting.place} felt friendly again.")

    world.facts.update(
        hero=hero,
        parent=parent,
        ghost=ghost,
        clue=clue,
        helper=helper_ent,
        source=source,
        mystery=mystery,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a child that includes the word "stop" and keeps the suspense gentle.',
        f"Tell a suspenseful story set in {f['setting'].place} where {f['hero'].id} hears {f['mystery'].clue} and a helper solves it.",
        f"Write a child-friendly ghost story where a scary-sounding mystery turns out to have a harmless answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What made {hero.id} feel scared at first?",
            answer=f"{hero.id} felt scared when {mystery.clue} sounded in {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look at the spooky sound?",
            answer=f"{helper.label} helped {hero.id} look carefully instead of running away.",
        ),
        QAItem(
            question="What stopped the suspense in the end?",
            answer=f"The suspense stopped when the mystery turned out to be {mystery.reveal}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the mystery was solved?",
            answer=f"{hero.id} felt relieved and calm after the scary sound made sense.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next because something seems uncertain or mysterious.",
        ),
        QAItem(
            question="Why can a floorboard make a creepy sound?",
            answer="A floorboard can creak when it is loose, old, or pressed by a step, so the sound does not always mean danger.",
        ),
        QAItem(
            question="What is a lantern for?",
            answer="A lantern gives off light so people can see better in dark places.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("house", "creak", "grandma", "Mia", "girl", "mother", "curious"),
    StoryParams("hall", "glow", "cat", "Leo", "boy", "father", "gentle"),
    StoryParams("house", "tap", "neighbor", "Nora", "girl", "mother", "brave"),
]


def asp_verify_program() -> str:
    return asp_program("#show can_story/3.")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_verify_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_verify_program())
        print(f"{len(asp.atoms(model, 'can_story'))} compatible stories:")
        for t in sorted(set(asp.atoms(model, "can_story"))):
            print(" ", t)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
