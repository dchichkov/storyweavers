#!/usr/bin/env python3
"""
storyworlds/worlds/arrange_flashback_transformation_dialogue_adventure.py
=========================================================================

A small adventure storyworld about a child who must arrange a few items for a
journey, remembers an earlier mistake, and transforms the plan through dialogue.

The seed premise:
- A child is getting ready for a small adventure.
- Something must be arranged correctly before leaving.
- A flashback reminds the child why care matters.
- A transformation happens through a helpful conversation.
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


@dataclass
class StoryParams:
    place: str
    goal: str
    object_name: str
    helper: str
    obstacle: str
    memory: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried: bool = False
    arranged: bool = False
    transformed: bool = False


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.arranged:
                bits.append("arranged=True")
            if e.transformed:
                bits.append("transformed=True")
            if e.carried:
                bits.append("carried=True")
            lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
        return "\n".join(lines)


SETTINGS = {
    "forest": "the forest path",
    "harbor": "the little harbor",
    "hill": "the windy hill",
    "cave": "the bright cave",
    "river": "the riverbank",
}

GOALS = {
    "forest": "follow the trail to the old oak",
    "harbor": "reach the map stone by the water",
    "hill": "climb to the lookout rock",
    "cave": "find the glowing shell in the cave",
    "river": "cross the bridge and reach the meadow",
}

OBJECTS = {
    "compass": ("a small brass compass", "compass"),
    "map": ("a folded map", "map"),
    "lantern": ("a round lantern", "lantern"),
    "rope": ("a coil of rope", "rope"),
    "snack": ("a wrapped snack", "snack"),
}

HELPERS = ["grandpa", "mom", "dad", "older sister", "kind ranger"]
OBSTACLES = {
    "wind": "the wind kept blowing the papers apart",
    "darkness": "the path was too dark to see clearly",
    "mud": "the muddy ground made every step slippery",
    "rain": "the rain made the trail hard to trust",
    "distance": "the goal felt far away and tiring",
}
MEMORIES = {
    "lost_map": "the time the child had rushed out and lost a map in the grass",
    "scattered_snack": "the day a bag of snacks had fallen open and rolled away",
    "broken_light": "the evening a lantern had tipped over because nothing was arranged well",
    "wrong_turn": "the afternoon the child had chosen the wrong turn and felt lost",
}


ASP_RULES = r"""
place(P) :- setting(P).
goal(G) :- seeking(G).
item(I) :- object(I).
help(H) :- helper(H).

needs_arrange(P, I) :- setting(P), object(I), obstacle(O), affects(O, I).
can_fix(I) :- object(I).

