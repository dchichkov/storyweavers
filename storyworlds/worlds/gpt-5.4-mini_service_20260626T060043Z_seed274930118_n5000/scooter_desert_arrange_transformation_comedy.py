#!/usr/bin/env python3
"""
A small storyworld about a child, a scooter, a desert, and a comic transformation.

Premise:
- A child loves riding a scooter.
- They bring it to a desert play area and want to arrange a little trail of fun.
- The desert wind causes a funny transformation: the scooter gets transformed into
  something impractical and goofy.
- A clever arrangement of shade, water, and a small ramp turns the mess into a
  comedy ending.

The world tracks:
- meters: dust, wobble, shade, water, tidiness
- memes: delight, embarrassment, surprise, pride, cooperation

The story should feel like a complete tiny comedy with a clear turn and resolution.
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
    plural: bool = False
    transformed: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def it(self) -> str:
        return "them" if self.plural else "it"

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the desert edge"
    affords: set[str] = field(default_factory=set)


@dataclass
class Trick:
    id: str
    trigger: str
    effect: str
    comedic: str
    result_label: str
    result_phrase: str


@dataclass
class StoryParams:
    place: str
    trick: str
    name: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "dunes": Setting(place="the dunes", affords={"arrange", "ride"}),
    "camp": Setting(place="the camp edge", affords={"arrange", "ride"}),
    "oasis": Setting(place="the oasis path", affords={"arrange", "ride"}),
}

TRICKS = {
    "heat": Trick(
        id="heat",
        trigger="the hot sun",
        effect="made the scooter's handlebars stretch into a long, wiggly neck",
        comedic="the scooter looked like it was trying to be a cactus",
        result_label="camel-scooter",
        result_phrase="a silly camel-scooter with a wobbly neck",
    ),
    "sand": Trick(
        id="sand",
        trigger="the drifting sand",
        effect="turned the wheels into round sandwich cookies made of sand",
        comedic="the scooter rolled like a snack with a mission",
        result_label="cookie-scooter",
        result_phrase="a cookie-scooter with crunchy sand wheels",
    ),
    "mirage": Trick(
        id="mirage",
        trigger="a shiny mirage",
        effect="made the scooter seem to wear a tiny top hat",
        comedic="the scooter looked as if it was headed to a tea party",
        result_label="tea-scooter",
        result_phrase="a tea-scooter with a very serious imaginary hat",
    ),
}

TRAITS = ["curious", "playful", "brave", "silly", "cheerful"]


@dataclass
class StoryState:
    actor: Entity
    scooter: Entity
    trick: Trick
    arranged: bool = False
    transformed: bool = False
    resolved: bool = False


def build_story_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    trick = TRICKS[params.trick]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        label=params.name,
        membranes := None,
    ))
    scooter = world.add(Entity(
        id="scooter",
        kind="thing",
        type="scooter",
        label="scooter",
        phrase="a bright red scooter with a silver bell",
        owner=child.id,
        meters={"dust": 0.0, "wobble": 0.0, "tidiness": 0.0, "shade": 0.0, "water": 0.0},
        memes={"delight": 0.0, "surprise": 0.0, "embarrassment": 0.0, "pride": 0.0, "cooperation": 0.0},
    ))
    world.facts["child"] = child
    world.facts["scooter"] = scooter
    world.facts["trick"] = trick
    return world


def do_arrange(world: World, state: StoryState) -> None:
    actor = state.actor
    scooter = state.scooter
    actor.memes["cooperation"] = actor.memes.get("cooperation", 0.0) + 1
    scooter.meters["shade"] = scooter.meters.get("shade", 0.0) + 1
    scooter.meters["tidiness"] = scooter.meters.get("tidiness", 0.0) + 1
    state.arranged = True
    world.say(
        f"{actor.id} began to arrange a tiny track beside {world.setting.place}, "
        f"lining up two flat stones and a scrap of cloth like a very serious stage."
    )
    world.say(
        f"The plan was to keep the scooter neat, because even a scooter can look "
        f"important when it has its own little parking spot."
    )


def do_transformation(world: World, state: StoryState) -> None:
    trick = state.trick
    scooter = state.scooter
    if scooter.meters.get("shade", 0.0) < THRESHOLD:
        scooter.meters["dust"] += 1
    scooter.transformed = True
    state.transformed = True
    scooter.memes["surprise"] = scooter.memes.get("surprise", 0.0) + 1
    scooter.meters["wobble"] += 1
    world.say(
        f"Then {trick.trigger} came along and {trick.effect}."
    )
    world.say(
        f"{trick.comedic.capitalize()}, and {scooter.label} turned into {trick.result_phrase}."
    )


def do_tension(world: World, state: StoryState) -> None:
    scooter = state.scooter
    actor = state.actor
    if scooter.transformed:
        scooter.memes["embarrassment"] += 1
        actor.memes["surprise"] += 1
        world.say(
            f"{actor.id} blinked twice, then laughed so hard that the desert seemed "
            f"to wiggle with them."
        )
        world.say(
            f"It was hard to be upset when the scooter had become something that looked "
            f"ready to serve tea to a cactus."
        )


def do_resolution(world: World, state: StoryState) -> None:
    actor = state.actor
    scooter = state.scooter
    trick = state.trick
    scooter.meters["water"] = scooter.meters.get("water", 0.0) + 1
    scooter.meters["shade"] = scooter.meters.get("shade", 0.0) + 1
    scooter.meters["wobble"] = max(0.0, scooter.meters.get("wobble", 0.0) - 0.5)
    scooter.meters["dust"] = max(0.0, scooter.meters.get("dust", 0.0) - 0.5)
    scooter.memes["pride"] = scooter.memes.get("pride", 0.0) + 1
    actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
    state.resolved = True
    world.say(
        f"So {actor.id} arranged a better answer: a little shade, a splash of water, "
        f"and a gentle push down the stone track."
    )
    world.say(
        f"That made the {trick.result_label} scoot in a straighter line, which was not "
        f"quite normal but was much funnier."
    )
    world.say(
        f"By the end, the scooter was still strange, the desert was still bright, and "
        f"{actor.id} was grinning at their own tiny parade."
    )


def tell(place: str, trick_id: str, name: str, trait: str) -> World:
    world = build_story_world(StoryParams(place=place, trick=trick_id, name=name, trait=trait))
    actor = world.get(name)
    scooter = world.get("scooter")
    trick = world.facts["trick"]
    state = StoryState(actor=actor, scooter=scooter, trick=trick)

    world.say(
        f"{actor.id} was a {trait} child who loved a shiny scooter and loved arranging "
        f"little things into neat lines."
    )
    world.say(
        f"On a day at {world.setting.place}, {actor.id} brought the scooter out to play "
        f"and began to arrange a trail in the sand."
    )
    world.para()
    do_arrange(world, state)
    do_transformation(world, state)
    world.para()
    do_tension(world, state)
    do_resolution(world, state)

    world.facts.update(
        actor=actor,
        scooter=scooter,
        trick=trick,
        place=place,
        state=state,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    actor = f["actor"]
    trick = f["trick"]
    return [
        f'Write a short comedy story for a young child about {actor.id}, a scooter, and the desert.',
        f'Tell a funny story where a child tries to arrange a play area, but a {trick.trigger} transforms the scooter.',
        f'Write a gentle desert story with a silly transformation and an ending where the child laughs and fixes the setup.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    actor = f["actor"]
    scooter = f["scooter"]
    trick = f["trick"]
    qa = [
        QAItem(
            question=f"What did {actor.id} bring to the desert to play with?",
            answer=f"{actor.id} brought a bright red scooter with a silver bell.",
        ),
        QAItem(
            question=f"What did {actor.id} try to do before the funny transformation?",
            answer=f"{actor.id} tried to arrange a tiny track and keep the scooter neat.",
        ),
        QAItem(
            question=f"What changed the scooter into something silly?",
            answer=f"{trick.trigger} caused the scooter to transform into {trick.result_phrase}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"{actor.id} arranged shade and water, and then laughed at the scooter's "
                f"very odd new look while it rolled more neatly."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scooter?",
            answer="A scooter is a small ride-on vehicle with wheels and a handlebar that a child can push or ride.",
        ),
        QAItem(
            question="What is a desert?",
            answer="A desert is a very dry place with lots of sand, strong sun, and not much water.",
        ),
        QAItem(
            question="What does arrange mean?",
            answer="To arrange something means to put the pieces in an order or a neat setup.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change where something becomes different from what it was before.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}}")
        if e.memes:
            parts.append(f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}")
        if e.transformed:
            parts.append("transformed=True")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: scooter, desert, arrange, transformation.")
    ap.add_argument("--place", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--trick", choices=sorted(TRICKS), default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--trait", choices=["curious", "playful", "brave", "silly", "cheerful"], default=None)
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
    place = args.place or rng.choice(sorted(SETTINGS))
    trick = args.trick or rng.choice(sorted(TRICKS))
    name = args.name or rng.choice(["Mina", "Owen", "Pia", "Noah", "Luna"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, trick=trick, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.trick, params.name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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


ASP_RULES = r"""
% A scooter can transform in a desert story when a trigger is present.
transform(S) :- scooter(S), in_desert(S), trigger(T), causes(T, S).

