#!/usr/bin/env python3
"""
storyworlds/worlds/tonsil_mere_attic_ladder_repetition_conflict_folk.py
=======================================================================

A small folk-tale storyworld set at an attic ladder, built from a seed idea:
a child, a repetition, a conflict, and a soft old-time ending image.

Premise:
- A child wants to go up the attic ladder to fetch a small treasured thing.
- Their throat is sore, so they keep repeating themselves.
- A grown helper worries about the climb and the dust in the attic.
- The child and helper clash, then settle on a safer way up.

World model:
- Characters and objects have physical meters and emotional memes.
- The ladder is a risky place: it can be climbed, but only carefully.
- Repetition raises insistence and makes the child speak in a folk-like refrain.
- Conflict rises when the child pushes and the helper refuses, then falls when
  the helper offers a safer compromise.

This script is self-contained except for the shared storyworld result/ASP helpers.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the attic ladder"
    affords: set[str] = field(default_factory=lambda: {"climb", "search"})


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    risk: str
    reward: str


@dataclass
class StoryParams:
    name: str
    gender: str
    helper: str
    treasure: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("repetition", 0) < THRESHOLD:
        return out
    sig = ("repetition",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["insistence"] = child.memes.get("insistence", 0) + 1
    child.meters["voice"] = child.meters.get("voice", 0) + 1
    out.append(f"{child.pronoun().capitalize()} said it again and again, like a little folk refrain.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("insistence", 0) < THRESHOLD or helper.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = child.memes.get("conflict", 0) + 1
    helper.memes["conflict"] = helper.memes.get("conflict", 0) + 1
    out.append("The two of them stood with the ladder between them, each certain of their own way.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes.get("conflict", 0) < THRESHOLD:
        return out
    if helper.memes.get("care", 0) < THRESHOLD:
        return out
    sig = ("settle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["conflict"] = 0
    helper.memes["conflict"] = 0
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    out.append("Then the helper found a safer way, and the sharpness of the quarrel softened.")
    return out


CAUSAL_RULES = [Rule("repetition", _r_repetition), Rule("conflict", _r_conflict), Rule("settle", _r_settle)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story content
# ---------------------------------------------------------------------------

SETTING = Setting(place="the attic ladder")

TREASURES = {
    "tin_flute": Treasure(
        id="tin_flute",
        label="tin flute",
        phrase="a little tin flute wrapped in blue cloth",
        risk="dusty and hard to play",
        reward="sing again",
    ),
    "button_box": Treasure(
        id="button_box",
        label="button box",
        phrase="a round button box with a moth-eaten lid",
        risk="lost in the dust",
        reward="mend the old coat",
    ),
    "seed_pouch": Treasure(
        id="seed_pouch",
        label="seed pouch",
        phrase="a tiny seed pouch tied with red thread",
        risk="spilled on the steps",
        reward="plant next spring",
    ),
}

NAMES = {
    "girl": ["Mara", "Nell", "Anya", "Tess"],
    "boy": ["Bram", "Owen", "Jory", "Pip"],
}

HELPERS = {
    "grandmother": "grandmother",
    "grandfather": "grandfather",
    "aunt": "aunt",
    "uncle": "uncle",
}


def choose_story(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(name=name, gender=gender, helper=helper, treasure=treasure)


def make_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"voice": 0.0, "throat": 1.0},
        memes={"repetition": 0.0, "insistence": 0.0, "conflict": 0.0, "joy": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=params.helper,
        meters={"worry": 0.0, "care": 1.0},
        memes={"worry": 1.0, "care": 1.0, "conflict": 0.0},
    ))
    treasure = TREASURES[params.treasure]
    tr = world.add(Entity(
        id="treasure",
        kind="thing",
        type=treasure.id,
        label=treasure.label,
        phrase=treasure.phrase,
        owner=helper.id,
        caretaker=helper.id,
        meters={"dust": 0.0, "value": 1.0},
        memes={"memory": 1.0},
    ))
    world.facts.update(child=child, helper=helper, treasure=tr, treasure_def=treasure, params=params)
    return world


def tell_story(world: World) -> None:
    c = world.get("child")
    h = world.get("helper")
    t = world.get("treasure")
    td: Treasure = world.facts["treasure_def"]

    world.say(
        f"{c.label} lived in a little house where the attic ladder creaked like an old song."
        f" One morning {c.label} remembered {t.phrase} above the beams, and {c.pronoun('possessive')} throat felt sore and tight."
    )
    world.say(
        f"Still, {c.label} wanted to climb up to find {t.label}, for {td.reward} was hidden with the old keepsakes."
        f" {c.pronoun().capitalize()} asked once, then again, then again: up the ladder, up the ladder, up the ladder."
    )
    c.memes["repetition"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"But {h.label} shook {h.pronoun('possessive')} head."
        f" The steps were steep, the boards were dusty, and the attic ladder was no place for a child to rush."
    )
    world.say(
        f"{h.pronoun().capitalize()} worried that the treasure might come down {td.risk}, and {c.label} crossed {c.pronoun('possessive')} arms."
    )
    h.memes["worry"] = 1.0
    c.memes["insistence"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"{c.label} repeated the request one more time, softer now but still stubborn, as if the same words might make the door open."
    )
    world.say(
        f"At last {h.label} brought a lamp and said they would climb together, one careful step at a time."
    )
    c.memes["conflict"] = 1.0
    h.memes["care"] = 1.0
    propagate(world)

    world.para()
    world.say(
        f"So {h.label} went first, and {c.label} followed close behind, holding the rail and breathing easy."
        f" In the dusty attic they found {t.phrase}, and it was just as dear as the old story had promised."
    )
    world.say(
        f"When they came back down the ladder, {c.label}'s sore throat was still sore, but the worry had gone."
        f" {c.label} kept the little treasure near, and the house felt warmer for the shared climb."
    )

    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    t = world.facts["treasure_def"]
    return [
        f"Write a short folk tale about {p.name} at the attic ladder, repeating a request until the grown helper listens.",
        f"Tell a gentle story where a sore throat, a treasure above the stairs, and a careful climb all matter.",
        f"Write a child-facing story that includes repetition, conflict, and a safe ending image with {t.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    h = world.get("helper")
    t = world.get("treasure")
    td: Treasure = world.facts["treasure_def"]
    c = world.get("child")

    return [
        QAItem(
            question=f"Why did {p.name} keep saying the same thing about the attic ladder?",
            answer=(
                f"{p.name} kept repeating the request because {p.name} really wanted to go up the attic ladder and fetch {t.label}."
                f" The sore throat made the voice small, but the wish stayed strong."
            ),
        ),
        QAItem(
            question=f"Why was the {p.helper} worried about the climb?",
            answer=(
                f"The {p.helper} worried because the ladder was steep and dusty, and the treasure above could come down {td.risk}."
                f" The helper wanted the child to be safe."
            ),
        ),
        QAItem(
            question="What changed after the argument?",
            answer=(
                f"After the argument, the helper brought a lamp and went up first, so the child could follow safely."
                f" The conflict faded, and they found {t.phrase} together."
            ),
        ),
        QAItem(
            question=f"How did {p.name} feel at the end?",
            answer=(
                f"At the end, {p.name} felt relieved and glad."
                f" The child came back down the ladder with {t.label}, and the house felt calmer."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ladder for?",
            answer="A ladder is for climbing up and down to reach a higher place carefully.",
        ),
        QAItem(
            question="What does repetition mean in a story?",
            answer="Repetition means saying, doing, or hearing something again and again.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is when characters want different things and have trouble agreeing.",
        ),
        QAItem(
            question="What does mere mean?",
            answer="Mere means only or just a small amount of something.",
        ),
        QAItem(
            question="What is a tonsil?",
            answer="A tonsil is a little soft part at the back of the throat.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/2.

valid_story(Child, Treasure) :- child(Child), treasure(Treasure), safe_climb(Child), shared_find(Child, Treasure).

safe_climb(Child) :- repetition(Child), care(helper), lamp(helper).
shared_find(Child, Treasure) :- helper(helper), child(Child), treasure(Treasure), climb_together(Child).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in ["child", "helper"]:
        lines.append(asp.fact(name, name))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    lines.append(asp.fact("repetition", "child"))
    lines.append(asp.fact("care", "helper"))
    lines.append(asp.fact("lamp", "helper"))
    lines.append(asp.fact("climb_together", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_pairs = set(asp.atoms(model, "valid_story"))
    py_pairs = {( "child", tid) for tid in TREASURES}
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python story space ({len(py_pairs)} treasures).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", sorted(asp_pairs))
    print("  python:", sorted(py_pairs))
    return 1


# ---------------------------------------------------------------------------
# Storyworld API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale world at an attic ladder.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--treasure", choices=list(TREASURES))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(list(HELPERS))
    treasure = args.treasure or rng.choice(list(TREASURES))
    return StoryParams(name=name, gender=gender, helper=helper, treasure=treasure)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(name="Mara", gender="girl", helper="grandmother", treasure="tin_flute"),
    StoryParams(name="Bram", gender="boy", helper="grandfather", treasure="button_box"),
    StoryParams(name="Nell", gender="girl", helper="aunt", treasure="seed_pouch"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise SystemExit(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for child, treasure in pairs:
            print(f"{child} -> {treasure}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.treasure} at the attic ladder"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
