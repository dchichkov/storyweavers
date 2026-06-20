#!/usr/bin/env python3
"""
storyworlds/worlds/honey_dusty_moss_misty_path_shopping_mall_2.py
=================================================================

A standalone storyworld for a seed prompt:

    Words: honey, dusty moss, misty path
    Setting: shopping mall
    Features: Inner Monologue, Bad Ending, Dialogue
    Style: Pirate Tale

Internal source tale
--------------------
At a shopping mall pirate promotion, a child spots a honey prize beyond a roped
"misty path" lined with dusty moss. A friend and a costumed kiosk captain warn
the child to wait because the path is not safe yet. The child privately decides
to snatch the prize like treasure anyway. The slick path betrays that choice,
the prize is ruined, and the display closes in a sticky, shamefaced bad ending.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "aunt", "sister"}
        male = {"boy", "man", "father", "uncle", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class MallArea:
    id: str
    label: str
    opening: str
    lookout: str
    final_image: str
    affords: set[str] = field(default_factory=set)
    displays: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Display:
    id: str
    label: str
    deck_name: str
    moss_detail: str
    path_detail: str
    warning: str
    closing_line: str
    hazards: set[str] = field(default_factory=set)
    prizes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Hazard:
    id: str
    cause: str
    trigger: str
    danger: str
    slip_line: str
    close_reason: str
    stain: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Prize:
    id: str
    item: str
    shine: str
    break_line: str
    loss_line: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    area: str
    display: str
    hazard: str
    prize: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    keeper: str
    keeper_gender: str
    trait: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[["World"], bool]


class World:
    def __init__(self, params: StoryParams) -> None:
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(par) for par in self.paragraphs if par)

    def remember(self, kind: str, **fields: str) -> None:
        row = {"kind": kind}
        row.update(fields)
        self.history.append(row)

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def trace(self) -> str:
        lines = [
            f"params: {self.params}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
            f"bad ending: {self.facts.get('bad_ending', False)}",
        ]
        for ent in self.entities.values():
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(f"  {ent.id} | {ent.kind} | {ent.type} | {ent.label}")
            if meters:
                lines.append(f"    meters={meters}")
            if memes:
                lines.append(f"    memes={memes}")
        for item in self.history:
            lines.append(f"  history={item}")
        return "\n".join(lines)


AREAS = {
    "anchor_atrium": MallArea(
        id="anchor_atrium",
        label="Anchor Atrium",
        opening=(
            "the bright Anchor Atrium of the shopping mall, where silver escalators "
            "rose like gangplanks under a painted sail"
        ),
        lookout="a ring of benches by the fountain",
        final_image=(
            "sticky footprints shone beside the fountain while shoppers steered wide "
            "of the roped display"
        ),
        affords={"fog_drift", "honey_drip"},
        displays={"captain_kiosk", "toy_window"},
    ),
    "garden_walk": MallArea(
        id="garden_walk",
        label="Garden Walk",
        opening=(
            "Garden Walk in the shopping mall, where potted palms and skylights made "
            "the floor feel like an indoor harbor"
        ),
        lookout="a row of carts outside the garden shop",
        final_image=(
            "a cleaner's yellow cart stood where the treasure lane had been, and the "
            "air smelled of soap instead of sweets"
        ),
        affords={"fog_drift", "moss_slide"},
        displays={"captain_kiosk", "moss_stage"},
    ),
    "lantern_lane": MallArea(
        id="lantern_lane",
        label="Lantern Lane",
        opening=(
            "Lantern Lane in the shopping mall, where hanging bulbs bobbed above the "
            "corridor like warm cabin lamps"
        ),
        lookout="the toy-store shutter and a polished railing",
        final_image=(
            "the shutter reflected a broken gleam on the tiles, and the pirate music "
            "had gone quiet"
        ),
        affords={"moss_slide", "honey_drip"},
        displays={"moss_stage", "toy_window"},
    ),
}


DISPLAYS = {
    "captain_kiosk": Display(
        id="captain_kiosk",
        label="Captain Crumble's Kiosk",
        deck_name="the captain's snack deck",
        moss_detail="dusty moss tucked around painted rocks at the base of the barrels",
        path_detail="a misty path of blue floor lights and low fog between velvet ropes",
        warning="That misty path is not part of the line yet, matey.",
        closing_line="The captain dropped a striped screen across the snack deck.",
        hazards={"fog_drift", "honey_drip"},
        prizes={"honey_cake", "honey_jar"},
    ),
    "moss_stage": Display(
        id="moss_stage",
        label="Mossy Treasure Stage",
        deck_name="the treasure stage",
        moss_detail="dusty moss draped over cardboard cliffs around a little bridge",
        path_detail="a misty path curling between fake tide pools and gold-painted shells",
        warning="The ropes stay shut until the deck is steady, little sailor.",
        closing_line="The treasure stage went dark behind a folding screen.",
        hazards={"fog_drift", "moss_slide"},
        prizes={"honey_jar", "honey_coin_bag"},
    ),
    "toy_window": Display(
        id="toy_window",
        label="Toy Window Galleon",
        deck_name="the toy galleon window",
        moss_detail="dusty moss piled under a cardboard prow and a toy anchor",
        path_detail="a misty path painted on the floor to lead eyes toward the window chest",
        warning="Mind the rope, matey. That path is for looking, not for boots.",
        closing_line="A worker pulled the toy galleon's curtain halfway closed.",
        hazards={"honey_drip", "moss_slide"},
        prizes={"honey_cake", "honey_coin_bag"},
    ),
}


HAZARDS = {
    "fog_drift": Hazard(
        id="fog_drift",
        cause="the fog machine had breathed a cool film onto the tiles",
        trigger="the low mist kept settling over the path",
        danger="the wet shine hid under the fake sea fog",
        slip_line="The child's shoe skated on the damp tile as if a wave had slapped the deck.",
        close_reason="The mall captain could not leave a wet path open after the tumble.",
        stain="wet streaks under the fog",
    ),
    "moss_slide": Hazard(
        id="moss_slide",
        cause="crumbly dusty moss had drifted onto the smooth floor",
        trigger="each step sent dry green bits sliding underfoot",
        danger="the dusty moss made the path look soft even though the tile beneath it was slick",
        slip_line="The child's foot crushed the dusty moss and shot sideways in one fast skid.",
        close_reason="The captain had to close the deck while the loose moss was swept away.",
        stain="green crumbs and gray dust",
    ),
    "honey_drip": Hazard(
        id="honey_drip",
        cause="a thin ribbon of honey had dripped from the prize barrel onto the path",
        trigger="the sweet drip kept spreading near the rope line",
        danger="the honey gleam looked golden and safe until it grabbed at shoes",
        slip_line="One shoe stuck, then lurched free, and the child pitched forward with a cry.",
        close_reason="No captain would keep selling treats over a fresh honey spill.",
        stain="amber smears on the tiles",
    ),
}


PRIZES = {
    "honey_cake": Prize(
        id="honey_cake",
        item="a honey cake shaped like a tiny treasure chest",
        shine="its sugared lid sparkled like a prize doubloon",
        break_line="The honey cake flipped from the platter and burst into crumbs.",
        loss_line="Treasure crumbs are poor comfort when the chest never reaches your hands.",
        ending="crushed cake crumbs shining in the mall light",
    ),
    "honey_jar": Prize(
        id="honey_jar",
        item="a squat honey jar with a paper pirate flag tied to the lid",
        shine="its amber glow looked brighter than a lantern at sea",
        break_line="The honey jar thumped onto the floor and leaked a thick golden puddle.",
        loss_line="A split jar cannot be carried home like treasure.",
        ending="a torn paper flag drooping beside a golden puddle",
    ),
    "honey_coin_bag": Prize(
        id="honey_coin_bag",
        item="a little bag of honey candies stamped like pirate coins",
        shine="the wrappers winked like treasure in a captain's chest",
        break_line="The candy bag burst, and sticky honey coins scattered across the tiles.",
        loss_line="Scattered sweets do not feel like victory when everyone has to step around them.",
        ending="sticky candy wrappers clinging to the shiny floor",
    ),
}


GIRL_NAMES = ["Lina", "Nora", "Ivy", "Mara", "Tess"]
BOY_NAMES = ["Finn", "Milo", "Theo", "Jules", "Arlo"]
KEEPER_WOMEN = ["Captain Rue", "Captain Inez", "Captain Miri"]
KEEPER_MEN = ["Captain Bram", "Captain Sol", "Captain Daren"]
TRAITS = ["eager", "restless", "daydreaming", "bold", "hasty"]


def compatible(area: MallArea, display: Display, hazard: Hazard, prize: Prize) -> bool:
    return (
        display.id in area.displays
        and hazard.id in area.affords
        and hazard.id in display.hazards
        and prize.id in display.prizes
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for area_id, area in AREAS.items():
        for display_id, display in DISPLAYS.items():
            for hazard_id, hazard in HAZARDS.items():
                for prize_id, prize in PRIZES.items():
                    if compatible(area, display, hazard, prize):
                        combos.append((area_id, display_id, hazard_id, prize_id))
    return sorted(combos)


def explain_rejection(area: MallArea, display: Display, hazard: Hazard, prize: Prize) -> str:
    if display.id not in area.displays:
        return (
            f"(No story: {display.label} does not stand in {area.label}. "
            "The shopping mall scene would not fit together.)"
        )
    if hazard.id not in area.affords:
        return (
            f"(No story: {area.label} does not allow hazard '{hazard.id}'. "
            "The floor conditions would be unreasonable there.)"
        )
    if hazard.id not in display.hazards:
        return (
            f"(No story: {display.label} does not produce hazard '{hazard.id}'. "
            "The bad ending needs a grounded cause.)"
        )
    return (
        f"(No story: {display.label} does not offer prize '{prize.id}'. "
        "The child cannot chase treasure that is not on the deck.)"
    )


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_hazard_primes_path(world: World) -> bool:
    path = world.get("path")
    floor = world.get("floor")
    moss = world.get("moss")
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    if not _mark(world, "hazard_primes_path", hazard.id):
        return False
    path.meters["misty"] += 1
    path.meters["rope_closed"] += 1
    if hazard.id == "fog_drift":
        path.meters["wet"] += 1
        path.meters["slick"] += 1
        floor.meters["wet"] += 1
    elif hazard.id == "moss_slide":
        moss.meters["loose"] += 1
        path.meters["gritty"] += 1
        path.meters["slick"] += 1
    elif hazard.id == "honey_drip":
        floor.meters["sticky"] += 1
        path.meters["sticky"] += 1
        path.meters["slick"] += 1
    return True


def _r_inner_voice_rises(world: World) -> bool:
    hero = world.get("hero")
    prize = world.get("prize")
    path = world.get("path")
    if hero.memes["greed"] < THRESHOLD or path.meters["slick"] < THRESHOLD:
        return False
    if not _mark(world, "inner_voice_rises", hero.id, prize.id):
        return False
    hero.memes["impatience"] += 1
    hero.memes["recklessness"] += 1
    return True


def _r_crossing_turns_bad(world: World) -> bool:
    hero = world.get("hero")
    prize = world.get("prize")
    path = world.get("path")
    floor = world.get("floor")
    if hero.meters["crossed_rope"] < THRESHOLD or path.meters["slick"] < THRESHOLD:
        return False
    if not _mark(world, "crossing_turns_bad", hero.id, prize.id):
        return False
    hero.meters["fallen"] += 1
    hero.meters["sticky_shoes"] += 1
    prize.meters["ruined"] += 1
    floor.meters["mess"] += 1
    return True


def _r_bad_ending_lands(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    keeper = world.get("keeper")
    display = world.get("display")
    prize = world.get("prize")
    if hero.meters["fallen"] < THRESHOLD or prize.meters["ruined"] < THRESHOLD:
        return False
    if not _mark(world, "bad_ending_lands", hero.id, prize.id):
        return False
    hero.memes["regret"] += 1
    friend.memes["worry"] += 1
    keeper.memes["alarm"] += 1
    display.meters["closed"] += 1
    world.facts["bad_ending"] = True
    return True


RULES = [
    Rule("hazard_primes_path", _r_hazard_primes_path),
    Rule("inner_voice_rises", _r_inner_voice_rises),
    Rule("crossing_turns_bad", _r_crossing_turns_bad),
    Rule("bad_ending_lands", _r_bad_ending_lands),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


def sentence_case(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def _pick_keeper(rng: random.Random, gender: str) -> str:
    return rng.choice(KEEPER_WOMEN if gender == "woman" else KEEPER_MEN)


def build_world(params: StoryParams) -> World:
    area = AREAS[params.area]
    display = DISPLAYS[params.display]
    hazard = HAZARDS[params.hazard]
    prize = PRIZES[params.prize]
    if not compatible(area, display, hazard, prize):
        raise StoryError(explain_rejection(area, display, hazard, prize))

    world = World(params)
    world.facts["area"] = area
    world.facts["display_cfg"] = display
    world.facts["hazard"] = hazard
    world.facts["prize_cfg"] = prize
    world.facts["bad_ending"] = False

    hero = world.add(
        Entity("hero", kind="character", type=params.hero_gender, label=params.hero, role="Hero")
    )
    friend = world.add(
        Entity("friend", kind="character", type=params.friend_gender, label=params.friend, role="Friend")
    )
    keeper = world.add(
        Entity("keeper", kind="character", type=params.keeper_gender, label=params.keeper, role="Keeper")
    )
    world.add(Entity("display", kind="thing", type="display", label=display.label, role="Display"))
    world.add(Entity("path", kind="thing", type="path", label="misty path", role="Path"))
    world.add(Entity("moss", kind="thing", type="moss", label="dusty moss", role="Moss"))
    world.add(Entity("floor", kind="thing", type="tile", label="mall tiles", role="Floor"))
    world.add(Entity("prize", kind="thing", type="prize", label=prize.item, role="Prize"))

    hero.memes["greed"] += 1
    hero.memes["inner_voice"] += 1
    friend.memes["care"] += 1
    keeper.memes["duty"] += 1
    world.get("moss").meters["dusty"] += 1
    world.get("prize").meters["visible"] += 1

    propagate(world)
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    area: MallArea = world.facts["area"]  # type: ignore[assignment]
    display: Display = world.facts["display_cfg"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    prize: Prize = world.facts["prize_cfg"]  # type: ignore[assignment]
    hero = world.get("hero")
    friend = world.get("friend")
    keeper = world.get("keeper")
    path = world.get("path")

    world.say(
        f"Once upon a time, {hero.label} and {friend.label} wandered through {area.opening}. "
        f"They stopped at {display.label}, a pirate display with {display.moss_detail} and "
        f"{display.path_detail}. At the far end waited {prize.item}; {prize.shine}."
    )
    world.say(
        f"The air smelled of honey, and the rope around the misty path made the little lane "
        f"look like a secret deck meant only for captains."
    )
    world.remember(
        "premise",
        area=area.label,
        display=display.label,
        prize=prize.item,
        path=path.label,
        moss=world.get("moss").label,
    )

    world.para()
    world.say(
        f"{keeper.label} tapped the rope with a striped cane and said, "
        f"\"{display.warning} {hazard.trigger.capitalize()}, and {hazard.danger}.\""
    )
    world.say(
        f"\"Let us wait, matey,\" whispered {friend.label}. \"Treasure tastes better when no one falls.\""
    )
    thought = (
        f"{hero.label} thought, \"If I move fast as a pirate on a raid, I can grab {prize.item} "
        f"before anyone stops me.\""
    )
    world.say(thought)
    world.remember(
        "warning",
        speaker=keeper.label,
        helper=friend.label,
        danger=hazard.danger,
        thought=thought,
    )

    world.para()
    hero.meters["crossed_rope"] += 1
    world.remember("choice", actor=hero.label, action="crossed the rope", reason="wanted the prize quickly")
    propagate(world)
    world.say(
        f"But {hero.label} ducked under the rope and hurried onto the misty path anyway. "
        f"{hazard.slip_line}"
    )
    world.say(prize.break_line)
    world.remember(
        "fall",
        actor=hero.label,
        cause=hazard.cause,
        spill=prize.break_line,
        stain=hazard.stain,
    )

    world.para()
    world.say(
        f"\"Oh no, matey!\" cried {friend.label}, reaching out too late. {display.closing_line} "
        f"{keeper.label} lifted a hand and said, \"Back up, everyone. {hazard.close_reason}\""
    )
    world.say(
        f"{hero.label} stood with sticky shoes and a hot face. {prize.loss_line} "
        f"{sentence_case(area.final_image)}. Only {prize.ending} remained where treasure should have been."
    )
    world.remember(
        "ending",
        keeper=keeper.label,
        friend=friend.label,
        result="display closed",
        image=f"{area.final_image}; {prize.ending}",
        lesson="greedy shortcuts can turn treasure into trouble",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    area: MallArea = world.facts["area"]  # type: ignore[assignment]
    display: Display = world.facts["display_cfg"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    prize: Prize = world.facts["prize_cfg"]  # type: ignore[assignment]
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        (
            f"Tell a pirate tale in a shopping mall where {hero.label} and {friend.label} find "
            f"{display.label} with honey, dusty moss, and a misty path."
        ),
        (
            f"Include dialogue that warns the child about how {hazard.cause}, plus an inner monologue "
            f"about taking {prize.item} too quickly."
        ),
        (
            "End with a clear bad ending caused by the child's reckless choice, and show the changed "
            "scene in a concrete final image."
        ),
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    area: MallArea = world.facts["area"]  # type: ignore[assignment]
    display: Display = world.facts["display_cfg"]  # type: ignore[assignment]
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    prize: Prize = world.facts["prize_cfg"]  # type: ignore[assignment]
    hero = world.get("hero")
    friend = world.get("friend")
    keeper = world.get("keeper")
    return [
        (
            f"Where did {hero.label} find the pirate display?",
            f"{hero.label} found it in {area.label} inside the shopping mall. The display stood in a busy indoor walkway, not on a real ship.",
        ),
        (
            f"What treasure did {hero.label} want?",
            f"{hero.label} wanted {prize.item}. It looked special because {prize.shine}.",
        ),
        (
            f"Why did {keeper.label} warn the children away from the misty path?",
            f"{keeper.label} warned them because {hazard.cause}. {hazard.danger.capitalize()}, so the path was not safe for running feet.",
        ),
        (
            f"What did {hero.label} say only in {hero.pronoun('possessive')} head?",
            f"{hero.label} told {hero.pronoun('object')}self that a quick pirate dash could snatch the prize. That inner monologue pushed {hero.pronoun('object')} toward a reckless shortcut.",
        ),
        (
            f"How did the bad ending happen?",
            f"The bad ending happened when {hero.label} crossed the rope instead of waiting. {hazard.slip_line} {prize.break_line}",
        ),
        (
            f"How did the shopping mall scene look at the very end?",
            f"At the end, {area.final_image}. {prize.ending.capitalize()} showed that the treasure was gone for good.",
        ),
    ]


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    hazard: Hazard = world.facts["hazard"]  # type: ignore[assignment]
    display: Display = world.facts["display_cfg"]  # type: ignore[assignment]
    return [
        (
            "Why is a roped display path different from a normal walking lane?",
            "A roped display path is part of a scene, not part of safe traffic. People should wait for staff when a prop area is still being prepared.",
        ),
        (
            "Why can honey make a floor dangerous?",
            "Honey is sticky and slippery at the same time. It can grab a shoe and then make the next step slide suddenly.",
        ),
        (
            "Why might dusty moss cause trouble indoors?",
            "Dusty moss can scatter and hide the surface beneath it. That makes it harder to see whether the floor is smooth, wet, or slick.",
        ),
        (
            f"What job did {display.label} staff need to do after the accident?",
            f"The staff needed to close the display and clean the path. {sentence_case(hazard.close_reason)} That cleanup kept other shoppers safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for prompt in sample.prompts:
        lines.append(f"- {prompt}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return "--- world model state ---\n" + world.trace()


CURATED = [
    StoryParams("anchor_atrium", "captain_kiosk", "honey_drip", "honey_cake", "Lina", "girl", "Finn", "boy", "Captain Rue", "woman", "eager"),
    StoryParams("garden_walk", "moss_stage", "moss_slide", "honey_jar", "Theo", "boy", "Nora", "girl", "Captain Bram", "man", "restless"),
    StoryParams("lantern_lane", "toy_window", "honey_drip", "honey_coin_bag", "Ivy", "girl", "Milo", "boy", "Captain Sol", "man", "daydreaming"),
    StoryParams("garden_walk", "captain_kiosk", "fog_drift", "honey_jar", "Arlo", "boy", "Mara", "girl", "Captain Inez", "woman", "hasty"),
]


ASP_RULES = r"""
valid(A,D,H,P) :- area_has_display(A,D), area_affords(A,H), display_hazard(D,H), display_prize(D,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for area_id, area in AREAS.items():
        lines.append(asp.fact("area", area_id))
        for display_id in sorted(area.displays):
            lines.append(asp.fact("area_has_display", area_id, display_id))
        for hazard_id in sorted(area.affords):
            lines.append(asp.fact("area_affords", area_id, hazard_id))
    for display_id, display in DISPLAYS.items():
        lines.append(asp.fact("display", display_id))
        for hazard_id in sorted(display.hazards):
            lines.append(asp.fact("display_hazard", display_id, hazard_id))
        for prize_id in sorted(display.prizes):
            lines.append(asp.fact("display_prize", display_id, prize_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def verify_generated_stories() -> list[str]:
    errors: list[str] = []
    for idx, combo in enumerate(valid_combos(), start=1):
        area_id, display_id, hazard_id, prize_id = combo
        hero_gender = "girl" if idx % 2 else "boy"
        friend_gender = "boy" if hero_gender == "girl" else "girl"
        params = StoryParams(
            area=area_id,
            display=display_id,
            hazard=hazard_id,
            prize=prize_id,
            hero=GIRL_NAMES[idx % len(GIRL_NAMES)] if hero_gender == "girl" else BOY_NAMES[idx % len(BOY_NAMES)],
            hero_gender=hero_gender,
            friend=BOY_NAMES[(idx + 1) % len(BOY_NAMES)] if friend_gender == "boy" else GIRL_NAMES[(idx + 1) % len(GIRL_NAMES)],
            friend_gender=friend_gender,
            keeper=_pick_keeper(random.Random(10_000 + idx), "woman" if idx % 2 else "man"),
            keeper_gender="woman" if idx % 2 else "man",
            trait=TRAITS[idx % len(TRAITS)],
            seed=20_000 + idx,
        )
        sample = generate(params)
        lowered = sample.story.lower()
        if "shopping mall" not in lowered:
            errors.append(f"missing shopping mall setting in {combo}")
        if "honey" not in lowered or "dusty moss" not in lowered or "misty path" not in lowered:
            errors.append(f"missing required seed words in {combo}")
        if "thought," not in sample.story:
            errors.append(f"missing inner monologue cue in {combo}")
        if "\"" not in sample.story:
            errors.append(f"missing dialogue in {combo}")
        if len(sample.story.split("\n\n")) < 4:
            errors.append(f"story too flat in {combo}")
        if not sample.world or not sample.world.facts.get("bad_ending"):
            errors.append(f"bad ending did not land in {combo}")
        if len(sample.story_qa) < 6 or len(sample.world_qa) < 4 or len(sample.prompts) < 3:
            errors.append(f"missing QA or prompts in {combo}")
        if "{" in sample.story or "}" in sample.story:
            errors.append(f"unresolved template text in {combo}")
    return errors


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    status = 0
    if python_set != asp_set:
        status = 1
        print("MISMATCH between ASP and Python valid_combos():")
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
    else:
        print(f"OK: ASP gate matches Python valid_combos() ({len(python_set)} combos).")

    errors = verify_generated_stories()
    if errors:
        status = 1
        print("Generated-story verification failed:")
        for err in errors:
            print(f"  - {err}")
    else:
        print(f"OK: generated stories passed structural checks ({len(python_set)} exercised combos).")
    return status


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Storyworld: pirate-flavored shopping mall tale with honey, dusty moss, "
            "a misty path, dialogue, inner monologue, and a bad ending."
        )
    )
    ap.add_argument("--area", choices=sorted(AREAS))
    ap.add_argument("--display", choices=sorted(DISPLAYS))
    ap.add_argument("--hazard", choices=sorted(HAZARDS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--keeper")
    ap.add_argument("--keeper-gender", choices=["woman", "man"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.area and args.display and args.display not in AREAS[args.area].displays:
        area = AREAS[args.area]
        display = DISPLAYS[args.display]
        hazard = HAZARDS[args.hazard] if args.hazard else HAZARDS[next(iter(area.affords))]
        prize = PRIZES[args.prize] if args.prize else PRIZES[next(iter(display.prizes))]
        raise StoryError(explain_rejection(area, display, hazard, prize))
    if args.area and args.hazard and args.hazard not in AREAS[args.area].affords:
        area = AREAS[args.area]
        display = DISPLAYS[args.display] if args.display else DISPLAYS[next(iter(area.displays))]
        hazard = HAZARDS[args.hazard]
        prize = PRIZES[args.prize] if args.prize else PRIZES[next(iter(display.prizes))]
        raise StoryError(explain_rejection(area, display, hazard, prize))
    if args.display and args.hazard and args.hazard not in DISPLAYS[args.display].hazards:
        display = DISPLAYS[args.display]
        area = AREAS[args.area] if args.area else next(
            value for value in AREAS.values() if display.id in value.displays
        )
        hazard = HAZARDS[args.hazard]
        prize = PRIZES[args.prize] if args.prize else PRIZES[next(iter(display.prizes))]
        raise StoryError(explain_rejection(area, display, hazard, prize))
    if args.display and args.prize and args.prize not in DISPLAYS[args.display].prizes:
        display = DISPLAYS[args.display]
        area = AREAS[args.area] if args.area else next(
            value for value in AREAS.values() if display.id in value.displays
        )
        hazard = HAZARDS[args.hazard] if args.hazard else HAZARDS[next(iter(display.hazards))]
        raise StoryError(explain_rejection(area, display, hazard, PRIZES[args.prize]))

    combos = [
        combo for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.display is None or combo[1] == args.display)
        and (args.hazard is None or combo[2] == args.hazard)
        and (args.prize is None or combo[3] == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid shopping-mall pirate story matches the given options.)")

    area, display, hazard, prize = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    keeper_gender = args.keeper_gender or rng.choice(["woman", "man"])
    keeper = args.keeper or _pick_keeper(rng, keeper_gender)
    trait = rng.choice(TRAITS)
    return StoryParams(
        area=area,
        display=display,
        hazard=hazard,
        prize=prize,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        keeper=keeper,
        keeper_gender=keeper_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_pairs(world)],
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


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(80, args.n * 80):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

    if args.json:
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, start=1):
        header = f"--- story {idx} ---" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except StoryError as err:
        print(err)
        sys.exit(1)
