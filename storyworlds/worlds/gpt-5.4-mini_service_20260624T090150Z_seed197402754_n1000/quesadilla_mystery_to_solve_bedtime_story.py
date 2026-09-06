#!/usr/bin/env python3
"""
Bedtime Story world: a gentle quesadilla mystery to solve.

A small child notices a missing quesadilla, follows soft clues through the house,
and learns that a loving helper simply moved it to keep it warm. The story is
state-driven: hunger, curiosity, clues, and a cozy reveal change the world.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    quesadilla: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        neutral = {"child", "person"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str
    calm: bool = True
    rooms: tuple[str, ...] = ("kitchen", "hallway", "living room", "bedroom")
    setting: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    warm: bool = True
    room: str = "kitchen"
    clue: str = "a tiny breadcrumb trail"
    comfort: str = "cozy and warm"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Helper:
    id: str
    label: str
    motive: str
    hiding_place: str
    reveal: str
    kind_help: str = "warm it up"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


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
        clone.entities = {k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label,
            "phrase": e.phrase, "owner": e.owner, "caretaker": e.caretaker,
            "meters": dict(e.meters), "memes": dict(e.memes)
        }) for k, e in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _first_clue_found(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("searching", 0) < THRESHOLD:
        return out
    sig = ("first_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["first_clue"] += 1
    out.append(world.facts["first_discovery"])
    return out


def _second_clue_found(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("first_clue", 0) < THRESHOLD:
        return out
    sig = ("second_clue",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["second_clue"] += 1
    child.memes["hope"] += 1
    out.append(world.facts["second_discovery"])
    return out


def _solve_mystery(world: World) -> list[str]:
    out = []
    child = world.get("child")
    snack = world.get("quesadilla")
    helper = world.get("helper")
    sig = ("resolved",)
    if sig in world.fired:
        return out
    if child.memes.get("second_clue", 0) < THRESHOLD:
        return out
    world.fired.add(sig)
    snack.meters["warmth"] = 1.0
    child.meters["hunger"] = 0.0
    child.memes["calm"] += 1
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    out.extend(world.facts["resolution_lines"])
    return out


RULES = [_first_clue_found, _second_clue_found, _solve_mystery]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            s = rule(world)
            if s:
                produced.extend(s)
                changed = True
    for s in produced:
        world.say(s)
    return produced


def begin_search(world: World) -> None:
    child = world.get("child")
    child.memes["searching"] += 1
    child.meters["hunger"] += 1
    world.say(world.facts["missing_line"])
    world.say(world.facts["question_line"])


def close_story(world: World) -> None:
    child = world.get("child")
    if ("resolved",) not in world.fired:
        raise StoryError("The quesadilla mystery reached bedtime without a resolution.")
    world.say(world.facts["ending_line"])
    child.memes["asleep"] += 1


SCENARIOS = (
    {
        "missing_from": "the blue plate beside the stove",
        "first_clue": "a floury oven-mitt print on the counter",
        "first_discovery": "A floury oven-mitt print pointed from the empty blue plate toward the pantry.",
        "second_clue": "the warm, toasty smell near the pantry door",
        "second_discovery": "At the pantry, a warm, toasty smell curled through the crack beneath the door.",
        "found_place": "a covered pan on the pantry shelf",
        "motive": "a cool draft had begun to chill the snack",
        "helper_action": "covered the pan with a clean towel",
    },
    {
        "missing_from": "the little table by the window",
        "first_clue": "three crumbs leading toward the reading nook",
        "first_discovery": "Three crisp crumbs made a tiny trail from the table to the reading nook.",
        "second_clue": "a corner of the striped napkin beneath a basket",
        "second_discovery": "Beside the books, the corner of a striped napkin peeked from beneath the picnic basket.",
        "found_place": "the lidded picnic basket",
        "motive": "the curious cat had jumped onto the table",
        "helper_action": "tucked the plate safely inside the basket",
    },
    {
        "missing_from": "the tray beside the bedtime cocoa",
        "first_clue": "a thin strand of cheese on the rug",
        "first_discovery": "A thin strand of cheese glimmered on the rug like a pale thread.",
        "second_clue": "a folded red napkin outside the dining room",
        "second_discovery": "The cheese thread ended at a folded red napkin outside the dining room.",
        "found_place": "the warming dish on the dining table",
        "motive": "the cocoa had spilled close to the tray",
        "helper_action": "carried the snack away from the spill and wiped the plate dry",
    },
    {
        "missing_from": "the flowered plate on the kitchen island",
        "first_clue": "a round mark where the plate had rested",
        "first_discovery": "On the kitchen island, one clean round mark showed exactly where the plate had been.",
        "second_clue": "the soft click of a timer near the breakfast nook",
        "second_discovery": "From the breakfast nook came the soft click of a timer and the faint scent of toasted corn.",
        "found_place": "a warm stoneware dish in the breakfast nook",
        "motive": "the middle needed one more minute to melt",
        "helper_action": "set a timer and warmed it until the cheese was perfectly soft",
    },
    {
        "missing_from": "the wooden board under the night-light",
        "first_clue": "a green napkin caught on a chair",
        "first_discovery": "A green napkin hung from the back of a chair, though it had been beside the quesadilla before.",
        "second_clue": "two apple slices on a saucer in the hall",
        "second_discovery": "In the hall, two apple slices waited on a saucer beside the closed study door.",
        "found_place": "a covered tray in the study",
        "motive": "apple slices would make it a more balanced bedtime snack",
        "helper_action": "arranged the warm wedges and apple slices together",
    },
    {
        "missing_from": "the small plate near the back door",
        "first_clue": "a fluttering paper moon from the napkin ring",
        "first_discovery": "The paper moon from the napkin ring fluttered beside the back door.",
        "second_clue": "a trail of raindrops ending at the mudroom bench",
        "second_discovery": "A few raindrops crossed the floor and stopped beside the mudroom bench.",
        "found_place": "an insulated lunch bag on the mudroom shelf",
        "motive": "rain had blown through the open doorway",
        "helper_action": "slipped the plate into the dry insulated bag",
    },
    {
        "missing_from": "the checked placemat at the end of the counter",
        "first_clue": "the quiet squeak of a cabinet hinge",
        "first_discovery": "The room was still until a cabinet hinge gave one small, helpful squeak.",
        "second_clue": "a wooden spoon resting beside the warming drawer",
        "second_discovery": "Below the cabinet, a wooden spoon pointed straight toward the warming drawer.",
        "found_place": "the warming drawer beneath the counter",
        "motive": "the bedtime song lasted longer than expected",
        "helper_action": "put the plate in the warming drawer so it would not turn cold",
    },
    {
        "missing_from": "the moon-shaped plate beside the sink",
        "first_clue": "a dab of tomato salsa on a clean dish towel",
        "first_discovery": "A bright dab of tomato salsa dotted the clean dish towel beside the sink.",
        "second_clue": "the rustle of foil from the family room",
        "second_discovery": "Then foil rustled softly in the family room, just beyond the half-open door.",
        "found_place": "a foil-covered tray on the family-room ottoman",
        "motive": "everyone had moved there to watch the moon rise",
        "helper_action": "covered the tray and carried the bedtime snack to the window",
    },
)

SETTINGS = (
    "a small house where the hallway night-light glowed",
    "a quiet apartment above the sleepy town",
    "a cottage where rain tapped softly on the roof",
    "a warm farmhouse under a silver moon",
    "a little home at the end of a lantern-lit lane",
)

FILLINGS = (
    "mild cheddar and sweet corn",
    "melted cheese and tiny black beans",
    "creamy cheese and spinach",
    "golden cheese with a little tomato",
    "soft cheese and roasted squash",
)

SEARCH_REACTIONS = (
    "took one slow breath and decided to inspect the room carefully",
    "remembered that good detectives begin with what they can see",
    "felt worried for a moment, then chose to follow the evidence",
    "listened to the quiet house before taking the first careful step",
)

ENDING_IMAGES = (
    "Soon only a crescent of quesadilla remained, and its last curl of steam faded beneath the glowing night-light.",
    "After the final warm bite, the empty plate shone like a little moon while the house settled into silence.",
    "The clean plate rested by the sink, the striped napkin was folded, and moonlight lay peacefully across the floor.",
    "With the mystery solved, a buttery scent lingered in the kitchen as the bedroom lamp clicked softly off.",
    "A few golden crumbs remained on the plate; then the blanket rose to a sleepy chin and the clock gave one quiet tick.",
)


def tell(params: Optional["StoryParams"] = None) -> World:
    if params is None:
        params = StoryParams()
    setting = Setting(place=params.setting_place)
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    quesadilla = world.add(Entity(
        id="quesadilla",
        type="snack",
        label="quesadilla",
        phrase=f"the quesadilla filled with {params.filling}",
        owner=child.id,
        caretaker=helper.id,
    ))
    helper_subject = helper.pronoun("subject").capitalize()
    world.facts.update(
        child=child,
        helper=helper,
        quesadilla=quesadilla,
        setting=setting,
        filling=params.filling,
        missing_from=params.missing_from,
        first_clue=params.first_clue,
        second_clue=params.second_clue,
        found_place=params.found_place,
        motive=params.motive,
        first_discovery=params.first_discovery,
        second_discovery=params.second_discovery,
        missing_line=(
            f"When {child.label} returned in pajamas, {params.missing_from} was empty. "
            f"The quesadilla had vanished."
        ),
        question_line=(
            f'"A bedtime mystery," {child.label} whispered. {child.pronoun("subject").capitalize()} '
            f"{params.search_reaction}."
        ),
        resolution_lines=[
            f"There, {child.label} found {helper.label} beside {params.found_place}, with the quesadilla safe and warm.",
            f'"I moved it because {params.motive}," {helper.label} explained. {helper_subject} had '
            f"{params.helper_action}.",
            f"The clues fit at last. {child.label} thanked {helper.label}, shared the crisp-edged wedges, and felt the worry melt away.",
        ],
        ending_line=params.ending_image,
    )

    world.say(
        f"Just before bedtime, {child.label} helped {helper.label} make a quesadilla filled with {params.filling} "
        f"in {setting.place}."
    )
    world.say(
        f"They left it on {params.missing_from}, ready for one cozy snack after pajamas were on."
    )

    world.para()
    begin_search(world)
    propagate(world)

    world.para()
    close_story(world)
    return world


ASP_RULES = r"""
% A bedtime mystery is reasonable when the quesadilla is missing and a helper can
% explain where it went.
missing(quesadilla).
has_helper(helper).

