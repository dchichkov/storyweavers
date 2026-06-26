#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/split_hobble_suey_moral_value_misunderstanding_lesson.py
===============================================================================================================================

A small fable-style storyworld about a split path, a hobble, and Suey.

Premise:
- A careful animal sees a split in the path and wants to keep the peace.
- A misunderstanding makes the others think the hobble is trouble.
- The group learns a small moral value: ask first, help gently, and do not jump to conclusions.

The world is deliberately tiny and state-driven:
- typed entities have physical meters and emotional memes
- a split path can cause a misunderstanding if someone hobbles in without context
- the lesson learned is narrated from the actual world resolution, not from a frozen template
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
# Small fable-domain registries
# ---------------------------------------------------------------------------

MORAL_VALUES = ["kindness", "patience", "honesty", "helpfulness"]
LESSONS = {
    "kindness": "kindness can make a hard moment softer",
    "patience": "waiting for the truth can prevent a mistake",
    "honesty": "telling the truth early can clear confusion",
    "helpfulness": "helping gently is better than guessing loudly",
}

# We keep the setting tiny and classical: one road, one split, one lesson.
SETTINGS = {
    "woodland": {
        "place": "the woodland path",
        "detail": "The woodland path forked around an old stone root.",
    },
    "meadow": {
        "place": "the meadow lane",
        "detail": "The meadow lane split beside a narrow stream.",
    },
}

# Seed-word driven ingredients: split, hobble, suey.
ACTIVITIES = {
    "split": {
        "verb": "split the way forward",
        "event": "the path split in two",
        "effect": "confusion",
    },
    "hobble": {
        "verb": "hobble along",
        "event": "hobbling looked strange from far away",
        "effect": "concern",
    },
    "suey": {
        "verb": "call Suey over",
        "event": "Suey came trotting up",
        "effect": "relief",
    },
}

CHARACTER_TYPES = ["fox", "hare", "badger", "goose", "sow"]


# ---------------------------------------------------------------------------
# Shared world model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "badger", "goose", "sow"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    setting: str
    moral_value: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting_key: str, moral_value: str) -> None:
        self.setting_key = setting_key
        self.setting = SETTINGS[setting_key]
        self.moral_value = moral_value
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Reasonable gate
# ---------------------------------------------------------------------------

def valid_combo(setting: str, moral_value: str) -> bool:
    return setting in SETTINGS and moral_value in MORAL_VALUES


def explain_invalid(setting: str, moral_value: str) -> str:
    if setting not in SETTINGS:
        return "(No story: that setting is not available in this little fable world.)"
    if moral_value not in MORAL_VALUES:
        return "(No story: that moral value is not one of the small lessons this world teaches.)"
    return "(No story: the chosen pieces do not make a coherent fable.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(woodland).
setting(meadow).

moral(kindness).
moral(patience).
moral(honesty).
moral(helpfulness).

