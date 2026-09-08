#!/usr/bin/env python3
"""A cautionary pirate tale about chowmein, patience, and listening within."""

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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    harbor: str = "Moonlit Cove"
    captain: str = "Luna"
    deckhand: str = "Pip"
    chowmein: str = "a steaming bowl of chowmein"
    seed: Optional[int] = None


HARBORS = {
    "cove": "Moonlit Cove",
    "island": "Parrot Island",
    "bay": "Silver Bay",
    "reef": "Coral Reef Harbor",
}
CAPTAINS = ["Luna", "Mara", "Nell", "Captain Kai"]
DECKHANDS = ["Pip", "Toby", "Mina", "Finn"]
CHOWMEIN = [
    "a steaming bowl of chowmein",
    "a little tin of chowmein",
    "a fragrant basket of chowmein",
]

INCIDENTS = [
    {
        "name": "the impatient shortcut",
        "danger": "a narrow reef passage glittered with hidden rocks",
        "clue": "the tide chart showed the safe channel bending wide around the reef",
        "bad": "sail straight through the gap before the tide could change",
        "captain_job": "read the tide chart aloud",
        "deckhand_job": "watch for the striped buoy",
        "result": "the ship followed the deep-water curve and passed the reef safely",
        "ending": "the chowmein steamed beside the tide chart while the reef gleamed harmlessly astern",
        "lesson": "a quick route is not a wise route when a careful warning is clear",
    },
    {
        "name": "the boastful bell",
        "danger": "a fog bank swallowed the harbor markers",
        "clue": "the bell buoy rang twice, then paused whenever the current turned",
        "bad": "ring the ship's bell wildly and trust the loudest sound",
        "captain_job": "count the bell's pauses",
        "deckhand_job": "keep the lantern low and steady",
        "result": "the ship matched the bell rhythm and reached the quiet harbor mouth",
        "ending": "warm chowmein filled their bowls as the bell chimed softly behind them",
        "lesson": "loud confidence cannot replace patient attention",
    },
    {
        "name": "the hungry hurry",
        "danger": "a sudden squall shoved the ship toward a floating timber",
        "clue": "the wind sock snapped hard from the eastern mast",
        "bad": "grab the chowmein and rush below without securing the sail",
        "captain_job": "call the wind direction",
        "deckhand_job": "tie the loose sail with a firm knot",
        "result": "the sail held, the ship turned, and no one spilled a single bowl",
        "ending": "they shared chowmein under a calm sky, with the tied sail snug above them",
        "lesson": "hunger may ask for haste, but safety must answer first",
    },
    {
        "name": "the tempting treasure",
        "danger": "a bright chest floated beside a patch of churning water",
        "clue": "the chest bobbed toward the whirlpool whenever the waves tugged",
        "bad": "lean over the rail and snatch the treasure at once",
        "captain_job": "measure the distance from the deck",
        "deckhand_job": "lower a rope only after the current weakened",
        "result": "they waited, pulled the chest from still water, and kept every sailor aboard",
        "ending": "the treasure proved to be painted shells, which decorated their chowmein table",
        "lesson": "a glittering prize is never worth risking a friend",
    },
    {
        "name": "the whispering compass",
        "danger": "the compass needle trembled near a field of magnetic stones",
        "clue": "the old map marked a long route around the stones",
        "bad": "smack the compass until it pointed where they wanted",
        "captain_job": "compare the compass with the stars",
        "deckhand_job": "trace the map's safe landmarks",
        "result": "the crew trusted the stars and map and sailed beyond the false needle",
        "ending": "beneath steady stars, they ate chowmein and thanked the patient map",
        "lesson": "forcing an answer does not make it true",
    },
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cautionary pirate chowmein story world.")
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--captain", choices=CAPTAINS)
    parser.add_argument("--deckhand", choices=DECKHANDS)
    parser.add_argument("--chowmein", choices=CHOWMEIN)
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
    captain = args.captain or rng.choice(CAPTAINS)
    deckhand = args.deckhand or rng.choice(DECKHANDS)
    if captain == deckhand:
        deckhand = rng.choice([name for name in DECKHANDS if name != captain])
    return StoryParams(
        harbor=HARBORS[args.harbor or rng.choice(list(HARBORS))],
        captain=captain,
        deckhand=deckhand,
        chowmein=args.chowmein or rng.choice(CHOWMEIN),
    )


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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


def incident_for(params: StoryParams) -> dict[str, str]:
    seed = params.seed if params.seed is not None else 0
    return INCIDENTS[seed % len(INCIDENTS)]


def tell(params: StoryParams) -> World:
    if params.captain == params.deckhand:
        raise StoryError("The captain and deckhand must be different characters.")
    if params.harbor not in HARBORS.values():
        raise StoryError("The harbor must come from the harbor registry.")
    if params.chowmein not in CHOWMEIN:
        raise StoryError("The chowmein must come from the chowmein registry.")

    incident = incident_for(params)
    world = World(params=params)
    captain = world.add(
        Entity(
            "captain",
            "character",
            params.captain,
            "captain",
            meters={"safety": 1.0, "hunger": 0.7},
            memes={"patience": 0.5, "care": 1.0},
            traits=["responsible"],
        )
    )
    deckhand = world.add(
        Entity(
            "deckhand",
            "character",
            params.deckhand,
            "deckhand",
            meters={"safety": 1.0, "hunger": 0.8},
            memes={"curiosity": 1.0, "trust": 0.8},
            traits=["eager"],
        )
    )
    food = world.add(
        Entity(
            "chowmein",
            "food",
            params.chowmein,
            "meal",
            meters={"warmth": 1.0, "hunger_relief": 1.0},
            memes={"comfort": 1.0},
            traits=["fragrant", "shared"],
        )
    )

    world.say(
        f"Under a moon as round as a captain's compass, {captain.label} guided the little ship toward {params.harbor}."
    )
    world.say(
        f"On the galley table waited {food.label}, fragrant enough to make {deckhand.label}'s stomach rumble like a distant cannon."
    )
    world.say(
        f"“Shall we eat now?” asked {deckhand.label}. “The chowmein is calling.”"
    )
    world.say(
        f"{captain.label} smiled, but thought, “A hungry sailor may hurry. I must keep my eyes on the sea before I lift a fork.”"
    )

    world.para()
    world.say(
        f"Then trouble rose: {incident['danger']}. The crew's safe passage depended on noticing that {incident['clue']}."
    )
    world.say(
        f"{deckhand.label} pointed toward the meal. “Perhaps we should {incident['bad']},” {deckhand.label} said."
    )
    world.say(
        f"“Hold fast,” replied {captain.label}. “{incident['lesson'].capitalize()}.”"
    )
    world.say(
        f"Inside, {deckhand.label} wondered, “Could waiting truly help us more than rushing?” The thought changed the deckhand's plan."
    )

    world.para()
    world.say(
        f"{captain.label} decided to {incident['captain_job']}, while {deckhand.label} agreed to {incident['deckhand_job']}."
    )
    world.say(
        f"“Tell me what you notice,” said {captain.label}. “I will listen before I steer.”"
    )
    world.say(
        f"“The warning matches the water,” said {deckhand.label}. “Let us take the careful way.”"
    )
    world.say(f"Together, they worked slowly and {incident['result']}.")
    captain.memes["patience"] += 1.0
    captain.memes["care"] += 1.0
    deckhand.memes["trust"] += 1.0
    deckhand.memes["curiosity"] += 0.5
    captain.meters["safety"] += 1.0
    deckhand.meters["safety"] += 1.0

    world.para()
    world.say(
        f"Only when the danger had passed did {captain.label} uncover {food.label}."
    )
    world.say(
        f"“Now the meal tastes better,” said {deckhand.label}. “We earned it by keeping everyone safe.”"
    )
    world.say(
        f"{captain.label} answered, “A good pirate listens to warnings, even when the treasure is dinner.”"
    )
    world.say(f"{incident['ending']}.")
    world.facts.update(
        captain=captain,
        deckhand=deckhand,
        food=food,
        harbor=params.harbor,
        incident=incident["name"],
        danger=incident["danger"],
        clue=incident["clue"],
        bad=incident["bad"],
        captain_job=incident["captain_job"],
        deckhand_job=incident["deckhand_job"],
        result=incident["result"],
        ending=incident["ending"],
        lesson=incident["lesson"],
        dialogue=True,
        inner_monologue=True,
        cautionary=True,
        safe=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    captain = facts["captain"].label
    deckhand = facts["deckhand"].label
    return [
        f"Write a cautionary pirate tale about {captain} and {deckhand} protecting a bowl of chowmein while sailing near {facts['harbor']}.",
        f"Include an inner monologue in which {captain} or {deckhand} realizes that patience is safer than a tempting shortcut.",
        f"Use dialogue to show how the crew learns that {facts['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    captain = facts["captain"].label
    deckhand = facts["deckhand"].label
    return [
        QAItem(
            question=f"What danger did {captain} and {deckhand} face?",
            answer=f"They faced {facts['danger']}, so they had to pay attention before enjoying their chowmein.",
        ),
        QAItem(
            question=f"What clue helped {captain} and {deckhand} choose safely?",
            answer=f"The important clue was that {facts['clue']}.",
        ),
        QAItem(
            question=f"How did {captain} and {deckhand} divide the work?",
            answer=f"{captain} chose to {facts['captain_job']}, while {deckhand} chose to {facts['deckhand_job']}.",
        ),
        QAItem(
            question="Why did the crew wait before eating the chowmein?",
            answer=f"They waited because safety came first, and {facts['result']}.",
        ),
        QAItem(
            question="What cautionary lesson did the pirates learn?",
            answer=f"They learned that {facts['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should sailors listen to warnings?",
            answer="Warnings can reveal hidden dangers and give people time to choose a safer action.",
        ),
        QAItem(
            question="What is chowmein?",
            answer="Chowmein is a noodle dish that may be cooked with vegetables, sauce, and other ingredients.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private stream of thoughts, shown to the reader but not spoken aloud.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    lines.append(f"facts: {world.facts['incident']}, safe={world.facts['safe']}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_harbor/1.
#show valid_chowmein/1.
valid_harbor(cove).
valid_harbor(island).
valid_harbor(bay).
valid_harbor(reef).
valid_chowmein(steaming).
valid_chowmein(tin).
valid_chowmein(basket).
"""


def asp_facts() -> str:
    import asp

    lines = [asp.fact("harbor", key) for key in HARBORS]
    lines.extend(asp.fact("meal", key) for key in ("steaming", "tin", "basket"))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        harbor_model = asp.one_model(asp_program("#show valid_harbor/1."))
        meal_model = asp.one_model(asp_program("#show valid_chowmein/1."))
        harbor_atoms = sorted(asp.atoms(harbor_model, "valid_harbor"))
        meal_atoms = sorted(asp.atoms(meal_model, "valid_chowmein"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1

    expected_harbors = sorted((key,) for key in HARBORS)
    expected_meals = sorted((key,) for key in ("steaming", "tin", "basket"))
    if harbor_atoms != expected_harbors or meal_atoms != expected_meals:
        print("MISMATCH: ASP registries differ from Python registries.")
        return 1

    for index, params in enumerate(
        [
            StoryParams(seed=index, harbor=harbor, captain="Luna", deckhand="Pip")
            for index, harbor in enumerate(HARBORS.values())
        ]
    ):
        sample = generate(params)
        if not sample.story or "chowmein" not in sample.story:
            print("MISMATCH: generated story failed its chowmein gate.")
            return 1
    print("OK: ASP registries match Python and generated stories pass.")
    return 0


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
    StoryParams(harbor="Moonlit Cove", captain="Luna", deckhand="Pip", seed=0),
    StoryParams(harbor="Parrot Island", captain="Mara", deckhand="Toby", seed=1),
    StoryParams(harbor="Silver Bay", captain="Nell", deckhand="Mina", seed=2),
    StoryParams(harbor="Coral Reef Harbor", captain="Captain Kai", deckhand="Finn", seed=3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_harbor/1.\n#show valid_chowmein/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Valid harbors:")
        for key, label in HARBORS.items():
            print(f"  {key}: {label}")
        print("Valid chowmein forms:")
        for meal in CHOWMEIN:
            print(f"  {meal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and attempt < limit:
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} at {sample.params.harbor}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
