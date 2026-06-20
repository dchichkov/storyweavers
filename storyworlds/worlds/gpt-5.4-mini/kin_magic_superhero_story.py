#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/kin_magic_superhero_story.py
=============================================================

A standalone story world for a small superhero-family magic tale.

Premise:
- A child superhero-in-training wants to use a magic charm for a flashy trick.
- A kin member notices the magic is becoming risky and warns them.
- The child either listens and uses the magic safely, or keeps going and causes a mess that a grown-up fixes.
- The ending proves what changed: safer use of magic, a repaired scene, and a warmer family feeling.

The world is tiny on purpose: a few typed entities, accumulating physical meters
and emotional memes, one causal turn, and a child-facing story that grows from
state instead of from a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "thoughtful", "calm", "wise"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    magical: bool = False
    fragile: bool = False
    sparkly: bool = False
    # meters = physical state, memes = emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class MagicKind:
    id: str
    label: str
    phrase: str
    glow: str
    effect: str
    risk: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Kin:
    id: str
    label: str
    relation: str
    type: str
    gender: str
    age: int
    role: str
    traits: list[str] = field(default_factory=list)
    brave: bool = False
    knows_magic: bool = False
    fragile: bool = False
    magical: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Scene:
    id: str
    label: str
    dark_spot: str
    spark_target: str
    thing: str
    thing_label: str
    recovery: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_glow(world: World) -> list[str]:
    out: list[str] = []
    magic = world.get("magic")
    if magic.meters["glow"] < THRESHOLD:
        return out
    sig = ("glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "room" in world.entities:
        world.get("room").meters["shine"] += 1
    out.append("The room shimmered with bright magic.")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    magic = world.get("magic")
    scene = world.get("scene")
    if magic.meters["glow"] < THRESHOLD:
        return out
    if magic.meters["wild"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scene.meters["scorch"] += 1
    for kid in ("child", "kin"):
        if kid in world.entities:
            world.get(kid).memes["worry"] += 1
    out.append("The magic crackled too hard and made the place too hot.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    scene = world.get("scene")
    if scene.meters["scorch"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "adult" in world.entities:
        world.get("adult").memes["calm"] += 1
    scene.meters["scorch"] = 0.0
    out.append("A grown-up cooled the scene and made everything safe again.")
    return out


CAUSAL_RULES = [
    Rule("glow", "physical", _r_glow),
    Rule("risk", "physical", _r_risk),
    Rule("fix", "social", _r_fix),
]


def magical_risk(magic: MagicKind, scene: Scene) -> bool:
    return magic.id in {"spark", "float", "flash"} and scene.id in {"studio", "roof"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def firepower(response: Response, scene: Scene, delay: int) -> bool:
    return response.power >= (1 + delay if scene.id == "roof" else delay + 1)


def would_listen(kin: Kin, child_age: int) -> bool:
    return kin.brave and kin.age > child_age and "wise" in kin.traits


def tell_magic(world: World, child: Entity, kin: Entity, adult: Entity, scene: Scene,
               magic: MagicKind, response: Response, delay: int) -> None:
    child.memes["joy"] += 1
    kin.memes["care"] += 1
    world.say(
        f"On a bright afternoon, {child.id} and {kin.id} were playing hero games in {scene.label}."
    )
    world.say(
        f"{child.id} found a magic charm that {magic.glow}. It could {magic.effect}, and that felt amazing."
    )
    world.say(
        f"But the {scene.dark_spot} made the trick tempting, because the adventure needed a little more light."
    )
    world.para()
    child.memes["bravery"] += 1
    world.say(
        f'"I can do it myself," said {child.id}, lifting the charm high.'
    )
    world.say(
        f'{kin.id} bit {kin.pronoun("possessive")} lip. "{child.id}, that charm is magic, but it can get too wild near {scene.thing_label}."'
    )
    if would_listen(scene_kin, child.age):
        child.memes["calm"] += 1
        world.say(
            f"{child.id} looked at {kin.id}, thought about {kin.label}, and nodded."
        )
        world.say(
            f'They chose a safer trick instead: {magic.phrase} turned gentle, and the glow lit the room without a fuss.'
        )
        return
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} did not stop. The charm flashed once, then bounced toward {scene.thing_label}."
    )
    world.say(
        f"{scene.thing_label.capitalize()} trembled as the magic got too hot and too bright."
    )
    magic_ent = world.get("magic")
    magic_ent.meters["glow"] += 1
    magic_ent.meters["wild"] += 1
    propagate(world)
    if firepower(response, scene, delay):
        world.say(
            f"{adult.label_word.capitalize()} hurried in and {response.text}."
        )
        world.say(
            f"The scary spark faded, and the room smelled safe again."
        )
        child.memes["relief"] += 1
        kin.memes["relief"] += 1
        world.say(
            f"Afterward, {adult.label_word.capitalize()} hugged them both and said magic was best when it stayed kind."
        )
    else:
        world.say(
            f"{adult.label_word.capitalize()} rushed in, but {response.fail}."
        )
        world.say(
            f"The magic left a smoky mark, and everyone had to step back outside."
        )
        child.memes["fear"] += 1
        kin.memes["fear"] += 1
        world.say(
            f"Still, {adult.label_word.capitalize()} got them safe, and later the family promised to use gentler magic."
        )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for mid, magic in MAGIC.items():
            if magical_risk(magic, scene):
                combos.append((sid, mid, "in_family"))
    return combos


@dataclass
@dataclass
class StoryParams:
    scene: str
    magic: str
    response: str
    child_name: str
    child_gender: str
    kin_name: str
    kin_gender: str
    adult_gender: str
    child_age: int = 6
    kin_age: int = 9
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


GIRL_NAMES = ["Maya", "Lena", "Iris", "Zoe", "Nina", "Ava", "Mila"]
BOY_NAMES = ["Leo", "Noah", "Finn", "Theo", "Eli", "Max", "Owen"]
TRAITS = ["careful", "wise", "calm", "clever"]
SCENE_KINDS = {
    "studio": Scene("studio", "the art studio", "the back shelf", "a crystal lamp", "a glass sculpture", "glimmering ribbons", tags={"glass", "light"}),
    "roof": Scene("roof", "the rooftop garden", "the dark corner", "a lantern", "a wind toy", "fresh moss", tags={"wind", "height"}),
    "basement": Scene("basement", "the basement fort", "the shadowy box pile", "a string of paper stars", "a stack of old comics", "a cardboard castle", tags={"dark", "paper"}),
}
MAGIC = {
    "spark": MagicKind("spark", "spark magic", "spark magic", "glowed like a tiny star", "make bright dancing lights", "tip into a hot spark", tags={"spark", "light"}),
    "float": MagicKind("float", "float magic", "float magic", "bobbled like a bubble", "lift small things into the air", "brush too close and wobble wildly", tags={"float", "lift"}),
    "flash": MagicKind("flash", "flash magic", "flash magic", "flared like a camera", "make a quick hero flash", "turn into a dazzling burst", tags={"flash", "light"}),
}
RESPONSES = {
    "shield": Response("shield", 3, 3, "raised a calm shield and gently pushed the magic away", "tried to raise a shield, but the burst was already too wild", "raised a calm shield and pushed the magic away", tags={"shield"}),
    "cloak": Response("cloak", 2, 2, "threw a heavy cloak over the spark and smothered the glare", "threw a cloak over it, but the glow was too big to stop", "threw a cloak over it and smothered the glare", tags={"cloak"}),
    "window": Response("window", 3, 4, "opened the windows and let the extra magic drift out into the air", "opened the windows, but the air was still too hot and bright", "opened the windows and let the extra magic drift away", tags={"window"}),
}
SCENES = SCENE_KINDS


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: kin, magic, and superhero courage.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--kin-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--kin-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man"])
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
    combos = [c for c in valid_combos()
              if args.scene is None or c[0] == args.scene
              if args.magic is None or c[1] == args.magic]
    if args.scene and args.magic and (args.scene, args.magic, "in_family") not in combos:
        raise StoryError("No valid magic scene matches the chosen options.")
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    scene, magic, _ = rng.choice(combos)
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    kin_gender = args.kin_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    kin_name = args.kin_name or rng.choice([n for n in (GIRL_NAMES if kin_gender == "girl" else BOY_NAMES) if n != child_name])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    return StoryParams(scene, magic, response, child_name, child_gender, kin_name, kin_gender, adult_gender, delay=rng.randint(0, 1))


def generate(params: StoryParams) -> StorySample:
    scene = SCENE_KINDS[params.scene]
    magic = MAGIC[params.magic]
    response = RESPONSES[params.response]
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", age=params.child_age, traits=["heroic"]))
    kin = world.add(Entity(id=params.kin_name, kind="character", type=params.kin_gender, role="kin", age=params.kin_age, traits=["wise", "kind"]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult_gender, role="adult", label="the grown-up"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="magic", type="thing", label=magic.label, magical=True, sparkly=True))
    world.add(Entity(id="scene", type="thing", label=scene.label, fragile=True))
    if params.scene == "roof":
        scene_kin = kin
    else:
        scene_kin = kin
    world.facts["scene_kin"] = scene_kin
    world.say(f"{child.id} and {kin.id} were kin, which meant they knew each other's smiles and secret hero names.")
    world.say(f"They were in {scene.label}, where the air felt ready for a superhero game.")
    world.say(f"{child.id} loved {magic.phrase} because it {magic.glow}.")
    world.para()
    tell_magic(world, child, kin, adult, scene, magic, response, params.delay)
    world.facts.update(child=child, kin=kin, adult=adult, scene=scene, magic=magic, response=response)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero-style story for a small child that includes the word "kin" and uses magic in a family adventure.',
        f"Tell a story where {f['child'].id} wants to use {f['magic'].label} but {f['kin'].id} warns them, and a grown-up helps if needed.",
        f"Write a gentle magic story with kin, a risky sparkling trick, and an ending that shows the family is safe and closer together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, kin, adult, scene, magic, response = f["child"], f["kin"], f["adult"], f["scene"], f["magic"], f["response"]
    return [
        ("Who are the story about?", f"It is about {child.id} and {kin.id}, who are kin and like playing superhero games together. {adult.label_word.capitalize()} helps keep the magic safe."),
        ("What did the child want to do?", f"{child.id} wanted to use {magic.label} for a flashy hero trick. The child wanted the trick to feel big and exciting."),
        ("Why did the kin warn them?", f"{kin.id} warned them because the magic could get too wild near {scene.thing_label}. That warning mattered because the risky sparkle could make the scene unsafe."),
    ] + (
        [("How was the problem fixed?", f"{adult.label_word.capitalize()} used {response.qa_text} so the magic settled down. After that, the room felt safe again and the family stayed together.")]
        if world.get("scene").meters["scorch"] < THRESHOLD else
        [("How did the grown-up help?", f"{adult.label_word.capitalize()} came in quickly and used {response.qa_text}, but the magic had already left a smoky mark. The family still got to safety and then cleaned up together.")]
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["magic"].tags) | set(world.facts["scene"].tags) | set(world.facts["response"].tags)
    qas = {
        "spark": [("What is spark magic?", "Spark magic makes tiny bright lights like a star. It looks exciting, but it should be used carefully.")],
        "float": [("What is float magic?", "Float magic can lift little things into the air. It works best when someone keeps it gentle and controlled.")],
        "flash": [("What is flash magic?", "Flash magic makes a quick burst of light. It can be useful, but too much flash can be overwhelming.")],
        "glass": [("Why must magic stay away from glass?", "Glass can break if something gets bumped or hit too hard. Magic should stay gentle around fragile things.")],
        "light": [("Why should bright magic be used carefully?", "Bright magic can surprise people and make a room too hot or too dazzling. Careful hands keep it safe.")],
        "shield": [("What does a shield do?", "A shield helps block danger and keep someone safe. Heroes use shields when they need protection.")],
        "cloak": [("What does a cloak do in a story?", "A cloak can cover and quiet something. In stories, it can hide a spark or keep something warm.")],
        "window": [("Why open a window?", "Opening a window can let fresh air in and move smoke or hot air out. That helps a room feel safer.")],
    }
    order = ["spark", "float", "flash", "light", "glass", "shield", "cloak", "window"]
    out = []
    for key in order:
        if key in tags and key in qas:
            out.extend(qas[key])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.magical:
            bits.append("magical")
        if e.fragile:
            bits.append("fragile")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("studio", "spark", "shield", "Maya", "girl", "Leo", "boy", "woman", delay=0),
    StoryParams("basement", "flash", "cloak", "Noah", "boy", "Ava", "girl", "man", delay=0),
    StoryParams("roof", "float", "window", "Iris", "girl", "Finn", "boy", "woman", delay=1),
]


ASP_RULES = r"""
magic_risk(S, M) :- scene(S), magic(M), risky_magic(M), risky_scene(S).
sensible(R) :- response(R), sense(R, N), N >= 2.
outcome(safe) :- not wild.
outcome(scary) :- wild.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for mid in MAGIC:
        lines.append(asp.fact("magic", mid))
        if mid in {"spark", "float", "flash"}:
            lines.append(asp.fact("risky_magic", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    return 0 if set(asp_sensible()) == {r.id for r in sensible_responses()} and _smoke() else 1


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def _smoke() -> bool:
    try:
        generate(CURATED[0])
        return True
    except Exception:
        return False


def build_story_for_params(params: StoryParams) -> StorySample:
    return generate(params)


def resolve_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    params.seed = args.seed
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show magic_risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name} and {p.kin_name}: {p.scene} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.magic is None or c[1] == args.magic)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    scene, magic, _ = rng.choice(combos)
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    kin_gender = args.kin_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    kin_pool = GIRL_NAMES if kin_gender == "girl" else BOY_NAMES
    kin_name = args.kin_name or rng.choice([n for n in kin_pool if n != child_name])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    return StoryParams(scene, magic, response, child_name, child_gender, kin_name, kin_gender, adult_gender, delay=rng.randint(0, 1))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for mid, magic in MAGIC.items():
            if magical_risk(magic, scene):
                combos.append((sid, mid, "in_family"))
    return combos


def generate(params: StoryParams) -> StorySample:
    scene = SCENE_KINDS[params.scene]
    magic = MAGIC[params.magic]
    response = RESPONSES[params.response]
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child", age=params.child_age))
    kin = world.add(Entity(id=params.kin_name, kind="character", type=params.kin_gender, role="kin", age=params.kin_age, traits=["wise", "kind"]))
    adult = world.add(Entity(id="Adult", kind="character", type=params.adult_gender, role="adult", label="the grown-up"))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(id="magic", type="thing", label=magic.label, magical=True, sparkly=True))
    world.add(Entity(id="scene", type="thing", label=scene.label, fragile=True))
    child.memes["bravery"] = BRAVERY_INIT
    kin.memes["care"] = 1.0
    world.say(f"{child.id} and {kin.id} were kin, and they liked playing superhero games together.")
    world.say(f"In {scene.label}, {child.id} found {magic.phrase} that {magic.glow}.")
    world.para()
    child.memes["joy"] += 1
    world.say(f"{child.id} wanted to use it for a big hero trick.")
    world.say(f"{kin.id} warned that the magic could get too wild near {scene.thing_label}.")
    if would_listen(kin, child.age):
        world.say(f"{child.id} listened, and together they made the magic gentle and bright.")
        world.say(f"That safe glow lit the scene like a tiny star, and the family cheered.")
        outcome = "safe"
    else:
        child.memes["defiance"] += 1
        magic_ent = world.get("magic")
        magic_ent.meters["glow"] += 1
        magic_ent.meters["wild"] += 1
        scene_ent = world.get("scene")
        scene_ent.meters["scorch"] += 1
        world.say(f"{child.id} kept going, and the magic burst too hard.")
        world.say(f"The bright flash made {scene.thing_label} tremble.")
        propagate(world)
        if firepower(response, scene, params.delay):
            world.say(f"{adult.label_word.capitalize()} hurried in and {response.text}.")
            world.say("The danger faded, and the family breathed out together.")
            outcome = "contained"
        else:
            world.say(f"{adult.label_word.capitalize()} rushed in, but {response.fail}.")
            world.say("The magic left a smoky mark, so everyone stepped back and stayed safe.")
            outcome = "scary"
    world.facts.update(child=child, kin=kin, adult=adult, scene=scene, magic=magic, response=response, outcome=outcome)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


if __name__ == "__main__":
    main()
