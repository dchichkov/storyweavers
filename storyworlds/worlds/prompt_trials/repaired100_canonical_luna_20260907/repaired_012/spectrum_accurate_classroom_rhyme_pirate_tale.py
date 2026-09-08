#!/usr/bin/env python3
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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0,
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Classroom:
    name: str
    spectrum: str
    accurate: bool = False
    rhyme_active: bool = False
    facts: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    captain_name: str
    mate_name: str
    classroom_name: str
    spectrum_name: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nell", "Pip", "Rory", "Tess", "Finn", "Mara"]
CLASSROOMS = ["Room Seven", "the Starboard Classroom", "Bluebell Classroom"]
SPECTRUMS = ["rainbow spectrum", "prism spectrum", "sunlit spectrum"]


ARCS = [
    {
        "key": "prism_chart",
        "premise": [
            "In {room}, pirate captain {captain} and mate {mate} prepared a bright {spectrum} chart for science day. Their teacher had asked for an accurate picture of how colors spread from a prism.",
            "Captain {captain} sailed into {room} with mate {mate} and a paper prism chart. They wanted to show the {spectrum} clearly, accurately, and with a little pirate cheer.",
        ],
        "problem": [
            "A gust from the open window scattered the color cards, so red landed beside blue and the spectrum looked all mixed up. Their chart was no longer accurate.",
            "The prism slipped, and several cards flipped upside down. The colors made a confusing rainbow while the class waited for an accurate answer.",
        ],
        "conflict": [
            "\"Pin the colors fast!\" cried {captain}. \"First check the order,\" replied {mate}. Their disagreement grew as the class bell ticked closer.",
            "{captain} wanted to guess from memory, but {mate} wanted to test each color with the prism. \"A quick guess will do,\" said one. \"An accurate chart matters,\" said the other.",
        ],
        "turn": [
            "Mate {mate} held the prism toward a stripe of sunlight. The colors appeared in a steady row, and {captain} noticed that the spectrum always began with red and ended with violet.",
            "They stopped arguing and watched one beam pass through the prism. A clear band of colors showed the true order, giving them an accurate clue.",
        ],
        "action": [
            "\"You test the beam, and I will place the cards,\" said {captain}. {mate} called each color while the captain pinned the spectrum in the same order.",
            "{captain} admitted that guessing was risky. {mate} checked the prism, and together they arranged every card from red to violet.",
        ],
        "resolution": [
            "The chart became accurate, and the class cheered when the colors matched the light. Captain and mate smiled because careful checking had saved their science lesson.",
            "The finished spectrum stretched neatly across the wall. Their disagreement ended when both pirates saw that testing and teamwork made the answer accurate.",
        ],
        "ending": [
            "The classroom prism flashed a rainbow across the chalkboard while the chart stayed bright and true.",
            "On the final bell, the accurate spectrum shimmered above the desks like a tiny flag from a friendly ship.",
        ],
        "problem_fact": "a window gust scattered the spectrum cards",
        "clue_fact": "a prism showed the accurate color order",
        "action_fact": "they tested the light and arranged the colors from red to violet",
        "outcome_fact": "the classroom chart became accurate",
    },
    {
        "key": "rainbow_riddle",
        "premise": [
            "Pirate captain {captain} and mate {mate} were writing a rhyming science riddle in {room}. Their clue described a {spectrum} hidden inside a beam of light.",
            "In {room}, {captain} drew a {spectrum} while {mate} wrote a rhyme for visiting families. They wanted every line to be playful and accurate.",
        ],
        "problem": [
            "The last rhyme said that green came after violet, so the riddle sent everyone to the wrong color. The rhyme sounded catchy, but it was not accurate.",
            "A missing word changed the rhyme's meaning. Children followed the silly clue to the wrong end of the spectrum.",
        ],
        "conflict": [
            "\"Keep the rhyme; it sounds grand!\" said {captain}. \"Fix the fact; it must be accurate,\" said {mate}. Their pirate quarrel echoed between the desks.",
            "{captain} wanted a funny ending, while {mate} wanted the true color order. Neither pirate would change the final line.",
        ],
        "turn": [
            "Mate {mate} pointed the prism at a white wall and read the colors aloud. The real spectrum gave them a new ending that rhymed with the correct fact.",
            "They tested the light instead of trusting the old verse. The beam showed the accurate order, and {captain} found a rhyme for violet.",
        ],
        "action": [
            "\"Red, orange, yellow, green, blue, indigo, violet,\" chanted {mate}. {captain} rewrote the rhyme so its music matched the spectrum.",
            "{captain} kept the playful beat but changed the wrong line. {mate} checked every color against the prism before they posted the riddle.",
        ],
        "resolution": [
            "The children solved the riddle and learned the accurate color order. The pirates discovered that a rhyme can be fun without bending the truth.",
            "The new verse made the class laugh and point to the right colors. Their rhyme and spectrum now agreed from beginning to end.",
        ],
        "ending": [
            "The corrected riddle hung beside the prism, singing softly whenever sunlight crossed the room.",
            "Seven color cards rested under the rhyme, each one in its accurate place.",
        ],
        "problem_fact": "a catchy rhyme gave the wrong spectrum order",
        "clue_fact": "the prism revealed the accurate color sequence",
        "action_fact": "they rewrote the rhyme to match the tested spectrum",
        "outcome_fact": "the class learned the true color order",
    },
]


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    text = "|".join(
        [params.captain_name, params.mate_name, params.classroom_name, params.spectrum_name]
    )
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


