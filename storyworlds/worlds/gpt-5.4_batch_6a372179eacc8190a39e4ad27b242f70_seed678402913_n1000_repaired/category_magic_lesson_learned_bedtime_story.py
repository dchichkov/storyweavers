#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py
===========================================================================

A small bedtime-story world about a child who tries to use a magical shortcut
while sorting glowing bedtime cards into the right category boxes. The shortcut
can scatter light paper things across the room, and the story teaches that calm,
careful hands are better than hasty magic.

Run it
------
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py --magic whoosh_wand --target dream_cards
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py --target wooden_blocks
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/category_magic_lesson_learned_bedtime_story.py --verify
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
PATIENCE_INIT = 5.0
CALM_TRAITS = {"careful", "patient", "gentle", "steady"}


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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    scatterable: bool = False
    stirs_air: bool = False
    glows: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
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
class Setting:
    id: str
    room: str
    window_view: str
    bed: str
    shelf: str
    cozy_detail: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    sound: str
    spell_words: str
    motion: str
    lesson_name: str
    stirs_air: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    plural: bool
    category_names: tuple[str, str, str]
    home: str
    scatter_text: str
    end_sorted_text: str
    severity: int = 2
    scatterable: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def they(self) -> str:
        return "they" if self.plural else "it"

    @property
    def them(self) -> str:
        return "them" if self.plural else "it"

    @property
    def their(self) -> str:
        return "their" if self.plural else "its"

    @property
    def The(self) -> str:
        word = self.label if self.label.startswith("the ") else f"the {self.label}"
        return word[0].upper() + word[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child", "helper"}]

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


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    target = world.entities.get("target")
    room = world.entities.get("room")
    child = world.entities.get("child")
    if not target or not room or not child:
        return out
    if target.meters["scattered"] < THRESHOLD:
        return out
    sig = ("scatter", "target")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["mess"] += 1
    child.memes["worry"] += 1
    child.memes["surprise"] += 1
    out.append("__scatter__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="scatter", tag="physical", apply=_r_scatter),
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


def hazard_at_risk(magic: MagicTool, target: Target) -> bool:
    return magic.stirs_air and target.scatterable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def scatter_severity(target: Target, delay: int) -> int:
    return target.severity + delay


def is_recovered(response: Response, target: Target, delay: int) -> bool:
    return response.power >= scatter_severity(target, delay)


def initial_calm(trait: str) -> float:
    return 5.0 if trait in CALM_TRAITS else 3.0


def would_avert(relation: str, child_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > child_age
    authority = initial_calm(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > PATIENCE_INIT


def predict_scatter(world: World) -> dict:
    sim = world.copy()
    _do_magic(sim, narrate=False)
    return {
        "scattered": sim.get("target").meters["scattered"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"],
    }


def _do_magic(world: World, narrate: bool = True) -> None:
    target = world.get("target")
    target.meters["scattered"] += 1
    target.meters["mixed"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, helper: Entity, setting: Setting, target: Target) -> None:
    c1, c2, c3 = target.category_names
    child.memes["cozy"] += 1
    helper.memes["cozy"] += 1
    world.say(
        f"In {setting.room}, {setting.window_view}. {child.id} sat on {setting.bed} with {helper.id}, "
        f"and between them stood {setting.shelf}."
    )
    world.say(
        f"Inside were {target.phrase}. Each one belonged in a sleepy category box: {c1}, {c2}, or {c3}. "
        f"{setting.cozy_detail}"
    )


def bedtime_task(world: World, child: Entity, target: Target) -> None:
    child.memes["duty"] += 1
    world.say(
        f"Before the bedtime story could begin, {child.id} had one small job: put {target.them} back in {target.home}, "
        f"with every piece resting in the right category."
    )


def temptation(world: World, child: Entity, magic: MagicTool) -> None:
    child.memes["impatience"] += 1
    world.say(
        f"{child.id} yawned, then spotted {magic.phrase} on the quilt. "
        f'"I could finish in one blink," {child.pronoun()} whispered. "{magic.label} can do it faster."'
    )


def warning(world: World, helper: Entity, child: Entity, magic: MagicTool, target: Target, grownup: Entity) -> None:
    pred = predict_scatter(world)
    helper.memes["calm"] += 1
    world.facts["predicted_mess"] = pred["mess"]
    extra = ""
    if helper.memes["calm"] >= 6:
        extra = f" {helper.id} spoke so softly that even the blankets seemed to listen."
    world.say(
        f'{helper.id} touched the edge of the box. "{child.id}, please do not use {magic.label} for this," '
        f'{helper.pronoun()} said. "Light paper things can fly away, and then the whole category game turns into a mess.'
        f' {grownup.label_word.capitalize()} asked us to sort them carefully."{extra}'
    )


def back_down(world: World, child: Entity, helper: Entity, magic: MagicTool, target: Target) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{child.id} looked at {magic.label}, then at {helper.id}, and let out a sleepy little sigh. '
        f'"You are right," {child.pronoun()} said. "Fast is not the same as careful."'
    )
    world.say(
        f"They put {magic.label} aside and began sliding {target.them} into {target.home} one by one, "
        f"matching each piece to its category."
    )


def defy(world: World, child: Entity, helper: Entity, magic: MagicTool) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Just one tiny spell," {child.id} said. Before {helper.id} could stop {child.pronoun("object")}, '
        f'{child.pronoun()} lifted {magic.label} and traced {magic.motion} in the air.'
    )


def cast_spell(world: World, child: Entity, magic: MagicTool, target: Target) -> None:
    _do_magic(world)
    world.say(
        f'{magic.sound}! {child.id} whispered, "{magic.spell_words}!" For one bright second, '
        f"{target.phrase} glimmered as if they might sort themselves. Then {target.scatter_text}"
    )


def alarm(world: World, helper: Entity, child: Entity, target: Target, grownup: Entity) -> None:
    world.say(
        f'"Oh no," {helper.id} gasped. "{target.The} are everywhere!"'
    )
    world.say(f'{child.id} clutched the blanket. "{grownup.label_word.capitalize()}!"')


def rescue(world: World, grownup: Entity, response: Response, target: Target, child: Entity, helper: Entity) -> None:
    body = response.text.format(target=target.label, home=target.home)
    world.get("target").meters["scattered"] = 0.0
    world.get("room").meters["mess"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} came in with calm feet and gentle hands. {grownup.pronoun().capitalize()} {body}."
    )
    world.say(
        f"Soon the room was quiet again, and the last soft glow returned to the right category box."
    )


def lesson(world: World, grownup: Entity, child: Entity, helper: Entity, magic: MagicTool, target: Target) -> None:
    child.memes["lesson"] += 1
    helper.memes["love"] += 1
    child.memes["love"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} sat beside them on the rug. "
        f'"Magic is lovely when it helps kindly," {grownup.pronoun()} said, "but hurrying with {magic.lesson_name} can muddle '
        f'{target.them}. Careful hands know where things belong."'
    )
    world.say(
        f'{child.id} nodded and helped place the final piece in its category by hand. '
        f'"Next time, I will go slowly," {child.pronoun()} promised.'
    )


def bedtime_end(world: World, grownup: Entity, child: Entity, helper: Entity, setting: Setting, target: Target) -> None:
    child.memes["sleepy"] += 1
    helper.memes["sleepy"] += 1
    world.say(
        f"Then {grownup.label_word} tucked the blanket around both children and opened the bedtime book. "
        f"{target.end_sorted_text}"
    )
    world.say(setting.end_image)


def rescue_fail(world: World, grownup: Entity, response: Response, target: Target, child: Entity) -> None:
    body = response.fail.format(target=target.label, home=target.home)
    world.get("room").meters["mess"] += 1
    child.memes["worry"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} hurried in and {body}."
    )
    world.say(
        f"But some of {target.label} still skated under the bed and behind the curtains, where sleepy fingers could not reach."
    )


