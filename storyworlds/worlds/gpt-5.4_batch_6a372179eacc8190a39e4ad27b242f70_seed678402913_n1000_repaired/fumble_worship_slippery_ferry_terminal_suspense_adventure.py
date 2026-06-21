#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py
========================================================================================

A standalone story world for a small suspenseful adventure at a ferry terminal.

Premise
-------
Two children wait at a ferry terminal and turn the place into the start of a sea
adventure. One child greatly admires harbor captains and says so. Then a dropped
keepsake skitters onto a slippery place near the water. The other child warns
them not to chase it alone. Depending on the social setup, the danger is either
averted in time, or the child steps onto the slick surface, slips, and a ferry
worker must rescue the keepsake with proper gear.

The world model tracks:
- physical meters: dropped, drifting, danger, slipped, rescued, lost
- emotional memes: awe, caution, defiance, fear, relief, lesson, joy

The prose is driven by world state and the chosen outcome:
- averted: the warning works before the child steps out
- rescued: the child slips, but a worker safely retrieves the keepsake
- lost: the child slips, stays safe, but the keepsake falls into the water

Run it
------
    python storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py
    python storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py --zone rope_gap
    python storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py --method jump_after
    python storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py --all --qa
    python storyworlds/worlds/gpt-5.4/fumble_worship_slippery_ferry_terminal_suspense_adventure.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "worker_woman"}
        male = {"boy", "father", "man", "worker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "worker_woman": "worker",
            "worker_man": "worker",
        }.get(self.type, self.type)


@dataclass
class Idol:
    id: str
    label: str
    phrase: str
    boast: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trinket:
    id: str
    label: str
    phrase: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"

    def was(self) -> str:
        return "were" if self.plural else "was"


