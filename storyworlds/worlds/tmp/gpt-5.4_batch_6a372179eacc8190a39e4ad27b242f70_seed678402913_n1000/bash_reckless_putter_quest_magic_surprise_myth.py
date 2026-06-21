#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py
==============================================================================

A standalone storyworld for a small myth-like quest tale built from the seed
words "bash", "reckless", and "putter", with the narrative features Quest,
Magic, and Surprise.

Premise
-------
A child leaves the village on a quest with a little tortoise named Putter.
They carry one magic gift toward a hill shrine, but a living obstacle blocks the
way. The child may be tempted to bash the obstacle in a reckless moment, or may
listen to Putter and use the right magic at once. Either way, the world model
tracks fear, danger, opening, and learning, and the ending image shows what the
quest changed.

Run it
------
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py --quest rain --obstacle ember_river --gift dew_shell
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py --gift star_key --obstacle thorn_gate
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py --all
python storyworlds/worlds/gpt-5.4/bash_reckless_putter_quest_magic_surprise_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly:
# .../storyworlds/worlds/gpt-5.4/file.py -> add .../storyworlds to sys.path.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.id


@dataclass
class Quest:
    id: str
    title: str = ""
    village_need: str = ""
    shrine: str = ""
    road: str = ""
    boon: str = ""
    ending: str = ""
    surprise: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str = ""
    phrase: str = ""
    sign: str = ""
    needed_magic: str = ""
    bash_result: str = ""
    calm_result: str = ""
    spook: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str = ""
    phrase: str = ""
    magic: str = ""
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    gift: str
    temper: str
    guide_trait: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.fired = set(self.fired)
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_anger(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    hero = world.get("hero")
    if obstacle.memes["anger"] >= THRESHOLD and ("anger",) not in world.fired:
        world.fired.add(("anger",))
        world.get("path").meters["danger"] += 1
        hero.memes["fear"] += 1
        out.append("__anger__")
    return out


def _r_open(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    if obstacle.meters["soothed"] >= THRESHOLD and ("open",) not in world.fired:
        world.fired.add(("open",))
        obstacle.meters["open"] += 1
        world.get("path").meters["clear"] += 1
        out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule(name="anger", apply=_r_anger),
    Rule(name="open", apply=_r_open),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


QUESTS = {
    "spring": Quest(
        id="spring",
        title="the Spring Bowl",
        village_need="the village fig tree had stopped making leaves",
        shrine="the mossy bowl of Spring on the hill",
        road="the goat path that curled toward the eastern hill",
        boon="green life",
        ending="By sunset, the fig tree wore a mist of new leaves, and children pointed up as swallows circled above it.",
        surprise="At the shrine, clear water bubbled from dry stone, and the first drop rolled all the way back to the village ditch.",
        tags={"spring", "shrine"},
    ),
    "rain": Quest(
        id="rain",
        title="the Cloud Bell",
        village_need="the bean rows were thirsty and the dust kept lifting in pale sighs",
        shrine="the old Cloud Bell on the windy ridge",
        road="the pale ridge path above the sleeping fields",
        boon="rain",
        ending="That night, the bean rows drank softly, and silver drops tapped on every roof in the village.",
        surprise="When the bell woke, a round cloud no bigger than a sheep came trotting after them and burst laughing into rain over the fields.",
        tags={"rain", "cloud"},
    ),
    "dawn": Quest(
        id="dawn",
        title="the Dawn Lamp",
        village_need="the valley mornings had been dim, as if the sun kept forgetting the first step",
        shrine="the high lamp-house above the dark valley",
        road="the narrow white path that climbed toward the bright stones",
        boon="light",
        ending="In the morning, the valley opened like an eye, and every doorstep caught a stripe of gold.",
        surprise="At the lamp-house, a flock of fireflies rose from the empty bowl and wove themselves into a shining ribbon ahead of them.",
        tags={"dawn", "light"},
    ),
}

OBSTACLES = {
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="thorn gate",
        phrase="a gate of living thorns, braided so tightly that even the wind could not slip through",
        sign="The vines twitched as if they were listening.",
        needed_magic="song",
        bash_result="The child lifted a staff to bash the thorn gate, but the thorns snapped awake and rattled like angry teeth.",
        calm_result="The thorns unbraided themselves, making a doorway just wide enough for two small travelers and one round tortoise.",
        spook=2,
        tags={"thorn", "song"},
    ),
    "ember_river": Obstacle(
        id="ember_river",
        label="ember river",
        phrase="a narrow river of red coals that hissed and drifted like fish in dark water",
        sign="Heat danced over it in wavy ribbons.",
        needed_magic="dew",
        bash_result="The child stamped and tried to bash a path through the ember river with a branch, but sparks skipped up in a bright, stinging shower.",
        calm_result="The embers sighed into black pebbles, and a cool crossing shone from bank to bank.",
        spook=3,
        tags={"ember", "dew"},
    ),
    "moon_door": Obstacle(
        id="moon_door",
        label="moon door",
        phrase="a silver stone door with no hinge, no handle, and a pale crescent sleeping in the middle",
        sign="It held the path like a closed eyelid.",
        needed_magic="star",
        bash_result="The child drew back a little and wanted to bash the moon door, but the stone answered with a deep hum that shook dust from the cliff.",
        calm_result="The crescent in the stone opened like a smile, and the door turned clear as glass before melting into moonlight.",
        spook=1,
        tags={"moon", "star"},
    ),
}

GIFTS = {
    "reed_flute": Gift(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute cut from river grass",
        magic="song",
        use_text="played one soft note after another until the tune sounded like a bird teaching morning to the leaves",
        tags={"flute", "song"},
    ),
    "dew_shell": Gift(
        id="dew_shell",
        label="dew shell",
        phrase="a pearly shell filled with dawn dew",
        magic="dew",
        use_text="tilted the dew shell and let the bright drops fall in a silver line over the heat",
        tags={"dew", "shell"},
    ),
    "star_key": Gift(
        id="star_key",
        label="star key",
        phrase="a little key hammered from star-bright tin",
        magic="star",
        use_text="held up the star key until its thin light fitted the waiting crescent perfectly",
        tags={"star", "key"},
    ),
}

TEMPER_HASTE = {
    "careful": 0,
    "eager": 0,
    "bold": 1,
    "reckless": 2,
}

GUIDE_PATIENCE = {
    "sleepy": 1,
    "patient": 2,
    "wise": 3,
}

GIRL_NAMES = ["Lila", "Mira", "Nora", "Zia", "Tala", "Rosa", "Ivy", "Asha"]
BOY_NAMES = ["Arin", "Niko", "Tomas", "Eli", "Soren", "Milo", "Darin", "Theo"]

KNOWLEDGE = {
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey taken to do something important. In stories, someone travels, meets trouble, and learns what kind of courage they have.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story with wonder in it. Myths often explain why something matters, like rain, dawn, or the turning of the seasons.",
        )
    ],
    "tortoise": [
        (
            "What is a tortoise?",
            "A tortoise is a land animal with a hard shell. It moves slowly, but it can be very steady and patient.",
        )
    ],
    "reckless": [
        (
            "What does reckless mean?",
            "Reckless means doing something without stopping to think about danger first. A reckless choice can make a problem bigger.",
        )
    ],
    "song": [
        (
            "Why might a song be called magic in a story?",
            "In a story, a song can be magic because it changes how the world behaves. It can calm, open, or wake things that do not answer to pushing.",
        )
    ],
    "dew": [
        (
            "What is dew?",
            "Dew is tiny drops of water that gather when the air grows cool. It can sparkle on grass in the morning.",
        )
    ],
    "star": [
        (
            "What is a star key in a fantasy story?",
            "A star key is a pretend magical key made for a special lock. Stories use it to show that some doors open to light, not force.",
        )
    ],
    "surprise": [
        (
            "What is a surprise ending?",
            "A surprise ending is when something unexpected happens at the end of the story. It still fits the story, but it gives the ending an extra wonder.",
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "myth", "tortoise", "reckless", "song", "dew", "star", "surprise"]


CURATED = [
    StoryParams(
        quest="spring",
        obstacle="thorn_gate",
        gift="reed_flute",
        temper="careful",
        guide_trait="wise",
        hero_name="Lila",
        hero_type="girl",
    ),
    StoryParams(
        quest="rain",
        obstacle="ember_river",
        gift="dew_shell",
        temper="reckless",
        guide_trait="patient",
        hero_name="Arin",
        hero_type="boy",
    ),
    StoryParams(
        quest="dawn",
        obstacle="moon_door",
        gift="star_key",
        temper="bold",
        guide_trait="sleepy",
        hero_name="Nora",
        hero_type="girl",
    ),
    StoryParams(
        quest="spring",
        obstacle="ember_river",
        gift="dew_shell",
        temper="eager",
        guide_trait="patient",
        hero_name="Theo",
        hero_type="boy",
    ),
    StoryParams(
        quest="rain",
        obstacle="thorn_gate",
        gift="reed_flute",
        temper="reckless",
        guide_trait="wise",
        hero_name="Mira",
        hero_type="girl",
    ),
]


def valid_combo(quest_id: str, obstacle_id: str, gift_id: str) -> bool:
    if quest_id not in QUESTS or obstacle_id not in OBSTACLES or gift_id not in GIFTS:
        return False
    return GIFTS[gift_id].magic == OBSTACLES[obstacle_id].needed_magic


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for quest_id in QUESTS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for gift_id, gift in GIFTS.items():
                if gift.magic == obstacle.needed_magic:
                    out.append((quest_id, obstacle_id, gift_id))
    return out


def would_bash_first(temper: str, guide_trait: str) -> bool:
    if temper not in TEMPER_HASTE:
        raise StoryError(f"(Unknown temper '{temper}'.)")
    if guide_trait not in GUIDE_PATIENCE:
        raise StoryError(f"(Unknown guide trait '{guide_trait}'.)")
    return TEMPER_HASTE[temper] > GUIDE_PATIENCE[guide_trait] - 1


def outcome_of(params: StoryParams) -> str:
    return "learned" if would_bash_first(params.temper, params.guide_trait) else "listened"


def explain_rejection(obstacle_id: str, gift_id: str) -> str:
    obstacle = OBSTACLES[obstacle_id]
    gift = GIFTS[gift_id]
    return (
        f"(No story: {gift.label} carries {gift.magic} magic, but the {obstacle.label} answers to "
        f"{obstacle.needed_magic} magic. This quest world only tells stories where the magic really fits the obstacle.)"
    )


def introduce(world: World, hero: Entity, guide: Entity, quest: Quest, gift: Gift) -> None:
    world.say(
        f"In the old days, when hills still listened, {quest.village_need}. "
        f"So {hero.name} was given {gift.phrase} and sent on a quest to {quest.shrine}."
    )
    world.say(
        f"Beside {hero.pronoun('object')} came {guide.name}, a little tortoise who liked to putter over stones "
        f"as if he had all the time in the world."
    )


def set_out(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    hero.memes["hope"] += 1
    guide.memes["steadiness"] += 1
    world.say(
        f"They took {quest.road}, and the morning felt large enough to hold a promise."
    )


def meet_obstacle(world: World, obstacle_cfg: Obstacle) -> None:
    obstacle = world.get("obstacle")
    world.say(
        f"Before long they found {obstacle_cfg.phrase}. {obstacle_cfg.sign}"
    )
    obstacle.meters["blocking"] += 1


def putter_warning(world: World, hero: Entity, guide: Entity, obstacle_cfg: Obstacle) -> None:
    world.say(
        f'"Slow shell, slow thought," said {guide.name}. "Do not be reckless. '
        f"The {obstacle_cfg.label} does not want a bash. It wants the right kind of magic."'
    )
    guide.memes["wisdom"] += 1
    hero.memes["tempted"] += 1


def do_bash(world: World, hero: Entity, obstacle_cfg: Obstacle) -> None:
    obstacle = world.get("obstacle")
    hero.memes["recklessness"] += 1
    obstacle.memes["anger"] += 1
    propagate(world, narrate=False)
    world.say(obstacle_cfg.bash_result)
    if world.get("path").meters["danger"] >= THRESHOLD:
        world.say(
            f"{hero.name}'s heart jumped. The path felt smaller now, and the brave idea suddenly seemed very small indeed."
        )


def use_magic(world: World, hero: Entity, guide: Entity, obstacle_cfg: Obstacle, gift_cfg: Gift) -> None:
    obstacle = world.get("obstacle")
    obstacle.meters["soothed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Now," murmured {guide.name}. {hero.name} {gift_cfg.use_text}.'
    )
    if obstacle.meters["open"] >= THRESHOLD:
        world.say(obstacle_cfg.calm_result)
    hero.memes["wonder"] += 1
    hero.memes["learning"] += 1
    world.get("path").meters["progress"] += 1


def reach_shrine(world: World, hero: Entity, quest: Quest, outcome: str) -> None:
    world.say(
        f"They went on to {quest.shrine}, and {hero.name} laid the gift's last light there with both hands."
    )
    if outcome == "learned":
        world.say(
            f"Because {hero.pronoun()} had nearly chosen force first, {hero.pronoun()} bowed low and spoke an honest sorry to the hill."
        )
    else:
        world.say(
            f"{hero.name} felt the quiet answer of the place and knew that patience can move faster than hitting ever could."
        )


def surprise_ending(world: World, hero: Entity, guide: Entity, quest: Quest, outcome: str) -> None:
    hero.memes["joy"] += 1
    world.say(quest.surprise)
    if outcome == "learned":
        world.say(
            f"{guide.name} blinked once, as if he had expected wonder all along, and {hero.name} laughed because the best surprise had come after a wiser second try."
        )
    else:
        world.say(
            f"{guide.name} tucked his head, pleased, and {hero.name} laughed at the lovely surprise waiting at the end of the quest."
        )
    world.say(quest.ending)


def tell(
    quest_cfg: Quest,
    obstacle_cfg: Obstacle,
    gift_cfg: Gift,
    temper: str,
    guide_trait: str,
    hero_name: str,
    hero_type: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=[temper],
            label=hero_name,
        )
    )
    guide = world.add(
        Entity(
            id="Putter",
            kind="character",
            type="tortoise",
            traits=[guide_trait],
            label="the tortoise",
            tags={"tortoise"},
        )
    )
    world.add(Entity(id="path", kind="thing", type="path", label="path"))
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle_cfg.label,
            phrase=obstacle_cfg.phrase,
        )
    )
    world.facts.update(
        hero=hero,
        guide=guide,
        quest=quest_cfg,
        obstacle_cfg=obstacle_cfg,
        gift_cfg=gift_cfg,
        temper=temper,
        guide_trait=guide_trait,
    )

    introduce(world, hero, guide, quest_cfg, gift_cfg)
    set_out(world, hero, guide, quest_cfg)

    world.para()
    meet_obstacle(world, obstacle_cfg)
    putter_warning(world, hero, guide, obstacle_cfg)

    bash_first = would_bash_first(temper, guide_trait)
    if bash_first:
        do_bash(world, hero, obstacle_cfg)
        world.say(
            f'"I thought a hard bash would make the world obey," {hero.name} said. "It did not."'
        )
    else:
        world.say(
            f"{hero.name} tightened {hero.pronoun('possessive')} fingers on the staff, then let the wild idea go."
        )

    world.para()
    use_magic(world, hero, guide, obstacle_cfg, gift_cfg)
    reach_shrine(world, hero, quest_cfg, "learned" if bash_first else "listened")

    world.para()
    surprise_ending(world, hero, guide, quest_cfg, "learned" if bash_first else "listened")

    world.facts.update(
        bash_first=bash_first,
        outcome="learned" if bash_first else "listened",
        danger=world.get("path").meters["danger"],
        opened=world.get("obstacle").meters["open"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    quest_cfg = world.facts["quest"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    gift_cfg = world.facts["gift_cfg"]
    outcome = world.facts["outcome"]
    second = "tries to bash a magical obstacle before learning better" if outcome == "learned" else "is warned away from a reckless bash and chooses patience"
    return [
        'Write a short child-facing myth that includes the words "bash", "reckless", and "putter", and uses Quest, Magic, and Surprise.',
        f"Tell a myth-like story about {hero.name} and a tortoise named Putter on a quest to {quest_cfg.shrine}, where {second}.",
        f"Write a gentle quest story in which {gift_cfg.label} is the right magic for a {obstacle_cfg.label}, and end with a surprising blessing for the village.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    quest_cfg = world.facts["quest"]
    obstacle_cfg = world.facts["obstacle_cfg"]
    gift_cfg = world.facts["gift_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.name}, who went on a quest, and {guide.name}, the little tortoise who traveled beside {hero.pronoun('object')}. They were trying to help the village by reaching {quest_cfg.shrine}.",
        ),
        (
            "What was the quest for?",
            f"The quest was meant to help because {quest_cfg.village_need}. {hero.name} carried {gift_cfg.phrase} to the shrine so the village could receive {quest_cfg.boon} again.",
        ),
        (
            f"What blocked the way?",
            f"The way was blocked by a {obstacle_cfg.label}. It was magical, so it would not answer to pushing or hitting like an ordinary thing.",
        ),
        (
            f"Why did Putter warn {hero.name} not to be reckless?",
            f"{guide.name} knew the {obstacle_cfg.label} wanted {obstacle_cfg.needed_magic} magic, not force. A reckless bash would only wake its temper and make the path more dangerous.",
        ),
    ]
    if outcome == "learned":
        qa.append(
            (
                f"What happened when {hero.name} tried to bash the obstacle?",
                f"The obstacle grew angry and the path felt dangerous, which frightened {hero.name}. That scary turn showed {hero.pronoun('object')} that force was the wrong answer.",
            )
        )
        qa.append(
            (
                f"How was the problem solved after that?",
                f"{hero.name} listened to {guide.name} and used the {gift_cfg.label} the right way. The proper magic soothed the {obstacle_cfg.label} and opened the road.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.name} bash the obstacle?",
                f"No. {hero.name} almost did, but stopped and listened to {guide.name} instead. That patient choice kept the path calm and let the quest continue.",
            )
        )
    qa.append(
        (
            "What was the surprise at the end?",
            f"The surprise was that {quest_cfg.surprise[0].lower() + quest_cfg.surprise[1:]} The ending feels magical because the world gives back more wonder than the travelers expected.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the village changed for the better: {quest_cfg.ending} The last image proves the quest mattered beyond the hill itself.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    obstacle_cfg = world.facts["obstacle_cfg"]
    gift_cfg = world.facts["gift_cfg"]
    tags = {"quest", "myth", "tortoise", "surprise"}
    tags.add("reckless")
    if obstacle_cfg.needed_magic == "song":
        tags.add("song")
    if obstacle_cfg.needed_magic == "dew":
        tags.add("dew")
    if obstacle_cfg.needed_magic == "star":
        tags.add("star")
    tags |= gift_cfg.tags
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for (name, *_) in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Q, O, G) :- quest(Q), obstacle(O), gift(G), needs(O, M), has_magic(G, M).

guide_power(1) :- chosen_guide_trait(sleepy).
guide_power(2) :- chosen_guide_trait(patient).
guide_power(3) :- chosen_guide_trait(wise).

temper_haste(0) :- chosen_temper(careful).
temper_haste(0) :- chosen_temper(eager).
temper_haste(1) :- chosen_temper(bold).
temper_haste(2) :- chosen_temper(reckless).

bash_first :- temper_haste(H), guide_power(P), H > P - 1.

outcome(learned) :- bash_first.
outcome(listened) :- not bash_first.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.needed_magic))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("has_magic", gid, gift.magic))
    for temper in sorted(TEMPER_HASTE):
        lines.append(asp.fact("temper_kind", temper))
    for trait in sorted(GUIDE_PATIENCE):
        lines.append(asp.fact("guide_trait_kind", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_temper", params.temper),
            asp.fact("chosen_guide_trait", params.guide_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    text = buf.getvalue()
    if not sample.story or "{" in sample.story or "}" in sample.story:
        raise StoryError("(Smoke test failed: story text looks broken.)")
    if "bash" not in sample.story.lower() or "putter" not in sample.story.lower():
        raise StoryError("(Smoke test failed: seed words missing from story text.)")
    if not text.strip():
        raise StoryError("(Smoke test failed: emit produced no output.)")


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(40):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp_val = asp_outcome(params)
        if py != asp_val:
            bad += 1
            print("  outcome mismatch:", params, py, asp_val)
    if bad == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like quest storyworld with Putter the tortoise, matching magic, and a surprise ending."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--temper", choices=sorted(TEMPER_HASTE))
    ap.add_argument("--guide-trait", choices=sorted(GUIDE_PATIENCE))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (quest, obstacle, gift) triples from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest is not None and args.quest not in QUESTS:
        raise StoryError(f"(Unknown quest '{args.quest}'.)")
    if args.obstacle is not None and args.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{args.obstacle}'.)")
    if args.gift is not None and args.gift not in GIFTS:
        raise StoryError(f"(Unknown gift '{args.gift}'.)")
    if args.temper is not None and args.temper not in TEMPER_HASTE:
        raise StoryError(f"(Unknown temper '{args.temper}'.)")
    if args.guide_trait is not None and args.guide_trait not in GUIDE_PATIENCE:
        raise StoryError(f"(Unknown guide trait '{args.guide_trait}'.)")
    if args.hero_type is not None and args.hero_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero type '{args.hero_type}'.)")

    if args.obstacle and args.gift and not valid_combo(args.quest or next(iter(QUESTS)), args.obstacle, args.gift):
        raise StoryError(explain_rejection(args.obstacle, args.gift))

    combos = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.gift is None or combo[2] == args.gift)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, obstacle_id, gift_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    temper = args.temper or rng.choice(sorted(TEMPER_HASTE))
    guide_trait = args.guide_trait or rng.choice(sorted(GUIDE_PATIENCE))
    return StoryParams(
        quest=quest_id,
        obstacle=obstacle_id,
        gift=gift_id,
        temper=temper,
        guide_trait=guide_trait,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest '{params.quest}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift '{params.gift}'.)")
    if params.temper not in TEMPER_HASTE:
        raise StoryError(f"(Unknown temper '{params.temper}'.)")
    if params.guide_trait not in GUIDE_PATIENCE:
        raise StoryError(f"(Unknown guide trait '{params.guide_trait}'.)")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero type '{params.hero_type}'.)")
    if not valid_combo(params.quest, params.obstacle, params.gift):
        raise StoryError(explain_rejection(params.obstacle, params.gift))

    world = tell(
        quest_cfg=QUESTS[params.quest],
        obstacle_cfg=OBSTACLES[params.obstacle],
        gift_cfg=GIFTS[params.gift],
        temper=params.temper,
        guide_trait=params.guide_trait,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, obstacle, gift) combos:\n")
        for quest_id, obstacle_id, gift_id in combos:
            print(f"  {quest_id:7} {obstacle_id:12} {gift_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.quest} / {p.obstacle} / {p.gift} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
