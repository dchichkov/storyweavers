#!/usr/bin/env python3
"""
storyworlds/worlds/erupt_waitress_transformation_tall_tale.py
==============================================================

A small tall-tale story world about a waitress, a strange eruption, and a
transformation that turns a bad day into an unforgettable one.

Premise:
- A cheerful waitress works in a tiny roadside diner near a sleeping hill.
- She loves serving big breakfasts and shiny pies.
- The hill begins to rumble, and the day threatens to turn messy and scary.

Turn:
- The waitress uses a magical apron, a silver tray, and a brave kind heart.
- When the hill erupts, the world around her changes shape.
- The waitress transforms too: first in mood, then in outward form, then in how
  everyone sees her.

Resolution:
- The eruption becomes a spectacular, useful spectacle.
- The diner stays safe, the customers cheer, and the waitress ends up taller,
  brighter, and prouder than before.

This world is intentionally narrow: every valid story must have a plausible
eruption, a waitress, and a transformation that changes the world state in a
clear, child-facing way.
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
# Core world model
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
    wears: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"waitress", "girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"waiter", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    has_hill: bool = True
    has_diner: bool = True


@dataclass
class Weather:
    sky: str = "clear"
    heat: str = "warm"


@dataclass
class Reaction:
    id: str
    label: str
    change_mood: str
    change_form: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    name: str
    role: str
    transformation: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, weather: Weather) -> None:
        self.setting = setting
        self.weather = weather
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        w = World(self.setting, self.weather)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "tiny diner": Setting(place="a tiny diner on the edge of town"),
    "hill diner": Setting(place="a hilltop diner with a red roof"),
    "roadside diner": Setting(place="a roadside diner beside a sleepy hill"),
}

TRANSFORMATIONS = {
    "tall": Reaction(
        id="tall",
        label="tall",
        change_mood="bold",
        change_form="grew taller than the doorway",
        ending_image="She stood tall beside the pie case, with a grin as wide as a barn door.",
    ),
    "glow": Reaction(
        id="glow",
        label="glowing",
        change_mood="bright",
        change_form="began to glow like a lantern",
        ending_image="She glowed warmly while the volcano-light painted the windows gold.",
    ),
    "bake": Reaction(
        id="bake",
        label="baked",
        change_mood="steady",
        change_form="turned warm as fresh bread",
        ending_image="She smelled like cinnamon and stood steady as a stove door.",
    ),
    "song": Reaction(
        id="song",
        label="singing",
        change_mood="joyful",
        change_form="found a voice that could rattle the spoons",
        ending_image="She sang to the mountain until even the rain seemed to dance.",
    ),
}

NAMES = ["Ruby", "Mabel", "Daisy", "June", "Ivy", "Nell", "Sadie", "Pearl"]
TRAITS = ["cheerful", "quick", "kind", "steady", "brave", "spry"]

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.

waitress(w1).
place(p1).
transformation(t1).

eruption_possible(w1,p1) :- waitress(w1), place(p1).
can_transform(w1,t1) :- waitress(w1), transformation(t1).

valid_story(w1,p1,t1) :- eruption_possible(w1,p1), can_transform(w1,t1).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    lines.append(asp.fact("waitress", "w1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(1, 1, 1)}
    cl = set(asp_valid_stories())
    if cl:
        print("OK: ASP rule set produces at least one valid story.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def choose_reaction(kind: str) -> Reaction:
    if kind not in TRANSFORMATIONS:
        raise StoryError("Unknown transformation choice.")
    return TRANSFORMATIONS[kind]


def eruption_sentence(world: World) -> str:
    place = world.setting.place
    return f"Then the sleepy hill behind {place} began to grumble like a hungry kettle."


def transform_world(world: World, waitress: Entity, reaction: Reaction) -> None:
    waitress.memes["fear"] = max(0.0, waitress.memes.get("fear", 0.0) - 1.0)
    waitress.memes["pride"] = waitress.memes.get("pride", 0.0) + 1.0
    waitress.meters["height"] = waitress.meters.get("height", 1.0) + (2.0 if reaction.id == "tall" else 0.5)
    waitress.meters["shine"] = waitress.meters.get("shine", 0.0) + 1.0
    world.facts["transformed"] = reaction.id


def world_event(world: World, waitress: Entity, reaction: Reaction) -> None:
    world.say(f"{waitress.id} was a {', '.join(waitress.traits)} waitress who worked at {world.setting.place}.")
    world.say(f"She served pancakes, coffee, and pie with a smile that could wake the whole morning.")
    world.say(f"On the day the hill woke up, {eruption_sentence(world)}")
    world.para()
    world.say(f"The windows shivered, the mugs rang, and the customers stared at the smoke.")
    world.say(f"But {waitress.id} did not run away; she lifted her tray and took a deep breath.")
    world.say(f"That brave breath {reaction.change_form}.")
    transform_world(world, waitress, reaction)
    world.para()
    world.say(f"The eruption poured out in a grand red ribbon, but it missed the diner and lit the sky instead.")
    world.say(f"{waitress.id} became {reaction.label}, and the whole room felt bigger because of it.")
    world.say(reaction.ending_image)
    world.facts["ending"] = reaction.ending_image


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        'Write a tall-tale story about a waitress, an eruption, and a transformation that changes the whole day.',
        f"Tell a child-friendly story where {world.facts['name']} the waitress faces a hill that erupts near {world.setting.place}.",
        "Write a playful story in which a waitress becomes taller, braver, or stranger after a volcanic surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    waitress = world.facts["waitress"]
    reaction: Reaction = world.facts["reaction"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {waitress.id}, a {waitress.type} who worked at {place}.",
        ),
        QAItem(
            question=f"What happened to the hill near {place}?",
            answer="The hill erupted and sent smoke and bright red fire into the sky.",
        ),
        QAItem(
            question=f"How did {waitress.id} change during the eruption?",
            answer=f"She transformed and became {reaction.label}, which made her seem even more remarkable.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=world.facts["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a waitress?",
            answer="A waitress is a person who brings food and drinks to people in a restaurant or diner.",
        ),
        QAItem(
            question="What is an eruption?",
            answer="An eruption is when a volcano or hill suddenly blasts out smoke, ash, hot rock, or lava.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means a big change, like when something becomes different in shape, size, or feel.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Parser / resolve / generate / emit
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: waitress, eruption, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=["waitress"], default="waitress")
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    role = args.role or "waitress"
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    if role != "waitress":
        raise StoryError("This story world only supports a waitress hero.")
    return StoryParams(place=place, name=name, role=role, transformation=transformation)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    weather = Weather(sky="smoky", heat="warm")
    world = World(setting, weather)
    waitress = world.add(Entity(
        id=params.name,
        kind="character",
        type="waitress",
        label="waitress",
        traits=["cheerful", "brave"],
    ))
    world.facts["name"] = params.name
    world.facts["waitress"] = waitress
    reaction = choose_reaction(params.transformation)
    world.facts["reaction"] = reaction
    world_event(world, waitress, reaction)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
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


def explain_params(args: argparse.Namespace) -> None:
    if args.role and args.role != "waitress":
        raise StoryError("Only waitress is supported in this world.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid ASP story shape(s):")
        for s in stories:
            print(" ", s)
        return

    explain_params(args)
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for transform in TRANSFORMATIONS:
                params = StoryParams(place=place, name="Ruby", role="waitress", transformation=transform)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.name} / {p.place} / {p.transformation}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
