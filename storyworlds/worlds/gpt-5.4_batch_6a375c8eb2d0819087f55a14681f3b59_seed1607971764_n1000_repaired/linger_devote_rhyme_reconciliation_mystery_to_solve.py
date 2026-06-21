#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py
==================================================================================

A standalone storyworld for a tall-tale mystery: two children devote themselves
to opening a grand little-town festival, the key festival item vanishes, one
child wrongly blames the other, and the pair must solve the mystery by reading
real clues. The ending always includes reconciliation, and the mystery is solved
through state, not by swapping nouns in a frozen paragraph.

The world is deliberately small and constraint-checked:

- a setting hosts only some giant-animal helpers,
- each missing item has a material/weight,
- each helper only plausibly takes some materials and only up to a carry limit.

So the mystery is only generated when the helper could honestly have taken the
item. The clue trail, the false accusation, the apology, and the final festival
celebration all read back from simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py --json --qa
    python storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py --asp
    python storyworlds/worlds/gpt-5.4/linger_devote_rhyme_reconciliation_mystery_to_solve.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    tall_line: str
    hideout: str
    hosts: set[str] = field(default_factory=set)
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
    material: str
    weight: int
    use_line: str
    opening_action: str
    replacement: str
    found_use: str
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
class Helper:
    id: str
    label: str
    phrase: str
    prefers: set[str] = field(default_factory=set)
    carry: int = 1
    clue: str = ""
    red_herring: str = ""
    motive: str = ""
    trade_offer: str = ""
    return_line: str = ""
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
class StoryParams:
    setting: str
    item: str
    helper: str
    accuser: str
    accuser_gender: str
    blamed: str
    blamed_gender: str
    elder_name: str
    elder_type: str
    relation: str = "friends"
    trust: int = 6
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


def _r_missing_delay(world: World) -> list[str]:
    item = world.get("item")
    square = world.get("square")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_delay",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square.meters["delay"] += 1
    for eid in ("accuser", "blamed"):
        world.get(eid).memes["worry"] += 1
    return ["__delay__"]


