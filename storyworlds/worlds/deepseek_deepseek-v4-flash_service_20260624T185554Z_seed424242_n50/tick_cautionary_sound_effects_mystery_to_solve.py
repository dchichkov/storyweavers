#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/tick_cautionary_sound_effects_mystery_to_solve.py
====================================================================================================================================

A standalone *story world* sketch for a cautionary myth about a mysterious
ticking sound that leads to a mystery that must be solved.  The story uses
sound effects (tick, whisper, rustle) and has a clear three-act shape:
warning, defiance, and a gear‑backed compromise that lets the child solve
the mystery.

Initial story (used to build a world model):
---
Long ago in the village of Ashwood, children were told: “Never follow the
tick after dusk, or the woods will steal your voice.”  A brave child named
Kael loved his grandfather’s silver whistle.  He wore it everywhere.

One evening the tick grew loud.  Kael wanted to prove he was brave, but
his mother warned, “If you follow the tick, the whisper will silence your
whistle’s song.”  Kael tried to sneak off, but his mother caught his hand.
“Then let’s wear the muffler scarf and go together.  But you must solve
the mystery: the tick is a trapped spirit.  Only its true name can free it.”

Kael and his mother walked into the woods.  Tick … tick … the sound came
from an old oak.  Kael remembered the name his grandfather had whispered –
“Tikani.”  He spoke it softly.  The tick stopped.  A gentle breeze
carried a sigh, and the woods fell silent.  Kael’s whistle still chirped
brightly.

Causal state updates:
---
    do activity                   -> actor.<mess> += 1   (silenced)
                                    actor.joy += 1
    actor silenced + worn item    -> item.<mess>++, item.dirty++   (item loses sound)
    item dirty (silenced)         -> item.caretaker.workload += 1
    warning ignored               -> actor.defiance += 1
    parent grabs defiant child    -> actor.conflict += 1
    gear worn + mystery solved    -> actor.joy/love += 1 ; actor.conflict -> 0
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

# Custom mess kinds for this domain – “silenced” means the item loses its voice.
MESS_KINDS = {"silenced", "dirty"}

# Body regions used for gear coverage.
REGIONS = {"ears", "throat", "torso"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # child, mother, father, elder, whistle, scarf...
    label: str = ""                # short reference
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # where a worn item sits: ears | throat | torso
    protective: bool = False       # gear that doesn't get ruined
    covers: set[str] = field(default_factory=set)   # regions the gear shields
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "elder_woman"}
        male = {"boy", "father", "dad", "elder_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the village of Ashwood"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str            # "follow the ticking sound"
    gerund: str          # "listening to the tick"
    rush: str            # "sneak into the woods"
    mess: str            # "silenced"
    soil: str            # "silent and sad"
    zone: set[str]       # {"torso"} – where the sound steals the voice
    weather: str         # "dusk"
    keyword: str = "tick"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]     # mess kinds it neutralises (here "silenced")
    prep: str            # body of offer
    tail: str            # closing clause
    plural: bool = False
    mystery_clue: str = ""   # extra hint for the mystery


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


def _r_soak(world: World) -> list[str]:
    """Activity mess + worn item in zone & uncovered -> item silenced."""
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
                sig = ("silence", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"The {item.label} grew still and silent – its voice stolen."
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
        out.append(f"To restore it, {carer.label} would need great patience.")
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


CAUSAL_RULES: list[Rule] = [
    Rule(name="silence", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
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
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "follow_tick": "the soft tick… tick… made the air feel full of secrets",
    }.get(activity.id, "it sounded like a puzzle hiding in the dusk")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return "The hearth crackled softly, and the shadows crept along the walls."
    return "The woods stood dark and still, lit only by the last glow of twilight."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} still sang clearly"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"In the village of Ashwood lived {hero.id}, a {desc} who heard every whisper of the wind.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the hushed evenings and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id}'s {parent.label_word} gave {hero.pronoun('object')} "
        f"{prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore "
        f"{prize.it()} like a charm against the dark."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One dusk, as the tick grew louder, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} stood at the edge of the Whispering Woods."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"If you follow the tick, the whisper will silence your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I will have to mend it with a lullaby"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Stay close."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the tick called {hero.pronoun('object')} by a secret name.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} caught "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can be brave, but you need not go alone."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and shook {hero.pronoun("possessive")} head. '
            f'"But I must solve the mystery of the tick!" {hero.pronoun()} said.'
        )


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
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled. '
        f'"Here – wear this {gear_def.label}, and I will come with you. '
        f'But you must listen for the true name of the tick – that is the mystery to solve."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    # The mystery is solved: the child remembers the name.
    mystery_name = gear_def.mystery_clue if gear_def.mystery_clue else "Tikani"
    world.facts["mystery_name"] = mystery_name
    world.say(
        f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} knew the name – "
        f"grandfather had whispered it once: '{mystery_name}'."
    )
    world.say(
        f"Together they walked into the woods. Tick … tick … the sound came from an old oak. "
        f"{hero.pronoun().capitalize()} spoke the name. The tick stopped. "
        f"A gentle breeze carried a sigh, and the woods fell quiet. "
        f"{prize_was_clean(hero, prize)}."
    )
    world.say(
        f"The mystery was solved. {parent.label_word} hugged {hero.pronoun('object')}, "
        f"and the evening settled into a peaceful hush."
    )


