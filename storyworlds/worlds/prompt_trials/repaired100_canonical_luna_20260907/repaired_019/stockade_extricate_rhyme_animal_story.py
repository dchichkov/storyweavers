#!/usr/bin/env python3
"""
A standalone animal storyworld about a stockade, a trapped friend, and a
rhyming plan to extricate them.

The world is small and causal: an animal becomes stuck inside a wooden
stockade, a friend listens to the trouble, and a rhyme helps the animals
remember the careful sequence that opens the gate.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE)))))
sys.path.insert(0, os.path.join(ROOT, "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Place:
    key: str
    name: str
    detail: str


@dataclass
class Animal:
    name: str
    kind: str
    trait: str
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Stockade:
    material: str = "rough pine"
    gate: str = "wooden gate"
    closed: bool = True
    latch_stuck: bool = True
    captive_inside: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    kind: str
    trait: str
    place: str
    helper_kind: str
    seed: Optional[int] = None


PLACES = {
    "meadow": Place("meadow", "the meadow", "where clover nodded under the morning sun"),
    "orchard": Place("orchard", "the orchard", "where apples hung above the green grass"),
    "marsh": Place("marsh", "the marsh edge", "where reeds whispered beside the muddy path"),
    "hill": Place("hill", "the hill pasture", "where the wind ran freely through the grass"),
}

KINDS = ["rabbit", "fox", "badger", "goat", "squirrel", "otter"]
TRAITS = ["clever", "patient", "kind", "brave", "cheerful"]
HELPERS = ["mouse", "crow", "beaver", "hedgehog", "sparrow"]

NAMES = {
    "rabbit": ["Luna", "Tilly", "Pip"],
    "fox": ["Rin", "Mira", "Fenn"],
    "badger": ["Bram", "Nora", "Moss"],
    "goat": ["Pella", "Biscuit", "Tansy"],
    "squirrel": ["Clover", "Nim", "Acorn"],
    "otter": ["Ollie", "Wren", "Pebble"],
}

HELPER_NAMES = {
    "mouse": ["Milo", "Midge", "Nell"],
    "crow": ["Cora", "Jet", "Sable"],
    "beaver": ["Bea", "Bruno", "Twig"],
    "hedgehog": ["Puck", "Poppy", "Bramble"],
    "sparrow": ["Skye", "Pip", "Dart"],
}


@dataclass(frozen=True)
class Trouble:
    sound: str
    symptom: str
    cause: str
    clue: str
    safe_action: str
    result: str
    image: str
    rhyme: str


TROUBLES = [
    Trouble(
        sound="clack-clack",
        symptom="one hind hoof was caught between two low rails",
        cause="a loose rail had slid inward after the rain",
        clue="the lower rail moved whenever Luna pressed her hoof against it",
        safe_action="slid a smooth branch beneath the rail and lifted it just enough",
        result="the rail rose without pinching the hoof",
        image="Luna bounded into the clover while the loose rail rested safely in its place",
        rhyme="Lift the rail, leave room to spare; free the hoof with patient care.",
    ),
    Trouble(
        sound="scrape-scrape",
        symptom="a vine had looped around the gate hinge and trapped the latch",
        cause="a climbing vine had tightened around the hinge",
        clue="green leaves trembled each time the gate was nudged",
        safe_action="cut the vine one loop at a time with a sharp reed knife",
        result="the hinge turned and the latch sprang free",
        image="the gate opened toward a path bright with fallen apples",
        rhyme="Find the vine, unwind the bind; open slowly, leave none behind.",
    ),
    Trouble(
        sound="tap-tap-tap",
        symptom="a small stone had wedged beneath the gate",
        cause="a round stone had rolled into the gate's bottom track",
        clue="the gate lifted a little but stopped against the hard bump",
        safe_action="used a flat stick to roll the stone out of the track",
        result="the gate swung wide without scraping the ground",
        image="the stone rolled away and the stockade stood quiet behind them",
        rhyme="Roll the stone from gate and ground; make a quiet way around.",
    ),
    Trouble(
        sound="creak-pop",
        symptom="the gate's wooden latch had twisted sideways",
        cause="one latch peg had loosened in its hole",
        clue="the latch lifted when pushed left but jammed when pulled straight",
        safe_action="pushed the latch left, then pressed the loose peg back into place",
        result="the latch lifted cleanly and held the gate open",
        image="the repaired peg gleamed pale against the dark stockade boards",
        rhyme="Push left first, then lift up high; mend the peg and let friends fly.",
    ),
    Trouble(
        sound="rustle-thump",
        symptom="a fallen branch blocked the only narrow opening",
        cause="wind had dropped an apple branch across the gate path",
        clue="the leaves shook whenever the trapped animal tried to step forward",
        safe_action="worked together to roll the branch aside instead of pulling the gate",
        result="the path cleared without bending the fence",
        image="the branch became a bridge over a puddle beside the stockade",
        rhyme="Roll the branch, clear the way; help each other, then away.",
    ),
    Trouble(
        sound="ring-ring",
        symptom="a bell rope had wrapped around the gate post",
        cause="the warning rope had wound tightly around the post",
        clue="the bell rang only when the rope was pulled upward",
        safe_action="unwound the rope from the post while the captive held it slack",
        result="the rope fell free and the gate could open",
        image="the little bell rang once for freedom and then rested in the sun",
        rhyme="Keep it slack, unwind the track; freedom comes when rope comes back.",
    ),
]


OPENINGS = [
    "At dawn, the animals shared the meadow as kindly neighbors.",
    "Near the orchard, every animal knew which paths were safe and which gates were old.",
    "Along the marsh edge, the animals helped one another whenever the reeds grew thick.",
    "In the hill pasture, even the smallest sound could carry a long way on the wind.",
]

LESSONS = [
    "A puzzle is easier when friends listen before they pull.",
    "Careful steps can open doors that strong pushes only tighten.",
    "A rhyme is useful when it helps kind hearts remember what to do.",
    "The best rescue leaves both the friend and the fence unharmed.",
]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.hero: Optional[Animal] = None
        self.helper: Optional[Animal] = None
        self.stockade = Stockade()
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.stockade.meters = {"distance_to_freedom": 1.0, "gate_tension": 1.0}
        self.stockade.memes = {"worry": 0.0, "hope": 0.0, "trust": 0.0}

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def hear_trouble(world: World) -> None:
    if "hear" in world.fired:
        return
    world.fired.add("hear")
    trouble = world.facts["trouble"]
    world.stockade.memes["worry"] = 1.0
    world.say(
        f"Then {world.helper.name} heard {trouble.sound} from the stockade. "
        f"It sounded like a tiny drum asking for help."
    )


def exchange_words(world: World) -> None:
    if "exchange" in world.fired:
        return
    world.fired.add("exchange")
    hero = world.hero
    helper = world.helper
    trouble = world.facts["trouble"]
    world.say(
        f'"Are you hurt?" called {helper.name}. '
        f'"Only frightened," answered {hero.name}. '
        f'"Tell me what moves." '
        f'"The lower rail moves when my hoof does."'
    )
    world.say(f"{helper.name} repeated the rhyme: “{trouble.rhyme}”")


def inspect(world: World) -> None:
    if "inspect" in world.fired:
        return
    world.fired.add("inspect")
    trouble = world.facts["trouble"]
    world.say(
        f"Instead of tugging at the gate, {world.helper.name} watched closely. "
        f"{trouble.clue.capitalize()}. That showed the cause: {trouble.cause}."
    )
    world.facts["cause_found"] = True


def extricate(world: World) -> None:
    if "extricate" in world.fired:
        return
    if not world.facts.get("cause_found"):
        raise StoryError("The animals must find the cause before they extricate the captive.")
    world.fired.add("extricate")
    trouble = world.facts["trouble"]
    world.say(f"Together, they followed the rhyme. {trouble.safe_action}.")
    world.say(
        f"{trouble.result.capitalize()}. {world.hero.name} stepped out, "
        f"and the stockade stopped groaning."
    )
    world.stockade.closed = False
    world.stockade.latch_stuck = False
    world.stockade.captive_inside = False
    world.stockade.meters["distance_to_freedom"] = 0.0
    world.stockade.meters["gate_tension"] = 0.0
    world.stockade.memes["worry"] = 0.0
    world.stockade.memes["hope"] = 1.0
    world.stockade.memes["trust"] = 1.0


def conclude(world: World) -> None:
    if "conclude" in world.fired:
        return
    world.fired.add("conclude")
    trouble = world.facts["trouble"]
    world.say(
        f"{trouble.image.capitalize()}. {world.hero.name} hugged {world.helper.name} "
        f"and said, “Your rhyme helped us remember every careful step.” "
        f"{world.facts['lesson']}"
    )


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.kind not in KINDS:
        raise StoryError(f"Unknown animal kind: {params.kind}")
    if params.helper_kind not in HELPERS:
        raise StoryError(f"Unknown helper kind: {params.helper_kind}")
    if params.kind == params.helper_kind:
        raise StoryError("The trapped animal and helper must be different kinds.")

    place = PLACES[params.place]
    world = World(place)
    world.hero = Animal(params.name, params.kind, params.trait)
    helper_name = HELPER_NAMES[params.helper_kind][
        (params.seed or 0) % len(HELPER_NAMES[params.helper_kind])
    ]
    world.helper = Animal(helper_name, params.helper_kind, "helpful")

    choice = params.seed
    if choice is None:
        key = "|".join([params.name, params.kind, params.trait, params.place, params.helper_kind])
        choice = sum((i + 1) * ord(c) for i, c in enumerate(key))

    world.facts["trouble"] = TROUBLES[choice % len(TROUBLES)]
    world.facts["opening"] = OPENINGS[(choice // len(TROUBLES)) % len(OPENINGS)]
    world.facts["lesson"] = LESSONS[(choice // (len(TROUBLES) * len(OPENINGS))) % len(LESSONS)]
    return world


def tell_story(world: World) -> None:
    hero = world.hero
    helper = world.helper
    trouble = world.facts["trouble"]
    place = world.place

    world.say(
        f"{world.facts['opening']} {hero.name}, a {hero.trait} little {hero.kind}, "
        f"lived near {place.name}, {place.detail}."
    )
    world.say(
        f"One morning, {hero.name} stepped into an old stockade to gather "
        f"clover and found the wooden gate shut behind them."
    )

    world.para()
    world.say(f"{hero.name} tried to move, but {trouble.symptom}.")
    hear_trouble(world)
    world.say(
        f"{helper.name}, a {helper.kind}, hurried over and peered through the rails."
    )
    exchange_words(world)

    world.para()
    inspect(world)
    extricate(world)

    world.para()
    conclude(world)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        problem=trouble.symptom,
        cause=trouble.cause,
        rhyme=trouble.rhyme,
        action=trouble.safe_action,
        result=trouble.result,
        ending=trouble.image,
        resolved=not world.stockade.captive_inside,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    helper = world.helper
    trouble = world.facts["trouble"]
    return [
        f"Write an animal story about {hero.name} trapped in a stockade while {helper.name} helps extricate them.",
        f"Use the rhyme “{trouble.rhyme}” as a memory tool in a child-friendly rescue tale.",
        f"Tell how a {hero.kind} and a {helper.kind} solve a stockade problem without using force.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"Why was {hero.name} unable to leave the stockade?",
            answer=f"{hero.name} could not leave because {f['problem']}.",
        ),
        QAItem(
            question=f"What did {helper.name} learn by listening carefully?",
            answer=f"{helper.name} learned that {f['cause']}. The moving part revealed where the trouble was.",
        ),
        QAItem(
            question="What rhyme helped the animals remember the rescue plan?",
            answer=f'The rhyme was “{f["rhyme"]}” It reminded them to work slowly and safely.',
        ),
        QAItem(
            question=f"How did the animals extricate {hero.name}?",
            answer=f"{helper.name} and {hero.name} {f['action']}. {f['result'].capitalize()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stockade?",
            answer="A stockade is an enclosed place surrounded by a strong fence made from upright posts or rails.",
        ),
        QAItem(
            question="What does extricate mean?",
            answer="Extricate means to carefully free someone or something from a difficult or trapped position.",
        ),
        QAItem(
            question="Why can a rhyme help during a task?",
            answer="A rhyme can make steps easier to remember, especially when people need to work calmly and in order.",
        ),
        QAItem(
            question="Why should rescuers inspect a problem before pulling hard?",
            answer="Inspecting first can reveal the real cause and prevent the trapped friend or the surrounding object from being hurt.",
        ),
    ]


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


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place={world.place.name}",
            f"hero={world.hero.name} ({world.hero.kind}, {world.hero.trait})",
            f"helper={world.helper.name} ({world.helper.kind})",
            f"problem={world.facts.get('problem')}",
            f"cause={world.facts.get('cause')}",
            f"rhyme={world.facts.get('rhyme')}",
            f"stockade.closed={world.stockade.closed}",
            f"stockade.latch_stuck={world.stockade.latch_stuck}",
            f"stockade.captive_inside={world.stockade.captive_inside}",
            f"stockade.meters={world.stockade.meters}",
            f"stockade.memes={world.stockade.memes}",
            f"fired={sorted(world.fired)}",
        ]
    )


ASP_RULES = r"""
place(P) :- place_name(P).
animal(A) :- animal_name(A).
helper(H) :- helper_name(H).
different(A,H) :- animal(A), helper(H), A != H.
valid(P,A,H) :- place(P), animal(A), helper(H), different(A,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in PLACES:
        lines.append(asp.fact("place_name", place))
    for kind in KINDS:
        lines.append(asp.fact("animal_name", kind))
    for kind in HELPERS:
        lines.append(asp.fact("helper_name", kind))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, animal, helper)
        for place in PLACES
        for animal in KINDS
        for helper in HELPERS
        if animal != helper
    ]


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP validity gates.")
        print("Only Python:", sorted(py - cl))
        print("Only ASP:", sorted(cl - py))
        return 1

    for seed in range(8):
        params = StoryParams(
            name="Luna",
            kind=KINDS[seed % len(KINDS)],
            trait=TRAITS[seed % len(TRAITS)],
            place=list(PLACES)[seed % len(PLACES)],
            helper_kind=HELPERS[seed % len(HELPERS)],
            seed=seed,
        )
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("Generated story failed to resolve.")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combinations), and generated stories resolve.")
    return 0


@dataclass
class _Args:
    place: Optional[str] = None
    kind: Optional[str] = None
    trait: Optional[str] = None
    helper: Optional[str] = None
    name: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False


CURATED = [
    StoryParams("Luna", "rabbit", "clever", "meadow", "mouse"),
    StoryParams("Bram", "badger", "patient", "orchard", "crow"),
    StoryParams("Pella", "goat", "brave", "hill", "beaver"),
    StoryParams("Clover", "squirrel", "cheerful", "marsh", "hedgehog"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="An animal story about a stockade, a rhyme, and a careful rescue.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--kind", choices=KINDS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    kind = args.kind or rng.choice(KINDS)
    helper_choices = [h for h in HELPERS if h != kind]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(
        name=args.name or rng.choice(NAMES[kind]),
        kind=kind,
        trait=args.trait or rng.choice(TRAITS),
        place=args.place or rng.choice(list(PLACES)),
        helper_kind=helper,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:\n")
        for place, kind, helper in combos:
            print(f"  {place:10} {kind:10} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, params in enumerate(CURATED):
            params.seed = base_seed + i
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        for i in range(max(args.n, 0) * 100 + 50):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.kind} and {p.helper_kind} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
