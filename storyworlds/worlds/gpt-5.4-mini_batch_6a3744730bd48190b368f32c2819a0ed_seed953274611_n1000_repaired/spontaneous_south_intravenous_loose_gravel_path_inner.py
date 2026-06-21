#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spontaneous_south_intravenous_loose_gravel_path_inner.py
========================================================================================

A small standalone storyworld about a strange night on a loose gravel path.

Premise:
- A child on a loose gravel path hears a whispery ghost-like feeling.
- An old nurse bag, a bottle of medicine, and a bright lantern become relevant.
- The child has an inner monologue that doubts, notices, and then chooses help.
- The story must naturally include the words spontaneous, south, and intravenous.
- The tone is close to a ghost story, but child-facing and safe.

The world model tracks physical meters and emotional memes so the prose is driven
by state rather than a frozen paragraph.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
        return self.label or self.id
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
    mood: str
    south_hint: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    is_real: bool = True
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
class Light:
    id: str
    label: str
    phrase: str
    glow: str
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
class Medicine:
    id: str
    label: str
    phrase: str
    route: str
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
class StoryParams:
    setting: str
    hazard: str
    light: str
    medicine: str
    response: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    seed: Optional[int] = None
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid, h in HAZARDS.items():
            if not h.is_real:
                continue
            for rid in RESPONSES:
                if RESPONSES[rid].sense >= SENSE_MIN:
                    combos.append((sid, hid, rid))
    return combos


def hazard_is_real(h: Hazard) -> bool:
    return h.is_real


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(delay: int) -> int:
    return 1 + delay


