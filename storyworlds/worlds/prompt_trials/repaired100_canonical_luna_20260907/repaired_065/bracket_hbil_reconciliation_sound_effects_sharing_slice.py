#!/usr/bin/env python3
"""A slice-of-life storyworld about sharing a bracket and reconciling a tiny hbil kit."""

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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Milo", "Nia", "Theo", "Mara", "Owen", "Ivy", "Sam"]
FRIENDS = ["her brother", "her cousin", "a neighbor", "her friend"]
PLACES = ["the kitchen table", "the sunny porch", "the apartment hallway", "the small craft room"]
ADULTS = ["Mom", "Dad", "Grandma", "Aunt Jo"]
SOUNDS = ["click-clack", "tap-tap", "clink", "snip-snap", "whirr-click"]
OPENINGS = [
    "Late afternoon light rested on the table.",
    "The kettle had just stopped humming.",
    "A breeze moved the curtain beside the workbench.",
    "After school, the room filled with the soft sounds of unpacking.",
    "The floor was warm where the sun had crossed it.",
]
LESSONS = [
    "A shared job needs shared turns.",
    "A disagreement can become a plan when everyone listens.",
    "Small clues are easier to notice when hands stop rushing.",
    "Reconciliation begins with making room for another person's idea.",
]


@dataclass(frozen=True)
class Incident:
    key: str
    project: str
    problem: str
    surprise: str
    clue: str
    repair: str
    result: str


INCIDENTS = [
    Incident(
        "loose_corner",
        "a little model shelf",
        "the silver bracket would not sit squarely between two wooden sides",
        "the shelf leaned and sent three buttons rolling across the table",
        "one edge of the bracket was turned inward",
        "Luna and her partner loosened the screw, turned the bracket, and held the sides steady while taking turns",
        "the shelf stood straight, with the buttons gathered in a neat cup",
    ),
    Incident(
        "missing_mark",
        "a cardboard birdhouse",
        "the bracket was placed over the wrong pair of holes",
        "the hbil tool made a bright ping and slipped harmlessly onto the cloth",
        "a faded blue dot matched the other side of the house",
        "they compared both sides, moved the bracket to the blue marks, and shared the hbil one careful turn at a time",
        "the birdhouse held together and its round doorway faced the window",
    ),
    Incident(
        "tight_turn",
        "a small book stand",
        "the bracket screw became too tight for either child to turn",
        "the hbil gave a soft squeak instead of moving",
        "the screw was tight because the two wooden pieces were pressing against each other",
        "they stopped pulling, opened the stand slightly, and asked the adult to check before sharing the next turn",
        "the screw turned easily and the stand held Luna's book upright",
    ),
    Incident(
        "mixed_pieces",
        "a recycled-paper picture frame",
        "the bracket and two matching washers were mixed with a pile of beads",
        "a washer bounced into an empty teacup with a tiny ting",
        "the bracket had a small notch that matched only one washer",
        "they sorted the pieces by shape, apologized for grabbing, and passed the hbil after each completed step",
        "the frame stood on the sill with a bright paper sun inside it",
    ),
]


@dataclass
class Entity:
    id: str
    type: str
    label: str
    owner: Optional[str] = None
    holder: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    place: str
    hero_name: str
    partner: str
    adult: str
    incident_key: str
    opening_index: int = 0
    sound_index: int = 0
    lesson_index: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple[str, str]] = set()

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


def incident_for(key: str) -> Incident:
    for incident in INCIDENTS:
        if incident.key == key:
            return incident
    raise StoryError(f"Unknown incident key: {key}")


def dialogue(world: World, speaker: str, line: str) -> None:
    world.say(f'"{line}" {speaker} said.')


