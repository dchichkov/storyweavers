#!/usr/bin/env python3
"""A gentle mountain ghost story about an avalanche, a certificate, and teamwork."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        sys.path.insert(0, str(_parent))
        break

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
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    captain: str = "Mira"
    friend: str = "Tavi"
    guide: str = "Nell"
    ghost: str = "Rowan"
    place: str = "Pineglass Pass"
    incident: int = 0
    opening: int = 0
    dialogue: int = 0


CHARACTER_NAMES = [
    "Mira", "Tavi", "Nell", "Jun", "Cleo", "Pip", "Ari", "Sasha",
]
GHOST_NAMES = ["Rowan", "Elsie", "Marlow", "Orin"]
PLACES = [
    "Pineglass Pass",
    "Mooncap Mountain",
    "Bellwether Ridge",
    "Silver Fir Pass",
]


INCIDENTS = [
    {
        "title": "the silent bell",
        "damage": "snapped the outside bell rope",
        "clue": "the brass shutter lever that could be worked from inside",
        "method": (
            "{captain} held the lantern steady, {friend} worked the brass shutter, "
            "and {guide} counted three flashes, a pause, and three more."
        ),
        "sound": "clack, clack, clack",
        "object": "brass shutter",
        "safe_shelter": True,
        "ghost_warning": True,
        "teamwork_plan": True,
        "signal_available": True,
    },
    {
        "title": "the frosted signal pane",
        "damage": "covered the low signal window with wind-packed snow",
        "clue": "the narrow upper vent, where a little moonlight still showed",
        "method": (
            "{captain} held the lantern near the vent, {friend} angled a polished "
            "tin plate to guide its light, and {guide} counted the three-flash signal."
        ),
        "sound": "scritch, scrape, glimmer",
        "object": "tin reflector",
        "safe_shelter": True,
        "ghost_warning": True,
        "teamwork_plan": True,
        "signal_available": True,
    },
    {
        "title": "the dim lantern",
        "damage": "cracked the signal lamp's outer lens",
        "clue": "a small spare lantern tucked beneath the map table",
        "method": (
            "{captain} lit the spare lantern, {friend} shielded it from the draft "
            "with a tin plate, and {guide} aimed it through the clear upper pane."
        ),
        "sound": "click, hush, shine",
        "object": "spare lantern",
        "safe_shelter": True,
        "ghost_warning": True,
        "teamwork_plan": True,
        "signal_available": True,
    },
    {
        "title": "the torn flag",
        "damage": "ripped the red signal flag from its outside hook",
        "clue": "the inside hook beside the clear east-facing window",
        "method": (
            "{captain} held the lantern behind the window, {friend} tied a bright "
            "scarf to the inside hook, and {guide} swung it in time with three flashes."
        ),
        "sound": "flick, flutter, flash",
        "object": "bright scarf",
        "safe_shelter": True,
        "ghost_warning": True,
        "teamwork_plan": True,
        "signal_available": True,
    },
]


OPENINGS = [
    "At {place}, dusk turned the snow lavender around the old signal hut.",
    "The wind hummed over {place} as {captain}, {friend}, and {guide} reached the stone hut.",
    "A thin moon rose above {place}, and the old signal hut's windows glimmered ahead.",
    "On the quiet trail at {place}, {captain} heard the mountain give a low, distant rumble.",
]

DIALOGUES = [
    (
        "{captain} whispered, 'Are you the keeper from the old picture?' "
        "'I am {ghost}, the keeper,' said the pale figure. 'The snow is still moving. "
        "Do not cross the slope.' '{friend} asked, 'Then how can we call the patrol?' "
        "The ghost pointed to {clue}. '{guide} nodded. 'We can send the signal together.'"
    ),
    (
        "'That sound came from the ridge,' said {friend}. 'Should we go and check?' "
        "'No,' said {ghost}, appearing beside the old nameplate. 'The slope is not safe.' "
        "'Then show us another way to call for help,' said {captain}. "
        "The ghost pointed to {clue}. '{guide} said, 'We will stay inside and work as a team.'"
    ),
    (
        "'We are cut off,' said {guide}. 'Will the patrol know where we are?' "
        "'I watched this pass for many winters,' answered {ghost}. 'Stay in the hut and look at {clue}.' "
        "'We can make the three-flash signal from here,' said {captain}. "
        "'I'll help,' said {friend}. 'Tell me what to hold.'"
    ),
]


ASP_RULES = r"""
reasonable(I) :-
    incident(I),
    safe_shelter(I),
    ghost_warning(I),
    teamwork_plan(I),
    signal_available(I),
    team_size(N),
    minimum_team_size(M),
    N >= M.
