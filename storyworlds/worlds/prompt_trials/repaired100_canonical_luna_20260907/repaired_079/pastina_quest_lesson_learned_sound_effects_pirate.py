#!/usr/bin/env python3
"""
A child-friendly pirate storyworld about pastina, a tiny quest, sound effects,
and a lesson learned.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    trace: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)
        self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain_name: str = "Luna"
    helper_name: str = "Pip"
    ship_name: str = "the Silver Spoon"


NAMES = ["Luna", "Mara", "Tessa", "Nico", "Pip", "Rafi", "Cleo", "Finn"]
SHIP_NAMES = ["the Silver Spoon", "the Kind Shark", "the Blue Teapot", "the Little Gull"]

QUESTS = [
    {
        "island": "Crumbcap Island",
        "goal": "carry a warm pot of pastina to the lighthouse keeper",
        "obstacle": "a fog bank hid the safe channel",
        "wrong": "followed a loud crashing sound and steered toward a rocky reef",
        "setback": "the boat had to anchor in a quiet cove, and the pastina began to cool",
        "clue": "the bell buoy made one clear ding whenever the safe channel opened",
        "sound": "Ding! Ding!",
        "plan": "listen for the bell buoy, count two quiet waves, and turn only after the second ding",
        "success": "the fog parted just long enough for the boat to glide into the lighthouse cove",
        "ending": "the keeper lifted the lid, and the tiny pastina stars steamed like a bowl of treasure",
        "lesson": "A loud sound is not always the right clue; careful listening can guide a brave crew.",
    },
    {
        "island": "Noodlehook Isle",
        "goal": "deliver a basket of pastina to children waiting at the harbor",
        "obstacle": "the tide had covered the painted dock signs",
        "wrong": "chased a parrot's squawk and landed at an empty fish dock",
        "setback": "the basket stayed safe, but the children had to wait while the crew found the right pier",
        "clue": "the harbor bell rang twice for the pastina pier",
        "sound": "Clang! Clang!",
        "plan": "ignore the squawk, follow the double bell, and ask the dock keeper before tying up",
        "success": "the crew found the right pier beneath a striped sail",
        "ending": "the children cheered as pastina bowls bobbed in their hands like little golden ships",
        "lesson": "Asking a helpful question is wiser than guessing from the noisiest sign.",
    },
    {
        "island": "Spoonbeard Cay",
        "goal": "find the old cook's recipe chest and bring it back aboard",
        "obstacle": "the jungle path was marked by drums and rustling palms",
        "wrong": "ran toward the biggest boom and wandered into a circle of friendly monkeys",
        "setback": "the monkeys borrowed the captain's map, so the quest stopped until everyone calmed down",
        "clue": "the recipe chest clicked softly whenever the correct path was near",
        "sound": "Click-click!",
        "plan": "walk slowly, stop after each click, and offer the monkeys a spare ribbon instead of grabbing the map",
        "success": "the monkeys returned the map and led the crew to the chest",
        "ending": "inside the chest lay a recipe card decorated with one smiling pastina star",
        "lesson": "Gentle choices can solve a problem that rushing only makes bigger.",
    },
    {
        "island": "Biscuit Bay",
        "goal": "bring pastina soup to a sleepy sailor on the far pier",
        "obstacle": "a playful sea lion splashed beside every boat",
        "wrong": "mistook each splash for a danger signal and zigzagged away from the pier",
        "setback": "the sailor waited longer, while the soup sloshed but stayed in its covered pot",
        "clue": "the sea lion clapped only when the boat pointed toward the pier",
        "sound": "Splish! Clap!",
        "plan": "watch the claps instead of fearing the splashes, then row in a straight line",
        "success": "the sea lion's claps made a cheerful path across the bay",
        "ending": "the sailor shared the last spoonful, and the sea lion applauded with both flippers",
        "lesson": "A surprising helper may be giving directions in a way we do not expect.",
    },
]

MODES = [
    ("The sea was calm, but Captain Luna knew every quest deserved care.", "The crew treated the mistake as a clue instead of a reason to quit."),
    ("The little ship smelled of warm pastina as it left the harbor.", "The next decision began when the crew stopped and listened together."),
    ("Captain Luna promised a simple voyage, but the sea had another idea.", "A patient plan turned the noisy trouble into useful information."),
]


def _setup(world: World, params: StoryParams) -> None:
    captain = world.add(Entity(params.captain_name, "character", "captain", params.captain_name))
    helper = world.add(Entity(params.helper_name, "character", "helper", params.helper_name))
    ship = world.add(Entity("ship", "thing", "ship", params.ship_name))
    pot = world.add(Entity("pastina_pot", "thing", "pot", "a covered pot of pastina"))
    bell = world.add(Entity("sound_marker", "thing", "sound", "the helpful sound"))

    captain.meters["courage"] = 1.0
    captain.memes["worry"] = 0.0
    helper.meters["listening"] = 1.0
    ship.meters["safety"] = 1.0
    pot.meters["warmth"] = 1.0
    bell.memes["clarity"] = 0.0
    world.facts.update(captain=captain, helper=helper, ship=ship, pot=pot, bell=bell)


def _token(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = "|".join((params.captain_name, params.helper_name, params.ship_name))
    return sum((i + 1) * ord(c) for i, c in enumerate(text))


def tell_story(params: StoryParams) -> World:
    world = World()
    _setup(world, params)
    quest = QUESTS[_token(params) % len(QUESTS)]
    mode = MODES[(_token(params) // len(QUESTS)) % len(MODES)]
    captain = world.facts["captain"]
    helper = world.facts["helper"]
    ship = world.facts["ship"]
    pot = world.facts["pot"]

    world.say(mode[0])
    world.say(
        f"Captain {captain.label} and {helper.label} sailed {ship.label} toward "
        f"{quest['island']} to {quest['goal']}."
    )
    world.say(
        f"The covered pot kept the pastina warm, and the sea made a cheerful "
        f"sound: {quest['sound']} But {quest['obstacle']}."
    )

    world.para()
    world.say(f"At first, Captain {captain.label} {quest['wrong']}.")
    world.say(f'"That sound must be the way!" cried {captain.label}.')
    world.say(
        f'"Let us pause and listen for a pattern," said {helper.label}. '
        "A good pirate does not have to hurry past every puzzling noise."
    )
    world.say(mode[1])
    world.say(f"The wrong turn brought trouble: {quest['setback']}.")

    world.para()
    world.say(
        f"The crew lowered the sail and listened again. They discovered that "
        f"{quest['clue']} The sound was {quest['sound']}"
    )
    world.say(
        f'"Now we know what to do," said {helper.label}. '
        f'"{quest["plan"].capitalize()}."'
    )
    world.say(
        f'"I will follow your careful ears," Captain {captain.label} replied. '
        '"We will make this quest together."'
    )
    world.say(f"Together they followed the new plan: they {quest['plan']}.")

    world.para()
    world.say(f"The plan worked: {quest['success']}.")
    world.say(f"They completed the quest and found that {quest['ending']}.")
    world.say(f'"We learned something important today," said {captain.label}.')
    world.say(f'"Yes," replied {helper.label}. "{quest["lesson"]}"')
    world.say(
        f"With the empty pot safely washed and the lesson tucked into their hearts, "
        f"the crew sailed home under a sky full of friendly stars."
    )

    ship.meters["safety"] = 1.0
    pot.meters["warmth"] = 0.0
    captain.memes["worry"] = 0.0
    world.facts.update(
        quest=quest,
        quest_index=_token(params) % len(QUESTS),
        params=params,
        completed=True,
        lesson_learned=True,
        sound_effect=quest["sound"],
    )
    world.fired.update({("quest", "begun"), ("quest", "mistake"), ("quest", "repaired"), ("quest", "completed")})
    return world


def valid_story() -> bool:
    return True


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    quest = world.facts["quest"]
    return [
        f"Write a child-friendly pirate tale in which {params.captain_name} quests to {quest['goal']} with pastina aboard a small ship.",
        f"Include the sound effect {quest['sound']}, a wrong turn, a brief dialogue exchange, and a lesson learned about careful listening.",
        f"Show how a pirate quest changes from trouble to a warm, happy ending through teamwork and a concrete plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    quest = world.facts["quest"]
    return [
        QAItem(
            question=f"What quest did {params.captain_name} and {params.helper_name} undertake?",
            answer=f"They sailed toward {quest['island']} to {quest['goal']}.",
        ),
        QAItem(
            question="What went wrong during the quest?",
            answer=f"The crew made a wrong turn when they {quest['wrong']}. This caused a setback: {quest['setback']}.",
        ),
        QAItem(
            question="What sound effect appeared in the story?",
            answer=f"The helpful sound was {quest['sound']}, made by the clue that guided the crew.",
        ),
        QAItem(
            question="How did the pirates repair their plan?",
            answer=f"They learned that {quest['clue']} Then they followed this plan: {quest['plan']}.",
        ),
        QAItem(
            question="What lesson did the crew learn?",
            answer=quest["lesson"],
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The quest ended happily because {quest['success']}. Then {quest['ending']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pastina?",
            answer="Pastina is tiny pasta, often cooked in a warm soup or broth.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a purposeful journey or task that someone works to complete.",
        ),
        QAItem(
            question="Why can sound effects help a story?",
            answer="Sound effects make an action easier to imagine and can give characters clues about what is happening.",
        ),
    ]


ASP_RULES = r"""
quest_started(S) :- has_pastina(S), pirate_crew(S).
wrong_turn(S) :- quest_started(S), noisy_clue(S).
lesson_learned(S) :- wrong_turn(S), careful_listening(S), kind_teamwork(S).
happy_ending(S) :- quest_started(S), lesson_learned(S), quest_completed(S).
valid_story(S) :- happy_ending(S).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("has_pastina", "story1"),
            asp.fact("pirate_crew", "story1"),
            asp.fact("noisy_clue", "story1"),
            asp.fact("careful_listening", "story1"),
            asp.fact("kind_teamwork", "story1"),
            asp.fact("quest_completed", "story1"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    actual = set(asp.atoms(model, "valid_story"))
    expected = {("story1",)} if valid_story() else set()
    if actual == expected:
        print("OK: clingo parity matches Python gate.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(actual))
    print("Python:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a pastina quest, sound effects, and a lesson learned."
    )
    parser.add_argument("--captain-name", choices=NAMES)
    parser.add_argument("--helper-name", choices=NAMES)
    parser.add_argument("--ship-name", choices=SHIP_NAMES)
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
    captain = args.captain_name or rng.choice(NAMES)
    choices = [name for name in NAMES if name != captain]
    helper = args.helper_name or rng.choice(choices)
    ship = args.ship_name or rng.choice(SHIP_NAMES)
    return StoryParams(
        seed=None,
        captain_name=captain,
        helper_name=helper,
        ship_name=ship,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(
            f"  {entity.id:14} ({entity.kind:9}) {' '.join(details)}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.append("")
    output.append("== (2) Story questions ==")
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.append("")
    output.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


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
    StoryParams(captain_name="Luna", helper_name="Pip", ship_name="the Silver Spoon"),
    StoryParams(captain_name="Mara", helper_name="Finn", ship_name="the Kind Shark"),
    StoryParams(captain_name="Tessa", helper_name="Rafi", ship_name="the Little Gull"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        for index in range(args.n):
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
