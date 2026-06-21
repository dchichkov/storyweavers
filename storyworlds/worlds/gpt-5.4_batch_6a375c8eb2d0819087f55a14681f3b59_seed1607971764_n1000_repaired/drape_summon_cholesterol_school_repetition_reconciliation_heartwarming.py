#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py
====================================================================================================

A standalone story world about two classmates preparing a school wellness-fair
booth. A hanging drape slips over an important poster about cholesterol, one
child keeps repeating a cheerful call to summon visitors, feelings get hurt,
and the children repair both the booth and their friendship.

Run it
------
python storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py
python storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py --topic heart --drape felt --repair clips --summon chant
python storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py --repair tape --drape velvet
python storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py --all --qa
python storyworlds/worlds/gpt-5.4/drape_summon_cholesterol_school_repetition_reconciliation_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher"}.get(self.type, self.type)
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
class Topic:
    id: str
    booth_name: str
    poster_title: str
    poster_line: str
    opening: str
    ending_image: str
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
class Drape:
    id: str
    label: str
    color: str
    weight: int
    texture: str
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
class SummonMethod:
    id: str
    sense: int
    volume: int
    repeated: bool
    line: str
    style: str
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
class Repair:
    id: str
    hold: int
    text: str
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


def _r_hidden_poster(world: World) -> list[str]:
    out: list[str] = []
    drape = world.get("drape")
    poster = world.get("poster")
    if drape.meters["covering"] >= THRESHOLD and poster.meters["visible"] < THRESHOLD:
        sig = ("hidden_poster",)
        if sig not in world.fired:
            world.fired.add(sig)
            poster.meters["hidden"] += 1
            out.append("__poster_hidden__")
    return out


def _r_repeated_call_stings(world: World) -> list[str]:
    out: list[str] = []
    poster = world.get("poster")
    eager = world.get("eager")
    careful = world.get("careful")
    if eager.meters["calling"] >= THRESHOLD and poster.meters["hidden"] >= THRESHOLD:
        sig = ("repeated_call_stings",)
        if sig not in world.fired:
            world.fired.add(sig)
            careful.memes["hurt"] += 1
            careful.memes["frustration"] += 1
            world.get("crowd").meters["confusion"] += 1
            out.append("__sting__")
    return out


def _r_visible_poster_draws(world: World) -> list[str]:
    out: list[str] = []
    poster = world.get("poster")
    eager = world.get("eager")
    careful = world.get("careful")
    crowd = world.get("crowd")
    if (
        poster.meters["visible"] >= THRESHOLD
        and eager.meters["calling"] >= THRESHOLD
        and careful.meters["ready"] >= THRESHOLD
    ):
        sig = ("visible_poster_draws",)
        if sig not in world.fired:
            world.fired.add(sig)
            crowd.meters["interest"] += 1
            eager.memes["pride"] += 1
            careful.memes["pride"] += 1
            out.append("__visitors__")
    return out


