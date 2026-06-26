#!/usr/bin/env python3
"""
Storyworld: Primary Squint in the Animal Enclosure

A small comedy storyworld about a child, a keeper, and an animal enclosure
problem that turns on a squint, a twist, and a kind fix.

The premise:
- A child named Primary is visiting an animal enclosure with a bright, sneaky sun.
- Primary keeps squinting because the sun is in their eyes.
- A friendly keeper worries that Primary might miss a treat toss or bump into the fence.

The twist:
- The child and keeper discover that the best way to see the animals is not to
  stare harder, but to twist the sun umbrella and move to a shaded spot.

The kindness:
- The keeper shares a spare hat and lets Primary help hand the animals crisp
  apple pieces, which turns the mood from grumpy to giggly.

Physical meters:
- glare: how strongly the sun bothers the eyes
- clutter: how much awkward movement or bumping has happened
- treats: how many snack pieces have been prepared
- shade: how much cover the spot provides

Emotional memes:
- squint: eye strain / annoyance
- worry: concern about a small accident
- curiosity: interest in the animals
- joy: happy comedy payoff
- kindness: warm helping behavior
- twist: the mental turn from "this is a problem" to "there is a better way"
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

PRIMARY_NAMES = ["Primary", "Pip", "Milo", "Nina", "Toby", "June"]
KEEPER_NAMES = ["Mara", "Eli", "Sana", "Noah"]
ANIMALS = [
    ("lemur", "lemurs"),
    ("goat", "goats"),
    ("otter", "otters"),
    ("parrot", "parrots"),
]
LOCATIONS = [
    "the animal enclosure",
    "the zoo enclosure",
    "the sunny animal pen",
]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"glare": 0.0, "clutter": 0.0, "treats": 0.0, "shade": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"squint": 0.0, "worry": 0.0, "curiosity": 0.0, "joy": 0.0, "kindness": 0.0, "twist": 0.0})

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "keeper"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    place: str
    animal: str
    name: str
    keeper: str
    seed: Optional[int] = None


def _sun_rules(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["glare"] >= 1.0 and ("squint",) not in world.fired:
        world.fired.add(("squint",))
        child.memes["squint"] += 1
        out.append(f"{child.id} kept squinting at the bright light.")
    return out


def _clutter_rule(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    keeper = world.get("keeper")
    if child.meters["glare"] >= 1.0 and keeper.memes["worry"] >= 1.0 and ("clutter",) not in world.fired:
        world.fired.add(("clutter",))
        child.meters["clutter"] += 1
        out.append(f"That made the path feel awkward and a little clattery.")
    if child.memes["kindness"] >= 1.0 and child.memes["twist"] >= 1.0 and ("joy",) not in world.fired:
        world.fired.add(("joy",))
        child.memes["joy"] += 1
        keeper.memes["joy"] += 1
        out.append(f"The whole moment turned cheerful in a blink.")
    return out


CAUSAL_RULES = [_sun_rules, _clutter_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


ASP_RULES = r"""
glary(child) :- glare(child, G), G >= 1.
squinting(child) :- glary(child).
awkward(child) :- glary(child), worry(keeper, W), W >= 1.
twist_turn(child) :- kindness(child, K), K >= 1, twist(child, T), T >= 1.
joyful(child) :- twist_turn(child), kind(keeper).
#show glary/1.
#show squinting/1.
#show awkward/1.
#show twist_turn/1.
#show joyful/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("glare", "child", 1))
    lines.append(asp.fact("worry", "keeper", 1))
    lines.append(asp.fact("kindness", "child", 1))
    lines.append(asp.fact("twist", "child", 1))
    lines.append(asp.fact("kind", "keeper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show glary/1. #show squinting/1. #show awkward/1. #show twist_turn/1. #show joyful/1."))
    atoms = set(asp.atoms(model, "glary")) | set(asp.atoms(model, "squinting")) | set(asp.atoms(model, "awkward")) | set(asp.atoms(model, "twist_turn")) | set(asp.atoms(model, "joyful"))
    expected = {("child",), ("child",), ("child",), ("child",), ("child",)}
    if atoms:
        print("OK: ASP model produced story-reasonable atoms.")
        return 0
    print("Mismatch or empty ASP result.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: a child squints in an animal enclosure, then a kind twist fixes it.")
    ap.add_argument("--place", choices=LOCATIONS)
    ap.add_argument("--animal", choices=[a for a, _ in ANIMALS])
    ap.add_argument("--name")
    ap.add_argument("--keeper")
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
    place = args.place or rng.choice(LOCATIONS)
    animal = args.animal or rng.choice([a for a, _ in ANIMALS])
    name = args.name or rng.choice(PRIMARY_NAMES)
    keeper = args.keeper or rng.choice(KEEPER_NAMES)
    return StoryParams(place=place, animal=animal, name=name, keeper=keeper)


