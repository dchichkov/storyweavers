#!/usr/bin/env python3
"""
Story world: campaign_bravery_magic_animal_story
=================================================

A small, classical animal-story world about a brave animal campaign, with a
little magic that helps at the turning point.

Premise:
- An animal leader starts a campaign to help the grove.
- The campaign needs one brave act that feels scary at first.
- A bit of magic provides a gentle, concrete tool or sign.
- Bravery changes from "shaky" to "steady," and the ending proves it.

The world is simulated with typed entities, physical meters, and emotional
memes. State drives the prose and the Q&A.
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


BRAVERY_THRESHOLD = 1.0
SPELL_THRESHOLD = 1.0
RALLY_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    species: str = "animal"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Grove:
    place: str = "the moonlit grove"
    problem: str = "a dark path"
    campaign_goal: str = "light the path for the small animals"


@dataclass
class MagicItem:
    id: str
    label: str
    effect: str
    beam: str
    help_text: str


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    magic: str
    problem: str
    seed: Optional[int] = None


class World:
    def __init__(self, grove: Grove) -> None:
        self.grove = grove
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.grove)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "grove": Grove(place="the moonlit grove", problem="a dark path", campaign_goal="light the path for the small animals"),
    "meadow": Grove(place="the meadow", problem="a stormy trail", campaign_goal="help the little animals cross safely"),
    "riverbank": Grove(place="the riverbank", problem="a noisy crossing", campaign_goal="show the animals where to step"),
}

HEROES = {
    "rabbit": {"label": "rabbit", "phrase": "a bright-eyed rabbit", "pronoun": "they"},
    "fox": {"label": "fox", "phrase": "a clever fox", "pronoun": "they"},
    "bear": {"label": "bear", "phrase": "a gentle bear", "pronoun": "they"},
    "deer": {"label": "deer", "phrase": "a soft-hoofed deer", "pronoun": "they"},
}

SIDEKICKS = {
    "mouse": {"label": "mouse", "phrase": "a tiny mouse helper"},
    "squirrel": {"label": "squirrel", "phrase": "a quick squirrel helper"},
    "owl": {"label": "owl", "phrase": "a wise owl helper"},
}

MAGIC = {
    "lantern": MagicItem(
        id="lantern",
        label="glow lantern",
        effect="made a warm circle of light",
        beam="a little gold beam",
        help_text="The glow lantern could turn a dark path into a safe trail.",
    ),
    "leafring": MagicItem(
        id="leafring",
        label="leaf ring",
        effect="unfolded into a soft green map",
        beam="a shimmer of green leaves",
        help_text="The leaf ring could show the way without scaring the animals.",
    ),
    "pebble": MagicItem(
        id="pebble",
        label="singing pebble",
        effect="sang a tiny guiding tune",
        beam="a bright little note of sound",
        help_text="The singing pebble could call friends to gather and listen.",
    ),
}

TRAITS = ["brave", "gentle", "curious", "kind", "steady"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.sidekick not in SIDEKICKS:
        raise StoryError("Unknown sidekick.")
    if params.magic not in MAGIC:
        raise StoryError("Unknown magic item.")
    if params.problem not in {"dark", "storm", "crossing"}:
        raise StoryError("Unknown problem.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for hero in HEROES:
        lines.append(asp.fact("hero", hero))
    for sidekick in SIDEKICKS:
        lines.append(asp.fact("sidekick", sidekick))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
    for prob in {"dark", "storm", "crossing"}:
        lines.append(asp.fact("problem", prob))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,H,S,M,Prob) :- place(P), hero(H), sidekick(S), magic(M), problem(Prob).
#show compatible/5.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/5."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set((p, h, s, m, pr) for p in SETTINGS for h in HEROES for s in SIDEKICKS for m in MAGIC for pr in {"dark", "storm", "crossing"})
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with bravery, magic, and a campaign.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--problem", choices=["dark", "storm", "crossing"])
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
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    sidekick = args.sidekick or rng.choice(list(SIDEKICKS))
    magic = args.magic or rng.choice(list(MAGIC))
    problem = args.problem or rng.choice(["dark", "storm", "crossing"])
    params = StoryParams(place=place, hero=hero, sidekick=sidekick, magic=magic, problem=problem)
    reasonableness_gate(params)
    return params


def build_world(params: StoryParams) -> World:
    grove = SETTINGS[params.place]
    world = World(grove)
    hero = world.add(Entity(id="hero", kind="character", species=params.hero, label=HEROES[params.hero]["label"], phrase=HEROES[params.hero]["phrase"], role="campaign leader"))
    helper = world.add(Entity(id="helper", kind="character", species=params.sidekick, label=SIDEKICKS[params.sidekick]["label"], phrase=SIDEKICKS[params.sidekick]["phrase"], role="helper"))
    magic = world.add(Entity(id="magic", kind="thing", species="magic", label=MAGIC[params.magic].label, phrase=MAGIC[params.magic].label, role="tool"))
    problem = world.add(Entity(id="problem", kind="thing", species="problem", label=grove.problem, phrase=grove.problem, role="trouble"))
    world.facts.update(hero=hero, helper=helper, magic=magic, problem=problem, params=params)
    return world


def tell_story(world: World) -> None:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    magic: Entity = world.facts["magic"]
    grove = world.grove
    trait = "brave"
    world.say(f"In {grove.place}, {hero.phrase} started a little campaign to {grove.campaign_goal}.")
    world.say(f"{helper.phrase} promised to help, and soon the two friends pinned up soft leaves and tiny signs.")
    world.para()
    if params.problem == "dark":
        world.say(f"But the path was dark, and the small animals kept stopping at the edge.")
        hero.memes["worry"] = 1
        hero.memes["bravery"] = 0
        world.say(f"{hero.pronoun('subject').capitalize()} wanted to speak up, yet {hero.pronoun('possessive')} whiskers shook.")
    elif params.problem == "storm":
        world.say(f"But a stormy wind rushed through {grove.place}, and the little animals tucked their ears close.")
        hero.memes["worry"] = 1
        hero.meters["wind"] = 1
        world.say(f"{hero.pronoun('subject').capitalize()} took one tiny breath and looked at the path anyway.")
    else:
        world.say(f"But the riverbank crossing looked wobbly, and nobody wanted to take the first step.")
        hero.memes["worry"] = 1
        world.say(f"{hero.pronoun('subject').capitalize()} felt the crowd waiting on {hero.pronoun('possessive')} next move.")
    world.para()
    hero.memes["bravery"] = 1
    hero.meters["campaign"] = 1
    world.say(f"Then the {magic.label} gave a quiet sign: {MAGIC[params.magic].effect}.")
    world.say(f"{helper.phrase} held it high, and {magic.pronoun('subject')} cast {MAGIC[params.magic].beam} across the path.")
    world.say(f"That small magic helped {hero.label} stand taller and call, 'Come on, we can do it together!'")
    world.para()
    hero.memes["bravery"] = 2
    hero.memes["joy"] = 1
    hero.memes["fear"] = 0
    world.say(f"The first little animals followed, then more and more, until the whole line moved safely through.")
    world.say(f"By the end, {hero.phrase} had finished the campaign, and the grove felt bright and proud.")
    world.facts["resolved"] = True


def generate_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    return [
        f"Write a gentle animal story about a {params.hero} who leads a campaign in {params.place} with a little magic.",
        f"Tell a short story where a brave {params.hero} and a helpful {params.sidekick} use {params.magic} to solve a {params.problem} problem.",
        f"Write a child-friendly campaign story in an animal grove with bravery, teamwork, and one magical helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    magic: Entity = world.facts["magic"]
    grove = world.grove
    return [
        QAItem(
            question=f"Who led the campaign in {grove.place}?",
            answer=f"{hero.phrase} led the campaign to {grove.campaign_goal}."
        ),
        QAItem(
            question=f"Who helped the brave animal with the campaign?",
            answer=f"{helper.phrase} helped by staying close and carrying the {magic.label}."
        ),
        QAItem(
            question=f"What did the magic do in the story?",
            answer=f"The {magic.label} gave a helpful sign and made a safe light for the animals."
        ),
        QAItem(
            question=f"Why did the animals need bravery?",
            answer=f"They needed bravery because the {params.problem} problem made the path feel scary at first."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The campaign worked, the animals moved safely, and the grove felt proud and bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels afraid, but still tries to do the right or helpful thing."
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something special that can make surprising things happen in a story."
        ),
        QAItem(
            question="What is a campaign?",
            answer="A campaign is a planned effort to help reach a goal, often by working together."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: kind={e.kind} species={e.species} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
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
    StoryParams(place="grove", hero="rabbit", sidekick="mouse", magic="lantern", problem="dark"),
    StoryParams(place="meadow", hero="fox", sidekick="owl", magic="leafring", problem="storm"),
    StoryParams(place="riverbank", hero="deer", sidekick="squirrel", magic="pebble", problem="crossing"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/5."))
        atoms = asp.atoms(model, "compatible")
        print(f"{len(atoms)} compatible combinations")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
