#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scan_tripod_locate_bravery_kindness_ghost_story.py
==================================================================================

A small standalone storyworld for a ghost-story style tale about a child who
wants to scan a dark place with a tripod, locates a shy ghost, and learns that
bravery and kindness can turn fear into help.

This world keeps the simulation tiny and concrete:
- physical state uses meters (light, tremble, found, soot)
- emotional state uses memes (bravery, kindness, fear, trust, relief)
- the story is driven by state changes, not by a fixed paragraph with swapped
  nouns

It also includes:
- a Python reasonableness gate
- an inline ASP twin for parity checks
- three Q&A sets grounded in the simulated world
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_MIN = 4
KINDNESS_MIN = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



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
    is_haunted: bool = True

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
class ScanRig:
    id: str
    label: str
    phrase: str
    glow: str
    power: int
    sense: int

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
class LocateTool:
    id: str
    label: str
    phrase: str
    reach: int

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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.meters["seen"] >= THRESHOLD and ("spook",) not in world.fired:
        world.fired.add(("spook",))
        child.memes["fear"] += 1
        ghost.memes["trust"] += 1
        out.append("__spook__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    if not ghost or not child:
        return out
    if ghost.memes["trust"] >= THRESHOLD and ("soothe",) not in world.fired:
        world.fired.add(("soothe",))
        child.memes["kindness"] += 1
        child.memes["relief"] += 1
        ghost.memes["relief"] += 1
        out.append("__soothe__")
    return out


CAUSAL_RULES = [
    Rule("spook", "social", _r_spook),
    Rule("soothe", "social", _r_soothe),
]


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


def valid_combo(setting: Setting, rig: ScanRig, locator: LocateTool) -> bool:
    return setting.is_haunted and rig.sense >= 2 and locator.reach >= 1


def safe_to_brave(hero: Entity) -> bool:
    return hero.memes["bravery"] >= BRAVERY_MIN and hero.memes["kindness"] >= KINDNESS_MIN


def scan_scene(world: World, hero: Entity, rig: ScanRig, setting: Setting) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"At dusk, {hero.id} carried the {rig.label} into {setting.place}. "
        f"{hero.pronoun().capitalize()} set the {rig.label} on a tripod and clicked it on."
    )
    world.say(
        f"The beam did not bounce; it scanned the dark corner by the old wall, "
        f"{rig.glow}, as if the room itself were holding its breath."
    )


def locate_ghost(world: World, ghost: Entity, setting: Setting) -> None:
    ghost.meters["seen"] += 1
    world.say(
        f"Behind {setting.dark_spot}, {ghost.id} was there at last -- a small, pale ghost "
        f"with a wobbling hat and a lonely sigh."
    )


def warn_fright(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} took one brave step back, but did not run. "
        f"{hero.pronoun().capitalize()} remembered to be kind, even while scared."
    )


def kind_help(world: World, hero: Entity, ghost: Entity, locator: LocateTool) -> None:
    hero.memes["kindness"] += 1
    ghost.memes["trust"] += 1
    world.say(
        f'"Are you lost?" {hero.id} asked softly. '
        f'{hero.pronoun().capitalize()} held up the {locator.label} so the ghost could see the path.'
    )
    world.say(
        f"The little light helped {ghost.id} locate the doorway again."
    )


def ending(world: World, hero: Entity, ghost: Entity, setting: Setting) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"{ghost.id} gave a thin, grateful smile and floated toward the hall, "
        f"no longer trapped in {setting.place}."
    )
    world.say(
        f"{hero.id} left the tripod standing by the wall, proud and calm. "
        f"The dark corner was still dark, but it was not scary anymore."
    )


def tell(setting: Setting, rig: ScanRig, locator: LocateTool,
         hero_name: str = "Nina", hero_gender: str = "girl",
         ghost_name: str = "Moth", ghost_kind: str = "ghost",
         parent_name: str = "Mom") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender,
                            role="child", traits=["brave"], memes={"bravery": 3.0, "kindness": 3.0}))
    parent = world.add(Entity(id=parent_name, kind="character", type="mother",
                              role="parent", label="Mom"))
    ghost = world.add(Entity(id=ghost_name, kind="character", type=ghost_kind,
                             role="ghost", label="the ghost"))
    world.add(Entity(id="tripod", type="tool", label="tripod"))
    world.add(Entity(id="corner", type="place", label=setting.dark_spot))

    world.say(
        f"{hero.id} loved ghost stories, but {setting.place} had a real hush to it after dark."
    )
    world.say(
        f"Tonight, {hero.id}'s {parent.label_word} let {hero.pronoun('object')} stay up late "
        f"and try a careful scan with a {rig.label}."
    )

    world.para()
    scan_scene(world, hero, rig, setting)
    if setting.is_haunted:
        locate_ghost(world, ghost, setting)
    propagate(world, narrate=False)

    world.para()
    warn_fright(world, hero)
    kind_help(world, hero, ghost, locator)
    propagate(world, narrate=False)

    world.para()
    ending(world, hero, ghost, setting)

    world.facts.update(
        hero=hero, parent=parent, ghost=ghost, setting=setting, rig=rig, locator=locator,
        located=ghost.meters["seen"] >= THRESHOLD, soothed=ghost.memes["trust"] >= THRESHOLD,
        brave=safe_to_brave(hero),
    )
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "the boxes under the rafters", True),
    "hall": Setting("hall", "the long hall", "the shadow beside the umbrella stand", True),
    "stairwell": Setting("stairwell", "the stairwell", "the bend under the stairs", True),
}

