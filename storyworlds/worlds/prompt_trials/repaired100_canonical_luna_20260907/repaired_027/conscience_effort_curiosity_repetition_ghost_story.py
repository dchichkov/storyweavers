#!/usr/bin/env python3
"""
A gentle ghost story about conscience, effort, curiosity, and repetition.

Luna hears the same small knock each night in an old house. Curiosity leads
her to investigate, conscience keeps her from mocking the unseen visitor, and
patient effort reveals why the ghost has been repeating its lonely signal.
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


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    region: str = ""

    def __post_init__(self) -> None:
        for key in ("darkness", "dust", "stuck", "open", "lit", "heard"):
            self.meters.setdefault(key, 0.0)
        for key in ("curiosity", "fear", "conscience", "hope", "relief", "trust"):
            self.memes.setdefault(key, 0.0)


@dataclass(frozen=True)
class Case:
    name: str
    room: str
    clue: str
    repeated_sound: str
    hidden_problem: str
    effort: str
    answer: str
    ending: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    caretaker: str = "Aunt May"
    house: str = "Willow House"
    case: str = "the blue bedroom"
    curiosity: bool = True
    repetition: bool = True
    conscience: bool = True
    effort: bool = True


NAMES = ["Luna", "Mara", "Nell", "Iris", "Tessa", "Mina"]
CARETAKERS = ["Aunt May", "Uncle Rowan", "Grandma June", "Mr. Bell"]
HOUSES = ["Willow House", "Moonrise Cottage", "Blackbird Hall", "The Old Lantern"]
ROOMS = ["the blue bedroom", "the attic nursery", "the west hallway", "the little library"]

CASES = [
    Case(
        name="the button ghost",
        room="the blue bedroom",
        clue="a pale button lying beneath the wardrobe",
        repeated_sound="tap, tap, pause",
        hidden_problem="a toy drum had rolled behind the wardrobe, and its loose wooden beater struck the wall whenever the night wind shook the floorboards",
        effort="moved the wardrobe inch by inch, swept away the dust, and reached the trapped drum",
        answer="The ghost was not trying to frighten anyone. The repeated tapping came from a lost toy drum, while the pale button belonged to a child's old nightcoat.",
        ending="When the moon rose again, the room was quiet except for Luna's soft goodnight to the friendly house.",
    ),
    Case(
        name="the window ghost",
        room="the attic nursery",
        clue="a ribbon caught on a cracked window latch",
        repeated_sound="scrape, scrape, hush",
        hidden_problem="the ribbon had tangled around the latch, and each draft pulled the window against its loose catch",
        effort="climbed carefully, freed the ribbon, and fastened the latch with a strip of cloth",
        answer="The ghostly scraping was a window asking to be shut, not a spirit asking to be chased away.",
        ending="The next night, moonlight rested peacefully on the nursery floor and the old window made no secret sound.",
    ),
    Case(
        name="the lantern ghost",
        room="the west hallway",
        clue="a silver thread leading beneath a narrow door",
        repeated_sound="flicker, click, flicker",
        hidden_problem="an old pull cord had caught on a floor nail, tugging the hallway lantern on whenever the boards trembled",
        effort="followed the thread, lifted the loose nail, and tied the cord safely out of the walkway",
        answer="The flickering ghost was an untidy cord and an old lantern repeating the house's smallest mistake.",
        ending="The hallway glowed steadily, and Luna felt the house breathe easier around her.",
    ),
    Case(
        name="the music ghost",
        room="the little library",
        clue="a dusty music box with one key still turning",
        repeated_sound="three thin notes, then silence",
        hidden_problem="the music box had been wound too tightly, so its bent tune repeated whenever the shelf shook",
        effort="read the faded label, cleaned the tiny gears, and let the spring unwind slowly",
        answer="The ghostly song came from a music box that needed care, not from a spirit that needed scolding.",
        ending="Afterward, Luna wound the box only once, and its three notes sounded like a smile.",
    ),
    Case(
        name="the stair ghost",
        room="the narrow stairs",
        clue="a wool scarf wedged beneath the third step",
        repeated_sound="thump, thump, still",
        hidden_problem="the scarf had caught on a loose stair board, and the board knocked each time the house settled",
        effort="knelt with a candle, loosened the scarf, and pressed the board flat",
        answer="The stair ghost was a trapped scarf and a restless board repeating the same little complaint.",
        ending="The stairs stopped thumping, and Luna climbed them without fear to tuck herself into bed.",
    ),
]


class World:
    def __init__(self, params: StoryParams, case: Case) -> None:
        self.params = params
        self.case = case
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def make_world(params: StoryParams, case: Case) -> World:
    world = World(params, case)
    luna = world.add(Entity("luna", "character", "child", params.name, region="house"))
    caretaker = world.add(Entity("caretaker", "character", "adult", params.caretaker, region="house"))
    house = world.add(Entity("house", "place", "house", params.house, region="night"))
    room = world.add(Entity("room", "place", "room", case.room, region="upstairs"))
    clue = world.add(Entity("clue", "thing", "clue", case.clue, region=case.room))
    ghost = world.add(Entity("ghost", "character", "ghost", "the quiet visitor", region=case.room))

    luna.memes["curiosity"] = 1.0
    luna.memes["conscience"] = 1.0
    caretaker.memes["trust"] = 1.0
    house.meters["darkness"] = 1.0
    room.meters["stuck"] = 1.0
    clue.meters["heard"] = 0.0
    ghost.memes["hope"] = 1.0
    return world


def tell(params: StoryParams) -> World:
    variant = params.seed if params.seed is not None else sum(
        ord(ch) for ch in f"{params.name}|{params.caretaker}|{params.house}|{params.case}"
    )
    case = CASES[variant % len(CASES)]
    world = make_world(params, case)
    luna = world.get("luna")
    caretaker = world.get("caretaker")
    room = world.get("room")
    clue = world.get("clue")
    ghost = world.get("ghost")

    world.say(
        f"In {params.house}, {params.name} slept near {case.room}, where the walls held old "
        f"shadows and the floorboards remembered every step."
    )
    world.say(
        f"For three nights, {params.name} heard the same sound from upstairs: "
        f"{case.repeated_sound}. It came, stopped, and came again."
    )
    world.para()
    world.say(
        f"On the fourth night, curiosity tugged harder than sleep. {params.name} carried a "
        f"small candle toward {case.room}, while the shadows stretched like long fingers."
    )
    world.say(
        f"{caretaker.label} woke at the bottom of the stairs and called, "
        f"\"{params.name}, wait. Do not tease whatever is making that sound.\""
    )
    world.say(
        f"\"I will not tease it,\" {params.name} answered. \"I only want to understand.\""
    )
    luna.memes["curiosity"] += 1.0
    luna.memes["fear"] += 1.0
    caretaker.memes["trust"] += 1.0
    world.para()

    world.say(
        f"Inside {case.room}, the sound repeated: {case.repeated_sound}. "
        f"The candle trembled, but {params.name}'s conscience spoke more clearly than fear."
    )
    world.say(
        f"Instead of shouting at the dark, {params.name} listened. Near the floor lay {case.clue}."
    )
    clue.meters["heard"] = 1.0
    luna.memes["conscience"] += 1.0
    ghost.memes["hope"] += 1.0
    world.say(
        f"\"Did you leave that clue?\" asked {caretaker.label}. "
        f"\"No,\" said {params.name}, \"but it may tell us what the house is trying to say.\""
    )
    world.say(
        f"Behind the room's stillness, {case.hidden_problem.capitalize()}."
    )
    world.para()

    luna.memes["effort"] = 1.0
    room.meters["stuck"] = 0.0
    room.meters["open"] = 1.0
    world.say(
        f"The work was slow. {params.name} {case.effort}. "
        f"Each small attempt made the candlelight steadier."
    )
    world.say(
        f"The sound came once more: {case.repeated_sound}. "
        f"Then {params.name} made one final careful adjustment, and the repetition stopped."
    )
    room.meters["open"] = 2.0
    ghost.memes["hope"] = 0.0
    ghost.memes["relief"] = 1.0
    luna.memes["fear"] = max(0.0, luna.memes["fear"] - 1.0)
    luna.memes["relief"] = 1.0

    world.para()
    world.say(f"{case.answer}")
    world.say(
        f"{caretaker.label} smiled and said, \"You used curiosity kindly, and effort patiently.\" "
        f"{params.name} nodded. \"A mystery is not an excuse to frighten someone who may need help.\""
    )
    world.say(case.ending)

    world.facts.update(
        luna=luna,
        caretaker=caretaker,
        house=world.get("house"),
        room=room,
        clue=clue,
        ghost=ghost,
        case=case,
        params=params,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    case: Case = world.facts["case"]
    luna: Entity = world.facts["luna"]
    caretaker: Entity = world.facts["caretaker"]
    return [
        QAItem(
            question=f"Who heard the repeated sound in {params.house}?",
            answer=f"{luna.label} heard the same sound in {params.house} and became curious about what was causing it.",
        ),
        QAItem(
            question=f"What did the sound repeat in {case.room}?",
            answer=f"It repeated the pattern {case.repeated_sound}. The repetition made the upstairs room seem haunted.",
        ),
        QAItem(
            question=f"Why did {luna.label} investigate instead of mocking the ghost?",
            answer=f"{luna.label}'s curiosity made the child investigate, while conscience made the child listen kindly instead of teasing or frightening the unseen visitor.",
        ),
        QAItem(
            question=f"What clue helped {luna.label} understand the mystery?",
            answer=f"The clue was {case.clue}. It connected the repeated sound to a physical problem in {case.room}.",
        ),
        QAItem(
            question=f"How did effort solve the ghostly problem?",
            answer=f"{luna.label} {case.effort}. That patient effort stopped the object from repeating its sound.",
        ),
        QAItem(
            question=f"What did {luna.label} learn from the ghost story?",
            answer=f"{luna.label} learned that curiosity should be guided by conscience, and that steady effort can uncover a frightening mystery without hurting anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale about a strange or unseen visitor, often creating mystery, worry, and eventually an explanation or resolution.",
        ),
        QAItem(
            question="What is conscience?",
            answer="Conscience is the inner sense that helps someone notice whether an action is kind, fair, or wrong.",
        ),
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes a person want to learn what is happening and ask careful questions.",
        ),
        QAItem(
            question="Why can repetition seem frightening at night?",
            answer="Repetition can seem frightening at night because the same unexplained sound returns again and again when it is hard to see its cause.",
        ),
        QAItem(
            question="Why is effort useful when solving a mystery?",
            answer="Effort is useful because patient, careful work can reveal clues and fix a problem that cannot be solved by one quick guess.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    case: Case = world.facts["case"]
    return [
        f"Write a gentle ghost story about {params.name}, whose curiosity follows the repeated sound {case.repeated_sound} in {params.house}.",
        f"Tell a child-facing mystery in {case.room} where conscience keeps {params.name} from mocking a ghost and effort reveals that {case.hidden_problem}.",
        f"Write a ghost story showing how {params.name} uses curiosity kindly, repeats careful observations, and solves the haunting with patient effort.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
        lines.append(f"  {entity.id:10} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  resolved: {world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Curiosity notices a repeated mystery.
curious(luna) :- hears_repeated_sound(luna), seeks_clue(luna).

% Conscience prevents cruel treatment of the unseen visitor.
kind_investigation(luna) :- curious(luna), respects_unknown(luna).

% Patient effort opens the stuck cause and ends the repetition.
resolved(luna) :- kind_investigation(luna), makes_effort(luna), stuck_cause.
silent_again(luna) :- resolved(luna), repetition_ended.

#show curious/1.
#show kind_investigation/1.
#show resolved/1.
#show silent_again/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hears_repeated_sound", "luna"),
            asp.fact("seeks_clue", "luna"),
            asp.fact("respects_unknown", "luna"),
            asp.fact("makes_effort", "luna"),
            asp.fact("stuck_cause"),
            asp.fact("repetition_ended"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
    expected = {
        "curious/1",
        "kind_investigation/1",
        "resolved/1",
        "silent_again/1",
    }
    if atoms == expected:
        print("OK: ASP twin matches the conscience-and-effort ghost logic.")
        return 0
    print("MISMATCH:", sorted(atoms), "expected", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about conscience, effort, curiosity, and repetition."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--caretaker", choices=CARETAKERS)
    parser.add_argument("--house", choices=HOUSES)
    parser.add_argument("--case", choices=ROOMS)
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
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        caretaker=args.caretaker or rng.choice(CARETAKERS),
        house=args.house or rng.choice(HOUSES),
        case=args.case or rng.choice(ROOMS),
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


CURATED = [
    StoryParams(name="Luna", caretaker="Aunt May", house="Willow House", case="the blue bedroom"),
    StoryParams(name="Mara", caretaker="Uncle Rowan", house="Moonrise Cottage", case="the attic nursery"),
    StoryParams(name="Iris", caretaker="Grandma June", house="Blackbird Hall", case="the little library"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        print(" ".join(str(symbol) for symbol in asp.one_model(asp_program())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if not samples:
        raise StoryError("No stories could be generated.")

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
