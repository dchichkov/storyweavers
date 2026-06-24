#!/usr/bin/env python3
"""
A small superhero-style storyworld about a hero, an amoeba mess, and learning
to say sorry in a stronger, kinder way.

The premise is simple:
- a young superhero tries to help
- an amoeba causes a sticky problem
- the hero makes a mistake
- the hero apology-izes and learns a lesson

This script is self-contained and uses only the standard library for the prose
engine. ASP support is available lazily through storyworlds/asp.py.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class City:
    name: str
    place: str
    indoors: bool = True
    supports: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    name: str
    action: str
    feat: str
    cost: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str] = field(default_factory=set)
    prep: str = ""
    tail: str = ""
    plural: bool = False


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

        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    power: str
    gear: str
    seed: Optional[int] = None


CITY = City(
    name="Metro Bay",
    place="the bright city lab",
    indoors=True,
    supports={"repair", "gather", "clean"},
)

HEROES = {
    "Nova": {"type": "girl", "trait": "brave"},
    "Bolt": {"type": "boy", "trait": "quick"},
    "Mira": {"type": "girl", "trait": "kind"},
    "Dash": {"type": "boy", "trait": "careful"},
}

SIDEKICKS = ["Pip", "Roo", "Tess", "Finn"]

POWERS = {
    "shield": Power(
        id="shield",
        name="shield sparkle",
        action="raise a shield",
        feat="a shining wall that keeps slime away",
        cost="a wobble in the hero's balance",
        tags={"protect", "sparkle"},
    ),
    "sweep": Power(
        id="sweep",
        name="super sweep",
        action="sweep up the goo",
        feat="a fast swirl that clears the floor",
        cost="a puff of tired air",
        tags={"clean", "sweep"},
    ),
    "lift": Power(
        id="lift",
        name="sky lift",
        action="lift the broken crate",
        feat="a strong lift that saves the day",
        cost="a little strain in the arms",
        tags={"lift", "help"},
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="gloves",
        protects={"goo"},
        prep="pull on bright gloves first",
        tail="slipped on the bright gloves",
    ),
    "mask": Gear(
        id="mask",
        label="a clean mask",
        protects={"spores"},
        prep="put on a clean mask",
        tail="put on the clean mask",
    ),
    "boots": Gear(
        id="boots",
        label="boots",
        protects={"goo"},
        prep="lace up sturdy boots",
        tail="laced up the sturdy boots",
    ),
}

AMOEBA = Entity(
    id="amoeba",
    kind="creature",
    type="amoeba",
    label="amoeba",
    phrase="a tiny wobbling amoeba",
)

LESSON_LEARNED = "When you make a mess or hurt a feeling, a quick apology and a helpful fix can make things better."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a superhero, an amoeba, an apology-ize moment, and a lesson learned."
    )
    ap.add_argument("--place", choices=[CITY.place], default=CITY.place)
    ap.add_argument("--hero", choices=sorted(HEROES), default=None)
    ap.add_argument("--sidekick", choices=SIDEKICKS, default=None)
    ap.add_argument("--power", choices=sorted(POWERS), default=None)
    ap.add_argument("--gear", choices=sorted(GEAR), default=None)
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for hero in HEROES:
        for sidekick in SIDEKICKS:
            for power in POWERS:
                for gear in GEAR:
                    combos.append((CITY.place, hero, sidekick, power))
    return combos


def reasonableness_gate(hero: str, power: str, gear: str) -> None:
    if hero not in HEROES:
        raise StoryError("Unknown hero choice.")
    if power not in POWERS:
        raise StoryError("Unknown power choice.")
    if gear not in GEAR:
        raise StoryError("Unknown gear choice.")


def aspiration_world_reasonable(params: StoryParams) -> bool:
    return params.hero in HEROES and params.power in POWERS and params.gear in GEAR


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, pdata in HEROES.items():
        lines.append(asp.fact("hero", pid))
        lines.append(asp.fact("hero_type", pid, pdata["type"]))
    for sid in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    for pow_id, p in POWERS.items():
        lines.append(asp.fact("power", pow_id))
        for t in sorted(p.tags):
            lines.append(asp.fact("power_tag", pow_id, t))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", gid, p))
    lines.append(asp.fact("setting", "city_lab"))
    lines.append(asp.fact("supports", "city_lab", "repair"))
    lines.append(asp.fact("supports", "city_lab", "gather"))
    lines.append(asp.fact("supports", "city_lab", "clean"))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(H, P, G) :- hero(H), power(P), gear(G).
#show compatible/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set((p[1], p[2], p[3]) for p in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates.")
    return 1


def pick(rng: random.Random, xs: list[str]) -> str:
    return rng.choice(xs)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or pick(rng, sorted(HEROES))
    sidekick = args.sidekick or pick(rng, SIDEKICKS)
    power = args.power or pick(rng, sorted(POWERS))
    gear = args.gear or pick(rng, sorted(GEAR))
    reasonableness_gate(hero, power, gear)
    return StoryParams(place=CITY.place, hero=hero, sidekick=sidekick, power=power, gear=gear)


def _say_intro(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"In {world.city.name}, {hero.id} was a {HEROES[hero.id]['trait']} superhero who helped people every day."
    )
    world.say(f"{hero.id} worked with {sidekick.id}, who kept the mission light and cheerful.")


def _say_problem(world: World, hero: Entity) -> None:
    world.say(
        f"One afternoon, the team found a tiny amoeba on a shiny lab tray, and the little creature had left a slippery trail."
    )
    world.say(
        f"{hero.id} wanted to fix the problem fast, but the goo made the floor tricky and the plan got rushed."
    )


def _do_power(world: World, hero: Entity, power: Power) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 1
    world.say(f"{hero.id} tried to {power.action}, but {power.cost} made the first try wobble.")
    if power.id == "sweep":
        world.say("The goo spread a little before the sweep could catch it.")
    elif power.id == "shield":
        world.say("The shield kept part of the room safe, but the hero still bumped a stack of papers.")
    else:
        world.say("The lift saved one crate, but another crate tipped and made the mess bigger.")


def _make_mistake(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    sidekick.memes["hurt"] = sidekick.memes.get("hurt", 0.0) + 1
    world.say(
        f"When the plan slipped, {hero.id} spoke too sharply to {sidekick.id}, and the room felt quiet."
    )


def _apology_ize(world: World, hero: Entity, sidekick: Entity, gear: Gear) -> None:
    hero.memes["remorse"] = hero.memes.get("remorse", 0.0) + 1
    sidekick.memes["hurt"] = max(0.0, sidekick.memes.get("hurt", 0.0) - 1)
    hero.memes["lesson"] = 1.0
    world.say(
        f"Then {hero.id} stopped, took a breath, and decided to apology-ize."
    )
    world.say(
        f'"I am sorry," {hero.id} said. "I rushed and I was unkind. Let me fix this with {gear.label} and help you clean up."'
    )
    world.say(
        f"{hero.id} {gear.tail}, and {sidekick.id} smiled because the apology sounded real."
    )


def _lesson_learned(world: World, hero: Entity) -> None:
    world.say(LESSON_LEARNED)
    world.say(
        f"At the end, {hero.id} was still a superhero, but now {hero.pronoun()} knew a kinder way to act when a job got hard."
    )


def tell(params: StoryParams) -> World:
    world = World(CITY)
    hero = world.add(Entity(id=params.hero, kind="character", type=HEROES[params.hero]["type"]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="child", label=params.sidekick))
    world.add(AMOEBA)
    power = POWERS[params.power]
    gear = GEAR[params.gear]

    _say_intro(world, hero, sidekick)
    world.para()
    _say_problem(world, hero)
    _do_power(world, hero, power)
    _make_mistake(world, hero, sidekick)
    world.para()
    _apology_ize(world, hero, sidekick, gear)
    _lesson_learned(world, hero)

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        power=power,
        gear=gear,
        lesson=LESSON_LEARNED,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    power = f["power"]
    gear = f["gear"]
    return [
        'Write a short superhero story for a young child that includes an amoeba and the word "apology-ize".',
        f"Tell a kind superhero story where {hero.id} tries to {power.action} but must apology-ize after making a mistake.",
        f"Write a story about {hero.id}, a tiny amoeba mess, and a lesson learned, ending with {gear.label} helping the cleanup.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    power = f["power"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, who was trying to help in Metro Bay.",
        ),
        QAItem(
            question=f"What caused the slippery problem?",
            answer="A tiny amoeba left a slippery trail on the lab tray and floor.",
        ),
        QAItem(
            question=f"What did {hero.id} do after speaking too sharply to {sidekick.id}?",
            answer=f"{hero.id} apology-ized, said sorry, and offered to fix the mess with {gear.label}.",
        ),
        QAItem(
            question=f"What lesson was learned?",
            answer=LESSON_LEARNED,
        ),
        QAItem(
            question=f"Which power did {hero.id} try to use?",
            answer=f"{hero.id} tried to use {power.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an amoeba?",
            answer="An amoeba is a tiny living thing, so small that you usually need a microscope to see it well.",
        ),
        QAItem(
            question="What does it mean to apologize?",
            answer="To apologize means to say you are sorry for a mistake and show that you want to do better.",
        ),
        QAItem(
            question="Why do heroes work with sidekicks?",
            answer="Heroes work with sidekicks because a helper can make big jobs easier and keep the team calm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place=CITY.place, hero="Nova", sidekick="Pip", power="shield", gear="gloves"),
    StoryParams(place=CITY.place, hero="Bolt", sidekick="Roo", power="sweep", gear="boots"),
    StoryParams(place=CITY.place, hero="Mira", sidekick="Tess", power="lift", gear="mask"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        models = asp_valid_combos()
        print(f"{len(models)} compatible hero/power/gear triples:\n")
        for item in models[:50]:
            print(item)
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
