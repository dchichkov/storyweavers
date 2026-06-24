#!/usr/bin/env python3
"""
storyworlds/worlds/intellectual_condense_peek_quest_ghost_story.py
===================================================================

A small ghost-story quest world for a child-friendly haunted-house tale.

Core premise:
- A curious child and a gentle ghost search an old house for a hidden quest item.
- The child uses intellectual patience to condense clues into a simple plan.
- They peek into rooms, follow the hints, and resolve the quest with a bright ending.

This world is deliberately compact:
- one setting,
- one quest,
- one helper ghost,
- one seeker,
- one hidden prize,
- a state-driven turn from confusion to insight to success.

The prose aims for a soft Ghost Story style rather than horror.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    mood: str
    rooms: list[str] = field(default_factory=list)


@dataclass
class Quest:
    id: str
    goal: str
    clue_words: list[str] = field(default_factory=list)
    finale: str = ""


@dataclass
class StoryParams:
    setting: str
    quest: str
    seeker_name: str
    seeker_type: str
    ghost_name: str
    ghost_type: str
    seed: Optional[int] = None


SETTINGS = {
    "old_house": Setting(
        place="the old house",
        mood="moonlit and quiet",
        rooms=["the hall", "the attic", "the library", "the staircase"],
    ),
    "library": Setting(
        place="the little library",
        mood="hushed and glowy",
        rooms=["the reading nook", "the map shelf", "the back room", "the window seat"],
    ),
}

QUESTS = {
    "silver_key": Quest(
        id="silver_key",
        goal="a silver key",
        clue_words=["peek", "intellectual", "condense"],
        finale="the silver key on a ribbon",
    ),
    "star_lantern": Quest(
        id="star_lantern",
        goal="a star-shaped lantern",
        clue_words=["peek", "intellectual", "condense"],
        finale="the star-shaped lantern with a warm little glow",
    ),
}

SEEKER_NAMES = ["Mina", "Eli", "Nora", "Theo", "Lena", "Finn"]
GHOST_NAMES = ["Moss", "Wisp", "Pip", "Murmur", "Luna"]


class World:
    def __init__(self, setting: Setting, quest: Quest) -> None:
        self.setting = setting
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        clone = World(self.setting, self.quest)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_peek(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.entities.get("seeker")
    ghost = world.entities.get("ghost")
    clue = world.entities.get("clue")
    if not seeker or not ghost or not clue:
        return out
    if seeker.meters["curiosity"] < THRESHOLD:
        return out
    sig = ("peeked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.memes["focus"] += 1
    ghost.memes["help"] += 1
    clue.meters["revealed"] += 1
    out.append("A clue shone just enough to notice.")
    return out


def _r_condense(world: World) -> list[str]:
    seeker = world.entities.get("seeker")
    if not seeker:
        return []
    if seeker.memes["focus"] < THRESHOLD:
        return []
    sig = ("condensed",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    seeker.memes["understanding"] += 1
    return ["The clues fit together like little puzzle pieces."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_peek, _r_condense):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str]]:
    return [(s, q) for s in SETTINGS for q in QUESTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A soft ghost-story quest world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--ghost-name")
    ap.add_argument("--type", choices=["girl", "boy"])
    ap.add_argument("--ghost-type", choices=["ghost"])
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid setting/quest combination matches the options.")
    setting, quest = rng.choice(sorted(combos))
    seeker_type = args.type or rng.choice(["girl", "boy"])
    seeker_name = args.name or rng.choice(SEEKER_NAMES)
    ghost_type = "ghost"
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(
        setting=setting,
        quest=quest,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        ghost_name=ghost_name,
        ghost_type=ghost_type,
    )


def setup_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    world = World(setting, quest)
    seeker = world.add(Entity(id="seeker", kind="character", type=params.seeker_type, label=params.seeker_name))
    ghost = world.add(Entity(id="ghost", kind="character", type=params.ghost_type, label=params.ghost_name))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="the clue note", phrase="a folded note"))
    prize = world.add(Entity(id="prize", kind="thing", type="prize", label=quest.goal, phrase=quest.finale))
    seeker.meters["curiosity"] = 1
    seeker.memes["wonder"] = 1
    ghost.memes["gentleness"] = 1
    clue.meters["revealed"] = 0
    prize.meters["hidden"] = 1
    world.facts.update(seeker=seeker, ghost=ghost, clue=clue, prize=prize)
    return world


def tell(world: World) -> World:
    seeker = world.get("seeker")
    ghost = world.get("ghost")
    clue = world.get("clue")
    prize = world.get("prize")
    setting = world.setting
    quest = world.quest

    world.say(
        f"{seeker.label} came to {setting.place}, where the air felt {setting.mood}."
    )
    world.say(
        f"Near the doorway, {ghost.label} floated out with a soft smile, like a lamp in mist."
    )
    world.say(
        f'"I have a quest," {seeker.label} whispered. "I need {quest.goal}."'
    )

    world.para()
    world.say(
        f"They began to peek into the quiet rooms, one by one, listening to floorboards and moonlight."
    )
    seeker.meters["curiosity"] += 1
    propagate(world, narrate=True)

    world.say(
        f"{seeker.label} did not rush. {seeker.label} used an intellectual kind of patience and condensed the clues into a tiny plan."
    )
    seeker.memes["focus"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"At last, {ghost.label} pointed to the last hiding place, and {seeker.label} peeked behind it."
    )
    prize.meters["found"] = 1
    world.say(
        f"There it was: {quest.finale}."
    )
    seeker.memes["joy"] += 1
    ghost.memes["joy"] += 1
    world.say(
        f"{seeker.label} smiled so wide the whole {setting.place} felt lighter, and {ghost.label} shimmered like a happy whisper."
    )

    world.facts.update(found=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost-story quest for a young child that includes the words "{world.quest.clue_words[0]}", "{world.quest.clue_words[1]}", and "{world.quest.clue_words[2]}".',
        f"Tell a story about {f['seeker'].label} and a friendly ghost exploring {world.setting.place} to find {world.quest.goal}.",
        f"Write a soft spooky adventure where a child peeks into quiet rooms, thinks carefully, condenses the clues, and finishes a quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    ghost = f["ghost"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who went on the quest in {world.setting.place}?",
            answer=f"{seeker.label} went on the quest with {ghost.label}, the friendly ghost. They looked for {world.quest.goal} together.",
        ),
        QAItem(
            question=f"What did {seeker.label} do before finding the prize?",
            answer=f"{seeker.label} peeked into the quiet rooms and used an intellectual kind of patience. Then {seeker.label} condensed the clues into a tiny plan.",
        ),
        QAItem(
            question=f"What did they find at the end?",
            answer=f"They found {prize.phrase}, and that was the end of the quest. The old place felt bright instead of lonely after that.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to peek?",
            answer="To peek means to look quickly and carefully, often into a place that is quiet or hidden.",
        ),
        QAItem(
            question="What does intellectual mean?",
            answer="Intellectual means using your thinking mind in a careful, smart way.",
        ),
        QAItem(
            question="What does condense mean?",
            answer="To condense means to make something smaller and simpler, like putting many clues into one short plan.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something important or solve a problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q) :- setting(S), quest(Q).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
        return 1
    print(f"OK: {len(py)} valid combos.")
    params = StoryParams(
        setting="old_house",
        quest="silver_key",
        seeker_name="Mina",
        seeker_type="girl",
        ghost_name="Wisp",
        ghost_type="ghost",
    )
    sample = generate(params)
    if not sample.story.strip():
        print("Smoke test failed: empty story")
        return 1
    print("OK: smoke test generated a story.")
    return 0


CURATED = [
    StoryParams(setting="old_house", quest="silver_key", seeker_name="Mina", seeker_type="girl", ghost_name="Wisp", ghost_type="ghost"),
    StoryParams(setting="library", quest="star_lantern", seeker_name="Theo", seeker_type="boy", ghost_name="Murmur", ghost_type="ghost"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    world = setup_world(params)
    tell(world)
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
        for s, q in asp_valid_combos():
            print(f"{s} {q}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
            header = f"### {p.seeker_name} and {p.ghost_name}: {p.setting} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if not combos:
        raise StoryError("No valid combination matches the filters.")
    setting, quest = rng.choice(sorted(combos))
    seeker_type = args.type or rng.choice(["girl", "boy"])
    seeker_name = args.name or rng.choice(SEEKER_NAMES)
    ghost_name = args.ghost_name or rng.choice(GHOST_NAMES)
    return StoryParams(
        setting=setting,
        quest=quest,
        seeker_name=seeker_name,
        seeker_type=seeker_type,
        ghost_name=ghost_name,
        ghost_type="ghost",
    )


if __name__ == "__main__":
    main()
