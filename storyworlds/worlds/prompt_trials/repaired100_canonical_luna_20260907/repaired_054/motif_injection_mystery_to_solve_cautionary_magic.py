#!/usr/bin/env python3
"""A child-facing detective StoryWorld about a magical motif injection mystery."""

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
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str = "the moonlit museum"
    detective_name: str = "Luna"
    helper_name: str = "Pip"
    object_name: str = "the silver compass"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    key: str
    opening: str
    mystery: str
    false_lead: str
    clue: str
    warning: str
    method: str
    detective_job: str
    helper_job: str
    reveal: str
    lesson: str
    ending: str


SETTINGS = {
    "the moonlit museum": True,
    "the whispering library": True,
    "the lantern garden": True,
    "the old clock tower": True,
}
NAMES = ["Luna", "Milo", "Pip", "Nia", "Theo", "Zara", "Owen", "Bea"]
OBJECTS = [
    ("the silver compass", "compass"),
    ("the blue key", "key"),
    ("the glass marble", "marble"),
    ("the brass bell", "bell"),
]

CASES = [
    Case(
        "vanishing-stars",
        "A row of painted stars vanished from the museum map.",
        "Every star disappeared except a tiny mark shaped like a crescent moon.",
        "A black cat had walked across the dusty floor, so it looked guilty.",
        "The missing stars were found as pale specks on the cat's whiskers, but the specks pointed toward the map room.",
        "Magic becomes risky when a copied sign is trusted without checking what it means.",
        "follow the crescent motif, test the map with the object, and speak the truth aloud",
        "compared the marks and noticed which way each crescent faced",
        "held the object near the map and watched for a safe glow",
        "The crescent was an injection of magic into the map, meant to make the stars lead visitors to a locked room.",
        "a warning sign should be investigated carefully before anyone follows it",
        "the stars returned to the map, while one honest crescent shone beside the museum door",
    ),
    Case(
        "sleeping-bells",
        "The clock tower's bells stopped ringing at noon.",
        "A golden spiral appeared on every silent bell.",
        "The tallest bell had a crack, and everyone guessed it had caused the silence.",
        "The crack held no dust, but the spiral was warm whenever someone told a small lie.",
        "A magical mark can grow stronger when people repeat a guess instead of checking facts.",
        "ask honest questions, trace the spiral, and place the object beneath the smallest bell",
        "listed what had truly been seen rather than what had been guessed",
        "listened for the quiet bell that answered with a single clear tick",
        "The spiral was an injection of sleeping magic placed by a lonely wind sprite.",
        "careful truth-telling can wake a mystery without hurting its maker",
        "the bells rang softly again, and the spiral faded into a harmless golden thread",
    ),
    Case(
        "frozen-lantern",
        "One lantern in the garden froze with its flame turned blue.",
        "A pattern of three drops was painted around its glass.",
        "A gardener's blue glove lay nearby, making the gardener seem suspicious.",
        "The glove was dry, while the three drops were made of melted moonlight.",
        "Magic should not be touched just because it looks beautiful.",
        "keep a safe distance, compare the pattern, and use the object to reflect moonlight",
        "measured the space around the lantern and drew the pattern in the air",
        "stood behind the stone bench and angled the object toward the flame",
        "The drops were an injection of chilly magic from a rain cloud that had lost its way.",
        "caution protects curious helpers while they solve a magical problem",
        "the blue flame warmed to gold, and the three drops became bright dew",
    ),
    Case(
        "library-whispers",
        "The library's storybooks began whispering the same sentence.",
        "Each whisper repeated a red triangle hidden in the margins.",
        "A red scarf on a chair made the visitors suspect that someone had marked the books.",
        "The triangles appeared only beside pages about doors, never beside pages about people.",
        "A repeated motif may be a clue, but it is not permission to open every door.",
        "read the matching pages, count the triangles, and ask the object to reveal the safe book",
        "sorted the books by their quiet clues and kept the red scarf untouched",
        "held the object above the safest page and waited for a gentle chime",
        "The triangle was an injection of wandering magic that had entered one unfinished tale.",
        "curiosity needs a boundary when a mystery might lead somewhere unsafe",
        "the books whispered new endings, and the red triangle became a tiny bookmark",
    ),
    Case(
        "mirror-moth",
        "A silver moth appeared in every mirror but nowhere in the room.",
        "Each reflection showed the moth carrying a different tiny key.",
        "A shiny button on the floor seemed to be the missing key.",
        "The button reflected no light, while every false key fluttered when the object came near.",
        "A magical reflection can imitate an answer without being the answer.",
        "cover the mirrors, inspect the real floor, and use the object only on the shared clue",
        "placed cloth over the mirrors and marked the keys that vanished",
        "searched beneath the rug for a key that made no reflection",
        "The moth was an injection of mirror magic caused by a careless wish.",
        "a copied image should be checked against the real world",
        "the moth flew out of the last mirror and left one real key beside the rug",
    ),
    Case(
        "candle-riddle",
        "Seven candles lit themselves in a dark hallway.",
        "Their flames formed the motif of an open eye.",
        "A draft under the door made the candles flicker, so it seemed to be the culprit.",
        "The flames leaned toward a sealed jar, but only when the hallway was quiet.",
        "Never open a magical container merely to make a riddle stop.",
        "observe from the doorway, read the flame pattern, and use the object as a listening charm",
        "counted the flames without stepping past the safe line",
        "listened for the jar's hidden answer through the object",
        "The eye was an injection of watchful magic trapped in the jar by an old spell.",
        "patience is safer than forcing open a mysterious thing",
        "the candles went dark one by one, leaving the open eye drawn in warm ash",
    ),
]

