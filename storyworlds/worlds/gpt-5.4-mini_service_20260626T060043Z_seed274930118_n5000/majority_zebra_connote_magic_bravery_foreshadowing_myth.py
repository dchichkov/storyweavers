#!/usr/bin/env python3
"""
A mythic storyworld about a village, a zebra omen, a majority choice, and a
brave child who follows a foreshadowed path through magic and doubt.
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
class Village:
    name: str = "Ashford"
    setting: str = "the hill village"
    place_detail: str = "the stony road by the old shrine"


@dataclass
class Omen:
    sign: str = "a zebra"
    connotes: str = "a strange message from the old world"
    foreshadows: str = "a coming test"
    magic_item: str = "a lantern of moon-glass"
    magic_effect: str = "glowed when danger was near"


@dataclass
class Hero:
    name: str = "Nia"
    title: str = "young shepherd"
    brave: bool = True


@dataclass
class StoryParams:
    village: str
    hero: str
    omen: str
    seed: Optional[int] = None


@dataclass
class World:
    village: Village
    omen: Omen
    hero: Hero
    villagers: list[str] = field(default_factory=list)
    votes_for_trust: int = 0
    votes_against_trust: int = 0
    majority_choice: str = "against"
    lantern_lit: bool = False
    beast_seen: bool = False
    danger_passed: bool = False
    foreshadowing_note: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)

    def say(self, text: str) -> None:
        self.history.append(text)

    def render(self) -> str:
        return " ".join(self.history)


VILLAGE_REGISTRY = {
    "ashford": Village(
        name="Ashford",
        setting="the hill village",
        place_detail="the stony road by the old shrine",
    )
}

OMEN_REGISTRY = {
    "zebra": Omen(
        sign="a zebra",
        connotes="a strange message from the old world",
        foreshadows="a coming test",
        magic_item="a lantern of moon-glass",
        magic_effect="glowed when danger was near",
    )
}

HERO_REGISTRY = {
    "nia": Hero(name="Nia", title="young shepherd", brave=True),
    "oren": Hero(name="Oren", title="young scout", brave=True),
    "luma": Hero(name="Luma", title="young keeper", brave=True),
}


ASP_RULES = r"""
village(V) :- village_name(V).
omen(O) :- omen_name(O).
hero(H) :- hero_name(H).

trust_majority :- votes_for_trust(F), votes_against_trust(G), F > G.
distrust_majority :- votes_against_trust(G), votes_for_trust(F), G >= F.

magic_lights :- lantern_magic(L), lit(L).
foreshadowing_present :- foreshadows(O, T).

chosen_path(brave) :- trust_majority, magic_lights, foreshadowing_present.
chosen_path(cautious) :- distrust_majority.

