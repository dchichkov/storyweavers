#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hundredth_gifted_humor_kindness_pirate_tale.py
===============================================================================

A small storyworld for a pirate tale with humor and kindness, built around a
child-friendly crew, a hundredth gift, and a comic-but-caring turn.

The core premise:
- A pirate crew has a tiny problem: they are preparing a hundredth gift for a
  shipmate, but the gift box is too plain, too quiet, or too small to feel
  special.
- A playful character tries a silly idea to make the gift more memorable.
- A kinder character spots a gentler, safer way to make the gift shine.
- The story turns on a practical fix: the crew adds a thoughtful, humorous touch
  without hurting anyone or ruining the surprise.

The story stays grounded in changing world state:
- gift box contents and decorations change
- characters gain joy, worry, relief, and pride
- the final image proves the gift was improved and shared

This script is standalone, uses only stdlib, and follows the Storyweavers
contract for state-driven narration, QA, and ASP parity.
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
SENSE_MIN = 2
BRAVERY_INIT = 5.0
KIND_TRAITS = {"kind", "gentle", "careful", "thoughtful"}


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
class Place:
    id: str
    scene: str
    detail: str
    hideout: str
    ship_name: str
    treasure_word: str
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
class Gift:
    id: str
    label: str
    phrase: str
    size: str
    humor: str
    kindness: str
    special: str
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
class Complication:
    id: str
    label: str
    action: str
    effect: str
    risky: bool
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
class Aid:
    id: str
    label: str
    action: str
    result: str
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


def _r_relief(world: World) -> list[str]:
    out = []
    if world.get("giftbox").meters["sparkle"] >= THRESHOLD and ("relief", "sparkle") not in world.fired:
        world.fired.add(("relief", "sparkle"))
        for eid in ("captain", "mate", "giftee"):
            world.get(eid).memes["joy"] += 1
            world.get(eid).memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def plausible_problem(complication: Complication, gift: Gift) -> bool:
    return complication.risky and gift.size in {"small", "tiny", "plain"}


def sensible_aid() -> list[Aid]:
    return [a for a in AIDS.values() if a.power >= SENSE_MIN]


def best_aid() -> Aid:
    return max(AIDS.values(), key=lambda a: a.power)


def outcome_of(params: "StoryParams") -> str:
    if params.kindness_first:
        return "kind"
    aid = AIDS[params.aid]
    return "sparkle" if aid.power >= COMPLICATIONS[params.complication].power else "mess"


def predict(world: World, gift_id: str, aid_id: str) -> dict:
    sim = world.copy()
    sim.get(gift_id).meters["sparkle"] += 1
    sim.get("giftbox").meters["sparkle"] += 1
    return {"sparkle": sim.get("giftbox").meters["sparkle"] >= THRESHOLD}


def setup(world: World, a: Entity, b: Entity, c: Entity, place: Place) -> None:
    for e in (a, b, c):
        e.memes["joy"] += 1
    world.say(
        f"On a breezy day at {place.scene}, the crew turned the deck into {place.detail}. "
        f"{place.hideout} was where they kept their plans."
    )
    world.say(
        f'"Captain {a.id}, Mate {b.id}, and {c.id}!" {a.id} shouted. '
        f'"Tonight we make the {place.treasure_word} for the hundredth gift!"'
    )


def problem(world: World, a: Entity, gift: Gift, comp: Complication) -> None:
    a.memes["worry"] += 1
    world.say(
        f"But the little gift box looked {gift.size} and plain. {a.id} rubbed "
        f"{a.pronoun('possessive')} chin. \"I know a funny way to make it bigger!\""
    )
    world.say(f"{a.id} wanted to {comp.action}, which would {comp.effect}.")


def warn(world: World, b: Entity, a: Entity, comp: Complication, gift: Gift) -> None:
    b.memes["care"] += 1
    world.say(
        f"{b.id} lifted an eyebrow. \"That sounds funny,\" {b.pronoun()} said, "
        f"\"but it might {comp.effect} instead of making the gift special.\""
    )
    world.say(
        f"Then {b.id} pointed to the {gift.label} and smiled. "
        f"\"We can do something kind and silly at the same time.\""
    )


def do_silly(world: World, a: Entity, comp: Complication) -> None:
    a.memes["bravery"] += 1
    world.say(f"{a.id} tried anyway, and the whole crew held its breath.")
    world.say(f"{a.id} did it just a little bit {comp.action}.")


