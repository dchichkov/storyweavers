#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/triumphant_lorry_flashback_heartwarming.py
===========================================================================

A small, heartwarming storyworld about a lorry, a problem on the road, and a
flashback that helps solve it. The story grows from a concrete world model:
the lorry has physical state (meters) and emotional state (memes); the road,
cargo, weather, and helper all matter; and a flashback is an actual narrated
turn, not a pasted paragraph.

The world supports:
- a triumphant ending,
- a flashback-based recovery,
- child-facing, grounded QA,
- an inline ASP twin and parity verification.

The tiny premise:
A lorry gets stuck after a mishap on a hill. The driver remembers, in a brief
flashback, how a neighbor once showed a clever trick for sharing weight and
using a ramp board. That remembered kindness helps the lorry finish the job and
arrive triumphantly.
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Road:
    id: str
    label: str
    steep: int
    rough: int
    safe_hill: bool = False
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
class Cargo:
    id: str
    label: str
    phrase: str
    heavy: int
    fragile: bool = False
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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    power: int
    sense: int
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
class StoryParams:
    road: str
    cargo: str
    fix: str
    lorry_name: str
    driver_name: str
    driver_gender: str
    helper_name: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None
    delay: int = 0
    load: int = 1
    rain: bool = False
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


def _r_weight_shift(world: World) -> list[str]:
    out = []
    lorry = world.entities.get("lorry")
    cargo = world.entities.get("cargo")
    road = world.entities.get("road")
    if not lorry or not cargo or not road:
        return out
    if lorry.meters["stuck"] >= THRESHOLD and ("shift",) not in world.fired:
        world.fired.add(("shift",))
        lorry.memes["worry"] += 1
        cargo.meters["tilted"] += 1
        if road.rough > 1:
            lorry.meters["wobble"] += 1
        out.append("__shift__")
    return out


def _r_brighten(world: World) -> list[str]:
    out = []
    if world.entities.get("driver") and world.entities["driver"].memes["hope"] >= THRESHOLD:
        if ("brighten",) not in world.fired:
            world.fired.add(("brighten",))
            world.entities["driver"].memes["steadiness"] += 1
            out.append("__brighten__")
    return out


CAUSAL_RULES = [Rule("weight_shift", _r_weight_shift), Rule("brighten", _r_brighten)]


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


def reason_ok(fix: Fix) -> bool:
    return fix.sense >= 2


def valid_combo(road: Road, cargo: Cargo, fix: Fix) -> bool:
    return reason_ok(fix) and cargo.heavy >= road.steep and fix.power >= road.steep + cargo.heavy // 2


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.sense)


def predict_stuck(world: World, road_id: str, cargo_id: str, delay: int) -> dict:
    sim = world.copy()
    sim.get("lorry").meters["stuck"] += 1
    sim.get("lorry").meters["load"] += sim.get(cargo_id).meters["mass"]
    if sim.get(road_id).rough >= 2:
        sim.get("lorry").meters["wobble"] += 1
    return {
        "stuck": sim.get("lorry").meters["stuck"] >= THRESHOLD,
        "wobble": sim.get("lorry").meters["wobble"],
        "delay": delay,
    }


def setup(world: World, driver: Entity, helper: Entity, lorry: Entity, road: Road, cargo: Cargo) -> None:
    world.say(
        f"{driver.id} drove the {lorry.label} up a {road.label} with {cargo.phrase} in the back."
    )
    world.say(
        f"The lorry liked the work, and {helper.id} rode along with a ready smile."
    )
    driver.memes["joy"] += 1
    helper.memes["joy"] += 1


def trouble(world: World, driver: Entity, lorry: Entity, road: Road, cargo: Cargo) -> None:
    driver.memes["worry"] += 1
    lorry.meters["stuck"] += 1
    lorry.meters["load"] += cargo.heavy
    if road.rough >= 2:
        lorry.meters["wobble"] += 1
    world.say(
        f"But the hill was steep, and the wheels slipped. The {lorry.label} gave a little groan and slowed to a stop."
    )


def flashback(world: World, driver: Entity, helper: Entity, fix: Fix, road: Road) -> None:
    driver.memes["hope"] += 1
    world.say(
        f"{driver.id} stared at the road, and a little flashback flickered through {driver.pronoun('possessive')} mind."
    )
    world.say(
        f"Once, {helper.id} had shown {driver.id} how to use {fix.phrase} when a load was too hard to pull alone."
    )
    world.say(
        f"That kind memory felt warm and bright, and it gave {driver.id} a steady breath."
    )


