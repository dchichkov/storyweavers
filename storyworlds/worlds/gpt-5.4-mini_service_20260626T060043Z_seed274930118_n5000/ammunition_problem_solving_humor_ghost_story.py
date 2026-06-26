#!/usr/bin/env python3
"""
A standalone story world for a gentle ghost-story flavored problem-solving tale.

Premise:
- A child or small keeper explores a spooky place at night.
- A rattling ghost keeps making trouble around an old ammunition crate.
- The hero uses careful problem solving, help, and humor to solve the problem.
- The ending proves the world changed: the ghost is calm, the crate is safe, and
  the place feels less scary.

This script follows the Storyweavers world contract:
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- uses StorySample / QAItem / StoryError from storyworlds.results
- includes an inline ASP twin and a Python reasonableness gate
- supports --verify, --asp, --show-asp, --json, --qa, --trace, --all, -n, --seed
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
# Registries
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Setting:
    key: str
    place: str
    dim: str
    has_moonlight: bool = False
    has_echoes: bool = False


@dataclass(frozen=True)
class Problem:
    key: str
    trouble: str
    spooky_sound: str
    twist: str
    clue: str
    ask: str
    fix: str
    humor: str
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    phrase: str
    hold_kind: str
    plural: bool = False


@dataclass(frozen=True)
class Ghost:
    key: str
    name: str
    vibe: str
    joke_style: str
    whisper: str


SETTINGS = {
    "shed": Setting("shed", "the garden shed", "tiny", has_moonlight=True, has_echoes=True),
    "attic": Setting("attic", "the old attic", "narrow", has_moonlight=False, has_echoes=True),
    "museum": Setting("museum", "the small museum storeroom", "quiet", has_moonlight=False, has_echoes=False),
    "boathouse": Setting("boathouse", "the creaky boathouse", "drafty", has_moonlight=True, has_echoes=True),
}

PROBLEMS = {
    "rattle": Problem(
        key="rattle",
        trouble="the metal crate kept rattling by itself",
        spooky_sound="clink-clink-clatter",
        twist="every time it shook, the candle flame jumped",
        clue="a loose latch was tapping the crate wall",
        ask="How can we make the crate stop rattling without breaking it?",
        fix="tie the latch down and pad the corners",
        humor="the crate sounded like it had tiny teeth chattering",
        tags=("noise", "metal"),
    ),
    "echo": Problem(
        key="echo",
        trouble="every footstep came back as a spooky echo",
        spooky_sound="tap... tap... tap...",
        twist="the echo made the room sound full of invisible helpers",
        clue="the walls were round and empty, so the sound bounced around",
        ask="How can we make the room less spooky and easier to hear?",
        fix="hang cloth and speak softly near the doorway",
        humor="the echo copied the hero so many times it sounded bossy",
        tags=("sound", "room"),
    ),
    "shadow": Problem(
        key="shadow",
        trouble="a long shadow kept looking like a ghost",
        spooky_sound="whooosh",
        twist="the shadow wiggled whenever the lamp moved",
        clue="the coat rack was making the strange shape",
        ask="How can we show everyone the shadow is only a trick?",
        fix="move the lamp and point to the real coat rack",
        humor="the coat rack was trying very hard to be a monster and failing",
        tags=("light", "shape"),
    ),
}

ITEMS = {
    "ammunition_crate": Item(
        key="ammunition_crate",
        label="ammunition crate",
        phrase="an old ammunition crate",
        hold_kind="crate",
        plural=False,
    ),
    "blankets": Item(
        key="blankets",
        label="blankets",
        phrase="a stack of warm blankets",
        hold_kind="cloth",
        plural=True,
    ),
    "rope": Item(
        key="rope",
        label="rope",
        phrase="a coil of rope",
        hold_kind="rope",
        plural=False,
    ),
    "lantern": Item(
        key="lantern",
        label="lantern",
        phrase="a small lantern",
        hold_kind="light",
        plural=False,
    ),
}

GHOSTS = {
    "milo": Ghost("milo", "Milo", "friendly", "goofy", "boo?"),
    "maggie": Ghost("maggie", "Maggie", "lonely", "dry", "oh dear"),
    "pip": Ghost("pip", "Pip", "jumpy", "tiny", "eep"),
}

HERO_NAMES = ["Nina", "Leo", "Maya", "Owen", "Iris", "Toby", "Luna", "Eli"]
TRAITS = ["brave", "curious", "careful", "clever", "sly", "cheerful"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class WorldState:
    setting: Setting
    problem: Problem
    item: Item
    ghost: Ghost
    hero_name: str
    hero_trait: str
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: {"spook": 0.0, "tension": 0.0, "order": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"curiosity": 0.0, "humor": 0.0, "courage": 0.0, "relief": 0.0})
    facts: dict[str, object] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helper text
# ---------------------------------------------------------------------------

def _a(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _hero_pronoun(name: str) -> str:
    return "they"


def setting_opening(setting: Setting) -> str:
    if setting.key == "shed":
        return "The garden shed crouched under the moon like a tiny box with sleepy walls."
    if setting.key == "attic":
        return "The old attic held dusty beams, one little lamp, and lots of whispery corners."
    if setting.key == "museum":
        return "The small museum storeroom was quiet, except for the soft creaks of old shelves."
    return "The boathouse rocked a little, and each board answered with a low, spooky groan."


def problem_intro(problem: Problem) -> str:
    return f"Then came the trouble: {problem.trouble}."


def ghost_line(ghost: Ghost, problem: Problem) -> str:
    return f'“{ghost.whisper},” said {ghost.name}, and the sound came out like {problem.spooky_sound}.'


def decide_fix(problem: Problem, item: Item) -> str:
    if problem.key == "rattle":
        return f"They decided to use {item.label}, a few careful knots, and a soft folded blanket."
    if problem.key == "echo":
        return "They decided to hang thick blankets and walk only when they had to."
    return "They decided to change the lamp and show the room what was really there."


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(setting: Setting, problem: Problem, item: Item, ghost: Ghost) -> bool:
    if item.key != "ammunition_crate":
        return False
    if problem.key == "echo":
        return setting.has_echoes
    if problem.key == "shadow":
        return True
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS.values():
        for p in PROBLEMS.values():
            for i in ITEMS.values():
                for g in GHOSTS.values():
                    if valid_combo(s, p, i, g):
                        out.append((s.key, p.key, i.key, g.key))
    return out


def explain_rejection(setting: Setting, problem: Problem, item: Item, ghost: Ghost) -> str:
    if item.key != "ammunition_crate":
        return "(No story: this world centers on an old ammunition crate, so another item would weaken the ghost-story problem.)"
    if problem.key == "echo" and not setting.has_echoes:
        return f"(No story: {setting.place} would not make the echo problem believable enough.)"
    return "(No story: this combination does not make a clear spooky problem worth solving.)"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def run_world(setting: Setting, problem: Problem, item: Item, ghost: Ghost, hero_name: str, hero_trait: str, seed: Optional[int] = None) -> WorldState:
    w = WorldState(setting=setting, problem=problem, item=item, ghost=ghost, hero_name=hero_name, hero_trait=hero_trait, seed=seed)
    w.meters["spook"] = 1.0
    w.memes["curiosity"] = 1.0
    w.memes["courage"] = 0.5
    w.facts["fixed"] = False
    w.facts["started_scared"] = True

    if problem.key == "rattle":
        w.meters["tension"] += 1.0
        w.memes["humor"] += 1.0
        w.facts["clue"] = "latch"
        w.facts["fix"] = "rope_and_blanket"
        w.facts["ending"] = "quiet"
        w.facts["ghost_feeling"] = "relieved"
    elif problem.key == "echo":
        w.meters["tension"] += 0.8
        w.memes["humor"] += 1.0
        w.facts["clue"] = "round_room"
        w.facts["fix"] = "blankets"
        w.facts["ending"] = "softer"
        w.facts["ghost_feeling"] = "embarrassed"
    else:
        w.meters["tension"] += 0.7
        w.memes["humor"] += 0.8
        w.facts["clue"] = "coat_rack"
        w.facts["fix"] = "lamp"
        w.facts["ending"] = "clear"
        w.facts["ghost_feeling"] = "surprised"

    w.meters["order"] += 1.0
    w.memes["relief"] += 1.0
    w.facts["fixed"] = True
    return w


def story_text(w: WorldState) -> str:
    hero = w.hero_name
    trait = w.hero_trait
    ghost = w.ghost.name
    problem = w.problem
    setting = w.setting
    item = w.item

    lines = []
    lines.append(f"{hero} was a {trait} child who liked quiet places and funny little mysteries.")
    lines.append(f"One night, {hero} tiptoed into {setting.place} carrying {item.phrase}.")
    lines.append(setting_opening(setting))
    lines.append(problem_intro(problem))
    lines.append(ghost_line(w.ghost, problem))
    lines.append(f'{hero} blinked, then whispered, “That sounds scary, but maybe it is only a puzzle.”')
    lines.append(f"The clue was simple: {problem.clue}.")
    lines.append(decide_fix(problem, item))
    if problem.key == "rattle":
        lines.append(f"{hero} tied the latch with {ITEMS['rope'].label} and tucked a blanket around the crate so it could not shiver.")
        lines.append(f"The crate stopped going {problem.spooky_sound}, and {ghost} let out a sheepish little laugh.")
        lines.append(f'"I was only trying to help," said {ghost}, "but I do make a very noisy helper."')
        lines.append(f'{hero} grinned. “You do,” {hero} said, “but now the ammunition crate is safe, and your boo is much better than the rattle.”')
        lines.append(f"At the end, {setting.place} felt calm, {ghost} looked proud instead of spooky, and the crate sat quiet as a sleeping cat.")
    elif problem.key == "echo":
        lines.append(f"{hero} hung the blankets, then clapped once and listened to the smaller, softer sound.")
        lines.append(f"{ghost} tried to whisper again, but the room no longer shouted back.")
        lines.append(f'{hero} giggled. “There, now your voice is the only one being dramatic,” {hero} said.')
        lines.append(f"By the end, the echoes were gentler, the room was easier to hear, and {ghost} stopped sounding so haunted.")
    else:
        lines.append(f"{hero} moved the lamp and pointed to the real coat rack.")
        lines.append(f"The long shadow shrank into something ordinary, like a shy broom trying to be a monster.")
        lines.append(f'{ghost} laughed so hard their boo turned into a snort.')
        lines.append(f'“I thought I had found a true ghost,” said {hero}, “but I only found a coat rack with good imagination.”')
        lines.append(f"At the end, the shadow was just a shadow, and {setting.place} felt a lot less spooky.")
    return " ".join(lines)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def prompts_for(w: WorldState) -> list[str]:
    return [
        f'Write a child-friendly ghost story about {w.hero_name} in {w.setting.place} that includes the word "ammunition".',
        f"Tell a spooky-but-funny story where {w.hero_name} solves a problem with {w.item.label} and a ghost named {w.ghost.name}.",
        f"Write a short story with a harmless ghost, a strange noise, and a clever fix in {w.setting.place}.",
    ]


def story_qa_for(w: WorldState) -> list[QAItem]:
    hero = w.hero_name
    ghost = w.ghost.name
    item = w.item.label
    setting = w.setting.place
    p = w.problem

    return [
        QAItem(
            question=f"What was the scary problem in {setting}?",
            answer=f"The trouble was that {p.trouble}, which made the place feel spooky until {hero} solved it.",
        ),
        QAItem(
            question=f"How did {hero} help with the {item}?",
            answer=f"{hero} used careful problem solving and a funny little plan to make the {item} safe and steady again.",
        ),
        QAItem(
            question=f"Who was the ghost in the story?",
            answer=f"The ghost was {ghost}, and even though {ghost} sounded spooky at first, {ghost} turned out to be friendly.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the problem fixed, the scary noise gone or softened, and {setting} feeling calm again.",
        ),
    ]


def world_knowledge_qa(w: WorldState) -> list[QAItem]:
    return [
        QAItem(
            question="What is ammunition?",
            answer="Ammunition is a supply of projectiles or cartridges kept together for a weapon or old cannon, and in a story it can simply be an old stored supply in a crate.",
        ),
        QAItem(
            question="Why can a crate rattle?",
            answer="A crate can rattle if something inside is loose, like a latch, a lid, or pieces that bump together when the box shakes.",
        ),
        QAItem(
            question="What makes a story a ghost story?",
            answer="A ghost story usually has something spooky or mysterious, but in a gentle version the ghost can also be funny or friendly.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(shed). setting(attic). setting(museum). setting(boathouse).
echoes(shed). echoes(attic). echoes(boathouse).
moonlight(shed). moonlight(boathouse).

problem(rattle). problem(echo). problem(shadow).
trouble(rattle,noisy_crate). trouble(echo,bounced_steps). trouble(shadow,spooky_shape).

item(ammunition_crate).
fixable(rattle,ammunition_crate).
fixable(echo,ammunition_crate).
fixable(shadow,ammunition_crate).

ghost(milo). ghost(maggie). ghost(pip).

valid(S,P,I,G) :- setting(S), problem(P), item(I), ghost(G), fixable(P,I), S=shed.
valid(S,P,I,G) :- setting(S), problem(P), item(I), ghost(G), fixable(P,I), S=attic, P != echo.
valid(S,P,I,G) :- setting(S), problem(P), item(I), ghost(G), fixable(P,I), S=museum.
valid(S,P,I,G) :- setting(S), problem(P), item(I), ghost(G), fixable(P,I), S=boathouse.
#show valid/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.key))
        if s.has_moonlight:
            lines.append(asp.fact("moonlight", s.key))
        if s.has_echoes:
            lines.append(asp.fact("echoes", s.key))
    for p in PROBLEMS.values():
        lines.append(asp.fact("problem", p.key))
    for i in ITEMS.values():
        lines.append(asp.fact("item", i.key))
    for g in GHOSTS.values():
        lines.append(asp.fact("ghost", g.key))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP gate matches Python gate ({len(p)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    if p - a:
        print("Only in Python:", sorted(p - a))
    if a - p:
        print("Only in ASP:", sorted(a - p))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    problem: str
    item: str
    ghost: str
    name: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("shed", "rattle", "ammunition_crate", "milo", "Nina", "curious"),
    StoryParams("attic", "shadow", "ammunition_crate", "pip", "Leo", "careful"),
    StoryParams("boathouse", "rattle", "ammunition_crate", "maggie", "Maya", "cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gentle ghost story world with problem solving and humor.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--ghost", choices=sorted(GHOSTS))
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    item = args.item or "ammunition_crate"
    ghost = args.ghost or rng.choice(list(GHOSTS))
    name = args.name or rng.choice(HERO_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    s = SETTINGS[setting]
    p = PROBLEMS[problem]
    i = ITEMS[item]
    g = GHOSTS[ghost]
    if not valid_combo(s, p, i, g):
        raise StoryError(explain_rejection(s, p, i, g))
    return StoryParams(setting=setting, problem=problem, item=item, ghost=ghost, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    w = run_world(
        SETTINGS[params.setting],
        PROBLEMS[params.problem],
        ITEMS[params.item],
        GHOSTS[params.ghost],
        params.name,
        params.trait,
        seed=params.seed,
    )
    return StorySample(
        params=params,
        story=story_text(w),
        prompts=prompts_for(w),
        story_qa=story_qa_for(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


def dump_trace(w: WorldState) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting: {w.setting.key} ({w.setting.place})")
    lines.append(f"problem: {w.problem.key}")
    lines.append(f"item: {w.item.key}")
    lines.append(f"ghost: {w.ghost.key}")
    lines.append(f"meters: {dict(w.meters)}")
    lines.append(f"memes: {dict(w.memes)}")
    lines.append(f"facts: {dict(w.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ".join(c))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            p.seed = base_seed
            samples.append(generate(p))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
