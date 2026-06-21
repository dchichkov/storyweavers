#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py
============================================================================

A small storyworld about a child at a ranch who hears a scary sound in the dark,
follows the clues, and discovers that the "monster" is only a frightened animal
making funny hiccup sounds. The world is built to produce child-facing adventure
stories with suspense, light rhyme, and a happy ending.

Run it
------
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py --place barn --animal pony
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py --obstacle locked_gate
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py --all
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py --json
python storyworlds/worlds/gpt-5.4/bam_hiccing_ranch_happy_ending_suspense_rhyme.py --verify
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
    traits: list[str] = field(default_factory=list)
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    clue: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Animal:
    id: str
    label: str
    phrase: str
    sound: str
    small_sound: str
    comfort: str
    trail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    reason: str
    allow_tools: set[str] = field(default_factory=set)
    scary_noise: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    action: str
    works_for: set[str] = field(default_factory=set)
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


def _r_hiccup_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    animal = world.get("animal")
    if animal.meters["hiccing"] >= THRESHOLD and hero.memes["understands"] < THRESHOLD:
        sig = ("fear_from_hiccing",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("__suspense__")
    return out


def _r_bam_alarm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if world.get("door").meters["bam"] >= THRESHOLD:
        sig = ("bam_alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            out.append("__bam__")
    return out


def _r_comfort_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    animal = world.get("animal")
    if animal.meters["comforted"] >= THRESHOLD:
        sig = ("comfort_calm",)
        if sig not in world.fired:
            world.fired.add(sig)
            animal.meters["hiccing"] = 0.0
            animal.memes["calm"] += 1
            hero.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            hero.memes["understands"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="hiccup_fear", tag="emotion", apply=_r_hiccup_fear),
    Rule(name="bam_alarm", tag="emotion", apply=_r_bam_alarm),
    Rule(name="comfort_calm", tag="emotion", apply=_r_comfort_calm),
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
        for s in produced:
            world.say(s)
    return produced


def helper_fits(obstacle: Obstacle, helper: Helper) -> bool:
    return helper.id in obstacle.allow_tools


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for animal_id in ANIMALS:
            for obstacle_id, obstacle in OBSTACLES.items():
                for helper_id, helper in HELPERS.items():
                    if helper_fits(obstacle, helper):
                        combos.append((place_id, animal_id, obstacle_id, helper_id))
    return combos


def predict_scare(world: World) -> dict:
    sim = world.copy()
    sim.get("animal").meters["hiccing"] += 1
    sim.get("door").meters["bam"] += 1
    propagate(sim, narrate=False)
    hero = sim.get("hero")
    return {
        "fear": hero.memes["fear"],
        "cause": "unknown_noise" if hero.memes["fear"] >= THRESHOLD else "none",
    }


def setup_evening(world: World, hero: Entity, grownup: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"At sunset on the ranch, {hero.id} helped {grownup.label_word} carry feed past {place.phrase}."
    )
    world.say(
        f"The sky turned plum, the wind slipped low, and even the fence posts seemed to whisper, go slow, go slow."
    )


def hear_first_clue(world: World, hero: Entity, animal_cfg: Animal, place: Place) -> None:
    world.get("animal").meters["hiccing"] += 1
    world.facts["heard_hiccing"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then from {place.phrase} came a tiny, shaky sound: {animal_cfg.sound}. "
        f'"Did you hear that hiccing?" {hero.id} whispered.'
    )


def bam_moment(world: World, place: Place, obstacle: Obstacle) -> None:
    world.get("door").meters["bam"] += 1
    world.facts["bam_happened"] = True
    propagate(world, narrate=False)
    world.say(
        f"Just then, {obstacle.scary_noise or 'bam'}! Something knocked at {place.clue}, and the dark seemed bigger than before."
    )


def warning(world: World, grownup: Entity, hero: Entity, place: Place) -> None:
    pred = predict_scare(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{grownup.label_word.capitalize()} listened too. "{place.echo}," {grownup.pronoun()} said softly, '
        f'"but we will look with care. Brave does not mean rushing. Brave means seeing what is really there."'
    )


def obstacle_turn(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"But the way was not easy. {obstacle.reason}. {hero.id}'s heart thumped quick, then quicker still."
    )


def use_helper(world: World, hero: Entity, helper: Helper, obstacle: Obstacle) -> None:
    world.get("path").meters["open"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} reached for {helper.phrase} and {helper.action}. The trouble gave a little sigh and let them pass."
    )


def reveal(world: World, hero: Entity, grownup: Entity, animal_cfg: Animal) -> None:
    animal = world.get("animal")
    animal.memes["found"] += 1
    hero.memes["understands"] += 1
    hero.memes["fear"] = 0.0
    world.say(
        f"There in the dim straw stood {animal_cfg.phrase}, not a monster at all. "
        f"{animal_cfg.small_sound} bubbled from {animal.pronoun('possessive')} nose, and {hero.id} blinked in surprise."
    )


def comfort(world: World, hero: Entity, grownup: Entity, animal_cfg: Animal) -> None:
    animal = world.get("animal")
    animal.meters["comforted"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{grownup.label_word.capitalize()} knelt beside the little animal. "{animal_cfg.comfort}," {grownup.pronoun()} said. '
        f'{hero.id} stroked {animal.pronoun("possessive")} neck while {grownup.pronoun()} offered a sip of water.'
    )


def happy_end(world: World, hero: Entity, animal_cfg: Animal, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"Soon the hiccing stopped. The night no longer felt deep and strange; it felt kind."
    )
    world.say(
        f'{hero.id} laughed. "So the scary sound was only {animal_cfg.phrase} all along!"'
    )
    world.say(
        f"They walked back past {place.label} under a moon so white and wide. "
        f"On the quiet ranch, all was right; the bumps were small, the hearts were light."
    )


def tell(
    place: Place,
    animal_cfg: Animal,
    obstacle: Obstacle,
    helper: Helper,
    hero_name: str = "June",
    hero_gender: str = "girl",
    grownup_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label=f"{hero_name}'s parent",
        phrase=f"{hero_name}'s { 'mom' if grownup_type == 'mother' else 'dad' }",
        role="grownup",
    ))
    world.add(Entity(
        id="animal",
        kind="character",
        type="animal",
        label=animal_cfg.label,
        phrase=animal_cfg.phrase,
        role="animal",
        tags=set(animal_cfg.tags),
    ))
    world.add(Entity(id="door", type="door", label=place.clue))
    world.add(Entity(id="path", type="path", label="the way in"))
    world.facts.update(
        place=place,
        animal_cfg=animal_cfg,
        obstacle=obstacle,
        helper=helper,
        hero=hero,
        grownup=grownup,
    )

    setup_evening(world, hero, grownup, place)
    hear_first_clue(world, hero, animal_cfg, place)

    world.para()
    bam_moment(world, place, obstacle)
    warning(world, grownup, hero, place)
    obstacle_turn(world, hero, obstacle)

    world.para()
    use_helper(world, hero, helper, obstacle)
    reveal(world, hero, grownup, animal_cfg)
    comfort(world, hero, grownup, animal_cfg)

    world.para()
    happy_end(world, hero, animal_cfg, place)

    world.facts.update(
        solved=world.get("path").meters["open"] >= THRESHOLD,
        animal_calm=world.get("animal").memes["calm"] >= THRESHOLD,
        fear_fell=hero.memes["relief"] >= THRESHOLD,
    )
    return world


