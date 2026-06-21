#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py
========================================================================

A standalone story world for a child-facing pirate-style cautionary tale with a
celebrity at the center of the temptation.

Premise
-------
Two children are playing pirates at a harbor festival. A celebrity pirate
performer is about to appear, and one child wants to take a dangerous shortcut
to reach the front faster. The other child warns that the shortcut is unsafe.
Sometimes the warning is enough and the shortcut is never tried. Sometimes the
child tries it anyway, slips, and a grown-up must help. In the happy ending they
still reach the show by the safe route. In the sadder cautionary ending they are
safe, but wet and late, and they miss the celebrity.

Run it
------
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py --shortcut dinghy
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py --response shout_only
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4/celebrity_cautionary_conflict_pirate_tale.py --verify
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
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    safe_route: str
    finish: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Celebrity:
    id: str
    label: str
    title: str
    entrance: str
    wave: str
    prize: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Shortcut:
    id: str
    label: str
    phrase: str
    hazard: str
    severity: int
    surface: str
    slip_text: str
    danger_text: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Response:
    id: str
    sense: int
    power: int
    works_for: set[str]
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        return [e for e in self.entities.values() if e.role in ("instigator", "cautioner")]

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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("instigator")
    route = world.entities.get("route")
    if child is None or route is None:
        return out
    if child.meters["slipping"] < THRESHOLD:
        return out
    sig = ("danger", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("harbor").meters["danger"] += 1
    child.meters["at_edge"] += 1
    if route.attrs.get("hazard") == "water":
        child.meters["wet"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__danger__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger", tag="physical", apply=_r_danger),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def hazard_at_risk(setting: Setting, shortcut: Shortcut) -> bool:
    return shortcut.risky and shortcut.id in setting.affords


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def event_severity(shortcut: Shortcut, delay: int) -> int:
    return shortcut.severity + delay


def is_contained(response: Response, shortcut: Shortcut, delay: int) -> bool:
    if shortcut.hazard not in response.works_for:
        return False
    return response.power >= event_severity(shortcut, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_trouble(world: World, shortcut_id: str) -> dict:
    sim = world.copy()
    route = sim.get(shortcut_id)
    _attempt_shortcut(sim, sim.get("instigator"), route, narrate=False)
    kid = sim.get("instigator")
    return {
        "danger": sim.get("harbor").meters["danger"],
        "wet": kid.meters["wet"],
        "slipping": kid.meters["slipping"],
    }


def _attempt_shortcut(world: World, child: Entity, route: Entity, narrate: bool = True) -> None:
    child.meters["slipping"] += 1
    child.meters["off_balance"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, setting: Setting, celebrity: Celebrity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright festival morning, {a.id} and {b.id} marched beside {setting.place} "
        f"pretending to be pirates. {setting.opening}"
    )
    world.say(
        f'"Captain {a.id} and Mate {b.id}!" {a.id} shouted. '
        f'"Today we see {celebrity.title}, the celebrity pirate!"'
    )


def celebrity_need(world: World, b: Entity, setting: Setting, celebrity: Celebrity) -> None:
    world.say(
        f"At the far end of the harbor, a little stage waited with a striped flag and "
        f"a sign for {celebrity.label}. Soon {celebrity.entrance}"
    )
    world.say(
        f'{b.id} stood on tiptoe. "If we get there in time, maybe {celebrity.label} '
        f'will {celebrity.prize}," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, shortcut: Shortcut) -> None:
    a.memes["impatience"] += 1
    world.say(
        f'{a.id} pointed at {shortcut.phrase}. "There! That is the fastest way. '
        f'Real pirates do not wait in line."'
    )


def warn(world: World, b: Entity, a: Entity, shortcut: Shortcut, parent: Entity) -> None:
    pred = predict_trouble(world, "route")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if pred["wet"] >= THRESHOLD:
        extra = " If you slip there, you could splash into the cold water."
    world.say(
        f'{b.id} caught {a.id}\'s sleeve. "No, {a.id}. {shortcut.surface} is not safe, '
        f'and {parent.label_word} said we must use the marked path.{extra}"'
    )


def defy(world: World, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    a.memes["defiance"] += 1
    instigator_older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if instigator_older:
        world.say(
            f'"Do not be such a shore-sparrow," {a.id} said. Because {a.id} was '
            f'{b.pronoun("possessive")} big {"brother" if a.type == "boy" else "sister"}, '
            f'{b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(f'"Do not be such a shore-sparrow," {a.id} said, and darted toward it.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting, celebrity: Celebrity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    world.say(
        f'{a.id} looked at the wobble of the boards, then at {b.id}\'s worried face, '
        f'and stopped. "All right," {a.pronoun()} muttered. "We will take the true captain\'s path."'
    )
    world.say(
        f"They stayed beside {parent.label_word} and followed {setting.safe_route} instead."
    )
    world.say(
        f"When they reached the front, {celebrity.label} gave them a big wave, and the hurry melted out of them."
    )


def accident(world: World, a: Entity, shortcut: Shortcut) -> None:
    route = world.get("route")
    _attempt_shortcut(world, a, route)
    world.say(shortcut.slip_text)
    world.say(shortcut.danger_text)


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} cried. "{parent.label_word.capitalize()}!"')


def rescue(world: World, parent: Entity, response: Response, a: Entity, shortcut: Shortcut) -> None:
    a.meters["slipping"] = 0.0
    a.meters["at_edge"] = 0.0
    a.meters["off_balance"] = 0.0
    if shortcut.hazard != "water":
        a.meters["wet"] = 0.0
    world.get("harbor").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast and {response.text}."
    )
    world.say(
        f"In one breath the scary part was over, though {a.id}'s knees still trembled."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, shortcut: Shortcut) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke except the gulls.")
    world.say(
        f'Then {parent.label_word} knelt beside them. "I am glad you called me," '
        f'{parent.pronoun()} said softly. "Harbors are not places for rushing. '
        f'{shortcut.surface[0].upper()}{shortcut.surface[1:]} can turn a game into danger very fast."'
    )
    world.say(f'"We know," whispered {b.id} and {a.id} together.')


def safe_finish(world: World, parent: Entity, a: Entity, b: Entity, setting: Setting, celebrity: Celebrity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["safety"] += 1
    b.memes["safety"] += 1
    world.say(
        f"After that, they used {setting.safe_route}. It felt slower at first, but it felt steady under every step."
    )
    world.say(
        f"At the end of the line, {celebrity.label} leaned down, {celebrity.wave}, and "
        f"called them brave for choosing the safe way."
    )
    world.say(setting.finish)


def rescue_fail(world: World, parent: Entity, response: Response, a: Entity, shortcut: Shortcut) -> None:
    a.meters["slipping"] = 0.0
    a.meters["off_balance"] = 0.0
    a.meters["at_edge"] += 1
    if shortcut.hazard == "water":
        a.meters["wet"] += 1
    world.get("harbor").meters["danger"] += 1
    world.say(f"{parent.label_word.capitalize()} {response.fail}.")
    if shortcut.hazard == "water":
        world.say(f"{a.id} came up splashing and sputtering, soaked from shoes to sleeves.")
    else:
        world.say(f"{a.id} landed in a heap, scraped and shaking hard from the scare.")


def loss_finish(world: World, parent: Entity, a: Entity, b: Entity, celebrity: Celebrity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    a.memes["disappointment"] += 1
    b.memes["disappointment"] += 1
    world.say(
        f"{parent.label_word.capitalize()} wrapped {a.id} in a warm towel and led both children away from the edge."
    )
    world.say(
        f"By the time they were dry and calm again, the music had ended and {celebrity.label} was waving goodbye from far down the pier."
    )
    world.say(
        "They were safe, but they had missed the show. The empty little stage looked very different from the bright treasure they had been rushing toward."
    )


def quiet_lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    world.say(
        f'{parent.label_word.capitalize()} hugged them close. "No celebrity is worth a dangerous shortcut," '
        f'{parent.pronoun()} said. "Next time, even if you are excited, your feet must listen before your hurry does."'
    )
    world.say(
        f"{a.id} nodded against {parent.pronoun('possessive')} shoulder, and {b.id} squeezed {a.pronoun('possessive')} hand."
    )


def tell(
    setting: Setting,
    celebrity: Celebrity,
    shortcut: Shortcut,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 7,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        traits=[trait],
        age=cautioner_age,
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    harbor = world.add(Entity(id="harbor", type="place", label=setting.place))
    route = world.add(Entity(
        id="route",
        type="shortcut",
        label=shortcut.label,
        attrs={"hazard": shortcut.hazard},
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    harbor.meters["danger"] = 0.0
    a.meters["slipping"] = 0.0
    a.meters["off_balance"] = 0.0
    a.meters["at_edge"] = 0.0
    a.meters["wet"] = 0.0

    play_setup(world, a, b, setting, celebrity)
    celebrity_need(world, b, setting, celebrity)

    world.para()
    tempt(world, a, shortcut)
    warn(world, b, a, shortcut, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, parent, setting, celebrity)
        severity = 0
        contained = True
    else:
        defy(world, a, b, shortcut)
        world.para()
        accident(world, a, shortcut)
        alarm(world, b, a, parent)
        severity = event_severity(shortcut, delay)
        a.meters["severity"] = float(severity)
        contained = is_contained(response, shortcut, delay)

        world.para()
        if contained:
            rescue(world, parent, response, a, shortcut)
            lesson(world, parent, a, b, shortcut)
            world.para()
            safe_finish(world, parent, a, b, setting, celebrity)
        else:
            rescue_fail(world, parent, response, a, shortcut)
            loss_finish(world, parent, a, b, celebrity)
            quiet_lesson(world, parent, a, b)

    outcome = "averted" if averted else ("contained" if contained else "missed")
    world.facts.update(
        setting=setting,
        celebrity=celebrity,
        shortcut=shortcut,
        response=response,
        instigator=a,
        cautioner=b,
        parent=parent,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        attempted=not averted,
        slipped=not averted,
        safe_finish=outcome in {"averted", "contained"},
    )
    return world


SETTINGS = {
    "festival_pier": Setting(
        id="festival_pier",
        place="the festival pier",
        opening="The railings wore strings of paper flags, and every bench became part of their pretend ship.",
        safe_route="the painted gangway with the rope rail",
        finish="Soon the two young pirates were laughing again, boots thumping safely along the boards.",
        affords={"rope_gap", "dinghy", "crate_stack"},
        tags={"harbor", "pier"},
    ),
    "museum_wharf": Setting(
        id="museum_wharf",
        place="the old museum wharf",
        opening="A tall ship rested beside the wharf, and the children pretended its masts belonged to their own grand pirate vessel.",
        safe_route="the wide visitor ramp",
        finish="They crossed the ramp together, slow and proud, like sailors who finally knew what courage was for.",
        affords={"rope_gap", "crate_stack"},
        tags={"harbor", "ship"},
    ),
    "market_dock": Setting(
        id="market_dock",
        place="the market dock",
        opening="Fish signs swung in the breeze, and the bobbing boats made the whole place feel like a storybook harbor.",
        safe_route="the marked family walkway",
        finish="When they walked back later, they stayed in the middle of the walkway, side by side and smiling.",
        affords={"dinghy", "rope_gap"},
        tags={"harbor", "dock"},
    ),
}

CELEBRITIES = {
    "captain_star": Celebrity(
        id="captain_star",
        label="Captain Star",
        title="Captain Star",
        entrance="the celebrity pirate would step onto the stage in a shining blue coat",
        wave="tipped a feathery hat",
        prize="stamp their treasure map",
        tags={"celebrity", "pirate"},
    ),
    "ruby_beard": Celebrity(
        id="ruby_beard",
        label="Ruby Beard",
        title="Ruby Beard",
        entrance="the celebrity sea-singer would begin a jolly pirate song",
        wave="swept a bright red cape",
        prize="sign their paper flag",
        tags={"celebrity", "music"},
    ),
    "admiral_spark": Celebrity(
        id="admiral_spark",
        label="Admiral Spark",
        title="Admiral Spark",
        entrance="the celebrity captain from the picture books would ring a brass bell",
        wave="grinned and raised a toy spyglass",
        prize="draw a star beside their names",
        tags={"celebrity", "books"},
    ),
}

SHORTCUTS = {
    "rope_gap": Shortcut(
        id="rope_gap",
        label="rope gap",
        phrase="a gap in the rope barrier near the slick edge",
        hazard="water",
        severity=2,
        surface="that narrow edge by the water",
        slip_text="The boards there were shiny with spray. One quick step, and {name}'s foot skidded sideways.".replace("{name}", "instigator"),
        danger_text="Arms pinwheeling, instigator lurched toward the dark water between the pilings.",
        risky=True,
        tags={"water", "dock"},
    ),
    "dinghy": Shortcut(
        id="dinghy",
        label="dinghy",
        phrase="a little untied dinghy bumping against the dock",
        hazard="water",
        severity=2,
        surface="that bobbing little boat",
        slip_text="The dinghy jumped away under the first step as if it had its own naughty idea.",
        danger_text="With a splash and a gasp, instigator pitched over the side.",
        risky=True,
        tags={"water", "boat"},
    ),
    "crate_stack": Shortcut(
        id="crate_stack",
        label="crate stack",
        phrase="a stack of fish crates beside the stage fence",
        hazard="fall",
        severity=3,
        surface="those wobbly crates",
        slip_text="The top crate tipped the moment a small foot touched it.",
        danger_text="Instigator windmilled wildly and nearly tumbled headfirst onto the planks below.",
        risky=True,
        tags={"fall", "crates"},
    ),
    "painted_path": Shortcut(
        id="painted_path",
        label="painted fish path",
        phrase="a painted fish path on the safe boards",
        hazard="none",
        severity=0,
        surface="those painted boards",
        slip_text="",
        danger_text="",
        risky=False,
        tags={"safe"},
    ),
}

RESPONSES = {
    "grab_back": Response(
        id="grab_back",
        sense=3,
        power=3,
        works_for={"water", "fall"},
        text="caught instigator's jacket, planted both feet, and pulled the child back to safety",
        fail="reached for instigator, but was a breath too late to stop the tumble",
        qa_text="caught the child and pulled them back to safety",
        tags={"rescue", "hands"},
    ),
    "life_ring": Response(
        id="life_ring",
        sense=3,
        power=2,
        works_for={"water"},
        text="snatched the life ring from its hook and swung it right where instigator could grab it",
        fail="threw the life ring, but the splash and shouting had already taken too long",
        qa_text="used the life ring so the child could grab on",
        tags={"rescue", "water", "life_ring"},
    ),
    "harbor_hook": Response(
        id="harbor_hook",
        sense=2,
        power=3,
        works_for={"water", "fall"},
        text="seized the harbor hook by the post and steadied instigator before the slip turned worse",
        fail="lunged with the harbor hook, but the child had already gone down hard",
        qa_text="used the harbor hook to steady the child",
        tags={"rescue", "harbor"},
    ),
    "shout_only": Response(
        id="shout_only",
        sense=1,
        power=1,
        works_for={"water", "fall"},
        text="shouted from far away until the child somehow froze in place",
        fail="shouted a warning, but a warning alone could not stop the fall",
        qa_text="only shouted a warning",
        tags={"warning"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "sensible", "steady", "thoughtful", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for sid, setting in SETTINGS.items():
        for cid in CELEBRITIES:
            for shid, shortcut in SHORTCUTS.items():
                if hazard_at_risk(setting, shortcut):
                    combos.append((sid, cid, shid))
    return combos


@dataclass
class StoryParams:
    setting: str
    celebrity: str
    shortcut: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "celebrity": [
        (
            "What is a celebrity?",
            "A celebrity is a person many people know from books, songs, shows, or sports. They may feel exciting to meet, but the same safety rules still matter around them.",
        )
    ],
    "harbor": [
        (
            "What is a harbor?",
            "A harbor is a place where boats come in and stay near the shore. Harbors can be busy and slippery, so children need to stay on the safe paths.",
        )
    ],
    "pier": [
        (
            "Why can docks and piers be slippery?",
            "Water spray can make boards smooth and slick. That is why people walk carefully and stay away from the edge.",
        )
    ],
    "water": [
        (
            "Why is water near a dock dangerous?",
            "Deep or cold water can pull a person off balance very quickly. Even a small slip near the edge can turn scary fast.",
        )
    ],
    "fall": [
        (
            "Why are wobbly stacks unsafe to climb?",
            "Things like crates can tip or slide because they are not made to be stairs. A child can fall before there is time to catch them.",
        )
    ],
    "life_ring": [
        (
            "What is a life ring?",
            "A life ring is a floating ring used to help someone in the water hold on. Grown-ups throw it so a person can stay up while help reaches them.",
        )
    ],
    "rescue": [
        (
            "What should a child do if someone slips near water?",
            "Call for a grown-up right away and stay where it is safe. Fast calling for help is brave because it brings the right hands quickly.",
        )
    ],
}

KNOWLEDGE_ORDER = ["celebrity", "harbor", "pier", "water", "fall", "life_ring", "rescue"]


def child_name(ent: Entity) -> str:
    return ent.label or ent.id


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
    setting = f["setting"]
    celebrity = f["celebrity"]
    shortcut = f["shortcut"]
    outcome = f["outcome"]
    aname = child_name(a)
    bname = child_name(b)
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old where two children at {setting.place} '
        f'get excited to see the celebrity {celebrity.label}, and one wants to rush by using {shortcut.label}. '
        f'Include the word "celebrity".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a near-miss story where {aname} wants a dangerous shortcut to reach {celebrity.label}, "
            f"but {bname} gives a careful warning and the children choose the safe route instead.",
            f"Write a gentle cautionary pirate tale where no one gets hurt because an older sibling stops the rush before the shortcut is tried.",
        ]
    if outcome == "missed":
        return [
            base,
            f"Tell a cautionary pirate tale where {aname} ignores {bname}'s warning, slips while rushing toward the celebrity, and is safe in the end but misses the show.",
            f"Write a story with conflict and consequence: excitement about a celebrity leads to a dangerous choice, and the ending teaches that no shortcut is worth the risk.",
        ]
    return [
        base,
        f"Tell a pirate-style cautionary story where {aname} ignores {bname}'s warning, slips during a dangerous shortcut, and a grown-up rescues the child before the family takes the safe route.",
        f"Write a simple story where a child learns that excitement about a celebrity does not change harbor safety rules, and end with a bright safe image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    setting = f["setting"]
    celebrity = f["celebrity"]
    shortcut = f["shortcut"]
    response = f["response"]
    relation = f["relation"]
    aname = child_name(a)
    bname = child_name(b)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, relation)}, {aname} and {bname}, at {setting.place}. "
            f"They were excited to see the celebrity {celebrity.label}.",
        ),
        (
            f"Why were the children in such a hurry?",
            f"They wanted to reach the front before {celebrity.label} began the show and {celebrity.prize}. "
            f"That excitement is what made the dangerous shortcut feel tempting.",
        ),
        (
            f"What shortcut did {aname} want to use, and why was it unsafe?",
            f"{aname} wanted to use {shortcut.phrase}. It was unsafe because {shortcut.surface} could turn a quick rush into a slip near danger.",
        ),
        (
            f"What did {bname} do when the shortcut looked dangerous?",
            f"{bname} warned {aname} and tried to stop the rush. The warning came from seeing that the safe path existed for a reason.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after {bname}'s warning?",
                f"{aname} stopped before trying the shortcut, and both children stayed beside their {pw}. "
                f"Because they slowed down in time, the scary part never had a chance to begin.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the children using {setting.safe_route} and still seeing {celebrity.label}. "
                f"The ending shows that patience helped them keep both the fun and their safety.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {aname} rushed ahead?",
                f"{aname} slipped while trying the shortcut, and everyone got frightened. "
                f"The trouble came from hurrying onto a place that was never meant to be the way through.",
            )
        )
        qa.append(
            (
                f"How did the {pw} help?",
                f"The {pw} {response.qa_text}. That quick help ended the danger before it could grow into something worse.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                f"They learned that being excited about a celebrity does not make an unsafe path safe. "
                f"After the rescue, they used the marked route and understood why it mattered.",
            )
        )
    else:
        qa.append(
            (
                f"Did the family still get to see {celebrity.label}?",
                f"No. They had to stop and get calm and dry first, so the show ended before they got back. "
                f"Missing the celebrity became the consequence of the dangerous shortcut.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with everyone safe but disappointed. The children learned that rushing toward something exciting can make them lose the very thing they wanted to see.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["celebrity"].tags) | set(world.facts["setting"].tags) | set(world.facts["shortcut"].tags)
    if world.facts["outcome"] != "averted":
        tags |= set(world.facts["response"].tags)
        tags.add("rescue")
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        label = e.label or e.id
        lines.append(f"  {e.id:10} ({e.type:9}) {label:18} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="festival_pier",
        celebrity="captain_star",
        shortcut="rope_gap",
        response="grab_back",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        setting="market_dock",
        celebrity="ruby_beard",
        shortcut="dinghy",
        response="life_ring",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        setting="museum_wharf",
        celebrity="admiral_spark",
        shortcut="crate_stack",
        response="harbor_hook",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="cautious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=3,
    ),
    StoryParams(
        setting="festival_pier",
        celebrity="ruby_beard",
        shortcut="dinghy",
        response="life_ring",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=2,
    ),
    StoryParams(
        setting="museum_wharf",
        celebrity="captain_star",
        shortcut="rope_gap",
        response="grab_back",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Mia",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=6,
    ),
]


def explain_rejection(setting: Setting, shortcut: Shortcut) -> str:
    if not shortcut.risky:
        return (
            f"(No story: {shortcut.phrase} is already safe, so there is no cautionary conflict to resolve. "
            f"Pick a dangerous shortcut like a rope gap, dinghy, or crate stack.)"
        )
    return (
        f"(No story: {shortcut.label} is not a real shortcut at {setting.place}. "
        f"Pick a shortcut that this harbor actually affords.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try a better rescue like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], SHORTCUTS[params.shortcut], params.delay)
    return "contained" if contained else "missed"


ASP_RULES = r"""
hazard(S, Sh) :- setting(S), shortcut(Sh), affords(S, Sh), risky(Sh).
sensible(R)   :- response(R), sense(R, V), sense_min(M), V >= M.
valid(S, C, Sh) :- setting(S), celebrity(C), shortcut(Sh), hazard(S, Sh).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)        :- cautioner_older.
bonus(0)        :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted         :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(V + D) :- chosen_shortcut(Sh), base_severity(Sh, V), delay(D).
compatible      :- chosen_response(R), chosen_shortcut(Sh), works_for(R, H), hazard_kind(Sh, H).
contained       :- compatible, chosen_response(R), power(R, P), severity(S), P >= S.

outcome(averted)   :- averted.
outcome(contained) :- not averted, contained.
outcome(missed)    :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for sh in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, sh))
    for cid in CELEBRITIES:
        lines.append(asp.fact("celebrity", cid))
    for shid, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shid))
        if shortcut.risky:
            lines.append(asp.fact("risky", shid))
        lines.append(asp.fact("base_severity", shid, shortcut.severity))
        lines.append(asp.fact("hazard_kind", shid, shortcut.hazard))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for h in sorted(response.works_for):
            lines.append(asp.fact("works_for", rid, h))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_shortcut", params.shortcut),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if sample.world is None:
        raise StoryError("Smoke test failed: world model missing.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(150):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: pirate excitement, a celebrity, and a dangerous harbor shortcut."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--celebrity", choices=CELEBRITIES)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the grown-up takes to react")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP and Python parity plus smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.shortcut:
        setting = SETTINGS[args.setting]
        shortcut = SHORTCUTS[args.shortcut]
        if not hazard_at_risk(setting, shortcut):
            raise StoryError(explain_rejection(setting, shortcut))
    if args.shortcut and not SHORTCUTS[args.shortcut].risky:
        setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        raise StoryError(explain_rejection(setting, SHORTCUTS[args.shortcut]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.celebrity is None or combo[1] == args.celebrity)
        and (args.shortcut is None or combo[2] == args.shortcut)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, celebrity_id, shortcut_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        setting=setting_id,
        celebrity=celebrity_id,
        shortcut=shortcut_id,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.celebrity not in CELEBRITIES:
        raise StoryError(f"(Unknown celebrity: {params.celebrity})")
    if params.shortcut not in SHORTCUTS:
        raise StoryError(f"(Unknown shortcut: {params.shortcut})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    setting = SETTINGS[params.setting]
    celebrity = CELEBRITIES[params.celebrity]
    shortcut = SHORTCUTS[params.shortcut]
    response = RESPONSES[params.response]

    if not hazard_at_risk(setting, shortcut):
        raise StoryError(explain_rejection(setting, shortcut))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        celebrity=celebrity,
        shortcut=shortcut,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )

    story = world.render()
    for public_name in (params.instigator, params.cautioner):
        story = story.replace("instigator", public_name).replace("cautioner", public_name if public_name == params.cautioner else story)
    story = story.replace("instigator", params.instigator)
    story = story.replace("cautioner", params.cautioner)

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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, celebrity, shortcut) combos:\n")
        for setting, celebrity, shortcut in combos:
            print(f"  {setting:13} {celebrity:14} {shortcut}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.shortcut} at {p.setting} "
                f"for {p.celebrity} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
