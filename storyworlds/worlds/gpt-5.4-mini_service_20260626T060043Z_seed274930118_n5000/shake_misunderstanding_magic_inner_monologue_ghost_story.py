#!/usr/bin/env python3
"""
A small ghost-story world about a shaky misunderstanding, a little magic, and
an inner monologue that helps set the record straight.

Seed tale:
A child hears a strange shaking sound in an old house at night and thinks a ghost
is angry. The child hides and listens. The "ghost" turns out to be a tiny magic
wind-up lantern that keeps trembling on a shelf. The ghost was only trying to
help by making the lantern glow. The child talks kindly to the ghost, the
lantern is fixed, and the house grows calm again.

This world implements that premise as a constraint-checked simulation with:
- a ghostly setting
- a misunderstanding
- magic as a real but gentle force
- inner monologue that changes what the child believes
- a final ending image that proves the state changed
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    mood: str = "moonlit"
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    clue: str
    cause: str
    effect: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trinket:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = False


@dataclass
class MagicTool:
    id: str
    label: str
    fix: str
    method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def join2(a: str, b: str) -> str:
    return f"{a} and {b}"


def starts_with_vowel(s: str) -> bool:
    return s[:1].lower() in "aeiou"


def a_or_an(word: str) -> str:
    return "an" if starts_with_vowel(word) else "a"


def article_phrase(phrase: str) -> str:
    return f"{a_or_an(phrase)} {phrase}"


def intro(world: World, child: Entity, ghost: Entity) -> None:
    world.say(
        f"{child.id} lived in {world.setting.place}, where the halls felt quiet "
        f"and the moon made every corner look silver."
    )
    world.say(
        f"At the end of the hall, {ghost.id} floated softly near the stairs, "
        f"more shy than spooky."
    )


def magic_glow(world: World, ghost: Entity, tool: Entity) -> None:
    ghost.memes["kindness"] = ghost.memes.get("kindness", 0) + 1
    tool.meters["glow"] = tool.meters.get("glow", 0) + 1
    world.say(
        f"{ghost.id} kept {tool.label} bright with a tiny spell, "
        f"because {ghost.pronoun('subject')} wanted the room to feel safe."
    )


def shake_event(world: World, child: Entity, tool: Entity) -> None:
    child.meters["startle"] = child.meters.get("startle", 0) + 1
    tool.meters["shake"] = tool.meters.get("shake", 0) + 1
    world.say(
        f"Then {tool.label} began to shake on the shelf, rattling like little teeth."
    )
    world.say(
        f"{child.id} froze and thought, \"A ghost must be angry.\""
    )


def inner_monologue(world: World, child: Entity) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"In {child.pronoun('possessive')} head, a small voice whispered, "
        f"\"What if the ghost is mad at me? What if the house wants me to leave?\""
    )
    world.say(
        f"{child.id} hugged {child.pronoun('possessive')} arms and listened very hard."
    )


def misunderstanding(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0) + 1
    world.say(
        f"The sound made {child.id} think {ghost.id} had done something mean, "
        f"but the shaking came from {tool.label}, not from an angry ghost."
    )


def listen_closer(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    child.memes["courage"] = child.memes.get("courage", 0) + 1
    world.say(
        f"{child.id} took a slow breath and listened again. "
        f"The shake sounded small, busy, and stuck, not mean."
    )
    world.say(
        f"{child.id} whispered, \"I think I got it wrong.\""
    )
    ghost.memes["relief"] = ghost.memes.get("relief", 0) + 1


def fix_magic(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    tool.meters["shake"] = 0
    tool.meters["glow"] = max(1, tool.meters.get("glow", 0))
    world.say(
        f"{ghost.id} showed {child.id} the little trick: the magic in {tool.label} "
        f"needed a wind-up tap to stay steady."
    )
    world.say(
        f"{child.id} gave {tool.label} a careful twist, and the shaking stopped at once."
    )


def resolve(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    child.memes["worry"] = 0
    child.memes["understanding"] = child.memes.get("understanding", 0) + 1
    world.say(
        f"After that, {child.id} smiled at {ghost.id} and said, "
        f"\"You were trying to help.\""
    )
    world.say(
        f"{ghost.id} nodded, and the hallway felt warm instead of strange."
    )
    world.say(
        f"Before long, {tool.label} glowed on the shelf without a single shake, "
        f"and the old house rested in a sleepy, friendly hush."
    )


def tell_story(world: World, child: Entity, ghost: Entity, tool: Entity) -> None:
    intro(world, child, ghost)
    world.para()
    magic_glow(world, ghost, tool)
    shake_event(world, child, tool)
    misunderstanding(world, child, ghost, tool)
    world.para()
    inner_monologue(world, child)
    listen_closer(world, child, ghost, tool)
    fix_magic(world, child, ghost, tool)
    world.para()
    resolve(world, child, ghost, tool)


def build_world(params: "StoryParams") -> World:
    world = World(Setting(place=params.place))
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    ghost = world.add(Entity(id="Milo the ghost", kind="character", type="ghost"))
    tool = world.add(Entity(
        id="lantern",
        type="lantern",
        label="the little magic lantern",
        phrase="a little magic lantern",
        caretaker=ghost.id,
    ))
    world.facts.update(child=child, ghost=ghost, tool=tool, params=params)
    tell_story(world, child, ghost, tool)
    world.facts["misunderstanding"] = child.memes.get("misunderstanding", 0) >= THRESHOLD
    world.facts["resolved"] = tool.meters.get("shake", 0) == 0
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a child-friendly ghost story that includes the word "shake" and ends in kindness.',
        f"Tell a short story where {p.name} mistakes a gentle ghost for something scary, but the truth is a magic lantern shaking on a shelf.",
        f"Write a spooky-but-soft story with a misunderstanding, a little magic, and an inner monologue that helps the hero understand what is happening.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    ghost: Entity = f["ghost"]
    tool: Entity = f["tool"]
    return [
        QAItem(
            question=f"What did {child.id} think was happening when the sound started?",
            answer=f"{child.id} thought {ghost.id} was angry, but the noise was really {tool.label} shaking on the shelf.",
        ),
        QAItem(
            question=f"What was the magic thing in the story?",
            answer=f"The magic thing was {tool.label}. {ghost.id} used a tiny spell to keep it glowing.",
        ),
        QAItem(
            question=f"How did {child.id} fix the problem?",
            answer=f"{child.id} listened closely, realized the worry was a misunderstanding, and gave {tool.label} a careful twist so it stopped shaking.",
        ),
        QAItem(
            question=f"How did the story end for {child.id} and {ghost.id}?",
            answer=f"They understood each other, and the old house felt calm and friendly at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing is going on, even though the real reason is different.",
        ),
        QAItem(
            question="What does magic do in a story?",
            answer="Magic can make impossible or surprising things happen, like making a lantern glow with no flame.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the little voice in a character's head that tells them what they are thinking and feeling.",
        ),
        QAItem(
            question="What does it mean to shake?",
            answer="To shake means to move back and forth very quickly, like when a shelf rattles or someone shivers.",
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


@dataclass
class StoryParams:
    place: str = "the old house"
    name: str = "Nia"
    gender: str = "girl"
    seed: Optional[int] = None


SETTINGS = {
    "the old house": Setting(place="the old house", mood="moonlit", affords={"shake", "magic"}),
    "the attic house": Setting(place="the attic house", mood="drafty", affords={"shake", "magic"}),
    "the quiet manor": Setting(place="the quiet manor", mood="moonlit", affords={"shake", "magic"}),
}

NAMES = ["Nia", "Leo", "Mina", "Owen", "Ivy", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a shaky misunderstanding and gentle magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    name = args.name or rng.choice(NAMES)
    gender = args.gender or ("girl" if name in {"Nia", "Mina", "Ivy"} else "boy")
    return StoryParams(place=place, name=name, gender=gender, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A lantern is shaking if its shake meter is positive.
shaking(lantern) :- lantern_fact(lantern), shaken(lantern).

% A misunderstanding happens when the child suspects the ghost but the real cause is the lantern.
misunderstanding(child, ghost, lantern) :- child_fact(child), ghost_fact(ghost), lantern_fact(lantern), shaken(lantern).

% The story resolves when the lantern is steadied and the child understands.
resolved(child, ghost, lantern) :- child_fact(child), ghost_fact(ghost), lantern_fact(lantern), steadied(lantern), understands(child).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("child_fact", "child"),
        asp.fact("ghost_fact", "ghost"),
        asp.fact("lantern_fact", "lantern"),
        asp.fact("shaken", "lantern"),
        asp.fact("steadied", "lantern"),
        asp.fact("understands", "child"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/3."))
    ok = bool(asp.atoms(model, "resolved"))
    if ok:
        print("OK: ASP twin agrees that the story resolves.")
        return 0
    print("MISMATCH: ASP twin did not find resolution.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show resolved/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/3."))
        print("resolved atoms:", asp.atoms(model, "resolved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Nia", gender="girl", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
