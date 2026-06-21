#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py
====================================================================

A standalone story world for a heartwarming **surprise quest**. A child secretly
tries to mend a loved one's torn pretend-play treasure, follows clue cards around
the house to find the right repair tool, and reveals the fixed gift at the end.

The odd seed word "cut-gerund" appears as a family code word on the first clue
card. The story treats it as a playful nonsense password, not as jargon.

Core reasonableness constraint
------------------------------
Different torn objects need different repairs:

* paper / cardboard -> tape or glue
* cloth             -> fabric glue or needle and thread

A method below the common-sense threshold is known to the world but refused.
Needle-and-thread is allowed, but it always requires a grown-up helper in the
screenplay. The ASP twin mirrors both the compatibility gate and the
help-needed outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py --gift cape --method needle_thread
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py --gift crown --method stapler
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cut_gerund_surprise_quest_heartwarming.py --verify
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "grandmother", "grandma", "woman"}
        male = {"boy", "father", "grandfather", "grandpa", "man"}
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
class QuestTheme:
    id: str
    scene: str
    trail: str
    quest_word: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    material: str
    play_use: str
    reveal_use: str
    break_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    phrase: str
    materials: set[str]
    sense: int
    needs_adult: bool
    repair_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    holds: set[str]
    clue_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    theme: str
    gift: str
    method: str
    hiding_place: str
    helper: str
    recipient_kind: str
    hero_name: str
    hero_gender: str
    recipient_name: str
    recipient_gender: str
    hero_age: int
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


def method_fits(gift: Gift, method: Method) -> bool:
    return gift.material in method.materials


def place_holds(place: HidingPlace, method: Method) -> bool:
    return method.id in place.holds


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for theme_id in QUESTS:
        for gift_id, gift in GIFTS.items():
            for method_id, method in METHODS.items():
                if method.sense < SENSE_MIN or not method_fits(gift, method):
                    continue
                for place_id, place in PLACES.items():
                    if place_holds(place, method):
                        combos.append((theme_id, gift_id, method_id, place_id))
    return combos


def help_needed(method: Method, hero_age: int) -> bool:
    return method.needs_adult or hero_age <= 4


def explain_rejection(gift: Gift, method: Method, place: Optional[HidingPlace] = None) -> str:
    if method.sense < SENSE_MIN:
        better = ", ".join(sorted(m.id for m in sensible_methods()))
        return (
            f"(No story: {method.label} is not a sensible way to mend {gift.label} "
            f"in this world. Try one of: {better}.)"
        )
    if not method_fits(gift, method):
        return (
            f"(No story: {gift.label} is made of {gift.material}, but {method.label} "
            f"does not reasonably mend that material.)"
        )
    if place is not None and not place_holds(place, method):
        return (
            f"(No story: the {place.label} would not be a normal place to find "
            f"{method.label}. Pick a place that could honestly hold the repair tool.)"
        )
    return "(No story: the given options do not make a reasonable repair quest.)"


def introduce(world: World, hero: Entity, recipient: Entity, gift: Gift, theme: QuestTheme) -> None:
    recipient_role = "little sibling" if recipient.attrs.get("relation") == "sibling" else "best friend"
    world.say(
        f"{hero.id} loved making small happy things for {recipient.id}, {hero.pronoun('possessive')} "
        f"{recipient_role}. On that soft afternoon, the house already felt full of "
        f"{theme.scene}."
    )
    world.say(
        f"{recipient.id} had been using {gift.phrase} for {gift.play_use}, but {gift.break_text}."
    )
    world.say(
        f"When {recipient.id} finally curled up for a rest, {hero.id} touched the tear and decided on "
        f"a secret plan. {hero.pronoun().capitalize()} would mend it before {recipient.id} woke up and "
        f"turn the whole errand into {theme.trail}."
    )
    hero.memes["love"] += 1
    hero.memes["resolve"] += 1
    recipient.memes["sad"] += 1
    world.get("gift").meters["torn"] += 1


def start_clue(world: World, hero: Entity, theme: QuestTheme) -> None:
    world.say(
        f"On the table lay the first clue card. In careful pencil it said, "
        f'"For the {theme.quest_word}, begin where neat things wait. Password: cut-gerund."'
    )
    hero.memes["curiosity"] += 1


