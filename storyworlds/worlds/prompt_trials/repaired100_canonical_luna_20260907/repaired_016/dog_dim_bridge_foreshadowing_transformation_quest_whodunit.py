#!/usr/bin/env python3
"""
A child-friendly whodunit about a dim dog, a bridge, and a quest that transforms
a worried pup into a brave clue-finder.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next((p for p in HERE.parents if (p / "results.py").is_file()), HERE.parent)
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    location: str = "Moonbeam Bridge"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    dialogue_turns: list[tuple[str, str]] = field(default_factory=list)

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
class Case:
    object_name: str
    owner: str
    clue: str
    false_clue: str
    hidden_cause: str
    search: str
    solution: str
    transformation: str
    ending: str


@dataclass
class StoryParams:
    dog_name: str
    child_name: str
    keeper_name: str
    seed: Optional[int] = None


DOG_NAMES = ["Dim", "Luna", "Moss", "Pip", "Comet"]
CHILD_NAMES = ["Maya", "Theo", "Nia", "Owen", "Zara"]
KEEPER_NAMES = ["Ada", "June", "Milo", "Ravi", "Tess"]

CASES = [
    Case(
        object_name="the silver bridge bell",
        owner="the bridge keeper",
        clue="a line of blue thread caught on the bell rope",
        false_clue="muddy paw marks pointed toward the riverbank",
        hidden_cause="a gust had snapped a kite string around the rope",
        search="followed the blue thread from the bell to a thornbush below the bridge",
        solution="found the kite string and freed the bell without blaming anyone",
        transformation="learned to trust careful noticing instead of loud barking",
        ending="the bell rang softly, and the once-dim dog stood bright-eyed beneath the moon",
    ),
    Case(
        object_name="a red picnic lantern",
        owner="the baker",
        clue="three warm drops of wax beside the bridge rail",
        false_clue="a trail of crumbs seemed to lead into the reeds",
        hidden_cause="a rolling cake cart had brushed the lantern and carried it downhill",
        search="tracked the wax drops across the stones to a wheel rut",
        solution="found the lantern under the cart and carried it safely back",
        transformation="turned his fear of dark places into patient courage",
        ending="the red lantern glowed above the bridge while the dog’s shadow looked tall and strong",
    ),
    Case(
        object_name="the mayor's blue ribbon",
        owner="the town mayor",
        clue="a tiny silver button wedged under a bridge plank",
        false_clue="a feather suggested that a crow had stolen the ribbon",
        hidden_cause="the ribbon had caught on a traveling coat and slipped free in the wind",
        search="examined the plank, then followed a row of loose blue fibers",
        solution="found the ribbon hanging from a willow branch on the far side",
        transformation="became a calm helper who asked questions before making guesses",
        ending="the blue ribbon fluttered above the bridge as the dog proudly led the way home",
    ),
    Case(
        object_name="the school music box",
        owner="the music teacher",
        clue="a faint tune came from beneath the bridge steps",
        false_clue="a shiny fish scale made the river look suspicious",
        hidden_cause="the box had slipped into a dry nook when a wagon bumped the railing",
        search="listened between the echoes and found the narrow nook",
        solution="guided the teacher to the music box and kept it dry",
        transformation="changed from a trembling listener into a brave sound-finder",
        ending="the music box played beside the bridge while Luna’s tail tapped the rhythm",
    ),
]

OPENINGS = [
    "At dusk, the village lights blinked on one by one.",
    "The first moon of autumn rose above the quiet river.",
    "A cool wind swept through the village just before supper.",
    "Everyone was gathering near the old bridge for the evening market.",
]

ASP_RULES = r"""
#show danger/1.
#show clue/1.
#show solved/1.
danger(bridge) :- missing(bridge_object).
clue(bridge) :- thread(bridge), careful_search.
solved(bridge) :- danger(bridge), clue(bridge), helper(dog), helper(child).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dog-dim bridge whodunit story world.")
    parser.add_argument("--dog-name", choices=DOG_NAMES)
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--keeper-name", choices=KEEPER_NAMES)
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
    dog = args.dog_name or rng.choice(DOG_NAMES)
    child = args.child_name or rng.choice(CHILD_NAMES)
    keeper = args.keeper_name or rng.choice(KEEPER_NAMES)
    return StoryParams(dog_name=dog, child_name=child, keeper_name=keeper)


def asp_facts(case: Case | None = None) -> str:
    import asp

    return "\n".join(
        [
            asp.fact("missing", "bridge_object"),
            asp.fact("thread", "bridge"),
            asp.fact("careful_search"),
            asp.fact("helper", "dog"),
            asp.fact("helper", "child"),
        ]
    )


