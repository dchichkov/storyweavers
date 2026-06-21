#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hallelujahs_folder_dilate_conflict_humor_pirate_tale.py
=======================================================================================

A small, standalone story world in a pirate-tale frame.

Premise
-------
Two pirates find a windy folder of treasure notes on a little ship. One pirate
wants to keep the folder tight and secret; the other wants to let it dilate open
so they can read the map. The argument gets silly, a burst of "hallelujahs"
interrupts the squabble, and the crew solves the problem by using a safe, funny
method that lets everyone see the clues.

This world keeps the domain small on purpose:
- one ship
- two child pirates
- one folder
- one treasure clue
- one conflict
- one humorous turn
- one resolution

It follows the storyworld contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate and an inline ASP twin
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

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
BRAVERY_INIT = 5.0
DILATE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class ShipFrame:
    id: str
    place: str
    deck_phrase: str
    dark_spot: str
    style_phrase: str
    sail_name: str

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
class Folder:
    id: str
    label: str
    phrase: str
    secret: str
    noisy: str
    can_dilate: bool = True
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
class TreasureClue:
    id: str
    label: str
    phrase: str
    place: str
    hidden: str
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
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
    def __init__(self, frame: ShipFrame) -> None:
        self.frame = frame
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
        clone = World(self.frame)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes["argue"] < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_humor(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("laughed") and ("humor",) not in world.fired:
        world.fired.add(("humor",))
        for e in world.characters():
            e.memes["glee"] += 1
        out.append("__humor__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict), Rule("humor", "social", _r_humor)]


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


def folder_at_risk(folder: Folder) -> bool:
    return folder.can_dilate


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= 2]


def resolution_ok(resolution: Resolution, delay: int) -> bool:
    return resolution.power >= delay + 1


def predict_dilate(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_dilate(sim, sim.get(target_id), narrate=False)
    target = sim.get(target_id)
    return {"opened": target.meters["open"] >= THRESHOLD, "messy": target.meters["messy"] > 0}


def _do_dilate(world: World, folder_ent: Entity, narrate: bool = True) -> None:
    folder_ent.meters["open"] += 1
    folder_ent.meters["pulled"] += 1
    if narrate:
        propagate(world, narrate=True)


def setup(world: World, a: Entity, b: Entity, frame: ShipFrame) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a breezy day aboard the {frame.sail_name}, {a.id} and {b.id} turned the deck "
        f"into {frame.style_phrase}. {frame.deck_phrase}"
    )


def find_folder(world: World, folder: Folder, clue: TreasureClue) -> None:
    world.say(
        f"Then they found {folder.phrase} tucked by {clue.hidden}. It looked too tight to open, "
        f"but it clearly hid {clue.phrase}."
    )


def want_read(world: World, a: Entity, folder: Folder) -> None:
    a.memes["desire"] += 1
    world.say(f'{a.id} pointed at the folder. "We should open it and read it now," {a.pronoun()} said.')


def warn(world: World, b: Entity, a: Entity, folder: Folder, clue: TreasureClue) -> None:
    pred = predict_dilate(world, "folder")
    b.memes["caution"] += 1
    world.facts["predicted_mess"] = pred["messy"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "If the folder dilates too fast, the clue '
        f'can flap out and blow away. We should be careful, mate."'
    )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["argue"] += 1
    b.memes["argue"] += 1
    world.say(f'"Nay, it will be fine!" {a.id} said. "{b.id}, you worry like a gull in a storm."')


def flash_hallelujahs(world: World, a: Entity, b: Entity) -> None:
    world.facts["laughed"] = True
    world.say(
        f"Just then, a deckhand sneezed three grand hallelujahs from the hatch, and the whole ship "
        f"blinked in surprise. Even the argument took a tiny bow."
    )


def dilate_folder(world: World, folder_ent: Entity, folder: Folder, clue: TreasureClue) -> None:
    _do_dilate(world, folder_ent, narrate=False)
    if folder_ent.meters["open"] >= THRESHOLD:
        world.say(
            f"{folder.label.capitalize()} dilated open with a soft fwip, and the treasure note popped "
            f"up like a tiny sail. For a second everyone stared."
        )
    else:
        world.say(f"{folder.label.capitalize()} only quivered, but that was enough to make them laugh.")


def rescue_clue(world: World, b: Entity, folder_ent: Entity, clue: TreasureClue, resolution: Resolution) -> None:
    folder_ent.meters["open"] = 0.0
    world.say(
        f'{b.id} laughed and used {resolution.text}. The note stayed put, and {clue.label} stayed safe in the folder.'
    )


def end(world: World, a: Entity, b: Entity, frame: ShipFrame, clue: TreasureClue) -> None:
    world.say(
        f"At last, the two pirates grinned, tucked the folder under {a.pronoun("possessive")} arm, and "
        f"followed {clue.phrase} toward the {frame.place}. They sailed on, still laughing about the hallelujahs."
    )


def scuttle_fail(world: World, a: Entity, b: Entity, frame: ShipFrame, clue: TreasureClue) -> None:
    world.say(
        f"That was too much at once. The note fluttered away toward the {frame.dark_spot}, and the pair "
        f"had to chase it while the whole deck shook with laughing confusion."
    )


def tell(frame: ShipFrame, folder: Folder, clue: TreasureClue, resolution: Resolution,
         a_name: str = "Pip", a_gender: str = "boy",
         b_name: str = "Ria", b_gender: str = "girl",
         delay: int = 0) -> World:
    world = World(frame)
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="instigator"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="cautioner"))
    folder_ent = world.add(Entity(id="folder", type="folder", label=folder.label))
    clue_ent = world.add(Entity(id="clue", type="clue", label=clue.label))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = 2.0

    setup(world, a, b, frame)
    world.para()
    find_folder(world, folder, clue)
    want_read(world, a, folder)
    warn(world, b, a, folder, clue)
    argue(world, a, b)
    flash_hallelujahs(world, a, b)

    world.para()
    dilate_folder(world, folder_ent, folder, clue)
    ok = resolution_ok(resolution, delay)
    if ok:
        rescue_clue(world, b, folder_ent, clue, resolution)
        end(world, a, b, frame, clue)
        outcome = "contained"
    else:
        scuttle_fail(world, a, b, frame, clue)
        outcome = "lost"

    world.facts.update(
        instigator=a, cautioner=b, frame=frame, folder=folder, clue=clue,
        resolution=resolution, outcome=outcome, delay=delay,
        opened=folder_ent.meters["open"] >= THRESHOLD
    )
    return world


