#!/usr/bin/env python3
"""
storyworlds/worlds/chop_dim_sharing_mystery_to_solve_curiosity.py
===================================================================

A tiny pirate-tale story world about curiosity, a mystery to solve, and a
kindly kind of sharing.

Seed premise:
- A young pirate finds a strange "chop-dim" clue.
- Curiosity pushes the crew to investigate.
- They share clues, solve the mystery, and end with a fair split.

The world is intentionally small and constraint-checked: only a handful of
settings, clues, and rewards are valid, and the story is only generated when
the clue, setting, and reward fit together honestly.
"""

from __future__ import annotations

import argparse
import copy
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
    plural: bool = False
    owner: Optional[str] = None
    shared_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("weight", "hidden", "found", "split", "glow", "work"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "joy", "trust", "worry", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    phrase: str
    clue_tag: str
    answer: str
    needed_place: str
    reveals: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    splitable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SharingTool:
    id: str
    label: str
    verb: str
    noun: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    mystery: str
    reward: str
    name: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "ship": Setting(
        place="the ship",
        detail="The deck creaked softly, and the lanterns blinked like sleepy stars.",
        affords={"listen", "search", "share"},
    ),
    "harbor": Setting(
        place="the harbor",
        detail="The water slapped the posts, and gulls cried over the dock.",
        affords={"listen", "search", "share"},
    ),
    "cove": Setting(
        place="the cove",
        detail="The rocks made a quiet ring around the blue water.",
        affords={"listen", "search", "share"},
    ),
}

MYSTERIES = {
    "chop_dim_map": Mystery(
        id="chop_dim_map",
        label="a chop-dim map scrap",
        phrase="a crooked little map scrap with a chop-dim mark",
        clue_tag="chop-dim",
        answer="the hidden shell cave",
        needed_place="cove",
        reveals="a bright shell cave where the crew had tucked the prize",
        tags={"chop-dim", "mystery", "curiosity"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        label="a missing brass key",
        phrase="a brass key that had vanished from its hook",
        clue_tag="key",
        answer="the captain's chest under the net",
        needed_place="ship",
        reveals="the chest under the fishing net by the mast",
        tags={"key", "mystery", "curiosity"},
    ),
    "whisper_note": Mystery(
        id="whisper_note",
        label="a whispery note",
        phrase="a note with a tiny wave drawn on it",
        clue_tag="note",
        answer="the lantern tucked in the harbor post",
        needed_place="harbor",
        reveals="the lantern hiding inside the old harbor post",
        tags={"note", "mystery", "curiosity"},
    ),
}

REWARDS = {
    "pearls": Reward(
        id="pearls",
        label="pearls",
        phrase="a small pouch of shared pearls",
        splitable=True,
        tags={"share", "treasure"},
    ),
    "cookies": Reward(
        id="cookies",
        label="cookies",
        phrase="a tin of sweet ship cookies",
        splitable=True,
        tags={"share", "treat"},
    ),
    "gems": Reward(
        id="gems",
        label="gems",
        phrase="a little bundle of bright gems",
        splitable=True,
        tags={"share", "treasure"},
    ),
}

TOOLS = {
    "magnifier": SharingTool(
        id="magnifier",
        label="a brass magnifier",
        verb="compare",
        noun="magnifier",
        tags={"curiosity", "mystery"},
    ),
    "lantern": SharingTool(
        id="lantern",
        label="a lantern",
        verb="light",
        noun="lantern",
        tags={"curiosity", "mystery"},
    ),
    "rope_table": SharingTool(
        id="rope_table",
        label="a rope-tied table",
        verb="spread out",
        noun="table",
        tags={"share"},
    ),
}

NAMES = ["Pip", "Mara", "Jory", "Nell", "Finn", "Sailor", "Ari", "Bo", "Tess", "Kit"]
HELPERS = ["mate", "captain", "friend", "deckhand"]
TRAITS = ["curious", "brave", "cheerful", "patient", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery.needed_place != place:
                continue
            for rid, reward in REWARDS.items():
                if reward.splitable and "share" in reward.tags:
                    out.append((place, mid, rid))
    return out


def explain_rejection(mystery: Mystery, reward: Reward) -> str:
    return (
        f"(No story: the mystery '{mystery.label}' belongs in {mystery.needed_place}, "
        f"and the reward must be a fair shareable prize. This pair does not fit.)"
    )


def explain_helper(helper: str) -> str:
    return f"(No story: '{helper}' is not a valid crew role for this tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate-tale story world: curiosity, a mystery to solve, and sharing."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--name")
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
    if args.mystery and args.reward:
        m, r = MYSTERIES[args.mystery], REWARDS[args.reward]
        if not (m.needed_place in SETTINGS and r.splitable):
            raise StoryError(explain_rejection(m, r))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.reward is None or c[2] == args.reward)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, reward = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        mystery=mystery,
        reward=reward,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
    )


def _maybe(name: str, a: str, b: str) -> str:
    return a if name else b


