#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pence_inner_monologue_sound_effects_kindness_whodunit.py
=======================================================================================

A standalone story world for a tiny whodunit: a child notices a missing coin,
follows sound effects and inner monologue clues, and solves the mystery with
kindness instead of blame. The word "pence" is woven into the simulated world
so the story can end with a recovered coin and a softened room.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a frozen paragraph
- QA sets grounded in simulated world state
- Python reasonableness gates plus an inline ASP twin
- direct CLI support for default runs, -n, --all, --seed, --trace, --qa,
  --json, --asp, --verify, and --show-asp
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    role: str = ""
    label: str = ""
    traits: list[str] = field(default_factory=list)
    kindred: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.id)


@dataclass
class Room:
    id: str
    kind: str = "room"
    type: str = "room"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Coin:
    id: str
    kind: str = "thing"
    type: str = "coin"
    label: str = "a pence coin"
    material: str = "metal"
    owner: str = ""
    found_by: str = ""
    hidden_in: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Mystery:
    id: str
    clue: str
    sound: str
    inner_thought: str
    kindness_move: str
    resolution: str
    culprit: str
    hidden_place: str
    coin_label: str = "pence"
    can_be_kind: bool = True
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["mystery"] < THRESHOLD:
        return out
    if ("worry", "hero") in world.fired:
        return out
    world.fired.add(("worry", "hero"))
    hero.memes["worry"] += 1
    out.append("__thought__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["kindness"] < THRESHOLD:
        return out
    if ("soften", "room") in world.fired:
        return out
    world.fired.add(("soften", "room"))
    friend.memes["relief"] += 1
    world.get("room").meters["tension"] = 0.0
    out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("worry", "mental", _r_worry),
    Rule("soften", "social", _r_soften),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_truth(mystery: Mystery) -> bool:
    return mystery.hidden_place in {"under the table", "inside the biscuit tin", "behind the vase"}


def kind_help_is_possible(mystery: Mystery) -> bool:
    return mystery.can_be_kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room in ROOMS:
        for mystery_id, mystery in MYSTERIES.items():
            for helper in HELPERS:
                if clue_truth(mystery) and kind_help_is_possible(mystery):
                    combos.append((room, mystery_id, helper))
    return combos


def find_coin(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    coin = world.get("coin")
    clue = mystery.clue
    sound = mystery.sound
    hero.meters["mystery"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"In the little room, {hero.id} noticed that the coin dish was empty. "
        f"The missing {mystery.coin_label} was not on the shelf."
    )
    world.say(f'{" ".join([clue])} {sound}')
    world.say(
        f'{hero.id} thought, "If I were a small coin, where would I hide?" '
        f'That question tugged at {hero.pronoun("possessive")} mind like a thread.'
    )
    coin.hidden_in = mystery.hidden_place


def accuse_or_listen(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    helper = world.get("helper")
    hero.memes["suspicion"] += 1
    world.say(
        f'{hero.id} looked at {friend.id} and almost blamed {friend.pronoun("object")}, '
        f'but the tiny "tick-tick" sound made {hero.id} pause.'
    )
    world.say(
        f'Inside {hero.pronoun("possessive")} head, {mystery.inner_thought} '
        f'kept repeating until {hero.id} decided to look more kindly.'
    )
    if helper.id:
        world.say(
            f'{helper.id} said, "Let us check together." '
            f'That gentle voice made the room feel less sharp.'
        )


def trace_clue(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    coin = world.get("coin")
    room = world.get("room")
    hero.meters["investigation"] += 1
    world.say(
        f'{hero.id} knelt down and listened. "Tap... tap... rustle..." '
        f'The sound came from {coin.hidden_in}.'
    )
    world.say(
        f'{" " if False else ""}{hero.id} reached carefully, and there it was: '
        f'{coin.label}, tucked away where nobody had expected.'
    )
    room.meters["tension"] += 0.0


def kindness_end(world: World, mystery: Mystery) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    helper = world.get("helper")
    coin = world.get("coin")
    hero.memes["kindness"] += 1
    friend.memes["gratitude"] += 1
    coin.meters["recovered"] = 1.0
    world.say(
        f'{hero.id} did not scold anyone. Instead, {hero.id} smiled and said, '
        f'"It is all right. We found it."'
    )
    world.say(
        f'The {mystery.coin_label} went back to the dish, and {friend.id} gave '
        f'{hero.pronoun("object")} a warm little grin.'
    )
    world.say(
        f'For the last clue, {hero.id} heard only a soft "clink" as the room '
        f'became calm again.'
    )


def tell(room: str, mystery: Mystery, hero_name: str = "Ivy", friend_name: str = "Milo",
         helper_name: str = "Mrs. Pine") -> World:
    world = World()
    room_ent = world.add(Room("room", label=room))
    hero = world.add(Person("hero", type="girl", role="detective", label=hero_name))
    friend = world.add(Person("friend", type="boy", role="witness", label=friend_name))
    helper = world.add(Person("helper", type="mother", role="helper", label=helper_name))
    coin = world.add(Coin("coin"))
    dish = world.add(ObjectThing("dish", label="coin dish"))
    mystery_obj = world.add(ObjectThing("mystery", label=mystery.id))

    room_ent.meters["tension"] = 0.0
    hero.memes["kindness"] = 0.0
    hero.memes["mystery"] = 0.0
    world.facts["room"] = room
    world.facts["mystery"] = mystery
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["helper"] = helper
    world.facts["coin"] = coin
    world.facts["dish"] = dish
    world.facts["mystery_obj"] = mystery_obj

    world.say(
        f'{hero.id} loved solving little mysteries. On a quiet afternoon, '
        f'{hero.id}, {friend.id}, and {helper.id} sat by the coin dish.'
    )
    world.say(
        f'Then {hero.id} noticed the missing {mystery.coin_label}. '
        f'That was when the whodunit began.'
    )
    world.para()
    find_coin(world, mystery)
    accuse_or_listen(world, mystery)
    world.para()
    trace_clue(world, mystery)
    kindness_end(world, mystery)
    propagate(world, narrate=False)

    world.facts["outcome"] = "found"
    world.facts["coin_place"] = mystery.hidden_place
    return world


ROOMS = {
    "kitchen": "the kitchen",
    "parlor": "the parlor",
    "schoolroom": "the schoolroom",
}

MYSTERIES = {
    "biscuit_tin": Mystery(
        "biscuit_tin",
        clue="From the kitchen came a faint",
        sound="clang! clink!",
        inner_thought="Maybe it rolled, maybe it was tucked away, maybe someone hid it by mistake",
        kindness_move="look kindly",
        resolution="the coin was found in the tin",
        culprit="no culprit at all",
        hidden_place="inside the biscuit tin",
        tags={"coin", "sound", "kindness"},
    ),
    "table_underside": Mystery(
        "table_underside",
        clue="Under the table there was a tiny",
        sound="scritch-scritch!",
        inner_thought="A soft sound usually means a soft hiding place",
        kindness_move="check together",
        resolution="the coin was under the table",
        culprit="a distracted pocket",
        hidden_place="under the table",
        tags={"coin", "sound", "kindness"},
    ),
    "vase_behind": Mystery(
        "vase_behind",
        clue="Near the window came a little",
        sound="clink... tap...",
        inner_thought="The answer is probably close, not far away",
        kindness_move="share the search",
        resolution="the coin was behind the vase",
        culprit="the shelf",
        hidden_place="behind the vase",
        tags={"coin", "sound", "kindness"},
    ),
}

HELPERS = ["Mila", "Noah", "Pip", "June"]


@dataclass
class StoryParams:
    room: str
    mystery: str
    helper: str
    hero: str
    friend: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit with kindness, inner monologue, and sound effects.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
    if args.mystery and not clue_truth(MYSTERIES[args.mystery]):
        raise StoryError("No story: the mystery does not offer a real clue trail.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, mystery, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Ivy", "Nina", "Ada", "Mara"])
    friend = args.friend or rng.choice(["Milo", "Otis", "Ben", "Toby"])
    return StoryParams(room, mystery, helper, hero, friend)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = f["mystery"]
    return [
        f'Write a whodunit story for a 3-to-5-year-old that includes the word "{m.coin_label}".',
        f"Tell a gentle mystery where {f['hero'].id} follows a sound clue, hears an inner thought, and solves the missing-coin problem kindly.",
        f"Write a story with sound effects and kindness where a child searches for {m.coin_label} and finds it without blaming anyone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    mystery = f["mystery"]
    coin = f["coin"]
    return [
        QAItem(
            question="What was missing at the start of the story?",
            answer=f"The missing thing was {coin.label}. That was the little mystery that made everyone look around."
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f'A small sound effect helped: {mystery.sound} and the other tiny noises led {hero.id} to the hiding place. The clue mattered because it pointed to {mystery.hidden_place}.'
        ),
        QAItem(
            question="How did the detective act toward the other child?",
            answer=f"{hero.id} acted kindly and did not scold {friend.id}. That kindness made the search feel safe, and it helped the answer come out gently."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does pence mean here?",
            answer="Pence is a small coin. In this story, a pence coin is the little treasure that went missing and then was found again."
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where someone tries to figure out what happened. The fun is in following clues until the answer appears."
        ),
        QAItem(
            question="Why are sound effects useful in a mystery?",
            answer="Sound effects can point to where something is hiding or happening. A tiny rustle or clink can be a clue when eyes are not enough."
        ),
        QAItem(
            question="Why is kindness useful in a mystery?",
            answer="Kindness keeps people calm and willing to help. When nobody feels blamed, it is easier to search together and find the truth."
        ),
    ]


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
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({getattr(e, 'type', ''):8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
real_clue(M) :- mystery(M), clue_ok(M).
kind_story(M) :- real_clue(M), can_be_kind(M).
valid(R, M, H) :- room(R), mystery(M), helper(H), kind_story(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if clue_truth(m):
            lines.append(asp.fact("clue_ok", mid))
        if m.can_be_kind:
            lines.append(asp.fact("can_be_kind", mid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams("kitchen", "biscuit_tin", "Mila", "Ivy", "Milo"),
    StoryParams("parlor", "table_underside", "Noah", "Nina", "Ben"),
    StoryParams("schoolroom", "vase_behind", "Pip", "Ada", "Otis"),
]


def tell(params: StoryParams) -> World:
    world = World()
    room = world.add(Entity("room", kind="room", type="room", label=ROOMS[params.room]))
    hero = world.add(Person("hero", type="girl", role="detective", label=params.hero))
    friend = world.add(Person("friend", type="boy", role="witness", label=params.friend))
    helper = world.add(Person("helper", type="mother", role="helper", label=params.helper))
    coin = world.add(Coin("coin"))
    world.add(ObjectThing("dish", label="coin dish"))
    mystery = MYSTERIES[params.mystery]

    world.facts.update(room=params.room, hero=hero, friend=friend, helper=helper, coin=coin, mystery=mystery)
    room.meters["tension"] = 1.0
    hero.memes["kindness"] = 0.0

    world.say(
        f"{hero.id} loved tiny mysteries. On a quiet afternoon, {hero.id}, {friend.id}, and {helper.id} "
        f"looked at the coin dish together."
    )
    world.say(
        f"Then {hero.id} noticed the missing pence. The dish was empty, and the question felt bright in the room."
    )
    world.para()
    find_coin(world, mystery)
    accuse_or_listen(world, mystery)
    world.para()
    trace_clue(world, mystery)
    kindness_end(world, mystery)

    world.facts["outcome"] = "found"
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny whodunit storyworld with inner monologue, sound effects, and kindness.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
