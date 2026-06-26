#!/usr/bin/env python3
"""
storyworlds/worlds/goose_galore_evidence_dialogue_quest_comedy.py
=================================================================

A small comedy story world about a goose on a quest for evidence, with lots of
silly dialogue and a satisfying little mystery.

Seed tale idea:
---
A bossy goose hears that a mystery happened at the pond. He waddles off on a
quest for evidence galore. He asks everyone a lot of questions, but keeps
finding only funny clues: a feather, a crumb trail, a tiny puddle, and a lost
button. In the end, the "mystery" turns out to be very small and very silly:
the goose himself was the one who scattered the snacks while stomping around.
He laughs, shares the snacks, and calls it a successful case.

This world turns that premise into a little stateful simulation:
- a goose detective tracks evidence from place to place
- dialogue updates trust, curiosity, and hilarity
- the quest resolves when enough evidence is gathered
- comedy comes from silly causal turns, not from a frozen paragraph
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
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"goose"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"child", "kid"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    clue_kinds: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    place_hint: str
    comedic_line: str
    reveals: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    name: str
    sidekick: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS: dict[str, Setting] = {
    "pond": Setting(place="the pond", clue_kinds={"feather", "crumb", "splash"}),
    "market": Setting(place="the market", clue_kinds={"crumb", "button", "track"}),
    "garden": Setting(place="the garden", clue_kinds={"feather", "leaf", "track"}),
    "library": Setting(place="the library", indoors=True, clue_kinds={"button", "paper", "ink"}),
}

CLUES: dict[str, Clue] = {
    "feather": Clue(
        id="feather",
        label="a feather",
        phrase="a fluffy white feather",
        kind="feather",
        place_hint="near the water",
        comedic_line="It tickled his beak every time he tried to look serious.",
        reveals="the goose had been flapping around earlier",
    ),
    "crumb": Clue(
        id="crumb",
        label="a crumb trail",
        phrase="a crumb trail leading in a circle",
        kind="crumb",
        place_hint="near the snack bench",
        comedic_line="The trail looked important, until it politely looped right back to the start.",
        reveals="someone was very excited about snacks",
    ),
    "button": Clue(
        id="button",
        label="a lost button",
        phrase="a shiny little button",
        kind="button",
        place_hint="under a chair",
        comedic_line="It was so tiny that even the goose gave it a tiny respectful stare.",
        reveals="someone had rushed off in a hurry",
    ),
    "track": Clue(
        id="track",
        label="muddy tracks",
        phrase="muddy tracks shaped like waddles",
        kind="track",
        place_hint="along the path",
        comedic_line="The tracks were so wiggly that they seemed to be giggling.",
        reveals="a very determined bird had marched through here",
    ),
}

NAMES = ["Gus", "Mabel", "Sunny", "Pip", "Milo", "Dora"]
SIDEKICKS = ["a mouse", "a duckling", "a kid", "a turtle", "a squirrel"]
TRAITS = ["serious", "brave", "curious", "fussy", "jumpy", "polite"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def clue_is_plausible(setting: Setting, clue: Clue) -> bool:
    return clue.kind in setting.clue_kinds


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        for cname, clue in CLUES.items():
            if clue_is_plausible(setting, clue):
                combos.append((sname, cname))
    return combos


def explain_rejection(setting: Setting, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} would not plausibly show up at {setting.place}. "
        f"Pick a clue that matches that place.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def describe_goose(goose: Entity) -> str:
    trait = next((t for t in goose.traits if t != "little"), "curious")
    return f"a little {trait} goose named {goose.id}"


def comedy_beat(clue: Clue) -> str:
    return clue.comedic_line


def make_entity_state() -> Entity:
    return Entity(
        id="goose",
        kind="character",
        type="goose",
        label="goose",
        traits=["little", "curious", "dramatic"],
        meters={"evidence": 0.0, "hunger": 1.0},
        memes={"curiosity": 1.0, "hilarity": 0.0, "confidence": 0.0, "suspicion": 0.0, "joy": 0.0},
    )


def make_sidekick(name: str) -> Entity:
    return Entity(
        id="sidekick",
        kind="character",
        type="kid",
        label=name,
        traits=["helpful", "bouncy"],
        meters={},
        memes={"confidence": 0.0, "joy": 0.0},
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def start_story(world: World, goose: Entity, sidekick: Entity, clue: Clue) -> None:
    world.say(
        f"{goose.id} was {describe_goose(goose)} who loved a good mystery."
    )
    world.say(
        f"At {world.setting.place}, {goose.pronoun('subject')} said, "
        f"\"I want evidence galore!\""
    )
    world.say(
        f"{sidekick.id} waved and said, \"I can help!\" "
        f"{goose.id} nodded very grandly, as if the quest had music."
    )
    world.facts["clue"] = clue
    world.facts["goose"] = goose
    world.facts["sidekick"] = sidekick


def begin_quest(world: World, goose: Entity, clue: Clue) -> None:
    goose.memes["curiosity"] += 1
    goose.memes["confidence"] += 0.5
    world.say(
        f"{goose.id} set off on a quest for {clue.label}, strutting down the path "
        f"with his chin in the air."
    )
    world.say(f"{clue.comedic_line}")


def ask_dialogue(world: World, goose: Entity, sidekick: Entity, clue: Clue) -> None:
    goose.memes["suspicion"] += 1
    world.say(
        f"\"Did you see the evidence?\" {goose.id} asked."
        f" \"Only if evidence can hide in plain sight,\" said {sidekick.id}."
    )
    world.say(
        f"\"That is not a yes,\" {goose.id} said, squinting at {clue.place_hint}."
    )


def find_clue(world: World, goose: Entity, clue: Clue) -> None:
    goose.meters["evidence"] += 1
    goose.memes["hilarity"] += 1
    world.say(
        f"Then {goose.id} found {clue.phrase} {clue.place_hint}."
    )
    world.say(
        f"\"Aha!\" he said. \"This is clearly important.\" {clue.reveals.capitalize()}."
    )


def reveal_truth(world: World, goose: Entity, sidekick: Entity, clue: Clue) -> None:
    goose.memes["suspicion"] += 1
    goose.memes["joy"] += 1
    world.say(
        f"{sidekick.id} looked at the clues and said, \"Maybe the mystery is just a silly goose problem.\""
    )
    world.say(
        f"{goose.id} blinked, then looked at his own muddy feet and said, "
        f"\"Oh no. I was the clue all along.\""
    )
    world.say(
        f"That was when the whole case made sense: the {clue.label} matched the mess {goose.id} had made while waddling in circles."
    )


def resolution(world: World, goose: Entity, sidekick: Entity) -> None:
    goose.memes["confidence"] += 1
    goose.memes["suspicion"] = 0.0
    world.say(
        f"{goose.id} laughed so hard that his feathers shook."
    )
    world.say(
        f"\"Quest complete,\" he said. \"Next time I will carry a snack bag instead of acting like a detective tornado.\""
    )
    world.say(
        f"{sidekick.id} grinned, and together they shared the snacks galore."
    )


def tell(setting: Setting, clue: Clue, name: str = "Gus", sidekick_name: str = "Pip") -> World:
    world = World(setting)
    goose = world.add(Entity(
        id=name,
        kind="character",
        type="goose",
        label="goose",
        traits=["little", "curious", "dramatic"],
        meters={"evidence": 0.0, "hunger": 1.0},
        memes={"curiosity": 1.0, "hilarity": 0.0, "confidence": 0.0, "suspicion": 0.0, "joy": 0.0},
    ))
    sidekick = world.add(make_sidekick(sidekick_name))

    start_story(world, goose, sidekick, clue)
    world.para()
    begin_quest(world, goose, clue)
    ask_dialogue(world, goose, sidekick, clue)
    world.para()
    find_clue(world, goose, clue)
    reveal_truth(world, goose, sidekick, clue)
    world.para()
    resolution(world, goose, sidekick)

    world.facts.update(setting=setting, clue=clue)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_place(pond).
setting_place(market).
setting_place(garden).
setting_place(library).

clue_kind(feather).
clue_kind(crumb).
clue_kind(button).
clue_kind(track).

place_allows(pond, feather) :- true.
place_allows(pond, crumb) :- true.
place_allows(pond, track) :- true.
place_allows(market, crumb) :- true.
place_allows(market, button) :- true.
place_allows(market, track) :- true.
place_allows(garden, feather) :- true.
place_allows(garden, track) :- true.
place_allows(garden, crumb) :- false.
place_allows(library, button) :- true.
place_allows(library, paper) :- true.

valid(Place, Clue) :- setting_place(Place), clue_kind(Clue), place_allows(Place, Clue).

#show valid/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sname, setting in SETTINGS.items():
        lines.append(asp.fact("setting_place", sname))
    for cname, clue in CLUES.items():
        lines.append(asp.fact("clue_kind", cname))
    for sname, setting in SETTINGS.items():
        for cname, clue in CLUES.items():
            if clue_is_plausible(setting, clue):
                lines.append(asp.fact("place_allows", sname, cname))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story about a goose named {f["goose"].id} who goes on a quest for evidence galore at {world.setting.place}.',
        f'Tell a child-friendly comedy with dialogue where {f["goose"].id} asks questions and finds {f["clue"].label}.',
        f'Write a short quest story set at {world.setting.place} about a goose, a clue, and a silly mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    goose: Entity = world.facts["goose"]
    sidekick: Entity = world.facts["sidekick"]
    clue: Clue = world.facts["clue"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who went on the quest for evidence at {place}?",
            answer=f"A little goose named {goose.id} went on the quest, and {sidekick.id} helped with the questions.",
        ),
        QAItem(
            question=f"What kind of clue did {goose.id} find?",
            answer=f"{goose.id} found {clue.phrase}, which was the clue that helped solve the silly mystery.",
        ),
        QAItem(
            question=f"Why did the mystery turn out to be funny?",
            answer=(
                f"It was funny because {goose.id} realized he had made the mess himself while waddling around, "
                f"so the big mystery was really just a silly goose mistake."
            ),
        ),
        QAItem(
            question=f"What did {goose.id} say when the quest was finished?",
            answer=(
                f"{goose.id} said the quest was complete and joked that next time he would carry a snack bag "
                f"instead of acting like a detective tornado."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue: Clue = world.facts["clue"]
    qa = [
        QAItem(
            question="What is evidence?",
            answer="Evidence is a clue or fact that helps explain what happened in a mystery.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to look for something important.",
        ),
        QAItem(
            question="Why do geese waddle?",
            answer="Geese waddle because their bodies are built a bit wide, so their walking looks bouncy and side-to-side.",
        ),
        QAItem(
            question="What does comedy mean in a story?",
            answer="Comedy means the story is meant to be funny and to make you smile or laugh.",
        ),
    ]
    if clue.kind == "crumb":
        qa.append(QAItem(
            question="What are crumbs?",
            answer="Crumbs are tiny pieces that break off food, like bread or crackers.",
        ))
    elif clue.kind == "button":
        qa.append(QAItem(
            question="What is a button?",
            answer="A button is a small round piece used to fasten clothes.",
        ))
    return qa


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
# CLI
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="pond", clue="feather", name="Gus", sidekick="Pip"),
    StoryParams(setting="market", clue="crumb", name="Mabel", sidekick="a mouse"),
    StoryParams(setting="garden", clue="track", name="Sunny", sidekick="a squirrel"),
    StoryParams(setting="library", clue="button", name="Dora", sidekick="a kid"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A comedy story world about a goose, evidence galore, dialogue, and a quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
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
    if args.setting and args.clue:
        if not clue_is_plausible(SETTINGS[args.setting], CLUES[args.clue]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], CLUES[args.clue]))
    combos = [
        (s, c) for s, c in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.clue is None or c == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid setting/clue combination matches the given options.)")
    setting, clue = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, clue=clue, name=name, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CLUES[params.clue], params.name, params.sidekick)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, clue) combos:\n")
        for setting, clue in combos:
            print(f"  {setting:8} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: quest at {p.setting} (clue: {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
