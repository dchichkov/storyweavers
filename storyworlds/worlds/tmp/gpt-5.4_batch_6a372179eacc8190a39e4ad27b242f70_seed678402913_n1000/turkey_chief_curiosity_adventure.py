#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py
==============================================================

A standalone story world about a curious child, a village chief, and a wild
turkey that seems to know a hidden path. The world model prefers adventures
where curiosity is guided by care: the child notices a clue, the chief helps
choose the right gear for the obstacle ahead, and together they either reach a
small discovery or learn to slow down and try again another day.

Run it
------
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py --setting pine_woods --obstacle brambles
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py --gear lantern --obstacle stream
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py --all
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/turkey_chief_curiosity_adventure.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root even though this file lives one level deeper than most
# worlds: storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "chief_woman", "mother"}
        male = {"boy", "man", "chief_man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def title_word(self) -> str:
        if self.role == "chief":
            return "chief"
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    trail: str
    affords_obstacles: set[str] = field(default_factory=set)
    affords_discoveries: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    need: int
    danger: str
    crossing: str
    pause_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Discovery:
    id: str
    label: str
    phrase: str
    sight: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    notice_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_curiosity_moves(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    trail = world.entities.get("trail")
    if not child or not trail:
        return out
    if child.memes["curiosity"] >= THRESHOLD:
        sig = ("curiosity_moves", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            trail.meters["followed"] += 1
    return out


def _r_prepared_opens_path(world: World) -> list[str]:
    out: list[str] = []
    trail = world.entities.get("trail")
    obstacle = world.entities.get("obstacle")
    bag = world.entities.get("gear")
    if not trail or not obstacle or not bag:
        return out
    if bag.meters["ready"] >= THRESHOLD and bag.attrs.get("fits_obstacle"):
        sig = ("prepared_opens", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            trail.meters["open"] += 1
    return out


def _r_unprepared_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    obstacle = world.entities.get("obstacle")
    bag = world.entities.get("gear")
    if not child or not obstacle or not bag:
        return out
    if obstacle.meters["met"] >= THRESHOLD and bag.meters["ready"] < THRESHOLD:
        sig = ("unprepared_worry", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] += 1
            child.memes["care"] += 1
    return out


def _r_rush_startles_turkey(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    turkey = world.entities.get("turkey")
    trail = world.entities.get("trail")
    obstacle = world.entities.get("obstacle")
    if not child or not turkey or not trail or not obstacle:
        return out
    rushed = child.memes["rush"] >= THRESHOLD
    hard_place = obstacle.attrs.get("need", 0) >= 2
    if rushed and hard_place:
        sig = ("rush_startles", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            turkey.memes["startled"] += 1
            trail.meters["lost"] += 1
            child.memes["worry"] += 1
    return out


def _r_found_discovery(world: World) -> list[str]:
    out: list[str] = []
    trail = world.entities.get("trail")
    discovery = world.entities.get("discovery")
    child = world.entities.get("child")
    chief = world.entities.get("chief")
    if not trail or not discovery or not child or not chief:
        return out
    if trail.meters["open"] >= THRESHOLD and trail.meters["lost"] < THRESHOLD:
        sig = ("found_discovery", discovery.id)
        if sig not in world.fired:
            world.fired.add(sig)
            discovery.meters["found"] += 1
            child.memes["wonder"] += 1
            chief.memes["pride"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="curiosity_moves", tag="meme", apply=_r_curiosity_moves),
    Rule(name="prepared_opens", tag="physical", apply=_r_prepared_opens_path),
    Rule(name="unprepared_worry", tag="meme", apply=_r_unprepared_worry),
    Rule(name="rush_startles", tag="meme", apply=_r_rush_startles_turkey),
    Rule(name="found_discovery", tag="physical", apply=_r_found_discovery),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            world.say(bit)
    return produced


SETTINGS = {
    "pine_woods": Setting(
        id="pine_woods",
        place="the pine woods",
        opening="Morning light slipped through the pine needles, and the village paths smelled of sap and sun-warmed bark.",
        trail="an old deer path between berry bushes and mossy stones",
        affords_obstacles={"brambles", "stream", "dusk"},
        affords_discoveries={"spring", "lookout"},
        tags={"forest"},
    ),
    "river_meadow": Setting(
        id="river_meadow",
        place="the river meadow",
        opening="The meadow beside the river shone green and bright, with reeds whispering whenever the wind passed by.",
        trail="a narrow path along the reeds and smooth river stones",
        affords_obstacles={"stream", "dusk"},
        affords_discoveries={"spring", "nest"},
        tags={"river"},
    ),
    "red_hills": Setting(
        id="red_hills",
        place="the red hills",
        opening="The red hills rose in warm folds above the village, and little lizards flashed between the rocks.",
        trail="a twisting goat path that curled around sunlit stones",
        affords_obstacles={"brambles", "dusk"},
        affords_discoveries={"lookout", "nest"},
        tags={"hills"},
    ),
}

OBSTACLES = {
    "brambles": Obstacle(
        id="brambles",
        label="brambles",
        phrase="a wall of thorny brambles",
        need=1,
        danger="The thorns snagged sleeves and scratched at the path.",
        crossing="held the branches aside and made a safe little doorway through the thorns",
        pause_line="Curiosity had to step softly where the thorns were waiting.",
        tags={"brambles", "thorns"},
    ),
    "stream": Obstacle(
        id="stream",
        label="stream",
        phrase="a cold stream skipping over stones",
        need=2,
        danger="The stones gleamed with water, and the little crossing looked slippery.",
        crossing="tested each stone, then showed where the safe steps lay",
        pause_line="A quick heart was not enough for a slippery stream.",
        tags={"stream", "water"},
    ),
    "dusk": Obstacle(
        id="dusk",
        label="dusk",
        phrase="a dim stretch of trail under evening shade",
        need=2,
        danger="Under the trees, the path turned blue-gray, and roots hid in the dark.",
        crossing="lifted the light high so every root and turn could be seen",
        pause_line="Curiosity still needed light when the trail grew dark.",
        tags={"dark", "trail"},
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="gloves",
        phrase="a pair of soft trail gloves",
        helps={"brambles"},
        use_text="The gloves kept their hands safe from the thorns.",
        tags={"gloves", "safe_hands"},
    ),
    "walking_stick": Gear(
        id="walking_stick",
        label="walking stick",
        phrase="a smooth walking stick",
        helps={"stream"},
        use_text="The walking stick tapped each stone before a foot landed there.",
        tags={"walking_stick", "balance"},
    ),
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        helps={"dusk"},
        use_text="The lantern poured a warm circle of light over the dark path.",
        tags={"lantern", "light"},
    ),
}

DISCOVERIES = {
    "spring": Discovery(
        id="spring",
        label="spring",
        phrase="a hidden spring",
        sight="clear water bubbled up between shining stones and made a silver song",
        gift="They cupped the cold water in their hands and laughed at how bright it tasted.",
        tags={"spring", "water"},
    ),
    "lookout": Discovery(
        id="lookout",
        label="lookout",
        phrase="a high lookout rock",
        sight="the whole valley opened below them, full of tiny roofs, fields, and curling smoke",
        gift="The wind tugged at their hair while the world looked wide enough for ten adventures.",
        tags={"lookout", "hill"},
    ),
    "nest": Discovery(
        id="nest",
        label="nest",
        phrase="a hidden nest",
        sight="a snug nest rested under tall grass, lined with soft feathers and tucked out of harm's way",
        gift="They only looked from a careful distance, then stepped back so the place would stay peaceful.",
        tags={"nest", "birds"},
    ),
}

CLUES = {
    "feather": Clue(
        id="feather",
        label="feather",
        phrase="a striped turkey feather",
        notice_text="A striped turkey feather lay on the path, fresh enough to tremble in the breeze.",
        tags={"feather", "turkey"},
    ),
    "tracks": Clue(
        id="tracks",
        label="tracks",
        phrase="small turkey tracks",
        notice_text="In the soft dirt, small turkey tracks stitched a tidy line toward the wild path.",
        tags={"tracks", "turkey"},
    ),
    "gobble": Clue(
        id="gobble",
        label="gobble",
        phrase="a far gobble",
        notice_text='From beyond the grass came a sudden "gobble-gobble," quick and bright as a drumbeat.',
        tags={"sound", "turkey"},
    ),
}

PACE_SCORES = {
    "careful": 2,
    "bold": 1,
}

GIRL_NAMES = ["Lila", "Mina", "Ava", "Tara", "Nora", "Zuri", "Esme", "Kira"]
BOY_NAMES = ["Niko", "Arlo", "Ben", "Theo", "Oren", "Milo", "Rafi", "Jules"]
CHIEF_NAMES = {
    "woman": ["Chief Sora", "Chief Mira", "Chief Tali", "Chief Niva"],
    "man": ["Chief Toma", "Chief Rafi", "Chief Ivo", "Chief Kellan"],
}
CHILD_TRAITS = ["curious", "bright-eyed", "eager", "quick", "thoughtful"]


def fitting_gears(obstacle_id: str) -> list[str]:
    return sorted(gid for gid, gear in GEAR.items() if obstacle_id in gear.helps)


def select_default_gear(obstacle_id: str) -> Optional[str]:
    fits = fitting_gears(obstacle_id)
    return fits[0] if fits else None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.affords_obstacles):
            if not fitting_gears(obstacle_id):
                continue
            for discovery_id in sorted(setting.affords_discoveries):
                combos.append((sid, obstacle_id, discovery_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    discovery: str
    gear: str
    clue: str
    pace: str
    child_name: str
    child_gender: str
    chief_name: str
    chief_gender: str
    trait: str
    seed: Optional[int] = None


def pace_score(pace: str) -> int:
    return PACE_SCORES.get(pace, 0)


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    return "found" if pace_score(params.pace) >= obstacle.need else "turned_back"


def explain_combo_rejection(setting_id: str, obstacle_id: str, discovery_id: str) -> str:
    setting = SETTINGS[setting_id]
    if obstacle_id not in setting.affords_obstacles:
        return (
            f"(No story: {setting.place} does not naturally include {OBSTACLES[obstacle_id].phrase}. "
            f"Pick an obstacle the setting can honestly hold.)"
        )
    if discovery_id not in setting.affords_discoveries:
        return (
            f"(No story: {DISCOVERIES[discovery_id].phrase} does not fit {setting.place}. "
            f"Choose a discovery that belongs in that landscape.)"
        )
    if not fitting_gears(obstacle_id):
        return (
            f"(No story: there is no sensible gear for {OBSTACLES[obstacle_id].label}, "
            f"so the chief would not lead the adventure there.)"
        )
    return "(No story: that setting, obstacle, and discovery do not belong together.)"


def explain_gear_rejection(gear_id: str, obstacle_id: str) -> str:
    gear = GEAR[gear_id]
    obstacle = OBSTACLES[obstacle_id]
    better = ", ".join(fitting_gears(obstacle_id))
    return (
        f"(No story: {gear.label} does not help with {obstacle.label}. "
        f"Try gear made for this obstacle, such as {better}.)"
    )


def clue_sentence(clue: Clue, child: Entity, turkey: Entity) -> str:
    return (
        f"{clue.notice_text} {child.id} looked up just in time to see the turkey "
        f"slip ahead along the trail."
    )


def introduce(world: World, child: Entity, chief: Entity, turkey: Entity) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{child.id} was a {child.type} with a {next((t for t in child.traits if t), 'curious')} way of noticing little wonders."
    )
    world.say(
        f"Near the edge of the village walked {chief.id}, the chief, who knew the old paths better than anyone."
    )
    world.say(
        f"Not far away, a wild turkey picked through the grass, glossy and watchful."
    )


def notice_clue(world: World, child: Entity, turkey: Entity, clue: Clue) -> None:
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 0.5
    turkey.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(clue_sentence(clue, child, turkey))
    world.say(
        f'"Where is it going?" {child.id} whispered. The question made {child.pronoun("possessive")} curiosity feel even bigger.'
    )


def ask_chief(world: World, child: Entity, chief: Entity, setting: Setting) -> None:
    chief.memes["care"] += 1
    chief.memes["curiosity"] += 1
    world.say(
        f'{child.id} ran to {chief.id}. "Chief, may I follow the turkey?"'
    )
    world.say(
        f'{chief.id} smiled and glanced at {setting.trail}. "We may follow," {chief.pronoun()} said, '
        f'"but adventure walks best with open eyes."'
    )


def pack_gear(world: World, chief: Entity, gear_cfg: Gear, obstacle_cfg: Obstacle) -> None:
    bag = world.get("gear")
    bag.meters["ready"] += 1
    bag.attrs["fits_obstacle"] = obstacle_cfg.id in gear_cfg.helps
    propagate(world, narrate=False)
    world.say(
        f"Before they stepped onto the wild trail, {chief.id} took {gear_cfg.phrase} from the supply shelf."
    )
    world.say(
        f'"We may be curious," {chief.pronoun()} said, "and we may be careful too."'
    )


def follow_turkey(world: World, child: Entity, turkey: Entity, setting: Setting) -> None:
    child.meters["walking"] += 1
    world.say(
        f"Together they followed the turkey along {setting.trail}. "
        f"Now and then the bird flicked its tail and hurried ahead as if checking whether they were still coming."
    )


def meet_obstacle(world: World, child: Entity, chief: Entity, obstacle_cfg: Obstacle, gear_cfg: Gear) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["met"] += 1
    propagate(world, narrate=False)
    world.say(
        f"After a while they reached {obstacle_cfg.phrase}. {obstacle_cfg.danger}"
    )
    world.say(
        f"{child.id} stopped at once. {obstacle_cfg.pause_line}"
    )
    if world.get("gear").attrs.get("fits_obstacle"):
        world.say(
            f"{chief.id} {obstacle_cfg.crossing}. {gear_cfg.use_text}"
        )


def rush_or_steady(world: World, child: Entity, chief: Entity, turkey: Entity, pace: str) -> None:
    if pace == "bold":
        child.memes["rush"] += 1
        world.say(
            f"{child.id}'s feet twitched to hurry after the turkey before it vanished around the next bend."
        )
    else:
        child.memes["steady"] += 1
        child.memes["care"] += 1
        world.say(
            f"{child.id} took a slow breath and stayed close beside {chief.id}, listening for each next step."
        )
    propagate(world, narrate=False)


def find_discovery(world: World, child: Entity, chief: Entity, turkey: Entity, discovery_cfg: Discovery) -> None:
    discovery = world.get("discovery")
    if discovery.meters["found"] < THRESHOLD:
        return
    child.memes["joy"] += 1
    chief.memes["joy"] += 1
    turkey.meters["guide"] += 1
    world.say(
        f"Beyond the obstacle, the turkey hopped onto a stone and gave one proud gobble."
    )
    world.say(
        f"Then the path opened onto {discovery_cfg.phrase}. There, {discovery_cfg.sight}."
    )
    world.say(discovery_cfg.gift)
    world.say(
        f'{chief.id} rested a hand on {child.id}\'s shoulder. "That is what careful curiosity can find," {chief.pronoun()} said.'
    )


def turn_back(world: World, child: Entity, chief: Entity, turkey: Entity, obstacle_cfg: Obstacle, clue: Clue) -> None:
    trail = world.get("trail")
    turkey.memes["startled"] += 0.0
    child.memes["care"] += 1
    chief.memes["care"] += 1
    world.say(
        f"But the turkey fluttered farther ahead, and in the hurry the trail grew confusing."
    )
    world.say(
        f'{chief.id} gently lifted a hand. "We stop when the path stops making sense," {chief.pronoun()} said.'
    )
    world.say(
        f"They did not reach the hidden place that day. Instead, {child.id} tucked {clue.phrase} into a pocket and looked back at {obstacle_cfg.label} with new respect."
    )
    world.say(
        f"At sunset they walked home together, already planning how to return more slowly another morning."
    )
    trail.meters["return"] += 1


def tell(
    setting: Setting,
    obstacle_cfg: Obstacle,
    discovery_cfg: Discovery,
    gear_cfg: Gear,
    clue_cfg: Clue,
    pace: str,
    child_name: str,
    child_gender: str,
    chief_name: str,
    chief_gender: str,
    trait: str,
) -> World:
    world = World(setting=setting)
    child_type = "girl" if child_gender == "girl" else "boy"
    chief_type = "chief_woman" if chief_gender == "woman" else "chief_man"

    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_type,
            role="child",
            traits=[trait, "curious"],
            label=child_name,
        )
    )
    chief = world.add(
        Entity(
            id=chief_name,
            kind="character",
            type=chief_type,
            role="chief",
            label="the chief",
        )
    )
    turkey = world.add(
        Entity(
            id="Turkey",
            kind="character",
            type="animal",
            role="guide",
            label="the turkey",
            tags={"turkey"},
        )
    )
    trail = world.add(
        Entity(
            id="trail",
            type="path",
            label="trail",
            phrase=setting.trail,
        )
    )
    obstacle = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.phrase,
            attrs={"need": obstacle_cfg.need},
            tags=set(obstacle_cfg.tags),
        )
    )
    gear = world.add(
        Entity(
            id="gear",
            type="gear",
            label=gear_cfg.label,
            phrase=gear_cfg.phrase,
            tags=set(gear_cfg.tags),
        )
    )
    discovery = world.add(
        Entity(
            id="discovery",
            type="discovery",
            label=discovery_cfg.label,
            phrase=discovery_cfg.phrase,
            tags=set(discovery_cfg.tags),
        )
    )

    world.facts["setting"] = setting
    world.facts["obstacle_cfg"] = obstacle_cfg
    world.facts["gear_cfg"] = gear_cfg
    world.facts["discovery_cfg"] = discovery_cfg
    world.facts["clue_cfg"] = clue_cfg
    world.facts["pace"] = pace

    introduce(world, child, chief, turkey)
    notice_clue(world, child, turkey, clue_cfg)

    world.para()
    ask_chief(world, child, chief, setting)
    pack_gear(world, chief, gear_cfg, obstacle_cfg)
    follow_turkey(world, child, turkey, setting)

    world.para()
    meet_obstacle(world, child, chief, obstacle_cfg, gear_cfg)
    rush_or_steady(world, child, chief, turkey, pace)
    propagate(world, narrate=False)

    if trail.meters["lost"] >= THRESHOLD:
        turn_back(world, child, chief, turkey, obstacle_cfg, clue_cfg)
        outcome = "turned_back"
    else:
        find_discovery(world, child, chief, turkey, discovery_cfg)
        outcome = "found"

    world.facts.update(
        child=child,
        chief=chief,
        turkey=turkey,
        trail=trail,
        obstacle=obstacle,
        gear=gear,
        discovery=discovery,
        outcome=outcome,
        reached=discovery.meters["found"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "turkey": [
        (
            "What is a turkey?",
            "A turkey is a large bird with strong legs and a fan-shaped tail. Wild turkeys can walk quickly through grass and woods."
        )
    ],
    "chief": [
        (
            "What does a chief do?",
            "A chief is a leader who helps guide and protect the people in a group. A good chief uses wisdom as well as courage."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to learn, look closer, or ask questions. It can lead to good discoveries when it is joined with care."
        )
    ],
    "brambles": [
        (
            "What are brambles?",
            "Brambles are thorny plants that can catch on clothes and scratch your skin. People move carefully around them."
        )
    ],
    "stream": [
        (
            "Why can a stream crossing be tricky?",
            "A stream can make stones wet and slippery. That is why people step slowly and check where their feet will go."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes light so you can see where you are going in dim places. Seeing clearly helps people move safely."
        )
    ],
    "walking_stick": [
        (
            "What is a walking stick for?",
            "A walking stick helps you keep balance and test the ground ahead. It is useful on uneven or slippery paths."
        )
    ],
    "gloves": [
        (
            "Why do gloves help on a thorny path?",
            "Gloves protect your hands from scratches and snags. They let you move branches aside more safely."
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is a place where water comes up from the ground. It can feed a tiny stream or pool."
        )
    ],
    "lookout": [
        (
            "What is a lookout?",
            "A lookout is a high place where you can see far across the land. People use lookouts to watch for paths, weather, or beautiful views."
        )
    ],
    "nest": [
        (
            "Why should people stay back from a wild bird's nest?",
            "Wild birds need quiet and space around their nests. Looking gently from far away helps keep the nest safe."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "turkey",
    "chief",
    "curiosity",
    "brambles",
    "stream",
    "lantern",
    "walking_stick",
    "gloves",
    "spring",
    "lookout",
    "nest",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    chief = world.facts["chief"]
    setting = world.facts["setting"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    discovery_cfg = world.facts["discovery_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    outcome = world.facts["outcome"]
    tail = "They reach the hidden place." if outcome == "found" else "They turn back safely and plan to return."
    return [
        f'Write a short adventure story for a 3-to-5-year-old that includes the words "turkey" and "chief" and centers on curiosity.',
        f"Tell a gentle adventure where {child.id} notices {clue_cfg.phrase} in {setting.place}, follows a turkey with the chief, and faces {obstacle_cfg.phrase}. {tail}",
        f"Write a child-facing story in which curiosity leads into a small wilderness adventure, but the chief teaches that brave exploring still needs care.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    chief = world.facts["chief"]
    setting = world.facts["setting"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    gear_cfg = world.facts["gear_cfg"]
    discovery_cfg = world.facts["discovery_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    pace = world.facts["pace"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a curious child, and {chief.id}, the chief, who follows the trail beside {child.pronoun('object')}. A wild turkey starts the adventure by drawing their eyes down the path.",
        ),
        (
            "What made the adventure begin?",
            f"The adventure began when {child.id} noticed {clue_cfg.phrase} and saw the turkey hurrying ahead. That clue made {child.pronoun('possessive')} curiosity grow into a real question about where the path might lead.",
        ),
        (
            f"Why did {chief.id} bring {gear_cfg.label}?",
            f"{chief.id} brought {gear_cfg.label} because the trail held {obstacle_cfg.phrase}. The gear matched the danger and helped them explore more safely instead of just hurrying blindly.",
        ),
    ]
    if outcome == "found":
        qa.append(
            (
                "What did they find at the end?",
                f"They found {discovery_cfg.phrase}. The careful crossing let them stay with the turkey's trail long enough to reach the hidden place.",
            )
        )
        qa.append(
            (
                f"How did {child.id}'s curiosity help?",
                f"{child.id}'s curiosity made {child.pronoun('object')} notice the clue and ask to follow it. Because that curiosity was guided by the chief and slowed down when needed, it led to a real discovery instead of trouble.",
            )
        )
    else:
        pace_reason = "hurried after the turkey" if pace == "bold" else "lost the clear line of the trail"
        qa.append(
            (
                "Why did they turn back?",
                f"They turned back because the path stopped feeling clear and safe after {child.id} {pace_reason}. The chief chose safety over guessing, so the adventure ended with a plan to return another day.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that curiosity is strongest when it listens and pays attention. The lesson came from seeing that a hidden place is not worth rushing toward if the trail stops making sense.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"turkey", "chief", "curiosity"}
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["gear_cfg"].tags)
    tags |= set(world.facts["discovery_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="pine_woods",
        obstacle="brambles",
        discovery="spring",
        gear="gloves",
        clue="feather",
        pace="careful",
        child_name="Lila",
        child_gender="girl",
        chief_name="Chief Sora",
        chief_gender="woman",
        trait="bright-eyed",
    ),
    StoryParams(
        setting="river_meadow",
        obstacle="stream",
        discovery="nest",
        gear="walking_stick",
        clue="tracks",
        pace="careful",
        child_name="Niko",
        child_gender="boy",
        chief_name="Chief Toma",
        chief_gender="man",
        trait="curious",
    ),
    StoryParams(
        setting="red_hills",
        obstacle="dusk",
        discovery="lookout",
        gear="lantern",
        clue="gobble",
        pace="careful",
        child_name="Mina",
        child_gender="girl",
        chief_name="Chief Mira",
        chief_gender="woman",
        trait="eager",
    ),
    StoryParams(
        setting="river_meadow",
        obstacle="stream",
        discovery="spring",
        gear="walking_stick",
        clue="feather",
        pace="bold",
        child_name="Theo",
        child_gender="boy",
        chief_name="Chief Kellan",
        chief_gender="man",
        trait="quick",
    ),
]


ASP_RULES = r"""
has_fit(O) :- fit(_, O).
valid(S, O, D) :- setting(S), obstacle(O), discovery(D),
                  affords_obstacle(S, O), affords_discovery(S, D), has_fit(O).

pace_score(careful, 2).
pace_score(bold, 1).

outcome(found) :- chosen_obstacle(O), need(O, N), chosen_pace(P), pace_score(P, S), S >= N.
outcome(turned_back) :- chosen_obstacle(O), need(O, N), chosen_pace(P), pace_score(P, S), S < N.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for obstacle_id in sorted(setting.affords_obstacles):
            lines.append(asp.fact("affords_obstacle", sid, obstacle_id))
        for discovery_id in sorted(setting.affords_discoveries):
            lines.append(asp.fact("affords_discovery", sid, discovery_id))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("need", oid, obstacle.need))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for obstacle_id in sorted(gear.helps):
            lines.append(asp.fact("fit", gid, obstacle_id))
    for did in DISCOVERIES:
        lines.append(asp.fact("discovery", did))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_fits() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show fit/2."))
    return sorted(set(asp.atoms(model, "fit")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_pace", params.pace),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_fit = set(asp_fits())
    p_fit = {(gid, oid) for gid, gear in GEAR.items() for oid in gear.helps}
    if c_fit == p_fit:
        print(f"OK: gear fits match ({sorted(c_fit)}).")
    else:
        rc = 1
        print("MISMATCH in gear fits:")
        if c_fit - p_fit:
            print("  only in clingo:", sorted(c_fit - p_fit))
        if p_fit - c_fit:
            print("  only in python:", sorted(p_fit - c_fit))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a curious child, a chief, a turkey, and a careful adventure."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--discovery", choices=DISCOVERIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--pace", choices=sorted(PACE_SCORES))
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--chief-gender", choices=["woman", "man"])
    ap.add_argument("--child-name")
    ap.add_argument("--chief-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def pick_chief_name(rng: random.Random, gender: str) -> str:
    return rng.choice(CHIEF_NAMES[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.obstacle and args.discovery:
        triple = (args.setting, args.obstacle, args.discovery)
        if triple not in valid_combos():
            raise StoryError(explain_combo_rejection(args.setting, args.obstacle, args.discovery))

    if args.gear and args.obstacle and args.obstacle not in GEAR[args.gear].helps:
        raise StoryError(explain_gear_rejection(args.gear, args.obstacle))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.discovery is None or combo[2] == args.discovery)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, discovery_id = rng.choice(sorted(combos))

    if args.gear is not None:
        if obstacle_id not in GEAR[args.gear].helps:
            raise StoryError(explain_gear_rejection(args.gear, obstacle_id))
        gear_id = args.gear
    else:
        gear_id = select_default_gear(obstacle_id)
        if gear_id is None:
            raise StoryError(f"(No story: no sensible gear exists for {obstacle_id}.)")

    clue_id = args.clue or rng.choice(sorted(CLUES))
    pace = args.pace or rng.choice(sorted(PACE_SCORES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    chief_gender = args.chief_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or pick_child_name(rng, child_gender)
    chief_name = args.chief_name or pick_chief_name(rng, chief_gender)
    trait = rng.choice(CHILD_TRAITS)

    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        discovery=discovery_id,
        gear=gear_id,
        clue=clue_id,
        pace=pace,
        child_name=child_name,
        child_gender=child_gender,
        chief_name=chief_name,
        chief_gender=chief_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, registry in (
        ("setting", SETTINGS),
        ("obstacle", OBSTACLES),
        ("discovery", DISCOVERIES),
        ("gear", GEAR),
        ("clue", CLUES),
    ):
        value = getattr(params, field_name)
        if value not in registry:
            raise StoryError(f"(Invalid {field_name}: {value})")
    if params.pace not in PACE_SCORES:
        raise StoryError(f"(Invalid pace: {params.pace})")
    if params.obstacle not in GEAR[params.gear].helps:
        raise StoryError(explain_gear_rejection(params.gear, params.obstacle))
    if (params.setting, params.obstacle, params.discovery) not in valid_combos():
        raise StoryError(explain_combo_rejection(params.setting, params.obstacle, params.discovery))

    world = tell(
        setting=SETTINGS[params.setting],
        obstacle_cfg=OBSTACLES[params.obstacle],
        discovery_cfg=DISCOVERIES[params.discovery],
        gear_cfg=GEAR[params.gear],
        clue_cfg=CLUES[params.clue],
        pace=params.pace,
        child_name=params.child_name,
        child_gender=params.child_gender,
        chief_name=params.chief_name,
        chief_gender=params.chief_gender,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show fit/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        fits = asp_fits()
        print(f"{len(combos)} compatible (setting, obstacle, discovery) combos:\n")
        for setting_id, obstacle_id, discovery_id in combos:
            gear_list = sorted(g for g, o in fits if o == obstacle_id)
            print(f"  {setting_id:12} {obstacle_id:9} {discovery_id:8}  gear: {', '.join(gear_list)}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name} with {p.chief_name}: {p.setting}, {p.obstacle}, "
                f"{p.discovery} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
