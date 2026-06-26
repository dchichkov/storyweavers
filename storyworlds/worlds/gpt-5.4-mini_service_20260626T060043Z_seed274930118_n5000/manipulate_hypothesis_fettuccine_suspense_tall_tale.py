#!/usr/bin/env python3
"""
storyworlds/worlds/manipulate_hypothesis_fettuccine_suspense_tall_tale.py
=========================================================================

A small tall-tale storyworld about a huge kitchen, a daring hypothesis, and
one impossibly long ribbon of fettuccine.

Premise:
- A child dreams up a hypothesis about how to make fettuccine twirl into a
  shape big enough to reach a soup pot.
- A grown-up worries the plan will splatter sauce everywhere.
- The child tries to manipulate the noodle with clever tools.
- Suspense comes from whether the noodle will behave, and the ending proves a
  surprising result.

This script is intentionally self-contained: it models the world, narrates the
story from the simulated state, and mirrors its reasonableness gate in ASP.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    verb: str
    help_text: str
    succeeds_against: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    noun: str
    risk: str
    mess: str
    event: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    challenge: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"twirl", "lift", "stir"}),
    "pantry": Setting(place="the pantry", indoor=True, affords={"twirl", "lift"}),
}

CHALLENGES = {
    "twirl": Challenge(
        id="twirl",
        label="fettuccine twirling",
        noun="fettuccine",
        risk="sauce-spattered",
        mess="saucy",
        event="twirled up like a golden lariat",
        requires={"fork", "spoon"},
        tags={"fettuccine", "sauce", "mess"},
    ),
    "stretch": Challenge(
        id="stretch",
        label="fettuccine stretching",
        noun="fettuccine",
        risk="slippery",
        mess="saucy",
        event="stretched long as a ribbon in a parade",
        requires={"fork", "tongs"},
        tags={"fettuccine", "sauce", "mess"},
    ),
}

PRIZES = {
    "apron": Prize(id="apron", label="apron", phrase="a bright blue apron", region="torso"),
    "tablecloth": Prize(id="tablecloth", label="tablecloth", phrase="a white tablecloth", region="table"),
}

TOOLS = [
    Tool(id="fork", label="a fork", verb="spin", help_text="a fork can catch slippery noodles", succeeds_against={"twirl", "stretch"}),
    Tool(id="tongs", label="a pair of tongs", verb="lift", help_text="tongs can hold long noodles steady", succeeds_against={"stretch"}),
    Tool(id="spoon", label="a spoon", verb="nudge", help_text="a spoon can guide a noodle into place", succeeds_against={"twirl"}),
]

GIRL_NAMES = ["Mina", "Lola", "Zia", "Nora", "Ivy", "Ada"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Finn", "Jasper"]
TRAITS = ["brave", "curious", "clever", "spirited", "bold", "cheerful"]


def reasonableness_ok(challenge: Challenge, prize: Prize) -> bool:
    return challenge.id in {"twirl", "stretch"} and prize.id in {"apron", "tablecloth"}


def select_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS:
        if challenge.id in tool.succeeds_against:
            return tool
    return None


def explain_rejection(challenge: Challenge, prize: Prize) -> str:
    return (
        f"(No story: {challenge.label} and {prize.label} do not make a sensible "
        f"tall-tale problem here.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: manipulate a hypothesis about fettuccine."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CHALLENGES:
            for p in PRIZES:
                if reasonableness_ok(CHALLENGES[c], PRIZES[p]):
                    combos.append((s, c, p))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.prize:
        if not reasonableness_ok(CHALLENGES[args.challenge], PRIZES[args.prize]):
            raise StoryError(explain_rejection(CHALLENGES[args.challenge], PRIZES[args.prize]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, prize = rng.choice(sorted(combos))
    pr = PRIZES[prize]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _do_challenge(world: World, actor: Entity, challenge: Challenge, prize: Entity, narrate: bool = True) -> None:
    actor.meters["effort"] = actor.meters.get("effort", 0) + 1
    actor.memes["hope"] = actor.memes.get("hope", 0) + 1
    if challenge.id == "twirl":
        actor.memes["suspense"] = actor.memes.get("suspense", 0) + 1
    if prize.worn_by == actor.id:
        actor.meters["mess"] = actor.meters.get("mess", 0) + 1
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} tried to {challenge.label}.")


def predict_outcome(world: World, actor: Entity, challenge: Challenge, prize_id: str) -> dict:
    sim = world.copy()
    _do_challenge(sim, sim.get(actor.id), challenge, sim.get(prize_id), narrate=False)
    prize = sim.get(prize_id)
    return {"messy": prize.meters.get("mess", 0) >= THRESHOLD}


def tell(world: World, hero: Entity, helper: Entity, prize: Entity, challenge: Challenge) -> None:
    tool = select_tool(challenge)
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1

    world.say(
        f"{hero.id} was a {hero.type} so {hero.pronoun('possessive')} curiosity "
        f"could climb a fence and look over the moon. "
        f"{hero.pronoun().capitalize()} had a hypothesis: if {hero.pronoun('subject')} "
        f"could manipulate the {challenge.noun} just right, it would dance instead of drip."
    )
    world.say(
        f"On a bright day in {world.setting.place}, {hero.id} wore {hero.pronoun('possessive')} {prize.label} "
        f"and listened while {helper.pronoun().capitalize()} warned, "
        f"\"That noodle is long enough to lasso a wagon wheel.\""
    )

    world.para()
    world.say(
        f"{hero.id} held up {tool.label if tool else 'careful hands'} and studied the {challenge.noun} like a scientist with a top hat."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to manipulate the noodle without making {prize.it()} messy, "
        f"because {helper.pronoun('subject')} worried {prize.it()} would be {challenge.risk}."
    )

    world.para()
    _do_challenge(world, hero, challenge, prize, narrate=False)
    world.say(
        f"Then came the suspense: the {challenge.noun} lifted, twirled, and hung in the air "
        f"like a golden ribbon trying to remember the wind."
    )
    if challenge.id == "stretch":
        world.say(
            f"{tool.label if tool else 'The kitchen'} helped keep it steady, and the fettuccine stretched exactly as the hypothesis predicted."
        )
    else:
        world.say(
            f"{tool.label if tool else 'A spoon'} nudged it into a neat spiral, and the noodle behaved as if it had been trained by circus stars."
        )

    outcome = predict_outcome(world, hero, challenge, prize.id)
    world.para()
    if outcome["messy"]:
        world.say(
            f"One little splash reached the {prize.label}, but {helper.pronoun('subject')} laughed, wiped it clean, and called it a successful experiment."
        )
    else:
        world.say(
            f"The {prize.label} stayed clean, the hypothesis proved true, and the great noodle settled down without a single splash."
        )
    world.say(
        f"In the end, {hero.id} and {helper.pronoun('subject')} ate dinner beside a bowl of shining fettuccine, "
        f"and the whole kitchen felt as grand as a parade under the stars."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        challenge=challenge,
        tool=tool,
    )


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    challenge = f["challenge"]
    prize = f["prize"]
    return [
        f'Write a tall-tale story for a child about a hypothesis, {challenge.noun}, and a brave kitchen experiment.',
        f"Tell a suspenseful story where {hero.id} tries to manipulate {prize.phrase} with a clever tool and learns what the fettuccine will do.",
        f'Write a short story that uses the words "manipulate", "hypothesis", and "fettuccine" and ends with a surprising dinner table image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    challenge = f["challenge"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What was {hero.id}'s hypothesis about the fettuccine?",
            answer=(
                f"{hero.id} thought that if {hero.pronoun('subject')} could manipulate the {challenge.noun} just right, "
                f"it would twirl neatly instead of making a mess."
            ),
        ),
        QAItem(
            question=f"Who warned {hero.id} about the fettuccine experiment?",
            answer=(
                f"{helper.pronoun().capitalize()} warned {hero.id} because the fettuccine was long, slippery, and could splash the {prize.label}."
            ),
        ),
        QAItem(
            question=f"What tool helped {hero.id} with the noodle?",
            answer=f"{tool.label if tool else 'Careful hands'} helped {hero.id} guide the fettuccine during the experiment.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"The fettuccine settled down, the hypothesis was proven, and {hero.id} ended the day eating dinner beside a shining bowl."
            ),
        ),
    ]


KNOWLEDGE = {
    "fettuccine": [
        (
            "What is fettuccine?",
            "Fettuccine is a type of pasta made of long, flat noodles.",
        )
    ],
    "hypothesis": [
        (
            "What is a hypothesis?",
            "A hypothesis is a guess you can test to see if it is true.",
        )
    ],
    "manipulate": [
        (
            "What does manipulate mean?",
            "To manipulate something means to handle or move it carefully and skillfully.",
        )
    ],
    "suspense": [
        (
            "What is suspense in a story?",
            "Suspense is the feeling of wondering what will happen next.",
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    out: list[QAItem] = []
    for key in ["manipulate", "hypothesis", "fettuccine", "suspense"]:
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
challenge(C) :- challenge_fact(C).
prize(P) :- prize_fact(P).

valid_story(S, C, P) :- setting_fact(S), challenge_fact(C), prize_fact(P),
                        reasonable(C, P).

reasonable(twirl, apron).
reasonable(twirl, tablecloth).
reasonable(stretch, apron).
reasonable(stretch, tablecloth).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for c in CHALLENGES:
        lines.append(asp.fact("challenge_fact", c))
    for p in PRIZES:
        lines.append(asp.fact("prize_fact", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=params.helper))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase))
    challenge = CHALLENGES[params.challenge]
    tell(world, hero, helper, prize, challenge)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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


CURATED = [
    StoryParams(setting="kitchen", challenge="twirl", prize="apron", name="Mina", gender="girl", helper="mother", trait="clever"),
    StoryParams(setting="kitchen", challenge="stretch", prize="tablecloth", name="Owen", gender="boy", helper="father", trait="bold"),
]


def build_curated() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.challenge} in {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