def _r_accusation_hurts(world: World) -> list[str]:
    accuser = world.get("accuser")
    blamed = world.get("blamed")
    if accuser.memes["accused"] < THRESHOLD or blamed.memes["blamed"] < THRESHOLD:
        return []
    sig = ("accusation_hurts",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    blamed.memes["hurt"] += 1
    accuser.memes["certainty"] += 1
    accuser.memes["rift"] += 1
    blamed.memes["rift"] += 1
    return ["__hurt__"]


def _r_truth_brings_guilt(world: World) -> list[str]:
    accuser = world.get("accuser")
    item = world.get("item")
    if accuser.memes["accused"] < THRESHOLD or item.meters["found"] < THRESHOLD:
        return []
    sig = ("truth_brings_guilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["guilt"] += 1
    return ["__guilt__"]


def _r_return_brings_relief(world: World) -> list[str]:
    item = world.get("item")
    square = world.get("square")
    if item.meters["returned"] < THRESHOLD:
        return []
    sig = ("return_brings_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    square.meters["delay"] = 0.0
    for eid in ("accuser", "blamed"):
        kid = world.get(eid)
        kid.memes["relief"] += 1
        kid.memes["hope"] += 1
    return ["__relief__"]


def _r_apology_mends(world: World) -> list[str]:
    accuser = world.get("accuser")
    blamed = world.get("blamed")
    if accuser.memes["apologized"] < THRESHOLD or blamed.memes["forgave"] < THRESHOLD:
        return []
    sig = ("apology_mends",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    accuser.memes["rift"] = 0.0
    blamed.memes["rift"] = 0.0
    accuser.memes["peace"] += 1
    blamed.memes["peace"] += 1
    blamed.memes["hurt"] = 0.0
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="missing_delay", tag="physical", apply=_r_missing_delay),
    Rule(name="accusation_hurts", tag="social", apply=_r_accusation_hurts),
    Rule(name="truth_brings_guilt", tag="social", apply=_r_truth_brings_guilt),
    Rule(name="return_brings_relief", tag="social", apply=_r_return_brings_relief),
    Rule(name="apology_mends", tag="social", apply=_r_apology_mends),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in out:
            world.say(sent)
    return out


SETTINGS = {
    "mesa": Setting(
        id="mesa",
        place="the red mesa fairground",
        tall_line="The red mesa rose so high that the sunrise had to climb it in two trips.",
        hideout="the weather vane on the tallest hay tower",
        hosts={"magpie", "goose"},
        tags={"mesa", "festival"},
    ),
    "riverbend": Setting(
        id="riverbend",
        place="the riverbend commons",
        tall_line="At Riverbend the creek bragged louder than a brass band and still nobody told it to hush.",
        hideout="the willow dam by the bend",
        hosts={"beaver", "goose"},
        tags={"river", "festival"},
    ),
    "windmill": Setting(
        id="windmill",
        place="the old windmill green",
        tall_line="The old windmill on the green was so tall it combed the clouds before breakfast.",
        hideout="the weather vane above the mill roof",
        hosts={"magpie", "beaver"},
        tags={"windmill", "festival"},
    ),
}

ITEMS = {
    "clapper": MissingItem(
        id="clapper",
        label="rhyme bell clapper",
        phrase="the brass rhyme bell clapper",
        material="shiny",
        weight=1,
        use_line="Without it, the giant bell could not sing the first rhyme of the day.",
        opening_action="strike the bell until the whole town chimed along",
        replacement="a polished tin lid",
        found_use="hung it beside a nest so it flashed and tinkled in the breeze",
        tags={"bell", "shiny"},
    ),
    "spoon": MissingItem(
        id="spoon",
        label="echo spoon",
        phrase="the long cedar echo spoon",
        material="wood",
        weight=2,
        use_line="Without it, the jam kettle could not be stirred for the opening feast.",
        opening_action="stir the kettle so the berry steam rolled over the town",
        replacement="a bundle of smooth willow sticks",
        found_use="wedged it into a leak in the dam where water had been nibbling through",
        tags={"spoon", "wood"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="chorus ribbon spool",
        phrase="the bright silk chorus ribbon spool",
        material="soft",
        weight=1,
        use_line="Without it, the parade kite tails could not be tied on for the opening march.",
        opening_action="tie the kite tails so they sang above the rooftops",
        replacement="a wagonful of soft straw",
        found_use="tucked long loops of it into a nest as soft lining",
        tags={"ribbon", "soft"},
    ),
}

HELPERS = {
    "magpie": Helper(
        id="magpie",
        label="giant magpie",
        phrase="a giant magpie",
        prefers={"shiny"},
        carry=1,
        clue="silver-black feathers and little flashes of light",
        red_herring="a shiny marble peeking from a pocket",
        motive="anything bright enough to wink back at the sun",
        trade_offer="the elder held up a polished lid that gleamed almost as brightly",
        return_line="The big bird cocked its head, accepted the trade, and dropped the clapper down as neatly as a spoon into a teacup.",
        tags={"magpie", "bird"},
    ),
    "beaver": Helper(
        id="beaver",
        label="beaver",
        phrase="a beaver broad as a porch swing",
        prefers={"wood"},
        carry=2,
        clue="wet tooth marks and little fan-shaped tail swipes in the mud",
        red_herring="muddy boots from the creek bank",
        motive="anything wooden that might patch, prop, or improve a dam",
        trade_offer="the elder rolled over a bundle of willow sticks, straight and fresh-cut",
        return_line="The beaver slapped the water once, took the willow bundle, and nudged the spoon free with a splash big enough to rinse the fence.",
        tags={"beaver", "river"},
    ),
    "goose": Helper(
        id="goose",
        label="giant goose",
        phrase="a giant goose",
        prefers={"soft"},
        carry=1,
        clue="downy feathers and long, sweeping nest tracks",
        red_herring="a white feather stuck to a sleeve",
        motive="anything soft enough to make eggs feel like they were sleeping on clouds",
        trade_offer="the elder came puffing with a cart piled high with fresh straw",
        return_line="The goose gave a proud honk, nosed the ribbon loose, and tucked the straw into the nest instead.",
        tags={"goose", "bird"},
    ),
}

GIRL_NAMES = ["Mira", "June", "Tessa", "Ruby", "Nell", "Clara", "Della", "Wren"]
BOY_NAMES = ["Eli", "Bo", "Jasper", "Otis", "Finn", "Cal", "Milo", "Ned"]
ELDER_NAMES = ["Aunt Maple", "Uncle Reed", "Mayor Thimble", "Granny Wren"]
TRAITS = ["bold", "careful", "quick-eyed", "stout-hearted", "cheerful"]


def helper_can_take(item: MissingItem, helper: Helper) -> bool:
    return item.material in helper.prefers and item.weight <= helper.carry


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for hid, helper in HELPERS.items():
                if hid in setting.hosts and helper_can_take(item, helper):
                    combos.append((sid, iid, hid))
    return sorted(combos)


def tone_of(params: StoryParams) -> str:
    return "warm" if params.relation == "siblings" or params.trust >= 6 else "earned"


def explain_combo_rejection(setting: Setting, item: MissingItem, helper: Helper) -> str:
    if helper.id not in setting.hosts:
        return (
            f"(No story: {helper.label} does not live around {setting.place}, so it "
            f"cannot honestly be the mystery helper there.)"
        )
    if item.weight > helper.carry:
        return (
            f"(No story: {helper.label} could not carry {item.phrase}; the mystery "
            f"needs a helper that can really move the missing thing.)"
        )
    return (
        f"(No story: {helper.label} would not take {item.phrase}. This helper looks "
        f"for {sorted(helper.prefers)}, not {item.material} things.)"
    )


def rhyme_couplet(helper: Helper, setting: Setting, item: MissingItem) -> str:
    if helper.id == "magpie":
        return (
            f'"If something bright has flown from sight, climb high and follow every light. '
            f'Where metal gleams and feathers play, the answer may not be far away."'
        )
    if helper.id == "beaver":
        return (
            f'"Where muddy nibbles mark the wood, look by the water holding good. '
            f'If creek tracks sweep and willow bends, the mystery waits where river mends."'
        )
    return (
        f'"When soft things stray and feathers drift, seek out the nest on the windy lift. '
        f'Where down lies thick and honkers rest, a missing piece may line a nest."'
    )


def opening_rhyme(item: MissingItem) -> str:
    if item.id == "clapper":
        return '"Ring and sing, clang and cling, wake the town with a chiming swing!"'
    if item.id == "spoon":
        return '"Stir and steam, berry gleam, wake the town with a breakfast dream!"'
    return '"Tie and fly, stream the sky, wake the town where the kites roll by!"'


def investigate(world: World, helper: Helper, setting: Setting, item: MissingItem) -> dict:
    sim = world.copy()
    sim.get("item").meters["found"] += 1
    return {
        "findable": helper_can_take(item, helper) and helper.id in setting.hosts,
        "hideout": setting.hideout,
        "clue": helper.clue,
    }


def introduce(world: World, accuser: Entity, blamed: Entity, elder: Entity, item: MissingItem) -> None:
    relation = world.facts["relation_phrase"]
    world.say(setting_text(world.setting))
    world.say(
        f"{accuser.id} and {blamed.id} were {relation} who had promised to devote the whole morning "
        f"to the festival opening. Their job was simple only in the way a mountain is simple: "
        f"they had to {item.opening_action} before the crowd grew noisy."
    )
    world.say(opening_rhyme(item))


def setting_text(setting: Setting) -> str:
    return f"In {setting.place}, {setting.tall_line}"


def discover_missing(world: World, accuser: Entity, blamed: Entity, item: MissingItem) -> None:
    thing = world.get("item")
    thing.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the two children reached the festival table, {item.phrase} was gone. "
        f"{item.use_line}"
    )
    world.say(
        f"For one long breath they both just stared, as if the empty space might fill itself "
        f"out of pure wishing."
    )


def false_accuse(world: World, accuser: Entity, blamed: Entity, helper: Helper) -> None:
    accuser.memes["accused"] += 1
    blamed.memes["blamed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {accuser.id} noticed {helper.red_herring} on {blamed.id} and jumped to the wrong idea. "
        f'"You took it!" {accuser.id} blurted.'
    )
    world.say(
        f"{blamed.id}'s face fell. "
        f'"I did not," {blamed.pronoun()} said, very quiet. "I was helping, same as you."'
    )


def linger_line(world: World, blamed: Entity) -> None:
    if blamed.memes["hurt"] >= THRESHOLD:
        world.say(
            f"The hurt on {blamed.id}'s face tried to linger, and for a moment the morning sagged."
        )


def clue_guide(world: World, elder: Entity, helper: Helper, setting: Setting, item: MissingItem) -> None:
    pred = investigate(world, helper, setting, item)
    world.facts["predicted_findable"] = pred["findable"]
    world.facts["predicted_hideout"] = pred["hideout"]
    world.say(
        f"Just then {elder.id} tipped {elder.pronoun('possessive')} hat, studied the ground, and said, "
        f"{rhyme_couplet(helper, setting, item)}"
    )
    world.say(
        f"{accusation_result_phrase(world)} Instead of arguing again, the children bent low and looked for real clues."
    )


def accusation_result_phrase(world: World) -> str:
    blamed = world.get("blamed")
    return (
        f"{blamed.id} could have stomped off then and there, but {blamed.pronoun()} stayed"
        if blamed.memes["hurt"] >= THRESHOLD
        else "Nobody ran away"
    )


def follow_clues(world: World, accuser: Entity, blamed: Entity, helper: Helper, setting: Setting) -> None:
    world.say(
        f"Soon they found {helper.clue} leading away from the table and toward {setting.hideout}. "
        f"Each step made the truth bigger and the false guess smaller."
    )


def find_helper(world: World, helper_ent: Entity, item_ent: Entity, helper: Helper, item: MissingItem, setting: Setting) -> None:
    item_ent.meters["found"] += 1
    item_ent.attrs["found_at"] = setting.hideout
    item_ent.attrs["found_use"] = item.found_use
    helper_ent.meters["holding_item"] += 1
    propagate(world, narrate=False)
    world.say(
        f"There at {setting.hideout} they found {helper.phrase}. It had {item.found_use}."
    )
    world.say(
        f"It was no thief in a black mask at all, only a busy creature following {helper.pronoun('possessive')} own giant idea of usefulness."
    )


def trade_and_return(world: World, elder: Entity, helper_ent: Entity, item_ent: Entity, helper: Helper) -> None:
    item_ent.meters["returned"] += 1
    item_ent.meters["missing"] = 0.0
    helper_ent.meters["holding_item"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{elder.id} did not scold. {helper.trade_offer}. {helper.return_line}"
    )


def apologize(world: World, accuser: Entity, blamed: Entity, tone: str) -> None:
    accuser.memes["apologized"] += 1
    blamed.memes["forgave"] += 1
    propagate(world, narrate=False)
    if tone == "warm":
        world.say(
            f'{accuser.id} picked up {blamed.id}\'s hand and said, '
            f'"I was wrong, and I am sorry I blamed you before I knew the truth."'
        )
        world.say(
            f'{blamed.id} squeezed back at once. "Next time we look first and guess later," '
            f'{blamed.pronoun()} said.'
        )
    else:
        world.say(
            f"{accuser.id} looked so ashamed that even the wind seemed to hush. "
            f'"I was wrong," {accuser.pronoun()} said. "I let one little clue grow too big, '
            f'and I hurt you. I am truly sorry."'
        )
        world.say(
            f"{blamed.id} let the silence sit for one steady heartbeat, then nodded. "
            f'"I was hurt," {blamed.pronoun()} said, "but I know you came after the truth. '
            f'Let us finish the job together."'
        )


def celebrate(world: World, accuser: Entity, blamed: Entity, elder: Entity, item: MissingItem) -> None:
    world.say(
        f"With {item.phrase} back in place, the festival sprang forward like a colt over a fence."
    )
    world.say(
        f"{accuser.id} and {blamed.id} finished the opening together while {elder.id} laughed into "
        f"{elder.pronoun('possessive')} sleeve."
    )
    if item.id == "clapper":
        world.say(
            "When the bell rang out, windows hummed, pie tins shivered, and even the scarecrows looked ready to dance."
        )
    elif item.id == "spoon":
        world.say(
            "When the spoon swept the kettle, berry steam rolled so high that the clouds came down for a sniff."
        )
    else:
        world.say(
            "When the ribbons flew, the kites tugged at the sky until the blue itself seemed stitched in place."
        )
    world.say(
        f"Nobody let the quarrel linger after that. The children stood shoulder to shoulder and sang, "
        f'"Clue by clue and friend by friend, we mend the start and mend the end!"'
    )


def relation_phrase(relation: str, accuser: Entity, blamed: Entity) -> str:
    if relation == "siblings":
        if accuser.type == "boy" and blamed.type == "boy":
            return "brothers"
        if accuser.type == "girl" and blamed.type == "girl":
            return "sisters"
        return "brother and sister"
    return "best friends"


def tell(
    setting: Setting,
    item: MissingItem,
    helper: Helper,
    *,
    accuser_name: str,
    accuser_gender: str,
    blamed_name: str,
    blamed_gender: str,
    elder_name: str,
    elder_type: str,
    relation: str,
    trust: int,
) -> World:
    world = World(setting)
    accuser = world.add(Entity(id="accuser", kind="character", type=accuser_gender, label=accuser_name, role="accuser"))
    blamed = world.add(Entity(id="blamed", kind="character", type=blamed_gender, label=blamed_name, role="blamed"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_name, role="elder"))
    square = world.add(Entity(id="square", type="place", label=setting.place))
    item_ent = world.add(Entity(id="item", type="tool", label=item.label, tags=set(item.tags)))
    helper_ent = world.add(Entity(id="helper", type="animal", label=helper.label, tags=set(helper.tags)))

    world.facts.update(
        relation=relation,
        relation_phrase=relation_phrase(relation, accuser, blamed),
        trust=trust,
        setting=setting,
        item_cfg=item,
        helper_cfg=helper,
        tone=tone_of(
            StoryParams(
                setting=setting.id,
                item=item.id,
                helper=helper.id,
                accuser=accuser_name,
                accuser_gender=accuser_gender,
                blamed=blamed_name,
                blamed_gender=blamed_gender,
                elder_name=elder_name,
                elder_type=elder_type,
                relation=relation,
                trust=trust,
                seed=None,
            )
        ),
    )

    accuser.attrs["name"] = accuser_name
    blamed.attrs["name"] = blamed_name
    elder.attrs["name"] = elder_name

    accuser.memes["devotion"] = 1.0
    blamed.memes["devotion"] = 1.0
    accuser.memes["trust"] = float(trust)
    blamed.memes["trust"] = float(trust)
    elder.memes["calm"] = 1.0
    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] = 0.0
    item_ent.meters["returned"] = 0.0
    helper_ent.meters["holding_item"] = 0.0
    square.meters["delay"] = 0.0

    introduce(world, accuser, blamed, elder, item)
    world.para()
    discover_missing(world, accuser, blamed, item)
    false_accuse(world, accuser, blamed, helper)
    linger_line(world, blamed)

    world.para()
    clue_guide(world, elder, helper, setting, item)
    follow_clues(world, accuser, blamed, helper, setting)
    find_helper(world, helper_ent, item_ent, helper, item, setting)

    world.para()
    trade_and_return(world, elder, helper_ent, item_ent, helper)
    apologize(world, accuser, blamed, world.facts["tone"])
    celebrate(world, accuser, blamed, elder, item)

    world.facts.update(
        accuser=accuser,
        blamed=blamed,
        elder=elder,
        square=square,
        item=item_ent,
        helper=helper_ent,
        solved=item_ent.meters["found"] >= THRESHOLD,
        returned=item_ent.meters["returned"] >= THRESHOLD,
        reconciled=accuser.memes["peace"] >= THRESHOLD and blamed.memes["peace"] >= THRESHOLD,
        hideout=setting.hideout,
    )
    return world


KNOWLEDGE = {
    "bell": [
        (
            "What does a bell clapper do?",
            "A bell clapper is the part inside a bell that strikes and makes the ringing sound. Without it, a bell looks like a bell but cannot sing properly.",
        )
    ],
    "spoon": [
        (
            "Why would a long wooden spoon be useful near a kettle?",
            "A long spoon lets you stir from farther away, so your hands do not have to get too close to the hot steam. Wooden tools also float and are easy to grip.",
        )
    ],
    "ribbon": [
        (
            "Why do people tie ribbons to kites or parade things?",
            "Ribbons flutter and show the wind, so they make movement easy to see. They also add color and make a parade feel festive.",
        )
    ],
    "magpie": [
        (
            "Why do magpies notice shiny things?",
            "Magpies are curious birds, and bright objects catch their eyes because they flash in the light. A shiny thing can look special even if it does not belong in a nest.",
        )
    ],
    "beaver": [
        (
            "Why do beavers carry wood?",
            "Beavers use wood to build and patch their homes and dams. A wooden thing can look like useful building material to a busy beaver.",
        )
    ],
    "goose": [
        (
            "Why would a goose want something soft for a nest?",
            "Soft nest lining helps keep eggs warm and cushioned. A goose looks for comfort and safety, not for a parade.",
        )
    ],
    "apology": [
        (
            "What makes an apology good?",
            "A good apology says what went wrong and admits the harm honestly. It also shows you want to do better next time.",
        )
    ],
    "clue": [
        (
            "What is a clue in a mystery?",
            "A clue is a small true sign that helps you figure out what happened. Good mystery-solvers follow clues instead of guessing too fast.",
        )
    ],
}
KNOWLEDGE_ORDER = ["clue", "bell", "spoon", "ribbon", "magpie", "beaver", "goose", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    accuser = f["accuser"]
    blamed = f["blamed"]
    item = f["item_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    return [
        (
            f'Write a tall-tale mystery for a 3-to-5-year-old that includes the words '
            f'"linger" and "devote". The story should take place at {setting.place} and '
            f'involve a missing {item.label}, a wrong accusation, clue-following, and reconciliation.'
        ),
        (
            f"Tell a child-friendly story where {accuser.attrs['name']} and {blamed.attrs['name']} "
            f"devote the morning to a festival, but {item.phrase} disappears. They solve the mystery "
            f"by following clues to {helper.label} and make up afterward."
        ),
        (
            f"Write a rhyming tall tale with a mystery to solve: a missing festival object, a hurt friend, "
            f"a calm elder, and an ending where nobody lets the quarrel linger."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    accuser = f["accuser"]
    blamed = f["blamed"]
    elder = f["elder"]
    item = f["item_cfg"]
    helper = f["helper_cfg"]
    setting = f["setting"]
    tone = f["tone"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {accuser.attrs['name']} and {blamed.attrs['name']}, who were getting a festival ready, and {elder.attrs['name']} who helped them read the clues.",
        ),
        (
            f"What mystery did they have to solve?",
            f"They had to find {item.phrase} after it vanished from the festival table. Without it, the opening could not happen the proper way.",
        ),
        (
            f"Why did {accuser.attrs['name']} blame {blamed.attrs['name']} at first?",
            f"{accuser.attrs['name']} saw {helper.red_herring} and guessed too fast. That clue looked suspicious, but it did not prove who had taken the missing thing.",
        ),
        (
            "How did they solve the mystery?",
            f"They stopped arguing and followed real signs -- {helper.clue} -- toward {setting.hideout}. Those clues led them to {helper.phrase}, which had used the missing item for its own reason.",
        ),
        (
            f"Why was the helper really holding the item?",
            f"It was not trying to ruin the festival. It wanted {helper.motive}, so the item looked useful in a different way.",
        ),
    ]
    if tone == "warm":
        qa.append(
            (
                f"How did the children make peace?",
                f"{accuser.attrs['name']} apologized as soon as the truth was clear, and {blamed.attrs['name']} forgave quickly. Their friendship was already strong enough that the hurt did not have to linger.",
            )
        )
    else:
        qa.append(
            (
                f"How did the children reconcile after the mistake?",
                f"{accuser.attrs['name']} admitted the blame was unfair and said so plainly. {blamed.attrs['name']} told the truth about being hurt, then chose to forgive so they could finish the festival together.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The item was returned, the opening went ahead, and the two children worked side by side again. The final song proves they solved both the mystery and the quarrel.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item = f["item_cfg"]
    helper = f["helper_cfg"]
    tags = {"clue", "apology"} | set(item.tags) | set(helper.tags)
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
    for eid, ent in world.entities.items():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.label:
            bits.append(f"label={ent.label}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {eid:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="windmill",
        item="clapper",
        helper="magpie",
        accuser="Mira",
        accuser_gender="girl",
        blamed="Eli",
        blamed_gender="boy",
        elder_name="Aunt Maple",
        elder_type="mother",
        relation="friends",
        trust=4,
    ),
    StoryParams(
        setting="riverbend",
        item="spoon",
        helper="beaver",
        accuser="Jasper",
        accuser_gender="boy",
        blamed="Ruby",
        blamed_gender="girl",
        elder_name="Uncle Reed",
        elder_type="father",
        relation="friends",
        trust=7,
    ),
    StoryParams(
        setting="mesa",
        item="ribbon",
        helper="goose",
        accuser="Clara",
        accuser_gender="girl",
        blamed="Nell",
        blamed_gender="girl",
        elder_name="Granny Wren",
        elder_type="mother",
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        setting="riverbend",
        item="ribbon",
        helper="goose",
        accuser="Bo",
        accuser_gender="boy",
        blamed="June",
        blamed_gender="girl",
        elder_name="Mayor Thimble",
        elder_type="father",
        relation="friends",
        trust=3,
    ),
    StoryParams(
        setting="windmill",
        item="spoon",
        helper="beaver",
        accuser="Tessa",
        accuser_gender="girl",
        blamed="Milo",
        blamed_gender="boy",
        elder_name="Aunt Maple",
        elder_type="mother",
        relation="siblings",
        trust=8,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S,I,H) :- setting(S), item(I), helper(H), hosts(S,H), prefers(H,M), material(I,M), weight(I,W), carry(H,C), W <= C.

% --- reconciliation tone ---------------------------------------------------
warm  :- relation(siblings).
warm  :- trust(T), T >= 6.
earned :- not warm.

tone(warm) :- warm.
tone(earned) :- earned.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.hosts):
            lines.append(asp.fact("hosts", sid, hid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("material", iid, item.material))
        lines.append(asp.fact("weight", iid, item.weight))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("carry", hid, helper.carry))
        for pref in sorted(helper.prefers):
            lines.append(asp.fact("prefers", hid, pref))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_tone(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("trust", params.trust),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show tone/1."))
    atoms = asp.atoms(model, "tone")
    return atoms[0][0] if atoms else "?"


def _smoke_generation() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = CURATED[:]
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_tone(params) != tone_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: tone model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} tone results differ.")

    try:
        _smoke_generation()
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale mystery storyworld: a missing festival object, a wrong guess, clue-following, and reconciliation."
    )
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("--accuser")
    ap.add_argument("--blamed")
    ap.add_argument("--accuser-gender", choices=["girl", "boy"])
    ap.add_argument("--blamed-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-name")
    ap.add_argument("--elder-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, item, helper) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python logic and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError("(No story: unknown setting.)")
    if args.item is not None and args.item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError("(No story: unknown helper.)")

    if args.setting and args.item and args.helper:
        setting = SETTINGS[args.setting]
        item = ITEMS[args.item]
        helper = HELPERS[args.helper]
        if not (args.setting, args.item, args.helper) in set(valid_combos()):
            raise StoryError(explain_combo_rejection(setting, item, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, helper_id = rng.choice(combos)
    relation = args.relation or rng.choice(["friends", "siblings"])
    trust = args.trust if args.trust is not None else rng.randint(2, 9)

    accuser_gender = args.accuser_gender or rng.choice(["girl", "boy"])
    blamed_gender = args.blamed_gender or rng.choice(["girl", "boy"])
    accuser = args.accuser or _pick_name(rng, accuser_gender)
    blamed = args.blamed or _pick_name(rng, blamed_gender, avoid=accuser)
    elder_name = args.elder_name or rng.choice(ELDER_NAMES)
    elder_type = args.elder_type or rng.choice(["mother", "father"])

    return StoryParams(
        setting=setting_id,
        item=item_id,
        helper=helper_id,
        accuser=accuser,
        accuser_gender=accuser_gender,
        blamed=blamed,
        blamed_gender=blamed_gender,
        elder_name=elder_name,
        elder_type=elder_type,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    helper = HELPERS[params.helper]
    if (params.setting, params.item, params.helper) not in set(valid_combos()):
        raise StoryError(explain_combo_rejection(setting, item, helper))

    world = tell(
        setting,
        item,
        helper,
        accuser_name=params.accuser,
        accuser_gender=params.accuser_gender,
        blamed_name=params.blamed,
        blamed_gender=params.blamed_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show tone/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, helper) combos:\n")
        for setting, item, helper in combos:
            print(f"  {setting:10} {item:8} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.accuser} & {p.blamed}: {p.item} at {p.setting} with {p.helper} ({tone_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
