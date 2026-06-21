#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py
=======================================================

A standalone story world for a small child-facing mystery with a happy ending:
on a quiet morn, a child finds a shiny familiar object missing, follows clues,
and discovers that a crow has borrowed it for a nest. A gentle helper solves
the mystery kindly, and the story ends with the lost thing safely home again.

Run it
------
    python storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py
    python storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py --scene porch --item bell
    python storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py --response throw_stick
    python storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py --all --qa
    python storyworlds/worlds/gpt-5.4/morn_happy_ending_mystery.py --verify
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
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
class Scene:
    id: str
    label: str
    opening: str
    spot_phrase: str
    search_line: str
    affords: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    shine: bool = True
    portable: bool = True
    ring_text: str = ""
    home_ending: str = ""
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
class Perch:
    id: str
    label: str
    where_line: str
    height: int
    nest_line: str
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
class Response:
    id: str
    sense: int
    reach: int
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
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "feather_found": False,
            "caw_heard": False,
            "perch_spotted": False,
            "solved": False,
            "kindly": False,
            "culprit": "crow",
            "response_reach": 0,
            "perch_height": 0,
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

    def copy(self) -> "World":
        clone = World(self.scene)
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


def _r_missing_stirs(world: World) -> list[str]:
    child = world.get("child")
    item = world.get("item")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_stirs", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    return []


