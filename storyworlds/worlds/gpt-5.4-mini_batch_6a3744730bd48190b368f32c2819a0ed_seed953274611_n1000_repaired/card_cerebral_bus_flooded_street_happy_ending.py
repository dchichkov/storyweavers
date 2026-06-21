#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/card_cerebral_bus_flooded_street_happy_ending.py
================================================================================

A tiny storyworld for a flooded street, a bus, a special card, and a careful
cerebral helper who helps turn a soggy problem into a happy ending.

The style goal is a gentle rhyming story: short, child-facing lines, clear
cause and effect, and an ending image that proves what changed.
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
RHYME_ENDINGS = ("light", "bright", "sight", "night", "flight")


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
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class Card:
    id: str
    label: str
    phrase: str
    shine: str
    rhyme: str
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
class Bus:
    id: str
    label: str
    phrase: str
    size: str
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
class Street:
    id: str
    label: str
    flooded: bool = True
    water: str = "knee-deep water"
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
class Helper:
    id: str
    label: str
    kind: str
    card_kind: str
    rhyme: str
    sense: int
    power: int
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
    card: str
    bus: str
    helper: str
    street: str = "flooded street"
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


def _r_wet_bus(world: World) -> list[str]:
    out: list[str] = []
    street = world.get("street")
    bus = world.get("bus")
    if street.meters["flood"] < THRESHOLD or bus.meters["stuck"] < THRESHOLD:
        return out
    sig = ("wet_bus",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bus.meters["soggy"] += 1
    for ent in list(world.entities.values()):
        if ent.role == "helper":
            ent.memes["concern"] += 1
    out.append("__splash__")
    return out


CAUSAL_RULES = [Rule("wet_bus", "physical", _r_wet_bus)]


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


def can_wear_card(card: Card, helper: Helper) -> bool:
    return card.id == helper.card_kind and helper.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for card_id, card in CARDS.items():
        for bus_id in BUSES:
            for helper_id, helper in HELPERS.items():
                if can_wear_card(card, helper):
                    combos.append((card_id, bus_id, helper_id))
    return combos


def flood_risk(street: Street, bus: Bus) -> bool:
    return street.flooded and bus.id == "bus"


def can_help(helper: Helper, bus: Bus) -> bool:
    return helper.power >= 1 and bus.id == "bus"


def should_clear(helper: Helper) -> bool:
    return helper.sense >= 2


def tell(card: Card, bus: Bus, helper: Helper, street: Street) -> World:
    world = World()
    hero = world.add(Entity(id="Mila", kind="character", type="girl", role="child"))
    guide = world.add(Entity(id=helper.id, kind="character", type="person", label=helper.label, role="helper"))
    world.add(Entity(id="street", type="place", label=street.label))
    bus_ent = world.add(Entity(id="bus", type="vehicle", label=bus.label))
    card_ent = world.add(Entity(id="card", type="thing", label=card.label))
    street_ent = world.get("street")
    street_ent.meters["flood"] += 1
    bus_ent.meters["stuck"] += 1
    hero.memes["worry"] += 1

    world.say(
        f"On the flooded street, where water went swish and a bus sat still, "
        f"Mila held a card with a shiny swirled twirl."
    )
    world.say(
        f"{hero.id} said, 'This card feels calm in my hand, "
        f"like a little bright light on the wet street land.'"
    )
    world.para()
    world.say(
        f"The bus could not roll, for the water was deep; "
        f"it rocked in the street like it had sunk in its sleep."
    )
    guide.memes["care"] = 1
    world.say(
        f"{guide.label.capitalize()} studied the water with thoughtful eyes. "
        f"'Let's read the card, and then make a plan with no surprise.'"
    )

    if not can_wear_card(card, helper):
        raise StoryError("The helper cannot use this card in a sensible way.")

    world.para()
    world.say(
        f"{guide.label.capitalize()} tucked the card close and tapped the bus's side. "
        f"'We can help it be safe, and we can still take pride.'"
    )
    if flood_risk(street, bus):
        bus_ent.meters["stuck"] += 1
        bus_ent.memes["fear"] += 1
        propagate(world, narrate=False)

    world.say(
        f"They lifted the bus sign high, so the driver could see, "
        f"then guided a smaller route where the water could flee."
    )
    bus_ent.meters["stuck"] = 0
    bus_ent.memes["calm"] += 1
    street_ent.meters["flood"] = 0
    hero.memes["joy"] += 1
    guide.memes["joy"] += 1

    world.para()
    world.say(
        f"The bus rolled on at last, with a hum and a cheer, "
        f"and the flooded street gleamed like a mirror so clear."
    )
    world.say(
        f"Mila waved her card in the warm morning light, "
        f"and the cerebral helper smiled: the day ended right."
    )

    world.facts.update(
        card=card,
        bus=bus,
        helper=helper,
        street=street,
        hero=hero,
        guide=guide,
        card_used=True,
        bus_moved=True,
        flood_cleared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a rhyming story for a young child that includes the words "card", '
        '"cerebral", and "bus".',
        'Tell a happy-ending story set on a flooded street, where a child and a '
        'cerebral helper use a card to help a bus.',
        'Write a short rhyming rescue story about a flooded street, a stuck bus, '
        'and a bright card that helps everyone move safely.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    bus = world.facts["bus"]
    street = world.facts["street"]
    return [
        (
            "What kind of street was in the story?",
            f"It was a flooded street, so water covered the road and made travel hard. "
            f"That is why the bus needed careful help.",
        ),
        (
            "Who helped with the problem?",
            f"Mila and the cerebral helper worked together to guide the bus. "
            f"They used a smart plan instead of rushing into the water.",
        ),
        (
            "What changed by the end?",
            f"The bus was able to move again, and the flood was cleared from the street. "
            f"The ending is happy because the road became safe and bright again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a bus?",
            "A bus is a big vehicle that carries people from place to place. "
            "It is useful for trips when many riders go together.",
        ),
        (
            "What does flooded mean?",
            "Flooded means covered with too much water. A flooded street can be hard to cross safely.",
        ),
        (
            "What does cerebral mean?",
            "Cerebral means thoughtful or brainy. It suggests a person who uses careful ideas and smart planning.",
        ),
        (
            "What is a card?",
            "A card is a small flat piece of paper or cardboard. It can hold a note, a picture, or an important message.",
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
    lines.append("== (3) World knowledge questions ==")
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
    return "\n".join(lines)


CARDS = {
    "card": Card(id="card", label="a bright card", phrase="a bright card", shine="bright", rhyme="light", tags={"card"}),
    "ticket": Card(id="ticket", label="a little ticket card", phrase="a little ticket card", shine="neat", rhyme="seat", tags={"card"}),
}

BUSES = {
    "bus": Bus(id="bus", label="the bus", phrase="the bus", size="big", tags={"bus"}),
}

HELPERS = {
    "cerebral": Helper(id="cerebral", label="the cerebral helper", kind="helper", card_kind="card", rhyme="bright", sense=3, power=3, tags={"cerebral"}),
    "gentle": Helper(id="gentle", label="the gentle helper", kind="helper", card_kind="ticket", rhyme="light", sense=2, power=2, tags={"cerebral"}),
}

STREETS = {
    "flooded street": Street(id="flooded street", label="the flooded street", flooded=True, water="knee-deep water", tags={"flooded"}),
}

@dataclass
class StoryParams:
    card: str
    bus: str
    helper: str
    street: str = "flooded street"
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


CURATED = [
    StoryParams(card="card", bus="bus", helper="cerebral", street="flooded street"),
    StoryParams(card="ticket", bus="bus", helper="gentle", street="flooded street"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CARDS.items():
        lines.append(asp.fact("card", cid))
        if c.tags:
            for t in c.tags:
                lines.append(asp.fact("tagged", cid, t))
    for bid in BUSES:
        lines.append(asp.fact("bus", bid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("card_kind", hid, h.card_kind))
        lines.append(asp.fact("sense", hid, h.sense))
        lines.append(asp.fact("power", hid, h.power))
    for sid, s in STREETS.items():
        lines.append(asp.fact("street", sid))
        if s.flooded:
            lines.append(asp.fact("flooded", sid))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(H) :- helper(H), sense(H,S), S >= 2.
valid(C,B,H) :- card(C), bus(B), helper(H), sensible(H), card_kind(H,C).
outcome(happy) :- valid(_,_,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP parity.")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal story generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"FAILED: generate() smoke test crashed: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming flooded-street storyworld.")
    ap.add_argument("--card", choices=CARDS)
    ap.add_argument("--bus", choices=BUSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--street", choices=STREETS)
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
    card = args.card or rng.choice(list(CARDS))
    bus = args.bus or rng.choice(list(BUSES))
    helper = args.helper or rng.choice(list(HELPERS))
    street = args.street or "flooded street"
    if card not in CARDS or bus not in BUSES or helper not in HELPERS or street not in STREETS:
        raise StoryError("Unknown parameter choice.")
    if not can_wear_card(CARDS[card], HELPERS[helper]):
        raise StoryError("That helper cannot sensibly use that card.")
    return StoryParams(card=card, bus=bus, helper=helper, street=street)


def generate(params: StoryParams) -> StorySample:
    if params.card not in CARDS or params.bus not in BUSES or params.helper not in HELPERS or params.street not in STREETS:
        raise StoryError("Invalid StoryParams.")
    world = tell(CARDS[params.card], BUSES[params.bus], HELPERS[params.helper], STREETS[params.street])
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
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
