#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/burger_teamwork_sound_effects_repetition_comedy.py
===================================================================================

A tiny standalone storyworld about a burger night where teamwork, sound effects,
and repetition turn a kitchen scramble into a funny, satisfying success.

Seed words:
- burger
- Teamwork
- Sound Effects
- Repetition
- Style: Comedy
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class World:
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


@dataclass
class TeamSetup:
    place: str
    task: str
    sound: str
    repeat: str
    ending: str

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
    setup: str
    chef_name: str
    helper_name: str
    chef_gender: str
    helper_gender: str
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


SETUPS = {
    "diner": TeamSetup("a tiny diner kitchen", "build the burger before the lunch crowd got grumpy", "sizzle", "Again!", "stacked and ready"),
    "food_truck": TeamSetup("a tiny food truck kitchen", "finish the burger before the bell rang", "splat", "One more time!", "wrapped and happy"),
    "backyard": TeamSetup("a little backyard cookout", "make the burger before the picnic guests got hungry", "pop", "Again and again!", "passed around with smiles"),
}

CHEF_NAMES = ["Mia", "Noah", "Luna", "Ben", "Ava", "Finn", "Ivy", "Leo"]
HELPER_NAMES = ["Tess", "Oli", "Pip", "Zoe", "Max", "Nia", "Bea", "Sam"]


class RuleBook:
    pass


def _r_sizzle(world: World) -> list[str]:
    out = []
    burger = world.entities.get("burger")
    pan = world.entities.get("pan")
    if not burger or not pan:
        return out
    if burger.meters["on_grill"] < THRESHOLD:
        return out
    sig = ("sizzle",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    burger.meters["hot"] += 1
    burger.memes["excitement"] += 1
    out.append("__sizzle__")
    return out


def _r_stack(world: World) -> list[str]:
    burger = world.entities.get("burger")
    if not burger or burger.meters["hot"] < THRESHOLD:
        return []
    sig = ("stack",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    burger.meters["assembled"] += 1
    burger.memes["pride"] += 1
    return ["__stack__"]


CAUSAL_RULES: list[Rule] = [
    Rule("sizzle", "physical", _r_sizzle),
    Rule("stack", "physical", _r_stack),
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


def predict_burger(world: World) -> dict:
    sim = world.copy()
    burger = sim.get("burger")
    burger.meters["on_grill"] += 1
    propagate(sim, narrate=False)
    return {
        "hot": sim.get("burger").meters["hot"] >= THRESHOLD,
        "assembled": sim.get("burger").meters["assembled"] >= THRESHOLD,
    }


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy burger teamwork storyworld.")
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--chef")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combos() -> list[tuple[str]]:
    return [(k,) for k in SETUPS]


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setup", k) for k in SETUPS]
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S) :- setup(S).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
    except Exception as err:  # noqa: BLE001
        print(f"MISMATCH: smoke test failed: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    setup = args.setup or rng.choice([c[0] for c in combos])
    chef = args.chef or rng.choice(CHEF_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != chef])
    chef_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    return StoryParams(setup, chef, helper, chef_gender, helper_gender)


def tell(params: StoryParams) -> World:
    setup = SETUPS[params.setup]
    world = World()
    chef = world.add(Entity(params.chef_name, kind="character", type=params.chef_gender, role="chef", traits=["busy"]))
    helper = world.add(Entity(params.helper_name, kind="character", type=params.helper_gender, role="helper", traits=["quick"]))
    burger = world.add(Entity("burger", type="food", label="burger"))
    pan = world.add(Entity("pan", type="thing", label="pan"))
    burger.meters["assembled"] += 0
    world.say(
        f"On a busy day in {setup.place}, {chef.id} and {helper.id} were making a burger for everybody."
    )
    world.say(
        f'{chef.id} said, "Bun, burger, bun. Burger, bun, burger!" '
        f'{helper.id} said, "I have the top bun! I have the top bun!"'
    )
    world.para()
    world.say(
        f'The pan went "{setup.sound}! {setup.sound}!" and the kitchen smelled like lunch was winning.'
    )
    world.say(
        f'But the burger wobbled like a sleepy stack of pancakes. "{setup.repeat} {setup.repeat}" said {helper.id}, '
        f'grabbing the spatula while {chef.id} held the bun.'
    )
    burger.meters["on_grill"] += 1
    propagate(world)
    world.para()
    world.say(
        f"Then the two friends worked together: one flipped, one stacked, and the burger turned out {setup.ending}."
    )
    world.say(
        f'{chef.id} laughed, {helper.id} laughed, and the burger landed on the plate with a cheerful little thump.'
    )
    world.say(
        f'"Burger for the team!" they cheered, and the whole kitchen cheered back.'
    )
    world.facts.update(
        chef=chef, helper=helper, burger=burger, pan=pan, setup=params.setup, setup_cfg=setup
    )
    return world


def generate(params: StoryParams) -> StorySample:
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
    setup = f["setup_cfg"]
    return [
        f'Write a funny teamwork story for a young child about a burger in {setup.place}.',
        f'Tell a comedy story where two helpers make a burger, use repeated lines, and include a loud sound effect.',
        f'Write a short child-friendly story that says "{setup.repeat}" more than once and ends with a happy burger.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    chef, helper, burger, setup = f["chef"], f["helper"], f["burger"], f["setup_cfg"]
    return [
        ("Who worked together in the story?",
         f"{chef.id} and {helper.id} worked together as a team to make the burger."),
        ("What sound did the kitchen make?",
         f'The pan went "{setup.sound}! {setup.sound}!" while they cooked. That noisy sound made the story feel funny and busy.'),
        ("How did the burger get finished?",
         f"{chef.id} held the bun while {helper.id} used the spatula, so the burger ended up {setup.ending}."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a burger?",
         "A burger is a sandwich with a cooked patty and a bun, and people often add toppings like lettuce or cheese."),
        ("What does teamwork mean?",
         "Teamwork means people help each other do a job together. When everyone has a part, the job can feel easier and more fun."),
        ("What is a sound effect in a story?",
         "A sound effect is a fun word or phrase that sounds like a noise, such as sizzle, pop, or thump."),
        ("Why do writers repeat words sometimes?",
         "Writers repeat words to make the story funny, musical, or easy to remember. Repetition can also sound excited or silly."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)]]
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
    StoryParams("diner", "Mia", "Tess", "girl", "girl"),
    StoryParams("food_truck", "Ben", "Oli", "boy", "boy"),
    StoryParams("backyard", "Ava", "Pip", "girl", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible setups:")
        for (s,) in asp_valid_combos():
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
