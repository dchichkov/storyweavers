#!/usr/bin/env python3
"""
Story world: a folk-tale quest about a husband, a guild, and a pollutant.

A small, self-contained story simulation in the style of a folk tale. The hero
remembers an old warning in a flashback, gathers courage, and leads a quest to
remove a pollutant from a village waterway.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)  # physical state
    memes: dict[str, float] = field(default_factory=dict)   # emotional state

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"husband", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"wife", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"guild", "group", "villagers"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    hero_name: str
    spouse_name: str
    guild_name: str
    pollutant: str
    quest: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str
    waterway: str
    pollutant_name: str
    quest_label: str
    flashback_scene: str
    brave_action: str
    resolution_image: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "brook": Setting(
        place="the mossy brook",
        waterway="brook",
        pollutant_name="black slime",
        quest_label="clear the brook",
        flashback_scene="the old mill bridge",
        brave_action="step into the cold water",
        resolution_image="the brook ran clear and bright under the reeds",
    ),
    "well": Setting(
        place="the village well",
        waterway="well",
        pollutant_name="rusty ooze",
        quest_label="clean the well",
        flashback_scene="the stone stair by the well",
        brave_action="lower the bucket into the dark water",
        resolution_image="the well water shone like a silver coin",
    ),
    "pond": Setting(
        place="the willow pond",
        waterway="pond",
        pollutant_name="green scum",
        quest_label="save the pond",
        flashback_scene="the willow shade by the pond",
        brave_action="push back the floating weeds with a long pole",
        resolution_image="the pond held the sky like a blue bowl",
    ),
}

POLLUTANTS = {
    "slime": "black slime",
    "ooze": "rusty ooze",
    "scum": "green scum",
}

QUESTS = {
    "clean": "clear the brook",
    "purify": "clean the well",
    "save": "save the pond",
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
polluted(W) :- pollutant(W, _).
quest_ready(H, W) :- husband(H), polluted(W), brave(H), guild_help(G), guild(G).
quest_success(W) :- quest_ready(_, W), action_done(W), pollutant_removed(W).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key, val in POLLUTANTS.items():
        lines.append(asp.fact("pollutant", key, val))
    for key, val in QUESTS.items():
        lines.append(asp.fact("quest", key, val))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_success/1."))
    return sorted(set(asp.atoms(model, "quest_success")))


def asp_verify() -> int:
    expected = {("brook",), ("well",), ("pond",)}
    got = set(asp_valid())
    if got == expected:
        print(f"OK: ASP and Python gates agree on {len(got)} settings.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  asp:", sorted(got))
    print("  py :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("Unknown place for this tale.")
    if params.pollutant not in POLLUTANTS:
        raise StoryError("Unknown pollutant for this tale.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest for this tale.")
    if params.quest != params.place and params.quest not in {"clean", "purify", "save"}:
        raise StoryError("The quest does not fit the chosen place.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)

    husband = world.add(Entity(
        id="Husband",
        kind="character",
        type="husband",
        label=params.hero_name,
        phrase=f"a husband named {params.hero_name}",
        memes={"love": 1.0, "duty": 1.0, "bravery": 0.0, "fear": 0.0},
    ))
    spouse = world.add(Entity(
        id="Spouse",
        kind="character",
        type="wife",
        label=params.spouse_name,
        phrase=f"his wife {params.spouse_name}",
        memes={"hope": 1.0},
    ))
    guild = world.add(Entity(
        id="Guild",
        kind="character",
        type="guild",
        label=params.guild_name,
        phrase=f"the guild",
        plural=True,
        memes={"doubt": 0.0, "trust": 1.0},
    ))
    pollutant = world.add(Entity(
        id="Pollutant",
        kind="thing",
        type="pollutant",
        label=setting.pollutant_name,
        phrase=f"{setting.pollutant_name} in the {setting.waterway}",
        location=setting.place,
        meters={"spreading": 1.0, "threat": 1.0},
    ))

    world.facts.update(
        husband=husband,
        spouse=spouse,
        guild=guild,
        pollutant=pollutant,
        setting=setting,
        params=params,
    )
    return world


def flashback(world: World) -> None:
    husband = world.get("Husband")
    husband.memes["sadness"] = 1.0
    world.say(
        f"Long before this day, at {world.setting.flashback_scene}, "
        f"{husband.label} had seen the same foul stain spread through the water."
    )
    world.say(
        f"He remembered how he had waited too long then, and the fish had gone quiet."
    )


def summon_guild(world: World) -> None:
    husband = world.get("Husband")
    guild = world.get("Guild")
    world.say(
        f"So {husband.label} went to the guild and asked for help on a quest "
        f"to {world.setting.quest_label}."
    )
    world.say(
        f"The guild listened, and their old foreman nodded at the brave request."
    )
    guild.memes["trust"] += 1.0


def choose_bravery(world: World) -> None:
    husband = world.get("Husband")
    husband.memes["fear"] += 1.0
    husband.memes["bravery"] += 1.0
    world.say(
        f"{husband.label} felt fear at the dark water, but he held it like a small stone "
        f"and chose bravery instead."
    )
    world.say(
        f"At last he said he would {world.setting.brave_action} with a steady heart."
    )


def do_quest(world: World) -> None:
    husband = world.get("Husband")
    pollutant = world.get("Pollutant")
    guild = world.get("Guild")

    husband.meters["work"] = 1.0
    pollutant.meters["spreading"] = 0.0
    pollutant.meters["removed"] = 1.0
    guild.memes["trust"] += 1.0

    world.say(
        f"With the guild beside him, {husband.label} worked through the mud and "
        f"pulled the {pollutant.label} away from the water."
    )
    world.say(
        f"He used baskets, reeds, and a long rope, and the dark stuff at last let go."
    )


def resolve(world: World) -> None:
    husband = world.get("Husband")
    spouse = world.get("Spouse")
    pollutant = world.get("Pollutant")

    husband.memes["joy"] = 1.0
    spouse.memes["relief"] = 1.0
    world.say(
        f"When the work was done, {husband.label} smiled back to {spouse.label}, "
        f"because the danger was gone."
    )
    world.say(
        f"{world.setting.resolution_image}; "
        f"the villagers came to praise the husband, the guild, and the brave quest."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get("Husband")

    world.say(
        f"Once in {world.setting.place}, there lived a kind husband named {hero.label}."
    )
    world.say(
        f"He loved his home, his wife, and the small folk of the village."
    )
    world.para()

    flashback(world)
    summon_guild(world)
    choose_bravery(world)
    world.para()

    do_quest(world)
    resolve(world)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    s = world.setting
    return [
        f"Write a folk tale about a husband named {p.hero_name} who leads a guild on a quest to remove {s.pollutant_name} from {s.place}.",
        f"Tell a child-friendly story with a flashback, bravery, and a helpful guild in {s.place}.",
        f"Write a short folk tale where a husband remembers an old warning and finds courage to save {s.waterway} from pollution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    s = world.setting
    return [
        QAItem(
            question=f"Who led the quest in {s.place}?",
            answer=f"The husband named {p.hero_name} led the quest with help from his guild.",
        ),
        QAItem(
            question=f"What did {p.hero_name} remember in the flashback?",
            answer=f"He remembered the old trouble at {s.flashback_scene} and how the water had turned bad before.",
        ),
        QAItem(
            question=f"Why was {p.hero_name} brave?",
            answer=f"He was brave because he wanted to protect his home and help the village clean away {s.pollutant_name}.",
        ),
        QAItem(
            question=f"What changed at the end of the tale?",
            answer=f"The polluted water was cleaned, and {s.resolution_image}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    s = world.setting
    return [
        QAItem(
            question="What is a guild?",
            answer="A guild is a group of workers or helpers who join together to do important work.",
        ),
        QAItem(
            question="What is a pollutant?",
            answer="A pollutant is something dirty or harmful that makes water, air, or land unclean.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the choice to do something hard or scary because it is the right thing to do.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before the main part of the tale.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / CLI
# ---------------------------------------------------------------------------

HERO_NAMES = ["Rowan", "Alaric", "Bram", "Cedric", "Edwin", "Gareth"]
SPOUSE_NAMES = ["Mira", "Elin", "Beth", "Lysa", "Anwen", "Sorrel"]
GUILD_NAMES = ["the River Guild", "the Reed Guild", "the Lantern Guild"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale about a husband, a guild, and a pollutant.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero-name")
    ap.add_argument("--spouse-name")
    ap.add_argument("--guild-name", choices=GUILD_NAMES)
    ap.add_argument("--pollutant", choices=sorted(POLLUTANTS))
    ap.add_argument("--quest", choices=sorted(QUESTS))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    pollutant = args.pollutant or rng.choice(sorted(POLLUTANTS))
    quest = args.quest or rng.choice(sorted(QUESTS))
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    spouse_name = args.spouse_name or rng.choice(SPOUSE_NAMES)
    guild_name = args.guild_name or rng.choice(GUILD_NAMES)
    return StoryParams(
        place=place,
        hero_name=hero_name,
        spouse_name=spouse_name,
        guild_name=guild_name,
        pollutant=pollutant,
        quest=quest,
    )


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="brook", hero_name="Rowan", spouse_name="Mira", guild_name="the River Guild", pollutant="slime", quest="clean"),
    StoryParams(place="well", hero_name="Bram", spouse_name="Elin", guild_name="the Lantern Guild", pollutant="ooze", quest="purify"),
    StoryParams(place="pond", hero_name="Cedric", spouse_name="Lysa", guild_name="the Reed Guild", pollutant="scum", quest="save"),
]


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify_gate() -> int:
    import asp
    model = asp.one_model(asp_program("#show quest_success/1."))
    got = set(asp.atoms(model, "quest_success"))
    expected = {("brook",), ("well",), ("pond",)}
    if got == expected:
        print(f"OK: ASP gate matches Python gate ({len(got)} settings).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("asp:", sorted(got))
    print("py :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_success/1."))
        return
    if args.verify:
        sys.exit(asp_verify_gate())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show quest_success/1."))
        vals = sorted(set(asp.atoms(model, "quest_success")))
        print(f"{len(vals)} compatible story settings:")
        for (place,) in vals:
            print(f"  {place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story not in seen:
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} at {p.place} ({p.pollutant})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
