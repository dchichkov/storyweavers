#!/usr/bin/env python3
"""
A small child-facing magic whodunit about a cyclone at a seaside fair.

The world models a lighthouse fair, a vanished magic lantern, a cyclone,
physical meters, emotional memes, clues, suspects, dialogue, and a fair
solution driven by evidence rather than blame.
"""
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
    label: str
    type: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class LighthouseWorld:
    place: str = "the lighthouse fair"
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    keeper_name: str
    suspect_name: str
    charm: str
    cyclone_name: str
    scenario_id: int = 0
    opening_id: int = 0
    dialogue_id: int = 0
    clue_id: int = 0
    ending_id: int = 0
    seed: Optional[int] = None


CHILD_NAMES = ["Luna", "Milo", "Iris", "Theo", "Nia", "Owen"]
KEEPERS = ["Captain Vale", "Aunt Maris", "Mr. Rowan"]
SUSPECTS = ["Pip the Magician", "Bram the Drummer", "Sela the Kite Maker"]
CHARMS = ["moonstone lantern", "silver compass", "blue star crystal"]
CYCLONES = ["Cyclone Orla", "Cyclone Niko", "Cyclone Vela"]

CASES = [
    {
        "object": "the magic lantern vanished from the lighthouse balcony",
        "suspect": "Pip the Magician had taken it to make the storm obey",
        "clue": "a trail of blue glitter led from the lantern hook to the old weather door",
        "truth": "the cyclone's strong wind had pulled the lantern's ribbon through the open weather door",
        "action": "followed the glitter trail and found the ribbon caught on a weather vane",
        "help": "held the door safely while the keeper freed the ribbon",
        "result": "the lantern was returned to its hook before the next gust arrived",
        "image": "the lantern cast a warm moon on the wet stones while the weather vane turned quietly",
        "lesson": "a clue can be kinder and more useful than a quick accusation",
    },
    {
        "object": "the magic compass spun wildly beside the storm bell",
        "suspect": "Bram the Drummer had hidden it to make the fair more exciting",
        "clue": "the compass needle pointed toward a copper wire beneath the bell",
        "truth": "lightning had charged the wire, and its invisible pull made the compass dance",
        "action": "watched from a dry step and traced the needle toward the copper wire",
        "help": "asked everyone to move back while the keeper lowered the storm bell's switch",
        "result": "the compass settled and pointed north again",
        "image": "the compass rested in Luna's palm with its needle aimed at the first clear star",
        "lesson": "careful watching can separate a magical-looking trick from a simple cause",
    },
    {
        "object": "the magic star crystal disappeared from the fair's wishing bowl",
        "suspect": "Sela the Kite Maker had borrowed it for a secret kite",
        "clue": "one shining thread stretched from the bowl to the lighthouse stair",
        "truth": "the cyclone had lifted the crystal's pouch and snagged it on a stair rail",
        "action": "climbed only after the keeper checked the steps and followed the shining thread",
        "help": "used a long wooden pole to lift the pouch down without reaching into the wind",
        "result": "the crystal returned to the wishing bowl, safe and dry",
        "image": "the star crystal glowed beside the bowl while rain pearls shone on the stair rail",
        "lesson": "solving a mystery means using evidence and safe help together",
    },
    {
        "object": "the magic lantern flashed three times during the cyclone warning",
        "suspect": "Pip the Magician was sending a secret signal to frighten everyone",
        "clue": "each flash followed a tap from the loose balcony shutter",
        "truth": "the shutter was bumping the lantern's spell switch whenever the wind pushed it",
        "action": "counted the flashes, watched the shutter, and found the loose hinge",
        "help": "closed the inner window and tied the shutter with a strong rope",
        "result": "the warning bell became the only flashing signal",
        "image": "the lantern glowed steadily above a neatly tied shutter",
        "lesson": "a fair test can turn a scary guess into a clear answer",
    },
]


OPENINGS = [
    "While a cyclone curled beyond the harbor, {child} arrived at the lighthouse fair and discovered that {object}.",
    "The lighthouse fair was bright and busy while a cyclone roared far out at sea. Then {child} noticed that {object}.",
    "While rain tapped the fair tents, {child} heard a gasp near the lighthouse: {object}.",
    "A cyclone warning fluttered above the fair while {child} found a mystery waiting on the lighthouse balcony: {object}.",
]

DIALOGUES = [
    '"Let us ask questions before we point fingers," {keeper} said.',
    '"A mystery needs eyes, ears, and a calm heart," {keeper} told {child}.',
    '"The wind may be loud, but the clues can still speak," {keeper} said.',
    '"We will solve this safely together," {keeper} promised.',
]

CLUE_LEADS = [
    "Luna knelt beside the hook and noticed that {clue}.",
    "The first useful sign was clear: {clue}.",
    "Instead of guessing, {child} studied the balcony and saw that {clue}.",
    "A tiny sparkle caught {child}'s eye. It showed that {clue}.",
]