class World:
    def __init__(self, classroom: Classroom) -> None:
        self.classroom = classroom
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def tell(params: StoryParams) -> World:
    classroom = Classroom(params.classroom_name, params.spectrum_name)
    world = World(classroom)
    captain = world.add(Entity(params.captain_name, "character", "captain"))
    mate = world.add(Entity(params.mate_name, "character", "mate"))
    prism = world.add(Entity("prism", "thing", "prism"))
    captain.meters["attention"] = 1.0
    mate.meters["attention"] = 1.0
    prism.meters["clarity"] = 1.0

    rng = _rng_for(params)
    arc = ARCS[(params.seed or rng.randrange(len(ARCS))) % len(ARCS)]
    beats = ["premise", "problem", "conflict", "turn", "action", "resolution", "ending"]
    chosen = {}
    for index, beat in enumerate(beats):
        if params.seed is not None:
            chosen[beat] = arc[beat][((params.seed // len(ARCS)) + index) % len(arc[beat])]
        else:
            chosen[beat] = rng.choice(arc[beat])
        if index:
            world.para()
        world.say(
            chosen[beat].format(
                captain=params.captain_name,
                mate=params.mate_name,
                room=params.classroom_name,
                spectrum=params.spectrum_name,
            )
        )

    classroom.accurate = True
    classroom.rhyme_active = True
    classroom.facts = {
        "captain": captain,
        "mate": mate,
        "prism": prism,
        "arc": arc,
        "problem": arc["problem_fact"],
        "clue": arc["clue_fact"],
        "action": arc["action_fact"],
        "outcome": arc["outcome_fact"],
        "problem_event": chosen["problem"].format(
            captain=params.captain_name, mate=params.mate_name,
            room=params.classroom_name, spectrum=params.spectrum_name
        ),
        "turn_event": chosen["turn"].format(
            captain=params.captain_name, mate=params.mate_name,
            room=params.classroom_name, spectrum=params.spectrum_name
        ),
        "action_event": chosen["action"].format(
            captain=params.captain_name, mate=params.mate_name,
            room=params.classroom_name, spectrum=params.spectrum_name
        ),
        "resolution_event": chosen["resolution"].format(
            captain=params.captain_name, mate=params.mate_name,
            room=params.classroom_name, spectrum=params.spectrum_name
        ),
    }
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly pirate tale set in a classroom about a spectrum and an accurate answer.",
        "Include a rhyme that helps two classroom pirates solve a color problem.",
        "Show how testing a prism changes a disagreement into teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.classroom.facts
    captain, mate = f["captain"], f["mate"]
    return [
        QAItem(
            f"What were {captain.id} and {mate.id} doing in the classroom?",
            f"They were preparing a classroom lesson about a {world.classroom.spectrum} and trying to make their work accurate.",
        ),
        QAItem("What went wrong?", f["problem_event"]),
        QAItem("What clue helped them?", f["turn_event"]),
        QAItem("How did they solve the problem?", f"{f['action_event']} {f['resolution_event']}"),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a spectrum?",
            "A spectrum is an ordered band of related colors or other things, such as the colors made when light passes through a prism.",
        ),
        QAItem(
            "What does accurate mean?",
            "Accurate means correct and matching the facts or the thing being measured.",
        ),
        QAItem(
            "What is a rhyme?",
            "A rhyme is a pattern in which words have matching or similar ending sounds.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:8}) meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  classroom={world.classroom.name}")
    lines.append(f"  spectrum={world.classroom.spectrum}")
    lines.append(f"  accurate={world.classroom.accurate}")
    lines.append(f"  rhyme_active={world.classroom.rhyme_active}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story :- setting(classroom), theme(spectrum), quality(accurate), feature(rhyme), style(pirate_tale).
#show valid_story/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("setting", "classroom"),
            asp.fact("theme", "spectrum"),
            asp.fact("quality", "accurate"),
            asp.fact("feature", "rhyme"),
            asp.fact("style", "pirate_tale"),
        ]
    )


def asp_program(show: str = "#show valid_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    if any(sym.name == "valid_story" for sym in model):
        print("OK: ASP twin recognizes the accurate classroom spectrum rhyme tale.")
        return 0
    print("MISMATCH: ASP twin rejected the story pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classroom pirate tale about an accurate spectrum and a rhyme."
    )
    parser.add_argument("--captain-name")
    parser.add_argument("--mate-name")
    parser.add_argument("--classroom-name", choices=CLASSROOMS)
    parser.add_argument("--spectrum-name", choices=SPECTRUMS)
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
    captain = args.captain_name or rng.choice(NAMES)
    mate = args.mate_name or rng.choice([name for name in NAMES if name != captain])
    return StoryParams(
        captain_name=captain,
        mate_name=mate,
        classroom_name=args.classroom_name or rng.choice(CLASSROOMS),
        spectrum_name=args.spectrum_name or rng.choice(SPECTRUMS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generate_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool, qa: bool, header: str = "") -> None:
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
        raise SystemExit(asp_verify())
    if args.asp:
        print("1 compatible classroom pirate story pattern: spectrum + accurate + rhyme")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "Milo", "Room Seven", "rainbow spectrum"),
            StoryParams("Nell", "Pip", "the Starboard Classroom", "prism spectrum"),
        ]
        samples = [generate(params) for params in params_list]
    else:
        samples = []
        seen = set()
        for index in range(max(args.n, 0)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

    if args.json:
        print(
            samples[0].to_json()
            if len(samples) == 1
            else json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False)
        )
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
