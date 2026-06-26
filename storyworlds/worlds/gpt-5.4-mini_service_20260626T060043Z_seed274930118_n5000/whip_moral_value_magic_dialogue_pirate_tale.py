#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/whip_moral_value_magic_dialogue_pirate_tale.py
===============================================================================================================

A small standalone pirate-tale story world with:
- a whip-shaped tool
- a magic element
- dialogue
- a clear moral value turn

The world is intentionally tiny and constraint-checked:
a pirate crew faces a small problem, a magical whip can help or cause trouble,
and the ending proves how the choice changed the world.
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
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    wielded_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the moonlit cove"
    afford_magic: bool = True
    afford_whip: bool = True


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    kind: str
    magic: bool = False
    moral: str = ""
    can_help: bool = False


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    relic: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


SETTINGS = {
    "cove": Setting(place="the moonlit cove"),
    "harbor": Setting(place="the sleepy harbor"),
    "island": Setting(place="the palm island shore"),
}

HEROES = {
    "captain": ("Captain Mira", "captain"),
    "pirate": ("Pip", "pirate"),
    "boy": ("Finn", "boy"),
    "girl": ("Nora", "girl"),
}

HELPERS = {
    "old_sailor": ("Old Sal", "pirate"),
    "mate": ("Jory", "boy"),
    "mate_girl": ("Mina", "girl"),
    "parrot": ("Pico", "bird"),
}

RELICS = {
    "whip": Relic(
        id="whip",
        label="a silver whip",
        phrase="a silver whip with a star-shaped handle",
        kind="whip",
        magic=True,
        moral="use power wisely",
        can_help=True,
    ),
    "map": Relic(
        id="map",
        label="a star map",
        phrase="a star map that glowed softly",
        kind="map",
        magic=True,
        moral="listen before acting",
        can_help=False,
    ),
    "shell": Relic(
        id="shell",
        label="a pearl shell",
        phrase="a pearl shell that hummed like a song",
        kind="shell",
        magic=True,
        moral="share kindly",
        can_help=False,
    ),
}

MORALS = [
    "use power wisely",
    "share kindly",
    "listen before acting",
]

DIALOGUE_BEATS = [
    "“Wait,” said the helper, “that whip is magic, but magic should not be used to bully the sea.”",
    "“Then what should we do?” asked the pirate.",
    "“Try kindness first,” said the helper, “and save the whip for a safe job.”",
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for hero in HEROES:
            for relic in RELICS:
                if relic == "whip":
                    out.append((place, hero, relic))
    return out


def reason_invalid(relic: str) -> str:
    if relic != "whip":
        return (
            f"(No story: this seed world needs the whip to carry the conflict and turn. "
            f"Try --relic whip.)"
        )
    return "(No story: invalid pirate story choice.)"


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    hero_name, hero_type = HEROES[params.hero]
    helper_name, helper_type = HELPERS[params.helper]
    relic = RELICS[params.relic]

    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name))
    tool = world.add(Entity(
        id="relic",
        kind="thing",
        type=relic.kind,
        label=relic.label,
        phrase=relic.phrase,
        owner=hero.id,
    ))

    hero.memes["greed"] = 1.0
    helper.memes["care"] = 1.0
    tool.meters["magic"] = 1.0

    world.facts.update(
        setting=setting,
        hero=hero,
        helper=helper,
        relic=relic,
        tool=tool,
        moral=relic.moral,
    )
    return world


def tell(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    relic: Relic = world.facts["relic"]
    tool: Entity = world.facts["tool"]

    world.say(
        f"At {world.setting.place}, {hero.label} was a little pirate who loved shiny surprises."
    )
    world.say(
        f"{hero.label} found {tool.phrase} tucked under a broken crate, and {hero.pronoun()} said, "
        f"“This will make me the biggest pirate on the bay!”"
    )

    world.para()
    world.say(
        f"That night, a sleepy storm tied the sails in knots. The crew could not leave the cove."
    )
    world.say(
        f"{hero.label} lifted the whip and snapped, “I can scare the storm away!”"
    )
    world.say(
        f"But {helper.label} stepped closer and said, “A whip can crack a rope, not a storm. "
        f"Magic is not for being cruel.”"
    )
    world.say(DIALOGUE_BEATS[1])
    world.say(DIALOGUE_BEATS[2])

    world.para()
    hero.memes["listening"] = 1.0
    hero.memes["greed"] = 0.0
    hero.memes["kindness"] = 1.0
    tool.meters["magic"] += 1.0
    tool.meters["used_safely"] = 1.0

    world.say(
        f"{hero.label} nodded and tried a gentler spell instead. The whip was used only to tap "
        f"the lantern three times, and the glowing light showed the crew a safe path around the rocks."
    )
    world.say(
        f"The storm stayed wild, but the ship slipped through on a calm current, and {hero.label} "
        f"shared the credit with {helper.label}."
    )
    world.say(
        f"By morning, the crew was laughing at breakfast, and the silver whip hung quietly by the mast, "
        f"waiting for a good and kind use."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a child that includes a magic whip and a spoken warning.',
        f"Tell a story where {f['hero'].label} learns to use power wisely while sailing at {world.setting.place}.",
        "Write a gentle pirate story with dialogue, magic, and a moral lesson about kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    relic: Relic = world.facts["relic"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who found the magical whip at {place}?",
            answer=f"{hero.label} found {relic.phrase} at {place}.",
        ),
        QAItem(
            question="Why did the helper warn the pirate not to use the whip the wrong way?",
            answer=(
                f"{helper.label} warned that the whip should not be used to bully the sea. "
                f"The helper wanted {hero.label} to use power wisely."
            ),
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=(
                f"{hero.label} stopped trying to act greedy and chose a kinder plan. "
                f"The crew got a safe path, and the whip became something to use gently."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whip?",
            answer="A whip is a long tool with a handle and a thin end. People can use it carefully, but it can hurt if it is used meanly.",
        ),
        QAItem(
            question="What does magic mean in a pirate tale?",
            answer="Magic means something strange and powerful can happen, like a glowing object or a spell that changes what people can do.",
        ),
        QAItem(
            question="Why are dialogues useful in stories?",
            answer="Dialogue lets characters speak to each other so readers can hear their worries, ideas, and feelings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_place(cove).
valid_place(harbor).
valid_place(island).

valid_hero(captain).
valid_hero(pirate).
valid_hero(boy).
valid_hero(girl).

valid_relic(whip).

valid_story(P, H, R) :- valid_place(P), valid_hero(H), valid_relic(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("valid_place", p))
    for h in HEROES:
        lines.append(asp.fact("valid_hero", h))
    for r in RELICS:
        lines.append(asp.fact("valid_relic", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    ap = set(asp.atoms(model, "valid_story"))
    if py == ap:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    if py - ap:
        print("only in python:", sorted(py - ap))
    if ap - py:
        print("only in ASP:", sorted(ap - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate tale world with magic, dialogue, and a moral turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--relic", choices=RELICS)
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
    if args.relic and args.relic != "whip":
        raise StoryError(reason_invalid(args.relic))
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(list(HEROES))
    helper = args.helper or rng.choice(list(HELPERS))
    relic = args.relic or "whip"
    return StoryParams(place=place, hero=hero, helper=helper, relic=relic)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
    tell(world)
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
    StoryParams(place="cove", hero="captain", helper="old_sailor", relic="whip"),
    StoryParams(place="harbor", hero="pirate", helper="mate", relic="whip"),
    StoryParams(place="island", hero="girl", helper="mate_girl", relic="whip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_stories():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
