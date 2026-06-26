#!/usr/bin/env python3
"""
storyworlds/worlds/ration_quest_tall_tale.py
============================================

A small Tall Tale storyworld about a Quest that must continue on rations.

Premise:
A bold little traveler sets out on a Quest with a satchel of ration cakes.
The road gets longer than expected, the weather turns, and the traveler must
choose between boasting, sharing, and careful rationing.

This world keeps the simulation simple but state-driven:
- the hero has a physical supply of ration pieces ("meters")
- pride, worry, and cheer are emotional "memes"
- events consume rations, raise or lower morale, and may trigger a rescue
- the ending depends on whether the hero learns to ration wisely and accept help

The prose aims for a Tall Tale feel: a little grand, a little playful, and
grounded in concrete changes to the world state.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACES = {
    "dustroad": {
        "label": "the dust road",
        "features": {"long", "hot", "wide"},
        "quest": True,
    },
    "hills": {
        "label": "the singing hills",
        "features": {"windy", "long"},
        "quest": True,
    },
    "river": {
        "label": "the river crossing",
        "features": {"wet", "wide"},
        "quest": True,
    },
    "canyon": {
        "label": "the canyon path",
        "features": {"long", "echoing"},
        "quest": True,
    },
}

QUESTS = {
    "bridge": {
        "goal": "bring a lantern to the far cottage",
        "risk": "the way may run longer than expected",
        "need": "steady steps and a careful share of ration cakes",
        "tag": "journey",
    },
    "well": {
        "goal": "carry water tokens to the old well-keeper",
        "risk": "the climb may be steeper than it looks",
        "need": "small bites and a brave heart",
        "tag": "travel",
    },
    "bell": {
        "goal": "deliver a brass bell to the hilltop school",
        "risk": "the wind may whistle the day away",
        "need": "enough ration for the last mile",
        "tag": "delivery",
    },
}

RATIONS = {
    "cakes": {
        "label": "oat cakes",
        "singular": "oat cake",
        "bite": "crumb",
        "count_word": "cakes",
    },
    "biscuits": {
        "label": "hard biscuits",
        "singular": "hard biscuit",
        "bite": "bite",
        "count_word": "biscuits",
    },
    "apples": {
        "label": "dried apples",
        "singular": "dried apple",
        "bite": "slice",
        "count_word": "apples",
    },
}

COMPANIONS = {
    "mule": {
        "label": "a mule named Bramble",
        "help": "carried the heaviest pack",
        "tone": "stubborn but kindly",
    },
    "dog": {
        "label": "a dog named Pippin",
        "help": "trotted ahead and found the shade",
        "tone": "bright-eyed and quick",
    },
    "aunt": {
        "label": "an aunt with a laugh like a kettle",
        "help": "kept the satchel from bouncing loose",
        "tone": "merry and practical",
    },
}

HERO_NAMES = ["Milo", "Nia", "Toby", "June", "Otis", "Lena", "Pia", "Eli", "Ruby", "Sage"]
TRAITS = ["bold", "cheerful", "spunky", "stout-hearted", "lively", "pluckish"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    features: set[str] = field(default_factory=set)
    quest: bool = False


@dataclass
class Quest:
    id: str
    goal: str
    risk: str
    need: str
    tag: str


@dataclass
class RationPack:
    id: str
    label: str
    singular: str
    bite: str
    count_word: str


@dataclass
class Companion:
    id: str
    label: str
    help: str
    tone: str


class World:
    def __init__(self, place: Place, quest: Quest, ration: RationPack) -> None:
        self.place = place
        self.quest = quest
        self.ration = ration
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        c = World(self.place, self.quest, self.ration)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    ration: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def quest_needs_ration(quest: Quest, ration: RationPack) -> bool:
    return quest.id in {"bridge", "well", "bell"} and ration.id in RATIONS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        if not place["quest"]:
            continue
        for qid in QUESTS:
            for rid in RATIONS:
                combos.append((pid, qid, rid))
    return combos


def explain_rejection(place: str, quest: str, ration: str) -> str:
    return (
        f"(No story: the quest '{quest}' at '{place}' cannot use ration '{ration}' "
        f"in a sensible way.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------

def opening_line(hero: Entity, trait: str, quest: Quest, place: Place) -> str:
    return (
        f"Once there was a {trait} {hero.type} named {hero.id}, and {hero.id} had a Quest "
        f"as tall as a telephone pole: {quest.goal}. Off {hero.pronoun('possessive')} went "
        f"toward {place.label}."
    )


def tall_tale_flourish(place: Place, quest: Quest) -> str:
    if "hot" in place.features:
        return "The sun sat over the road like a brass skillet, and the dust jumped up at every bootstep."
    if "wet" in place.features:
        return "The water flashed and sparkled so hard it looked like the river had swallowed the sky."
    if "windy" in place.features:
        return "The wind blew so strong it could have combed a coyote's whiskers straight."
    return "The road stretched on with more swagger than a carnival drum."


def needs_line(quest: Quest, ration: RationPack) -> str:
    return f"This Quest needed {quest.need}, and the pack held {ration.label} packed neat as fence posts."


def consume_ration(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.meters["ration"] = max(0.0, hero.meters.get("ration", 0.0) - amount)
    if hero.meters["ration"] <= THRESHOLD:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.trace.append(f"{hero.id} ration -> {hero.meters['ration']}")


def boasted_too_big(hero: Entity, world: World) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 0.5
    world.say(
        f"{hero.id} patted {hero.pronoun('possessive')} satchel and bragged that "
        f"{hero.pronoun()} could cross the whole world on a nibble and a grin."
    )


def share_with_companion(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1.0
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.5)
    world.say(
        f"Then {hero.id} shared a careful bite with {companion.id}, and that made the trail feel less lonesome."
    )


def emergency_help(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1.0
    world.say(
        f"{companion.id} {companion.phrase if False else companion.label} {companion.id and 'came along'}"
    )


def enter_midday(world: World, hero: Entity, place: Place, quest: Quest) -> None:
    world.para()
    world.say(
        f"By midday, {place.label} had grown long in the leg and sly in the shade."
    )
    world.say(tall_tale_flourish(place, quest))


def run_short(world: World, hero: Entity, companion: Entity) -> None:
    if hero.meters.get("ration", 0.0) <= 1.0:
        hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
        world.say(
            f"{hero.id}'s satchel began to feel as light as a feather pillow, and the stomach rumbles got louder than a wash tub."
        )


def turn_and_fix(world: World, hero: Entity, companion: Entity, ration: RationPack) -> bool:
    if hero.meters.get("ration", 0.0) > 1.0:
        return False
    hero.memes["humility"] = hero.memes.get("humility", 0.0) + 1.0
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 1.0)
    world.say(
        f"At last, {hero.id} stopped strutting and counted the last {ration.bite} in {hero.pronoun('possessive')} hand."
    )
    world.say(
        f"{hero.id} shared the last little ration with {companion.id}, and {companion.id} {companion.phrase if False else 'pointed'}"
    )
    return True


def ending_image(world: World, hero: Entity, place: Place, quest: Quest) -> None:
    hero.memes["contentment"] = hero.memes.get("contentment", 0.0) + 1.0
    world.say(
        f"Before long, {hero.id} reached the end of {place.label}, and {quest.goal} was done at last."
    )
    world.say(
        f"{hero.id} stood a little taller, not because the pack was heavy, but because {hero.id} had learned how to make a ration last."
    )


# ---------------------------------------------------------------------------
# Tell the story
# ---------------------------------------------------------------------------

def tell(place: Place, quest: Quest, ration: RationPack, hero_name: str, hero_type: str,
         hero_trait: str, companion: Companion) -> World:
    world = World(place, quest, ration)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"ration": 3.0},
        memes={"pride": 1.0},
    ))
    sidekick = world.add(Entity(
        id="Companion",
        kind="character",
        type="companion",
        label=companion.label,
    ))

    world.say(opening_line(hero, hero_trait, quest, place))
    world.say(needs_line(quest, ration))
    world.say(
        f"Along the way went {companion.label}, who was {companion.tone} and {companion.help}."
    )

    world.para()
    world.say(f"{quest.risk.capitalize()}.")
    world.say(
        f"{hero.id} marched on anyway, and every mile took one careful mouthful from {hero.pronoun('possessive')} ration."
    )
    consume_ration(world, hero, 1.0)
    boasted_too_big(hero, world)

    enter_midday(world, hero, place, quest)
    consume_ration(world, hero, 1.0)
    run_short(world, hero, sidekick)

    if hero.meters.get("ration", 0.0) <= 1.0:
        world.para()
        world.say(
            f"That was when {hero.id} admitted the truth: no one, not even the tallest tale-teller in the county, can out-talk an empty belly."
        )
        world.say(
            f"{companion.id} came closer, and together they counted the crumbs."
        )
        world.say(
            f"{hero.id} chose to ration the rest instead of gobbling it all at once."
        )
        if turn_and_fix(world, hero, sidekick, ration):
            world.say(
                f"The road seemed shorter after that, and the two of them went on with steadier steps."
            )

    world.para()
    ending_image(world, hero, place, quest)

    world.facts.update(
        hero=hero,
        companion=sidekick,
        place=place,
        quest=quest,
        ration=ration,
        resolved=True,
        ration_left=hero.meters.get("ration", 0.0),
    )
    return world


# ---------------------------------------------------------------------------
# Registries and sample generation
# ---------------------------------------------------------------------------

PLACE_REGISTRY = {k: Place(id=k, label=v["label"], features=set(v["features"]), quest=v["quest"]) for k, v in PLACES.items()}
QUEST_REGISTRY = {k: Quest(id=k, goal=v["goal"], risk=v["risk"], need=v["need"], tag=v["tag"]) for k, v in QUESTS.items()}
RATION_REGISTRY = {k: RationPack(id=k, label=v["label"], singular=v["singular"], bite=v["bite"], count_word=v["count_word"]) for k, v in RATIONS.items()}
COMPANION_REGISTRY = {k: Companion(id=k, label=v["label"], help=v["help"], tone=v["tone"]) for k, v in COMPANIONS.items()}

GIRL_NAMES = ["Lily", "Mina", "Zora", "Nell", "Ruby", "Tia"]
BOY_NAMES = ["Bo", "Alec", "Rory", "Finn", "Tate", "Ollie"]
TRAITS = ["bold", "cheerful", "stout-hearted", "spunky", "lively"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    place: Place = f["place"]
    ration: RationPack = f["ration"]
    return [
        f'Write a Tall Tale about a little {hero.type} named {hero.id} who goes on a Quest at {place.label} with some {ration.label}.',
        f"Tell a playful story where {hero.id} must learn to ration {ration.label} while completing a great Quest.",
        f"Write a short child-friendly Tall Tale that includes the word 'ration' and ends with {hero.id} using {quest.goal}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    place: Place = f["place"]
    quest: Quest = f["quest"]
    ration: RationPack = f["ration"]
    left = f["ration_left"]
    return [
        QAItem(
            question=f"What was {hero.id}'s Quest?",
            answer=f"{hero.id} was trying to {quest.goal}. The journey took place at {place.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry for the journey?",
            answer=f"{hero.id} carried {ration.label} so there would be something to eat on the road.",
        ),
        QAItem(
            question=f"Who helped {hero.id} along the way?",
            answer=f"{companion.id} helped by {companion.label.lower() if companion.label else companion.id}. {companion.help.capitalize()}.",
        ),
        QAItem(
            question=f"What changed about the ration by the end?",
            answer=f"The ration got smaller during the Quest, and {hero.id} had only about {left:g} units left by the end.",
        ),
        QAItem(
            question=f"Why did {hero.id} have to be careful with the ration?",
            answer=f"{quest.risk.capitalize()}, so {hero.id} needed to ration the food instead of eating it too quickly.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to ration something?",
            answer="To ration something means to use it a little at a time so it lasts longer.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or mission to do something important or hard.",
        ),
        QAItem(
            question="Why do travelers carry food on a long trip?",
            answer="Travelers carry food so they can keep their strength up when the road is far away.",
        ),
    ]


# ---------------------------------------------------------------------------
# Trace / formatting
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.extend(f"  trace: {t}" for t in world.trace)
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- place_fact(P).
quest(Q) :- quest_fact(Q).
ration(R) :- ration_fact(R).
valid(P,Q,R) :- place(P), quest(Q), ration(R), quest_needs_ration(Q,R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest_fact", qid))
    for rid in RATIONS:
        lines.append(asp.fact("ration_fact", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall Tale quest world with rationing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--ration", choices=RATIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=COMPANIONS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.ration:
        combos = [c for c in combos if c[2] == args.ration]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, quest, ration = rng.choice(combos)
    quest_obj = QUEST_REGISTRY[quest]
    ration_obj = RATION_REGISTRY[ration]
    if not quest_needs_ration(quest_obj, ration_obj):
        raise StoryError(explain_rejection(place, quest, ration))

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(list(COMPANION_REGISTRY))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        quest=quest,
        ration=ration,
        name=name,
        gender=gender,
        companion=companion,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACE_REGISTRY[params.place]
    quest = QUEST_REGISTRY[params.quest]
    ration = RATION_REGISTRY[params.ration]
    companion = COMPANION_REGISTRY[params.companion]
    hero_type = params.gender
    world = tell(place, quest, ration, params.name, hero_type, params.trait, companion)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="dustroad", quest="bridge", ration="cakes", name="Milo", gender="boy", companion="mule", trait="bold"),
            StoryParams(place="hills", quest="well", ration="biscuits", name="Nia", gender="girl", companion="dog", trait="cheerful"),
            StoryParams(place="canyon", quest="bell", ration="apples", name="Ruby", gender="girl", companion="aunt", trait="stout-hearted"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