def search(world: World, hero: Entity, place: HidingPlace, helper: Entity, method: Method) -> None:
    hero.meters["steps"] += 1
    world.say(
        f"{hero.id} padded to {place.phrase}. Behind a stack of towels and a tin of buttons, "
        f"{hero.pronoun()} found a small box with a paper star on top."
    )
    world.say(
        f"The next clue was tucked underneath. It pointed right back to {helper.label_word.capitalize()}, "
        f"who had hidden the box there to make the surprise feel like a real adventure."
    )
    world.say(
        f"Inside waited {method.phrase}. At once, {hero.id} knew the quest had led to the right thing."
    )
    world.facts["password_seen"] = True
    world.facts["found_tool"] = True


def worry(world: World, hero: Entity, recipient: Entity, gift: Gift) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"For one moment, {hero.id} worried the tear in the {gift.label} looked too big. "
        f"If {gift.phrase} stayed broken, {recipient.id}'s game would not feel the same when "
        f"{recipient.pronoun()} woke."
    )


def repair_with_help(world: World, hero: Entity, helper: Entity, recipient: Entity,
                     gift: Gift, method: Method) -> None:
    world.say(
        f"{helper.label_word.capitalize()} sat beside {hero.id} at the kitchen table. "
        f'"You may be the quest leader," {helper.pronoun()} whispered, '
        f'"and I can be your steady hands."'
    )
    world.say(
        f"Together they {method.repair_text.format(gift=gift.label)}. "
        f"{hero.id} held the torn edges close while {helper.label_word} worked slowly enough "
        f"for {hero.pronoun('object')} to see each careful step."
    )
    world.get("gift").meters["torn"] = 0.0
    world.get("gift").meters["mended"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    recipient.memes["sad"] = 0.0
    recipient.memes["joy"] += 1
    world.facts["repair_mode"] = "helped"


def repair_solo(world: World, hero: Entity, gift: Gift, method: Method) -> None:
    world.say(
        f"At the kitchen table, {hero.id} took a deep breath and {method.repair_text.format(gift=gift.label)}."
    )
    world.say(
        f"The torn place stopped gaping. Little by little, the {gift.label} looked ready for play again."
    )
    world.get("gift").meters["torn"] = 0.0
    world.get("gift").meters["mended"] += 1
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.facts["repair_mode"] = "solo"


def reveal(world: World, hero: Entity, recipient: Entity, gift: Gift, theme: QuestTheme) -> None:
    world.say(
        f"Just then, small footsteps whispered down the hall. {recipient.id} blinked into the room, "
        f"still warm from resting, and stopped when {hero.id} held up {gift.phrase}."
    )
    world.say(
        f'"Surprise," {hero.id} said. "{theme.ending_line}"'
    )
    world.say(
        f"{recipient.id}'s whole face opened into a smile. {recipient.pronoun().capitalize()} hugged "
        f"{hero.id}, took the {gift.label} gently, and used it for {gift.reveal_use} as if the afternoon "
        f"had turned bright from the inside."
    )
    hero.memes["love"] += 1
    recipient.memes["love"] += 1
    recipient.memes["joy"] += 1


def ending_image(world: World, hero: Entity, recipient: Entity, theme: QuestTheme) -> None:
    world.say(
        f"Soon the two of them were back in {theme.scene}, and this time the room felt steadier. "
        f"The quest had ended, the surprise had worked, and even the silly password cut-gerund "
        f"made them giggle as they played."
    )


def tell(params: StoryParams) -> World:
    theme = QUESTS[params.theme]
    gift_cfg = GIFTS[params.gift]
    method = METHODS[params.method]
    place = PLACES[params.hiding_place]
    world = World()

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        role="hero",
        attrs={"age": params.hero_age},
    ))
    relation = "sibling" if params.recipient_kind == "sibling" else "friend"
    recipient = world.add(Entity(
        id=params.recipient_name,
        kind="character",
        type=params.recipient_gender,
        role="recipient",
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        role="helper",
        label="the helper",
    ))
    gift = world.add(Entity(
        id="gift",
        type="gift",
        label=gift_cfg.label,
        phrase=gift_cfg.phrase,
        tags=set(gift_cfg.tags),
    ))

    introduce(world, hero, recipient, gift_cfg, theme)
    world.para()
    start_clue(world, hero, theme)
    search(world, hero, place, helper, method)
    worry(world, hero, recipient, gift_cfg)
    world.para()
    if help_needed(method, params.hero_age):
        repair_with_help(world, hero, helper, recipient, gift_cfg, method)
    else:
        repair_solo(world, hero, gift_cfg, method)
        recipient.memes["sad"] = 0.0
        recipient.memes["joy"] += 1
    world.para()
    reveal(world, hero, recipient, gift_cfg, theme)
    ending_image(world, hero, recipient, theme)

    world.facts.update(
        hero=hero,
        recipient=recipient,
        helper=helper,
        theme=theme,
        gift_cfg=gift_cfg,
        method=method,
        place=place,
        help_needed=help_needed(method, params.hero_age),
        repaired=gift.meters["mended"] >= THRESHOLD,
        relation=relation,
    )
    return world


