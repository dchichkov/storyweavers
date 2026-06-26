#!/usr/bin/env python3
"""
Storyworld: Bonnie, the lorry, and the little mystery.

A small slice-of-life story domain built from the seed words:
bonnie, lorry, regress

Features:
- Mystery to Solve
- Happy Ending
- Rhyme
- Slice of Life style
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
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Mystery:
    id: str
    title: str
    clue: str
    culprit: str
    solved_with: str
    resolution: str
    rhyme_end: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "garden": Setting(place="the garden", detail="The garden was warm, with little paths between the beans and herbs."),
    "kitchen": Setting(place="the kitchen", detail="The kitchen was bright, with a low table and a bowl of apples nearby."),
    "porch": Setting(place="the porch", detail="The porch was tidy, with a bench, boots, and a soft mat by the door."),
}

MYSTERIES = {
    "missing_lorry": Mystery(
        id="missing_lorry",
        title="The Missing Lorry",
        clue="a line of tiny mud prints",
        culprit="the garden snail",
        solved_with="follow the prints slowly",
        resolution="Bonnie found the lorry behind a pot of basil, tucked beside a shiny snail trail.",
        rhyme_end="The lorry was found, and the day felt right; Bonnie smiled in the warm afternoon light.",
        tags={"lorry", "mud", "snail"},
    ),
    "stuck_wheel": Mystery(
        id="stuck_wheel",
        title="The Stuck Wheel",
        clue="a squeak from one bent wheel",
        culprit="a pebble in the axle",
        solved_with="lift the lorry and wiggle the wheel free",
        resolution="Bonnie popped the pebble out, and the little lorry rolled again without a wobble.",
        rhyme_end="The wheel spun round, so happy and bright; Bonnie laughed when the lorry felt just right.",
        tags={"lorry", "wheel", "pebble"},
    ),
    "missing_bow": Mystery(
        id="missing_bow",
        title="The Missing Bow",
        clue="a ribbon left on the chair",
        culprit="the sidekick's pocket",
        solved_with="check the pockets and ask kindly",
        resolution="The bow was in the pocket, and Bonnie tied it back on with careful fingers.",
        rhyme_end="The bow was back, and the room felt sweet; Bonnie's happy little mystery was complete.",
        tags={"ribbon", "pocket", "happy"},
    ),
}

SIDEKICKS = ["cat", "grandma", "brother", "neighbor", "friend"]
NAMES = ["Bonnie", "Mina", "Pippa", "Ruby", "Holly"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid in MYSTERIES:
            combos.append((sid, mid))
    return combos


def _is_reasonable(setting: str, mystery: str) -> bool:
    return setting in SETTINGS and mystery in MYSTERIES


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: the setting '{setting}' and mystery '{mystery}' do not form a reasonable tiny mystery.)"


def build_story(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["curious"] = 1
    hero.memes["hope"] = 1
    hero.memes["worry"] = 1

    world.say(f"Bonnie was a little {hero.type} who liked neat corners, warm tea, and tiny adventures.")
    world.say(f"In {world.setting.place}, she had a favorite lorry with a red roof and round blue wheels.")
    world.say(f"One day, something odd happened: {mystery.title.lower()}.")

    world.para()
    if mystery.id == "missing_lorry":
        world.say(f"Bonnie looked on the shelf, under the chair, and beside the flower pots, but the lorry was gone.")
        world.say(f"Then she noticed {mystery.clue}.")
        world.say(f"\"That clue could help us {mystery.solved_with},\" said her {sidekick.type}.")
    elif mystery.id == "stuck_wheel":
        world.say(f"Bonnie tried to roll the lorry, but one wheel gave a tiny squeak and stopped.")
        world.say(f"She saw {mystery.clue}.")
        world.say(f"\"Let's {mystery.solved_with},\" said her {sidekick.type}.")
    else:
        world.say(f"Bonnie tied a ribbon to the lorry, but later she could not find the bow.")
        world.say(f"She noticed {mystery.clue}.")
        world.say(f"\"We should {mystery.solved_with},\" said her {sidekick.type}.")

    world.say(f"Bonnie followed the clue with careful steps, because small mysteries need slow feet and a patient heart.")
    world.say(f"That is how they learned the truth: {mystery.culprit}.")
    world.say(mystery.resolution)

    world.para()
    hero.memes["worry"] = 0
    hero.memes["joy"] = 1
    world.say(f"Bonnie gave a happy sigh and put everything back in order.")
    world.say(f"{mystery.rhyme_end}")
    world.say("And that was the end of the little mystery, with a smile, a lorry, and a calm bright day.")

    world.facts.update(hero=hero, sidekick=sidekick, mystery=mystery)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, M) :- setting(S), mystery(M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mystery stories for Bonnie and a lorry.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", default="Bonnie")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    if args.setting and args.mystery and not _is_reasonable(args.setting, args.mystery):
        raise StoryError(explain_rejection(args.setting, args.mystery))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mystery=mystery, name=name, sidekick=sidekick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life mystery story about Bonnie and a lorry in {world.setting.place}.',
        f"Tell a gentle story where Bonnie notices {f['mystery'].clue} and solves the small problem with help from a {f['sidekick'].type}.",
        f'Write a child-friendly story that includes the words "bonnie", "lorry", and "regress" in a natural way, and ends happily.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    mystery: Mystery = f["mystery"]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"The story was about Bonnie and her {sidekick.type}, who helped with a small mystery in {world.setting.place}.",
        ),
        QAItem(
            question="What was Bonnie trying to find or fix?",
            answer=f"Bonnie was trying to solve {mystery.title.lower()} about her lorry.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the problem solved and the lorry back where it belonged.",
        ),
        QAItem(
            question="Why is the word regress in the story?",
            answer="Bonnie had to go back over the clues and regress to the first place she had looked, which helped her solve the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a lorry?",
            answer="A lorry is a truck or big wheeled vehicle that can carry things from one place to another.",
        ),
        QAItem(
            question="What does it mean to regress?",
            answer="To regress means to go back to an earlier place, step, or state. In a mystery, going back over clues can help solve it.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling thing that needs clues and careful thinking to solve.",
        ),
    ]


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
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="character", type=params.sidekick, label=params.sidekick))
    lorry = world.add(Entity(id="lorry", kind="thing", type="lorry", label="lorry", owner=hero.id, location=setting.place))
    world.facts.update(hero=hero, sidekick=sidekick, lorry=lorry, mystery=mystery, setting=setting)
    build_story(world, hero, sidekick, mystery)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(setting="garden", mystery="missing_lorry", name="Bonnie", sidekick="cat"),
    StoryParams(setting="kitchen", mystery="stuck_wheel", name="Bonnie", sidekick="grandma"),
    StoryParams(setting="porch", mystery="missing_bow", name="Bonnie", sidekick="friend"),
]


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery) combos:")
        for setting, mystery in combos:
            print(f"  {setting:8} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
