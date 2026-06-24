#!/usr/bin/env python3
"""
Story world: a small superhero tale with inner monologue and magic.

Seed premise:
A rookie superhero notices a tiny reptile trapped in the widening extent of a
magic spell. The hero wrestles with a mean inner monologue, then chooses a
kind, clever rescue instead of showy force.

The story world is built around one causal problem:
- a magic effect has an extent that can spread
- a vulnerable reptile is in that extent
- the hero can panic, think, and use a focused magical fix
- the ending shows the extent shrunk and the reptile safe
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "heroine"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "hero"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the city plaza"
    setting_detail: str = "The marble plaza gleamed under the afternoon sun."
    magic_kind: str = "glow"
    danger_kind: str = "spell"
    extent_threshold: float = 3.0


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    reptile_name: str
    reptile_type: str
    magic_kind: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Arlo", "Mina", "Jett", "Ruby", "Sky", "Orion", "Tess"]
REPTILE_NAMES = ["Pebble", "Slink", "Iggy", "Vera", "Moss", "Nim"]
HERO_TYPES = ["girl", "boy"]
REPTILE_TYPES = ["lizard", "gecko", "turtle", "iguana"]
PLACES = {
    "city plaza": Scene(place="the city plaza", setting_detail="The marble plaza gleamed under the afternoon sun."),
    "rooftop garden": Scene(place="the rooftop garden", setting_detail="The rooftop garden swayed in a warm wind above the streets."),
    "museum steps": Scene(place="the museum steps", setting_detail="The museum steps stood quiet, with people gasping near the doors."),
}
MAGIC_KINDS = ["glow", "spark", "bubble", "ribbon"]


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        return World(self.scene, entities=copy.deepcopy(self.entities), paragraphs=[[]], fired=set(self.fired), facts=dict(self.facts))


def _hero_inner_monologue(hero: Entity, danger: str) -> str:
    return (
        f"{hero.id} thought, 'Don't freeze. Don't be a schmuck. "
        f"You can see the {danger} clearly, so act clearly too.'"
    )


def _risk_extent(world: World, reptile: Entity) -> bool:
    return reptile.meters.get("in_extent", 0.0) >= 1.0


def _spell_spreads(world: World) -> None:
    if "spread" in world.fired:
        return
    world.fired.add("spread")
    orb = world.get("spell")
    if orb.meters.get("extent", 0.0) < world.scene.extent_threshold:
        orb.meters["extent"] = world.scene.extent_threshold
        world.say("The magic spell kept widening, and its bright edge crawled farther across the plaza.")


def _fear_and_focus(world: World, hero: Entity) -> None:
    if hero.memes.get("fear", 0.0) >= 1.0 and "focus" not in world.fired:
        world.fired.add("focus")
        hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0
        hero.memes["panic"] = max(0.0, hero.memes.get("panic", 0.0) - 1.0)
        world.say(_hero_inner_monologue(hero, "magic"))
        world.say(f"{hero.id} took one breath and decided to help instead of showing off.")


def _reptile_safe(world: World, reptile: Entity) -> bool:
    return reptile.meters.get("safe", 0.0) >= 1.0


def _rescue(world: World, hero: Entity, reptile: Entity) -> None:
    if "rescue" in world.fired:
        return
    if not _risk_extent(world, reptile):
        return
    world.fired.add("rescue")
    spell = world.get("spell")
    hero.meters["magic"] = hero.meters.get("magic", 0.0) + 1.0
    spell.meters["extent"] = max(0.0, spell.meters.get("extent", 0.0) - 2.0)
    reptile.meters["safe"] = 1.0
    reptile.meters["in_extent"] = 0.0
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} hand and cast a small, careful spell."
    )
    world.say(
        f"The bright edge shrank back, and {reptile.id} slipped out of the magic's extent."
    )


def _ending(world: World, hero: Entity, reptile: Entity) -> None:
    if "ending" in world.fired:
        return
    if not _reptile_safe(world, reptile):
        return
    world.fired.add("ending")
    world.say(
        f"At the end, {reptile.id} sat safe beside {hero.id}, and the plaza was calm again."
    )
    world.say(
        f"{hero.id} smiled at the quiet light, glad that a brave heart and a careful spell had both helped."
    )


def tell(scene: Scene, hero_name: str, hero_type: str, reptile_name: str, reptile_type: str, magic_kind: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="hero"))
    reptile = world.add(Entity(id=reptile_name, kind="character", type=reptile_type, label="reptile"))
    spell = world.add(Entity(id="spell", kind="thing", type="magic", label=magic_kind))
    spell.meters["extent"] = 4.0
    reptile.meters["in_extent"] = 1.0
    hero.memes["fear"] = 1.0
    hero.memes["panic"] = 1.0

    world.say(f"{scene.setting_detail} {hero.id} was a young superhero who liked solving problems with kindness.")
    world.say(f"One day, {reptile.id} was caught near a {magic_kind} spell whose extent kept growing.")
    world.para()
    world.say(f"{hero.id} looked at the widening magic and worried that the reptile would be hurt.")
    world.say(f"Inside {hero.id}'s head, a sharp little voice tried to sound tough, but it only made {hero.id} think harder.")
    _spell_spreads(world)
    _fear_and_focus(world, hero)
    _rescue(world, hero, reptile)
    world.para()
    _ending(world, hero, reptile)

    world.facts.update(hero=hero, reptile=reptile, spell=spell, scene=scene)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    reptile = f["reptile"]
    spell = f["spell"]
    scene = f["scene"]
    return [
        f"Write a short superhero story where {hero.id} saves a {reptile.type} named {reptile.id} from a {spell.label} spell at {scene.place}.",
        f"Tell a child-friendly adventure with inner monologue, magic, and a brave choice in {scene.place}.",
        f"Write a simple story about a superhero who refuses to act like a schmuck and uses careful magic to protect a reptile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    reptile = world.facts["reptile"]
    spell = world.facts["spell"]
    scene = world.facts["scene"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young superhero, and {reptile.id}, the reptile who needed help at {scene.place}.",
        ),
        QAItem(
            question=f"What problem did {reptile.id} have?",
            answer=f"{reptile.id} was stuck near a {spell.label} spell, and the spell's extent kept getting bigger.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of panicking?",
            answer=f"{hero.id} thought carefully, used a small magic spell, and shrank the dangerous extent so {reptile.id} could get safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended with {reptile.id} safe beside {hero.id} and the plaza calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reptile?",
            answer="A reptile is a kind of animal with a scaly body, like a lizard, turtle, snake, or iguana.",
        ),
        QAItem(
            question="What does extent mean?",
            answer="Extent means how far something reaches or spreads out.",
        ),
        QAItem(
            question="What is a spell?",
            answer="A spell is a magic action or magic words that can make unusual things happen in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with magic, extent, and a reptile rescue.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--reptile-name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--reptile-type", choices=REPTILE_TYPES)
    ap.add_argument("--magic-kind", choices=MAGIC_KINDS)
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
    place = args.place or rng.choice(list(PLACES))
    hero_name = args.name or rng.choice(HERO_NAMES)
    reptile_name = args.reptile_name or rng.choice(REPTILE_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    reptile_type = args.reptile_type or rng.choice(REPTILE_TYPES)
    magic_kind = args.magic_kind or rng.choice(MAGIC_KINDS)
    if hero_name.lower() == reptile_name.lower():
        raise StoryError("Hero and reptile need different names.")
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        reptile_name=reptile_name,
        reptile_type=reptile_type,
        magic_kind=magic_kind,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], params.hero_name, params.hero_type, params.reptile_name, params.reptile_type, params.magic_kind)
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


ASP_RULES = r"""
place(city_plaza).
place(rooftop_garden).
place(museum_steps).

