#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py
============================================================================

A standalone story world for a cautionary rhyming tale about an optic toy and a
small dangerous change. Children pretend, a bright beam tempts them, something
begins to transform the wrong way, and a calm grown-up redirects the story
toward a safer wonder.

The domain centers on a **magnifying optic lens**: it can gather sunlight into a
hot bright dot. In the wrong place that dot can scorch thin, dry things; in the
right hands, a grown-up can stop the danger and offer safer ways to enjoy light.

Run it
------
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --theme detectives --target paper_map
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --target stone_step
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --response wave_cloth
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/optic_cautionary_transformation_rhyming_story.py --verify
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
BOLDNESS_INIT = 6.0
CAREFUL_TRAITS = {"careful", "thoughtful", "steady", "sensible"}


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
    scorchable: bool = False
    focuses_light: bool = False
    gives_light: bool = False
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
class Theme:
    id: str
    scene: str
    props: str
    titles: tuple[str, str]
    goal: str
    dim_place: str
    send_off: str
    role_plural: str
    role_solo: str
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


@dataclass
class OpticTool:
    id: str
    label: str
    phrase: str
    where: str
    boast: str
    beam_word: str
    warning_name: str
    not_toy: str
    focuses_light: bool = True
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
class Target:
    id: str
    label: str
    the: str
    near: str
    texture: str
    dry_word: str
    spread: int = 1
    scorchable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class SafeWonder:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_scorch_spreads(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["scorching"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["smoke"] += 1
        ent.meters["marked"] += 1
        if "room" in world.entities:
            world.get("room").meters["danger"] += 1
        for kid in world.kids():
            kid.memes["fear"] += 1
        out.append("__scorch__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scorch_spreads", tag="physical", apply=_r_scorch_spreads),
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


def hazard_at_risk(tool: OpticTool, target: Target) -> bool:
    return tool.focuses_light and target.scorchable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def heat_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= heat_severity(target, delay)


def initial_care(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_care(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BOLDNESS_INIT


def _do_focus_beam(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["scorching"] += 1
    propagate(world, narrate=narrate)


def predict_scorch(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_focus_beam(sim, sim.get(target_id), narrate=False)
    return {
        "scorches": sim.get(target_id).meters["marked"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    t1, t2 = theme.titles
    world.say(
        f"On a bright small day, {a.id} and {b.id} made the room into {theme.scene}. "
        f"{theme.props}"
    )
    world.say(
        f'"{t1} {a.id} and {t2} {b.id}!" sang {a.id}. '
        f'"Let\'s find {theme.goal} before the sun slips away."'
    )


def need_help(world: World, b: Entity, theme: Theme, target: Target) -> None:
    world.say(
        f"But {theme.dim_place}, beside {target.texture}, looked dim and gray. "
        f'"A brighter clue would help us play," {b.id} said.'
    )


def tempt(world: World, a: Entity, tool: OpticTool) -> None:
    a.memes["show_off"] += 1
    world.say(
        f'{a.id} grinned wide. "{tool.boast} I saw {tool.phrase} {tool.where}. '
        f'Its optic glass can make one little sunbeam stay."'
    )
    world.say("For one bold blink, the trick looked clever, neat, and bright as day.")


def warn(world: World, b: Entity, a: Entity, tool: OpticTool, target: Target, parent: Entity) -> None:
    pred = predict_scorch(world, "target")
    b.memes["care"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["care"] >= 6:
        extra = f" {b.pronoun().capitalize()} tucked {b.pronoun('possessive')} chin and would not play along."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, {parent.label_word.capitalize()} said '
        f'we must not play with {tool.label}. A bright hot dot can mark {target.the} the wrong way."{extra}'
    )


def defy(world: World, a: Entity, b: Entity, tool: OpticTool) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Don\'t fuss," {a.id} said with a swaggering sway. '
            f'Because {a.id} was the older one, {b.id} could not make {a.pronoun("object")} stay.'
        )
    else:
        world.say(f'"Don\'t fuss," {a.id} said, and hurried off without delay.')


def back_down(world: World, a: Entity, b: Entity, tool: OpticTool, parent: Entity, theme: Theme) -> None:
    a.memes["boldness"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'"Don\'t fuss," {a.id} started to say. But {b.id}, the older {rel}, held firm, '
        f'and {a.id} let the reckless notion drift away.'
    )
    world.say(
        f"They left {tool.label} where it was and went to ask {parent.label_word} for a safer ray."
    )


def ignite(world: World, target_ent: Entity, tool: OpticTool, target: Target) -> None:
    _do_focus_beam(world, target_ent)
    world.say(
        f"Soon the optic lens caught sunlight in a tiny dancing spot. "
        f"The bright round bead sat still and hot. Then it kissed {target.near}, "
        f"and {target.the} began to curl and spot."
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{a.id}! Look! {target.The}!" cried {b.id}.')
    world.say(f'"{parent.label_word.upper()}! Please come right away!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["scorching"] = 0.0
    world.get("room").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} came quick and calm, not wild with fright. "
        f"{parent.pronoun().capitalize()} {body}."
    )
    world.say(
        f"The sharp hot trouble faded fast. A thin gray curl was all that stayed in sight."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, tool: OpticTool, target: Target) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f"Then {parent.label_word.capitalize()} knelt beside them on the floor. "
        f'"I am glad you called for me," {parent.pronoun()} said. '
        f'"An optic lens can help us learn, but {tool.not_toy}. '
        f'It can change {target.the} into smoke before you can count to four."'
    )
    world.say(
        f"{a.id} looked at the little mark, and {b.id} held close. "
        f'"We know now. We will be careful more."'
    )


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme,
              w1: SafeWonder, w2: SafeWonder) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word} had a kinder optic way. "
        f"{parent.pronoun().capitalize()} brought {w1.phrase} that {w1.glow}, "
        f"and {w2.phrase} that {w2.glow}."
    )
    world.say(
        f'"If you want bright wonders," {parent.pronoun()} smiled, '
        f'"use these and let the dangerous trickery stay away."'
    )
    world.say(
        f"{a.id} peered, {b.id} laughed, and colored flecks began to dance and sway. "
        f"{theme.send_off}, wiser than before, in safe and shining play."
    )


def rescue_fail(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
        world.get("room").meters["danger"] += 1
    target_ent.meters["scorching"] += 1
    target_ent.meters["smoke"] += 1
    body = response.fail.replace("{target}", target.label)
    world.say(
        f"{parent.label_word.capitalize()} rushed in and {body}. "
        f"But the heat had run ahead of help that day."
    )
    world.say(
        f"Smoke thickened, dark and bitter, where the little spot had learned to stay."
    )


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"There was no time for games or guesses. {parent.label_word.capitalize()} took their hands "
        f"and led them out the door, away."
    )
    world.say(
        "From the path they saw the window glow. Their paper clues and props were lost to smoke and gray."
    )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity, tool: OpticTool) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} held them close outside and said, '
        f'"You are safe, and that is what matters most today."'
    )
    world.say(
        f"But neither child forgot the bitter truth: {tool.not_toy}, "
        f"and one bright spot can steal a homey game away."
    )


