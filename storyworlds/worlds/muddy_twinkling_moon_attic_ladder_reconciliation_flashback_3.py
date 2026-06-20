#!/usr/bin/env python3
"""
Standalone storyworld for a TinyStories-style seed:

    Words: muddy, twinkling moon
    Setting: attic ladder
    Features: Reconciliation, Flashback, Happy Ending
    Style: Fable

Internal source tale:
    Two small friends climb an attic ladder to visit a moon charm in a high loft.
    After rain, muddy traces appear and the charm is knocked crooked. One friend
    blames the other too quickly, then a flashback recalls an older kindness on
    the same ladder. That memory slows the quarrel long enough for both friends
    to inspect the loft, find a grounded physical cause, fix it together, and
    reconcile under the twinkling moon.
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
    suspect_reason: str
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
    attrs: dict[str, str] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))


@dataclass
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
    "ivy_gable": AtticPlace(
        key="ivy_gable",
        cottage_name="the mossy gable cottage",
        ladder_label="the ivy attic ladder",
        loft_label="the ivy loft under the rafters",
        window_label="the little crescent attic window",
        moon_object="their tin moon charm above a basket of ribbon",
        moon_name="moon charm",
        ending_image="the clean ladder shining pale as oat straw",
        tags=frozenset({"ivy_rope", "moon_window"}),
    ),
    "cedar_loft": AtticPlace(
        key="cedar_loft",
        cottage_name="the cedar seed house",
        ladder_label="the cedar attic ladder",
        loft_label="the cedar loft with low beams",
        window_label="the round moon pane",
        moon_object="their painted moon plate beside a cedar trunk",
        moon_name="moon plate",
        ending_image="the straight moon plate glowing above the top step",
        tags=frozenset({"cedar_trunk", "moon_window"}),
    ),
    "sparrow_nook": AtticPlace(
        key="sparrow_nook",
        cottage_name="the thatched sparrow cottage",
        ladder_label="the sparrow attic ladder",
        loft_label="the sparrow nook near the eaves",
        window_label="the high attic moon slit",
        moon_object="their silver moon spinner tied near a spool shelf",
        moon_name="moon spinner",
        ending_image="the top rung dry and bright beneath the roof beams",
        tags=frozenset({"eaves_hook", "cedar_trunk"}),
    ),
}


CLUES: dict[str, MudClue] = {
    "ivy_leaf": MudClue(
        key="ivy_leaf",
        family="ivy",
        clue_text="a muddy ivy leaf stuck to the fourth rung",
        suspect_reason="Jun had braided an ivy ring that afternoon after the rain",
        accusation="you were working with the wet ivy, so this crooked moon charm must be your fault",
        tags=frozenset({"mud", "ivy"}),
    ),
    "clay_bead": MudClue(
        key="clay_bead",
        family="trunk",
        clue_text="a muddy clay bead rolled against the top step",
        suspect_reason="Jun had opened the cedar trunk to search for old clay marbles",
        accusation="you were the one at the cedar trunk, so you must have made this muddy mess",
        tags=frozenset({"mud", "trunk", "clay"}),
    ),
    "feather_fluff": MudClue(
        key="feather_fluff",
        family="eaves",
        clue_text="a muddy tuft of feather fluff pasted to the side rail",
        suspect_reason="Jun had checked the eaves nest before supper",
        accusation="you were by the eaves nest, so these muddy marks must have come from you",
        tags=frozenset({"mud", "eaves", "feather"}),
    ),
}


MEMORIES: dict[str, Memory] = {
    "steady_paws": Memory(
        key="steady_paws",
        flashback="Last winter, when one rung cracked with a dry little snap, Jun had planted both paws on the ladder and held it steady until Mira reached the floor.",
        lesson="A friend who keeps you safe on a shaking ladder deserves patience when trouble appears.",
        tags=frozenset({"flashback", "ladder", "safety"}),
    ),
    "berry_share": Memory(
        key="berry_share",
        flashback="On the first warm night of spring, Jun had split his last berry tart in two and pushed the larger half toward Mira without a word.",
        lesson="Remembered generosity can soften a hard guess before it becomes a hurtful one.",
        tags=frozenset({"flashback", "kindness", "sharing"}),
    ),
    "storm_song": Memory(
        key="storm_song",
        flashback="During a stormy dusk, Jun had climbed the attic ladder humming a brave little song so Mira would not sit alone under the banging roof.",
        lesson="Old courage can quiet new suspicion when the heart begins to race.",
        tags=frozenset({"flashback", "courage", "moon"}),
    ),
}


CAUSES: dict[str, Cause] = {
    "toadlet_visit": Cause(
        key="toadlet_visit",
        family="ivy",
        need="escort_toadlet",
        required_tag="ivy_rope",
        discovery="a tiny toadlet crouching inside the ivy basket while the moon charm hung crooked above it",
        cause_text="a rain-wet toadlet had climbed the ivy rope through the window, brushed the moon charm with its round back, and left muddy flecks as it searched for a dark corner",
        fix_result="Once the toadlet was carried back to the damp garden bed, the loft stayed still and nothing nudged the charm again.",
        closing_line="The loft smelled of cedar and wet leaves, but not of quarrel anymore.",
        tags=frozenset({"toadlet", "ivy", "garden"}),
    ),
    "jar_spill": Cause(
        key="jar_spill",
        family="trunk",
        need="mop_jar",
        required_tag="cedar_trunk",
        discovery="a cracked seed jar on its side beside the trunk, dripping brown water toward the moon plate stand",
        cause_text="rainwater had slipped through a loose roof seam into a cracked seed jar, and the jar had tipped over and sent a muddy trickle down the ladder rail into the moon stand",
        fix_result="When the jar was emptied and the rail was dried, the muddy line vanished and the moon keepsake could hang straight again.",
        closing_line="Even the old trunk seemed to settle with a quiet, honest sigh.",
        tags=frozenset({"jar", "trunk", "rainwater"}),
    ),
    "swallow_chick": Cause(
        key="swallow_chick",
        family="eaves",
        need="return_chick",
        required_tag="eaves_hook",
        discovery="a damp swallow chick peeping behind a spool box while loose nest fluff clung to the top rung",
        cause_text="a startled swallow chick had tumbled in from the eaves, bumped the moon spinner sideways, and tracked muddy spots while it hopped about looking for shelter",
        fix_result="After the chick was tucked back into its nest, no more frightened wings shook the moon keepsake or scattered fresh mud.",
        closing_line="A soft chirp drifted from the eaves as if the roof itself had joined the peace.",
        tags=frozenset({"bird", "eaves", "chick"}),
    ),
}


REPAIRS: dict[str, Repair] = {
    "escort_toadlet": Repair(
        key="escort_toadlet",
        need="escort_toadlet",
        action_text="Mira scooped the little toadlet onto a dustpan while Jun wiped each muddy rung with a cloth, and together they carried the visitor back to the moonlit ivy patch.",
        result_text="The ladder grew safe under their feet again, and the moon charm stopped swaying once the basket was empty.",
        tags=frozenset({"repair", "garden", "care"}),
    ),
    "mop_jar": Repair(
        key="mop_jar",
        need="mop_jar",
        action_text="Jun held the moon plate steady while Mira tipped the cracked jar empty, dried the rail with an attic towel, and looped fresh string around the hook.",
        result_text="The muddy drip was gone, and the top step felt dry and trustworthy again.",
        tags=frozenset({"repair", "drying", "trunk"}),
    ),
    "return_chick": Repair(
        key="return_chick",
        need="return_chick",
        action_text="Mira cupped the shivering swallow chick in her apron while Jun rebuilt the soft nest edge and brushed the muddy fluff from the ladder.",
        result_text="The ladder turned neat again, and the silver spinner stopped trembling once the chick was safe above the eaves.",
        tags=frozenset({"repair", "bird", "gentleness"}),
    ),
}


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or storage space tucked high under a roof. People and animals often reach it by a ladder or narrow stairs.",
        )
    ],
    "ladder": [
        (
            "Why does a ladder need clean rungs?",
            "Clean rungs help feet or paws grip the wood. Mud can turn a quick climb into a dangerous slip.",
        )
    ],
    "moon": [
        (
            "Why might a fable end under a twinkling moon?",
            "A twinkling moon makes the ending feel calm and watchful. It can also show that the trouble in the story has been settled.",
        )
    ],
    "mud": [
        (
            "Why can muddy traces mislead someone?",
            "Mud shows that something wet passed by, but it does not always show who caused the trouble. A careful look is needed before blame becomes fair.",
        )
    ],
    "flashback": [
        (
            "What does a flashback add to a story?",
            "A flashback brings an older moment into the present story. That memory can change how a character judges what is happening now.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is the making of peace after hurt or anger. It usually needs truth, apology, and a willing heart on both sides.",
        )
    ],
    "toadlet": [
        (
            "Why might a small toad leave mud behind?",
            "A toadlet has damp skin and lives close to wet ground. If it climbs onto wood, it can leave dark little marks behind.",
        )
    ],
    "jar": [
        (
            "Why can a cracked jar make a muddy mess?",
            "A cracked jar can collect dirty rainwater and leak it where it does not belong. If it tips, the spill spreads farther than anyone expects.",
        )
    ],
    "bird": [
        (
            "Why would a young bird need gentle help?",
            "A young bird can panic when it falls from a nest. Calm hands can return it safely before cold or fear makes things worse.",
        )
    ],
    "kindness": [
        (
            "How can kindness help an argument end well?",
            "Kindness slows the tongue long enough for the truth to appear. Once people feel heard, they can repair both the problem and the friendship.",
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
    "toadlet",
    "jar",
    "bird",
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
            f"{clue.key} points to {clue.family} evidence, but {cause.key} belongs to {cause.family} trouble."
        )
    if not repair_fits_cause(cause, repair):
        reasons.append(f"{repair.key} does not solve the need created by {cause.key}.")
    if not place_supports_cause(place, cause):
        reasons.append(
            f"{place.key} does not contain the physical setup needed for {cause.key}."
        )
    if not reasons:
        reasons.append("The requested choices do not make one grounded attic-ladder fable.")
    reasons.append(
        f"Memory {memory.key} can vary freely, but the clue, cause, repair, and place still need to describe one believable mess and one believable fix."
    )
    return "Invalid story choices: " + " ".join(reasons)


def _r_flashback_cools_blame(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["blame"] < THRESHOLD or hero.memes["flashback"] < THRESHOLD:
        return False
    sig = ("flashback_cools_blame", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = max(0.0, hero.memes["blame"] - 0.5)
    hero.memes["reflection"] += 1.0
    hero.memes["trust"] += 0.5
    friend.memes["hope"] += 0.5
    world.log("flashback_cools_blame", hero=hero.id, friend=friend.id)
    return True


def _r_truth_softens_hurt(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    if ladder.meters["true_cause_found"] < THRESHOLD:
        return False
    sig = ("truth_softens_hurt", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = 0.0
    hero.memes["understanding"] += 1.0
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 0.5)
    world.facts["truth_seen"] = True
    world.log("truth_softens_hurt", hero=hero.id, friend=friend.id)
    return True


def _r_reconciliation_lands(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    moon = world.get("moon")
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return False
    if ladder.meters["clean"] < THRESHOLD or ladder.meters["safe"] < THRESHOLD:
        return False
    sig = ("reconciliation_lands", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    moon.meters["twinkling_seen"] += 1.0
    world.facts["reconciled"] = True
    world.facts["happy_ending"] = True
    world.log("reconciliation_lands", hero=hero.id, friend=friend.id)
    return True


CAUSAL_RULES = [
    _r_flashback_cools_blame,
    _r_truth_softens_hurt,
    _r_reconciliation_lands,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity) -> None:
    moon = world.get("moon")
    moon.meters["visible"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"In {world.place.cottage_name}, Mira the mouse and Jun the rabbit loved to climb {world.place.ladder_label} when evening turned soft."
    )
    world.say(
        f"At {world.place.loft_label}, {world.place.moon_object} waited beneath {world.place.window_label}, where the twinkling moon peeped in like a silver eye."
    )
    world.say(
        'Grandmother Wren, who nested above the beams, often told them, "A muddy clue may speak first, but a true heart should answer last."'
    )
    world.log("introduce", hero=hero.id, friend=friend.id, elder=elder.id, place=world.place.key)


def muddy_discovery(world: World, clue: MudClue) -> None:
    ladder = world.get("ladder")
    moon_object = world.get("moon_object")
    ladder.meters["muddy"] += 1.0
    ladder.meters["safe"] = 0.0
    moon_object.meters["crooked"] += 1.0
    world.say(
        f"After the rain, Mira found {clue.clue_text}. The attic ladder looked muddy almost to the top."
    )
    world.say(
        f"Worse, {world.place.moon_object} hung crooked, as if something wet and hasty had brushed past it."
    )
    world.facts["mess_seen"] = True
    world.log("muddy_discovery", clue=clue.key)


def accuse(world: World, clue: MudClue, hero: Entity, friend: Entity) -> None:
    hero.memes["blame"] += 1.0
    friend.memes["hurt"] += 1.0
    world.say(
        f'Mira remembered that {clue.suspect_reason}. She turned to Jun and said, "Jun, {clue.accusation}."'
    )
    world.say(
        '"I was near it earlier," Jun answered, "but I did not bend our moon treasure."'
    )
    world.log("accuse", hero=hero.id, friend=friend.id, clue=clue.key)


def flashback(world: World, memory: Memory) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1.0
    world.say(f"Then a flashback opened in Mira's mind: {memory.flashback}")
    world.say(f"The memory cooled her first hot thought. {memory.lesson}")
    world.facts["flashback_text"] = memory.flashback
    world.facts["flashback_lesson"] = memory.lesson
    world.log("flashback", memory=memory.key)
    propagate(world)


def investigate(world: World, cause: Cause) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    hero.memes["curiosity"] += 1.0
    friend.memes["steadiness"] += 1.0
    ladder.meters["true_cause_found"] += 1.0
    world.say(
        f"So Mira climbed more slowly and looked again. At the top, she and Jun discovered {cause.discovery}."
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
    world.log("repair", repair=repair.key)


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1.0
    friend.memes["forgiveness"] += 1.0
    world.say(
        '"Jun," Mira said, resting one paw on the clean rung, "I am sorry I blamed you before I looked with care."'
    )
    world.say(
        f'"My feelings were sore," Jun said, touching the straightened {world.place.moon_name}, "but truth mends more quickly when friends speak it kindly."'
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
        f"Mira and Jun sat shoulder to shoulder in {world.place.loft_label}. {cause.closing_line}"
    )
    world.say(
        "From that evening on, Mira remembered the attic lesson: muddy signs may begin a quarrel, but careful truth can end one with peace."
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
        Entity("Mira", kind="character", type="girl", label="Mira", role="hero", traits=["quick"])
    )
    friend = world.add(
        Entity("Jun", kind="character", type="boy", label="Jun", role="friend", traits=["steady"])
    )
    elder = world.add(
        Entity("Grandmother Wren", kind="character", type="mother", label="Grandmother Wren", role="elder", traits=["wise"])
    )
    world.add(Entity("ladder", kind="thing", type="ladder", label=place.ladder_label))
    world.add(Entity("moon_object", kind="thing", type="moon_object", label=place.moon_object))
    world.add(Entity("moon", kind="thing", type="moon", label="twinkling moon"))

    introduce(world, hero, friend, elder)
    world.para()
    muddy_discovery(world, clue)
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
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    return [
        'Write a gentle fable for children that includes the words "muddy" and "twinkling moon" and takes place on an attic ladder.',
        f"Tell a reconciliation story in which Mira blames Jun after finding {clue.clue_text}, but a flashback makes her look again with patience.",
        f"Write a happy-ending attic tale where the moon keepsake is disturbed because {cause.cause_text}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    repair: Repair = world.facts["repair"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where does the story take place?",
            f"The story takes place in {world.place.cottage_name}, around {world.place.ladder_label} and {world.place.window_label}. That high attic space matters because Mira and Jun climb there to visit their moon treasure together.",
        ),
        QAItem(
            "Why did Mira blame Jun at first?",
            f"Mira saw {clue.clue_text} and remembered that {clue.suspect_reason}. The clue seemed to point at Jun, so she spoke before she had checked the whole loft.",
        ),
        QAItem(
            "What did the flashback change for Mira?",
            f"The flashback reminded Mira of this earlier kindness: {world.facts['flashback_text']} That memory made her slow her anger and treat Jun as a friend worth hearing.",
        ),
        QAItem(
            "What was the real cause of the muddy mess?",
            f"The real cause was that {cause.cause_text}. Once Mira and Jun searched carefully, the physical signs matched that cause better than Mira's first guess.",
        ),
        QAItem(
            "How did the friends solve the problem?",
            f"{repair.action_text} That repair fixed the true source of the mess, so the ladder became safe again and the {world.place.moon_name} could stay straight.",
        ),
        QAItem(
            "How do we know the ending is happy?",
            f"Mira apologized, Jun forgave her, and they sat together under the twinkling moon. The clean attic ladder and the steady moon treasure showed that both the mess and the quarrel were truly over.",
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

    if not clue_matches_cause(clue, cause) or not repair_fits_cause(cause, repair) or not place_supports_cause(place, cause):
        raise StoryError(
            explain_rejection(params.place, params.clue, params.memory, params.cause, params.repair)
        )

    world = tell(place, clue, memory, cause, repair)
    if not world.facts.get("happy_ending"):
        raise StoryError("World did not produce the required happy ending.")

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_questions(world),
        world_qa=world_knowledge_questions(world),
        world=world,
    )


ASP_RULES = r"""
place(P) :- attic_place(P).
clue(C) :- mud_clue(C).
memory(M) :- flashback_memory(M).
cause(K) :- true_cause(K).
repair(R) :- repair_action(R).

