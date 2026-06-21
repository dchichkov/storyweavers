#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py
=================================================================================

A small standalone storyworld about two children, one wind-up robot named
"Psycho", and a problem solved with kindness and sharing.

Every story is a complete little rhyming tale:
- a bright setup with a scarce toy,
- a real social pinch when one child keeps it,
- a sensible sharing plan,
- and an ending image that proves the children changed.

The word "minute" appears through one-minute turns when the chosen tool is a
timer, and the word "psycho" appears as the printed name on the toy robot
itself -- never as an insult.

Run it
------
    python storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py --setting porch --challenge race --tool sand_timer
    python storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py --challenge maze --tool kitchen_timer
    python storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/minute_psycho_rhyme_kindness_sharing_rhyming_story.py --verify
"""

from __future__ import annotations

import argparse
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
POSSESSIVE_BASE = 5
SOFT_TRAITS = {"kind", "gentle", "tender", "thoughtful"}
PATIENT_TRAITS = {"calm", "steady", "thoughtful", "cheerful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "teacher_f"}
        male = {"boy", "father", "uncle", "teacher_m"}
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
            "aunt": "aunt",
            "uncle": "uncle",
            "teacher_f": "teacher",
            "teacher_m": "teacher",
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
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    intro: str
    request: str
    scene: str
    plan: str
    closing: str
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
    supports: set[str] = field(default_factory=set)
    cue: str = ""
    minute_based: bool = False
    rhythmic: bool = False
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
    warmth: int
    line: str
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
class StoryParams:
    setting: str
    challenge: str
    tool: str
    helper: str
    sharer: str
    sharer_gender: str
    waiter: str
    waiter_gender: str
    sharer_trait: str
    waiter_trait: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "sharing_started": False,
            "plan_kind": "",
            "tool_kind": "",
            "turns_taken": 0,
            "jobs_assigned": False,
        }

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


def _r_waiting_hurts(world: World) -> list[str]:
    out: list[str] = []
    toy = world.entities.get("toy")
    sharer = world.entities.get("sharer")
    waiter = world.entities.get("waiter")
    if not toy or not sharer or not waiter:
        return out
    if toy.attrs.get("holder") != sharer.id or waiter.memes["want_turn"] < THRESHOLD:
        return out
    sig = ("waiting_hurts", sharer.id, waiter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    waiter.memes["sad"] += 1
    sharer.memes["clutchy"] += 1
    out.append("__pinch__")
    return out


def _r_sharing_heals(world: World) -> list[str]:
    out: list[str] = []
    sharer = world.entities.get("sharer")
    waiter = world.entities.get("waiter")
    toy = world.entities.get("toy")
    if not sharer or not waiter or not toy:
        return out
    if not world.facts.get("sharing_started"):
        return out
    sig = ("sharing_heals", world.facts.get("plan_kind", ""))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sharer.memes["kindness"] += 1
    waiter.memes["relief"] += 1
    sharer.memes["joy"] += 1
    waiter.memes["joy"] += 1
    waiter.memes["sad"] = 0.0
    toy.meters["shared"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule(name="waiting_hurts", tag="social", apply=_r_waiting_hurts),
    Rule(name="sharing_heals", tag="social", apply=_r_sharing_heals),
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
    "playroom": Setting(
        id="playroom",
        place="the playroom rug",
        detail="Paper stars were taped to the wall, and a strip of sun lay gold on the rug.",
        affords={"race", "maze", "dance"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch boards",
        detail="The porch boards hummed in the breeze, and the shadows made long little roads.",
        affords={"race", "dance"},
    ),
    "reading_nook": Setting(
        id="reading_nook",
        place="the reading nook",
        detail="Cushions sat in a soft half-moon, with baskets and cardboard boxes close by.",
        affords={"maze", "dance"},
    ),
}

CHALLENGES = {
    "race": Challenge(
        id="race",
        intro="They found a shiny tin robot with the word Psycho painted on its belly in bright blue.",
        request="Both children wanted to wind it up and send it skittering first.",
        scene="across the floor in a click-clack race",
        plan="turns",
        closing="Soon the little robot rattled out and back, and both children laughed at every crooked track.",
        tags={"robot", "sharing", "minute"},
    ),
    "maze": Challenge(
        id="maze",
        intro="They found a shiny tin robot with the word Psycho painted on its belly in bright blue.",
        request="One child wanted to wind it while the other wanted to guide it through a box maze.",
        scene="through a cardboard maze with flap doors and tape",
        plan="teamwork",
        closing="Soon the robot marched through paper lanes, and both children cheered its tiny tippy trains.",
        tags={"robot", "sharing", "teamwork"},
    ),
    "dance": Challenge(
        id="dance",
        intro="They found a shiny tin robot with the word Psycho painted on its belly in bright blue.",
        request="Both children wanted to make it dance and bow on the beat.",
        scene="on a chalk square with a drumbeat beat",
        plan="teamwork",
        closing="Soon the robot bowed and spun, and sharing turned the game to twice the fun.",
        tags={"robot", "sharing", "teamwork", "rhyme"},
    ),
}

TOOLS = {
    "sand_timer": Tool(
        id="sand_timer",
        label="sand timer",
        phrase="a little sand timer",
        supports={"turns"},
        cue="The sand slid softly from top to toe, a tiny grainy golden flow.",
        minute_based=True,
        rhythmic=False,
        tags={"timer", "minute"},
    ),
    "kitchen_timer": Tool(
        id="kitchen_timer",
        label="kitchen timer",
        phrase="a round kitchen timer",
        supports={"turns"},
        cue='It gave a neat tick-tick and a bright ding at the end, like a very patient friend.',
        minute_based=True,
        rhythmic=False,
        tags={"timer", "minute"},
    ),
    "role_cards": Tool(
        id="role_cards",
        label="role cards",
        phrase="two picture role cards",
        supports={"teamwork"},
        cue="One card showed winding, one card showed guiding, and the jobs fit together side by side.",
        minute_based=False,
        rhythmic=False,
        tags={"teamwork", "sharing"},
    ),
    "rhyme_cards": Tool(
        id="rhyme_cards",
        label="rhyme cards",
        phrase="a stack of rhyme cards",
        supports={"turns", "teamwork"},
        cue='Each card held a little line: "share and smile, and wait a while."',
        minute_based=False,
        rhythmic=True,
        tags={"rhyme", "sharing"},
    ),
}

HELPERS = {
    "mother": HelperCfg(
        id="mother",
        type="mother",
        warmth=2,
        line="Mom knelt low and spoke so slow, making room for each small feeling to show.",
        tags={"adult", "kindness"},
    ),
    "father": HelperCfg(
        id="father",
        type="father",
        warmth=2,
        line="Dad crouched near with a steady grin and made the busy room feel calm again.",
        tags={"adult", "kindness"},
    ),
    "teacher": HelperCfg(
        id="teacher",
        type="teacher_f",
        warmth=1,
        line="Their teacher folded her hands and said the fair way could be found before the game raced ahead.",
        tags={"adult", "kindness"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Tess", "Ruby", "Ava", "Ella", "June"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Owen", "Sam", "Leo", "Finn", "Max"]
SOFT_NAME_TRAITS = ["kind", "gentle", "tender", "thoughtful"]
OTHER_TRAITS = ["eager", "proud", "bouncy", "busy"]
WAITER_TRAITS = ["calm", "steady", "thoughtful", "cheerful", "hopeful"]


def require_key(name: str, key: str, registry: dict):
    if key not in registry:
        raise StoryError(f"(Unknown {name}: {key})")
    return registry[key]


def valid_combo(setting_id: str, challenge_id: str, tool_id: str) -> bool:
    if setting_id not in SETTINGS or challenge_id not in CHALLENGES or tool_id not in TOOLS:
        return False
    setting = SETTINGS[setting_id]
    challenge = CHALLENGES[challenge_id]
    tool = TOOLS[tool_id]
    return challenge_id in setting.affords and challenge.plan in tool.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for challenge_id in CHALLENGES:
            for tool_id in TOOLS:
                if valid_combo(setting_id, challenge_id, tool_id):
                    combos.append((setting_id, challenge_id, tool_id))
    return combos


def explain_rejection(setting_id: Optional[str], challenge_id: Optional[str], tool_id: Optional[str]) -> str:
    if challenge_id and setting_id and setting_id in SETTINGS and challenge_id in CHALLENGES:
        if challenge_id not in SETTINGS[setting_id].affords:
            return (
                f"(No story: {SETTINGS[setting_id].place} does not suit the "
                f"{challenge_id} game, so the children would not honestly play it there.)"
            )
    if challenge_id and tool_id and challenge_id in CHALLENGES and tool_id in TOOLS:
        challenge = CHALLENGES[challenge_id]
        tool = TOOLS[tool_id]
        if challenge.plan not in tool.supports:
            need = "one-minute turns" if challenge.plan == "turns" else "paired jobs"
            return (
                f"(No story: {tool.label} does not support the needed sharing plan. "
                f"This {challenge_id} setup needs {need}.)"
            )
    return "(No valid combination matches the given options.)"


def softness_score(trait: str) -> int:
    return 2 if trait in SOFT_TRAITS else 0


def patience_score(trait: str) -> int:
    return 1 if trait in PATIENT_TRAITS else 0


def tool_bonus(tool: Tool) -> int:
    if tool.minute_based:
        return 1
    if tool.rhythmic:
        return 1
    return 0


def outcome_of(params: StoryParams) -> str:
    tool = require_key("tool", params.tool, TOOLS)
    helper = require_key("helper", params.helper, HELPERS)
    challenge = require_key("challenge", params.challenge, CHALLENGES)
    soften = softness_score(params.sharer_trait) + helper.warmth + tool_bonus(tool)
    if challenge.plan == "teamwork":
        soften += patience_score(params.waiter_trait)
    return "quick_share" if soften >= 3 else "taught_share"


def introduce(world: World, sharer: Entity, waiter: Entity, helper: Entity, challenge: Challenge) -> None:
    world.say(
        f"In {world.setting.place}, bright with play, {sharer.id} and {waiter.id} found joy that day."
    )
    world.say(world.setting.detail)
    world.say(challenge.intro)
    world.say(
        f"{helper.label_word.capitalize()} was close enough to hear their feet and close enough to hear their little hearts beat."
    )


def delight(world: World, sharer: Entity, waiter: Entity, challenge: Challenge) -> None:
    for kid in (sharer, waiter):
        kid.memes["wonder"] += 1
    world.say(
        f"The toy could walk {challenge.scene}, and at once the game felt bright and new."
    )
    world.say(challenge.request)


def grab(world: World, sharer: Entity, waiter: Entity, toy: Entity) -> None:
    toy.attrs["holder"] = sharer.id
    toy.meters["wound"] += 1
    sharer.memes["mine"] += 1
    waiter.memes["want_turn"] += 1
    world.say(
        f'"Me first," said {sharer.id}, quick as a kite, and {sharer.pronoun()} hugged the robot close and tight.'
    )
    world.say(
        f'{waiter.id} reached with a hopeful hand. "Can I have a turn too?" {waiter.pronoun()} asked, trying to understand.'
    )
    propagate(world, narrate=False)
    if waiter.memes["sad"] >= THRESHOLD:
        world.say(
            f"But {waiter.id}'s smile slipped small and thin, and the room lost some of its sparkle and spin."
        )


def helper_steps_in(world: World, helper: Entity, tool: Tool, challenge: Challenge) -> None:
    world.say(HELPERS[helper.attrs["cfg"]].line)
    world.say(tool.cue)
    if challenge.plan == "turns" and tool.minute_based:
        world.say(
            f'"One minute for one, then one minute for two," {helper.pronoun()} said. "That is a fair and friendly thing to do."'
        )
    elif challenge.plan == "turns":
        world.say(
            f'"Pass the toy when the rhyme is through," {helper.pronoun()} said. "Fair hands make room for both of you."'
        )
    else:
        world.say(
            f'"This game works best when two friends share: one can do one job, and one can do a pair."'
        )


def soften_quickly(world: World, sharer: Entity, waiter: Entity, tool: Tool) -> None:
    sharer.memes["notice"] += 1
    world.say(
        f"{sharer.id} looked at {waiter.id}'s waiting face and felt a warm, important kind of grace."
    )
    if tool.minute_based:
        world.say(
            f'"All right," said {sharer.id}. "We can take a minute each, and then the fun can reach us both."'
        )
    else:
        world.say(
            f'"All right," said {sharer.id}. "We can share the game and keep the happy there."'
        )


def teach_kindness_rhyme(world: World, helper: Entity, sharer: Entity, waiter: Entity) -> None:
    helper.memes["guiding"] += 1
    world.say(
        f'{helper.label_word.capitalize()} tapped the floor and sang a tiny guide: "Kind hands share; kind hearts make room inside."'
    )
    world.say(
        f"{sharer.id} said the line once, then said it twice, and on the second time it sounded wise and nice."
    )
    world.say(
        f"{sharer.id} glanced at {waiter.id}, no longer keeping the whole game piled on one side."
    )


def start_turns(world: World, sharer: Entity, waiter: Entity, toy: Entity, tool: Tool, challenge: Challenge) -> None:
    world.facts["sharing_started"] = True
    world.facts["plan_kind"] = "turns"
    world.facts["tool_kind"] = tool.id
    if tool.minute_based:
        world.facts["turn_length"] = "minute"
        world.say(
            f"{sharer.id} wound Psycho for one minute while {waiter.id} watched the tiny feet go click-click on the floor."
        )
        world.say(
            f"Then the timer ended, the toy changed hands, and {waiter.id} got the next minute just as planned."
        )
    else:
        world.facts["turn_length"] = "rhyme"
        world.say(
            f"{sharer.id} held Psycho through one rhyme card, then passed the toy along with a careful, willing arm."
        )
        world.say(
            f"{waiter.id} read the next rhyme with a grin and sent the robot skittering back again."
        )
    toy.attrs["holder"] = "both"
    world.facts["turns_taken"] = 2
    propagate(world, narrate=False)
    world.say(challenge.closing)


def start_teamwork(world: World, sharer: Entity, waiter: Entity, toy: Entity, tool: Tool, challenge: Challenge) -> None:
    world.facts["sharing_started"] = True
    world.facts["plan_kind"] = "teamwork"
    world.facts["tool_kind"] = tool.id
    world.facts["jobs_assigned"] = True
    if challenge.id == "maze":
        world.say(
            f"{sharer.id} turned the key, and {waiter.id} pointed the path through the cardboard lanes."
        )
        world.say(
            f"Psycho bumped one flap, then found the right way through, because one child wound and one child knew what to do."
        )
    elif challenge.id == "dance":
        world.say(
            f"{sharer.id} wound Psycho, and {waiter.id} tapped the beat with cheerful feet."
        )
        world.say(
            f"The robot bowed and bobbed between them both, as if it liked a shared game most."
        )
    else:
        world.say(
            f"{sharer.id} did one part, and {waiter.id} did another, so the game grew bigger under both together."
        )
    toy.attrs["holder"] = "both"
    toy.meters["moving"] += 1
    propagate(world, narrate=False)
    world.say(challenge.closing)


def ending_image(world: World, sharer: Entity, waiter: Entity, helper: Entity, challenge: Challenge) -> None:
    if world.facts["plan_kind"] == "turns":
        world.say(
            f"Soon waiting did not sting or scare, because a fair small minute had taught them how to share."
        )
    else:
        world.say(
            f"Soon neither child needed all the glow, because shared jobs helped the whole game grow."
        )
    world.say(
        f"{helper.label_word.capitalize()} smiled to see it plain: kindness had made more room than grabbing ever gained."
    )
    world.say(
        f"And there in {world.setting.place}, with Psycho stepping brave and slow, {sharer.id} and {waiter.id} made the happy game both know."
    )


def tell(
    setting: Setting,
    challenge: Challenge,
    tool: Tool,
    helper_cfg: HelperCfg,
    sharer_name: str,
    sharer_gender: str,
    waiter_name: str,
    waiter_gender: str,
    sharer_trait: str,
    waiter_trait: str,
) -> World:
    world = World(setting=setting)
    sharer = world.add(
        Entity(
            id=sharer_name,
            kind="character",
            type=sharer_gender,
            label=sharer_name,
            role="sharer",
            traits=[sharer_trait],
            attrs={},
        )
    )
    waiter = world.add(
        Entity(
            id=waiter_name,
            kind="character",
            type=waiter_gender,
            label=waiter_name,
            role="waiter",
            traits=[waiter_trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_cfg.type,
            label="the helper",
            role="helper",
            traits=["warm"],
            attrs={"cfg": helper_cfg.id},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            kind="thing",
            type="robot",
            label="Psycho",
            role="toy",
            traits=["tin", "windup"],
            attrs={"holder": "", "printed_name": "Psycho"},
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            role="tool",
            attrs={},
        )
    )

    sharer.memes["possessive"] = float(POSSESSIVE_BASE)
    sharer.memes["kindness"] = float(softness_score(sharer_trait))
    waiter.memes["patience"] = float(patience_score(waiter_trait))
    helper.memes["warmth"] = float(helper_cfg.warmth)
    toy.meters["wound"] = 0.0
    toy.meters["moving"] = 0.0
    toy.meters["shared"] = 0.0
    tool_ent.meters["ready"] = 1.0

    world.facts.update(
        setting=setting,
        challenge=challenge,
        tool=tool,
        helper=helper,
        sharer=sharer,
        waiter=waiter,
        toy=toy,
        outcome="",
        printed_name=toy.attrs["printed_name"],
    )

    introduce(world, sharer, waiter, helper, challenge)
    delight(world, sharer, waiter, challenge)

    world.para()
    grab(world, sharer, waiter, toy)

    world.para()
    helper_steps_in(world, helper, tool, challenge)

    outcome = (
        "quick_share"
        if softness_score(sharer_trait) + helper_cfg.warmth + tool_bonus(tool)
        + (patience_score(waiter_trait) if challenge.plan == "teamwork" else 0) >= 3
        else "taught_share"
    )
    world.facts["outcome"] = outcome

    if outcome == "quick_share":
        soften_quickly(world, sharer, waiter, tool)
    else:
        teach_kindness_rhyme(world, helper, sharer, waiter)

    world.para()
    if challenge.plan == "turns":
        start_turns(world, sharer, waiter, toy, tool, challenge)
    else:
        start_teamwork(world, sharer, waiter, toy, tool, challenge)

    world.para()
    ending_image(world, sharer, waiter, helper, challenge)
    return world


KNOWLEDGE = {
    "robot": [
        (
            "What is a wind-up robot?",
            "A wind-up robot is a toy with a key or knob that you turn with your hand. After you wind it, it can move for a short time all by itself.",
        )
    ],
    "minute": [
        (
            "What is a minute?",
            "A minute is a short bit of time with sixty seconds in it. It is long enough for a little turn, but short enough that someone else can have a turn soon too.",
        )
    ],
    "timer": [
        (
            "What does a timer do?",
            "A timer helps people notice when a set amount of time is finished. That can make turn-taking feel fair, because everyone knows when it is time to switch.",
        )
    ],
    "sharing": [
        (
            "Why does sharing help a game?",
            "Sharing helps a game because more than one person gets to join the fun. It can also stop hurt feelings before they grow bigger.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to care about how someone else feels. It often means making room, helping gently, or taking turns so another person feels welcome too.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more people do different parts of one job together. A game can work better that way because each person helps in a useful way.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like share and care. Rhymes can make a rule or a little lesson easier to remember.",
        )
    ],
}
KNOWLEDGE_ORDER = ["robot", "minute", "timer", "sharing", "kindness", "teamwork", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    sharer = f["sharer"]
    waiter = f["waiter"]
    challenge = f["challenge"]
    tool = f["tool"]
    if challenge.plan == "turns":
        plan_bit = "one-minute turns"
    else:
        plan_bit = "shared jobs"
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the words "minute" and "psycho", and teaches kindness through sharing.',
        f"Tell a rhyming story where {sharer.id} and {waiter.id} both want a wind-up robot named Psycho, and a grown-up helps them use {plan_bit}.",
        f'Write a child-facing story in rhyme about one toy, two children, and a fair plan using {tool.label}, ending with the children happily sharing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sharer = f["sharer"]
    waiter = f["waiter"]
    challenge = f["challenge"]
    tool = f["tool"]
    helper = f["helper"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {sharer.id} and {waiter.id}, who both wanted to play with a little robot named Psycho. {helper.label_word.capitalize()} stayed nearby and helped them find a fair way to keep the game going.",
        ),
        (
            "What was the problem?",
            f"The problem was that both children wanted the same toy at the same time. {sharer.id} grabbed Psycho first, and that left {waiter.id} waiting and sad.",
        ),
    ]
    if challenge.plan == "turns":
        qa.append(
            (
                f"How did they solve the problem with the {tool.label}?",
                f"They used the {tool.label} to divide the play into fair turns. Each child got a chance, so the waiting stopped hurting and the game felt kinder again.",
            )
        )
    else:
        qa.append(
            (
                "How did they solve the problem by sharing jobs?",
                f"They turned one toy into a two-person game by splitting the jobs. One child helped Psycho move, and the other helped guide or keep the beat, so both children mattered in the same game.",
            )
        )
    if outcome == "quick_share":
        qa.append(
            (
                f"Why did {sharer.id} agree to share so quickly?",
                f"{sharer.id} noticed {waiter.id}'s face and understood that keeping the whole toy felt unkind. The helper's calm words and the clear plan made sharing feel easy instead of scary.",
            )
        )
    else:
        qa.append(
            (
                f"What helped {sharer.id} change from grabbing to sharing?",
                f"The helper taught a small kindness rhyme, and that gave {sharer.id} a better idea to hold onto. Saying the words out loud helped the fair choice feel real enough to do.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with both children enjoying Psycho together instead of pulling the game apart. The ending image shows that kindness made more room for fun, not less.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"robot", "sharing", "kindness"}
    challenge = world.facts["challenge"]
    tool = world.facts["tool"]
    tags |= set(challenge.tags)
    tags |= set(tool.tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k not in {'sharer', 'waiter', 'helper', 'tool', 'challenge', 'setting', 'toy'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="playroom",
        challenge="race",
        tool="sand_timer",
        helper="mother",
        sharer="Mina",
        sharer_gender="girl",
        waiter="Leo",
        waiter_gender="boy",
        sharer_trait="eager",
        waiter_trait="calm",
        seed=101,
    ),
    StoryParams(
        setting="reading_nook",
        challenge="maze",
        tool="role_cards",
        helper="teacher",
        sharer="Ruby",
        sharer_gender="girl",
        waiter="Milo",
        waiter_gender="boy",
        sharer_trait="thoughtful",
        waiter_trait="steady",
        seed=102,
    ),
    StoryParams(
        setting="porch",
        challenge="race",
        tool="rhyme_cards",
        helper="father",
        sharer="Finn",
        sharer_gender="boy",
        waiter="Nora",
        waiter_gender="girl",
        sharer_trait="proud",
        waiter_trait="hopeful",
        seed=103,
    ),
    StoryParams(
        setting="playroom",
        challenge="dance",
        tool="rhyme_cards",
        helper="mother",
        sharer="Ava",
        sharer_gender="girl",
        waiter="Theo",
        waiter_gender="boy",
        sharer_trait="gentle",
        waiter_trait="cheerful",
        seed=104,
    ),
    StoryParams(
        setting="reading_nook",
        challenge="dance",
        tool="role_cards",
        helper="teacher",
        sharer="Ben",
        sharer_gender="boy",
        waiter="June",
        waiter_gender="girl",
        sharer_trait="busy",
        waiter_trait="thoughtful",
        seed=105,
    ),
]


ASP_RULES = r"""
valid(S, C, T) :- affords(S, C), needs_plan(C, P), supports(T, P).

