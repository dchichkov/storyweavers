#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py
===================================================================================

A small storyworld about a child making a secret romantic drawing, losing it in a
mysterious little accident, and solving the mystery with help before the gift is
shared at the end.

The domain is deliberately narrow and state-driven:
- a hero makes a heart-filled drawing for someone special
- a mover (breeze / kitten / puppy) carries it away with a sound effect
- the paper lands in a hiding spot
- a helper follows a clue and solves the mystery
- the drawing is revealed, and the ending is warm and happy

The "romantic" tone stays child-facing: the drawing is a sweet heart picture for
someone special, not an adult romance story.

Run it
------
    python storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py
    python storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py --trace
    python storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4/drawing_romantic_suspense_happy_ending_sound_effects.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    traits: tuple = field(default_factory=tuple)
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    id: str
    label: str
    opening: str
    mystery_detail: str
    affords_movers: set[str] = field(default_factory=set)
    affords_spots: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mover:
    id: str
    label: str
    sound: str
    action: str
    clue: str
    leaves_clue: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Spot:
    id: str
    label: str
    place_text: str
    found_text: str
    reachable: bool = True
    visible_clue: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperCfg:
    id: str
    label: str
    hear_bonus: bool
    style: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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


SCENES = {
    "bedroom": Scene(
        id="bedroom",
        label="bedroom",
        opening="In the late afternoon, the little bedroom glowed pink from the sunset.",
        mystery_detail="A lace curtain hung near the window, and every tiny stir in the room seemed to whisper a secret.",
        affords_movers={"breeze", "kitten"},
        affords_spots={"under_bed", "behind_curtain"},
        tags={"room", "mystery"},
    ),
    "porch": Scene(
        id="porch",
        label="porch",
        opening="At the front porch, flowerpots lined the steps and the evening light made long gold stripes on the boards.",
        mystery_detail="The porch swing creaked softly, and the quiet corners felt like the start of a mystery.",
        affords_movers={"breeze", "puppy"},
        affords_spots={"under_bench", "flowerpot"},
        tags={"porch", "mystery"},
    ),
    "art_corner": Scene(
        id="art_corner",
        label="art corner",
        opening="In the art corner by the hallway, a small lamp shone over paper, crayons, and a jar of ribbons.",
        mystery_detail="Even the shadows under the shelf looked as if they were hiding clues.",
        affords_movers={"breeze", "kitten"},
        affords_spots={"under_bench", "behind_curtain"},
        tags={"art", "mystery"},
    ),
}

MOVERS = {
    "breeze": Mover(
        id="breeze",
        label="breeze",
        sound="whoooosh",
        action="slipped through the open window and lifted the paper in one quick flutter",
        clue="a trail of silver glitter and a corner of paper peeking where the air had pushed it",
        leaves_clue=True,
        tags={"wind", "sound"},
    ),
    "kitten": Mover(
        id="kitten",
        label="kitten",
        sound="patter-patter",
        action="batted the paper with one soft paw and sent it skimming away",
        clue="tiny pawprints and a bent ribbon beside the place it had hidden",
        leaves_clue=True,
        tags={"pet", "sound"},
    ),
    "puppy": Mover(
        id="puppy",
        label="puppy",
        sound="tap-tap-tap",
        action="trotted by too fast, caught the paper in the puff of its run, and nudged it out of sight",
        clue="a wagging tail, scratch marks, and the white edge of paper near the hiding place",
        leaves_clue=True,
        tags={"pet", "sound"},
    ),
}

SPOTS = {
    "under_bed": Spot(
        id="under_bed",
        label="under the bed",
        place_text="slid under the bed into the cool shadow there",
        found_text="flat against a wooden leg under the bed",
        reachable=True,
        visible_clue=True,
        tags={"under", "bed"},
    ),
    "behind_curtain": Spot(
        id="behind_curtain",
        label="behind the curtain",
        place_text="fluttered behind the curtain and went still",
        found_text="caught in the curtain hem, safe and uncrumpled",
        reachable=True,
        visible_clue=True,
        tags={"curtain", "window"},
    ),
    "under_bench": Spot(
        id="under_bench",
        label="under the bench",
        place_text="skated under the little bench by the wall",
        found_text="resting under the bench beside a dropped ribbon",
        reachable=True,
        visible_clue=True,
        tags={"bench"},
    ),
    "flowerpot": Spot(
        id="flowerpot",
        label="behind the flowerpot",
        place_text="tucked itself behind the biggest flowerpot on the porch",
        found_text="standing behind the flowerpot with only one corner showing",
        reachable=True,
        visible_clue=True,
        tags={"flowerpot", "porch"},
    ),
}

