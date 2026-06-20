#!/usr/bin/env python3
"""
storyworlds/worlds/rusty_sign_attic_ladder_twist_moral_value_2.py
==================================================================

A standalone storyworld for a child-facing space adventure on an attic ladder.

Internal source tale:
    A young space cadet hears a rumor that treasure is hidden above a repair
    bay. On the attic ladder the cadet finds a rusty sign that seems to point
    toward glory. The middle turn comes when a tempting shortcut would make the
    climb unsafe. The cadet chooses careful teamwork instead, and the twist is
    that the "treasure" is really useful rescue equipment or repair gear that
    helps everyone below. The moral value is that honest, helpful choices shine
    brighter than greedy ones.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass(frozen=True)
class AtticState:
    key: str
    name: str
    ladder: str
    attic_image: str
    below_sound: str
    final_image: str
    supports: tuple[str, ...]
    risk: str


@dataclass(frozen=True)
class SignState:
    key: str
    object_label: str
    mark: str
    message: str
    study: str
    signal: str
    apparent_treasure: str


@dataclass(frozen=True)
class TemptationState:
    key: str
    label: str
    bad_move: str
    danger: str
    refusal: str
    value_line: str
    lure: float
    kind: str


@dataclass(frozen=True)
class TwistState:
    key: str
    apparent: str
    truth: str
    reveal: str
    payoff: str
    moral: str
    outcome: str
    ending_image: str


@dataclass
class StoryParams:
    attic: str
    sign: str
    temptation: str
    twist: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    captain: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "uncle", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def reflexive(self) -> str:
        if self.kind in {"girl", "mother", "aunt", "grandmother"}:
            return "herself"
        if self.kind in {"boy", "father", "uncle", "grandfather"}:
            return "himself"
        return "themself"


@dataclass
class Event:
    key: str
    details: dict[str, str]


@dataclass
class World:
    params: StoryParams
    attic: AtticState
    sign: SignState
    temptation: TemptationState
    twist: TwistState
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    fired: set[str] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def event(self, key: str, **details: str) -> None:
        self.history.append(Event(key=key, details=details))

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            "params: "
            + json.dumps(asdict(self.params), ensure_ascii=False, sort_keys=True)
        )
        rows.append(
            f"attic: {self.attic.key} | sign: {self.sign.key} | "
            f"temptation: {self.temptation.key} | twist: {self.twist.key}"
        )
        for entity in self.entities.values():
            rows.append(
                f"entity {entity.id:<10} kind={entity.kind:<12} "
                f"location={entity.location:<18} owner={entity.owner or '-':<10} "
                f"traits={entity.traits} meters={dict(entity.meters)} "
                f"memes={dict(entity.memes)}"
            )
        rows.append("history:")
        for idx, event in enumerate(self.history, start=1):
            rows.append(f"  {idx:02d}. {event.key} {json.dumps(event.details, sort_keys=True)}")
        rows.append("facts:")
        for key in sorted(self.facts):
            rows.append(f"  {key}: {self.facts[key]}")
        return "\n".join(rows)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: callable


ATTICS = {
    "launch_loft": AtticState(
        key="launch_loft",
        name="the launch loft above Dock Seven",
        ladder="the blue-rung attic ladder above Dock Seven",
        attic_image="silver ducts curved through the rafters like sleeping comets",
        below_sound="repair carts hummed below like tiny moons rolling over tin",
        final_image="the attic hatch glowed softly over the ladder rails",
        supports=("arrow", "light"),
        risk="the middle rung gave a thin squeak whenever someone leaned too far",
    ),
    "moon_map_nook": AtticState(
        key="moon_map_nook",
        name="the moon-map nook over the tool room",
        ladder="the narrow attic ladder beside the moon-map closet",
        attic_image="folded star maps and old helmets hung in stripes of dusty light",
        below_sound="a practice rocket fan purred under the floorboards",
        final_image="fresh map clips shone beside the safe ladder hatch",
        supports=("light", "magnet"),
        risk="the top rungs vanished into shadow unless someone held a lamp below",
    ),
    "comet_storage": AtticState(
        key="comet_storage",
        name="the comet-storage attic above the repair bay",
        ladder="the copper-rail attic ladder above the repair bay",
        attic_image="hooks of spare fins and signal cords swayed over a row of crates",
        below_sound="the beacon stand clicked patiently on the floor below",
        final_image="the beacon stand blinked with clean green light under the attic lip",
        supports=("arrow", "magnet"),
        risk="one side rail twitched if a climber tried to reach sideways in a hurry",
    ),
}


SIGNS = {
    "arrow_plate": SignState(
        key="arrow_plate",
        object_label="a bent rusty sign bolted to a beam",
        mark="a faded rocket arrow scratched through old red paint",
        message="Follow the true nose, not the brightest glitter.",
        study="the arrow only made sense when it lined up with a beam and the edge of one careful rung",
        signal="arrow",
        apparent_treasure="the captain's star chest",
    ),
    "star_hole_sign": SignState(
        key="star_hole_sign",
        object_label="a rusty sign punched with tiny star holes",
        mark="five bright pinpricks around a smoky ring",
        message="When starlight lands, the right box answers.",
        study="the little holes let a skylight sprinkle dots onto one plain crate and nowhere else",
        signal="light",
        apparent_treasure="a moon-gold meteor prize",
    ),
    "magnet_ring_sign": SignState(
        key="magnet_ring_sign",
        object_label="a crooked rusty sign with a dangling iron ring",
        mark="a ring that tugged toward the attic wall whenever it stopped swinging",
        message="Trust the pull that tells the truth.",
        study="the iron ring kept leaning toward one hidden latch instead of toward the shiny boxes in open view",
        signal="magnet",
        apparent_treasure="a secret comet medal",
    ),
}


TEMPTATIONS = {
    "rush_grab": TemptationState(
        key="rush_grab",
        label="lunging for the shiniest crate",
        bad_move="stretching early for the brightest crate instead of following the clue",
        danger="the ladder would kick sideways and a crate could tumble onto the floor below",
        refusal="The shiny thing could wait, because safe hands had to come first.",
        value_line="Careful feet reach farther than greedy hands.",
        lure=2.0,
        kind="rush",
    ),
    "keep_secret": TemptationState(
        key="keep_secret",
        label="keeping the clue to yourself",
        bad_move="hiding the clue so nobody else could share the prize",
        danger="the helper would not know where to steady the ladder, and the climb would become lonely and risky",
        refusal="A clue grows stronger when a trusted friend can help protect it.",
        value_line="Sharing the truth makes brave work safer.",
        lure=2.0,
        kind="hide",
    ),
    "show_off": TemptationState(
        key="show_off",
        label="showing off with one hand",
        bad_move="waving to the deck below and climbing one-handed to look daring",
        danger="the climber would miss the true clue and make the ladder sway for no good reason",
        refusal="Looking impressive mattered less than getting everyone home safely.",
        value_line="Real skill is quiet and steady.",
        lure=2.0,
        kind="boast",
    ),
}


TWISTS = {
    "beacon_battery": TwistState(
        key="arrow",
        apparent="the captain's star chest",
        truth="a rescue beacon battery wrapped in silver cloth",
        reveal="Behind the beam sat a plain case, and inside it rested the spare rescue beacon battery that the landing lights needed.",
        payoff="The spare battery snapped into the beacon stand, and the rooftop landing lights blinked awake one by one.",
        moral="The best treasure is the thing that helps everyone find a safe way home.",
        outcome="landing_lights_restored",
        ending_image="The beacon winked over the roof while the old sign rested honestly above the ladder.",
    ),
    "patch_kit": TwistState(
        key="light",
        apparent="a moon-gold meteor prize",
        truth="a hull-patch kit for the little training shuttle",
        reveal="The plain crate held soft seal patches and bright tape for the training shuttle, not a pile of moon-gold at all.",
        payoff="Together the crew pressed the patches onto the tiny shuttle, and its silver side stopped hissing.",
        moral="Useful work can shine more brightly than pretend riches.",
        outcome="training_shuttle_repaired",
        ending_image="The patched shuttle gleamed under the hatch while the sign's star holes sparkled in quiet light.",
    ),
    "repair_map": TwistState(
        key="magnet",
        apparent="a secret comet medal",
        truth="a folded repair map for the loose attic hatch bolts",
        reveal="Behind the wall slat waited a folded repair map with bright circles around the loose hatch bolts that kept rattling.",
        payoff="The bright circles guided steady hands to the loose bolts, and the whole attic ladder stopped shivering.",
        moral="An honest clue is more valuable than a shiny prize when it helps people fix what matters.",
        outcome="hatch_secured",
        ending_image="The hatch sat firm and still, and the old ring on the rusty sign no longer trembled.",
    ),
}


HERO_NAMES = {
    "girl": ("Nova", "Mira", "Sera", "Tali"),
    "boy": ("Orin", "Jules", "Nico", "Bram"),
}

HELPER_NAMES = {
    "girl": ("Lyra", "June", "Pia", "Rin"),
    "boy": ("Jax", "Timo", "Reed", "Cal"),
}

CAPTAINS = ("Vega", "Orion", "Sol")
TRAITS = ("careful", "patient", "bright-eyed")


def valid_combo(attic_key: str, sign_key: str, temptation_key: str, twist_key: str) -> bool:
    if attic_key not in ATTICS or sign_key not in SIGNS:
        return False
    if temptation_key not in TEMPTATIONS or twist_key not in TWISTS:
        return False
    attic = ATTICS[attic_key]
    sign = SIGNS[sign_key]
    twist = TWISTS[twist_key]
    temptation = TEMPTATIONS[temptation_key]
    return sign.signal in attic.supports and sign.signal == twist.key and temptation.lure >= 2.0


def invalid_reason(attic_key: str, sign_key: str, temptation_key: str, twist_key: str) -> str:
    if attic_key not in ATTICS:
        return f"No story: unknown attic setting {attic_key!r}."
    if sign_key not in SIGNS:
        return f"No story: unknown rusty sign {sign_key!r}."
    if temptation_key not in TEMPTATIONS:
        return f"No story: unknown temptation {temptation_key!r}."
    if twist_key not in TWISTS:
        return f"No story: unknown twist {twist_key!r}."
    attic = ATTICS[attic_key]
    sign = SIGNS[sign_key]
    twist = TWISTS[twist_key]
    if sign.signal not in attic.supports:
        supported = ", ".join(attic.supports)
        return (
            f"No story: {attic.name} does not physically support a {sign.signal} clue. "
            f"Try one of: {supported}."
        )
    if sign.signal != twist.key:
        return (
            f"No story: {sign.key} points by {sign.signal}, but {twist_key!r} resolves by {twist.key}. "
            "The twist has to grow from the same physical clue."
        )
    return (
        "No story: this combination weakens the moral turn, so it is outside this world."
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for attic_key in sorted(ATTICS):
        for sign_key in sorted(SIGNS):
            for temptation_key in sorted(TEMPTATIONS):
                for twist_key in sorted(TWISTS):
                    if valid_combo(attic_key, sign_key, temptation_key, twist_key):
                        combos.append((attic_key, sign_key, temptation_key, twist_key))
    return combos


def ensure_reasonable(params: StoryParams) -> None:
    if not valid_combo(params.attic, params.sign, params.temptation, params.twist):
        raise StoryError(invalid_reason(params.attic, params.sign, params.temptation, params.twist))
    if params.hero == params.helper:
        raise StoryError("No story: hero and helper must be different people.")
    if params.hero_gender not in HERO_NAMES:
        raise StoryError(f"No story: unsupported hero gender {params.hero_gender!r}.")
    if params.helper_gender not in HELPER_NAMES:
        raise StoryError(f"No story: unsupported helper gender {params.helper_gender!r}.")


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def upper_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _r_decode_sign(world: World) -> bool:
    sign = world.get("sign")
    hero = world.get("hero")
    if sign.meters["studied"] >= THRESHOLD and "decoded_sign" not in world.fired:
        world.fired.add("decoded_sign")
        sign.meters["decoded"] += 1
        hero.memes["insight"] += 1
        world.facts["decoded_path"] = world.sign.study
        world.event("decoded_sign", clue=world.sign.signal)
        return True
    return False


def _r_notice_risk(world: World) -> bool:
    ladder = world.get("ladder")
    hero = world.get("hero")
    if ladder.meters["wobble"] >= THRESHOLD and "noticed_risk" not in world.fired:
        world.fired.add("noticed_risk")
        hero.memes["caution"] += 1
        world.event("noticed_risk", risk=world.attic.risk)
        return True
    return False


def _r_accept_help(world: World) -> bool:
    hero = world.get("hero")
    helper = world.get("helper")
    ladder = world.get("ladder")
    if (
        hero.memes["choose_help"] >= THRESHOLD
        and hero.memes["insight"] >= THRESHOLD
        and "accepted_help" not in world.fired
    ):
        world.fired.add("accepted_help")
        ladder.meters["steady"] += 1
        hero.memes["teamwork"] += 1
        helper.memes["trust"] += 1
        hero.memes["temptation"] = max(0.0, hero.memes["temptation"] - world.temptation.lure)
        world.event("accepted_help", helper=helper.label)
        return True
    return False


def _r_reveal_twist(world: World) -> bool:
    sign = world.get("sign")
    ladder = world.get("ladder")
    cache = world.get("cache")
    hero = world.get("hero")
    if (
        sign.meters["decoded"] >= THRESHOLD
        and ladder.meters["steady"] >= THRESHOLD
        and "revealed_truth" not in world.fired
    ):
        world.fired.add("revealed_truth")
        cache.meters["revealed"] += 1
        cache.meters["useful"] += 1
        hero.memes["wonder"] += 1
        hero.memes["generosity"] += 1
        world.event("revealed_truth", outcome=world.twist.outcome)
        return True
    return False


def _r_learn_lesson(world: World) -> bool:
    hero = world.get("hero")
    cache = world.get("cache")
    if cache.meters["revealed"] >= THRESHOLD and "learned_lesson" not in world.fired:
        world.fired.add("learned_lesson")
        hero.memes["wisdom"] += 1
        world.event("learned_lesson", moral=world.twist.moral)
        return True
    return False


RULES = [
    Rule("decode_sign", _r_decode_sign),
    Rule("notice_risk", _r_notice_risk),
    Rule("accept_help", _r_accept_help),
    Rule("reveal_twist", _r_reveal_twist),
    Rule("learn_lesson", _r_learn_lesson),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            if rule.apply(world):
                changed = True


def _story_people(params: StoryParams, attic: AtticState) -> World:
    world = World(
        params=params,
        attic=attic,
        sign=SIGNS[params.sign],
        temptation=TEMPTATIONS[params.temptation],
        twist=TWISTS[params.twist],
    )
    hero = world.add(
        Entity(
            id="hero",
            kind=params.hero_gender,
            label=params.hero,
            location="ladder_base",
            traits=[params.trait, "young"],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind=params.helper_gender,
            label=params.helper,
            location="ladder_base",
            traits=["steady", "kind"],
        )
    )
    captain = world.add(
        Entity(
            id="captain",
            kind="captain",
            label=params.captain,
            location="repair_bay",
            traits=["wise"],
        )
    )
    ladder = world.add(
        Entity(
            id="ladder",
            kind="attic_ladder",
            label=attic.ladder,
            location="attic_hatch",
        )
    )
    sign = world.add(
        Entity(
            id="sign",
            kind="rusty_sign",
            label=world.sign.object_label,
            location="upper_beam",
        )
    )
    cache = world.add(
        Entity(
            id="cache",
            kind="hidden_cache",
            label=world.twist.apparent,
            location="attic_shadow",
            owner=captain.label,
        )
    )
    world.facts["hero_name"] = hero.label
    world.facts["helper_name"] = helper.label
    world.facts["captain_name"] = captain.label
    return world


def predict_bad_choice(world: World) -> str:
    sim = world.copy()
    ladder = sim.get("ladder")
    hero = sim.get("hero")
    cache = sim.get("cache")
    temptation = sim.temptation
    ladder.meters["wobble"] += 2
    hero.memes["showing_off"] += 1 if temptation.kind == "boast" else 0
    hero.memes["selfishness"] += 1 if temptation.kind == "hide" else 0
    cache.meters["drop_risk"] += 1 if temptation.kind == "rush" else 0

    if cache.meters["drop_risk"] >= THRESHOLD:
        return f"If {hero.label} lunged early, the crate could skid loose and crash toward the floor."
    if hero.memes["selfishness"] >= THRESHOLD:
        return f"If {hero.label} hid the clue, nobody below would know where to steady the ladder or why the risk mattered."
    return f"If {hero.label} showed off, the ladder would sway harder and the true clue would be missed."


def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    sign = world.get("sign")
    ladder = world.get("ladder")
    cache = world.get("cache")

    hero.memes["curiosity"] += 1
    hero.memes["wonder"] += 1
    helper.memes["care"] += 1
    world.event("premise", rumor=world.sign.apparent_treasure)

    sign.meters["found"] += 1
    sign.meters["studied"] += 1
    hero.location = "middle_rung"
    world.event("found_sign", mark=world.sign.mark)
    propagate(world)

    ladder.meters["wobble"] += 1
    hero.memes["temptation"] += world.temptation.lure
    world.facts["predicted_bad_choice"] = predict_bad_choice(world)
    world.event("temptation", move=world.temptation.bad_move)
    propagate(world)

    hero.memes["choose_help"] += 1
    helper.location = "ladder_foot"
    world.event("choose_help", refusal=world.temptation.refusal)
    propagate(world)

    if cache.meters["revealed"] < THRESHOLD:
        raise StoryError("No story: the clue never turned into a real attic-ladder reveal.")

    hero.location = "attic_lip"
    cache.location = "open_case"
    world.facts["final_image"] = world.twist.ending_image
    world.facts["moral"] = world.twist.moral


def _beginning(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    captain = world.get("captain")
    return [
        (
            f"Once upon a time, {hero.label} was a {world.params.trait} young cadet on "
            f"Captain {captain.label}'s little roof-orbit crew."
        ),
        (
            f"One silver evening, {hero.label} and {helper.label} stood by {world.attic.ladder} in "
            f"{world.attic.name}, where {world.attic.attic_image}."
        ),
        (
            f"Below them, {world.attic.below_sound}, and everyone whispered that {world.sign.apparent_treasure} "
            f"might be hidden up there."
        ),
        (
            f"Halfway up, {hero.label} found {world.sign.object_label}. It was a rusty sign marked with "
            f"{world.sign.mark}."
        ),
    ]


def _turn(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("helper")
    caution_line = (
        f"{hero.label} did not grab wildly. {hero.pronoun('subject').capitalize()} studied the sign and noticed that "
        f"{world.sign.study}."
    )
    temptation_line = (
        f"Then the tempting mistake arrived: {world.temptation.bad_move}. "
        f"{upper_first(world.attic.risk)}, so even a small boast or greedy reach could turn mean."
    )
    prediction_line = str(world.facts["predicted_bad_choice"])
    choice_line = (
        f'{hero.label} swallowed the bad idea and said, "'
        f'{world.temptation.refusal}" {helper.label} planted both feet at the ladder base and held the rails steady.'
    )
    value_line = (
        f"{world.temptation.value_line} That was the brave choice in this space adventure."
    )
    return [caution_line, temptation_line, prediction_line, choice_line, value_line]


def _ending(world: World) -> list[str]:
    hero = world.get("hero")
    captain = world.get("captain")
    return [
        (
            f"With the ladder steady and the clue understood, {hero.label} reached into the dim attic edge. "
            f"{world.twist.reveal}"
        ),
        (
            f"That was the twist: instead of {world.twist.apparent.lower()}, the sign had been guarding "
            f"{world.twist.truth}."
        ),
        world.twist.payoff,
        (
            f"{hero.label} learned that {world.twist.moral.lower()}"
        ),
        (
            f"In the end, {lower_first(world.twist.ending_image)} Captain {captain.label} smiled up at the safe ladder, "
            f"and even the rusty sign looked like an honest little star."
        ),
    ]


def render_story(world: World) -> str:
    return "\n\n".join(
        [
            " ".join(_beginning(world)),
            " ".join(_turn(world)),
            " ".join(_ending(world)),
        ]
    )


def story_prompts(world: World) -> list[str]:
    hero = world.get("hero")
    return [
        (
            f"Tell a child-facing space adventure about {hero.label} on {world.attic.ladder} who finds "
            f"{world.sign.object_label}."
        ),
        (
            f"Make the middle turn about resisting {world.temptation.label} and choosing safe teamwork instead."
        ),
        (
            f"End with the twist that {world.twist.truth} and show this final image: {world.twist.ending_image}"
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    helper = world.get("helper")
    return [
        QAItem(
            question=f"What did the rusty sign really lead {hero.label} to?",
            answer=(
                f"It led {hero.label} to {world.twist.truth}. "
                f"The clue only looked like treasure at first, but it was really there to help the crew."
            ),
        ),
        QAItem(
            question=f"Why did {hero.label} refuse {world.temptation.label}?",
            answer=(
                f"{hero.label} refused because {world.attic.risk} and the climb was already risky. "
                f"{world.facts['predicted_bad_choice']} Asking {helper.label} for help kept the clue and the climber safe."
            ),
        ),
        QAItem(
            question="What was the twist in the attic?",
            answer=(
                f"The twist was that the hidden prize was not {world.twist.apparent.lower()} at all. "
                f"It was {world.twist.truth}, so the attic surprise turned into something useful."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=(
                f"{hero.label} learned that {world.twist.moral.lower()} "
                f"That lesson mattered because the careful choice helped everyone below the ladder."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why is it smart to ask for help on an attic ladder?",
            answer=(
                "A helper can steady the rails and watch the risky spots while someone climbs. "
                "That makes it easier to follow the real clue instead of rushing into danger."
            ),
        ),
        QAItem(
            question="How can a rusty sign still be useful in a space adventure?",
            answer=(
                "A rusty sign can still point truthfully if its marks fit the place around it. "
                "Old metal may look dull, but a real clue can keep working long after its paint fades."
            ),
        ),
        QAItem(
            question="Why can a useful tool be a better treasure than a shiny prize?",
            answer=(
                "A useful tool can fix a problem, protect people, or help everyone get home safely. "
                "A shiny prize may sparkle, but it does not always do any good."
            ),
        ),
    ]


ASP_RULES = """
attic_supports(A,K) :- supports(A,K).
sign_signal(S,K) :- sign_key(S,K).
twist_signal(T,K) :- twist_key(T,K).
tempting(T) :- temptation_lure(T,L), L >= 2.

