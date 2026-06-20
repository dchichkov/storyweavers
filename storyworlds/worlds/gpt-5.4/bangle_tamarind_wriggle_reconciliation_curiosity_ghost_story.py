#!/usr/bin/env python3
"""
bangle_tamarind_wriggle_reconciliation_curiosity_ghost_story.py
================================================================

A small StoryWorld for the seed:

    words: bangle, tamarind, wriggle
    features: Reconciliation, Curiosity
    style: Ghost Story

Internal source tale:
    In a tamarind courtyard, a child notices a pale wriggle of ghost-light
    under an old tree. The ghost is not trying to scare anyone; it is trying
    to return a lost bangle that carries an apology the living relative never
    heard. Curiosity helps the child match the right search to the right clue,
    uncover the bangle, and bring it home. The ending image proves that
    reconciliation happened in the physical world, not only in words.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


SOURCE_TALE = (
    "A child in a tamarind yard sees a ghost-light wriggle near an old hiding place. "
    "The ghost wants a lost bangle found so that a living relative can finally hear an apology. "
    "The child follows curiosity instead of panic, matches a careful search to the clue, "
    "and carries the bangle into a scene of reconciliation."
)


@dataclass(frozen=True)
class CourtyardSpot:
    key: str
    phrase: str
    landmark: str
    dusk_detail: str
    support_keys: tuple[str, ...]
    end_view: str


@dataclass(frozen=True)
class GhostMemory:
    key: str
    name: str
    role: str
    living_relative: str
    regret: str
    whisper: str
    reply: str
    needs_tags: tuple[str, ...]


@dataclass(frozen=True)
class Bangle:
    key: str
    phrase: str
    clue_key: str
    hiding_place: str
    memory_text: str
    apology_line: str
    proof_image: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class CuriosityMethod:
    key: str
    phrase: str
    action: str
    tool: str
    solves: tuple[str, ...]
    calming_line: str


@dataclass
class StoryParams:
    spot: str
    ghost: str
    bangle: str
    method: str
    hero: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    spot: CourtyardSpot
    ghost: GhostMemory
    bangle: Bangle
    method: CuriosityMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)
    opening_text: str = ""
    clue_text: str = ""
    turn_text: str = ""
    ending_text: str = ""
    story: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"spot={self.spot.key} ghost={self.ghost.key} bangle={self.bangle.key} "
            f"method={self.method.key} hero={self.params.hero}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<10} ({ent.kind:<10}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


SPOTS: dict[str, CourtyardSpot] = {
    "root_nook": CourtyardSpot(
        key="root_nook",
        phrase="the root nook under the tamarind tree",
        landmark="twisted roots around a clay lamp",
        dusk_detail="the longest shadows gathered there first",
        support_keys=("wriggle", "glint"),
        end_view="the roots rested in a quiet half-moon around the lamp",
    ),
    "pod_basket": CourtyardSpot(
        key="pod_basket",
        phrase="the pod basket by the veranda steps",
        landmark="a wicker basket full of dry tamarind shells",
        dusk_detail="the dry pods clicked whenever the evening cooled",
        support_keys=("rattle", "wriggle"),
        end_view="the basket sat still, and not one pod clicked in complaint",
    ),
    "swing_post": CourtyardSpot(
        key="swing_post",
        phrase="the swing post beside the tamarind trunk",
        landmark="a rope swing that brushed the bark",
        dusk_detail="the swing chain caught every scrap of moonlight",
        support_keys=("glint", "rattle"),
        end_view="the swing moved only once in the soft night breeze",
    ),
}

GHOSTS: dict[str, GhostMemory] = {
    "leela": GhostMemory(
        key="leela",
        name="Leela",
        role="the older sister who had walked away from home in anger",
        living_relative="Auntie Devi",
        regret="Leela had accused her sister of taking a keepsake and never returned to undo the wound.",
        whisper='"Please let my sister hold the bangle and know I was sorry," the ghost whispered.',
        reply='"I was hurt, but I was hurting too. Let the tamarind tree keep the quarrel no longer," Auntie Devi said.',
        needs_tags=("family", "apology"),
    ),
    "parveen": GhostMemory(
        key="parveen",
        name="Parveen",
        role="the cousin who had laughed at the wrong moment during a harvest dance",
        living_relative="Cousin Sara",
        regret="Parveen had mocked Sara after a stumble and let pride grow larger than the family feast.",
        whisper='"If Sara sees the bangle, she will remember the dance before she remembers the sting," the ghost whispered.',
        reply='"We were children with sharp tongues. I would rather keep the memory than the blame," Cousin Sara said.',
        needs_tags=("festival", "apology"),
    ),
    "bhaskar": GhostMemory(
        key="bhaskar",
        name="Bhaskar",
        role="the brother who had broken a promise beneath the tree",
        living_relative="Uncle Manoj",
        regret="Bhaskar had chosen anger over a promise to share the tamarind sweets and never repaired the break.",
        whisper='"My brother should hear the promise ring again, not only the silence after it," the ghost whispered.',
        reply='"The promise was ours, and so is the forgiveness," Uncle Manoj said.',
        needs_tags=("promise", "family"),
    ),
}

BANGLES: dict[str, Bangle] = {
    "brass_mango": Bangle(
        key="brass_mango",
        phrase="a brass mango-leaf bangle",
        clue_key="rattle",
        hiding_place="inside a fold of husks where the dry pods could tap against it",
        memory_text="it had clicked between two sisters while they shelled tamarind together on hot afternoons",
        apology_line="I should have asked before I took what we both loved.",
        proof_image="Auntie Devi slipped the brass bangle over her wrist, and its warm ring sounded like yes.",
        tags=("family", "apology"),
    ),
    "green_glass": Bangle(
        key="green_glass",
        phrase="a green glass bangle",
        clue_key="glint",
        hiding_place="beneath leaf mold where one bright edge could still catch the lantern",
        memory_text="it had shone at the harvest dance when cousins spun under the tamarind branches",
        apology_line="I let pride crack our laughter before the glass ever cracked.",
        proof_image="The green bangle glowed in Cousin Sara's hand while the tamarind leaves stopped shaking.",
        tags=("festival", "apology"),
    ),
    "silver_bell": Bangle(
        key="silver_bell",
        phrase="a silver bell bangle",
        clue_key="wriggle",
        hiding_place="inside a curtain of root fibers that seemed to wriggle in the moonlight",
        memory_text="it had chimed when two brothers promised to share the sweetest tamarind pods fairly",
        apology_line="I broke our promise when anger felt easier than kindness.",
        proof_image="The silver bangle rested in Uncle Manoj's palm, and the tiny bell made one peaceful note.",
        tags=("promise", "family"),
    ),
}

METHODS: dict[str, CuriosityMethod] = {
    "listen_still": CuriosityMethod(
        key="listen_still",
        phrase="a listen-still search",
        action="stood quiet until the faintest rattle chose one hiding place",
        tool="quiet ears",
        solves=("rattle",),
        calming_line="The more quietly the child listened, the less the yard sounded angry.",
    ),
    "lantern_low": CuriosityMethod(
        key="lantern_low",
        phrase="a lantern-low search",
        action="swept a lantern close to the ground until a shy glint answered back",
        tool="a brass lantern",
        solves=("glint",),
        calming_line="Curiosity became a careful light instead of a frightened guess.",
    ),
    "trace_wriggle": CuriosityMethod(
        key="trace_wriggle",
        phrase="a finger-trace search",
        action="traced the place where the shadow seemed to wriggle like gray thread in water",
        tool="bare fingertips",
        solves=("wriggle",),
        calming_line="By following the wriggle slowly, the child turned fear into understanding.",
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Tara", "Nila"),
    "boy": ("Arun", "Kavi", "Neel"),
}


def valid_combo(spot: str, ghost: str, bangle: str, method: str) -> bool:
    if spot not in SPOTS or ghost not in GHOSTS or bangle not in BANGLES or method not in METHODS:
        return False
    clue = BANGLES[bangle].clue_key
    if clue not in SPOTS[spot].support_keys:
        return False
    if clue not in METHODS[method].solves:
        return False
    bangle_tags = set(BANGLES[bangle].tags)
    return all(tag in bangle_tags for tag in GHOSTS[ghost].needs_tags)


def explain_rejection(spot: str, ghost: str, bangle: str, method: str) -> str:
    if spot not in SPOTS:
        return f"No story: unknown tamarind-yard spot {spot!r}."
    if ghost not in GHOSTS:
        return f"No story: unknown ghost memory {ghost!r}."
    if bangle not in BANGLES:
        return f"No story: unknown bangle {bangle!r}."
    if method not in METHODS:
        return f"No story: unknown curiosity method {method!r}."
    clue = BANGLES[bangle].clue_key
    if clue not in SPOTS[spot].support_keys:
        return (
            f"No story: {SPOTS[spot].phrase} cannot ground {BANGLES[bangle].phrase}; "
            f"that bangle needs a {clue} clue."
        )
    if clue not in METHODS[method].solves:
        return (
            f"No story: {METHODS[method].phrase} does not fit {BANGLES[bangle].phrase}; "
            f"try a method that can read a {clue} clue."
        )
    missing = [tag for tag in GHOSTS[ghost].needs_tags if tag not in BANGLES[bangle].tags]
    if missing:
        return (
            f"No story: {GHOSTS[ghost].name}'s haunting needs a bangle carrying "
            f"{', '.join(missing)} memory."
        )
    return "No story: the tamarind-yard choices do not form a reasonable ghost tale."


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for spot in sorted(SPOTS):
        for ghost in sorted(GHOSTS):
            for bangle in sorted(BANGLES):
                for method in sorted(METHODS):
                    if valid_combo(spot, ghost, bangle, method):
                        combos.append((spot, ghost, bangle, method))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def hiding_place_for(spot: str, clue: str) -> str:
    hiding_map: dict[tuple[str, str], str] = {
        ("pod_basket", "rattle"): "inside a fold of husks where the dry pods could tap against it",
        ("swing_post", "rattle"): "in a crack of the swing post where loose seed shells had gathered",
        ("root_nook", "glint"): "beneath leaf mold between the roots where one edge could still catch the lantern",
        ("swing_post", "glint"): "under a worn brick below the swing where moonlight could reach it",
        ("root_nook", "wriggle"): "inside a curtain of root fibers that seemed to wriggle in the moonlight",
        ("pod_basket", "wriggle"): "under the basket handle where the ghost-light kept wriggling through the weave",
    }
    return hiding_map[(spot, clue)]


def build_world(params: StoryParams) -> World:
    spot = SPOTS[params.spot]
    ghost = GHOSTS[params.ghost]
    bangle = BANGLES[params.bangle]
    method = METHODS[params.method]
    hero = Entity(name=params.hero, kind="child")
    spirit = Entity(name=ghost.name, kind="ghost")
    relative = Entity(name=ghost.living_relative, kind="adult")
    tree = Entity(name="the tamarind tree", kind="tree")
    bracelet = Entity(name=bangle.phrase, kind="bangle")
    world = World(
        params=params,
        spot=spot,
        ghost=ghost,
        bangle=bangle,
        method=method,
        entities={
            "Hero": hero,
            "Ghost": spirit,
            "Relative": relative,
            "Tree": tree,
            "Bangle": bracelet,
        },
    )
    hero.set_meter("distance_m", 0.0)
    hero.set_meter("carried_object", 0.0)
    spirit.set_meter("visible", 0.0)
    spirit.set_meter("shadow_wriggle", 1.0)
    relative.set_meter("door_open", 0.0)
    bracelet.set_meter("hidden", 1.0)
    bracelet.set_meter("found", 0.0)
    bracelet.set_meter("worn_or_held", 0.0)
    tree.set_tag("landmark", spot.landmark)
    tree.set_tag("dusk_detail", spot.dusk_detail)
    bracelet.set_tag("hiding_place", hiding_place_for(spot.key, bangle.clue_key))
    bracelet.set_tag("memory_text", bangle.memory_text)
    world.facts["source_tale"] = SOURCE_TALE
    world.facts["ending"] = "unresolved"
    return world


def _clue_line(world: World) -> str:
    clue_map: dict[tuple[str, str], str] = {
        ("pod_basket", "rattle"): (
            "From the wicker basket, a dry little rattle came twice, and a pale line of light seemed to wriggle along the husks."
        ),
        ("swing_post", "rattle"): (
            "The swing chain gave two dry ticks, and a pale line of light wriggled at the foot of the post."
        ),
        ("root_nook", "glint"): (
            "A thin ghost-light wriggled across the bricks and stopped where a green glint hid under the leaves."
        ),
        ("swing_post", "glint"): (
            "Moonlight slid down the swing rope and halted at a green glint tucked beneath a worn brick."
        ),
        ("root_nook", "wriggle"): (
            "The hanging root fibers began to wriggle like gray thread in water, though the evening air was still."
        ),
        ("pod_basket", "wriggle"): (
            "Ghost-light wriggled through the basket weave and curled under the handle as if one hidden thing were trying to breathe."
        ),
    }
    return clue_map[(world.spot.key, world.bangle.clue_key)]


def _r_open_under_tamarind(world: World) -> bool:
    hero = world.entities["Hero"]
    spirit = world.entities["Ghost"]
    tree = world.entities["Tree"]

    hero.add_meme("curiosity", 1.1)
    hero.add_meme("fear", 0.6)
    hero.add_meme("kindness", 0.4)
    hero.add_meter("distance_m", 1.5)
    spirit.add_meme("regret", 1.6)
    spirit.add_meme("hope", 0.5)
    tree.add_meme("memory", 1.1)
    tree.add_meme("hush", 0.8)

    world.opening_text = (
        f"The tamarind courtyard held dusk longer than the lane outside. "
        f"{world.params.hero} had only come to collect a bowl of tamarind pods when something near {world.spot.phrase} gave a slow wriggle, "
        f"even though {world.spot.dusk_detail} and no wind touched the leaves."
    )
    world.note(world.opening_text)
    return True


def _r_reveal_ghost_need(world: World) -> bool:
    hero = world.entities["Hero"]
    spirit = world.entities["Ghost"]
    relative = world.entities["Relative"]

    spirit.set_meter("visible", 1.0)
    spirit.add_meme("hope", 0.7)
    hero.add_meme("fear", 0.3)
    relative.add_meme("hurt", 1.2)
    relative.add_meme("memory", 0.8)

    world.clue_text = (
        f"It was not a snake or a trick of smoke. It was the ghost of {world.ghost.name}, {world.ghost.role}. "
        f"{_clue_line(world)} {world.ghost.whisper} {world.ghost.regret}"
    )
    world.note(world.clue_text)
    return True


def _r_follow_curiosity(world: World) -> bool:
    hero = world.entities["Hero"]
    spirit = world.entities["Ghost"]
    bracelet = world.entities["Bangle"]
    tree = world.entities["Tree"]

    hero.add_meme("curiosity", 0.8)
    hero.add_meme("courage", 1.0)
    hero.add_meme("fear", -0.4)
    hero.add_meter("distance_m", 1.2)
    hero.set_meter("carried_object", 1.0)
    spirit.add_meme("trust", 0.9)
    tree.add_meme("hush", 0.4)
    bracelet.set_meter("hidden", 0.0)
    bracelet.set_meter("found", 1.0)
    bracelet.set_meter("worn_or_held", 1.0)

    world.turn_text = (
        f"Curiosity pulled harder than fear, so {world.params.hero} chose {world.method.phrase}. "
        f"{world.params.hero} {world.method.action}. {world.method.calming_line} "
        f"At last, hidden {world.entities['Bangle'].tags['hiding_place']}, {world.params.hero} found {world.bangle.phrase}. "
        f"The bangle mattered because {world.bangle.memory_text}."
    )
    world.note(world.turn_text)
    return True


def _r_reconcile_by_touch(world: World) -> bool:
    hero = world.entities["Hero"]
    spirit = world.entities["Ghost"]
    relative = world.entities["Relative"]
    bracelet = world.entities["Bangle"]

    relative.set_meter("door_open", 1.0)
    relative.add_meme("hurt", -0.6)
    relative.add_meme("forgiveness", 1.5)
    relative.add_meme("peace", 1.1)
    spirit.add_meme("peace", 1.8)
    spirit.add_meme("regret", -0.8)
    spirit.add_meme("trust", 0.7)
    hero.add_meme("kindness", 0.9)
    hero.add_meme("relief", 1.0)
    bracelet.set_tag("heard_apology", "yes")
    world.facts["ending"] = "reconciled"

    world.ending_text = (
        f"{world.params.hero} carried the bangle to {world.ghost.living_relative} on the veranda and repeated the words hidden inside it: "
        f"\"{world.bangle.apology_line}\" {world.ghost.reply} "
        f"The ghost no longer had to wriggle the shadows for attention. {world.bangle.proof_image} "
        f"Behind them, {world.spot.end_view}, and the tamarind yard sounded like a place that had finally forgiven itself."
    )
    world.note(world.ending_text)
    return True


RULES: tuple[tuple[str, Callable[[World], bool]], ...] = (
    ("open_under_tamarind", _r_open_under_tamarind),
    ("reveal_ghost_need", _r_reveal_ghost_need),
    ("follow_curiosity", _r_follow_curiosity),
    ("reconcile_by_touch", _r_reconcile_by_touch),
)


def run_world(world: World) -> World:
    for name, rule in RULES:
        fired = rule(world)
        if fired:
            world.fired_rules.append(name)
    return world


def render_story(world: World) -> str:
    middle = (
        f"{world.clue_text} Then {world.params.hero} stayed in the yard instead of running inside. "
        f"{world.turn_text}"
    )
    ending = world.ending_text
    return "\n\n".join((world.opening_text, middle, ending))


def prompts_for(world: World) -> list[str]:
    return [
        "Write a child-friendly ghost story set in a tamarind courtyard.",
        f"Include a lost bangle as the physical object that carries the apology for {world.ghost.living_relative}.",
        f"Let curiosity guide {world.params.hero} through {world.method.phrase}, and keep the word wriggle in the haunting.",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What first made the child stop and pay attention in the tamarind yard?",
            answer=(
                f"{world.params.hero} noticed a strange wriggle near {world.spot.phrase} when the rest of the courtyard was still. "
                f"That moving patch of ghost-light felt too purposeful to ignore, so curiosity took hold before panic could."
            ),
        ),
        QAItem(
            question="Why was the ghost pointing toward the hidden bangle?",
            answer=(
                f"{world.ghost.name} needed {world.ghost.living_relative} to touch {world.bangle.phrase} and hear the apology tied to it. "
                f"The bangle carried the family memory that the ghost could not deliver alone."
            ),
        ),
        QAItem(
            question="How did curiosity help the child search in the right way?",
            answer=(
                f"{world.params.hero} matched the clue to {world.method.phrase} instead of clawing through the whole yard. "
                f"That careful choice let the child read the place the way the haunting wanted it to be read."
            ),
        ),
        QAItem(
            question="Why did the living relative forgive once the bangle was found?",
            answer=(
                f"The bangle brought back a shared memory, not just a missing object. "
                f"When {world.ghost.living_relative} held it and heard the apology, the old hurt finally had something solid to answer."
            ),
        ),
        QAItem(
            question="What final image proves that reconciliation truly happened?",
            answer=(
                f"The ending image is this: {world.bangle.proof_image} "
                f"That picture proves the change is real because the object is back in loving hands and the haunted yard grows quiet at the same moment."
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Which physical object carries the main change in this story world?",
            answer=(
                f"The main carrier is {world.bangle.phrase}. "
                f"It holds the memory, the apology, and the touch that lets reconciliation move from a ghost's wish into the living world."
            ),
        ),
        QAItem(
            question="Why is the tamarind setting important to the haunting?",
            answer=(
                "The tamarind yard matters because the quarrel, the hiding place, and the memory all belong to that one physical place. "
                "The ghost is anchored there until the object hidden under its branches is found and understood."
            ),
        ),
        QAItem(
            question="How do curiosity and reconciliation work together in this domain?",
            answer=(
                "Curiosity opens the path by helping the child notice and test the clue instead of fleeing from it. "
                "Reconciliation finishes the path when the discovered object lets the living relative answer the old hurt with forgiveness."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.spot, params.ghost, params.bangle, params.method):
        raise StoryError(explain_rejection(params.spot, params.ghost, params.bangle, params.method))
    world = run_world(build_world(params))
    story = render_story(world)
    world.story = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts ==", *[f"{i}. {item}" for i, item in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Tamarind-yard ghost story of curiosity and reconciliation.")
    parser.add_argument("--spot", choices=sorted(SPOTS))
    parser.add_argument("--ghost", choices=sorted(GHOSTS))
    parser.add_argument("--bangle", choices=sorted(BANGLES))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.spot is None or combo[0] == args.spot)
        and (args.ghost is None or combo[1] == args.ghost)
        and (args.bangle is None or combo[2] == args.bangle)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.spot or "root_nook",
                args.ghost or "leela",
                args.bangle or "silver_bell",
                args.method or "trace_wriggle",
            )
        )
    spot, ghost, bangle, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    return StoryParams(
        spot=spot,
        ghost=ghost,
        bangle=bangle,
        method=method,
        hero=hero,
        gender=gender,
    )


ASP_RULES = r"""
invalid(S,G,B,M) :- spot(S), ghost(G), bangle(B), method(M), bangle_clue(B,C), not spot_support(S,C).
invalid(S,G,B,M) :- spot(S), ghost(G), bangle(B), method(M), bangle_clue(B,C), not method_solves(M,C).
invalid(S,G,B,M) :- spot(S), ghost(G), bangle(B), method(M), ghost_need(G,T), not bangle_tag(B,T).

