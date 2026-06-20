#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anchor_fuzzy_moss_crystal_lighthouse_kitchen_twist_2.py
===================================================================================

A standalone storyworld built from the seed:

    Words: anchor, fuzzy moss, crystal lighthouse
    Setting: kitchen
    Features: Twist
    Style: Adventure

Internal source tale
--------------------
On a rainy afternoon, two children turn a cozy kitchen into a tiny ship. They
must find a missing supper prize before the soup is ready. A crystal lighthouse
on the counter looks like the obvious treasure box, and a rushed shortcut would
be to pry, shake, or rake through the clues. Instead, the children stay gentle.
The lighthouse throws a beam onto an anchor marker, the anchor points toward a
patch of fuzzy moss, and the real prize waits there. The twist is that the
crystal lighthouse was never a box to open. It was the map.
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
from typing import Callable, Iterable, Optional

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
    location: str = ""
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Event:
    id: str
    text: str
    details: dict[str, str] = field(default_factory=dict)


@dataclass
class Kitchen:
    id: str
    phrase: str
    weather: str
    counter: str
    mood: str
    routes: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Crew:
    id: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    phrase: str
    pledge: str
    care: int
    tags: set[str] = field(default_factory=set)


@dataclass
class CrystalLighthouse:
    id: str
    label: str
    phrase: str
    lens: str
    beam: str
    hint: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MossPatch:
    id: str
    label: str
    phrase: str
    area: str
    texture: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnchorMark:
    id: str
    label: str
    phrase: str
    place: str
    use: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    temptation: str
    thought: str
    target: str
    damage: str
    consequence: str
    safe_choice: str
    lure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    apparent: str
    prize: str
    truth: str
    reveal: str
    ending: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], None]


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.fired: set[tuple[str, str]] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

    def note(self, event_id: str, text: str, **details: str) -> None:
        self.history.append(Event(event_id, text, details))

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.kitchen)
        clone.entities = copy.deepcopy(self.entities)
        clone.history = copy.deepcopy(self.history)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def trace(self) -> str:
        lines = ["--- world trace ---"]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            bits = []
            if ent.location:
                bits.append(f"location={ent.location}")
            if meters:
                bits.append(f"meters={dict(meters)}")
            if memes:
                bits.append(f"memes={dict(memes)}")
            lines.append(f"  {ent.id:12} ({ent.type:18}) {' '.join(bits)}")
        lines.append("  events:")
        for event in self.history:
            lines.append(f"    - {event.id}: {event.text}")
        lines.append(f"  fired rules: {sorted({name for name, _ in self.fired})}")
        return "\n".join(lines)


def _r_notice_hurry(world: World) -> None:
    hero = world.get("hero")
    shortcut = world.get("shortcut")
    sig = ("notice_hurry", shortcut.id)
    if shortcut.meters["noticed"] < THRESHOLD or sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["hurry"] += shortcut.meters["lure"]


def _r_read_lighthouse(world: World) -> None:
    hero = world.get("hero")
    lighthouse = world.get("lighthouse")
    sig = ("read_lighthouse", lighthouse.id)
    if lighthouse.meters["turned"] < THRESHOLD:
        return
    if lighthouse.meters["cracked"] >= THRESHOLD:
        return
    if sig in world.fired:
        return
    world.fired.add(sig)
    lighthouse.meters["guiding"] += 1
    hero.memes["insight"] += 1


def _r_choose_steady(world: World) -> None:
    hero = world.get("hero")
    shortcut = world.get("shortcut")
    sig = ("choose_steady", hero.id)
    if hero.memes["insight"] < THRESHOLD:
        return
    if shortcut.meters["noticed"] < THRESHOLD:
        return
    if hero.memes["care"] < shortcut.meters["lure"]:
        return
    if sig in world.fired:
        return
    world.fired.add(sig)
    hero.memes["steady"] += 1


def _r_light_anchor(world: World) -> None:
    hero = world.get("hero")
    lighthouse = world.get("lighthouse")
    anchor = world.get("anchor")
    sig = ("light_anchor", anchor.id)
    if lighthouse.meters["guiding"] < THRESHOLD:
        return
    if hero.memes["steady"] < THRESHOLD:
        return
    if lighthouse.attrs["key"] != anchor.attrs["key"]:
        return
    if sig in world.fired:
        return
    world.fired.add(sig)
    anchor.meters["lit"] += 1


def _r_find_prize(world: World) -> None:
    anchor = world.get("anchor")
    moss = world.get("moss")
    prize = world.get("prize")
    hero = world.get("hero")
    team = world.get("team")
    sig = ("find_prize", prize.id)
    if anchor.meters["lit"] < THRESHOLD:
        return
    if moss.meters["lifted"] < THRESHOLD:
        return
    if anchor.attrs["key"] != moss.attrs["key"] or moss.attrs["key"] != prize.attrs["key"]:
        return
    if sig in world.fired:
        return
    world.fired.add(sig)
    prize.meters["found"] += 1
    hero.memes["wonder"] += 1
    team.memes["relief"] += 1


