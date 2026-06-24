#!/usr/bin/env python3
"""
A small Animal Story world about a subtle, foreshadowed, suspenseful rescue at
the pond.

Premise:
- A young animal notices a tiny sign that something is wrong.
- The sign is subtle at first, then grows into suspense.
- A careful helper acts in time, and the ending proves the change.

The domain is intentionally small:
- One main animal, one helper animal, one vulnerable creature, one place.
- Physical meters represent distance, strength, weather, and danger.
- Emotional memes represent worry, courage, relief, and trust.

The story engine chooses only reasonable combinations:
- The place must make sense for the danger.
- The helper must have the right kind of tool/ability.
- The ending must be caused by the simulated world state, not by a frozen template.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "animal" | "thing"
    species: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.species in {"fox", "rabbit", "deer", "bear", "mouse", "squirrel"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    habitat: str
    clues: list[str] = field(default_factory=list)
    dangers: set[str] = field(default_factory=set)
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sign: str
    danger: str
    zone: set[str]
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    tool: str
    tool_kind: str
    action: str
    rescue_tail: str
    supports: set[str] = field(default_factory=set)
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------

PLACES = {
    "pond": Place(
        name="the pond",
        habitat="water",
        clues=["a thin ripple", "a reed bending low", "a patch of darker water"],
        dangers={"sinking", "cold"},
        affords={"look", "swim", "call"},
    ),
    "meadow": Place(
        name="the meadow",
        habitat="grass",
        clues=["a broken stalk", "a hush in the grass", "a feather drifting low"],
        dangers={"lost", "wind"},
        affords={"look", "run", "call"},
    ),
    "wood": Place(
        name="the wood",
        habitat="trees",
        clues=["a snapped twig", "a leaf turning in the breeze", "a faraway rustle"],
        dangers={"lost", "dark"},
        affords={"look", "hide", "call"},
    ),
}

ACTIVITIES = {
    "sinking_frog": Activity(
        id="sinking_frog",
        verb="help the little frog",
        gerund="helping the little frog",
        sign="a tiny bubble trail near the edge of the pond",
        danger="sinking",
        zone={"water"},
        clue="the water looked as if something small was struggling",
        tags={"frog", "water", "pond", "subtle", "suspense"},
    ),
    "lost_duckling": Activity(
        id="lost_duckling",
        verb="find the duckling",
        gerund="searching for the duckling",
        sign="a soft peep from the reeds",
        danger="lost",
        zone={"grass", "water"},
        clue="the reeds kept whispering like they were hiding a secret",
        tags={"duckling", "water", "subtle", "foreshadowing", "suspense"},
    ),
    "shivering_kit": Activity(
        id="shivering_kit",
        verb="bring warmth to the little kit",
        gerund="hurrying to the little kit",
        sign="a small sneeze from behind a fallen log",
        danger="cold",
        zone={"trees", "grass"},
        clue="the air felt ordinary, but one tiny sound made it not feel ordinary anymore",
        tags={"fox", "cold", "subtle", "foreshadowing", "suspense"},
    ),
}

HELPERS = {
    "lily": Helper(
        id="lily",
        label="the little rabbit",
        tool="a round leaf",
        tool_kind="leaf",
        action="float the leaf like a tiny boat",
        rescue_tail="pushed the leaf out and guided it slowly toward the edge",
        supports={"water", "cold"},
        protects={"water"},
    ),
    "mossy": Helper(
        id="mossy",
        label="the mossy turtle",
        tool="a sturdy reed",
        tool_kind="reed",
        action="reach where small paws could not",
        rescue_tail="used the reed to pull the little one closer, inch by inch",
        supports={"water", "lost"},
        protects={"water", "grass"},
    ),
    "bramble": Helper(
        id="bramble",
        label="the brave hedgehog",
        tool="a soft blanket of dry moss",
        tool_kind="moss",
        action="wrap up a shivery animal",
        rescue_tail="tucked the moss around the cold little body until the trembling slowed",
        supports={"cold", "lost"},
        protects={"trees", "grass"},
    ),
}

CHARACTER_NAMES = {
    "rabbit": ["Pip", "Nell", "Milo", "Luna", "Bibi"],
    "turtle": ["Moss", "Toby", "Tara", "Ollie", "June"],
    "hedgehog": ["Bramble", "Pea", "Nip", "Daisy", "Finn"],
    "frog": ["Tiny", "Hopper", "Midge"],
    "duckling": ["Puddle", "Beak", "Sunny"],
    "fox": ["Flick", "Rusty", "Amber"],
}

SPECIES_FOR_ACT = {
    "sinking_frog": "frog",
    "lost_duckling": "duckling",
    "shivering_kit": "fox",
}

# -----------------------------------------------------------------------------
# Inline ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is subtle if it appears before the danger becomes obvious.
subtle(A) :- clue(A).

% An activity is risky in a place when its danger is among the place's dangers.
at_risk(P, A) :- place(P), activity(A), place_danger(P, D), danger_of(A, D).

% A helper is compatible when its supports match the activity danger.
compatible(H, A) :- helper(H), activity(A), helper_support(H, D), danger_of(A, D).

% A story is reasonable only if there is both risk and a compatible helper.
valid_story(P, A, H) :- at_risk(P, A), compatible(H, A).

#show valid_story/3.
#show at_risk/2.
#show subtle/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for d in sorted(place.dangers):
            lines.append(asp.fact("place_danger", pid, d))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("danger_of", aid, act.danger))
        lines.append(asp.fact("clue", aid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for d in sorted(helper.supports):
            lines.append(asp.fact("helper_support", hid, d))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program())
    triples = sorted(set(asp.atoms(model, "valid_story")))
    return [(a, b, c) for a, b, c in triples]


# -----------------------------------------------------------------------------
# Simulation
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    helper: str
    hero_name: str
    hero_species: str
    vulnerable_name: str
    vulnerable_species: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for act in ACTIVITIES:
            for helper in HELPERS:
                if ACTIVITIES[act].danger in HELPERS[helper].supports and ACTIVITIES[act].danger in PLACES[place].dangers:
                    combos.append((place, act, helper))
    return combos


class Runtime:
    def __init__(self, world: World) -> None:
        self.world = world

    def notify(self, ent: Entity, key: str, amount: float = 1.0) -> None:
        ent.meters[key] = ent.meters.get(key, 0.0) + amount

    def feel(self, ent: Entity, key: str, amount: float = 1.0) -> None:
        ent.memes[key] = ent.memes.get(key, 0.0) + amount


def predict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    activity = ACTIVITIES[params.activity]
    helper = HELPERS[params.helper]
    vulnerable = sim.get("vulnerable")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    if activity.danger == "sinking":
        vulnerable.meters["danger"] = vulnerable.meters.get("danger", 0.0) + 1.0
    elif activity.danger == "lost":
        vulnerable.memes["worry"] = vulnerable.memes.get("worry", 0.0) + 1.0
    else:
        vulnerable.meters["cold"] = vulnerable.meters.get("cold", 0.0) + 1.0
    return {
        "danger": activity.danger,
        "helper": helper.id,
        "is_bad": True,
    }


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    act = ACTIVITIES[params.activity]
    helper_def = HELPERS[params.helper]

    hero = world.add(Entity(id="hero", kind="animal", species=params.hero_species, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="animal", species=helper_def.id, label=helper_def.label))
    vulnerable = world.add(Entity(id="vulnerable", kind="animal", species=params.vulnerable_species, label=params.vulnerable_name))

    hero.memes["subtle_notice"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] = 0.0
    helper.memes["calm"] = 1.0
    vulnerable.meters["danger"] = 0.0
    vulnerable.memes["fear"] = 0.0

    world.facts.update(hero=hero, helper=helper, vulnerable=vulnerable, activity=act, place=place, helper_def=helper_def)

    # Act 1: a subtle clue.
    world.say(
        f"One quiet day at {place.name}, {hero.label} noticed {act.sign}."
    )
    world.say(
        f"It was only a small thing, but the clue did not feel ordinary."
    )
    world.say(
        f"{hero.label} looked again and saw {act.clue}."
    )

    # Act 2: suspense grows.
    world.para()
    hero.memes["worry"] += 1.0
    vulnerable.meters["danger"] += 1.0
    world.say(
        f"{hero.label} followed the clue and got closer to the water's edge."
        if act.danger == "sinking"
        else f"{hero.label} listened hard and crept toward the reeds."
        if act.danger == "lost"
        else f"{hero.label} hurried deeper into the trees."
    )
    world.say(
        f"Then {vulnerable.label} made a tiny sound, and the day felt suddenly still."
    )
    world.say(
        f"{hero.label} held still for a breath, because now the worry had turned into suspense."
    )

    # Act 3: rescue.
    world.para()
    helper.memes["calm"] += 1.0
    hero.memes["hope"] += 1.0
    vulnerable.memes["fear"] += 1.0
    world.say(
        f"Just then, {helper.label} arrived with {helper_def.tool}."
    )
    world.say(
        f"{helper.label} knew how to {helper_def.action}, so they did not rush."
    )
    world.say(
        f"{helper.label} {helper_def.rescue_tail}."
    )

    vulnerable.meters["danger"] = 0.0
    vulnerable.memes["fear"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["hope"] += 1.0

    world.para()
    world.say(
        f"In the end, {vulnerable.label} was safe, and {hero.label} could finally breathe out."
    )
    world.say(
        f"The little clue from earlier had been a warning, and the warning had helped save the day."
    )

    return world


# -----------------------------------------------------------------------------
# QA generation
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    helper = f["helper_def"]
    place = f["place"]
    return [
        f'Write a gentle animal story with a subtle clue and suspense at {place.name}.',
        f"Tell a story where a small animal notices {act.sign} and gets help from {helper.label}.",
        f'Write a child-friendly story that includes the words "subtle" and "suspense" and ends with a safe rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper_def: Helper = f["helper_def"]
    helper: Entity = f["helper"]
    vulnerable: Entity = f["vulnerable"]
    act: Activity = f["activity"]
    place: Place = f["place"]

    return [
        QAItem(
            question=f"What did {hero.label} notice at {place.name}?",
            answer=f"{hero.label} noticed {act.sign}, which was a subtle clue that something was wrong.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because {hero.label} got closer, {vulnerable.label} made a tiny sound, and nobody knew right away if they could help in time.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} arrived with {helper_def.tool} and used it to {helper_def.action}, which brought {vulnerable.label} back to safety.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {vulnerable.label} was safe and {hero.label} felt relief instead of worry.",
        ),
    ]


KNOWLEDGE = {
    "frog": [
        ("What does a frog like to do?", "A frog likes to hop, swim, and sit near water."),
    ],
    "duckling": [
        ("What is a duckling?", "A duckling is a baby duck."),
    ],
    "fox": [
        ("What is a fox?", "A fox is a wild animal with a bushy tail and quick feet."),
    ],
    "water": [
        ("Why do some animals live near water?", "Some animals live near water because they need water to drink, eat, or stay cool."),
    ],
    "leaf": [
        ("What can a leaf do in water?", "A leaf can float on water if it is light enough."),
    ],
    "reed": [
        ("What is a reed?", "A reed is a tall plant that grows near water and can bend without breaking easily."),
    ],
    "moss": [
        ("What is moss?", "Moss is a soft green plant that grows close to the ground and feels spongy."),
    ],
    "subtle": [
        ("What does subtle mean?", "Subtle means small or not easy to notice right away."),
    ],
    "suspense": [
        ("What is suspense?", "Suspense is the feeling of waiting to find out what will happen next."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.update({"subtle", "suspense"})
    helper = f["helper_def"]
    tags.add(helper.tool_kind)
    tags.add(f["activity"].danger if f["activity"].danger in KNOWLEDGE else "")
    out: list[QAItem] = []
    for tag in ["subtle", "suspense", "water", "leaf", "reed", "moss", "frog", "duckling", "fox"]:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:10} ({e.species:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


# -----------------------------------------------------------------------------
# Parameter selection
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    helper: str
    hero_name: str
    hero_species: str
    vulnerable_name: str
    vulnerable_species: str
    seed: Optional[int] = None


def explain_rejection() -> str:
    return "(No story: the chosen place, danger, and helper do not fit together well enough.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with subtle foreshadowing and suspense.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.place or args.activity or args.helper:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.activity is None or c[1] == args.activity)
            and (args.helper is None or c[2] == args.helper)
        ]
    if not combos:
        raise StoryError(explain_rejection())

    place, activity, helper = rng.choice(sorted(combos))
    act = ACTIVITIES[activity]
    hero_species = "rabbit" if helper == "lily" else "turtle" if helper == "mossy" else "hedgehog"
    vulnerable_species = SPECIES_FOR_ACT[activity]

    hero_name = args.name or rng.choice(CHARACTER_NAMES[hero_species])
    vulnerable_name = rng.choice(CHARACTER_NAMES[vulnerable_species])
    return StoryParams(
        place=place,
        activity=activity,
        helper=helper,
        hero_name=hero_name,
        hero_species=hero_species,
        vulnerable_name=vulnerable_name,
        vulnerable_species=vulnerable_species,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# -----------------------------------------------------------------------------
# ASP verification
# -----------------------------------------------------------------------------

def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

CURATED = [
    StoryParams(
        place="pond",
        activity="sinking_frog",
        helper="mossy",
        hero_name="Pip",
        hero_species="rabbit",
        vulnerable_name="Midge",
        vulnerable_species="frog",
    ),
    StoryParams(
        place="pond",
        activity="lost_duckling",
        helper="lily",
        hero_name="Nell",
        hero_species="rabbit",
        vulnerable_name="Sunny",
        vulnerable_species="duckling",
    ),
    StoryParams(
        place="wood",
        activity="shivering_kit",
        helper="bramble",
        hero_name="Milo",
        hero_species="hedgehog",
        vulnerable_name="Flick",
        vulnerable_species="fox",
    ),
]


def asp_show_program() -> str:
    return asp_program()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
