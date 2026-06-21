#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py
================================================================

A standalone story world for tiny pirate tales about a rough treasure clue whose
texture must be transformed before it can be read.

Premise
-------
Two young pirates find something important -- a map scrap, a pennant, or a page
from the ship's log -- but seawater or muck has changed its texture. It feels
rough, stiff, or gritty, so the clue cannot yet unfold or show its hidden mark.
An eager child wants the answer right away. A wiser helper chooses a gentle
method that truly fits the material and the mess. As the texture changes, the
clue changes too: it softens, smooths, and finally reveals the path to a small
treasure.

The world model enforces that a transformation method must:
- treat the actual texture problem, and
- be gentle enough for the clue's material.

So a harsh scraping tool is known to the world but refused. A soggy rinse is
fine for cloth and leather, but not for fragile parchment. The story's turn
comes from the simulated change in texture, not from slot-swapped prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py --clue map --texture salt_crust
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py --method knife_scrape
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/texture_transformation_pirate_tale.py --verify
"""

from __future__ import annotations

import argparse
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "captain_f", "woman"}
        male = {"boy", "father", "captain_m", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.role == "captain":
            return "Captain"
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    stash: str
    finish: str
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
class Clue:
    id: str
    label: str
    phrase: str
    material: str
    fragility: int
    hideout: str
    reveal: str
    ending_image: str
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
class TextureProblem:
    id: str
    label: str
    meter_key: str
    feel: str
    blocks: str
    fixed: str
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
class Method:
    id: str
    label: str
    sense: int
    treats: set[str]
    max_fragility: int
    action: str
    transform: str
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


def _r_texture_yields(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    method = world.facts.get("method_cfg")
    texture = world.facts.get("texture_cfg")
    if clue.meters["treated"] < THRESHOLD or method is None or texture is None:
        return out
    sig = ("texture_yields", method.id, texture.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if texture.meter_key in clue.meters:
        clue.meters[texture.meter_key] = 0.0
    clue.meters["smooth"] += 1
    clue.meters["readable"] += 1
    helper = world.get("helper")
    seeker = world.get("seeker")
    helper.memes["wonder"] += 1
    seeker.memes["wonder"] += 1
    out.append("__transformed__")
    return out


def _r_mark_revealed(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["readable"] < THRESHOLD:
        return out
    sig = ("mark_revealed", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.attrs["mark_visible"] = True
    world.facts["mark_visible"] = True
    out.append("__mark__")
    return out


def _r_treasure_found(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if not clue.attrs.get("mark_visible"):
        return out
    sig = ("treasure_found", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chest = world.get("treasure")
    chest.attrs["found"] = True
    chest.meters["open"] += 1
    for eid in ("seeker", "helper", "captain"):
        world.get(eid).memes["joy"] += 1
    out.append("__treasure__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="texture_yields", tag="physical", apply=_r_texture_yields),
    Rule(name="mark_revealed", tag="discovery", apply=_r_mark_revealed),
    Rule(name="treasure_found", tag="resolution", apply=_r_treasure_found),
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


SETTINGS = {
    "cove": Setting(
        id="cove",
        place="a moon-bright cove",
        opening="The tide whispered around the rocks, and the little pirate skiff knocked softly against the sand.",
        stash="under a crooked plank beside a barrel of shells",
        finish="At the edge of the cove, the waves kept winking at them as if the sea itself knew the secret.",
        tags={"sea", "pirates"},
    ),
    "deck": Setting(
        id="deck",
        place="the sun-warmed deck",
        opening="The old pirate ship creaked gently, and gulls cried high above the mast.",
        stash="inside a coil of rope by the rail",
        finish="Up on deck, the pennant snapped happily in the wind while the ship rocked like it was dancing.",
        tags={"ship", "pirates"},
    ),
    "cabin": Setting(
        id="cabin",
        place="the captain's snug cabin",
        opening="Lantern light glowed on brass buttons and sea charts, and the ship hummed under the floorboards.",
        stash="behind a stack of chart tubes near the porthole",
        finish="In the warm cabin, the lantern shone on their prize and made it sparkle like a captured star.",
        tags={"ship", "lantern"},
    ),
}

CLUES = {
    "map": Clue(
        id="map",
        label="map scrap",
        phrase="a rolled parchment map scrap",
        material="parchment",
        fragility=1,
        hideout="rolled tight",
        reveal="a red X tucked beside a tiny island",
        ending_image="the small map lay smooth on the deck, with its red X bright as a berry",
        tags={"map", "parchment"},
    ),
    "pennant": Clue(
        id="pennant",
        label="pennant",
        phrase="a little cloth pennant",
        material="cloth",
        fragility=3,
        hideout="twisted up like a sleepy ribbon",
        reveal="a stitched compass rose in blue thread",
        ending_image="the pennant fluttered overhead, its compass rose finally clear",
        tags={"cloth", "flag"},
    ),
    "logpage": Clue(
        id="logpage",
        label="logbook page",
        phrase="a torn page from the captain's log",
        material="paper",
        fragility=2,
        hideout="folded into a hard little square",
        reveal="a dotted trail leading to a star-shaped shell",
        ending_image="the page rested flat in Captain's hand, and the dotted trail pointed true",
        tags={"paper", "logbook"},
    ),
}

TEXTURES = {
    "salt_crust": TextureProblem(
        id="salt_crust",
        label="salt crust",
        meter_key="crusted",
        feel="rough and crackly",
        blocks="the crust kept the clue from unfolding without a tear",
        fixed="the white crust melted away and left the surface soft enough to open",
        tags={"salt", "texture"},
    ),
    "mud_cake": TextureProblem(
        id="mud_cake",
        label="mud cake",
        meter_key="gritty",
        feel="lumpy and gritty",
        blocks="the dried mud hid the marks and made the clue feel like a little board",
        fixed="the grit washed off and the clue stopped feeling stiff and scratchy",
        tags={"mud", "texture"},
    ),
    "seaweed_slime": TextureProblem(
        id="seaweed_slime",
        label="seaweed slime",
        meter_key="sticky",
        feel="slick and sticky",
        blocks="the slime glued the folds together so the clue would not open cleanly",
        fixed="the sticky film slipped away and the clue opened without pulling",
        tags={"seaweed", "texture"},
    ),
}

METHODS = {
    "mist_and_wait": Method(
        id="mist_and_wait",
        label="a spray bottle and patient hands",
        sense=3,
        treats={"salt_crust", "seaweed_slime"},
        max_fragility=2,
        action="misted the clue with a few careful drops and waited while the stiff parts loosened",
        transform="The rough texture slowly changed under their fingers. What had felt hard and fussy began to feel gentle and bendy instead.",
        qa_text="used a little spray of water and waited for the clue to loosen",
        tags={"water", "patience"},
    ),
    "sponge_dab": Method(
        id="sponge_dab",
        label="a soft sea sponge",
        sense=3,
        treats={"salt_crust", "mud_cake", "seaweed_slime"},
        max_fragility=3,
        action="dabbed the clue with a soft sea sponge, lifting the mess a little at a time",
        transform="With each dab, the bad texture gave up. The clue stopped feeling gritty and started feeling smooth enough to read.",
        qa_text="dabbed it gently with a soft sea sponge",
        tags={"sponge", "gentle"},
    ),
    "rinse_and_pat": Method(
        id="rinse_and_pat",
        label="a rinse bucket and a drying cloth",
        sense=2,
        treats={"mud_cake", "seaweed_slime"},
        max_fragility=3,
        action="swished the clue quickly in fresh water and then patted it dry with a clean cloth",
        transform="The heavy mess slipped away, and the surface changed from sticky and lumpy to soft and flat.",
        qa_text="rinsed it and patted it dry",
        tags={"water", "cloth"},
    ),
    "knife_scrape": Method(
        id="knife_scrape",
        label="the little rope knife",
        sense=1,
        treats={"salt_crust", "mud_cake", "seaweed_slime"},
        max_fragility=3,
        action="scraped at the clue with the knife edge",
        transform="",
        qa_text="scraped at it with a knife",
        tags={"knife"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Nora", "Ava", "Elsie", "June", "Mina"]
BOY_NAMES = ["Finn", "Toby", "Ned", "Ollie", "Jory", "Bram", "Leo", "Hugh"]
HELPERS = [
    ("Pearl", "girl"),
    ("Kit", "boy"),
    ("Sailor May", "girl"),
    ("Pip", "boy"),
]
CAPTAINS = [
    ("Captain Mara", "captain_f"),
    ("Captain Reed", "captain_m"),
]


def clue_has_problem(clue: Clue, texture: TextureProblem) -> bool:
    return True


def method_is_sensible(method: Method) -> bool:
    return method.sense >= SENSE_MIN


def method_fits(clue: Clue, texture: TextureProblem, method: Method) -> bool:
    return (
        clue_has_problem(clue, texture)
        and texture.id in method.treats
        and clue.fragility <= method.max_fragility
        and method_is_sensible(method)
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for clue_id, clue in CLUES.items():
            for texture_id, texture in TEXTURES.items():
                for method_id, method in METHODS.items():
                    if method_fits(clue, texture, method):
                        combos.append((setting_id, clue_id, texture_id, method_id))
    return combos


def predict_success(world: World, method: Method) -> dict:
    sim = world.copy()
    sim.facts["method_cfg"] = method
    clue = sim.get("clue")
    clue.meters["treated"] += 1
    propagate(sim, narrate=False)
    return {
        "readable": clue.meters["readable"] >= THRESHOLD,
        "mark_visible": bool(sim.facts.get("mark_visible")),
    }


def introduce(world: World, seeker: Entity, helper: Entity, captain: Entity) -> None:
    world.say(
        f"{world.setting.opening} {seeker.id} and {helper.id} were the youngest pirates on the ship, "
        f"always first to sniff out a mystery and last to stop pretending."
    )
    world.say(
        f"That afternoon, they were hunting for treasure in {world.setting.place} while {captain.id} sorted ropes and hummed an old sea song."
    )


def discover(world: World, seeker: Entity, helper: Entity, clue_cfg: Clue, texture: TextureProblem) -> None:
    seeker.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"Then {seeker.id} found {clue_cfg.phrase} {world.setting.stash}. "
        f"It was {clue_cfg.hideout}, and when {seeker.pronoun()} touched it, it felt {texture.feel}."
    )
    world.say(
        f'"A clue!" {seeker.id} whispered. But {texture.blocks}.'
    )


def grab_too_fast(world: World, seeker: Entity, clue_cfg: Clue) -> None:
    seeker.memes["impatience"] += 1
    world.say(
        f'{seeker.id} tugged at the {clue_cfg.label} right away. "If I pull hard, maybe it will pop open," {seeker.pronoun()} said.'
    )


def warn(world: World, helper: Entity, seeker: Entity, clue_cfg: Clue, texture: TextureProblem, method: Method) -> None:
    pred = predict_success(world, method)
    helper.memes["caution"] += 1
    world.facts["predicted_readable"] = pred["readable"]
    world.say(
        f'{helper.id} caught {seeker.pronoun("possessive")} wrist. "Wait," {helper.pronoun()} said. '
        f'"That texture means the {clue_cfg.label} is still stuck. If we are gentle first, it can change instead of tearing."'
    )


def captain_helps(world: World, captain: Entity, method: Method) -> None:
    captain.memes["care"] += 1
    world.say(
        f'{captain.id} knelt beside them and nodded. "A good pirate does not fight every mystery," {captain.pronoun()} said. '
        f'"Sometimes the sea asks for patient hands. We will use {method.label}."'
    )


def apply_method(world: World, seeker: Entity, helper: Entity, captain: Entity, method: Method) -> None:
    clue = world.get("clue")
    world.facts["method_cfg"] = method
    clue.meters["treated"] += 1
    seeker.memes["trust"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"So the three of them {method.action}."
    )
    propagate(world, narrate=False)
    world.say(method.transform)


def reveal(world: World, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    if clue.attrs.get("mark_visible"):
        world.say(
            f"When the last bit of mess was gone, the clue opened all the way and showed {clue_cfg.reveal}."
        )


def follow_clue(world: World, seeker: Entity, helper: Entity, captain: Entity) -> None:
    treasure = world.get("treasure")
    if treasure.attrs.get("found"):
        world.say(
            f'{seeker.id} and {helper.id} followed the fresh mark across the planks and behind a rope chest. '
            f'There they found a tiny treasure box no bigger than a loaf of bread.'
        )
        world.say(
            f'{captain.id} lifted the lid, and inside lay three gold-colored buttons and a shell that shone like moonlight on water.'
        )


def ending(world: World, clue_cfg: Clue) -> None:
    world.say(
        f"Nobody yanked or scratched anymore. They had seen a hard, fussy clue turn soft and useful, and that felt like a little kind of magic."
    )
    world.say(
        f"In the end, {clue_cfg.ending_image}. {world.setting.finish}"
    )


def tell(
    setting: Setting,
    clue_cfg: Clue,
    texture: TextureProblem,
    method: Method,
    seeker_name: str = "Finn",
    seeker_gender: str = "boy",
    helper_name: str = "Lina",
    helper_gender: str = "girl",
    captain_name: str = "Captain Mara",
    captain_type: str = "captain_f",
) -> World:
    world = World(setting)
    seeker = world.add(Entity(
        id="seeker",
        kind="character",
        type=seeker_gender,
        label=seeker_name,
        role="seeker",
        traits=["eager", "brave"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        traits=["careful", "clever"],
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_type,
        label=captain_name,
        role="captain",
        traits=["calm", "wise"],
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type=clue_cfg.material,
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        attrs={"mark_visible": False},
    ))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="chest",
        label="treasure box",
        attrs={"found": False},
    ))

    clue.meters[texture.meter_key] = 1.0
    clue.meters["treated"] = 0.0
    clue.meters["smooth"] = 0.0
    clue.meters["readable"] = 0.0

    for actor in (seeker, helper, captain):
        actor.memes["joy"] = 0.0
        actor.memes["wonder"] = 0.0

    world.facts.update(
        setting=setting,
        clue_cfg=clue_cfg,
        texture_cfg=texture,
        method_cfg=None,
        seeker=seeker,
        helper=helper,
        captain=captain,
        mark_visible=False,
    )

    introduce(world, seeker, helper, captain)
    discover(world, seeker, helper, clue_cfg, texture)
    world.para()
    grab_too_fast(world, seeker, clue_cfg)
    warn(world, helper, seeker, clue_cfg, texture, method)
    captain_helps(world, captain, method)
    world.para()
    apply_method(world, seeker, helper, captain, method)
    reveal(world, clue_cfg)
    follow_clue(world, seeker, helper, captain)
    world.para()
    ending(world, clue_cfg)

    world.facts.update(
        transformed=clue.meters["smooth"] >= THRESHOLD,
        readable=clue.meters["readable"] >= THRESHOLD,
        found_treasure=treasure.attrs.get("found", False),
    )
    return world


KNOWLEDGE = {
    "texture": [
        (
            "What does texture mean?",
            "Texture is how something feels when you touch it, like rough, smooth, sticky, or soft. Different textures can tell you how to handle something."
        )
    ],
    "salt": [
        (
            "Why can salt make things feel rough?",
            "When seawater dries, little salt crystals can stay behind. Those crystals feel scratchy and can make cloth or paper stiff."
        )
    ],
    "mud": [
        (
            "Why does dried mud feel gritty?",
            "Dried mud is made of tiny bits of dirt that harden as the water leaves. That is why it can feel lumpy and scratchy."
        )
    ],
    "seaweed": [
        (
            "Why can seaweed slime make something sticky?",
            "Wet sea plants can leave a slippery coating behind. That coating can glue folds together until it is cleaned away."
        )
    ],
    "sponge": [
        (
            "Why is a soft sponge good for cleaning delicate things?",
            "A soft sponge lifts dirt without scraping hard. That makes it useful when something can rip or fray."
        )
    ],
    "patience": [
        (
            "Why does waiting sometimes help when you clean something?",
            "A little waiting gives water time to loosen what is stuck. Then you do not have to pull so hard."
        )
    ],
    "parchment": [
        (
            "What is parchment?",
            "Parchment is a writing material used long ago for maps and pages. It can grow stiff if it gets dry and crusty."
        )
    ],
    "map": [
        (
            "What does a treasure map do?",
            "A treasure map gives clues about where to look. It may use marks, pictures, or an X to point the way."
        )
    ],
    "flag": [
        (
            "What is a pennant?",
            "A pennant is a small flag. Pirates or sailors might tie one up high so it can flutter in the wind."
        )
    ],
    "logbook": [
        (
            "What is a captain's log?",
            "A captain's log is a record of what happened on a journey. It can hold notes about places, weather, and useful clues."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "texture",
    "salt",
    "mud",
    "seaweed",
    "sponge",
    "patience",
    "parchment",
    "map",
    "flag",
    "logbook",
]


@dataclass
class StoryParams:
    setting: str
    clue: str
    texture: str
    method: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    captain: str
    captain_type: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue_cfg: Clue = f["clue_cfg"]
    texture: TextureProblem = f["texture_cfg"]
    return [
        f'Write a short pirate tale for a 3-to-5-year-old that uses the word "texture" and includes a gentle transformation.',
        f"Tell a story where young pirates find {clue_cfg.phrase} that feels {texture.feel}, and they must change its texture before they can read the clue.",
        f"Write a child-facing treasure story in which patience and careful hands turn a ruined-looking clue into something useful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker: Entity = f["seeker"]
    helper: Entity = f["helper"]
    captain: Entity = f["captain"]
    clue_cfg: Clue = f["clue_cfg"]
    texture: TextureProblem = f["texture_cfg"]
    method: Method = f["method_cfg"] if f["method_cfg"] is not None else METHODS[world.facts.get("method_id", "sponge_dab")]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young pirates, {seeker.label} and {helper.label}, and {captain.label}, who helps them with a treasure clue."
        ),
        (
            "What did the pirates find?",
            f"They found {clue_cfg.phrase} hidden away. It mattered because it was really a clue, not just an old scrap."
        ),
        (
            "What was wrong with the clue?",
            f"It felt {texture.feel}, and {texture.blocks}. The bad texture was the problem they had to solve before the story could move on."
        ),
        (
            f"Why did {helper.label} stop {seeker.label} from pulling at it?",
            f"{helper.label} knew the clue was still stuck and could tear if {seeker.label} yanked it open. The safer plan was to change the texture first so the clue could open cleanly."
        ),
    ]
    if f.get("transformed"):
        qa.append(
            (
                "How did they change the clue?",
                f"They {method.qa_text}. That gentle method matched the clue's problem, so the rough texture changed instead of the clue being damaged."
            )
        )
        qa.append(
            (
                "What happened after the texture changed?",
                f"The clue became readable and showed {clue_cfg.reveal}. Because the mark appeared, the pirates could follow it to the little treasure box."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the pirates finding a small treasure and remembering to be gentle. The ending image proves the change: what began hard and troublesome ended smooth and useful."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    clue_cfg: Clue = f["clue_cfg"]
    texture: TextureProblem = f["texture_cfg"]
    method: Method = f["method_cfg"] if f["method_cfg"] is not None else METHODS["sponge_dab"]
    tags: set[str] = {"texture"}
    if texture.id == "salt_crust":
        tags.add("salt")
    if texture.id == "mud_cake":
        tags.add("mud")
    if texture.id == "seaweed_slime":
        tags.add("seaweed")
    if method.id == "sponge_dab":
        tags.add("sponge")
    if method.id == "mist_and_wait":
        tags.add("patience")
    if clue_cfg.id == "map":
        tags |= {"map", "parchment"}
    elif clue_cfg.id == "pennant":
        tags.add("flag")
    elif clue_cfg.id == "logpage":
        tags.add("logbook")

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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cove",
        clue="map",
        texture="salt_crust",
        method="mist_and_wait",
        seeker="Finn",
        seeker_gender="boy",
        helper="Lina",
        helper_gender="girl",
        captain="Captain Mara",
        captain_type="captain_f",
    ),
    StoryParams(
        setting="deck",
        clue="pennant",
        texture="mud_cake",
        method="rinse_and_pat",
        seeker="Mira",
        seeker_gender="girl",
        helper="Pip",
        helper_gender="boy",
        captain="Captain Reed",
        captain_type="captain_m",
    ),
    StoryParams(
        setting="cabin",
        clue="logpage",
        texture="seaweed_slime",
        method="sponge_dab",
        seeker="Ned",
        seeker_gender="boy",
        helper="Tess",
        helper_gender="girl",
        captain="Captain Mara",
        captain_type="captain_f",
    ),
    StoryParams(
        setting="deck",
        clue="map",
        texture="salt_crust",
        method="sponge_dab",
        seeker="Ava",
        seeker_gender="girl",
        helper="Kit",
        helper_gender="boy",
        captain="Captain Reed",
        captain_type="captain_m",
    ),
]


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(mid for mid, m in METHODS.items() if method_is_sensible(m)))
    return (
        f"(Refusing method '{method_id}': it is too harsh or foolish for this world "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of the gentler methods: {better}.)"
    )


def explain_rejection(clue: Clue, texture: TextureProblem, method: Method) -> str:
    if not method_is_sensible(method):
        return explain_method(method.id)
    if texture.id not in method.treats:
        return (
            f"(No story: {method.label} does not really solve {texture.label}. "
            f"The transformation must fit the actual texture problem.)"
        )
    if clue.fragility > method.max_fragility:
        return (
            f"(No story: {method.label} is too rough or too wet for {clue.phrase}. "
            f"The clue is too delicate for that method.)"
        )
    return "(No story: this combination does not make sense in the world.)"


ASP_RULES = r"""
sensible_method(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.
fits_material(C, M) :- clue(C), method(M), fragility(C, F), max_fragility(M, Max), F <= Max.
treats_problem(M, T) :- method(M), treats(M, T).

valid(S, C, T, M) :- setting(S), clue(C), texture(T), method(M),
                     sensible_method(M), treats_problem(M, T), fits_material(C, M).

#show valid/4.
#show sensible_method/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("fragility", cid, clue.fragility))
    for tid in TEXTURES:
        lines.append(asp.fact("texture", tid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("max_fragility", mid, method.max_fragility))
        for texture_id in sorted(method.treats):
            lines.append(asp.fact("treats", mid, texture_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: young pirates transform the texture of a clue so it can be read."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--texture", choices=TEXTURES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--seeker")
    ap.add_argument("--helper")
    ap.add_argument("--captain", choices=[name for name, _ in CAPTAINS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def _pick_helper(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    choices = [(n, g) for (n, g) in HELPERS if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and not method_is_sensible(METHODS[args.method]):
        raise StoryError(explain_method(args.method))
    if args.clue and args.texture and args.method:
        clue = CLUES[args.clue]
        texture = TEXTURES[args.texture]
        method = METHODS[args.method]
        if not method_fits(clue, texture, method):
            raise StoryError(explain_rejection(clue, texture, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.clue is None or combo[1] == args.clue)
        and (args.texture is None or combo[2] == args.texture)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, clue_id, texture_id, method_id = rng.choice(sorted(combos))
    seeker_name, seeker_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_helper(rng, avoid=seeker_name)
    if args.seeker:
        seeker_name = args.seeker
        seeker_gender = "girl" if seeker_name in GIRL_NAMES else "boy"
    if args.helper:
        helper_name = args.helper
        helper_gender = "girl" if args.helper in GIRL_NAMES or args.helper in {"Pearl", "Sailor May"} else "boy"
    captain_name, captain_type = rng.choice(CAPTAINS)
    if args.captain:
        found = [(n, t) for (n, t) in CAPTAINS if n == args.captain]
        captain_name, captain_type = found[0]
    return StoryParams(
        setting=setting_id,
        clue=clue_id,
        texture=texture_id,
        method=method_id,
        seeker=seeker_name,
        seeker_gender=seeker_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        captain=captain_name,
        captain_type=captain_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.texture not in TEXTURES:
        raise StoryError(f"(Unknown texture: {params.texture})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    clue = CLUES[params.clue]
    texture = TEXTURES[params.texture]
    method = METHODS[params.method]
    if not method_fits(clue, texture, method):
        raise StoryError(explain_rejection(clue, texture, method))

    world = tell(
        setting=SETTINGS[params.setting],
        clue_cfg=clue,
        texture=texture,
        method=method,
        seeker_name=params.seeker,
        seeker_gender=params.seeker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        captain_name=params.captain,
        captain_type=params.captain_type,
    )
    world.facts["method_cfg"] = method
    world.facts["method_id"] = params.method
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


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sense = set(asp_sensible_methods())
    p_sense = {mid for mid, method in METHODS.items() if method_is_sensible(method)}
    if c_sense == p_sense:
        print(f"OK: sensible methods match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(sample, trace=True, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default-resolved story was empty")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible_methods())}\n")
        print(f"{len(combos)} valid (setting, clue, texture, method) combos:\n")
        for setting_id, clue_id, texture_id, method_id in combos:
            print(f"  {setting_id:7} {clue_id:8} {texture_id:13} {method_id}")
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
            header = f"### {p.setting}: {p.clue} with {p.texture} via {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