RULES = [
    Rule("notice_hurry", _r_notice_hurry),
    Rule("read_lighthouse", _r_read_lighthouse),
    Rule("choose_steady", _r_choose_steady),
    Rule("light_anchor", _r_light_anchor),
    Rule("find_prize", _r_find_prize),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        fired_before = len(world.fired)
        for rule in RULES:
            rule.apply(world)
        if len(world.fired) != fired_before:
            changed = True


KITCHENS = {
    "rainy_window": Kitchen(
        "rainy_window",
        "Grandma's kitchen by the rainy window",
        "Rain tapped the glass in silver dots",
        "the blue-striped counter",
        "a brave little ship cabin",
        {"window_blue", "pantry_gold"},
        tags={"kitchen", "adventure", "rain"},
    ),
    "warm_stove": Kitchen(
        "warm_stove",
        "the kitchen beside the warm stove",
        "The soup pot purred while golden steam curled upward",
        "the bread board near the stove",
        "a bright harbor galley",
        {"stove_amber", "sink_green"},
        tags={"kitchen", "adventure", "warmth"},
    ),
    "pantry_cove": Kitchen(
        "pantry_cove",
        "the kitchen by the pantry door",
        "The kettle hummed like a faraway harbor bell",
        "the flour-dusted table",
        "a snug treasure cove",
        {"pantry_gold", "window_blue"},
        tags={"kitchen", "adventure", "harbor"},
    ),
}


CREWS = {
    "mara_theo": Crew(
        "mara_theo",
        "Mara",
        "girl",
        "Theo",
        "boy",
        "two careful galley explorers",
        '"Gentle hands first, fast hands last," they always said.',
        4,
        tags={"care", "adventure"},
    ),
    "niko_bea": Crew(
        "niko_bea",
        "Niko",
        "boy",
        "Bea",
        "girl",
        "two bold pantry sailors",
        '"A true captain watches before grabbing," they reminded each other.',
        5,
        tags={"care", "adventure"},
    ),
    "poppy_sol": Crew(
        "poppy_sol",
        "Poppy",
        "girl",
        "Sol",
        "boy",
        "two eager snack-deck scouts",
        '"We can be quick after we are wise," they promised.',
        3,
        tags={"care", "adventure"},
    ),
    "jude_ava": Crew(
        "jude_ava",
        "Jude",
        "boy",
        "Ava",
        "girl",
        "two kitchen quest mates",
        '"We keep the clues safe so the clues can help us," they liked to say.',
        4,
        tags={"care", "adventure"},
    ),
}


LIGHTHOUSES = {
    "window_lighthouse": CrystalLighthouse(
        "window_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with a blue roof and tiny clear windows",
        "the blue roof",
        "blue beam",
        "The little beam is asking us to look away from the tower.",
        "window_blue",
        tags={"crystal", "lighthouse", "blue"},
    ),
    "pantry_lighthouse": CrystalLighthouse(
        "pantry_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with a gold lantern cap",
        "the gold lantern cap",
        "gold beam",
        "The light keeps sailing toward the pantry side of the room.",
        "pantry_gold",
        tags={"crystal", "lighthouse", "gold"},
    ),
    "stove_lighthouse": CrystalLighthouse(
        "stove_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with an amber door and a bright top",
        "the amber door",
        "amber beam",
        "The glow is drifting toward the warm side of the kitchen.",
        "stove_amber",
        tags={"crystal", "lighthouse", "amber"},
    ),
    "sink_lighthouse": CrystalLighthouse(
        "sink_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with a green glass ring",
        "the green glass ring",
        "green beam",
        "The beam keeps slipping toward the sink as if it knows a secret there.",
        "sink_green",
        tags={"crystal", "lighthouse", "green"},
    ),
}


MOSS_PATCHES = {
    "window_moss": MossPatch(
        "window_moss",
        "the fuzzy moss",
        "the fuzzy moss around the tiny fern boat",
        "the fern boat by the window ledge",
        "soft and cool like a damp pillow",
        "window_blue",
        tags={"moss", "window", "soft"},
    ),
    "pantry_moss": MossPatch(
        "pantry_moss",
        "the fuzzy moss",
        "the fuzzy moss beside the flour jar",
        "the pantry shelf beside the flour jar",
        "thick and springy like velvet grass",
        "pantry_gold",
        tags={"moss", "pantry", "soft"},
    ),
    "stove_moss": MossPatch(
        "stove_moss",
        "the fuzzy moss",
        "the fuzzy moss around the basil cup",
        "the basil cup by the stove",
        "warm and fluffy like a tiny blanket",
        "stove_amber",
        tags={"moss", "stove", "soft"},
    ),
    "sink_moss": MossPatch(
        "sink_moss",
        "the fuzzy moss",
        "the fuzzy moss under the mint saucer",
        "the mint saucer beside the sink",
        "fresh and feathery like a green cloud",
        "sink_green",
        tags={"moss", "sink", "soft"},
    ),
}


ANCHORS = {
    "window_anchor": AnchorMark(
        "window_anchor",
        "the anchor magnet",
        "the anchor magnet",
        "the window latch",
        "it pointed toward the fern boat like a harbor sign",
        "window_blue",
        tags={"anchor", "window"},
    ),
    "pantry_anchor": AnchorMark(
        "pantry_anchor",
        "the anchor hook",
        "the anchor hook",
        "the pantry frame",
        "it hung over the flour jar like a quiet arrow",
        "pantry_gold",
        tags={"anchor", "pantry"},
    ),
    "stove_anchor": AnchorMark(
        "stove_anchor",
        "the anchor cookie cutter",
        "the anchor cookie cutter",
        "the stove shelf",
        "it leaned toward the basil cup like a tiny captain's pointer",
        "stove_amber",
        tags={"anchor", "stove"},
    ),
    "sink_anchor": AnchorMark(
        "sink_anchor",
        "the anchor spoon rest",
        "the anchor spoon rest",
        "the sink tiles",
        "it sat by the mint saucer like a sign for safe landing",
        "sink_green",
        tags={"anchor", "sink"},
    ),
}


SHORTCUTS = {
    "pry_lens": Shortcut(
        "pry_lens",
        "prying at the crystal lighthouse lens",
        "pop open the crystal lighthouse and peek inside right away",
        '"Maybe the prize is trapped in the tower,"',
        "lighthouse",
        "cracked",
        "the crystal lighthouse would crack and lose its guiding light.",
        "They left the crystal lighthouse whole and useful.",
        4,
        tags={"care", "crystal"},
    ),
    "shake_anchor": Shortcut(
        "shake_anchor",
        "shaking the anchor marker loose",
        "grab the anchor and wave it toward every shelf",
        '"Maybe the anchor is the treasure, and we should snatch it first,"',
        "anchor",
        "moved",
        "the anchor would stop marking the right place.",
        "They let the anchor stay still enough to keep speaking.",
        3,
        tags={"care", "anchor"},
    ),
    "rake_moss": Shortcut(
        "rake_moss",
        "raking through the fuzzy moss in one sweep",
        "pull the fuzzy moss apart as fast as possible",
        '"Maybe the prize is under the fuzzy moss, and I can grab it in one swoop,"',
        "moss",
        "scattered",
        "the fuzzy moss would scatter and the hidden prize could slip deeper away.",
        "They kept the fuzzy moss neat until the clue was sure.",
        5,
        tags={"care", "moss"},
    ),
}


TWISTS = {
    "window_badge": Twist(
        "window_badge",
        "Grandma's moon-shaped spoon badge",
        "Grandma's moon-shaped spoon badge",
        "the crystal lighthouse was not a treasure chest at all; it was the map that led them to the prize",
        "The badge had been tucked into the soft moss so it would stay dry and quiet until someone followed the light.",
        "Grandma pinned the moon badge on the apron string and said the kitchen had found its best young captains.",
        "window_blue",
        tags={"twist", "badge", "window"},
    ),
    "pantry_map": Twist(
        "pantry_map",
        "the rolled snack-shelf map",
        "the rolled snack-shelf map",
        "the shining lighthouse was only a guide, and the real treasure was the little map sleeping under the moss",
        "The map had waited in the soft spot where no flour puff and no grabbing hand could spoil it.",
        "Soon the children followed the map to a high pantry shelf and found the snack chest smiling behind the jars.",
        "pantry_gold",
        tags={"twist", "map", "pantry"},
    ),
    "stove_token": Twist(
        "stove_token",
        "the supper bell token",
        "the supper bell token",
        "the crystal lighthouse was only the clue, while the anchor and moss kept the true prize safe",
        "Instead of opening the brightest thing in the kitchen, they let it point them to the quietest place.",
        "When the token tapped a spoon, everyone came to the table as if a harbor bell had called them home.",
        "stove_amber",
        tags={"twist", "token", "stove"},
    ),
    "sink_ring": Twist(
        "sink_ring",
        "the soup-stir ring",
        "the soup-stir ring",
        "the crystal lighthouse was the guide and not the goal, and the real prize had been resting under the moss all along",
        "The little ring had stayed hidden in the cool green nest until the beam and anchor agreed on the same spot.",
        "The soup-stir ring shone beside the ladle, and the whole kitchen seemed proud of its small brave secret.",
        "sink_green",
        tags={"twist", "ring", "sink"},
    ),
}


@dataclass
class StoryParams:
    kitchen: str
    crew: str
    lighthouse: str
    moss: str
    anchor: str
    shortcut: str
    twist: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "lighthouse": [
        QAItem(
            "What does a lighthouse do?",
            "A lighthouse helps guide travelers by sending out a bright signal. In a story, that guiding job can matter even more than holding treasure.",
        )
    ],
    "crystal": [
        QAItem(
            "Why can crystal make a bright little beam?",
            "Crystal can catch light and bend it in a new direction. That is why it can throw a sparkle or a beam across a room.",
        )
    ],
    "anchor": [
        QAItem(
            "What does an anchor usually help with?",
            "An anchor helps keep a boat from drifting away. In a pretend adventure, it can also act like a sign that marks the right spot.",
        )
    ],
    "moss": [
        QAItem(
            "Why is fuzzy moss a gentle hiding place?",
            "Fuzzy moss is soft, so it can cushion a tiny object without scratching it. It also makes a secret place look calm instead of flashy.",
        )
    ],
    "kitchen": [
        QAItem(
            "Why can a kitchen feel like an adventure place?",
            "A kitchen has shelves, tools, jars, sounds, and smells that spark imagination. A child can turn all of that into a ship, a harbor, or a treasure room.",
        )
    ],
    "care": [
        QAItem(
            "Why is carefulness part of adventure?",
            "Good adventurers do not only rush ahead. They protect clues and friends so the story can end in a true discovery instead of a broken mess.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lighthouse", "crystal", "anchor", "moss", "kitchen", "care"]


def route_matches(
    kitchen: Kitchen,
    lighthouse: CrystalLighthouse,
    moss: MossPatch,
    anchor: AnchorMark,
    twist: Twist,
) -> bool:
    return (
        lighthouse.key in kitchen.routes
        and lighthouse.key == moss.key == anchor.key == twist.key
    )


def crew_can_resist(crew: Crew, shortcut: Shortcut) -> bool:
    return crew.care >= shortcut.lure


def explain_rejection(
    kitchen: Kitchen,
    crew: Crew,
    lighthouse: CrystalLighthouse,
    moss: MossPatch,
    anchor: AnchorMark,
    shortcut: Shortcut,
    twist: Twist,
) -> str:
    if lighthouse.key not in kitchen.routes:
        return (
            f"(No story: {kitchen.phrase} does not give {lighthouse.label} a clear route. "
            "Pick a lighthouse whose beam belongs in that kitchen.)"
        )
    if lighthouse.key != moss.key or lighthouse.key != anchor.key or lighthouse.key != twist.key:
        return (
            "(No story: the crystal lighthouse, anchor, fuzzy moss, and twist do not all point to "
            "the same kitchen clue line.)"
        )
    if not crew_can_resist(crew, shortcut):
        return (
            f"(No story: {crew.hero_name} and {crew.helper_name} are not steady enough for "
            f"{shortcut.label}; choose a calmer crew or a gentler shortcut.)"
        )
    return "(No story: these parts do not make a reasonable kitchen adventure together.)"


def valid_params(params: StoryParams) -> tuple[bool, str]:
    kitchen = KITCHENS[params.kitchen]
    crew = CREWS[params.crew]
    lighthouse = LIGHTHOUSES[params.lighthouse]
    moss = MOSS_PATCHES[params.moss]
    anchor = ANCHORS[params.anchor]
    shortcut = SHORTCUTS[params.shortcut]
    twist = TWISTS[params.twist]
    if not route_matches(kitchen, lighthouse, moss, anchor, twist):
        return False, explain_rejection(kitchen, crew, lighthouse, moss, anchor, shortcut, twist)
    if not crew_can_resist(crew, shortcut):
        return False, explain_rejection(kitchen, crew, lighthouse, moss, anchor, shortcut, twist)
    return True, ""


def all_combos() -> list[tuple[str, str, str, str, str, str, str]]:
    combos = []
    for kitchen_id, kitchen in KITCHENS.items():
        for crew_id, crew in CREWS.items():
            for lighthouse_id, lighthouse in LIGHTHOUSES.items():
                for moss_id, moss in MOSS_PATCHES.items():
                    for anchor_id, anchor in ANCHORS.items():
                        for shortcut_id, shortcut in SHORTCUTS.items():
                            for twist_id, twist in TWISTS.items():
                                if route_matches(kitchen, lighthouse, moss, anchor, twist) and crew_can_resist(crew, shortcut):
                                    combos.append(
                                        (
                                            kitchen_id,
                                            crew_id,
                                            lighthouse_id,
                                            moss_id,
                                            anchor_id,
                                            shortcut_id,
                                            twist_id,
                                        )
                                    )
    return sorted(combos)


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str, str, str]]:
    combos = []
    for combo in all_combos():
        kitchen_id, crew_id, lighthouse_id, moss_id, anchor_id, shortcut_id, twist_id = combo
        if args.kitchen and args.kitchen != kitchen_id:
            continue
        if args.crew and args.crew != crew_id:
            continue
        if args.lighthouse and args.lighthouse != lighthouse_id:
            continue
        if args.moss and args.moss != moss_id:
            continue
        if args.anchor and args.anchor != anchor_id:
            continue
        if args.shortcut and args.shortcut != shortcut_id:
            continue
        if args.twist and args.twist != twist_id:
            continue
        combos.append(combo)
    return combos


