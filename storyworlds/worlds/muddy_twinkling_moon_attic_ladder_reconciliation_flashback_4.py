#!/usr/bin/env python3
"""
Standalone storyworld for a TinyStories-style seed:

    Words: muddy, twinkling moon
    Setting: attic ladder
    Features: Reconciliation, Flashback, Happy Ending
    Style: Fable

Internal source tale:
    In a roof-high loft, two small friends climb an attic ladder each evening to
    visit a moon keepsake. After rain, a muddy trace appears on the rungs and the
    keepsake hangs crooked. One friend blames the other too quickly, but a
    flashback recalls an old kindness on that same ladder. The memory slows the
    quarrel, both friends inspect the loft, discover a grounded physical cause,
    repair the mess together, and reconcile under the twinkling moon.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass(frozen=True)
class AtticPlace:
    key: str
    cottage_name: str
    ladder_label: str
    loft_label: str
    window_label: str
    moon_object: str
    moon_name: str
    ending_image: str
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class MudClue:
    key: str
    family: str
    clue_text: str
    blame_reason: str
    accusation: str
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Memory:
    key: str
    flashback: str
    lesson: str
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Cause:
    key: str
    family: str
    need: str
    required_tag: str
    discovery: str
    cause_text: str
    fix_result: str
    closing_line: str
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class Repair:
    key: str
    need: str
    action_text: str
    result_text: str
    tags: frozenset[str] = field(default_factory=frozenset)


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass(frozen=True)
class StoryParams:
    place: str
    clue: str
    memory: str
    cause: str
    repair: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: AtticPlace) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple[str, ...]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        if ent.role:
            self.entities[ent.role] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        text = text.strip()
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(parts) for parts in self.paragraphs if parts)

    def log(self, event: str, **details: str) -> None:
        row = {"event": event}
        row.update({key: str(value) for key, value in details.items()})
        self.history.append(row)

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


PLACES: dict[str, AtticPlace] = {
    "mill_loft": AtticPlace(
        key="mill_loft",
        cottage_name="the flour-mill cottage",
        ladder_label="the mill attic ladder",
        loft_label="the beam-loft over the mill room",
        window_label="the round loft window",
        moon_object="their willow moon garland above a berry basket",
        moon_name="moon garland",
        ending_image="the dry ladder glowing like pale wheat",
        tags=frozenset({"willow_basket", "moon_window"}),
    ),
    "peat_attic": AtticPlace(
        key="peat_attic",
        cottage_name="the peat-roof house",
        ladder_label="the peat attic ladder",
        loft_label="the snug loft tucked beneath the roof boards",
        window_label="the small roof pane",
        moon_object="their tin moon lantern beside an old peat chest",
        moon_name="moon lantern",
        ending_image="the straight moon lantern shining above the top rung",
        tags=frozenset({"peat_chest", "moon_window"}),
    ),
    "swallow_eaves": AtticPlace(
        key="swallow_eaves",
        cottage_name="the swallow-eaves cottage",
        ladder_label="the swallow attic ladder",
        loft_label="the eaves loft with low rafters",
        window_label="the moon slit under the tiles",
        moon_object="their silver moon mobile near a swallow basket",
        moon_name="moon mobile",
        ending_image="the clean top step bright beneath the rafters",
        tags=frozenset({"eaves_nest", "moon_window"}),
    ),
}


CLUES: dict[str, MudClue] = {
    "willow_strip": MudClue(
        key="willow_strip",
        family="basket",
        clue_text="a muddy strip of willow bark clinging to the fifth rung",
        blame_reason="Moss had been mending the berry basket with wet willow after the rain",
        accusation="you were working with the damp willow, so you must have bent our moon garland",
        tags=frozenset({"mud", "basket", "willow"}),
    ),
    "peat_smear": MudClue(
        key="peat_smear",
        family="chest",
        clue_text="a muddy peat smear darkening the top rail",
        blame_reason="Moss had opened the peat chest before supper to fetch an attic cloth",
        accusation="you were at the chest, so this muddy mark and the crooked lantern must be your doing",
        tags=frozenset({"mud", "chest", "peat"}),
    ),
    "feather_dab": MudClue(
        key="feather_dab",
        family="eaves",
        clue_text="a muddy feather and a dab of straw pressed against the side rung",
        blame_reason="Moss had checked the swallows near the eaves that afternoon",
        accusation="you were near the swallows, so these muddy signs must have come from you",
        tags=frozenset({"mud", "eaves", "feather"}),
    ),
}


MEMORIES: dict[str, Memory] = {
    "steady_shoulder": Memory(
        key="steady_shoulder",
        flashback="One frosty evening, Pia had slipped on the same ladder, and Moss had braced his shoulder beneath her foot until she found the next rung.",
        lesson="A friend who keeps you from falling deserves a careful hearing before blame.",
        tags=frozenset({"flashback", "ladder", "safety"}),
    ),
    "pear_share": Memory(
        key="pear_share",
        flashback="At midsummer, Moss had broken his last pear tart in half and quietly given Pia the larger piece when he saw her hungry face.",
        lesson="Remembered generosity can loosen the knot of a harsh guess.",
        tags=frozenset({"flashback", "sharing", "kindness"}),
    ),
    "storm_hum": Memory(
        key="storm_hum",
        flashback="During a roof-rattling storm, Moss had climbed first and hummed a calm tune so Pia would not be afraid of the thunder above the loft.",
        lesson="Old courage can cool a new suspicion before the tongue runs ahead of the truth.",
        tags=frozenset({"flashback", "courage", "moon"}),
    ),
    "blanket_wait": Memory(
        key="blanket_wait",
        flashback="One late autumn night, Moss had waited on the middle rung with a wool blanket until Pia finished watching the moon, because he knew she hated climbing down cold and alone.",
        lesson="Patient care in an older moment can teach patience in a troubled one.",
        tags=frozenset({"flashback", "care", "moon"}),
    ),
}


CAUSES: dict[str, Cause] = {
    "hedgehog_kit": Cause(
        key="hedgehog_kit",
        family="basket",
        need="guide_hedgehog",
        required_tag="willow_basket",
        discovery="a rain-damp hedgehog kit nosing around inside the berry basket while the moon garland leaned sideways above it",
        cause_text="a little hedgehog kit had waddled in through the window crack, rubbed its muddy side against the basket, and bumped the moon garland while looking for a dark place to hide",
        fix_result="Once the hedgehog kit was carried back to the herb bed, nothing else nudged the garland or tracked fresh mud across the rungs.",
        closing_line="The loft still smelled faintly of rain and herbs, but the sharp smell of quarrel was gone.",
        tags=frozenset({"hedgehog", "basket", "garden"}),
    ),
    "dripping_bowl": Cause(
        key="dripping_bowl",
        family="chest",
        need="empty_bowl",
        required_tag="peat_chest",
        discovery="a cracked wash bowl tipped beside the peat chest, leaking brown rainwater toward the lantern hook",
        cause_text="roof drips had filled a cracked wash bowl with muddy water, and when the bowl tipped, the spill slid along the rail and tugged the moon lantern crooked",
        fix_result="After the bowl was emptied and the rail was dried, the muddy line disappeared and the lantern hung true again.",
        closing_line="Even the old chest seemed to rest more honestly once the dripping stopped.",
        tags=frozenset({"bowl", "rainwater", "chest"}),
    ),
    "swallow_chick": Cause(
        key="swallow_chick",
        family="eaves",
        need="return_swallow",
        required_tag="eaves_nest",
        discovery="a damp swallow chick peeping behind a spool box while loose straw clung to the ladder",
        cause_text="a frightened swallow chick had tumbled from the eaves, fluttered under the moon mobile, and left muddy spots as it hopped about seeking shelter",
        fix_result="When the chick was tucked back into its nest, the loft grew still and no fresh wings shook the moon mobile again.",
        closing_line="A soft peep drifted from the eaves as if the roof itself approved of peace.",
        tags=frozenset({"swallow", "bird", "eaves"}),
    ),
}


REPAIRS: dict[str, Repair] = {
    "guide_hedgehog": Repair(
        key="guide_hedgehog",
        need="guide_hedgehog",
        action_text="Pia slid a grain scoop under the tiny hedgehog kit while Moss wiped each muddy rung with a flour cloth, and together they carried the sleepy visitor back to the herb bed.",
        result_text="The ladder felt safe under their feet again, and the willow moon garland stopped swaying once the basket corner was quiet.",
        tags=frozenset({"repair", "garden", "gentleness"}),
    ),
    "empty_bowl": Repair(
        key="empty_bowl",
        need="empty_bowl",
        action_text="Moss steadied the moon lantern while Pia tipped the cracked bowl empty, dried the rail with the attic cloth, and set a fresh pan beneath the roof drip.",
        result_text="The muddy water was gone, and the top rail felt dry and trustworthy again.",
        tags=frozenset({"repair", "drying", "rainwater"}),
    ),
    "return_swallow": Repair(
        key="return_swallow",
        need="return_swallow",
        action_text="Pia cupped the shivering swallow chick in her apron while Moss rebuilt the nest edge and brushed the muddy straw from the ladder.",
        result_text="The ladder turned neat once more, and the silver moon mobile stopped trembling when the chick was safe above the rafters.",
        tags=frozenset({"repair", "bird", "care"}),
    ),
}


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or storage space high under a roof. People or animals often reach it by a ladder or narrow stairs.",
        )
    ],
    "ladder": [
        (
            "Why do clean ladder rungs matter?",
            "Clean rungs help paws and feet grip safely. Mud can turn an easy climb into a risky slip.",
        )
    ],
    "moon": [
        (
            "Why does a twinkling moon fit a fable ending?",
            "A twinkling moon makes the ending feel quiet and watchful. It can also show that trouble has settled into peace.",
        )
    ],
    "mud": [
        (
            "Why can muddy traces lead to a wrong guess?",
            "Mud shows that something wet passed by, but it does not always reveal who caused the trouble. Careful looking must come before blame.",
        )
    ],
    "flashback": [
        (
            "What does a flashback do in a story?",
            "A flashback brings an older moment into the present one. That remembered moment can change how a character understands what is happening now.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is the making of peace after hurt or anger. It usually needs truth, apology, and willing hearts on both sides.",
        )
    ],
    "hedgehog": [
        (
            "Why might a little hedgehog track mud indoors?",
            "A hedgehog close to a wet garden can carry damp soil on its feet and belly. If it wanders inside, it can leave muddy marks behind.",
        )
    ],
    "bowl": [
        (
            "Why can a cracked bowl make a mess?",
            "A cracked bowl can fill and tip without warning. If the water is dirty, the spill can spread mud wherever it runs.",
        )
    ],
    "swallow": [
        (
            "Why should a fallen swallow chick be handled gently?",
            "A young bird can panic when it falls from a nest. Calm and careful help can return it safely before cold or fear harms it.",
        )
    ],
    "kindness": [
        (
            "How can kindness help a quarrel end well?",
            "Kindness slows the tongue long enough for the truth to appear. Once hearts feel heard, people can mend both the problem and the friendship.",
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
    "hedgehog",
    "bowl",
    "swallow",
    "kindness",
]


def clue_matches_cause(clue: MudClue, cause: Cause) -> bool:
    return clue.family == cause.family


def repair_fits_cause(cause: Cause, repair: Repair) -> bool:
    return cause.need == repair.need


def place_supports_cause(place: AtticPlace, cause: Cause) -> bool:
    return cause.required_tag in place.tags


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_key, place in PLACES.items():
        for clue_key, clue in CLUES.items():
            for memory_key in MEMORIES:
                for cause_key, cause in CAUSES.items():
                    for repair_key, repair in REPAIRS.items():
                        if not clue_matches_cause(clue, cause):
                            continue
                        if not repair_fits_cause(cause, repair):
                            continue
                        if not place_supports_cause(place, cause):
                            continue
                        combos.append((place_key, clue_key, memory_key, cause_key, repair_key))
    return sorted(combos)


def explain_rejection(
    place_key: str,
    clue_key: str,
    memory_key: str,
    cause_key: str,
    repair_key: str,
) -> str:
    place = PLACES[place_key]
    clue = CLUES[clue_key]
    memory = MEMORIES[memory_key]
    cause = CAUSES[cause_key]
    repair = REPAIRS[repair_key]
    reasons: list[str] = []
    if not clue_matches_cause(clue, cause):
        reasons.append(
            f"{clue.key} suggests {clue.family} evidence, but {cause.key} describes {cause.family} trouble."
        )
    if not repair_fits_cause(cause, repair):
        reasons.append(f"{repair.key} does not solve the need created by {cause.key}.")
    if not place_supports_cause(place, cause):
        reasons.append(
            f"{place.key} does not contain the physical setup required for {cause.key}."
        )
    if not reasons:
        reasons.append("The requested choices do not form one grounded attic-ladder fable.")
    reasons.append(
        f"Memory {memory.key} may vary freely, but place, clue, cause, and repair still need to describe one believable mess and one believable fix."
    )
    return "Invalid story choices: " + " ".join(reasons)


def _r_flashback_checks_haste(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["blame"] < THRESHOLD or hero.memes["flashback"] < THRESHOLD:
        return False
    sig = ("flashback_checks_haste", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = max(0.0, hero.memes["blame"] - 0.5)
    hero.memes["reflection"] += 1.0
    hero.memes["trust"] += 0.5
    friend.memes["hope"] += 0.5
    world.log("flashback_checks_haste", hero=hero.id, friend=friend.id)
    return True


def _r_truth_cools_hurt(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    if ladder.meters["true_cause_found"] < THRESHOLD:
        return False
    sig = ("truth_cools_hurt", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = 0.0
    hero.memes["understanding"] += 1.0
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 0.5)
    world.facts["truth_seen"] = True
    world.log("truth_cools_hurt", hero=hero.id, friend=friend.id)
    return True


def _r_shared_work_restores_friendship(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    moon_object = world.get("moon_object")
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return False
    if ladder.meters["clean"] < THRESHOLD or ladder.meters["safe"] < THRESHOLD:
        return False
    if moon_object.meters["steady"] < THRESHOLD:
        return False
    sig = ("shared_work_restores_friendship", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.get("moon").meters["twinkling_seen"] += 1.0
    world.facts["reconciled"] = True
    world.facts["happy_ending"] = True
    world.log("shared_work_restores_friendship", hero=hero.id, friend=friend.id)
    return True


CAUSAL_RULES = [
    _r_flashback_checks_haste,
    _r_truth_cools_hurt,
    _r_shared_work_restores_friendship,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity) -> None:
    world.get("moon").meters["visible"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"In {world.place.cottage_name}, Pia the mouse and Moss the mole loved to climb {world.place.ladder_label} when evening turned blue and quiet."
    )
    world.say(
        f"At {world.place.loft_label}, {world.place.moon_object} waited beneath {world.place.window_label}, where the twinkling moon looked in like a patient eye."
    )
    world.say(
        'Old Finch, who slept on a beam nearby, often told them, "In a fable, the first muddy sign is not always the truest one."'
    )
    world.log("introduce", hero=hero.id, friend=friend.id, elder=elder.id, place=world.place.key)


def discover_mess(world: World, clue: MudClue) -> None:
    ladder = world.get("ladder")
    moon_object = world.get("moon_object")
    ladder.meters["muddy"] += 1.0
    ladder.meters["safe"] = 0.0
    moon_object.meters["crooked"] += 1.0
    world.say(
        f"After a day of rain, Pia found {clue.clue_text}. The attic ladder looked muddy almost to the top."
    )
    world.say(
        f"Worse, {world.place.moon_object} hung crooked, as if something wet and hurried had brushed past it."
    )
    world.facts["mess_seen"] = True
    world.log("discover_mess", clue=clue.key)


def accuse(world: World, clue: MudClue, hero: Entity, friend: Entity) -> None:
    hero.memes["blame"] += 1.0
    friend.memes["hurt"] += 1.0
    world.say(
        f'Pia remembered that {clue.blame_reason}. She turned to Moss and said, "Moss, {clue.accusation}."'
    )
    world.say(
        '"I was near it earlier," Moss answered, "but I did not twist our moon treasure."'
    )
    world.log("accuse", hero=hero.id, friend=friend.id, clue=clue.key)


def remember(world: World, memory: Memory) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1.0
    world.say(f"Then a flashback opened in Pia's mind: {memory.flashback}")
    world.say(f"The memory cooled her first hot thought. {memory.lesson}")
    world.facts["flashback_text"] = memory.flashback
    world.facts["flashback_lesson"] = memory.lesson
    world.log("remember", memory=memory.key)
    propagate(world)


def investigate(world: World, cause: Cause) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    hero.memes["curiosity"] += 1.0
    friend.memes["steadiness"] += 1.0
    ladder.meters["true_cause_found"] += 1.0
    world.say(
        f"So Pia climbed more slowly and looked again. At the top, she and Moss discovered {cause.discovery}."
    )
    world.say(f"The true trouble was plain and physical: {cause.cause_text}.")
    world.facts["discovery"] = cause.discovery
    world.facts["true_cause"] = cause.cause_text
    world.log("investigate", cause=cause.key)
    propagate(world)


def repair_scene(world: World, repair: Repair, cause: Cause) -> None:
    ladder = world.get("ladder")
    moon_object = world.get("moon_object")
    ladder.meters["clean"] += 1.0
    ladder.meters["safe"] += 1.0
    moon_object.meters["steady"] += 1.0
    moon_object.meters["crooked"] = 0.0
    world.say(repair.action_text)
    world.say(f"{repair.result_text} {cause.fix_result}")
    world.facts["repair_action"] = repair.action_text
    world.facts["repair_result"] = repair.result_text
    world.log("repair_scene", repair=repair.key)


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1.0
    friend.memes["forgiveness"] += 1.0
    world.say(
        '"Moss," Pia said, resting one paw on the clean rung, "I am sorry I blamed you before I looked with care."'
    )
    world.say(
        f'"My feelings were sore," Moss said, touching the straightened {world.place.moon_name}, "but truth and kindness mend quicker when friends carry them together."'
    )
    world.log("reconcile", hero=hero.id, friend=friend.id)
    propagate(world)


def closing(world: World, cause: Cause) -> None:
    if not world.facts.get("happy_ending"):
        raise StoryError("Story did not reach the required happy ending.")
    world.say(
        f"When they looked up again, the twinkling moon silvered {world.place.ending_image}."
    )
    world.say(
        f"Pia and Moss sat shoulder to shoulder in {world.place.loft_label}. {cause.closing_line}"
    )
    world.say(
        "From that evening on, Pia remembered the attic lesson: muddy signs may begin a quarrel, but patient truth can end one in peace."
    )
    world.log("closing", happy="yes")


def tell(
    place: AtticPlace,
    clue: MudClue,
    memory: Memory,
    cause: Cause,
    repair: Repair,
) -> World:
    world = World(place)
    hero = world.add(
        Entity("Pia", kind="character", type="mouse", label="Pia", role="hero", traits=["quick"])
    )
    friend = world.add(
        Entity("Moss", kind="character", type="mole", label="Moss", role="friend", traits=["steady"])
    )
    elder = world.add(
        Entity("Old Finch", kind="character", type="bird", label="Old Finch", role="elder", traits=["wise"])
    )
    world.add(Entity("ladder", kind="thing", type="ladder", label=place.ladder_label))
    world.add(Entity("moon_object", kind="thing", type="moon_object", label=place.moon_object))
    world.add(Entity("moon", kind="thing", type="moon", label="twinkling moon"))

    introduce(world, hero, friend, elder)
    world.para()
    discover_mess(world, clue)
    accuse(world, clue, hero, friend)
    remember(world, memory)
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
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    return [
        'Write a gentle fable for children that includes the words "muddy" and "twinkling moon" and takes place on an attic ladder.',
        f"Tell a reconciliation story in which Pia blames Moss after finding {clue.clue_text}, but a flashback teaches her patience.",
        f"Write a happy-ending attic tale where the moon keepsake is disturbed because {cause.cause_text}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    repair: Repair = world.facts["repair"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where does the story happen?",
            f"The story happens in {world.place.cottage_name}, around {world.place.ladder_label} and {world.place.window_label}. That attic space matters because Pia and Moss climb there to visit their moon keepsake together.",
        ),
        QAItem(
            "Why did Pia blame Moss at first?",
            f"Pia saw {clue.clue_text} and remembered that {clue.blame_reason}. The clue seemed to point toward Moss, so she spoke before she had checked the whole loft.",
        ),
        QAItem(
            "What did the flashback change for Pia?",
            f"The flashback reminded Pia of this earlier kindness: {world.facts['flashback_text']} Because of that memory, her anger slowed and she treated Moss like a friend worth hearing.",
        ),
        QAItem(
            "What really caused the muddy mess?",
            f"The real cause was that {cause.cause_text}. Once Pia and Moss searched carefully, the physical signs matched that cause better than Pia's first guess.",
        ),
        QAItem(
            "How did the friends fix the problem?",
            f"{repair.action_text} That repair solved the true source of the mess, so the ladder became safe again and the {world.place.moon_name} could hang straight.",
        ),
        QAItem(
            "How do we know the ending is happy?",
            f"Pia apologized, Moss forgave her, and they sat together under the twinkling moon. The clean ladder and the steady moon keepsake showed that both the quarrel and the mess were truly over.",
        ),
    ]


def world_knowledge_questions(world: World) -> list[QAItem]:
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    tags = {"attic", "ladder", "moon", "mud", "flashback", "reconciliation", "kindness"}
    tags |= set(cause.tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag not in tags:
            continue
        for question, answer in KNOWLEDGE[tag]:
            out.append(QAItem(question, answer))
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

    if not clue_matches_cause(clue, cause):
        raise StoryError(explain_rejection(params.place, params.clue, params.memory, params.cause, params.repair))
    if not repair_fits_cause(cause, repair):
        raise StoryError(explain_rejection(params.place, params.clue, params.memory, params.cause, params.repair))
    if not place_supports_cause(place, cause):
        raise StoryError(explain_rejection(params.place, params.clue, params.memory, params.cause, params.repair))

    world = tell(place, clue, memory, cause, repair)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
        world=world,
    )


ASP_RULES = r"""
same_family(CL,CA) :- clue_family(CL,F), cause_family(CA,F).
solves(CA,RP) :- cause_need(CA,N), repair_need(RP,N).
supported(P,CA) :- place_tag(P,T), cause_requires(CA,T).
valid(P,CL,M,CA,RP) :-
    place(P),
    clue(CL),
    memory(M),
    cause(CA),
    repair(RP),
    same_family(CL,CA),
    solves(CA,RP),
    supported(P,CA).
