#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py
=================================================================================

A standalone storyworld about a small mystery in a hardware store: a curious
child notices a muddy trail, a kind helper follows the clues, and the surprising
ending reveals that the "mystery" was just soil from a cracked plant pot and a
careful, helpful cleanup.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- state-driven prose, not frozen template swapping
- a reasonableness gate plus inline ASP twin
- three Q&A sets grounded in world state

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py --all
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py --trace
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py --json
    python storyworlds/worlds/gpt-5.4-mini/soil_hardware_store_kindness_curiosity_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

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

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)



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
    kind: str = "hardware store"
    has_soil: bool = True
    has_planter: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Clue:
    id: str
    label: str
    hint: str
    soil_source: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class Fix:
    id: str
    label: str
    action: str
    cleanup: str
    good: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_mud(world: World) -> list[str]:
    out: list[str] = []
    trail = world.get("trail")
    if trail.meters.get("soil", 0) >= THRESHOLD and ("mud", "trail") not in world.fired:
        world.fired.add(("mud", "trail"))
        trail.memes["mystery"] = trail.memes.get("mystery", 0) + 1
        out.append("__mystery__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    trail = world.get("trail")
    child = world.get("child")
    if trail.memes.get("mystery", 0) >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
        out.append("__curious__")
    return out


CAUSAL_RULES = [_r_mud, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_scene(place: Place, clue: Clue) -> bool:
    return place.has_soil and clue.soil_source


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: f.good)


def choose_fix() -> list[Fix]:
    return [f for f in FIXES.values() if f.good >= 2]


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


PLACES = {
    "hardware_store": Place("hardware_store", "the hardware store"),
}

CLUES = {
    "soil": Clue("soil", "soil", "a little trail of soil", soil_source=True),
}

FIXES = {
    "plant_pot": Fix("plant_pot", "a cracked plant pot", "carefully lifted the broken pot", "swept the soil into a dustpan", 3, {"cleanup"}),
    "bag": Fix("bag", "a torn bag of potting soil", "tied the bag shut and placed it in a cart", "wiped up the spilled soil", 2, {"cleanup"}),
    "scoop": Fix("scoop", "a small scoop and brush", "used the scoop and brush", "cleaned the path in tiny strokes", 3, {"cleanup"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Eli", "Max"]


def scene_text(place: Place, clue: Clue) -> str:
    return (
        f"{place.label} smelled like wood, metal, and rain from people's boots. "
        f"Near the garden aisle, {clue.label} made a little brown line on the floor."
    )


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("trail").meters["soil"] = 1
    propagate(sim, narrate=False)
    return {"mystery": sim.get("trail").memes.get("mystery", 0), "curiosity": sim.get("child").memes.get("curiosity", 0)}


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity("child", "character", params.child_gender, params.child_name, "child", ["kind", "curious"], {"curiosity": 0}, {"kindness": 1}))
    helper = world.add(Entity("helper", "character", params.helper_gender, params.helper_name, "helper", ["kind"], {"kindness": 1}, {"kindness": 2}))
    trail = world.add(Entity("trail", "thing", "trail", "the trail", "trail", [], {"soil": 0.0}, {"mystery": 0.0}))
    pot = world.add(Entity("pot", "thing", "pot", "the plant pot"))
    store = world.add(Entity("store", "place", "place", PLACES[params.place].label))
    clue = CLUES[params.clue]
    fix = FIXES[params.fix]

    world.say(
        f"{child.id} and {helper.id} were at {store.label}. "
        f"{child.id} noticed something strange first: {clue.label} near the garden aisle."
    )
    world.say(
        f'"Look," said {child.id}, "there is a little mystery here." '
        f'{helper.id} knelt down with a gentle smile and looked too.'
    )

    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    trail.meters["soil"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"{helper.id} followed the clue and found the answer: {fix.label}. "
        f"{helper.id} said it probably tipped and left the {clue.label} behind."
    )
    world.say(
        f"Together they {fix.action}, and then {fix.cleanup}."
    )

    trail.meters["soil"] = 0
    trail.memes["mystery"] = 0
    child.memes["curiosity"] += 1
    helper.memes["kindness"] += 1

    world.para()
    world.say(
        f"In the end, the floor was clean, the aisle was calm, and the little mystery was solved. "
        f"{child.id} smiled because being curious had helped, and {helper.id} smiled because kindness had made the answer easy to find."
    )

    world.facts.update(
        child=child,
        helper=helper,
        trail=trail,
        place=store,
        clue=clue,
        fix=fix,
        solved=True,
        ending="solved",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story set in {f["place"].label} that includes the word "{f["clue"].label}".',
        f"Tell a short story where {f['child'].id} is curious about a little mess in a hardware store and a kind helper solves the mystery.",
        "Write a gentle mystery with a clean ending, a clue, kindness, and curiosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    clue = f["clue"]
    fix = f["fix"]
    return [
        QAItem(
            question="What did the child notice in the store?",
            answer=f"{child.id} noticed a little {clue.label} trail near the garden aisle. That was the clue that made the scene feel like a mystery."
        ),
        QAItem(
            question="How did the helper solve the problem?",
            answer=f"{helper.id} found {fix.label}, explained what had happened, and helped clean up the soil. The kindness made the answer calm and easy."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with a clean floor and a solved mystery. The child stayed curious, and the helper stayed kind."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soil?",
            answer="Soil is the dark earth where plants grow. It can spill into a little pile or a trail if something tips over."
        ),
        QAItem(
            question="What is a hardware store?",
            answer="A hardware store is a shop that sells tools, paint, screws, buckets, and other things people use to fix and build."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means helping gently, using calm words, and making things better for someone else."
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look closely and ask questions to figure out how something works."
        ),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in PLACES.values():
        for clue in CLUES.values():
            for fix in FIXES.values():
                if valid_scene(place, clue):
                    out.append((place.id, clue.id, fix.id))
    return out


ASP_RULES = r"""
valid(P, C, F) :- place(P), clue(C), fix(F), soil_scene(P, C).
outcome(solved) :- valid_scene.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_soil:
            lines.append(asp.fact("soil_scene", pid, "soil"))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    clue: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    ap = argparse.ArgumentParser(description="A tiny hardware-store mystery world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid mystery scenes exist.")
    combo = [c for c in combos if (args.place is None or c[0] == args.place)
             and (args.clue is None or c[1] == args.clue)
             and (args.fix is None or c[2] == args.fix)]
    if not combo:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, fix = rng.choice(sorted(combo))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if gender == "girl" else "girl")
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    if helper_name == child_name:
        helper_name = "Jules"
    return StoryParams(place, clue, fix, child_name, gender, helper_name, helper_gender)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams("hardware_store", "soil", "plant_pot", "Mia", "girl", "Jules", "girl"),
    StoryParams("hardware_store", "soil", "scoop", "Leo", "boy", "Nora", "girl"),
    StoryParams("hardware_store", "soil", "bag", "Ava", "girl", "Ben", "boy"),
]


def asp_verify() -> int:
    import asp
    c = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if c == p:
        print(f"OK: gate matches valid_combos() ({len(c)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
        print("only in clingo:", sorted(c - p))
        print("only in python:", sorted(p - c))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.world is not None
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for x in asp_valid_combos():
            print(" ", x)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
