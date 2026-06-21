#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/clarify_sound_effects_bad_ending_comedy.py
=========================================================================

A tiny comedy storyworld about a misunderstanding, a few loud sound effects,
and a bad ending that still feels child-facing and playful.

Premise
-------
A child tries to use sound effects for a pretend game, but the noises are
misread, the situation escalates, and the ending goes wrong in a funny,
contained way: a spilled bowl, a ruined snack, a blamed squeak, and nobody
quite managing to clarify things in time.

The world is intentionally small:
- typed entities with physical meters and emotional memes
- simulated state drives the prose
- one bad ending branch, one avertable-ish branch that still ends badly
- a Python reasonableness gate plus inline ASP twin
- three QA sets grounded in the simulated state

This file is standalone and uses only the stdlib plus the shared repo helpers.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOUND_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)
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
class Setting:
    id: str
    place: str
    setup: str
    mood: str
    messable: bool = True
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
class SoundEffect:
    id: str
    onom: str
    action: str
    body: str
    loudness: int
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    breakable: bool = False
    spillable: bool = False
    sticky: bool = False
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
class Response:
    id: str
    sense: int
    power: int
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


@dataclass
class StoryParams:
    setting: str
    sound: str
    object: str
    response: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen", "the table was set for a snack game", "bright", True),
    "playroom": Setting("playroom", "the playroom", "pillows made a tiny stage", "cozy", True),
    "garage": Setting("garage", "the garage", "boxes and a toy bin made a noisy cave", "echoey", True),
}

SOUNDS = {
    "squeak": SoundEffect("squeak", "SQUEAK!", "press the toy", "the toy mouse", 2, {"toy", "noise"}),
    "boombox": SoundEffect("boombox", "BOOM!", "tap the old speaker", "the old speaker", 4, {"speaker", "noise"}),
    "drum": SoundEffect("drum", "BAP-BAP-BAP!", "bang the drum", "the drum", 3, {"drum", "noise"}),
    "foghorn": SoundEffect("foghorn", "HONK!", "push the big button", "the giant horn", 5, {"horn", "noise"}),
}

OBJECTS = {
    "bowl": ObjectThing("bowl", "bowl", "a bowl of jelly snack", breakable=True, spillable=True, tags={"bowl", "food"}),
    "juice": ObjectThing("juice", "juice box", "a juice box", spillable=True, tags={"juice", "food"}),
    "cookies": ObjectThing("cookies", "cookie plate", "a plate of cookies", spillable=False, breakable=False, tags={"cookies", "food"}),
    "vase": ObjectThing("vase", "vase", "a tall vase", breakable=True, spillable=True, tags={"vase"}),
}

RESPONSES = {
    "clarify": Response(
        "clarify", 3, 3,
        "said, 'Wait -- let me clarify,' and reached for the towel before the mess got bigger",
        "tried to clarify, but the mess had already turned into a splash parade",
        "managed to clarify the confusion and stop the mess",
        {"clarify", "help"}),
    "stomp": Response(
        "stomp", 2, 2,
        "stomped toward the trouble with a brave little thump",
        "stomped, slipped, and made the mess twice as funny and twice as bad",
        "stomped the problem down",
        {"help"}),
    "freeze": Response(
        "freeze", 2, 1,
        "froze in place like a tiny statue",
        "froze too long, and the snack went flying",
        "froze the chaos for a moment",
        {"help"}),
    "water": Response(
        "water", 1, 1,
        "grabbed a cup of water and made the splash even splashier",
        "used water, which only added to the puddle party",
        "used water on the mess",
        {"bad"}),
}

GIRLS = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOYS = ["Max", "Leo", "Finn", "Ben", "Theo", "Sam"]
TRAITS = ["curious", "silly", "careful", "goofy", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        if not setting.messable:
            continue
        for snd_id, snd in SOUNDS.items():
            for oid, obj in OBJECTS.items():
                if snd.loudness >= 3 and (obj.spillable or obj.breakable):
                    combos.append((sid, snd_id, oid))
    return combos


def reason_gate(sound: SoundEffect, obj: ObjectThing) -> bool:
    return sound.loudness >= 3 and (obj.spillable or obj.breakable)


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SOUND_MIN]


