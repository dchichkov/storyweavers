#!/usr/bin/env python3
"""
storyworlds/worlds/tambourine_kindness_superhero_story.py
=========================================================

A small standalone story world for a superhero-style kindness tale.

Premise:
- A child hero carries a tambourine.
- A nearby moment of need threatens a cheerless public scene.
- Kindness is the superpower: the hero can choose to include, comfort, and
  brighten another character, changing the emotional state of the world.
- The story ends with the tambourine being used in a way that proves kindness
  has made the scene better.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP_RULES twin
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: Optional[str] = None
    worn_by: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    scene: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    risk: str
    emotionally_needs: str
    place_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    fix: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    parent_type: str
    need: str
    tool: str
    seed: Optional[int] = None


PLACES = {
    "city_square": Place(
        id="city_square",
        name="the city square",
        scene="a bright plaza with a fountain and a little stage",
        supports={"music", "helping", "gathering"},
    ),
    "school_yard": Place(
        id="school_yard",
        name="the school yard",
        scene="a school yard with painted hopscotch lines and a bench",
        supports={"music", "helping", "gathering"},
    ),
    "community_garden": Place(
        id="community_garden",
        name="the community garden",
        scene="a garden with tall sunflowers and a tiny picnic table",
        supports={"music", "helping", "gathering"},
    ),
}

NEEDS = {
    "lonely_new_kid": Need(
        id="lonely_new_kid",
        label="new kid",
        phrase="a new kid with a shy face",
        risk="felt left out",
        emotionally_needs="belonging",
        place_need="gathering",
        tags={"kindness", "gathering"},
    ),
    "dropped_markers": Need(
        id="dropped_markers",
        label="box of markers",
        phrase="a box of markers spilled near the bench",
        risk="looked upsetting",
        emotionally_needs="helping",
        place_need="helping",
        tags={"kindness", "helping"},
    ),
    "sad_song": Need(
        id="sad_song",
        label="song",
        phrase="a sad song that nobody could quite hear",
        risk="made the plaza feel quiet",
        emotionally_needs="music",
        place_need="music",
        tags={"kindness", "music"},
    ),
}

TOOLS = {
    "tambourine": Tool(
        id="tambourine",
        label="tambourine",
        phrase="a shiny tambourine",
        fix="made a happy rhythm",
        tags={"tambourine", "music", "kindness"},
    ),
    "kind_words": Tool(
        id="kind_words",
        label="kind words",
        phrase="a warm smile and kind words",
        fix="made the other child feel seen",
        tags={"kindness"},
    ),
    "helping_hands": Tool(
        id="helping_hands",
        label="helping hands",
        phrase="both helping hands",
        fix="made the mess easier to clean",
        tags={"kindness", "helping"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ava", "Zoe", "Iris", "Maya"]
BOY_NAMES = ["Leo", "Theo", "Ezra", "Noah", "Ben", "Eli", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for need in NEEDS.values():
            for tool in TOOLS.values():
                if reasonableness_gate(place, need, tool):
                    combos.append((place.id, need.id, tool.id))
    return combos


def reasonableness_gate(place: Place, need: Need, tool: Tool) -> bool:
    return need.place_need in place.supports and (
        tool.id == "tambourine" or "kindness" in tool.tags
    )


def explain_rejection(place: Place, need: Need, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fit this kindness moment at {place.name}. "
        f"Pick a need the place supports, or use the tambourine to help the scene.")
    )


def setup_names(rng: random.Random) -> tuple[str, str, str, str]:
    hero_gender = rng.choice(["girl", "boy"])
    side_gender = rng.choice(["girl", "boy"])
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    side = rng.choice([n for n in (GIRL_NAMES if side_gender == "girl" else BOY_NAMES) if n != hero])
    return hero, hero_gender, side, side_gender


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_gender, role="sidekick"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent", label="the parent"))
    need = world.add(Entity(id="need", kind="thing", type=NEEDS[params.need].label, label=NEEDS[params.need].label))
    tool = world.add(Entity(id="tool", kind="thing", type=TOOLS[params.tool].label, label=TOOLS[params.tool].label))
    world.facts.update(hero=hero, sidekick=sidekick, parent=parent, need_cfg=NEEDS[params.need], tool_cfg=TOOLS[params.tool], need=need, tool=tool)
    return world


def tell(world: World, params: StoryParams) -> None:
    hero = world.facts["hero"]
    sidekick = world.facts["sidekick"]
    parent = world.facts["parent"]
    need = world.facts["need_cfg"]
    tool = world.facts["tool_cfg"]

    hero.memes["hope"] += 1
    sidekick.memes["curiosity"] += 1

    world.say(
        f"On a sunny day at {world.place.name}, {hero.id} and {sidekick.id} "
        f"stood beside {world.place.scene}."
    )
    world.say(
        f"They noticed {need.phrase}, and it {need.risk}."
    )
    world.para()

    hero.memes["desire"] += 1
    if params.tool == "tambourine":
        world.say(
            f"{hero.id} lifted the {tool.label} and gave it a soft shake. "
            f"The little jingle spread through the square like a brave hello."
        )
    else:
        world.say(
            f"{hero.id} chose {tool.phrase}, hoping it could help."
        )

    sidekick.memes["worry"] += 1
    world.say(
        f"{sidekick.id} looked at {need.label} and then at {hero.id}. "
        f"{sidekick.pronoun().capitalize()} wondered if the moment needed a kinder plan."
    )

    world.para()
    if params.tool == "tambourine":
        hero.memes["kindness"] += 2
        sidekick.memes["joy"] += 1
        need_entity = world.facts["need"]
        need_entity.meters["attention"] = 1
        world.say(
            f"{hero.id} stepped closer, smiled, and played a cheerful rhythm. "
            f"The beat invited {need.label} into the circle instead of leaving {need.label} alone."
        )
        if need.id == "lonely_new_kid":
            world.say(
                f"{sidekick.id} waved, and the shy new kid blinked, then smiled back."
            )
        elif need.id == "dropped_markers":
            world.say(
                f"The music made everyone kneel down together, and soon the markers were gathered before they rolled away."
            )
        else:
            world.say(
                f"The bright rhythm turned the quiet song into a chorus that carried all the way across {world.place.name}."
            )
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} saw the kindness and nodded. "
            f'"That is a real superhero move," {parent.pronoun()} said.'
        )
        world.say(
            f"At the end, {hero.id} kept tapping the {tool.label} while {sidekick.id} "
            f"stood a little taller, and {need.label} was no longer lonely in the middle of {world.place.name}."
        )
    else:
        hero.memes["kindness"] += 1
        world.say(
            f"That helped a little, but not enough. So {hero.id} paused, "
            f"took a breath, and chose kindness instead."
        )
        world.say(
            f"Then {hero.id} found the {TOOLS['kind_words'].phrase}, and the scene softened right away."
        )
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} smiled at the change. "
            f'“That is how a superhero helps,” {parent.pronoun()} said.'
        )
        world.say(
            f"By the end, the {tool.label} was not what saved the day, "
            f"but the kinder choice made {need.label} feel safe and welcome."
        )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes a "{f["tool_cfg"].label}" and a kindness problem.',
        f"Tell a child-friendly superhero story where {f['hero'].id} uses a {f['tool_cfg'].label} to help {f['need_cfg'].label} at {world.place.name}.",
        f"Write a simple story about a kind hero, a shy or sad moment, and a tambourine that makes the day better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    need = f["need_cfg"]
    tool = f["tool_cfg"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Who is the superhero story about?",
            answer=f"It is about {hero.id}, who acted like a kind superhero, and {sidekick.id}, who helped by watching closely and joining in.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice at {world.place.name}?",
            answer=f"{hero.id} noticed {need.phrase}. It {need.risk}, so the moment needed kindness and a brave choice.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help?",
            answer=f"{hero.id} used the {tool.label}. Its happy sound and bright rhythm made the scene feel friendlier.",
        ),
        QAItem(
            question=f"How did {parent.label_word} react to the ending?",
            answer=f"{parent.label_word.capitalize()} smiled and called it a real superhero move because kindness changed the mood of the whole place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small hand drum with jingly metal discs around the edge. When you shake or tap it, it makes a bright, cheerful sound.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, include, or comfort someone in a gentle way. It can turn a hard moment into a better one.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            bits.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("city_square", "Ava", "girl", "Leo", "boy", "mother", "lonely_new_kid", "tambourine"),
    StoryParams("school_yard", "Mia", "girl", "Max", "boy", "father", "dropped_markers", "tambourine"),
    StoryParams("community_garden", "Noah", "boy", "Iris", "girl", "mother", "sad_song", "tambourine"),
]


ASP_RULES = r"""
place(city_square). place(school_yard). place(community_garden).
supports(city_square,gathering). supports(city_square,helping). supports(city_square,music).
supports(school_yard,gathering). supports(school_yard,helping). supports(school_yard,music).
supports(community_garden,gathering). supports(community_garden,helping). supports(community_garden,music).

