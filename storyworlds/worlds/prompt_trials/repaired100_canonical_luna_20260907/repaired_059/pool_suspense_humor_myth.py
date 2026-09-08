#!/usr/bin/env python3
"""
A small mythic storyworld about Luna, a pool, suspense, and humor.
"""

from __future__ import annotations

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
    treasure: str
    setting: str = "moonlit pool"
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


NAMES = ["Luna", "Mira", "Ivo", "Nia", "Orin", "Tala"]
COMPANIONS = ["fox", "raven", "little goat", "hedgehog", "frog"]
TREASURES = ["silver apple", "star pearl", "golden reed", "moonstone"]

SCENARIOS = [
    {
        "key": "echoing_crown",
        "premise": "the old pool wore a ring of pale lilies, and something beneath the water wore a crown of ripples",
        "problem": "the crown seemed to rise whenever Luna stepped closer, as if the pool's hidden king had awakened",
        "mistake": "Luna lifted a spoon like a royal sword and announced that she would challenge the water at once",
        "clue": "each ripple appeared a heartbeat after the raven tapped a stone on the bank",
        "dialogue": "'Your Majesty is only an echo,' Luna said. 'Then I shall tap very quietly,' said the raven",
        "action": "Luna set down the spoon, watched from the dry bank, and asked the raven to stop tapping while an elder checked the pool",
        "result": "the ripples vanished, revealing a fallen branch below the surface instead of a palace or a monster",
        "ending": "the lilies closed like tiny white curtains, and the raven bowed to the defeated branch",
        "lesson": "suspense becomes wisdom when a brave guess is tested before anyone takes a dangerous step",
    },
    {
        "key": "sleeping_dragon",
        "premise": "a warm mist curled over the pool like a sleeping dragon's breath",
        "problem": "a deep bubbling sound made the travelers wonder whether the dragon was about to sneeze",
        "mistake": "Luna whispered a heroic greeting into the mist, and the frog answered with an enormous burp",
        "clue": "the bubbles rose in a steady line beside the stone spring at the pool's edge",
        "dialogue": "'If it is a dragon, it has a very regular breath,' Luna said. 'And terrible manners,' replied the frog",
        "action": "They backed away from the slippery stones and watched the spring from a safe patch of grass",
        "result": "the bubbling stayed gentle, and the mist thinned until only warm spring water remained",
        "ending": "the frog gave one tiny polite croak to the harmless spring, then hid behind Luna's boot",
        "lesson": "a frightening sound can become funny after careful observation makes its cause clear",
    },
    {
        "key": "moon_mirror",
        "premise": "the pool reflected a second moon, bright enough to make the night birds whisper",
        "problem": "the reflected moon seemed to drift toward the deep center whenever Luna moved along the bank",
        "mistake": "Luna tried to catch the second moon with a reed, which only made the reflection wobble and the companion squeak",
        "clue": "the second moon moved exactly when clouds crossed the real moon above the trees",
        "dialogue": "'It follows the sky, not my reed,' Luna said. 'Then it is a very loyal moon,' said the fox",
        "action": "They kept their feet on the firm bank and waited for the clouds to pass",
        "result": "the reflection became still, and the pool showed one moon above and one moon below",
        "ending": "the fox saluted both moons, then tripped over the reed and blamed gravity",
        "lesson": "wonder grows brighter when curiosity stays patient and safe",
    },
    {
        "key": "whispering_stones",
        "premise": "flat stones around the pool whispered whenever the wind slipped between them",
        "problem": "one whisper sounded like a warning that Luna's treasure would be stolen before dawn",
        "mistake": "Luna hid the treasure under her cloak and tried to interrogate every stone",
        "clue": "the warning changed into a whistle whenever the wind passed through a narrow crack",
        "dialogue": "'The stone has a windy voice,' Luna said. 'Ask it to sing lower,' said the little goat",
        "action": "Luna placed the treasure in a dry pouch, marked the safe path with pebbles, and stayed away from the loose stones",
        "result": "the wind softened, the warning disappeared, and the treasure remained safe in the pouch",
        "ending": "the stones hummed a sleepy tune while the little goat took a triumphant bow",
        "lesson": "a calm investigation can turn a threatening tale into a useful map",
    },
    {
        "key": "splashing_guardian",
        "premise": "a tall shadow guarded the pool, raising an arm whenever moonlight struck the water",
        "problem": "the shadow looked like a giant guardian preparing to block the path",
        "mistake": "Luna raised both arms to look equally giant, but the companion laughed so hard that the shadow shook",
        "clue": "the guardian leaned whenever the willow branch above the pool leaned",
        "dialogue": "'A true guardian would stand straighter,' Luna said. 'This one needs a tree for balance,' said the fox",
        "action": "They moved to a clear, dry place and watched the branch sway without approaching the water",
        "result": "the shadow shrank when the wind calmed, revealing only the willow and its long leaves",
        "ending": "the fox crowned the willow with a fallen leaf and named it Keeper of Wobbly Arms",
        "lesson": "humor is helpful when it makes room for careful noticing instead of reckless daring",
    },
    {
        "key": "underwater_bell",
        "premise": "a bell rang beneath the pool each time a star appeared between the clouds",
        "problem": "the ringing made everyone fear that an ancient spirit was calling swimmers into the dark water",
        "mistake": "Luna answered with a saucepan lid, producing a clang that startled a sleeping duck",
        "clue": "the bell rang only when a thin stream touched a hollow clay jar near the bank",
        "dialogue": "'The spirit has a jar for a throat,' Luna said. 'And your saucepan has no manners,' said the hedgehog",
        "action": "They left the jar where it was, kept clear of the water, and asked an adult to move the path around the slippery bank",
        "result": "the bell became a soft trickle, and no one entered the pool to chase its sound",
        "ending": "the duck settled again while the hedgehog whispered that even ghosts should dry their dishes",
        "lesson": "safe distance and patient listening can solve a mystery without disturbing its world",
    },
]