OPENINGS = [
    "{detective} kept a notebook for mysteries that ordinary eyes missed.",
    "Rain tapped the windows as {detective} began a new case.",
    "At dusk, {detective} and {helper} entered {setting} with careful steps.",
    "A small magical disturbance waited for {detective} near the oldest shelf.",
    "The night guard called {detective} because something impossible had happened.",
    "In {setting}, even a quiet footprint could become a clue.",
]

REACTIONS = [
    "'We need facts before guesses,' {detective} said.",
    "{helper} whispered, 'A strange mark is a clue, not a command.'",
    "'Let us look closely, but let us not touch the magic yet,' said {detective}.",
    "The two friends froze until they could name a safe next step.",
    "'What changed, and what stayed the same?' {helper} asked.",
    "{detective} closed the notebook. 'A careful detective protects people while solving a case.'",
]

TURN_LINES = [
    "That question changed the case from a frightening guess into a puzzle with a safe plan.",
    "The new clue showed them that the motif had been injected, not naturally grown.",
    "They stopped chasing the loudest suspect and followed the quietest fact.",
    "The mystery turned when the object answered only to a truthful observation.",
    "Their caution became part of the solution, not an obstacle to it.",
    "They divided the work so one friend could observe while the other stayed safe.",
]

OBJECT_ACTIONS = {
    "the silver compass": "the compass",
    "the blue key": "the key",
    "the glass marble": "the marble",
    "the brass bell": "the bell",
}


