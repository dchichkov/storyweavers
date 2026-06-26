#!/usr/bin/env python3
"""
storyworlds/worlds/photograph_visit_wail_friendship_mystery_to_solve.py
======================================================================

A small whodunit-style story world about friendship, a visit, a photograph,
and a mystery to solve.

The seed image is a gentle little detective tale:
a child visits a friend, finds an old photograph that does not make sense,
and the two friends follow clues until the mystery is solved. The emotional
turn is a wail of surprise or worry when the clue seems to point the wrong
way, followed by a careful, friendly resolution.

The story is driven by a compact world model:
- typed entities with physical meters and emotional memes
- a clue chain involving a photograph, a visit, a wail, and a solved mystery
- a reasonableness gate that keeps the plots coherent
- an inline ASP twin for parity checks
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
    holder: Optional[str] = None
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
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    topic: str
    key_clue: str
    mislead_clue: str
    solution: str
    photo_subject: str
    wail_reason: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    friend: str
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


SETTINGS = {
    "cottage": Setting(place="the little cottage", indoor=True, affords={"visit"}),
    "library": Setting(place="the old library", indoor=True, affords={"visit"}),
    "garden": Setting(place="the garden gate", indoor=False, affords={"visit"}),
}

MYSTERIES = {
    "photo-frame": Mystery(
        id="photo-frame",
        topic="the missing photograph",
        key_clue="a photograph tucked behind the frame",
        mislead_clue="a muddy thumbprint on the glass",
        solution="the photo was not stolen at all; it had slipped behind the frame",
        photo_subject="a smiling puppy beside two friends",
        wail_reason="the friends thought the photograph was gone for good",
        tags={"photograph", "visit", "wail", "friendship", "mystery"},
    ),
    "garden-map": Mystery(
        id="garden-map",
        topic="the torn photograph map",
        key_clue="a torn corner that matched the photograph",
        mislead_clue="a rustle in the hedge that sounded suspicious",
        solution="the torn piece completed a hidden map on the back of the photograph",
        photo_subject="a bench under the big oak tree",
        wail_reason="the clue looked lost and the friends feared the mystery would stay unsolved",
        tags={"photograph", "visit", "wail", "friendship", "mystery"},
    ),
}

NAMES = ["Mia", "Lily", "Nora", "Eli", "Ben", "Ava", "Theo", "Zoe"]
FRIEND_NAMES = ["Jules", "Finn", "Maya", "Ivy", "Sam", "Noah", "Rose", "Leo"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery_id) for place in SETTINGS for mystery_id in MYSTERIES if "visit" in SETTINGS[place].affords]


@dataclass
class Reasoner:
    world: World
    child: Entity
    friend: Entity
    mystery: Mystery
    photo: Entity
    clue_found: bool = False
    wrong_turn: bool = False
    solved: bool = False


def reasonableness_gate(place: str, mystery_id: str) -> None:
    if place not in SETTINGS:
        raise StoryError(f"Unknown place: {place}")
    if mystery_id not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {mystery_id}")
    if "visit" not in SETTINGS[place].affords:
        raise StoryError("This setting does not support a visit-based story.")
    if not MYSTERIES[mystery_id].photo_subject:
        raise StoryError("The mystery must be anchored by a photograph.")


def tell(setting: Setting, mystery: Mystery, name: str, friend_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type="child", label=name, memes={"curiosity": 1.0, "friendship": 1.0}))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", label=friend_name, memes={"friendship": 1.0}))
    photo = world.add(Entity(
        id="photo",
        kind="thing",
        type="photograph",
        label="photograph",
        phrase=f"a old photograph of {mystery.photo_subject}",
        owner=friend.id,
        holder=friend.id,
        meters={"age": 1.0},
    ))
    state = Reasoner(world=world, child=child, friend=friend, mystery=mystery, photo=photo)

    world.say(f"{child.id} loved solving little mysteries with {friend.id}.")
    world.say(f"One day, {child.id} went to visit {friend.id} at {setting.place}.")
    world.say(f"Inside, {friend.id} showed {child.id} {photo.phrase}.")
    world.say(f"It looked important because it pictured {mystery.photo_subject}.")

    world.para()
    world.say(f"{child.id} noticed {mystery.mislead_clue}.")
    world.say(f"That made the room feel strange, and soon {friend.id} gave a sudden wail.")
    world.say(f"{friend.id} feared {mystery.wail_reason}.")

    state.wrong_turn = True
    world.para()
    world.say(f"But {child.id} did not stop at the first clue.")
    world.say(f"{child.id} checked the frame, the table, and the light by the window.")
    world.say(f"Then {child.id} found {mystery.key_clue}.")
    state.clue_found = True

    world.para()
    world.say(f"{child.id} and {friend.id} compared the clues like tiny detectives.")
    world.say(f"They understood that {mystery.solution}.")
    state.solved = True
    world.say(f"{friend.id} let out a small relieved laugh instead of a wail.")
    world.say(f"The friends smiled at the photograph, and the mystery was solved together.")

    world.facts.update(
        child=child,
        friend=friend,
        photo=photo,
        mystery=mystery,
        setting=setting,
        state=state,
        solved=state.solved,
        wail=state.wrong_turn,
    )
    return world


KNOWLEDGE = {
    "photograph": [
        ("What is a photograph?",
         "A photograph is a picture made with a camera that can show a moment from real life."),
    ],
    "visit": [
        ("What does it mean to visit someone?",
         "To visit someone means to go to their home or place for a short time to see them."),
    ],
    "wail": [
        ("What is a wail?",
         "A wail is a long, loud cry that can show worry, sadness, or surprise."),
    ],
    "friendship": [
        ("What is friendship?",
         "Friendship is the caring bond between people who help each other and like being together."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is something puzzling that people try to understand by looking for clues."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short whodunit for a young child that includes the words "photograph", "visit", and "wail".',
        f"Tell a friendship story where {f['child'].id} goes to visit {f['friend'].id} and they solve {mystery.topic}.",
        f"Write a gentle mystery about a photograph that makes one friend wail before the clues are understood.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]

    return [
        QAItem(
            question=f"Who went to visit {friend.id}?",
            answer=f"{child.id} went to visit {friend.id} at {setting.place}.",
        ),
        QAItem(
            question="What did the friends look at first?",
            answer=f"They looked at a photograph showing {mystery.photo_subject}.",
        ),
        QAItem(
            question=f"Why did {friend.id} wail?",
            answer=f"{friend.id} wail because {mystery.wail_reason}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{child.id} and {friend.id} followed the clues and solved the mystery together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags)
    out: list[QAItem] = []
    for tag in ["photograph", "visit", "wail", "friendship", "mystery"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  solved: {world.facts.get('solved')}")
    return "\n".join(lines)


def explain_rejection(place: str, mystery_id: str) -> str:
    mystery = MYSTERIES[mystery_id]
    return (
        f"(No story: the chosen setting cannot support a clear visit-and-clue chain "
        f"for {mystery.topic}.)"
    )


CURATED = [
    StoryParams(place="cottage", mystery="photo-frame", name="Mia", friend="Jules"),
    StoryParams(place="library", mystery="garden-map", name="Eli", friend="Maya"),
    StoryParams(place="garden", mystery="photo-frame", name="Nora", friend="Finn"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        reasonableness_gate(args.place, args.mystery)
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    return StoryParams(place=place, mystery=mystery_id, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params.place, params.mystery)
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.friend)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style friendship mystery story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--friend", choices=FRIEND_NAMES)
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


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_id(M).
visit_story(P,M) :- place(P), mystery(M), affords(P,visit).
showable(P,M) :- visit_story(P,M), has_photograph(M), has_wail(M), has_friendship(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", mid))
        lines.append(asp.fact("has_photograph", mid))
        lines.append(asp.fact("has_wail", mid))
        lines.append(asp.fact("has_friendship", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show visit_story/2."))
    return sorted(set(asp.atoms(model, "visit_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show visit_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible visit-story combos:\n")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
