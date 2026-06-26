#!/usr/bin/env python3
"""
pupa_appetizing_quail_campground_reconciliation_kindness_quest.py
=================================================================

A small Animal-Story-style world about a campground quest where a pupa,
an appetizing snack, and a quail become part of a reconciliation story.

Premise:
- A young animal wants to take part in a campground quest.
- A tempting appetizing treat creates tension.
- A quail's nest or a shared snack gets tangled in the choice.
- Kindness and reconciliation turn the moment into a gentle ending.

The story is state-driven: characters have physical meters and emotional memes,
the world tracks simple causal facts, and the ending image proves what changed.
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
# World data
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
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the campground"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    name: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    tempt: str
    region: str
    mess: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "campground": Setting(place="the campground", affords={"quest"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        name="reconciliation quest",
        verb="follow the trail",
        gerund="following the trail",
        rush="dash toward the pine path",
        risk="leave a friend behind",
        keyword="quest",
        tags={"quest", "reconciliation", "kindness"},
    ),
}

TASTES = {
    "snack": Treat(
        id="snack",
        label="appetizing snack",
        phrase="an appetizing snack wrapped in paper",
        tempt="look delicious",
        region="snout",
        mess="crumbs",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Pippa", "Nora", "Tia"]
BOY_NAMES = ["Bram", "Otto", "Milo", "Finn", "Rowan"]
ANIMAL_TYPES = ["rabbit", "fox", "badger", "squirrel", "deer"]
TRAITS = ["curious", "gentle", "brave", "quiet", "kind"]


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for quest_id in setting.affords:
            for treat_id in TASTES:
                combos.append((place, quest_id, treat_id))
    return combos


ASP_RULES = r"""
place(campground).
affords(campground,quest).
quest(quest).
treat(snack).
valid(Place,Quest,Treat) :- place(Place), affords(Place,Quest), treat(Treat), quest(Quest).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for q in sorted(setting.affords):
            lines.append(asp.fact("affords", place, q))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for t in TASTES:
        lines.append(asp.fact("treat", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
# Story model
# ---------------------------------------------------------------------------

def predict(world: World, hero: Entity, quest: Quest, treat: Treat) -> dict:
    sim = world.copy()
    _begin_quest(sim, sim.get(hero.id), quest, narrate=False)
    _tempt(sim, sim.get(hero.id), treat, narrate=False)
    return {
        "mess": sim.get(hero.id).meters.get("crumbs", 0) >= THRESHOLD,
        "hurt_feelings": sim.get(hero.id).memes.get("hurt", 0) >= THRESHOLD,
    }


def _begin_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.facts["quest_started"] = True
    if narrate:
        world.say(
            f"{hero.id} wanted to join the {quest.name} at {world.setting.place}, "
            f"because the trail looked exciting."
        )


def _tempt(world: World, hero: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    if narrate:
        world.say(
            f"Near the fire ring, an {treat.label} began to {treat.tempt}, "
            f"and {hero.id} paused to sniff the air."
        )


def _messy_choice(world: World, hero: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.meters[treat.mess] = hero.meters.get(treat.mess, 0) + 1
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    if narrate:
        world.say(
            f"{hero.id} took a bite too fast, and {treat.label} left {treat.mess} "
            f"on {hero.pronoun('possessive')} paws."
        )


def _apology(world: World, hero: Entity, helper: Entity, treat: Treat, narrate: bool = True) -> None:
    hero.memes["apology"] = hero.memes.get("apology", 0) + 1
    helper.memes["softness"] = helper.memes.get("softness", 0) + 1
    if narrate:
        world.say(
            f"{hero.id} lowered {hero.pronoun('possessive')} head and said sorry to "
            f"{helper.id}, then offered to wipe the crumbs away."
        )


def _reconcile(world: World, hero: Entity, helper: Entity, quest: Quest, treat: Treat, narrate: bool = True) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.memes["peace"] = 1
    helper.memes["peace"] = 1
    if narrate:
        world.say(
            f"{helper.id} smiled and shared the {treat.label} more slowly, and "
            f"{hero.id} promised to be careful on the {quest.gerund} path."
        )
        world.say(
            f"Together they walked on, side by side, with the trail ahead and "
            f"their friendship feeling lighter."
        )


def run_world(world: World, hero: Entity, helper: Entity, quest: Quest, treat: Treat) -> None:
    _begin_quest(world, hero, quest)
    world.para()
    _tempt(world, hero, treat)
    if predict(world, hero, quest, treat)["mess"]:
        _messy_choice(world, hero, treat)
        world.say(
            f"{helper.id} noticed the mess and did not scold {hero.id}; instead, "
            f"{helper.id} gave a calm look and a cloth."
        )
        _apology(world, hero, helper, treat)
        _reconcile(world, hero, helper, quest, treat)
    else:
        world.say(
            f"Nothing went wrong, so {hero.id} and {helper.id} kept walking "
            f"through the campground with easy smiles."
        )


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    treat: str
    name: str
    species: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: a campground quest with kindness and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--treat", choices=TASTES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=ANIMAL_TYPES)
    ap.add_argument("--helper", choices=["friend", "parent", "ranger"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.quest is None or c[1] == args.quest)
        and (args.treat is None or c[2] == args.treat)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, treat = rng.choice(sorted(combos))
    species = args.species or rng.choice(ANIMAL_TYPES)
    name = args.name or rng.choice(GIRL_NAMES if rng.random() < 0.5 else BOY_NAMES)
    helper = args.helper or rng.choice(["friend", "parent", "ranger"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, treat=treat, name=name, species=species, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.species, memes={}, meters={}))
    helper = world.add(Entity(id=params.helper.capitalize(), kind="character", type="adult", label=params.helper))
    world.add(Entity(id="pupa", type="pupa", label="pupa"))
    quest = QUESTS[params.quest]
    treat = TASTES[params.treat]

    world.say(
        f"{hero.id} was a {params.trait} {params.species} at {world.setting.place}, "
        f"and even the tiny pupa by the pine log seemed to be waiting for a busy day."
    )
    world.say(
        f"{hero.id} loved the campground because every path promised a small quest, "
        f"and the air sometimes smelled appetizing near the picnic table."
    )
    world.para()
    run_world(world, hero, helper, quest, treat)

    world.facts = {
        "hero": hero,
        "helper": helper,
        "quest": quest,
        "treat": treat,
        "params": params,
        "reconciled": hero.memes.get("peace", 0) >= THRESHOLD,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    treat = f["treat"]
    return [
        f'Write a gentle animal story for young children set at a campground with a "reconciliation" turn.',
        f"Tell a story where {hero.id} wants to join a {quest.name} but an {treat.label} becomes tempting, and the friends resolve it kindly.",
        f'Write a simple campground tale that includes the words "pupa", "appetizing", and "quail" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    treat = f["treat"]
    return [
        QAItem(
            question=f"Where does {hero.id}'s story take place?",
            answer=f"It takes place at {world.setting.place}, where the campground paths and picnic table make room for a small quest.",
        ),
        QAItem(
            question=f"Why did {hero.id} pause during the quest?",
            answer=f"{hero.id} paused because the {treat.label} looked appetizing, and the smell made it hard to stay focused on {quest.gerund}.",
        ),
        QAItem(
            question=f"What did {helper.id} do after the mistake?",
            answer=f"{helper.id} stayed calm, offered help, and guided {hero.id} toward reconciliation instead of scolding.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} and {helper.id} were walking together again, and kindness made the campground feel peaceful.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pupa?",
            answer="A pupa is the resting stage of some insects while they change into their grown-up form.",
        ),
        QAItem(
            question="What does appetizing mean?",
            answer="Appetizing means something looks or smells tasty and makes you want to eat it.",
        ),
        QAItem(
            question="What is a quail?",
            answer="A quail is a small bird that lives on the ground and often moves in quick little steps.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means treating others gently, helping them, and choosing care instead of meanness.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement or a hurt feeling.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task done to find something, learn something, or help someone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
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
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{ent.id}: {ent.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
    StoryParams(place="campground", quest="quest", treat="snack", name="Mina", species="rabbit", helper="friend", trait="kind"),
    StoryParams(place="campground", quest="quest", treat="snack", name="Bram", species="fox", helper="ranger", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
