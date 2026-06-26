#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/installment_peter_statue_bravery_magic_teamwork_rhyming.py
==============================================================================================================

A standalone story world for a rhyming TinyStories-style tale about Peter,
an installment, a statue, bravery, magic, and teamwork.

The story model keeps track of:
- physical meters: distance, weight, shine, crack, lift, glow
- emotional memes: courage, worry, joy, trust, pride

Premise:
Peter must bring a missing installment to a silent statue in the square.
The statue needs the right magical piece to wake the song inside it.

Tension:
The path is high, the stone is heavy, and Peter is scared to fail alone.

Turn:
Peter and a helper use brave hearts, a bit of magic, and teamwork.

Resolution:
The statue glows, the installment clicks into place, and the square feels
bright and safe again.
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the square"
    setting_word: str = "square"
    afford_magic: bool = True
    afford_teamwork: bool = True


@dataclass
class Artifact:
    name: str
    phrase: str
    fit: str
    glow_needed: float
    can_be_moved: bool = True


@dataclass
class Help:
    name: str
    label: str
    action: str
    lift_bonus: float
    magic_bonus: float
    teamwork_bonus: float


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.done: set[str] = set()

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

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.done = set(self.done)
        w.paragraphs = [[]]
        return w


SETTING = Setting()

ARTIFACT = Artifact(
    name="installment",
    phrase="a shining installment",
    fit="slot",
    glow_needed=1.0,
    can_be_moved=True,
)

HELPERS = {
    "bird": Help(
        name="bird",
        label="a small bird",
        action="flutter beside",
        lift_bonus=0.2,
        magic_bonus=0.0,
        teamwork_bonus=0.3,
    ),
    "lamp": Help(
        name="lamp",
        label="a lantern",
        action="cast a warm gleam on",
        lift_bonus=0.0,
        magic_bonus=0.7,
        teamwork_bonus=0.0,
    ),
    "friend": Help(
        name="friend",
        label="a kind friend",
        action="steady",
        lift_bonus=0.5,
        magic_bonus=0.0,
        teamwork_bonus=0.8,
    ),
}

ASP_RULES = r"""
% A story is valid when Peter can reach the statue, the installment fits,
% and the helpers together provide enough lift and glow.
need_magic(story) :- artifact(installment), statue(statue), fit(installment, slot).
can_finish(story) :- bravery(peter), teamwork(peter), magic(peter),
                     reaches(peter, statue), need_magic(story).
"""


