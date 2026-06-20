#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rinse_twist_fairy_tale.py
=========================================================

A standalone story world for a tiny fairy-tale domain: a child gets a magical
gift, a twist makes the first plan go wrong, a gentle helper suggests a rinsing
spell, and the ending proves the change with a bright, clean image.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes,
- a forward-chained causal model,
- a reasonableness gate,
- a Python/ASP twin,
- and three separate QA sets built from world state.

The seed words and instruments are:
- rinse
- Twist
- Fairy Tale
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

BRAVE_INIT = 5.0
TWIST_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    magical: bool = False
    rinsed: bool = False
    spoiled: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "fairy": "fairy"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    name: str
    brightness: str
    garden: bool = False
    hall: bool = False
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
class MagicalThing:
    id: str
    label: str
    phrase: str
    shine: str
    sparkle: str
    twisty: bool = False
    can_rinse: bool = True
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
    act: str
    wisdom: str
    power: int
    sense: int
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["twist"] < THRESHOLD:
            continue
        sig = ("spoil", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.spoiled = True
        ent.meters["spoiled"] += 1
        if "child" in world.entities:
            world.get("child").memes["worry"] += 1
        out.append("__twist__")
    return out


def _r_rinse_calms(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["rinsed"] < THRESHOLD:
            continue
        sig = ("calm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.spoiled = False
        ent.rinsed = True
        ent.meters["gleam"] += 1
        if "child" in world.entities:
            world.get("child").memes["relief"] += 1
        out.append("__gleam__")
    return out


CAUSAL_RULES = [
    Rule("spoil", "physical", _r_spoil),
    Rule("rinsing", "physical", _r_rinse_calms),
]


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


def twist_risk(item: MagicalThing) -> bool:
    return item.twisty


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def is_reasonable(item: MagicalThing, place: Place, helper: Helper) -> bool:
    return twist_risk(item) and helper.sense >= SENSE_MIN and item.can_rinse and place.garden


def predict_twist(world: World, item_id: str) -> dict:
    sim = world.copy()
    _do_twist(sim, sim.get(item_id), narrate=False)
    return {
        "spoiled": sim.get(item_id).spoiled,
        "worry": sim.get("child").memes["worry"],
    }


def _do_twist(world: World, item: Entity, narrate: bool = True) -> None:
    item.meters["twist"] += 1
    item.meters["shine"] = 0
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, place: Place, item: MagicalThing) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Once in a little fairy-tale land, {child.id} wandered into {place.name}, "
        f"where a {item.label} waited with {item.shine} and {item.sparkle}."
    )
    world.say(
        f"{child.id} loved the bright thing at once, because it seemed like a gift "
        f"made only for {child.pronoun('object')}."
    )


def desire(world: World, child: Entity, item: MagicalThing) -> None:
    child.memes["want"] += 1
    world.say(
        f"{child.id} reached for the {item.label} and whispered, "
        f'"I want to keep it shining forever."'
    )


def twist(world: World, child: Entity, item: MagicalThing) -> None:
    child.memes["surprise"] += 1
    world.say(
        f"But then came the Twist: a stray vine curled around the {item.label}, "
        f"and the bright thing turned dim and dusty in one blink."
    )


def warn(world: World, child: Entity, helper: Helper, item: MagicalThing) -> None:
    pred = predict_twist(world, item.id)
    child.memes["listening"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} leaned close and said, "{item.label_word if hasattr(item, "label_word") else item.label} can be made bright again. '
        f"But first it must be rinsed, or the dust will stay on it."
    )


def rinse(world: World, child: Entity, helper: Helper, item: MagicalThing) -> None:
    helper.meters["help"] += 1
    item.meters["rinsed"] += 1
    item.rinsed = True
    _do_rinse_effect(world, item)
    world.say(
        f"{helper.id} led {child.id} to the silver spring and helped {child.pronoun('object')} rinse the {item.label} clean."
    )


def _do_rinse_effect(world: World, item: Entity) -> None:
    item.meters["twist"] = 0
    item.meters["rinsed"] += 1
    propagate(world, narrate=False)


def resolve(world: World, child: Entity, helper: Helper, item: MagicalThing) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    world.say(
        f"The water ran clear, the {item.label} shone again, and {child.id} laughed "
        f"like a bell. {helper.id} smiled and said, \"A little rinse can save a fair gift.\""
    )
    world.say(
        f"By evening, {child.id} wore a wet grin and carried the {item.label} home, "
        f"glowing softly as if the Twist had never won."
    )


