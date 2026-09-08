#!/usr/bin/env python3
"""A child-safe meadow adventure about a tremble, kindness, and brave choices."""

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


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Meadow:
    key: str
    name: str
    landmark: str
    weather: str
    sound: str


@dataclass(frozen=True)
class Adventure:
    key: str
    danger: str
    clue: str
    first_guess: str
    test: str
    truth: str
    kindness: str
    consequence: str
    ending: str
    lesson: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero: str = "Luna"
    hero_kind: str = "girl"
    companion: str = "Tavi"
    meadow: str = "sunny_meadow"
    adventure: str = "shivering_fawn"
    weather: str = "morning"
    narrative_mode: int = 0
    dialogue_mode: int = 0
    turn_mode: int = 0


class World:
    def __init__(self, meadow: Meadow):
        self.meadow = meadow
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


MEADOWS = {
    "sunny_meadow": Meadow(
        "sunny_meadow",
        "Dandelion Meadow",
        "a leaning stone under an old oak",
        "golden morning",
        "bees humming over the clover",
    ),
    "misty_meadow": Meadow(
        "misty_meadow",
        "Mistbell Meadow",
        "a narrow wooden footbridge",
        "cool morning mist",
        "water whispering through reeds",
    ),
    "hill_meadow": Meadow(
        "hill_meadow",
        "Windstep Meadow",
        "a ring of white stones",
        "bright hilltop wind",
        "grass brushing the fence posts",
    ),
}

ADVENTURES = {
    "shivering_fawn": Adventure(
        "shivering_fawn",
        "a young fawn was trapped behind a fallen branch beside the meadow path",
        "tiny hoofprints stopped where the tall grass bent toward the stream",
        "the fawn had run away from the herd because it was frightened",
        "follow the hoofprints from the dry path and listen before stepping closer",
        "the fawn was not lost; one leg was caught under a light branch, and the herd waited beyond the reeds",
        "speak softly, keep a safe distance, and ask the forest ranger to lift the branch",
        "The fawn drank from the stream after the ranger freed its leg.",
        "The meadow grew quiet until the fawn took one careful step toward its family.",
        "Kindness means helping without making a frightened creature feel more afraid.",
    ),
    "whispering_nest": Adventure(
        "whispering_nest",
        "a nest had fallen into a patch of tall grass during a sudden gust",
        "three pale feathers pointed from the grass toward a low hawthorn",
        "a fox had carried the nest away",
        "compare the feathers with nests in nearby branches and watch from the path",
        "the wind had rolled the nest downhill, while the parent birds circled above it",
        "make a small sign to keep walkers back and tell the wildlife keeper",
        "The keeper returned the nest to a sheltered fork while the children watched.",
        "The parent bird landed nearby when the grass stopped shaking.",
        "Kindness gives small lives room to recover instead of rushing them.",
    ),
    "lost_bell": Adventure(
        "lost_bell",
        "a little brass bell had vanished from the meadow's sheep gate",
        "a bright scrape curved from the gate toward a muddy puddle",
        "someone had taken the bell as a prize",
        "compare the scrape with the gate hinge and search only from the marked path",
        "the loose hinge had carried the bell down the slope when the gate swung in the wind",
        "tell the shepherd and help hold the gate while an adult retrieves the bell",
        "The shepherd fastened the bell after clearing the hinge.",
        "Its gentle chime guided the sheep home before sunset.",
        "Kindness can protect people and animals by noticing a small problem early.",
    ),
    "storm_lantern": Adventure(
        "storm_lantern",
        "a trail lantern trembled on its hook as dark clouds gathered",
        "wet footprints led away from the lantern toward the old shelter",
        "a careless traveler had left the lantern burning",
        "count the footprints and ask who had used the shelter before touching anything",
        "a tired hedgehog had brushed the hook while seeking a dry corner; the flame was already out",
        "keep back from the lantern and ask the ranger to secure it before the rain",
        "The ranger tied the lantern safely beneath the shelter roof.",
        "Rain tapped the roof while the lantern shone steadily beside the resting hedgehog.",
        "Kindness includes care for a place and every creature sharing it.",
    ),
    "butterfly_bridge": Adventure(
        "butterfly_bridge",
        "a cloud of butterflies fluttered low above a bridge blocked by a fallen reed bundle",
        "yellow wings gathered on one side of the bridge",
        "the butterflies were trapped by a dangerous swarm",
        "watch the wind and see whether the butterflies choose the same flowers",
        "the reed bundle hid the bridge's sunny opening, so the butterflies were following the only warm patch",
        "ask the groundskeeper to move the reeds while everyone waits at the railing",
        "The path opened, and the butterflies drifted across without being touched.",
        "Luna watched their yellow wings settle on flowers beyond the bridge.",
        "Kindness lets living things choose their own safe way forward.",
    ),
}

