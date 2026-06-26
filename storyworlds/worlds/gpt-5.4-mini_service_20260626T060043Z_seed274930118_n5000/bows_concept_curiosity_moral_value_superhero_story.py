#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bows_concept_curiosity_moral_value_superhero_story.py
================================================================================================

A compact superhero-style storyworld about a curious young hero, a valuable
idea, and a bow-powered solution.

Seed tale sketch:
---
A child superhero loved asking questions about everything in the city. One day
they found a clever concept for helping people with bright ribbon bows, but a
villain tried to steal the idea and use it for selfish praise. The hero had to
choose whether to boast, hide the concept, or share it wisely. By listening,
testing, and explaining the moral value of helping others, the hero protected
the idea and used the bows to make a small rescue plan that worked.
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Concept:
    name: str
    phrase: str
    delight: str
    at_risk_with: set[str]
    moral_axis: str
    keyword: str = "concept"


@dataclass
class Bows:
    id: str
    label: str
    phrase: str
    color: str
    helps: set[str]
    style: str
    plural: bool = True


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy

        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


THRESHOLD = 1.0


def _hero_curiosity(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero_id"])
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    key = ("curious", hero.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    out.append(f"{hero.label} kept looking closely, because every clue felt like a door to open.")
    return out


def _villain_stir(world: World) -> list[str]:
    out = []
    villain = world.get(world.facts["villain_id"])
    concept = world.get(world.facts["concept_id"])
    if villain.memes.get("greed", 0) < THRESHOLD:
        return out
    key = ("stir", villain.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    concept.meters["risk"] = concept.meters.get("risk", 0) + 1
    out.append(f"{villain.label} reached for the {concept.label} and called it their own clever trick.")
    return out


def _moral_turn(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero_id"])
    concept = world.get(world.facts["concept_id"])
    if concept.meters.get("risk", 0) < THRESHOLD or hero.memes.get("moral_value", 0) < THRESHOLD:
        return out
    key = ("moral", hero.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
    out.append(f"{hero.label} remembered that a good idea is worth more when it helps people.")
    return out


def _bow_fix(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero_id"])
    concept = world.get(world.facts["concept_id"])
    bows = world.get(world.facts["bows_id"])
    if concept.meters.get("risk", 0) < THRESHOLD or hero.memes.get("resolve", 0) < THRESHOLD:
        return out
    key = ("bows", hero.id)
    if key in world.fired:
        return out
    world.fired.add(key)
    concept.meters["protected"] = concept.meters.get("protected", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    out.append(f"{hero.label} tied the {bows.label} into a bright signal so neighbors could follow the plan.")
    return out


RULES = [_hero_curiosity, _villain_stir, _moral_turn, _bow_fix]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule(world)
            if lines:
                changed = True
                for line in lines:
                    world.say(line)


def build_story(world: World) -> None:
    hero = world.get(world.facts["hero_id"])
    mentor = world.get(world.facts["mentor_id"])
    villain = world.get(world.facts["villain_id"])
    concept = world.get(world.facts["concept_id"])
    bows = world.get(world.facts["bows_id"])

    world.say(f"In {world.place.name}, {hero.label} was a young hero who was famous for asking questions.")
    world.say(f"{hero.label} loved the way new ideas could change a city, and {hero.pronoun('subject')} especially loved the {concept.phrase}.")
    world.say(f"{mentor.label} said the {concept.label} had real moral value, because it could help people instead of show off.")
    world.say(f"One bright afternoon, {hero.label} found {bows.phrase} near the rooftop lab and thought they matched the {concept.label} perfectly.")

    world.say(f"Then {villain.label} appeared and tried to snatch the {concept.label} for selfish praise.")
    hero.memes["curiosity"] = 1.0
    villain.memes["greed"] = 1.0
    hero.memes["moral_value"] = 1.0

    propagate(world)

    if concept.meters.get("protected", 0) >= THRESHOLD:
        world.say(f"{hero.label} explained the concept to the crowd, used the {bows.label}, and turned the theft into a rescue.")
        world.say(f"By the end, the city cheered, the {concept.label} stayed safe, and {hero.label} learned that curiosity is strongest when it serves others.")
    else:
        world.say(f"{hero.label} thought hard, but the idea was never fully protected, so the day ended with a quiet warning to try again tomorrow.")


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    mentor: str
    mentor_type: str
    villain: str
    villain_type: str
    concept: str
    bows: str
    seed: Optional[int] = None


PLACES = {
    "city": Place("the city", "busy", {"rescue", "riddle", "signal"}),
    "rooftop": Place("the rooftop lab", "windy", {"rescue", "signal"}),
    "museum": Place("the museum district", "quiet", {"rescue", "exhibit"}),
    "subway": Place("the subway station", "echoing", {"rescue", "signal"}),
}

CONCEPTS = {
    "signal_plan": Concept(
        name="signal_plan",
        phrase="a clever rescue concept",
        delight="it could help people find the safe path",
        at_risk_with={"greed", "showing off"},
        moral_axis="helping others",
        keyword="concept",
    ),
    "bridge_map": Concept(
        name="bridge_map",
        phrase="a new bridge map concept",
        delight="it could guide lost neighbors home",
        at_risk_with={"greed", "pride"},
        moral_axis="sharing wisely",
        keyword="concept",
    ),
    "kind_code": Concept(
        name="kind_code",
        phrase="a kind code concept",
        delight="it could let friends ask for help without fear",
        at_risk_with={"greed", "teasing"},
        moral_axis="care and honesty",
        keyword="concept",
    ),
}

BOWS = {
    "red_bows": Bows("red_bows", "red ribbon bows", "bright red ribbon bows", "red", {"signal", "rescue"}, "flashy"),
    "blue_bows": Bows("blue_bows", "blue ribbon bows", "bright blue ribbon bows", "blue", {"signal", "exhibit"}, "calm"),
    "gold_bows": Bows("gold_bows", "gold ribbon bows", "shiny gold ribbon bows", "gold", {"rescue", "signal"}, "heroic"),
}

HERO_NAMES = ["Nova", "Skye", "Piper", "Milo", "Zuri", "Ivy", "Jun", "Aria"]
MENTOR_NAMES = ["Captain Sage", "Aunt Lantern", "Professor Halo", "Mayor Bright"]
VILLAIN_NAMES = ["Dr. Mirthless", "Shade Sparrow", "Count Cinder", "Murmur Mask"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for concept in CONCEPTS.values():
            for bows in BOWS.values():
                if any(tok in place.affords for tok in concept.at_risk_with) or "signal" in place.affords:
                    if bows.helps & place.affords:
                        out.append((place.name, concept.name, bows.id))
    return out


def choose_name(rng: random.Random, pool: list[str]) -> str:
    return rng.choice(pool)


def build_world(params: StoryParams) -> World:
    place = next(p for p in PLACES.values() if p.name == params.place)
    concept = CONCEPTS[params.concept]
    bows = BOWS[params.bows]

    world = World(place)
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_type, label=params.hero))
    mentor = world.add(Entity(params.mentor, kind="character", type=params.mentor_type, label=params.mentor))
    villain = world.add(Entity(params.villain, kind="character", type=params.villain_type, label=params.villain))
    concept_ent = world.add(Entity(concept.name, label="concept", phrase=concept.phrase))
    bows_ent = world.add(Entity(bows.id, label="bows", phrase=bows.phrase, plural=True))

    world.facts.update(
        hero_id=hero.id,
        mentor_id=mentor.id,
        villain_id=villain.id,
        concept_id=concept_ent.id,
        bows_id=bows_ent.id,
        place=params.place,
        concept=params.concept,
        bows=params.bows,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    build_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.get(world.facts["hero_id"])
    mentor = world.get(world.facts["mentor_id"])
    villain = world.get(world.facts["villain_id"])
    concept = world.get(world.facts["concept_id"])
    bows = world.get(world.facts["bows_id"])
    return [
        f'Write a short superhero story for a small child about {hero.label}, curiosity, and a useful {concept.label}.',
        f"Tell a moral-value story where {villain.label} tries to steal a {concept.label}, but {hero.label} protects it with {bows.phrase}.",
        f'Write a gentle superhero tale that includes the word "concept" and ends with a city being helped by a brave choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get(world.facts["hero_id"])
    mentor = world.get(world.facts["mentor_id"])
    villain = world.get(world.facts["villain_id"])
    concept = world.get(world.facts["concept_id"])
    bows = world.get(world.facts["bows_id"])
    return [
        QAItem(
            question=f"Who was the curious superhero in the story?",
            answer=f"The curious superhero was {hero.label}, who kept asking questions and looking for good ideas.",
        ),
        QAItem(
            question=f"Why did {mentor.label} say the {concept.label} mattered?",
            answer=f"{mentor.label} said it had moral value because it could help people instead of being used just for praise.",
        ),
        QAItem(
            question=f"What did {villain.label} try to take?",
            answer=f"{villain.label} tried to take the {concept.phrase} for selfish praise.",
        ),
        QAItem(
            question=f"How did {hero.label} use the {bows.label} at the end?",
            answer=f"{hero.label} used the {bows.phrase} as a bright signal to protect the idea and help the rescue plan work.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What does curiosity mean?",
        answer="Curiosity means wanting to learn more by asking questions, looking closely, and wondering how things work.",
    ),
    QAItem(
        question="What is moral value?",
        answer="Moral value is what makes a choice good or right, especially when it helps other people and shows care.",
    ),
    QAItem(
        question="What are bows often used for?",
        answer="Bows are often used to decorate things, tie things together, or make something look bright and special.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
hero_curious(H) :- hero(H), curiosity(H).
villain_greedy(V) :- villain(V), greed(V).
concept_at_risk(C) :- concept(C), risk(C).
moral_turn(H) :- hero(H), moral_value(H), concept_at_risk(_).
protects_better(B) :- bows(B), helps_signal(B).
good_story(P,C,B) :- place(P), concept(C), bows(B), protects_better(B).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.name))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", p.name, a))
    for c in CONCEPTS.values():
        lines.append(asp.fact("concept", c.name))
        for r in sorted(c.at_risk_with):
            lines.append(asp.fact("risk_with", c.name, r))
    for b in BOWS.values():
        lines.append(asp.fact("bows", b.id))
        for h in sorted(b.helps):
            lines.append(asp.fact("helps_signal", b.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld about curiosity, moral value, and bows.")
    ap.add_argument("--place", choices=[p for p in PLACES])
    ap.add_argument("--concept", choices=[c for c in CONCEPTS])
    ap.add_argument("--bows", choices=[b for b in BOWS])
    ap.add_argument("--name")
    ap.add_argument("--mentor")
    ap.add_argument("--villain")
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
    combos = valid_combos()
    if args.place and args.concept and args.bows:
        if (args.place, args.concept, args.bows) not in combos:
            raise StoryError("That combination does not make a reasonable superhero story.")
    choices = [c for c in combos if (not args.place or c[0] == args.place) and (not args.concept or c[1] == args.concept) and (not args.bows or c[2] == args.bows)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, concept, bows = rng.choice(choices)
    hero = args.name or choose_name(rng, HERO_NAMES)
    mentor = args.mentor or choose_name(rng, MENTOR_NAMES)
    villain = args.villain or choose_name(rng, VILLAIN_NAMES)
    hero_type = rng.choice(["girl", "boy"])
    mentor_type = rng.choice(["woman", "man"])
    villain_type = rng.choice(["woman", "man"])
    return StoryParams(place, hero, hero_type, mentor, mentor_type, villain, villain_type, concept, bows)


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


CURATED = [
    StoryParams("the city", "Nova", "girl", "Captain Sage", "woman", "Dr. Mirthless", "man", "signal_plan", "red_bows"),
    StoryParams("the rooftop lab", "Skye", "boy", "Professor Halo", "man", "Shade Sparrow", "woman", "bridge_map", "gold_bows"),
    StoryParams("the subway station", "Piper", "girl", "Aunt Lantern", "woman", "Count Cinder", "man", "kind_code", "blue_bows"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, concept, bows) combos:")
        for place, concept, bows in combos:
            print(f"  {place:18} {concept:14} {bows}")
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
            header = f"### {p.name}: {p.concept} at {p.place} (bows: {p.bows})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
