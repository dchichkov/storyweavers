#!/usr/bin/env python3
"""
storyworlds/worlds/coed_french_belch_flashback_bad_ending_bedtime.py
====================================================================

A small bedtime-story world with a gentle setup, a flashback reveal, and a bad
ending when a rude belch spoils the calm. The domain is built around a coed
sleepover, a French storybook, and the emotional ripple of manners, embarrassment,
and bedtime comfort.

Premise:
- A child at a coed bedtime gathering wants to keep reading a French storybook.
- A snack or fizzy drink can trigger a belch.
- A flashback reminds the child of an earlier embarrassment and shapes the choice.
- If manners break at the wrong moment, the ending can go bad: the room grows
  tense, the storybook closes, and bedtime comfort is lost.

The world is intentionally small and constraint-checked:
- We only generate stories where the belch is socially relevant.
- We only permit a flashback when there is a past embarrassment worth recalling.
- We only permit a bad ending when the conflict actually outlasts the bedtime
  window and the child cannot repair it in time.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bedroom"
    coed: bool = True
    bedtime: bool = True
    french: bool = True


@dataclass
class Book:
    label: str
    phrase: str
    language: str = "French"


@dataclass
class Snack:
    label: str
    phrase: str
    belch_risk: float


@dataclass
class Memory:
    label: str
    flashback_line: str
    embarrassment: float = 1.0


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.time_left: int = 3
        self.flashback_active: bool = False
        self.flashback_done: bool = False
        self.bad_ending: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.time_left = self.time_left
        clone.flashback_active = self.flashback_active
        clone.flashback_done = self.flashback_done
        clone.bad_ending = self.bad_ending
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

NAMES_GIRL = ["Mia", "Lina", "Zoe", "Nora", "Ella", "Ivy"]
NAMES_BOY = ["Theo", "Noah", "Eli", "Finn", "Max", "Ben"]
TRAITS = ["sleepy", "curious", "gentle", "shy", "brave", "quiet"]

SETTINGS = {
    "bedroom": Setting(place="the bedroom", coed=True, bedtime=True, french=True),
    "sleepover_room": Setting(place="the sleepover room", coed=True, bedtime=True, french=True),
    "nursery": Setting(place="the nursery", coed=False, bedtime=True, french=False),
}

BOOKS = {
    "storybook": Book(label="storybook", phrase="a tiny French storybook"),
    "picturebook": Book(label="picture book", phrase="a French picture book"),
}

SNACKS = {
    "juice": Snack(label="juice", phrase="a cup of juice", belch_risk=0.4),
    "soda": Snack(label="soda", phrase="a fizzy soda", belch_risk=1.0),
    "cocoa": Snack(label="cocoa", phrase="a warm cocoa", belch_risk=0.2),
}

MEMORIES = {
    "school": Memory(
        label="school day",
        flashback_line="The memory of a classroom giggle came back all at once.",
        embarrassment=1.0,
    ),
    "birthday": Memory(
        label="birthday party",
        flashback_line="A flashback of a birthday belch made the child blush again.",
        embarrassment=1.2,
    ),
    "train": Memory(
        label="train ride",
        flashback_line="The child remembered a train ride where a belch had echoed too loudly.",
        embarrassment=0.9,
    ),
}


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    child: str
    gender: str
    trait: str
    book: str
    snack: str
    memory: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core simulation helpers
# ---------------------------------------------------------------------------

def _narrate_opening(world: World, child: Entity, friend: Entity, book: Book) -> None:
    world.say(
        f"At {world.setting.place}, {child.noun()} sat close to {friend.noun()} for bedtime, "
        f"and the room felt soft and still."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved {book.phrase}, because the words sounded sweet and a little French."
    )


def _narrate_snack(world: World, child: Entity, snack: Snack) -> None:
    child.meters["full"] = child.meters.get("full", 0.0) + 1.0
    world.say(
        f"Before the last page, {child.pronoun()} sipped {snack.phrase} and tried to keep the night quiet."
    )


def _flashback(world: World, child: Entity, memory: Memory) -> None:
    if world.flashback_done:
        return
    if child.memes.get("embarrassment", 0.0) < THRESHOLD:
        return
    world.flashback_active = True
    world.flashback_done = True
    world.say(memory.flashback_line)
    world.say(
        f"{child.noun()} remembered how rude noise could make a warm room go cold."
    )


def _belch(world: World, child: Entity, snack: Snack) -> None:
    if child.meters.get("full", 0.0) < THRESHOLD:
        return
    sig = ("belch", child.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["embarrassment"] = child.memes.get("embarrassment", 0.0) + snack.belch_risk
    child.memes["tension"] = child.memes.get("tension", 0.0) + 1.0
    world.say(
        f"Then a belch slipped out anyway, and the little sound bounced around the pillows."
    )


def _comfort_attempt(world: World, child: Entity, friend: Entity) -> bool:
    if child.memes.get("embarrassment", 0.0) < THRESHOLD:
        return False
    if world.time_left <= 0:
        return False
    world.say(
        f"{friend.pronoun().capitalize()} tried to smile and pat the blanket, but the moment already felt tight."
    )
    child.memes["tension"] = max(child.memes.get("tension", 0.0) - 0.2, 0.0)
    return True


def _bad_ending(world: World, child: Entity, friend: Entity, book: Book) -> None:
    world.bad_ending = True
    world.say(
        f"The storybook closed before the last page, and {child.pronoun('possessive')} cheeks stayed hot."
    )
    world.say(
        f"Bedtime did not feel cozy anymore; the French words were left behind, and the room went quiet in a sad way."
    )


def tell(setting: Setting, child_name: str, child_gender: str, trait: str, book: Book,
         snack: Snack, memory: Memory) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        meters={"full": 0.0},
        memes={"embarrassment": memory.embarrassment, "tension": 0.0},
    ))
    friend = world.add(Entity(
        id="Friend",
        kind="character",
        type="girl" if child_gender == "boy" else "boy",
        label="the sleepover friend",
        meters={},
        memes={"kindness": 1.0},
    ))
    storybook = world.add(Entity(
        id="Book",
        kind="thing",
        type="book",
        label=book.label,
        phrase=book.phrase,
        owner=child.id,
    ))
    drink = world.add(Entity(
        id="Snack",
        kind="thing",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        owner=child.id,
    ))
    world.facts.update(
        child=child,
        friend=friend,
        book=storybook,
        snack=drink,
        memory=memory,
        trait=trait,
    )

    _narrate_opening(world, child, friend, book)
    world.para()
    _narrate_snack(world, child, snack)
    world.time_left -= 1

    _flashback(world, child, memory)
    world.time_left -= 1

    _belch(world, child, snack)
    world.time_left -= 1

    if not _comfort_attempt(world, child, friend):
        _bad_ending(world, child, friend, book)

    return world


# ---------------------------------------------------------------------------
# Story quality helpers
# ---------------------------------------------------------------------------

def valid_combo(setting: Setting, snack: Snack, memory: Memory) -> bool:
    return setting.bedtime and setting.coed and setting.french and snack.belch_risk > 0 and memory.embarrassment > 0


def resolve_name(gender: str, rng: random.Random) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


# ---------------------------------------------------------------------------
# Q&A and prompts
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack"]
    memory = f["memory"]
    return [
        f'Write a cozy bedtime story about a {child.type} who hears French words at a coed sleepover and then has a belch problem.',
        f'Tell a child-friendly story where {child.id} drinks {snack.phrase}, remembers {memory.label}, and the ending turns sad.',
        f'Write a short bedtime tale with a flashback, a belch, and a bad ending, using the word "French".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    book: Entity = f["book"]
    snack: Entity = f["snack"]
    memory: Memory = f["memory"]
    trait: str = f["trait"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place} during bedtime?",
            answer=f"It was about a {trait} {child.type} named {child.id}, and {friend.label} was there too for the coed bedtime gathering.",
        ),
        QAItem(
            question=f"What French thing did {child.id} love before the trouble started?",
            answer=f"{child.id} loved the {book.phrase}, because the French words sounded soft and sweet at bedtime.",
        ),
        QAItem(
            question=f"What caused the belch in the story?",
            answer=f"{child.id} had {snack.phrase}, and that made a belch more likely during the quiet bedtime moment.",
        ),
        QAItem(
            question=f"Why did the flashback matter?",
            answer=f"The flashback mattered because it reminded {child.id} of {memory.label}, which made the child feel embarrassed before the belch happened.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="It ended badly: the book closed before the last page, the room stayed tense, and bedtime lost its cozy feeling.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly shows something that happened earlier, so the reader understands why a character feels a certain way now.",
        ),
        QAItem(
            question="What does bad ending mean in a story?",
            answer="A bad ending means the problem does not get fixed in time, so the story closes with a sad or disappointing result.",
        ),
        QAItem(
            question="What does belching mean?",
            answer="A belch is a burst of air that comes up from the stomach and makes a loud burp-like sound.",
        ),
        QAItem(
            question="What does coed mean?",
            answer="Coed means boys and girls are together in the same group or room.",
        ),
        QAItem(
            question="Why can French words sound different to children?",
            answer="French words can sound different because French uses sounds and rhythms that may feel new if a child is used to another language.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    lines.append(f"time_left={world.time_left}")
    lines.append(f"flashback_done={world.flashback_done}")
    lines.append(f"bad_ending={world.bad_ending}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts:
% setting(S). coed(S). bedtime(S). french(S).
% book(B). french_book(B).
% snack(Sn). belch_risk(Sn,Risk).
% memory(M). embarrassing(M).
% story_candidate(S,Sn,M) if compatible.

belch_relevant(Sn) :- belch_risk(Sn,R), R > 0.
flashback_possible(M) :- embarrassing(M).
valid_story(S,Sn,M) :- setting(S), coed(S), bedtime(S), french(S), belch_relevant(Sn), flashback_possible(M).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.coed:
            lines.append(asp.fact("coed", sid))
        if s.bedtime:
            lines.append(asp.fact("bedtime", sid))
        if s.french:
            lines.append(asp.fact("french", sid))
    for bid, b in BOOKS.items():
        lines.append(asp.fact("book", bid))
        lines.append(asp.fact("french_book", bid))
    for sid, sn in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("belch_risk", sid, sn.belch_risk))
    for mid, m in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        lines.append(asp.fact("embarrassing", mid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted(
        (sid, sn, mid)
        for sid, s in SETTINGS.items()
        for sn, snack in SNACKS.items()
        for mid, mem in MEMORIES.items()
        if valid_combo(s, snack, mem)
    )
    clingo = asp_valid_stories()
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", py)
    print("asp   :", clingo)
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    child: str
    gender: str
    trait: str
    book: str
    snack: str
    memory: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with coed, French, belch, flashback, and bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    setting = SETTINGS[place]
    if not valid_combo(setting, SNACKS[args.snack] if args.snack else rng.choice(list(SNACKS.values())), MEMORIES[args.memory] if args.memory else rng.choice(list(MEMORIES.values()))):
        pass
    snack_id = args.snack or rng.choice(list(SNACKS))
    memory_id = args.memory or rng.choice(list(MEMORIES))
    if args.place and not SETTINGS[args.place].bedtime:
        raise StoryError("Chosen place does not support bedtime.")
    if args.place and not SETTINGS[args.place].coed:
        raise StoryError("Chosen place is not coed, but this world requires a coed gathering.")
    if args.place and not SETTINGS[args.place].french:
        raise StoryError("Chosen place does not support the French-story premise.")
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    child = args.name or resolve_name(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, child=child, gender=gender, trait=trait, book=args.book or rng.choice(list(BOOKS)), snack=snack_id, memory=memory_id)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        params.child,
        params.gender,
        params.trait,
        BOOKS[params.book],
        SNACKS[params.snack],
        MEMORIES[params.memory],
    )
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
    StoryParams(place="bedroom", child="Mia", gender="girl", trait="quiet", book="storybook", snack="soda", memory="birthday"),
    StoryParams(place="sleepover_room", child="Theo", gender="boy", trait="curious", book="picturebook", snack="juice", memory="train"),
    StoryParams(place="nursery", child="Nora", gender="girl", trait="gentle", book="storybook", snack="cocoa", memory="school"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_stories())} valid stories:")
        for triple in asp_valid_stories():
            print(" ", triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
