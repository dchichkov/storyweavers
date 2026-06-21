#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py
===================================================================================

A standalone story world for a small fable-shaped domain: in a little animal
nation, a vain ruler frets over a troublesome scalp, spreads gloom through the
square, then accepts a silly boogie remedy from a wiser helper. The ruler's
scalp transforms in a funny, gentle way, laughter turns kind instead of cruel,
and the whole nation ends in a happy dance.

The seed asked for the words "boogie", "nation", and "scalp", plus
Transformation, Humor, and a Happy Ending in a Fable style. This world models
those directly:

- a ruler's gloomy vanity physically concerns a scalp
- a helper proposes a common-sense, setting-grounded remedy
- a ridiculous boogie is the turning action
- a transformation changes the ruler's appearance and heart
- the ending image proves the moral: kind laughter is better than proud demands

Run it
------
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py --nation meadow --trouble bare --remedy clover_cream
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py --nation marsh --remedy feather_pomade
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/boogie_nation_scalp_transformation_humor_happy_ending.py --verify
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
from contextlib import redirect_stdout
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "duck", "mother", "queen", "girl", "ewe"}
        male = {"fox", "mole", "badger", "father", "king", "boy", "ram"}
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
class Nation:
    id: str
    title: str
    place: str
    citizens: str
    floor: str
    affords: set[str] = field(default_factory=set)
    closing_image: str = ""
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
class Trouble:
    id: str
    label: str
    need: str
    opening: str
    complaint: str
    mirror_line: str
    risk: str
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
class Remedy:
    id: str
    label: str
    needs: set[str]
    ingredients: set[str]
    mix_text: str
    boogie_text: str
    transform_name: str
    transform_text: str
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
    def __init__(self, nation: Nation) -> None:
        self.nation = nation
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def citizens(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role == "citizen"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.nation)
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


