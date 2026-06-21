#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py
=======================================================================

A standalone story world for a tall-tale flavored fiction-making problem:
two children want to make the grandest made-up story picture in town, but
there is only one giant drawing tool. They first tug over it, then a calm
grown-up helps them solve the sharing problem with a sensible plan.

The world models:
- typed entities with physical meters and emotional memes
- a small reasonableness gate over surface/tool compatibility
- a simple outcome model for whether the sharing plan finishes the giant work
- an inline ASP twin that mirrors the Python gate and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py --setting schoolyard --project river_map
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py --tool chalkbeam --setting barn
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/fiction_sharing_problem_solving_tall_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    surface: str = ""
    usable_on: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "teacher", "librarian", "woman"}
        male = {"boy", "father", "uncle", "man"}
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
            "teacher": "teacher",
            "librarian": "librarian",
            "aunt": "aunt",
        }.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    surface: str
    opener: str
    sky: str
    supports: set[str] = field(default_factory=set)
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
class Project:
    id: str
    label: str
    phrase: str
    demand: int
    surfaces: set[str] = field(default_factory=set)
    boast: str = ""
    ending: str = ""
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
class Tool:
    id: str
    label: str
    phrase: str
    marks: str
    power: int
    stroke: str
    squeak: str
    surfaces: set[str] = field(default_factory=set)
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
class Plan:
    id: str
    label: str
    sense: int
    power: int
    method: str
    success_text: str
    close_call_text: str
    fail_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        return [e for e in self.entities.values() if e.role in {"starter", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_tug_smudge(world: World) -> list[str]:
    art = world.get("art")
    tool = world.get("tool")
    if tool.meters["tugged"] < THRESHOLD:
        return []
    sig = ("tug_smudge",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    art.meters["smudged"] += 1
    tool.meters["wobble"] += 1
    for kid in world.kids():
        kid.memes["frustration"] += 1
    return ["__smudge__"]


def _r_smudge_worry(world: World) -> list[str]:
    art = world.get("art")
    if art.meters["smudged"] < THRESHOLD:
        return []
    sig = ("smudge_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_finished_pride(world: World) -> list[str]:
    art = world.get("art")
    if art.meters["finished"] < THRESHOLD:
        return []
    sig = ("finished_pride",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["pride"] += 1
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="tug_smudge", tag="physical", apply=_r_tug_smudge),
    Rule(name="smudge_worry", tag="emotional", apply=_r_smudge_worry),
    Rule(name="finished_pride", tag="emotional", apply=_r_finished_pride),
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


def project_supported(setting: Setting, project: Project) -> bool:
    return project.id in setting.supports and setting.surface in project.surfaces


def tool_fits(setting: Setting, tool: Tool) -> bool:
    return setting.surface in tool.surfaces


def sensible_plans() -> list[Plan]:
    return [p for p in PLANS.values() if p.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for project_id, project in PROJECTS.items():
            if not project_supported(setting, project):
                continue
            for tool_id, tool in TOOLS.items():
                if tool_fits(setting, tool):
                    combos.append((setting_id, project_id, tool_id))
    return combos


def outcome_level(project: Project, tool: Tool, plan: Plan, delay: int) -> str:
    total = tool.power + plan.power
    need = project.demand + delay
    if total > need:
        return "grand"
    if total == need:
        return "just_in_time"
    return "unfinished"


def predict_finish(world: World, project: Project, tool: Tool, plan: Plan, delay: int) -> dict:
    sim = world.copy()
    art = sim.get("art")
    art.meters["progress"] += tool.power + plan.power
    art.meters["deadline"] = float(project.demand + delay)
    level = outcome_level(project, tool, plan, delay)
    if level in {"grand", "just_in_time"}:
        art.meters["finished"] += 1
        if level == "grand":
            art.meters["huge"] += 1
    else:
        art.meters["unfinished"] += 1
    propagate(sim, narrate=False)
    return {
        "level": level,
        "progress": art.meters["progress"],
        "deadline": art.meters["deadline"],
        "finished": art.meters["finished"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting, project: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["imagination"] += 1
    world.say(
        f"In {setting.place}, where {setting.sky}, {a.id} and {b.id} came with a plan "
        f"so big it sounded half like homework and half like fiction."
    )
    world.say(
        f"They wanted to make {project.phrase}, a piece so grand {project.boast}."
    )
    world.say(setting.opener)


def spot_one_tool(world: World, a: Entity, b: Entity, tool: Tool) -> None:
    world.say(
        f"On the ground waited {tool.phrase}, ready to leave {tool.marks}. "
        f"It was plenty for one pair of hands and not nearly enough for two eager ones."
    )
    world.say(
        f'"I saw it first," said {a.id}. "{tool.label.capitalize()} for the title!" '
        f'"Then I need it for the brave parts," said {b.id}.'
    )


def tug(world: World, a: Entity, b: Entity, tool: Tool, project: Project) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["tugged"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They both grabbed at once. {tool.squeak} The line they meant for {project.label} "
        f"zigged, zagged, and slithered across the middle like a startled eel."
    )
    world.say(
        f"For one breath they looked at the wobble and knew that if they kept pulling, "
        f"their giant idea would shrink into a squabble."
    )


def helper_warn(world: World, helper: Entity, a: Entity, b: Entity,
                project: Project, tool: Tool, plan: Plan, delay: int) -> None:
    pred = predict_finish(world, project, tool, plan, delay)
    world.facts["predicted_level"] = pred["level"]
    world.facts["predicted_deadline"] = pred["deadline"]
    helper_word = helper.label_word.capitalize()
    if pred["level"] == "unfinished":
        line = (
            f'"At this rate," {helper_word} said, "that grand piece will still be missing a corner '
            f'when the bell rings. The problem is not the tool. The problem is the sharing."'
        )
    else:
        line = (
            f'"The tool is big enough," {helper_word} said, "if your plan is bigger than your tugging. '
            f'The trick is to share with a purpose."'
        )
    world.say(line)
    world.say(
        f"{helper_word} tapped the shaky stripe and showed them {plan.method}."
    )


def solve(world: World, a: Entity, b: Entity, helper: Entity,
          project: Project, tool: Tool, plan: Plan, delay: int) -> str:
    art = world.get("art")
    tool_ent = world.get("tool")
    tool_ent.meters["shared"] += 1
    a.memes["frustration"] = 0.0
    b.memes["frustration"] = 0.0
    a.memes["cooperation"] += 1
    b.memes["cooperation"] += 1
    pred = predict_finish(world, project, tool, plan, delay)
    art.meters["progress"] += tool.power + plan.power
    art.meters["deadline"] = float(project.demand + delay)
    if pred["level"] == "grand":
        art.meters["finished"] += 1
        art.meters["huge"] += 1
        art.meters["smudged"] = 0.0
        propagate(world, narrate=False)
        world.say(plan.success_text.format(a=a.id, b=b.id, tool=tool.label, project=project.label))
        world.say(
            f"When they stepped back, {project.ending}."
        )
    elif pred["level"] == "just_in_time":
        art.meters["finished"] += 1
        art.meters["smudged"] = 0.0
        art.meters["close_call"] += 1
        propagate(world, narrate=False)
        world.say(plan.close_call_text.format(a=a.id, b=b.id, tool=tool.label, project=project.label))
        world.say(
            f"They finished on the very last useful heartbeat, and {project.ending.lower()}."
        )
    else:
        art.meters["unfinished"] += 1
        art.meters["smudged"] += 1
        propagate(world, narrate=False)
        world.say(plan.fail_text.format(a=a.id, b=b.id, tool=tool.label, project=project.label))
        world.say(
            f"They had solved the grabbing part, but not the clock, and the giant work stood there with one brave side still waiting."
        )
    world.say(
        f'{helper.label_word.capitalize()} smiled. "That is how a problem shrinks," {helper.pronoun()} said, '
        f'"when people stop tugging and start thinking together."'
    )
    return pred["level"]


def ending_gift(world: World, a: Entity, b: Entity, tool: Tool, project: Project, outcome: str) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
    if outcome == "unfinished":
        world.say(
            f"Afterward, {a.id} held one end of the {tool.label} and {b.id} held the other, this time gently. "
            f"They promised that the next giant fiction project would begin with a plan instead of a tug."
        )
    else:
        world.say(
            f"After that, whenever {a.id} and {b.id} saw one tool and two bright ideas, they split the work before the quarrel could grow whiskers. "
            f"The next tall tale they made began with sharing, and somehow it looked even bigger."
        )


def tell(setting: Setting, project: Project, tool: Tool, plan: Plan,
         starter_name: str = "Mara", starter_gender: str = "girl",
         partner_name: str = "Owen", partner_gender: str = "boy",
         helper_type: str = "teacher", delay: int = 0) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=starter_name,
        kind="character",
        type=starter_gender,
        role="starter",
        traits=["bold"],
        attrs={},
    ))
    b = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["quick"],
        attrs={},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        attrs={},
    ))
    world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        usable_on=set(tool.surfaces),
        tags=set(tool.tags),
        attrs={},
    ))
    world.add(Entity(
        id="art",
        kind="thing",
        type="project",
        label=project.label,
        surface=setting.surface,
        tags=set(project.tags),
        attrs={},
    ))

    world.facts["setting"] = setting
    world.facts["project"] = project
    world.facts["tool_cfg"] = tool
    world.facts["plan_cfg"] = plan
    world.facts["delay"] = delay
    world.facts["starter"] = a
    world.facts["partner"] = b
    world.facts["helper"] = helper

    introduce(world, a, b, setting, project)
    world.para()
    spot_one_tool(world, a, b, tool)
    tug(world, a, b, tool, project)
    helper_warn(world, helper, a, b, project, tool, plan, delay)
    world.para()
    outcome = solve(world, a, b, helper, project, tool, plan, delay)
    world.para()
    ending_gift(world, a, b, tool, project, outcome)

    art = world.get("art")
    world.facts.update(
        outcome=outcome,
        finished=art.meters["finished"] >= THRESHOLD,
        smudged=art.meters["smudged"] >= THRESHOLD,
        progress=art.meters["progress"],
        deadline=art.meters["deadline"],
    )
    return world


SETTINGS = {
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard",
        surface="sidewalk",
        opener="The long sidewalk lay in the sun like a gray river waiting for a story to swim across it.",
        sky="the clouds looked piled as high as haystacks",
        supports={"river_map"},
        tags={"sidewalk"},
    ),
    "porch": Setting(
        id="porch",
        place="the library porch",
        surface="paper_roll",
        opener="A roll of paper was clipped across two crates, stretching so wide it looked ready to catch a whole afternoon.",
        sky="the town breeze kept trying to peek over every shoulder",
        supports={"cloud_whale", "moonfish_banner"},
        tags={"paper"},
    ),
    "barn": Setting(
        id="barn",
        place="the red barn wall at fair time",
        surface="cloth_banner",
        opener="A clean banner hung on the barn wall, flapping like it already knew it was about to become famous.",
        sky="the weather vane pointed so proudly it might have been showing off",
        supports={"cloud_whale", "moonfish_banner"},
        tags={"cloth"},
    ),
}

