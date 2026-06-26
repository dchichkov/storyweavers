#!/usr/bin/env python3
"""
Storyworld: grow_fallen_tree_trail_curiosity_teamwork_myth
===========================================================

A small mythic story world about a fallen tree trail, where curiosity and
teamwork help a little community make something new grow from what was broken.

Premise:
- A path is blocked by a fallen tree on a trail.
- Curious children and helpers want to see what lies beyond it.
- They cannot simply push the tree away; instead they learn to work together.

Tension:
- The trail is blocked, and the old tree is heavy.
- Curiosity pulls the characters forward, but the path is still unusable.

Turn:
- The helpers notice roots, soil, moss, seeds, and sunlight.
- With teamwork, they guide living things to grow around and over the fallen trunk.

Resolution:
- A green archway, vines, mushrooms, and small saplings transform the obstacle
  into a legendary walkway.
- The trail opens, and the ending image proves the change.

This world models physical meters and emotional memes, emits ASP facts/rules, and
supports the standard Storyworld CLI.
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
# Domain registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "fallen_tree_trail": {
        "label": "the fallen tree trail",
        "place": "fallen tree trail",
        "hazards": {"blocked_path", "silence"},
        "gifts": {"moss", "roots", "seeds", "sunlight"},
    }
}

FEATURES = {
    "Curiosity": {"tag": "curiosity", "color": "bright-eyed"},
    "Teamwork": {"tag": "teamwork", "color": "many-handed"},
}

STYLES = {
    "Myth": {"voice": "mythic"},
}

GENDERS = ["girl", "boy"]
NAMES = ["Ari", "Mina", "Taro", "Lena", "Oren", "Ivy", "Niko", "Sana"]
GROWN_THINGS = [
    "a new green arch of vines",
    "a ring of saplings",
    "a lantern of moss",
    "a path of roots and flowers",
    "a small bridge of living branches",
]
HELPERS = ["the wind", "the rain", "the bees", "the mushrooms", "the ants"]


@dataclass
class StoryParams:
    place: str = "fallen_tree_trail"
    style: str = "Myth"
    seed_word: str = "grow"
    name: str = "Ari"
    gender: str = "girl"
    helper: str = "the wind"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: dict
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# World mechanics
# ---------------------------------------------------------------------------

def myth_voice(name: str) -> str:
    return f"long ago, when the trail still remembered old feet, {name}"


def opening_image(world: World, child: Entity) -> None:
    world.say(
        f"{myth_voice(child.id)} came to the fallen tree trail, where a great trunk lay across the path like a sleeping giant."
    )
    world.say(
        f"The air was hushed, but {child.pronoun().capitalize()} kept looking past the bark, because curiosity made the blocked road feel like a riddle."
    )


def obstacle(world: World) -> None:
    world.facts["blocked"] = True
    world.say(
        "No one could pass easily, and even the moss seemed to wait and watch."
    )


def call_team(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.memes["hope"] = child.memes.get("hope", 0) + 1
    world.say(
        f"{child.id} wondered what lived beyond the fallen giant, and {child.pronoun('possessive')} heart urged a question into the trees."
    )
    world.say(
        f"Then {child.id} called for {helper.label}, and soon the trail answered with teamwork."
    )
    world.facts["teamwork_started"] = True


def grow_solution(world: World, child: Entity, helper: Entity) -> str:
    grown = random.choice(GROWN_THINGS)
    world.facts["grown"] = grown
    world.facts["helper"] = helper.label
    world.say(
        f"Together they gathered seeds, lifted wet roots, and asked the earth to {world.facts['seed_word']}."
    )
    world.say(
        f"{helper.label.capitalize()} carried pollen and rain, while {child.id} made careful little gaps for light."
    )
    return grown


def transform(world: World, grown: str) -> None:
    world.facts["open"] = True
    world.say(
        f"By dawn, {grown} had begun to rise around the fallen trunk, and the old obstacle looked less like a wall and more like a doorway."
    )
    world.say(
        "Moss softened the bark, mushrooms ringed the roots, and tiny leaves flickered where there had been only silence."
    )


def ending(world: World, child: Entity) -> None:
    world.say(
        f"In the end, {child.id} walked the trail again, and the path was no longer blocked."
    )
    world.say(
        f"{child.pronoun().capitalize()} smiled at the living arch above the fallen tree, because curiosity had found its answer and teamwork had helped it grow."
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.style not in STYLES:
        raise StoryError("Unknown style.")
    if params.gender not in GENDERS:
        raise StoryError("Unknown gender.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")

    setting = SETTINGS[params.place]
    world = World(setting=setting)
    world.facts["seed_word"] = params.seed_word

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"footsteps": 0.0},
        memes={"curiosity": 1.0, "hope": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=params.helper,
    ))

    world.facts.update(child=child, helper_entity=helper, setting=setting, params=params)
    opening_image(world, child)
    world.para()
    obstacle(world)
    call_team(world, child, helper)
    world.para()
    grown = grow_solution(world, child, helper)
    transform(world, grown)
    world.para()
    ending(world, child)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short myth for children about the "{p.place}" where curiosity and teamwork help something grow.',
        f"Tell a gentle legend about {p.name} on {world.setting['label']} who asks what lies beyond a fallen tree.",
        f'Compose a simple story that uses the word "{p.seed_word}" and ends with a green path opening on the trail.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper_entity"]
    grown = world.facts["grown"]
    return [
        QAItem(
            question=f"Who came to the fallen tree trail?",
            answer=f"{p.name} came to the fallen tree trail, full of curiosity and ready to learn what the blocked path was hiding.",
        ),
        QAItem(
            question=f"What blocked the trail?",
            answer="A great fallen tree blocked the trail, like a giant sleeping across the path.",
        ),
        QAItem(
            question=f"Who helped {p.name} make the path change?",
            answer=f"{helper.label.capitalize()} helped {p.name}, and together they used teamwork to grow {grown}.",
        ),
        QAItem(
            question=f"How did the story end for {p.name}?",
            answer=f"{p.name} walked the trail again and smiled at the living arch, because the path was open at last.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and find out what is hidden.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when two or more helpers work together to do something that is hard alone.",
        ),
        QAItem(
            question="What does it mean when plants grow?",
            answer="When plants grow, they become bigger and stronger over time as they drink water, catch sunlight, and send out roots or leaves.",
        ),
        QAItem(
            question="Why can a fallen tree become part of a forest path?",
            answer="A fallen tree can become part of a forest path when moss, roots, and new plants grow around it and turn it into something useful or beautiful.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A trail is blocked when a fallen tree lies across it.
blocked(T) :- trail(T), fallen_tree(T), across_path(T).

% Curiosity asks for a question about what lies beyond a block.
wants_to_know(C) :- curious(C), blocked(trail).

% Teamwork can turn a block into a growing place.
can_grow_solution(T) :- blocked(T), teamwork(T), seeds(T), sunlight(T), roots(T).

% The ending is successful when something living grows around the obstacle.
open_trail(T) :- can_grow_solution(T), growing_arch(T).

#show blocked/1.
#show wants_to_know/1.
#show can_grow_solution/1.
#show open_trail/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("trail", "trail"),
        asp.fact("fallen_tree", "trail"),
        asp.fact("across_path", "trail"),
        asp.fact("curious", "child"),
        asp.fact("teamwork", "trail"),
        asp.fact("seeds", "trail"),
        asp.fact("sunlight", "trail"),
        asp.fact("roots", "trail"),
        asp.fact("growing_arch", "trail"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show blocked/1. #show wants_to_know/1. #show can_grow_solution/1. #show open_trail/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    want = {("blocked", ("trail",)), ("wants_to_know", ("child",)), ("can_grow_solution", ("trail",)), ("open_trail", ("trail",))}
    if atoms == want:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(want))
    return 1


# ---------------------------------------------------------------------------
# Serialization / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world on a fallen tree trail.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="fallen_tree_trail")
    ap.add_argument("--style", choices=STYLES.keys(), default="Myth")
    ap.add_argument("--seed-word", default="grow")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPERS)
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
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(GENDERS)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        place=args.place,
        style=args.style,
        seed_word=args.seed_word,
        name=name,
        gender=gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.seed is not None:
        random.seed(params.seed)
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting['label']}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {', '.join(bits)}")
    lines.append(f"facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show blocked/1. #show wants_to_know/1. #show can_grow_solution/1. #show open_trail/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        cur = [
            StoryParams(name="Ari", gender="girl", helper="the wind"),
            StoryParams(name="Mina", gender="girl", helper="the bees"),
            StoryParams(name="Taro", gender="boy", helper="the rain"),
        ]
        samples = [generate(p) for p in cur]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name} on {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