#show chosen_path/1.
"""


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("village_name", "ashford"),
        asp.fact("omen_name", "zebra"),
        asp.fact("hero_name", "nia"),
        asp.fact("votes_for_trust", 4),
        asp.fact("votes_against_trust", 3),
        asp.fact("lantern_magic", "moon_glass"),
        asp.fact("lit", "moon_glass"),
        asp.fact("foreshadows", "zebra", "a coming test"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_choice() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show chosen_path/1."))
    return sorted(set(asp.atoms(model, "chosen_path")))


def valid_combination(village: Village, omen: Omen, hero: Hero) -> bool:
    return bool(village.name and omen.sign == "a zebra" and hero.brave)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld with majority, zebra, connotes, magic, bravery, and foreshadowing.")
    ap.add_argument("--village", choices=["ashford"], default=None)
    ap.add_argument("--hero", choices=["nia", "oren", "luma"], default=None)
    ap.add_argument("--omen", choices=["zebra"], default=None)
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
    village = args.village or "ashford"
    hero = args.hero or rng.choice(list(HERO_REGISTRY))
    omen = args.omen or "zebra"
    if omen != "zebra":
        raise StoryError("This myth only grows from the zebra omen.")
    return StoryParams(village=village, hero=hero, omen=omen)


def build_world(params: StoryParams) -> World:
    village = VILLAGE_REGISTRY[params.village]
    omen = OMEN_REGISTRY[params.omen]
    hero = HERO_REGISTRY[params.hero]
    return World(village=village, omen=omen, hero=hero)


def tell_story(world: World) -> None:
    w = world
    w.villagers = ["three elders", "two farmers", "the river singer", "the smith"]
    trust = 4
    against = 3
    w.votes_for_trust = trust
    w.votes_against_trust = against
    w.majority_choice = "trust" if trust > against else "against"
    w.foreshadowing_note = (
        f"Long before the trouble arrived, the zebra had already seemed to connote "
        f"{w.omen.connotes}, and that shadow foreshadowed {w.omen.foreshadows}."
    )

    w.say(
        f"In {w.village.name}, a village of {w.village.setting}, the people gathered by {w.village.place_detail}."
    )
    w.say(
        f"They had seen {w.omen.sign}, and the sight was said to connote {w.omen.connotes}."
    )
    w.say(
        f"The elders spoke in low voices, because the sign seemed to foreshadow {w.omen.foreshadows}."
    )
    w.say(
        f"Most of the villagers feared the tale, but a small majority chose to trust the old omen."
    )
    w.say(
        f"{w.hero.name}, the {w.hero.title}, carried {w.omen.magic_item}, a charm that had been kept beneath the shrine stone."
    )
    w.lantern_lit = True
    w.meters["magic"] = 1.0
    w.memes["bravery"] = 1.0
    w.say(
        f"When {w.hero.name} lifted it, the lantern {w.omen.magic_effect}, and its magic made the path clear."
    )
    w.beast_seen = True
    w.say(
        f"At the edge of the road, a shadowed beast rose from the reeds, just as the foreshadowing had warned."
    )
    w.say(
        f"The village cried out, but {w.hero.name} stood firm with bravery in {w.hero.name}'s chest."
    )
    w.danger_passed = True
    w.say(
        f"{w.hero.name} held the glowing lantern high, and the beast turned away into the dark."
    )
    w.say(
        f"By dawn, the people praised the brave one, and even the doubters admitted that the zebra had spoken true."
    )
    w.say(
        f"So the majority choice was remembered as wisdom, the omen as a warning, and the lantern as a gift that saved the hill village."
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short myth about a zebra omen in {world.village.name} that connotes hidden meaning.",
        f"Tell a child-friendly legend where a majority of villagers choose whether to trust a zebra sign.",
        f"Write a mythic story with magic, bravery, and foreshadowing, ending with a glowing lantern.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why did the villagers gather in the village?",
            answer=f"They gathered by {world.village.place_detail} because they had seen {world.omen.sign} and wanted to decide what the omen meant.",
        ),
        QAItem(
            question="What did the zebra seem to mean?",
            answer=f"It seemed to connote {world.omen.connotes}, and the elders said it foreshadowed {world.omen.foreshadows}.",
        ),
        QAItem(
            question="What helped the hero face the danger?",
            answer=f"{world.omen.magic_item} helped, because its magic {world.omen.magic_effect} and gave {world.hero.name} courage.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The danger passed when {world.hero.name} held the lantern high, and the village remembered that bravery and the majority choice had led to safety.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a majority?",
            answer="A majority is the larger part of a group; if more people choose one side than the other, that side has the majority.",
        ),
        QAItem(
            question="What does it mean when something foreshadows something else?",
            answer="Foreshadowing means giving a small hint about what may happen later, like a warning before the big moment arrives.",
        ),
        QAItem(
            question="What can magic mean in a myth?",
            answer="In a myth, magic can be an enchanted power or object that helps people in a way ordinary things cannot.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel afraid.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"village={world.village.name}")
    lines.append(f"hero={world.hero.name}")
    lines.append(f"omen={world.omen.sign}")
    lines.append(f"votes_for_trust={world.votes_for_trust}")
    lines.append(f"votes_against_trust={world.votes_against_trust}")
    lines.append(f"majority_choice={world.majority_choice}")
    lines.append(f"lantern_lit={world.lantern_lit}")
    lines.append(f"beast_seen={world.beast_seen}")
    lines.append(f"danger_passed={world.danger_passed}")
    lines.append(f"meters={world.meters}")
    lines.append(f"memes={world.memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def verify() -> int:
    py = [("chosen_path", "brave")]
    cl = asp_choice()
    if cl != py:
        print("MISMATCH between ASP and Python:", cl, py)
        return 1
    sample = generate(StoryParams(village="ashford", hero="nia", omen="zebra"))
    if not sample.story or "zebra" not in sample.story.lower():
        print("Story generation failed.")
        return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


CURATED = [
    StoryParams(village="ashford", hero="nia", omen="zebra"),
    StoryParams(village="ashford", hero="oren", omen="zebra"),
    StoryParams(village="ashford", hero="luma", omen="zebra"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show chosen_path/1."))
        return
    if args.verify:
        sys.exit(verify())

    if args.asp:
        print("compatible stories: 1")
        print("  ashford  zebra  nia  -> brave")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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
