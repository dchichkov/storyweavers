#!/usr/bin/env python3
"""
storyworlds/worlds/swoon_friendship_detective_story.py
========================================================

A detective‑story domain about a mysterious swoon that threatens a friendship.
Two best friends, one a young detective, must work together to clear a name.
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

# Physical and emotional meters used throughout
METER_KEYS = {"suspicion", "trust", "evidence", "worry", "joy", "loyalty", "faint"}

# -------------------------------------------------------------------------
# Entities
# -------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "detectivefox"}
        male = {"boy", "man", "casey"}
        if self.type.lower() in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type.lower() in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

# -------------------------------------------------------------------------
# Domain parameters
# -------------------------------------------------------------------------
@dataclass
class Setting:
    name: str = "the town park"
    afford_activities: set[str] = field(default_factory=lambda: {"investigate"})

@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Clue:
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"detective", "friend"})

@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False

# -------------------------------------------------------------------------
# World model
# -------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
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
        clone.paragraphs = [[]]
        return clone

# -------------------------------------------------------------------------
# Causal rules
# -------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_swoon_evidence(world: World) -> list[str]:
    """When someone faints, evidence meter increases for the detective."""
    out = []
    for actor in world.characters():
        if actor.meters["faint"] >= THRESHOLD:
            for other in world.characters():
                if other.id != actor.id and "detective" in other.type.lower():
                    sig = ("swoon_evidence", other.id, actor.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        other.meters["evidence"] += 0.5
                        out.append(f"{other.label} noted the time of the swoon.")
    return out

def _r_friend_trust(world: World) -> list[str]:
    """If detective has enough evidence and trust is low, tension builds."""
    out = []
    for det in world.characters():
        if "detective" not in det.type.lower():
            continue
        if det.meters["evidence"] >= THRESHOLD and det.meters["trust"] < THRESHOLD:
            for friend in world.characters():
                if friend.id != det.id and "friend" in friend.type.lower():
                    sig = ("trust_break", det.id, friend.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        det.memes["worry"] += 1
                        out.append(f"{det.label} started to worry about {friend.label}.")
    return out

CAUSAL_RULES = [
    Rule("swoon", "physical", _r_swoon_evidence),
    Rule("trust", "social", _r_friend_trust),
]

def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# -------------------------------------------------------------------------
# Detective story beats
# -------------------------------------------------------------------------
def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} was a clever {hero.type} who solved small mysteries. "
        f"{hero.pronoun('possessive')} best friend {friend.id} "
        f"was always by {hero.pronoun('possessive')} side. "
        "Together they explored every corner of their town."
    )

def friendship_bond(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} shared everything: snacks, secrets, "
        "and a purple friendship bracelet that never came off."
    )

def mysterious_swoon(world: World, victim: Entity, activity: Activity) -> None:
    world.say(
        f"One afternoon, while {activity.gerund} in {world.setting.name}, "
        f"{victim.id} suddenly let out a soft gasp and swooned—"
        "fainted right onto the soft grass."
    )
    victim.meters["faint"] += 1
    propagate(world, narrate=True)

def suspicion_arises(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} hurried to the scene. '{friend.id}, did you see anything?' "
        f"But {friend.id} was quiet and avoided {hero.pronoun('possessive')} eyes."
    )
    hero.meters["suspicion"] += 1
    hero.meters["trust"] -= 0.5
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {clue.label} "
        f"({clue.phrase}) fell out of {friend.pronoun('possessive')} pocket. "
        "Now the whole park was whispering: was the best friend responsible?"
    )

def detective_work(world: World, hero: Entity, activity: Activity, gear: Gear) -> None:
    world.say(
        f"{hero.id} took out {gear.label} and began to investigate. "
        f"'{activity.verb} is what I do best,' {hero.pronoun()} murmured."
    )
    hero.meters["evidence"] += 1

def find_truth(world: World, hero: Entity, victim: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} checked {victim.pronoun('possessive')} bag and found "
        "a note about a bee sting allergy. The swoon was an allergic reaction, "
        "not anything {friend.id} did!"
    )
    hero.meters["trust"] += 2
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    friend.meters["suspicion"] = 0.0

def reconciliation(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"'{friend.id}, I'm sorry I doubted you,' {hero.id} said."
    )
    friend.memes["loyalty"] += 1
    world.say(
        f"{friend.id} smiled and hugged {hero.pronoun('object')}. "
        "'A real detective always finds the truth—and a true friend never leaves.' "
        "They walked home together, the bracelet shining in the afternoon light."
    )

# -------------------------------------------------------------------------
# Registry data
# -------------------------------------------------------------------------
SETTINGS = {
    "park": Setting("the town park", {"investigate"}),
    "library": Setting("the quiet library", {"investigate"}),
    "playground": Setting("the school playground", {"investigate"}),
}

ACTIVITIES = {
    "investigate": Activity(
        "investigate",
        "solve the mystery",
        "solving mysteries",
        "question everyone",
        "curious",
        "full of clues",
        {"sight", "sound"},
        keyword="mystery",
        tags={"mystery", "clue", "swoon"},
    ),
}

CLUES = {
    "bracelet": Clue("friendship bracelet", "a purple friendship bracelet", "wrist"),
    "notebook": Clue("notebook", "a small notebook with scribbles", "pocket"),
    "magnifier": Clue("magnifying glass", "a shiny magnifying glass", "hand"),
}

GEAR = [
    Gear("notebook", "notebook", {"pocket"}, {"curious"},
         "open my notebook and write down clues",
         "wrote the facts in his notebook"),
    Gear("magnifier", "magnifying glass", {"hand"}, {"curious"},
         "take out my magnifying glass and look closely",
         "examined the ground with the magnifying glass"),
]

# Characters
DETECTIVE_NAMES = ["Fox", "Mia", "Rex", "Ava"]
FRIEND_NAMES = ["Casey", "Liam", "Nina", "Zara"]
VICTIM_NAMES = ["Jules", "Riley", "Sam", "Quinn"]

def valid_combos():
    """All valid detective/friend/victim/clue combos (simple: one activity)."""
    combos = []
    for set_name in SETTINGS:
        for clue_id in CLUES:
            # Always possible: one activity, multiple gears
            for gear in GEAR:
                combos.append((set_name, clue_id, gear.id))
    return combos

# -------------------------------------------------------------------------
# Story parameters
# -------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    clue: str
    gear: str
    detective_name: str
    friend_name: str
    victim_name: str
    seed: Optional[int] = None

# -------------------------------------------------------------------------
# QA generators
# -------------------------------------------------------------------------
KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "swoon": [("What does it mean to swoon?",
               "To swoon means to faint suddenly, often because of a surprise or illness.")],
    "friendship": [("Why is friendship important?",
                    "Friends help each other, trust each other, and stick together even when things are hard.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues, asks questions, and solves mysteries to find the truth.")],
    "mystery": [("What is a mystery?",
                 "A mystery is something that is unknown or hard to explain, like a strange event that needs solving.")],
}
KNOWLEDGE_ORDER = ["swoon", "friendship", "detective", "mystery"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f.get("detective", Entity("D", type="person"))
    friend = f.get("friend", Entity("F", type="person"))
    return [
        f'Write a short detective story for young children featuring a "swoon" and a strong friendship.',
        f"Tell a story where {hero.id} the detective must prove {friend.id} is innocent after a mysterious fainting.",
        f'Create a gentle mystery that ends with the friends hugging and the truth coming out.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f.get("detective", Entity("D", type="person"))
    friend = f.get("friend", Entity("F", type="person"))
    victim = f.get("victim", Entity("V", type="person"))
    place = world.setting.name
    clue_label = f.get("clue_label", "friendship bracelet")
    gear_label = f.get("gear_label", "notebook")

    qa = [
        QAItem(
            f"Who are the two best friends in the story?",
            f"The two best friends are {hero.id}, a young detective, and {friend.id}."
        ),
        QAItem(
            f"What happened to {victim.id} in {place}?",
            f"{victim.id} suddenly swooned – fainted – while playing in {place}."
        ),
        QAItem(
            f"Why did people start to suspect {friend.id}?",
            f"A {clue_label} belonging to {friend.id} was found near the spot, so some thought {friend.pronoun('subject')} might be guilty."
        ),
        QAItem(
            f"How did {hero.id} prove {friend.id} was innocent?",
            f"{hero.id} used {gear_label} to investigate and found that {victim.id} had a bee sting allergy – the swoon was an accident, not anyone's fault."
        ),
        QAItem(
            f"How did the story end?",
            f"{hero.id} apologized, the friends hugged, and they walked home together, their friendship even stronger."
        ),
    ]
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in world.facts.get("tags", set()):
            for q, a in KNOWLEDGE.get(tag, []):
                out.append(QAItem(q, a))
    return out

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

# -------------------------------------------------------------------------
# Tell the story
# -------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, clue_cfg: Clue, gear_cfg: Gear,
         det_name: str, friend_name: str, victim_name: str) -> World:
    world = World(setting)

    detective = world.add(Entity(
        id=det_name, kind="character", type="detectivefox", label=f"the detective {det_name}",
        traits=["clever", "brave"]))
    friend = world.add(Entity(
        id=friend_name, kind="character", type="boy", label=f"the friend {friend_name}",
        traits=["loyal", "kind"]))
    victim = world.add(Entity(
        id=victim_name, kind="character", type="person", label=victim_name,
        traits=["playful"]))

    clue_entity = world.add(Entity(
        id=clue_cfg.label, kind="thing", type="clue",
        label=clue_cfg.label, phrase=clue_cfg.phrase,
        region=clue_cfg.region, plural=clue_cfg.plural))

    gear_entity = world.add(Entity(
        id=gear_cfg.id, kind="gear", type="gear",
        label=gear_cfg.label, protective=False,
        covers=gear_cfg.covers, plural=gear_cfg.plural))

    world.facts["detective"] = detective
    world.facts["friend"] = friend
    world.facts["victim"] = victim
    world.facts["clue_label"] = clue_cfg.label
    world.facts["gear_label"] = gear_cfg.label
    world.facts["tags"] = activity.tags

    # Act 1
    introduce(world, detective, friend)
    friendship_bond(world, detective, friend)

    # Act 2
    world.para()
    mysterious_swoon(world, victim, activity)
    suspicion_arises(world, detective, friend, clue_cfg)
    detective_work(world, detective, activity, gear_cfg)

    # Act 3
    world.para()
    find_truth(world, detective, victim, friend)
    reconciliation(world, detective, friend)

    return world

# -------------------------------------------------------------------------
# CLI / parser
# -------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: a swoon, a friendship, a mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gear", choices=[g.id for g in GEAR])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if args.gear:
        combos = [c for c in combos if c[2] == args.gear]
    if not combos:
        raise StoryError("No valid combination for given options.")
    place, clue_id, gear_id = rng.choice(sorted(combos))
    det = rng.choice(DETECTIVE_NAMES)
    friend = rng.choice(FRIEND_NAMES)
    victim = rng.choice(VICTIM_NAMES)
    return StoryParams(place=place, clue=clue_id, gear=gear_id,
                       detective_name=det, friend_name=friend, victim_name=victim)

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES["investigate"],
                 CLUES[params.clue],
                 next(g for g in GEAR if g.id == params.gear),
                 params.detective_name, params.friend_name, params.victim_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def emit(sample: StorySample, *, trace=False, qa=False, header="") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n--- World model state ---")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            mm = {k: v for k, v in e.memes.items() if v}
            print(f"  {e.id}: meters={dict(m)}, memes={dict(mm)}")
    if qa:
        print()
        print(format_qa(sample))

# -------------------------------------------------------------------------
# ASP twin (simple gate)
# -------------------------------------------------------------------------
ASP_RULES = r"""
% place affords activity, activity has swoon tag
affords(Place, investigate).
swoon_tag(investigate).
valid_story(Place, Clue, Gear) :- affords(Place, _), clue(Clue), gear(Gear).
"""

def asp_facts() -> str:
    lines = []
    for sn in SETTINGS:
        lines.append(f"setting({sn}).")
        lines.append(f"affords({sn}, investigate).")
    for cid in CLUES:
        lines.append(f"clue({cid}).")
    for g in GEAR:
        lines.append(f"gear({g.id}).")
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches Python ({len(python_set)} combos).")
        return 0
    print("MISMATCH")
    print(f"  Python only: {python_set - clingo_set}")
    print(f"  Clingo only: {clingo_set - python_set}")
    return 1

# -------------------------------------------------------------------------
# main
# -------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, clue, gear) combos:")
        for c in combos:
            print(f"  {c[0]:10} {c[1]:10} {c[2]:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        # Use a curated set from valid combos
        rng = random.Random(base_seed)
        for place, clue, gear in rng.sample(sorted(valid_combos()), min(3, len(valid_combos()))):
            params = StoryParams(place=place, clue=clue, gear=gear,
                                 detective_name=rng.choice(DETECTIVE_NAMES),
                                 friend_name=rng.choice(FRIEND_NAMES),
                                 victim_name=rng.choice(VICTIM_NAMES))
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### Story {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
