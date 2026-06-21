#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/apparel_sound_effects_reconciliation_kindness_superhero_story.py
=================================================================================================

A standalone storyworld for a tiny superhero-play domain built from the seed:
apparel + sound effects + reconciliation + kindness.

Premise
-------
A child puts on superhero apparel and makes a dramatic entrance with a loud
sound effect. Another child has built a pretend rescue place. The noisy move
causes a small problem: blocks tumble, paper people blow away, or a pet plush is
startled. The superhero child notices the hurt, chooses kindness, helps fix the
mess, and the two children reconcile into one team.

Reasonableness constraint
-------------------------
Not every sound effect fits every piece of apparel or every play scene. This
world only allows combinations where:

* the apparel honestly supports the kind of noisy entrance being narrated,
* the play scene is delicate enough that the entrance could cause a small,
  child-sized problem,
* and the chosen kindness repair actually addresses the problem.

The world also carries a small ASP twin of that same gate and outcome model.

Run it
------
python storyworlds/worlds/gpt-5.4/apparel_sound_effects_reconciliation_kindness_superhero_story.py
python storyworlds/worlds/gpt-5.4/apparel_sound_effects_reconciliation_kindness_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/apparel_sound_effects_reconciliation_kindness_superhero_story.py --qa --json
python storyworlds/worlds/gpt-5.4/apparel_sound_effects_reconciliation_kindness_superhero_story.py --verify
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