valid(S,G,B,M) :- spot(S), ghost(G), bangle(B), method(M), not invalid(S,G,B,M).

#show valid/4.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for spot in SPOTS.values():
        rows.append(asp.fact("spot", spot.key))
        for support in spot.support_keys:
            rows.append(asp.fact("spot_support", spot.key, support))
    for ghost in GHOSTS.values():
        rows.append(asp.fact("ghost", ghost.key))
        for tag in ghost.needs_tags:
            rows.append(asp.fact("ghost_need", ghost.key, tag))
    for bangle in BANGLES.values():
        rows.append(asp.fact("bangle", bangle.key))
        rows.append(asp.fact("bangle_clue", bangle.key, bangle.clue_key))
        for tag in bangle.tags:
            rows.append(asp.fact("bangle_tag", bangle.key, tag))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        for clue in method.solves:
            rows.append(asp.fact("method_solves", method.key, clue))
    return "\n".join(rows)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            spot=combo[0],
            ghost=combo[1],
            bangle=combo[2],
            method=combo[3],
            hero="Mira",
            gender="girl",
            seed=2400 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if "tamarind" not in story:
            problems.append(f"{combo}: story is missing the seed word 'tamarind'")
        if "bangle" not in story:
            problems.append(f"{combo}: story is missing the seed word 'bangle'")
        if "wriggle" not in story:
            problems.append(f"{combo}: story is missing the seed word 'wriggle'")
        if "ghost" not in story:
            problems.append(f"{combo}: story does not read like a ghost story")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story-grounded QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world-knowledge QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if world is None:
            problems.append(f"{combo}: sample is missing its world model")
            continue
        if world.facts.get("ending") != "reconciled":
            problems.append(f"{combo}: world never reached reconciliation")
        if world.entities["Bangle"].meters.get("found") != 1.0:
            problems.append(f"{combo}: bangle was never marked as found")
        if world.entities["Relative"].memes.get("forgiveness", 0.0) < 1.0:
            problems.append(f"{combo}: living relative never reached forgiveness")
        if world.entities["Ghost"].memes.get("peace", 0.0) < 1.0:
            problems.append(f"{combo}: ghost never reached peace")
    return problems


def verify_world() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, and reconciliation checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    for offset in range(max(1, args.n)):
        seed = base_seed + offset
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))
    return samples


def _all_samples(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos()):
        gender = args.gender or ("girl" if index % 2 == 0 else "boy")
        seed = (args.seed if args.seed is not None else 5000) + index
        hero = args.hero or _pick_hero(random.Random(seed), gender)
        params = StoryParams(
            spot=combo[0],
            ghost=combo[1],
            bangle=combo[2],
            method=combo[3],
            hero=hero,
            gender=gender,
            seed=seed,
        )
        samples.append(generate(params))
    return samples


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.asp:
            print(asp_valid_combos())
            return 0
        if args.verify:
            return verify_world()

        samples = _all_samples(args) if args.all else _sample_n(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
