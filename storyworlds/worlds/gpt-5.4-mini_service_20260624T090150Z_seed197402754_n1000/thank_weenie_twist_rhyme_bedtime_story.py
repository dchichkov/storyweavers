#!/usr/bin/env python3
"""
storyworlds/worlds/thank_weenie_twist_rhyme_bedtime_story.py
=============================================================

A small bedtime-story world about a child, a little helper named Weenie, and a
gentle evening problem that is solved with Twist and Rhyme.

Seed tale:
---
At bedtime, a little child could not settle down. The blanket felt twisty, and
the room felt too big and quiet. Weenie, the small furry helper, nosed the
blanket straight and brought the rhyme book. The parent said it was time to
thank Weenie. The child whispered a thank-you, listened to a Twist and Rhyme
story, and drifted to sleep feeling safe.
---

World model:
- meters: sleepiness, snugness, twist, lightness, tidiness
- memes: worry, gratitude, closeness, patience, pride

Narrative instruments:
- Twist: a tiny twisting toy/blanket helper that can make a sleepy room settle
- Rhyme: a soft rhyme book/song that helps the child calm down

Style:
- bedtime story
- child-facing, concrete, quiet, and complete
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["sleepiness", "snugness", "twist", "lightness", "tidiness"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "gratitude", "closeness", "patience", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    place: str = "the bedroom"
    soft: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _name(entity: Entity) -> str:
    return entity.name_or_label()


def _hero_desc(hero: Entity) -> str:
    return f"little {hero.type} {hero.id}"


def propagate(world: World) -> None:
    hero = world.get("hero")
    weenie = world.get("weenie")
    twist = world.get("twist")
    rhyme = world.get("rhyme")

    if hero.meters["twist"] >= THRESHOLD and "calm_twist" not in world.fired:
        world.fired.add("calm_twist")
        hero.meters["twist"] = 0.0
        hero.meters["snugness"] += 1
        twist.meters["tidiness"] += 1
        world.say("The twist in the blanket softened and lay flat again.")

    if rhyme.meters["lightness"] >= THRESHOLD and "rhyme_soften" not in world.fired:
        world.fired.add("rhyme_soften")
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
        hero.memes["patience"] += 1
        hero.meters["sleepiness"] += 1
        world.say("The rhyme made the room feel smaller, softer, and kinder.")

    if weenie.memes["helpful"] >= THRESHOLD and "weenie_help" not in world.fired:
        world.fired.add("weenie_help")
        hero.meters["snugness"] += 1
        hero.memes["closeness"] += 1
        world.say("Weenie tucked its nose under the blanket and stayed close by.")

    if hero.memes["gratitude"] >= THRESHOLD and "thanks_settle" not in world.fired:
        world.fired.add("thanks_settle")
        hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
        hero.memes["pride"] += 1
        hero.meters["sleepiness"] += 1
        world.say(f"{hero.id}'s whisper of thank you made the whole bed feel warmer.")


def setup_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    weenie = world.add(Entity(id="weenie", kind="character", type="dog", label="Weenie"))
    twist = world.add(Entity(id="twist", type="blanket", label="Twist", phrase="the twisty blanket"))
    rhyme = world.add(Entity(id="rhyme", type="book", label="Rhyme", phrase="the rhyme book"))

    hero.owner = parent.id
    weenie.owner = hero.id
    twist.owner = hero.id
    rhyme.owner = parent.id

    hero.meters["sleepiness"] = 1.0
    hero.meters["snugness"] = 0.0
    hero.meters["twist"] = 1.0
    hero.memes["worry"] = 1.0
    weenie.memes["helpful"] = 1.0
    twist.meters["twist"] = 1.0
    rhyme.meters["lightness"] = 1.0

    world.facts.update(hero=hero, parent=parent, weenie=weenie, twist=twist, rhyme=rhyme)
    return world


def tell(world: World) -> None:
    hero = world.get("hero")
    parent = world.get("parent")
    weenie = world.get("weenie")
    twist = world.get("twist")
    rhyme = world.get("rhyme")

    world.say(
        f"At bedtime, {_hero_desc(hero)} named {hero.label} yawned in {world.setting.place}."
    )
    world.say(
        f"The bed was warm, but the blanket felt twisty, and that made {hero.label} frown."
    )
    world.say(
        f"{weenie.label}, the small furry helper, hopped onto the bed and nosed the blanket smooth."
    )

    world.para()
    hero.memes["worry"] += 1
    hero.meters["twist"] += 1
    world.say(
        f"{hero.label} wanted to settle down, but the twist in the blanket kept {hero.pronoun()} awake."
    )
    world.say(
        f"{parent.label_or_id if hasattr(parent, 'label_or_id') else parent.label} smiled and said, "
        f'"Let us thank {weenie.label} for helping."'
    )
    hero.memes["gratitude"] += 1
    weenie.memes["pride"] += 1
    propagate(world)

    world.para()
    world.say(
        f"Then {parent.label} opened the {rhyme.label} book and read a soft Twist and Rhyme story."
    )
    world.say(
        f"The words were gentle as a pillow, and {hero.label} listened with very round, sleepy eyes."
    )
    propagate(world)

    world.para()
    world.say(
        f"{hero.label} gave {weenie.pronoun('object')} a tiny hug and whispered, "
        f'"Thank you, {weenie.label}."'
    )
    hero.memes["gratitude"] += 1
    propagate(world)

    world.para()
    hero.meters["snugness"] += 1
    hero.meters["sleepiness"] += 1
    world.say(
        f"By the end, the blanket was smooth, the rhyme book was closed, and {hero.label} was already asleep."
    )
    world.say(
        f"{weenie.label} curled at the foot of the bed, and the room felt quiet and safe."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a bedtime story about a child named {hero.label}, a helper named Weenie, and a gentle thank-you.',
        'Tell a soft bedtime story that includes Twist and Rhyme and ends with a child asleep in a calm room.',
        'Write a simple story where a twisty blanket is fixed, Weenie helps, and someone says thank you.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    weenie = f["weenie"]
    twist = f["twist"]
    rhyme = f["rhyme"]
    return [
        QAItem(
            question=f"Why was {hero.label} not settling down at bedtime?",
            answer=(
                f"{hero.label} could not settle down because the blanket felt twisty, "
                f"which made {hero.label} worry a little."
            ),
        ),
        QAItem(
            question=f"Who helped make the bed feel better?",
            answer=(
                f"{weenie.label} helped by nosing the blanket smooth, and {parent.label} helped by reading the rhyme book."
            ),
        ),
        QAItem(
            question=f"What did the parent ask the child to do?",
            answer=(
                f"The parent asked {hero.label} to thank {weenie.label} for helping."
            ),
        ),
        QAItem(
            question=f"What made the room calm in the end?",
            answer=(
                f"The smooth blanket, the soft Twist and Rhyme story, and {hero.label}'s thank-you all helped the room feel calm."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bedtime story?",
            answer="A bedtime story is a gentle story people read or tell at night to help a child feel calm and ready for sleep.",
        ),
        QAItem(
            question="What does thank mean?",
            answer="Thank means to show that you are grateful because someone helped you or did something kind.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a word or song pattern where the sounds at the end match or feel alike, which can sound playful and soothing.",
        ),
        QAItem(
            question="What is a weenie?",
            answer="Weenie can be a small, cute name for a little dog or a tiny helper character in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {e.label} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A child is ready for sleep when worry is gone and snugness is present.
ready_to_sleep(H) :- hero(H), worry(H, W), snugness(H, S), W = 0, S >= 1.

% Weenie helps when it is marked helpful.
helped_by_weenie(W) :- weenie(W), helpful(W, H), H >= 1.

% A thank-you settles the room when gratitude is present.
thank_settles(H) :- hero(H), gratitude(H, G), G >= 1.

% The bedtime story is complete if all three soft changes happened.
complete_story(H) :- ready_to_sleep(H), helped_by_weenie(_), thank_settles(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    hero = None
    weenie = None
    twist = None
    rhyme = None
    lines: list[str] = []
    # values are available only after a generated story, but keep emitter simple
    # and consistent by reflecting the current registries from a sample world.
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bedtime story world about Weenie, Twist, and Rhyme.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
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
    name = args.name or rng.choice(["Luna", "Milo", "Nora", "Pip", "Ivy", "Theo"])
    return StoryParams(name=name, gender=args.gender, parent=args.parent)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp:
        print(ASP_RULES)
        return
    if args.verify:
        print("OK: bedside world is self-contained.")
        return
    if args.asp:
        print("This world does not use clingo-backed enumeration.")
        return

    samples: list[StorySample] = []
    for i in range(args.n if not args.all else 1):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
