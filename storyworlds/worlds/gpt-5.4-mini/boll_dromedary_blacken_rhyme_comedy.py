#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boll_dromedary_blacken_rhyme_comedy.py
=======================================================================

A standalone storyworld for a small comedy: a child tries to make a silly snack
song, a dromedary gets involved, a hot pan starts to blacken the treat, and a
calm grown-up turns the muddle into a funny, safe ending.

Seed words:
- boll
- dromedary
- blacken

Style:
- Comedy

Feature:
- Rhyme

This world models a tiny kitchen scene with physical meters and emotional memes,
state-driven turns, a reasonableness gate, QA from world state, and an inline ASP
twin for parity checks.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Item:
    id: str
    label: str
    phrase: str
    hot: bool = False
    edible: bool = False
    blackens: bool = False
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
class Helper:
    id: str
    label: str
    phrase: str
    role: str
    sense: int
    power: int
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
@dataclass
class StoryParams:
    kitchen: str
    snack: str
    helper: str
    child: str
    child_gender: str
    grownup: str
    grownup_gender: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
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


def _r_blacken(world: World) -> list[str]:
    out: list[str] = []
    snack = world.entities.get("snack")
    if not snack or snack.meters["hot"] < THRESHOLD:
        return out
    sig = ("blacken",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["blackened"] += 1
    world.get("child").memes["alarm"] += 1
    out.append("__blacken__")
    return out


CAUSAL_RULES = [Rule("blacken", "physical", _r_blacken)]


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


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def issue_at_risk(helper: Helper, snack: Item) -> bool:
    return helper.sense >= 0 and snack.blackens


def heat_severity(delay: int) -> int:
    return 1 + delay


def can_fix(helper: Helper, delay: int) -> bool:
    return helper.power >= heat_severity(delay)


def predict_blacken(world: World, delay: int) -> dict:
    sim = world.copy()
    sim.get("snack").meters["hot"] += 1
    propagate(sim, narrate=False)
    return {
        "blackened": sim.get("snack").meters["blackened"] >= THRESHOLD,
        "alarm": sim.get("child").memes["alarm"],
        "severity": heat_severity(delay),
    }


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def setup(world: World, child: Entity, grownup: Entity, kitchen: Item) -> None:
    child.memes["mirth"] += 1
    world.say(
        f"In {kitchen.phrase}, {child.id} set a silly scene, with a bright copper "
        f"bowl and a laugh so keen."
    )
    world.say(
        f"{child.id} tapped a spoon and started to sing, while a sleepy "
        f"dromedary watched everything."
    )


def tempt(world: World, child: Entity, snack: Item, dromedary: Entity) -> None:
    child.memes["glee"] += 1
    world.say(
        f'{child.id} said, "This boll will be a snack so grand, if I warm it up '
        f"by hand!"
    )
    world.say(
        f"The dromedary blinked, then gave a snort; it looked like it wanted a "
        f"chef's report."
    )


def warn(world: World, grownup: Entity, child: Entity, snack: Item, delay: int) -> None:
    pred = predict_blacken(world, delay)
    grownup.memes["care"] += 1
    world.facts["predicted_blacken"] = pred["blackened"]
    if pred["blackened"]:
        world.say(
            f'{grownup.id} said, "That pan is hot, my dear. If you keep going, '
            f"the {snack.label} may blacken here."
        )
    else:
        world.say(
            f'{grownup.id} said, "Slow down first, sweet one. Hot pans make '
            f"trouble for little buns."
        )


def clown_about(world: World, dromedary: Entity) -> None:
    dromedary.memes["mischief"] += 1
    world.say(
        "The dromedary huffed and puffed, then nudged the flour with a velvet lip; "
        "powder flew like a tiny ship."
    )


def cook(world: World, snack: Item) -> None:
    snack.meters["hot"] += 1
    snack.meters["time"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {snack.label} sat on the pan and began to brown, but the rim went "
        f"dark and made a comic frown."
    )


def alarm(world: World, child: Entity, snack: Item, grownup: Entity) -> None:
    if snack.meters["blackened"] >= THRESHOLD:
        world.say(
            f'"Oh no!" {child.id} cried. "My {snack.label} turned blacken by '
            f"mistake!"
        )
        world.say(f'"{grownup.id}!"')


def rescue(world: World, grownup: Entity, helper: Helper, snack: Item) -> None:
    snack.meters["hot"] = 0
    snack.meters["saved"] = 1
    world.say(
        f"{grownup.id} came at once and {helper.phrase}, turning the heat away "
        f"before the joke got mean."
    )
    world.say(
        f"The pan cooled down, the smoke drifted out, and the little snack stayed "
        f"safe and proud."
    )


def lesson(world: World, grownup: Entity, child: Entity, snack: Item) -> None:
    child.memes["relief"] += 1
    child.memes["love"] += 1
    world.say(
        f"{grownup.id} smiled and hugged {child.id} tight. \"Hot things can "
        f"blacken fast,\" {grownup.pronoun()} said, \"so we ask for help.\""
    )
    world.say(
        f"{child.id} nodded, a little wiser and a lot less frazzled, while the "
        f"dromedary looked pleased and dazzled."
    )


def ending(world: World, child: Entity, dromedary: Entity, snack: Item) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then {child.id} made a new plan that was bright and clean: a cool snack "
        f"song with a sillier routine."
    )
    world.say(
        f"The dromedary bowed like a stage-star of old, and the evening ended "
        f"with a chuckle and a bowl."
    )