def params_from_combo(combo: tuple[str, str, str, str, str, str, str], seed: int) -> StoryParams:
    kitchen, crew, lighthouse, moss, anchor, shortcut, twist = combo
    return StoryParams(kitchen, crew, lighthouse, moss, anchor, shortcut, twist, seed)


def predict_shortcut(world: World, shortcut: Shortcut) -> dict[str, object]:
    sim = world.copy()
    target = sim.get(shortcut.target)
    target.meters[shortcut.damage] += 1
    if shortcut.target == "lighthouse":
        target.meters["guiding"] = 0.0
    if shortcut.target == "anchor":
        target.meters["lit"] = 0.0
    if shortcut.target == "moss":
        target.meters["lifted"] = 0.0
        target.meters["scattered"] += 1
    prize = sim.get("prize")
    return {
        "blocked": shortcut.target in {"lighthouse", "anchor", "moss"},
        "target_label": target.label,
        "target_phrase": target.phrase or target.label,
        "damage": shortcut.damage,
        "consequence": shortcut.consequence,
        "prize_found": prize.meters["found"] >= THRESHOLD,
    }


def introduce(
    world: World,
    crew: Crew,
    kitchen: Kitchen,
    lighthouse: CrystalLighthouse,
    anchor: AnchorMark,
    moss: MossPatch,
) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    team = world.get("team")
    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    team.memes["mission"] += 1
    world.say(
        f"Once upon a time, {crew.hero_name} and {crew.helper_name} stood in {kitchen.phrase}. "
        f"{kitchen.weather}. The whole room felt like {kitchen.mood}."
    )
    world.say(
        f"On {kitchen.counter} stood {lighthouse.phrase}. Near {anchor.place} waited {anchor.phrase}, "
        f"and close by rested {moss.phrase}."
    )
    world.note("opening", "The kitchen adventure begins.", kitchen=kitchen.id)


