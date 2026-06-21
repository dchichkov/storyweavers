#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py
=========================================================================

A standalone story world for a warm-weather friendship tale: two children come
in hot from play, there is a fudgecicle problem, feelings get hurt, and a small
act of sharing repairs the moment.

This world is deliberately narrow. It models one tiny domain well instead of
covering many weak combinations:

- two friends after active play
- a cold treat need on a hot day
- a conflict over the fudgecicle supply
- a heartwarming repair by sharing in a sensible way

The world state, not frozen templates, determines the prose:
heat and tiredness make the treat matter, scarcity creates conflict, melting
adds urgency, and the chosen repair changes the ending image.

Run it
------
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/fudgecicle_conflict_friendship_heartwarming.py --verify
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
KIND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    cold_food: bool = False
    divisible: bool = False
    share_tool: bool = False
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
        return self.label or self.type
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
    play: str
    heat_line: str
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
class Need:
    id: str
    setup: str
    trace_word: str
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
class Supply:
    id: str
    count: int
    phrase: str
    scarce: bool
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
class Repair:
    id: str
    kindness: int
    needs_divisible: bool
    needs_tool: bool
    text: str
    qa_text: str
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
        return [e for e in self.entities.values() if e.role in {"starter", "friend"}]

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


def _r_scarcity_hurts(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("supply_count", 0) != 1:
        return out
    if world.facts.get("claimed_by") is None:
        return out
    claimer = world.get(world.facts["claimed_by"])
    other = world.get(world.facts["other_id"])
    sig = ("scarcity_hurts", claimer.id, other.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    claimer.memes["possessive"] += 1
    other.memes["left_out"] += 1
    other.memes["sad"] += 1
    for kid in world.kids():
        kid.memes["conflict"] += 1
    out.append("__conflict__")
    return out


def _r_melt(world: World) -> list[str]:
    out: list[str] = []
    treat = world.get("treat")
    if treat.meters["exposed"] < THRESHOLD:
        return out
    sig = ("melt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treat.meters["melting"] += 1
    for kid in world.kids():
        kid.memes["urgency"] += 1
    out.append("__melt__")
    return out


def _r_share_repairs(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("shared"):
        return out
    sig = ("share_repairs",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["conflict"] = 0.0
        kid.memes["sad"] = 0.0
        kid.memes["left_out"] = 0.0
        kid.memes["warmth"] += 1
        kid.memes["friendship"] += 1
    out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule(name="scarcity_hurts", tag="social", apply=_r_scarcity_hurts),
    Rule(name="melt", tag="physical", apply=_r_melt),
    Rule(name="share_repairs", tag="social", apply=_r_share_repairs),
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


def conflict_exists(supply: Supply) -> bool:
    return supply.scarce and supply.count == 1


def repair_possible(repair: Repair, treat_divisible: bool, tool_present: bool) -> bool:
    if repair.kindness < KIND_MIN:
        return False
    if repair.needs_divisible and not treat_divisible:
        return False
    if repair.needs_tool and not tool_present:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for need_id in NEEDS:
            for supply_id, supply in SUPPLIES.items():
                for repair_id, repair in REPAIRS.items():
                    if conflict_exists(supply) and repair_possible(
                        repair,
                        treat_divisible=True,
                        tool_present=True,
                    ):
                        combos.append((setting_id, need_id, supply_id, repair_id))
    return combos


def predict_feelings(world: World) -> dict:
    sim = world.copy()
    sim.facts["claimed_by"] = sim.facts["starter_id"]
    sim.facts["other_id"] = sim.facts["friend_id"]
    sim.get("treat").meters["exposed"] += 1
    propagate(sim, narrate=False)
    friend = sim.get(sim.facts["friend_id"])
    return {
        "sad": friend.memes["sad"] >= THRESHOLD,
        "melting": sim.get("treat").meters["melting"] >= THRESHOLD,
    }


def introduce(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    for kid in (a, b):
        kid.memes["playful"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} played {setting.play} at {setting.place}."
    )
    world.say(setting.heat_line)


def come_in_hot(world: World, a: Entity, b: Entity, need: Need) -> None:
    for kid in (a, b):
        kid.meters["hot"] += 1
        kid.meters["tired"] += 1
    world.facts["need_word"] = need.trace_word
    world.say(need.setup)


def find_treats(world: World, supply: Supply) -> None:
    world.facts["supply_count"] = supply.count
    world.say(
        f"In the freezer they found {supply.phrase}."
    )


def claim_last(world: World, a: Entity, b: Entity) -> None:
    world.facts["claimed_by"] = a.id
    world.facts["other_id"] = b.id
    treat = world.get("treat")
    treat.meters["exposed"] += 1
    a.memes["eager"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"There is only one fudgecicle," {a.id} said, reaching for it first. '
        f'"I saw it before you did."'
    )
    if b.memes["sad"] >= THRESHOLD:
        world.say(
            f"{b.id}'s smile fell. {b.pronoun().capitalize()} had been just as hot and tired."
        )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["stubborn"] += 1
    b.memes["hurt"] += 1
    world.say(
        f'"That is not fair," {b.id} said. "We both came in together."'
    )
    world.say(
        f"For a moment the room felt smaller than before, and the sweet cold treat did not feel sweet at all."
    )


def notice_melting(world: World, a: Entity, b: Entity) -> None:
    treat = world.get("treat")
    if treat.meters["melting"] >= THRESHOLD:
        treat.meters["dripping"] += 1
        a.memes["guilt"] += 1
        world.say(
            "A brown drop slid down the side of the fudgecicle and landed on the wrapper."
        )
        world.say(
            f"{a.id} looked at the drip, then at {b.id}'s face, and understood that the problem was bigger than who had grabbed first."
        )


def repair_share(world: World, a: Entity, b: Entity, repair: Repair) -> None:
    world.facts["shared"] = True
    a.memes["generous"] += 1
    a.memes["guilt"] = 0.0
    b.memes["hope"] += 1
    propagate(world, narrate=False)
    world.say(repair.text.format(a=a.id, b=b.id))
    world.say(
        "They leaned close so the drips would not fall, and the first cold bite made them both laugh a little."
    )


def ending(world: World, a: Entity, b: Entity, repair: Repair) -> None:
    world.say(
        repair.ending.format(a=a.id, b=b.id, ending_image=world.setting.ending_image)
    )


def tell(
    setting: Setting,
    need: Need,
    supply: Supply,
    repair: Repair,
    starter_name: str = "Lina",
    starter_gender: str = "girl",
    friend_name: str = "Owen",
    friend_gender: str = "boy",
    adult_type: str = "mother",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id=starter_name,
        kind="character",
        type=starter_gender,
        label=starter_name,
        role="starter",
        attrs={},
    ))
    b = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        attrs={},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the grown-up",
        role="adult",
        attrs={},
    ))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type="dessert",
        label="fudgecicle",
        cold_food=True,
        divisible=True,
        attrs={},
    ))
    tool = world.add(Entity(
        id="plate",
        kind="thing",
        type="plate",
        label="small plate",
        share_tool=True,
        attrs={},
    ))

    world.facts.update(
        starter_id=a.id,
        friend_id=b.id,
        adult=adult,
        supply_count=supply.count,
        shared=False,
        chosen_repair=repair.id,
    )
    treat.meters["frozen"] = 1.0
    tool.meters["ready"] = 1.0

    introduce(world, a, b, setting)
    come_in_hot(world, a, b, need)

    world.para()
    find_treats(world, supply)
    claim_last(world, a, b)
    argue(world, a, b)

    world.para()
    notice_melting(world, a, b)
    repair_share(world, a, b, repair)

    world.para()
    ending(world, a, b, repair)

    world.facts.update(
        starter=a,
        friend=b,
        setting=setting,
        need=need,
        supply=supply,
        repair=repair,
        treat=treat,
        tool=tool,
        outcome="shared" if world.facts["shared"] else "unrepaired",
        conflict=a.memes["conflict"] >= THRESHOLD or b.memes["conflict"] >= THRESHOLD,
        friendship_repaired=a.memes["friendship"] >= THRESHOLD and b.memes["friendship"] >= THRESHOLD,
        melting=treat.meters["melting"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "porch": Setting(
        id="porch",
        place="the shady front porch",
        play="chalk pictures and hopscotch",
        heat_line="Their cheeks were pink, their shoes were dusty, and the day still hummed with summer heat.",
        ending_image="the porch steps, with their bare feet swinging in the shade",
        tags={"summer", "porch"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the apartment courtyard",
        play="tag between the flower pots",
        heat_line="By the time they came in, the sun had made the backs of their necks warm and sticky.",
        ending_image="the cool hallway bench by the window",
        tags={"summer", "courtyard"},
    ),
    "yard": Setting(
        id="yard",
        place="the backyard under the maple tree",
        play="a long game of catch",
        heat_line="The grass smelled green and warm, and both children were breathing hard from play.",
        ending_image="the old wooden step under the maple shade",
        tags={"summer", "yard"},
    ),
}

NEEDS = {
    "cool_down": Need(
        id="cool_down",
        setup="At last they hurried inside for something cold, hoping the freezer might hold a little summer treasure.",
        trace_word="cool_down",
        tags={"heat"},
    ),
    "after_race": Need(
        id="after_race",
        setup="After racing each other all across the yard, they dashed in for something cold to calm their hot mouths and tired legs.",
        trace_word="after_race",
        tags={"heat", "race"},
    ),
    "after_helping": Need(
        id="after_helping",
        setup="They had worked hard carrying cushions and toy buckets back into place, and now both of them wanted the same chilly reward.",
        trace_word="after_helping",
        tags={"heat", "helping"},
    ),
}

SUPPLIES = {
    "last_one": Supply(
        id="last_one",
        count=1,
        phrase="just one fudgecicle tucked in the back behind the peas",
        scarce=True,
        tags={"scarce", "fudgecicle"},
    ),
}

REPAIRS = {
    "split_plate": Repair(
        id="split_plate",
        kindness=3,
        needs_divisible=True,
        needs_tool=True,
        text='"Wait," {a} said softly. "{b}, let us put it on the small plate and split the fudgecicle in half."',
        qa_text="They put the fudgecicle on a small plate and split it in half so both friends could have some.",
        ending="Soon {a} and {b} were shoulder to shoulder on {ending_image}, sharing the last bites and letting the hard feeling melt away.",
        tags={"sharing", "plate"},
    ),
    "break_two_sticks": Repair(
        id="break_two_sticks",
        kindness=2,
        needs_divisible=True,
        needs_tool=False,
        text='"Wait," {a} said softly. "{b}, I can break the fudgecicle across the middle, and we can each have a side."',
        qa_text="They carefully broke the fudgecicle into two parts so neither friend was left out.",
        ending="Soon {a} and {b} sat together on {ending_image}, licking chocolate from their fingers and smiling at each other again.",
        tags={"sharing"},
    ),
    "hide_it": Repair(
        id="hide_it",
        kindness=0,
        needs_divisible=False,
        needs_tool=False,
        text='',
        qa_text="",
        ending="",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ella", "Lucy", "Ava", "Ivy", "Zoe"]
BOY_NAMES = ["Owen", "Ben", "Noah", "Eli", "Sam", "Leo", "Finn", "Max"]


@dataclass
class StoryParams:
    setting: str
    need: str
    supply: str
    repair: str
    starter_name: str
    starter_gender: str
    friend_name: str
    friend_gender: str
    adult: str
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
    "fudgecicle": [(
        "What is a fudgecicle?",
        "A fudgecicle is a cold frozen treat with a chocolate flavor. People eat it to cool down on a warm day."
    )],
    "sharing": [(
        "Why can sharing help friends?",
        "Sharing can help because it shows that both people's feelings matter. When friends make room for each other, hurt feelings often soften."
    )],
    "summer": [(
        "Why do cold treats feel good on a hot day?",
        "Cold treats feel good because they cool your mouth and can make your body feel more comfortable for a little while. That is why they seem extra special after running and playing."
    )],
    "plate": [(
        "Why would someone use a plate to split a treat?",
        "A plate gives the food a clean place to rest while it is being divided. That makes sharing easier and helps keep drips from falling on the floor."
    )],
}
KNOWLEDGE_ORDER = ["fudgecicle", "summer", "sharing", "plate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["starter"]
    b = f["friend"]
    setting = f["setting"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the word "fudgecicle" and shows a friendship conflict gently being repaired.',
        f"Tell a warm summer story where {a.id} and {b.id} come in hot from play at {setting.place}, argue over the last fudgecicle, and find a kind way to share.",
        "Write a simple story about two friends who almost let a small dessert problem turn into a big hurt feeling, but choose friendship in the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["starter"]
    b = f["friend"]
    supply = f["supply"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}. They had been playing together on a hot day before the fudgecicle trouble began."
        ),
        (
            "Why did the children go to the freezer?",
            "They went looking for something cold because they were hot and tired from playing. The heat is what made the treat feel important to both of them."
        ),
        (
            "What caused the conflict?",
            f"The conflict started because there was only {supply.count} fudgecicle left, and both friends wanted it. When {a.id} reached for it first, {b.id} felt left out and hurt."
        ),
    ]
    if f.get("melting"):
        qa.append((
            "What made the argument change?",
            f"The fudgecicle started to melt while they were upset, and that helped {a.id} stop and think. Seeing the drip made the moment feel less like winning and more like taking care of each other."
        ))
    qa.append((
        "How did they solve the problem?",
        f"{repair.qa_text} That repaired the friendship because both children were included instead of one child being left out."
    ))
    qa.append((
        "How did the story end?",
        f"It ended with {a.id} and {b.id} sitting close together and enjoying the treat as friends again. The peaceful ending image shows that the hard feeling had melted away."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"fudgecicle", "sharing"} | set(f["setting"].tags) | set(f["repair"].tags)
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
        flags = [n for n, on in (("cold_food", e.cold_food), ("divisible", e.divisible), ("share_tool", e.share_tool)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k not in {'starter', 'friend', 'adult', 'setting', 'need', 'supply', 'repair', 'treat', 'tool'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="porch",
        need="cool_down",
        supply="last_one",
        repair="split_plate",
        starter_name="Lina",
        starter_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        adult="mother",
    ),
    StoryParams(
        setting="courtyard",
        need="after_race",
        supply="last_one",
        repair="break_two_sticks",
        starter_name="Maya",
        starter_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        adult="father",
    ),
    StoryParams(
        setting="yard",
        need="after_helping",
        supply="last_one",
        repair="split_plate",
        starter_name="Leo",
        starter_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        adult="mother",
    ),
]


def explain_supply(supply: Supply) -> str:
    return (
        f"(No story: {supply.phrase} does not create a real friendship conflict here. "
        f"This world needs exactly one fudgecicle so both children want the same treat.)"
    )


def explain_repair(repair: Repair) -> str:
    if repair.kindness < KIND_MIN:
        return (
            f"(Refusing repair '{repair.id}': it is too unkind for this heartwarming friendship world. "
            f"Choose a sharing repair like split_plate or break_two_sticks.)"
        )
    return (
        f"(No story: repair '{repair.id}' does not fit the physical setup needed to share one fudgecicle.)"
    )


ASP_RULES = r"""
conflict_supply(S) :- supply(S), count(S,1), scarce(S).
kind_repair(R) :- repair(R), kindness(R,K), kind_min(M), K >= M.
repair_possible(R) :- kind_repair(R), needs_divisible(R,0), needs_tool(R,0).
repair_possible(R) :- kind_repair(R), needs_divisible(R,1), treat_divisible, needs_tool(R,0).
repair_possible(R) :- kind_repair(R), needs_divisible(R,1), treat_divisible, needs_tool(R,1), tool_present.
valid(St,N,S,R) :- setting(St), need(N), conflict_supply(S), repair_possible(R).

outcome(shared) :- chosen_supply(S), conflict_supply(S), chosen_repair(R), repair_possible(R).
:- chosen_supply(S), not conflict_supply(S).
:- chosen_repair(R), not repair_possible(R).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for sid, supply in SUPPLIES.items():
        lines.append(asp.fact("supply", sid))
        lines.append(asp.fact("count", sid, supply.count))
        if supply.scarce:
            lines.append(asp.fact("scarce", sid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("kindness", rid, repair.kindness))
        lines.append(asp.fact("needs_divisible", rid, 1 if repair.needs_divisible else 0))
        lines.append(asp.fact("needs_tool", rid, 1 if repair.needs_tool else 0))
    lines.append(asp.fact("kind_min", KIND_MIN))
    lines.append(asp.fact("treat_divisible"))
    lines.append(asp.fact("tool_present"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_supply", params.supply),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    supply = SUPPLIES[params.supply]
    repair = REPAIRS[params.repair]
    if conflict_exists(supply) and repair_possible(repair, treat_divisible=True, tool_present=True):
        return "shared"
    return "?"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a friendship conflict over the last fudgecicle, repaired by sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--supply", choices=SUPPLIES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.supply:
        supply = SUPPLIES[args.supply]
        if not conflict_exists(supply):
            raise StoryError(explain_supply(supply))
    if args.repair:
        repair = REPAIRS[args.repair]
        if not repair_possible(repair, treat_divisible=True, tool_present=True):
            raise StoryError(explain_repair(repair))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.need is None or c[1] == args.need)
        and (args.supply is None or c[2] == args.supply)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, need, supply, repair = rng.choice(sorted(combos))
    starter_name, starter_gender = _pick_kid(rng)
    friend_name, friend_gender = _pick_kid(rng, avoid=starter_name)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        need=need,
        supply=supply,
        repair=repair,
        starter_name=starter_name,
        starter_gender=starter_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        need = NEEDS[params.need]
        supply = SUPPLIES[params.supply]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err.args[0]})") from None

    if not conflict_exists(supply):
        raise StoryError(explain_supply(supply))
    if not repair_possible(repair, treat_divisible=True, tool_present=True):
        raise StoryError(explain_repair(repair))

    world = tell(
        setting=setting,
        need=need,
        supply=supply,
        repair=repair,
        starter_name=params.starter_name,
        starter_gender=params.starter_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
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
        print(f"{len(combos)} compatible (setting, need, supply, repair) combos:\n")
        for setting, need, supply, repair in combos:
            print(f"  {setting:10} {need:13} {supply:10} {repair}")
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
            header = f"### {p.starter_name} & {p.friend_name}: {p.setting}, {p.need}, {p.repair}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