FRAMES = {
    "pirate_tale": ShipFrame(
        "pirate_tale", "cove", "The deck was all ropes, barrels, and a sleepy crow's nest.",
        "the dark spot under the sailcloth", "a pirate game", "the Little Gull"
    ),
    "harbor_tale": ShipFrame(
        "harbor_tale", "harbor", "The deck smelled like salt and plank wood, and a bucket clanked nearby.",
        "the shadow behind the mainmast", "a shipboard game", "the Bright Prow"
    ),
}

FOLDERS = {
    "ledger": Folder("ledger", "a squashed folder", "a squashed folder of treasure notes", "the map", "the note"),
    "bundle": Folder("bundle", "a blue folder", "a blue folder tied with string", "the clue", "the paper"),
}

CLUES = {
    "island": TreasureClue("island", "treasure clue", "a treasure clue", "the island", "a palm leaf"),
    "cove": TreasureClue("cove", "sea clue", "a sea clue", "the cove", "a barrel"),
}

RESOLUTIONS = {
    "clip": Resolution(
        "clip", 3, 3,
        "clipped the folder shut with a wooden clothespin",
        "tried to clip it shut, but the note still flapped away",
        "clipped the folder shut with a wooden clothespin",
        tags={"folder", "humor"},
    ),
    "stone": Resolution(
        "stone", 3, 2,
        "pressed the folder flat with a round pebble",
        "pressed the folder flat, but the wind was too keen",
        "pressed the folder flat with a round pebble",
        tags={"folder", "humor"},
    ),
    "song": Resolution(
        "song", 2, 1,
        "sang a silly sailor song while holding the folder steady",
        "sang a silly sailor song, but the page still bounced free",
        "sang a silly sailor song while holding the folder steady",
        tags={"humor"},
    ),
}

NAMES = ["Pip", "Ria", "Milo", "Nell", "Toby", "Ada", "Jo", "Kit"]
GENDERS = ["boy", "girl"]


