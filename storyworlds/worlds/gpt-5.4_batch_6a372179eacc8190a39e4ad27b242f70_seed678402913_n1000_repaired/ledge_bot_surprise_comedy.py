#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py
=======================================================

A standalone storyworld for a tiny comedy domain: a child spots something stuck
on a ledge, thinks about climbing, and a helpful little bot turns the problem
into a funny surprise by solving it safely.

The world model tracks typed entities with physical meters and emotional memes.
Stories vary by place, object on the ledge, the bot's safe method, and the final
surprise gag, while a reasonableness gate refuses weak combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --place playroom --item airplane
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --item fishbowl
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --method spring_hat
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --all
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/ledge_bot_surprise_comedy.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    ledge: str
    scene: str
    adult_here: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class LedgeItem:
    id: str
    label: str
    phrase: str
    texture: str
    problem: str
    weight: int
    flat: bool = False
    soft: bool = False
    fragile: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Method:
    id: str
    label: str
    sense: int
    lift: int
    needs_flat: bool = False
    avoids_fragile: bool = False
    body: str = ""
    qa_text: str = ""
    fail_reason: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    setup: str
    reveal: str
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    stool = world.get("stool")
    room = world.get("room")
    out: list[str] = []
    if child.meters["climbing"] >= THRESHOLD and stool.meters["wobbly"] >= THRESHOLD:
        sig = ("wobble", "child")
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["alarm"] += 1
            room.meters["risk"] += 1
            out.append("__wobble__")
    return out


def _r_relieved(world: World) -> list[str]:
    child = world.get("child")
    bot = world.get("bot")
    item = world.get("item")
    room = world.get("room")
    out: list[str] = []
    if item.meters["retrieved"] >= THRESHOLD:
        sig = ("relief", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["relief"] += 1
            child.memes["joy"] += 1
            bot.memes["pride"] += 1
            room.meters["risk"] = 0.0
            out.append("__retrieved__")
    return out


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="relief", tag="social", apply=_r_relieved),
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


def method_works(item: LedgeItem, method: Method) -> bool:
    if method.sense < SENSE_MIN:
        return False
    if item.weight > method.lift:
        return False
    if method.needs_flat and not item.flat:
        return False
    if method.avoids_fragile and item.fragile:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id in sorted(place.affords):
            item = ITEMS[item_id]
            for method_id, method in METHODS.items():
                if not method_works(item, method):
                    continue
                for surprise_id in SURPRISES:
                    combos.append((place_id, item_id, method_id, surprise_id))
    return combos


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def explain_rejection(item: LedgeItem, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method.id}' is too silly to count as a safe fix here. "
            f"Pick a steadier bot method like {', '.join(sorted(m.id for m in sensible_methods()))}.)"
        )
    if item.weight > method.lift:
        return (
            f"(No story: {item.phrase} is too heavy for {method.label}. "
            f"The bot would need a stronger way to reach the ledge.)"
        )
    if method.needs_flat and not item.flat:
        return (
            f"(No story: {method.label} only works on something with a flat side, "
            f"and {item.phrase} does not give the cup a good grip.)"
        )
    if method.avoids_fragile and item.fragile:
        return (
            f"(No story: {method.label} would be too rough for {item.phrase}. "
            f"This world refuses a fix that might break the object.)"
        )
    return "(No story: that item and bot method do not make a reasonable pair.)"


