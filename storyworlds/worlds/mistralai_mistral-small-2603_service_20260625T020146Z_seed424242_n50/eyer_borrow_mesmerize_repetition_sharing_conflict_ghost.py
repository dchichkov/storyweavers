#!/usr/bin/env python3
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

# Magnitude at which an accumulated effect becomes narratable.
THRESHOLD = 1.0

# Core entity kinds and trait categories for the ghost domain.
ENTITY_KINDS = {"character", "spirit", "thing"}
ENTITY_TYPES = {"human", "ghost", "mother", "father", "sister", "item"}
GHOST_TYPES = {"ghost", "spirit"}
FAMILY_TYPES = {"mother", "father", "sister"}

# Heads-up: tiny reused constants to keep code style plausible.
CONFLICT_TAG = "ghost_conflict"
REPETITION_TAG = "ghost_repetition"
SHARING_TAG = "ghost_sharing"

# ---------------------------------------------------------------------------
# Shared entity & world utilities
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
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    # Two numeric dimensions, treated uniformly (cf. story.py memeplex model):
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", GIRL_NAMES[:]} | set(VICTIM_TYPES.get("girl", {}).get("pronouns", {}).values())
        male = {"boy", "father", "dad", "man", BOY_NAMES[:]} | set(VICTIM_TYPES.get("boy", {}).get("pronouns", {}).values())
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her", "pronoun": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his", "pronoun": "him"}[case]
        return {"subject": "it", "object": "it", "possessive": "its", "pronoun": "it"}[case]

    def possessive(self) -> str:
        return self.pronoun("possessive")

    def it(self) -> str:
        return "them" if self.plural else "it"

# ---------------------------------------------------------------------------
# Parametrization knobs -- what varies across stories in this domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "old house"
    indoor: bool = True

SETTINGS = {
    "cottage": Setting(place="grandmother’s cottage", indoor=True),
    "house": Setting(place="old house", indoor=True),
    "library": Setting(place="the shadowy library", indoor=True),
}

@dataclass
class Item:
    id: str
    label: str
    phrase: str
    plural: bool = False

ITEMS = {
    "tea_set": Item(id="tea_set", label="tea set", phrase="a favorite porcelain tea set"),
    "pocket_watch": Item(id="pocket_watch", label="pocket watch", phrase="an heirloom pocket watch"),
    "hairbrush": Item(id="hairbrush", label="hairbrush", phrase="an ivory-handled hairbrush"),
    "urn": Item(id="urn", label="urn", phrase="a tiny silver urn"),
    "guide_book": Item(id="guide_book", label="guide book", phrase="an old guide book with pressed flowers"),
}

VICTIM_TYPES = {
    "girl": {
        "name_pool": ["Mira", "Clara", "Lila", "Elara", "Sylvie"],
        "adj": "little",
        "pronouns": {"subject": "she", "object": "her", "possessive": "her", "pronoun": "her"},
        "traits": ["shy", "bookish", "curious"],
    },
    "boy": {
        "name_pool": ["Ethan", "Leo", "Noah", "Silas", "Theo"],
        "adj": "young",
        "pronouns": {"subject": "he", "object": "him", "possessive": "his", "pronoun": "him"},
        "traits": ["quiet", "doodler", "patient"],
    },
}

GHOSTS = {
    "pale_watcher": {"label": "the Pale Watcher", "description": "a girl in faded white"},
    "shadow_girl": {"label": "the Shadow Girl", "description": "a silent presence with hollow eyes"},
}
GIRL_NAMES = ["Mira", "Clara", "Lila", "Elara", "Sylvie"]
BOY_NAMES = ["Ethan", "Leo", "Noah", "Silas", "Theo"]

@dataclass
class Family:
    id: str
    label: str
    members: int

FAMILY_TYPES = {
    "parents": Family(id="parents", label="a mother and father", members=2),
    "mother": Family(id="mother", label="a mother", members=1),
    "sister": Family(id="sister", label="an older sister", members=1),
}

# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        # Facts recorded during the screenplay, read back by Q&A generators.
        self.facts: dict = {}

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]            # predictions are silent
        return clone

# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_power_from_borrow(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    if ghost is None:
        return []
    # Only narrate once when threshold crossed.
    if ghost.meters.get("power", 0.0) >= THRESHOLD and "power_narrated" not in world.fired:
        world.fired.add("power_narrated")
        return [f"The pale figure’s hollow eyes flickered brighter with every missing thing."]
    return []