def announce_mission(world: World, crew: Crew, twist: Twist) -> None:
    world.say(
        f'"Find {twist.apparent} before the soup is ready," {crew.helper_name} said. '
        f"The two friends called themselves {crew.phrase} and took the mission very seriously."
    )
    world.say(
        f"{crew.hero_name} looked straight at the crystal lighthouse and felt sure the prize must be hidden inside it."
    )
    world.note("mission", "The crew mistakes the lighthouse for the treasure box.", apparent=twist.apparent)


def inspect_lighthouse(world: World, crew: Crew, lighthouse: CrystalLighthouse) -> None:
    lighthouse_ent = world.get("lighthouse")
    lighthouse_ent.meters["turned"] += 1
    world.say(
        f"{crew.hero_name} turned the crystal lighthouse with careful fingers until {lighthouse.lens} caught the room light."
    )
    propagate(world)
    if lighthouse_ent.meters["guiding"] >= THRESHOLD:
        world.say(
            f"A thin {lighthouse.beam} slipped across the kitchen. "
            f'"Look," {crew.helper_name} whispered. "{lighthouse.hint}"'
        )
    world.note("beam", "The lighthouse begins acting like a guide.", beam=lighthouse.beam)


def tempt_shortcut(world: World, crew: Crew, shortcut: Shortcut) -> None:
    shortcut_ent = world.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    prediction = predict_shortcut(world, shortcut)
    world.facts["prediction"] = prediction
    world.say(f"Then {crew.hero_name} had a rushing idea: {shortcut.temptation}.")
    world.say(f'{shortcut.thought} {crew.hero_name} thought.')
    world.say(
        f'"Wait," {crew.helper_name} said. "If you do that, {shortcut.consequence}"'
    )
    propagate(world)
    world.note("shortcut", "A fast shortcut tempts the crew.", shortcut=shortcut.id, risk=shortcut.consequence)


