#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/coaster_hideous_dialogue_inner_monologue_tall_tale.py
=====================================================================================

A standalone story world for a tall-tale-style, child-facing story about a
mischievous mug, a prized table, and a saving coaster. The domain is small and
constraint-checked: a hideous stain can threaten a beloved surface, a child may
be tempted to ignore the coaster, a wise helper predicts the mess, and the story
ends with a safer habit and a bright image of what changed.

Seed words / features:
- Words: coaster, hideous
- Features: Dialogue, Inner Monologue
- Style: Tall Tale
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    delicate: bool = False
    warm: bool = False
    holds_drink: bool = False
    coaster: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa",
                "mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    surface: str
    mood: str
    props: str
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
class Drink:
    id: str
    label: str
    phrase: str
    hot: bool
    sticky: bool
    splash: str
    stain: str
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
class Coaster:
    id: str
    label: str
    phrase: str
    remedy: str
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
    power: int
    text: str
    fail: str
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


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["spill"] < THRESHOLD:
            continue
        sig = ("stain", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        table = world.entities.get("table")
        if table:
            table.meters["stained"] += 1
        for char in list(world.entities.values()):
            if char.kind == "character":
                char.memes["alarm"] += 1
        out.append("__stain__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("stain", "physical", _r_stain)]


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


def hazard_at_risk(drink: Drink, setting: Setting) -> bool:
    return drink.sticky and "table" in setting.props


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def stain_severity(drink: Drink, delay: int) -> int:
    return 1 + delay + (1 if drink.sticky else 0)


def is_managed(response: Response, drink: Drink, delay: int) -> bool:
    return response.power >= stain_severity(drink, delay)


def predict_stain(world: World, drink_id: str) -> dict:
    sim = world.copy()
    _spill(sim, sim.get(drink_id), narrate=False)
    return {
        "stained": sim.get("table").meters["stained"] >= THRESHOLD if "table" in sim.entities else False,
    }


def _spill(world: World, drink: Entity, narrate: bool = True) -> None:
    drink.meters["spill"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, setting: Setting, drink: Drink) -> None:
    child.memes["joy"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"On a day so wide it seemed to lean over the horizon, {child.id} and "
        f"{helper.id} sat in {setting.place}. {setting.props}"
    )
    world.say(
        f'The room felt as grand as a wagon ride across the sky, and the mug on '
        f'the table looked as if it had been poured by a thundercloud.'
    )


def setup_problem(world: World, child: Entity, drink: Drink, setting: Setting) -> None:
    world.say(
        f'The drink was {drink.phrase}, and it sat there {drink.splash} beside '
        f'the {setting.surface}.'
    )
    world.say(
        f'{child.id} stared at it and thought, "If that thing tips, it will make '
        f'a {drink.stain} mess as {drink.label_word if hasattr(drink, "label_word") else drink.label} as a swamp-monster."'
    )


def desire(world: World, child: Entity, drink: Drink) -> None:
    child.memes["wanting"] += 1
    world.say(
        f'{child.id} reached for the mug and said, "I can carry it myself, '
        f'promise!"'
    )
    world.say(
        f'Inside {child.id}\'s head, a tiny voice whispered, "Maybe I should get '
        f'the coaster first."'
    )


def warn(world: World, helper: Entity, child: Entity, setting: Setting, drink: Drink) -> None:
    pred = predict_stain(world, "mug")
    if not pred["stained"]:
        return
    helper.memes["warning"] += 1
    world.facts["predicted_stain"] = True
    world.say(
        f'"Easy now," {helper.id} said. "That table is as proud as a peacock, '
        f'and it will remember a stain forever. Put the coaster under {drink.label}."'
    )


def defy(world: World, child: Entity, drink: Drink) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"I know," {child.id} said, but {child.id} lifted the mug anyway, as bold '
        f'as a bucking bronco.'
    )


def spill(world: World, drink: Entity) -> None:
    _spill(world, drink)
    world.say(
        f'The mug wobbled once, twice, and then -- splash! -- a {drink.stain} '
        f'arc leapt toward the table like a jumping fish.'
    )


def alarm(world: World, helper: Entity, child: Entity) -> None:
    world.say(f'"Whoa!" {helper.id} shouted. "{child.id}, the table!"')


def rescue(world: World, helper: Entity, drink: Entity, response: Response) -> None:
    drink.meters["spill"] = 0.0
    world.get("table").meters["stained"] = 0.0
    world.say(
        f'Without losing a breath, {helper.id} {response.text.replace("{target}", drink.label)}.'
    )
    world.say(
        f'The mess stopped short, and the table shone again like a polished shield.'
    )


def lesson(world: World, helper: Entity, child: Entity, coaster: Coaster) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    helper.memes["love"] += 1
    world.say(
        f'"I\'m not angry," {helper.id} said, softer now. "I am glad you stopped and '
        f"called for help. A coaster keeps a drink from making a hideous ring."
    )
    world.say(
        f'{child.id} nodded and tucked the {coaster.label} under the mug, right where '
        f'it belonged.'
    )


def ending(world: World, child: Entity, helper: Entity, coaster: Coaster, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f'Then {child.id} set the mug down on the {coaster.label}. The room grew '
        f'quiet and bright, and the old table wore a neat little circle like a badge of honor.'
    )
    world.say(
        f'{helper.id} laughed. "{child.id}, that coaster was the smallest hero in the county!"'
    )
    world.say(
        f'And {child.id}, grinning as wide as a fence line at sunset, kept the mug steady '
        f"while the whole place stayed clean."
    )


def tell(setting: Setting, drink: Drink, coaster: Coaster, response: Response,
         child_name: str = "Mabel", child_gender: str = "girl",
         helper_name: str = "Gran", helper_gender: str = "grandmother",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    table = world.add(Entity(id="table", type="table", label="the table", delicate=True))
    mug = world.add(Entity(id="mug", type="mug", label=drink.label, holds_drink=True))
    coaster_ent = world.add(Entity(id="coaster", type="coaster", label=coaster.label, coaster=True))
    child.memes["curiosity"] = 1.0

    opening(world, child, helper, setting, drink)
    setup_problem(world, child, drink, setting)
    world.para()
    desire(world, child, drink)
    warn(world, helper, child, setting, drink)
    defy(world, child, drink)
    world.para()
    spill(world, mug)
    alarm(world, helper, child)
    if is_managed(response, drink, delay):
        rescue(world, helper, mug, response)
        lesson(world, helper, child, coaster)
        world.para()
        ending(world, child, helper, coaster, setting)
        outcome = "contained"
    else:
        world.say(
            f'The stain ran too fast for the chosen fix, and the table was left with a hideous mark.'
        )
        outcome = "failed"
    world.facts.update(child=child, helper=helper, table=table, mug=mug, coaster=coaster_ent,
                       setting=setting, drink=drink, response=response, outcome=outcome, delay=delay)
    return world


SETTINGS = {
    "front_porch": Setting(
        "front_porch", "the front porch", "wooden table", "windy", "the porch rail and the table",
        tags={"porch", "table"},
    ),
    "cabin": Setting(
        "cabin", "the little cabin", "wooden table", "cozy", "the lamp, the table, and the big window",
        tags={"cabin", "table"},
    ),
    "diner": Setting(
        "diner", "the tiny diner", "counter", "busy", "the counter and a row of stools",
        tags={"diner", "table"},
    ),
}

DRINKS = {
    "cocoa": Drink("cocoa", "cocoa", "a steaming mug of cocoa", True, True, "close to the edge", "hideous brown", tags={"drink", "hot"}),
    "syrup": Drink("syrup", "syrup", "a sticky mug of syrup water", False, True, "right by the lamp", "hideous sticky", tags={"drink", "sticky"}),
    "berry_juice": Drink("berry_juice", "berry juice", "a bright mug of berry juice", False, True, "nestled near the table lamp", "hideous purple", tags={"drink", "sticky"}),
}

COASTERS = {
    "wood": Coaster("wood", "coaster", "a flat wooden coaster", "keep the mug steady", tags={"coaster"}),
    "stone": Coaster("stone", "coaster", "a cool stone coaster", "steady the mug like a wagon wheel", tags={"coaster"}),
    "braided": Coaster("braided", "coaster", "a braided reed coaster", "catch drips before they spread", tags={"coaster"}),
}

RESPONSES = {
    "coaster": Response("coaster", 3, 3, "slid the coaster under the mug and steadied it", "tried to steady the mug, but the stain kept spreading", "slid the coaster under the mug and steadied it", tags={"coaster"}),
    "cloth": Response("cloth", 2, 2, "snatched up a dry cloth and blotted the spill before it spread", "blotted at the spill, but the stain had already bloomed", "snatched up a dry cloth and blotted the spill before it spread", tags={"cloth"}),
    "tray": Response("tray", 3, 4, "caught the mug on a tray and wiped the table dry", "used a tray, but the spill had already run wild", "caught the mug on a tray and wiped the table dry", tags={"tray"}),
}

NAMES = ["Mabel", "June", "Nell", "Ruby", "Benny", "Otis", "Penny", "Wes"]
TRAITS = ["steady", "curious", "spunky", "careful", "brave"]
TALL_TALE_FILLERS = [
    "It was so quiet you could hear a spoon dream.",
    "The wind had a voice like an old fiddle.",
    "Even the dust motes looked sleepy and surprised.",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for did, drink in DRINKS.items():
            if not hazard_at_risk(drink, setting):
                continue
            for cid in COASTERS:
                combos.append((sid, did, cid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    drink: str
    coaster: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    delay: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about a coaster, a hideous stain, dialogue, and an inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--coaster", choices=COASTERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def explain_rejection() -> str:
    return "(No story: this combination doesn't create a believable stain-and-coaster problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': sense={r.sense} < {SENSE_MIN}. Try: {better}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.drink is None or c[1] == args.drink)
              and (args.coaster is None or c[2] == args.coaster)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, drink, coaster = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["grandmother", "grandfather"])
    child_name = args.child_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(["Gran", "Grandpa"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, drink, coaster, response, child_name, child_gender, helper_name, helper_gender, trait, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child that includes the words "{f["drink"].label}" and "coaster".',
        f"Tell a funny, exaggerated story where {f['child'].id} nearly makes a hideous mess with {f['drink'].phrase}, then listens to {f['helper'].id} and uses a coaster.",
        f"Write a story with dialogue and an inner monologue about keeping a mug steady in {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, drink, coaster = f["child"], f["helper"], f["drink"], f["coaster"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who shared a very tricky mug and a small but mighty coaster."),
        ("What did the child want to do?",
         f"{child.id} wanted to carry the mug without using the coaster first. That was the risky choice because the drink was easy to spill."),
        ("What stopped the mess?",
         f"{helper.id} warned {child.pronoun('object')}, and then the coaster helped steady the mug. That kept the hideous stain from spreading."),
    ]
    if f["outcome"] == "contained":
        qa.append((
            "How did the story end?",
            f"It ended with the mug sitting safely on the coaster and the table staying clean. The child learned to use the coaster first."
        ))
        qa.append((
            "Why was the helper glad?",
            f"{helper.id} was glad because {child.id} listened and the table did not get a hideous ring. The small coaster saved a lot of fuss."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["drink"].tags) | set(world.facts["coaster"].tags)
    out = []
    if "coaster" in tags:
        out.append(("What is a coaster?",
                     "A coaster is a small pad or plate you put under a drink so the table does not get wet, sticky, or stained."))
    if "drink" in tags:
        out.append(("Why can a mug spill be messy?",
                     "A mug spill can spread across the table and make a sticky or stained mess. That is why people put cups on coasters or trays."))
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
        if e.coaster:
            bits.append("coaster=True")
        if e.delicate:
            bits.append("delicate=True")
        if e.holds_drink:
            bits.append("holds_drink=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def _tall_tale_phrase(setting: Setting) -> str:
    return random.choice(TALL_TALE_FILLERS)


def tell(setting: Setting, drink: Drink, coaster: Coaster, response: Response,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         trait: str, delay: int) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=[trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="table", type="table", label="the table", delicate=True))
    mug = world.add(Entity(id="mug", type="mug", label=drink.label, holds_drink=True))
    world.add(Entity(id="coaster", type="coaster", label=coaster.label, coaster=True))
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["drink"] = drink
    world.facts["coaster"] = coaster
    world.facts["setting"] = setting

    child.memes["pride"] = 1.0
    opening(world, child, helper, setting, drink)
    world.say(_tall_tale_phrase(setting))
    world.para()
    setup_problem(world, child, drink, setting)
    desire(world, child, drink)
    warn(world, helper, child, setting, drink)
    child.memes["defiance"] += 1
    world.say(
        f'{child.id} muttered, "I can do it quick as lightning." '
        f"Inside, {child.id} thought, 'Maybe quick is not the same as careful.'"
    )
    world.para()
    spill(world, mug)
    alarm(world, helper, child)
    if is_managed(response, drink, delay):
        rescue(world, helper, mug, response)
        lesson(world, helper, child, coaster)
        world.para()
        ending(world, child, helper, coaster, setting)
        outcome = "contained"
    else:
        world.say(
            f"The stain spread so wide it looked like a dark bootprint from a giant in a hurry."
        )
        outcome = "failed"

    world.facts["outcome"] = outcome
    world.facts["response"] = response
    world.facts["delay"] = delay
    return world


def valid_story_params() -> list[StoryParams]:
    out = []
    for s, d, c in valid_combos():
        out.append(StoryParams(s, d, c, "coaster", "Mabel", "girl", "Gran", "grandmother", "careful", 0))
    return out


CURATED = [
    StoryParams("cabin", "cocoa", "wood", "coaster", "Mabel", "girl", "Gran", "grandmother", "careful", 0),
    StoryParams("front_porch", "berry_juice", "stone", "cloth", "Benny", "boy", "Grandpa", "grandfather", "brave", 0),
    StoryParams("diner", "syrup", "braided", "tray", "Ruby", "girl", "Gran", "grandmother", "curious", 1),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did, d in DRINKS.items():
        lines.append(asp.fact("drink", did))
        if d.sticky:
            lines.append(asp.fact("sticky", did))
    for cid in COASTERS:
        lines.append(asp.fact("coaster", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(D) :- drink(D), sticky(D).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,D,C) :- setting(S), drink(D), coaster(C), hazard(D).
safe_response(D,R) :- drink(D), response(R), power(R,P), sticky(D), P >= 2.
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
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH: ASP sensible responses differ from Python.")
    try:
        s = generate(resolve_params(argparse.Namespace(setting=None, drink=None, coaster=None, response=None, child_name=None, helper_name=None, delay=None), random.Random(7)))
        assert s.story
        print("OK: smoke-generated story produced.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        DRINKS[params.drink],
        COASTERS[params.coaster],
        RESPONSES[params.response],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
        params.trait,
        params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for s, d, c in asp_valid_combos():
            print(f"{s:12} {d:12} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
