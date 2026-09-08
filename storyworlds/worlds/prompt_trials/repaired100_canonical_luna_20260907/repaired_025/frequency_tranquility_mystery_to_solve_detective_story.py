#!/usr/bin/env python3
"""
A compact detective storyworld about frequency, tranquility, and a mystery to solve.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT) and not os.path.exists(os.path.join(ROOT, "results.py")):
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""


@dataclass
class Setting:
    name: str
    affordances: set[str]


@dataclass(frozen=True)
class Case:
    id: str
    opening: str
    disturbance: str
    clue: str
    false_lead: str
    method: str
    reveal: str
    repair: str
    ending: str


@dataclass
class StoryParams:
    detective: str
    companion: str
    case: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.events: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.events.append(text)

    def render(self) -> str:
        return "\n\n".join(self.events)


SETTING = Setting(
    name="the quiet clock tower",
    affordances={"listen", "compare_frequency", "inspect", "restore_tranquility"},
)

DETECTIVES = ["Luna", "Milo", "Nia", "Theo", "Pia"]
COMPANIONS = ["Ravi", "Suri", "Bea", "Owen", "Kit"]

CASES = {
    "bell": Case(
        id="bell",
        opening="Detective Luna arrived at the quiet clock tower just before dawn.",
        disturbance="The tower's morning bell had stopped, yet a soft tapping returned every seventh minute.",
        clue="A dust mark beside the bell rope showed seven fresh arcs, while the clock face showed eight.",
        false_lead="At first, the loose window latch seemed guilty because it clicked in the wind.",
        method="Luna recorded the sound's frequency and compared it with the swinging pendulum.",
        reveal="The tapping came from a small brass gear rubbing against a bent peg inside the clock.",
        repair="Luna straightened the peg, and the gear turned with the pendulum again.",
        ending="When the bell rang at sunrise, the tower settled into deep tranquility, and the pigeons lifted their heads together.",
    ),
    "fountain": Case(
        id="fountain",
        opening="Detective Luna visited the moonlit garden where everyone loved the fountain's tranquility.",
        disturbance="The fountain now hummed at a sharp frequency, and the sleeping flowers folded their petals.",
        clue="The hum grew louder near the stone basin but vanished beside the ivy wall.",
        false_lead="A hidden cricket looked suspicious because its chirps echoed under the basin.",
        method="Luna tapped three stones and counted which vibration matched the hum.",
        reveal="A pebble had slipped into the fountain pump and was striking its little wheel.",
        repair="Luna lifted out the pebble and wrapped the pump in a strip of soft moss.",
        ending="Water whispered once more, the flowers opened, and tranquility returned to every path.",
    ),
    "library": Case(
        id="library",
        opening="Detective Luna entered the old library, where the shelves usually rested in perfect tranquility.",
        disturbance="One shelf whispered at a high frequency whenever the librarian turned off the lamp.",
        clue="The whisper stopped when a book about birds was moved but returned when the book was replaced.",
        false_lead="A mouse behind the wall seemed responsible because its tiny footsteps came at the same time.",
        method="Luna compared the whisper with the book's loose brass clasp.",
        reveal="The clasp was vibrating against the shelf whenever the room became quiet.",
        repair="Luna tied the clasp with blue thread and placed a felt pad beneath the book.",
        ending="The library became tranquil again, and the mystery rested quietly between the shelves.",
    ),
    "harbor": Case(
        id="harbor",
        opening="Detective Luna walked to the harbor before the first boats left the pier.",
        disturbance="A warning buoy rang at an odd frequency even though the sea was calm.",
        clue="Its ringing matched the rhythm of a rope knocking against a nearby post.",
        false_lead="A gull seemed to be causing the trouble because it cried whenever the bell rang.",
        method="Luna watched the rope's swing and measured its timing against the buoy.",
        reveal="A knot had loosened, letting the rope strike the post again and again.",
        repair="Luna tightened the knot and tucked the rope beneath a leather guard.",
        ending="The harbor grew tranquil, and the buoy gave one clear note to welcome the boats.",
    ),
    "greenhouse": Case(
        id="greenhouse",
        opening="Detective Luna entered the glass greenhouse, where warm leaves usually breathed in tranquility.",
        disturbance="A thin whistle rose at a changing frequency whenever the misting pipes opened.",
        clue="The whistle became lower when Luna covered one tiny vent with her hand.",
        false_lead="A singing bird in the rafters drew blame because it knew many different notes.",
        method="Luna followed the changing frequency from vent to vent.",
        reveal="A leaf had wedged against a cracked pipe vent and was fluttering like a little flag.",
        repair="Luna removed the leaf and sealed the crack with a waxed band.",
        ending="The mist fell softly, the plants stood still, and tranquility filled the greenhouse.",
    ),
}

DIALOGUES = [
    ('"A mystery leaves a pattern," said {detective}.', '"Then let us listen before we guess," replied {companion}.'),
    ('"The quiet is part of the evidence," whispered {companion}.', '"Yes," said {detective}, "so every sound must earn our trust."'),
    ('"Could the obvious clue be misleading us?" asked {companion}.', '"It could," answered {detective}. "We will compare it with the frequency."'),
    ('"What changed when the disturbance began?" asked {detective}.', '"Only the rhythm," said {companion}. "That may be our way in."'),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Frequency and tranquility detective storyworld.")
    parser.add_argument("--detective", choices=DETECTIVES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--case", choices=sorted(CASES))
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
    detective = args.detective or rng.choice(DETECTIVES)
    companion = args.companion or rng.choice([n for n in COMPANIONS if n != detective])
    case = args.case or rng.choice(sorted(CASES))
    return StoryParams(detective=detective, companion=companion, case=case)


def _article(word: str) -> str:
    return "an" if word[0].lower() in "aeiou" else "a"


def tell(params: StoryParams) -> World:
    if params.case not in CASES:
        raise StoryError(f"Unknown detective case: {params.case}")
    case = CASES[params.case]
    world = World(SETTING)
    detective = world.add(Entity(
        params.detective, "character", "detective", params.detective,
        meters={"observation": 0.0, "frequency_skill": 0.0},
        memes={"curiosity": 1.0, "confidence": 0.0},
        location=SETTING.name,
    ))
    companion = world.add(Entity(
        params.companion, "character", "assistant", params.companion,
        meters={"listening": 0.0},
        memes={"patience": 1.0},
        location=SETTING.name,
    ))
    disturbance = world.add(Entity(
        "disturbance", "event", "sound", "the strange sound",
        meters={"frequency": 0.0, "regularity": 0.0},
        memes={"unexplained": 1.0},
        location=SETTING.name,
    ))
    world.facts.update(case=case, detective=detective, companion=companion, disturbance=disturbance)

    world.say(case.opening.replace("Detective Luna", f"Detective {params.detective}"))
    world.say(case.disturbance)
    world.say(f'{params.companion} was waiting beside {params.detective} with a notebook.')
    dialogue = DIALOGUES[(params.seed or 0) % len(DIALOGUES)]
    world.say(dialogue[0].format(detective=params.detective, companion=params.companion))
    world.say(case.false_lead)
    world.say(f"{params.detective} did not accuse anyone. Instead, {params.detective} studied the clue: {case.clue}")
    world.say(dialogue[1].format(detective=params.detective, companion=params.companion))
    companion.meters["listening"] = 1.0
    detective.meters["observation"] = 1.0
    detective.meters["frequency_skill"] = 1.0
    disturbance.meters["frequency"] = 1.0
    disturbance.meters["regularity"] = 1.0
    world.say(f"{params.detective} {case.method.lower()}")
    world.say(f"The careful test ruled out the false lead. {case.reveal}")
    world.say(case.repair)
    disturbance.memes["unexplained"] = 0.0
    detective.memes["confidence"] = 1.0
    world.fired.update({"clue_found", "false_lead_rejected", "mystery_solved", "tranquility_restored"})
    world.say(case.ending)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    case: Case = world.facts["case"]  # type: ignore[assignment]
    detective: Entity = world.facts["detective"]  # type: ignore[assignment]
    companion: Entity = world.facts["companion"]  # type: ignore[assignment]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a Detective Story in which {detective.id} solves the {case.id} mystery by studying frequency.",
            f"Tell a Mystery to Solve where {companion.id} helps {detective.id} protect tranquility.",
            f"Write a child-friendly detective story ending with this image: {case.ending}",
        ],
        story_qa=[
            QAItem(
                f"What disturbance began the mystery for {detective.id}?",
                case.disturbance,
            ),
            QAItem(
                f"What clue helped {detective.id} investigate?",
                case.clue,
            ),
            QAItem(
                f"What false lead did {detective.id} reject?",
                case.false_lead,
            ),
            QAItem(
                f"How did {detective.id} use frequency to solve the case?",
                case.method,
            ),
            QAItem(
                "What caused the strange sound?",
                case.reveal,
            ),
            QAItem(
                "How was tranquility restored?",
                case.repair + " " + case.ending,
            ),
        ],
        world_qa=[
            QAItem(
                "What is frequency?",
                "Frequency is how often a repeated sound or motion happens during a certain amount of time.",
            ),
            QAItem(
                "What does tranquility mean?",
                "Tranquility means a calm, peaceful feeling with little disturbance.",
            ),
            QAItem(
                "What is a mystery to solve?",
                "A mystery to solve is a question or puzzling event that requires clues, careful thinking, and a reasonable explanation.",
            ),
            QAItem(
                "What does a detective do?",
                "A detective observes clues, tests ideas, and uses evidence to discover what happened.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} type={entity.type:10} location={entity.location:22} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid_case(C) :- case(C), has_frequency(C), restores_tranquility(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for case_id, case in CASES.items():
        lines.append(asp.fact("case", case_id))
        if case.method and case.repair:
            lines.append(asp.fact("has_frequency", case_id))
        if case.ending:
            lines.append(asp.fact("restores_tranquility", case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_case/1."))
    actual = set(asp.atoms(model, "valid_case"))
    expected = {(case_id,) for case_id in CASES}
    if actual == expected:
        print(f"OK: clingo gate matches Python gate ({len(expected)} cases).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in clingo:", sorted(actual - expected))
    print("only in Python:", sorted(expected - actual))
    return 1


def build_story_from_args(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    seen = set()
    for index in range(max(args.n * 20, 20)):
        if len(samples) >= args.n:
            break
        rng = random.Random(base_seed + index)
        params = resolve_params(args, rng)
        params.seed = base_seed + index
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


CURATED = [
    StoryParams("Luna", "Ravi", "bell", 0),
    StoryParams("Milo", "Suri", "fountain", 1),
    StoryParams("Nia", "Bea", "library", 2),
    StoryParams("Theo", "Owen", "harbor", 3),
    StoryParams("Pia", "Kit", "greenhouse", 4),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_case/1."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_case/1."))
        cases = sorted(asp.atoms(model, "valid_case"))
        print(f"{len(cases)} valid mystery cases.")
        for case in cases:
            print(case[0])
        return
    samples = [generate(p) for p in CURATED] if args.all else build_story_from_args(args)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return
    for index, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {index + 1}" if len(samples) > 1 else "")
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
