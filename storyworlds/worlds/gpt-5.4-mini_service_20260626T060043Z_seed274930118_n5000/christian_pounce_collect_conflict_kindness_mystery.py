#!/usr/bin/env python3
"""
A small Storyweavers world: Christian, a pounce of suspicion, a collection of clues,
and a mystery that can only be solved with kindness.

The seed for this world suggests a child-friendly mystery tone with the words
"christian", "pounce", and "collect", plus the narrative instruments Conflict
and Kindness. The implementation below turns that into a tiny simulation:
a child notices something missing, gathers clues, clashes with a skeptic, and
then solves the case by being gentle, observant, and helpful.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    clues: list[str]
    hidey_places: list[str]


@dataclass
class Mystery:
    missing: str
    suspect: str
    clue_kind: str
    answer_place: str
    trail: str
    pounce_line: str
    collect_line: str


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


@dataclass
class StoryParams:
    place: str
    mystery: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(
        place="the garden",
        clues=["muddy pawprints", "a bent petal", "a shiny button"],
        hidey_places=["under the bench", "behind the watering can", "by the fence"],
    ),
    "classroom": Setting(
        place="the classroom",
        clues=["tiny chalk dust", "a torn ribbon", "a crumpled note"],
        hidey_places=["inside the art box", "under a desk", "behind a book stack"],
    ),
    "library": Setting(
        place="the library",
        clues=["a paper scrap", "a soft thump", "a glittery bookmark"],
        hidey_places=["under the reading rug", "between big books", "behind the globe"],
    ),
}

MYSTERIES = {
    "badge": Mystery(
        missing="library badge",
        suspect="the wind",
        clue_kind="paper",
        answer_place="behind the globe",
        trail="a paper scrap fluttered near the shelves",
        pounce_line="Christian pounced toward the clue like a tiny detective cat",
        collect_line="Christian carefully collected the clues in a neat little pile",
    ),
    "key": Mystery(
        missing="classroom key",
        suspect="a rushed helper",
        clue_kind="metal",
        answer_place="inside the art box",
        trail="something small clinked near the paint jars",
        pounce_line="Christian pounced beside the paint table when the clink sounded",
        collect_line="Christian collected every clue without knocking anything over",
    ),
    "seed_pouch": Mystery(
        missing="seed pouch",
        suspect="a busy squirrel",
        clue_kind="leaf",
        answer_place="under the bench",
        trail="little leaves were scattered in a wiggly line",
        pounce_line="Christian pounced over the grass as soon as the leaf trail appeared",
        collect_line="Christian collected the leaves, one by one, so none would blow away",
    ),
}

NAMES = ["Christian"]
HELPER_NAMES = ["Maya", "Noah", "Ava", "Ben"]
ADJECTIVES = ["curious", "gentle", "careful", "brave"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mystery world about Christian, clues, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in SETTINGS for mystery in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid mystery matches the given options.")
    place, mystery = rng.choice(combos)
    return StoryParams(place=place, mystery=mystery)


class Narrative:
    def __init__(self, world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
        self.world = world
        self.hero = hero
        self.helper = helper
        self.mystery = mystery

    def setup(self) -> None:
        self.hero.memes["curiosity"] = 1
        self.world.say(
            f"Christian was a curious child who liked to notice small things before anyone else did."
        )
        self.world.say(
            f"One morning at {self.world.setting.place}, something important was missing: the {self.mystery.missing}."
        )
        self.world.say(
            f"Christian loved to collect clues, and today the first clue was {self.mystery.trail}."
        )

    def conflict(self) -> None:
        self.hero.memes["conflict"] = 1
        self.helper.memes["doubt"] = 1
        self.world.para()
        self.world.say(self.mystery.pounce_line + ".")
        self.world.say(
            f"Then {self.helper.id} frowned and said, 'Maybe you are chasing the wrong thing.'"
        )
        self.world.say(
            f"Christian felt a little Conflict in {self.hero.pronoun('possessive')} chest, but {self.hero.pronoun()} did not stop."
        )

    def kindness(self) -> None:
        self.world.para()
        self.hero.memes["kindness"] = 1
        self.helper.memes["kindness"] = 1
        self.world.say(
            f"Instead of arguing, Christian used Kindness and asked {self.helper.id} to help collect the clues."
        )
        self.world.say(self.mystery.collect_line + ".")
        self.world.say(
            f"That gentle choice made {self.helper.id} soften right away, because kindness can make a tense room feel safe."
        )

    def reveal(self) -> None:
        self.world.para()
        clue_place = self.mystery.answer_place
        if clue_place not in self.world.setting.hidey_places:
            clue_place = self.world.setting.hidey_places[0]
        self.world.say(
            f"At last, the trail led to {clue_place}, where the missing {self.mystery.missing} was waiting."
        )
        self.world.say(
            f"It had never been stolen after all; it had only slipped away while everyone was busy."
        )
        self.world.say(
            f"Christian smiled, handed it back, and the whole place felt calmer than before."
        )

    def finish(self) -> None:
        self.world.para()
        self.world.say(
            f"By the end, Christian had collected the clues, solved the mystery, and turned Conflict into Kindness."
        )
        self.world.say(
            f"The last thing anyone saw was Christian carrying the {self.mystery.missing} home in a careful little bundle."
        )


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id="Christian", kind="character", type="boy"))
    helper = world.add(Entity(id="Helper", kind="character", type="girl"))
    mystery = MYSTERIES[params.mystery]
    helper.type = random.choice(["girl", "boy"])
    helper.id = random.choice(HELPER_NAMES)

    narrative = Narrative(world, hero, helper, mystery)
    narrative.setup()
    narrative.conflict()
    narrative.kindness()
    narrative.reveal()
    narrative.finish()

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        place=world.setting.place,
        solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle mystery story about Christian who likes to collect clues and solve a missing-object puzzle.',
        f"Tell a child-friendly story set at {f['place']} where Christian follows a clue trail, feels Conflict, and ends with Kindness.",
        f'Write a short mystery that uses the words "Christian", "pounce", and "collect" in a natural way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    mystery = f["mystery"]
    return [
        QAItem(
            question="Who was the story about?",
            answer="The story was about Christian, a curious child who liked to solve little mysteries.",
        ),
        QAItem(
            question=f"What did Christian do when the clue appeared at {f['place']}?",
            answer=f"Christian pounced toward the clue and carefully collected it with the rest of the trail.",
        ),
        QAItem(
            question=f"Why did the mood change from Conflict to Kindness?",
            answer=(
                f"The mood changed because Christian stopped arguing, asked {helper.id} for help, "
                f"and chose Kindness instead of suspicion."
            ),
        ),
        QAItem(
            question=f"What was missing in the mystery?",
            answer=f"The missing thing was the {mystery.missing}.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=(
                f"Christian followed the clues all the way to {mystery.answer_place} and found the missing {mystery.missing} there."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="What does it mean to pounce?",
            answer="To pounce means to jump quickly toward something, often because you noticed it suddenly.",
        ),
        QAItem(
            question="What does it mean to collect something?",
            answer="To collect something means to gather it together and keep it in one place.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:10} kind={e.kind} type={e.type} "
            f"memes={dict(e.memes)} meters={dict(e.meters)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- case(M).
valid(P, M) :- place(P), mystery(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for mystery in MYSTERIES:
        lines.append(asp.fact("case", mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in Python:", sorted(py - ac))
    print("only in ASP:", sorted(ac - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    world = World(setting)
    world = tell(world, params)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for mystery in MYSTERIES:
                params = StoryParams(place=place, mystery=mystery, seed=base_seed)
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
