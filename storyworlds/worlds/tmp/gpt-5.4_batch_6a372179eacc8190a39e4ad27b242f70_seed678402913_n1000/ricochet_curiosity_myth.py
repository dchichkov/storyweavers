#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ricochet_curiosity_myth.py
=====================================================

A small myth-flavored storyworld about curiosity, a bright little object, and
the lesson that questions can be followed safely.

The domain:
- A curious child in a shrine-like place wants to flick a hard little object at
  a hard surface just to hear and see it ricochet.
- A guide predicts that the ricochet could strike something delicate nearby.
- In some stories the child listens before throwing anything.
- In others the child acts first, and the guide must contain the near-miss.
- If the guide is too late or chooses a weak response, a small sacred thing is
  chipped or spilled, and the child helps mend what curiosity disturbed.

The world model is intentionally narrow. A story is only valid when:
- the chosen object is hard enough to bounce,
- the chosen surface is hard enough to send it back,
- the nearby thing is delicate enough to be harmed by a ricochet.

The inline ASP twin mirrors both the validity gate and the outcome logic.
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "priestess", "guide_f"}
        male = {"boy", "father", "man", "keeper", "guide_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Sanctuary:
    id: str
    name: str
    opening: str
    sacred_surface_line: str
    safe_place_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Missile:
    id: str
    label: str
    phrase: str
    hard: bool = True
    shine: str = ""
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    rebounds: bool = True
    sound: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    phrase: str
    delicate: bool = True
    severity: int = 1
    harm: str = ""
    mending: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeTest:
    id: str
    phrase: str
    method: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
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


def _r_ricochet(world: World) -> list[str]:
    missile = world.get("missile")
    surface = world.get("surface")
    risk = world.get("risk")
    child = world.get("child")
    if missile.meters["airborne"] < THRESHOLD:
        return []
    if not surface.attrs.get("rebounds"):
        return []
    sig = ("ricochet", missile.id, surface.id, risk.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    missile.meters["ricochet"] += 1
    risk.meters["threatened"] += 1
    child.memes["fear"] += 1
    child.memes["wonder"] += 1
    if risk.type == "lamp":
        world.get("hall").meters["danger"] += 1
    return ["__ricochet__"]


CAUSAL_RULES = [
    Rule(name="ricochet", tag="physical", apply=_r_ricochet),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def can_ricochet(missile: Missile, surface: Surface) -> bool:
    return missile.hard and surface.rebounds


def risk_at_stake(risk: Risk) -> bool:
    return risk.delicate


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(risk: Risk, delay: int) -> int:
    return risk.severity + delay


def is_contained(response: Response, risk: Risk, delay: int) -> bool:
    return response.power >= severity_of(risk, delay)


def predict_ricochet(world: World) -> dict:
    sim = world.copy()
    sim.get("missile").meters["airborne"] += 1
    propagate(sim, narrate=False)
    return {
        "ricochet": sim.get("missile").meters["ricochet"] >= THRESHOLD,
        "threatened": sim.get("risk").meters["threatened"] >= THRESHOLD,
        "danger": sim.get("hall").meters["danger"],
    }


def _do_throw(world: World) -> None:
    world.get("missile").meters["airborne"] += 1
    propagate(world, narrate=False)


def myth_opening(world: World, child: Entity, guide: Entity, sanctuary: Sanctuary) -> None:
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{sanctuary.opening} In that place walked {child.id}, a child whose questions "
        f"seemed to wake before the birds did."
    )
    world.say(
        f"Near {child.pronoun('object')} moved {guide.id}, the old {guide.label_word}, "
        f"who believed that good questions should be guided, not crushed."
    )
    world.say(sanctuary.sacred_surface_line)


def lure(world: World, child: Entity, missile: Missile, surface: Surface, risk: Risk) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"That morning {child.id} found {missile.phrase}, bright with {missile.shine}. "
        f"When {child.pronoun()} looked at {surface.phrase}, a thought leapt into "
        f"{child.pronoun('possessive')} mind: what song would the little thing make "
        f"if it struck and flew back in a ricochet?"
    )
    world.say(
        f"Beside {surface.phrase} rested {risk.phrase}, delicate and still, waiting "
        f"for gentle hands rather than flying stones."
    )


def warning(world: World, child: Entity, guide: Entity, missile: Missile, surface: Surface, risk: Risk) -> None:
    pred = predict_ricochet(world)
    world.facts["predicted_danger"] = pred["danger"]
    child.memes["tension"] += 1
    world.say(
        f'{guide.id} saw the thought on {child.id}\'s face and said, '
        f'"Little seeker, hard things bounce from hard things. If {missile.label} '
        f"strikes {surface.label}, it may ricochet into {risk.phrase}." 
        f'"'
    )
    if pred["danger"] >= THRESHOLD:
        world.say(
            f'"And if the lamp spills," {guide.id} added, "a room of prayer can become '
            f'a room of smoke."'
        )
    else:
        world.say(
            f'"Curiosity is a torch," {guide.id} said, "but a torch needs a careful hand."'
        )


def back_down(world: World, child: Entity, guide: Entity) -> None:
    child.memes["restraint"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} closed {child.pronoun('possessive')} fingers around the little object, "
        f"then opened them again. The question stayed, but the throwing did not."
    )
    world.say(
        f'"Then show me a wiser way," {child.pronoun()} said, and {guide.id} smiled as if '
        f"the dawn itself had answered."
    )


