#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld: a deckhand, a tricky stance, and a mitt that can
turn a slippery moment into a safe and funny one.

Seed tale inspiration:
---
A young deckhand on a small pirate ship wants to help near the aft deck, but the
boards are slick and the roll of the sea makes a wobbly stance risky. A mate
warns the child, spots the danger before it happens, and offers a bright mitt so
the child can grip the rope and keep steady. There is a little humor in the
sailors' shouts and the squeaky sound effects of the ship, but the ending is
warm: the child learns a better stance and helps safely aft of the mast.
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
class Entity:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the aft deck"
    swell: str = "rocky"
    sound: str = "creak"
    foreshadow: str = "The sea had a sly look, like it was about to tease the deck."


@dataclass
class Stance:
    id: str
    name: str
    steadiness: float
    slip_risk: float
    funny_desc: str
    sound: str


@dataclass
class Mitt:
    id: str
    name: str
    grip: float
    warmth: float
    sound: str
    protects_from_slip: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    stance: str
    mitt: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


SETTINGS = {
    "aft_deck": Setting(
        place="the aft deck",
        swell="rocky",
        sound="creak",
        foreshadow="The sea kept bumping the hull like it knew a joke was coming.",
    ),
    "harbor_quarterdeck": Setting(
        place="the quarterdeck aft of the mast",
        swell="bobbing",
        sound="clatter",
        foreshadow="The ropes hummed softly, as if they were warning everyone to mind their feet.",
    ),
}

STANCES = {
    "wobbly": Stance(
        id="wobbly",
        name="wobbly stance",
        steadiness=0.2,
        slip_risk=0.9,
        funny_desc="a wobble like a pudding on a spoon",
        sound="wibble-wobble",
    ),
    "wide": Stance(
        id="wide",
        name="wide stance",
        steadiness=0.9,
        slip_risk=0.1,
        funny_desc="feet spread like a baby crab learning to dance",
        sound="thump-thump",
    ),
    "tiptoe": Stance(
        id="tiptoe",
        name="tiptoe stance",
        steadiness=0.4,
        slip_risk=0.6,
        funny_desc="as if the deck were made of hot pies",
        sound="tap-tap",
    ),
}

