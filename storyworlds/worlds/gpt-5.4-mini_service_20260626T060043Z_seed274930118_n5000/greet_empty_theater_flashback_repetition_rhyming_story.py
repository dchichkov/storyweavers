#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/greet_empty_theater_flashback_repetition_rhyming_story.py
===============================================================================================================================

A tiny storyworld about a child in an empty theater.

Seed impression:
- A child steps into an empty theater, greets it, and hears the echo.
- A flashback shows the same theater full of people and applause.
- Repetition turns a lonely hall into a friendly place.
- The story should feel like a rhyming story: light, lyrical, and concrete.

This script keeps a small simulated world model with physical meters and emotional memes.
The prose is driven by state changes, not by a frozen template swap.
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
# World entities
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    empty: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    line: str
    rhyme_line: str
    flashback_line: str
    echo_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    owner_role: str = "caretaker"


@dataclass
class StoryParams:
    setting: str
    mood: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.history.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.history = list(self.history)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "empty_theater": Setting(place="the empty theater", empty=True, affords={"greet"}),
}

MOODS = {
    "soft_echo": Mood(
        id="soft_echo",
        line="She greeted the empty theater with a tiny hello.",
        rhyme_line="Hello, hello, the hall said so low.",
        flashback_line="Then she remembered a brighter time, when the seats were full in a happy line.",
        echo_line="Her greeting bounced back, neat and sweet, like little tap shoes on dancer feet.",
        tags={"greet", "empty", "theater", "flashback", "repetition", "rhyme"},
    ),
}

PRIZES = {
    "program": Prize(
        id="program",
        label="old play program",
        phrase="a folded play program with gold stars",
        type="paper",
    ),
    "bouquet": Prize(
        id="bouquet",
        label="paper bouquet",
        phrase="a paper bouquet tied with blue ribbon",
        type="paper",
    ),
}

NAMES = {
    "girl": ["Maya", "Nia", "Lila", "Sora", "Mina"],
    "boy": ["Theo", "Eli", "Noah", "Ben", "Arin"],
}

TRAITS = ["brave", "gentle", "curious", "bright", "cheery"]

# ---------------------------------------------------------------------------
# Storyworld model
# ---------------------------------------------------------------------------


def _bump(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.meters.get("traits", [])), "small")
    world.say(f"{child.id} was a little {trait} {child.type} who loved soft words and bright spots.")


def enter_theater(world: World, child: Entity) -> None:
    _bump(child, "steps", 1)
    _bump_meme(child, "wonder", 1)
    world.say(f"One quiet evening, {child.id} stepped into {world.setting.place}.")
    if world.setting.empty:
        _bump(world.get("theater"), "empty", 1)
        _bump_meme(world.get("theater"), "stillness", 1)
        world.say("The seats were empty, and the stage sat still in the dark.")


def greet_theater(world: World, child: Entity) -> None:
    theater = world.get("theater")
    _bump_meme(child, "courage", 1)
    _bump(theater, "echo", 1)
    world.say("She lifted a hand and said, 'Hello, theater, hello.'")
    world.say("The empty hall did not answer at first, but the walls held the sound and sent it back.")
    _bump_meme(theater, "echoing", 1)


def flashback(world: World, child: Entity) -> None:
    theater = world.get("theater")
    _bump_meme(child, "memory", 1)
    _bump(theater, "memory", 1)
    world.say("Then came a flashback, warm as a lantern glow.")
    world.say(
        "She remembered the theater full of clapping hands, shining shoes, and a curtain that swayed like a boat."
    )
    world.say("She remembered bows, bouquets, and the big cheer that rolled through the rows.")


def repeat_greeting(world: World, child: Entity) -> None:
    theater = world.get("theater")
    _bump_meme(child, "joy", 1)
    _bump_meme(child, "bravery", 1)
    _bump(theater, "echo", 1)
    world.say("So she tried again, and again, and again: 'Hello, hello, hello!'")
    world.say("The words came back like bells, bright and small, and the empty theater felt less empty at all.")


def resolve(world: World, child: Entity, prize: Entity) -> None:
    _bump_meme(child, "love", 1)
    _bump(world.get("theater"), "warmth", 1)
    world.say(
        f"At last, {child.id} placed {child.pronoun('possessive')} {prize.label} on the front seat as a little gift to the quiet room."
    )
    world.say(
        "The theater still held its hush, but now it felt kind, like it was waiting for tomorrow's shine."
    )
    world.say(
        f"{child.id} smiled and whispered, 'Hello again, theater,' and the echo smiled back through the air."
    )


