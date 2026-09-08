#!/usr/bin/env python3
"""
A small pirate tale about triumph through industry, reconciliation, and kindness.
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
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)
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
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    captain: str
    trait: str
    incident: str
    telling_mode: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Incident:
    title: str
    beginning: str
    conflict: str
    first_try: str
    clue: str
    action: str
    reconciliation: str
    resolution: str
    lesson: str
    ending: str
    question: str
    answer: str


INCIDENTS = [
    Incident(
        "the torn sail",
        "The crew planned to cross Brightwater Bay before sunset.",
        "A sharp wind tore the little ship's main sail, and two deckhands blamed each other for tying the old knot.",
        "Luna tried to pull the sail tight alone, but the cloth flapped harder and the mast groaned.",
        "She found that the rope had worn thin where it rubbed against a rough ring.",
        "Luna asked both deckhands to help: one held the spar while the other fetched a strong spare rope.",
        "The deckhands apologized and tied the new knot together, choosing teamwork over blame.",
        "Their industry mended the sail before dusk, and the ship reached the quiet harbor safely.",
        "Kindness can turn an argument into useful work.",
        "At sunset, the repaired sail shone gold above three friends sharing a warm loaf.",
        "What helped the crew repair the torn sail?",
        "Luna discovered that a worn rope had caused the trouble, and the deckhands worked together with a strong spare rope.",
    ),
    Incident(
        "the empty water cask",
        "The pirate crew was rowing toward an island where a sick seabird needed help.",
        "Their water cask was empty, and the youngest deckhand feared the others would scold him for forgetting the lid.",
        "Luna started bailing seawater into the cask, hoping hard work could make it fresh.",
        "The captain showed her a small rain cloth folded beneath the bench.",
        "They spread the cloth, caught clean rain, and shared the last cup with the thirsty deckhand.",
        "The deckhand admitted his mistake, and the captain answered with kindness instead of anger.",
        "The crew reached the island, gave the seabird water, and filled the cask from a spring.",
        "Kindness makes room for honest mistakes and better choices.",
        "The seabird lifted one bright wing beside a full blue cask.",
        "How did the crew get fresh water?",
        "They caught rain in a clean cloth, shared their last cup, and later filled the cask at an island spring.",
    ),
    Incident(
        "the stubborn anchor",
        "The ship needed to leave a rocky cove before the tide turned.",
        "The anchor would not rise, and the boatswain said the cabin boy had dropped it in the wrong place.",
        "Luna tugged the chain until her boots slid across the deck.",
        "A pale line beneath the water showed that the anchor had caught on a fallen branch.",
        "She lowered a hook, and the boatswain helped guide it around the branch.",
        "The boatswain thanked the cabin boy for spotting the branch and admitted that his first guess was unfair.",
        "The anchor came free, and the ship sailed on the turning tide.",
        "A careful look can reconcile people faster than a loud accusation.",
        "The anchor rested safely on deck while the boatswain and cabin boy shared the steering wheel.",
        "Why would the anchor not rise?",
        "It had caught on a fallen branch beneath the water, not because the cabin boy had placed it badly.",
    ),
    Incident(
        "the lantern challenge",
        "Luna promised to light the harbor lantern before night covered the reef.",
        "The wick was short, and the old keeper insisted that no child could repair it.",
        "Luna gathered every loose thread she could find, but the flame still sputtered.",
        "A coil of lampwick lay in the keeper's chest beside a note from his former helper.",
        "Luna asked permission, measured the coil carefully, and worked while the keeper held the lantern steady.",
        "The keeper apologized for doubting her, and Luna thanked him for sharing the right tool.",
        "Their patient industry lit the reef, guiding fishing boats home.",
        "Respect grows when people make room for one another's skills.",
        "The harbor lantern glowed like a small moon above the friendly boats.",
        "What finally made the harbor lantern burn brightly?",
        "Luna used the proper lampwick from the keeper's chest while he helped hold the lantern steady.",
    ),
    Incident(
        "the divided map",
        "Two pirate crews met at an island market with half of an old map each.",
        "Each crew wanted the hidden orchard for itself, and their captains began shouting across the pier.",
        "Luna tried to snatch both map pieces and run, but a gust scattered them among the baskets.",
        "The torn edges matched, and the map showed a spring large enough for every traveler.",
        "Luna returned both pieces and suggested that the crews search together and share the orchard.",
        "The captains shook hands, apologized for their greed, and agreed to protect the spring together.",
        "The united crews found fruit, fresh water, and a safe path home.",
        "Sharing a useful treasure can bring rivals back together.",
        "Two flags flew side by side over the orchard gate.",
        "Why did the two crews stop fighting over the map?",
        "They saw that the matching pieces led to a spring and orchard large enough for everyone, so they agreed to share it.",
    ),
    Incident(
        "the silent bell",
        "A warning bell watched over the harbor channel.",
        "The bell rope snapped, and the harbor master blamed a quiet sailor who had been polishing it.",
        "Luna tied three quick knots, but the short rope could not reach the bell.",
        "The quiet sailor pointed to a coil of sturdy line beside the old boathouse.",
        "Luna and the sailor measured the line, braided a new rope, and tested it from the pier.",
        "The harbor master apologized and offered the sailor the first pull of the bell.",
        "The clear ringing warned a fishing boat away from the rocks.",
        "Kindness listens to quiet helpers whose clues may save the day.",
        "The bell rang over the water as the once-blamed sailor smiled beside the harbor master.",
        "Who helped Luna discover the right rope?",
        "The quiet sailor pointed out the sturdy coil beside the old boathouse.",
    ),
]


OPENINGS = [
    "At dawn, the sea wore a silver smile.",
    "The little pirate ship bobbed where gulls cried bright and clear.",
    "A salty breeze carried a puzzle across the waves.",
    "On a warm morning, Luna climbed the creaking deck.",
    "The harbor woke beneath a red-and-gold sky.",
]


GIRL_NAMES = ["Luna", "Mara", "Nia", "Pia"]
BOY_NAMES = ["Finn", "Kai", "Toby", "Milo"]
TRAITS = ["curious", "patient", "brave", "cheerful", "thoughtful"]


@dataclass
class Setting:
    place: str = "the harbor"
    affords: set[str] = field(default_factory=lambda: {"sail", "repair", "share"})


SETTING = Setting()


def can_story(place: str, activity: str, prize: str) -> bool:
    return place == "harbor" and activity == "repair" and prize == "safe passage"


ASP_RULES = r"""
place(harbor).
activity(repair).
prize(safe_passage).
feature(reconciliation).
feature(kindness).

