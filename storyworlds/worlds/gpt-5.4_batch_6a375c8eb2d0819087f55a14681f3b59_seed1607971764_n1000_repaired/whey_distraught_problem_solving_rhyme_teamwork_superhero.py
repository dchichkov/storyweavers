#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py
=======================================================================================

A standalone story world about a tiny superhero team making fresh cheese in capes.

The source-tale premise behind this world:
- three children are playing superheroes in a kitchen
- they are making soft cheese for a snack
- the curds drip whey through a cheesecloth bundle
- a problem appears: a loose knot, a wobbly bowl, or a bundle too heavy to hold
- one helper becomes distraught
- the team uses problem solving, teamwork, and a rhyming hero chant to fix it
- the ending shows what changed: calm hands, saved curds, and a shared snack

Run it
------
python storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py
python storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py --all
python storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py --qa --json
python storyworlds/worlds/gpt-5.4/whey_distraught_problem_solving_rhyme_teamwork_superhero.py --verify
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    intro: str
    ending: str
    available_tools: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    severity: int
    setup_text: str
    alarm_text: str
    risk_text: str
    fail_text: str
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
class Tool:
    id: str
    label: str
    phrase: str
    power: int
    fit: dict[str, int] = field(default_factory=dict)
    action_text: str = ""
    qa_text: str = ""
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
class Rhyme:
    id: str
    chant: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "partner", "apprentice"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(setting=self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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


def _r_whey_puddle(world: World) -> list[str]:
    bundle = world.get("bundle")
    bowl = world.get("bowl")
    floor = world.get("floor")
    apprentice = world.get("apprentice")
    out: list[str] = []
    if bundle.meters["dripping"] < THRESHOLD:
        return out
    if bowl.attrs.get("catching_whey", False):
        return out
    sig = ("whey_puddle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["slippery"] += 1
    floor.meters["whey"] += 1
    apprentice.memes["fear"] += 1
    out.append("__whey__")
    return out


def _r_curds_lost(world: World) -> list[str]:
    bundle = world.get("bundle")
    curds = world.get("curds")
    apprentice = world.get("apprentice")
    out: list[str] = []
    if bundle.meters["fall_risk"] < THRESHOLD:
        return out
    if bundle.attrs.get("supported", False):
        return out
    sig = ("curds_lost",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    curds.meters["lost"] += 1
    apprentice.memes["fear"] += 1
    out.append("__loss__")
    return out


def _r_team_calm(world: World) -> list[str]:
    captain = world.get("captain")
    partner = world.get("partner")
    apprentice = world.get("apprentice")
    bundle = world.get("bundle")
    floor = world.get("floor")
    out: list[str] = []
    if bundle.attrs.get("supported", False) and not floor.meters["slippery"]:
        sig = ("team_calm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        for kid in (captain, partner, apprentice):
            kid.memes["relief"] += 1
            kid.memes["confidence"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="whey_puddle", tag="physical", apply=_r_whey_puddle),
    Rule(name="curds_lost", tag="physical", apply=_r_curds_lost),
    Rule(name="team_calm", tag="emotional", apply=_r_team_calm),
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


SETTINGS = {
    "clubhouse": Setting(
        id="clubhouse",
        place="the Bright-Beam Clubhouse kitchen",
        intro="Sunlight flashed on mixing bowls, and three paper capes swished across the tiles.",
        ending="On the counter, the little snack plate looked as if a superhero team had truly saved the day.",
        available_tools={"clip", "bowl", "colander"},
    ),
    "school": Setting(
        id="school",
        place="the school cooking room",
        intro="The windows glowed after school, and the long table looked like a secret hero lab.",
        ending="By the sink, their capes hung crooked and proud, like flags after a mission.",
        available_tools={"clip", "bowl", "colander"},
    ),
    "farmstand": Setting(
        id="farmstand",
        place="the farm-stand kitchen tent",
        intro="Canvas walls fluttered in the breeze, and the snack table smelled of warm milk and lemons.",
        ending="Outside the tent, evening light turned their capes bright gold as they shared the rescued snack.",
        available_tools={"clip", "colander"},
    ),
}

PROBLEMS = {
    "loose_knot": Problem(
        id="loose_knot",
        severity=1,
        setup_text="The cheesecloth bundle sagged, and the knot at the top began to creep open.",
        alarm_text="A few soft curds pushed toward the gap while thin yellow whey dripped faster and faster.",
        risk_text="If the knot gave way, the curds would slide out and the team would lose their snack.",
        fail_text="The knot slipped open and the curds slumped out in a sleepy plop.",
        tags={"cheese", "whey", "knot"},
    ),
    "wobbly_bowl": Problem(
        id="wobbly_bowl",
        severity=1,
        setup_text="The little bowl under the bundle sat on a folded towel and rocked from side to side.",
        alarm_text="Each drip of whey made the bowl shimmy harder, as if it might tip and splash the floor.",
        risk_text="If the bowl tipped, the floor would turn slippery and nobody could work safely.",
        fail_text="The bowl tipped with a slosh, and whey skated across the tiles.",
        tags={"cheese", "whey", "bowl"},
    ),
    "heavy_bundle": Problem(
        id="heavy_bundle",
        severity=2,
        setup_text="The curd bundle had grown heavy, and one small hand was trying very hard to hold it up alone.",
        alarm_text="The cloth twisted lower and lower while a bright thread of whey ran down to the wrist below.",
        risk_text="If nobody supported the bundle, the curds could drop before they had time to drain.",
        fail_text="The heavy bundle lurched down, and the curds tumbled before the team could catch them.",
        tags={"cheese", "whey", "heavy"},
    ),
}

TOOLS = {
    "clip": Tool(
        id="clip",
        label="spring clip",
        phrase="a red spring clip",
        power=1,
        fit={"loose_knot": 3, "heavy_bundle": 1},
        action_text="snapped a red spring clip over the slipping cloth and pinched the top tight",
        qa_text="used a spring clip to pinch the loose cloth shut",
        tags={"clip", "problem_solving"},
    ),
    "bowl": Tool(
        id="bowl",
        label="mixing bowl",
        phrase="a wide mixing bowl",
        power=1,
        fit={"wobbly_bowl": 3},
        action_text="slid a wide mixing bowl under the bundle and set it flat on the counter",
        qa_text="set a wide mixing bowl flat under the bundle to catch the whey",
        tags={"bowl", "problem_solving"},
    ),
    "colander": Tool(
        id="colander",
        label="colander",
        phrase="a sturdy blue colander",
        power=2,
        fit={"heavy_bundle": 3, "loose_knot": 1},
        action_text="set a sturdy blue colander over a bowl and rested the whole bundle inside it",
        qa_text="rested the bundle in a colander so it was fully supported",
        tags={"colander", "problem_solving"},
    ),
}

RHYMES = {
    "steady": Rhyme(
        id="steady",
        chant='"Steady and ready, left and right; hero hands can fix it right!"',
        tags={"rhyme", "teamwork"},
    ),
    "curds": Rhyme(
        id="curds",
        chant='"Clip it, grip it, save the day; catch the curds and guide the whey!"',
        tags={"rhyme", "teamwork", "whey"},
    ),
    "team": Rhyme(
        id="team",
        chant='"Think it through and do our part; three brave helpers, one calm heart!"',
        tags={"rhyme", "teamwork"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Nora", "Ivy", "Ruby", "Ella"]
BOY_NAMES = ["Max", "Leo", "Finn", "Eli", "Theo", "Jack", "Sam", "Ben"]
TRAITS = ["brave", "careful", "quick-thinking", "kind", "steady", "clever"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    rhyme: str
    captain: str
    captain_gender: str
    partner: str
    partner_gender: str
    apprentice: str
    apprentice_gender: str
    mentor: str
    delay: int = 0
    captain_trait: str = "brave"
    partner_trait: str = "steady"
    apprentice_trait: str = "kind"
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


def tool_fit(problem_id: str, tool_id: str) -> int:
    return TOOLS[tool_id].fit.get(problem_id, 0)


def sensible_tools(problem_id: str) -> list[str]:
    return [tid for tid in TOOLS if tool_fit(problem_id, tid) >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for problem_id in PROBLEMS:
            for tool_id in sensible_tools(problem_id):
                if tool_id in setting.available_tools:
                    combos.append((setting_id, problem_id, tool_id))
    return combos


def explain_tool(problem_id: str, tool_id: str) -> str:
    fit = tool_fit(problem_id, tool_id)
    if fit >= SENSE_MIN:
        return ""
    problem = PROBLEMS[problem_id]
    tool = TOOLS[tool_id]
    return (
        f"(Refusing tool '{tool_id}': {tool.label} is not a sensible fix for {problem.id}. "
        f"This world only tells stories where the chosen tool honestly matches the kitchen problem.)"
    )


def outcome_of(params: StoryParams) -> str:
    tool = TOOLS[params.tool]
    problem = PROBLEMS[params.problem]
    severity = problem.severity + params.delay
    if tool.power >= severity:
        return "smooth_save" if params.delay == 0 else "messy_save"
    return "lost_batch"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    return {
        "slippery": sim.get("floor").meters["slippery"] >= THRESHOLD,
        "lost": sim.get("curds").meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, captain: Entity, partner: Entity, apprentice: Entity, mentor: Entity) -> None:
    world.say(
        f"{world.setting.intro} {captain.id}, {partner.id}, and {apprentice.id} called themselves "
        f"the Whey Rangers, and today their mission was to make a soft cheese snack with {mentor.label_word}."
    )
    world.say(
        f"{mentor.label_word.capitalize()} showed them the pot where fluffy curds had formed, "
        f"while pale whey shimmered underneath like a tiny yellow pond."
    )


def assign_roles(world: World, captain: Entity, partner: Entity, apprentice: Entity) -> None:
    for kid in (captain, partner, apprentice):
        kid.memes["joy"] += 1
    world.say(
        f'"Captain Ladle takes the lead!" {captain.id} said. '
        f'"Mixer Meteor watches the bowl," {partner.id} answered. '
        f'"And I am Drip Defender," {apprentice.id} whispered, grinning into {apprentice.pronoun("possessive")} cape.'
    )


def mission_setup(world: World) -> None:
    bundle = world.get("bundle")
    bundle.meters["dripping"] = 1.0
    world.say(
        "They spooned the curds into a square of cheesecloth and lifted the bundle over a bowl to let it drain."
    )


def problem_appears(world: World, problem: Problem, apprentice: Entity) -> None:
    world.say(problem.setup_text)
    world.say(problem.alarm_text)
    apprentice.memes["fear"] += 1
    apprentice.memes["distraught"] += 1
    world.say(
        f"{apprentice.id}'s smile vanished. {apprentice.pronoun().capitalize()} looked downright distraught and clutched the edge of the counter."
    )
    world.say(problem.risk_text)


def warn_with_prediction(world: World, captain: Entity, partner: Entity, apprentice: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_slippery"] = pred["slippery"]
    world.facts["predicted_lost"] = pred["lost"]
    if pred["lost"] and pred["slippery"]:
        world.say(
            f'{captain.id} took one good look and said, "If we rush, we could lose the curds and make the floor slippery too."'
        )
    elif pred["lost"]:
        world.say(
            f'{captain.id} narrowed {captain.pronoun("possessive")} eyes. "If we do nothing, the curds will fall before snack time."'
        )
    elif pred["slippery"]:
        world.say(
            f'{partner.id} pointed at the dripping bundle. "If we do nothing, the whey will splash and the floor will turn slippery."'
        )
    apprentice.memes["trust"] += 1


def use_tool(world: World, tool: Tool, rhyme: Rhyme, captain: Entity, partner: Entity, apprentice: Entity, delay: int) -> None:
    bundle = world.get("bundle")
    bowl = world.get("bowl")
    floor = world.get("floor")
    world.say(
        f'"Team huddle!" said {captain.id}. {partner.id} fetched {tool.phrase}, {apprentice.id} steadied the cloth with two careful hands, '
        f"and together they chanted {rhyme.chant}"
    )
    if delay > 0:
        propagate(world, narrate=False)
        if floor.meters["slippery"] >= THRESHOLD and not world.facts.get("spill_narrated"):
            world.facts["spill_narrated"] = True
            world.say(
                "For one second they were too slow. A ribbon of whey slipped over the rim and drew a shiny curl across the counter and floor."
            )
    if tool.id == "bowl":
        bowl.attrs["catching_whey"] = True
        bundle.attrs["supported"] = True
    elif tool.id == "clip":
        if world.facts["problem"].id == "loose_knot":
            bundle.attrs["supported"] = True
            bowl.attrs["catching_whey"] = True
        else:
            bundle.attrs["supported"] = False
    elif tool.id == "colander":
        bundle.attrs["supported"] = True
        bowl.attrs["catching_whey"] = True
    world.say(f"Then {partner.id} {tool.action_text}.")
    if floor.meters["slippery"] >= THRESHOLD:
        floor.meters["slippery"] = 0.0
        world.say(
            f"{captain.id} whisked a towel across the shiny whey while {apprentice.id} kept the bundle from wobbling."
        )
    propagate(world, narrate=False)


def celebrate_success(world: World, tool: Tool, apprentice: Entity, mentor: Entity) -> None:
    curds = world.get("curds")
    curds.meters["saved"] += 1
    apprentice.memes["fear"] = 0.0
    apprentice.memes["distraught"] = 0.0
    apprentice.memes["joy"] += 1
    world.say(
        "The cloth stopped twisting. The drips slowed to a calm pat-pat, and the whey landed exactly where it should."
    )
    world.say(
        f'{apprentice.id} let out a breath and smiled again. "{tool.label.capitalize()} for the win," {apprentice.pronoun()} said.'
    )
    world.say(
        f"{mentor.label_word.capitalize()} laughed softly. \"That was real hero work,\" {mentor.pronoun()} said. "
        "Nobody shouted, nobody gave up, and everyone used their brain before their hands."
    )
    world.say(world.setting.ending)


def lose_batch(world: World, problem: Problem, apprentice: Entity, mentor: Entity) -> None:
    curds = world.get("curds")
    floor = world.get("floor")
    curds.meters["lost"] = 1.0
    apprentice.memes["fear"] += 1
    apprentice.memes["distraught"] += 1
    if floor.meters["slippery"] < THRESHOLD:
        floor.meters["slippery"] = 1.0
    world.say(problem.fail_text)
    world.say(
        f"{apprentice.id} blinked hard and looked distraught all over again, but {mentor.label_word} crouched beside {apprentice.pronoun('object')} at once."
    )
    world.say(
        f'"We lost this batch, not our courage," {mentor.label_word} said. "Heroes learn, wipe up the mess, and try again together."'
    )
    apprentice.memes["fear"] = 0.0
    apprentice.memes["distraught"] = 0.0
    apprentice.memes["hope"] += 1
    world.say(
        "So they cleaned the whey, tied a better cloth, and started over more slowly, this time with four calm hands around the bowl."
    )


def ending_image(world: World, apprentice: Entity) -> None:
    if world.get("curds").meters["saved"] >= THRESHOLD:
        world.say(
            f"Soon they spread the soft cheese on little crackers, and {apprentice.id} bit one with a proud superhero grin."
        )
    else:
        world.say(
            f"When the next batch was finally ready, {apprentice.id} tasted it first and nodded as if a tiny cape were fluttering inside {apprentice.pronoun('object')}."
        )


def tell(
    setting: Setting,
    problem: Problem,
    tool: Tool,
    rhyme: Rhyme,
    captain_name: str,
    captain_gender: str,
    partner_name: str,
    partner_gender: str,
    apprentice_name: str,
    apprentice_gender: str,
    mentor_type: str,
    delay: int,
    captain_trait: str,
    partner_trait: str,
    apprentice_trait: str,
) -> World:
    world = World(setting=setting)

    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        traits=[captain_trait],
        attrs={"display": captain_name},
    ))
    partner = world.add(Entity(
        id="partner",
        kind="character",
        type=partner_gender,
        label=partner_name,
        role="partner",
        traits=[partner_trait],
        attrs={"display": partner_name},
    ))
    apprentice = world.add(Entity(
        id="apprentice",
        kind="character",
        type=apprentice_gender,
        label=apprentice_name,
        role="apprentice",
        traits=[apprentice_trait],
        attrs={"display": apprentice_name},
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type=mentor_type,
        label="the parent",
        role="mentor",
        attrs={"display": mentor_type},
    ))
    world.add(Entity(
        id="bundle",
        type="cheesecloth",
        label="cheesecloth bundle",
        attrs={"supported": False},
    ))
    world.add(Entity(
        id="bowl",
        type="bowl",
        label="catch bowl",
        attrs={"catching_whey": False},
    ))
    world.add(Entity(
        id="floor",
        type="floor",
        label="floor",
        attrs={},
    ))
    world.add(Entity(
        id="curds",
        type="curds",
        label="soft cheese curds",
        attrs={},
    ))

    world.facts.update(
        setting=setting,
        problem=problem,
        tool=tool,
        rhyme=rhyme,
        delay=delay,
        captain=captain,
        partner=partner,
        apprentice=apprentice,
        mentor=mentor,
        spill_narrated=False,
        predicted_slippery=False,
        predicted_lost=False,
    )

    mission_setup(world)
    bundle = world.get("bundle")
    bowl = world.get("bowl")
    if problem.id == "loose_knot":
        bundle.meters["fall_risk"] = 1.0
        bowl.attrs["catching_whey"] = True
    elif problem.id == "wobbly_bowl":
        bowl.attrs["catching_whey"] = False
        bundle.attrs["supported"] = True
    elif problem.id == "heavy_bundle":
        bundle.meters["fall_risk"] = 1.0
        bowl.attrs["catching_whey"] = delay == 0

    introduce(world, captain, partner, apprentice, mentor)
    assign_roles(world, captain, partner, apprentice)
    world.para()
    world.say(f"They were in {setting.place}.")
    problem_appears(world, problem, apprentice)
    warn_with_prediction(world, captain, partner, apprentice)
    world.para()

    use_tool(world, tool, rhyme, captain, partner, apprentice, delay)
    if outcome_of(StoryParams(
        setting=setting.id,
        problem=problem.id,
        tool=tool.id,
        rhyme=rhyme.id,
        captain=captain.label,
        captain_gender=captain.type,
        partner=partner.label,
        partner_gender=partner.type,
        apprentice=apprentice.label,
        apprentice_gender=apprentice.type,
        mentor=mentor.type,
        delay=delay,
        captain_trait=captain_trait,
        partner_trait=partner_trait,
        apprentice_trait=apprentice_trait,
    )) == "lost_batch":
        lose_batch(world, problem, apprentice, mentor)
    else:
        celebrate_success(world, tool, apprentice, mentor)

    world.para()
    ending_image(world, apprentice)
    world.facts["outcome"] = outcome_of(StoryParams(
        setting=setting.id,
        problem=problem.id,
        tool=tool.id,
        rhyme=rhyme.id,
        captain=captain.label,
        captain_gender=captain.type,
        partner=partner.label,
        partner_gender=partner.type,
        apprentice=apprentice.label,
        apprentice_gender=apprentice.type,
        mentor=mentor.type,
        delay=delay,
        captain_trait=captain_trait,
        partner_trait=partner_trait,
        apprentice_trait=apprentice_trait,
    ))
    return world


def pair_label(a: Entity, b: Entity, c: Entity) -> str:
    return f"{a.label}, {b.label}, and {c.label}"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    problem = f["problem"]
    rhyme = f["rhyme"]
    apprentice = f["apprentice"]
    outcome = f["outcome"]
    prompts = [
        f'Write a superhero story for a 3-to-5-year-old where a tiny team solves a kitchen problem together in {setting.place}. Include the word "whey".',
        f'Write a warm story where one child becomes distraught when cheese curds are in trouble, and the team uses problem solving, teamwork, and a rhyme to help.',
        f'Write a short cape-and-kitchen adventure that includes this chant: {rhyme.chant}',
    ]
    if outcome == "lost_batch":
        prompts.append(
            f"Make the problem a little harder: the team tries to save the bundle, loses the first batch, and then learns to start again calmly."
        )
    else:
        prompts.append(
            f"Let the problem be {problem.id}, but end with the snack saved and {apprentice.label} smiling again."
        )
    return prompts


KNOWLEDGE = {
    "whey": [(
        "What is whey?",
        "Whey is the watery part of milk that is left after curds form. It can drip out of cheesecloth while soft cheese drains."
    )],
    "curds": [(
        "What are curds?",
        "Curds are the soft, thicker parts of milk that clump together when cheese starts to form. People can drain them to make fresh cheese."
    )],
    "colander": [(
        "What is a colander for?",
        "A colander is a bowl with holes in it. It supports food while liquid drains away."
    )],
    "clip": [(
        "What does a clip do?",
        "A clip pinches things together so they do not slip apart. In a kitchen, that can help hold cloth shut."
    )],
    "bowl": [(
        "Why use a wide bowl under something drippy?",
        "A wide bowl catches drips better because it gives the liquid a bigger place to land. That helps keep counters and floors cleaner."
    )],
    "teamwork": [(
        "Why is teamwork useful when a problem happens?",
        "Teamwork helps because one person can steady, another can fetch, and another can think. Problems often get smaller when people help each other at the same time."
    )],
    "rhyme": [(
        "Why can a rhyme help during a task?",
        "A rhyme can help people stay calm and remember what to do next. It also makes everyone move together."
    )],
}
KNOWLEDGE_ORDER = ["whey", "curds", "clip", "bowl", "colander", "teamwork", "rhyme"]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    partner = f["partner"]
    apprentice = f["apprentice"]
    mentor = f["mentor"]
    problem = f["problem"]
    tool = f["tool"]
    rhyme = f["rhyme"]
    outcome = f["outcome"]
    team = pair_label(captain, partner, apprentice)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about three children playing superheroes: {team}. They are making soft cheese with {mentor.label_word} and trying to act brave and careful at the same time."
        ),
        (
            "Why was there whey in the story?",
            "The children were draining fresh cheese, so the watery part of the milk was dripping away. That watery part is called whey, and its drips showed the team where the trouble was happening."
        ),
        (
            f"Why did {apprentice.label} become distraught?",
            f"{apprentice.label} saw that the cheese bundle was in trouble and thought the snack might be ruined. The danger felt big because {problem.risk_text.lower()}"
        ),
        (
            "How did the team solve the problem?",
            f"They stopped rushing, thought about what was going wrong, and worked together. Then they {tool.qa_text} while chanting {rhyme.chant}, which helped them move as one team."
        ),
    ]
    if outcome == "smooth_save":
        qa.append((
            "What changed after they fixed it?",
            "The bundle stopped wobbling and the whey landed safely where it belonged. That let the children finish the snack calmly, so the scary moment turned back into a game."
        ))
    elif outcome == "messy_save":
        qa.append((
            "Did anything spill before the fix worked?",
            "Yes. A little whey splashed first, but the team wiped it quickly and still saved the curds. Their teamwork mattered because they solved the mess and the main problem at the same time."
        ))
    else:
        qa.append((
            "Did the team save the first batch?",
            "No, they lost the first batch of curds. But the story still ends hopefully because they cleaned up, learned from the mistake, and tried again together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "rhyme", "whey", "curds"} | set(world.facts["tool"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label!r}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="clubhouse",
        problem="loose_knot",
        tool="clip",
        rhyme="curds",
        captain="Luna",
        captain_gender="girl",
        partner="Max",
        partner_gender="boy",
        apprentice="Ivy",
        apprentice_gender="girl",
        mentor="mother",
        delay=0,
        captain_trait="brave",
        partner_trait="steady",
        apprentice_trait="kind",
    ),
    StoryParams(
        setting="school",
        problem="wobbly_bowl",
        tool="bowl",
        rhyme="steady",
        captain="Theo",
        captain_gender="boy",
        partner="Ruby",
        partner_gender="girl",
        apprentice="Mia",
        apprentice_gender="girl",
        mentor="father",
        delay=1,
        captain_trait="quick-thinking",
        partner_trait="careful",
        apprentice_trait="kind",
    ),
    StoryParams(
        setting="farmstand",
        problem="heavy_bundle",
        tool="colander",
        rhyme="team",
        captain="Finn",
        captain_gender="boy",
        partner="Ava",
        partner_gender="girl",
        apprentice="Nora",
        apprentice_gender="girl",
        mentor="mother",
        delay=0,
        captain_trait="clever",
        partner_trait="steady",
        apprentice_trait="kind",
    ),
    StoryParams(
        setting="clubhouse",
        problem="heavy_bundle",
        tool="colander",
        rhyme="curds",
        captain="Ben",
        captain_gender="boy",
        partner="Ella",
        partner_gender="girl",
        apprentice="Zoe",
        apprentice_gender="girl",
        mentor="father",
        delay=1,
        captain_trait="brave",
        partner_trait="quick-thinking",
        apprentice_trait="kind",
    ),
    StoryParams(
        setting="school",
        problem="heavy_bundle",
        tool="clip",
        rhyme="steady",
        captain="Sam",
        captain_gender="boy",
        partner="Luna",
        partner_gender="girl",
        apprentice="Ivy",
        apprentice_gender="girl",
        mentor="mother",
        delay=1,
        captain_trait="brave",
        partner_trait="careful",
        apprentice_trait="kind",
    ),
]


ASP_RULES = r"""
sensible(P, T) :- fit(P, T, S), sense_min(M), S >= M.
valid(Place, P, T) :- place(Place), problem(P), tool(T), available(Place, T), sensible(P, T).

severity_total(V) :- chosen_problem(P), severity(P, S), delay(D), V = S + D.
contained :- chosen_tool(T), power(T, Pw), severity_total(V), Pw >= V.

outcome(smooth_save) :- contained, delay(0).
outcome(messy_save) :- contained, delay(D), D > 0.
outcome(lost_batch) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for tid in sorted(setting.available_tools):
            lines.append(asp.fact("available", sid, tid))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, problem.severity))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, tool.power))
        for pid, fit in sorted(tool.fit.items()):
            lines.append(asp.fact("fit", pid, tid, fit))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_tool", params.tool),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero kitchen story world: whey, a distraught helper, and a team problem-solving mission."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the team waits before acting")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.problem and args.tool:
        reason = explain_tool(args.problem, args.tool)
        if reason:
            raise StoryError(reason)
    if args.setting and args.tool and args.tool not in SETTINGS[args.setting].available_tools:
        raise StoryError(
            f"(No story: {TOOLS[args.tool].label} is not available in {SETTINGS[args.setting].place}.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.problem is None or combo[1] == args.problem)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, problem_id, tool_id = rng.choice(sorted(combos))
    rhyme_id = args.rhyme or rng.choice(sorted(RHYMES))
    mentor = args.mentor or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])

    captain_gender = rng.choice(["girl", "boy"])
    captain_name = _pick_name(rng, captain_gender, set())
    partner_gender = rng.choice(["girl", "boy"])
    partner_name = _pick_name(rng, partner_gender, {captain_name})
    apprentice_gender = rng.choice(["girl", "boy"])
    apprentice_name = _pick_name(rng, apprentice_gender, {captain_name, partner_name})

    return StoryParams(
        setting=setting_id,
        problem=problem_id,
        tool=tool_id,
        rhyme=rhyme_id,
        captain=captain_name,
        captain_gender=captain_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        apprentice=apprentice_name,
        apprentice_gender=apprentice_gender,
        mentor=mentor,
        delay=delay,
        captain_trait=rng.choice(TRAITS),
        partner_trait=rng.choice(TRAITS),
        apprentice_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    if params.mentor not in {"mother", "father"}:
        raise StoryError(f"(Unknown mentor type: {params.mentor})")
    if params.tool not in SETTINGS[params.setting].available_tools:
        raise StoryError(
            f"(No story: {TOOLS[params.tool].label} is not available in {SETTINGS[params.setting].place}.)"
        )
    reason = explain_tool(params.problem, params.tool)
    if reason:
        raise StoryError(reason)

    world = tell(
        setting=SETTINGS[params.setting],
        problem=PROBLEMS[params.problem],
        tool=TOOLS[params.tool],
        rhyme=RHYMES[params.rhyme],
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        apprentice_name=params.apprentice,
        apprentice_gender=params.apprentice_gender,
        mentor_type=params.mentor,
        delay=params.delay,
        captain_trait=params.captain_trait,
        partner_trait=params.partner_trait,
        apprentice_trait=params.apprentice_trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace("captain", params.captain).replace("partner", params.partner).replace("apprentice", params.apprentice),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    text = sample.story
    if sample.world is not None:
        w = sample.world
        repl = {
            "captain": w.facts["captain"].label,
            "partner": w.facts["partner"].label,
            "apprentice": w.facts["apprentice"].label,
        }
        for k, v in repl.items():
            text = text.replace(k, v)
    print(text)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch} outcome differences.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (setting, problem, tool) combos:\n")
        for setting_id, problem_id, tool_id in combos:
            print(f"  {setting_id:10} {problem_id:12} {tool_id}")
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
            header = f"### {p.setting}: {p.problem} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
