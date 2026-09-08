#!/usr/bin/env python3
"""A child-safe magical detective storyworld about a sweeping broom and a fair fight."""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ("dirt", "danger", "magic", "evidence"):
            self.meters.setdefault(key, 0.0)
        for key in ("worry", "courage", "trust", "relief", "surprise"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    place: str
    detective: str
    helper: str
    suspect: str
    object_name: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    title: str
    clue: str
    false_guess: str
    cause: str
    method: str
    fight_reason: str
    transformation: str
    bad_ending: str
    repair: str
    lesson: str
    final_image: str


CASES = [
    Case(
        "The Vanishing Blue Broom",
        "a line of blue dust curved from the front steps to a locked cupboard",
        "the broom had swept itself away",
        "a jealous shadow spell had pulled the broom toward the cupboard",
        "they followed the dust while keeping one hand on the brass bell that broke small enchantments",
        "the shadow wanted the broom, and the broom resisted by rattling its handle",
        "the broom changed into a bright blue feather duster when the bell rang",
        "if they chased the shadow into the cupboard, the whole station would become a dark maze",
        "they opened the cupboard in daylight, thanked the broom, and swept the shadow into a jar",
        "A strange change needs careful evidence, not a hurried guess",
        "the blue duster made neat circles while morning light filled the station",
    ),
    Case(
        "The Moonlit Footprints",
        "silver footprints stopped beside a fresh pile of swept leaves",
        "the gardener had sneaked through the locked gate",
        "a moon charm had transformed the leaves into tiny walking boots",
        "they measured the prints with a ruler and compared them with the charm's loose thread",
        "the enchanted leaves marched toward the fountain and knocked over its warning sign",
        "the leaves became ordinary leaves when the detective named each one aloud",
        "if the leaves reached the fountain, the water would rise over the square",
        "they swept the leaves into a marked basket and tied the charm safely shut",
        "Naming what you observe can turn a magical puzzle into a manageable task",
        "the fountain trickled quietly beside a tidy basket of leaves",
    ),
    Case(
        "The Broomstick Challenge",
        "two clean stripes crossed the dusty hall even though no one admitted sweeping",
        "the stripes proved that the caretaker had cheated",
        "a practice broom had copied every movement from a friendly training fight",
        "they checked the floor marks, asked both players questions, and inspected the broom's knot",
        "the broom mistook a safe sparring match for a dangerous fight",
        "the broom transformed into a wooden referee and raised a tiny flag",
        "if they blamed someone, the magic would choose a new fighter and make the argument worse",
        "they set clear rules, swept the hall together, and ended the match with a bow",
        "Fair questions can stop a small quarrel from becoming a bad ending",
        "the wooden referee rested by the clean hall while both friends laughed",
    ),
    Case(
        "The Black Glitter Trail",
        "black glitter lay beneath the library window and sparkled only near moonlight",
        "the missing storybook had flown out the window",
        "a spell inside the book had transformed its bookmark into a trail",
        "they swept the glitter into a paper line and followed it to a reading cushion",
        "the bookmark was frightened by the loud fight outside",
        "the bookmark changed into a small silver key",
        "if the book stayed frightened, its stories would vanish before sunrise",
        "they quieted the room, used the key, and returned the bookmark to its page",
        "Gentle actions can reveal more than a loud confrontation",
        "the returned book opened to a picture of a silver key",
    ),
]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)


DETECTIVES = ["Luna", "Mara", "Theo", "Nell", "Pip"]
HELPERS = ["Robin", "Ivy", "Jasper", "Milo", "Sana"]
SUSPECTS = ["the caretaker", "the moon gardener", "the practice wizard", "the quiet librarian"]
OBJECTS = ["broom", "dustpan", "storybook", "silver key"]


def choose_case(seed: Optional[int]) -> Case:
    return CASES[(seed or 0) % len(CASES)]


