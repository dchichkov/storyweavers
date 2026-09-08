#!/usr/bin/env python3
"""
A small mythic daytime storyworld beneath a city, where Luna follows a
whispering sewer stream, faces suspense, and learns that courage listens before
it leaps.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    name: str
    companion: str
    token: str
    setting: str = "day sewer"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


NAMES = ["Luna", "Mira", "Tavi", "Niko", "Sela", "Orin"]
COMPANIONS = ["a small fox", "a blue jay", "a brave mouse", "a young badger"]
TOKENS = ["moon-stone", "silver button", "blue feather", "red thread"]

SCENARIOS = [
    {
        "key": "echoing_gate",
        "premise": "a pale bell beneath the street began ringing though no hand touched it",
        "threat": "the sewer water was rising toward the old gate",
        "clue": "each bell note came just after a distant clank in the wall",
        "memory": "the old keeper's saying that a warning often wears the voice of fear",
        "dialogue": "'Do we run toward the bell?' asked the companion. 'We listen first,' said Luna.",
        "action": "Luna held the token against the stones and counted three clanks before leading the companion to a high maintenance stair",
        "result": "a hidden sluice opened, lowering the water and silencing the bell",
        "ending": "When noon light touched the street grate, the bell gave one gentle note, like a myth remembering its name",
        "lesson": "courage is not the absence of fear; it is giving fear time to explain itself",
    },
    {
        "key": "shadow_below",
        "premise": "a huge shadow slid across the sewer wall and swallowed the afternoon sunbeam",
        "threat": "the narrow passage behind them filled with rushing water",
        "clue": "the shadow's tail moved only when a wheel turned above the street",
        "memory": "a tale about the First City, whose giants were only carts seen through mist",
        "dialogue": "'The giant is coming!' cried the companion. 'Then let us learn its footsteps,' Luna replied.",
        "action": "Luna watched the repeating shadow, found a dry alcove, and waited there until the street wheel rolled past",
        "result": "the supposed giant vanished, while the water drained into a lower channel",
        "ending": "Above them, a wagon crossed the road, and its shadow bowed on the sewer wall like a harmless giant",
        "lesson": "a frightening shape becomes smaller when its pattern is understood",
    },
    {
        "key": "whispering_pipe",
        "premise": "an iron pipe whispered Luna's name from the deepest bend",
        "threat": "the whisper drew the pair toward a broken ledge beside a dark drop",
        "clue": "the same whisper repeated whenever wind passed through a cracked vent",
        "memory": "the river myth in which the moon answered every question only after the questioner became still",
        "dialogue": "'It knows you,' said the companion. 'It knows the wind,' Luna answered.",
        "action": "Luna stopped, placed the token on the dry stones, and followed the wind toward a ladder marked with a sun",
        "result": "they climbed to a safe inspection platform and found the ledge crumbling below",
        "ending": "The pipe whispered once more, but in daylight it sounded like a flute beneath the city",
        "lesson": "stillness can separate a true summons from an echo",
    },
    {
        "key": "sleeping_lantern",
        "premise": "a lantern under the sewer arch flickered with a blue flame at midday",
        "threat": "its light revealed footprints leading into a flooded tunnel",
        "clue": "the footprints stopped where a warm air vent rose from the floor",
        "memory": "the village myth of a star that guided travelers by showing them where not to step",
        "dialogue": "'The blue flame wants us inside,' said the companion. 'Perhaps it wants us to notice the edge,' Luna said.",
        "action": "Luna marked the safe stones with the token's red thread and called for the city keeper",
        "result": "the keeper found a broken gas valve and closed it before anyone entered the tunnel",
        "ending": "The lantern burned gold again, guarding the arch without asking anyone to follow it",
        "lesson": "a sign can guide you by warning you away from danger",
    },
    {
        "key": "stone_heart",
        "premise": "a round stone pulsed in a drain chamber like a sleeping heart",
        "threat": "every pulse loosened pebbles from the ceiling",
        "clue": "the pulses matched the pounding of a pump on the far side of the wall",
        "memory": "the mountain myth in which the earth's heart beat whenever people forgot to repair its paths",
        "dialogue": "'Should we wake it?' asked the companion. 'No; we should wake the keeper,' said Luna.",
        "action": "Luna climbed the service ladder and used the token to signal the keeper through the grate",
        "result": "the pump was stopped, the stones settled, and the chamber became quiet",
        "ending": "The round stone rested in a beam of day, ordinary as bread and twice as precious",
        "lesson": "the wisest hero calls for help before touching a mystery",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, day_sewer), token(P, _), companion(P, _).
story_ok(P) :- valid(P), suspense(P), listened(P), safe(P), resolved(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mythic suspense storyworld in a daytime sewer."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--token")
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
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    token = args.token or rng.choice(TOKENS)
    if not name.strip():
        raise StoryError("The hero's name cannot be empty.")
    if companion not in COMPANIONS:
        raise StoryError("The companion must be a listed sewer companion.")
    if token not in TOKENS:
        raise StoryError("The token must be a listed mythic token.")
    return StoryParams(name=name, companion=companion, token=token)


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("params", "p1"),
            asp.fact("setting", "p1", "day_sewer"),
            asp.fact("companion", "p1", "fox"),
            asp.fact("token", "p1", "moon_stone"),
            asp.fact("suspense", "p1"),
            asp.fact("listened", "p1"),
            asp.fact("safe", "p1"),
            asp.fact("resolved", "p1"),
        ]
    )


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    complete = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in complete:
        print("OK: ASP and Python gates accept the mythic sewer story.")
        return 0
    print("Mismatch: ASP did not accept the storyworld.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "day sewer":
        raise StoryError("This storyworld requires the setting 'day sewer'.")
    if params.companion not in COMPANIONS:
        raise StoryError("This companion is not part of the day sewer myth.")
    if params.token not in TOKENS:
        raise StoryError("This token is not part of the day sewer myth.")

    world = World(params)
    hero = world.add(Entity(params.name, "hero", params.name))
    companion = world.add(Entity("companion", "companion", params.companion))
    token = world.add(Entity("token", "token", params.token))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(c) for c in f"{params.name}|{params.companion}|{params.token}")
    scenario = SCENARIOS[stable_seed % len(SCENARIOS)]

    hero.memes.update(courage=1.0, patience=1.0, wonder=1.0)
    companion.memes.update(unease=0.8, trust=0.9)
    token.meters["dry"] = 1.0
    world.facts.update(
        setting="day sewer",
        scenario=scenario["key"],
        threat=scenario["threat"],
        clue=scenario["clue"],
        listened=True,
        safe=True,
        resolved=True,
        suspense=True,
        entered_danger=False,
    )

    world.say(
        f"In the bright part of the day, {params.name} and {params.companion} "
        f"stood beside a sewer where the city carried its hidden rivers. "
        f"There, {scenario['premise']}. Even the sunbeam at the grate seemed to hold its breath."
    )
    world.say(
        f"The danger was not a dragon from an ancient song, but it felt just as near: "
        f"{scenario['threat']}. {params.name} held the {params.token} tightly, while "
        f"the companion watched the black water."
    )
    world.say(
        f"Then {params.name} remembered {scenario['memory']}. "
        f"The first fear had become suspense, and suspense became a question."
    )
    world.say(
        f"{scenario['dialogue']} The pair stayed on the dry stones and listened. "
        f"The clue was clear: {scenario['clue']}."
    )
    world.say(
        f"Instead of rushing into the dark, {scenario['action']}. "
        f"They did not climb into the water, touch the unknown machine, or leave the safe path."
    )
    world.say(
        f"That choice changed the hidden world. {scenario['result']}. "
        f"{params.name} understood that {scenario['lesson']}."
    )
    world.say(
        f"At last, the sewer no longer seemed like a monster's throat. "
        f"{scenario['ending']}. The ordinary day above them felt like a blessing."
    )

    story_qa = [
        QAItem(
            question=f"What first frightened {params.name} in the sewer?",
            answer=f"The first frightening sign was that {scenario['premise']}. It created suspense because the pair could not yet tell what caused it.",
        ),
        QAItem(
            question="What clue helped solve the mystery?",
            answer=f"The clue was that {scenario['clue']}. That repeating pattern showed what the strange event really meant.",
        ),
        QAItem(
            question=f"How did {params.name} act bravely?",
            answer=f"{params.name} did not rush into danger. {scenario['action']}.",
        ),
        QAItem(
            question="What happened after the careful choice?",
            answer=f"{scenario['result']}. The safe action changed the danger instead of making it worse.",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=f"It taught that {scenario['lesson']}. The ending proved this through a safe, calmer world.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a sewer?",
            answer="A sewer is an underground system of channels and pipes that carries wastewater or rainwater away from streets and buildings.",
        ),
        QAItem(
            question="Why should people stay out of sewers?",
            answer="People should stay out of sewers because dark water, slippery surfaces, sudden flooding, gases, and machinery can make them dangerous.",
        ),
        QAItem(
            question="What makes suspense work in a story?",
            answer="Suspense grows when a character faces an uncertain danger, notices clues, and must choose what to do before the answer is known.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is a traditional kind of story that uses memorable characters and strange events to explore a lasting truth or lesson.",
        ),
    ]
    prompts = [
        f"Tell a mythic suspense story about {params.name} and {params.companion} in a daytime sewer.",
        f"Use a {params.token} as a clue, let the characters speak, and resolve the sewer mystery safely.",
        "Write a child-facing myth where listening turns a frightening underground sign into understanding.",
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False) -> None:
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
        print(f"facts={sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(aspire())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(aspire())
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("Luna", "a small fox", "moon-stone", seed=base_seed),
            StoryParams("Mira", "a blue jay", "blue feather", seed=base_seed + 1),
            StoryParams("Tavi", "a brave mouse", "silver button", seed=base_seed + 2),
            StoryParams("Sela", "a young badger", "red thread", seed=base_seed + 3),
        ]
    else:
        params_list = []
        for index in range(max(0, args.n)):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(params) for params in params_list]
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {index + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
