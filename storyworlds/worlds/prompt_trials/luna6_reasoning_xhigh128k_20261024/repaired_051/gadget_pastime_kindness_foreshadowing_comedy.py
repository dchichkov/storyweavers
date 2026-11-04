#!/usr/bin/env python3
"""
A small comedy storyworld about a pastime, a homemade gadget, and a kind choice.

Each tale begins with a warning from a gadget, turns when that warning proves
useful, and ends with the friends helping someone before returning to their
pastime.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


_ROOT = None
for _parent in Path(__file__).resolve().parents:
    if (_parent / "storyworlds" / "results.py").is_file():
        _ROOT = _parent
        break
if _ROOT is not None and str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SCENARIOS: list[dict[str, str]] = [
    {
        "key": "pond_boats",
        "gadget_key": "puff_puff_fan",
        "pastime_key": "paper_boat_racing",
        "gadget": "Puff-Puff Fan",
        "pastime": "paper-boat racing",
        "place": "Puddlewick Pond",
        "setup": "Their homemade {gadget} was meant to send folded boats gliding without anyone splashing in the water.",
        "neighbor_intro": "{neighbor}, a {neighbor_type}, was folding a tiny paper boat around a surprise paper sun for her grandpa.",
        "foreshadow": "Before the race, a yellow feather on the {gadget} trembled toward the reed tunnel whenever its crank turned.",
        "mishap": "{hero} spun the crank as fast as she could. A wall of air flipped the start flags and swept {neighbor}'s little boat under the low boardwalk.",
        "reaction": "{neighbor} peered into the shadow, worried that the paper sun for her grandpa was stuck there too.",
        "mistake": "{hero} reached under the boardwalk with a stick, but the splash only nudged the boat deeper into the dark.",
        "dialogue_one": "“Our race is waiting,” {hero} said, then glanced at {neighbor}. “Should we keep going?”",
        "dialogue_two": "“Not while {neighbor} is worried,” {friend} replied. “That feather showed which way the fan pushes. Tiny puffs could guide her boat back.”",
        "dialogue_three": "“Then we help first,” {hero} said. “I'll follow your little puffs.”",
        "repair_action": "{friend} tilted the fan toward the pond entrance and turned its handle in tiny strokes while {hero} guided a broad reed from the bank.",
        "success": "The gentle breeze brought {neighbor}'s boat within reach, and {hero} lifted it out with the reed without stepping into the pond.",
        "share": "{neighbor} joined the race with her rescued boat, and this time the friends used one careful puff at a time.",
        "comic": "The goose referee awarded the slowest boat a ribbon for its “excellent sightseeing.”",
        "ending": "Their boats floated side by side beneath the flags while the goose referee wore one flag as a very lopsided hat.",
        "gadget_job": "send folded boats gliding without touching the water",
        "warning_answer": "The fan's yellow feather trembled toward the reed tunnel when its crank turned. It hinted at where a strong puff would send the boat.",
        "turn_answer": "A hard gust swept the boat under the boardwalk, and reaching for it with a stick pushed it farther away.",
        "kindness_answer": "They set their race aside to help their worried neighbor, then used tiny puffs and a reed from the bank to retrieve her boat.",
        "outcome_answer": "The boat and its paper sun were recovered, and their neighbor joined the race. The goose referee's crooked flag hat showed that the game had become a shared joke.",
    },
    {
        "key": "painted_bubbles",
        "gadget_key": "bubble_booster",
        "pastime_key": "bubble_painting",
        "gadget": "Bubble-Booster",
        "pastime": "bubble painting",
        "place": "the Sunpatch garden wall",
        "setup": "The {gadget} blew paint-tinted bubbles that left round marks on pictures.",
        "neighbor_intro": "{neighbor}, a {neighbor_type}, was painting a sunset card to give her grandmother.",
        "foreshadow": "Before they started, the blue cap on the {gadget} whistled whenever its handle was squeezed twice, then fell quiet.",
        "mishap": "{hero} squeezed the handle six times without pausing. A booming cloud of bubbles burst across {neighbor}'s wet sunset and dragged blue paint into a crooked streak.",
        "reaction": "{neighbor} stared at the streak, while the friends' bright bubble pictures suddenly seemed less important.",
        "mistake": "{hero} tried to wipe the mark with a sleeve, mixing the blue and orange paint into a purple thumbprint.",
        "dialogue_one": "“I'm sorry, {neighbor}. What would you like us to do?” {hero} asked.",
        "dialogue_two": "“The streak could be a moon,” {neighbor} replied. “Could we turn the whole picture into a night sky?”",
        "dialogue_three": "“Yes,” {friend} said. “And that little whistle means gentle squeezes, not six big ones.”",
        "repair_action": "{neighbor} chose the moon, {hero} dabbed purple stars around it with a brush, and {friend} loosened the cap so the {gadget} made small, neat bubbles.",
        "success": "{neighbor}'s sunset became the night-sky picture she wanted to give her grandmother.",
        "share": "The friends returned to bubble painting together, and {neighbor} showed them how to make a bubble moon without covering the whole sky.",
        "comic": "One tiny bubble landed on {hero}'s nose and stayed there like a shiny clown button.",
        "ending": "The moon-and-bubble picture dried on the wall while {hero} tried to admire it without cross-eyed nose-watching.",
        "gadget_job": "blow small, paint-tinted bubbles onto pictures",
        "warning_answer": "The Bubble-Booster's cap whistled after two squeezes. The whistle warned that the next puffs needed to be gentle.",
        "turn_answer": "Six fast squeezes covered the neighbor's wet sunset with bubbles, and wiping the streak spread the paint into a purple mark.",
        "kindness_answer": "They asked their neighbor what she wanted instead of choosing for her. She asked them to turn the streak into a moon, and they helped paint the night sky.",
        "outcome_answer": "Their neighbor chose to give her grandmother the new night-sky picture. They also learned to use the Bubble-Booster in gentle squeezes, as the whistle had warned.",
    },
    {
        "key": "leaf_kites",
        "gadget_key": "ribbon_twirler",
        "pastime_key": "leaf_kite_decorating",
        "gadget": "Ribbon-Twirler",
        "pastime": "leaf-kite decorating",
        "place": "Bramble Hill",
        "setup": "The {gadget} wound bright ribbon tails onto the friends' leaf kites.",
        "neighbor_intro": "{neighbor}, a {neighbor_type}, had decorated a small kite with pressed leaves to fly with her little brother.",
        "foreshadow": "As the spool filled, the {gadget}'s brass axle clicked twice, and a loose ribbon quivered toward a low apple branch.",
        "mishap": "{hero} kept winding past the double click. The ribbon sprang free, looped over the branch, and tugged {neighbor}'s kite into the leaves.",
        "reaction": "{neighbor} held the kite's handle and looked up at its tangled tail.",
        "mistake": "{friend} yanked the ribbon, and the branch bobbed a shower of leaves onto their heads; one landed over {hero}'s ears like lettuce.",
        "dialogue_one": "“I can pull harder,” {hero} said, brushing a leaf from her ear.",
        "dialogue_two": "“That double click meant the spool was full,” {friend} replied. “If we unwind a little, the ribbon will slacken instead of tugging {neighbor}'s kite.”",
        "dialogue_three": "“Could you hold its handle while I guide the ribbon?” {neighbor} asked. “We'll do it slowly together,” {hero} replied.",
        "repair_action": "{friend} unwound the spool in small turns while {hero} held the kite steady and {neighbor} freed the ribbon from the low branch.",
        "success": "The tail came loose, and {neighbor}'s pressed-leaf kite stayed whole for its flight with her little brother.",
        "share": "They decorated a short new tail together, stopping at the double click, and let {neighbor} take the first turn flying her kite.",
        "comic": "The leaf on {hero}'s ear stayed put long enough for a sparrow to inspect it as a possible salad.",
        "ending": "Three leaf kites bobbed above the hill, their ribbons drawing bright loops while the sparrow watched from a branch.",
        "gadget_job": "wind colorful tails onto leaf kites",
        "warning_answer": "The Ribbon-Twirler clicked twice when its spool was full, and its loose ribbon quivered toward the nearby branch. The warning foretold that winding farther could tangle the tail.",
        "turn_answer": "Winding past the double click sent ribbon around a branch and caught the neighbor's kite. Yanking only shook more leaves loose.",
        "kindness_answer": "They listened when their neighbor asked them to hold the kite and guide its ribbon slowly. The friend unwound the spool while the others freed the tail.",
        "outcome_answer": "Their neighbor's kite was safe for its flight with her little brother, and the friends decorated another kite while watching for the spool's double click.",
    },
]

GADGET_REGISTRY = {item["gadget_key"]: item["gadget"] for item in SCENARIOS}
PASTIME_REGISTRY = {item["pastime_key"]: item["pastime"] for item in SCENARIOS}
ANIMAL_TYPES = (
    "badger",
    "duck",
    "fox",
    "hedgehog",
    "mouse",
    "otter",
    "rabbit",
    "squirrel",
    "turtle",
)
HERO_NAMES = ("Nori", "Bram", "Lulu", "Pip", "Moss", "Juniper")
FRIEND_NAMES = ("Kit", "Mallow", "Tansy", "Ollie", "Wren", "Poppy")
NEIGHBOR_NAMES = ("Tansy", "Mallow", "Fern", "Clover", "Pip", "Basil")
OPENINGS = (
    "One bright Saturday morning",
    "Just as the sun peeked over the rooftops",
    "After a robin's noisy warm-up",
    "On a breezy day made for trying things",
    "When the town path was still quiet",
    "As the clouds made room for sunshine",
    "Before the first lunch bell",
    "On a morning full of promising plans",
)


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "distance": 0.0,
            "pressure": 0.0,
            "calibration": 0.0,
            "completeness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "eagerness": 0.0,
            "kindness": 0.0,
            "trust": 0.0,
            "relief": 0.0,
            "delight": 0.0,
        }
    )


@dataclass
class Setting:
    place: str


@dataclass
class StoryParams:
    gadget: str
    pastime: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    neighbor_name: str
    neighbor_type: str
    scenario_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}
        self.state: dict[str, bool] = {
            "foreshadow_seen": False,
            "mishap": False,
            "kindness_chosen": False,
            "repair": False,
            "pastime_shared": False,
            "happy_ending": False,
        }
        self.trace_log: list[str] = []

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

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def _canonical_registry_value(value: str, registry: dict[str, str], field_name: str) -> str:
    folded = value.strip().casefold()
    for label in registry.values():
        if label.casefold() == folded:
            return label
    choices = ", ".join(registry.values())
    raise StoryError(f"Unknown {field_name} {value!r}. Choose one of: {choices}.")


def _canonical_type(value: str, field_name: str) -> str:
    folded = value.strip().casefold()
    if folded in ANIMAL_TYPES:
        return folded
    raise StoryError(f"Unknown {field_name} {value!r}. Choose an animal type such as rabbit, mouse, or turtle.")


def _validate_name(value: str, field_name: str) -> str:
    name = value.strip()
    if not name or len(name) > 40 or not name[0].isalpha() or not name[-1].isalpha():
        raise StoryError(f"{field_name} must be a short name made of letters, spaces, apostrophes, or hyphens.")
    if any(not (character.isalpha() or character.isspace() or character in "'-") for character in name):
        raise StoryError(f"{field_name} must be a short name made of letters, spaces, apostrophes, or hyphens.")
    if any(character in "\r\n\t" for character in name):
        raise StoryError(f"{field_name} cannot contain a line break or tab.")
    return name


def _pick_distinct(rng: random.Random, options: tuple[str, ...], used: set[str]) -> str:
    choices = [option for option in options if option.casefold() not in used]
    return rng.choice(choices)


def _scenario_for_params(params: StoryParams) -> dict[str, str]:
    if not isinstance(params.scenario_index, int) or not 0 <= params.scenario_index < len(SCENARIOS):
        raise StoryError(f"scenario_index must be between 0 and {len(SCENARIOS) - 1}.")
    scenario = SCENARIOS[params.scenario_index]
    gadget = _canonical_registry_value(params.gadget, GADGET_REGISTRY, "gadget")
    pastime = _canonical_registry_value(params.pastime, PASTIME_REGISTRY, "pastime")
    if gadget.casefold() != scenario["gadget"].casefold() or pastime.casefold() != scenario["pastime"].casefold():
        raise StoryError(
            f"{gadget} is not paired with {pastime} in scenario {params.scenario_index}. "
            "Choose a registered gadget and pastime pair."
        )
    return scenario


def reasonableness_gate(params: StoryParams) -> dict[str, str]:
    """Validate that the requested cast and registered gadget-pastime pair make sense."""
    scenario = _scenario_for_params(params)
    _validate_name(params.hero_name, "hero name")
    _validate_name(params.friend_name, "friend name")
    _validate_name(params.neighbor_name, "neighbor name")
    names = (params.hero_name.casefold(), params.friend_name.casefold(), params.neighbor_name.casefold())
    if len(set(names)) != len(names):
        raise StoryError("The hero, friend, and neighbor must have different names.")
    _canonical_type(params.hero_type, "hero type")
    _canonical_type(params.friend_type, "friend type")
    _canonical_type(params.neighbor_type, "neighbor type")
    if not isinstance(params.detail_variant, int):
        raise StoryError("detail_variant must be an integer.")
    return scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Make a funny, kind story about a pastime and a gadget."
    )
    parser.add_argument("--gadget", help="Choose a registered gadget.")
    parser.add_argument("--pastime", help="Choose a registered pastime.")
    parser.add_argument("--name", help="Hero's name.")
    parser.add_argument("--type", "--animal", dest="hero_type", help="Hero's animal type.")
    parser.add_argument("--friend", help="Friend's name.")
    parser.add_argument("--friend-type", help="Friend's animal type.")
    parser.add_argument("--neighbor", help="Neighbor's name.")
    parser.add_argument("--neighbor-type", help="Neighbor's animal type.")
    parser.add_argument("-n", type=int, default=1, help="Number of stories to generate.")
    parser.add_argument("--all", action="store_true", help="Generate one story for every registered pair.")
    parser.add_argument("--seed", type=int, default=None, help="Seed for repeatable story choices.")
    parser.add_argument("--trace", action="store_true", help="Show the simulated world state.")
    parser.add_argument("--qa", action="store_true", help="Show prompts and questions with answers.")
    parser.add_argument("--json", action="store_true", help="Emit the shared JSON result format.")
    parser.add_argument("--asp", action="store_true", help="Solve the inline ASP twin.")
    parser.add_argument("--verify", action="store_true", help="Check Python and ASP parity and exercise stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the inline ASP program and its facts.")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    explicit_gadget = args.gadget is not None
    explicit_pastime = args.pastime is not None

    gadget = (
        _canonical_registry_value(args.gadget, GADGET_REGISTRY, "gadget")
        if explicit_gadget
        else None
    )
    pastime = (
        _canonical_registry_value(args.pastime, PASTIME_REGISTRY, "pastime")
        if explicit_pastime
        else None
    )

    candidates = [
        (index, scenario)
        for index, scenario in enumerate(SCENARIOS)
        if (gadget is None or scenario["gadget"] == gadget)
        and (pastime is None or scenario["pastime"] == pastime)
    ]
    if not candidates:
        raise StoryError(
            f"{gadget} and {pastime} are not a registered gadget-pastime pair. "
            "Choose a matching pair."
        )
    scenario_index, scenario = rng.choice(candidates)

    hero_name = args.name if args.name is not None else rng.choice(HERO_NAMES)
    hero_name = _validate_name(hero_name, "hero name")
    used = {hero_name.casefold()}

    friend_name = args.friend if args.friend is not None else _pick_distinct(rng, FRIEND_NAMES, used)
    friend_name = _validate_name(friend_name, "friend name")
    if friend_name.casefold() in used:
        raise StoryError("The hero and friend must have different names.")
    used.add(friend_name.casefold())

    neighbor_name = args.neighbor if args.neighbor is not None else _pick_distinct(rng, NEIGHBOR_NAMES, used)
    neighbor_name = _validate_name(neighbor_name, "neighbor name")
    if neighbor_name.casefold() in used:
        raise StoryError("The hero, friend, and neighbor must have different names.")

    hero_type = _canonical_type(args.hero_type or rng.choice(ANIMAL_TYPES), "hero type")
    friend_type = _canonical_type(args.friend_type or rng.choice(ANIMAL_TYPES), "friend type")
    neighbor_type = _canonical_type(args.neighbor_type or rng.choice(ANIMAL_TYPES), "neighbor type")

    return StoryParams(
        gadget=scenario["gadget"],
        pastime=scenario["pastime"],
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        neighbor_name=neighbor_name,
        neighbor_type=neighbor_type,
        scenario_index=scenario_index,
        detail_variant=rng.randrange(100_000),
    )


def _fill(template: str, **values: str) -> str:
    try:
        return template.format(**values)
    except KeyError as exc:
        raise StoryError(f"Story scenario is missing a narrative detail: {exc.args[0]}.") from exc


def tell(params: StoryParams) -> World:
    scenario = reasonableness_gate(params)
    world = World(Setting(place=scenario["place"]))
    hero = world.add(
        Entity(
            id="hero",
            kind="animal",
            type=_canonical_type(params.hero_type, "hero type"),
            label=params.hero_name,
        )
    )
    friend = world.add(
        Entity(
            id="friend",
            kind="animal",
            type=_canonical_type(params.friend_type, "friend type"),
            label=params.friend_name,
        )
    )
    neighbor = world.add(
        Entity(
            id="neighbor",
            kind="animal",
            type=_canonical_type(params.neighbor_type, "neighbor type"),
            label=params.neighbor_name,
        )
    )
    gadget = world.add(
        Entity(
            id="gadget",
            kind="thing",
            type="gadget",
            label=scenario["gadget"],
            owner=hero.id,
        )
    )
    pastime = world.add(
        Entity(
            id="pastime",
            kind="activity",
            type="pastime",
            label=scenario["pastime"],
        )
    )
    world.facts.update(
        hero=hero,
        friend=friend,
        neighbor=neighbor,
        gadget=gadget,
        pastime=pastime,
        scenario=scenario,
    )

    hero.memes["eagerness"] = 1.0
    friend.memes["trust"] = 1.0
    gadget.meters["calibration"] = 0.5
    names = {
        "hero": hero.label,
        "friend": friend.label,
        "neighbor": neighbor.label,
        "neighbor_type": neighbor.type,
        "gadget": gadget.label,
    }

    opening = OPENINGS[params.detail_variant % len(OPENINGS)]
    world.say(
        f"{opening}, {hero.label} the {hero.type} and {friend.label} the {friend.type} "
        f"met at {world.setting.place} for their favorite pastime, {pastime.label}."
    )
    world.say(_fill(scenario["setup"], **names))
    world.say(_fill(scenario["neighbor_intro"], **names))
    world.para()

    world.say(_fill(scenario["foreshadow"], **names))
    gadget.meters["calibration"] = 0.25
    gadget.memes["worry"] = 0.2
    world.state["foreshadow_seen"] = True
    world.log("The gadget gave a clear warning before the mishap.")

    world.say(_fill(scenario["mishap"], **names))
    world.state["mishap"] = True
    gadget.meters["pressure"] = 1.0
    hero.memes["worry"] = 1.0
    neighbor.memes["worry"] = 1.0
    world.say(_fill(scenario["reaction"], **names))
    world.say(_fill(scenario["mistake"], **names))
    friend.memes["concern"] = 1.0
    world.para()

    world.say(_fill(scenario["dialogue_one"], **names))
    world.say(_fill(scenario["dialogue_two"], **names))
    world.say(_fill(scenario["dialogue_three"], **names))
    world.state["kindness_chosen"] = True
    hero.memes["kindness"] = 1.0
    friend.memes["kindness"] = 1.0
    friend.memes["trust"] += 1.0
    world.log("The friends paused their pastime and chose a repair that answered their neighbor's need.")

    world.say(_fill(scenario["repair_action"], **names))
    gadget.meters["pressure"] = 0.15
    gadget.meters["calibration"] = 1.0
    gadget.memes["worry"] = 0.0
    world.state["repair"] = True
    world.say(_fill(scenario["success"], **names))
    neighbor.memes["worry"] = 0.0
    neighbor.memes["relief"] = 1.0
    world.para()

    world.say(_fill(scenario["share"], **names))
    world.state["pastime_shared"] = True
    hero.memes["eagerness"] = 0.0
    hero.memes["delight"] = 1.0
    friend.memes["delight"] = 1.0
    neighbor.memes["delight"] = 1.0
    gadget.meters["completeness"] = 1.0
    world.say(_fill(scenario["comic"], **names))
    world.say(_fill(scenario["ending"], **names))
    world.state["happy_ending"] = True
    world.log("The pastime resumed with the neighbor included and the gadget used more carefully.")
    return world


def python_reasonableness(world: World) -> bool:
    state = world.state
    if not state["foreshadow_seen"] or not state["mishap"]:
        return False
    if state["kindness_chosen"] and not state["mishap"]:
        return False
    if state["repair"] and not state["kindness_chosen"]:
        return False
    if state["pastime_shared"] and not state["repair"]:
        return False
    if state["happy_ending"] and not state["pastime_shared"]:
        return False
    neighbor: Entity = world.facts["neighbor"]
    gadget: Entity = world.facts["gadget"]
    return neighbor.memes["relief"] > 0 and gadget.meters["calibration"] == 1.0


def check_world_reasonableness(world: World) -> None:
    if not python_reasonableness(world):
        raise StoryError("The simulated story did not reach a kind, repaired, shared ending.")


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    neighbor: Entity = world.facts["neighbor"]
    gadget: Entity = world.facts["gadget"]
    pastime: Entity = world.facts["pastime"]
    return [
        f"Write a funny, child-friendly story about {hero.label} and {friend.label} enjoying {pastime.label}.",
        f"Tell a story where {gadget.label} gives an early warning, and the friends use kindness to help {neighbor.label}.",
        f"Make the gadget's warning matter when {hero.label} and {friend.label} return to their pastime of {scenario['pastime']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    neighbor: Entity = world.facts["neighbor"]
    gadget: Entity = world.facts["gadget"]
    pastime: Entity = world.facts["pastime"]
    values = {
        "hero": hero.label,
        "friend": friend.label,
        "neighbor": neighbor.label,
        "gadget": gadget.label,
    }
    return [
        QAItem(
            question=f"What pastime were {hero.label} and {friend.label} enjoying, and what was their gadget for?",
            answer=(
                f"They were enjoying {pastime.label}. They used the {gadget.label} to "
                f"{scenario['gadget_job']}."
            ),
        ),
        QAItem(
            question=f"What warning did the {gadget.label} give?",
            answer=scenario["warning_answer"],
        ),
        QAItem(
            question=f"What went wrong, and why did the first fix fail?",
            answer=scenario["turn_answer"],
        ),
        QAItem(
            question=f"How did {hero.label} and {friend.label} show kindness to {neighbor.label}?",
            answer=scenario["kindness_answer"],
        ),
        QAItem(
            question=f"How did things change by the end?",
            answer=scenario["outcome_answer"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gadget?",
            answer="A gadget is a small tool or device made to do a particular job, such as helping someone with a hobby.",
        ),
        QAItem(
            question="What is a pastime?",
            answer="A pastime is an activity someone enjoys doing in their free time, such as painting pictures or flying a kite.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is an early hint about something that will matter later. A warning sound or a wobbly part can help a character understand a later problem.",
        ),
        QAItem(
            question="What does kindness look like?",
            answer="Kindness means noticing what another person needs and choosing to help with care and respect.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        parts = [f"kind={entity.kind}", f"type={entity.type}"]
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{entity.id} ({entity.label}): " + ", ".join(parts))
    lines.append("events: " + " | ".join(world.trace_log))
    lines.append("state: " + ", ".join(f"{key}={value}" for key, value in world.state.items()))
    return "\n".join(lines)


ASP_RULES = r"""
:- selected_scenario(S), not scenario_pair(S,_,_).
:- selected_scenario(S), scenario_pair(S,G,P), chosen_gadget(H), G != H.
:- selected_scenario(S), scenario_pair(S,G,P), chosen_pastime(Q), P != Q.