def asp_program(show: str = "#show danger/1.\n#show clue/1.\n#show solved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _dialogue(world: World, speaker: Entity, line: str) -> None:
    world.dialogue_turns.append((speaker.name, line))
    world.say(f'{speaker.name} said, "{line}"')


def _setup(params: StoryParams) -> World:
    world = World()
    dog = world.add(Entity("dog", params.dog_name, "dog", memes={"courage": 0.2, "curiosity": 0.8}))
    child = world.add(Entity("child", params.child_name, "child", memes={"patience": 0.8}))
    keeper = world.add(Entity("keeper", params.keeper_name, "bridge keeper", memes={"trust": 0.7}))
    world.facts.update(dog=dog, child=child, keeper=keeper)
    return world


def _choose_case(params: StoryParams) -> Case:
    key = params.seed if params.seed is not None else sum(map(ord, params.dog_name + params.child_name))
    return CASES[key % len(CASES)]


def generate_story(world: World, params: StoryParams) -> None:
    dog: Entity = world.facts["dog"]
    child: Entity = world.facts["child"]
    keeper: Entity = world.facts["keeper"]
    case = _choose_case(params)
    key = params.seed or 0
    opening = OPENINGS[key % len(OPENINGS)]

    world.facts.update(case=case, opening=opening, resolved=False)
    world.meters.update({"bridge_safety": 1.0, "mystery": 1.0})
    world.say(opening)
    world.say(
        f"{dog.name} was a dog-dim pup whose coat looked gray even under bright lamps. "
        f"Still, {dog.name} noticed small things that other dogs missed."
    )
    world.say(
        f"At {world.location}, {keeper.name} discovered that {case.object_name} was gone. "
        f"{keeper.name} had last seen it resting beside the bridge rail."
    )

    world.para()
    _dialogue(world, keeper, f"Who took it? The bridge must stay safe, and the truth must be found.")
    _dialogue(world, child, f"We should inspect the clues before we accuse anyone.")
    world.say(f"{dog.name} sniffed near the railing and found {case.false_clue}.")
    _dialogue(world, dog, "Woof!")
    _dialogue(world, child, f"I think {dog.name} is saying that clue is not the whole story.")
    world.say(f"Then {dog.name} noticed {case.clue}. It was a quiet hint, planted before the mystery began.")
    world.facts["foreshadowing"] = case.clue

    world.para()
    world.say(f"The three investigators began their quest. {dog.name} {case.search}.")
    _dialogue(world, keeper, "Can you really lead us through the dark?")
    _dialogue(world, child, f"Yes. {dog.name} is dim in the dark, but bright when following a true clue.")
    world.say(f"The hidden cause was that {case.hidden_cause}.")
    world.say(f"At last, the team {case.solution}.")
    world.meters["mystery"] = 0.0
    dog.memes["courage"] = 1.0
    dog.memes["confidence"] = 1.0
    world.facts["resolved"] = True
    world.say(
        f"The mystery changed {dog.name}: {case.transformation}. "
        f"{keeper.name} thanked the pup and promised to ask for help before guessing."
    )
    world.say(f"In the ending image, {case.ending}.")


def story_qa(world: World) -> list[QAItem]:
    dog: Entity = world.facts["dog"]
    child: Entity = world.facts["child"]
    keeper: Entity = world.facts["keeper"]
    case: Case = world.facts["case"]
    return [
        QAItem(
            question=f"Why did {keeper.name} need help at the bridge?",
            answer=f"{case.object_name.capitalize()} had gone missing, so {keeper.name} needed help finding it safely.",
        ),
        QAItem(
            question=f"What clue did {dog.name} notice after the misleading clue?",
            answer=f"{dog.name} noticed {case.clue}.",
        ),
        QAItem(
            question=f"How did {dog.name} and {child.name} solve the mystery?",
            answer=f"They {case.search}, learned that {case.hidden_cause}, and then {case.solution}.",
        ),
        QAItem(
            question=f"How was {dog.name} transformed by the quest?",
            answer=f"{dog.name} {case.transformation}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early hint that prepares us for something important later.",
        ),
        QAItem(
            question="Why should a mystery solver check more than one clue?",
            answer="A mystery solver should check more than one clue because the first sign can be misleading.",
        ),
        QAItem(
            question="What makes a bridge safe?",
            answer="A bridge is safer when its boards, rails, and supports are sound and people cross carefully.",
        ),
        QAItem(
            question="Why is careful observation useful?",
            answer="Careful observation helps people notice small facts that can explain a larger problem.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    dog: Entity = world.facts["dog"]
    child: Entity = world.facts["child"]
    case: Case = world.facts["case"]
    return [
        f"Write a child-friendly whodunit about {dog.name}, a dog-dim clue finder, and {child.name} investigating {case.object_name} at Moonbeam Bridge.",
        f"Use foreshadowing: include the clue that {case.clue}, then turn it into a quest and a safe solution.",
        f"Show the transformation of {dog.name} from a worried pup into a brave investigator, ending with {case.ending}.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  location: {world.location}")
    lines.append(f"  meters: {world.meters}")
    lines.append(f"  facts: {world.facts['resolved']=}, {world.facts['foreshadowing']=}")
    for entity in world.entities.values():
        lines.append(f"  {entity.id}: name={entity.name} role={entity.role} memes={entity.memes}")
    lines.append(f"  dialogue turns: {len(world.dialogue_turns)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not params.dog_name or not params.child_name or not params.keeper_name:
        raise StoryError("All character names must be provided.")
    world = _setup(params)
    generate_story(world, params)
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
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Dim", "Maya", "Ada"),
    StoryParams("Luna", "Theo", "June"),
    StoryParams("Moss", "Nia", "Ravi"),
    StoryParams("Pip", "Owen", "Tess"),
]


def verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    danger = asp.atoms(model, "danger")
    clue = asp.atoms(model, "clue")
    solved = asp.atoms(model, "solved")
    if ("bridge",) not in danger or ("bridge",) not in clue or ("bridge",) not in solved:
        print("MISMATCH: ASP bridge reasoning failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve.")
            return 1
        if len(sample.world.dialogue_turns) < 4:
            print("MISMATCH: generated story lacks dialogue.")
            return 1
    print("OK: Python and ASP bridge-whodunit checks passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("danger:", asp.atoms(model, "danger"))
        print("clue:", asp.atoms(model, "clue"))
        print("solved:", asp.atoms(model, "solved"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(1, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
