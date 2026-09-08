#!/usr/bin/env python3
"""
A small pirate tale about a cabinet, a nickel, and a clever rhyme that turns
a stuck treasure hunt into a teamwork success.
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


SETTINGS = {
    "moonlit_cove": {
        "place": "Moonlit Cove",
        "detail": "Moonlit Cove curled around a quiet harbor, where purple waves tapped the wooden docks.",
    },
    "parrot_island": {
        "place": "Parrot Island",
        "detail": "Parrot Island was warm and green, with bright birds calling above a crooked pirate path.",
    },
    "foggy_bay": {
        "place": "Foggy Bay",
        "detail": "Foggy Bay wore a blanket of silver mist, and every ship bell sounded twice.",
    },
}

NAMES = ["Luna", "Pip", "Mara", "Finn", "Tess", "Jory", "Nell", "Kai"]
GENDERS = {"Luna": "girl", "Pip": "boy", "Mara": "girl", "Finn": "boy",
           "Tess": "girl", "Jory": "boy", "Nell": "girl", "Kai": "boy"}
CAPTAINS = ["Captain Bea", "Captain Sol", "Captain Uma", "Captain Ned"]
TRAITS = ["curious", "brave", "cheerful", "patient", "clever", "bouncy"]

INCIDENTS = [
    {
        "id": "stuck_drawer",
        "problem": "The cabinet's top drawer was stuck, and the treasure map seemed to be hiding inside it.",
        "clue": "A nickel had slipped beneath the cabinet's front foot, tilting the whole cabinet just enough to pinch the drawer.",
        "plan": "Luna held the lantern, the captain watched the drawer, and two deckhands carefully moved the nickel with a spoon.",
        "twist": "The nickel was not treasure at all; it was the tiny wedge keeping the cabinet crooked.",
        "ending": "Inside the drawer lay the map, dry socks, and a note that said, 'Good crews look low as well as high.'",
    },
    {
        "id": "false_coin",
        "problem": "A shiny coin on the cabinet shelf appeared to mark the treasure, but the shelf would not turn.",
        "clue": "The nickel's edge matched a round notch hidden beneath the shelf's brass handle.",
        "plan": "The child read the carved marks, the captain held the cabinet steady, and the crew tested the nickel without forcing anything.",
        "twist": "The shiny coin was only a button; the ordinary nickel was the real key to the secret catch.",
        "ending": "The cabinet opened to reveal a compass, a biscuit tin, and a message praising careful eyes.",
    },
    {
        "id": "riddle_lock",
        "problem": "A cabinet lock had three letters, but no one could agree which pirate word would open it.",
        "clue": "A rhyme painted on the cabinet door mentioned a coin, a join, and a line.",
        "plan": "The child said the rhyme aloud, the captain wrote the matching words, and the crew tried one letter at a time.",
        "twist": "The answer was not a grand pirate password; it was NICKEL, the small coin named by the rhyme.",
        "ending": "The lock clicked open, and the crew found a bright red scarf tied around the missing ship key.",
    },
    {
        "id": "rolling_coin",
        "problem": "A nickel rolled beneath the cabinet just as the captain needed the cabinet moved away from the tide.",
        "clue": "The coin's soft ringing showed that the cabinet stood on a loose board.",
        "plan": "The crew made a human chain, passed a hook safely from hand to hand, and lifted the cabinet only when the captain called.",
        "twist": "The nickel had not caused the trouble; it had revealed the loose board before anyone tripped.",
        "ending": "The crew fixed the board, rescued the coin, and painted a gold arrow pointing to the safe deck.",
    },
]

RHYME_LINES = [
    "A nickel in a trick, makes a stuck door click.",
    "Find the coin, join the line, and the hidden latch will shine.",
    "When a little nickel rolls, teamwork steadies pirate souls.",
    "A small round gleam, can guide a careful team.",
]

JOKES = [
    "The parrot puffed up as if it had invented the whole mystery.",
    "The captain's hat leaned sideways, which was its way of thinking hard.",
    "One deckhand blamed a sea cucumber, but the sea cucumber was nowhere nearby.",
    "The parrot announced, 'Aha!' before anyone had actually found an aha.",
    "The crew marched in a line so straight that even the shadows looked organized.",
]

ROUTES = [
    ("At dawn", "Then", "At last"),
    ("Under a silver moon", "Just when the crew felt puzzled", "With every hand helping"),
    ("Near the harbor bell", "After the first guess failed", "A moment later"),
    ("Beside the salty tide pools", "That was when Luna noticed", "Soon"),
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    name: str
    gender: str
    captain: str
    trait: str
    seed: Optional[int] = None
    incident: int = 0
    rhyme: int = 0
    route: int = 0
    joke: int = 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A pirate tale about a cabinet, a nickel, rhyme, teamwork, and a twist."
    )
    parser.add_argument("--place", choices=SETTINGS.keys())
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--captain", choices=CAPTAINS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    return StoryParams(
        place=args.place or rng.choice(list(SETTINGS)),
        name=name,
        gender=args.gender or GENDERS[name],
        captain=args.captain or rng.choice(CAPTAINS),
        trait=args.trait or rng.choice(TRAITS),
        incident=rng.randrange(len(INCIDENTS)),
        rhyme=rng.randrange(len(RHYME_LINES)),
        route=rng.randrange(len(ROUTES)),
        joke=rng.randrange(len(JOKES)),
    )


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError("The pirate ship needs a known setting.")
    if params.name not in NAMES:
        raise StoryError("The cabin child must have a known name.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("The cabin child must be a girl or boy.")
    if not 0 <= params.incident < len(INCIDENTS):
        raise StoryError("The cabinet mystery is not available.")
    if not 0 <= params.rhyme < len(RHYME_LINES):
        raise StoryError("The selected rhyme is not available.")


def _build_world(params: StoryParams) -> World:
    reasonableness_gate(params)
    incident = INCIDENTS[params.incident]
    opening, turn, ending_turn = ROUTES[params.route % len(ROUTES)]
    world = World(place=SETTINGS[params.place]["place"])

    child = world.add(Entity(
        id="Child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"curiosity": 1.0, "confidence": 0.6},
        memes={"team_spirit": 0.4},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label=params.captain,
        meters={"patience": 1.0, "worry": 0.7},
        memes={"trust": 0.5},
    ))
    cabinet = world.add(Entity(
        id="Cabinet",
        kind="thing",
        type="cabinet",
        label="cabinet",
        phrase="an old blue cabinet",
        meters={"drawer_open": 0.0, "stable": 0.0},
        memes={"mystery": 1.0},
    ))
    nickel = world.add(Entity(
        id="Nickel",
        kind="thing",
        type="nickel",
        label="nickel",
        phrase="a small five-cent nickel",
        owner="Child",
        meters={"under_cabinet": 1.0, "visible": 0.0},
        memes={"clue": 0.2},
    ))
    map_entity = world.add(Entity(
        id="Map",
        kind="thing",
        type="map",
        label="treasure map",
        phrase="a rolled treasure map",
        meters={"hidden": 1.0, "safe": 0.0},
    ))
    world.add(Entity(
        id="Lantern",
        kind="thing",
        type="lantern",
        label="lantern",
        phrase="a warm brass lantern",
        owner="Child",
        meters={"lit": 1.0},
    ))

    rhyme = RHYME_LINES[params.rhyme]
    plan = incident["plan"].replace("Luna", params.name)
    joke = JOKES[params.joke]

    world.say(
        f"{opening}, {params.name}, a {params.trait} {params.gender}, sailed with {params.captain} to {world.place}."
    )
    world.say(SETTINGS[params.place]["detail"])
    world.say(
        f"Beside the dock stood {cabinet.phrase}, and on its door someone had painted a strange rhyme: "
        f'"{rhyme}"'
    )
    world.say(
        f"The crew wanted the treasure map inside, but {incident['problem']}"
    )
    world.say(f"{joke}")
    world.para()

    world.say(
        f"{params.name} spotted {nickel.phrase} near the cabinet and lifted the lantern close."
    )
    world.say(f"{incident['clue']}")
    world.say(
        f'{params.name} asked, "Captain, should I pull the cabinet door?"'
    )
    world.say(
        f'{params.captain} answered, "Not yet. A clever pirate checks the clue before tugging with all their might."'
    )
    world.say(
        f'{params.name} said, "Then the rhyme is telling us to work together, not rush alone."'
    )
    world.say(f'{params.captain} replied, "Exactly. You read the words, and we will share the careful jobs."')
    world.say(turn + " " + plan + ".")
    world.say(
        "The crew repeated the jobs aloud so nobody grabbed, shoved, or stepped into another pirate's work."
    )
    world.para()

    world.say(f"The nickel moved, the cabinet settled, and the hidden catch gave a soft click.")
    world.say(f"{incident['twist']}")
    world.say(
        f"{ending_turn}, {incident['ending']}"
    )
    world.say(
        f"{params.name} smiled and said, 'A tiny coin and a good team can unlock a very big surprise.'"
    )
    world.say(
        f"{params.captain} nodded. 'That is the pirate way: use your eyes, share the work, and let a twist teach you something.'"
    )

    child.memes["team_spirit"] = 1.0
    captain.memes["trust"] = 1.0
    cabinet.meters["drawer_open"] = 1.0
    cabinet.meters["stable"] = 1.0
    nickel.meters["under_cabinet"] = 0.0
    nickel.meters["visible"] = 1.0
    nickel.memes["clue"] = 1.0
    map_entity.meters["hidden"] = 0.0
    map_entity.meters["safe"] = 1.0

    world.facts.update(
        params=params,
        incident=incident,
        rhyme=rhyme,
        plan=plan,
        child=child,
        captain=captain,
        cabinet=cabinet,
        nickel=nickel,
        map=map_entity,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a child-friendly Pirate Tale about {p.name}, a cabinet, and a nickel.",
        "Write a pirate story using rhyme, teamwork, and a surprising twist to solve a cabinet mystery.",
        f"Tell a gentle pirate adventure in which {p.name} discovers that a small nickel is an important clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    incident = world.facts["incident"]
    return [
        QAItem(
            question="Where did the pirate mystery happen?",
            answer=f"The pirate mystery happened in {world.place}, beside an old blue cabinet.",
        ),
        QAItem(
            question="What problem did the crew face?",
            answer=incident["problem"],
        ),
        QAItem(
            question="How did the nickel help?",
            answer=incident["clue"],
        ),
        QAItem(
            question="How did the crew use teamwork?",
            answer=f"{incident['plan']} They shared the jobs and checked the clue before opening the cabinet.",
        ),
        QAItem(
            question="What was the twist?",
            answer=incident["twist"],
        ),
        QAItem(
            question=f"What did {p.name} learn?",
            answer="A small clue can matter, and careful teamwork is better than rushing alone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cabinet?",
            answer="A cabinet is a piece of furniture with shelves or drawers for storing things.",
        ),
        QAItem(
            question="What is a nickel?",
            answer="A nickel is a coin worth five cents in the United States.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme uses words with matching or similar ending sounds.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people share jobs and help one another reach a goal.",
        ),
        QAItem(
            question="What is a pirate?",
            answer="A pirate is a sailor in an adventure story who travels by ship and searches for treasure.",
        ),
    ]


ASP_RULES = r"""
#show compatible/1.
compatible(story) :- cabinet_present, nickel_present, rhyme_used,
                      teamwork_used, twist_resolved, dialogue_present.