compatible(P,A,R) :-
    place(P),
    activity(A),
    prize(R),
    P = harbor,
    A = repair,
    R = safe_passage.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "harbor"),
            asp.fact("activity", "repair"),
            asp.fact("prize", "safe_passage"),
            asp.fact("feature", "reconciliation"),
            asp.fact("feature", "kindness"),
        ]
    )


def asp_program(show: str = "#show compatible/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("harbor", "repair", "safe_passage")]


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[int(params.incident.rsplit("_", 1)[1])]
    opening = OPENINGS[int(params.telling_mode.rsplit("_", 1)[1])]

    world = World()
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=params.gender,
            label=params.name,
            memes={"kindness": 1.0, "industry": 1.0},
        )
    )
    captain = world.add(
        Entity(
            id="captain",
            kind="character",
            type=params.captain,
            label="the captain",
            memes={"trust": 0.0},
        )
    )
    ship = world.add(
        Entity(
            id="ship",
            kind="vehicle",
            type="ship",
            label="the little pirate ship",
            meters={"damage": 1.0, "safety": 0.0},
        )
    )
    world.facts.update(child=child, captain=captain, ship=ship, incident=incident)

    world.say(opening)
    world.say(
        f"{params.name}, a {params.trait} young pirate, served aboard the little pirate ship "
        f"with the captain."
    )
    world.say(
        f"The crew hoped to earn a triumph by reaching safe harbor through steady industry, "
        f"not by grabbing treasure or pushing anyone aside."
    )
    world.para()
    world.say(incident.beginning)
    world.say(incident.conflict)
    world.say(
        f'"We must work together," {params.name} said. '
        f'"But first, let us learn what really happened."'
    )
    world.say(incident.first_try)
    world.para()
    world.say(incident.clue)
    world.say(f'"A kind question is better than a sharp blame," the captain said.')
    world.say(incident.action)
    child.memes["confidence"] = 1.0
    captain.memes["trust"] = 1.0
    world.fired.add("clue_found")
    world.para()
    world.say(incident.reconciliation)
    world.say(
        f'"Thank you for helping me see the truth," {params.name} said. '
        f'"Now our work can help everyone."'
    )
    ship.meters["damage"] = 0.0
    ship.meters["safety"] = 1.0
    world.fired.add("reconciliation")
    world.say(incident.resolution)
    world.say(
        f"The crew's triumph came from industry and kindness: they worked carefully, "
        f"listened fairly, and left no friend behind."
    )
    world.say(incident.lesson)
    world.say(incident.ending)
    world.facts.update(
        title=incident.title,
        clue=incident.clue,
        reconciliation=incident.reconciliation,
        resolution=incident.resolution,
        lesson=incident.lesson,
        ending=incident.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    incident = world.facts["incident"]
    return [
        "Write a child-friendly Pirate Tale about triumph through industry, reconciliation, and kindness.",
        f"Tell a pirate story in which {child.label} solves {incident.title} by discovering the real cause.",
        f"Show how kindness changes the crew's choice after this clue: {incident.clue}",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What kind of triumph did {child.label} seek?",
            answer=f"{child.label} sought a triumph earned through steady industry, careful work, and helping the crew reach safety.",
        ),
        QAItem(
            question=incident.question,
            answer=incident.answer,
        ),
        QAItem(
            question=f"How did reconciliation change the crew's actions during {incident.title}?",
            answer=incident.reconciliation,
        ),
        QAItem(
            question=f"What did {child.label} learn from the {incident.title} problem?",
            answer=incident.lesson,
        ),
        QAItem(
            question="What final image showed that the problem was solved?",
            answer=incident.ending,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is industry?",
            answer="Industry is steady, careful effort toward a useful goal.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and choosing to work together.",
        ),
        QAItem(
            question="Why is kindness useful on a ship?",
            answer="Kindness helps people share clues, admit mistakes, and solve difficult work without hurting one another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:8} ({entity.type:10}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random, seed: int) -> StoryParams:
    if args.place and args.place != "harbor":
        raise StoryError("This pirate storyworld uses the harbor setting.")
    if args.activity and args.activity != "repair":
        raise StoryError("This pirate storyworld centers on repair and careful work.")
    if args.prize and args.prize != "safe passage":
        raise StoryError("The supported prize is safe passage.")
    if args.gender and args.gender not in {"girl", "boy"}:
        raise StoryError("Gender must be girl or boy.")

    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    captain = args.captain or rng.choice(["captain", "harbor master"])
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        place="harbor",
        activity="repair",
        prize="safe passage",
        name=name,
        gender=gender,
        captain=captain,
        trait=trait,
        incident=f"incident_{seed % len(INCIDENTS):02d}",
        telling_mode=f"mode_{(seed // len(INCIDENTS)) % len(OPENINGS):02d}",
        seed=seed,
    )


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A Pirate Tale about triumph, industry, reconciliation, and kindness."
    )
    parser.add_argument("--place", choices=["harbor"])
    parser.add_argument("--activity", choices=["repair"])
    parser.add_argument("--prize", choices=["safe passage"])
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--captain", choices=["captain", "harbor master"])
    parser.add_argument("--name")
    parser.add_argument("--trait", choices=TRAITS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_combos = set(asp_valid_combos())
    if py != clingo_combos:
        print("MISMATCH between Python and ASP:")
        print("  only in Python:", sorted(py - clingo_combos))
        print("  only in ASP:", sorted(clingo_combos - py))
        return 1

    for seed in range(12):
        params = resolve_params(
            argparse.Namespace(
                place=None,
                activity=None,
                prize=None,
                gender=None,
                captain=None,
                name=None,
                trait=None,
            ),
            random.Random(seed),
            seed,
        )
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            print("Generated story verification failed.")
            return 1

    print(f"OK: ASP matches Python ({len(py)} valid combination). Stories generated successfully.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            sys.exit(asp_verify())
        except ImportError as exc:
            raise StoryError("ASP verification requires clingo to be installed.") from exc

    if args.asp:
        try:
            print(asp_valid_combos())
        except ImportError as exc:
            raise StoryError("ASP mode requires clingo to be installed.") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = resolve_params(args, random.Random(base_seed), base_seed)
        samples.append(generate(params))
    else:
        seen: set[str] = set()
        for index in range(max(args.n, 1)):
            seed = base_seed + index
            params = resolve_params(args, random.Random(seed), seed)
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)

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
