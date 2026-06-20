#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gasoline_baptize_conflict_problem_solving_rhyming_story.py
==========================================================================================

A standalone storyworld for a tiny rhyming tale about a family garage project:
a child wants to "baptize" a little boat with gasoline to make it sparkle, a
careful helper spots the danger, conflict flares, and the grown-up solves the
problem with a safe, cheerful alternative.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained rule engine
- a reasonableness gate and an ASP twin
- story-grounded and world-knowledge QA
- child-facing rhyming prose with a clear beginning, middle turn, and ending image
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    flammable: bool = False
    splashes: bool = False
    shiny: bool = False


@dataclass
class ActionCfg:
    id: str
    verb: str
    rhyme: str
    mess: str
    risk: str
    zone: set[str]
    guards: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    act = world.facts.get("action")
    if not act:
        return out
    for kid in world.entities.values():
        if kid.kind != "character" or kid.role != "instigator":
            continue
        if kid.meters[act.mess] < THRESHOLD:
            continue
        sig = ("spill", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("floor").meters[act.mess] += 1
        world.get("room").meters["danger"] += 1
        out.append("__spill__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.entities.get("room")
    if not room or room.meters["danger"] < THRESHOLD:
        return out
    sig = ("fear", "room")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.entities.values():
        if ent.kind == "character":
            ent.memes["fear"] += 1
    out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("spill", "physical", _r_spill), Rule("fear", "social", _r_fear)]


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


def hazard_at_risk(action: ActionCfg, obj: ObjectCfg) -> bool:
    return action.id == "baptize" and obj.flammable


def sensible_fixes() -> list[FixCfg]:
    return [f for f in FIXES.values() if f.sense >= 2]


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(fix: FixCfg, delay: int) -> bool:
    return fix.power >= fire_severity(delay)


def predict(world: World, obj_id: str) -> dict:
    sim = world.copy()
    sim.get(obj_id).meters["wet"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": sim.get("room").meters["danger"],
        "fear": sum(e.memes["fear"] for e in sim.entities.values() if e.kind == "character"),
    }


def make_setup(world: World, child: Entity, helper: Entity, parent: Entity) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"One bright day in a cluttered bay, {child.id} and {helper.id} began to play. "
        f"The little boat sat ready with a ribbon of blue, and the garage smelled faintly new."
    )
    world.say(
        f'"Let us baptize the boat," said {child.id} with pride, "and send it off on a shiny tide."'
    )


def want_gasoline(world: World, child: Entity, obj: Entity) -> None:
    child.memes["want"] += 1
    world.say(
        f"{child.id} spotted a bottle of {obj.label_word if obj.label else obj.label}. "
        f'"Gasoline will make it gleam!" {child.id} said. "What a marvelous dream."'
    )


def warn(world: World, helper: Entity, child: Entity, parent: Entity, obj: ObjectCfg) -> None:
    pred = predict(world, "boat")
    helper.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{helper.id} frowned and bit {helper.pronoun("possessive")} lip. '
        f'"No, no, dear friend; gasoline is not for a toy, and it can spark in a flame."'
    )
    world.say(
        f'"{parent.label_word.capitalize()} said keep it far away," {helper.id} went on, '
        f'"for a little spill could bring great trouble and shame."'
    )


def conflict(world: World, child: Entity, helper: Entity) -> None:
    child.memes["defiance"] += 1
    helper.memes["stress"] += 1
    world.say(
        f'{child.id} crossed {child.pronoun("possessive")} arms and gave a hard little sigh, '
        f'"I want my shiny baptize," {child.id} cried. "Why, oh why?"'
    )
    world.say(
        f"But {helper.id} held steady and stayed by {child.id}'s side, "
        f"for a problem needs kindness when feelings run wide."
    )


def do_bad(world: World, boat: Entity, gas: Entity) -> None:
    boat.meters["wet"] += 1
    boat.meters["slick"] += 1
    world.get("room").meters["danger"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Still, the cap popped open with a hiss and a pop; a splash of gasoline would not stop. "
        f"It kissed the boat with a shiny thin sheen, and the air turned sharp, not soft and clean."
    )
    world.say(
        f"{helper_name(world)} gasped, because even a tiny drop can make a place feel unsafe and hot."
    )


def helper_name(world: World) -> str:
    return world.facts["helper"].id


def alarm(world: World, child: Entity, helper: Entity, parent: Entity) -> None:
    world.say(
        f'"{parent.label_word.upper()}!" shouted {child.id} and {helper.id} in a ringing spree, '
        f"and {parent.id} came hurrying quickly to see."
    )


def solve(world: World, parent: Entity, fix: FixCfg, boat: Entity, child: Entity, helper: Entity) -> None:
    boat.meters["wet"] = 0.0
    world.get("room").meters["danger"] = 0.0
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came with a careful grin, and chose the safest win. "
        f"{parent.pronoun().capitalize()} set the gasoline out of reach, far from the floor, "
        f"then {fix.text} to settle the score."
    )
    world.say(
        f"The boat got a splash of water instead, a bright little baptize with no fear overhead. "
        f"It shimmered and smiled in the yellow light, and the two small kids felt brave and right."
    )
    world.say(
        f"With the danger gone and the tidy boat near, they waved it goodbye with a happy cheer."
    )


def is_rhymey_line(text: str) -> str:
    return text


