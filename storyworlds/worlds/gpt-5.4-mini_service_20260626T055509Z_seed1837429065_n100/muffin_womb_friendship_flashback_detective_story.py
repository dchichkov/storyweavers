#!/usr/bin/env python3
"""
storyworlds/worlds/muffin_womb_friendship_flashback_detective_story.py
======================================================================

A small detective-story world about a missing muffin, a loyal friendship,
and a flashback that explains the clue trail.

The seed words are threaded through the world:
- muffin
- womb

The story is designed to feel like a tiny, child-facing detective tale:
someone notices a mystery, follows clues, remembers a flashback, and ends
with friendship making the answer feel kind instead of scary.
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
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the kitchen"
    indoors: bool = True
    affords: set[str] = field(default_factory=lambda: {"investigate", "hide", "remember"})


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    place: str


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_seen = False

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


def build_world() -> World:
    return World(SETTINGS["kitchen"])


def clue_is_muffin(clue: Clue) -> bool:
    return clue.label == "muffin"


def tell(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    if setting is None:
        raise StoryError("Unknown setting.")
    world = World(setting)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        memes={"curiosity": 1.0, "friendship": 1.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        label=params.friend_name,
        memes={"friendship": 1.0},
    ))
    muffin = world.add(Entity(
        id="muffin",
        type="muffin",
        label="muffin",
        phrase="a warm blueberry muffin",
        owner=detective.id,
        caretaker=detective.id,
    ))

    # Act 1: setup.
    world.say(f"{detective.id} was a little detective who loved quiet puzzles.")
    world.say(f"{detective.id} and {friend.id} were best friends, and they shared a lot of secrets.")
    world.say(f"One morning, {detective.id} found {detective.pronoun('possessive')} muffin missing from the table.")
    world.say(f"The kitchen felt still, and the missing muffin made the room seem twice as big.")

    # Act 2: investigation and flashback.
    world.para()
    world.say(f"{detective.id} looked under a cup, behind a napkin, and beside the sink.")
    world.say(f"Then {detective.id} noticed a tiny crumb trail leading to the window.")
    world.say(f"That clue made {detective.id} pause, because it felt like something from before.")
    world.say(
        f"In a flashback, {friend.id} had once listened to a story about the womb, "
        f"the warm place where a baby grows before birth."
    )
    world.say(
        f"In that memory, {friend.id} had said they liked stories that helped them feel close, "
        f"safe, and brave."
    )
    world.flashback_seen = True

    # Act 3: resolution.
    world.para()
    world.say(
        f"At last, {detective.id} followed the crumbs to a sunny chair by the window, "
        f"where {friend.id} had tucked the muffin into a napkin so it would not get squashed."
    )
    world.say(
        f"{friend.id} looked worried, then smiled and said they were only trying to keep {muffin.label} safe "
        f"until breakfast."
    )
    world.say(
        f"{detective.id} laughed, because the mystery was small, the answer was kind, "
        f"and friendship made the whole story feel warmer."
    )
    world.say(
        f"Then the two friends split the muffin, and the kitchen felt cozy again."
    )

    world.facts.update(
        detective=detective,
        friend=friend,
        muffin=muffin,
        setting=setting,
        flashback=world.flashback_seen,
        solved=True,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"investigate", "hide", "remember"}),
    "nursery": Setting(place="the nursery", indoors=True, affords={"investigate", "remember"}),
    "porch": Setting(place="the porch", indoors=False, affords={"investigate", "hide"}),
}

DETECTIVE_NAMES = ["Milo", "Nina", "Tess", "Owen", "Ada", "June"]
FRIEND_NAMES = ["Pip", "Mina", "Jory", "Luz", "Benji", "Kiki"]
CHAR_TYPES = ["boy", "girl"]


@dataclass
class WorldRegistry:
    clues: list[Clue] = field(default_factory=lambda: [
        Clue(id="crumbs", label="crumbs", phrase="a tiny crumb trail", place="window"),
        Clue(id="napkin", label="napkin", phrase="a folded napkin", place="chair"),
        Clue(id="muffin", label="muffin", phrase="a blueberry muffin", place="table"),
    ])


REGISTRY = WorldRegistry()


def valid_settings() -> list[str]:
    return list(SETTINGS.keys())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about a muffin, a flashback, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--detective-name", choices=DETECTIVE_NAMES)
    ap.add_argument("--detective-type", choices=CHAR_TYPES)
    ap.add_argument("--friend-name", choices=FRIEND_NAMES)
    ap.add_argument("--friend-type", choices=CHAR_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    detective_type = args.detective_type or rng.choice(CHAR_TYPES)
    friend_type = args.friend_type or ("girl" if detective_type == "boy" else "boy")
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    if detective_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES if n != detective_name])
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_type=detective_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short detective story for young children that includes a muffin and a flashback.',
        f"Tell a gentle mystery where {f['detective'].id} looks for a missing muffin and remembers a kind friendship moment.",
        "Write a cozy story where a clue leads to a happy answer and the word 'womb' appears in a child-friendly flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    fr = f["friend"]
    return [
        QAItem(
            question=f"What kind of story was this about {d.id} and {fr.id}?",
            answer=f"It was a tiny detective story about {d.id}, {fr.id}, and a missing muffin.",
        ),
        QAItem(
            question=f"What clue did {d.id} follow?",
            answer="They followed a tiny crumb trail to the window chair.",
        ),
        QAItem(
            question="What did the flashback help explain?",
            answer="The flashback helped explain that the friend remembered a story about the womb, where a baby grows before birth, and that memory fit the cozy, close feeling of the scene.",
        ),
        QAItem(
            question=f"Where was the muffin found?",
            answer=f"It was found tucked into a napkin by a sunny chair near the window.",
        ),
        QAItem(
            question=f"How did {d.id} feel at the end?",
            answer=f"{d.id} felt happy because the mystery was solved by friendship, not by blame.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a muffin?",
            answer="A muffin is a small baked treat that is soft and round on top.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that jumps back to something that happened earlier.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, helping them, and being kind to them.",
        ),
        QAItem(
            question="What is the womb?",
            answer="The womb is a safe place inside a mother's body where a baby grows before birth.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}, meters={e.meters}, memes={e.memes}")
    lines.append(f"flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


ASP_RULES = r"""
story(mystery) :- muffin_missing, flashback, friendship.
muffin_missing :- clue(crumbs).
flashback :- remembers(womb_story).
friendship :- friends(_, _).
#show story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("clue", "crumbs"),
        asp.fact("remembers", "womb_story"),
        asp.fact("friends", "detective", "friend"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story/1."))
    ok = ("story", ("mystery",)) in set(asp.atoms(model, "story"))
    if ok:
        print("OK: ASP twin recognizes the mystery story.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected story.")
    return 1


def asp_reasonable() -> bool:
    return True


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
        print(asp_program("#show story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story/1."))
        print("ASP facts derived:")
        for atom in asp.atoms(model, "story"):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="kitchen", detective_name="Nina", detective_type="girl", friend_name="Pip", friend_type="boy"),
            StoryParams(setting="nursery", detective_name="Milo", detective_type="boy", friend_name="Kiki", friend_type="girl"),
            StoryParams(setting="porch", detective_name="Ada", detective_type="girl", friend_name="Benji", friend_type="boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.detective_name} and {p.friend_name} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
