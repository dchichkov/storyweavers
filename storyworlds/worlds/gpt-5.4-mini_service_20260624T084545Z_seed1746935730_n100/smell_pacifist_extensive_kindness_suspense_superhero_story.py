#!/usr/bin/env python3
"""
storyworlds/worlds/smell_pacifist_extensive_kindness_suspense_superhero_story.py
===============================================================================

A tiny superhero story world about a pacifist hero, a suspicious smell, and an
extensive act of kindness that resolves suspense without a fight.

The seed tale behind this world is a child-facing superhero story in which:
- the hero notices a strange smell,
- suspense builds because something seems wrong,
- the hero chooses pacifism instead of punching,
- kindness is used extensively to solve the problem,
- the ending proves the city is safer and calmer.

This script models that premise as a small simulation with physical meters and
emotional memes, plus an inline ASP twin for parity checks.
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
    owner: Optional[str] = None
    ally_of: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class City:
    name: str
    place: str
    smell_source: str
    afflicts: str
    shelter: str


@dataclass
class HeroKit:
    label: str
    use: str
    solves: str
    kind: str = "tool"


@dataclass
class StoryParams:
    city: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    source: str
    kit: str
    seed: Optional[int] = None


CITIES = {
    "harbor": City(
        name="Harbor City",
        place="the lighthouse plaza",
        smell_source="a burst pipe under the fountain",
        afflicts="the air smelled strange and sharp",
        shelter="the big blue shelter tent",
    ),
    "garden": City(
        name="Garden City",
        place="the moonflower bridge",
        smell_source="a toppled cart of onions and soap",
        afflicts="the air smelled odd and stinging",
        shelter="the warm community greenhouse",
    ),
    "skyway": City(
        name="Skyway",
        place="the rooftop park",
        smell_source="a dusty vent that puffed out smoke",
        afflicts="the air smelled smoky and worrisome",
        shelter="the bright rooftop clinic",
    ),
}

HERO_NAMES = ["Nova", "Mira", "Ray", "Juno", "Piper", "Zane", "Ari", "Luna"]
SIDEKICK_NAMES = ["Beep", "Dot", "Echo", "Zip", "Sunny", "Moss"]

KITS = {
    "mask": HeroKit(label="a soft filter mask", use="filter the smell", solves="help everyone breathe easier"),
    "fan": HeroKit(label="a gentle wind fan", use="move the air away", solves="push the smell out of the plaza"),
    "spray": HeroKit(label="a calming lavender spray", use="cover the bad odor", solves="make the air feel kinder"),
}

TRAITS = ["brave", "gentle", "patient", "curious", "calm", "kind"]


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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
        w = World(self.city)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def setup_reasonable(city: City, source: str, kit: str) -> bool:
    return source in CITIES and kit in KITS


def smell_is_serious(city: City) -> bool:
    return city.smell_source != ""


def asp_facts() -> str:
    import asp
    lines = []
    for cid, city in CITIES.items():
        lines.append(asp.fact("city", cid))
        lines.append(asp.fact("smell_source", cid, city.smell_source))
        lines.append(asp.fact("place", cid, city.place))
    for kid, kit in KITS.items():
        lines.append(asp.fact("kit", kid))
        lines.append(asp.fact("uses", kid, kit.use))
        lines.append(asp.fact("solves", kid, kit.solves))
    lines.append(asp.fact("theme", "smell"))
    lines.append(asp.fact("theme", "pacifist"))
    lines.append(asp.fact("theme", "extensive"))
    lines.append(asp.fact("feature", "kindness"))
    lines.append(asp.fact("feature", "suspense"))
    return "\n".join(lines)


ASP_RULES = r"""
% A smell is serious when it comes from some city source.
serious(C) :- city(C), smell_source(C, _).

% A kit is compatible if it helps with the smell and can resolve the danger.
compatible(K) :- kit(K), uses(K, _), solves(K, _).

valid_story(C, K) :- serious(C), compatible(K).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = {(cid, kid) for cid in CITIES for kid in KITS if smell_is_serious(CITIES[cid])}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def hero_intro(world: World, hero: Entity, sidekick: Entity) -> None:
    trait = next((t for t in hero.meters.get("traits", []) if t), None)
    world.say(
        f"{hero.id} was a {world.facts['trait']} superhero who lived in {world.city.name}."
    )
    world.say(
        f"{hero.id} and {sidekick.id} loved helping people, especially when the day felt tense."
    )


def begin_suspense(world: World, hero: Entity, sidekick: Entity) -> None:
    city = world.city
    hero.memes["alert"] = hero.memes.get("alert", 0) + 1
    world.say(
        f"One afternoon at {city.place}, {hero.id} stopped and sniffed the air."
    )
    world.say(
        f"The air smelled strange because {city.smell_source}; that made the whole plaza feel suspenseful."
    )