def tell(theme: Theme, tool: OpticTool, target: Target, wonders: tuple[SafeWonder, SafeWonder],
         response: Response, instigator: str = "Nia", instigator_gender: str = "girl",
         cautioner: str = "Ben", cautioner_gender: str = "boy",
         trait: str = "careful", parent_type: str = "mother", delay: int = 0,
         instigator_age: int = 6, cautioner_age: int = 4, relation: str = "siblings",
         trust: int = 6) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator, kind="character", type=instigator_gender, role="instigator",
        traits=["bold"], age=instigator_age, attrs={"relation": relation}
    ))
    b = world.add(Entity(
        id=cautioner, kind="character", type=cautioner_gender, role="cautioner",
        traits=[trait], age=cautioner_age, attrs={"relation": relation}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent", label="the parent"
    ))
    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["trust"] = float(trust)
    b.memes["care"] = initial_care(trait)
    world.add(Entity(id="room", type="room", label="the room"))
    lens = world.add(Entity(id="tool", type="tool", label=tool.label, focuses_light=True))
    tgt = world.add(Entity(id="target", type="target", label=target.label, scorchable=target.scorchable))
    w1, w2 = wonders

    play_setup(world, a, b, theme)
    need_help(world, b, theme, target)

    world.para()
    tempt(world, a, tool)
    warn(world, b, a, tool, target, parent)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, tool, parent, theme)
        world.para()
        safe_gift(world, parent, a, b, theme, w1, w2)
        severity = 0
        contained = True
    else:
        defy(world, a, b, tool)
        world.para()
        ignite(world, tgt, tool, target)
        alarm(world, b, a, target, parent)

        severity = heat_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)

        world.para()
        if contained:
            rescue(world, parent, response, tgt, target)
            lesson(world, parent, a, b, tool, target)
            a.memes["transformed"] += 1
            world.para()
            safe_gift(world, parent, a, b, theme, w1, w2)
        else:
            rescue_fail(world, parent, response, tgt, target)
            escape_and_loss(world, parent, a, b, theme)
            grim_lesson(world, parent, a, b, tool)
            a.memes["transformed"] += 1

    outcome = "averted" if averted else ("contained" if contained else "burned")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        tool_cfg=tool,
        target_cfg=target,
        tool=lens,
        target=tgt,
        wonders=(w1, w2),
        response=response,
        ignited=tgt.meters["marked"] >= THRESHOLD,
        outcome=outcome,
        rescued=contained,
        severity=severity,
        delay=delay,
        relation=relation,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "detectives": Theme(
        id="detectives",
        scene="a whispery detective den",
        props="A striped blanket became a secret tent, a shoebox held clue cards, and chalk arrows curved across the rug.",
        titles=("Detective", "Scout"),
        goal="the hidden clue",
        dim_place="the shady corner by the window seat",
        send_off="So the little detectives followed rainbow hints from clue to clue",
        role_plural="detectives",
        role_solo="detective",
    ),
    "explorers": Theme(
        id="explorers",
        scene="a tiny explorer camp",
        props="A chair was a lookout hill, a towel was a map-cloth, and a basket held pretend trail snacks.",
        titles=("Captain", "Guide"),
        goal="the lost path",
        dim_place="the dusky nook near the big fern",
        send_off="So the small explorers went hunting for the lost path",
        role_plural="explorers",
        role_solo="explorer",
    ),
    "stargazers": Theme(
        id="stargazers",
        scene="a little star club",
        props="Pillows became moon rocks, silver stickers became planets, and a cardboard tube pointed toward pretend constellations.",
        titles=("Star-Finder", "Sky-Helper"),
        goal="the hidden star chart",
        dim_place="the soft dark patch under the shelf",
        send_off="So the young stargazers traced bright patterns through the room",
        role_plural="stargazers",
        role_solo="stargazer",
    ),
}

