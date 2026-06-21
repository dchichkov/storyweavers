#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py
========================================================================

A standalone story world for a tiny pirate-tale domain: two children play at
being river pirates on a quest, pause to help someone in trouble, and discover
that kindness helps them travel further than hurry ever could.

The core constraint is simple and physical: each kind of trouble needs the right
kind of help. A rope can tow a stuck boat, a knife can cut a tangled net, and a
push-pole can free something snarled in reeds. The world refuses mismatched
choices because the moral turn must also be plausible in the physical world.

Run it
------
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py --quest medicine --encounter rowboat_mud --tool towrope
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py --encounter turtle_net --tool pushpole
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/barge_further_moral_value_quest_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
class Quest:
    id: str
    cargo: str
    phrase: str
    need_line: str
    place: str
    closing_gift: str
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
class Encounter:
    id: str
    who: str
    kind: str
    trouble: str
    trouble_line: str
    needs: str
    rescue_text: str
    gratitude_text: str
    return_help: str
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
    article: str
    action: str
    use_text: str
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


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.meters["freed"] < THRESHOLD:
        return out
    sig = ("gratitude", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["gratitude"] += 1
    world.facts["helper_ready"] = True
    out.append("__gratitude__")
    return out


def _r_repay(world: World) -> list[str]:
    out: list[str] = []
    barge = world.get("barge")
    helper = world.get("helper")
    if barge.meters["stalled"] < THRESHOLD or helper.memes["gratitude"] < THRESHOLD:
        return out
    sig = ("repay", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    barge.meters["stalled"] = 0.0
    barge.meters["progress"] += 2.0
    barge.meters["helped_forward"] += 1.0
    helper.memes["loyalty"] += 1.0
    out.append("__repay__")
    return out


CAUSAL_RULES = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="repay", tag="physical", apply=_r_repay),
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


def compatible(encounter: Encounter, tool: Tool) -> bool:
    return encounter.needs == tool.action


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid in QUESTS:
        for eid, enc in ENCOUNTERS.items():
            for tid, tool in TOOLS.items():
                if compatible(enc, tool):
                    combos.append((qid, eid, tid))
    return combos


def explain_rejection(encounter: Encounter, tool: Tool) -> str:
    return (
        f"(No story: {encounter.who} is {encounter.trouble}, so the scene needs "
        f"something that can {encounter.needs}. {tool.article.capitalize()} {tool.label} "
        f"cannot honestly do that.)"
    )


def predict_delay(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    barge = sim.get("barge")
    helper.meters["freed"] += 1.0
    propagate(sim, narrate=False)
    barge.meters["stalled"] += 1.0
    propagate(sim, narrate=False)
    return {
        "goes_further": barge.meters["progress"] >= 2.0,
        "helper_ready": bool(sim.facts.get("helper_ready")),
    }


def setup_play(world: World, captain: Entity, mate: Entity, quest: Quest) -> None:
    captain.memes["joy"] += 1.0
    mate.memes["joy"] += 1.0
    world.say(
        f"On a silver-blue afternoon, {captain.id} and {mate.id} turned the riverbank "
        f"into pirate country. A flat wooden barge became their proud pirate ship, "
        f"a broom handle became a mast, and a knotted scarf became their fluttering flag."
    )
    world.say(
        f'"Captain {captain.id} and Mate {mate.id}!" {captain.id} cried. '
        f'"We have a quest to carry {quest.phrase} to {quest.place} before dusk."'
    )


def launch(world: World, captain: Entity, mate: Entity, quest: Quest, elder: Entity) -> None:
    world.say(
        f"They pushed the barge away from the reeds and drifted out on the slow river. "
        f"{elder.label_word.capitalize()} was waiting at {quest.place}, and {quest.need_line}"
    )
    world.get("barge").meters["progress"] += 1.0
    world.facts["goal_place"] = quest.place


def spot_trouble(world: World, captain: Entity, mate: Entity, encounter: Encounter) -> None:
    helper = world.get("helper")
    helper.meters["trapped"] = 1.0
    captain.memes["hurry"] += 1.0
    mate.memes["care"] += 1.0
    world.say(
        f"Then {mate.id} pointed toward the bend in the river. There, beside the rushes, "
        f"{encounter.trouble_line}"
    )
    world.say(
        f'"If we stop now, we may never get further before dusk," said {captain.id}.'
    )


def choose_kindness(world: World, captain: Entity, mate: Entity, encounter: Encounter) -> None:
    pred = predict_delay(world)
    world.facts["predicted_further"] = pred["goes_further"]
    world.say(
        f'{mate.id} shook {mate.pronoun("possessive")} head. "A real pirate quest is not just '
        f'about getting there first," {mate.pronoun()} said. "It is about helping when someone needs us."'
    )
    if pred["helper_ready"]:
        world.say(
            f"For one quiet moment, even {captain.id} could imagine that kindness might carry the barge further than hurry."
        )


def rescue(world: World, captain: Entity, mate: Entity, encounter: Encounter, tool: Tool) -> None:
    helper = world.get("helper")
    helper.meters["trapped"] = 0.0
    helper.meters["freed"] += 1.0
    captain.memes["kindness"] += 1.0
    mate.memes["kindness"] += 1.0
    world.say(
        f"So the two young pirates steered close, and {captain.id} reached for {tool.article} {tool.label}. "
        f"{tool.use_text} {encounter.rescue_text}"
    )
    propagate(world, narrate=False)
    world.say(encounter.gratitude_text)
    world.facts["rescued_with"] = tool.label


def stall(world: World, captain: Entity, mate: Entity) -> None:
    barge = world.get("barge")
    barge.meters["stalled"] += 1.0
    captain.memes["worry"] += 1.0
    mate.memes["worry"] += 1.0
    world.say(
        f"A little farther on, the river widened and the wind turned stubborn. The barge shivered, "
        f"nudged sideways, and stuck in a sleepy patch of reeds."
    )
    propagate(world, narrate=False)


def repay(world: World, encounter: Encounter) -> None:
    barge = world.get("barge")
    if barge.meters["helped_forward"] >= THRESHOLD:
        world.say(encounter.return_help)
        world.facts["repaid"] = True
    else:
        world.facts["repaid"] = False


def arrive(world: World, captain: Entity, mate: Entity, quest: Quest, elder: Entity) -> None:
    captain.memes["relief"] += 1.0
    mate.memes["relief"] += 1.0
    captain.memes["pride"] += 1.0
    mate.memes["pride"] += 1.0
    elder.memes["gratitude"] += 1.0
    world.say(
        f"Soon the barge slid free and glided to {quest.place}. {elder.label_word.capitalize()} was there on the dock, "
        f"smiling with both hands held out for {quest.cargo}."
    )
    world.say(
        f'"You finished the quest," {elder.label_word} said, "and you brought kind hearts with you too."'
    )
    world.say(
        f"That evening, {quest.closing_gift}. The river looked golden, the little barge rocked softly, "
        f"and the young pirates knew the world felt brighter when they helped along the way."
    )


def tell(
    quest: Quest,
    encounter: Encounter,
    tool: Tool,
    captain_name: str = "Tess",
    captain_gender: str = "girl",
    mate_name: str = "Ben",
    mate_gender: str = "boy",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    captain = world.add(
        Entity(
            id=captain_name,
            kind="character",
            type=captain_gender,
            role="captain",
            traits=["bold"],
        )
    )
    mate = world.add(
        Entity(
            id=mate_name,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=["kind"],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="receiver",
            label="the elder",
        )
    )
    world.add(Entity(id="barge", type="barge", label="barge"))
    world.add(Entity(id="cargo", type="cargo", label=quest.cargo))
    world.add(
        Entity(
            id="helper",
            kind="character" if encounter.kind == "child" else "thing",
            type=encounter.kind,
            label=encounter.who,
            role="stranded",
        )
    )

    world.facts.update(
        quest=quest,
        encounter=encounter,
        tool=tool,
        captain=captain,
        mate=mate,
        elder=elder,
        helper_ready=False,
        repaid=False,
    )

    setup_play(world, captain, mate, quest)
    launch(world, captain, mate, quest, elder)

    world.para()
    spot_trouble(world, captain, mate, encounter)
    choose_kindness(world, captain, mate, encounter)
    rescue(world, captain, mate, encounter, tool)

    world.para()
    stall(world, captain, mate)
    repay(world, encounter)
    arrive(world, captain, mate, quest, elder)
    return world


QUESTS = {
    "medicine": Quest(
        id="medicine",
        cargo="the jar of willow-bark medicine",
        phrase="a jar of willow-bark medicine",
        need_line="the old fisher on the island had a fever and needed it before night",
        place="Lantern Island",
        closing_gift="grandma poured them mint tea and cut thick slices of honey bread",
        tags={"medicine", "kindness", "quest", "island"},
    ),
    "bread": Quest(
        id="bread",
        cargo="the warm round loaf",
        phrase="a warm round loaf of bread",
        need_line="the lightkeeper had been alone all day and supper would be late without it",
        place="Driftwood Dock",
        closing_gift="grandpa split the loaf, added blackberry jam, and let them eat on the dock",
        tags={"bread", "kindness", "quest", "island"},
    ),
    "oil": Quest(
        id="oil",
        cargo="the tin of lantern oil",
        phrase="a tin of lantern oil",
        need_line="the little island lantern would go dark without it",
        place="Pebble Point",
        closing_gift="the keeper lit the lantern, and its warm glow made their flag shine like treasure",
        tags={"lantern", "kindness", "quest", "island"},
    ),
}

ENCOUNTERS = {
    "turtle_net": Encounter(
        id="turtle_net",
        who="a young river turtle",
        kind="turtle",
        trouble="caught in an old fishing net",
        trouble_line="a young river turtle was caught in an old fishing net, kicking and twisting in the shallows.",
        needs="cut",
        rescue_text="With careful fingers, they sawed through the wet cords until the last loop fell away.",
        gratitude_text="The little turtle blinked, bobbed once, and slipped into the water with a grateful splash.",
        return_help="Ahead of them, the turtle swam through the deep channel between the reeds, and the children followed its ripples until the barge slid free and went further downstream.",
        tags={"turtle", "kindness", "net", "river"},
    ),
    "rowboat_mud": Encounter(
        id="rowboat_mud",
        who="a little fisher child",
        kind="child",
        trouble="stuck fast in the mud",
        trouble_line="a little fisher child was pulling at a rowboat that had sunk nose-first into thick brown mud.",
        needs="tow",
        rescue_text="Together they made the rope fast, leaned back with all their might, and the rowboat slurped free from the mud.",
        gratitude_text="The child laughed in relief and waved both arms. \"Thank you, pirates!\"",
        return_help="When the barge stuck, the fisher child ran along the bank, caught the line they tossed, and pulled until the flat boat slid free and could travel further.",
        tags={"boat", "rope", "kindness", "river"},
    ),
    "heron_reeds": Encounter(
        id="heron_reeds",
        who="a gray heron",
        kind="bird",
        trouble="snarled among the reeds",
        trouble_line="a gray heron had tangled one long leg in the reeds and could not step back into open water.",
        needs="push",
        rescue_text="Using the pole gently, they pressed the thick reeds aside and opened a safe path.",
        gratitude_text="The heron shook out its wings, gave one solemn flap, and stalked back into the river's bright edge.",
        return_help="Later the heron rose into the air, circled once, and glided above the open waterway; the children steered beneath it, and the barge found the clear path further on.",
        tags={"bird", "reeds", "kindness", "river"},
    ),
}

TOOLS = {
    "knife": Tool(
        id="knife",
        label="river knife",
        article="a",
        action="cut",
        use_text="",
        tags={"knife", "tool"},
    ),
    "towrope": Tool(
        id="towrope",
        label="towrope",
        article="a",
        action="tow",
        use_text="",
        tags={"rope", "tool"},
    ),
    "pushpole": Tool(
        id="pushpole",
        label="push-pole",
        article="a",
        action="push",
        use_text="",
        tags={"pole", "tool"},
    ),
}

GIRL_NAMES = ["Tess", "Mira", "Lila", "Nora", "Ava", "June", "Poppy", "Rosa"]
BOY_NAMES = ["Ben", "Finn", "Leo", "Sam", "Theo", "Eli", "Jack", "Max"]


@dataclass
class StoryParams:
    quest: str
    encounter: str
    tool: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    elder_type: str
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
    "barge": [
        (
            "What is a barge?",
            "A barge is a wide, flat boat made to carry things on calm water. It moves slowly, but it can hold heavy cargo.",
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a purpose. Someone sets out to do an important job and keeps going until it is done.",
        )
    ],
    "kindness": [
        (
            "Why is kindness important on a journey?",
            "Kindness helps other people when they are in trouble. It also builds trust, so help often comes back when you need it.",
        )
    ],
    "medicine": [
        (
            "What is medicine for?",
            "Medicine is used to help a sick person feel better. It should be brought carefully and on time.",
        )
    ],
    "bread": [
        (
            "Why do people share bread?",
            "Bread is food, and sharing food is a caring thing to do. It helps everyone feel welcome and cared for.",
        )
    ],
    "lantern": [
        (
            "Why does a lantern need oil?",
            "A lantern needs fuel so its light can keep burning. Without oil, the lamp can go dark.",
        )
    ],
    "turtle": [
        (
            "Why is an old net dangerous for a turtle?",
            "A net can wrap around a turtle's body or flippers and stop it from swimming. Then the turtle cannot move safely.",
        )
    ],
    "rope": [
        (
            "What is a rope good for on a boat?",
            "A rope can tie, pull, or hold things steady. On the water, it helps boats tow or rescue safely.",
        )
    ],
    "pole": [
        (
            "What does a push-pole do?",
            "A push-pole helps a boat move in shallow water or through reeds. You press it against the ground or plants to guide the boat.",
        )
    ],
    "knife": [
        (
            "Why must a knife be used carefully?",
            "A knife is a tool for cutting. Because it is sharp, only careful hands should use it for a real job.",
        )
    ],
    "island": [
        (
            "What is an island?",
            "An island is a piece of land with water all around it. You usually need a boat or a bridge to reach it.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "barge",
    "quest",
    "kindness",
    "medicine",
    "bread",
    "lantern",
    "turtle",
    "rope",
    "pole",
    "knife",
    "island",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    enc = f["encounter"]
    captain = f["captain"]
    mate = f["mate"]
    return [
        (
            f'Write a pirate tale for a 3-to-5-year-old that includes the words "barge" '
            f'and "further" and is about a kind quest on a river.'
        ),
        (
            f"Tell a gentle pirate story where {captain.id} and {mate.id} are carrying "
            f"{quest.cargo} on a barge, stop to help {enc.who}, and discover that kindness helps them travel further."
        ),
        (
            f"Write a quest story with a clear moral value: two child pirates are in a hurry, but helping someone beside the river becomes the very thing that saves their voyage."
        ),
    ]


def pair_noun(captain: Entity, mate: Entity) -> str:
    if captain.type == "girl" and mate.type == "girl":
        return "two young pirate girls"
    if captain.type == "boy" and mate.type == "boy":
        return "two young pirate boys"
    return "two young pirates"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    elder = f["elder"]
    quest = f["quest"]
    enc = f["encounter"]
    tool = f["tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, mate)}, {captain.id} and {mate.id}, on a river quest. They are trying to bring {quest.cargo} to {quest.place}.",
        ),
        (
            "What was their quest?",
            f"Their quest was to carry {quest.cargo} by barge to {quest.place} before dusk. Someone there needed it, so the trip mattered from the start.",
        ),
        (
            f"Why did {captain.id} want to keep going instead of stopping?",
            f"{captain.id} was afraid they would not get further before dusk if they paused. The hurry came from wanting to finish the quest on time.",
        ),
        (
            "What trouble did they find by the river?",
            f"They found {enc.who} {enc.trouble}. That changed the trip, because the children had to choose between speed and kindness.",
        ),
        (
            f"How did they help?",
            f"They used {tool.article} {tool.label} because that tool could {tool.action} in the right way for the problem. Their help worked, so the trapped one was freed instead of being left behind.",
        ),
    ]
    if f.get("repaid"):
        qa.append(
            (
                "How did helping make the trip go better later?",
                f"Later the barge stuck in reeds, but the one they had rescued helped them find or pull the clear way through. So kindness did not only help at the river bend; it helped them travel further and finish the quest.",
            )
        )
    qa.append(
        (
            "What did they learn at the end?",
            f"They learned that a real quest is not only about being first. It is also about caring for others, and that caring can guide you farther than hurry.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They reached {quest.place} with {quest.cargo}, and {elder.label_word} praised their kind hearts. The ending shows that they finished the job and changed inside too.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"barge", "quest", "kindness", "island"} | set(f["quest"].tags) | set(f["encounter"].tags) | set(f["tool"].tags)
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="medicine",
        encounter="turtle_net",
        tool="knife",
        captain="Tess",
        captain_gender="girl",
        mate="Ben",
        mate_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="bread",
        encounter="rowboat_mud",
        tool="towrope",
        captain="Finn",
        captain_gender="boy",
        mate="Mira",
        mate_gender="girl",
        elder_type="grandfather",
    ),
    StoryParams(
        quest="oil",
        encounter="heron_reeds",
        tool="pushpole",
        captain="Nora",
        captain_gender="girl",
        mate="Sam",
        mate_gender="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        quest="medicine",
        encounter="rowboat_mud",
        tool="towrope",
        captain="June",
        captain_gender="girl",
        mate="Leo",
        mate_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="bread",
        encounter="turtle_net",
        tool="knife",
        captain="Max",
        captain_gender="boy",
        mate="Poppy",
        mate_gender="girl",
        elder_type="grandfather",
    ),
]


ASP_RULES = r"""
needs(E, A) :- encounter(E), encounter_needs(E, A).
works(T, E) :- tool(T), needs(E, A), tool_action(T, A).
valid(Q, E, T) :- quest(Q), encounter(E), tool(T), works(T, E).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for eid, enc in ENCOUNTERS.items():
        lines.append(asp.fact("encounter", eid))
        lines.append(asp.fact("encounter_needs", eid, enc.needs))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_action", tid, tool.action))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke generation and emit succeeded.")
    except Exception as exc:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: child pirates on a barge learn that kindness helps a quest go further."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--encounter", choices=ENCOUNTERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.encounter and args.tool:
        enc = ENCOUNTERS[args.encounter]
        tool = TOOLS[args.tool]
        if not compatible(enc, tool):
            raise StoryError(explain_rejection(enc, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.encounter is None or combo[1] == args.encounter)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, encounter, tool = rng.choice(sorted(combos))
    captain_gender = rng.choice(["girl", "boy"])
    mate_gender = rng.choice(["girl", "boy"])
    captain = _pick_name(rng, captain_gender)
    mate = _pick_name(rng, mate_gender, avoid=captain)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    return StoryParams(
        quest=quest,
        encounter=encounter,
        tool=tool,
        captain=captain,
        captain_gender=captain_gender,
        mate=mate,
        mate_gender=mate_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.encounter not in ENCOUNTERS:
        raise StoryError(f"(Unknown encounter: {params.encounter})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.elder_type not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")

    quest = QUESTS[params.quest]
    encounter = ENCOUNTERS[params.encounter]
    tool = TOOLS[params.tool]
    if not compatible(encounter, tool):
        raise StoryError(explain_rejection(encounter, tool))

    world = tell(
        quest=quest,
        encounter=encounter,
        tool=tool,
        captain_name=params.captain,
        captain_gender=params.captain_gender,
        mate_name=params.mate,
        mate_gender=params.mate_gender,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (quest, encounter, tool) combos:\n")
        for quest, encounter, tool in combos:
            print(f"  {quest:9} {encounter:12} {tool}")
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
            header = f"### {p.captain} & {p.mate}: {p.quest} / {p.encounter} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