SCAN_RIGS = {
    "lamp_scan": ScanRig("lamp_scan", "scan lamp", "a scan lamp", "steady gold", 3, 3),
    "ghost_camera": ScanRig("ghost_camera", "ghost camera", "a ghost camera", "white and bright", 4, 4),
    "lantern_scan": ScanRig("lantern_scan", "lantern", "a lantern on a tripod", "soft amber", 2, 2),
}

LOCATORS = {
    "bell": LocateTool("bell", "silver bell", "a silver bell", 1),
    "ribbon": LocateTool("ribbon", "red ribbon", "a red ribbon", 1),
    "lantern": LocateTool("lantern", "small lantern", "a small lantern", 2),
}

NAMES = ["Nina", "Maya", "Ivy", "Lena", "Owen", "Theo", "June", "Ada"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    rig: str
    locator: str
    hero_name: str
    hero_gender: str
    ghost_name: str
    parent_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for rid, r in SCAN_RIGS.items():
            for lid, l in LOCATORS.items():
                if valid_combo(s, r, l):
                    combos.append((sid, rid, lid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: scan, tripod, locate, kindness, bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rig", choices=SCAN_RIGS)
    ap.add_argument("--locator", choices=LOCATORS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ghost-name")
    ap.add_argument("--parent")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.rig is None or c[1] == args.rig)
              and (args.locator is None or c[2] == args.locator)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, rig, locator = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        rig=rig,
        locator=locator,
        hero_name=args.name or rng.choice(NAMES),
        hero_gender=args.gender or rng.choice(["girl", "boy"]),
        ghost_name=args.ghost_name or rng.choice(["Moth", "Pale Will", "Tiny Whisper"]),
        parent_name=args.parent or "Mom",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the words "scan", "tripod", and "locate".',
        f"Tell a gentle spooky story where {f['hero'].id} uses a {f['rig'].label} on a tripod to scan a dark place and locate a lost ghost.",
        f"Write a story about bravery and kindness in a haunted place, where a child scans the shadows and helps a ghost locate the way home.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, setting = f["hero"], f["ghost"], f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} use to scan the dark place?",
            answer=f"{hero.id} used a {f['rig'].label} on a tripod to scan the dark place. The steady light helped {hero.pronoun()} see what was hidden."
        ),
        QAItem(
            question=f"Who did {hero.id} locate?",
            answer=f"{hero.id} located {ghost.id}, a small ghost who was hiding near {setting.dark_spot}. Once seen, the ghost was no longer alone."
        ),
        QAItem(
            question=f"How did {hero.id} show bravery and kindness?",
            answer=f"{hero.id} stayed brave enough to keep scanning, and kind enough to speak softly instead of running away. That helped {ghost.id} trust {hero.pronoun('object')} and find the way out."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does it mean to scan something?",
               "To scan means to look slowly and carefully over a place, often with a light or a tool, so you can notice what is there."),
        QAItem("What is a tripod for?",
               "A tripod is a stand with three legs that helps keep a tool steady while it points at one place."),
        QAItem("What does locate mean?",
               "To locate something means to find where it is."),
        QAItem("What is bravery?",
               "Bravery means feeling afraid and still doing the helpful thing anyway."),
        QAItem("What is kindness?",
               "Kindness means speaking and acting gently so someone else feels safe and cared for."),
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
    lines.append("== (3) World knowledge ==")
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SCAN_RIGS[params.rig], LOCATORS[params.locator],
                 params.hero_name, params.hero_gender, params.ghost_name, "ghost", params.parent_name)
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
    StoryParams("attic", "ghost_camera", "lantern", "Nina", "girl", "Moth", "Mom"),
    StoryParams("hall", "lamp_scan", "bell", "Owen", "boy", "Pale Will", "Mom"),
    StoryParams("stairwell", "lantern_scan", "ribbon", "June", "girl", "Tiny Whisper", "Mom"),
]


def explain_rejection() -> str:
    return "(No story: that combination does not give the child a real chance to scan, locate, and help in the haunted place.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in SCAN_RIGS:
        lines.append(asp.fact("rig", rid))
    for lid in LOCATORS:
        lines.append(asp.fact("locator", lid))
    for sid, s in SETTINGS.items():
        if s.is_haunted:
            lines.append(asp.fact("haunted", sid))
    for rid, r in SCAN_RIGS.items():
        lines.append(asp.fact("sense", rid, r.sense))
    for lid, l in LOCATORS.items():
        lines.append(asp.fact("reach", lid, l.reach))
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    lines.append(asp.fact("kindness_min", KINDNESS_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, R, L) :- setting(S), rig(R), locator(L), haunted(S), sense(R, SR), SR >= 2, reach(L, RL), RL >= 1.
brave_ok(B) :- bravery_min(B).
kind_ok(K) :- kindness_min(K).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def build_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = build_choice(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