@dataclass
@dataclass
class StoryParams:
    frame: str
    folder: str
    clue: str
    resolution: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    delay: int = 0
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
    for f in FRAMES:
        for folder in FOLDERS:
            for clue in CLUES:
                if folder_at_risk(FOLDERS[folder]):
                    combos.append((f, folder, clue))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld with conflict, humor, hallelujahs, and a dilating folder.")
    ap.add_argument("--frame", choices=FRAMES)
    ap.add_argument("--folder", choices=FOLDERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--instigator")
    ap.add_argument("--instigator-gender", choices=GENDERS, dest="instigator_gender")
    ap.add_argument("--cautioner")
    ap.add_argument("--cautioner-gender", choices=GENDERS, dest="cautioner_gender")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              if (args.frame is None or c[0] == args.frame)
              and (args.folder is None or c[1] == args.folder)
              and (args.clue is None or c[2] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    frame, folder, clue = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(k for k, r in RESOLUTIONS.items() if r.sense >= 2))
    if RESOLUTIONS[resolution].sense < 2:
        raise StoryError("(Refusing a too-weak resolution.)")
    ig = args.instigator_gender or rng.choice(GENDERS)
    cg = args.cautioner_gender or ("girl" if ig == "boy" else "boy")
    instigator = args.instigator or rng.choice(NAMES)
    cautioner = args.cautioner or rng.choice([n for n in NAMES if n != instigator])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(frame, folder, clue, resolution, instigator, ig, cautioner, cg, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(FRAMES[params.frame], FOLDERS[params.folder], CLUES[params.clue], RESOLUTIONS[params.resolution],
                 params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child using the words "hallelujahs", "folder", and "dilate".',
        f"Tell a funny pirate story where {f['instigator'].id} and {f['cautioner'].id} argue about opening a folder, then laugh when the hallelujahs interrupt them.",
        f"Write a short conflict-and-humor story on a ship where a folder dilates open and the crew solves the problem in a safe, playful way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b = f["instigator"], f["cautioner"]
    folder, clue = f["folder"], f["clue"]
    resolution = f["resolution"]
    qa = [
        ("Who is the story about?",
         f"It is about {a.id} and {b.id}, two little pirates on a ship."),
        ("What did they find?",
         f"They found {folder.phrase}, and inside it there was {clue.phrase}."),
        ("Why did they argue?",
         f"{a.id} wanted to open the folder right away, but {b.id} worried the pages would flutter away if it dilated too fast."),
        ("What made the story funny?",
         f"The silly burst of hallelujahs from the hatch interrupted their argument, so even the pirates had to laugh."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did they solve the problem?",
            f"They used {resolution.qa_text} so the folder could stay open without losing the note. That let them keep the clue safe and keep sailing."
        ))
    else:
        qa.append((
            "What happened at the end?",
            f"The note blew away in the wind, so they had to chase it across the deck. It was still funny, but they had to start over."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["folder"].tags) | set(world.facts["clue"].tags) | set(world.facts["resolution"].tags)
    out = []
    if "folder" in tags:
        out.append(("What is a folder?", "A folder is something that holds papers together so they do not get lost."))
    if "humor" in tags:
        out.append(("What is humor?", "Humor is when something is funny and makes people smile or laugh."))
    out.append(("What does dilate mean?", "To dilate means to open wider or stretch out more."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict(E) :- argue(E).
humor :- laughed.
valid(F, Fo, C) :- frame(F), folder(Fo), clue(C), folder_at_risk(Fo).
outcome(contained) :- chosen_resolution(R), delay(D), power(R, P), P >= D + 1.
outcome(lost) :- chosen_resolution(R), delay(D), power(R, P), P < D + 1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid in FRAMES:
        lines.append(asp.fact("frame", fid))
    for fid, f in FOLDERS.items():
        lines.append(asp.fact("folder", fid))
        if f.can_dilate:
            lines.append(asp.fact("folder_at_risk", fid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([asp.fact("chosen_resolution", params.resolution), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    samples = [generate(resolve_params(argparse.Namespace(frame=None, folder=None, clue=None, resolution=None, instigator=None, instigator_gender=None, cautioner=None, cautioner_gender=None, delay=None), random.Random(s)))
               for s in range(10)]
    if all(s.story for s in samples):
        print("OK: generate() smoke test passed.")
    else:
        rc = 1
        print("MISMATCH: empty generated story.")
    return rc


CURATED = [
    StoryParams("pirate_tale", "ledger", "island", "clip", "Pip", "boy", "Ria", "girl", 0),
    StoryParams("harbor_tale", "bundle", "cove", "stone", "Milo", "boy", "Nell", "girl", 1),
    StoryParams("pirate_tale", "bundle", "island", "song", "Ada", "girl", "Toby", "boy", 0),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.frame and args.folder and args.clue and (args.frame, args.folder, args.clue) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    frame, folder, clue = rng.choice(sorted([c for c in combos
                                             if (args.frame is None or c[0] == args.frame)
                                             and (args.folder is None or c[1] == args.folder)
                                             and (args.clue is None or c[2] == args.clue)]))
    resolution = args.resolution or rng.choice(sorted(k for k, v in RESOLUTIONS.items() if v.sense >= 2))
    if RESOLUTIONS[resolution].sense < 2:
        raise StoryError("(Refusing a too-weak resolution.)")
    ig = args.instigator_gender or rng.choice(GENDERS)
    cg = args.cautioner_gender or ("girl" if ig == "boy" else "boy")
    instigator = args.instigator or rng.choice(NAMES)
    cautioner = args.cautioner or rng.choice([n for n in NAMES if n != instigator])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(frame, folder, clue, resolution, instigator, ig, cautioner, cg, delay)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(f, folder, clue) for f in FRAMES for folder in FOLDERS for clue in CLUES if folder_at_risk(FOLDERS[folder])]


def generate(params: StoryParams) -> StorySample:
    world = tell(FRAMES[params.frame], FOLDERS[params.folder], CLUES[params.clue], RESOLUTIONS[params.resolution],
                 params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def tell_world(params: StoryParams) -> World:
    return tell(FRAMES[params.frame], FOLDERS[params.folder], CLUES[params.clue], RESOLUTIONS[params.resolution],
                params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender, params.delay)


if __name__ == "__main__":
    main()