HEROES = {"Luna": "girl", "Milo": "boy", "Nia": "girl", "Rowan": "child"}
COMPANIONS = ("Tavi", "Grandma Bea", "Rin", "Uncle Sol")

OPENINGS = (
    "Luna loved adventures that began with a quiet path and an unanswered question.",
    "The meadow looked peaceful, but the grass was trembling in one unusual place.",
    "At sunrise, Luna and Tavi entered the meadow with careful feet and curious eyes.",
    "A breeze ran through the flowers as a small meadow mystery began.",
    "The adventure started when Luna heard a sound softer than a birdcall.",
    "Beyond the gate, the meadow glittered with dew and seemed to hold its breath.",
)

DIALOGUES = (
    '"Let us look first and hurry second," Tavi said.',
    '"A frightened friend needs space as well as help," said Tavi.',
    '"Tell me what you know, and we can decide what to do," Tavi suggested.',
    '"Kindness is brave when it protects someone smaller than us," Tavi said.',
    '"We should ask an adult before we touch anything risky," Tavi reminded Luna.',
    '"The clue may explain what happened, but it does not tell us to blame anyone," said Tavi.',
)

TURN_BRIDGES = (
    "Their careful test changed the adventure.",
    "The next clue made the meadow mystery gentler and clearer.",
    "That was the turning point: the sound had a cause, but not the cause Luna first imagined.",
    "When they stopped guessing and started observing, the path showed them what to do.",
    "The meadow offered one more fact, and it changed a worried guess into a helpful plan.",
)

