#!/usr/bin/env python3
"""Animal mysteries in which disgust gives way to careful understanding."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    helper: str = "Pip"
    elder: str = "Mara"
    place: str = "the woodland pond"
    mystery: int = 0
    opening: int = 0
    reaction: int = 0
    turn: int = 0
    ending: int = 0


NAMES = ["Luna", "Nala", "Clover", "Mimi", "Daisy", "Poppy"]
HELPERS = ["Pip", "Toby", "Finn", "Roo", "Bram"]
ELDERS = ["Mara", "Olive", "Maple", "Sage"]
PLACES = [
    "the woodland pond",
    "the ferny creek",
    "the old apple orchard",
    "the meadow burrow",
    "the mossy garden",
]

MYSTERIES = [
    {
        "title": "the sour smell by the pond",
        "premise": "Each morning, a sour smell drifted across the pond, and the ducks hurried away from the reeds.",
        "clue": "Luna noticed tiny bubbles rising beside a fallen yellow bucket.",
        "wrong": "The animals guessed that a monster had spoiled the water.",
        "action": "Luna and Pip pulled the bucket free and found wet apples packed beneath it.",
        "cause": "The apples had begun to ferment in the warm water.",
        "result": "Mara rinsed the apples into the compost pile, and the pond smelled fresh again.",
        "lesson": "A disgusting clue can point to a simple cause when we investigate gently.",
        "ending": "By sunset, dragonflies skimmed the clean pond while the ducks paddled in a shining row.",
        "object": "fallen bucket",
    },
    {
        "title": "the green patch on the picnic cloth",
        "premise": "A green patch appeared on the picnic cloth, and everyone wrinkled their noses at it.",
        "clue": "Luna saw that the patch was only beneath a damp basket of forgotten bread.",
        "wrong": "The animals whispered that the cloth must be cursed.",
        "action": "Luna asked Pip to lift the basket while she carried the cloth into the sunlight.",
        "cause": "Moisture had allowed harmless mold to grow on the cloth and bread.",
        "result": "Mara washed the cloth and moved the food into a dry basket.",
        "lesson": "Disgust can warn us to pause, but it should not replace finding the facts.",
        "ending": "The clean cloth dried beneath the breeze, ready for a careful new picnic.",
        "object": "picnic cloth",
    },
    {
        "title": "the fishy scent in the burrow",
        "premise": "A fishy scent curled through the rabbit burrow, and the young rabbits covered their noses.",
        "clue": "Luna followed the smell to a cracked jar tucked behind the root shelf.",
        "wrong": "Everyone feared that a river creature had crept underground.",
        "action": "Luna and Pip opened the window hole, then asked Mara to move the jar with a long stick.",
        "cause": "The jar held old pondweed that had been forgotten in the warm burrow.",
        "result": "Fresh air swept through the tunnel, and the jar went outside for the compost.",
        "lesson": "A mystery becomes smaller when we follow evidence instead of fear.",
        "ending": "The rabbits slept peacefully as cool night air moved through the clean burrow.",
        "object": "cracked jar",
    },
    {
        "title": "the sticky trail to the berry basket",
        "premise": "A sticky trail led from the berry basket, and its sweet-sour smell made the squirrels gasp.",
        "clue": "Luna found one torn berry leaf caught under the basket's loose handle.",
        "wrong": "The squirrels announced that a slimy beast had visited during the night.",
        "action": "Luna and Pip lifted the basket and discovered crushed berries beneath its flat bottom.",
        "cause": "The basket had rested on warm berries and pressed their juice onto the floor.",
        "result": "The squirrels cleaned the trail and saved the uncrushed berries for breakfast.",
        "lesson": "Looking closely can turn a frightening story into a useful explanation.",
        "ending": "The basket stood on a little wooden rack, with bright berries safely above the ground.",
        "object": "berry basket",
    },
    {
        "title": "the strange feathers in the nest",
        "premise": "Strange gray feathers filled a nest, and the young birds felt disgusted by their dusty smell.",
        "clue": "Luna noticed that the feathers were caught around a loose chimney cap.",
        "wrong": "The birds guessed that a giant bird had invaded their home.",
        "action": "Luna held the nest steady while Pip nudged the cap loose and Mara swept away the feathers.",
        "cause": "Wind had blown old feathers down the chimney during the night.",
        "result": "The nest was aired out, and the birds replaced the dusty lining with soft grass.",
        "lesson": "When we find the source, disgust need not become blame.",
        "ending": "The nest smelled of fresh grass as the hatchlings opened their beaks for breakfast.",
        "object": "nest",
    },
    {
        "title": "the wobbling pumpkin near the gate",
        "premise": "A pumpkin wobbled near the gate and leaked a dark, unpleasant liquid.",
        "clue": "Luna spotted a tiny hole where beetles had entered the pumpkin's side.",
        "wrong": "The animals thought the pumpkin was hiding a sleeping spider queen.",
        "action": "Luna kept everyone back while Pip rolled the pumpkin toward the compost heap with a branch.",
        "cause": "The pumpkin had softened and rotted after rain entered through the hole.",
        "result": "Mara cleaned the gate and placed a dry lantern there instead.",
        "lesson": "Safety and curiosity can work together when we inspect a troubling clue carefully.",
        "ending": "The gate gleamed beside the warm lantern, and no one stepped in the leaking patch.",
        "object": "pumpkin",
    },
]

OPENINGS = [
    "At {place}, {name} the young fox loved solving questions that made other animals pause.",
    "One bright morning at {place}, {name} heard a worried whisper near the path.",
    "The animals of {place} were preparing breakfast when {name} noticed something unusual.",
    "Before the sun climbed high over {place}, {name} stopped beside a trail no one could explain.",
    "At {place}, {name} believed every strange smell or sound had a story behind it.",
    "A quiet morning at {place} changed when {name} saw several animals covering their noses.",
]

REACTIONS = [
    "{name} felt disgust rise in her throat, but she did not touch the mystery.",
    "The smell made {name}'s whiskers twitch. She stepped back and took a careful breath.",
    "{name} wrinkled her nose, yet she remembered that a feeling was a warning to investigate, not a final answer.",
    "Everyone looked uncomfortable. {name} said, 'Let us stay safe and find where it began.'",
    "{name} wanted to run away, but her curiosity was stronger than her first disgust.",
]

TURNS = [
    "'The clue is over here,' said {name}. 'I can see what changed.' 'Then I will help from this side,' said {helper}.",
    "'Could the smell have a source?' asked {helper}. {name} nodded. 'We will look without touching it.'",
    "'I thought it was a monster,' admitted {helper}. 'A mystery can feel huge before we check,' said {name}.",
    "{name} called, 'Mara, may we use a stick and keep our paws clean?' 'Good thinking,' Mara replied.",
    "'Disgust tells us to be careful,' said {name}, 'but it does not tell us the whole story.' 'Then let us learn the rest,' said {helper}.",
]

ENDINGS = [
    "The animals agreed that a careful question was stronger than a frightened guess.",
    "From then on, they marked strange things first and told stories about them only after checking.",
    "{name} smiled because the mystery had not needed a brave leap, only patient eyes and kind helpers.",
    "The animals washed their paws, shared the useful lesson, and left the place safer than they found it.",
    "No one laughed at the first disgust. They simply learned how to turn it into careful action.",
]


ASP_RULES = r"""
#show concern/2.
#show lesson/1.

