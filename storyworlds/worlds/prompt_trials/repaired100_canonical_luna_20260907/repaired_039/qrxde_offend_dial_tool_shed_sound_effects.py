#!/usr/bin/env python3
"""A child-friendly pirate mystery about a strange dial in a tool shed."""

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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

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
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    helper: str = "Captain Bea"
    setting: str = "the tool shed"
    quest: str = "find the hidden bell"
    mystery: str = "why the old dial says qrxde"
    word_one: str = "qrxde"
    word_two: str = "offend"
    word_three: str = "dial"
    style: str = "Pirate Tale"


@dataclass(frozen=True)
class Case:
    key: str
    sound: str
    clue: str
    failed_try: str
    hero_job: str
    helper_job: str
    solution: str
    reveal: str
    lesson: str
    ending: str


@dataclass
class World:
    params: StoryParams
    people: dict[str, Person] = field(default_factory=dict)
    items: dict[str, ObjectItem] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Milo", "Pip", "Nora", "Tess", "Kai"]
HELPERS = ["Captain Bea", "First Mate Jo", "Aunt Mara", "Old Tom"]
QUESTS = [
    "find the hidden bell",
    "recover the brass compass",
    "unlock the captain's chest",
    "follow the map to the garden gate",
]
SOUNDS = [
    ("clink-clank", "two loose tools struck the same metal hook"),
    ("creak-creak", "the shed door moved in the sea breeze"),
    ("plink-plonk", "a tiny coin bounced inside the wooden box"),
    ("thump-scrape", "something slid behind the barrel"),
    ("jingle-jangle", "a ring of keys swung beneath the bench"),
]
CASES = [
    Case(
        "hook",
        "clink-clank",
        "the sound came whenever the red wrench brushed a brass hook",
        "pulling every tool from the wall made the noise louder",
        "held the wrench still",
        "marked the hook with a strip of blue cloth",
        "They turned the dial slowly while touching one tool at a time.",
        "The letters were not a pirate insult; qrxde was a scrambled clue for the bell.",
        "a puzzling message deserves patient listening before angry guessing",
        "the hidden bell rang beside the blue-marked hook",
    ),
    Case(
        "barrel",
        "thump-scrape",
        "the noise stopped when the empty barrel faced the north wall",
        "rolling the barrel around the shed sent dust into the air",
        "blocked the barrel with a wooden wedge",
        "checked the floorboards behind it",
        "They lined up the dial's arrow with the floorboard that sounded hollow.",
        "Under the board lay a brass compass and a note pointing toward the bell.",
        "a clear question can turn a jumble into a useful direction",
        "the compass needle glittered beside the quiet barrel",
    ),
    Case(
        "keys",
        "jingle-jangle",
        "the key ring chimed only when the dial pointed at the moon mark",
        "spinning the dial quickly mixed every sound together",
        "counted each click aloud",
        "held the lantern near the moon mark",
        "They listened for three clicks, then stopped exactly when the key ring chimed.",
        "The dial opened a narrow drawer containing the quest map.",
        "careful turns help a team hear what hurried hands miss",
        "the map unfurled beneath the moon-shaped shadow",
    ),
    Case(
        "coin",
        "plink-plonk",
        "a coin rolled whenever the dial's pointer faced the cracked shelf",
        "shaking the box hid the coin under a rag",
        "kept the box level",
        "lifted the rag with a paintbrush",
        "They followed the coin's path and found a small message under the shelf.",
        "The message explained that qrxde was a sailor's code, not a rude word.",
        "unknown words should be investigated instead of used to offend",
        "the coded note shone like treasure in Luna's palm",
    ),
]


def make_world(params: StoryParams) -> World:
    if params.setting != "the tool shed":
        raise StoryError("This quest belongs in the tool shed.")
    if not all(params.word_one and params.word_two and params.word_three):
        raise StoryError("The three mystery words must not be empty.")
    world = World(params=params)
    hero = Person(params.hero, "young pirate")
    helper = Person(params.helper, "captain")
    dial = ObjectItem("dial", "an old brass dial", owner=params.helper)
    world.people = {hero.name: hero, helper.name: helper}
    world.items = {dial.name: dial}
    world.facts.update(hero=hero, helper=helper, dial=dial, setting=params.setting)
    return world