OPTIC_TOOLS = {
    "magnifier": OpticTool(
        id="magnifier",
        label="the optic magnifier",
        phrase="a round optic magnifier",
        where="on the sunny desk",
        boast="I know a faster way!",
        beam_word="hot dot",
        warning_name="optic lens",
        not_toy="optic lenses are not playthings in the sun",
        tags={"optic", "magnifier", "sunlight", "call_adult"},
    ),
    "science_lens": OpticTool(
        id="science_lens",
        label="the optic science lens",
        phrase="the optic science lens",
        where="beside the plant book",
        boast="I know a science trick!",
        beam_word="bright bead",
        warning_name="optic lens",
        not_toy="optic lenses are not for sun tricks",
        tags={"optic", "magnifier", "sunlight", "call_adult"},
    ),
}

TARGETS = {
    "paper_map": Target(
        id="paper_map",
        label="paper map",
        the="the paper map",
        near="the edge of the paper map",
        texture="a folded paper map",
        dry_word="papery",
        spread=2,
        scorchable=True,
        tags={"paper", "flammable"},
    ),
    "tissue_kite": Target(
        id="tissue_kite",
        label="tissue kite",
        the="the tissue kite",
        near="the thin tail of the tissue kite",
        texture="a tissue kite with a ribbon tail",
        dry_word="tissue-thin",
        spread=3,
        scorchable=True,
        tags={"paper", "flammable"},
    ),
    "dry_leaf": Target(
        id="dry_leaf",
        label="dry leaf",
        the="the dry leaf",
        near="the crisp dry leaf",
        texture="a tray of crisp leaves",
        dry_word="crispy",
        spread=2,
        scorchable=True,
        tags={"leaf", "flammable"},
    ),
    "stone_step": Target(
        id="stone_step",
        label="stone step",
        the="the stone step",
        near="the cool stone step",
        texture="a cool stone step",
        dry_word="stony",
        spread=1,
        scorchable=False,
        tags={"stone"},
    ),
}

