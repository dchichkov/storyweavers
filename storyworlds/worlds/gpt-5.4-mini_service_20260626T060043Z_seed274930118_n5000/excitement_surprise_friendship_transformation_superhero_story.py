#!/usr/bin/env python3
"""
Story world: excitement, surprise, friendship, transformation, superhero story.

A small, constraint-checked superhero tale domain where a kid hero discovers a
surprise, learns friendship, and transforms to save the day.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
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


@dataclass
class City:
    name: str
    place_words: list[str]
    danger: str
    surprise: str
    transformation: str
    excitement: str


@dataclass
class HeroSpec:
    id: str
    type: str
    title: str
    power: str
    weakness: str
    costume: str


@dataclass
class VillainSpec:
    id: str
    type: str
    title: str
    scheme: str
    fear: str


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    effect: str
    transforms: bool = False


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.city)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


CITY = City(
    name="Star Harbor",
    place_words=["roof", "bridge", "cove", "tower", "station"],
    danger="shadow storm",
    surprise="mystery signal",
    transformation="glowing suit",
    excitement="sparkling excitement",
)

HEROES = {
    "nova": HeroSpec("Nova", "girl", "Captain Nova", "light bursts", "doubt", "silver cape"),
    "spark": HeroSpec("Spark", "boy", "Rocket Spark", "speed", "fear", "red mask"),
    "pulse": HeroSpec("Pulse", "girl", "Mighty Pulse", "shielding", "worry", "blue boots"),
}

VILLAINS = {
    "gloom": VillainSpec("Gloom", "shadow", "Captain Gloom", "steals brightness", "loud noises"),
    "snare": VillainSpec("Snare", "robot", "Tangle Snare", "ties up bridges", "kind words"),
}

ARTIFACTS = {
    "bracelet": Artifact("bracelet", "star bracelet", "a tiny star bracelet", "wrist", "it can glow brighter when friends hold hands", True),
    "badge": Artifact("badge", "hero badge", "a shiny hero badge", "chest", "it helps the hero remember their promise", False),
    "cape": Artifact("cape", "cape", "a bright cape", "back", "it swishes like a banner of courage", False),
}

NAME_OPTIONS = ["Ari", "Mina", "Theo", "Luna", "Eli", "Zara", "Ivy", "Kai"]
TRAITS = ["brave", "curious", "kind", "bouncy", "quick", "gentle"]


@dataclass
class StoryParams:
    hero: str
    villain: str
    artifact: str
    name: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world.")
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--villain", choices=VILLAINS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def choose(rng: random.Random, seq):
    return rng.choice(list(seq))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or choose(rng, HEROES)
    villain = args.villain or choose(rng, VILLAINS)
    artifact = args.artifact or choose(rng, ARTIFACTS)
    name = args.name or choose(rng, NAME_OPTIONS)
    trait = args.trait or choose(rng, TRAITS)
    if hero == "spark" and artifact == "badge":
        pass
    return StoryParams(hero=hero, villain=villain, artifact=artifact, name=name, trait=trait)


def _set_meter(e: Entity, key: str, val: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + val


def _set_meme(e: Entity, key: str, val: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + val


def tell(params: StoryParams) -> World:
    city = CITY
    world = World(city)
    hero_spec = HEROES[params.hero]
    villain_spec = VILLAINS[params.villain]
    artifact = ARTIFACTS[params.artifact]

    hero = world.add(Entity(id=params.name, kind="character", type="hero", label=hero_spec.title))
    sidekick = world.add(Entity(id="Friend", kind="character", type="friend", label="a best friend"))
    villain = world.add(Entity(id=villain_spec.id, kind="character", type="villain", label=villain_spec.title))
    item = world.add(Entity(id=artifact.id, type="artifact", label=artifact.label, phrase=artifact.phrase))
    item.owner = hero.id

    hero.memes["excitement"] = 1
    hero.memes["friendship"] = 1
    item.worn_by = hero.id

    world.say(
        f"{hero.id} was a {params.trait} hero named {hero_spec.title}, and {hero.pronoun('subject')} loved {CITY.excitement}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wore {artifact.phrase}, and it felt ready for a big day in {CITY.name}."
    )

    world.para()
    world.say(
        f"One afternoon, a surprise message flashed over the {city.place_words[0]}: a {city.surprise} called for help."
    )
    world.say(
        f"{hero.id} rushed with {sidekick.pronoun('possessive')} best friend to the {city.place_words[1]}, where the sky had turned into a {city.danger}."
    )
    _set_meter(hero, "speed", 1)
    _set_meme(hero, "excitement", 1)
    _set_meme(sidekick, "friendship", 1)

    world.para()
    world.say(
        f"{villain_spec.title} was there, chuckling, and {villain_spec.scheme} made the lights shake."
    )
    world.say(
        f"{hero.id} felt a wobble of fear, because {villain_spec.fear} made {hero.pronoun('possessive')} hands tremble."
    )
    _set_meme(hero, "fear", 1)
    if artifact.transforms:
        world.say(
            f"Then {sidekick.pronoun('subject')} grabbed {hero.pronoun('possessive')} hand and said, "
            f'"We can do this together!"'
        )
        _set_meme(hero, "friendship", 1)
        _set_meme(sidekick, "friendship", 1)
        _set_meme(hero, "courage", 1)
        world.say(
            f"The {artifact.label} began to shine, and {hero.id} changed into {city.transformation}."
        )
        _set_meme(hero, "transformation", 1)
        _set_meter(hero, "glow", 1)

    world.para()
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} glowing hands and made a bright burst that chased the shadows away."
    )
    _set_meme(villain, "defeat", 1)
    _set_meter(villain, "retreat", 1)

    world.say(
        f"{villain_spec.title} slipped back into the dark, and the city lights came on one by one like tiny stars."
    )
    world.say(
        f"{hero.id} smiled at {sidekick.pronoun('possessive')} friend, still wearing the shining {artifact.label}, "
        f"and the whole street felt full of excitement again."
    )

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "villain": villain,
        "artifact": item,
        "params": params,
        "hero_spec": hero_spec,
        "villain_spec": villain_spec,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a superhero story with excitement, surprise, friendship, and transformation about {p.name}.",
        f"Tell a child-friendly story where {p.name} and a friend discover a surprise and stop {f['villain_spec'].title}.",
        f"Write a short superhero adventure where a {p.trait} hero uses {ARTIFACTS[p.artifact].phrase} to transform and help a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    hero: Entity = f["hero"]
    villain_spec: VillainSpec = f["villain_spec"]
    artifact: Artifact = f["artifact"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {p.name}, a {p.trait} superhero who loves surprise adventures in {CITY.name}.",
        ),
        QAItem(
            question=f"What surprise helped start the adventure?",
            answer=f"A {CITY.surprise} flashed over the city and led {p.name} and a friend toward danger.",
        ),
        QAItem(
            question=f"Who helped {p.name} feel braver?",
            answer=f"A best friend helped {p.name} feel braver, and their friendship gave the hero courage.",
        ),
        QAItem(
            question=f"What changed when the {artifact.label} began to glow?",
            answer=f"{p.name} transformed into {CITY.transformation}, which helped the hero face {villain_spec.title}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{p.name} chased away the shadows, and the city felt safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a brave character who uses special powers or tools to help others and protect people.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and like being together.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing into something new, like becoming stronger, brighter, or different in a big way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {', '.join(bits)}")
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
    StoryParams(hero="nova", villain="gloom", artifact="bracelet", name="Ari", trait="brave"),
    StoryParams(hero="spark", villain="snare", artifact="cape", name="Mina", trait="curious"),
    StoryParams(hero="pulse", villain="gloom", artifact="badge", name="Theo", trait="kind"),
]


ASP_RULES = r"""
hero(H) :- hero_name(H).
villain(V) :- villain_name(V).
artifact(A) :- artifact_name(A).

