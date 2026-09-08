#!/usr/bin/env python3
"""A child-facing superhero story about bacon, a twist, and reconciliation."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Hero:
    name: str
    title: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Case:
    smell: str
    first_guess: str
    twist: str
    truth: str
    safe_action: str
    repair: str
    reconciliation: str
    ending: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    partner_name: str = "Bramble"
    place: str = "the Moonlight Diner"
    case: str = "smoke_alarm"
    route: str = "signal_first"


@dataclass
class World:
    hero: Hero
    partner: Hero
    place: Place
    case: Case
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


CASES = {
    "smoke_alarm": Case(
        "A sharp bacon smell curled through the Moonlight Diner",
        "the grill fire had leaped too high",
        "the smoke alarm was chirping, but no fire was burning",
        "a strip of bacon had fallen across a warm drain cover and made a tiny cloud of steam",
        "used her heat-proof cape to block the steam while Bramble called the diner cook",
        "the cook removed the bacon with long tongs, cooled the drain cover, and cleaned the alarm",
        "Luna admitted she had blamed Bramble for leaving the grill on, and Bramble forgave her after she listened",
        "the diner window glowed softly while fresh bacon sizzled safely on the cleaned grill",
    ),
    "missing_plate": Case(
        "the hero breakfast plate was gone",
        "a sneaky thief had taken the bacon",
        "the plate was not stolen; it was balanced on the rooftop weather vane",
        "a gust had lifted the paper tablecloth and carried the light plate upward",
        "followed the plate from the ground while Bramble kept everyone inside",
        "lowered the vane with a rescue rope and moved plates away from the open window",
        "Luna thanked Bramble for warning her not to leap, and Bramble accepted her apology for arguing",
        "the recovered plate rested on a sturdy table as friends shared the bacon",
    ),
    "yellow_cape": Case(
        "a yellow cape flashed beside the kitchen",
        "a masked villain was hiding near the pantry",
        "the flash came from a mop bucket mirror",
        "sunlight bounced from the clean bucket whenever the swinging door moved",
        "asked Bramble to stand at the doorway while she checked the reflection from a safe distance",
        "turned the bucket away from the sun and placed a bright warning ribbon on the door",
        "Bramble confessed that fear had made him shout, and Luna said she should have asked before teasing him",
        "the harmless bucket shone only once, beneath a calm afternoon sky",
    ),
}

ROUTES = ("signal_first", "dialogue_first", "alarm_first", "friend_first", "twist_first")

PLACES = {
    "the Moonlight Diner": Place("the Moonlight Diner"),
    "the Comet Kitchen": Place("the Comet Kitchen"),
    "the Starry Food Truck": Place("the Starry Food Truck"),
}

HEROES = (
    ("Luna", "Captain Moonbeam"),
    ("Nova", "Shield Star"),
    ("Pip", "Rocket Helper"),
)

PARTNERS = (
    ("Bramble", "Kindness Knight"),
    ("Tess", "Truth Lantern"),
    ("Milo", "Tiny Titan"),
)


ASP_RULES = r"""
hero(luna).
partner(bramble).
case(smoke_alarm).
has_twist(smoke_alarm).
has_reconciliation(smoke_alarm).
truth(smoke_alarm).
valid_story(C) :- case(C), has_twist(C), has_reconciliation(C), truth(C).
"""


def asp_facts(params: StoryParams) -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("hero", params.hero_name.lower()),
            asp.fact("partner", params.partner_name.lower()),
            asp.fact("case", params.case),
            asp.fact("has_twist", params.case),
            asp.fact("has_reconciliation", params.case),
            asp.fact("truth", params.case),
        ]
    )


def asp_program(params: StoryParams, show: str = "#show valid_story/1.") -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    params = StoryParams()
    model = asp.one_model(asp_program(params))
    found = set(asp.atoms(model, "valid_story"))
    expected = {("smoke_alarm",)}
    if found == expected:
        print("OK: ASP and Python story gates agree.")
        return 0
    print("MISMATCH between ASP and Python story gates.")
    print("ASP:", sorted(found))
    print("Python:", sorted(expected))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    key = "|".join(
        str(x)
        for x in (
            params.seed,
            params.hero_name,
            params.partner_name,
            params.place,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.case not in CASES:
        raise StoryError(f"Unknown case: {params.case}")
    if not params.hero_name.strip() or not params.partner_name.strip():
        raise StoryError("Hero and partner names must not be empty.")
    hero_title = next((title for name, title in HEROES if name == params.hero_name), "Moonlight Hero")
    partner_title = next((title for name, title in PARTNERS if name == params.partner_name), "Brave Friend")
    return World(
        hero=Hero(params.hero_name, hero_title),
        partner=Hero(params.partner_name, partner_title),
        place=PLACES[params.place],
        case=CASES[params.case],
    )


def tell_story(world: World, params: StoryParams) -> None:
    hero, partner, place, case = world.hero, world.partner, world.place, world.case
    rng = story_rng(params)
    hero.memes.update(courage=0.0, trust=0.0)
    partner.memes.update(courage=0.0, trust=0.0)

    openings = {
        "signal_first": f"A bacon smell curled through {place.name}, and the emergency bell gave one worried chirp. {hero.name}, the {hero.title}, hurried toward the kitchen.",
        "dialogue_first": f'"Did you hear that bell?" {hero.name} asked at {place.name}. The bacon smell was strong, and {partner.name}, the {partner.title}, pointed toward the kitchen.',
        "alarm_first": f"The alarm chirped above {place.name}. {hero.name} spread her moon-bright cape and saw bacon near the kitchen drain.",
        "friend_first": f"{hero.name} and {partner.name} were sharing a quiet superhero breakfast when bacon smoke curled past their table. Then the alarm chirped.",
        "twist_first": f"Everyone thought a bacon fire had started at {place.name}. That was only the beginning of the mystery for {hero.name}, the {hero.title}.",
    }
    world.say(openings[params.route])
    world.say(f"The first guess was that {case.first_guess}, and the hungry crowd began to hurry toward the door.")
    world.say(rng.choice([
        f'"Stay behind me," {hero.name} said. "{case.safe_action.capitalize()}."',
        f'{partner.name} asked, "What should I do?" {hero.name} answered, "Keep everyone calm while I look for evidence."',
        f'"A superhero protects people before chasing a mystery," {hero.name} said. {partner.name} nodded and guided the diners away.',
    ]))

    world.para()
    world.say(f"{hero.name} checked the kitchen from the safe side of the doorway. {case.twist.capitalize()}.")
    world.say(rng.choice([
        f'That was the twist: {case.truth.capitalize()}.',
        f'"Wait," {partner.name} said. "The clues do not match a fire." {case.truth.capitalize()}.',
        f"The alarm sounded frightening, but the evidence told a smaller story: {case.truth}.",
    ]))
    world.say(f"Instead of blaming anyone, they agreed that {case.safe_action}.")

    world.para()
    world.say(f"{hero.name} and {partner.name} worked together. They {case.repair}.")
    world.say(rng.choice([
        f'"I am sorry I blamed you before checking," {hero.name} told {partner.name}.',
        f'{partner.name} took a slow breath. "I was scared too. Thank you for listening."',
        f'"We can fix the problem and fix our friendship," {hero.name} said.',
    ]))
    world.say(f"This was the reconciliation: {case.reconciliation}.")
    hero.memes["courage"] = 1.0
    hero.memes["trust"] = 1.0
    partner.memes["courage"] = 1.0
    partner.memes["trust"] = 1.0
    hero.meters["safe_actions"] = 2.0
    place.meters["danger_removed"] = 1.0

    world.para()
    world.say(f"The friends remembered that courage means checking facts, protecting others, and repairing hurt feelings.")
    world.say(f"At last, {case.ending}")
    world.facts.update(
        hero=hero,
        partner=partner,
        place=place,
        case=case,
        twist=case.twist,
        reconciliation=case.reconciliation,
        repair=case.repair,
        ending=case.ending,
        bacon="bacon",
        removed=True,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].name} investigating bacon trouble at {f['place'].name}.",
        f"Include this twist: {f['twist']}.",
        f"End with reconciliation: {f['reconciliation']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, place, case = f["hero"], f["partner"], f["place"], f["case"]
    return [
        QAItem(
            question=f"What problem did {hero.name} investigate at {place.name}?",
            answer=f"{hero.name} investigated the bacon smell and the chirping alarm because everyone feared that {case.first_guess}.",
        ),
        QAItem(
            question="What was the twist in the mystery?",
            answer=f"The twist was that {case.twist}. The real explanation was that {case.truth}.",
        ),
        QAItem(
            question=f"How did {hero.name} and {partner.name} solve the problem safely?",
            answer=f"They {case.repair}. They removed the danger instead of rushing into an unsafe rescue.",
        ),
        QAItem(
            question="How did the friends reconcile?",
            answer=f"They reconciled when {case.reconciliation}. They listened, apologized, and chose to trust each other.",
        ),
        QAItem(
            question="What did the ending show had changed?",
            answer=f"The ending showed that the danger was gone and the friends could enjoy a safe meal together: {case.ending}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bacon?",
            answer="Bacon is a food made from cured meat that is often cooked until crisp.",
        ),
        QAItem(
            question="Why should a person remove food from a hot surface with care?",
            answer="Careful tools and an adult's help can prevent burns when something is hot.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a person or character who uses special abilities, courage, and responsibility to help others.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means repairing a disagreement by listening, apologizing when needed, and making peace.",
        ),
        QAItem(
            question="Why should heroes check facts before blaming someone?",
            answer="Checking facts can reveal a surprising cause and keep an innocent friend from being blamed unfairly.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Superhero story about bacon, a twist, and reconciliation.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--hero-name")
    parser.add_argument("--partner-name")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--case", choices=sorted(CASES))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name, _ = rng.choice(HEROES)
    partner_name, _ = rng.choice(PARTNERS)
    return StoryParams(
        seed=args.seed,
        hero_name=args.hero_name or hero_name,
        partner_name=args.partner_name or partner_name,
        place=args.place or rng.choice(sorted(PLACES)),
        case=args.case or rng.choice(sorted(CASES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.hero, world.partner):
        lines.append(f"{entity.name}: meters={entity.meters} memes={entity.memes}")
    lines.append(
        f"{world.place.name}: meters={world.place.meters}; "
        f"bacon_removed={world.facts.get('removed')} "
        f"twist={world.facts.get('twist')!r}"
    )
    lines.append(f"reconciliation={world.facts.get('reconciliation')!r}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for i, prompt in enumerate(sample.prompts, 1):
            print(f"{i}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        params = StoryParams()
        print(asp_program(params))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        params = StoryParams()
        model = asp.one_model(asp_program(params))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 3 if args.all else args.n
    samples: list[StorySample] = []

    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
