#!/usr/bin/env python3
"""
A standalone story world for a slice-of-life fettuccine scene with sound effects.

Premise:
A child wants to make and eat fettuccine, but the kitchen process is full of tiny
noises and small mishaps. A careful helper turns the moment into a cozy,
successful evening.

The world model tracks:
- physical state in meters: noodles, sauce, steam, bowl warmth, mess
- emotional state in memes: hunger, patience, delight, worry, pride

The story is generated from simulated causality, not a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

SOUND_EFFECTS = {
    "boil": "glug-glug-glug",
    "drain": "swishhh",
    "stir": "tink-tink",
    "sauce": "splish",
    "slurp": "sluuurp",
    "sizzle": "tssss",
    "lid": "clack",
    "fork": "tap-tap",
}

PASTA_SHAPES = {
    "fettuccine": {
        "label": "fettuccine",
        "description": "wide, ribbon-like noodles",
        "cook_sound": "glug-glug-glug",
        "eat_sound": "sluuurp",
    }
}

TASKS = {
    "cook": "cook the fettuccine",
    "mix": "mix the sauce",
    "serve": "serve dinner",
}

KITCHENS = {
    "home": "the kitchen at home",
    "grandma": "Grandma's kitchen",
    "apartment": "the tiny apartment kitchen",
}

HELPERS = {
    "mom": "mom",
    "dad": "dad",
    "grandma": "Grandma",
    "older_sibling": "older sister",
}

NAMES = {
    "child": ["Mia", "Leo", "Nora", "Ben", "Luna", "Ivy", "Theo", "Ava"],
    "helper": ["Mom", "Dad", "Grandma", "Auntie"],
}

TRAITS = ["curious", "helpful", "patient", "bouncy", "quiet", "cheerful"]


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom", "grandma", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class KitchenConfig:
    place: str = "the kitchen at home"
    counter_height: str = "low"
    has_timer: bool = True
    has_big_pan: bool = True


@dataclass
class PastaConfig:
    name: str = "fettuccine"
    sauce: str = "butter and cheese"
    shape: str = "wide"
    noodle_sound: str = "glug-glug-glug"
    eating_sound: str = "sluuurp"


@dataclass
class StoryParams:
    kitchen: str
    helper: str
    task: str
    child_name: str
    child_type: str
    child_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

class World:
    def __init__(self, kitchen: KitchenConfig, pasta: PastaConfig) -> None:
        self.kitchen = kitchen
        self.pasta = pasta
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.sound_events: list[str] = []
        self.time = "early evening"

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.kitchen, self.pasta)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        w.facts = dict(self.facts)
        w.sound_events = list(self.sound_events)
        w.time = self.time
        return w


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sound(name: str) -> str:
    return SOUND_EFFECTS[name]


def likely_reasonable(params: StoryParams) -> bool:
    if params.task not in TASKS:
        return False
    if params.helper not in HELPERS:
        return False
    if params.kitchen not in KITCHENS:
        return False
    return True


def choose_reasonable_task(rng: random.Random) -> str:
    return rng.choice(list(TASKS))


# ---------------------------------------------------------------------------
# Causal simulation
# ---------------------------------------------------------------------------

def make_noise(world: World, kind: str) -> None:
    if kind not in world.sound_events:
        world.sound_events.append(kind)


def boil_pasta(world: World, child: Entity) -> None:
    sig = ("boil", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.meters["steam"] = child.meters.get("steam", 0.0) + 1
    child.memes["excitement"] = child.memes.get("excitement", 0.0) + 1
    make_noise(world, "boil")
    world.say(f"The pot went {sound('boil')} as the water began to dance.")


def drain_pasta(world: World, helper: Entity) -> None:
    sig = ("drain", helper.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.meters["busy"] = helper.meters.get("busy", 0.0) + 1
    make_noise(world, "drain")
    world.say(f"Then the colander made a {sound('drain')} when the noodles came down.")


def stir_sauce(world: World, helper: Entity) -> None:
    sig = ("stir", helper.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    make_noise(world, "stir")
    world.say(f"The spoon went {sound('stir')} around the warm sauce in little circles.")


def serve_bowl(world: World, child: Entity, helper: Entity) -> None:
    sig = ("serve", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.meters["hunger"] = max(0.0, child.meters.get("hunger", 0.0) - 1)
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    world.say("At last, the bowls were full and the table felt cozy and close.")


def slurp_eating(world: World, child: Entity) -> None:
    sig = ("eat", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["delight"] = child.memes.get("delight", 0.0) + 1
    make_noise(world, "slurp")
    world.say(f"{child.id} took one happy bite and made a tiny {sound('slurp')}.")


def warm_room(world: World) -> None:
    world.say("The kitchen smelled like butter, garlic, and a little bit of patience.")


def story_turn(world: World, child: Entity, helper: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"{child.id} wanted dinner right away, but the pasta still had to go through the whole little cooking dance."
    )
    world.say(
        f"{child.id} asked, 'Is it almost ready?' and {helper.id} smiled while the pot kept bubbling."
    )


def fix_the_wait(world: World, child: Entity, helper: Entity) -> None:
    child.memes["patience"] = child.memes.get("patience", 0.0) + 1
    child.memes["worry"] = 0.0
    helper.memes["tenderness"] = helper.memes.get("tenderness", 0.0) + 1
    world.say(
        f"{helper.id} let {child.id} sprinkle the cheese, and that made the waiting feel smaller."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    kitchen = KitchenConfig(place=KITCHENS[params.kitchen])
    pasta = PastaConfig(
        name="fettuccine",
        sauce="butter and cheese",
        shape="wide",
        noodle_sound=sound("boil"),
        eating_sound=sound("slurp"),
    )
    world = World(kitchen, pasta)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_type,
        meters={"hunger": 2.0},
        memes={"happiness": 1.0},
    ))
    helper = world.add(Entity(
        id=HELPERS[params.helper],
        kind="character",
        type=params.helper,
        label=HELPERS[params.helper],
        meters={"busy": 0.0},
        memes={"care": 1.0},
    ))
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="a blue bowl",
    ))

    world.facts.update(
        child=child,
        helper=helper,
        bowl=bowl,
        params=params,
        pasta=pasta,
        kitchen=kitchen,
    )

    # Beginning.
    world.say(f"It was {world.time} in {kitchen.place}, and {child.id} was hungry for dinner.")
    world.say(
        f"{child.id} loved fettuccine because the noodles were long and soft, and they made the kitchen feel like home."
    )
    world.say(
        f"{helper.id} had already set out a pot, a spoon, and the kind of sauce that smelled like comfort."
    )
    warm_room(world)

    # Middle.
    world.say(
        f"The water hit a boil with a cheerful {sound('boil')} and the noodles slid in like ribbons."
    )
    boil_pasta(world, child)
    story_turn(world, child, helper)
    stir_sauce(world, helper)
    drain_pasta(world, helper)
    fix_the_wait(world, child, helper)

    # Resolution.
    world.say(
        f"The fettuccine got folded into the sauce, and the whole bowl gave off a warm {sound('sauce')}."
    )
    serve_bowl(world, child, helper)
    slurp_eating(world, child)
    world.say(
        f"By the end, {child.id} sat with a happy smile, and the empty pot cooled quietly on the stove."
    )

    world.facts["resolved"] = True
    world.facts["sound_events"] = list(world.sound_events)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

KITCHENS_REGISTRY = {
    "home": KitchenConfig(place=KITCHENS["home"]),
    "grandma": KitchenConfig(place=KITCHENS["grandma"]),
    "apartment": KitchenConfig(place=KITCHENS["apartment"]),
}

CHILD_TYPES = ["girl", "boy"]
HELPER_TYPES = list(HELPERS)
TASKS_REGISTRY = list(TASKS)

CURATED = [
    StoryParams(kitchen="home", helper="mom", task="cook", child_name="Mia", child_type="girl", child_trait="curious"),
    StoryParams(kitchen="grandma", helper="grandma", task="serve", child_name="Leo", child_type="boy", child_trait="helpful"),
    StoryParams(kitchen="apartment", helper="dad", task="mix", child_name="Nora", child_type="girl", child_trait="patient"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    params: StoryParams = f["params"]
    return [
        f'Write a gentle slice-of-life story for a young child about fettuccine in {world.kitchen.place}.',
        f"Tell a small home story where {child.id} waits for dinner while {helper.id} makes fettuccine sound cozy and fun.",
        f'Write a story that includes the sound effects "{sound("boil")}" and "{sound("slurp")}" and ends with a happy bowl of pasta.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"Who wanted dinner right away in the story?",
            answer=f"{child.id} wanted dinner right away because the fettuccine smelled so good.",
        ),
        QAItem(
            question=f"What did {helper.id} help make in the kitchen?",
            answer=f"{helper.id} helped make fettuccine with a warm, cozy sauce.",
        ),
        QAItem(
            question="What sound did the boiling water make?",
            answer=f"The boiling water went {sound('boil')}.",
        ),
        QAItem(
            question="What happened at the end of the story?",
            answer=f"{child.id} ate the fettuccine happily and the kitchen grew quiet again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fettuccine?",
            answer="Fettuccine is a kind of pasta with long, flat noodles.",
        ),
        QAItem(
            question="Why does pasta get soft when it cooks?",
            answer="Pasta gets soft because hot water changes the dry noodles into tender cooked noodles.",
        ),
        QAItem(
            question="What does a boiling pot sound like?",
            answer="A boiling pot can sound like bubbling water, often with a glug-glug sound.",
        ),
        QAItem(
            question="Why do people stir sauce?",
            answer="People stir sauce so it heats evenly and does not stick to the pan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append("kind=character")
        lines.append(f"  {e.id}: {' '.join(bits) if bits else 'empty'}")
    lines.append(f"  sounds: {world.sound_events}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/3.

valid(K, T, H) :- kitchen(K), task(T), helper(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in KITCHENS_REGISTRY:
        lines.append(asp.fact("kitchen", k))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(k, t, h) for k in KITCHENS_REGISTRY for t in TASKS for h in HELPERS}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life fettuccine story world with sound effects.")
    ap.add_argument("--kitchen", choices=KITCHENS_REGISTRY)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--task", choices=TASKS_REGISTRY)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=CHILD_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = []
    for k in KITCHENS_REGISTRY:
        for h in HELPERS:
            for t in TASKS_REGISTRY:
                if args.kitchen and k != args.kitchen:
                    continue
                if args.helper and h != args.helper:
                    continue
                if args.task and t != args.task:
                    continue
                combos.append((k, h, t))
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    kitchen, helper, task = rng.choice(combos)
    child_type = args.child_type or rng.choice(CHILD_TYPES)
    child_name = args.name or rng.choice(NAMES["child"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        kitchen=kitchen,
        helper=helper,
        task=task,
        child_name=child_name,
        child_type=child_type,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if not likely_reasonable(params):
        raise StoryError("The requested story settings are not reasonable for this world.")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
            header = f"### {p.child_name}: fettuccine in {p.kitchen} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
