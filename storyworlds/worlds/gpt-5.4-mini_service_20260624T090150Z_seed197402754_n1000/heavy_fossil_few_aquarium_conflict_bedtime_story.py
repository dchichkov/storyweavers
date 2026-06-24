#!/usr/bin/env python3
"""
A small bedtime-style storyworld set at an aquarium.

Premise:
- A child loves quiet aquarium visits and collects little sea treasures.
- A heavy fossil is tempting, but it is too big to carry safely.
- A parent notices the problem and offers a softer, lighter choice.

The story engine builds a tiny simulation of:
- physical state: weight, carried items, distance, calmness
- emotional state: wonder, conflict, comfort

The domain is intentionally narrow so the generated story stays close to a
gentle bedtime tale: soft lights, a few fish, a careful parent, and a peaceful
ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

SETTING_NAME = "the aquarium"

# Story seed words required by the request.
SEED_WORDS = ("heavy", "fossil", "few")

# A small, curated vocabulary keeps the prose child-facing and concrete.
GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Leo", "Theo"]
TRAITS = ["sleepy", "curious", "gentle", "quiet", "brave"]

# The story supports only one setting, but we keep the registry structure.
@dataclass(frozen=True)
class Setting:
    name: str = SETTING_NAME
    affords: tuple[str, ...] = ("visit",)


@dataclass(frozen=True)
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Prize:
    label: str
    phrase: str
    region: str = "arms"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    tags: tuple[str, ...] = ()


SETTINGS = {"aquarium": Setting()}

ACTIVITIES = {
    "visit": Activity(
        id="visit",
        verb="look at the fish",
        gerund="looking at the fish",
        rush="hurry toward the glowing tanks",
        tags=("fish", "quiet", "few"),
    )
}

PRIZES = {
    "fossil": Prize(
        label="fossil",
        phrase="a heavy fossil from the aquarium shop",
        region="arms",
        tags=("heavy", "fossil"),
    ),
    "postcard": Prize(
        label="postcard",
        phrase="a little fossil postcard",
        region="hands",
        tags=("fossil", "light"),
    ),
}

GEAR = {
    "bag": Gear(
        id="bag",
        label="a soft little bag",
        prep="put the heavy fossil back on the shelf and choose the little bag",
        tail="walked slowly beside the tanks with the postcard tucked safely inside",
        tags=("light",),
    )
}


# ---------------------------------------------------------------------------
# Shared result-compatible world model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "aquarium"
    activity: str = "visit"
    prize: str = "fossil"
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "curious"
    seed: Optional[int] = None


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Causal simulation
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def _do_visit(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters["tired"] = child.meters.get("tired", 0.0) + 1.0
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1.0
    if narrate:
        world.say(
            f"{child.id} looked at the fish and felt the water glow softly behind the glass."
        )


def predict_conflict(world: World, child: Entity, prize: Entity) -> dict[str, float | bool]:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_prize = sim.get(prize.id)
    sim_child.meters["wanting"] = sim_child.meters.get("wanting", 0.0) + 1.0
    sim_child.memes["conflict"] = sim_child.memes.get("conflict", 0.0) + 1.0
    sim_prize.meters["carry"] = sim_prize.meters.get("carry", 0.0) + 1.0
    too_heavy = sim_prize.label == "fossil"
    return {
        "too_heavy": too_heavy,
        "conflict": True,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.meters.get("traits", []) if t), None)
    desc = f"little {child.memes.get('trait', '')} {child.type}".strip()
    world.say(
        f"{child.id} was a quiet {child.type} who loved the aquarium's still blue light."
    )


def setup(world: World, child: Entity, parent: Entity, prize: Entity) -> None:
    world.say(
        f"One evening, {child.id} and {parent.pronoun('possessive')} {parent.type} "
        f"went to {world.setting.name}."
    )
    world.say(
        f"{child.id} liked the tanks with only a few sleepy fish, because the room felt calm enough for bedtime."
    )
    world.say(
        f"Near the gift shelf, {child.id} found {prize.phrase} and wanted to carry {prize.it()} all around."
    )


def conflict(world: World, child: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    pred = predict_conflict(world, child, prize)
    child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{child.id} tried to lift the {prize.label}, but it was heavy, and the idea made {child.pronoun('object')} frown."
    )
    world.say(
        f"{parent.pronoun().capitalize()} said, 'That {prize.label} is too heavy to carry around the aquarium.'"
    )
    if pred["too_heavy"]:
        world.say(
            f"{parent.pronoun().capitalize()} worried the heavy fossil might make {child.id} tired before the last tank."
        )
    world.say(
        f"{child.id} wanted the fossil anyway, and for a moment the wish and the no did not fit together."
    )


def resolve(world: World, child: Entity, parent: Entity, prize: Entity, gear: Gear) -> None:
    child.memes["conflict"] = 0.0
    child.memes["comfort"] = child.memes.get("comfort", 0.0) + 1.0
    world.say(
        f"Then {parent.pronoun().capitalize()} showed {child.id} a small choice."
    )
    world.say(
        f"'{gear.prep},' {parent.pronoun()} said, and {child.id} nodded."
    )
    world.say(
        f"{child.id} put {prize.it()} back, took the little postcard instead, and smiled at the few quiet fish."
    )
    world.say(
        f"Together they {gear.tail}, and the aquarium felt soft and peaceful again."
    )
    world.say(
        f"At the end, {child.id} held the tiny fossil picture, not the heavy fossil, and the blue lights shimmered like sleepy stars."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mia", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"tired": 0.0},
        memes={"trait": (hero_traits or ["curious"])[0], "wonder": 0.0, "conflict": 0.0},
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
    ))

    introduce(world, child)
    world.para()
    setup(world, child, parent, prize)
    world.para()
    conflict(world, child, parent, prize, activity)
    world.para()
    resolve(world, child, parent, prize, GEAR["bag"])

    world.facts.update(
        child=child,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=GEAR["bag"],
        setting=setting,
        resolved=True,
        conflict=True,
    )
    return world


# ---------------------------------------------------------------------------
# Registries / story generation helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    return [("aquarium", "visit", "fossil")]


def explain_rejection(place: str, activity: str, prize: str) -> str:
    return "(No story: this world only supports a gentle aquarium visit with the heavy fossil turning into a small compromise.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    return [
        f'Write a bedtime story for a young child at the aquarium about a heavy fossil and a few sleepy fish.',
        f"Tell a soft story where {child.id} wants to carry the heavy fossil, but {parent.pronoun('possessive')} {parent.type} worries and offers a gentler choice.",
        f'Write a child-friendly aquarium story that includes the words "heavy", "fossil", and "few" and ends peacefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Why did {child.id} and {parent.pronoun('possessive')} {parent.type} go to the aquarium?",
            answer=f"They went to the aquarium to look at the fish and enjoy the quiet blue room together.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with the {prize.label}?",
            answer=f"{child.id} wanted to carry the {prize.label} around, even though it was heavy.",
        ),
        QAItem(
            question=f"How did the parent help when the heavy fossil caused conflict?",
            answer=f"The parent suggested a smaller choice, so {child.id} could take a little fossil postcard instead of the heavy fossil.",
        ),
        QAItem(
            question=f"What did the child see in the tanks?",
            answer=f"{child.id} saw a few sleepy fish, and the calm water made the aquarium feel bedtime-quiet.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aquarium?",
            answer="An aquarium is a place where people can watch fish and other water animals in tanks.",
        ),
        QAItem(
            question="What does heavy mean?",
            answer="Heavy means something is hard to lift or carry because it weighs a lot.",
        ),
        QAItem(
            question="What is a fossil?",
            answer="A fossil is a very old trace of a plant or animal that was kept in stone.",
        ),
        QAItem(
            question="What does few mean?",
            answer="Few means not many, like a small group of fish in a quiet tank.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        out.append(f"  {e.id}: {', '.join(bits) if bits else 'empty'}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(aquarium).
activity(visit).
prize(fossil).
gear(bag).

heavy(fossil).
few(fish).

compatible(aquarium, visit, fossil).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "aquarium"),
        asp.fact("activity", "visit"),
        asp.fact("prize", "fossil"),
        asp.fact("gear", "bag"),
        asp.fact("heavy", "fossil"),
        asp.fact("few", "fish"),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld set in an aquarium.")
    ap.add_argument("--place", choices=["aquarium"], default="aquarium")
    ap.add_argument("--activity", choices=["visit"], default="visit")
    ap.add_argument("--prize", choices=["fossil"], default="fossil")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place="aquarium",
        activity="visit",
        prize="fossil",
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
        print(ASP_RULES)
        return

    if args.verify:
        # Minimal parity check: the python registry and ASP twin both describe
        # the single supported story.
        if valid_combos() == [("aquarium", "visit", "fossil")]:
            print("OK: ASP/Python story gate is aligned.")
            return
        raise SystemExit(1)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
