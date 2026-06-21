#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py
==================================================================================

A standalone story world for a tiny adventure about friendship and problem
solving: two friends build a pretend expedition camp, a small treasure token
rolls into a place a hand should not go, and they solve the problem together
with a safe homemade tool.

This world is intentionally small and constraint-driven. It always includes the
words "whisk" and "minimal", but the story text is state-driven: a child may
grab, a friend may warn, a grown-up may help, and the ending image proves what
changed about both the problem and the friendship.

Run it
------
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py --site drain --tool whisk --plan ask_parent
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py --site thorn_bush
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py --all
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/whisk_minimal_moral_value_friendship_problem_solving.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    reach: int = 0
    safe_for: set[str] = field(default_factory=set)
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Theme:
    id: str
    scene: str
    setup: str
    titles: tuple[str, str]
    goal: str
    ending: str
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
class Site:
    id: str
    label: str
    the: str
    danger_word: str
    need_reach: int
    safe_tools: set[str]
    rescue_text: str
    warning_text: str
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
class ToolCfg:
    id: str
    label: str
    phrase: str
    reach: int
    safe_for: set[str]
    building_text: str
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
    helper_needed: bool
    success_text: str
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
        return [e for e in self.entities.values() if e.role in {"leader", "friend"}]

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


def _r_stuck_worry(world: World) -> list[str]:
    token = world.get("token")
    if token.meters["stuck"] < THRESHOLD:
        return []
    sig = ("stuck_worry", "token")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__stuck__"]


