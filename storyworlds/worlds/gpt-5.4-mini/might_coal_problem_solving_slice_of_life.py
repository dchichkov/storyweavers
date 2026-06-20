#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/might_coal_problem_solving_slice_of_life.py
===========================================================================

A standalone storyworld for a small slice-of-life problem-solving tale built
from the seed words "might" and "coal".

Premise:
- A child and a grown-up notice a small household problem involving coal.
- They think through the mess, test a simple fix, and settle on a careful plan.

The domain is intentionally small:
- a kitchen, porch, or backyard grill area
- a few typed entities with physical meters and emotional memes
- a reasonableness gate that only allows a believable fix
- a Python world model plus an inline ASP twin for parity checks

The story style is slice of life: concrete, gentle, domestic, and child-facing.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
COAL_DUST = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "clean": 0.0})
    memes: dict[str, float] = field(default_factory=dict)

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
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    name: str
    place: str
    surface: str
    cozy_detail: str
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
class Problem:
    id: str
    label: str
    sentence: str
    source: str
    spill: str
    risk: str
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
class Fix:
    id: str
    label: str
    action: str
    result: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.kind != "thing":
            continue
        if ent.meters.get("coal_dust", 0.0) < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "floor" in world.entities:
            world.get("floor").meters["mess"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["concern"] = e.memes.get("concern", 0.0) + 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill)]


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


def reasonableness_gate(problem: Problem, fix: Fix) -> bool:
    return problem.id == "coal_bucket" and fix.power >= 1


def fix_can_help(problem: Problem, fix: Fix) -> bool:
    return problem.id == "coal_bucket" and fix.power >= 1


def predict_problem(world: World, problem: Problem) -> dict:
    sim = world.copy()
    _do_problem(sim, narrate=False)
    return {
        "mess": sim.get("floor").meters.get("mess", 0.0),
        "concern": sum(e.memes.get("concern", 0.0) for e in sim.entities.values() if e.kind == "character"),
    }


def _do_problem(world: World, narrate: bool = True) -> None:
    bucket = world.get("coal")
    bucket.meters["coal_dust"] += 1
    bucket.meters["mess"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, adult: Entity, setting: Setting, problem: Problem) -> None:
    child.memes["curiosity"] = 1.0
    child.memes["care"] = 1.0
    adult.memes["patience"] = 1.0
    world.say(
        f"On a quiet afternoon, {child.id} and {adult.id} were in {setting.place}. "
        f"{setting.cozy_detail}"
    )
    world.say(
        f"{child.id} noticed {problem.sentence} and said, \"{problem.source}.\""
    )


def worry(world: World, adult: Entity, child: Entity, problem: Problem) -> None:
    pred = predict_problem(world, problem)
    adult.memes["concern"] = adult.memes.get("concern", 0.0) + 1
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f"{adult.id} looked closer. \"That coal might make a mess on the floor,\" "
        f"{adult.pronoun()} said. \"Let's think of a simple way to clean it up.\""
    )


def test_fix(world: World, adult: Entity, fix: Fix) -> None:
    world.say(
        f"{adult.id} fetched {fix.label} and {fix.action}."
    )


def solve(world: World, child: Entity, adult: Entity, problem: Problem, fix: Fix) -> None:
    coal = world.get("coal")
    floor = world.get("floor")
    coal.meters["coal_dust"] = 0.0
    floor.meters["mess"] = 0.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    adult.memes["relief"] = adult.memes.get("relief", 0.0) + 1
    world.say(
        f"Together they used {fix.label}: {fix.result}. In a little while, the dark dust was gone."
    )
    world.say(
        f"{child.id} smiled and said, \"{child.id} thought we might need to try twice, but we did it.\""
    )
    world.say(
        f"By the end, the floor was tidy again, and the small coal problem was solved."
    )


def tell(setting: Setting, problem: Problem, fix: Fix, child_name: str = "Mina",
         child_type: str = "girl", adult_name: str = "Dad", adult_type: str = "father") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_type, role="adult"))
    world.add(Entity(id="floor", type="floor", label="the floor"))
    world.add(Entity(id="coal", type="thing", label="the coal bucket"))

    setup(world, child, adult, setting, problem)
    world.para()
    _do_problem(world)
    worry(world, adult, child, problem)
    world.para()
    test_fix(world, adult, fix)
    world.para()
    solve(world, child, adult, problem, fix)

    world.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        problem=problem,
        fix=fix,
        solved=True,
        mess_before=1.0,
    )
    return world


SETTINGS = {
    "porch": Setting(
        id="porch",
        name="front porch",
        place="the front porch",
        surface="wooden boards",
        cozy_detail="A warm mug sat nearby, and a pair of shoes waited by the door.",
        tags={"porch"},
    ),
    "kitchen": Setting(
        id="kitchen",
        name="kitchen",
        place="the kitchen",
        surface="tile floor",
        cozy_detail="A kettle hummed softly on the stove, and the afternoon light sat on the table.",
        tags={"kitchen"},
    ),
    "backyard": Setting(
        id="backyard",
        name="backyard",
        place="the backyard",
        surface="stone pavers",
        cozy_detail="A small chair stood by the door, and a bowl of apples waited for snack time.",
        tags={"backyard"},
    ),
}

