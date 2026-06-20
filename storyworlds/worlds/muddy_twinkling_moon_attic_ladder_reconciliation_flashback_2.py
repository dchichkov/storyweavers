#!/usr/bin/env python3
"""
Standalone storyworld for a TinyStories-style seed:

    Words: muddy, twinkling moon
    Setting: attic ladder
    Features: Reconciliation, Flashback, Happy Ending
    Style: Fable

Internal source tale:
    Two small friends climb an attic ladder each evening to look at the moon
    through a little attic window and turn their moon wheel. After rain, muddy
    marks appear on the rungs and the wheel is knocked crooked. The quick
    squirrel blames the hedgehog too fast, then remembers an earlier kindness.
    That flashback slows the blame long enough for both friends to look again,
    discover the true physical cause, repair the mess together, and reconcile
    under the twinkling moon.
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
    house_name: str
    ladder_label: str
    loft_label: str
    window_label: str
    moon_keepsake: str
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
    cause_text: str
    discovery: str
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "hen"}:
            forms = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "father", "man"}:
            forms = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            forms = {"subject": "they", "object": "them", "possessive": "their"}
        return forms[case]


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

    def clone(self) -> World:
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
    "pumpkin_window": AtticPlace(
        key="pumpkin_window",
        house_name="the chestnut cottage",
        ladder_label="the narrow attic ladder",
        loft_label="the pumpkin loft",
        window_label="the round attic window",
        moon_keepsake="their painted moon wheel beside a string of dried pumpkin flowers",
        ending_image="the clean ladder glowing like warm straw",
        tags=frozenset({"garden_edge", "eaves"}),
    ),
    "grain_loft": AtticPlace(
        key="grain_loft",
        house_name="the miller's little loft house",
        ladder_label="the wooden attic ladder",
        loft_label="the grain loft",
        window_label="the square moon pane",
        moon_keepsake="their brass moon wheel hanging above a grain chest",
        ending_image="the last muddy shine gone from the side rails",
        tags=frozenset({"garden_edge", "yard_trunk"}),
    ),
    "beam_nook": AtticPlace(
        key="beam_nook",
        house_name="the hazel-roof burrow",
        ladder_label="the steep attic ladder",
        loft_label="the beam nook under the rafters",
        window_label="the tiny attic moon window",
        moon_keepsake="their silver moon wheel tied near a box of thread spools",
        ending_image="the moon wheel resting still above the swept top step",
        tags=frozenset({"yard_trunk", "eaves"}),
    ),
}


CLUES: dict[str, MudClue] = {
    "pumpkin_tendril": MudClue(
        key="pumpkin_tendril",
        family="garden",
        clue_text="a muddy pumpkin tendril stuck across the third rung",
        suspect_reason="Rowan had spent the afternoon tying pumpkin vines in the garden",
        accusation="you were the one in the muddy pumpkin patch, so this must be your doing",
        tags=frozenset({"mud", "garden", "vine"}),
    ),
    "yard_pebble": MudClue(
        key="yard_pebble",
        family="yard",
        clue_text="a muddy yard pebble pressed into the top step",
        suspect_reason="Rowan had carried pebbles from the yard to line a flower pot",
        accusation="you were the one carrying yard pebbles, so you must have knocked everything crooked",
        tags=frozenset({"mud", "yard", "pebble"}),
    ),
    "nest_straw": MudClue(
        key="nest_straw",
        family="roof",
        clue_text="a muddy strand of nest straw pasted along the side rail",
        suspect_reason="Rowan had helped gather roof straw after the rain",
        accusation="you were the one near the roof straw, so these muddy marks must be yours",
        tags=frozenset({"mud", "roof", "straw"}),
    ),
}


MEMORIES: dict[str, Memory] = {
    "steady_shoulder": Memory(
        key="steady_shoulder",
        flashback="Last frost, when a rung creaked under Hazel's foot, Rowan had braced the ladder with his small strong shoulders until she climbed down safely.",
        lesson="A friend who steadies you in danger deserves a careful hearing in calmer moments.",
        tags=frozenset({"flashback", "ladder", "trust"}),
    ),
    "shared_fig": Memory(
        key="shared_fig",
        flashback="On the first cold moon of autumn, Rowan had broken his sweetest fig in half and pushed the larger piece into Hazel's paws without being asked.",
        lesson="Kindness remembered can loosen the knot in a hurried heart.",
        tags=frozenset({"flashback", "kindness", "sharing"}),
    ),
    "storm_lantern": Memory(
        key="storm_lantern",
        flashback="During a dark storm, Rowan had climbed the attic ladder with a lantern so Hazel would not have to wait alone in the rattling loft.",
        lesson="Old courage can light the way when new suspicion makes everything dim.",
        tags=frozenset({"flashback", "courage", "moon"}),
    ),
}


CAUSES: dict[str, Cause] = {
    "snail_guest": Cause(
        key="snail_guest",
        family="garden",
        need="return_snail",
        required_tag="garden_edge",
        cause_text="a rain-soaked snail had ridden in on a pumpkin vine through the attic window, nudged the moon wheel with its shell, and left a muddy ribbon on the rungs",
        discovery="a little snail glistening on the window ledge beside the tilted moon wheel",
        fix_result="Once the snail was back among the wet leaves outside, nothing else kept pushing the moon wheel askew.",
        closing_line="The loft smelled sweet and earthy instead of cross and wet.",
        tags=frozenset({"snail", "garden", "guest"}),
    ),
    "boot_spill": Cause(
        key="boot_spill",
        family="yard",
        need="dry_boot",
        required_tag="yard_trunk",
        cause_text="an old yard boot full of rainwater had tipped beside a low storage box and spilled a muddy stream down the ladder rail into the moon wheel stand",
        discovery="the old yard boot lying on its side while brown drops slid from a low storage box toward the top step",
        fix_result="When the boot was emptied and set outside, the loft stopped dripping and the moon wheel could hang straight again.",
        closing_line="The air turned dry and still, as if the loft itself had stopped fretting.",
        tags=frozenset({"boot", "yard", "water"}),
    ),
    "nestling_flurry": Cause(
        key="nestling_flurry",
        family="roof",
        need="return_nestling",
        required_tag="eaves",
        cause_text="a wet nestling had fluttered in from the eaves, knocked the moon wheel sideways, and stamped muddy little marks while searching for a perch",
        discovery="a trembling nestling peeping behind a storage box while loose straw clung to the top rung",
        fix_result="After the nestling was back in its snug roof nest, no frightened wings were left to bump the moon wheel again.",
        closing_line="Only one safe chirp floated down from the rafters, and it sounded like thanks.",
        tags=frozenset({"bird", "roof", "nestling"}),
    ),
}


REPAIRS: dict[str, Repair] = {
    "return_snail": Repair(
        key="return_snail",
        need="return_snail",
        action_text="Rowan lifted the snail on a cabbage leaf while Hazel wiped each muddy rung with a dry cloth, and together they carried their tiny guest back to the wet garden bed.",
        result_text="The rungs turned safe again, and the moon wheel stopped wobbling once the shell was gone from the ledge.",
        tags=frozenset({"repair", "garden", "kindness"}),
    ),
    "dry_boot": Repair(
        key="dry_boot",
        need="dry_boot",
        action_text="Hazel and Rowan poured the rainwater from the old boot, dried the rail with an attic towel, and tied the moon wheel straight with fresh thread.",
        result_text="The muddy track disappeared, and the top step felt firm under their paws again.",
        tags=frozenset({"repair", "yard", "drying"}),
    ),
    "return_nestling": Repair(
        key="return_nestling",
        need="return_nestling",
        action_text="Hazel cupped the shivering nestling against her scarf while Rowan rebuilt the soft eaves nest and brushed the muddy straw from the ladder.",
        result_text="The moon wheel hung still again, and the loft no longer fluttered with frightened motion.",
        tags=frozenset({"repair", "roof", "care"}),
    ),
}


KNOWLEDGE: dict[str, list[tuple[str, str]]] = {
    "attic": [
        (
            "What is an attic?",
            "An attic is a room or storage space high under a roof. It is often reached by a ladder or narrow stairs.",
        )
    ],
    "ladder": [
        (
            "Why should an attic ladder stay clean?",
            "A clean ladder is easier to climb safely because feet or paws can grip the rungs. Mud can turn one hurried step into a slip.",
        )
    ],
    "moon": [
        (
            "Why might a story mention a twinkling moon?",
            "A twinkling moon makes the scene feel gentle and watchful. In a fable, it can also show that peace has returned.",
        )
    ],
    "mud": [
        (
            "Why can muddy marks be a poor clue by themselves?",
            "Mud can tell you where something came from, but not always who caused the trouble. Different creatures and objects can carry the same mud.",
        )
    ],
    "flashback": [
        (
            "What does a flashback do in a story?",
            "A flashback brings back a memory from earlier. That memory can change how a character understands the problem in front of them.",
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation is when hurt people make peace again. They tell the truth, listen well, and choose friendship over anger.",
        )
    ],
    "snail": [
        (
            "Why might a snail leave a muddy trail?",
            "A snail moves slowly with a soft wet body that picks up dirt. If it crosses a clean board, it can leave both dampness and mud behind.",
        )
    ],
    "boot": [
        (
            "Why would an old boot full of rainwater make a mess?",
            "Rainwater sitting in a boot can mix with yard dirt and become muddy. If the boot tips over, the water can spread that mud across wood or cloth.",
        )
    ],
    "bird": [
        (
            "Why might a nestling need help after rain?",
            "A young bird can become cold and confused in wet weather. Gentle hands can return it to a safe nest before it grows weaker.",
        )
    ],
    "kindness": [
        (
            "How can kindness help solve an argument?",
            "Kindness slows the urge to strike with words. Once tempers soften, people can look more carefully at what really happened.",
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
    "snail",
    "boot",
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
            f"{clue.key} points to {clue.family} mud, but {cause.key} comes from {cause.family} trouble."
        )
    if not repair_fits_cause(cause, repair):
        reasons.append(f"{repair.key} does not solve the need created by {cause.key}.")
    if not place_supports_cause(place, cause):
        reasons.append(
            f"{place.key} does not support {cause.key}; the attic place lacks the physical setup needed for that cause."
        )
    if not reasons:
        reasons.append("The requested choices do not form one coherent attic-ladder fable.")
    reasons.append(
        f"Memory {memory.key} is allowed, but the clue, cause, and repair must still describe one grounded mess and one grounded fix."
    )
    return "Invalid story choices: " + " ".join(reasons)


def _r_flashback_softens_blame(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["blame"] < THRESHOLD or hero.memes["flashback"] < THRESHOLD:
        return False
    sig = ("flashback_softens", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = max(0.0, hero.memes["blame"] - 0.5)
    hero.memes["reflection"] += 1.0
    hero.memes["trust"] += 0.5
    friend.memes["hope"] += 0.5
    world.log("flashback_softens_blame", hero=hero.id, friend=friend.id)
    return True


def _r_truth_clears_accusation(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    if ladder.meters["true_cause_found"] < THRESHOLD:
        return False
    sig = ("truth_clears", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["blame"] = 0.0
    hero.memes["understanding"] += 1.0
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 0.5)
    world.facts["truth_seen"] = True
    world.log("truth_clears_accusation", hero=hero.id, friend=friend.id)
    return True


def _r_reconciliation_completes(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    ladder = world.get("ladder")
    moon = world.get("moon")
    if hero.memes["apology"] < THRESHOLD or friend.memes["forgiveness"] < THRESHOLD:
        return False
    if ladder.meters["clean"] < THRESHOLD or ladder.meters["safe"] < THRESHOLD:
        return False
    sig = ("reconciled", hero.id, friend.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    moon.meters["twinkling_seen"] += 1.0
    world.facts["reconciled"] = True
    world.facts["happy_ending"] = True
    world.log("reconciliation_completes", hero=hero.id, friend=friend.id)
    return True


CAUSAL_RULES = [
    _r_flashback_softens_blame,
    _r_truth_clears_accusation,
    _r_reconciliation_completes,
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity) -> None:
    place = world.place
    moon = world.get("moon")
    moon.meters["visible"] += 1.0
    hero.memes["friendship"] += 1.0
    friend.memes["friendship"] += 1.0
    world.say(
        f"In {place.house_name}, Hazel the squirrel and Rowan the hedgehog loved to climb {place.ladder_label} at evening."
    )
    world.say(
        f"At {place.loft_label}, {place.moon_keepsake} waited beneath {place.window_label}, where the twinkling moon looked in like a patient silver lantern."
    )
    world.say(
        f'Old Finch, who lived under the rafters, often told them, "A ladder may forgive quick feet, but a friend is slower to forgive quick blame."'
    )
    world.log("introduce", hero=hero.id, friend=friend.id, elder=elder.id, place=place.key)


def muddy_discovery(world: World, clue: MudClue) -> None:
    ladder = world.get("ladder")
    wheel = world.get("moon_wheel")
    ladder.meters["muddy"] += 1.0
    ladder.meters["safe"] = 0.0
    wheel.meters["crooked"] += 1.0
    world.say(
        f"After a wet afternoon, Hazel found {clue.clue_text}. The attic ladder looked muddy almost to the very top."
    )
    world.say(
        f"Worse, {world.place.moon_keepsake} hung crooked, as if something hurried and small had brushed past it."
    )
    world.facts["mess_seen"] = True
    world.log("muddy_discovery", clue=clue.key)


def accuse(world: World, clue: MudClue, hero: Entity, friend: Entity) -> None:
    hero.memes["blame"] += 1.0
    friend.memes["hurt"] += 1.0
    world.say(
        f'Hazel remembered that {clue.suspect_reason}. She turned to Rowan and said, "Rowan, {clue.accusation}."'
    )
    world.say(
        'Rowan lowered his prickly little shoulders. "I was muddy earlier," he said, "but I did not touch our moon wheel."'
    )
    world.log("accusation", hero=hero.id, friend=friend.id, clue=clue.key)


def flashback(world: World, memory: Memory) -> None:
    hero = world.get("hero")
    hero.memes["flashback"] += 1.0
    world.say(f"Then a flashback opened in Hazel's mind: {memory.flashback}")
    world.say(f"The memory tugged on her temper. {memory.lesson}")
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
        f"So Hazel climbed more slowly and looked again. At the top, she and Rowan discovered {cause.discovery}."
    )
    world.say(
        f"The true trouble was plain and physical: {cause.cause_text}."
    )
    world.facts["true_cause"] = cause.cause_text
    world.facts["discovery"] = cause.discovery
    world.log("investigation", cause=cause.key)
    propagate(world)


def repair_scene(world: World, repair: Repair, cause: Cause) -> None:
    ladder = world.get("ladder")
    wheel = world.get("moon_wheel")
    ladder.meters["clean"] += 1.0
    ladder.meters["safe"] += 1.0
    wheel.meters["steady"] += 1.0
    wheel.meters["crooked"] = 0.0
    world.say(repair.action_text)
    world.say(f"{repair.result_text} {cause.fix_result}")
    world.facts["repair_action"] = repair.action_text
    world.facts["repair_result"] = repair.result_text
    world.log("repair", repair=repair.key)


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["apology"] += 1.0
    friend.memes["forgiveness"] += 1.0
    world.say(
        'Hazel placed one paw on the clean rung and said, "I am sorry I blamed you before I looked properly."'
    )
    world.say(
        'Rowan touched the straightened moon wheel and answered, "My feelings were hurt, but the truth feels better than holding anger."'
    )
    world.log("reconcile", hero=hero.id, friend=friend.id)
    propagate(world)


def closing(world: World, cause: Cause) -> None:
    if not world.facts.get("happy_ending"):
        raise StoryError("Story did not reach the required happy ending.")
    world.say(
        f"When they looked up again, the twinkling moon poured over {world.place.ending_image}."
    )
    world.say(
        f"Hazel and Rowan sat side by side in {world.place.loft_label}. {cause.closing_line}"
    )
    world.say(
        "From then on, Hazel remembered that a muddy sign may start a story, but only patience can finish it truthfully."
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
        Entity("Hazel", kind="character", type="girl", label="Hazel", role="hero", traits=["quick"])
    )
    friend = world.add(
        Entity("Rowan", kind="character", type="boy", label="Rowan", role="friend", traits=["steady"])
    )
    elder = world.add(
        Entity("Old Finch", kind="character", type="man", label="Old Finch", role="elder", traits=["wise"])
    )
    world.add(Entity("ladder", kind="thing", type="ladder", label=place.ladder_label))
    world.add(Entity("moon_wheel", kind="thing", type="moon_wheel", label=place.moon_keepsake))
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
        f"Tell a reconciliation story in which Hazel blames Rowan after finding {clue.clue_text}, but a flashback helps her slow down and look again.",
        f"Write a happy-ending attic story where the moon keepsake is disturbed because {cause.cause_text}.",
    ]


def story_questions(world: World) -> list[QAItem]:
    clue: MudClue = world.facts["clue"]  # type: ignore[assignment]
    cause: Cause = world.facts["cause"]  # type: ignore[assignment]
    repair: Repair = world.facts["repair"]  # type: ignore[assignment]
    return [
        QAItem(
            "Where does the story take place?",
            f"The story takes place in {world.place.house_name}, around {world.place.ladder_label} and {world.place.window_label}. That high little space matters because Hazel and Rowan climb there to watch the moon together.",
        ),
        QAItem(
            "Why did Hazel blame Rowan at first?",
            f"Hazel saw {clue.clue_text} and remembered that {clue.suspect_reason}. The clue seemed to point at Rowan, so she spoke before she had checked the whole scene.",
        ),
        QAItem(
            "What did the flashback remind Hazel of?",
            f"The flashback reminded Hazel of this earlier moment: {world.facts['flashback_text']} That memory showed her Rowan had already been kind and dependable in an earlier hard moment.",
        ),
        QAItem(
            "What was the real cause of the muddy mess?",
            f"The real cause was that {cause.cause_text}. Once Hazel looked carefully, the physical signs fit that cause better than her first accusation did.",
        ),
        QAItem(
            "How did the friends fix the problem?",
            f"{repair.action_text} That repair solved the true problem, so the ladder became safe again and the moon wheel could stay straight.",
        ),
        QAItem(
            "How do we know the ending is happy?",
            f"Hazel apologized, Rowan forgave her, and they sat together under the twinkling moon. The clean attic ladder and the steady moon wheel showed that both the mess and the quarrel were over.",
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
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            print("Generated story missed required QA or prompt output for combo:", combo)
            return 1
        if not sample.world or not sample.world.facts.get("happy_ending"):
            print("Generated story failed to reach happy ending for combo:", combo)
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
                "=== muddy_twinkling_moon_attic_ladder_reconciliation_flashback_2 "
                f"#{index} seed={sample.params.seed} ==="
            )
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