def choose_care(world: World, crew: Crew, shortcut: Shortcut) -> None:
    hero = world.get("hero")
    hero.memes["patience"] += 1
    world.say(
        f"{crew.hero_name} took a breath and remembered, {crew.pledge}"
    )
    world.say(
        f"So {crew.hero_name} stepped back. {shortcut.safe_choice}"
    )
    propagate(world)
    world.note("choice", "The crew chooses care over speed.", care=str(crew.care))


def follow_anchor(world: World, lighthouse: CrystalLighthouse, anchor: AnchorMark) -> None:
    anchor_ent = world.get("anchor")
    if anchor_ent.meters["lit"] >= THRESHOLD:
        world.say(
            f"The {lighthouse.beam} landed on {anchor.phrase} at {anchor.place}."
        )
        world.say(
            f"The anchor was not the treasure at all. {anchor.use.capitalize()}."
        )
        world.note("anchor_clue", "The anchor becomes the next clue.", anchor=anchor.id)


def reveal_prize(world: World, crew: Crew, moss: MossPatch, twist: Twist) -> None:
    moss_ent = world.get("moss")
    moss_ent.meters["lifted"] += 1
    world.say(
        f"{crew.hero_name} knelt by {moss.area} and lifted the fuzzy moss as softly as if {crew.hero_name} were tucking in a sleeping bird."
    )
    propagate(world)
    prize = world.get("prize")
    if prize.meters["found"] >= THRESHOLD:
        world.say(
            f"Under the fuzzy moss lay {twist.prize}. {twist.reveal}"
        )
    world.say(f"That was the twist: {twist.truth}.")
    world.note("reveal", "The true prize is discovered under the moss.", prize=twist.prize)


