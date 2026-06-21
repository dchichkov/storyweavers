#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/styrofoam_pasture_cautionary_transformation_adventure.py
=======================================================================================

A standalone story world for a small adventure tale about a child, a fragile
styrofoam float, a wide pasture, a cautionary warning, and a transformation
from a bad plan into a safer one.

The world keeps two kinds of state:
- meters: physical quantities like drifting, soggy, cracked, trampled
- memes: feelings like worry, courage, relief, pride

The premise is simple: two friends want an adventure across a pasture. One child
wants to use a styrofoam thing as a bridge or boat for the game. The other child
foresees the trouble, warns them, and the story turns toward a careful
transformation: the fragile prop becomes something else, and the adventure
continues safely.

Words from the seed are guaranteed to appear:
- styrofoam
- pasture

Features:
- Cautionary: the story includes a clear warning about a risky choice.
- Transformation: the unsafe object or plan changes into a safer use.

Style:
- Adventure tone, child-facing, concrete, state-driven, complete story.
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
SENSE_MIN = 2


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
    fragile: bool = False
    floats: bool = False
    safe_use: str = ""

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
class Theme:
    id: str
    scene: str
    rig: str
    hero_title: str
    friend_title: str
    goal: str
    wild_word: str
    safe_word: str
    send_off: str
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
    unsafe_use: str
    warns: str
    break_word: str
    makes_risk: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Transform:
    id: str
    from_use: str
    to_use: str
    text: str
    result: str
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
    theme: str
    hazard: str
    transform: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    delay: int = 0
    hero_age: int = 6
    friend_age: int = 5
    relation: str = "friends"
    trust: int = 5
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
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


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["risk"] < THRESHOLD:
            continue
        sig = ("trouble", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("__risk__")
    return out


CAUSAL_RULES = [Rule("trouble", _r_trouble)]


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


def risk_at_play(hazard: Hazard, theme: Theme) -> bool:
    return hazard.makes_risk and "pasture" in theme.wild_word.lower()


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def risk_severity(delay: int) -> int:
    return 1 + delay


def is_safe(response: Response, delay: int) -> bool:
    return response.power >= risk_severity(delay)


def predict_risk(world: World, hazard_id: str) -> dict:
    sim = world.copy()
    _do_risky(sim, sim.get(hazard_id), narrate=False)
    return {
        "risky": sim.get(hazard_id).meters["risk"] >= THRESHOLD,
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_risky(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["risk"] += 1
    target.meters["bent"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, theme: Theme) -> None:
    hero.memes["courage"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"One bright morning, {hero.id} and {friend.id} set out toward {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.hero_title} {hero.id} and {theme.friend_title} {friend.id}," '
        f'{hero.id} said, "let\'s reach {theme.goal}!"'
    )


def need_course(world: World, friend: Entity, theme: Theme) -> None:
    world.say(
        f"But the way ahead crossed a wide {theme.wild_word}, and the wind made it feel bigger than it looked."
    )
    world.say(f'"We need a way across," {friend.id} said quietly.')


def tempt(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["bold"] += 1
    world.say(
        f'{hero.id} grinned. "I know! {hazard.phrase} {hazard.unsafe_use}."'
    )
    world.say("For a moment, the idea sounded like a shortcut to adventure.")


def warn(world: World, friend: Entity, hero: Entity, hazard: Hazard) -> None:
    pred = predict_risk(world, "hazard")
    friend.memes["worry"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{friend.id} frowned. "{hero.id}, don\'t use {hazard.label}. '
        f"{hazard.warns}. It could {hazard.break_word} right away.""
    )


def refuse(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} slowed down, looked at the little white piece, and took a breath."
    )
    hero.memes["bravery"] += 1
    friend.memes["relief"] += 1


def transform(world: World, hazard: Hazard, trans: Transform) -> None:
    item = world.get("hazard")
    item.safe_use = trans.to_use
    item.meters["risk"] = 0
    item.meters["remade"] += 1
    world.say(trans.text.replace("{object}", hazard.label))
    world.say(trans.result)


def rescue(world: World, parent: Entity, response: Response, hazard: Hazard) -> None:
    body = response.text.replace("{object}", hazard.label)
    world.say(
        f"{parent.label_word.capitalize()} came hurrying over and {body}."
    )
    world.say(
        "The danger eased, and the pasture air felt calm again."
    )


def lesson(world: World, parent: Entity, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    for kid in (hero, friend):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
    world.say("For a moment, everyone stood still.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt and said, "
        f'"That was a brave warning, and a smart choice. '
        f'{hazard.label.capitalize()} is not a toy, and a risky shortcut can snap faster than you can blink."'
    )


def ending(world: World, parent: Entity, hero: Entity, friend: Entity, theme: Theme) -> None:
    world.say(
        f"After that, they made a safer plan: {theme.send_off}. "
        f"{hero.id} led the way, and {friend.id} followed with a grin."
    )
    world.say(
        f"The same {theme.wild_word} that had looked scary now felt like part of the adventure."
    )


def tell(theme: Theme, hazard: Hazard, transform_cfg: Transform, response: Response,
         hero: str, hero_gender: str, friend: str, friend_gender: str,
         parent_type: str, delay: int, hero_age: int, friend_age: int,
         relation: str, trust: int) -> World:
    world = World()
    h = world.add(Entity(id=hero, kind="character", type=hero_gender, role="hero", attrs={"relation": relation}))
    f = world.add(Entity(id=friend, kind="character", type=friend_gender, role="friend", attrs={"relation": relation}))
    p = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    haz = world.add(Entity(id="hazard", kind="thing", type="thing", label=hazard.label, fragile=True))
    world.facts["theme"] = theme

    setup(world, h, f, theme)
    need_course(world, f, theme)
    world.para()
    tempt(world, h, hazard)
    warn(world, f, h, hazard)

    averted = trust >= 7 and hero_age > friend_age
    if averted:
        refuse(world, h, f)
        world.para()
        transform(world, hazard, transform_cfg)
        ending(world, p, h, f, theme)
        outcome = "averted"
    else:
        _do_risky(world, haz)
        world.para()
        body = f'"{h.id}! Stop! That thing could snap!"'
        world.say(body)
        if is_safe(response, delay):
            rescue(world, p, response, hazard)
            lesson(world, p, h, f, hazard)
            world.para()
            transform(world, hazard, transform_cfg)
            ending(world, p, h, f, theme)
            outcome = "contained"
        else:
            world.say(
                f"{p.label_word.capitalize()} rushed in but could not stop the trouble in time."
            )
            world.say(
                f"The little styrofoam piece cracked, floated off uselessly, and the crossing had to be abandoned."
            )
            world.say(
                "They got home safely, but the adventure had to end early."
            )
            outcome = "failed"

    world.facts.update(
        hero=h, friend=f, parent=p, hazard=hazard, transform=transform_cfg,
        response=response, outcome=outcome, delay=delay
    )
    return world


THEMES = {
    "adventure": Theme(
        id="adventure",
        scene="the edge of a windy pasture",
        rig="They packed a rope, a map, and a tin lunchbox, and they called the field their quest road.",
        hero_title="Captain",
        friend_title="Scout",
        goal="the old oak by the far hill",
        wild_word="pasture",
        safe_word="trail",
        send_off="follow the fence line to the old oak and back",
    ),
    "explore": Theme(
        id="explore",
        scene="a lumpy pasture beside the barn",
        rig="They carried a lantern, a coil of string, and a small compass, as if the field were a secret country.",
        hero_title="Trailmaster",
        friend_title="Guide",
        goal="the stone gate",
        wild_word="pasture",
        safe_word="path",
        send_off="follow the path beside the barn and return at sunset",
    ),
}

HAZARDS = {
    "styrofoam_boat": Hazard(
        id="styrofoam_boat",
        label="styrofoam",
        phrase="the styrofoam board",
        unsafe_use="as a boat over the mud",
        warns="it is too light and too crumbly for a real crossing",
        break_word="crack and sink into the muck",
    ),
    "styrofoam_bridge": Hazard(
        id="styrofoam_bridge",
        label="styrofoam",
        phrase="the styrofoam block",
        unsafe_use="as a bridge across the ditch",
        warns="it can break under a boot and send you tumbling",
        break_word="snap apart and tilt in the grass",
    ),
}

TRANSFORMS = {
    "float_marker": Transform(
        id="float_marker",
        from_use="boat",
        to_use="marker",
        text="So they tied the styrofoam to the fence as a bright marker instead.",
        result="That turned the risky idea into a trail sign, easy to see from far away.",
        tags={"transformation"},
    ),
    "raft_sign": Transform(
        id="raft_sign",
        from_use="bridge",
        to_use="sign",
        text="So they carried the styrofoam back and propped it upright like a little sign.",
        result="That turned the fragile thing into a guidepost for the adventure trail.",
        tags={"transformation"},
    ),
}

RESPONSES = {
    "rope_walk": Response(
        id="rope_walk",
        sense=3,
        power=2,
        text="tied a rope to the fence and made a safe stepping line instead of trusting the styrofoam",
        fail="tied a rope, but the shortcut was already too far gone",
        qa_text="tied a rope to the fence and made a safe stepping line",
        tags={"rope"},
    ),
    "lift_off": Response(
        id="lift_off",
        sense=2,
        power=1,
        text="grabbed the styrofoam before it drifted and set it back on the grass",
        fail="grabbed it, but it had already cracked and skidded away",
        qa_text="grabbed the styrofoam before it drifted and set it back on the grass",
        tags={"care"},
    ),
    "water_watching": Response(
        id="water_watching",
        sense=1,
        power=1,
        text="watched the puddle and hoped it would stay calm",
        fail="watched, but hoping was not enough",
        qa_text="watched the puddle and hoped it would stay calm",
        tags={"weak"},
    ),
}

CURATED = [
    StoryParams(theme="adventure", hazard="styrofoam_boat", transform="float_marker", response="rope_walk",
                hero="Nia", hero_gender="girl", friend="Ben", friend_gender="boy",
                parent="mother", delay=0, hero_age=7, friend_age=5, relation="friends", trust=8),
    StoryParams(theme="explore", hazard="styrofoam_bridge", transform="raft_sign", response="lift_off",
                hero="Milo", hero_gender="boy", friend="Ada", friend_gender="girl",
                parent="father", delay=1, hero_age=6, friend_age=5, relation="friends", trust=5),
]

GIRL_NAMES = ["Nia", "Ada", "Mia", "Luna", "Rose", "Ivy"]
BOY_NAMES = ["Ben", "Milo", "Theo", "Eli", "Noah", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for th in THEMES:
        for hz in HAZARDS:
            for tr in TRANSFORMS:
                if "styrofoam" in hz and "sign" in tr:
                    combos.append((th, hz, tr))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with a cautionary transformation.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("Refusing a response that is too weak and not child-sensible.")
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.transform is None or c[2] == args.transform)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, hazard, transform = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        theme=theme, hazard=hazard, transform=transform, response=response,
        hero=hero, hero_gender=hero_gender, friend=friend, friend_gender=friend_gender,
        parent=parent, delay=rng.randint(0, 1), hero_age=7, friend_age=5, relation="friends",
        trust=rng.randint(4, 9),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t: Theme = f["theme"]
    h: Hazard = f["hazard"]
    return [
        f'Write a child-friendly adventure story that uses the words "styrofoam" and "pasture".',
        f"Tell a cautionary adventure where {f['hero'].id} almost uses styrofoam in a risky way across the pasture, but a friend warns them and the idea changes.",
        f"Write a story where the styrofoam object gets transformed into a safer part of the adventure instead of being used as a bridge or boat.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    h = f["hero"]
    fr = f["friend"]
    p = f["parent"]
    hazard = f["hazard"]
    trans = f["transform"]
    qa = [
        ("Who is the story about?",
         f"It is about {h.id} and {fr.id}, who went on an adventure across a pasture with {p.label_word} nearby."),
        ("What risky thing did they want to use?",
         f"They wanted to use styrofoam as if it were a real crossing, but it was too fragile for that job."),
        ("Why did the warning matter?",
         f"{fr.id} noticed the risk before the plan got worse. That warning kept the adventure from becoming a tumble into mud or a broken mess."),
    ]
    if f["outcome"] in {"averted", "contained"}:
        qa.append((
            "How did the styrofoam change?",
            f"It stopped being a risky crossing and became {trans.result.lower()} The story turns the unsafe idea into a safer tool for the trip."
        ))
        qa.append((
            "How did the story end?",
            f"They kept the adventure going safely, with the pasture ahead of them and the styrofoam turned into something useful instead of dangerous."
        ))
    else:
        qa.append((
            "How did the story end?",
            "The fragile plan failed, so they had to stop and go home early. The caution still mattered because it showed why the shortcut was a bad idea."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is styrofoam?",
         "Styrofoam is a very light, foamy material. It can be useful for packing or craft ideas, but it is too fragile for rough jobs."),
        ("What is a pasture?",
         "A pasture is a grassy field where animals may graze. It can be wide, open, and windy."),
        ("Why should you be careful with fragile things?",
         "Fragile things can break when they are pushed too hard. It is smarter to use them only in ways they can handle."),
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
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(H) :- hazard(H), risky_use(H).
safe(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T, H, X) :- theme(T), hazard(H), transform(X), risk(H).
outcome(averted) :- friend_warned, safe_choice.
outcome(contained) :- not outcome(averted), safe(_).
outcome(failed) :- not outcome(averted), not safe(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
        lines.append(asp.fact("risky_use", h))
    for x in TRANSFORMS:
        lines.append(asp.fact("transform", x))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        params = CURATED[0]
        sample = generate(params)
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample)
    print("OK: smoke test and ASP parity check passed.")
    return rc


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def generate(params: StoryParams) -> StorySample:
    if params.hazard not in HAZARDS or params.transform not in TRANSFORMS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError("Response too weak.")
    world = tell(
        THEMES[params.theme], HAZARDS[params.hazard], TRANSFORMS[params.transform],
        RESPONSES[params.response], params.hero, params.hero_gender, params.friend,
        params.friend_gender, params.parent, params.delay, params.hero_age,
        params.friend_age, params.relation, params.trust
    )
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