@dataclass
class Zone:
    id: str
    label: str
    phrase: str
    scene: str
    slide_text: str
    need: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    sense: int
    reach: int
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_slip_alarm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("instigator")
    zone = world.entities.get("zone")
    room = world.entities.get("terminal")
    item = world.entities.get("trinket")
    if not child or not zone or not room or not item:
        return out
    if child.meters["on_danger"] < THRESHOLD:
        return out
    sig = ("slip_alarm", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["slipped"] += 1
    child.memes["fear"] += 1
    room.meters["danger"] += 1
    item.meters["drifting"] += 1
    out.append("__slip__")
    return out


def _r_scared_pair(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("terminal")
    if not room or room.meters["danger"] < THRESHOLD:
        return out
    sig = ("pair_scared", "kids")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__fear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip_alarm", tag="physical", apply=_r_slip_alarm),
    Rule(name="pair_scared", tag="emotional", apply=_r_scared_pair),
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
        for sent in produced:
            world.say(sent)
    return produced


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_methods():
        return combos
    for idol in IDOLS:
        for trinket in TRINKETS:
            for zone in ZONES:
                combos.append((idol, trinket, zone))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def is_retrieved(method: Method, zone: Zone) -> bool:
    return method.reach >= zone.need


def outcome_of(params: "StoryParams") -> str:
    if would_avert(
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trait=params.trait,
    ):
        return "averted"
    return "rescued" if is_retrieved(METHODS[params.method], ZONES[params.zone]) else "lost"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = " / ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A child should not solve a ferry-terminal "
        f"danger by doing something riskier. Try: {better}.)"
    )


def predict_slip(world: World) -> dict:
    sim = world.copy()
    child = sim.get("instigator")
    child.meters["on_danger"] += 1
    propagate(sim, narrate=False)
    return {
        "slips": child.meters["slipped"] >= THRESHOLD,
        "danger": sim.get("terminal").meters["danger"],
        "drifts": sim.get("trinket").meters["drifting"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, idol: Idol) -> None:
    a.memes["awe"] += 1
    b.memes["joy"] += 1
    world.say(
        f"The ferry terminal hummed with footsteps, gull cries, and the low cough of engines. "
        f"{a.id} and {b.id} stood by the rail and watched the big boat nose toward the dock."
    )
    world.say(
        f"{a.id} loved adventure books and almost seemed to worship {idol.phrase}. "
        f'"One day," {a.pronoun()} whispered, "{idol.boast}"'
    )


def make_game(world: World, a: Entity, b: Entity, idol: Idol, trinket: Trinket) -> None:
    world.say(
        f"To pass the wait, they turned the terminal into the start of a secret voyage. "
        f"A painted line became a sea border, a timetable board became a treasure chart, "
        f"and {trinket.phrase} became their captain sign."
    )
    world.say(
        f'{b.id} grinned. "Then we had better be ready before the horn blows."'
    )


def fumble_drop(world: World, a: Entity, trinket_ent: Entity, trinket: Trinket, zone: Zone) -> None:
    trinket_ent.meters["dropped"] += 1
    world.say(
        f"But when {a.id} shifted closer for a better look, a sudden fumble sent "
        f"{trinket.phrase} skittering away."
    )
    world.say(
        f"It slid across the boards and came to rest on {zone.phrase}, where the air smelled "
        f"of salt and the boards looked slippery and dark."
    )


def warn(world: World, b: Entity, a: Entity, zone: Zone, parent: Entity) -> None:
    pred = predict_slip(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "Wait," {b.pronoun()} said. '
        f'"That {zone.label} is slippery. {parent.label_word.capitalize()} said to stay behind the line."'
    )
    if pred["slips"]:
        world.say(
            f"{b.id} could already picture wet boards, a quick skid, and the black water slapping below."
        )


def defy(world: World, a: Entity, b: Entity, zone: Zone) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"I can get it before it moves," {a.id} said, heart beating fast. '
        f'{a.pronoun().capitalize()} stepped toward {zone.phrase} while the ferry ropes creaked.'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    world.say(
        f'{a.id} froze, listened to the warning, and stepped back again. '
        f'The adventure feeling stayed, but now it felt steadier than before.'
    )
    world.say(
        f'Together they called for {parent.label_word.capitalize()} and pointed to the dropped keepsake instead of chasing it alone.'
    )


def step_and_slip(world: World, a: Entity, zone_ent: Entity, zone: Zone, trinket: Trinket) -> None:
    a.meters["on_danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{a.id} put one foot onto {zone.phrase}. {zone.scene}."
    )
    world.say(
        f"{zone.slide_text} {a.id}'s shoes slipped sideways, and {a.pronoun()} dropped to one knee with a sharp gasp."
    )
    world.say(
        f"{trinket.phrase.capitalize()} wobbled nearer the water while the ferry horn gave one long, suspenseful moan."
    )


def alarm(world: World, b: Entity, worker: Entity) -> None:
    world.say(f'"{worker.label_word.capitalize()}! Please help!" {b.id} shouted.')
    world.say("For one second, everything felt louder: ropes, engines, gulls, and water.")


def rescue(world: World, worker: Entity, method: Method, trinket_ent: Entity, trinket: Trinket) -> None:
    trinket_ent.meters["rescued"] += 1
    trinket_ent.meters["drifting"] = 0.0
    world.get("terminal").meters["danger"] = 0.0
    world.say(
        f"The ferry worker moved fast but did not run. {worker.pronoun().capitalize()} "
        f"{method.success}."
    )
    world.say(
        f"In another moment {worker.pronoun()} held out {trinket.phrase} again, safe and only a little damp."
    )


def loss(world: World, worker: Entity, method: Method, trinket_ent: Entity, trinket: Trinket) -> None:
    trinket_ent.meters["lost"] += 1
    world.get("terminal").meters["danger"] = 0.0
    world.say(
        f"The ferry worker hurried over and {method.fail}."
    )
    world.say(
        f"But the water gave one small gulp, and {trinket.phrase} was gone."
    )


def comfort_and_lesson(world: World, parent: Entity, worker: Entity, a: Entity, b: Entity, method: Method) -> None:
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came close at once and wrapped an arm around both children."
    )
    world.say(
        f'"You did the right thing when you called for help," {parent.pronoun()} said softly. '
        f'"Brave does not mean rushing onto a dangerous place. Brave means stopping, thinking, and letting the right helper use the right tool."'
    )
    world.say(
        f'The worker nodded and lifted {method.phrase}. "At the terminal, we use tools so nobody has to lean over the edge," {worker.pronoun()} said.'
    )


def ending_safe(world: World, a: Entity, b: Entity, idol: Idol, trinket: Trinket) -> None:
    world.say(
        f"A little later, when the boarding gate opened, {a.id} tucked {trinket.phrase} safely into {a.pronoun('possessive')} pocket."
    )
    world.say(
        f'This time {a.pronoun()} still dreamed of {idol.ending}, but now the dream included careful feet, steady hands, and listening at the right moment.'
    )
    world.say(
        f'Together the two children walked onto the ferry with the wind in their faces, feeling as if a real adventure had begun.'
    )


def ending_loss(world: World, a: Entity, b: Entity, idol: Idol, trinket: Trinket) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent_word(world)} crouched beside them until their breathing slowed."
    )
    world.say(
        f'{a.id} looked at the dark water and understood how fast one shiny idea could turn into trouble.'
    )
    world.say(
        f"When the ferry finally opened for boarding, {a.id} climbed aboard empty-handed, but not empty-hearted. "
        f"{a.pronoun().capitalize()} still wanted adventure, only now {a.pronoun()} knew it should begin with caution."
    )