ENDINGS = [
    "At last, {result}.",
    "By the time the cyclone moved farther out to sea, {result}.",
    "The fair grew calm again, and {result}.",
    "When the rain softened to a whisper, {result}.",
]


def valid_combo(params: StoryParams) -> bool:
    if not all([
        params.child_name.strip(),
        params.keeper_name.strip(),
        params.suspect_name.strip(),
        params.charm.strip(),
        params.cyclone_name.strip(),
    ]):
        return False
    if params.child_name == params.suspect_name:
        return False
    if params.charm not in CHARMS:
        return False
    return True


ASP_RULES = r"""
missing(Item) :- object_missing(Item).
fair_solution :- clue_found, safe_help, missing(charm).
#show missing/1.
#show fair_solution/0.
"""


def asp_facts(params: Optional[StoryParams] = None) -> str:
    import asp
    charm = params.charm if params else "moonstone_lantern"
    return "\n".join([
        asp.fact("object_missing", charm.replace(" ", "_")),
        asp.fact("clue_found"),
        asp.fact("safe_help"),
    ])


def asp_program(params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}"


def tell(params: StoryParams) -> LighthouseWorld:
    if not valid_combo(params):
        raise StoryError("The child, keeper, suspect, charm, and cyclone must be distinct and usable.")
    case = CASES[params.scenario_id % len(CASES)]
    world = LighthouseWorld()
    child = world.add(Entity(
        params.child_name, "child", params.child_name, params.child_type,
        meters={"curiosity": 1.0, "safety": 0.0},
        memes={"worry": 0.0, "courage": 0.0, "trust": 0.0},
    ))
    keeper = world.add(Entity(
        "keeper", "adult", params.keeper_name, "keeper",
        meters={"safety": 1.0}, memes={"patience": 1.0},
    ))
    suspect = world.add(Entity(
        "suspect", "magician", params.suspect_name, "performer",
        meters={"magic": 1.0}, memes={"worry": 0.0},
    ))
    charm = world.add(Entity(
        "charm", "object", params.charm,
        meters={"glow": 1.0, "wind_risk": 0.0},
        memes={"wonder": 1.0},
    ))
    storm = world.add(Entity(
        "cyclone", "weather", params.cyclone_name, "cyclone",
        meters={"wind": 1.0, "rain": 1.0}, memes={"danger": 1.0},
    ))
    world.facts.update(
        child=child, keeper=keeper, suspect=suspect, charm=charm, storm=storm,
        case=case, resolved=False, clue_found=False, safe_help=False,
    )

    world.say(OPENINGS[params.opening_id % len(OPENINGS)].format(
        child=child.label, object=case["object"],
    ))
    world.say(
        f"The fair workers looked toward {suspect.label}, because {case['suspect']}. "
        f"{child.label} felt worried, but the keeper raised a steady hand."
    )
    child.memes["worry"] = 1.0
    world.para()

    world.say(DIALOGUES[params.dialogue_id % len(DIALOGUES)].format(
        keeper=keeper.label, child=child.label,
    ))
    world.say(
        f'"Did you take the {charm.label}?" {child.label} asked {suspect.label}. '
        f'"No," said {suspect.label}. "I was tying down the blue fair tent while the cyclone grew stronger."'
    )
    world.say(
        f'"Then we will check the evidence," {keeper.label} said. '
        f'"Words can tell us where to look, but clues will tell us what happened."'
    )
    child.memes["courage"] = 1.0
    world.para()

    world.say(CLUE_LEADS[params.clue_id % len(CLUE_LEADS)].format(
        child=child.label, clue=case["clue"],
    ))
    world.say(
        f'The clue matched the storm: {case["truth"]}. '
        f'{child.label} no longer blamed {suspect.label}; instead, {child.label} {case["action"]}.'
    )
    world.say(
        f'"I see it now," {child.label} said. '
        f'"The cyclone moved the magic, but nobody meant to cause trouble."'
    )
    world.say(
        f'"Exactly," {keeper.label} replied. "Now let us use safe hands." '
        f'{keeper.label} {case["help"]}.'
    )
    world.facts["clue_found"] = True
    world.facts["safe_help"] = True
    child.memes["worry"] = 0.0
    child.memes["trust"] = 1.0
    world.para()

    world.say(f'{ENDINGS[params.ending_id % len(ENDINGS)].format(result=case["result"])}')
    world.say(f'{case["image"]}.')
    world.say(
        f'{suspect.label} smiled at {child.label}. "Thank you for asking instead of guessing," '
        f'{suspect.label} said.'
    )
    world.say(
        f'{child.label} learned that {case["lesson"]} '
        f'while the cyclone passed beyond the harbor.'
    )
    world.facts["resolved"] = True
    charm.meters["wind_risk"] = 0.0
    return world


