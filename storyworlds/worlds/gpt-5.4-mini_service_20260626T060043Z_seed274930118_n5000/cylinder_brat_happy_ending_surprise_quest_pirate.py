#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cylinder_brat_happy_ending_surprise_quest_pirate.py
================================================================================================

A small pirate-tale storyworld with a bratty child, a mysterious cylinder,
a quest, a surprise, and a happy ending.

Premise seed:
- A young pirate's helper is a brat.
- The child loves a shiny cylinder found on the ship.
- A sea quest begins when the grown-up notices the cylinder is not a toy.
- A surprise inside the cylinder changes the plan.
- The ending is happy because the child earns a better role and the ship stays safe.

The world model tracks:
- physical meters: curiosity, mischief, danger, soot, treasure, trust
- emotional memes: joy, annoyance, pride, surprise, fear, relief, loyalty

Story shape:
1) Setup: the child and the cylinder on a pirate ship.
2) Tension: the brat wants to rush off with the cylinder during a quest.
3) Surprise turn: the cylinder hides a tiny map clue.
4) Resolution: the child helps on the quest, proving they are not just a brat.
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


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    reveal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.place_detail: str = ""

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
        clone.place_detail = self.place_detail
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "shipdeck": Setting(place="the ship deck", affords={"quest", "surprise"}),
    "cabin": Setting(place="the lantern-lit cabin", indoors=True, affords={"quest", "surprise"}),
    "harbor": Setting(place="the busy harbor", affords={"quest", "surprise"}),
}

QUESTS = {
    "quest": Quest(
        id="quest",
        verb="search for the lost star map",
        gerund="searching for the lost star map",
        rush="dash toward the captain's chart table",
        danger="sail into the wrong waters",
        reveal="a tiny rolled map hidden in the cylinder",
        keyword="quest",
        tags={"quest", "map", "treasure"},
    ),
    "surprise": Quest(
        id="surprise",
        verb="open the mystery cylinder",
        gerund="opening the mystery cylinder",
        rush="snatch the cylinder from the table",
        danger="break the clue inside",
        reveal="a secret note tied with blue string",
        keyword="surprise",
        tags={"surprise", "cylinder"},
    ),
}

PRIZES = {
    "cylinder": Prize(
        id="cylinder",
        label="cylinder",
        phrase="a smooth brass cylinder",
        region="hands",
        fragile=True,
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="sailor gloves",
        helps={"quest", "surprise"},
        covers={"hands"},
        prep="slip on sailor gloves first",
        tail="slipped on the sailor gloves",
        plural=True,
    ),
    "satchel": Gear(
        id="satchel",
        label="a canvas satchel",
        helps={"quest"},
        covers={"hands"},
        prep="put the cylinder in a canvas satchel",
        tail="tucked the cylinder safely in the satchel",
    ),
}

CHILD_NAMES = ["Milo", "Nell", "Pip", "Rosa", "Jett", "Tessa", "Finn", "Ada"]
GROWNUP_NAMES = ["Captain Brine", "Matey Rook", "Old Salt"]

