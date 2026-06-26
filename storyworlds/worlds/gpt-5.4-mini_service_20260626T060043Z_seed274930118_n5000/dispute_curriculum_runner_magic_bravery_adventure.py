#!/usr/bin/env python3
"""
A standalone story world about a runner, a training curriculum, and a dispute
about using magic versus relying on bravery and effort.

The premise is adventure-flavored and child-facing: a young runner wants to
finish a hard trail race. A coach has written a curriculum of careful practice,
but a shiny bit of magic tempts the runner to skip the hard parts. A dispute
grows when the runner wants glory now and the coach wants courage built slowly.
The ending turns on bravery: the runner chooses the real training, uses the
magic only in a harmless, supportive way, and reaches the finish with a stronger
heart.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- eager import of shared result containers
- lazy ASP import inside helpers
- StoryParams, registries, parser, resolve_params, generate, emit, main
- Python reasonableness gate plus inline ASP_RULES twin
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
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    magical: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "coach"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Route:
    place: str
    weather: str
    terrain: str
    challenge: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Curriculum:
    id: str
    name: str
    steps: list[str]
    needs: set[str]
    teaches: set[str]


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    effect: str
    allowed: set[str]
    risky: bool = False


@dataclass
class StoryParams:
    route: str
    curriculum: str
    magic: str
    runner_name: str
    runner_type: str
    coach_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, route: Route) -> None:
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.route)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROUTES = {
    "forest": Route(
        place="the forest track",
        weather="cool",
        terrain="roots and pine needles",
        challenge="a steep climb",
        afford={"training", "sprint"},
    ),
    "hill": Route(
        place="the hill trail",
        weather="windy",
        terrain="loose stones",
        challenge="a long climb",
        afford={"training", "sprint"},
    ),
    "river": Route(
        place="the river path",
        weather="misty",
        terrain="damp grass",
        challenge="a narrow bend",
        afford={"training", "sprint"},
    ),
}

CURRICULA = {
    "steps": Curriculum(
        id="steps",
        name="a careful step-by-step curriculum",
        steps=[
            "warm up",
            "practice footwork",
            "rest at the water break",
            "try the hill again",
        ],
        needs={"training"},
        teaches={"bravery", "patience"},
    ),
    "breath": Curriculum(
        id="breath",
        name="a breathing curriculum for tough climbs",
        steps=[
            "breathe in for four",
            "breathe out for four",
            "run the first stretch slowly",
            "finish with a brave sprint",
        ],
        needs={"training", "sprint"},
        teaches={"bravery", "focus"},
    ),
    "trail": Curriculum(
        id="trail",
        name="a trail runner's curriculum",
        steps=[
            "check the shoes",
            "listen to the trail",
            "keep a steady pace",
            "save energy for the end",
        ],
        needs={"training"},
        teaches={"bravery", "steadiness"},
    ),
}

MAGIC_ITEMS = {
    "glow_shoes": MagicItem(
        id="glow_shoes",
        label="glow shoes",
        phrase="a pair of glow shoes",
        effect="they feel light and fast",
        allowed={"training"},
        risky=True,
    ),
    "wind_charm": MagicItem(
        id="wind_charm",
        label="wind charm",
        phrase="a small wind charm",
        effect="it cools tired cheeks and clears the mind",
        allowed={"training", "sprint"},
        risky=False,
    ),
    "lantern_mark": MagicItem(
        id="lantern_mark",
        label="lantern paint",
        phrase="a streak of lantern paint",
        effect="it shines on the path and helps the runner see the curve",
        allowed={"training", "sprint"},
        risky=False,
    ),
}

NAMES = ["Milo", "Nina", "Tess", "Arlo", "June", "Kai", "Lena", "Owen"]
TYPES = ["boy", "girl"]
COACH_TYPES = ["mother", "father", "coach"]
TRAITS = ["brave", "curious", "determined", "restless", "cheerful"]

CURATED = [
    StoryParams("forest", "steps", "wind_charm", "Milo", "boy", "coach", "determined"),
    StoryParams("hill", "breath", "lantern_mark", "Nina", "girl", "mother", "curious"),
    StoryParams("river", "trail", "glow_shoes", "Tess", "girl", "father", "restless"),
]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A route works when the curriculum can be done there and the magic is allowed.
valid_story(R, C, M) :- route(R), curriculum(C), magic(M),
                        route_affords(R, training),
                        curriculum_needs(C, training),
                        magic_allowed(M, training),
                        not magic_risky(M).

% Risky magic can still appear only if the story has a real dispute and the
% runner chooses bravery over shortcut.
valid_story(R, C, M) :- route(R), curriculum(C), magic(M),
                        route_affords(R, training),
                        curriculum_needs(C, training),
                        magic_allowed(M, training),
                        magic_risky(M),
                        has_dispute(R, C, M),
                        chooses_bravery(R, C, M).

% Dispute is about wanting to skip the curriculum.
has_dispute(R, C, M) :- route(R), curriculum(C), magic(M), risky_shortcut(M).

chooses_bravery(R, C, M) :- route(R), curriculum(C), magic(M), bravery_choice(R, C, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_place", rid, r.place))
        for a in sorted(r.afford):
            lines.append(asp.fact("route_affords", rid, a))
    for cid, c in CURRICULA.items():
        lines.append(asp.fact("curriculum", cid))
        for n in sorted(c.needs):
            lines.append(asp.fact("curriculum_needs", cid, n))
        for t in sorted(c.teaches):
            lines.append(asp.fact("curriculum_teaches", cid, t))
    for mid, m in MAGIC_ITEMS.items():
        lines.append(asp.fact("magic", mid))
        if m.risky:
            lines.append(asp.fact("magic_risky", mid))
            lines.append(asp.fact("risky_shortcut", mid))
        for a in sorted(m.allowed):
            lines.append(asp.fact("magic_allowed", mid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    asp_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if asp_set - py_set:
        print("  only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in python:", sorted(py_set - asp_set))
    return 1

# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid, route in ROUTES.items():
        for cid, cur in CURRICULA.items():
            if "training" not in route.afford:
                continue
            if "training" not in cur.needs:
                continue
            for mid, magic in MAGIC_ITEMS.items():
                if "training" not in magic.allowed and "sprint" not in magic.allowed:
                    continue
                if magic.risky:
                    # only if the story can turn into a dispute and end bravely
                    combos.append((rid, cid, mid))
                else:
                    combos.append((rid, cid, mid))
    return combos


def explain_rejection(route: Route, cur: Curriculum, magic: MagicItem) -> str:
    return (
        f"(No story: the {cur.name} and {magic.label} do not fit a believable "
        f"runner adventure on {route.place}. The dispute needs a real choice, and "
        f"this combination does not create one.)"
    )

# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_outcome(world: World, runner: Entity, route: Route, magic: MagicItem) -> dict:
    sim = world.copy()
    sim.facts["using_magic"] = magic.id
    if magic.risky:
        sim.facts["shortcut_temptation"] = True
    # if risky magic, the runner's confidence rises but bravery is only resolved by choice
    return {
        "temptation": magic.risky,
        "clean_finish": not magic.risky,
    }


def intro(world: World, runner: Entity, coach: Entity) -> None:
    world.say(
        f"{runner.id} was a {runner.traits[0]} young runner who loved the sound of "
        f"fast feet on dirt."
    )
    world.say(
        f"{coach.pronoun('subject').capitalize()} had built a small curriculum of "
        f"careful lessons so {runner.id} could get stronger one day at a time."
    )


def describe_route(world: World, route: Route) -> None:
    world.say(
        f"The goal was {route.challenge} on {route.place}, where the trail curled "
        f"past {route.terrain}."
    )


def dispute(world: World, runner: Entity, coach: Entity, cur: Curriculum, magic: MagicItem) -> None:
    runner.memes["want_speed"] = runner.memes.get("want_speed", 0) + 1
    world.say(
        f"But {runner.id} saw {magic.phrase} and wanted to use it to win right away."
    )
    world.say(
        f"{coach.id} pointed at the {cur.name} and said it had to be followed in order."
    )
    if magic.risky:
        world.say(
            f"That started a dispute, because {runner.id} wanted a shortcut and {coach.id} "
            f"wanted brave practice instead."
        )


def train(world: World, cur: Curriculum, runner: Entity) -> None:
    runner.memes["focus"] = runner.memes.get("focus", 0) + 1
    world.say(f"They began with {cur.steps[0]}.")
    world.say(f"Then they moved through {cur.steps[1]} and {cur.steps[2]}.")


def tempt_magic(world: World, runner: Entity, magic: MagicItem) -> None:
    if magic.risky:
        runner.memes["tempted"] = runner.memes.get("tempted", 0) + 1
        world.say(
            f"{magic.label} sparkled so brightly that {runner.id} almost grabbed it first."
        )
    else:
        world.say(
            f"{magic.label} gave a calm helpful glow, not a shortcut, just a little aid."
        )


def brave_choice(world: World, runner: Entity, coach: Entity, cur: Curriculum, magic: MagicItem) -> None:
    runner.memes["bravery"] = runner.memes.get("bravery", 0) + 1
    runner.memes["dispute"] = 0
    world.say(
        f"At last, {runner.id} took a breath and chose the curriculum instead of the shortcut."
    )
    if magic.risky:
        world.say(
            f"{runner.id} tucked the {magic.label} into a pocket and promised to save it for cheering, not cheating."
        )
    else:
        world.say(
            f"{runner.id} kept the {magic.label} for support and stayed true to the training."
        )


def finish(world: World, runner: Entity, coach: Entity, route: Route, cur: Curriculum, magic: MagicItem) -> None:
    world.say(
        f"On the last stretch, {runner.id} ran the hill with steady steps and a brave heart."
    )
    world.say(
        f"The finish line came into view, and {runner.id} crossed it with {magic.effect}."
    )
    world.say(
        f"{coach.id} smiled because the real victory was not only speed but the courage to do the hard thing."
    )


def tell(route: Route, cur: Curriculum, magic: MagicItem,
         runner_name: str, runner_type: str, coach_type: str, trait: str) -> World:
    world = World(route)
    runner = world.add(Entity(
        id=runner_name,
        kind="character",
        type=runner_type,
        traits=[trait, "young"],
    ))
    coach = world.add(Entity(
        id="Coach",
        kind="character",
        type=coach_type,
        label="the coach",
    ))
    world.facts.update(route=route, curriculum=cur, magic=magic, runner=runner, coach=coach)

    intro(world, runner, coach)
    world.para()
    describe_route(world, route)
    dispute(world, runner, coach, cur, magic)
    tempt_magic(world, runner, magic)
    train(world, cur, runner)
    brave_choice(world, runner, coach, cur, magic)
    world.para()
    finish(world, runner, coach, route, cur, magic)
    world.facts["resolved"] = True
    return world

# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route: Route = f["route"]
    cur: Curriculum = f["curriculum"]
    magic: MagicItem = f["magic"]
    runner: Entity = f["runner"]
    return [
        f'Write a short adventure story for a child about {runner.id}, a runner, and a dispute over {magic.label}.',
        f'Tell a brave story where a young runner follows {cur.name} on {route.place} and chooses training over a shortcut.',
        f'Write a simple adventure with the words “runner”, “curriculum”, and “magic” that ends with courage winning.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    runner: Entity = f["runner"]
    coach: Entity = f["coach"]
    route: Route = f["route"]
    cur: Curriculum = f["curriculum"]
    magic: MagicItem = f["magic"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {runner.id}, a {runner.traits[0]} runner who wanted to finish the trail adventure.",
        ),
        QAItem(
            question=f"What did {runner.id} and {coach.label} disagree about?",
            answer=f"They had a dispute about whether to use {magic.label} as a shortcut or follow the {cur.name}.",
        ),
        QAItem(
            question=f"Where did the final brave run happen?",
            answer=f"It happened on {route.place}, where the trail had {route.terrain} and a hard {route.challenge}.",
        ),
    ]
    if magic.risky:
        qa.append(
            QAItem(
                question=f"Why was {magic.label} a problem at first?",
                answer=f"It was tempting because it seemed fast, but it could have replaced the honest work of the curriculum.",
            )
        )
    qa.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"{runner.id} chose bravery, kept training, and crossed the finish line stronger than before.",
        )
    )
    return qa


WORLD_KNOWLEDGE = {
    "runner": [
        ("What is a runner?",
         "A runner is a person who practices running and moves fast on foot."),
    ],
    "curriculum": [
        ("What is a curriculum?",
         "A curriculum is a planned set of lessons or steps that helps someone learn in order."),
    ],
    "magic": [
        ("What is magic in a story?",
         "Magic in a story is something unusual or enchanted that can change how events feel or happen."),
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery means doing something hard or scary even when you feel nervous."),
    ],
    "dispute": [
        ("What is a dispute?",
         "A dispute is a disagreement when two people want different things."),
    ],
    "trail": [
        ("What is a trail?",
         "A trail is a narrow path outdoors that people can walk or run on."),
    ],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question=q, answer=a)
        for key in ["runner", "curriculum", "magic", "bravery", "dispute", "trail"]
        for q, a in WORLD_KNOWLEDGE[key]
    ]

# ---------------------------------------------------------------------------
# Formatting / trace
# ---------------------------------------------------------------------------

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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  route={world.route.place}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: dispute, curriculum, runner, magic, bravery.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--curriculum", choices=CURRICULA)
    ap.add_argument("--magic", choices=MAGIC_ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=TYPES)
    ap.add_argument("--coach", choices=COACH_TYPES)
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
    route = args.route or rng.choice(list(ROUTES))
    curriculum = args.curriculum or rng.choice(list(CURRICULA))
    magic = args.magic or rng.choice(list(MAGIC_ITEMS))
    r = ROUTES[route]
    c = CURRICULA[curriculum]
    m = MAGIC_ITEMS[magic]
    if args.route and args.curriculum and args.magic:
        if (route, curriculum, magic) not in valid_combos():
            raise StoryError(explain_rejection(r, c, m))
    gender = args.gender or rng.choice(TYPES)
    name = args.name or rng.choice(NAMES)
    coach = args.coach or rng.choice(COACH_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(route, curriculum, magic, name, gender, coach, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        ROUTES[params.route],
        CURRICULA[params.curriculum],
        MAGIC_ITEMS[params.magic],
        params.runner_name,
        params.runner_type,
        params.coach_type,
        params.trait,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_stories()
        print(f"{len(items)} compatible route/curriculum/magic combos:\n")
        for rid, cid, mid in items:
            print(f"  {rid:8} {cid:10} {mid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [
            generate(StoryParams(p, c, m, "Milo", "boy", "coach", "brave"))
            for p, c, m in CURATED
        ]
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
            header = f"### {p.runner_name}: {p.route} / {p.curriculum} / {p.magic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