SAFE_WONDERS = {
    "flashlight": SafeWonder(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on with a steady white gleam",
        tags={"flashlight"},
    ),
    "kaleidoscope": SafeWonder(
        id="kaleidoscope",
        label="kaleidoscope",
        phrase="a little kaleidoscope",
        glow="filled the eye with tumbling shapes and color",
        tags={"kaleidoscope", "optic"},
    ),
    "prism": SafeWonder(
        id="prism",
        label="prism",
        phrase="a glass prism",
        glow="spilled a rainbow stripe across the wall",
        tags={"prism", "optic"},
    ),
    "star_lamp": SafeWonder(
        id="star_lamp",
        label="star lamp",
        phrase="a star lamp",
        glow="sprinkled gentle dots of light across the ceiling",
        tags={"lamp"},
    ),
}

RESPONSES = {
    "cover_lens": Response(
        id="cover_lens",
        sense=3,
        power=4,
        text="covered the lens with a thick cloth, moved it from the sun, and patted the smoking {target} flat on a tray",
        fail="covered the lens, but the {target} had already taken too much heat",
        qa_text="covered the lens, moved it out of the sun, and stopped the hot spot",
        tags={"shade", "call_adult"},
    ),
    "water_mist": Response(
        id="water_mist",
        sense=3,
        power=3,
        text="misted the {target} with the plant sprayer and slid it onto the cool sink edge",
        fail="sprayed a little water, but the {target} was already smoking too hard",
        qa_text="misted the {target} and cooled it quickly",
        tags={"water", "call_adult"},
    ),
    "wave_cloth": Response(
        id="wave_cloth",
        sense=1,
        power=1,
        text="waved a dishcloth at the smoke",
        fail="waved a dishcloth at the smoke, which only fed the worry",
        qa_text="waved a cloth at the smoke",
        tags={"cloth"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Maya", "Ivy", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Leo", "Sam", "Noah", "Eli"]
TRAITS = ["careful", "thoughtful", "steady", "sensible", "curious", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme in THEMES:
        for tool_id, tool in OPTIC_TOOLS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(tool, target):
                    combos.append((theme, tool_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    tool: str
    target: str
    wonder1: str
    wonder2: str
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
    trust: int = 6
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
    "optic": [(
        "What does optic mean?",
        "Optic means something has to do with sight or light. An optic tool helps your eyes look at light in a special way."
    )],
    "magnifier": [(
        "What does a magnifier do?",
        "A magnifier is a lens that makes things look bigger. In sunlight, some magnifiers can also gather light into one hot bright spot."
    )],
    "sunlight": [(
        "Why can sunlight through a lens be dangerous?",
        "A curved lens can bunch sunlight into a tiny bright dot. That little dot can get hot enough to scorch thin dry things."
    )],
    "paper": [(
        "Why can paper scorch quickly?",
        "Paper is thin and dry, so heat can mark it fast. If the heat stays there, smoke or fire can begin."
    )],
    "leaf": [(
        "Why can a dry leaf smoke or burn easily?",
        "A dry leaf has very little water in it, so heat changes it quickly. That is why crisp leaves must be kept away from hot spots."
    )],
    "call_adult": [(
        "What should a child do if something starts to smoke?",
        "Move back and call a grown-up right away. Getting help quickly is the safest and bravest choice."
    )],
    "flashlight": [(
        "Why is a flashlight safer than a hot lens trick?",
        "A flashlight gives light with batteries and does not make a tiny burning spot. It helps you see without scorching things."
    )],
    "kaleidoscope": [(
        "What is a kaleidoscope?",
        "A kaleidoscope is an optic toy that shows colored shapes and patterns when you look through it. It is for looking, not for making things hot."
    )],
    "prism": [(
        "What does a prism do?",
        "A prism bends light and can spread it into rainbow colors. It shows light in a pretty safe way when used carefully."
    )],
    "lamp": [(
        "What does a star lamp do?",
        "A star lamp shines soft light to help a room glow. It can make playtime feel magical without using a hot beam from the sun."
    )],
    "shade": [(
        "How can taking a lens out of the sun help?",
        "If the lens is covered or moved into shade, the bright hot spot disappears. Without that hot spot, the danger drops right away."
    )],
}
KNOWLEDGE_ORDER = [
    "optic", "magnifier", "sunlight", "paper", "leaf", "call_adult",
    "flashlight", "kaleidoscope", "prism", "lamp", "shade"
]


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
    a, b = f["instigator"], f["cautioner"]
    tool, theme, target = f["tool_cfg"], f["theme"], f["target_cfg"]
    w1, w2 = f["wonders"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a rhyming cautionary story for a 3-to-5-year-old that includes the word "optic" and ends safely before anything burns.',
            f"Tell a gentle rhyming story where {a.id} wants to use {tool.label}, but {b.id} warns {a.pronoun('object')} and the dangerous idea is dropped.",
            f"Write a transformation story in rhyme where the children change from reckless curiosity to careful wonder, ending with {w1.label} and {w2.label}.",
        ]
    if outcome == "burned":
        return [
            f'Write a rhyming cautionary story that includes the word "optic" and shows how a bright trick with sunlight can become too dangerous.',
            f"Tell a sad-but-child-safe rhyming story where {a.id} ignores a warning about {tool.label} near {target.the}, and the smoke grows too big to stop.",
            f"Write a transformation rhyme where a playful moment changes into a serious lesson about asking a grown-up for help.",
        ]
    return [
        f'Write a rhyming cautionary story for a 3-to-5-year-old that includes the word "optic" and ends with a safer way to enjoy light.',
        f"Tell a gentle rhyme where {a.id} uses {tool.label} the wrong way near {target.the}, but a calm grown-up fixes the problem.",
        f"Write a transformation story in rhyme where fear changes into wisdom and the ending image uses {w1.label} and {w2.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    tool, theme, target, response = f["tool_cfg"], f["theme"], f["target_cfg"], f["response"]
    w1, w2 = f["wonders"]
    pw = parent.label_word
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing {theme.role_plural}. A grown-up came to help when the bright trick became unsafe."
        ),
        (
            "Why did they want more light?",
            f"They were trying to find {theme.goal} in a dim place. That need for brightness made the optic trick feel tempting."
        ),
        (
            f"What did {a.id} want to use, and why did {b.id} warn {a.pronoun('object')}?",
            f"{a.id} wanted to use {tool.label}. {b.id} warned that the sun through the lens could make a hot bright spot on {target.the} and change it the dangerous way."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"How was the problem solved before anything burned?",
            f"{a.id} listened and gave up the risky idea. Then {pw} helped them use {w1.phrase} and {w2.phrase} so they could keep playing safely."
        ))
        qa.append((
            "How did the story show transformation?",
            f"The change was inside the children. They went from a risky plan to a wiser one, and their play turned from danger back into wonder."
        ))
    elif f["outcome"] == "contained":
        body = response.qa_text.replace("{target}", target.label)
        qa.append((
            f"What happened when the lens touched sunlight to {target.the}?",
            f"{target.The} began to curl and mark, and a little smoke appeared. The lens had focused the sunlight into one hot spot, which is why the danger came so fast."
        ))
        qa.append((
            f"How did {a.id}'s {pw} stop the problem?",
            f"{pw.capitalize()} {body}. That worked because removing or cooling the hot spot stopped the dangerous change from growing."
        ))
        qa.append((
            "How did the story show transformation?",
            f"The {target.label} began to transform from safe plaything into something smoky and damaged. After that scare, the children transformed too, becoming more careful and choosing safer optic wonders."
        ))
        qa.append((
            f"What was different at the end?",
            f"At the end, they were still looking at light, but now they used {w1.label} and {w2.label} instead of the risky lens trick. The ending image proves they learned a safer way to wonder."
        ))
    else:
        fail = response.fail.replace("{target}", target.label)
        qa.append((
            f"Could {a.id}'s {pw} stop the smoke in time?",
            f"No. {pw.capitalize()} {fail}, and the danger had already grown too big. That is why everyone had to leave instead of staying to play."
        ))
        qa.append((
            "How did the story show transformation?",
            f"A tiny bright dot transformed into thick smoke and loss. The children also changed, because after that they understood how quickly a risky sun trick can turn serious."
        ))
        qa.append((
            "How did the story end?",
            f"It ended sadly but safely, with the family outside together. The game was gone, yet the children were alive and had learned to call for help right away."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    outcome = f["outcome"]
    tags = set(f["tool_cfg"].tags) | set(f["target_cfg"].tags)
    if outcome == "contained":
        tags |= set(f["response"].tags)
        for wonder in f["wonders"]:
            tags |= set(wonder.tags)
    elif outcome == "averted":
        for wonder in f["wonders"]:
            tags |= set(wonder.tags)
    else:
        tags |= set(f["response"].tags)
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
        flags = [n for n, on in (("scorchable", e.scorchable), ("focuses_light", e.focuses_light), ("gives_light", e.gives_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="detectives",
        tool="magnifier",
        target="paper_map",
        wonder1="flashlight",
        wonder2="kaleidoscope",
        response="cover_lens",
        instigator="Nia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        theme="explorers",
        tool="science_lens",
        target="dry_leaf",
        wonder1="prism",
        wonder2="flashlight",
        response="water_mist",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Maya",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        theme="stargazers",
        tool="magnifier",
        target="tissue_kite",
        wonder1="star_lamp",
        wonder2="prism",
        response="water_mist",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        theme="detectives",
        tool="science_lens",
        target="paper_map",
        wonder1="flashlight",
        wonder2="prism",
        response="cover_lens",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
]


def explain_rejection(tool: OpticTool, target: Target) -> str:
    if not target.scorchable:
        return (
            f"(No story: {tool.label} can focus sunlight, but {target.the} will not scorch in a way that creates this cautionary problem. "
            f"Pick a thin dry target like a paper map, tissue kite, or dry leaf.)"
        )
    return "(No story: this combination does not create a plausible heat hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    contained = is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "contained" if contained else "burned"


ASP_RULES = r"""
hazard(Tool, Tg) :- focuses_light(Tool), scorchable(Tg).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Theme, Tool, Tg) :- theme(Theme), tool(Tool), target(Tg), hazard(Tool, Tg).

careful_now(T) :- trait(T), is_careful(T).
init_care(5) :- trait(T), careful_now(T).
init_care(3) :- trait(T), not careful_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_care(C), bonus(B).
averted :- cautioner_older, authority(A), boldness_init(B), A > B.

severity(Sp + D) :- chosen_target(Tg), spread(Tg, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for oid, tool in OPTIC_TOOLS.items():
        lines.append(asp.fact("tool", oid))
        if tool.focuses_light:
            lines.append(asp.fact("focuses_light", oid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if target.scorchable:
            lines.append(asp.fact("scorchable", tid))
        lines.append(asp.fact("spread", tid, target.spread))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
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

    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
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
    parser = build_parser()
    for s in range(120):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an optic light trick, a caution, and a safer transformation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--tool", choices=OPTIC_TOOLS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the heat gets before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].scorchable:
        tool = OPTIC_TOOLS[args.tool] if args.tool else next(iter(OPTIC_TOOLS.values()))
        raise StoryError(explain_rejection(tool, TARGETS[args.target]))
    if args.tool and args.target:
        tool = OPTIC_TOOLS[args.tool]
        target = TARGETS[args.target]
        if not hazard_at_risk(tool, target):
            raise StoryError(explain_rejection(tool, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.tool is None or c[1] == args.tool)
        and (args.target is None or c[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, tool, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    wonder1, wonder2 = rng.sample(sorted(SAFE_WONDERS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme,
        tool=tool,
        target=target,
        wonder1=wonder1,
        wonder2=wonder2,
        response=response,
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
    try:
        theme = THEMES[params.theme]
        tool = OPTIC_TOOLS[params.tool]
        target = TARGETS[params.target]
        wonder1 = SAFE_WONDERS[params.wonder1]
        wonder2 = SAFE_WONDERS[params.wonder2]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    if not hazard_at_risk(tool, target):
        raise StoryError(explain_rejection(tool, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if params.wonder1 == params.wonder2:
        raise StoryError("(Pick two different safe optic wonders.)")

    world = tell(
        theme=theme,
        tool=tool,
        target=target,
        wonders=(wonder1, wonder2),
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, tool, target) combos:\n")
        for theme, tool, target in combos:
            print(f"  {theme:11} {tool:13} {target}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.tool} near {p.target} ({p.theme}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
