#!/usr/bin/env python3
"""
A small adventure storyworld about a squire whose itchy panic becomes a lesson
in careful courage.
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
class Entity:
    id: str
    kind: str
    label: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

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


@dataclass
class StoryParams:
    hero: str
    knight: str
    squire: str
    quest: str
    creature: str
    lesson: str
    ending: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    opening: str
    danger: str
    clue: str
    tool: str
    action: str
    result: str


@dataclass(frozen=True)
class Lesson:
    temptation: str
    truth: str
    repair: str


@dataclass(frozen=True)
class Ending:
    image: str
    final: str


QUESTS = {
    "moon_bridge": Quest(
        "the moon bridge had vanished behind a curtain of silver fog",
        "a sharp itch began crawling beneath the squire's collar as the ravine roared below",
        "three blue stones glimmered in a line beside the old watchtower",
        "a coil of red rope",
        "tied the rope from stone to stone and tested each foothold before crossing",
        "the hidden bridge appeared when the fog lifted from the safe path",
    ),
    "whispering_cave": Quest(
        "a lost bell was ringing somewhere inside the Whispering Cave",
        "the squire heard a growl and felt an itch race along one arm",
        "small silver feathers lay beside a crack in the cave wall",
        "a lantern with a green glass door",
        "raised the lantern and followed the feathers instead of rushing into the dark",
        "the bell was found beside a sleepy cave bird, not a monster",
    ),
    "storm_tower": Quest(
        "a storm had trapped the castle's signal flag atop the old tower",
        "wind tugged at the ladder while an itch made the squire want to drop everything",
        "the tower keeper had left yellow knots on the safest rungs",
        "a leather climbing belt",
        "climbed one marked rung at a time and fastened the flag to the calm side of the pole",
        "the bright flag flew safely above the storm",
    ),
    "sunken_gate": Quest(
        "the gate to the garden kingdom had sunk into a muddy moat",
        "the mud bubbled, and panic fluttered in the squire's chest when a hidden root brushed a boot",
        "flat stepping stones led toward a dry willow root",
        "a sturdy wooden plank",
        "laid the plank across the softest mud and pulled the gate free with steady teamwork",
        "the garden gate rose, dripping, and opened to the sunlit road",
    ),
    "dragon_library": Quest(
        "an ancient map had been left in the dragon library",
        "a warm puff of air stirred the shelves while an itch tickled the squire's nose",
        "the map's corner shone beneath a stack of books about gentle dragons",
        "a feather duster",
        "cleared the shelf slowly and read the warning before touching the map",
        "the map revealed a peaceful route through the hills",
    ),
}


LESSONS = {
    "breathe": Lesson(
        "run ahead without looking",
        "panic makes a small danger look like a giant one",
        "counted three breaths, named what was truly happening, and chose the next safe step",
    ),
    "ask_help": Lesson(
        "hide the itch and pretend nothing was wrong",
        "asking for help lets trusted friends see a danger sooner",
        "told the knight about the itch and accepted a careful inspection of the path",
    ),
    "slowly": Lesson(
        "rush because brave people never pause",
        "true courage can move slowly when the path is uncertain",
        "waited, checked the ground, and continued only when each step was ready",
    ),
    "notice": Lesson(
        "swat wildly at every strange feeling",
        "attention turns confusion into useful clues",
        "looked closely and discovered that the itch came from a burr caught in the cloak",
    ),
}


ENDINGS = {
    "lantern": Ending(
        "At sunset, warm lanterns glowed along the road home",
        "The squire smiled because the bravest journey had begun with one careful breath.",
    ),
    "feast": Ending(
        "That evening, the castle cooks served honey cakes beneath a banner of victory",
        "The squire saved the smallest cake for the friend who had helped keep everyone safe.",
    ),
    "sunrise": Ending(
        "At dawn, the rescued road shone gold beyond the castle gate",
        "The squire carried the lesson forward like a bright shield.",
    ),
    "campfire": Ending(
        "By the campfire, the rescued travelers told the adventure again with happy voices",
        "Each telling grew less frightening and more full of wonder.",
    ),
}


NAMES = ["Luna", "Mira", "Tarin", "Pip", "Ari", "Nell", "Soren", "Kato"]
KNIGHTS = ["Sir Rowan", "Captain Vale", "Lady Brin", "the castle knight"]
CREATURES = ["a moon fox", "a sleepy griffin", "a tiny dragon", "a silver owl"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adventure storyworld of the itchy squire.")
    parser.add_argument("--hero")
    parser.add_argument("--knight")
    parser.add_argument("--squire")
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--creature")
    parser.add_argument("--lesson", choices=LESSONS)
    parser.add_argument("--ending", choices=ENDINGS)
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
    hero = args.hero or rng.choice(NAMES)
    knight = args.knight or rng.choice([x for x in KNIGHTS if x != hero])
    squire = args.squire or hero
    if not squire.strip():
        raise StoryError("The squire needs a name.")
    return StoryParams(
        hero=hero,
        knight=knight,
        squire=squire,
        quest=args.quest or rng.choice(tuple(QUESTS)),
        creature=args.creature or rng.choice(CREATURES),
        lesson=args.lesson or rng.choice(tuple(LESSONS)),
        ending=args.ending or rng.choice(tuple(ENDINGS)),
    )


def tell(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    lesson = LESSONS[params.lesson]
    ending = ENDINGS[params.ending]

    world = World()
    squire = world.add(Entity("squire", "character", params.squire, "castle road"))
    knight = world.add(Entity("knight", "character", params.knight, "castle road"))
    companion = world.add(Entity("companion", "creature", params.creature, "castle road"))
    world.add(Entity("quest_object", "object", "the quest object", "far road"))
    world.facts.update(
        squire=squire,
        knight=knight,
        companion=companion,
        quest=quest,
        lesson=lesson,
        ending=ending,
        resolved=False,
    )

    world.say(
        f"At dawn, {params.knight} asked {params.squire}, the castle squire, "
        f"to travel beyond the gate with {params.creature} and complete a brave quest."
    )
    world.say(f"They set out because {quest.opening}.")
    world.para()

    squire.meters["uncertainty"] = 1.0
    squire.memes["courage"] = 0.4
    world.say(f"Near the first bend, {quest.danger}.")
    world.say(f"{params.squire} gripped the reins, and panic made the road seem twice as wild.")
    world.say(f"{params.knight} called, \"Tell me what you notice, {params.squire}.\"")
    world.say(f"\"I feel an itch, and I am afraid,\" {params.squire} answered. \"But I can still look.\"")
    world.para()

    world.say(f"The squire remembered the temptation to {lesson.temptation}.")
    world.say(f"Instead, {params.squire} listened as {params.knight} said, \"{lesson.truth.capitalize()}.\"")
    world.say(f"Together they found that {quest.clue}.")
    world.say(f"The itch came from a tiny burr caught in the squire's cloak, not from a hidden beast.")
    squire.memes["panic"] = 0.0
    squire.memes["trust"] = 1.0
    squire.meters["uncertainty"] = 0.2
    world.say(f"{params.squire} chose to {lesson.repair}.")
    world.para()

    world.say(f"With {quest.tool}, the squire {quest.action}.")
    world.say(f"At the hardest moment, {params.creature.capitalize()} gave a soft warning cry, and the squire stopped to listen.")
    world.say(f"Because they worked calmly, {quest.result}.")
    world.say(f"{params.knight} smiled. \"You did not defeat panic by pretending it was gone,\" {params.knight} said. \"You learned how to guide it.\"")
    world.say(f"\"And I learned to ask, breathe, and look closely,\" {params.squire} replied.")
    world.para()

    world.say(f"The lesson learned was simple: {lesson.truth}.")
    world.say(f"{ending.image}.")
    world.say(ending.final)
    world.facts["resolved"] = True
    world.facts["change"] = quest.result
    return world


def generation_prompts(world: World) -> list[str]:
    quest: Quest = world.facts["quest"]
    return [
        f"Write an adventure about a squire facing this danger: {quest.danger}.",
        "Include an itch, a moment of panic, a helpful exchange, a happy ending, and a lesson learned.",
        f"Show how the squire solves the quest using this clue: {quest.clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    squire: Entity = world.facts["squire"]
    knight: Entity = world.facts["knight"]
    quest: Quest = world.facts["quest"]
    lesson: Lesson = world.facts["lesson"]
    return [
        QAItem(
            question=f"Why did {squire.label} feel panic?",
            answer=f"{squire.label} felt panic because {quest.danger}. The strange itch made the danger feel even larger, but the squire stopped to examine it.",
        ),
        QAItem(
            question=f"How did {knight.label} help the squire?",
            answer=f"{knight.label} asked the squire to describe what was happening and reminded the squire that {lesson.truth}.",
        ),
        QAItem(
            question="What changed after the squire faced the problem?",
            answer=f"The squire chose to {lesson.repair}. As a result, {quest.result}.",
        ),
        QAItem(
            question="What lesson did the squire learn?",
            answer=f"The squire learned that {lesson.truth}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a squire?",
            answer="A squire is a young helper who serves and learns from a knight.",
        ),
        QAItem(
            question="What can someone do during panic?",
            answer="Someone can pause, breathe slowly, name the real danger, and ask a trusted person for help.",
        ),
        QAItem(
            question="Why can an itch be useful information?",
            answer="An itch can encourage someone to stop and check whether a burr, insect, or other small cause needs attention.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:12} kind={entity.kind:10} location={entity.location:14} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  resolved={world.facts.get('resolved')}")
    return "\n".join(lines)


ASP_RULES = r"""
place(castle_road).
theme(itch).
theme(panic).
role(squire).
feature(happy_ending).
feature(lesson_learned).
valid(castle_road,itch,panic,squire).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "castle_road"),
            asp.fact("theme", "itch"),
            asp.fact("theme", "panic"),
            asp.fact("role", "squire"),
            asp.fact("feature", "happy_ending"),
            asp.fact("feature", "lesson_learned"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("castle_road", "itch", "panic", "squire")]


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("ASP/Python parity failure.")
        print("Python only:", sorted(python_set - clingo_set))
        print("ASP only:", sorted(clingo_set - python_set))
        return 1
    sample = generate(
        StoryParams(
            hero="Luna",
            knight="Sir Rowan",
            squire="Luna",
            quest="moon_bridge",
            creature="a moon fox",
            lesson="breathe",
            ending="lantern",
        )
    )
    if "itch" not in sample.story or "panic" not in sample.story or "squire" not in sample.story.lower():
        print("Generated story exercise failed.")
        return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"[Prompt {index}] {prompt}")
        for item in sample.story_qa + sample.world_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams("Luna", "Sir Rowan", "Luna", "moon_bridge", "a moon fox", "breathe", "lantern"),
    StoryParams("Mira", "Lady Brin", "Mira", "storm_tower", "a silver owl", "slowly", "sunrise"),
    StoryParams("Tarin", "Captain Vale", "Tarin", "whispering_cave", "a sleepy griffin", "ask_help", "campfire"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
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
