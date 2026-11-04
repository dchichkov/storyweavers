#!/usr/bin/env python3
"""
A small animal-story world set in a picnic meadow.

A squirrel is eager to begin a picnic, a hedgehog offers help, and a kind
rabbit makes room for a new friend. A rushed choice spoils the berry tart.
Depending on the ending, the squirrel accepts the kindness offered or walks
home alone.

The picnic card marked “tuvwxy” is part of the animals' letter hunt.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_STORYWORLDS_DIR = None
for _parent in Path(__file__).resolve().parents:
    if (_parent / "results.py").is_file():
        _STORYWORLDS_DIR = _parent
        break
if _STORYWORLDS_DIR is None:
    raise ImportError("Could not locate storyworlds/results.py")
sys.path.insert(0, str(_STORYWORLDS_DIR))

from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "object"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    indoor: bool = False
    affords: frozenset[str] = frozenset()


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


# ---------------------------------------------------------------------------
# Registries and parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "picnic_meadow"
    incident: str = "wind"
    ending: str = "bad"
    squirrel_name: str = "Nibs"
    rabbit_name: str = "Mira"
    hedgehog_name: str = "Pip"
    opening: int = 0
    dialogue_style: int = 0
    ending_image: int = 0
    seed: Optional[int] = None


SETTINGS = {
    "picnic_meadow": Setting(
        id="picnic_meadow",
        place="picnic meadow",
        indoor=False,
        affords=frozenset({"wind", "rain", "ants"}),
    )
}

ENDINGS = ("bad", "kind")

INCIDENTS = {
    "wind": {
        "description": "a sudden gust tugging at the picnic cloth",
        "signal": "A gust tugged at one corner and sent the napkin spinning across the clover.",
        "offers": [
            "I brought smooth pebbles. May I hold down the corners?",
            "The breeze is lifting the cloth. These pebbles can weigh it down.",
            "Could I help? Flat stones will keep the blanket still.",
        ],
        "bad_action": "{squirrel} darted after the napkin instead of letting {hedgehog} weigh down the cloth.",
        "mishap": "The cloth snapped, {squirrel}'s elbow nudged the plate, and the berry tart slid into damp grass.",
        "cause": "the blanket corner was loose, and the squirrel rushed after the napkin before the plate was steady",
        "help_question": "set the pebbles on the corners while I gather the clean food",
        "repair": "{hedgehog} set smooth pebbles on the four corners while {rabbit} moved the clean oatcakes into the dry basket.",
    },
    "rain": {
        "description": "a gray cloud bringing cold drops to the blanket",
        "signal": "A gray cloud slid over the sun, and cold drops began tapping the cloth.",
        "offers": [
            "The oak is dry beneath its branches. Shall I show you?",
            "We can carry the food under the oak together, if you like.",
            "I know a sheltered place beneath that oak. Let me help you move the picnic.",
        ],
        "bad_action": "{squirrel} grabbed the tart tin and hurried toward the oak alone.",
        "mishap": "The tin tilted in {squirrel}'s paws, and the berry tart slipped face-down into wet grass.",
        "cause": "the squirrel hurried with the tart tin alone, so it tipped before the group reached shelter",
        "help_question": "carry the dry food beneath the oak with me",
        "repair": "{hedgehog} held the basket level while {rabbit} carried the clean oatcakes beneath the oak's broad branches.",
    },
    "ants": {
        "description": "a line of ants following crumbs toward the picnic basket",
        "signal": "A narrow line of ants appeared beside the basket, following crumbs toward the food.",
        "offers": [
            "We can move the basket beyond their path and leave the ants room to pass.",
            "The ants are following these crumbs. May I help move the food away from their trail?",
            "Let's carry the picnic to that flat stone without blocking the ants' path.",
        ],
        "bad_action": "{squirrel} yanked the basket toward himself before {hedgehog} could help.",
        "mishap": "The basket caught on the cloth; the tin tipped, and the berry tart landed in the grass beside the ant trail.",
        "cause": "the squirrel tugged the basket alone, and it caught on the cloth before the tart tin tipped",
        "help_question": "move the clean oatcakes to that flat stone beyond the ants' path",
        "repair": "{rabbit} carried the clean oatcakes to a flat stone while {hedgehog} moved the basket away from the trail, leaving the ants a clear path.",
    },
}

SQUIRREL_NAMES = ["Nibs", "Tansy", "Acorn", "Pipkin"]
RABBIT_NAMES = ["Mira", "Clover", "Luma", "Bramble"]
HEDGEHOG_NAMES = ["Pip", "Hazel", "Moss", "Fern"]

OPENINGS = [
    "Clover-scented air drifted through {place} as {squirrel}, a squirrel, spread a red-checkered blanket.",
    "The sun warmed {place} while {squirrel}, a squirrel with a picnic basket, chose a soft patch of grass.",
    "At {place}, {squirrel}, a squirrel, hurried to lay out a blanket before anyone could ask for the first treat.",
]

REFUSALS = [
    "I can manage. Please do not touch the tart.",
    "We are fine. I want to start eating now.",
    "Let me finish setting this out before you fuss over it.",
]

RABBIT_REPLIES = [
    "There is room for one more. Let us listen before we rush.",
    "Pip came to help, and we can make a place for Pip.",
    "We can solve the picnic problem together. Please hear Pip out.",
]

BAD_ENDINGS = [
    "At sunset, {squirrel} carried the empty tart tin home alone; beneath the oak, the card marked “tuvwxy” rested beside a place left open.",
    "{rabbit} and {hedgehog} finished the clean oatcakes together, while {squirrel} walked home alone with the empty tin.",
    "The picnic ended without its tart. {squirrel} went home alone, and the little “tuvwxy” card lay flat on the quiet blanket.",
]

KIND_ENDINGS = [
    "The three friends shared oatcakes beneath the oak; the tart was still gone, but the little “tuvwxy” card stayed dry between them.",
    "The empty tart tin sat beside three sets of oatcake crumbs as the friends leaned together over their letter card.",
    "Under the oak, {squirrel} helped hold the blanket flat while {rabbit} and {hedgehog} finished the oatcakes; only the lost tart was missing.",
]


# ---------------------------------------------------------------------------
# ASP twin and Python reasonableness gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
valid(P,I,E) :- setting(P), affords(P,I), incident(I), ending_kind(E).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for incident_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, incident_id))
    for incident_id in sorted(INCIDENTS):
        lines.append(asp.fact("incident", incident_id))
    for ending in ENDINGS:
        lines.append(asp.fact("ending_kind", ending))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple]:
    return sorted(
        (place_id, incident_id, ending)
        for place_id, setting in SETTINGS.items()
        for incident_id in setting.affords
        for ending in ENDINGS
    )


def asp_verify() -> int:
    try:
        asp_combinations = set(asp_valid())
    except ImportError as exc:
        print(f"ERROR: ASP verification needs clingo: {exc}")
        return 2

    python_combinations = set(python_valid())
    if asp_combinations != python_combinations:
        print("MISMATCH between clingo and Python reasonableness gates:")
        if asp_combinations - python_combinations:
            print("  only in clingo:", sorted(asp_combinations - python_combinations))
        if python_combinations - asp_combinations:
            print("  only in Python:", sorted(python_combinations - asp_combinations))
        return 1

    checked = 0
    for place, incident, ending in sorted(python_combinations):
        params = StoryParams(
            place=place,
            incident=incident,
            ending=ending,
            squirrel_name="Nibs",
            rabbit_name="Mira",
            hedgehog_name="Pip",
            seed=checked,
        )
        try:
            sample = generate(params)
        except StoryError as exc:
            print(f"ERROR: a valid ASP combination failed to generate: {exc}")
            return 1
        if (
            not sample.story.strip()
            or "tuvwxy" not in sample.story
            or '"' not in sample.story
            or "\n\n" not in sample.story
            or not sample.story_qa
            or not sample.world_qa
            or not sample.world.facts.get("tart_lost")
        ):
            print(f"ERROR: generated story did not pass quality checks: {place}, {incident}, {ending}")
            return 1
        checked += 1

    print(
        f"OK: clingo gate matches the Python gate ({len(python_combinations)} combinations); "
        f"all {checked} generated stories passed checks."
    )
    return 0


def _validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(
            f"Unknown place {params.place!r}. The available place is 'picnic_meadow' "
            "(picnic meadow)."
        )
    if params.incident not in INCIDENTS:
        choices = ", ".join(sorted(INCIDENTS))
        raise StoryError(f"Unknown picnic incident {params.incident!r}. Choose from: {choices}.")
    if params.ending not in ENDINGS:
        raise StoryError("Unknown ending. Choose 'bad' or 'kind'.")
    if (params.place, params.incident, params.ending) not in set(python_valid()):
        raise StoryError("That place, incident, and ending do not make a reasonable story.")

    names = [params.squirrel_name, params.rabbit_name, params.hedgehog_name]
    if any(not isinstance(name, str) or not name.strip() or name != name.strip() for name in names):
        raise StoryError("Character names must be non-empty and may not have leading or trailing spaces.")
    if len({name.casefold() for name in names}) != len(names):
        raise StoryError("The squirrel, rabbit, and hedgehog need different names.")

    for field_name, value, limit in (
        ("opening", params.opening, len(OPENINGS)),
        ("dialogue_style", params.dialogue_style, len(REFUSALS)),
        ("ending_image", params.ending_image, len(BAD_ENDINGS)),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < limit:
            raise StoryError(f"Invalid {field_name}; choose an index from 0 to {limit - 1}.")


# ---------------------------------------------------------------------------
# World construction and story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> StoryState:
    _validate_params(params)

    setting = SETTINGS[params.place]
    world = StoryState(setting=setting)
    incident = INCIDENTS[params.incident]
    squirrel_name = params.squirrel_name
    rabbit_name = params.rabbit_name
    hedgehog_name = params.hedgehog_name

    squirrel = world.add(
        Entity(
            id=squirrel_name,
            kind="character",
            type="squirrel",
            label=f"{squirrel_name}, the squirrel",
            traits=["eager", "impatient"],
            meters={"distance_from_group_m": 0.0, "energy": 0.85},
            memes={"impatience": 0.75, "pride": 0.65, "friendship": 0.25},
        )
    )
    rabbit = world.add(
        Entity(
            id=rabbit_name,
            kind="character",
            type="rabbit",
            label=f"{rabbit_name}, the rabbit",
            traits=["patient", "kind"],
            meters={"distance_from_group_m": 0.0, "energy": 0.8},
            memes={"kindness": 0.95, "concern": 0.5},
        )
    )
    hedgehog = world.add(
        Entity(
            id=hedgehog_name,
            kind="character",
            type="hedgehog",
            label=f"{hedgehog_name}, the hedgehog",
            traits=["helpful", "a little shy"],
            meters={"distance_from_group_m": 1.0, "energy": 0.7},
            memes={"hope": 0.45, "belonging": 0.2},
        )
    )

    blanket = world.add(
        Entity(
            id="blanket",
            type="picnic_blanket",
            label="red-checkered picnic blanket",
            owner=squirrel_name,
            meters={"corner_stability": 0.25, "dryness": 1.0},
        )
    )
    tart = world.add(
        Entity(
            id="berry_tart",
            type="picnic_food",
            label="berry tart",
            owner=squirrel_name,
            traits=["sweet", "in a small tin"],
            meters={"food_condition": 1.0, "distance_from_basket_m": 0.0},
        )
    )
    oatcakes = world.add(
        Entity(
            id="oatcakes",
            type="picnic_food",
            label="clean oatcakes",
            owner=rabbit_name,
            meters={"food_condition": 1.0, "dryness": 1.0},
        )
    )
    basket = world.add(
        Entity(
            id="basket",
            type="picnic_basket",
            label="picnic basket",
            owner=squirrel_name,
            meters={"upright": 1.0, "distance_from_group_m": 0.0},
        )
    )
    letter_card = world.add(
        Entity(
            id="letter_card",
            type="game_card",
            label="letter card marked tuvwxy",
            owner=rabbit_name,
            meters={"dryness": 1.0, "distance_from_blanket_m": 0.2},
        )
    )

    if params.incident == "wind":
        weather = world.add(
            Entity(
                id="gust",
                type="weather",
                label="a brisk gust",
                meters={"strength": 0.8},
            )
        )
    elif params.incident == "rain":
        weather = world.add(
            Entity(
                id="rain_cloud",
                type="weather",
                label="a passing rain cloud",
                meters={"rainfall": 0.2},
            )
        )
    else:
        weather = world.add(
            Entity(
                id="ant_trail",
                type="animal_trail",
                label="a line of ants following crumbs",
                traits=["small", "moving toward the crumbs"],
                meters={"distance_to_basket_m": 0.3},
                memes={"calm": 1.0},
            )
        )

    opening = OPENINGS[params.opening].format(
        place=setting.place,
        squirrel=squirrel_name,
    )
    offer = incident["offers"][params.dialogue_style]
    refusal = REFUSALS[params.dialogue_style]
    rabbit_reply = RABBIT_REPLIES[params.dialogue_style]

    world.say(opening)
    world.say(
        f'Beside the basket, {rabbit_name}, the rabbit, had placed a little card marked '
        f'“tuvwxy”—six letters for their meadow hunt.'
    )
    world.say(f"{incident['signal']} The berry tart was ready, but the picnic was not.")
    world.say(
        f'{hedgehog_name}, the hedgehog, paused at the blanket. "{offer}" '
        f'{squirrel_name} frowned. "{refusal}" '
        f'{rabbit_name} replied, "{rabbit_reply}"'
    )

    world.para()
    world.say(incident["bad_action"].format(squirrel=squirrel_name, hedgehog=hedgehog_name))
    world.say(incident["mishap"].format(squirrel=squirrel_name))
    world.say(
        f'"The tart is spoiled, but the oatcakes are clean," said {rabbit_name}. '
        f'"{hedgehog_name}, would you help me {incident["help_question"]}?"'
    )
    world.say(
        f'"Gladly," {hedgehog_name} answered. '
        f'{incident["repair"].format(rabbit=rabbit_name, hedgehog=hedgehog_name)}'
    )

    # Physical state follows the mishap and the helpful repair.
    tart.meters["food_condition"] = 0.0
    tart.meters["distance_from_basket_m"] = 1.2
    blanket.meters["corner_stability"] = 0.95
    basket.meters["upright"] = 1.0
    oatcakes.meters["food_condition"] = 1.0
    letter_card.meters["distance_from_blanket_m"] = 0.1
    squirrel.memes["impatience"] = 0.25 if params.ending == "kind" else 0.8
    rabbit.memes["concern"] = 0.2
    hedgehog.memes["hope"] = 0.9
    hedgehog.memes["belonging"] = 0.8
    world.facts["tart_lost"] = True
    world.facts["loss_cause"] = incident["cause"]
    world.facts["helper"] = hedgehog_name
    world.facts["method"] = incident["repair"]
    world.facts["incident_id"] = params.incident
    world.facts["ending"] = params.ending

    world.para()
    if params.ending == "bad":
        world.say(
            f'{rabbit_name} held out a clean oatcake. "You can still sit with us, '
            f'{squirrel_name}."'
        )
        world.say(
            f'"No. I wanted the tart. I am going home," {squirrel_name} said. '
            f'{hedgehog_name} called, "I will save you a place if you come back."'
        )
        world.say(
            BAD_ENDINGS[params.ending_image].format(
                squirrel=squirrel_name,
                rabbit=rabbit_name,
                hedgehog=hedgehog_name,
            )
        )
        squirrel.meters["distance_from_group_m"] = 4.0
        squirrel.memes["pride"] = 0.9
        squirrel.memes["friendship"] = 0.15
        world.facts["squirrel_choice"] = "turned down the invitation and went home alone"
        world.facts["resolution"] = "the rabbit and hedgehog shared the clean oatcakes"
    else:
        world.say(
            f'{squirrel_name} looked at the empty tart tin. "I am sorry I rushed and shut you out. '
            f'May I help?"'
        )
        world.say(
            f'"Yes," said {hedgehog_name}. "Hold this corner with me." '
            f'{squirrel_name} held the blanket steady while {rabbit_name} set out the oatcakes.'
        )
        world.say(
            KIND_ENDINGS[params.ending_image].format(
                squirrel=squirrel_name,
                rabbit=rabbit_name,
                hedgehog=hedgehog_name,
            )
        )
        squirrel.meters["distance_from_group_m"] = 0.2
        squirrel.memes["pride"] = 0.2
        squirrel.memes["friendship"] = 0.85
        squirrel.memes["remorse"] = 0.8
        world.facts["squirrel_choice"] = "apologized and joined the others"
        world.facts["resolution"] = "the three friends shared the clean oatcakes"

    world.facts.update(
        squirrel=squirrel,
        rabbit=rabbit,
        hedgehog=hedgehog,
        blanket=blanket,
        tart=tart,
        oatcakes=oatcakes,
        basket=basket,
        letter_card=letter_card,
        weather=weather,
        place=setting.place,
        incident=incident,
        ending_image=(
            BAD_ENDINGS[params.ending_image]
            if params.ending == "bad"
            else KIND_ENDINGS[params.ending_image]
        ),
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryState) -> list[str]:
    facts = world.facts
    incident = facts["incident"]
    return [
        f"Write a short animal story set in a picnic meadow about {facts['squirrel'].id}, "
        f"{facts['rabbit'].id}, and {facts['hedgehog'].id}.",
        f'Include the “tuvwxy” letter card, {incident["description"]}, and a spoken exchange '
        "that changes what one of the animals decides to do.",
        f"Give the picnic a {facts['ending']} ending, while showing kindness through a concrete "
        "offer of help and a clear consequence for the spoiled tart.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    facts = world.facts
    squirrel = facts["squirrel"].id
    rabbit = facts["rabbit"].id
    hedgehog = facts["hedgehog"].id
    incident = facts["incident"]

    if facts["ending"] == "bad":
        ending_answer = (
            f"{squirrel} turned down {rabbit}'s invitation and went home alone. "
            f"{rabbit} and {hedgehog} still shared the clean oatcakes, but the berry tart was lost."
        )
    else:
        ending_answer = (
            f"{squirrel} apologized for rushing and joined {rabbit} and {hedgehog}. "
            "They shared the clean oatcakes, although the berry tart could not be saved."
        )

    return [
        QAItem(
            question="What did the card marked “tuvwxy” mean?",
            answer=(
                f"It was the six-letter card {rabbit} brought for the animals' meadow hunt. "
                "The card gave their picnic a small game to play together."
            ),
        ),
        QAItem(
            question=f"What help did {hedgehog} offer?",
            answer=(
                f"{hedgehog} noticed {incident['description']} and offered to help with the picnic. "
                "That offer gave the others a safe, practical way to respond."
            ),
        ),
        QAItem(
            question="Why was the berry tart lost?",
            answer=(
                f"The tart was lost because {incident['cause']}. "
                "The clean oatcakes were still safe to share."
            ),
        ),
        QAItem(
            question=f"How did {rabbit} show kindness?",
            answer=(
                f"{rabbit} made room for {hedgehog}, listened to the offer of help, and invited "
                f"{squirrel} to stay even after the tart was spoiled."
            ),
        ),
        QAItem(
            question=f"What happened to {squirrel} at the end?",
            answer=ending_answer,
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a picnic blanket be useful?",
            answer=(
                "A picnic blanket gives people or animals a clean place to sit and helps keep "
                "their food off the grass."
            ),
        ),
        QAItem(
            question="How can someone be kind when a newcomer asks to join?",
            answer=(
                "Someone can listen, make room, and offer a useful task instead of turning the "
                "newcomer away."
            ),
        ),
        QAItem(
            question="What is a hedgehog?",
            answer=(
                "A hedgehog is a small mammal with short legs and protective spines on its back."
            ),
        ),
        QAItem(
            question="What is a thoughtful way to picnic near ants?",
            answer=(
                "People can keep food covered, move it away from the ants' trail, and leave the "
                "ants room to pass."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---", f"  place: {world.setting.place}"]
    for entity in world.entities.values():
        traits = f" traits={entity.traits}" if entity.traits else ""
        owner = f" owner={entity.owner}" if entity.owner else ""
        lines.append(
            f"  {entity.id} ({entity.type}){traits}{owner} "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  ending: {world.facts.get('ending')}")
    lines.append(f"  tart_lost: {world.facts.get('tart_lost')}")
    lines.append(f"  loss_cause: {world.facts.get('loss_cause')}")
    lines.append(f"  squirrel_choice: {world.facts.get('squirrel_choice')}")
    lines.append(f"  resolution: {world.facts.get('resolution')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI parameter handling
# ---------------------------------------------------------------------------

def _normalize_place(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip().lower().replace("-", "_")
    if cleaned in {"picnic_meadow", "picnic meadow"}:
        return "picnic_meadow"
    raise StoryError(
        f"Unknown place {value!r}. The available place is 'picnic meadow'."
    )


def _normalize_incident(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned not in INCIDENTS:
        choices = ", ".join(sorted(INCIDENTS))
        raise StoryError(f"Unknown incident {value!r}. Choose from: {choices}.")
    return cleaned


def _normalize_ending(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip().lower()
    if cleaned not in ENDINGS:
        raise StoryError("Unknown ending. Choose 'bad' or 'kind'.")
    return cleaned


def _choose_names(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str]:
    requested = [
        getattr(args, "name", None),
        getattr(args, "friend", None),
        getattr(args, "guest", None),
    ]
    pools = [SQUIRREL_NAMES, RABBIT_NAMES, HEDGEHOG_NAMES]
    labels = ["squirrel", "rabbit", "hedgehog"]
    chosen: list[str] = []
    used: set[str] = set()

    for label, name, pool in zip(labels, requested, pools):
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                raise StoryError(f"The {label}'s name must not be empty.")
            clean_name = name.strip()
            if clean_name.casefold() in used:
                raise StoryError("The squirrel, rabbit, and hedgehog need different names.")
        else:
            available = [candidate for candidate in pool if candidate.casefold() not in used]
            clean_name = rng.choice(available)
        chosen.append(clean_name)
        used.add(clean_name.casefold())

    return chosen[0], chosen[1], chosen[2]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = _normalize_place(getattr(args, "place", None)) or "picnic_meadow"
    incident_filter = _normalize_incident(getattr(args, "incident", None))
    ending_filter = _normalize_ending(getattr(args, "ending", None))
    incident = incident_filter or rng.choice(sorted(INCIDENTS))
    ending = ending_filter or rng.choice(ENDINGS)
    squirrel_name, rabbit_name, hedgehog_name = _choose_names(args, rng)

    params = StoryParams(
        place=place,
        incident=incident,
        ending=ending,
        squirrel_name=squirrel_name,
        rabbit_name=rabbit_name,
        hedgehog_name=hedgehog_name,
        opening=rng.randrange(len(OPENINGS)),
        dialogue_style=rng.randrange(len(REFUSALS)),
        ending_image=rng.randrange(len(BAD_ENDINGS)),
        seed=getattr(args, "seed", None),
    )
    _validate_params(params)
    return params


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal story world: a picnic meadow, a spoiled tart, and kindness."
    )
    parser.add_argument("--place", help="story setting (picnic meadow)")
    parser.add_argument("--incident", help="picnic mishap: wind, rain, or ants")
    parser.add_argument("--ending", help="choose a bad or kind ending")
    parser.add_argument("--name", help="name the squirrel")
    parser.add_argument("--friend", help="name the rabbit")
    parser.add_argument("--guest", help="name the hedgehog")
    parser.add_argument("-n", type=int, default=1, help="number of stories to generate")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument("--all", action="store_true", help="generate every valid incident and ending")
    parser.add_argument("--trace", action="store_true", help="print the simulated world state")
    parser.add_argument("--qa", action="store_true", help="print story and world questions")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--asp", action="store_true", help="list ASP-valid story combinations")
    parser.add_argument("--verify", action="store_true", help="compare ASP and Python gates and test stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return parser


def _all_samples(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    place = _normalize_place(getattr(args, "place", None)) or "picnic_meadow"
    incident_filter = _normalize_incident(getattr(args, "incident", None))
    ending_filter = _normalize_ending(getattr(args, "ending", None))
    names = _choose_names(args, random.Random(base_seed))
    samples: list[StorySample] = []
    index = 0

    for incident in sorted(INCIDENTS):
        if incident_filter is not None and incident != incident_filter:
            continue
        for ending in ENDINGS:
            if ending_filter is not None and ending != ending_filter:
                continue
            params = StoryParams(
                place=place,
                incident=incident,
                ending=ending,
                squirrel_name=names[0],
                rabbit_name=names[1],
                hedgehog_name=names[2],
                opening=index % len(OPENINGS),
                dialogue_style=index % len(REFUSALS),
                ending_image=index % len(BAD_ENDINGS),
                seed=base_seed + index,
            )
            samples.append(generate(params))
            index += 1
    return samples


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program())
            return
        if args.verify:
            sys.exit(asp_verify())
        if args.asp:
            combinations = asp_valid()
            print(f"{len(combinations)} valid story combinations:\n")
            for place, incident, ending in combinations:
                print(f"  {place:14} {incident:6} {ending}")
            return

        if args.n < 1 and not args.all:
            raise StoryError("The number of stories must be at least 1.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        if args.all:
            samples = _all_samples(args, base_seed)
        else:
            samples = []
            for index in range(args.n):
                sample_seed = base_seed + index
                rng = random.Random(sample_seed)
                params = resolve_params(args, rng)
                params.seed = sample_seed
                samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = f"### variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
