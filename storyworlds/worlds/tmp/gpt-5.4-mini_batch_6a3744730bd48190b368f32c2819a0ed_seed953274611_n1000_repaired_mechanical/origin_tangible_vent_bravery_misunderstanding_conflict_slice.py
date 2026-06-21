#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/origin_tangible_vent_bravery_misunderstanding_conflict_slice.py
================================================================================================

A small slice-of-life story world about a child, a misplaced craft, and a gentle
misunderstanding that turns into a brave apology.

The seed words are woven into the domain itself:
- origin: where a thing came from
- tangible: a real object that can be held
- vent: a wall vent in a quiet room

The story premise is simple and everyday:
A child finds a tangible object near a vent, assumes the wrong origin for it,
and a small conflict follows. Bravery is not about fighting; it is about asking,
admitting the mistake, and making things right.

The generated stories are intentionally modest and grounded. They should feel
like a real afternoon in a home, classroom, or community room: a small worry,
a misunderstanding, a short conflict, then a calm resolution that leaves the
world a little kinder than before.
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
        female = {"girl", "mother", "mom", "woman", "teacher", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
    origin_place: str
    vent_place: str
    mood: str
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
    origin_label: str
    tangible: bool = True
    fragile: bool = False
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
    ease: int
    success_text: str
    fail_text: str
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
        clone = World()
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] += 1
        out.append("__conflict__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["conflict"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("relief", "social", _r_relief),
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


def reasonableness_gate(place: Place, obj: ObjectThing, response: Response) -> bool:
    return place.id in PLACES and obj.id in OBJECTS and response.id in RESPONSES


def did_misunderstand(place: Place, obj: ObjectThing) -> bool:
    return place.vent_place == "near" and obj.tangible


def should_bring_up_bravery(hero: Entity) -> bool:
    return hero.memes["bravery"] >= 1 or "brave" in hero.traits


def choose_title(hero: Entity) -> str:
    return "kid" if hero.type in {"boy", "girl"} else hero.label_word


def tell(place: Place, obj: ObjectThing, response: Response,
         hero_name: str = "Nina", hero_gender: str = "girl",
         helper_name: str = "Mara", helper_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "mother",
         seed: Optional[int] = None) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    hero.memes["bravery"] = 1.0
    helper.memes["care"] = 1.0
    adult.memes["patience"] = 1.0

    world.say(
        f"On an ordinary afternoon in {place.label}, {hero.id} and {helper.id} were "
        f"tidying up after a small craft project. The room was quiet except for the soft hum "
        f"from the vent in the wall."
    )
    world.say(
        f"Near that vent, {hero.id} noticed a tangible little thing: {obj.phrase}. "
        f"{hero.id} picked it up and turned it over in {hero.pronoun('possessive')} hands."
    )
    world.para()
    if did_misunderstand(place, obj):
        hero.memes["misunderstanding"] += 1
        world.say(
            f"\"Maybe this came from the vent,\" {hero.id} said. \"Maybe it blew out of the wall "
            f"and nobody was looking.\""
        )
        world.say(
            f"{helper.id} frowned. \"I don't think so. It looks like it has a real origin, and I think "
            f"it belongs to someone.\""
        )
        world.say(
            f"{hero.id} felt a little embarrassed and a little stubborn. A tiny conflict started "
            f"between wanting to be right and wanting to be kind."
        )
        propagate(world, narrate=False)
    else:
        world.say(
            f"{hero.id} was careful enough to ask where it came from before making a guess, so the "
            f"little misunderstanding never grew into a conflict."
        )

    world.para()
    world.say(
        f"{adult.label_word.capitalize()} came in after hearing the voices and looked at the item. "
        f"\"That did not come from the vent,\" {adult.id} said gently. \"It was left here by the art "
        f"club last week. Its origin is the supply box.\""
    )
    hero.memes["bravery"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{hero.id} took a breath. Being brave felt tangible now, like something {hero.id} could hold "
        f"inside {hero.pronoun('possessive')} chest."
    )

    response_ok = response.sense >= 2 and response.ease >= 1
    if response_ok:
        world.say(
            f"Then {hero.id} did the bravest thing: {hero.pronoun().capitalize()} admitted the mistake. "
            f"\"I thought it came from the vent,\" {hero.id} said, \"but I was wrong.\""
        )
        world.say(
            f"{adult.id} smiled. \"Thanks for saying that. Questions are good, and admitting a misunderstanding "
            f"is part of growing up.\""
        )
        world.say(
            f"{helper.id} handed the object back to the supply basket. The little conflict faded, and the room "
            f"felt calm again."
        )
        world.para()
        world.say(
            f"Before long, the craft table was neat, the vent hummed softly, and {hero.id} knew the object's "
            f"real origin. The day stayed small and ordinary, but {hero.id} walked away feeling taller."
        )
        outcome = "resolved"
    else:
        world.say(
            f"{hero.id} wanted to fix the feeling fast, but the chosen reply did not help much. The conflict "
            f"lingered until {adult.id} stepped in with a simpler, kinder answer."
        )
        world.say(
            f"In the end, {hero.id} still had to admit the mistake, and the room quieted down after that."
        )
        outcome = "softened"

    world.facts.update(
        place=place,
        obj=obj,
        response=response,
        hero=hero,
        helper=helper,
        adult=adult,
        outcome=outcome,
        misunderstood=bool(hero.memes["misunderstanding"] >= THRESHOLD),
        conflict=bool(hero.memes["conflict"] >= THRESHOLD),
        bravery=float(hero.memes["bravery"]),
    )
    return world


@dataclass
class StoryParams:
    place: str
    object: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    adult: str
    adult_gender: str
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


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the classroom",
        origin_place="the supply shelf",
        vent_place="near",
        mood="quiet",
        tags={"vent", "origin"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        origin_place="the counter basket",
        vent_place="near",
        mood="calm",
        tags={"vent", "origin"},
    ),
    "community_room": Place(
        id="community_room",
        label="the community room",
        origin_place="the lost-and-found shelf",
        vent_place="near",
        mood="sunlit",
        tags={"vent", "origin"},
    ),
}