valid(A,S,P,T) :-
    attic(A),
    sign(S),
    temptation(P),
    twist(T),
    attic_supports(A,K),
    sign_signal(S,K),
    twist_signal(T,K),
    tempting(P).

chosen_valid :-
    chosen_attic(A),
    chosen_sign(S),
    chosen_temptation(P),
    chosen_twist(T),
    valid(A,S,P,T).

chosen_outcome(O) :-
    chosen_valid,
    chosen_twist(T),
    twist_outcome(T,O).
"""


def asp_facts() -> str:
    from storyworlds import asp

    facts: list[str] = []
    for attic in ATTICS.values():
        facts.append(asp.fact("attic", attic.key))
        for signal in attic.supports:
            facts.append(asp.fact("supports", attic.key, signal))
    for sign in SIGNS.values():
        facts.append(asp.fact("sign", sign.key))
        facts.append(asp.fact("sign_key", sign.key, sign.signal))
    for temptation in TEMPTATIONS.values():
        facts.append(asp.fact("temptation", temptation.key))
        facts.append(asp.fact("temptation_lure", temptation.key, int(temptation.lure)))
    for twist_key, twist in TWISTS.items():
        facts.append(asp.fact("twist", twist_key))
        facts.append(asp.fact("twist_key", twist_key, twist.key))
        facts.append(asp.fact("twist_outcome", twist_key, twist.outcome))
    return "\n".join(facts)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    bits = [asp_facts(), ASP_RULES.strip()]
    if extra:
        bits.append(extra.strip())
    if show:
        bits.append(show.strip())
    return "\n".join(bits) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    atoms = asp.one_model(asp_program())
    return sorted(tuple(parts) for parts in asp.atoms(atoms, "valid"))


def asp_outcome(params: StoryParams) -> str:
    from storyworlds import asp

    extra = "\n".join(
        [
            asp.fact("chosen_attic", params.attic),
            asp.fact("chosen_sign", params.sign),
            asp.fact("chosen_temptation", params.temptation),
            asp.fact("chosen_twist", params.twist),
        ]
    )
    symbols = asp.one_model(
        asp_program(extra=extra, show="#show chosen_valid/0.\n#show chosen_outcome/1.")
    )
    if not asp.atoms(symbols, "chosen_valid"):
        raise StoryError(invalid_reason(params.attic, params.sign, params.temptation, params.twist))
    outcomes = asp.atoms(symbols, "chosen_outcome")
    if not outcomes:
        raise StoryError("ASP parity failed: no chosen outcome was derived.")
    return str(outcomes[0][0])


def matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    if args.attic:
        combos = [c for c in combos if c[0] == args.attic]
    if args.sign:
        combos = [c for c in combos if c[1] == args.sign]
    if args.temptation:
        combos = [c for c in combos if c[2] == args.temptation]
    if args.twist:
        combos = [c for c in combos if c[3] == args.twist]
    return combos


def _pick_name(
    explicit: Optional[str],
    pool: tuple[str, ...],
    rng: random.Random,
    ordinal: int,
) -> str:
    if explicit:
        return explicit
    return pool[ordinal % len(pool)] if ordinal >= 0 else rng.choice(pool)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1, help="number of samples to generate")
    parser.add_argument("--all", action="store_true", help="generate all valid parameter combinations")
    parser.add_argument("--seed", type=int, default=None, help="random seed")
    parser.add_argument("--trace", action="store_true", help="show world-model trace")
    parser.add_argument("--qa", action="store_true", help="show prompts and QA sets")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of plain text")
    parser.add_argument("--asp", action="store_true", help="show ASP-derived combinations or selected outcome")
    parser.add_argument("--verify", action="store_true", help="run Python/ASP parity and sample checks")
    parser.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    parser.add_argument("--attic", choices=sorted(ATTICS), help="attic setting key")
    parser.add_argument("--sign", choices=sorted(SIGNS), help="rusty sign key")
    parser.add_argument("--temptation", choices=sorted(TEMPTATIONS), help="temptation key")
    parser.add_argument("--twist", choices=sorted(TWISTS), help="twist key")
    parser.add_argument("--hero", help="hero name")
    parser.add_argument("--hero-gender", choices=sorted(HERO_NAMES), help="hero gender")
    parser.add_argument("--helper", help="helper name")
    parser.add_argument("--helper-gender", choices=sorted(HELPER_NAMES), help="helper gender")
    parser.add_argument("--captain", choices=CAPTAINS, help="captain name")
    parser.add_argument("--trait", choices=TRAITS, help="hero trait")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    ordinal: int = -1,
) -> StoryParams:
    combos = matching_combos(args)
    if not combos:
        raise StoryError("No story: no valid parameter combinations match the requested filters.")
    combo = combos[ordinal % len(combos)] if ordinal >= 0 else rng.choice(combos)
    attic_key, sign_key, temptation_key, twist_key = combo

    hero_gender = args.hero_gender or ("girl" if ordinal % 2 == 0 else "boy" if ordinal >= 0 else rng.choice(["girl", "boy"]))
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = _pick_name(args.hero, HERO_NAMES[hero_gender], rng, ordinal)
    helper = _pick_name(args.helper, HELPER_NAMES[helper_gender], rng, ordinal + 1 if ordinal >= 0 else -1)
    if hero == helper:
        helper_pool = tuple(name for name in HELPER_NAMES[helper_gender] if name != hero)
        helper = _pick_name(args.helper, helper_pool, rng, ordinal + 2 if ordinal >= 0 else -1)
    captain = args.captain or (CAPTAINS[ordinal % len(CAPTAINS)] if ordinal >= 0 else rng.choice(CAPTAINS))
    trait = args.trait or (TRAITS[ordinal % len(TRAITS)] if ordinal >= 0 else rng.choice(TRAITS))
    params = StoryParams(
        attic=attic_key,
        sign=sign_key,
        temptation=temptation_key,
        twist=twist_key,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        captain=captain,
        trait=trait,
        seed=args.seed,
    )
    ensure_reasonable(params)
    return params


def generate(params: StoryParams) -> StorySample:
    ensure_reasonable(params)
    world = _story_people(params, ATTICS[params.attic])
    simulate(world)
    sample = StorySample(
        params=params,
        story=render_story(world),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    json_mode: bool = False,
) -> None:
    if json_mode:
        print(sample.to_json())
        return
    print(sample.story)
    if qa:
        print("\nPrompts:")
        for item in sample.prompts:
            print(f"- {item}")
        print("\nStory QA:")
        for item in sample.story_qa:
            print(f"- Q: {item.question}")
            print(f"  A: {item.answer}")
        print("\nWorld QA:")
        for item in sample.world_qa:
            print(f"- Q: {item.question}")
            print(f"  A: {item.answer}")
    if trace and sample.world is not None:
        print("\n" + sample.world.trace())


def _verify_story(sample: StorySample) -> None:
    if "rusty sign" not in sample.story.lower():
        raise StoryError("Verification failed: story never mentions the rusty sign.")
    if "attic ladder" not in sample.story.lower():
        raise StoryError("Verification failed: story never mentions the attic ladder.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Verification failed: unresolved template braces in story text.")
    if len(sample.story_qa) < 3 or len(sample.world_qa) < 3:
        raise StoryError("Verification failed: QA sets are incomplete.")
    world = sample.world
    if world is None:
        raise StoryError("Verification failed: sample lost its world model.")
    if world.get("cache").meters["revealed"] < THRESHOLD:
        raise StoryError("Verification failed: hidden cache never became visible.")
    if world.get("hero").memes["wisdom"] < THRESHOLD:
        raise StoryError("Verification failed: moral state never landed in the hero.")


def verify() -> int:
    py = set(valid_combos())
    asp = set(asp_valid_combos())
    if py != asp:
        missing = sorted(py - asp)
        extra = sorted(asp - py)
        raise StoryError(f"ASP parity failed. Missing={missing} Extra={extra}")

    rng = random.Random(0)
    combos = valid_combos()
    for idx, _combo in enumerate(combos):
        params = StoryParams(
            attic=_combo[0],
            sign=_combo[1],
            temptation=_combo[2],
            twist=_combo[3],
            hero=HERO_NAMES["girl"][idx % len(HERO_NAMES["girl"])],
            hero_gender="girl",
            helper=HELPER_NAMES["boy"][idx % len(HELPER_NAMES["boy"])],
            helper_gender="boy",
            captain=CAPTAINS[idx % len(CAPTAINS)],
            trait=TRAITS[idx % len(TRAITS)],
            seed=0,
        )
        sample = generate(params)
        _verify_story(sample)
        if asp_outcome(params) != TWISTS[params.twist].outcome:
            raise StoryError(
                f"ASP outcome mismatch for {params.attic}/{params.sign}/{params.temptation}/{params.twist}."
            )

    smoke_params = resolve_params(build_parser().parse_args([]), rng)
    _verify_story(generate(smoke_params))
    print(f"verify: ok ({len(combos)} valid combos checked)")
    return 0


def _json_dump(samples: Iterable[StorySample]) -> None:
    rows = [sample.to_dict() for sample in samples]
    if len(rows) == 1:
        print(json.dumps(rows[0], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(rows, indent=2, ensure_ascii=False))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(
            asp_program(
                show="#show valid/4.\n#show chosen_valid/0.\n#show chosen_outcome/1."
            )
        )
        return

    if args.verify:
        raise SystemExit(verify())

    rng = random.Random(args.seed)

    if args.asp:
        if any([args.attic, args.sign, args.temptation, args.twist]):
            params = resolve_params(args, rng)
            row = {
                "params": asdict(params),
                "valid": valid_combo(params.attic, params.sign, params.temptation, params.twist),
                "outcome": asp_outcome(params),
            }
            print(json.dumps(row, indent=2, ensure_ascii=False))
            return
        print(json.dumps(asp_valid_combos(), indent=2, ensure_ascii=False))
        return

    if args.all:
        combos = matching_combos(args)
        samples = [generate(resolve_params(args, rng, ordinal=i)) for i in range(len(combos))]
    else:
        samples = [generate(resolve_params(args, rng)) for _ in range(max(1, args.n))]

    if args.json:
        _json_dump(samples)
        return

    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 72 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, json_mode=False)


if __name__ == "__main__":
    main()