need(lonely_new_kid). need(dropped_markers). need(sad_song).
place_need(lonely_new_kid,gathering). place_need(dropped_markers,helping). place_need(sad_song,music).

tool(tambourine). tool(kind_words). tool(helping_hands).
kind_tool(tambourine). kind_tool(kind_words). kind_tool(helping_hands).

valid(P,N,T) :- place(P), need(N), tool(T), place_need(N,X), supports(P,X), kind_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for s in sorted(p.supports):
            lines.append(asp.fact("supports", p.id, s))
    for n in NEEDS.values():
        lines.append(asp.fact("need", n.id))
        lines.append(asp.fact("place_need", n.id, n.place_need))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        if "kindness" in t.tags or t.id == "tambourine":
            lines.append(asp.fact("kind_tool", t.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero-style kindness story world with a tambourine.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.need is None or c[1] == args.need)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need, tool = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    side_gender = rng.choice(["girl", "boy"])
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice([n for n in (GIRL_NAMES if side_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, hero, hero_gender, sidekick, side_gender, parent, need, tool)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    sidekick = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_gender, role="sidekick"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, role="parent", label="the parent"))
    need = world.add(Entity(id="need", kind="thing", type=NEEDS[params.need].label, label=NEEDS[params.need].label))
    tool = world.add(Entity(id="tool", kind="thing", type=TOOLS[params.tool].label, label=TOOLS[params.tool].label))
    world.facts.update(hero=hero, sidekick=sidekick, parent=parent, need_cfg=NEEDS[params.need], tool_cfg=TOOLS[params.tool], need=need, tool=tool)
    tell(world, params)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
