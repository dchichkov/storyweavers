#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lighten_quest_conflict_twist_whodunit.py
=========================================================================

A small whodunit-style storyworld for a child-sized mystery about a quest to
lighten a dark room, a conflict over a missing object, and a twist that reveals
the surprising culprit. The world is built from typed entities, physical meters,
and emotional memes, with a causal turn driven by evidence rather than a frozen
paragraph template.

The premise is simple:
- A child detective wants to solve a small mystery.
- Something important has gone missing in a dark place.
- A conflict grows because the wrong person is blamed.
- The twist reveals the true culprit was helpful, not harmful.
- The ending proves the room has been lightened and the group feels better.

This script follows the Storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- StoryParams, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- Python gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    found: bool = False
    hidden: bool = False
    helpful: bool = False
    clue: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    dark_spot: str
    quest_goal: str
    mood: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    useful_for: str
    hidden_reason: str = ""
    lightens: bool = False
    clue_value: int = 0
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    oddity: str
    clue_style: str
    innocent: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_dark(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["darkness"] < THRESHOLD:
        return out
    sig = ("dark",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["unease"] += 1
    out.append("__dark__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    if detective.meters["clues"] < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["confidence"] += 1
    out.append("__clue__")
    return out


CAUSAL_RULES = [Rule("dark", "physical", _r_dark), Rule("clue", "social", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(setting: Setting, item: Item, suspect: Suspect) -> bool:
    return setting.place and item.lightens and suspect.innocent


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for sus_id, suspect in SUSPECTS.items():
                if reasonableness_ok(setting, item, suspect):
                    combos.append((sid, iid, sus_id))
    return combos


def make_room(world: World, setting: Setting) -> None:
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    room.meters["darkness"] = 1.0
    room.attrs["dark_spot"] = setting.dark_spot


def examine(world: World, detective: Entity, suspect: Entity, item: Item) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"In {world.get('room').label}, {detective.id} began a little quest to solve a whodunit. "
        f"{detective.pronoun().capitalize()} wanted to find the missing {item.label} and "
        f"lighten the dark room."
    )
    world.say(
        f"At first, {suspect.id} looked guilty. {suspect.alibi} But there was still a strange clue: "
        f"{suspect.oddity}."
    )


def conflict(world: World, detective: Entity, suspect: Entity, item: Item) -> None:
    detective.memes["worry"] += 1
    suspect.memes["hurt"] += 1
    world.say(
        f'"It was {suspect.id}!" said {detective.id}, and the room grew tense. '
        f'But {suspect.id} frowned. "{item.label} was never stolen," {suspect.pronoun()} said. '
        f'The argument made the mystery feel bigger.'
    )


def find_clue(world: World, detective: Entity, item: Item, helper: Entity) -> None:
    detective.meters["clues"] += 1
    world.say(
        f"{detective.id} checked the floor, the shelf, and the window ledge. Then {helper.id} pointed to a "
        f"small clue: {item.phrase} tucked in a safe place where nobody had looked."
    )


def twist(world: World, detective: Entity, suspect: Entity, helper: Entity, item: Item) -> None:
    detective.memes["surprise"] += 1
    helper.memes["warmth"] += 1
    world.say(
        f"Then came the twist. {helper.id} had moved the {item.label} to keep it safe during cleaning, "
        f"and {suspect.id} had only been trying to help."
    )
    world.say(
        f"{detective.id} blinked, then laughed softly. The real answer was kinder than the guess."
    )


def lighten_scene(world: World, detective: Entity, helper: Entity, item: Item) -> None:
    room = world.get("room")
    room.meters["darkness"] = 0.0
    room.meters["light"] += 1
    for c in world.characters():
        c.memes["relief"] += 1
    world.say(
        f"{helper.id} opened the curtains and turned on a bright lamp. The room began to lighten at once, "
        f"and the shadows slipped away from the corners."
    )
    world.say(
        f"{detective.id} set the {item.label} on the table, safe and found, while everyone smiled at the solved mystery."
    )


def tell(setting: Setting, item: Item, suspect: Suspect, helper_name: str = "Mina",
         detective_name: str = "Nico", helper_type: str = "girl", detective_type: str = "boy") -> World:
    world = World()
    make_room(world, setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type,
                                 role="detective", traits=["curious"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type,
                              role="helper", traits=["careful"]))
    suspect_ent = world.add(Entity(id=suspect.id, kind="character", type=suspect.type,
                                   role="suspect", traits=["quiet"]))
    world.add(Entity(id="clue", type="thing", label=item.label, clue=True, helpful=True))
    examine(world, detective, suspect_ent, item)
    world.para()
    conflict(world, detective, suspect_ent, item)
    find_clue(world, detective, item, helper)
    world.para()
    twist(world, detective, suspect_ent, helper, item)
    lighten_scene(world, detective, helper, item)
    world.facts.update(setting=setting, item=item, suspect=suspect, helper=helper,
                       detective=detective, room=world.get("room"), outcome="solved")
    return world


SETTINGS = {
    "library": Setting("library", "the little library", "the back shelves", "find the missing lamp", "quiet"),
    "attic": Setting("attic", "the attic", "the dusty corner", "find the missing candle lantern", "dim"),
    "hall": Setting("hall", "the hall", "the umbrella stand", "find the missing key", "hushed"),
}

ITEMS = {
    "lamp": Item("lamp", "lamp", "a small lamp", "to brighten dark places", hidden_reason="cleaning", lightens=True, clue_value=2, tags={"lighten"}),
    "lantern": Item("lantern", "lantern", "a tiny lantern", "to lighten dark rooms", hidden_reason="set aside for safety", lightens=True, clue_value=2, tags={"lighten"}),
    "key": Item("key", "key", "a brass key", "to open a locked drawer", hidden_reason="borrowed for a puzzle", lightens=False, clue_value=1, tags={"quest"}),
}

SUSPECTS = {
    "cat": Suspect("Patches", "cat", "thing", "Patches was curled by the chair", "there was dust on its paws", "paw prints", innocent=True, tags={"twist"}),
    "neighbor": Suspect("MrsWren", "woman", "Mrs. Wren was nearby with a tidy basket", "she had been carrying books", "a ribbon was tied to the basket", innocent=True, tags={"conflict"}),
    "brother": Suspect("Owen", "boy", "Owen had been helping in the hall", "he looked nervous", "his pockets were full of paper stars", innocent=True, tags={"quest"}),
}

QUESTION_KNOWLEDGE = {
    "lamp": [("What does a lamp do?", "A lamp shines light so people can see in a dark place.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can glow softly and help brighten a room or path.")],
    "key": [("What is a key for?", "A key opens a lock, like on a drawer, door, or box.")],
    "quest": [("What is a quest?", "A quest is a goal or search someone goes on to find something important.")],
    "twist": [("What is a twist in a mystery?", "A twist is a surprising new fact that changes what you thought was true.")],
    "conflict": [("What is conflict in a story?", "Conflict is when characters disagree or have a problem that needs to be solved.")],
    "lighten": [("What does lighten mean?", "To lighten something means to make it less dark or brighter.")],
}
QUESTION_ORDER = ["quest", "conflict", "twist", "lighten", "lamp", "lantern", "key"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    item: str
    suspect: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit where a curious detective follows a quest to {f['setting'].quest_goal} and includes the word 'lighten'.",
        f"Tell a mystery story with conflict and a twist where {f['detective'].id} suspects {f['suspect'].id} but the answer turns out kinder than expected.",
        f"Write a short story about a missing {f['item'].label}, a wrong guess, and a final scene that lightens the room.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    det, sus, helper, item, setting = f["detective"], f["suspect"], f["helper"], f["item"], f["setting"]
    return [
        ("Who was trying to solve the mystery?",
         f"{det.id} was the one on the quest, trying to solve the whodunit and find the missing {item.label}."),
        ("Why was there conflict?",
         f"{det.id} thought {sus.id} was guilty, so they argued for a moment. The tension came from guessing too fast before checking the clues."),
        ("What was the twist?",
         f"{helper.id} showed that {sus.id} had been helping, not hiding the {item.label}. The surprising truth changed the whole mystery."),
        ("How did the story end?",
         f"The room was lightened when {helper.id} turned on a lamp and the missing {item.label} was set back in place. After that, everyone felt relieved and the mystery was solved."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | set(world.facts["suspect"].tags) | {"quest", "conflict", "twist", "lighten"}
    out: list[tuple[str, str]] = []
    for tag in QUESTION_ORDER:
        if tag in tags:
            out.extend(QUESTION_KNOWLEDGE[tag])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.found:
            bits.append("found=True")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.item in ITEMS and params.suspect in SUSPECTS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, suspect = rng.choice(sorted(combos))
    return StoryParams(setting, item, suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], SUSPECTS[params.suspect])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
valid(S, I, U) :- setting(S), item(I), suspect(U), lightens(I), innocent(U).
outcome(solved) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.lightens:
            lines.append(asp.fact("lightens", iid))
        if item.tags:
            for t in sorted(item.tags):
                lines.append(asp.fact("tag", iid, t))
    for uid, sus in SUSPECTS.items():
        lines.append(asp.fact("suspect", uid))
        if sus.innocent:
            lines.append(asp.fact("innocent", uid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("only in python:", sorted(py - cl))
        print("only in clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-tested ordinary generation.")
    except Exception as e:
        rc = 1
        print(f"FAIL: generation smoke test crashed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with quest, conflict, and twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
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


CURATED = [
    StoryParams("library", "lamp", "cat"),
    StoryParams("attic", "lantern", "neighbor"),
    StoryParams("hall", "key", "brother"),
]


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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for t in vals:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
