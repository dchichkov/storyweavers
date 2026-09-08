#!/usr/bin/env python3
"""
A small storyworld about an awkward pirate reconciliation.
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
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass(frozen=True)
class Arc:
    key: str
    object_name: str
    problem: str
    repair: str
    ending: str


ARCS = (
    Arc(
        "map",
        "the treasure map",
        "Captain Luna and First Mate Pip both grabbed the map, and its middle tore with an awkward little rip",
        "Luna admitted she had tugged too hard, while Pip held the pieces together and helped paste them beneath the ship's brass compass",
        "the map showed one path again, and the two pirates sailed by the same bright star",
    ),
    Arc(
        "parrot",
        "the parrot's perch",
        "Luna moved the perch without telling Pip, so the parrot flapped into the soup pot with an awkward squawk",
        "Luna said she should have asked first, and Pip tied the perch safely beside the warm galley window",
        "the parrot settled between them and shared one cracker with each friend",
    ),
    Arc(
        "flag",
        "the red sail flag",
        "Pip hid the red sail flag as a joke, but Luna searched the deck through an awkward, worried silence",
        "Pip returned it and said the joke had gone too far, while Luna explained that the flag helped her steer home",
        "the flag flew from the mast, and both pirates waved beneath it",
    ),
    Arc(
        "barrel",
        "the water barrel",
        "Luna blamed Pip when the water barrel rolled loose, making an awkward crash beside the anchor",
        "Luna listened when Pip explained that a rope knot had slipped, then they tied the barrel down together",
        "the barrel stayed snug, and fresh water waited for every thirsty sailor",
    ),
    Arc(
        "bell",
        "the deck bell",
        "Pip rang the deck bell too early, and Luna gave an awkward scowl before the crew knew what the alarm meant",
        "Pip apologized and Luna showed him the proper signal, so they practiced the bell together",
        "the bell rang clearly, and nobody mistook friendship for a storm",
    ),
)


@dataclass
class StoryParams:
    port: str
    captain_name: str
    mate_name: str
    captain_gender: str = "girl"
    mate_gender: str = "boy"
    seed: Optional[int] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


PORTS = {
    "moonlit_cove": Place("moonlit_cove", "Moonlit Cove", {"sea", "cove"}),
    "whispering_island": Place("whispering_island", "Whispering Island", {"sea", "island"}),
    "coral_harbor": Place("coral_harbor", "Coral Harbor", {"sea", "harbor"}),
}

NAMES = {
    "girl": ["Luna", "Mara", "Pearl", "Ivy", "Tessa"],
    "boy": ["Pip", "Finn", "Jasper", "Theo", "Nico"],
}


def valid_combos() -> list[tuple[str, str]]:
    return [(port, arc.key) for port in PORTS for arc in ARCS]


def tell(params: StoryParams) -> World:
    if params.port not in PORTS:
        raise StoryError(f"Unknown port: {params.port}")
    if params.captain_name == params.mate_name:
        raise StoryError("The captain and mate must have different names.")
    if params.captain_gender not in NAMES or params.mate_gender not in NAMES:
        raise StoryError("Each pirate must have a supported gender.")

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = ARCS[rng.randrange(len(ARCS))]
    world = World(PORTS[params.port])
    captain = world.add(Entity(params.captain_name, "character", "captain", params.captain_name))
    mate = world.add(Entity(params.mate_name, "character", "mate", params.mate_name))
    object_entity = world.add(Entity("ship_object", "thing", "object", arc.object_name))

    captain.memes["pride"] = 1
    mate.memes["hurt"] = 1
    captain.meters["trust"] = 0
    mate.meters["trust"] = 0
    world.facts.update(
        captain=captain,
        mate=mate,
        object=object_entity,
        arc=arc,
        awkward=True,
        reconciled=False,
    )

    world.say(f"At {world.place.label}, Captain {captain.label} sailed the little ship Starling.")
    world.say(f"First Mate {mate.label} trimmed the sails while gulls cried, “Arrr!”")
    world.para()

    world.say(f"{arc.problem}.")
    world.say(f'"This is awkward," said {captain.label}, staring at the deck.')
    world.say(f'"It is awkward," agreed {mate.label}, "but we can mend more than {arc.object_name}."')
    world.para()

    captain.memes["pride"] = 0
    captain.memes["honesty"] = 1
    mate.memes["hurt"] = 0
    captain.meters["trust"] = 1
    mate.meters["trust"] = 1
    world.facts["reconciled"] = True

    world.say(f"Captain {captain.label} took a slow breath and apologized. {arc.repair}.")
    world.say(f'"Friends before treasure," said {mate.label}.')
    world.say(f'"Friends before treasure," said Captain {captain.label}, and they bumped elbows like cheerful pirates.')
    world.para()

    captain.memes["joy"] = 1
    mate.memes["joy"] = 1
    world.say(f"By sunset, {arc.ending}.")
    world.say("The Starling sailed on, with two honest voices sharing the lookout.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a child-friendly Pirate Tale that uses the word "awkward" and ends with reconciliation.',
        f"Tell a pirate story in which {f['captain'].label} and {f['mate'].label} repair a friendship after trouble with {f['object'].label}.",
        "Write a gentle sea adventure where an apology changes what two pirate friends do next.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    arc: Arc = f["arc"]  # type: ignore[assignment]
    return [
        QAItem(
            "What made the moment awkward?",
            f"The moment was awkward because {arc.problem.lower()}.",
        ),
        QAItem(
            "How did the pirates reconcile?",
            f"They reconciled when Captain {f['captain'].label} apologized and then {arc.repair.lower()}.",
        ),
        QAItem(
            "What showed that their friendship was repaired?",
            f"By the end, {arc.ending}, and they shared the lookout again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What does reconciliation mean?",
            "Reconciliation means making peace after a disagreement and finding a way to be friends or work together again.",
        ),
        QAItem(
            "Why can an apology help?",
            "An apology can show that someone understands the hurt they caused and wants to make a better choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"  {entity.id}: meters={meters} memes={memes}")
    lines.append(f"  place: {world.place.id}")
    lines.append(f"  reconciled: {world.facts.get('reconciled')}")
    return "\n".join(lines)


ASP_RULES = r"""
awkward :- trouble(object).
heard(apology) :- awkward, speaks(captain), speaks(mate).
reconciled :- heard(apology), repairs(object), trust(captain), trust(mate).
outcome(reconciliation) :- reconciled.
"""


def asp_facts() -> str:
    import asp
    facts = [
        asp.fact("trouble", "object"),
        asp.fact("object", "object"),
        asp.fact("captain", "captain"),
        asp.fact("mate", "mate"),
        asp.fact("speaks", "captain"),
        asp.fact("speaks", "mate"),
        asp.fact("repairs", "object"),
        asp.fact("trust", "captain"),
        asp.fact("trust", "mate"),
    ]
    return "\n".join(facts)


def asp_program(show: str = "#show outcome/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    return asp.atoms(model, "outcome")


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program())
        if ("reconciliation",) not in asp.atoms(model, "outcome"):
            print("ASP parity failed: reconciliation was not derived.")
            return 1
        params = StoryParams("moonlit_cove", "Luna", "Pip", seed=3)
        sample = generate(params)
        if "awkward" not in sample.story.lower() or not sample.world.facts["reconciled"]:
            print("Python story verification failed.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


CURATED = [
    StoryParams("moonlit_cove", "Luna", "Pip", seed=0),
    StoryParams("whispering_island", "Mara", "Finn", seed=1),
    StoryParams("coral_harbor", "Pearl", "Jasper", seed=2),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if captain_gender == "girl" else "girl")
    captain = args.captain or rng.choice(NAMES[captain_gender])
    choices = [name for name in NAMES[mate_gender] if name != captain]
    mate = args.mate or rng.choice(choices)
    return StoryParams(
        port=args.port or rng.choice(list(PORTS)),
        captain_name=captain,
        mate_name=mate,
        captain_gender=captain_gender,
        mate_gender=mate_gender,
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


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="An awkward pirate reconciliation storyworld.")
    parser.add_argument("--port", choices=PORTS)
    parser.add_argument("--captain")
    parser.add_argument("--mate")
    parser.add_argument("--captain-gender", choices=["girl", "boy"])
    parser.add_argument("--mate-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
