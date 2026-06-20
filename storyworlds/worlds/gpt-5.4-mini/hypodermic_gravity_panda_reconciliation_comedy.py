#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypodermic_gravity_panda_reconciliation_comedy.py
==================================================================================

A standalone storyworld for a tiny comedy about a panda, a hypodermic, gravity,
and reconciliation.

Premise
-------
A small panda tries to be clever with a pretend "medicine launcher" during a
playful kitchen science game. Gravity makes the joke backfire: the soft toy rolls
away, a mess starts, and two friends fall out for a moment. A calm adult or a
kind friend helps them clean up, admit the mistake, and make peace with a silly
new plan that is safe and funny.

This world is built to satisfy the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen paragraph
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in world state
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
MIN_SENSE = 2
MAX_GRAVITY = 10

NAMES = ["Pip", "Milo", "Nina", "Toby", "Ruby", "Ollie", "Mara", "Zed"]
PANDA_NAMES = ["Panda", "Poppy", "Paco", "Pudding"]
COMFORT_ITEMS = ["a red scarf", "a blue cap", "a tiny bell", "a striped ribbon"]


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    label: str
    kind: str
    gravity: int
    comedic: bool = True
    unsafe: bool = False


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    adult: str
    adult_type: str
    item: str
    response: str
    gravity: int
    seed: Optional[int] = None


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("fall", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["fallen"] += 1
        out.append("__fall__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if world.entities.get("bowl", None) and world.get("bowl").meters["spilled"] >= THRESHOLD:
        sig = ("spill", "bowl")
        if sig not in world.fired:
            world.fired.add(sig)
            if "floor" in world.entities:
                world.get("floor").meters["sticky"] += 1
            for e in world.entities.values():
                if e.kind == "character":
                    e.memes["surprise"] += 1
            out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("fall", _r_fall), Rule("spill", _r_spill)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            msgs = rule.apply(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if not m.startswith("__"))
    if narrate:
        for msg in produced:
            world.say(msg)
    return produced


def reason_gate(item: Item, gravity: int) -> bool:
    return item.unsafe and gravity >= 4


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= MIN_SENSE]


def story_outcome(params: StoryParams) -> str:
    return "reconcile" if RESPONSES[params.response].power >= params.gravity else "mess"


def predict(world: World, gravity: int) -> dict:
    sim = world.copy()
    sim.get("panda").meters["wobble"] += gravity / 2
    sim.get("panda").meters["wobble"] += 1
    propagate(sim, narrate=False)
    return {"fall": sim.get("panda").meters["fallen"] >= THRESHOLD,
            "sticky": sim.get("floor").meters["sticky"] >= THRESHOLD if "floor" in sim.entities else False}


def setup(world: World, hero: Entity, friend: Entity, adult: Entity, item: Item) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} the panda and {friend.id} were trying a silly science game. "
        f"They called the fancy toy a {item.label}, even though it was only pretend."
    )
    world.say(
        f'{hero.id} grinned. "{item.label.capitalize()}!" {hero.id} chirped, and {friend.id} laughed so hard '
        f"that {friend.pronoun('possessive')} snack nearly wiggled off the table."
    )


def temptation(world: World, hero: Entity, item: Item) -> None:
    hero.memes["bold"] += 1
    world.say(
        f"{hero.id} wanted to aim the {item.label} at the paper cup tower. It sounded dramatic, like a tiny hero move."
    )


def warn(world: World, friend: Entity, hero: Entity, item: Item, adult: Entity, gravity: int) -> None:
    friend.memes["care"] += 1
    world.facts["predicted"] = predict(world, gravity)
    world.say(
        f'{friend.id} tilted {friend.pronoun("possessive")} head. "{hero.id}, that looks wobbly. '
        f'{adult.label.capitalize()} said no pointy pretending."'
    )
    world.say(
        f"{friend.id} also glanced at the table edge. Gravity liked to win arguments with anything not held still."
    )