def tell(child_name: str, child_gender: str, helper_name_: str, helper_gender: str,
         parent_type: str, action: ActionCfg, obj: ObjectCfg, fix: FixCfg, delay: int) -> World:
    world = World()
    child = world.add(Entity(child_name, kind="character", type=child_gender, role="instigator"))
    helper = world.add(Entity(helper_name_, kind="character", type=helper_gender, role="cautioner"))
    parent = world.add(Entity("Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    room = world.add(Entity("room", type="room", label="the room"))
    floor = world.add(Entity("floor", type="thing", label="the floor"))
    boat = world.add(Entity("boat", type="thing", label=obj.label))
    gas = world.add(Entity("gas", type="thing", label=obj.label))
    world.facts.update(child=child, helper=helper, parent=parent, action=action, obj=obj, fix=fix, delay=delay)
    make_setup(world, child, helper, parent)
    world.para()
    want_gasoline(world, child, gas)
    warn(world, helper, child, parent, obj)
    world.para()
    conflict(world, child, helper)
    do_bad(world, boat, gas)
    alarm(world, child, helper, parent)
    world.para()
    if is_contained(fix, delay):
        solve(world, parent, fix, boat, child, helper)
    else:
        world.say(
            f"The parent moved fast, but the spill had already grown into a fright. "
            f"They aired the garage and kept everyone bright."
        )
    world.facts["outcome"] = "contained" if is_contained(fix, delay) else "burned"
    world.facts["boat"] = boat
    world.facts["room"] = room
    world.facts["floor"] = floor
    world.facts["gasoline"] = gas
    return world


THE_ACTION = ActionCfg(
    id="baptize",
    verb="baptize",
    rhyme="glide",
    mess="wet",
    risk="spill",
    zone={"floor"},
    guards={"water"},
    tags={"baptize", "conflict", "problem_solving"},
)

OBJECTS = {
    "gasoline": ObjectCfg("gasoline", "gasoline", "the gasoline bottle", flammable=True, splashes=True, shiny=False),
    "boat": ObjectCfg("boat", "toy boat", "the little toy boat", flammable=False, splashes=True, shiny=True),
}

FIXES = {
    "water": FixCfg("water", 3, 3, "used a cup of water to baptize the boat safely", "used a cup of water to baptize the boat safely", tags={"water"}),
    "fan": FixCfg("fan", 2, 2, "used a fan to dry the slick floor and keep the air fresh", "used a fan to dry the slick floor and keep the air fresh", tags={"fan"}),
}

NAMES_GIRL = ["Maya", "Lina", "Rose", "Nora", "Ella"]
NAMES_BOY = ["Theo", "Finn", "Eli", "Max", "Jude"]
TRAITS = ["careful", "curious", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    parent: str
    fix: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for _ in [1]:
        if hazard_at_risk(THE_ACTION, OBJECTS["gasoline"]):
            combos.append(("garage", "baptize", "gasoline"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about gasoline, baptize, conflict, and problem solving.")
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
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
    if args.fix and args.fix not in FIXES:
        raise StoryError("Unknown fix.")
    fix = args.fix or "water"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice([n for n in (NAMES_BOY if helper_gender == "boy" else NAMES_GIRL) if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = 0 if args.delay is None else args.delay
    return StoryParams(child, child_gender, helper, helper_gender, parent, fix, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a rhyming story that includes gasoline and baptize, where a child wants to do something unsafe and a helper solves the problem kindly.",
        f"Tell a rhyming conflict story about {f['child'].id} wanting gasoline near a toy boat, then show a problem-solving ending.",
        "Write a child-facing garage story with a safe choice, a warning, and a happy ending image of a clean little boat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, parent, fix = f["child"], f["helper"], f["parent"], f["fix"]
    return [
        QAItem(
            question=f"Why did {helper.id} warn {child.id}?",
            answer=f"{helper.id} warned {child.id} because gasoline is dangerous near a toy boat and could make the garage unsafe. {helper.id} wanted to stop the spill before it turned into a bigger problem."
        ),
        QAItem(
            question="How was the problem solved?",
            answer=f"{parent.label_word.capitalize()} chose a safer way and {fix.text}. That kept the gasoline away and let the boat get a safe baptize instead."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the little boat shining clean and the children feeling calm and proud. The dangerous gasoline was put away, so the last image was safe and bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gasoline?",
            answer="Gasoline is a fuel that can burn very fast, so it must stay away from flames and child play."
        ),
        QAItem(
            question="What does baptize mean in a story like this?",
            answer="In a story, baptize can mean a little naming splash or a ceremonial sprinkle. Here it means giving the boat a special safe splash, not a dangerous one."
        ),
        QAItem(
            question="Why is it important to solve problems carefully?",
            answer="Careful problem solving keeps people safe and turns a hard moment into a better plan. It is a kind way to fix trouble without making more."
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(F, O) :- gasoline(F), flammable(O).
valid_choice(F, O) :- hazard(F, O).
outcome(contained) :- valid_choice(gasoline, boat).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("gasoline", "gasoline"), asp.fact("flammable", "boat"), asp.fact("baptize", "baptize")]
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_choice/2."))
    return sorted(set(asp.atoms(model, "valid_choice")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set([("gasoline", "boat")]):
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        params.child, params.child_gender, params.helper, params.helper_gender,
        params.parent, THE_ACTION, OBJECTS["gasoline"], FIXES[params.fix], params.delay
    )
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
        print(asp_program("", "#show valid_choice/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:", asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams("Maya", "girl", "Theo", "boy", "mother", "water", 0))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
