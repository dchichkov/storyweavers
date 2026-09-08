#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a truthful report, friendship, and a
stormy rescue near a hidden island.
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

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    id: str
    name: str
    shelter: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Voyage:
    id: str
    destination: str
    danger: str
    prize: str
    clue: str


@dataclass
class StoryParams:
    place: str
    voyage: str
    captain: str
    friend1: str
    friend2: str
    seed: Optional[int] = None
    voice: str = "deck"


PLACES = {
    "parrot_cove": Place(
        "parrot_cove", "Parrot Cove", shelter=True, affords={"rescue", "report"}
    ),
    "moonlit_reef": Place(
        "moonlit_reef", "the Moonlit Reef", shelter=False, affords={"rescue", "report"}
    ),
    "whispering_isle": Place(
        "whispering_isle", "Whispering Isle", shelter=True, affords={"rescue", "report"}
    ),
}

VOYAGES = {
    "bell_boat": Voyage(
        "bell_boat",
        "Bell Boat Island",
        "a sudden squall",
        "the lost brass bell",
        "three scratches beside a drawing of a bell",
    ),
    "coconut_lagoon": Voyage(
        "coconut_lagoon",
        "Coconut Lagoon",
        "a drifting fog bank",
        "a chest of warm golden coconuts",
        "a palm-leaf arrow pointing east",
    ),
    "starfish_shoal": Voyage(
        "starfish_shoal",
        "Starfish Shoal",
        "a tide that pulled hard toward the rocks",
        "the admiral's silver compass",
        "a red thread tied around the map's corner",
    ),
}

NAMES = ["Luna", "Pip", "Mara", "Toby", "Nell", "Finn", "Cora", "Jasper"]
NAME_TYPES = {
    "Luna": "girl",
    "Pip": "boy",
    "Mara": "girl",
    "Toby": "boy",
    "Nell": "girl",
    "Finn": "boy",
    "Cora": "girl",
    "Jasper": "boy",
}

VOICES = {
    "deck": {
        "opening": "At dawn, Luna stood on the deck of the little ship and found a damp report tucked beneath the wheel.",
        "friendship": "\"A good captain does not sail alone,\" Luna said. \"Friends, will you help me read it?\"",
        "ending": "The friends sailed home with the report safe and the rescued treasure shining between them.",
    },
    "logbook": {
        "opening": "The old ship's log began with a curious report that Luna discovered beside the brass compass.",
        "friendship": "\"We can be brave together,\" said Luna. \"Will you help me follow its clue?\"",
        "ending": "That evening, the friends wrote a new report: friendship had guided the ship home.",
    },
    "storm": {
        "opening": "Before the first gull cried, Luna found a report fluttering against the mast.",
        "friendship": "\"The sea is wide,\" Luna said, \"but friendship makes a strong harbor. Come with me.\"",
        "ending": "When the storm cleared, the friends shared the treasure and watched their bright sail glow.",
    },
}

