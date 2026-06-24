#!/usr/bin/env python3
"""
A small fairy-tale story world about Sillydilly at a busy street crossing,
where magic, foreshadowing, and practical problem solving turn a risky crossing
into a safe one.
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
    seed: Optional[int] = None
    name: str = "Sillydilly"
    companion: str = "the little mouse"
    object_name: str = "the gold crumb"
    crossing: str = "busy street crossing"
    charm: str = "moon-glimmer charm"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
        lines.append(f"  facts={self.facts}")
        return "\n".join(lines)


SETTINGS = {
    "busy street crossing": {
        "place_line": "At a busy street crossing, carts rattled, bells chimed, and boots hurried over the stones.",
        "risk": "the road was crowded with wagons and a splashy puddle hid the curb",
        "foreshadow": "A shiny tram bell had already rung three times, which was a fair-tale warning that trouble was near.",
    }
}

CHARS = [
    ("Sillydilly", "character"),
    ("Myrtle", "character"),
    ("the little mouse", "companion"),
]

MAGIC_CHOICES = [
    "a moon-glimmer charm",
    "a pocket lantern of gold dust",
    "a whispering ribbon",
]

PROBLEM_SOLVERS = [
    "counting the steps aloud",
    "drawing a safe path with chalk",
    "asking the sparrow guide for the quietest moment",
    "waiting for the red wagon to pass",
]


ASP_RULES = r"""
character(sillydilly).
setting(busy_street_crossing).
magic(moon_glimmer_charm).
problem(traffic).
solution(chalk_path).

unsafe(C) :- character(C), setting(busy_street_crossing).
needs_plan(C) :- unsafe(C), magic(moon_glimmer_charm).
safe(C) :- needs_plan(C), solution(chalk_path).
#show unsafe/1.
#show needs_plan/1.
#show safe/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("character", "sillydilly"),
        asp.fact("setting", "busy_street_crossing"),
        asp.fact("magic", "moon_glimmer_charm"),
        asp.fact("solution", "chalk_path"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: Sillydilly at a busy street crossing."
    )
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
    if args.n < 1:
        raise StoryError("n must be at least 1")
    return StoryParams(
        seed=args.seed,
        name="Sillydilly",
        companion=rng.choice([c for c, k in CHARS if c != "Sillydilly"]),
        object_name="the gold crumb",
        crossing="busy street crossing",
        charm=rng.choice(MAGIC_CHOICES),
    )


def make_world(params: StoryParams) -> World:
    w = World(params=params)
    hero = w.add(Entity(id=params.name, kind="character", label=params.name))
    comp = w.add(Entity(id="companion", kind="character", label=params.companion))
    charm = w.add(Entity(id="charm", kind="thing", label=params.charm))
    prize = w.add(Entity(id="crumb", kind="thing", label=params.object_name))
    road = w.add(Entity(id="crossing", kind="place", label=params.crossing))

    hero.memes["curious"] = 1
    hero.memes["hope"] = 1
    comp.memes["wary"] = 1
    road.meters["crowd"] = 3
    road.meters["danger"] = 2
    charm.meters["glow"] = 1

    w.facts.update(
        hero=hero.id,
        companion=comp.label,
        object=prize.label,
        crossing=road.label,
        charm=charm.label,
    )
    return w


def generate_story(world: World) -> None:
    p = world.params
    hero = world.get(p.name)
    comp = world.get("companion")
    road = world.get("crossing")
    charm = world.get("charm")
    crumb = world.get("crumb")

    setup = SETTINGS[p.crossing]
    world.say(
        f"Once upon a time, Sillydilly lived under a lintel of ivy and dreamed of "
        f"{crumb.label} that sparkled like dawn."
    )
    world.say(
        f"That morning, {setup['place_line']} Sillydilly held {comp.label} close and "
        f"looked at {charm.label} tucked in a tiny pocket."
    )
    world.say(
        f"{setup['foreshadow']} Sillydilly still wanted to cross, because {crumb.label} "
        f"lay on the far side, where a baker had dropped it by mistake."
    )

    world.para()
    hero.memes["want"] = 1
    hero.meters["steps"] = 1
    world.say(
        f"Sillydilly began to step toward the curb, but the street hissed with wheels "
        f"and the crossing looked like a river of hurry."
    )
    world.say(
        f"{comp.label.capitalize()} squeaked, 'Wait! A busy road needs a plan, not a dash.'"
    )
    world.say(
        f"Then the {p.charm} gave a tiny blink, as if it knew a clever answer was near."
    )

    world.para()
    hero.memes["concern"] = 1
    comp.memes["idea"] = 1
    world.say(
        f"Sillydilly remembered the chalk in the satchel, so they drew a white little path "
        f"from the curb to the lamp post and back again."
    )
    world.say(
        f"They waited for the red wagon to roll by, counted three breaths, and held hands "
        f"with {comp.label} while the charm shone softly."
    )
    world.say(
        f"When the bell rang a last time, Sillydilly crossed on the chalk path, brave and "
        f"careful, and {crumb.label} was lifted from the stones at the other side."
    )

    world.para()
    hero.memes["joy"] = 2
    comp.memes["relief"] = 2
    road.meters["danger"] = 0
    world.say(
        f"In the end, Sillydilly smiled at the busy crossing, for magic had helped, "
        f"but problem solving had truly made the way safe."
    )
    world.say(
        f"They tucked {crumb.label} into a napkin, and the street seemed less fearsome, "
        f"as if it had learned to mind its manners."
    )
    world.facts["resolved"] = True
    world.facts["magic"] = p.charm
    world.facts["problem_solving"] = "chalk path"


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    return [
        QAItem(
            question="Who was the fairy-tale hero in the story?",
            answer=f"The fairy-tale hero was {p.name}, who was called Sillydilly.",
        ),
        QAItem(
            question="What made the crossing feel risky?",
            answer="It felt risky because the street was busy, with wagons, bells, and hurried traffic.",
        ),
        QAItem(
            question="How did Sillydilly solve the problem?",
            answer="Sillydilly solved the problem by drawing a chalk path, waiting for a safe moment, and crossing carefully with a helper.",
        ),
        QAItem(
            question="What magical thing helped in the story?",
            answer=f"The {p.charm} gave a gentle glow that made the careful plan feel magical.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue that something important or tricky may happen soon.",
        ),
        QAItem(
            question="Why is a busy street crossing a place where people must be careful?",
            answer="People must be careful there because cars, wagons, and other travelers can move quickly and make crossing dangerous.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a smart way to handle a difficulty instead of rushing into it.",
        ),
        QAItem(
            question="How can magic appear in a fairy tale?",
            answer="Magic can appear as a glow, a charm, a whispered spell, or another wonder that helps the characters.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a fairy tale about {p.name} at a busy street crossing with a little magic and a careful solution.",
        f"Tell a story where Sillydilly sees a warning sign, remembers a charm, and solves the crossing problem wisely.",
        f"Compose a child-friendly tale that includes foreshadowing, a magic charm, and a safe way to cross the street.",
    ]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
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
        print(sample.world.trace())
    if qa:
        print()
        for i, q in enumerate(sample.prompts, 1):
            print(f"P{i}. {q}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def valid_combos() -> list[tuple[str, str, str]]:
    return [("busy street crossing", "magic", "problem solving")]


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show safe/1."))
    return sorted(set(asp.atoms(model, "safe")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def resolve_and_generate(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show safe/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(seed=base_seed))]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
