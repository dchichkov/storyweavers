#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py
==================================================================================

A standalone storyworld for a gentle bedtime tale with velvet, transformation,
humor, and a cautionary turn.

Premise
-------
A child finds a magical velvet costume piece in a dress-up basket at bedtime.
A grown-up has one simple rule: costume magic is only for the bedtime play, and
only when a grown-up is there. If the child sneaks it on after lights-out and
whispers the stage word, the child briefly transforms into a silly animal form.
The transformation is funny, but it makes bedtime harder and teaches the child
to ask for help instead of trying secret magic alone.

The world model tracks:
- physical meters: transformed, sleepy, bedtime_delay, mess
- emotional memes: excitement, defiance, worry, relief, trust, lesson

The reasonableness gate prefers only:
- enchanted velvet items
- animal forms the chosen item is actually known to make
- remedies that fit the transformed form

Run it
------
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py --item cape --form kitten
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py --form goldfish
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py --all
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py --qa --json
python storyworlds/worlds/gpt-5.4/velvet_transformation_humor_cautionary_bedtime_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class MagicItem:
    id: str
    label: str
    phrase: str
    velvet_phrase: str
    worn_on: str
    allowed_forms: tuple[str, ...]
    warning: str
    tags: set[str] = field(default_factory=set)
    enchanted: bool = True


@dataclass
class Form:
    id: str
    animal: str
    article: str
    sound: str
    move: str
    trouble: str
    bedtime_problem: str
    favorite_fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sense: int
    works_for: tuple[str, ...]
    action_text: str
    qa_text: str
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


