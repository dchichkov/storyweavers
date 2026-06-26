#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure domain.

Premise:
A young space explorer wants to visit a glowing moon garden, but a helmet
problem makes the trip unsafe. The explorer tries again and again, learns a
lesson about safety, and ends with a bad ending that still feels complete:
the mission is lost, but the rule is learned.

This world emphasizes:
- helmet
- grin
- repetition
- lesson learned
- bad ending

The simulated world tracks physical meters and emotional memes, then renders
story text from the evolving state.
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
    phrase: str = ""
    owner: Optional[str] = None
    wearer: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "pilot"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "captain"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Location:
    id: str
    label: str
    place: str
    vacuum: bool = False
    glow: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    safe: str
    weather: str
    requires_helmet: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, location: Location) -> None:
        self.location = location
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: str = "space"

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
        c = World(self.location)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.zone = self.zone
        c.paragraphs = [[]]
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.wearer == actor.id]


def _r_expose(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters.get("outside_helmet", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("risk", 0.0) < THRESHOLD:
            continue
        sig = ("expose", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1.0
        out.append(f"{actor.pronoun().capitalize()} felt the danger of the open air.")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson_learned"] = actor.memes.get("lesson_learned", 0.0) + 1.0
        out.append("The lesson was clear: in space, a helmet was not optional.")
    return out


CAUSAL_RULES = [_r_expose, _r_lesson]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_without_helmet(world: World, actor: Entity) -> bool:
    helmet = next((g for g in world.worn_items(actor) if g.id == "helmet"), None)
    return helmet is None


def predict_bad_end(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    act = sim.get(actor.id)
    act.meters["risk"] = 1.0 if activity.requires_helmet else 0.0
    act.meters["outside_helmet"] = 1.0 if risk_without_helmet(sim, act) else 0.0
    propagate(sim, narrate=False)
    return sim.get(actor.id).memes.get("lesson_learned", 0.0) >= THRESHOLD


def intro(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a young space explorer with a bright grin and a big dream."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} under the silver stars."
    )


def mission(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"One night, {hero.id} stepped toward the {world.location.label} near {world.location.place}."
    )
    if world.location.glow:
        world.say("The moon garden glowed softly, like a lantern in the dark.")
    world.say(
        f"{hero.id} wanted to {activity.verb}, but the helmet check had to come first."
    )


def repeat_warning(world: World, hero: Entity) -> None:
    world.say(
        f'"Helmet first," the ship voice said. "Helmet first."'
    )
    world.say(
        f'{hero.id} nodded, then looked away, then heard it again: "Helmet first."'
    )


def ignore_and_try(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["risk"] = 1.0
    hero.meters["outside_helmet"] = 1.0 if risk_without_helmet(world, hero) else 0.0
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(
        f'{hero.id} kept the grin anyway and tried to {activity.verb} without the helmet.'
    )
    propagate(world, narrate=True)


def bad_ending(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"The path never opened safely, so the mission stopped before it could begin."
    )
    world.say(
        f'{hero.id} stood still, grin fading into a small sigh, while the stars watched.'
    )


def lesson(world: World, hero: Entity) -> None:
    if hero.memes.get("lesson_learned", 0.0) >= THRESHOLD:
        world.say(
            f'At last, {hero.id} understood that a good adventure starts with safe gear.'
        )


def tell(location: Location, activity: Activity, hero_name: str = "Nova") -> World:
    world = World(location)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy" if hero_name != "Astra" else "girl"))
    helmet = world.add(Entity(
        id="helmet",
        type="gear",
        label="helmet",
        phrase="a shiny helmet",
        owner=hero.id,
        wearer=None,
        protective=True,
    ))
    world.add(Entity(
        id="moon_garden",
        type="place",
        label="moon garden",
        phrase="a glowing moon garden",
        owner=None,
    ))
    hero.meters["outside_helmet"] = 1.0
    intro(world, hero, activity)
    world.para()
    mission(world, hero, activity)
    repeat_warning(world, hero)
    ignore_and_try(world, hero, activity)
    world.para()
    bad_ending(world, hero, activity)
    lesson(world, hero)
    world.facts.update(hero=hero, helmet=helmet, activity=activity, location=location)
    return world


LOCATIONS = {
    "moon_base": Location(id="moon_base", label="moon garden", place="Moon Base Nine", vacuum=True, glow=True),
    "orbital_dock": Location(id="orbital_dock", label="dock ring", place="Orbital Dock Seven", vacuum=True, glow=False),
}

ACTIVITIES = {
    "float": Activity(
        id="float",
        verb="float outside",
        gerund="floating outside",
        risk="space wind",
        safe="slow steps",
        weather="cold",
        requires_helmet=True,
        tags={"space", "helmet"},
    ),
    "hop": Activity(
        id="hop",
        verb="hop along the airwalk",
        gerund="hopping along the airwalk",
        risk="thin air",
        safe="careful steps",
        weather="cold",
        requires_helmet=True,
        tags={"space", "helmet"},
    ),
}

DEFAULT_PARAMS = {
    "location": "moon_base",
    "activity": "float",
}


@dataclass
class StoryParams:
    location: str
    activity: str
    name: str = "Nova"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld with helmet, grin, repetition, and lesson learned.")
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
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
    location = args.location or rng.choice(list(LOCATIONS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    name = args.name or rng.choice(["Nova", "Pax", "Milo", "Iris"])
    return StoryParams(location=location, activity=activity, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short Space Adventure story for a child that includes the word "helmet".',
        f"Tell a story about {f['hero'].id} with a bright grin who wants to {f['activity'].verb} but must learn a safety lesson.",
        "Write a gentle space story with repetition, a bad ending, and a clear lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep hearing the same warning?",
            answer="Because the ship voice repeated that the helmet had to come first.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {act.verb} near the moon garden.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer="The lesson was that a helmet is important before going out into space.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a helmet do in space?",
            answer="A helmet helps protect your head and keeps you safer where there is no air.",
        ),
        QAItem(
            question="What is a grin?",
            answer="A grin is a big smile that shows someone feels happy or excited.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.kind:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(L, A) :- location(L), activity(A), needs_helmet(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid in LOCATIONS:
        lines.append(asp.fact("location", lid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if act.requires_helmet:
            lines.append(asp.fact("needs_helmet", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(l, a) for l in LOCATIONS for a, act in ACTIVITIES.items() if act.requires_helmet}
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(LOCATIONS[params.location], ACTIVITIES[params.activity], params.name)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for loc in LOCATIONS:
            for act in ACTIVITIES:
                p = StoryParams(location=loc, activity=act, name="Nova")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
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