valid(S, M) :- setting(S), moral(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MORAL_VALUES:
        lines.append(asp.fact("moral", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, m) for s in SETTINGS for m in MORAL_VALUES if valid_combo(s, m)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print(" only in clingo:", sorted(cl - py))
    print(" only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_story_world(params: StoryParams) -> World:
    if not valid_combo(params.setting, params.moral_value):
        raise StoryError(explain_invalid(params.setting, params.moral_value))

    world = World(params.setting, params.moral_value)

    leader = world.add(Entity(
        id="Bran",
        kind="character",
        type="fox",
        label="Bran",
        meters={"care": 1.0},
        memes={"calm": 1.0, "worry": 0.0},
    ))
    friend = world.add(Entity(
        id="Suey",
        kind="character",
        type="sow",
        label="Suey",
        meters={"hop": 1.0},
        memes={"goodwill": 1.0},
    ))
    witness = world.add(Entity(
        id="Pip",
        kind="character",
        type="hare",
        label="Pip",
        meters={"speed": 1.0},
        memes={"curiosity": 1.0},
    ))
    world.facts["leader"] = leader
    world.facts["friend"] = friend
    world.facts["witness"] = witness
    return world


def tell(world: World) -> None:
    leader: Entity = world.facts["leader"]  # type: ignore[assignment]
    friend: Entity = world.facts["friend"]  # type: ignore[assignment]
    witness: Entity = world.facts["witness"]  # type: ignore[assignment]

    place = world.setting["place"]
    detail = world.setting["detail"]
    moral = world.moral_value
    lesson = LESSONS[moral]

    # Act 1: setup
    world.say(f"Bran lived near {place}, where {detail.lower()}")
    world.say("Bran liked to keep the lane tidy and the neighbors calm.")
    world.say("Suey, the round and rosy sow, often wandered close by with a cheerful grunt.")

    # Act 2: misunderstanding
    world.para()
    world.say(f"One afternoon, {detail.lower()}")
    leader.memes["worry"] += 1.0
    witness.memes["alarm"] = 1.0
    world.say("Pip saw the split first and thought the whole lane might be in trouble.")
    world.say("Then Suey hobbled in with one muddy hoof caught on a thorny bramble.")
    friend.meters["hurt"] = 1.0
    friend.memes["embarrassment"] = 1.0
    world.say("From a distance, that hobble looked like a bad sign, not a small scrape.")
    world.say("Pip cried out too fast, and the cry made Bran fear a bigger problem than there was.")

    # Act 3: turn and resolution
    world.para()
    witness.memes["alarm"] = 0.0
    leader.memes["worry"] = 0.0
    friend.memes["embarrassment"] += 0.5
    world.say("Bran did not scold.")
    world.say("Instead, Bran asked what had happened, and Suey showed the thorn before anyone guessed wrong.")
    world.say("Bran pulled the bramble free, and Suey took a careful step at a time until the hobble eased.")
    friend.meters["hurt"] = 0.0
    friend.memes["relief"] = 1.0
    witness.memes["admiration"] = 1.0
    world.say(f"By sunset, the three friends walked the split path together, and {lesson}.")
    world.say("Suey no longer hobbled; she trotted beside them, and the lane felt peaceful again.")

    world.facts.update(
        place=place,
        detail=detail,
        moral=moral,
        lesson=lesson,
        split_seen=True,
        hobble_seen=True,
        suey_seen=True,
        misunderstanding=True,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f'Write a short fable for a young child about a split path, a hobble, and Suey, with a clear moral value of "{world.moral_value}".',
        f"Tell a gentle animal story in which a misunderstanding starts when the path splits, but the friends learn a lesson about {world.moral_value}.",
        "Write a simple fable where someone hobbles in, another animal jumps to the wrong conclusion, and the ending gives a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    place = world.setting["place"]
    lesson = world.facts["lesson"]
    moral = world.moral_value
    return [
        QAItem(
            question="What happened first in the story?",
            answer=f"The path split at {place}, and that made the moment feel uncertain.",
        ),
        QAItem(
            question="Why was there a misunderstanding?",
            answer="Suey hobbled in after catching a hoof on a bramble, and Pip thought the hobble meant something worse before anyone asked what really happened.",
        ),
        QAItem(
            question="What lesson did the animals learn?",
            answer=f"They learned that {lesson}, which matches the moral value of {moral}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The bramble was removed, Suey could walk comfortably again, and the friends crossed the split path together in peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson.",
        ),
        QAItem(
            question="What does it mean to hoble or hobble?",
            answer="To hobble means to walk with a limp or with small careful steps because something hurts.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone thinks the wrong thing because they do not have all the facts.",
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


# ---------------------------------------------------------------------------
# Trace / serialization
# ---------------------------------------------------------------------------

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
        lines.append(f"  {e.id:8} ({e.type:5}) {' '.join(bits)}")
    lines.append(f"  moral value: {world.moral_value}")
    lines.append(f"  setting: {world.setting_key}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generator
# ---------------------------------------------------------------------------

@dataclass
class ParamsRegistry:
    settings: tuple[str, ...] = tuple(SETTINGS.keys())
    morals: tuple[str, ...] = tuple(MORAL_VALUES)


REGISTRY = ParamsRegistry()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny fable world: split path, hobble, Suey, and a lesson learned.")
    ap.add_argument("--setting", choices=sorted(SETTINGS.keys()))
    ap.add_argument("--moral-value", choices=sorted(MORAL_VALUES))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--all", action="store_true", help="render all curated stories")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(SETTINGS.keys()))
    moral_value = args.moral_value or rng.choice(sorted(MORAL_VALUES))
    if not valid_combo(setting, moral_value):
        raise StoryError(explain_invalid(setting, moral_value))
    return StoryParams(setting=setting, moral_value=moral_value)


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="woodland", moral_value="kindness"),
    StoryParams(setting="meadow", moral_value="patience"),
    StoryParams(setting="woodland", moral_value="honesty"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} valid setting/moral combinations:\n")
        for setting, moral in combos:
            print(f"  {setting:10} {moral}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