HELPERS = {
    "listener": HelperCfg(
        id="listener",
        label="good listener",
        hear_bonus=True,
        style="stopped, listened hard, and trusted even the smallest sound",
        tags={"listening", "mystery"},
    ),
    "tracker": HelperCfg(
        id="tracker",
        label="careful tracker",
        hear_bonus=False,
        style="knelt low and searched for clues the way a tiny detective would",
        tags={"clues", "mystery"},
    ),
    "both": HelperCfg(
        id="both",
        label="careful listener",
        hear_bonus=True,
        style="used both sharp ears and sharp eyes like a real little detective",
        tags={"listening", "clues", "mystery"},
    ),
}


def valid_combo(scene_id: str, mover_id: str, spot_id: str, helper_id: str) -> bool:
    scene = SCENES[scene_id]
    mover = MOVERS[mover_id]
    spot = SPOTS[spot_id]
    helper = HELPERS[helper_id]
    if mover.id not in scene.affords_movers:
        return False
    if spot.id not in scene.affords_spots:
        return False
    if not spot.reachable:
        return False
    if not (spot.visible_clue or mover.leaves_clue or helper.hear_bonus):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for mover_id in MOVERS:
            for spot_id in SPOTS:
                for helper_id in HELPERS:
                    if valid_combo(scene_id, mover_id, spot_id, helper_id):
                        out.append((scene_id, mover_id, spot_id, helper_id))
    return out


def mystery_mode(helper_id: str, mover_id: str, spot_id: str) -> str:
    helper = HELPERS[helper_id]
    mover = MOVERS[mover_id]
    spot = SPOTS[spot_id]
    heard = helper.hear_bonus
    clue = mover.leaves_clue or spot.visible_clue
    if heard and clue:
        return "quick"
    if clue:
        return "clue_first"
    if heard:
        return "sound_first"
    return "stuck"


def explain_rejection(scene_id: str, mover_id: str, spot_id: str, helper_id: str) -> str:
    scene = SCENES[scene_id]
    mover = MOVERS[mover_id]
    spot = SPOTS[spot_id]
    helper = HELPERS[helper_id]
    if mover.id not in scene.affords_movers:
        return f"(No story: a {mover.label} is not a plausible mover in the {scene.label}.)"
    if spot.id not in scene.affords_spots:
        return f"(No story: the {scene.label} does not have a plausible hiding place like {spot.label}.)"
    if not spot.reachable:
        return f"(No story: {spot.label} is not reachable, so the mystery cannot end happily.)"
    if not (spot.visible_clue or mover.leaves_clue or helper.hear_bonus):
        return f"(No story: {helper.label} would have no clue and no sound to follow, so the mystery would stall.)"
    return "(No story: this combination is not reasonable.)"


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    if world.history:
        lines.append(f"  history={world.history}")
    return "\n".join(lines)


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(world.scene.opening)
    world.say(world.scene.mystery_detail)
    world.say(
        f"{hero.id} sat at a little table making a drawing for {helper.id}. "
        f"It was a romantic drawing in the child-sized way {hero.pronoun()} meant it: "
        f"two birds under a moon, a red heart, and tiny silver stars."
    )
    hero.memes["hope"] += 1
    hero.memes["shy"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} wanted it to be a surprise, so {hero.pronoun()} tucked "
        f"one ribbon around the paper and smiled to {hero.pronoun('object')}self."
    )


def vanish(world: World, hero: Entity, mover: Mover, spot: Spot) -> None:
    drawing = world.get("drawing")
    world.para()
    world.say(
        f"Then came a sound: \"{mover.sound}!\" A {mover.label} {mover.action}. "
        f"The drawing {spot.place_text}."
    )
    drawing.meters["missing"] += 1
    hero.memes["fear"] += 1
    hero.memes["wonder"] += 1
    world.history.append("drawing_missing")
    world.say(
        f"{hero.id} blinked. The paper had been right there a moment before, and now it was gone."
    )


def call_helper(world: World, hero: Entity, helper: Entity, helper_cfg: HelperCfg) -> None:
    world.say(
        f'"{helper.id}," whispered {hero.id}, "{helper.pronoun().capitalize()} think something took my drawing."'
    )
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} came close, {helper_cfg.style}. Suddenly the room felt less lonely and more like a mystery to solve."
    )


