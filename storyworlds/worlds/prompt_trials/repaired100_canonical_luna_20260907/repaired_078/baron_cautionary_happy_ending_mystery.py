#!/usr/bin/env python3
"""A child-friendly mystery StoryWorld about a baron who learns careful courage."""

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

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))

from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "Baron and the Bell in the Fog"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    baron_name: str = "Baron Alder"
    companion: str = "Mira"
    object_name: str = "the moonstone key"
    place: str = "the old hill castle"
    weather: str = "a silver fog"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Case:
    name: str
    mission: str
    first_clue: str
    false_lead: str
    danger: str
    question: str
    witness: str
    method: str
    resolution: str
    ending: str
    lesson: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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


CASES = [
    Case(
        "the vanished bell",
        "find the little bell that summoned the castle gardeners",
        "a trail of damp ivy led from the bell tower to the locked west door",
        "a black feather lay beside the empty bell hook",
        "the baron nearly followed a narrow stair without checking its loose stones",
        "Why would ivy be wet when no rain had fallen?",
        "a sleepy owl blinked from a beam and dropped a silver thread",
        "Mira compared the thread with the bell rope, then checked the tower window before anyone climbed",
        "the thread matched a torn curtain, and the wind had pulled the bell through the open window onto a safe hay cart",
        "the gardeners rang the recovered bell while warm lanterns glowed along the castle path",
        "A brave detective pauses before stepping into danger.",
    ),
    Case(
        "the missing portrait",
        "discover who moved the smiling portrait from the great hall",
        "a clean rectangle showed where the dusty frame had rested",
        "three muddy footprints pointed toward the banquet room",
        "the baron almost accused the cook before asking whether the prints were real",
        "Why did the footprints stop at the rug?",
        "a mouse had gnawed a corner of the rug and left the marks",
        "Mira lifted the rug edge and followed a faint line of blue paint",
        "the portrait was found behind a curtain, where a painter had moved it to repair the wall",
        "the portrait returned to the hall, and everyone admired its newly bright smile",
        "A clue is not proof until you test it.",
    ),
    Case(
        "the silent fountain",
        "learn why the courtyard fountain stopped singing",
        "round drops of water dotted a path toward the old greenhouse",
        "a shiny coin at the fountain base seemed to promise treasure",
        "the baron reached into a dark drain without a lantern",
        "What could carry water away from the fountain?",
        "a robin tugged a green ribbon caught on a pipe",
        "Mira tied a safe marker, fetched a lantern, and traced the pipe to a bent greenhouse valve",
        "the valve was closed by a fallen branch, and opening it restored the fountain",
        "the fountain sang again as the robin hopped beside the sparkling pool",
        "Curiosity is useful when it travels with caution.",
    ),
    Case(
        "the cold library",
        "solve why a warm reading room had suddenly grown chilly",
        "a row of paper stars pointed toward a high window",
        "a book about dragons lay open on the floor",
        "the baron wanted to climb a tall stack of books to reach the latch",
        "What had made the paper stars turn toward the window?",
        "a draft fluttered one star whenever the wind crossed the roof",
        "Mira used a mirror from the floor to inspect the latch without climbing",
        "the window had been left open by a delivery bird, and closing it warmed the library",
        "the baron read aloud by the fire while the paper stars rested still",
        "A clever question can prevent a risky shortcut.",
    ),
    Case(
        "the secret garden gate",
        "find who had opened the garden gate before dawn",
        "tiny yellow petals formed a line from the gate to the tool shed",
        "a rusty key lay in a puddle",
        "the baron tried the key in the gate and nearly slipped on the wet stones",
        "Why did the petals point away from the garden?",
        "a gardener's basket had spilled while being carried to the shed",
        "Mira dried the key, checked its shape, and asked the gardener about the basket",
        "the gardener had opened the gate to rescue a trapped hedgehog and had forgotten to close it",
        "the gate was mended, and the hedgehog waddled safely beneath the roses",
        "Before blaming someone, ask what helpful reason may be hidden.",
    ),
    Case(
        "the clockwork whisper",
        "discover what made a whisper inside the castle clock",
        "the whisper returned every time the minute hand reached twelve",
        "a hidden note seemed to say, 'Leave now'",
        "the baron wanted to pull the clock apart while its gears were moving",
        "What happened only at the top of the hour?",
        "a loose paper fan trembled behind the clock face",
        "Mira stopped the clock safely, marked the gear position, and asked the keeper for the old repair plan",
        "the fan had been left inside during a repair, and its flutter made the whisper",
        "the clock chimed clearly, and the baron placed the repair plan beside it",
        "When a mystery repeats, observe the pattern before acting.",
    ),
]


