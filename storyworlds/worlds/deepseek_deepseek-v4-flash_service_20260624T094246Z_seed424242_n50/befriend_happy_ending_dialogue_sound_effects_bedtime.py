#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/befriend_happy_ending_dialogue_sound_effects_bedtime.py

A standalone story world sketch for a "befriend" bedtime story with dialogue,
sound effects, and a happy ending.
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
MESS_KINDS = {"shy", "lonely"}  # emotional "mess" kinds that can be washed away
REGIONS = {"heart", "mind"}     # metaphorical regions

# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "character"
    type: str = "child"          # child, parent, friend
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "friend": "new friend"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str            # emotional mess (shy, lonely)
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    sound_effect: str = ""   # e.g. "whoosh", "tap tap tap"


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
    """Social 'gear' that helps overcome loneliness/shyness."""
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spread_shyness(world: World) -> list[str]:
    """When a child's shyness is high, they avoid the other child."""
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("shy", 0) >= THRESHOLD and not actor.memes.get("befriended", 0):
            sig = ("shy", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            # The other child becomes lonely if not approached
            for other in world.characters():
                if other.id != actor.id and other.memes.get("befriended", 0) == 0:
                    other.meters["lonely"] += 0.5
                    out.append(f"{actor.id} felt too shy to say hello. {other.id} looked away.")
    return out


def _r_friendship_grows(world: World) -> list[str]:
    """If one child overcomes shyness, the other's loneliness fades."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("befriended", 0) >= THRESHOLD:
            for other in world.characters():
                if other.id != actor.id and other.meters.get("lonely", 0) > 0:
                    sig = ("friend", other.id, actor.id)
                    if sig in world.fired:
                        continue
                    world.fired.add(sig)
                    other.meters["lonely"] = max(0.0, other.meters["lonely"] - 1.0)
                    out.append(f"{other.id} smiled back. The loneliness melted away.")
    return out


CAUSAL_RULES = [
    Rule(name="spread_shyness", tag="social", apply=_r_spread_shyness),
    Rule(name="friendship_grows", tag="social", apply=_r_friendship_grows),
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
                produced.extend(s for s in sents)
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


# ---------------------------------------------------------------------------
# Prediction (simulate forward to see if social gear works)
# ---------------------------------------------------------------------------
def predict_friendship(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "befriended": any(e.memes.get("befriended", 0) >= THRESHOLD for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return f"The {activity.sound_effect} made everything feel like a game."


def setting_detail(setting: Setting, activity: Activity) -> str:
    base = f"{setting.place.capitalize()} was full of warm light."
    if activity.sound_effect:
        base += f" The air whispered with a soft '{activity.sound_effect}'."
    return base


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved to explore the world.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["playful"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {parent.label_word} gave {hero.id} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["happy"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} hugged {prize.it()} close and carried it everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One sunny morning" if world.weather == "sunny" else "One quiet afternoon"
    world.say(f"{day}, {hero.id} and {pronoun_possessive(hero)} {parent.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def sees_other(world: World, hero: Entity, other: Entity) -> None:
    world.say(f"There, {hero.id} saw {other.id}, a {other.type} about the same age, playing alone.")
    # Sound effect
    if world.setting.place == "park":
        world.say("A whoosh of wind rustled the leaves.")
    else:
        world.say("The quiet 'tap tap tap' of feet echoed nearby.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity, other: Entity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb}, but a knot of shyness grew in {pronoun_possessive(hero)} tummy.")
    hero.meters["shy"] += 1
    propagate(world)


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    # In this domain, the parent encourages instead of warning
    world.say(f"\"Go on, say hello,\" {parent.label_word} whispered gently. \"You can do it.\"")
    return True  # always a reason to encourage


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["brave"] += 1
    world.say(f"{hero.id} took a deep breath. A tiny step forward. Then another.")
    # Sound effect
    world.say("The leaves rustled again — 'shhh-whoosh'.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    world.say(f"{parent.label_word} gave {pronoun_possessive(hero)} hand a squeeze.")
    world.say("\"You're ready,\" {parent.label_word} said. \"Just be yourself.\"")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"But {hero.id} still felt the shyness buzzing like a little bee.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if not predict_friendship(world, hero, activity, prize.id)["befriended"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.label_word} said, \"How about we {gear_def.prep} and then try together?\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["befriended"] += 2
    world.say(f"{hero.id} nodded and smiled. {pronoun_possessive(hero)} shyness faded like mist in the sun.")
    world.say(f"\"Hi!\" {hero.id} said, holding out {prize.label}.")
    world.say(f"The other child looked up and smiled back. \"Hi!\"")
    world.say(f"They played together. {activity_delight(activity)}")
    world.say(f"The sound of laughter mixed with the '{activity.sound_effect}' of the wind.")
    world.say(f"That night, {hero.id} hugged {prize.it()} tight and whispered, \"I made a friend today.\"")
    world.say(f"{parent.label_word} kissed {pronoun_possessive(hero)} forehead. \"That's the best bedtime story of all.\"")
    propagate(world)


# Helper for possessive pronoun string
def pronoun_possessive(entity: Entity) -> str:
    return entity.pronoun("possessive")


# ---------------------------------------------------------------------------
# Main storytelling function
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "sunny" if not setting.indoor else "indoor"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "shy"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    other = world.add(Entity(
        id="Other", kind="character", type="child", label="the other child",
        phrase="a child about the same age", traits=["friendly"],
    ))

    # Act 1 – Setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – Tension
    world.para()
    arrive(world, hero, parent, activity)
    sees_other(world, hero, other)
    wants(world, hero, parent, activity, other)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3 – Resolution (dialogue + sound effects + happy ending)
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)
    else:
        # Fallback happy ending: direct approach
        world.say(f"{hero.id} took a deep breath and walked over. \"Hi, my name is {hero.id}.\"")
        world.say("The other child grinned. They started playing together, and soon they were laughing.")
        world.say("The wind whispered 'whoosh' as if celebrating the new friendship.")
        world.say("That night, {hero.id} fell asleep with a happy smile, knowing tomorrow they'd play again.")
        hero.memes["befriended"] += 2

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       other=other,
                       conflict=hero.memes.get("shy", 0) >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(place="the park", indoor=False, affords={"befriend"}),
    "garden": Setting(place="the garden", indoor=False, affords={"befriend"}),
    "playground": Setting(place="the playground", indoor=False, affords={"befriend"}),
}

ACTIVITIES = {
    "befriend": Activity(
        id="befriend",
        verb="say hello and make a friend",
        gerund="making new friends",
        rush="step forward awkwardly",
        mess="shy",
        soil="shy and lonely",
        zone={"heart"},
        weather="sunny",
        keyword="friend",
        tags={"friend", "shy"},
        sound_effect="whoosh",
    ),
}

PRIZES = {
    "toy": Prize(
        label="toy",
        phrase="a shiny red toy car",
        type="toy",
        region="heart",
        genders={"girl", "boy"},
    ),
    "ball": Prize(
        label="ball",
        phrase="a bouncy blue ball",
        type="ball",
        region="heart",
        genders={"girl", "boy"},
    ),
    "book": Prize(
        label="book",
        phrase="a book about dragons",
        type="book",
        region="heart",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="smile",
        label="a warm smile",
        covers={"heart"},
        guards={"shy", "lonely"},
        prep="offer a smile and say hello",
        tail="smiled and waved from afar",
    ),
    Gear(
        id="hello",
        label="a friendly hello",
        covers={"heart"},
        guards={"shy", "lonely"},
        prep="say hello and ask their name",
        tail="said hello and asked to play",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["shy", "curious", "stubborn", "cheerful", "spirited", "lively"]


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
    "friend": [
        ("What is a friend?",
         "A friend is someone you like to play with, talk to, and share things with."),
    ],
    "shy": [
        ("Why do people feel shy?",
         "Shy is when you feel worried or nervous about meeting someone new. It goes away when you get to know them."),
    ],
    "play": [
        ("Why is playing with others fun?",
         "Playing with others is fun because you can laugh, share toys, and make happy memories together."),
    ],
}
KNOWLEDGE_ORDER = ["friend", "shy", "play"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword
    return [
        f'Write a short bedtime story for a 3-to-5-year-old about a child who overcomes shyness and makes a new friend, using the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} goes to {world.setting.place} with {pronoun_possessive(hero)} {parent.label_word} and learns to say hello.",
        f"Write a simple story that ends with a happy friendship, includes a sound effect like '{act.sound_effect}', and has a child speaking to a new friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    other = f["other"]
    place = world.setting.place
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), pronoun_possessive(hero))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    return [
        QAItem(
            question=f"Who is the bedtime story about?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} who goes to {place} with {pos} {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} learn to do?",
            answer=f"{hero.id} learned to say hello and make a new friend. {pronoun_possessive(hero)} shyness went away when {sub} smiled.",
        ),
        QAItem(
            question=f"How did the story sound?",
            answer=f"The story had a 'whoosh' sound from the wind, and the children laughed and talked. At the end, everyone was happy.",
        ),
        QAItem(
            question=f"What did {hero.id} and {other.id} do together?",
            answer=f"They played together, shared {prize.label}, and became friends. {hero.id} felt happy and not shy anymore.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
    lines.append("== (3) World knowledge ==")
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
    return "\n".join(lines)


# Curated set (used by --all)
CURATED = [
    StoryParams(place="park", activity="befriend", prize="toy", name="Lily", gender="girl", parent="mother", trait="shy"),
    StoryParams(place="garden", activity="befriend", prize="ball", name="Tim", gender="boy", parent="father", trait="curious"),
    StoryParams(place="playground", activity="befriend", prize="book", name="Zoe", gender="girl", parent="mother", trait="spirited"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return (f"(No story: {activity.gerund} touches the {sorted(activity.zone)}, "
            f"but {noun} sits on the {prize.region}. Try a prize with region in {sorted(activity.zone)}.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't typical for a {gender}; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, shyness, a new friend – bedtime style.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

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
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "shy"], params.parent)
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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