def ending(world: World, crew: Crew, twist: Twist) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    team = world.get("team")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    team.memes["pride"] += 1
    world.say(twist.ending)
    world.say(
        f"In the warm kitchen light, {twist.prize} gleamed beside the crystal lighthouse, "
        "and even the anchor looked proud to have kept the secret path."
    )
    world.facts["resolved"] = True
    world.note("ending", "The kitchen ends in a clear image of the solved adventure.")


def tell(params: StoryParams) -> World:
    kitchen = KITCHENS[params.kitchen]
    crew = CREWS[params.crew]
    lighthouse = LIGHTHOUSES[params.lighthouse]
    moss = MOSS_PATCHES[params.moss]
    anchor = ANCHORS[params.anchor]
    shortcut = SHORTCUTS[params.shortcut]
    twist = TWISTS[params.twist]

    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)

    world = World(kitchen)
    hero = world.add(
        Entity(
            "hero",
            kind="character",
            type=crew.hero_type,
            label=crew.hero_name,
            phrase=crew.hero_name,
        )
    )
    helper = world.add(
        Entity(
            "helper",
            kind="character",
            type=crew.helper_type,
            label=crew.helper_name,
            phrase=crew.helper_name,
        )
    )
    team = world.add(
        Entity(
            "team",
            kind="group",
            type="crew",
            label=f"{crew.hero_name} and {crew.helper_name}",
            phrase=crew.phrase,
        )
    )
    hero.memes["care"] = float(crew.care)
    team.memes["care"] = float(crew.care)
    world.add(
        Entity(
            "lighthouse",
            type="crystal lighthouse",
            label=lighthouse.label,
            phrase=lighthouse.phrase,
            location=kitchen.counter,
            attrs={"key": lighthouse.key},
        )
    )
    world.add(
        Entity(
            "moss",
            type="fuzzy moss",
            label=moss.label,
            phrase=moss.phrase,
            location=moss.area,
            attrs={"key": moss.key},
        )
    )
    world.add(
        Entity(
            "anchor",
            type="anchor",
            label=anchor.label,
            phrase=anchor.phrase,
            location=anchor.place,
            attrs={"key": anchor.key},
        )
    )
    world.add(
        Entity(
            "shortcut",
            type="shortcut",
            label=shortcut.label,
            phrase=shortcut.temptation,
        )
    )
    world.add(
        Entity(
            "prize",
            type="treasure",
            label=twist.prize,
            phrase=twist.prize,
            attrs={"key": twist.key},
        )
    )

    introduce(world, crew, kitchen, lighthouse, anchor, moss)
    announce_mission(world, crew, twist)

    world.para()
    inspect_lighthouse(world, crew, lighthouse)
    tempt_shortcut(world, crew, shortcut)
    choose_care(world, crew, shortcut)

    world.para()
    follow_anchor(world, lighthouse, anchor)
    reveal_prize(world, crew, moss, twist)

    world.para()
    ending(world, crew, twist)

    world.facts.update(
        kitchen=kitchen,
        crew=crew,
        lighthouse=lighthouse,
        moss=moss,
        anchor=anchor,
        shortcut=shortcut,
        twist=twist,
        hero=hero,
        helper=helper,
        team=team,
        prize=world.get("prize"),
        outcome="guide_revealed",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    crew = world.facts["crew"]
    kitchen = world.facts["kitchen"]
    twist = world.facts["twist"]
    assert isinstance(crew, Crew)
    assert isinstance(kitchen, Kitchen)
    assert isinstance(twist, Twist)
    return [
        'Write a child-friendly Adventure story set in a kitchen using the words "anchor", "fuzzy moss", and "crystal lighthouse".',
        f"Tell a tiny kitchen quest where {crew.hero_name} and {crew.helper_name} choose careful hands instead of a fast shortcut.",
        f"Write a Twist story where the crystal lighthouse only guides the children to {twist.prize} in {kitchen.phrase}.",
    ]


def story_qa_items(world: World) -> list[QAItem]:
    crew = world.facts["crew"]
    kitchen = world.facts["kitchen"]
    lighthouse = world.facts["lighthouse"]
    moss = world.facts["moss"]
    anchor = world.facts["anchor"]
    shortcut = world.facts["shortcut"]
    twist = world.facts["twist"]
    prediction = world.facts["prediction"]
    assert isinstance(crew, Crew)
    assert isinstance(kitchen, Kitchen)
    assert isinstance(lighthouse, CrystalLighthouse)
    assert isinstance(moss, MossPatch)
    assert isinstance(anchor, AnchorMark)
    assert isinstance(shortcut, Shortcut)
    assert isinstance(twist, Twist)
    assert isinstance(prediction, dict)
    return [
        QAItem(
            "Where does the adventure happen?",
            f"It happens in {kitchen.phrase}. The room feels adventurous because {kitchen.weather.lower()} and the children imagine it as {kitchen.mood}.",
        ),
        QAItem(
            f"What did {crew.hero_name} first think about the crystal lighthouse?",
            f"{crew.hero_name} first thought the prize must be hidden inside the crystal lighthouse. That wrong guess sets up the twist because the lighthouse turns out to be a guide instead.",
        ),
        QAItem(
            "Why did the children refuse the fast shortcut?",
            f"They refused because {shortcut.consequence} That would have damaged the clue path instead of helping them solve the kitchen adventure.",
        ),
        QAItem(
            "What did the anchor do in the story?",
            f"{anchor.label.capitalize()} caught the lighthouse beam at {anchor.place}. That showed the anchor was a marker pointing toward the next clue rather than a treasure itself.",
        ),
        QAItem(
            "What was hidden under the fuzzy moss?",
            f"Under the fuzzy moss they found {twist.prize}. The soft moss kept it safe until the beam and the anchor agreed on the right spot.",
        ),
        QAItem(
            "What was the twist at the end?",
            f"The twist was that {twist.truth}. The brightest object looked important first, but the quiet moss was where the real prize had been waiting.",
        ),
        QAItem(
            "How did careful behavior help the ending?",
            f"The children kept the clues whole by not damaging {prediction['target_label']} or scattering anything. Because they stayed gentle, the light could keep guiding them all the way to the prize.",
        ),
    ]


def world_knowledge_qa_items(world: World) -> list[QAItem]:
    kitchen = world.facts["kitchen"]
    crew = world.facts["crew"]
    lighthouse = world.facts["lighthouse"]
    moss = world.facts["moss"]
    anchor = world.facts["anchor"]
    shortcut = world.facts["shortcut"]
    tags = (
        set(kitchen.tags)
        | set(crew.tags)
        | set(lighthouse.tags)
        | set(moss.tags)
        | set(anchor.tags)
        | set(shortcut.tags)
        | {"kitchen", "care", "lighthouse"}
    )
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa_items(world),
        world_qa=world_knowledge_qa_items(world),
        world=world,
    )