def tell(place: Place, item: MagicalThing, helper: Helper,
         child_name: str = "Mira", child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guide = world.add(Entity(id=helper.id, kind="character", type="fairy", role="helper"))
    gift = world.add(Entity(id=item.id, type="thing", label=item.label))
    world.facts["place"] = place
    world.facts["item"] = item
    world.facts["helper"] = helper
    world.facts["child"] = child
    world.facts["guide"] = guide
    world.facts["gift"] = gift

    intro(world, child, place, item)
    world.para()
    desire(world, child, item)
    twist(world, child, item)
    warn(world, child, helper, item)
    if item.twisty:
        world.para()
        rinse(world, child, helper, item)
        resolve(world, child, helper, item)

    world.facts["outcome"] = "rinsed" if item.twisty else "clean"
    world.facts["helped"] = True
    return world


PLACES = {
    "garden": Place("garden", "the moonlit garden", "soft", garden=True, tags={"garden"}),
    "spring": Place("spring", "the silver spring", "bright", garden=True, tags={"water", "spring"}),
    "hall": Place("hall", "the castle hall", "warm", hall=True, tags={"castle"}),
}

ITEMS = {
    "crown": MagicalThing("crown", "tiny crown", "a tiny crown", "sparkled", "twinkled", twisty=True, tags={"crown"}),
    "cloak": MagicalThing("cloak", "silver cloak", "a silver cloak", "glimmered", "shone", twisty=True, tags={"cloak"}),
    "lantern": MagicalThing("lantern", "glass lantern", "a glass lantern", "glowed", "winked", twisty=True, tags={"lantern"}),
}

HELPERS = {
    "fairy": Helper("Twist", "fairy helper", "a little fairy", "brought the rinse water",
                    "know how to mend bright things", 3, 3, tags={"fairy", "rinse"}),
    "brook": Helper("Brook", "brook sprite", "a brook sprite", "carried clear water",
                    "trusts the rinsing path", 2, 2, tags={"brook", "rinse"}),
    "queen": Helper("Queen", "queen", "a kind queen", "ordered a rinse bowl",
                    "can choose wise fixes", 4, 4, tags={"queen", "rinse"}),
}

CHILDREN = ["Mira", "Lena", "Ivy", "Nora", "Pip", "Elsie"]


@dataclass
@dataclass
class StoryParams:
    place: str
    item: str
    helper: str
    child: str
    child_gender: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for i in ITEMS.values():
            for h in HELPERS.values():
                if is_reasonable(i, p, h):
                    combos.append((p.id, i.id, h.id))
    return combos


def explain_rejection(item: MagicalThing, place: Place, helper: Helper) -> str:
    if not item.can_rinse:
        return f"(No story: {item.label} cannot be rinsed clean.)"
    if not place.garden:
        return f"(No story: this fairy tale needs water nearby so the rinse can happen.)"
    if helper.sense < SENSE_MIN:
        return f"(No story: {helper.id} is too silly a helper for this gentle twist.)"
    return "(No story: this combination is not reasonable enough for the tale.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    helper = f["helper"]
    place = f["place"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the word "rinse" and the name Twist.',
        f"Tell a gentle fairy tale where {child.id} finds a {item.label} at {place.name}, a Twist makes it dusty, and {helper.id} helps with a rinse.",
        f"Write a small magical story where a bright thing gets spoiled by a Twist, then a wise helper shows how to rinse it clean.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    item = f["item"]
    helper = f["helper"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, who found a magical {item.label} and needed help when a Twist made it dusty."),
        ("What happened after the Twist?",
         f"The {item.label} turned dull and dusty. That change made it look less magical, so the child needed a gentle fix."),
        ("How was the problem solved?",
         f"{helper.id} helped {child.id} rinse the {item.label} at {place.name}. The water washed the dust away and the shine came back."),
        ("How did the ending prove the change?",
         f"By the end, the {item.label} was bright again and {child.id} carried it home glowing softly. That ending image shows the rinse worked."),
    ]
    if f.get("predicted_worry", 0) >= 1:
        qa.append((
            "Why did the helper suggest rinsing?",
            f"Because the helper could see that the Twist would leave dust on the {item.label}. Rinsing was the calm, sensible way to restore its shine."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item"].tags) | set(f["helper"].tags) | set(f["place"].tags)
    qa = []
    if "rinse" in tags:
        qa.append((
            "What does it mean to rinse something?",
            "To rinse something means to run water over it so dirt, dust, or soap can wash away. It is a gentle way to make something clean again."
        ))
    if "fairy" in tags:
        qa.append((
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical helper in stories. Fairies often bring sparkles, good advice, or a little magic fix."
        ))
    if "water" in tags or "spring" in tags:
        qa.append((
            "Why is clear water useful in stories like this?",
            "Clear water can wash away dust without hurting the thing itself. That makes it useful for gentle magical cleaning."
        ))
    return qa


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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "crown", "fairy", "Mira", "girl"),
    StoryParams("spring", "cloak", "brook", "Lena", "girl"),
    StoryParams("garden", "lantern", "queen", "Pip", "boy"),
]


def outcome_of(params: StoryParams) -> str:
    return "rinsed" if ITEMS[params.item].twisty else "clean"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.garden:
            lines.append(asp.fact("garden", pid))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.twisty:
            lines.append(asp.fact("twisty", iid))
        if i.can_rinse:
            lines.append(asp.fact("can_rinse", iid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(P,I,H) :- place(P), item(I), helper(H), garden(P), twisty(I), can_rinse(I), sense(H,S), sense_min(M), S >= M.
outcome(rinsed) :- reasonable(_,_,_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))

    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, item=None, helper=None, child=None, child_gender=None), random.Random(1)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world with a Twist and a rinse.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
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


def _pick_child(rng: random.Random, gender: Optional[str]) -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    name = rng.choice(CHILDREN)
    return name, g


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.place and not is_reasonable(ITEMS[args.item], PLACES[args.place], HELPERS[args.helper] if args.helper else list(HELPERS.values())[0]):
        raise StoryError(explain_rejection(ITEMS[args.item], PLACES[args.place], HELPERS[args.helper] if args.helper else list(HELPERS.values())[0]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, helper = rng.choice(sorted(combos))
    child, gender = _pick_child(rng, args.child_gender)
    if args.child:
        child = args.child
    if args.helper and args.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    return StoryParams(place, item, helper, child, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], HELPERS[params.helper], params.child, params.child_gender)
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
        print(asp_program(show="#show reasonable/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, i, h in combos:
            print(f"  {p:8} {i:8} {h}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.item} in the {p.place} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
