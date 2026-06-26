#!/usr/bin/env python3
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
class Character:
    name: str
    role: str
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self) -> str:
        return "they"


@dataclass
class ObjectItem:
    name: str
    kind: str = "thing"
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    market: str
    value: str
    teamwork: str
    seed_word: str
    name: str
    helper_name: str
    seed: Optional[int] = None


@dataclass
class World:
    market: str
    value: str
    teamwork: str
    seed_word: str
    hero: Character
    helper: Character
    vendor: Character
    beret: ObjectItem
    pupa: ObjectItem
    facts: dict = field(default_factory=dict)


MARKETS = ["market"]
VALUES = ["honesty", "kindness", "patience"]
TEAMWORKS = ["shared search", "careful sorting", "clean-up crew"]
SEED_WORDS = ["pupa", "fatal", "beret"]
NAMES = ["Mina", "Tomas", "Lina", "Rafi", "Nora", "Eli"]
HELPER_NAMES = ["June", "Arlo", "Mara", "Ivo", "Sana", "Pia"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life market storyworld.")
    ap.add_argument("--market", choices=MARKETS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--teamwork", choices=TEAMWORKS)
    ap.add_argument("--seed-word", choices=SEED_WORDS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    market = args.market or "market"
    value = args.value or rng.choice(VALUES)
    teamwork = args.teamwork or rng.choice(TEAMWORKS)
    seed_word = args.seed_word or rng.choice(SEED_WORDS)
    name = args.name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != name])
    return StoryParams(
        market=market,
        value=value,
        teamwork=teamwork,
        seed_word=seed_word,
        name=name,
        helper_name=helper_name,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.market != "market":
        raise StoryError("This story only works in a market.")
    if params.seed_word not in {"pupa", "fatal", "beret"}:
        raise StoryError("The seed word must be pupa, fatal, or beret.")
    if params.value not in VALUES:
        raise StoryError("Unsupported moral value.")
    if params.teamwork not in TEAMWORKS:
        raise StoryError("Unsupported teamwork pattern.")


ASP_RULES = r"""
value(honesty;kindness;patience).
teamwork("shared search";"careful sorting";"clean-up crew").
seed_word(pupa;fatal;beret).
compatible(V,T,W) :- value(V), teamwork(T), seed_word(W).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VALUES:
        lines.append(asp.fact("value", v))
    for t in TEAMWORKS:
        lines.append(asp.fact("teamwork", t))
    for w in SEED_WORDS:
        lines.append(asp.fact("seed_word", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatibility() -> set[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return set(asp.atoms(model, "compatible"))


def python_compatibility() -> set[tuple[str, str, str]]:
    return {(v, t, w) for v in VALUES for t in TEAMWORKS for w in SEED_WORDS}


def asp_verify() -> int:
    a = asp_compatibility()
    b = python_compatibility()
    if a == b:
        print(f"OK: ASP matches Python ({len(a)} combinations).")
        return 0
    print("MISMATCH")
    if a - b:
        print("only in ASP:", sorted(a - b))
    if b - a:
        print("only in Python:", sorted(b - a))
    return 1


def generate_story(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    hero = Character(name=params.name, role="child", meters={"joy": 1.0}, memes={params.value: 1.0, "teamwork": 1.0})
    helper = Character(name=params.helper_name, role="friend", meters={"care": 1.0}, memes={"teamwork": 1.0})
    vendor = Character(name="the vendor", role="vendor", meters={"busy": 1.0}, memes={"kindness": 1.0})
    beret = ObjectItem(name="beret", owner=hero.name, meters={"clean": 1.0}, memes={"pride": 1.0})
    pupa = ObjectItem(name="pupa", owner=None, meters={"fragile": 1.0}, memes={"life": 1.0})

    world = World(
        market=params.market,
        value=params.value,
        teamwork=params.teamwork,
        seed_word=params.seed_word,
        hero=hero,
        helper=helper,
        vendor=vendor,
        beret=beret,
        pupa=pupa,
    )

    if params.seed_word == "beret":
        opening = (
            f"{hero.name} went to the market with a small beret tucked in hand. "
            f"The beret was the one thing {hero.name} wanted to wear all day."
        )
        middle = (
            f"Near the bread stall, {hero.name} spotted a little pupa resting on a leaf. "
            f"It looked so still and delicate that {hero.name} slowed down at once."
        )
        turn = (
            f"{helper.name} leaned in and said they should make a careful circle around it, "
            f"so nobody bumped the leaf. That was their {params.teamwork}."
        )
        ending = (
            f"{hero.name} thanked {helper.name}, and together they told the vendor. "
            f"The vendor smiled, and the market kept its friendly hum while the beret stayed neat."
        )
    elif params.seed_word == "pupa":
        opening = (
            f"At the market, {hero.name} carried a basket and kept looking for a bright beret. "
            f"{hero.name} liked how a beret could make an ordinary day feel special."
        )
        middle = (
            f"Behind a crate of oranges, {hero.name} found a tiny pupa on a twig. "
            f"{hero.name} almost forgot the shopping because it seemed so small and important."
        )
        turn = (
            f"{helper.name} suggested asking the vendor for a paper cup and a leaf, "
            f"so the pupa could travel safely. Their {params.teamwork} helped them work fast and gently."
        )
        ending = (
            f"{hero.name} carried the cup while {helper.name} held the leaf. "
            f"The vendor thanked them for being careful, and the beret was bought after the good deed."
        )
    else:
        opening = (
            f"{hero.name} and {helper.name} walked through the market under a sunny awning. "
            f"{hero.name} wanted a beret, and {helper.name} wanted to help choose one."
        )
        middle = (
            f"At the flower stall, a sign warned that one wrong step could be fatal for a tiny pupa. "
            f"{hero.name} understood that the sign was serious, so {hero.name} stopped right away."
        )
        turn = (
            f"Together they moved the basket back from the path and asked the vendor to set a tiny fence around it. "
            f"It was a small act of {params.value} and easy {params.teamwork}."
        )
        ending = (
            f"After that, the market felt calm again. {hero.name} chose a soft beret, and both children left proud of their careful choice."
        )

    story = " ".join([opening, middle, turn, ending])

    world.facts = {
        "hero": hero,
        "helper": helper,
        "vendor": vendor,
        "beret": beret,
        "pupa": pupa,
        "params": params,
    }

    prompts = [
        f"Write a gentle slice-of-life story set in a market about {params.name}, a {params.value} lesson, and teamwork.",
        f"Tell a child-friendly story that includes the words pupa, fatal, and beret without making the scene frightening.",
        f"Write a market story where {params.name} and {params.helper_name} use {params.teamwork} to do the right thing.",
    ]

    story_qa = [
        QAItem(
            question=f"Where does the story happen?",
            answer=f"It happens in a market, where stalls, baskets, and careful walking matter.",
        ),
        QAItem(
            question=f"What moral value is shown when {params.name} helps?",
            answer=f"The story shows {params.value}, because {params.name} chooses to be thoughtful instead of careless.",
        ),
        QAItem(
            question=f"How do {params.name} and {params.helper_name} work together?",
            answer=f"They use {params.teamwork} by helping each other stay careful, carry things, and make a good choice.",
        ),
        QAItem(
            question=f"What important thing stays safe in the story?",
            answer=f"The tiny pupa stays safe because the children watch where they step and move gently around it.",
        ),
        QAItem(
            question=f"What does the beret have to do with the day?",
            answer=f"The beret is the little item {params.name} wants, and it helps make the market trip feel special.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a pupa?",
            answer="A pupa is a stage in the life of some insects, when they are changing before they become adults.",
        ),
        QAItem(
            question="What is a beret?",
            answer="A beret is a soft, round hat that people wear on their heads.",
        ),
        QAItem(
            question="Why do people work together in a busy market?",
            answer="People work together so they can move safely, share jobs, and help things go smoothly.",
        ),
        QAItem(
            question="What does fatal mean?",
            answer="Fatal means something can cause death, so it is a very serious word and should be used carefully.",
        ),
    ]

    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print("--- trace ---")
        print(sample.world.facts["hero"])
        print(sample.world.facts["helper"])
        print(sample.world.facts["vendor"])
        print(sample.world.facts["beret"])
        print(sample.world.facts["pupa"])
    if qa:
        print()
        for i, item in enumerate(sample.prompts, 1):
            print(f"P{i}: {item}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = sorted(asp_compatibility())
        print(f"{len(combos)} compatible combinations:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for value in VALUES:
            for teamwork in TEAMWORKS:
                for seed_word in SEED_WORDS:
                    params = StoryParams(
                        market="market",
                        value=value,
                        teamwork=teamwork,
                        seed_word=seed_word,
                        name="Mina",
                        helper_name="June",
                    )
                    samples.append(generate_story(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            try:
                sample = generate_story(params)
            except StoryError as err:
                print(err)
                return
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
            p = sample.params
            header = f"### {idx + 1}: {p.name} / {p.seed_word} / {p.value} / {p.teamwork}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