"""


def asp_facts() -> str:
    return "\n".join([
        "cabinet_present.",
        "nickel_present.",
        "rhyme_used.",
        "teamwork_used.",
        "twist_resolved.",
        "dialogue_present.",
    ])


def asp_program(show: str = "#show compatible/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        from storyworlds import asp
        symbols = asp.one_model(asp_program())
        compatible = asp.atoms(symbols, "compatible")
        if compatible != [("story",)]:
            return 1
    except Exception:
        return 1

    for params in CURATED:
        sample = generate(params)
        text = sample.story.lower()
        required = ["cabinet", "nickel", "rhyme", "teamwork", "twist"]
        if any(word not in text for word in required):
            return 1
        if '"' not in sample.story and "'" not in sample.story:
            return 1
        if not sample.story_qa:
            return 1
    return 0


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
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
            f"  {entity.id:8} ({entity.type:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moonlit_cove", name="Luna", gender="girl", captain="Captain Bea",
        trait="curious", incident=0, rhyme=0, route=0, joke=0
    ),
    StoryParams(
        place="parrot_island", name="Finn", gender="boy", captain="Captain Sol",
        trait="brave", incident=1, rhyme=1, route=1, joke=2
    ),
    StoryParams(
        place="foggy_bay", name="Mara", gender="girl", captain="Captain Uma",
        trait="patient", incident=2, rhyme=2, route=2, joke=3
    ),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            from storyworlds import asp
            symbols = asp.one_model(asp_program())
            print(" ".join(str(symbol) for symbol in symbols))
        except Exception as exc:
            raise StoryError(f"ASP mode could not run: {exc}") from exc
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.name}: pirate cabinet mystery"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