def contained(resp: Response, delay: int) -> bool:
    return resp.power >= severity(delay)


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS or params.hazard not in HAZARDS or params.light not in LIGHTS or params.medicine not in MEDS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters for this storyworld.")
    setting = SETTINGS[params.setting]
    hazard = HAZARDS[params.hazard]
    light = LIGHTS[params.light]
    med = MEDS[params.medicine]
    resp = RESPONSES[params.response]
    if not hazard_is_real(hazard):
        raise StoryError("This hazard is too imaginary to drive a ghost story.")
    if resp.sense < SENSE_MIN:
        raise StoryError("That response is too weak or unwise for this story.")

    w = World(setting)
    child = w.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    adult = w.add(Entity(id=params.adult_name, kind="character", type=params.adult_gender, role="adult"))
    path = w.add(Entity(id="path", type="place", label=setting.place, tags={"path"}))
    lantern = w.add(Entity(id="lantern", type="thing", label=light.label, tags=light.tags))
    bag = w.add(Entity(id="bag", type="thing", label=med.label, tags=med.tags))
    phantom = w.add(Entity(id="phantom", type="thing", label=hazard.label, tags=hazard.tags))

    child.memes["unease"] = 1
    child.memes["curiosity"] = 1
    adult.memes["calm"] = 1

    w.say(
        f"{child.id} walked along the loose gravel path, where the stones clicked underfoot like tiny teeth. "
        f"The air felt {setting.mood}, and the path pointed {setting.south_hint}."
    )
    w.say(
        f"In the dark, {child.id} noticed {hazard.phrase} by a crooked fence. "
        f"It seemed to rise out of the night, all at once, almost spontaneous."
    )
    w.say(
        f'Inside {child.id}\'s head, a small inner voice whispered, "Do not be silly. '
        f'Ghosts do not need {med.label}; people do."'
    )

    w.para()
    child.memes["fear"] = 1
    w.say(
        f"Still, the sight of the {hazard.label} made {child.id}'s chest feel tight. "
        f'The inner voice went on: "Why is it so quiet? Why does the dark look deeper here?"'
    )
    w.say(
        f"Then {adult.id} lifted {light.phrase} and the path changed shape at once. "
        f"{light.glow.capitalize()}, and the gravel no longer looked like hiding places."
    )

    if params.delay > 0:
        child.memes["fear"] += 1

    w.para()
    if contained(resp, params.delay):
        w.say(
            f'{child.id} blurted out, "I think I scared myself." {adult.id} knelt beside {child.id} and said, '
            f'"Good. You told me. Now we can fix this the sensible way."'
        )
        body = resp.text.replace("{target}", hazard.label)
        w.say(f"{adult.id} {body}.")
        w.say(
            f"The spooky shape was only a coat hanging from a fence post, and the night became ordinary again. "
            f"{child.id} looked down at the stones and felt brave enough to keep walking."
        )
    else:
        w.say(
            f'{child.id} tried to be brave, but the worry kept growing. "I should have called sooner," '
            f"{child.id} thought, hearing the stones shuffle like footsteps."
        )
        body = resp.fail.replace("{target}", hazard.label)
        w.say(f"{adult.id} {body}.")
        w.say(
            f"The night stayed scary for a little while, but {adult.id} kept {child.id} close and led "
            f"{child.id} away from the fence and toward the house lights."
        )

    w.para()
    w.say(
        f"At the end, the loose gravel path looked smaller and friendlier. "
        f"{child.id} still remembered the ghost-story feeling, but now it had a answer: a lantern, a steady hand, "
        f"and a calm word spoken before the dark could win."
    )

    w.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        hazard=hazard,
        light=light,
        medicine=med,
        response=resp,
        outcome="contained" if contained(resp, params.delay) else "unclear",
        delay=params.delay,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story style story for a young child on a loose gravel path that includes the words '
        f'"spontaneous", "south", and "intravenous".',
        f'Tell a child-facing inner-monologue story where {f["child"].id} is walking south on a loose gravel path, '
        f'feels a ghostly fright, and then gets help from {f["adult"].id}.',
        f'Write a spooky-but-safe story with an inner voice, a lantern, and a calm grown-up who keeps the fear from growing.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    haz = f["hazard"]
    med = f["medicine"]
    resp = f["response"]
    out = f["outcome"]
    qa = [
        (
            "What made the child feel frightened?",
            f"The child saw {haz.phrase} on the loose gravel path and thought it might be a ghost. "
            f"The dark and the stillness made the feeling grow in {child.pronoun('possessive')} head."
        ),
        (
            f"What was {child.id}'s inner monologue saying?",
            f"It was saying the child should not panic and should notice what was really there. "
            f"The little voice kept asking questions instead of letting the fear run wild."
        ),
        (
            "How did the grown-up help?",
            f"{adult.id} brought a lantern, stayed calm, and used {resp.text.replace('{target}', haz['label'])}. "
            f"That turned the scary shape into something ordinary and safe."
        ),
    ]
    if out == "contained":
        qa.append(
            (
                "What changed by the end?",
                f"The path felt less like a ghost story and more like a safe walk home. "
                f"The child learned that calm help can make a dark place feel smaller."
            )
        )
    else:
        qa.append(
            (
                "What happened when help came too late?",
                f"The fear kept hovering until the grown-up led the child away. "
                f"Even then, staying together kept the night from becoming worse."
            )
        )
    qa.append(
        (
            f"Why did the story mention {med.label}?",
            f"It was part of the strange thought that made the child's inner voice sound worried. "
            f"The word helped give the story its eerie, ghost-like mood."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a loose gravel path?",
            "It is a path covered with small stones that crunch and shift under your shoes. "
            "Because the stones move, the path can feel noisy and a little spooky at night."
        ),
        (
            "What does spontaneous mean?",
            "Spontaneous means something happens suddenly, without much planning. "
            "In a story, it can make a moment feel surprising."
        ),
        (
            "What does south mean?",
            "South is one direction on a map or compass. "
            "It helps people know which way they are going."
        ),
        (
            "What does intravenous mean?",
            "Intravenous means medicine or fluid goes into a vein, usually with help from a trained grown-up. "
            "It is a medical word, not a toy word."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "loose_gravel_path": Setting(id="loose_gravel_path", place="loose gravel path", mood="cold and watchful", south_hint="south"),
    "graveyard_path": Setting(id="graveyard_path", place="loose gravel path by the old gate", mood="thin and moon-cold", south_hint="south"),
}

HAZARDS = {
    "shadow_coat": Hazard(id="shadow_coat", label="shadow coat", phrase="a long black shape", is_real=True, tags={"ghost", "coat"}),
    "lamp_post": Hazard(id="lamp_post", label="lamp post", phrase="the crooked lamp post", is_real=False, tags={"lamp"}),
}

LIGHTS = {
    "lantern": Light(id="lantern", label="lantern", phrase="a little lantern", glow="the lantern glowed steady as a candle behind glass", tags={"light"}),
    "flashlight": Light(id="flashlight", label="flashlight", phrase="a small flashlight", glow="the flashlight made a bright white path", tags={"light"}),
}

MEDS = {
    "intravenous_bag": Medicine(id="intravenous_bag", label="intravenous bag", phrase="a hospital intravenous bag", route="intravenous", tags={"intravenous", "medicine"}),
    "medicine_box": Medicine(id="medicine_box", label="medicine box", phrase="a medicine box", route="oral", tags={"medicine"}),
}

RESPONSES = {
    "steady_lantern": Response(id="steady_lantern", sense=3, power=2, text="lifted the lantern and held it steady until the shadows stopped shaking", fail="lifted the lantern, but the dark still felt bigger than the light", tags={"light"}),
    "call_help": Response(id="call_help", sense=4, power=3, text="called a nurse and a neighbor, and together they checked the path and the fence", fail="called for help, but the night had already turned everyone nervous", tags={"help"}),
    "walk_home": Response(id="walk_home", sense=2, power=2, text="took the child home by the hand and shut the door on the spooky shapes", fail="tried to hurry home, but the fear kept trailing behind them", tags={"home"}),
}

SENSE_MIN = 2

CURATED = [
    StoryParams(setting="loose_gravel_path", hazard="shadow_coat", light="lantern", medicine="intravenous_bag", response="steady_lantern", child_name="Mina", child_gender="girl", adult_name="Nurse June", adult_gender="woman", delay=0),
    StoryParams(setting="graveyard_path", hazard="shadow_coat", light="flashlight", medicine="intravenous_bag", response="call_help", child_name="Eli", child_gender="boy", adult_name="Mr. Vale", adult_gender="man", delay=1),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.hazard in HAZARDS and params.light in LIGHTS and params.medicine in MEDS and params.response in RESPONSES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story style inner-monologue storyworld on a loose gravel path.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--medicine", choices=MEDS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-name")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    light = args.light or rng.choice(list(LIGHTS))
    medicine = args.medicine or rng.choice(list(MEDS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    if HAZARDS[hazard].is_real is False:
        raise StoryError("That hazard is too unreal to build a ghost story around.")
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError("That response is too weak for this story.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mina", "Eli", "Nora", "Sam", "Ivy", "Theo"])
    adult_name = args.adult_name or rng.choice(["Nurse June", "Mr. Vale", "Aunt Ada", "Uncle Wes"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting=setting, hazard=hazard, light=light, medicine=medicine, response=response, child_name=child_name, child_gender=child_gender, adult_name=adult_name, adult_gender=adult_gender, delay=delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        if h.is_real:
            lines.append(asp.fact("real", hid))
    for lid in LIGHTS:
        lines.append(asp.fact("light", lid))
    for mid in MEDS:
        lines.append(asp.fact("medicine", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,H,R) :- setting(S), real(H), response(R), sensible(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        ok = False
        print("MISMATCH: ASP sensible responses differ from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    try:
        # default-style random generation, exercising resolve_params and tell
        args = build_parser().parse_args([])
        p = resolve_params(args, random.Random(777))
        _ = generate(p)
    except Exception as exc:
        ok = False
        print(f"DEFAULT SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke tests passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.child_name} on {p.setting} ({p.response})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