def defy(world: World, child: Entity, missile: Missile) -> None:
    child.memes["impulse"] += 1
    world.say(
        f"But curiosity ran faster than caution. Before another word could settle, "
        f"{child.id} flicked {missile.phrase} from {child.pronoun('possessive')} thumb."
    )


def throw_and_ricochet(world: World, child: Entity, missile: Missile, surface: Surface, risk: Risk) -> None:
    _do_throw(world)
    sound = surface.sound or "ting"
    world.say(
        f"{sound}! It struck {surface.phrase}, and at once it sprang away in a bright "
        f"ricochet. For one breath {child.id} thought the sound was beautiful."
    )
    world.say(
        f"Then the little shining arc flew straight toward {risk.phrase}, and beauty "
        f"turned sharp with danger."
    )


def contain(world: World, guide: Entity, response: Response, risk: Risk) -> None:
    world.get("risk").meters["threatened"] = 0.0
    world.get("hall").meters["danger"] = 0.0
    body = response.text.replace("{risk}", risk.label)
    world.say(f"{guide.id} moved like someone answering an old prayer and {body}.")
    world.say(
        f"The small object clattered harmlessly to the floor. {guide.id} let the silence "
        f"settle until even {child_name(world)} could hear {child_pronoun(world, 'possessive')} own heart slow down."
    )


def damage(world: World, response: Response, risk: Risk) -> None:
    world.get("risk").meters["damaged"] += 1
    body = response.fail.replace("{risk}", risk.label)
    world.say(body)
    world.say(risk.harm)


def mend(world: World, child: Entity, guide: Entity, risk: Risk) -> None:
    child.memes["remorse"] += 1
    child.memes["learning"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"{child.id}'s face grew hot. {guide.id} did not thunder. {guide.pronoun().capitalize()} "
        f"only placed the little object in {child.pronoun('possessive')} palm and asked "
        f"{child.pronoun('object')} to look carefully at what curiosity had touched."
    )
    world.say(risk.mending)