valid_choice :-
    selected_scenario(S),
    scenario_pair(S,G,P),
    chosen_gadget(G),
    chosen_pastime(P).

story_turn :-
    valid_choice,
    foreshadow_seen,
    mishap_happened,
    kindness_chosen,
    repair_done.

kind_ending :-
    story_turn,
    pastime_shared.

:- not valid_choice.
:- not story_turn.
:- not kind_ending.

#show valid_choice/0.
#show story_turn/0.
#show kind_ending/0.
"""


def _asp_helpers():
    from storyworlds import asp

    return asp


def asp_facts(params: Optional[StoryParams] = None) -> str:
    """Emit both registry facts and the selected tale's ground facts."""
    asp = _asp_helpers()
    if params is None:
        params = StoryParams(
            gadget=SCENARIOS[0]["gadget"],
            pastime=SCENARIOS[0]["pastime"],
            hero_name="Nori",
            hero_type="rabbit",
            friend_name="Kit",
            friend_type="mouse",
            neighbor_name="Tansy",
            neighbor_type="turtle",
            scenario_index=0,
        )
    scenario = reasonableness_gate(params)
    facts: list[str] = []
    for index, item in enumerate(SCENARIOS):
        scenario_id = f"scenario_{index}"
        facts.append(asp.fact("registered_gadget", item["gadget_key"], item["gadget"]))
        facts.append(asp.fact("registered_pastime", item["pastime_key"], item["pastime"]))
        facts.append(
            asp.fact(
                "gadget_for",
                item["gadget_key"],
                item["pastime_key"],
            )
        )
        facts.append(
            asp.fact(
                "scenario_pair",
                scenario_id,
                item["gadget_key"],
                item["pastime_key"],
            )
        )
    facts.extend(
        [
            asp.fact("selected_scenario", f"scenario_{params.scenario_index}"),
            asp.fact("chosen_gadget", scenario["gadget_key"]),
            asp.fact("chosen_pastime", scenario["pastime_key"]),
            asp.fact("foreshadow_seen"),
            asp.fact("mishap_happened"),
            asp.fact("kindness_chosen"),
            asp.fact("repair_done"),
            asp.fact("pastime_shared"),
        ]
    )
    return "\n".join(facts)


