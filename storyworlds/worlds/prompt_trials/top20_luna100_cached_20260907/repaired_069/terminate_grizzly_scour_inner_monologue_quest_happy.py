#!/usr/bin/env python3
"""A child-friendly superhero quest about a grizzly, a careful scour, and a happy ending."""

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
    owner: Optional[str] = None
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
    hero: str = "Luna"
    grizzly: str = "Bruno"
    helper: str = "Pip"
    place: str = "Brightwood"
    quest: int = 0
    opening: int = 0
    thought: int = 0
    dialogue: int = 0
    ending: int = 0


HEROES = ["Luna", "Nova", "Skye", "Comet", "Mira"]
GRIZZLIES = ["Bruno", "Granite", "Hugo", "Tundra"]
HELPERS = ["Pip", "Tess", "Robin", "Jax"]
PLACES = ["Brightwood", "Sunbeam City", "Moonlit Park", "Cloudbridge"]

QUESTS = [
    {
        "title": "the dark signal tower",
        "problem": "The beacon tower had gone dark just before the town's night rescue drill.",
        "clue": "Luna saw dusty pollen packed around the little solar lens.",
        "scour": "She used a soft scarf to scour the pollen from the lens without scratching it.",
        "result": "The clean lens caught the last orange ray and sent a bright signal across the hills.",
        "lesson": "A gentle, careful fix can be stronger than a flashy one.",
        "object": "solar lens",
    },
    {
        "title": "the muddy hero bridge",
        "problem": "A storm left the bridge slippery, and young campers could not cross safely.",
        "clue": "Luna noticed that the mud was hiding shallow grooves in the bridge boards.",
        "scour": "She and Pip scoured the grooves with stiff brushes while Bruno carried fresh sand.",
        "result": "The boards became safe and firm, and the campers crossed one by one.",
        "lesson": "A hero notices the small danger before it becomes a big one.",
        "object": "bridge boards",
    },
    {
        "title": "the vanished park map",
        "problem": "The rescue map at the park gate had faded beneath layers of soot and rain.",
        "clue": "Luna found a blue star beneath the gray coating.",
        "scour": "She carefully scoured the map with a damp sponge, stopping whenever a colored line appeared.",
        "result": "The hidden trails returned, and the lost hikers found the sunny picnic hill.",
        "lesson": "Patience can reveal a path that rushing would destroy.",
        "object": "park map",
    },
    {
        "title": "the humming power box",
        "problem": "A power box hummed beside the playground, making everyone nervous.",
        "clue": "Luna discovered leaves wedged against its outside cooling grate.",
        "scour": "With Bruno watching the safe distance, she scoured the leaves away using a long wooden brush.",
        "result": "The humming softened, the safety lights returned, and the playground reopened.",
        "lesson": "Bravery means using good judgment, not charging blindly.",
        "object": "cooling grate",
    },
    {
        "title": "the cloud-rail rescue",
        "problem": "A tiny sky-train stalled above the city with three passengers inside.",
        "clue": "Luna spotted silver dust blocking the emergency signal mirror.",
        "scour": "She floated close and scoured the mirror clean with her star-glove.",
        "result": "The mirror flashed, the rescue crew found the train, and every passenger came home.",
        "lesson": "Clear signals help helpers arrive in time.",
        "object": "signal mirror",
    },
    {
        "title": "the grizzly's lost badge",
        "problem": "Bruno's old forest-guard badge had fallen into a muddy stream.",
        "clue": "Luna saw its golden edge beneath a coat of river grit.",
        "scour": "She scoured the badge with river water and a soft leaf until the tiny bear emblem shone.",
        "result": "Bruno pinned it proudly to his vest and led the festival parade.",
        "lesson": "Restoring something precious can restore someone's courage too.",
        "object": "forest-guard badge",
    },
    {
        "title": "the smoky library window",
        "problem": "Smoke from a distant campfire covered the library window before story hour.",
        "clue": "Luna found one clear corner where the wind had passed.",
        "scour": "She scoured the glass in wide circles while Pip opened the vents.",
        "result": "Sunlight filled the reading room, and the children gathered for a bright new tale.",
        "lesson": "Teamwork turns a cloudy problem into a clear view.",
        "object": "library window",
    },
    {
        "title": "the comet garden alarm",
        "problem": "The garden alarm would not terminate its warning chirp after a harmless twig fell nearby.",
        "clue": "Luna heard the chirp change whenever dust touched the sensor.",
        "scour": "She scoured the sensor's cover clean, then waited for Bruno to confirm the garden was safe.",
        "result": "The alarm stopped, and the moonflowers opened without fear.",
        "lesson": "Before stopping a warning, a hero checks why it began.",
        "object": "garden sensor",
    },
]

