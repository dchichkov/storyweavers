#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py
===============================================================

A standalone story world for a tiny mythic tale about a child carrying an iced
offering to a hill shrine. The story's turn is driven by a foreshadowed danger:
heat or dry wind can spoil the icing before the gift reaches the shrine. The
resolution is driven by kindness: the child helps a small creature on the road,
and later that same creature returns the help in a way that fits the path.

Run it
------
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py --route sun_steps --helper swallow
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py --route ember_ridge --helper swallow
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py --all
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py --trace
    python storyworlds/worlds/gpt-5.4/icing_foreshadowing_kindness_myth.py --json
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    icing: str
    shape: str
    scent: str
    sensitivity: int
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
class Shrine:
    id: str
    label: str
    keeper: str
    blessing: str
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
class Route:
    id: str
    label: str
    path_text: str
    omen_text: str
    hazard: str
    danger_text: str
    foreshadow_text: str
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
class Helper:
    id: str
    label: str
    intro_text: str
    trouble_text: str
    kindness_text: str
    thanks_text: str
    aid_text: str
    solves: set[str] = field(default_factory=set)
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


def helper_fits_route(helper: Helper, route: Route) -> bool:
    return route.hazard in helper.solves


def danger_score(route: Route, offering: Offering) -> int:
    return offering.sensitivity + {"sun": 1, "dry_wind": 1, "hot_stone": 2}[route.hazard]