def do_kind(world: World, b: Entity, c: Entity, gift: Gift) -> None:
    b.memes["kindness"] += 1
    c.memes["kindness"] += 1
    world.get("giftbox").meters["sparkle"] += 1
    world.get("giftbox").memes["pride"] += 1
    world.say(
        f"{b.id} and {c.id} chose the gentle fix. They added a bright ribbon, "
        f"a little joke tag, and one careful bow."
    )
    world.say(
        f"The {gift.label} still looked ready to laugh, but now it looked thoughtful too."
    )
    propagate(world, narrate=False)


def ending(world: World, a: Entity, b: Entity, c: Entity, gift: Gift, place: Place) -> None:
    world.say(
        f"When the hundredth gift was opened, everyone laughed at the joke tag and "
        f"then smiled at how kind the wrapping was."
    )
    world.say(
        f"{a.id} grinned, {b.id} nodded, and {c.id} held up the {gift.label}. "
        f"On the deck at {place.hideout}, the little package sparkled like treasure."
    )


def rescue(world: World, comp: Complication, aid: Aid) -> None:
    if aid.power < comp.power:
        world.say(f"The idea fizzled a bit, but the crew fixed it before it caused trouble.")
    else:
        world.say(f"The plan worked, and the tidy little surprise stayed safe.")


def tell(place: Place, gift: Gift, comp: Complication, aid: Aid,
         captain: str = "Ruby", mate: str = "Ned", giftee: str = "Mina") -> World:
    world = World()
    a = world.add(Entity(id=captain, kind="character", type="girl", role="captain"))
    b = world.add(Entity(id=mate, kind="character", type="boy", role="mate"))
    c = world.add(Entity(id=giftee, kind="character", type="girl", role="giftee"))
    box = world.add(Entity(id="giftbox", type="thing", label="gift box"))
    box.meters["sparkle"] = 0.0

    setup(world, a, b, c, place)
    world.para()
    problem(world, a, gift, comp)
    warn(world, b, a, comp, gift)

    if comp.id == "kind_only":
        do_kind(world, b, c, gift)
    else:
        do_silly(world, a, comp)
        if aid.power >= comp.power:
            world.para()
            do_kind(world, b, c, gift)
            rescue(world, comp, aid)
        else:
            world.para()
            world.say(
                f"The deck got a little messy, so {b.id} quickly helped straighten "
                f"everything out with a calm laugh and a broom."
            )
            do_kind(world, b, c, gift)

    world.para()
    ending(world, a, b, c, gift, place)
    world.facts.update(
        captain=a, mate=b, giftee=c, place=place, gift=gift, complication=comp,
        aid=aid, sparkle=world.get("giftbox").meters["sparkle"] >= THRESHOLD
    )
    return world


@dataclass
class StoryParams:
    place: str
    gift: str
    complication: str
    aid: str
    captain: str
    mate: str
    giftee: str
    kindness_first: bool = False
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
    "dock": Place("dock", "the sunny dock", "a tiny lantern-lit lookout", "the old crate nook", "ship's nook", "gift"),
    "cove": Place("cove", "a sheltered cove", "a splashy line of sea-chest stories", "the rope-shadow corner", "treasure shelf", "gift"),
    "deck": Place("deck", "the wobbly deck", "a ribbon-trimmed map corner", "the sail-shadow hatch", "prize chest", "gift"),
}

GIFTS = {
    "shell": Gift("shell", "shell", "a shiny shell", "small", "make it giggle", "make it kind", "a shell with a smile"),
    "book": Gift("book", "book", "a little story book", "plain", "tickle the picture", "wrap it with care", "a book with a bow"),
    "cup": Gift("cup", "cup", "a tiny cup", "tiny", "draw a mustache on it", "add a warm note", "a cup with a joke tag"),
}

COMPLICATIONS = {
    "loudjoke": Complication("loudjoke", "loud joke", "shout a sea-shanty in the gift box", "wake the whole ship", True, 2),
    "confetti": Complication("confetti", "confetti burst", "blast confetti everywhere", "cover the deck in sparkly bits", True, 2),
    "gigglefit": Complication("gigglefit", "giggle fit", "laugh so hard they wobble", "spill the ribbon pile", False, 1),
}

AIDS = {
    "ribbon": Aid("ribbon", "ribbon", "tie a bright ribbon", "make it look festive", 2),
    "note": Aid("note", "kind note", "write a kind note", "make it feel thoughtful", 3),
    "sticker": Aid("sticker", "smiley sticker", "add a smiley sticker", "make it feel cheerful", 2),
    "kind_only": Aid("kind_only", "kind hands", "use kind hands", "make the box feel safe", 3),
}

