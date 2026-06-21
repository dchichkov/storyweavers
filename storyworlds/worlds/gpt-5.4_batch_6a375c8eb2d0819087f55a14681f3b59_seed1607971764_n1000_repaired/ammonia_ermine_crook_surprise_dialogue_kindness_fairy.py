#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py
===================================================================================

A standalone story world in a gentle fairy-tale mode.

Premise
-------
A child in a moonlit kingdom finds a festival cloak with soft ermine trim
snagged near the water. The hem is stained. In the wash-house sits a bottle of
ammonia that looks like a quick answer, but the world knows it is too harsh for
ermine. A kind shepherd with a crook helps lift the cloak down, and together
they choose a gentler way to clean it. The surprise is that the cloak belongs to
a hidden fairy lady, who rewards the kindness she saw.

Why the coverage constraint exists
----------------------------------
This world refuses to tell stories where ammonia is used on ermine trim. The
bottle is present in the wash-house so the word belongs naturally to the tale,
but the reasonableness gate rejects it: the cleaner is too sharp for delicate
fur. The story only generates compatible stain-and-cleaning pairs where a gentle
method could honestly help.

Run it
------
python storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py
python storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py --stain soot --method brush
python storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py --method ammonia
python storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py --all
python storyworlds/worlds/gpt-5.4/ammonia_ermine_crook_surprise_dialogue_kindness_fairy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    delicate: bool = False
    hooked: bool = False
    # two simulation axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "lady"}
        male = {"boy", "father", "man", "shepherd"}
        if self.type in female:
            table = {"subject": "she", "object": "her", "possessive": "her"}
            return table[case]
        if self.type in male:
            table = {"subject": "he", "object": "him", "possessive": "his"}
            return table[case]
        table = {"subject": "it", "object": "it", "possessive": "its"}
        return table[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    sight: str
    snag: str
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
class Stain:
    id: str
    label: str
    source: str
    mark: str
    severity: int
    lines: tuple[str, str]
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
    power: int
    harsh: bool
    use_text: str
    fix_text: str
    fail_text: str
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


@dataclass
class SurpriseGift:
    id: str
    token: str
    blessing: str
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
class StoryParams:
    place: str
    stain: str
    method: str
    child_name: str
    child_gender: str
    parent_type: str
    child_trait: str
    surprise: str
    delay: int = 0
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    cloak = world.get("cloak")
    child = world.get("child")
    if cloak.meters["stained"] >= THRESHOLD:
        sig = ("worry", "cloak")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
    if cloak.meters["snagged"] >= THRESHOLD:
        sig = ("worry", "snag")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
    return out


def _r_harsh(world: World) -> list[str]:
    cloak = world.get("cloak")
    child = world.get("child")
    if cloak.meters["sharp_fumes"] < THRESHOLD:
        return []
    sig = ("harsh", "ermine")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if cloak.delicate:
        cloak.meters["damaged"] += 1
        child.memes["guilt"] += 1
    return []


def _r_restore(world: World) -> list[str]:
    cloak = world.get("cloak")
    if cloak.meters["retrieved"] < THRESHOLD:
        return []
    if cloak.meters["stain_help"] < THRESHOLD:
        return []
    sig = ("restore", int(cloak.meters["stain_help"]), int(cloak.meters["retrieved"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cloak.meters["clean"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="harsh", tag="physical", apply=_r_harsh),
    Rule(name="restore", tag="physical", apply=_r_restore),
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
            world.say(s)
    return produced


PLACES = {
    "moon_bridge": Place(
        id="moon_bridge",
        label="the Moon Bridge",
        sight="silver water moved under the bridge like a sleeping ribbon",
        snag="on a branch above the water",
        tags={"bridge", "water"},
    ),
    "willow_bank": Place(
        id="willow_bank",
        label="the Willow Bank",
        sight="long willow leaves brushed the stream and whispered together",
        snag="in the low willow branches",
        tags={"willow", "water"},
    ),
    "castle_gate": Place(
        id="castle_gate",
        label="the Castle Gate",
        sight="the gate towers shone pale in the evening light",
        snag="in the rose thorns beside the gate",
        tags={"castle", "garden"},
    ),
}

STAINS = {
    "blackberry": Stain(
        id="blackberry",
        label="blackberry stain",
        source="a burst blackberry tart",
        mark="a purple crescent along the hem",
        severity=2,
        lines=(
            "A bit of berry filling had left a purple smile near the edge.",
            "The stain looked small, yet it glowed darkly against the white fur.",
        ),
        tags={"berries", "cloth"},
    ),
    "soot": Stain(
        id="soot",
        label="soot stain",
        source="a sleepy lantern",
        mark="a gray smear by the clasp",
        severity=1,
        lines=(
            "A lantern had coughed once and brushed the cloth with soot.",
            "The mark was powdery, but it made the pale cloak look sad.",
        ),
        tags={"soot", "lantern"},
    ),
    "pond_mud": Stain(
        id="pond_mud",
        label="pond-mud stain",
        source="the splash of a cart wheel",
        mark="a brown splash across the hem",
        severity=2,
        lines=(
            "Mud from the road had freckled the hem in brown spots.",
            "The damp earth had begun to dry into stubborn little scales.",
        ),
        tags={"mud", "water"},
    ),
}

METHODS = {
    "brush": Method(
        id="brush",
        label="a soft silver brush",
        sense=3,
        power=1,
        harsh=False,
        use_text="drew a soft silver brush through the cloth with tiny patient strokes",
        fix_text="The loose soot floated away like gray dust from a dream.",
        fail_text="The brush helped a little, but the deeper mark would not yield.",
        qa_text="used a soft silver brush to lift the mark away",
        tags={"brush", "gentle"},
    ),
    "soapflakes": Method(
        id="soapflakes",
        label="soap flakes in warm water",
        sense=3,
        power=2,
        harsh=False,
        use_text="melted soap flakes into warm water and dabbed the hem with a folded cloth",
        fix_text="Little by little, the stain loosened and the white fur shone again.",
        fail_text="The soap sweetened the cloth, but the set-in stain stayed behind in a faint shadow.",
        qa_text="washed the hem with soap flakes and warm water",
        tags={"soap", "gentle"},
    ),
    "snow_rinse": Method(
        id="snow_rinse",
        label="fresh snow and rainwater",
        sense=2,
        power=2,
        harsh=False,
        use_text="rubbed the mark with fresh snow and then rinsed it in a bowl of rainwater",
        fix_text="The snow brightened the fur, and the muddy color slipped away.",
        fail_text="The snow cooled the cloth, but the old mark still clung to the threads.",
        qa_text="cleaned the mark with fresh snow and rainwater",
        tags={"snow", "gentle"},
    ),
    "ammonia": Method(
        id="ammonia",
        label="the bottle of ammonia from the wash-house shelf",
        sense=1,
        power=3,
        harsh=True,
        use_text="uncorked the ammonia and the sharp smell jumped into the air at once",
        fix_text="The mark might fade fast, but the delicate fur would pay the price.",
        fail_text="The sharp cleaner bit at the ermine trim and spoiled its soft white grace.",
        qa_text="reached for ammonia",
        tags={"ammonia", "sharp"},
    ),
}

SURPRISES = {
    "bell": SurpriseGift(
        id="bell",
        token="a bell of moon-silver",
        blessing="Whenever it rang, lost things seemed easier to find.",
    ),
    "seed": SurpriseGift(
        id="seed",
        token="a pearl-bright seed",
        blessing="By spring it would grow into a tree with silver blossoms.",
    ),
    "ribbon": SurpriseGift(
        id="ribbon",
        token="a ribbon woven from frost-light",
        blessing="It never frayed and always shone clean after rain.",
    ),
}

GIRL_NAMES = ["Elin", "Mira", "Nora", "Ava", "Lina", "Rose"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Milo", "Oren", "Ben"]
TRAITS = ["gentle", "curious", "patient", "bright-hearted", "careful", "kind"]

ALLOWED_BY_STAIN = {
    "soot": {"brush", "soapflakes"},
    "blackberry": {"soapflakes", "snow_rinse"},
    "pond_mud": {"soapflakes", "snow_rinse"},
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for stain_id, methods in ALLOWED_BY_STAIN.items():
            for method_id in sorted(methods):
                if METHODS[method_id].sense >= SENSE_MIN:
                    combos.append((place_id, stain_id, method_id))
    return combos


def stain_severity(stain: Stain, delay: int) -> int:
    return stain.severity + delay


def restored(method: Method, stain: Stain, delay: int) -> bool:
    return method.power >= stain_severity(stain, delay)


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    return (
        f"(Refusing method '{method_id}': {method.label} is too harsh or unwise here "
        f"(sense={method.sense} < {SENSE_MIN}). In this world, ammonia does not belong "
        f"on delicate ermine trim. Try a gentle method such as brush, soapflakes, or snow_rinse.)"
    )


def explain_combo_rejection(stain_id: str, method_id: str) -> str:
    stain = STAINS[stain_id]
    method = METHODS[method_id]
    return (
        f"(No story: {method.label} is not a reasonable fix for {stain.label}. "
        f"The method must honestly suit the stain while keeping the ermine safe.)"
    )


def predict_cleaning(world: World, method: Method, stain: Stain, delay: int) -> dict:
    sim = world.copy()
    cloak = sim.get("cloak")
    cloak.meters["snagged"] = 0.0
    cloak.meters["retrieved"] = 1.0
    if method.harsh:
        cloak.meters["sharp_fumes"] += 1
    if restored(method, stain, delay):
        cloak.meters["stain_help"] += 1
    propagate(sim, narrate=False)
    return {
        "clean": cloak.meters["clean"] >= THRESHOLD,
        "damaged": cloak.meters["damaged"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"In a small kingdom where dew sometimes shone like glass beads, "
        f"{child.id} lived with {child.pronoun('possessive')} {parent.label_word} near {world.place.label}."
    )
    world.say(
        f"{child.pronoun().capitalize()} was a {next(iter(child.traits), 'kind')} child, and "
        f"{world.place.sight}."
    )


def find_cloak(world: World, child: Entity, stain: Stain) -> None:
    cloak = world.get("cloak")
    cloak.meters["snagged"] = 1.0
    cloak.meters["stained"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"On the eve of the Winter Lantern Feast, {child.id} found a white traveling cloak "
        f"{world.place.snag}. The cloak was lined with ermine, soft as cloud edges."
    )
    world.say(stain.lines[0])
    world.say(stain.lines[1])


def wish_to_help(world: World, child: Entity) -> None:
    child.memes["kindness"] += 1
    world.say(
        f'"Someone will need this tonight," {child.id} whispered. '
        f'"I must help before the lanterns are lit."'
    )


def ammonia_temptation(world: World, child: Entity) -> None:
    child.memes["hurry"] += 1
    world.say(
        f"In the little wash-house nearby stood a bottle labeled ammonia. "
        f"{child.id} looked at it and thought a quick strong cleaner might solve everything."
    )


def shepherd_arrives(world: World, shepherd: Entity) -> None:
    world.say(
        f"Just then an old shepherd came down the path, leaning on a crook polished smooth by years."
    )
    world.say(
        f'"Softly now," said the shepherd. "A sharp answer is not always a kind one."'
    )


def warning(world: World, child: Entity, shepherd: Entity, method: Method, stain: Stain, delay: int) -> None:
    pred = predict_cleaning(world, method, stain, delay)
    world.facts["pred_clean"] = pred["clean"]
    world.facts["pred_damaged"] = pred["damaged"]
    if method.id == "ammonia":
        child.memes["caution"] += 1
        world.say(
            f'{shepherd.pronoun().capitalize()} touched the bottle with one finger and shook '
            f'{shepherd.pronoun("possessive")} head. "Not ammonia for ermine," '
            f'{shepherd.pronoun()} said. "It may chase the stain, but it will bite the fur."'
        )
    elif pred["clean"]:
        world.say(
            f'"Your thought is gentle enough," said the shepherd, "and if we are patient, the mark may leave."'
        )
    else:
        world.say(
            f'"It is a kind start," said the shepherd, "yet this stain has sat too long. We may save the cloak, though a shadow could remain."'
        )


def retrieve_with_crook(world: World, child: Entity, shepherd: Entity) -> None:
    cloak = world.get("cloak")
    child.memes["hope"] += 1
    shepherd.memes["kindness"] += 1
    cloak.meters["snagged"] = 0.0
    cloak.meters["retrieved"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"The shepherd reached up with the crook, caught the cloth by its loop, "
        f"and lowered it without tearing so much as one white hair."
    )
    world.say(
        f'"Here," {shepherd.pronoun()} said, placing it in {child.id}\'s arms. '
        f'"Kind hands first. Clean hands second."'
    )


def gentle_clean(world: World, child: Entity, method: Method, stain: Stain, delay: int) -> None:
    cloak = world.get("cloak")
    world.say(f"Together they carried the cloak to the wash-house table.")
    world.say(f"{child.id} {method.use_text}.")
    if method.harsh:
        cloak.meters["sharp_fumes"] += 1
    elif restored(method, stain, delay):
        cloak.meters["stain_help"] += 1
    propagate(world, narrate=False)
    if cloak.meters["clean"] >= THRESHOLD and cloak.meters["damaged"] < THRESHOLD:
        world.say(method.fix_text)
    elif cloak.meters["damaged"] >= THRESHOLD:
        world.say(method.fail_text)
    else:
        world.say(method.fail_text)


def fairy_reveal(world: World, child: Entity, surprise: SurpriseGift) -> None:
    fairy = world.get("fairy")
    cloak = world.get("cloak")
    if cloak.meters["clean"] >= THRESHOLD and cloak.meters["damaged"] < THRESHOLD:
        fairy.memes["gratitude"] += 1
        child.memes["joy"] += 1
        child.memes["wonder"] += 1
        world.say(
            "When the last fold was smoothed, a lady in a plain gray shawl stepped from the doorway."
        )
        world.say(
            f'"You have returned my cloak," she said, and at once the gray shawl slipped away like mist. '
            f'Beneath it shone the hidden Fairy of the Winter Feast.'
        )
        world.say(
            f'"You chose kindness over hurry," the fairy said. "Take {surprise.token}." '
            f"{surprise.blessing}"
        )
        world.say(
            f"{child.id} looked for the shepherd to thank him too, but the path was empty except for "
            f"a single silver curl of wool beside the prints of a crook."
        )
    else:
        fairy.memes["gratitude"] += 1
        child.memes["relief"] += 1
        world.say(
            "Before they could sigh again, a lady in a plain gray shawl stepped from the doorway."
        )
        world.say(
            f'"This is my cloak," she said, and moonlight shivered over her until she stood revealed as the Fairy of the Winter Feast.'
        )
        world.say(
            f'She touched the faint mark and smiled kindly. "You did not hide from the trouble," she said. '
            f'"You chose care instead of ammonia, and that kindness matters more than a perfect hem."'
        )
        world.say(
            f"Then she brushed the cloak once with her fingers. The mark faded to the softness of old snow, "
            f"and {child.id} bowed in wonder."
        )


def closing_image(world: World, child: Entity) -> None:
    world.say(
        f"That night, as the lanterns kindled one by one, {child.id} walked home more slowly than before."
    )
    world.say(
        "Now the child knew that in a true fairy tale, the gentlest answer could shine brighter than the quickest one."
    )


def tell(place: Place, stain: Stain, method: Method, surprise: SurpriseGift,
         child_name: str = "Elin", child_gender: str = "girl", parent_type: str = "mother",
         child_trait: str = "kind", delay: int = 0) -> World:
    world = World(place)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[child_trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    shepherd = world.add(Entity(
        id="Shepherd",
        kind="character",
        type="shepherd",
        label="the shepherd",
        role="helper",
    ))
    cloak = world.add(Entity(
        id="cloak",
        type="cloak",
        label="cloak",
        phrase="a white traveling cloak lined with ermine",
        delicate=True,
        hooked=True,
    ))
    fairy = world.add(Entity(
        id="Fairy",
        kind="character",
        type="lady",
        label="the fairy lady",
        role="owner",
    ))

    child.memes["kindness"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["wonder"] = 0.0
    child.memes["guilt"] = 0.0
    child.memes["relief"] = 0.0
    shepherd.memes["kindness"] = 0.0
    fairy.memes["gratitude"] = 0.0
    cloak.meters["snagged"] = 0.0
    cloak.meters["stained"] = 0.0
    cloak.meters["retrieved"] = 0.0
    cloak.meters["stain_help"] = 0.0
    cloak.meters["clean"] = 0.0
    cloak.meters["damaged"] = 0.0
    cloak.meters["sharp_fumes"] = 0.0

    introduce(world, child, parent)
    find_cloak(world, child, stain)
    wish_to_help(world, child)

    world.para()
    ammonia_temptation(world, child)
    shepherd_arrives(world, shepherd)
    warning(world, child, shepherd, method, stain, delay)
    retrieve_with_crook(world, child, shepherd)

    world.para()
    gentle_clean(world, child, method, stain, delay)
    fairy_reveal(world, child, surprise)
    closing_image(world, child)

    outcome = "restored" if cloak.meters["clean"] >= THRESHOLD and cloak.meters["damaged"] < THRESHOLD else "marked"
    world.facts.update(
        child=child,
        parent=parent,
        shepherd=shepherd,
        cloak=cloak,
        fairy=fairy,
        place=place,
        stain=stain,
        method=method,
        surprise=surprise,
        delay=delay,
        outcome=outcome,
        used_ammonia=method.id == "ammonia",
        kindness=child.memes["kindness"] >= THRESHOLD or shepherd.memes["kindness"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ammonia": [(
        "What is ammonia?",
        "Ammonia is a very strong cleaner with a sharp smell. It should only be handled by a grown-up because it can sting noses, eyes, and skin."
    )],
    "ermine": [(
        "What is ermine?",
        "Ermine is a soft white fur often used in old fairy tales for royal cloaks. Because it is delicate, it must be cleaned very gently."
    )],
    "crook": [(
        "What is a shepherd's crook?",
        "A shepherd's crook is a staff with a hooked end. The hook helps reach, guide, or lift things without grabbing too hard."
    )],
    "soot": [(
        "What is soot?",
        "Soot is soft black dust left by smoke or a flame. It can smear easily, so a gentle brush often works better than hard scrubbing."
    )],
    "soap": [(
        "Why can soap flakes help clean cloth?",
        "Soap flakes melt into water and help loosen dirt or stains from cloth. When you dab gently, the fabric can be cleaned without rough rubbing."
    )],
    "snow": [(
        "Why might snow and water help in an old fairy-tale wash-house?",
        "Fresh snow is cold and clean, and people in stories sometimes use it with water to freshen delicate cloth. It is a gentle choice compared with a harsh cleaner."
    )],
    "berries": [(
        "Why can berry juice stain cloth?",
        "Berry juice has strong color in it, so it can sink into threads and leave a purple mark. The longer it sits, the harder it is to wash away."
    )],
    "kindness": [(
        "What does kindness mean in this story world?",
        "Kindness means helping carefully and thinking about what will keep someone or something safe. It is not only being nice with words, but choosing a gentle action too."
    )],
}
KNOWLEDGE_ORDER = ["ammonia", "ermine", "crook", "soot", "soap", "snow", "berries", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    stain = f["stain"]
    method = f["method"]
    return [
        'Write a short fairy tale for a 3-to-5-year-old that includes the words "ammonia", "ermine", and "crook".',
        f"Tell a gentle fairy-tale story where a child named {child.id} finds an ermine-lined cloak, hears a warning about ammonia, and is helped by a shepherd with a crook.",
        f"Write a story with dialogue, kindness, and a surprise ending where {method.label} is chosen to save a {stain.label} without harming the ermine trim.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    shepherd = f["shepherd"]
    stain = f["stain"]
    method = f["method"]
    surprise = f["surprise"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who found a white cloak lined with ermine, and a kind shepherd who came with a crook. Together they tried to save the cloak before the feast."
        ),
        (
            "What problem did the child find?",
            f"{child.id} found the cloak snagged and marked with {stain.mark}. That made the child worry because someone would need it that very night."
        ),
        (
            "Why did the shepherd warn against ammonia?",
            f'The shepherd said ammonia was too sharp for ermine. It might chase the stain quickly, but it could hurt the soft fur, so kindness meant choosing a gentler answer.'
        ),
        (
            "How did the crook help?",
            f"The shepherd used the crook to lift the cloak down without tearing it. That mattered because the cloak had to be rescued gently before anyone could clean the stain."
        ),
    ]
    if outcome == "restored":
        qa.append((
            "How was the cloak saved?",
            f"{child.id} and the shepherd used {method.label}, and the stain came away. They matched a gentle method to the kind of mark, so the ermine stayed soft while the cloak grew clean again."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"The plain lady was really the Fairy of the Winter Feast, and she gave {child.id} {surprise.token}. The gift came because she had seen the kindness in the child's choices."
        ))
    else:
        qa.append((
            "Did the child still do the right thing even though the mark stayed?",
            f"Yes. The child chose care instead of ammonia, so the ermine was not harmed. The fairy even said that kindness mattered more than making the hem perfect right away."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"The cloak belonged to the Fairy of the Winter Feast. She appeared in disguise, thanked {child.id}, and used a little magic to soften the mark after seeing such careful help."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ammonia", "ermine", "crook", "kindness"}
    stain = f["stain"]
    method = f["method"]
    if "soot" in stain.tags:
        tags.add("soot")
    if "berries" in stain.tags:
        tags.add("berries")
    if method.id == "soapflakes":
        tags.add("soap")
    if method.id == "snow_rinse":
        tags.add("snow")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.delicate:
            bits.append("delicate=True")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_bridge",
        stain="blackberry",
        method="soapflakes",
        child_name="Elin",
        child_gender="girl",
        parent_type="mother",
        child_trait="kind",
        surprise="bell",
        delay=0,
    ),
    StoryParams(
        place="willow_bank",
        stain="soot",
        method="brush",
        child_name="Finn",
        child_gender="boy",
        parent_type="father",
        child_trait="patient",
        surprise="seed",
        delay=0,
    ),
    StoryParams(
        place="castle_gate",
        stain="pond_mud",
        method="snow_rinse",
        child_name="Mira",
        child_gender="girl",
        parent_type="mother",
        child_trait="careful",
        surprise="ribbon",
        delay=1,
    ),
    StoryParams(
        place="moon_bridge",
        stain="blackberry",
        method="snow_rinse",
        child_name="Theo",
        child_gender="boy",
        parent_type="father",
        child_trait="curious",
        surprise="bell",
        delay=1,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.method not in METHODS or params.stain not in STAINS:
        return "?"
    return "restored" if restored(METHODS[params.method], STAINS[params.stain], params.delay) else "marked"


ASP_RULES = r"""
% reasonableness gate
valid(P,S,M) :- place(P), stain(S), method(M), allowed(S,M), sense(M,Sm), sense_min(Min), Sm >= Min.

% outcome model
severity(V) :- chosen_stain(S), stain_severity(S,Base), delay(D), V = Base + D.
good_method :- chosen_method(M), power(M,P), severity(V), P >= V.
outcome(restored) :- good_method.
outcome(marked) :- not good_method.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for stain_id, stain in STAINS.items():
        lines.append(asp.fact("stain", stain_id))
        lines.append(asp.fact("stain_severity", stain_id, stain.severity))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("power", method_id, method.power))
    for stain_id, methods in ALLOWED_BY_STAIN.items():
        for method_id in sorted(methods):
            lines.append(asp.fact("allowed", stain_id, method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_stain", params.stain),
        asp.fact("chosen_method", params.method),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child, an ermine cloak, a crook, and the choice between hurry and kindness."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--stain", choices=STAINS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the stain has had to set")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, stain, method) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(args.method))
    if args.stain and args.method:
        if args.method not in ALLOWED_BY_STAIN.get(args.stain, set()):
            raise StoryError(explain_combo_rejection(args.stain, args.method))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.stain is None or combo[1] == args.stain)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, stain_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    surprise = rng.choice(sorted(SURPRISES))
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        place=place_id,
        stain=stain_id,
        method=method_id,
        child_name=name,
        child_gender=gender,
        parent_type=parent_type,
        child_trait=trait,
        surprise=surprise,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.stain not in STAINS:
        raise StoryError(f"(Unknown stain: {params.stain})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method_rejection(params.method))
    if params.method not in ALLOWED_BY_STAIN.get(params.stain, set()):
        raise StoryError(explain_combo_rejection(params.stain, params.method))

    world = tell(
        place=PLACES[params.place],
        stain=STAINS[params.stain],
        method=METHODS[params.method],
        surprise=SURPRISES[params.surprise],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
        child_trait=params.child_trait,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            emit(smoke, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
        if not smoke.story.strip():
            raise StoryError("smoke story was empty")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, stain, method) combos:\n")
        for place_id, stain_id, method_id in combos:
            print(f"  {place_id:12} {stain_id:10} {method_id}")
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
            header = f"### {p.child_name}: {p.stain} at {p.place} ({p.method}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
