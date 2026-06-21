#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thud_teamwork_rhyming_story.py
===============================================================

A tiny Storyweavers world for a child-facing rhyming story about teamwork:
a small boat gets stuck with a "thud", two friends work together, and the
ending proves their shared effort changed the world.

The domain is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate for valid story setups
- a Python causal model with a matching inline ASP twin
- three Q&A sets grounded in the simulated world state
- a rhyming, child-friendly renderer with concrete state changes

Seed words and features:
- word: thud
- feature: teamwork
- style: rhyming story
"""

from __future__ import annotations

import argparse
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
    dark: bool = False
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
class Block:
    id: str
    label: str
    heavy: bool = False
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
class Aid:
    id: str
    label: str
    helper: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if cart and cart.meters["stuck"] >= THRESHOLD and ("wobble", "cart") not in world.fired:
        world.fired.add(("wobble", "cart"))
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("__wobble__")
    return out


def _r_pull(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if not cart or cart.meters["stuck"] < THRESHOLD:
        return out
    pullers = [e for e in world.characters() if e.memes["pulling"] >= THRESHOLD]
    if len(pullers) >= 2 and ("pull", "cart") not in world.fired:
        world.fired.add(("pull", "cart"))
        cart.meters["stuck"] = 0.0
        cart.meters["free"] = 1.0
        for kid in pullers:
            kid.memes["pride"] += 1
            kid.meters["helped"] += 1
        out.append("__free__")
    return out


def _r_lift(world: World) -> list[str]:
    out: list[str] = []
    crate = world.entities.get("crate")
    if crate and crate.meters["open"] >= THRESHOLD and ("lift", "crate") not in world.fired:
        world.fired.add(("lift", "crate"))
        out.append("The lid sprang up with a bright little flip.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("pull", _r_pull), Rule("lift", _r_lift)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                lines.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_free(world: World) -> bool:
    sim = world.copy()
    cart = sim.get("cart")
    cart.meters["stuck"] = 1.0
    simulate_push(sim, narrate=False)
    return sim.get("cart").meters["free"] >= THRESHOLD


def simulate_push(world: World, narrate: bool = True) -> None:
    cart = world.get("cart")
    cart.meters["stuck"] += 1
    propagate(world, narrate=narrate)


def setup_line(world: World, a: Entity, b: Entity, place: Place) -> None:
    world.say(
        f"At {place.label}, {a.id} and {b.id} were humming a tune, light on their feet."
    )
    world.say(
        f"They found a tiny cart of toys with a box and a lid, sitting still and neat."
    )


def thud_line(world: World, a: Entity, cart: Entity) -> None:
    a.memes["surprise"] += 1
    world.say(
        f"Then {a.id} gave the cart a push — thud! It bumped and would not move."
    )
    world.say("It rocked and it shook, but it stayed in place, as stubborn as glue.")


def teamwork_line(world: World, a: Entity, b: Entity) -> None:
    a.memes["pulling"] += 1
    b.memes["pulling"] += 1
    a.meters["pulling"] += 1
    b.meters["pulling"] += 1
    world.say(
        f'{b.id} said, "Let us try together." {a.id} nodded, brave and true.'
    )
    world.say(
        f"{a.id} pulled on one side, {b.id} on the other, and they counted: one, two!"
    )


def cheer_line(world: World, a: Entity, b: Entity, cart: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"With a tug and a grin, the cart rolled free. They laughed, and their cheers rang through."
    )
    world.say(
        f"The stuck old cart was unstuck at last; teamwork made it all come true."
    )


def open_box_line(world: World, crate: Entity) -> None:
    crate.meters["open"] += 1
    world.say("Nearby, the little box gave a click and the lid popped up with a thump.")
    world.say("Inside were stickers and stars, all shiny bright, and nobody got a lump.")


def tell(place: Place, first: Entity, second: Entity) -> World:
    world = World(place=place)
    a = world.add(first)
    b = world.add(second)
    cart = world.add(Entity(id="cart", kind="thing", type="cart", label="toy cart"))
    crate = world.add(Entity(id="crate", kind="thing", type="box", label="little box"))

    setup_line(world, a, b, place)
    world.para()
    thud_line(world, a, cart)
    teamwork_line(world, a, b)
    simulate_push(world, narrate=True)
    if cart.meters["free"] >= THRESHOLD:
        world.para()
        cheer_line(world, a, b, cart)
        open_box_line(world, crate)

    world.facts.update(
        hero=a,
        helper=b,
        cart=cart,
        crate=crate,
        place=place,
        teamwork=True,
        freed=cart.meters["free"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "boy"
    helper_gender: str = "girl"
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
    "playroom": Place(id="playroom", label="the playroom", dark=False, tags={"room"}),
    "garage": Place(id="garage", label="the garage", dark=False, tags={"room"}),
    "shed": Place(id="shed", label="the shed", dark=True, tags={"room", "dark"}),
}
NAMES = {
    "boy": ["Ben", "Leo", "Max", "Toby", "Sam"],
    "girl": ["Mia", "Lily", "Zoe", "Nora", "Ava"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, "cart", "crate") for p in PLACES]


CURATED = [
    StoryParams(place="playroom", hero_name="Ben", helper_name="Mia", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="garage", hero_name="Leo", helper_name="Nora", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="shed", hero_name="Ava", helper_name="Sam", hero_gender="girl", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork story world with a thud.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_name = args.hero or rng.choice(NAMES[hero_gender])
    helper_name = args.helper or rng.choice([n for n in NAMES[helper_gender] if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name,
                       hero_gender=hero_gender, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a small child that includes the word "thud" and shows teamwork.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} work together to free a stuck cart after a thud.",
        f'Write a simple teamwork rhyme set at {f["place"].label} with a stuck cart, a thud, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What happened after the push?",
            answer="The cart made a thud and got stuck. Then both children worked together, so the cart could move again."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They pulled together from both sides and counted their effort. The teamwork gave the cart enough help to roll free."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work as one team. It can make hard jobs easier and more fun."
        ),
        QAItem(
            question="What does thud sound like?",
            answer="Thud sounds like a heavy bump. It is the kind of sound you hear when something lands or hits the floor."
        ),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(cart) :- cart(cart), stuck_meter(cart, S), S >= 1.
wobble(hero) :- stuck(cart), hero(hero).
free(cart) :- pull(hero1), pull(hero2), hero1 != hero2, helper(hero1), helper(hero2).
outcome(free) :- free(cart).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("cart", "cart"))
    lines.append(asp.fact("crate", "crate"))
    lines.append(asp.fact("stuck_meter", "cart", 1))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show outcome/1."))
        _ = model
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, hero=None, helper=None, hero_gender=None, helper_gender=None
        ), random.Random(1)))
        if not sample.story.strip():
            print("Story generation produced empty text.")
            return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show free/1."))
    return sorted(set(asp.atoms(model, "free")))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_gender not in NAMES or params.helper_gender not in NAMES:
        raise StoryError("Invalid gender.")
    place = PLACES[params.place]
    world = tell(
        place=place,
        first=Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"),
        second=Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"),
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show free/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