def asp_facts() -> str:
    from asp import fact

    lines: list[str] = []
    for kitchen in KITCHENS.values():
        lines.append(fact("kitchen", kitchen.id))
        for route in sorted(kitchen.routes):
            lines.append(fact("kitchen_route", kitchen.id, route))
    for crew in CREWS.values():
        lines.append(fact("crew", crew.id))
        lines.append(fact("crew_care", crew.id, crew.care))
    for lighthouse in LIGHTHOUSES.values():
        lines.append(fact("lighthouse", lighthouse.id))
        lines.append(fact("lighthouse_key", lighthouse.id, lighthouse.key))
    for moss in MOSS_PATCHES.values():
        lines.append(fact("moss", moss.id))
        lines.append(fact("moss_key", moss.id, moss.key))
    for anchor in ANCHORS.values():
        lines.append(fact("anchor", anchor.id))
        lines.append(fact("anchor_key", anchor.id, anchor.key))
    for shortcut in SHORTCUTS.values():
        lines.append(fact("shortcut", shortcut.id))
        lines.append(fact("shortcut_lure", shortcut.id, shortcut.lure))
    for twist in TWISTS.values():
        lines.append(fact("twist", twist.id))
        lines.append(fact("twist_key", twist.id, twist.key))
    return "\n".join(lines) + "\n"


ASP_RULES = r"""
valid(K,C,L,M,A,S,T) :-
    kitchen(K),
    crew(C),
    lighthouse(L),
    moss(M),
    anchor(A),
    shortcut(S),
    twist(T),
    kitchen_route(K, Key),
    lighthouse_key(L, Key),
    moss_key(M, Key),
    anchor_key(A, Key),
    twist_key(T, Key),
    crew_care(C, Care),
    shortcut_lure(S, Lure),
    Care >= Lure.

#show valid/7.
"""


def asp_program() -> str:
    return asp_facts() + ASP_RULES


def asp_valid_combos() -> list[tuple[str, str, str, str, str, str, str]]:
    from asp import atoms, one_model

    return sorted(atoms(one_model(asp_program()), "valid"))


def verify_sample(sample: StorySample) -> None:
    world = sample.world
    if world is None:
        raise AssertionError("sample world is missing")
    story_lower = sample.story.lower()
    for needle in ("anchor", "fuzzy moss", "crystal lighthouse", "kitchen"):
        if needle not in story_lower:
            raise AssertionError(f"story is missing {needle!r}")
    if sample.story.count("\n\n") < 3:
        raise AssertionError("story should have at least four paragraphs")
    if "{" in sample.story or "}" in sample.story:
        raise AssertionError("story leaked unresolved formatting")
    if "meters=" in sample.story or "memes=" in sample.story:
        raise AssertionError("story leaked debug language")
    if world.get("lighthouse").meters.get("guiding", 0) < 1:
        raise AssertionError("lighthouse never became a guide")
    if world.get("anchor").meters.get("lit", 0) < 1:
        raise AssertionError("anchor never became an active clue")
    if world.get("moss").meters.get("lifted", 0) < 1:
        raise AssertionError("moss was never lifted")
    if world.get("prize").meters.get("found", 0) < 1:
        raise AssertionError("prize was never found")
    if world.get("team").memes.get("pride", 0) < 1:
        raise AssertionError("team never reached a proud ending state")
    if not world.facts.get("resolved"):
        raise AssertionError("story never marked itself resolved")
    event_ids = {event.id for event in world.history}
    for required in ("opening", "mission", "beam", "shortcut", "choice", "anchor_clue", "reveal", "ending"):
        if required not in event_ids:
            raise AssertionError(f"missing event {required!r}")
    if len(sample.prompts) != 3:
        raise AssertionError("expected exactly three prompts")
    if len(sample.story_qa) < 6:
        raise AssertionError("story QA is too thin")
    if len(sample.world_qa) < 4:
        raise AssertionError("world knowledge QA is too thin")
    for item in list(sample.story_qa) + list(sample.world_qa):
        if len(item.answer.split()) < 12:
            raise AssertionError(f"answer is too short: {item.question}")


