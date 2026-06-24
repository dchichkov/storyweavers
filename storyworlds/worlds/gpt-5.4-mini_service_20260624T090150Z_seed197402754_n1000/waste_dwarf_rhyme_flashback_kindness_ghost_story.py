#!/usr/bin/env python3
"""
A tiny ghost-story world about a dwarf, waste, a rhyme, a flashback, and a
kindness that helps a haunted place feel gentle again.

The seed image:
---
A small dwarf lives beside an old house where the sink leaks dark waste into a
stone drain. Every night, a pale ghost hums a rhyme that sounds like a warning.
The dwarf remembers, in a flashback, how the house once laughed before the waste
spilled there. Instead of running away, the dwarf cleans the mess, speaks
kindly to the ghost, and the rhyme changes into a soft goodnight.

World idea:
- The physical problem is waste spreading from a broken drain.
- The emotional problem is fear of the ghost.
- The turn is a flashback that explains the ghost's sadness.
- The resolution is kindness: the dwarf helps, the ghost softens, and the house
  becomes calm again.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dwarf", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    detail: str = "a crooked kitchen and a stone drain"


@dataclass
class StoryParams:
    place: str = "the old house"
    name: str = "Milo"
    trait: str = "brave"
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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about waste, a dwarf, and kindness.")
    ap.add_argument("--place", default="the old house")
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def _noun(name: str) -> str:
    return name[0].upper() + name[1:]


def _story_rhyme() -> str:
    return "The sink went drip and the shadows went swish."


def _flashback_line() -> str:
    return "In a flashback, the dwarf remembered the house before the waste, when warm lanterns glowed and no one had to hide."


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    dwarf = world.add(Entity(id=params.name, kind="character", type="dwarf", label=params.name, traits=[params.trait]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the ghost"))
    waste = world.add(Entity(id="waste", type="waste", label="waste", meters={"spread": 1.0, "smell": 1.0}))
    house = world.add(Entity(id="house", type="place", label=params.place, meters={"quiet": 1.0}, memes={"sadness": 1.0}))

    world.say(f"{_noun(dwarf.id)} was a little {params.trait} dwarf who lived in {params.place}.")
    world.say(f"At night, a pale ghost drifted by the door, and {_story_rhyme()}")
    world.say(f"Inside the old house, a broken drain let waste gather in the stone sink.")

    world.para()
    dwarf.memes["fear"] = 1.0
    ghost.memes["loneliness"] = 1.0
    waste.meters["spread"] += 1.0
    world.say(f"{dwarf.id} felt scared, but {dwarf.pronoun('possessive')} small hands still picked up a bucket and a rag.")
    world.say(_flashback_line())
    world.say("The memory made the ghost look less spooky and more sad.")

    world.para()
    dwarf.memes["kindness"] = 1.0
    ghost.memes["kindness"] = 1.0
    waste.meters["spread"] = 0.0
    waste.meters["cleaned"] = 1.0
    house.memes["sadness"] = 0.0
    house.meters["quiet"] = 0.0
    world.say(f"{dwarf.id} cleaned the waste carefully so it would not stink up the rooms.")
    world.say(f"Then {dwarf.id} spoke kindly to the ghost and said, “You do not have to haunt the house alone.”")
    world.say(f"The ghost’s eyes brightened, and the rhyme changed: “Goodnight, good light, and rest till morning bright.”")
    world.say(f"At the end, {params.name} and the ghost stood together beside a clean sink, and {params.place} felt gentle again.")

    world.facts.update(
        dwarf=dwarf,
        ghost=ghost,
        waste=waste,
        house=house,
        place=params.place,
        trait=params.trait,
        rhyme=_story_rhyme(),
        flashback=True,
        kindness=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about a dwarf in {f["place"]} where waste causes a problem.',
        f"Tell a gentle story with a rhyme, a flashback, and kindness that helps a dwarf and a ghost feel better.",
        f'Write a spooky-but-kind story using the words "waste" and "dwarf".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dwarf: Entity = f["dwarf"]
    ghost: Entity = f["ghost"]
    return [
        QAItem(
            question=f"Who lived in {f['place']} and tried to fix the waste problem?",
            answer=f"A little {f['trait']} dwarf named {dwarf.id} lived there, and {dwarf.id} cleaned the waste with a bucket and a rag.",
        ),
        QAItem(
            question="What did the dwarf remember in the flashback?",
            answer="The dwarf remembered the house before the waste, when it felt warm and happy and did not need hiding.",
        ),
        QAItem(
            question="How did the dwarf help the ghost?",
            answer="The dwarf spoke kindly to the ghost, and that kindness helped the ghost feel less lonely.",
        ),
        QAItem(
            question="What happened to the rhyme at the end?",
            answer="The spooky rhyme turned into a soft goodnight rhyme because the house became calm and the ghost felt better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is waste?",
            answer="Waste is unwanted dirty stuff that people clean up so it does not make a place smell bad or feel messy.",
        ),
        QAItem(
            question="What is a dwarf in a fairy tale?",
            answer="A dwarf is usually a small storybook person who can be brave, busy, and very helpful.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring to someone, especially when they feel sad or scared.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, which can make a song or poem easy to remember.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory in a story that shows something from before the present moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A story is reasonable when a dwarf exists, waste is present, and kindness resolves fear.
story_ok :- dwarf(D), waste(W), ghost(G), kindness(D,G), flashback(D), rhyme(G).

resolved :- story_ok, cleaned(waste), soothed(ghost).

#show story_ok/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("dwarf", "dwarf"),
            asp.fact("ghost", "ghost"),
            asp.fact("waste", "waste"),
            asp.fact("flashback", "flashback"),
            asp.fact("kindness", "kindness"),
            asp.fact("rhyme", "rhyme"),
            asp.fact("cleaned", "waste"),
            asp.fact("soothed", "ghost"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show story_ok/0.\n#show resolved/0."))
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    want = {("story_ok", 0), ("resolved", 0)}
    if atoms == want:
        print("OK: ASP program yields the expected story markers.")
        return 0
    print(f"Mismatch: got {sorted(atoms)}, expected {sorted(want)}")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(["Milo", "Ned", "Oren", "Pip"])
    trait = args.trait or rng.choice(["brave", "gentle", "curious", "steady"])
    return StoryParams(place=args.place, name=name, trait=trait)


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show story_ok/0.\n#show resolved/0."))
        return
    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP unavailable: {exc}")
        model = asp.one_model(asp_program("#show story_ok/0.\n#show resolved/0."))
        print("ASP atoms:", sorted(f"{sym.name}/{len(sym.arguments)}" for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
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
