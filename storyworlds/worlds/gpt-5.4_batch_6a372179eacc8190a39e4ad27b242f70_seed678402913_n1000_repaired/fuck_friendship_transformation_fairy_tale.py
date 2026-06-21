#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py
=======================================================================

A standalone story world for a fairy-tale domain about friendship, rude words,
and transformation. A child in an enchanted place lets anger jump out as the
word "fuck", and magic changes them into a strange form. A faithful friend does
not run away, but uses the right gentle remedy to bring them back. The world
model tracks the curse, the transformed body's physical limits, and the change
in the two friends' hearts.

The reasonableness gate is narrow on purpose: each transformed form can only be
undone by one kind of remedy, and the helper must actually have the talent to
carry it out. The ASP twin checks the same compatibility relation.

Run it
------
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py --form frog --helper singer --remedy true_name_song
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py --form stone_child --helper singer --remedy warm_broth
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py --qa
    python storyworlds/worlds/gpt-5.4/fuck_friendship_transformation_fairy_tale.py --verify
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
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    scene: str
    task: str
    magic_source: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Form:
    id: str
    label: str
    article: str
    body_effect: str
    burden_text: str
    cure_need: str
    proof_text: str
    hardness: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperKind:
    id: str
    label: str
    phrase: str
    talents: set[str] = field(default_factory=set)
    comfort_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    required_talent: str
    cures_form: str
    act_text: str
    cure_text: str
    lesson_text: str
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


