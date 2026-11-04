#!/usr/bin/env python3
"""
A tiny comedy storyworld about an inventive gadget, a favorite pastime, and
the small acts of kindness that keep everyone in the game.

Each scenario plants a peculiar clue in the gadget's behavior, then lets that
same clue help the characters solve a later mishap. The world tracks physical
meters and emotional memes so the story's changes have a concrete cause.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

_HERE = Path(__file__).resolve()
ROOT = next(
    (parent for parent in _HERE.parents if (parent / "storyworlds" / "results.py").is_file()),
    _HERE.parents[-1],
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


GADGETS = {
    "polka_bellows": {"label": "Polka-Dot Bellows"},
    "sock_seesaw": {"label": "Sock-Sorting Seesaw"},
    "wiggle_timer": {"label": "Whirly-Wiggle Timer"},
    "crumb_umbrella": {"label": "Crumb-Catching Umbrella"},
    "button_meter": {"label": "Button-Bopping Meter"},
    "echo_map": {"label": "Tin-Can Echo Map"},
    "tangle_spool": {"label": "Tangle-Taming Spool"},
    "puff_periscope": {"label": "Pancake-Puff Periscope"},
}

PASTIMES = {
    "paper_plane_races": {"label": "paper-airplane races"},
    "sock_puppet_theater": {"label": "sock-puppet theater"},
    "snail_races": {"label": "garden snail races"},
    "picnic_chess": {"label": "picnic-blanket chess"},
    "bubble_making": {"label": "bubble making"},
    "hide_and_seek": {"label": "backyard hide-and-seek"},
    "ribbon_dancing": {"label": "ribbon dancing"},
    "cloud_watching": {"label": "cloud watching"},
}

ANIMAL_TYPES = ("rabbit", "mouse", "otter", "fox", "bear", "duck", "cat", "raccoon")
NAMES = ("Mina", "Pip", "Lulu", "Toby", "Nell", "Bram", "Clover", "Momo")
OPENINGS = (
    "On a bright morning",
    "One breezy afternoon",
    "Just after the breakfast bell",
    "As the clouds made funny shapes overhead",
    "On the sort of day made for playing outside",
    "While the market clock gave a sleepy yawn",
)


SCENARIOS: list[dict[str, str]] = [
    {
        "key": "willow_wind",
        "gadget": "polka_bellows",
        "pastime": "paper_plane_races",
        "place": "the schoolyard flight line",
        "target": "Nori",
        "target_type": "turtle",
        "setup": "Nori had brought a paper plane with a crooked blue tail and hoped it would fly as far as the willow.",
        "early": "The bellows' paper ribbon kept pointing toward the willow, even when the air felt still.",
        "snag": "a crosswind swept the planes toward a low pond, and Nori's blue-tailed plane caught in a willow fork",
        "failed": "{hero} chased the biggest plane, but the wind whisked {hero}'s hat into the pond instead.",
        "payoff": "The ribbon snapped toward the pond: the crosswind was still pushing from the willow.",
        "clue": "Bram noticed that the bellows' ribbon pointed straight into the gust, just as it had before the race.",
        "action": "They used the ribbon as a wind arrow, waited for a lull, and lowered Nori's plane with a long willow switch.",
        "kindness": "{hero} invited Nori to launch from the sheltered side and helped him fold a stronger paper nose.",
        "result": "Nori's plane sailed safely across the grass, and everyone cheered when it landed beside the starting line.",
        "lesson": "a strange little warning can help when someone takes time to notice it",
        "comic": "A frog climbed onto {hero}'s floating hat and looked ready to captain it across the pond.",
        "ending": "the rescued plane rested beside the willow while the frog's new hat-boat bobbed in the pond",
    },
    {
        "key": "curtain_twitch",
        "gadget": "sock_seesaw",
        "pastime": "sock_puppet_theater",
        "place": "the community hall's little stage",
        "target": "Pip",
        "target_type": "mole",
        "setup": "Pip had made a shy purple puppet and was practicing its very tiny royal wave.",
        "early": "The seesaw tipped whenever the puppet curtain gave a tiny twitch.",
        "snag": "the curtain rope slipped, and one corner of the stage sagged just as Pip's puppet was about to appear",
        "failed": "{hero} gave the rope a mighty tug, which made the curtain droop lower and a sock puppet wave at the floor.",
        "payoff": "The seesaw tipped again when the curtain sagged, pointing to the loose rope loop.",
        "clue": "Bram remembered the seesaw's little tilt and spotted the rope loop slipping behind the curtain.",
        "action": "Bram set the seesaw's basket beneath the drooping curtain while {hero} retied the loose loop.",
        "kindness": "{hero} offered Pip the first puppet and asked him to open the show with his royal wave.",
        "result": "The curtain rose smoothly, and Pip's puppet received the loudest applause from the front row.",
        "lesson": "a kind invitation can help someone share a talent they were nervous to show",
        "comic": "A brave sock king finished the show by bowing so low that his button crown rolled into the audience.",
        "ending": "Pip's purple puppet took a bow beneath the straight curtain while its button crown rolled in a happy circle",
    },
    {
        "key": "slow_tick",
        "gadget": "wiggle_timer",
        "pastime": "snail_races",
        "place": "the community garden's pebble track",
        "target": "Dot",
        "target_type": "snail",
        "setup": "Dot had decorated her shell with one bright yellow star and was eager to join the starting line.",
        "early": "The timer's tick slowed whenever it sat beside the damp garden stones.",
        "snag": "a leaky watering can spread a slick puddle across the track, and Dot's little shell team stopped at its edge",
        "failed": "{hero} tried to wipe the puddle away with a leaf, but only made a soggy leaf hat.",
        "payoff": "The timer slowed to a sleepy tick beside the puddle, just as it had near the damp stones.",
        "clue": "Bram followed the timer's slower ticks and found a drip falling from the watering can.",
        "action": "They stopped the leak and laid broad, dry leaves around the puddle to make a safe path.",
        "kindness": "{hero} moved the finish line so Dot could join the race without anyone hurrying her.",
        "result": "Dot crossed the leaf path at her own pace, and the other racers waited to cheer her over the line.",
        "lesson": "making room for someone else can make a game better for everyone",
        "comic": "The soggy leaf hat slid over {hero}'s eyes, so {hero} crossed the finish line by following the cheers.",
        "ending": "Dot's yellow-star shell rested by the finish line while a soggy leaf hat sat on the winner's ribbon",
    },
    {
        "key": "breezy_chess",
        "gadget": "crumb_umbrella",
        "pastime": "picnic_chess",
        "place": "the park's picnic hill",
        "target": "Caper",
        "target_type": "crow",
        "setup": "Caper had been guarding the picnic crumbs and was curious about the tiny chess pieces.",
        "early": "The umbrella leaned into every breeze, then scooped up crumbs like a very greedy duck.",
        "snag": "a gust skimmed across the hill and sent the chess pieces rattling toward Caper's crumb pile",
        "failed": "{hero} tried to catch every piece at once and accidentally trapped a cracker beneath one shoe.",
        "payoff": "The umbrella leaned sharply again just before a second gust rattled the board.",
        "clue": "Bram saw the umbrella's tilt point into the breeze before the chess pieces began to skitter.",
        "action": "They turned the board sideways to the wind and tucked the pieces beneath the umbrella's steady rim.",
        "kindness": "{hero} invited Caper to choose the next chess move instead of blaming him for guarding the crumbs.",
        "result": "The board stayed put, and Caper made a clever move with a crumb balanced on his beak.",
        "lesson": "including someone is often a better plan than blaming them",
        "comic": "Caper's crumb fell onto the chessboard and looked, for one surprising moment, like a very round king.",
        "ending": "the chess pieces stood steady beneath the umbrella as Caper studied his crumb-shaped king",
    },
    {
        "key": "wand_wobble",
        "gadget": "button_meter",
        "pastime": "bubble_making",
        "place": "the sunny corner of the meadow",
        "target": "Lulu",
        "target_type": "lamb",
        "setup": "Lulu had brought a bubble wand almost as wide as her smile.",
        "early": "The meter's red button clicked whenever the bubble wand wobbled.",
        "snag": "a cross-breeze kept twisting the wand, so Lulu's biggest bubbles popped before they reached the daisies",
        "failed": "{hero} blew harder, but the bubbles burst so quickly that one landed as a tiny soap mustache.",
        "payoff": "The red button clicked again when the wand began twisting in the same cross-breeze.",
        "clue": "Bram noticed the meter clicked only when the wand wobbled, not when the air was calm.",
        "action": "They waited for the clicks to stop, then held the wand behind a hedge where the air was still.",
        "kindness": "{hero} gave Lulu the first steady turn and showed her how to hold the loop level.",
        "result": "Lulu sent a shining bubble floating over the daisies, and the friends made room for her next turn.",
        "lesson": "patient help can give someone the confidence to try again",
        "comic": "The soap mustache on {hero}'s face made the next bubble look as if it were laughing.",
        "ending": "Lulu's bubble floated above the daisies while {hero}'s soap mustache shone in the sun",
    },
    {
        "key": "barrel_echo",
        "gadget": "echo_map",
        "pastime": "hide_and_seek",
        "place": "the old orchard's shady yard",
        "target": "Momo",
        "target_type": "mouse",
        "setup": "Momo had asked for one extra count before choosing a hiding place.",
        "early": "The map made a hollow bonk whenever the friends passed the old rain barrel.",
        "snag": "the counting ended, but Momo was nowhere in the usual hiding spots and the friends began to worry",
        "failed": "{hero} shouted Momo's name so loudly that a sleepy pigeon fell off the fence in surprise.",
        "payoff": "A hollow bonk sounded again beside the rain barrel, just as it had on their first walk past.",
        "clue": "Bram listened to the map's echo and realized it was pointing toward the barrel, not the empty shed.",
        "action": "They followed the echo and called gently to Momo instead of yanking the barrel's lid.",
        "kindness": "{hero} let Momo decide whether to pop out or stay hidden for one more count.",
        "result": "Momo popped out with a grin, and the friends agreed that one more count was a perfectly fair rule.",
        "lesson": "respecting a friend's choice can be part of playing together",
        "comic": "The startled pigeon settled back onto the fence wearing a leaf like a very small hat.",
        "ending": "Momo peeked beside the rain barrel while the pigeon proudly kept its leaf hat",
    },
    {
        "key": "ribbon_knot",
        "gadget": "tangle_spool",
        "pastime": "ribbon_dancing",
        "place": "the village green's smooth path",
        "target": "Fennie",
        "target_type": "fox",
        "setup": "Fennie had brought a bright green ribbon and hoped to learn a new dance step.",
        "early": "The spool gave a tiny click whenever its ribbon brushed a knot.",
        "snag": "Fennie's ribbon caught on a rosebush just as the music began, and the dancers froze mid-twirl",
        "failed": "{hero} pulled on the ribbon, which only made a knot tight enough to look like a tiny bow tie.",
        "payoff": "A familiar click came from the ribbon snagged against the rosebush.",
        "clue": "Bram listened for the spool's click and found the exact place where the ribbon had caught.",
        "action": "They used the spool to wind the ribbon back gently instead of pulling it through the thorns.",
        "kindness": "Bram offered Fennie a shorter ribbon and the first dance once the path was clear.",
        "result": "Fennie tried the new step, and the friends followed in a wobbly but cheerful line.",
        "lesson": "gentle help can turn an awkward moment into a new beginning",
        "comic": "The tight little knot bobbed on the spool like a very proud bow tie.",
        "ending": "Fennie led the dancing line with a short green ribbon while the spool wore its ridiculous bow tie",
    },
    {
        "key": "western_clouds",
        "gadget": "puff_periscope",
        "pastime": "cloud_watching",
        "place": "the sunny lookout above the creek",
        "target": "Tansy",
        "target_type": "tortoise",
        "setup": "Tansy had brought a cloud chart and a pencil sharpened to a very careful point.",
        "early": "The periscope lens fogged whenever it pointed toward the western hill.",
        "snag": "gray clouds rolled over the hill and a sprinkle began to speckle Tansy's cloud chart",
        "failed": "{hero} tried to wipe the lens with the chart, leaving one cloud with a pencil-colored smudge.",
        "payoff": "The lens fogged again as the gray clouds gathered over the western hill.",
        "clue": "Bram remembered the foggy lens and used the periscope to check the cloudbank before the rain thickened.",
        "action": "They carried the chart beneath a wide picnic awning and watched the clouds from the dry side.",
        "kindness": "{hero} shared the sheltered viewing spot with Tansy and let her name the first cloud.",
        "result": "Tansy named the biggest cloud a woolly dragon, and everyone stayed dry while they sketched it.",
        "lesson": "sharing a safe, comfortable place helps everyone enjoy the same adventure",
        "comic": "The pencil smudge made one cloud look as if the woolly dragon had a very serious eyebrow.",
        "ending": "Tansy's woolly dragon cloud filled the dry chart, complete with one very serious pencil eyebrow",
    },
]


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(
        default_factory=lambda: {
            "steadiness": 0.0,
            "readiness": 0.0,
            "participation": 0.0,
            "usefulness": 0.0,
        }
    )
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "worry": 0.0,
            "curiosity": 0.0,
            "trust": 0.0,
            "kindness": 0.0,
            "joy": 0.0,
            "relief": 0.0,
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
    scenario_index: int = 0
    opening_index: int = 0
    detail_variant: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def log(self, text: str) -> None:
        self.trace_log.append(text)


def _registry_key(value: str, registry: dict[str, dict[str, str]], what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StoryError(f"{what} must be a non-empty name.")
    candidate = value.strip().casefold()
    for key, entry in registry.items():
        if candidate in {key.casefold(), entry["label"].casefold()}:
            return key
    choices = ", ".join(entry["label"] for entry in registry.values())
    raise StoryError(f"Unknown {what} {value!r}. Choose one of: {choices}.")


def _animal_type(value: str, what: str) -> str:
    if not isinstance(value, str) or value.strip().casefold() not in ANIMAL_TYPES:
        raise StoryError(f"Unknown {what} {value!r}. Choose an animal type such as rabbit, mouse, or otter.")
    return value.strip().casefold()


def scenario_gate(scenario: dict[str, str]) -> bool:
    """Python reasonableness gate mirrored by the inline ASP rules."""
    return bool(
        scenario.get("key")
        and scenario.get("gadget") in GADGETS
        and scenario.get("pastime") in PASTIMES
        and scenario.get("early", "").strip()
        and scenario.get("payoff", "").strip()
        and scenario.get("kindness", "").strip()
        and scenario.get("comic", "").strip()
    )


def reasonableness(params: StoryParams) -> dict[str, str]:
    if not isinstance(params, StoryParams):
        raise StoryError("Story parameters must be a StoryParams instance.")
    if not (0 <= params.scenario_index < len(SCENARIOS)):
        raise StoryError(f"Scenario index {params.scenario_index!r} is outside the available story set.")
    gadget_key = _registry_key(params.gadget, GADGETS, "gadget")
    pastime_key = _registry_key(params.pastime, PASTIMES, "pastime")
    scenario = SCENARIOS[params.scenario_index]
    if scenario["gadget"] != gadget_key or scenario["pastime"] != pastime_key:
        raise StoryError(
            f"{GADGETS[gadget_key]['label']} and {PASTIMES[pastime_key]} do not belong to the selected story scenario."
        )
    _animal_type(params.hero_type, "hero animal type")
    _animal_type(params.friend_type, "friend animal type")
    if not params.hero_name.strip() or not params.friend_name.strip():
        raise StoryError("Both animal friends need non-empty names.")
    if params.hero_name.strip().casefold() == params.friend_name.strip().casefold():
        raise StoryError("The two animal friends need different names so their dialogue is clear.")
    if not scenario_gate(scenario):
        raise StoryError("This scenario is missing a clue, a kindness, or a comic payoff.")
    required = ("place", "setup", "snag", "failed", "clue", "action", "result", "lesson", "ending")
    missing = [field_name for field_name in required if not scenario.get(field_name, "").strip()]
    if missing:
        raise StoryError(f"This scenario is incomplete: {', '.join(missing)}.")
    return scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Make a comic little story about a gadget, a pastime, and a kind turn."
    )
    parser.add_argument("--gadget", help="Choose a registered gadget by name.")
    parser.add_argument("--pastime", help="Choose a registered pastime by name.")
    parser.add_argument("--name", help="Name the first animal friend.")
    parser.add_argument("--type", dest="hero_type", help="Choose the first friend's animal type.")
    parser.add_argument("--sidekick", help="Name the second animal friend.")
    parser.add_argument("--sidekick-type", help="Choose the second friend's animal type.")
    parser.add_argument("-n", type=int, default=1, help="Number of distinct stories to generate.")
    parser.add_argument("--all", action="store_true", help="Generate one story for every curated scenario.")
    parser.add_argument("--seed", type=int, default=None, help="Set the random seed.")
    parser.add_argument("--trace", action="store_true", help="Show the simulated meters and memes.")
    parser.add_argument("--qa", action="store_true", help="Show prompts and question-and-answer sets.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of story text.")
    parser.add_argument("--asp", action="store_true", help="Solve and display the ASP twin.")
    parser.add_argument("--verify", action="store_true", help="Check Python/ASP parity and generated stories.")
    parser.add_argument("--show-asp", action="store_true", help="Print the ASP program.")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    requested_gadget = _registry_key(args.gadget, GADGETS, "gadget") if args.gadget else None
    requested_pastime = _registry_key(args.pastime, PASTIMES, "pastime") if args.pastime else None
    eligible = [
        (index, scenario)
        for index, scenario in enumerate(SCENARIOS)
        if (requested_gadget is None or scenario["gadget"] == requested_gadget)
        and (requested_pastime is None or scenario["pastime"] == requested_pastime)
    ]
    if not eligible:
        raise StoryError("That gadget and pastime do not form one of the available story pairs.")
    index, scenario = rng.choice(eligible)
    hero_type = _animal_type(args.hero_type, "hero animal type") if args.hero_type else rng.choice(ANIMAL_TYPES)
    friend_type = (
        _animal_type(args.sidekick_type, "friend animal type")
        if args.sidekick_type
        else rng.choice(ANIMAL_TYPES)
    )
    return StoryParams(
        gadget=GADGETS[scenario["gadget"]]["label"],
        pastime=PASTIMES[scenario["pastime"]]["label"],
        hero_name=args.name.strip() if args.name else rng.choice(NAMES),
        hero_type=hero_type,
        friend_name=args.sidekick.strip() if args.sidekick else rng.choice(NAMES),
        friend_type=friend_type,
        scenario_index=index,
        opening_index=rng.randrange(len(OPENINGS)),
        detail_variant=rng.randrange(10_000),
    )


def _format(text: str, **values: str) -> str:
    return text.format(**values)


def tell(params: StoryParams) -> World:
    scenario = reasonableness(params)
    gadget_label = GADGETS[scenario["gadget"]]["label"]
    pastime_label = PASTIMES[scenario["pastime"]]["label"]
    hero_name = params.hero_name.strip()
    friend_name = params.friend_name.strip()
    target_name = scenario["target"]

    world = World(Setting(place=scenario["place"]))
    hero = world.add(
        Entity(id="hero", kind="animal", type=params.hero_type.casefold(), label=hero_name)
    )
    friend = world.add(
        Entity(id="friend", kind="animal", type=params.friend_type.casefold(), label=friend_name)
    )
    target = world.add(
        Entity(
            id="neighbor",
            kind="animal",
            type=scenario["target_type"],
            label=target_name,
        )
    )
    gadget = world.add(
        Entity(id="gadget", kind="thing", type="gadget", label=gadget_label, owner=friend.id)
    )
    pastime = world.add(
        Entity(id="pastime", kind="activity", type="pastime", label=pastime_label)
    )
    values = {
        "hero": hero.label,
        "friend": friend.label,
        "target": target.label,
        "gadget": gadget.label,
        "pastime": pastime.label,
    }
    world.facts.update(
        hero=hero,
        friend=friend,
        target=target,
        gadget=gadget,
        pastime=pastime,
        scenario=scenario,
    )

    hero.memes["joy"] = 0.5
    friend.memes["pride"] = 0.4
    friend.memes["trust"] = 0.3
    gadget.meters["readiness"] = 0.5
    gadget.meters["steadiness"] = 0.3

    opening = OPENINGS[params.opening_index % len(OPENINGS)]
    world.say(
        f"{opening}, {hero.label} the {hero.type} and {friend.label} the {friend.type} "
        f"arrived at {world.setting.place} for {pastime.label}."
    )
    world.say(
        f"{friend.label} had built the {gadget.label}, a gadget meant to make "
        f"{pastime.label} easier. {scenario['setup']}"
    )
    world.say(_format(scenario["early"], **values))
    world.say(
        f"{friend.label} called the gadget's odd little habit a feature, although "
        f"{hero.label} privately wondered whether it needed a nap."
    )
    gadget.meters["readiness"] = 0.8
    gadget.meters["steadiness"] = 0.45
    gadget.memes["curiosity"] = 0.5
    hero.memes["curiosity"] = 0.6
    world.log("The gadget gave its first unusual signal before the pastime began.")
    world.para()

    world.say(
        f"Then {scenario['snag']}. { _format(scenario['failed'], **values) }"
    )
    hero.memes["worry"] = 0.8
    friend.memes["worry"] = 0.5
    gadget.meters["steadiness"] = 0.15
    world.log("The first hurried attempt failed and raised the friends' worry.")
    world.para()

    world.say(
        f'"The {gadget.label} is doing that odd thing again," {friend.label} said. '
        f'"Do you think it is a clue?"'
    )
    world.say(
        f'"I do," {hero.label} replied. "Let us help {target.label} before we start again. '
        f"Everyone deserves a turn.\""
    )
    world.say(_format(scenario["payoff"], **values))
    world.say(_format(scenario["clue"], **values))
    gadget.meters["steadiness"] = 0.75
    hero.memes["curiosity"] = 1.0
    friend.memes["trust"] = 0.8
    world.log("The friends recognized the foreshadowed signal and changed their plan.")
    world.para()

    world.say(_format(scenario["action"], **values))
    world.say(_format(scenario["kindness"], **values))
    gadget.meters["steadiness"] = 1.0
    gadget.meters["usefulness"] = 1.0
    pastime.meters["participation"] = 1.0
    hero.memes["kindness"] = 1.0
    hero.memes["worry"] = 0.1
    hero.memes["joy"] = 0.9
    friend.memes["worry"] = 0.1
    friend.memes["joy"] = 0.8
    target.meters["participation"] = 1.0
    target.memes["relief"] = 0.8
    target.memes["joy"] = 1.0
    world.log("The friends used the clue to solve the mishap and include their neighbor.")
    world.para()

    world.say(_format(scenario["result"], **values))
    world.say(
        f"{hero.label} realized that {scenario['lesson']}. "
        f"{_format(scenario['comic'], **values)}"
    )
    world.say(f"By the time they packed up, {scenario['ending']}.")
    world.log("The pastime ended with the neighbor included and the gadget's odd habit understood.")
    return world


def generation_prompts(world: World) -> list[str]:
    scenario = world.facts["scenario"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    target: Entity = world.facts["target"]
    gadget: Entity = world.facts["gadget"]
    pastime: Entity = world.facts["pastime"]
    return [
        f"Write a comic, child-friendly story about {hero.label} and {friend.label} using the {gadget.label} for {pastime.label}.",
        f"Tell a story at {world.setting.place} where an odd clue from the {gadget.label} helps the friends include {target.label}.",
        f"Write a gentle comedy about {pastime.label} with a foreshadowed gadget mishap and a kind solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    scenario: dict[str, str] = world.facts["scenario"]
    hero: Entity = world.facts["hero"]
    friend: Entity = world.facts["friend"]
    target: Entity = world.facts["target"]
    gadget: Entity = world.facts["gadget"]
    pastime: Entity = world.facts["pastime"]
    values = {
        "hero": hero.label,
        "friend": friend.label,
        "target": target.label,
        "gadget": gadget.label,
        "pastime": pastime.label,
    }
    return [
        QAItem(
            question=f"What pastime did {hero.label} and {friend.label} want to enjoy?",
            answer=f"They planned to enjoy {pastime.label} with the {gadget.label}, which {friend.label} had built to help.",
        ),
        QAItem(
            question=f"What odd clue did the {gadget.label} give before the trouble?",
            answer=(
                f"{_format(scenario['early'], **values)} Later, the same clue helped the friends "
                f"understand what had gone wrong."
            ),
        ),
        QAItem(
            question=f"Why did the first attempt to fix the problem fail?",
            answer=(
                f"{_format(scenario['failed'], **values)} Rushing did not solve the real problem, "
                f"so the friends stopped and looked for a clue."
            ),
        ),
        QAItem(
            question=f"How did the friends use the clue to solve the mishap?",
            answer=(
                f"{_format(scenario['clue'], **values)} {_format(scenario['action'], **values)}"
            ),
        ),
        QAItem(
            question=f"How did they show kindness to {target.label}?",
            answer=(
                f"{_format(scenario['kindness'], **values)} That helped {target.label} take part "
                f"and made the pastime more enjoyable for everyone."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gadget?",
            answer="A gadget is a small tool or device made to do a particular job, sometimes in a clever or amusing way.",
        ),
        QAItem(
            question="What is a pastime?",
            answer="A pastime is an activity someone enjoys doing in their free time, such as playing a game or making something.",
        ),
        QAItem(
            question="What does it mean to foreshadow something in a story?",
            answer="Foreshadowing is an early hint about something that will matter later. A small clue can make a later surprise feel earned.",
        ),
        QAItem(
            question="How can kindness help a group enjoy a game?",
            answer="Kindness can make room for someone who is worried or left out, so everyone gets a fair chance to join in.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        meters = {key: round(value, 2) for key, value in entity.meters.items() if value}
        memes = {key: round(value, 2) for key, value in entity.memes.items() if value}
        lines.append(
            f"{entity.id}: kind={entity.kind}, type={entity.type}, "
            f"meters={meters}, memes={memes}"
        )
    lines.extend(f"event: {entry}" for entry in world.trace_log)
    return "\n".join(lines)


ASP_RULES = r"""
paired(S) :- scenario(S), uses(S,G,P), gadget(G), pastime(P).
story_ready(S) :- paired(S), early_signal(S), paid_off(S), kind_act(S), funny(S).
happy_end(S) :- story_ready(S).
"""


def asp_facts() -> str:
    """Emit registry and scenario facts for the inline ASP twin."""
    from storyworlds import asp

    facts: list[str] = []
    for key in GADGETS:
        facts.append(asp.fact("gadget", key))
    for key in PASTIMES:
        facts.append(asp.fact("pastime", key))
    for scenario in SCENARIOS:
        key = scenario["key"]
        facts.extend(
            (
                asp.fact("scenario", key),
                asp.fact("uses", key, scenario["gadget"], scenario["pastime"]),
            )
        )
        if scenario.get("early", "").strip():
            facts.append(asp.fact("early_signal", key))
        if scenario.get("payoff", "").strip():
            facts.append(asp.fact("paid_off", key))
        if scenario.get("kindness", "").strip():
            facts.append(asp.fact("kind_act", key))
        if scenario.get("comic", "").strip():
            facts.append(asp.fact("funny", key))
    return "\n".join(facts)


def asp_program(show: str = "#show story_ready/1. #show happy_end/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    from storyworlds import asp

    symbols = asp.one_model(asp_program())
    python_ready = {
        (scenario["key"],)
        for scenario in SCENARIOS
        if scenario_gate(scenario)
    }
    asp_ready = set(asp.atoms(symbols, "story_ready"))
    asp_happy = set(asp.atoms(symbols, "happy_end"))
    if asp_ready != python_ready or asp_happy != python_ready:
        print(
            "MISMATCH: ASP and Python disagree:",
            f"ready={sorted(asp_ready)}, happy={sorted(asp_happy)}, python={sorted(python_ready)}",
        )
        return 1

    for index, scenario in enumerate(SCENARIOS):
        params = StoryParams(
            gadget=GADGETS[scenario["gadget"]]["label"],
            pastime=PASTIMES[scenario["pastime"]]["label"],
            hero_name="Mina",
            hero_type="rabbit",
            friend_name="Bram",
            friend_type="otter",
            scenario_index=index,
            opening_index=index % len(OPENINGS),
            detail_variant=index,
        )
        sample = generate(params)
        if (
            not sample.story.strip()
            or sample.story.count('"') < 4
            or scenario["ending"] not in sample.story
            or any("{" in item.answer or "}" in item.answer for item in sample.story_qa)
        ):
            print(f"FAIL: generated story {scenario['key']} did not pass the story checks.")
            return 1

    bad = StoryParams(
        gadget=GADGETS["polka_bellows"]["label"],
        pastime=PASTIMES["snail_races"]["label"],
        hero_name="Mina",
        hero_type="rabbit",
        friend_name="Bram",
        friend_type="otter",
        scenario_index=0,
    )
    try:
        reasonableness(bad)
    except StoryError:
        pass
    else:
        print("FAIL: an incompatible gadget and pastime were not rejected.")
        return 1

    print("OK: ASP/Python parity passed, and all generated scenarios passed.")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        gadget=GADGETS[scenario["gadget"]]["label"],
        pastime=PASTIMES[scenario["pastime"]]["label"],
        hero_name=("Mina", "Pip", "Lulu", "Toby", "Nell", "Clover", "Momo", "Nell")[index],
        hero_type=("rabbit", "mouse", "otter", "fox", "bear", "duck", "cat", "raccoon")[index],
        friend_name=("Bram", "Nell", "Momo", "Pip", "Clover", "Toby", "Lulu", "Pip")[index],
        friend_type=("otter", "bear", "duck", "cat", "mouse", "rabbit", "fox", "bear")[index],
        scenario_index=index,
        opening_index=index % len(OPENINGS),
        detail_variant=index,
    )
    for index, scenario in enumerate(SCENARIOS)
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        from storyworlds import asp

        symbols = asp.one_model(asp_program())
        print("ASP model:", " ".join(str(atom) for atom in symbols))
        return
    if args.n < 0:
        raise SystemExit("-n must be zero or greater.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        limit = max(args.n * 50, 50)
        while len(samples) < args.n and attempt < limit:
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            attempt += 1
            sample = generate(params)
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


if __name__ == "__main__":
    main()