@dataclass
class Apparel:
    id: str
    label: str
    phrase: str
    supports: set[str] = field(default_factory=set)
    flair: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Effect:
    id: str
    sound: str
    verb: str
    source: str
    force: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Scene:
    id: str
    label: str
    phrase: str
    fragile: int
    damage: str
    room_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    fixes: set[str] = field(default_factory=set)
    act: str = ""
    result: str = ""
    qa_result: str = ""
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


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("hero")
    friend = world.get("friend")
    scene = world.get("scene")
    if actor.meters["impact"] < THRESHOLD:
        return out
    if scene.meters["damaged"] < THRESHOLD:
        return out
    sig = ("hurt", actor.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["sad"] += 1
    friend.memes["surprised"] += 1
    actor.memes["guilt"] += 1
    out.append("__sad__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    actor = world.get("hero")
    friend = world.get("friend")
    scene = world.get("scene")
    if actor.memes["kindness"] < THRESHOLD:
        return out
    if scene.meters["repaired"] < THRESHOLD:
        return out
    sig = ("reconcile", actor.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    friend.memes["trust"] += 1
    friend.memes["sad"] = 0.0
    actor.memes["relief"] += 1
    actor.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1
    out.append("__reconciled__")
    return out


CAUSAL_RULES = [
    Rule(name="hurt", tag="social", apply=_r_hurt),
    Rule(name="kindness", tag="social", apply=_r_kindness),
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


def valid_combo(apparel: Apparel, effect: Effect, scene: Scene, repair: Repair) -> bool:
    return (
        effect.id in apparel.supports
        and effect.force >= scene.fragile
        and scene.damage in repair.fixes
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for apparel_id, apparel in APPAREL.items():
        for effect_id, effect in EFFECTS.items():
            for scene_id, scene in SCENES.items():
                for repair_id, repair in REPAIRS.items():
                    if valid_combo(apparel, effect, scene, repair):
                        combos.append((apparel_id, effect_id, scene_id, repair_id))
    return combos


def outcome_for(params: "StoryParams") -> str:
    if REPAIRS[params.repair].id:
        return "reconciled"
    return "oops"


def explain_rejection(
    apparel: Optional[Apparel],
    effect: Optional[Effect],
    scene: Optional[Scene],
    repair: Optional[Repair],
) -> str:
    if apparel and effect and effect.id not in apparel.supports:
        return (
            f"(No story: {apparel.phrase} does not honestly support a "
            f'"{effect.sound}" entrance. Pick apparel that fits that sound effect.)'
        )
    if effect and scene and effect.force < scene.fragile:
        return (
            f"(No story: {effect.sound} is too soft to disturb {scene.phrase}, "
            f"so there is no real problem to reconcile.)"
        )
    if scene and repair and scene.damage not in repair.fixes:
        return (
            f"(No story: {repair.act} would not fix a {scene.damage} problem in "
            f"{scene.phrase}. Pick a kindness move that actually repairs the harm.)"
        )
    return "(No valid combination matches the given options.)"


def predict_problem(world: World) -> dict:
    sim = world.copy()
    scene = sim.get("scene")
    hero = sim.get("hero")
    effect = sim.facts["effect"]
    scene_cfg = sim.facts["scene_cfg"]
    hero.meters["impact"] += float(effect.force)
    scene.meters["damaged"] += 1
    scene.attrs["damage_kind"] = scene_cfg.damage
    propagate(sim, narrate=False)
    return {
        "damaged": scene.meters["damaged"] >= THRESHOLD,
        "friend_sad": sim.get("friend").memes["sad"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, apparel: Apparel, friend: Entity, scene: Scene) -> None:
    hero.memes["joy"] += 1
    friend.memes["focus"] += 1
    world.say(
        f"After school, {hero.id} pulled on {apparel.phrase}. {apparel.flair}"
    )
    world.say(
        f"In the middle of the room, {friend.id} was busy with {scene.phrase}. "
        f"{scene.room_line}"
    )


def boast(world: World, hero: Entity, apparel: Apparel, effect: Effect) -> None:
    hero.memes["showoff"] += 1
    world.say(
        f"{hero.id} spread {hero.pronoun('possessive')} arms and whispered, "
        f'"Time for Captain Kind to arrive with a {effect.sound}!"'
    )
    world.say(
        f"The {apparel.label} made {effect.source} feel extra grand, and {hero.pronoun()} "
        f"could almost imagine the whole room becoming a superhero sky."
    )


def noisy_entrance(world: World, hero: Entity, friend: Entity, effect: Effect, scene: Scene) -> None:
    hero.meters["impact"] += float(effect.force)
    scene.meters["damaged"] += 1
    scene.attrs["damage_kind"] = scene.damage
    propagate(world, narrate=False)
    world.say(
        f'{effect.sound}! {hero.id} {effect.verb}.'
    )
    if scene.damage == "blocks":
        world.say(
            f"The rush of motion bumped the edge of {scene.label}, and the front row of blocks tipped over with a clatter."
        )
    elif scene.damage == "papers":
        world.say(
            f"The gust skipped across {scene.label}, and the paper people slid away over the rug."
        )
    else:
        world.say(
            f"The sudden noise startled the little plush perched beside {scene.label}, and it flopped into the middle of the game."
        )
    world.say(
        f"{friend.id} blinked hard. The game did not feel heroic anymore."
    )


def hurt_beat(world: World, hero: Entity, friend: Entity, scene: Scene) -> None:
    pred = predict_problem(world)
    world.facts["predicted_damaged"] = pred["damaged"]
    world.facts["predicted_friend_sad"] = pred["friend_sad"]
    if friend.memes["sad"] >= THRESHOLD:
        world.say(
            f'"Oh," said {hero.id}, suddenly small. {hero.pronoun().capitalize()} saw '
            f"{friend.id}'s face and understood that the big entrance had hurt more than {scene.label}."
        )
    world.say(
        f'"I wanted to sound brave," {hero.id} said, "but I was not being kind."'
    )


def apologize(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["sorry"] += 1
    friend.memes["heard"] += 1
    world.say(
        f'{hero.id} knelt down beside {friend.id}. "I am sorry," {hero.pronoun()} said. '
        f'"I should have checked before making all that noise."'
    )


def repair_scene(world: World, hero: Entity, friend: Entity, scene: Entity, repair: Repair) -> None:
    hero.memes["kindness"] += 1
    scene.meters["repaired"] += 1
    scene.meters["damaged"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.id} {repair.act}."
    )
    world.say(repair.result)
    if friend.memes["trust"] >= THRESHOLD:
        world.say(
            f"{friend.id}'s shoulders loosened. {friend.pronoun().capitalize()} could see that the apology was real because the help was real too."
        )


def reconcile(world: World, hero: Entity, friend: Entity, effect: Effect, scene: Scene) -> None:
    hero.memes["care"] += 1
    friend.memes["forgive"] += 1
    world.say(
        f'"Can we still be a team?" {hero.id} asked.'
    )
    world.say(
        f'{friend.id} nodded. "Yes," {friend.pronoun()} said, "but let the hero sound softer next time."'
    )
    world.say(
        f"So they tried again together: a gentle {effect.sound.lower()} under their breath, a careful step, and then {scene.ending_line}."
    )


def tell(
    apparel: Apparel,
    effect: Effect,
    scene_cfg: Scene,
    repair_cfg: Repair,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    scene = world.add(Entity(id="scene", type="scene", label=scene_cfg.label))
    apparel_ent = world.add(Entity(id="apparel", type="apparel", label=apparel.label, phrase=apparel.phrase))
    world.facts.update(
        apparel=apparel,
        effect=effect,
        scene_cfg=scene_cfg,
        repair=repair_cfg,
        hero=hero,
        friend=friend,
        parent=parent,
        scene=scene,
    )

    introduce(world, hero, apparel, friend, scene_cfg)
    world.para()
    boast(world, hero, apparel, effect)
    noisy_entrance(world, hero, friend, effect, scene_cfg)
    hurt_beat(world, hero, friend, scene_cfg)
    world.para()
    apologize(world, hero, friend)
    repair_scene(world, hero, friend, scene, repair_cfg)
    reconcile(world, hero, friend, effect, scene_cfg)

    world.facts.update(
        damage_kind=scene_cfg.damage,
        reconciled=friend.memes["trust"] >= THRESHOLD and scene.meters["repaired"] >= THRESHOLD,
        outcome="reconciled",
    )
    return world


APPAREL = {
    "cape": Apparel(
        id="cape",
        label="cape",
        phrase="a red superhero apparel set with a cape and bright boots",
        supports={"whoosh", "stomp"},
        flair="The cape swished behind her like a tiny flag, and the boots made her feel taller than the sofa.",
        tags={"apparel", "cape"},
    ),
    "mask": Apparel(
        id="mask",
        label="mask and wrist cuffs",
        phrase="a blue superhero apparel set with a mask and wrist cuffs",
        supports={"zap", "whoosh"},
        flair="The little mask made her eyebrows feel brave, and the cuffs begged for a dramatic pose.",
        tags={"apparel", "mask"},
    ),
    "jacket": Apparel(
        id="jacket",
        label="lightning jacket",
        phrase="a silver superhero apparel jacket with soft elbow pads",
        supports={"zip", "stomp"},
        flair="The shiny jacket flashed in the window light, as if even ordinary cloth had decided to be heroic.",
        tags={"apparel", "jacket"},
    ),
}

EFFECTS = {
    "whoosh": Effect(
        id="whoosh",
        sound="WHOOSH",
        verb="spun past the rug like a flying rescuer",
        source="swooping fabric",
        force=2,
        tags={"sound", "whoosh"},
    ),
    "stomp": Effect(
        id="stomp",
        sound="THUMP THUMP",
        verb="landed in a mighty crouch",
        source="heavy pretend boots",
        force=3,
        tags={"sound", "stomp"},
    ),
    "zap": Effect(
        id="zap",
        sound="ZAP",
        verb="pointed both cuffs and leaped forward",
        source="clicking pretend power bands",
        force=1,
        tags={"sound", "zap"},
    ),
    "zip": Effect(
        id="zip",
        sound="ZIP!",
        verb="raced in a fast silver blur",
        source="slick jacket sleeves",
        force=2,
        tags={"sound", "zip"},
    ),
}

SCENES = {
    "block_city": Scene(
        id="block_city",
        label="the block city",
        phrase="a careful block city with tiny bridges and a paper hospital",
        fragile=2,
        damage="blocks",
        room_line="Every tower had a name, and the tallest one was the rescue tower.",
        ending_line="the rebuilt city stood steady enough for two tiny heroes to patrol",
        tags={"blocks", "city"},
    ),
    "paper_rescue": Scene(
        id="paper_rescue",
        label="the paper rescue camp",
        phrase="a paper rescue camp filled with folded beds and little drawn people",
        fragile=1,
        damage="papers",
        room_line="The paper people were lined up neatly, waiting for a pretend storm drill.",
        ending_line="the paper camp rustled gently while they saved everyone together",
        tags={"paper", "camp"},
    ),
    "plush_clinic": Scene(
        id="plush_clinic",
        label="the plush clinic",
        phrase="a plush-animal clinic made from cushions and a blanket ramp",
        fragile=1,
        damage="plush",
        room_line="A tiny stuffed fox sat on top, ready to be the first patient.",
        ending_line="the plush clinic glowed cozy and calm under the blanket roof",
        tags={"plush", "clinic"},
    ),
}

REPAIRS = {
    "rebuild": Repair(
        id="rebuild",
        fixes={"blocks"},
        act="helped stack each fallen block back into place, one careful piece at a time",
        result="Soon the rescue tower was standing again, straighter than before because four small hands had worked on it together.",
        qa_result="helped rebuild the fallen blocks",
        tags={"kindness", "repair"},
    ),
    "gather": Repair(
        id="gather",
        fixes={"papers"},
        act="chased the paper people, gathered every one of them, and smoothed their bent corners flat",
        result="The little camp looked neat again, and none of the drawn people were left lost on the rug.",
        qa_result="gathered the paper people and smoothed them flat again",
        tags={"kindness", "repair"},
    ),
    "comfort": Repair(
        id="comfort",
        fixes={"plush"},
        act="picked up the stuffed fox, brushed the lint from its ears, and tucked it back safely on its pillow",
        result="The clinic felt gentle again, the way a place for helping should feel.",
        qa_result="picked up the startled plush and tucked it back safely",
        tags={"kindness", "repair"},
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Mia"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Finn", "Jack", "Noah", "Eli"]


@dataclass
class StoryParams:
    apparel: str
    effect: str
    scene: str
    repair: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "apparel": [
        (
            "What does apparel mean?",
            "Apparel means clothing. It is another word for the things people wear, like jackets, capes, boots, or masks.",
        )
    ],
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of cloth that hangs from your shoulders. In pretend play, it can make someone feel like a superhero.",
        )
    ],
    "mask": [
        (
            "What is a mask in dress-up play?",
            "A mask is something you wear on your face. Children use costume masks in pretend games to feel like a new character.",
        )
    ],
    "jacket": [
        (
            "What is a jacket?",
            "A jacket is a piece of clothing you wear on the top half of your body. It can keep you warm and also be part of a costume.",
        )
    ],
    "sound": [
        (
            "What is a sound effect?",
            "A sound effect is a noise used to make a moment feel exciting, like WHOOSH or ZAP. In stories and games, sound effects can make pretend play feel bigger.",
        )
    ],
    "blocks": [
        (
            "Why do block towers fall over easily?",
            "Block towers can fall when something bumps them or shakes the floor. They need careful balance to stay standing.",
        )
    ],
    "paper": [
        (
            "Why can paper things blow away?",
            "Paper is light, so air from a fast movement can push it around. That is why paper crafts need a calm spot.",
        )
    ],
    "plush": [
        (
            "What is a plush toy?",
            "A plush toy is a soft stuffed toy made of cloth and filling. Many children like plush toys because they feel cozy and comforting.",
        )
    ],
    "kindness": [
        (
            "What does kindness look like after a mistake?",
            "Kindness after a mistake means noticing the hurt, saying sorry, and helping fix what went wrong. It is not only words; it is caring action too.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means becoming friendly again after a hurt feeling or disagreement. It often happens when people listen, apologize, and make things better together.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "apparel",
    "cape",
    "mask",
    "jacket",
    "sound",
    "blocks",
    "paper",
    "plush",
    "kindness",
    "reconciliation",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    apparel = f["apparel"]
    effect = f["effect"]
    scene = f["scene_cfg"]
    hero = f["hero"]
    friend = f["friend"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that uses the word "apparel" and includes the sound effect "{effect.sound}".',
        f"Tell a gentle story where {hero.label} wears superhero apparel, makes a noisy entrance near {friend.label}'s {scene.label}, and then chooses kindness to fix the problem.",
        f"Write a reconciliation story in a superhero-play style where a dramatic sound effect leads to hurt feelings, but an apology and helpful action turn the two children into a team again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    apparel = f["apparel"]
    effect = f["effect"]
    scene = f["scene_cfg"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, who put on {apparel.phrase}, and {friend.label}, who was building {scene.phrase}. The story follows how they went from a hurt moment back to being a team.",
        ),
        (
            f"What sound did {hero.label} make?",
            f'{hero.label} made the sound "{effect.sound}" during a big superhero entrance. The sound was part of the pretend play, but it was louder and rougher than the game around {scene.label} needed.',
        ),
        (
            f"What problem happened in the room?",
            f"{hero.label}'s noisy entrance disturbed {scene.label}. That changed the game from exciting to upsetting because {friend.label} had been working carefully on it.",
        ),
        (
            f"Why did {hero.label} say sorry?",
            f"{hero.label} realized the big entrance had hurt {friend.label}'s feelings, not just the play scene. The apology mattered because {hero.pronoun()} understood that sounding brave is not the same as being kind.",
        ),
        (
            "How did the children reconcile?",
            f"{hero.label} apologized and then {repair.qa_result}. That helpful action showed real care, so {friend.label} forgave {hero.pronoun('object')} and they started playing together again.",
        ),
        (
            "How did the story end?",
            f"It ended with a softer kind of heroism: a quieter sound, careful movement, and the repaired game shared by both children. The final picture proves they changed from showy play to kind teamwork.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"apparel", "sound", "kindness", "reconciliation"}
    tags |= set(f["apparel"].tags)
    tags |= set(f["scene_cfg"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        apparel="cape",
        effect="whoosh",
        scene="block_city",
        repair="rebuild",
        hero_name="Maya",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        apparel="mask",
        effect="zap",
        scene="paper_rescue",
        repair="gather",
        hero_name="Zoe",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        apparel="jacket",
        effect="stomp",
        scene="plush_clinic",
        repair="comfort",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        apparel="jacket",
        effect="zip",
        scene="block_city",
        repair="rebuild",
        hero_name="Lucy",
        hero_gender="girl",
        friend_name="Noah",
        friend_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
supports(A, E) :- apparel_support(A, E).
strong_enough(E, S) :- effect(E), scene(S), force(E, F), fragile(S, G), F >= G.
fixes(R, S) :- repair(R), scene(S), scene_damage(S, D), repair_fixes(R, D).

valid(A, E, S, R) :- apparel(A), effect(E), scene(S), repair(R),
                     supports(A, E), strong_enough(E, S), fixes(R, S).

outcome(reconciled) :- chosen_combo(A, E, S, R), valid(A, E, S, R).
:- chosen_combo(A, E, S, R), not valid(A, E, S, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for apparel_id, apparel in APPAREL.items():
        lines.append(asp.fact("apparel", apparel_id))
        for effect_id in sorted(apparel.supports):
            lines.append(asp.fact("apparel_support", apparel_id, effect_id))
    for effect_id, effect in EFFECTS.items():
        lines.append(asp.fact("effect", effect_id))
        lines.append(asp.fact("force", effect_id, effect.force))
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        lines.append(asp.fact("fragile", scene_id, scene.fragile))
        lines.append(asp.fact("scene_damage", scene_id, scene.damage))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for damage in sorted(repair.fixes):
            lines.append(asp.fact("repair_fixes", repair_id, damage))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_combo", params.apparel, params.effect, params.scene, params.repair),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for params in cases:
        if asp_outcome(params) != outcome_for(params):
            rc = 1
            print("MISMATCH in outcome for:", params)
            break
    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: superhero apparel, noisy play, kindness, and reconciliation."
    )
    ap.add_argument("--apparel", choices=APPAREL)
    ap.add_argument("--effect", choices=EFFECTS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    apparel = APPAREL.get(args.apparel) if args.apparel else None
    effect = EFFECTS.get(args.effect) if args.effect else None
    scene = SCENES.get(args.scene) if args.scene else None
    repair = REPAIRS.get(args.repair) if args.repair else None

    if args.apparel and args.effect and effect and apparel and effect.id not in apparel.supports:
        raise StoryError(explain_rejection(apparel, effect, scene, repair))
    if args.effect and args.scene and effect and scene and effect.force < scene.fragile:
        raise StoryError(explain_rejection(apparel, effect, scene, repair))
    if args.scene and args.repair and scene and repair and scene.damage not in repair.fixes:
        raise StoryError(explain_rejection(apparel, effect, scene, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.apparel is None or combo[0] == args.apparel)
        and (args.effect is None or combo[1] == args.effect)
        and (args.scene is None or combo[2] == args.scene)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError(explain_rejection(apparel, effect, scene, repair))

    apparel_id, effect_id, scene_id, repair_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        apparel=apparel_id,
        effect=effect_id,
        scene=scene_id,
        repair=repair_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.apparel not in APPAREL:
        raise StoryError(f"(Unknown apparel: {params.apparel})")
    if params.effect not in EFFECTS:
        raise StoryError(f"(Unknown effect: {params.effect})")
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")

    apparel = APPAREL[params.apparel]
    effect = EFFECTS[params.effect]
    scene = SCENES[params.scene]
    repair = REPAIRS[params.repair]
    if not valid_combo(apparel, effect, scene, repair):
        raise StoryError(explain_rejection(apparel, effect, scene, repair))

    world = tell(
        apparel=apparel,
        effect=effect,
        scene_cfg=scene,
        repair_cfg=repair,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
    )

    story_text = world.render()
    story_text = story_text.replace(" hero ", " ").replace(" friend ", " ")
    story_text = story_text.replace("hero", params.hero_name).replace("friend", params.friend_name)

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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (apparel, effect, scene, repair) combos:\n")
        for apparel_id, effect_id, scene_id, repair_id in combos:
            print(f"  {apparel_id:7} {effect_id:7} {scene_id:12} {repair_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} & {p.friend_name}: {p.apparel}, {p.effect}, {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
