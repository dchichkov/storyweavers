#!/usr/bin/env python3
"""
storyworlds/worlds/cut_gerund_twist_dialogue_animal_story.py
============================================================

A small animal-story world with a cut-gerund premise, a dialogue beat, and a
twist ending.

Seed tale:
---
A little beaver loved cutting reeds near the pond. One day, she found a long
green stem blocking the path to her stash. She grabbed her snips and started to
cut it, but the stem moved and a tiny duckling's voice called out from inside.
It was not a stem at all. It was a rope tied around a basket, and the basket had
fallen into the reeds.

The beaver and her friend untied the rope together, and the duckling wiggled
free. The beaver still got to cut the reeds, but only the empty ones, and she
used the reeds to patch the basket instead.

World model:
- Physical meters: snip_progress, tangle, wetness, repair
- Emotional memes: worry, relief, pride, curiosity, trust
- Dialogue and twist are driven by world state, not by fixed text swaps.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {"snip_progress": 0.0, "tangle": 0.0, "wetness": 0.0, "repair": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"worry": 0.0, "relief": 0.0, "pride": 0.0, "curiosity": 0.0, "trust": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        female = {"she", "girl", "mother", "sister"}
        male = {"he", "boy", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    safe_for: set[str]
    sharpness: float
    helps: set[str]


@dataclass
class StoryParams:
    place: str
    protagonist: str
    friend: str
    object: str
    tool: str
    twist: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "pond": Setting("the pond", {"reeds", "water", "basket"}),
    "bank": Setting("the river bank", {"reeds", "water", "basket"}),
    "marsh": Setting("the marsh", {"reeds", "water", "basket"}),
}

TOOLS = {
    "snips": Tool("snips", "little snips", "tool", {"reeds", "cord"}, 1.0, {"cut"}),
    "scissors": Tool("scissors", "small scissors", "tool", {"reeds", "cord"}, 1.2, {"cut"}),
    "beak": Tool("beak", "a sharp beak", "body", {"soft reeds"}, 0.7, {"peck"}),
}

ANIMALS = {
    "beaver": ("beaver", "beaver"),
    "rabbit": ("rabbit", "rabbit"),
    "duck": ("duck", "duck"),
    "fox": ("fox", "fox"),
    "mouse": ("mouse", "mouse"),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for protagonist in ANIMALS:
            for friend in ANIMALS:
                if friend == protagonist:
                    continue
                for obj in ("reeds", "cord", "basket"):
                    for tool in TOOLS:
                        if tool == "beak" and protagonist != "duck":
                            continue
                        if obj == "basket" and tool == "beak":
                            continue
                        out.append((place, protagonist, friend, obj, tool))
    return out


@dataclass
class Scene:
    target: Entity
    friend: Entity
    object: Entity
    tool: Entity
    twist_is_inside: bool = False
    rescued: bool = False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with cut-gerund, dialogue, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--protagonist", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--object", choices=["reeds", "cord", "basket"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--twist", choices=["duckling", "kit", "nestling"])
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
    choices = valid_combos()
    filtered = []
    for c in choices:
        place, protagonist, friend, obj, tool = c
        if args.place and place != args.place:
            continue
        if args.protagonist and protagonist != args.protagonist:
            continue
        if args.friend and friend != args.friend:
            continue
        if args.object and obj != args.object:
            continue
        if args.tool and tool != args.tool:
            continue
        filtered.append(c)
    if not filtered:
        raise StoryError("No valid animal story matches those choices.")
    place, protagonist, friend, obj, tool = rng.choice(filtered)
    twist = args.twist or rng.choice(["duckling", "kit", "nestling"])
    return StoryParams(place, protagonist, friend, obj, tool, twist)


def _setup_world(params: StoryParams) -> tuple[World, Scene]:
    world = World(SETTINGS[params.place])
    protagonist = world.add(Entity(params.protagonist, kind="character", type=params.protagonist, label=params.protagonist))
    friend = world.add(Entity(params.friend, kind="character", type=params.friend, label=params.friend))
    obj = world.add(Entity(params.object, type=params.object, label=params.object))
    tool = world.add(Entity(params.tool, type="tool", label=TOOLS[params.tool].label))
    scene = Scene(protagonist, friend, obj, tool)
    world.facts.update(params=params, protagonist=protagonist, friend=friend, obj=obj, tool=tool, scene=scene)
    return world, scene


def _introduce(world: World, s: Scene) -> None:
    world.say(f"A little {s.target.label} loved {s.tool.label} near {world.setting.place}.")
    world.say(f"{s.target.label.capitalize()} liked the neat feeling of cut reeds and tidy paths.")


def _do_cut(world: World, s: Scene) -> None:
    s.target.memes["curiosity"] += 1
    s.target.meters["snip_progress"] += 1
    world.say(f"One day, {s.target.label} saw a long green stem blocking the way.")
    world.say(f'"I can fix this," {s.target.label} said, and {s.target.pronoun().capitalize()} began {s.tool.label}ing.')
    if s.object.id == "basket":
        s.object.meters["tangle"] += 1
        s.target.memes["worry"] += 1
        world.say(f"The stem did not split the way {s.target.label} expected. It tugged back like a knot.")
        world.say(f'"Wait!" called a tiny voice from the reeds. "Please don\'t cut that yet!"')
        s.twist_is_inside = True
    elif s.object.id == "cord":
        s.object.meters["tangle"] += 1
        s.target.memes["worry"] += 1
        world.say(f"The cord gave a small shiver under the snips, and a soft squeak came from nearby.")
        s.twist_is_inside = True
    else:
        world.say(f"The reeds made a soft whisper as they fell into a tidy pile.")
    world.fired.add(("cut", s.object.id))


def _dialogue_and_twist(world: World, s: Scene, twist_word: str) -> None:
    if s.twist_is_inside:
        s.friend.memes["curiosity"] += 1
        world.say(f'"What is it?" asked {s.friend.label}.')
        world.say(f'"It\'s {twist_word}," said a shaky little voice. "I got stuck in the reeds."')
        s.target.memes["worry"] += 1
        s.friend.memes["trust"] += 1
    else:
        world.say(f'"That was quick," said {s.friend.label}, smiling at the neat stack of cut reeds.')


def _help_and_fix(world: World, s: Scene) -> None:
    if s.twist_is_inside:
        s.target.memes["curiosity"] += 1
        s.target.memes["trust"] += 1
        s.friend.meters["repair"] += 1
        s.target.meters["repair"] += 1
        s.object.meters["tangle"] = 0.0
        s.target.memes["worry"] = 0.0
        s.target.memes["relief"] += 1
        world.say(f'"Then we should free it," said {s.target.label}.')
        world.say(f"The two friends loosened the knot together, one careful tug at a time.")
        world.say(f"At last, the tiny {world.facts['params'].twist} popped out and blinked at the sky.")
        s.rescued = True
        world.say(f'"Thank you," said the tiny {world.facts["params"].twist}. "I only wanted my basket back."')
        world.say(f'{s.target.label.capitalize()} laughed and cut only the empty reeds after that, using them to patch the basket.')
        s.target.memes["pride"] += 1
    else:
        s.target.memes["pride"] += 1
        world.say(f"Then {s.target.label} used the cut reeds to make a soft nest, and the path stayed clear.")


def tell(params: StoryParams) -> World:
    world, scene = _setup_world(params)
    _introduce(world, scene)
    world.para()
    _do_cut(world, scene)
    _dialogue_and_twist(world, scene, params.twist)
    world.para()
    _help_and_fix(world, scene)
    world.facts["resolved"] = scene.rescued or scene.object.meters["tangle"] == 0.0
    return world


CURATED = [
    StoryParams("pond", "beaver", "duck", "basket", "snips", "duckling"),
    StoryParams("bank", "rabbit", "fox", "cord", "scissors", "nestling"),
    StoryParams("marsh", "duck", "mouse", "reeds", "beak", "kit"),
]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f'Write a short animal story for young children about a {p.protagonist} who loves {TOOLS[p.tool].label.lower()} near {world.setting.place}.',
        f'Tell a gentle story with dialogue where a {p.protagonist} starts to cut {p.object} but discovers a twist.',
        f'Write an animal story that includes the word "cut" as a gerund idea and ends with a kind rescue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    scene: Scene = world.facts["scene"]
    qa = [
        QAItem(
            question=f"What kind of animal is the main character in the story?",
            answer=f"The main character is a {p.protagonist}, and the friend is a {p.friend}.",
        ),
        QAItem(
            question=f"What was the character trying to cut near {world.setting.place}?",
            answer=f"{p.protagonist.capitalize()} was trying to cut the {p.object}.",
        ),
        QAItem(
            question=f"What changed when the character started cutting?",
            answer=(
                f"The cutting turned into a surprise because a tiny {p.twist} was hidden in the reeds. "
                f"Instead of leaving it tangled, the friends helped it out."
            ),
        ),
    ]
    if scene.rescued:
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with the {p.twist} safe, the basket fixed, and the {p.protagonist} feeling proud.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are reeds?",
            answer="Reeds are tall, thin plants that grow near water and can bend in the wind.",
        ),
        QAItem(
            question="Why should a child be careful with sharp tools?",
            answer="Sharp tools can cut skin or damage things, so they should be used carefully and with help.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprise that changes what you thought was happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid when the protagonist can plausibly cut the object.
can_cut(P, O) :- protagonist(P), object(O), tool(T), helps(T, cut), safe_for(T, O).

% The twist happens when cutting a basket or cord reveals a hidden animal.
twist(P, O) :- can_cut(P, O), hidden_in(O, X), animal(X).

% A valid story needs a setting, a protagonist, a friend, a target object, and a tool.
valid(Place, P, F, O, T) :- place(Place), protagonist(P), friend(F), object(O), tool(T),
                            can_cut(P, O), P != F.
#show valid/5.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ANIMALS:
        lines.append(asp.fact("protagonist", a))
        lines.append(asp.fact("friend", a))
        lines.append(asp.fact("animal", a))
    for o in ("reeds", "cord", "basket"):
        lines.append(asp.fact("object", o))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        for x in sorted(tool.safe_for):
            lines.append(asp.fact("safe_for", t, x))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", t, h))
    lines.append(asp.fact("hidden_in", "basket", "duckling"))
    lines.append(asp.fact("animal", "duckling"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos_python() -> list[tuple[str, str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for p in ANIMALS:
            for f in ANIMALS:
                if p == f:
                    continue
                for o in ("reeds", "cord", "basket"):
                    for t, tool in TOOLS.items():
                        if o not in tool.safe_for:
                            continue
                        if t == "beak" and p != "duck":
                            continue
                        out.append((place, p, f, o, t))
    return out


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos_python())
    if a == b:
        print(f"OK: ASP and Python agree on {len(a)} valid combos.")
        return 0
    print("MISMATCH:")
    print("only in ASP:", sorted(a - b))
    print("only in Python:", sorted(b - a))
    return 1


def build_story(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/5."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
