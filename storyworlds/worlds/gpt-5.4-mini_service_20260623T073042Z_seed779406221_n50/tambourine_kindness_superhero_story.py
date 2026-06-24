#!/usr/bin/env python3
"""
storyworlds/worlds/tambourine_kindness_superhero_story.py
========================================================

A small standalone storyworld in the style of a superhero story.

Seed premise:
- A child superhero uses a tambourine during a neighborhood performance.
- Kindness matters: the hero can notice someone left out, turn the moment,
  and make the team feel bigger and brighter.
- The world is tiny, state-driven, and readable by children.

This script models a simple premise/tension/turn/resolution:
- A neighborhood performance is about to start.
- The hero wants to shine with their tambourine.
- A shy helper or neighbor feels left out.
- The hero uses kindness to share, include, and rescue the mood.
- The ending proves what changed in the world: joy rises, loneliness falls,
  and the tambourine becomes a shared symbol of teamwork.

The implementation follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of results.py for QAItem, StoryError, StorySample
- lazy import of asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- --verify compares Python and ASP parity and exercises generated stories
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owns: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    bright: str
    joy_boost: float
    risk: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class ObjectConfig:
    id: str
    label: str
    phrase: str
    owner_kind: str
    region: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpingTool:
    id: str
    label: str
    phrase: str
    fix: str
    guards: set[str]
    helpful: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather: str = ""

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
        clone.fired = set(self.fired)
        clone.weather = self.weather
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    helper_tool: str
    hero: str
    sidekick: str
    hero_type: str
    sidekick_type: str
    seed: Optional[int] = None


PLACES = {
    "square": Place(id="square", label="the sunny square", indoor=False, afford={"perform"}),
    "park": Place(id="park", label="the neighborhood park", indoor=False, afford={"perform"}),
    "hall": Place(id="hall", label="the community hall", indoor=True, afford={"perform"}),
}

ACTIVITIES = {
    "parade": Activity(
        id="parade",
        verb="lead the parade",
        gerund="leading the parade",
        rush="dash ahead of the crowd",
        bright="the drums and banners made the street feel alive",
        joy_boost=1.0,
        risk="left out",
        keywords={"superhero", "crowd", "joy"},
    ),
    "show": Activity(
        id="show",
        verb="perform on stage",
        gerund="performing on stage",
        rush="jump onto the stage",
        bright="the spotlight made the whole room sparkle",
        joy_boost=1.0,
        risk="shy",
        keywords={"superhero", "stage", "music"},
    ),
    "rescue": Activity(
        id="rescue",
        verb="help the crowd",
        gerund="helping the crowd",
        rush="run toward the noise",
        bright="the air felt bold and busy",
        joy_boost=1.0,
        risk="lonely",
        keywords={"superhero", "help", "kindness"},
    ),
}

ITEMS = {
    "tambourine": ObjectConfig(
        id="tambourine",
        label="tambourine",
        phrase="a bright red tambourine",
        owner_kind="hero",
        region="hands",
        tags={"tambourine", "music"},
    ),
    "cape": ObjectConfig(
        id="cape",
        label="cape",
        phrase="a blue cape with a silver star",
        owner_kind="hero",
        region="back",
        tags={"cape", "superhero"},
    ),
    "badge": ObjectConfig(
        id="badge",
        label="kindness badge",
        phrase="a kindness badge",
        owner_kind="sidekick",
        region="chest",
        tags={"kindness"},
    ),
}

TOOLS = {
    "share": HelpingTool(
        id="share",
        label="share the tambourine",
        phrase="share the tambourine",
        fix="let the neighbor tap a happy beat too",
        guards={"left out", "shy", "lonely"},
        tags={"kindness", "tambourine"},
    ),
    "invite": HelpingTool(
        id="invite",
        label="invite the neighbor in",
        phrase="invite the neighbor into the circle",
        fix="move over and make room",
        guards={"left out", "shy", "lonely"},
        tags={"kindness"},
    ),
    "cheer": HelpingTool(
        id="cheer",
        label="cheer kindly",
        phrase="cheer kindly and point to a safe place",
        fix="speak gently and guide everyone together",
        guards={"left out", "shy", "lonely"},
        tags={"kindness"},
    ),
}

NAMES = ["Maya", "Leo", "Nina", "Eli", "Ava", "Noah", "Zoe", "Milo"]
TRAITS = ["brave", "kind", "quick", "bright", "gentle", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for a in ACTIVITIES:
            for item in ITEMS:
                if item == "tambourine" and a in {"parade", "show", "rescue"}:
                    out.append((p, a, item))
    return out


def reasonableness_gate(place: Place, activity: Activity, item: ObjectConfig) -> bool:
    return place.id in PLACES and activity.id in ACTIVITIES and item.id in ITEMS and item.id == "tambourine"


def select_tool(activity: Activity) -> Optional[HelpingTool]:
    for tool in TOOLS.values():
        if activity.risk in tool.guards:
            return tool
    return None


def outcome_of(params: StoryParams) -> str:
    return "kindness" if params.helper_tool in TOOLS else "none"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero kindness storyworld with a tambourine.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper-tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-type", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, item = rng.choice(sorted(combos))
    helper_tool = args.helper_tool or rng.choice(sorted(TOOLS))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    sidekick_type = args.sidekick_type or ("boy" if hero_type == "girl" else "girl")
    hero = args.hero or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place, activity, item, helper_tool, hero, sidekick, hero_type, sidekick_type)


def _initialize_entity(ent: Entity) -> None:
    for key in ["joy", "lonely", "kindness", "pride", "shyness"]:
        ent.memes.setdefault(key, 0.0)
    for key in ["grip", "noise"]:
        ent.meters.setdefault(key, 0.0)


def tell(place: Place, activity: Activity, item: ObjectConfig, tool: HelpingTool,
         hero_name: str, sidekick_name: str, hero_type: str, sidekick_type: str) -> World:
    world = World(place)
    world.weather = "bright" if not place.indoor else "warm"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type=sidekick_type, role="sidekick"))
    crowd = world.add(Entity(id="crowd", kind="place", type="crowd", label="the crowd"))
    tamb = world.add(Entity(id="tambourine", type="instrument", label="tambourine"))
    badge = world.add(Entity(id="badge", type="thing", label="kindness badge"))
    for e in [hero, sidekick, crowd, tamb, badge]:
        _initialize_entity(e)

    hero.owns = tamb.id
    sidekick.owns = badge.id
    hero.carries = tamb.id
    world.facts["activity"] = activity
    world.facts["item_cfg"] = item
    world.facts["tool_cfg"] = tool
    world.facts["hero"] = hero
    world.facts["sidekick"] = sidekick
    world.facts["place"] = place

    hero.memes["joy"] += 1
    sidekick.memes["shyness"] += 1
    world.say(f"{hero.id} was a small superhero with a bright {item.label} and a big smile.")
    world.say(f"{hero.id} and {sidekick.id} went to {place.label}, where {activity.bright}.")
    world.para()
    world.say(f"{hero.id} wanted to {activity.verb}, and {hero.pronoun('possessive')} {item.label} shone in {hero.pronoun('possessive')} hands.")
    world.say(f"But {sidekick.id} stood a little behind the line, looking {activity.risk}.")
    hero.memes["pride"] += 1
    sidekick.memes["lonely"] += 1

    world.para()
    if activity.risk in {"left out", "shy", "lonely"}:
        world.say(f"{hero.id} noticed the small frown and chose kindness instead of a big solo moment.")
        world.say(f'"Come tap with me," {hero.id} said, and {tool.fix}.')
        sidekick.memes["lonely"] = 0.0
        sidekick.memes["joy"] += 1
        hero.memes["kindness"] += 1
        hero.memes["joy"] += 1
        world.say(f"{sidekick.id} stepped closer, and soon the two of them were making one happy beat together.")
        world.para()
        world.say(f"The crowd cheered because the superhero used {item.label} to share, not to show off.")
        world.say(f"At the end, {hero.id} and {sidekick.id} stood side by side, bright as a team.")
    else:
        world.say(f"{hero.id} played on, but the room felt less warm until {hero.id} remembered to include {sidekick.id}.")
        world.say(f"That small act of kindness turned the music into a team song.")

    world.facts["resolved"] = True
    world.facts["tool"] = tool
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    activity = f["activity"]
    item = f["item_cfg"]
    return [
        f'Write a short superhero story for a young child about {hero.id} and {sidekick.id} with a {item.label}.',
        f"Tell a gentle superhero story where {hero.id} uses a {item.label} while {sidekick.id} feels left out, and kindness changes the scene.",
        f'Write a child-friendly story that includes a tambourine and ends with the hero sharing it kindly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    activity = f["activity"]
    item = f["item_cfg"]
    tool = f["tool_cfg"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who is the story about at {place.label}?",
            answer=f"It is about {hero.id}, a small superhero, and {sidekick.id}, who came along to help.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to {activity.verb} with the {item.label} and make the moment shine.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} look lonely at first?",
            answer=f"{sidekick.id} felt left out while the music was starting, so {hero.id} chose kindness.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} used {tool.label} and let {sidekick.id} join in, so the two of them shared the music.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tambourine?",
            answer="A tambourine is a small hand drum with little jingles that make a bright rattling sound when you shake or tap it.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means noticing someone else's feelings and helping them feel welcome, safe, and included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} memes={dict(e.memes)} meters={dict(e.meters)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,I) :- place(P), activity(A), item(I), I = tambourine.
kindness_turn(H,S) :- hero(H), sidekick(S), lonely(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("tambourine", "tambourine"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: ASP matches Python valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - p))
    print("only in Python:", sorted(p - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    activity = ACTIVITIES[params.activity]
    item = ITEMS[params.item]
    tool = TOOLS[params.helper_tool]
    if not reasonableness_gate(place, activity, item):
        raise StoryError("Invalid combination for this world.")
    world = tell(place, activity, item, tool, params.hero, params.sidekick, params.hero_type, params.sidekick_type)
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
        for combo in asp_valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
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


CURATED = [
    StoryParams("square", "show", "tambourine", "share", "Maya", "Leo", "girl", "boy"),
    StoryParams("park", "parade", "tambourine", "invite", "Eli", "Ava", "boy", "girl"),
    StoryParams("hall", "rescue", "tambourine", "cheer", "Nina", "Milo", "girl", "boy"),
]


if __name__ == "__main__":
    main()
