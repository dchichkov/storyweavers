#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py
============================================================

A small myth-flavored story world about a child hero who goes on a quest for a
blessing, gets trapped by a magical obstacle, and uses the right helper to
escape safely and bring a gift home.

Run it
------
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py --realm thorn_maze --obstacle briar_gate --helper moon_shears
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py --realm echo_cavern --obstacle black_water --helper moon_shears
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py --all
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/escape_quest_happy_ending_myth.py --verify
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
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "goddess"}
        male = {"boy", "man", "father", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Realm:
    id: str
    place: str
    entry: str
    image: str
    keeper: str
    allows: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    arrival: str
    threat: str
    solved_by: str
    calm_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    use_text: str
    solves: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    found_text: str
    blessing: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
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


def _r_trapped(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if not hero or not obstacle:
        return out
    if obstacle.meters["blocking"] < THRESHOLD:
        return out
    sig = ("trapped", obstacle.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["trapped"] += 1
    hero.memes["fear"] += 1
    out.append("__trapped__")
    return out


def _r_blessing(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    village = world.entities.get("village")
    treasure = world.entities.get("treasure")
    if not hero or not village or not treasure:
        return out
    if hero.meters["escaped"] < THRESHOLD or treasure.meters["carried"] < THRESHOLD:
        return out
    sig = ("blessing", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    village.meters["blessed"] += 1
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    out.append("__blessing__")
    return out


CAUSAL_RULES = [
    Rule(name="trapped", tag="physical", apply=_r_trapped),
    Rule(name="blessing", tag="social", apply=_r_blessing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


THEMES = {
    "brave": "brave",
    "gentle": "gentle",
    "patient": "patient",
    "curious": "curious",
    "steadfast": "steadfast",
}

REALMS = {
    "thorn_maze": Realm(
        id="thorn_maze",
        place="the Thorn Maze",
        entry="Beyond the olive hill stood the Thorn Maze, old as the oldest song.",
        image="Its green walls curled like sleeping dragons around a hidden heart.",
        keeper="the orchard goddess",
        allows={"briar_gate"},
        tags={"maze", "thorns"},
    ),
    "echo_cavern": Realm(
        id="echo_cavern",
        place="the Echo Cavern",
        entry="Under the mountain mouth waited the Echo Cavern, where even whispers walked twice.",
        image="Blue stone shone in the dark like water holding moonlight.",
        keeper="the cave spirit",
        allows={"black_water"},
        tags={"cave", "river"},
    ),
    "sun_peak": Realm(
        id="sun_peak",
        place="the Sun Peak",
        entry="Far above the sheep paths rose the Sun Peak, bright and windy under the wide sky.",
        image="Its high stair of stone climbed toward clouds that glowed like gold wool.",
        keeper="the dawn keeper",
        allows={"wind_bridge"},
        tags={"mountain", "height"},
    ),
}

OBSTACLES = {
    "briar_gate": Obstacle(
        id="briar_gate",
        label="briar gate",
        arrival="When the prize was in hand, a briar gate twisted shut behind the hero.",
        threat="The thorns knit themselves so tightly that the path home vanished.",
        solved_by="moon_shears",
        calm_line="The cut vines fell apart with a soft sigh, and a clean path opened through the roses.",
        tags={"thorns", "escape"},
    ),
    "black_water": Obstacle(
        id="black_water",
        label="black water",
        arrival="When the hero turned back, black water rushed across the cave floor and swallowed the stepping stones.",
        threat="The stream spun cold circles in the dark, and there was no dry way out.",
        solved_by="silver_reed",
        calm_line="The water listened, slowed, and laid itself flat as a dark glass road.",
        tags={"river", "escape"},
    ),
    "wind_bridge": Obstacle(
        id="wind_bridge",
        label="wind bridge",
        arrival="When the hero reached the high pass, the wind bridge began to sway like a loose ribbon.",
        threat="Each gust tugged harder, and the empty air below felt far too deep.",
        solved_by="sun_kite",
        calm_line="The bright kite caught the wild gusts and pulled the bridge straight and steady.",
        tags={"height", "escape"},
    ),
}

HELPERS = {
    "moon_shears": Helper(
        id="moon_shears",
        label="moon shears",
        phrase="a pair of moon shears",
        use_text="lifted the moon shears and snipped the silver thorns one by one",
        solves={"briar_gate"},
        tags={"tool", "thorns"},
    ),
    "silver_reed": Helper(
        id="silver_reed",
        label="silver reed",
        phrase="a silver reed flute",
        use_text="raised the silver reed and played a slow river song",
        solves={"black_water"},
        tags={"music", "river"},
    ),
    "sun_kite": Helper(
        id="sun_kite",
        label="sun kite",
        phrase="a little sun kite",
        use_text="threw the sun kite into the roaring air and held fast to its golden string",
        solves={"wind_bridge"},
        tags={"wind", "height"},
    ),
}

TREASURES = {
    "golden_apple": Treasure(
        id="golden_apple",
        label="golden apple",
        phrase="the golden apple of morning",
        found_text="On a low branch, warm as sunrise, hung the golden apple of morning.",
        blessing="Its light brought sweet color back to the village orchard.",
        ending_image="Soon even the oldest tree wore young leaves again.",
        tags={"apple", "harvest"},
    ),
    "singing_shell": Treasure(
        id="singing_shell",
        label="singing shell",
        phrase="the singing shell of the first tide",
        found_text="In a stone bowl lay the singing shell of the first tide, humming softly to itself.",
        blessing="Its song filled the dry village well with clear, laughing water.",
        ending_image="Children leaned over the well and saw the sky smiling in it.",
        tags={"shell", "water"},
    ),
    "dawn_lantern": Treasure(
        id="dawn_lantern",
        label="dawn lantern",
        phrase="the dawn lantern",
        found_text="Upon a high altar rested the dawn lantern, no bigger than two hands and brighter than a star.",
        blessing="Its glow chased the long gray chill from every doorway in the village.",
        ending_image="That night, every window shone like a small friendly sun.",
        tags={"light", "dawn"},
    ),
}

GIRL_NAMES = ["Lila", "Mira", "Nora", "Iris", "Talia", "Rhea", "Asha", "Dora"]
BOY_NAMES = ["Tarin", "Niko", "Leo", "Orin", "Milo", "Damon", "Theo", "Aren"]


@dataclass
class StoryParams:
    realm: str
    obstacle: str
    helper: str
    treasure: str
    hero_name: str
    hero_gender: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


def helper_fits(helper: Helper, obstacle: Obstacle) -> bool:
    return obstacle.id in helper.solves


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for obstacle_id in sorted(realm.allows):
            obstacle = OBSTACLES[obstacle_id]
            for helper_id, helper in HELPERS.items():
                if not helper_fits(helper, obstacle):
                    continue
                for treasure_id in TREASURES:
                    combos.append((realm_id, obstacle_id, helper_id, treasure_id))
    return combos


def explain_rejection(realm: Realm, obstacle: Obstacle, helper: Helper) -> str:
    if obstacle.id not in realm.allows:
        return (
            f"(No story: {obstacle.label} does not belong in {realm.place}. "
            f"Pick an obstacle that fits that realm's path out.)"
        )
    return (
        f"(No story: {helper.label} cannot solve the {obstacle.label}. "
        f"A mythic escape needs a helper that truly opens the way home.)"
    )


def introduce_hero(world: World, hero: Entity, elder: Entity, realm: Realm, treasure: Treasure) -> None:
    world.say(
        f"In the days when springs answered songs and hills remembered names, "
        f"there lived a {hero.traits[0]} child named {hero.id}."
    )
    world.say(
        f"One evening {hero.id}'s {elder.label_word} stood by the hearth and said that "
        f"only {treasure.phrase} from {realm.place} could help the village."
    )


def charge_quest(world: World, hero: Entity, elder: Entity, realm: Realm, treasure: Treasure, helper: Helper) -> None:
    hero.memes["duty"] += 1
    hero.memes["hope"] += 1
    hero.meters["prepared"] += 1
    world.say(
        f'"Will you go?" asked the {elder.label_word}. {hero.id} nodded at once, '
        f"for the quest was hard, but the need was true."
    )
    world.say(
        f"The elder placed {helper.phrase} in {hero.pronoun('possessive')} hands and told "
        f"{hero.pronoun('object')} to remember both courage and care."
    )
    world.say(f"{realm.entry} {realm.image}")


def reach_treasure(world: World, hero: Entity, realm: Realm, treasure: Treasure) -> None:
    treasure_ent = world.get("treasure")
    hero.meters["in_realm"] += 1
    treasure_ent.meters["carried"] += 1
    hero.meters["carrying"] += 1
    world.say(
        f"{hero.id} walked on until the heart of {realm.place} opened at last."
    )
    world.say(treasure.found_text)
    world.say(
        f"{hero.pronoun().capitalize()} wrapped it carefully in a cloak fold, already thinking of home."
    )


def obstacle_rises(world: World, hero: Entity, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(obstacle.arrival)
    world.say(obstacle.threat)
    if hero.meters["trapped"] >= THRESHOLD:
        world.say(
            f"For one small moment, {hero.id} could not escape, and fear beat like a bird inside {hero.pronoun('possessive')} chest."
        )


def use_helper(world: World, hero: Entity, helper: Helper, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    hero.memes["resolve"] += 1
    world.say(
        f"But {hero.id} remembered the gift from home, {helper.use_text}."
    )
    obstacle_ent.meters["blocking"] = 0.0
    hero.meters["trapped"] = 0.0
    hero.meters["path_open"] += 1
    hero.memes["fear"] = 0.0
    world.say(obstacle.calm_line)


def escape_realm(world: World, hero: Entity, realm: Realm) -> None:
    hero.meters["escaped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Only then could {hero.id} escape {realm.place} and run back under the evening sky."
    )


def return_home(world: World, hero: Entity, elder: Entity, treasure: Treasure) -> None:
    village = world.get("village")
    village.meters["saved"] += 1
    world.say(
        f"When {hero.id} came home, the {elder.label_word} lifted both hands in thanks."
    )
    world.say(
        f"{treasure.blessing} {treasure.ending_image}"
    )
    world.say(
        f"{hero.id} slept that night with tired feet and a peaceful heart, and the village spoke of the happy ending for many winters."
    )


def tell(
    realm: Realm,
    obstacle: Obstacle,
    helper: Helper,
    treasure: Treasure,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    elder_type: str = "mother",
    trait: str = "brave",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=[trait],
        tags={"hero"},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        tags={"elder"},
    ))
    world.add(Entity(
        id="village",
        kind="thing",
        type="place",
        label="the village",
        phrase="the village by the hill",
        tags={"home"},
    ))
    world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle.label,
        phrase=obstacle.label,
        tags=set(obstacle.tags),
    ))
    world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        tags=set(treasure.tags),
    ))
    world.add(Entity(
        id="helper",
        kind="thing",
        type="helper",
        label=helper.label,
        phrase=helper.phrase,
        tags=set(helper.tags),
    ))

    introduce_hero(world, hero, elder, realm, treasure)
    charge_quest(world, hero, elder, realm, treasure, helper)

    world.para()
    reach_treasure(world, hero, realm, treasure)
    obstacle_rises(world, hero, obstacle)

    world.para()
    use_helper(world, hero, helper, obstacle)
    escape_realm(world, hero, realm)
    return_home(world, hero, elder, treasure)

    world.facts.update(
        hero=hero,
        elder=elder,
        realm=realm,
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        treasure_cfg=treasure,
        escaped=hero.meters["escaped"] >= THRESHOLD,
        trapped_once=("trapped", "obstacle") in world.fired or hero.memes["resolve"] >= THRESHOLD,
        blessing_given=world.get("village").meters["blessed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "maze": [
        (
            "What is a maze?",
            "A maze is a place with many twisting paths. You have to find the right way through it to get out.",
        )
    ],
    "cave": [
        (
            "Why can caves feel scary?",
            "Caves can feel scary because they are dark and full of echoes. When you cannot see well, it is easier to feel lost.",
        )
    ],
    "river": [
        (
            "Why is rushing water hard to cross?",
            "Rushing water pushes against your feet and can knock you off balance. That is why people should be careful near it.",
        )
    ],
    "height": [
        (
            "Why do high places need care?",
            "High places need care because strong wind and narrow paths can make walking harder. You should move slowly and keep your balance.",
        )
    ],
    "music": [
        (
            "How can music help in stories?",
            "In stories, music can calm wild things and change the mood of a place. A soft song can make danger feel gentle again.",
        )
    ],
    "thorns": [
        (
            "What are thorns?",
            "Thorns are sharp points that grow on some plants. They help protect the plant, but they can scratch skin and cloth.",
        )
    ],
    "tool": [
        (
            "What is a tool?",
            "A tool is something you use to help do a job. Good tools make a hard task easier and safer.",
        )
    ],
    "wind": [
        (
            "What does wind do on a mountain?",
            "Wind can push, pull, and shake things on a mountain. A strong gust can make a path or bridge feel unsteady.",
        )
    ],
    "harvest": [
        (
            "Why is fruit important in stories about villages?",
            "Fruit can stand for food, health, and plenty. When trees bear fruit, a village can feel safe and hopeful.",
        )
    ],
    "water": [
        (
            "Why is water precious to a village?",
            "Water helps people drink, wash, and grow plants. A good water source can help the whole village live well.",
        )
    ],
    "light": [
        (
            "Why does light matter in a dark time?",
            "Light helps people see and feel safe. In stories, it also often stands for hope.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "maze",
    "cave",
    "river",
    "height",
    "music",
    "thorns",
    "tool",
    "wind",
    "harvest",
    "water",
    "light",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    realm = f["realm"]
    treasure = f["treasure_cfg"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    return [
        'Write a short myth for a 3-to-5-year-old that includes the word "escape" and ends happily.',
        f"Tell a quest story about a child named {hero.label} who travels to {realm.place} for {treasure.phrase}, gets stopped by a {obstacle.label}, and escapes with {helper.phrase}.",
        f"Write a gentle myth where courage, a true helper, and a gift carried home bring a village a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    realm = f["realm"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    treasure = f["treasure_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a {hero.traits[0]} child, and {hero.pronoun('possessive')} {elder.label_word}. The story follows {hero.label}'s quest to help the village.",
        ),
        (
            f"Why did {hero.label} go to {realm.place}?",
            f"{hero.label} went there to bring back {treasure.phrase} for the village. The quest mattered because everyone at home needed its blessing.",
        ),
        (
            f"What happened after {hero.label} found the {treasure.label}?",
            f"{obstacle.arrival} {obstacle.threat}",
        ),
        (
            f"How did {hero.label} escape?",
            f"{hero.label} used {helper.phrase} to face the {obstacle.label}. {obstacle.calm_line} That opened the way home.",
        ),
        (
            "How did the story end?",
            f"It ended happily because {hero.label} escaped safely and carried the treasure home. {treasure.blessing} {treasure.ending_image}",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["realm"].tags) | set(f["obstacle_cfg"].tags) | set(f["helper_cfg"].tags) | set(f["treasure_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="thorn_maze",
        obstacle="briar_gate",
        helper="moon_shears",
        treasure="golden_apple",
        hero_name="Lila",
        hero_gender="girl",
        elder_type="mother",
        trait="brave",
    ),
    StoryParams(
        realm="echo_cavern",
        obstacle="black_water",
        helper="silver_reed",
        treasure="singing_shell",
        hero_name="Orin",
        hero_gender="boy",
        elder_type="father",
        trait="patient",
    ),
    StoryParams(
        realm="sun_peak",
        obstacle="wind_bridge",
        helper="sun_kite",
        treasure="dawn_lantern",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="mother",
        trait="steadfast",
    ),
]


ASP_RULES = r"""
valid(R, O, H, T) :- realm(R), allows(R, O), obstacle(O), helper(H), solves(H, O), treasure(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for obstacle_id in sorted(realm.allows):
            lines.append(asp.fact("allows", realm_id, obstacle_id))
    for obstacle_id in OBSTACLES:
        lines.append(asp.fact("obstacle", obstacle_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for obstacle_id in sorted(helper.solves):
            lines.append(asp.fact("solves", helper_id, obstacle_id))
    for treasure_id in TREASURES:
        lines.append(asp.fact("treasure", treasure_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "escape" not in sample.story.lower():
            raise StoryError("(Smoke test failed: generated story was empty or missed the seed word.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Myth-flavored quest storyworld: a child hero seeks a blessing, faces a magical obstacle, and escapes home."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.obstacle and args.obstacle not in REALMS[args.realm].allows:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper] if args.helper else next(iter(HELPERS.values()))
        raise StoryError(explain_rejection(REALMS[args.realm], obstacle, helper))
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        realm = REALMS[args.realm] if args.realm else next(iter(REALMS.values()))
        if not helper_fits(helper, obstacle):
            raise StoryError(explain_rejection(realm, obstacle, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.helper is None or combo[2] == args.helper)
        and (args.treasure is None or combo[3] == args.treasure)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, obstacle_id, helper_id, treasure_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(sorted(THEMES))
    return StoryParams(
        realm=realm_id,
        obstacle=obstacle_id,
        helper=helper_id,
        treasure=treasure_id,
        hero_name=hero_name,
        hero_gender=gender,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        realm = REALMS[params.realm]
        obstacle = OBSTACLES[params.obstacle]
        helper = HELPERS[params.helper]
        treasure = TREASURES[params.treasure]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err})") from err

    if obstacle.id not in realm.allows or not helper_fits(helper, obstacle):
        raise StoryError(explain_rejection(realm, obstacle, helper))

    world = tell(
        realm=realm,
        obstacle=obstacle,
        helper=helper,
        treasure=treasure,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        trait=params.trait,
    )

    return StorySample(
        params=params,
        story=world.render().replace(" hero ", f" {params.hero_name} ").replace(" hero.", f" {params.hero_name}."),
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, obstacle, helper, treasure) combos:\n")
        for realm_id, obstacle_id, helper_id, treasure_id in combos:
            print(f"  {realm_id:12} {obstacle_id:12} {helper_id:12} {treasure_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.realm} / {p.obstacle} / {p.helper} / {p.treasure}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
