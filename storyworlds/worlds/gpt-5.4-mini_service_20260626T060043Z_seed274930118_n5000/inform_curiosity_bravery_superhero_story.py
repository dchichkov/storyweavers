#!/usr/bin/env python3
"""
A small superhero storyworld about a curious hero whose bravery helps them
inform others before a big problem turns into a rescue.

Premise:
- A young superhero notices something odd in the city.
- Their curiosity makes them investigate instead of ignoring it.
- Their bravery helps them act when the problem becomes real.
- They inform the right helper, team up, and save the day.

The story generator keeps the world state concrete:
- meters track physical conditions like stuck, blocked, cracked, and packed
- memes track emotions like curiosity, bravery, worry, and trust

This world intentionally supports a small, tightly constrained set of
story shapes, all centered on curiosity, bravery, and informing.
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


THRESHOLD = 1.0


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
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class City:
    place: str = "Star City"
    zone: str = "the museum street"
    affords: set[str] = field(default_factory=set)


@dataclass
class HeroProfile:
    name: str
    gender: str
    trait: str
    suit: str
    helper: str


@dataclass
class StoryParams:
    place: str
    event: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


EVENTS = {
    "smoke": {
        "label": "smoke on the roof",
        "problem": "smoky",
        "risk": "smoke",
        "verb": "check the roof",
        "curiosity": "peeked toward the roof",
        "investigate": "fly up to the roof",
        "soil": "smoky",
        "zone": {"air"},
        "need": "inform the fire crew",
        "rescue": "open the vent",
    },
    "rubble": {
        "label": "rubble near the bridge",
        "problem": "blocked",
        "risk": "rubble",
        "verb": "look under the bridge",
        "curiosity": "noticed the bridge shaking",
        "investigate": "fly to the bridge",
        "soil": "blocked",
        "zone": {"path"},
        "need": "inform the rescue team",
        "rescue": "clear the path",
    },
    "kite": {
        "label": "a kite stuck in a tall tree",
        "problem": "stuck",
        "risk": "stuck",
        "verb": "look at the tree",
        "curiosity": "spotted something high in the branches",
        "investigate": "climb closer",
        "soil": "stuck",
        "zone": {"branches"},
        "need": "inform the park helper",
        "rescue": "reach the kite",
    },
    "parcel": {
        "label": "a lost parcel on the sidewalk",
        "problem": "missing",
        "risk": "missing",
        "verb": "check the sidewalk",
        "curiosity": "noticed a dropped package",
        "investigate": "go see it",
        "soil": "missing",
        "zone": {"ground"},
        "need": "inform the delivery helper",
        "rescue": "bring it back",
    },
}

TOOLS = {
    "mask": {"label": "a bright mask", "protects": {"smoke"}},
    "gloves": {"label": "strong gloves", "protects": {"rubble"}},
    "rope": {"label": "a rescue rope", "protects": {"stuck"}},
    "satchel": {"label": "a messenger satchel", "protects": {"missing"}},
}

HELPERS = {
    "fire crew": "the fire crew",
    "rescue team": "the rescue team",
    "park helper": "the park helper",
    "delivery helper": "the delivery helper",
}

GIRL_NAMES = ["Maya", "Luna", "Zoe", "Ivy", "Nora", "Tia"]
BOY_NAMES = ["Eli", "Kai", "Milo", "Theo", "Finn", "Noah"]
TRAITS = ["curious", "brave", "bold", "quick", "gentle", "alert"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in CITY_REGISTRY:
        for event in EVENTS:
            for tool in TOOLS:
                if event in TOOLS[tool]["protects"]:
                    out.append((place, event, tool))
    return out


@dataclass
class StoryWorldModel:
    city: City
    hero: Entity
    helper: Entity
    tool: Entity
    event: dict


def _do_event(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    event = world.facts["event"]
    hero.meters[event["problem"]] = hero.meters.get(event["problem"], 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    if narrate:
        world.say(f"{hero.id} {event['curiosity']}.")


def _inform(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    event = world.facts["event"]
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    world.facts["informed"] = True
    if narrate:
        world.say(
            f"{hero.id} hurried back and informed {helper.id} about {event['label']}."
        )


def _rescue(world: World, narrate: bool = True) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    event = world.facts["event"]
    tool = world.get("tool")
    hero.meters[event["problem"]] = 0
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    if narrate:
        world.say(
            f"With {tool.label}, {hero.id} and {helper.id} worked together to {event['rescue']}."
        )


def tell(city: City, event_key: str, profile: HeroProfile) -> World:
    world = World(city)
    event = EVENTS[event_key]

    hero = world.add(Entity(id="hero", kind="character", type=profile.gender, label=profile.name))
    helper = world.add(Entity(id="helper", kind="character", type="person", label=profile.helper))
    tool_key = next(k for k, v in TOOLS.items() if event_key in v["protects"])
    tool = world.add(Entity(id="tool", type="thing", label=TOOLS[tool_key]["label"]))
    world.facts["event"] = event
    world.facts["tool_key"] = tool_key

    hero.memes["curiosity"] = 1.0
    hero.memes["bravery"] = 0.0

    world.say(
        f"{profile.name} was a {profile.trait} superhero who patrolled {city.place} with a bright smile."
    )
    world.say(
        f"{profile.name} loved to stay curious, because curiosity helped {hero.pronoun('object')} notice trouble early."
    )

    world.para()
    world.say(
        f"One afternoon at {city.zone}, {profile.name} {event['curiosity']}."
    )
    _do_event(world, narrate=True)
    world.say(
        f"{profile.name} wanted to {event['verb']}, but first {hero.pronoun('subject')} chose to inform {profile.helper}."
    )
    _inform(world, narrate=True)

    world.para()
    world.say(
        f"{profile.helper} listened right away, and that made {profile.name} feel brave."
    )
    _rescue(world, narrate=True)
    world.say(
        f"In the end, {profile.name} stood tall in {city.zone}, glad that curiosity and bravery had helped save the day."
    )

    world.facts.update(hero=hero, helper=helper, tool=tool, profile=profile, city=city)
    return world


CITY_REGISTRY = [
    "Star City",
    "Nova Harbor",
    "Cloudport",
]

CITY_BY_NAME = {name: City(place=name, zone="the museum street", affords=set(EVENTS)) for name in CITY_REGISTRY}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    profile: HeroProfile = f["profile"]
    event = f["event"]
    return [
        f'Write a short superhero story for a child where {profile.name} uses curiosity to notice {event["label"]}.',
        f"Tell a brave story about {profile.name} informing {profile.helper} before helping fix a city problem.",
        f'Write a simple superhero tale that uses the word "inform" and ends with a rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    profile: HeroProfile = f["profile"]
    event = f["event"]
    helper = profile.helper
    return [
        QAItem(
            question=f"Why did {profile.name} go to {world.city.zone}?",
            answer=f"{profile.name} went there because curiosity led {profile.hero.pronoun('object')} to notice {event['label']}."
        ),
        QAItem(
            question=f"What did {profile.name} do before the rescue?",
            answer=f"Before the rescue, {profile.name} informed {helper} about the problem."
        ),
        QAItem(
            question=f"How did {profile.name} feel when the helper listened?",
            answer=f"{profile.name} felt brave, because being heard made the next step feel safe."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to inform someone?",
            answer="To inform someone means to tell them important information so they can help or know what is happening."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to learn more, look closer, and ask questions."
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing the right thing even when something feels scary or hard."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)} label={e.label}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
event_problem(E, P) :- event(E), problem(E, P).
tool_fits(T, E) :- tool(T), event(E), protects(T, E).
valid_story(City, E, T) :- city(City), event(E), tool(T), tool_fits(T, E).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CITY_REGISTRY:
        lines.append(asp.fact("city", c))
    for e in EVENTS:
        lines.append(asp.fact("event", e))
        lines.append(asp.fact("problem", e, EVENTS[e]["problem"]))
    for t, info in TOOLS.items():
        lines.append(asp.fact("tool", t))
        for p in info["protects"]:
            lines.append(asp.fact("protects", t, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(event_key: str, tool_key: str) -> str:
    return (
        f"(No story: the chosen tool '{tool_key}' does not fit the problem '{event_key}'. "
        f"The hero must have a tool that truly helps before the informed rescue can happen.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero storyworld about curiosity, bravery, and informing others."
    )
    ap.add_argument("--place", choices=CITY_REGISTRY)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    event = args.event or rng.choice(list(EVENTS))
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(CITY_REGISTRY)
    return StoryParams(place=place, event=event, helper=helper, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    city = CITY_BY_NAME[params.place]
    profile = HeroProfile(
        name=params.name,
        gender=params.gender,
        trait=params.trait,
        suit="bright suit",
        helper=HELPERS[params.helper],
    )
    world = tell(city, params.event, profile)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in CITY_REGISTRY:
            for event in EVENTS:
                for helper in HELPERS:
                    params = StoryParams(place=place, event=event, helper=helper, name="Maya", gender="girl", trait="curious")
                    samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
