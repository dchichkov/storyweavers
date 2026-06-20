#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toe_pl_repetition_cautionary_sound_effects_bedtime.py
=====================================================================================

A small bedtime storyworld built from the seed words "toe-pl" with repetition,
cautionary beats, and gentle sound effects.

Core premise:
- A sleepy child wants one more tiny bedtime adventure with a noisy toy called
  Toe-Pl.
- A cautious grown-up warns that Toe-Pl can be loud after lights-out.
- The child almost makes a mess of bedtime, then listens, calms down, and picks
  a softer ritual instead.
- The story uses repeated phrases, onomatopoeia, and a cozy ending image that
  proves the mood changed.

This script follows the storyworld contract:
- stdlib only
- eager import of storyworlds.results for QAItem, StoryError, StorySample
- lazy import of storyworlds.asp inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, --show-asp
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

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_noise(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    toy = world.entities.get("toy")
    room = world.entities.get("room")
    if not child or not toy or not room:
        return out
    if toy.meters["noisy"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["awake"] += 1
    child.memes["wideawake"] += 1
    out.append("__sound__")
    return out


CAUSAL_RULES = [Rule("noise", "social", _r_noise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


@dataclass
class Bedroom:
    id: str
    title: str
    blanket: str
    lamp: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Toy:
    id: str
    label: str
    sound: str
    bedtime_risky: bool = True
    makes_noise: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Comfort:
    id: str
    label: str
    phrase: str
    glow: str
    quiet: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


ROOMS = {
    "nursery": Bedroom("nursery", "a cozy nursery", "a striped blanket", "a little lamp"),
    "room": Bedroom("room", "a small bedroom", "a moon blanket", "a bedtime lamp"),
}

TOYS = {
    "toe_pl": Toy("toe_pl", "toe-pl", "toe-pl", tags={"toe-pl", "toy", "noise"}),
    "drum": Toy("drum", "tiny drum", "drum", tags={"drum", "noise"}),
    "rattle": Toy("rattle", "baby rattle", "rattle", tags={"rattle", "noise"}),
}

COMFORTS = {
    "book": Comfort("book", "picture book", "a picture book", "glowed softly", tags={"book", "quiet"}),
    "lamp": Comfort("lamp", "night-light", "a night-light", "glowed like a tiny moon", tags={"lamp", "quiet"}),
    "song": Comfort("song", "lullaby", "a lullaby", "hummed softly", tags={"song", "quiet"}),
}

RESPONSES = {
    "put_away": Response("put_away", 3, "put Toe-Pl back on the shelf and closed the toy box", "put Toe-Pl back on the shelf", tags={"quiet"}),
    "hush": Response("hush", 3, "covered Toe-Pl with the blanket and whispered a hush-hush goodnight", "covered Toe-Pl with the blanket", tags={"quiet"}),
    "battery_out": Response("battery_out", 2, "took out the tiny batteries so Toe-Pl could only rest and not beep", "took out the batteries", tags={"quiet"}),
    "wait": Response("wait", 1, "waited and hoped the noise would stop on its own", "waited and hoped", tags={"weak"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Zoe", "Maya"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Finn", "Noah", "Eli"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for toy in TOYS:
            for comfort in COMFORTS:
                if TOYS[toy].bedtime_risky and TOYS[toy].makes_noise:
                    combos.append((room, toy, comfort))
    return combos


def sound_at_risk(toy: Toy) -> bool:
    return toy.bedtime_risky and toy.makes_noise


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def reasonableness_check(toy: Toy, comfort: Comfort) -> bool:
    return sound_at_risk(toy) and comfort.quiet


def predict_noise(world: World, toy_id: str) -> dict:
    sim = world.copy()
    sim.get(toy_id).meters["noisy"] += 1
    propagate(sim, narrate=False)
    return {"awake": sim.get("room").meters["awake"], "wideawake": sim.get("child").memes["wideawake"]}


def introduce(world: World, child: Entity, room: Bedroom) -> None:
    world.say(
        f"At bedtime, {child.id} snuggled under {room.blanket} in {room.title}. "
        f"The {room.lamp} made the room feel soft and still."
    )
    world.say(
        f'{child.id} liked the quiet best. Still, {child.pronoun()} kept toe-pl '
        f"near the bed, just in case there was time for one more tiny game."
    )


def tempt(world: World, child: Entity, toy: Toy) -> None:
    child.memes["curious"] += 1
    world.say(
        f'The little toy went "tap-tap, tippity-tap." Toe-Pl! Toe-Pl! Toe-Pl!'
    )
    world.say(
        f'{child.id} whispered, "Just one little toe-pl. Just one little toe-pl."'
    )


def warn(world: World, grownup: Entity, child: Entity, toy: Toy) -> None:
    pred = predict_noise(world, "toy")
    grownup.memes["care"] += 1
    world.facts["predicted_awake"] = pred["awake"]
    world.say(
        f'"Toe-Pl is for daytime," {grownup.id} said softly. '
        f'"Toe-Pl can wake the room if it goes tap-tap after lights-out."'
    )


def defy(world: World, child: Entity, toy: Toy) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} grinned and gave Toe-Pl one more little tap. '
        f'"Just one little toe-pl," {child.id} said again.'
    )


def make_noise(world: World, toy: Toy) -> None:
    toy_ent = world.get("toy")
    toy_ent.meters["noisy"] += 1
    propagate(world, narrate=False)
    world.say(
        'Toe-Pl answered with a bright "BIP-BIP-BAP!" and a squeaky '
        '"toe-pl, toe-pl, toe-pl!"'
    )


def alarm(world: World, grownup: Entity, child: Entity) -> None:
    world.say(
        f"{grownup.id} opened {grownup.pronoun('possessive')} eyes at once. "
        f'"Too loud for bedtime," {grownup.id} said, but {grownup.pronoun()} stayed kind.'
    )


def calm_fix(world: World, grownup: Entity, child: Entity, response: Response,
             comfort: Comfort) -> None:
    world.get("toy").meters["noisy"] = 0.0
    world.get("room").meters["awake"] = 0.0
    world.say(
        f"Then {grownup.id} calmly {response.text}. "
        f"{comfort.phrase.capitalize()} {comfort.glow} on the pillow."
    )


def lesson(world: World, grownup: Entity, child: Entity, toy: Toy, comfort: Comfort) -> None:
    child.memes["relief"] += 1
    child.memes["sleepy"] += 1
    world.say(
        f'{grownup.id} tucked the blanket higher and said, "Night time likes soft sounds." '
        f'"Soft sounds, soft sounds," {child.id} repeated, and the words felt sleepy.'
    )
    world.say(
        f'{child.id} gave Toe-Pl a last pat and set it by the {comfort.label}. '
        f'The room grew quieter and quieter.'
    )


def ending(world: World, child: Entity, comfort: Comfort) -> None:
    world.say(
        f'At last {child.id} closed {child.pronoun("possessive")} eyes. '
        f'Toe-Pl stayed still, the {comfort.label} glowed, and the room breathed hush-hush hush.'
    )


def tell(room: Bedroom, toy: Toy, comfort: Comfort,
         child_name: str = "Mina", child_gender: str = "girl",
         grownup_name: str = "Mom", grownup_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity("child", "character", child_gender, traits=["sleepy"], role="child"))
    child.id = child_name
    grownup = world.add(Entity("grownup", "character", grownup_gender, role="grownup"))
    grownup.id = grownup_name
    toy_ent = world.add(Entity("toy", "thing", "toy", label=toy.label))
    toy_ent.meters["noisy"] = 1.0
    room_ent = world.add(Entity("room", "thing", "room", label=room.title))
    world.facts.update(room=room, toy=toy, comfort=comfort)

    introduce(world, child, room)
    world.para()
    tempt(world, child, toy)
    warn(world, grownup, child, toy)
    defy(world, child, toy)
    make_noise(world, toy)
    alarm(world, grownup, child)
    world.para()
    response = best_response()
    calm_fix(world, grownup, child, response, comfort)
    lesson(world, grownup, child, toy, comfort)
    world.para()
    ending(world, child, comfort)

    world.facts.update(child=child, grownup=grownup, response=response)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a bedtime story for a young child that repeats the words "toe-pl" and ends very softly.',
        f"Tell a cautionary bedtime story where {f['child'].id} wants to play with Toe-Pl after lights-out, but {f['grownup'].id} helps {f['child'].pronoun('object')} choose a quieter ritual.",
        'Write a gentle story with repeated sound effects like "tap-tap" and "hush-hush" that teaches bedtime is for soft sounds.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, grownup, response = f["child"], f["grownup"], f["response"]
    return [
        ("What did the child want to do at bedtime?",
         f"{child.id} wanted one more little game with Toe-Pl, even though it was already bedtime. The toy made the room feel too awake."),
        ("Why did the grown-up warn the child?",
         f"{grownup.id} warned that Toe-Pl could wake the room if it went tap-tap after lights-out. That was a gentle bedtime caution, not a scolding."),
        ("How did the problem get fixed?",
         f"{grownup.id} {response.qa_text} and then chose a quiet comfort instead. That made the room calm again so sleep could come back."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("Why are bedtime stories often soft and slow?",
         "Bedtime stories are often soft and slow because quiet words help children relax and get ready for sleep."),
        ("What kind of sound is good at bedtime?",
         "Soft sounds are best at bedtime. Gentle words, whispers, and quiet little noises help the room stay calm."),
        ("Why can a loud toy be a problem at night?",
         "A loud toy can make it harder to fall asleep because noise wakes the room up and keeps everyone alert."),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)




def explain_rejection(toy: Toy, comfort: Comfort) -> str:
    if not reasonableness_check(toy, comfort):
        return f"(No story: {toy.label} is not a good bedtime problem for that quiet ending.)"
    return "(No story: this combination is not available.)"


def outcome_of(_: StoryParams) -> str:
    return "calmed"


@dataclass
class StoryParams:
    room: str
    toy: str
    comfort: str
    child_name: str
    child_gender: str
    grownup_name: str
    grownup_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

CURATED = [
    ("nursery", "toe_pl", "book", "Mina", "girl", "Mom", "mother"),
    ("room", "drum", "lamp", "Theo", "boy", "Dad", "father"),
    ("nursery", "rattle", "song", "Nora", "girl", "Mom", "mother"),
]



def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for tid, t in TOYS.items():
        lines.append(asp.fact("toy", tid))
        if t.bedtime_risky:
            lines.append(asp.fact("bedtime_risky", tid))
        if t.makes_noise:
            lines.append(asp.fact("makes_noise", tid))
    for cid, c in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        if c.quiet:
            lines.append(asp.fact("quiet", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,T,C) :- room(R), toy(T), comfort(C), bedtime_risky(T), makes_noise(T), quiet(C).
sensible(R) :- response(R), sense(R,S), S >= 2.
outcome(calmed) :- sensible(_).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        print("MISMATCH in sensible responses")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, toy=None, comfort=None, child_name=None, child_gender=None, grownup_name=None, grownup_gender=None), random.Random(7)))
        _ = sample.story
        _ = format_qa(sample)
    except Exception:
        traceback.print_exc()
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld with toe-pl, repetition, caution, and soft sound effects.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup-name")
    ap.add_argument("--grownup-gender", choices=["mother", "father"])
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
    room = args.room or rng.choice(list(ROOMS))
    toy = args.toy or rng.choice(list(TOYS))
    comfort = args.comfort or rng.choice(list(COMFORTS))
    if args.toy and args.comfort and not reasonableness_check(TOYS[toy], COMFORTS[comfort]):
        raise StoryError(explain_rejection(TOYS[toy], COMFORTS[comfort]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father"])
    grownup_name = args.grownup_name or ("Mom" if grownup_gender == "mother" else "Dad")
    return StoryParams(room, toy, comfort, child_name, child_gender, grownup_name, grownup_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], TOYS[params.toy], COMFORTS[params.comfort],
                 params.child_name, params.child_gender,
                 params.grownup_name, params.grownup_gender)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        print()
        for r, t, c in asp_valid_combos():
            print(r, t, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for room, toy, comfort, cn, cg, gn, gg in CURATED:
            samples.append(generate(StoryParams(room, toy, comfort, cn, cg, gn, gg)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        hdr = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
