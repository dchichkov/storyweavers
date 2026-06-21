#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py
============================================================================

A standalone story world about a small mystery at a neighborhood event:
something on a display table has changed shape, a curious child follows clues,
and the "culprit" turns out to be an accidental helper rather than a villain.

This world is built around:
- the seed words "slag" and "event"
- the narrative features Transformation and Curiosity
- a gentle whodunit shape

Run it
------
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py --all
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py --qa --json
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py --asp
python storyworlds/worlds/gpt-5.4/slag_event_transformation_curiosity_whodunit.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type or self.label or "grown-up")


@dataclass
class EventCfg:
    id: str
    place: str
    opening: str
    crowd: str
    forge_booth: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ExhibitCfg:
    id: str
    label: str
    phrase: str
    material: str
    display: str
    transformed: str
    susceptible: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class CauseCfg:
    id: str
    label: str
    tool: str
    clue: str
    touch: str
    effect_meter: str
    effect_line: str
    explanation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectCfg:
    id: str
    label: str
    role_line: str
    tool_tags: set[str] = field(default_factory=set)
    innocent_line: str = ""
    apology_line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    label: str
    action: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    event: str
    exhibit: str
    cause: str
    suspect: str
    repair: str
    investigator_name: str
    investigator_gender: str
    maker_name: str
    maker_gender: str
    host_type: str
    seed: Optional[int] = None


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    exhibit = world.entities.get("exhibit")
    investigator = world.entities.get("investigator")
    maker = world.entities.get("maker")
    if not exhibit or exhibit.meters["changed"] < THRESHOLD:
        return []
    sig = ("worry", exhibit.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if investigator:
        investigator.memes["curiosity"] += 1
    if maker:
        maker.memes["worry"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="social", apply=_r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                produced.extend(out)
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


EVENTS = {
    "fair": EventCfg(
        id="fair",
        place="the neighborhood maker fair",
        opening="Colorful tables stood in a row under paper flags at the neighborhood maker fair.",
        crowd="Children drifted from table to table, pointing at tiny inventions and handmade treasures.",
        forge_booth="At one end of the event, a careful grown-up ran a metal booth with a bowl of cool black slag for children to touch after it had gone cold.",
        ending="By the end of the fair, people were smiling at the rebuilt display instead of whispering about the mystery.",
        tags={"event", "fair"},
    ),
    "library": EventCfg(
        id="library",
        place="the library invention event",
        opening="The library invention event filled the meeting room with bright posters, folded paper signs, and excited feet.",
        crowd="Families moved softly between the tables, reading labels and asking little questions.",
        forge_booth="Near the door stood a supervised recycling display with a tray of cold slag from a metal-melting lesson earlier that morning.",
        ending="When the mystery was solved, the room felt warm with relief instead of hushed with guessing.",
        tags={"event", "library"},
    ),
    "garden": EventCfg(
        id="garden",
        place="the school garden event",
        opening="String lights hung over the school garden event, and every bench had been turned into a tiny display table.",
        crowd="Neighbors stopped to admire projects while bees hummed near the marigolds.",
        forge_booth="Beside the fence, a science table showed cooled slag from an old rock-and-metal lesson, black and bumpy like crumbled toast.",
        ending="Soon the garden was full of talking and laughter again, and nobody looked worried anymore.",
        tags={"event", "garden"},
    ),
}

EXHIBITS = {
    "wax_dragon": ExhibitCfg(
        id="wax_dragon",
        label="dragon",
        phrase="a little wax dragon",
        material="wax",
        display="Its tail curled proudly around a cardboard cave.",
        transformed="the dragon had drooped sideways, with one wing folded into a shiny puddle",
        susceptible={"heat_lamp", "warm_vent"},
        tags={"wax", "transformation"},
    ),
    "ice_castle": ExhibitCfg(
        id="ice_castle",
        label="castle",
        phrase="a tiny ice castle",
        material="ice",
        display="Its clear towers sparkled over a blue cloth like frozen glass.",
        transformed="the castle had sunk low, and its towers had turned into a clear puddle around the base",
        susceptible={"heat_lamp", "warm_vent"},
        tags={"ice", "transformation"},
    ),
    "clay_turtle": ExhibitCfg(
        id="clay_turtle",
        label="turtle",
        phrase="a soft clay turtle",
        material="clay",
        display="Its shell was pressed with neat little leaf marks.",
        transformed="the turtle had slumped flat, and the leaf marks were blurred in the middle",
        susceptible={"sprinkler"},
        tags={"clay", "transformation"},
    ),
}

CAUSES = {
    "heat_lamp": CauseCfg(
        id="heat_lamp",
        label="a bright heat lamp",
        tool="lamp",
        clue="A warm yellow circle lay across the tablecloth, and the air above the display still felt cozy.",
        touch="warm",
        effect_meter="soft",
        effect_line="Whatever had happened had happened with warmth, not with splashing.",
        explanation="The lamp had been aimed too close to the table, and the warmth changed the exhibit's shape.",
        tags={"heat", "lamp"},
    ),
    "warm_vent": CauseCfg(
        id="warm_vent",
        label="a warm floor vent",
        tool="vent",
        clue="A slow ribbon of warm air brushed across the display, and a paper label nearby kept fluttering.",
        touch="warm",
        effect_meter="soft",
        effect_line="The clue pointed to a steady stream of heat instead of a quick bump or spill.",
        explanation="The vent had been switched on under the table, and the warm air slowly changed the exhibit.",
        tags={"heat", "vent"},
    ),
    "sprinkler": CauseCfg(
        id="sprinkler",
        label="a garden sprinkler",
        tool="water",
        clue="Tiny drops shone on the cloth, and damp speckles dotted the sign beside the display.",
        touch="cool",
        effect_meter="wet",
        effect_line="The mystery smelled of water, not warmth.",
        explanation="The sprinkler had sprayed farther than expected, and the water changed the clay turtle's shape.",
        tags={"water", "sprinkler"},
    ),
}

SUSPECTS = {
    "stage_helper": SuspectCfg(
        id="stage_helper",
        label="Ms. Pia",
        role_line="Ms. Pia was helping the music table and had borrowed a lamp so the signs could be read.",
        tool_tags={"lamp"},
        innocent_line='Ms. Pia blinked and said, "I only wanted the paper sign to shine."',
        apology_line='Ms. Pia put a hand on her heart and said, "Oh dear. I moved the lamp, and I did not notice it was warming the display."',
        tags={"lamp"},
    ),
    "caretaker": SuspectCfg(
        id="caretaker",
        label="Mr. Reed",
        role_line="Mr. Reed, the caretaker, had been checking plugs and switches all morning.",
        tool_tags={"vent"},
        innocent_line='Mr. Reed rubbed his chin and said, "I did turn on one heater, but only because the room felt chilly."',
        apology_line='Mr. Reed nodded sadly and said, "That warm vent was my doing. I meant to help the room, not harm the project."',
        tags={"vent"},
    ),
    "gardener": SuspectCfg(
        id="gardener",
        label="Mrs. Sol",
        role_line="Mrs. Sol had been watering the seedlings beside the path.",
        tool_tags={"water"},
        innocent_line='Mrs. Sol looked at the drops and whispered, "I was watering the beans. I did not see the spray reach the table."',
        apology_line='Mrs. Sol sighed and said, "The sprinkler turned wider than I thought. I am sorry it reached the turtle."',
        tags={"water"},
    ),
    "smith": SuspectCfg(
        id="smith",
        label="Old Ben",
        role_line="Old Ben was running the metal lesson and showing children pieces of cooled slag.",
        tool_tags={"slag"},
        innocent_line='Old Ben chuckled softly. "My slag is cold as a stone now. It can leave a crumb, but it cannot melt a dragon or splash a turtle."',
        apology_line='Old Ben smiled and shook his head. "This one was not me."',
        tags={"slag"},
    ),
}

REPAIRS = {
    "cool_and_reshape": RepairCfg(
        id="cool_and_reshape",
        label="cool and reshape it",
        action="set the piece on a cool tray and gently shape it again with clean wooden sticks",
        ending_image="The little figure stood straighter than before, as if it had taken a deep breath.",
        tags={"repair"},
    ),
    "move_and_rebuild": RepairCfg(
        id="move_and_rebuild",
        label="move it into shade and rebuild it",
        action="carry the display to a shady spot and stack fresh pieces carefully into place",
        ending_image="Soon the towers caught the light again, but this time from a safe, cool corner.",
        tags={"repair"},
    ),
    "pat_and_dry": RepairCfg(
        id="pat_and_dry",
        label="pat it back into shape and let it dry",
        action="blot away the drops, press the shell back gently, and leave it where the air was still",
        ending_image="When the shell held its round shape again, the leaf marks looked neat and proud.",
        tags={"repair"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ella", "Ava", "Lucy", "Ivy"]
BOY_NAMES = ["Owen", "Max", "Theo", "Ben", "Eli", "Noah", "Finn", "Sam"]


def suspect_can_cause(suspect_id: str, cause_id: str) -> bool:
    if suspect_id not in SUSPECTS or cause_id not in CAUSES:
        return False
    return CAUSES[cause_id].tool in SUSPECTS[suspect_id].tool_tags


def select_repair(exhibit_id: str) -> Optional[str]:
    if exhibit_id == "wax_dragon":
        return "cool_and_reshape"
    if exhibit_id == "ice_castle":
        return "move_and_rebuild"
    if exhibit_id == "clay_turtle":
        return "pat_and_dry"
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for event_id in EVENTS:
        for exhibit_id, exhibit in EXHIBITS.items():
            if not select_repair(exhibit_id):
                continue
            for cause_id in sorted(exhibit.susceptible):
                for suspect_id in SUSPECTS:
                    if suspect_can_cause(suspect_id, cause_id):
                        combos.append((event_id, exhibit_id, cause_id, suspect_id))
    return combos


def explain_combo_rejection(exhibit: ExhibitCfg, cause: CauseCfg) -> str:
    return (
        f"(No story: {cause.label.capitalize()} would not reasonably transform "
        f"{exhibit.phrase}. This world only allows causes that fit the material.)"
    )


def explain_suspect_rejection(suspect: SuspectCfg, cause: CauseCfg) -> str:
    return (
        f"(No story: {suspect.label} is not the right accidental culprit for "
        f"{cause.label}. The clues and the helper's tools would not match.)"
    )


def predict_change(world: World, cause_id: str) -> dict:
    sim = world.copy()
    exhibit = sim.get("exhibit")
    cause = CAUSES[cause_id]
    exhibit.meters["changed"] += 1
    exhibit.meters[cause.effect_meter] += 1
    propagate(sim, narrate=False)
    return {
        "changed": exhibit.meters["changed"] >= THRESHOLD,
        "feel": cause.touch,
        "meter": cause.effect_meter,
    }


def introduce(world: World, event: EventCfg, investigator: Entity, maker: Entity, exhibit: ExhibitCfg) -> None:
    investigator.memes["curiosity"] += 1
    maker.memes["pride"] += 1
    world.say(event.opening)
    world.say(event.crowd)
    world.say(event.forge_booth)
    world.say(
        f"{maker.id} had brought {exhibit.phrase} to the event. {exhibit.display}"
    )
    world.say(
        f"{investigator.id} loved peeking closely at every table and asking how things worked."
    )


def discovery(world: World, investigator: Entity, maker: Entity, exhibit_cfg: ExhibitCfg, cause_cfg: CauseCfg) -> None:
    exhibit = world.get("exhibit")
    exhibit.meters["changed"] += 1
    exhibit.meters[cause_cfg.effect_meter] += 1
    propagate(world, narrate=False)
    maker.memes["worry"] += 1
    world.para()
    world.say(
        f"But when {maker.id} came back with a paper cup of water, {exhibit_cfg.transformed}."
    )
    world.say(
        f'"Oh no," {maker.id} whispered. "{investigator.id}, something happened to my {exhibit_cfg.label}."'
    )
    world.say(
        "Near the table lay one tiny crumb of black slag, and for a moment that made the mystery look even stranger."
    )


def inspect_clues(world: World, investigator: Entity, exhibit_cfg: ExhibitCfg, cause_cfg: CauseCfg) -> None:
    pred = predict_change(world, cause_cfg.id)
    world.facts["predicted_feel"] = pred["feel"]
    world.facts["predicted_meter"] = pred["meter"]
    investigator.memes["focus"] += 1
    world.para()
    world.say(
        f"{investigator.id} did not point at anyone right away. {investigator.pronoun().capitalize()} crouched by the table and looked slowly."
    )
    world.say(cause_cfg.clue)
    world.say(cause_cfg.effect_line)
    world.say(
        f'{investigator.id} touched the edge of the cloth with one finger. "It feels {cause_cfg.touch}," {investigator.pronoun()} said.'
    )


def question_red_herring(world: World, investigator: Entity) -> None:
    smith = SUSPECTS["smith"]
    world.say(
        f"First {investigator.id} asked {smith.label}, because of the little slag crumb on the floor."
    )
    world.say(smith.innocent_line)
    world.facts["red_herring"] = smith.label


def question_true_suspect(world: World, investigator: Entity, suspect_cfg: SuspectCfg) -> None:
    world.say(suspect_cfg.role_line)
    world.say(suspect_cfg.innocent_line)


def deduce(world: World, investigator: Entity, maker: Entity, suspect_cfg: SuspectCfg, cause_cfg: CauseCfg) -> None:
    investigator.memes["confidence"] += 1
    world.para()
    world.say(
        f'Then {investigator.id} looked from the clue to the table and back again. "{suspect_cfg.label} did it," {investigator.pronoun()} said, '
        f'"but not by being mean. {cause_cfg.explanation}"'
    )
    world.say(
        f"{maker.id} blinked, then looked at the clue again and nodded slowly."
    )
    world.facts["culprit_named"] = suspect_cfg.label


def confess_and_repair(world: World, investigator: Entity, maker: Entity, suspect_cfg: SuspectCfg, repair_cfg: RepairCfg) -> None:
    maker.memes["relief"] += 1
    investigator.memes["relief"] += 1
    suspect = world.get("suspect")
    exhibit = world.get("exhibit")
    suspect.memes["care"] += 1
    exhibit.meters["restored"] += 1
    exhibit.meters["changed"] = 0.0
    exhibit.meters["soft"] = 0.0
    exhibit.meters["wet"] = 0.0
    world.say(suspect_cfg.apology_line)
    world.say(
        f"Then {suspect_cfg.label} helped {maker.id} {repair_cfg.action}."
    )
    world.say(
        f"{repair_cfg.ending_image} {investigator.id} smiled, pleased that curiosity had solved the puzzle kindly."
    )


def tell(
    event_cfg: EventCfg,
    exhibit_cfg: ExhibitCfg,
    cause_cfg: CauseCfg,
    suspect_cfg: SuspectCfg,
    repair_cfg: RepairCfg,
    investigator_name: str,
    investigator_gender: str,
    maker_name: str,
    maker_gender: str,
    host_type: str,
) -> World:
    world = World()
    investigator = world.add(
        Entity(
            id=investigator_name,
            kind="character",
            type=investigator_gender,
            role="investigator",
            traits=["curious"],
        )
    )
    maker = world.add(
        Entity(
            id=maker_name,
            kind="character",
            type=maker_gender,
            role="maker",
            traits=["careful"],
        )
    )
    host = world.add(
        Entity(
            id="Host",
            kind="character",
            type=host_type,
            role="host",
            label="the host",
        )
    )
    exhibit = world.add(
        Entity(
            id="exhibit",
            type="exhibit",
            label=exhibit_cfg.label,
            phrase=exhibit_cfg.phrase,
            attrs={"material": exhibit_cfg.material},
            tags=set(exhibit_cfg.tags),
        )
    )
    suspect = world.add(
        Entity(
            id="suspect",
            kind="character",
            type="adult",
            label=suspect_cfg.label,
            role="suspect",
            tags=set(suspect_cfg.tags),
        )
    )

    introduce(world, event_cfg, investigator, maker, exhibit_cfg)
    discovery(world, investigator, maker, exhibit_cfg, cause_cfg)
    inspect_clues(world, investigator, exhibit_cfg, cause_cfg)
    question_red_herring(world, investigator)
    question_true_suspect(world, investigator, suspect_cfg)
    deduce(world, investigator, maker, suspect_cfg, cause_cfg)
    confess_and_repair(world, investigator, maker, suspect_cfg, repair_cfg)

    world.para()
    world.say(
        f'{host.label_word.capitalize()} clapped softly. "That was good noticing," {host.pronoun()} said. "A mystery is easier to solve when someone looks before blaming."'
    )
    world.say(event_cfg.ending)

    world.facts.update(
        event=event_cfg,
        exhibit_cfg=exhibit_cfg,
        cause_cfg=cause_cfg,
        suspect_cfg=suspect_cfg,
        repair_cfg=repair_cfg,
        investigator=investigator,
        maker=maker,
        host=host,
        exhibit=exhibit,
        culprit=suspect_cfg.label,
        solved=True,
        accidental=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    investigator = f["investigator"]
    exhibit = f["exhibit_cfg"]
    cause = f["cause_cfg"]
    event = f["event"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "slag" and "event".',
        f"Tell a curious mystery set at {event.place} where a child notices that {exhibit.phrase} has changed shape and follows clues instead of guessing wildly.",
        f"Write a story where {investigator.id} solves a small mystery by noticing that {cause.label} transformed the display, and the ending stays kind instead of scary.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    investigator = f["investigator"]
    maker = f["maker"]
    exhibit_cfg = f["exhibit_cfg"]
    cause_cfg = f["cause_cfg"]
    suspect_cfg = f["suspect_cfg"]
    repair_cfg = f["repair_cfg"]
    red_herring = f.get("red_herring", "Old Ben")
    return [
        (
            "Who was the mystery-solver in the story?",
            f"It was {investigator.id}. {investigator.pronoun().capitalize()} stayed calm and looked for clues before blaming anyone.",
        ),
        (
            f"What happened to {maker.id}'s display?",
            f"{maker.id}'s {exhibit_cfg.label} changed shape during the event. The transformation was the heart of the mystery, because it told {investigator.id} that something in the room had acted on it.",
        ),
        (
            "Why did the slag crumb seem important at first?",
            f"It looked important because it made the metal booth seem suspicious. But it was only a red herring, and {investigator.id} kept looking after {red_herring} explained that cold slag could not cause that kind of change.",
        ),
        (
            f"How did {investigator.id} solve the mystery?",
            f"{investigator.id} noticed the real clue: {cause_cfg.clue.lower()} {cause_cfg.effect_line} That helped {investigator.pronoun('object')} match the change in the display to the right cause and the right helper.",
        ),
        (
            f"Who caused the problem, and was it on purpose?",
            f"It was {suspect_cfg.label}, but not on purpose. {cause_cfg.explanation} so the mistake came from trying to help, not from being unkind.",
        ),
        (
            "How did the story end?",
            f"The grown-up apologized, and everyone worked together to {repair_cfg.label}. The ending image shows the change clearly, because the display looked right again and the whispers at the event stopped.",
        ),
    ]


KNOWLEDGE = {
    "slag": [
        (
            "What is slag?",
            "Slag is the rough, stony stuff left behind after metal is melted. Once it has cooled, it can feel hard and bumpy, but it is not the same as shiny metal.",
        )
    ],
    "event": [
        (
            "What is an event?",
            "An event is a planned happening where people gather to do or see something together. A fair, a show, or a school display can all be events.",
        )
    ],
    "wax": [
        (
            "What happens when wax gets warm?",
            "Warm wax gets soft and can bend or droop. If it cools again, it can firm up in a new shape.",
        )
    ],
    "ice": [
        (
            "What happens when ice gets warm?",
            "Ice melts into water when it gets warm. That is why an ice shape can turn into a puddle.",
        )
    ],
    "clay": [
        (
            "Why can wet clay change shape?",
            "Soft clay can slump when water gets on it because it becomes looser and squishier. That makes little marks blur and edges sag.",
        )
    ],
    "heat": [
        (
            "How can heat change things?",
            "Heat can soften or melt some materials. That means warmth can transform how something looks and feels.",
        )
    ],
    "water": [
        (
            "How can water change things?",
            "Water can soak into some materials and make them softer or messier. That is why splashes can change a clay project.",
        )
    ],
    "mystery": [
        (
            "What helps solve a mystery?",
            "Good mystery-solvers look for clues and think carefully about what fits. They do not just point at someone because of one surprising thing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["slag", "event", "wax", "ice", "clay", "heat", "water", "mystery"]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    exhibit_cfg = f["exhibit_cfg"]
    cause_cfg = f["cause_cfg"]
    tags = {"slag", "event", "mystery"}
    if exhibit_cfg.material == "wax":
        tags.add("wax")
    if exhibit_cfg.material == "ice":
        tags.add("ice")
    if exhibit_cfg.material == "clay":
        tags.add("clay")
    if "heat" in cause_cfg.tags:
        tags.add("heat")
    if "water" in cause_cfg.tags:
        tags.add("water")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
usable_repair(E, R) :- repair_for(E, R).

valid(Ev, E, C, S) :- event(Ev), exhibit(E), cause(C), suspect(S),
                      susceptible(E, C),
                      tool_of(C, T),
                      has_tool(S, T),
                      usable_repair(E, _).

culprit(S) :- chosen_cause(C), chosen_suspect(S), tool_of(C, T), has_tool(S, T).
story_ok   :- chosen_exhibit(E), chosen_cause(C), chosen_suspect(S),
              susceptible(E, C), culprit(S), usable_repair(E, _).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for event_id in EVENTS:
        lines.append(asp.fact("event", event_id))
    for exhibit_id, exhibit in EXHIBITS.items():
        lines.append(asp.fact("exhibit", exhibit_id))
        for cause_id in sorted(exhibit.susceptible):
            lines.append(asp.fact("susceptible", exhibit_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("tool_of", cause_id, cause.tool))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for tag in sorted(suspect.tool_tags):
            lines.append(asp.fact("has_tool", suspect_id, tag))
    for exhibit_id in EXHIBITS:
        repair_id = select_repair(exhibit_id)
        if repair_id:
            lines.append(asp.fact("repair_for", exhibit_id, repair_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_culprit(params: StoryParams) -> list[str]:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_exhibit", params.exhibit),
            asp.fact("chosen_cause", params.cause),
            asp.fact("chosen_suspect", params.suspect),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show culprit/1.\n#show story_ok/0."))
    culprits = [s for (s,) in asp.atoms(model, "culprit")]
    ok = asp.atoms(model, "story_ok")
    return culprits if ok else []


def outcome_ok(params: StoryParams) -> bool:
    if params.exhibit not in EXHIBITS or params.cause not in CAUSES or params.suspect not in SUSPECTS:
        return False
    if params.cause not in EXHIBITS[params.exhibit].susceptible:
        return False
    if not suspect_can_cause(params.suspect, params.cause):
        return False
    return select_repair(params.exhibit) == params.repair


CURATED = [
    StoryParams(
        event="fair",
        exhibit="wax_dragon",
        cause="heat_lamp",
        suspect="stage_helper",
        repair="cool_and_reshape",
        investigator_name="Lina",
        investigator_gender="girl",
        maker_name="Owen",
        maker_gender="boy",
        host_type="teacher",
    ),
    StoryParams(
        event="library",
        exhibit="ice_castle",
        cause="warm_vent",
        suspect="caretaker",
        repair="move_and_rebuild",
        investigator_name="Max",
        investigator_gender="boy",
        maker_name="Ava",
        maker_gender="girl",
        host_type="teacher",
    ),
    StoryParams(
        event="garden",
        exhibit="clay_turtle",
        cause="sprinkler",
        suspect="gardener",
        repair="pat_and_dry",
        investigator_name="Nora",
        investigator_gender="girl",
        maker_name="Finn",
        maker_gender="boy",
        host_type="teacher",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A gentle whodunit story world about a transformed display at an event."
    )
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--host", choices=["mother", "father", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.exhibit and args.cause:
        exhibit = EXHIBITS[args.exhibit]
        cause = CAUSES[args.cause]
        if args.cause not in exhibit.susceptible:
            raise StoryError(explain_combo_rejection(exhibit, cause))
    if args.suspect and args.cause:
        suspect = SUSPECTS[args.suspect]
        cause = CAUSES[args.cause]
        if not suspect_can_cause(args.suspect, args.cause):
            raise StoryError(explain_suspect_rejection(suspect, cause))

    combos = [
        combo
        for combo in valid_combos()
        if (args.event is None or combo[0] == args.event)
        and (args.exhibit is None or combo[1] == args.exhibit)
        and (args.cause is None or combo[2] == args.cause)
        and (args.suspect is None or combo[3] == args.suspect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    event_id, exhibit_id, cause_id, suspect_id = rng.choice(sorted(combos))
    repair_id = select_repair(exhibit_id)
    if repair_id is None:
        raise StoryError("(No valid repair exists for that exhibit.)")

    investigator_name, investigator_gender = _pick_child(rng)
    maker_name, maker_gender = _pick_child(rng, avoid=investigator_name)
    host_type = args.host or rng.choice(["mother", "father", "teacher"])

    return StoryParams(
        event=event_id,
        exhibit=exhibit_id,
        cause=cause_id,
        suspect=suspect_id,
        repair=repair_id,
        investigator_name=investigator_name,
        investigator_gender=investigator_gender,
        maker_name=maker_name,
        maker_gender=maker_gender,
        host_type=host_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        event_cfg = EVENTS[params.event]
        exhibit_cfg = EXHIBITS[params.exhibit]
        cause_cfg = CAUSES[params.cause]
        suspect_cfg = SUSPECTS[params.suspect]
        repair_cfg = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if params.cause not in exhibit_cfg.susceptible:
        raise StoryError(explain_combo_rejection(exhibit_cfg, cause_cfg))
    if not suspect_can_cause(params.suspect, params.cause):
        raise StoryError(explain_suspect_rejection(suspect_cfg, cause_cfg))
    if select_repair(params.exhibit) != params.repair:
        raise StoryError("(Invalid repair for this exhibit.)")

    world = tell(
        event_cfg=event_cfg,
        exhibit_cfg=exhibit_cfg,
        cause_cfg=cause_cfg,
        suspect_cfg=suspect_cfg,
        repair_cfg=repair_cfg,
        investigator_name=params.investigator_name,
        investigator_gender=params.investigator_gender,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        host_type=params.host_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)

    for params in cases:
        py_ok = outcome_ok(params)
        asp_out = asp_culprit(params)
        asp_ok = bool(asp_out)
        if py_ok != asp_ok:
            rc = 1
            print(f"MISMATCH outcome for {params}: python={py_ok} asp={asp_ok}")
            break
        if py_ok and asp_out != [params.suspect]:
            rc = 1
            print(f"MISMATCH culprit for {params}: asp={asp_out}")
            break

    try:
        sample = generate(CURATED[0])
        if not sample.story or "slag" not in sample.story.lower() or "event" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story text missing required elements.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    if rc == 0:
        print(f"OK: ASP and Python agree on {len(cases)} checked scenarios.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show culprit/1.\n#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (event, exhibit, cause, suspect) combos:\n")
        for event_id, exhibit_id, cause_id, suspect_id in combos:
            print(f"  {event_id:8} {exhibit_id:12} {cause_id:10} {suspect_id}")
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
            header = f"### {p.event}: {p.exhibit} changed by {p.cause} ({p.suspect})"
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
