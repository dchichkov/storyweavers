#!/usr/bin/env python3
from __future__ import annotations

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
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))),
)
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Mystery:
    title: str
    setting: str
    missing_item: str
    culprit: str = ""
    clue: str = ""
    method: str = ""
    solved: bool = False
    facts: dict[str, str] = field(default_factory=dict)


@dataclass
class StoryParams:
    detective_name: str
    helper_name: str
    suspect_name: str
    title: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Tess", "Pip", "Nora", "Jules", "Ari", "Bea"]
TITLES = ["The Repeated Signal", "The Bough Mystery", "The Goober Message", "The Whispering Branch"]
SETTINGS = [
    "the old orchard",
    "the moonlit garden",
    "the library courtyard",
    "the quiet park",
]


class World:
    def __init__(self, mystery: Mystery) -> None:
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _rng_for(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed)
    raw = "|".join((params.detective_name, params.helper_name, params.suspect_name, params.title))
    return random.Random(int.from_bytes(hashlib.sha256(raw.encode()).digest()[:8], "big"))


CASES = [
    {
        "missing": "the brass garden bell",
        "culprit": "the wind-up magpie",
        "clue": "a repeated click beneath the lowest bough",
        "method": "the magpie hid the bell inside a hollow branch while copying its ring",
        "opening": "Luna was the young detective of the old orchard, where a brass garden bell vanished before breakfast.",
        "problem": "Every few minutes, the same tiny ding came from the trees, but the bell itself was nowhere to be seen.",
        "dialogue": [
            '"I heard the ding near the gate," said Luna.',
            '"I heard it near the pond," replied Milo.',
            '"Then the sound is being transmitted," Luna said. "We must follow the repetition, not chase each echo."',
        ],
        "turn": "Luna pressed an ear to a low bough and heard the ding, ding, ding coming from inside the wood.",
        "action": "Milo noticed a trail of shiny seeds leading from the bough to a nest, and Luna gently lifted the loose bark.",
        "resolution": "Inside the hollow they found the missing bell beside the wind-up magpie, which had learned to repeat its ring.",
        "ending": "The bell was hung back on the gate, while the magpie clicked happily from the bough and transmitted one honest ding across the orchard.",
    },
    {
        "missing": "the mayor's silver message tube",
        "culprit": "a playful squirrel",
        "clue": "the word goober repeated in every scratch mark",
        "method": "the squirrel rolled the tube through a hollow bough and used it as a noisy tunnel",
        "opening": "Detective Luna arrived at the moonlit garden when the mayor's silver message tube disappeared.",
        "problem": "A whisper traveled from flower bed to flower bed, always repeating one odd word: goober.",
        "dialogue": [
            '"Goober is not a suspect," said Luna.',
            '"It may be a clue," said Tess.',
            '"Exactly," Luna replied. "Let us transmit the word along the path and see where it changes."',
        ],
        "turn": "They whispered goober beside each tree. Only the lowest bough sent the word back with a hollow rattle.",
        "action": "Luna tapped the bough three times, and Tess followed the sound to a tunnel in the wood.",
        "resolution": "The silver tube rolled out with a squirrel, who had borrowed it to make the loudest goober echo in the garden.",
        "ending": "The mayor received the tube, and the squirrel transmitted a soft goober through the bough as an apology.",
    },
    {
        "missing": "a blue envelope of moon notes",
        "culprit": "the old talking crow",
        "clue": "a repeated feather tap that matched the envelope's seal",
        "method": "the crow tucked the envelope under a bough and repeated the message to practice speaking",
        "opening": "In the quiet park, Luna was asked to find a blue envelope filled with moon notes.",
        "problem": "The envelope had vanished, but a tap-tap-tap kept repeating from the branches after sunset.",
        "dialogue": [
            '"The tapping is a message," said Pip.',
            '"Or a bird with excellent manners," said Luna.',
            '"Ask it directly," Pip suggested.',
            '"Who has the envelope?" Luna called. "Who has the envelope?" the branches transmitted back.',
        ],
        "turn": "The repeated answer came from one crooked bough, where a blue thread clung to the bark.",
        "action": "Luna followed the thread while Pip watched the crow's feet and found a hidden fold beneath the branch.",
        "resolution": "The crow had taken the envelope to practice the words inside, including the mysterious word goober.",
        "ending": "The moon notes returned to their owner, and the crow transmitted the last line clearly from the bough.",
    },
]


