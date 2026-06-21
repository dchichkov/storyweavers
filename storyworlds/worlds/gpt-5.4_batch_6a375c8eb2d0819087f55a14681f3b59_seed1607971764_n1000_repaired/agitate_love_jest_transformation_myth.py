#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py
===================================================================

A standalone story world in a mythic mode: a child makes a careless jest at a
sacred place, agitates a small god, suffers a transformation, and is restored
through love, humility, and a fitting act of repair.

The world model is intentionally small and classical. A shrine has a domain
(river, olive, or dawn); a transformed form must belong to that domain; and the
remedy must soothe that same domain. A loving helper can reverse the change only
when devotion and gentleness together are strong enough for the guardian's
wrath.

Run it
------
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --all
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --shrine river --form reed --remedy water_song
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --json
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --asp
    python storyworlds/worlds/gpt-5.4/agitate_love_jest_transformation_myth.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
WRATH_BASE = 4

GENTLE_TRAITS = {"kind", "patient", "faithful"}
PROUD_TRAITS = {"vain", "quicktongued", "showy"}


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
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "mother":
            return "mother"
        if self.type == "father":
            return "father"
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
class Shrine:
    id: str
    place: str
    guardian_name: str
    guardian_type: str
    sacred_thing: str
    shimmer: str
    closing: str
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
class Form:
    id: str
    label: str
    phrase: str
    stillness: str
    mark: str
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
class Remedy:
    id: str
    act: str
    labor: str
    gift_line: str
    qa_text: str
    gentleness: int
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
class HelperKind:
    id: str
    label: str
    type: str
    devotion: int
    kinship: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_wrath_spreads(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.get("guardian")
    child = world.get("child")
    helper = world.get("helper")
    shrine = world.get("shrine")
    if guardian.meters["wrath"] >= THRESHOLD:
        sig = ("wrath_spreads",)
        if sig not in world.fired:
            world.fired.add(sig)
            shrine.meters["unease"] += 1
            child.memes["fear"] += 1
            helper.memes["fear"] += 1
            out.append("__unease__")
    return out


def _r_transformation_lonely(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.meters["transformed"] >= THRESHOLD:
        sig = ("transformation_lonely",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["lonely"] += 1
            helper.memes["love"] += 1
            out.append("__lonely__")
    return out


def _r_love_stirs_repair(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.memes["love"] >= THRESHOLD and helper.meters["offering"] >= THRESHOLD:
        sig = ("love_stirs_repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["courage"] += 1
            out.append("__repair__")
    return out


CAUSAL_RULES = [
    Rule(name="wrath_spreads", tag="meme", apply=_r_wrath_spreads),
    Rule(name="transformation_lonely", tag="meme", apply=_r_transformation_lonely),
    Rule(name="love_stirs_repair", tag="meme", apply=_r_love_stirs_repair),
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


SHRINES = {
    "river": Shrine(
        id="river",
        place="the bend of the river where white stones shone under clear water",
        guardian_name="Neria",
        guardian_type="goddess",
        sacred_thing="the singing water",
        shimmer="the river made little silver sounds against the stones",
        closing="After that, the river still sang, but now it sounded like a blessing.",
        tags={"water", "river"},
    ),
    "olive": Shrine(
        id="olive",
        place="the oldest olive tree on the hill, where the air smelled green and bright",
        guardian_name="Melon",
        guardian_type="god",
        sacred_thing="the patient olive branches",
        shimmer="the leaves flashed their pale undersides whenever the wind turned them",
        closing="After that, the old tree seemed to bow whenever the child passed below it.",
        tags={"olive", "leaf"},
    ),
    "dawn": Shrine(
        id="dawn",
        place="the little terrace that faced the eastern sky above the village roofs",
        guardian_name="Eoselle",
        guardian_type="goddess",
        sacred_thing="the first light of dawn",
        shimmer="the sky wore a thin pink thread over the sleeping sea",
        closing="After that, sunrise came soft and golden, as if the day remembered kindness.",
        tags={"dawn", "light"},
    ),
}

FORMS = {
    "reed": Form(
        id="reed",
        label="reed",
        phrase="a slender reed rooted by the bank",
        stillness="could only bend and whisper when the wind passed",
        mark="from then on, the child's voice kept a soft river hush",
        tags={"water", "river"},
    ),
    "sparrow": Form(
        id="sparrow",
        label="sparrow",
        phrase="a little olive-brown sparrow among the branches",
        stillness="could only hop and tremble on the bark",
        mark="from then on, the child's quick laugh always sounded a little like birdsong",
        tags={"olive", "leaf"},
    ),
    "sunflower": Form(
        id="sunflower",
        label="sunflower",
        phrase="a tall sunflower turning its face to the east",
        stillness="could only wait with bright petals open toward the sky",
        mark="from then on, the child woke before sunrise and loved the quiet first light",
        tags={"dawn", "light"},
    ),
}

REMEDIES = {
    "water_song": Remedy(
        id="water_song",
        act="knelt beside the water and sang a low song while pouring a clean bowl back into the stream",
        labor="carried water in a clay bowl again and again until the shrine sounded peaceful",
        gift_line="the song was not a jest now, but a gift",
        qa_text="sang by the river and returned clean water with careful hands",
        gentleness=2,
        tags={"water", "river"},
    ),
    "olive_garland": Remedy(
        id="olive_garland",
        act="wove fallen olive leaves into a small garland and laid it at the roots",
        labor="gathered only leaves already fallen and worked until a neat green circle lay at the tree",
        gift_line="the hands that had pointed in mockery now worked in reverence",
        qa_text="wove a garland from fallen olive leaves and laid it at the roots",
        gentleness=2,
        tags={"olive", "leaf"},
    ),
    "dawn_lamp": Remedy(
        id="dawn_lamp",
        act="lit a little oil lamp before sunrise and kept watch until the first gold touched the terrace",
        labor="guarded the small flame through the chill dark and greeted the morning in silence",
        gift_line="the waiting itself became a prayer",
        qa_text="kept a dawn lamp burning and greeted the first light in silence",
        gentleness=2,
        tags={"dawn", "light"},
    ),
    "great_hymn": Remedy(
        id="great_hymn",
        act="raised a solemn hymn and bowed three times before the shrine",
        labor="sang until the whole place seemed to breathe more gently",
        gift_line="even the air listened",
        qa_text="sang a solemn hymn and bowed before the shrine",
        gentleness=1,
        tags={"water", "river", "olive", "leaf", "dawn", "light"},
    ),
}

HELPER_KINDS = {
    "sister": HelperKind(
        id="sister",
        label="sister",
        type="girl",
        devotion=2,
        kinship="sibling",
        tags={"family", "love"},
    ),
    "brother": HelperKind(
        id="brother",
        label="brother",
        type="boy",
        devotion=2,
        kinship="sibling",
        tags={"family", "love"},
    ),
    "mother": HelperKind(
        id="mother",
        label="mother",
        type="mother",
        devotion=3,
        kinship="parent",
        tags={"family", "love"},
    ),
    "father": HelperKind(
        id="father",
        label="father",
        type="father",
        devotion=3,
        kinship="parent",
        tags={"family", "love"},
    ),
    "friend": HelperKind(
        id="friend",
        label="friend",
        type="girl",
        devotion=1,
        kinship="friend",
        tags={"friend", "love"},
    ),
}

GIRL_NAMES = ["Lysa", "Mira", "Thaleia", "Ione", "Danae", "Chloe", "Rhea", "Daphne"]
BOY_NAMES = ["Leon", "Panos", "Theron", "Nikos", "Iason", "Damon", "Orin", "Milo"]
TRAITS = ["vain", "quicktongued", "showy", "kind", "patient", "faithful"]


def shared_tag(a: set[str], b: set[str]) -> bool:
    return bool(set(a) & set(b))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for shrine_id, shrine in SHRINES.items():
        for form_id, form in FORMS.items():
            if not shared_tag(shrine.tags, form.tags):
                continue
            for remedy_id, remedy in REMEDIES.items():
                if shared_tag(shrine.tags, remedy.tags):
                    combos.append((shrine_id, form_id, remedy_id))
    return sorted(combos)


def helper_devotion(kind_id: str) -> int:
    return HELPER_KINDS[kind_id].devotion


def trait_humility(trait: str) -> int:
    return 0 if trait in PROUD_TRAITS else 1


def full_restoration(kind_id: str, remedy_id: str, trait: str) -> bool:
    remedy = REMEDIES[remedy_id]
    return helper_devotion(kind_id) + remedy.gentleness + trait_humility(trait) >= WRATH_BASE


def explain_rejection(shrine: Shrine, form: Form, remedy: Remedy) -> str:
    if not shared_tag(shrine.tags, form.tags):
        return (
            f"(No story: {form.phrase} does not belong to {shrine.place}, so the "
            f"transformation would feel arbitrary. Choose a form tied to the shrine's domain.)"
        )
    return (
        f"(No story: {remedy.id} does not fit the sacred work of {shrine.place}. "
        f"The repair must soothe the same place the child offended.)"
    )


def helper_type(kind: HelperKind, requested_gender: str) -> str:
    if kind.id == "friend":
        return requested_gender
    return kind.type


def initial_love(kind_id: str) -> float:
    return 1.0 if helper_devotion(kind_id) >= 2 else 0.5


def predict_outcome(world: World, remedy_id: str) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    guardian = sim.get("guardian")
    helper.meters["offering"] += 1
    helper.memes["love"] += 1
    propagate(sim, narrate=False)
    full = full_restoration(
        kind_id=sim.facts["helper_kind"].id,
        remedy_id=remedy_id,
        trait=sim.facts["trait"],
    )
    return {
        "calmed": helper.memes["courage"] >= THRESHOLD,
        "full_restoration": full,
        "wrath": guardian.meters["wrath"],
    }


def introduce(world: World, child: Entity, helper: Entity, shrine: Shrine) -> None:
    world.say(
        f"In the elder days, when even village paths remembered the feet of gods, "
        f"{child.id} and {helper.id} often climbed to {shrine.place}."
    )
    world.say(
        f"There {shrine.shimmer}, and people said that {shrine.guardian_name}, "
        f"keeper of {shrine.sacred_thing}, listened to every honest word."
    )


def establish_bonds(world: World, child: Entity, helper: Entity, kind: HelperKind, trait: str) -> None:
    helper.memes["love"] += initial_love(kind.id)
    child.memes["joy"] += 1
    world.say(
        f"{helper.id}, {child.id}'s {kind.label if kind.id != 'friend' else 'dear friend'}, "
        f"went with {child.pronoun('object')} out of love, for the two were seldom apart."
    )
    world.say(
        f"But {child.id} was {trait}, and loved to make a bright jest whenever silence felt too grand."
    )


def admire_then_mock(world: World, child: Entity, shrine: Shrine) -> None:
    child.memes["pride"] += 1
    world.say(
        f"At first {child.pronoun()} admired the place. Then, seeing {shrine.sacred_thing} so calm, "
        f"{child.pronoun()} let a foolish smile creep across {child.pronoun('possessive')} face."
    )
    world.say(
        f'"If a little laugh can agitate a god, then this shrine must be ruled by a very small one," '
        f"{child.id} said in jest."
    )


def warn(world: World, helper: Entity, child: Entity, shrine: Shrine, remedy: Remedy) -> None:
    pred = predict_outcome(world, remedy.id)
    helper.memes["care"] += 1
    world.facts["predicted_full_restoration"] = pred["full_restoration"]
    world.say(
        f'{helper.id} caught {child.pronoun("possessive")} sleeve. "Do not mock {shrine.guardian_name}," '
        f"{helper.pronoun()} whispered. \"Sacred things hear more than we do.\""
    )


def agitate_guardian(world: World, guardian: Entity, shrine_ent: Entity, child: Entity) -> None:
    guardian.meters["wrath"] += 1
    shrine_ent.meters["unease"] += 0.0
    child.memes["fear"] += 0.0
    propagate(world, narrate=False)
    world.say(
        f"At once the air changed. The leaves turned their pale sides, or the water shivered, "
        f"or the dawn light drew tight like a held breath. The careless words did agitate the hidden power there."
    )


def transform(world: World, child: Entity, form: Form) -> None:
    child.meters["transformed"] += 1
    child.attrs["form"] = form.id
    child.attrs["form_label"] = form.label
    child.attrs["restored"] = False
    propagate(world, narrate=False)
    world.say(
        f"A voice greater than thunder and softer than rain said, "
        f'"Let the tongue that mocked learn stillness." In that moment {child.id} became {form.phrase} and '
        f"{form.stillness}."
    )


def lament(world: World, helper: Entity, child: Entity, shrine: Shrine, kind: HelperKind) -> None:
    helper.memes["grief"] += 1
    helper.memes["love"] += 1
    world.say(
        f"{helper.id} fell to {helper.pronoun('possessive')} knees and wept. "
        f'"Great {shrine.guardian_name}," {helper.pronoun()} cried, "I do not defend the jest, but I love '
        f'{child.id}. Show me what can be mended."'
    )
    if kind.kinship == "parent":
        world.say(
            f"The plea sounded especially deep, for the love of a {kind.label} is a heavy and faithful thing."
        )


def reveal_remedy(world: World, guardian: Entity, remedy: Remedy, shrine: Shrine) -> None:
    guardian.meters["mercy"] += 1
    world.say(
        f"Then the guardian's anger thinned enough for an answer to come: "
        f'"Let love labor where pride mocked. Let the child be freed when another {remedy.act}."'
    )


def perform_remedy(world: World, helper: Entity, remedy: Remedy) -> None:
    helper.meters["offering"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {helper.id} {remedy.act}. {remedy.labor}, and {remedy.gift_line}."
    )


def restore_full(world: World, child: Entity, helper: Entity, guardian: Entity, form: Form) -> None:
    child.meters["transformed"] = 0.0
    child.attrs["restored"] = True
    child.attrs["mark"] = form.mark
    child.memes["humility"] += 1
    guardian.meters["wrath"] = 0.0
    guardian.meters["peace"] += 1
    world.say(
        f"The sacred place softened. Bark became skin, stem became arm, feather became hand, "
        f"and {child.id} stood again beside {helper.id}, trembling but whole."
    )
    world.say(
        f'"I will never turn holy silence into a jest again," {child.id} said. '
        f"Love had brought {child.pronoun('object')} back, and the lesson entered deeper than fear."
    )


def restore_marked(world: World, child: Entity, helper: Entity, guardian: Entity, form: Form) -> None:
    child.meters["transformed"] = 0.0
    child.attrs["restored"] = True
    child.attrs["mark"] = form.mark
    child.memes["humility"] += 1
    guardian.meters["wrath"] = 0.0
    guardian.meters["peace"] += 1
    world.say(
        f"The change loosened slowly. By sunset {child.id} was human once more, but the shrine left a kindly mark: "
        f"{form.mark}."
    )
    world.say(
        f"{child.id} bowed low and thanked both the guardian and {helper.id}. The old pride was gone, "
        f"and a quieter heart stood in its place."
    )


def closing(world: World, child: Entity, shrine: Shrine) -> None:
    world.say(
        f"From that day on, {child.id} came to the shrine with clear hands and gentler words. {shrine.closing}"
    )


def tell(
    shrine: Shrine,
    form: Form,
    remedy: Remedy,
    helper_kind: HelperKind,
    child_name: str = "Lysa",
    child_gender: str = "girl",
    helper_name: str = "Mira",
    helper_gender: str = "girl",
    trait: str = "vain",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"form": "", "restored": False, "mark": ""},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type(helper_kind, helper_gender),
        label=helper_name,
        role="helper",
        traits=["loving"],
        attrs={},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=shrine.guardian_type,
        label=shrine.guardian_name,
        role="guardian",
        traits=["sacred"],
        attrs={},
    ))
    shrine_ent = world.add(Entity(
        id="shrine",
        kind="thing",
        type="shrine",
        label=shrine.place,
        role="shrine",
        traits=[],
        attrs={},
    ))

    guardian.meters["wrath"] = 0.0
    guardian.meters["peace"] = 0.0
    guardian.meters["mercy"] = 0.0
    shrine_ent.meters["unease"] = 0.0
    child.meters["transformed"] = 0.0
    helper.meters["offering"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["pride"] = 0.0
    child.memes["humility"] = 0.0
    child.memes["lonely"] = 0.0
    helper.memes["love"] = initial_love(helper_kind.id)
    helper.memes["care"] = 0.0
    helper.memes["fear"] = 0.0
    helper.memes["grief"] = 0.0
    helper.memes["courage"] = 0.0

    world.facts.update(
        shrine=shrine,
        form=form,
        remedy=remedy,
        helper_kind=helper_kind,
        trait=trait,
        child=child,
        helper=helper,
        guardian=guardian,
        shrine_ent=shrine_ent,
    )

    introduce(world, child, helper, shrine)
    establish_bonds(world, child, helper, helper_kind, trait)

    world.para()
    admire_then_mock(world, child, shrine)
    warn(world, helper, child, shrine, remedy)

    world.para()
    agitate_guardian(world, guardian, shrine_ent, child)
    transform(world, child, form)

    world.para()
    lament(world, helper, child, shrine, helper_kind)
    reveal_remedy(world, guardian, remedy, shrine)
    perform_remedy(world, helper, remedy)

    full = full_restoration(helper_kind.id, remedy.id, trait)
    world.facts["outcome"] = "full_return" if full else "marked_return"
    if full:
        restore_full(world, child, helper, guardian, form)
    else:
        restore_marked(world, child, helper, guardian, form)

    world.para()
    closing(world, child, shrine)
    return world


@dataclass
class StoryParams:
    shrine: str
    form: str
    remedy: str
    helper_kind: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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
    "river": [
        ("Why do many myths place gods near rivers?",
         "Rivers feel alive because they move, sing, and give water to people and fields. In myths, living places are often guarded by spirits or gods.")
    ],
    "olive": [
        ("Why is an olive tree special in old stories?",
         "Olive trees live a very long time and give fruit, oil, and shade. That makes them a symbol of patience, peace, and blessing in many old tales.")
    ],
    "dawn": [
        ("Why does dawn matter in myths?",
         "Dawn is the moment when darkness changes into light. Myths often use it as a sign of hope, mercy, and a new beginning.")
    ],
    "transformation": [
        ("What is a transformation in a myth?",
         "A transformation is when a person changes into another shape, like a bird, plant, or stone. In myths, the change usually teaches something about pride, kindness, or fate.")
    ],
    "jest": [
        ("What is a jest?",
         "A jest is a joke or teasing remark. A jest can be playful, but it can also hurt when it makes fun of something serious or sacred.")
    ],
    "love": [
        ("How can love help in a myth?",
         "Love often gives someone the courage to keep helping when a task is hard. In many myths, love is stronger than fear and helps mend what pride has broken.")
    ],
    "reed": [
        ("What is a reed?",
         "A reed is a tall, slender plant that grows near water. Wind can bend it, so it often appears in stories about rivers and whispers.")
    ],
    "sparrow": [
        ("What is a sparrow?",
         "A sparrow is a small bird with quick movements and a chirping voice. Because it is light and lively, stories often use it to show smallness or sudden change.")
    ],
    "sunflower": [
        ("Why does a sunflower fit a dawn story?",
         "A sunflower turns toward the light as it grows. That makes it a good symbol for seeking warmth, truth, or morning light.")
    ],
}
KNOWLEDGE_ORDER = [
    "transformation", "jest", "love", "river", "olive", "dawn", "reed", "sparrow", "sunflower"
]


CURATED = [
    StoryParams(
        shrine="river",
        form="reed",
        remedy="water_song",
        helper_kind="sister",
        child_name="Lysa",
        child_gender="girl",
        helper_name="Mira",
        helper_gender="girl",
        trait="vain",
    ),
    StoryParams(
        shrine="olive",
        form="sparrow",
        remedy="olive_garland",
        helper_kind="mother",
        child_name="Theron",
        child_gender="boy",
        helper_name="Althea",
        helper_gender="girl",
        trait="showy",
    ),
    StoryParams(
        shrine="dawn",
        form="sunflower",
        remedy="great_hymn",
        helper_kind="friend",
        child_name="Ione",
        child_gender="girl",
        helper_name="Chloe",
        helper_gender="girl",
        trait="kind",
    ),
    StoryParams(
        shrine="dawn",
        form="sunflower",
        remedy="dawn_lamp",
        helper_kind="father",
        child_name="Milo",
        child_gender="boy",
        helper_name="Damon",
        helper_gender="boy",
        trait="quicktongued",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    shrine = f["shrine"]
    form = f["form"]
    outcome = f["outcome"]
    if outcome == "full_return":
        ending = "and the child is fully restored through love and a fitting act of repair"
    else:
        ending = "and the child is restored with a gentle lasting mark that shows what changed"
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the words "agitate", "love", and "jest".',
        f"Tell a mythic story where {child.id} mocks a sacred place, is transformed into {form.phrase}, and {helper.id} helps undo the spell.",
        f"Write a child-facing myth about pride, transformation, and mercy at {shrine.place}, where {ending}.",
    ]


def pair_noun(kind: HelperKind) -> str:
    if kind.kinship == "parent":
        return "a child and a loving parent"
    if kind.kinship == "sibling":
        return "two siblings"
    return "two close friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    shrine = f["shrine"]
    form = f["form"]
    remedy = f["remedy"]
    kind = f["helper_kind"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(kind)}, {child.id} and {helper.id}, at {shrine.place}. "
            f"The story also includes {shrine.guardian_name}, the guardian of that sacred place."
        ),
        (
            f"Why did {shrine.guardian_name} punish {child.id}?",
            f"{child.id} made a foolish jest about the sacred place and mocked what should have been honored. "
            f"That disrespect did agitate the guardian's anger."
        ),
        (
            f"What did {child.id} turn into?",
            f"{child.id} was transformed into {form.phrase}. "
            f"The new form matched the shrine, so the change felt like part of the place itself."
        ),
        (
            f"Why did {helper.id} try to help?",
            f"{helper.id} loved {child.id} and could not bear to leave {child.pronoun('object')} under the spell. "
            f"That love gave {helper.pronoun('object')} the courage to beg for mercy and do the hard repair."
        ),
        (
            f"What did {helper.id} do to mend the wrong?",
            f"{helper.id} {remedy.qa_text}. "
            f"It was the right kind of work for that shrine, so it answered pride with care instead of another insult."
        ),
    ]
    if outcome == "full_return":
        qa.append((
            f"How did the story end?",
            f"{child.id} became human again and promised never to turn holy silence into a jest. "
            f"The ending shows that love and humility can calm anger and put things right."
        ))
    else:
        qa.append((
            f"How did the story end?",
            f"{child.id} became human again, but kept a gentle sign of the transformation: {form.mark}. "
            f"The mark mattered because it helped {child.pronoun('object')} remember the lesson forever."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"transformation", "jest", "love"}
    shrine = f["shrine"]
    form = f["form"]
    if "river" in shrine.tags:
        tags.add("river")
    if "olive" in shrine.tags:
        tags.add("olive")
    if "dawn" in shrine.tags:
        tags.add("dawn")
    tags.add(form.id)
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
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, R) :- shrine(S), form(F), remedy(R), shrine_tag(S, T), form_tag(F, T), remedy_tag(R, T).

devotion_of(D) :- chosen_helper(H), devotion(H, D).
gentleness_of(G) :- chosen_remedy(R), gentleness(R, G).
humility_bonus(0) :- chosen_trait(T), proud_trait(T).
humility_bonus(1) :- chosen_trait(T), not proud_trait(T).
score(D + G + H) :- devotion_of(D), gentleness_of(G), humility_bonus(H).

full_return :- score(S), wrath_base(W), S >= W.
marked_return :- not full_return.

outcome(full_return) :- full_return.
outcome(marked_return) :- marked_return.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for shrine_id, shrine in SHRINES.items():
        lines.append(asp.fact("shrine", shrine_id))
        for tag in sorted(shrine.tags):
            lines.append(asp.fact("shrine_tag", shrine_id, tag))
    for form_id, form in FORMS.items():
        lines.append(asp.fact("form", form_id))
        for tag in sorted(form.tags):
            lines.append(asp.fact("form_tag", form_id, tag))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("gentleness", remedy_id, remedy.gentleness))
        for tag in sorted(remedy.tags):
            lines.append(asp.fact("remedy_tag", remedy_id, tag))
    for kind_id, kind in HELPER_KINDS.items():
        lines.append(asp.fact("helper_kind", kind_id))
        lines.append(asp.fact("devotion", kind_id, kind.devotion))
    for trait in sorted(PROUD_TRAITS):
        lines.append(asp.fact("proud_trait", trait))
    lines.append(asp.fact("wrath_base", WRATH_BASE))
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
        asp.fact("chosen_helper", params.helper_kind),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "full_return" if full_restoration(params.helper_kind, params.remedy, params.trait) else "marked_return"


def _validate_params(params: StoryParams) -> None:
    if params.shrine not in SHRINES:
        raise StoryError(f"(Unknown shrine: {params.shrine})")
    if params.form not in FORMS:
        raise StoryError(f"(Unknown form: {params.form})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")
    if params.helper_kind not in HELPER_KINDS:
        raise StoryError(f"(Unknown helper kind: {params.helper_kind})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.helper_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown helper gender: {params.helper_gender})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if (params.shrine, params.form, params.remedy) not in set(valid_combos()):
        raise StoryError(explain_rejection(SHRINES[params.shrine], FORMS[params.form], REMEDIES[params.remedy]))


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
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            rc = 1
            print(f"Unexpected resolution failure for seed {s}.")
            continue
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
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic transformation storyworld: a jest agitates a guardian, love repairs the harm."
    )
    ap.add_argument("--shrine", choices=sorted(SHRINES))
    ap.add_argument("--form", choices=sorted(FORMS))
    ap.add_argument("--remedy", choices=sorted(REMEDIES))
    ap.add_argument("--helper-kind", choices=sorted(HELPER_KINDS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid story triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.shrine is None or combo[0] == args.shrine)
        and (args.form is None or combo[1] == args.form)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if args.shrine and args.form and args.remedy:
        if (args.shrine, args.form, args.remedy) not in set(valid_combos()):
            raise StoryError(explain_rejection(SHRINES[args.shrine], FORMS[args.form], REMEDIES[args.remedy]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    shrine_id, form_id, remedy_id = rng.choice(sorted(combos))
    helper_kind = args.helper_kind or rng.choice(sorted(HELPER_KINDS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=child_name)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(
        shrine=shrine_id,
        form=form_id,
        remedy=remedy_id,
        helper_kind=helper_kind,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        trait=trait,
    )
    _validate_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        shrine=SHRINES[params.shrine],
        form=FORMS[params.form],
        remedy=REMEDIES[params.remedy],
        helper_kind=HELPER_KINDS[params.helper_kind],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (shrine, form, remedy) combos:\n")
        for shrine_id, form_id, remedy_id in combos:
            print(f"  {shrine_id:8} {form_id:10} {remedy_id}")
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
            header = (
                f"### {p.child_name}: {p.shrine} / {p.form} / {p.remedy} "
                f"({p.helper_kind}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
