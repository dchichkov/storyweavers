#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py
=======================================================================================

A standalone storyworld for a fairy-tale domain about a child, a stormy shutter,
a tempting look outside, and the kind supervision that turns trouble into wisdom.

The seed asked for:
- words: shutter, splash, supervision
- features: Inner Monologue, Magic, Kindness
- style: Fairy Tale

This world models a small enchanted cottage or tower where a child longs to open
a shutter during magical weather. If the child waits for supervision, the moment
stays gentle and safe. If the child acts alone, wind and rain can splash onto a
delicate treasure by the window, and a kind grown-up answers with help rather than
anger. Some remedies are sensible and strong enough; weak ones are known but
refused by the reasonableness gate.

Run it
------
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py --wonder silver_rain --prize star_map
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py --prize pebble_crown
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py --all
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/shutter_splash_supervision_inner_monologue_magic_kindness.py --verify
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
WAITING_TRAITS = {"patient", "gentle", "careful", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    vulnerable_to_splash: bool = False
    magical: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman", "fairy_godmother"}
        male = {"boy", "father", "wizard", "man", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "wizard": "wizard",
            "fairy_godmother": "godmother",
            "keeper": "keeper",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    room_detail: str
    outside_detail: str
    guardian_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    lure: str
    weather_word: str
    sight: str
    sound: str
    strength: int = 1
    wet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    damage: str
    restored: str
    splashable: bool = True
    magical: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    sense: int = 2
    power: int = 2
    text: str = ""
    fail: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting, wonder: Wonder) -> None:
        self.setting = setting
        self.wonder = wonder
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
        clone = World(self.setting, self.wonder)
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


def _r_shutter_splash(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    prize = world.get("prize")
    if room.meters["shutter_open"] < THRESHOLD:
        return out
    if not world.wonder.wet:
        return out
    sig = ("splash", world.wonder.id, prize.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["splash"] += 1
    child.memes["alarm"] += 1
    if prize.vulnerable_to_splash:
        prize.meters["wet"] += 1
        prize.meters["ruined"] += 1
        child.memes["regret"] += 1
        out.append("__splash__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="shutter_splash", tag="physical", apply=_r_shutter_splash),
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


def prize_at_risk(wonder: Wonder, prize: Prize) -> bool:
    return wonder.wet and prize.splashable


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def is_waiting_trait(trait: str) -> bool:
    return trait in WAITING_TRAITS


def outcome_of(params: "StoryParams") -> str:
    if is_waiting_trait(params.trait):
        return "supervised"
    remedy = REMEDIES[params.remedy]
    wonder = WONDERS[params.wonder]
    return "fixed" if remedy.power >= wonder.strength else "soggy"


def predict_splash(world: World) -> dict:
    sim = world.copy()
    sim.get("room").meters["shutter_open"] += 1
    propagate(sim, narrate=False)
    prize = sim.get("prize")
    return {
        "splash": sim.get("room").meters["splash"] >= THRESHOLD,
        "ruined": prize.meters["ruined"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, guardian: Entity, prize: Entity) -> None:
    world.say(
        f"Once, in {world.setting.place}, there lived {child.id}, a little {child.type} "
        f"with bright wondering eyes. {world.setting.room_detail}"
    )
    world.say(
        f"Beside the window rested {prize.phrase}, and {child.id} loved it as if a "
        f"small blessing had been sewn into every edge."
    )
    child.memes["love"] += 1
    prize.memes["cherished"] += 1
    world.say(
        f"{guardian.label_word.capitalize()} {guardian.id} watched over the room with "
        f"kind supervision, never harsh and never far away."
    )


def tempting_weather(world: World, child: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"That evening, {world.wonder.sight} passed beyond the shutter, and "
        f"{world.wonder.sound}. {world.setting.outside_detail}"
    )
    world.say(
        f"{child.id} pressed close to the wall and whispered inside {child.pronoun('possessive')} "
        f"own heart, \"If I open the shutter just a little, I might see {world.wonder.lure} better.\""
    )


def warning(world: World, child: Entity, guardian: Entity, prize: Entity) -> None:
    pred = predict_splash(world)
    world.facts["predicted_ruined"] = pred["ruined"]
    world.facts["predicted_splash"] = pred["splash"]
    child.memes["caution"] += 1
    world.say(
        f"But another thought fluttered after it: \"What if the rain sends a splash onto "
        f"my {prize.label}?\""
    )
    if pred["ruined"]:
        world.say(
            f"{guardian.id} noticed the wondering face and said softly, "
            f"\"Little one, wait for supervision before you touch the shutter. "
            f"The storm is lively tonight, and {prize.phrase} could be spoiled.\""
        )


def ask_for_help(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{child.id} folded small fingers together and listened to the better thought. "
        f"\"I will ask first,\" {child.pronoun()} decided."
    )
    world.say(
        f"Then {child.pronoun()} called, \"{guardian.id}, will you come with me? "
        f"I want to look, but I want supervision too.\""
    )


def supervised_open(world: World, child: Entity, guardian: Entity, prize: Entity) -> None:
    room = world.get("room")
    room.meters["shutter_open"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{guardian.id} came at once and smiled, pleased by the careful choice. "
        f"Together they moved {prize.phrase} back from the sill."
    )
    world.say(
        f"Only then did {guardian.pronoun()} lift the shutter a crack. Cool silver air "
        f"slipped in, but no wild splash could reach the treasure."
    )
    world.say(
        f"{child.id} saw {world.wonder.lure} shining outside and thought, "
        f"\"Waiting did not steal the wonder. It kept the wonder gentle.\""
    )


def sneak_open(world: World, child: Entity, prize: Entity) -> None:
    room = world.get("room")
    room.meters["shutter_open"] += 1
    child.memes["impulse"] += 1
    world.say(
        f"But wonder tugged too hard. {child.id} reached up, touched the shutter latch, "
        f"and pushed it open alone."
    )
    propagate(world, narrate=False)
    if prize.meters["ruined"] >= THRESHOLD:
        world.say(
            f"At once a cold splash leapt through the window and kissed {prize.phrase}. "
            f"{prize.label.capitalize()} {prize.damage}."
        )
        world.say(
            f"{child.id}'s heart dropped. \"Oh no,\" {child.pronoun()} thought. "
            f"\"I wanted beauty, and I brought trouble instead.\""
        )


def call_guardian(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"{child.id} did not hide. {child.pronoun().capitalize()} called for {guardian.id} at once, "
        f"voice trembling but truthful."
    )
    world.say(
        f"{guardian.id} hurried over, not with anger, but with a face full of concern and kindness."
    )


def repair(world: World, child: Entity, guardian: Entity, prize: Entity, remedy: Remedy) -> None:
    prize.meters["wet"] = 0.0
    prize.meters["ruined"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    child.memes["love"] += 1
    world.say(
        f"{guardian.id} wrapped one arm around {child.id} and {remedy.text.replace('{prize}', prize.label)}."
    )
    world.say(
        f"Soon {prize.restored}, and the room felt warm again. "
        f"\"Magic is brightest when it walks beside kindness,\" {guardian.pronoun()} said."
    )


def repair_fail(world: World, child: Entity, guardian: Entity, prize: Entity, remedy: Remedy) -> None:
    child.memes["sadness"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"{guardian.id} tried {remedy.fail.replace('{prize}', prize.label)}, but the storm had been too rough."
    )
    world.say(
        f"{prize.label.capitalize()} stayed {prize.damage}, and a little silence sat between them like a damp bird."
    )
    world.say(
        f"Still, {guardian.id} kissed the top of {child.id}'s head and said, "
        f"\"The treasure can be mourned, little one, but you told the truth, and that matters.\""
    )


def closing_safe(world: World, child: Entity, guardian: Entity) -> None:
    world.say(
        f"Later, they watched the weather together by candle glow, the shutter resting half closed "
        f"under loving supervision."
    )
    world.say(
        f"And whenever {child.id} heard rain whisper at the window after that, "
        f"{child.pronoun()} remembered that asking first could keep both wonder and peace."
    )


def closing_soggy(world: World, child: Entity, guardian: Entity) -> None:
    world.say(
        f"That night the storm sang on outside the shutter, but inside the lesson stayed longer than the rain."
    )
    world.say(
        f"From then on, {child.id} sought supervision before opening any window to the weather, "
        f"and kindness made the memory bearable."
    )


def tell(
    setting: Setting,
    wonder: Wonder,
    prize_cfg: Prize,
    remedy: Remedy,
    *,
    child_name: str = "Lina",
    child_type: str = "girl",
    guardian_name: str = "Mara",
    guardian_type: str = "mother",
    trait: str = "patient",
) -> World:
    world = World(setting=setting, wonder=wonder)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        traits=[trait],
        role="child",
        magical=False,
    ))
    guardian = world.add(Entity(
        id=guardian_name,
        kind="character",
        type=guardian_type,
        label=guardian_name,
        traits=["kind"],
        role="guardian",
        magical=True,
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        vulnerable_to_splash=prize_cfg.splashable,
        magical=prize_cfg.magical,
        tags=set(prize_cfg.tags),
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label="room",
        phrase="the little room by the window",
    ))

    introduce(world, child, guardian, prize)
    tempting_weather(world, child)

    world.para()
    warning(world, child, guardian, prize)

    if is_waiting_trait(trait):
        ask_for_help(world, child, guardian)
        world.para()
        supervised_open(world, child, guardian, prize)
        outcome = "supervised"
    else:
        sneak_open(world, child, prize)
        world.para()
        call_guardian(world, child, guardian)
        if remedy.power >= wonder.strength:
            repair(world, child, guardian, prize, remedy)
            outcome = "fixed"
        else:
            repair_fail(world, child, guardian, prize, remedy)
            outcome = "soggy"

    world.para()
    if outcome in {"supervised", "fixed"}:
        closing_safe(world, child, guardian)
    else:
        closing_soggy(world, child, guardian)

    world.facts.update(
        child=child,
        guardian=guardian,
        prize=prize,
        prize_cfg=prize_cfg,
        remedy=remedy,
        wonder=wonder,
        setting=setting,
        outcome=outcome,
        supervised=(outcome == "supervised"),
        restored=(outcome == "fixed"),
        truth_told=(child.memes["honesty"] >= THRESHOLD),
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a moss-roofed cottage at the edge of the wood",
        opening="a round window with blue shutters",
        room_detail="A round window with blue shutters looked toward the brook, and rosemary hung drying from the beams.",
        outside_detail="The brook below made the whole garden gleam.",
        guardian_title="mother",
        tags={"cottage"},
    ),
    "tower": Setting(
        id="tower",
        place="a little moon tower above the sleeping village",
        opening="a tall arched window with pearl shutters",
        room_detail="A tall arched window with pearl shutters watched the clouds, and soft lamplight trembled over stone steps.",
        outside_detail="Far below, rooftops shone like coins in a wishing bowl.",
        guardian_title="keeper",
        tags={"tower"},
    ),
    "bakery": Setting(
        id="bakery",
        place="a cinnamon-sweet bakery cottage near the square",
        opening="a square window with cherry-red shutters",
        room_detail="A square window with cherry-red shutters faced the lane, and the air smelled of bread and honey.",
        outside_detail="The cobbles outside sparkled as if someone had sprinkled them with sugar.",
        guardian_title="father",
        tags={"bakery"},
    ),
}

WONDERS = {
    "silver_rain": Wonder(
        id="silver_rain",
        lure="silver rain threading the twilight like tiny strings of pearls",
        weather_word="rain",
        sight="Silver rain came sweeping down in shining slants",
        sound="the drops tapped a small drum-song on the roof",
        strength=2,
        wet=True,
        tags={"rain", "splash"},
    ),
    "frog_parade": Wonder(
        id="frog_parade",
        lure="a parade of frog princes splashing in puddles below",
        weather_word="rain",
        sight="Below the window, little frogs in leaf-caps hopped through the wet garden path",
        sound="their puddles answered with a merry splash after splash",
        strength=1,
        wet=True,
        tags={"frogs", "splash", "rain"},
    ),
    "storm_rainbow": Wonder(
        id="storm_rainbow",
        lure="the storm rainbow trying to grow out of the clouds",
        weather_word="storm",
        sight="A storm rainbow bent and unbent across the dark sky",
        sound="wind rattled the latch and the rain ran quick along the sill",
        strength=3,
        wet=True,
        tags={"rainbow", "storm", "splash"},
    ),
    "fireflies": Wonder(
        id="fireflies",
        lure="the green fireflies sewing lantern-light through the dusk",
        weather_word="night",
        sight="Fireflies rose among the mint leaves like tiny floating stars",
        sound="the evening stayed mild and full of crickets",
        strength=0,
        wet=False,
        tags={"fireflies"},
    ),
}

PRIZES = {
    "star_map": Prize(
        id="star_map",
        label="star map",
        phrase="a paper star map painted with gold dots",
        damage="curled and ran with little golden tears",
        restored="the star map lay flat again, its golden dots shining bravely",
        splashable=True,
        magical=True,
        tags={"paper", "map"},
    ),
    "sugar_bird": Prize(
        id="sugar_bird",
        label="sugar bird",
        phrase="a spun-sugar bird from the spring fair",
        damage="softened and bent at the wings",
        restored="the sugar bird stood bright and crisp again on its little stand",
        splashable=True,
        magical=True,
        tags={"sugar"},
    ),
    "moon_scarf": Prize(
        id="moon_scarf",
        label="moon scarf",
        phrase="a moon-thread scarf that glimmered pale blue",
        damage="drooped heavy and dim against the sill",
        restored="the moon scarf shimmered dry and light once more",
        splashable=True,
        magical=True,
        tags={"cloth"},
    ),
    "pebble_crown": Prize(
        id="pebble_crown",
        label="pebble crown",
        phrase="a pebble crown polished by the brook",
        damage="only glittered a little wetter than before",
        restored="the pebble crown looked exactly as it always had",
        splashable=False,
        magical=False,
        tags={"stone"},
    ),
}

REMEDIES = {
    "sun_thread": Remedy(
        id="sun_thread",
        sense=3,
        power=3,
        text="drew a warm sun-thread charm through the air and dried the {prize} from edge to edge",
        fail="to spin a sun-thread charm over the {prize}",
        qa_text="used a warm sun-thread charm to dry it",
        tags={"magic", "drying"},
    ),
    "hearth_breath": Remedy(
        id="hearth_breath",
        sense=2,
        power=2,
        text="breathed a hearth-warm spell across the {prize} until every drop vanished",
        fail="to breathe a hearth-warm spell over the {prize}",
        qa_text="breathed a hearth-warm spell over it until it dried",
        tags={"magic", "hearth"},
    ),
    "window_song": Remedy(
        id="window_song",
        sense=2,
        power=1,
        text="sang a window song so softly that the {prize} dried under the tune",
        fail="to sing a window song for the {prize}",
        qa_text="sang a soft window song to help it dry",
        tags={"magic", "song"},
    ),
    "apron_dab": Remedy(
        id="apron_dab",
        sense=1,
        power=1,
        text="dabbed the {prize} with an apron corner",
        fail="to dab the {prize} with an apron corner",
        qa_text="dabbed it with an apron corner",
        tags={"cloth"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nora", "Ivy", "Wren", "Ada", "Poppy"]
BOY_NAMES = ["Rowan", "Milo", "Tobin", "Eli", "Finn", "Theo", "Bram", "Leo"]
TRAITS = ["patient", "gentle", "careful", "thoughtful", "curious", "restless", "eager", "impulsive"]


@dataclass
class StoryParams:
    setting: str
    wonder: str
    prize: str
    remedy: str
    child_name: str
    child_type: str
    guardian_name: str
    guardian_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "shutter": [(
        "What is a shutter?",
        "A shutter is a solid cover on the outside or inside of a window. You can open it to let in light or close it to help keep out weather."
    )],
    "supervision": [(
        "What does supervision mean?",
        "Supervision means a careful grown-up is nearby and paying attention. It helps children stay safe when something looks tempting or tricky."
    )],
    "splash": [(
        "What is a splash?",
        "A splash is what happens when water jumps or scatters quickly. A splash can make nearby things wet in only a moment."
    )],
    "rain": [(
        "Why can rain hurt paper things?",
        "Paper drinks up water very fast and can wrinkle or tear when it gets wet. That is why a paper treasure should be kept away from rain."
    )],
    "magic": [(
        "What is magic in a fairy tale?",
        "Magic in a fairy tale is a special power that can change how things happen. Good magic is often joined with wisdom and kindness."
    )],
    "kindness": [(
        "What does kindness look like when someone makes a mistake?",
        "Kindness means helping without being cruel. A kind grown-up can correct a mistake and still make a child feel safe enough to tell the truth."
    )],
    "truth": [(
        "Why is it good to tell the truth after an accident?",
        "Telling the truth helps grown-ups understand what happened and help quickly. It also shows courage, even when you feel worried."
    )],
    "rainbow": [(
        "What is a rainbow?",
        "A rainbow is a band of colors that can appear when light shines through water in the air. It often comes after or during rain."
    )],
    "fireflies": [(
        "What are fireflies?",
        "Fireflies are little insects that glow with their own light. In stories they can look like living lanterns."
    )],
}
KNOWLEDGE_ORDER = [
    "shutter",
    "supervision",
    "splash",
    "rain",
    "magic",
    "kindness",
    "truth",
    "rainbow",
    "fireflies",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for wonder_id, wonder in WONDERS.items():
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(wonder, prize):
                    combos.append((setting_id, wonder_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    wonder = f["wonder"]
    prize_cfg = f["prize_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short fairy-tale story for a 3-to-5-year-old that uses the words '
        f'"shutter", "splash", and "supervision", and includes inner monologue, magic, and kindness.'
    )
    if outcome == "supervised":
        return [
            base,
            f"Tell a gentle fairy tale where {child.id} wants to open a shutter to see {wonder.lure}, "
            f"but chooses to ask {guardian.id} for supervision first and keeps {prize_cfg.phrase} safe.",
            f"Write a magical bedtime story where a child listens to an inner voice, waits for help, "
            f"and learns that caution can protect wonder instead of spoiling it.",
        ]
    if outcome == "fixed":
        return [
            base,
            f"Tell a fairy tale where {child.id} opens the shutter alone, a splash ruins {prize_cfg.phrase}, "
            f"and {guardian.id} answers with a kind magical repair instead of anger.",
            f"Write a story where a child makes a mistake because of curiosity, tells the truth, "
            f"and a loving grown-up uses magic and kindness to mend both the object and the child's feelings.",
        ]
    return [
        base,
        f"Tell a sadder fairy tale where {child.id} opens the shutter alone during {wonder.weather_word}, "
        f"a splash damages {prize_cfg.phrase}, and even a kind magical remedy cannot fully mend it.",
        f"Write a story that teaches why supervision matters when a child is tempted by beautiful weather at the window.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    prize = f["prize_cfg"]
    wonder = f["wonder"]
    remedy = f["remedy"]
    outcome = f["outcome"]
    guardian_word = guardian.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a little {child.type}, and {guardian.id}, the kind {guardian_word} who watches over {child.pronoun('object')}. "
            f"Their story begins beside a window and a cherished {prize.label}."
        ),
        (
            "What tempted the child?",
            f"{child.id} wanted to open the shutter to see {wonder.lure} more clearly. "
            f"The beauty outside made the risky choice feel small and easy at first."
        ),
        (
            "What was the child thinking inside?",
            f"{child.id} had an inner monologue about opening the shutter just a little. "
            f"Another thought warned that a splash might reach the {prize.label}, so the child felt torn between wonder and caution."
        ),
    ]
    if outcome == "supervised":
        qa.append((
            "Why did nothing get ruined?",
            f"Nothing was ruined because {child.id} asked for supervision before touching the shutter. "
            f"{guardian.id} helped move the {prize.label} away first, so the weather could not reach it."
        ))
        qa.append((
            "What lesson did the child learn?",
            f"{child.id} learned that waiting for help did not make the magical moment smaller. "
            f"It made the moment safer and kinder, so wonder and peace could stay together."
        ))
    elif outcome == "fixed":
        qa.append((
            "What happened when the child opened the shutter alone?",
            f"A splash came through the window and the {prize.label} {prize.damage}. "
            f"The trouble happened because the child acted before asking for supervision."
        ))
        qa.append((
            "How did the grown-up respond?",
            f"{guardian.id} responded with kindness and {remedy.qa_text}. "
            f"{guardian.pronoun().capitalize()} also comforted {child.id}, so the child learned without feeling cast away."
        ))
        qa.append((
            "Why was telling the truth important?",
            f"Telling the truth let {guardian.id} hurry in and help right away. "
            f"It also turned the mistake into a lesson about honesty as well as caution."
        ))
    else:
        qa.append((
            "Could the treasure be fully mended?",
            f"No. {guardian.id} tried to help, but the storm had been too rough and the {prize.label} stayed damaged. "
            f"That sad ending shows why waiting for supervision matters."
        ))
        qa.append((
            "Was the grown-up cruel?",
            f"No. {guardian.id} stayed kind even though the object was lost. "
            f"The comfort mattered because the child had already learned the cost of the mistake."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"shutter", "supervision", "splash", "magic", "kindness"}
    wonder = world.facts["wonder"]
    if "rain" in wonder.tags or "storm" in wonder.tags:
        tags.add("rain")
    if "rainbow" in wonder.tags:
        tags.add("rainbow")
    if "fireflies" in wonder.tags:
        tags.add("fireflies")
    if world.facts["truth_told"]:
        tags.add("truth")
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.vulnerable_to_splash:
            bits.append("vulnerable_to_splash=True")
        if ent.magical:
            bits.append("magical=True")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  outcome: {world.facts.get('outcome')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        wonder="silver_rain",
        prize="star_map",
        remedy="hearth_breath",
        child_name="Lina",
        child_type="girl",
        guardian_name="Mara",
        guardian_type="mother",
        trait="patient",
    ),
    StoryParams(
        setting="tower",
        wonder="frog_parade",
        prize="sugar_bird",
        remedy="window_song",
        child_name="Rowan",
        child_type="boy",
        guardian_name="Hollis",
        guardian_type="keeper",
        trait="curious",
    ),
    StoryParams(
        setting="bakery",
        wonder="storm_rainbow",
        prize="moon_scarf",
        remedy="sun_thread",
        child_name="Mira",
        child_type="girl",
        guardian_name="Tomas",
        guardian_type="father",
        trait="eager",
    ),
    StoryParams(
        setting="tower",
        wonder="storm_rainbow",
        prize="star_map",
        remedy="hearth_breath",
        child_name="Theo",
        child_type="boy",
        guardian_name="Seren",
        guardian_type="wizard",
        trait="impulsive",
    ),
]


def explain_rejection(wonder: Wonder, prize: Prize) -> str:
    if not wonder.wet:
        return (
            f"(No story: {wonder.id} is lovely, but it sends no wet splash through the window, "
            f"so {prize.phrase} is not truly at risk. Pick a rainy wonder instead.)"
        )
    if not prize.splashable:
        return (
            f"(No story: {prize.phrase} would not really be harmed by a splash, "
            f"so there is no honest problem for supervision to solve.)"
        )
    return "(No story: this combination does not create a real splash risk.)"


def explain_remedy(rid: str) -> str:
    remedy = REMEDIES[rid]
    better = ", ".join(sorted(r.id for r in sensible_remedies()))
    return (
        f"(Refusing remedy '{rid}': it scores too low on common sense "
        f"(sense={remedy.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
risk(W, P) :- wet(W), splashable(P).
sensible(R) :- remedy(R), sense(R, S), sense_min(M), S >= M.
valid(S, W, P) :- setting(S), wonder(W), prize(P), risk(W, P).

% --- outcome model ---------------------------------------------------------
waiting_trait(T) :- trait_name(T), patient_like(T).
outcome(supervised) :- chosen_trait(T), waiting_trait(T).

fixed_enough :- chosen_remedy(R), power(R, P), chosen_wonder(W), strength(W, S), P >= S.

outcome(fixed) :- chosen_trait(T), not waiting_trait(T), fixed_enough.
outcome(soggy) :- chosen_trait(T), not waiting_trait(T), not fixed_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for wonder_id, wonder in WONDERS.items():
        lines.append(asp.fact("wonder", wonder_id))
        lines.append(asp.fact("strength", wonder_id, wonder.strength))
        if wonder.wet:
            lines.append(asp.fact("wet", wonder_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        if prize.splashable:
            lines.append(asp.fact("splashable", prize_id))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(WAITING_TRAITS):
        lines.append(asp.fact("patient_like", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
        asp.fact("chosen_trait", params.trait),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("chosen_wonder", params.wonder),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_remedies()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible remedies match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible remedies: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    parser = build_parser()
    cases: list[StoryParams] = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child, a shutter, a splash, supervision, and kind magic."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--guardian", choices=["mother", "father", "keeper", "wizard", "fairy_godmother"])
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.prize and args.wonder:
        wonder = WONDERS[args.wonder]
        prize = PRIZES[args.prize]
        if not prize_at_risk(wonder, prize):
            raise StoryError(explain_rejection(wonder, prize))
    if args.prize and not args.wonder and not PRIZES[args.prize].splashable:
        wonder = next(iter(WONDERS.values()))
        raise StoryError(explain_rejection(wonder, PRIZES[args.prize]))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(explain_remedy(args.remedy))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.wonder is None or combo[1] == args.wonder)
        and (args.prize is None or combo[2] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, wonder_id, prize_id = rng.choice(sorted(combos))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    guardian_type = args.guardian or rng.choice(["mother", "father", "keeper", "wizard", "fairy_godmother"])
    guardian_name = rng.choice(["Mara", "Tomas", "Seren", "Juniper", "Hollis", "Elowen", "Bramble", "Aster"])
    if guardian_name == child_name:
        guardian_name = guardian_name + " the Elder"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        wonder=wonder_id,
        prize=prize_id,
        remedy=remedy_id,
        child_name=child_name,
        child_type=child_type,
        guardian_name=guardian_name,
        guardian_type=guardian_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        wonder = WONDERS[params.wonder]
        prize = PRIZES[params.prize]
        remedy = REMEDIES[params.remedy]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]!r})") from None
    if not prize_at_risk(wonder, prize):
        raise StoryError(explain_rejection(wonder, prize))
    if remedy.sense < SENSE_MIN:
        raise StoryError(explain_remedy(params.remedy))

    world = tell(
        setting=setting,
        wonder=wonder,
        prize_cfg=prize,
        remedy=remedy,
        child_name=params.child_name,
        child_type=params.child_type,
        guardian_name=params.guardian_name,
        guardian_type=params.guardian_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, wonder, prize) combos:\n")
        for setting_id, wonder_id, prize_id in combos:
            print(f"  {setting_id:8} {wonder_id:14} {prize_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.wonder} at {p.setting} "
                f"(prize: {p.prize}, remedy: {p.remedy}, outcome: {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