def _r_transformation_trouble(world: World) -> list[str]:
    child = world.entities.get("child")
    room = world.entities.get("room")
    if child is None or room is None:
        return []
    if child.meters["transformed"] < THRESHOLD:
        return []
    sig = ("transformation_trouble",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["bedtime_delay"] += 1
    room.meters["commotion"] += 1
    child.memes["worry"] += 1
    helper = world.entities.get("helper")
    if helper is not None:
        helper.memes["concern"] += 1
    return ["__transform__"]


CAUSAL_RULES = [
    Rule(name="transformation_trouble", tag="magic", apply=_r_transformation_trouble),
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


ITEMS = {
    "cape": MagicItem(
        id="cape",
        label="cape",
        phrase="a velvet moon-cape",
        velvet_phrase="the soft velvet cape",
        worn_on="shoulders",
        allowed_forms=("bat", "owl"),
        warning="The moon-cape is for our pretend play, and only when a grown-up is with you.",
        tags={"velvet", "cape", "costume"},
        enchanted=True,
    ),
    "bonnet": MagicItem(
        id="bonnet",
        label="bonnet",
        phrase="a velvet star-bonnet",
        velvet_phrase="the little velvet bonnet",
        worn_on="head",
        allowed_forms=("rabbit", "kitten"),
        warning="The star-bonnet is for our pretend play, and only when a grown-up is with you.",
        tags={"velvet", "bonnet", "costume"},
        enchanted=True,
    ),
    "slippers": MagicItem(
        id="slippers",
        label="slippers",
        phrase="a pair of velvet cloud-slippers",
        velvet_phrase="the velvet slippers",
        worn_on="feet",
        allowed_forms=("duck", "kitten"),
        warning="The cloud-slippers are for our pretend play, and only when a grown-up is with you.",
        tags={"velvet", "slippers", "costume"},
        enchanted=True,
    ),
    "ribbon": MagicItem(
        id="ribbon",
        label="ribbon",
        phrase="a velvet ribbon",
        velvet_phrase="the velvet ribbon",
        worn_on="hair",
        allowed_forms=(),
        warning="The ribbon is only a ribbon. It has no bedtime magic at all.",
        tags={"velvet", "ribbon"},
        enchanted=False,
    ),
}

FORMS = {
    "bat": Form(
        id="bat",
        animal="bat",
        article="a tiny bat",
        sound="eep-eeped",
        move="flapped in a wobbling circle",
        trouble="kept trying to hang from the curtain tie",
        bedtime_problem="Bats do not settle nicely under blankets.",
        favorite_fix="warm cocoa and a soft song",
        tags={"bat", "night_animal"},
    ),
    "owl": Form(
        id="owl",
        animal="owl",
        article="a round-eyed owl",
        sound="hoo-hooed",
        move="bobbed on the bedpost",
        trouble="looked serious while knocking the pillow to the floor",
        bedtime_problem="Owls feel far too awake at bedtime.",
        favorite_fix="dim lights and a hush-hush lullaby",
        tags={"owl", "night_animal"},
    ),
    "rabbit": Form(
        id="rabbit",
        animal="rabbit",
        article="a small rabbit",
        sound="sniff-sniffed",
        move="boinged across the rug",
        trouble="nibbled the corner of the bedtime story bookmark",
        bedtime_problem="Rabbits bounce when children ought to be still.",
        favorite_fix="a lap cuddle and three slow breaths",
        tags={"rabbit", "soft_animal"},
    ),
    "kitten": Form(
        id="kitten",
        animal="kitten",
        article="a whiskery kitten",
        sound="mew-mewed",
        move="pounced on the tassel of the blanket",
        trouble="curled up inside the pillowcase instead of on the pillow",
        bedtime_problem="Kittens make bedtime silly instead of sleepy.",
        favorite_fix="gentle brushing and a warm blanket nest",
        tags={"kitten", "soft_animal"},
    ),
    "duck": Form(
        id="duck",
        animal="duck",
        article="a fluffy duck",
        sound="quack-quacked",
        move="waddled across the bedroom very importantly",
        trouble="tried to paddle in the washbasin with one brave foot",
        bedtime_problem="Ducks leave tiny wet footprints where pajamas should go.",
        favorite_fix="a towel rub and a low sleepy hum",
        tags={"duck", "water_animal"},
    ),
    "goldfish": Form(
        id="goldfish",
        animal="goldfish",
        article="a goldfish",
        sound="made silent bubble mouths",
        move="blinked in surprise",
        trouble="had no business being in a bed at all",
        bedtime_problem="A goldfish is not a sensible bedtime shape for a child.",
        favorite_fix="nothing in this room can safely make that happen",
        tags={"goldfish"},
    ),
}

REMEDIES = {
    "lullaby": Remedy(
        id="lullaby",
        label="a lullaby",
        sense=3,
        works_for=("bat", "owl"),
        action_text="wrapped the child in a blanket, dimmed the lamp, and sang a low lullaby until the spell grew drowsy",
        qa_text="sang a low lullaby in the dim room until the spell grew sleepy and let go",
        tags={"lullaby", "bedtime"},
    ),
    "cuddle": Remedy(
        id="cuddle",
        label="a cuddle",
        sense=3,
        works_for=("rabbit",),
        action_text="lifted the little rabbit shape into a lap cuddle and counted three slow breaths together",
        qa_text="gathered the rabbit shape into a lap cuddle and counted three slow breaths",
        tags={"cuddle", "bedtime"},
    ),
    "brush": Remedy(
        id="brush",
        label="a soft brush",
        sense=3,
        works_for=("kitten",),
        action_text="used the soft hairbrush with tiny gentle strokes and tucked a warm blanket around the purring bundle",
        qa_text="brushed the kitten shape gently and tucked it into a warm blanket nest",
        tags={"brush", "bedtime"},
    ),
    "towel": Remedy(
        id="towel",
        label="a fluffy towel",
        sense=2,
        works_for=("duck",),
        action_text="rubbed the duck shape dry with a fluffy towel and hummed until the waddling slowed to a yawn",
        qa_text="rubbed the duck shape dry with a fluffy towel and hummed it back toward sleep",
        tags={"towel", "bedtime"},
    ),
    "scold": Remedy(
        id="scold",
        label="a scolding",
        sense=1,
        works_for=(),
        action_text="crossed both arms and scolded the spell",
        qa_text="scolded loudly",
        tags={"scold"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Nora"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["curious", "bouncy", "dreamy", "mischievous", "sleepy", "eager"]


def valid_combo(item: MagicItem, form: Form, remedy: Remedy) -> bool:
    if not item.enchanted:
        return False
    if form.id not in item.allowed_forms:
        return False
    if remedy.sense < SENSE_MIN:
        return False
    if form.id not in remedy.works_for:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for form_id, form in FORMS.items():
            for remedy_id, remedy in REMEDIES.items():
                if valid_combo(item, form, remedy):
                    combos.append((item_id, form_id, remedy_id))
    return combos


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def predict_trouble(item: MagicItem, form: Form) -> dict:
    world = World()
    child = world.add(Entity(id="child", kind="character", type="girl", role="child"))
    world.add(Entity(id="room", type="room", label="bedroom"))
    world.add(Entity(id="helper", kind="character", type="mother", role="helper"))
    child.meters["transformed"] = 1
    world.facts["item_cfg"] = item
    world.facts["form_cfg"] = form
    propagate(world, narrate=False)
    return {
        "delay": child.meters["bedtime_delay"],
        "commotion": world.get("room").meters["commotion"],
    }


@dataclass
class StoryParams:
    item: str
    form: str
    remedy: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def bedroom_glow() -> str:
    return random.choice(
        [
            "The hallway night-light made a small golden stripe under the door.",
            "Moonlight lay across the blanket like pale milk.",
            "The bedroom lamp was off, and only the quiet night-light glowed.",
        ]
    )


def introduce(world: World, child: Entity, helper: Entity, item: MagicItem) -> None:
    world.say(
        f"{child.id} was a little {child.type} with a {child.attrs.get('trait', 'curious')} heart and eyes that stayed bright even when bedtime had already begun."
    )
    world.say(
        f"On the chair beside the bed sat {item.phrase}, tucked there after a silly family dress-up game."
    )
    world.say(bedroom_glow())


def bedtime_rule(world: World, helper: Entity, item: MagicItem) -> None:
    world.say(
        f'Before the blanket was tucked in, {helper.label_word} had smiled and said, "{item.warning}"'
    )


def temptation(world: World, child: Entity, item: MagicItem) -> None:
    child.memes["excitement"] += 1
    world.say(
        f"But once the room grew quiet, {child.id} kept peeking at {item.velvet_phrase}. Velvet looked much too soft and much too important to ignore."
    )
    world.say(
        f"{child.pronoun().capitalize()} wondered whether wearing it for just one tiny minute could really matter."
    )


def sneak_spell(world: World, child: Entity, item: MagicItem) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"So {child.id} slipped out one foot, reached for {item.velvet_phrase}, and put it on very, very carefully."
    )
    world.say(
        f'Then, because bedtime makes whispers sound bigger than they are, {child.pronoun()} breathed the old stage word: "Twinkle-turn."'
    )


def transform(world: World, child: Entity, form: Form) -> None:
    child.meters["transformed"] += 1
    child.attrs["form"] = form.id
    propagate(world, narrate=False)
    world.say(
        f"At once, the room gave a tiny fizzing shiver. Where {child.id} had been stood {form.article} in rumpled pajamas, wearing a very surprised face."
    )
    world.say(
        f"The little creature {form.sound}, {form.move}, and {form.trouble}."
    )


def call_helper(world: World, child: Entity, helper: Entity, form: Form) -> None:
    child.memes["worry"] += 1
    world.say(
        f'{child.id} tried to say, "{helper.label_word.capitalize()}?" but it came out in {form.animal} noises instead.'
    )
    world.say(
        f'Luckily, the sound was silly enough to wake {helper.label_word}.'
    )


def helper_arrives(world: World, helper: Entity, form: Form) -> None:
    world.say(
        f"{helper.label_word.capitalize()} opened the door, blinked once, and then blinked again at the small {form.animal} in the bedroom."
    )
    world.say(
        f'"Oh," {helper.pronoun()} said, trying not to laugh, "that is exactly why secret bedtime magic is a poor idea."'
    )


def fix_spell(world: World, child: Entity, helper: Entity, remedy: Remedy, form: Form) -> None:
    world.say(
        f"Still, {helper.label_word} did not fuss. {helper.pronoun().capitalize()} {remedy.action_text}."
    )
    child.meters["transformed"] = 0.0
    child.meters["sleepy"] += 1
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    child.memes["lesson"] += 1
    child.attrs["form"] = "child"
    world.say(
        f"Little by little, whiskers or feathers or webby waddles melted away, and {child.id} became {child.pronoun('object')}self again."
    )
    world.say(
        f"{form.bedtime_problem} Now the room felt soft and ordinary once more."
    )


def lesson(world: World, child: Entity, helper: Entity, item: MagicItem) -> None:
    world.say(
        f'{helper.label_word.capitalize()} tucked the blanket back under {child.pronoun("possessive")} chin. "Magic that belongs to family play is not for sneaking," {helper.pronoun()} said gently. "If you are curious, ask me first."'
    )
    world.say(
        f'"I will," whispered {child.id}. {child.pronoun().capitalize()} was embarrassed, but mostly glad to have fingers and toes in the right places again.'
    )
    world.say(
        f"The {item.label} was set on the high shelf for tomorrow, where velvet could stay velvet until morning."
    )


def ending(world: World, child: Entity, helper: Entity, item: MagicItem, form: Form) -> None:
    world.say(
        f"Soon {child.id} gave one real yawn, hugged the pillow instead of pouncing on it, and listened while {helper.label_word} read the next page of the bedtime book."
    )
    world.say(
        f"Outside, the house stayed quiet. Inside, even {item.velvet_phrase} looked sleepy, and no one in the room was trying to be {form.article} anymore."
    )


def tell(
    item: MagicItem,
    form: Form,
    remedy: Remedy,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            label=child_name,
            attrs={"trait": trait, "form": "child"},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
        )
    )
    room = world.add(Entity(id="room", type="room", label="bedroom"))
    prop = world.add(
        Entity(
            id="item",
            type="costume",
            label=item.label,
            phrase=item.phrase,
            tags=set(item.tags),
            attrs={"enchanted": item.enchanted},
        )
    )
    room.meters["quiet"] += 1
    child.memes["trust"] += 1

    introduce(world, child, helper, item)
    bedtime_rule(world, helper, item)

    world.para()
    temptation(world, child, item)
    sneak_spell(world, child, item)
    transform(world, child, form)
    call_helper(world, child, helper, form)

    world.para()
    helper_arrives(world, helper, form)
    fix_spell(world, child, helper, remedy, form)
    lesson(world, child, helper, item)

    world.para()
    ending(world, child, helper, item, form)

    world.facts.update(
        child=child,
        helper=helper,
        room=room,
        item_cfg=item,
        form_cfg=form,
        remedy_cfg=remedy,
        transformed=True,
        fixed=child.meters["transformed"] < THRESHOLD,
        trouble_delay=child.meters["bedtime_delay"],
    )
    return world


CURATED = [
    StoryParams(
        item="bonnet",
        form="kitten",
        remedy="brush",
        child_name="Lily",
        child_gender="girl",
        helper_type="mother",
        trait="curious",
        seed=1,
    ),
    StoryParams(
        item="cape",
        form="owl",
        remedy="lullaby",
        child_name="Ben",
        child_gender="boy",
        helper_type="father",
        trait="eager",
        seed=2,
    ),
    StoryParams(
        item="bonnet",
        form="rabbit",
        remedy="cuddle",
        child_name="Mia",
        child_gender="girl",
        helper_type="grandmother",
        trait="dreamy",
        seed=3,
    ),
    StoryParams(
        item="slippers",
        form="duck",
        remedy="towel",
        child_name="Theo",
        child_gender="boy",
        helper_type="mother",
        trait="mischievous",
        seed=4,
    ),
    StoryParams(
        item="cape",
        form="bat",
        remedy="lullaby",
        child_name="Nora",
        child_gender="girl",
        helper_type="grandfather",
        trait="bouncy",
        seed=5,
    ),
]


def explain_invalid(item: MagicItem, form: Form, remedy: Remedy) -> str:
    if not item.enchanted:
        return (
            f"(No story: {item.phrase} is velvet, but it is not enchanted, so no transformation would happen.)"
        )
    if form.id not in item.allowed_forms:
        allowed = ", ".join(item.allowed_forms) if item.allowed_forms else "none"
        return (
            f"(No story: {item.label} is only known to make {allowed}, not a {form.animal}.)"
        )
    if remedy.sense < SENSE_MIN:
        better = ", ".join(sorted(r.id for r in sensible_remedies()))
        return (
            f"(Refusing remedy '{remedy.id}': it scores too low on common sense for this bedtime world. Try: {better}.)"
        )
    if form.id not in remedy.works_for:
        fits = ", ".join(remedy.works_for) if remedy.works_for else "nothing useful here"
        return (
            f"(No story: {remedy.label} fits {fits}, not a {form.animal} transformation.)"
        )
    return "(No valid story for that combination.)"


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item = world.facts["item_cfg"]
    form = world.facts["form_cfg"]
    helper = world.facts["helper"]
    return [
        f'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "velvet" and features a funny transformation.',
        f"Tell a bedtime story where a {child.type} named {child.id} secretly tries on {item.phrase}, turns into {form.article}, and needs {helper.label_word} to help.",
        "Write a cautionary but cozy story in which secret magic makes bedtime sillier and harder, and the child learns to ask a grown-up first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    item = world.facts["item_cfg"]
    form = world.facts["form_cfg"]
    remedy = world.facts["remedy_cfg"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type} who was supposed to be settling down for bed, and {helper_word}, who came to help. The story begins with a quiet bedtime and a tempting velvet costume piece nearby.",
        ),
        (
            f"What rule did {helper_word} give about the velvet {item.label}?",
            f"{helper_word.capitalize()} said the velvet {item.label} was only for pretend play when a grown-up was there. That rule mattered because the costume magic was not safe for secret bedtime experiments.",
        ),
        (
            f"Why did {child.id} get into trouble?",
            f"{child.id} was too curious and put on the velvet {item.label} after lights-out instead of asking first. Then {child.pronoun()} whispered the stage word and changed into {form.article}.",
        ),
        (
            f"What was funny about the transformation?",
            f"The transformed child {form.sound}, {form.move}, and {form.trouble}. The scene is silly because bedtime became a little animal comedy instead of a calm tuck-in.",
        ),
        (
            f"How did {helper_word} fix the problem?",
            f"{helper_word.capitalize()} {remedy.qa_text}. The fix matched the kind of animal {child.id} had become, so the spell relaxed and let {child.pronoun('object')} turn back.",
        ),
        (
            "What did the child learn?",
            f"{child.id} learned not to sneak family magic at bedtime and to ask a grown-up first. The lesson came after seeing that one secret choice made bedtime noisier, longer, and much harder.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "velvet": [
        (
            "What is velvet?",
            "Velvet is a soft cloth with a fuzzy, smooth surface. It feels gentle when you touch it, which is why it often seems fancy and cozy.",
        )
    ],
    "bedtime": [
        (
            "Why do children have bedtime routines?",
            "Bedtime routines help bodies and brains slow down. Quiet steps like brushing teeth, dim lights, and stories make sleep easier.",
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song sung to help someone feel calm and sleepy. The slow rhythm helps the room feel peaceful.",
        )
    ],
    "cuddle": [
        (
            "Why can a cuddle help someone calm down?",
            "A gentle cuddle can make a child feel safe and steady. When the body feels safe, it is easier to breathe slowly and relax.",
        )
    ],
    "brush": [
        (
            "Why can gentle brushing feel soothing?",
            "Soft, slow brushing can feel regular and calming on the skin or hair. Repeating the same gentle motion often helps a fussy body settle.",
        )
    ],
    "towel": [
        (
            "Why does drying off help after water gets on you?",
            "A dry towel takes water off your skin and clothes. That helps you feel warmer and more comfortable.",
        )
    ],
    "costume": [
        (
            "Why should children ask before using special costume things?",
            "Special costume things may be fragile, important, or meant for grown-up help. Asking first keeps play safer and kinder.",
        )
    ],
    "curiosity": [
        (
            "Is curiosity good?",
            "Yes, curiosity is good because it helps children learn. It works best when children ask safe questions and let grown-ups help.",
        )
    ],
}
KNOWLEDGE_ORDER = ["velvet", "bedtime", "costume", "curiosity", "lullaby", "cuddle", "brush", "towel"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item = world.facts["item_cfg"]
    remedy = world.facts["remedy_cfg"]
    tags = {"velvet", "bedtime", "costume", "curiosity"} | set(remedy.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
enchanted_item(I) :- item(I), enchanted(I).
valid(I, F, R) :- enchanted_item(I), allowed(I, F), remedy(R), sense(R, S), sense_min(M), S >= M, works_for(R, F).

outcome(fixed) :- valid(chosen_item, chosen_form, chosen_remedy).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.enchanted:
            lines.append(asp.fact("enchanted", item_id))
        for form_id in item.allowed_forms:
            lines.append(asp.fact("allowed", item_id, form_id))
    for form_id in FORMS:
        lines.append(asp.fact("form", form_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        for form_id in remedy.works_for:
            lines.append(asp.fact("works_for", remedy_id, form_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test produced incomplete output")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a velvet bedtime costume, a funny transformation, and a gentle cautionary lesson."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--form", choices=FORMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid (item, form, remedy) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None and args.item not in ITEMS:
        raise StoryError(f"(Unknown item: {args.item})")
    if args.form is not None and args.form not in FORMS:
        raise StoryError(f"(Unknown form: {args.form})")
    if args.remedy is not None and args.remedy not in REMEDIES:
        raise StoryError(f"(Unknown remedy: {args.remedy})")

    if args.item and args.form and args.remedy:
        item = ITEMS[args.item]
        form = FORMS[args.form]
        remedy = REMEDIES[args.remedy]
        if not valid_combo(item, form, remedy):
            raise StoryError(explain_invalid(item, form, remedy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.form is None or combo[1] == args.form)
        and (args.remedy is None or combo[2] == args.remedy)
    ]
    if not combos:
        if args.item and args.form and not args.remedy:
            remedy = next(iter(REMEDIES.values()))
            raise StoryError(explain_invalid(ITEMS[args.item], FORMS[args.form], remedy))
        if args.item and args.form:
            raise StoryError(explain_invalid(ITEMS[args.item], FORMS[args.form], REMEDIES["scold"]))
        raise StoryError("(No valid combination matches the given options.)")

    item_id, form_id, remedy_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if child_gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        form=form_id,
        remedy=remedy_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS or params.form not in FORMS or params.remedy not in REMEDIES:
        raise StoryError("(StoryParams refer to unknown registry keys.)")
    item = ITEMS[params.item]
    form = FORMS[params.form]
    remedy = REMEDIES[params.remedy]
    if not valid_combo(item, form, remedy):
        raise StoryError(explain_invalid(item, form, remedy))
    world = tell(
        item=item,
        form=form,
        remedy=remedy,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, form, remedy) combos:\n")
        for item_id, form_id, remedy_id in combos:
            print(f"  {item_id:10} {form_id:8} {remedy_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.item} -> {p.form} ({p.remedy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