"""


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("team_size", 3),
        asp.fact("minimum_team_size", 2),
    ]
    for index, incident in enumerate(INCIDENTS):
        key = f"incident_{index}"
        facts.append(asp.fact("incident", key))
        for field_name, predicate in (
            ("safe_shelter", "safe_shelter"),
            ("ghost_warning", "ghost_warning"),
            ("teamwork_plan", "teamwork_plan"),
            ("signal_available", "signal_available"),
        ):
            if incident[field_name]:
                facts.append(asp.fact(predicate, key))
    return "\n".join(facts)


def asp_program(show: str = "#show reasonable/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about an avalanche and a mountain rescue team."
    )
    parser.add_argument("--captain", choices=CHARACTER_NAMES)
    parser.add_argument("--friend", choices=CHARACTER_NAMES)
    parser.add_argument("--guide", choices=CHARACTER_NAMES)
    parser.add_argument("--ghost", choices=GHOST_NAMES)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--incident", type=int, choices=range(len(INCIDENTS)))
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
    captain = args.captain or rng.choice(CHARACTER_NAMES)
    remaining = [name for name in CHARACTER_NAMES if name != captain]
    friend = args.friend or rng.choice(remaining)
    remaining = [name for name in remaining if name != friend]
    guide = args.guide or rng.choice(remaining)
    return StoryParams(
        seed=args.seed,
        captain=captain,
        friend=friend,
        guide=guide,
        ghost=args.ghost or rng.choice(GHOST_NAMES),
        place=args.place or rng.choice(PLACES),
        incident=(
            args.incident
            if args.incident is not None
            else rng.randrange(len(INCIDENTS))
        ),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
    )


def python_reasonable_incidents() -> set[str]:
    """The Python twin of the ASP gate for the registered story situations."""
    team_size = 3
    minimum_team_size = 2
    return {
        f"incident_{index}"
        for index, incident in enumerate(INCIDENTS)
        if team_size >= minimum_team_size
        and incident["safe_shelter"]
        and incident["ghost_warning"]
        and incident["teamwork_plan"]
        and incident["signal_available"]
    }


def validate_params(params: StoryParams) -> None:
    roles = [params.captain, params.friend, params.guide, params.ghost]
    if any(not isinstance(name, str) or not name.strip() for name in roles):
        raise StoryError("Every character needs a non-empty name.")
    if len(set(roles)) != len(roles):
        raise StoryError("The captain, friend, guide, and ghost need distinct names.")
    if params.ghost not in GHOST_NAMES:
        raise StoryError(f"Unknown ghost name: {params.ghost!r}.")
    if params.place not in PLACES:
        raise StoryError(f"Unknown mountain setting: {params.place!r}.")
    if not isinstance(params.incident, int) or not 0 <= params.incident < len(INCIDENTS):
        raise StoryError(f"Incident must be an integer from 0 to {len(INCIDENTS) - 1}.")
    if not 0 <= params.opening < len(OPENINGS):
        raise StoryError("Opening choice is outside the registered range.")
    if not 0 <= params.dialogue < len(DIALOGUES):
        raise StoryError("Dialogue choice is outside the registered range.")
    if f"incident_{params.incident}" not in python_reasonable_incidents():
        raise StoryError("This situation lacks a safe shelter, a signal, or a workable team plan.")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    incident = INCIDENTS[params.incident]
    common = {
        "captain": params.captain,
        "friend": params.friend,
        "guide": params.guide,
        "ghost": params.ghost,
        "place": params.place,
    }

    world = World()
    captain = world.add(
        Entity(
            id=params.captain,
            kind="character",
            type="young_trail_helper",
            label=params.captain,
            meters={"distance_to_shelter": 0.0, "body_warmth": 1.0},
            memes={"confidence": 0.7, "fear": 0.1, "trust": 0.3},
        )
    )
    friend = world.add(
        Entity(
            id=params.friend,
            kind="character",
            type="young_trail_helper",
            label=params.friend,
            meters={"distance_to_shelter": 0.0, "body_warmth": 1.0},
            memes={"confidence": 0.5, "fear": 0.2, "trust": 0.3},
        )
    )
    guide = world.add(
        Entity(
            id=params.guide,
            kind="character",
            type="trail_guide",
            label=params.guide,
            meters={"distance_to_shelter": 0.0, "body_warmth": 1.0},
            memes={"confidence": 0.7, "fear": 0.1, "trust": 0.4},
        )
    )
    ghost = world.add(
        Entity(
            id=params.ghost,
            kind="character",
            type="ghostly_pass_keeper",
            label=params.ghost,
            meters={"glow": 0.4, "distance_to_shelter": 0.0},
            memes={"watchfulness": 1.0, "loneliness": 0.7, "hope": 0.2},
        )
    )
    hut = world.add(
        Entity(
            id="signal hut",
            kind="place",
            type="stone_shelter",
            label="the old signal hut",
            meters={"wall_strength": 1.0, "snow_depth_at_door": 0.0},
        )
    )
    certificate = world.add(
        Entity(
            id="teamwork certificate",
            kind="object",
            type="certificate",
            label="the Pass Teamwork Certificate",
            meters={"dryness": 1.0, "displayed": 0.0},
        )
    )
    lamp = world.add(
        Entity(
            id="signal lamp",
            kind="tool",
            type="lantern",
            label="the signal lantern",
            meters={"brightness": 0.7, "visible_from_village": 0.0},
        )
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        guide=guide,
        ghost=ghost,
        hut=hut,
        certificate=certificate,
        lamp=lamp,
        incident=incident,
        place=params.place,
        safe_shelter=True,
        signal_sent=False,
        certificate_displayed=False,
    )

    world.say(OPENINGS[params.opening].format(**common))
    world.say(
        f"{params.captain}, {params.friend}, and {params.guide} had come to hang "
        f"the Pass Teamwork Certificate inside the hut. It thanked them for repairing "
        f"the lower trail markers, and {params.captain} carried it in a waxed blue tube."
    )
    world.say(
        "They had just stepped inside when an avalanche thundered down the far bowl. "
        f"The stone walls held, but the slide buried the marked path and {incident['damage']}. "
        "The slope was still shifting, so the three helpers knew they must not cross it."
    )
    hut.meters["snow_depth_at_door"] = 1.4
    captain.memes["fear"] = 0.6
    friend.memes["fear"] = 0.7
    guide.memes["fear"] = 0.4

    clue = incident["clue"]
    world.say(
        f"A pale lantern-glow appeared beside the hut's old brass nameplate. "
        f"A see-through keeper stood in the blue light, his coat as faint as fog."
    )
    dialogue = DIALOGUES[params.dialogue].format(**common, clue=clue)
    world.say(dialogue)

    captain.memes["trust"] = 0.8
    friend.memes["trust"] = 0.8
    guide.memes["trust"] = 0.8
    captain.memes["fear"] = 0.3
    friend.memes["fear"] = 0.3
    guide.memes["resolve"] = 0.9
    ghost.memes["hope"] = 0.8

    world.say(
        f"Following the keeper's clue, {incident['method'].format(**common)} "
        f"{incident['sound'].capitalize()} went the shutter and lantern. "
        "Three short flashes crossed the snow, then three more answered them."
    )
    lamp.meters["brightness"] = 1.0
    lamp.meters["visible_from_village"] = 1.0
    world.facts["signal_sent"] = True

    world.say(
        "A answering lantern winked from the village side of the valley. "
        "The patrol had seen their signal and knew to reach the hut by the safer lower trail."
    )
    world.say(
        "Before long, rescuers arrived at the stone door. They checked that everyone was warm "
        "and safe, then helped the team bring the dry certificate to the hut wall."
    )
    world.say(
        f"Beside the old plate, the certificate read, 'For teamwork that keeps the pass safe.' "
        f"{params.captain} looked at the keeper and said, 'Your light kept the pass safe too, {params.ghost}.' "
        f"The ghost smiled. At dawn, his lantern-glow rested like a small star beside the certificate."
    )
    certificate.meters["displayed"] = 1.0
    world.facts["certificate_displayed"] = True
    ghost.meters["glow"] = 0.1
    ghost.memes["loneliness"] = 0.1
    ghost.memes["peace"] = 1.0

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
    incident = facts["incident"]
    captain = facts["captain"]
    friend = facts["friend"]
    guide = facts["guide"]
    return [
        (
            f"Write a gentle ghost story about {captain.label}, {friend.label}, and "
            f"{guide.label} working together after an avalanche at {facts['place']}."
        ),
        (
            f"Tell a child-facing mountain story in which a kind ghost helps a team "
            f"send a rescue signal during {incident['title']}."
        ),
        (
            "Write a complete story with spoken dialogue, a teamwork certificate, "
            "a safe rescue, and a memorable ghostly ending."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    incident = facts["incident"]
    captain = facts["captain"]
    friend = facts["friend"]
    guide = facts["guide"]
    ghost = facts["ghost"]
    return [
        QAItem(
            question="What did the avalanche do to the trail and the signal equipment?",
            answer=(
                f"The avalanche buried the marked path and {incident['damage']}. "
                "Because the slope was still shifting, the helpers stayed inside the stone hut."
            ),
        ),
        QAItem(
            question=f"How did {ghost.label} help the team?",
            answer=(
                f"{ghost.label} warned them not to cross the moving slope and pointed them to "
                f"{incident['clue']}. That clue let the team signal the patrol from the shelter."
            ),
        ),
        QAItem(
            question=f"How did {captain.label}, {friend.label}, and {guide.label} work together?",
            answer=(
                f"{incident['method'].format(captain=captain.label, friend=friend.label, guide=guide.label)} "
                "Their three-flash signal brought the patrol to them by the safer lower trail."
            ),
        ),
        QAItem(
            question="Why was the certificate important at the end?",
            answer=(
                "The certificate thanked the three helpers for teamwork that kept the pass safe. "
                "They hung it beside the old keeper's nameplate, honoring both their teamwork and his watch."
            ),
        ),
        QAItem(
            question="What changed for the ghost?",
            answer=(
                f"{ghost.label} had watched the pass alone for many winters. When the helpers thanked "
                "him and hung their certificate beside his nameplate, he smiled peacefully as dawn came."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an avalanche?",
            answer=(
                "An avalanche is a large mass of snow that rushes down a mountain. "
                "People nearby should move to safety and follow trained rescuers' instructions."
            ),
        ),
        QAItem(
            question="What does a certificate show?",
            answer=(
                "A certificate is a written document that recognizes an achievement, "
                "a completed course, or a special contribution."
            ),
        ),
        QAItem(
            question="Why can teamwork help during an emergency?",
            answer=(
                "Teamwork lets people share useful jobs, listen to one another, and make a safer plan "
                "instead of asking one person to do everything."
            ),
        ),
        QAItem(
            question="What is a signal lantern used for?",
            answer=(
                "A signal lantern makes light that can help people show where they are or send a simple "
                "message when others can see it."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions -- answerable from the story text =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions -- child level, no story needed =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"  {entity.label:24} ({entity.type}) {' '.join(details)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(str(args[0]) for args in asp.atoms(model, "reasonable"))


def asp_verify() -> int:
    import asp

    expected = python_reasonable_incidents()
    model = asp.one_model(asp_program())
    actual = {str(args[0]) for args in asp.atoms(model, "reasonable")}
    if actual != expected:
        print("MISMATCH between clingo and the Python reasonableness gate.")
        print("  clingo:", sorted(actual))
        print("  python:", sorted(expected))
        return 1

    try:
        for index in range(len(INCIDENTS)):
            sample = generate(
                StoryParams(
                    captain="Mira",
                    friend="Tavi",
                    guide="Nell",
                    ghost="Rowan",
                    place=PLACES[index % len(PLACES)],
                    incident=index,
                    opening=index % len(OPENINGS),
                    dialogue=index % len(DIALOGUES),
                )
            )
            if not all(
                phrase in sample.story.lower()
                for phrase in ("avalanche", "certificate", "ghost", "patrol")
            ):
                raise StoryError(f"Generated story {index} is missing a required story element.")
            if len(sample.story) < 500 or not sample.story_qa:
                raise StoryError(f"Generated story {index} is incomplete.")
        try:
            generate(StoryParams(captain="Mira", friend="Mira", guide="Nell"))
        except StoryError:
            pass
        else:
            raise StoryError("The invalid duplicate-name case was not rejected.")
    except StoryError as exc:
        print(f"Story exercise failed: {exc}")
        return 1

    print("OK: clingo parity matches the Python gate; all registered stories passed.")
    return 0


CURATED = [
    StoryParams(
        captain="Mira", friend="Tavi", guide="Nell", ghost="Rowan",
        place="Pineglass Pass", incident=0, opening=0, dialogue=0,
    ),
    StoryParams(
        captain="Jun", friend="Cleo", guide="Ari", ghost="Elsie",
        place="Mooncap Mountain", incident=1, opening=2, dialogue=1,
    ),
    StoryParams(
        captain="Pip", friend="Sasha", guide="Mira", ghost="Marlow",
        place="Bellwether Ridge", incident=2, opening=1, dialogue=2,
    ),
    StoryParams(
        captain="Nell", friend="Tavi", guide="Cleo", ghost="Orin",
        place="Silver Fir Pass", incident=3, opening=3, dialogue=0,
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
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        suggestions = asp_valid()
        print(f"{len(suggestions)} ASP-approved avalanche situations")
        for key in suggestions:
            index = int(key.rsplit("_", 1)[1])
            print(f"{key}: {INCIDENTS[index]['title']}")
        return
    if args.n < 1 and not args.all:
        parser.error("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    try:
        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            seen: set[str] = set()
            attempt = 0
            limit = max(50, args.n * 40)
            while len(samples) < args.n and attempt < limit:
                params = resolve_params(args, random.Random(base_seed + attempt))
                sample = generate(params)
                if sample.story not in seen:
                    seen.add(sample.story)
                    samples.append(sample)
                attempt += 1
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.captain} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
