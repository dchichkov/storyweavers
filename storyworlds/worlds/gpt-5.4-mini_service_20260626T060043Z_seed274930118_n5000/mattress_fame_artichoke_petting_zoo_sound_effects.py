#!/usr/bin/env python3
"""
Standalone story world: petting zoo with sound effects, repetition, and reconciliation.

Premise:
A child visits a petting zoo and wants to make a funny sound effect with a loud,
bouncy mattress prop they brought for a little show. The child also has a prized
artichoke-shaped fame ribbon from a school contest. When the sound effects scare
the animals, the child and a helper must calm things down, repair the moment, and
find a gentler way to share the joke.

This file models a small causal world with physical meters and emotional memes,
plus a Python reasonableness gate and an inline ASP twin for parity checks.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

ANIMAL_KINDS = {"goat", "lamb", "piglet", "rabbit", "pony"}

SOUND_EFFECTS = {
    "boing": {"bounce": 1.0, "loud": 1.0},
    "boop": {"loud": 0.3},
    "tap": {"loud": 0.1},
    "honk": {"loud": 0.8},
}

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------

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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    animal: object | None = None
    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def _meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    place: str = "the petting zoo"
    affords: set[str] = field(default_factory=set)
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
class Prop:
    id: str
    label: str
    phrase: str
    sound: str
    loudness: float
    mess: str
    emotion: str
    guards: set[str] = field(default_factory=set)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
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
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_role: str
    prop: str
    sound_effect: str
    animal: str
    scenario: str = "welcome_show"
    opening_variant: int = 0
    response_variant: int = 0
    ending_variant: int = 0
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "petting_zoo": Setting(place="the petting zoo", affords={"sound_effects", "reconciliation"}),
}

PROPS = {
    "mattress": Prop(
        id="mattress",
        label="mattress",
        phrase="a small mattress prop",
        sound="boing",
        loudness=1.0,
        mess="bump",
        emotion="showy",
        guards={"soft"},
    ),
    "artichoke": Prop(
        id="artichoke",
        label="artichoke",
        phrase="a bright artichoke-shaped fame ribbon",
        sound="boop",
        loudness=0.2,
        mess="nervous",
        emotion="proud",
        guards={"gentle"},
    ),
    "tambourine": Prop(
        id="tambourine",
        label="tambourine",
        phrase="a shiny little tambourine",
        sound="honk",
        loudness=0.8,
        mess="clatter",
        emotion="lively",
        guards={"gentle"},
    ),
}

ANIMALS = {
    "goat": {"kind": "goat", "nickname": "goat", "noise": "bleat"},
    "lamb": {"kind": "lamb", "nickname": "lamb", "noise": "baa"},
    "piglet": {"kind": "piglet", "nickname": "piglet", "noise": "oink"},
    "rabbit": {"kind": "rabbit", "nickname": "rabbit", "noise": "squeak"},
    "pony": {"kind": "pony", "nickname": "pony", "noise": "neigh"},
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Pia", "Tess"]
BOY_NAMES = ["Eli", "Owen", "Theo", "Noah", "Milo", "Finn"]
HELPERS = ["zookeeper", "mom", "dad", "older sister", "older brother"]


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def prop_at_risk(prop: Prop, animal: str) -> bool:
    return prop.id in {"mattress", "artichoke"} and animal in ANIMAL_KINDS


def valid_combo(place: str, prop: str, animal: str) -> bool:
    if place not in SETTINGS:
        return False
    if prop not in PROPS or animal not in ANIMALS:
        return False
    return prop_at_risk(_safe_lookup(PROPS, prop), animal)


def explain_rejection(place: str, prop: str, animal: str) -> str:
    return (
        f"(No story: at the petting zoo, the {prop} situation with a {animal} "
        f"doesn't create a believable little problem and fix.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def sound_repeat(effect: str, times: int = 3) -> str:
    return " ".join([effect] * times)


def _sound(world: World, child: Entity, prop: Prop, animal: Entity) -> None:
    sig = ("sound", prop.id, animal.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    child.meters["activity"] = child.meters.get("activity", 0.0) + 1
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1

    if prop.sound == "boing":
        child.meters["bounce"] = child.meters.get("bounce", 0.0) + 1

    if prop.loudness >= 0.7:
        animal.memes["startle"] = animal.memes.get("startle", 0.0) + 1
        world.say(
            f"{child.id} went, “{sound_repeat(prop.sound)}!” and the little sound "
            f"filled the pen like a round toy drum."
        )
        world.say(
            f"{animal.label.capitalize()} flinched and stepped back."
        )
    else:
        world.say(
            f"{child.id} made a small “{prop.sound},” then smiled at the neat little echo."
        )

    if prop.id == "mattress":
        world.facts["repetition"] = True
        world.facts["sound_effect"] = prop.sound
        world.facts["animal_startled"] = animal.memes.get("startle", 0.0) >= THRESHOLD


def _reconcile(world: World, child: Entity, helper: Entity, animal: Entity, prop: Prop) -> None:
    sig = ("reconcile", child.id, animal.id)
    if sig in world.fired:
        return
    world.fired.add(sig)

    if animal.memes.get("startle", 0.0) < THRESHOLD:
        return

    child.memes["embarrassment"] = child.memes.get("embarrassment", 0.0) + 1
    helper.memes["gentleness"] = helper.memes.get("gentleness", 0.0) + 1
    animal.memes["calm"] = animal.memes.get("calm", 0.0) + 1

    world.say(
        f"Then {helper.id} knelt beside {child.id} and said it was all right."
    )
    world.say(
        f"{child.id} looked at the {animal.label}, lowered the mattress, and tried a softer “{prop.sound}.”"
    )
    world.say(
        f"{animal.label.capitalize()} listened, stayed put, and nosed a tuft of hay instead."
    )
    world.say(
        f"{child.id} and {helper.id} smiled because the joke had turned kind again."
    )


@dataclass(frozen=True)
class Scenario:
    animal: str
    premise: str
    goal: str
    trouble: str
    evidence: str
    repair: str
    result: str


SCENARIOS = {
    "welcome_show": Scenario(
        animal="goat",
        premise="had promised to open the keeper's welcome talk with one cheerful bounce",
        goal="make the waiting families laugh without bothering the animals",
        trouble="the mattress skidded against the gate, and the sudden boom sent the goat behind its water tub",
        evidence="The goat's ears stayed flat whenever the mattress faced the pen",
        repair="turned the mattress on its side as a quiet backdrop and tapped the artichoke ribbon for a tiny plip",
        result="the goat stepped out and ate from the keeper's open palm",
    ),
    "portrait_booth": Scenario(
        animal="pony",
        premise="was helping make a soft portrait corner for the petting zoo's adoption board",
        goal="earn a fine photograph instead of chasing more applause",
        trouble="a showy bounce flashed the fame ribbon, and the pony backed out of the camera frame",
        evidence="The pony returned near the blanket but stopped when the springs squeaked",
        repair="laid the mattress flat, covered its squeaky corner, and let the pony sniff the artichoke ribbon",
        result="the pony stood calmly beside the hand-painted adoption sign",
    ),
    "nap_corner": Scenario(
        animal="lamb",
        premise="had brought an old crib mattress to pad the lambs' supervised rest corner",
        goal="finish the useful job before showing anyone the school fame ribbon",
        trouble="testing the springs with three comic boings woke a lamb and tangled a hay basket",
        evidence="The lamb paced beside the fallen basket instead of settling on the fresh straw",
        repair="lifted the mattress with the helper, righted the basket, and hummed a soft baa-boop rhythm",
        result="the lamb curled against the padded rail and closed its eyes",
    ),
    "snack_demo": Scenario(
        animal="rabbit",
        premise="was scheduled to explain which garden vegetables the animals may eat",
        goal="share an artichoke fact clearly, even though the fame ribbon made performing tempting",
        trouble="a mattress-drum flourish drowned out the keeper's warning and made the rabbit bolt from the display",
        evidence="The untouched artichoke leaf lay beside a rabbit-shaped gap in the straw",
        repair="put the mattress away, repeated the safety rule in a whisper, and placed an approved leaf by the hide box",
        result="the rabbit emerged, sniffed the leaf, and nibbled while everyone listened quietly",
    ),
    "muddy_crossing": Scenario(
        animal="piglet",
        premise="was carrying a narrow mattress pad to cover a muddy patch outside the piglet yard",
        goal="help small visitors cross cleanly and prove that useful work mattered more than fame",
        trouble="the pad landed with a whomp, splashing mud and sending the piglet squealing into its shelter",
        evidence="Tiny hoofprints ended at the shelter door, where the piglet peered out",
        repair="moved the pad farther from the fence, wiped the rail, and answered each oink with a gentle boop",
        result="the piglet followed the quiet calls back to its feed pan",
    ),
    "lost_ribbon": Scenario(
        animal="goat",
        premise="planned one photograph with the artichoke-shaped ribbon that had made them briefly famous at school",
        goal="find the missing ribbon without blaming a curious animal",
        trouble="a bounce shook the ribbon loose, and the goat carried it beneath the climbing bridge",
        evidence="Green paper points showed beneath the bridge, but the goat guarded the narrow opening",
        repair="stopped bouncing, traded the goat a keeper-approved twig, and slid the mattress under the ribbon",
        result="the ribbon came out unchewed, and the goat kept the twig",
    ),
    "runaway_cart": Scenario(
        animal="pony",
        premise="was wheeling a folded mattress toward the first-aid tent for tired volunteers",
        goal="deliver it safely before joining the little fame-ribbon ceremony",
        trouble="a wheel struck a stone, the load cried sproing, and the cart rolled toward the pony's lead rope",
        evidence="The helper caught the handle, but the trembling pony had pulled the rope taut",
        repair="chocked the wheel with a block, carried the mattress by hand, and counted soft clip-clops with the pony",
        result="the loose rope hung in a curve while the pony drank peacefully",
    ),
    "story_stage": Scenario(
        animal="lamb",
        premise="had built a mattress stage for a tiny tale about a famous artichoke explorer",
        goal="finish the tale in a way the youngest visitors and the lamb could enjoy",
        trouble="the explorer's giant ker-boing made the lamb knock over the page board",
        evidence="The lamb stood on the final picture, hiding how the adventure ended",
        repair="sat on the floor, invited the lamb off with the keeper, and made each sound with two quiet finger taps",
        result="the last page showed the artichoke explorer sharing a leafy picnic",
    ),
    "rain_shelter": Scenario(
        animal="rabbit",
        premise="was using a clean mattress as a temporary wall while rain blew into the education shed",
        goal="keep the rabbit demonstration dry rather than protect a fancy reputation",
        trouble="an extra bounce loosened one strap; wind slapped the mattress with a whump and tipped the artichoke model toward the rabbit pen",
        evidence="The rabbit froze beneath the bench while rain dotted the floor",
        repair="fastened the mattress with two straps and moved the wobbling model onto a low crate",
        result="the rabbit stretched into a dry patch as rain ticked safely outside",
    ),
    "quiet_parade": Scenario(
        animal="piglet",
        premise="wanted the petting zoo parade to honor helpers, not just the wearer of a fame ribbon",
        goal="find a sound the piglet could comfortably follow",
        trouble="drumming on the mattress made the piglet turn around and scatter the paper artichoke badges",
        evidence="The piglet followed bare footsteps but veered away whenever the drumbeat returned",
        repair="gave every helper a badge and replaced the mattress drum with a soft pat-pat walking beat",
        result="the piglet followed the line past every smiling helper",
    ),
    "counting_game": Scenario(
        animal="goat",
        premise="was teaching preschoolers to count using an artichoke poster and a mattress-shaped number board",
        goal="help the children notice the goat's signals as carefully as the numbers",
        trouble="ten fast boings won loud applause but made the goat kick its empty bucket",
        evidence="The bucket clanged once, and the goat pressed itself against the far fence",
        repair="asked everyone for ten silent fingers, refilled the bucket, and counted the goat's slow chews instead",
        result="ten fingers lowered while the goat crunched its final mouthful",
    ),
    "kindness_prize": Scenario(
        animal="pony",
        premise="expected to receive the famous artichoke ribbon after a petting-zoo sound contest",
        goal="decide what the prize should mean after the contest went wrong",
        trouble="the winning mattress boom startled the pony and made another child drop the ribbon in the dust",
        evidence="Nobody cheered; the pony sidestepped each time someone raised a hand to clap",
        repair="apologized, brushed off the ribbon, and pinned it on the helper for keeping the pony calm",
        result="the children waved silently while the pony rested its chin above the clean ribbon",
    ),
}

OPENINGS = [
    "Morning sun striped the straw when {child} arrived at {place}.",
    "Just after the gates opened, {child} followed {helper} into {place}.",
    "A hand-painted QUIET FEET sign greeted {child} at {place}.",
    "At feeding time, {child} could hear hooves and buckets all across {place}.",
]

RESPONSES = [
    '"Watch the animal, not the audience," {helper} said. {child} nodded and {repair}.',
    '{child} whispered, "My joke caused that. I need to fix it." With {helper} nearby, {pronoun} {repair}.',
    '"First make it safe; then make it funny," said {helper}. So {child} {repair}.',
    '{child} took off the fame ribbon. "Being noticed is not the same as being helpful," {pronoun} said, then {repair}.',
]

ENDINGS = [
    "At closing time, {result}; the artichoke ribbon hung quietly from the mattress handle.",
    "Before leaving, {child} drew the peaceful {animal} beside a green artichoke, with the mattress folded in the corner.",
    "The final sound was {animal_noise}, followed by one careful {soft_sound}; nothing flinched, tipped, or ran away.",
    "In the last photograph, {result}, and {child}'s fame ribbon was almost hidden behind a bit of hay.",
]


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    prop = _safe_lookup(PROPS, params.prop)
    plan = _safe_lookup(SCENARIOS, params.scenario)
    animal_kind = plan.animal
    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        traits=["little", "careful", "proud"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_role if params.helper_role in {"mother", "father"} else "person",
        label=params.helper_name,
        traits=["calm", "patient"],
    ))
    animal_info = _safe_lookup(ANIMALS, animal_kind)
    animal = world.add(Entity(
        id=animal_kind,
        kind="animal",
        type=animal_info["kind"],
        label=animal_info["nickname"],
        traits=["small", "curious"],
        meters={},
        memes={},
    ))
    item = world.add(Entity(
        id=prop.id,
        kind="thing",
        type="prop",
        label=prop.label,
        phrase=prop.phrase,
        owner=child.id,
        caretaker=helper.id,
    ))

    child.memes["fame"] = 1.0
    child.meters["careful"] = 1.0

    animal_noise = animal_info["noise"]
    soft_sound = {"boing": "boop", "boop": "tap", "honk": "tap"}.get(params.sound_effect, "tap")
    opening = OPENINGS[params.opening_variant % len(OPENINGS)].format(
        child=child.id, helper=helper.id, place=setting.place
    )
    world.say(opening)
    world.say(
        f"{child.id} wore an artichoke-shaped ribbon from a school contest and carried a small mattress. "
        f"{child.pronoun().capitalize()} had a job: {child.pronoun()} {plan.premise}. "
        f"That little taste of fame also made {child.pronoun('object')} eager to add a performance."
    )
    world.say(f"The plan was to {plan.goal}.")

    world.para()
    world.say(f'At first came a neat "{soft_sound}." Then {child.id} tried "{sound_repeat(params.sound_effect)}!"')
    world.say(f"Because of that, {plan.trouble}.")
    animal.memes["startle"] = 1.0
    child.memes["embarrassment"] = 1.0
    world.fired.add(("sound", prop.id, animal.id))
    world.facts["repetition"] = True
    world.facts["sound_effect"] = params.sound_effect
    world.facts["animal_startled"] = True
    world.say(plan.evidence + ".")

    world.para()
    response = RESPONSES[params.response_variant % len(RESPONSES)].format(
        child=child.id,
        helper=helper.id,
        pronoun=child.pronoun(),
        repair=plan.repair,
    )
    world.say(response)
    world.say(f"The change worked: {plan.result}.")
    animal.memes["calm"] = 1.0
    helper.memes["gentleness"] = 1.0
    child.memes["care"] = 1.0
    world.fired.add(("reconcile", child.id, animal.id))

    world.para()
    ending = ENDINGS[params.ending_variant % len(ENDINGS)].format(
        child=child.id,
        animal=animal.label,
        animal_noise=animal_noise,
        soft_sound=soft_sound,
        result=plan.result,
    )
    world.say(ending)

    world.facts.update(
        child=child,
        helper=helper,
        animal=animal,
        prop=item,
        prop_cfg=prop,
        setting=setting,
        plan=plan,
        trouble=plan.trouble,
        evidence=plan.evidence,
        repair=plan.repair,
        result=plan.result,
        animal_noise=animal_noise,
        resolved=animal.memes.get("calm", 0.0) >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a complete petting-zoo story about a mattress, brief fame, an artichoke-shaped ribbon, useful sound effects, and a gentle repair.",
        f"Tell how {f['child'].id}'s repeated {f['prop_cfg'].sound} causes a problem for a {f['animal'].label}, then show the specific action that makes it calm again.",
        f"Write a child-friendly story in which {f['child'].id} learns that caring for an animal matters more than applause; end after {f['result']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    animal = _safe_fact(world, f, "animal")
    prop = _safe_fact(world, f, "prop_cfg")

    return [
        QAItem(
            question=f"What did {child.id} bring to the petting zoo?",
            answer=f"{child.id} brought {prop.phrase} and wore an artichoke-shaped fame ribbon from school. The mattress helped create the sound effect that caused the problem.",
        ),
        QAItem(
            question=f"How did the repeated sound cause trouble for the {animal.label}?",
            answer=f"The repeated {prop.sound} led to this problem: {f['trouble']}. {f['evidence']}.",
        ),
        QAItem(
            question=f"How did {child.id} and {helper.id} fix the awkward moment?",
            answer=f"{helper.id.capitalize()} helped {child.id} slow down and pay attention. {child.id} {f['repair']}, so {f['result']}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At first the {animal.label} was startled by the performance. By the end, {f['result']}, proving that {child.id}'s repair worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where children can meet and gently visit small farm animals.",
        ),
        QAItem(
            question="What is a sound effect?",
            answer="A sound effect is a special sound people make on purpose to seem funny, dramatic, or exciting.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making things friendly and okay again after a small problem or hurt feeling.",
        ),
        QAItem(
            question="Why can repetition make a sound funnier?",
            answer="Repetition can make a sound funnier because hearing the same sound again and again can feel playful and bouncy.",
        ),
        QAItem(
            question="What is an artichoke?",
            answer="An artichoke is a green vegetable with layers of leaves, and its name can sound a little funny and fancy.",
        ),
        QAItem(
            question="What is a mattress?",
            answer="A mattress is the soft thing you sleep on in a bed.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prop_at_risk(mattress, A) :- animal(A).
prop_at_risk(artichoke, A) :- animal(A).

needs_reconciliation(C, A) :- startled(A), child(C), animal(A).
good_story(P, C, A) :- place(P), prop(mattress), child(C), animal(A), prop_at_risk(mattress, A), needs_reconciliation(C, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = [asp.fact("child", "child")]
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for pid in PROPS:
        lines.append(asp.fact("prop", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
        lines.append(asp.fact("startled", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = sorted((p, "child", a) for p in SETTINGS for a in ANIMALS if valid_combo(p, "mattress", a))
    cl = asp_valid_combos()
    if set(py) == set(cl):
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("python:", py)
    print("clingo:", cl)
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Petting-zoo slice-of-life story world with sound effects and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--role", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "petting_zoo"
    prop = getattr(args, "prop", None) or "mattress"
    compatible_scenarios = [
        key for key, plan in SCENARIOS.items()
        if getattr(args, "animal", None) in {None, plan.animal}
    ]
    scenario = rng.choice(compatible_scenarios)
    animal = getattr(args, "animal", None) or SCENARIOS[scenario].animal
    if not valid_combo(place, prop, animal):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    requested_role = getattr(args, "role", None)
    helper = getattr(args, "helper", None)
    if helper is None and requested_role is not None:
        helper = "mom" if requested_role == "mother" else "dad"
    helper = helper or rng.choice(HELPERS)
    helper_role = requested_role or {
        "mom": "mother",
        "dad": "father",
    }.get(helper, "person")
    return StoryParams(
        place=place,
        child_name=name,
        child_gender=gender,
        helper_name=helper,
        helper_role=helper_role,
        prop=prop,
        sound_effect=_safe_lookup(PROPS, prop).sound,
        animal=animal,
        scenario=scenario,
        opening_variant=rng.randrange(len(OPENINGS)),
        response_variant=rng.randrange(len(RESPONSES)),
        ending_variant=rng.randrange(len(ENDINGS)),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def CURATED_PARAMS() -> list[StoryParams]:
    return [
        StoryParams(
            place="petting_zoo",
            child_name="Mina",
            child_gender="girl",
            helper_name="Mom",
            helper_role="mother",
            prop="mattress",
            sound_effect="boing",
            animal="goat",
        ),
        StoryParams(
            place="petting_zoo",
            child_name="Eli",
            child_gender="boy",
            helper_name="Dad",
            helper_role="father",
            prop="mattress",
            sound_effect="boing",
            animal="pony",
        ),
        StoryParams(
            place="petting_zoo",
            child_name="Ivy",
            child_gender="girl",
            helper_name="Zoe",
            helper_role="mother",
            prop="artichoke",
            sound_effect="boop",
            animal="rabbit",
        ),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED_PARAMS()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.prop} at {p.place} with {p.animal}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
