#!/usr/bin/env python3
"""
A mystery storyworld about a chalk picture that gets devastated, a small cast
of suspects, and a careful child detective who follows clues through dialogue.

The core premise is simple:
- someone makes a chalk creation,
- it is devastated before the reveal,
- the characters talk, notice clues, and discover the cause,
- the ending explains who did it and why, with a satisfying image of repair.

The world model tracks physical evidence in meters and feelings in memes.
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


@dataclass
class Place:
    name: str
    indoor: bool = True
    features: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    detective_name: str
    helper_name: str
    culprit_name: str
    culprit_kind: str
    culprit_reason: str
    seed: Optional[int] = None


PLACES = {
    "hallway": Place("the hallway", indoor=True, features={"wall", "door", "floor"}),
    "porch": Place("the porch", indoor=False, features={"wall", "steps", "floor"}),
    "classroom": Place("the classroom", indoor=True, features={"wall", "desk", "floor"}),
    "sidewalk": Place("the sidewalk", indoor=False, features={"curb", "wall", "ground"}),
}

DETECTIVE_NAMES = ["Mina", "Noah", "Piper", "Eli", "June", "Toby"]
HELPER_NAMES = ["Lena", "Owen", "Iris", "Cal", "Ruby", "Jasper"]
CULPRIT_NAMES = ["Milo", "Nina", "Bram", "Tess", "Arlo", "Kia"]

REASONS = [
    "wanted to share the picture",
    "was trying to make room for new chalk",
    "thought the drawing was already a game",
    "wanted to see what would happen",
]

CHALK_FACTS = [
    ("What is chalk?", "Chalk is a soft white or colored stick that can draw marks on a sidewalk, wall, or board."),
    ("Why can chalk be dusty?", "Chalk is dusty because tiny bits break off when it rubs against a surface."),
    ("What does it mean to smudge chalk?", "To smudge chalk means to smear the lines so the picture looks blurry or mixed up."),
]

ASP_RULES = r"""
#show valid/2.
#show culprit/1.

place(hallway). place(porch). place(classroom). place(sidewalk).

detective_name(mina;noah;piper;eli;june;toby).
helper_name(lena;owen;iris;cal;ruby;jasper).

reason(share). reason(clear_room). reason(game). reason(curious).

valid(P, R) :- place(P), reason(R).