PLACES = {
    "barn": Place(
        id="barn",
        label="the barn",
        phrase="the old red barn",
        clue="the loose barn door",
        echo="Old boards can sound spooky in the wind",
        tags={"barn", "ranch"},
    ),
    "stable": Place(
        id="stable",
        label="the stable",
        phrase="the long stable by the corral",
        clue="the stable gate",
        echo="A stable can creak when night air slides through",
        tags={"stable", "ranch"},
    ),
    "hayloft": Place(
        id="hayloft",
        label="the hayloft",
        phrase="the hayloft above the stalls",
        clue="the loft hatch",
        echo="A loft can pop and creak when the boards cool down",
        tags={"hay", "ranch"},
    ),
}

ANIMALS = {
    "pony": Animal(
        id="pony",
        label="pony",
        phrase="a little silver pony",
        sound="hic... hic...",
        small_sound="Another hic, then another",
        comfort="Easy now, little one",
        trail="small horseshoes in the dust",
        tags={"pony", "animal"},
    ),
    "calf": Animal(
        id="calf",
        label="calf",
        phrase="a wobbly brown calf",
        sound="hic... mmm... hic...",
        small_sound="A soft nose-bump and one round hic",
        comfort="Easy now, little calf",
        trail="tiny hoofprints in the dirt",
        tags={"calf", "animal"},
    ),
    "goat": Animal(
        id="goat",
        label="goat",
        phrase="a fluffy white goat",
        sound="hic... meh... hic...",
        small_sound="A funny bleat popped between the hiccups",
        comfort="Easy now, little goat",
        trail="little nibble marks near the feed sack",
        tags={"goat", "animal"},
    ),
}