def ignore(world: World, hero: Entity, item: Item) -> None:
    hero.memes["defiance"] += 1
    world.say(f'"Nonsense," {hero.id} said, trying to be brave in a way that was mostly comedy.')
    world.say(f"{hero.id} reached for the {item.label} anyway.")


def slip(world: World, item: Item, gravity: int) -> None:
    world.get("panda").meters["wobble"] += gravity / 2
    world.get("panda").meters["gravity_pull"] += gravity
    world.get("bowl").meters["spilled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The {item.label} tipped, the bowl slid, and gravity won with a slapstick thunk. "
        f"One spoon spun away like it had its own secret schedule."
    )


def quarrel(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["embarrassment"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"{friend.id} frowned, and {hero.id} frowned back. For a tiny moment, the room felt grumpy and too quiet."
    )


def reconcile(world: World, hero: Entity, friend: Entity, adult: Entity, item: Item) -> None:
    hero.memes["remorse"] += 1
    friend.memes["forgiveness"] += 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then {hero.id} took a breath, looked at {friend.id}, and said, "
        f'"I was showing off. I am sorry."'
    )
    world.say(
        f'{friend.id} blinked, then snorted a little laugh. "{hero.id}, you are a panda. '
        f'Pandas are already funny."'
    )
    world.say(
        f"{adult.label.capitalize()} helped wipe up the mess and said, "
        f'"A good apology is better than a perfect trick."'
    )
    world.say(
        f"{hero.id} and {friend.id} bumped shoulders, built the cup tower again, and this time they used the {item.label} as a pretend wand instead."
    )


def ending(world: World, hero: Entity, friend: Entity, adult: Entity, item: Item) -> None:
    world.say(
        f"At the end, the floor was clean, the cup tower stood straight, and the {item.label} was tucked safely on the shelf."
    )
    world.say(
        f"{hero.id} was still a panda, gravity was still gravity, and everyone was laughing together again."
    )


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(params.hero, kind="character", type=params.hero_type, role="hero"))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend_type, role="friend"))
    adult = world.add(Entity(params.adult, kind="character", type=params.adult_type, role="adult", label="the grown-up"))
    world.add(Entity("floor", type="thing", label="the floor"))
    world.add(Entity("bowl", type="thing", label="the bowl"))

    item = ITEMS[params.item]

    setup(world, hero, friend, adult, item)
    world.para()
    temptation(world, hero, item)
    warn(world, friend, hero, item, adult, params.gravity)
    ignore(world, hero, item)
    slip(world, item, params.gravity)
    quarrel(world, hero, friend)
    world.para()
    if story_outcome(params) == "reconcile":
        reconcile(world, hero, friend, adult, item)
    else:
        world.say(
            f"{adult.label.capitalize()} tried to calm things down, but the joke had turned into a bigger mess than expected."
        )
        world.say(
            f"{hero.id} and {friend.id} cleaned up in silence first, then apologized and made up once the floor was safe."
        )
        world.say(
            f"By the end they were friends again, though the cup tower had become a wobbly memory."
        )
    ending(world, hero, friend, adult, item)
    world.facts.update(hero=hero, friend=friend, adult=adult, item=item, params=params,
                       outcome=story_outcome(params), predicted=world.facts.get("predicted", {}))
    return world


THEME = "comedy reconciliation with a panda and a gravity mishap"

ITEMS = {
    "hypodermic": Item("hypodermic", "hypodermic", "toy", gravity=6, unsafe=True),
    "feather": Item("feather", "feather", "toy", gravity=1),
    "spray": Item("spray", "spray bottle", "toy", gravity=2),
}

