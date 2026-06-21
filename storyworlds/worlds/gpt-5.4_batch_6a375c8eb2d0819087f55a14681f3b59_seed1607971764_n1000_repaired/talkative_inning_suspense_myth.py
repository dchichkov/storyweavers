#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py
============================================================

A standalone storyworld for a small suspenseful mythic tale: during an inning of
a hilltop ball game, a talkative child hears an old shrine calling back. The
child's choice, the kind of seal that guards the shrine, and the grown-up ritual
used to mend it determine whether the night is held back in time.

Run it
------
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py --game moonball --omen whisper --seal reed_knots
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py --seal ash_ring --omen whisper
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py --all
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/talkative_inning_suspense_myth.py --verify
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
CURIOUS_INIT = 5.0
WISE_TRAITS = {"careful", "solemn", "steady"}


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
        female = {"girl", "woman", "priestess", "mother"}
        male = {"boy", "man", "priest", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "priestess": "priestess",
            "priest": "priest",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
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
class Game:
    id: str
    scene: str
    ball: str
    opening: str
    goal: str
    sendoff: str
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
class Omen:
    id: str
    sign: str
    whisper: str
    verb: str
    weakness: str
    spread: int
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
class Seal:
    id: str
    label: str
    phrase: str
    weakness: str
    location: str
    guarding: str
    remake: str
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
    repairs: set[str]
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
        return [e for e in self.entities.values() if e.role in {"caller", "watcher"}]

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


def _r_darkness(world: World) -> list[str]:
    out: list[str] = []
    seal = world.get("seal")
    if seal.meters["breached"] < THRESHOLD:
        return out
    sig = ("darkness", "seal")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("field").meters["darkness"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__breach__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="darkness", tag="physical", apply=_r_darkness),
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


def hazard_at_risk(omen: Omen, seal: Seal) -> bool:
    return omen.weakness == seal.weakness


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(response: Response, seal: Seal) -> bool:
    return seal.id in response.repairs


def breach_severity(omen: Omen, delay: int) -> int:
    return omen.spread + delay


def is_contained(omen: Omen, response: Response, seal: Seal, delay: int) -> bool:
    return response_fits(response, seal) and response.power >= breach_severity(omen, delay)


def initial_wisdom(trait: str) -> float:
    return 5.0 if trait in WISE_TRAITS else 3.0


def would_avert(relation: str, caller_age: int, watcher_age: int, trait: str) -> bool:
    watcher_older = relation == "siblings" and watcher_age > caller_age
    authority = initial_wisdom(trait) + 1.0 + (3.0 if watcher_older else 0.0)
    return watcher_older and authority > CURIOUS_INIT


def predict_breach(world: World) -> dict:
    sim = world.copy()
    seal = sim.get("seal")
    seal.meters["breached"] += 1
    propagate(sim, narrate=False)
    return {
        "breached": seal.meters["breached"] >= THRESHOLD,
        "darkness": sim.get("field").meters["darkness"],
    }


def festival_setup(world: World, caller: Entity, watcher: Entity, game: Game, inning: str) -> None:
    for kid in (caller, watcher):
        kid.memes["joy"] += 1
    world.say(
        f"In the old days, when the moon still leaned close enough to listen, "
        f"the children of the hill played {game.id} on the stone field above the village."
    )
    world.say(
        f"{game.opening} A bright {game.ball} flashed from hand to hand, and "
        f"the people below counted on the game to {game.goal}."
    )
    world.say(
        f"That evening {caller.id}, a talkative {caller.type}, had been chosen to call the {inning}. "
        f"{watcher.id} kept watch beside the shrine at the edge of the field."
    )


def omen_stirs(world: World, caller: Entity, watcher: Entity, omen: Omen, seal: Seal, inning: str) -> None:
    caller.memes["curiosity"] += 1
    world.say(
        f"But in the middle of the {inning}, just when the players grew still to hear the count, "
        f"{omen.sign} beside {seal.phrase} {seal.location}."
    )
    world.say(
        f"{caller.id} heard it first. {omen.whisper} The sound curled around {caller.pronoun('possessive')} ear "
        f"as if the hill itself had learned {caller.pronoun('possessive')} name."
    )


def warn(world: World, watcher: Entity, caller: Entity, omen: Omen, seal: Seal, helper: Entity) -> None:
    pred = predict_breach(world)
    watcher.memes["wisdom"] += 1
    world.facts["predicted_darkness"] = pred["darkness"]
    world.say(
        f'{watcher.id} caught {caller.id} by the sleeve. "Do not answer," {watcher.pronoun()} said. '
        f'"{seal.phrase.capitalize()} was laid there to keep {seal.guarding} asleep. '
        f'If a child answers {omen.verb}, the old binding opens, and we must call the {helper.label_word} at once."'
    )


def back_down(world: World, caller: Entity, watcher: Entity, helper: Entity, seal: Seal) -> None:
    caller.memes["relief"] += 1
    watcher.memes["relief"] += 1
    caller.memes["curiosity"] = 0.0
    world.say(
        f"{caller.id} swallowed the answer that had already reached the tip of "
        f"{caller.pronoun('possessive')} tongue. For one trembling breath, the field felt colder."
    )
    world.say(
        f"Then {caller.pronoun()} stepped back from {seal.phrase}, and the two children ran together to fetch the "
        f"{helper.label_word} instead of testing the voice in the dark."
    )


def defy(world: World, caller: Entity, omen: Omen) -> None:
    caller.memes["defiance"] += 1
    world.say(
        f"But {caller.id} had a quick mouth and a quicker heart. Before anyone could stop "
        f"{caller.pronoun('object')}, {caller.pronoun()} answered {omen.verb}."
    )


def breach(world: World, caller: Entity, watcher: Entity, omen: Omen, seal: Seal, game: Game) -> None:
    seal_ent = world.get("seal")
    seal_ent.meters["breached"] += 1
    seal_ent.meters["frailty"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once {seal.phrase} shivered. A crack of night opened under it, and "
        f"{omen.sign.lower()} became a real thing."
    )
    world.say(
        f"The {game.ball} rolled to the chalk line and stopped there by itself. "
        f"{watcher.id} grabbed {caller.id}'s hand as the dark breathed out over the field."
    )


def mend(world: World, helper: Entity, response: Response, seal: Seal, omen: Omen) -> None:
    world.get("seal").meters["breached"] = 0.0
    world.get("field").meters["darkness"] = 0.0
    body = response.text.replace("{seal}", seal.label)
    world.say(
        f"The {helper.label_word} came up the hill without hurrying, but every step sounded certain. "
        f"{helper.pronoun().capitalize()} {body}."
    )
    world.say(
        f"The strange breath thinned, the stone underfoot warmed again, and the night drew back behind {seal.phrase}."
    )


def mend_fail(world: World, helper: Entity, response: Response, seal: Seal, game: Game) -> None:
    world.get("field").meters["darkness"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    body = response.fail.replace("{seal}", seal.label)
    world.say(
        f"The {helper.label_word} hurried to the shrine and {body}."
    )
    world.say(
        f"But the darkness had already tasted the open air. It swept across the lines of the field, "
        f"lifted the {game.ball}, and carried it down into the crack below the stones."
    )


def lesson(world: World, helper: Entity, caller: Entity, watcher: Entity, omen: Omen) -> None:
    for kid in (caller, watcher):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'The {helper.label_word} laid a warm hand on both their heads. "{omen.verb.capitalize()} is a little thing," '
        f'{helper.pronoun()} said, "but little doors can open into great darkness. '
        f'When the old hill calls, children must fetch help, not answer back."'
    )


def quiet_gift(world: World, helper: Entity, caller: Entity, watcher: Entity, game: Game, inning: str) -> None:
    for kid in (caller, watcher):
        kid.memes["joy"] += 1
        kid.memes["patience"] += 1
    world.say(
        f"The next evening the {helper.label_word} brought them a small shell horn for the counting of innings."
    )
    world.say(
        f'"This is for the {caller.id} who can hold words until the right moment," '
        f'{helper.pronoun()} said with a smile.'
    )
    world.say(
        f"When the {inning} came again, {caller.id} lifted the shell horn instead of shouting, "
        f"and its clear note floated over the field. {game.sendoff}"
    )


def sad_close(world: World, helper: Entity, caller: Entity, watcher: Entity, game: Game) -> None:
    for kid in (caller, watcher):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say(
        f"The game could not go on that night. The villagers stood in a ring with lamps while the crack was sealed stone by stone."
    )
    world.say(
        f"Long after the hill grew quiet, {caller.id} remembered the empty place where the {game.ball} had been, "
        f"and never again did {caller.pronoun()} speak lightly to a voice from the dark."
    )


def tell(
    game: Game,
    omen: Omen,
    seal: Seal,
    response: Response,
    caller_name: str = "Neri",
    caller_gender: str = "girl",
    watcher_name: str = "Taro",
    watcher_gender: str = "boy",
    watcher_trait: str = "careful",
    helper_type: str = "priestess",
    inning: str = "third inning",
    delay: int = 0,
    caller_age: int = 5,
    watcher_age: int = 7,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    caller = world.add(Entity(
        id=caller_name,
        kind="character",
        type=caller_gender,
        role="caller",
        age=caller_age,
        attrs={"relation": relation},
        traits=["talkative"],
    ))
    watcher = world.add(Entity(
        id=watcher_name,
        kind="character",
        type=watcher_gender,
        role="watcher",
        age=watcher_age,
        attrs={"relation": relation},
        traits=[watcher_trait],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    field_ent = world.add(Entity(id="field", type="field", label="the field"))
    seal_ent = world.add(Entity(id="seal", type="seal", label=seal.label))
    ball_ent = world.add(Entity(id="ball", type="ball", label=game.ball))
    caller.memes["curiosity"] = CURIOUS_INIT
    watcher.memes["trust"] = float(trust)
    watcher.memes["wisdom"] = initial_wisdom(watcher_trait)
    field_ent.meters["darkness"] = 0.0
    seal_ent.meters["breached"] = 0.0
    seal_ent.meters["frailty"] = 0.0
    ball_ent.meters["lost"] = 0.0
    world.facts["predicted_darkness"] = 0
    world.facts["relation"] = relation

    festival_setup(world, caller, watcher, game, inning)
    world.para()
    omen_stirs(world, caller, watcher, omen, seal, inning)
    warn(world, watcher, caller, omen, seal, helper)

    averted = would_avert(relation, caller_age, watcher_age, watcher_trait)
    if averted:
        back_down(world, caller, watcher, helper, seal)
        world.para()
        body = response.text.replace("{seal}", seal.label)
        world.say(
            f"When they reached the shrine, the {helper.label_word} {body}, though the old binding had only just begun to tremble."
        )
        lesson(world, helper, caller, watcher, omen)
        world.para()
        quiet_gift(world, helper, caller, watcher, game, inning)
        contained = True
        severity = 0
    else:
        defy(world, caller, omen)
        world.para()
        breach(world, caller, watcher, omen, seal, game)
        severity = breach_severity(omen, delay)
        world.get("seal").meters["severity"] = float(severity)
        contained = is_contained(omen, response, seal, delay)
        world.para()
        if contained:
            mend(world, helper, response, seal, omen)
            lesson(world, helper, caller, watcher, omen)
            world.para()
            quiet_gift(world, helper, caller, watcher, game, inning)
        else:
            mend_fail(world, helper, response, seal, game)
            world.get("ball").meters["lost"] += 1
            sad_close(world, helper, caller, watcher, game)

    outcome = "averted" if averted else ("contained" if contained else "lost")
    world.facts.update(
        game=game,
        omen=omen,
        seal_cfg=seal,
        response=response,
        caller=caller,
        watcher=watcher,
        helper=helper,
        inning=inning,
        ignited=world.get("seal").meters["frailty"] >= THRESHOLD,
        outcome=outcome,
        contained=contained,
        severity=severity,
        delay=delay,
        lost_ball=world.get("ball").meters["lost"] >= THRESHOLD,
    )
    return world


GAMES = {
    "moonball": Game(
        id="moonball",
        scene="a silver field",
        ball="white leather ball",
        opening="The elders said the game had been taught by the Hare in the Moon.",
        goal="keep the hill cheerful so the shadows below would sleep",
        sendoff="The children finished the game beneath a brave and watchful moon.",
        tags={"game", "moon"},
    ),
    "sunball": Game(
        id="sunball",
        scene="a golden field",
        ball="red-stitched ball",
        opening="The elders said the Sun once tossed the first ball down to the hill at dawn.",
        goal="keep the village bright-hearted until the lamps were lit",
        sendoff="The children played on until the last rim of gold slipped beyond the trees.",
        tags={"game", "sun"},
    ),
    "reedball": Game(
        id="reedball",
        scene="a windy field",
        ball="woven reed ball",
        opening="The old singers claimed river spirits first taught the game to the fisher children.",
        goal="make the hillside ring with life so lonely things would stay in their holes",
        sendoff="At the end, the reed ball leapt from palm to palm like a happy little fish.",
        tags={"game", "river"},
    ),
}

OMENS = {
    "whisper": Omen(
        id="whisper",
        sign="a thin whisper slid up from the stones",
        whisper='"Neri... count for me too..."',
        verb="whispering back",
        weakness="speech",
        spread=2,
        tags={"whisper", "voice"},
    ),
    "gust": Omen(
        id="gust",
        sign="a cold gust breathed out of a crack in the hill",
        whisper='"Closer..." the wind seemed to say, though no mouth could be seen.',
        verb="calling into the wind",
        weakness="air",
        spread=2,
        tags={"wind", "cold"},
    ),
    "trickle": Omen(
        id="trickle",
        sign="a black trickle crept between the shrine stones",
        whisper='"Come see what the hill is hiding..."',
        verb="leaning down to answer",
        weakness="water",
        spread=2,
        tags={"water", "shadow"},
    ),
}

SEALS = {
    "reed_knots": Seal(
        id="reed_knots",
        label="reed-knot curtain",
        phrase="the reed-knot curtain",
        weakness="speech",
        location="before the mouth of the shrine",
        guarding="the Echo Jackal",
        remake="retied with seven still knots",
        tags={"reed_knots", "shrine"},
    ),
    "blue_lamp": Seal(
        id="blue_lamp",
        label="blue shrine lamp",
        phrase="the blue shrine lamp",
        weakness="air",
        location="in a niche of black stone",
        guarding="the Wind Sleeper",
        remake="fed with oil until the blue flame stood steady again",
        tags={"lamp", "shrine"},
    ),
    "ash_ring": Seal(
        id="ash_ring",
        label="ash ring",
        phrase="the ash ring",
        weakness="water",
        location="around a split stone at the field's rim",
        guarding="the Hollow Eel",
        remake="drawn again in a clean white circle",
        tags={"ash", "shrine"},
    ),
}

RESPONSES = {
    "retie": Response(
        id="retie",
        sense=3,
        power=3,
        repairs={"reed_knots"},
        text="knelt by the shrine and retied the loosened reeds with seven slow knots",
        fail="tried to retie the reed-knot curtain, but too many strands had already come loose",
        qa_text="retied the loosened reeds with seven slow knots",
        tags={"ritual", "knots"},
    ),
    "oil": Response(
        id="oil",
        sense=3,
        power=3,
        repairs={"blue_lamp"},
        text="cupped the blue flame with one hand and fed it sacred oil with the other until it stood straight again",
        fail="poured sacred oil into the lamp, but the gust had already blown the flame thin as a thread",
        qa_text="fed the blue shrine lamp sacred oil and steadied its flame",
        tags={"ritual", "lamp"},
    ),
    "salt_ash": Response(
        id="salt_ash",
        sense=3,
        power=3,
        repairs={"ash_ring"},
        text="scattered salt, then drew fresh ash in a bright ring around the split stone",
        fail="cast salt and ash around the split stone, but the dark water had already washed the ring apart",
        qa_text="scattered salt and drew a fresh ash ring",
        tags={"ritual", "ash"},
    ),
    "shout": Response(
        id="shout",
        sense=1,
        power=1,
        repairs=set(),
        text="shouted at the darkness and stamped the field stones",
        fail="shouted at the darkness, which only answered louder",
        qa_text="shouted at the darkness",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Neri", "Ila", "Mina", "Sora", "Lumi", "Aya"]
BOY_NAMES = ["Taro", "Kiro", "Sami", "Ren", "Danu", "Peko"]
TRAITS = ["careful", "solemn", "steady", "clever", "curious", "brisk"]
INNINGS = ["first inning", "second inning", "third inning", "last inning"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for game_id in GAMES:
        for omen_id, omen in OMENS.items():
            for seal_id, seal in SEALS.items():
                if hazard_at_risk(omen, seal):
                    combos.append((game_id, omen_id, seal_id))
    return combos


@dataclass
class StoryParams:
    game: str
    omen: str
    seal: str
    response: str
    caller: str
    caller_gender: str
    watcher: str
    watcher_gender: str
    helper: str
    watcher_trait: str
    inning: str
    delay: int = 0
    caller_age: int = 5
    watcher_age: int = 7
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
    "whisper": [(
        "Why can a whisper feel scary in the dark?",
        "A whisper is quiet and close, so your mind tries hard to guess where it came from. When you cannot see the speaker, it can make a safe place feel strange."
    )],
    "wind": [(
        "Why does a cold gust feel spooky?",
        "A cold gust can arrive all at once and touch your skin before you see anything moving. That surprise can make people feel nervous."
    )],
    "water": [(
        "Why can water wash away markings on the ground?",
        "Moving water carries tiny bits of dust and ash with it. If a line is light and powdery, the water can smear it apart."
    )],
    "ritual": [(
        "What is a ritual in an old story?",
        "A ritual is a special set of actions done in a careful order. In myths, people use rituals to show respect and to keep important promises."
    )],
    "lamp": [(
        "Why does adding oil help a lamp burn?",
        "The flame uses the oil as fuel. When there is enough fuel and the flame is sheltered, it grows steady and bright again."
    )],
    "ash": [(
        "What is ash?",
        "Ash is the soft gray powder left after something burns. It is light, so wind and water can move it easily."
    )],
    "knots": [(
        "Why do knots hold things together?",
        "A knot wraps one part around another so it cannot slip free easily. Careful knots can keep a curtain or cord tight."
    )],
}
KNOWLEDGE_ORDER = ["whisper", "wind", "water", "ritual", "lamp", "ash", "knots"]


def pair_noun(caller: Entity, watcher: Entity, relation: str) -> str:
    if relation == "siblings":
        if caller.type == "boy" and watcher.type == "boy":
            return "two brothers"
        if caller.type == "girl" and watcher.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    caller = f["caller"]
    watcher = f["watcher"]
    game = f["game"]
    omen = f["omen"]
    seal = f["seal_cfg"]
    inning = f["inning"]
    outcome = f["outcome"]
    base = (
        f'Write a short myth-like story for a 3-to-5-year-old about a talkative child during the {inning} of {game.id}. '
        f'Include suspense and the word "inning".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle myth where {caller.id} almost answers {omen.sign}, but {watcher.id} stops {caller.pronoun('object')} before {seal.phrase} opens.",
            f"Write a suspenseful story with an old shrine, an older sibling's warning, and a calm ending where the child learns to hold words."
        ]
    if outcome == "lost":
        return [
            base,
            f"Tell a mythic cautionary story where {caller.id} answers a dark voice by {seal.phrase}, and the game is lost for the night.",
            f"Write a suspense story with a shrine, a child's mistake, and an ending that teaches respect for old warnings."
        ]
    return [
        base,
        f"Tell a suspenseful myth where {caller.id} answers a strange sign during the {inning}, the shrine begins to open, and a wise grown-up closes it in time.",
        f"Write a child-facing story with an old hill, a dangerous whisper, and an ending image that shows the child has become more careful."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    caller = f["caller"]
    watcher = f["watcher"]
    helper = f["helper"]
    game = f["game"]
    omen = f["omen"]
    seal = f["seal_cfg"]
    response = f["response"]
    inning = f["inning"]
    relation = f.get("relation", "friends")
    pair = pair_noun(caller, watcher, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {caller.id} and {watcher.id}, during a game of {game.id} on the hill. A wise {helper.label_word} also comes to help when the shrine is in danger."
        ),
        (
            f"What was happening when the trouble began?",
            f"The trouble began in the {inning}, when the field grew still for the count. That quiet moment made it easy for {caller.id} to hear {omen.sign} beside {seal.phrase}."
        ),
        (
            f"Why did {watcher.id} warn {caller.id} not to answer?",
            f"{watcher.id} knew {seal.phrase} was meant to keep {seal.guarding} asleep. {watcher.pronoun().capitalize()} also foresaw that answering could open the old binding and let darkness spread onto the field."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {caller.id} do after the warning?",
            f"{caller.id} swallowed the answer and stepped away from the shrine instead of speaking back. Then the children fetched the {helper.label_word}, so the danger never became a full breach."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly and safely. The next evening {caller.id} used a shell horn to mark the innings, which showed that {caller.pronoun()} had learned to be careful with words."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"How did the {helper.label_word} fix the problem?",
            f"The {helper.label_word} {response.qa_text}. That careful ritual pushed the darkness back behind {seal.phrase} before it could take the field."
        ))
        qa.append((
            f"What did {caller.id} learn?",
            f"{caller.id} learned that even a small answer can open a dangerous door. At the end, {caller.pronoun()} counted the next inning with the shell horn instead of shouting, which proved the lesson had stayed with {caller.pronoun('object')}."
        ))
    else:
        qa.append((
            "What happened because the help came too late?",
            f"The darkness swept over the field and carried the {game.ball} away into the crack. The game had to stop, so the loss itself became the lesson."
        ))
        qa.append((
            f"Why did {caller.id} never forget that night?",
            f"{caller.id} remembered the empty place where the ball had been. That missing ball showed how one careless answer could change the whole night."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["omen"].tags) | set(f["response"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        game="moonball",
        omen="whisper",
        seal="reed_knots",
        response="retie",
        caller="Neri",
        caller_gender="girl",
        watcher="Taro",
        watcher_gender="boy",
        helper="priestess",
        watcher_trait="careful",
        inning="third inning",
        delay=0,
        caller_age=5,
        watcher_age=7,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        game="sunball",
        omen="gust",
        seal="blue_lamp",
        response="oil",
        caller="Ren",
        caller_gender="boy",
        watcher="Aya",
        watcher_gender="girl",
        helper="priestess",
        watcher_trait="steady",
        inning="second inning",
        delay=0,
        caller_age=6,
        watcher_age=6,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        game="reedball",
        omen="trickle",
        seal="ash_ring",
        response="salt_ash",
        caller="Mina",
        caller_gender="girl",
        watcher="Kiro",
        watcher_gender="boy",
        helper="priest",
        watcher_trait="curious",
        inning="last inning",
        delay=2,
        caller_age=6,
        watcher_age=5,
        relation="siblings",
        trust=3,
    ),
    StoryParams(
        game="moonball",
        omen="gust",
        seal="blue_lamp",
        response="oil",
        caller="Ila",
        caller_gender="girl",
        watcher="Lumi",
        watcher_gender="girl",
        helper="priestess",
        watcher_trait="solemn",
        inning="first inning",
        delay=0,
        caller_age=4,
        watcher_age=7,
        relation="siblings",
        trust=8,
    ),
]


def explain_rejection(omen: Omen, seal: Seal) -> str:
    return (
        f"(No story: {omen.id} threatens a seal weakened by {omen.weakness}, but {seal.phrase} is weakened by "
        f"{seal.weakness}. The danger and the shrine do not match.)"
    )


def explain_response(response: Response, seal: Seal) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Choose a careful ritual instead.)"
        )
    return (
        f"(No story: {response.id} does not actually mend {seal.phrase}. The ritual must fit the kind of seal that failed.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.caller_age, params.watcher_age, params.watcher_trait):
        return "averted"
    omen = OMENS[params.omen]
    response = RESPONSES[params.response]
    seal = SEALS[params.seal]
    return "contained" if is_contained(omen, response, seal, params.delay) else "lost"


ASP_RULES = r"""
hazard(O, S) :- omen(O), seal(S), omen_weakness(O, W), seal_weakness(S, W).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
fits(R, S) :- repairs(R, S).

valid(G, O, S) :- game(G), hazard(O, S).

wise_now(T) :- trait(T), wise_trait(T).
init_wisdom(5) :- trait(T), wise_now(T).
init_wisdom(3) :- trait(T), not wise_now(T).
watcher_older :- relation(siblings), caller_age(CA), watcher_age(WA), WA > CA.
bonus(3) :- watcher_older.
bonus(0) :- not watcher_older.
authority(W + 1 + B) :- init_wisdom(W), bonus(B).
averted :- watcher_older, authority(A), curious_init(C), A > C.

severity(Sp + D) :- chosen_omen(O), omen_spread(O, Sp), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- chosen_seal(S), chosen_response(R), fits(R, S), resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gid in GAMES:
        lines.append(asp.fact("game", gid))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        lines.append(asp.fact("omen_weakness", oid, omen.weakness))
        lines.append(asp.fact("omen_spread", oid, omen.spread))
    for sid, seal in SEALS.items():
        lines.append(asp.fact("seal", sid))
        lines.append(asp.fact("seal_weakness", sid, seal.weakness))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
        for sid in sorted(response.repairs):
            lines.append(asp.fact("repairs", rid, sid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curious_init", int(CURIOUS_INIT)))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("wise_trait", trait))
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
        asp.fact("chosen_omen", params.omen),
        asp.fact("chosen_seal", params.seal),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("caller_age", params.caller_age),
        asp.fact("watcher_age", params.watcher_age),
        asp.fact("trait", params.watcher_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a talkative child, an old shrine, and a suspenseful inning on the hill."
    )
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--seal", choices=SEALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--helper", choices=["priestess", "priest"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the breach gets before help arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.omen and args.seal:
        omen = OMENS[args.omen]
        seal = SEALS[args.seal]
        if not hazard_at_risk(omen, seal):
            raise StoryError(explain_rejection(omen, seal))
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            seal = SEALS[args.seal] if args.seal else next(iter(SEALS.values()))
            raise StoryError(explain_response(response, seal))
        if args.seal and not response_fits(response, SEALS[args.seal]):
            raise StoryError(explain_response(response, SEALS[args.seal]))

    combos = [
        c for c in valid_combos()
        if (args.game is None or c[0] == args.game)
        and (args.omen is None or c[1] == args.omen)
        and (args.seal is None or c[2] == args.seal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    game_id, omen_id, seal_id = rng.choice(sorted(combos))
    sensible = [r.id for r in sensible_responses() if response_fits(r, SEALS[seal_id])]
    if args.response:
        if args.response not in sensible:
            raise StoryError(explain_response(RESPONSES[args.response], SEALS[seal_id]))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(sensible))

    caller, caller_gender = _pick_kid(rng)
    watcher, watcher_gender = _pick_kid(rng, avoid=caller)
    helper = args.helper or rng.choice(["priestess", "priest"])
    watcher_trait = rng.choice(TRAITS)
    inning = rng.choice(INNINGS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    caller_age, watcher_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(2, 9)

    return StoryParams(
        game=game_id,
        omen=omen_id,
        seal=seal_id,
        response=response_id,
        caller=caller,
        caller_gender=caller_gender,
        watcher=watcher,
        watcher_gender=watcher_gender,
        helper=helper,
        watcher_trait=watcher_trait,
        inning=inning,
        delay=delay,
        caller_age=caller_age,
        watcher_age=watcher_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.game not in GAMES:
        raise StoryError(f"(Unknown game: {params.game})")
    if params.omen not in OMENS:
        raise StoryError(f"(Unknown omen: {params.omen})")
    if params.seal not in SEALS:
        raise StoryError(f"(Unknown seal: {params.seal})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    omen = OMENS[params.omen]
    seal = SEALS[params.seal]
    response = RESPONSES[params.response]
    if not hazard_at_risk(omen, seal):
        raise StoryError(explain_rejection(omen, seal))
    if response.sense < SENSE_MIN or not response_fits(response, seal):
        raise StoryError(explain_response(response, seal))

    world = tell(
        game=GAMES[params.game],
        omen=omen,
        seal=seal,
        response=response,
        caller_name=params.caller,
        caller_gender=params.caller_gender,
        watcher_name=params.watcher,
        watcher_gender=params.watcher_gender,
        watcher_trait=params.watcher_trait,
        helper_type=params.helper,
        inning=params.inning,
        delay=params.delay,
        caller_age=params.caller_age,
        watcher_age=params.watcher_age,
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
        print(f"{len(combos)} compatible (game, omen, seal) combos:\n")
        for game, omen, seal in combos:
            print(f"  {game:8} {omen:8} {seal}")
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
            header = f"### {p.caller} & {p.watcher}: {p.game}, {p.omen}, {p.seal} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
