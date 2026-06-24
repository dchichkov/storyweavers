#!/usr/bin/env python3
"""
storyworlds/worlds/fraternity_meow_keen_kindness_foreshadowing_lesson_learned.py
==================================================================================

A small adventure storyworld about a keen child, a meowing kitten, and a
friendly fraternity house where kindness, foreshadowing, and a lesson learned
all matter.

Seed tale inspiration:
---
A keen child follows a faint meow to a fraternity porch, where a tiny kitten has
hidden under a chair. The child notices clues ahead of time, helps the kitten,
and learns that kindness can turn a small mystery into a happy rescue.

World shape:
- A child and a kitten explore one compact place.
- A problem is foreshadowed by a missing item and a worrying sound.
- The child chooses kindness, which changes both the physical state and the
  emotional state of the kitten, the helper, and the family nearby.
- The ending proves what changed: the kitten is safe, the missing thing is found,
  and the lesson is remembered.

The story stays grounded in typed entities with physical meters and emotional
memes, and all prose is driven by the simulated world state.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fraternity porch"
    detail: str = "The porch boards were warm, and the steps led up to a cozy house."


@dataclass
class StoryParams:
    place: str = "fraternity"
    name: str = "Mina"
    gender: str = "girl"
    helper: str = "father"
    trait: str = "keen"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _m(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _e(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def reset_meme(entity: Entity, key: str) -> None:
    entity.memes[key] = 0.0


def build_setting() -> Setting:
    return Setting()


def foreshadow(world: World, child: Entity, kitten: Entity, helper: Entity) -> None:
    world.say(
        f"{child.id} was a {child.trait if hasattr(child, 'trait') else 'keen'} little {child.type} "
        f"who loved adventure. {child.pronoun().capitalize()} had a keen eye for clues, "
        f"and that afternoon {child.pronoun()} heard a soft meow from the fraternity porch."
    )
    world.say(world.setting.detail)
    world.say(
        f"Near the steps, {child.id} noticed a ribbon on the floor and a tiny pawprint in dust. "
        f"That was a small foreshadowing clue: something furry had been nearby for a while."
    )
    add_meme(child, "curiosity", 1)
    add_meme(child, "keen", 1)
    add_meme(kitten, "worry", 1)


def search(world: World, child: Entity, kitten: Entity, helper: Entity) -> None:
    child.meters["searching"] = 1
    world.para()
    world.say(
        f"{child.id} followed the meow past a chair and toward the porch bench. "
        f"{child.pronoun().capitalize()} listened carefully, because the sound was faint but steady."
    )
    world.say(
        f"{helper.id} stayed close and pointed to the ribbon. 'If we look gently, we may find who needs help,' "
        f"{helper.pronoun().capitalize()} said."
    )
    add_meme(helper, "hope", 1)
    add_meme(child, "resolve", 1)


def discover(world: World, child: Entity, kitten: Entity) -> None:
    kitten.location = "under the porch bench"
    world.say(
        f"Under the porch bench, {child.id} found a tiny kitten with bright eyes. "
        f"It was stuck behind a fallen basket and could not climb out on its own."
    )
    add_meter(kitten, "stuck", 1)
    add_meme(kitten, "fear", 1)
    add_meme(child, "sympathy", 1)


def kindness_action(world: World, child: Entity, helper: Entity, kitten: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} could have reached quickly, but {child.pronoun()} chose kindness instead. "
        f"{child.pronoun().capitalize()} knelt down, spoke softly, and slid the basket aside without scaring the kitten."
    )
    add_meme(child, "kindness", 1)
    add_meme(helper, "pride", 1)
    add_meter(kitten, "safe", 1)
    add_meter(kitten, "stuck", -1)


def rescue(world: World, child: Entity, helper: Entity, kitten: Entity) -> None:
    if _m(kitten, "safe") < THRESHOLD:
        return
    kitten.carried_by = child.id
    kitten.location = "in the child's arms"
    kitten.memes["fear"] = 0.0
    kitten.memes["joy"] = 1.0
    world.say(
        f"The kitten stepped free at last. It gave a tiny meow, then pressed its paws into {child.pronoun('possessive')} hands."
    )
    world.say(
        f"{helper.id} smiled and said that the child had been brave in the gentlest way."
    )


def lesson_learned(world: World, child: Entity, helper: Entity, kitten: Entity) -> None:
    world.para()
    child.memes["lesson_learned"] = 1.0
    world.say(
        f"At the end, {child.id} learned a lesson learned by heart: kindness can be the strongest kind of help. "
        f"{child.pronoun().capitalize()} carried the kitten back to the porch steps, and the little meow changed into a happy purr."
    )
    world.say(
        f"The fraternity porch felt brighter than before, because the missing kitten was safe and everyone knew why the clue had mattered."
    )


def tell(params: StoryParams) -> World:
    world = World(build_setting())
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    child.trait = params.trait  # type: ignore[attr-defined]
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label="the helper"))
    kitten = world.add(Entity(id="KeenMeow", kind="character", type="cat", label="the kitten"))
    kitten.location = "somewhere near the fraternity"
    kitten.memes["worry"] = 1.0

    foreshadow(world, child, kitten, helper)
    search(world, child, kitten, helper)
    discover(world, child, kitten)
    kindness_action(world, child, helper, kitten)
    rescue(world, child, helper, kitten)
    lesson_learned(world, child, helper, kitten)

    world.facts.update(
        child=child,
        helper=helper,
        kitten=kitten,
        params=params,
        foreshadowed=True,
        kindness=True,
        lesson=True,
    )
    return world


SETTINGS = {"fraternity": build_setting()}
TRAITS = ["keen", "gentle", "brave", "curious", "helpful"]
GIRL_NAMES = ["Mina", "Lena", "Tara", "Nina", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Theo", "Finn"]


KNOWLEDGE = {
    "cat": [
        (
            "What does a cat say?",
            "A cat often says meow, which is a soft sound cats make to talk to people or ask for help.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means being gentle, helpful, and caring about how another creature feels.",
        )
    ],
    "fraternity": [
        (
            "What is a fraternity?",
            "A fraternity is a group of people who belong to the same club or organization and often share a house or meeting place.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is something important you understand after what happened, so you can do better next time.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing?",
            "Foreshadowing is a small clue at the start of a story that hints something important may happen later.",
        )
    ],
    "keen": [
        (
            "What does keen mean?",
            "Keen can mean sharp and careful, like noticing little clues very quickly.",
        )
    ],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [("fraternity", "meow", "keen")]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: fraternity, meow, keen.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.place != "fraternity":
        raise StoryError("This small adventure only takes place at the fraternity.")
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place="fraternity", name=name, gender=gender, helper=helper, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    return [
        'Write a short adventure story that includes the words "fraternity", "meow", and "keen".',
        f"Tell a gentle rescue story about {c.id}, a keen child, who hears a meow at the fraternity and chooses kindness.",
        "Write a child-friendly story with foreshadowing, a small mystery, and a lesson learned at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    kitten = f["kitten"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Who heard the meow at the fraternity?",
            answer=f"{child.id} heard the meow first and followed it to the fraternity porch.",
        ),
        QAItem(
            question="What clue foreshadowed the kitten's problem?",
            answer="A ribbon on the floor and a tiny pawprint in dust foreshadowed that something furry needed help.",
        ),
        QAItem(
            question="How did the child help the kitten?",
            answer=f"{child.id} chose kindness, moved the basket gently, and helped the kitten get free without scaring it.",
        ),
        QAItem(
            question="What lesson learned ended the story?",
            answer="The lesson learned was that kindness can be the strongest kind of help.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["fraternity", "cat", "kindness", "foreshadowing", "lesson", "keen"]:
        for q, a in KNOWLEDGE.get(tag, []):
            out.append(QAItem(question=q, answer=a))
    return out


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
has_theme(fraternity).
has_theme(meow).
has_theme(keen).

kindness_story :- has_theme(fraternity), has_theme(meow), has_theme(keen).
lesson_learned_story :- kindness_story.

#show kindness_story/0.
#show lesson_learned_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("theme", "fraternity"), asp.fact("theme", "meow"), asp.fact("theme", "keen")]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show kindness_story/0."))
    return [tuple()] if asp.atoms(model, "kindness_story") else []


def asp_verify() -> int:
    py = bool(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show kindness_story/0."))
    cl = bool(asp.atoms(model, "kindness_story"))
    if py == cl:
        print("OK: ASP parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


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
        print(asp_program("#show lesson_learned_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("1 compatible story combo: fraternity / meow / keen")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="fraternity", name="Mina", gender="girl", helper="father", trait="keen")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
            seed = base_seed + i
            i += 1
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
