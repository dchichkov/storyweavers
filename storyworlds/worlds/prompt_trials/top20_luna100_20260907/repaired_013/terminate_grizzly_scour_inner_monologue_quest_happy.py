#!/usr/bin/env python3
"""
A child-facing superhero quest about a grizzly, a dangerous scour, and the
choice to terminate the danger without harming anyone.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class StoryParams:
    setting: str = "Beacon City"
    hero: str = "Luna"
    partner: str = "Pip"
    grizzly: str = "Bruno"
    seed: Optional[int] = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.name] = entity
        return entity


SETTING_REGISTRY = {
    "Beacon City": {"mood": "bright and busy", "landmark": "the Skyway Bridge"},
    "Harbor Heights": {"mood": "windy and glittering", "landmark": "the lighthouse pier"},
    "Willow Metro": {"mood": "green and humming", "landmark": "the old train station"},
}


@dataclass(frozen=True)
class Quest:
    title: str
    danger: str
    discovery: str
    choice: str
    action: str
    resolution: str
    ending: str
    danger_answer: str
    discovery_answer: str
    choice_answer: str
    resolution_answer: str


QUESTS = [
    Quest(
        "The Grizzly Beneath the Bridge",
        "A black cloud of cleaning scour rolled beneath the Skyway Bridge and made the road slippery.",
        "Luna found Bruno the grizzly trapped beside a humming drain, not causing the trouble but frightened by it.",
        "She thought, *I can terminate the scour without turning Bruno into an enemy.*",
        "Luna sent a soft blue signal to the city pipes while Pip led Bruno toward a sunny patch of grass.",
        "The scour drained into a sealed tank, and Bruno stepped safely into the park.",
        "That evening, Bruno napped beside Luna's cape while the bridge lights blinked like friendly stars.",
        "The cleaning scour made the bridge slippery and trapped Bruno beside a humming drain.",
        "Luna discovered that Bruno was frightened and trapped, rather than being the cause of the danger.",
        "She chose to terminate the scour safely while helping Bruno instead of attacking him.",
        "The scour flowed into a sealed tank, and Bruno reached the park safely.",
    ),
    Quest(
        "The Grizzly's Lost Roar",
        "A loud machine began a street-cleaning scour that chased every bird from the town square.",
        "The machine's roar had startled Bruno, who was hiding inside the fountain tunnel.",
        "Luna thought, *A hero must scour the problem from its roots, not simply silence a scared friend.*",
        "She followed the pipes, found a loose copper bell, and tied it still while Pip spoke calmly to Bruno.",
        "The machine became quiet, the birds returned, and Bruno padded out without a growl.",
        "Bruno received a basket of berries, and his gentle snore became the square's happiest new sound.",
        "The machine's loud scour drove birds away and frightened Bruno into the fountain tunnel.",
        "Luna learned that a loose copper bell caused the frightening roar.",
        "She investigated and fixed the real problem while Pip comforted Bruno.",
        "The machine grew quiet, the birds returned, and Bruno came out safely.",
    ),
    Quest(
        "The Golden Trail",
        "A glittering scour of tiny metal flakes spread from the city's inventor lab toward the river.",
        "The trail ended at Bruno's den because he had followed the bright flakes, believing they were stars.",
        "Luna thought, *I must terminate the spill and protect the curious grizzly at the same time.*",
        "She raised a magnetic shield, and Pip scattered plain white stones to make a safe trail home.",
        "The shield drew every flake into a jar, and Bruno followed the stones away from the river.",
        "The inventor thanked Bruno with a honey cake, and the grizzly watched the cleaned river sparkle.",
        "Metal flakes from the lab spread toward the river and led Bruno to his den.",
        "Luna decided to stop the spill while guiding Bruno away from the river.",
        "Her magnetic shield collected the flakes, and Bruno followed a safe trail home.",
    ),
    Quest(
        "The Rooftop Rescue",
        "A rainstorm pushed a strong scour across the rooftops, sweeping toys and flowerpots toward the edge.",
        "Bruno had climbed up after a red kite and now trembled on a narrow roof.",
        "Luna thought, *First I will terminate the rushing water; then I will give my big friend a way down.*",
        "She planted her solar shield over the drain while Pip lowered a padded rescue ramp.",
        "The water slowed, and Bruno walked down the ramp with the kite tucked gently in his paws.",
        "Children cheered from the windows as Bruno returned the kite and received a shining red badge.",
        "Storm water swept across the roofs, leaving Bruno stranded beside a red kite.",
        "Luna planned to stop the rushing water before rescuing Bruno.",
        "Her shield slowed the scour, and a padded ramp brought Bruno safely down.",
    ),
    Quest(
        "The Quiet City Signal",
        "A strange green scour covered the city's signal tower and made every traffic light blink at once.",
        "Luna realized the green glow came from a harmless rescue flare stuck in a vent.",
        "She thought, *I should scour away the confusion, not destroy the tower that guides people home.*",
        "She asked Bruno to sniff out the vent while Pip counted the safe blinking pattern.",
        "Together they removed the flare, and Luna reset the lights before any car moved.",
        "The tower shone steadily, and Bruno became the city's official signal-safety mascot.",
        "A green glow confused the traffic lights and looked like a dangerous scour.",
        "Luna learned that a rescue flare in a vent caused the glow.",
        "She chose to investigate and remove the flare instead of destroying the tower.",
        "Bruno found the vent, the flare was removed, and Luna reset the lights safely.",
    ),
]


OPENINGS = [
    "{hero} was Beacon City's young superhero, and {partner} was the clever friend who carried the emergency map.",
    "When the city lights began to flicker, {hero} zipped across {setting} with {partner close behind.",
    "Every superhero quest begins with a question. For {hero}, today's question arrived over the radio from {setting}.",
    "The people of {setting} knew {hero} could fly, but they also knew the hero stopped to listen.",
]


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum((i + 1) * ord(c) for i, c in enumerate(
        "|".join((params.setting, params.hero, params.partner, params.grizzly))
    ))


def _fill(text: str, facts: dict[str, object]) -> str:
    return text.format(**facts)


def _cap(text: str) -> str:
    return text[:1].upper() + text[1:]


def _story_lines(world: World) -> list[str]:
    f = world.facts
    quest: Quest = f["quest"]
    opening = _fill(OPENINGS[f["opening_variant"]], f)
    lines = [
        opening,
        f"{quest.danger} {quest.discovery}",
        f'"What should we do?" asked {f["partner"]}. {f["hero"]} took a breath and thought, "{quest.choice.split("*")[1] if "*" in quest.choice else quest.choice}"',
        f"{quest.action}",
        f"{quest.resolution} \"A true hero protects frightened creatures, too,\" said {f['partner']}.",
        f"{quest.ending} That was the happy ending to the quest called \"{quest.title}.\"",
    ]
    return lines


ASP_RULES = r"""
place(beacon_city).
place(harbor_heights).
place(willow_metro).
threat(scour).
creature(grizzly).
feature(inner_monologue).
feature(quest).
feature(happy_ending).
hero_can_help(P) :- place(P), threat(scour), creature(grizzly),
                     feature(inner_monologue), feature(quest),
                     feature(happy_ending).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTING_REGISTRY:
        lines.append(asp.fact("place", place.lower().replace(" ", "_")))
    lines.extend([
        asp.fact("threat", "scour"),
        asp.fact("creature", "grizzly"),
        asp.fact("feature", "inner_monologue"),
        asp.fact("feature", "quest"),
        asp.fact("feature", "happy_ending"),
    ])
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A superhero quest about Luna, a grizzly, and a dangerous scour."
    )
    parser.add_argument("--setting", choices=list(SETTING_REGISTRY))
    parser.add_argument("--hero")
    parser.add_argument("--partner")
    parser.add_argument("--grizzly")
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    hero = args.hero or rng.choice(["Luna", "Nova", "Skye", "Milo"])
    partner = args.partner or rng.choice(["Pip", "Tess", "Ravi", "Juno"])
    grizzly = args.grizzly or rng.choice(["Bruno", "Maple", "Gus", "Bear"])
    if hero == partner:
        raise StoryError("The hero and partner must be different characters.")
    if hero == grizzly or partner == grizzly:
        raise StoryError("The grizzly must have a character name different from the helpers.")
    return StoryParams(setting=setting, hero=hero, partner=partner, grizzly=grizzly)


