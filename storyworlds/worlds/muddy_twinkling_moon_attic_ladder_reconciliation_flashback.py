#!/usr/bin/env python3
"""
storyworlds/worlds/muddy_twinkling_moon_attic_ladder_reconciliation_flashback.py
=================================================================================

Standalone storyworld for a TinyStories-style seed:

    Words: muddy, twinkling moon
    Setting: attic ladder
    Features: Reconciliation, Flashback, Happy Ending
    Style: Fable

Internal source tale:
    Two young animal friends climb an attic ladder each night to watch the moon
    at a round attic window. After rain, muddy marks appear on the ladder and
    the moon chart is knocked askew. One friend blames the other too quickly.
    A flashback of earlier kindness interrupts that blame, so the friends look
    again, find a gentler true cause, mend the mess, and reconcile under the
    twinkling moon.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass(frozen=True)
class LadderPlace:
    key: str
    house_name: str
    ladder_label: str
    window_label: str
    landing_label: str
    attic_treasure: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class MudClue:
    key: str
    family: str
    clue_text: str
    suspect_reason: str
    accusation: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Memory:
    key: str
    flashback: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Cause:
    key: str
    family: str
    need: str
    cause_text: str
    discovery: str
    fix_result: str
    closing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Repair:
    key: str
    need: str
    action_text: str
    result_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen", "doe"}
        male = {"boy", "father", "man", "buck"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    clue: str
    memory: str
    cause: str
    repair: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: LadderPlace) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()
        self.facts: dict[str, object] = {}
        self.history: list[dict[str, str]] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def log(self, event: str, **details: str) -> None:
        item = {"event": event}
        item.update({k: str(v) for k, v in details.items()})
        self.history.append(item)

    def clone(self) -> "World":
        return copy.deepcopy(self)

    def trace(self) -> str:
        lines = ["--- world ---", f"place={self.place.key}"]
        seen: set[int] = set()
        for ent in self.entities.values():
            if id(ent) in seen:
                continue
            seen.add(id(ent))
            meters = {k: v for k, v in ent.meters.items() if v}
            memes = {k: v for k, v in ent.memes.items() if v}
            lines.append(
                f"{ent.id}: kind={ent.kind} type={ent.type} meters={meters} memes={memes}"
            )
        lines.append("history:")
        for item in self.history:
            lines.append(f"  - {item}")
        return "\n".join(lines)


def _r_flashback_softens_blame(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["blame"] < THRESHOLD or hero.memes["flashback"] < THRESHOLD:
        return []
    sig = ("soften", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["blame"] = max(0.0, hero.memes["blame"] - 0.5)
    hero.memes["curiosity"] += 1.0
    hero.memes["trust"] += 0.5
    friend.memes["hope"] += 0.5
    world.log("flashback_softens_blame", hero=hero.id, friend=friend.id)
    return []


def _r_truth_changes_direction(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    attic_ladder = world.get("ladder")
    if attic_ladder.meters["true_cause_found"] < THRESHOLD:
        return []
    sig = ("truth", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["certainty_friend_innocent"] += 1.0
    hero.memes["blame"] = 0.0
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 0.5)
    world.log("truth_changes_direction", hero=hero.id, friend=friend.id)
    return []


def _r_reconciliation_restores_moon(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    moon = world.get("moon")
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return []
    if ladder.meters["clean"] < THRESHOLD or ladder.meters["safe"] < THRESHOLD:
        return []
    sig = ("reconciled", hero.id, friend.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    moon.meters["twinkling_seen"] += 1.0
    world.facts["reconciled"] = True
    world.facts["happy_ending"] = True
    world.log("reconciliation_restores_moon", hero=hero.id, friend=friend.id)
    return []


CAUSAL_RULES = [
    _r_flashback_softens_blame,
    _r_truth_changes_direction,
    _r_reconciliation_restores_moon,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True


PLACES: dict[str, LadderPlace] = {
    "round_window": LadderPlace(
        key="round_window",
        house_name="the bramble cottage",
        ladder_label="the narrow attic ladder",
        window_label="the round attic window",
        landing_label="the little loft landing",
        attic_treasure="their moon chart pinned beside a basket of dry lavender",
        ending_image="the clean rungs shining like pale honey",
        tags={"attic", "ladder", "moon"},
    ),
    "quilt_loft": LadderPlace(
        key="quilt_loft",
        house_name="the hill burrow",
        ladder_label="the old attic ladder",
        window_label="the square moon pane",
        landing_label="the quilt loft",
        attic_treasure="their folded moon map tucked above the quilt chest",
        ending_image="the ladder resting still beside the quilt chest",
        tags={"attic", "ladder", "quilt"},
    ),
    "seed_nook": LadderPlace(
        key="seed_nook",
        house_name="the seedkeeper's cottage",
        ladder_label="the smooth attic ladder",
        window_label="the tiny attic moon window",
        landing_label="the seed nook under the rafters",
        attic_treasure="their silver moon calendar hanging near the seed jars",
        ending_image="the last muddy streak gone from the ladder rails",
        tags={"attic", "ladder", "seed"},
    ),
}


CLUES: dict[str, MudClue] = {
    "garden_leaf": MudClue(
        key="garden_leaf",
        family="garden",
        clue_text="a muddy turnip leaf stuck to the third rung",
        suspect_reason="Moss had spent the morning pulling turnips in the garden",
        accusation="You were the one in the muddy garden, so you must have done this.",
        tags={"mud", "garden", "leaf"},
    ),
    "pond_reed": MudClue(
        key="pond_reed",
        family="pond",
        clue_text="a muddy reed thread pasted across the side rail",
        suspect_reason="Moss had carried pond reeds home for weaving",
        accusation="You were the one by the pond, so these muddy marks must be yours.",
        tags={"mud", "pond", "reed"},
    ),
    "meadow_clover": MudClue(
        key="meadow_clover",
        family="meadow",
        clue_text="a muddy clover head mashed against the top step",
        suspect_reason="Moss had run through the meadow with clover in his fur",
        accusation="You came from the meadow, so you must have bumped everything on the way up.",
        tags={"mud", "meadow", "clover"},
    ),
}


MEMORIES: dict[str, Memory] = {
    "steady_rung": Memory(
        key="steady_rung",
        flashback="Last winter, when one rung shook loose, Moss had planted both feet and held the ladder steady until Bramble climbed down safely.",
        lesson="A friend who keeps you from falling deserves to be heard before being blamed.",
        tags={"flashback", "ladder", "trust"},
    ),
    "shared_cookie": Memory(
        key="shared_cookie",
        flashback="On the first cold night of autumn, Moss had given Bramble the larger half of a moon cookie and said that warm things should be shared.",
        lesson="Kindness remembered can interrupt sharp words.",
        tags={"flashback", "kindness", "trust"},
    ),
    "storm_lantern": Memory(
        key="storm_lantern",
        flashback="During a thunderstorm, Moss had climbed the attic ladder in the dark just to relight the lantern so Bramble would not be afraid.",
        lesson="Courage shown in an earlier hard moment can guide a later choice.",
        tags={"flashback", "courage", "moon"},
    ),
}


CAUSES: dict[str, Cause] = {
    "toad_shelter": Cause(
        key="toad_shelter",
        family="garden",
        need="carry_garden_guest",
        cause_text="a rain-shivering toad had slipped in through the window ledge, hidden under the seed crate, and splashed the moon chart stand with muddy feet",
        discovery="a tiny toad blinking from under the seed crate while the chart stand leaned sideways",
        fix_result="With the little visitor back in the damp garden bed, nothing kept bumping the chart stand anymore.",
        closing_line="The garden smelled sweet again, and the loft stopped feeling cross.",
        tags={"toad", "garden", "guest"},
    ),
    "reed_bucket": Cause(
        key="reed_bucket",
        family="pond",
        need="drain_pond_water",
        cause_text="a forgotten reed bucket of pond water had tipped near the window, sending a muddy ribbon down the side rail and into the moon map pins",
        discovery="the reed bucket lying on its side while pond water dripped from the window sill",
        fix_result="Dry pins held the moon map firm instead of letting it curl.",
        closing_line="The air no longer smelled marshy, and the ladder stopped glistening with slime.",
        tags={"bucket", "pond", "water"},
    ),
    "swallow_chick": Cause(
        key="swallow_chick",
        family="meadow",
        need="settle_meadow_bird",
        cause_text="a soaked swallow chick from the meadow eaves had fluttered in through the attic window, knocked the clover pot, and dabbed muddy wing marks all along the top step",
        discovery="a swallow chick peeping behind the clover pot while loose soil spread under the window",
        fix_result="With the chick safe in its dry eaves nest, no loose wings were left to knock the pot again.",
        closing_line="The rafters grew quiet except for one safe little chirp above them.",
        tags={"swallow", "meadow", "bird"},
    ),
}


REPAIRS: dict[str, Repair] = {
    "carry_garden_guest": Repair(
        key="carry_garden_guest",
        need="carry_garden_guest",
        action_text="Moss cupped the toad in a scarf, and Bramble wiped the muddy stand before they carried their guest back to the wet garden bed below the window.",
        result_text="The moon chart stood straight again once the toad was safe outside.",
        tags={"kindness", "garden", "repair"},
    ),
    "drain_pond_water": Repair(
        key="drain_pond_water",
        need="drain_pond_water",
        action_text="Together they emptied the reed bucket, dried each rung with an old towel, and pressed the damp moon map flat with smooth buttons.",
        result_text="The side rail stopped dripping, and the moon map lay flat again.",
        tags={"water", "pond", "repair"},
    ),
    "settle_meadow_bird": Repair(
        key="settle_meadow_bird",
        need="settle_meadow_bird",
        action_text="Bramble held the little bird close while Moss rebuilt the soft nest in the eaves, and then they brushed the spilled soil from the top step.",
        result_text="The top step cleared, and the clover pot sat upright again.",
        tags={"bird", "meadow", "repair"},
    ),
}


KNOWLEDGE = {
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or storage space high under a roof. It is often reached by a ladder or narrow stairs.",
        )
    ],
    "ladder": [
        (
            "Why should a ladder be kept clean?",
            "A clean ladder is safer to climb because feet do not slide as easily. Mud on a rung can turn a small trip into a fall.",
        )
    ],
    "moon": [
        (
            "What does a twinkling moon mean in a story?",
            "A twinkling moon is a bright moon that seems lively and gentle. Writers often use it to make the ending feel calm or hopeful.",
        )
    ],
    "mud": [
        (
            "Why can mud be a tricky clue?",
            "Mud can show where something came from, but it does not always show who caused the trouble. Many different things can carry the same mud.",
        )
    ],
    "flashback": [
        (
            "What is a flashback?",
            "A flashback is a memory from earlier in the story or from an earlier time. It can help a character understand the present more wisely.",
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people make peace after hurt or anger. They listen, tell the truth, and choose friendship again.",
        )
    ],
    "toad": [
        (
            "Why might a toad hide during rain?",
            "A toad likes damp places, but a sudden hard rain can still make it seek shelter. Small animals often hide wherever they can stay safe for a moment.",
        )
    ],
    "pond": [
        (
            "Why does pond water make a place slippery?",
            "Pond water can carry mud and slime. When that dries or smears on wood, the surface becomes slick.",
        )
    ],
    "bird": [
        (
            "Why would a young bird need help after a storm?",
            "A young bird can become cold, wet, or confused in rough weather. Gentle help can return it to a safe nest.",
        )
    ],
    "kindness": [
        (
            "How can kindness help solve a problem?",
            "Kindness slows angry thoughts and makes room for careful looking. Once people feel safer, they can notice the real cause.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "attic",
    "ladder",
    "moon",
    "mud",
    "flashback",
    "reconciliation",
    "toad",
    "pond",
    "bird",
    "kindness",
]


def clue_matches_cause(clue: MudClue, cause: Cause) -> bool:
    return clue.family == cause.family


def repair_fits_cause(cause: Cause, repair: Repair) -> bool:
    return cause.need == repair.need


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_key in sorted(PLACES):
        for clue_key, clue in CLUES.items():
            for memory_key in sorted(MEMORIES):
                for cause_key, cause in CAUSES.items():
                    for repair_key, repair in REPAIRS.items():
                        if clue_matches_cause(clue, cause) and repair_fits_cause(cause, repair):
                            combos.append((place_key, clue_key, memory_key, cause_key, repair_key))
    return sorted(combos)


def explain_rejection(place_key: str, clue_key: str, memory_key: str, cause_key: str, repair_key: str) -> str:
    place = PLACES[place_key]
    clue = CLUES[clue_key]
    memory = MEMORIES[memory_key]
    cause = CAUSES[cause_key]
    repair = REPAIRS[repair_key]
    reasons: list[str] = []
    if not clue_matches_cause(clue, cause):
        reasons.append(
            f'{clue.key} leaves {clue.family} mud, but {cause.key} comes from {cause.family}; '
            "the clue would not plausibly mislead the hero toward that cause."
        )
    if not repair_fits_cause(cause, repair):
        reasons.append(
            f"{repair.key} does not solve {cause.key}; the repair must answer the actual need."
        )
    if not reasons:
        reasons.append(
            f"The requested combination at {place.house_name} could not produce a grounded attic-ladder reconciliation."
        )
    reasons.append(
        f"Memory {memory.key} is allowed, but the clue/cause/repair chain must still describe one coherent physical mess."
    )
    return "Invalid story choices: " + " ".join(reasons)


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity) -> None:
    place = world.place
    moon = world.get("moon")
    moon.meters["visible"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"In {place.house_name}, Bramble the young squirrel and Moss the rabbit loved to climb {place.ladder_label} each night."
    )
    world.say(
        f"At {place.landing_label}, {place.attic_treasure} waited beneath {place.window_label}, where the twinkling moon shone like a patient silver eye."
    )
    world.say(
        f"Aunt Wren always told them, \"Feet may be quick on a ladder, but words should be careful.\""
    )
    world.log("introduce", hero=hero.id, friend=friend.id, elder=elder.id, place=place.key)


def muddy_discovery(world: World, clue: MudClue, cause: Cause) -> None:
    ladder = world.get("ladder")
    chart = world.get("chart")
    ladder.meters["muddy"] += 1.0
    ladder.meters["safe"] = 0.0
    chart.meters["askew"] += 1.0
    world.say(
        f"After a wet afternoon, Bramble came back to find {clue.clue_text}. The ladder looked muddy clear up to {world.place.landing_label}."
    )
    world.say(
        f"Worse, {world.place.attic_treasure} had been knocked crooked, as if some hurrying body had brushed past it."
    )
    world.facts["mess"] = cause.cause_text
    world.log("muddy_discovery", clue=clue.key, cause_family=cause.family)


def accuse(world: World, clue: MudClue, hero: Entity, friend: Entity) -> None:
    hero.memes["blame"] += 1.0
    friend.memes["hurt"] += 1.0
    world.say(
        f"Bramble remembered that {clue.suspect_reason}. \"Moss,\" he said, \"{clue.accusation}\""
    )
    world.say(
        f"Moss set back his ears. \"I was muddy earlier,\" he said, \"but I did not touch our moon things.\""
    )
    world.log("accusation", hero=hero.id, friend=friend.id, clue=clue.key)


def flashback(world: World, memory: Memory) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1.0
    world.say(
        f"Then a flashback opened in Bramble's mind: {memory.flashback}"
    )
    world.say(
        f"The memory tugged at his temper. {memory.lesson}"
    )
    world.facts["flashback"] = memory.flashback
    world.facts["lesson"] = memory.lesson
    world.log("flashback", memory=memory.key)
    propagate(world)


def investigate(world: World, cause: Cause) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    hero.memes["curiosity"] += 1.0
    friend.memes["courage"] += 1.0
    ladder.meters["true_cause_found"] += 1.0
    world.say(
        f"So Bramble climbed more slowly and looked again. At the top, they discovered {cause.discovery}."
    )
    world.say(
        f"The true trouble was simple and physical: {cause.cause_text}."
    )
    world.facts["true_cause"] = cause.cause_text
    world.facts["discovery"] = cause.discovery
    world.log("investigation", cause=cause.key)
    propagate(world)


def repair_scene(world: World, repair: Repair, cause: Cause) -> None:
    ladder = world.get("ladder")
    chart = world.get("chart")
    ladder.meters["clean"] += 1.0
    ladder.meters["safe"] += 1.0
    chart.meters["steady"] += 1.0
    chart.meters["askew"] = 0.0
    world.say(repair.action_text)
    world.say(
        f"{repair.result_text} {cause.fix_result}"
    )
    world.facts["repair_action"] = repair.action_text
    world.facts["repair_result"] = repair.result_text
    world.log("repair", repair=repair.key)


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1.0
    friend.memes["forgiveness"] += 1.0
    world.say(
        f'Bramble looked down at the clean rung under his paws. "I am sorry I blamed you before I looked properly," he said.'
    )
    world.say(
        f'Moss touched the side rail and nodded. "I was hurt," he said, "but I would rather climb with the truth than sit alone with anger."'
    )
    world.log("reconcile", hero=hero.id, friend=friend.id)
    propagate(world)


def closing(world: World, cause: Cause) -> None:
    moon = world.get("moon")
    if moon.meters["twinkling_seen"] < THRESHOLD:
        raise StoryError("Story did not reach a grounded happy ending under the moon.")
    world.say(
        f"When they looked up again, the twinkling moon poured over {world.place.ending_image}."
    )
    world.say(
        f"Bramble and Moss sat shoulder to shoulder at {world.place.landing_label}. {cause.closing_line}"
    )
    world.say(
        "From then on, Bramble remembered that one muddy step can tell a story, but only patience can tell the whole one."
    )
    world.log("closing", happy="yes")


def tell(place: LadderPlace, clue: MudClue, memory: Memory, cause: Cause, repair: Repair) -> World:
    world = World(place)
    hero = world.add(Entity("Bramble", kind="character", type="boy", label="Bramble", role="hero", traits=["quick"]))
    friend = world.add(Entity("Moss", kind="character", type="rabbit", label="Moss", role="friend", traits=["steady"]))
    elder = world.add(Entity("Aunt Wren", kind="character", type="woman", label="Aunt Wren", role="elder", traits=["wise"]))
    world.add(Entity("ladder", kind="thing", type="ladder", label=place.ladder_label))
    world.add(Entity("chart", kind="thing", type="moon_chart", label=place.attic_treasure))
    world.add(Entity("moon", kind="thing", type="moon", label="twinkling moon"))

    introduce(world, hero, friend, elder)
    world.para()
    muddy_discovery(world, clue, cause)
    accuse(world, clue, hero, friend)
    flashback(world, memory)
    world.para()
    investigate(world, cause)
    repair_scene(world, repair, cause)
    reconcile(world, hero, friend)
    closing(world, cause)

    world.facts.update(
        place=place,
        clue=clue,
        memory=memory,
        cause=cause,
        repair=repair,
        hero=hero,
        friend=friend,
        elder=elder,
        reconciled=bool(world.facts.get("reconciled")),
        happy_ending=bool(world.facts.get("happy_ending")),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    place: LadderPlace = world.facts["place"]  # type: ignore[assignment]
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    return [
        'Write a gentle fable for young children that includes the words "muddy" and "twinkling moon" and takes place on an attic ladder.',
        f"Tell a reconciliation story where Bramble blames Moss after finding {clue.clue_text}, then a flashback helps Bramble discover the true cause.",
        f"Write a happy-ending attic story in {place.house_name} where the moonlit treasure is disturbed because {cause.cause_text}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    repair: Repair = world.facts["repair"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where did the story happen?",
            f"The story happened in the attic of {world.place.house_name}, around {world.place.ladder_label} and {world.place.window_label}. That high little space mattered because the friends climbed there to watch the moon together.",
        ),
        QAItem(
            "Why did Bramble blame Moss at first?",
            f"Bramble saw {clue.clue_text} and remembered that {clue.suspect_reason}. The clue matched Moss's day, so Bramble jumped to a quick and hurtful conclusion.",
        ),
        QAItem(
            "What did the flashback remind Bramble of?",
            f"The flashback reminded Bramble of this earlier moment: {world.facts['flashback']} That memory reminded Bramble that Moss had already proved his kindness and steadiness before.",
        ),
        QAItem(
            "What was the true cause of the muddy mess?",
            f"The real cause was that {cause.cause_text}. Once Bramble and Moss looked carefully, the physical mess made more sense than the first accusation.",
        ),
        QAItem(
            "How did they fix the problem?",
            f"{repair.action_text} That solved the real trouble instead of the imagined one, so the ladder became safe and the moon treasure could be set right.",
        ),
        QAItem(
            "How did the story end?",
            f"Bramble apologized, Moss forgave him, and the friends sat together under the twinkling moon. The clean attic ladder showed the change because the danger and the anger were both gone.",
        ),
    ]


def world_knowledge_questions(world: World) -> list[QAItem]:
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    tags = {"attic", "ladder", "moon", "mud", "flashback", "reconciliation", "kindness"}
    tags |= set(cause.tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(q, a))
    return out


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.memory not in MEMORIES:
        raise StoryError("Unknown place, clue, or memory key.")
    if params.cause not in CAUSES or params.repair not in REPAIRS:
        raise StoryError("Unknown cause or repair key.")
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    memory = MEMORIES[params.memory]
    cause = CAUSES[params.cause]
    repair = REPAIRS[params.repair]
    if not clue_matches_cause(clue, cause) or not repair_fits_cause(cause, repair):
        raise StoryError(explain_rejection(params.place, params.clue, params.memory, params.cause, params.repair))

    world = tell(place, clue, memory, cause, repair)
    if not world.facts.get("happy_ending"):
        raise StoryError("World did not reach the required happy ending.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- ladder_place(P).
clue(C) :- mud_clue(C).
memory(M) :- flashback_memory(M).
cause(K) :- true_cause(K).
repair(R) :- repair_action(R).

valid(P,C,M,K,R) :-
    place(P), clue(C), memory(M), cause(K), repair(R),
    clue_family(C,F), cause_family(K,F),
    cause_need(K,N), repair_need(R,N).

#show valid/5.
"""


