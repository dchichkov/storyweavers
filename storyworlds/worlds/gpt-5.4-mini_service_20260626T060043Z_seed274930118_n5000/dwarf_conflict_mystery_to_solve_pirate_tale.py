#!/usr/bin/env python3
"""
storyworlds/worlds/dwarf_conflict_mystery_to_solve_pirate_tale.py
==================================================================

A small story world in a pirate-tale style: a dwarf, a conflict, and a mystery
to solve.

The seed image:
---
A dwarf in a pirate camp notices that a vital item is gone. The captain gets
frustrated, the crew argues, and the dwarf follows clues through a ship, a dock,
or a cave. The truth turns out to be small, practical, and visible at the end:
the missing thing is found, the conflict eases, and the crew sails on with a
clearer plan.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dwarf", "man", "pirate", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    clue_style: str = ""


@dataclass
class Mystery:
    id: str
    missing: str
    clue1: str
    clue2: str
    found_in: str
    ending_image: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    dwarf_name: str
    captain_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.trace = list(self.trace)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the pirate ship", affords={"search", "argue", "sail"}, clue_style="deck"),
    "dock": Setting(place="the windy dock", affords={"search", "argue"}, clue_style="ropes"),
    "cave": Setting(place="the sea cave", affords={"search", "argue"}, clue_style="echoes"),
    "island": Setting(place="the small island", affords={"search", "argue", "sail"}, clue_style="sand"),
}

MYSTERIES = {
    "missing_map": Mystery(
        id="missing_map",
        missing="the captain's map",
        clue1="a wet trail on the deck",
        clue2="a strip of paper tucked under a barrel",
        found_in="the chart room",
        ending_image="the map lay flat again beside the lantern",
    ),
    "missing_key": Mystery(
        id="missing_key",
        missing="the brass key",
        clue1="a key-shaped mark in the sand",
        clue2="a glint by a rope coil",
        found_in="the skipper's pocket",
        ending_image="the brass key shone from the captain's hand",
    ),
    "missing_lantern": Mystery(
        id="missing_lantern",
        missing="the lantern",
        clue1="a warm smell of oil",
        clue2="a bright circle of light behind crates",
        found_in="the galley",
        ending_image="the lantern glowed steady at the mast",
    ),
    "missing_compass": Mystery(
        id="missing_compass",
        missing="the compass",
        clue1="a small scratch on the rail",
        clue2="a hum from inside a sea chest",
        found_in="the captain's coat",
        ending_image="the compass sat safe in the coat pocket",
    ),
}

DWARF_NAMES = ["Bran", "Rurik", "Nori", "Dorin", "Bram", "Kellan"]
CAPTAIN_NAMES = ["Captain Marlow", "Captain Sera", "Captain Flint", "Captain Vale"]
TRAITS = ["bright-eyed", "sturdy", "quick", "kind", "clever"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _m(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    e = world.get(eid)
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _em(world: World, eid: str, key: str, amt: float = 1.0) -> None:
    e = world.get(eid)
    e.memes[key] = e.memes.get(key, 0.0) + amt


def _textual_place(setting: Setting) -> str:
    return setting.place


def _dwarf_intro(world: World, dwarf: Entity) -> None:
    trait = dwarf.traits[0] if dwarf.traits else "small"
    world.say(f"{dwarf.id} was a {trait} dwarf who liked finding tidy answers in messy places.")


def _setup(world: World, dwarf: Entity, captain: Entity, mystery: Mystery) -> None:
    world.say(
        f"On {world.setting.place}, {dwarf.id} served with {captain.id} and the crew, "
        f"and everyone depended on {mystery.missing}."
    )
    _em(world, dwarf.id, "care", 1)
    _em(world, captain.id, "duty", 1)


def _discover_missing(world: World, dwarf: Entity, captain: Entity, mystery: Mystery) -> None:
    _em(world, captain.id, "worry", 1)
    _em(world, dwarf.id, "curiosity", 1)
    _em(world, captain.id, "conflict", 1)
    world.say(
        f"One day, the crew looked high and low, but {mystery.missing} was gone."
    )
    world.say(
        f'"Where is it?" {captain.id} snapped, and the deck grew tense.'
    )
    world.say(
        f"{dwarf.id} did not like the sharp words, but {dwarf.pronoun('subject')} knew a mystery could be solved by calm eyes."
    )


def _follow_clues(world: World, dwarf: Entity, mystery: Mystery) -> None:
    _m(world, dwarf.id, "search", 1)
    _em(world, dwarf.id, "focus", 1)
    world.say(
        f"{dwarf.id} crouched low and studied {mystery.clue1}."
    )
    world.say(
        f"Then {dwarf.pronoun('subject')} found {mystery.clue2}, which pointed the crew toward {mystery.found_in}."
    )


def _reveal(world: World, dwarf: Entity, captain: Entity, mystery: Mystery) -> None:
    _m(world, captain.id, "relief", 1)
    _em(world, captain.id, "shame", 1)
    captain.memes["conflict"] = 0.0
    world.say(
        f"At last, the truth came clear: {mystery.missing} was in {mystery.found_in}."
    )
    world.say(
        f"{captain.id} blinked, then laughed softly. 'Aye, I put it there and forgot,' {captain.pronoun('subject')} said."
    )
    world.say(
        f"{dwarf.id} smiled, and the crew's grumble faded like foam behind the ship."
    )
    world.say(f"By evening, {mystery.ending_image}.")


def tell(setting: Setting, mystery: Mystery, dwarf_name: str, captain_name: str) -> World:
    world = World(setting)
    dwarf = world.add(Entity(id=dwarf_name, kind="character", type="dwarf", traits=["clever", "little"]))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain", traits=["stern", "sailor"]))
    item = world.add(Entity(id="missing_item", type="thing", label=mystery.missing, owner=captain.id))

    world.facts.update(dwarf=dwarf, captain=captain, item=item, mystery=mystery)

    _dwarf_intro(world, dwarf)
    _setup(world, dwarf, captain, mystery)
    world.para()
    _discover_missing(world, dwarf, captain, mystery)
    world.para()
    _follow_clues(world, dwarf, mystery)
    _reveal(world, dwarf, captain, mystery)

    world.facts["resolved"] = True
    world.facts["conflict"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate-tale story for a child about a dwarf solving a mystery on {world.setting.place}.',
        f"Tell a gentle story where {f['dwarf'].id} notices that {f['mystery'].missing} is gone and helps calm a conflict.",
        f"Write a simple story about a dwarf, an argument, and clues that lead back to the missing item.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dwarf: Entity = f["dwarf"]
    captain: Entity = f["captain"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question=f"Who solves the mystery in the story?",
            answer=f"{dwarf.id} solves it by watching carefully and following clues.",
        ),
        QAItem(
            question=f"What item was missing?",
            answer=f"{mystery.missing} was missing, and that made the crew upset.",
        ),
        QAItem(
            question=f"Why did {captain.id} sound angry at first?",
            answer=f"{captain.id} was worried because the crew could not find {mystery.missing}.",
        ),
        QAItem(
            question=f"Where did the clues lead the crew?",
            answer=f"The clues led them toward {mystery.found_in}, where the missing thing turned up.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The missing item was found, the conflict eased, and the crew could sail on again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dwarf in a fantasy pirate story?",
            answer="A dwarf is a small person from fantasy stories who is often strong, careful, and brave.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something unknown that people try to solve by looking for clues.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates for sailing, exploring, and carrying treasures or supplies.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery is valid when it has a missing thing and a place where clues can be found.
valid_mystery(M) :- mystery(M), missing(M, _), clue_place(M, _).

% A story is valid when the setting affords searching and the mystery can be solved there.
valid_story(S, M) :- setting(S), mystery(M), affords(S, search), valid_mystery(M).

% Dwarf and captain are compatible with pirate tale stories.
pirate_tale_story(S, M, dwarf) :- valid_story(S, M), hero_kind(dwarf).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue_place", mid, m.found_in))
    lines.append(asp.fact("hero_kind", "dwarf"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(s, m) for s in SETTINGS for m in MYSTERIES if "search" in SETTINGS[s].affords}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python story gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld: dwarf, conflict, mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--dwarf-name", choices=DWARF_NAMES)
    ap.add_argument("--captain-name", choices=CAPTAIN_NAMES)
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
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.mystery is not None and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    dwarf_name = args.dwarf_name or rng.choice(DWARF_NAMES)
    captain_name = args.captain_name or rng.choice(CAPTAIN_NAMES)
    return StoryParams(setting=setting, mystery=mystery, dwarf_name=dwarf_name, captain_name=captain_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.dwarf_name, params.captain_name)
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
        lines.append(f"  {e.id:16} kind={e.kind:9} type={e.type:8} meters={e.meters} memes={e.memes}")
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
    StoryParams(setting="ship", mystery="missing_map", dwarf_name="Bran", captain_name="Captain Marlow"),
    StoryParams(setting="dock", mystery="missing_key", dwarf_name="Nori", captain_name="Captain Sera"),
    StoryParams(setting="cave", mystery="missing_lantern", dwarf_name="Dorin", captain_name="Captain Flint"),
    StoryParams(setting="island", mystery="missing_compass", dwarf_name="Kellan", captain_name="Captain Vale"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (setting, mystery) combos:\n")
        for s, m in stories:
            print(f"  {s:8} {m}")
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
            header = f"### {p.dwarf_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
