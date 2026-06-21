#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rental_way_register_bad_ending_bravery_misunderstanding.py
==========================================================================================

A standalone storyworld for a small mythic tale about a brave child, a rented
token, a misunderstood warning, and a bad ending in which a sacred gate is lost.

Seed words:
- rental
- way
- register

Features:
- Bad Ending
- Bravery
- Misunderstanding
- Myth style

The world is intentionally tiny: a traveler seeks a way across a river-gate,
borrows a luminous rental token from a shrine-register, misunderstands a
warning, and chooses bravery in the wrong moment. The result is a sad ending
that still proves what changed in the world.

The script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
- includes a Python reasonableness gate plus inline ASP twin
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
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    mythic_name: str
    gate: str
    way: str
    danger: str
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
class Rental:
    id: str
    label: str
    phrase: str
    register_name: str
    token_name: str
    shines: str
    cost: int
    makes_guide: bool = True
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
class Woe:
    id: str
    label: str
    severity: int
    text: str
    fail: str
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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["misunderstanding"] < THRESHOLD:
            continue
        sig = ("misunderstanding", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] += 1
        out.append("__warn__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["bravery"] < THRESHOLD:
            continue
        sig = ("bravery", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["resolve"] += 1
        out.append("__move__")
    return out


CAUSAL_RULES = [
    Rule("misunderstanding", "social", _r_misunderstanding),
    Rule("bravery", "social", _r_bravery),
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


def reasonableness_gate(place: Place, rental: Rental, woe: Woe) -> bool:
    return rental.makes_guide and place.way and woe.severity >= 1


def best_rental() -> Rental:
    return max(RENTALS.values(), key=lambda r: r.cost)


def outcome_of(params: "StoryParams") -> str:
    return "bad"


def predict_loss(world: World, child: Entity, place: Place, woe: Woe) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["misunderstanding"] += 1
    sim.get(child.id).memes["bravery"] += 1
    return {"loss": True, "fear": 1}


def _do_crossing(world: World, child: Entity, place: Place, rental: Rental) -> None:
    child.meters["on_way"] += 1
    child.meters["carrying"] += 1
    propagate(world, narrate=False)


def seek_way(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"Long ago, {child.id} stood before {place.mythic_name}, where the old way to the gate was hidden by mist."
    )
    world.say(
        f'The only path forward led toward {place.way}, and {child.id} wanted a sign that the way was safe.'
    )


def ask_register(world: World, child: Entity, rental: Rental, keeper: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"{child.id} went to the sacred register and asked for {rental.phrase}."
    )
    world.say(
        f'{keeper.id} wrote the rental down and whispered that every borrowed thing must be returned with care.'
    )


def warn(world: World, child: Entity, keeper: Entity, place: Place, woe: Woe) -> None:
    child.memes["misunderstanding"] += 1
    world.facts["predicted_loss"] = predict_loss(world, child, place, woe)["loss"]
    world.say(
        f'"Do not rush the gate," {keeper.id} warned. "The bridge answers to patience, and the river can steal a careless step."'
    )


def mishear(world: World, child: Entity, keeper: Entity, rental: Rental) -> None:
    world.say(
        f'{child.id} nodded, but {child.pronoun("possessive")} ears caught only part of the warning.'
    )
    world.say(
        f'{child.id} thought the register meant, "Be brave and go quickly," and so {child.pronoun()} gripped the {rental.label}.'
    )


def cross(world: World, child: Entity, place: Place, rental: Rental) -> None:
    child.memes["bravery"] += 1
    _do_crossing(world, child, place, rental)
    world.say(
        f"{child.id} stepped onto the old bridge with brave feet and the borrowed guide shining in {child.pronoun('possessive')} hand."
    )


def break_way(world: World, child: Entity, place: Place, woe: Woe) -> None:
    place_label = place.gate
    world.get("gate").meters["broken"] += 1
    world.get("gate").meters["lost"] += 1
    world.say(
        f"Then the bridge groaned, the stones shifted, and {place_label} gave way."
    )
    world.say(
        f"The river took the shining token, and the only clear way across was gone."
    )


def ending_lament(world: World, child: Entity, keeper: Entity, place: Place, rental: Rental) -> None:
    child.memes["sorrow"] += 1
    keeper.memes["sorrow"] += 1
    world.say(
        f"For a while, nobody spoke. {keeper.id} had to mark the rental as lost in the register."
    )
    world.say(
        f'{keeper.id} said softly, "Bravery is good, but bravery without understanding can lead a child straight into grief."'
    )
    world.say(
        f"{child.id} returned home with empty hands, and the mist-covered gate stayed broken behind them."
    )


def tell(place: Place, rental: Rental, woe: Woe,
         child_name: str = "Ivo", child_gender: str = "boy",
         keeper_name: str = "Sera", keeper_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="traveler"))
    keeper = world.add(Entity(id=keeper_name, kind="character", type=keeper_gender, role="keeper"))
    gate = world.add(Entity(id="gate", kind="thing", type="thing", label=place.gate))
    token = world.add(Entity(id="token", kind="thing", type="thing", label=rental.label))

    child.memes["bravery"] = 1.0
    child.memes["misunderstanding"] = 0.0
    keeper.memes["duty"] = 1.0

    seek_way(world, child, place)
    ask_register(world, child, rental, keeper)
    world.para()
    warn(world, child, keeper, place, woe)
    mishear(world, child, keeper, rental)
    world.para()
    cross(world, child, place, rental)
    break_way(world, child, place, woe)
    world.para()
    ending_lament(world, child, keeper, place, rental)

    world.facts.update(
        child=child,
        keeper=keeper,
        place=place,
        rental=rental,
        woe=woe,
        gate=gate,
        token=token,
        outcome="bad",
        lost=True,
    )
    return world


PLACES = {
    "rivergate": Place("rivergate", "the river gate", "River Gate", "the silver gate", "the winding way", "the old current", tags={"myth", "way"}),
    "templepath": Place("templepath", "the temple path", "Temple Path", "the stone gate", "the sacred way", "the deep shadow", tags={"myth", "way"}),
    "hillroad": Place("hillroad", "the hill road", "Hill Road", "the hill gate", "the mountain way", "the wind and rain", tags={"myth", "way"}),
}

RENTALS = {
    "lantern": Rental("lantern", "lantern", "a rental lantern", "register", "lantern", "glowed like a small star", 3, True, tags={"rental", "register"}),
    "staff": Rental("staff", "staff", "a rental way-staff", "register", "staff", "pointed toward the safe path", 2, True, tags={"rental", "way"}),
    "cloak": Rental("cloak", "cloak", "a rental guiding cloak", "register", "cloak", "shone with river-light", 1, True, tags={"rental"}),
}

WOES = {
    "fall": Woe("fall", "fall", 2, "the bridge might drop a careless step", "the bridge broke under the brave but rushed feet", tags={"bad", "bravery"}),
    "loss": Woe("loss", "loss", 3, "the token might be carried away", "the river carried the rented guide away", tags={"bad", "misunderstanding"}),
}

CHILDREN = ["Ivo", "Mara", "Nilo", "Tari", "Lina", "Orin"]
KEEPERS = ["Sera", "Asha", "Dorin", "Miren"]
TRAITS = ["bold", "curious", "steady", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for rid, rental in RENTALS.items():
            for wid, woe in WOES.items():
                if reasonableness_gate(place, rental, woe):
                    combos.append((pid, rid, wid))
    return combos


@dataclass
@dataclass
class StoryParams:
    place: str
    rental: str
    woe: str
    child: str
    child_gender: str
    keeper: str
    keeper_gender: str
    trait: str
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


KNOWLEDGE = {
    "rental": [("What is a rental thing?", "A rental thing is something you borrow for a while and then return later.")],
    "register": [("What is a register?", "A register is a record kept so people remember what was borrowed or promised.")],
    "way": [("What is a way?", "A way is a path or route that helps someone get from one place to another.")],
    "bravery": [("What is bravery?", "Bravery is doing something hard or scary while still trying to do the right thing.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone hears or thinks the wrong thing.")],
    "bad": [("What is a bad ending?", "A bad ending is when the problem turns out sadly instead of being fixed well.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the words "rental", "way", and "register".',
        f"Tell a myth where {f['child'].id} is brave but misunderstands a warning from {f['keeper'].id}, and the ending is sad.",
        f"Write a short story in a legendary style about borrowing a guide from a register and losing the way across a river gate.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, keeper, place, rental, woe = f["child"], f["keeper"], f["place"], f["rental"], f["woe"]
    return [
        ("Who is the story about?", f"It is about {child.id}, who went to {place.mythic_name} with {keeper.id} watching over the register."),
        ("What did {0} borrow?".format(child.id), f"{child.id} borrowed {rental.phrase} from the register so {child.pronoun()} could try to find the way."),
        ("Why did things go wrong?", f"{child.id} misunderstood {keeper.id}'s warning and treated it like permission to hurry. That brave mistake led straight to the loss of the bridge and the rented guide."),
        ("How did the story end?", f"It ended badly. {child.id} came home safely, but the {place.gate} was broken and the rental token was lost in the river."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["rental"].tags) | set(world.facts["woe"].tags)
    out: list[tuple[str, str]] = []
    for key in ["rental", "register", "way", "bravery", "misunderstanding", "bad"]:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rivergate", "lantern", "fall", "Ivo", "boy", "Sera", "woman", "bold"),
    StoryParams("templepath", "staff", "loss", "Mara", "girl", "Dorin", "man", "curious"),
]


def explain_rejection(place: Place, rental: Rental, woe: Woe) -> str:
    return "(No story: this combination does not make a mythic warning worth telling.)"


def explain_response(rid: str) -> str:
    return f"(Refusing response '{rid}': this world only tells the bad-ending branch.)"


ASP_RULES = r"""
valid(P, R, W) :- place(P), rental(R), woe(W), makes_guide(R), way(P), severity(W, S), S >= 1.
bad(outcome) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, r in RENTALS.items():
        lines.append(asp.fact("rental", rid))
        if r.makes_guide:
            lines.append(asp.fact("makes_guide", rid))
    for wid, w in WOES.items():
        lines.append(asp.fact("woe", wid))
        lines.append(asp.fact("severity", wid, w.severity))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    # smoke test ordinary generation
    try:
        s = generate(CURATED[0])
        if not s.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic rental-way-register storyworld with a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rental", choices=RENTALS)
    ap.add_argument("--woe", choices=WOES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.rental is None or c[1] == args.rental)
              and (args.woe is None or c[2] == args.woe)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, rental, woe = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(CHILDREN)
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    keeper = args.keeper or rng.choice(KEEPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, rental, woe, child, child_gender, keeper, keeper_gender, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], RENTALS[params.rental], WOES[params.woe],
                 params.child, params.child_gender, params.keeper, params.keeper_gender)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for item in asp_valid_combos():
            print(" ", item)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
