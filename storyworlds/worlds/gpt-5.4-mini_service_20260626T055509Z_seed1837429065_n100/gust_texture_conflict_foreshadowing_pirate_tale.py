#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100/gust_texture_conflict_foreshadowing_pirate_tale.py
=========================================================================================================

A small pirate-tale storyworld about a crew, a gust, and a telling texture.

The seed suggests a classical, child-facing pirate story with:
- gust: a sudden wind that can push the ship off course
- texture: a map or sail surface that can be felt, read, or noticed
- conflict: the crew disagrees about what to do
- foreshadowing: a subtle clue at the start that matters later

This script models a tiny shipboard world with physical meters and emotional memes,
then simulates a short tale where a strange texture and an uneasy gust become part
of the solution.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little ship"
    sea_state: str = "calm"


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.weather: str = "calm"

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
        import copy

        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.weather = self.weather
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "harbor": Setting(place="the harbor", sea_state="calm"),
    "reef": Setting(place="the reef side", sea_state="breezy"),
    "island": Setting(place="the island cove", sea_state="windy"),
}

CHAR_TYPES = {
    "girl": ["Ava", "Mina", "Lena", "Tia"],
    "boy": ["Finn", "Rowan", "Pip", "Jory"],
}

MATES = {
    "parrot": Entity(id="parrot", kind="character", type="bird", label="parrot"),
    "first_mate": Entity(id="first_mate", kind="character", type="man", label="first mate"),
}

# A small curated set of pirate items with a tactile clue and a weather risk.
ITEMS = {
    "map": {
        "label": "map",
        "phrase": "an old treasure map with a rough, sandpapery texture",
        "texture": "rough",
        "clue": "There was a tiny crease in the corner, like it had been folded again and again.",
        "risk": "blown loose",
        "fix": "press the map flat under a brass compass",
    },
    "sail": {
        "label": "sail",
        "phrase": "a striped sail with a stiff, cracked texture",
        "texture": "stiff",
        "clue": "One seam had a shiny patch, as if someone had already repaired it before.",
        "risk": "ripped",
        "fix": "patch the sail with fresh canvas",
    },
    "rope": {
        "label": "rope",
        "phrase": "a coil of rope with a gritty salt texture",
        "texture": "gritty",
        "clue": "A few fibers were frayed near the end, as if the rope had tugged at something hard.",
        "risk": "slipped",
        "fix": "wrap the rope around the cleat twice",
    },
}

ACTIONS = {
    "gust": {
        "verb": "catch the sudden gust",
        "rush": "grab the flapping cloth",
        "weather": "windy",
        "effect": "the gust rocked the deck",
        "ask": "What if the wind comes harder?",
        "solve": "use the wind to guide the ship",
    },
    "texture": {
        "verb": "study the texture",
        "rush": "rub the surface",
        "weather": "breezy",
        "effect": "the surface told a quiet clue",
        "ask": "Why does it feel like that?",
        "solve": "notice the clue hidden in the feel of it",
    },
}

# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def intro(world: World, captain: Entity, mate: Entity, item: dict) -> None:
    world.say(
        f"Captain {captain.id} sailed {world.setting.place} with {mate.label} by {captain.pronoun('possessive')} side."
    )
    world.say(
        f"They carried {item['phrase']}, and its {item['texture']} feel made {captain.id} slow down for a moment."
    )


def foreshadow(world: World, item: dict) -> None:
    world.say(item["clue"])
    world.say("It was a tiny clue, but it sat in the story like a pebble in a shoe.")


def conflict(world: World, captain: Entity, mate: Entity, item: dict, action: dict) -> None:
    captain.memes["worry"] = captain.memes.get("worry", 0.0) + 1
    mate.memes["worry"] = mate.memes.get("worry", 0.0) + 1
    world.say(
        f"Then a sudden gust sprang up, and {action['effect']}."
    )
    world.say(
        f"{captain.id} wanted to {action['solve']}, but {mate.label} said the {item['label']} might get {item['risk']}."
    )
    world.say(
        f"They argued for a breath or two, while the wind rattled the ropes and the deck creaked under their boots."
    )


