#!/usr/bin/env python3
"""A child-friendly driveway whodunit about rubble, a crate, and a happy ending."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    name: str
    label: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Grandma"
    setting: str = "the driveway"
    crate: str = "the blue crate"
    treasure: str = "a little garden sign"


@dataclass(frozen=True)
class Case:
    key: str
    opening: str
    trouble: str
    clue: str
    false_lead: str
    discovery: str
    solution: str
    ending: str
    lesson: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


HEROES = ["Luna", "Milo", "Nora", "Theo", "Pia", "Sam"]
HELPERS = ["Grandma", "Grandpa", "Dad", "Mom", "Aunt May"]
CRATES = ["the blue crate", "the red crate", "the green crate", "the wooden crate"]
TREASURES = ["a little garden sign", "a painted birdhouse", "a basket of seed packets", "a bright welcome flag"]

CASES = [
    Case(
        "pawprints",
        "Luna was sweeping the driveway before the neighborhood garden party.",
        "When she returned with a fresh broom, a pile of rubble sat beside the blue crate, and the garden sign was gone.",
        "Tiny pawprints crossed the dust and stopped beneath the crate.",
        "At first, Luna suspected the delivery cart because one wheel had left a round mark.",
        "Grandma lifted the crate just enough for Luna to see a corner of painted wood.",
        "They moved the rubble one small stone at a time, slid out the sign, and discovered that a curious puppy had nudged the crate over it.",
        "The puppy wagged its tail, the sign stood safely by the gate, and the garden party began with everyone laughing.",
        "Good detectives follow a clue gently instead of blaming the first thing that looks unusual.",
    ),
    Case(
        "chalk",
        "Luna drew arrows in chalk on the driveway to mark where the garden sign should go.",
        "A gust scattered the arrows, tipped the crate, and buried the sign under loose rubble.",
        "One bright chalk line remained on the crate's lower edge.",
        "Luna wondered whether a passerby had carried the sign away.",
        "The chalk line showed that the crate had slid across the sign when the wind pushed its open lid.",
        "Luna and Grandma cleared a safe path, rolled the crate aside, and found the sign underneath.",
        "They redrew the arrows, placed a stone on each corner, and watched the happy party decorations flutter without falling.",
        "A small leftover mark can explain a big-looking mystery.",
    ),
    Case(
        "wheel",
        "Luna and Grandma were preparing the driveway for a family treasure hunt.",
        "The clue box was missing, and a trail of rubble led away from the crate.",
        "The rubble was fresh only beside one crate wheel, while the rest of the driveway was clean.",
        "Luna first guessed that a squirrel had dragged the box toward the hedge.",
        "Grandma noticed a bent wheel pin and a shallow track under the crate.",
        "They repaired the pin with a wooden peg, lifted the crate together, and found the clue box tucked behind its back corner.",
        "The treasure hunt continued, and the final clue led Luna to a basket of treats waiting beneath the shade tree.",
        "Understanding how an object moved is often better than guessing who touched it.",
    ),
    Case(
        "blue_ribbon",
        "Luna tied a blue ribbon to the crate so guests would know where to leave garden tools.",
        "The ribbon vanished, and rubble covered the place where the welcome flag had been.",
        "A tiny blue thread clung to a rough stone near the crate.",
        "Luna suspected the wind had carried the ribbon over the fence.",
        "The thread showed that the ribbon had snagged when the crate scraped across the rubble.",
        "They brushed the stones aside, found the ribbon looped around the flagpole, and lifted the flag free.",
        "The flag waved over the clean driveway, and Luna gave the mystery a cheerful bow.",
        "Clues can connect two ordinary events into one clear answer.",
    ),
    Case(
        "rain",
        "After a short rain, Luna went outside to place seed packets beside the driveway crate.",
        "The crate was full of damp rubble, and the seed basket was nowhere in sight.",
        "A dry rectangle beneath the crate was the exact shape of the missing basket.",
        "Luna thought the rain might have washed the basket toward the drain.",
        "Grandma saw that the crate had been pushed over the basket to keep it dry.",
        "They emptied the rubble into a bucket, pulled out the basket, and set the seeds on a sunny bench.",
        "The seeds stayed safe, and Luna planted the first row while the clouds opened to a patch of blue.",
        "A strange arrangement may have been a helpful choice, not a naughty one.",
    ),
]

DETAILS = [
    "They wore gloves and checked each stone before moving it.",
    "They marked the safe edge with chalk before touching the crate.",
    "They counted together so the crate would move evenly.",
    "They paused whenever dust rose and waited for the air to clear.",
    "They kept the driveway open for bicycles and neighbors.",
]


def make_world(params: StoryParams) -> World:
    if params.hero == params.helper:
        raise StoryError("hero and helper must be different people")
    world = World(params=params)
    hero = Person(params.hero, "young detective")
    helper = Person(params.helper, "trusted helper")
    crate = ObjectItem("crate", params.crate, owner=params.hero)
    rubble = ObjectItem("rubble", "a pile of loose rubble", meters={"weight": 1.0})
    world.people = {hero.name: hero, helper.name: helper}
    world.items = {"crate": crate, "rubble": rubble}
    world.facts.update(hero=hero.name, helper=helper.name, setting=params.setting)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(CASES)

    world.say(case.opening)
    world.say(f"{params.hero} had placed {params.crate} at the edge of {params.setting}, ready for {params.treasure}.")
    world.para()
    world.say(case.trouble)
    world.say(f'"A mystery!" said {params.hero}. "{params.helper}, will you help me investigate?"')
    world.say(f'"Of course," said {params.helper}. "Let us study the clues before we move anything."')
    world.say(f"They examined the scene and found this clue: {case.clue}")
    world.say(f"{params.hero} considered a false lead: {case.false_lead}")
    world.para()
    world.say(f'"That guess does not explain the whole trail," said {params.helper}.')
    world.say(f"{case.discovery} {rng.choice(DETAILS)}")
    world.say(f'"Now we know what happened," said {params.hero}. "The clue points to the crate, not a thief."')
    world.say(f'"And knowing the cause gives us a safe plan," said {params.helper}.')
    world.say(case.solution)
    world.para()
    world.say(case.ending)
    world.say(f"The solved mystery left {params.hero} feeling proud, and {params.helper} smiled at the careful detective.")
    world.say(f"The lesson of the case was clear: {case.lesson}")

    world.people[params.hero].memes.update(curiosity=1.0, confidence=1.0, blame=0.0)
    world.people[params.helper].memes.update(patience=1.0, trust=1.0)
    world.items["crate"].meters.update(stable=1.0, inspected=1.0)
    world.items["rubble"].meters["cleared"] = 1.0
    world.facts.update(
        case=case.key,
        trouble=case.trouble,
        clue=case.clue,
        false_lead=case.false_lead,
        discovery=case.discovery,
        solution=case.solution,
        ending=case.ending,
        lesson=case.lesson,
        resolved=True,
        happy_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a child-friendly whodunit about {p.hero} investigating rubble and a crate in {p.setting}.",
        f"Tell a mystery in which {p.hero} and {p.helper} use a physical clue to solve a missing-object problem.",
        f"Create a happy ending where a careful investigation makes the driveway safe and joyful.",
    ]


def lower_first(text: object) -> str:
    value = str(text)
    return value[:1].lower() + value[1:]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            question=f"What mystery did {p.hero} investigate?",
            answer=f"{p.hero} investigated why {p.treasure} was missing while rubble had appeared beside {p.crate} in {p.setting}.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The important clue was that {lower_first(f['clue'])} It connected the rubble or crate with the missing item instead of pointing to a random suspect.",
        ),
        QAItem(
            question=f"What did {p.hero} and {p.helper} do to investigate safely?",
            answer=f"They studied the scene first, marked a safe area, and moved {p.crate} and the rubble carefully together rather than rushing.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"{lower_first(f['ending'])} The driveway became useful again, and the missing item was safe.",
        ),
        QAItem(
            question="What did the detectives learn?",
            answer=f"They learned that {lower_first(f['lesson'])}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a detail that helps explain what happened. Good investigators compare clues with the whole scene before deciding.",
        ),
        QAItem(
            question="Why should people move rubble carefully?",
            answer="Rubble can be heavy, sharp, or unstable. People should clear a safe path, use suitable protection, and ask for help with large objects.",
        ),
        QAItem(
            question="Why is it unwise to blame someone too quickly?",
            answer="An unusual mark may have a simple physical cause. Waiting for evidence prevents unfair blame and leads to a more accurate solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
driveway(S) :- setting(S).
crate(C) :- crate_name(C).
rubble(R) :- rubble_name(R).
case_solved(H,K,S,C,R) :- hero(H), helper(K), driveway(S), crate(C), rubble(R), safe_clue, shared_investigation(H,K), happy_ending.
whodunit(H,K,S) :- case_solved(H,K,S,_,_).
"""

