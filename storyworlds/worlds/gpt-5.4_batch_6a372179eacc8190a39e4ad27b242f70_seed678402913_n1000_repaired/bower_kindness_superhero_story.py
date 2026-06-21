#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py
============================================================

A standalone story world for small "Superhero Story" tales where a child learns
that kindness can be the strongest superpower of all. Every story includes a
bower, a clear little problem, a flashy but unhelpful first impulse, and a
state-driven turn toward a kind fix.

The domain is intentionally small and constrained:

* A superhero game happens at one kind of bower scene.
* One problem appears in or near the bower.
* One remedy is chosen.
* The world only allows remedies that actually fit the need.

So the stories do not just swap nouns. The world state tracks worry, courage,
thirst, help, and completion, and the prose follows those changes.

Run it
------
    python storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py
    python storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py --need lantern_string
    python storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py --asp
    python storyworlds/worlds/gpt-5.4/bower_kindness_superhero_story.py --verify
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
# from the repo root or from this nested directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | place | thing | plant
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Scene:
    id: str
    label: str
    opening: str
    bower_desc: str
    festival: str
    closing_image: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    title: str
    subject_kind: str
    subject_label: str
    issue: str
    ask: str
    flashy_fail: str
    relief: str
    completion_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    handles: set[str] = field(default_factory=set)
    act_text: str = ""
    result_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    scene: str
    need: str
    remedy: str
    hero_name: str
    hero_gender: str
    other_name: str
    other_gender: str
    parent: str
    trait: str
    cape_color: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    needer = world.entities.get("needer")
    if hero is None or needer is None:
        return out
    if needer.meters["problem"] < THRESHOLD:
        return out
    sig = ("worry", needer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["concern"] += 1
    needer.memes["hope"] += 1
    out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    needer = world.entities.get("needer")
    bower = world.entities.get("bower")
    if hero is None or needer is None or bower is None:
        return out
    if hero.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness", needer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    needer.meters["problem"] = 0.0
    needer.memes["relief"] += 1
    needer.memes["joy"] += 1
    hero.memes["joy"] += 1
    hero.memes["real_hero"] += 1
    bower.meters["glow"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="social", apply=_r_worry),
    Rule(name="kindness", tag="social", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            result = rule.apply(world)
            if result:
                changed = True
                produced.extend(s for s in result if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def compatible(scene: Scene, need: Need, remedy: Remedy) -> bool:
    return need.id in scene.supports and need.id in remedy.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for need_id, need in NEEDS.items():
            for remedy_id, remedy in REMEDIES.items():
                if compatible(scene, need, remedy):
                    combos.append((scene_id, need_id, remedy_id))
    return combos


def explain_rejection(scene: Scene, need: Need, remedy: Remedy) -> str:
    if need.id not in scene.supports:
        return (
            f"(No story: {scene.label} does not fit the need '{need.id}'. "
            f"This scene supports {', '.join(sorted(scene.supports))}.)"
        )
    return (
        f"(No story: {remedy.label} would not honestly solve '{need.id}'. "
        f"Pick a remedy that actually helps the problem.)"
    )


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_flashy_failure(world: World, need: Need) -> str:
    sim = world.copy()
    needer = sim.get("needer")
    needer.meters["problem"] += 0.0
    return need.flashy_fail


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setup_scene(world: World, hero: Entity, other: Entity, parent: Entity,
                scene: Scene, cape_color: str, trait: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["showiness"] += 1
    other.memes["joy"] += 1
    world.say(
        f"{scene.opening} {hero.id} wore a {cape_color} cape that fluttered behind "
        f"{hero.pronoun('object')}, and {other.id} called {hero.pronoun('object')} "
        f'"Captain Kind."'
    )
    world.say(
        f"Their {parent.label_word} smiled and said that the {scene.bower_desc} "
        f"was the perfect place for a superhero meeting. {hero.id} stood as tall "
        f"as a {trait} little hero and promised to guard {scene.festival}."
    )


def introduce_need(world: World, need: Need) -> None:
    needer = world.get("needer")
    bower = world.get("bower")
    needer.meters["problem"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But under the bower, {need.issue} The bower suddenly felt hushed, as if "
        f"it were waiting to see what kind of hero would answer {needer.label}'s trouble."
    )
    world.say(need.ask)


def flashy_pose(world: World, hero: Entity, need: Need) -> None:
    hero.memes["showiness"] += 1
    world.say(
        f'{hero.id} threw one arm into the air. "Maybe this is a job for a thunder pose '
        f"and super speed!" {hero.pronoun()} said."
    )
    world.say(predict_flashy_failure(world, need))


def kindness_turn(world: World, parent: Entity, hero: Entity, other: Entity) -> None:
    hero.memes["thinking"] += 1
    other.memes["trust"] += 1
    world.say(
        f'{other.id} tugged gently on {hero.pronoun("possessive")} cape. '
        f'"Real heroes notice who needs help," {other.pronoun()} whispered.'
    )
    world.say(
        f"{hero.id}'s {parent.label_word} nodded. "
        f'"The best superpower is kindness used at the right time," {parent.pronoun()} said.'
    )


def do_remedy(world: World, hero: Entity, need: Need, remedy: Remedy) -> None:
    hero.memes["kindness"] += 1
    world.say(remedy.act_text.format(hero=hero.id, subject=need.subject_label))
    propagate(world, narrate=False)
    world.say(remedy.result_text.format(subject=need.subject_label, relief=need.relief))


def ending(world: World, hero: Entity, other: Entity, scene: Scene, need: Need) -> None:
    bower = world.get("bower")
    glow = "glowed" if bower.meters["glow"] >= THRESHOLD else "waited"
    world.say(
        f"Soon the whole bower {glow} with a warmer kind of magic. {need.completion_image}"
    )
    world.say(
        f'{other.id} grinned at {hero.id}. "You really were Captain Kind," '
        f"{other.pronoun()} said."
    )
    world.say(
        f"{hero.id} touched the cape and discovered that it did not feel grandest "
        f"when it was flapping fast. It felt grandest after a kind deed, while "
        f"{scene.closing_image}."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(scene: Scene, need: Need, remedy: Remedy, *, hero_name: str,
         hero_gender: str, other_name: str, other_gender: str, parent_type: str,
         trait: str, cape_color: str) -> World:
    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        attrs={"display": hero_name},
    ))
    other = world.add(Entity(
        id="other",
        kind="character",
        type=other_gender,
        label=other_name,
        phrase=other_name,
        role="friend",
        attrs={"display": other_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    bower = world.add(Entity(
        id="bower",
        kind="place",
        type="bower",
        label="bower",
        phrase=scene.bower_desc,
    ))
    needer = world.add(Entity(
        id="needer",
        kind="thing" if need.subject_kind != "character" else "character",
        type="thing" if need.subject_kind != "character" else "child",
        label=need.subject_label,
        phrase=need.subject_label,
        role="needer",
    ))

    setup_scene(world, hero, other, parent, scene, cape_color, trait)
    world.para()
    introduce_need(world, need)
    flashy_pose(world, hero, need)
    world.para()
    kindness_turn(world, parent, hero, other)
    do_remedy(world, hero, need, remedy)
    world.para()
    ending(world, hero, other, scene, need)

    world.facts.update(
        scene=scene,
        need=need,
        remedy=remedy,
        hero=hero,
        other=other,
        parent=parent,
        bower=bower,
        needer=needer,
        hero_name=hero_name,
        other_name=other_name,
        solved=needer.meters["problem"] < THRESHOLD,
        kindness=hero.memes["kindness"] >= THRESHOLD,
        cape_color=cape_color,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SCENES = {
    "rose_fair": Scene(
        id="rose_fair",
        label="the Rose Fair",
        opening="At the Rose Fair, red petals nodded around a little bower woven with climbing vines.",
        bower_desc="rose bower",
        festival="the fair",
        closing_image="rose shadows made tiny heart-shapes on the path",
        supports={"lantern_string", "shy_guest"},
        tags={"flowers", "bower"},
    ),
    "bean_garden": Scene(
        id="bean_garden",
        label="the Bean Garden",
        opening="In the Bean Garden, a green bower arched over the path like a secret tunnel for heroes.",
        bower_desc="bean-vine bower",
        festival="the garden",
        closing_image="bean leaves rustled like a soft round of applause",
        supports={"drooping_vine", "shy_guest"},
        tags={"garden", "plants", "bower"},
    ),
    "honeysuckle_evening": Scene(
        id="honeysuckle_evening",
        label="the Honeysuckle Evening Walk",
        opening="On the evening walk, a sweet-smelling bower of honeysuckle turned the path into a superhero hideout.",
        bower_desc="honeysuckle bower",
        festival="the walk",
        closing_image="honeysuckle stars of scent drifted in the dusk",
        supports={"lantern_string", "drooping_vine"},
        tags={"garden", "bower"},
    ),
}

NEEDS = {
    "lantern_string": Need(
        id="lantern_string",
        title="a lantern string too high",
        subject_kind="thing",
        subject_label="the paper lantern string",
        issue="a paper lantern string had slipped too high in the branches for small hands to reach.",
        ask='"Oh no," said a little helper nearby. "The bower will look dark for the parade unless someone reaches it."',
        flashy_fail="But a thunder pose could not make careful hands any taller, and super-speed feet would only make the lanterns swing harder.",
        relief="The lanterns stopped wobbling and hung where the path could shine again.",
        completion_image="Soon little lights bobbed safely under the leaves, and everyone could walk beneath them smiling.",
        tags={"lantern", "helping", "bower"},
    ),
    "drooping_vine": Need(
        id="drooping_vine",
        title="a thirsty vine",
        subject_kind="plant",
        subject_label="the drooping vine",
        issue="one young vine in the bower had bent low, its leaves hanging as if they were too tired to wave.",
        ask='"Please look," said the gardener. "This little vine needs gentle help before the afternoon gets hotter."',
        flashy_fail="But a superhero stomp would not bring a thirsty vine a drink, and zooming past would only leave it thirsty for longer.",
        relief="A soft drink reached the roots, and the leaves slowly lifted themselves again.",
        completion_image="Soon the vine was peeking up proudly, as if it wanted to grow into the kindness it had just been given.",
        tags={"plants", "water", "kindness"},
    ),
    "shy_guest": Need(
        id="shy_guest",
        title="a shy guest",
        subject_kind="character",
        subject_label="a shy child",
        issue="a shy child stood at the edge of the bower and would not step in, even though the music game was starting inside.",
        ask='"I want to join," the child whispered, "but it feels dark and twisty in there by myself."',
        flashy_fail="But a loud hero shout would only make the quiet child shrink smaller, and rushing ahead alone would leave the lonely part unchanged.",
        relief="The child took a steady breath and stepped under the leaves with a brave little smile.",
        completion_image="Soon two small shadows walked side by side under the bower, and the music game had room for one more laugh.",
        tags={"feelings", "friendship", "kindness"},
    ),
}

REMEDIES = {
    "stool_share": Remedy(
        id="stool_share",
        label="sharing a stool",
        phrase="share a stool and hold it steady",
        handles={"lantern_string"},
        act_text="{hero} found a small stool, invited another pair of hands close, and held it steady with superhero care while the lantern string was lowered.",
        result_text="{relief}",
        qa_text="shared a small stool and held it steady so the lantern string could be reached safely",
        tags={"sharing", "lantern"},
    ),
    "watering_can": Remedy(
        id="watering_can",
        label="bringing a watering can",
        phrase="bring a watering can and pour slowly",
        handles={"drooping_vine"},
        act_text="{hero} fetched a watering can, knelt beside {subject}, and tipped the water so gently that the soil could drink without washing away.",
        result_text="{relief}",
        qa_text="brought a watering can and poured slowly at the drooping vine's roots",
        tags={"watering", "plants"},
    ),
    "hand_hold": Remedy(
        id="hand_hold",
        label="offering a hand",
        phrase="offer a hand and walk together",
        handles={"shy_guest"},
        act_text="{hero} held out a hand instead of making a noisy speech and asked if they could walk into the bower together, one small step at a time.",
        result_text="{relief}",
        qa_text="offered a hand and walked into the bower together",
        tags={"friendship", "kindness"},
    ),
}

GIRL_NAMES = ["Luna", "Mia", "Zoe", "Ava", "Ivy", "Nora", "Ella", "Ruby"]
BOY_NAMES = ["Max", "Leo", "Theo", "Eli", "Ben", "Sam", "Noah", "Finn"]
TRAITS = ["bright", "gentle", "hopeful", "brave", "thoughtful", "eager"]
CAPE_COLORS = ["red", "blue", "gold", "green", "purple"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bower": [
        (
            "What is a bower?",
            "A bower is a shady little place made by arching branches or climbing plants. It can feel like a tiny green room in a garden.",
        )
    ],
    "lantern": [
        (
            "What is a paper lantern?",
            "A paper lantern is a light cover made of thin paper. People often hang lanterns to make a place look warm and bright.",
        )
    ],
    "plants": [
        (
            "Why do plants droop when they are thirsty?",
            "Plants need water to stay firm and healthy. When they do not have enough, their leaves and stems can bend and droop.",
        )
    ],
    "watering": [
        (
            "Why should you pour water gently on a plant?",
            "Pouring gently helps the water soak into the soil near the roots. It also keeps the soil from splashing away.",
        )
    ],
    "feelings": [
        (
            "How can kindness help someone who feels shy?",
            "Kindness can make a shy person feel safer and less alone. A calm voice or a hand to hold can help courage grow.",
        )
    ],
    "friendship": [
        (
            "What does it mean to be a good friend?",
            "A good friend notices when someone needs help and stays kind. Good friends do not just show off; they help each other feel brave.",
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing lets more people use what is needed. It turns one person's thing into a way for everyone to do better together.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, comfort, or care for someone or something. It is a gentle way of making the world better.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bower", "lantern", "plants", "watering", "feelings", "friendship", "sharing", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    other = f["other"]
    scene = f["scene"]
    need = f["need"]
    remedy = f["remedy"]
    return [
        'Write a short superhero story for a 3-to-5-year-old that includes the word "bower" and shows that kindness is a real superpower.',
        f"Tell a gentle superhero story where {hero.label} starts by wanting to look impressive at {scene.label}, but becomes a true hero by solving {need.title} with {remedy.label}.",
        f"Write a child-facing story about {hero.label} and {other.label} in a {scene.bower_desc} where the big turn is that kindness works better than showing off.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    other = f["other"]
    parent = f["parent"]
    scene = f["scene"]
    need = f["need"]
    remedy = f["remedy"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child pretending to be a superhero, and {other.label}, who helps {hero.pronoun('object')} see what a real hero should do. The story happens at {scene.label}, in and around a bower.",
        ),
        (
            "What problem appeared under the bower?",
            f"Under the bower, {need.issue} That problem changed the game, because someone or something needed gentle help instead of a loud superhero pose.",
        ),
        (
            f"What did {hero.label} think about doing first?",
            f"{hero.label} first imagined using a flashy superhero move. But {need.flashy_fail.lower()}",
        ),
        (
            f"How did {hero.label} solve the problem?",
            f"{hero.label} {remedy.qa_text}. That worked because the fix matched what the trouble really needed, and kindness turned worry into relief.",
        ),
        (
            "What changed at the end?",
            f"By the end, the trouble in the bower was gone and the place felt bright again. {hero.label} also changed, because {hero.pronoun()} learned that being kind made {hero.pronoun('object')} feel more heroic than showing off did.",
        ),
    ]
    if need.id == "shy_guest":
        qa.append(
            (
                "Why was offering a hand better than making a loud speech?",
                "Offering a hand made the shy child feel safe enough to try. A loud speech would have put more attention on the child's fear instead of gently easing it.",
            )
        )
    elif need.id == "drooping_vine":
        qa.append(
            (
                "Why did the vine need gentle help?",
                "The vine was thirsty, so it needed water, not noise or rushing. Gentle care helped the roots drink and the leaves lift again.",
            )
        )
    else:
        qa.append(
            (
                "Why was sharing the stool a kind superhero act?",
                "Sharing the stool turned one child's helper tool into a team effort. It let the lanterns be fixed safely instead of making the problem wobblier.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bower", "kindness"} | set(world.facts["need"].tags) | set(world.facts["remedy"].tags)
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated set for --all
CURATED = [
    StoryParams(
        scene="rose_fair",
        need="lantern_string",
        remedy="stool_share",
        hero_name="Luna",
        hero_gender="girl",
        other_name="Max",
        other_gender="boy",
        parent="mother",
        trait="bright",
        cape_color="gold",
    ),
    StoryParams(
        scene="bean_garden",
        need="drooping_vine",
        remedy="watering_can",
        hero_name="Theo",
        hero_gender="boy",
        other_name="Ivy",
        other_gender="girl",
        parent="father",
        trait="gentle",
        cape_color="green",
    ),
    StoryParams(
        scene="rose_fair",
        need="shy_guest",
        remedy="hand_hold",
        hero_name="Ruby",
        hero_gender="girl",
        other_name="Leo",
        other_gender="boy",
        parent="mother",
        trait="brave",
        cape_color="red",
    ),
    StoryParams(
        scene="honeysuckle_evening",
        need="drooping_vine",
        remedy="watering_can",
        hero_name="Ben",
        hero_gender="boy",
        other_name="Mia",
        other_gender="girl",
        parent="father",
        trait="thoughtful",
        cape_color="blue",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
compatible(N, R) :- handles(R, N).
valid(S, N, R) :- scene(S), need(N), remedy(R), supports(S, N), compatible(N, R).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for need_id in sorted(scene.supports):
            lines.append(asp.fact("supports", scene_id, need_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        for need_id in sorted(remedy.handles):
            lines.append(asp.fact("handles", remedy_id, need_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
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
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero child learns that kindness is a real superpower in a bower."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--other-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--other-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches valid_combos() and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.need and args.remedy:
        scene = SCENES[args.scene]
        need = NEEDS[args.need]
        remedy = REMEDIES[args.remedy]
        if not compatible(scene, need, remedy):
            raise StoryError(explain_rejection(scene, need, remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.need is None or combo[1] == args.need)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        if args.scene and args.need and args.remedy:
            raise StoryError(explain_rejection(SCENES[args.scene], NEEDS[args.need], REMEDIES[args.remedy]))
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, need_id, remedy_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    other_gender = args.other_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    other_name = args.other_name or _pick_name(rng, other_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    cape_color = rng.choice(CAPE_COLORS)
    return StoryParams(
        scene=scene_id,
        need=need_id,
        remedy=remedy_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        other_name=other_name,
        other_gender=other_gender,
        parent=parent,
        trait=trait,
        cape_color=cape_color,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {params.remedy})")

    scene = SCENES[params.scene]
    need = NEEDS[params.need]
    remedy = REMEDIES[params.remedy]
    if not compatible(scene, need, remedy):
        raise StoryError(explain_rejection(scene, need, remedy))

    world = tell(
        scene=scene,
        need=need,
        remedy=remedy,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        other_name=params.other_name,
        other_gender=params.other_gender,
        parent_type=params.parent,
        trait=params.trait,
        cape_color=params.cape_color,
    )

    story_text = world.render()
    story_text = story_text.replace(" hero", " hero")
    story_text = story_text.replace("hero ", "hero ")
    story_text = story_text.replace("hero.", "hero.")
    story_text = story_text.replace("Captain Kind", "Captain Kind")
    story_text = story_text.replace("  ", " ")

    # Replace internal ids with display names in the rendered prose.
    story_text = story_text.replace("hero", params.hero_name)
    story_text = story_text.replace("other", params.other_name)
    story_text = story_text.replace("parent", {"mother": "mom", "father": "dad"}[params.parent])

    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, need, remedy) combos:\n")
        for scene_id, need_id, remedy_id in combos:
            print(f"  {scene_id:20} {need_id:16} {remedy_id}")
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
            header = f"### {p.hero_name}: {p.need} at {p.scene} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
