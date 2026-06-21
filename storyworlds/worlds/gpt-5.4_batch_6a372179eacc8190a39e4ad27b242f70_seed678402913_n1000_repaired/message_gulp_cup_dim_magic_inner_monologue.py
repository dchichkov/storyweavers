#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py
=======================================================================

A standalone storyworld about a silly magical breakfast cup that writes a
message in its steam. If a child gulps too fast, the cup goes cup-dim and the
message blurs. A calmer second try can bring the glow back and reveal a small,
funny surprise.

Seed ingredients rebuilt as a world model
-----------------------------------------
Words: message, gulp, cup-dim
Features: Magic, Inner Monologue, Foreshadowing
Style: Comedy

This world models a tiny magical rule:
    warm drink + glowing cup -> steam message appears
    hasty gulps              -> steam fades, cup dims, message blurs
    calm waiting/stirring    -> glow returns, message clears

The prose is driven from simulated state, not from a frozen paragraph template.
It supports a reasonableness gate (only warm drinks can make the steam-message
story work) and an inline ASP twin that mirrors the Python logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py --drink cocoa
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py --drink juice
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4/message_gulp_cup_dim_magic_inner_monologue.py --verify
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
    warm: bool = False
    magical: bool = False
    can_stir: bool = False
    patient: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Drink:
    id: str
    label: str
    phrase: str
    warm: bool
    steam_line: str
    taste_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    hiding_place: str
    reveal_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    phrase: str
    action: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    needs_stir: bool
    patience_bonus: int
    text: str
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


