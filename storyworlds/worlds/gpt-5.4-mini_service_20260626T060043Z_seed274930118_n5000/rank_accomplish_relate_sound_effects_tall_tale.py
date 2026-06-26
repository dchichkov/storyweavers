#!/usr/bin/env python3
"""
storyworlds/worlds/rank_accomplish_relate_sound_effects_tall_tale.py
=====================================================================

A small, standalone story world in a tall-tale style.

Premise:
- A child and a grown helper take part in an outlandish county fair challenge.
- The story uses sound effects as narrative instruments: every big action gets a
  concrete noise, and the noises help the child understand what to do next.
- The child must accomplish a task well enough to earn a rank ribbon.

The world simulates:
- physical effort, distance, height, and noise
- emotional pride, worry, and delight
- whether the task is accomplished honestly or only by bragging

The world theme words required by the seed:
- rank
- accomplish
- relate

The style aim:
- Tall tale: larger-than-life, playful exaggeration, but still grounded in a
  coherent little simulation with a clear beginning, turn, and ending.

This file follows the storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("effort", "noise", "distance", "height", "rank"):
            self.meters.setdefault(k, 0.0)
        for k in ("pride", "worry", "delight", "brag", "resolve", "confusion"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Challenge:
    id: str
    label: str
    verb: str
    gerund: str
    sound: str
    accomplish: str
    rank_needed: int
    effort_cost: float
    noise_cost: float
    relation: str


@dataclass
class Prize:
    label: str
    phrase: str
    rank_word: str
    needed_rank: int


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "fair": Setting("the county fair", "The place smelled like popcorn, sawdust, and sunshine."),
    "barn": Setting("the big red barn", "The boards echoed like a drum when the wind came through."),
    "hill": Setting("the windy hill", "The grass bent low, and the sky looked wide enough to swallow a kite."),
}

CHALLENGES = {
    "log": Challenge(
        id="log",
        label="the floating log crossing",
        verb="cross the log",
        gerund="crossing the log",
        sound="KNOCK-KNOCK-THUD!",
        accomplish="crossed the log straight and true",
        rank_needed=2,
        effort_cost=2.0,
        noise_cost=1.0,
        relation="relate to the river's rhythm",
    ),
    "bell": Challenge(
        id="bell",
        label="the barn bell ring",
        verb="ring the bell",
        gerund="ringing the bell",
        sound="CLANG-CLANG-CLAAAAANG!",
        accomplish="rang the bell so hard it sang back",
        rank_needed=3,
        effort_cost=1.5,
        noise_cost=2.0,
        relation="relate to the bell's deep voice",
    ),
    "stack": Challenge(
        id="stack",
        label="the hay-bale stack",
        verb="stack the hay bales",
        gerund="stacking hay bales",
        sound="HUP! HUP! WHOOMP!",
        accomplish="stacked the hay bales taller than a porch roof",
        rank_needed=2,
        effort_cost=2.5,
        noise_cost=0.5,
        relation="relate to the weight of the hay",
    ),
    "kite": Challenge(
        id="kite",
        label="the kite-raising contest",
        verb="raise the giant kite",
        gerund="raising the giant kite",
        sound="FWOOOOSH!",
        accomplish="raised the giant kite until it tickled the clouds",
        rank_needed=1,
        effort_cost=1.0,
        noise_cost=1.5,
        relation="relate to the wind's push",
    ),
}

PRIZES = {
    "blue": Prize("blue ribbon", "a blue ribbon with a gold edge", "first", 3),
    "red": Prize("red ribbon", "a red ribbon with a bright star", "second", 2),
    "yellow": Prize("yellow ribbon", "a yellow ribbon with a shining fringe", "third", 1),
}

NAMES = ["Mina", "Jo", "Tess", "Nell", "Walt", "Bo", "Zeke", "Ivy", "June", "Otis"]
GROWNUPS = ["uncle", "aunt", "father", "mother", "grandpa", "grandma"]
TRAITS = ["bold", "cheerful", "quick", "sturdy", "bright", "spirited"]


@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    name: str
    grownup: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(setting: Setting, challenge: Challenge, prize: Prize) -> bool:
    return challenge.rank_needed <= prize.needed_rank + 2


def explain_rejection(setting: Setting, challenge: Challenge, prize: Prize) -> str:
    return (
        f"(No story: the {challenge.label} and {prize.label} do not fit a sensible "
        f"rank-and-accomplish tale at {setting.place}. Try a smaller prize or a task "
        f"that can honestly lead to that rank.)"
    )


class StoryWorld:
    def __init__(self, setting: Setting, challenge: Challenge, prize: Prize, hero: Entity, grownup: Entity) -> None:
        self.setting = setting
        self.challenge = challenge
        self.prize = prize
        self.hero = hero
        self.grownup = grownup
        self.noise = 0.0
        self.effort = 0.0
        self.rank = 0
        self.accomplished = False
        self.relation = ""
        self.soundline: list[str] = []


def _rule_noise_to_rank(world: StoryWorld) -> None:
    sig = ("noise_to_rank", world.hero.id, world.challenge.id)
    if sig in world.fired:
        return
    if world.noise >= world.challenge.noise_cost and world.effort >= world.challenge.effort_cost:
        world.fired.add(sig)
        world.rank = max(world.rank, world.challenge.rank_needed)
        world.hero.meters["rank"] = float(world.rank)
        world.hero.memes["pride"] += 1.0


def _rule_accomplish(world: StoryWorld) -> None:
    sig = ("accomplish", world.hero.id, world.challenge.id)
    if sig in world.fired:
        return
    if world.effort >= world.challenge.effort_cost and world.rank >= world.challenge.rank_needed:
        world.fired.add(sig)
        world.accomplished = True
        world.hero.memes["delight"] += 1.0


def _rule_relate(world: StoryWorld) -> None:
    sig = ("relate", world.hero.id, world.challenge.id)
    if sig in world.fired:
        return
    if world.accomplished:
        world.fired.add(sig)
        world.relation = world.challenge.relation
        world.hero.memes["resolve"] += 1.0


def propagate(world: StoryWorld) -> None:
    before = None
    while before != (world.rank, world.accomplished, world.relation, world.noise, world.effort):
        before = (world.rank, world.accomplished, world.relation, world.noise, world.effort)
        _rule_noise_to_rank(world)
        _rule_accomplish(world)
        _rule_relate(world)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("rank_needed", cid, ch.rank_needed))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_rank", pid, pr.needed_rank))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, C, P) :- setting(S), challenge(C), prize(P),
                  rank_needed(C, R1), prize_rank(P, R2), R1 =< R2 + 2.
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for s in SETTINGS:
        for c, ch in CHALLENGES.items():
            for p, pr in PRIZES.items():
                if reasonableness_gate(SETTINGS[s], ch, pr):
                    py.add((s, c, p))
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about rank, accomplish, and relate, with sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--trait", choices=TRAITS)
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
    s = args.setting or rng.choice(list(SETTINGS))
    c = args.challenge or rng.choice(list(CHALLENGES))
    p = args.prize or rng.choice(list(PRIZES))
    if not reasonableness_gate(SETTINGS[s], CHALLENGES[c], PRIZES[p]):
        raise StoryError(explain_rejection(SETTINGS[s], CHALLENGES[c], PRIZES[p]))
    return StoryParams(
        setting=s,
        challenge=c,
        prize=p,
        name=args.name or rng.choice(NAMES),
        grownup=args.grownup or rng.choice(GROWNUPS),
        trait=args.trait or rng.choice(TRAITS),
    )


def build_world(params: StoryParams) -> StoryWorld:
    setting = SETTINGS[params.setting]
    challenge = CHALLENGES[params.challenge]
    prize = PRIZES[params.prize]
    hero = Entity(id=params.name, kind="character", type="boy" if params.name in {"Otis", "Walt", "Bo", "Zeke"} else "girl")
    grownup = Entity(id=params.grownup.title(), kind="character", type=params.grownup)
    return StoryWorld(setting, challenge, prize, hero, grownup)


def tell(params: StoryParams) -> StoryWorld:
    world = build_world(params)
    h, g, c, p = world.hero, world.grownup, world.challenge, world.prize

    h.memes["resolve"] += 1.0
    world.soundline.append(c.sound)

    world.hero.meters["effort"] += c.effort_cost / 2
    world.effort += c.effort_cost / 2
    world.noise += c.noise_cost / 2

    first = f"{h.id} was a {params.trait} {h.type} who could {c.relation} as easy as blinking."
    second = f"At {world.setting.place}, {g.id} told a tall tale about a task that could {c.accomplish}."
    third = f"{h.id} loved the sound of {c.sound} because it made the whole world feel ready to move."
    world_facts = [first, second, third]
    world.paragraphs[0].extend(world_facts)

    world.para()
    world.say(
        f"One day, the pair marched to {world.setting.place}. {world.setting.detail} "
        f"The judge held up {p.phrase} and said the winner would get the {p.rank_word} rank."
    )
    world.say(
        f'{h.id} said, "I can {c.verb}!" and {g.id} answered, '
        f'"Then we will see whether that big talk can become a big accomplish!"'
    )

    world.para()
    world.say(
        f"{h.id} climbed up, and the fair went quiet as a tick-tock clock. "
        f"Then came {c.sound} as {h.id} started {c.gerund} with both boots planted and both elbows out."
    )
    world.effort += c.effort_cost
    world.noise += c.noise_cost
    h.meters["effort"] += c.effort_cost
    h.meters["noise"] += c.noise_cost
    propagate(world)

    if world.accomplished:
        world.say(
            f"{h.id} {c.accomplish}. That let the judge rank {h.id}'s work right at the top of the board."
        )
        world.say(
            f"{g.id} grinned and said the sound of the deed matched the size of the deed itself."
        )
    else:
        world.say(
            f"The first try wobbled like a fence in a thunderstorm, and the deed was not finished yet."
        )
        world.say(
            f"{g.id} leaned close and showed {h.id} how to aim the effort where the task could hear it best."
        )
        world.para()
        world.say(
            f"On the second try came {c.sound} again, louder than a goose in a thunder hat. "
            f"This time the work stuck, and the rank rose up like a flag in a prairie wind."
        )
        world.effort += 1.0
        world.noise += 1.0
        h.meters["effort"] += 1.0
        h.meters["noise"] += 1.0
        propagate(world)

    world.para()
    if world.accomplished:
        world.say(
            f"In the end, {h.id} won the {p.label}, and everyone could see how the sound, the effort, "
            f"and the rank all related to one another."
        )
        world.say(
            f"{h.id} carried the ribbon home like a banner, still humming the same great {c.sound} under {h.id.lower()} breath."
        )
    else:
        world.say(
            f"In the end, {h.id} did not earn the ribbon, but {h.id} did learn how true effort and true sound must go together."
        )
    world.facts.update(hero=h, grownup=g, challenge=c, prize=p)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    return [
        f'Write a tall tale for a child about how {world.hero.id} can rank a daring deed by sound alone.',
        f'Tell a playful story where someone tries to accomplish {world.challenge.label} and learns to relate the sound to the effort.',
        f'Write a short story with the words "rank", "accomplish", and "relate" and at least one big sound effect.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    h, g, c, p = world.hero, world.grownup, world.challenge, world.prize
    return [
        QAItem(
            question=f"What was {h.id} trying to accomplish at {world.setting.place}?",
            answer=f"{h.id} was trying to {c.verb}. It was a big, tall-tale sort of job, and the sound effects helped show the effort.",
        ),
        QAItem(
            question=f"Why did the story keep using {c.sound}?",
            answer=f"The sound {c.sound} belonged to the challenge, and it helped the story relate the noise to how hard {h.id} was working.",
        ),
        QAItem(
            question=f"How did {h.id} get the {p.label}?",
            answer=f"{h.id} worked hard enough to {c.accomplish}, and that let the judge rank the work high enough for the {p.label}.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rank?",
            answer="A rank is a position in order, like first, second, or third.",
        ),
        QAItem(
            question="What does accomplish mean?",
            answer="To accomplish something means to finish it or get it done.",
        ),
        QAItem(
            question="What does relate mean?",
            answer="To relate things means to show how they are connected or how one thing helps explain another.",
        ),
        QAItem(
            question="What is a sound effect in a story?",
            answer="A sound effect is a written noise like BOOM, CLANG, or WHOOSH that helps the reader imagine the action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"setting={world.setting.place}")
    lines.append(f"challenge={world.challenge.id}")
    lines.append(f"prize={world.prize.label}")
    lines.append(f"rank={world.rank}")
    lines.append(f"accomplished={world.accomplished}")
    lines.append(f"effort={world.effort}")
    lines.append(f"noise={world.noise}")
    lines.append(f"relation={world.relation}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("fair", "bell", "blue", "June", "uncle", "bold"),
    StoryParams("barn", "stack", "red", "Mina", "grandpa", "sturdy"),
    StoryParams("hill", "kite", "yellow", "Otis", "aunt", "bright"),
]


def asp_verify_story() -> int:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("Story generation failed.")
        return 1
    print("OK: generated a story sample for verification.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(0 if asp_verify() == 0 and asp_verify_story() == 0 else 1)
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, challenge, prize) combos:")
        for s, c, p in combos:
            print(f"  {s:8} {c:10} {p}")
        return

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
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i - 1
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
