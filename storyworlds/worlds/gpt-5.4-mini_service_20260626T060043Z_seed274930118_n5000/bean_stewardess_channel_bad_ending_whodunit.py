#!/usr/bin/env python3
"""
storyworlds/worlds/bean_stewardess_channel_bad_ending_whodunit.py
=================================================================

A small whodunit story world with a bad ending.

Premise:
- A child detective boards a modest flight.
- A stewardess finds a strange bean in the cabin.
- The radio channel crackles with hints, but the clues are slippery.
- Someone is suspected, but the case ends wrong.

This world is built to tell a compact mystery with a clear clue trail,
a tense questioning middle, and a bad ending where the truth does not
get properly settled.

The seed words are preserved in the world model and prose:
bean, stewardess, channel.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "stewardess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cabin"
    channel: str = "the radio channel"
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_type: str
    stewardess_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "cabin": Setting(place="the cabin", channel="the radio channel", affords={"search"}),
    "galley": Setting(place="the galley", channel="the intercom channel", affords={"search"}),
    "lounge": Setting(place="the waiting lounge", channel="the announcement channel", affords={"search"}),
}

DETECTIVES = {
    "lena": ("Lena", "girl"),
    "milo": ("Milo", "boy"),
    "nora": ("Nora", "girl"),
}

STEWARDESSES = ["Ada", "Iris", "June", "Mina"]

# The clue is always a bean, but its context changes.
CLUE_BEAN = {
    "plain": "a lone bean",
    "soup": "a bean from a soup cup",
    "tray": "a bean on a tray",
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the setting has a channel and the clue is a bean.
valid_story(S, D, St) :- setting(S), detective(D), stewardess(St), has_channel(S), has_bean_clue(S).

% The bad ending is encoded by an unresolved case.
bad_ending(S) :- valid_story(S, _, _), unresolved(S).

% The detective suspects the stewardess when the bean is found near the channel.
suspect(St) :- valid_story(_, _, St).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("has_channel", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for did in DETECTIVES:
        lines.append(asp.fact("detective", did))
    for st in STEWARDESSES:
        lines.append(asp.fact("stewardess", st))
    lines.append(asp.fact("has_bean_clue", "cabin"))
    lines.append(asp.fact("has_bean_clue", "galley"))
    lines.append(asp.fact("has_bean_clue", "lounge"))
    lines.append(asp.fact("unresolved", "cabin"))
    lines.append(asp.fact("unresolved", "galley"))
    lines.append(asp.fact("unresolved", "lounge"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def _search(world: World, detective: Entity, stewardess: Entity, clue: Entity) -> None:
    detective.meme["curiosity"] += 1
    stewardess.meme["worry"] += 1
    world.say(
        f"{detective.id} noticed something small near {world.setting.channel}: "
        f"{clue.phrase}."
    )
    world.say(
        f"{stewardess.id} frowned and said she had seen it too, but the bean had already been moved once."
    )

def _question(world: World, detective: Entity, stewardess: Entity, clue: Entity) -> None:
    detective.meme["suspicion"] += 1
    stewardess.meme["nervous"] += 1
    world.say(
        f"{detective.id} asked who had touched {clue.id}, and the answer was only a crackle from {world.setting.channel}."
    )
    world.say(
        f"{stewardess.id} listened carefully, but the channel gave back nothing useful."
    )

def _accuse(world: World, detective: Entity, stewardess: Entity, clue: Entity) -> None:
    detective.meme["certainty"] += 1
    world.say(
        f"{detective.id} decided the stewardess must know more, because she was standing closest when the bean was found."
    )

def _bad_ending(world: World, detective: Entity, stewardess: Entity, clue: Entity) -> None:
    detective.meme["regret"] += 1
    stewardess.meme["hurt"] += 1
    world.say(
        f"But the case ended before anyone proved it. The bean was swept away, the channel went quiet, and {stewardess.id} walked off looking sad."
    )
    world.say(
        f"{detective.id} stared at the empty spot and knew the mystery was not truly solved."
    )

def tell(setting: Setting, detective_name: str, detective_type: str, stewardess_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type))
    stewardess = world.add(Entity(id=stewardess_name, kind="character", type="stewardess"))
    clue = world.add(Entity(id="bean", kind="thing", type="bean", label="bean", phrase=CLUE_BEAN["plain"]))

    world.say(
        f"{detective.id} was a little {detective.type} who liked solving tiny mysteries."
    )
    world.say(
        f"On a quiet day in {setting.place}, {stewardess.id} was the stewardess in charge of {setting.channel}."
    )
    world.say(
        f"Then someone found {clue.phrase} near the seats, and everyone went still."
    )

    world.para()
    _search(world, detective, stewardess, clue)
    _question(world, detective, stewardess, clue)
    _accuse(world, detective, stewardess, clue)

    world.para()
    _bad_ending(world, detective, stewardess, clue)

    world.facts.update(
        detective=detective,
        stewardess=stewardess,
        clue=clue,
        setting=setting,
        unresolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child about a bean, a stewardess, and a {f["setting"].channel}.',
        f"Tell a mystery story where {f['detective'].id} suspects {f['stewardess'].id}, but the case ends badly.",
        "Write a simple bad-ending mystery with a small clue and a quiet final scene.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    stewardess: Entity = f["stewardess"]
    clue: Entity = f["clue"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is trying to solve the mystery in {setting.place}?",
            answer=f"{detective.id} is trying to solve the mystery in {setting.place}.",
        ),
        QAItem(
            question=f"What strange clue did they find near {setting.channel}?",
            answer=f"They found {clue.phrase}, which was a tiny clue that made everyone wonder what had happened.",
        ),
        QAItem(
            question=f"Why did {detective.id} look at {stewardess.id} so closely?",
            answer=f"{detective.id} thought {stewardess.id} knew something because she was the stewardess closest to the clue when it was found.",
        ),
        QAItem(
            question="Did the mystery get solved?",
            answer="No. The story ends with the case still unresolved, which makes it a bad ending.",
        ),
    ]

def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stewardess?",
            answer="A stewardess is a worker on a plane or in a travel place who helps passengers stay safe and comfortable.",
        ),
        QAItem(
            question="What is a channel?",
            answer="A channel is a path for sound or messages, like a radio channel or an intercom channel.",
        ),
        QAItem(
            question="What is a bean?",
            answer="A bean is a small seed or food that can be cooked and eaten.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meter={e.meter} meme={e.meme}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parser / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit world about a bean, a stewardess, and a channel.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--detective-name", choices=[v[0] for v in DETECTIVES.values()])
    ap.add_argument("--stewardess-name", choices=STEWARDESSES)
    ap.add_argument("--detective-type", choices=["girl", "boy"])
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
    detective_name, detective_type = rng.choice(list(DETECTIVES.values()))
    if args.detective_name:
        detective_name = args.detective_name
    if args.detective_type:
        detective_type = args.detective_type
    stewardess_name = args.stewardess_name or rng.choice(STEWARDESSES)
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_type=detective_type,
        stewardess_name=stewardess_name,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.detective_name, params.detective_type, params.stewardess_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
# ASP verification
# ---------------------------------------------------------------------------

def asp_verify() -> int:
    import asp
    expected = set()
    for sid in SETTINGS:
        expected.add((sid, "lena", "Ada"))
        expected.add((sid, "milo", "Ada"))
        expected.add((sid, "nora", "Ada"))
    actual = set(asp_valid_stories())
    if actual == expected:
        print(f"OK: clingo gate matches expected story space ({len(actual)} stories).")
        return 0
    print("MISMATCH between clingo and expected story space:")
    print("  only in clingo:", sorted(actual - expected))
    print("  only in python:", sorted(expected - actual))
    return 1


def asp_show() -> str:
    return asp_program("#show valid_story/3.")

def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid mystery stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            params = StoryParams(
                setting=setting,
                detective_name="Lena",
                detective_type="girl",
                stewardess_name=STEWARDESSES[0],
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