RESPONSES = {
    "apologize": Response("apologize", 3, 6,
                          "helped them both laugh, clean up, and apologize to each other",
                          "tried to apologize, but the joke was already too tangled to untwist",
                          "apologized, cleaned up, and made peace"),
    "giggle": Response("giggle", 2, 5,
                       "laughed, then reset the mess and made up",
                       "laughed, but the mess stayed sticky",
                       "laughed, reset the mess, and made up"),
    "ignore": Response("ignore", 1, 1,
                       "shrugged and hoped gravity would be polite",
                       "ignored the problem, but gravity was not polite at all",
                       "ignored the problem"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for rid, resp in RESPONSES.items():
            if reason_gate(item, item.gravity) and resp.sense >= MIN_SENSE:
                combos.append(("kitchen", item_id, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny comedy storyworld with a panda, gravity, and reconciliation.")
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.item not in ITEMS:
        raise StoryError("Unknown item.")
    if args.item and not reason_gate(ITEMS[args.item], ITEMS[args.item].gravity):
        raise StoryError("That item is too harmless for the comedy mishap.")

    combos = [c for c in valid_combos() if args.item is None or c[1] == args.item]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, item_id, response_id = rng.choice(combos)
    hero = rng.choice(PANDA_NAMES)
    friend = rng.choice([n for n in NAMES if n != hero])
    adult = rng.choice(["Mina", "June", "Parker", "Sage"])
    hero_type = "panda"
    friend_type = rng.choice(["girl", "boy"])
    adult_type = rng.choice(["mother", "father", "woman", "man"])
    gravity = ITEMS[item_id].gravity
    if args.response:
        response_id = args.response
    return StoryParams(hero, hero_type, friend, friend_type, adult, adult_type, item_id, response_id, gravity)


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
    item = f["item"].label
    return [
        f'Write a funny story for a young child that includes the words "hypodermic", "gravity", and "panda".',
        f"Tell a comedy story where {f['hero'].id} the panda gets into trouble with a {item} and learns to apologize.",
        f"Write a reconciliation story with a silly gravity mishap, a panda, and a friendly ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    item = f["item"]
    pred = f.get("predicted", {})
    return [
        ("Who is the story about?",
         f"It is about {hero.id} the panda, {friend.id}, and {adult.label}. The joke goes wrong and they have to make up."),
        ("Why did the trouble happen?",
         f"{hero.id} tried to use the {item.label} like a dramatic toy, but gravity made everything slide and wobble. That is why the silly plan turned into a mess."),
        ("How did they fix the friendship?",
         f"{hero.id} apologized, {friend.id} laughed, and {adult.label} helped them clean up. Then they rebuilt the game in a safer, funnier way."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a panda?",
         "A panda is a bear with black and white fur. Pandas like bamboo and are often seen as gentle and funny."),
        ("What does gravity do?",
         "Gravity pulls things down toward the ground. That is why dropped things fall and why wobbly piles tip over."),
        ("What should you do after you upset a friend?",
         "Say sorry, listen, and help fix the problem. A good apology can help everyone feel better."),
    ]


ASP_RULES = r"""
valid_combo(kitchen, I, R) :- item(I), response(R), unsafe(I), sense(R, S), sense_min(M), S >= M.
outcome(reconcile) :- chosen_item(I), unsafe(I), chosen_response(R), power(R, P), item_gravity(I, G), P >= G.
outcome(mess) :- chosen_item(I), unsafe(I), chosen_response(R), power(R, P), item_gravity(I, G), P < G.
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", MIN_SENSE)]
    for i, item in ITEMS.items():
        lines.append(asp.fact("item", i))
        lines.append(asp.fact("item_gravity", i, item.gravity))
        if item.unsafe:
            lines.append(asp.fact("unsafe", i))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, resp.sense))
        lines.append(asp.fact("power", r, resp.power))
    return "\n".join(lines)

def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))

def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc

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
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
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
    StoryParams("Panda", "panda", "Nina", "girl", "Mina", "mother", "hypodermic", "apologize", 6),
    StoryParams("Poppy", "panda", "Toby", "boy", "June", "father", "hypodermic", "giggle", 5),
]

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid_combo/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
