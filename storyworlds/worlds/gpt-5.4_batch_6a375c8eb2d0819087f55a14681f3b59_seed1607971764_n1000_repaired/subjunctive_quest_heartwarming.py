#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py
============================================================

A standalone storyworld about a small, heartwarming quest.

The domain:
    A child sees that someone nearby needs comfort, declares a tiny heroic
    quest, and goes to fetch the needed item. A real obstacle stands in the
    way, so a helper offers the right tool and, when needed, a steady hand.
    The child succeeds, brings the item back, and the ending image proves that
    kindness changed the room.

The special seed constraint:
    The story text includes the exact word "subjunctive" in a natural way:
    the hero makes an "If I were ..." wish before beginning the quest.

Why the constraint gate exists:
    This world only tells quests whose obstacle can honestly be solved by the
    chosen tool, and some goals also require a helper who can steady and assist.
    For example, a lantern does not solve a muddy garden path, and a puppy
    cannot safely steady a stool under a high shelf. Invalid explicit choices
    are rejected with a clear StoryError.

Run it:
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py --goal blanket --tool stool
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py --goal blanket --helper puppy
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/subjunctive_quest_heartwarming.py --verify
"""

from __future__ import annotations

import argparse
import copy
import contextlib
import io
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister", "aunt"}
        male = {"boy", "father", "man", "grandfather", "brother", "uncle"}
        neutral = {"animal", "dog", "puppy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandfather": "grandpa",
            "grandmother": "grandma",
            "sister": "sister",
            "brother": "brother",
            "puppy": "puppy",
        }
        return mapping.get(self.type, self.label or self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class QuestTheme:
    id: str
    role_noun: str
    route_line: str
    token: str
    ending_line: str
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
class Obstacle:
    id: str
    label: str
    capability: str
    risk: str
    block_line: str
    open_line: str
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
class Goal:
    id: str
    item_label: str
    item_phrase: str
    source_place: str
    recipient_name: str
    recipient_type: str
    recipient_label: str
    opening_need: str
    request_line: str
    obstacle: str
    discovery_line: str
    delivery_line: str
    ending_image: str
    needs_steady: bool = False
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
    capability: str
    offer_line: str
    use_line: str
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
class HelperCfg:
    id: str
    type: str
    label: str
    phrase: str
    can_steady: bool
    teaches: bool
    comfort_style: str
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


def _r_open_path(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    tool = world.get("tool")
    place = world.get("place")
    if hero.meters["at_source"] < THRESHOLD or tool.meters["ready"] < THRESHOLD:
        return out
    if place.meters["open"] >= THRESHOLD:
        return out
    sig = ("open_path",)
    if sig in world.fired:
        return out
    if tool.attrs.get("capability") != place.attrs.get("obstacle"):
        return out
    if place.attrs.get("needs_steady") and helper.meters["helping"] < THRESHOLD:
        return out
    world.fired.add(sig)
    place.meters["open"] += 1
    hero.memes["hope"] += 1
    out.append("__open__")
    return out


def _r_retrieve_item(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    place = world.get("place")
    item = world.get("item")
    if hero.meters["at_source"] < THRESHOLD or place.meters["open"] < THRESHOLD:
        return out
    sig = ("retrieve_item",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["retrieved"] += 1
    hero.meters["carrying"] += 1
    hero.memes["joy"] += 1
    out.append("__retrieved__")
    return out


def _r_deliver_item(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    recipient = world.get("recipient")
    helper = world.get("helper")
    if hero.meters["home"] < THRESHOLD or item.meters["retrieved"] < THRESHOLD:
        return out
    sig = ("deliver_item",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["delivered"] += 1
    recipient.memes["comfort"] += 2
    recipient.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    out.append("__delivered__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="open_path", tag="physical", apply=_r_open_path),
    Rule(name="retrieve_item", tag="physical", apply=_r_retrieve_item),
    Rule(name="deliver_item", tag="social", apply=_r_deliver_item),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


QUESTS = {
    "knight": QuestTheme(
        id="knight",
        role_noun="a little knight",
        route_line="The hallway felt as long as a castle road.",
        token="a paper star shield",
        ending_line="The room felt less like an ordinary room and more like a tiny kingdom made safe by kindness.",
    ),
    "ranger": QuestTheme(
        id="ranger",
        role_noun="a trail ranger",
        route_line="Each doorway looked like the start of a gentle forest trail.",
        token="a green ribbon map",
        ending_line="The house seemed to glow like a warm cabin after a good walk home.",
    ),
    "star_scout": QuestTheme(
        id="star_scout",
        role_noun="a star scout",
        route_line="Even the dim corners looked like places where a brave scout might earn one more star.",
        token="a silver paper badge",
        ending_line="The room felt bright and close, as if a small star had landed right there among them.",
    ),
    "courier": QuestTheme(
        id="courier",
        role_noun="a royal courier",
        route_line="The trip across the house felt important, as if every step carried a message of care.",
        token="a folded note tucked in a pocket",
        ending_line="It felt as though kindness itself had arrived at the door and been invited in.",
    ),
}

OBSTACLES = {
    "high_shelf": Obstacle(
        id="high_shelf",
        label="a high shelf",
        capability="reach_high",
        risk="tip and stretch too far",
        block_line="The shelf stood above little hands, with the needed thing resting on the top ledge.",
        open_line="The stool made the high place reachable, and a steady hand kept the climb calm and safe.",
        tags={"high", "shelf"},
    ),
    "dark_corner": Obstacle(
        id="dark_corner",
        label="a dark corner",
        capability="light_dark",
        risk="fumble in the dark and miss the item",
        block_line="The corner looked dusky and deep, and the needed thing was hidden where shadows crowded together.",
        open_line="The lantern pushed the shadows back, and the hiding place became plain to see.",
        tags={"dark", "light"},
    ),
    "muddy_path": Obstacle(
        id="muddy_path",
        label="a muddy path",
        capability="cross_mud",
        risk="slip and splash before reaching the door",
        block_line="The path to the little shed was a ribbon of mud, shiny and slippery after the rain.",
        open_line="The boots made each step firm, so the path could be crossed with a brave little squish instead of a slip.",
        tags={"mud", "path"},
    ),
    "thorny_patch": Obstacle(
        id="thorny_patch",
        label="a thorny patch",
        capability="handle_thorns",
        risk="get prickled fingers",
        block_line="The ribbon was caught where thin thorns reached out like tiny hooks.",
        open_line="The gloves let careful fingers work without any prickles at all.",
        tags={"thorn", "garden"},
    ),
}

GOALS = {
    "blanket": Goal(
        id="blanket",
        item_label="blanket",
        item_phrase="a soft yellow blanket",
        source_place="the tall linen shelf in the hall closet",
        recipient_name="Pip",
        recipient_type="boy",
        recipient_label="baby brother",
        opening_need="Baby Pip sat on the sofa with chilly toes and a wobbling lower lip.",
        request_line="He needed his favorite blanket before he could settle down and rest.",
        obstacle="high_shelf",
        discovery_line="Folded at the back of the shelf was the soft yellow blanket they had been looking for.",
        delivery_line="The blanket was tucked around Pip until his toes disappeared and his shoulders stopped shivering.",
        ending_image="Pip sighed, pressed his cheek to the blanket, and gave the room a sleepy little smile.",
        needs_steady=True,
        tags={"blanket", "comfort"},
    ),
    "songbook": Goal(
        id="songbook",
        item_label="songbook",
        item_phrase="the red songbook",
        source_place="the dark cupboard under the stairs",
        recipient_name="Grandma",
        recipient_type="grandmother",
        recipient_label="grandma",
        opening_need="Grandma had promised a bedtime song, but she could not find the little red book with all the family favorites.",
        request_line="Without it, the song she wanted most stayed stuck behind a thoughtful hush.",
        obstacle="dark_corner",
        discovery_line="There, behind a stack of puzzles, lay the red songbook with its ribbon marker peeking out.",
        delivery_line="Grandma opened the songbook right away and found the page she had been missing.",
        ending_image="Soon her voice filled the room again, soft and warm as a blanket made of sound.",
        needs_steady=False,
        tags={"music", "book"},
    ),
    "honey": Goal(
        id="honey",
        item_label="honey jar",
        item_phrase="a small jar of honey",
        source_place="the little shed beyond the muddy garden path",
        recipient_name="Mrs. Dell",
        recipient_type="woman",
        recipient_label="neighbor",
        opening_need="Mrs. Dell had a scratchy throat and was waiting on the porch with a cup of plain tea.",
        request_line="A little honey would make the tea gentler and sweeter.",
        obstacle="muddy_path",
        discovery_line="On the shed shelf sat the small honey jar, gold and bright even in the gray light.",
        delivery_line="The honey was stirred into the tea until the cup smelled sweet and cozy.",
        ending_image="Mrs. Dell took a careful sip, and the tight look around her throat softened into relief.",
        needs_steady=False,
        tags={"tea", "honey", "neighbor"},
    ),
    "ribbon": Goal(
        id="ribbon",
        item_label="ribbon",
        item_phrase="the blue ribbon",
        source_place="the rose arbor by the gate",
        recipient_name="Nia",
        recipient_type="girl",
        recipient_label="friend",
        opening_need="Nia's little kite had lost its tail, and without the blue ribbon it only flopped instead of dancing.",
        request_line="The ribbon had blown away and snagged where nobody wanted scratched hands.",
        obstacle="thorny_patch",
        discovery_line="The blue ribbon fluttered from the rose arbor, still bright and still worth rescuing.",
        delivery_line="The ribbon was tied back onto the kite with a neat, hopeful bow.",
        ending_image="When the kite lifted at last, Nia laughed so hard that even the gate seemed to rattle with joy.",
        needs_steady=False,
        tags={"kite", "ribbon", "friend"},
    ),
}

TOOLS = {
    "stool": Tool(
        id="stool",
        label="stool",
        phrase="a little wooden stool",
        capability="reach_high",
        offer_line="brought over a little wooden stool",
        use_line="set the stool in place and climbed one careful step at a time",
        tags={"stool", "reach"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a battery lantern",
        capability="light_dark",
        offer_line="clicked on a battery lantern",
        use_line="lifted the lantern high so the dark place could not keep its secret",
        tags={"lantern", "light"},
    ),
    "boots": Tool(
        id="boots",
        label="boots",
        phrase="a pair of rain boots",
        capability="cross_mud",
        offer_line="found a pair of rain boots by the back door",
        use_line="pulled on the boots and stepped into the mud with steady little thumps",
        tags={"boots", "mud"},
    ),
    "gloves": Tool(
        id="gloves",
        label="gloves",
        phrase="soft garden gloves",
        capability="handle_thorns",
        offer_line="shook out a pair of soft garden gloves",
        use_line="slid on the gloves and reached slowly between the thorns",
        tags={"gloves", "garden"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        label="Mom",
        phrase="her mom",
        can_steady=True,
        teaches=True,
        comfort_style="smiled in the calm way that makes hard things seem possible",
        tags={"parent", "mother"},
    ),
    "grandfather": HelperCfg(
        id="grandfather",
        type="grandfather",
        label="Grandpa",
        phrase="grandpa",
        can_steady=True,
        teaches=True,
        comfort_style="twinkled at the plan as if he had been waiting all day for such a quest",
        tags={"grandparent", "grandpa"},
    ),
    "sister": HelperCfg(
        id="sister",
        type="sister",
        label="Ada",
        phrase="her big sister Ada",
        can_steady=True,
        teaches=False,
        comfort_style="leaned close with a grin that said they could do this together",
        tags={"sibling", "sister"},
    ),
    "puppy": HelperCfg(
        id="puppy",
        type="puppy",
        label="Button",
        phrase="the puppy Button",
        can_steady=False,
        teaches=False,
        comfort_style="wagged as if the whole quest were the best idea in the world",
        tags={"animal", "puppy"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Zoe", "Ella", "Ruby", "Tess", "Ivy", "Nora"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Eli", "Sam", "Leo", "Ben"]
TRAITS = ["gentle", "bright-eyed", "careful", "hopeful", "kind", "eager"]


def goal_obstacle(goal: Goal) -> Obstacle:
    if goal.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle for goal '{goal.id}': {goal.obstacle})")
    return OBSTACLES[goal.obstacle]


def tool_matches(goal: Goal, tool: Tool) -> bool:
    return tool.capability == goal_obstacle(goal).capability


def helper_supports(goal: Goal, helper: HelperCfg) -> bool:
    return (not goal.needs_steady) or helper.can_steady


def valid_combo(goal: Goal, tool: Tool, helper: HelperCfg) -> bool:
    return tool_matches(goal, tool) and helper_supports(goal, helper)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for goal_id, goal in GOALS.items():
            for tool_id, tool in TOOLS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_combo(goal, tool, helper):
                        combos.append((quest_id, goal_id, tool_id, helper_id))
    return combos


def explain_tool(goal: Goal, tool: Tool) -> str:
    obstacle = goal_obstacle(goal)
    return (
        f"(No story: {tool.phrase} does not solve {obstacle.label} while trying to fetch "
        f"{goal.item_phrase}. Pick a tool that can handle {obstacle.label}.)"
    )


def explain_helper(goal: Goal, helper: HelperCfg) -> str:
    return (
        f"(No story: fetching {goal.item_phrase} needs a helper who can steady and assist, "
        f"but {helper.label} cannot do that safely. Pick a steadier helper.)"
    )


def approach_of(params: "StoryParams") -> str:
    if params.goal not in GOALS or params.helper not in HELPERS:
        raise StoryError("(Cannot infer approach: unknown goal or helper.)")
    goal = GOALS[params.goal]
    helper = HELPERS[params.helper]
    if goal.needs_steady:
        return "assisted"
    if helper.teaches:
        return "guided"
    return "companion"


def predict_without_solution(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    place = sim.get("place")
    hero.meters["at_source"] += 1
    propagate(sim, narrate=False)
    return {
        "open": place.meters["open"] >= THRESHOLD,
        "risk": place.attrs.get("risk", ""),
    }


def introduce(world: World, hero: Entity, helper: Entity, recipient: Entity,
              theme: QuestTheme, goal: Goal) -> None:
    hero.memes["care"] += 1
    recipient.memes["worry"] += 1
    world.say(
        f"{hero.id} was a {', '.join(hero.traits[:2])} little {hero.type} who never liked to leave a worried face alone for long."
    )
    world.say(goal.opening_need)
    world.say(goal.request_line)
    world.say(
        f'"If I were {theme.role_noun}, I would begin at once," {hero.id} said, touching {theme.token} as if it were a real badge.'
    )
    world.say(
        f"It was a subjunctive kind of sentence, the sort of brave pretend wish that helps real feet start moving. {helper.label} {helper.attrs.get('comfort_style', '')}."
    )


def set_quest(world: World, hero: Entity, theme: QuestTheme, goal: Goal) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"So the quest was clear: travel to {goal.source_place}, fetch {goal.item_phrase}, and bring it back before the room grew any sadder."
    )
    world.say(theme.route_line)


def warn_and_offer(world: World, hero: Entity, helper: Entity, goal: Goal, tool: Tool) -> None:
    pred = predict_without_solution(world)
    world.facts["predicted_risk"] = pred["risk"]
    obstacle = goal_obstacle(goal)
    world.say(obstacle.block_line)
    if pred["risk"]:
        world.say(
            f'{helper.label} noticed that trying it bare-handed would {pred["risk"]}. "{tool.offer_line.capitalize()}," {helper.label.lower() if helper.type == "puppy" else helper.label} said.'
        )
    else:
        world.say(f"{helper.label} looked the way over and still reached for {tool.phrase}, just to make the trip easier.")
    if goal.needs_steady:
        world.say(
            f'"I will keep it steady for you," {helper.label} promised. That made the quest feel safer without making it feel any smaller.'
        )
    elif helper.attrs.get("teaches"):
        world.say(
            f'"Good quests use the right tools," {helper.label} said softly. {hero.id} nodded and listened.'
        )
    else:
        world.say(
            f"{helper.label} came along at once, eager to be part of the adventure."
        )


def go_to_source(world: World, hero: Entity, goal: Goal) -> None:
    hero.meters["at_source"] += 1
    hero.meters["home"] = 0.0
    world.say(
        f"{hero.id} hurried to {goal.source_place}, heart busy with the important kind of hurry that comes from trying to help."
    )


def ready_tool(world: World, hero: Entity, helper: Entity, tool: Tool, goal: Goal) -> None:
    tool_ent = world.get("tool")
    tool_ent.meters["ready"] += 1
    if goal.needs_steady:
        helper.meters["helping"] += 1
    world.say(f"{hero.id} {tool.use_line}.")
    if goal.needs_steady:
        world.say(f"{helper.label} held everything firm and safe from below.")


def open_and_find(world: World, hero: Entity, goal: Goal) -> None:
    place = world.get("place")
    item = world.get("item")
    propagate(world, narrate=False)
    if place.meters["open"] < THRESHOLD:
        raise StoryError("(Story logic error: the path never opened.)")
    world.say(goal_obstacle(goal).open_line)
    if item.meters["retrieved"] < THRESHOLD:
        raise StoryError("(Story logic error: the item was not retrieved.)")
    world.say(goal.discovery_line)


def return_and_deliver(world: World, hero: Entity, recipient: Entity, goal: Goal) -> None:
    hero.meters["home"] += 1
    propagate(world, narrate=False)
    item = world.get("item")
    if item.meters["delivered"] < THRESHOLD:
        raise StoryError("(Story logic error: the item was not delivered.)")
    world.say(
        f"{hero.id} carried the prize back with both hands, careful as if kindness itself might spill if the journey became too bouncy."
    )
    world.say(goal.delivery_line)


def ending(world: World, hero: Entity, helper: Entity, recipient: Entity,
           theme: QuestTheme, goal: Goal, approach: str) -> None:
    hero.memes["love"] += 1
    if helper.memes["joy"] < THRESHOLD:
        helper.memes["joy"] += 1
    world.say(goal.ending_image)
    if approach == "assisted":
        world.say(
            f'{hero.id} looked at {helper.label} and smiled. "It was my quest," {hero.pronoun()} said, "but it was easier because you came too."'
        )
    elif approach == "guided":
        world.say(
            f"{helper.label} squeezed {hero.pronoun('possessive')} shoulder, proud that listening and courage had worked together so well."
        )
    else:
        world.say(
            f"Even {helper.label} seemed pleased, padding or hurrying in small happy circles beside the hero."
        )
    world.say(theme.ending_line)


@dataclass
class StoryParams:
    quest: str
    goal: str
    tool: str
    helper: str
    hero_name: str
    hero_gender: str
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


def tell(theme: QuestTheme, goal: Goal, tool: Tool, helper_cfg: HelperCfg,
         hero_name: str = "Lina", hero_gender: str = "girl",
         trait: str = "kind") -> World:
    if not valid_combo(goal, tool, helper_cfg):
        if not tool_matches(goal, tool):
            raise StoryError(explain_tool(goal, tool))
        raise StoryError(explain_helper(goal, helper_cfg))

    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait, "small"],
        attrs={},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        attrs={
            "can_steady": helper_cfg.can_steady,
            "teaches": helper_cfg.teaches,
            "comfort_style": helper_cfg.comfort_style,
        },
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=goal.recipient_type,
        label=goal.recipient_name,
        role="recipient",
        attrs={"relation": goal.recipient_label},
    ))
    place = world.add(Entity(
        id="place",
        kind="thing",
        type="place",
        label=goal.source_place,
        role="source",
        attrs={
            "obstacle": goal_obstacle(goal).capability,
            "needs_steady": goal.needs_steady,
            "risk": goal_obstacle(goal).risk,
        },
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=goal.item_label,
        phrase=goal.item_phrase,
        role="goal_item",
        attrs={},
    ))
    tool_ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        role="tool",
        attrs={"capability": tool.capability},
    ))

    world.facts.update(
        theme=theme,
        goal=goal,
        tool_cfg=tool,
        helper_cfg=helper_cfg,
        hero_name=hero_name,
        hero_gender=hero_gender,
        trait=trait,
        approach=approach_of(StoryParams(
            quest=theme.id,
            goal=goal.id,
            tool=tool.id,
            helper=helper_cfg.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            trait=trait,
        )),
    )

    introduce(world, hero, helper, recipient, theme, goal)
    set_quest(world, hero, theme, goal)

    world.para()
    warn_and_offer(world, hero, helper, goal, tool)
    go_to_source(world, hero, goal)
    ready_tool(world, hero, helper, tool, goal)

    world.para()
    open_and_find(world, hero, goal)
    return_and_deliver(world, hero, recipient, goal)

    world.para()
    ending(world, hero, helper, recipient, theme, goal, world.facts["approach"])

    world.facts.update(
        hero=hero,
        helper=helper,
        recipient=recipient,
        item=item,
        place=place,
        tool=tool_ent,
        delivered=item.meters["delivered"] >= THRESHOLD,
        comforted=recipient.memes["comfort"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a trip with a purpose. Someone sets out to do something important and keeps going until the job is done."
        )
    ],
    "subjunctive": [
        (
            "What does subjunctive mean in a sentence like 'If I were a knight'?",
            "Subjunctive is a grammar word for an imagined wish or possibility. It helps people talk about what they hope, pretend, or wonder about."
        )
    ],
    "stool": [
        (
            "What is a stool used for?",
            "A stool is a small seat or step you can stand on to reach something high. A grown-up should stay close so it does not wobble."
        )
    ],
    "lantern": [
        (
            "What does a lantern help with?",
            "A lantern gives light so you can see into dark places. It helps hidden things stop being hidden."
        )
    ],
    "boots": [
        (
            "Why do boots help on mud?",
            "Boots protect your feet and give you steadier steps. That makes muddy ground safer to cross."
        )
    ],
    "gloves": [
        (
            "Why do gloves help near thorns?",
            "Gloves cover your hands, so scratchy thorns are less likely to prick your skin. They let you work more carefully."
        )
    ],
    "blanket": [
        (
            "Why can a blanket comfort someone?",
            "A blanket can make someone feel warm and tucked in. Feeling warm often helps a body relax."
        )
    ],
    "songbook": [
        (
            "What is a songbook?",
            "A songbook is a book that keeps songs or words together in one place. It helps people remember what to sing."
        )
    ],
    "honey": [
        (
            "Why do people put honey in tea?",
            "Honey makes tea sweet and smooth. Some people like it when their throat feels scratchy."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth used for tying or decorating things. It can make a kite tail flutter nicely in the wind."
        )
    ],
    "help": [
        (
            "Why is asking for help a strong thing to do?",
            "Asking for help is strong because it means you care more about doing something safely than about showing off. Teamwork often solves problems better."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "quest",
    "subjunctive",
    "stool",
    "lantern",
    "boots",
    "gloves",
    "blanket",
    "songbook",
    "honey",
    "ribbon",
    "help",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    goal = world.facts["goal"]
    theme = world.facts["theme"]
    helper = world.facts["helper"]
    tool = world.facts["tool"]
    return [
        (
            f'Write a heartwarming quest story for a 3-to-5-year-old that includes the exact word '
            f'"subjunctive" and begins with a child saying, "If I were {theme.role_noun}..."'
        ),
        (
            f"Tell a gentle story where {hero.label} goes on a tiny quest to fetch {goal.item_phrase} "
            f"for {goal.recipient_name}, faces {goal_obstacle(goal).label}, and succeeds by using {tool.phrase} with help from {helper.label}."
        ),
        (
            f"Write a warm home adventure about kindness turning into action, with a real obstacle, a sensible tool, and an ending image that shows {goal.recipient_label} feeling better."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    recipient = world.facts["recipient"]
    goal = world.facts["goal"]
    theme = world.facts["theme"]
    tool = world.facts["tool"]
    obstacle = goal_obstacle(goal)
    approach = world.facts["approach"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who wanted to help {recipient.label}, and {helper.label}, who came along on the quest."
        ),
        (
            "What was the quest?",
            f"The quest was to fetch {goal.item_phrase} from {goal.source_place} and bring it back to {recipient.label}. It mattered because {goal.request_line[0].lower() + goal.request_line[1:]}"
        ),
        (
            "Why does the story use the word 'subjunctive'?",
            f"The story uses it when {hero.label} says, 'If I were {theme.role_noun}.' That kind of sentence is about imagining bravery before acting on it."
        ),
        (
            f"What obstacle stood in the way?",
            f"{obstacle.label.capitalize()} stood in the way. Without the right help, {hero.label} might {obstacle.risk}, so the quest needed a sensible plan."
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} used {tool.phrase} to get past {obstacle.label}. That worked because {tool.label} matched the problem instead of just making the trip feel busy."
        ),
    ]
    if approach == "assisted":
        qa.append(
            (
                f"Why did {helper.label} need to help closely?",
                f"{goal.item_phrase.capitalize()} was in a place that needed a steady helper. {helper.label} kept things safe, so {hero.label} could be brave without being reckless."
            )
        )
    elif approach == "guided":
        qa.append(
            (
                f"What did {helper.label} add to the quest?",
                f"{helper.label} added calm advice as well as company. The helper showed that courage grows better when someone teaches the safe way to do a hard thing."
            )
        )
    else:
        qa.append(
            (
                f"What did {helper.label} add to the quest?",
                f"{helper.label} added cheerful company and made the trip feel less lonely. Even small help can make a brave job feel warmer."
            )
        )
    qa.append(
        (
            f"How did the story end?",
            f"It ended with {recipient.label} feeling better after {goal.delivery_line[0].lower() + goal.delivery_line[1:]}. The final image proves the quest changed the room, not just the hero."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    goal = world.facts["goal"]
    tool = world.facts["tool_cfg"]
    tags: set[str] = {"quest", "subjunctive", "help"}
    tags |= set(tool.tags)
    if goal.id == "blanket":
        tags.add("blanket")
    elif goal.id == "songbook":
        tags.add("songbook")
    elif goal.id == "honey":
        tags.add("honey")
    elif goal.id == "ribbon":
        tags.add("ribbon")
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:9} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="knight",
        goal="blanket",
        tool="stool",
        helper="mother",
        hero_name="Lina",
        hero_gender="girl",
        trait="kind",
    ),
    StoryParams(
        quest="star_scout",
        goal="songbook",
        tool="lantern",
        helper="grandfather",
        hero_name="Milo",
        hero_gender="boy",
        trait="hopeful",
    ),
    StoryParams(
        quest="ranger",
        goal="honey",
        tool="boots",
        helper="puppy",
        hero_name="Nora",
        hero_gender="girl",
        trait="careful",
    ),
    StoryParams(
        quest="courier",
        goal="ribbon",
        tool="gloves",
        helper="sister",
        hero_name="Owen",
        hero_gender="boy",
        trait="bright-eyed",
    ),
]


ASP_RULES = r"""
valid(Q, G, T, H) :- quest(Q), goal(G), tool(T), helper(H),
                     obstacle_of(G, O), handles(T, O),
                     not needs_steady(G).