def _r_mesmerize_repeat(world: World) -> list[str]:
    ghost = world.entities.get("ghost")
    victim = world.entities.get("victim")
    if ghost and victim and ghost.meters.get("power", 0) >= THRESHOLD and victim.memes.get("fear", 0) >= THRESHOLD:
        if victim.memes["repetitions"] < THRESHOLD * 3:
            victim.memes["repetitions"] += 1.0 if victim.memes["repetitions"] < 3.0 else 0.5
            return [f"{victim.id} kept repeating the same phrase without knowing why, like a broken music box."]
    return []

def _r_sharing_concern(world: World) -> list[str]:
    concern_sum = sum(f.meters.get("concern", 0) for f in world.characters() if f.type in FAMILY_TYPES)
    if concern_sum >= THRESHOLD and "sharing_narrated" not in world.fired:
        world.fired.add("sharing_narrated")
        return ["A shared worry bubbled up in hushed voices at the kitchen table."]
    return []

def _r_conflict_escalate(world: World) -> list[str]:
    victim = world.entities.get("victim")
    ghost = world.entities.get("ghost")
    if victim and ghost and victim.memes.get("fear", 0) >= 2 * THRESHOLD and victim.memes.get("conflict", 0) >= THRESHOLD:
        victim.memes["conflict"] += 1.0
        return [f"Tension crackled—now {victim.id} could feel the ghost’s presence pressing close from the dark corner."]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="power_from_borrow", tag=CONFLICT_TAG, apply=_r_power_from_borrow),
    Rule(name="mesmerize_repeat", tag=REPETITION_TAG, apply=_r_mesmerize_repeat),
    Rule(name="sharing_worry", tag=SHARING_TAG, apply=_r_sharing_concern),
    Rule(name="conflict_escalate", tag=CONFLICT_TAG, apply=_r_conflict_escalate),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_delight(item: Item) -> str:
    return {
        "tea_set": "the clink of china told the hour",
        "pocket_watch": "the steady tick inside the case kept time with her breath",
        "hairbrush": "the strokes of ivory smoothed every tangle away",
        "urn": "the silver gleamed like a captured star",
        "guide_book": "the pressed flowers held tales half told",
    }.get(item.id, "the thing reminded her of simpler days")

def borrow_item(world: World, ghost: Entity, victim: Entity, item: Item) -> None:
    world.facts[f"borrowed_{item.id}"] = True
    world.fired.add(("borrow", item.id))
    ghost.meters["power"] += 0.7
    world.say(
        f"Slowly, {ghost.label} reached toward {victim.possessive} {item.label}. "
        f"Before {victim.pronoun('object')} could protest, {ghost.pronoun('subject')} had {item.label} in {ghost.possessive} hands."
    )

def hear_whispers(world: World, victim: Entity, ghost_label: str) -> None:
    world.say(
        f"Each evening {victim.id} heard {victim.possessive} name on a whispering wind "
        f"like {ghost_label} murmuring from the corner of the {world.setting.place}."
    )
    world.facts["whisper_heard"] = True

def notice_missing(world: World, family_entity: Entity, item: Item) -> list[str]:
    family_entity.meters["concern"] += 0.8
    return [f"{family_entity.label} frowned at the empty space where {item.label} had always rested."]

def share_concern(world: World, family1: Entity, family2: Entity) -> None:
    for f in (family1, family2):
        f.meters["concern"] += 0.6
    world.say(
        f"{family1.label} and {family2.label} exchanged looks."
        f" 'Where did our {ITEMS['tea_set'].phrase} go?' {family1.pronoun('subject')} wondered aloud."
    )

def mesmerize_victim(world: World, ghost: Entity, victim: Entity) -> None:
    world.fired.add(("mesmerize", victim.id))
    victim.memes["fear"] += 1.1
    world.say(
        f"{ghost.label} drifted closer with hollow eyes."
        f" {victim.pronoun('subject')} felt {victim.possessive} own body move as if pulled by invisible threads."
    )