def generation_prompts(world: LighthouseWorld) -> list[str]:
    case = world.facts["case"]
    child = world.facts["child"].label
    charm = world.facts["charm"].label
    return [
        f"Write a child-friendly magic whodunit in which {child} investigates why the {charm} vanished while a cyclone approaches.",
        f"Tell a complete lighthouse-fair mystery with suspects, a concrete clue, spoken dialogue, safe teamwork, and a changed ending.",
        f"Use this mystery problem: {case['object']}. Reveal the truth through evidence rather than accusation.",
    ]


def story_qa(world: LighthouseWorld) -> list[QAItem]:
    case = world.facts["case"]
    child = world.facts["child"].label
    keeper = world.facts["keeper"].label
    suspect = world.facts["suspect"].label
    charm = world.facts["charm"].label
    return [
        QAItem(
            f"Why did {child} first suspect {suspect}?",
            f"{child} first suspected {suspect} because {case['suspect']}.",
        ),
        QAItem(
            f"What clue helped {child} solve the mystery?",
            f"The clue was that {case['clue']}. It pointed toward the cyclone's real effect.",
        ),
        QAItem(
            f"How did {child} and {keeper} recover the {charm}?",
            f"{child} {case['action']}. Then {keeper} {case['help']}.",
        ),
        QAItem(
            "What was the real cause of the problem?",
            f"The real cause was that {case['truth']}.",
        ),
        QAItem(
            f"What did {child} learn?",
            f"{child} learned that {case['lesson']}",
        ),
    ]


def world_knowledge_qa(world: LighthouseWorld) -> list[QAItem]:
    return [
        QAItem(
            "What is a cyclone?",
            "A cyclone is a large spinning storm with strong winds and often heavy rain.",
        ),
        QAItem(
            "What is magic in a story?",
            "Magic in a story is an imaginary power that can make unusual things happen.",
        ),
        QAItem(
            "Why should people stay safe during a strong storm?",
            "People should stay indoors or follow trusted adults because strong wind, rain, and lightning can hurt them.",
        ),
        QAItem(
            "What is a whodunit?",
            "A whodunit is a mystery story in which characters use clues to discover who caused an event.",
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A magic cyclone whodunit storyworld.")
    parser.add_argument("--name", dest="child_name")
    parser.add_argument("--keeper")
    parser.add_argument("--suspect")
    parser.add_argument("--charm", choices=CHARMS)
    parser.add_argument("--cyclone", choices=CYCLONES)
    parser.add_argument("--seed", type=int, default=None)
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
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    keeper_name = args.keeper or rng.choice(KEEPERS)
    suspect_name = args.suspect or rng.choice(SUSPECTS)
    charm = args.charm or rng.choice(CHARMS)
    cyclone = args.cyclone or rng.choice(CYCLONES)
    if child_name == suspect_name:
        raise StoryError("The investigator and suspect must have different names.")
    return StoryParams(
        child_name=child_name,
        child_type="girl" if child_name in {"Luna", "Iris", "Nia"} else "boy",
        keeper_name=keeper_name,
        suspect_name=suspect_name,
        charm=charm,
        cyclone_name=cyclone,
        scenario_id=rng.randrange(len(CASES)),
        opening_id=rng.randrange(len(OPENINGS)),
        dialogue_id=rng.randrange(len(DIALOGUES)),
        clue_id=rng.randrange(len(CLUE_LEADS)),
        ending_id=rng.randrange(len(ENDINGS)),
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def dump_trace(world: LighthouseWorld) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label}: kind={entity.kind}; "
            f"meters={entity.meters}; memes={entity.memes}; props={entity.props}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    params = StoryParams(
        child_name="Luna",
        child_type="girl",
        keeper_name="Captain Vale",
        suspect_name="Pip the Magician",
        charm="moonstone lantern",
        cyclone_name="Cyclone Orla",
    )
    model = asp.one_model(asp_program(params))
    atoms = {str(atom) for atom in model}
    if not any("fair_solution" in atom for atom in atoms):
        print("MISMATCH: ASP did not find the safe fair solution.")
        return 1
    sample = generate(params)
    if not sample.world.facts["resolved"]:
        print("MISMATCH: Python story did not resolve.")
        return 1
    if "cyclone" not in sample.story.lower() or "clue" not in sample.story.lower():
        print("MISMATCH: story lacks required causal evidence.")
        return 1
    print("OK: Python and ASP agree that the magic mystery has a safe solution.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("Luna", "girl", "Captain Vale", "Pip the Magician", "moonstone lantern", "Cyclone Orla", 0, 0, 0, 0, 0),
            StoryParams("Milo", "boy", "Aunt Maris", "Bram the Drummer", "silver compass", "Cyclone Niko", 1, 1, 1, 1, 1),
            StoryParams("Iris", "girl", "Mr. Rowan", "Sela the Kite Maker", "blue star crystal", "Cyclone Vela", 2, 2, 2, 2, 2),
            StoryParams("Theo", "boy", "Captain Vale", "Pip the Magician", "moonstone lantern", "Cyclone Niko", 3, 3, 3, 3, 3),
        ]
        samples = [generate(params) for params in presets]
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            samples.append(generate(resolve_params(args, rng)))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### mystery {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