PROJECTS = {
    "river_map": Project(
        id="river_map",
        label="the giant river map",
        phrase="a giant river map about a catfish so wide it could shade three wagons",
        demand=4,
        surfaces={"sidewalk", "paper_roll"},
        boast="somebody said even the sparrows might need directions to cross it",
        ending="the catfish on the map looked ready to gulp the whole schoolyard in one polite sip",
        tags={"map", "fiction"},
    ),
    "cloud_whale": Project(
        id="cloud_whale",
        label="the cloud-whale poster",
        phrase="a cloud-whale poster about a beast that sneezed weather from one end of the county to the other",
        demand=3,
        surfaces={"paper_roll", "cloth_banner"},
        boast="it seemed likely to need its own gust of wind just to turn around",
        ending="the cloud-whale billowed across the page so grandly that even the breeze slowed down to stare",
        tags={"poster", "fiction"},
    ),
    "moonfish_banner": Project(
        id="moonfish_banner",
        label="the moonfish banner",
        phrase="a moonfish banner about a silver fish that could leap over the moon and still have room for a tail wiggle",
        demand=5,
        surfaces={"paper_roll", "cloth_banner"},
        boast="the story was so oversized it sounded borrowed from a trumpet",
        ending="the moonfish stretched from end to end as if the night sky had loaned them one shining secret",
        tags={"banner", "fiction"},
    ),
}

