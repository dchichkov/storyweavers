#!/usr/bin/env python3
"""
storyworlds/worlds/boat_quest_heartwarming.py
=============================================

A small heartwarming storyworld about a boat trip and a gentle quest.

Premise:
A child, guardian, and a little boat set out on a short quest to return or
deliver something important across the water. The quest can run into a simple
problem: the river path is wide, the wind is chilly, or a needed item is missing.

Tension:
The hero worries the trip may fail, or that someone waiting on the far shore may
be disappointed.

Turn:
A kind helper, practical gear, or a clever plan makes the quest possible.

Resolution:
The boat reaches the right place, the important thing is delivered or returned,
and everyone feels warmer and happier than before.

The world is intentionally small and constraint-checked: every generated story is
meant to read like a complete, gentle TinyStories-style scene.
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
# Core model
# ---------------------------------------------------------------------------

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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    water: bool = False
    breezy: bool = False
    warm: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    region: str
    precious: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps_with: set[str] = field(default_factory=set)
    warmth: bool = False
    cover: set[str] = field(default_factory=set)
    prep: str = ""
    closing: str = ""


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "river": Place(name="the river", water=True, breezy=True, affords={"deliver", "rescue"}),
    "lake": Place(name="the lake", water=True, breezy=False, affords={"deliver", "find"}),
    "harbor": Place(name="the harbor", water=True, breezy=True, affords={"deliver", "find"}),
}

QUESTS = {
    "deliver_lunch": {
        "verb": "deliver lunch",
        "gerund": "delivering lunch",
        "goal": "bring lunch to the other shore",
        "risk": "the lunch could get cold",
        "turn": "a warm basket",
        "success": "the lunch stayed warm",
        "tags": {"deliver", "warm"},
    },
    "return_hat": {
        "verb": "return a missing hat",
        "gerund": "carrying the missing hat",
        "goal": "take the hat back to its owner",
        "risk": "the hat could blow away",
        "turn": "a snug ribbon",
        "success": "the hat stayed safe",
        "tags": {"find", "return"},
    },
    "visit_friend": {
        "verb": "visit a friend",
        "gerund": "sailing to see a friend",
        "goal": "reach a friend on the far shore",
        "risk": "the trip might feel long and lonely",
        "turn": "a cheerful song",
        "success": "the trip felt shorter and brighter",
        "tags": {"find", "deliver", "kind"},
    },
}

PRIZES = {
    "basket": QuestItem(
        id="basket",
        label="basket",
        phrase="a little lunch basket",
        region="hands",
    ),
    "hat": QuestItem(
        id="hat",
        label="hat",
        phrase="a soft blue hat",
        region="head",
    ),
    "letter": QuestItem(
        id="letter",
        label="letter",
        phrase="a folded paper letter",
        region="hands",
    ),
}

GEAR = {
    "blanket": Gear(
        id="blanket",
        label="blanket",
        phrase="a warm blanket",
        helps_with={"warm"},
        warmth=True,
        cover={"legs", "shoulders"},
        prep="wrap up in a warm blanket first",
        closing="snuggled under the blanket",
    ),
    "ribbon": Gear(
        id="ribbon",
        label="ribbon",
        phrase="a snug ribbon",
        helps_with={"return", "find"},
        warmth=False,
        cover={"head"},
        prep="tie on a snug ribbon first",
        closing="kept the hat tied safely",
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        helps_with={"find", "deliver", "kind"},
        warmth=False,
        cover=set(),
        prep="take a little lantern along",
        closing="lit the way across the water",
    ),
}

NAMES_GIRL = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella"]
NAMES_BOY = ["Leo", "Ben", "Theo", "Finn", "Noah", "Jack"]
TRAITS = ["gentle", "curious", "cheerful", "patient", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for quest_id, q in QUESTS.items():
            if q["verb"] == "return a missing hat":
                prize_id = "hat"
            elif q["verb"] == "deliver lunch":
                prize_id = "basket"
            else:
                prize_id = "letter"
            if "deliver" in place.affords or "find" in place.affords or "rescue" in place.affords:
                out.append((place_id, quest_id, prize_id))
    return out


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def boat_sentence(hero: Entity, helper: Entity, place: Place) -> str:
    return f"{hero.id} and {helper.id} climbed into a little boat on {place.name}."


def introduce(world: World, hero: Entity, helper: Entity, quest: dict, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'kind')} {hero.type} who loved a good Quest."
    )
    world.say(
        f"{hero.id} and {helper.id} had a special Quest: {quest['goal']} with {prize.phrase}."
    )
    world.say(
        f"{hero.id} cared about {prize.label} because it was important to someone waiting on the far shore."
    )


def tension(world: World, hero: Entity, helper: Entity, quest: dict) -> None:
    world.para()
    world.say(boat_sentence(hero, helper, world.place))
    if world.place.breezy:
        world.say(
            f"The breeze tugged at their hair, and {hero.id} worried the small boat might wobble."
        )
    else:
        world.say(
            f"The water looked calm, but {hero.id} still worried the trip might take too long."
        )
    world.say(
        f"{hero.id} whispered that {quest['risk']}."
    )


def resolve(world: World, hero: Entity, helper: Entity, quest: dict, prize: Entity, gear: Optional[Gear]) -> None:
    world.para()
    if gear is not None:
        if gear.id == "lantern":
            world.say(
                f"{helper.id} smiled and said they could {gear.prep}, so the boat would not lose its way."
            )
        else:
            world.say(
                f"{helper.id} had a careful plan: they could {gear.prep} before setting off."
            )
        world.say(
            f"{hero.id} nodded, and that made the Quest feel possible."
        )
    else:
        world.say(
            f"{helper.id} took a steady breath and told {hero.id} they would go slowly together."
        )
    if quest["verb"] == "return a missing hat":
        world.say(
            f"They held the hat close, and the wind could not steal it now."
        )
    elif quest["verb"] == "deliver lunch":
        world.say(
            f"They tucked the lunch basket safely in the middle of the boat, where it stayed warm and snug."
        )
    else:
        world.say(
            f"They followed the soft glow and found the friend waiting with a relieved smile."
        )
    world.say(
        f"When the boat reached the shore, {prize.label} was safe, and {quest['success']}."
    )
    world.say(
        f"{hero.id} smiled because the Quest had become a kind little adventure, not a scary one."
    )


def choose_gear(quest_id: str, prize_id: str) -> Optional[Gear]:
    q = QUESTS[quest_id]
    if quest_id == "deliver_lunch":
        return GEAR["blanket"]
    if quest_id == "return_hat":
        return GEAR["ribbon"]
    if quest_id == "visit_friend":
        return GEAR["lantern"]
    return None


# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

def tell(place: Place, quest_id: str, prize_id: str, hero_name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(place)
    quest = QUESTS[quest_id]
    prize_cfg = PRIZES[prize_id]

    hero = world.add(Entity(id=hero_name, kind="character", type=gender, memes={"trait": trait}))
    helper = world.add(Entity(id=helper_kind, kind="character", type="parent" if helper_kind in {"mom", "dad"} else "adult"))
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg.label, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, quest_id=quest_id, place_id=place.name, prize_cfg=prize_cfg)

    introduce(world, hero, helper, quest, prize)
    tension(world, hero, helper, quest)
    gear = choose_gear(quest_id, prize_id)
    resolve(world, hero, helper, quest, prize, gear)
    world.facts["gear"] = gear
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize_cfg"]
    return [
        f'Write a heartwarming story about a child named {hero.id} on a Quest with a boat.',
        f"Tell a gentle story where {hero.id} wants to {quest['verb']} and a helper makes the trip feel safe.",
        f"Write a short story that includes a boat, a Quest, and {prize.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    prize = f["prize_cfg"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What was {hero.id} doing on the boat?",
            answer=f"{hero.id} was on a Quest to {quest['goal']}, and the important thing was {prize.phrase}.",
        ),
        QAItem(
            question=f"Who went with {hero.id} on the trip?",
            answer=f"{helper.id} went with {hero.id} and helped make the boat trip feel calm and kind.",
        ),
        QAItem(
            question=f"What helped the Quest go well?",
            answer=(
                f"{gear.phrase if gear else 'Their steady plan'} helped keep everyone safe, so the Quest could finish happily."
            ),
        ),
    ]


WORLD_KNOWLEDGE = {
    "boat": QAItem(
        question="What is a boat?",
        answer="A boat is a vehicle that floats on water and can carry people from one shore to another.",
    ),
    "quest": QAItem(
        question="What is a Quest?",
        answer="A Quest is a special trip or mission to find, bring, or help with something important.",
    ),
    "warm": QAItem(
        question="Why do people like blankets on a chilly day?",
        answer="People like blankets because blankets help them stay warm and cozy when the air feels cool.",
    ),
    "ribbon": QAItem(
        question="What does a ribbon do when it is tied securely?",
        answer="A ribbon can hold something in place, like a hat, so it does not slip away.",
    ),
    "lantern": QAItem(
        question="What is a lantern for?",
        answer="A lantern gives off light, which helps people see where they are going in the dark.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [WORLD_KNOWLEDGE["boat"], WORLD_KNOWLEDGE["quest"]]
    gear = f.get("gear")
    if gear and gear.id in WORLD_KNOWLEDGE:
        out.append(WORLD_KNOWLEDGE[gear.id])
    if f["quest_id"] == "deliver_lunch":
        out.append(WORLD_KNOWLEDGE["warm"])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place_valid(P) :- place(P).
quest_valid(Q) :- quest(Q).
story_ok(P,Q,R) :- place_valid(P), quest_valid(Q), prize(R), compatible(P,Q,R).
#show story_ok/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid in PRIZES:
        lines.append(asp.fact("prize", rid))
    for p, q, r in valid_combos():
        lines.append(asp.fact("compatible", p, q, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    clingo_set = set(asp.atoms(model, "story_ok"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming boat Quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mom", "dad", "grandma", "grandpa", "friend"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.prize and gender not in PRIZES[prize].genders:
        raise StoryError("That prize does not fit the requested gender in this world.")
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(["mom", "dad", "grandma", "grandpa", "friend"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.quest, params.prize, params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/3."))
        combos = sorted(set(asp.atoms(model, "story_ok")))
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("river", "deliver_lunch", "basket", "Mia", "girl", "grandma", "gentle"),
            StoryParams("lake", "return_hat", "hat", "Leo", "boy", "dad", "curious"),
            StoryParams("harbor", "visit_friend", "letter", "Nora", "girl", "friend", "kind"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