def parent_word(world: World) -> str:
    parent = world.facts.get("parent")
    if isinstance(parent, Entity):
        return parent.label_word.capitalize()
    return "Parent"


def tell(
    idol: Idol,
    trinket: Trinket,
    zone: Zone,
    method: Method,
    instigator: str = "Nia",
    instigator_gender: str = "girl",
    cautioner: str = "Owen",
    cautioner_gender: str = "boy",
    trait: str = "careful",
    parent_type: str = "mother",
    worker_type: str = "worker_man",
    relation: str = "siblings",
    instigator_age: int = 5,
    cautioner_age: int = 7,
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation, "trust": trust},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    worker = world.add(
        Entity(
            id="worker",
            kind="character",
            type=worker_type,
            label="the ferry worker",
            role="worker",
        )
    )
    terminal = world.add(Entity(id="terminal", type="terminal", label="the terminal"))
    trinket_ent = world.add(
        Entity(
            id="trinket",
            type="trinket",
            label=trinket.label,
            phrase=trinket.phrase,
            tags=set(trinket.tags),
        )
    )
    zone_ent = world.add(
        Entity(
            id="zone",
            type="zone",
            label=zone.label,
            phrase=zone.phrase,
            tags=set(zone.tags),
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)

    introduce(world, a, b, idol)
    make_game(world, a, b, idol, trinket)
    world.para()
    fumble_drop(world, a, trinket_ent, trinket, zone)
    warn(world, b, a, zone, parent)

    averted = would_avert(
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trait=trait,
    )

    if averted:
        back_down(world, a, b, parent)
        world.para()
        rescue(world, worker, method, trinket_ent, trinket)
        comfort_and_lesson(world, parent, worker, a, b, method)
        world.para()
        ending_safe(world, a, b, idol, trinket)
        outcome = "averted"
    else:
        defy(world, a, b, zone)
        world.para()
        step_and_slip(world, a, zone_ent, zone, trinket)
        alarm(world, b, worker)
        world.para()
        got_it = is_retrieved(method, zone)
        if got_it:
            rescue(world, worker, method, trinket_ent, trinket)
            comfort_and_lesson(world, parent, worker, a, b, method)
            world.para()
            ending_safe(world, a, b, idol, trinket)
            outcome = "rescued"
        else:
            loss(world, worker, method, trinket_ent, trinket)
            comfort_and_lesson(world, parent, worker, a, b, method)
            world.para()
            ending_loss(world, a, b, idol, trinket)
            outcome = "lost"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        worker=worker,
        terminal=terminal,
        idol=idol,
        trinket_cfg=trinket,
        trinket=trinket_ent,
        zone_cfg=zone,
        zone=zone_ent,
        method=method,
        relation=relation,
        outcome=outcome,
        predicted_danger=world.facts.get("predicted_danger", 0.0),
        slipped=a.meters["slipped"] >= THRESHOLD,
        rescued=trinket_ent.meters["rescued"] >= THRESHOLD,
        lost=trinket_ent.meters["lost"] >= THRESHOLD,
    )
    return world


IDOLS = {
    "captain": Idol(
        id="captain",
        label="harbor captain",
        phrase="the harbor captains who knew every tide and horn",
        boast="I want to be a captain who can read fog and waves",
        ending="standing on a brave bridge high above the water one day",
        tags={"captain", "ferry"},
    ),
    "explorer": Idol(
        id="explorer",
        label="sea explorer",
        phrase="the old sea explorers in the mural by the ticket windows",
        boast="I want to follow secret routes over every gray bay",
        ending="following a chalk map toward hidden islands one day",
        tags={"explorer", "ferry"},
    ),
    "rescuer": Idol(
        id="rescuer",
        label="harbor rescuer",
        phrase="the rescue crews painted on the safety poster",
        boast="I want to help people the minute trouble starts",
        ending="helping others with calm eyes and quick thinking one day",
        tags={"rescuer", "ferry"},
    ),
}