def fix_the_problem(world: World, driver: Entity, helper: Entity, lorry: Entity, cargo: Cargo, fix: Fix, road: Road) -> None:
    lorry.meters["stuck"] = 0.0
    lorry.meters["wobble"] = 0.0
    cargo.meters["tilted"] = 0.0
    driver.memes["hope"] += 1
    world.say(
        f"{driver.id} remembered the trick, and together they used {fix.method}."
    )
    world.say(
        f"{helper.id} guided the {lorry.label} just so, and the cargo settled safe and square again."
    )
    world.say(
        f"Slowly, then surely, the {lorry.label} climbed the last bit of the hill."
    )


def triumphant_finish(world: World, driver: Entity, helper: Entity, lorry: Entity, cargo: Cargo, road: Road) -> None:
    driver.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"At the top, the {lorry.label} rolled into the sun with {cargo.label} steady in the back."
    )
    world.say(
        f"{driver.id} smiled a triumphant smile, and {helper.id} laughed, because the hard part was over and the day felt gentle again."
    )
    world.say(
        f"The little lorry looked bright against the hill, ready for the next trip home."
    )


def tell(params: StoryParams) -> World:
    road = ROADS[params.road]
    cargo = CARGOS[params.cargo]
    fix = FIXES[params.fix]
    if not valid_combo(road, cargo, fix):
        raise StoryError("That road, cargo, and fix do not make a reasonable story.")

    world = World()
    driver = world.add(Entity(id=params.driver_name, kind="character", type=params.driver_gender, role="driver"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role=params.helper_role))
    lorry = world.add(Entity(id="lorry", kind="thing", type="lorry", label=params.lorry_name))
    road_ent = world.add(Entity(id="road", kind="thing", type="road", label=road.label))
    cargo_ent = world.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label))
    cargo_ent.meters["mass"] = cargo.heavy
    if params.rain:
        road_ent.meters["slick"] += 1

    setup(world, driver, helper, lorry, road, cargo)
    world.para()
    trouble(world, driver, lorry, road, cargo)
    flashback(world, driver, helper, fix, road)
    world.para()
    fix_the_problem(world, driver, helper, lorry, cargo, fix, road)
    triumphant_finish(world, driver, helper, lorry, cargo, road)

    world.facts.update(
        driver=driver,
        helper=helper,
        lorry=lorry,
        road=road,
        cargo=cargo,
        fix=fix,
        outcome="triumphant",
        had_flashback=True,
    )
    return world


ROADS = {
    "hillroad": Road(id="hillroad", label="hill road", steep=2, rough=1, safe_hill=True, tags={"hill", "road"}),
    "countryroad": Road(id="countryroad", label="country road", steep=1, rough=2, safe_hill=True, tags={"road"}),
    "lanebend": Road(id="lanebend", label="bend in the lane", steep=2, rough=2, safe_hill=True, tags={"lane"}),
}

CARGOS = {
    "apples": Cargo(id="apples", label="apples", phrase="a basket of apples", heavy=2, fragile=True, tags={"food"}),
    "books": Cargo(id="books", label="books", phrase="a neat stack of library books", heavy=2, fragile=False, tags={"books"}),
    "blankets": Cargo(id="blankets", label="blankets", phrase="a stack of warm blankets", heavy=3, fragile=False, tags={"warmth"}),
}

FIXES = {
    "ramp": Fix(id="ramp", label="ramp board", phrase="the old ramp board", method="a ramp board and a careful push", power=4, sense=3, tags={"ramp"}),
    "rope": Fix(id="rope", label="rope pull", phrase="a kind rope pull", method="a rope, a tug, and a patient count", power=3, sense=3, tags={"rope"}),
    "rest": Fix(id="rest", label="rest break", phrase="a little rest and a sip of tea", method="a short rest while the driver looked back and breathed", power=2, sense=2, tags={"rest"}),
    "bucket": Fix(id="bucket", label="water bucket", phrase="a water bucket", method="a bucket of water", power=1, sense=1, tags={"bad"}),
}

