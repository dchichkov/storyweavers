#!/usr/bin/env python3
"""
A fairy-tale story world about a small quest, a cautious inner monologue,
and a brave revision of course. The seed words are woven in as part of the
domain vocabulary: piss, puggle, revise.
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
class Character:
    name: str
    role: str
    type: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class Relic:
    name: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carried_by: Optional[str] = None
    hidden: bool = False


@dataclass
class World:
    setting: str
    mood: str = "misty"
    characters: dict[str, Character] = field(default_factory=dict)
    relics: dict[str, Relic] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Parameters / registries
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    caution: str
    name: str
    seed: Optional[int] = None


SETTINGS = {
    "moonwood": "the moonwood",
    "rosebridge": "the rose bridge",
    "rivergate": "the river gate",
}

QUESTS = {
    "find_puggle": {
        "goal": "find the lost puggle",
        "item": "puggle",
        "trail": "little paw prints in the moss",
        "risk": "a whispering ditch",
        "turn": "the puggle was not trapped; it was waiting near a warm lantern",
    },
    "revise_scroll": {
        "goal": "revise the royal scroll",
        "item": "scroll",
        "trail": "crumbled gold dust by the steps",
        "risk": "the windy tower stairs",
        "turn": "the wrong line was easy to mend once she read it aloud again",
    },
    "carry_piss": {
        "goal": "carry the tiny bottle of piss water to the healer",
        "item": "bottle",
        "trail": "shaky drips on the stone",
        "risk": "a slippery gate",
        "turn": "the healer only needed a careful hand, not a rushed one",
    },
}

CAUTIONS = {
    "soft_voice": "she must keep her voice soft so the old owl would not wake",
    "slow_steps": "she must take slow steps over the roots",
    "think_first": "she must think first before she touched the magic",
}

NAMES = ["Mira", "Nell", "Tamsin", "Rowan", "Iris", "Pippa"]
ROLES = ["girl", "boy", "child"]


# ---------------------------------------------------------------------------
# Inline ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/3.

valid_story(S,Q,C) :- setting(S), quest(Q), caution(C).
quest_item(find_puggle,puggle).
quest_item(revise_scroll,scroll).
quest_item(carry_piss,bottle).

reasonably_compatible(find_puggle,soft_voice).
reasonably_compatible(revise_scroll,think_first).
reasonably_compatible(carry_piss,slow_steps).

valid_story(S,Q,C) :- setting(S), quest(Q), caution(C), reasonably_compatible(Q,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for c in CAUTIONS:
        lines.append(asp.fact("caution", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for q in QUESTS:
            for c in CAUTIONS:
                if (q, c) in {
                    ("find_puggle", "soft_voice"),
                    ("revise_scroll", "think_first"),
                    ("carry_piss", "slow_steps"),
                }:
                    out.append((s, q, c))
    return out


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH:")
    print(" only Python:", sorted(py - cl))
    print(" only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.caution not in CAUTIONS:
        raise StoryError("Unknown caution.")
    allowed = {
        "find_puggle": "soft_voice",
        "revise_scroll": "think_first",
        "carry_piss": "slow_steps",
    }
    if allowed[params.quest] != params.caution:
        raise StoryError("That caution does not fit this quest.")


def build_world(params: StoryParams) -> World:
    world = World(setting=SETTINGS[params.setting])
    hero = Character(name=params.name, role="quester")
    helper = Character(name="Grandmother", role="guide")
    relic_name = QUESTS[params.quest]["item"]
    relic = Relic(name=relic_name)
    world.characters[hero.name] = hero
    world.characters[helper.name] = helper
    world.relics[relic.name] = relic
    world.facts.update(hero=hero.name, helper=helper.name, quest=params.quest, caution=params.caution, setting=params.setting)
    return world


def tell_story(world: World, params: StoryParams) -> str:
    hero = world.characters[params.name]
    helper = world.characters["Grandmother"]
    q = QUESTS[params.quest]

    hero.memes["hope"] = 1
    hero.memes["curiosity"] = 1
    world.say(
        f"Once in {world.setting}, there lived a child named {hero.name} who had a small heart full of hope."
    )
    world.say(
        f"{hero.name} was sent on a quest to {q['goal']}, and {helper.name} said the road would be gentler if {CAUTIONS[params.caution]}."
    )
    world.para()

    # Inner Monologue beat
    hero.memes["worry"] = 1
    hero.memes["inner_monologue"] = 1
    world.say(
        f"In {hero.name}'s inner monologue, a tiny thought murmured, 'If I rush, the day may go crooked.'"
    )
    world.say(
        f"So {hero.name} looked at {q['trail']} and remembered the caution, letting the warning sit like a lantern in the chest."
    )
    world.para()

    # Cautionary turn
    hero.meters["risk"] = 1
    world.say(
        f"At {q['risk']}, the stones looked slippery and bright, and the old story warned that careless feet could tumble."
    )
    world.say(
        f"{hero.name} took one breath, then another, and chose the safer way instead of the quick way."
    )

    # Quest resolution
    hero.memes["bravery"] = 1
    if params.quest == "find_puggle":
        world.say(
            f"At last {hero.name} found the puggle curled by a warm lantern, sleepy and safe."
        )
        world.say(
            f"The puggle blinked, gave a tiny squeak, and followed {hero.name} home through the moonwood."
        )
    elif params.quest == "revise_scroll":
        world.say(
            f"{hero.name} unrolled the royal scroll and saw the mistake at once."
        )
        world.say(
            f"With a calm finger and a careful voice, {hero.name} revised the line until it read true."
        )
    else:
        world.say(
            f"{hero.name} carried the bottle of piss water with both hands and never let it spill."
        )
        world.say(
            f"The healer thanked {hero.name}, and the little errand ended without a mess."
        )

    # Ending image proving change
    hero.memes["peace"] = 1
    world.say(
        f"In the end, {hero.name} returned by the old road with a steadier step, and the world felt less frightening than before."
    )
    return world.render()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World, params: StoryParams) -> list[str]:
    q = QUESTS[params.quest]["goal"]
    return [
        f"Write a Fairy Tale about a child on a quest to {q}, using an inner monologue and a cautionary turn.",
        f"Tell a gentle story set in {world.setting} where the hero must choose wisely and revise their course.",
        f"Write a short child-friendly tale that includes the words piss, puggle, and revise in a meaningful way.",
    ]


def story_qa(world: World, params: StoryParams) -> list[QAItem]:
    hero = world.facts["hero"]
    q = QUESTS[params.quest]["goal"]
    caution = CAUTIONS[params.caution]
    return [
        QAItem(
            question=f"What quest did {hero} have to do in the story?",
            answer=f"{hero} had to {q}.",
        ),
        QAItem(
            question=f"What caution guided {hero} in the story?",
            answer=f"The guide reminded {hero} that {caution}.",
        ),
        QAItem(
            question=f"How did {hero} change by the end?",
            answer=f"{hero} became steadier and calmer, because the quest ended with a careful choice instead of a rushed one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private voice of a character's thoughts, the words they say only inside their own mind.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before acting so something does not go wrong.",
        ),
        QAItem(
            question="What is a quest in a fairy tale?",
            answer="A quest is a journey or task where a character goes looking for something important or tries to fix a problem.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for c in world.characters.values():
        lines.append(f"{c.name}: meters={dict(c.meters)} memes={dict(c.memes)}")
    for r in world.relics.values():
        lines.append(f"{r.name}: meters={dict(r.meters)} memes={dict(r.memes)} carried_by={r.carried_by}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale storyworld of quest, caution, and revision.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--caution", choices=CAUTIONS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_stories()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.quest:
        combos = [c for c in combos if c[1] == args.quest]
    if args.caution:
        combos = [c for c in combos if c[2] == args.caution]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    setting, quest, caution = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    params = StoryParams(setting=setting, quest=quest, caution=caution, name=name)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = build_world(params)
    story = tell_story(world, params)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world, params),
        story_qa=story_qa(world, params),
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
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="moonwood", quest="find_puggle", caution="soft_voice", name="Mira"),
    StoryParams(setting="rosebridge", quest="revise_scroll", caution="think_first", name="Nell"),
    StoryParams(setting="rivergate", quest="carry_piss", caution="slow_steps", name="Tamsin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s, q, c in stories:
            print(f"  {s:10} {q:15} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
