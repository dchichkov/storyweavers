#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/limousine_fisted_kindness_curiosity_superhero_story.py
==============================================================================================================

A compact superhero-story world about a hero, a limousine, a fisted problem,
and the twin powers of Kindness and Curiosity.

Seed tale imagined from the prompt:
---
A young superhero loved riding in a shiny limousine with a friendly driver.
One day the limousine got stuck because someone had fisted the door shut with
a stubborn lock-clench. The hero felt curious about how it worked, then chose
kindness over force: they listened, learned the reason, and used a gentle tool
to open the door without breaking it. The limousine rolled again, and the day
ended with a bright smile.

This file is self-contained and follows the Storyweavers storyworld contract.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str
    indoors: bool = False
    label: str = ""


@dataclass
class Power:
    id: str
    label: str
    virtue: str
    action: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    source: str
    blocked_by: str
    pressure: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self._para[-1].append(text)

    def para(self) -> None:
        if self._para[-1]:
            self._para.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self._para if p)

    def init_narration(self) -> None:
        self._para: list[list[str]] = [[]]


SCENES = {
    "garage": Scene(place="the garage", indoors=True, label="garage"),
    "street": Scene(place="the city street", indoors=False, label="street"),
    "driveway": Scene(place="the driveway", indoors=False, label="driveway"),
}

HEROES = [
    ("Nova", "girl"),
    ("Jet", "boy"),
    ("Mira", "girl"),
    ("Zane", "boy"),
]

DRIVERS = ["Aunt June", "Mr. Vale", "Ms. Penny", "Coach Ray"]

POTENTIAL_POWERS = {
    "kindness": Power(
        id="kindness",
        label="Kindness",
        virtue="kindness",
        action="speak gently",
        effect="the tense frown melt away",
        tags={"kindness", "gentle"},
    ),
    "curiosity": Power(
        id="curiosity",
        label="Curiosity",
        virtue="curiosity",
        action="ask careful questions",
        effect="the mystery make sense",
        tags={"curiosity", "ask"},
    ),
}

THREATS = {
    "fisted": Threat(
        id="fisted",
        label="a fisted lock-clench",
        source="a stubborn hand squeeze on the limousine door",
        blocked_by="gentle understanding",
        pressure="the door would not budge",
        tags={"fisted", "stuck"},
    ),
    "locked": Threat(
        id="locked",
        label="a jammed latch",
        source="a jam that held the door shut",
        blocked_by="the right key and patience",
        pressure="the door stayed shut",
        tags={"locked", "stuck"},
    ),
}

LEVER_ITEMS = {
    "keycard": "a silver keycard",
    "spanner": "a tiny chrome spanner",
    "glove": "a soft glove",
}

REGISTRY = {
    "scenes": SCENES,
    "powers": POTENTIAL_POWERS,
    "threats": THREATS,
}


@dataclass
class StoryParams:
    scene: str
    hero_name: str
    hero_type: str
    driver: str
    threat: str
    power_a: str
    power_b: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: limousine, fisted, kindness, curiosity.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--driver", choices=DRIVERS)
    ap.add_argument("--power-a", choices=POTENTIAL_POWERS)
    ap.add_argument("--power-b", choices=POTENTIAL_POWERS)
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
    scene = args.scene or rng.choice(list(SCENES))
    threat = args.threat or rng.choice(list(THREATS))
    power_a = args.power_a or "kindness"
    power_b = args.power_b or "curiosity"
    if power_a == power_b:
        raise StoryError("Kindness and Curiosity must be different powers in this world.")
    hero_name, hero_type = (args.hero_name, args.hero_type)
    if hero_name is None or hero_type is None:
        hero_name, hero_type = rng.choice(HEROES)
    driver = args.driver or rng.choice(DRIVERS)
    if scene == "street" and threat == "fisted":
        pass
    return StoryParams(scene=scene, hero_name=hero_name, hero_type=hero_type, driver=driver, threat=threat, power_a=power_a, power_b=power_b)


def reasonableness_gate(params: StoryParams) -> None:
    if params.power_a == params.power_b:
        raise StoryError("A superhero story needs two different beats: one for Kindness and one for Curiosity.")
    if params.threat not in THREATS:
        raise StoryError("Unknown threat.")
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")


def narrative_title(world: World, hero: Entity) -> str:
    return f"{hero.id} and the limousine"


def intro(world: World, hero: Entity, driver: Entity, threat: Threat) -> None:
    world.say(
        f"{hero.id} was a little superhero who loved shiny rides and big questions."
    )
    world.say(
        f"One bright day, {hero.pronoun('possessive')} favorite limousine waited near {world.scene.place}, "
        f"with {driver.label} smiling at the wheel."
    )
    world.say(
        f"But the limousine faced {threat.label}: {threat.pressure}."
    )