def resolution(world: World, captain: Entity, mate: Entity, item: dict, action: dict) -> None:
    captain.memes["joy"] = captain.memes.get("joy", 0.0) + 1
    captain.memes["worry"] = 0.0
    mate.memes["worry"] = 0.0
    world.say(
        f"At last, {captain.id} felt the {item['texture']} edge again and remembered the little crease from before."
    )
    world.say(
        f"That was the answer: the {item['label']} was not a warning to hide from, but a clue to use."
    )
    world.say(
        f"They did not fight the gust; they trimmed the sail, tied the rope, and steered the ship where the wind wanted to help."
    )
    world.say(
        f"By sunset, the sea was calm again, and {captain.id} smiled at how the first clue had led them safely home."
    )


def tell(setting: Setting, captain_name: str, mate_name: str) -> World:
    world = World(setting)
    captain = world.add(Entity(id=captain_name, kind="character", type="girl" if captain_name in CHAR_TYPES["girl"] else "boy"))
    mate = world.add(Entity(id=mate_name, kind="character", type="man", label="the first mate"))

    item_key = "map"
    item = ITEMS[item_key]
    action = ACTIONS["gust"]

    world.facts.update(
        captain=captain,
        mate=mate,
        item=item,
        action=action,
        setting=setting,
    )

    intro(world, captain, mate, item)
    world.para()
    foreshadow(world, item)
    world.para()
    conflict(world, captain, mate, item, action)
    world.para()
    resolution(world, captain, mate, item, action)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    item = f["item"]
    return [
        f"Write a short pirate tale for a young child about Captain {captain.id}, a gust of wind, and {item['phrase']}.",
        f"Tell a gentle story where a pirate notices the texture of a map before a gust causes trouble.",
        f"Write a small sea adventure with foreshadowing, a conflict over the wind, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    item = f["item"]
    action = f["action"]
    return [
        QAItem(
            question=f"What did Captain {captain.id} notice about the treasure map at the start?",
            answer=f"Captain {captain.id} noticed that {item['phrase']} had a {item['texture']} feel, and that small detail mattered later.",
        ),
        QAItem(
            question=f"Why did {captain.id} and {mate.label} start to worry when the gust blew?",
            answer=f"They worried because the sudden gust could make the {item['label']} {item['risk']}, and that would spoil their plan at sea.",
        ),
        QAItem(
            question=f"How did Captain {captain.id} solve the problem in the end?",
            answer=f"{captain.id} remembered the clue in the texture, then used the wind well by trimming the sail and steadying the rope instead of fighting the gust.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gust?",
            answer="A gust is a sudden burst of wind that can push hats, sails, and loose papers around.",
        ),
        QAItem(
            question="What does texture mean?",
            answer="Texture is how something feels to touch, like rough, smooth, soft, or scratchy.",
        ),
        QAItem(
            question="Why do sailors watch the wind?",
            answer="Sailors watch the wind because it can help move a ship or make it harder to steer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A map-like item is relevant when its texture is noticed before the wind event.
noticed_texture(I) :- item(I), texture(I,_).

% A gust creates conflict if the crew worries and the item can be blown loose.
gust_conflict(I) :- item(I), risk(I,"blown loose").

% A story is valid when it has both foreshadowing and a conflict that is later resolved.
valid_story(S) :- setting(S), noticed_texture(map), gust_conflict(map).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("sea_state", sid, s.sea_state))
    for iid, info in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("texture", iid, info["texture"]))
        lines.append(asp.fact("risk", iid, info["risk"]))
    for aid, info in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("weather", aid, info["weather"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/1."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {("harbor",)}
    if clingo_set == python_set:
        print("OK: clingo gate matches python gate (1 valid story).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("  clingo:", sorted(clingo_set))
    print("  python:", sorted(python_set))
    return 1


def asp_show() -> str:
    return asp_program("#show valid_story/1.")


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with gust, texture, conflict, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--captain-name", choices=CHAR_TYPES["girl"] + CHAR_TYPES["boy"])
    ap.add_argument("--mate-name", default="the first mate")
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
    captain_name = args.captain_name or rng.choice(CHAR_TYPES["girl"] + CHAR_TYPES["boy"])
    mate_name = args.mate_name or "the first mate"
    return StoryParams(captain_name=captain_name, mate_name=mate_name, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.captain_name, params.mate_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(f"{len(asp.atoms(model, 'valid_story'))} valid story seed(s).")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting in SETTINGS:
            params = StoryParams(captain_name="Ava", mate_name="the first mate", setting=setting)
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