TRAITS = ["bratty", "bold", "curious", "stubborn", "cheeky"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    grownup: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def is_reasonable(setting: Setting, quest: Quest, prize: Prize) -> bool:
    return quest.id in setting.affords and prize.id == "cylinder"


def choose_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR.values():
        if quest.id in gear.helps and prize.region in gear.covers:
            return gear
    return None


def reason_rejection(setting: Setting, quest: Quest, prize: Prize) -> str:
    if quest.id not in setting.affords:
        return f"(No story: {setting.place} does not support that pirate quest.)"
    return f"(No story: the cylinder setup has no safe pirate fix.)"


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
def predict_outcome(world: World, hero: Entity, quest: Quest, prize: Entity) -> dict:
    sim = world.copy()
    do_quest(sim, sim.get(hero.id), quest, narrate=False)
    cyl = sim.get(prize.id)
    return {
        "lost": cyl.memes.get("lost", 0) >= THRESHOLD,
        "reveal": sim.facts.get("reveal", ""),
    }


def do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    world.facts["quest_started"] = True
    hero.meters["curiosity"] = hero.meters.get("curiosity", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["annoyance"] = hero.memes.get("annoyance", 0) + 0.5
    if narrate:
        world.say(f"{hero.id} kept peeking at the {quest.keyword} and wanted to rush ahead.")
    if quest.id == "surprise":
        world.facts["reveal"] = quest.reveal
        world.facts["surprise"] = True
        if narrate:
            world.say(f"That was when the {quest.keyword} gave a surprise: {quest.reveal}.")


def tension(world: World, hero: Entity, grownup: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    grownup.memes["worry"] = grownup.memes.get("worry", 0) + 1
    world.say(
        f"\"Easy now,\" {grownup.id} said. \"That {prize.label} is for the quest, not for a bratty game.\""
    )
    world.say(f"But {hero.id} only puffed up and tried to {quest.rush}.")


def surprise_turn(world: World, hero: Entity, quest: Quest, prize: Prize) -> None:
    world.say(f"Then the {prize.label} rolled open with a surprise.")
    world.say(f"Inside was {quest.reveal}, and the room fell quiet for a blink.")


def compromise(world: World, hero: Entity, grownup: Entity, quest: Quest, prize: Prize) -> Optional[Gear]:
    gear = choose_gear(quest, prize)
    if gear is None:
        return None
    if world.facts.get("surprise"):
        world.say(
            f"{grownup.id} smiled and said, \"If you can carry it carefully, you can help.\""
        )
        world.say(f"\"First, {gear.prep}.\"")
    return gear


def resolution(world: World, hero: Entity, grownup: Entity, quest: Quest, prize: Prize, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.memes["defiance"] = 0
    hero.memes["loyalty"] = hero.memes.get("loyalty", 0) + 1
    world.say(
        f"{hero.id} stopped acting like a brat and helped with the {quest.keyword} instead."
    )
    world.say(
        f"They {gear.tail}, followed the little clue, and found the right path before sunset."
    )
    world.say(
        f"In the end, {hero.id} was not in trouble at all; {hero.pronoun()} was trusted with the next lookout."
    )
    world.say(
        f"The ship sailed on with the {prize.label} safe, the clue solved, and a happy ending on the tide."
    )


def tell(setting: Setting, quest: Quest, prize: Prize, hero_name: str, grownup_name: str, trait: str) -> World:
    world = World(setting)
    world.place_detail = setting.place

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type="boy" if hero_name in {"Milo", "Pip", "Jett", "Finn"} else "girl",
        meters={"curiosity": 0, "mischief": 0},
        memes={"joy": 0, "annoyance": 0, "defiance": 0, "pride": 0, "loyalty": 0},
    ))
    grownup = world.add(Entity(
        id=grownup_name,
        kind="character",
        type="man",
        meters={"duty": 1},
        memes={"worry": 0, "care": 1},
    ))
    cylinder = world.add(Entity(
        id=prize.id,
        type="thing",
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=grownup.id,
        carried_by=hero.id,
        meters={"danger": 0, "treasure": 0},
        memes={"annoyance": 0, "surprise": 0, "lost": 0},
    ))

    world.say(
        f"On the ship deck, {hero.id} was a {trait} little pirate helper who loved the shiny {cylinder.label}."
    )
    world.say(
        f"{grownup.id} had brought a {quest.keyword} and said it needed careful hands."
    )

    world.para()
    world.say(
        f"At {setting.place}, {hero.id} wanted to {quest.verb}, but {hero.pronoun('possessive')} hands were already reaching for the {cylinder.label}."
    )
    tension(world, hero, grownup, quest, cylinder)
    do_quest(world, hero, quest)
    surprise_turn(world, hero, quest, cylinder)

    world.para()
    gear = compromise(world, hero, grownup, quest, cylinder)
    if gear is None:
        raise StoryError(reason_rejection(setting, quest, cylinder))
    resolution(world, hero, grownup, quest, cylinder, gear)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        prize=cylinder,
        quest=quest,
        gear=gear,
        surprise=world.facts.get("surprise", False),
        reveal=world.facts.get("reveal", ""),
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a short pirate tale for a child named {hero.id} that includes a cylinder, a quest, and a surprise.',
        f"Tell a happy-ending story where {hero.id} acts bratty at first, then helps with {quest.verb}.",
        f'Write a simple sea adventure using the words "cylinder" and "brat" and ending in trust.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    quest = f["quest"]
    cyl = f["prize"]
    return [
        QAItem(
            question=f"Who was the story about on the pirate ship?",
            answer=f"It was about {hero.id}, a {hero.pronoun('subject')} little pirate helper who started out acting bratty.",
        ),
        QAItem(
            question=f"What shiny thing did {hero.id} want to grab?",
            answer=f"{hero.id} wanted to grab the {cyl.label}, a smooth brass cylinder that mattered for the quest.",
        ),
        QAItem(
            question=f"Why did {grownup.id} tell {hero.id} to be careful?",
            answer=f"{grownup.id} was worried because the {cyl.label} was part of the quest and could not be broken or lost.",
        ),
        QAItem(
            question=f"What surprise was found inside the cylinder?",
            answer=f"The cylinder held {f['reveal']}, which changed the moment from trouble into a real quest clue.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily because {hero.id} helped with the quest, earned trust, and kept the {cyl.label} safe.",
        ),
    ]


KNOWLEDGE = {
    "cylinder": [
        QAItem(
            question="What is a cylinder?",
            answer="A cylinder is a round shape with straight sides and circle-shaped ends, like a tube or a can.",
        )
    ],
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task where someone searches for something important or tries to solve a problem.",
        )
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes you stop and look again.",
        )
    ],
    "pirate": [
        QAItem(
            question="What do pirates usually do in stories?",
            answer="In stories, pirates sail ships, search for treasure, and have adventures at sea.",
        )
    ],
    "brat": [
        QAItem(
            question="What does bratty mean?",
            answer="Bratty means acting rude, pushy, or hard to please, especially when someone wants their own way.",
        )
    ],
    "happy": [
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish the story feeling okay or glad.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    tags.add("cylinder")
    tags.add("pirate")
    out: list[QAItem] = []
    for key in ["cylinder", "quest", "surprise", "pirate", "brat", "happy"]:
        if key in tags or key in {"brat", "happy"}:
            out.extend(KNOWLEDGE[key])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A cylinder story is reasonable only when the setting can host the quest.
reasonable_story(S, Q, P) :- setting(S), quest(Q), prize(P), affords(S, Q), prize_ok(P).

% A surprise is part of the reasoning when the quest has a reveal.
has_surprise(Q) :- quest(Q), reveal(Q, _).

% A compatible fix exists when the helper gear covers the prize region and helps the quest.
has_fix(Q, P) :- quest(Q), prize(P), gear(G), helps(G, Q), covers(G, R), prize_region(P, R).

valid_story(S, Q, P) :- reasonable_story(S, Q, P), has_surprise(Q), has_fix(Q, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("reveal", qid, q.reveal))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
        lines.append(asp.fact("prize_ok", pid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for q in sorted(g.helps):
            lines.append(asp.fact("helps", gid, q))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(clingo_model, "valid_story"))
    python_set = set(valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_stories() ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            for pid, prize in PRIZES.items():
                if is_reasonable(setting, quest, prize) and choose_gear(quest, prize):
                    out.append((sid, qid, pid))
    return out


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale storyworld with a cylinder, a brat, a quest, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name", choices=CHILD_NAMES)
    ap.add_argument("--grownup", choices=GROWNUP_NAMES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    name = args.name or rng.choice(CHILD_NAMES)
    grownup = args.grownup or rng.choice(GROWNUP_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if args.setting and args.quest:
        if not is_reasonable(SETTINGS[args.setting], QUESTS[args.quest], PRIZES["cylinder"]):
            raise StoryError(reason_rejection(SETTINGS[args.setting], QUESTS[args.quest], PRIZES["cylinder"]))
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    return StoryParams(setting=setting, quest=quest, name=name, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], PRIZES["cylinder"], params.name, params.grownup, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="shipdeck", quest="surprise", name="Pip", grownup="Captain Brine", trait="bratty"),
    StoryParams(setting="cabin", quest="quest", name="Milo", grownup="Matey Rook", trait="curious"),
    StoryParams(setting="harbor", quest="surprise", name="Rosa", grownup="Old Salt", trait="cheeky"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid pirate stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
