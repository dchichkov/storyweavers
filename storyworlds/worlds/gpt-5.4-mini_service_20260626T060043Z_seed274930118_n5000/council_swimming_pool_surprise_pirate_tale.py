#!/usr/bin/env python3
"""
storyworlds/worlds/council_swimming_pool_surprise_pirate_tale.py
===============================================================

A tiny pirate-tale storyworld set at a swimming pool, centered on a council
meeting, a surprise, and a child-friendly turn from worry to wonder.

The seed image behind this world:
- A pirate council gathers at a swimming pool.
- They are planning a surprise.
- The surprise is meant to feel like a cheerful pirate tale, not a grim one.
- The story should end with a clear changed image: the secret becomes a shared
  celebration.

This script keeps the world deliberately small:
- one setting
- one main activity
- one planned surprise
- one emotional turn
- one resolution

The prose engine, QA generation, and ASP gate all share the same world model.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pirate", "matey"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the swimming pool"
    affords: set[str] = field(default_factory=lambda: {"swim", "splash", "dive"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    weather: str
    keyword: str = "council"
    tags: set[str] = field(default_factory=set)


@dataclass
class SurprisePlan:
    id: str
    label: str
    phrase: str
    reveal: str
    props: list[str] = field(default_factory=list)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wet_clothes(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("splash", 0.0) < THRESHOLD:
            continue
        sig = ("wet", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["glee"] = actor.memes.get("glee", 0.0) + 1
        out.append(f"{actor.id} got a burst of splashy glee.")
    return out


def _r_secret_tension(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("kept_out", 0.0) < THRESHOLD:
            continue
        sig = ("tension", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        out.append(f"{actor.id} grew a little worried about the secret.")
    return out


CAUSAL_RULES = [
    Rule("wet_clothes", "physical", _r_wet_clothes),
    Rule("secret_tension", "social", _r_secret_tension),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_surprise(world: World, hero: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "splash": sim.get(hero.id).meters.get("splash", 0.0),
        "glee": sim.get(hero.id).memes.get("glee", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("That activity does not belong in this swimming pool tale.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


SETTINGS = {
    "pool": Setting(),
}

ACTIVITIES = {
    "swim": Activity(
        id="swim",
        verb="swim in the pool",
        gerund="swimming in the pool",
        rush="dash to the pool ladder",
        mess="splash",
        zone={"arms", "legs", "torso"},
        weather="sunny",
        keyword="council",
        tags={"water", "pool", "council"},
    ),
}

SURPRISES = {
    "banner": SurprisePlan(
        id="banner",
        label="a hidden banner",
        phrase="a bright pirate banner rolled tight in a towel",
        reveal="the banner unfurled above the pool",
        props=["banner", "towel"],
    ),
    "crown": SurprisePlan(
        id="crown",
        label="a tiny gold crown",
        phrase="a tiny gold crown tucked inside a seashell box",
        reveal="the crown sparkled on the chair back",
        props=["crown", "seashell box"],
    ),
}


@dataclass
class StoryParams:
    place: str = "pool"
    activity: str = "swim"
    surprise: str = "banner"
    name: str = "Mina"
    title: str = "captain"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A pirate council story set at a swimming pool, with a surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--title", choices=["captain", "matey"])
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
    place = args.place or "pool"
    activity = args.activity or "swim"
    surprise = args.surprise or rng.choice(list(SURPRISES))
    name = args.name or rng.choice(["Mina", "Jory", "Lina", "Pip", "Rafi"])
    title = args.title or rng.choice(["captain", "matey"])
    return StoryParams(place=place, activity=activity, surprise=surprise, name=name, title=title)


def story_qas(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    plan: SurprisePlan = f["surprise_plan"]
    return [
        QAItem(
            question=f"Where did the pirate council meet?",
            answer=f"They met at the swimming pool, where the water glittered and echoed around the tiles.",
        ),
        QAItem(
            question=f"What surprise did {hero.id} help prepare?",
            answer=f"They helped prepare {plan.phrase}, because the pirate council wanted a cheerful surprise.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop worrying at the end?",
            answer=f"Because the secret was revealed kindly, and the surprise became something fun to share.",
        ),
    ]


def world_qas(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a council?",
            answer="A council is a group of people who meet to talk and decide something together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something kept secret for a little while so it can be revealed later.",
        ),
        QAItem(
            question="What is a swimming pool?",
            answer="A swimming pool is a place filled with water where people can swim and splash safely.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    plan: SurprisePlan = f["surprise_plan"]
    return [
        'Write a short pirate tale set at a swimming pool with a council and a surprise.',
        f"Tell a child-friendly story where {hero.id} and the pirate council hide {plan.label}.",
        "Make the ending feel like a happy reveal at the pool.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.title,
        traits=["little", "brave", "curious"],
    ))
    matey = world.add(Entity(
        id="Matey",
        kind="character",
        type="matey",
        traits=["sly", "cheerful"],
    ))
    council = world.add(Entity(
        id="Council",
        kind="thing",
        type="council",
        label="pirate council",
    ))
    plan = SURPRISES[params.surprise]
    prop = world.add(Entity(
        id=plan.id,
        kind="thing",
        type="surprise",
        label=plan.label,
        phrase=plan.phrase,
        caretaker=hero.id,
    ))

    world.facts.update(hero=hero, matey=matey, council=council, surprise_plan=plan)

    world.say(
        f"On a bright day, {hero.id} came to the swimming pool with the pirate council."
    )
    world.say(
        f"The council had a secret, and {hero.pronoun('possessive')} eyes shone with curiosity."
    )

    world.para()
    world.say(
        f"They spoke in hushed pirate whispers: the council wanted a surprise for the pool."
    )
    world.say(
        f"{hero.id} helped hide {plan.phrase} near the pool chairs, while the water lapped softly."
    )

    world.para()
    _do_activity(world, hero, ACTIVITIES[params.activity], narrate=False)
    world.say(
        f"Then {hero.id} wanted to {ACTIVITIES[params.activity].verb}, but the secret made {hero.pronoun()} pause."
    )
    world.say(
        f"{matey.id} grinned and said the old council rule: keep the surprise safe until the right splash."
    )
    hero.memes["kept_out"] = 1.0
    hero.memes["curiosity"] = 1.0
    propagate(world, narrate=True)

    world.para()
    hero.memes["worry"] = max(hero.memes.get("worry", 0.0), 1.0)
    world.say(
        f"At last, the council lifted the towel, and {plan.reveal}."
    )
    world.say(
        f"{hero.id} laughed, and the pirate council clapped as if the pool itself had joined the cheer."
    )
    world.say(
        f"Soon {hero.id} was {ACTIVITIES[params.activity].gerund}, smiling wide, with the surprise shining beside the blue water."
    )

    world.facts["hero"] = hero
    world.facts["surprise_plan"] = plan
    world.facts["prop"] = prop
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qas(world),
        world_qa=world_qas(world),
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


ASP_RULES = r"""
#show valid_story/2.

valid_story(pool, banner) :- place(pool), surprise(banner).
valid_story(pool, crown) :- place(pool), surprise(crown).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "pool"))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    got = sorted(set(asp.atoms(model, "valid_story")))
    want = [("pool", sid) for sid in sorted(SURPRISES)]
    if got == want:
        print(f"OK: clingo gate matches Python registry ({len(got)} surprises).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("  clingo:", got)
    print("  python:", want)
    return 1


CURATED = [
    StoryParams(place="pool", activity="swim", surprise="banner", name="Mina", title="captain"),
    StoryParams(place="pool", activity="swim", surprise="crown", name="Pip", title="matey"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.surprise} at the pool"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