surprise(H) :- hero(H), sees_signal(H).
friendship(H) :- hero(H), has_friend(H).
transformation(H) :- hero(H), glows(A), artifact(A).
victory(H) :- transformation(H), friendship(H), surprise(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in HEROES:
        lines.append(asp.fact("hero_name", k))
    for k in VILLAINS:
        lines.append(asp.fact("villain_name", k))
    for k in ARTIFACTS:
        lines.append(asp.fact("artifact_name", k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show hero/1. #show villain/1. #show artifact/1."))
    ok = bool(model)
    print("OK: ASP program is syntactically valid." if ok else "ASP produced no model.")
    return 0 if ok else 1


def build_random_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        hero=args.hero or rng.choice(list(HEROES)),
        villain=args.villain or rng.choice(list(VILLAINS)),
        artifact=args.artifact or rng.choice(list(ARTIFACTS)),
        name=args.name or rng.choice(NAME_OPTIONS),
        trait=args.trait or rng.choice(TRAITS),
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show surprise/1. #show friendship/1. #show transformation/1. #show victory/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show surprise/1. #show friendship/1. #show transformation/1. #show victory/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1 and not args.all:
            print(f"### variant {idx + 1}")
        elif args.all:
            p = sample.params
            print(f"### {p.name}: {p.hero} vs {p.villain} with {p.artifact}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