def _r_apology_repairs_friendship(world: World) -> list[str]:
    out: list[str] = []
    eager = world.get("eager")
    careful = world.get("careful")
    if eager.memes["apology"] >= THRESHOLD and careful.meters["working_together"] >= THRESHOLD:
        sig = ("apology_repairs_friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            careful.memes["hurt"] = 0.0
            eager.memes["relief"] += 1
            careful.memes["relief"] += 1
            eager.memes["closeness"] += 1
            careful.memes["closeness"] += 1
            out.append("__reconciled__")
    return out


CAUSAL_RULES = [
    Rule(name="hidden_poster", tag="physical", apply=_r_hidden_poster),
    Rule(name="repeated_call_stings", tag="social", apply=_r_repeated_call_stings),
    Rule(name="visible_poster_draws", tag="social", apply=_r_visible_poster_draws),
    Rule(name="apology_repairs_friendship", tag="social", apply=_r_apology_repairs_friendship),
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
        for sent in produced:
            world.say(sent)
    return produced


def sensible_summons() -> list[SummonMethod]:
    return [s for s in SUMMONS.values() if s.sense >= SENSE_MIN]


def repair_holds(drape: Drape, repair: Repair) -> bool:
    return repair.hold >= drape.weight


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for topic_id in TOPICS:
        for drape_id, drape in DRAPES.items():
            for summon_id, summon in SUMMONS.items():
                if summon.sense < SENSE_MIN:
                    continue
                for repair_id, repair in REPAIRS.items():
                    if repair_holds(drape, repair):
                        combos.append((topic_id, drape_id, summon_id, repair_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    summon = SUMMONS[params.summon]
    return "apology_repair" if summon.repeated and summon.volume >= 2 else "quick_repair"


def predict_before_fix(world: World) -> dict:
    sim = world.copy()
    poster = sim.get("poster")
    drape = sim.get("drape")
    eager = sim.get("eager")
    poster.meters["visible"] = 0.0
    drape.meters["covering"] = 1.0
    eager.meters["calling"] = 1.0
    propagate(sim, narrate=False)
    return {
        "hidden": poster.meters["hidden"] >= THRESHOLD,
        "confusion": sim.get("crowd").meters["confusion"],
        "hurt": sim.get("careful").memes["hurt"],
    }


def setup_morning(world: World, eager: Entity, careful: Entity, teacher: Entity,
                  topic: Topic, drape: Drape) -> None:
    eager.memes["joy"] += 1
    careful.memes["joy"] += 1
    world.say(
        f"It was wellness-fair morning at school, and {eager.id} and {careful.id} had been chosen "
        f"to share the {topic.booth_name}. Their teacher, {teacher.id}, smiled as they spread a "
        f"{drape.color} {drape.label} across the front of the little table."
    )
    world.say(
        f"On the easel behind it stood a poster called {topic.poster_title}, and in the middle "
        f"of the page {careful.id} had written, \"{topic.poster_line}\""
    )
    world.say(topic.opening)


def slip_drape(world: World, eager: Entity, careful: Entity, drape: Drape) -> None:
    poster = world.get("poster")
    drape_ent = world.get("drape")
    drape_ent.meters["covering"] += 1
    poster.meters["visible"] = 0.0
    propagate(world, narrate=False)
    careful.memes["worry"] += 1
    world.say(
        f"Then one corner of the {drape.label} slid loose. It began to drape itself across the poster "
        f"until the biggest word on the page, cholesterol, almost disappeared."
    )
    world.say(
        f"{careful.id} reached toward it at once. \"Wait,\" {careful.pronoun()} said softly. "
        f"\"The poster is hiding.\""
    )


def try_to_summon(world: World, eager: Entity, careful: Entity, summon: SummonMethod) -> None:
    eager.meters["calling"] += 1
    eager.memes["eagerness"] += 1
    pred = predict_before_fix(world)
    world.facts["predicted_hidden"] = pred["hidden"]
    world.facts["predicted_confusion"] = pred["confusion"]
    if summon.repeated:
        line = summon.line
        world.say(
            f"But {eager.id} was already trying to summon the first visitors. "
            f"{eager.pronoun().capitalize()} called, \"{line}\" Then {eager.pronoun()} said it again: "
            f"\"{line}\" And once more, with the same hopeful bounce: \"{line}\""
        )
    else:
        world.say(
            f"But {eager.id} was already trying to summon the first visitors in {summon.style}. "
            f"{eager.pronoun().capitalize()} said, \"{summon.line}\""
        )
    propagate(world, narrate=False)
    if careful.memes["hurt"] >= THRESHOLD:
        world.say(
            f"A few children glanced over and kept walking. {careful.id} hugged the edge of the poster. "
            f"{careful.pronoun().capitalize()} had worked hard on the heart facts, and it stung to hear the call "
            f"repeated while nobody could see the page."
        )


def speak_hurt(world: World, eager: Entity, careful: Entity) -> None:
    careful.memes["honesty"] += 1
    world.say(
        f"At last {careful.id} said, \"I know you want to help, but when you keep saying it and the poster "
        f"is covered, it feels like my part does not matter.\""
    )


def notice_and_apologize(world: World, eager: Entity, careful: Entity, teacher: Entity,
                         topic: Topic) -> None:
    eager.memes["apology"] += 1
    eager.memes["care"] += 1
    world.say(
        f"{eager.id} stopped in the middle of the next call and really looked. Under the fallen cloth, "
        f"the bright letters of {topic.poster_title} were almost gone."
    )
    world.say(
        f'"Oh," {eager.pronoun()} whispered. "I was so busy trying to help that I did not listen. '
        f'I am sorry, {careful.id}."'
    )
    world.say(
        f"{teacher.id} did not scold. {teacher.pronoun().capitalize()} only came close enough to smile and say, "
        f"\"A booth works best when both voices fit together.\""
    )


def repair_display(world: World, eager: Entity, careful: Entity, drape: Drape,
                   repair: Repair) -> None:
    world.get("drape").meters["covering"] = 0.0
    world.get("poster").meters["hidden"] = 0.0
    world.get("poster").meters["visible"] = 1.0
    careful.meters["ready"] += 1
    careful.meters["working_together"] += 1
    eager.meters["working_together"] += 1
    careful.meters["working_together"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Together they fixed it. {eager.id} held the {drape.label} back while {careful.id} "
        f"{repair.text}."
    )
    world.say(
        f"Now the word cholesterol could be seen clearly again, right under the painted heart."
    )


def share_roles(world: World, eager: Entity, careful: Entity, summon: SummonMethod,
                topic: Topic) -> None:
    careful.meters["ready"] += 1
    eager.meters["calling"] = 1.0
    careful.meters["working_together"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they made a new plan. {eager.id} would invite people over, and {careful.id} would point "
        f"to the poster and explain one friendly fact at a time."
    )
    world.say(
        f'So {eager.id} tried again, this time in a smaller voice: "{summon.line}" '
        f"And when the children came near, {careful.id} showed them the poster and explained, "
        f"\"{topic.poster_line}\""
    )


def warm_ending(world: World, eager: Entity, careful: Entity, topic: Topic) -> None:
    crowd = world.get("crowd")
    if crowd.meters["interest"] >= THRESHOLD:
        eager.memes["joy"] += 1
        careful.memes["joy"] += 1
        world.say(
            f"Soon the space in front of the table filled with shoes and whispery questions. "
            f"A little line of students formed, not because anyone shouted, but because the booth finally "
            f"made sense."
        )
    world.say(
        f"When the bell rang for the next class, {eager.id} and {careful.id} were still standing shoulder to "
        f"shoulder. {topic.ending_image}"
    )


@dataclass
class StoryParams:
    topic: str
    drape: str
    summon: str
    repair: str
    eager: str
    eager_gender: str
    careful: str
    careful_gender: str
    teacher: str
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


def tell(topic: Topic, drape: Drape, summon: SummonMethod, repair: Repair,
         eager_name: str = "Mina", eager_gender: str = "girl",
         careful_name: str = "Owen", careful_gender: str = "boy",
         teacher_name: str = "Ms. Hall") -> World:
    world = World()
    eager = world.add(Entity(id=eager_name, kind="character", type=eager_gender, role="eager"))
    careful = world.add(Entity(id=careful_name, kind="character", type=careful_gender, role="careful"))
    teacher = world.add(Entity(id=teacher_name, kind="character", type="teacher", role="teacher"))
    poster = world.add(Entity(id="poster", type="poster", label=topic.poster_title))
    drape_ent = world.add(Entity(id="drape", type="drape", label=drape.label))
    crowd = world.add(Entity(id="crowd", type="crowd", label="the passing students"))
    booth = world.add(Entity(id="booth", type="booth", label=topic.booth_name))

    poster.meters["visible"] = 1.0
    careful.meters["ready"] = 1.0
    eager.meters["calling"] = 0.0
    drape_ent.meters["covering"] = 0.0
    crowd.meters["interest"] = 0.0
    crowd.meters["confusion"] = 0.0
    eager.memes["apology"] = 0.0
    careful.memes["hurt"] = 0.0

    setup_morning(world, eager, careful, teacher, topic, drape)
    world.para()
    slip_drape(world, eager, careful, drape)
    try_to_summon(world, eager, careful, summon)
    speak_hurt(world, eager, careful)
    world.para()
    notice_and_apologize(world, eager, careful, teacher, topic)
    repair_display(world, eager, careful, drape, repair)
    share_roles(world, eager, careful, summon, topic)
    world.para()
    warm_ending(world, eager, careful, topic)

    world.facts.update(
        topic=topic,
        drape_cfg=drape,
        summon_cfg=summon,
        repair_cfg=repair,
        eager=eager,
        careful=careful,
        teacher=teacher,
        poster=poster,
        booth=booth,
        crowd=crowd,
        repeated=summon.repeated,
        outcome=outcome_of(
            StoryParams(
                topic=topic.id,
                drape=drape.id,
                summon=summon.id,
                repair=repair.id,
                eager=eager_name,
                eager_gender=eager_gender,
                careful=careful_name,
                careful_gender=careful_gender,
                teacher=teacher_name,
                seed=None,
            )
        ),
        repaired=poster.meters["visible"] >= THRESHOLD,
        reconciled=careful.memes["hurt"] < THRESHOLD and careful.memes["closeness"] >= THRESHOLD,
    )
    return world


TOPICS = {
    "heart": Topic(
        id="heart",
        booth_name="Healthy Heart Booth",
        poster_title="A Kind Heart and a Strong Heart",
        poster_line="Too much cholesterol can make it harder for the heart to do its job, so we can choose foods and habits that help our hearts stay strong.",
        opening="They wanted their table to feel welcoming, like a little corner where hard health words could sound gentle and understandable.",
        ending_image="The poster stood straight, their voices took turns, and the whole table looked as if friendship had been tucked neatly into every corner.",
        tags={"cholesterol", "heart", "school_fair"},
    ),
    "lunch": Topic(
        id="lunch",
        booth_name="Smart Lunch Booth",
        poster_title="What Helps a Busy Heart",
        poster_line="Some foods help keep cholesterol in a healthy range, and that gives the heart one more reason to smile through a busy school day.",
        opening="Their job was to help the younger students see that healthy choices could begin with an ordinary lunch tray.",
        ending_image="Beside the neat stack of lunch cards, the bright poster shone, and the two friends smiled as if they had learned something larger than a school fact.",
        tags={"cholesterol", "food", "school_fair"},
    ),
    "movement": Topic(
        id="movement",
        booth_name="Move and Smile Booth",
        poster_title="Hearts Like Motion",
        poster_line="Exercise helps the heart stay strong, and learning what cholesterol means can help us understand one more way to care for our bodies.",
        opening="Their corner of the room had paper sneakers, a little jump-rope drawing, and a promise that body words could be taught with kindness.",
        ending_image="Even after the hallway quieted, the booth still looked lively, with the poster clear and the children leaning together in easy peace.",
        tags={"cholesterol", "exercise", "school_fair"},
    ),
}

DRAPES = {
    "paper": Drape(
        id="paper",
        label="paper drape",
        color="crepe-paper",
        weight=1,
        texture="light",
        tags={"drape", "paper"},
    ),
    "felt": Drape(
        id="felt",
        label="felt drape",
        color="blue",
        weight=2,
        texture="soft",
        tags={"drape", "felt"},
    ),
    "velvet": Drape(
        id="velvet",
        label="velvet drape",
        color="red",
        weight=3,
        texture="heavy",
        tags={"drape", "fabric"},
    ),
}

SUMMONS = {
    "chant": SummonMethod(
        id="chant",
        sense=2,
        volume=2,
        repeated=True,
        line="Come see our heart table!",
        style="a bright chant",
        tags={"summon", "repetition"},
    ),
    "bell": SummonMethod(
        id="bell",
        sense=3,
        volume=1,
        repeated=False,
        line="Come learn one heart fact with us!",
        style="a gentle bell-and-smile way",
        tags={"summon", "school"},
    ),
    "card": SummonMethod(
        id="card",
        sense=3,
        volume=0,
        repeated=False,
        line="Would you like to see our poster?",
        style="a quiet hand-out-a-card way",
        tags={"summon", "school"},
    ),
    "megaphone": SummonMethod(
        id="megaphone",
        sense=1,
        volume=3,
        repeated=True,
        line="Everybody over here right now!",
        style="a too-loud parade way",
        tags={"summon"},
    ),
}

REPAIRS = {
    "tape": Repair(
        id="tape",
        hold=1,
        text="smoothed it back with one strip of classroom tape",
        qa_text="smoothed the drape back with classroom tape",
        tags={"tape"},
    ),
    "clips": Repair(
        id="clips",
        hold=2,
        text="fastened the cloth with two bright binder clips",
        qa_text="fastened the drape with binder clips",
        tags={"clips"},
    ),
    "pins": Repair(
        id="pins",
        hold=3,
        text="secured the heavy edge with safety pins from the art drawer",
        qa_text="secured the drape with safety pins",
        tags={"pins"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Tessa", "Ruby", "June", "Ava"]
BOY_NAMES = ["Owen", "Leo", "Milo", "Evan", "Noah", "Theo", "Ben", "Finn"]


CURATED = [
    StoryParams(
        topic="heart",
        drape="felt",
        summon="chant",
        repair="clips",
        eager="Mina",
        eager_gender="girl",
        careful="Owen",
        careful_gender="boy",
        teacher="Ms. Hall",
        seed=None,
    ),
    StoryParams(
        topic="lunch",
        drape="paper",
        summon="bell",
        repair="tape",
        eager="Leo",
        eager_gender="boy",
        careful="Ruby",
        careful_gender="girl",
        teacher="Ms. Park",
        seed=None,
    ),
    StoryParams(
        topic="movement",
        drape="velvet",
        summon="card",
        repair="pins",
        eager="Nora",
        eager_gender="girl",
        careful="Milo",
        careful_gender="boy",
        teacher="Ms. Chen",
        seed=None,
    ),
]


KNOWLEDGE = {
    "cholesterol": [
        (
            "What is cholesterol?",
            "Cholesterol is a waxy substance in the body. Our bodies need some of it, but too much can make it harder for the heart and blood vessels to work well.",
        )
    ],
    "heart": [
        (
            "What does the heart do?",
            "The heart is a strong muscle that pumps blood around the body. It keeps sending blood where it needs to go.",
        )
    ],
    "school_fair": [
        (
            "What is a school fair booth?",
            "A school fair booth is a little table or corner where students share a game, project, or idea with other people. It helps visitors stop, look, and learn.",
        )
    ],
    "drape": [
        (
            "What is a drape?",
            "A drape is a piece of cloth or paper that hangs down. People use it to decorate or cover something.",
        )
    ],
    "repetition": [
        (
            "What does repetition mean in a story?",
            "Repetition means saying or showing something again and again. It can make a feeling stronger or help you notice a problem.",
        )
    ],
    "summon": [
        (
            "What does summon mean?",
            "To summon someone means to call them to come closer. You can summon people with words, a wave, or another signal.",
        )
    ],
    "clips": [
        (
            "What are binder clips for?",
            "Binder clips hold papers or cloth together with a strong pinch. They are useful when tape is not strong enough.",
        )
    ],
    "pins": [
        (
            "What are safety pins for?",
            "Safety pins can fasten cloth and help keep it from slipping. The sharp point closes safely under a little cover.",
        )
    ],
    "tape": [
        (
            "What does tape do?",
            "Tape sticks things in place. It is handy for light decorations and paper.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "school_fair",
    "drape",
    "summon",
    "repetition",
    "cholesterol",
    "heart",
    "clips",
    "pins",
    "tape",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    topic = f["topic"]
    eager = f["eager"]
    careful = f["careful"]
    summon = f["summon_cfg"]
    return [
        f'Write a heartwarming school story that includes the words "drape," "summon," and "cholesterol."',
        f"Tell a story set at a school wellness fair where {eager.id} and {careful.id} make a booth together, a drape slips over a poster, and repetition reveals the problem before the children reconcile.",
        f"Write a gentle story where one child tries to summon visitors with {summon.style}, but listening and teamwork matter more than repeating the same line.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    eager = f["eager"]
    careful = f["careful"]
    teacher = f["teacher"]
    topic = f["topic"]
    drape = f["drape_cfg"]
    summon = f["summon_cfg"]
    repair = f["repair_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two classmates, {eager.id} and {careful.id}, working at a school wellness-fair booth with {teacher.id}. They are trying to help other students learn in a kind way.",
        ),
        (
            "What was hidden by the drape?",
            f"The slipped {drape.label} covered the poster where the children had written about cholesterol and heart health. That mattered because people could not learn the main idea if they could not see the page.",
        ),
        (
            f"Why did {careful.id}'s feelings get hurt?",
            f"{careful.id} had worked hard on the poster, but {eager.id} kept repeating the call to summon visitors while the poster was still hidden. It made {careful.id} feel as if the careful work on the display was being missed.",
        ),
    ]
    if f["outcome"] == "apology_repair":
        qa.append(
            (
                f"How did repetition change the story?",
                f"{eager.id} repeated the same cheerful line again and again, but the repetition did not fix the problem because the poster was hidden. Hearing the call over and over helped both children notice that what they needed most was not more calling, but better listening.",
            )
        )
    else:
        qa.append(
            (
                f"How did the children fix the booth?",
                f"They stopped, looked carefully, and worked together. {careful.id} {repair.qa_text}, so the poster could be seen clearly again.",
            )
        )
    qa.append(
        (
            "How did the children reconcile?",
            f"{eager.id} apologized for not listening, and then the two children shared the job instead of pulling in different directions. One invited visitors while the other explained the poster, so the booth and the friendship both felt whole again.",
        )
    )
    qa.append(
        (
            "What did the poster teach?",
            f'The poster said, "{topic.poster_line}" It turned a big school word into something the younger students could understand.',
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["topic"].tags) | set(f["drape_cfg"].tags) | set(f["summon_cfg"].tags) | set(f["repair_cfg"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_repair_rejection(drape: Drape, repair: Repair) -> str:
    return (
        f"(No story: {repair.id} is too weak for the {drape.label}. "
        f"The drape weighs {drape.weight}, but that repair only holds {repair.hold}. "
        f"Pick a stronger fix so the display can really stay open.)"
    )


def explain_summon_rejection(summon_id: str) -> str:
    summon = SUMMONS[summon_id]
    better = ", ".join(sorted(s.id for s in sensible_summons()))
    return (
        f"(Refusing summon method '{summon_id}': it is too disruptive for school "
        f"(sense={summon.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
sensible_summon(S) :- summon(S), sense(S, V), sense_min(M), V >= M.
holds(D, R) :- drape(D), repair(R), weight(D, W), hold(R, H), H >= W.
valid(T, D, S, R) :- topic(T), drape(D), summon(S), repair(R), sensible_summon(S), holds(D, R).

big_repeat(S) :- repeated(S), volume(S, V), V >= 2.
outcome(apology_repair) :- chosen_summon(S), big_repeat(S).
outcome(quick_repair) :- chosen_summon(S), not big_repeat(S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for topic_id in TOPICS:
        lines.append(asp.fact("topic", topic_id))
    for drape_id, drape in DRAPES.items():
        lines.append(asp.fact("drape", drape_id))
        lines.append(asp.fact("weight", drape_id, drape.weight))
    for summon_id, summon in SUMMONS.items():
        lines.append(asp.fact("summon", summon_id))
        lines.append(asp.fact("sense", summon_id, summon.sense))
        lines.append(asp.fact("volume", summon_id, summon.volume))
        if summon.repeated:
            lines.append(asp.fact("repeated", summon_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("hold", repair_id, repair.hold))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_summon", params.summon)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke-test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a school booth, a slipped drape, repeated calling, and reconciliation."
    )
    ap.add_argument("--topic", choices=TOPICS)
    ap.add_argument("--drape", choices=DRAPES)
    ap.add_argument("--summon", choices=SUMMONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.summon and SUMMONS[args.summon].sense < SENSE_MIN:
        raise StoryError(explain_summon_rejection(args.summon))
    if args.drape and args.repair:
        drape = DRAPES[args.drape]
        repair = REPAIRS[args.repair]
        if not repair_holds(drape, repair):
            raise StoryError(explain_repair_rejection(drape, repair))

    combos = [
        c for c in valid_combos()
        if (args.topic is None or c[0] == args.topic)
        and (args.drape is None or c[1] == args.drape)
        and (args.summon is None or c[2] == args.summon)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    topic_id, drape_id, summon_id, repair_id = rng.choice(sorted(combos))
    eager_gender = rng.choice(["girl", "boy"])
    careful_gender = "boy" if eager_gender == "girl" else "girl" if rng.random() < 0.6 else eager_gender
    eager_name = _pick_name(rng, eager_gender)
    careful_name = _pick_name(rng, careful_gender, avoid=eager_name)
    teacher = rng.choice(["Ms. Hall", "Ms. Park", "Ms. Chen", "Ms. Diaz"])

    return StoryParams(
        topic=topic_id,
        drape=drape_id,
        summon=summon_id,
        repair=repair_id,
        eager=eager_name,
        eager_gender=eager_gender,
        careful=careful_name,
        careful_gender=careful_gender,
        teacher=teacher,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.topic not in TOPICS:
        raise StoryError(f"(Unknown topic: {params.topic})")
    if params.drape not in DRAPES:
        raise StoryError(f"(Unknown drape: {params.drape})")
    if params.summon not in SUMMONS:
        raise StoryError(f"(Unknown summon method: {params.summon})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    drape = DRAPES[params.drape]
    summon = SUMMONS[params.summon]
    repair = REPAIRS[params.repair]

    if summon.sense < SENSE_MIN:
        raise StoryError(explain_summon_rejection(params.summon))
    if not repair_holds(drape, repair):
        raise StoryError(explain_repair_rejection(drape, repair))

    world = tell(
        topic=TOPICS[params.topic],
        drape=drape,
        summon=summon,
        repair=repair,
        eager_name=params.eager,
        eager_gender=params.eager_gender,
        careful_name=params.careful,
        careful_gender=params.careful_gender,
        teacher_name=params.teacher,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (topic, drape, summon, repair) combos:\n")
        for topic, drape, summon, repair in combos:
            print(f"  {topic:9} {drape:7} {summon:8} {repair}")
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
            header = f"### {p.eager} & {p.careful}: {p.topic}, {p.drape}, {p.summon}, {p.repair} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