CURATED = [
    StoryParams(place="dock", gift="shell", complication="loudjoke", aid="note",
                captain="Ruby", mate="Ned", giftee="Mina"),
    StoryParams(place="cove", gift="book", complication="confetti", aid="ribbon",
                captain="Ada", mate="Bo", giftee="Lina"),
    StoryParams(place="deck", gift="cup", complication="gigglefit", aid="sticker",
                captain="Ivy", mate="Finn", giftee="Milo", kindness_first=True),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for g in GIFTS:
            for c in COMPLICATIONS:
                if plausible_problem(COMPLICATIONS[c], GIFTS[g]):
                    combos.append((p, g, c))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a child that includes the words "hundredth" and "gifted".',
        f"Tell a funny and kind story about {f['captain'].id}, {f['mate'].id}, and "
        f"{f['giftee'].id} on {f['place'].scene}.",
        f"Write a short pirate story where a silly gift idea gets replaced by a kinder one.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    gift: Gift = f["gift"]
    comp: Complication = f["complication"]
    aid: Aid = f["aid"]
    qas = [
        QAItem(
            question="What were the pirates making?",
            answer=f"They were making the hundredth gift for {f['giftee'].id}. It was meant to be a small surprise, so they could make it feel special without making a fuss."
        ),
        QAItem(
            question="Why did one pirate worry about the plan?",
            answer=f"{f['mate'].id} worried because {f['captain'].id}'s idea could {comp.effect}. That would have made the gift messier instead of kinder."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They added {aid.label}, a bright ribbon, and a careful bow. That made the {gift.label} look funny and loving at the same time."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with laughter, a safe deck, and a sparkling little package. The hundredth gift looked playful, but it was still gentle and neat."
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a pirate crew?", "A pirate crew is a group of sailors who work together on a ship. In a story, they can be silly, brave, or kind as they help each other."),
        QAItem("What does kind mean?", "Kind means caring about other people and trying to help them feel safe and happy. Kind actions often make a problem smaller instead of bigger."),
        QAItem("What is a gift?", "A gift is something you give to someone without asking for payment. Gifts can be small and still feel very special."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
sparkle_box :- giftbox, sparkle(G), G >= 1.
valid(Place, Gift, Comp) :- place(Place), gift(Gift), complication(Comp), risky(Comp), small(Gift).
kind_ending :- aid(A), aid_power(A,P), P >= 2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
        if GIFTS[gid].size in {"small", "tiny", "plain"}:
            lines.append(asp.fact("small", gid))
    for cid, c in COMPLICATIONS.items():
        lines.append(asp.fact("complication", cid))
        if c.risky:
            lines.append(asp.fact("risky", cid))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        lines.append(asp.fact("aid_power", aid, a.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, gift=None, complication=None, aid=None,
            captain=None, mate=None, giftee=None, kindness_first=False
        ), random.Random(7)))
        _ = sample.story
    except Exception:
        rc = 1
        print("MISMATCH: normal generate smoke test failed.")
        traceback.print_exc()
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate kindness tale with humor and a hundredth gift.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--complication", choices=COMPLICATIONS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--captain")
    ap.add_argument("--mate")
    ap.add_argument("--giftee")
    ap.add_argument("--kindness-first", action="store_true")
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
              if (args.place is None or c[0] == args.place)
              and (args.gift is None or c[1] == args.gift)
              and (args.complication is None or c[2] == args.complication)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift, comp = rng.choice(sorted(combos))
    aid = args.aid or rng.choice(sorted(AIDS))
    return StoryParams(
        place=place, gift=gift, complication=comp, aid=aid,
        captain=args.captain or rng.choice(["Ruby", "Ada", "Ivy", "Mina"]),
        mate=args.mate or rng.choice(["Ned", "Bo", "Finn", "Bea"]),
        giftee=args.giftee or rng.choice(["Milo", "Lina", "Tess", "Jory"]),
        kindness_first=args.kindness_first,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.gift not in GIFTS or params.complication not in COMPLICATIONS or params.aid not in AIDS:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], GIFTS[params.gift], COMPLICATIONS[params.complication], AIDS[params.aid],
                 captain=params.captain, mate=params.mate, giftee=params.giftee)
    return StorySample(
        params=params,
        story=world.render(),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
