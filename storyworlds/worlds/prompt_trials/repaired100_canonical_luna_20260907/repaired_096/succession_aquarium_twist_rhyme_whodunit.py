#!/usr/bin/env python3
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class SuccessionRule:
    id: str
    title: str
    order: tuple[str, ...]
    clue: str
    rhyme: str
    twist: str


@dataclass(frozen=True)
class Aquarium:
    id: str
    name: str
    landmark: str
    affords: set[str]


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    aquarium: Aquarium
    rule: SuccessionRule
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


AQUARIUMS = {
    "moonlit_aquarium": Aquarium(
        id="moonlit_aquarium",
        name="the Moonlit Aquarium",
        landmark="a glass tunnel where silver fish flashed like commas",
        affords={"shell_succession"},
    )
}

SUCCESSION_RULES = {
    "shell_succession": SuccessionRule(
        id="shell_succession",
        title="the Keeper's Shell succession",
        order=("Nera", "Pip", "Toma"),
        clue="a wet blue thread caught beneath the empty crown stand",
        rhyme="Who follows the tide must read what the bubbles confide.",
        twist="the missing crown had not been stolen at all; the outgoing keeper hid it to test whether the next keeper would follow the written succession rule rather than seize it",
    )
}

NAMES = {
    "girl": ["Luna", "Mira", "Nera", "Sela"],
    "boy": ["Luna", "Pip", "Toma", "Jori"],
}
TRAITS = ["curious", "patient", "sharp-eyed", "kind", "brave"]

OPENINGS = [
    "On the night the Moonlit Aquarium chose its next keeper, every tank glowed blue.",
    "The Moonlit Aquarium was quiet except for bubbles and the tap of a missing crown.",
    "At the aquarium's succession ceremony, the fish swam in a circle that looked almost like a question mark.",
]

@dataclass
class StoryParams:
    place: str
    succession: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place, rule_id)
        for place, aquarium in AQUARIUMS.items()
        for rule_id in aquarium.affords
        if rule_id in SUCCESSION_RULES
    ]


