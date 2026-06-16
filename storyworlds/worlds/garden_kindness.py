#!/usr/bin/env python3
"""
storyworlds/worlds/garden_kindness.py
=====================================

A standalone story world from the seed:

    Words: sparkle, garden, cheerful
    Features: Inner Monologue, Kindness, Moral Value
    Style: Animal Story

The world models a young animal who wants to take a sparkling garden thing. A
mentor predicts, by simulating the action on a copy of the world, which creature
or garden process would be hurt. The story is only valid when a kind alternative
actually protects the threatened role.

Run it
------
    python storyworlds/worlds/garden_kindness.py
    python storyworlds/worlds/garden_kindness.py --all --trace --qa
    python storyworlds/worlds/garden_kindness.py --thing flower --hero rabbit
    python storyworlds/worlds/garden_kindness.py --thing shell --place meadow  # rejected
    python storyworlds/worlds/garden_kindness.py --verify
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
ROLES = {"food", "water", "shelter", "seed"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    depends_on: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "aunt", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "uncle", "fox"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    phrase: str
    affords: set[str]


@dataclass
class GardenThing:
    id: str
    label: str
    phrase: str
    role: str
    dependent: str
    need: str
    take_verb: str
    admire_verb: str
    sparkle: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindPlan:
    id: str
    label: str
    solves: set[str]
    offer: str
    result: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_removed_hurts_dependent(world: World) -> list[str]:
    out: list[str] = []
    for thing in world.entities.values():
        if thing.meters["removed"] < THRESHOLD or not thing.depends_on:
            continue
        dependent = world.get(thing.depends_on)
        sig = ("need", dependent.id, thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dependent.meters[f"missing_{thing.role}"] += 1
        dependent.memes["upset"] += 1
        out.append(f"{dependent.label.capitalize()} would lose important {thing.role}.")
    return out


def _r_kindness_eases_dependent(world: World) -> list[str]:
    out: list[str] = []
    for dependent in world.entities.values():
        if dependent.memes["helped"] < THRESHOLD:
            continue
        sig = ("cheered", dependent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        dependent.memes["upset"] = 0.0
        dependent.memes["joy"] += 1
        out.append(f"{dependent.label.capitalize()} stayed safe and cheerful.")
    return out


CAUSAL_RULES = [
    Rule("removed_hurts_dependent", _r_removed_hurts_dependent),
    Rule("kindness_eases_dependent", _r_kindness_eases_dependent),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def thing_at_risk(thing: GardenThing) -> bool:
    return thing.role in ROLES


def select_plan(thing: GardenThing) -> Optional[KindPlan]:
    for plan in PLANS:
        if thing.role in plan.solves:
            return plan
    return None


def loss_phrase(thing: GardenThing) -> str:
    return {
        "food": f"the {thing.need} it needed",
        "water": f"the {thing.need} it needed",
        "shelter": f"its {thing.need}",
        "seed": f"the {thing.need} it was saving",
    }.get(thing.role, f"its {thing.role}")


def importance_phrase(thing: GardenThing) -> str:
    return {
        "food": f"held {loss_phrase(thing)}",
        "water": f"was {loss_phrase(thing)}",
        "shelter": f"was {loss_phrase(thing)}",
        "seed": f"was {loss_phrase(thing)}",
    }.get(thing.role, f"mattered to the {thing.dependent}")


def take_thing(world: World, hero: Entity, thing: Entity, narrate: bool = True) -> None:
    hero.memes["desire"] += 1
    thing.meters["removed"] += 1
    propagate(world, narrate=narrate)


def predict_harm(world: World, hero: Entity, thing: Entity) -> dict:
    sim = world.copy()
    take_thing(sim, sim.get(hero.id), sim.get(thing.id), narrate=False)
    dependent = sim.get(thing.depends_on or "")
    return {
        "upset": dependent.memes["upset"] >= THRESHOLD,
        "missing": {k: v for k, v in dependent.meters.items() if v},
        "dependent": dependent,
    }


def introduce(world: World, hero: Entity, mentor: Entity) -> None:
    world.say(
        f"Once upon a time, there was a cheerful young {hero.type} named {hero.id}. "
        f"{hero.id} lived near {world.setting.phrase} with {hero.pronoun('possessive')} "
        f"{mentor.label}."
    )


def loves_sparkle(world: World, hero: Entity) -> None:
    hero.memes["love_sparkle"] += 1
    world.say(
        f"{hero.id} loved anything with a sparkle. "
        f'"Maybe I can find one bright thing for my den," {hero.pronoun()} thought.'
    )


def notice(world: World, hero: Entity, thing_cfg: GardenThing, thing: Entity) -> None:
    world.say(
        f"One morning near {world.setting.phrase}, {hero.id} saw {thing_cfg.phrase}. "
        f"It {thing_cfg.sparkle}."
    )


def wants(world: World, hero: Entity, thing_cfg: GardenThing) -> None:
    hero.memes["want"] += 1
    world.say(f"{hero.id} wanted to {thing_cfg.take_verb}.")


def warn(world: World, hero: Entity, mentor: Entity, thing_cfg: GardenThing,
         thing: Entity) -> bool:
    pred = predict_harm(world, hero, thing)
    if not pred["upset"]:
        return False
    dependent = pred["dependent"]
    world.facts["predicted_dependent"] = dependent.label
    world.facts["predicted_role"] = thing.role
    world.say(
        f'"If you take it, {dependent.label} will lose {loss_phrase(thing_cfg)}," '
        f'{hero.pronoun("possessive")} {mentor.label} said.'
    )
    return True


def defies(world: World, hero: Entity, thing_cfg: GardenThing) -> None:
    hero.memes["selfish_pull"] += 1
    world.say(
        f"{hero.id} reached toward it anyway, still thinking about the shine."
    )


def pause_for_kindness(world: World, hero: Entity, mentor: Entity, thing_cfg: GardenThing) -> None:
    hero.memes["inner_conflict"] += 1
    world.say(
        f"Then {hero.id} paused. "
        f'"A sparkle is not very cheerful if someone else gets hurt," '
        f"{hero.pronoun()} thought."
    )


def compromise(world: World, hero: Entity, mentor: Entity, thing_cfg: GardenThing,
               thing: Entity) -> KindPlan:
    plan = select_plan(thing_cfg)
    if plan is None:
        raise StoryError(explain_rejection(world.setting, thing_cfg))
    dependent = world.get(thing.depends_on or "")
    dependent.memes["helped"] += 1
    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {mentor.label} smiled and said, '
        f'"Let us {plan.offer}."'
    )
    world.say(plan.result.format(hero=hero.id, thing=thing_cfg.label, dependent=dependent.label))
    return plan


def moral(world: World, hero: Entity, thing_cfg: GardenThing) -> None:
    world.say(
        f"{hero.id} learned that kindness can make a garden sparkle brighter than taking."
    )


def tell(setting: Setting, thing_cfg: GardenThing, hero_name: str, hero_type: str,
         mentor_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(hero_name, kind="character", type=hero_type, label=hero_name))
    mentor = world.add(Entity("Mentor", kind="character", type=mentor_type,
                              label=mentor_type))
    dependent = world.add(Entity("Dependent", kind="character", type=thing_cfg.dependent,
                                 label=f"the {thing_cfg.dependent}"))
    thing = world.add(Entity("Thing", type=thing_cfg.id, label=thing_cfg.label,
                             phrase=thing_cfg.phrase, depends_on=dependent.id,
                             role=thing_cfg.role))

    introduce(world, hero, mentor)
    loves_sparkle(world, hero)
    world.para()
    notice(world, hero, thing_cfg, thing)
    wants(world, hero, thing_cfg)
    warn(world, hero, mentor, thing_cfg, thing)
    defies(world, hero, thing_cfg)
    world.para()
    pause_for_kindness(world, hero, mentor, thing_cfg)
    plan = compromise(world, hero, mentor, thing_cfg, thing)
    moral(world, hero, thing_cfg)
    world.facts.update(hero=hero, mentor=mentor, dependent=dependent, thing=thing,
                       thing_cfg=thing_cfg, setting=setting, plan=plan)
    return world


SETTINGS = {
    "garden": Setting("a bright garden", {"flower", "dewdrop", "seed"}),
    "meadow": Setting("a sunny meadow", {"flower", "dewdrop"}),
    "greenhouse": Setting("a warm greenhouse", {"flower", "seed", "leaf"}),
    "stone_path": Setting("a mossy garden path", {"shell", "dewdrop", "leaf"}),
}

THINGS = {
    "flower": GardenThing(
        "flower", "flower", "a golden flower", "food", "butterfly", "pollen",
        "pick the sparkling flower", "look at the flower",
        "sparkled like a tiny sun", {"flower", "pollen"},
    ),
    "dewdrop": GardenThing(
        "dewdrop", "dewdrop", "a round dewdrop on a leaf", "water", "bee", "drink",
        "carry the dewdrop away", "watch the dewdrop",
        "sparkled like a little star", {"dew", "water"},
    ),
    "seed": GardenThing(
        "seed", "seed", "a shiny striped seed", "seed", "mouse", "winter seed",
        "take the seed home", "roll the seed gently",
        "sparkled under a bit of sun", {"seed", "garden"},
    ),
    "shell": GardenThing(
        "shell", "shell", "a pearly snail shell", "shelter", "snail", "home",
        "keep the shell", "touch the shell softly",
        "sparkled beside the path", {"shell", "shelter"},
    ),
    "leaf": GardenThing(
        "leaf", "leaf", "a silver-green leaf", "shelter", "ladybug", "shade",
        "pull the leaf down", "count the leaf veins",
        "sparkled where the rain had kissed it", {"leaf", "shelter"},
    ),
}

PLANS = [
    KindPlan(
        "drawing", "a drawing", {"food", "shelter"},
        "make a picture of the sparkle and leave the real one here",
        "{hero} made a careful picture of the {thing}, and {dependent} kept what it needed.",
        {"drawing", "kindness"},
    ),
    KindPlan(
        "pebble", "a shiny pebble", {"water"},
        "find a shiny pebble instead and leave the water for drinking",
        "{hero} found a bright pebble, and {dependent} still had a drink.",
        {"pebble", "water"},
    ),
    KindPlan(
        "planting", "planting", {"seed"},
        "plant the seed and mark the spot with a little twig",
        "{hero} planted the seed, and {dependent} would have more to share later.",
        {"seed", "growth"},
    ),
]

HEROES = {
    "rabbit": ["Pip", "Nola", "Moss", "Lulu"],
    "squirrel": ["Tavi", "Mira", "Nim", "Penny"],
    "hedgehog": ["Bram", "Hazel", "Otto", "Mina"],
}
MENTORS = ["mother", "father", "aunt", "uncle"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for thing_id in setting.affords:
            thing = THINGS[thing_id]
            if thing_at_risk(thing) and select_plan(thing):
                combos.append((place, thing_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    thing: str
    hero: str
    name: str
    mentor: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "flower": [("Why do butterflies visit flowers?",
                "Butterflies drink nectar from flowers, and pollen can help new plants grow.")],
    "pollen": [("What is pollen?",
                "Pollen is a tiny powder from flowers that helps many plants make seeds.")],
    "dew": [("What is dew?",
             "Dew is tiny drops of water that collect on leaves and grass in cool air.")],
    "water": [("Why do small animals need water?",
               "Small animals need water to stay alive, just like people do.")],
    "seed": [("What can a seed become?",
              "A seed can grow into a new plant when it has soil, water, light, and time.")],
    "garden": [("Why is sharing good for a garden?",
                "Sharing lets animals and plants keep helping each other, so the garden stays healthy.")],
    "shell": [("Why might a shell matter to a snail?",
               "A snail's shell protects its soft body and gives it a safe place to rest.")],
    "shelter": [("Why do little creatures need shelter?",
                 "Shelter keeps little creatures safer from weather and danger.")],
    "leaf": [("How can a leaf help an insect?",
              "A leaf can give shade, a place to hide, or a spot to rest.")],
    "kindness": [("What is kindness?",
                  "Kindness means thinking about how your choice affects someone else and trying to help.")],
}
KNOWLEDGE_ORDER = ["flower", "pollen", "dew", "water", "seed", "garden",
                   "shell", "shelter", "leaf", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, thing = f["hero"], f["thing_cfg"]
    return [
        'Write an animal story for young children using the words "sparkle", '
        '"garden", and "cheerful".',
        f"Tell a gentle moral story where a young {hero.type} named {hero.id} "
        f"wants to {thing.take_verb} but learns to protect the {thing.dependent}.",
        "Write a short story with inner monologue where kindness matters more "
        "than keeping a shiny treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, mentor, dependent, thing, plan = (
        f["hero"], f["mentor"], f["dependent"], f["thing_cfg"], f["plan"]
    )
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    return [
        ("Who is the story about?",
         f"It is about a cheerful young {hero.type} named {hero.id} and {pos} {mentor.label}."),
        (f"What did {hero.id} want to take?",
         f"{hero.id} wanted to {thing.take_verb} because it sparkled near {world.setting.phrase}."),
        (f"Who would be hurt if {hero.id} took it?",
         f"{dependent.label.capitalize()} would be hurt because the {thing.label} {importance_phrase(thing)}."),
        ("How did the mentor know there might be a problem?",
         f"{mentor.label.capitalize()} imagined what would happen if {hero.id} took the {thing.label}. "
         f"In that prediction, {dependent.label} would lose {loss_phrase(thing)}."),
        ("How did they solve the problem?",
         f"They chose to {plan.offer}. That let {hero.id} enjoy the sparkle while leaving the {thing.label} for {dependent.label}."),
        (f"What did {hero.id} learn?",
         f"{hero.id} learned that kindness can make a garden feel brighter than keeping a shiny thing."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["thing_cfg"].tags) | set(f["plan"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.depends_on:
            bits.append(f"depends_on={ent.depends_on}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("garden", "flower", "rabbit", "Pip", "mother"),
    StoryParams("meadow", "dewdrop", "squirrel", "Mira", "aunt"),
    StoryParams("greenhouse", "seed", "hedgehog", "Bram", "father"),
    StoryParams("stone_path", "shell", "rabbit", "Nola", "uncle"),
    StoryParams("greenhouse", "leaf", "squirrel", "Tavi", "mother"),
]


def explain_rejection(setting: Setting, thing: GardenThing) -> str:
    if thing.id not in setting.affords:
        return (f"(No story: {setting.phrase} does not contain {thing.phrase}, "
                "so the world cannot honestly stage that choice.)")
    if not thing_at_risk(thing):
        return f"(No story: taking the {thing.label} does not threaten a tracked garden role.)"
    return (f"(No story: the catalog has no kind alternative that protects "
            f"{thing.role}, so the compromise would not solve the problem.)")


ASP_RULES = r"""
at_risk(T) :- thing_role(T, R), role(R).
has_plan(T) :- thing_role(T, R), solves(_, R).
valid(P, T) :- affords(P, T), at_risk(T), has_plan(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for role in sorted(ROLES):
        lines.append(asp.fact("role", role))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for thing_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, thing_id))
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        lines.append(asp.fact("thing_role", thing_id, thing.role))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan.id))
        for role in sorted(plan.solves):
            lines.append(asp.fact("solves", plan.id, role))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: sparkle, garden, kindness. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--name")
    ap.add_argument("--mentor", choices=MENTORS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.thing:
        setting, thing = SETTINGS[args.place], THINGS[args.thing]
        if (args.place, args.thing) not in valid_combos():
            raise StoryError(explain_rejection(setting, thing))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.thing is None or c[1] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, thing = rng.choice(combos)
    hero = args.hero or rng.choice(sorted(HEROES))
    name = args.name or rng.choice(HEROES[hero])
    mentor = args.mentor or rng.choice(MENTORS)
    return StoryParams(place, thing, hero, name, mentor)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], THINGS[params.thing],
                 params.name, params.hero, params.mentor)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, thing) combos:\n")
        for place, thing in combos:
            print(f"  {place:10} {thing}")
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
            header = f"### {p.name}: {p.thing} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
