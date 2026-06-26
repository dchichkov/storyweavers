#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a child helping at a market stall while
following a cautious hunch and learning that bravery can look gentle.
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

SAFETY_THRESHOLD = 1.0


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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool
    has_cover: bool


@dataclass
class Scenario:
    id: str
    want: str
    gerund: str
    risk: str
    risk_kind: str
    hint: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Protection:
    id: str
    label: str
    phrase: str
    covers: set[str]
    neutralizes: set[str]
    offer: str
    ending: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def clean_article(phrase: str) -> str:
    return phrase if phrase.startswith(("a ", "an ", "the ")) else f"a {phrase}"


def need_an(word: str) -> bool:
    return word[:1].lower() in "aeiou"


def with_article(phrase: str) -> str:
    return f"an {phrase}" if need_an(phrase) else f"a {phrase}"


SETTINGS = {
    "market": Setting(place="the little market", indoor=False, has_cover=True),
    "bakery": Setting(place="the bakery window", indoor=True, has_cover=True),
    "street": Setting(place="the corner street", indoor=False, has_cover=False),
    "community-garden": Setting(place="the community garden stall", indoor=False, has_cover=True),
}

SCENARIOS = {
    "wind": Scenario(
        id="wind",
        want="help at the stall",
        gerund="helping at the stall",
        risk="the sign might blow over",
        risk_kind="blown",
        hint="the wind kept tugging at the paper price tags",
        zone="stall",
        keyword="stall",
        tags={"stall", "wind", "protection"},
    ),
    "rain": Scenario(
        id="rain",
        want="stay dry while helping at the stall",
        gerund="working under the awning",
        risk="the baskets might get wet",
        risk_kind="wet",
        hint="clouds made the day feel damp and gray",
        zone="stall",
        keyword="protection",
        tags={"protection", "rain"},
    ),
    "dust": Scenario(
        id="dust",
        want="keep the jars clean",
        gerund="arranging the jars carefully",
        risk="the jars might get dusty",
        risk_kind="dusty",
        hint="the road beside the stall was dry and powdery",
        zone="stall",
        keyword="hunch",
        tags={"hunch", "stall"},
    ),
}

PROTECTIONS = {
    "weights": Protection(
        id="weights",
        label="small stone weights",
        phrase="a pair of small stone weights",
        covers={"stall"},
        neutralizes={"blown"},
        offer="put the weights on the cloth corners first",
        ending="set the stone weights on the cloth",
    ),
    "awning": Protection(
        id="awning",
        label="a canvas awning",
        phrase="a wide canvas awning",
        covers={"stall"},
        neutralizes={"wet"},
        offer="pull out the canvas awning first",
        ending="smiled under the awning",
    ),
    "cloth": Protection(
        id="cloth",
        label="a clean cloth cover",
        phrase="a clean cloth cover",
        covers={"stall"},
        neutralizes={"dusty"},
        offer="cover the jars with a clean cloth first",
        ending="covered the jars with the cloth",
    ),
}

HERO_NAMES = ["Mina", "Iris", "Noah", "Tavi", "Leah", "Jun", "Maya", "Owen"]
ADULT_NAMES = ["Aunt Ren", "Uncle Bo", "Mom", "Dad", "Aunt Suri", "Mr. Vale"]
TRAITS = ["brave", "careful", "patient", "curious", "steady", "gentle"]


@dataclass
class StoryParams:
    setting: str
    scenario: str
    protection: str
    name: str
    age_word: str
    adult: str
    trait: str
    seed: Optional[int] = None


def reasonableness_gate(scenario: Scenario, protection: Protection) -> bool:
    return scenario.risk_kind in protection.neutralizes and scenario.zone in protection.covers