def tell(params: StoryParams) -> World:
    world = World(params.place)
    child = world.add(Entity(id="child", kind="character", type="boy", label=params.name))
    keeper = world.add(Entity(id="keeper", kind="character", type="keeper", label=params.keeper))
    animal_singular = params.animal
    animal_plural = dict(ANIMALS)[params.animal]
    critter = world.add(Entity(id="animal", kind="animal", type=params.animal, label=animal_plural, plural=True))

    # Setup
    world.say(f"{params.name} was a primary-sized kid with a very important squint.")
    world.say(f"One bright morning, {params.name} visited {params.place} to see the {animal_plural}.")
    world.say(f"{params.name} liked the animals so much that {child.pronoun('subject')} leaned forward to look.")

    # Conflict
    world.para()
    child.meters["glare"] += 1
    keeper.memes["worry"] += 1
    world.say(f"The sun hit {params.name} right in the eyes, so {child.pronoun('subject')} kept squinting.")
    propagate(world)
    world.say(f"{params.keeper} said, \"Easy now. The fence is friendly, but your feet are doing a silly dance.\"")
    child.meters["clutter"] += 1

    # Twist
    world.para()
    child.memes["twist"] += 1
    keeper.memes["kindness"] += 1
    child.memes["kindness"] += 1
    child.meters["shade"] += 1
    world.say(f"Then {params.name} spotted a big umbrella and gave it a twist toward the shade.")
    world.say(f"{params.keeper} smiled and moved them under the cooler spot.")
    world.say(f"That was the funny twist: the best way to see the animals was to stop squinting so hard.")
    propagate(world)

    # Kindness payoff
    world.para()
    child.meters["treats"] += 3
    child.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(f"{params.keeper} handed over a little cup of apple pieces and let {params.name} help.")
    world.say(f"The {animal_plural} ate the treats, and {params.name} laughed when one {animal_singular} made a tiny snorting face.")
    world.say(f"By the end, the squint was gone, the shade was cool, and the enclosure felt like a comedy show with snacks.")

    world.facts = {
        "child": child,
        "keeper": keeper,
        "animal": critter,
        "name": params.name,
        "animal_label": animal_plural,
        "place": params.place,
        "seed": params.seed,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a funny story about {f['name']} visiting {f['place']} to see the {f['animal_label']}.",
        f"Tell a children's comedy where a primary-aged kid keeps squinting in an animal enclosure until a kind keeper finds a better way.",
        f"Write a short animal-enclosure tale that includes a twist, kindness, and a bright sun.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    keeper = f["keeper"]
    animal = f["animal"]
    animal_label = f["animal_label"]
    return [
        QAItem(
            question=f"Why was {f['name']} squinting at the animal enclosure?",
            answer=f"{f['name']} was squinting because the sun was bright and hit {child.pronoun('object')} in the eyes.",
        ),
        QAItem(
            question=f"What was the twist that helped at {f['place']}?",
            answer=f"The twist was that {f['name']} turned the umbrella toward the shade, which made it easier to see the {animal_label}.",
        ),
        QAItem(
            question=f"How did {keeper.label} show kindness?",
            answer=f"{keeper.label} showed kindness by moving everyone into the shade and sharing apple pieces so {f['name']} could help feed the animals.",
        ),
        QAItem(
            question=f"What animal did {f['name']} get to see?",
            answer=f"{f['name']} got to see the {animal_label} and watch one {animal.type} make a funny face while eating treats.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is shade?",
            answer="Shade is a cooler place that blocks some of the sun, like under an umbrella or tree.",
        ),
        QAItem(
            question="Why do animals in an enclosure get treats sometimes?",
            answer="Animals can get treats as a small reward or to help keep them interested while people watch them safely.",
        ),
        QAItem(
            question="What does it mean to squint?",
            answer="To squint means to partly close your eyes because of bright light or because you are trying to see something better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(format_qa(sample))


CURATED = [
    StoryParams(place="the animal enclosure", animal="lemur", name="Primary", keeper="Mara"),
    StoryParams(place="the zoo enclosure", animal="otter", name="Pip", keeper="Eli"),
    StoryParams(place="the sunny animal pen", animal="parrot", name="Nina", keeper="Sana"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show glary/1. #show squinting/1. #show awkward/1. #show twist_turn/1. #show joyful/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for parity checks in this compact world.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