valid(P,C,M,K,R) :-
    place(P), clue(C), memory(M), cause(K), repair(R),
    clue_family(C,F),
    cause_family(K,F),
    cause_need(K,N),
    repair_need(R,N),
    cause_tag(K,T),
    place_tag(P,T).

#show valid/5.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for place in PLACES.values():
        rows.append(asp.fact("attic_place", place.key))
        for tag in sorted(place.tags):
            rows.append(asp.fact("place_tag", place.key, tag))
    for clue in CLUES.values():
        rows.append(asp.fact("mud_clue", clue.key))
        rows.append(asp.fact("clue_family", clue.key, clue.family))
    for memory in MEMORIES.values():
        rows.append(asp.fact("flashback_memory", memory.key))
    for cause in CAUSES.values():
        rows.append(asp.fact("true_cause", cause.key))
        rows.append(asp.fact("cause_family", cause.key, cause.family))
        rows.append(asp.fact("cause_need", cause.key, cause.need))
        rows.append(asp.fact("cause_tag", cause.key, cause.required_tag))
    for repair in REPAIRS.values():
        rows.append(asp.fact("repair_action", repair.key))
        rows.append(asp.fact("repair_need", repair.key, repair.need))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(tuple(str(x) for x in atom) for atom in asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("Python/ASP mismatch")
        print("Only Python:", sorted(python_set - asp_set))
        print("Only ASP:", sorted(asp_set - python_set))
        return 1

    for index, combo in enumerate(sorted(python_set), start=1):
        sample = generate(StoryParams(*combo, seed=index))
        story = sample.story
        if "muddy" not in story or "twinkling moon" not in story:
            print("Generated story missed required seed words for combo:", combo)
            return 1
        if "attic ladder" not in story:
            print("Generated story missed attic ladder setting for combo:", combo)
            return 1
        if "flashback" not in story.lower():
            print("Generated story missed the flashback instrument for combo:", combo)
            return 1
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            print("Generated story missed required prompt or QA output for combo:", combo)
            return 1
        if not sample.world or not sample.world.facts.get("happy_ending"):
            print("Generated story failed to reach a happy ending for combo:", combo)
            return 1
        if "{" in story or "}" in story:
            print("Generated story leaked template scaffolding for combo:", combo)
            return 1
    print(
        f"OK: Python and ASP agree on {len(python_set)} valid attic-ladder fables, and all generated stories pass basic checks."
    )
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
            generate(StoryParams(*combo, seed=base_seed + index))
            for index, combo in enumerate(valid_combos(), start=1)
        ]

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    offset = 0
    while len(samples) < target and attempts < target * 30:
        local_args = copy.copy(args)
        local_args.seed = base_seed + offset
        attempts += 1
        offset += 1
        params = resolve_params(local_args, random.Random(local_args.seed), index=offset)
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for index, sample in enumerate(samples, start=1):
        header = ""
        if args.all:
            params = sample.params
            header = (
                f"=== place={params.place} clue={params.clue} memory={params.memory} "
                f"cause={params.cause} repair={params.repair} seed={params.seed} ==="
            )
        elif len(samples) > 1:
            header = (
                "=== muddy_twinkling_moon_attic_ladder_reconciliation_flashback_3 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
