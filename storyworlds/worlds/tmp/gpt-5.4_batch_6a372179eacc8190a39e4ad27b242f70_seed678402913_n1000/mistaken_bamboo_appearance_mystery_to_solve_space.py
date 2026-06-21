#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py
==============================================================================

A standalone storyworld about a strange bamboo-like appearance in a space habitat.
The children first make a mistaken guess about what they are seeing, then solve
the mystery by testing the world carefully. The story stays small, concrete, and
child-facing while keeping a light space-adventure tone.

Run it
------
    python storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py
    python storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py --setting moon_base --appearance dust_forest
    python storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py --reveal space_blast
    python storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py --all --qa
    python storyworlds/worlds/gpt-5.4/mistaken_bamboo_appearance_mystery_to_solve_space.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        neutral_person = {"robot", "captain", "friend"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.kind == "character" or self.type in neutral_person:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    opening: str
    view: str
    hosts: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Appearance:
    id: str
    label: str
    phrase: str
    location: str
    looks_like: str
    move_text: str
    receptive: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    emits: set[str] = field(default_factory=set)
    explain: str = ""
    proof: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    label: str
    phrase: str
    action: str = ""
    checks: set[str] = field(default_factory=set)
    success: str = ""
    qa_text: str = ""
    sense: int = 3
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    appearance: str
    source: str
    reveal: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    parent: str
    hero_trait: str
    partner_trait: str
    robot_name: str
    seed: Optional[int] = None


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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "partner"}]

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