OPENINGS = [
    "At dawn in {place}, {hero} zipped above the rooftops, watching for anyone who needed help.",
    "The sun rose over {place}, and {hero} felt the familiar spark of a new superhero quest.",
    "In {place}, people knew {hero} for a bright cape and an even brighter habit of looking closely.",
    "A silver alert flashed above {place}, and {hero} landed beside {helper} before the town bell rang.",
    "The morning was cheerful in {place} until {hero} heard a worried grumble near the town square.",
]

THOUGHTS = [
    "Luna thought, 'I am nervous, but I can learn what is wrong before I act.'",
    "Inside, Luna told herself, 'A real hero does not need the loudest move; I need the safest useful one.'",
    "Luna's thoughts raced: 'First notice the danger, then find the cause, then help.'",
    "For one moment Luna wanted to rush. Then she thought, 'Careful eyes can be brave eyes.'",
    "Luna took a breath and thought, 'If I listen to Bruno and check the clue, we can solve this together.'",
]

DIALOGUES = [
    '"Should we blast it away?" asked Bruno. "No," said Luna. "Let us scour the trouble gently and see what changes."',
    '"I am too large for this tiny job," said Bruno. Luna smiled. "You can guard the people while I clean the clue."',
    '"What do you know?" asked Luna. "The noise changes near the dust," said Bruno. "Then that is where we begin," Luna replied.',
    '"I can carry the heavy gear," said Bruno. "And I can handle the careful part," said Luna. "That makes us a team."',
    '"Will this quest work?" whispered Pip. "We will test each step," Luna said. Bruno nodded. "And I will stay close."',
]

ENDINGS = [
    "When the work was done, the town cheered, and Luna's cape glowed above a happy crowd.",
    "Everyone celebrated with warm berry muffins, while Luna and Bruno watched the safe place shine.",
    "The rescued neighbors waved from below, and Luna felt her worried thoughts turn into peaceful pride.",
    "Bruno lifted Luna onto his broad shoulders, and together they watched the town sparkle safely.",
    "That evening, the hero bell rang once for courage and twice for teamwork.",
]