TOOLS = {
    "chalkbeam": Tool(
        id="chalkbeam",
        label="chalkbeam",
        phrase="a stick of sidewalk chalk as long as a loaf of bread",
        marks="wide pale rivers of color",
        power=3,
        stroke="broad",
        squeak="Skrreee!",
        surfaces={"sidewalk"},
        tags={"chalk"},
    ),
    "feather_brush": Tool(
        id="feather_brush",
        label="feather brush",
        phrase="a feather brush with a handle nearly as long as a fishing pole",
        marks="swishing blue and gold curves",
        power=2,
        stroke="curvy",
        squeak="Swish-flop!",
        surfaces={"paper_roll", "cloth_banner"},
        tags={"brush"},
    ),
    "paint_roller": Tool(
        id="paint_roller",
        label="paint roller",
        phrase="a paint roller that looked fit to whitewash a cloud",
        marks="thunder-wide bands of color",
        power=3,
        stroke="wide",
        squeak="Whuff-whuff!",
        surfaces={"paper_roll", "cloth_banner"},
        tags={"paint"},
    ),
}

PLANS = {
    "take_turns": Plan(
        id="take_turns",
        label="take turns",
        sense=3,
        power=2,
        method="to let one child make the title while the other counted to ten, then swap jobs",
        success_text="{a} made the roaring title first, then {b} took the {tool} for the bold middle, and back and forth they went until {project} filled out neatly.",
        close_call_text="{a} and {b} traded the {tool} so quickly and carefully that every turn mattered. The waiting felt long, but each pass added just enough.",
        fail_text="{a} and {b} took turns with the {tool}, which stopped the grabbing at once, but the giant work still asked for more time than they had.",
        qa_text="They solved it by taking turns with one big tool instead of grabbing at the same time.",
        tags={"sharing"},
    ),
    "outline_fill": Plan(
        id="outline_fill",
        label="outline and fill",
        sense=4,
        power=3,
        method="to have one child draw the big outline while the other filled every open space the moment it appeared",
        success_text="{a} sketched the grand edges while {b} rushed in behind with the rich parts, and the two jobs fitted together like gears in a story clock.",
        close_call_text="{a} handled the outline and {b} filled every waiting patch, and the work clicked along so tightly there was barely a blink to spare.",
        fail_text="{a} drew the outline while {b} filled behind, and it was a smart plan, but this giant piece was bigger than one short fair minute.",
        qa_text="They split the work into two jobs, so one child outlined and the other filled the spaces. Sharing the task made the single tool useful instead of troublesome.",
        tags={"sharing", "problem_solving"},
    ),
    "story_panels": Plan(
        id="story_panels",
        label="story panels",
        sense=3,
        power=4,
        method="to fold the work into story panels and pass the tool at each line like runners passing a baton",
        success_text="They broke the picture into panels, passed the {tool} at every border, and built {project} one brave piece at a time until the whole thing stood grinning.",
        close_call_text="They turned the work into panels and passed the {tool} at each border. It was a close shave, but the last panel landed just before the bell.",
        fail_text="They divided the work into panels and passed the {tool} sensibly, but the banner was still too hungry for time and color to finish that day.",
        qa_text="They divided the giant picture into smaller panels and shared the tool at each border. Breaking the problem into parts helped them work faster together.",
        tags={"sharing", "problem_solving"},
    ),
    "tug_together": Plan(
        id="tug_together",
        label="both hold it at once",
        sense=1,
        power=1,
        method="to keep holding the tool together and simply hope for the best",
        success_text="{a} and {b} somehow wrestled the {tool} into place.",
        close_call_text="{a} and {b} somehow finished by luck.",
        fail_text="{a} and {b} kept both hands on the {tool}, and the marks wandered everywhere.",
        qa_text="They did not really solve the sharing problem.",
        tags={"grabbing"},
    ),
}

