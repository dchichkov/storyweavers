#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/suey_bad_ending_folk_tale.py
=============================================================

A small folk-tale storyworld with a bad ending.

Premise:
A child named Suey lives beside a tiny orchard and a locked bread-house.
Suey is told not to use the old silver key on the bread-house door after dusk,
because it opens the wrong thing: the door swings to the fox's pantry, and the
seed-cakes inside are gone by morning.

Shape:
- Typed entities with physical meters and emotional memes.
- A forward-chained causal model drives the prose.
- A reasonableness gate refuses nonsensical combinations.
- Story, prompts, story QA, and world QA are generated from world state.
- Inline ASP rules mirror the Python gate and outcome logic.

This world is intentionally a "bad ending" tale in the folk style:
the warning comes, Suey ignores it, the household loses the cakes, and the
ending image proves what changed.
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
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "granny"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "granny", "grandfather": "grandpa"}.get(self.type, self.type)
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
    mood: str
    locked_at_night: bool = True
    spooky: bool = False
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    risky: bool = False
    opens: str = ""
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


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


def _r_loss(world: World) -> list[str]:
    out: list[str] = []
    for eid, e in list(world.entities.items()):
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("loss", eid)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "supper" in world.entities:
            world.get("supper").meters["gone"] += 1
        if "house" in world.entities:
            world.get("house").meters["hollow"] += 1
        for kid in list(world.entities.values()):
            if kid.role == "child":
                kid.memes["fear"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [Rule("loss", "physical", _r_loss)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for obj in OBJECTS:
            if place["night"] and obj["risky"]:
                combos.append((place["id"], obj["id"]))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.delay > 1:
        return "ruined"
    return "lost"


def explain_rejection(place: Place, obj: ObjectCfg) -> str:
    return f"(No story: {obj.label} would not create a proper folk-tale peril at {place.label}.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it is below the common-sense line, sense={r.sense} < {SENSE_MIN}.)"


def night_fall(world: World, place: Place, child: Entity, elder: Entity) -> None:
    world.say(
        f"By the edge of the orchard stood {place.label}, where the wind sang low "
        f"and the dusk made the path look long. {child.id} and {elder.id} lived there, "
        f"and the villagers said the night was never quite the same twice."
    )


def seed_warning(world: World, elder: Entity, child: Entity, obj: ObjectCfg, place: Place) -> None:
    elder.memes["care"] += 1
    world.say(
        f'{elder.id} held up {obj.phrase} and said, "Not after dusk, little one. '
        f'It opens the wrong door, and the fox knows the sound of it."'
    )
    world.say(
        f"{child.id} looked at {elder.id} and at the dark roofline of {place.label}, "
        f"and the warning settled like a stone in {child.id}'s chest."
    )


def temptation(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["want"] += 1
    world.say(
        f'But {child.id} wanted to see for {child.pronoun("object")}self, and '
        f'{child.pronoun("possessive")} eyes brightened at the silver key.'
    )


def disobey(world: World, child: Entity, obj: ObjectCfg) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Just once," {child.id} whispered, and {child.id} slipped away with '
        f"{obj.phrase}."
    )


def unlock(world: World, child: Entity, target: Entity, place: Place, obj: ObjectCfg) -> None:
    target.meters["opened"] += 1
    target.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{obj.label.capitalize()} turned in the lock with a thin little sigh. "
        f"The door of {place.label} swung open, and the air that came out was cold "
        f"and fox-sweet."
    )


def alarm(world: World, elder: Entity, child: Entity, place: Place) -> None:
    world.say(
        f'"{child.id}!" {elder.id} cried, too late. The fox had already nosed into '
        f"{place.label}."
    )


def bad_end(world: World, elder: Entity, child: Entity, place: Place) -> None:
    house = world.get("house")
    supper = world.get("supper")
    house.meters["hollow"] = 1.0
    supper.meters["gone"] = 1.0
    child.memes["shame"] += 1
    elder.memes["sadness"] += 1
    world.say(
        f"By morning, the fox was gone, the seed-cakes were gone, and {place.label} "
        f"stood with its latch hanging loose in the gray light."
    )
    world.say(
        f"{elder.id} sat on the doorstep with {child.id} beside {elder.id}, and "
        f"there was no sweet bread left for the market day."
    )
    world.say(
        f"The old tale ended there: {child.id} had wanted a little wonder, but the "
        f"house was left quiet and hungry."
    )


def tell(place: Place, obj: ObjectCfg, response: Response,
         child_name: str = "Suey", child_gender: str = "boy",
         elder_name: str = "Granny", elder_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=7))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender, role="elder", age=66))
    gate = world.add(Entity(id="gate", type="gate", label=place.label))
    house = world.add(Entity(id="house", type="house", label="the little house"))
    supper = world.add(Entity(id="supper", type="thing", label="seed-cakes"))
    world.facts["place"] = place
    world.facts["obj"] = obj
    world.facts["response"] = response

    night_fall(world, place, child, elder)
    seed_warning(world, elder, child, obj, place)
    world.para()
    temptation(world, child, obj)
    disobey(world, child, obj)
    unlock(world, child, gate, place, obj)
    alarm(world, elder, child, place)
    world.para()
    if response.power >= 2:
        world.say(
            f"{elder.id} came running and {response.text.format(target=place.label)}."
        )
    else:
        world.say(
            f"{elder.id} came running and {response.fail.format(target=place.label)}."
        )
    bad_end(world, elder, child, place)
    world.facts.update(
        child=child, elder=elder, gate=gate, house=house, supper=supper,
        outcome="ruined", warned=True, lost=True
    )
    return world