def search(world: World, hero: Entity, helper: Entity, mover: Mover, spot: Spot, helper_cfg: HelperCfg) -> None:
    heard = helper_cfg.hear_bonus
    clue = mover.leaves_clue or spot.visible_clue
    mode = mystery_mode(helper_cfg.id, mover.id, spot.id)
    world.facts["mode"] = mode
    world.para()
    if heard:
        helper.memes["focus"] += 1
        world.say(
            f'They stood very still. "{mover.sound}..." {helper.id} murmured, hearing the last tiny echo.'
        )
    if clue:
        helper.memes["focus"] += 1
        world.say(
            f"Then {helper.id} noticed {mover.clue}."
        )
    if mode == "quick":
        world.say(
            f"That was enough. Step by step, the two children followed sound and clue toward {spot.label}."
        )
    elif mode == "clue_first":
        world.say(
            f"The clue led them onward, and every careful step made the mystery smaller."
        )
    elif mode == "sound_first":
        world.say(
            f"The sound gave them a direction, and they searched that way until the hiding place came into view."
        )
    else:
        raise StoryError("(No story: the mystery has no solvable trail.)")
    hero.memes["fear"] = 0.0
    hero.memes["hope"] += 1
    world.history.append("search")


def recover(world: World, hero: Entity, helper: Entity, spot: Spot) -> None:
    drawing = world.get("drawing")
    world.para()
    drawing.meters["missing"] = 0.0
    drawing.meters["found"] += 1
    hero.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f'Then {helper.id} gasped softly. "There!" The drawing was {spot.found_text}.'
    )
    world.say(
        f"{hero.id} pulled it out with careful fingers. Not a corner was torn."
    )
    world.history.append("drawing_found")


def reveal(world: World, hero: Entity, helper: Entity) -> None:
    drawing = world.get("drawing")
    world.para()
    hero.memes["shy"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} looked at the moon, the birds, and the bright heart in the middle. "
        f'"Was this for someone special?" {helper.pronoun()} asked.'
    )
    world.say(
        f"{hero.id}'s cheeks turned warm. \"It was for you,\" {hero.pronoun()} said. "
        f"\"I wanted to give you the drawing because you make every day feel kind.\""
    )
    helper.memes["love"] += 1
    hero.memes["love"] += 1
    drawing.meters["given"] += 1
    world.say(
        f"For one tiny second the mystery changed into a sweeter surprise."
    )
    world.history.append("reveal")


def ending(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} hugged the picture to {helper.pronoun('possessive')} chest and smiled so wide that "
        f"even the room seemed brighter. Then {helper.pronoun()} made a place for it where everyone could see the red heart shine."
    )
    world.say(
        f"Outside, something went \"creak\" or \"swish,\" but now it did not sound spooky at all. "
        f"The little mystery had ended happily, and the romantic drawing had found exactly the right home."
    )
    world.history.append("happy_end")


def tell(
    scene: Scene,
    mover: Mover,
    spot: Spot,
    helper_cfg: HelperCfg,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
) -> World:
    if not valid_combo(scene.id, mover.id, spot.id, helper_cfg.id):
        raise StoryError(explain_rejection(scene.id, mover.id, spot.id, helper_cfg.id))

    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", label=helper_name))
    world.add(Entity(id="drawing", kind="thing", type="paper", role="gift", label="drawing", phrase="the heart drawing"))
    world.facts.update(
        scene=scene,
        mover=mover,
        spot=spot,
        helper_cfg=helper_cfg,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper)
    vanish(world, hero, mover, spot)
    call_helper(world, hero, helper, helper_cfg)
    search(world, hero, helper, mover, spot, helper_cfg)
    recover(world, hero, helper, spot)
    reveal(world, hero, helper)
    ending(world, hero, helper)

    world.facts.update(
        solved=True,
        heard_sound=helper_cfg.hear_bonus,
        clue_seen=(mover.leaves_clue or spot.visible_clue),
        romantic=True,
    )
    return world


