#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/favorite_llama_central_kindness_heartwarming.py
==============================================================================

A small heartwarming storyworld built from the seed words:
favorite, llama, central, with kindness at the center.

Premise:
A child is worried about a favorite ribbon at a central community fair.
A shy llama helps, kindness spreads, and the child learns to share warmth
instead of guarding the favorite thing alone.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven prose
- three QA sets
- Python reasonableness gate and inline ASP twin
- build_parser / resolve_params / generate / emit / main
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    friendly: bool = False
    gives_help: bool = False

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
class Place:
    id: str
    label: str
    central: bool = False
    welcoming: bool = True
    bright: bool = True
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
    favorite: bool = False
    fragile: bool = False
    could_be_shared: bool = True
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
class HelperCfg:
    id: str
    label: str
    phrase: str
    comfort: str
    kindness: int
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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    llama = world.get("llama")
    if child.memes["worry"] >= THRESHOLD and llama.memes["kindness"] >= THRESHOLD:
        sig = ("kindness",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["calm"] += 1
        llama.memes["bond"] += 1
        out.append("__kindness__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["calm"] >= THRESHOLD and "hall" in world.entities:
        sig = ("smile",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        world.get("hall").meters["warmth"] += 1
        out.append("__warmth__")
    return out


CAUSAL_RULES = [
    Rule("kindness", "social", _r_kindness),
    Rule("smile", "social", _r_smile),
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


def central_place(place: Place) -> bool:
    return place.central


def reasonable_combo(place: Place, obj: ObjectCfg, helper: HelperCfg) -> bool:
    return central_place(place) and obj.favorite and helper.kindness >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for oid, obj in OBJECTS.items():
            for hid, helper in HELPERS.items():
                if reasonable_combo(place, obj, helper):
                    combos.append((pid, oid, hid))
    return combos


def predict(world: World, helper: Entity) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    sim.get(helper.id).memes["kindness"] += 1
    propagate(sim, narrate=False)
    return {
        "calmed": sim.get("child").memes["calm"] >= THRESHOLD,
        "warmth": sim.get("hall").meters["warmth"],
    }


def setup(world: World, child: Entity, helper: Entity, place: Place, obj: ObjectCfg) -> None:
    child.memes["love"] += 1
    child.memes["worry"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"On a bright afternoon, {child.id} visited the {place.label}. "
        f"In the middle of it all, {child.id} kept hold of {obj.phrase}, {obj.label}, {obj.label}."
    )
    world.say(
        f"Near the central table, {helper.id} stood with a gentle smile. "
        f"{helper.id} was a llama with soft ears and a kind look."
    )


def worry(world: World, child: Entity, obj: ObjectCfg) -> None:
    world.say(
        f"{child.id} hugged {child.pronoun('possessive')} {obj.label} a little tighter. "
        f'"It is my favorite," {child.id} whispered.'
    )


def offer(world: World, helper: Entity, child: Entity, place: Place, obj: ObjectCfg, cfg: HelperCfg) -> None:
    pred = predict(world, helper)
    world.facts["predicted"] = pred
    world.say(
        f'{helper.id} tilted {helper.pronoun("possessive")} head. '
        f'"Would you like to share the central space with me?" {helper.id} asked. '
        f'"{cfg.phrase} can keep your {obj.label} safe while everyone looks."'
    )


def accept(world: World, child: Entity, helper: Entity, obj: ObjectCfg, cfg: HelperCfg) -> None:
    child.memes["generosity"] += 1
    child.memes["calm"] += 1
    child.memes["worry"] = 0.0
    helper.memes["joy"] += 1
    world.say(
        f"{child.id}'s face softened. {child.id} put {child.pronoun('possessive')} {obj.label} "
        f"carefully on {cfg.phrase}, then nodded. Together they made a little spot for friends."
    )
    world.say(
        f"{helper.id} nuzzled close, and the central table felt warmer at once. "
        f"{child.id} smiled because {child.pronoun('possessive')} favorite thing was still safe, "
        f"and now it was shared with kindness."
    )


def tell(place: Place, obj: ObjectCfg, helper: HelperCfg, child_name: str = "Mina", child_type: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    llama = world.add(Entity(id="llama", kind="character", type="llama", role="helper", friendly=True, gives_help=True))
    hall = world.add(Entity(id="hall", kind="thing", type="room", label="the hall"))
    child.memes["worry"] = 1.0
    llama.memes["kindness"] = float(helper.kindness)

    setup(world, child, llama, place, obj)
    world.para()
    worry(world, child, obj)
    offer(world, llama, child, place, obj, helper)
    propagate(world, narrate=True)
    world.para()
    accept(world, child, llama, obj, helper)
    world.get("hall").meters["warmth"] += 1
    world.facts.update(
        child=child,
        llama=llama,
        hall=hall,
        place=place,
        object=obj,
        helper=helper,
        outcome="shared",
    )
    return world


@dataclass
class StoryParams:
    place: str
    object: str
    helper: str
    child_name: str = "Mina"
    child_gender: str = "girl"
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
    "central": Place(id="central", label="central hall", central=True, welcoming=True, bright=True, tags={"central"}),
    "plaza": Place(id="plaza", label="plaza", central=True, welcoming=True, bright=True, tags={"central"}),
    "market": Place(id="market", label="market square", central=True, welcoming=True, bright=True, tags={"central"}),
    "corner": Place(id="corner", label="quiet corner", central=False, welcoming=False, bright=False, tags={"quiet"}),
}

OBJECTS = {
    "favorite_ribbon": ObjectCfg(id="favorite_ribbon", label="ribbon", phrase="a favorite ribbon", favorite=True, fragile=False, could_be_shared=True, tags={"favorite"}),
    "favorite_ball": ObjectCfg(id="favorite_ball", label="ball", phrase="a favorite ball", favorite=True, fragile=False, could_be_shared=True, tags={"favorite"}),
    "book": ObjectCfg(id="book", label="book", phrase="a little book", favorite=False, fragile=False, could_be_shared=True, tags={"book"}),
}

HELPERS = {
    "llama": HelperCfg(id="llama", label="llama", phrase="a soft blanket", comfort="blanket", kindness=3, tags={"llama", "kindness"}),
    "helpful_llama": HelperCfg(id="helpful_llama", label="llama", phrase="a tiny basket", comfort="basket", kindness=4, tags={"llama", "kindness"}),
}

GIRL_NAMES = ["Mina", "Lina", "Rosa", "Tia", "Nora"]
BOY_NAMES = ["Ben", "Owen", "Theo", "Max", "Eli"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the words "favorite", "llama", and "central".',
        f"Tell a gentle story about {f['child'].id} and a llama in a central place where kindness makes everyone feel safe.",
        f"Write a story where a favorite thing is shared in the central hall, and the ending feels warm and kind.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    obj = f["object"]
    helper = f["helper"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and a helpful llama who meet in a central place. The story follows how kindness helps them feel safe together."),
        ("What was {child.id}'s favorite thing?".replace("{child.id}", child.id),
         f"{child.id}'s favorite thing was {obj.phrase}. {child.id} held it close at first because it mattered a lot."),
        ("What did the llama do?",
         f"The llama offered a calm, kind way to share the central space. That gentle offer helped {child.id} relax and keep {obj.label} safe."),
        ("How did the story end?",
         f"It ended with {child.id} and the llama sharing the space kindly. The hall felt warmer, and {child.id} was smiling beside the favorite thing."),
    ]
    if f["predicted"]["calmed"]:
        qa.append((
            "Why did the child stop worrying?",
            f"The llama's kindness changed the mood. When the child saw a gentle offer instead of a push, the worry faded and trust grew."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a llama?",
         "A llama is an animal with a long neck and soft fur. People can be kind to llamas, and llamas can be gentle too."),
        ("What does central mean?",
         "Central means in the middle or at the center of something. It is a place where people can gather and be easy to find."),
        ("What is kindness?",
         "Kindness is when you treat someone gently and helpfully. Kind acts make people feel safe, seen, and cared for."),
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
        if e.friendly:
            bits.append("friendly=True")
        if e.gives_help:
            bits.append("gives_help=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
favorite_object(O) :- object(O), favorite(O).
central_place(P) :- place(P), central(P).
kind_story(P,O,H) :- central_place(P), favorite_object(O), helper(H), kindness(H,K), K >= 2.
shared_ending :- kind_story(P,O,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.central:
            lines.append(asp.fact("central", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.favorite:
            lines.append(asp.fact("favorite", oid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("kindness", hid, h.kindness))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kind_story/3."))
    return sorted(set(asp.atoms(model, "kind_story")))


def asp_verify() -> int:
    rc = 0
    try:
        import asp
        asp_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only in ASP:", sorted(asp_set - py_set))
        print("  only in Python:", sorted(py_set - asp_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, object=None, helper=None, child_gender=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"generate() smoke test failed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld with kindness, a llama, and a central place.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
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
    obj_choice = getattr(args, "object_", None)
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (obj_choice is None or c[1] == obj_choice)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, helper = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    return StoryParams(place=place, object=obj, helper=helper, child_name=child_name, child_gender=gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.object not in OBJECTS or params.helper not in HELPERS:
        raise StoryError("Invalid StoryParams choices.")
    place = PLACES[params.place]
    obj = OBJECTS[params.object]
    helper = HELPERS[params.helper]
    if not reasonable_combo(place, obj, helper):
        raise StoryError("(No valid combination matches the given StoryParams.)")
    world = tell(place, obj, helper, child_name=params.child_name, child_type=params.child_gender)
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


CURATED = [
    StoryParams(place="central", object="favorite_ribbon", helper="llama", child_name="Mina", child_gender="girl"),
    StoryParams(place="plaza", object="favorite_ball", helper="helpful_llama", child_name="Owen", child_gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show kind_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show kind_story/3."))
        combos = sorted(set(asp.atoms(model, "kind_story")))
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