def tension(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["concern"] = hero.memes.get("concern", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} fisted {hero.pronoun('possessive')} hands for a moment, then took a slow breath."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to fix it fast, but {threat.source} made the problem tricky."
    )


def use_curiosity(world: World, hero: Entity, driver: Entity, threat: Threat) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} chose Curiosity first and asked {driver.label} how the door had gotten stuck."
    )
    world.say(
        f"{driver.label} explained that a small clench had jammed the latch, and that {threat.blocked_by} would help most."
    )


def use_kindness(world: World, hero: Entity, driver: Entity, threat: Threat) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"Then {hero.id} used Kindness and spoke softly instead of pushing harder."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} gentle words helped {driver.label} relax, which made the stuck door less scary."
    )


def resolve(world: World, hero: Entity, driver: Entity, threat: Threat) -> None:
    tool = LEVER_ITEMS["keycard"] if threat.id == "fisted" else LEVER_ITEMS["spanner"]
    hero.meters["effort"] = hero.meters.get("effort", 0) + 1
    world.say(
        f"Together they used {tool}, worked the latch carefully, and the limousine door clicked open."
    )
    world.say(
        f"At last the limousine rolled forward again, and {hero.id} smiled because {hero.pronoun('possessive')} kindness had helped more than force."
    )
    world.say(
        f"{driver.label} thanked {hero.id}, and the whole street seemed brighter as the ride went on."
    )


def tell(params: StoryParams) -> World:
    world = World(SCENES[params.scene])
    world.init_narration()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    driver = world.add(Entity(id="Driver", kind="character", type="adult", label=params.driver))
    threat = THREATS[params.threat]
    world.facts.update(hero=hero, driver=driver, threat=threat, params=params)

    intro(world, hero, driver, threat)
    world.para()
    tension(world, hero, threat)
    use_curiosity(world, hero, driver, threat)
    use_kindness(world, hero, driver, threat)
    world.para()
    resolve(world, hero, driver, threat)
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a superhero story for preschoolers about {p.hero_name}, a limousine, and a fisted problem.",
        f"Tell a short story where Kindness and Curiosity help {p.hero_name} open a stuck limousine door.",
        f"Create a gentle superhero tale set in {world.scene.place} with a shiny limousine and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    threat: Threat = world.facts["threat"]  # type: ignore[assignment]
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    driver: Entity = world.facts["driver"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a little {hero.type} who loves the limousine and helps with care.",
        ),
        QAItem(
            question=f"What problem did the limousine have?",
            answer=f"The limousine had {threat.label}, which meant {threat.pressure}.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} fixed it by using Curiosity to learn what happened and Kindness to stay gentle, then {driver.label} helped open the door with a careful tool.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when you choose gentle, caring actions that help someone feel safe and respected.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the urge to ask questions and learn how something works.",
        ),
        QAItem(
            question="What is a limousine?",
            answer="A limousine is a long car with lots of space inside, often used for special rides.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"scene={world.scene.place}")
    return "\n".join(lines)


ASP_RULES = r"""
power(kindness).
power(curiosity).
threat(fisted).
thing(limousine).

compatible(kindness, fisted).
compatible(curiosity, fisted).

complete_story(S) :- compatible(kindness, S), compatible(curiosity, S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("power", "kindness"), asp.fact("power", "curiosity"), asp.fact("threat", "fisted"), asp.fact("thing", "limousine")]
    lines.append(asp.fact("compatible", "kindness", "fisted"))
    lines.append(asp.fact("compatible", "curiosity", "fisted"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = {("kindness", "fisted"), ("curiosity", "fisted")}
    if asp_set == py_set:
        print("OK: ASP matches Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def build_story_params_list(args: argparse.Namespace, rng: random.Random) -> list[StoryParams]:
    if args.all:
        return [
            StoryParams(scene="garage", hero_name="Nova", hero_type="girl", driver="Aunt June", threat="fisted", power_a="kindness", power_b="curiosity"),
            StoryParams(scene="street", hero_name="Jet", hero_type="boy", driver="Mr. Vale", threat="fisted", power_a="kindness", power_b="curiosity"),
            StoryParams(scene="driveway", hero_name="Mira", hero_type="girl", driver="Ms. Penny", threat="fisted", power_a="kindness", power_b="curiosity"),
        ]
    params = resolve_params(args, rng)
    params.seed = args.seed
    return [params]


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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/2."))
        atoms = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(atoms)} compatible pairs:")
        for a, b in atoms:
            print(f"  {a} -> {b}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i, params in enumerate(build_story_params_list(args, random.Random(base_seed))):
        if not args.all:
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
