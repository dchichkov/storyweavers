#!/usr/bin/env python3
"""
storyworlds/worlds/clumsy_mystic_mum_shopping_mall_sound_effects.py
====================================================================

A small detective-style storyworld set in a shopping mall, seeded by the
words "clumsy", "mystic", and "mum", with sound effects as a narrative
instrument.

Premise:
- A child or parent notices a missing or swapped mall item.
- The "clumsy mystic mum" premise pushes a mysterious mistake into a public
  place full of clatters, chimes, and squeaks.
- A sensible clue trail leads to a reveal, then to a repair.

The simulation models:
- physical meters: dropped, wet, noisy, hidden, found
- emotional memes: worry, curiosity, relief, pride, embarrassment

The story beats:
- setup: a family goes to the mall for a simple errand
- tension: a clumsy magical mishap creates odd sound clues and a missing item
- turn: the detective-minded character follows the sound trail
- resolution: the real cause is found, and order returns with a clean ending image
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "mother", "mum", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def short(self) -> str:
        return self.label or self.id


@dataclass
class Scene:
    place: str
    sound: str
    clue: str
    suspect: str
    fix: str


@dataclass
class StoryParams:
    name: str
    child_type: str
    mum_name: str
    item: str
    scene: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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


SCENES: dict[str, Scene] = {
    "mall": Scene(
        place="the shopping mall",
        sound="ding!",
        clue="a glittery chime from the fountain",
        suspect="the coin kiosk",
        fix="the stray token was returned to the fountain",
    ),
    "food_court": Scene(
        place="the shopping mall food court",
        sound="clink-clink!",
        clue="a spoon tapping under a bench",
        suspect="the snack tray",
        fix="the lost spoon was tucked back beside the bowl",
    ),
    "toy_shop": Scene(
        place="the toy shop in the shopping mall",
        sound="squeak!",
        clue="a rubber duck squeaking behind a shelf",
        suspect="the stuffed toy display",
        fix="the duck was handed back to the shopkeeper",
    ),
}


ITEMS: dict[str, dict[str, str]] = {
    "coin": {"label": "silver coin", "phrase": "a shiny silver coin"},
    "button": {"label": "red button", "phrase": "a bright red button"},
    "key": {"label": "tiny key", "phrase": "a tiny brass key"},
}


GIRL_NAMES = ["Mia", "Nora", "Ada", "Lily", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Theo", "Finn", "Owen"]


ASP_RULES = r"""
% A story is valid when a mall scene has one clue, one suspect, and one fix.
scene(S) :- mall(S).
valid_story(S) :- scene(S), clue(S), suspect(S), fix(S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("mall", sid) for sid in SCENES]
    for sid, scene in SCENES.items():
        lines.append(asp.fact("clue", sid))
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("fix", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {("mall",), ("food_court",), ("toy_shop",)}
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches python stories ({len(asp_set)} scenes).")
        return 0
    print("MISMATCH between clingo and python:")
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style mall storyworld with clumsy mystic mum and sound clues."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--mum")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    scene = args.scene or rng.choice(list(SCENES))
    item = args.item or rng.choice(list(ITEMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mum = args.mum or "Mum"
    return StoryParams(name=name, child_type=gender, mum_name=mum, item=item, scene=scene)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child set in {f["place"]} with a clumsy mystic mum and a mysterious sound.',
        f"Tell a shopping-mall mystery where {f['child']} follows sound clues to find {f['item_phrase']}.",
        f'Write a gentle story that includes the sound "{f["sound"]}" and ends with a solved clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {f['child']} and {f['mum']}, who went to {f['place']} and solved a small mystery together.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The helpful clue was {f['clue']}. It pointed the family toward {f['suspect']} and then to the lost item.",
        ),
        QAItem(
            question=f"What sound kept showing up in the story?",
            answer=f"The story kept using the sound effect {f['sound']}, which made the search feel like a little detective case.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shopping mall?",
            answer="A shopping mall is a big building with many stores and shared walkways where people can shop, eat, and walk around indoors.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a problem or mystery.",
        ),
        QAItem(
            question="Why do stories use sound effects?",
            answer="Stories use sound effects to make scenes feel lively, like footsteps, chimes, or squeaks that help the reader imagine what is happening.",
        ),
    ]


def build_world(params: StoryParams) -> World:
    scene = SCENES[params.scene]
    world = World(scene)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.name))
    mum = world.add(Entity(id="mum", kind="character", type="mother", label=params.mum_name))
    item = ITEMS[params.item]

    world.facts.update(
        child=child.short(),
        mum=mum.short(),
        place=scene.place,
        sound=scene.sound,
        clue=scene.clue,
        suspect=scene.suspect,
        fix=scene.fix,
        item_label=item["label"],
        item_phrase=item["phrase"],
    )

    child.memes["curiosity"] = 1
    mum.memes["embarrassment"] = 1
    mum.memes["mystic"] = 1
    child.memes["worry"] = 0

    world.say(f"{child.short()} and {mum.short()} went to {scene.place} on a busy afternoon.")
    world.say(f"{mum.short()} was clumsy, mystic, and kind, and she muttered, \"Watch the signs.\"")

    world.para()
    world.say(f"Then the whole hallway went {scene.sound}!")
    world.say(f"A small thing was missing, and {child.short()} felt like a detective at once.")
    world.say(f"First they found {scene.clue}, which made them look near {scene.suspect}.")
    child.memes["curiosity"] += 1
    child.memes["worry"] += 1

    world.para()
    world.say(f"{child.short()} followed the sound trail past a shop window and under a bright bench.")
    world.say(f"There, tucked away, was {item['phrase']}.")
    world.say(f"{mum.short()} laughed, then admitted her clumsy spell had nudged it loose.")

    world.para()
    world.say(f"Together they fixed it at once: {scene.fix}.")
    child.memes["worry"] = 0
    child.memes["pride"] = 1
    mum.memes["relief"] = 1
    world.say(f"At the end, {child.short()} listened to the soft mall hum and smiled like a true detective.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) label={e.label!r} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
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
    StoryParams(name="Mia", child_type="girl", mum_name="Mum", item="coin", scene="mall"),
    StoryParams(name="Leo", child_type="boy", mum_name="Mum", item="key", scene="food_court"),
    StoryParams(name="Nora", child_type="girl", mum_name="Mum", item="button", scene="toy_shop"),
]


def valid_choices() -> list[tuple[str, str]]:
    return [(scene, item) for scene in SCENES for item in ITEMS]


def resolve_filtered(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = resolve_params(args, rng)
    return params


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible scenes:", ", ".join(s for (s,) in asp_valid_stories()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_filtered(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
