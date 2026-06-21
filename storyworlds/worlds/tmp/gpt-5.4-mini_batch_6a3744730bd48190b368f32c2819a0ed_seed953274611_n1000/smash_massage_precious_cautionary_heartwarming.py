#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/smash_massage_precious_cautionary_heartwarming.py
===================================================================================

A tiny cautionary, heartwarming storyworld about a child who wants to smash
something to solve a problem, a precious thing that must be protected, and a
gentle adult turn toward safety and care.

Seed words: smash, massage, precious
Style: heartwarming
Feature: cautionary

This world models a small kitchen-and-living-room domain:
- a child wants to smash a hard treat or object to get to something useful;
- a nearby precious object is at risk of breaking;
- a caregiver warns them off or helps them choose a safer way;
- the story ends with a warm, caring image that proves what changed.

The world uses typed entities with physical meters and emotional memes, a small
forward rule engine, a Python reasonableness gate, and an inline ASP twin.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    safe_tool: bool = False
    precious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    mess: str = "shards"
    power: int = 1
    sense: int = 2
    tags: set[str] = field(default_factory=set)
    makes_noise: str = "smash!"
    is_tool: bool = False


@dataclass
class PreciousThing:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    precious: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeAction:
    id: str
    label: str
    phrase: str
    help_text: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["shatter"] < THRESHOLD:
            continue
        sig = ("break", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for e in world.entities.values():
            if e.precious:
                e.memes["worry"] += 1
        out.append("__break__")
    return out


CAUSAL_RULES = [Rule("break", _r_break)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def sensible_things() -> list[Thing]:
    return [t for t in THINGS.values() if t.sense >= SENSE_MIN]


def valid_combo(action: Thing, precious: PreciousThing) -> bool:
    return action.power >= 1 and precious.fragile


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for aid, act in THINGS.items():
        for pid, pr in PRECIOUS.items():
            if valid_combo(act, pr):
                out.append((aid, pid))
    return out


def predict_break(world: World, action: Thing, precious_id: str) -> bool:
    sim = world.copy()
    sim.get(action.id).meters["shatter"] += 1
    propagate(sim, narrate=False)
    return sim.get(precious_id).memes["worry"] >= THRESHOLD


def do_smash(world: World, child: Entity, action: Thing, precious: PreciousThing) -> None:
    child.memes["impulse"] += 1
    child.meters["shatter"] += 1
    propagate(world, narrate=False)
    world.say(f"{child.id} lifted the {action.label} and gave it a great {action.makes_noise}.")


def warn(world: World, parent: Entity, child: Entity, precious: PreciousThing, action: Thing) -> bool:
    if not predict_break(world, action, precious.id):
        return False
    parent.memes["care"] += 1
    world.say(
        f'{parent.id} held up a hand. "{child.id}, please do not smash anything near '
        f'{precious.label}. It is too precious to risk."'
    )
    return True


def choose_safer(world: World, child: Entity, parent: Entity, action: Thing, safe: SafeAction) -> None:
    child.memes["relief"] += 1
    world.say(
        f"{child.id} stopped, looked at {parent.pronoun('object')}, and nodded. "
        f'Together they chose to {safe.phrase} instead.'
    )


def finish_happy(world: World, child: Entity, parent: Entity, safe: SafeAction, precious: PreciousThing) -> None:
    child.memes["love"] += 1
    parent.memes["love"] += 1
    world.say(
        f"{child.id} used {safe.help_text}, and the {precious.label} stayed safe and bright."
    )
    world.say(
        f"Then {child.id} gave {parent.pronoun('object')} a gentle massage, and {parent.id} smiled with tired, happy eyes."
    )
    world.say("The kitchen felt warm again, like a place where careful hands and kind hearts belonged.")


def finish_cautionary(world: World, parent: Entity, child: Entity, precious: PreciousThing, action: Thing) -> None:
    child.memes["fear"] += 1
    parent.memes["care"] += 1
    world.say(
        f"{child.id} learned the hard way that one sharp smash can send pieces flying toward something precious."
    )
    world.say(
        f"After that scare, {child.id} asked for help first, and {parent.id} gave a calm nod and a hug."
    )
    world.say("That evening ended gently, with safe hands, a whole home, and a quieter kind of bravery.")


def tell(action: Thing, precious: PreciousThing, safe: SafeAction,
         child_name: str = "Milo", child_type: str = "boy",
         parent_name: str = "Nina", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent"))
    target = world.add(Entity(id=precious.id, kind="thing", type="thing", label=precious.label, precious=True, fragile=precious.fragile))
    tool = world.add(Entity(id=action.id, kind="thing", type="tool", label=action.label, safe_tool=False))
    world.facts.update(child=child, parent=parent, precious=precious, action=action, safe=safe)

    world.say(
        f"On a quiet afternoon, {child.id} noticed {precious.phrase} on the table and thought it looked {precious.label} and special."
    )
    world.say(
        f'{child.id} wanted to smash the hard shell open at once, because the filling inside smelled delicious.'
    )

    world.para()
    warned = warn(world, parent, child, precious, action)
    if warned:
        world.say(f'But {parent.id} gently explained that a loose smash could hurt something precious.')
        world.para()
        choose_safer(world, child, parent, action, safe)
        world.para()
        finish_happy(world, child, parent, safe, precious)
        outcome = "averted"
    else:
        do_smash(world, child, action, precious)
        world.para()
        if valid_combo(action, precious):
            world.say(f"The shell cracked open, but the room still felt nervous for a moment.")
            finish_happy(world, child, parent, safe, precious)
            outcome = "contained"
        else:
            finish_cautionary(world, parent, child, precious, action)
            outcome = "burned"

    world.facts["outcome"] = outcome
    world.facts["target"] = target
    world.facts["tool"] = tool
    return world


THINGS = {
    "hammer": Thing(id="hammer", label="tiny hammer", phrase="a tiny hammer", power=2, sense=1, tags={"smash"}, makes_noise="smash!"),
    "nutcracker": Thing(id="nutcracker", label="nutcracker", phrase="a nutcracker", power=2, sense=3, tags={"smash"}, makes_noise="click!"),
    "spoon": Thing(id="spoon", label="wooden spoon", phrase="a wooden spoon", power=0, sense=0, tags={"smash"}),
}

PRECIOUS = {
    "vase": PreciousThing(id="vase", label="blue vase", phrase="a precious blue vase", tags={"precious"}),
    "photo": PreciousThing(id="photo", label="framed photo", phrase="a precious framed photo", tags={"precious"}),
    "bowl": PreciousThing(id="bowl", label="grandma's bowl", phrase="grandma's precious bowl", tags={"precious"}),
}

SAFE = {
    "open": SafeAction(id="open", label="safe opener", phrase="use the nutcracker carefully", help_text="the nutcracker carefully", tags={"safe"}),
    "ask": SafeAction(id="ask", label="ask for help", phrase="ask a grown-up for help", help_text="a grown-up's help", tags={"safe"}),
}


@dataclass
class StoryParams:
    action: str
    precious: str
    safe: str
    child_name: str
    child_type: str
    parent_name: str
    parent_type: str = "mother"
    seed: Optional[int] = None


CURATED = [
    StoryParams(action="nutcracker", precious="vase", safe="open", child_name="Milo", child_type="boy", parent_name="Nina"),
    StoryParams(action="hammer", precious="bowl", safe="ask", child_name="Sana", child_type="girl", parent_name="Asha"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming cautionary storyworld with smash, massage, and precious.")
    ap.add_argument("--action", choices=THINGS)
    ap.add_argument("--precious", choices=PRECIOUS)
    ap.add_argument("--safe", choices=SAFE)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["boy", "girl"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    act = args.action or rng.choice(list(THINGS))
    pr = args.precious or rng.choice(list(PRECIOUS))
    safe = args.safe or rng.choice(list(SAFE))
    if not valid_combo(THINGS[act], PRECIOUS[pr]):
        raise StoryError("This smash would not make a reasonable cautionary story.")
    return StoryParams(
        action=act,
        precious=pr,
        safe=safe,
        child_name=args.child_name or rng.choice(["Milo", "Sana", "Toby", "Lila"]),
        child_type=args.child_type or rng.choice(["boy", "girl"]),
        parent_name=args.parent_name or rng.choice(["Nina", "Asha", "Ravi", "Mara"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming cautionary story that uses the words "smash", "massage", and "precious".',
        f"Tell a short story where {f['child'].id} wants to smash something, but a precious item needs protecting and a grown-up helps them choose a safer way.",
        f"Write a warm family story about a child learning that careful hands are better than a smash near something precious.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    precious: PreciousThing = f["precious"]
    safe: SafeAction = f["safe"]
    outcome = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, with a precious thing resting nearby on the table."),
        ("Why did the parent warn the child?",
         f"Because a smash can send pieces flying, and the precious {precious.label} was close enough to be hurt. The warning gave them a chance to choose a safer way."),
    ]
    if outcome == "averted":
        qa.append((
            "What happened instead of the smash?",
            f"{child.id} listened, and they chose to {safe.help_text} instead. That kept the precious {precious.label} safe and made the whole room calmer."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended with care and relief, because the family chose safety after the scare. Even the massage at the end felt like a promise to be gentle."
        ))
    qa.append((
        "Why was the ending heartwarming?",
        f"Because the grown-up stayed kind, the child learned something important, and nobody was left alone with fear. The story ends with a hug and a calmer home."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does smash mean?",
         "Smash means to hit something hard so it breaks or cracks. That is why you should be careful with things that are fragile."),
        ("What is a massage?",
         "A massage is gentle rubbing with your hands to help someone feel relaxed or less sore. It should always be soft and caring."),
        ("What does precious mean?",
         "Precious means very special and important to someone. People protect precious things because they do not want them to get broken or lost."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.precious:
            bits.append("precious=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
shatter_happens :- chosen_action(A), power(A, P), P >= 1.
worry(P) :- precious(P), shatter_happens.
valid(A, P) :- action(A), precious(P), fragile(P), power(A, X), X >= 1.
outcome(averted) :- avoid_smash.
outcome(contained) :- shatter_happens, safe_after.
outcome(burned) :- shatter_happens, not safe_after.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid, a in THINGS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, a.power))
    for pid, p in PRECIOUS.items():
        lines.append(asp.fact("precious", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combo_pairs()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(action=None, precious=None, safe=None, child_name=None, child_type=None, parent_name=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combo_pairs() -> list[tuple[str, str]]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    if params.action not in THINGS or params.precious not in PRECIOUS or params.safe not in SAFE:
        raise StoryError("Unknown story parameters.")
    action = THINGS[params.action]
    precious = PRECIOUS[params.precious]
    safe = SAFE[params.safe]
    if not valid_combo(action, precious):
        raise StoryError("That action and precious thing do not make a good cautionary story.")
    world = tell(action, precious, safe, params.child_name, params.child_type, params.parent_name, params.parent_type)
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
        print(asp_program("", "#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