HELPERS = {
    "fan": Helper("fan", "fan", "a table fan", "cooling", 3, 3, {"cool", "air"}),
    "mitt": Helper("mitt", "mitt", "an oven mitt", "protecting", 3, 2, {"heat"}),
    "tray": Helper("tray", "tray", "a cool tray", "supporting", 2, 2, {"heat"}),
}

KITCHENS = {
    "kitchen": Item("kitchen", "kitchen", "the kitchen", hot=False, tags={"kitchen"}),
    "sunroom": Item("sunroom", "sunroom", "the sunny sunroom", hot=False, tags={"kitchen"}),
}

SNACKS = {
    "boll": Item("boll", "boll", "a sweet boll", edible=True, blackens=True, tags={"boll"}),
    "bun": Item("bun", "bun", "a soft bun", edible=True, blackens=True, tags={"bun"}),
    "tart": Item("tart", "tart", "a tiny tart", edible=True, blackens=True, tags={"tart"}),
}

DROMEDARIES = {
    "dromedary": Entity("dromedary", kind="character", type="animal", label="dromedary"),
}

GIRL_NAMES = ["Maya", "Lina", "Tia", "Nora", "Ava", "Rae"]
BOY_NAMES = ["Finn", "Owen", "Noah", "Eli", "Theo", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for k in KITCHENS:
        for s in SNACKS:
            for h in HELPERS:
                if can_fix(HELPERS[h], 0):
                    combos.append((k, s, h))
    return combos


@dataclass
class StorySampleParams:
    kitchen: str
    snack: str
    helper: str
    child: str
    child_gender: str
    grownup: str
    grownup_gender: str
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
    ap = argparse.ArgumentParser(description="Comedy rhyme storyworld with a dromedary, a boll, and blackening heat.")
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StorySampleParams:
    if args.helper and args.delay is not None and not can_fix(HELPERS[args.helper], args.delay):
        raise StoryError("That helper is too weak for the hot-pan mishap.")
    combos = [c for c in valid_combos()
              if (args.kitchen is None or c[0] == args.kitchen)
              and (args.snack is None or c[1] == args.snack)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    kitchen, snack, helper = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    grownup_gender = args.grownup_gender or rng.choice(["mother", "father"])
    grownup = args.grownup or rng.choice(["Mom", "Dad"])
    return StorySampleParams(kitchen, snack, helper, child, child_gender, grownup, grownup_gender)


def tell(params: StorySampleParams, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(params.child, kind="character", type=params.child_gender, role="child"))
    grownup = world.add(Entity(params.grownup, kind="character", type=params.grownup_gender, role="grownup"))
    drom = world.add(Entity("dromedary", kind="character", type="animal", label="dromedary"))
    kitchen = world.add(Entity("kitchen", type="place", label=params.kitchen, attrs={"phrase": KITCHENS[params.kitchen].phrase}))
    snack = world.add(Entity("snack", type="food", label=params.snack, attrs={"kind": params.snack}))
    snack.meters["hot"] = 0
    world.facts["helper"] = HELPERS[params.helper]
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["grownup"] = grownup
    world.facts["dromedary"] = drom
    world.facts["snack"] = snack
    setup(world, child, grownup, KITCHENS[params.kitchen])
    world.para()
    tempt(world, child, SNACKS[params.snack], drom)
    warn(world, grownup, child, SNACKS[params.snack], delay)
    clown_about(world, drom)
    cook(world, snack)
    alarm(world, child, snack, grownup)
    world.para()
    rescue(world, grownup, HELPERS[params.helper], snack)
    lesson(world, grownup, child, snack)
    world.para()
    ending(world, child, drom, snack)
    world.facts["outcome"] = "contained"
    world.facts["snack"] = snack
    return world


def generate(params: StorySampleParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a funny rhyming story for a young child that includes the words "boll", "dromedary", and "blacken".',
        f"Tell a comedic rhyme story where {f['child'].id} tries to heat a boll, a dromedary causes a silly stir, and a grown-up keeps the snack from blackening.",
        "Write a playful kitchen story with a rhyme-like rhythm, a dromedary cameo, and a safe ending after a hot snack starts to blacken.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    snack = f["snack"]
    drom = f["dromedary"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {grownup.id}, and a dromedary in a funny kitchen mix-up. The snack and the silly animal make the scene a comic little rhyme."),
        (f"What happened to the {snack.label}?",
         f"It got hot and began to blacken. That happened because it stayed on the pan long enough for the heat to change it."),
        ("Why did the grown-up help?",
         f"The grown-up helped because the snack was getting too hot and the joke could turn into a burn. A calm fix kept the food safe and stopped the trouble."),
        ("What made the story silly?",
         f"The dromedary made it silly by snorting, nudging the flour, and acting like a stage star. Its wobbling ways made the kitchen feel like a tiny comedy show."),
    ]


WORLD_KNOWLEDGE = {
    "boll": [("What is a boll?",
              "A boll can mean a small round piece of bread or a little lump of food. In a story, it can be a playful snack word.")],
    "dromedary": [("What is a dromedary?",
                   "A dromedary is a camel with one hump. It is a real animal that can walk in dry places and carry things.")],
    "blacken": [("What does blacken mean?",
                 "To blacken means to become dark or black, often because of heat or burning.")],
    "heat": [("Why can a hot pan change food?",
              "Heat makes food cook. If it stays too long, the outside can get too dark or burn.")],
    "comedy": [("What makes a story comedic?",
                "A comedic story is meant to be funny. It often has silly actions, surprise, and a happy ending.")],
}
WORLD_ORDER = ["boll", "dromedary", "blacken", "heat", "comedy"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"boll", "dromedary", "blacken", "heat", "comedy"}
    out: list[tuple[str, str]] = []
    for key in WORLD_ORDER:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
blackened(S) :- hot(S), not cooled(S).
cooled(S) :- helper(H), power(H,P), P >= 1.
valid(K,S,H) :- kitchen(K), snack(S), helper(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in KITCHENS:
        lines.append(asp.fact("kitchen", k))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
    for h, hh in HELPERS.items():
        lines.append(asp.fact("helper", h))
        lines.append(asp.fact("sense", h, hh.sense))
        lines.append(asp.fact("power", h, hh.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        assert sample.story.strip()
        print("OK: smoke-test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_rejection(helper: Helper) -> str:
    return f"(No story: the helper {helper.label} is too weak for the hot snack.)"


def build_sample(params: StorySampleParams) -> StorySample:
    return generate(params)


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for k, s, h in asp_valid_combos():
            print(f"  {k:10} {s:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("kitchen", "boll", "fan", "Maya", "girl", "Mom"),
            StoryParams("sunroom", "bun", "mitt", "Finn", "boy", "Dad"),
            StoryParams("kitchen", "tart", "tray", "Nora", "girl", "Mom"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.child}: {p.snack} in {p.kitchen}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