soft(Tr)    :- trait(Tr), soft_trait(Tr).
patient(Tr) :- wait_trait(Tr), patient_trait(Tr).

soft_points(2) :- trait(Tr), soft(Tr).
soft_points(0) :- trait(Tr), not soft(Tr).

patience_points(1) :- wait_trait(Tr), patient(Tr).
patience_points(0) :- wait_trait(Tr), not patient(Tr).

tool_points(1) :- chosen_tool(T), minute_based(T).
tool_points(1) :- chosen_tool(T), rhythmic(T), not minute_based(T).
tool_points(0) :- chosen_tool(T), not minute_based(T), not rhythmic(T).

team_bonus(1) :- chosen_challenge(C), needs_plan(C, teamwork), patience_points(1).
team_bonus(0) :- chosen_challenge(C), needs_plan(C, teamwork), patience_points(0).
team_bonus(0) :- chosen_challenge(C), needs_plan(C, turns).

score(SP + HP + TP + TB) :-
    soft_points(SP), chosen_helper(H), warmth(H, HP), tool_points(TP), team_bonus(TB).

outcome(quick_share) :- score(V), V >= 3.
outcome(taught_share) :- score(V), V < 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for challenge_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, challenge_id))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("needs_plan", challenge_id, challenge.plan))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for support in sorted(tool.supports):
            lines.append(asp.fact("supports", tool_id, support))
        if tool.minute_based:
            lines.append(asp.fact("minute_based", tool_id))
        if tool.rhythmic:
            lines.append(asp.fact("rhythmic", tool_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("warmth", helper_id, helper.warmth))
    for trait in sorted(SOFT_TRAITS):
        lines.append(asp.fact("soft_trait", trait))
    for trait in sorted(PATIENT_TRAITS):
        lines.append(asp.fact("patient_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_challenge", params.challenge),
            asp.fact("trait", params.sharer_trait),
            asp.fact("wait_trait", params.waiter_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "Psycho" not in sample.story or "minute" not in sample.story:
        raise StoryError("(Smoke test failed: story text was incomplete.)")
    if not sample.story_qa or not sample.world_qa or sample.world is None:
        raise StoryError("(Smoke test failed: QA or world payload missing.)")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke_test()
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming sharing storyworld: two children, one toy robot, and a fair plan."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.challenge and args.tool and not valid_combo(args.setting, args.challenge, args.tool):
        raise StoryError(explain_rejection(args.setting, args.challenge, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.setting, args.challenge, args.tool))

    setting_id, challenge_id, tool_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    sharer_gender = rng.choice(["girl", "boy"])
    waiter_gender = rng.choice(["girl", "boy"])
    sharer_name = pick_name(rng, sharer_gender)
    waiter_name = pick_name(rng, waiter_gender, avoid=sharer_name)
    sharer_trait = rng.choice(sorted(SOFT_NAME_TRAITS + OTHER_TRAITS))
    waiter_trait = rng.choice(sorted(WAITER_TRAITS))

    return StoryParams(
        setting=setting_id,
        challenge=challenge_id,
        tool=tool_id,
        helper=helper_id,
        sharer=sharer_name,
        sharer_gender=sharer_gender,
        waiter=waiter_name,
        waiter_gender=waiter_gender,
        sharer_trait=sharer_trait,
        waiter_trait=waiter_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.challenge, params.tool):
        raise StoryError(explain_rejection(params.setting, params.challenge, params.tool))
    setting = require_key("setting", params.setting, SETTINGS)
    challenge = require_key("challenge", params.challenge, CHALLENGES)
    tool = require_key("tool", params.tool, TOOLS)
    helper_cfg = require_key("helper", params.helper, HELPERS)

    world = tell(
        setting=setting,
        challenge=challenge,
        tool=tool,
        helper_cfg=helper_cfg,
        sharer_name=params.sharer,
        sharer_gender=params.sharer_gender,
        waiter_name=params.waiter,
        waiter_gender=params.waiter_gender,
        sharer_trait=params.sharer_trait,
        waiter_trait=params.waiter_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, challenge, tool) combos:\n")
        for setting_id, challenge_id, tool_id in combos:
            print(f"  {setting_id:12} {challenge_id:8} {tool_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sharer} & {p.waiter}: {p.challenge} at {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
