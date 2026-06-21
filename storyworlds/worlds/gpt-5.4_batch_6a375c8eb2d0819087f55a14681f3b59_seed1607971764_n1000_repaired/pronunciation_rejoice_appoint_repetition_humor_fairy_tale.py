#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pronunciation_rejoice_appoint_repetition_humor_fairy_tale.py
=======================================================================================

A standalone story world for a small fairy-tale domain: a child at a castle
hopes to be appointed as the royal greeter, but first must learn the tricky
pronunciation of a magical guest's name.

This world is built to support a narrow, reasoned family of stories:
- a ruler needs someone at the right place in the castle grounds,
- a child eagerly tries to say a visitor's elaborate name,
- the first attempt goes wrong in a funny way,
- a helper teaches a fitting practice method,
- the child tries again,
- the ruler says, "I appoint you...",
- and everyone begins to rejoice.

The domain uses repetition and gentle humor, with a fairy-tale tone.
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "queen", "fairy", "woman", "princess"}
        male = {"boy", "king", "wizard", "man", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {"queen": "queen", "king": "king"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class GuestName:
    id: str
    spoken: str
    kind_label: str
    arrival_place: str
    challenge: str
    beats: int
    bounce: str
    humor_slip: str
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
class PracticeMethod:
    id: str
    label: str
    helps: set[str] = field(default_factory=set)
    power: int = 0
    teach_text: str = ""
    repeat_text: str = ""
    qa_text: str = ""
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
class CourtRole:
    id: str
    label: str
    place: str
    duty: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
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
class StoryParams:
    guest: str
    method: str
    role: str
    child_name: str
    child_gender: str
    ruler_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_stumble_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    hall = world.get("hall")
    if child.meters["stumble"] >= THRESHOLD:
        sig = ("stumble_worry",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            hall.meters["delay"] += 1
            out.append("__stumble__")
    return out


def _r_ready_confident(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    needed = float(world.facts["needed_clarity"])
    if child.meters["clarity"] >= needed:
        sig = ("ready",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["confidence"] += 1
            world.facts["ready"] = True
            out.append("__ready__")
    return out


def _r_appoint_rejoice(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    court = world.get("court")
    if child.meters["appointed"] >= THRESHOLD:
        sig = ("rejoice",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["joy"] += 1
            court.memes["joy"] += 1
            world.facts["rejoice"] = True
            out.append("__rejoice__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stumble_worry", tag="social", apply=_r_stumble_worry),
    Rule(name="ready_confident", tag="social", apply=_r_ready_confident),
    Rule(name="appoint_rejoice", tag="social", apply=_r_appoint_rejoice),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def method_fits(guest: GuestName, method: PracticeMethod) -> bool:
    return guest.challenge in method.helps and method.power >= guest.beats


def role_fits(guest: GuestName, role: CourtRole) -> bool:
    return guest.arrival_place == role.place


def valid_combo(guest: GuestName, method: PracticeMethod, role: CourtRole) -> bool:
    return method_fits(guest, method) and role_fits(guest, role)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for guest_id, guest in GUESTS.items():
        for method_id, method in METHODS.items():
            for role_id, role in ROLES.items():
                if valid_combo(guest, method, role):
                    combos.append((guest_id, method_id, role_id))
    return sorted(combos)


def explain_rejection(guest: GuestName, method: PracticeMethod, role: CourtRole) -> str:
    if not role_fits(guest, role):
        return (
            f"(No story: {guest.spoken} arrives at the {guest.arrival_place}, but "
            f"the {role.label} belongs at the {role.place}. The child must be "
            f"appointed where the guest actually appears.)"
        )
    if guest.challenge not in method.helps:
        return (
            f"(No story: {method.label} does not teach the right kind of pronunciation "
            f"for {guest.spoken}. This guest needs help with {guest.challenge.replace('_', ' ')}.)"
        )
    if method.power < guest.beats:
        return (
            f"(No story: {method.label} is too weak for a {guest.beats}-beat name. "
            f"The practice must be strong enough to carry the full pronunciation.)"
        )
    return "(No story: this combination does not make a reasonable court tale.)"


def outcome_of(params: StoryParams) -> str:
    guest = GUESTS[params.guest]
    method = METHODS[params.method]
    role = ROLES[params.role]
    return "appointed" if valid_combo(guest, method, role) else "not_ready"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_success(world: World, method: PracticeMethod) -> dict:
    sim = world.copy()
    child = sim.get("child")
    guest = sim.facts["guest_cfg"]
    child.meters["clarity"] += method.power
    child.attrs["used_method"] = method.id
    propagate(sim, narrate=False)
    return {
        "ready": bool(sim.facts.get("ready")),
        "clarity": child.meters["clarity"],
        "needed": sim.facts["needed_clarity"],
        "challenge": guest.challenge,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def opening(world: World, child: Entity, ruler: Entity, helper: Entity, guest: GuestName, role: CourtRole) -> None:
    world.say(
        f"In the bright stone castle of Cloverkeep, {child.id} loved to stand on tiptoe "
        f"and listen when messages came over the morning wind."
    )
    world.say(
        f"One gold-splashed dawn, {ruler.title_word.capitalize()} {ruler.id} announced that "
        f"{guest.spoken}, a {guest.kind_label}, would soon appear at the {guest.arrival_place}."
    )
    world.say(
        f'"Whoever greets our guest clearly may be my {role.label}," said {ruler.title_word} '
        f"{ruler.id}. At once, {child.id}'s heart gave a hopeful jump."
    )
    child.memes["hope"] += 1


def first_try(world: World, child: Entity, guest: GuestName) -> None:
    child.meters["stumble"] += 1
    child.meters["clarity"] = max(0.0, guest.beats - 2)
    world.facts["first_slip"] = guest.humor_slip
    propagate(world, narrate=False)
    world.say(
        f"{child.id} puffed up {child.pronoun('possessive')} chest and tried the grand pronunciation "
        f"at once. But instead of saying \"{guest.spoken},\" {child.pronoun()} cried, "
        f"\"{guest.humor_slip}!\""
    )
    world.say(
        "A sleepy raven on the gate gave a shocked croak. A cook in the yard laughed so hard "
        "that three plum tarts wobbled on her tray."
    )
    if child.memes["worry"] >= THRESHOLD:
        world.say(
            f"{child.id}'s ears turned pink. The name was not wicked, only twisty, but it felt too big "
            f"for one small mouth."
        )


def helper_teaches(world: World, child: Entity, helper: Entity, guest: GuestName, method: PracticeMethod) -> None:
    pred = predict_success(world, method)
    world.facts["predicted_ready"] = pred["ready"]
    child.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id}, the castle {helper.type}, bent down with a smile. "
        f"\"A hard name is only a name that wants a path,\" {helper.pronoun()} said."
    )
    world.say(method.teach_text.format(name=guest.spoken, bounce=guest.bounce))
    world.say(
        f'Together they practiced: "{method.repeat_text.format(name=guest.spoken, bounce=guest.bounce)}" '
        f'Once. Twice. Thrice.'
    )
    if pred["ready"]:
        world.say(
            f"Each time, the sounds sat straighter. The pronunciation stopped slipping about like a fish "
            f"and began to march in a tidy row."
        )


def second_try(world: World, child: Entity, guest: GuestName, method: PracticeMethod) -> None:
    child.attrs["used_method"] = method.id
    child.meters["clarity"] += method.power
    child.meters["stumble"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} tried again. \"{guest.spoken},\" {child.pronoun()} said, slow and bright, "
        f"with every beat in its proper place."
    )
    if world.facts.get("ready"):
        world.say(
            "This time the raven did not croak. It bowed, as if even birds could hear when a name had landed properly."
        )


def appoint_child(world: World, child: Entity, ruler: Entity, role: CourtRole, guest: GuestName) -> None:
    child.meters["appointed"] += 1
    propagate(world, narrate=False)
    world.facts["appointed_role"] = role.id
    world.say(
        f'{ruler.title_word.capitalize()} {ruler.id} clapped once. "Well said," {ruler.pronoun()} declared. '
        f'"I appoint you my {role.label}. You shall {role.duty} when {guest.spoken} arrives."'
    )


def arrival_and_ending(world: World, child: Entity, guest: GuestName, role: CourtRole) -> None:
    child.memes["pride"] += 1
    court = world.get("court")
    court.memes["joy"] += 1
    world.say(
        f"Just then a silver shimmer curled through the air, and {guest.spoken} stepped out smiling, "
        f"exactly where the message had promised."
    )
    world.say(
        f"{child.id} bowed and spoke the name once more, and not a single syllable tumbled over its shoes."
    )
    if world.facts.get("rejoice"):
        world.say(
            f"The court began to rejoice. Even the raven cried the name after {child.pronoun('object')}—almost correctly."
        )
    world.say(role.ending_image.format(child=child.id, guest=guest.spoken))


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    guest: GuestName,
    method: PracticeMethod,
    role: CourtRole,
    child_name: str = "Poppy",
    child_gender: str = "girl",
    ruler_type: str = "queen",
    helper_name: str = "Mirth",
    helper_type: str = "fairy",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    ruler = world.add(Entity(id="ruler", kind="character", type=ruler_type, label="the ruler", role="ruler"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    hall = world.add(Entity(id="hall", kind="thing", type="hall", label="the castle hall"))
    court = world.add(Entity(id="court", kind="thing", type="court", label="the court"))

    child.id = child_name
    ruler.id = "Queen Hazel" if ruler_type == "queen" else "King Alder"
    helper.id = helper_name

    world.facts["guest_cfg"] = guest
    world.facts["method_cfg"] = method
    world.facts["role_cfg"] = role
    world.facts["needed_clarity"] = float(guest.beats)
    world.facts["ready"] = False
    world.facts["rejoice"] = False
    world.facts["first_slip"] = ""
    world.facts["predicted_ready"] = False
    world.facts["appointed_role"] = ""

    child.meters["clarity"] = 0.0
    child.meters["stumble"] = 0.0
    child.meters["appointed"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["pride"] = 0.0
    helper.memes["care"] = 0.0
    hall.meters["delay"] = 0.0
    court.memes["joy"] = 0.0

    opening(world, child, ruler, helper, guest, role)
    world.para()
    first_try(world, child, guest)
    helper_teaches(world, child, helper, guest, method)
    world.para()
    second_try(world, child, guest, method)
    appoint_child(world, child, ruler, role, guest)
    world.para()
    arrival_and_ending(world, child, guest, role)

    world.facts.update(
        child=child,
        ruler=ruler,
        helper=helper,
        hall=hall,
        court=court,
        guest=guest,
        method=method,
        role=role,
        success=child.meters["appointed"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
GUESTS = {
    "bristlewhistle": GuestName(
        id="bristlewhistle",
        spoken="Bristlewhistle",
        kind_label="hedge fairy with a hat like a teacup",
        arrival_place="rose gate",
        challenge="whistle",
        beats=3,
        bounce="bris-tle-whis-tle",
        humor_slip="Biscuit-whistle",
        tags={"pronunciation", "fairy", "whistle"},
    ),
    "rumblethimble": GuestName(
        id="rumblethimble",
        spoken="Rumblethimble",
        kind_label="bridge troll who wore velvet mittens",
        arrival_place="moon bridge",
        challenge="many_beats",
        beats=4,
        bounce="rum-ble-thim-ble",
        humor_slip="Rumble-wobble",
        tags={"pronunciation", "beats", "bridge"},
    ),
    "larkalora": GuestName(
        id="larkalora",
        spoken="Larkalora",
        kind_label="singing lake sprite with lily-pad slippers",
        arrival_place="lily stair",
        challenge="rolling_l",
        beats=4,
        bounce="lar-ka-lo-ra",
        humor_slip="Lumpy-Laura",
        tags={"pronunciation", "lake", "song"},
    ),
}

METHODS = {
    "feather_blow": PracticeMethod(
        id="feather_blow",
        label="the feather-blow game",
        helps={"whistle"},
        power=3,
        teach_text='"{name} likes airy sounds," said the helper. "Blow a feather, then let the name float after it."',
        repeat_text="{name}, feather first, {name}",
        qa_text="They blew a feather into the air and used the soft breath to shape the whistling sounds.",
        tags={"breathing", "pronunciation"},
    ),
    "drum_steps": PracticeMethod(
        id="drum_steps",
        label="the drum-step rhyme",
        helps={"many_beats"},
        power=4,
        teach_text='The helper tapped a tiny drum. "One beat for each piece: {bounce}. Let your feet remember what your tongue forgets."',
        repeat_text="{bounce}, {name}, {bounce}",
        qa_text="They matched each syllable to a drumbeat, so the long name could be said one piece at a time.",
        tags={"rhythm", "pronunciation"},
    ),
    "mirror_song": PracticeMethod(
        id="mirror_song",
        label="the silver mirror song",
        helps={"rolling_l"},
        power=4,
        teach_text='The helper held up a silver mirror. "Watch how your tongue lifts for the l sounds, and sing the name instead of pushing it."',
        repeat_text="{name} in the mirror, {name} in the song",
        qa_text="They used a silver mirror and sang the name slowly, which helped the child place the l sounds clearly.",
        tags={"mirror", "pronunciation"},
    ),
    "honey_sip": PracticeMethod(
        id="honey_sip",
        label="a honey sip",
        helps={"whistle"},
        power=2,
        teach_text='The helper offered one tiny sip of honeyed water. "Sweetness is nice, but sweetness alone cannot carry a whole grand name."',
        repeat_text="{name}",
        qa_text="They tried a sweet sip first, but it was only a little comfort, not a full practice plan.",
        tags={"drink"},
    ),
}

ROLES = {
    "gate_greeter": CourtRole(
        id="gate_greeter",
        label="Gate Greeter",
        place="rose gate",
        duty="open the morning welcome at the rose gate",
        ending_image="{child} stood by the rose gate with a ribboned staff, and the roses seemed to nod whenever {guest} was spoken.",
        tags={"gate"},
    ),
    "bridge_caller": CourtRole(
        id="bridge_caller",
        label="Bridge Caller",
        place="moon bridge",
        duty="call the guest across the moon bridge",
        ending_image="{child} stood upon the moon bridge, calling for {guest}, while the water below giggled at the echo.",
        tags={"bridge"},
    ),
    "stair_herald": CourtRole(
        id="stair_herald",
        label="Stair Herald",
        place="lily stair",
        duty="sing the first welcome on the lily stair",
        ending_image="{child} waited on the lily stair with a lantern shell in hand, and {guest}'s name rang as neatly as a bell.",
        tags={"stair"},
    ),
}

GIRL_NAMES = ["Poppy", "Nella", "Ivy", "Mira", "Elsie", "Wren"]
BOY_NAMES = ["Rowan", "Tobin", "Milo", "Perrin", "Jory", "Finn"]
HELPERS = [
    ("Mirth", "fairy"),
    ("Bramble", "wizard"),
    ("Tansy", "fairy"),
    ("Pip", "wizard"),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "pronunciation": [
        (
            "What does pronunciation mean?",
            "Pronunciation is the way we say a word out loud. Good pronunciation means the sounds come in the right order so other people can understand the word."
        )
    ],
    "rhythm": [
        (
            "How can rhythm help with a hard word?",
            "Rhythm can break a long word into small beats. Saying one beat at a time helps your mouth remember where each sound belongs."
        )
    ],
    "mirror": [
        (
            "Why might a mirror help someone say a word?",
            "A mirror lets you watch your mouth and tongue as you speak. That can help you notice how to shape tricky sounds more clearly."
        )
    ],
    "breathing": [
        (
            "Why does calm breathing help speech?",
            "Calm breathing gives your voice a steady start. When you are not rushing, the sounds can come out more clearly."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a small magical being from storybook worlds. Fairies often help with problems by using clever, gentle magic."
        )
    ],
    "bridge": [
        (
            "Why do voices echo near a bridge over water?",
            "Sound can bounce back from stone and water, which makes an echo. That is why words sometimes seem to answer themselves in such places."
        )
    ],
}
KNOWLEDGE_ORDER = ["pronunciation", "rhythm", "mirror", "breathing", "fairy", "bridge"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    guest = world.facts["guest"]
    role = world.facts["role"]
    return [
        f'Write a fairy tale for ages 3 to 5 that includes the word "pronunciation" and ends with a child being told, "I appoint you."',
        f"Tell a gentle, funny castle story where {child.id} must learn to say {guest.spoken} correctly before becoming the {role.label}.",
        'Write a fairy-tale story that uses repetition for practice, a humorous mistaken name, and an ending where the court begins to rejoice.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    ruler = world.facts["ruler"]
    helper = world.facts["helper"]
    guest = world.facts["guest"]
    method = world.facts["method"]
    role = world.facts["role"]
    slip = world.facts.get("first_slip", guest.humor_slip)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who wanted an important castle job. {ruler.id} and {helper.id} also mattered because one set the challenge and the other helped solve it."
        ),
        (
            f"Why did {child.id} want to learn the pronunciation of {guest.spoken}?",
            f"{child.id} wanted to greet the guest properly and hoped to become the {role.label}. The ruler promised to appoint the child who could say the name clearly at the right place."
        ),
        (
            f"What went wrong the first time {child.id} tried to say the name?",
            f"{child.id} said \"{slip}\" instead of \"{guest.spoken}.\" That mistake was funny to the court, but it also made {child.pronoun('object')} worry because the grand name still felt twisty."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} used {method.label}. {method.qa_text}"
        ),
        (
            f"Why did the practice work the second time?",
            f"The practice matched the kind of hard sounds in {guest.spoken}, and it was strong enough for the whole name. Because the method fit the problem, {child.id}'s voice became clear enough to say every beat in order."
        ),
        (
            "How did the story end?",
            f"{ruler.id} said, \"I appoint you my {role.label},\" and the court began to rejoice. In the ending image, {child.id} was already standing where the welcome would happen, proving the child had truly changed from hopeful to ready."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    guest = world.facts["guest"]
    method = world.facts["method"]
    tags = set(guest.tags) | set(method.tags)
    if world.facts["role"].id == "bridge_caller":
        tags.add("bridge")
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:14} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts: ready={world.facts.get('ready')} rejoice={world.facts.get('rejoice')} appointed_role={world.facts.get('appointed_role')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        guest="bristlewhistle",
        method="feather_blow",
        role="gate_greeter",
        child_name="Poppy",
        child_gender="girl",
        ruler_type="queen",
        helper_name="Mirth",
        helper_type="fairy",
    ),
    StoryParams(
        guest="rumblethimble",
        method="drum_steps",
        role="bridge_caller",
        child_name="Rowan",
        child_gender="boy",
        ruler_type="king",
        helper_name="Bramble",
        helper_type="wizard",
    ),
    StoryParams(
        guest="larkalora",
        method="mirror_song",
        role="stair_herald",
        child_name="Ivy",
        child_gender="girl",
        ruler_type="queen",
        helper_name="Tansy",
        helper_type="fairy",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits_method(G, M) :- guest(G), method(M), challenge(G, C), helps(M, C), beats(G, B), power(M, P), P >= B.
fits_role(G, R)   :- guest(G), role(R), arrival_place(G, L), role_place(R, L).
valid(G, M, R)    :- fits_method(G, M), fits_role(G, R).

outcome(appointed) :- chosen_guest(G), chosen_method(M), chosen_role(R), valid(G, M, R).
outcome(not_ready) :- chosen_guest(G), chosen_method(M), chosen_role(R), not valid(G, M, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for guest_id, guest in GUESTS.items():
        lines.append(asp.fact("guest", guest_id))
        lines.append(asp.fact("challenge", guest_id, guest.challenge))
        lines.append(asp.fact("beats", guest_id, guest.beats))
        lines.append(asp.fact("arrival_place", guest_id, guest.arrival_place))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("power", method_id, method.power))
        for item in sorted(method.helps):
            lines.append(asp.fact("helps", method_id, item))
    for role_id, role in ROLES.items():
        lines.append(asp.fact("role", role_id))
        lines.append(asp.fact("role_place", role_id, role.place))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_guest", params.guest),
            asp.fact("chosen_method", params.method),
            asp.fact("chosen_role", params.role),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases: list[StoryParams] = []
    for guest_id in GUESTS:
        for method_id in METHODS:
            for role_id in ROLES:
                cases.append(
                    StoryParams(
                        guest=guest_id,
                        method=method_id,
                        role=role_id,
                        child_name="Poppy",
                        child_gender="girl",
                        ruler_type="queen",
                        helper_name="Mirth",
                        helper_type="fairy",
                    )
                )
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a child learns a tricky name, earns an appointment, and the court begins to rejoice."
    )
    ap.add_argument("--guest", choices=GUESTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ruler", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.guest and args.method and args.role:
        guest = GUESTS[args.guest]
        method = METHODS[args.method]
        role = ROLES[args.role]
        if not valid_combo(guest, method, role):
            raise StoryError(explain_rejection(guest, method, role))

    combos = [
        combo
        for combo in valid_combos()
        if (args.guest is None or combo[0] == args.guest)
        and (args.method is None or combo[1] == args.method)
        and (args.role is None or combo[2] == args.role)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    guest_id, method_id, role_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    ruler_type = args.ruler or rng.choice(["queen", "king"])
    helper_name, helper_type = rng.choice(HELPERS)

    return StoryParams(
        guest=guest_id,
        method=method_id,
        role=role_id,
        child_name=child_name,
        child_gender=gender,
        ruler_type=ruler_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.guest not in GUESTS:
        raise StoryError(f"(Unknown guest: {params.guest})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.role not in ROLES:
        raise StoryError(f"(Unknown role: {params.role})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")
    if params.ruler_type not in {"queen", "king"}:
        raise StoryError(f"(Unknown ruler type: {params.ruler_type})")

    guest = GUESTS[params.guest]
    method = METHODS[params.method]
    role = ROLES[params.role]
    if not valid_combo(guest, method, role):
        raise StoryError(explain_rejection(guest, method, role))

    world = tell(
        guest=guest,
        method=method,
        role=role,
        child_name=params.child_name,
        child_gender=params.child_gender,
        ruler_type=params.ruler_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
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
        print(f"{len(combos)} valid (guest, method, role) combos:\n")
        for guest_id, method_id, role_id in combos:
            print(f"  {guest_id:15} {method_id:13} {role_id}")
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
            header = f"### {p.child_name}: {p.guest} with {p.method} -> {p.role}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
