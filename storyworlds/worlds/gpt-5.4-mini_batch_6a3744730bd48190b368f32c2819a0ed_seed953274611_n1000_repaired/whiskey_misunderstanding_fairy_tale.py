#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/whiskey_misunderstanding_fairy_tale.py
======================================================================

A standalone storyworld for a small fairy-tale misunderstanding about whiskey:
a child finds a bottle with a grown-up label, mistakes it for a sweet potion,
and a careful adult clears up the mix-up before anyone drinks it. The storyworld
keeps the premise tiny, concrete, and state-driven: misunderstanding, warning,
clarification, and a safe ending image.

The world uses typed entities with physical meters and emotional memes, a small
forward rule engine, an explicit reasonableness gate, and an inline ASP twin.
It supports story generation, JSON, QA, trace, and verify modes.
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
SAFE_MIN_AGE = 4


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
        female = {"girl", "mother", "queen", "princess", "woman", "sister"}
        male = {"boy", "father", "king", "prince", "man", "brother"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Beverage:
    id: str
    label: str
    phrase: str
    where: str
    age_min: int
    senses: int
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
class Vessel:
    id: str
    label: str
    phrase: str
    material: str
    clear: bool
    closable: bool
    sweet_smell: bool
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_misread(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["curiosity"] < THRESHOLD:
            continue
        if e.attrs.get("misread") != "whiskey":
            continue
        sig = ("misread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] += 1
        out.append("__misread__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.get("bottle")
    if bottle.meters["opened"] < THRESHOLD:
        return out
    for e in list(world.entities.values()):
        if e.role != "child":
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_clarify(world: World) -> list[str]:
    out: list[str] = []
    if world.get("adult").memes["clarified"] < THRESHOLD:
        return out
    sig = ("clarify_done",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__clarify__")
    return out


CAUSAL_RULES = [Rule("misread", _r_misread), Rule("worry", _r_worry), Rule("clarify", _r_clarify)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def is_reasonable(beverage: Beverage, vessel: Vessel) -> bool:
    return beverage.id == "whiskey" and vessel.clear and vessel.closable and beverage.age_min >= SAFE_MIN_AGE


def sense_gate(response: Response) -> bool:
    return response.sense >= SENSE_MIN


def explain_rejection(beverage: Beverage, vessel: Vessel) -> str:
    return (
        f"(No story: {beverage.label} belongs in a sealed grown-up vessel, and "
        f"{vessel.label} does not make a clear fairy-tale misunderstanding.)"
    )


def explain_response(response: Response) -> str:
    return f"(Refusing response '{response.id}': it scores too low on common sense.)"


def predict(world: World, beverage: Beverage) -> dict:
    sim = world.copy()
    sim.get("child").attrs["misread"] = beverage.id
    sim.get("bottle").meters["opened"] += 1
    propagate(sim, narrate=False)
    return {
        "worry": sim.get("child").memes["worry"],
        "opened": sim.get("bottle").meters["opened"],
    }


def scene(world: World, child: Entity, adult: Entity, beverage: Beverage, vessel: Vessel) -> None:
    child.memes["curiosity"] += 1
    child.memes["joy"] += 1
    adult.memes["care"] += 1
    world.say(
        f"Once in a little cottage at the edge of the forest, {child.id} found "
        f"{vessel.phrase} on a high shelf. The bottle held {beverage.label}, "
        f"and the label glittered like a spell."
    )
    world.say(
        f'{child.id} leaned close and whispered, "It smells sweet. Is this a potion?" '
        f"{adult.id} was nearby, tending the hearth."
    )


def misunderstanding(world: World, child: Entity, beverage: Beverage, vessel: Vessel) -> None:
    child.attrs["misread"] = beverage.id
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} mistook the {beverage.label} for a kind wizard's drink, "
        f"because the bottle was clear and the smell seemed gentle."
    )
    world.say(
        f'"Look," {child.id} said, "a shining amber potion in a glass bottle!"'
    )


def warn(world: World, adult: Entity, child: Entity, beverage: Beverage, vessel: Vessel) -> None:
    pred = predict(world, beverage)
    adult.memes["clarified"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{adult.id} set down the broom and said, "{child.id}, that is not a potion. '
        f'It is {beverage.label}, and it is only for grown-ups."'
    )
    world.say(
        f'"It must stay closed in {vessel.label} where little hands cannot reach it, '
        f'and it is not safe to taste by mistake."'
    )


def resolve(world: World, adult: Entity, child: Entity, response: Response) -> None:
    if not sense_gate(response):
        raise StoryError(explain_response(response))
    adult.memes["warmth"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{adult.id} smiled gently and {response.text}."
    )
    world.say(
        f"{child.id}'s cheeks went pink with relief, and the bottle stayed sealed."
    )


def ending(world: World, child: Entity, adult: Entity, vessel: Vessel) -> None:
    world.say(
        f"After that, {child.id} watched the little bottle rest safely on the shelf, "
        f"and {adult.id} tied the stopper tight again."
    )
    world.say(
        f"The cottage was quiet, the fire was warm, and the only magic in the room "
        f"was the safe kind: a closed bottle, a clear warning, and a child who had learned."
    )


def tell(beverage: Beverage, vessel: Vessel, response: Response,
         child_name: str = "Mila", child_gender: str = "girl",
         adult_name: str = "Grandma", adult_gender: str = "woman",
         child_age: int = 5) -> World:
    if not is_reasonable(beverage, vessel):
        raise StoryError(explain_rejection(beverage, vessel))
    if child_age < SAFE_MIN_AGE:
        raise StoryError("(No story: the child is too young for this misunderstanding tale.)")

    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", attrs={"age": child_age}))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender,
                             role="adult"))
    bottle = world.add(Entity(id="bottle", kind="thing", type="bottle", label=vessel.label))
    bottle.meters["opened"] = 0.0

    scene(world, child, adult, beverage, vessel)
    world.para()
    misunderstanding(world, child, beverage, vessel)
    warn(world, adult, child, beverage, vessel)
    world.para()
    resolve(world, adult, child, response)
    ending(world, child, adult, vessel)

    world.facts.update(
        child=child, adult=adult, bottle=bottle, beverage=beverage, vessel=vessel,
        response=response, outcome="clarified", child_age=child_age,
    )
    return world


@dataclass
class StoryParams:
    beverage: str
    vessel: str
    response: str
    child_name: str = "Mila"
    child_gender: str = "girl"
    adult_name: str = "Grandma"
    adult_gender: str = "woman"
    child_age: int = 5
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


BEVERAGES = {
    "whiskey": Beverage(
        id="whiskey",
        label="whiskey",
        phrase="a bottle of whiskey",
        where="on the high shelf",
        age_min=21,
        senses=3,
        tags={"whiskey", "grownup", "drink"},
    ),
}

VESSELS = {
    "crystal_bottle": Vessel(
        id="crystal_bottle",
        label="crystal bottle",
        phrase="a clear crystal bottle",
        material="glass",
        clear=True,
        closable=True,
        sweet_smell=False,
        tags={"bottle", "clear"},
    ),
    "ruby_flask": Vessel(
        id="ruby_flask",
        label="ruby flask",
        phrase="a ruby flask with a stopper",
        material="glass",
        clear=False,
        closable=True,
        sweet_smell=True,
        tags={"bottle", "stopper"},
    ),
}

RESPONSES = {
    "clarify": Response(
        id="clarify",
        sense=3,
        text="pointed to the label, closed the stopper, and explained that whiskey is a grown-up drink",
        fail="could not untangle the confusion",
        qa_text="pointed to the label, closed the stopper, and explained that whiskey is a grown-up drink",
        tags={"clarify", "grownup"},
    ),
    "wrap_and_lock": Response(
        id="wrap_and_lock",
        sense=2,
        text="wrapped the bottle in a cloth, set it high on the shelf, and told the child not to touch it",
        fail="wrapped the bottle, but the child was still uncertain",
        qa_text="wrapped the bottle in cloth, set it high on the shelf, and kept it out of reach",
        tags={"safe", "high_shelf"},
    ),
}

CHILD_NAMES = ["Mila", "Pip", "Nora", "Hugo", "Elsie", "Theo"]
ADULT_NAMES = ["Grandma", "Grandpa", "Aunt Lark", "Uncle Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for b in BEVERAGES:
        for v in VESSELS:
            if is_reasonable(BEVERAGES[b], VESSELS[v]):
                for r in RESPONSES:
                    if RESPONSES[r].sense >= SENSE_MIN:
                        combos.append((b, v, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about a whiskey misunderstanding.")
    ap.add_argument("--beverage", choices=BEVERAGES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--adult-name")
    ap.add_argument("--child-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--adult-gender", choices=["woman", "man", "girl", "boy"])
    ap.add_argument("--child-age", type=int)
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
    if args.beverage and args.vessel and not is_reasonable(BEVERAGES[args.beverage], VESSELS[args.vessel]):
        raise StoryError(explain_rejection(BEVERAGES[args.beverage], VESSELS[args.vessel]))
    if args.response and not sense_gate(RESPONSES[args.response]):
        raise StoryError(explain_response(RESPONSES[args.response]))
    combos = [c for c in valid_combos()
              if (args.beverage is None or c[0] == args.beverage)
              and (args.vessel is None or c[1] == args.vessel)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    beverage, vessel, response = rng.choice(sorted(combos))
    return StoryParams(
        beverage=beverage,
        vessel=vessel,
        response=response,
        child_name=args.child_name or rng.choice(CHILD_NAMES),
        child_gender=args.child_gender or rng.choice(["girl", "boy"]),
        adult_name=args.adult_name or rng.choice(ADULT_NAMES),
        adult_gender=args.adult_gender or rng.choice(["woman", "man"]),
        child_age=args.child_age if args.child_age is not None else rng.randint(4, 7),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy-tale story for a child that includes the word "whiskey" and a misunderstanding about what it is.',
        f"Tell a gentle fairy-tale story where {f['child'].id} mistakes whiskey for a potion, and {f['adult'].id} clears up the confusion.",
        "Write a tiny story about a clear bottle, a strange smell, and a grown-up who explains that whiskey is not for children.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, adult, bev, vessel = f["child"], f["adult"], f["beverage"], f["vessel"]
    return [
        (
            "What did the child think the whiskey was?",
            f"{child.id} thought the whiskey was a potion because the bottle looked magical and the smell seemed sweet."
            f" The adult then explained that it was really a grown-up drink."
        ),
        (
            "Why did the adult stop the child?",
            f"The adult stopped {child.id} because whiskey is only for grown-ups and should stay sealed."
            f" That kept the child safe and prevented the misunderstanding from turning into a mistake."
        ),
        (
            "How did the story end?",
            f"It ended with the bottle closed on the shelf and the child feeling relieved."
            f" The cottage stayed calm, and the fairy-tale confusion was cleared away."
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is whiskey?", "Whiskey is a strong grown-up drink. Children should never taste it."),
        ("Why should a bottle be kept closed?", "A closed bottle helps keep its contents safe and stops curious hands from reaching in."),
        ("What should you do if you are not sure what something is?", "Ask a grown-up before touching or tasting it."),
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(beverage="whiskey", vessel="crystal_bottle", response="clarify", child_name="Mila", child_gender="girl", adult_name="Grandma", adult_gender="woman", child_age=5),
    StoryParams(beverage="whiskey", vessel="ruby_flask", response="wrap_and_lock", child_name="Theo", child_gender="boy", adult_name="Aunt Lark", adult_gender="woman", child_age=6),
]


ASP_RULES = r"""
valid(B,V,R) :- beverage(B), vessel(V), response(R), clear(V), closable(V), whiskey(B), sense_ok(R).
"""


def asp_facts() -> str:
    import asp
    parts = []
    for bid in BEVERAGES:
        parts.append(asp.fact("beverage", bid))
        if bid == "whiskey":
            parts.append(asp.fact("whiskey", bid))
    for vid, v in VESSELS.items():
        parts.append(asp.fact("vessel", vid))
        if v.clear:
            parts.append(asp.fact("clear", vid))
        if v.closable:
            parts.append(asp.fact("closable", vid))
    for rid, r in RESPONSES.items():
        parts.append(asp.fact("response", rid))
        if r.sense >= SENSE_MIN:
            parts.append(asp.fact("sense_ok", rid))
    return "\n".join(parts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            beverage=None, vessel=None, response=None, child_name=None, adult_name=None,
            child_gender=None, adult_gender=None, child_age=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.beverage not in BEVERAGES:
        raise StoryError("(Invalid beverage.)")
    if params.vessel not in VESSELS:
        raise StoryError("(Invalid vessel.)")
    if params.response not in RESPONSES:
        raise StoryError("(Invalid response.)")
    world = tell(
        BEVERAGES[params.beverage],
        VESSELS[params.vessel],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
        child_age=params.child_age,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible whiskey story combinations:")
        for b, v, r in asp_valid_combos():
            print(f"  {b} {v} {r}")
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
            header = f"### {p.child_name}: whiskey misunderstanding"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