OBJECTS = {
    "pencil_case": ObjectThing(
        id="pencil_case",
        label="pencil case",
        phrase="a small blue pencil case",
        origin_label="the art club supply box",
        tangible=True,
        fragile=False,
        tags={"tangible", "origin"},
    ),
    "button": ObjectThing(
        id="button",
        label="button",
        phrase="a shiny red button",
        origin_label="a sewing jar",
        tangible=True,
        fragile=False,
        tags={"tangible", "origin"},
    ),
    "keychain": ObjectThing(
        id="keychain",
        label="keychain",
        phrase="a tiny star keychain",
        origin_label="the library prize drawer",
        tangible=True,
        fragile=False,
        tags={"tangible", "origin"},
    ),
}

RESPONSES = {
    "admit": Response(
        id="admit",
        sense=3,
        ease=3,
        success_text="admitted the mistake and asked where it really came from",
        fail_text="tried to explain it away and only made the moment tighter",
        tags={"bravery", "misunderstanding", "conflict"},
    ),
    "ask": Response(
        id="ask",
        sense=3,
        ease=2,
        success_text="asked calmly about the origin and listened",
        fail_text="asked too quickly and still sounded upset",
        tags={"bravery", "misunderstanding"},
    ),
    "apologize": Response(
        id="apologize",
        sense=3,
        ease=2,
        success_text="gave a small apology and handed the item back",
        fail_text="mumbled and still kept the item in hand",
        tags={"bravery", "conflict"},
    ),
}