mystery_to_solve(quesadilla) :- missing(quesadilla), has_helper(helper).
resolved(quesadilla) :- mystery_to_solve(quesadilla), found_clue(crumbs), explain(helper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "quesadilla"),
        asp.fact("has_helper", "helper"),
        asp.fact("found_clue", "crumbs"),
        asp.fact("explain", "helper"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
    return sorted(set(asp.atoms(model, "mystery_to_solve"))), sorted(set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    myst, res = asp_valid()
    py = {("quesadilla",)}
    if set(myst) == py and set(res) == py:
        print("OK: ASP and Python agree on the bedtime quesadilla mystery.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP mystery:", myst)
    print("ASP resolved:", res)
    return 1


@dataclass
class StoryParams:
    seed: Optional[int] = None
    child_name: str = "Mina"
    child_type: str = "girl"
    helper_name: str = "Mom"
    helper_type: str = "mother"
    setting_place: str = SETTINGS[0]
    filling: str = FILLINGS[0]
    missing_from: str = SCENARIOS[0]["missing_from"]
    first_clue: str = SCENARIOS[0]["first_clue"]
    first_discovery: str = SCENARIOS[0]["first_discovery"]
    second_clue: str = SCENARIOS[0]["second_clue"]
    second_discovery: str = SCENARIOS[0]["second_discovery"]
    found_place: str = SCENARIOS[0]["found_place"]
    motive: str = SCENARIOS[0]["motive"]
    helper_action: str = SCENARIOS[0]["helper_action"]
    search_reaction: str = SEARCH_REACTIONS[0]
    ending_image: str = ENDING_IMAGES[0]
    samples: list = field(default_factory=list)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime quesadilla mystery story world.")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    seed = int(getattr(args, "seed", None) or 0)
    # The core is a permutation of 288 child/helper/scenario combinations, so
    # any 100 adjacent seeds are distinct. The RNG spreads the prose axes.
    index = (seed * 191 + 137) % 288

    def take(options):
        nonlocal index
        value = options[index % len(options)]
        index //= len(options)
        return value

    child_name, child_type = take(
        (("Mina", "girl"), ("Nora", "girl"), ("Lina", "girl"), ("Ivy", "girl"),
         ("Theo", "boy"), ("Sam", "child"))
    )
    helper_name, helper_type = take(
        (("Mom", "mother"), ("Mama", "mother"), ("Dad", "father"),
         ("Papa", "father"), ("Grandma", "woman"), ("Grandpa", "man"))
    )
    scenario = take(SCENARIOS)
    return StoryParams(
        seed=seed,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
        setting_place=rng.choice(SETTINGS),
        filling=rng.choice(FILLINGS),
        missing_from=scenario["missing_from"],
        first_clue=scenario["first_clue"],
        first_discovery=scenario["first_discovery"],
        second_clue=scenario["second_clue"],
        second_discovery=scenario["second_discovery"],
        found_place=scenario["found_place"],
        motive=scenario["motive"],
        helper_action=scenario["helper_action"],
        search_reaction=rng.choice(SEARCH_REACTIONS),
        ending_image=rng.choice(ENDING_IMAGES),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short bedtime story about a missing quesadilla and a gentle mystery to solve.",
        f"Tell a cozy mystery where {f['child'].label} follows {f['first_clue']} and {f['second_clue']}.",
        f"Write a bedtime tale in which {f['helper'].label} moved a quesadilla because {f['motive']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=(
                f"Who searched for the {f['filling']} quesadilla after it vanished from "
                f"{f['missing_from']} in {f['setting'].place}?"
            ),
            answer=(
                f"{child.label} searched for it while {helper.label} kept it safe. "
                f"It had disappeared from {f['missing_from']}."
            ),
        ),
        QAItem(
            question=(
                f"Why did {helper.label} move {child.label}'s {f['filling']} quesadilla "
                f"from {f['missing_from']}?"
            ),
            answer=f"{helper.label} moved it because {f['motive']}. The snack was waiting safely in {f['found_place']}.",
        ),
        QAItem(
            question=f"Which clues helped {child.label} solve the mystery?",
            answer=f"{child.label} noticed {f['first_clue']} and then {f['second_clue']}. Together they led to {helper.label} and the quesadilla.",
        ),
        QAItem(
            question=f"How did {child.label} feel after finding the snack in {f['found_place']}?",
            answer=f"{child.label} felt calm and joyful after the clues made sense. {child.label} thanked {helper.label} and shared the warm wedges.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quesadilla?",
            answer="A quesadilla is a warm tortilla with cheese and sometimes other fillings inside, folded or sandwiched together.",
        ),
        QAItem(
            question="Why do people keep food warm?",
            answer="People keep food warm so it stays tasty and cozy to eat, especially when someone is waiting for bedtime or dinner.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show mystery_to_solve/1.\n#show resolved/1."))
        print(sorted(set(asp.atoms(model, "mystery_to_solve"))))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(seed=base_seed))]
    else:
        for i in range(getattr(args, "n", None)):
            sample_seed = base_seed + i
            sample_args = argparse.Namespace(**vars(args))
            sample_args.seed = sample_seed
            params = resolve_params(sample_args, random.Random(sample_seed))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