# ---------------------------------------------------------------------------
# The screenplay (myth‑style cautionary tale)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Kael", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "dusk"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ashwood": Setting(place="the village of Ashwood", indoor=False, affords={"follow_tick"}),
}

ACTIVITIES = {
    "follow_tick": Activity(
        id="follow_tick",
        verb="follow the ticking sound",
        gerund="listening to the tick",
        rush="sneak into the Whispering Woods",
        mess="silenced",
        soil="silent and sad",
        zone={"torso"},
        weather="dusk",
        keyword="tick",
        tags={"tick", "whisper", "mystery"},
    ),
}

GEAR = [
    Gear(
        id="muffler_scarf",
        label="muffler scarf",
        covers={"torso"},
        guards={"silenced"},
        prep="put on the muffler scarf",
        tail="wrapped the muffler scarf around the whistle",
        mystery_clue="Tikani",
    ),
    Gear(
        id="silence_cloak",
        label="cloak of silence",
        covers={"torso", "ears"},
        guards={"silenced"},
        prep="wear the cloak of silence",
        tail="draped the cloak of silence over their shoulders",
        mystery_clue="Shira",
    ),
]

PRIZES = {
    "whistle": Prize(
        label="whistle",
        phrase="a silver whistle that could mimic any sound",
        type="whistle",
        region="torso",
    ),
    "locket": Prize(
        label="locket",
        phrase="a gold locket that hummed a forgotten tune",
        type="locket",
        region="torso",
    ),
}

GIRL_NAMES = ["Elara", "Lina", "Mira", "Sela", "Tara"]
BOY_NAMES = ["Kael", "Rune", "Dain", "Fen", "Nash"]
TRAITS = ["brave", "curious", "trusting", "quick-eared", "patient"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per‑world parameters
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
    "tick": [("What makes a ticking sound in the woods?",
              "The tick is a mysterious sound that echoes through the Whispering "
              "Woods at dusk. The elders say it is a trapped spirit calling for "
              "its name.")],
    "whisper": [("Why do whispers steal voices in the myth?",
                 "In the story, the whisper of the woods can steal the sound from "
                 "a whistle or a voice if you follow the tick without protection.")],
    "mystery": [("How do you solve the mystery of the tick?",
                 "You must listen carefully and recall the true name of the spirit. "
                 "Speaking that name breaks the spell and frees the trapped sound.")],
    "scarf": [("What does a muffler scarf do?",
               "A muffler scarf wraps around your chest and protects your whistle "
               "from being silenced by the woods.")],
    "cloak": [("What does a cloak of silence do?",
               "A cloak of silence covers your ears and torso, keeping the "
               "whispering woods from stealing your voice.")],
}
KNOWLEDGE_ORDER = ["tick", "whisper", "mystery", "scarf", "cloak"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword
    return [
        f'Write a myth‑style cautionary story for a young child that includes '
        f'the sound "tick… tick…" and a mystery to solve.',
        f"Tell a tale where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize.phrase}, and they solve a mystery together.",
        f'Write a story that uses the word "{kw}" and ends with the child '
        f"recalling a secret name that frees the trapped spirit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} while wearing {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to the edge of the woods at dusk, and "
                f"{hero.id} is wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do in the evenings before "
                f"{pw} warned about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved the hushed evenings and "
                f"{act.gerund}. The tick called {obj} like a riddle."
            ),
        ),
        QAItem(
            question=(
                f"What special {prize.label} did {hero.id}'s {pw} give {obj} "
                f"before the {act.keyword} adventure at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} gave {obj} {prize.phrase}. "
                f"{hero.id} loved it and wore it always."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "silent and sad")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was worried because if {hero.id} "
               f"followed the tick, {pos} {prize.label} would become {soil}")
        why += (f", and then {pw} would need to mend it. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} hand and said they would go together.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        mystery_name = f.get("mystery_name", "Tikani")
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} solve the mystery?"
            ),
            answer=(
                f"With the {gear.label} on, {hero.id} could enter the woods "
                f"without losing {pos} {prize.label}'s voice. Then "
                f"{hero.id} remembered the true name '{mystery_name}' and "
                f"spoke it, freeing the spirit and stopping the tick."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {hero.id} feel after solving the mystery of the tick?"
            ),
            answer=(
                f"{hero.id} felt happy and proud. {pos.capitalize()} {pw} hugged "
                f"{obj}, and the woods became peacefully quiet."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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


CURATED = [
    StoryParams(
        place="ashwood",
        activity="follow_tick",
        prize="whistle",
        name="Kael",
        gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        place="ashwood",
        activity="follow_tick",
        prize="locket",
        name="Elara",
        gender="girl",
        parent="father",
        trait="curious",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region} – it wouldn't get "
                f"silenced. Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"from {activity.gerund}. The compromise must actually cover the "
            f"at‑risk item.)")


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
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythical cautionary story: a child, a ticking mystery, "
                    "a solved puzzle. Unspecified choices are random.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="curated set")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible combos via clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check ASP gate vs Python")
    ap.add_argument("--show-asp", action="store_true",
                    help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: a {PRIZES[args.prize].label} is not typical "
                         f"for a {args.gender} here.)")

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
                 [params.trait, "brave"], params.parent)
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