def asp_verify() -> int:
    py = all_combos()
    lp = asp_valid_combos()
    if py != lp:
        only_py = sorted(set(py) - set(lp))
        only_lp = sorted(set(lp) - set(py))
        print("MISMATCH between Python and ASP gates:", file=sys.stderr)
        if only_py:
            print(f"  only in Python: {only_py}", file=sys.stderr)
        if only_lp:
            print(f"  only in ASP: {only_lp}", file=sys.stderr)
        return 1
    print(f"OK: ASP parity matches Python gate ({len(py)} valid kitchen adventure stories).")
    for index, combo in enumerate(py):
        verify_sample(generate(params_from_combo(combo, 1000 + index)))
    print(f"OK: generated stories and QA passed for all {len(py)} valid combinations.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a child-friendly kitchen adventure about an anchor, fuzzy moss, and a crystal lighthouse."
    )
    parser.add_argument("--kitchen", choices=sorted(KITCHENS))
    parser.add_argument("--crew", choices=sorted(CREWS))
    parser.add_argument("--lighthouse", choices=sorted(LIGHTHOUSES))
    parser.add_argument("--moss", choices=sorted(MOSS_PATCHES))
    parser.add_argument("--anchor", choices=sorted(ANCHORS))
    parser.add_argument("--shortcut", choices=sorted(SHORTCUTS))
    parser.add_argument("--twist", choices=sorted(TWISTS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random | None = None,
    index: int = 0,
) -> StoryParams:
    seed = (args.seed if args.seed is not None else 13) + index
    combos = matching_combos(args)
    if not combos:
        kitchen = KITCHENS[args.kitchen or next(iter(KITCHENS))]
        crew = CREWS[args.crew or next(iter(CREWS))]
        lighthouse = LIGHTHOUSES[args.lighthouse or next(iter(LIGHTHOUSES))]
        moss = MOSS_PATCHES[args.moss or next(iter(MOSS_PATCHES))]
        anchor = ANCHORS[args.anchor or next(iter(ANCHORS))]
        shortcut = SHORTCUTS[args.shortcut or next(iter(SHORTCUTS))]
        twist = TWISTS[args.twist or next(iter(TWISTS))]
        raise StoryError(explain_rejection(kitchen, crew, lighthouse, moss, anchor, shortcut, twist))

    explicit = all(
        getattr(args, field) is not None
        for field in ("kitchen", "crew", "lighthouse", "moss", "anchor", "shortcut", "twist")
    )
    if explicit:
        params = StoryParams(
            args.kitchen,
            args.crew,
            args.lighthouse,
            args.moss,
            args.anchor,
            args.shortcut,
            args.twist,
            seed,
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params

    chooser = rng or random.Random(seed)
    return params_from_combo(chooser.choice(combos), seed)


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        combos = matching_combos(args)
        if not combos:
            kitchen = KITCHENS[args.kitchen or next(iter(KITCHENS))]
            crew = CREWS[args.crew or next(iter(CREWS))]
            lighthouse = LIGHTHOUSES[args.lighthouse or next(iter(LIGHTHOUSES))]
            moss = MOSS_PATCHES[args.moss or next(iter(MOSS_PATCHES))]
            anchor = ANCHORS[args.anchor or next(iter(ANCHORS))]
            shortcut = SHORTCUTS[args.shortcut or next(iter(SHORTCUTS))]
            twist = TWISTS[args.twist or next(iter(TWISTS))]
            raise StoryError(explain_rejection(kitchen, crew, lighthouse, moss, anchor, shortcut, twist))
        return [generate(params_from_combo(combo, args.seed + index)) for index, combo in enumerate(combos)]

    samples: list[StorySample] = []
    for index in range(max(1, args.n)):
        seed = args.seed + index
        samples.append(generate(resolve_params(args, random.Random(seed), index)))
    return samples


def format_qa(sample: StorySample) -> str:
    lines = ["PROMPTS"]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("STORY QA")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("WORLD KNOWLEDGE QA")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print()
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.show_asp:
        print(asp_program())
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid kitchen adventure stories:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:16}" for part in combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for index, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== anchor_fuzzy_moss_crystal_lighthouse_kitchen_twist_2 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