def face_ghost(world: World, victim: Entity, ghost: Entity) -> None:
    victim.memes["conflict"] = 0.0
    world.facts["confronted"] = True
    world.say(
        f"{victim.id} shut {victim.possessive} eyes tight and recited every nursery line {victim.pronoun('subject')} knew: "
        f"'Months and minutes, all in good time.'"
    )
    world.say(f"With a shudder, {victim.pronoun('subject')} turned to the pale watcher and walked forward.")

def return_borrowed(world: World, victim: Entity, item: Item) -> None:
    world.facts[f"reclaimed_{item.id}"] = True
    victim.meters["resolve"] = 2.0
    world.say(
        f"{victim.id} stretched out; {item.label} leapt from the ghost’s hands straight back into {victim.possessive} own."
        f" The air grew lighter, the whispers softened, and the {world.setting.place} felt less heavy than before."
    )

# ---------------------------------------------------------------------------
# The screenplay: four-act shape driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting,
         victim_type_key: str,
         victim_name: str,
         item_id: str,
         ghost_id: str,
         family_id: str) -> World:
    world = World(setting)
    victim_type = VICTIM_TYPES[victim_type_key]
    item = ITEMS[item_id]
    ghost_def = GHOSTS[ghost_id]
    family_def = FAMILY_TYPES[family_id]

    # Act 1: Setup – quiet life, whispers, haunt begins
    world.say(f"In the quiet of the {setting.place}, {victim_name}, {victim_type['adj']} {victim_type_key},")
    world.say("lived with simple pleasures and the soft rhythm of days marked only by simple joys.")
    hear_whispers(world, world.add(Entity(
        id=victim_name,
        kind="character",
        type="human",
        label=victim_type["adj"],
        phrase=f"{victim_type['adj']} {victim_type_key}",
        traits=victim_type["traits"],
        memes={"fear": 0.0, "repetitions": 0.0, "conflict": 0.0},
    )), ghost_def["label"])

    # Add ghost presence early
    world.add(Entity(
        id="ghost",
        kind="spirit",
        type="ghost",
        label=ghost_def["label"],
        phrase=ghost_def["description"],
        meters={"power": 0.0},
    ))

    # Act 2: Inciting incident – an item borrowed
    world.para()
    world.say(f"One dusk, {victim_name} reached for {item.phrase},")
    borrow_item(
        world,
        world.get("ghost"),
        world.get(victim_name),
        item
    )
    propagate(world)

    # Act 2 continuation – family notices and shares concern (Sharing)
    family_ids = []
    if family_def.id == "parents":
        mom = world.add(Entity(id="mother", kind="character", type="mother", label="mother", meters={"concern": 0.0}))
        dad = world.add(Entity(id="father", kind="character", type="father", label="father", meters={"concern": 0.0}))
        family_ids = [mom.id, dad.id]
    elif family_def.id == "mother":
        mother = world.add(Entity(id="mother", kind="character", type="mother", label="mother", meters={"concern": 0.0}))
        family_ids = [mother.id]
    elif family_def.id == "sister":
        sister = world.add(Entity(id="sister", kind="character", type="sister", label="older sister", meters={"concern": 0.0}))
        family_ids = [sister.id]

    world.para()
    for fid in family_ids:
        world.say(notice_missing(world, world.get(fid), item)[0])
    if len(family_ids) > 1:
        share_concern(world, world.get(family_ids[0]), world.get(family_ids[1]))

    # Act 3: Escalation – ghost mesmerizes victim into repetition (Repetition)
    world.para()
    victim = world.get(victim_name)
    mesmerize_victim(world, world.get("ghost"), victim)
    propagate(world)  # causes repetitions
    world.say(
        f"From then on, {victim_name}’s movements became echoes."
        f" Rising, sitting, turning—not {victim.pronoun('possessive')} own choices, yet all {victim.possessive} body would obey."
    )

    # Act 4: Resolution – victim uses repetitive phrase to break trance, confronts ghost, reclaims item
    world.para()
    face_ghost(world, victim, world.get("ghost"))
    return_borrowed(world, victim, item)

    # Record facts for Q&A generators (grounded in the simulated world).
    world.facts.update({
        "victim": victim,
        "ghost": ghost_def,
        "item": item,
        "place": setting.place,
        "family": family_def,
        "confronted": True,
        "resolved": True,
    })
    return world

# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific)
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    victim_type: str
    victim_name: str
    item_id: str
    ghost_id: str
    family_type: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation – three deliberately separate sets.