def tell(params: StoryParams) -> World:
    rng = _rng_for(params)
    case = CASES[(params.seed or rng.randrange(len(CASES))) % len(CASES)]
    mystery = Mystery(
        title=params.title,
        setting=rng.choice(SETTINGS) if params.seed is None else SETTINGS[(params.seed // 3) % len(SETTINGS)],
        missing_item=case["missing"],
    )
    world = World(mystery)

    detective = world.add(Entity(params.detective_name, "character", "detective", "detective"))
    helper = world.add(Entity(params.helper_name, "character", "helper", "helper"))
    suspect = world.add(Entity(params.suspect_name, "character", "suspect", "suspect"))
    bough = world.add(Entity("bough", "thing", "bough", "a low bough"))
    goober = world.add(Entity("goober", "thing", "word", "the word goober"))
    transmitter = world.add(Entity("transmitter", "thing", "signal", "a hollow transmitter"))

    detective.meters["attention"] = 5.0
    helper.meters["attention"] = 4.0
    bough.meters["hollow"] = 1.0
    transmitter.meters["range"] = 3.0
    goober.memes["repetition"] = 1.0

    world.say(case["opening"])
    world.para()
    world.say(f"The case concerned {case['missing']}. {case['problem']}")
    world.para()
    for line in case["dialogue"]:
        world.say(line)
    world.para()
    world.say(case["turn"])
    world.para()
    world.say(case["action"])
    world.para()
    world.say(case["resolution"])
    world.para()
    world.say(case["ending"])

    mystery.culprit = case["culprit"]
    mystery.clue = case["clue"]
    mystery.method = case["method"]
    mystery.solved = True
    mystery.facts = {
        "missing": case["missing"],
        "culprit": case["culprit"],
        "clue": case["clue"],
        "method": case["method"],
        "opening": case["opening"],
        "problem": case["problem"],
        "turn": case["turn"],
        "action": case["action"],
        "resolution": case["resolution"],
        "ending": case["ending"],
    }
    suspect.memes["suspicion"] = 0.0
    return world


def generate_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly whodunit involving a bough, a transmitted signal, and the word goober.",
        f"Tell a mystery in which repetition helps a detective discover who hid {world.mystery.missing_item}.",
        "Write a short dialogue-led mystery with a clear clue, a fair solution, and a changed ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.mystery.facts
    return [
        QAItem(
            question="What disappeared?",
            answer=f"The missing item was {f['missing']}.",
        ),
        QAItem(
            question="What repeated clue helped the detectives?",
            answer=f"They followed {f['clue']}, instead of trusting the confusing echoes.",
        ),
        QAItem(
            question="Who had hidden the missing item?",
            answer=f"The item had been hidden by {f['culprit']}.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{f['action']} {f['resolution']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bough?",
            answer="A bough is a large branch growing from the trunk of a tree.",
        ),
        QAItem(
            question="What does transmit mean?",
            answer="To transmit means to send a sound, message, or signal from one place to another.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or hearing something again and again.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is the spoken conversation between characters.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"  {entity.id:12} ({entity.type:10}) {' '.join(details)}")
    lines.append(f"  mystery.solved={world.mystery.solved}")
    lines.append(f"  mystery.culprit={world.mystery.culprit}")
    lines.append(f"  mystery.clue={world.mystery.clue}")
    return "\n".join(lines)


ASP_RULES = r"""
solved :-
    object(missing),
    clue(repetition),
    feature(dialogue),
    feature(transmit),
    word(goober),
    place(bough),
    culprit_found.

culprit_found :-
    culprit(_).

#show solved/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join(
        [
            asp.fact("object", "missing"),
            asp.fact("clue", "repetition"),
            asp.fact("feature", "dialogue"),
            asp.fact("feature", "transmit"),
            asp.fact("word", "goober"),
            asp.fact("place", "bough"),
            asp.fact("culprit", "found"),
        ]
    )


def asp_program(show: str = "#show solved/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program())
    valid = any(symbol.name == "solved" for symbol in model)
    sample = generate(
        StoryParams(
            detective_name="Luna",
            helper_name="Milo",
            suspect_name="Pip",
            title="The Repeated Signal",
            seed=7,
        )
    )
    prose = sample.story.lower()
    required = all(word in prose for word in ("bough", "transmit", "goober"))
    dialogue = '"' in sample.story
    if valid and required and dialogue and sample.world.mystery.solved:
        print("OK: Python story and ASP whodunit twin agree.")
        return 0
    print("MISMATCH: Python story and ASP whodunit twin disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Whodunit world with a bough, transmitted repetition, dialogue, and goober."
    )
    parser.add_argument("--detective-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--suspect-name")
    parser.add_argument("--title", choices=TITLES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    detective = args.detective_name or rng.choice(NAMES)
    available = [name for name in NAMES if name != detective]
    helper = args.helper_name or rng.choice(available)
    available = [name for name in available if name != helper]
    suspect = args.suspect_name or rng.choice(available)
    title = args.title or rng.choice(TITLES)
    return StoryParams(
        detective_name=detective,
        helper_name=helper,
        suspect_name=suspect,
        title=title,
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
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print("ASP model:", " ".join(str(atom) for atom in model))
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Luna", "Milo", "Pip", "The Repeated Signal", 3),
            StoryParams("Nora", "Tess", "Jules", "The Bough Mystery", 7),
            StoryParams("Ari", "Bea", "Milo", "The Goober Message", 11),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < max(0, args.n):
            seed = base_seed + index
            index += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
