#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/oodles_regress_unicycle_inner_monologue_sound_effects.py
=========================================================================================

A small bedtime-story world about a child, a wobbling unicycle, and the way a
gentle helper keeps a little dare from turning into a big tumble.

Seed words: oodles, regress, unicycle
Features: Inner Monologue, Sound Effects, Dialogue
Style: Bedtime Story
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    adult: str
    style: str
    noise: str
    vehicle: str
    comfort: str
    can_wobble: bool = True
    regress_limit: int = 2
    seed: Optional[int] = None


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
        import copy

        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    bike = world.entities.get("vehicle")
    child = world.entities.get("child")
    if bike and child and bike.meters.get("steady", 0.0) >= THRESHOLD and bike.meters.get("wobble", 0.0) == 0:
        sig = ("settle",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] = child.memes.get("relief", 0.0) + 1
            out.append("__settled__")
    return out


def _r_regress(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    vehicle = world.entities.get("vehicle")
    helper = world.entities.get("helper")
    if not child or not vehicle or not helper:
        return out
    if child.memes.get("worry", 0.0) < THRESHOLD:
        return out
    if vehicle.meters.get("wobble", 0.0) < THRESHOLD:
        return out
    if child.memes.get("regress", 0.0) >= THRESHOLD:
        sig = ("regress",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.say(f"Inside {child.id}'s tiny chest, a shy thought whispered that {child.id} might need to go back to the safest, smallest step.")
        return ["__regress__"]
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_regress, _r_settle):
            s = rule(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_tumble(world: World) -> dict:
    sim = world.copy()
    vehicle = sim.get("vehicle")
    child = sim.get("child")
    vehicle.meters["wobble"] = vehicle.meters.get("wobble", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    propagate(sim, narrate=False)
    return {"wobble": vehicle.meters.get("wobble", 0.0), "worry": child.memes.get("worry", 0.0)}


def setup(world: World, child: Entity, helper: Entity, adult: Entity, params: StoryParams) -> None:
    child.memes["delight"] = 1.0
    helper.memes["warmth"] = 1.0
    world.say(
        f"At bedtime, {child.id} found a little unicycle in the hall, bright as a moonbeam, and thought of {params.comfort} and {params.noise} in the quiet house."
    )
    world.say(
        f'"{params.style} stories are the best," {child.id} murmured, and {helper.id} smiled like a soft night-light.'
    )
    world.say(
        f'{"I wonder if I can ride it," if child.type == "thing" else f"I wonder if I can ride it,"} {child.id} thought. "Maybe I can do oodles of laps!"'
    )


def need_help(world: World, child: Entity, helper: Entity, params: StoryParams) -> None:
    world.say(
        f"But the unicycle was tall and a little wiggly, and {child.id} felt the first hush of worry. " 
        f'"What if I regress and tip over?" {child.id} wondered.'
    )
    world.say(
        f'"I can help," {helper.id} said. "Slow is lovely."'
    )


def attempt(world: World, child: Entity, vehicle: Entity, helper: Entity) -> None:
    child.memes["regress"] = child.memes.get("regress", 0.0) + 1
    vehicle.meters["wobble"] = vehicle.meters.get("wobble", 0.0) + 1
    world.say(f"{child.id} climbed up anyway. The seat went: wobble-wobble, and the wheel answered: clink-clink.")
    world.say(f'"I am doing oodles of brave things," {child.id} thought, while {helper.id} held out {helper.pronoun("possessive")} hands.')


def warn(world: World, helper: Entity, child: Entity, adult: Entity) -> None:
    pred = predict_tumble(world)
    if pred["wobble"] >= THRESHOLD:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.say(
            f'"Careful," {helper.id} said. "{adult.id} said not to rush."'
        )
        world.say(
            f'{helper.id} leaned close and said, "If the wheel keeps wobbling, we can stop and try again with smaller steps."'
        )


def arrest(world: World, helper: Entity, child: Entity, vehicle: Entity) -> None:
    helper.memes["calm"] = helper.memes.get("calm", 0.0) + 1
    vehicle.meters["wobble"] = 0.0
    vehicle.meters["steady"] = 1.0
    world.say(
        f'{helper.id} reached out and steadied the unicycle. "There," {helper.id} said, "no need to hurry."'
    )
    world.say(
        f"The wheel stopped its little chatter: click... click... and the hall felt quieter at once."
    )


def end_bed(world: World, child: Entity, helper: Entity, params: StoryParams) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    world.say(
        f"{child.id} slid down, tucked {child.pronoun('possessive')} feet back on the floor, and laughed a sleepy laugh."
    )
    world.say(
        f'"We can practice tomorrow," {helper.id} said. "{adult_line(params.adult)}"'
    )
    world.say(
        f"So {child.id} and {helper.id} left the unicycle by the wall, safe and still, like a small round moon waiting for morning."
    )


def adult_line(name: str) -> str:
    return f"{name} says we should take tiny turns first"


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult", label="the grown-up"))
    vehicle = world.add(Entity(id="vehicle", kind="thing", type="toy", label="unicycle"))
    vehicle.meters["steady"] = 0.0
    vehicle.meters["wobble"] = 0.0
    world.facts["params"] = params
    world.facts["vehicle"] = vehicle

    setup(world, child, helper, adult, params)
    world.para()
    need_help(world, child, helper, params)
    attempt(world, child, vehicle, helper)
    warn(world, helper, child, adult)
    arrest(world, helper, child, vehicle)
    world.para()
    end_bed(world, child, helper, params)
    propagate(world, narrate=False)

    world.facts.update(child=child, helper=helper, adult=adult, vehicle=vehicle)
    return world


CHILD_NAMES = ["Mina", "Pip", "Toby", "Lulu", "Nora", "Finn"]
HELPER_NAMES = ["Milo", "Ivy", "June", "Wren", "Oli", "Bea"]
ADULT_NAMES = ["Mama", "Papa", "Nana", "Dada", "Auntie", "Uncle"]
COMFORTS = ["a stack of pillows", "a warm blanket", "a sleepy teddy bear", "a cup of cocoa"]
NOISES = ["tap-tap", "buzz-buzz", "hum-hum", "ding-ding"]


@dataclass
class Registry:
    child_gender: str
    helper_gender: str
    child_name: str
    helper_name: str
    adult_name: str


REGISTRY = [
    Registry("girl", "girl", "Mina", "Ivy", "Mama"),
    Registry("boy", "boy", "Pip", "Milo", "Papa"),
    Registry("girl", "boy", "Lulu", "Oli", "Nana"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bedroom", "inner_monologue", "unicycle")]


def explain_rejection() -> str:
    return "(No story: this bedtime world only accepts the unicycle in a calm bedroom scene.)"


ASP_RULES = r"""
steady(vehicle) :- vehicle(vehicle), not wobble(vehicle).
wobbly(vehicle) :- wobble(vehicle), wobble(vehicle).
needs_help(child) :- worry(child), wobbly(vehicle).
regresses(child) :- needs_help(child), regress_word(regress).
settled(child) :- steady(vehicle), helper(helper).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("vehicle", "unicycle"),
        asp.fact("regress_word", "regress"),
        asp.fact("helper", "helper"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show settled/1."))
    return sorted(set(asp.atoms(model, "settled")))


def asp_verify() -> int:
    import asp as _asp  # lazy twin presence
    rc = 0
    try:
        _ = _asp.one_model(asp_program("#show settled/1."))
    except Exception as e:
        print(f"ASP smoke test failed: {e}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(child=None, helper=None, adult=None, style=None, noise=None, vehicle=None, comfort=None), random.Random(0)))
        _ = sample.story
        print("OK: ordinary generation smoke test passed.")
    except Exception as e:
        print(f"Generation smoke test failed: {e}")
        rc = 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        print("MISMATCH: ASP gate does not match valid_combos().")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about oodles, regress, and a unicycle.")
    ap.add_argument("--child", choices=CHILD_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--style", default="Bedtime Story")
    ap.add_argument("--noise", choices=NOISES)
    ap.add_argument("--vehicle", choices=["unicycle"], default="unicycle")
    ap.add_argument("--comfort", choices=COMFORTS)
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
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice([x for x in HELPER_NAMES if x != child])
    adult = args.adult or rng.choice(ADULT_NAMES)
    style = args.style or "Bedtime Story"
    noise = args.noise or rng.choice(NOISES)
    comfort = args.comfort or rng.choice(COMFORTS)
    return StoryParams(
        child=child,
        child_gender="girl" if child in {"Mina", "Lulu", "Nora"} else "boy",
        helper=helper,
        helper_gender="girl" if helper in {"Ivy", "June", "Wren", "Bea"} else "boy",
        adult=adult,
        style=style,
        noise=noise,
        vehicle="unicycle",
        comfort=comfort,
        can_wobble=True,
        regress_limit=2,
    )


def generate(params: StoryParams) -> StorySample:
    if params.vehicle != "unicycle":
        raise StoryError("This world only tells stories about a unicycle.")
    world = tell(params)
    prompts = [
        f'Write a {params.style.lower()} that uses the words "oodles", "regress", and "unicycle".',
        f'Tell a gentle story with dialogue, sound effects, and inner monologue about {params.child} and a unicycle.',
        f"Write a bedtime story where a child wants to do oodles of brave things, then slows down instead of letting the moment regress into a tumble.",
    ]
    story_qa = [
        QAItem(
            question="Why did the child pause instead of rushing on the unicycle?",
            answer=f"{params.child} noticed the wobble and felt worried. The helper steadied the unicycle so the child could keep trying in a safer, slower way."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended softly, with {params.child} and {params.helper} leaving the unicycle safe and still by the wall. The child could practice again tomorrow, after bedtime and after the room had gone quiet."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a unicycle?",
            answer="A unicycle is a one-wheeled ride-on toy or vehicle. It needs balance, so a helper and slow practice make it feel safer."
        ),
        QAItem(
            question="What does regress mean in this story?",
            answer="Here, regress means to slip back from a brave plan into an older, smaller, safer step. It is a signal to slow down and try again gently."
        ),
        QAItem(
            question="What are sound effects for in a bedtime story?",
            answer="Sound effects help the reader hear the scene in their imagination. Little sounds can make a quiet story feel alive without making it scary."
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: meters={e.meters} memes={e.memes} role={e.role}")
    return "\n".join(parts)


CURATED = [
    StoryParams(child="Mina", child_gender="girl", helper="Ivy", helper_gender="girl", adult="Mama", style="Bedtime Story", noise="tap-tap", vehicle="unicycle", comfort="a warm blanket", can_wobble=True, regress_limit=2),
    StoryParams(child="Pip", child_gender="boy", helper="Milo", helper_gender="boy", adult="Papa", style="Bedtime Story", noise="hum-hum", vehicle="unicycle", comfort="a sleepy teddy bear", can_wobble=True, regress_limit=2),
]


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
        print(asp_program("#show settled/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} ASP combos: {asp_valid_combos()}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