NAMES_GIRL = ["Mia", "Ivy", "Nora", "Lily"]
NAMES_BOY = ["Ben", "Theo", "Max", "Eli"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for rid, road in ROADS.items():
        for cid, cargo in CARGOS.items():
            for fid, fix in FIXES.items():
                if valid_combo(road, cargo, fix):
                    out.append((rid, cid, fid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a lorry named {f["lorry"].label} that includes the word "lorry" and ends triumphantly.',
        f"Tell a gentle story where {f['driver'].id} remembers a helpful moment in a flashback and uses it to help the lorry finish the hill.",
        f"Write a short story with the words triumphant and lorry, with a flashback that helps solve the problem kindly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    driver = f["driver"]
    helper = f["helper"]
    lorry = f["lorry"]
    cargo = f["cargo"]
    fix = f["fix"]
    road = f["road"]
    return [
        QAItem(
            question="What was the problem in the story?",
            answer=f"The {lorry.label} got stuck on the {road.label} while carrying {cargo.label}. The hill was hard, so they had to find a kinder, steadier way to keep going.",
        ),
        QAItem(
            question="What did the flashback help the driver remember?",
            answer=f"The flashback helped {driver.id} remember how {helper.id} once showed a simple trick for moving a heavy load. That memory gave {driver.id} hope and pointed them toward {fix.label}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the {lorry.label} reaching the top and the day feeling triumphant. The cargo stayed safe, and everyone could smile at the finish.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lorry?",
            answer="A lorry is a big truck that carries things from one place to another. It is useful for moving heavy loads safely.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story briefly remembers something that happened before. It can help a character understand what to do now.",
        ),
        QAItem(
            question="What does triumphant mean?",
            answer="Triumphant means full of happy victory. It is the feeling you get when something hard goes well at the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(road="hillroad", cargo="books", fix="ramp", lorry_name="the bright blue lorry", driver_name="Ava", driver_gender="girl", helper_name="Grandpa", helper_gender="man", helper_role="helper", delay=0, load=1, rain=False),
    StoryParams(road="lanebend", cargo="blankets", fix="rope", lorry_name="the little red lorry", driver_name="Noah", driver_gender="boy", helper_name="Mum", helper_gender="woman", helper_role="helper", delay=0, load=1, rain=False),
    StoryParams(road="countryroad", cargo="apples", fix="rest", lorry_name="the cheerful lorry", driver_name="Ivy", driver_gender="girl", helper_name="Ben", helper_gender="boy", helper_role="neighbor", delay=0, load=1, rain=True),
]


def explain_rejection(fix: Fix) -> str:
    return f"(No story: {fix.label} is too weak or not sensible enough to help the lorry up the hill.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.fix and not reason_ok(FIXES[args.fix]):
        raise StoryError(explain_rejection(FIXES[args.fix]))
    combos = [c for c in valid_combos()
              if (args.road is None or c[0] == args.road)
              and (args.cargo is None or c[1] == args.cargo)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    road, cargo, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper_name = rng.choice(["Mum", "Dad", "Grandpa", "Nana", "Pip"])
    helper_gender = rng.choice(["woman", "man", "girl", "boy"])
    return StoryParams(
        road=road, cargo=cargo, fix=fix,
        lorry_name=args.lorry or "the lorry",
        driver_name=name, driver_gender=gender,
        helper_name=helper_name, helper_gender=helper_gender,
        helper_role="helper",
        delay=0, load=1, rain=False,
    )


def generate(params: StoryParams) -> StorySample:
    if params.road not in ROADS or params.cargo not in CARGOS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming lorry storyworld with a flashback.")
    ap.add_argument("--road", choices=ROADS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--lorry")
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


ASP_RULES = r"""
reason_ok(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid(R, C, F) :- road(R), cargo(C), fix(F), reason_ok(F), steep(R, SR), heavy(C, HC), power(F, P), P >= SR + HC / 2.
outcome(triumphant) :- valid(R, C, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, r in ROADS.items():
        lines.append(asp.fact("road", rid))
        lines.append(asp.fact("steep", rid, r.steep))
    for cid, c in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        lines.append(asp.fact("heavy", cid, c.heavy))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    for p in CURATED:
        try:
            _ = generate(p)
        except Exception as exc:
            print(f"CURATED GENERATION FAILED: {exc}")
            rc = 1
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