def tell(setting: Setting, mood: Mood, prize_cfg: Prize, name: str, gender: str, parent: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    theater = world.add(Entity(id="theater", type="theater", label="theater"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=child.id))
    parent_ent = world.add(Entity(id="parent", kind="character", type=parent, label=parent))

    child.meters["traits"] = [random.choice(TRAITS)]
    child.memes["softness"] = 1
    world.facts.update(child=child, theater=theater, prize=prize, parent=parent_ent, mood=mood)

    introduce(world, child)
    world.say(mood.line)
    world.para()

    enter_theater(world, child)
    greet_theater(world, child)
    world.para()

    flashback(world, child)
    repeat_greeting(world, child)
    resolve(world, child, prize)

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(setting_key: str, mood_key: str, prize_key: str, gender: str) -> bool:
    setting = SETTINGS.get(setting_key)
    mood = MOODS.get(mood_key)
    prize = PRIZES.get(prize_key)
    if not setting or not mood or not prize:
        return False
    if setting_key != "empty_theater":
        return False
    if "greet" not in setting.affords:
        return False
    if gender not in {"girl", "boy"}:
        return False
    return True


def explain_rejection(setting_key: str, mood_key: str, prize_key: str, gender: str) -> str:
    if setting_key != "empty_theater":
        return "(No story: this tale only works in the empty theater.)"
    if prize_key not in PRIZES:
        return "(No story: the prize choice is not part of this theater world.)"
    return "(No story: these choices do not make a gentle greet-and-echo story.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    mood = f["mood"]
    prize = f["prize"]
    return [
        f'Write a short rhyming story for a young child about {child.id} greeting an empty theater.',
        f"Tell a gentle story where {child.id} goes into the empty theater, remembers a flashback, and repeats a hello.",
        f'Write a simple rhyme that includes the words "greet," "empty," and "theater," and ends with a warm echo.',
        f"Write a story where a {child.type} named {child.id} feels alone for a moment, then braver after hearing an echo.",
        f"Tell a child-friendly story about {child.id}, {mood.id}, and {prize.label} in an empty theater.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    prize: Entity = f["prize"]
    theater: Entity = f["theater"]
    mood: Mood = f["mood"]

    return [
        QAItem(
            question=f"What did {child.id} do when {child.id} entered the empty theater?",
            answer=f"{child.id} greeted the empty theater with a soft hello, and the sound came back as an echo.",
        ),
        QAItem(
            question=f"What did {child.id} remember in the flashback?",
            answer="She remembered the theater full of applause, bright seats, and happy bows on stage.",
        ),
        QAItem(
            question=f"What did {child.id} repeat to make the empty hall feel warmer?",
            answer="She repeated 'Hello, hello, hello!' until the words bounced around the room like tiny bells.",
        ),
        QAItem(
            question=f"What did {child.id} place on the front seat at the end?",
            answer=f"{child.id} placed {child.pronoun('possessive')} {prize.label} on the front seat as a small gift to the quiet theater.",
        ),
        QAItem(
            question=f"How did the theater feel by the end of the story?",
            answer="It was still quiet, but it felt warm, friendly, and ready for tomorrow.",
        ),
        QAItem(
            question=f"Why is this a rhyming story?",
            answer="It uses repeated sounds and lines like hello, echo, and glow, so the story feels musical and light.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off walls or rocks and comes back to you.",
        ),
        QAItem(
            question="What is a theater?",
            answer="A theater is a place where people sit and watch plays, music, or dancing.",
        ),
        QAItem(
            question="What does empty mean?",
            answer="Empty means there is nobody or almost nothing inside a place.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from earlier, like a memory.",
        ),
        QAItem(
            question="Why do people repeat words in a poem or story?",
            answer="People repeat words to make the lines sound playful, musical, and easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid_story(S, M, P, G) :- setting(S), mood(M), prize(P), gender(G),
                           can_greet(S), empty_theater(S),
                           works_together(S, M, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.empty:
            lines.append(asp.fact("empty_theater", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("can_greet", sid))
            lines.append(asp.fact("affords", sid, a))
    for mid in MOODS:
        lines.append(asp.fact("mood", mid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for sid in SETTINGS:
        for mid in MOODS:
            for pid in PRIZES:
                lines.append(asp.fact("works_together", sid, mid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (s, m, p, g)
        for s in SETTINGS
        for m in MOODS
        for p in PRIZES
        for g in ["girl", "boy"]
        if valid_story(s, m, p, g)
    }
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_story():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about greeting an empty theater.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    setting = args.setting or "empty_theater"
    mood = args.mood or "soft_echo"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if not valid_story(setting, mood, prize, gender):
        raise StoryError(explain_rejection(setting, mood, prize, gender))
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(NAMES[gender])
    return StoryParams(setting=setting, mood=mood, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MOODS[params.mood], PRIZES[params.prize], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s, m, p, g in stories:
            print(f"  {s:14} {m:10} {p:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(setting="empty_theater", mood="soft_echo", prize=pid, name="Maya", gender="girl", parent="mother")
            for pid in PRIZES
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples: list[StorySample] = []
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

    for i, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
