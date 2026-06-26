#!/usr/bin/env python3
"""
storyworlds/worlds/naughty_pile_inner_monologue_sound_effects_sharing.py
========================================================================

A tall‑tale storyworld about a child who builds a twig fort, knocks it down
naughtily, and learns to share the work of rebuilding.  The story includes
inner monologue (italicised thoughts), sound effects (onomatopoeia embedded
in the prose), and a sharing resolution.

Seed words: naughty, pile
Features : Inner Monologue, Sound Effects, Sharing
Style    : Tall Tale (exaggerated, larger‑than‑life descriptions)
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

MESS_KINDS = {"twiggy", "muddy", "leafy", "crumbly"}

REGIONS = {"feet", "legs", "torso"}


# ---------------------------------------------------------------------------
# Entity
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        override = {"mother": "mom", "father": "dad", "aunt": "auntie", "uncle": "uncle"}
        return override.get(self.type, self.type)

    @property
    def tall_adjective(self) -> str:
        """Tall‑tale exaggeration: one of a set of larger‑than‑life descriptors."""
        opts = {
            "feet": ("a giant’s", "mountain-sized"),
            "legs": ("heavy as a boulder", "knee-high"),
            "torso": ("like a bear’s", "broad as a door"),
        }
        return ""  # used inline during prose; not a stored property.


@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    sound: str
    inner_thought: str
    mess: str
    soil: str
    zone: set[str]
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    # Tall‑tale metaphors
    tall_builder: str = "a fort made of twigs as tall as a giant"
    tall_crash: str = "the whole pile came down with a roar like a bear"
    tall_share: str = "they worked together like a team of oxen"


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.inner_thoughts: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        # Insert inner‑monologue italic blocks after the paragraph that contains
        # the act boundary.  (Simplified: we attach them after the last line.)
        final = []
        for p in self.paragraphs:
            block = " ".join(p)
            if block:
                final.append(block)
        # Append any recorded inner thoughts as a separate italic line.
        for thought in self.inner_thoughts:
            if thought:
                final.append(f"*{thought}*")
        return "\n\n".join(final)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone

    def think(self, text: str) -> None:
        self.inner_thoughts.append(text)


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="soil", tag="physical", apply=_r_soil),
    Rule(name="workload", tag="physical", apply=_r_workload),
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
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Tall‑tale prose helpers
# ---------------------------------------------------------------------------
TALL_EXAGGERATIONS = {
    "fort": "towered like a mountain",
    "crash": "echoed like thunder through the valley",
    "child": "could lift a wagon with one hand",
    "parent": "had arms as strong as oak branches",
    "sharing": "moved like a team of bears",
    "sound": "CRRRUNCH!  WHOOMPH!  TING-TING-TING",
}

SOUND_EFFECTS = {
    "snap": "SNAP!",
    "crunch": "CRRRUNCH!",
    "whistle": "WHEEE!",
    "crash": "KABOOM!",
    "fizzle": "psssshhh",
    "thump": "THUMP!",
}


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Finn", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "father") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["wild", "big-dreaming"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # ACT 1 – Introduce the hero and the pile.
    world.say(f"In a place where the wind whispered through tall grass, "
              f"there lived a {hero_type} named {hero_name}. {hero_name} was "
              f"a {', '.join(hero_traits)} child who dreamed of building "
              f"{activity.tall_builder}.")
    world.think(f"I will make the biggest fort the world has ever seen! "
                f"A pile that reaches the clouds!")
    world.para()

    # Use a sound effect to show enthusiasm.
    world.say(f"Every morning, {hero_name} ran outside. {SOUND_EFFECTS['whistle']} "
              f"The twigs snapped as {hero.pronoun()} gathered them.")

    world.say(
        f"One day, {hero_name}'s {parent.label_word} brought "
        f"{hero.pronoun('object')} {prize.phrase}. {hero_name} put "
        f"{prize.it()} on at once, {prize.label} as bright as new pennies."
    )

    # ACT 2 – conflict: the naughty pile.
    world.para()
    world.say(f"{hero_name} and {hero.pronoun('possessive')} {parent.label_word} "
              f"went to {setting.place}. The pile of twigs sat there, "
              f"waiting. A naughty idea tickled {hero.pronoun('possessive')} toes.")
    world.say(f"{hero_name} wanted to {activity.verb}, but "
              f"{hero.pronoun('possessive')} {parent.label_word} said, "
              f"\"Wait – that {prize.label} will get {activity.soil}.\"")

    # Predict and warn.
    from copy import deepcopy as _deepcopy
    sim = world.copy()
    # Simulate the activity on the copy.
    sim.entities[hero.id].meters[activity.mess] += 1
    # (We won't check prize dirtiness in detail; just proceed.)
    world.say(
        f"\"You'll get your {prize.label} {activity.soil}, and then we'll have "
        f"to clean {prize.it()},\" {hero.pronoun('possessive')} {parent.label_word} said."
    )

    world.say(
        f"But {hero_name} {activity.rush} with a {SOUND_EFFECTS['snap']}, and "
        f"{hero.pronoun()} knocked the pile. {activity.tall_crash}!"
    )
    world.think(f"Uh‑oh. The pile is everywhere. And my {prize.label} is "
                f"all {activity.mess}.")
    world.para()

    # ACT 3 – sharing resolution.
    world.say(f"{hero_name} looked at the scattered twigs. "
              f"{hero.pronoun('possessive').capitalize()} {parent.label_word} "
              f"kneeled down. \"Let's {activity.gerund} together! "
              f"Sharing the work makes it fun.\"")
    world.say(f"{hero_name} nodded. {SOUND_EFFECTS['crunch']} went the twigs "
              f"as they both gathered them.")
    world.say(
        f"They {activity.tall_share}. When the pile was rebuilt, "
        f"{hero_name}'s {prize.label} was clean, and "
        f"{hero.pronoun('possessive')} {parent.label_word} laughed."
    )

    # Record facts.
    world.facts.update(hero=hero, parent=parent, prize=prize,
                       prize_cfg=prize_cfg, activity=activity,
                       setting=setting, conflict=True, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False,
                        affords={"fort"}),
    "garden":  Setting(place="the garden", indoor=False,
                       affords={"fort", "mud"}),
    "playroom":Setting(place="the playroom", indoor=True, affords={"building"}),
}

ACTIVITIES = {
    "fort": Activity(
        id="fort",
        verb="jump into the pile of twigs",
        gerund="gathering twigs",
        rush="rushed at the pile",
        sound="CRRACKLE!",
        inner_thought="A fort this big must be knocked down at least once!",
        mess="twiggy",
        soil="all twiggy and dusty",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="pile",
        tags={"twig", "pile", "naughty"},
        tall_builder="a fort made of twigs as tall as a giant",
        tall_crash="the whole pile came down with a roar like a bear",
        tall_share="worked together like a team of oxen",
    ),
    "mud": Activity(
        id="mud",
        verb="stomp in the mud pile",
        gerund="squishing mud",
        rush="ran towards the mud",
        sound="SQUELCH!",
        inner_thought="Mud is the best thing on earth!",
        mess="muddy",
        soil="all muddy",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="pile",
        tags={"mud", "pile", "naughty"},
        tall_builder="a mountain of mud",
        tall_crash="the mud splattered like a volcano",
        tall_share="squished mud side by side",
    ),
    "building": Activity(
        id="building",
        verb="knock down the block pile",
        gerund="stacking blocks",
        rush="charged the tower of blocks",
        sound="CLATTER!",
        inner_thought="Down it goes!",
        mess="crumbly",
        soil="covered in block dust",
        zone={"torso"},
        weather="",
        keyword="pile",
        tags={"block", "pile", "naughty"},
        tall_builder="a tower of blocks that touched the ceiling",
        tall_crash="the blocks rained down like hail",
        tall_share="stacked the blocks together in no time",
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a bright red shirt",
        type="shirt",
        region="torso",
    ),
    "shoes": Prize(
        label="shoes",
        phrase="new blue shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "pants": Prize(
        label="pants",
        phrase="clean white pants",
        type="pants",
        region="legs",
        plural=True,
    ),
}

GEAR = [
    Gear(id="playclothes", label="old play clothes",
         covers={"feet", "legs", "torso"},
         guards={"twiggy", "muddy", "crumbly"},
         prep="put on your old play clothes",
         tail="went to put on their old play clothes",
         plural=True),
    Gear(id="boots", label="rain boots",
         covers={"feet"},
         guards={"twiggy", "muddy"},
         prep="put on your rain boots",
         tail="walked back to put on their rain boots",
         plural=True),
]

GIRL_NAMES = ["Maya", "Lily", "Nina", "Rosa", "Aria"]
BOY_NAMES = ["Finn", "Leo", "Milo", "Jack", "Theo"]
TRAITS = ["wild", "curious", "stubborn", "imaginative", "brave"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pile": [
        ("What is a pile?",
         "A pile is a heap of things, like twigs or blocks or mud, "
         "that are stacked together."),
    ],
    "twig": [
        ("What is a twig?",
         "A twig is a small, thin branch that falls from a tree. "
         "It can be used to build little forts."),
    ],
    "mud": [
        ("What is mud?",
         "Mud is wet, squishy earth. It feels cool and soft, "
         "and it sticks to your fingers and clothes."),
    ],
    "naughty": [
        ("What does 'naughty' mean?",
         "'Naughty' is when someone does something they know they "
         "shouldn't do, like knocking over a pile on purpose."),
    ],
    "sharing": [
        ("Why is sharing good?",
         "Sharing is good because it makes work faster and more fun. "
         "When you share, everyone helps and nobody feels left out."),
    ],
    "fort": [
        ("What is a fort?",
         "A fort is a strong shelter you can build with sticks, "
         "blocks, or blankets. People play inside forts."),
    ],
}
KNOWLEDGE_ORDER = ["pile", "twig", "mud", "naughty", "sharing", "fort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    kw = act.keyword or act.mess
    return [
        f'Write a tall tale for a 3-to-5-year-old that includes the word "{kw}" '
        f'and teaches about sharing.',
        f'Tell a story where a {hero.type} named {hero.id} learns to share '
        f"after being naughty with a {kw}.",
        f'Include sound effects and inner thoughts in a story about a child '
        f'and a pile of {kw}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a {trait} {hero.type} named {hero.id} and "
                   f"{pos} {pw}. They go to {place} and {act.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{hero.id} loved to {act.verb} and build {act.tall_builder}.",
        ),
        QAItem(
            question=f"What new {prize.label} did {hero.id}'s {pw} give "
                     f"{obj}?",
            answer=f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. "
                   f"{hero.id} wore {prize.it()} proudly.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {hero.id} knock down the pile?",
            answer=f"{hero.id} felt a naughty urge and {act.rush}. "
                   f"{act.tall_crash} happened. {hero.pronoun('possessive').capitalize()} "
                   f"{prize.label} got {act.soil}.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did {hero.id} and {pos} {pw} fix the mess?",
            answer=f"They shared the work. {sub.capitalize()} and {pos} {pw} "
                   f"{act.tall_share}. The {prize.label} was clean again.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World‑knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  inner thoughts: {world.inner_thoughts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M),
                   covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
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
        description="Tall‑tale storyworld: a naughty pile, inner monologue, "
                    "sound effects, and sharing. Unspecified choices are random.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(f"(No story: the {pr.label} is not a body part "
                             f"splashed by {act.gerund}, or no gear covers it.)")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: a {prize.label} is not typical for that gender.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="backyard", activity="fort", prize="shirt",
                    name="Finn", gender="boy", parent="father", trait="wild"),
            StoryParams(place="garden", activity="mud", prize="pants",
                    name="Maya", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="playroom", activity="building", prize="shoes",
                    name="Leo", gender="boy", parent="aunt", trait="brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