def explain_rejection(route: Route, helper: Helper) -> str:
    pretty = ", ".join(sorted(helper.solves))
    return (
        f"(No story: {helper.label} can help with {pretty}, but not with the "
        f"{route.hazard.replace('_', ' ')} danger on {route.label}. Kindness in this "
        f"world must return in a believable way, so choose a helper whose gift fits the path.)"
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for shrine_id in SHRINES:
        for offering_id in OFFERINGS:
            for route_id, route in ROUTES.items():
                for helper_id, helper in HELPERS.items():
                    if helper_fits_route(helper, route):
                        combos.append((shrine_id, offering_id, route_id, helper_id))
    return combos


def _r_heat_threat(world: World) -> list[str]:
    child = world.get("child")
    cake = world.get("offering")
    route = world.facts["route"]
    if child.meters["on_hazard"] < THRESHOLD:
        return []
    sig = ("hazard", route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cake.meters["threat"] += danger_score(route, world.facts["offering_cfg"])
    child.memes["worry"] += 1
    return ["__hazard__"]


def _r_drip(world: World) -> list[str]:
    cake = world.get("offering")
    if cake.meters["threat"] < 2 or cake.meters["cooled"] >= THRESHOLD:
        return []
    sig = ("drip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cake.meters["dripping"] += 1
    cake.meters["tilt"] += 1
    return ["__drip__"]


def _r_repay_kindness(world: World) -> list[str]:
    helper = world.get("helper")
    child = world.get("child")
    cake = world.get("offering")
    route = world.facts["route"]
    if helper.memes["gratitude"] < THRESHOLD:
        return []
    if child.meters["on_hazard"] < THRESHOLD:
        return []
    if not helper_fits_route(world.facts["helper_cfg"], route):
        return []
    sig = ("aid", helper.id, route.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.meters["aiding"] += 1
    cake.meters["cooled"] += 1
    if cake.meters["threat"] > 0:
        cake.meters["threat"] = max(0.0, cake.meters["threat"] - 3.0)
    if cake.meters["dripping"] > 0:
        cake.meters["saved"] += 1
    child.memes["relief"] += 1
    return ["__aid__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="heat_threat", tag="physical", apply=_r_heat_threat),
    Rule(name="drip", tag="physical", apply=_r_drip),
    Rule(name="repay_kindness", tag="social", apply=_r_repay_kindness),
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
    return produced


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["on_hazard"] += 1
    propagate(sim, narrate=False)
    cake = sim.get("offering")
    return {
        "threat": int(cake.meters["threat"]),
        "dripping": cake.meters["dripping"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, elder: Entity, offering: Offering, shrine: Shrine) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In the old hill country, when dawn still wore pearl-colored mist, "
        f"{child.id} was chosen to carry {offering.phrase} to {shrine.label}."
    )
    world.say(
        f"The little cake was {offering.shape}, and its {offering.icing} icing "
        f"shone softly. It smelled of {offering.scent}, as if morning itself had been baked into it."
    )
    world.say(
        f'{elder.id}, {child.id}\'s {elder.label_word}, laid the offering in {child.pronoun("possessive")} hands and said, '
        f'"Carry it gently for {shrine.keeper}, and walk with a clean heart."'
    )


def foreshadow(world: World, child: Entity, route: Route) -> None:
    pred = predict_risk(world)
    world.facts["predicted_threat"] = pred["threat"]
    world.facts["predicted_dripping"] = pred["dripping"]
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} set out by {route.path_text}. {route.omen_text}"
    )
    world.say(
        f"{route.foreshadow_text} {child.id} held the cake a little higher and walked on."
    )


def meet_helper(world: World, child: Entity, helper: Entity, helper_cfg: Helper) -> None:
    world.say(helper_cfg.intro_text)
    world.say(helper_cfg.trouble_text)
    child.memes["kindness"] += 1
    helper.memes["gratitude"] += 1
    helper.meters["helped"] += 1
    world.say(helper_cfg.kindness_text.replace("{child}", child.id))
    world.say(helper_cfg.thanks_text)


def enter_danger(world: World, child: Entity, route: Route) -> None:
    child.meters["on_hazard"] += 1
    produced = propagate(world, narrate=False)
    world.say(route.danger_text)
    if "__drip__" in produced or world.get("offering").meters["dripping"] >= THRESHOLD:
        world.say(
            "A bright bead of icing slipped down one side, and for a breath it looked as if the offering would arrive spoiled."
        )
    else:
        world.say(
            "The child felt the danger of the road pressing close, even before anything was lost."
        )


def repay(world: World, child: Entity, helper: Entity, helper_cfg: Helper) -> None:
    if helper.meters["aiding"] < THRESHOLD:
        return
    world.say(helper_cfg.aid_text.replace("{child}", child.id))
    if world.get("offering").meters["saved"] >= THRESHOLD:
        world.say(
            "The shining bead of icing stopped its fall and settled back into a sweet white curve."
        )


def arrival(world: World, child: Entity, shrine: Shrine, offering: Offering, helper_cfg: Helper) -> None:
    cake = world.get("offering")
    child.memes["joy"] += 1
    child.memes["reverence"] += 1
    world.say(
        f"At last {child.id} climbed to {shrine.label} and set down the {offering.label} before {shrine.keeper}."
    )
    if cake.meters["dripping"] >= THRESHOLD and cake.meters["saved"] >= THRESHOLD:
        world.say(
            f"The icing was no longer in danger. It glimmered a little unevenly, but it still looked like a gift made with care."
        )
    else:
        world.say(
            f"The icing still shone whole and fair, as if the road itself had bowed and let the gift pass."
        )
    world.say(
        f"Then {shrine.blessing} {shrine.ending_image}"
    )
    world.facts["moral"] = (
        f"In that valley people said that kindness walks ahead of a traveler and comes back at the steepest part of the road."
    )
    if helper_cfg.id == "swallow":
        world.say("High above, a small swallow drew one last silver circle in the sky.")
    elif helper_cfg.id == "tortoise":
        world.say("Near the stair, a little tortoise blinked as cool drops gathered in the moss.")
    else:
        world.say("From a crack in the stones, a cave cricket sang a thin, bright note of evening thanks.")


def tell(
    shrine: Shrine,
    offering: Offering,
    route: Route,
    helper_cfg: Helper,
    child_name: str = "Iria",
    child_type: str = "girl",
    elder_type: str = "mother",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label="the elder", role="elder"))
    helper = world.add(Entity(id="helper", kind="character", type="creature", label=helper_cfg.label, role="helper"))
    offering_ent = world.add(Entity(id="offering", kind="thing", type="cake", label=offering.label, role="offering"))
    offering_ent.meters["threat"] = 0.0
    offering_ent.meters["dripping"] = 0.0
    offering_ent.meters["cooled"] = 0.0
    offering_ent.meters["saved"] = 0.0
    child.meters["on_hazard"] = 0.0
    helper.meters["aiding"] = 0.0
    helper.meters["helped"] = 0.0
    child.memes["kindness"] = 0.0
    helper.memes["gratitude"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] = 0.0

    world.facts["child"] = child
    world.facts["elder"] = elder
    world.facts["helper"] = helper
    world.facts["offering"] = offering_ent
    world.facts["shrine"] = shrine
    world.facts["offering_cfg"] = offering
    world.facts["route"] = route
    world.facts["helper_cfg"] = helper_cfg

    opening(world, child, elder, offering, shrine)
    world.para()
    foreshadow(world, child, route)
    meet_helper(world, child, helper, helper_cfg)
    world.para()
    enter_danger(world, child, route)
    repay(world, child, helper, helper_cfg)
    world.para()
    arrival(world, child, shrine, offering, helper_cfg)

    world.facts["success"] = offering_ent.meters["cooled"] >= THRESHOLD
    world.facts["dripped"] = offering_ent.meters["dripping"] >= THRESHOLD
    world.facts["kindness_returned"] = helper.meters["aiding"] >= THRESHOLD
    return world


OFFERINGS = {
    "snow_cake": Offering(
        id="snow_cake",
        label="snow cake",
        phrase="a round snow cake with white icing",
        icing="white",
        shape="round as a small moon",
        scent="vanilla and sweet milk",
        sensitivity=1,
        tags={"icing", "cake"},
    ),
    "berry_cake": Offering(
        id="berry_cake",
        label="berry cake",
        phrase="a berry cake with pale pink icing",
        icing="pale pink",
        shape="round as a sunrise cloud",
        scent="berries and warm flour",
        sensitivity=1,
        tags={"icing", "berries"},
    ),
    "honey_cake": Offering(
        id="honey_cake",
        label="honey cake",
        phrase="a honey cake with gold-thread icing",
        icing="gold-thread",
        shape="round as a harvest drum",
        scent="honey and wheat",
        sensitivity=2,
        tags={"icing", "honey"},
    ),
}

SHRINES = {
    "dawn_well": Shrine(
        id="dawn_well",
        label="the Dawn Well",
        keeper="the Lady of First Light",
        blessing="the first sunlight spilled gently over the terraces, and the village cisterns filled clear and bright.",
        ending_image="Children ran barefoot to see little stars trembling in every bucket.",
        tags={"well", "dawn"},
    ),
    "moon_stone": Shrine(
        id="moon_stone",
        label="the Moon Stone",
        keeper="the Sleeper Beneath the Hill",
        blessing="a cool silver peace settled over the orchards, and no fruit fell too early that season.",
        ending_image="By evening the pears hung heavy and still, as if listening.",
        tags={"moon", "orchard"},
    ),
    "orchard_gate": Shrine(
        id="orchard_gate",
        label="the Orchard Gate",
        keeper="the Keeper of Blossoms",
        blessing="a sweet wind moved through the valley, and every tree opened one more ring of bloom.",
        ending_image="Petals drifted across the path like tiny boats.",
        tags={"orchard", "blossom"},
    ),
}

ROUTES = {
    "sun_steps": Route(
        id="sun_steps",
        label="the Sun Steps",
        path_text="the Sun Steps, where old stone climbed the hill in bright terraces",
        omen_text="Already the stair rails were warm, and pine sap on the trunks shone like drops of melted sugar.",
        hazard="sun",
        danger_text="Halfway up, the bare stones gathered the sun and threw it back in wavering gold. Heat breathed against the little cake.",
        foreshadow_text="It was the sort of morning when even strong icing might soften before noon, yet the child remembered the elder's charge.",
        tags={"sun", "heat"},
    ),
    "reed_path": Route(
        id="reed_path",
        label="the Reed Path",
        path_text="the Reed Path beside the marsh, where the dry stalks whispered around the ankles",
        omen_text="Though the sky was pale, the wind had no coolness in it, and the reeds hissed like thirsty paper.",
        hazard="dry_wind",
        danger_text="Soon a thin dry wind came racing over the marsh. It licked at the sweet top of the cake and tried to roughen the soft icing.",
        foreshadow_text="The elders said such wind could steal the shine from a sweet before the shrine bell heard your steps, and the omen felt true.",
        tags={"wind", "marsh"},
    ),
    "ember_ridge": Route(
        id="ember_ridge",
        label="Ember Ridge",
        path_text="Ember Ridge, a dark path of black stones above the fields",
        omen_text="Even in morning shadow, the rocks held night's buried warmth, and the air trembled just above them.",
        hazard="hot_stone",
        danger_text="When the ridge rose steeply, heat climbed out of the black stones in little waves. The warm breath of the earth pressed upward under the icing.",
        foreshadow_text="Grandmothers used to say that a careless traveler could lose a whole sweet to those stones before reaching the top, and the warning felt old and wise.",
        tags={"stone", "ridge", "heat"},
    ),
}

HELPERS = {
    "swallow": Helper(
        id="swallow",
        label="a swallow",
        intro_text="Near a fig tree, a swallow fluttered low and crooked instead of leaping into the sky.",
        trouble_text="One thin thorn-vine had caught around its wing, and each frightened beat only tightened the green thread.",
        kindness_text="{child} set the cake on a flat stone, loosened the vine with careful fingers, and lifted the swallow free.",
        thanks_text='The swallow shook its feathers and chirped as if saying, "I remember."',
        aid_text="Then the swallow called from above. Three more swallows came, wheeling wing to wing, and their circling shadows cooled the cake while {child} crossed the brightest stretch.",
        solves={"sun"},
        tags={"bird", "shade"},
    ),
    "tortoise": Helper(
        id="tortoise",
        label="a little tortoise",
        intro_text="By a split milestone, a little tortoise lay on its back, feet pawing slowly at the air.",
        trouble_text="Its shell had rolled against a root, and it could not turn itself on the dry ground.",
        kindness_text="{child} knelt in the dust, set the cake safely aside, and gently turned the little tortoise right side up.",
        thanks_text='The tortoise blinked once and stretched its neck, as if saying, "Slow feet remember good hands."',
        aid_text="Then the tortoise began to plod toward a crack between reeds. {child} followed and found a hidden spring there, cool enough to kiss the air. In that breath of water, the icing steadied.",
        solves={"dry_wind"},
        tags={"spring", "tortoise"},
    ),
    "cricket": Helper(
        id="cricket",
        label="a cave cricket",
        intro_text="At the foot of the ridge, a cave cricket scraped weakly beneath a fallen bit of shrine tile.",
        trouble_text="The shard pinned one bright leg, and the tiny singer could not hop back into the shade.",
        kindness_text="{child} balanced the cake on both knees, lifted the shard, and waited until the cricket slipped free into the cool crack of stone.",
        thanks_text='From the shadow came a clear little song, as if saying, "A kind road is never walked alone."',
        aid_text="Then the cricket sang again from a narrow cleft. Hidden there was a short cool passage through the ridge, and {child} crossed in stone shade until the black rocks could no longer trouble the icing.",
        solves={"hot_stone"},
        tags={"cave", "cricket", "shade"},
    ),
}

GIRL_NAMES = ["Iria", "Nema", "Sola", "Mira", "Tali", "Ena", "Lysa", "Rina"]
BOY_NAMES = ["Aren", "Tomas", "Lio", "Beren", "Niko", "Sami", "Darin", "Pavel"]


@dataclass
class StoryParams:
    shrine: str
    offering: str
    route: str
    helper: str
    child_name: str
    child_gender: str
    elder: str
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
    "icing": [
        (
            "What is icing?",
            "Icing is a sweet soft topping spread over a cake. Warm air can make it soften or slide if it is carried too long."
        )
    ],
    "bird": [
        (
            "Why can a bird make shade by flying overhead?",
            "When a bird flies between you and the sun, its body and wings block a little light. A flock can make a moving patch of shade for a moment."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that comes out of the ground by itself. Spring water is often cool, so the air around it can feel cooler too."
        )
    ],
    "cave": [
        (
            "Why can a cave or stone passage feel cool?",
            "Stone keeps out a lot of the sun's heat. That is why caves and shaded cracks often feel cooler than open ground."
        )
    ],
    "shade": [
        (
            "Why does shade help on a hot day?",
            "Shade blocks direct sunlight. Without the sun shining straight on something, it warms more slowly."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help someone, even when you are busy. In stories, kindness often changes what happens next because other hearts remember it."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story that feels larger than everyday life. It often explains why people honor certain places, seasons, or small acts."
        )
    ],
}
KNOWLEDGE_ORDER = ["icing", "shade", "bird", "spring", "cave", "kindness", "myth"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    shrine = world.facts["shrine"]
    route = world.facts["route"]
    helper = world.facts["helper_cfg"]
    offering = world.facts["offering_cfg"]
    return [
        f'Write a myth-like story for a 3-to-5-year-old that includes the word "icing" and begins with a child carrying an offering up a sacred path.',
        f"Tell a gentle myth where {child.label} carries {offering.phrase} to {shrine.label}, meets {helper.label}, and later kindness returns when the road turns hard.",
        f"Write a short story with foreshadowing on {route.label}, where the child notices an early sign of danger before the sweet offering is tested.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    shrine = world.facts["shrine"]
    route = world.facts["route"]
    helper = world.facts["helper_cfg"]
    offering = world.facts["offering_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child carrying {offering.phrase} to {shrine.label}. {elder.label_word.capitalize()} sends the child on the journey, and {helper.label} becomes important on the road."
        ),
        (
            "What was the child carrying?",
            f"{child.label} was carrying {offering.phrase}. The icing mattered because the road's heat or wind could spoil it before it reached the shrine."
        ),
        (
            "What was the early warning on the road?",
            f"The warning came from the way the path already felt before the real trouble began: {route.omen_text.lower()} That was foreshadowing, because it hinted that the offering might soon be in danger."
        ),
        (
            f"How did {child.label} show kindness?",
            f"{child.label} stopped to help {helper.label} instead of hurrying past. The child did that even while carrying a sacred gift, which shows the kindness was a real choice."
        ),
    ]
    if world.facts["kindness_returned"]:
        qa.append(
            (
                "How did kindness help later?",
                f"Later, when the road threatened the icing, the helper returned the good deed: {helper.aid_text.replace('{child}', child.label)} Because of that help, the offering could still be carried properly to the shrine."
            )
        )
    if world.facts["dripped"]:
        qa.append(
            (
                "Did the icing almost get ruined?",
                "Yes. A little bead of icing began to slip, which showed the danger was real. The helper's return of kindness stopped the trouble before the gift was lost."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the offering safely laid before {shrine.keeper}, and then {shrine.blessing} The ending image proves that a small kind act on the road became part of a larger blessing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"icing", "kindness", "myth"}
    tags |= set(world.facts["helper_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        shrine="dawn_well",
        offering="snow_cake",
        route="sun_steps",
        helper="swallow",
        child_name="Iria",
        child_gender="girl",
        elder="mother",
    ),
    StoryParams(
        shrine="moon_stone",
        offering="berry_cake",
        route="reed_path",
        helper="tortoise",
        child_name="Aren",
        child_gender="boy",
        elder="father",
    ),
    StoryParams(
        shrine="orchard_gate",
        offering="honey_cake",
        route="ember_ridge",
        helper="cricket",
        child_name="Mira",
        child_gender="girl",
        elder="mother",
    ),
]


ASP_RULES = r"""
fits(H, R) :- helper(H), route(R), solves(H, Z), hazard(R, Z).
valid(S, O, R, H) :- shrine(S), offering(O), route(R), helper(H), fits(H, R).

severity(O, R, V) :- sensitivity(O, S), hazard_weight(R, W), V = S + W.
drips(O, R) :- severity(O, R, V), V >= 3.
saved_by_kindness(R, H) :- fits(H, R).

outcome(saved) :- chosen_route(R), chosen_helper(H), saved_by_kindness(R, H).
would_drip :- chosen_route(R), chosen_offering(O), drips(O, R).
#show valid/4.
#show outcome/1.
#show would_drip/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for shrine_id in SHRINES:
        lines.append(asp.fact("shrine", shrine_id))
    for offering_id, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", offering_id))
        lines.append(asp.fact("sensitivity", offering_id, offering.sensitivity))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("hazard", route_id, route.hazard))
        lines.append(
            asp.fact(
                "hazard_weight",
                route_id,
                {"sun": 1, "dry_wind": 1, "hot_stone": 2}[route.hazard],
            )
        )
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for hazard in sorted(helper.solves):
            lines.append(asp.fact("solves", helper_id, hazard))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> tuple[str, bool]:
    import asp

    program = asp_program(
        extra="\n".join(
            [
                asp.fact("chosen_route", params.route),
                asp.fact("chosen_helper", params.helper),
                asp.fact("chosen_offering", params.offering),
            ]
        ),
        show="#show outcome/1.\n#show would_drip/0.",
    )
    model = asp.one_model(program)
    outcomes = asp.atoms(model, "outcome")
    would_drip = bool(asp.atoms(model, "would_drip"))
    return (outcomes[0][0] if outcomes else "?"), would_drip


def outcome_of(params: StoryParams) -> tuple[str, bool]:
    helper = HELPERS[params.helper]
    route = ROUTES[params.route]
    offering = OFFERINGS[params.offering]
    return ("saved" if helper_fits_route(helper, route) else "lost", danger_score(route, offering) >= 3)


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for s in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during resolve_params smoke case seed={s}")
            break

    mismatch = 0
    for params in cases:
        a_out, a_drip = asp_outcome(params)
        p_out, p_drip = outcome_of(params)
        if (a_out, a_drip) != (p_out, p_drip):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False)
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic story world: a child carries an iced offering, a path foreshadows danger, and kindness returns at the steep part of the road."
    )
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.helper:
        route = ROUTES[args.route]
        helper = HELPERS[args.helper]
        if not helper_fits_route(helper, route):
            raise StoryError(explain_rejection(route, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.shrine is None or combo[0] == args.shrine)
        and (args.offering is None or combo[1] == args.offering)
        and (args.route is None or combo[2] == args.route)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shrine_id, offering_id, route_id, helper_id = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father"])
    return StoryParams(
        shrine=shrine_id,
        offering=offering_id,
        route=route_id,
        helper=helper_id,
        child_name=name,
        child_gender=gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.shrine not in SHRINES:
        raise StoryError(f"(Unknown shrine: {params.shrine})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Unknown offering: {params.offering})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    shrine = SHRINES[params.shrine]
    offering = OFFERINGS[params.offering]
    route = ROUTES[params.route]
    helper = HELPERS[params.helper]
    if not helper_fits_route(helper, route):
        raise StoryError(explain_rejection(route, helper))

    world = tell(
        shrine=shrine,
        offering=offering,
        route=route,
        helper_cfg=helper,
        child_name=params.child_name,
        child_type=params.child_gender,
        elder_type=params.elder,
    )

    story = world.render().replace("child", params.child_name)
    story = story.replace("elder", params.elder.capitalize())
    return StorySample(
        params=params,
        story=story.replace("  ", " "),
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
        print(asp_program(show="#show valid/4.\n#show outcome/1.\n#show would_drip/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (shrine, offering, route, helper) combos:\n")
        for shrine, offering, route, helper in combos:
            print(f"  {shrine:12} {offering:11} {route:11} {helper}")
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
            header = f"### {p.child_name}: {p.offering} by {p.route} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
