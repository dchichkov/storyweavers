#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py
===================================================================================

A small standalone storyworld in a folk-tale style: a curious child in an
American riverside village follows a mystery, gathers clues from the world model,
and reaches a happy ending by solving it with care instead of rushing.

The domain is intentionally tiny:
- one child
- one elder guide
- one missing/strange thing to investigate
- a few concrete places and clues
- a calm resolution image that proves what changed

The story is driven by state:
- curiosity rises as the child notices odd facts
- clues move from one place/entity to another
- a tension beat appears when a suspicious sign is discovered
- the solution is found by comparing clues, not by magic
- the ending shows the mystery resolved and the child calmer and prouder

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/american_curiosity_happy_ending_mystery_to_solve.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

MOODS = ["calm", "curious", "hopeful", "troubled", "relieved", "proud"]
PLACES = ["porch", "garden", "barn", "riverbank", "market", "schoolyard"]
MYSTERIES = ["missing pie", "lost key", "gone bell", "empty basket", "hidden letter"]
CLUES = ["muddy footprints", "blue thread", "crumbs", "fresh hay", "a torn ribbon", "a whistle tune"]
SOLUTIONS = ["the goat", "the wind", "the baker's boy", "the old cat", "the laughing brook"]

GIRL_NAMES = ["Mabel", "Nell", "Ada", "Rose", "Lily", "June", "Anna"]
BOY_NAMES = ["Ben", "Tom", "Eli", "Sam", "Nate", "Owen", "Will"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mystery:
    id: str
    missing: str
    clue: str
    found_at: str
    culprit: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    clue1: str
    clue2: str
    culprit: str
    hero: str
    hero_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_curiosity(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["curiosity"] >= THRESHOLD and ("curious", "spark") not in world.fired:
        world.fired.add(("curious", "spark"))
        hero.memes["curiosity"] += 1
        out.append("__curious__")
    return out


def _r_clue_chain(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    clue1 = world.get("clue1")
    clue2 = world.get("clue2")
    if clue1.meters["found"] >= THRESHOLD and clue2.meters["found"] < THRESHOLD:
        if ("clue2", clue2.id) not in world.fired:
            world.fired.add(("clue2", clue2.id))
            clue2.meters["found"] += 1
            hero.memes["hope"] += 1
            out.append("__clue2__")
    return out


def _r_resolution(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    mystery = world.get("mystery")
    if hero.meters["solved"] >= THRESHOLD and ("resolved", mystery.id) not in world.fired:
        world.fired.add(("resolved", mystery.id))
        mystery.meters["resolved"] += 1
        out.append("__resolved__")
    return out


CAUSAL_RULES = [Rule("curiosity", _r_curiosity), Rule("clue_chain", _r_clue_chain), Rule("resolution", _r_resolution)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend([s for s in sents if not s.startswith("__")])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _find_clue(world: World, finder: Entity, clue: Entity, place: Entity, text: str) -> None:
    finder.memes["curiosity"] += 1
    clue.meters["found"] += 1
    place.meters["visited"] += 1
    world.say(text)
    propagate(world, narrate=False)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=params.hero_gender, role="child"))
    elder = world.add(Entity("elder", kind="character", type=params.elder_gender, role="guide"))
    mystery = world.add(Entity("mystery", kind="thing", label=params.mystery))
    place = world.add(Entity("place", kind="place", label=params.place))
    clue1 = world.add(Entity("clue1", kind="thing", label=params.clue1))
    clue2 = world.add(Entity("clue2", kind="thing", label=params.clue2))
    culprit = world.add(Entity("culprit", kind="thing", label=params.culprit))

    hero.id = params.hero
    elder.id = params.elder

    hero.memes["curiosity"] = 2
    elder.memes["calm"] = 2
    world.facts.update(hero=hero, elder=elder, mystery=mystery, place=place, clue1=clue1, clue2=clue2, culprit=culprit, params=params)

    world.say(
        f"In an American village by the river, {hero.id} was a little child with a bright mind and a bigger question."
    )
    world.say(
        f"One morning, {hero.id} noticed a {params.mystery} at {params.place}, and the oddness would not leave {hero.pronoun('possessive')} thoughts."
    )

    world.para()
    world.say(
        f'{hero.id} wandered closer with careful feet. "Why is it gone?" {hero.pronoun()} whispered, and {hero.pronoun("possessive")} curiosity grew like a lantern in the dark.'
    )
    _find_clue(
        world,
        hero,
        clue1,
        place,
        f"Under a rail and beside some old straw, {hero.id} found {params.clue1}."
    )

    world.para()
    world.say(
        f"{params.elder} came along and smiled at the little search. \"A mystery is a patient thing,\" {elder.pronoun()} said. \"Look for what does not fit.\""
    )
    _find_clue(
        world,
        hero,
        clue2,
        place,
        f"Then {hero.id} saw {params.clue2} by the door, and the pieces began to fit together."
    )

    world.para()
    hero.meters["solved"] += 1
    world.say(
        f"{hero.id} thought of the clues together and guessed the answer at last: the {params.culprit} had carried the missing thing away."
    )
    world.say(
        f"{params.elder} laughed softly and led {hero.id} to the right corner, where the {params.mystery} was found safe and sound."
    )

    world.para()
    world.say(
        f"By evening, everyone knew the answer, and the little village was peaceful again."
    )
    world.say(
        f"{hero.id} stood a little taller, with a calm heart and a happy grin, because curiosity had led to a solved mystery instead of a worry."
    )

    world.facts["outcome"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a folk-tale story for a small child in an American village where {p.hero} notices a mystery and solves it with help from an elder.",
        f"Tell a happy ending story where curiosity leads {p.hero} to follow two clues and discover who took the missing {p.mystery}.",
        f"Write a gentle mystery-to-solve tale that includes the word 'american' and ends with relief, pride, and a found treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    elder = world.facts["elder"]
    mystery = world.facts["mystery"]
    clue1 = world.facts["clue1"]
    clue2 = world.facts["clue2"]
    culprit = world.facts["culprit"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep looking around?",
            answer=f"{hero.id} was curious about the missing {p.mystery}, so {hero.pronoun()} kept looking for clues. {hero.id} did not want to guess in a hurry; {hero.pronoun('possessive')} careful looking helped solve the mystery."
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{hero.id} found {clue1.label} and then {clue2.label}, and the two clues pointed to the {culprit.label}. After that, {elder.id} helped {hero.id} find the missing {mystery.label} safely."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily, with the missing {mystery.label} found and the village calm again. {hero.id} felt proud because curiosity helped turn a worry into an answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to know more, ask questions, and look closely at what is strange or new."
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that does not make sense right away. People solve mysteries by noticing clues and thinking about them carefully."
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish safe, relieved, or joyful."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


@dataclass
class StoryState:
    place: str
    mystery: str
    clue1: str
    clue2: str
    culprit: str


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for clue1 in CLUES:
                for clue2 in CLUES:
                    if clue1 == clue2:
                        continue
                    for culprit in SOLUTIONS:
                        combos.append((place, mystery, clue1, clue2, culprit))
    return combos


def explain_rejection(_: StoryParams) -> str:
    return "(No story: the requested mystery setup could not be made reasonable.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an American folk-tale curiosity mystery with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue1", choices=CLUES)
    ap.add_argument("--clue2", choices=CLUES)
    ap.add_argument("--culprit", choices=SOLUTIONS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "mother", "father"])
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
    place = args.place or rng.choice(PLACES)
    mystery = args.mystery or rng.choice(MYSTERIES)
    clue1 = args.clue1 or rng.choice(CLUES)
    clue2 = args.clue2 or rng.choice([c for c in CLUES if c != clue1])
    culprit = args.culprit or rng.choice(SOLUTIONS)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_gender = args.elder_gender or rng.choice(["mother", "father"])
    elder = args.elder or rng.choice(GIRL_NAMES if elder_gender in {"mother", "woman"} else BOY_NAMES)
    return StoryParams(place, mystery, clue1, clue2, culprit, hero, hero_gender, elder, elder_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(P, M, C1, C2, Cul) :- place(P), mystery(M), clue(C1), clue(C2), clue(C1), clue(C2), C1 != C2, culprit(Cul).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for c in SOLUTIONS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = clingo_set == python_set
    if ok:
        print(f"OK: ASP matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, clue1=None, clue2=None, culprit=None, hero=None, hero_gender=None, elder=None, elder_gender=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"FAIL: generate() smoke test crashed: {exc}")
        return 1
    return 0 if ok else 1


CURATED = [
    StoryParams("barn", "gone bell", "muddy footprints", "blue thread", "the goat", "Mabel", "girl", "Grandma", "mother"),
    StoryParams("riverbank", "missing pie", "crumbs", "fresh hay", "the wind", "Ben", "boy", "Grandpa", "father"),
    StoryParams("garden", "hidden letter", "a torn ribbon", "a whistle tune", "the baker's boy", "June", "girl", "Aunt May", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:")
        for row in combos[:20]:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
