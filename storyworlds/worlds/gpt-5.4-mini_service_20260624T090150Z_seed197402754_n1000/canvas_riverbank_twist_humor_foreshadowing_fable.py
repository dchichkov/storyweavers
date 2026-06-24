#!/usr/bin/env python3
"""
A small fable-style story world set at a riverbank, with a canvas, a twist,
gentle humor, and a bit of foreshadowing.

Seed tale:
---
A young otter named Pip loved painting on a canvas by the riverbank. Pip's
grandmother warned that the breeze near the water could be sneaky. Pip tried to
paint a big bright fish, but the wind kept nudging the canvas.

Then Pip noticed a funny thing: the "fish" on the canvas looked a lot like a
cloud with whiskers. When the last breeze came, it turned the canvas around and
revealed a hidden sketch on the back. Grandmother had drawn a tiny bridge long
ago, and it showed Pip a safe place to paint.

Moral shape:
- Setup: a child loves the canvas at the riverbank.
- Foreshadowing: the elder mentions the breeze and the back of the canvas.
- Twist: the canvas turns, revealing a hidden sketch.
- Humor: the picture looks unexpectedly funny before the reveal.
- Resolution: the hidden sketch leads to a better, safer place.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden_back: bool = False
    back_label: str = ""
    fragile: bool = False

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "grandmother", "woman", "aunt"}
        masculine = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def title(self) -> str:
        return self.label or self.type


@dataclass
class Riverbank:
    place: str = "the riverbank"
    breeze: bool = True
    current: str = "gentle"
    affords: set[str] = field(default_factory=lambda: {"paint", "sketch", "sit"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Riverbank) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "riverbank": Riverbank(),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a picture",
        gerund="painting pictures",
        rush="grab the brush and paint faster",
        mess="painted",
        soil="spattered with paint",
        zone={"hands", "torso"},
        keyword="canvas",
        tags={"canvas", "paint", "humor", "twist", "foreshadowing"},
    ),
    "sketch": Activity(
        id="sketch",
        verb="sketch a scene",
        gerund="sketching scenes",
        rush="reach for the charcoal and sketch quickly",
        mess="smudged",
        soil="smudged with charcoal",
        zone={"hands"},
        keyword="canvas",
        tags={"canvas", "twist", "foreshadowing"},
    ),
}

PRIZES = {
    "canvas": Prize(
        label="canvas",
        phrase="a blank canvas on a small wooden frame",
        type="canvas",
        region="hands",
    ),
}

GIRL_NAMES = ["Ava", "Mina", "Lina", "Nora", "Maya", "Ivy"]
BOY_NAMES = ["Pip", "Theo", "Milo", "Finn", "Otto", "Leo"]
TRAITS = ["curious", "gentle", "bright", "thoughtful", "cheerful"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    place = args.place or "riverbank"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "canvas"
    if place not in SETTINGS:
        raise StoryError("This story world only knows the riverbank.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if prize not in PRIZES:
        raise StoryError("Unknown prize.")
    return place, activity, prize


def predict_twist(world: World, hero: Entity, activity: Activity, canvas: Entity) -> bool:
    sim = world.copy()
    h = sim.get(hero.id)
    c = sim.get(canvas.id)
    h.meters[activity.mess] = 1.0
    if sim.setting.breeze:
        c.memes["turning"] = 1.0
    return True


def introduce(world: World, hero: Entity, elder: Entity, canvas: Entity, activity: Activity) -> None:
    world.say(
        f"At the riverbank, {hero.id} was a little {hero.type} who loved {activity.gerund} "
        f"on {hero.pronoun('possessive')} {canvas.label}."
    )
    world.say(
        f"{elder.label.capitalize()} had a calm voice and a clever smile, and {elder.pronoun()} "
        f"often said the breeze near the water liked to play tricks."
    )
    world.facts["foreshadowed_breeze"] = True


def foreshadow(world: World, elder: Entity, hero: Entity, canvas: Entity) -> None:
    world.say(
        f'"If the wind leans close," {elder.pronoun("subject")} said, '
        f'"it may turn the {canvas.label} and show you what hides on the back."'
    )
    world.facts["hidden_back_mentioned"] = True


def start_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters[activity.mess] = 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    world.say(
        f"{hero.id} smiled and began to {activity.verb}, because the water and the sky "
        f"made a fine place for a busy little scene."
    )


def humor(world: World, hero: Entity, canvas: Entity) -> None:
    world.say(
        f"{hero.id} painted a fish with a round nose and a very serious eyebrow, "
        f"and that made the whole picture look a little funny."
    )
    hero.memes["amusement"] = hero.memes.get("amusement", 0.0) + 1.0


def twist(world: World, hero: Entity, elder: Entity, canvas: Entity) -> None:
    if not world.setting.breeze:
        return
    canvas.memes["turned"] = 1.0
    world.say(
        f"Then the breeze gave the frame a small nudge. The {canvas.label} spun around, "
        f"and everyone blinked."
    )
    world.say(
        f"On the back was a hidden sketch of a tiny bridge, drawn long ago by "
        f"{elder.label}."
    )
    world.facts["twist_revealed"] = True


def resolution(world: World, hero: Entity, elder: Entity, canvas: Entity) -> None:
    world.say(
        f"{hero.id} looked at the bridge and understood. The best place to paint was "
        f"the quiet path beside it, where the breeze was softer."
    )
    world.say(
        f"So {hero.id} carried the {canvas.label} to the new spot, and the little picture "
        f"grew brighter there."
    )
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1.0
    world.facts["resolved"] = True


def tell(setting: Riverbank, activity: Activity, prize_cfg: Prize,
         name: str = "Pip", hero_type: str = "otter", elder_type: str = "grandmother",
         trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=hero_type))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="grandmother"))
    canvas = world.add(Entity(id="canvas", type=prize_cfg.type, label=prize_cfg.label,
                              phrase=prize_cfg.phrase, owner=hero.id, caretaker=elder.id,
                              hidden_back=True, back_label="tiny bridge"))

    world.facts.update(hero=hero, elder=elder, canvas=canvas, activity=activity, setting=setting)

    introduce(world, hero, elder, canvas, activity)
    foreshadow(world, elder, hero, canvas)

    world.para()
    start_activity(world, hero, activity)
    humor(world, hero, canvas)
    twist(world, hero, elder, canvas)

    world.para()
    resolution(world, hero, elder, canvas)
    world.facts["trait"] = trait
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        'Write a short fable set at a riverbank that includes a canvas and a gentle surprise.',
        f"Tell a child-sized story where {hero.id} loves to {act.verb} beside the riverbank and learns a wise lesson.",
        f'Write a humorous fable with foreshadowing, a canvas, and a twist in the wind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    canvas = f["canvas"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} love to do at the riverbank?",
            answer=f"{hero.id} loved {act.gerund} on the {canvas.label}.",
        ),
        QAItem(
            question=f"What warning did {elder.label} give about the breeze?",
            answer=(
                f"{elder.label} warned that the breeze might turn the {canvas.label} "
                f"and reveal what was on the back."
            ),
        ),
        QAItem(
            question="What was funny about the picture before the twist?",
            answer=(
                f"The fish on the canvas had a round nose and a serious eyebrow, "
                f"which made it look silly."
            ),
        ),
        QAItem(
            question="What was revealed when the canvas turned?",
            answer=(
                f"A hidden sketch of a tiny bridge appeared on the back of the canvas."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"{hero.id} carried the canvas to the quieter place near the bridge "
                f"and painted there, where the breeze was softer."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a canvas?",
            answer="A canvas is a strong cloth surface that people can paint on.",
        ),
        QAItem(
            question="What does a breeze do?",
            answer="A breeze is a light wind that can move leaves, cloth, or paper.",
        ),
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land along the side of a river.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / serialization helpers
# ---------------------------------------------------------------------------

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
        if e.hidden_back:
            bits.append("hidden_back=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(riverbank).
% activity(paint).  mess_of(paint, painted).  splashes(paint, hands). splashes(paint, torso).
% activity(sketch). mess_of(sketch, smudged). splashes(sketch, hands).
% prize(canvas). worn_on(canvas, hands).

needs_warning(A) :- activity(A), splashes(A, hands), worn_on(canvas, hands).
has_foreshadowing :- needs_warning(A), activity(A).

has_humor(A) :- activity(A), mess_of(A, M), M = painted.
has_twist :- has_foreshadowing, setting(riverbank).

good_story :- setting(riverbank), prize(canvas), has_foreshadowing, has_humor(paint), has_twist.

#show needs_warning/1.
#show has_foreshadowing/0.
#show has_humor/1.
#show has_twist/0.
#show good_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "riverbank")]
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    return "\n".join(lines)


def asp_program(show: str = "#show good_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_set() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/0."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    import asp
    program = asp_program("#show good_story/0.")
    model = asp.one_model(program)
    shown = set(asp.atoms(model, "good_story"))
    expected = {()}
    if shown == expected:
        print("OK: ASP twin matches the Python story gate.")
        return 0
    print("MISMATCH: ASP twin disagrees with the Python story gate.")
    print("  ASP:", sorted(shown))
    print("  Python:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: riverbank fable with canvas, twist, humor, and foreshadowing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "riverbank"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "canvas"
    if place != "riverbank":
        raise StoryError("This story world is set only at the riverbank.")
    if prize != "canvas":
        raise StoryError("This story world needs a canvas.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = "grandmother"
    parent = args.parent or elder_type
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=name,
        hero_type="otter" if gender == "boy" else "otter",
        elder_type=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        name=params.name,
        hero_type=params.hero_type,
        elder_type=params.elder_type,
        trait=params.trait,
    )
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
        print(asp_program("#show good_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story pattern:")
        print("  riverbank / any activity / canvas")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for activity in ACTIVITIES:
            params = StoryParams(
                place="riverbank",
                activity=activity,
                prize="canvas",
                name="Pip",
                hero_type="otter",
                elder_type="grandmother",
                trait="curious",
            )
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
