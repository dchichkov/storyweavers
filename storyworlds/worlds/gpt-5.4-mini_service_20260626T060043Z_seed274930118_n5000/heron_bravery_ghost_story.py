#!/usr/bin/env python3
"""
A tiny storyworld for a brave heron and a gentle ghost.

The source tale inspiration:
- A heron stands alone at dusk near a quiet marsh.
- A shy ghost scares the small fish and makes the water hush.
- The heron feels afraid at first, then gathers bravery.
- The heron speaks kindly, learns the ghost only wants company,
  and helps the ghost glow softly instead of startling everyone.
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
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("brightness", 0.0)
        self.meters.setdefault("stillness", 0.0)
        self.meters.setdefault("wetness", 0.0)
        self.memes.setdefault("fear", 0.0)
        self.memes.setdefault("bravery", 0.0)
        self.memes.setdefault("loneliness", 0.0)
        self.memes.setdefault("kindness", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"heron"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the marsh"
    dusk: bool = True


@dataclass
class World:
    setting: Setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def propagate(world: World) -> None:
    heron = world.get("heron")
    ghost = world.get("ghost")
    lantern = world.get("lantern")

    if ghost.meters["brightness"] >= THRESHOLD and heron.memes["fear"] >= THRESHOLD:
        heron.memes["bravery"] += 1
        heron.memes["fear"] = max(0.0, heron.memes["fear"] - 1)
        world.say("The heron took one slow breath and let its bravery grow bigger than its fear.")

    if heron.memes["kindness"] >= THRESHOLD and ghost.memes["loneliness"] >= THRESHOLD:
        ghost.memes["relief"] += 1
        ghost.memes["loneliness"] = max(0.0, ghost.memes["loneliness"] - 1)
        ghost.meters["brightness"] += 1
        world.say("The ghost glowed softer, as if a heavy blanket had slid off its shoulders.")

    if lantern.meters["brightness"] >= THRESHOLD and ghost.meters["brightness"] >= THRESHOLD:
        ghost.memes["relief"] += 1


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "heron"
    place: str = "the marsh"


SETTINGS = {
    "marsh": Setting(place="the marsh", dusk=True),
    "pond": Setting(place="the pond", dusk=True),
    "riverbank": Setting(place="the riverbank", dusk=True),
}

HERO_NAMES = ["heron", "heron"]


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.name != "heron":
        raise StoryError("This tiny world only tells the story of a heron.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place for this heron story.")


ASP_RULES = r"""
place(marsh).
place(pond).
place(riverbank).
hero(heron).

can_story(P) :- place(P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("hero", "heron")]
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show can_story/1.")
    model = asp.one_model(program)
    got = set(asp.atoms(model, "can_story"))
    expected = {(p,) for p in SETTINGS}
    if got == expected:
        print(f"OK: clingo gate matches Python gate ({len(got)} places).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(got))
    print("  python:", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heron bravery ghost story world.")
    ap.add_argument("--place", choices=SETTINGS)
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
    place = args.place or rng.choice(list(SETTINGS))
    params = StoryParams(seed=None, name="heron", place=place)
    reasonableness_gate(params)
    return params


def _make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    heron = world.add(Entity(
        id="heron",
        kind="character",
        type="heron",
        label="heron",
        phrase="a tall white heron",
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="ghost",
        phrase="a shy marsh ghost",
    ))
    lantern = world.add(Entity(
        id="lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a small lantern",
    ))

    # Setup
    world.say(f"At {world.setting.place} near dusk, a tall white heron stood very still among the reeds.")
    world.say("It listened to the frogs and watched the water turn silver-blue.")
    world.say("Then a shy marsh ghost floated up from the mist and made the cattails tremble.")

    # Tension
    world.para()
    ghost.meters["brightness"] += 1
    ghost.memes["loneliness"] += 1
    heron.memes["fear"] += 1
    world.say("The heron froze, because the ghost looked spooky in the dim light.")
    world.say("The ghost did not mean to frighten anyone; it only wanted a friend.")
    world.say("Still, its chilly glow made the small fish hide under the mud.")

    propagate(world)

    # Turn
    world.para()
    heron.memes["kindness"] += 1
    heron.memes["bravery"] += 1
    lantern.meters["brightness"] += 1
    world.say("The heron gathered its bravery and stepped closer instead of flying away.")
    world.say("It bowed politely and held up a little lantern with a warm, steady shine.")
    world.say('"Hello," the heron said softly. "You do not have to scare the marsh to be noticed."')

    propagate(world)

    # Resolution
    world.para()
    ghost.memes["loneliness"] += 1
    propagate(world)
    world.say("The ghost gave a tiny wobble, then smiled in the lantern light.")
    world.say("It learned to glow gently beside the heron, and the frogs sang again.")
    world.say("By the end, the marsh was calm, the fish had returned, and the heron was no longer afraid.")

    world.facts.update(
        place=params.place,
        heron=heron,
        ghost=ghost,
        lantern=lantern,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short ghost story for a child about a heron who finds bravery at the marsh.',
        f"Tell a gentle dusk story set at {world.setting.place} where a heron helps a lonely ghost.",
        'Write a tiny story where fear turns into bravery and a spooky glow becomes friendly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is the main character in the story?",
            answer="The main character is a heron.",
        ),
        QAItem(
            question="Why did the heron feel scared at first?",
            answer="The heron felt scared because a shy ghost rose up out of the mist and looked spooky in the dim light.",
        ),
        QAItem(
            question="What helped the heron become brave?",
            answer="The heron became brave by taking a slow breath, stepping closer, and holding up a little lantern with warm light.",
        ),
        QAItem(
            question="What changed about the ghost by the end?",
            answer="By the end, the ghost glowed more gently and felt less lonely because the heron spoke kindly to it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a heron?",
            answer="A heron is a long-legged water bird that stands near ponds, marshes, and rivers to look for fish.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is the feeling that helps you do something even when you feel scared.",
        ),
        QAItem(
            question="What is a ghost in a story?",
            answer="In a story, a ghost is a spooky-sounding character that might glow, drift, or whisper in the dark.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:7} ({e.type:7}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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


def asp_valid_places() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/1."))
    return sorted(set(asp.atoms(model, "can_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible places:")
        for (p,) in asp_valid_places():
            print(f"  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(seed=base_seed, name="heron", place=place)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