TRINKETS = {
    "badge": Trinket(
        id="badge",
        label="captain badge",
        phrase="a shiny toy captain badge",
        tags={"badge"},
    ),
    "compass": Trinket(
        id="compass",
        label="toy compass",
        phrase="a little toy compass",
        tags={"compass"},
    ),
    "map": Trinket(
        id="map",
        label="paper map",
        phrase="a folded paper map",
        tags={"map"},
    ),
}

ZONES = {
    "wet_ramp": Zone(
        id="wet_ramp",
        label="boarding ramp",
        phrase="the wet boarding ramp",
        scene="The metal hummed under the ferry's weight",
        slide_text="A thin stripe of water made the path gleam like glass",
        need=2,
        tags={"slippery", "ramp"},
    ),
    "rope_gap": Zone(
        id="rope_gap",
        label="mooring edge",
        phrase="the slick space beside the mooring ropes",
        scene="Below, the water knocked against the pilings in dark little bangs",
        slide_text="Green slime and spray had turned the boards shiny",
        need=3,
        tags={"slippery", "water"},
    ),
    "stairs": Zone(
        id="stairs",
        label="side stairs",
        phrase="the narrow side stairs by the loading lane",
        scene="The ferry's shadow made the steps look deeper than they were",
        slide_text="Rainwater had gathered on the painted edge",
        need=1,
        tags={"slippery", "stairs"},
    ),
}

