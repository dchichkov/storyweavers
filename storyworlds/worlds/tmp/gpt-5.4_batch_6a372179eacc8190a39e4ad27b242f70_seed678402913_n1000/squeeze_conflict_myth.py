#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py
==================================================

A standalone storyworld in a child-facing myth style.

Premise
-------
In a small old valley, a spirit brings one good thing each day: river water,
morning wind, or first light. On this day, the gift cannot reach the people,
because the spirit tries to squeeze through a narrow pass that has been choked
by reeds, roots, or fallen stones. The harder the spirit fights, the more the
valley trembles. A child helper sees that conflict makes the trouble worse,
finds the right remedy, and helps the spirit pass in peace.

This world prefers a small set of reasonable variants over broad coverage:
each obstacle has one sensible remedy, and explicit mismatches are refused.

Run it
------
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --spirit river_serpent --obstacle stones --remedy lever
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --obstacle reeds --remedy lever
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --all
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --trace
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --json
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --asp
python storyworlds/worlds/gpt-5.4/squeeze_conflict_myth.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Spirit:
    id: str
    label: str
    title: str
    gift: str
    gift_effect: str
    passage: str
    voice: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    severity: int
    harm: str
    matching_remedy: str
    clearing: str
    snag: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    verb: str
    power: int
    use_text: str
    lesson_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_conflict(world: World) -> list[str]:
    spirit = world.get("spirit")
    village = world.get("village")
    if spirit.meters["strain"] < THRESHOLD:
        return []
    sig = ("conflict", int(spirit.meters["strain"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    spirit.memes["anger"] += 1
    village.meters["unease"] += 1
    hero = world.get("hero")
    hero.memes["worry"] += 1
    return ["__conflict__"]


def _r_damage(world: World) -> list[str]:
    spirit = world.get("spirit")
    village = world.get("village")
    if spirit.meters["strain"] < 2.0:
        return []
    sig = ("damage", int(spirit.meters["strain"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["damage"] += 1
    hero = world.get("hero")
    hero.memes["urgency"] += 1
    return ["__damage__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="damage", tag="physical", apply=_r_damage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SPIRITS = {
    "river_serpent": Spirit(
        id="river_serpent",
        label="river serpent",
        title="the River Serpent",
        gift="water",
        gift_effect="the fields drank and the ducks paddled in silver loops",
        passage="the stone throat of the pass",
        voice="like jars singing when they are filled",
        ending="slid into the valley in one bright blue curve",
        tags={"river", "water", "serpent"},
    ),
    "wind_stag": Spirit(
        id="wind_stag",
        label="wind stag",
        title="the Wind Stag",
        gift="wind",
        gift_effect="the mills turned and the laundry snapped like little flags",
        passage="the high notch between two cliffs",
        voice="like flutes hidden in grass",
        ending="leaped through the notch and shook cool air from its antlers",
        tags={"wind", "breeze", "stag"},
    ),
    "sun_lion": Spirit(
        id="sun_lion",
        label="sun lion",
        title="the Sun Lion",
        gift="light",
        gift_effect="the roofs warmed and the fig leaves opened their hands",
        passage="the eastern gate in the mountain",
        voice="like bronze bells struck softly",
        ending="poured through the gate and laid gold across the valley floor",
        tags={"sun", "light", "lion"},
    ),
}

OBSTACLES = {
    "reeds": Obstacle(
        id="reeds",
        label="reeds",
        phrase="a knot of dry reeds",
        severity=1,
        harm="the streamside grass bent in the quarreling gusts",
        matching_remedy="comb",
        clearing="combed the reeds apart",
        snag="caught and whispered around every edge",
        tags={"reeds", "plants"},
    ),
    "roots": Obstacle(
        id="roots",
        label="roots",
        phrase="a braid of old roots",
        severity=2,
        harm="dust danced from the shrine steps and little stones skipped downhill",
        matching_remedy="spade",
        clearing="cut the roots away from the pass",
        snag="held fast like clenched fingers",
        tags={"roots", "tree"},
    ),
    "stones": Obstacle(
        id="stones",
        label="stones",
        phrase="a tumble of fallen stones",
        severity=3,
        harm="a garden wall cracked and the goats cried from their pen",
        matching_remedy="lever",
        clearing="pried the stones loose one by one",
        snag="jammed the opening as if the mountain had shut its teeth",
        tags={"stones", "rock"},
    ),
}

REMEDIES = {
    "comb": Remedy(
        id="comb",
        label="reed comb",
        phrase="a long reed comb from the shrine shelf",
        verb="comb",
        power=1,
        use_text="used the long teeth to tease a path open",
        lesson_text="small tangles answer to patient fingers",
        tags={"comb", "patience"},
    ),
    "spade": Remedy(
        id="spade",
        label="moon spade",
        phrase="a moon-shaped spade from the fig tree",
        verb="cut",
        power=2,
        use_text="pressed the shining edge down and sliced the roots apart",
        lesson_text="living knots must be loosened with care, not rage",
        tags={"spade", "care"},
    ),
    "lever": Remedy(
        id="lever",
        label="ash-wood lever",
        phrase="an ash-wood lever from the old mill",
        verb="pry",
        power=3,
        use_text="set the wood under the stones and lifted until the heap rolled free",
        lesson_text="heavy trouble yields when strength is guided wisely",
        tags={"lever", "strength"},
    ),
}

GIRL_NAMES = ["Tala", "Mira", "Neri", "Ila", "Sena", "Luma", "Pia", "Rina"]
BOY_NAMES = ["Orin", "Daren", "Tavi", "Nilo", "Soren", "Mika", "Pavel", "Lio"]
TRAITS = ["brave", "watchful", "gentle", "steady", "quick", "thoughtful"]
TEMPER_ORDER = ["calm", "proud"]


def valid_combo(obstacle_id: str, remedy_id: str) -> bool:
    if obstacle_id not in OBSTACLES or remedy_id not in REMEDIES:
        return False
    obstacle = OBSTACLES[obstacle_id]
    remedy = REMEDIES[remedy_id]
    return obstacle.matching_remedy == remedy.id and remedy.power >= obstacle.severity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for spirit_id in sorted(SPIRITS):
        for obstacle_id in sorted(OBSTACLES):
            for remedy_id in sorted(REMEDIES):
                if valid_combo(obstacle_id, remedy_id):
                    combos.append((spirit_id, obstacle_id, remedy_id))
    return combos


def damage_score(obstacle: Obstacle, temper: str, delay: int) -> int:
    pride = 1 if temper == "proud" else 0
    return obstacle.severity + delay + pride


def outcome_of_params(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    return "scarred" if damage_score(obstacle, params.temper, params.delay) >= 5 else "healed"


def predict_struggle(world: World, obstacle: Obstacle, temper: str, delay: int) -> dict:
    sim = world.copy()
    spirit = sim.get("spirit")
    for _ in range(obstacle.severity + delay + (1 if temper == "proud" else 0)):
        spirit.meters["strain"] += 1
        propagate(sim, narrate=False)
    village = sim.get("village")
    return {
        "damage": village.meters["damage"],
        "unease": village.meters["unease"],
    }


def opening(world: World, spirit_cfg: Spirit, hero: Entity, obstacle: Obstacle) -> None:
    spirit = world.get("spirit")
    village = world.get("village")
    spirit.memes["duty"] += 1
    hero.memes["wonder"] += 1
    village.meters["hope"] += 1
    world.say(
        f"In the oldest days, when hills still remembered the names of the stars, "
        f"the people of the valley waited each morning for {spirit_cfg.title}."
    )
    world.say(
        f"When the spirit came, it brought {spirit_cfg.gift}, and then {spirit_cfg.gift_effect}."
    )
    world.say(
        f"Among the waiting people was {hero.id}, a {hero.attrs['trait']} child who listened closely to "
        f"mountains and birds."
    )
    world.say(
        f"That day, though, {obstacle.phrase} had grown across {spirit_cfg.passage}."
    )


def spirit_struggles(world: World, spirit_cfg: Spirit, obstacle: Obstacle, temper: str, delay: int) -> None:
    spirit = world.get("spirit")
    world.say(
        f"{spirit_cfg.title} reached the opening and tried to squeeze through, but the {obstacle.label} "
        f"{obstacle.snag}."
    )
    loops = obstacle.severity + delay + (1 if temper == "proud" else 0)
    for _ in range(loops):
        spirit.meters["strain"] += 1
        propagate(world, narrate=False)
    if temper == "proud":
        spirit.memes["pride"] += 1
        world.say(
            f'"Move for me!" cried the spirit in a voice {spirit_cfg.voice}. '
            f'"I have crossed these hills since before your roots and stones were born."'
        )
    else:
        world.say(
            f'The spirit pushed once, then twice, and the pass answered only with a hard, scraping sound.'
        )
    village = world.get("village")
    if village.meters["damage"] >= THRESHOLD:
        world.say(
            f"The valley shook with the quarrel. {obstacle.harm}"
        )
    else:
        world.say(
            "The birds flew up from the trees, and the people looked at one another, wondering why the gift had not come."
        )


def hero_warns(world: World, spirit_cfg: Spirit, obstacle: Obstacle, temper: str, delay: int) -> None:
    hero = world.get("hero")
    pred = predict_struggle(world, obstacle, temper, delay)
    world.facts["predicted_damage"] = pred["damage"]
    world.facts["predicted_unease"] = pred["unease"]
    hero.memes["courage"] += 1
    if pred["damage"] >= THRESHOLD:
        world.say(
            f"{hero.id} stepped onto the shrine stones and called, "
            f'"Great {spirit_cfg.label}, if you fight the pass, the valley will suffer before {spirit_cfg.gift} arrives."'
        )
    else:
        world.say(
            f"{hero.id} lifted both hands and called, "
            f'"Great {spirit_cfg.label}, the pass is narrow today. Please do not quarrel with the mountain."'
        )
    world.say(
        f'"Let me help. Not every door opens to anger."'
    )


def fetch_remedy(world: World, remedy: Remedy) -> None:
    hero = world.get("hero")
    helper = world.get("remedy")
    helper.attrs["carried"] = True
    world.say(
        f"So {hero.id} ran to fetch {remedy.phrase}."
    )


def clear_obstacle(world: World, obstacle: Obstacle, remedy: Remedy) -> None:
    hero = world.get("hero")
    spirit = world.get("spirit")
    spirit.memes["anger"] = 0.0
    spirit.memes["trust"] += 1
    world.get("village").meters["blocked"] = 0.0
    world.get("pass").meters["blocked"] = 0.0
    world.say(
        f"While the spirit held still, {hero.id} {remedy.use_text}. Soon {hero.pronoun()} "
        f"{obstacle.clearing}, and a clear way opened through the pass."
    )


def spirit_passes(world: World, spirit_cfg: Spirit) -> None:
    spirit = world.get("spirit")
    village = world.get("village")
    spirit.meters["flowing"] += 1
    village.meters["gift_received"] += 1
    village.memes["relief"] += 1
    world.say(
        f"Then {spirit_cfg.title} {spirit_cfg.ending}."
    )


def gentle_ending(world: World, spirit_cfg: Spirit, remedy: Remedy) -> None:
    hero = world.get("hero")
    spirit = world.get("spirit")
    spirit.memes["gratitude"] += 1
    hero.memes["joy"] += 1
    world.say(
        f'The spirit bent low and said, "Little one, today you taught me that {remedy.lesson_text}."'
    )
    world.say(
        f"From then on, whenever {spirit_cfg.title} met a narrow place, it slowed, listened, and passed in peace."
    )
    world.say(
        f"And the elders said that was why the valley stayed gentle even on busy mornings."
    )


def scarred_ending(world: World, spirit_cfg: Spirit, remedy: Remedy, obstacle: Obstacle) -> None:
    hero = world.get("hero")
    spirit = world.get("spirit")
    spirit.memes["shame"] += 1
    spirit.memes["gratitude"] += 1
    hero.memes["solemn"] += 1
    world.say(
        f'The spirit bowed its head. "My anger struck the valley before my gift did," it said. '
        f'"I will remember that {remedy.lesson_text}."'
    )
    world.say(
        f"The wall was mended, the goats were soothed, and the crack in the garden was filled with new earth, "
        f"but the people never forgot how loud conflict can become."
    )
    world.say(
        f"So in later years, when anyone felt ready to shove and squeeze at a stubborn thing, they would say, "
        f'"Do not fight like the {spirit_cfg.label}. Clear the way first."'
    )


def tell(
    spirit_cfg: Spirit,
    obstacle: Obstacle,
    remedy: Remedy,
    hero_name: str,
    hero_gender: str,
    hero_trait: str,
    temper: str,
    delay: int,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        attrs={"trait": hero_trait},
    ))
    spirit = world.add(Entity(
        id="spirit",
        kind="character",
        type="spirit",
        label=spirit_cfg.label,
        phrase=spirit_cfg.title,
        role="spirit",
        tags=set(spirit_cfg.tags),
    ))
    village = world.add(Entity(
        id="village",
        kind="thing",
        type="village",
        label="the valley village",
        role="village",
    ))
    world.add(Entity(
        id="pass",
        kind="thing",
        type="pass",
        label="the mountain pass",
        role="pass",
    ))
    world.add(Entity(
        id="remedy",
        kind="thing",
        type="tool",
        label=remedy.label,
        phrase=remedy.phrase,
        role="remedy",
        tags=set(remedy.tags),
    ))

    world.get("pass").meters["blocked"] = float(obstacle.severity)
    world.get("village").meters["blocked"] = 1.0

    opening(world, spirit_cfg, hero, obstacle)
    world.para()
    spirit_struggles(world, spirit_cfg, obstacle, temper, delay)
    hero_warns(world, spirit_cfg, obstacle, temper, delay)
    world.para()
    fetch_remedy(world, remedy)
    clear_obstacle(world, obstacle, remedy)
    spirit_passes(world, spirit_cfg)
    world.para()
    outcome = "scarred" if world.get("village").meters["damage"] >= THRESHOLD else "healed"
    if outcome == "healed":
        gentle_ending(world, spirit_cfg, remedy)
    else:
        scarred_ending(world, spirit_cfg, remedy, obstacle)

    world.facts.update(
        spirit_cfg=spirit_cfg,
        obstacle=obstacle,
        remedy_cfg=remedy,
        hero=hero,
        spirit=spirit,
        village=village,
        temper=temper,
        delay=delay,
        outcome=outcome,
        strain=int(spirit.meters["strain"]),
        damage=int(village.meters["damage"]),
        gift=spirit_cfg.gift,
    )
    return world


KNOWLEDGE = {
    "river": [
        (
            "What is a river?",
            "A river is moving water that flows across the land. It can carry water to fields, fish, and people."
        )
    ],
    "wind": [
        (
            "What is wind?",
            "Wind is moving air. You cannot hold it in your hands, but you can feel it on your face and see what it moves."
        )
    ],
    "sun": [
        (
            "Why is sunlight important?",
            "Sunlight warms the ground and helps plants grow. It also helps people see the world clearly."
        )
    ],
    "reeds": [
        (
            "What are reeds?",
            "Reeds are tall, thin plants that grow near water. When many reeds tangle together, they can make a thick knot."
        )
    ],
    "roots": [
        (
            "What do roots do?",
            "Roots hold a plant or tree in the ground and help it drink water. Old roots can twist together into a hard knot."
        )
    ],
    "stones": [
        (
            "What is a lever used for?",
            "A lever is a strong bar of wood or metal used to lift heavy things. It helps a small push move a big weight."
        )
    ],
    "comb": [
        (
            "What does a comb do?",
            "A comb separates and straightens tangled things. Its teeth help pull strands apart gently."
        )
    ],
    "spade": [
        (
            "What is a spade?",
            "A spade is a digging tool with a flat blade. People use it to cut soil or roots and move earth."
        )
    ],
    "care": [
        (
            "Why is patience useful when something is tangled?",
            "Patience helps you slow down and notice how the tangle fits together. When you move carefully, you can fix it without making the trouble worse."
        )
    ],
    "strength": [
        (
            "Why should strength be guided carefully?",
            "Strength can solve a hard problem, but only when it is aimed the right way. Wild force can break things that careful force would save."
        )
    ],
}
KNOWLEDGE_ORDER = ["river", "wind", "sun", "reeds", "roots", "stones", "comb", "spade", "care", "strength"]


@dataclass
class StoryParams:
    spirit: str
    obstacle: str
    remedy: str
    name: str
    gender: str
    trait: str
    temper: str
    delay: int
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spirit_cfg = f["spirit_cfg"]
    obstacle = f["obstacle"]
    hero = f["hero"]
    outcome = f["outcome"]
    if outcome == "healed":
        return [
            f'Write a short myth for a 3-to-5-year-old that includes the word "squeeze" and tells of a {spirit_cfg.label} blocked by {obstacle.label}.',
            f"Tell a child-facing myth where {hero.id}, a small {hero.type}, stops a quarrel between a mountain pass and {spirit_cfg.title}, then helps the spirit bring {spirit_cfg.gift}.",
            f"Write a gentle origin-style story in which conflict grows because a spirit tries to squeeze through a narrow place, but a child chooses the right tool and peace returns.",
        ]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "squeeze" and shows how conflict can hurt a whole valley.',
        f"Tell an origin myth where {hero.id} helps a proud {spirit_cfg.label}, but some harm is done before the lesson is learned.",
        f"Write a simple mythic story about a spirit fighting a blocked pass until a child clears the way and teaches that anger makes heavy trouble louder.",
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    spirit_cfg = f["spirit_cfg"]
    obstacle = f["obstacle"]
    remedy = f["remedy_cfg"]
    outcome = f["outcome"]
    damage = f["damage"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.attrs['trait']} child, and {spirit_cfg.title}. The story follows how they faced a blocked mountain pass together."
        ),
        (
            f"Why could {spirit_cfg.title} not reach the valley?",
            f"{obstacle.phrase.capitalize()} had grown across the pass, so the spirit could not get through. The spirit tried to squeeze past it, but the opening was too tight."
        ),
        (
            "What was the conflict in the story?",
            f"The conflict began when the spirit fought the blocked pass instead of stopping to clear it. Each angry push made the valley more afraid and turned a small blockage into a bigger problem."
        ),
        (
            f"How did {hero.id} help?",
            f"{hero.id} fetched {remedy.phrase} and used it the right way. That worked because {remedy.label} matched the kind of obstacle blocking the pass."
        ),
    ]
    if outcome == "healed":
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully: the spirit reached the valley and brought {spirit_cfg.gift}. After that, the spirit learned to slow down instead of fighting a narrow place."
            )
        )
    else:
        qa.append(
            (
                "Did the valley get hurt before the problem was fixed?",
                f"Yes. The valley was scarred before the pass was cleared, and damage happened {damage} time in the world model. Even so, the child's help stopped the trouble from growing further."
            )
        )
        qa.append(
            (
                "What lesson did the spirit learn?",
                f"The spirit learned that {remedy.lesson_text}. The story says conflict can grow louder than the problem itself if no one pauses to clear the way."
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    spirit_cfg = f["spirit_cfg"]
    obstacle = f["obstacle"]
    remedy = f["remedy_cfg"]
    if "river" in spirit_cfg.tags:
        tags.add("river")
    if "wind" in spirit_cfg.tags:
        tags.add("wind")
    if "sun" in spirit_cfg.tags:
        tags.add("sun")
    tags |= obstacle.tags
    tags |= remedy.tags
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if ent.tags:
            parts.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spirit="river_serpent",
        obstacle="reeds",
        remedy="comb",
        name="Tala",
        gender="girl",
        trait="watchful",
        temper="calm",
        delay=0,
    ),
    StoryParams(
        spirit="wind_stag",
        obstacle="roots",
        remedy="spade",
        name="Orin",
        gender="boy",
        trait="steady",
        temper="proud",
        delay=1,
    ),
    StoryParams(
        spirit="sun_lion",
        obstacle="stones",
        remedy="lever",
        name="Mira",
        gender="girl",
        trait="brave",
        temper="proud",
        delay=2,
    ),
    StoryParams(
        spirit="river_serpent",
        obstacle="stones",
        remedy="lever",
        name="Tavi",
        gender="boy",
        trait="thoughtful",
        temper="calm",
        delay=1,
    ),
]


def explain_rejection(obstacle_id: str, remedy_id: str) -> str:
    if obstacle_id not in OBSTACLES:
        return f"(No story: unknown obstacle '{obstacle_id}'.)"
    if remedy_id not in REMEDIES:
        return f"(No story: unknown remedy '{remedy_id}'.)"
    obstacle = OBSTACLES[obstacle_id]
    remedy = REMEDIES[remedy_id]
    if obstacle.matching_remedy != remedy.id:
        expected = obstacle.matching_remedy
        return (
            f"(No story: {remedy.label} does not reasonably clear {obstacle.phrase}. "
            f"Use --remedy {expected} instead.)"
        )
    if remedy.power < obstacle.severity:
        return (
            f"(No story: {remedy.label} is too weak for {obstacle.phrase}. "
            f"Pick a stronger fix.)"
        )
    return "(No story: this obstacle and remedy do not make a reasonable myth.)"


ASP_RULES = r"""
good_for(O, R) :- matching_remedy(O, R), power(R, P), severity(O, S), P >= S.
valid(S, O, R) :- spirit(S), obstacle(O), remedy(R), good_for(O, R).

pride_bonus(1) :- temper(proud).
pride_bonus(0) :- temper(calm).
damage_score(V) :- chosen_obstacle(O), severity(O, S), delay(D), pride_bonus(B), V = S + D + B.
outcome(scarred) :- damage_score(V), V >= 5.
outcome(healed) :- damage_score(V), V < 5.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for spirit_id in sorted(SPIRITS):
        lines.append(asp.fact("spirit", spirit_id))
    for obstacle_id, obstacle in sorted(OBSTACLES.items()):
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("severity", obstacle_id, obstacle.severity))
        lines.append(asp.fact("matching_remedy", obstacle_id, obstacle.matching_remedy))
    for remedy_id, remedy in sorted(REMEDIES.items()):
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("temper", params.temper),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a blocked pass, and a mythic conflict resolved by the right remedy."
    )
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--temper", choices=TEMPER_ORDER)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.remedy and not valid_combo(args.obstacle, args.remedy):
        raise StoryError(explain_rejection(args.obstacle, args.remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spirit is None or combo[0] == args.spirit)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spirit_id, obstacle_id, remedy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    temper = args.temper or rng.choice(TEMPER_ORDER)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        spirit=spirit_id,
        obstacle=obstacle_id,
        remedy=remedy_id,
        name=name,
        gender=gender,
        trait=trait,
        temper=temper,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.spirit not in SPIRITS:
        raise StoryError(f"(No story: unknown spirit '{params.spirit}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(No story: unknown remedy '{params.remedy}'.)")
    if params.temper not in TEMPER_ORDER:
        raise StoryError(f"(No story: unknown temper '{params.temper}'.)")
    if not valid_combo(params.obstacle, params.remedy):
        raise StoryError(explain_rejection(params.obstacle, params.remedy))

    world = tell(
        spirit_cfg=SPIRITS[params.spirit],
        obstacle=OBSTACLES[params.obstacle],
        remedy=REMEDIES[params.remedy],
        hero_name=params.name,
        hero_gender=params.gender,
        hero_trait=params.trait,
        temper=params.temper,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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


def asp_verify() -> int:
    rc = 0
    py_combos = set(valid_combos())
    asp_combos = set(asp_valid_combos())
    if py_combos == asp_combos:
        print(f"OK: ASP valid combos match Python ({len(py_combos)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_combos - py_combos:
            print("  only in ASP:", sorted(asp_combos - py_combos))
        if py_combos - asp_combos:
            print("  only in Python:", sorted(py_combos - asp_combos))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of_params(params)
        asp = asp_outcome(params)
        if py != asp:
            mismatches += 1
            print(f"  outcome mismatch for {params}: python={py} asp={asp}")
    if mismatches == 0:
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (spirit, obstacle, remedy) combos:\n")
        for spirit_id, obstacle_id, remedy_id in combos:
            print(f"  {spirit_id:14} {obstacle_id:8} {remedy_id}")
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
            header = f"### {p.name}: {p.spirit} blocked by {p.obstacle} ({outcome_of_params(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