GIRL_NAMES = ["Nina", "Mara", "Ivy", "Sofia", "Leah", "June", "Ada", "Pia"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Finn", "Leo", "Arlo", "Theo", "Milo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for oid, obj in OBJECTS.items():
            if did_misunderstand(place, obj):
                for rid in RESPONSES:
                    combos.append((pid, oid, rid))
    return combos


def explain_rejection(place: Place, obj: ObjectThing) -> str:
    return (
        f"(No story: this setup would not naturally create a misunderstanding. "
        f"Try a tangible item found near the vent, like {obj.phrase} in {place.label}.)"
    )


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': it is not a supported response in this world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: origin, tangible, and vent, with bravery and a small misunderstanding."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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
    if args.object and args.place:
        if not did_misunderstand(PLACES[args.place], OBJECTS[args.object]):
            raise StoryError(explain_rejection(PLACES[args.place], OBJECTS[args.object]))
    if args.response and args.response not in RESPONSES:
        raise StoryError(explain_response(args.response))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, obj_id, response_id = rng.choice(sorted(combos))
    gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or ("girl" if gender == "boy" else "boy")
    helper = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    adult = args.adult or ("Mom" if adult_gender == "mother" else "Dad")
    return StoryParams(
        place=place_id,
        object=obj_id,
        response=args.response or response_id,
        hero=hero,
        hero_gender=gender,
        helper=helper,
        helper_gender=helper_gender,
        adult=adult,
        adult_gender=adult_gender,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES.get(params.place)
    obj = OBJECTS.get(params.object)
    response = RESPONSES.get(params.response)
    if place is None or obj is None or response is None:
        raise StoryError("Invalid params: unknown place, object, or response.")
    world = tell(
        place=place,
        obj=obj,
        response=response,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        adult_name=params.adult,
        adult_gender=params.adult_gender,
        seed=params.seed,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    obj: ObjectThing = f["obj"]
    response: Response = f["response"]
    hero: Entity = f["hero"]
    return [
        f'Write a slice-of-life story that includes the words "origin", "{obj.label}", and "vent".',
        f"Tell a small story about {hero.id} noticing {obj.phrase} near a vent and wondering about its origin.",
        f"Write a calm story where a child makes a misunderstanding about where {obj.label} came from, then finds the bravery to admit it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    adult: Entity = f["adult"]
    obj: ObjectThing = f["obj"]
    place: Place = f["place"]
    response: Response = f["response"]
    qa = [
        ("What was the story about?",
         f"It was about {hero.id}, who found {obj.phrase} near a vent and wondered about its origin. It stayed a small, everyday story in {place.label}."),
        ("Why did the misunderstanding happen?",
         f"{hero.id} guessed that {obj.label} might have come from the vent. That guess was wrong, so the guess turned into a little conflict when {helper.id} disagreed."),
        ("What did the adult explain?",
         f"{adult.id} explained that the item had a real origin in the art club's supplies. The vent was only a noisy part of the room, not the source of the object."),
    ]
    if f.get("conflict"):
        qa.append((
            "What made the conflict go away?",
            f"{hero.id} admitted the mistake and listened. That brave choice made the misunderstanding shrink, and the room felt calm again."
        ))
    if f.get("outcome") == "resolved":
        qa.append((
            "How did the story end?",
            f"It ended quietly, with the item returned and everyone feeling better. {hero.id} learned that asking about origin is better than guessing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["obj"].tags) | set(f["response"].tags) | {"origin", "tangible", "vent", "bravery", "misunderstanding", "conflict"}
    out = []
    if "origin" in tags:
        out.append(("What does origin mean?",
                    "Origin means where something came from or where it started. People often ask about origin when they find something and want to know its story."))
    if "tangible" in tags:
        out.append(("What does tangible mean?",
                    "Tangible means something real that you can touch and hold. A tangible thing is not just an idea or a thought."))
    if "vent" in tags:
        out.append(("What is a vent?",
                    "A vent is an opening that lets air move through a room. It can make a soft hum or whooshing sound."))
    if "bravery" in tags:
        out.append(("What is bravery?",
                    "Bravery means doing the right thing even when you feel nervous. Sometimes bravery looks like telling the truth or saying sorry."))
    if "misunderstanding" in tags:
        out.append(("What is a misunderstanding?",
                    "A misunderstanding happens when people think something different from what is true. Talking kindly can clear it up."))
    if "conflict" in tags:
        out.append(("What is conflict?",
                    "Conflict is a small problem or disagreement between people. It can fade once everyone listens and explains what they mean."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(H) :- hero(H), sees_near_vent(H), tangible_item(H).
conflict(H) :- misunderstanding(H).
resolved(H) :- conflict(H), admits_mistake(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("tangible", oid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show misunderstanding/1."))
    return sorted(set(asp.atoms(model, "misunderstanding")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != {("classroom",), ("kitchen",), ("community_room",)}:
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, object=None, response=None, hero=None, hero_gender=None,
            helper=None, helper_gender=None, adult=None, adult_gender=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print("OK: story generation smoke test passed.")
    return rc


CURATED = [
    StoryParams(place="classroom", object="pencil_case", response="admit",
                hero="Nina", hero_gender="girl", helper="Mara", helper_gender="girl",
                adult="Mom", adult_gender="mother"),
    StoryParams(place="kitchen", object="button", response="ask",
                hero="Owen", hero_gender="boy", helper="Eli", helper_gender="boy",
                adult="Dad", adult_gender="father"),
    StoryParams(place="community_room", object="keychain", response="apologize",
                hero="Leah", hero_gender="girl", helper="June", helper_gender="girl",
                adult="Mom", adult_gender="mother"),
]


def generate_prompts(world: World) -> list[str]:
    return generation_prompts(world)


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"origin", "tangible", "vent", "bravery", "misunderstanding", "conflict"}
    return [
        ("What does origin mean?",
         "Origin means where something came from or where it started. People often ask about origin when they find something and want to know its story."),
        ("What does tangible mean?",
         "Tangible means something real that you can touch and hold. A tangible thing is not just an idea or a thought."),
        ("What is a vent?",
         "A vent is an opening that lets air move through a room. It can make a soft hum or whooshing sound."),
        ("What is bravery?",
         "Bravery means doing the right thing even when you feel nervous. Sometimes bravery looks like telling the truth or saying sorry."),
        ("What is a misunderstanding?",
         "A misunderstanding happens when people think something different from what is true. Talking kindly can clear it up."),
        ("What is conflict?",
         "Conflict is a small problem or disagreement between people. It can fade once everyone listens and explains what they mean."),
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny slice-of-life storyworld about origin, tangible, and vent.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show misunderstanding/1.\n#show conflict/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show misunderstanding/1."))
        print(f"{len(asp.atoms(model, 'misunderstanding'))} compatible entries.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
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


if __name__ == "__main__":
    main()