ASP_RULES = r"""
#show valid/1.
#show story_ok/1.

valid(P) :- params(P), setting(P, moonlit_pool), companion(P, _), treasure(P, _).
story_ok(P) :- valid(P), suspense(P), humor(P), resolved(P), safe(P).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mythic pool storyworld with suspense and humor.")
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--treasure", choices=TREASURES)
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
    treasure = args.treasure or rng.choice(TREASURES)
    if not treasure:
        raise StoryError("A mythic pool story needs a named treasure.")
    return StoryParams(name=name, companion=companion, treasure=treasure)


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("params", "p1"),
        asp.fact("setting", "p1", "moonlit_pool"),
        asp.fact("suspense", "p1"),
        asp.fact("humor", "p1"),
        asp.fact("resolved", "p1"),
        asp.fact("safe", "p1"),
    ]
    for companion in COMPANIONS:
        facts.append(asp.fact("companion", "p1", companion))
    for treasure in TREASURES:
        facts.append(asp.fact("treasure", "p1", treasure.replace(" ", "_")))
    return "\n".join(facts)


def aspire() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_verify() -> int:
    import asp

    model = asp.one_model(aspire())
    valid = set(asp.atoms(model, "valid"))
    accepted = set(asp.atoms(model, "story_ok"))
    if ("p1",) in valid and ("p1",) in accepted:
        print("OK: ASP rules accept the mythic pool world.")
        return 0
    print("Mismatch: ASP rules rejected the mythic pool world.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting != "moonlit pool":
        raise StoryError("This world only supports the moonlit pool setting.")

    world = World(params)
    hero = world.add(Entity(params.name, "character", params.name))
    companion = world.add(Entity("companion", "creature", f"the {params.companion}"))
    treasure = world.add(Entity("treasure", "object", params.treasure))

    stable_seed = params.seed
    if stable_seed is None:
        stable_seed = sum(ord(char) for char in f"{params.name}|{params.companion}|{params.treasure}")
    scenario = SCENARIOS[stable_seed % len(SCENARIOS)]

    values = {
        "name": params.name,
        "companion": params.companion,
        "treasure": params.treasure,
    }
    detail = {
        key: value.format(**values)
        for key, value in scenario.items()
        if key != "key"
    }

    hero.memes.update({"curiosity": 1.0, "courage": 1.0, "humor": 1.0, "care": 1.0})
    companion.memes["alert"] = 1.0
    treasure.meters["dry"] = 1.0
    treasure.meters["safe"] = 1.0

    world.facts.update(
        setting="moonlit pool",
        scenario=scenario["key"],
        suspense=True,
        humor=True,
        safe=True,
        resolved=True,
        clue=detail["clue"],
        danger=detail["problem"],
        action=detail["action"],
        outcome=detail["result"],
        lesson=detail["lesson"],
        entered_pool=False,
    )

    world.say(
        f"Long ago, beneath a moon thin as a silver fingernail, {params.name} came to a quiet pool "
        f"with the {params.companion} and a {params.treasure}. {detail['premise']}."
    )
    world.say(
        f"Then the suspense began. {detail['problem']}. "
        f"{detail['mistake']}. The {params.companion} made a sound that was half gasp and half laugh."
    )
    world.say(
        f"{params.name} did not step into the pool. Instead, the traveler remembered that even old magic "
        f"must leave clues. The clue was simple: {detail['clue']}."
    )
    world.say(
        f"'{detail['dialogue'].split(\"'\")[1]}' {detail['dialogue'].split(\"'\")[2]} "
        f"{detail['dialogue'].split(\"'\")[3]}'"
    )
    world.say(
        f"The joke loosened the fear, but the clue chose the plan. {detail['action']}. "
        f"The treasure stayed dry, and no one reached into the dark water."
    )
    world.say(
        f"At last, {detail['result']}. The pool kept its secret, but the travelers understood its shape: "
        f"{detail['lesson']}."
    )
    world.say(
        f"{detail['ending']}. By dawn, the pool was peaceful again, and {params.name} carried the "
        f"{params.treasure} home as proof that a careful hero can outwit a frightening mystery."
    )

    world.facts.update(hero=hero, companion=companion, treasure=treasure)

    story_qa = [
        QAItem(
            question=f"What made the pool seem mysterious to {params.name}?",
            answer=f"The pool seemed mysterious because {detail['problem']}.",
        ),
        QAItem(
            question="What clue helped solve the suspenseful mystery?",
            answer=f"The important clue was that {detail['clue']}.",
        ),
        QAItem(
            question=f"How did {params.name} act safely?",
            answer=f"{detail['action']}. {params.name} did not enter the pool or reach into the dark water.",
        ),
        QAItem(
            question="How did humor help the travelers?",
            answer=f"The funny exchange softened the fear, but it did not replace careful observation. The travelers used the clue to choose a safe plan.",
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{detail['result']}. {detail['ending']}.",
        ),
        QAItem(
            question="What lesson did the myth teach?",
            answer=f"The myth taught that {detail['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="Why can a pool be dangerous at night?",
            answer="A pool can be dangerous at night because darkness hides depth, slippery edges, and moving water.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of wondering what may happen next while a problem remains uncertain.",
        ),
        QAItem(
            question="Why should people stay on a firm bank near deep water?",
            answer="People should stay on a firm bank because wet edges can be slippery and deep water may be hard to escape.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an imaginative traditional tale that often uses extraordinary events to explore a human lesson.",
        ),
    ]

    prompts = [
        f"Tell a mythic suspense story about {params.name} discovering a mystery at a moonlit pool.",
        f"Write a humorous safe adventure with {params.name}, a {params.companion}, and a {params.treasure}.",
        "Create a child-facing myth in which observation turns a frightening pool mystery into a wise lesson.",
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
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams("Luna", "fox", "silver apple", seed=base_seed),
            StoryParams("Mira", "raven", "star pearl", seed=base_seed + 1),
            StoryParams("Ivo", "little goat", "golden reed", seed=base_seed + 2),
            StoryParams("Nia", "hedgehog", "moonstone", seed=base_seed + 3),
        ]
        samples = [generate(params) for params in presets]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

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