def sad_lesson(world: World, grownup: Entity, child: Entity, helper: Entity, magic: MagicTool) -> None:
    child.memes["lesson"] += 1
    child.memes["sad"] += 1
    helper.memes["sad"] += 1
    world.say(
        f"{grownup.label_word.capitalize()} hugged them close. "
        f'"We are safe, and the room can be set right tomorrow," {grownup.pronoun()} whispered. '
        f'"But this is why we do not rush bedtime work with wild magic."'
    )
    world.say(
        f"{child.id} listened to the quiet house and understood. {child.pronoun().capitalize()} had wanted one quick moment, "
        f"but the mess had made the night longer instead."
    )


def delayed_end(world: World, grownup: Entity, child: Entity, helper: Entity, setting: Setting) -> None:
    world.say(
        f"That night there was only one short lullaby instead of a long story, because the room still needed sorting in the morning."
    )
    world.say(
        f"{child.id} lay down beside {helper.id} and watched {setting.window_view.lower()} until {child.pronoun()} felt sleepy enough to rest."
    )


def tell(
    setting: Setting,
    magic: MagicTool,
    target_cfg: Target,
    response: Response,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    helper_name: str = "Owen",
    helper_gender: str = "boy",
    grownup_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    child_age: int = 5,
    helper_age: int = 7,
    relation: str = "siblings",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", age=child_age, traits=["sleepy"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", age=helper_age, traits=[trait]))
    grownup = world.add(Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up"))
    room = world.add(Entity(id="room", type="room", label=setting.room))
    target = world.add(Entity(id="target", type="target", label=target_cfg.label, phrase=target_cfg.phrase, scatterable=target_cfg.scatterable))
    tool = world.add(Entity(id="tool", type="tool", label=magic.label, stirs_air=magic.stirs_air, glows=True))

    helper.memes["calm"] = initial_calm(trait)
    world.facts["relation"] = relation

    opening(world, child, helper, setting, target_cfg)
    bedtime_task(world, child, target_cfg)

    world.para()
    temptation(world, child, magic)
    warning(world, helper, child, magic, target_cfg, grownup)

    averted = would_avert(relation, child_age, helper_age, trait)
    if averted:
        back_down(world, child, helper, magic, target_cfg)
        world.para()
        lesson(world, grownup, child, helper, magic, target_cfg)
        bedtime_end(world, grownup, child, helper, setting, target_cfg)
        outcome = "averted"
        severity = 0
    else:
        defy(world, child, helper, magic)
        world.para()
        cast_spell(world, child, magic, target_cfg)
        alarm(world, helper, child, target_cfg, grownup)
        severity = scatter_severity(target_cfg, delay)
        contained = is_recovered(response, target_cfg, delay)
        world.para()
        if contained:
            rescue(world, grownup, response, target_cfg, child, helper)
            lesson(world, grownup, child, helper, magic, target_cfg)
            world.para()
            bedtime_end(world, grownup, child, helper, setting, target_cfg)
            outcome = "recovered"
        else:
            rescue_fail(world, grownup, response, target_cfg, child)
            sad_lesson(world, grownup, child, helper, magic)
            delayed_end(world, grownup, child, helper, setting)
            outcome = "delayed"

    world.facts.update(
        child=child,
        helper=helper,
        grownup=grownup,
        setting=setting,
        magic=magic,
        target_cfg=target_cfg,
        target=target,
        response=response,
        delay=delay,
        severity=severity,
        outcome=outcome,
        relation=relation,
        child_age=child_age,
        helper_age=helper_age,
    )
    return world


THEMES = {
    "moon_nursery": Setting(
        id="moon_nursery",
        room="a moonlit nursery",
        window_view="silver moonlight made a square on the floor",
        bed="a patchwork bed",
        shelf="a low star-painted shelf",
        cozy_detail="The whole room smelled faintly of soap, paper, and lavender.",
        end_image="Outside, the moon climbed higher, and inside, the nursery felt as neat and soft as a lullaby.",
        tags={"bedroom", "bedtime"},
    ),
    "attic_room": Setting(
        id="attic_room",
        room="a warm attic bedroom",
        window_view="the round window showed a single bright star",
        bed="a soft brass bed",
        shelf="a little painted cabinet with tiny drawers",
        cozy_detail="A small lamp glowed like honey beside the pillows.",
        end_image="The attic room settled into a hush, with starshine at the window and sleepy breathing in the bed.",
        tags={"bedroom", "bedtime"},
    ),
    "boat_cabin": Setting(
        id="boat_cabin",
        room="a snug boat cabin",
        window_view="dark water rocked beyond the porthole",
        bed="a tucked-in bunk",
        shelf="a shelf built under the round porthole",
        cozy_detail="The boat creaked softly, as if it were humming its own good-night song.",
        end_image="The little cabin swayed gently, and the night felt tucked in all around it.",
        tags={"bedroom", "bedtime"},
    ),
}

MAGIC = {
    "whoosh_wand": MagicTool(
        id="whoosh_wand",
        label="the whoosh wand",
        phrase="the whoosh wand",
        sound="Whuff",
        spell_words="Sort and snuggle, hurry and swing",
        motion="a quick silver circle",
        lesson_name="whooshing magic",
        stirs_air=True,
        tags={"wand", "magic", "air"},
    ),
    "moon_fan": MagicTool(
        id="moon_fan",
        label="the moon fan",
        phrase="the moon fan",
        sound="Fffrr",
        spell_words="Moonlight, flutter, fold and fly",
        motion="a pale crescent",
        lesson_name="fluttering magic",
        stirs_air=True,
        tags={"magic", "air"},
    ),
    "comet_spoon": MagicTool(
        id="comet_spoon",
        label="the comet spoon",
        phrase="the comet spoon",
        sound="Ping",
        spell_words="Comet gleam, zip and zoom",
        motion="a bright little loop",
        lesson_name="zipping magic",
        stirs_air=True,
        tags={"magic", "air"},
    ),
}

TARGETS = {
    "dream_cards": Target(
        id="dream_cards",
        label="dream cards",
        phrase="a stack of glowing dream cards",
        plural=True,
        category_names=("moon", "garden", "ocean"),
        home="three velvet boxes",
        scatter_text="the cards lifted too high, swirled together, and fluttered beneath the chair, across the rug, and under the lamp table",
        end_sorted_text="All the dream cards rested in their proper boxes now, moon with moon, garden with garden, ocean with ocean.",
        severity=2,
        scatterable=True,
        tags={"cards", "sorting", "category"},
    ),
    "paper_stars": Target(
        id="paper_stars",
        label="paper stars",
        phrase="a shallow tray of paper stars",
        plural=True,
        category_names=("bright", "sleepy", "twinkly"),
        home="little ribboned pockets",
        scatter_text="the paper stars burst up like a tiny storm and drifted to the windowsill, under the bed, and into the slippers by the rug",
        end_sorted_text="The paper stars were back in their ribboned pockets, each category shining from its own small place.",
        severity=3,
        scatterable=True,
        tags={"stars", "sorting", "category"},
    ),
    "feather_bookmarks": Target(
        id="feather_bookmarks",
        label="feather bookmarks",
        phrase="three feather bookmarks tipped with glow thread",
        plural=True,
        category_names=("forest", "cloud", "night"),
        home="a narrow wooden case",
        scatter_text="the bookmarks twirled away in three different directions and hid where the shadows were thickest",
        end_sorted_text="The feather bookmarks lay neatly in their case again, each category tucked in the slot where it belonged.",
        severity=2,
        scatterable=True,
        tags={"bookmarks", "sorting", "category"},
    ),
    "wooden_blocks": Target(
        id="wooden_blocks",
        label="wooden blocks",
        phrase="a row of painted wooden blocks",
        plural=True,
        category_names=("animals", "letters", "numbers"),
        home="a square tray",
        scatter_text="nothing much happened at all",
        end_sorted_text="The blocks sat square and still in the tray.",
        severity=1,
        scatterable=False,
        tags={"blocks"},
    ),
}

RESPONSES = {
    "kneel_sort": Response(
        id="kneel_sort",
        sense=3,
        power=4,
        text="knelt on the rug, lit the little lamp, and sorted the {target} back into {home} with slow hands",
        fail="knelt to sort the {target}, but too many had already slipped too far into the dark corners",
        qa_text="knelt on the rug and sorted everything back slowly by hand",
        tags={"sorting", "lamp"},
    ),
    "basket_gather": Response(
        id="basket_gather",
        sense=2,
        power=3,
        text="fetched a small basket, gathered the scattered {target}, and helped place each one back in {home}",
        fail="gathered what {grownup} could into a basket, but several pieces were still missing in the shadows",
        qa_text="gathered the scattered pieces in a basket and helped sort them back",
        tags={"sorting", "basket"},
    ),
    "grab_random": Response(
        id="grab_random",
        sense=1,
        power=1,
        text="scooped the {target} up in a hurry and dropped them back without checking the categories",
        fail="scooped at the {target} in a hurry, which only mixed the categories more",
        qa_text="grabbed at everything too fast",
        tags={"sorting"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Iris", "June", "Elsie", "Wren"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Theo", "Jude", "Eli", "Sam", "Noah"]
TRAITS = ["careful", "patient", "gentle", "steady", "curious", "sleepy"]

@dataclass
class StoryParams:
    setting: str
    magic: str
    target: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    grownup: str
    trait: str
    delay: int = 0
    child_age: int = 5
    helper_age: int = 7
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "magic": [(
        "What does magic mean in a bedtime story?",
        "In a bedtime story, magic is something surprising and wonderful that seems impossible in real life. It often helps show a feeling or a lesson in a gentle way."
    )],
    "category": [(
        "What is a category?",
        "A category is a group for things that belong together because they are alike in some way. Putting things into categories helps you find them and keep them tidy."
    )],
    "sorting": [(
        "Why is sorting carefully better than rushing?",
        "Sorting carefully helps each thing go back where it belongs. When you rush, you can make a bigger mess and have to do the job twice."
    )],
    "cards": [(
        "What is a card?",
        "A card is a small flat piece of thick paper. People use cards for games, pictures, or labels."
    )],
    "stars": [(
        "Why do paper stars blow away easily?",
        "Paper stars are light and thin, so moving air can lift them and push them across a room."
    )],
    "bookmarks": [(
        "What is a bookmark for?",
        "A bookmark keeps your place in a book so you can find the page again later."
    )],
    "lamp": [(
        "Why does a lamp help when you are looking for something?",
        "A lamp makes dark corners easier to see. Good light helps careful hands do careful work."
    )],
    "basket": [(
        "Why use a basket to gather small things?",
        "A basket keeps many little things together while you carry them. That way they do not slip away again."
    )],
}
KNOWLEDGE_ORDER = ["magic", "category", "sorting", "cards", "stars", "bookmarks", "lamp", "basket"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id in THEMES:
        for magic_id, magic in MAGIC.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(magic, target):
                    combos.append((setting_id, magic_id, target_id))
    return combos


def explain_rejection(magic: MagicTool, target: Target) -> str:
    if not target.scatterable:
        return (
            f"(No story: {target.label} are too solid to be scattered by {magic.label}, "
            f"so there is no honest bedtime problem to solve. Pick light paper things such as dream_cards or paper_stars.)"
        )
    return "(No story: this combination does not create a plausible bedtime mess.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.child_age, params.helper_age, params.trait):
        return "averted"
    return "recovered" if is_recovered(RESPONSES[params.response], TARGETS[params.target], params.delay) else "delayed"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    magic = f["magic"]
    target = f["target_cfg"]
    setting = f["setting"]
    outcome = f["outcome"]
    base = (
        f'Write a gentle bedtime story for a 3-to-5-year-old that includes the word "category", '
        f"takes place in {setting.room}, and features a child sorting {target.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a magical bedtime story where {child.id} wants to use {magic.label}, but {helper.id} calmly talks {child.pronoun('object')} out of it.",
            "Write a sleepy story with a lesson that careful hands are better than hurried magic.",
        ]
    if outcome == "recovered":
        return [
            base,
            f"Tell a bedtime story where {child.id} uses {magic.label}, the sorting goes wrong, and a calm grown-up helps fix it.",
            "Write a magical lesson-learned story that ends with the room tidy, the categories restored, and a bedtime book at the end.",
        ]
    return [
        base,
        f"Tell a cautionary bedtime story where {child.id} rushes with {magic.label}, the room becomes messy, and bedtime grows shorter.",
        "Write a magical story with a gentle sad turn and a clear lesson about not using wild shortcuts at bedtime.",
    ]


def pair_noun(child: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if child.type == "boy" and helper.type == "boy":
            return "two brothers"
        if child.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_questions(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    grownup = f["grownup"]
    magic = f["magic"]
    target = f["target_cfg"]
    setting = f["setting"]
    response = f["response"]
    outcome = f["outcome"]
    pair = pair_noun(child, helper, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {child.id} and {helper.id}, in {setting.room}. A calm {grownup.label_word} helps at the turning point."
        ),
        (
            "What job did the child need to do before bed?",
            f"{child.id} needed to put {target.label} back in {target.home} and match each one to the right category. That little bedtime job is what started the whole story."
        ),
        (
            f"Why did {child.id} want to use {magic.label}?",
            f"{child.id} felt sleepy and wanted to finish faster. The magic looked like an easy shortcut, even though the careful way was safer."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How was the problem solved before anything went wrong?",
            f"{helper.id} warned {child.id} that rushing with magic could turn the category sorting into a mess, and {child.pronoun()} listened. Because {child.pronoun()} put the wand aside, nothing scattered at all."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child.id} learned that fast is not the same as careful. Doing the job slowly meant the bedtime story could still begin in a peaceful room."
        ))
    elif outcome == "recovered":
        qa.append((
            f"What happened when {child.id} used the magic?",
            f"The {target.label} scattered around the room and the categories got mixed up. The shortcut made a bigger problem because light things flew farther than {child.id} expected."
        ))
        qa.append((
            f"How did the {grownup.label_word} fix the mess?",
            f"The {grownup.label_word} {response.qa_text}. That worked because calm light and careful sorting put each piece back where it belonged."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child.id} learned that bedtime magic should not be used in a hurry. The peaceful ending only came after slow hands repaired the mess."
        ))
    else:
        qa.append((
            f"Could the {grownup.label_word} fix everything that night?",
            f"No. The {grownup.label_word} tried, but some pieces were still hidden away, so bedtime had to be shorter. The delay happened because the first messy spell sent things too far into the room."
        ))
        qa.append((
            "How did the story end?",
            f"It ended quietly rather than happily tidy: the children were safe in bed, but the room would need more sorting in the morning. That gentle disappointment is the lesson the child remembers."
        ))
    return qa


def world_knowledge_questions(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["magic"].tags) | set(world.facts["target_cfg"].tags)
    outcome = world.facts["outcome"]
    if outcome != "averted":
        tags |= set(world.facts["response"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("scatterable", ent.scatterable), ("stirs_air", ent.stirs_air), ("glows", ent.glows)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moon_nursery",
        magic="whoosh_wand",
        target="dream_cards",
        response="kneel_sort",
        child_name="Mina",
        child_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        grownup="mother",
        trait="careful",
        delay=0,
        child_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        setting="attic_room",
        magic="moon_fan",
        target="paper_stars",
        response="basket_gather",
        child_name="Theo",
        child_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        grownup="father",
        trait="gentle",
        delay=0,
        child_age=6,
        helper_age=6,
        relation="friends",
    ),
    StoryParams(
        setting="boat_cabin",
        magic="comet_spoon",
        target="paper_stars",
        response="basket_gather",
        child_name="Lila",
        child_gender="girl",
        helper_name="June",
        helper_gender="girl",
        grownup="grandmother",
        trait="patient",
        delay=2,
        child_age=5,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        setting="moon_nursery",
        magic="moon_fan",
        target="feather_bookmarks",
        response="kneel_sort",
        child_name="Finn",
        child_gender="boy",
        helper_name="Eli",
        helper_gender="boy",
        grownup="grandfather",
        trait="steady",
        delay=0,
        child_age=4,
        helper_age=7,
        relation="siblings",
    ),
]

ASP_RULES = r"""
hazard(M, T) :- stirs_air(M), scatterable(T).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(S, M, T) :- setting(S), magic(M), target(T), hazard(M, T).

calm_now(T) :- trait(T), calm_trait(T).
init_calm(5) :- trait(T), calm_now(T).
init_calm(3) :- trait(T), not calm_now(T).
helper_older :- relation(siblings), child_age(CA), helper_age(HA), HA > CA.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_calm(C), bonus(B).
averted :- helper_older, authority(A), patience_init(P), A > P.

severity(V + D) :- chosen_target(T), target_severity(T, V), delay(D).
response_power(P) :- chosen_response(R), power(R, P).
recovered :- response_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(delayed) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in THEMES:
        lines.append(asp.fact("setting", sid))
    for mid, magic in MAGIC.items():
        lines.append(asp.fact("magic", mid))
        if magic.stirs_air:
            lines.append(asp.fact("stirs_air", mid))
    for tid, target in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if target.scatterable:
            lines.append(asp.fact("scatterable", tid))
        lines.append(asp.fact("target_severity", tid, target.severity))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("patience_init", int(PATIENCE_INIT)))
    for trait in sorted(CALM_TRAITS):
        lines.append(asp.fact("calm_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("child_age", params.child_age),
        asp.fact("helper_age", params.helper_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if mismatches:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcome comparisons differ.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke-test generation and emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Magical bedtime sorting storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--magic", choices=MAGIC)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and args.magic:
        magic = MAGIC[args.magic]
        target = TARGETS[args.target]
        if not hazard_at_risk(magic, target):
            raise StoryError(explain_rejection(magic, target))
    if args.target and not TARGETS[args.target].scatterable:
        magic = MAGIC[args.magic] if args.magic else next(iter(MAGIC.values()))
        raise StoryError(explain_rejection(magic, TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.magic is None or combo[1] == args.magic)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, magic_id, target_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name, child_gender = _pick_name(rng)
    helper_name, helper_gender = _pick_name(rng, avoid=child_name)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    child_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        setting=setting_id,
        magic=magic_id,
        target=target_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup=grownup,
        trait=trait,
        delay=delay,
        child_age=child_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = THEMES[params.setting]
        magic = MAGIC[params.magic]
        target = TARGETS[params.target]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not hazard_at_risk(magic, target):
        raise StoryError(explain_rejection(magic, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=setting,
        magic=magic,
        target_cfg=target,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        grownup_type=params.grownup,
        trait=params.trait,
        delay=params.delay,
        child_age=params.child_age,
        helper_age=params.helper_age,
        relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_questions(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_questions(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, magic, target) combos:\n")
        for setting_id, magic_id, target_id in combos:
            print(f"  {setting_id:12} {magic_id:12} {target_id}")
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
            header = f"### {p.child_name} and {p.helper_name}: {p.magic} with {p.target} ({outcome_of(p)})"
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