def build_world(params: StoryParams) -> World:
    if params.place not in AQUARIUMS:
        raise StoryError(f"Unknown aquarium: {params.place}")
    if params.succession not in SUCCESSION_RULES:
        raise StoryError(f"Unknown succession rule: {params.succession}")
    if (params.place, params.succession) not in valid_combos():
        raise StoryError("That aquarium does not support the selected succession.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("The hero type must be girl or boy.")

    aquarium = AQUARIUMS[params.place]
    rule = SUCCESSION_RULES[params.succession]
    world = World(aquarium=aquarium, rule=rule)

    hero = world.add(Entity(params.hero_name, params.hero_name, params.hero_type))
    outgoing = world.add(Entity("Nera", "Nera, the outgoing keeper", "keeper"))
    witness = world.add(Entity("Pip", "Pip, the pearl diver", "witness"))
    crown = world.add(Entity("crown", "the coral crown", "relic"))

    rng = random.Random(params.seed)
    opening = rng.choice(OPENINGS)
    wrong_suspect = rng.choice(["Pip", "the sleepy seal", "the night guard"])
    investigation = rng.choice([
        "counted the empty hooks and compared them with the ceremony ledger",
        "asked each witness where they had stood when the lights flickered",
        "followed the trail without touching a single wet mark",
    ])
    extra_line = rng.choice([
        "The smallest fish nudged a shell toward the clue.",
        "A crab lifted one claw as if it, too, had noticed the pattern.",
        "The eels blinked in a row, making the clue seem almost underlined.",
    ])

    world.facts.update(
        hero=hero,
        outgoing=outgoing,
        witness=witness,
        crown=crown,
        wrong_suspect=wrong_suspect,
        investigation=investigation,
        clue=rule.clue,
        rhyme=rule.rhyme,
        twist=rule.twist,
        solved=True,
    )

    world.say(opening)
    world.say(
        f"{params.hero_name}, a {params.trait} {params.hero_type}, had come to witness the succession of aquarium keepers. "
        f"Above the coral desk hung a brass list: first {rule.order[0]}, then {rule.order[1]}, then {rule.order[2]}."
    )
    world.say(
        f"But when the bell rang, the coral crown was gone. Without it, nobody knew whether the succession should continue."
    )
    world.para()
    world.say(
        f"Captain Nera frowned at {wrong_suspect}. “The crown vanished near your station,” she said."
    )
    world.say(
        f"“That is not proof,” {params.hero_name} replied. “Let us ask what the aquarium remembers.”"
    )
    world.say(f"{params.hero_name} {investigation}.")
    world.say(f"The first clue was {rule.clue}. {extra_line}")
    world.say(
        f"Pip pointed to a trail of bubbles. “They rise from the old lesson tank,” he said."
    )
    world.say(
        f"“And this rhyme is scratched beside it,” {params.hero_name} answered: “{rule.rhyme}”"
    )
    world.para()
    world.say(
        f"The trail led beneath a model ship, where the coral crown rested inside a dry bucket. "
        f"The twist was clear: {rule.twist}."
    )
    world.say(
        f"Nera lowered her head. “I wanted the next keeper to understand that a title is inherited by trust, not grabbed by speed.”"
    )
    world.say(
        f"“Then the succession can proceed honestly,” {params.hero_name} said. “Pip follows you, and the aquarium will record why.”"
    )
    world.say(
        f"Nera placed the crown on Pip's head, and Pip placed the ledger in {params.hero_name}'s hands for the next ceremony."
    )
    world.para()
    world.say(
        f"The fish gathered beneath the glass tunnel as the new succession was announced: {rule.order[0]}, then {rule.order[1]}, then {rule.order[2]}."
    )
    world.say(
        f"The aquarium grew calm again. The final lesson was simple: a careful detective protects both the truth and the order that makes trust possible."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit about a missing succession crown in {world.aquarium.name}.",
        f"Include the clue '{f['clue']}', a rhyme, and the twist that {f['twist']}.",
        "End with a fair succession ceremony that proves the mystery has been solved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rule = world.rule
    return [
        QAItem(
            "What disappeared at the aquarium ceremony?",
            "The coral crown disappeared, and the keepers needed it to mark the next succession.",
        ),
        QAItem(
            f"How did {hero.label} investigate?",
            f"{hero.label} {f['investigation']} and followed the clue instead of accusing someone without proof.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The clue was {f['clue']}. It led the investigators toward the old lesson tank.",
        ),
        QAItem(
            "What was the twist?",
            f"The twist was that {f['twist']}.",
        ),
        QAItem(
            "Who became the next keeper?",
            f"{rule.order[1]} became the next keeper after {rule.order[0]}, because the written succession order was checked and followed.",
        ),
        QAItem(
            "What lesson did the mystery teach?",
            "It taught that succession should follow a trusted rule and that careful evidence matters more than a quick accusation.",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        "What is an aquarium?",
        "An aquarium is a place or container where water animals and plants are kept so people can observe them.",
    ),
    QAItem(
        "What is succession?",
        "Succession is the process by which one person or group follows another in an important role.",
    ),
    QAItem(
        "What is a whodunit?",
        "A whodunit is a mystery story in which readers look for clues to discover who caused an event.",
    ),
    QAItem(
        "What is a rhyme?",
        "A rhyme is a pair or group of words with matching or similar ending sounds.",
    ),
    QAItem(
        "What is a twist in a story?",
        "A twist is a surprising change in what the reader thought was happening.",
    ),
]


def asp_facts() -> str:
    import asp
    lines = []
    for place, aquarium in AQUARIUMS.items():
        lines.append(asp.fact("aquarium", place))
        for rule in sorted(aquarium.affords):
            lines.append(asp.fact("supports", place, rule))
    for rule in SUCCESSION_RULES:
        lines.append(asp.fact("succession", rule))
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/2.
valid(A, S) :- aquarium(A), succession(S), supports(A, S).
"""


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("ASP/Python mismatch.")
        print("Only Python:", sorted(py - cl))
        print("Only ASP:", sorted(cl - py))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combinations), and generated stories passed.")
    return 0


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.succession:
        combos = [c for c in combos if c[1] == args.succession]
    if not combos:
        raise StoryError("No compatible aquarium and succession choices remain.")
    place, succession = rng.choice(combos)
    hero_type = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[hero_type])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, succession, name, hero_type, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=list(WORLD_KNOWLEDGE),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"aquarium: {world.aquarium.name}")
    lines.append(f"succession: {world.rule.title}")
    lines.append(f"resolved: {world.facts.get('solved')}")
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    return "\n".join(lines)


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="moonlit_aquarium",
        succession="shell_succession",
        hero_name="Luna",
        hero_type="girl",
        trait="curious",
        seed=96096,
    )
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A child-facing aquarium succession whodunit with a rhyme and a twist."
    )
    parser.add_argument("--place", choices=sorted(AQUARIUMS))
    parser.add_argument("--succession", choices=sorted(SUCCESSION_RULES))
    parser.add_argument("--name")
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        for place, succession in asp_valid_combos():
            print(f"{place}: {succession}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