def generate_story_world(params: StoryParams) -> World:
    world = make_world(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    case = rng.choice(CASES)
    p = params

    world.say(
        f"Luna was a young pirate with a brave heart and a careful ear. "
        f"One bright morning, she entered {p.setting} with {p.helper}."
    )
    world.say(
        f"Their quest was to {p.quest}, but an old brass {p.word_three} stood in their way. "
        f"Beside it, a dusty label read “{p.word_one}.”"
    )
    world.say(
        f"“That word may look strange,” said {p.helper}, “but we must not let a mystery offend us before we understand it.”"
    )
    world.para()

    world.say(f"Then came a sharp sound: {case.sound}! {case.clue}.")
    world.say(
        f"“Arrr, the shed is hiding something,” Luna said. “I will solve the mystery without making a mess.”"
    )
    world.say(f"At first, {case.failed_try}.")
    world.say(
        f"“Stop,” said {p.helper}. “Tell me what you heard, and we will test one clue at a time.”"
    )
    world.say(f"Luna replied, “I heard {case.sound}, and I think the {p.word_three} is pointing us somewhere.”")
    world.para()

    world.say(f"Luna {case.hero_job}, while {p.helper} {case.helper_job}.")
    world.say(case.solution)
    world.say(
        f"The dial clicked three times. A small card appeared with the word “{p.word_two}.” "
        f"Luna read it aloud, then waited before deciding what it meant."
    )
    world.say(case.reveal)
    world.para()

    world.say(f"Together they completed their quest to {p.quest}.")
    world.say(
        f"{p.helper} smiled. “A pirate solves a mystery with courage, questions, and kind words.”"
    )
    world.say(f"Luna nodded. “And with ears ready for {case.sound}!”")
    world.say(f"{case.ending}.")
    world.say(f"The tool shed grew quiet, but its little sounds now felt like clues instead of scares.")

    world.people[p.hero].meters.update(attention=1.0, confidence=1.0)
    world.people[p.hero].memes.update(curiosity=1.0, kindness=1.0)
    world.people[p.helper].meters.update(guidance=1.0, patience=1.0)
    world.people[p.helper].memes.update(trust=1.0, kindness=1.0)
    world.items["dial"].meters.update(aligned=1.0, safe=1.0)
    world.items["dial"].memes.update(mystery_solved=1.0)
    world.facts.update(
        case=case.key,
        sound=case.sound,
        clue=case.clue,
        failed_try=case.failed_try,
        hero_job=case.hero_job,
        helper_job=case.helper_job,
        solution=case.solution,
        reveal=case.reveal,
        lesson=case.lesson,
        ending=case.ending,
        resolved=True,
        quest=p.quest,
        mystery=p.mystery,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.params
    return [
        f"Write a pirate tale about {p.hero} solving a mystery in {p.setting}.",
        f"Use the words {p.word_one}, {p.word_two}, and {p.word_three} in a child-friendly quest story.",
        f"Include sound effects while {p.hero} and {p.helper} investigate an old dial.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p, f = world.params, world.facts
    return [
        QAItem(
            question=f"Where did {p.hero} and {p.helper} investigate?",
            answer=f"They investigated {p.setting}, where an old brass {p.word_three} and a strange label made the quest mysterious.",
        ),
        QAItem(
            question=f"What sound helped {p.hero} solve the mystery?",
            answer=f"The important sound was {f['sound']}. They connected it to this clue: {f['clue']}.",
        ),
        QAItem(
            question="Why did the pirates avoid making a quick angry guess?",
            answer=f"They avoided a quick guess because the word {p.word_one} looked strange but might be a code. They did not want to let confusion offend them or make them accuse the wrong thing.",
        ),
        QAItem(
            question="How did the two pirates work together?",
            answer=f"{p.hero} {f['hero_job']}, while {p.helper} {f['helper_job']}. Their separate jobs helped them use the dial carefully.",
        ),
        QAItem(
            question="What proved that the quest was complete?",
            answer=f"They completed the quest to {f['quest']}. In the final scene, {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dial?",
            answer="A dial is a round control or face that can turn or point to marks. People use dials to choose, measure, or follow a setting.",
        ),
        QAItem(
            question="Why can sound effects help solve a mystery?",
            answer="A repeated sound can show where something moves or which object is involved. Listening carefully gives investigators evidence instead of a wild guess.",
        ),
        QAItem(
            question="What does it mean to offend someone?",
            answer="To offend someone means to hurt their feelings or show disrespect. Asking questions kindly can prevent a misunderstanding from becoming hurtful.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
place(P) :- setting(P).
mystery(M) :- mystery_text(M).
quest(Q) :- quest_text(Q).
solved(H,K,P,Q,M) :- hero(H), helper(K), place(P), quest(Q), mystery(M), kind_investigation(H,K).
pirate_tale(H,K,P,Q,M) :- solved(H,K,P,Q,M).
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
            asp.fact("quest_text", p.quest),
            asp.fact("mystery_text", p.mystery),
            asp.fact("kind_investigation", p.hero, p.helper),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show pirate_tale/5."))
    atoms = asp.atoms(symbols, "pirate_tale")
    if not atoms:
        print("MISMATCH: ASP did not produce a pirate tale.")
        return 1
    sample = generate(DEFAULT_PARAMS)
    if not sample.world or not sample.world.facts.get("resolved"):
        print("MISMATCH: Python story did not resolve.")
        return 1
    print("OK: ASP and Python both produce a resolved pirate mystery.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--quest", choices=QUESTS)
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
        hero=args.hero or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        quest=args.quest or rng.choice(QUESTS),
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
            "\n--- trace ---\n"
            f"hero={sample.world.params.hero}\n"
            f"helper={sample.world.params.helper}\n"
            f"case={sample.world.facts['case']}\n"
            f"sound={sample.world.facts['sound']}\n"
            f"resolved={sample.world.facts['resolved']}"
        )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show pirate_tale/5."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        atoms = asp.atoms(
            asp.one_model(asp_program("#show pirate_tale/5.")),
            "pirate_tale",
        )
        print("1 compatible pirate mystery pattern." if atoms else "No compatible pattern.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, case in enumerate(CASES):
            params = StoryParams(
                seed=base_seed + i,
                hero=args.hero or "Luna",
                helper=args.helper or "Captain Bea",
                quest=args.quest or "find the hidden bell",
            )
            samples.append(generate(params))
    else:
        for i in range(args.n):
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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
