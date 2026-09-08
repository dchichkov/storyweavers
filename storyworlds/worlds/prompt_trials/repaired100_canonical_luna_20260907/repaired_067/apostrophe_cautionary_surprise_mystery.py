#!/usr/bin/env python3
"""
A small mystery storyworld about an apostrophe, a caution, and a surprise.

A misplaced apostrophe makes a harmless sign seem alarming. A careful child
checks the evidence, asks a helper, and discovers a warm surprise.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        sys.path.insert(0, str(_parent / "storyworlds"))
        break
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
careful(X) :- child(X), checks_clue(X), asks_helper(X).
mystery(X) :- child(X), finds_apostrophe(X), sees_surprise(X).
cautionary(X) :- child(X), avoids_risk(X), shares_evidence(X).
solved(X) :- careful(X), mystery(X), cautionary(X).
"""

NAMES = ["Luna", "Milo", "Nia", "Theo", "Iris", "Pip"]
HELPERS = ["Grandma June", "Mr. Vale", "Aunt Rosa", "the librarian"]
PLACES = ["the old garden gate", "the quiet museum", "the village bakery", "the moonlit library"]
OBJECTS = ["a brass key", "a blue envelope", "a tin whistle", "a silver button"]
TREATS = ["warm cinnamon rolls", "lemon biscuits", "apple tarts", "honey cakes"]


@dataclass(frozen=True)
class Case:
    title: str
    premise: str
    clue: str
    risky_guess: str
    warning: str
    question: str
    action: str
    discovery: str
    surprise: str
    lesson: str
    ending: str


CASES = [
    Case(
        "the missing apostrophe",
        "A hand-painted sign on the garden gate said, “The cats missing.”",
        "one tiny white space after the word cats and a curled mark of fresh blue paint",
        "assume that a cat had vanished and climb through the locked gate",
        "the gate's old latch was loose above a bed of thorny roses",
        "Who had gone missing, and why was the sign written so strangely?",
        "copied the sign carefully, compared it with the caretaker's letter, and called for help before touching the latch",
        "the apostrophe belonged in “cat's,” because one particular cat owned the sign's missing paintbrush",
        "inside the shed, the caretaker had prepared",
        "An apostrophe can change a sentence, but careful questions can change a worry into a clue.",
        "The cat blinked from a basket beside the finished sign while the blue apostrophe shone like a tiny moon.",
    ),
    Case(
        "the baker's warning",
        "A paper on the bakery door announced, “The baker’s gone.”",
        "the apostrophe leaned toward the word baker and floury paw prints crossed the bottom edge",
        "believe the baker had disappeared and rush into the hot kitchen",
        "a tray of fresh buns sat near the open oven",
        "Was the baker gone, or did the sentence mean something else?",
        "read the note aloud, asked the baker's neighbor, and stayed outside the hot kitchen",
        "the baker's cat had carried off the note while the baker was in the back room",
        "the baker had placed",
        "A strange message deserves a calm check before a dangerous dash.",
        "The cat curled beside a basket of rolls, wearing a floury ribbon like a badge.",
    ),
    Case(
        "the museum's secret",
        "A label beneath an empty case read, “The queen’s missing.”",
        "a bright thread snagged on the case hinge and a second label lay face down nearby",
        "reach through the open side panel to rescue a priceless crown",
        "the panel had a sharp metal edge and the alarm light was blinking",
        "Was the queen missing, or was one of her belongings missing?",
        "showed the clue to the guide, kept hands away from the case, and turned over the second label",
        "the queen's crown was safe; the missing object was a small toy horse from the children's display",
        "the guide had set out",
        "Good detectives use evidence and helpers instead of grabbing at the first exciting answer.",
        "The toy horse stood on a new velvet square while the crown gleamed safely behind glass.",
    ),
    Case(
        "the library's whisper",
        "A note on a reading-room chair said, “The librarian’s waiting.”",
        "the apostrophe was written in purple ink, matching a bookmark tucked beneath the cushion",
        "sneak into the closed archive alone",
        "the archive door was heavy and its warning bell still worked",
        "Was the librarian waiting for a person or for a book?",
        "showed the note to the librarian and followed the bookmark's page clue",
        "the librarian was waiting for a lost storybook, not a runaway visitor",
        "the librarian had placed",
        "Mysteries become safer when clues are shared with someone who knows the place.",
        "The missing storybook rested on a reading pillow, open to a page about a moonlit fox.",
    ),
    Case(
        "the gardener's footprints",
        "A chalkboard beside the greenhouse said, “The gardener’s muddy.”",
        "two sets of damp footprints ended beneath the board and the apostrophe had been rubbed",
        "decide the gardener had fallen and squeeze through the narrow greenhouse window",
        "the glass roof was wet and the window frame wobbled",
        "Did the sentence describe the gardener or something belonging to the gardener?",
        "photographed the footprints, asked the groundskeeper, and waited by the safe door",
        "the gardener's old boots were muddy because a small rabbit had hidden inside them",
        "the groundskeeper had found",
        "A cautionary clue may look dramatic, but patience keeps a mystery from becoming an accident.",
        "The rabbit hopped free while the muddy boots stood neatly beside a row of shining pots.",
    ),
    Case(
        "the captain's surprise",
        "A harbor notice said, “The captain’s lost.”",
        "a salt-stained apostrophe and a ribbon from the harbor festival clung to the notice board",
        "run onto the pier to search the dark water",
        "the tide was rising around slippery boards",
        "Was the captain lost, or had the captain lost something?",
        "read the notice with the harbor keeper and searched the dry office first",
        "the captain's lucky compass was lost, while the captain waited safely by the lantern",
        "the harbor keeper had found",
        "A careful reader can prevent a frightening mistake before it becomes a real danger.",
        "The captain hugged the recovered compass as festival lanterns blinked across the calm harbor.",
    ),
]