def validate(params: StoryParams) -> None:
    if not params.place.strip():
        raise StoryError("place must not be empty")
    names = {params.detective.strip(), params.helper.strip()}
    if len(names) != 2:
        raise StoryError("detective and helper must have different names")
    if not params.object_name.strip():
        raise StoryError("object_name must not be empty")


def tell_story(params: StoryParams) -> World:
    validate(params)
    case = choose_case(params.seed)
    world = World(params.place)

    detective = world.add(Entity(
        params.detective, "character", "detective", params.detective,
        memes={"courage": 1.0, "worry": 1.0},
    ))
    helper = world.add(Entity(
        params.helper, "character", "helper", params.helper,
        memes={"trust": 1.0, "surprise": 1.0},
    ))
    suspect = world.add(Entity(
        "suspect", "character", "possible suspect", params.suspect,
        memes={"worry": 1.0},
    ))
    broom = world.add(Entity(
        "broom", "object", "magical cleaning tool", params.object_name,
        meters={"dirt": 0.8, "danger": 0.4, "magic": 1.0, "evidence": 0.0},
    ))

    world.facts.update(
        case=case,
        detective=detective,
        helper=helper,
        suspect=suspect,
        broom=broom,
        resolved=False,
        child_safe=True,
    )

    world.say(f"In the {params.place}, Detective {params.detective} noticed that the {params.object_name} was missing.")
    world.say(f"{params.helper} stood beside a half-swept floor, while {params.suspect} waited near the notice board.")
    world.say(f'"I saw a fight of shadows, but I did not see who began it," {params.helper} said.')
    world.say(f'"Then we will sweep for clues before we choose a culprit," {params.detective} replied.')
    world.say(f"The first clue was {case.clue}.")
    world.say(f'{params.detective} wondered whether {case.false_guess}, but that guess did not explain every mark.')
    world.say(f'"Let us test the floor, the broom, and the story," said {params.detective}. "Nobody needs to fight while we investigate."')
    world.say(f"They {case.method}.")
    world.say(f"The evidence showed that {case.cause}.")
    world.say(f'A brief {case.fight_reason}; {params.detective} placed the brass bell between the arguing shapes and asked everyone to step back.')
    world.say(f"The magic caused this transformation: {case.transformation}.")
    world.say(f'"We must stop before this becomes a bad ending," {params.helper} said. "What would happen if we did nothing?"')
    world.say(f"They learned that {case.bad_ending}.")
    world.say(f"With calm voices and a careful sweep, {case.repair}.")
    world.say(f'"{case.lesson}," {params.detective} said.')
    world.say(f"{case.final_image.capitalize()}. The case was closed, and nobody had been blamed without proof.")

    broom.meters.update(dirt=0.0, danger=0.0, evidence=1.0)
    detective.memes.update(worry=0.0, courage=1.0, relief=1.0)
    helper.memes.update(surprise=0.0, trust=1.0, relief=1.0)
    suspect.memes["worry"] = 0.0
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    return [
        'Write a child-safe detective story using the words "sweep" and "fight".',
        f'Tell a magical detective mystery about "{case.title}" with a transformation and a narrowly avoided bad ending.',
        f"Show how the clue that {case.clue} changes the detective's decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    detective: Entity = world.facts["detective"]
    helper: Entity = world.facts["helper"]
    broom: Entity = world.facts["broom"]
    return [
        QAItem(
            f"What did Detective {detective.label} do before choosing a culprit?",
            f"Detective {detective.label} swept for clues and tested the floor, the {broom.label}, and the story before blaming anyone.",
        ),
        QAItem(
            "What clue started the investigation?",
            f"The clue was that {case.clue}. It gave the detective a physical trail to examine.",
        ),
        QAItem(
            "What caused the strange event?",
            f"The detective discovered that {case.cause}. The cause explained the magical marks better than the first guess.",
        ),
        QAItem(
            "How did the characters handle the fight?",
            f"They stepped back, used calm voices, and kept investigating instead of turning the disagreement into a dangerous fight.",
        ),
        QAItem(
            "What transformation happened, and what bad ending did they avoid?",
            f"{case.transformation}. They avoided the bad ending in which {case.bad_ending}.",
        ),
        QAItem(
            f"What lesson did {helper.label} and the detective learn?",
            case.lesson + ".",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does a detective do?",
            "A detective gathers clues, asks careful questions, tests explanations, and uses evidence to understand a mystery.",
        ),
        QAItem(
            "Why can sweeping help an investigation?",
            "Sweeping can reveal or collect small physical clues such as dust, glitter, footprints, or threads.",
        ),
        QAItem(
            "How should children handle a fight?",
            "Children should move away, use calm words, and ask a trusted adult for help rather than joining the fight.",
        ),
        QAItem(
            "What is magic in this storyworld?",
            "Magic is an unusual force that can move objects, reveal clues, or transform one thing into another, but careful choices still matter.",
        ),
        QAItem(
            "What is a bad ending?",
            "A bad ending is a harmful result that can happen when people ignore evidence, blame unfairly, or keep an unsafe argument going.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *sample.prompts, "", "== story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"place: {world.place}", f"resolved: {world.facts['resolved']}"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.label}: kind={entity.kind} type={entity.type} "
            f"meters={meters} memes={memes}"
        )
    case: Case = world.facts["case"]
    lines.append(f"case: {case.title}")
    lines.append(f"cause: {case.cause}")
    lines.append(f"transformation: {case.transformation}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Magical detective storyworld about a sweeping mystery.")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = rng.choice(DETECTIVES)
    helper = rng.choice([name for name in HELPERS if name != detective])
    return StoryParams(
        place="the old town mystery station",
        detective=detective,
        helper=helper,
        suspect=rng.choice(SUSPECTS),
        object_name=rng.choice(OBJECTS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print("\n" + format_qa(sample))


ASP_RULES = r"""
place(old_town_mystery_station).
theme(sweep).
theme(fight).
feature(transformation).
feature(bad_ending).
feature(magic).
style(detective_story).
safe_investigation :- theme(sweep), theme(fight), style(detective_story).
careful_resolution :- safe_investigation, feature(transformation), feature(magic).
avoids_bad_ending :- careful_resolution, feature(bad_ending).
#show safe_investigation/0.
#show careful_resolution/0.
#show avoids_bad_ending/0.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("place", "old_town_mystery_station"),
        asp.fact("theme", "sweep"),
        asp.fact("theme", "fight"),
        asp.fact("feature", "transformation"),
        asp.fact("feature", "bad_ending"),
        asp.fact("feature", "magic"),
        asp.fact("style", "detective_story"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from asp import atoms, one_model
        symbols = one_model(asp_program())
        required = {"safe_investigation", "careful_resolution", "avoids_bad_ending"}
        found = {name for name in required if atoms(symbols, name)}
        if found != required:
            return 1
    except Exception:
        return 1

    for index in range(len(CASES)):
        params = StoryParams(
            place="the old town mystery station",
            detective="Luna",
            helper="Robin",
            suspect="the caretaker",
            object_name="broom",
            seed=index,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            return 1
        if "sweep" not in sample.story.lower() or "fight" not in sample.story.lower():
            return 1
        if not sample.story_qa or not sample.world_qa:
            return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp or args.asp:
        print(asp_program("#show place/1.\n#show theme/1.\n#show safe_investigation/0.\n#show careful_resolution/0.\n#show avoids_bad_ending/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        params_list = [
            StoryParams(
                place="the old town mystery station",
                detective="Luna",
                helper="Robin",
                suspect="the caretaker",
                object_name="broom",
                seed=index,
            )
            for index in range(len(CASES))
        ]
    else:
        params_list = []
        for offset in range(max(0, args.n)):
            seed = base_seed + offset
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            params_list.append(params)

    samples = [generate(params) for params in params_list]

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