def _r_crow_clues(world: World) -> list[str]:
    crow = world.get("crow")
    if crow.meters["took_item"] < THRESHOLD:
        return []
    sig = ("crow_clues", crow.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["feather_found"] = True
    world.facts["caw_heard"] = True
    child = world.get("child")
    child.memes["focus"] += 1
    return []


def _r_recover_item(world: World) -> list[str]:
    helper = world.get("helper")
    item = world.get("item")
    child = world.get("child")
    if helper.meters["trying"] < THRESHOLD:
        return []
    if not world.facts.get("perch_spotted"):
        return []
    if item.meters["missing"] < THRESHOLD:
        return []
    if world.facts.get("response_reach", 0) < world.facts.get("perch_height", 0):
        return []
    sig = ("recover_item", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    helper.memes["care"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.facts["solved"] = True
    world.facts["kindly"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_stirs", tag="emotional", apply=_r_missing_stirs),
    Rule(name="crow_clues", tag="mystery", apply=_r_crow_clues),
    Rule(name="recover_item", tag="resolution", apply=_r_recover_item),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def item_can_be_taken(item: MissingItem) -> bool:
    return item.shine and item.portable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def can_reach(response: Response, perch: Perch) -> bool:
    return response.reach >= perch.height


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, scene in SCENES.items():
        for iid, item in ITEMS.items():
            if not item_can_be_taken(item):
                continue
            for pid, perch in PERCHES.items():
                if pid in scene.affords:
                    combos.append((sid, iid, pid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    response = RESPONSES[params.response]
    perch = PERCHES[params.perch]
    return "solved" if response.sense >= SENSE_MIN and can_reach(response, perch) else "stuck"


def explain_item(item: MissingItem) -> str:
    if not item.shine:
        return (
            f"(No story: {item.phrase} is not shiny enough for this crow mystery. "
            f"The world only supports objects a crow would honestly notice and borrow.)"
        )
    if not item.portable:
        return (
            f"(No story: {item.phrase} is too big or awkward for a crow to carry. "
            f"Pick a small shiny object instead.)"
        )
    return "(No story: this object does not fit the crow mystery.)"


def explain_response(response: Response, perch: Perch) -> str:
    if response.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_responses()))
        return (
            f"(Refusing response '{response.id}': it is too rough or foolish for a "
            f"gentle happy-ending mystery. Try one of: {better}.)"
        )
    return (
        f"(No story: '{response.id}' cannot reach {perch.label}. "
        f"The helper needs a method tall enough to get the lost object back kindly.)"
    )


def predict_solution(world: World, response: Response, perch: Perch) -> dict:
    sim = world.copy()
    sim.facts["response_reach"] = response.reach
    sim.facts["perch_height"] = perch.height
    sim.facts["perch_spotted"] = True
    sim.get("helper").meters["trying"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": sim.facts["solved"],
        "reachable": response.reach >= perch.height,
    }


def introduce(world: World, child: Entity, helper: Entity, item: MissingItem) -> None:
    world.say(
        f"On a soft gray morn, {child.id} stepped into {world.scene.label} with "
        f"{helper.label_word} and stopped at once."
    )
    world.say(world.scene.opening)
    world.say(
        f"But {item.phrase} that usually rested {world.scene.spot_phrase} was gone."
    )


def notice_loss(world: World, child: Entity, item: MissingItem) -> None:
    if child.memes["curiosity"] >= THRESHOLD:
        world.say(
            f"{child.id} looked under the mat, behind the flowerpot, and along the step. "
            f"The empty place made the whole morning feel like a tiny mystery."
        )
    world.say(f'"My {item.label} is missing," {child.id} whispered.')


def inspect_clues(world: World, child: Entity, helper: Entity) -> None:
    feather = "a glossy black feather on the rail" if world.facts["feather_found"] else "nothing strange at all"
    caw = "a scratchy caw from above" if world.facts["caw_heard"] else "only the wind"
    world.say(
        f"{helper.label_word.capitalize()} did not laugh. Together they noticed {feather} "
        f"and heard {caw}."
    )
    if child.memes["focus"] >= THRESHOLD:
        world.say(
            f"{child.id} narrowed {child.pronoun('possessive')} eyes. "
            f'"That is not a people clue," {child.pronoun()} said.'
        )


def follow_clues(world: World, child: Entity, perch: Perch, item: MissingItem) -> None:
    world.say(world.scene.search_line)
    world.say(perch.where_line)
    world.say(
        f"There, tucked among twigs, was a bright little gleam. {perch.nest_line}"
    )
    world.facts["perch_spotted"] = True
    child.meters["spotted"] += 1
    world.say(
        f'"It was the crow," {child.id} breathed. "The crow borrowed my {item.label}."'
    )


def recover(world: World, child: Entity, helper: Entity, item: MissingItem,
            perch: Perch, response: Response) -> None:
    forecast = predict_solution(world, response, perch)
    helper.meters["trying"] += 1
    world.facts["response_reach"] = response.reach
    world.facts["perch_height"] = perch.height
    propagate(world, narrate=False)
    if not forecast["solved"] or not world.facts["solved"]:
        raise StoryError(explain_response(response, perch))
    body = response.text.replace("{item}", item.label)
    world.say(
        f"{helper.label_word.capitalize()} smiled and kept {helper.pronoun('possessive')} voice calm. "
        f"{helper.pronoun().capitalize()} {body}."
    )
    world.say(
        f"The crow blinked, decided the trade was fair, and let the {item.label} come down without a fuss."
    )


def ending(world: World, child: Entity, helper: Entity, item: MissingItem) -> None:
    child.memes["gratitude"] += 1
    world.say(
        f'{child.id} held the {item.label} against {child.pronoun("possessive")} chest and laughed. '
        f'"So that was the mystery."'
    )
    world.say(
        f'{helper.label_word.capitalize()} hung it back where it belonged and said, '
        f'"The best mysteries are the ones we solve kindly."'
    )
    world.say(item.home_ending)


def tell(scene: Scene, item_cfg: MissingItem, perch: Perch, response: Response,
         child_name: str = "Nora", child_type: str = "girl",
         helper_type: str = "grandfather", trait: str = "observant") -> World:
    world = World(scene)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=[trait, "gentle"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        traits=["calm", "kind"],
    ))
    crow = world.add(Entity(
        id="crow",
        kind="character",
        type="bird",
        label="the crow",
        role="culprit",
        attrs={"borrowed": item_cfg.id},
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="lost_item",
        label=item_cfg.label,
        attrs={"item_id": item_cfg.id, "home": scene.spot_phrase},
    ))
    world.add(Entity(
        id="perch",
        kind="thing",
        type="perch",
        label=perch.label,
        attrs={"height": perch.height},
    ))

    world.facts.update(
        scene=scene,
        item_cfg=item_cfg,
        perch_cfg=perch,
        response=response,
        child=child,
        helper=helper,
        culprit=crow,
        response_reach=response.reach,
        perch_height=perch.height,
    )

    item.meters["missing"] += 1
    crow.meters["took_item"] += 1
    propagate(world, narrate=False)

    introduce(world, child, helper, item_cfg)
    notice_loss(world, child, item_cfg)

    world.para()
    inspect_clues(world, child, helper)
    follow_clues(world, child, perch, item_cfg)

    world.para()
    recover(world, child, helper, item_cfg, perch, response)
    ending(world, child, helper, item_cfg)

    return world


SCENES = {
    "porch": Scene(
        id="porch",
        label="the front porch",
        opening="The boards still held a little night-cool, and the geranium leaves shivered with dew.",
        spot_phrase="on the hook beside the blue door",
        search_line="They followed the feather past the rain barrel and slowly tipped their heads back.",
        affords={"gate_arch", "shed_roof", "oak_branch"},
        tags={"porch", "mystery"},
    ),
    "garden": Scene(
        id="garden",
        label="the garden gate",
        opening="Pea vines twined around the fence, and the beans were silvered with dew.",
        spot_phrase="from the little peg by the gate latch",
        search_line="They walked between the bean rows and looked higher than the roses, higher than the fence.",
        affords={"gate_arch", "oak_branch"},
        tags={"garden", "mystery"},
    ),
    "yard": Scene(
        id="yard",
        label="the back yard",
        opening="The grass was wet at the tips, and the air smelled like mint and wet wood.",
        spot_phrase="from the nail near the tool shed",
        search_line="They crossed the damp grass, listening for the caw that hopped from one corner of the yard to another.",
        affords={"shed_roof", "oak_branch"},
        tags={"yard", "mystery"},
    ),
}

ITEMS = {
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="the little brass bell",
        shine=True,
        portable=True,
        ring_text="rang in one clear note",
        home_ending="A moment later the little brass bell was home again, ringing a bright note into the clean morn air.",
        tags={"bell", "shiny"},
    ),
    "spoon": MissingItem(
        id="spoon",
        label="spoon",
        phrase="the silver jam spoon",
        shine=True,
        portable=True,
        ring_text="caught the light like water",
        home_ending="Soon the silver jam spoon was back in its place, catching the pale morn light as if it had never left.",
        tags={"spoon", "shiny"},
    ),
    "star": MissingItem(
        id="star",
        label="star charm",
        phrase="the tin star charm",
        shine=True,
        portable=True,
        ring_text="twinkled when it swung",
        home_ending="Before breakfast, the tin star charm was hanging safely again, twinkling in the gentle morn light.",
        tags={"star", "shiny"},
    ),
    "watering_can": MissingItem(
        id="watering_can",
        label="watering can",
        phrase="the green watering can",
        shine=False,
        portable=False,
        ring_text="",
        home_ending="",
        tags={"garden_tool"},
    ),
}

PERCHES = {
    "gate_arch": Perch(
        id="gate_arch",
        label="the gate arch",
        where_line="Up on the curved arch above the gate sat a crow with one bright eye turned sideways.",
        height=1,
        nest_line="Its nest was wedged in the ivy, and something shiny gleamed between the leaves.",
        tags={"crow", "ivy"},
    ),
    "shed_roof": Perch(
        id="shed_roof",
        label="the shed roof",
        where_line="On the edge of the shed roof stood a crow, black as a dropped glove against the sky.",
        height=2,
        nest_line="By the chimney pot lay a lopsided nest, and inside it winked a silver spark.",
        tags={"crow", "roof"},
    ),
    "oak_branch": Perch(
        id="oak_branch",
        label="the high oak branch",
        where_line="High in the old oak, a crow shuffled along a branch and gave a rusty little caw.",
        height=3,
        nest_line="In the fork of the branch sat a nest lined with twigs, string, and one stolen gleam.",
        tags={"crow", "tree"},
    ),
}

RESPONSES = {
    "blanket_trade": Response(
        id="blanket_trade",
        sense=2,
        reach=1,
        text="spread a soft blanket below, held up a shiny jar lid near the nest, and waited until the crow dropped the {item} safely into the blanket",
        fail="tried to coax the crow from below, but the perch was simply too high",
        qa_text="used a soft blanket and a shiny trade to get the item down safely",
        tags={"kindness", "blanket"},
    ),
    "stool_trade": Response(
        id="stool_trade",
        sense=2,
        reach=2,
        text="stood on a sturdy stool, lifted a glittery button tin, and traded with the crow for the {item}",
        fail="stood on a stool and coaxed gently, but could not reach high enough",
        qa_text="stood on a stool and traded a glittery tin for the item",
        tags={"kindness", "stool"},
    ),
    "ladder_trade": Response(
        id="ladder_trade",
        sense=3,
        reach=3,
        text="set up a ladder, held out a bright jar lid, and made a patient trade for the {item}",
        fail="climbed partway up, but the crow hopped even higher and kept the item out of reach",
        qa_text="used a ladder and a shiny trade to bring the item back",
        tags={"kindness", "ladder"},
    ),
    "throw_stick": Response(
        id="throw_stick",
        sense=1,
        reach=3,
        text="threw a stick toward the nest",
        fail="threw a stick and only frightened the crow",
        qa_text="threw a stick at the nest",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ella", "Zoe", "Anna", "Rose", "Lucy"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Finn", "Eli", "Jack", "Max"]
TRAITS = ["observant", "careful", "patient", "curious", "thoughtful"]


@dataclass
class StoryParams:
    scene: str
    item: str
    perch: str
    response: str
    child: str
    child_gender: str
    helper_type: str
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
    "crow": [(
        "Why do crows like shiny things?",
        "Crows notice bright, glittery objects very quickly. Sometimes they pick them up because the shine catches their eye."
    )],
    "feather": [(
        "What can a feather tell you in a mystery?",
        "A feather can be a clue that a bird was nearby. Clues help you guess what happened before you saw it."
    )],
    "bell": [(
        "What does a bell do?",
        "A bell makes a ringing sound when it moves. People use bells to call attention or make a cheerful sound."
    )],
    "spoon": [(
        "What is a jam spoon for?",
        "A jam spoon is a small spoon used to scoop and stir sweet jam. A shiny metal spoon can flash in the light."
    )],
    "star": [(
        "What is a charm?",
        "A charm is a small hanging decoration or trinket. People keep charms because they look pretty or feel special."
    )],
    "ladder": [(
        "What is a ladder for?",
        "A ladder helps a grown-up reach something high. It should be used carefully and held steady."
    )],
    "stool": [(
        "What is a stool?",
        "A stool is a short seat or step that can help a person reach a little higher. It is for low places, not very tall ones."
    )],
    "kindness": [(
        "Why is it good to solve an animal problem gently?",
        "Animals do not understand our rules the way people do. A gentle fix keeps both the people and the animal safe."
    )],
    "mystery": [(
        "What is a mystery?",
        "A mystery is something puzzling that you do not understand yet. You solve it by noticing clues and thinking carefully."
    )],
}
KNOWLEDGE_ORDER = ["mystery", "crow", "feather", "bell", "spoon", "star", "ladder", "stool", "kindness"]


CURATED = [
    StoryParams(
        scene="porch",
        item="bell",
        perch="shed_roof",
        response="stool_trade",
        child="Nora",
        child_gender="girl",
        helper_type="grandfather",
        trait="observant",
    ),
    StoryParams(
        scene="garden",
        item="spoon",
        perch="gate_arch",
        response="blanket_trade",
        child="Ben",
        child_gender="boy",
        helper_type="grandmother",
        trait="careful",
    ),
    StoryParams(
        scene="yard",
        item="star",
        perch="oak_branch",
        response="ladder_trade",
        child="Mia",
        child_gender="girl",
        helper_type="uncle",
        trait="curious",
    ),
    StoryParams(
        scene="porch",
        item="spoon",
        perch="oak_branch",
        response="ladder_trade",
        child="Theo",
        child_gender="boy",
        helper_type="aunt",
        trait="patient",
    ),
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item = world.facts["item_cfg"]
    scene = world.facts["scene"]
    return [
        f'Write a short mystery story for a 3-to-5-year-old that includes the word "morn" and has a happy ending.',
        f"Tell a gentle mystery where a {child.type} named {child.id} notices that {item.phrase} is missing in {scene.label}, follows clues, and solves the puzzle kindly.",
        f"Write a child-facing mystery about a missing shiny object, a crow, and a calm helper, ending with the {item.label} safely back where it belongs.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item_cfg"]
    perch = world.facts["perch_cfg"]
    response = world.facts["response"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery at the start of the story?",
            f"The mystery was that {item.phrase} had vanished from its usual place. On that quiet morn, the empty spot made {child.id} stop and start looking for clues."
        ),
        (
            "What clues did they find?",
            f"They found a black feather and heard a crow calling from above. Those clues told them to look up instead of blaming a person."
        ),
        (
            "Who had the missing item, and where was it?",
            f"A crow had borrowed the {item.label}, and it was in a nest near {perch.label}. The bright shine in the nest helped {child.id} solve the mystery."
        ),
        (
            f"How did {helper.label_word} get the {item.label} back?",
            f"{helper.label_word.capitalize()} {response.qa_text}. The fix was calm and gentle, so the crow was not hurt and the {item.label} came back safely."
        ),
        (
            "Why is the ending happy?",
            f"The missing thing was returned to its proper place, and everyone understood what had happened. The mystery ended with relief instead of fear because they solved it kindly."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item_cfg"]
    response = world.facts["response"]
    tags: set[str] = {"mystery", "crow", "feather", "kindness"} | set(item.tags) | set(response.tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    shown_facts = {
        k: v for k, v in world.facts.items()
        if k in {"feather_found", "caw_heard", "perch_spotted", "solved", "response_reach", "perch_height"}
    }
    lines.append(f"  facts: {shown_facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
portable_shiny(I) :- item(I), shiny(I), portable(I).
valid(S, I, P) :- scene(S), item(I), perch(P), affords(S, P), portable_shiny(I).

sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
adequate(R, P) :- response(R), perch(P), reach(R, RR), height(P, H), RR >= H.

ready :- chosen_response(R), chosen_perch(P), sensible(R), adequate(R, P).
outcome(solved) :- ready.
outcome(stuck) :- not ready.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SCENES.items():
        lines.append(asp.fact("scene", sid))
        for pid in sorted(scene.affords):
            lines.append(asp.fact("affords", sid, pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.shine:
            lines.append(asp.fact("shiny", iid))
        if item.portable:
            lines.append(asp.fact("portable", iid))
    for pid, perch in PERCHES.items():
        lines.append(asp.fact("perch", pid))
        lines.append(asp.fact("height", pid, perch.height))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("reach", rid, response.reach))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_response", params.response),
        asp.fact("chosen_perch", params.perch),
    ])
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

    clingo_resp = set(asp_sensible())
    python_resp = {r.id for r in sensible_responses()}
    if clingo_resp == python_resp:
        print(f"OK: sensible responses match ({sorted(clingo_resp)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_resp)} python={sorted(python_resp)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params() smoke test with seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(smoke, trace=True, qa=True, header="### smoke")
        if "smoke" not in buf.getvalue():
            raise StoryError("Emit smoke test did not print expected header.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle morning mystery about a missing shiny thing, a crow, and a kind solution."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--perch", choices=PERCHES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None:
        item = ITEMS[args.item]
        if not item_can_be_taken(item):
            raise StoryError(explain_item(item))

    if args.response is not None and args.perch is not None:
        response = RESPONSES[args.response]
        perch = PERCHES[args.perch]
        if response.sense < SENSE_MIN or not can_reach(response, perch):
            raise StoryError(explain_response(response, perch))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.item is None or combo[1] == args.item)
        and (args.perch is None or combo[2] == args.perch)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, item_id, perch_id = rng.choice(sorted(combos))
    sensible = [
        rid for rid, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and can_reach(response, PERCHES[perch_id])
    ]
    if args.response is not None:
        if args.response not in sensible:
            raise StoryError(explain_response(RESPONSES[args.response], PERCHES[perch_id]))
        response_id = args.response
    else:
        response_id = rng.choice(sorted(sensible))

    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        scene=scene_id,
        item=item_id,
        perch=perch_id,
        response=response_id,
        child=child,
        child_gender=gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        scene = SCENES[params.scene]
        item = ITEMS[params.item]
        perch = PERCHES[params.perch]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]}.)") from None

    if not item_can_be_taken(item):
        raise StoryError(explain_item(item))
    if params.perch not in scene.affords:
        raise StoryError(
            f"(No story: {scene.label} does not support the perch '{params.perch}' in this world.)"
        )
    if response.sense < SENSE_MIN or not can_reach(response, perch):
        raise StoryError(explain_response(response, perch))

    world = tell(
        scene=scene,
        item_cfg=item,
        perch=perch,
        response=response,
        child_name=params.child,
        child_type=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, item, perch) combos:\n")
        for scene, item, perch in combos:
            print(f"  {scene:8} {item:14} {perch}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.item} in {p.scene} ({p.perch}, {p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