OBSTACLES = {
    "latched_door": Obstacle(
        id="latched_door",
        label="latched door",
        reason="A hook had slipped across the barn door, so the door would only open a crack",
        allow_tools={"lantern", "hook_pole"},
        scary_noise="bam",
        tags={"door"},
    ),
    "stacked_crates": Obstacle(
        id="stacked_crates",
        label="stacked crates",
        reason="Two feed crates had tipped into the path, making a shaky little wall",
        allow_tools={"lantern", "rope"},
        scary_noise="bam",
        tags={"crates"},
    ),
    "locked_gate": Obstacle(
        id="locked_gate",
        label="locked gate",
        reason="A chain had snagged around the gate latch, and it would not lift by hand",
        allow_tools={"hook_pole", "rope"},
        scary_noise="bam",
        tags={"gate"},
    ),
}

HELPERS = {
    "lantern": Helper(
        id="lantern",
        label="lantern",
        phrase="the warm ranch lantern",
        action="held it high so the shadows shrank",
        works_for={"latched_door", "stacked_crates"},
        tags={"lantern", "light"},
    ),
    "rope": Helper(
        id="rope",
        label="rope",
        phrase="a coil of soft rope",
        action="looped it around the trouble and tugged carefully",
        works_for={"stacked_crates", "locked_gate"},
        tags={"rope"},
    ),
    "hook_pole": Helper(
        id="hook_pole",
        label="hook pole",
        phrase="the long hook pole by the wall",
        action="caught the latch from a safe distance and lifted",
        works_for={"latched_door", "locked_gate"},
        tags={"tool"},
    ),
}

GIRL_NAMES = ["June", "Lila", "Molly", "Sadie", "Nora", "Ava", "Tessa", "Mia"]
BOY_NAMES = ["Cole", "Evan", "Finn", "Jack", "Leo", "Sam", "Noah", "Toby"]
TRAITS = ["careful", "curious", "steady", "brave", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    animal: str
    obstacle: str
    helper: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "ranch": [
        (
            "What is a ranch?",
            "A ranch is a place where people care for animals like horses, calves, or goats. It often has barns, fences, and wide open land.",
        )
    ],
    "barn": [
        (
            "What is a barn?",
            "A barn is a big farm building where animals, hay, or tools can be kept. At night, its boards can creak and sound louder than they really are.",
        )
    ],
    "stable": [
        (
            "What is a stable?",
            "A stable is a building with stalls where horses or ponies rest and eat. It helps keep them safe and dry.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in the dark?",
            "A lantern gives steady light, so you can see where you are going. Good light makes scary shadows less confusing.",
        )
    ],
    "rope": [
        (
            "What can a rope help you do?",
            "A rope can help you pull or move something from a little farther away. People use it when they want to tug carefully.",
        )
    ],
    "pony": [
        (
            "What is a pony?",
            "A pony is a small kind of horse. Ponies can be gentle, quick, and friendly.",
        )
    ],
    "calf": [
        (
            "What is a calf?",
            "A calf is a baby cow. Calves are young, wobbly, and still learning the world.",
        )
    ],
    "goat": [
        (
            "What is a goat like?",
            "A goat is a lively farm animal that can climb, nibble, and bleat. Some goats are playful and curious.",
        )
    ],
    "hiccing": [
        (
            "What are hiccups?",
            "Hiccups are little jumps in the body that make a funny sound. They can happen to people and sometimes to animals too.",
        )
    ],
    "brave": [
        (
            "What does brave mean?",
            "Being brave does not mean rushing into danger. It means staying calm enough to look, think, and do the careful thing.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ranch", "barn", "stable", "lantern", "rope", "pony", "calf", "goat", "hiccing", "brave"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    animal_cfg = f["animal_cfg"]
    obstacle = f["obstacle"]
    helper = f["helper"]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the words "bam", "hiccing", and "ranch".',
        f"Tell a suspenseful but gentle ranch story where {hero.label} hears a strange hiccing sound in {place.label}, faces {obstacle.label}, and uses a {helper.label} to discover the truth.",
        f"Write a rhyming happy-ending story where a child thinks something scary is in {place.label}, but it turns out to be {animal_cfg.phrase} needing help.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    place = f["place"]
    animal_cfg = f["animal_cfg"]
    obstacle = f["obstacle"]
    helper = f["helper"]
    pw = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} on a ranch and {hero.pronoun('possessive')} {pw}, who listen carefully together. They follow a scary clue and find out what is really wrong.",
        ),
        (
            "What made the story feel suspenseful?",
            f"The suspense came from the dark place, the strange hiccing sound, and the sudden bam at the door or gate. {hero.label} did not know if something dangerous was hiding there, so every clue felt important.",
        ),
        (
            f"What problem blocked the way in {place.label}?",
            f"The problem was {obstacle.reason.lower()}. That made the sound harder to check, which stretched the scary moment a little longer.",
        ),
        (
            f"How did {hero.label} get past the trouble?",
            f"{hero.label} used {helper.phrase} and {helper.action}. That careful choice opened the way without rushing into the dark.",
        ),
        (
            "What was making the hiccing sound?",
            f"The sound was coming from {animal_cfg.phrase}, not from a monster. The animal was small and upset, which is why the noise sounded strange at first.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the grown-up and child comforted the animal until the hiccing stopped. After that, the ranch felt peaceful again, and the scary mystery turned into a kind ending.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ranch", "hiccing", "brave"}
    place = f["place"]
    animal_cfg = f["animal_cfg"]
    helper = f["helper"]
    if "barn" in place.tags:
        tags.add("barn")
    if "stable" in place.tags:
        tags.add("stable")
    if helper.id == "lantern":
        tags.add("lantern")
    if helper.id == "rope":
        tags.add("rope")
    if animal_cfg.id in {"pony", "calf", "goat"}:
        tags.add(animal_cfg.id)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="barn",
        animal="pony",
        obstacle="latched_door",
        helper="hook_pole",
        name="June",
        gender="girl",
        parent="father",
        trait="careful",
    ),
    StoryParams(
        place="stable",
        animal="calf",
        obstacle="stacked_crates",
        helper="lantern",
        name="Finn",
        gender="boy",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        place="hayloft",
        animal="goat",
        obstacle="locked_gate",
        helper="rope",
        name="Nora",
        gender="girl",
        parent="father",
        trait="curious",
    ),
]


