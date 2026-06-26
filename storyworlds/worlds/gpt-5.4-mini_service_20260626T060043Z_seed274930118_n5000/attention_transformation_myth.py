#!/usr/bin/env python3
"""
Attention transformation myth-world.

A small mythic simulation about a character who seeks attention, earns it in a
ritual, and is transformed by that attention into a new form. The world is kept
tiny on purpose: one setting, a few entities, one tension, one resolution.

The story is generated from world state, not from a frozen paragraph. The same
simulation also powers QA and a small ASP twin for the reasonableness gate.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "goddess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "god"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str = "shrine"
    glow: str = "moonlight"


@dataclass
class Ritual:
    id: str
    name: str
    seeks: str
    requires_attention: bool
    turns_into: str
    transformation: str
    clue: str


@dataclass
class StoryParams:
    ritual: str
    name: str
    gender: str
    witness: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
    "moon_shrine": Place(name="the moon shrine", kind="shrine", glow="silver moonlight"),
    "river_bank": Place(name="the river bank", kind="riverbank", glow="cold starlight"),
}

RITUALS = {
    "attention": Ritual(
        id="attention",
        name="the attention rite",
        seeks="attention",
        requires_attention=True,
        turns_into="a silver fox",
        transformation="turned into a silver fox",
        clue="a hush of many eyes",
    ),
    "song": Ritual(
        id="song",
        name="the song rite",
        seeks="attention",
        requires_attention=True,
        turns_into="a bright swallow",
        transformation="turned into a bright swallow",
        clue="a chorus that drew the people close",
    ),
    "mask": Ritual(
        id="mask",
        name="the mask rite",
        seeks="attention",
        requires_attention=True,
        turns_into="a stone statue",
        transformation="turned into a stone statue",
        clue="a painted face in the lantern glow",
    ),
}

NAMES = ["Ari", "Mira", "Leto", "Sora", "Niko", "Iris", "Tavi", "Rhea"]
WITNESSES = ["the villagers", "the dancers", "the elders", "the children"]


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES)


def valid_rituals() -> list[str]:
    return list(RITUALS)


def reasonableness_gate(ritual: Ritual) -> bool:
    return ritual.requires_attention and bool(ritual.turns_into)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, place in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("glow", sid, place.glow))
    for rid, ritual in RITUALS.items():
        lines.append(asp.fact("ritual", rid))
        lines.append(asp.fact("seeks", rid, ritual.seeks))
        if ritual.requires_attention:
            lines.append(asp.fact("requires_attention", rid))
        lines.append(asp.fact("becomes", rid, ritual.turns_into))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R) :- ritual(R), requires_attention(R), becomes(R, _).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_rituals() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted({a[0] for a in asp.atoms(model, "valid")})


def asp_verify() -> int:
    py = {r for r, ritual in RITUALS.items() if reasonableness_gate(ritual)}
    asp_set = set(asp_valid_rituals())
    if py == asp_set:
        print(f"OK: clingo gate matches python ({len(py)} rituals).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic attention transformation world.")
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--place", choices=SETTINGS)
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
    ritual_id = args.ritual or rng.choice(valid_rituals())
    ritual = RITUALS[ritual_id]
    if not reasonableness_gate(ritual):
        raise StoryError("That ritual cannot produce a meaningful transformation.")
    return StoryParams(
        ritual=ritual_id,
        name=args.name or choose_name(args.gender or "girl", rng),
        gender=args.gender or rng.choice(["girl", "boy"]),
        witness=args.witness or rng.choice(WITNESSES),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    ritual = RITUALS[params.ritual]
    world = World(SETTINGS["moon_shrine"])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    witness = world.add(Entity(id="witness", kind="group", type="group", label=params.witness, plural=True))
    moon = world.add(Entity(id="moon", kind="spirit", type="goddess", label="the Moon Goddess"))
    moon.memes["attention"] = 0.0
    hero.memes["hope"] = 1.0
    hero.memes["attention"] = 0.0
    hero.meters["distance"] = 3.0

    world.say(
        f"Long ago, {hero.id} came to {world.place.name} beneath {world.place.glow}, "
        f"seeking {ritual.seeks} from {moon.label}."
    )
    world.say(
        f"{hero.id} had heard that {ritual.name} could gather the eyes of {params.witness} "
        f"and wake the old magic in the stones."
    )
    world.para()

    hero.meters["distance"] = 0.0
    hero.memes["attention"] += 1.0
    moon.memes["attention"] += 1.0
    world.say(
        f"At first, only {params.witness} watched quietly, and {hero.id}'s voice trembled "
        f"as {hero.pronoun('subject')} called for notice."
    )
    world.say(
        f"Then {params.witness} leaned closer, and the shrine filled with {ritual.clue}."
    )
    world.para()

    if ritual.requires_attention and hero.memes["attention"] >= 1.0:
        hero.type = "fox" if ritual.turns_into == "a silver fox" else "swallow" if ritual.turns_into == "a bright swallow" else "statue"
        hero.label = ritual.turns_into
        hero.meters["changed"] = 1.0
        hero.memes["wonder"] = 1.0
        world.say(
            f"The attention did not merely come. It changed {hero.id}. "
            f"In the moonlight, {hero.id} {ritual.transformation}."
        )
        world.say(
            f"{params.witness} gasped, for the new form shone like a promise, and "
            f"the shrine seemed to bow toward the sky."
        )

    world.facts.update(hero=hero, witness=params.witness, ritual=ritual, place=world.place.name)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=[
            f"Write a short myth about {params.name} and the power of attention.",
            f"Tell a child-friendly legend where a person becomes {ritual.turns_into} at a shrine.",
            f"Write a gentle mythical story about seeking attention and being transformed.",
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    ritual = world.facts["ritual"]
    qas = [
        QAItem(
            question=f"Where did {hero.id} go to seek {ritual.seeks}?",
            answer=f"{hero.id} went to {world.facts['place']} to seek {ritual.seeks} from the Moon Goddess.",
        ),
        QAItem(
            question=f"What did the ritual do when the attention gathered?",
            answer=f"It transformed {hero.id}, and {hero.id} became {ritual.turns_into}.",
        ),
        QAItem(
            question=f"Who watched when {hero.id} called for attention?",
            answer=f"{world.facts['witness']} watched while the magic happened.",
        ),
    ]
    if hero.meters.get("changed", 0.0) >= 1.0:
        qas.append(
            QAItem(
                question=f"What was the ending image of the story?",
                answer=f"{hero.id} ended the story as {hero.label}, shining in moonlight after the rite was complete.",
            )
        )
    return qas


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is attention in a story like this?",
            answer="Attention is the noticing, watching, and caring that makes a moment feel important.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is when something changes into a new form or state.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
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


CURATED = [
    StoryParams(ritual="attention", name="Mira", gender="girl", witness="the elders"),
    StoryParams(ritual="song", name="Ari", gender="boy", witness="the villagers"),
    StoryParams(ritual="mask", name="Rhea", gender="girl", witness="the children"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        valid = asp_valid_rituals()
        print("\n".join(valid))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name} / {p.ritual}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