ASP_RULES = r"""
meadow(M) :- meadow_fact(M).
adventure(A) :- adventure_fact(A).
kind_action(A) :- adventure_fact(A), adult_help(A).
safe_choice(A) :- adventure_fact(A), adult_help(A), no_touching_danger(A).
resolved(A) :- adventure_fact(A), kind_action(A), safe_choice(A).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("meadow_fact", key) for key in MEADOWS]
    lines += [asp.fact("adventure_fact", key) for key in ADVENTURES]
    lines += [asp.fact("adult_help", key) for key in ADVENTURES]
    lines += [asp.fact("no_touching_danger", key) for key in ADVENTURES]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Meadow adventure about tremble and kindness.")
    parser.add_argument("--hero")
    parser.add_argument("--companion")
    parser.add_argument("--meadow", choices=sorted(MEADOWS))
    parser.add_argument("--adventure", choices=sorted(ADVENTURES))
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
    hero = args.hero or rng.choice(list(HEROES))
    meadow = args.meadow or rng.choice(list(MEADOWS))
    adventure = args.adventure or rng.choice(list(ADVENTURES))
    return StoryParams(
        seed=args.seed,
        hero=hero,
        hero_kind=HEROES.get(hero, "child"),
        companion=args.companion or rng.choice(COMPANIONS),
        meadow=meadow,
        adventure=adventure,
        weather=rng.choice(["morning", "afternoon", "early evening"]),
        narrative_mode=rng.randrange(len(OPENINGS)),
        dialogue_mode=rng.randrange(len(DIALOGUES)),
        turn_mode=rng.randrange(len(TURN_BRIDGES)),
    )


def tell(params: StoryParams) -> World:
    if params.meadow not in MEADOWS:
        raise StoryError(f"Unknown meadow: {params.meadow}")
    if params.adventure not in ADVENTURES:
        raise StoryError(f"Unknown adventure: {params.adventure}")
    if not params.hero.strip() or not params.companion.strip():
        raise StoryError("Hero and companion names must not be empty.")

    meadow = MEADOWS[params.meadow]
    adventure = ADVENTURES[params.adventure]
    world = World(meadow)

    hero = world.add(Entity(params.hero, params.hero_kind, params.hero, location=meadow.name))
    companion = world.add(Entity(params.companion, "adult", params.companion, location=meadow.name))
    hero.memes.update(curiosity=1.0, kindness=1.0, courage=0.5)
    companion.memes.update(wisdom=1.0, kindness=1.0)

    world.say(OPENINGS[params.narrative_mode])
    world.say(
        f"On a {params.weather}, {hero.label} and {companion.label} walked through "
        f"{meadow.name}, where {meadow.sound} filled the air."
    )
    world.say(
        f"Near {meadow.landmark}, something began to tremble: {adventure.danger}."
    )
    world.para()

    world.say(f"Luna noticed that {adventure.clue}.")
    world.say(f"At first, {hero.label} wondered whether {adventure.first_guess}.")
    world.say(DIALOGUES[params.dialogue_mode].replace("Luna", hero.label))
    world.say(
        f"Instead of rushing in, {hero.label} decided to {adventure.test}."
    )
    world.say(f"The careful look showed that {adventure.truth}.")
    world.say(TURN_BRIDGES[params.turn_mode])

    world.para()
    world.say(
        f"{companion.label} helped {hero.label} make a kind plan: {adventure.kindness}."
    )
    world.say(f"Because they waited and worked gently, {adventure.consequence}")
    world.say(adventure.ending)
    world.say(
        f"{hero.label} smiled and said, \"I was worried, but kindness helped us find the right way.\""
    )
    world.say(adventure.lesson)

    hero.meters.update(distance=0.8, safety=1.0, helpfulness=1.0)
    world.facts.update(
        hero=hero,
        companion=companion,
        meadow=meadow,
        adventure=adventure,
        first_guess=adventure.first_guess,
        test=adventure.test,
        truth=adventure.truth,
        kindness=adventure.kindness,
        resolved=True,
        safe=True,
    )
    world.trace.extend(
        (
            f"meadow:{meadow.key}",
            f"adventure:{adventure.key}",
            f"clue:{adventure.clue}",
            f"test:{adventure.test}",
            f"truth:{adventure.truth}",
            f"kindness:{adventure.kindness}",
            "resolved:True",
        )
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]
    adventure: Adventure = world.facts["adventure"]
    meadow: Meadow = world.facts["meadow"]
    return [
        f"Write an adventure about {hero.label} in {meadow.name}.",
        f"Include a meadow that seems to tremble because {adventure.danger}.",
        f"Show kindness through this safe plan: {adventure.kindness}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    meadow: Meadow = world.facts["meadow"]
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            question=f"Where did {hero.label} go?",
            answer=f"{hero.label} went to {meadow.name}, near {meadow.landmark}.",
        ),
        QAItem(
            question="What made the meadow adventure worrying?",
            answer=f"It was worrying because {adventure.danger}.",
        ),
        QAItem(
            question=f"What did {hero.label} first wonder?",
            answer=f"{hero.label} first wondered whether {adventure.first_guess}.",
        ),
        QAItem(
            question=f"How did {hero.label} and {companion.label} investigate safely?",
            answer=f"They decided to {adventure.test}, instead of rushing toward the danger.",
        ),
        QAItem(
            question="What was really happening?",
            answer=f"They discovered that {adventure.truth}.",
        ),
        QAItem(
            question="How did kindness solve the problem?",
            answer=f"They showed kindness when they chose to {adventure.kindness}.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=adventure.ending,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    adventure: Adventure = world.facts["adventure"]
    return [
        QAItem(
            question="Why should children ask an adult before helping near a wild animal or damaged trail?",
            answer="An adult can judge the danger and use the right tools, while children stay at a safe distance.",
        ),
        QAItem(
            question="What does kindness look like in an adventure?",
            answer="Kindness means noticing who needs help, avoiding extra fear or harm, and choosing a safe action that respects living things.",
        ),
        QAItem(
            question="Why is observing better than guessing?",
            answer=f"Observation revealed that {adventure.truth}, so the characters could help without blaming or rushing.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.extend(f"  {entry}" for entry in world.trace)
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}) location={entity.location} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts={sorted(world.facts)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hero="Luna",
        hero_kind="girl",
        companion="Tavi",
        meadow="sunny_meadow",
        adventure="shivering_fawn",
        narrative_mode=0,
        dialogue_mode=1,
        turn_mode=0,
    ),
    StoryParams(
        hero="Milo",
        hero_kind="boy",
        companion="Grandma Bea",
        meadow="misty_meadow",
        adventure="storm_lantern",
        narrative_mode=3,
        dialogue_mode=3,
        turn_mode=2,
    ),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1

    show = (
        "#show meadow/1.\n"
        "#show adventure/1.\n"
        "#show kind_action/1.\n"
        "#show safe_choice/1.\n"
        "#show resolved/1.\n"
    )
    model = asp.one_model(asp_program(show))
    if not model:
        print("ASP produced no model.")
        return 1
    required = {"meadow", "adventure", "kind_action", "safe_choice", "resolved"}
    names = {symbol.name for symbol in model}
    if not required.issubset(names):
        print("ASP parity check failed.")
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("resolved"):
            print("Python story verification failed.")
            return 1
    print("OK: ASP and Python verification passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def main() -> None:
    args = build_parser().parse_args()
    show = (
        "#show meadow/1.\n"
        "#show adventure/1.\n"
        "#show kind_action/1.\n"
        "#show safe_choice/1.\n"
        "#show resolved/1.\n"
    )

    if args.show_asp:
        print(asp_program(show))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        samples = []
        for offset in range(args.n):
            params = resolve_params(args, random.Random(base_seed + offset))
            params.seed = base_seed + offset
            samples.append(generate(params))

    if args.asp:
        try:
            import asp
        except Exception as exc:
            raise StoryError(f"ASP unavailable: {exc}") from exc
        model = asp.one_model(asp_program(show))
        print(json.dumps({"asp_atoms": [str(atom) for atom in model]}, indent=2))
        return

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
