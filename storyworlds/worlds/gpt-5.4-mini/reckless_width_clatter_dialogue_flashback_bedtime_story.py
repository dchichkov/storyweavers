#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reckless_width_clatter_dialogue_flashback_bedtime_story.py
=========================================================================================

A standalone bedtime-story world about a sleepy child, a tiny nighttime bridge,
and the careful lesson that a bridge's width matters. The child remembers an
earlier warning in a brief flashback, hears a clatter in the dark, speaks with a
gentle adult in dialogue, and learns that reckless choices are not wise.

Seed words:
- reckless
- width
- clatter

Features:
- Dialogue
- Flashback

Style:
- Bedtime Story

This script follows the storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates a real simulated world, not a frozen paragraph template
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    width: int
    clatter_risk: int
    has_flashback_spot: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    fragile: bool
    noisy: bool
    falls_if_pushed: bool
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)


@dataclass
class Move:
    id: str
    sense: int
    balance: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


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


def _r_clatter(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    bridge = world.entities.get("bridge")
    if not child or not bridge:
        return out
    if child.meters["reckless"] < THRESHOLD:
        return out
    sig = ("clatter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bridge.meters["shaken"] += 1
    bridge.meters["danger"] += 1
    child.memes["startled"] += 1
    out.append("A sharp clatter woke the dark little bridge.")
    return out


def _r_warning(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["startled"] < THRESHOLD:
        return out
    sig = ("warning",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("The child held still and listened.")
    return out


CAUSAL_RULES = [Rule("clatter", "physical", _r_clatter), Rule("warning", "social", _r_warning)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bridge_is_safe(place: Place, move: Move) -> bool:
    return place.width >= move.balance


def sensible_moves() -> list[Move]:
    return [m for m in MOVES.values() if m.sense >= SENSE_MIN]


def best_move() -> Move:
    return max(MOVES.values(), key=lambda m: m.sense)


def would_reckless_fail(place: Place, move: Move) -> bool:
    return not bridge_is_safe(place, move)


def predict(world: World, move: Move) -> dict:
    sim = world.copy()
    _do_move(sim, sim.get("child"), move, narrate=False)
    return {
        "danger": sim.get("bridge").meters["danger"],
        "shaken": sim.get("bridge").meters["shaken"],
    }


def _do_move(world: World, child: Entity, move: Move, narrate: bool = True) -> None:
    child.meters["reckless"] += 1
    child.memes["hope"] += 1
    if narrate:
        world.say(move.text)
    if world.entities.get("bridge"):
        world.get("bridge").meters["crossing"] += 1
    if child.meters["reckless"] >= THRESHOLD:
        propagate(world, narrate=narrate)


def setup(world: World, child: Entity, parent: Entity, place: Place, bridge: Entity, item: ObjectThing) -> None:
    child.memes["sleepy"] += 1
    child.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.id} stepped into {place.label}, "
        f"where a little bridge crossed the dark water."
    )
    world.say(
        f"{child.id} noticed the bridge's narrow width and the soft {item.label} "
        f"waiting on the other side."
    )


def dialogue_choice(world: World, child: Entity, parent: Entity, move: Move, place: Place) -> None:
    world.say(
        f'"Can I hurry across?" asked {child.id}. "{parent.id}, I can make it!"'
    )
    world.say(
        f'"Slow feet are safer," {parent.id} said. "This bridge is only {place.width} steps wide."'
    )
    if child.meters["reckless"] >= THRESHOLD:
        world.say(f'{child.id} whispered, "I know... but I want to try anyway."')


def flashback(world: World, child: Entity, parent: Entity) -> None:
    child.memes["memory"] += 1
    world.say(
        f"For a tiny moment, {child.id} remembered another night, when {parent.id} "
        f"had shown {child.pronoun("object")} how to wait for a lantern before crossing."
    )
    world.say(
        f'The memory felt warm, like a blanket. "First be careful, then be brave," '
        f'{parent.id} had said.'
    )


def clatter_event(world: World, child: Entity, bridge: Entity, item: ObjectThing) -> None:
    world.say(
        f"{child.id} took one reckless step, and then another. The boards gave a clatter "
        f"under {child.pronoun('possessive')} shoes."
    )
    world.say(
        f"The bridge wobbled, and {item.label} rattled against the rail."
    )


def rescue(world: World, parent: Entity, move: Move, bridge: Entity, item: ObjectThing) -> None:
    parent.memes["calm"] += 1
    world.say(
        f'"Back to me," {parent.id} said. Then {parent.id} reached out and guided {item.label} '
        f"to the middle, where the bridge felt steadier."
    )
    if move.sense >= 2:
        world.say(
            f'Together they found the safer way: one hand on the rail, one slow step at a time.'
        )
    world.say(
        f"The clatter stopped, the water stayed quiet, and the little bridge rested still again."
    )


def ending(world: World, child: Entity, parent: Entity, place: Place, item: ObjectThing, safe: bool) -> None:
    if safe:
        child.memes["pride"] += 1
        child.memes["fear"] = 0.0
        world.say(
            f'At last {child.id} crossed safely, and {item.label} waited untouched under the soft night sky.'
        )
        world.say(
            f'{parent.id} smiled and tucked {child.id} closer. "Brave means using your head too," {parent.id} whispered.'
        )
    else:
        child.memes["fear"] += 1
        world.say(
            f'{parent.id} caught {child.id} before the widest step, and the little pair turned back home.'
        )
        world.say(
            f"That night, the bridge stayed on one side of the water, and sleep came easier once they were indoors."
        )


def tell(place: Place, item: ObjectThing, move: Move, child_name: str = "Mina", child_gender: str = "girl",
         parent_name: str = "Mara", parent_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity("child", kind="character", type=child_gender, label=child_name, role="child"))
    parent = world.add(Entity("parent", kind="character", type=parent_gender, label=parent_name, role="parent"))
    bridge = world.add(Entity("bridge", type="bridge", label="the bridge"))
    world.add(Entity("item", type="thing", label=item.label))
    setup(world, child, parent, place, bridge, item)
    world.para()
    dialogue_choice(world, child, parent, move, place)
    flashback(world, child, parent)
    if would_reckless_fail(place, move):
        world.para()
        child.meters["reckless"] += 1
        clatter_event(world, child, bridge, item)
        rescue(world, parent, move, bridge, item)
        ending(world, child, parent, place, item, safe=False)
        outcome = "warned"
    else:
        world.para()
        _do_move(world, child, move, narrate=False)
        world.say(
            f"{parent.id} let {child.id} try again, this time with slower steps and both hands near the rail."
        )
        world.say(
            f"The boards made only a tiny tap, and the night stayed peaceful."
        )
        ending(world, child, parent, place, item, safe=True)
        outcome = "safe"
    world.facts.update(place=place, item=item, move=move, child=child, parent=parent, outcome=outcome)
    return world


PLACES = {
    "narrow_footbridge": Place("narrow_footbridge", "a narrow footbridge", width=2, clatter_risk=3, tags={"bridge", "width"}),
    "garden_plank": Place("garden_plank", "a little garden plank bridge", width=3, clatter_risk=2, tags={"bridge", "width"}),
    "wide_boardwalk": Place("wide_boardwalk", "a wide boardwalk", width=5, clatter_risk=1, tags={"boardwalk", "width"}),
}

ITEMS = {
    "lantern": ObjectThing("lantern", "lantern", "a small lantern", fragile=True, noisy=False, falls_if_pushed=False, tags={"light"}),
    "basket": ObjectThing("basket", "basket", "a picnic basket", fragile=False, noisy=True, falls_if_pushed=True, tags={"basket"}),
    "teddy": ObjectThing("teddy", "teddy bear", "a soft teddy bear", fragile=False, noisy=False, falls_if_pushed=False, tags={"bedtime"}),
}

MOVES = {
    "rush": Move("rush", sense=1, balance=4, text="Mina rushed ahead with sleepy, reckless feet.", fail="could not steady the path", tags={"reckless"}),
    "slow": Move("slow", sense=3, balance=2, text="Mina breathed in and took a slow step.", fail="did not fit the bridge", tags={"careful"}),
    "careful": Move("careful", sense=4, balance=3, text="Mina placed one hand on the rail and crossed carefully.", fail="did not fit the bridge", tags={"careful"}),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Ella", "June"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Noah", "Owen", "Ben"]
TRAITS = ["sleepy", "curious", "gentle", "brave"]


@dataclass
class StoryParams:
    place: str
    item: str
    move: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, move in MOVES.items():
            for iid in ITEMS:
                if would_reckless_fail(place, move):
                    combos.append((pid, mid, iid))
    return combos


def explain_rejection(place: Place, move: Move) -> str:
    return (
        f"(No story: the move '{move.id}' is too careful for this particular bridge, "
        f"or the bridge is too wide for any clatter to matter. Pick a narrower bridge or a bolder move.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about width, clatter, dialogue, and flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
    if args.place and args.move:
        if not would_reckless_fail(PLACES[args.place], MOVES[args.move]):
            raise StoryError(explain_rejection(PLACES[args.place], MOVES[args.move]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.move is None or c[1] == args.move)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, move, item = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    parent_name = args.parent_name or rng.choice(["Mara", "Liam", "Sofia", "Noel"])
    trait = rng.choice(TRAITS)
    return StoryParams(place, item, move, child_name, gender, parent_name, parent_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, move, item = f["place"], f["move"], f["item"]
    return [
        f'Write a bedtime story for a child that includes the words "reckless", "width", and "clatter".',
        f"Tell a gentle story where {f['child'].id} wants to hurry across {place.label}, but {f['parent'].id} warns about the bridge's width and a clatter in the dark.",
        f"Write a story with dialogue and a flashback in which a sleepy child learns why reckless steps are unwise on a narrow bridge.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, parent, place, item, move = f["child"], f["parent"], f["place"], f["item"], f["move"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.label} and {parent.label}, who were crossing {place.label} at bedtime."),
        ("What made the child want to hurry?",
         f"{child.label} felt sleepy but also excited, so the idea of rushing across seemed reckless and easy. That is why {parent.label} reminded {child.label} to go slowly."),
        ("What did the parent say about the bridge?",
         f'{parent.label} said the bridge had a narrow width and that slow feet were safer. The warning fit the little bridge because a quick step could make it clatter."),
    ]
    if f["outcome"] == "warned":
        qa.append((
            "What happened when the child moved too fast?",
            f"The boards gave a clatter, the bridge wobbled, and everyone stopped right away. The noisy shake showed that reckless steps were not a good idea."
        ))
        qa.append((
            "How did the bedtime story end?",
            f"It ended safely, with the child turning back home and getting tucked in after the warning. The bridge stayed quiet, and the dark night felt calm again."
        ))
    else:
        qa.append((
            "How did they cross in the safe ending?",
            f"They crossed with slow steps and careful hands on the rail. That kept the width of the bridge from feeling scary."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does width mean?",
         "Width means how wide something is from one side to the other. A narrow bridge has a small width, while a wide boardwalk has more room."),
        ("What is a clatter?",
         "A clatter is a loud, clacky noise made when something bumps or rattles. Loose boards or fallen things can make a clatter."),
        ("What is a flashback in a story?",
         "A flashback is a memory scene that shows something from earlier. It helps explain why a character feels the way they do now."),
        ("Why do adults tell children to go slowly on a bridge?",
         "Because a bridge can wobble if someone moves too fast. Slow steps help keep everyone safe."),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("narrow_footbridge", "basket", "rush", "Mina", "girl", "Mara", "woman", "sleepy"),
    StoryParams("garden_plank", "lantern", "rush", "Theo", "boy", "Liam", "man", "gentle"),
]


ASP_RULES = r"""
bridge_wide(P, M) :- place(P), move(M), width(P, W), balance(M, B), W < B.
reckless(M) :- move(M), sense(M, S), S < sense_min(Min), S < Min.
clatter_happens(P, M) :- bridge_wide(P, M), place(P), move(M).
safe_story(P, M) :- place(P), move(M), width(P, W), balance(M, B), W >= B.
valid(P, M, I) :- clatter_happens(P, M), item(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("width", pid, p.width))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("balance", mid, m.balance))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], ITEMS[params.item], MOVES[params.move],
                 params.child_name, params.child_gender, params.parent_name, params.parent_gender)
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
        for combo in asp_valid_combos():
            print("  ", combo)
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
            params = resolve_params(args, random.Random(seed))
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