def _r_steam_message(world: World) -> list[str]:
    out: list[str] = []
    cup = world.get("cup")
    drink = world.get("drink")
    if not (cup.magical and drink.warm):
        return out
    if cup.meters["glow"] < THRESHOLD:
        return out
    if drink.meters["steam"] < THRESHOLD:
        return out
    if cup.meters["message_visible"] >= THRESHOLD:
        return out
    sig = ("steam_message",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cup.meters["message_visible"] = 1.0
    out.append("__message__")
    return out


def _r_gulp_dims(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cup = world.get("cup")
    drink = world.get("drink")
    if child.meters["gulps"] < THRESHOLD:
        return out
    sig = ("gulp_dims", int(child.meters["gulps"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    drink.meters["steam"] = max(0.0, drink.meters["steam"] - 1.0)
    cup.meters["glow"] = max(0.0, cup.meters["glow"] - 1.0)
    child.memes["embarrassment"] += 1.0
    if cup.meters["glow"] < THRESHOLD or drink.meters["steam"] < THRESHOLD:
        cup.meters["message_visible"] = 0.0
        cup.meters["message_blurred"] += 1.0
        out.append("__cup_dim__")
    return out


def _r_repair_restores(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cup = world.get("cup")
    drink = world.get("drink")
    if child.meters["repair_steps"] < THRESHOLD:
        return out
    sig = ("repair_restores", int(child.meters["repair_steps"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cup.meters["glow"] += 1.0
    drink.meters["steam"] += 1.0
    child.memes["calm"] += 1.0
    if cup.meters["glow"] >= THRESHOLD and drink.meters["steam"] >= THRESHOLD:
        cup.meters["message_visible"] = 1.0
        out.append("__restored__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="steam_message", tag="magic", apply=_r_steam_message),
    Rule(name="gulp_dims", tag="physical", apply=_r_gulp_dims),
    Rule(name="repair_restores", tag="magic", apply=_r_repair_restores),
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


def message_possible(drink: Drink) -> bool:
    return drink.warm


def repair_effective(repair: Repair, helper: Helper) -> bool:
    if repair.needs_stir and "spoon" not in helper.tags:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for drink_id, drink in DRINKS.items():
        if not message_possible(drink):
            continue
        for helper_id, helper in HELPERS.items():
            for repair_id, repair in REPAIRS.items():
                if repair_effective(repair, helper):
                    combos.append((drink_id, helper_id, repair_id))
    return combos


def success_score(repair: Repair, patience: int) -> int:
    return repair.patience_bonus + patience


def story_outcome(params: "StoryParams") -> str:
    if not message_possible(DRINKS[params.drink]):
        return "impossible"
    if not repair_effective(REPAIRS[params.repair], HELPERS[params.helper]):
        return "failed"
    return "restored" if success_score(REPAIRS[params.repair], params.patience) >= 2 else "faded"


def predict_after_gulp(world: World) -> dict:
    sim = world.copy()
    do_gulp(sim, narrate=False)
    return {
        "cup_dim": sim.get("cup").meters["glow"] < THRESHOLD,
        "message_visible": sim.get("cup").meters["message_visible"] >= THRESHOLD,
    }


def predict_after_repair(world: World, repair: Repair) -> dict:
    sim = world.copy()
    do_gulp(sim, narrate=False)
    do_repair(sim, repair, narrate=False)
    return {
        "restored": sim.get("cup").meters["message_visible"] >= THRESHOLD,
        "glow": sim.get("cup").meters["glow"],
    }


def do_gulp(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["gulps"] += 1.0
    child.memes["hurry"] += 1.0
    propagate(world, narrate=narrate)


def do_repair(world: World, repair: Repair, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["repair_steps"] += 1.0
    if repair.needs_stir and "spoon" in world.facts["helper"].tags:
        world.get("spoon").meters["used"] += 1.0
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, cup: Entity, drink: Drink) -> None:
    world.say(
        f"On a bright, bumpy morning, {child.id} climbed onto a kitchen chair and found "
        f"{drink.phrase} waiting in a magical cup with tiny gold stars around the rim."
    )
    world.say(
        f"The cup gave a polite little shimmer. That should have been the first clue that "
        f"breakfast was not planning to behave normally."
    )
    world.say(drink.steam_line)


def first_message(world: World, prize: Prize) -> None:
    cup = world.get("cup")
    if cup.meters["message_visible"] >= THRESHOLD:
        world.say(
            f"In the steam, curly letters floated up like sleepy acrobats: "
            f'"{prize.reveal_line}"'
        )


def inner_monologue(world: World, child: Entity, drink: Drink) -> None:
    child.memes["wonder"] += 1.0
    world.say(
        f'{child.id} blinked. "{drink.label} does not usually send a message," '
        f'{child.pronoun()} thought. "Unless I am still dreaming, or this cup is magic, '
        f'or both."'
    )


def temptation(world: World, child: Entity, drink: Drink) -> None:
    child.memes["greed"] += 1.0
    world.say(
        f'But {drink.taste_line}, and the smell curled right under {child.pronoun("possessive")} nose. '
        f'That is when a brave but very silly idea marched into {child.pronoun("possessive")} head: '
        f'"If one sip is good, a giant gulp is faster."'
    )


def gulp_scene(world: World, child: Entity) -> None:
    do_gulp(world, narrate=False)
    world.say(
        f'So {child.id} took a heroic gulp. It was far too heroic. {child.pronoun().capitalize()} made a tiny '
        f'"hoo-hot!" sound, waved one hand in front of {child.pronoun("possessive")} mouth, and stared at the cup.'
    )
    if world.get("cup").meters["message_blurred"] >= THRESHOLD:
        world.say(
            "The glow shrank at once, the steam thinned, and the cup went cup-dim, as if someone had "
            "turned down a very dramatic moon."
        )
    world.say(
        f'"Oh no," {child.pronoun()} thought. "I gulped the magic crooked."'
    )


def helper_arrives(world: World, child: Entity, helper_ent: Entity, helper: Helper) -> None:
    world.say(
        f"Just then, {helper.phrase} came in, {helper.action}. {helper_ent.pronoun().capitalize()} saw "
        f"{child.id} staring at the cup as if it might start giving homework."
    )
    world.say(
        f'"Did the breakfast start talking again?" {helper_ent.pronoun()} asked.'
    )


def explain_problem(world: World, child: Entity, helper_ent: Entity, prize: Prize) -> None:
    world.say(
        f'"It sent a message!" said {child.id}. "Then I took a gulp, and now it is all swirly and shy."'
    )
    world.say(
        f'{child.id} pointed at the steam. "{prize.reveal_line}" had become a curly fog that looked more like '
        f'"bring socks to a turnip."'
    )


def advice_scene(world: World, helper_ent: Entity, helper: Helper, repair: Repair) -> None:
    world.say(
        f'{helper_ent.label_word.capitalize()} smiled the smile of someone who had seen stranger things before breakfast. '
        f'"{helper.advice}"'
    )
    world.say(repair.text)


def repair_scene(world: World, child: Entity, repair: Repair) -> None:
    do_repair(world, repair, narrate=False)
    action = "stirred once, then waited with both eyebrows lifted" if repair.needs_stir else "set the cup down, breathed slowly, and waited"
    world.say(
        f"{child.id} {action}. This felt extremely long, which is to say it lasted about three breaths."
    )
    world.say(
        f'"Steady now," {child.pronoun()} thought. "No more champion gulps. Tiny sips only. I can be wise for at least one minute."'
    )


def restored_ending(world: World, child: Entity, helper_ent: Entity, prize: Prize) -> None:
    child.memes["joy"] += 1.0
    child.memes["pride"] += 1.0
    world.say(
        "The stars on the cup brightened again. Fresh steam rose in a neat silver ribbon, and the letters came back, clear as window chalk."
    )
    world.say(
        f'This time the message said, "{prize.reveal_line}"'
    )
    world.say(
        prize.ending_line
    )
    world.say(
        f'{child.id} found {prize.phrase} there and laughed so hard that even {helper_ent.label_word} had to lean on the counter. '
        f'After that, {child.id} took careful little sips, because it is hard to argue with a cup that has already won once.'
    )


def faded_ending(world: World, child: Entity, helper_ent: Entity) -> None:
    child.memes["acceptance"] += 1.0
    world.say(
        "The cup did brighten a little, but not enough for full magic. The steam made one polite curl, then drifted away like a forgetful cloud."
    )
    world.say(
        f'{child.id} sighed, then giggled. "{child.pronoun("possessive").capitalize()} message has gone shy for the day," said {helper_ent.label_word}.'
    )
    world.say(
        f'So they made up their own message instead: "Sip first, boast later." {child.id} repeated it every time {child.pronoun()} looked at the cup, '
        f'and by snack time it had become the funniest house rule in the kitchen.'
    )


def tell(
    *,
    child_name: str,
    child_gender: str,
    drink: Drink,
    prize: Prize,
    helper: Helper,
    repair: Repair,
    patience: int,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label=child_name,
        traits=["eager", "funny"],
    ))
    helper_ent = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper.type,
        role="helper",
        label=helper.phrase,
        phrase=helper.phrase,
        tags=set(helper.tags),
    ))
    cup = world.add(Entity(
        id="cup",
        type="cup",
        label="cup",
        phrase="the magic cup",
        magical=True,
    ))
    drink_ent = world.add(Entity(
        id="drink",
        type="drink",
        label=drink.label,
        phrase=drink.phrase,
        warm=drink.warm,
        tags=set(drink.tags),
    ))
    spoon = world.add(Entity(
        id="spoon",
        type="spoon",
        label="spoon",
        can_stir=True,
    ))

    cup.meters["glow"] = 1.0
    drink_ent.meters["steam"] = 1.0 if drink.warm else 0.0
    child.memes["patience"] = float(patience)

    world.facts.update(
        child=child,
        helper=helper,
        helper_ent=helper_ent,
        drink_cfg=drink,
        prize=prize,
        repair=repair,
        patience=patience,
    )

    opening(world, child, cup, drink)
    propagate(world, narrate=False)
    first_message(world, prize)
    inner_monologue(world, child, drink)

    world.para()
    temptation(world, child, drink)
    pred = predict_after_gulp(world)
    world.facts["predicted_cup_dim"] = pred["cup_dim"]
    gulp_scene(world, child)

    world.para()
    helper_arrives(world, child, helper_ent, helper)
    explain_problem(world, child, helper_ent, prize)
    advice_scene(world, helper_ent, helper, repair)
    pred_fix = predict_after_repair(world, repair)
    world.facts["predicted_restored"] = pred_fix["restored"]
    repair_scene(world, child, repair)

    world.para()
    outcome = story_outcome(StoryParams(
        drink=drink.id,
        prize=prize.id,
        helper=helper.id,
        repair=repair.id,
        name=child_name,
        gender=child_gender,
        patience=patience,
        seed=None,
    ))
    if outcome == "restored":
        restored_ending(world, child, helper_ent, prize)
    else:
        faded_ending(world, child, helper_ent)

    world.facts["outcome"] = outcome
    world.facts["message_seen"] = cup.meters["message_visible"] >= THRESHOLD
    world.facts["cup_dimmed"] = cup.meters["message_blurred"] >= THRESHOLD
    return world


DRINKS = {
    "cocoa": Drink(
        id="cocoa",
        label="cocoa",
        phrase="a warm mug of cocoa",
        warm=True,
        steam_line="Warm cocoa steam curled up from the cup and wrote loops in the air.",
        taste_line="the cocoa smelled like chocolate wearing a winter hat",
        tags={"warm_drink", "cocoa", "steam"},
    ),
    "tea": Drink(
        id="tea",
        label="tea",
        phrase="a warm cup of honey tea",
        warm=True,
        steam_line="Honey-sweet steam rose from the tea and twirled into neat little commas.",
        taste_line="the tea smelled soft and lemony, like sunshine trying to whisper",
        tags={"warm_drink", "tea", "steam"},
    ),
    "cider": Drink(
        id="cider",
        label="cider",
        phrase="a warm cup of apple cider",
        warm=True,
        steam_line="Apple-cider steam floated up in puffy curls that looked almost ready to spell something.",
        taste_line="the cider smelled like apples, cinnamon, and trouble",
        tags={"warm_drink", "cider", "steam"},
    ),
    "juice": Drink(
        id="juice",
        label="juice",
        phrase="a cold glass of apple juice",
        warm=False,
        steam_line="The juice sat quietly and did not steam at all.",
        taste_line="the juice smelled crisp and ordinary",
        tags={"cold_drink", "juice"},
    ),
}

PRIZES = {
    "bun": Prize(
        id="bun",
        label="bun",
        phrase="a cinnamon bun with a crooked raisin smile",
        hiding_place="the bread box",
        reveal_line="Look in the bread box",
        ending_line="They opened the bread box, and there sat a cinnamon bun with a crooked raisin smile, as if it had been waiting to hear the joke.",
        tags={"bun", "bread_box"},
    ),
    "berry": Prize(
        id="berry",
        label="berry_tart",
        phrase="a tiny berry tart on a blue plate",
        hiding_place="the coolest shelf in the pantry",
        reveal_line="Peek at the pantry shelf",
        ending_line="Inside the pantry waited a tiny berry tart on a blue plate, looking much too proud of itself.",
        tags={"tart", "pantry"},
    ),
    "sticker": Prize(
        id="sticker",
        label="sticker",
        phrase="a shiny star sticker tucked beside the napkins",
        hiding_place="the napkin drawer",
        reveal_line="Try the napkin drawer",
        ending_line="In the napkin drawer lay a shiny star sticker, which was not a snack at all but still felt like a victory.",
        tags={"sticker", "drawer"},
    ),
}

HELPERS = {
    "grandma": Helper(
        id="grandma",
        type="grandmother",
        phrase="Grandma",
        action="carrying a plate and humming to herself",
        advice="Magic likes manners. Slow down and let the steam gather its thoughts.",
        tags={"adult", "spoon"},
    ),
    "dad": Helper(
        id="dad",
        type="father",
        phrase="Dad",
        action="looking for the jam with one slipper half on",
        advice="No racing the cup. Set it down and give the magic room to catch up.",
        tags={"adult"},
    ),
    "aunt": Helper(
        id="aunt",
        type="woman",
        phrase="Aunt Nia",
        action="balancing two oranges and a newspaper",
        advice="The cup is dramatic, not mean. Be patient and it may start showing off again.",
        tags={"adult", "spoon"},
    ),
}

REPAIRS = {
    "wait": Repair(
        id="wait",
        label="wait quietly",
        needs_stir=False,
        patience_bonus=1,
        text='So they tried the serious method first: no gulping, no waving, just a quiet wait.',
        qa_text="They set the cup down and waited calmly for the magic to gather again.",
        tags={"patience"},
    ),
    "stir": Repair(
        id="stir",
        label="stir slowly",
        needs_stir=True,
        patience_bonus=2,
        text='Then came the fancier method: one slow stir, as if the spoon were smoothing wrinkled letters.',
        qa_text="They stirred the drink slowly so the steam and glow could settle and return.",
        tags={"spoon", "patience"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nora", "Zoe", "Ivy", "Maya", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Toby", "Finn", "Leo", "Max", "Noah", "Eli"]


@dataclass
class StoryParams:
    drink: str
    prize: str
    helper: str
    repair: str
    name: str
    gender: str
    patience: int
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        drink="cocoa",
        prize="bun",
        helper="grandma",
        repair="stir",
        name="Milo",
        gender="boy",
        patience=1,
        seed=None,
    ),
    StoryParams(
        drink="tea",
        prize="sticker",
        helper="dad",
        repair="wait",
        name="Nora",
        gender="girl",
        patience=1,
        seed=None,
    ),
    StoryParams(
        drink="cider",
        prize="berry",
        helper="aunt",
        repair="stir",
        name="Poppy",
        gender="girl",
        patience=0,
        seed=None,
    ),
    StoryParams(
        drink="tea",
        prize="bun",
        helper="dad",
        repair="wait",
        name="Finn",
        gender="boy",
        patience=0,
        seed=None,
    ),
]


KNOWLEDGE = {
    "steam": [
        (
            "Why can warm drinks make steam?",
            "Warm drinks heat water into tiny drops that float up into the air. That cloudy steam is easier to see when the drink is hot."
        )
    ],
    "warm_drink": [
        (
            "Why would a magic message show better over a warm drink than a cold one?",
            "A warm drink makes steam, and steam gives the magic something to write on. A cold drink does not make that same cloudy ribbon."
        )
    ],
    "cocoa": [
        (
            "What is cocoa?",
            "Cocoa is a warm chocolate drink. People often sip it slowly because it can be hot."
        )
    ],
    "tea": [
        (
            "What is tea?",
            "Tea is a drink made by soaking leaves or herbs in hot water. It is often warm and smells gentle and sweet."
        )
    ],
    "cider": [
        (
            "What is apple cider?",
            "Apple cider is a drink made from apples, and warm cider can smell spicy and sweet. It often steams when it is hot."
        )
    ],
    "spoon": [
        (
            "What does stirring do in a cup?",
            "Stirring moves the drink around so the heat and flavor mix together. In a magic story, it can also help the steam rise evenly again."
        )
    ],
    "patience": [
        (
            "What does patience mean?",
            "Patience means waiting without rushing, even when you want something right away. It helps people notice things they would miss in a hurry."
        )
    ],
    "bread_box": [
        (
            "What is a bread box?",
            "A bread box is a container for keeping bread or buns in the kitchen. It is a funny but sensible place to hide a breakfast surprise."
        )
    ],
    "drawer": [
        (
            "What is a drawer?",
            "A drawer is a box-like part of a table or cabinet that slides in and out. People keep napkins, tools, or small things inside."
        )
    ],
    "pantry": [
        (
            "What is a pantry?",
            "A pantry is a place where food is stored in a kitchen. Shelves there hold snacks, jars, and baking things."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "steam",
    "warm_drink",
    "cocoa",
    "tea",
    "cider",
    "spoon",
    "patience",
    "bread_box",
    "drawer",
    "pantry",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    drink = f["drink_cfg"]
    prize = f["prize"]
    helper_ent = f["helper_ent"]
    return [
        f'Write a funny magical breakfast story for a 3-to-5-year-old that includes the words "message", "gulp", and "cup-dim".',
        f"Tell a comedy story where {child.id} finds a message in the steam above {drink.phrase}, gulps too fast, and must calm down with help from {helper_ent.label_word}.",
        f"Write a child-facing story with inner monologue and foreshadowing where a magic cup reveals a clue leading to {prize.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper_ent = f["helper_ent"]
    drink = f["drink_cfg"]
    prize = f["prize"]
    repair = f["repair"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who finds magic in a breakfast cup, and {helper_ent.label_word} who helps when the message goes wrong."
        ),
        (
            "What was strange about the cup at the beginning?",
            f"The cup glowed and a message appeared in the steam above {drink.label}. That showed right away that this was not an ordinary breakfast."
        ),
        (
            f"Why did the cup go cup-dim?",
            f"It went cup-dim because {child.id} took a big gulp too fast. The rushed gulp thinned the steam and made the magic message blur."
        ),
        (
            f"What was {child.id} thinking when the magic started?",
            f"{child.id} thought that drinks do not usually send messages, so the cup must be magical or the morning must be very odd. That inner thought shows {child.pronoun('object')} noticing the magic before anyone else does."
        ),
        (
            f"How did {helper_ent.label_word} help?",
            f"{helper_ent.label_word.capitalize()} told {child.id} not to rush and to try {repair.label}. The advice mattered because the cup's magic worked better when the steam had time to settle."
        ),
    ]
    if outcome == "restored":
        qa.append(
            (
                "How was the problem solved?",
                f"The problem was solved when they {repair.qa_text.lower()} The cup brightened again, and the message became clear enough to lead them to {prize.phrase}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily and sillily: the message returned, and they found {prize.phrase}. The ending proves that calm little sips worked better than one giant gulp."
            )
        )
    else:
        qa.append(
            (
                "Did the magic come all the way back?",
                f"No. The cup brightened a little, but the full message did not return. Even so, {child.id} learned to laugh and slow down instead of trying to boss the magic."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a funny family rule instead of a treasure. They decided to say 'Sip first, boast later,' because rushing had made the message disappear."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    f = world.facts
    tags |= set(f["drink_cfg"].tags)
    tags |= set(f["repair"].tags)
    tags |= set(f["prize"].tags)
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
        bits: list[str] = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        flags = [name for name, on in (("warm", e.warm), ("magical", e.magical), ("can_stir", e.can_stir), ("patient", e.patient)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(drink: Drink, helper: Optional[Helper] = None, repair: Optional[Repair] = None) -> str:
    if not message_possible(drink):
        return (
            f"(No story: {drink.phrase} is cold, so it makes no steam for a magic message. "
            f"Pick a warm drink like cocoa, tea, or cider.)"
        )
    if helper is not None and repair is not None and not repair_effective(repair, helper):
        return (
            f"(No story: repair '{repair.id}' needs a helper with a spoon-ready move, but {helper.phrase} "
            f"does not bring that kind of help in this world. Pick a different helper or use --repair wait.)"
        )
    return "(No story: this combination does not fit the world rules.)"


ASP_RULES = r"""
% A valid story needs a warm drink, because the message is written in steam.
message_possible(D) :- drink(D), warm(D).

% Some repairs need a helper who can support stirring.
repair_effective(R, H) :- repair(R), helper(H), not needs_stir(R).
repair_effective(R, H) :- repair(R), helper(H), needs_stir(R), has_spoon(H).

valid(D, H, R) :- message_possible(D), repair_effective(R, H).

score(S) :- chosen_repair(R), patience(P), bonus(R, B), S = P + B.
outcome(restored) :- chosen_drink(D), message_possible(D), chosen_helper(H), chosen_repair(R),
                     repair_effective(R, H), score(S), S >= 2.
outcome(faded) :- chosen_drink(D), message_possible(D), chosen_helper(H), chosen_repair(R),
                  repair_effective(R, H), score(S), S < 2.
outcome(failed) :- chosen_drink(D), message_possible(D), chosen_helper(H), chosen_repair(R),
                   not repair_effective(R, H).
outcome(impossible) :- chosen_drink(D), not message_possible(D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for drink_id, drink in DRINKS.items():
        lines.append(asp.fact("drink", drink_id))
        if drink.warm:
            lines.append(asp.fact("warm", drink_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        if "spoon" in helper.tags:
            lines.append(asp.fact("has_spoon", helper_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        if repair.needs_stir:
            lines.append(asp.fact("needs_stir", repair_id))
        lines.append(asp.fact("bonus", repair_id, repair.patience_bonus))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_drink", params.drink),
        asp.fact("chosen_helper", params.helper),
        asp.fact("chosen_repair", params.repair),
        asp.fact("patience", params.patience),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed at seed {seed}.")
            break
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != story_outcome(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches story_outcome() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a magical breakfast cup, a hasty gulp, and a steam message."
    )
    ap.add_argument("--drink", choices=DRINKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--patience", type=int, choices=[0, 1, 2], help="how ready the child is to slow down")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (drink, helper, repair) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.drink is not None and not message_possible(DRINKS[args.drink]):
        raise StoryError(explain_rejection(DRINKS[args.drink]))
    if args.helper is not None and args.repair is not None:
        helper = HELPERS[args.helper]
        repair = REPAIRS[args.repair]
        if not repair_effective(repair, helper):
            raise StoryError(explain_rejection(DRINKS[args.drink] if args.drink else DRINKS["cocoa"], helper, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.drink is None or combo[0] == args.drink)
        and (args.helper is None or combo[1] == args.helper)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    drink_id, helper_id, repair_id = rng.choice(sorted(combos))
    prize_id = args.prize or rng.choice(sorted(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    patience = args.patience if args.patience is not None else rng.choice([0, 1, 2])

    return StoryParams(
        drink=drink_id,
        prize=prize_id,
        helper=helper_id,
        repair=repair_id,
        name=name,
        gender=gender,
        patience=patience,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.drink not in DRINKS:
        raise StoryError(f"Unknown drink: {params.drink}")
    if params.prize not in PRIZES:
        raise StoryError(f"Unknown prize: {params.prize}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")
    if params.repair not in REPAIRS:
        raise StoryError(f"Unknown repair: {params.repair}")
    if params.gender not in {"girl", "boy"}:
        raise StoryError(f"Unknown gender: {params.gender}")
    if not message_possible(DRINKS[params.drink]):
        raise StoryError(explain_rejection(DRINKS[params.drink]))
    if not repair_effective(REPAIRS[params.repair], HELPERS[params.helper]):
        raise StoryError(explain_rejection(DRINKS[params.drink], HELPERS[params.helper], REPAIRS[params.repair]))

    world = tell(
        child_name=params.name,
        child_gender=params.gender,
        drink=DRINKS[params.drink],
        prize=PRIZES[params.prize],
        helper=HELPERS[params.helper],
        repair=REPAIRS[params.repair],
        patience=params.patience,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (drink, helper, repair) combos:\n")
        for drink_id, helper_id, repair_id in combos:
            print(f"  {drink_id:8} {helper_id:8} {repair_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.name}: {p.drink}, {p.helper}, {p.repair} "
                f"({story_outcome(p)})"
            )
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
