#!/usr/bin/env python3
"""
A small fable-like storyworld about a quibble under the sky, where kindness
and bravery can turn a tuckus of a problem into a gentle ending.
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

@dataclass
class Actor:
    id: str
    kind: str
    title: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class StoryParams:
    hero: str
    friend: str
    setting: str
    problem: str
    seed: Optional[int] = None


@dataclass
class World:
    hero: Actor
    friend: Actor
    setting: str
    problem: str
    sky_state: str = "clear"
    quibble_resolved: bool = False
    faced_tuckus: bool = False
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

HEROES = {
    "fox": Actor("fox", "animal", "fox", "he", "him", "his"),
    "hare": Actor("hare", "animal", "hare", "she", "her", "her"),
    "crow": Actor("crow", "animal", "crow", "he", "him", "his"),
    "mole": Actor("mole", "animal", "mole", "she", "her", "her"),
}

FRIENDS = {
    "badger": Actor("badger", "animal", "badger", "he", "him", "his"),
    "squirrel": Actor("squirrel", "animal", "squirrel", "she", "her", "her"),
    "sparrow": Actor("sparrow", "animal", "sparrow", "he", "him", "his"),
    "rabbit": Actor("rabbit", "animal", "rabbit", "she", "her", "her"),
}

SETTINGS = {
    "meadow": "the meadow",
    "hill": "the hill",
    "orchard": "the orchard",
    "brook": "the brook",
}

PROBLEMS = {
    "quibble": "a small quibble over a shiny berry",
    "tuckus": "a tuckus about the last warm leaf nest",
    "sky": "a sky-watching quarrel over who would tell the sunset first",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like storyworld about quibble, sky, and tuckus.")
    ap.add_argument("--hero", choices=sorted(HEROES))
    ap.add_argument("--friend", choices=sorted(FRIENDS))
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
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


def _copy_actor(a: Actor) -> Actor:
    return Actor(
        id=a.id,
        kind=a.kind,
        title=a.title,
        pronoun_subject=a.pronoun_subject,
        pronoun_object=a.pronoun_object,
        pronoun_possessive=a.pronoun_possessive,
        meters=dict(a.meters),
        memes=dict(a.memes),
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(list(HEROES))
    friend = args.friend or rng.choice([k for k in FRIENDS if k != hero])
    setting = args.setting or rng.choice(list(SETTINGS))
    problem = args.problem or rng.choice(list(PROBLEMS))
    if friend == hero:
        raise StoryError("hero and friend must be different characters.")
    return StoryParams(hero=hero, friend=friend, setting=setting, problem=problem)


def _init_world(params: StoryParams) -> World:
    hero = _copy_actor(HEROES[params.hero])
    friend = _copy_actor(FRIENDS[params.friend])
    return World(hero=hero, friend=friend, setting=SETTINGS[params.setting], problem=params.problem)


def _narrate_setup(world: World) -> None:
    h, f = world.hero, world.friend
    world.say(
        f"Once in {world.setting}, a little {h.title} and a kind {f.title} lived beneath the wide sky."
    )
    world.say(
        f"{h.pronoun_subject.capitalize()} often had an inner monologue that sounded like a tiny bell: "
        f"what if there was a better way to share?"
    )
    world.say(
        f"They loved to look up at the sky, but one day {world.problem} began as a small quibble."
    )


def _turn(world: World) -> None:
    h, f = world.hero, world.friend
    world.para()
    h.memes["quibble"] = 1.0
    f.memes["quibble"] = 1.0
    world.faced_tuckus = True
    world.sky_state = "clouded"
    world.say(
        f"The quarrel grew into a tuckus, and the sky seemed to dim as if it were listening."
    )
    world.say(
        f"{h.pronoun_subject.capitalize()} wanted to keep the prize, while {f.pronoun_subject} wanted to be heard."
    )
    world.say(
        f"Inside, {h.pronoun_subject} thought, 'If I shout, I may win, but I may lose a friend.'"
    )


def _resolution(world: World) -> None:
    h, f = world.hero, world.friend
    world.para()
    h.memes["bravery"] = 1.0
    h.memes["kindness"] = 1.0
    f.memes["kindness"] = 1.0
    world.quibble_resolved = True
    world.sky_state = "golden"
    world.say(
        f"Then {h.pronoun_subject} found bravery enough to speak gently and listen first."
    )
    world.say(
        f"{h.pronoun_subject.capitalize()} offered to share the best part and let {f.pronoun_object} have a turn."
    )
    world.say(
        f"{f.pronoun_subject.capitalize()} smiled, and kindness made the tuckus shrink until it was no more than a pebble on the path."
    )
    world.say(
        f"By sunset, the sky was bright again, and the friends walked home side by side."
    )


def generate_world(params: StoryParams) -> World:
    world = _init_world(params)
    _narrate_setup(world)
    _turn(world)
    _resolution(world)
    world.facts = {
        "hero": world.hero,
        "friend": world.friend,
        "setting": world.setting,
        "problem": world.problem,
        "sky_state": world.sky_state,
        "resolved": world.quibble_resolved,
    }
    return world


# ---------------------------------------------------------------------------
# Story/QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short fable about a {world.hero.title}, a {world.friend.title}, and a quibble under the sky.",
        f"Tell a gentle story where kindness and bravery turn a tuckus into peace in {world.setting}.",
        f"Write a child-friendly fable that includes inner monologue, kindness, bravery, quibble, sky, and tuckus.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h, f = world.hero, world.friend
    return [
        QAItem(
            question=f"Who had the inner monologue in the story?",
            answer=f"The {h.title} had the inner monologue and quietly thought about a better way to act.",
        ),
        QAItem(
            question=f"What started the trouble beneath the sky?",
            answer=f"A {world.problem} started the trouble and turned into a tuckus before it was solved.",
        ),
        QAItem(
            question=f"How did the friends solve the quibble?",
            answer=f"{h.title.capitalize()} used kindness and bravery, listened, and shared so the quarrel could end.",
        ),
        QAItem(
            question=f"What happened to the sky at the end?",
            answer=f"The sky turned golden and bright again after the friends made peace.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means acting with care, warmth, and helpfulness toward someone else.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing the right thing even when you feel a little afraid.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice in your own mind that helps you think.",
        ),
        QAItem(
            question="What does the sky look like on a clear day?",
            answer="On a clear day, the sky looks wide and bright above the world.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    lines.append(f"setting: {world.setting}")
    lines.append(f"problem: {world.problem}")
    lines.append(f"sky_state: {world.sky_state}")
    lines.append(f"resolved: {world.quibble_resolved}")
    for a in [world.hero, world.friend]:
        lines.append(f"{a.id}: meters={a.meters} memes={a.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_fact(H).
friend(F) :- friend_fact(F).
setting(S) :- setting_fact(S).
problem(P) :- problem_fact(P).

quibble(P) :- problem_fact(P), quibble_word(P).
sky(S) :- sky_fact(S).
tuckus(T) :- tuckus_word(T).

problematic(P) :- problem_fact(P).
resolved(P) :- problematic(P), kindness(K), bravery(B), K, B.

valid_story(H,F,S,P) :- hero_fact(H), friend_fact(F), setting_fact(S), problem_fact(P), H != F.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in HEROES:
        lines.append(asp.fact("hero_fact", k))
    for k in FRIENDS:
        lines.append(asp.fact("friend_fact", k))
    for k in SETTINGS:
        lines.append(asp.fact("setting_fact", k))
    for k in PROBLEMS:
        lines.append(asp.fact("problem_fact", k))
    lines.append(asp.fact("quibble_word", "quibble"))
    lines.append(asp.fact("sky_fact", "sky"))
    lines.append(asp.fact("tuckus_word", "tuckus"))
    lines.append(asp.fact("kindness"))
    lines.append(asp.fact("bravery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for h in HEROES:
        for f in FRIENDS:
            if h != f:
                for s in SETTINGS:
                    for p in PROBLEMS:
                        py_set.add((h, f, s, p))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches Python combinations ({len(py_set)}).")
        return 0
    print("MISMATCH between clingo and Python.")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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


def _valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for h in HEROES:
        for f in FRIENDS:
            if h == f:
                continue
            for s in SETTINGS:
                for p in PROBLEMS:
                    out.append((h, f, s, p))
    return out


CURATED = [
    StoryParams(hero="fox", friend="squirrel", setting="meadow", problem="quibble"),
    StoryParams(hero="hare", friend="badger", setting="hill", problem="sky"),
    StoryParams(hero="crow", friend="rabbit", setting="orchard", problem="tuckus"),
    StoryParams(hero="mole", friend="sparrow", setting="brook", problem="quibble"),
]


def resolve_for_story(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hero and args.friend and args.hero == args.friend:
        raise StoryError("hero and friend must be different.")
    combos = _valid_combos()
    combos = [
        c for c in combos
        if (args.hero is None or c[0] == args.hero)
        and (args.friend is None or c[1] == args.friend)
        and (args.setting is None or c[2] == args.setting)
        and (args.problem is None or c[3] == args.problem)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    h, f, s, p = rng.choice(sorted(combos))
    return StoryParams(hero=h, friend=f, setting=s, problem=p)


def build_parser_main() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser_main().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_for_story(args, rng)
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