@dataclass
class StoryParams:
    place: str = "square"
    helper: str = "friend"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: Peter, a statue, and a magical installment."
    )
    ap.add_argument("--place", choices=["square"], default="square")
    ap.add_argument("--helper", choices=sorted(HELPERS), default=None)
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
    helper = args.helper or rng.choice(list(HELPERS))
    return StoryParams(place=args.place, helper=helper)


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    peter = world.add(Entity(id="peter", kind="character", type="boy", label="Peter"))
    statue = world.add(Entity(id="statue", kind="thing", type="thing", label="statue"))
    helper = world.add(Entity(
        id=params.helper,
        kind="character" if params.helper == "friend" else "thing",
        type="friend" if params.helper == "friend" else "thing",
        label=HELPERS[params.helper].label,
    ))
    installment = world.add(Entity(
        id="installment",
        kind="thing",
        type="thing",
        label="installment",
        phrase=ARTIFACT.phrase,
        owner="statue",
        carried_by="peter",
        meters={"shine": 0.0, "fit": 0.0},
    ))

    peter.memes.update({"worry": 0.0, "courage": 1.0, "joy": 0.0, "trust": 0.0, "pride": 0.0})
    statue.meters.update({"crack": 1.0, "glow": 0.0, "weight": 2.0})
    helper.memes.update({"teamwork": 1.0})

    world.say(
        "In the square, by a stone statue bright, "
        "Peter found an installment tucked out of sight."
    )
    world.say(
        "The statue was quiet, with cracks in its seam, "
        "and Peter could tell it had lost its sweet dream."
    )
    world.say(
        "He held the small piece and took a deep breath, "
        "then whispered, 'I can be brave. I can do this, yes!'"
    )

    world.para()
    world.say(
        "The stair was steep, and the stone felt grand, "
        "so Peter asked kindly for a helping hand."
    )

    # state-driven conflict: helper increases lift and glow
    peter.memes["worry"] += 1.0
    peter.memes["courage"] += 1.0
    helper.memes["teamwork"] += 1.0
    installment.meters["shine"] += 1.0
    statue.meters["glow"] += 0.3

    if params.helper == "friend":
        world.say(
            "His friend came close with a smile so wide, "
            "and said, 'We'll move it together. I'll stay by your side.'"
        )
    elif params.helper == "bird":
        world.say(
            "A bird fluttered near with a soft little cheer, "
            "as if magic itself had come glimmering near."
        )
    else:
        world.say(
            "A lantern shone warm with a gentle gold gleam, "
            "and Peter felt hope like a bright little beam."
        )

    world.say(
        "With teamwork and magic, the path did not bite, "
        "for one small brave step can make trouble feel light."
    )

    # resolution
    statue.meters["glow"] += 1.0
    statue.meters["crack"] = max(0.0, statue.meters["crack"] - 1.0)
    installment.meters["fit"] = 1.0
    peter.memes["joy"] += 1.0
    peter.memes["pride"] += 1.0
    peter.memes["trust"] += 1.0

    world.para()
    world.say(
        "The installment clicked in with a tiny clear chime, "
        "and the statue woke up just right on time."
    )
    world.say(
        "It shimmered and shined in the sun's golden grin, "
        "while Peter stood taller, all brave from within."
    )
    world.say(
        "So if a thing seems too hard, do not quit in a stew; "
        "with bravery, magic, and teamwork, you can make it through."
    )

    world.facts = {
        "peter": peter,
        "statue": statue,
        "helper": helper,
        "installment": installment,
        "place": params.place,
        "helper_id": params.helper,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a short rhyming story about Peter, a statue, and a missing installment.",
        "Tell a gentle poem-like story where bravery, magic, and teamwork help Peter.",
        "Make a child-friendly rhyming tale in the square with a statue that wakes up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    helper: Entity = f["helper"]
    peter: Entity = f["peter"]
    statue: Entity = f["statue"]
    installment: Entity = f["installment"]
    return [
        QAItem(
            question="Who found the installment in the square?",
            answer="Peter found the installment in the square by the statue.",
        ),
        QAItem(
            question="Why was Peter brave?",
            answer="Peter was brave because the statue needed help and the path felt hard, but he chose to keep going.",
        ),
        QAItem(
            question="What helped Peter finish the job?",
            answer=f"{helper.label} helped Peter, and together they used bravery, magic, and teamwork to make the installment fit.",
        ),
        QAItem(
            question="What changed at the end?",
            answer="The statue began to glow, the installment clicked into place, and Peter felt proud and happy.",
        ),
        QAItem(
            question="What was Peter carrying?",
            answer=f"Peter was carrying {installment.phrase}.",
        ),
        QAItem(
            question="Who did Peter help?",
            answer=f"Peter helped the statue in the square.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something hard or scary even when you feel worried.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together and help each other finish something.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is a special power or wonder that can make unusual things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("artifact", "installment"),
        asp.fact("fit", "installment", "slot"),
        asp.fact("statue", "statue"),
        asp.fact("bravery", "peter"),
        asp.fact("magic", "peter"),
        asp.fact("teamwork", "peter"),
        asp.fact("reaches", "peter", "statue"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_finish/1."))
    atoms = asp.atoms(model, "can_finish")
    ok = ("story",) in atoms
    if ok:
        print("OK: ASP gate recognizes the Peter/statue/installment story.")
        return 0
    print("MISMATCH: ASP gate failed.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        em = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if em:
            bits.append(f"memes={em}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show can_finish/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_finish/1."))
        print("ASP atoms:", asp.atoms(model, "can_finish"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params = StoryParams(place="square", helper="friend")
        params.seed = base_seed
        samples = [generate(params)]
    else:
        for i in range(max(1, args.n)):
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