def _r_risky_grab(world: World) -> list[str]:
    leader = world.get("leader")
    if leader.memes["grab_attempt"] < THRESHOLD:
        return []
    sig = ("risky_grab", leader.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    leader.meters["at_risk"] += 1
    friend = world.get("friend")
    friend.memes["care"] += 1
    return ["__risk__"]


def _r_rescue_relief(world: World) -> list[str]:
    token = world.get("token")
    if token.meters["rescued"] < THRESHOLD:
        return []
    sig = ("rescue_relief", "token")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
        kid.memes["teamwork"] += 1
        kid.memes["worry"] = 0.0
    return ["__relief__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck_worry", tag="emotion", apply=_r_stuck_worry),
    Rule(name="risky_grab", tag="safety", apply=_r_risky_grab),
    Rule(name="rescue_relief", tag="emotion", apply=_r_rescue_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend([s for s in produced if not s.startswith("__")])
    if narrate:
        for sent in out:
            world.say(sent)
    return out


def site_reachable(tool: ToolCfg, site: Site) -> bool:
    return tool.reach >= site.need_reach


def tool_safe(tool: ToolCfg, site: Site) -> bool:
    return site.id in tool.safe_for and tool.id in site.safe_tools


def plan_works(tool: ToolCfg, plan: Plan, site: Site) -> bool:
    return site_reachable(tool, site) and tool_safe(tool, site) and plan.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for site_id, site in SITES.items():
            for tool_id, tool in TOOLS.items():
                for plan_id, plan in PLANS.items():
                    if plan_works(tool, plan, site):
                        combos.append((theme_id, site_id, tool_id, plan_id))
    return combos


def predict_attempt(world: World, tool_id: str, site_id: str, plan_id: str) -> dict:
    sim = world.copy()
    tool = TOOLS[tool_id]
    site = SITES[site_id]
    plan = PLANS[plan_id]
    if not plan_works(tool, plan, site):
        sim.get("leader").memes["grab_attempt"] += 1
        propagate(sim, narrate=False)
    else:
        sim.get("token").meters["rescued"] += 1
        sim.get("token").meters["stuck"] = 0.0
        propagate(sim, narrate=False)
    return {
        "rescued": sim.get("token").meters["rescued"] >= THRESHOLD,
        "risk": sim.get("leader").meters["at_risk"],
        "worry": sim.get("leader").memes["worry"] + sim.get("friend").memes["worry"],
    }


def introduce(world: World, leader: Entity, friend: Entity, theme: Theme) -> None:
    a_title, b_title = theme.titles
    for kid in (leader, friend):
        kid.memes["joy"] += 1
        kid.memes["friendship"] += 1
    world.say(
        f"After breakfast, {leader.id} and {friend.id} turned the yard into {theme.scene}. "
        f"{theme.setup}"
    )
    world.say(
        f'"{a_title} {leader.id} and {b_title} {friend.id}!" {leader.id} called. '
        f'"Today we find {theme.goal}."'
    )


def find_token(world: World, leader: Entity, friend: Entity, site: Site) -> None:
    token = world.get("token")
    token.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They followed a chalk map until the shiny trail ended with their brass star token. "
        f"It had slipped into {site.the}."
    )
    world.say(
        f"{friend.id} crouched beside it. \"Oh no,\" {friend.pronoun()} whispered. "
        f"\"It's down by {site.danger_word}.\""
    )


def tempt_grab(world: World, leader: Entity, site: Site) -> None:
    leader.memes["impatience"] += 1
    world.say(
        f"{leader.id} leaned closer. \"I can get it fast,\" {leader.pronoun()} said, "
        f"reaching toward {site.the} with bare fingers."
    )


def warn_friend(world: World, leader: Entity, friend: Entity, site: Site,
                tool: ToolCfg, plan: Plan, parent: Entity) -> None:
    pred = predict_attempt(world, tool.id, site.id, plan.id)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_rescue"] = pred["rescued"]
    world.say(
        f'{friend.id} caught {leader.id}\'s sleeve. "{site.warning_text}," '
        f'{friend.pronoun()} said. "Let\'s do this the clever way and ask {parent.label_word} '
        f'for a minimal plan."'
    )


def risky_reach(world: World, leader: Entity, friend: Entity, site: Site) -> None:
    leader.memes["grab_attempt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{leader.id}'s hand stopped right at the edge of {site.the}. "
        f"The adventure suddenly felt real instead of pretend."
    )
    world.say(
        f"{friend.id} stepped beside {leader.pronoun('object')} instead of walking away. "
        f"That small act of friendship made {leader.id} pause."
    )


def fetch_tool(world: World, leader: Entity, friend: Entity, tool: ToolCfg, parent: Entity) -> None:
    world.say(
        f"Together they hurried to the porch table, where a box of odd supplies waited. "
        f"There was {tool.phrase} and only a few other things."
    )
    world.say(
        f'{parent.label_word.capitalize()} smiled when {friend.id} said they wanted a safe rescue '
        f'with a minimal kit. {tool.building_text}'
    )


def rescue(world: World, leader: Entity, friend: Entity, parent: Entity,
           tool: ToolCfg, site: Site, plan: Plan, theme: Theme) -> None:
    token = world.get("token")
    token.meters["rescued"] += 1
    token.meters["stuck"] = 0.0
    propagate(world, narrate=False)
    body = plan.success_text.format(tool=tool.label, site=site.label)
    world.say(
        f"{parent.label_word.capitalize()} stayed close while {leader.id} and {friend.id} {body}."
    )
    world.say(
        f"Soon the brass star clicked free, and {friend.id} caught it before it could whisk away "
        f"again."
    )
    world.say(
        f'"We solved it together," {leader.id} said. The brave part of the adventure was not the grab; '
        f"it was the thinking."
    )
    world.say(
        f"They tucked the star into their map pouch and {theme.ending}."
    )


def resolve_feelings(world: World, leader: Entity, friend: Entity) -> None:
    leader.memes["gratitude"] += 1
    friend.memes["pride"] += 1
    world.say(
        f'{leader.id} looked at {friend.id}. "Thanks for stopping me," {leader.pronoun()} said. '
        f'"Good partners help each other make safe choices."'
    )
    world.say(
        f'{friend.id} grinned and bumped shoulders with {leader.pronoun("object")}. '
        f'"That is what friends are for," {friend.pronoun()} said.'
    )


def tell(theme: Theme, site: Site, tool: ToolCfg, plan: Plan,
         leader_name: str = "Nia", leader_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         parent_type: str = "mother", trait: str = "steady") -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["bold", trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["careful", "kind"],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(
        id="token",
        type="treasure",
        label="brass star token",
        phrase="a little brass star token",
    ))
    world.facts["theme"] = theme
    world.facts["site_cfg"] = site
    world.facts["tool_cfg"] = tool
    world.facts["plan_cfg"] = plan
    world.facts["leader"] = leader
    world.facts["friend"] = friend
    world.facts["parent"] = parent

    introduce(world, leader, friend, theme)
    world.para()
    find_token(world, leader, friend, site)
    tempt_grab(world, leader, site)
    warn_friend(world, leader, friend, site, tool, plan, parent)
    risky_reach(world, leader, friend, site)
    world.para()
    fetch_tool(world, leader, friend, tool, parent)
    rescue(world, leader, friend, parent, tool, site, plan, theme)
    resolve_feelings(world, leader, friend)

    world.facts.update(
        token=world.get("token"),
        solved=world.get("token").meters["rescued"] >= THRESHOLD,
        friendship_help=friend.memes["care"] >= THRESHOLD,
        risky_start=leader.meters["at_risk"] >= THRESHOLD,
        learned=leader.memes["gratitude"] >= THRESHOLD,
    )
    return world


THEMES = {
    "expedition": Theme(
        id="expedition",
        scene="a hidden expedition camp",
        setup="A blanket over two chairs became their cliff tent, a jump rope marked the river, and a cardboard box was the mountain supply crate.",
        titles=("Captain", "Scout"),
        goal="the lost star of the map",
        ending="set off for the next checkpoint with steadier feet",
        tags={"adventure", "friendship"},
    ),
    "jungle": Theme(
        id="jungle",
        scene="a whispery jungle base",
        setup="A fern patch became the jungle edge, a garden path turned into a canyon trail, and their paper map showed where the old star should be.",
        titles=("Explorer", "Guide"),
        goal="the hidden star key",
        ending="marched on through the make-believe jungle with smiles as bright as lanterns",
        tags={"adventure", "teamwork"},
    ),
}

SITES = {
    "drain": Site(
        id="drain",
        label="drain",
        the="the drain grate",
        danger_word="the dark little bars",
        need_reach=2,
        safe_tools={"whisk", "magnet_pole"},
        rescue_text="lifted the token out from between the bars",
        warning_text="Your hand could get pinched there",
        tags={"drain", "safety"},
    ),
    "fence_gap": Site(
        id="fence_gap",
        label="fence gap",
        the="the fence gap",
        danger_word="the splintery boards",
        need_reach=3,
        safe_tools={"whisk", "grabber"},
        rescue_text="hooked the token and slid it back through the gap",
        warning_text="Those boards are rough and full of splinters",
        tags={"fence", "safety"},
    ),
    "thorn_bush": Site(
        id="thorn_bush",
        label="thorn bush",
        the="the thorn bush",
        danger_word="the sharp little thorns",
        need_reach=3,
        safe_tools={"grabber"},
        rescue_text="pinched the token gently and lifted it out of the branches",
        warning_text="Those thorns are sharp enough to scratch hard",
        tags={"thorns", "safety"},
    ),
}

TOOLS = {
    "whisk": ToolCfg(
        id="whisk",
        label="whisk",
        phrase="a kitchen whisk with a long handle",
        reach=3,
        safe_for={"drain", "fence_gap"},
        building_text="They tied a ribbon around the handle of the whisk so it would not slip, and the looped wires made a gentle little catcher.",
        tags={"whisk", "tool"},
    ),
    "grabber": ToolCfg(
        id="grabber",
        label="grabber",
        phrase="a toy grabber from the dress-up box",
        reach=3,
        safe_for={"fence_gap", "thorn_bush"},
        building_text="They tested the grabber on a leaf first, and when it closed softly, they nodded like real adventurers.",
        tags={"grabber", "tool"},
    ),
    "magnet_pole": ToolCfg(
        id="magnet_pole",
        label="magnet pole",
        phrase="a stick with a little magnet taped to the end",
        reach=2,
        safe_for={"drain"},
        building_text="They wound tape neatly around the stick and checked that the tiny magnet did not wobble.",
        tags={"magnet", "tool"},
    ),
}

PLANS = {
    "ask_parent": Plan(
        id="ask_parent",
        label="ask a parent and build together",
        sense=3,
        helper_needed=True,
        success_text="worked side by side, using the {tool} to reach into the {site}",
        fail_text="asked for help, but the tool they chose could not safely reach the token",
        qa_text="They asked a grown-up for help and used the tool together.",
        tags={"ask_help", "problem_solving"},
    ),
    "teamwork_only": Plan(
        id="teamwork_only",
        label="make a careful plan together",
        sense=2,
        helper_needed=False,
        success_text="counted to three, held steady, and used the {tool} to reach into the {site}",
        fail_text="made a plan together, but the tool still was not safe for that spot",
        qa_text="They slowed down, made a careful plan, and solved the problem together.",
        tags={"teamwork", "problem_solving"},
    ),
    "grab_fast": Plan(
        id="grab_fast",
        label="grab fast with a bare hand",
        sense=1,
        helper_needed=False,
        success_text="should not appear",
        fail_text="tried to snatch it fast with bare fingers",
        qa_text="They tried to grab too fast.",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Lila", "Tara", "Ivy", "Zoe", "Ava", "Nora"]
BOY_NAMES = ["Ben", "Theo", "Max", "Eli", "Finn", "Sam", "Leo", "Noah"]
TRAITS = ["steady", "brave", "thoughtful", "patient", "curious"]


@dataclass
class StoryParams:
    theme: str
    site: str
    tool: str
    plan: str
    leader_name: str
    leader_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    trait: str
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
    "whisk": [(
        "What is a whisk?",
        "A whisk is a kitchen tool with looped wires for stirring and mixing. If a grown-up says yes, it can also be used carefully for a simple homemade tool."
    )],
    "drain": [(
        "Why should you not put your fingers into a drain grate?",
        "A drain grate has hard edges and narrow spaces that can pinch or scrape your hand. It is safer to ask a grown-up and use a tool instead."
    )],
    "fence": [(
        "Why can a fence gap be unsafe for fingers?",
        "A fence gap can hide rough wood and splinters. Reaching into it can hurt your hand."
    )],
    "thorns": [(
        "Why are thorn bushes dangerous to touch?",
        "Thorns are sharp and can scratch or poke your skin. That is why people use care and tools around thorny plants."
    )],
    "ask_help": [(
        "Why is asking for help a smart choice?",
        "Asking for help gives you another brain and often a safer plan. Good problem solving means noticing when you should not do a risky thing alone."
    )],
    "teamwork": [(
        "How does teamwork help solve a problem?",
        "Teamwork lets two people share ideas and help each other stay calm. One friend can notice a danger while the other thinks of a solution."
    )],
    "problem_solving": [(
        "What does problem solving mean?",
        "Problem solving means stopping to think about what is wrong and trying a safe plan to fix it. It is not just doing the fastest thing."
    )],
    "friendship": [(
        "What does a good friend do in a tricky moment?",
        "A good friend tells the truth kindly and helps keep people safe. Friendship is not only playing together, but also making good choices together."
    )],
    "magnet": [(
        "What can a magnet do?",
        "A magnet can pull some metal objects toward it. That can help lift a tiny metal thing without using your fingers."
    )],
    "grabber": [(
        "What is a grabber tool for?",
        "A grabber helps you pick something up from a place that is hard to reach. It gives your hand extra distance."
    )],
}
KNOWLEDGE_ORDER = [
    "friendship", "problem_solving", "ask_help", "teamwork",
    "whisk", "drain", "fence", "thorns", "magnet", "grabber",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    site = f["site_cfg"]
    tool = f["tool_cfg"]
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "whisk" and "minimal" and teaches friendship through problem solving.',
        f"Tell an adventure where {leader.id} and {friend.id} lose a treasure token in {site.the}, and a friend stops a risky grab so they can solve the problem together.",
        f"Write a gentle story where children use a minimal kit and a {tool.label} to solve a tricky problem safely, showing that good friends help each other think.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    friend = f["friend"]
    parent = f["parent"]
    site = f["site_cfg"]
    tool = f["tool_cfg"]
    plan = f["plan_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {leader.id} and {friend.id}, on a pretend adventure. {parent.label_word.capitalize()} stays nearby when they need help."
        ),
        (
            "What problem did they face?",
            f"Their brass star token slipped into {site.the}, where bare fingers were not safe. That changed the game from simple play into a real problem to solve."
        ),
        (
            f"Why did {friend.id} stop {leader.id} from grabbing right away?",
            f"{friend.id} saw that {site.warning_text.lower()}. So {friend.pronoun()} asked for a safer plan instead of letting the adventure become an accident."
        ),
        (
            "What did they use to solve the problem?",
            f"They used a {tool.label} as part of a minimal rescue kit. The tool gave them safe reach, and the plan worked because they slowed down and thought first."
        ),
        (
            "How did friendship help in the story?",
            f"Friendship helped because {friend.id} did not laugh or walk away when the problem appeared. {friend.pronoun().capitalize()} stayed close, warned kindly, and helped turn a risky moment into a team solution."
        ),
    ]
    if f.get("solved"):
        qa.append((
            "How did the story end?",
            f"They got the brass star back and kept going on their adventure. The ending shows they had learned that being brave can mean asking for help and solving problems together."
        ))
        qa.append((
            f"What did {leader.id} learn?",
            f"{leader.id} learned that grabbing fast is not always the brave choice. {leader.pronoun().capitalize()} thanked {friend.id} because a good partner helps with both safety and thinking."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"friendship", "problem_solving"}
    site = world.facts["site_cfg"]
    tool = world.facts["tool_cfg"]
    plan = world.facts["plan_cfg"]
    tags |= set(site.tags) | set(tool.tags) | set(plan.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.reach:
            bits.append(f"reach={ent.reach}")
        if ent.safe_for:
            bits.append(f"safe_for={sorted(ent.safe_for)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="expedition",
        site="drain",
        tool="whisk",
        plan="ask_parent",
        leader_name="Nia",
        leader_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        theme="jungle",
        site="fence_gap",
        tool="whisk",
        plan="teamwork_only",
        leader_name="Theo",
        leader_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        parent="father",
        trait="patient",
    ),
    StoryParams(
        theme="expedition",
        site="thorn_bush",
        tool="grabber",
        plan="ask_parent",
        leader_name="Lila",
        leader_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        theme="jungle",
        site="drain",
        tool="magnet_pole",
        plan="teamwork_only",
        leader_name="Finn",
        leader_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        parent="father",
        trait="curious",
    ),
]


def explain_rejection(site: Site, tool: ToolCfg, plan: Plan) -> str:
    if plan.sense < SENSE_MIN:
        return (
            f"(No story: the plan '{plan.id}' is too reckless for this world. "
            f"The adventure should reward friendship and problem solving, not a bare-handed snatch.)"
        )
    if not site_reachable(tool, site):
        return (
            f"(No story: {tool.label} is not long enough for {site.the}. "
            f"The rescue tool must truly reach the stuck object.)"
        )
    if not tool_safe(tool, site):
        return (
            f"(No story: {tool.label} is not a safe fit for {site.the}. "
            f"Pick a tool that can reach without scraping fingers or tangling in the wrong place.)"
        )
    return "(No story: this combination does not make a reasonable rescue.)"


ASP_RULES = r"""
safe_tool_for_site(Tool, Site) :- tool(Tool), site(Site), tool_safe(Tool, Site), site_accepts(Site, Tool).
reaches(Tool, Site) :- tool(Tool), site(Site), tool_reach(Tool, R), site_need(Site, N), R >= N.
good_plan(P) :- plan(P), sense(P, S), sense_min(M), S >= M.

valid(Theme, Site, Tool, Plan) :-
    theme(Theme), site(Site), tool(Tool), plan(Plan),
    safe_tool_for_site(Tool, Site),
    reaches(Tool, Site),
    good_plan(Plan).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        lines.append(asp.fact("site_need", site_id, site.need_reach))
        for tool_id in sorted(site.safe_tools):
            lines.append(asp.fact("site_accepts", site_id, tool_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_reach", tool_id, tool.reach))
        for site_id in sorted(tool.safe_for):
            lines.append(asp.fact("tool_safe", tool_id, site_id))
    for plan_id, plan in PLANS.items():
        lines.append(asp.fact("plan", plan_id))
        lines.append(asp.fact("sense", plan_id, plan.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        rng = random.Random(123)
        params = resolve_params(build_parser().parse_args([]), rng)
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("Random generated story was empty.")
        print("OK: random seeded generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny adventure about friendship, safe choices, and problem solving."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
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
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.tool and args.plan:
        site = SITES[args.site]
        tool = TOOLS[args.tool]
        plan = PLANS[args.plan]
        if not plan_works(tool, plan, site):
            raise StoryError(explain_rejection(site, tool, plan))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.site is None or combo[1] == args.site)
        and (args.tool is None or combo[2] == args.tool)
        and (args.plan is None or combo[3] == args.plan)
    ]
    if not combos:
        if args.site and args.tool and args.plan:
            raise StoryError(explain_rejection(SITES[args.site], TOOLS[args.tool], PLANS[args.plan]))
        raise StoryError("(No valid combination matches the given options.)")

    theme, site, tool, plan = rng.choice(sorted(combos))
    leader_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=leader_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        theme=theme,
        site=site,
        tool=tool,
        plan=plan,
        leader_name=leader_name,
        leader_gender=leader_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")

    site = SITES[params.site]
    tool = TOOLS[params.tool]
    plan = PLANS[params.plan]
    if not plan_works(tool, plan, site):
        raise StoryError(explain_rejection(site, tool, plan))

    world = tell(
        theme=THEMES[params.theme],
        site=site,
        tool=tool,
        plan=plan,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (theme, site, tool, plan) combos:\n")
        for theme, site, tool, plan in combos:
            print(f"  {theme:10} {site:11} {tool:11} {plan}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader_name} & {p.friend_name}: {p.site} with {p.tool} ({p.plan})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