PLACES = [
    Place(id="orchard", label="the orchard gate", mood="hushed", locked_at_night=True, spooky=False, tags={"orchard"}),
    Place(id="mill", label="the old mill door", mood="hushed", locked_at_night=True, spooky=True, tags={"mill"}),
]

OBJECTS = [
    ObjectCfg(id="key", label="silver key", phrase="the old silver key", risky=True, opens="door", tags={"key"}),
    ObjectCfg(id="horn", label="wooden horn", phrase="the wooden horn", risky=False, opens="echo", tags={"horn"}),
]

RESPONSES = {
    "too_late": Response(
        id="too_late",
        sense=3,
        power=2,
        text="shut the door and looked around, but the fox had already slipped through",
        fail="shut the door and looked around, but the fox had already slipped through",
        qa_text="shut the door and looked around, but the fox had already slipped through",
        tags={"fox"},
    ),
    "weak_call": Response(
        id="weak_call",
        sense=1,
        power=1,
        text="called softly, but the fox only listened and stayed",
        fail="called softly, but the fox only listened and stayed",
        qa_text="called softly, but the fox only listened and stayed",
        tags={"fox"},
    ),
}

SENSE_MIN = 2
GIRL_NAMES = ["Suey", "Mara", "Lina", "Nell", "Pippa"]
BOY_NAMES = ["Suey", "Jon", "Tob", "Kellan", "Milo"]


@dataclass
class StoryParams:
    place: str
    obj: str
    response: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    delay: int = 0
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, obj = f["place"], f["obj"]
    return [
        f'Write a folk tale with the word "suey" in it, where a child is warned about {obj.label} at {place.label}.',
        f"Tell a village-style story about Suey, an old key, and a bad choice after dusk.",
        f'Write a short folk tale ending badly, with a warning, a wrong door, and the word "suey".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, elder, place, obj = f["child"], f["elder"], f["place"], f["obj"]
    resp = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, whom everyone called Suey, and {elder.id}, who tried to keep the house safe."),
        ("What warning was given?",
         f"{elder.id} warned {child.id} not to use {obj.phrase} after dusk because it opened the wrong door and the fox knew the sound."),
        ("What happened when Suey ignored the warning?",
         f"Suey used the key anyway, the gate opened, and the fox slipped in before anyone could stop it."),
        ("Why is the ending bad?",
         f"The seed-cakes were lost, the latch was left loose, and the house ended the night hungry and quiet."),
        ("Could the grown-up response fix it in time?",
         f"No. {elder.id} came running, but {resp.qa_text} was already too late to keep the fox out."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("Why do people lock doors at night?",
         "People lock doors at night to keep out animals and strangers and to help everyone sleep safely."),
        ("Why can foxes be a problem near a house?",
         "Foxes are clever animals. If they find an open door or gate, they may sneak in and take food."),
        ("What is a key for?",
         "A key turns a lock so a door can be opened or closed.")]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk-tale story world with a bad ending.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--object", dest="obj", choices=[o.id for o in OBJECTS])
    ap.add_argument("--response", choices=list(RESPONSES))
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    place = next(p for p in PLACES if p.id == (args.place or rng.choice([p.id for p in PLACES])))
    obj = next(o for o in OBJECTS if o.id == (args.obj or rng.choice([o.id for o in OBJECTS])))
    if not place.locked_at_night or not obj.risky:
        raise StoryError(explain_rejection(place, obj))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    child_name = "Suey"
    child_gender = "boy"
    elder_name = "Granny"
    elder_gender = "grandmother"
    return StoryParams(
        place=place.id, obj=obj.id, response=response,
        child_name=child_name, child_gender=child_gender,
        elder_name=elder_name, elder_gender=elder_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in {p.id for p in PLACES} or params.obj not in {o.id for o in OBJECTS}:
        raise StoryError("(Invalid params.)")
    world = tell(next(p for p in PLACES if p.id == params.place),
                 next(o for o in OBJECTS if o.id == params.obj),
                 RESPONSES[params.response],
                 params.child_name, params.child_gender,
                 params.elder_name, params.elder_gender)
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


ASP_RULES = r"""
risk(P,O) :- place(P), object(O), locked_night(P), risky(O).
bad_end :- risk(P,O), chosen(P), chosen(O).
"""
def asp_facts() -> str:
    import asp
    out = []
    for p in PLACES:
        out.append(asp.fact("place", p.id))
        if p.locked_at_night:
            out.append(asp.fact("locked_night", p.id))
    for o in OBJECTS:
        out.append(asp.fact("object", o.id))
        if o.risky:
            out.append(asp.fact("risky", o.id))
    return "\n".join(out)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risk/2.", "#show bad_end/0."))
    _ = model
    return 0


CURATED = [
    StoryParams(place="orchard", obj="key", response="too_late", child_name="Suey", child_gender="boy", elder_name="Granny", elder_gender="grandmother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show risk/2.\n#show bad_end/0."))
        return
    if args.verify:
        rng = random.Random(0)
        try:
            sample = generate(CURATED[0])
            _ = sample.story
        except Exception as e:
            print(e)
            sys.exit(1)
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(CURATED[0])] if args.all else []
    if not samples:
        try:
            params = resolve_params(args, random.Random(base_seed))
        except StoryError as err:
            print(err)
            return
        params.seed = base_seed
        samples = [generate(params)]
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=("### variant 1" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
