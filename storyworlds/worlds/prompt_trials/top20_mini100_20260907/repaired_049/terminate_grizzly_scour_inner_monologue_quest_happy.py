#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
)
sys.path.insert(0, STORYWORLDS_ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


def _lazy_asp():
    import asp
    return asp


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    location: str = "the city"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass(frozen=True)
class Scenario:
    opener: str
    threat: str
    wrong_turn: str
    clue: str
    dialogue: str
    action: str
    result: str
    ending: str
    inner_monologue: str


SCENARIOS = [
    Scenario(
        opener="At dusk, the city hummed like a giant battery while Captain Bright watched the rooftops from the clock tower.",
        threat="A grizzly beast had appeared in the museum district, and every tram bell rang with fear.",
        wrong_turn="Captain Bright wanted to terminate the problem with one flashy blast, but the streets below were full of people and parked carts.",
        clue="Then a scratch on the marble steps showed the grizzly was not attacking the museum; it was following spilled honey from the rooftop market.",
        dialogue='Captain Bright whispered, "Can you help me trace it instead of chasing it?" and the museum guard answered, "Yes, but do it carefully."',
        action="He swept the alley with his flashlight, followed the sticky trail, and used a soft net to guide the grizzly away from the market stall.",
        result="The grizzly was safely led into the hill park, where a ranger could care for it and the crowd could breathe again.",
        ending="By moonrise, the city was calm, the market was open, and Captain Bright stood smiling beside a new sign that read: KEEP HONEY OFF THE ROOF.",
        inner_monologue="If I rush, I may hurt someone; if I scour the streets first, I may find the real cause.",
    ),
    Scenario(
        opener="When the sky turned orange, Hero Star clipped onto the bridge cables and listened to the river below.",
        threat="A grizzly shadow had been seen near the power station, and the mayor begged for a quick fix.",
        wrong_turn="Hero Star almost chose to terminate every light on the block to stop the shadow from moving.",
        clue="But a bent fence panel showed paw marks leading away from the station, not toward it.",
        dialogue='Hero Star said, "What if the grizzly only wants to get to the berry truck?" The driver replied, "Then let us open a safer path."',
        action="He lit a bright lane through the plaza, scooped the berries into a crate, and scoured the sidewalk for hidden claws before opening the gate.",
        result="The grizzly followed the berries into the freight yard, where it found food without fear and left the power station untouched.",
        ending="The next morning, the mayor pinned a gold star on Hero Star’s cape, and the bridge lights shone over a happy, safe city.",
        inner_monologue="A hero is not only someone who wins; a hero is someone who notices before striking.",
    ),
    Scenario(
        opener="Above the train yard, Masked Comet balanced on a chimney and watched sirens blink between the rails.",
        threat="A grizzly had wandered into a loading bay after smelling fish from the diner next door.",
        wrong_turn="Masked Comet first thought of a loud blast to terminate the danger at once.",
        clue="Then the diner window fogged, and claw prints pointed straight to a tipped fish crate.",
        dialogue='Masked Comet called, "Did anyone leave food here?" and the diner cook answered, "I did, and I am sorry."',
        action="He tucked the crate onto a high cart, scoured the loading bay for scraps, and guided the grizzly toward the river path with a bouncing red ball.",
        result="The grizzly lumbered away, the train yard quieted, and the cook promised to lock the fish in a cooler from then on.",
        ending="As the last train rolled out, Masked Comet laughed with the cook, and the yard lights glowed like tiny stars.",
        inner_monologue="Search first. Smash later only if there is no kinder way.",
    ),
]


@dataclass
class StoryParams:
    city: str
    hero: str
    sidekick: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld with an inner-monologue quest and a happy ending.")
    ap.add_argument("--city", choices=["city"], default="city")
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    hero = args.hero or rng.choice(["Captain Bright", "Hero Star", "Masked Comet"])
    sidekick = args.sidekick or rng.choice(["Mina", "Jace", "Lola", "Nico"])
    return StoryParams(city="city", hero=hero, sidekick=sidekick)


def reasonableness_gate(params: StoryParams) -> None:
    if params.city != "city":
        raise StoryError("This quest belongs in a city setting.")
    if not params.hero or not params.sidekick:
        raise StoryError("A hero and a sidekick are required.")
    if params.hero == params.sidekick:
        raise StoryError("The hero and sidekick must be different characters.")


def _scenario_key(params: StoryParams) -> int:
    base = params.seed if params.seed is not None else sum((i + 1) * ord(c) for i, c in enumerate(params.hero + params.sidekick))
    return base


def generate_story(world: World, params: StoryParams) -> World:
    reasonableness_gate(params)
    scenario = SCENARIOS[_scenario_key(params) % len(SCENARIOS)]
    hero = world.add(Entity(id="hero", kind="character", type="man", label=params.hero, location="clock tower"))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="woman", label=params.sidekick, location="street"))
    grizzly = world.add(Entity(id="grizzly", kind="creature", type="bear", label="grizzly", location="museum district"))

    world.say(scenario.opener)
    world.say(scenario.threat)
    world.say(scenario.wrong_turn)
    world.say(f"Inside his helmet, {params.hero} had one sharp inner monologue: {scenario.inner_monologue}")
    world.say(scenario.clue)
    world.say(scenario.dialogue)
    world.say(scenario.action)
    world.say(scenario.result)
    world.say(f"{params.sidekick} grinned and said, \"We did it together.\" {params.hero} answered, \"That was the real quest.\"")
    world.say(scenario.ending)

    world.facts.update(hero=hero, sidekick=sidekick, grizzly=grizzly, scenario=scenario)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Scenario = f["scenario"]
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    return [
        QAItem(
            question="Who was the superhero in the story?",
            answer=f"{hero.label} was the superhero who solved the city problem.",
        ),
        QAItem(
            question="What problem did the heroes face?",
            answer="They had to deal with a grizzly beast near busy city streets without harming people.",
        ),
        QAItem(
            question="What was the hero's inner monologue?",
            answer=s.inner_monologue,
        ),
        QAItem(
            question="What clue changed the hero's plan?",
            answer=s.clue,
        ),
        QAItem(
            question="What did the hero and sidekick say to each other?",
            answer=f'They spoke when {s.dialogue}',
        ),
        QAItem(
            question="How did the quest end?",
            answer=s.ending,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to scour a place?",
            answer="To scour a place means to search it carefully and thoroughly.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to end something or stop it completely.",
        ),
        QAItem(
            question="Why is a happy ending important in a superhero story?",
            answer="A happy ending shows that the danger passed and the city is safe again.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to solve a problem or reach a goal.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a superhero story with an inner monologue, a quest, and a happy ending.",
        "Include the words terminate, grizzly, and scour in a child-friendly city adventure.",
        "Make sure the hero has a brief spoken exchange that changes what they do next.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {e.kind} {e.type} {e.label} @{e.location} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(city).
valid(hero).
valid(sidekick).
valid(threat).
"""

def asp_facts() -> str:
    asp = _lazy_asp()
    return "\n".join([
        asp.fact("setting", "city"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "happy_ending"),
        asp.fact("style", "superhero_story"),
        asp.fact("seed_word", "terminate"),
        asp.fact("seed_word", "grizzly"),
        asp.fact("seed_word", "scour"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    asp = _lazy_asp()
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [("city", "hero", "sidekick"), ("city", "hero", "threat")]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = {("city", "hero", "sidekick"), ("city", "hero", "threat")}
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(setting="city")
    world = generate_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for i, q in enumerate(sample.prompts, 1):
            print(f"Prompt {i}: {q}")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")


CURATED = [
    StoryParams(city="city", hero="Captain Bright", sidekick="Mina", seed=1),
    StoryParams(city="city", hero="Hero Star", sidekick="Jace", seed=2),
    StoryParams(city="city", hero="Masked Comet", sidekick="Lola", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/1."))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seed = args.seed if args.seed is not None else random.randrange(2**31)
        rng = random.Random(seed)
        samples = []
        for i in range(args.n):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            samples.append(generate(params))

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
            header = f"### {p.hero} and {p.sidekick}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