#show valid/5.
"""


def asp_facts() -> str:
    from storyworlds import asp

    facts: list[str] = []
    for place in PLACES.values():
        facts.append(asp.fact("place", place.key))
        for tag in sorted(place.tags):
            facts.append(asp.fact("place_tag", place.key, tag))
    for clue in CLUES.values():
        facts.append(asp.fact("clue", clue.key))
        facts.append(asp.fact("clue_family", clue.key, clue.family))
    for memory in MEMORIES.values():
        facts.append(asp.fact("memory", memory.key))
    for cause in CAUSES.values():
        facts.append(asp.fact("cause", cause.key))
        facts.append(asp.fact("cause_family", cause.key, cause.family))
        facts.append(asp.fact("cause_need", cause.key, cause.need))
        facts.append(asp.fact("cause_requires", cause.key, cause.required_tag))
    for repair in REPAIRS.values():
        facts.append(asp.fact("repair", repair.key))
        facts.append(asp.fact("repair_need", repair.key, repair.need))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    from storyworlds import asp

    combos: set[tuple[str, str, str, str, str]] = set()
    for model in asp.solve(asp_facts() + ASP_RULES):
        for atom in asp.atoms(model, "valid"):
            combos.add(tuple(str(x) for x in atom))  # type: ignore[arg-type]
    return sorted(combos)


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py != lp:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(py - lp))
        print("Only ASP:", sorted(lp - py))
        return 1

    for combo in sorted(py):
        sample = generate(StoryParams(*combo, seed=0))
        if "muddy" not in sample.story or "twinkling moon" not in sample.story:
            print("Generated story missed required seed words:", combo)
            return 1
        if not sample.world or not sample.world.facts.get("happy_ending"):
            print("Generated story did not reach a happy ending:", combo)
            return 1
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 4:
            print("Generated story did not produce enough QA:", combo)
            return 1
    print(f"OK: Python and ASP agree on {len(py)} valid muddy moon attic fables, and every generated sample passed basic verification.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
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
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def filtered_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str]]:
    return [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.memory is None or combo[2] == args.memory)
        and (args.cause is None or combo[3] == args.cause)
        and (args.repair is None or combo[4] == args.repair)
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    choices = filtered_combos(args)
    if not choices:
        place = args.place or sorted(PLACES)[0]
        clue = args.clue or sorted(CLUES)[0]
        memory = args.memory or sorted(MEMORIES)[0]
        cause = args.cause or sorted(CAUSES)[0]
        repair = args.repair or sorted(REPAIRS)[0]
        raise StoryError(explain_rejection(place, clue, memory, cause, repair))
    combo = choices[index % len(choices)] if args.all else rng.choice(choices)
    return StoryParams(*combo, seed=args.seed)


def format_qa(title: str, items: list[QAItem]) -> list[str]:
    lines = [title]
    for item in items:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return lines


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
        print("\n".join(format_qa("STORY QA", sample.story_qa)))
        print()
        print("\n".join(format_qa("WORLD KNOWLEDGE QA", sample.world_qa)))
    if trace and sample.world is not None:
        print()
        print("TRACE")
        print(sample.world.trace())


def samples_from_args(args: argparse.Namespace) -> list[StorySample]:
    if args.all:
        choices = filtered_combos(args)
        if not choices:
            resolve_params(args, random.Random(args.seed if args.seed is not None else 0))
        samples: list[StorySample] = []
        for idx, combo in enumerate(choices):
            seed = (args.seed if args.seed is not None else 1) + idx
            samples.append(generate(StoryParams(*combo, seed=seed)))
        return samples

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    i = 0
    attempts = 0
    while len(samples) < target and attempts < target * 30:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = argparse.Namespace(**vars(args))
        local_args.seed = seed
        params = resolve_params(local_args, random.Random(seed))
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.show_asp:
        print(asp_facts() + ASP_RULES)
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print(" ".join(combo))
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = (
                "=== muddy_twinkling_moon_attic_ladder_reconciliation_flashback_4 "
                f"#{idx} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