def tell(setting: Setting, params: StoryParams) -> World:
    incident = incident_for(params.incident_key)
    world = World(setting)

    hero = world.add(Entity("hero", "child", params.hero_name))
    partner = world.add(Entity("partner", "child", params.partner))
    adult = world.add(Entity("adult", "adult", params.adult))
    bracket = world.add(Entity("bracket", "hardware", "the bracket", owner="hero"))
    hbil = world.add(Entity("hbil", "tool", "the hbil", owner="adult"))

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    sound = SOUNDS[params.sound_index % len(SOUNDS)]
    lesson = LESSONS[params.lesson_index % len(LESSONS)]

    bracket.meters.update(aligned=0.0, useful=1.0)
    hbil.meters.update(shared=0.0, safe=1.0)
    hero.memes.update(pride=1.0, patience=0.0, kindness=1.0)
    partner.memes.update(pride=1.0, patience=0.0, kindness=1.0)
    adult.memes.update(guidance=1.0)

    world.say(opening)
    world.say(
        f"In {setting.place}, {params.hero_name} opened a small box for {incident.project}. "
        "Inside were a silver bracket, two wooden pieces, and an unusual hand tool labeled hbil."
    )
    world.say(
        f"{params.partner.capitalize()} sat beside {params.hero_name}. "
        f"They wanted to finish the project together, but {incident.problem}."
    )
    world.para()

    dialogue(world, params.partner.capitalize(), "I can hold the bracket while you use the hbil.")
    dialogue(world, params.hero_name, "I thought you said I could do the whole next step.")
    world.say(f"They both reached forward. {sound.upper()}! {incident.surprise}.")
    world.say(
        f"{params.hero_name} pulled back, and {params.partner} pulled back too. "
        "For a moment, neither child spoke."
    )
    world.para()

    dialogue(world, params.partner.capitalize(), "I was not trying to take your turn.")
    dialogue(world, params.hero_name, "I was worried the project would not be mine anymore.")
    world.say(
        f"{params.adult} came to the table and said, "
        '"The bracket belongs in the project, but the work can belong to both of you. Let us find the clue first."'
    )
    world.say(f"They noticed that {incident.clue}.")
    world.para()

    world.say(incident.repair)
    world.say(f"{sound.upper()}! The hbil moved gently, one turn at a time.")
    world.say(incident.result)
    world.say(
        f"{params.hero_name} looked at {params.partner} and said, "
        '"I am sorry I grabbed. You can choose the next turn."'
    )
    world.say(
        f"{params.partner.capitalize()} smiled and answered, "
        '"I am sorry I grabbed too. We can finish it together."'
    )
    world.say(f"They had learned that {lesson.lower()}")
    world.say(
        f"By evening, the finished project rested in the light, and the bracket no longer looked like a problem. "
        "It looked like the small piece that helped two people make room for each other."
    )

    bracket.meters["aligned"] = 1.0
    hbil.meters["shared"] = 1.0
    hero.memes["patience"] = 1.0
    partner.memes["patience"] = 1.0
    world.fired.update(
        {
            ("problem", incident.key),
            ("sound", incident.key),
            ("reconciliation", incident.key),
            ("sharing", incident.key),
            ("resolution", incident.key),
        }
    )
    world.facts.update(
        hero=hero,
        partner=partner,
        adult=adult,
        bracket=bracket,
        hbil=hbil,
        incident=incident,
        sound=sound,
        lesson=lesson,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    return [
        f"Write a slice-of-life story about {p.hero_name} sharing a bracket and an hbil with {p.partner}.",
        f"Show reconciliation after this problem: {incident.problem.capitalize()}.",
        "Use concrete sound effects and let a kind conversation change the children's actions.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    incident: Incident = world.facts["incident"]  # type: ignore[assignment]
    sound: str = world.facts["sound"]  # type: ignore[assignment]
    lesson: str = world.facts["lesson"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What were {p.hero_name} and {p.partner} trying to make?",
            answer=f"They were trying to make {incident.project}.",
        ),
        QAItem(
            question="What went wrong with the bracket?",
            answer=f"{incident.problem.capitalize()}.",
        ),
        QAItem(
            question="What sound showed that the first attempt had gone wrong?",
            answer=f"The story used the sound effect “{sound.upper()}!” when {incident.surprise}.",
        ),
        QAItem(
            question="What clue helped them solve the problem?",
            answer=f"They noticed that {incident.clue}.",
        ),
        QAItem(
            question="How did the children reconcile?",
            answer=(
                "They admitted that they had both grabbed for the work, apologized to each other, "
                "and agreed to share the hbil one careful turn at a time."
            ),
        ),
        QAItem(
            question="What did the finished project show?",
            answer=f"It showed that {incident.result}. The children also learned that {lesson.lower()}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bracket?",
            answer="A bracket is a piece that helps hold or join other pieces together.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people take part, often by making a fair plan for turns.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after a disagreement by listening, apologizing, and choosing a better way forward.",
        ),
        QAItem(
            question="Why can sound effects help a story?",
            answer="Sound effects help readers notice an important action or change in the scene.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: {entity.type} {entity.label} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
shared(H, P, T) :- child(H), child(P), tool(T), holder(T, H).
sound_event(H, P, T) :- shared(H, P, T), sound_effect(T).
reconcile(H, P) :- sound_event(H, P, T), speaks(H), speaks(P).
aligned(B) :- bracket(B), reconcile(hero, partner).
resolved(B, T) :- aligned(B), tool(T), safe(T).
#show shared/3.
#show sound_event/3.
#show reconcile/2.
#show aligned/1.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child", "hero"),
            asp.fact("child", "partner"),
            asp.fact("tool", "hbil"),
            asp.fact("bracket", "bracket"),
            asp.fact("holder", "hbil", "hero"),
            asp.fact("sound_effect", "hbil"),
            asp.fact("safe", "hbil"),
            asp.fact("speaks", "hero"),
            asp.fact("speaks", "partner"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_parity() -> bool:
    import asp

    model = asp.one_model(asp_program())
    expected = {
        ("hero", "partner", "hbil"),
    }
    return set(asp.atoms(model, "shared")) == expected


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A slice-of-life sharing world about a bracket and hbil.")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--partner", choices=FRIENDS)
    parser.add_argument("--adult", choices=ADULTS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=name,
        partner=args.partner or rng.choice(FRIENDS),
        adult=args.adult or rng.choice(ADULTS),
        incident_key=rng.choice(INCIDENTS).key,
        opening_index=rng.randrange(len(OPENINGS)),
        sound_index=rng.randrange(len(SOUNDS)),
        lesson_index=rng.randrange(len(LESSONS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(Setting(params.place), params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def curated() -> list[StoryParams]:
    return [
        StoryParams(
            place="the kitchen table",
            hero_name="Luna",
            partner="her brother",
            adult="Mom",
            incident_key="loose_corner",
            opening_index=0,
            sound_index=0,
            lesson_index=0,
        ),
        StoryParams(
            place="the sunny porch",
            hero_name="Milo",
            partner="his cousin",
            adult="Grandma",
            incident_key="missing_mark",
            opening_index=2,
            sound_index=2,
            lesson_index=2,
        ),
        StoryParams(
            place="the small craft room",
            hero_name="Nia",
            partner="a neighbor",
            adult="Aunt Jo",
            incident_key="mixed_pieces",
            opening_index=4,
            sound_index=1,
            lesson_index=3,
        ),
    ]


def verify() -> int:
    for params in curated():
        sample = generate(params)
        if not sample.story.strip():
            return 1
        if "bracket" not in sample.story or "hbil" not in sample.story:
            return 1
        if not sample.story_qa or not sample.world_qa:
            return 1
        world = sample.world
        if world is None or ("reconciliation", params.incident_key) not in world.fired:
            return 1
    try:
        if not asp_parity():
            return 1
    except ImportError:
        pass
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in curated()]
    else:
        samples = []
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

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