valid(Q, G, T, H) :- quest(Q), goal(G), tool(T), helper(H),
                     obstacle_of(G, O), handles(T, O),
                     needs_steady(G), can_steady(H).

approach(assisted)  :- chosen_goal(G), needs_steady(G).
approach(guided)    :- chosen_goal(G), not needs_steady(G),
                       chosen_helper(H), teaches(H).
approach(companion) :- chosen_goal(G), not needs_steady(G),
                       chosen_helper(H), not teaches(H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("obstacle_of", gid, goal.obstacle))
        if goal.needs_steady:
            lines.append(asp.fact("needs_steady", gid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("capability", oid, obstacle.capability))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        needed_obstacles = [oid for oid, ob in OBSTACLES.items() if ob.capability == tool.capability]
        for oid in needed_obstacles:
            lines.append(asp.fact("handles", tid, oid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.can_steady:
            lines.append(asp.fact("can_steady", hid))
        if helper.teaches:
            lines.append(asp.fact("teaches", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_approach(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_goal", params.goal),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(extra, "#show approach/1."))
    atoms = asp.atoms(model, "approach")
    return atoms[0][0] if atoms else "?"


def _smoke_story() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("(Smoke test failed: generated story was empty.)")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=True, qa=True)
    dumped = buf.getvalue()
    if "subjunctive" not in sample.story:
        raise StoryError("(Smoke test failed: generated story did not include 'subjunctive'.)")
    if not dumped.strip():
        raise StoryError("(Smoke test failed: emit() produced no output.)")


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    bad = 0
    for params in cases:
        py = approach_of(params)
        asp_res = asp_approach(params)
        if py != asp_res:
            bad += 1
    if bad == 0:
        print(f"OK: approach model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} approach predictions differ.")

    try:
        _smoke_story()
        print("OK: smoke generation/emit test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming quest storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible quest combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal and args.tool:
        goal = GOALS[args.goal]
        tool = TOOLS[args.tool]
        if not tool_matches(goal, tool):
            raise StoryError(explain_tool(goal, tool))
    if args.goal and args.helper:
        goal = GOALS[args.goal]
        helper = HELPERS[args.helper]
        if not helper_supports(goal, helper):
            raise StoryError(explain_helper(goal, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.goal is None or combo[1] == args.goal)
        and (args.tool is None or combo[2] == args.tool)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, goal_id, tool_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        goal=goal_id,
        tool=tool_id,
        helper=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest theme: {params.quest})")
    if params.goal not in GOALS:
        raise StoryError(f"(Unknown goal: {params.goal})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")

    goal = GOALS[params.goal]
    tool = TOOLS[params.tool]
    helper = HELPERS[params.helper]
    if not valid_combo(goal, tool, helper):
        if not tool_matches(goal, tool):
            raise StoryError(explain_tool(goal, tool))
        raise StoryError(explain_helper(goal, helper))

    world = tell(
        theme=QUESTS[params.quest],
        goal=goal,
        tool=tool,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        trait=params.trait,
    )
    hero_ent = world.get("hero")
    hero_ent.label = params.hero_name

    story_text = world.render().replace("hero", params.hero_name)
    story_text = story_text.replace('"I will keep it steady for you," Mom promised.', '"I will keep it steady for you," Mom promised.')
    story_text = story_text.replace(" hero ", f" {params.hero_name} ")
    story_text = story_text.replace(" hero.", f" {params.hero_name}.")
    story_text = story_text.replace(" hero,", f" {params.hero_name},")

    # Replace internal hero id where it occurred in prose.
    story_text = story_text.replace("hero's", f"{params.hero_name}'s")
    story_text = story_text.replace("hero", params.hero_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("", "#show valid/4.\n#show approach/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, goal, tool, helper) combos:\n")
        for quest_id, goal_id, tool_id, helper_id in combos:
            print(f"  {quest_id:10} {goal_id:9} {tool_id:8} {helper_id}")
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
            header = f"### {p.hero_name}: {p.quest} quest for {p.goal} ({p.tool}, {p.helper})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