def story_logic(world: World, hero: Entity, helper: Entity, mystery: Mystery, reward: Reward, tool: SharingTool) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was a curious little pirate who liked to peer into corners and under ropes."
    )
    world.say(
        f"One day on {world.setting.place}, {hero.id} found {mystery.phrase}. "
        f"The little chop-dim mark made {hero.id} tilt {hero.pronoun('possessive')} head."
    )
    world.para()
    world.say(world.setting.detail)
    world.say(
        f"{hero.id} wanted to know what the chop-dim clue meant, so {hero.pronoun()} called {helper.id} over."
    )
    world.say(
        f"Together they used {tool.label} to {tool.verb} the clue and look for the next sign."
    )
    helper.memes["trust"] += 1
    hero.memes["joy"] += 1

    if mystery.needed_place == "cove":
        world.say(
            f"They followed the arrow marks all the way to the cove, where the rocks hummed in the breeze."
        )
    elif mystery.needed_place == "ship":
        world.say(
            f"They searched along the ship until the mast shadow pointed them toward the hidden place."
        )
    else:
        world.say(
            f"They walked the harbor boards until the clue matched the little sign they had missed before."
        )

    world.para()
    world.say(
        f"The mystery was solved: {mystery.reveals}. Inside it was {reward.phrase}."
    )
    world.say(
        f"{hero.id} did not keep it all. {hero.pronoun().capitalize()} shared it with {helper.id}, "
        f"and then the two of them split the prize fair and square."
    )
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    helper.memes["joy"] += 1
    reward.meters["split"] = 1.0
    reward.shared_with.update({hero.id, helper.id})
    world.say(
        f"By nightfall, {hero.id} and {helper.id} were smiling on the deck, with half the treasure each "
        f"and the chop-dim mystery tucked safely into memory."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="pirate", label=params.name))
    helper = world.add(Entity(id=params.helper.capitalize(), kind="character", type="pirate", label=params.helper))
    mystery = MYSTERIES[params.mystery]
    reward = REWARDS[params.reward]
    tool = TOOLS["magnifier" if params.mystery != "whisper_note" else "lantern"]

    world.add(Entity(id=mystery.id, label=mystery.label, phrase=mystery.phrase))
    world.add(Entity(id=reward.id, label=reward.label, phrase=reward.phrase, plural=reward.splitable))
    world.add(Entity(id=tool.id, label=tool.label, phrase=tool.label))

    story_logic(world, hero, helper, mystery, reward, tool)

    world.facts.update(
        hero=hero,
        helper=helper,
        mystery=mystery,
        reward=reward,
        tool=tool,
        setting=world.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short pirate story for a small child about a curious pirate who finds {f['mystery'].phrase} and solves a mystery by sharing clues.",
        f"Tell a gentle pirate tale set on {f['setting'].place} where {f['hero'].id} and {f['helper'].id} use {f['tool'].label} to solve the chop-dim mystery together.",
        f"Write a child-friendly story about curiosity, sharing, and treasure, and make sure the words 'chop-dim' and '{f['reward'].label}' appear.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    reward: Reward = f["reward"]
    return [
        QAItem(
            question=f"Why did {hero.id} lean in to look at the chop-dim clue?",
            answer=f"{hero.id} was curious, so {hero.pronoun()} wanted to find out what the chop-dim mark meant.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the mystery together?",
            answer=f"They shared the clue, used {f['tool'].label}, and followed the signs until they found {mystery.reveals}.",
        ),
        QAItem(
            question=f"What happened to the {reward.label} at the end?",
            answer=f"The {reward.label} were shared fairly between {hero.id} and {helper.id}, so nobody was left out.",
        ),
        QAItem(
            question=f"Where was the mystery hiding?",
            answer=f"It was hiding at {world.setting.place}, which is where the clue made the most sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn more about what they find.",
        ),
        QAItem(
            question="Why is sharing nice?",
            answer="Sharing is nice because it lets everyone have a part of something good.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to solve by looking for clues.",
        ),
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat that pirates use to travel over the sea and carry their gear.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], ""]
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(ship). setting(harbor). setting(cove).

mystery(chop_dim_map). mystery(missing_key). mystery(whisper_note).
reward(pearls). reward(cookies). reward(gems).

needs_place(chop_dim_map,cove).
needs_place(missing_key,ship).
needs_place(whisper_note,harbor).

shareable(pearls). shareable(cookies). shareable(gems).

valid(Place, M, R) :- setting(Place), mystery(M), reward(R), needs_place(M, Place), shareable(R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("needs_place", m.id, m.needed_place))
    for r in REWARDS.values():
        lines.append(asp.fact("reward", r.id))
        if r.splitable:
            lines.append(asp.fact("shareable", r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


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


CURATED = [
    StoryParams(place="cove", mystery="chop_dim_map", reward="pearls", name="Pip", helper="mate"),
    StoryParams(place="ship", mystery="missing_key", reward="cookies", name="Mara", helper="friend"),
    StoryParams(place="harbor", mystery="whisper_note", reward="gems", name="Nell", helper="deckhand"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3;"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
