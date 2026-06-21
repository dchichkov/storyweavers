#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barrette_suspense_friendship_fairy_tale.py
===========================================================================

A small storyworld in a fairy-tale register: a child loses a treasured
barrette, suspense grows in a moonlit place, and a friend helps recover it.
The world is simulated with typed entities carrying physical ``meters`` and
emotional ``memes`` so the prose grows from state changes rather than from a
fixed paragraph template.

The core premise is simple:
- a child treasures a barrette,
- a breeze or mishap sends it into a risky place,
- a friend and/or grown helper search with growing suspense,
- friendship and care resolve the tension,
- the ending image proves the barrette is safe again.

This world supports default runs, curated runs, JSON, trace, QA, and an
inline ASP twin for parity checking.
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
FEAR_RISE = 1.0
JOY_RISE = 1.0


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
    owner: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "queen", "witch"}
        male = {"boy", "father", "dad", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)
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
class Place:
    id: str
    label: str
    dark: bool = False
    risky: bool = False
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
class Barrette:
    id: str
    label: str
    phrase: str
    sparkle: str
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
    courage: int
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
    power: int
    sense: int
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


@dataclass
class StoryParams:
    place: str
    barrette: str
    helper: str
    response: str
    heroine: str
    heroine_gender: str
    friend: str
    friend_gender: str
    parent: str
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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_fear(world: World) -> list[str]:
    out = []
    if world.get("barrette").meters["lost"] >= THRESHOLD and world.get("hero").memes["worry"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["fear"] += FEAR_RISE
            world.get("friend").memes["fear"] += 0.5
            out.append("__fear__")
    return out


def _r_joy(world: World) -> list[str]:
    out = []
    if world.get("barrette").meters["found"] >= THRESHOLD:
        sig = ("joy",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["joy"] += JOY_RISE
            world.get("friend").memes["joy"] += JOY_RISE
            out.append("__joy__")
    return out


CAUSAL_RULES = [Rule("fear", _r_fear), Rule("joy", _r_joy)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard(place: Place, barrette: Barrette) -> bool:
    return place.dark and place.risky and "barrette" in barrette.tags


def sensible_response(resp: Response) -> bool:
    return resp.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for bid, barrette in BARRETTES.items():
            for hid, helper in HELPERS.items():
                if hazard(place, barrette) and helper.courage >= 1:
                    combos.append((pid, bid, hid))
    return combos


def _do_loss(world: World, place: Place, barrette: Barrette) -> None:
    world.get("barrette").meters["lost"] = 1.0
    world.get("place").meters["searched"] += 1
    propagate(world, narrate=False)


def predict_search(world: World) -> dict:
    sim = world.copy()
    _do_loss(sim, PLACES[sim.facts["place"].id], BARRETTES[sim.facts["barrette"].id])
    return {
        "fear": sim.get("hero").memes["fear"],
        "lost": sim.get("barrette").meters["lost"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, friend: Entity, place: Place, barrette: Barrette) -> None:
    world.say(
        f"Once upon a lantern-lit evening, {hero.id} and {friend.id} walked to {place.label}. "
        f"{hero.id} wore {barrette.phrase}, and it shone with {barrette.sparkle}."
    )


def suspense(world: World, hero: Entity, friend: Entity, place: Place, barrette: Barrette) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 0.5
    world.say(
        f"But as they reached the old path, a sharp breeze tugged at {hero.pronoun('possessive')} hair. "
        f"The {barrette.label} slipped away and vanished near {place.label}."
    )
    world.say(
        f"{friend.id} gasped softly. The little path turned quiet, and even the crickets seemed to hold their breath."
    )


def search(world: World, hero: Entity, friend: Entity, helper: Entity, place: Place) -> None:
    pred = predict_search(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f"{friend.id} squeezed {hero.pronoun('possessive')} hand. \"Stay close,\" {friend.pronoun()} said, "
        f"and together they searched by the moonlight."
    )
    if pred["fear"] >= 1:
        world.say(
            f"{helper.label_word.capitalize()} heard their whisper and came with a steady lantern, "
            f"because the dark little place could make any heart tremble."
        )


def recover(world: World, hero: Entity, friend: Entity, helper: Entity, barrette: Barrette, response: Response) -> None:
    world.get("barrette").meters["found"] = 1.0
    world.get("barrette").meters["lost"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} {response.text.replace('{barrette}', barrette.label)}."
    )
    world.say(
        f"At last, the {barrette.label} gleamed in the grass, caught on a silver leaf, "
        f"and {hero.id} laughed with relief."
    )


def ending(world: World, hero: Entity, friend: Entity, barrette: Barrette) -> None:
    world.say(
        f"{hero.id} pinned the {barrette.label} back in place, and {friend.id} tied the ribbon once more. "
        f"Under the soft moon, their friendship looked brighter than any jewel."
    )


BARRETTES = {
    "ruby": Barrette(
        id="ruby",
        label="ruby barrette",
        phrase="a ruby barrette",
        sparkle="a tiny red glow",
        tags={"barrette"},
    ),
    "pearl": Barrette(
        id="pearl",
        label="pearl barrette",
        phrase="a pearl barrette",
        sparkle="a pearly shimmer",
        tags={"barrette"},
    ),
    "golden": Barrette(
        id="golden",
        label="golden barrette",
        phrase="a golden barrette",
        sparkle="a warm gold sparkle",
        tags={"barrette"},
    ),
}

PLACES = {
    "hedge": Place(id="hedge", label="the thorn hedge", dark=True, risky=True, tags={"dark", "hedge"}),
    "well": Place(id="well", label="the old well", dark=True, risky=True, tags={"dark", "well"}),
    "grove": Place(id="grove", label="the moonlit grove", dark=True, risky=True, tags={"dark", "grove"}),
}

HELPERS = {
    "sister": Helper(id="sister", label="the sister", phrase="a brave sister", courage=2, tags={"friendship"}),
    "cousin": Helper(id="cousin", label="the cousin", phrase="a kind cousin", courage=2, tags={"friendship"}),
    "friend": Helper(id="friend", label="the friend", phrase="a loyal friend", courage=2, tags={"friendship"}),
}

RESPONSES = {
    "lantern": Response(
        id="lantern",
        power=3,
        sense=3,
        text="lifted a lantern high and found it at once",
        fail="looked and looked, but the darkness hid it",
        tags={"light"},
    ),
    "listen": Response(
        id="listen",
        power=2,
        sense=3,
        text="listened for the soft click of the clasp and found it by the roots",
        fail="listened, but the wind had already carried it farther away",
        tags={"listen"},
    ),
    "broom": Response(
        id="broom",
        power=1,
        sense=1,
        text="swished a broom about and hoped for the best",
        fail="swished a broom, but it was far too little help",
        tags={"weak"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elia", "Sora", "Nora", "Tessa", "Luna", "Ivy"]
BOY_NAMES = ["Finn", "Milo", "Theo", "Robin", "Eli", "Ned", "Oren"]
TRAITS = ["gentle", "brave", "curious", "kind"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a lost barrette and a loyal friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--barrette", choices=BARRETTES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--heroine")
    ap.add_argument("--heroine-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "queen", "king"])
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
    if args.response and not sensible_response(RESPONSES[args.response]):
        raise StoryError(f"(Refusing response '{args.response}': it is too weak for a suspense story.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.barrette is None or c[1] == args.barrette)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, barrette, helper = rng.choice(sorted(combos))
    response = args.response or rng.choice(["lantern", "listen"])
    heroine_gender = args.heroine_gender or "girl"
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    heroine = args.heroine or rng.choice(GIRL_NAMES if heroine_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != heroine])
    parent = args.parent or rng.choice(["mother", "father", "queen"])
    return StoryParams(
        place=place,
        barrette=barrette,
        helper=helper,
        response=response,
        heroine=heroine,
        heroine_gender=heroine_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id=params.heroine, kind="character", type=params.heroine_gender, role="hero", traits=["tender"]))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend", traits=["loyal"]))
    helper = world.add(Entity(id="helper", kind="character", type=params.parent, role="helper", label=f"the {params.parent}"))
    place = world.add(Entity(id="place", type="place", label=PLACES[params.place].label))
    barrette = world.add(Entity(id="barrette", type="object", label=BARRETTES[params.barrette].label))

    world.facts.update(place=PLACES[params.place], barrette=BARRETTES[params.barrette], helper=HELPERS[params.helper], response=RESPONSES[params.response])

    introduce(world, hero, friend, PLACES[params.place], BARRETTES[params.barrette])
    world.para()
    suspense(world, hero, friend, PLACES[params.place], BARRETTES[params.barrette])
    world.para()
    search(world, hero, friend, helper, PLACES[params.place])
    world.para()
    recover(world, hero, friend, helper, BARRETTES[params.barrette], RESPONSES[params.response])
    ending(world, hero, friend, BARRETTES[params.barrette])

    world.facts.update(hero=hero, friend=friend, helper_ent=helper, outcome="found")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a young child that includes the word "{f["barrette"].label}" and a loyal friend helping in the dark.',
        f"Tell a suspenseful friendship tale where a {f['barrette'].label} is lost near {f['place'].label} and is found by moonlight.",
        f"Write a gentle fairy tale with suspense, friendship, and a happy ending where someone recovers a {f['barrette'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    helper: Entity = f["helper_ent"]
    barrette: Barrette = f["barrette"]
    place: Place = f["place"]
    return [
        (
            "What did the story revolve around?",
            f"It revolved around {hero.id}'s {barrette.label}, which was precious enough to matter when it went missing. The loss created the suspense that pulled the scene forward.",
        ),
        (
            f"Why did {hero.id} feel afraid?",
            f"{hero.id} felt afraid because the {barrette.label} disappeared near {place.label}, a dark place where small things are hard to spot. The quiet of the place made the search feel more tense.",
        ),
        (
            "How was the problem solved?",
            f"{friend.id} stayed close, and {helper.label_word} helped with a lantern. That kind help found the {barrette.label} before the fear could grow larger.",
        ),
        (
            "How did the story end?",
            f"It ended with the {barrette.label} pinned safely back in place and the two children smiling together. Their friendship was the bright thing left after the suspense was gone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["barrette"].tags) | set(f["place"].tags) | set(f["helper"].tags)
    out = []
    if "barrette" in tags:
        out.append(("What is a barrette?", "A barrette is a small hair clip that helps hold hair in place. People often wear it as a pretty decoration too."))
    if "dark" in tags:
        out.append(("Why can a dark place feel spooky?", "A dark place makes it harder to see what is there. When you cannot see well, even a little sound can feel mysterious."))
    if "friendship" in tags:
        out.append(("What is friendship?", "Friendship is when people care about each other, help each other, and stay kind. Friends make scary moments feel less lonely."))
    if f["response"].id == "lantern":
        out.append(("What does a lantern do?", "A lantern gives off light so people can see in the dark. It is a safe helper in a story like this."))
    if f["response"].id == "listen":
        out.append(("What does it mean to listen closely?", "Listening closely means being quiet and paying attention to small sounds. That can help you notice where something fell."))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hedge", barrette="ruby", helper="sister", response="lantern", heroine="Lina", heroine_gender="girl", friend="Milo", friend_gender="boy", parent="mother"),
    StoryParams(place="grove", barrette="pearl", helper="friend", response="listen", heroine="Mira", heroine_gender="girl", friend="Nora", friend_gender="girl", parent="queen"),
    StoryParams(place="well", barrette="golden", helper="cousin", response="lantern", heroine="Tessa", heroine_gender="girl", friend="Finn", friend_gender="boy", parent="father"),
]


def valid_story_params(args: StoryParams) -> bool:
    return hazard(PLACES[args.place], BARRETTES[args.barrette]) and sensible_response(RESPONSES[args.response])


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.barrette not in BARRETTES or params.helper not in HELPERS or params.response not in RESPONSES:
        raise StoryError("Invalid params.")
    if not hazard(PLACES[params.place], BARRETTES[params.barrette]):
        raise StoryError("This place and barrette do not create enough suspense for a story.")
    if not sensible_response(RESPONSES[params.response]):
        raise StoryError("Response is too weak for the story.")
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
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid in BARRETTES:
        lines.append(asp.fact("barrette", bid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 2))
    for pid, p in PLACES.items():
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
    for bid, b in BARRETTES.items():
        if "barrette" in b.tags:
            lines.append(asp.fact("sparkly", bid))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(P,B) :- dark(P), risky(P), barrette(B).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(P,B,H) :- hazard(P,B), helper(H), sensible(R).
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH in valid combos")
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generate() smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_story_params_from_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.barrette is None or c[1] == args.barrette)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, barrette, helper = rng.choice(sorted(combos))
    response = args.response or rng.choice(["lantern", "listen"])
    return StoryParams(
        place=place,
        barrette=barrette,
        helper=helper,
        response=response,
        heroine=args.heroine or rng.choice(GIRL_NAMES),
        heroine_gender=args.heroine_gender or "girl",
        friend=args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != (args.heroine or "")]),
        friend_gender=args.friend_gender or rng.choice(["girl", "boy"]),
        parent=args.parent or rng.choice(["mother", "father", "queen"]),
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and not sensible_response(RESPONSES[args.response]):
        raise StoryError(f"(Refusing response '{args.response}': too weak.)")
    return build_story_params_from_choice(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, b, h in asp_valid_combos():
            print(f"  {p:8} {b:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.heroine} and {p.friend}: {p.barrette} near {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
