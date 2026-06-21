#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nosh_compliant_friendship_conflict_problem_solving_tall.py
======================================================================================

A standalone storyworld for a tall-tale flavored friendship story:
two friends prepare an enormous snack, quarrel over how to solve a practical
problem, then work together and end with a bigger, kinder feast.

The seed asks for:
- the words "nosh" and "compliant"
- features of Friendship, Conflict, and Problem Solving
- a style close to a Tall Tale

This world models those as live state:
- a shared snack project grows too grand for one simple tool,
- one friend pushes a boastful shortcut,
- the other offers a steadier plan,
- the plan either succeeds cleanly or, in one cautionary branch, they waste time
  on the boast first and must recover together.

The prose is always driven by simulated state: heaviness, wobble, stuckness,
hunger, pride, trust, upset, relief, and cooperation.
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
    boast: str
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
class Snack:
    id: str
    label: str
    phrase: str
    cargo: str
    smell: str
    serving: str
    share_line: str
    magnitude: int
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
class Problem:
    id: str
    label: str
    cause: str
    fix_need: str
    severity: int
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
    capacity: int
    sense: int
    team: bool
    carry_text: str
    solve_text: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    problem = world.get("problem")
    if cart.meters["load"] >= THRESHOLD and problem.meters["stuck"] >= THRESHOLD:
        sig = ("wobble",)
        if sig not in world.fired:
            world.fired.add(sig)
            cart.meters["wobble"] += 1
            for kid_id in ("lead", "friend"):
                world.get(kid_id).memes["worry"] += 1
            out.append("__wobble__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    friend = world.get("friend")
    if lead.memes["boast"] >= THRESHOLD and world.facts.get("warning_given"):
        sig = ("conflict",)
        if sig not in world.fired:
            world.fired.add(sig)
            lead.memes["stubborn"] += 1
            friend.memes["upset"] += 1
            out.append("__conflict__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamed_up") and world.get("problem").meters["solved"] >= THRESHOLD:
        sig = ("teamwork",)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid_id in ("lead", "friend"):
                world.get(kid_id).memes["relief"] += 1
                world.get(kid_id).memes["friendship"] += 1
            out.append("__teamwork__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
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


def valid_combo(problem: Problem, tool: Tool) -> bool:
    return tool.capacity >= problem.severity and tool.sense >= SENSE_MIN


def best_tools(problem: Problem) -> list[str]:
    return sorted(tid for tid, t in TOOLS.items() if valid_combo(problem, t))


def predict_attempt(problem: Problem, tool: Tool) -> dict:
    return {
        "works": tool.capacity >= problem.severity,
        "sensible": tool.sense >= SENSE_MIN,
        "team": tool.team,
    }


def explain_problem_rejection(problem: Problem, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        better = ", ".join(best_tools(problem))
        return (
            f"(No story: {tool.label} is known in the world, but it is too silly for this problem "
            f"(sense={tool.sense} < {SENSE_MIN}). Try a more reasonable fix like {better}.)"
        )
    if tool.capacity < problem.severity:
        return (
            f"(No story: {tool.label} cannot handle {problem.label}. The load is too much, "
            f"so the fix would not honestly solve the problem.)"
        )
    return "(No story: this problem and tool do not make a reasonable tale.)"


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for snack_id in SNACKS:
            for problem_id, problem in PROBLEMS.items():
                for tool_id, tool in TOOLS.items():
                    if valid_combo(problem, tool):
                        combos.append((setting_id, snack_id, problem_id, tool_id))
    return combos


def introduce(world: World, lead: Entity, friend: Entity, setting: Setting, snack: Snack) -> None:
    for kid in (lead, friend):
        kid.memes["friendship"] += 1
        kid.memes["joy"] += 1
        kid.meters["hunger"] += 1
    world.say(
        f"In {setting.place}, {lead.id} and {friend.id} were such good friends that "
        f"people said they could hear each other grin from two hills away."
    )
    world.say(
        f"That morning they planned {snack.phrase}, and the smell of {snack.smell} "
        f"rolled so far that even sleepy fence posts seemed to sniff the air."
    )
    world.say(
        f"They called the feast their grand nosh, because in their part of the world "
        f"a snack was never just a snack when two hungry friends were dreaming big."
    )


def build_snack(world: World, lead: Entity, friend: Entity, snack: Snack, setting: Setting) -> None:
    cart = world.get("cart")
    cart.meters["load"] = float(snack.magnitude)
    world.say(
        f"They piled {snack.cargo} onto a handcart until it looked high enough to tap "
        f"a passing cloud. {setting.boast}"
    )
    world.say(
        f'"We will roll this marvelous nosh all the way to the children waiting by {setting.ending_image}," '
        f'{lead.id} declared.'
    )


def problem_appears(world: World, friend: Entity, problem: Problem) -> None:
    prob = world.get("problem")
    prob.meters["stuck"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"But before they had gone twelve giant strides, {problem.cause}. "
        f"The cart stopped so suddenly that a crumb flew up and nearly circled the moon."
    )
    world.say(
        f'{friend.id} knelt beside the trouble. "Now the {problem.label} means we need {problem.fix_need}," '
        f'{friend.pronoun()} said.'
    )


def boast_bad_plan(world: World, lead: Entity, friend: Entity, tool: Tool) -> None:
    pred = predict_attempt(PROBLEMS[world.facts["problem_cfg"].id], tool)
    world.facts["warning_given"] = True
    lead.memes["boast"] += 1
    propagate(world, narrate=False)
    extra = ""
    if not pred["works"]:
        extra = " It looked exciting, but it was plain from the first blink that it would not do."
    elif not pred["sensible"]:
        extra = " It sounded loud and splendid, but not especially wise."
    world.say(
        f'{lead.id} puffed up proudly. "No need to fuss. We can use {tool.phrase}!" '
        f'{lead.pronoun().capitalize()} wanted the quickest, showiest answer.{extra}'
    )
    world.say(
        f'{friend.id} was compliant enough to listen, but not so compliant as to pretend a poor plan was good. '
        f'"A real fix should match the problem," {friend.pronoun()} said.'
    )


def failed_try(world: World, lead: Entity, tool: Tool) -> None:
    cart = world.get("cart")
    cart.meters["wobble"] += 1
    lead.memes["embarrassed"] += 1
    friend = world.get("friend")
    friend.memes["upset"] += 1
    world.say(
        f"They tried {tool.phrase}. For one noisy moment the cart lurched, rattled, and leaned like a tower of pies in a windstorm."
    )
    world.say(
        f"Then it settled back into the same stuck spot. Nobody was hurt, but the grand nosh looked in danger of becoming a grand mess."
    )


def apology_turn(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["stubborn"] = 0.0
    lead.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f'{lead.id} rubbed the back of {lead.pronoun("possessive")} neck. '
        f'"I was trying to sound bigger than the problem," {lead.pronoun()} admitted.'
    )
    world.say(
        f'{friend.id} nodded. "{friend.pronoun().capitalize()} can be big and still think carefully," '
        f'{friend.pronoun()} said, and the sharp part of the quarrel began to soften.'
    )


def choose_good_plan(world: World, lead: Entity, friend: Entity, tool: Tool) -> None:
    world.facts["teamed_up"] = True
    world.say(
        f'Together they chose {tool.phrase}. {tool.carry_text.capitalize()}, and this time each move made sense instead of just making noise.'
    )
    if tool.team:
        world.say(
            f"Because the plan asked for two pairs of hands, the friends had to listen to each other, count together, and pull at the same moment."
        )


def solve_problem(world: World, tool: Tool, snack: Snack) -> None:
    prob = world.get("problem")
    cart = world.get("cart")
    prob.meters["stuck"] = 0.0
    prob.meters["solved"] = 1.0
    cart.meters["wobble"] = 0.0
    cart.meters["moving"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{tool.solve_text.capitalize()}. The cart rolled free so neatly that even the crumbs seemed pleased."
    )
    world.say(
        f"Soon the friends reached the waiting children and shared {snack.serving}. {snack.share_line}"
    )


def ending(world: World, lead: Entity, friend: Entity, setting: Setting) -> None:
    world.say(
        f"After that, whenever a problem rose up as tall as a barn, {lead.id} and {friend.id} remembered that friendship worked best when pride stepped aside and thinking stepped in."
    )
    world.say(
        f"And under {setting.ending_image}, they ate, laughed, and watched the last crumbs shine like tiny golden sleds."
    )


def tell(setting: Setting, snack: Snack, problem_cfg: Problem, good_tool: Tool,
         bad_tool: Tool, lead_name: str = "Mara", lead_type: str = "girl",
         friend_name: str = "Bo", friend_type: str = "boy",
         parent_type: str = "mother", detour: bool = True) -> World:
    world = World()
    lead = world.add(Entity(id="lead", kind="character", type=lead_type, label=lead_name, role="lead"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    helper = world.add(Entity(id="helper", kind="character", type=parent_type, label="the baker", role="helper"))
    cart = world.add(Entity(id="cart", type="cart", label="handcart"))
    problem = world.add(Entity(id="problem", type="problem", label=problem_cfg.label))
    world.facts.update(
        setting=setting,
        snack=snack,
        problem_cfg=problem_cfg,
        good_tool=good_tool,
        bad_tool=bad_tool,
        detour=detour,
        warning_given=False,
        teamed_up=False,
        lead=lead,
        friend=friend,
        helper=helper,
        outcome="",
    )

    introduce(world, lead, friend, setting, snack)
    build_snack(world, lead, friend, snack, setting)

    world.para()
    problem_appears(world, friend, problem_cfg)

    world.para()
    if detour:
        boast_bad_plan(world, lead, friend, bad_tool)
        failed_try(world, lead, bad_tool)
        apology_turn(world, lead, friend)
    else:
        world.say(
            f'{lead.id} opened {lead.pronoun("possessive")} mouth for a brag, then stopped. '
            f'"Better idea," {lead.pronoun()} said. "Let us solve what is truly here, not the story I wanted to tell about it."'
        )
        world.say(
            f'{friend.id} grinned. "That is the best kind of giant talk," {friend.pronoun()} said.'
        )

    world.para()
    choose_good_plan(world, lead, friend, good_tool)
    solve_problem(world, good_tool, snack)

    world.para()
    ending(world, lead, friend, setting)

    world.facts["outcome"] = "recovered" if detour else "smooth"
    world.facts["shared"] = True
    world.facts["apologized"] = detour
    return world


SETTINGS = {
    "hill": Setting(
        id="hill",
        place="a windy hill town",
        boast="The handcart cast a shadow wide enough for three goats to nap in.",
        ending_image="the long hill grass",
        tags={"outdoor", "hill"},
    ),
    "river": Setting(
        id="river",
        place="a river village with a dock as long as a yawn",
        boast="The handcart creaked like a tiny ship carrying a feast for giants.",
        ending_image="the bright riverbank",
        tags={"outdoor", "river"},
    ),
    "orchard": Setting(
        id="orchard",
        place="an orchard where apples hung thick as lanterns",
        boast="The handcart rolled between the trees like a parade float for hungry birds.",
        ending_image="the apple trees",
        tags={"outdoor", "orchard"},
    ),
}

SNACKS = {
    "sandwiches": Snack(
        id="sandwiches",
        label="sandwiches",
        phrase="an armada of honey sandwiches",
        cargo="stack after stack of honey sandwiches and berry buns",
        smell="warm bread and bright berries",
        serving="plates piled with sandwiches and buns",
        share_line="Everybody ate until the talking slowed into happy chewing and soft sighs.",
        magnitude=2,
        tags={"food", "bread"},
    ),
    "pancakes": Snack(
        id="pancakes",
        label="pancakes",
        phrase="a mountain of skillet pancakes",
        cargo="pancakes, jam jars, and a butter crock the size of a boot tub",
        smell="butter, maple, and toasted batter",
        serving="pancakes folded around jam",
        share_line="Children licked jam from their thumbs and declared it the finest nosh in three counties.",
        magnitude=3,
        tags={"food", "breakfast"},
    ),
    "dumplings": Snack(
        id="dumplings",
        label="dumplings",
        phrase="a hill of picnic dumplings",
        cargo="baskets of dumplings and a kettle of sweet dipping sauce",
        smell="ginger, steam, and toasted sesame",
        serving="warm dumplings dipped in sweet sauce",
        share_line="The children cheered between bites, because good sharing somehow made every dumpling taste bigger.",
        magnitude=2,
        tags={"food", "savory"},
    ),
}

PROBLEMS = {
    "mud": Problem(
        id="mud",
        label="muddy rut",
        cause="one wheel sank into a muddy rut deeper than a boot and twice as clingy",
        fix_need="lift and steady the load",
        severity=2,
        tags={"mud", "stuck"},
    ),
    "bridge": Problem(
        id="bridge",
        label="narrow bridge",
        cause="the bridge ahead was so narrow that the cart could not pass straight through",
        fix_need="shift the load and guide the wheels carefully",
        severity=3,
        tags={"bridge", "balance"},
    ),
    "gate": Problem(
        id="gate",
        label="jammed gate",
        cause="a jammed gate blocked the path and would not budge for bluster alone",
        fix_need="brace the cart and work the latch together",
        severity=2,
        tags={"gate", "stuck"},
    ),
}

TOOLS = {
    "shoulder_poles": Tool(
        id="shoulder_poles",
        label="shoulder poles",
        phrase="two stout shoulder poles and a counted lift",
        capacity=3,
        sense=3,
        team=True,
        carry_text="They slid the poles under the trays, counted to three, and raised the load together",
        solve_text="With the weight shared between them, the cart and its burden moved where they asked",
        tags={"carry", "teamwork"},
    ),
    "board_ramp": Tool(
        id="board_ramp",
        label="board ramp",
        phrase="a wide board set firm under the wheel",
        capacity=2,
        sense=3,
        team=False,
        carry_text="They wedged the board under the troubled wheel and pushed in one smooth line",
        solve_text="The wheel climbed the board and out of trouble",
        tags={"ramp", "problem_solving"},
    ),
    "rope_harness": Tool(
        id="rope_harness",
        label="rope harness",
        phrase="a rope harness looped properly around the cart",
        capacity=3,
        sense=2,
        team=True,
        carry_text="They tied the rope low and snug, then leaned forward side by side",
        solve_text="The cart came along behind them steady as a well-trained pony",
        tags={"rope", "teamwork"},
    ),
    "goose_flap": Tool(
        id="goose_flap",
        label="goose feather fan",
        phrase="a giant goose feather fan and a heroic flap",
        capacity=0,
        sense=1,
        team=False,
        carry_text="They flapped the enormous feather as if wind alone could argue with gravity",
        solve_text="Nothing sensible happened",
        tags={"silly"},
    ),
    "moon_whistle": Tool(
        id="moon_whistle",
        label="moon whistle",
        phrase="a silver whistle meant to command the moon",
        capacity=0,
        sense=1,
        team=False,
        carry_text="They blew a long note and waited for the sky to help",
        solve_text="The sky stayed magnificent and unhelpful",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Mara", "June", "Lila", "Tess", "Nora", "Wren"]
BOY_NAMES = ["Bo", "Eli", "Finn", "Sam", "Toby", "Jude"]
TRAITS = ["brave", "cheerful", "steady", "bold", "kind", "quick-thinking"]


@dataclass
class StoryParams:
    setting: str
    snack: str
    problem: str
    solution_tool: str
    bad_tool: str
    lead_name: str
    lead_type: str
    friend_name: str
    friend_type: str
    helper_type: str
    detour: bool = True
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
    "mud": [(
        "Why can mud trap a wheel?",
        "Mud is soft and sticky, so a wheel can sink into it and lose the firm ground it needs to roll. The deeper the wheel sinks, the more lifting or support it needs."
    )],
    "bridge": [(
        "Why do narrow bridges need careful guiding?",
        "A narrow bridge gives very little room on either side. If a heavy cart is not guided carefully, a wheel can bump or slip."
    )],
    "gate": [(
        "Why is a jammed gate hard to open?",
        "A jammed gate sticks where its parts meet. Pushing harder is not always enough, so people often need to steady things and work the latch the right way."
    )],
    "carry": [(
        "Why does sharing a heavy load help?",
        "When two people share a load, each person carries less of the weight. That can make a hard job steadier and safer."
    )],
    "ramp": [(
        "What does a ramp do for a stuck wheel?",
        "A ramp gives the wheel a firm path to climb. That helps the wheel rise out of a hole or rut instead of spinning in place."
    )],
    "rope": [(
        "What is a harness for?",
        "A harness helps pull something by spreading force through a strap or rope. When it is tied properly, it can make pulling steadier."
    )],
    "teamwork": [(
        "Why is teamwork useful for solving problems?",
        "Teamwork lets people combine their strength and ideas. It also helps them notice mistakes and choose a better plan."
    )],
    "food": [(
        "What does the word 'nosh' mean?",
        "Nosh is a cozy word for food or a snack. People often use it when they are talking about eating happily together."
    )],
}
KNOWLEDGE_ORDER = ["food", "mud", "bridge", "gate", "carry", "ramp", "rope", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    snack = f["snack"]
    problem = f["problem_cfg"]
    if f["detour"]:
        return [
            f'Write a tall-tale friendship story that includes the word "nosh" and the word "compliant".',
            f"Tell a playful tall tale about two friends in {setting.place} whose giant {snack.label} trip is stopped by a {problem.label}, causing a quarrel before they solve it together.",
            f"Write a child-facing story where one friend boasts, the other gives a wiser plan, and the ending shows that teamwork beats pride.",
        ]
    return [
        f'Write a tall-tale story using the words "nosh" and "compliant".',
        f"Tell a giant-feeling friendship story in {setting.place} where two friends face a {problem.label} and solve it together without a big quarrel.",
        f"Write a gentle problem-solving story where the friends choose the sensible plan early and share their feast at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    friend = f["friend"]
    setting = f["setting"]
    snack = f["snack"]
    problem = f["problem_cfg"]
    good_tool = f["good_tool"]
    bad_tool = f["bad_tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {lead.label} and {friend.label}, who were carrying a giant shared nosh through {setting.place}. Their friendship matters because the problem is too big for one child to solve alone."
        ),
        (
            "What problem stopped the friends?",
            f"A {problem.label} stopped their cart. The trouble mattered because it blocked the path and threatened the food they meant to share."
        ),
        (
            "Why did the friends disagree?",
            f"{lead.label} wanted a showy shortcut, while {friend.label} wanted a plan that truly matched the problem. The conflict came from pride on one side and careful thinking on the other."
        ),
    ]
    if f["detour"]:
        qa.append((
            f"What happened when they tried {bad_tool.label}?",
            f"It did not solve the problem. The cart only lurched and wobbled, which showed that a loud idea is not always a useful one."
        ))
        qa.append((
            "How did they fix the quarrel?",
            f"{lead.label} admitted that boasting had not helped, and {friend.label} stayed kind enough to keep working together. Their apology cleared the hurt feelings so they could solve the real problem."
        ))
    qa.append((
        f"How did the friends solve the problem?",
        f"They used {good_tool.label}. That worked because it fit the kind of trouble they had and let them move the load in a steady, sensible way."
    ))
    qa.append((
        "How did the story end?",
        f"They reached the waiting children and shared the food. The ending proves the change because the friends are not just carrying a meal anymore; they are carrying each other a little better too."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"food"}
    tags |= set(world.facts["problem_cfg"].tags)
    tags |= set(world.facts["good_tool"].tags)
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
        if e.label and e.label != e.id:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="hill",
        snack="sandwiches",
        problem="mud",
        solution_tool="board_ramp",
        bad_tool="goose_flap",
        lead_name="Mara",
        lead_type="girl",
        friend_name="Bo",
        friend_type="boy",
        helper_type="mother",
        detour=True,
    ),
    StoryParams(
        setting="river",
        snack="pancakes",
        problem="bridge",
        solution_tool="shoulder_poles",
        bad_tool="moon_whistle",
        lead_name="June",
        lead_type="girl",
        friend_name="Finn",
        friend_type="boy",
        helper_type="father",
        detour=True,
    ),
    StoryParams(
        setting="orchard",
        snack="dumplings",
        problem="gate",
        solution_tool="rope_harness",
        bad_tool="goose_flap",
        lead_name="Eli",
        lead_type="boy",
        friend_name="Lila",
        friend_type="girl",
        helper_type="mother",
        detour=False,
    ),
]


ASP_RULES = r"""
valid_combo(P, T) :- problem(P), tool(T), capacity(T, C), severity(P, S), C >= S, sense(T, N), sense_min(M), N >= M.
valid(S, Sn, P, T) :- setting(S), snack(Sn), valid_combo(P, T).

smooth :- detour(0).
recovered :- detour(1).

outcome(smooth) :- smooth.
outcome(recovered) :- recovered.

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for snid in SNACKS:
        lines.append(asp.fact("snack", snid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, p.severity))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("capacity", tid, t.capacity))
        lines.append(asp.fact("sense", tid, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("detour", 1 if params.detour else 0)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "recovered" if params.detour else "smooth"


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
    for i in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(i))
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
        print(f"MISMATCH: {bad}/{len(cases)} ASP outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale friendship storyworld: a giant nosh, a quarrel, and a shared solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution-tool", choices=TOOLS)
    ap.add_argument("--bad-tool", choices=TOOLS)
    ap.add_argument("--detour", choices=["yes", "no"], help="whether they waste time on the boastful bad plan first")
    ap.add_argument("--lead-type", choices=["girl", "boy"])
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, typ: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if typ == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detour = None
    if args.detour is not None:
        detour = args.detour == "yes"

    if args.problem and args.solution_tool:
        if not valid_combo(PROBLEMS[args.problem], TOOLS[args.solution_tool]):
            raise StoryError(explain_problem_rejection(PROBLEMS[args.problem], TOOLS[args.solution_tool]))
    if args.problem and args.bad_tool and TOOLS[args.bad_tool].sense >= SENSE_MIN:
        raise StoryError("(No story: --bad-tool should name a boastful wrong tool, not a sensible solution.)")
    if args.solution_tool and args.bad_tool and args.solution_tool == args.bad_tool:
        raise StoryError("(No story: the wrong tool and the real solution tool must be different.)")

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.snack is None or c[1] == args.snack)
        and (args.problem is None or c[2] == args.problem)
        and (args.solution_tool is None or c[3] == args.solution_tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, snack_id, problem_id, solution_tool = rng.choice(sorted(combos))
    bad_choices = sorted(tid for tid, t in TOOLS.items() if t.sense < SENSE_MIN)
    if args.bad_tool is not None:
        if args.bad_tool not in bad_choices:
            raise StoryError("(No story: explicit --bad-tool must be an actually bad tool from this world.)")
        bad_tool = args.bad_tool
    else:
        bad_tool = rng.choice(bad_choices)

    lead_type = args.lead_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    lead_name = _pick_name(rng, lead_type)
    friend_name = _pick_name(rng, friend_type, avoid=lead_name)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    if detour is None:
        detour = rng.choice([True, False, True])

    return StoryParams(
        setting=setting_id,
        snack=snack_id,
        problem=problem_id,
        solution_tool=solution_tool,
        bad_tool=bad_tool,
        lead_name=lead_name,
        lead_type=lead_type,
        friend_name=friend_name,
        friend_type=friend_type,
        helper_type=helper_type,
        detour=detour,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.solution_tool not in TOOLS:
        raise StoryError(f"(Unknown solution tool: {params.solution_tool})")
    if params.bad_tool not in TOOLS:
        raise StoryError(f"(Unknown bad tool: {params.bad_tool})")

    problem = PROBLEMS[params.problem]
    good_tool = TOOLS[params.solution_tool]
    bad_tool = TOOLS[params.bad_tool]

    if not valid_combo(problem, good_tool):
        raise StoryError(explain_problem_rejection(problem, good_tool))
    if bad_tool.sense >= SENSE_MIN:
        raise StoryError("(The bad tool must remain a bad idea in this world.)")
    if params.bad_tool == params.solution_tool:
        raise StoryError("(The bad tool and the solution tool must be different.)")

    world = tell(
        setting=SETTINGS[params.setting],
        snack=SNACKS[params.snack],
        problem_cfg=problem,
        good_tool=good_tool,
        bad_tool=bad_tool,
        lead_name=params.lead_name,
        lead_type=params.lead_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.helper_type,
        detour=params.detour,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, snack, problem, solution_tool) combos:\n")
        for setting_id, snack_id, problem_id, tool_id in combos:
            print(f"  {setting_id:8} {snack_id:11} {problem_id:7} {tool_id}")
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
                f"### {p.lead_name} and {p.friend_name}: {p.snack} / {p.problem} "
                f"({p.solution_tool}, {'detour' if p.detour else 'smooth'})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