def asp_program(params: Optional[StoryParams] = None) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES.strip()}\n"


def asp_verify() -> int:
    asp = _asp_helpers()
    expected = {"valid_choice/0", "story_turn/0", "kind_ending/0"}
    for index, scenario in enumerate(SCENARIOS):
        params = StoryParams(
            gadget=scenario["gadget"],
            pastime=scenario["pastime"],
            hero_name=("Nori", "Bram", "Lulu")[index],
            hero_type=("rabbit", "fox", "otter")[index],
            friend_name=("Kit", "Wren", "Moss")[index],
            friend_type=("mouse", "duck", "badger")[index],
            neighbor_name=("Tansy", "Mallow", "Fern")[index],
            neighbor_type=("turtle", "hedgehog", "squirrel")[index],
            scenario_index=index,
            detail_variant=100 + index,
            seed=100 + index,
        )
        sample = generate(params)
        if not python_reasonableness(sample.world):
            print(f"MISMATCH: Python reasoning gate failed for {scenario['key']}.")
            return 1
        if sample.story.count("“") < 2 or len(sample.story.split()) < 100:
            print(f"MISMATCH: generated story is incomplete for {scenario['key']}.")
            return 1
        if any(token in sample.story for token in ("{", "}", "None", "meters=", "memes=")):
            print(f"MISMATCH: internal scaffold leaked into {scenario['key']}.")
            return 1
        if len(sample.story_qa) < 4 or not all(item.answer.strip() for item in sample.story_qa):
            print(f"MISMATCH: story questions are incomplete for {scenario['key']}.")
            return 1

        model = asp.one_model(asp_program(params))
        actual = {f"{symbol.name}/{len(symbol.arguments)}" for symbol in model}
        if actual != expected:
            print(f"MISMATCH: ASP for {scenario['key']} returned {sorted(actual)}, expected {sorted(expected)}.")
            return 1

    print("OK: Python and ASP parity passed; every registered story was exercised.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    check_world_reasonableness(world)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        gadget=SCENARIOS[0]["gadget"],
        pastime=SCENARIOS[0]["pastime"],
        hero_name="Nori",
        hero_type="rabbit",
        friend_name="Kit",
        friend_type="mouse",
        neighbor_name="Tansy",
        neighbor_type="turtle",
        scenario_index=0,
        detail_variant=11,
    ),
    StoryParams(
        gadget=SCENARIOS[1]["gadget"],
        pastime=SCENARIOS[1]["pastime"],
        hero_name="Bram",
        hero_type="fox",
        friend_name="Wren",
        friend_type="duck",
        neighbor_name="Mallow",
        neighbor_type="hedgehog",
        scenario_index=1,
        detail_variant=23,
    ),
    StoryParams(
        gadget=SCENARIOS[2]["gadget"],
        pastime=SCENARIOS[2]["pastime"],
        hero_name="Lulu",
        hero_type="otter",
        friend_name="Moss",
        friend_type="badger",
        neighbor_name="Fern",
        neighbor_type="squirrel",
        scenario_index=2,
        detail_variant=37,
    ),
]


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program(CURATED[0]))
            return
        if args.verify:
            raise SystemExit(asp_verify())

        if args.asp:
            seed = args.seed if args.seed is not None else random.randrange(2**31)
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            asp = _asp_helpers()
            model = asp.one_model(asp_program(params))
            print("ASP model:", " ".join(str(atom) for atom in model))
            return

        if args.n < 1 and not args.all:
            raise StoryError("-n must be at least 1.")
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)

        if args.all:
            samples = [generate(params) for params in CURATED]
        else:
            samples: list[StorySample] = []
            seen: set[str] = set()
            attempt = 0
            limit = max(args.n * 30, 30)
            while len(samples) < args.n and attempt < limit:
                seed = base_seed + attempt
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
                attempt += 1
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
            header = f"### variant {index + 1}" if len(samples) > 1 and not args.all else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