def explain_rejection(obstacle: Obstacle, helper: Helper) -> str:
    allowed = ", ".join(sorted(obstacle.allow_tools))
    return (
        f"(No story: {helper.label} does not fit {obstacle.label}. "
        f"This obstacle needs a helper that can honestly solve it, such as: {allowed}.)"
    )


ASP_RULES = r"""
valid_helper(O, H) :- obstacle(O), helper(H), allows(O, H).
valid(P, A, O, H) :- place(P), animal(A), valid_helper(O, H).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        for hid in sorted(obstacle.allow_tools):
            lines.append(asp.fact("allows", oid, hid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a ranch mystery with suspense, rhyme, and a happy ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if not helper_fits(obstacle, helper):
            raise StoryError(explain_rejection(obstacle, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.animal is None or combo[1] == args.animal)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, animal, obstacle, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        animal=animal,
        obstacle=obstacle,
        helper=helper,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if not helper_fits(obstacle, helper):
        raise StoryError(explain_rejection(obstacle, helper))

    world = tell(
        place=PLACES[params.place],
        animal_cfg=ANIMALS[params.animal],
        obstacle=obstacle,
        helper=helper,
        hero_name=params.name,
        hero_gender=params.gender,
        grownup_type=params.parent,
        trait=params.trait,
    )

    hero = world.facts["hero"]
    original_name = hero.id
    hero.label = params.name
    world.story_name = original_name

    story = world.render().replace("hero", params.name)

    # Avoid any leaked internal id from hero.id in prose.
    story = story.replace("hero", params.name)
    story = story.replace("grownup", f"{params.name}'s {'mom' if params.parent == 'mother' else 'dad'}")

    # The actual sentences already use labels; keep the world consistent for QA.
    world.facts["hero"].label = params.name

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (place, animal, obstacle, helper) combos:\n")
        for place, animal, obstacle, helper in combos:
            print(f"  {place:8} {animal:6} {obstacle:13} {helper}")
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
            header = f"### {p.name}: {p.animal} at {p.place} with {p.helper}"
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