PROBLEMS = {
    "coal_bucket": Problem(
        id="coal_bucket",
        label="coal bucket",
        sentence="a little pile of coal dust had spilled from the bucket",
        source="It might stain the floor",
        spill="coal dust",
        risk="messy marks",
        tags={"coal", "mess"},
    ),
}

FIXES = {
    "broom_pan": Fix(
        id="broom_pan",
        label="a broom and dustpan",
        action="swept the dust into a neat little pile",
        result="they swept the coal dust into the dustpan and carried it to the bin",
        power=1,
        tags={"cleaning", "coal"},
    ),
    "damp_cloth": Fix(
        id="damp_cloth",
        label="a damp cloth",
        action="wiped the floor carefully",
        result="they wiped the black dust away before it could spread",
        power=1,
        tags={"cleaning", "coal"},
    ),
    "tray": Fix(
        id="tray",
        label="a shallow tray",
        action="slid the bucket onto a tray",
        result="they moved the bucket onto a tray so the dust stayed in one spot",
        power=1,
        tags={"cleaning", "coal"},
    ),
}

CHILD_NAMES = ["Mina", "Tessa", "Ruby", "Owen", "Leo", "Nina", "Theo", "Luna"]
ADULT_NAMES = ["Mom", "Dad", "Aunt Jo", "Grandma", "Grandpa"]



@dataclass
class StoryParams:
    setting: str
    problem: str
    fix: str
    child_name: str
    child_gender: str
    adult_name: str
    adult_type: str
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

CURATED = [
    ("porch", "coal_bucket", "broom_pan", "Mina", "girl", "Dad", "father"),
    ("kitchen", "coal_bucket", "damp_cloth", "Owen", "boy", "Mom", "mother"),
    ("backyard", "coal_bucket", "tray", "Luna", "girl", "Grandma", "grandmother"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, f) for s in SETTINGS for p in PROBLEMS for f in FIXES if reasonableness_gate(PROBLEMS[p], FIXES[f])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life problem solving storyworld about coal and small fixes.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--adult-type", choices=["mother", "father", "grandmother", "grandfather"])
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
    if args.problem and args.fix and not reasonableness_gate(PROBLEMS[args.problem], FIXES[args.fix]):
        raise StoryError("No story: that fix does not really solve this coal problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.problem is None or c[1] == args.problem)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, problem, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    adult_name = args.adult or rng.choice(ADULT_NAMES)
    adult_type = args.adult_type or ("mother" if adult_name in {"Mom", "Aunt Jo", "Grandma"} else "father")
    return StoryParams(setting, problem, fix, child_name, gender, adult_name, adult_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the words "might" and "coal".',
        f"Tell a gentle problem-solving story about {f['child'].id} and {f['adult'].id} cleaning up coal at {f['setting'].place}.",
        f"Write a small family story where someone says the coal {f['problem'].spill} {f['problem'].risk} and they choose a careful fix.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    setting = f["setting"]
    problem = f["problem"]
    fix = f["fix"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {adult.id} in {setting.place}. They are handling a small household problem together."),
        ("What problem did they notice?",
         f"They noticed that {problem.sentence}. {adult.id} thought it might stain the floor, so they paused and looked for a safe fix."),
        ("How did they solve it?",
         f"They used {fix.label} and worked together. That careful step kept the coal from making a bigger mess."),
    ]
    return qa


KNOWLEDGE = {
    "coal": [("What is coal?",
              "Coal is a black rock that can burn for heat. It is messy when its dust spills, so people keep it tidy.")],
    "broom": [("What does a broom do?",
               "A broom sweeps crumbs and dust into a pile so they are easier to clean up.")],
    "dustpan": [("What is a dustpan?",
                   "A dustpan is a shallow pan that holds swept-up dirt until you can throw it away.")],
    "cloth": [("Why can a cloth help clean a floor?",
                "A cloth can wipe up dust and small spills. A damp cloth can grab tiny bits that a dry broom might leave behind.")],
    "tray": [("What is a tray for?",
              "A tray is a flat pan that helps carry things without spilling them.")],
    "might": [("What does the word 'might' mean?",
               "Might means something could happen, but it is not certain yet.")],
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["problem"].tags) | set(world.facts["fix"].tags) | {"might"}
    out: list[tuple[str, str]] = []
    for key in ["might", "coal", "broom", "dustpan", "cloth", "tray"]:
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
problem(P) :- problem_id(P).
fix(F) :- fix_id(F).
valid(S,P,F) :- setting(S), problem(P), fix(F), reasonableness(P,F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix_id", fid))
    lines.append(asp.fact("reasonableness", "coal_bucket", "broom_pan"))
    lines.append(asp.fact("reasonableness", "coal_bucket", "damp_cloth"))
    lines.append(asp.fact("reasonableness", "coal_bucket", "tray"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, fix=None, name=None, gender=None, adult=None, adult_type=None), random.Random(7)))
        _ = sample.story
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    else:
        print("OK: generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PROBLEMS[params.problem], FIXES[params.fix], params.child_name, params.child_gender, params.adult_name, params.adult_type)
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

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*p)) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child_name} and {p.adult_name}: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