DEFAULT_PARAMS = StoryParams()


def asp_facts() -> str:
    import asp
    p = DEFAULT_PARAMS
    return "\n".join(
        [
            asp.fact("hero_name", p.hero),
            asp.fact("helper_name", p.helper),
            asp.fact("setting", p.setting),
            asp.fact("crate_name", p.crate),
            asp.fact("rubble_name", "rubble"),
            asp.fact("safe_clue"),
            asp.fact("shared_investigation", p.hero, p.helper),
            asp.fact("happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show whodunit/3.")
    atoms = asp.atoms(asp.one_model(program), "whodunit")
    if not atoms:
        print("MISMATCH: ASP whodunit atom missing.")
        return 1
    sample = generate(StoryParams(seed=17))
    checks = [
        "rubble" in sample.story,
        "crate" in sample.story,
        "driveway" in sample.story,
        sample.world is not None and sample.world.facts.get("happy_ending") is True,
        "mystery" in sample.story.lower(),
    ]
    if not all(checks):
        print("MISMATCH: generated story failed domain checks.")
        return 1
    print("OK: ASP and Python agree on a solved driveway whodunit with a happy ending.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--setting", choices=["the driveway"])
    parser.add_argument("--crate", choices=CRATES)
    parser.add_argument("--treasure", choices=TREASURES)
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        helper=args.helper or rng.choice(HELPERS),
        setting=args.setting or "the driveway",
        crate=args.crate or rng.choice(CRATES),
        treasure=args.treasure or rng.choice(TREASURES),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story_world(params)
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
    if trace and sample.world:
        print(
            "\n--- trace ---"
            f"\ncase={sample.world.facts['case']}"
            f"\nclue={sample.world.facts['clue']}"
            f"\nresolved={sample.world.facts['resolved']}"
            f"\nhappy_ending={sample.world.facts['happy_ending']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show whodunit/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        atoms = asp.atoms(asp.one_model(asp_program("#show whodunit/3.")), "whodunit")
        print("1 compatible driveway whodunit with rubble, a crate, and a happy ending." if atoms else "0 compatible stories.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    count = len(CASES) if args.all else args.n
    for i in range(count):
        seed = base_seed + i
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