culprit(X) :- valid(_, _), X = mystery.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in DETECTIVE_NAMES:
        lines.append(asp.fact("detective_name", n.lower()))
    for n in HELPER_NAMES:
        lines.append(asp.fact("helper_name", n.lower()))
    for r in ["share", "clear_room", "game", "curious"]:
        lines.append(asp.fact("reason", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)
    mystery_notes: list[str] = field(default_factory=list)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def trace_world(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  notes: {world.mystery_notes}")
    return "\n".join(lines)


def build_mystery(world: World, detective: Entity, helper: Entity, culprit: Entity) -> None:
    board = world.add(Entity(
        id="board",
        kind="thing",
        type="board",
        label="chalk drawing",
        phrase="a bright chalk drawing of a smiling moon and three stars",
        meters={"intact": 1.0, "chalk": 1.0},
        memes={"pride": 1.0},
    ))
    board.owner = detective.id

    detective.memes["curious"] = 1.0
    helper.memes["worried"] = 1.0
    culprit.memes["nervous"] = 1.0

    world.say(
        f"{detective.id} stood in {world.place.name} and grinned at the chalk drawing on the wall."
    )
    world.say(
        f'"It looks perfect," {helper.id} said. "{board.phrase} is the best part of the room."'
    )
    world.para()

    world.say(
        f"Then the room went quiet. A sharp scrape showed up across the chalk, and part of it was devastated."
    )
    board.meters["smudged"] = 1.0
    board.meters["intact"] = 0.0
    board.meters["chalk"] = 0.2
    world.facts["damaged"] = True
    world.facts["damage"] = "smudged chalk"
    world.mystery_notes.append("scrape on wall")

    world.say(f'"Who did that?" {detective.id} asked.')
    world.say(f'"Not me," {helper.id} said quickly.')
    world.say(f'"I only heard the chalk cry out," {culprit.id} muttered.')
    world.para()

    detective.memes["suspicion"] = 1.0
    helper.memes["suspicion"] = 0.3
    culprit.memes["suspicion"] = 0.8

    if culprit.type == "cat":
        world.say(
            f"{detective.id} knelt and found pale dust on {culprit.pronoun('possessive')} paws."
        )
        world.say(
            f'"{You did it by accident, didn\'t you?" {detective.id} asked softly.'
        )
        world.say(f'"Mrrp," {culprit.id} answered, which was not a very good denial.')
        culprit.memes["guilt"] = 1.0
    else:
        world.say(
            f"{detective.id} noticed chalk dust on {culprit.pronoun('possessive')} sleeve."
        )
        world.say(f'"Why do you have chalk on you?" {helper.id} asked.')
        world.say(
            f'"I was trying to make room for new chalk," {culprit.id} admitted. '
            f'"I did not mean to devastate it."'
        )
        culprit.memes["guilt"] = 1.0

    world.para()
    world.say(
        f"{detective.id} listened, looked at the scrape, and nodded."
    )
    world.say(
        f'"You can help fix it," {detective.id} said, "but first we need a careful plan."'
    )
    board.meters["chalk"] = 1.0
    board.meters["repaired"] = 1.0
    culprit.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    detective.memes["relief"] = 1.0

    if culprit.type == "cat":
        world.say(
            f"Together they brushed away the dust and drew the moon again, a little lower this time so the cat's tail would not hit it."
        )
    else:
        world.say(
            f"Together they brushed away the smear and drew the stars again, with a tiny border so no elbow could rub them away."
        )
    world.say(
        f"By the end, {board.phrase} shone fresh and clear, and everyone could see what had changed."
    )
    world.facts.update(
        detective=detective.id,
        helper=helper.id,
        culprit=culprit.id,
        culprit_kind=culprit.type,
        culprit_reason=culprit.phrase,
        board=board,
        resolved=True,
    )


def build_story(params: StoryParams) -> World:
    world = World(place=PLACES[params.place])
    detective = world.add(Entity(id=params.detective_name, kind="character", type="girl"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="girl"))
    culprit = world.add(Entity(
        id=params.culprit_name,
        kind="character",
        type=params.culprit_kind,
        phrase=params.culprit_reason,
    ))
    build_mystery(world, detective, helper, culprit)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child about a chalk picture that gets devastated in {world.place.name}.',
        f'Write a dialogue-heavy story where {f["detective"]} asks who ruined the chalk drawing and the answer is found by looking at clues.',
        'Tell a gentle mystery with chalk dust, a small mistake, and a happy repair at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    board = f["board"]
    qa = [
        QAItem(
            question=f"What was devastated in the story?",
            answer=f"The chalk drawing was devastated. It got smeared and lost its first neat shape before they fixed it.",
        ),
        QAItem(
            question=f"Who asked the questions and solved the mystery?",
            answer=f"{detective} asked the questions and followed the clues until the cause of the damage made sense.",
        ),
        QAItem(
            question=f"How did the story end after the chalk was repaired?",
            answer=f"It ended with the chalk picture looking fresh again, and everyone could see the careful repair on the wall.",
        ),
        QAItem(
            question=f"Why did {culprit} admit what happened?",
            answer=f"{culprit} admitted it after the others noticed chalk dust and the scrape, so the small secret could not stay hidden.",
        ),
    ]
    if culprit == "Milo":
        qa.append(QAItem(
            question="What clue showed who had been near the chalk?",
            answer="The clue was pale chalk dust on the sleeve, which showed someone had been close to the drawing.",
        ))
    else:
        qa.append(QAItem(
            question="What clue showed what happened to the picture?",
            answer="The clue was the sharp scrape across the wall, which showed the chalk picture had been rubbed and smudged.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in CHALK_FACTS]


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


def choose_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != detective_name])
    culprit_name = args.culprit_name or rng.choice([n for n in CULPRIT_NAMES if n not in {detective_name, helper_name}])
    culprit_kind = args.culprit_kind or rng.choice(["boy", "girl", "cat"])
    culprit_reason = args.culprit_reason or rng.choice(REASONS)
    return StoryParams(
        place=place,
        detective_name=detective_name,
        helper_name=helper_name,
        culprit_name=culprit_name,
        culprit_kind=culprit_kind,
        culprit_reason=culprit_reason,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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
        print(trace_world(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld: chalk, clues, and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
    ap.add_argument("--culprit-name", choices=CULPRIT_NAMES)
    ap.add_argument("--culprit-kind", choices=["boy", "girl", "cat"])
    ap.add_argument("--culprit-reason", choices=REASONS)
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
    return choose_params(args, rng)


def explain_asp() -> str:
    return asp_program("#show valid/2.")


def asp_verify() -> int:
    import asp
    py = {(p, r) for p in PLACES for r in ["share", "clear_room", "game", "curious"]}
    clingo_set = set(asp_valid_pairs())
    python_set = py
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="classroom", detective_name="Mina", helper_name="Lena", culprit_name="Milo", culprit_kind="cat", culprit_reason="wanted to share the picture"),
    StoryParams(place="hallway", detective_name="Noah", helper_name="Iris", culprit_name="Bram", culprit_kind="boy", culprit_reason="was trying to make room for new chalk"),
    StoryParams(place="porch", detective_name="June", helper_name="Owen", culprit_name="Tess", culprit_kind="girl", culprit_reason="wanted to see what would happen"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(explain_asp())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible pairs:")
        for p, r in asp_valid_pairs():
            print(p, r)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: chalk mystery in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