BARON_NAMES = ["Baron Alder", "Baron Rowan", "Baron Linden"]
COMPANIONS = ["Mira", "Tomas", "Nell"]
OBJECTS = ["the moonstone key", "the brass compass", "the ruby button"]
PLACES = ["the old hill castle", "the misty riverside manor", "the lantern tower"]
WEATHER = ["a silver fog", "a gentle spring rain", "a blue evening mist"]


def choose_case(params: StoryParams) -> Case:
    seed = params.seed if params.seed is not None else 0
    return CASES[seed % len(CASES)]


def setup_world(params: StoryParams, case: Case) -> World:
    if not params.baron_name.startswith("Baron "):
        raise StoryError("baron_name must begin with 'Baron ' so the story has a clear baron.")
    if not params.companion.strip():
        raise StoryError("companion must not be empty.")
    world = World(params.place)
    baron = world.add(Entity(
        id="baron",
        kind="character",
        type="baron",
        label=params.baron_name,
        meters={"caution": 0.2, "danger": 0.0},
        memes={"curiosity": 1.0, "confidence": 0.4},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="helper",
        label=params.companion,
        meters={"observation": 1.0},
        memes={"patience": 1.0},
    ))
    object_entity = world.add(Entity(
        id="mystery_object",
        kind="thing",
        type="object",
        label=params.object_name,
        owner=baron.id,
        meters={"hidden": 1.0},
    ))
    world.facts.update(
        baron=baron,
        companion=companion,
        object=object_entity,
        case=case,
        weather=params.weather,
        place=params.place,
    )
    return world


def tell(params: StoryParams) -> World:
    case = choose_case(params)
    world = setup_world(params, case)
    baron: Entity = world.facts["baron"]
    companion: Entity = world.facts["companion"]
    pronoun = "he" if baron.label.endswith(("Alder", "Rowan", "Linden")) else "they"

    world.say(
        f"At {world.place}, {baron.label} kept a small mystery room beneath the tallest tower. "
        f"On the morning of {params.weather}, a worried sound or sight brought a new case to his door."
    )
    world.say(
        f"That day, the mystery was {case.name}: {case.mission}. "
        f"{baron.label} carried {world.facts['object'].label}, though it was a clue tool, not a magic answer."
    )
    world.say(f"{case.first_clue.capitalize()}.")
    world.para()

    world.say(
        f"Beside the clue, {case.false_lead}. {baron.label} leaned forward eagerly. "
        f'"I will solve it first!" he said.'
    )
    world.say(
        f'"Wait, {baron.label}," said {companion.label}. "What do we know, and what are we only guessing?"'
    )
    world.say(
        f'"We know the first clue," {baron.label} replied. "But I should not hurry past a warning."'
    )
    world.say(f"For one moment, {pronoun} ignored that warning: {case.danger}.")
    baron.meters["danger"] = 1.0
    baron.memes["hurry"] = 1.0
    world.fired.add(("hurry_caused_risk", case.name))
    world.para()

    world.say(f"{companion.label} pointed to the evidence. " + case.question + " " + case.witness.capitalize() + ".")
    world.say(
        f'"The mystery has a safer next step," said {companion.label}. '
        f'"Let us look, ask, and test before we touch anything dangerous."'
    )
    world.say(
        f'"You are right," said {baron.label}. "I will listen and follow the careful plan." '
        f"Together, they {case.method}."
    )
    baron.meters["caution"] = 1.0
    baron.memes["listening"] = 1.0
    world.fired.add(("evidence_tested", case.name))
    world.para()

    world.say(f"Because they checked the clues instead of trusting the false lead, {case.resolution}.")
    baron.meters["danger"] = 0.0
    baron.meters["mystery_solved"] = 1.0
    baron.memes["courage"] = 1.0
    world.facts["answer"] = case.resolution
    world.say(
        f'{baron.label} smiled. "Caution did not stop our adventure," he said. '
        f'"It helped us finish it safely."'
    )
    world.say(f"By sunset, {case.ending}. {case.lesson}")
    world.fired.add(("happy_ending", case.name))
    return world


