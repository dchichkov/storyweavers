#!/usr/bin/env python3
"""
A standalone storyworld for a small mystery on an icy sidewalk.

Premise:
A child finds a bridal flyer fluttering on an icy sidewalk and notices that it
does not belong there. Following the flyer leads to suspense, a conflict over
what it means, and a twist that reveals who left it and why.
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
    held_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    icy: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    tag: str


@dataclass
class StoryParams:
    place: str = "sidewalk"
    clue: str = "flyer"
    object: str = "bridal"
    hero_name: str = "Mina"
    hero_type: str = "girl"
    helper_name: str = "Nora"
    helper_type: str = "woman"
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _narrate_event(world: World, text: str) -> None:
    world.say(text)


def resolve_ice(world: World, actor: Entity) -> None:
    if world.place.icy:
        actor.memes["care"] = actor.memes.get("care", 0.0) + 1


def clue_finds_clue(world: World, hero: Entity, clue: Entity) -> None:
    sig = ("find", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    clue.meters["seen"] = clue.meters.get("seen", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    _narrate_event(
        world,
        f"{hero.id} saw a {clue.label} lying on the icy sidewalk, as if the cold had dropped a secret there."
    )


def clue_stirs_suspense(world: World, hero: Entity, clue: Entity) -> None:
    sig = ("suspense", clue.id)
    if sig in world.fired:
        return
    if clue.meters.get("seen", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["suspense"] = hero.memes.get("suspense", 0.0) + 1
    _narrate_event(
        world,
        f"{hero.id} picked it up carefully. The paper was cold, and the words on it felt important."
    )


def conflict_on_misread(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return
    if clue.meters.get("seen", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1
    _narrate_event(
        world,
        f"{helper.id} frowned and said the flyer looked too strange to trust, which made {hero.id} upset."
    )


def twist_reveal(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    sig = ("twist", clue.id)
    if sig in world.fired:
        return
    if hero.memes.get("conflict", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    clue.meters["explained"] = clue.meters.get("explained", 0.0) + 1
    _narrate_event(
        world,
        f"Then the twist came: the flyer was a bridal notice for the helper's sister, and it had slipped out of her bag."
    )


def resolution(world: World, hero: Entity, helper: Entity, clue: Entity) -> None:
    sig = ("resolve", clue.id)
    if sig in world.fired:
        return
    if clue.meters.get("explained", 0.0) < THRESHOLD:
        return
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    _narrate_event(
        world,
        f"{hero.id} and {helper.id} laughed together, and they carried the bridal flyer home before it could skate away again."
    )


SETTINGS = {
    "sidewalk": Place(name="the icy sidewalk", icy=True, affords={"walk", "search"}),
}

CLUES = {
    "flyer": Clue(
        id="flyer",
        text="a bridal flyer",
        tag="flyer",
    ),
}

HERO_NAMES = ["Mina", "Tessa", "Lina", "Ivy", "Nora", "Zuri"]
HELPER_NAMES = ["Nora", "Aunt June", "Mara", "Ella", "Rina", "Sage"]


ASP_RULES = r"""
clue_seen(C) :- clue(C).
suspense(C) :- clue_seen(C).
conflict(H,C) :- hero(H), clue_seen(C).
twist(C) :- conflict(_,C), bridal(C).
resolved(C) :- twist(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.icy:
            lines.append(asp.fact("icy", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("bridal", cid))
        lines.append(asp.fact("tag", cid, clue.tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_validity() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show clue_seen/1.\n#show suspense/1.\n#show conflict/2.\n#show twist/1.\n#show resolved/1."))
    out = []
    out.extend(("clue_seen", *t) for t in asp.atoms(model, "clue_seen"))
    out.extend(("suspense", *t) for t in asp.atoms(model, "suspense"))
    out.extend(("conflict", *t) for t in asp.atoms(model, "conflict"))
    out.extend(("twist", *t) for t in asp.atoms(model, "twist"))
    out.extend(("resolved", *t) for t in asp.atoms(model, "resolved"))
    return out


def asp_verify() -> int:
    expected = {
        ("clue_seen", "flyer"),
        ("suspense", "flyer"),
        ("conflict", "Mina", "flyer"),
        ("twist", "flyer"),
        ("resolved", "flyer"),
    }
    actual = set(asp_validity())
    if actual == expected:
        print(f"OK: clingo gate matches expected story-state atoms ({len(actual)} atoms).")
        return 0
    print("MISMATCH between clingo and expected atoms:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in expected:", sorted(expected - actual))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about a bridal flyer on an icy sidewalk.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--object", choices=["bridal"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = args.place or "sidewalk"
    clue = args.clue or "flyer"
    obj = args.object or "bridal"
    if place not in SETTINGS:
        raise StoryError("The story needs the icy sidewalk setting.")
    if clue != "flyer" or obj != "bridal":
        raise StoryError("This storyworld is built around a bridal flyer.")
    name = args.name or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    if helper == name:
        helper = "Nora" if name != "Nora" else "Mara"
    return StoryParams(place=place, clue=clue, object=obj, hero_name=name, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    clue = world.add(Entity(id="flyer", type="flyer", label="bridal flyer", phrase="a bridal flyer"))

    world.facts.update(hero=hero, helper=helper, clue=clue, params=params, place=place)

    _narrate_event(
        world,
        f"{hero.id} was walking on the icy sidewalk when something white fluttered near {hero.pronoun('object')} shoes."
    )
    clue_finds_clue(world, hero, clue)
    world.para()
    clue_stirs_suspense(world, hero, clue)
    _narrate_event(
        world,
        f"The flyer said 'bridal' in fancy letters, but no one nearby seemed to know why it was there."
    )
    conflict_on_misread(world, hero, helper, clue)
    world.para()
    twist_reveal(world, hero, helper, clue)
    resolution(world, hero, helper, clue)

    world.facts["done"] = clue.meters.get("explained", 0.0) >= THRESHOLD

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
    hero = f["hero"]
    helper = f["helper"]
    return [
        'Write a short mystery story for a young child about a bridal flyer on an icy sidewalk.',
        f"Tell a suspenseful, child-friendly story where {hero.id} finds a flyer, argues a little with {helper.id}, and learns the truth.",
        "Write a simple story with a twist ending about a paper clue blowing across cold pavement.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    clue: Entity = f["clue"]
    return [
        QAItem(
            question=f"What did {hero.id} find on the sidewalk?",
            answer=f"{hero.id} found {clue.phrase} on the icy sidewalk.",
        ),
        QAItem(
            question=f"Why was the middle part of the story suspenseful?",
            answer=(
                f"It was suspenseful because the flyer looked important, and {hero.id} did not know who had dropped it."
            ),
        ),
        QAItem(
            question=f"What caused the conflict between {hero.id} and {helper.id}?",
            answer=(
                f"The conflict happened when {helper.id} worried that the flyer might be a mistake, but {hero.id} wanted to keep searching."
            ),
        ),
        QAItem(
            question="What was the twist?",
            answer="The twist was that the bridal flyer belonged to the helper's sister and had slipped out of a bag.",
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended happily when {hero.id} and {helper.id} laughed together and carried the flyer home."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bridal mean?",
            answer="Bridal means something is connected to a wedding, like a bride or wedding plans.",
        ),
        QAItem(
            question="Why is an icy sidewalk slippery?",
            answer="An icy sidewalk is slippery because the frozen water makes the ground smooth and hard to grip.",
        ),
        QAItem(
            question="What is a flyer?",
            answer="A flyer is a small paper notice that tells people about something, like an event or a sale.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_verify_mode() -> int:
    return asp_verify()


def asp_facts_for_show() -> str:
    return asp_facts()


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show resolved/1."))
    return sorted(set(asp.atoms(model, "resolved")))


def aspirational_storyworld() -> str:
    return "mystery"


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
        print(asp_program("#show clue_seen/1.\n#show suspense/1.\n#show conflict/2.\n#show twist/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify_mode())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show clue_seen/1.\n#show suspense/1.\n#show conflict/2.\n#show twist/1.\n#show resolved/1."))
        atoms = []
        for pred in ["clue_seen", "suspense", "conflict", "twist", "resolved"]:
            atoms.extend((pred, *t) for t in asp.atoms(model, pred))
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(hero_name="Mina", helper_name="Nora")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