concern(A, M) :- notices(A, M), unpleasant(M).
lesson(L) :- learned(L).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("notices", "fox", "mystery"),
            asp.fact("unpleasant", "mystery"),
            asp.fact("learned", "investigate_before_judging"),
            asp.fact("learned", "disgust_is_a_warning_not_a_verdict"),
        ]
    )


def asp_program(show: str = "#show concern/2.\n#show lesson/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal storyworld about disgust, a mystery to solve, and a lesson learned."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--elder", choices=ELDERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--mystery", type=int, choices=range(len(MYSTERIES)))
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
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    return StoryParams(
        seed=args.seed,
        name=args.name or rng.choice(NAMES),
        helper=args.helper or rng.choice(HELPERS),
        elder=args.elder or rng.choice(ELDERS),
        place=args.place or rng.choice(PLACES),
        mystery=args.mystery if args.mystery is not None else rng.randrange(len(MYSTERIES)),
        opening=rng.randrange(len(OPENINGS)),
        reaction=rng.randrange(len(REACTIONS)),
        turn=rng.randrange(len(TURNS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.name == params.helper:
        raise StoryError("the animal and helper must have different names")
    if not 0 <= params.mystery < len(MYSTERIES):
        raise StoryError("mystery choice is outside the available registry")

    mystery = MYSTERIES[params.mystery]
    world = World()

    animal = world.add(Entity(params.name, "fox", params.name))
    helper = world.add(Entity(params.helper, "squirrel", params.helper))
    elder = world.add(Entity(params.elder, "badger", params.elder))
    animal.meters.update(alertness=0.8, distance_to_clue=1.0)
    animal.memes.update(disgust=0.7, curiosity=0.9, courage=0.8)
    helper.memes.update(helpfulness=0.9)
    elder.memes.update(wisdom=1.0)

    replacements = {
        "name": animal.label,
        "helper": helper.label,
        "elder": elder.label,
        "place": params.place,
    }

    def fill(text: str) -> str:
        return text.format(**replacements)

    world.say(fill(OPENINGS[params.opening]))
    world.say(mystery["premise"])
    world.say(fill(REACTIONS[params.reaction]))
    world.say(mystery["wrong"])
    world.say(fill(TURNS[params.turn]))
    world.say(mystery["clue"])
    world.say(mystery["action"])
    world.say(f"{elder.label} examined the safe distance and explained, '{mystery['cause']}'")
    world.say(mystery["result"])

    animal.memes["disgust"] = 0.1
    animal.memes["understanding"] = 1.0
    animal.memes["curiosity"] = 1.0
    world.facts.update(
        mystery=mystery,
        place=params.place,
        cause=mystery["cause"],
        object=mystery["object"],
        solved=True,
        disgust_present=True,
        lesson=mystery["lesson"],
    )

    world.say(f"Lesson learned: {mystery['lesson']}")
    world.say(fill(ENDINGS[params.ending]))
    world.say(mystery["ending"])

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    mystery = world.facts["mystery"]
    place = world.facts["place"]
    return [
        f"Write a child-friendly animal story at {place} about {mystery['title']}.",
        "Tell a mystery-to-solve story in which disgust becomes a reason to investigate safely.",
        f"End with a clear lesson and a peaceful image involving the {mystery['object']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery = world.facts["mystery"]
    animal = world.entities[next(eid for eid, e in world.entities.items() if e.type == "fox")]
    helper = world.entities[next(eid for eid, e in world.entities.items() if e.type == "squirrel")]
    return [
        QAItem(
            question=f"What mystery did {animal.label} investigate?",
            answer=f"{animal.label} investigated {mystery['title']}. {mystery['premise']}",
        ),
        QAItem(
            question=f"What clue helped {animal.label} solve the mystery?",
            answer=mystery["clue"],
        ),
        QAItem(
            question=f"How did {animal.label} and {helper.label} investigate safely?",
            answer=mystery["action"],
        ),
        QAItem(
            question="What caused the unpleasant problem?",
            answer=mystery["cause"],
        ),
        QAItem(
            question="What lesson did the animals learn?",
            answer=mystery["lesson"],
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is disgust?",
            answer="Disgust is a strong feeling that makes something seem unpleasant and tells us to pause or stay away.",
        ),
        QAItem(
            question="Why should disgust not be treated as the whole truth?",
            answer="Disgust can warn us to be careful, but careful observation is needed to learn what actually caused a problem.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question whose answer is not known yet and can be discovered by noticing clues.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.label:8} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "concern")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    expected_concern = {("fox", "mystery")}
    actual_concern = set(asp.atoms(model, "concern"))
    expected_lessons = {
        ("investigate_before_judging",),
        ("disgust_is_a_warning_not_a_verdict",),
    }
    actual_lessons = set(asp.atoms(model, "lesson"))
    if actual_concern != expected_concern or actual_lessons != expected_lessons:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo concern:", sorted(actual_concern))
        print("  python concern:", sorted(expected_concern))
        print("  clingo lessons:", sorted(actual_lessons))
        print("  python lessons:", sorted(expected_lessons))
        return 1

    for params in CURATED:
        sample = generate(params)
        if "Lesson learned:" not in sample.story or "disgust" not in sample.story.lower():
            print("MISMATCH: generated story failed the narrative gate.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("MISMATCH: generated story lacks QA coverage.")
            return 1

    print("OK: clingo parity and generated-story checks passed.")
    return 0


CURATED = [
    StoryParams(
        seed=1,
        name="Luna",
        helper="Pip",
        elder="Mara",
        place="the woodland pond",
        mystery=0,
        opening=0,
        reaction=2,
        turn=4,
        ending=2,
    ),
    StoryParams(
        seed=2,
        name="Clover",
        helper="Finn",
        elder="Olive",
        place="the old apple orchard",
        mystery=1,
        opening=3,
        reaction=3,
        turn=0,
        ending=4,
    ),
    StoryParams(
        seed=3,
        name="Poppy",
        helper="Roo",
        elder="Maple",
        place="the meadow burrow",
        mystery=4,
        opening=5,
        reaction=1,
        turn=2,
        ending=0,
    ),
]


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
        facts = asp_valid()
        print(f"{len(facts)} ASP concern facts")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(50, args.n * 40)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1
        if len(samples) < args.n:
            raise StoryError("could not produce the requested number of distinct stories")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.name}: {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