def _r_curse_burden(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["cursed"] < THRESHOLD:
        return []
    sig = ("burden", hero.attrs.get("form", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["shame"] += 1
    hero.memes["fear"] += 1
    friend.memes["worry"] += 1
    friend.memes["loyalty"] += 1
    return []


def _r_form_effect(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["cursed"] < THRESHOLD:
        return []
    form_id = hero.attrs.get("form", "")
    sig = ("form_effect", form_id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if form_id == "frog":
        hero.meters["small"] += 1
        hero.meters["springy"] += 1
        hero.meters["voice_strange"] += 1
    elif form_id == "thornbush":
        hero.meters["rooted"] += 1
        hero.meters["prickly"] += 1
        hero.meters["tangled"] += 1
    elif form_id == "stone_child":
        hero.meters["cold"] += 1
        hero.meters["still"] += 1
        hero.meters["heavy"] += 1
    return []


def _r_true_friendship(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.meters["cured"] < THRESHOLD:
        return []
    sig = ("friendship", "mended")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["joy"] += 1
    friend.memes["love"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="curse_burden", tag="emotional", apply=_r_curse_burden),
    Rule(name="form_effect", tag="physical", apply=_r_form_effect),
    Rule(name="true_friendship", tag="emotional", apply=_r_true_friendship),
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
        for sent in produced:
            world.say(sent)
    return produced


def compatible(form: Form, helper: HelperKind, remedy: Remedy) -> bool:
    return remedy.cures_form == form.id and remedy.required_talent in helper.talents


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for form_id, form in FORMS.items():
        for helper_id, helper in HELPERS.items():
            for remedy_id, remedy in REMEDIES.items():
                if compatible(form, helper, remedy):
                    combos.append((form_id, helper_id, remedy_id))
    return combos


def explain_rejection(form: Form, helper: HelperKind, remedy: Remedy) -> str:
    if remedy.cures_form != form.id:
        return (
            f"(No story: {remedy.label} is the wrong cure for {form.article} {form.label}. "
            f"That form can only be undone by {form.cure_need}.)"
        )
    if remedy.required_talent not in helper.talents:
        return (
            f"(No story: {helper.label} cannot perform {remedy.label}. "
            f"Pick a helper with the needed talent.)"
        )
    return "(No story: this combination does not fit the world.)"


def predict_restoration(world: World, form: Form, helper: HelperKind, remedy: Remedy) -> bool:
    sim = world.copy()
    sim.facts["compatible"] = compatible(form, helper, remedy)
    if sim.facts["compatible"]:
        h = sim.get("hero")
        h.meters["cured"] += 1
        h.meters["cursed"] = 0.0
        propagate(sim, narrate=False)
    return sim.get("hero").meters["cured"] >= THRESHOLD


@dataclass
class StoryParams:
    place: str
    form: str
    helper: str
    remedy: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


PLACES = {
    "moon_glen": Place(
        id="moon_glen",
        label="the Moonlit Glen",
        scene="where blue bells rang whenever the wind brushed them",
        task="carry a basket of star-apples home before dusk",
        magic_source="the listening well in the middle of the glen",
        ending_image="They walked home beneath the silver moon, and even the apples seemed to shine.",
        tags={"enchanted_forest"},
    ),
    "silver_bridge": Place(
        id="silver_bridge",
        label="the Silver Bridge",
        scene="where fish flashed under the planks like pieces of sky",
        task="bring a ribbon bundle across the bridge to the village fair",
        magic_source="the bright river under the bridge",
        ending_image="They crossed the bridge together while lanterns blinked on in the village below.",
        tags={"river"},
    ),
    "willow_garden": Place(
        id="willow_garden",
        label="the Willow Garden",
        scene="where long green branches swept the ground like soft brooms",
        task="gather moon-mint for the old baker before evening",
        magic_source="the whispering willow at the garden gate",
        ending_image="They went out through the willow gate with mint in their pockets and laughter in their sleeves.",
        tags={"garden"},
    ),
}

FORMS = {
    "frog": Form(
        id="frog",
        label="little green frog",
        article="a",
        body_effect="all at once, the child's shoes vanished, tiny webbed feet slapped the stones, and a round frog voice popped out instead of words",
        burden_text="The hero could only bob, blink, and make frightened little croaks.",
        cure_need="a true-name song sung by a loyal friend",
        proof_text="When the last note faded, the frog stretched, shimmered, and stood up as a child again.",
        hardness=1,
        tags={"frog", "transformation"},
    ),
    "thornbush": Form(
        id="thornbush",
        label="thorny rosebush",
        article="a",
        body_effect="in a swirl of green light, arms became twiggy branches and hair turned into curling vines tipped with roses and sharp thorns",
        burden_text="The hero could not walk at all, and every frightened shiver rattled the thorns.",
        cure_need="a ribbon braid tied with patient hands",
        proof_text="The thorns folded like sleeping fingers, the vines unwound, and the child stepped free.",
        hardness=1,
        tags={"thorn", "transformation"},
    ),
    "stone_child": Form(
        id="stone_child",
        label="stone child",
        article="a",
        body_effect="a gray hush ran over skin and clothes until the whole child looked carved from moon-cold rock",
        burden_text="The hero could barely move, and cold silence sat on their shoulders like winter.",
        cure_need="warm broth shared by a steady friend",
        proof_text="Warm color crept back into the stone cheeks, the gray shell cracked, and the child breathed again.",
        hardness=1,
        tags={"stone", "transformation"},
    ),
}

HELPERS = {
    "singer": HelperKind(
        id="singer",
        label="singer",
        phrase="a friend with a clear bell-like voice",
        talents={"song"},
        comfort_text="The friend bent close and promised not to leave, even for one blink of the moon.",
        tags={"song"},
    ),
    "weaver": HelperKind(
        id="weaver",
        label="weaver",
        phrase="a friend whose fingers were always quick with knots and ribbons",
        talents={"weave"},
        comfort_text="The friend spoke softly and kept both hands gentle, as if kindness itself could untangle the spell.",
        tags={"ribbon"},
    ),
    "cook": HelperKind(
        id="cook",
        label="cook",
        phrase="a friend who knew how to warm hungry hearts as well as empty bellies",
        talents={"warmth"},
        comfort_text="The friend tucked close, guarding a little flame of hope the way one guards a candle from the wind.",
        tags={"warmth"},
    ),
    "gifted": HelperKind(
        id="gifted",
        label="gifted friend",
        phrase="a bright friend who could sing a little and weave a little",
        talents={"song", "weave"},
        comfort_text="The friend stayed so near that the spell could not make loneliness grow between them.",
        tags={"song", "ribbon"},
    ),
}

REMEDIES = {
    "true_name_song": Remedy(
        id="true_name_song",
        label="the true-name song",
        required_talent="song",
        cures_form="frog",
        act_text="knelt by the water and sang the hero's true name three times, once for the feet, once for the heart, and once for home",
        cure_text="The music curled around the pond like warm gold thread.",
        lesson_text="A truer word can mend the tear made by a cruel one.",
        tags={"song", "frog"},
    ),
    "ribbon_braid": Remedy(
        id="ribbon_braid",
        label="the ribbon braid",
        required_talent="weave",
        cures_form="thornbush",
        act_text="worked a scarlet ribbon through the branches, slowly and patiently, until every thorn had a place to rest",
        cure_text="The bright ribbon gathered the wild branches into a shape gentle enough for the spell to loosen.",
        lesson_text="Patient hands can answer the hurt made by a sudden mouth.",
        tags={"ribbon", "thorn"},
    ),
    "warm_broth": Remedy(
        id="warm_broth",
        label="the warm broth",
        required_talent="warmth",
        cures_form="stone_child",
        act_text="heated sweet broth with mint and honey, touched the cup to the stone lips, and spoke the old friendly promises that children make when they mean them",
        cure_text="Little threads of steam wound around the cold body and chased the winter out.",
        lesson_text="Shared warmth can soften even a hard magic.",
        tags={"warmth", "stone"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Wren", "Tilda", "May"]
BOY_NAMES = ["Rowan", "Finn", "Otis", "Theo", "Milo", "Robin", "Jules"]
TRAITS = ["kind", "quick", "bright", "gentle", "brave"]


CURATED = [
    StoryParams(
        place="moon_glen",
        form="frog",
        helper="singer",
        remedy="true_name_song",
        hero_name="Rowan",
        hero_gender="boy",
        friend_name="Lina",
        friend_gender="girl",
    ),
    StoryParams(
        place="silver_bridge",
        form="thornbush",
        helper="weaver",
        remedy="ribbon_braid",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
    ),
    StoryParams(
        place="willow_garden",
        form="stone_child",
        helper="cook",
        remedy="warm_broth",
        hero_name="Finn",
        hero_gender="boy",
        friend_name="May",
        friend_gender="girl",
    ),
    StoryParams(
        place="moon_glen",
        form="frog",
        helper="gifted",
        remedy="true_name_song",
        hero_name="Elsie",
        hero_gender="girl",
        friend_name="Robin",
        friend_gender="boy",
    ),
]


def base_traits(rng: random.Random) -> list[str]:
    return ["little", rng.choice(TRAITS)]


def introduce(world: World, place: Place, hero: Entity, friend: Entity, helper: HelperKind) -> None:
    world.say(
        f"In {place.label}, {place.scene}, lived {hero.id} and {friend.id}, two young friends who almost always walked side by side."
    )
    world.say(
        f"{friend.id} was {helper.phrase}, and {hero.id} liked nothing better than sharing work and wonder with {friend.pronoun('object')}."
    )
    world.say(
        f"That evening they had promised to {place.task}."
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1
    friend.memes["loyalty"] += 1


def frustration(world: World, place: Place, hero: Entity, friend: Entity) -> None:
    world.say(
        f"But near {place.magic_source}, the task went crooked. A strap snagged, a basket tipped, and {hero.id} felt hot annoyance rush up faster than a good thought could catch it."
    )
    hero.memes["anger"] += 1
    world.say(
        f'{friend.id} reached out to help, yet in that sharp little moment {hero.id} stamped a foot and cried, "fuck!"'
    )


def transform(world: World, place: Place, hero: Entity, form: Form) -> None:
    hero.meters["cursed"] += 1
    hero.attrs["form"] = form.id
    propagate(world, narrate=False)
    world.say(
        f"The magic of {place.magic_source} did not like cruel speech. It answered at once: {form.body_effect}."
    )
    world.say(form.burden_text)


def friend_stays(world: World, hero: Entity, friend: Entity, helper: HelperKind, form: Form) -> None:
    friend.memes["steady"] += 1
    world.say(
        f"For one startled heartbeat, {friend.id} went pale. Then {helper.comfort_text}"
    )
    if form.id == "frog":
        world.say(
            f'"I know those eyes," {friend.id} whispered. "You are still {hero.id}, even if your voice has gone froggy."'
        )
    elif form.id == "thornbush":
        world.say(
            f'"I know this is you," {friend.id} said, careful not to fear the thorns more than the friend inside them.'
        )
    else:
        world.say(
            f'"I know you are in there," {friend.id} said. "Cold magic is not stronger than friendship."'
        )


def attempt_remedy(world: World, hero: Entity, friend: Entity, form: Form, helper: HelperKind, remedy: Remedy) -> None:
    ok = compatible(form, helper, remedy)
    world.facts["compatible"] = ok
    restored = predict_restoration(world, form, helper, remedy)
    if not ok or not restored:
        raise StoryError(explain_rejection(form, helper, remedy))
    friend.meters["remedy_work"] += 1
    world.say(
        f"So {friend.id} {remedy.act_text}. {remedy.cure_text}"
    )
    hero.meters["cured"] += 1
    hero.meters["cursed"] = 0.0
    hero.meters["small"] = 0.0
    hero.meters["springy"] = 0.0
    hero.meters["voice_strange"] = 0.0
    hero.meters["rooted"] = 0.0
    hero.meters["prickly"] = 0.0
    hero.meters["tangled"] = 0.0
    hero.meters["cold"] = 0.0
    hero.meters["still"] = 0.0
    hero.meters["heavy"] = 0.0
    propagate(world, narrate=False)
    world.say(form.proof_text)


def resolution(world: World, place: Place, hero: Entity, friend: Entity, remedy: Remedy) -> None:
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    world.say(
        f"{hero.id} threw both arms around {friend.id}. \"I am sorry,\" {hero.pronoun()} said. \"I let an ugly word leap out of me.\""
    )
    world.say(
        f'"Then let a better word live there now," {friend.id} answered. "{remedy.lesson_text}"'
    )
    world.say(
        f"Together they set the spilled things right, and this time when the work felt hard, {hero.id} took a breath instead of letting anger speak first."
    )
    world.say(place.ending_image)


def tell(
    place: Place,
    form: Form,
    helper_cfg: HelperKind,
    remedy: Remedy,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            phrase=hero_name,
            role="hero",
            traits=["little", "earnest"],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            label=friend_name,
            phrase=friend_name,
            role="friend",
            traits=["faithful"],
        )
    )
    world.facts.update(
        place=place,
        form=form,
        helper_cfg=helper_cfg,
        remedy=remedy,
        hero=hero,
        friend=friend,
    )

    introduce(world, place, hero, friend, helper_cfg)
    world.para()
    frustration(world, place, hero, friend)
    transform(world, place, hero, form)
    world.para()
    friend_stays(world, hero, friend, helper_cfg, form)
    attempt_remedy(world, hero, friend, form, helper_cfg, remedy)
    world.para()
    resolution(world, place, hero, friend, remedy)
    world.facts["restored"] = hero.meters["cured"] >= THRESHOLD
    return world


KNOWLEDGE = {
    "friendship": [
        (
            "What does a good friend do when something goes wrong?",
            "A good friend tries to help instead of walking away. They stay kind and steady, especially when someone feels ashamed or afraid."
        )
    ],
    "transformation": [
        (
            "What is a transformation in a fairy tale?",
            "A transformation is when magic changes someone into a different shape or form. Fairy tales use it to show a feeling or lesson on the outside."
        )
    ],
    "frog": [
        (
            "Why do fairy tales turn people into frogs?",
            "A frog form is small and awkward, so it shows that a person has lost ease and pride for a while. It also lets the story prove that the person inside is still the same."
        )
    ],
    "thorn": [
        (
            "Why are thorns a good fairy-tale symbol for angry words?",
            "Thorns poke and hurt, just like sharp words can. In a fairy tale, outer thorns can show the hurt that angry speech causes."
        )
    ],
    "stone": [
        (
            "Why is stone used in fairy tales to show sadness or shock?",
            "Stone feels cold, hard, and still. That makes it a strong picture for a heart or body that has gone numb with fear or sorrow."
        )
    ],
    "song": [
        (
            "Why do songs matter in fairy tales?",
            "Songs can hold memory, truth, and names. A true song often reminds magic who someone really is."
        )
    ],
    "ribbon": [
        (
            "What can a ribbon mean in a fairy tale?",
            "A ribbon can mean care, order, and tenderness. Tying something gently together can show that hurt is being mended."
        )
    ],
    "warmth": [
        (
            "Why does warmth often break cold magic?",
            "Warmth stands for life, comfort, and welcome. In fairy tales, shared warmth can push out lonely or frozen spells."
        )
    ],
    "kind_words": [
        (
            "Why do words matter so much in fairy tales?",
            "Fairy tales often treat words like little pieces of magic. A harsh word can wound, and a true kind word can heal."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "friendship",
    "transformation",
    "kind_words",
    "frog",
    "thorn",
    "stone",
    "song",
    "ribbon",
    "warmth",
]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    form = world.facts["form"]
    remedy = world.facts["remedy"]
    place = world.facts["place"]
    return [
        f'Write a fairy tale for young readers where a child says the word "fuck" in anger, is transformed into {form.article} {form.label}, and is saved by friendship.',
        f"Tell a magical friendship story set in {place.label} where {friend.id} stays loyal to {hero.id} after a sudden transformation and uses {remedy.label} to bring {hero.pronoun('object')} back.",
        f"Write a gentle cautionary fairy tale about how one ugly word causes trouble, but a faithful friend and a fitting act of care make things right again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    form = world.facts["form"]
    remedy = world.facts["remedy"]
    place = world.facts["place"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {hero.id} and {friend.id}, in {place.label}. The story follows the trouble that begins when {hero.id} speaks in anger and the loyalty that helps put it right."
        ),
        (
            f"Why was {hero.id} transformed?",
            f"{hero.id} was transformed because {hero.pronoun()} let an ugly angry word jump out beside {place.magic_source}. In this fairy tale, that magic place punishes cruel speech at once."
        ),
        (
            f"What did {hero.id} turn into?",
            f"{hero.pronoun().capitalize()} turned into {form.article} {form.label}. The new form made the problem visible because {form.burden_text.lower()}"
        ),
        (
            f"What did {friend.id} do when the magic happened?",
            f"{friend.id} did not run away. {friend.pronoun().capitalize()} stayed close, recognized the friend inside the strange form, and chose to help instead of leaving {hero.id} alone."
        ),
        (
            f"How was the spell broken?",
            f"The spell was broken when {friend.id} used {remedy.label}. That worked because it was the right cure for {form.article} {form.label}, not just a random kind gesture."
        ),
        (
            "How did the story end?",
            f"It ended with {hero.id} restored and the friendship stronger than before. The ending image shows the change because {hero.id} breathed first when work felt hard, instead of speaking in anger again."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    form = world.facts["form"]
    helper_cfg = world.facts["helper_cfg"]
    remedy = world.facts["remedy"]
    tags = {"friendship", "transformation", "kind_words"} | set(form.tags) | set(helper_cfg.tags) | set(remedy.tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:5}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(Form, Helper, Remedy) :-
    form(Form), helper(Helper), remedy(Remedy),
    cures(Remedy, Form),
    requires(Remedy, Talent),
    has_talent(Helper, Talent).

valid(Form, Helper, Remedy) :- compatible(Form, Helper, Remedy).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for form_id in FORMS:
        lines.append(asp.fact("form", form_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for talent in sorted(helper.talents):
            lines.append(asp.fact("has_talent", helper_id, talent))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("requires", remedy_id, remedy.required_talent))
        lines.append(asp.fact("cures", remedy_id, remedy.cures_form))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fairy-tale story world: a rude word, a transformation, and a faithful friend."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.form and args.helper and args.remedy:
        form = FORMS[args.form]
        helper = HELPERS[args.helper]
        remedy = REMEDIES[args.remedy]
        if not compatible(form, helper, remedy):
            raise StoryError(explain_rejection(form, helper, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.form is None or combo[0] == args.form)
        and (args.helper is None or combo[1] == args.helper)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    form_id, helper_id, remedy_id = rng.choice(sorted(combos))
    place_id = args.place or rng.choice(sorted(PLACES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    return StoryParams(
        place=place_id,
        form=form_id,
        helper=helper_id,
        remedy=remedy_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        form = FORMS[params.form]
        helper = HELPERS[params.helper]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from None
    if not compatible(form, helper, remedy):
        raise StoryError(explain_rejection(form, helper, remedy))

    world = tell(
        place=place,
        form=form,
        helper_cfg=helper,
        remedy=remedy,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = [CURATED[0]]
    try:
        args = build_parser().parse_args([])
        sample_params = resolve_params(args, random.Random(7))
        sample_params.seed = 7
        smoke_cases.append(sample_params)
    except StoryError as err:
        rc = 1
        print("FAILED: resolve_params smoke test:", err)

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated story was empty")
            if not sample.prompts or not sample.story_qa or not sample.world_qa:
                raise StoryError("generated sample missed prompts or QA")
            print(f"OK: smoke story {i} generated ({len(sample.story)} chars).")
        except Exception as err:  # pragma: no cover - defensive for batch verification
            rc = 1
            print(f"FAILED: smoke generation {i}: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (form, helper, remedy) combos:\n")
        for form_id, helper_id, remedy_id in combos:
            print(f"  {form_id:12} {helper_id:8} {remedy_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.form} / {p.helper} / {p.remedy}"
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