def explain_rejection(scenario: Scenario, protection: Protection) -> str:
    return (
        f"(No story: {protection.label} does not protect the stall from {scenario.risk_kind} problems. "
        f"Try a protection that fits the risk.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with hunches, stall work, and protection.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--protection", choices=PROTECTIONS)
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULT_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--age-word", default="little")
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
    setting_id = args.setting or rng.choice(list(SETTINGS))
    scenario_id = args.scenario or rng.choice([s for s in SCENARIOS if s in {"wind", "rain", "dust"}])
    scenario = SCENARIOS[scenario_id]
    protection_id = args.protection or rng.choice(list(PROTECTIONS))
    protection = PROTECTIONS[protection_id]
    if not reasonableness_gate(scenario, protection):
        raise StoryError(explain_rejection(scenario, protection))
    name = args.name or rng.choice(HERO_NAMES)
    adult = args.adult or rng.choice(ADULT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting_id, scenario=scenario_id, protection=protection_id, name=name, age_word=args.age_word, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    scenario = SCENARIOS[params.scenario]
    protection = PROTECTIONS[params.protection]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in {"Mina", "Iris", "Leah", "Maya"} else "boy", memes={"bravery": 0, "caution": 0, "joy": 0, "hunch": 0}))
    adult = world.add(Entity(id=params.adult, kind="character", type="adult", label=params.adult, memes={"worry": 0, "warmth": 0}))
    prop = world.add(Entity(id=protection.id, type="thing", label=protection.label, phrase=protection.phrase, owner=child.id, caretaker=adult.id, protective=True, worn_by=child.id))

    child.memes["hunch"] += 1
    child.memes["caution"] += 1
    world.say(f"{child.id} was {clean_article(params.age_word)} {params.trait} child who liked helping {adult.id} at the market stall.")
    world.say(f"One day, {child.id} had a quiet hunch that {scenario.hint}.")
    world.say(f"{child.id} loved {scenario.gerund}, even when the work felt small and steady.")
    world.say(f"{adult.id} was setting out cups and bread, and {child.id} noticed {scenario.risk}.")

    world.say(f"{child.id} wanted to {scenario.want}, but {adult.id} said, “Let’s be careful first.”")
    if scenario.id == "wind":
        world.say(f"{child.id} looked at {prop.phrase} and decided to use them before the gusts got stronger.")
    elif scenario.id == "rain":
        world.say(f"{child.id} pointed at the sky, and {adult.id} reached for {protection.offer}.")
    else:
        world.say(f"{child.id} smiled and helped {adult.id} {protection.offer}.")

    child.memes["bravery"] += 1
    adult.memes["warmth"] += 1
    world.say(f"That was brave in a quiet way, because {child.id} did not rush; {child.id} chose care, and the stall stayed safe.")
    world.say(f"Together they {protection.ending}, and the little market felt calm again.")

    world.facts.update(child=child, adult=adult, scenario=scenario, protection=protection, setting=setting, param=params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    scenario = f["scenario"]
    return [
        f'Write a soft slice-of-life story about {child.id} and a market stall, including the word "{scenario.keyword}".',
        f"Tell a child-friendly story where a hunch helps {child.id} choose protection before helping at the stall.",
        f"Write a gentle story about bravery and caution that ends with a calm market stall.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    scenario = f["scenario"]
    protection = f["protection"]
    return [
        QAItem(
            question=f"What did {child.id} notice with a hunch?",
            answer=f"{child.id} noticed that {scenario.hint}, so {child.id} paid attention before helping at the stall.",
        ),
        QAItem(
            question=f"Who helped {child.id} stay careful at the stall?",
            answer=f"{adult.id} helped {child.id} stay careful, and they used {protection.phrase} to protect the stall.",
        ),
        QAItem(
            question=f"How was {child.id} brave?",
            answer=f"{child.id} was brave by choosing to help in a careful way instead of rushing in too soon.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"{child.id} and {adult.id} used {protection.label} to keep the stall safe, and the day settled back into a calm, ordinary rhythm.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    scenario = f["scenario"]
    protection = f["protection"]
    out = [
        QAItem(
            question="What is a hunch?",
            answer="A hunch is a quiet feeling that something might happen, even before you know all the facts.",
        ),
        QAItem(
            question="What does protection do?",
            answer="Protection helps keep something safe from harm, like cover that blocks wind, rain, or dust.",
        ),
        QAItem(
            question="What is a stall?",
            answer="A stall is a small place where someone sells or shows things, often at a market.",
        ),
    ]
    if "wind" in scenario.tags:
        out.append(QAItem(question="Why do people use weights on a cloth?", answer="People use weights so the cloth does not lift and flap away in the wind."))
    if "rain" in scenario.tags:
        out.append(QAItem(question="Why do people use an awning?", answer="People use an awning to make a dry space under light rain or strong sun."))
    if "dust" in scenario.tags:
        out.append(QAItem(question="Why cover jars with cloth?", answer="A cloth cover helps keep dust and dirt off things that should stay clean."))
    if protection.id == "weights":
        out.append(QAItem(question="What are small stone weights for?", answer="Small stone weights hold down paper, cloth, or signs so the wind cannot blow them away."))
    return out


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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="market", scenario="wind", protection="weights", name="Mina", age_word="little", adult="Aunt Ren", trait="brave"),
    StoryParams(setting="bakery", scenario="rain", protection="awning", name="Leah", age_word="small", adult="Mom", trait="careful"),
    StoryParams(setting="community-garden", scenario="dust", protection="cloth", name="Jun", age_word="little", adult="Dad", trait="gentle"),
]


ASP_RULES = r"""
scenario_risk(wind, blown).
scenario_risk(rain, wet).
scenario_risk(dust, dusty).

protection_neutralizes(weights, blown).
protection_neutralizes(awning, wet).
protection_neutralizes(cloth, dusty).

covers(weights, stall).
covers(awning, stall).
covers(cloth, stall).

valid(S, P) :- scenario_risk(S, R), protection_neutralizes(P, R), covers(P, stall).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("risk_kind", sid, s.risk_kind))
    for pid, p in PROTECTIONS.items():
        lines.append(asp.fact("protection", pid))
        for c in sorted(p.covers):
            lines.append(asp.fact("covers", pid, c))
        for n in sorted(p.neutralizes):
            lines.append(asp.fact("neutralizes", pid, n))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    asp_set = sorted(set(asp.atoms(model, "valid")))
    py_set = sorted((s, p) for s in SCENARIOS for p in PROTECTIONS if reasonableness_gate(SCENARIOS[s], PROTECTIONS[p]))
    if set(asp_set) == set(py_set):
        print(f"OK: clingo gate matches Python reasonableness gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("asp:", asp_set)
    print("py :", py_set)
    return 1


def build_valid_pairs() -> list[tuple[str, str]]:
    return [(s, p) for s in SCENARIOS for p in PROTECTIONS if reasonableness_gate(SCENARIOS[s], PROTECTIONS[p])]


def resolve_pairs(args: argparse.Namespace, rng: random.Random) -> tuple[str, str]:
    pairs = build_valid_pairs()
    if args.scenario:
        pairs = [x for x in pairs if x[0] == args.scenario]
    if args.protection:
        pairs = [x for x in pairs if x[1] == args.protection]
    if not pairs:
        raise StoryError("(No valid combination matches the given options.)")
    return rng.choice(sorted(pairs))


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
        import asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid scenario/protection pairs:")
        for s, p in vals:
            print(f"  {s:5}  {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                if args.setting or args.scenario or args.protection:
                    scenario_id, protection_id = resolve_pairs(args, rng)
                else:
                    scenario_id, protection_id = rng.choice(build_valid_pairs())
                setting_id = args.setting or rng.choice(list(SETTINGS))
                if not reasonableness_gate(SCENARIOS[scenario_id], PROTECTIONS[protection_id]):
                    raise StoryError(explain_rejection(SCENARIOS[scenario_id], PROTECTIONS[protection_id]))
                params = StoryParams(
                    setting=setting_id,
                    scenario=scenario_id,
                    protection=protection_id,
                    name=args.name or rng.choice(HERO_NAMES),
                    age_word=args.age_word,
                    adult=args.adult or rng.choice(ADULT_NAMES),
                    trait=args.trait or rng.choice(TRAITS),
                    seed=seed,
                )
            except StoryError as err:
                print(err)
                return
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
            header = f"### {p.name}: {p.scenario} with {p.protection}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