def predict_climb(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["climbing"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("room").meters["risk"],
        "alarm": sim.get("child").memes["alarm"],
    }


def introduce(world: World, child: Entity, adult: Entity, bot: Entity, item: LedgeItem) -> None:
    world.say(
        f"{child.id} was in {world.place.label} with {child.pronoun('possessive')} "
        f"{adult.label_word} and a round helper bot named {bot.id}. {world.place.scene}"
    )
    world.say(
        f"{child.id} looked up and gasped. {item.phrase.capitalize()} was stuck on {world.place.ledge}."
    )
    child.memes["want"] += 1
    bot.memes["notice"] += 1


def desire(world: World, child: Entity, item: LedgeItem) -> None:
    world.say(
        f'"Oh no," said {child.id}. "My {item.label} is way up there." '
        f"{item.problem.capitalize()}."
    )


def risky_idea(world: World, child: Entity) -> None:
    stool = world.get("stool")
    stool.meters["wobbly"] += 1
    world.say(
        f"{child.id} dragged over a little stool and put one foot on it. "
        f"The stool gave a tiny wiggle."
    )
    child.meters["climbing"] += 1
    propagate(world, narrate=False)


def bot_warning(world: World, child: Entity, bot: Entity) -> None:
    pred = predict_climb(world)
    world.facts["predicted_risk"] = pred["risk"]
    bot.memes["care"] += 1
    world.say(
        f'{bot.id} zipped forward and blinked a blue light. '
        f'"Beep-beep. Wobbly plan detected," {bot.pronoun()} said. '
        f'"If you climb, the stool may wobble and your tummy may do a jump."'
    )


def pause(world: World, adult: Entity, child: Entity) -> None:
    child.memes["embarrassed"] += 1
    world.say(
        f'{adult.label_word.capitalize()} touched {child.id}\'s shoulder and smiled. '
        f'"Let the bot try first," {adult.pronoun()} said.'
    )


def bot_attempt(world: World, bot: Entity, item: LedgeItem, method: Method) -> None:
    bot.meters["working"] += 1
    world.say(method.body.format(bot=bot.id, item=item.label, ledge=world.place.ledge))
    world.get("item").meters["retrieved"] += 1
    propagate(world, narrate=False)


def safe_retrieval(world: World, child: Entity, bot: Entity, item: LedgeItem, method: Method) -> None:
    world.say(
        f"In one neat little swoop, {bot.id} brought {item.it()} down from the ledge and rolled back to {child.id}."
    )
    world.say(
        f'{child.id} laughed so hard {child.pronoun()} nearly forgot to look worried. '
        f'"You got it!" {child.pronoun()} said.'
    )


def surprise_turn(world: World, child: Entity, adult: Entity, bot: Entity, surprise: Surprise) -> None:
    child.memes["surprise"] += 1
    child.memes["joy"] += 1
    bot.memes["comedy"] += 1
    world.say(surprise.setup.format(child=child.id, adult=adult.label_word, bot=bot.id))
    world.say(surprise.reveal.format(child=child.id, adult=adult.label_word, bot=bot.id))
    world.say(surprise.closing.format(child=child.id, adult=adult.label_word, bot=bot.id))


def ending(world: World, child: Entity, adult: Entity, bot: Entity, item: LedgeItem) -> None:
    child.memes["lesson"] += 1
    world.say(
        f'{adult.label_word.capitalize()} gave {child.id} a hug. '
        f'"High ledges are for grown-up reaching and careful helpers," {adult.pronoun()} said.'
    )
    world.say(
        f"{child.id} tucked {item.it()} close, and {bot.id} did one proud little spin on the floor. "
        f"The room felt bright, safe, and very silly."
    )


def tell(place: Place, item_cfg: LedgeItem, method: Method, surprise: Surprise,
         child_name: str = "Mia", child_type: str = "girl", adult_type: str = "mother",
         bot_name: str = "Bop") -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", role="adult"))
    bot = world.add(Entity(id="bot", kind="character", type="bot", label=bot_name, role="helper", tags={"bot"}))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, phrase=item_cfg.phrase, tags=set(item_cfg.tags)))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    stool = world.add(Entity(id="stool", kind="thing", type="stool", label="stool"))

    child.attrs["name"] = child_name
    adult.attrs["name"] = adult_type
    bot.attrs["name"] = bot_name

    introduce(world, child, adult, bot, item_cfg)
    desire(world, child, item_cfg)

    world.para()
    risky_idea(world, child)
    bot_warning(world, child, bot)
    pause(world, adult, child)

    world.para()
    bot_attempt(world, bot, item_cfg, method)
    safe_retrieval(world, child, bot, item_cfg, method)

    world.para()
    surprise_turn(world, child, adult, bot, surprise)
    ending(world, child, adult, bot, item_cfg)

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        method=method,
        surprise=surprise,
        child=child,
        adult=adult,
        bot=bot,
        item=item,
        risk=room.meters["risk"],
        retrieved=item.meters["retrieved"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    method: str
    surprise: str
    child_name: str
    child_gender: str
    adult: str
    bot_name: str
    seed: Optional[int] = None


PLACES = {
    "playroom": Place(
        id="playroom",
        label="the playroom",
        ledge="the sunny window ledge",
        scene="Blocks were stacked like little towers, and crayons slept in a bright tin.",
        adult_here="mother",
        affords={"airplane", "duck", "mitten"},
        tags={"playroom"},
    ),
    "classroom": Place(
        id="classroom",
        label="the classroom",
        ledge="the tall reading-corner ledge",
        scene="Picture books leaned in a basket, and the art table smelled faintly of glue.",
        adult_here="teacher",
        affords={"airplane", "star", "duck"},
        tags={"classroom"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the kitchen",
        ledge="the high pantry ledge",
        scene="A bowl of lemons shone on the counter, and the clock made slow tick-tock sounds.",
        adult_here="father",
        affords={"mitten", "star", "fishbowl"},
        tags={"kitchen"},
    ),
}

ITEMS = {
    "airplane": LedgeItem(
        id="airplane",
        label="paper airplane",
        phrase="a paper airplane",
        texture="light and crisp",
        problem="it had sailed higher than any throw was supposed to go",
        weight=1,
        flat=True,
        soft=True,
        tags={"paper", "airplane"},
    ),
    "duck": LedgeItem(
        id="duck",
        label="stuffed duck",
        phrase="a stuffed duck with one floppy wing",
        texture="soft and squishy",
        problem="it stared down from above as if it had climbed there by itself",
        weight=1,
        soft=True,
        tags={"toy", "duck"},
    ),
    "mitten": LedgeItem(
        id="mitten",
        label="red mitten",
        phrase="a red mitten",
        texture="soft and woolly",
        problem="it looked as if the ledge had tried it on and kept it",
        weight=1,
        soft=True,
        tags={"clothes", "mitten"},
    ),
    "star": LedgeItem(
        id="star",
        label="gold paper star",
        phrase="a gold paper star from the craft table",
        texture="light and flat",
        problem="it glittered from the ledge like a tiny prize",
        weight=1,
        flat=True,
        tags={"craft", "star"},
    ),
    "fishbowl": LedgeItem(
        id="fishbowl",
        label="fishbowl",
        phrase="a round fishbowl",
        texture="heavy and sloshy",
        problem="it sat there looking far too breakable and far too heavy",
        weight=3,
        flat=False,
        fragile=True,
        tags={"glass", "fish"},
    ),
}

METHODS = {
    "grabber": Method(
        id="grabber",
        label="the soft grabber arm",
        sense=3,
        lift=2,
        body="{bot} popped open a striped grabber arm, stretched toward {ledge}, and pinched the {item} as gently as a polite crab",
        qa_text="used a soft grabber arm to bring it down safely",
        fail_reason="it could not hold the item safely",
        tags={"grabber", "safe_tool"},
    ),
    "suction": Method(
        id="suction",
        label="the suction cup",
        sense=3,
        lift=1,
        needs_flat=True,
        body="{bot} made a brave little whirr, raised a rubber cup, and stuck it to the {item} before backing away very slowly",
        qa_text="used a suction cup to pull it down from the ledge",
        fail_reason="the item gave the cup no good grip",
        tags={"suction", "safe_tool"},
    ),
    "net": Method(
        id="net",
        label="the tiny catching net",
        sense=2,
        lift=1,
        avoids_fragile=True,
        body="{bot} flipped out a tiny net, scooped under the {item}, and tipped it neatly off {ledge}",
        qa_text="used a little net to scoop it down",
        fail_reason="the scoop would have been too rough",
        tags={"net", "safe_tool"},
    ),
    "spring_hat": Method(
        id="spring_hat",
        label="the spring hat",
        sense=1,
        lift=1,
        body="{bot} tried to launch a springy hat upward, which would have been more circus than helper",
        qa_text="bounced a spring hat at it",
        fail_reason="it was too silly to count as safe help",
        tags={"silly"},
    ),
}

SURPRISES = {
    "sticker": Surprise(
        id="sticker",
        setup="{bot} gave a happy beep, and a tiny drawer in its belly popped open.",
        reveal="Out slid a shiny sticker that said, \"Ledge Legend.\" {child} blinked, then burst out laughing.",
        closing="{adult} laughed too, and {bot} gave a proud boop as if it had planned the joke all along.",
        tags={"sticker", "surprise"},
    ),
    "trumpet": Surprise(
        id="trumpet",
        setup="{child} reached for the rescued thing, but {bot} hiccupped a funny click first.",
        reveal="Instead of another beep, a silly trumpet toot came out. It was so loud and so tiny that everyone jumped, then giggled.",
        closing="{bot} spun in a circle like the toot had been a fanfare for winning.",
        tags={"trumpet", "surprise"},
    ),
    "confetti": Surprise(
        id="confetti",
        setup="{bot} rolled back, puffed once, and suddenly looked very important.",
        reveal="A puff of paper confetti fluttered from a hidden slot and landed on {child}'s hair like a tiny parade.",
        closing="{adult} brushed the paper dots away, still smiling, while {bot} blinked as if it had just told the best joke in the room.",
        tags={"confetti", "surprise"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Finn"]
BOT_NAMES = ["Bop", "Pip", "Zing", "Dot"]
ADULT_TYPES = ["mother", "father", "teacher"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    item = f["item_cfg"]
    place = f["place"]
    bot = f["bot"]
    return [
        f'Write a funny surprise story for a 3-to-5-year-old that includes the words "ledge" and "bot".',
        f"Tell a comedy where a child named {child.attrs['name']} sees {item.phrase} stuck on a ledge in {place.label}, almost tries a wobbly climb, and a helper bot saves the day.",
        f"Write a gentle story with a silly twist where {bot.label} reaches something high up safely and ends with everyone laughing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    bot = f["bot"]
    item_cfg = f["item_cfg"]
    place = f["place"]
    method = f["method"]
    surprise = f["surprise"]
    adult_word = adult.label_word
    qa = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']}, a helpful little bot named {bot.label}, and {child.pronoun('possessive')} {adult_word}. They were together in {place.label} when something ended up on a ledge.",
        ),
        (
            f"What problem did {child.attrs['name']} have?",
            f"{item_cfg.phrase.capitalize()} was stuck on {place.ledge}, so {child.attrs['name']} could not reach it. That is what started the whole funny problem.",
        ),
        (
            f"Why did the bot stop {child.attrs['name']} from climbing?",
            f"{bot.label.capitalize()} noticed the stool was wobbly and warned that climbing would be a bad plan. The bot was trying to keep {child.attrs['name']} safe before anyone slipped.",
        ),
        (
            f"How did the bot get the {item_cfg.label} down?",
            f"{bot.label.capitalize()} {method.qa_text}. The safe tool worked better than climbing because the object was high but still reasonable for the bot to handle.",
        ),
        (
            "What was the surprise at the end?",
            f"There was a funny surprise when {surprise.reveal.split('.')[0].lower()}. Everyone laughed because the bot solved the problem and then added one more silly moment.",
        ),
        (
            "How did the story end?",
            f"It ended safely and happily: {child.attrs['name']} got the {item_cfg.label} back, nobody had to climb the ledge, and the room filled with laughter. The ending shows that careful help can be funny too.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "ledge": [
        (
            "What is a ledge?",
            "A ledge is a narrow shelf or edge that sticks out from a wall or window. Things can rest there, but it may be too high for a child to reach."
        )
    ],
    "bot": [
        (
            "What is a bot?",
            "A bot is a little machine or robot made to help with jobs. Some bots roll, beep, or use tools to do things safely."
        )
    ],
    "grabber": [
        (
            "What is a grabber arm?",
            "A grabber arm is a tool that reaches out and gently pinches or holds something. It helps you get things without climbing."
        )
    ],
    "suction": [
        (
            "What does a suction cup do?",
            "A suction cup sticks to a smooth, flat thing by making a tight seal. That can help pull light objects down."
        )
    ],
    "net": [
        (
            "What is a catching net used for?",
            "A small catching net can scoop up a light thing so it does not fall far. It is useful when you need a gentle catch."
        )
    ],
    "safe_tool": [
        (
            "Why is using a tool safer than climbing a wobbly stool?",
            "A safe tool can reach the high thing without making a child balance up high. That lowers the chance of falling."
        )
    ],
    "surprise": [
        (
            "Why can surprises be funny in a story?",
            "A surprise is funny when something unexpected happens but no one is hurt. It makes the ending feel lively and playful."
        )
    ],
}
KNOWLEDGE_ORDER = ["ledge", "bot", "grabber", "suction", "net", "safe_tool", "surprise"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ledge", "bot", "surprise"} | set(world.facts["method"].tags)
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
        if e.label and e.id != e.label:
            bits.append(f"label={e.label!r}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% reasonable tool pairing
works(I, M) :- item(I), method(M), sense(M, S), sense_min(Min), S >= Min,
               weight(I, W), lift(M, L), W <= L,
               not flat_needed_but_missing(I, M),
               not fragile_forbidden(I, M).

flat_needed_but_missing(I, M) :- needs_flat(M), not flat(I).
fragile_forbidden(I, M) :- avoids_fragile(M), fragile(I).

valid(P, I, M, S) :- place(P), affords(P, I), works(I, M), surprise(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for item_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, item_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("weight", item_id, item.weight))
        if item.flat:
            lines.append(asp.fact("flat", item_id))
        if item.fragile:
            lines.append(asp.fact("fragile", item_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("lift", method_id, method.lift))
        if method.needs_flat:
            lines.append(asp.fact("needs_flat", method_id))
        if method.avoids_fragile:
            lines.append(asp.fact("avoids_fragile", method_id))
    for surprise_id in SURPRISES:
        lines.append(asp.fact("surprise", surprise_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        place="playroom",
        item="airplane",
        method="suction",
        surprise="trumpet",
        child_name="Mia",
        child_gender="girl",
        adult="mother",
        bot_name="Bop",
    ),
    StoryParams(
        place="classroom",
        item="duck",
        method="grabber",
        surprise="sticker",
        child_name="Ben",
        child_gender="boy",
        adult="teacher",
        bot_name="Pip",
    ),
    StoryParams(
        place="kitchen",
        item="star",
        method="net",
        surprise="confetti",
        child_name="Nora",
        child_gender="girl",
        adult="father",
        bot_name="Zing",
    ),
    StoryParams(
        place="playroom",
        item="mitten",
        method="grabber",
        surprise="sticker",
        child_name="Theo",
        child_gender="boy",
        adult="mother",
        bot_name="Dot",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a ledge, a helpful bot, and a funny surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=ADULT_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--bot-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and args.item:
        item = ITEMS[args.item]
        method = METHODS[args.method]
        if not method_works(item, method):
            raise StoryError(explain_rejection(item, method))
    if args.place and args.item and args.item not in PLACES[args.place].affords:
        raise StoryError(
            f"(No story: {ITEMS[args.item].phrase} does not belong in {PLACES[args.place].label} for this tiny world.)"
        )

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.item is None or c[1] == args.item)
        and (args.method is None or c[2] == args.method)
        and (args.surprise is None or c[3] == args.surprise)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item, method, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or PLACES[place].adult_here
    bot_name = args.bot_name or rng.choice(BOT_NAMES)
    return StoryParams(
        place=place,
        item=item,
        method=method,
        surprise=surprise,
        child_name=name,
        child_gender=gender,
        adult=adult,
        bot_name=bot_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.surprise not in SURPRISES:
        raise StoryError(f"(Unknown surprise: {params.surprise})")
    if params.item not in PLACES[params.place].affords:
        raise StoryError(
            f"(No story: {ITEMS[params.item].phrase} is not used in {PLACES[params.place].label} here.)"
        )
    if not method_works(ITEMS[params.item], METHODS[params.method]):
        raise StoryError(explain_rejection(ITEMS[params.item], METHODS[params.method]))

    world = tell(
        place=PLACES[params.place],
        item_cfg=ITEMS[params.item],
        method=METHODS[params.method],
        surprise=SURPRISES[params.surprise],
        child_name=params.child_name,
        child_type=params.child_gender,
        adult_type=params.adult,
        bot_name=params.bot_name,
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("(Default generation did not populate all result fields.)")
        print("OK: default generate() path succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, method, surprise) combos:\n")
        for place, item, method, surprise in combos:
            print(f"  {place:10} {item:9} {method:8} {surprise}")
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
            header = f"### {p.child_name}: {p.item} on a ledge in {p.place} ({p.method}, {p.surprise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