def explain_rejection(sound: SoundEffect, obj: ObjectThing) -> str:
    return f"(No story: {sound.onom} near {obj.label} is not messy enough for this comedy.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': sense={r.sense} is too low; this world prefers kinder, clearer fixes.)"


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters.get("mess", 0.0) < THRESHOLD:
            continue
        sig = ("spill", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        obj = world.get("object")
        obj.meters["spilled"] = obj.meters.get("spilled", 0.0) + 1
        world.get("adult").memes["alarm"] = world.get("adult").memes.get("alarm", 0.0) + 1
        world.get("helper").memes["guilt"] = world.get("helper").memes.get("guilt", 0.0) + 1
        out.append("__spill__")
    return out


def _r_confusion(world: World) -> list[str]:
    if world.get("helper").memes.get("confused", 0.0) < THRESHOLD:
        return []
    sig = ("confusion",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child").memes["excitement"] = world.get("child").memes.get("excitement", 0.0) + 1
    return ["__confusion__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_spill, _r_confusion):
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if not m.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, sound: SoundEffect, obj: ObjectThing) -> dict:
    sim = world.copy()
    sim.get("child").meters["mess"] = 1.0
    sim.get("helper").memes["confused"] = 1.0
    _trigger(sim, narrate=False)
    return {
        "spilled": sim.get("object").meters.get("spilled", 0.0) >= THRESHOLD,
        "alarm": sim.get("adult").memes.get("alarm", 0.0),
    }


def _trigger(world: World, narrate: bool = True) -> None:
    world.get("child").meters["mess"] = world.get("child").meters.get("mess", 0.0) + 1
    world.get("helper").memes["confused"] = world.get("helper").memes.get("confused", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"On a bright afternoon, {child.id} and {helper.id} turned {setting.place} into a tiny stage."
    )
    world.say(f"{setting.setup}.")
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1


def play_sound(world: World, child: Entity, sound: SoundEffect) -> None:
    world.say(
        f'{child.id} wanted to make a funny noise, so {child.pronoun()} went, "{sound.onom}"'
    )
    world.say(f"The sound made everyone blink and grin at the same time.")


def clarify_attempt(world: World, helper: Entity, child: Entity, sound: SoundEffect) -> None:
    helper.memes["confused"] = helper.memes.get("confused", 0.0) + 1
    world.say(
        f'{helper.id} squinted. "I think you want to {sound.action}," {helper.pronoun()} said, '
        f'but then {helper.pronoun()} added, "Or maybe you want a snack?"'
    )
    world.say(f"That did not clarify much, but it was very enthusiastic.")


def nudge_toward_misread(world: World, child: Entity, helper: Entity, obj: Entity, sound: SoundEffect) -> None:
    child.memes["bravado"] = child.memes.get("bravado", 0.0) + 1
    world.say(
        f'{child.id} laughed and pointed at {obj.label}. "No, no, I meant the {sound.id} game!"'
    )
    world.say(f'But {helper.id} had already heard "{sound.action}" as "{obj.label}" and grabbed the wrong thing.')


def trigger(world: World, child: Entity, helper: Entity, sound: SoundEffect, obj: Entity) -> None:
    _trigger(world)
    world.say(
        f'{sound.onom} {child.id} made the whole room echo, and then {helper.id} reached for {obj.label}.'
    )
    if obj.id == "bowl":
        world.say("The bowl wobbled like it had its own joke.")
    elif obj.id == "juice":
        world.say("The juice box gave one little gasp.")
    else:
        world.say("Even the plate looked nervous.")


def bad_turn(world: World, adult: Entity, response: Response, obj: Entity) -> None:
    obj.meters["spilled"] = obj.meters.get("spilled", 0.0) + 1
    world.get("adult").memes["alarm"] = world.get("adult").memes.get("alarm", 0.0) + 1
    if response.id == "water":
        world.say(
            f"{adult.label_word.capitalize()} came running and {response.text.replace('{target}', obj.label)}."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} came running and {response.text.replace('{target}', obj.label)}."
        )
    world.say("But the snack was already doing a belly flop onto the floor.")


def ending(world: World, child: Entity, helper: Entity, adult: Entity, obj: Entity, response: Response) -> None:
    world.say("For a second, the room went very quiet.")
    world.say(
        f"Then {adult.label_word.capitalize()} sighed, not angry, just tired, and said, "
        f"'{response.qa_text}.'"
    )
    world.say(
        f"{child.id} tried to {sound_name(world)} again, but only a tiny squeak came out of the spoon."
    )
    world.say(
        f"By the end, the {obj.label} was a sticky puddle, the towel was heroic, and everyone had to eat crackers instead."
    )


def sound_name(world: World) -> str:
    return world.facts["sound"].action


def tell(setting: Setting, sound: SoundEffect, obj: ObjectThing, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Max", helper_gender: str = "boy",
         adult_name: str = "Mom", adult_gender: str = "mother",
         trait: str = "silly") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["confused"]))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult", label="the grown-up"))
    thing = world.add(Entity(id="object", kind="thing", type=obj.id, label=obj.label))
    world.add(Entity(id="setting", kind="thing", type="room", label=setting.place))

    intro(world, child, helper, setting)
    world.para()
    play_sound(world, child, sound)
    clarify_attempt(world, helper, child, sound)
    nudge_toward_misread(world, child, helper, thing, sound)

    world.para()
    trigger(world, child, helper, sound, thing)
    bad_turn(world, adult, response, thing)
    world.say(
        f"{adult.label_word.capitalize()} tried to clarify the story, but by then the snack and the joke were both beyond saving."
    )
    world.say(
        f"The whole room ended in crumbs, laughter, and one very embarrassed spoon."
    )

    world.facts.update(
        child=child, helper=helper, adult=adult, object=thing, setting=setting,
        sound=sound, response=response, outcome="bad", spilled=thing.meters.get("spilled", 0.0) >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny short story for a young child that includes the word "clarify" and the sound {f["sound"].onom}.',
        f"Tell a comedy story where {f['child'].id} makes a noisy game, {f['helper'].id} gets confused, and the ending goes badly.",
        f"Write a playful story with sound effects, a misunderstanding, and a bad ending in which the grown-up tries to clarify too late.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, adult = f["child"], f["helper"], f["adult"]
    obj, sound, resp = f["object"], f["sound"], f["response"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {helper.id}, and {adult.label_word}. They are the people who get tangled up in the noisy misunderstanding."),
        (f"What sound did {child.id} make?",
         f'{child.id} made a {sound.onom} sound. That noise set the whole mix-up in motion because {helper.id} heard it the wrong way.'),
        (f"Why did the problem get worse?",
         f"{helper.id} got confused and grabbed {obj.label}, so the mess got bigger instead of smaller. The adults arrived too late to stop the spill."),
    ]
    qa.append((
        "How did the story end?",
        f"It ended badly and kind of sillily: the snack was ruined, the floor got sticky, and everyone had to switch to crackers. The grown-up tried to clarify things, but not in time to save the snack."
    ))
    if f.get("spilled"):
        qa.append((
            f"What happened after the sound effect?",
            f"The {obj.label} tipped or spilled, and the room turned into a little disaster. That happened because the sound made the helper reach for the wrong thing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["sound"].tags) | set(f["object"].tags) | {"clarify", "help"}
    out: list[tuple[str, str]] = []
    if "clarify" in tags:
        out.append(("What does it mean to clarify something?",
                    "To clarify something means to make it easier to understand. You explain it more clearly so other people stop being confused."))
    if "noise" in tags:
        out.append(("Why can loud noises cause confusion?",
                    "Loud noises can make people look up, jump, or hear the wrong thing. Then they may guess instead of understanding."))
    if "food" in tags:
        out.append(("Why is a spilled snack a bad ending?",
                    "A spilled snack is a bad ending because the food is wasted and the floor gets messy. It can also make everyone stop the game and clean up."))
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
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", sound="squeak", object="bowl", response="clarify",
                child="Mia", child_gender="girl", helper="Max", helper_gender="boy",
                adult="Mom", adult_gender="mother", trait="silly"),
    StoryParams(setting="playroom", sound="drum", object="juice", response="stomp",
                child="Leo", child_gender="boy", helper="Ava", helper_gender="girl",
                adult="Dad", adult_gender="father", trait="goofy"),
    StoryParams(setting="garage", sound="foghorn", object="vase", response="freeze",
                child="Nora", child_gender="girl", helper="Ben", helper_gender="boy",
                adult="Mom", adult_gender="mother", trait="curious"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("loudness", sid, s.loudness))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.breakable:
            lines.append(asp.fact("breakable", oid))
        if o.spillable:
            lines.append(asp.fact("spillable", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SOUND_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O) :- sound(S), object(O), loudness(S,L), L >= 3, (spillable(O); breakable(O)).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
bad_end(S,O,R) :- valid(S,O), sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(set(asp.atoms(model, "sensible")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))

    # Smoke test a normal generate path.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld with sound effects, a bad ending, and clarifying too late.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.response and RESPONSES[args.response].sense < SOUND_MIN:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.sound is None or c[1] == args.sound)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, sound, obj = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(GIRLS if child_gender == "girl" else BOYS)
    helper = args.helper or rng.choice([n for n in (GIRLS if helper_gender == "girl" else BOYS) if n != child])
    adult = args.adult or ("Mom" if adult_gender == "mother" else "Dad")
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, sound=sound, object=obj, response=response,
                       child=child, child_gender=child_gender, helper=helper,
                       helper_gender=helper_gender, adult=adult,
                       adult_gender=adult_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.sound not in SOUNDS or params.object not in OBJECTS or params.response not in RESPONSES:
        raise StoryError("invalid params")
    sound = SOUNDS[params.sound]
    obj = OBJECTS[params.object]
    if not reason_gate(sound, obj):
        raise StoryError(explain_rejection(sound, obj))
    world = tell(SETTINGS[params.setting], sound, obj, RESPONSES[params.response],
                 params.child, params.child_gender, params.helper, params.helper_gender,
                 params.adult, params.adult_gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (sound, object) combos:\n")
        for s, o in combos:
            print(f"  {s:10} {o}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.child} with {p.sound} and {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