def generate_world(params: StoryParams) -> World:
    if params.detective_name == params.helper_name:
        raise StoryError("The detective and helper must have different names.")
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.object_name not in {name for name, _ in OBJECTS}:
        raise StoryError(f"Unknown magical object: {params.object_name}")

    world = World(params.setting)
    detective = world.add(Entity("detective", "character", params.detective_name))
    helper = world.add(Entity("helper", "character", params.helper_name))
    object_entity = world.add(Entity("object", "magical_object", params.object_name))
    case = CASES[abs(params.seed or 0) % len(CASES)]
    opening = OPENINGS[(abs(params.seed or 0) // 7) % len(OPENINGS)]
    reaction = REACTIONS[(abs(params.seed or 0) // 11) % len(REACTIONS)]
    turn = TURN_LINES[(abs(params.seed or 0) // 17) % len(TURN_LINES)]

    world.say(opening.format(detective=detective.label, helper=helper.label, setting=world.setting))
    world.say(f"{case.opening} The case concerned {object_entity.label}, which gave off a faint magical shimmer.")
    world.say(case.mystery)
    world.say(reaction.format(detective=detective.label, helper=helper.label))
    world.para()
    world.say(f"At first, {case.false_lead}")
    world.say(f"Then {detective.label} found a better clue: {case.clue}")
    world.say(f"{helper.label} read the warning aloud: {case.warning}")
    world.say(turn)
    world.say(f"Their plan was to {case.method}.")
    world.say(f"{detective.label} {case.detective_job}, while {helper.label} {case.helper_job}.")
    world.para()
    world.say(f"When they worked together, {case.reveal}")
    world.say(f"{detective.label} asked, 'Did we prove what happened?'")
    world.say(f"{helper.label} answered, 'Yes. We followed the motif, checked the injection, and kept everyone safe.'")
    world.say(f"The mystery was solved because the friends did not mistake a magical sign for a safe command.")
    world.say(f"They learned that {case.lesson}.")
    world.say(f"At the end, {case.ending}")

    detective.meters.update(safety=1.0, attention=1.0)
    helper.meters.update(safety=1.0, attention=1.0)
    detective.memes.update(courage=1.0, caution=1.0)
    helper.memes.update(courage=1.0, caution=1.0)
    object_entity.meters.update(magic=1.0, inspected=1.0)
    world.facts.update(
        detective=detective.label,
        helper=helper.label,
        object=object_entity.label,
        case=case.key,
        opening=case.opening,
        mystery=case.mystery,
        false_lead=case.false_lead,
        clue=case.clue,
        warning=case.warning,
        method=case.method,
        detective_job=case.detective_job,
        helper_job=case.helper_job,
        reveal=case.reveal,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
        safe=True,
        motif=True,
        injection=True,
        magic=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {f['detective']} investigate?",
            answer=f"{f['detective']} investigated this mystery: {f['mystery']} The case centered on {f['opening'].lower()}",
        ),
        QAItem(
            question="What clue changed the investigation?",
            answer=f"The important clue was that {f['clue']} It moved the detectives away from the false lead.",
        ),
        QAItem(
            question="What careful plan did the friends use?",
            answer=f"They planned to {f['method']}. {f['detective']} {f['detective_job']}, while {f['helper']} {f['helper_job']}.",
        ),
        QAItem(
            question="What was the magical injection?",
            answer=f"The magical injection was this hidden change: {f['reveal']} The motif helped reveal it.",
        ),
        QAItem(
            question="What cautionary lesson closed the story?",
            answer=f"They learned that {f['lesson']} The ending image was that {f['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question whose answer is not known yet. Careful observers use clues to solve it.",
        ),
        QAItem(
            question="What is a motif?",
            answer="A motif is a repeated shape, image, sound, or idea that can help connect clues.",
        ),
        QAItem(
            question="What is an injection in a magical story?",
            answer="An injection is something newly put into a place, object, or spell. It may change how the magic behaves.",
        ),
        QAItem(
            question="Why is caution useful around magic?",
            answer="Caution is useful because magical objects may behave unexpectedly. Observing first can prevent harm.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a detective story in {world.setting} where {f['detective']} solves a magical mystery.",
        f"Create a cautionary mystery about the motif and magical injection: {f['clue']}",
        f"Tell a child-friendly case in which {f['detective']} and {f['helper']} use {f['object']} safely.",
    ]


ASP_RULES = r"""
safe_case(C) :- mystery_case(C), clue_checked(C), caution_followed(C).
motif_injection(C) :- mystery_case(C), has_motif(C), has_injection(C), magic(C).
solved(C) :- safe_case(C), motif_injection(C), evidence(C).
#show safe_case/1.
#show motif_injection/1.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for case in CASES:
        lines.extend(
            [
                asp.fact("mystery_case", case.key),
                asp.fact("has_motif", case.key),
                asp.fact("has_injection", case.key),
                asp.fact("magic", case.key),
                asp.fact("clue_checked", case.key),
                asp.fact("caution_followed", case.key),
                asp.fact("evidence", case.key),
            ]
        )
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    symbols = asp.one_model(asp_program("#show solved/1."))
    solved = asp.atoms(symbols, "solved")
    if solved:
        print("OK: ASP found a safe solved motif-injection mystery.")
        return 0
    print("MISMATCH: ASP found no solved mystery.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--detective-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--object", dest="object_name", choices=[name for name, _ in OBJECTS])
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective_name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice([name for name in NAMES if name != detective])
    if detective == helper:
        raise StoryError("The detective and helper must have different names.")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        detective_name=detective,
        helper_name=helper,
        object_name=args.object_name or rng.choice([name for name, _ in OBJECTS]),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("the moonlit museum", "Luna", "Pip", "the silver compass", 0),
    StoryParams("the whispering library", "Milo", "Nia", "the blue key", 1),
    StoryParams("the lantern garden", "Zara", "Theo", "the glass marble", 2),
    StoryParams("the old clock tower", "Bea", "Owen", "the brass bell", 3),
]


def emit(sample: StorySample, trace: bool, qa: bool, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        facts = sample.world.facts
        print(
            "\n--- world model state ---\n"
            f"case={facts['case']} solved={facts['solved']} safe={facts['safe']} "
            f"motif={facts['motif']} injection={facts['injection']} magic={facts['magic']}"
        )
    if qa:
        for index, item in enumerate(sample.story_qa, 1):
            print(f"Q{index}: {item.question}\nA{index}: {item.answer}")
        for index, item in enumerate(sample.world_qa, 1):
            print(f"W{index}: {item.question}\nA{index}: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_case/1. #show motif_injection/1. #show solved/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        symbols = asp.one_model(asp_program("#show safe_case/1. #show motif_injection/1. #show solved/1."))
        print("\n".join(str(symbol) for symbol in symbols))
        return

    base = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            params = resolve_params(args, random.Random(base + index))
            params.seed = base + index
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], ensure_ascii=False, indent=2))
        return

    for index, sample in enumerate(samples):
        emit(sample, args.trace, args.qa, f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