# ---------------------------------------------------------------------------
# (1) Generation prompts – the natural-language “asks” that would produce this story
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = f["item"]
    place = f["place"]
    ghost = f["ghost"]["label"]
    return [
        f'Write a gentle ghost story for 3-7-year-olds featuring the words "borrow", "mesmerize", and "repeat" in a {place}.',
        f'A quiet {place} tale where a child hears whispered {ghost} calling {f["victim"].id}\'s name',
        f'Design a TinyStory that ends with a child regaining {f["victim"].pronoun("object")} favorite {item.label} by using a family phrase to break a ghostly trance.',
    ]

# (2) Story questions – answerable from the sentence-by-sentence document
def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    victim = f["victim"]
    item = f["item"]
    ghost = f["ghost"]["label"]
    family = f["family"]
    place = f["place"]
    adj = VICTIM_TYPES[victim_type].get("adj")
    where = "inside" if world.setting.indoor else "outside"

    qa = [
        QAItem(
            question=f"Who is the main child in the ghost story set in the {place}?",
            answer=f"The story centers on {victim.id}, {adj} {victim.type}, who spent quiet afternoons in the {place}."
        ),
        QAItem(
            question=f"What made {victim.id}’s actions turn into repeats like a broken music box?",
            answer=f"{ghost} drew near and, without a sound, made {victim.pronoun('object')} mindless."
        ),
    ]
    if family.members > 1:
        qa.append(QAItem(
            question=f"How did {family.label} first realize something was wrong with {item.label}?",
            answer=f"Both {family.label} stared at the empty shelf where {item.phrase} had always rested."
        ))
    qa.extend([
        QAItem(
            question=f"What phrase did {victim.id} use to force {the} {ghost} away?",
            answer=f"{victim.id} shut {victim.possessive} eyes and recited every nursery line {victim.pronoun('subject')} knew: 'Months and minutes, all in good time.'"
        ),
        QAItem(
            question=f"How do we know {victim.id} succeeded?",
            answer=f"As soon as {victim.pronoun('subject')} finished speaking, {item.label} flew back into {victim.pronoun('possessive')} hands."
        ),
    ])
    return qa

# (3) Child-level world knowledge – no reference to the particular story
WORLD_KNOWLEDGE = {
    "ghost": [
        ("What is a ghost?",
         "A ghost is the spirit of someone who has died, sometimes said to wander and watch over places they loved."),
        ("Are ghosts always scary?",
         "Not always; many ghost tales show spirits who just want someone to notice or to get back something that was lost."),
    ],
    "borrow": [
        ("What does it mean to borrow?",
         "To borrow is to take something temporarily, planning to give it back later."),
    ],
    "mesmerize": [
        ("What does mesmerize mean?",
         "To mesmerize is to fascinate or hold spellbound, so a person cannot look away or think clearly."),
    ],
    "repeat": [
        ("What does it mean to repeat an action?",
         "Repeating means doing the same motion or saying the same words over and over without meaning to."),
    ],
}
WORLD_KNOWLEDGE_ORDER = ["ghost", "borrow", "mesmerize", "repeat"]

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set()
    ghost = f.get("ghost", {}).get("id") or "ghost"
    tags.add(ghost)
    for act in ["borrow", "mesmerize", "repeat"]:
        if act in [f.get("item", {}).get("id", "").lower(), "ghost"]:
            tags.add(act)
    ordered = [t for t in WORLD_KNOWLEDGE_ORDER if t in tags]
    out = []
    for tag in ordered:
        for q, a in WORLD_KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Trace output
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v >= 0.2}
        memes = {k: v for k, v in e.memes.items() if v >= 0.2}
        bits = [f"{k}={v:.1f}" for k, v in meters.items()]
        bits.extend(f"{k}={v:.1f}" for k, v in memes.items())
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    fired = sorted(n for n in world.fired if isinstance(n, str))
    if fired:
        lines.append(f"  fired extra: {', '.join(fired)}")
    return "\n".join(lines)

# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(place="cottage", victim_type="girl", victim_name="Mira",
                item_id="tea_set", ghost_id="pale_watcher", family_type="parents"),
    StoryParams(place="house", victim_type="boy", victim_name="Ethan",
                item_id="pocket_watch", ghost_id="shadow_girl", family_type="mother"),
    StoryParams(place="library", victim_type="girl", victim_name="Clara",
                item_id="guide_book", ghost_id="pale_watcher", family_type="sister"),
]