QUESTS = {
    "castle": QuestTheme(
        id="castle",
        scene="castle play",
        trail="a little castle quest",
        quest_word="castle quest",
        ending_line="The royal treasure is ready again.",
        tags={"quest"},
    ),
    "space": QuestTheme(
        id="space",
        scene="spaceship play",
        trail="a tiny moon quest",
        quest_word="moon quest",
        ending_line="Mission repair is complete.",
        tags={"quest"},
    ),
    "garden": QuestTheme(
        id="garden",
        scene="garden picnic play",
        trail="a gentle garden quest",
        quest_word="garden quest",
        ending_line="The picnic treasure is ready again.",
        tags={"quest"},
    ),
}

GIFTS = {
    "crown": Gift(
        id="crown",
        label="paper crown",
        phrase="the shiny paper crown",
        material="paper",
        play_use="being the kind ruler of the sofa castle",
        reveal_use="a proud little parade around the rug",
        break_text="one side had torn where the gold paper bent",
        tags={"paper", "surprise"},
    ),
    "map": Gift(
        id="map",
        label="cardboard star map",
        phrase="the cardboard star map",
        material="cardboard",
        play_use="guiding a toy rocket past pillow planets",
        reveal_use="pointing the way to the moon blanket again",
        break_text="a corner had split where a tape moon used to shine",
        tags={"cardboard", "surprise"},
    ),
    "cape": Gift(
        id="cape",
        label="cloth cape",
        phrase="the little red cloth cape",
        material="cloth",
        play_use="flying from chair to chair to rescue stuffed animals",
        reveal_use="another brave rescue across the cushions",
        break_text="the shoulder tie had torn loose in the morning game",
        tags={"cloth", "surprise"},
    ),
}

METHODS = {
    "tape": Method(
        id="tape",
        label="gold tape",
        phrase="a roll of gold tape",
        materials={"paper", "cardboard"},
        sense=3,
        needs_adult=False,
        repair_text="smoothed the torn edges of the {gift} together and laid a neat strip of gold tape across the weak spot",
        qa_text="used gold tape to hold the torn edges together",
        tags={"tape", "repair"},
    ),
    "glue": Method(
        id="glue",
        label="school glue",
        phrase="a bottle of school glue",
        materials={"paper", "cardboard"},
        sense=2,
        needs_adult=False,
        repair_text="dabbed school glue under the tear in the {gift} and pressed it flat with patient fingers",
        qa_text="used school glue and pressed the torn part flat",
        tags={"glue", "repair"},
    ),
    "fabric_glue": Method(
        id="fabric_glue",
        label="fabric glue",
        phrase="a small tube of fabric glue",
        materials={"cloth"},
        sense=3,
        needs_adult=False,
        repair_text="lined up the cloth edges of the {gift} and sealed the torn part with fabric glue",
        qa_text="sealed the torn cloth with fabric glue",
        tags={"fabric_glue", "repair"},
    ),
    "needle_thread": Method(
        id="needle_thread",
        label="needle and thread",
        phrase="a needle already threaded with red string",
        materials={"cloth"},
        sense=3,
        needs_adult=True,
        repair_text="stitched the torn tie of the {gift} back into place with small red loops",
        qa_text="stitched the torn tie back into place",
        tags={"sewing", "repair"},
    ),
    "stapler": Method(
        id="stapler",
        label="stapler",
        phrase="a heavy stapler",
        materials={"paper"},
        sense=1,
        needs_adult=True,
        repair_text="",
        qa_text="",
        tags={"bad_fix"},
    ),
}