MITTS = {
    "rope_mitt": Mitt(
        id="rope_mitt",
        name="a rope mitt",
        grip=0.8,
        warmth=0.3,
        sound="squeak-squeak",
    ),
    "sea_mitt": Mitt(
        id="sea_mitt",
        name="a sea mitt",
        grip=0.7,
        warmth=0.6,
        sound="snug-swish",
    ),
    "captain_mitt": Mitt(
        id="captain_mitt",
        name="a captain's mitt",
        grip=0.9,
        warmth=0.4,
        sound="thrum-thrum",
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Tessa", "Pip", "Ada", "Luna"]
BOY_NAMES = ["Finn", "Jory", "Nate", "Ollie", "Bram", "Theo"]
PARENTS = ["mate", "captain", "first mate"]


def reasonableness_gate(stance: Stance, mitt: Mitt) -> bool:
    return stance.slip_risk > 0.45 and mitt.protects_from_slip and mitt.grip >= 0.7


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in STANCES.items():
        lines.append(asp.fact("stance", sid))
        lines.append(asp.fact("steadiness", sid, int(s.steadiness * 10)))
        lines.append(asp.fact("slip_risk", sid, int(s.slip_risk * 10)))
    for mid, m in MITTS.items():
        lines.append(asp.fact("mitt", mid))
        lines.append(asp.fact("grip", mid, int(m.grip * 10)))
        if m.protects_from_slip:
            lines.append(asp.fact("protects_from_slip", mid))
    return "\n".join(lines)


ASP_RULES = r"""
unsafe_stance(S) :- stance(S), slip_risk(S, R), R >= 5.
good_mitt(M) :- mitt(M), protects_from_slip(M), grip(M, G), G >= 7.
compatible(S, M) :- unsafe_stance(S), good_mitt(M).
#show compatible/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibles() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {
        (sid, mid)
        for sid, s in STANCES.items()
        for mid, m in MITTS.items()
        if reasonableness_gate(s, m)
    }
    asp_set = set(asp_compatibles())
    if py == asp_set:
        print(f"OK: clingo gate matches Python reasonableness ({len(py)} pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in python:", sorted(py - asp_set))
    print("  only in ASP:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld: aft, stance, mitt.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--stance", choices=STANCES)
    ap.add_argument("--mitt", choices=MITTS)
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
    stance_id = args.stance or rng.choice(list(STANCES))
    mitt_id = args.mitt or rng.choice(list(MITTS))
    if not reasonableness_gate(STANCES[stance_id], MITTS[mitt_id]):
        raise StoryError("No honest pirate story fits that stance and mitt together.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent, stance=stance_id, mitt=mitt_id)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS["aft_deck"])
    hero = world.add(Entity(id=params.name, type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type="adult", label=params.parent))
    stance = STANCES[params.stance]
    mitt = MITTS[params.mitt]

    hero.memes["curious"] = 1
    world.say(f"{hero.id} was a young deckhand with a brave heart and a curious grin.")
    world.say(f"{world.setting.foreshadow}")
    world.say(f"{hero.id} loved helping aft of the mast, where the ropes swayed and the deck went {world.setting.sound}.")
    world.say(f"But {hero.pronoun('possessive')} {stance.name} was {stance.funny_desc}, and that made the boards feel tricky.")

    world.lines.append("")
    world.say(f"One salty morning, the ship gave a loud {world.setting.sound}! The line near the aft deck went {stance.sound} under {hero.id}'s feet.")
    world.say(f"{hero.id} tried to stand {stance.name}, but the sea rolled the deck and made {hero.pronoun('possessive')} knees dance.")
    world.say(f'"Hold steady!" cried the {parent.label}. "That stance is a slippery scallop on a stormy plate!"')
    world.say(f"{hero.id} blinked, then giggled. " f'"A scallop? I thought I was only wobbly, not dinner!"')

    world.lines.append("")
    if reasonableness_gate(stance, mitt):
        world.say(f"The {parent.label} held up {mitt.name}, and it made a friendly {mitt.sound}.")
        world.say(f'"Put this on," said the {parent.label}. "It can grip the rope, and your feet can try a better stance."')
        world.say(f"{hero.id} slipped {mitt.it()} on, and the mitt felt snug and sure.")
        world.say(f"With the mitt on, {hero.id} switched to a wide stance, feet apart like a little crab on parade.")
        world.say(f"The rope stopped slipping away, and the deck no longer felt like a joke played by the sea.")
        world.say(f"{hero.id} hauled the line aft with a strong heave-ho, and the sails answered with a happy flap.")
        world.say(f"At the end, {hero.id} stood steady by the aft rail, mitt bright, grin wider, while the ship rocked safely on.")
    else:
        raise StoryError("The chosen stance and mitt do not make a safe pirate tale.")

    world.facts.update(hero=hero, parent=parent, stance=stance, mitt=mitt, setting=world.setting)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale for a child that uses the words "aft", "stance", and "mitt".',
        f"Tell a humorous shipboard story where {f['hero'].id} learns a safer stance aft of the mast with help from {f['mitt'].name}.",
        f"Write a tiny pirate story with foreshadowing and sound effects, ending with a deckhand standing steady on the aft deck.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, stance, mitt = f["hero"], f["parent"], f["stance"], f["mitt"]
    return [
        QAItem(
            question=f"Why did {hero.id} need help on the aft deck?",
            answer=f"{hero.id} needed help because {hero.pronoun('possessive')} {stance.name} was wobbly and the deck was slick, so a safer way was needed.",
        ),
        QAItem(
            question=f"What did the {parent.label} give {hero.id} to make gripping safer?",
            answer=f"The {parent.label} gave {hero.id} {mitt.name}, which helped {hero.id} grip the rope and keep steady.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"It ended with {hero.id} standing steady in a wide stance on the aft deck and helping the ship safely.",
        ),
        QAItem(
            question=f"What funny thing did {hero.id} say about the warning?",
            answer=f"{hero.id} laughed and said {hero.pronoun('subject')} was only wobbly, not dinner, after being called a slippery scallop.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does aft mean on a ship?",
            answer="Aft means toward the back of the ship.",
        ),
        QAItem(
            question="What is a mitt used for?",
            answer="A mitt is something you wear on your hand to help keep it warm or give it a better grip.",
        ),
        QAItem(
            question="What is a stance?",
            answer="A stance is the way someone stands with their feet and body.",
        ),
    ]


def dump_trace(world: World) -> str:
    f = world.facts
    return "\n".join([
        "--- world model state ---",
        f"hero={f['hero'].id} stance={f['stance'].id} mitt={f['mitt'].id}",
        f"setting={f['setting'].place} swell={f['setting'].swell}",
    ])


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mira", gender="girl", parent="mate", stance="wobbly", mitt="rope_mitt"),
    StoryParams(name="Finn", gender="boy", parent="first mate", stance="tiptoe", mitt="sea_mitt"),
    StoryParams(name="Nell", gender="girl", parent="captain", stance="wobbly", mitt="captain_mitt"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_pairs() -> list[tuple]:
    return asp_compatibles()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible stance/mitt pairs:\n")
        for s, m in pairs:
            print(f"  {s:10} {m}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
            header = f"### {p.name}: {p.stance} with {p.mitt}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