def investigate(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.meters["search"] = hero.meters.get("search", 0) + 1
    sidekick.meters["search"] = sidekick.meters.get("search", 0) + 1
    world.say(
        f"{hero.id} followed the smell with careful steps, and {sidekick.id} peeked under benches and rails."
    )
    world.say(
        f"They found the source near the fountain, where a small problem was making everyone worry."
    )


def pacifist_choice(world: World, hero: Entity, sidekick: Entity) -> None:
    hero.memes["pacifist"] = hero.memes.get("pacifist", 0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    world.say(
        f"{hero.id} did not punch, grab, or shout."
    )
    world.say(
        f"Instead, {hero.id} chose a pacifist way and whispered, 'Let's help kindly.'"
    )


def extensive_kindness(world: World, hero: Entity, sidekick: Entity, kit: HeroKit) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 2
    sidekick.memes["kindness"] = sidekick.memes.get("kindness", 0) + 1
    world.say(
        f"Together they used {kit.label} to {kit.use}."
    )
    world.say(
        f"They also handed out water, opened windows, and guided families toward {world.city.shelter}."
    )
    world.say(
        f"It was an extensive act of kindness, because they kept helping until the air felt safe again."
    )


def resolve(world: World, hero: Entity, sidekick: Entity, kit: HeroKit) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    sidekick.memes["relief"] = sidekick.memes.get("relief", 0) + 1
    world.facts["resolved"] = True
    world.say(
        f"At last, the strange smell faded, and the city could breathe easily."
    )
    world.say(
        f"{hero.id} smiled because {kit.solves}, and {sidekick.id} cheered beside {hero.pronoun('object')}."
    )
    world.say(
        f"By the end, {world.city.name} was calm, bright, and full of thankful neighbors."
    )


def tell(city: City, hero_name: str, hero_type: str, sidekick_name: str, sidekick_type: str, source: str, kit_id: str, trait: str) -> World:
    world = World(city)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type))
    kit = KITS[kit_id]
    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        kit=kit,
        trait=trait,
        source=source,
    )
    hero_intro(world, hero, sidekick)
    world.para()
    begin_suspense(world, hero, sidekick)
    investigate(world, hero, sidekick)
    world.para()
    pacifist_choice(world, hero, sidekick)
    extensive_kindness(world, hero, sidekick, kit)
    resolve(world, hero, sidekick, kit)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "smell" and ends with kindness.',
        f"Tell a suspenseful but gentle story about {f['hero'].id} and {f['sidekick'].id} in {world.city.name} when a strange smell appears.",
        f"Write a pacifist superhero story where the hero solves a problem with extensive kindness instead of fighting.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    sidekick: Entity = f["sidekick"]  # type: ignore[assignment]
    kit: HeroKit = f["kit"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What made {hero.id} stop and look around at {world.city.place}?",
            answer=f"{hero.id} stopped because the air smelled strange and sharp from {world.city.smell_source}.",
        ),
        QAItem(
            question=f"How did {hero.id} choose to solve the problem when the suspense grew?",
            answer=f"{hero.id} chose a pacifist way and helped kindly instead of fighting.",
        ),
        QAItem(
            question=f"What did {hero.id} and {sidekick.id} use to help the city?",
            answer=f"They used {kit.label} and lots of careful kindness to make the air safe again.",
        ),
        QAItem(
            question=f"Why did the ending feel happy after the extensive help?",
            answer=f"The smell faded, the neighbors could breathe easier, and the city became calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a smell?",
            answer="A smell is something you notice with your nose, like the scent of flowers, soup, or smoke.",
        ),
        QAItem(
            question="What does pacifist mean?",
            answer="Pacifist means choosing not to fight and trying to solve problems in a peaceful way.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being caring, gentle, and helpful to other people.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense is the feeling of wondering what will happen next.",
        ),
        QAItem(
            question="What does extensive mean?",
            answer="Extensive means very large, wide, or done in a lot of detail.",
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


NAME_POOL = {
    "girl": ["Nova", "Mira", "Luna", "Ava"],
    "boy": ["Ray", "Zane", "Ari", "Jace"],
}


@dataclass
class StoryParams:
    city: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    source: str
    kit: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: smell, pacifist, extensive kindness, suspense.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
    ap.add_argument("--source", choices=["harbor", "garden", "skyway"])
    ap.add_argument("--kit", choices=KITS)
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
    city = args.city or rng.choice(list(CITIES))
    source = args.source or city
    kit = args.kit or rng.choice(list(KITS))
    if not setup_reasonable(CITIES[city], source, kit):
        raise StoryError("No valid story matches those options.")
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    hero_name = args.hero_name or rng.choice(NAME_POOL[hero_type])
    sidekick_name = args.sidekick_name or rng.choice(SIDEKICK_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(city=city, hero_name=hero_name, hero_type=hero_type,
                       sidekick_name=sidekick_name, sidekick_type=sidekick_type,
                       source=source, kit=kit, trait=trait)


def generate(params: StoryParams) -> StorySample:
    city = CITIES[params.city]
    world = tell(city, params.hero_name, params.hero_type, params.sidekick_name,
                 params.sidekick_type, params.source, params.kit, params.trait)
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
    StoryParams(city="harbor", hero_name="Nova", hero_type="girl", sidekick_name="Beep", sidekick_type="boy", source="harbor", kit="mask", trait="gentle"),
    StoryParams(city="garden", hero_name="Ray", hero_type="boy", sidekick_name="Sunny", sidekick_type="girl", source="garden", kit="spray", trait="kind"),
    StoryParams(city="skyway", hero_name="Luna", hero_type="girl", sidekick_name="Zip", sidekick_type="boy", source="skyway", kit="fan", trait="calm"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story seeds:\n")
        for city, kit in stories:
            print(f"  {city:8} {kit}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.city} ({p.kit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