% A story is valid when it includes a scooter, a desert setting, arrange, and a transformation.
valid_story(P) :- place(P), desert(P), action(arrange), feature(transformation), scooter_story.
"""

SETTINGS_REGISTRY = {
    "dunes": {"desert": True},
    "camp": {"desert": True},
    "oasis": {"desert": True},
}

def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        if s.get("desert"):
            lines.append(asp.fact("desert", pid))
    lines.append(asp.fact("action", "arrange"))
    lines.append(asp.fact("feature", "transformation"))
    lines.append(asp.fact("scooter_story"))
    for t in TRICKS.values():
        lines.append(asp.fact("trigger", t.id))
        lines.append(asp.fact("causes", t.id, "scooter"))
    lines.append(asp.fact("scooter", "scooter"))
    lines.append(asp.fact("in_desert", "scooter"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in SETTINGS for t in TRICKS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Simple parity check: the ASP program should at least produce a non-empty model.
    import asp
    model = asp.one_model(asp_program("#show transform/1."))
    if model is None:
        print("MISMATCH: ASP returned no model.")
        return 1
    print("OK: ASP program grounded and solved.")
    return 0


CURATED = [
    StoryParams(place="dunes", trick="heat", name="Mina", trait="curious"),
    StoryParams(place="camp", trick="sand", name="Owen", trait="playful"),
    StoryParams(place="oasis", trick="mirage", name="Luna", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