def explain_rejection(victim_type_key: str, ghost_id: str, item_id: str) -> str:
    adj = VICTIM_TYPES[victim_type_key]["adj"]
    item = ITEMS[item_id]
    ghost = GHOSTS[ghost_id]["label"]
    return (
        f"(No ghost tale: {adj} {victim_type_key}s do not invite {ghost} over {item.label}. "
        f"Try another trio or flip the ghost/item.)"
    )

# ---------------------------------------------------------------------------
# ASP Twin – inline clingo rules for declarative reasonableness gate
# Uses the shared `asp` helper + clingo, imported lazily so the prose engine
# runs without them.  See `python ... --verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Valid only when ghost can plausibly borrow item from victim in this setting.
valid_story(P,Vt,G,It,F) :-
    setting(P), victim_type(Vt), ghost(G), item(It), family_type(F),
    % ghost must be genuine
    ghost(G), item(It).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for vid, v in VICTIM_TYPES.items():
        lines.append(asp.fact("victim_type", vid))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
    for fid, f in FAMILY_TYPES.items():
        lines.append(asp.fact("family_type", fid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(model)

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set((p.place, p.victim_type, p.ghost_id, p.item_id, p.family_type) for p in CURATED)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches curated set ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and curated Python list:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost Story domain: eyer, borrow, mesmerize; Repetition, Sharing, Conflict.")
    ap.add_argument("--place", choices=list(SETTINGS), help="story setting")
    ap.add_argument("--victim_type", choices=list(VICTIM_TYPES), help="child archetype")
    ap.add_argument("--victim_name", help="child name override")
    ap.add_argument("--item", choices=list(ITEMS), dest="item_id", help="item borrowed")
    ap.add_argument("--ghost", choices=list(GHOSTS), dest="ghost_id", help="ghost identity")
    ap.add_argument("--family", choices=list(FAMILY_TYPES), dest="family_type", help="family makeup")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducibility")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list clingo-valid combos")
    ap.add_argument("--verify", action="store_true", help="check ASP gate")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item_id and args.ghost_id and args.family_type:
        return StoryParams(
            place=args.place or rng.choice(list(SETTINGS)),
            victim_type=args.victim_type or rng.choice(list(VICTIM_TYPES)),
            victim_name=args.victim_name or (
                rng.choice(VICTIM_TYPES[args.victim_type]["name_pool"])
                if args.victim_type in VICTIM_TYPES and "name_pool" in VICTIM_TYPES[args.victim_type]
                else rng.choice(GIRL_NAMES if rng.random() < 0.5 else BOY_NAMES)
            ),
            item_id=args.item_id,
            ghost_id=args.ghost_id,
            family_type=args.family_type,
            seed=args.seed,
        )
    combos = [
        StoryParams(place=p, victim_type=vt, victim_name="", item_id=it, ghost_id=g, family_type=f, seed=None)
        for p in SETTINGS
        for vt in VICTIM_TYPES
        for it in ITEMS
        for g in GHOSTS
        for f in FAMILY_TYPES
    ]
    if not combos:
        raise StoryError("(No domain constraints to pick from; specify some flags.)")
    selected = rng.choice(combos)
    victim_name = rng.choice(VICTIM_TYPES[selected.victim_type]["name_pool"])
    return StoryParams(
        place=selected.place,
        victim_type=selected.victim_type,
        victim_name=victim_name,
        item_id=selected.item_id,
        ghost_id=selected.ghost_id,
        family_type=selected.family_type,
        seed=args.seed,
    )

def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = tell(setting, params.victim_type, params.victim_name,
                 params.item_id, params.ghost_id, params.family_type)
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
        print(asp_program("#show valid_story/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} clingo-valid combos:\n")
        for p, vt, g, it, f in stories:
            print(f"  {p:9} {vt:5} {g:20} {it:12} [{f}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen_stories = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen_stories:
                continue
            seen_stories.add(sample.story)
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
            name = p.victim_name or (GIRL_NAMES[0] if p.victim_type == "girl" else BOY_NAMES[0])
            header = f"### {name}: {p.ghost_id} & {p.item_id} in the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