ASP_RULES = r"""
place(P) :- place_name(P).
voyage(V) :- voyage_name(V).
can_report(P) :- affords(P, report).
can_rescue(P) :- affords(P, rescue).
valid_voyage(P, V) :- place(P), voyage(V), can_report(P), can_rescue(P),
                       destination(V, P).
#show valid_voyage/2.
"""


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a report, rescue, and friendship."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--voyage", choices=sorted(VOYAGES))
    parser.add_argument("--captain")
    parser.add_argument("--friend1")
    parser.add_argument("--friend2")
    parser.add_argument("--voice", choices=sorted(VOICES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def valid_combos() -> list[tuple[str, str]]:
    return [
        (place_id, voyage_id)
        for place_id, place in PLACES.items()
        for voyage_id, voyage in VOYAGES.items()
        if place.shelter or voyage_id != "starfish_shoal"
    ]


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place_name", pid))
        for ability in sorted(place.affords):
            lines.append(asp.fact("affords", pid, ability))
    for vid, voyage in VOYAGES.items():
        lines.append(asp.fact("voyage_name", vid))
        destination = {
            "bell_boat": "parrot_cove",
            "coconut_lagoon": "whispering_isle",
            "starfish_shoal": "moonlit_reef",
        }[vid]
        lines.append(asp.fact("destination", vid, destination))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_voyage/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> set[tuple[str, str]]:
    import asp

    model = asp.one_model(asp_program())
    return set(asp.atoms(model, "valid_voyage"))


def asp_verify() -> int:
    py = set(valid_combos())
    try:
        clingo_pairs = asp_valid_combos()
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if py == clingo_pairs:
        print(f"OK: ASP and Python agree on {len(py)} valid voyages.")
        return 0
    print("Mismatch between ASP and Python:")
    print("  only in ASP:", sorted(clingo_pairs - py))
    print("  only in Python:", sorted(py - clingo_pairs))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if args.place is None or combo[0] == args.place
        if args.voyage is None or combo[1] == args.voyage
    ]
    if not combos:
        raise StoryError("No valid place and voyage match the requested options.")

    place, voyage = rng.choice(sorted(combos))
    captain = args.captain or rng.choice(NAMES)
    available = [name for name in NAMES if name != captain]
    friend1 = args.friend1 or rng.choice(available)
    available = [name for name in available if name != friend1]
    friend2 = args.friend2 or rng.choice(available)
    return StoryParams(
        place=place,
        voyage=voyage,
        captain=captain,
        friend1=friend1,
        friend2=friend2,
        voice=args.voice or rng.choice(sorted(VOICES)),
    )


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    voyage = VOYAGES[params.voyage]
    voice = VOICES[params.voice]
    world = World(place)

    captain = world.add(
        Entity(
            params.captain,
            kind="character",
            label=params.captain,
            memes={"courage": 1.0, "trust": 1.0},
        )
    )
    friend1 = world.add(
        Entity(
            params.friend1,
            kind="character",
            label=params.friend1,
            memes={"friendship": 1.0, "helpfulness": 1.0},
        )
    )
    friend2 = world.add(
        Entity(
            params.friend2,
            kind="character",
            label=params.friend2,
            memes={"friendship": 1.0, "helpfulness": 1.0},
        )
    )
    report = world.add(
        Entity(
            "report",
            kind="report",
            label="the sea report",
            meters={"readable": 1.0, "truthful": 1.0},
        )
    )
    lantern = world.add(
        Entity("lantern", kind="tool", label="the brass lantern", meters={"lit": 1.0})
    )
    rope = world.add(
        Entity("rope", kind="tool", label="the rescue rope", meters={"strong": 1.0})
    )

    world.facts.update(
        captain=captain,
        friends=[friend1, friend2],
        report=report,
        lantern=lantern,
        rope=rope,
        voyage=voyage,
        place=place,
    )

    world.say(voice["opening"])
    world.say(
        f"The report said that a small boat had drifted near {voyage.destination}, "
        f"where {voyage.danger} could trap anyone who sailed alone."
    )
    world.say(
        f"At the bottom of the page, {voyage.clue} marked the route to the lost "
        f"{voyage.prize}."
    )

    world.para()
    world.say(voice["friendship"])
    world.say(
        f"{friend1.label} read the report aloud while {friend2.label} checked the "
        f"lantern and rope. Their friendship made each task steadier."
    )
    world.say(
        f"\"The report tells us where to look,\" said {friend1.label}. "
        f"\"And we will tell one another if the sea changes,\" answered {friend2.label}."
    )
    world.say(
        f"They followed the clue toward {voyage.destination}, but {voyage.danger} "
        f"rose around the ship."
    )
    world.say(
        f"{captain.label} held the wheel, {friend1.label} raised the lantern, and "
        f"{friend2.label} cast the rope. Because they trusted one another, they "
        f"found the drifting boat before it struck the rocks."
    )
    world.fired.add("friendship_guided_rescue")
    captain.memes["trust"] += 1.0
    friend1.memes["friendship"] += 1.0
    friend2.memes["friendship"] += 1.0

    world.para()
    world.say(
        f"Together they rescued the sailor and recovered {voyage.prize}. "
        f"The sailor thanked them for believing the truthful report."
    )
    world.say(
        f"\"Your report saved us,\" said the sailor. \"Our friendship helped us act "
        f"on it,\" replied {captain.label}."
    )
    world.say(voice["ending"])
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    voyage: Voyage = world.facts["voyage"]  # type: ignore[assignment]
    captain: Entity = world.facts["captain"]  # type: ignore[assignment]
    return [
        "Write a child-friendly pirate tale about a truthful report and friendship.",
        f"Tell how {captain.label} and two friends use a report to face {voyage.danger}.",
        "Include a brief back-and-forth conversation and end with a clear rescue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    captain: Entity = world.facts["captain"]  # type: ignore[assignment]
    friends: list[Entity] = world.facts["friends"]  # type: ignore[assignment]
    report: Entity = world.facts["report"]  # type: ignore[assignment]
    voyage: Voyage = world.facts["voyage"]  # type: ignore[assignment]
    return [
        QAItem(
            f"What did {captain.label} find at the beginning?",
            f"{captain.label} found {report.label}, which described a dangerous route and a clue to the lost {voyage.prize}.",
        ),
        QAItem(
            f"Who helped {captain.label}?",
            f"{friends[0].label} and {friends[1].label} helped, and their friendship made the voyage safer.",
        ),
        QAItem(
            "How did the friends use the report?",
            f"They read it carefully, followed its clue toward {voyage.destination}, and warned one another when the danger changed.",
        ),
        QAItem(
            "How did the team complete the rescue?",
            f"The captain held the wheel, one friend raised the lantern, and the other cast the rope to reach the drifting boat.",
        ),
        QAItem(
            "What happened at the end?",
            f"They rescued the sailor, recovered the {voyage.prize}, and sailed home together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a report?",
            "A report is a clear account that tells people what happened or what may happen.",
        ),
        QAItem(
            "What is friendship?",
            "Friendship is a caring bond in which people trust, help, and listen to one another.",
        ),
        QAItem(
            "Why is a rescue rope useful on a ship?",
            "A rescue rope can help people reach or pull someone to safety.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} kind={entity.kind:10} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


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
    sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = ""
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
    StoryParams(
        place="parrot_cove",
        voyage="bell_boat",
        captain="Luna",
        friend1="Pip",
        friend2="Mara",
        voice="deck",
    ),
    StoryParams(
        place="whispering_isle",
        voyage="coconut_lagoon",
        captain="Finn",
        friend1="Cora",
        friend2="Nell",
        voice="logbook",
    ),
    StoryParams(
        place="moonlit_reef",
        voyage="starfish_shoal",
        captain="Jasper",
        friend1="Toby",
        friend2="Luna",
        voice="storm",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            pairs = sorted(asp_valid_combos())
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        print(f"{len(pairs)} valid voyages:")
        for pair in pairs:
            print(" ", pair)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < max(1, args.n) and attempts < max(50, args.n * 50):
            attempts += 1
            rng = random.Random(base_seed + attempts)
            try:
                params = resolve_params(args, rng)
            except StoryError as exc:
                print(exc)
                return
            params.seed = base_seed + attempts
            sample = generate(params)
            if sample.story not in seen:
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
