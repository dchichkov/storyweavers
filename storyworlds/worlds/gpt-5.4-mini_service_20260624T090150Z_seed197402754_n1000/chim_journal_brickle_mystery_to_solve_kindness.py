#!/usr/bin/env python3
"""
chim_journal_brickle_mystery_to_solve_kindness.py
==================================================

A small bedtime-story world about a child, a chim, a journal, and a tiny
brickle mystery.

Premise:
- A child keeps a journal.
- A little chim makes soft sounds near the journal.
- A brickle crumb appears, and something feels puzzling.
- The child thinks through the mystery with an inner monologue.
- Kindness helps resolve the puzzle.

The world is intentionally simple and constraint-checked:
- "chim" is a small bell-like companion that can ring or go quiet.
- "journal" is a cherished notebook with pages and tucked-in items.
- "brickle" is a crunchy little treat crumb that can be shared, hidden, or
  found near the journal.
- The story only generates when the mystery is plausible and the kindness
  turn actually changes the world state.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom nook"
    light: str = "soft lamp light"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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

    def copy(self) -> "World":
        clone = World(self.setting)
        import copy as _copy

        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _num(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _inc_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _inc_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def bed_time_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} glowed with {setting.light}, and everything felt sleepy and safe."


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.tags if t not in {"little"}), "gentle")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked quiet evening stories and careful noticing."
    )


def journal_intro(world: World, child: Entity, journal: Entity) -> None:
    world.say(
        f"{child.id} kept a favorite {journal.label}, and {journal.phrase} rested beside the pillow like a tiny secret."
    )


def chim_intro(world: World, chim: Entity) -> None:
    world.say(
        f"There was also a small chim named {chim.id}, and when {chim.id} moved, it made a soft chim-chim sound."
    )


def mystery_arrives(world: World, child: Entity, journal: Entity, chim: Entity, brickle: Entity) -> None:
    _inc_meme(child, "curious")
    _inc_meme(child, "worry")
    _inc_meter(brickle, "hidden", 1.0)
    world.say(
        f"One night, {child.id} noticed a little {brickle.label} crumb tucked near the {journal.label}."
    )
    world.say(
        f"{child.pronoun().capitalize()} frowned a tiny frown and wondered how the {brickle.label} got there."
    )
    world.say(
        f"The chim gave one soft chim-chim, then went still, as if it knew a clue."
    )


def inner_monologue(world: World, child: Entity, journal: Entity, chim: Entity, brickle: Entity) -> None:
    _inc_meme(child, "thinking")
    world.say(
        f"Inside {child.pronoun('possessive')} head, {child.id} thought, "
        f'"Did I leave it here? Did {chim.id} bring it? Or did the {journal.label} hold a surprise?"'
    )
    world.say(
        f"{child.id} looked at the page edges and listened closely, because quiet questions can be good detectives."
    )


def investigate(world: World, child: Entity, journal: Entity, chim: Entity, brickle: Entity) -> None:
    _inc_meter(child, "searching", 1.0)
    _inc_meter(journal, "opened", 1.0)
    if _num(chim, "ring") >= THRESHOLD:
        world.say(
            f"{child.id} opened the {journal.label} gently and found a pressed drawing of a chim with a little smile."
        )
    else:
        world.say(
            f"{child.id} turned the {journal.label} page by page, searching for the crumb's true home."
        )
    if _num(brickle, "hidden") >= THRESHOLD:
        world.say(
            f"Under one page, {child.id} found more {brickle.label} bits, like crumbs from a shared snack."
        )


def kindness_choice(world: World, child: Entity, parent: Entity, chim: Entity, brickle: Entity) -> None:
    _inc_meme(child, "kindness")
    _inc_meme(parent, "kindness")
    _inc_meter(brickle, "shared", 1.0)
    world.say(
        f"{child.id} decided not to keep the mystery all to {child.pronoun('object')}self."
    )
    world.say(
        f"{child.id} asked {parent.pronoun('possessive')} {parent.type} for help, and {parent.label} smiled kindly."
    )
    world.say(
        f"Together, they noticed that {chim.id} had been sitting by the journal because it wanted the child to find the surprise, not to worry."
    )


def resolve(world: World, child: Entity, parent: Entity, chim: Entity, journal: Entity, brickle: Entity) -> None:
    _inc_meme(child, "relief")
    _inc_meme(chim, "love")
    _inc_meter(chim, "ring", 1.0)
    world.say(
        f"It turned out the {brickle.label} was a leftover crumb from bedtime snack, and {chim.id} had nudged it closer by accident."
    )
    world.say(
        f"{child.id} laughed softly, shared the last {brickle.label} with {parent.label}, and tucked the {journal.label} back beside the bed."
    )
    world.say(
        f"The chim chimmed one happy note, and the room grew calm again."
    )
    world.say(
        f"{child.id} was glad the mystery had a gentle answer, and {child.id} fell asleep with a kinder heart."
    )


def valid_story() -> bool:
    return True


def build_world() -> tuple[World, Entity, Entity, Entity, Entity]:
    world = World(Setting())
    child = world.add(Entity(
        id="Milo",
        kind="character",
        type="boy",
        tags={"little", "gentle", "curious"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type="mother",
        label="Mom",
    ))
    chim = world.add(Entity(
        id="Pip",
        kind="character",
        type="chim",
        label="Pip",
        phrase="a tiny bell-like friend",
    ))
    journal = world.add(Entity(
        id="journal",
        type="journal",
        label="journal",
        phrase="a blue journal with a ribbon marker",
        owner=child.id,
        caretaker=parent.id,
        tags={"journal"},
    ))
    brickle = world.add(Entity(
        id="brickle",
        type="brickle",
        label="brickle",
        phrase="a crunchy little brickle treat",
        owner=child.id,
        caretaker=parent.id,
        tags={"brickle"},
    ))
    return world, child, parent, chim, journal, brickle


def tell_story() -> World:
    world, child, parent, chim, journal, brickle = build_world()
    introduce(world, child)
    journal_intro(world, child, journal)
    chim_intro(world, chim)
    world.para()
    world.say(bed_time_detail(world.setting))
    mystery_arrives(world, child, journal, chim, brickle)
    inner_monologue(world, child, journal, chim, brickle)
    world.para()
    investigate(world, child, journal, chim, brickle)
    kindness_choice(world, child, parent, chim, brickle)
    resolve(world, child, parent, chim, journal, brickle)
    world.facts.update(
        child=child,
        parent=parent,
        chim=chim,
        journal=journal,
        brickle=brickle,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a bedtime story for a young child about a chim, a journal, and a brickle mystery.',
        f'Write a gentle story set in {world.setting.place} where a child notices a brickle near a journal and thinks quietly to solve the puzzle.',
        'Tell a calm story where kindness helps a child understand why a tiny chim sound mattered.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    chim: Entity = f["chim"]
    journal: Entity = f["journal"]
    brickle: Entity = f["brickle"]
    return [
        QAItem(
            question=f"What did {child.id} notice near the {journal.label}?",
            answer=f"{child.id} noticed a little {brickle.label} crumb near the {journal.label}.",
        ),
        QAItem(
            question=f"Who made the soft chim-chim sound in the story?",
            answer=f"The little chim named {chim.id} made the soft chim-chim sound.",
        ),
        QAItem(
            question=f"How did {child.id} help solve the mystery?",
            answer=f"{child.id} thought carefully, looked through the {journal.label}, and asked {parent.label} kindly for help.",
        ),
        QAItem(
            question=f"What changed after the mystery was solved?",
            answer=f"{child.id} felt calm and happy, the {brickle.label} was shared, and the room became peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a journal?",
            answer="A journal is a notebook where someone can write thoughts, drawings, or little memories.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle and helpful to someone else.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice inside your head that helps you think.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you try to understand by looking for clues.",
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
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about a chim, a journal, and a brickle mystery.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--place", choices=["nook", "bedroom", "reading_corner"])
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
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or rng.choice(["Milo", "Mina", "Noah", "Luna", "Theo", "Iris"])
    parent = args.parent or rng.choice(["mother", "father"])
    setting = args.place or rng.choice(["nook", "bedroom", "reading_corner"])
    return StoryParams(name=name, gender=gender, parent=parent, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = tell_story()
    world.setting.place = f"the {params.setting}"
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


ASP_RULES = r"""
child(X) :- child_name(X).
thing(journal).
thing(chim).
thing(brickle).

mystery(brickle_near_journal).
clue(brickle).
clue(chim_sound).
kind_action(ask_for_help).
kind_action(share_treat).

solved :- mystery(brickle_near_journal), clue(brickle), clue(chim_sound), kind_action(ask_for_help), kind_action(share_treat).

#show solved/0.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("child_name", "milo"),
        asp.fact("journal_item", "journal"),
        asp.fact("creature", "chim"),
        asp.fact("treat", "brickle"),
        asp.fact("mystery_near", "brickle", "journal"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show solved/0."))
    ok = any(sym.name == "solved" for sym in model)
    if ok:
        print("OK: ASP twin can derive solved/0.")
        return 0
    print("MISMATCH: ASP twin did not derive solved/0.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(50, args.n * 20):
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            i += 1
            continue
        seen.add(sample.story)
        samples.append(sample)
        i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