GIRL_NAMES = ["Mara", "Lila", "June", "Nell", "Tess", "Ada", "Molly", "Pearl"]
BOY_NAMES = ["Owen", "Beau", "Finn", "Jude", "Silas", "Eli", "Theo", "Wes"]


@dataclass
class StoryParams:
    setting: str
    project: str
    tool: str
    plan: str
    starter_name: str
    starter_gender: str
    partner_name: str
    partner_gender: str
    helper: str
    delay: int = 0
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
    "fiction": [
        (
            "What is fiction?",
            "Fiction is a made-up story. It can use pretend creatures and impossible things even when the people telling it are using real paper, chalk, or paint."
        )
    ],
    "sharing": [
        (
            "Why is sharing one tool helpful?",
            "Sharing keeps two people from blocking each other. When they take turns or split jobs, the tool can keep moving instead of getting stuck in a tug."
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means noticing what is going wrong and making a plan that fits the real problem. A good plan changes the situation instead of only wishing it away."
        )
    ],
    "chalk": [
        (
            "What is sidewalk chalk for?",
            "Sidewalk chalk is for drawing on pavement. It makes bright marks on stone, but it is not the right tool for cloth or paper banners."
        )
    ],
    "brush": [
        (
            "What does a paint brush do?",
            "A paint brush spreads paint in lines and curves. It works well on paper or cloth because those surfaces can hold the paint."
        )
    ],
    "paint": [
        (
            "What is a paint roller used for?",
            "A paint roller covers a wide area quickly. That makes it handy for big paper or cloth work when a project is very large."
        )
    ],
    "map": [
        (
            "What is a map?",
            "A map is a picture that shows where things are. In a tall tale, a map can also show a made-up place or creature from a pretend story."
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long piece of cloth or paper with words or pictures on it. People hang it up so everyone can see it from far away."
        )
    ],
    "poster": [
        (
            "What is a poster?",
            "A poster is a big sheet with words or pictures meant to be looked at. It is made to catch people's eyes quickly."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["starter"]
    b = f["partner"]
    setting = f["setting"]
    project = f["project"]
    tool = f["tool_cfg"]
    outcome = f["outcome"]
    if outcome == "unfinished":
        return [
            f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "fiction" and is about sharing one {tool.label}.',
            f"Tell a story where {a.id} and {b.id} try to make {project.label} in {setting.place}, first pull over one tool, and then solve the problem wisely even though they run short on time.",
            f"Write a child-friendly story about sharing and problem solving where the children fix the quarrel before the grown-up lesson at the end."
        ]
    return [
        f'Write a tall-tale style story for a 3-to-5-year-old that includes the word "fiction" and is about children sharing one giant art tool.',
        f"Tell a story where {a.id} and {b.id} want to make {project.label} in {setting.place}, start by tugging over one {tool.label}, and then solve the problem by sharing cleverly.",
        f"Write a simple tall tale with a huge pretend picture, one shared tool, a calm helper, and a happy ending that proves the children changed."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["starter"]
    b = f["partner"]
    helper = f["helper"]
    setting = f["setting"]
    project = f["project"]
    tool = f["tool_cfg"]
    plan = f["plan_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children making a giant piece of fiction in {setting.place}. A calm {helper.label_word} helps when the sharing problem starts."
        ),
        (
            "What problem did the children have?",
            f"They both wanted the same {tool.label} at the same time. Because they grabbed together, the line wobbled and the big picture started to go wrong."
        ),
        (
            f"Why did the first line go crooked?",
            f"It went crooked because {a.id} and {b.id} tugged on one tool at once. The pulling made the mark wobble instead of going where either child meant it to go."
        ),
        (
            f"How did the {helper.label_word} help?",
            f"The {helper.label_word} showed them {plan.label}. {plan.qa_text} That fixed the real problem, which was sharing, not imagination."
        ),
    ]
    if outcome == "grand":
        qa.append(
            (
                "How did the story end?",
                f"It ended with the giant picture finished in a grand way. Sharing turned one troublesome tool into enough help for both children, so their huge idea finally fit on the page."
            )
        )
    elif outcome == "just_in_time":
        qa.append(
            (
                "Did their plan work right away?",
                f"Yes, but only just in time. Their plan was good enough to finish before the bell, which shows that solving the problem helped even when time was tight."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the picture finished at the last moment. The children still won a good ending because they shared instead of fighting."
            )
        )
    else:
        qa.append(
            (
                "Did they solve the problem even though the picture was not finished?",
                f"Yes. They stopped the grabbing and learned how to share the tool fairly. The banner stayed unfinished because there was not enough time left, but the children had changed for the better."
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a big problem gets smaller when they think together. Sharing early would have saved time as well as hurt feelings."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    project = f["project"]
    tool = f["tool_cfg"]
    plan = f["plan_cfg"]
    tags = {"fiction"}
    if "sharing" in plan.tags:
        tags.add("sharing")
    if "problem_solving" in plan.tags:
        tags.add("problem_solving")
    tags |= set(tool.tags) | set(project.tags)
    out: list[tuple[str, str]] = []
    order = ["fiction", "sharing", "problem_solving", "chalk", "brush", "paint", "map", "banner", "poster"]
    for tag in order:
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
        if ent.surface:
            bits.append(f"surface={ent.surface}")
        if ent.usable_on:
            bits.append(f"usable_on={sorted(ent.usable_on)}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, project: Project, tool: Tool) -> str:
    if not project_supported(setting, project):
        return (
            f"(No story: {project.label} does not fit {setting.place}. That place offers a {setting.surface} surface, "
            f"but this project belongs on one of {sorted(project.surfaces)}.)"
        )
    if not tool_fits(setting, tool):
        return (
            f"(No story: {tool.label} does not work on {setting.surface}. Pick a tool that can mark that surface.)"
        )
    return "(No story: that combination is not supported in this world.)"


def explain_plan(plan_id: str) -> str:
    plan = PLANS[plan_id]
    good = ", ".join(sorted(p.id for p in sensible_plans()))
    return (
        f"(Refusing plan '{plan_id}': it scores too low on common sense "
        f"(sense={plan.sense} < {SENSE_MIN}). Try a real sharing plan like: {good}.)"
    )


ASP_RULES = r"""
supported(S,P) :- setting(S), project(P), setting_surface(S,Surf), project_surface(P,Surf), offers(S,P).
fits(S,T)      :- setting(S), tool(T), setting_surface(S,Surf), tool_surface(T,Surf).
sensible(Pl)   :- plan(Pl), sense(Pl,S), sense_min(M), S >= M.
valid(S,P,T)   :- supported(S,P), fits(S,T).

score(Tool,Plan,TP + PP) :- chosen_tool(Tool), chosen_plan(Plan), tool_power(Tool,TP), plan_power(Plan,PP).
need(Project,D + Delay)  :- chosen_project(Project), demand(Project,D), delay(Delay).

outcome(grand)        :- score(T,Pts), need(P,N), Pts > N.
outcome(just_in_time) :- score(T,Pts), need(P,N), Pts = N.
outcome(unfinished)   :- score(T,Pts), need(P,N), Pts < N.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("setting_surface", setting_id, setting.surface))
        for project_id in sorted(setting.supports):
            lines.append(asp.fact("offers", setting_id, project_id))
    for project_id, project in PROJECTS.items():
        lines.append(asp.fact("project", project_id))
        lines.append(asp.fact("demand", project_id, project.demand))
        for surface in sorted(project.surfaces):
            lines.append(asp.fact("project_surface", project_id, surface))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_power", tool_id, tool.power))
        for surface in sorted(tool.surfaces):
            lines.append(asp.fact("tool_surface", tool_id, surface))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
        lines.append(asp.fact("plan_power", plan_id, plan.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_plans() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(p for (p,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_project", params.project),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_plan", params.plan),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="schoolyard",
        project="river_map",
        tool="chalkbeam",
        plan="outline_fill",
        starter_name="Mara",
        starter_gender="girl",
        partner_name="Owen",
        partner_gender="boy",
        helper="teacher",
        delay=0,
    ),
    StoryParams(
        setting="porch",
        project="cloud_whale",
        tool="feather_brush",
        plan="take_turns",
        starter_name="Lila",
        starter_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        helper="librarian",
        delay=1,
    ),
    StoryParams(
        setting="barn",
        project="moonfish_banner",
        tool="paint_roller",
        plan="story_panels",
        starter_name="Pearl",
        starter_gender="girl",
        partner_name="Beau",
        partner_gender="boy",
        helper="aunt",
        delay=0,
    ),
    StoryParams(
        setting="porch",
        project="moonfish_banner",
        tool="feather_brush",
        plan="take_turns",
        starter_name="June",
        starter_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        helper="teacher",
        delay=2,
    ),
    StoryParams(
        setting="barn",
        project="cloud_whale",
        tool="feather_brush",
        plan="outline_fill",
        starter_name="Ada",
        starter_gender="girl",
        partner_name="Wes",
        partner_gender="boy",
        helper="librarian",
        delay=1,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: two children, one giant tool, and a sharing plan."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--helper", choices=["teacher", "librarian", "aunt", "mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra time pressure before the bell")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.project and args.tool:
        setting = SETTINGS[args.setting]
        project = PROJECTS[args.project]
        tool = TOOLS[args.tool]
        if not (project_supported(setting, project) and tool_fits(setting, tool)):
            raise StoryError(explain_rejection(setting, project, tool))
    if args.plan and PLANS[args.plan].sense < SENSE_MIN:
        raise StoryError(explain_plan(args.plan))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, project_id, tool_id = rng.choice(sorted(combos))
    plan_id = args.plan or rng.choice(sorted(plan.id for plan in sensible_plans()))
    starter_name, starter_gender = _pick_name(rng)
    partner_name, partner_gender = _pick_name(rng, avoid=starter_name)
    helper = args.helper or rng.choice(["teacher", "librarian", "aunt", "mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        project=project_id,
        tool=tool_id,
        plan=plan_id,
        starter_name=starter_name,
        starter_gender=starter_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        helper=helper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    setting = SETTINGS[params.setting]
    project = PROJECTS[params.project]
    tool = TOOLS[params.tool]
    plan = PLANS[params.plan]

    if not project_supported(setting, project) or not tool_fits(setting, tool):
        raise StoryError(explain_rejection(setting, project, tool))
    if plan.sense < SENSE_MIN:
        raise StoryError(explain_plan(params.plan))

    world = tell(
        setting=setting,
        project=project,
        tool=tool,
        plan=plan,
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        helper_type=params.helper,
        delay=params.delay,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: gate matches valid_combos() ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {p.id for p in sensible_plans()}
    clingo_sensible = set(asp_sensible_plans())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible plans match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible plans:")
        print("  python:", sorted(python_sensible))
        print("  clingo:", sorted(clingo_sensible))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_level(PROJECTS[params.project], TOOLS[params.tool], PLANS[params.plan], params.delay)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
            print(f"MISMATCH outcome for {params}: python={py} clingo={cl}")
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(123)))
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path
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
        print(f"sensible plans: {', '.join(asp_sensible_plans())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, project, tool) combos:\n")
        for setting, project, tool in combos:
            print(f"  {setting:10} {project:16} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            outcome = outcome_level(PROJECTS[p.project], TOOLS[p.tool], PLANS[p.plan], p.delay)
            header = f"### {p.starter_name} & {p.partner_name}: {p.project} at {p.setting} ({p.tool}, {p.plan}, {outcome})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
