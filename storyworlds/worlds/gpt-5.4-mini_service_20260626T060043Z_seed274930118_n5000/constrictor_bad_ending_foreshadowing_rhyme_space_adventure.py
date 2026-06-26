#!/usr/bin/env python3
"""
storyworlds/worlds/constrictor_bad_ending_foreshadowing_rhyme_space_adventure.py
==============================================================================

A tiny space-adventure storyworld about a curious child, a cramped ship, and a
constrictor that hints at trouble before the trouble lands.

Premise
-------
A small crew explores a bright moon base. The child loves listening to the ship's
rhymes and watching the stars. The crew carries a narrow supply tube called the
constrictor, a flexible cargo coil that keeps one crate from sliding during
takeoff.

Tension
-------
The captain notices a foreshadowing sign: the constrictor's clasp is warm, the
cargo bay smells of ozone, and the ship's lights keep flickering in a pattern
that rhymes with trouble. Still, the child wants to pull the coil tighter and
peek into the sealed hatch.

Turn
----
The child ignores the warning and the constrictor snaps hard around the cargo
crate. The hatch sticks, the coil jams the only path to the repair ladder, and
the crew cannot open the bay in time.

Resolution
----------
This world deliberately allows a bad ending: the mission does not recover, the
cargo is lost to drifting cold, and the final image proves the warning was real.
The story remains child-facing, concrete, and fully state-driven.
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Ship:
    name: str
    place: str = "the moon base"
    spaceworthy: bool = True
    alarm: bool = False


@dataclass
class World:
    ship: Ship
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.ship)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Nova"
    gender: str = "girl"
    parent: str = "captain"
    trait: str = "curious"
    ship: str = "Star Kite"
    cargo: str = "constrictor"
    ending: str = "bad"


CREW_NAMES = ["Nova", "Iris", "Milo", "Pip", "Arlo", "Lyra", "Juno", "Rio"]
TRAITS = ["curious", "brave", "hopeful", "restless", "bright", "careful"]
SHIP_NAMES = ["Star Kite", "Comet Bell", "Moon Ribbon", "Sky Lantern"]


def rhyme_line(one: str, two: str) -> str:
    return f"{one} and {two} sound alike in the quiet ship night."


def foreshadow_text() -> str:
    return (
        "The bay lights blinked twice, then once, like a tiny warning in code. "
        "The constrictor's clasp felt warm, and the air near the hatch smelled faintly of ozone."
    )


def bad_ending_text(hero: Entity, cargo: Entity) -> str:
    return (
        f"The coil jammed the hatch, and the crew could not free {cargo.it()} in time. "
        f"By the time the alarms faded, the crate had drifted into the dark."
    )


def setup(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"hope": 1.0, "curiosity": 1.0},
        memes={"joy": 1.0},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label=params.parent,
        meters={"worry": 1.0},
        memes={"care": 1.0},
    ))
    cargo = world.add(Entity(
        id="Constrictor",
        type="tool",
        label="constrictor",
        phrase="a flexible cargo coil",
        caretaker=captain.id,
        meters={"tightness": 0.5, "heat": 0.5},
        memes={"quiet_warning": 1.0},
    ))
    world.facts.update(child=child, captain=captain, cargo=cargo, params=params)
    return child, captain, cargo


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    captain: Entity = f["captain"]
    cargo: Entity = f["cargo"]
    return [
        QAItem(
            question=f"Who wanted to inspect the constrictor on the moon base?",
            answer=f"{child.id} wanted to inspect the constrictor while {captain.label} watched the cargo bay."
        ),
        QAItem(
            question="What warning helped foreshadow the bad ending?",
            answer=(
                "The bay lights blinked in a strange pattern, the clasp felt warm, "
                "and the air smelled like ozone, which hinted that the cargo would get stuck."
            ),
        ),
        QAItem(
            question="What happened when the constrictor was pulled too tight?",
            answer=(
                f"It jammed the hatch shut, trapped the repair ladder, and kept the crew from saving the cargo."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a constrictor in this story?",
            answer=(
                "A constrictor is a tight cargo coil that squeezes around a crate so it will not slide during takeoff."
            ),
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer=(
                "Foreshadowing gives little warning signs early, so the reader can sense that something important may happen later."
            ),
        ),
        QAItem(
            question="What is a rhyme?",
            answer=(
                "A rhyme is when two words or lines sound alike at the end, which makes the story feel playful or musical."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    return [
        "Write a short space adventure for a young child that includes a constrictor, a warning sign, and a sad ending.",
        f"Tell a moon-base story where {child.id} notices a rhyming warning before the cargo bay goes wrong.",
        "Write a child-facing sci-fi tale that uses foreshadowing and ends with the crew losing the crate.",
    ]


def generate_story(world: World) -> None:
    child: Entity = world.facts["child"]
    captain: Entity = world.facts["captain"]
    cargo: Entity = world.facts["cargo"]
    ship = world.ship

    world.say(
        f"On the {ship.place}, {child.id} loved every shiny panel of the ship {ship.name}. "
        f"{child.pronoun().capitalize()} liked the quiet hum, the star maps, and little rhymes that the captain sang."
    )
    world.say(
        f"One job on the ship was the constrictor, a flexible cargo coil that held a crate still for launch."
    )
    world.para()
    world.say(
        f"Before the hatch was opened, {captain.label} pointed at the bay and spoke softly. "
        f"{foreshadow_text()}"
    )
    world.say(
        f'"The hiss and the twist, the warning will insist," {captain.label} said with a rhyme. '
        f"{child.id} smiled, but the warning was real."
    )
    world.para()
    world.say(
        f"{child.id} wanted to pull the constrictor tighter and peek inside the sealed hatch."
    )
    world.say(
        f"{child.pronoun().capitalize()} did not listen when {captain.label} asked {child.pronoun('object')} to stop."
    )
    world.say(
        f"The coil snapped snug around the crate, and the hatch stuck fast with a heavy clack."
    )
    world.say(
        f"{bad_ending_text(child, cargo)}"
    )
    world.para()
    world.say(
        f"In the end, the moon base stayed quiet in the dark, and the little rhyme felt like a real warning after all."
    )
    world.facts["ending"] = "bad"
    world.facts["foreshadowed"] = True
    world.facts["rhymed"] = True
    world.facts["failed"] = True


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
    lines.append(f"  ship     ({world.ship.name}) place={world.ship.place} spaceworthy={world.ship.spaceworthy}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.kind:9}/{e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_wants(C) :- child(C), curious(C).
foreshadowed :- warm_clasp, ozone_smell, blinking_lights.
warning_sign :- foreshadowed.
bad_ending :- child_wants(C), ignores_warning(C), hatch_stuck, cargo_lost.
rhyme_present :- rhyme(W1,W2).
story_valid :- child(C), constrictor(Co), warning_sign, rhyme_present, bad_ending.
#show story_valid/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("child", "Nova"))
    lines.append(asp.fact("constrictor", "Constrictor"))
    lines.append(asp.fact("warm_clasp"))
    lines.append(asp.fact("ozone_smell"))
    lines.append(asp.fact("blinking_lights"))
    lines.append(asp.fact("rhyme", "hiss", "twist"))
    lines.append(asp.fact("ignores_warning", "Nova"))
    lines.append(asp.fact("hatch_stuck"))
    lines.append(asp.fact("cargo_lost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_valid/0."))
    ok = any(sym.name == "story_valid" for sym in model)
    if ok:
        print("OK: ASP twin agrees that this world can produce the intended bad-ending space story.")
        return 0
    print("MISMATCH: ASP twin did not validate the story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure world with a constrictor, foreshadowing, rhyme, and a bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CREW_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        seed=args.seed,
        name=name,
        gender=gender,
        parent="captain",
        trait=trait,
        ship="Star Kite",
        cargo="constrictor",
        ending="bad",
    )


def generate(params: StoryParams) -> StorySample:
    world = World(Ship(name=params.ship))
    setup(world, params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_valid/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        seeds = [base_seed + i for i in range(5)]
    else:
        seeds = [base_seed + i for i in range(args.n)]

    for seed in seeds:
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
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
