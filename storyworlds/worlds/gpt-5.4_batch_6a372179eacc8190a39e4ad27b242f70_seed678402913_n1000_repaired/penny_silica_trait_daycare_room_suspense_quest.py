#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py
=============================================================================

A standalone story world for a tiny myth-flavored daycare-room quest:

A child in a daycare room is using a sensory table filled with silica sand when
a shiny penny -- the "sun coin" of their pretend quest -- disappears. The room
briefly feels enchanted: a hiss, shadow, or rattle makes the search suspenseful.
The child must use a sensible tool to recover the penny, and the ending depends
on whether their trait lets them keep steady or whether they wisely ask the
teacher for help.

The world model is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate for search tools
- a state-driven screenplay with premise, suspense, turn, and resolution
- grounded QA generated from the simulated state
- an inline ASP twin for the compatibility gate and outcome model

Run it
------
    python storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py
    python storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py --tool magnet
    python storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py --all
    python storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py --qa --json
    python storyworlds/worlds/gpt-5.4/penny_silica_trait_daycare_room_suspense_quest.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# Make the shared result containers importable when this script is run directly:
# this file lives under storyworlds/worlds/gpt-5.4/, so add storyworlds/ itself.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_female"}
        male = {"boy", "father", "man", "teacher_male"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher_female": "teacher", "teacher_male": "teacher"}.get(self.type, self.type)


@dataclass
class Guardian:
    id: str
    title: str
    mural: str
    promise: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingSpot:
    id: str
    label: str
    sentence: str
    need: str
    difficulty: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspense:
    id: str
    omen: str
    truth: str
    rank: int
    tags: set[str] = field(default_factory=set)


@dataclass
class TraitCfg:
    id: str
    label: str
    line: str
    calm: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


GUARDIANS = {
    "lion": Guardian(
        id="lion",
        title="Lion of Morning",
        mural="a paper lion with a mane of yellow streamers",
        promise="the lion watched brave beginnings",
        ending="the paper lion seemed to smile over the cubbies",
        tags={"lion", "myth"},
    ),
    "owl": Guardian(
        id="owl",
        title="Owl of Quiet Eyes",
        mural="a painted owl with wide silver circles for eyes",
        promise="the owl guarded careful seekers",
        ending="the owl looked wise and peaceful above the bookshelf",
        tags={"owl", "myth"},
    ),
    "turtle": Guardian(
        id="turtle",
        title="Turtle of the Slow Light",
        mural="a green turtle painted on the art shelf",
        promise="the turtle loved steady hearts",
        ending="the turtle seemed to carry calm right across the room",
        tags={"turtle", "myth"},
    ),
}

HIDING_SPOTS = {
    "buried": HidingSpot(
        id="buried",
        label="buried in the silica sand",
        sentence="The penny slipped from small fingers and vanished into the pale silica sand like a sun falling into a tiny desert.",
        need="sifting",
        difficulty=1,
        tags={"silica", "sand"},
    ),
    "under_cup": HidingSpot(
        id="under_cup",
        label="under a little cup in the silica sand",
        sentence="The penny flashed once, then slid under a little upside-down cup half-buried in the silica sand.",
        need="lifting",
        difficulty=1,
        tags={"silica", "sand"},
    ),
    "tray_groove": HidingSpot(
        id="tray_groove",
        label="in the tray groove under silica dust",
        sentence="The penny skated to the tray edge and hid in a narrow groove under a whisper of silica dust.",
        need="brushing",
        difficulty=2,
        tags={"silica", "sand"},
    ),
}

TOOLS = {
    "sieve": Tool(
        id="sieve",
        label="sieve",
        phrase="a little blue sieve",
        works_for={"buried", "under_cup"},
        tags={"sieve", "tool"},
    ),
    "scoop": Tool(
        id="scoop",
        label="scoop",
        phrase="a small red scoop",
        works_for={"buried", "under_cup"},
        tags={"scoop", "tool"},
    ),
    "brush": Tool(
        id="brush",
        label="brush",
        phrase="a soft table brush",
        works_for={"tray_groove"},
        tags={"brush", "tool"},
    ),
    "magnet": Tool(
        id="magnet",
        label="magnet wand",
        phrase="a magnet wand",
        works_for=set(),
        tags={"magnet", "tool"},
    ),
}

SUSPENSES = {
    "vent_hiss": Suspense(
        id="vent_hiss",
        omen="From the vent came a long hush-hiss that made the daycare room sound like it had a sleeping serpent somewhere in the walls.",
        truth="It was only the warm air turning on through the vent.",
        rank=2,
        tags={"vent", "suspense"},
    ),
    "coat_shadow": Suspense(
        id="coat_shadow",
        omen="A hanging raincoat swayed by the door, and its shadow stretched tall across the floor like a silent giant.",
        truth="It was only a raincoat moving when the door settled.",
        rank=1,
        tags={"shadow", "suspense"},
    ),
    "block_rattle": Suspense(
        id="block_rattle",
        omen="A block on the shelf rolled and clicked, and the sound was small but sudden, like a hidden creature tapping once in the dark.",
        truth="It was only one loose block shifting on the shelf.",
        rank=1,
        tags={"blocks", "suspense"},
    ),
}

TRAITS = {
    "brave": TraitCfg(
        id="brave",
        label="brave",
        line="Bravery was the trait that kept the child's breathing slow and steady.",
        calm=2,
        tags={"trait", "brave"},
    ),
    "patient": TraitCfg(
        id="patient",
        label="patient",
        line="Patience was the trait that kept small hands from digging too fast.",
        calm=1,
        tags={"trait", "patient"},
    ),
    "observant": TraitCfg(
        id="observant",
        label="observant",
        line="An observant trait helped the child notice tiny clues instead of panicking.",
        calm=1,
        tags={"trait", "observant"},
    ),
    "gentle": TraitCfg(
        id="gentle",
        label="gentle",
        line="A gentle trait made the child careful with the sand and with the truth of the room.",
        calm=1,
        tags={"trait", "gentle"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Zoe", "Ivy", "Anna", "Lucy"]
BOY_NAMES = ["Theo", "Milo", "Ben", "Leo", "Eli", "Noah", "Sam", "Finn"]


def tool_fits(tool: Tool, hiding: HidingSpot) -> bool:
    return hiding.id in tool.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for guardian_id in GUARDIANS:
        for hiding_id, hiding in HIDING_SPOTS.items():
            for tool_id, tool in TOOLS.items():
                if not tool_fits(tool, hiding):
                    continue
                for suspense_id in SUSPENSES:
                    combos.append((guardian_id, hiding_id, tool_id, suspense_id))
    return combos


def outcome_for(trait_id: str, suspense_id: str) -> str:
    trait = TRAITS[trait_id]
    suspense = SUSPENSES[suspense_id]
    return "self_found" if trait.calm >= suspense.rank else "guided"


@dataclass
class StoryParams:
    guardian: str
    hiding_spot: str
    tool: str
    suspense: str
    trait: str
    name: str
    gender: str
    teacher: str
    seed: Optional[int] = None


def explain_tool(tool: Tool, hiding: HidingSpot) -> str:
    if tool.id == "magnet":
        return (
            "(No story: a magnet wand is not a sensible way to find a penny here. "
            "A penny is not reliably picked up by a classroom magnet, so choose a "
            "tool that can really search silica sand, like a sieve, scoop, or brush.)"
        )
    return (
        f"(No story: {tool.phrase} does not fit a penny hidden {hiding.label}. "
        f"This quest only works when the search tool matches the hiding place.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a myth-flavored daycare room quest for a lost penny in silica sand."
    )
    ap.add_argument("--guardian", choices=GUARDIANS)
    ap.add_argument("--hiding-spot", choices=HIDING_SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--suspense", choices=SUSPENSES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["teacher_female", "teacher_male"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and args.hiding_spot:
        tool = TOOLS[args.tool]
        hiding = HIDING_SPOTS[args.hiding_spot]
        if not tool_fits(tool, hiding):
            raise StoryError(explain_tool(tool, hiding))

    combos = [
        c for c in valid_combos()
        if (args.guardian is None or c[0] == args.guardian)
        and (args.hiding_spot is None or c[1] == args.hiding_spot)
        and (args.tool is None or c[2] == args.tool)
        and (args.suspense is None or c[3] == args.suspense)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    guardian_id, hiding_id, tool_id, suspense_id = rng.choice(sorted(combos))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    teacher = args.teacher or rng.choice(["teacher_female", "teacher_male"])
    return StoryParams(
        guardian=guardian_id,
        hiding_spot=hiding_id,
        tool=tool_id,
        suspense=suspense_id,
        trait=trait_id,
        name=name,
        gender=gender,
        teacher=teacher,
    )


def tell(
    guardian: Guardian,
    hiding: HidingSpot,
    tool: Tool,
    suspense: Suspense,
    trait_cfg: TraitCfg,
    name: str,
    gender: str,
    teacher_type: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        traits=[trait_cfg.label],
        tags={"child"},
    ))
    teacher = world.add(Entity(
        id="Teacher",
        kind="character",
        type=teacher_type,
        label="the teacher",
        tags={"teacher"},
    ))
    penny = world.add(Entity(
        id="penny",
        kind="thing",
        type="coin",
        label="penny",
        phrase="a bright penny",
        tags={"penny", "coin"},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="daycare room",
        phrase="the daycare room",
        tags={"daycare"},
    ))

    child.memes["wonder"] += 1
    child.memes["quest"] += 1
    room.meters["silica_sand"] += 1

    world.say(
        f"In the daycare room, the cubbies stood like little cliffs and the art shelf held {guardian.mural}. "
        f"To {name}, it looked less like an ordinary room and more like a hall from an old myth, where {guardian.promise}."
    )
    world.say(
        f"That morning {name} was carrying a penny for the class game and calling it the Sun Coin. "
        f"The sensory table was full of pale silica sand, soft and sparkling as if a tiny desert had been poured indoors."
    )

    world.para()
    world.say(hiding.sentence)
    penny.meters["lost"] += 1
    child.memes["alarm"] += 1
    world.say(
        f'"The quest is not over," {name} whispered, because the Sun Coin was meant for the {guardian.title}.'
    )
    world.say(trait_cfg.line)

    world.para()
    world.say(suspense.omen)
    child.memes["fear"] += float(suspense.rank)
    if outcome_for(trait_cfg.id, suspense.id) == "self_found":
        child.memes["steady"] += 1
        world.say(
            f"{name} froze for one heartbeat, then listened again. "
            f"{trait_cfg.label.capitalize()} thoughts settled the scary feeling into a smaller shape."
        )
        world.say(
            f"With {tool.phrase}, {name} searched slowly through the silica sand."
        )
        if hiding.id == "buried":
            world.say("Grain by grain, the sand slipped away until one warm copper flash shone through.")
        elif hiding.id == "under_cup":
            world.say("The little cup lifted, and beneath it lay the round edge of the penny, waiting like a secret sun.")
        else:
            world.say("A soft sweep cleared the dusty groove, and the penny blinked there at the tray edge.")
        penny.meters["found"] += 1
        penny.meters["lost"] = 0.0
        child.memes["joy"] += 1
        child.memes["fear"] = 0.0
        world.say(
            f"Then {name} understood the sound at last. {suspense.truth} "
            f"The spell of fear broke, and the daycare room became a daycare room again."
        )
        outcome = "self_found"
    else:
        child.memes["seeks_help"] += 1
        world.say(
            f"{name} held very still and did not dig wildly. "
            f'Instead, {child.pronoun()} called, "{teacher.label_word.capitalize()}, will you come on the quest with me?"'
        )
        teacher.memes["helpfulness"] += 1
        world.say(
            f"{teacher.label_word.capitalize()} came softly and knelt beside the table. "
            f'"Let us look with true eyes," {teacher.pronoun()} said.'
        )
        world.say(
            f"Together they listened. {suspense.truth} "
            f"The frightening mystery shrank at once."
        )
        world.say(
            f"Then {teacher.label_word} passed {name} {tool.phrase}, and together they searched the silica sand."
        )
        if hiding.id == "buried":
            world.say("They sifted and tapped until the penny rang a tiny copper note against the plastic rim.")
        elif hiding.id == "under_cup":
            world.say("They lifted the little cup, and the penny shone underneath it like a hidden morning.")
        else:
            world.say("A gentle brush along the tray edge uncovered the penny from its dusty groove.")
        penny.meters["found"] += 1
        penny.meters["lost"] = 0.0
        child.memes["joy"] += 1
        child.memes["fear"] = 0.0
        child.memes["trust"] += 1
        outcome = "guided"

    world.para()
    world.say(
        f"{name} set the penny before the {guardian.title}, and for a moment the shiny coin made a little sun in the room."
    )
    if outcome == "self_found":
        world.say(
            f'{teacher.label_word.capitalize()} smiled from across the table. "You used your {trait_cfg.label} trait well," '
            f"{teacher.pronoun()} said."
        )
    else:
        world.say(
            f'"That is a good trait too," {teacher.label_word} said. '
            f'"A brave quest can include asking for help when a room feels strange."'
        )
    world.say(
        f"{guardian.ending}, and even the silica sand looked less like a desert of danger and more like a place where careful hands could find lost light."
    )

    world.facts.update(
        child=child,
        teacher=teacher,
        penny=penny,
        room=room,
        guardian=guardian,
        hiding=hiding,
        tool=tool,
        suspense=suspense,
        trait=trait_cfg,
        outcome=outcome,
        asked_for_help=child.memes["seeks_help"] >= THRESHOLD,
        found_penny=penny.meters["found"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    suspense = f["suspense"]
    trait_cfg = f["trait"]
    return [
        'Write a short myth-like story for a 3-to-5-year-old set in a daycare room that includes the words "penny", "silica", and "trait".',
        f"Tell a suspenseful quest where a child named {child.id} loses a penny in silica sand and thinks the daycare room has become the hall of the {guardian.title}.",
        f"Write a gentle story where a child's {trait_cfg.label} trait helps solve a scary moment after {suspense.omen.lower()}",
    ]


KNOWLEDGE = {
    "penny": [
        (
            "What is a penny?",
            "A penny is a small coin made to be used as money. It is round, copper-colored, and easy to lose because it is so little."
        )
    ],
    "silica": [
        (
            "What is silica sand?",
            "Silica sand is a fine kind of sand made from tiny bits of mineral. In a sensory table it feels soft and pourable, so children can scoop and sift it."
        )
    ],
    "trait": [
        (
            "What is a trait?",
            "A trait is a part of how someone usually acts, like being brave, patient, or gentle. A good trait can help you make wise choices."
        )
    ],
    "sieve": [
        (
            "What does a sieve do?",
            "A sieve lets fine sand fall through while larger things stay behind. That makes it useful for finding a small object hiding in sand."
        )
    ],
    "scoop": [
        (
            "What is a scoop for?",
            "A scoop helps you lift and move sand or small loose things. It is good when you want to search gently instead of grabbing with your hands."
        )
    ],
    "brush": [
        (
            "What does a soft brush do?",
            "A soft brush sweeps away light dust or grains without poking hard. That makes it helpful for clearing a narrow crack or edge."
        )
    ],
    "vent": [
        (
            "Why does a vent hiss?",
            "A vent can hiss when air starts blowing through it. The sound may feel mysterious at first, but it is just air moving."
        )
    ],
    "shadow": [
        (
            "Why can a shadow look scary?",
            "A shadow can look strange when it stretches across a room. If you look again in good light, you can often see what made it."
        )
    ],
    "blocks": [
        (
            "Why might a block rattle on a shelf?",
            "A loose block can roll or tap when something nearby moves. A sudden little sound can seem spooky until you find the simple cause."
        )
    ],
    "help": [
        (
            "When should a child ask a grown-up for help?",
            "A child should ask a grown-up for help when something feels confusing, scary, or hard to do safely. Asking for help is a smart and brave choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["penny", "silica", "trait", "sieve", "scoop", "brush", "vent", "shadow", "blocks", "help"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    teacher = f["teacher"]
    guardian = f["guardian"]
    hiding = f["hiding"]
    tool = f["tool"]
    suspense = f["suspense"]
    trait_cfg = f["trait"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in a daycare room, and the teacher who helps keep the room calm and true. "
            f"The quest centers on a lost penny that {child.id} calls the Sun Coin."
        ),
        (
            "What was the quest?",
            f"The quest was to find the lost penny and place it before the {guardian.title}. "
            f"In {child.id}'s imagination, that made the daycare room feel like a myth hall instead of an ordinary classroom."
        ),
        (
            "Where did the penny go?",
            f"The penny was lost {hiding.label}. "
            f"That mattered because the hiding place decided what kind of search tool could really work."
        ),
        (
            "Why did the room feel suspenseful?",
            f"The room felt suspenseful because {suspense.omen.lower()} "
            f"At first the sound or shadow seemed magical, but later everyone learned the simple truth."
        ),
        (
            f"What trait helped {child.id}?",
            f"{trait_cfg.label.capitalize()} was the trait that shaped the quest. "
            f"It kept {child.id} from grabbing wildly, so the search stayed thoughtful instead of turning into a bigger mess."
        ),
    ]
    if outcome == "self_found":
        qa.append((
            f"How did {child.id} solve the problem?",
            f"{child.id} stayed steady and used {tool.phrase} to search the silica sand. "
            f"That careful method matched where the penny was hidden, so the coin could be found without panic."
        ))
        qa.append((
            "Did the child need help from the teacher?",
            f"No, not to finish the search. {child.id} understood that {suspense.truth.lower()} and then found the penny alone with the right tool."
        ))
    else:
        qa.append((
            f"Why did {child.id} call the teacher?",
            f"{child.id} called the teacher because the strange sound or shadow felt too big for the moment. "
            f"Asking for help let the scary feeling shrink after the teacher explained that {suspense.truth.lower()}."
        ))
        qa.append((
            f"How was the penny finally found?",
            f"{child.id} and the teacher searched together with {tool.phrase}. "
            f"The right tool matched the hiding place, and the calm help made the quest feel safe again."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the penny shining before the {guardian.title}. "
        f"That final image shows the change: the daycare room no longer felt haunted or strange, only bright and peaceful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"penny", "silica", "trait", "help"}
    tags |= set(f["tool"].tags)
    tags |= set(f["suspense"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(Tool, Spot) :- tool(Tool), hiding_spot(Spot), works_for(Tool, Spot).
valid(G, Spot, Tool, Susp) :- guardian(G), hiding_spot(Spot), tool(Tool), suspense(Susp), fits(Tool, Spot).

self_found :- chosen_trait(T), chosen_suspense(S), calm(T, C), rank(S, R), C >= R.
guided :- chosen_trait(T), chosen_suspense(S), calm(T, C), rank(S, R), C < R.

outcome(self_found) :- self_found.
outcome(guided) :- guided.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for guardian_id in GUARDIANS:
        lines.append(asp.fact("guardian", guardian_id))
    for hiding_id in HIDING_SPOTS:
        lines.append(asp.fact("hiding_spot", hiding_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for hiding_id in sorted(tool.works_for):
            lines.append(asp.fact("works_for", tool_id, hiding_id))
    for suspense_id, suspense in SUSPENSES.items():
        lines.append(asp.fact("suspense", suspense_id))
        lines.append(asp.fact("rank", suspense_id, suspense.rank))
    for trait_id, trait_cfg in TRAITS.items():
        lines.append(asp.fact("trait", trait_id))
        lines.append(asp.fact("calm", trait_id, trait_cfg.calm))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_suspense", params.suspense),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"FAILED: resolve_params crashed for seed {seed}.")
            break

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_for(p.trait, p.suspense):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test story rendered empty output")
        emit(smoke, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"FAILED: generate/emit smoke test crashed: {err}")
    return rc


CURATED = [
    StoryParams(
        guardian="lion",
        hiding_spot="buried",
        tool="sieve",
        suspense="vent_hiss",
        trait="brave",
        name="Lina",
        gender="girl",
        teacher="teacher_female",
    ),
    StoryParams(
        guardian="owl",
        hiding_spot="tray_groove",
        tool="brush",
        suspense="coat_shadow",
        trait="patient",
        name="Theo",
        gender="boy",
        teacher="teacher_male",
    ),
    StoryParams(
        guardian="turtle",
        hiding_spot="under_cup",
        tool="scoop",
        suspense="block_rattle",
        trait="gentle",
        name="Maya",
        gender="girl",
        teacher="teacher_female",
    ),
    StoryParams(
        guardian="lion",
        hiding_spot="tray_groove",
        tool="brush",
        suspense="vent_hiss",
        trait="observant",
        name="Eli",
        gender="boy",
        teacher="teacher_male",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.guardian not in GUARDIANS:
        raise StoryError(f"(Invalid guardian: {params.guardian})")
    if params.hiding_spot not in HIDING_SPOTS:
        raise StoryError(f"(Invalid hiding spot: {params.hiding_spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.suspense not in SUSPENSES:
        raise StoryError(f"(Invalid suspense: {params.suspense})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid gender: {params.gender})")
    if params.teacher not in {"teacher_female", "teacher_male"}:
        raise StoryError(f"(Invalid teacher: {params.teacher})")

    hiding = HIDING_SPOTS[params.hiding_spot]
    tool = TOOLS[params.tool]
    if not tool_fits(tool, hiding):
        raise StoryError(explain_tool(tool, hiding))

    world = tell(
        guardian=GUARDIANS[params.guardian],
        hiding=hiding,
        tool=tool,
        suspense=SUSPENSES[params.suspense],
        trait_cfg=TRAITS[params.trait],
        name=params.name,
        gender=params.gender,
        teacher_type=params.teacher,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (guardian, hiding_spot, tool, suspense) combos:\n")
        for guardian_id, hiding_id, tool_id, suspense_id in combos:
            print(f"  {guardian_id:7} {hiding_id:11} {tool_id:7} {suspense_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.guardian} / {p.hiding_spot} / {p.tool} / "
                f"{p.suspense} ({outcome_for(p.trait, p.suspense)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