magic(glow).
magic(spark).
magic(bubble).
magic(ribbon).

reptile(lizard).
reptile(gecko).
reptile(turtle).
reptile(iguana).

hero_type(girl).
hero_type(boy).

safe_choice(P, M) :- place(P), magic(M).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p.replace(" ", "_")))
    for m in MAGIC_KINDS:
        lines.append(asp.fact("magic", m))
    for r in REPTILE_TYPES:
        lines.append(asp.fact("reptile", r))
    for h in HERO_TYPES:
        lines.append(asp.fact("hero_type", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show safe_choice/2.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "safe_choice"))
    expected = {(p.replace(" ", "_"), m) for p in PLACES for m in MAGIC_KINDS}
    if atoms == expected:
        print(f"OK: ASP gate matches python registry ({len(atoms)} choices).")
        return 0
    print("MISMATCH:")
    print("only in asp:", sorted(atoms - expected))
    print("only in python:", sorted(expected - atoms))
    return 1


CURATED = [
    StoryParams(place="city plaza", hero_name="Nova", hero_type="girl", reptile_name="Pebble", reptile_type="gecko", magic_kind="glow"),
    StoryParams(place="rooftop garden", hero_name="Arlo", hero_type="boy", reptile_name="Slink", reptile_type="lizard", magic_kind="spark"),
    StoryParams(place="museum steps", hero_name="Mina", hero_type="girl", reptile_name="Iggy", reptile_type="iguana", magic_kind="ribbon"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show safe_choice/2."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show safe_choice/2."))
        print(sorted(asp.atoms(model, "safe_choice")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        for i in range(max(1, args.n) * 50):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