def _r_gloom_spreads(world: World) -> list[str]:
    out: list[str] = []
    ruler = world.get("ruler")
    if ruler.memes["gloom"] < THRESHOLD:
        return out
    for citizen in world.citizens():
        sig = ("gloom", citizen.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        citizen.memes["gloom"] += 1
        out.append("__gloom__")
    return out


def _r_transformation(world: World) -> list[str]:
    ruler = world.get("ruler")
    if ruler.meters["prepared_scalp"] < THRESHOLD or ruler.meters["danced"] < THRESHOLD:
        return []
    sig = ("transform", world.facts.get("remedy", ""), world.facts.get("trouble", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ruler.meters["transformed"] += 1
    ruler.meters["bare_scalp"] = 0.0
    ruler.meters["dusty_scalp"] = 0.0
    ruler.meters["plain_scalp"] = 0.0
    ruler.memes["gloom"] = 0.0
    ruler.memes["joy"] += 2
    ruler.memes["kindness"] += 1
    for citizen in world.citizens():
        citizen.memes["joy"] += 1
        citizen.memes["gloom"] = 0.0
    return ["__transform__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="gloom_spreads", tag="emotional", apply=_r_gloom_spreads),
    Rule(name="transformation", tag="physical", apply=_r_transformation),
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


def remedy_fits(nation: Nation, trouble: Trouble, remedy: Remedy) -> bool:
    if trouble.need not in remedy.needs:
        return False
    return remedy.ingredients.issubset(nation.affords)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for nation_id, nation in NATIONS.items():
        for trouble_id, trouble in TROUBLES.items():
            for remedy_id, remedy in REMEDIES.items():
                if remedy_fits(nation, trouble, remedy):
                    combos.append((nation_id, trouble_id, remedy_id))
    return combos


def explain_rejection(nation: Nation, trouble: Trouble, remedy: Remedy) -> str:
    if trouble.need not in remedy.needs:
        return (
            f"(No story: {remedy.label} does not suit a {trouble.label}. "
            f"This trouble needs a remedy that can {trouble.need} the scalp.)"
        )
    missing = sorted(remedy.ingredients - nation.affords)
    if missing:
        return (
            f"(No story: in {nation.title}, the needed ingredient"
            f"{'' if len(missing) == 1 else 's'} {', '.join(missing)} "
            f"{'is' if len(missing) == 1 else 'are'} not available, so {remedy.label} "
            f"cannot honestly be mixed there.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def predict_square(world: World) -> dict[str, float]:
    sim = world.copy()
    propagate(sim, narrate=False)
    citizen_gloom = sum(c.memes["gloom"] for c in sim.citizens())
    return {
        "citizen_gloom": citizen_gloom,
        "ruler_gloom": sim.get("ruler").memes["gloom"],
    }


def introduce(world: World, ruler: Entity, trouble: Trouble) -> None:
    world.say(
        f"In {world.nation.title}, beside {world.nation.place}, there lived a ruler named "
        f"{ruler.id}. {trouble.opening}"
    )
    world.say(
        f"{ruler.id} often peered into a brass spoon as if it were a royal mirror, for "
        f"{ruler.pronoun('possessive')} scalp troubled {ruler.pronoun('object')} more than a storm troubled a sail."
    )


def show_gloom(world: World, ruler: Entity, trouble: Trouble) -> None:
    ruler.memes["gloom"] += 1
    ruler.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{trouble.complaint}" sighed {ruler.id}. {trouble.mirror_line}'
    )


def tax_vanity(world: World, ruler: Entity) -> None:
    ruler.meters["demanded_crown"] += 1
    world.say(
        f"Soon {ruler.pronoun()} was ordering the cobblers, the bakers, and even the geese to search for a grand crown. "
        f"Because the ruler sulked, the whole nation grew quieter than usual."
    )


def helper_warns(world: World, helper: Entity, ruler: Entity, trouble: Trouble, remedy: Remedy) -> None:
    pred = predict_square(world)
    world.facts["predicted_citizen_gloom"] = pred["citizen_gloom"]
    world.say(
        f"But {helper.id}, the smallest court friend with the steadiest eyes, bowed and said, "
        f'"Your Grace, a heavy crown will not mend a scalp, and {trouble.risk}"'
    )
    if pred["citizen_gloom"] >= THRESHOLD:
        world.say(
            f"{helper.id} looked around the square and saw drooping ears, bent beaks, and paws that no longer clapped. "
            f"The ruler's long sulk was already dimming the cheer of the nation."
        )
    world.say(
        f'"What may help," {helper.pronoun()} added, "is {remedy.label} and one brave boogie."'
    )


def doubt(world: World, ruler: Entity, helper: Entity) -> None:
    ruler.memes["embarrassment"] += 1
    world.say(
        f'"A boogie?" cried {ruler.id}. "{ruler.pronoun("Subject") if False else ""}'
    )
    world.paragraphs[-1][-1] = (
        f'"A boogie?" cried {ruler.id}. "Rulers do not wiggle."'
    )
    world.say(
        f"Yet when {ruler.pronoun()} glanced again at the spoon, {ruler.pronoun('possessive')} face looked lonelier than grand, "
        f"and even {helper.id} could not help a tiny smile."
    )


def mix_remedy(world: World, helper: Entity, ruler: Entity, remedy: Remedy) -> None:
    ruler.meters["prepared_scalp"] += 1
    world.say(
        f"So {helper.id} {remedy.mix_text} and spread the mixture gently over {ruler.id}'s scalp."
    )


def dance(world: World, ruler: Entity, remedy: Remedy) -> None:
    ruler.meters["danced"] += 1
    world.say(
        f'Then {ruler.id} {remedy.boogie_text}. The first step was stiff, the second was silly, and by the third the palace pigeons were cooing in time.'
    )


def transform(world: World, ruler: Entity, remedy: Remedy) -> None:
    propagate(world, narrate=False)
    world.say(
        f"At once, {remedy.transform_text} upon {ruler.id}'s scalp."
    )
    world.say(
        f"The sight was so surprising that a laugh leapt through the square. It was not a sharp laugh. "
        f"It was the round, warm laugh people make when a dear friend finally becomes free."
    )
    ruler.attrs["crown_name"] = remedy.transform_name


def soften(world: World, ruler: Entity, helper: Entity) -> None:
    world.say(
        f"{ruler.id} blinked, then laughed louder than anyone. {ruler.pronoun().capitalize()} bowed to {helper.id} and said, "
        f'"I asked for gold, and you gave me sense."'
    )
    world.say(
        f"From that hour, {ruler.pronoun()} stopped demanding a costly crown and began greeting bakers, cobblers, and children by name."
    )


def closing(world: World, ruler: Entity, helper: Entity) -> None:
    crown_name = ruler.attrs.get("crown_name", "new crest")
    world.say(
        f"Every market morning after that, {world.nation.citizens} gathered on {world.nation.floor} and danced the Boogie of Good Cheer. "
        f"{ruler.id} led the line with {crown_name} bobbing merrily, and {helper.id} kept the beat."
    )
    world.say(world.nation.closing_image)
    world.say(
        "Thus the nation learned that a kind joke can mend a proud heart, while pride alone can make even a sunny square feel small."
    )


def tell(
    nation: Nation,
    trouble: Trouble,
    remedy: Remedy,
    *,
    ruler_name: str = "King Bristle",
    ruler_type: str = "badger",
    helper_name: str = "Mira",
    helper_type: str = "hen",
    helper_trait: str = "calm",
) -> World:
    world = World(nation)
    ruler = world.add(
        Entity(
            id=ruler_name,
            kind="character",
            type=ruler_type,
            label="the ruler",
            role="ruler",
            traits=["vain"],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
            traits=[helper_trait],
            attrs={},
        )
    )
    citizens = [
        Entity(id="citizen1", kind="character", type="goose", label="a goose", role="citizen"),
        Entity(id="citizen2", kind="character", type="mole", label="a mole", role="citizen"),
        Entity(id="citizen3", kind="character", type="duck", label="a duck", role="citizen"),
    ]
    for citizen in citizens:
        citizen.memes["gloom"] = 0.0
        citizen.memes["joy"] = 0.0
        world.add(citizen)

    world.facts["nation"] = nation.id
    world.facts["trouble"] = trouble.id
    world.facts["remedy"] = remedy.id

    ruler.meters["bare_scalp"] = 1.0 if trouble.id == "bare" else 0.0
    ruler.meters["dusty_scalp"] = 1.0 if trouble.id == "dusty" else 0.0
    ruler.meters["plain_scalp"] = 1.0 if trouble.id == "plain" else 0.0
    ruler.meters["prepared_scalp"] = 0.0
    ruler.meters["danced"] = 0.0
    ruler.meters["transformed"] = 0.0
    ruler.meters["demanded_crown"] = 0.0
    ruler.memes["gloom"] = 0.0
    ruler.memes["pride"] = 0.0
    ruler.memes["joy"] = 0.0
    ruler.memes["kindness"] = 0.0
    ruler.memes["embarrassment"] = 0.0
    helper.memes["hope"] = 1.0

    introduce(world, ruler, trouble)
    show_gloom(world, ruler, trouble)
    tax_vanity(world, ruler)

    world.para()
    helper_warns(world, helper, ruler, trouble, remedy)
    doubt(world, ruler, helper)

    world.para()
    mix_remedy(world, helper, ruler, remedy)
    dance(world, ruler, remedy)
    transform(world, ruler, remedy)

    world.para()
    soften(world, ruler, helper)
    closing(world, ruler, helper)

    world.facts.update(
        ruler=ruler,
        helper=helper,
        trouble_cfg=trouble,
        remedy_cfg=remedy,
        transformed=ruler.meters["transformed"] >= THRESHOLD,
        crown_name=ruler.attrs.get("crown_name", ""),
        citizen_gloom=sum(c.memes["gloom"] for c in world.citizens()),
    )
    return world


NATIONS = {
    "meadow": Nation(
        id="meadow",
        title="the Clover Nation",
        place="a silver pond and a ring of clover fields",
        citizens="the meadow folk",
        floor="the flat stone by the pond",
        affords={"clover", "dew", "daisy"},
        closing_image="The silver pond shivered with reflected feet, and even the cattails seemed to chuckle in the breeze.",
        tags={"nation", "clover"},
    ),
    "marsh": Nation(
        id="marsh",
        title="the Reed Nation",
        place="the green marsh among singing reeds",
        citizens="the reed folk",
        floor="a dry boardwalk between the rushes",
        affords={"reed_oil", "dew", "feather"},
        closing_image="The reeds swayed like laughing judges, and the marsh ducks stamped a beat that made the water tremble.",
        tags={"nation", "reed"},
    ),
    "orchard": Nation(
        id="orchard",
        title="the Orchard Nation",
        place="an old orchard where pears knocked softly together",
        citizens="the orchard folk",
        floor="the round threshing stone under the pear tree",
        affords={"daisy", "feather", "clover"},
        closing_image="Above them, pears tapped branch to branch like little wooden drums keeping time for the dance.",
        tags={"nation", "orchard"},
    ),
}

TROUBLES = {
    "bare": Trouble(
        id="bare",
        label="bare scalp",
        need="cover",
        opening="He had a bare scalp that shone in the sun so brightly that sparrows sometimes mistook it for a pebble in water.",
        complaint="My scalp looks like an egg that forgot to hatch",
        mirror_line="Whenever children bowed, they also squinted.",
        risk="while you hunt for splendor, your people must carry your grumpiness on their backs.",
        tags={"scalp", "bare"},
    ),
    "dusty": Trouble(
        id="dusty",
        label="dusty scalp",
        need="clean",
        opening="His scalp was forever dusty, for he paced the square so much that flour, pollen, and road powder settled on it like tired weather.",
        complaint="My scalp looks as if a miller used it for a shelf",
        mirror_line="Even the palace cat once sneezed at the sight.",
        risk="the dust on your head is lighter than the mood in this square.",
        tags={"scalp", "dust"},
    ),
    "plain": Trouble(
        id="plain",
        label="plain scalp",
        need="adorn",
        opening="There was nothing wrong with his scalp at all, except that he wanted it to look grander than the moon, which is a troublesome wish for any ruler.",
        complaint="My scalp is too plain for a throne",
        mirror_line="He tilted the spoon left and right, hoping majesty would appear by surprise.",
        risk="when a ruler chases showiness, the people pay for the chase.",
        tags={"scalp", "plain"},
    ),
}

REMEDIES = {
    "clover_cream": Remedy(
        id="clover_cream",
        label="clover cream",
        needs={"cover"},
        ingredients={"clover", "dew"},
        mix_text="crushed clover with cool dew into a green cream",
        boogie_text="did a side-to-side boogie so careful at first that the guards bit their lips not to laugh",
        transform_name="a velvet clover cap",
        transform_text="a soft velvet clover cap unfurled like spring grass",
        qa_text="mixed clover cream and then danced until a soft clover cap unfurled",
        tags={"boogie", "clover", "transformation"},
    ),
    "reed_polish": Remedy(
        id="reed_polish",
        label="reed polish",
        needs={"clean"},
        ingredients={"reed_oil", "dew"},
        mix_text="stirred reed oil with a few bright drops of dew into a shining polish",
        boogie_text="twisted in a brisk marsh boogie, knees high and tail low, until everyone in the square was snorting behind their paws",
        transform_name="a daisy-bright gleam",
        transform_text="the dust slipped away and a ring of tiny white daisies twinkled around the clean shine",
        qa_text="polished the scalp clean with reed oil and dew, then boogied until little daisies twinkled around it",
        tags={"boogie", "reed", "transformation"},
    ),
    "feather_pomade": Remedy(
        id="feather_pomade",
        label="feather pomade",
        needs={"adorn"},
        ingredients={"feather", "daisy"},
        mix_text="whisked daisy pollen with the fluff of shed feathers into a light pomade",
        boogie_text="spun through a proud little boogie, lifting each foot so high that the ministers forgot to look solemn",
        transform_name="a feathered crest",
        transform_text="a jaunty feathered crest sprang up and tipped forward with comic dignity",
        qa_text="smoothed on feather pomade and spun in a boogie until a feathered crest sprang up",
        tags={"boogie", "feather", "transformation"},
    ),
}

RULER_NAMES = ["Bramble", "Cedric", "Pipkin", "Rowan", "Juniper", "Otis"]
HELPER_NAMES = ["Mira", "Tansy", "Poppy", "Lark", "Nettle", "Wren"]
RULER_TYPES = ["badger", "fox", "mole"]
HELPER_TYPES = ["hen", "duck", "goose"]
HELPER_TRAITS = ["calm", "merry", "wise", "patient"]


@dataclass
class StoryParams:
    nation: str
    trouble: str
    remedy: str
    ruler_name: str
    ruler_type: str
    helper_name: str
    helper_type: str
    helper_trait: str
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
    "boogie": [
        (
            "What is a boogie?",
            "A boogie is a lively dance with bouncy steps and a playful rhythm. People often boogie when they feel cheerful or want to make others smile.",
        )
    ],
    "nation": [
        (
            "What is a nation in this story?",
            "A nation is a whole community living together under the same ruler and customs. In a fable, it can be a little animal people sharing one place and one way of life.",
        )
    ],
    "scalp": [
        (
            "What is a scalp?",
            "A scalp is the skin on top of your head where hair grows. It can feel bare, dusty, itchy, or warm, so it needs gentle care.",
        )
    ],
    "clover": [
        (
            "What is clover?",
            "Clover is a small green plant with soft leaves. Animals can find it in fields and meadows, and it often stands for freshness and spring.",
        )
    ],
    "reed": [
        (
            "What is a reed?",
            "A reed is a tall plant that grows near water. Reeds bend in the wind and are common in marshes and ponds.",
        )
    ],
    "feather": [
        (
            "What is a feather?",
            "A feather is a light covering from a bird's body. Feathers help birds fly, stay warm, and show color.",
        )
    ],
    "transformation": [
        (
            "What does transformation mean?",
            "Transformation means changing from one form into another. In a fable, the outside change often shows an inside change too.",
        )
    ],
    "kindness": [
        (
            "Why is kind laughter different from mean laughter?",
            "Kind laughter invites someone to laugh too, so it helps hearts feel lighter. Mean laughter tries to hurt, so it makes shame grow instead of joy.",
        )
    ],
}
KNOWLEDGE_ORDER = ["boogie", "nation", "scalp", "clover", "reed", "feather", "transformation", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    nation = NATIONS[f["nation"]]
    trouble = f["trouble_cfg"]
    remedy = f["remedy_cfg"]
    ruler = f["ruler"]
    helper = f["helper"]
    return [
        (
            f'Write a short fable for a 3-to-5-year-old that uses the words "boogie", '
            f'"nation", and "scalp", and ends happily after a funny transformation.'
        ),
        (
            f"Tell a gentle animal fable set in {nation.title} where {ruler.id} worries about a {trouble.label}, "
            f"but {helper.id} fixes the trouble with {remedy.label} and a silly boogie."
        ),
        (
            f"Write a humorous transformation tale where a proud ruler learns that kindness is better than showy pride, "
            f"and the whole nation ends by dancing together."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ruler = f["ruler"]
    helper = f["helper"]
    trouble = f["trouble_cfg"]
    remedy = f["remedy_cfg"]
    nation = NATIONS[f["nation"]]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {ruler.id}, a ruler in {nation.title}, and {helper.id}, the friend who dared to help. "
            f"The story follows how the ruler's worry changed the whole square and then changed back again.",
        ),
        (
            f"Why was {ruler.id} unhappy at the beginning?",
            f"{ruler.id} felt ashamed of {ruler.pronoun('possessive')} {trouble.label} and thought a grand crown would hide the problem. "
            f"Because {ruler.pronoun()} sulked over it, the cheer of the nation began to droop too.",
        ),
        (
            f"What did {helper.id} notice about the nation?",
            f"{helper.id} saw that the ruler's long sulk was spreading gloom through the square. "
            f"When a proud leader stays gloomy, the citizens often stop singing and laughing freely.",
        ),
        (
            f"How did {helper.id} help {ruler.id}?",
            f"{helper.id} {remedy.qa_text}. "
            f"The silly dance mattered because the story's transformation happened only after the remedy was on the scalp and the ruler truly joined the boogie.",
        ),
        (
            f"What changed when {ruler.id}'s scalp transformed?",
            f"{ruler.id}'s appearance changed, but {ruler.pronoun('possessive')} heart changed too. "
            f"The new look broke the spell of pride, and laughter returned as warmth instead of worry.",
        ),
        (
            "How did the story end?",
            f"It ended happily with the whole nation dancing together while {ruler.id} led the line. "
            f"The final image proves that shared joy became more precious than a costly crown.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    trouble = world.facts["trouble_cfg"]
    remedy = world.facts["remedy_cfg"]
    tags = {"boogie", "nation", "scalp", "transformation", "kindness"}
    tags |= remedy.tags
    tags |= trouble.tags
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:6}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        nation="meadow",
        trouble="bare",
        remedy="clover_cream",
        ruler_name="Bramble",
        ruler_type="badger",
        helper_name="Mira",
        helper_type="hen",
        helper_trait="wise",
    ),
    StoryParams(
        nation="marsh",
        trouble="dusty",
        remedy="reed_polish",
        ruler_name="Cedric",
        ruler_type="fox",
        helper_name="Tansy",
        helper_type="duck",
        helper_trait="calm",
    ),
    StoryParams(
        nation="orchard",
        trouble="plain",
        remedy="feather_pomade",
        ruler_name="Pipkin",
        ruler_type="mole",
        helper_name="Lark",
        helper_type="goose",
        helper_trait="merry",
    ),
]


ASP_RULES = r"""
fits_need(R, T) :- remedy(R), trouble(T), remedy_need(R, N), trouble_need(T, N).
has_ingredients(Nat, R) :- nation(Nat), remedy(R),
                           not missing_ingredient(Nat, R).
missing_ingredient(Nat, R) :- remedy_ingredient(R, I), not affords(Nat, I).

valid(Nat, T, R) :- nation(Nat), trouble(T), remedy(R),
                    fits_need(R, T), has_ingredients(Nat, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for nation_id, nation in NATIONS.items():
        lines.append(asp.fact("nation", nation_id))
        for ingredient in sorted(nation.affords):
            lines.append(asp.fact("affords", nation_id, ingredient))
    for trouble_id, trouble in TROUBLES.items():
        lines.append(asp.fact("trouble", trouble_id))
        lines.append(asp.fact("trouble_need", trouble_id, trouble.need))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for need in sorted(remedy.needs):
            lines.append(asp.fact("remedy_need", remedy_id, need))
        for ingredient in sorted(remedy.ingredients):
            lines.append(asp.fact("remedy_ingredient", remedy_id, ingredient))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "boogie" not in sample.story.lower():
            raise StoryError("smoke test story missing or did not contain 'boogie'")
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        printed = buf.getvalue()
        if "### smoke" not in printed or "world model state" not in printed:
            raise StoryError("emit smoke test did not print expected sections")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a proud ruler, a silly boogie, and a transformed scalp in a happy fable."
    )
    ap.add_argument("--nation", choices=sorted(NATIONS))
    ap.add_argument("--trouble", choices=sorted(TROUBLES))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--ruler-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (nation, trouble, remedy) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.nation and args.trouble and args.remedy:
        nation = NATIONS[args.nation]
        trouble = TROUBLES[args.trouble]
        remedy = REMEDIES[args.remedy]
        if not remedy_fits(nation, trouble, remedy):
            raise StoryError(explain_rejection(nation, trouble, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.nation is None or combo[0] == args.nation)
        and (args.trouble is None or combo[1] == args.trouble)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    nation_id, trouble_id, remedy_id = rng.choice(sorted(combos))
    ruler_name = args.ruler_name or rng.choice(RULER_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != ruler_name])
    ruler_type = rng.choice(RULER_TYPES)
    helper_type = rng.choice(HELPER_TYPES)
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        nation=nation_id,
        trouble=trouble_id,
        remedy=remedy_id,
        ruler_name=ruler_name,
        ruler_type=ruler_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.nation not in NATIONS:
        raise StoryError(f"(Unknown nation: {params.nation})")
    if params.trouble not in TROUBLES:
        raise StoryError(f"(Unknown trouble: {params.trouble})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    nation = NATIONS[params.nation]
    trouble = TROUBLES[params.trouble]
    remedy = REMEDIES[params.remedy]
    if not remedy_fits(nation, trouble, remedy):
        raise StoryError(explain_rejection(nation, trouble, remedy))

    world = tell(
        nation=nation,
        trouble=trouble,
        remedy=remedy,
        ruler_name=params.ruler_name,
        ruler_type=params.ruler_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_trait=params.helper_trait,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (nation, trouble, remedy) combos:\n")
        for nation_id, trouble_id, remedy_id in combos:
            print(f"  {nation_id:8} {trouble_id:7} {remedy_id}")
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
            header = f"### {p.ruler_name}: {p.trouble} in {p.nation} with {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