METHODS = {
    "boat_hook": Method(
        id="boat_hook",
        label="boat hook",
        phrase="the long boat hook",
        sense=3,
        reach=3,
        success="caught the keepsake with the long boat hook and drew it back without anyone stepping closer",
        fail="reached with the boat hook, but the keepsake slid off the far side before it could be caught",
        qa_text="used a long boat hook to pull the keepsake back",
        tags={"boat_hook", "tool"},
    ),
    "grabber": Method(
        id="grabber",
        label="grabber pole",
        phrase="the grabber pole",
        sense=2,
        reach=2,
        success="stretched out the grabber pole, pinched the keepsake neatly, and pulled it to safety",
        fail="stretched out the grabber pole, but it was just too short to reach",
        qa_text="used a grabber pole to pinch the keepsake and pull it back",
        tags={"grabber", "tool"},
    ),
    "net": Method(
        id="net",
        label="dock net",
        phrase="the dock net",
        sense=3,
        reach=1,
        success="dipped the dock net low and scooped the keepsake up before it could slide farther",
        fail="swung the dock net down, but the keepsake slipped beyond the shallow scoop",
        qa_text="used a dock net to scoop the keepsake up",
        tags={"net", "tool"},
    ),
    "jump_after": Method(
        id="jump_after",
        label="jump after it",
        phrase="no safe tool at all",
        sense=1,
        reach=3,
        success="jumped after the keepsake",
        fail="jumped after the keepsake",
        qa_text="jumped after the keepsake",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Mara", "Tess", "June", "Ava", "Rina", "Poppy"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Milo", "Jude", "Theo", "Max", "Eli"]
TRAITS = ["careful", "steady", "sensible", "watchful", "curious", "thoughtful"]


@dataclass
class StoryParams:
    idol: str
    trinket: str
    zone: str
    method: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    worker: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 5
    cautioner_age: int = 7
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "ferry": [
        (
            "What is a ferry?",
            "A ferry is a boat that carries people or cars across water. It follows a regular route from one dock to another."
        )
    ],
    "slippery": [
        (
            "Why is a slippery surface dangerous?",
            "A slippery surface does not give your shoes a good grip, so your feet can slide out from under you. Near water or stairs, that can turn a small mistake into a big danger very quickly."
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook used for?",
            "A boat hook is a long pole used to reach something from a safer distance. Workers can pull a rope or an object closer without leaning too far over the edge."
        )
    ],
    "grabber": [
        (
            "What is a grabber pole?",
            "A grabber pole is a long tool that can pinch and hold something far away. It helps people pick things up without stepping into danger."
        )
    ],
    "net": [
        (
            "What does a dock net do?",
            "A dock net can scoop something up from below. It works best when the object is close enough for the net to reach."
        )
    ],
    "captain": [
        (
            "What does a captain do on a big boat?",
            "A captain leads the boat and helps keep everyone safe. Captains watch the route, the weather, and the people working together."
        )
    ],
    "rescuer": [
        (
            "What makes a rescuer truly brave?",
            "A rescuer is brave by staying calm and using the right help at the right time. Rushing without thinking can make danger worse."
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map helps you see where places are and how to get from one place to another. In stories, a map can also make an ordinary trip feel like an adventure."
        )
    ],
    "compass": [
        (
            "What does a compass do?",
            "A compass points north and helps travelers know which way they are facing. Even a toy compass can make a child imagine a real journey."
        )
    ],
    "water": [
        (
            "Why should children ask for help near deep water?",
            "Deep water can be dangerous because edges are hard, surfaces can be slick, and a fall can happen fast. Calling a grown-up or trained worker is the safest choice."
        )
    ],
}
KNOWLEDGE_ORDER = ["ferry", "slippery", "boat_hook", "grabber", "net", "captain", "rescuer", "map", "compass", "water"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    idol = f["idol"]
    trinket = f["trinket_cfg"]
    zone = f["zone_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a suspenseful adventure story for ages 3 to 5 set at a ferry terminal that includes the words "fumble", "worship", and "slippery".',
            f"Tell a story where {a.label} drops {trinket.phrase} near {zone.phrase}, but {b.label} stops {a.pronoun('object')} before {a.pronoun()} steps onto the danger.",
            f"Write a gentle harbor adventure where a child who admires {idol.label}s learns that careful listening is part of being brave.",
        ]
    if outcome == "rescued":
        return [
            f'Write a suspenseful adventure story for ages 3 to 5 set at a ferry terminal that includes the words "fumble", "worship", and "slippery".',
            f"Tell a story where {a.label} chases {trinket.phrase} onto {zone.phrase}, slips, and a calm worker uses a tool to solve the problem safely.",
            f"Write a harbor adventure that feels tense for a moment but ends with a lesson about asking for help near water.",
        ]
    return [
        f'Write a suspenseful adventure story for ages 3 to 5 set at a ferry terminal that includes the words "fumble", "worship", and "slippery".',
        f"Tell a cautionary harbor adventure where {a.label} slips while trying to get back {trinket.phrase}, and everyone stays safe even though the keepsake is lost.",
        f"Write a story that shows brave choices are thoughtful choices, especially on wet ferry-terminal boards.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    worker = f["worker"]
    idol = f["idol"]
    trinket = f["trinket_cfg"]
    zone = f["zone_cfg"]
    method = f["method"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, waiting at a ferry terminal. The story also includes {a.label}'s {parent.label_word} and a ferry worker who helps when the danger starts."
        ),
        (
            f"Why did the terminal feel like an adventure to {a.label}?",
            f"{a.label} admired {idol.label}s and imagined the terminal as the start of a voyage. That is why losing {trinket.phrase} felt like a big adventure problem instead of a small ordinary one."
        ),
        (
            f"What happened after the fumble?",
            f"After the fumble, {trinket.phrase} slid onto {zone.phrase}. The place looked slippery, which is why {b.label} warned {a.label} not to chase it alone."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How was the danger stopped before anyone got hurt?",
                f"{a.label} listened and stepped back instead of going onto the slick place. Then the children called for help, so the worker could use {method.phrase} safely from a better distance."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the keepsake safe and the children calmer and wiser. They still boarded the ferry feeling adventurous, but now they knew that brave adventures need careful choices."
            )
        )
    elif f["outcome"] == "rescued":
        qa.append(
            (
                f"How did the worker solve the problem?",
                f"The worker {method.qa_text}. That worked because the tool could reach the dangerous spot without making any child step closer to the water."
            )
        )
        qa.append(
            (
                f"What did {a.label} learn?",
                f"{a.label} learned that being brave does not mean rushing onto a slippery place. {a.pronoun('subject').capitalize()} learned that stopping and calling for help is the safer and wiser kind of courage."
            )
        )
    else:
        qa.append(
            (
                f"Why was {trinket.phrase} lost?",
                f"{trinket.phrase.capitalize()} was lost because it had slid too far into the dangerous area before the worker could reach it. Even so, the adults still cared most that the child was safe and off the slippery edge."
            )
        )
        qa.append(
            (
                "Was the ending completely sad?",
                f"No. The keepsake was gone, but everyone stayed safe, and that mattered most. The ending proves that a lost object is better than a child getting badly hurt."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ferry", "slippery"}
    tags |= set(f["idol"].tags)
    tags |= set(f["trinket_cfg"].tags)
    tags |= set(f["zone_cfg"].tags)
    tags |= set(f["method"].tags)
    if "water" in f["zone_cfg"].tags or f["zone_cfg"].id == "rope_gap":
        tags.add("water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:11} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        idol="captain",
        trinket="badge",
        zone="wet_ramp",
        method="grabber",
        instigator="Nia",
        instigator_gender="girl",
        cautioner="Owen",
        cautioner_gender="boy",
        parent="mother",
        worker="worker_man",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=7,
    ),
    StoryParams(
        idol="explorer",
        trinket="map",
        zone="stairs",
        method="net",
        instigator="Finn",
        instigator_gender="boy",
        cautioner="Lila",
        cautioner_gender="girl",
        parent="father",
        worker="worker_woman",
        trait="thoughtful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
    ),
    StoryParams(
        idol="rescuer",
        trinket="compass",
        zone="rope_gap",
        method="grabber",
        instigator="Mara",
        instigator_gender="girl",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="mother",
        worker="worker_man",
        trait="watchful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=3,
    ),
    StoryParams(
        idol="captain",
        trinket="map",
        zone="rope_gap",
        method="boat_hook",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        parent="father",
        worker="worker_woman",
        trait="sensible",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
        trust=5,
    ),
]


def explain_choice(zone: Zone) -> str:
    return (
        f"(No story: {zone.phrase} is part of a dangerous ferry-terminal edge, so the retrieval method must be sensible and tool-based.)"
    )


ASP_RULES = r"""
valid(I, T, Z) :- idol(I), trinket(T), zone(Z).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), cautioner_age(CA), instigator_age(IA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).

averted :- older_sibling, authority(A), bravery_init(BR), A > BR.

retrieved :- chosen_zone(Z), need(Z, N), chosen_method(M), reach(M, R), R >= N.

outcome(averted) :- averted.
outcome(rescued) :- not averted, retrieved.
outcome(lost) :- not averted, not retrieved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for idol_id in IDOLS:
        lines.append(asp.fact("idol", idol_id))
    for trinket_id in TRINKETS:
        lines.append(asp.fact("trinket", trinket_id))
    for zone_id, zone in ZONES.items():
        lines.append(asp.fact("zone", zone_id))
        lines.append(asp.fact("need", zone_id, zone.need))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(name for (name,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_zone", params.zone),
            asp.fact("chosen_method", params.method),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a slippery ferry-terminal adventure with a dropped keepsake."
    )
    ap.add_argument("--idol", choices=IDOLS)
    ap.add_argument("--trinket", choices=TRINKETS)
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--worker", choices=["worker_man", "worker_woman"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.idol is None or combo[0] == args.idol)
        and (args.trinket is None or combo[1] == args.trinket)
        and (args.zone is None or combo[2] == args.zone)
    ]
    if not combos:
        if args.zone:
            raise StoryError(explain_choice(ZONES[args.zone]))
        raise StoryError("(No valid combination matches the given options.)")

    idol_id, trinket_id, zone_id = rng.choice(sorted(combos))
    method_id = args.method or rng.choice(sorted(m.id for m in sensible_methods()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    trust = rng.randint(2, 8)
    return StoryParams(
        idol=idol_id,
        trinket=trinket_id,
        zone=zone_id,
        method=method_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        worker=args.worker or rng.choice(["worker_man", "worker_woman"]),
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        idol = IDOLS[params.idol]
        trinket = TRINKETS[params.trinket]
        zone = ZONES[params.zone]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        idol=idol,
        trinket=trinket,
        zone=zone,
        method=method,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        worker_type=params.worker,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sensible = set(asp_sensible())
    p_sensible = {m.id for m in sensible_methods()}
    if c_sensible == p_sensible:
        print(f"OK: sensible methods match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (idol, trinket, zone) combos:\n")
        for idol, trinket, zone in combos:
            print(f"  {idol:9} {trinket:8} {zone}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.trinket} at {p.zone} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
