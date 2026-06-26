#!/usr/bin/env python3
"""
storyworlds/worlds/dim_tool_shed_dialogue_quest_magic_mystery.py
=================================================================

A small story world set in a dim tool shed, shaped like a child-friendly
mystery with dialogue, a quest, and a little bit of magic.

Premise:
- A child and a helper go into a dim tool shed to find a missing tool.
- They follow clues, ask questions, and use a small magic light to reveal the
  hiding place.
- The ending proves the quest changed the world: the tool is found, the shed
  feels less scary, and the child leaves braver and happier.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- live simulation drives prose
- inline ASP twin with parity checks
- standalone stdlib script interface
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

DIM_THRESHOLD = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str = "the tool shed"
    dim: bool = True
    affords: set[str] = field(default_factory=lambda: {"search", "seek"})


@dataclass
class Quest:
    goal: str
    clue: str
    ending: str
    keyword: str = "dim"
    tags: set[str] = field(default_factory=set)


@dataclass
class Magic:
    id: str
    label: str
    phrase: str
    effect: str
    reveal: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.shadow: float = 1.0

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.shadow = self.shadow
        return clone


def _r_dim_fear(world: World) -> list[str]:
    out = []
    if world.shadow < DIM_THRESHOLD:
        return out
    for ch in world.characters():
        if ch.memes.get("fear", 0.0) < DIM_THRESHOLD:
            continue
        sig = ("fear", ch.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ch.memes["courage"] = ch.memes.get("courage", 0.0) + 1
        out.append("The dimness made the air feel prickly.")
    return out


def _r_magic_reveal(world: World) -> list[str]:
    out = []
    torch = world.entities.get("lantern")
    clue = world.entities.get("clue")
    if not torch or not clue:
        return out
    if torch.meters.get("glow", 0.0) < DIM_THRESHOLD:
        return out
    if clue.meters.get("hidden", 0.0) < DIM_THRESHOLD:
        return out
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["hidden"] = 0.0
    clue.meters["seen"] = 1.0
    out.append("The little lantern glow reached under the shelf and showed the hidden clue.")
    return out


def _r_found_tool(world: World) -> list[str]:
    out = []
    clue = world.entities.get("clue")
    tool = world.entities.get("tool")
    hero = next((c for c in world.characters() if c.kind == "character" and c.id != "Helper"), None)
    if not clue or not tool or not hero:
        return out
    if clue.meters.get("seen", 0.0) < DIM_THRESHOLD:
        return out
    if tool.meters.get("found", 0.0) >= DIM_THRESHOLD:
        return out
    sig = ("found", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tool.meters["found"] = 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    out.append("That clue led straight to the missing tool.")
    return out


RULES = [_r_dim_fear, _r_magic_reveal, _r_found_tool]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    name: str
    helper: str
    seed: Optional[int] = None


NAMES = ["Mia", "Noah", "Lina", "Eli", "Ada", "Leo", "Nora", "Finn"]
HELPERS = ["mother", "father", "grandparent", "neighbor"]


def tell(params: StoryParams) -> World:
    world = World(Place())
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mia", "Lina", "Ada", "Nora"} else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    tool = world.add(Entity(id="tool", type="wrench", label="wrench", phrase="a small silver wrench", owner=helper.id))
    clue = world.add(Entity(id="clue", type="note", label="note", phrase="a torn note", owner=helper.id))
    lantern = world.add(Entity(id="lantern", type="lantern", label="lantern", phrase="a tiny magic lantern", owner=helper.id))

    clue.meters["hidden"] = 1.0
    lantern.meters["glow"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["fear"] = 1.0
    world.shadow = 1.0

    world.say(
        f"{hero.id} stood in the dim tool shed and listened to the quiet drip of rain on the roof."
    )
    world.say(
        f"{hero.id} had come on a small quest to find the missing {tool.label}, and {helper.label} wanted to help."
    )
    world.para()
    world.say(
        f'"Where did it go?" {hero.id} asked. "{helper.label.capitalize()}, do you know any clue?"'
    )
    world.say(
        f'"Look near the back shelf," {helper.label} said softly. "The dim shed likes to hide small things."'
    )

    world.para()
    world.say(
        f"{hero.id} lifted the tiny magic lantern and whispered, "
        f'"Shine, little light."'
    )
    world.shadow = 0.0
    propagate(world, narrate=True)
    world.say(
        f'"I can see it!" {hero.id} said. The glow had found the torn note, and the note pointed to the old crate.'
    )
    propagate(world, narrate=True)

    world.para()
    if tool.meters.get("found", 0.0) >= DIM_THRESHOLD:
        world.say(
            f"{hero.id} pulled out the wrench, grinned, and held it up like treasure."
        )
        world.say(
            f'"We solved it," {helper.label} said. "A dim shed can feel mysterious, but clues and a little magic make it kinder."'
        )
        world.say(
            f"{hero.id} smiled at the clean little beam of light and walked out of the shed feeling braver than before."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        tool=tool,
        clue=clue,
        lantern=lantern,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        f'Write a short mystery for a young child set in a dim tool shed, where {hero.id} and {helper.label} search for a missing wrench.',
        f"Tell a story with dialogue, a quest, and a little magic lantern that helps {hero.id} solve a mystery in a tool shed.",
        f'Write a gentle mystery where a dim shed feels scary at first, but a clue and magic light help the characters find the missing tool.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, tool, clue, lantern = f["hero"], f["helper"], f["tool"], f["clue"], f["lantern"]
    return [
        QAItem(
            question=f"Where does {hero.id} look for the missing {tool.label}?",
            answer=f"{hero.id} looks for the missing {tool.label} in the dim tool shed with {helper.label}.",
        ),
        QAItem(
            question=f"What is the quest in the story?",
            answer=f"The quest is to find the missing {tool.label}.",
        ),
        QAItem(
            question=f"What helps reveal the clue?",
            answer=f"The tiny magic lantern helps reveal the hidden clue in the dim shed.",
        ),
        QAItem(
            question=f"How does the story end?",
            answer=f"It ends with {hero.id} holding up the found {tool.label} and feeling braver after solving the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tool shed?",
            answer="A tool shed is a small building or room where people keep tools like hammers, nails, and wrenches.",
        ),
        QAItem(
            question="Why can a dim place feel mysterious?",
            answer="A dim place has little light, so it can hide things in shadows and make people wonder what is there.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, often with clues and a goal to reach.",
        ),
        QAItem(
            question="What does magic often do in stories?",
            answer="Magic in stories can reveal, help, or change things in a surprising way.",
        ),
        QAItem(
            question="Why do people use lanterns in dark places?",
            answer="People use lanterns in dark places so they can see better and find things safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "tool_shed"))
    lines.append(asp.fact("dim_place", "tool_shed"))
    lines.append(asp.fact("affords", "tool_shed", "search"))
    lines.append(asp.fact("affords", "tool_shed", "seek"))
    lines.append(asp.fact("quest", "find_wrench"))
    lines.append(asp.fact("magic", "lantern"))
    lines.append(asp.fact("reveals", "lantern", "clue"))
    lines.append(asp.fact("goal", "find_wrench", "tool"))
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P), dim_place(P).
possible_quest(Q) :- quest(Q).
possible_magic(M) :- magic(M).
solves(Q) :- goal(Q, tool), reveals(lantern, clue), place_ok(tool_shed).
#show place_ok/1.
#show possible_quest/1.
#show possible_magic/1.
#show solves/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_result_atoms(name: str) -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(f"#show {name}/1."))
    return sorted(set(asp.atoms(model, name)))


def asp_verify() -> int:
    import asp
    py_ok = {("tool_shed",)}
    asp_ok = set(asp_result_atoms("place_ok"))
    if py_ok != asp_ok:
        print("MISMATCH between Python and ASP place checks")
        print("python:", sorted(py_ok))
        print("asp:", sorted(asp_ok))
        return 1
    print("OK: ASP parity check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A dim tool shed mystery with dialogue, quest, and magic.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    if args.helper == "self":
        raise StoryError("helper cannot be the same as the child")
    return StoryParams(name=name, helper=helper, seed=args.seed)


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
        print(asp_program("#show solves/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show place_ok/1.\n#show possible_quest/1.\n#show possible_magic/1.\n#show solves/1."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", helper="mother"),
            StoryParams(name="Noah", helper="father"),
            StoryParams(name="Lina", helper="grandparent"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
