#!/usr/bin/env python3
"""
A small storyworld for a ghost-story-like tale set on a riverbank, centered on a
quilt, dialogue, transformation, and a moral value turn.
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
    kind: str
    label: str
    type: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    transformed_from: Optional[str] = None

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    water: bool = True
    reeds: bool = True
    moonlit: bool = True


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)


PLACES = {
    "riverbank": Place(id="riverbank", label="the riverbank", water=True, reeds=True, moonlit=True),
}

CHILD_NAMES = ["Mina", "Iris", "Noa", "Pip", "Lina", "Tess", "Owen", "Bram"]
GHOST_NAMES = ["Ash", "Murmur", "Willow", "Belt", "Silk", "Hush"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story storyworld: quilt, dialogue, transformation, moral value.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
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
    place = args.place or "riverbank"
    if place not in PLACES:
        raise StoryError("This storyworld only knows the riverbank.")

    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)

    if child_name == ghost_name:
        raise StoryError("The child and the ghost need different names.")
    return StoryParams(place=place, child_name=child_name, child_type=child_type, ghost_name=ghost_name)


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "riverbank":
        raise StoryError("The ghost story here must be set at the riverbank.")


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(PLACES[params.place])

    child = world.add(Entity(id="child", kind="child", label=params.child_name, type=params.child_type))
    ghost = world.add(Entity(id="ghost", kind="ghost", label=params.ghost_name))
    quilt = world.add(Entity(id="quilt", kind="thing", label="quilt", owner=child.id))
    quilt.meters["folded"] = 1
    quilt.meters["warm"] = 0
    quilt.meters["tattered"] = 0
    child.memes["fear"] = 1
    child.memes["kindness"] = 0
    ghost.memes["lonely"] = 1
    ghost.memes["hope"] = 0

    world.say(f"{child.label} came to {world.place.label} at dusk, carrying a small quilt.")
    world.say(f"The water was dark and still, and the reeds whispered like someone trying not to cry.")
    world.say(f"Then a pale shape rose from the mist. It was {ghost.label}, a ghost with a voice like a breeze.")
    world.say(f'"Why do you hold that quilt so tight?" {ghost.label} asked.')

    world.para()
    world.say(f'"Because it was my grandmother’s," {child.label} said. "{child.pronoun("subject").capitalize()} said it kept our home warm."')
    world.say(f'"I only wanted to borrow its memory," {ghost.label} replied. "{ghost.pronoun("subject").capitalize()} forgot how to feel warm."')
    child.memes["fear"] += 1
    child.memes["curiosity"] = 1
    ghost.memes["hope"] += 1

    world.para()
    world.say(f"{child.label} looked at the quilt, then at the ghost, and remembered a small moral truth: keeping one treasure safe does not mean refusing kindness.")
    world.say(f'"You may not take it," {child.label} said, "but you may sit with me under it."')
    quilt.meters["folded"] = 0
    quilt.meters["warm"] = 1
    ghost.memes["lonely"] = 0
    ghost.memes["hope"] += 2
    child.memes["fear"] = 0
    child.memes["kindness"] += 2

    world.say(f"The ghost drifted lower, and together they spread the quilt over both their shoulders.")
    world.say(f"The mist changed softly around them. {ghost.label} grew brighter, as if the moon had found a new place to rest.")
    world.say(f"By the time the river lapped the stones, the ghost had transformed from a lonely shiver into a gentle, smiling light.")
    world.say(f"{child.label} went home with the quilt still safe, and {child.pronoun('subject')} carried a new value too: kindness can share warmth without giving away what is loved.")

    world.facts.update(
        child=child,
        ghost=ghost,
        quilt=quilt,
        place=world.place,
        moral="kindness can share warmth without giving away what is loved",
        transformed=True,
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    ghost = world.facts["ghost"]
    return [
        'Write a gentle ghost story for children about a quilt at a riverbank.',
        f'Write a story where {child.label} meets {ghost.label}, they speak kindly, and something changes from eerie to warm.',
        'Tell a short tale that includes dialogue, a transformation, and a moral lesson about kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    ghost: Entity = world.facts["ghost"]
    qa = [
        QAItem(
            question=f"Who came to the riverbank with the quilt?",
            answer=f"{child.label} came to the riverbank carrying the quilt.",
        ),
        QAItem(
            question=f"What did {ghost.label} want when {ghost.pronoun('subject')} saw the quilt?",
            answer=f"{ghost.label} wanted to borrow its memory because {ghost.pronoun('subject')} felt lonely and wished to feel warm.",
        ),
        QAItem(
            question=f"How did the story end for the ghost?",
            answer=f"The ghost transformed from a lonely shiver into a gentle, smiling light.",
        ),
        QAItem(
            question="What moral value did the child learn?",
            answer=f"{world.facts['moral'].capitalize()}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quilt?",
            answer="A quilt is a warm cover made of stitched pieces of cloth.",
        ),
        QAItem(
            question="What is a riverbank?",
            answer="A riverbank is the land beside a river.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means changing from one state or form into another.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea about how to be good, fair, or kind.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.transformed_from:
            bits.append(f"transformed_from={e.transformed_from}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:6}) {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
child_event(quilt_story).
transformation(ghost_to_light) :- ghost_event, kindness.
moral_value(kindness) :- speaks_kindly, shares_warmth.
compatible_story(riverbank, quilt, ghost_story) :- child_event(quilt_story), transformation(ghost_to_light), moral_value(kindness).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "riverbank"),
        asp.fact("story_element", "quilt"),
        asp.fact("genre", "ghost_story"),
        asp.fact("feature", "dialogue"),
        asp.fact("feature", "transformation"),
        asp.fact("feature", "moral_value"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    clingo_set = set(asp.atoms(model, "compatible_story"))
    python_set = {("riverbank", "quilt", "ghost_story")}
    if clingo_set == python_set:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  ASP:", sorted(clingo_set))
    print("  Python:", sorted(python_set))
    return 1


def asp_compatible_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


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
    StoryParams(place="riverbank", child_name="Mina", child_type="girl", ghost_name="Hush"),
    StoryParams(place="riverbank", child_name="Owen", child_type="boy", ghost_name="Willow"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "riverbank"
    if place != "riverbank":
        raise StoryError("This world only supports the riverbank setting.")
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    if child_name == ghost_name:
        raise StoryError("The child and the ghost must be different names.")
    return StoryParams(place=place, child_name=child_name, child_type=child_type, ghost_name=ghost_name)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_compatible_stories()
        print(f"{len(combos)} compatible story pattern(s):")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
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