KNOWLEDGE = {
    "drawing": [
        (
            "What is a drawing?",
            "A drawing is a picture someone makes with pencils, crayons, chalk, or markers. People use drawings to show ideas and feelings."
        )
    ],
    "romantic": [
        (
            "What can romantic mean in a child's story?",
            "In a child's story, romantic can mean sweet and full of hearts or kind feelings for someone special. It should stay gentle and age-appropriate."
        )
    ],
    "mystery": [
        (
            "What makes a mystery story feel mysterious?",
            "A mystery feels mysterious when something important goes missing or seems puzzling. Then characters look for clues and solve what happened."
        )
    ],
    "sound": [
        (
            "Why do stories use sound words like whoooosh or tap-tap?",
            "Sound words help readers imagine what a moment feels like. They can make a scene funny, exciting, or a little suspenseful."
        )
    ],
    "breeze": [
        (
            "What can a breeze do to paper?",
            "A breeze can lift light paper and push it across a room or porch. That is why people use paperweights or hold their papers down."
        )
    ],
    "kitten": [
        (
            "Why do kittens bat at paper?",
            "Kittens like to pounce and swat at things that flutter or slide. A moving paper can look like a toy to them."
        )
    ],
    "puppy": [
        (
            "Why can a puppy make a mess by accident?",
            "Puppies move quickly and do not always notice what is in their way. Their paws, noses, and wagging tails can bump light things around."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. It might be a sound, a footprint, or a corner of paper sticking out."
        )
    ],
}

KNOWLEDGE_ORDER = ["drawing", "romantic", "mystery", "sound", "breeze", "kitten", "puppy", "clue"]


@dataclass
class StoryParams:
    scene: str
    mover: str
    spot: str
    helper_style: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Eli", "Finn", "Theo", "Noah"]


CURATED = [
    StoryParams(
        scene="bedroom",
        mover="breeze",
        spot="behind_curtain",
        helper_style="both",
        hero_name="Lily",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
    ),
    StoryParams(
        scene="porch",
        mover="puppy",
        spot="flowerpot",
        helper_style="listener",
        hero_name="Mia",
        hero_gender="girl",
        helper_name="Leo",
        helper_gender="boy",
    ),
    StoryParams(
        scene="art_corner",
        mover="kitten",
        spot="under_bench",
        helper_style="tracker",
        hero_name="Sam",
        hero_gender="boy",
        helper_name="Zoe",
        helper_gender="girl",
    ),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    scene = world.facts["scene"]
    mover = world.facts["mover"]
    return [
        'Write a short child-facing mystery story that includes the words "drawing" and "romantic", uses sound effects, and ends happily.',
        f"Tell a gentle suspense story where {hero.id} makes a romantic drawing for {helper.id}, it vanishes in the {scene.label}, and a small mystery is solved.",
        f'Write a cozy mystery for ages 3 to 5 where a {mover.label} makes a drawing disappear with a sound like "{mover.sound}", but the ending is warm and sweet.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mover = world.facts["mover"]
    spot = world.facts["spot"]
    scene = world.facts["scene"]
    mode = world.facts.get("mode", "quick")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who made a secret drawing, and {helper.id}, who helped solve the mystery. The story follows their search from worry to relief."
        ),
        (
            f"What was {hero.id} making?",
            f"{hero.id} was making a romantic drawing for {helper.id}: a picture with two birds, a moon, and a red heart. It was meant as a sweet surprise for someone special."
        ),
        (
            "Why did the story feel suspenseful?",
            f"The drawing suddenly vanished after a loud little sound from the {mover.label}. That made the room feel full of questions until the children found a clue."
        ),
        (
            f"Where did the drawing go?",
            f"It ended up {spot.label}. The hiding place mattered because it turned an ordinary lost paper into a real mystery."
        ),
        (
            f"How did {helper.id} help solve the mystery?",
            _helper_answer(helper, mover, mode),
        ),
        (
            "How did the story end?",
            f"It ended happily when the drawing was found safe and {hero.id} gave it to {helper.id}. The final smile shows that the scary little mystery became a warm surprise."
        ),
    ]
    if scene.id == "porch":
        qa.append(
            (
                "What sounds were in the story?",
                f'The story used sound effects like "{mover.sound}" and soft porch noises to make the mystery feel real. Those sounds helped the scene feel suspenseful without becoming too scary.'
            )
        )
    return qa


