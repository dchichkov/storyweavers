#!/usr/bin/env python3
"""
A standalone storyworld for a small Space Adventure tale set in a tidal pool:
a scout crew finds a garland, greed tempts one crewmate, a trawler stirs up
trouble, and an inner monologue helps choose caution over conflict.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "captain"}:
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


@dataclass
class StoryParams:
    name: str
    role: str
    partner: str
    mood: str
    seed: Optional[int] = None


ROLES = {
    "pilot": "pilot",
    "navigator": "navigator",
    "scout": "scout",
}
PARTNERS = {
    "captain": "captain",
    "mechanic": "mechanic",
    "friend": "friend",
}
MOODS = ["curious", "bold", "restless", "careful"]
NAMES = ["Nova", "Mira", "Orin", "Jax", "Lyra", "Pip", "Tala", "Rin"]


ASP_RULES = r"""
#show valid/1.
#show valid_story/3.

valid(P) :- place(P), activity(a_garland), prize(g_garland).
valid_story(P,A,G) :- valid(P), activity(A), guard(G).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "tidal_pool"),
        asp.fact("activity", "a_garland"),
        asp.fact("prize", "g_garland"),
        asp.fact("guard", "caution"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld in a tidal pool.")
    ap.add_argument("--name")
    ap.add_argument("--role", choices=sorted(ROLES))
    ap.add_argument("--partner", choices=sorted(PARTNERS))
    ap.add_argument("--mood", choices=MOODS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("tidal_pool", "garland", "caution")]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(sorted(ROLES))
    partner = args.partner or rng.choice(sorted(PARTNERS))
    mood = args.mood or rng.choice(MOODS)
    return StoryParams(name=name, role=role, partner=partner, mood=mood)


def build_world(params: StoryParams) -> World:
    world = World(place="tidal pool")
    scout = world.add(Entity(id=params.name, kind="character", type="pilot", label=params.name))
    partner = world.add(Entity(id="Partner", kind="character", type=params.partner, label=params.partner))
    garland = world.add(Entity(
        id="garland",
        type="garland",
        label="garland",
        phrase="a bright garland woven from silver seaweed",
        owner=scout.id,
        caretaker=partner.id,
        worn_by=scout.id,
    ))
    trawler = world.add(Entity(
        id="trawler",
        type="trawler",
        label="trawler",
        phrase="a rumbling trawler with a net full of glittering scraps",
    ))
    world.facts.update(params=params, scout=scout, partner=partner, garland=garland, trawler=trawler)
    return world


def tell(world: World) -> None:
    f = world.facts
    scout: Entity = f["scout"]
    partner: Entity = f["partner"]
    garland: Entity = f["garland"]
    trawler: Entity = f["trawler"]
    mood = f["params"].mood

    world.say(
        f"In the tidal pool, {scout.id} was a {mood} little scout who loved the hush of alien water "
        f"and the shimmer of starfish between the rocks."
    )
    world.say(
        f"Today {scout.id} found {garland.phrase}, and {scout.pronoun()} felt as if the tide itself had picked "
        f"{garland.it()} for a crown."
    )
    world.para()
    world.say(
        f"Out beyond the foam, {trawler.phrase} growled near the reef, and its wake shook shells loose from the stones."
    )
    world.say(
        f"{scout.id} wanted to keep {garland.it()} for {scout.pronoun('object')}self. "
        f"Greed whispered that one small treasure could not matter in such a big sea."
    )
    world.say(
        f'But {scout.id} had an inner monologue that sounded like a tiny ship computer: '
        f'"Caution first. Treasures shared in a tidal pool last longer than treasures hidden from friends."'
    )
    world.para()
    world.say(
        f"{partner.id} pointed at the trawler and warned, \"That boat stirs up the water. If we chase the shiny bits, "
        f"we could lose the garland and bump into the rocks.\""
    )
    world.say(
        f"{scout.id} looked at the widening swirls, then at {partner.pronoun('object')}, and felt the conflict "
        f"between greedy wanting and careful wanting."
    )
    world.say(
        f"At last {scout.id} tied the garland around a safe shell post and helped {partner.id} guide a frightened crab "
        f"away from the trawler's wake."
    )
    world.say(
        f"When the water settled, the garland still shone, the crab was safe, and {scout.id} understood that caution "
        f"was a braver kind of treasure."
    )


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        "Write a short Space Adventure story about a tidal pool, a garland, and a choice between greed and caution.",
        f"Tell a child-friendly space story where {p.name} wants to keep a garland but hears an inner monologue about being careful.",
        "Write a story with a trawler, conflict, and a gentle warning that ends with a safer choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    scout: Entity = f["scout"]
    qa = [
        QAItem(
            question=f"What did {p.name} find in the tidal pool?",
            answer=f"{p.name} found a bright garland woven from silver seaweed.",
        ),
        QAItem(
            question="What feeling tried to tempt the scout into the wrong choice?",
            answer="Greed tried to tempt the scout into keeping the garland all to themself.",
        ),
        QAItem(
            question="What helped the scout make a safer choice?",
            answer="The scout listened to an inner monologue and chose caution instead of greed.",
        ),
        QAItem(
            question="What caused the conflict near the end?",
            answer="The trawler's noisy wake stirred up the water and made the choice feel urgent.",
        ),
        QAItem(
            question=f"What did {scout.id} do with the garland at the end?",
            answer="The scout tied the garland to a safe shell post so it would stay safe in the tidal pool.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trawler?",
            answer="A trawler is a fishing boat that pulls a net through the water to catch fish or collect things.",
        ),
        QAItem(
            question="What is a tidal pool?",
            answer="A tidal pool is a small pool of seawater left behind among rocks when the tide goes out.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking about danger before acting.",
        ),
        QAItem(
            question="What is greed?",
            answer="Greed means wanting to keep too much for yourself, even when sharing would be better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid/1.\n#show valid_story/3.")
    model = asp.one_model(program)
    atoms = asp.atoms(model, "valid")
    if atoms and atoms[0] == ("tidal_pool",):
        print("OK: ASP gate is present.")
        return 0
    print("MISMATCH: ASP gate did not produce expected facts.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1.\n#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story shape:\n  tidal_pool garland caution")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name=n, role="pilot", partner="captain", mood="careful")) for n in NAMES[:3]]
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