def generate(params: StoryParams) -> StorySample:
    seed = _stable_seed(params)
    quest = QUESTS[seed % len(QUESTS)]
    world = World(params.setting)

    hero = world.add(Entity(
        params.hero, "superhero",
        meters={"speed": 0.9, "power": 0.8},
        memes={"courage": 1.0, "care": 1.0},
    ))
    partner = world.add(Entity(
        params.partner, "helper",
        meters={"mobility": 0.6},
        memes={"cleverness": 1.0, "care": 1.0},
    ))
    grizzly = world.add(Entity(
        params.grizzly, "grizzly",
        meters={"safety": 0.25, "fear": 0.8},
        memes={"trust": 0.2},
    ))
    scour = world.add(Entity(
        "the dangerous scour", "threat",
        meters={"spread": 0.8, "harm": 0.7},
        memes={"confusion": 0.7},
    ))
    world.add(Entity(
        "the sealed tank", "safety_device",
        meters={"capacity": 1.0},
        memes={"protection": 1.0},
    ))

    world.facts.update({
        "hero": hero.name,
        "partner": partner.name,
        "grizzly": grizzly.name,
        "setting": params.setting,
        "quest": quest,
        "opening_variant": (seed // len(QUESTS)) % len(OPENINGS),
        "theme": "terminate, grizzly, scour, inner monologue, quest, happy ending",
        "danger": quest.danger,
        "resolution": quest.resolution,
    })

    if "scour" not in quest.danger.lower() and "scour" not in quest.discovery.lower():
        raise StoryError("Generated quest lost the required scour danger.")
    if "grizzly" not in quest.discovery.lower() and params.grizzly.lower() not in quest.discovery.lower():
        raise StoryError("Generated quest lost its grizzly encounter.")

    story = "\n\n".join(_story_lines(world))
    prompts = [
        f"Write a superhero story about {params.hero} protecting a grizzly in {params.setting}.",
        "Tell a child-friendly quest where a hero must terminate a dangerous scour without hurting a frightened animal.",
        "Use an inner monologue, a brave rescue, and a happy ending.",
    ]
    story_qa = [
        QAItem(
            question=f"What danger did {params.hero} face in the quest called \"{quest.title}\"?",
            answer=quest.danger_answer,
        ),
        QAItem(
            question=f"What did {params.hero} discover about {params.grizzly}?",
            answer=quest.discovery_answer,
        ),
        QAItem(
            question="What choice did the hero make?",
            answer=quest.choice_answer,
        ),
        QAItem(
            question="How did the quest end?",
            answer=quest.resolution_answer,
        ),
        QAItem(
            question=f"What happy ending image closes \"{quest.title}\"?",
            answer=f"The story closes with {quest.ending}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear that needs space, safety, and respect."
        ),
        QAItem(
            question="What does terminate mean?",
            answer="To terminate something means to bring it to an end."
        ),
        QAItem(
            question="What is a scour?",
            answer="A scour is a strong washing or rushing flow that can strip or carry things away."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thought written in words."
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the danger is resolved and people or creatures are safe."
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.name}: kind={entity.kind}, "
                f"meters={dict(entity.meters)}, memes={dict(entity.memes)}"
            )
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


def _valid_python() -> list[str]:
    return sorted(place.lower().replace(" ", "_") for place in SETTING_REGISTRY)


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show hero_can_help/1."))
    return sorted(set(asp.atoms(model, "hero_can_help")))


def asp_verify() -> int:
    import asp
    expected = {(place,) for place in _valid_python()}
    program = asp_program("#show hero_can_help/1.")
    actual = set(asp.atoms(asp.one_model(program), "hero_can_help"))
    if expected != actual:
        print("MISMATCH between clingo and python:")
        print("python only:", sorted(expected - actual))
        print("clingo only:", sorted(actual - expected))
        return 1
    for index, place in enumerate(SETTING_REGISTRY):
        params = StoryParams(
            setting=place,
            hero="Luna",
            partner="Pip",
            grizzly="Bruno",
            seed=index,
        )
        sample = generate(params)
        required = ("terminate", "grizzly", "scour")
        if not all(word in sample.story.lower() for word in required):
            print(f"Generation check failed for {place}.")
            return 1
    print(f"OK: clingo gate matches python ({len(expected)} settings), and stories pass.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hero_can_help/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in _asp_valid():
            print(item[0])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTING_REGISTRY:
            samples.append(generate(StoryParams(
                setting=setting,
                hero="Luna",
                partner="Pip",
                grizzly="Bruno",
                seed=base_seed,
            )))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 50):
            seed = base_seed + attempt
            attempt += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError as error:
                print(error)
                return
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
