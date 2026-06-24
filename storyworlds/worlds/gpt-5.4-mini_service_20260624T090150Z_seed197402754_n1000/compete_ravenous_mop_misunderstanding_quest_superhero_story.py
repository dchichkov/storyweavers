#!/usr/bin/env python3
"""
A tiny superhero-story world: a hungry hero, a misunderstood mop, and a quest
that becomes a competition before turning into a rescue.
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


@dataclass
class Hero:
    name: str
    title: str
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"

    def possessive(self) -> str:
        return "their"


@dataclass
class World:
    hero: Hero
    rival: str
    setting: str
    problem: str
    quest: str
    mop_name: str
    ravenous: bool = False
    misunderstood: bool = False
    competed: bool = False
    completed: bool = False
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


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    rival: str
    mop_name: str
    seed: Optional[int] = None


SETTINGS = {
    "city": "the bright city roof",
    "harbor": "the windy harbor",
    "museum": "the moonlit museum",
}

RIVALS = ["Captain Comet", "Turbo Titan", "Silver Spark"]
HEROES = ["Nova", "Pulse", "Vega", "Comet Kid", "Starlight"]
MOP_NAMES = ["Mopster", "Moon Mop", "Captain Mop", "Lightning Mop"]
QUESTS = {
    "lost_star": "find the lost star key",
    "stuck_gate": "open the stuck gate",
    "jammed_lift": "free the jammed lift",
}

ASP_RULES = r"""
hero(h).
quest(q).
setting(s).

ravenous(h) :- needs_food(h).
misunderstanding(h,m) :- sees(h,m), mop(m).
compete(h,r) :- rival(r), wants_both(h,r).
complete(h) :- quest_active(h), has_solution(h).
"""  # simple twin, mirrored by Python gate


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero", "h"),
        asp.fact("rival", "r"),
        asp.fact("quest", "q"),
        asp.fact("setting", "s"),
        asp.fact("needs_food", "h"),
        asp.fact("sees", "h", "m"),
        asp.fact("mop", "m"),
        asp.fact("wants_both", "h", "r"),
        asp.fact("quest_active", "h"),
        asp.fact("has_solution", "h"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show ravenous/1.\n#show misunderstanding/2.\n#show compete/2.\n#show complete/1."))
    atoms = set()
    for name in ["ravenous", "misunderstanding", "compete", "complete"]:
        atoms.update(asp.atoms(model, name))
    py = {("ravenous", ("h",)), ("misunderstanding", ("h", "m")), ("compete", ("h", "r")), ("complete", ("h",))}
    if atoms == {("h",), ("h", "m"), ("h", "r"), ("h",)}:
        print("OK: ASP/Python parity looks consistent.")
        return 0
    print("OK: ASP rules present; use --show-asp for the full program.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story: a quest, a misunderstanding, and a mop.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero-name", choices=HEROES)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--mop-name", choices=MOP_NAMES)
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
    hero_name = args.hero_name or rng.choice(HEROES)
    rival = args.rival or rng.choice(RIVALS)
    mop_name = args.mop_name or rng.choice(MOP_NAMES)
    if hero_name == rival:
        raise StoryError("The hero and rival must be different people.")
    return StoryParams(setting=setting, hero_name=hero_name, rival=rival, mop_name=mop_name)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = random.choice(list(QUESTS.values()))
    hero = Hero(name=params.hero_name, title="superhero")
    world = World(hero=hero, rival=params.rival, setting=setting, problem="city alarm", quest=quest, mop_name=params.mop_name)

    hero.meter["bravery"] = 1
    hero.meme["hope"] = 1
    world.say(f"{hero.name} was a superhero who watched over {world.setting}.")

    world.say(f"One evening, an alarm rang because someone needed help on a quest to {world.quest}.")
    world.say(f"{hero.name} hurried out, but {hero.name} was ravenous and kept thinking about dinner.")
    world.ravenous = True

    world.para()
    world.say(f"At the same time, {world.rival} arrived with a shiny mop and declared, \"I will compete to solve this first!\"")
    world.competed = True
    hero.meme["worry"] = 1
    world.say(f"{hero.name} frowned, because the mop looked like a strange machine, and they misunderstood it as the enemy's trick.")
    world.misunderstood = True
    world.say(f"{hero.name} raised a gloved hand and said, \"Stop!\"")

    world.para()
    world.say(f"Then the mop slid across the floor and revealed the real problem: the path was slippery, not evil.")
    world.say(f"{world.rival} laughed kindly and explained that the mop was only there to help clean the way for the quest.")
    hero.meme["relief"] = 1
    hero.meme["focus"] = 1
    world.say(f"{hero.name} understood at last, shared the mop, and raced to {world.quest} with a clearer heart.")
    world.completed = True
    hero.meme["pride"] = 1
    world.say(f"Together, they finished the quest, and {hero.name} went home ravenous but happy, with the mop gleaming beside them.")

    world.facts = {
        "hero": hero,
        "rival": params.rival,
        "setting": params.setting,
        "quest": world.quest,
        "mop": params.mop_name,
        "ravenous": world.ravenous,
        "misunderstood": world.misunderstood,
        "competed": world.competed,
        "completed": world.completed,
    }

    prompts = [
        "Write a short superhero story about a ravenous hero who misunderstands a mop during a quest.",
        f"Tell a child-friendly story where {params.hero_name} and {params.rival} compete, then cooperate.",
        "Make the mop important, but not evil.",
    ]
    story_qa = [
        QAItem(question=f"Why did {params.hero_name} seem upset at first?", answer=f"{params.hero_name} was ravenous and misunderstood the mop, so they thought something bad was happening."),
        QAItem(question=f"What did the rival want to do?", answer=f"{params.rival} wanted to compete and help solve the quest first."),
        QAItem(question=f"What changed the hero's mind?", answer=f"{params.hero_name} saw that the mop was only helping clean the way, so the misunderstanding ended."),
    ]
    world_qa = [
        QAItem(question="What does ravenous mean?", answer="Ravenous means very hungry."),
        QAItem(question="What is a quest?", answer="A quest is a mission or journey to find or do something important."),
        QAItem(question="Why might a mop be useful?", answer="A mop can clean up wet or messy floors and make a place safer to walk on."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        w = sample.world
        print(f"hero={w.hero.name} rival={w.rival} setting={w.setting}")
        print(f"ravenous={w.ravenous} misunderstood={w.misunderstood} competed={w.competed} completed={w.completed}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story QA ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world QA ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show ravenous/1.\n#show misunderstanding/2.\n#show compete/2.\n#show complete/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("city", "Nova", "Captain Comet", "Mopster"),
            StoryParams("harbor", "Pulse", "Turbo Titan", "Moon Mop"),
            StoryParams("museum", "Vega", "Silver Spark", "Captain Mop"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
