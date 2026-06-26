#!/usr/bin/env python3
"""
storyworlds/worlds/morphodite_sharing_magic_space_adventure.py
===============================================================

A standalone story world for a morphodite in a space adventure,
learning to share magic safely.

Initial story:
---
On a bright space station, a young morphodite named Zara loved to shimmer and shift.
She could turn her arms into wings and her voice into a galaxy of colors.
Her best friend Kael gave her a glowing crystal that hummed with starlight.
Zara wore it around her neck every day.

One space-day, Zara and Kael were in the observation dome.
Zara wanted to release a burst of magic for everyone to see.
But Kael warned, "If you send too much magic at once, the station's field will flicker."
Zara felt the urge to share her magic anyway.
She tried to let the pulses fly, but Kael grabbed her hand and said,
"We can still share the magic, but we need a diffuser to keep it safe."

Zara pouted. "But I want everyone to feel the magic now!"
Kael smiled. "How about we use the energy diffuser first, and then we release
the pulses together?"

Zara's eyes shone. "Yes! Let's do that."
They put the diffuser on the crystal, and soon soft, safe magic waves
filled the dome. Zara shimmered happily, and Kael laughed beside her.
---

Causal rules:
  share magic (activity)         -> hero.magic++, hero.joy++
  magic burst without diffuser   -> crystal overload -> station flicker (conflict)
  warning ignored                -> hero.defiance++
  friend grabs hand              -> hero.conflict++
  compromise (use diffuser)      -> hero.joy++, conflict=0, safe sharing
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
        female = {"morphodite", "girl", "mother"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "friend": "friend"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:  # noqa: F821 (forward ref)
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
# Setting, Activity, Prize, Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the observation dome"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"morphodite"})


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
# Causal rules
# ---------------------------------------------------------------------------
def _r_magic_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["magic"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id, "magic")
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["overloaded"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} started to glow too brightly.")
    return out


def _r_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["overloaded"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["worry"] += 1
        out.append(f"That would make the station field flicker and worry {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    type("Rule", (), {"name": "magic_soak", "tag": "physical", "apply": _r_magic_soak})(),
    type("Rule", (), {"name": "workload", "tag": "physical", "apply": _r_workload})(),
    type("Rule", (), {"name": "grab_conflict", "tag": "social", "apply": _r_grab_conflict})(),
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["overloaded"] >= THRESHOLD),
        "worry": sum(e.meters["worry"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return "the soft hum of magic made the air feel like a melody"


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place} was quiet, and stars glittered beyond the glass."


# ---------------------------------------------------------------------------
# Scene verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little morphodite who could shimmer and shift.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def buys(world: World, friend: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.id}'s {friend.label_word} gave {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore it every day.")


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(f"One space-day, {hero.id} and {hero.pronoun('possessive')} {friend.label_word} were in {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {friend.label_word} held up a gentle hand.")


def warn(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    clause = f"If you send too much magic at once, the station's field will flicker"
    if pred["worry"] >= THRESHOLD:
        clause += ", and I'll worry about the crystal"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {friend.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the urge to share magic was still tugging hard. {hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, friend: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {friend.label_word} grabbed {hero.pronoun('possessive')} hand and said, \"You can want to {activity.verb}, and we can still choose the safe way.\"")


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. "But I want everyone to feel the magic now!" {hero.pronoun()} said.')


def compromise(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=friend.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f'{hero.pronoun("possessive").capitalize()} {friend.label_word} looked at the {prize.label}, then back at {hero.id}, and smiled. "How about we {gear_def.prep} and {activity.verb} together?"')
    return gear_def


def accept(world: World, friend: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f'{hero.id}\'s eyes shone and {hero.pronoun()} hugged {hero.pronoun("possessive")} {friend.label_word}. "Yes! Let\'s do that!"')
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, the {prize.label} glowing softly, and {friend.label_word} was laughing beside {hero.pronoun('object')}.")


# ---------------------------------------------------------------------------
# Tell
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Zara", hero_type: str = "morphodite",
         hero_traits: Optional[list[str]] = None, friend_type: str = "friend") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["shimmering", "eager"]),
    ))
    friend = world.add(Entity(id="Friend", kind="character", type=friend_type, label="the friend"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=friend.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, friend, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, friend, activity)
    wants(world, hero, friend, activity)
    warn(world, friend, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, friend, hero, activity)

    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, friend, hero, activity, prize)
    if gear_def:
        accept(world, friend, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=friend, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "dome": Setting(place="the observation dome", indoor=True, affords={"magic_burst"}),
    "lab": Setting(place="the energy lab", indoor=True, affords={"magic_burst"}),
}

ACTIVITIES = {
    "magic_burst": Activity(
        id="magic_burst",
        verb="release a burst of magic",
        gerund="releasing bursts of magic",
        rush="let the magic pulses fly",
        mess="magic",
        soil="glowing too brightly",
        zone={"neck", "chest"},
        weather="",
        keyword="magic",
        tags={"magic", "shimmer"},
    ),
}

# Gear: energy diffuser covers neck and chest and guards magic overload
GEAR = [
    Gear(
        id="diffuser",
        label="energy diffuser",
        covers={"neck", "chest"},
        guards={"magic"},
        prep="put the energy diffuser on your crystal first",
        tail="put the diffuser on the crystal",
        plural=False,
    ),
    Gear(
        id="sharing_ring",
        label="sharing ring",
        covers={"neck"},
        guards={"magic"},
        prep="wear the sharing ring around your neck",
        tail="put on the sharing ring",
        plural=False,
    ),
]

PRIZES = {
    "crystal": Prize(
        label="crystal",
        phrase="a glowing crystal that hummed with starlight",
        type="crystal",
        region="neck",
        genders={"morphodite"},
    ),
    "orb": Prize(
        label="orb",
        phrase="a tiny orb of captured starlight",
        type="orb",
        region="neck",
        genders={"morphodite"},
    ),
}

NAMES = ["Zara", "Luna", "Kael", "Nova", "Ryn"]
TRAITS = ["shimmering", "eager", "curious", "gentle", "sparkly"]


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
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str  # we call it friend
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "magic": [("What is a morphodite?",
               "A morphodite is a creature from space that can change its shape and glow with magic."),
              ("Why is it important to share magic safely?",
               "Sharing magic can be beautiful, but too much at once can overload things, so we use tools to keep it safe.")],
    "shimmer": [("What does shimmer mean?",
                 "Shimmer means to shine with a soft, flickering light, like stars.")],
}
KNOWLEDGE_ORDER = ["magic", "shimmer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword
    return [
        f'Write a short story for a young child about a morphodite learning to share magic safely, using the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {friend.label_word} worries about {prize.phrase}, and they find a happy compromise.",
        f'Write a space adventure story that includes a glowing {prize.label} and a safe way to share magic.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = friend.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {place} to {act.verb} with {pos} {prize.label}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. They go to {place}, and {hero.id} is wearing {pos} {prize.label}."
        ),
        QAItem(
            question=f"What did the little {hero.type} love to do in {place} before {pw} worried about {pos} {prize.label}?",
            answer=f"{trait.capitalize()} {hero.id} loved {act.gerund}. That wish became tricky because {pos} {prize.label} could overload."
        ),
        QAItem(
            question=f"What {prize.label} did {hero.id}'s {pw} give to the {trait} {hero.type} before the magic play?",
            answer=f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. {hero.id} loved it and wore it every day."
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "glowing too brightly")
        worry = f.get("predicted_worry", 0)
        why = (f"{pos.capitalize()} {pw} was worried because if {hero.id} went to {act.verb}, {pos} {prize.label} would {soil}")
        why += (f", and then {pw} would worry about the station. " if worry >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} held {pos} hand and reminded {obj} they could still want to {act.verb} while choosing a safer way.")
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} when {trait} {hero.id} wanted to {act.verb}?",
            answer=why
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=f"How did {gear.label} help {trait} {hero.id} {act.verb} without ruining {pos} {prize.label}?",
            answer=f"They agreed to use {gear.label} first, so {hero.id} could {act.verb} safely. The plan let {obj} play while {pos} {prize.label} stayed safe."
        ))
        qa.append(QAItem(
            question=f"How did {trait} {hero.id} feel after {pw} agreed to the {gear_plan} plan for magic?",
            answer=f"{hero.id} felt happy and hugged {pos} {pw} once they agreed. At the end, {sub} was {act.gerund} with {pw} laughing nearby."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q=q, a=a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
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


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="dome", activity="magic_burst", prize="crystal", name="Zara", gender="morphodite", parent="friend", trait="shimmering"),
    StoryParams(place="lab", activity="magic_burst", prize="orb", name="Luna", gender="morphodite", parent="friend", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} affects {sorted(activity.zone)}, but {noun} sits on {prize.region}. Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing protects {noun} ({prize.region}) from {activity.gerund}. The compromise must cover the at-risk item.)")


# ---------------------------------------------------------------------------
# ASP
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
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a morphodite, magic, a compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["morphodite"])
    ap.add_argument("--friend", choices=["friend"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = "morphodite"
    name = args.name or rng.choice(NAMES)
    friend = "friend"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "eager"], params.parent)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