def lesson(world: World, child: Entity, guide: Entity, missile: Missile) -> None:
    child.memes["learning"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    world.say(
        f'"Questions are holy," {guide.id} said softly. "But you must send them out in ways '
        f'that do not wound the world that answers them."'
    )
    world.say(
        f"{child.id} nodded and turned {missile.label} over in {child.pronoun('possessive')} hand, "
        f"as if it had become heavier with meaning."
    )


def safe_demonstration(world: World, child: Entity, guide: Entity, safe_test: SafeTest) -> None:
    child.memes["joy"] += 1
    child.memes["understanding"] += 1
    child.memes["curiosity"] += 1
    world.say(safe_test.method)
    world.say(
        f"Soon {child.id} was laughing, not because danger had brushed by, but because "
        f"the answer had come in a kinder shape."
    )
    world.say(safe_test.ending_image)


def child_name(world: World) -> str:
    return world.facts["child"].id


def child_pronoun(world: World, case: str = "subject") -> str:
    return world.facts["child"].pronoun(case)


def tell(
    sanctuary: Sanctuary,
    missile: Missile,
    surface: Surface,
    risk: Risk,
    safe_test: SafeTest,
    response: Response,
    child_name_value: str = "Iria",
    child_type: str = "girl",
    guide_name: str = "Theron",
    guide_type: str = "keeper",
    temper: str = "hasty",
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(id=child_name_value, kind="character", type=child_type, role="child", label=child_name_value))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide", label="keeper"))
    world.add(Entity(id="hall", type="hall", label="the hall"))
    world.add(Entity(id="missile", type="missile", label=missile.label, phrase=missile.phrase, attrs={"hard": missile.hard}))
    world.add(Entity(id="surface", type="surface", label=surface.label, phrase=surface.phrase, attrs={"rebounds": surface.rebounds}))
    risk_type = "lamp" if "lamp" in risk.tags else "risk"
    world.add(Entity(id="risk", type=risk_type, label=risk.label, phrase=risk.phrase))

    myth_opening(world, child, guide, sanctuary)
    lure(world, child, missile, surface, risk)

    world.para()
    warning(world, child, guide, missile, surface, risk)

    if temper == "patient":
        back_down(world, child, guide)
        world.para()
        lesson(world, child, guide, missile)
        safe_demonstration(world, child, guide, safe_test)
        outcome = "averted"
    else:
        defy(world, child, missile)
        world.para()
        throw_and_ricochet(world, child, missile, surface, risk)

        world.para()
        if is_contained(response, risk, delay):
            contain(world, guide, response, risk)
            lesson(world, child, guide, missile)
            world.para()
            safe_demonstration(world, child, guide, safe_test)
            outcome = "contained"
        else:
            damage(world, response, risk)
            mend(world, child, guide, risk)
            world.para()
            lesson(world, child, guide, missile)
            safe_demonstration(world, child, guide, safe_test)
            outcome = "marred"

    world.facts.update(
        child=child,
        guide=guide,
        sanctuary=sanctuary,
        missile_cfg=missile,
        surface_cfg=surface,
        risk_cfg=risk,
        safe_test=safe_test,
        response=response,
        outcome=outcome,
        delay=delay,
        thrown=temper != "patient",
        damaged=world.get("risk").meters["damaged"] >= THRESHOLD,
        ricocheted=world.get("missile").meters["ricochet"] >= THRESHOLD,
    )
    return world


SANCTUARIES = {
    "sun_temple": Sanctuary(
        id="sun_temple",
        name="the House of the Sun",
        opening="In the age when the hills still traded stories with the sky, there stood the House of the Sun on a white ridge.",
        sacred_surface_line="Bronze shields hung there for festival days, and the floor remembered the feet of singers.",
        safe_place_line="Beyond the steps stood a sand court where teachers tested sounds without harming anything.",
        tags={"temple", "sun"},
    ),
    "moon_court": Sanctuary(
        id="moon_court",
        name="the Court of the Moon",
        opening="In the silver years, when moonlight was said to pool in stone basins, there stood the Court of the Moon among cypress trees.",
        sacred_surface_line="Marble arches gleamed there, and the night wind liked to whisper through them.",
        safe_place_line="At the edge of the court lay a ring of soft sand where lessons were tried before they were trusted.",
        tags={"moon", "court"},
    ),
    "thunder_stoa": Sanctuary(
        id="thunder_stoa",
        name="the Stoa of Thunder",
        opening="In the old days, when thunder was still called a god's drumbeat, a long stoa stood above the sea-cliffs.",
        sacred_surface_line="Basalt steps ran dark as storm clouds, and bronze bowls waited for offerings.",
        safe_place_line="Near the back wall rested a practice board and a tray of river sand for careful hands.",
        tags={"thunder", "sea"},
    ),
}

MISSILES = {
    "bronze_bead": Missile(
        id="bronze_bead",
        label="the bronze bead",
        phrase="a bronze bead",
        hard=True,
        shine="a drop of trapped sunrise",
        tags={"bronze", "ricochet"},
    ),
    "river_pebble": Missile(
        id="river_pebble",
        label="the river pebble",
        phrase="a smooth river pebble",
        hard=True,
        shine="a soft gray sheen",
        tags={"stone", "ricochet"},
    ),
    "shell_disc": Missile(
        id="shell_disc",
        label="the shell disc",
        phrase="a flat shell disc",
        hard=True,
        shine="a pale moon-glimmer",
        tags={"shell", "ricochet"},
    ),
    "fig": Missile(
        id="fig",
        label="the fig",
        phrase="a ripe fig",
        hard=False,
        shine="purple sweetness",
        tags={"fruit"},
    ),
}

SURFACES = {
    "bronze_shield": Surface(
        id="bronze_shield",
        label="the bronze shield",
        phrase="the hanging bronze shield",
        rebounds=True,
        sound="Tang",
        tags={"bronze", "echo"},
    ),
    "basalt_step": Surface(
        id="basalt_step",
        label="the basalt step",
        phrase="the edge of a basalt step",
        rebounds=True,
        sound="Tik",
        tags={"stone", "echo"},
    ),
    "marble_arch": Surface(
        id="marble_arch",
        label="the marble arch",
        phrase="the smooth marble arch",
        rebounds=True,
        sound="Ting",
        tags={"marble", "echo"},
    ),
    "moss_bank": Surface(
        id="moss_bank",
        label="the moss bank",
        phrase="the mossy bank by the wall",
        rebounds=False,
        sound="thup",
        tags={"moss"},
    ),
}

RISKS = {
    "honey_lamp": Risk(
        id="honey_lamp",
        label="the honey lamp",
        phrase="a shallow honey lamp with a floating wick",
        delicate=True,
        severity=2,
        harm="The lamp tipped, and a golden thread of oil slid across the stone before the flame went out.",
        mending="Together they wiped the oil away, trimmed a fresh wick, and relit the lamp with steadier hands.",
        tags={"lamp", "fire"},
    ),
    "ink_bowl": Risk(
        id="ink_bowl",
        label="the ink bowl",
        phrase="a blue bowl of ink for copying hymns",
        delicate=True,
        severity=1,
        harm="The bowl rang, jumped, and spilled a dark fan of ink over the hymn cloth beside it.",
        mending="They carried water, dabbed the cloth clean as best they could, and copied the blurred lines anew before noon.",
        tags={"ink", "craft"},
    ),
    "swallow_nest": Risk(
        id="swallow_nest",
        label="the swallow nest",
        phrase="a swallow nest tucked under the eaves",
        delicate=True,
        severity=2,
        harm="The nest shook, and the mother swallow burst into the air in a panic, circling the beams above them.",
        mending="So they stood back in silence until the bird returned, and later they tied fresh straw below the eaves where the nest had loosened.",
        tags={"bird", "nest"},
    ),
}

SAFE_TESTS = {
    "sand_tray": SafeTest(
        id="sand_tray",
        phrase="a tray of sand",
        method="Then the guide led the child to a tray of sand and set up a little board beside it, so a tossed object could strike, ricochet, and fall harmlessly where it could hurt no lamp, bowl, or nest.",
        ending_image="By the end, small arcs marked the sand like tiny comets, and the lesson shone brighter than the bead itself.",
        tags={"sand", "safe_test"},
    ),
    "echo_drum": SafeTest(
        id="echo_drum",
        phrase="an echo drum",
        method="Then the guide brought out an old echo drum and showed how a tap with a padded stick could send a bright answer back without any flying stone at all.",
        ending_image="The drum spoke, the arches answered, and the child listened with both delight and care.",
        tags={"drum", "safe_test"},
    ),
    "reed_target": SafeTest(
        id="reed_target",
        phrase="a reed target",
        method="Then the guide planted a reed target in a patch of soft earth and let the child test angles there, where every bounce died in the ground like rain.",
        ending_image="Soon the soft earth was pricked with neat little marks, and curiosity had become patient skill.",
        tags={"target", "safe_test"},
    ),
}

RESPONSES = {
    "cloak_sweep": Response(
        id="cloak_sweep",
        sense=3,
        power=3,
        text="swept a fold of his cloak beneath the flying bead, changing its path before it could strike {risk}",
        fail="{guide} tried to sweep the bead aside with a fold of cloth, but it slipped past and struck {risk}",
        qa_text="swept the flying object aside with a quick fold of the cloak",
        tags={"cloak", "safety"},
    ),
    "open_palm": Response(
        id="open_palm",
        sense=2,
        power=2,
        text="caught the bead's second hop in an open palm before it could hit {risk}",
        fail="{guide} reached with an open palm, but the object skipped once too fast and clipped {risk}",
        qa_text="caught the second hop in an open palm",
        tags={"hand", "safety"},
    ),
    "warning_only": Response(
        id="warning_only",
        sense=1,
        power=1,
        text="only shouted a warning",
        fail="The warning came first, but the object was already too fast and struck {risk}",
        qa_text="only shouted a warning",
        tags={"warning"},
    ),
}


@dataclass
class StoryParams:
    sanctuary: str
    missile: str
    surface: str
    risk: str
    safe_test: str
    response: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    temper: str
    delay: int = 0
    seed: Optional[int] = None


CHILD_NAMES_GIRL = ["Iria", "Nysa", "Daphne", "Lysa", "Mira", "Thaleia"]
CHILD_NAMES_BOY = ["Aren", "Theron", "Pylos", "Dorian", "Iasos", "Leander"]
GUIDE_NAMES = ["Theron", "Melia", "Oren", "Lyra", "Sima", "Cassian"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for sanctuary in SANCTUARIES:
        for missile_id, missile in MISSILES.items():
            for surface_id, surface in SURFACES.items():
                for risk_id, risk in RISKS.items():
                    if can_ricochet(missile, surface) and risk_at_stake(risk):
                        combos.append((sanctuary, missile_id, surface_id, risk_id))
    return combos


KNOWLEDGE = {
    "ricochet": [
        (
            "What does ricochet mean?",
            "Ricochet means a little object hits something hard and bounces away in a new direction. That bounce can be surprising, so you should only try it in a safe place.",
        )
    ],
    "lamp": [
        (
            "Why is an oil lamp delicate?",
            "An oil lamp can tip, spill, or break if something hits it. If it spills while lit, it can make a bigger danger.",
        )
    ],
    "ink": [
        (
            "Why can ink make a mess?",
            "Ink is a dark liquid that spreads fast across cloth or paper. Once it spills, it can stain things and spoil careful work.",
        )
    ],
    "bird": [
        (
            "Why should we not scare a bird at its nest?",
            "A nest is where birds rest and care for their eggs or babies. Loud surprises can frighten the parent and make the nest less safe.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces back after it hits a wall or another hard surface. That is why big stone places sometimes seem to answer you.",
        )
    ],
    "sand": [
        (
            "Why is sand a safer place for a bouncing test?",
            "Sand is soft, so it slows and stops little objects quickly. That makes it a good place to learn without breaking delicate things.",
        )
    ],
    "drum": [
        (
            "How can a drum answer a question about sound?",
            "A drum lets you hear how sound travels and comes back without throwing anything hard. It is a safer way to explore echoes.",
        )
    ],
    "target": [
        (
            "Why use a practice target?",
            "A practice target gives curious hands a place to aim on purpose. It helps people test an idea where nothing delicate is nearby.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ricochet", "echo", "lamp", "ink", "bird", "sand", "drum", "target"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    sanctuary = f["sanctuary"]
    risk = f["risk_cfg"]
    missile = f["missile_cfg"]
    safe_test = f["safe_test"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a short myth-like story for a 3-to-5-year-old that includes the word "ricochet" and centers on curiosity guided into wisdom.',
            f"Tell a gentle myth where a curious child in {sanctuary.name} wants to make {missile.phrase} ricochet, but listens to an elder before anything is harmed.",
            f"Write a small mythic story where a guide shows {child.id} a safer experiment with {safe_test.phrase}, so the answer comes without breaking {risk.label}.",
        ]
    if outcome == "contained":
        return [
            f'Write a short myth-like story for a 3-to-5-year-old that includes the word "ricochet" and a near miss caused by curiosity.',
            f"Tell a mythic story where a curious child acts too fast, a little object ricochets toward {risk.phrase}, and a calm elder saves the day.",
            f"Write a story in a shrine setting where curiosity nearly causes harm, but the ending shows a safer way to learn.",
        ]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the word "ricochet" and shows curiosity learning responsibility after a mistake.',
        f"Tell a myth where a child sends {missile.phrase} into a ricochet near {risk.phrase}, and afterward helps mend what was disturbed.",
        f"Write a gentle cautionary myth with a small sacred accident, a calm elder, and an ending that turns curiosity into careful skill.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    sanctuary = f["sanctuary"]
    missile = f["missile_cfg"]
    surface = f["surface_cfg"]
    risk = f["risk_cfg"]
    safe_test = f["safe_test"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {guide.id}, the old {guide.label_word} in {sanctuary.name}. The story follows how curiosity was guided toward wisdom.",
        ),
        (
            f"What did {child.id} want to find out?",
            f"{child.id} wanted to know what sound and motion {missile.label} would make against {surface.label}. That is why the child imagined a bright ricochet.",
        ),
        (
            f"Why did {guide.id} warn {child.id}?",
            f"{guide.id} knew that hard things bounce from hard things and may fly somewhere unexpected. In this story, that meant {missile.label} could ricochet into {risk.phrase}.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What did {child.id} do after the warning?",
                f"{child.id} stopped before throwing anything and asked for a wiser way to learn. The child kept the question, but chose not to risk {risk.label}.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a safe lesson using {safe_test.phrase}. The final image shows curiosity still alive, but shaped into care.",
            )
        )
    elif outcome == "contained":
        qa.append(
            (
                "What happened when the object flew back?",
                f"It struck {surface.label} and sprang away in a ricochet toward {risk.phrase}. The danger came from the bounce changing direction so quickly.",
            )
        )
        qa.append(
            (
                f"How did {guide.id} stop the danger?",
                f"{guide.pronoun().capitalize()} {response.qa_text}. That quick move kept {risk.label} safe and gave the child time to understand what nearly happened.",
            )
        )
        qa.append(
            (
                "What changed by the end of the story?",
                f"At first curiosity rushed ahead of caution. By the end, {child.id} was still curious, but now learned through {safe_test.phrase} instead of a risky throw.",
            )
        )
    else:
        qa.append(
            (
                f"Was {risk.label} harmed?",
                f"Yes. {risk.harm} Afterward, the child had to look carefully at the result and help put things right.",
            )
        )
        qa.append(
            (
                f"How did {guide.id} react after the accident?",
                f"{guide.id} stayed calm and taught instead of raging. That calm made room for {child.id} to feel sorry, help mend the harm, and learn a wiser habit.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a safer demonstration using {safe_test.phrase}. The ending proves that curiosity did not disappear; it became more careful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ricochet", "echo"} | set(f["risk_cfg"].tags)
    tags |= set(f["safe_test"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for ent in world.entities.values():
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        sanctuary="sun_temple",
        missile="bronze_bead",
        surface="bronze_shield",
        risk="honey_lamp",
        safe_test="sand_tray",
        response="cloak_sweep",
        child_name="Iria",
        child_type="girl",
        guide_name="Theron",
        guide_type="keeper",
        temper="hasty",
        delay=0,
    ),
    StoryParams(
        sanctuary="moon_court",
        missile="river_pebble",
        surface="marble_arch",
        risk="ink_bowl",
        safe_test="echo_drum",
        response="open_palm",
        child_name="Aren",
        child_type="boy",
        guide_name="Lyra",
        guide_type="priestess",
        temper="patient",
        delay=0,
    ),
    StoryParams(
        sanctuary="thunder_stoa",
        missile="shell_disc",
        surface="basalt_step",
        risk="swallow_nest",
        safe_test="reed_target",
        response="open_palm",
        child_name="Daphne",
        child_type="girl",
        guide_name="Cassian",
        guide_type="keeper",
        temper="hasty",
        delay=1,
    ),
]


def explain_rejection(missile: Missile, surface: Surface, risk: Risk) -> str:
    if not missile.hard:
        return (
            f"(No story: {missile.phrase} is too soft to make a true ricochet. "
            f"This world needs a hard little object and a hard surface.)"
        )
    if not surface.rebounds:
        return (
            f"(No story: {surface.phrase} will only swallow the throw instead of sending it back. "
            f"Without a ricochet, this myth has no sharp turn.)"
        )
    if not risk.delicate:
        return (
            f"(No story: {risk.phrase} is not delicate enough to be troubled by the bounce.)"
        )
    return "(No story: that combination does not create a believable ricochet hazard.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.temper == "patient":
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], RISKS[params.risk], params.delay) else "marred"


ASP_RULES = r"""
% --- validity gate ---------------------------------------------------------
hazard(M, S, R) :- hard(M), rebounds(S), delicate(R).
sensible(Rs) :- response(Rs), sense(Rs, N), sense_min(Min), N >= Min.
valid(T, M, S, R) :- sanctuary(T), missile(M), surface(S), risk(R), hazard(M, S, R).

% --- outcome model ---------------------------------------------------------
outcome(averted) :- temper(patient).
severity(V + D) :- chosen_risk(R), risk_severity(R, V), delay(D).
contained :- chosen_response(Rs), power(Rs, P), severity(N), P >= N.
outcome(contained) :- temper(hasty), contained.
outcome(marred) :- temper(hasty), not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SANCTUARIES:
        lines.append(asp.fact("sanctuary", sid))
    for mid, missile in MISSILES.items():
        lines.append(asp.fact("missile", mid))
        if missile.hard:
            lines.append(asp.fact("hard", mid))
    for sid, surface in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        if surface.rebounds:
            lines.append(asp.fact("rebounds", sid))
    for rid, risk in RISKS.items():
        lines.append(asp.fact("risk", rid))
        if risk.delicate:
            lines.append(asp.fact("delicate", rid))
        lines.append(asp.fact("risk_severity", rid, risk.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_risk", params.risk),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("temper", params.temper),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in validity gate:")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "ricochet" not in sample.story.lower():
            raise StoryError("smoke test failed: generated story missing expected text")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-flavored storyworld: curiosity, a ricochet, and a safer way to learn."
    )
    ap.add_argument("--sanctuary", choices=SANCTUARIES)
    ap.add_argument("--missile", choices=MISSILES)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--safe-test", dest="safe_test", choices=SAFE_TESTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--temper", choices=["patient", "hasty"])
    ap.add_argument("--child-type", dest="child_type", choices=["girl", "boy"])
    ap.add_argument("--guide-type", dest="guide_type", choices=["keeper", "priestess"])
    ap.add_argument("--child-name")
    ap.add_argument("--guide-name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how late the guide's move is")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child_name(rng: random.Random, child_type: str) -> str:
    pool = CHILD_NAMES_GIRL if child_type == "girl" else CHILD_NAMES_BOY
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.missile and args.surface and args.risk:
        missile = MISSILES[args.missile]
        surface = SURFACES[args.surface]
        risk = RISKS[args.risk]
        if not (can_ricochet(missile, surface) and risk_at_stake(risk)):
            raise StoryError(explain_rejection(missile, surface, risk))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.sanctuary is None or combo[0] == args.sanctuary)
        and (args.missile is None or combo[1] == args.missile)
        and (args.surface is None or combo[2] == args.surface)
        and (args.risk is None or combo[3] == args.risk)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    sanctuary, missile, surface, risk = rng.choice(sorted(combos))
    safe_test = args.safe_test or rng.choice(sorted(SAFE_TESTS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    temper = args.temper or rng.choice(["patient", "hasty", "hasty"])
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    guide_type = args.guide_type or rng.choice(["keeper", "priestess"])
    child_name = args.child_name or _pick_child_name(rng, child_type)
    guide_name = args.guide_name or rng.choice([n for n in GUIDE_NAMES if n != child_name])

    return StoryParams(
        sanctuary=sanctuary,
        missile=missile,
        surface=surface,
        risk=risk,
        safe_test=safe_test,
        response=response,
        child_name=child_name,
        child_type=child_type,
        guide_name=guide_name,
        guide_type=guide_type,
        temper=temper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        sanctuary = SANCTUARIES[params.sanctuary]
        missile = MISSILES[params.missile]
        surface = SURFACES[params.surface]
        risk = RISKS[params.risk]
        safe_test = SAFE_TESTS[params.safe_test]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from None

    if not (can_ricochet(missile, surface) and risk_at_stake(risk)):
        raise StoryError(explain_rejection(missile, surface, risk))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.temper not in {"patient", "hasty"}:
        raise StoryError("(Temper must be 'patient' or 'hasty'.)")
    if params.delay not in {0, 1}:
        raise StoryError("(Delay must be 0 or 1.)")

    world = tell(
        sanctuary=sanctuary,
        missile=missile,
        surface=surface,
        risk=risk,
        safe_test=safe_test,
        response=response,
        child_name_value=params.child_name,
        child_type=params.child_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        temper=params.temper,
        delay=params.delay,
    )

    # Patch response fail text with guide label for story-grounded rendering.
    world.facts["response"] = Response(
        id=response.id,
        sense=response.sense,
        power=response.power,
        text=response.text,
        fail=response.fail.replace("{guide}", world.facts["guide"].id),
        qa_text=response.qa_text,
        tags=set(response.tags),
    )

    if world.facts["outcome"] == "marred":
        story = world.render().replace("{guide}", world.facts["guide"].id)
    else:
        story = world.render()

    return StorySample(
        params=params,
        story=story,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sanctuary, missile, surface, risk) combos:\n")
        for sanctuary, missile, surface, risk in combos:
            print(f"  {sanctuary:13} {missile:13} {surface:13} {risk}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.missile} at {p.surface} near {p.risk} "
                f"({p.sanctuary}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