ready(P, I) :- needs_arrange(P, I), can_fix(I).
story_ok(P, G, I) :- place(P), goal(G), item(I), ready(P, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, place in SETTINGS.items():
        lines.append(asp.fact("setting", key))
        lines.append(asp.fact("path", key, place))
    for key, goal in GOALS.items():
        lines.append(asp.fact("seeking", key))
        lines.append(asp.fact("goal_text", key, goal))
    for key, (phrase, short) in OBJECTS.items():
        lines.append(asp.fact("object", key))
        lines.append(asp.fact("object_phrase", key, phrase))
        lines.append(asp.fact("object_short", key, short))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for k in OBSTACLES:
        lines.append(asp.fact("obstacle", k))
    lines.append(asp.fact("affects", "wind", "map"))
    lines.append(asp.fact("affects", "wind", "compass"))
    lines.append(asp.fact("affects", "darkness", "lantern"))
    lines.append(asp.fact("affects", "mud", "rope"))
    lines.append(asp.fact("affects", "rain", "map"))
    lines.append(asp.fact("affects", "rain", "snack"))
    lines.append(asp.fact("affects", "distance", "snack"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.goal not in GOALS:
        raise StoryError(f"Unknown goal: {params.goal}")
    if params.object_name not in OBJECTS:
        raise StoryError(f"Unknown object: {params.object_name}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"Unknown obstacle: {params.obstacle}")
    if params.memory not in MEMORIES:
        raise StoryError(f"Unknown memory: {params.memory}")


def generate_story(world: World) -> None:
    p = world.params
    place = SETTINGS[p.place]
    goal = GOALS[p.goal]
    obj_phrase, obj_short = OBJECTS[p.object_name]
    obstacle = OBSTACLES[p.obstacle]
    memory = MEMORIES[p.memory]

    hero = world.add(Entity(id="hero", kind="character", label="the child"))
    helper = world.add(Entity(id="helper", kind="character", label=p.helper))
    obj = world.add(Entity(id="object", kind="thing", label=obj_short, phrase=obj_phrase))

    world.say(f"One morning, the child stood at {place} with a plan to {goal}.")
    world.say(f"{p.helper.capitalize()} helped by pointing at {obj_phrase} and saying, \"Let's arrange it before we go.\"")
    obj.arranged = True
    hero.memes["hope"] = 1.0
    helper.memes["calm"] = 1.0

    world.para()
    world.say(f"Then the child looked at the trail and frowned, because {obstacle}.")
    world.say(f"That worry brought back a flashback: {memory}.")
    hero.memes["worry"] = 1.0
    hero.memes["memory"] = 1.0

    world.para()
    world.say(f'"If we arrange the {obj_short} first, will the trip be safer?" the child asked.')
    world.say(f'"Yes," said {p.helper}, "and if we check it now, we can keep moving with a braver step."')
    world.say(f"The child listened, took a deep breath, and arranged the {obj_short} more carefully.")
    obj.arranged = True
    obj.transformed = True
    hero.memes["worry"] = 0.0
    hero.memes["brave"] = 1.0
    world.facts.update(
        place=p.place,
        goal=p.goal,
        object_name=p.object_name,
        helper=p.helper,
        obstacle=p.obstacle,
        memory=p.memory,
        arranged=True,
        transformed=True,
    )

    world.para()
    world.say(f"This time, the {obj_short} was ready, the child felt braver, and the two of them went on.")
    world.say(f"With the plan arranged, the little adventure could begin, and the path no longer felt so large.")


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a short adventure story about a child who must arrange a {p.object_name} before leaving {SETTINGS[p.place]}.",
        f"Tell a child-friendly story with a flashback, a helpful dialogue, and a small transformation in how the child feels.",
        f"Write a gentle adventure story where {p.helper} helps a child arrange something carefully so the journey can continue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    obj_phrase, obj_short = OBJECTS[p.object_name]
    place = SETTINGS[p.place]
    goal = GOALS[p.goal]
    obstacle = OBSTACLES[p.obstacle]
    memory = MEMORIES[p.memory]
    return [
        QAItem(
            question=f"Where did the child want to go in the story?",
            answer=f"The child wanted to go to {place} and {goal}.",
        ),
        QAItem(
            question=f"What did the helper ask the child to do first?",
            answer=f"{p.helper.capitalize()} asked the child to arrange {obj_phrase} before going on.",
        ),
        QAItem(
            question=f"What did the child remember in the flashback?",
            answer=f"The child remembered that {memory}.",
        ),
        QAItem(
            question=f"Why did the child need to pause and think?",
            answer=f"The child needed to pause because {obstacle}.",
        ),
        QAItem(
            question=f"What changed after the dialogue with {p.helper}?",
            answer=f"After the dialogue, the child felt braver and the {obj_short} was arranged carefully for the trip.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    p = world.params
    obj_phrase, obj_short = OBJECTS[p.object_name]
    out = [
        QAItem(
            question="What does it mean to arrange something?",
            answer="To arrange something means to put it in the right order or place so it is ready to use.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when a story remembers something that happened earlier.",
        ),
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters talk to each other using spoken words.",
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer="A transformation is a change, like when a plan becomes safer or a character becomes braver.",
        ),
        QAItem(
            question=f"Why might {obj_phrase} matter on an adventure?",
            answer=f"{obj_phrase.capitalize()} can help a child stay ready, careful, and prepared on the way.",
        ),
    ]
    return out


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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/3."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    # A simple parity check: every registered place/goal/object combo with a fix
    # should appear in the ASP model.
    import asp
    program = asp_program("#show story_ok/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "story_ok"))
    py_set = set()
    for place in SETTINGS:
        for goal in GOALS:
            for obj in OBJECTS:
                if (place == "forest" and obj in {"map", "compass"}) or \
                   (place == "harbor" and obj in {"map", "lantern"}) or \
                   (place == "hill" and obj in {"rope", "snack"}) or \
                   (place == "cave" and obj in {"lantern", "rope"}) or \
                   (place == "river" and obj in {"map", "snack"}):
                    py_set.add((place, goal, obj))
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure world with arrange, flashback, transformation, and dialogue.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--goal", choices=sorted(GOALS))
    ap.add_argument("--object", dest="object_name", choices=sorted(OBJECTS))
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--obstacle", choices=sorted(OBSTACLES))
    ap.add_argument("--memory", choices=sorted(MEMORIES))
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
    place = args.place or rng.choice(sorted(SETTINGS))
    goal = args.goal or rng.choice(sorted(GOALS))
    object_name = args.object_name or rng.choice(sorted(OBJECTS))
    helper = args.helper or rng.choice(HELPERS)
    obstacle = args.obstacle or rng.choice(sorted(OBSTACLES))
    memory = args.memory or rng.choice(sorted(MEMORIES))
    return StoryParams(place=place, goal=goal, object_name=object_name, helper=helper, obstacle=obstacle, memory=memory)


def generate(params: StoryParams) -> StorySample:
    _reasonableness_gate(params)
    world = World(params)
    generate_story(world)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="forest", goal="forest", object_name="compass", helper="grandpa", obstacle="wind", memory="lost_map"),
    StoryParams(place="cave", goal="cave", object_name="lantern", helper="kind ranger", obstacle="darkness", memory="broken_light"),
    StoryParams(place="river", goal="river", object_name="map", helper="mom", obstacle="rain", memory="wrong_turn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story triples:")
        for t in stories:
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