def _helper_answer(helper: Entity, mover: Mover, mode: str) -> str:
    if mode == "quick":
        return (
            f"{helper.id} listened for the fading sound and noticed the clue left by the {mover.label}. "
            f"Using both hearing and careful looking helped {helper.pronoun('object')} solve the mystery quickly."
        )
    if mode == "clue_first":
        return (
            f"{helper.id} searched carefully until {helper.pronoun()} spotted a clue left by the {mover.label}. "
            f"That clue pointed the way to the hidden drawing."
        )
    if mode == "sound_first":
        return (
            f"{helper.id} trusted the last small sound and followed the direction it came from. "
            f"That was enough to lead to the hiding place."
        )
    return (
        f"{helper.id} kept helping and did not give up. "
        f"Working together made the children brave enough to keep searching."
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mover = world.facts["mover"]
    tags = {"drawing", "romantic", "mystery", "sound", "clue", mover.id}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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


ASP_RULES = r"""
valid(Scene, Mover, Spot, Helper) :-
    scene(Scene), mover(Mover), spot(Spot), helper(Helper),
    affords_mover(Scene, Mover),
    affords_spot(Scene, Spot),
    reachable(Spot),
    (visible_clue(Spot); leaves_clue(Mover); hear_bonus(Helper)).

mode(Helper, Mover, Spot, quick) :-
    helper(Helper), mover(Mover), spot(Spot),
    hear_bonus(Helper), (leaves_clue(Mover); visible_clue(Spot)).
mode(Helper, Mover, Spot, clue_first) :-
    helper(Helper), mover(Mover), spot(Spot),
    not hear_bonus(Helper), (leaves_clue(Mover); visible_clue(Spot)).
mode(Helper, Mover, Spot, sound_first) :-
    helper(Helper), mover(Mover), spot(Spot),
    hear_bonus(Helper), not leaves_clue(Mover), not visible_clue(Spot).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for mover_id in sorted(scene.affords_movers):
            lines.append(asp.fact("affords_mover", scene_id, mover_id))
        for spot_id in sorted(scene.affords_spots):
            lines.append(asp.fact("affords_spot", scene_id, spot_id))
    for mover_id, mover in MOVERS.items():
        lines.append(asp.fact("mover", mover_id))
        if mover.leaves_clue:
            lines.append(asp.fact("leaves_clue", mover_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.reachable:
            lines.append(asp.fact("reachable", spot_id))
        if spot.visible_clue:
            lines.append(asp.fact("visible_clue", spot_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if helper.hear_bonus:
            lines.append(asp.fact("hear_bonus", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_mode(helper_id: str, mover_id: str, spot_id: str) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", helper_id),
            asp.fact("chosen_mover", mover_id),
            asp.fact("chosen_spot", spot_id),
            "selected_mode(M) :- mode(H, Mo, S, M), chosen_helper(H), chosen_mover(Mo), chosen_spot(S).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show selected_mode/1."))
    atoms = asp.atoms(model, "selected_mode")
    return atoms[0][0] if atoms else "stuck"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a missing drawing, a tiny mystery, and a happy reveal."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper-style", choices=HELPERS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.mover and args.spot and args.helper_style:
        if not valid_combo(args.scene, args.mover, args.spot, args.helper_style):
            raise StoryError(explain_rejection(args.scene, args.mover, args.spot, args.helper_style))

    combos = [
        c for c in valid_combos()
        if (args.scene is None or c[0] == args.scene)
        and (args.mover is None or c[1] == args.mover)
        and (args.spot is None or c[2] == args.spot)
        and (args.helper_style is None or c[3] == args.helper_style)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, mover_id, spot_id, helper_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_name = args.helper_name or _pick_name(rng, helper_gender, avoid=hero_name)
    return StoryParams(
        scene=scene_id,
        mover=mover_id,
        spot=spot_id,
        helper_style=helper_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(No story: unknown scene '{params.scene}'.)")
    if params.mover not in MOVERS:
        raise StoryError(f"(No story: unknown mover '{params.mover}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(No story: unknown spot '{params.spot}'.)")
    if params.helper_style not in HELPERS:
        raise StoryError(f"(No story: unknown helper style '{params.helper_style}'.)")

    world = tell(
        scene=SCENES[params.scene],
        mover=MOVERS[params.mover],
        spot=SPOTS[params.spot],
        helper_cfg=HELPERS[params.helper_style],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos parity matches ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases: list[StoryParams] = list(CURATED)
    for s in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        py_mode = mystery_mode(p.helper_style, p.mover, p.spot)
        asp_m = asp_mode(p.helper_style, p.mover, p.spot)
        if py_mode != asp_m:
            bad += 1
    if bad == 0:
        print(f"OK: mystery mode parity matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} mode results differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Verification failed: generated story was empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show mode/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, mover, spot, helper) combos:\n")
        for scene_id, mover_id, spot_id, helper_id in combos:
            print(f"  {scene_id:10} {mover_id:8} {spot_id:15} {helper_id}")
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
            header = f"### {p.hero_name} and {p.helper_name}: {p.mover} in {p.scene}"
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