ASP_RULES = r"""
#show quest/1.
#show safe/1.

quest(Q) :- chosen_quest(Q), clue(Q), careful_action(Q).
safe(Q) :- quest(Q), danger_checked(Q), repaired(Q).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("chosen_quest", "careful_rescue"),
            asp.fact("clue", "careful_rescue"),
            asp.fact("careful_action", "careful_rescue"),
            asp.fact("danger_checked", "careful_rescue"),
            asp.fact("repaired", "careful_rescue"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero storyworld about Luna, a grizzly, and a careful quest."
    )
    parser.add_argument("--hero", choices=HEROES)
    parser.add_argument("--grizzly", choices=GRIZZLIES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--quest", type=int, choices=range(len(QUESTS)))
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
        raise StoryError("-n must be at least 1.")
    return StoryParams(
        seed=args.seed,
        hero=args.hero or rng.choice(HEROES),
        grizzly=args.grizzly or rng.choice(GRIZZLIES),
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        quest=args.quest if args.quest is not None else rng.randrange(len(QUESTS)),
        opening=rng.randrange(len(OPENINGS)),
        thought=rng.randrange(len(THOUGHTS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if not params.hero or not params.grizzly or not params.helper or not params.place:
        raise StoryError("A hero, grizzly, helper, and place are required.")
    if not 0 <= params.quest < len(QUESTS):
        raise StoryError("Quest index is outside the available quest registry.")

    world = World()
    hero = world.add(
        Entity(
            id=params.hero,
            type="hero",
            label=params.hero,
            meters={"energy": 1.0, "focus": 1.0},
            memes={"courage": 0.7, "worry": 0.3},
        )
    )
    grizzly = world.add(
        Entity(
            id=params.grizzly,
            type="grizzly",
            label=params.grizzly,
            meters={"strength": 1.0},
            memes={"loyalty": 0.8, "worry": 0.4},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            type="helper",
            label=params.helper,
            meters={"quickness": 0.8},
            memes={"hope": 0.9},
        )
    )

    quest = QUESTS[params.quest]

    def replace_names(text: str) -> str:
        return (
            text.replace("Luna", hero.id)
            .replace("Bruno", grizzly.id)
            .replace("Pip", helper.id)
        )

    world.say(
        OPENINGS[params.opening % len(OPENINGS)].format(
            place=params.place, hero=hero.id, helper=helper.id
        )
    )
    world.say(f"Her quest was {quest['title']}. {quest['problem']}")
    world.say(
        f"{grizzly.id} stood nearby, a large grizzly with a kind heart, but the danger made him uneasy."
    )
    world.say(replace_names(THOUGHTS[params.thought % len(THOUGHTS)]))
    world.say(replace_names(DIALOGUES[params.dialogue % len(DIALOGUES)]))
    world.say(f"{hero.id} studied the scene instead of rushing. {quest['clue']}")
    world.say(
        f"{helper.id} marked a safe path, while {grizzly.id} kept everyone behind the bright safety line."
    )
    world.say(quest["scour"])
    world.say(
        f"The first careful pass changed the problem, so {hero.id} checked the clue again before making a second pass."
    )
    world.say(quest["result"])
    world.say(
        f"With the danger gone, {hero.id} pressed the town's blue button to terminate the warning signal."
    )

    hero.memes["courage"] = 1.0
    hero.memes["worry"] = 0.0
    grizzly.memes["worry"] = 0.0
    helper.memes["hope"] = 1.0

    world.say(f"Lesson learned: {quest['lesson']}")
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    world.facts.update(
        hero=hero,
        grizzly=grizzly,
        helper=helper,
        place=params.place,
        quest=quest,
        quest_title=quest["title"],
        clue=quest["clue"],
        scour=quest["scour"],
        repaired=True,
        danger_checked=True,
        warning_terminated=True,
        happy_ending=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    hero = facts["hero"]
    grizzly = facts["grizzly"]
    quest = facts["quest"]
    return [
        f"Write a child-friendly superhero story about {hero.id} completing {quest['title']} with {grizzly.id} the grizzly.",
        f"Tell a quest story where a hero uses a careful scour to solve {quest['object']} and terminate a warning safely.",
        f"Write a superhero adventure with an inner monologue, back-and-forth dialogue, a clear quest, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    grizzly = facts["grizzly"]
    helper = facts["helper"]
    quest = facts["quest"]
    return [
        QAItem(
            question=f"What quest did {hero.id} complete?",
            answer=f"{hero.id} completed {quest['title']}, helping the people of {facts['place']}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice before acting?",
            answer=f"{hero.id} noticed this clue: {quest['clue']}",
        ),
        QAItem(
            question=f"How did {hero.id} scour the problem?",
            answer=quest["scour"],
        ),
        QAItem(
            question=f"How did {grizzly.id} and {helper.id} help?",
            answer=(
                f"{grizzly.id} kept everyone safe behind the safety line, while {helper.id} marked a safe path "
                "so the careful work could happen without a new danger."
            ),
        ),
        QAItem(
            question="Why did the hero terminate the warning signal?",
            answer=(
                f"The hero terminated the warning only after checking that the danger had been repaired and the "
                f"area was safe. The repair was {quest['result']}"
            ),
        ),
        QAItem(
            question="What made the ending happy?",
            answer=(
                f"The danger ended, the people were safe, and {hero.id}, {grizzly.id}, and {helper.id} "
                "celebrated their teamwork."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or stop it.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. Grizzlies are powerful wild animals and should be observed safely from a distance.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to clean or search something carefully, often by rubbing or looking closely.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thoughts written as words inside the story.",
        ),
        QAItem(
            question="What makes a superhero story?",
            answer="A superhero story usually has a hero, a difficult problem, brave choices, helpful allies, and a hopeful result.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
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
            f"  {entity.id:10} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> set[tuple[str, ...]]:
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show safe/1."))
    return {
        tuple(str(value) for value in atom)
        for predicate in ("quest", "safe")
        for atom in asp.atoms(model, predicate)
    }


def asp_verify() -> int:
    expected = {
        ("careful_rescue",),
    }
    import asp
    model = asp.one_model(asp_program("#show quest/1.\n#show safe/1."))
    actual = set(asp.atoms(model, "quest")) | set(asp.atoms(model, "safe"))
    if actual == expected | expected:
        sample = generate(
            StoryParams(
                seed=1,
                hero="Luna",
                grizzly="Bruno",
                helper="Pip",
                place="Brightwood",
                quest=0,
            )
        )
        required = ["terminate", "grizzly", "scour"]
        if all(word in sample.story.lower() for word in required):
            print("OK: ASP parity and generated-story checks passed.")
            return 0
        print("Generated story is missing a required seed word.")
        return 1
    print("MISMATCH between clingo and Python gate.")
    print("  clingo:", sorted(actual))
    print("  python:", sorted(expected | expected))
    return 1


CURATED = [
    StoryParams(
        seed=1,
        hero="Luna",
        grizzly="Bruno",
        helper="Pip",
        place="Brightwood",
        quest=0,
        opening=0,
        thought=0,
        dialogue=0,
        ending=0,
    ),
    StoryParams(
        seed=2,
        hero="Nova",
        grizzly="Granite",
        helper="Tess",
        place="Sunbeam City",
        quest=4,
        opening=1,
        thought=2,
        dialogue=3,
        ending=2,
    ),
    StoryParams(
        seed=3,
        hero="Skye",
        grizzly="Hugo",
        helper="Robin",
        place="Cloudbridge",
        quest=7,
        opening=3,
        thought=4,
        dialogue=2,
        ending=4,
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
        print(asp_program("#show quest/1.\n#show safe/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print("ASP-supported atoms:")
        for atom in sorted(asp_valid()):
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            sample = generate(params)
            attempt += 1
            if sample.story in seen:
                if attempt > max(100, args.n * 50):
                    raise StoryError("Could not produce enough distinct story variants.")
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
        if args.all:
            header = f"### {sample.params.hero}: superhero quest"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