def generation_prompts(world: World) -> list[str]:
    case: Case = world.facts["case"]
    baron: Entity = world.facts["baron"]
    return [
        f"Write a child-friendly mystery about {baron.label}, a baron investigating {case.name} at {world.place}.",
        f"Show how a false lead, a useful clue, and careful questioning help solve the mystery about {world.facts['object'].label}.",
        "Include a cautionary turn, spoken back-and-forth dialogue, and a happy ending where caution makes the adventure safer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case: Case = world.facts["case"]
    baron: Entity = world.facts["baron"]
    companion: Entity = world.facts["companion"]
    return [
        QAItem(
            question=f"What mystery did {baron.label} investigate?",
            answer=f"{baron.label} investigated {case.name}: {case.mission}.",
        ),
        QAItem(
            question="What was the cautionary warning in the story?",
            answer=f"The warning was that {case.danger}. The baron learned not to hurry into a risky action.",
        ),
        QAItem(
            question=f"How did {companion.label} help solve the mystery?",
            answer=f"{companion.label} asked a careful question, noticed useful evidence, and helped test the clue safely: {case.method}.",
        ),
        QAItem(
            question="Why was the first lead misleading?",
            answer=f"The first lead was misleading because {case.false_lead}. The characters needed more evidence before deciding what it meant.",
        ),
        QAItem(
            question="How did the story end happily?",
            answer=f"{case.resolution.capitalize()}. Then {case.ending}, so the mystery ended safely and happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or puzzling event that people investigate by observing clues and testing ideas.",
        ),
        QAItem(
            question="Why is caution useful during an investigation?",
            answer="Caution helps investigators pause, avoid danger, and check evidence before making a choice.",
        ),
        QAItem(
            question="What is a baron?",
            answer="A baron is a noble person in a traditional European-style story. In this world, the baron is also a curious detective.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:15} ({entity.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = [
        asp.fact("role", "baron"),
        asp.fact("role", "companion"),
        asp.fact("virtue", "caution"),
        asp.fact("method", "question"),
        asp.fact("method", "test"),
        asp.fact("ending", "happy"),
    ]
    for case in CASES:
        lines.append(asp.fact("case", case.name))
    return "\n".join(lines)


ASP_RULES = r"""
mystery_method :- method(question), method(test).
safe_investigation :- virtue(caution), mystery_method.
happy_resolution :- safe_investigation, ending(happy).
good_story :- role(baron), role(companion), happy_resolution.
#show mystery_method/0.
#show safe_investigation/0.
#show happy_resolution/0.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/0."))
    if not asp.atoms(model, "good_story"):
        print("ASP verification failed: no complete cautious mystery.")
        return 1
    for seed in range(len(CASES) * 2):
        sample = generate(StoryParams(seed=seed))
        if "caution" not in sample.story.lower() or not sample.world.fired:
            print("Python verification failed on generated story.")
            return 1
    print("OK: ASP/Python mystery parity and generated stories verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary baron mystery story world.")
    parser.add_argument("--baron-name", choices=BARON_NAMES, default=None)
    parser.add_argument("--companion", choices=COMPANIONS, default=None)
    parser.add_argument("--object-name", choices=OBJECTS, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
    parser.add_argument("--weather", choices=WEATHER, default=None)
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
    return StoryParams(
        baron_name=args.baron_name or rng.choice(BARON_NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        object_name=args.object_name or rng.choice(OBJECTS),
        place=args.place or rng.choice(PLACES),
        weather=args.weather or rng.choice(WEATHER),
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        baron_name="Baron Alder",
        companion="Mira",
        object_name="the moonstone key",
        place="the old hill castle",
        weather="a silver fog",
        seed=0,
    ),
    StoryParams(
        baron_name="Baron Rowan",
        companion="Tomas",
        object_name="the brass compass",
        place="the misty riverside manor",
        weather="a gentle spring rain",
        seed=13,
    ),
    StoryParams(
        baron_name="Baron Linden",
        companion="Nell",
        object_name="the ruby button",
        place="the lantern tower",
        weather="a blue evening mist",
        seed=27,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show mystery_method/0. "
                "#show safe_investigation/0. "
                "#show happy_resolution/0. "
                "#show good_story/0."
            )
        )
        for predicate in ("mystery_method", "safe_investigation", "happy_resolution", "good_story"):
            print(asp.atoms(model, predicate))
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
        header = ""
        if args.all:
            header = f"### {sample.params.baron_name} / {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