PLACES = {
    "craft_drawer": HidingPlace(
        id="craft_drawer",
        label="craft drawer",
        phrase="the craft drawer in the hall table",
        holds={"tape", "glue", "fabric_glue"},
        clue_text="where colored paper sleeps",
        tags={"drawer"},
    ),
    "sewing_basket": HidingPlace(
        id="sewing_basket",
        label="sewing basket",
        phrase="the sewing basket by the lamp",
        holds={"needle_thread", "fabric_glue"},
        clue_text="where thread curls up like tiny snakes",
        tags={"basket"},
    ),
    "supply_shelf": HidingPlace(
        id="supply_shelf",
        label="supply shelf",
        phrase="the high supply shelf in the laundry room",
        holds={"tape", "glue"},
        clue_text="where tidy boxes wait in rows",
        tags={"shelf"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


KNOWLEDGE = {
    "quest": [(
        "What is a quest?",
        "A quest is a special trip with a goal. In a story, a character usually follows clues or keeps going until the goal is reached."
    )],
    "surprise": [(
        "What is a surprise?",
        "A surprise is something kind or unexpected that someone did not know was coming. A happy surprise can make a person feel loved."
    )],
    "paper": [(
        "Why can paper tear easily?",
        "Paper is thin, so if it bends hard or gets pulled, it can split. That is why paper crafts need gentle hands."
    )],
    "cardboard": [(
        "What is cardboard?",
        "Cardboard is thick, stiff paper. It is stronger than plain paper, but it can still bend or tear at the corners."
    )],
    "cloth": [(
        "What is cloth?",
        "Cloth is soft material made from threads woven together. Clothes, capes, and blankets can all be made from cloth."
    )],
    "tape": [(
        "What does tape do?",
        "Tape sticks things together. It can help hold a tear closed if the material is light enough."
    )],
    "glue": [(
        "What does glue do?",
        "Glue is a sticky liquid that helps things stay joined after it dries. It works best when you press the pieces gently together."
    )],
    "fabric_glue": [(
        "What is fabric glue for?",
        "Fabric glue is made to stick cloth together. It helps mend soft things without using a needle."
    )],
    "sewing": [(
        "What does sewing mean?",
        "Sewing means joining cloth with thread. A grown-up can use a needle to make small stitches that hold fabric together."
    )],
}
KNOWLEDGE_ORDER = [
    "quest",
    "surprise",
    "paper",
    "cardboard",
    "cloth",
    "tape",
    "glue",
    "fabric_glue",
    "sewing",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    gift = f["gift_cfg"]
    theme = f["theme"]
    method = f["method"]
    return [
        f'Write a heartwarming surprise quest for a young child that includes the word "cut-gerund".',
        f"Tell a gentle story where {hero.id} secretly mends a torn {gift.label} for {recipient.id} and follows clues through the house to find {method.label}.",
        f"Write a cozy quest story set in {theme.scene} where a child fixes something important before a loved one wakes up, ending with a warm surprise reveal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    helper = f["helper"]
    gift = f["gift_cfg"]
    method = f["method"]
    place = f["place"]
    relation_word = "little sibling" if f["relation"] == "sibling" else "friend"
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to do something kind for {recipient.id}, {hero.pronoun('possessive')} {relation_word}. "
            f"It is also about {recipient.id}, whose torn {gift.label} mattered to the game they loved."
        ),
        (
            f"Why did {hero.id} start the quest?",
            f"{hero.id} saw that the {gift.label} was torn and wanted to mend it before {recipient.id} woke up. "
            f"The quest gave {hero.pronoun('object')} a way to turn worry into a loving surprise."
        ),
        (
            'What did the first clue say about "cut-gerund"?',
            f'The first clue used "cut-gerund" as a silly password for the quest. '
            f'It made the search feel playful instead of scary.'
        ),
        (
            f"Where did {hero.id} find the repair tool?",
            f"{hero.pronoun().capitalize()} found {method.phrase} at {place.phrase}. "
            f"The clue trail led there on purpose, because {helper.label_word} had hidden the tool in a place where it could honestly belong."
        ),
    ]
    if f["help_needed"]:
        qa.append((
            f"How was the {gift.label} mended?",
            f"{helper.label_word.capitalize()} helped {hero.id} mend it. Together they {method.qa_text}, because that repair needed steady grown-up help."
        ))
    else:
        qa.append((
            f"How was the {gift.label} mended?",
            f"{hero.id} mended it alone and {method.qa_text}. The repair worked because the tool matched the material of the torn gift."
        ))
    qa.append((
        f"How did the story end?",
        f"It ended with a happy surprise: {recipient.id} woke up, saw the mended {gift.label}, and smiled right away. "
        f"The final image shows that the quest changed the room from worry back into play."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["theme"].tags) | set(f["gift_cfg"].tags) | set(f["method"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="castle",
        gift="crown",
        method="tape",
        hiding_place="craft_drawer",
        helper="mother",
        recipient_kind="sibling",
        hero_name="Lily",
        hero_gender="girl",
        recipient_name="Tom",
        recipient_gender="boy",
        hero_age=6,
    ),
    StoryParams(
        theme="space",
        gift="map",
        method="glue",
        hiding_place="supply_shelf",
        helper="father",
        recipient_kind="friend",
        hero_name="Ben",
        hero_gender="boy",
        recipient_name="Mia",
        recipient_gender="girl",
        hero_age=5,
    ),
    StoryParams(
        theme="garden",
        gift="cape",
        method="fabric_glue",
        hiding_place="sewing_basket",
        helper="grandmother",
        recipient_kind="sibling",
        hero_name="Ava",
        hero_gender="girl",
        recipient_name="Leo",
        recipient_gender="boy",
        hero_age=6,
    ),
    StoryParams(
        theme="castle",
        gift="cape",
        method="needle_thread",
        hiding_place="sewing_basket",
        helper="grandfather",
        recipient_kind="friend",
        hero_name="Sam",
        hero_gender="boy",
        recipient_name="Zoe",
        recipient_gender="girl",
        hero_age=7,
    ),
    StoryParams(
        theme="space",
        gift="crown",
        method="tape",
        hiding_place="craft_drawer",
        helper="mother",
        recipient_kind="sibling",
        hero_name="Nora",
        hero_gender="girl",
        recipient_name="Finn",
        recipient_gender="boy",
        hero_age=4,
    ),
]


ASP_RULES = r"""
fits(G, M) :- gift(G), method(M), material_of(G, Mat), repairs(M, Mat).
stored(P, M) :- place(P), method(M), holds(P, M).
sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

valid(T, G, M, P) :- theme(T), gift(G), method(M), place(P),
                     sensible(M), fits(G, M), stored(P, M).

help_needed :- chosen_method(M), needs_adult(M).
help_needed :- hero_age(A), A <= 4.

outcome(helped) :- help_needed.
outcome(solo)   :- not help_needed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in QUESTS:
        lines.append(asp.fact("theme", tid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("material_of", gid, gift.material))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        if method.needs_adult:
            lines.append(asp.fact("needs_adult", mid))
        for mat in sorted(method.materials):
            lines.append(asp.fact("repairs", mid, mat))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.holds):
            lines.append(asp.fact("holds", pid, mid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_method", params.method),
        asp.fact("hero_age", params.hero_age),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "helped" if help_needed(METHODS[params.method], params.hero_age) else "solo"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    if "cut-gerund" not in sample.story:
        raise StoryError('Smoke test failed: story did not include the required word "cut-gerund".')


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a child follows a clue trail to mend a torn gift as a surprise."
    )
    ap.add_argument("--theme", choices=QUESTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=PLACES)
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--recipient-kind", dest="recipient_kind", choices=["sibling", "friend"])
    ap.add_argument("--hero-age", dest="hero_age", type=int, choices=[4, 5, 6, 7])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gift and args.method:
        gift = GIFTS[args.gift]
        method = METHODS[args.method]
        place = PLACES[args.hiding_place] if args.hiding_place else None
        if not method_fits(gift, method) or method.sense < SENSE_MIN:
            raise StoryError(explain_rejection(gift, method))
        if place is not None and not place_holds(place, method):
            raise StoryError(explain_rejection(gift, method, place))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.gift is None or c[1] == args.gift)
        and (args.method is None or c[2] == args.method)
        and (args.hiding_place is None or c[3] == args.hiding_place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, gift, method, hiding_place = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather"])
    recipient_kind = args.recipient_kind or rng.choice(["sibling", "friend"])
    hero_name, hero_gender = _pick_child(rng)
    recipient_name, recipient_gender = _pick_child(rng, avoid=hero_name)
    hero_age = args.hero_age if args.hero_age is not None else rng.choice([4, 5, 6, 7])
    return StoryParams(
        theme=theme,
        gift=gift,
        method=method,
        hiding_place=hiding_place,
        helper=helper,
        recipient_kind=recipient_kind,
        hero_name=hero_name,
        hero_gender=hero_gender,
        recipient_name=recipient_name,
        recipient_gender=recipient_gender,
        hero_age=hero_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in QUESTS:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.hiding_place not in PLACES:
        raise StoryError(f"(Unknown hiding place: {params.hiding_place})")

    gift = GIFTS[params.gift]
    method = METHODS[params.method]
    place = PLACES[params.hiding_place]
    if not method_fits(gift, method) or method.sense < SENSE_MIN or not place_holds(place, method):
        raise StoryError(explain_rejection(gift, method, place))

    world = tell(params)
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, gift, method, hiding_place) combos:\n")
        for theme, gift, method, place in combos:
            print(f"  {theme:7} {gift:6} {method:13} {place}")
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
            header = f"### {p.hero_name}: {p.theme} quest, {p.gift} with {p.method}"
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