@dataclass
class Character:
    id: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    name: str
    helper: str
    place: str
    object: str
    treat: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    hero: Character
    helper: Character
    object: str
    treat: str
    case: Case
    route: int = 0
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A cautionary apostrophe mystery storyworld.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--object", choices=OBJECTS)
    parser.add_argument("--treat", choices=TREATS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("child", "hero"),
            asp.fact("checks_clue", "hero"),
            asp.fact("asks_helper", "hero"),
            asp.fact("finds_apostrophe", "hero"),
            asp.fact("sees_surprise", "hero"),
            asp.fact("avoids_risk", "hero"),
            asp.fact("shares_evidence", "hero"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show solved/1."))
    found = set(asp.atoms(model, "solved"))
    expected = {("hero",)}
    if found == expected:
        print("OK: ASP parity verified.")
        return 0
    print(f"MISMATCH: found {found}, expected {expected}")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        object=args.object or rng.choice(OBJECTS),
        treat=args.treat or rng.choice(TREATS),
    )


def make_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if params.name == params.helper:
        raise StoryError("the child and helper must be different characters")
    key = params.seed if params.seed is not None else sum(ord(c) for c in "|".join(vars(params).values() if False else [
        params.name, params.helper, params.place, params.object, params.treat
    ]))
    hero = Character(
        id=params.name,
        role="careful young detective",
        meters={"attention": 0.9, "risk": 0.2},
        memes={"curiosity": 0.8, "trust": 0.7},
    )
    helper = Character(
        id=params.helper,
        role="trusted helper",
        meters={"knowledge": 0.9, "patience": 0.9},
        memes={"kindness": 0.8},
    )
    return World(
        setting=Setting(place=params.place),
        hero=hero,
        helper=helper,
        object=params.object,
        treat=params.treat,
        case=CASES[key % len(CASES)],
        route=(key // len(CASES)) % 4,
    )


def tell(world: World) -> None:
    h = world.hero
    helper = world.helper
    case = world.case
    openings = [
        f"At {world.setting.place}, {h.id} found a mystery waiting beside an ordinary sign.",
        f"The quietest clue of the day appeared at {world.setting.place}.",
        f"{h.id} had come to {world.setting.place} for {world.treat}, but noticed something stranger first.",
        f"A small curled apostrophe turned an ordinary afternoon at {world.setting.place} into a mystery.",
    ]
    world.say(f"{openings[world.route]} {case.premise}")
    world.say(
        f"{h.id} looked closely and found {case.clue}. The words sounded alarming, but the evidence did not yet explain what had happened."
    )
    world.para()
    world.say(
        f"For a moment, {h.id} wanted to {case.risky_guess}. "
        f'"Wait," said {helper.id}. "What does the apostrophe tell us?"'
    )
    world.say(
        f"{h.id} pointed to the danger. "{case.warning.capitalize()}." "
        f'"Then let us ask a safer question," said {helper.id}. "{case.question}"'
    )
    world.para()
    world.say(
        f"Together, {h.id} and {helper.id} {case.action}. "
        f"They kept the {world.object} nearby as a useful comparison clue."
    )
    world.say(
        f"The answer was a surprise: {case.discovery}. "
        f"After that, {case.surprise} {world.treat} for everyone who had helped."
    )
    world.para()
    world.say(
        f'"So the apostrophe was not a warning by itself," said {h.id}. '
        f'"It was a clue about who had what."'
    )
    world.say(
        f"{helper.id} smiled. {case.lesson} "
        f"{case.ending}"
    )
    world.facts.update(
        hero=h,
        helper=helper,
        setting=world.setting,
        case=case,
        clue=case.clue,
        warning=case.warning,
        question=case.question,
        action=case.action,
        discovery=case.discovery,
        surprise=case.surprise,
        ending=case.ending,
    )


def generation_prompts(world: World) -> list[str]:
    case = world.case
    return [
        f"Write a child-friendly mystery at {world.setting.place} about an apostrophe that changes the meaning of a puzzling sign.",
        f"Tell a cautionary surprise story in which {world.hero.id} notices {case.clue}, asks {world.helper.id} for help, and avoids {case.warning}.",
        f"Write an ending where the mystery is solved by evidence, careful reading, and the surprise that {case.discovery}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.case
    h = world.hero
    helper = world.helper
    return [
        QAItem(
            question=f"What clue did {h.id} notice at {world.setting.place}?",
            answer=f"{h.id} noticed {case.clue}. The clue made the apostrophe important without proving the first frightening guess.",
        ),
        QAItem(
            question=f"Why did {h.id} avoid the risky first idea?",
            answer=f"{h.id} avoided it because {case.warning}. Instead of rushing, {h.id} shared the evidence with {helper.id}.",
        ),
        QAItem(
            question="How did the apostrophe help solve the mystery?",
            answer=f"The apostrophe showed that the words could describe ownership or possession, so {h.id} and {helper.id} asked a more careful question: {case.question}",
        ),
        QAItem(
            question=f"What did {h.id} and {helper.id} do to solve the case?",
            answer=f"Together, they {case.action}. Their careful method led to the discovery that {case.discovery}.",
        ),
        QAItem(
            question="What was the surprise at the end?",
            answer=f"The surprise was that {case.discovery}. Then {case.surprise} {world.treat} for the helpers.",
        ),
        QAItem(
            question="What proved that the danger had passed?",
            answer=f"The ending showed that the mystery was safe and solved: {case.ending}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an apostrophe?",
            answer="An apostrophe is a small mark used in contractions and to show possession, as in “the cat's basket.”",
        ),
        QAItem(
            question="Why should a person check a mysterious sign carefully?",
            answer="A person should check it carefully because punctuation and missing words can change the meaning, while rushing may lead to an unsafe choice.",
        ),
        QAItem(
            question="Why is it helpful to ask a trusted helper?",
            answer="A trusted helper may know the place, notice another clue, and help someone choose a safe action instead of guessing alone.",
        ),
    ]


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"hero={world.hero.id} role={world.hero.role}",
            f"hero_meters={world.hero.meters}",
            f"hero_memes={world.hero.memes}",
            f"helper={world.helper.id} role={world.helper.role}",
            f"helper_meters={world.helper.meters}",
            f"helper_memes={world.helper.memes}",
            f"place={world.setting.place}",
            f"object={world.object}",
            f"treat={world.treat}",
            f"case={world.case.title}",
            f"clue={world.case.clue}",
            f"action={world.case.action}",
            f"discovery={world.case.discovery}",
        ]
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell(world)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams("Luna", "Grandma June", PLACES[0], OBJECTS[0], TREATS[0]),
        StoryParams("Milo", "Mr. Vale", PLACES[1], OBJECTS[1], TREATS[1]),
        StoryParams("Nia", "Aunt Rosa", PLACES[2], OBJECTS[2], TREATS[2]),
        StoryParams("Theo", "the librarian", PLACES[3], OBJECTS[3], TREATS[3]),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(
            asp_program(
                "#show careful/1.\n#show mystery/1.\n#show cautionary/1.\n#show solved/1."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
