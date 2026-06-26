#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale:
a child on a ship, a quest for a missing sixpence, a twist, and a moral value
revealed through action rather than explanation.

The world is kept intentionally small:
- one setting with a few navigable locations,
- one quest object that can be found only by following clues,
- one emotional turn where the hero chooses honesty over keeping the coin.

The seed words "even" and "sixpence" are built into the narrative vocabulary.
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.id in {"Ava", "Milo", "Nia", "Jonah"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case] if self.id in {"Ava", "Nia"} else {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    ship: str = "the Star Lantern"
    room_names: list[str] = field(default_factory=lambda: [
        "the bridge", "the galley", "the observation deck", "the cargo nook"
    ])


@dataclass
class Quest:
    title: str
    clue1: str
    clue2: str
    twist: str
    moral_value: str
    object_label: str = "sixpence"


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    place: str
    quest: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(),
}

QUESTS = {
    "lost_sixpence": Quest(
        title="the lost sixpence",
        clue1="a silver glint in the air vent",
        clue2="a tiny clink behind the galley warmer",
        twist="the missing coin had rolled into the robot's cup holder",
        moral_value="honesty matters more than keeping a shiny thing",
    ),
}

NAMES = {
    "girl": ["Ava", "Nia", "Mira", "Zoe", "Luna"],
    "boy": ["Milo", "Jonah", "Theo", "Finn", "Ezra"],
}

COMPANIONS = ["robot", "cat", "co-pilot", "astronaut"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
quest(Q) :- quest_key(Q).
coin(sixpence).
value(honesty).
even_word(even).

compatible(Q) :- quest(Q), coin(sixpence), value(honesty).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("quest_key", "lost_sixpence"),
        asp.fact("coin", "sixpence"),
        asp.fact("value", "honesty"),
        asp.fact("word", "even"),
    ]
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/1."))
    return sorted(set(asp.atoms(model, "compatible")))

def asp_verify() -> int:
    py = {("lost_sixpence",)}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP parity matches Python gate (1 quest).")
        return 0
    print("MISMATCH between Python and ASP.")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------

def valid_quests() -> list[str]:
    return ["lost_sixpence"]

def explain_rejection() -> str:
    return "(No story: this world only supports a simple space quest for a lost sixpence.)"

# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = SETTINGS["ship"]
    quest = QUESTS[params.quest]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", label=params.name))
    companion = world.add(Entity(id="Companion", kind="character", label=params.companion))
    coin = world.add(Entity(
        id="sixpence",
        kind="thing",
        label="sixpence",
        phrase="a small silver sixpence",
        owner=hero.id,
        location=params.place,
    ))
    world.facts.update(hero=hero, companion=companion, coin=coin, quest=quest)
    return world

def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    coin: Entity = f["coin"]
    quest: Quest = f["quest"]

    world.say(
        f"On the ship {world.setting.ship}, {hero.id} liked to count the bright dials and say "
        f"that space felt even safer when {hero.pronoun('possessive')} pocket held a sixpence."
    )
    world.say(
        f"But one night the sixpence was gone, and {hero.id} and {companion.label} began a quiet quest "
        f"from {world.setting.room_names[0]} to {world.setting.room_names[-1]}."
    )

    world.para()
    world.say(
        f"They found {quest.clue1} near the air vent, then {quest.clue2} by the galley. "
        f"Each clue made the search feel like a real space adventure."
    )
    world.say(
        f"At last they heard a little clink. The twist was simple: {quest.twist}."
    )

    world.para()
    world.say(
        f"{hero.id} picked up the coin, then noticed a crew badge beside it. "
        f"{hero.id} could have kept the shiny prize, but {quest.moral_value} mattered more."
    )
    world.say(
        f"So {hero.id} returned the sixpence, and the badge, too. {companion.label} smiled, "
        f"and the ship felt calmer than before."
    )

    coin.location = "returned"
    hero.memes["honest"] = 1.0
    hero.memes["pride"] = 1.0
    world.facts["resolved"] = True
    world.facts["twist"] = quest.twist
    world.facts["moral_value"] = quest.moral_value

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest: Quest = f["quest"]
    return [
        'Write a short space adventure for a child about a lost sixpence and a kind choice.',
        f"Tell a story where {hero.id} goes on a quest for a sixpence aboard a starship and learns that {quest.moral_value}.",
        'Write a simple adventure story that includes the words "even" and "sixpence" and ends with an honest choice.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    quest: Quest = f["quest"]
    return [
        QAItem(
            question=f"What was {hero.id} looking for on the ship?",
            answer="They were looking for a sixpence that had gone missing during the night.",
        ),
        QAItem(
            question="What did the clues lead them to?",
            answer=f"The clues led them through the ship until they found that {quest.twist}.",
        ),
        QAItem(
            question="What choice did the hero make at the end?",
            answer="The hero chose to return the sixpence instead of keeping it.",
        ),
        QAItem(
            question="What did the story say mattered more than the shiny coin?",
            answer=f"It said that {quest.moral_value} mattered more than keeping the coin.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sixpence?",
            answer="A sixpence was a small old coin people once used in Britain.",
        ),
        QAItem(
            question="What does a quest mean?",
            answer="A quest is a search for something important, often with clues and challenges.",
        ),
        QAItem(
            question="What does even mean?",
            answer="Even can mean smooth, level, or fair, like things being balanced.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story turn in a new direction.",
        ),
        QAItem(
            question="What is moral value in a story?",
            answer="A moral value is a lesson about how to act kindly, honestly, or fairly.",
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------

def valid_names(gender: str) -> list[str]:
    return NAMES[gender]

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.quest not in valid_quests():
        raise StoryError(explain_rejection())
    quest = args.quest or rng.choice(valid_quests())
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(valid_names(gender))
    companion = args.companion or rng.choice(COMPANIONS)
    place = args.place or "ship"
    return StoryParams(
        name=name,
        gender=gender,
        companion=companion,
        place=place,
        quest=quest,
    )

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(name="Ava", gender="girl", companion="robot", place="ship", quest="lost_sixpence"),
    StoryParams(name="Milo", gender="boy", companion="cat", place="ship", quest="lost_sixpence"),
    StoryParams(name="Nia", gender="girl", companion="co-pilot", place="ship", quest="lost_sixpence"),
]

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with a sixpence quest, a twist, and a moral value.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--place", choices=["ship"], default="ship")
    ap.add_argument("--quest", choices=list(QUESTS))
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

def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_text("#show compatible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program_text("#show compatible/1."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 20):
            attempts += 1
            try:
                params = resolve_params(args, random.Random(rng.randrange(2**31)))
            except StoryError as err:
                print(err)
                return
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
