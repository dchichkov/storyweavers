#!/usr/bin/env python3
"""
efficient_nut_snow_inner_monologue_adventure.py
==============================================

A small story world about an efficient little squirrel, a hidden nut stash,
and an adventurous dash through the snow.

Premise:
- A squirrel wants to gather nuts before the snow gets too deep.
- The squirrel thinks in a steady inner monologue, planning the safest route.
- A small mishap creates tension, but clever thinking leads to a neat ending.

World model:
- typed entities with meters and memes
- physical state: snow depth, nut count, warmth, path clarity
- emotional state: worry, focus, pride, relief

The story is intentionally narrow:
- fewer, stronger variants
- a clear beginning, turn, and resolution
- child-facing prose with a concrete ending image
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"snow": 0.0, "nuts": 0.0, "warmth": 0.0, "path": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "focus": 0.0, "pride": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"squirrel", "girl", "boy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the snowy woods"
    affords: set[str] = field(default_factory=lambda: {"gather_nuts"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    fix: str
    weather: str = "snowy"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.route: str = "clear"

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.route = self.route
        return clone


ACTION = Action(
    id="gather",
    verb="gather the nuts",
    gerund="gathering nuts",
    rush="dash toward the old oak tree",
    risk="snow would bury the trail",
    fix="make a neat shortcut",
    tags={"snow", "nuts", "efficient"},
)

TOOLS = [
    Tool(
        id="sled",
        label="a little sled",
        phrase="a little sled with smooth runners",
        helps={"snow"},
        covers={"trail"},
        plural=False,
    ),
    Tool(
        id="map",
        label="a pinecone map",
        phrase="a pinecone map with a careful line drawn on it",
        helps={"efficient"},
        covers={"mind"},
        plural=False,
    ),
]


@dataclass
class StoryParams:
    place: str = "woods"
    action: str = "gather"
    name: str = "Nina"
    species: str = "squirrel"
    seed: Optional[int] = None


SETTINGS = {
    "woods": Setting(place="the snowy woods"),
}

NAMES = ["Nina", "Milo", "Tara", "Pip", "Sage", "Roo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world: efficient, nut, snow, inner monologue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
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
    place = args.place or "woods"
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, name=name, seed=args.seed)


def _predict_mess(world: World, hero: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["snow"] += 1
    return sim.get(hero.id).meters["snow"] >= THRESHOLD


def _think(world: World, hero: Entity, text: str) -> None:
    world.say(f"{hero.id} thought, “{text}”")


def _intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little squirrel who loved busy days and neat plans.")
    world.say(f"{hero.pronoun().capitalize()} liked to do things the efficient way, one careful step at a time.")


def _desire(world: World, hero: Entity) -> None:
    hero.memes["focus"] += 1
    world.say(f"Today, {hero.id} wanted to gather the nuts before the snow got too deep.")
    _think(world, hero, "If I move quickly and keep my paws warm, I can bring home more nuts.")


def _warn(world: World, hero: Entity) -> bool:
    if _predict_mess(world, hero):
        hero.memes["worry"] += 1
        world.say(f"But the white snow was already drifting over the trail.")
        _think(world, hero, "If I rush without a plan, I might lose the path and waste time.")
        return True
    return False


def _tool_offer(world: World, hero: Entity) -> Tool:
    tool = world.add(Entity(
        id="sled",
        kind="thing",
        type="sled",
        label="sled",
        phrase="a little sled with smooth runners",
        owner=hero.id,
    ))
    hero.memes["focus"] += 1
    world.say(f"{hero.id} spotted {tool.phrase}.")
    _think(world, hero, "A sled will save steps. That is the efficient choice.")
    return TOOLS[0]


def _journey(world: World, hero: Entity, tool: Tool) -> None:
    world.para()
    world.say(f"{hero.id} climbed onto the little sled and {ACTION.rush}.")
    hero.meters["path"] += 1
    hero.meters["snow"] += 1
    if hero.meters["snow"] >= THRESHOLD:
        world.say(f"Snow brushed {hero.pronoun('possessive')} fur, but the sled kept the trip quick.")
    world.say(f"At the old oak, the nuts waited under a soft blanket of snow.")
    hero.meters["nuts"] += 3
    _think(world, hero, "Good. I found them faster than I feared.")


def _turn(world: World, hero: Entity) -> None:
    world.para()
    world.say(f"Then a gust of wind shook the branches, and a few nuts slid out of reach.")
    hero.memes["worry"] += 1
    _think(world, hero, "I can still solve this. I just need a better angle.")


def _resolution(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} tucked the sled sideways to make a small ramp in the snow.")
    _think(world, hero, "Short cuts can be clever if they stay safe.")
    hero.meters["nuts"] += 2
    hero.memes["pride"] += 1
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    world.say(f"One by one, the last nuts rolled right into {hero.pronoun('possessive')} paws.")
    world.say(f"By the end, {hero.id} had a full bundle of nuts and a tidy path home through the snow.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.species))
    world.facts["hero"] = hero
    world.facts["action"] = ACTION

    _intro(world, hero)
    _desire(world, hero)
    _warn(world, hero)
    tool = _tool_offer(world, hero)
    _journey(world, hero, tool)
    _turn(world, hero)
    _resolution(world, hero)
    world.facts["tool"] = tool
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        'Write a short adventure story for young children about an efficient helper, a nut stash, and snow.',
        f"Tell a story where {hero.id} thinks carefully, crosses the snowy woods, and brings home nuts.",
        'Write a gentle adventure with an inner monologue that includes the words efficient, nut, and snow.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little squirrel who likes to be efficient.",
        ),
        QAItem(
            question="Why did the squirrel worry at first?",
            answer="The squirrel worried because the snow was starting to cover the trail and could make the trip harder.",
        ),
        QAItem(
            question="How did the squirrel solve the problem?",
            answer="The squirrel used a little sled and made a small ramp in the snow so the last nuts could roll close again.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the squirrel had a full bundle of nuts, felt proud, and had a neat path home through the snow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nut?",
            answer="A nut is a hard little seed or fruit that many animals eat for food.",
        ),
        QAItem(
            question="What is snow?",
            answer="Snow is frozen water that falls as soft white flakes and can cover the ground.",
        ),
        QAItem(
            question="What does efficient mean?",
            answer="Efficient means doing something in a smart way that saves time or effort.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"route={world.route}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the squirrel faces snow and has a way to act efficiently.
has_theme(efficient) :- keyword(efficient).
has_theme(nut) :- keyword(nut).
has_theme(snow) :- keyword(snow).

valid_story(woods, gather, squirrel) :- setting(woods), action(gather), species(squirrel),
                                        has_theme(efficient), has_theme(nut), has_theme(snow).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "woods"),
        asp.fact("action", "gather"),
        asp.fact("species", "squirrel"),
        asp.fact("keyword", "efficient"),
        asp.fact("keyword", "nut"),
        asp.fact("keyword", "snow"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {("woods", "gather", "squirrel")}
    if atoms == expected:
        print("OK: ASP gate matches Python reasonableness check.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


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


def build_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)
    samples: list[StorySample] = []
    if args.all:
        samples.append(generate(StoryParams(place="woods", name="Nina", seed=base_seed)))
        return samples
    for i in range(args.n):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        samples.append(generate(params))
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    samples = build_samples(args)

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