def asp_facts() -> str:
    import asp

    rows: list[str] = []
    for place in PLACES.values():
        rows.append(asp.fact("ladder_place", place.key))
    for clue in CLUES.values():
        rows.append(asp.fact("mud_clue", clue.key))
        rows.append(asp.fact("clue_family", clue.key, clue.family))
    for memory in MEMORIES.values():
        rows.append(asp.fact("flashback_memory", memory.key))
    for cause in CAUSES.values():
        rows.append(asp.fact("true_cause", cause.key))
        rows.append(asp.fact("cause_family", cause.key, cause.family))
        rows.append(asp.fact("cause_need", cause.key, cause.need))
    for repair in REPAIRS.values():
        rows.append(asp.fact("repair_action", repair.key))
        rows.append(asp.fact("repair_need", repair.key, repair.need))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(tuple(str(x) for x in atom) for atom in asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1
    for idx, combo in enumerate(sorted(py), start=1):
        sample = generate(StoryParams(*combo, seed=idx))
        if "muddy" not in sample.story or "twinkling moon" not in sample.story:
            print("Generated story missed required seed words for combo:", combo)
            return 1
        if "attic ladder" not in sample.story:
            print("Generated story missed attic ladder setting for combo:", combo)
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("Generated story missed QA output for combo:", combo)
            return 1
        if not sample.world.facts.get("happy_ending"):
            print("Generated story failed to reach happy ending for combo:", combo)
            return 1
    print(f"OK: Python and ASP agree on {len(py)} valid attic-ladder fables, and all generated stories pass basic checks.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Storyworld: muddy attic ladder fable with flashback, reconciliation, and a happy ending."
    )
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--memory", choices=sorted(MEMORIES))
    parser.add_argument("--cause", choices=sorted(CAUSES))
    parser.add_argument("--repair", choices=sorted(REPAIRS))
    parser.add_argument("--seed", type=int)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.memory is None or combo[2] == args.memory)
        and (args.cause is None or combo[3] == args.cause)
        and (args.repair is None or combo[4] == args.repair)
    ]
    if not choices:
        place_key = args.place or sorted(PLACES)[0]
        clue_key = args.clue or sorted(CLUES)[0]
        memory_key = args.memory or sorted(MEMORIES)[0]
        cause_key = args.cause or sorted(CAUSES)[0]
        repair_key = args.repair or sorted(REPAIRS)[0]
        raise StoryError(explain_rejection(place_key, clue_key, memory_key, cause_key, repair_key))
    place_key, clue_key, memory_key, cause_key, repair_key = rng.choice(sorted(choices))
    seed = (args.seed if args.seed is not None else 1000) + index
    return StoryParams(place_key, clue_key, memory_key, cause_key, repair_key, seed=seed)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print()
        print("PROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print()
        print("STORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("WORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        base_seed = args.seed if args.seed is not None else 1000
        return [
            generate(StoryParams(*combo, seed=base_seed + idx))
            for idx, combo in enumerate(valid_combos(), start=1)
        ]

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    seen: set[str] = set()
    samples: list[StorySample] = []
    attempts = 0
    i = 0
    while len(samples) < target and attempts < target * 30:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed), index=i)
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Could not generate enough unique attic-ladder stories with the requested constraints.")
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    try:
        samples = samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
        return 2

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0

    for idx, sample in enumerate(samples, start=1):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"=== place={p.place} clue={p.clue} memory={p.memory} "
                f"cause={p.cause} repair={p.repair} seed={p.seed} ==="
            )
        elif len(samples) > 1:
            header = f"=== muddy_twinkling_moon_attic_ladder_reconciliation_flashback #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