def _r_mystery_feelings(world: World) -> list[str]:
    out: list[str] = []
    anomaly = world.entities.get("anomaly")
    if anomaly is None or anomaly.meters["visible"] < THRESHOLD:
        return out
    sig = ("mystery_feelings", anomaly.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["curiosity"] += 1
        kid.memes["awe"] += 1
        kid.memes["worry"] += 1
    out.append("__mystery__")
    return out


def _r_solution_feelings(world: World) -> list[str]:
    out: list[str] = []
    source = world.entities.get("source")
    if source is None or source.meters["explained"] < THRESHOLD:
        return out
    sig = ("solution_feelings", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
        kid.memes["worry"] = 0.0
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="mystery_feelings", tag="emotional", apply=_r_mystery_feelings),
    Rule(name="solution_feelings", tag="emotional", apply=_r_solution_feelings),
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


SETTINGS = {
    "orbital_station": Setting(
        id="orbital_station",
        label="the ring station above the moon",
        opening="Far above the moon, a silver ring station hummed softly in the dark.",
        view="Through the wide cupola windows, the stars looked close enough to touch.",
        hosts={"bamboo_reflection", "bamboo_shadow"},
        tags={"station", "space"},
    ),
    "moon_base": Setting(
        id="moon_base",
        label="the moon base at the edge of a quiet crater",
        opening="At the edge of a quiet crater, the moon base glowed like a tiny city of lamps.",
        view="Beyond the clear dome, the ground lay pale and powdery under the stars.",
        hosts={"bamboo_reflection", "visor_glint"},
        tags={"moon", "space"},
    ),
    "crater_lab": Setting(
        id="crater_lab",
        label="the little science lab beside the rover shed",
        opening="Beside the rover shed, the little crater lab blinked with blue and green lights.",
        view="Every hallway felt like a tunnel inside a friendly spaceship.",
        hosts={"bamboo_shadow", "visor_glint"},
        tags={"lab", "space"},
    ),
}

APPEARANCES = {
    "dome_bars": Appearance(
        id="dome_bars",
        label="green bars on the dome",
        phrase="a strange green appearance of long bars across the dome glass",
        location="across the dome glass",
        looks_like="a ladder made of bamboo reaching up into space",
        move_text="The bars trembled whenever someone walked past the lighted garden door.",
        receptive={"glass", "light"},
        tags={"glass", "light"},
    ),
    "wall_waves": Appearance(
        id="wall_waves",
        label="wiggly bands on the wall",
        phrase="a wavering green appearance on the silver wall",
        location="on the silver wall",
        looks_like="bamboo shadows dancing in a secret breeze",
        move_text="The green lines swayed and shivered as if they were breathing.",
        receptive={"wall", "light", "moving"},
        tags={"wall", "shadow"},
    ),
    "dust_forest": Appearance(
        id="dust_forest",
        label="a tiny forest on the dust",
        phrase="a striped green appearance on the moon dust by the rover bay",
        location="on the moon dust by the rover bay",
        looks_like="a little bamboo forest growing where no plant should grow",
        move_text="When the rover visor tilted, the thin green stalks slid across the dust.",
        receptive={"dust", "light"},
        tags={"dust", "reflection"},
    ),
}

SOURCES = {
    "bamboo_reflection": Source(
        id="bamboo_reflection",
        label="bamboo reflection",
        phrase="the tall bamboo in the hydroponic garden",
        emits={"glass", "light"},
        explain="the tall bamboo in the hydroponic garden was shining back from curved glass",
        proof="When the lamp angle changed, the bars on the dome changed too.",
        tags={"bamboo", "reflection", "light"},
    ),
    "bamboo_shadow": Source(
        id="bamboo_shadow",
        label="bamboo shadow",
        phrase="the bamboo leaves beside a humming air fan",
        emits={"wall", "light", "moving"},
        explain="the bamboo leaves near the air fan were tossing their shadows across the wall",
        proof="When the fan paused, the dancing bands stopped dancing.",
        tags={"bamboo", "shadow", "moving"},
    ),
    "visor_glint": Source(
        id="visor_glint",
        label="visor glint",
        phrase="the rover's curved visor catching a picture of the bamboo rack",
        emits={"dust", "light"},
        explain="the rover's curved visor was catching the picture of the bamboo rack and tossing it onto the dust",
        proof="When the visor was covered, the little forest vanished at once.",
        tags={"bamboo", "reflection", "dust"},
    ),
}

REVEALS = {
    "dim_lamps": Reveal(
        id="dim_lamps",
        label="dim the grow lamps",
        phrase="the grow-lamp switch",
        action="slid the lamp control down until the greenhouse lights became soft and low",
        checks={"light"},
        success="At once the green pattern faded, and the children saw that the bright lines had needed the strong lamps all along.",
        qa_text="They dimmed the grow lamps, and the strange pattern faded right away.",
        sense=3,
        tags={"light", "investigate"},
    ),
    "pause_fan": Reveal(
        id="pause_fan",
        label="pause the air fan",
        phrase="the fan button",
        action="pressed the air-fan button for one careful second",
        checks={"moving"},
        success="The swaying lines froze, then melted away, and the mystery stopped looking alive.",
        qa_text="They paused the air fan, and the swaying bands stopped and faded.",
        sense=3,
        tags={"fan", "investigate"},
    ),
    "cover_visor": Reveal(
        id="cover_visor",
        label="cover the rover visor",
        phrase="a silver cloth",
        action="laid a silver cloth over the rover visor",
        checks={"dust"},
        success="The tiny green forest blinked out of the dust, as if someone had switched off an invisible projector.",
        qa_text="They covered the rover visor, and the little green forest disappeared from the dust.",
        sense=3,
        tags={"visor", "investigate"},
    ),
    "space_blast": Reveal(
        id="space_blast",
        label="blast it with the repair cannon",
        phrase="the repair cannon",
        action="aimed the repair cannon at the mystery",
        checks={"boom"},
        success="Nothing sensible happened.",
        qa_text="They tried a repair blast.",
        sense=1,
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Ava", "Nora", "Tess", "Ivy", "June", "Zoe"]
BOY_NAMES = ["Kai", "Leo", "Milo", "Jax", "Theo", "Finn", "Eli", "Ben"]
TRAITS = ["careful", "curious", "brave", "thoughtful", "quick", "calm"]
ROBOTS = ["Pip", "Comet", "Blink", "Moss", "Orbit"]


def source_matches_appearance(source: Source, appearance: Appearance) -> bool:
    return appearance.receptive.issubset(source.emits)


def reveal_matches_source(reveal: Reveal, source: Source) -> bool:
    return reveal.sense >= SENSE_MIN and reveal.checks.issubset(source.emits)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for source_id in sorted(setting.hosts):
            source = SOURCES[source_id]
            for appearance_id, appearance in APPEARANCES.items():
                if not source_matches_appearance(source, appearance):
                    continue
                for reveal_id, reveal in REVEALS.items():
                    if reveal_matches_source(reveal, source):
                        combos.append((setting_id, appearance_id, source_id, reveal_id))
    return sorted(combos)


def explain_source_mismatch(source: Source, appearance: Appearance) -> str:
    return (
        f"(No story: {source.phrase} does not make an appearance like {appearance.label}. "
        f"The source gives {sorted(source.emits)}, but the appearance needs {sorted(appearance.receptive)}.)"
    )


def explain_reveal_mismatch(reveal: Reveal, source: Source) -> str:
    if reveal.sense < SENSE_MIN:
        better = ", ".join(sorted(rid for rid, r in REVEALS.items() if r.sense >= SENSE_MIN))
        return (
            f"(Refusing reveal '{reveal.id}': it is too unreasonable for this mystery "
            f"(sense={reveal.sense} < {SENSE_MIN}). Try one of: {better}.)"
        )
    return (
        f"(No story: {reveal.label} would not really test {source.label}. "
        f"The reveal checks {sorted(reveal.checks)}, but the source depends on {sorted(source.emits)}.)"
    )


def introduce(world: World, hero: Entity, partner: Entity, robot: Entity, parent: Entity) -> None:
    world.say(world.setting.opening)
    world.say(world.setting.view)
    world.say(
        f"{hero.id} and {partner.id} were on evening patrol with {robot.id}, "
        f"their round little helper robot, while {hero.id}'s {parent.label_word} checked maps in the next room."
    )


def mission_mood(world: World, hero: Entity, partner: Entity) -> None:
    for kid in (hero, partner):
        kid.memes["joy"] += 1
    world.say(
        f"To the two children, every quiet hallway felt like the start of a space adventure."
    )


def spot_appearance(world: World, hero: Entity, partner: Entity, appearance: Appearance, anomaly: Entity) -> None:
    anomaly.meters["visible"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {partner.id} stopped so fast that {hero.id} almost bumped into {partner.pronoun('object')}. "
        f"There {appearance.location} was {appearance.phrase}."
    )
    world.say(
        f"It had the look of {appearance.looks_like}. {appearance.move_text}"
    )


def mistaken_guess(world: World, hero: Entity, partner: Entity, appearance: Appearance) -> None:
    hero.memes["alarm"] += 1
    world.say(
        f'"Do you see it?" whispered {hero.id}. "That bamboo appearance was not there before."'
    )
    world.say(
        f'"Maybe it\'s growing outside the station," said {partner.id}. '
        f'"Or maybe we are seeing a secret space plant."'
    )
    world.say(
        f"For one breath, the children were mistaken. The strange shape looked so real that it almost felt alive."
    )


def choose_to_investigate(world: World, hero: Entity, partner: Entity, robot: Entity, reveal: Reveal) -> None:
    world.say(
        f"But {robot.id} gave a polite beep, and that helped everyone slow down."
    )
    world.say(
        f'"Let\'s test it before we decide," {hero.id} said. '
        f'"A real mystery to solve needs careful eyes."'
    )
    world.say(
        f"{partner.id} nodded and reached for {reveal.phrase}."
    )


def solve_mystery(world: World, hero: Entity, partner: Entity, source: Entity, reveal: Reveal, source_cfg: Source) -> None:
    source.meters["explained"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} {reveal.action}. {reveal.success}"
    )
    world.say(
        f"Then they saw the true answer: {source_cfg.explain}."
    )
    world.say(source_cfg.proof)


def parent_arrives(world: World, parent: Entity, hero: Entity, partner: Entity, source_cfg: Source) -> None:
    world.say(
        f"{parent.label_word.capitalize()} came over at the sound of their excited voices and smiled."
    )
    world.say(
        f'"Good noticing," {parent.pronoun()} said. "You did not stay frightened. '
        f'You checked the clues, and that is how mysteries get solved."'
    )
    world.say(
        f"{hero.id} pointed at {source_cfg.phrase}, and {partner.id} laughed at the big mistaken guess they had made."
    )


def ending(world: World, hero: Entity, partner: Entity, robot: Entity, appearance: Appearance) -> None:
    hero.memes["bravery"] += 1
    partner.memes["bravery"] += 1
    world.say(
        f"After that, the odd appearance no longer looked spooky. It looked clever."
    )
    world.say(
        f"Soon the children and {robot.id} were back on patrol, with starlight on the windows and a solved mystery behind them."
    )
    world.say(
        f"Whenever a green line flickered again, they grinned first and wondered second."
    )


def tell(
    setting: Setting,
    appearance_cfg: Appearance,
    source_cfg: Source,
    reveal_cfg: Reveal,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    partner_name: str = "Kai",
    partner_gender: str = "boy",
    parent_type: str = "mother",
    hero_trait: str = "curious",
    partner_trait: str = "careful",
    robot_name: str = "Pip",
) -> World:
    world = World(setting=setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            label=hero_name,
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=[partner_trait],
            label=partner_name,
        )
    )
    robot = world.add(
        Entity(
            id=robot_name,
            kind="character",
            type="robot",
            role="robot",
            label=robot_name,
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    anomaly = world.add(
        Entity(
            id="anomaly",
            kind="thing",
            type="appearance",
            label=appearance_cfg.label,
            phrase=appearance_cfg.phrase,
            tags=set(appearance_cfg.tags),
        )
    )
    source = world.add(
        Entity(
            id="source",
            kind="thing",
            type="source",
            label=source_cfg.label,
            phrase=source_cfg.phrase,
            tags=set(source_cfg.tags),
        )
    )

    introduce(world, hero, partner, robot, parent)
    mission_mood(world, hero, partner)

    world.para()
    spot_appearance(world, hero, partner, appearance_cfg, anomaly)
    mistaken_guess(world, hero, partner, appearance_cfg)
    choose_to_investigate(world, hero, partner, robot, reveal_cfg)

    world.para()
    solve_mystery(world, hero, partner, source, reveal_cfg, source_cfg)
    parent_arrives(world, parent, hero, partner, source_cfg)

    world.para()
    ending(world, hero, partner, robot, appearance_cfg)

    world.facts.update(
        hero=hero,
        partner=partner,
        robot=robot,
        parent=parent,
        anomaly=anomaly,
        source=source,
        setting=setting,
        appearance=appearance_cfg,
        source_cfg=source_cfg,
        reveal=reveal_cfg,
        solved=source.meters["explained"] >= THRESHOLD,
        mistaken=True,
    )
    return world


KNOWLEDGE = {
    "bamboo": [
        (
            "What is bamboo?",
            "Bamboo is a tall plant with smooth green stalks. Some kinds grow very quickly and look like straight green poles.",
        )
    ],
    "reflection": [
        (
            "What is a reflection?",
            "A reflection is a picture of something bouncing off a shiny surface. It can make an object seem to appear somewhere it is not.",
        )
    ],
    "shadow": [
        (
            "What makes a shadow move?",
            "A shadow moves when the light moves, the object moves, or both. That is why a fan can make leaf shadows wiggle on a wall.",
        )
    ],
    "visor": [
        (
            "What is a visor?",
            "A visor is a curved clear shield on a helmet or rover window. Because it is shiny and curved, it can bounce light in surprising ways.",
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues and test one idea at a time. Good mystery solving means checking carefully instead of guessing too fast.",
        )
    ],
    "space": [
        (
            "Why do space stations need bright lamps for plants?",
            "Plants need light to grow, even in space. Grow lamps help them live where sunlight does not reach them well enough.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "bamboo", "reflection", "shadow", "visor", "space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    setting = f["setting"]
    appearance = f["appearance"]
    return [
        (
            f'Write a short space-adventure story for a 3-to-5-year-old about a mistaken '
            f'bamboo appearance that turns into a mystery to solve. Include the word "{appearance.label.split()[0]}".'
        ),
        (
            f"Tell a gentle mystery where {hero.id} and {partner.id} see a strange green shape in "
            f"{setting.label}, make a mistaken guess, and then solve it by testing the clues."
        ),
        (
            "Write a child-facing story with stars, a station or moon base feeling, and a small mystery "
            "that ends with relief and wonder instead of danger."
        ),
    ]


def pair_noun(hero: Entity, partner: Entity) -> str:
    if hero.type == "girl" and partner.type == "girl":
        return "two young space explorers"
    if hero.type == "boy" and partner.type == "boy":
        return "two young space explorers"
    return "two young space explorers"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    robot = f["robot"]
    parent = f["parent"]
    setting = f["setting"]
    appearance = f["appearance"]
    source_cfg = f["source_cfg"]
    reveal = f["reveal"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, partner)}, {hero.id} and {partner.id}, and their helper robot {robot.id}. "
            f"They are with {hero.id}'s {parent.label_word} in {setting.label}.",
        ),
        (
            "What strange thing did the children notice?",
            f"They noticed {appearance.phrase}. It looked so much like {appearance.looks_like} that it felt like a real mystery.",
        ),
        (
            "Why was their first idea mistaken?",
            f"At first they thought the bamboo-like shape might be some new thing growing or moving outside. "
            f"That guess was mistaken because the shape was only an appearance made by light and a real object inside the habitat.",
        ),
        (
            "How did they solve the mystery?",
            f"They tested the clue instead of only staring at it. {reveal.qa_text} That showed them the pattern depended on the station equipment, not on a strange plant outside.",
        ),
        (
            "What was really causing the bamboo appearance?",
            f"It was not a space plant at all. The true cause was that {source_cfg.explain}.",
        ),
        (
            "How did the story end?",
            f"It ended with relief and wonder. After the mystery was solved, the children felt brave again and went back on patrol with the stars outside.",
        ),
    ]
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mystery", "bamboo", "space"}
    source_cfg = world.facts["source_cfg"]
    if "reflection" in source_cfg.tags:
        tags.add("reflection")
    if "shadow" in source_cfg.tags:
        tags.add("shadow")
    if "dust" in source_cfg.tags:
        tags.add("visor")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orbital_station",
        appearance="dome_bars",
        source="bamboo_reflection",
        reveal="dim_lamps",
        hero="Lina",
        hero_gender="girl",
        partner="Kai",
        partner_gender="boy",
        parent="mother",
        hero_trait="curious",
        partner_trait="careful",
        robot_name="Pip",
    ),
    StoryParams(
        setting="crater_lab",
        appearance="wall_waves",
        source="bamboo_shadow",
        reveal="pause_fan",
        hero="Milo",
        hero_gender="boy",
        partner="Ava",
        partner_gender="girl",
        parent="father",
        hero_trait="brave",
        partner_trait="thoughtful",
        robot_name="Comet",
    ),
    StoryParams(
        setting="moon_base",
        appearance="dust_forest",
        source="visor_glint",
        reveal="cover_visor",
        hero="Nora",
        hero_gender="girl",
        partner="Leo",
        partner_gender="boy",
        parent="mother",
        hero_trait="calm",
        partner_trait="quick",
        robot_name="Blink",
    ),
    StoryParams(
        setting="moon_base",
        appearance="dome_bars",
        source="bamboo_reflection",
        reveal="dim_lamps",
        hero="Tess",
        hero_gender="girl",
        partner="Finn",
        partner_gender="boy",
        parent="father",
        hero_trait="thoughtful",
        partner_trait="curious",
        robot_name="Orbit",
    ),
]


ASP_RULES = r"""
valid(Setting, Appearance, Source, Reveal) :-
    setting(Setting), appearance(Appearance), source(Source), reveal(Reveal),
    hosts(Setting, Source),
    appearance_needs(Appearance, Need),
    source_emits(Source, Need),
    reveal_checks(Reveal, Check),
    source_emits(Source, Check),
    sense(Reveal, S), sense_min(M), S >= M.

sensible(Reveal) :- reveal(Reveal), sense(Reveal, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for source_id in sorted(setting.hosts):
            lines.append(asp.fact("hosts", setting_id, source_id))
    for appearance_id, appearance in APPEARANCES.items():
        lines.append(asp.fact("appearance", appearance_id))
        for need in sorted(appearance.receptive):
            lines.append(asp.fact("appearance_needs", appearance_id, need))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for emit in sorted(source.emits):
            lines.append(asp.fact("source_emits", source_id, emit))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        lines.append(asp.fact("sense", reveal_id, reveal.sense))
        for check in sorted(reveal.checks):
            lines.append(asp.fact("reveal_checks", reveal_id, check))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(rid for (rid,) in asp.atoms(model, "sensible"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space-adventure mystery storyworld with a mistaken bamboo-like appearance."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--appearance", choices=APPEARANCES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.setting and args.source not in SETTINGS[args.setting].hosts:
        raise StoryError(
            f"(No story: {args.source} does not belong in {args.setting}. Pick a source the setting can actually host.)"
        )
    if args.source and args.appearance:
        source = SOURCES[args.source]
        appearance = APPEARANCES[args.appearance]
        if not source_matches_appearance(source, appearance):
            raise StoryError(explain_source_mismatch(source, appearance))
    if args.reveal and args.source:
        reveal = REVEALS[args.reveal]
        source = SOURCES[args.source]
        if not reveal_matches_source(reveal, source):
            raise StoryError(explain_reveal_mismatch(reveal, source))
    if args.reveal and REVEALS[args.reveal].sense < SENSE_MIN:
        raise StoryError(explain_reveal_mismatch(REVEALS[args.reveal], SOURCES.get(args.source, next(iter(SOURCES.values())))))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.appearance is None or combo[1] == args.appearance)
        and (args.source is None or combo[2] == args.source)
        and (args.reveal is None or combo[3] == args.reveal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, appearance_id, source_id, reveal_id = rng.choice(combos)
    hero, hero_gender = _pick_child(rng)
    partner, partner_gender = _pick_child(rng, avoid=hero)
    return StoryParams(
        setting=setting_id,
        appearance=appearance_id,
        source=source_id,
        reveal=reveal_id,
        hero=hero,
        hero_gender=hero_gender,
        partner=partner,
        partner_gender=partner_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        hero_trait=rng.choice(TRAITS),
        partner_trait=rng.choice(TRAITS),
        robot_name=rng.choice(ROBOTS),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.appearance not in APPEARANCES:
        raise StoryError(f"(Unknown appearance: {params.appearance})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.reveal not in REVEALS:
        raise StoryError(f"(Unknown reveal: {params.reveal})")

    setting = SETTINGS[params.setting]
    appearance = APPEARANCES[params.appearance]
    source = SOURCES[params.source]
    reveal = REVEALS[params.reveal]

    if params.source not in setting.hosts:
        raise StoryError(f"(No story: {params.source} is not hosted by {params.setting}.)")
    if not source_matches_appearance(source, appearance):
        raise StoryError(explain_source_mismatch(source, appearance))
    if not reveal_matches_source(reveal, source):
        raise StoryError(explain_reveal_mismatch(reveal, source))

    world = tell(
        setting=setting,
        appearance_cfg=appearance,
        source_cfg=source,
        reveal_cfg=reveal,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        parent_type=params.parent,
        hero_trait=params.hero_trait,
        partner_trait=params.partner_trait,
        robot_name=params.robot_name,
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
    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid combo gate matches ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = sorted(rid for rid, reveal in REVEALS.items() if reveal.sense >= SENSE_MIN)
    clingo_sensible = asp_sensible()
    if python_sensible == clingo_sensible:
        print(f"OK: sensible reveals match ({python_sensible}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible reveals: python={python_sensible} clingo={clingo_sensible}")

    try:
        sample = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
        print("OK: curated generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED on curated sample: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        params.seed = 123
        sample = generate(params)
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        print("OK: default random resolve/generate smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED on default path: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        print(f"sensible reveals: {', '.join(sensible)}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, appearance, source, reveal) combos:\n")
        for setting, appearance, source, reveal in combos:
            print(f"  {setting:16} {appearance:12} {source:18} {reveal}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero} & {p.partner}: {p.appearance} in {p.setting} "
                f"({p.source}, {p.reveal})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
