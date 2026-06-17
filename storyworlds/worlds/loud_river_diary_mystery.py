#!/usr/bin/env python3
"""A storyworld for an adventure mystery by a loud river.

Seed:
    Words: loud river, diary
    Features: Mystery to Solve
    Style: Adventure

The protagonist finds a diary near a loud river. A risky investigation would
damage the key clue, so a companion predicts that consequence on a copied world
and suggests a tool that lets the mystery be solved without losing evidence.
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


@dataclass(frozen=True)
class RiverPlace:
    id: str
    label: str
    scene: str
    affords: set[str]
    opening: str
    tags: set[str]


@dataclass(frozen=True)
class SearchMove:
    id: str
    label: str
    want: str
    gerund: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class DiaryClue:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    answer: str
    mystery: str
    tags: set[str]


@dataclass(frozen=True)
class Kit:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
    tags: set[str]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    zone: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        forms = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return forms.get(self.gender or "child", forms["child"])[case]


class World:
    def __init__(self, params: "StoryParams"):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_move: Optional[str] = None
        self.active_clue: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, sentence: str) -> None:
        sentence = sentence.strip()
        if sentence:
            self.paragraphs[-1].append(sentence)

    def break_para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def protection_for(self, clue: Entity, risk: str) -> bool:
        for ent in self.entities.values():
            if not ent.protective or ent.used_on != clue.id:
                continue
            if clue.zone in ent.covers and risk in ent.guards:
                return True
        return False

    def trace(self) -> str:
        lines = [
            f"place: {self.params.place}",
            f"fired rules: {', '.join(self.fired_names) if self.fired_names else 'none'}",
        ]
        for ent in self.entities.values():
            bits = [f"  {ent.id} | {ent.kind} | {ent.label}"]
            if ent.zone:
                bits.append(f"zone={ent.zone}")
            if ent.guards:
                bits.append(f"guards={sorted(ent.guards)}")
            if ent.covers:
                bits.append(f"covers={sorted(ent.covers)}")
            if ent.used_on:
                bits.append(f"used_on={ent.used_on}")
            lines.append(" | ".join(bits))
            if ent.meters:
                lines.append(f"    meters={dict(ent.meters)}")
            if ent.memes:
                lines.append(f"    memes={dict(ent.memes)}")
        return "\n".join(lines)


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _mark(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_clue_damage(world: World, narrate: bool) -> bool:
    if not world.active_move or not world.active_clue:
        return False
    move = MOVES[world.active_move]
    hero = world.get("hero")
    clue = world.get(world.active_clue)
    if hero.meters[move.risk] < THRESHOLD:
        return False
    if clue.zone not in move.zones or move.risk not in clue.guards:
        return False
    if world.protection_for(clue, move.risk):
        return False
    if not _mark(world, "clue_damage", move.id, clue.id, move.risk):
        return False
    clue.meters["damaged"] += 1
    clue.meters["mystery_blocked"] += 1
    if narrate:
        world.say(f"The {clue.label} nearly lost the mark that made the mystery answerable.")
    return True


def _r_companion_alarm(world: World, narrate: bool) -> bool:
    clue_id = world.active_clue
    companion_id = world.facts.get("companion")
    if not isinstance(clue_id, str) or not isinstance(companion_id, str):
        return False
    clue = world.get(clue_id)
    companion = world.get(companion_id)
    if clue.meters["mystery_blocked"] < THRESHOLD:
        return False
    if not _mark(world, "companion_alarm", clue.id, companion.id):
        return False
    companion.memes["alarm"] += 1
    if narrate:
        world.say(f"{companion.label} saw that the diary clue had to stay readable.")
    return True


def _r_adventure_tension(world: World, narrate: bool) -> bool:
    hero = world.get("hero")
    companion_id = world.facts.get("companion")
    if not isinstance(companion_id, str):
        return False
    companion = world.get(companion_id)
    if hero.memes["urgency"] < THRESHOLD or hero.meters["paused"] < THRESHOLD:
        return False
    if not _mark(world, "adventure_tension", hero.id, companion.id):
        return False
    hero.memes["impatience"] += 1
    companion.memes["steadying"] += 1
    if narrate:
        world.say(f"{hero.label} stopped, but the roar of the loud river made waiting feel hard.")
    return True


CAUSAL_RULES = [
    Rule("clue_damage", _r_clue_damage),
    Rule("companion_alarm", _r_companion_alarm),
    Rule("adventure_tension", _r_adventure_tension),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


PLACES = {
    "mill_bridge": RiverPlace(
        "mill_bridge",
        "the old mill bridge",
        "the loud river under the old mill bridge",
        {"read_spray", "follow_echo"},
        "The boards shook each time the water slapped the stones.",
        {"river", "bridge", "adventure"},
    ),
    "pine_bank": RiverPlace(
        "pine_bank",
        "the pine bank",
        "the loud river beside the pine bank",
        {"follow_echo", "lift_stone"},
        "Mist moved through the pine needles like breath.",
        {"river", "forest", "mystery"},
    ),
    "ferry_rocks": RiverPlace(
        "ferry_rocks",
        "the ferry rocks",
        "the loud river by the ferry rocks",
        {"read_spray", "lift_stone"},
        "The old ferry rope hummed whenever the current pulled it tight.",
        {"river", "rocks", "diary"},
    ),
}


MOVES = {
    "read_spray": SearchMove(
        "read_spray",
        "read the diary beside the spray",
        "wanted to open the diary right beside the spray",
        "opening the diary beside the spray",
        "soak",
        {"page", "bank"},
        "soak the clue before the ink can be compared",
        {"diary", "water", "ink"},
    ),
    "follow_echo": SearchMove(
        "follow_echo",
        "run after the echo trail",
        "wanted to run after the echo before it faded",
        "running after the echo trail",
        "scatter",
        {"bank", "path"},
        "scatter the loose clue into the grass",
        {"echo", "river", "haste"},
    ),
    "lift_stone": SearchMove(
        "lift_stone",
        "pry up the marker stone",
        "wanted to pry up the marker stone at once",
        "prying up the marker stone",
        "tear",
        {"pocket", "stone"},
        "tear the folded clue hidden under the edge",
        {"stone", "diary", "clue"},
    ),
}


CLUES = {
    "ink_map": DiaryClue(
        "ink_map",
        "ink map",
        "blue ink map in the diary",
        "page",
        {"soak"},
        "The ink map matched the bend where the missing canoe had been tied.",
        "where the missing canoe went",
        {"diary", "map", "ink"},
    ),
    "loose_note": DiaryClue(
        "loose_note",
        "loose note",
        "loose note tucked in the diary",
        "bank",
        {"soak", "scatter"},
        "The loose note named the hollow pine as the hiding place for the key.",
        "where the ferry key was hidden",
        {"diary", "note", "key"},
    ),
    "pressed_leaf": DiaryClue(
        "pressed_leaf",
        "pressed leaf",
        "pressed leaf inside the diary",
        "pocket",
        {"tear"},
        "The pressed leaf matched the tree beside the safe stepping stones.",
        "which crossing was safe",
        {"diary", "leaf", "crossing"},
    ),
    "chalk_arrow": DiaryClue(
        "chalk_arrow",
        "chalk arrow",
        "chalk arrow copied into the diary",
        "path",
        {"scatter"},
        "The chalk arrow pointed to a quiet path above the flood line.",
        "which path avoided the flood",
        {"diary", "path", "arrow"},
    ),
}


KITS = {
    "oilcloth": Kit(
        "oilcloth",
        "oilcloth cover",
        {"page", "bank"},
        {"soak"},
        "Slide the diary under the oilcloth before reading",
        "slid the diary under the oilcloth before reading",
        {"diary", "water", "care"},
    ),
    "brass_clip": Kit(
        "brass_clip",
        "brass clip",
        {"bank", "path"},
        {"scatter"},
        "Clip the loose pages before chasing the clue",
        "clipped the loose pages before chasing the clue",
        {"diary", "wind", "evidence"},
    ),
    "thin_spade": Kit(
        "thin_spade",
        "thin spade",
        {"pocket", "stone"},
        {"tear"},
        "Use the thin spade instead of pulling by hand",
        "used the thin spade instead of pulling by hand",
        {"stone", "tool", "care"},
    ),
}


METHODS = {
    "oilcloth": "sliding the diary under the oilcloth before reading",
    "brass_clip": "clipping the loose pages before chasing the clue",
    "thin_spade": "lifting the stone with the thin spade instead of pulling by hand",
}


NAMES = {
    "girl": ["Mira", "Tess", "Nell", "Ada"],
    "boy": ["Leo", "Finn", "Owen", "Sam"],
    "child": ["Riley", "Ari", "Quinn", "Rowan"],
}
COMPANIONS = ["Grandpa", "Aunt Jo", "Milo", "Nora"]
TRAITS = ["bold", "careful", "restless", "curious"]
GENDERS = ["girl", "boy", "child"]


def at_risk(move: SearchMove, clue: DiaryClue) -> bool:
    return clue.zone in move.zones and move.risk in clue.vulnerable


def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def choose_kit(move: SearchMove, clue: DiaryClue) -> Optional[Kit]:
    for kit in KITS.values():
        if clue.zone in kit.covers and move.risk in kit.guards:
            return kit
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES.values():
        for move in MOVES.values():
            if move.id not in place.affords:
                continue
            for clue in CLUES.values():
                if not at_risk(move, clue):
                    continue
                if choose_kit(move, clue) is None:
                    continue
                for gender in GENDERS:
                    combos.append((place.id, move.id, clue.id, gender))
    return sorted(combos)


def explain_rejection(place_id: str, move_id: str, clue_id: str, gender: str) -> str:
    if place_id not in PLACES:
        return f"Unknown river place {place_id!r}."
    if move_id not in MOVES:
        return f"Unknown search move {move_id!r}."
    if clue_id not in CLUES:
        return f"Unknown diary clue {clue_id!r}."
    if gender not in GENDERS:
        return f"Unknown gender {gender!r}."
    place = PLACES[place_id]
    move = MOVES[move_id]
    clue = CLUES[clue_id]
    if move.id not in place.affords:
        return f"{place.label} does not plausibly support {move.label}."
    if not at_risk(move, clue):
        return f"{move.label} would not honestly endanger the {clue.label}."
    if choose_kit(move, clue) is None:
        return f"No kit protects the {clue.label} from {move.risk}."
    return "The requested river diary mystery is not in the valid set."


def introduce(world: World, place: RiverPlace, hero: Entity, companion: Entity, clue_cfg: DiaryClue) -> Entity:
    clue = world.add(
        Entity(
            clue_cfg.id,
            "clue",
            clue_cfg.label,
            zone=clue_cfg.zone,
            guards=set(clue_cfg.vulnerable),
        )
    )
    world.say(f"At sunrise, {hero.label}, a {world.params.trait} adventurer, reached {place.scene}.")
    world.say(f"{companion.label} carried the rope, and {hero.label} carried the old diary.")
    world.say(place.opening)
    world.say(f"Inside the diary was a mystery about {clue_cfg.mystery}.")
    hero.memes["curiosity"] += 1
    companion.memes["trust"] += 1
    world.facts["hero"] = hero.id
    world.facts["companion"] = companion.id
    world.facts["clue"] = clue.id
    return clue


def want_search(world: World, hero: Entity, move: SearchMove) -> None:
    world.break_para()
    world.say(f"{hero.label} {move.want}.")
    world.say(f"The loud river made every second feel like the clue might vanish.")
    hero.memes["urgency"] += 1
    hero.memes["resolve"] += 1


def risky_probe(world: World, move: SearchMove, clue: Entity) -> None:
    world.active_move = move.id
    world.active_clue = clue.id
    hero = world.get("hero")
    hero.meters[move.risk] += 1
    propagate(world, narrate=False)


def predict_damage(world: World, move: SearchMove, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    risky_probe(sim, MOVES[move.id], sim.get(clue.id))
    sim_clue = sim.get(clue.id)
    return {
        "risk": move.risk,
        "damaged": sim_clue.meters["damaged"] >= THRESHOLD,
        "warning": move.warning,
        "fired": list(sim.fired_names),
    }


def warn(world: World, hero: Entity, companion: Entity, move: SearchMove, clue: Entity) -> None:
    prediction = predict_damage(world, move, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {companion.label}. "If you try {move.gerund} now, '
        f'you may {prediction["warning"]}. A mystery is easier when the evidence stays whole."'
    )
    companion.memes["caution"] += 1


def pause(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} held the diary against {hero.pronoun('possessive')} jacket.")
    world.say(f'"But the answer is right here," {hero.pronoun("subject")} said.')
    hero.meters["paused"] += 1
    propagate(world, narrate=True)


def use_kit(world: World, hero: Entity, companion: Entity, move: SearchMove, clue: Entity) -> Kit:
    clue_cfg = CLUES[clue.id]
    kit = choose_kit(move, clue_cfg)
    if kit is None:
        raise StoryError("No kit can protect this clue.")
    world.break_para()
    world.add(
        Entity(
            kit.id,
            "kit",
            kit.label,
            covers=set(kit.covers),
            guards=set(kit.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{companion.label} opened the field kit and chose the {kit.label}.")
    world.say(f'"{kit.advice}," {companion.label} said.')
    world.say(f"So {hero.label} {kit.action}.")
    hero.memes["patience"] += 1
    companion.memes["relief"] += 1
    world.facts["kit"] = kit.id
    return kit


def solve_mystery(world: World, hero: Entity, companion: Entity, clue: Entity) -> None:
    clue_cfg = CLUES[clue.id]
    world.say(clue_cfg.answer)
    world.say(f"{hero.label} solved the mystery of {clue_cfg.mystery}.")
    world.say(f"The loud river kept roaring, but now it sounded like a cheer.")
    hero.memes["triumph"] += 1
    companion.memes["pride"] += 1
    clue.memes["meaning"] += 1


def tell(world: World) -> str:
    params = world.params
    place = PLACES[params.place]
    move = MOVES[params.move]
    clue_cfg = CLUES[params.clue]
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    companion = world.add(Entity("companion", "character", params.companion))
    clue = introduce(world, place, hero, companion, clue_cfg)
    want_search(world, hero, move)
    warn(world, hero, companion, move, clue)
    pause(world, hero)
    use_kit(world, hero, companion, move, clue)
    solve_mystery(world, hero, companion, clue)
    return world.render()


@dataclass(frozen=True)
class StoryParams:
    place: str
    move: str
    clue: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("mill_bridge", "read_spray", "ink_map", "Mira", "girl", "Grandpa", "curious", 161),
    StoryParams("pine_bank", "follow_echo", "chalk_arrow", "Leo", "boy", "Aunt Jo", "bold", 162),
    StoryParams("ferry_rocks", "lift_stone", "pressed_leaf", "Riley", "child", "Milo", "careful", 163),
    StoryParams("mill_bridge", "follow_echo", "loose_note", "Ada", "girl", "Nora", "restless", 164),
]


def generation_prompts(params: StoryParams) -> list[str]:
    clue = CLUES[params.clue]
    return [
        'Write an adventure mystery that includes "loud river" and "diary".',
        f"Write a story where {params.name} protects {article(clue.label)} {clue.label} while solving a mystery.",
        "Write a mystery-to-solve story where careful evidence handling matters.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    move = MOVES[params.move]
    clue = CLUES[params.clue]
    kit = KITS[str(world.facts["kit"])]
    method = METHODS[kit.id]
    companion = params.companion
    return [
        QAItem(
            f"Why did {companion} stop {params.name}?",
            f"{companion} stopped {params.name} because {move.gerund} could {move.warning}. "
            "That consequence was predicted before the diary clue was actually damaged.",
        ),
        QAItem(
            f"How did {params.name} keep the diary clue safe?",
            f"{params.name} used the {kit.label} by {method}. "
            f"That protected the {clue.label} long enough to solve the mystery.",
        ),
        QAItem(
            "What mystery was solved?",
            f"The mystery was {clue.mystery}. {clue.answer}",
        ),
    ]


KNOWLEDGE = {
    "diary": QAItem(
        "Why can a diary be useful in a mystery?",
        "A diary can hold dates, maps, sketches, or private notes. Those details can become evidence when someone reads them carefully.",
    ),
    "river": QAItem(
        "Why is it hard to hear near a loud river?",
        "Fast water makes steady noise as it hits rocks and banks. That sound can cover footsteps, voices, or other clues.",
    ),
    "ink": QAItem(
        "Why should ink be kept dry?",
        "Many inks blur when they get wet. Keeping a page dry helps words and maps stay readable.",
    ),
    "water": QAItem(
        "Why should paper stay away from spray?",
        "Paper can wrinkle or tear when it gets wet. A cover gives the page time to be read safely.",
    ),
    "wind": QAItem(
        "Why clip loose pages outside?",
        "Wind and running can scatter loose pages. A clip keeps the evidence together.",
    ),
    "stone": QAItem(
        "Why use a tool under a stone?",
        "A thin tool can lift an edge evenly. Pulling by hand may tear something fragile.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    move = MOVES[params.move]
    clue = CLUES[params.clue]
    kit = KITS[choose_kit(move, clue).id]  # type: ignore[union-attr]
    tags = set().union(move.tags, clue.tags, kit.tags, {"diary", "river"})
    return [item for key, item in KNOWLEDGE.items() if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    combo = (params.place, params.move, params.clue, params.gender)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.move, params.clue, params.gender))
    world = World(params)
    story = tell(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(params),
        story_qa=story_qa(params, world),
        world_qa=world_qa(params),
        world=world,
    )


ASP_RULES = r"""
at_risk(M,C) :- move_zone(M,Z), clue_zone(C,Z), risk(M,R), vulnerable(C,R).
effective(M,C,K) :- at_risk(M,C), clue_zone(C,Z), risk(M,R), covers(K,Z), guards(K,R).
valid(P,M,C,G) :- place(P), affords(P,M), clue(C), gender(G), effective(M,C,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for place in PLACES.values():
        facts.append(asp.fact("place", place.id))
        for move_id in place.affords:
            facts.append(asp.fact("affords", place.id, move_id))
    for move in MOVES.values():
        facts.append(asp.fact("move", move.id))
        facts.append(asp.fact("risk", move.id, move.risk))
        for zone in move.zones:
            facts.append(asp.fact("move_zone", move.id, zone))
    for clue in CLUES.values():
        facts.append(asp.fact("clue", clue.id))
        facts.append(asp.fact("clue_zone", clue.id, clue.zone))
        for risk in clue.vulnerable:
            facts.append(asp.fact("vulnerable", clue.id, risk))
    for kit in KITS.values():
        facts.append(asp.fact("kit", kit.id))
        for zone in kit.covers:
            facts.append(asp.fact("covers", kit.id, zone))
        for risk in kit.guards:
            facts.append(asp.fact("guards", kit.id, risk))
    for gender in GENDERS:
        facts.append(asp.fact("gender", gender))
    return "\n".join(facts) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    combos: set[tuple[str, str, str, str]] = set()
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
    print(f"OK: Python and ASP agree on {len(py)} valid loud-river diary mysteries.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--move", choices=sorted(MOVES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--name")
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--trait", choices=TRAITS)
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


def resolve_params(args, rng: random.Random) -> StoryParams:
    choices = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.move is None or combo[1] == args.move)
        and (args.clue is None or combo[2] == args.clue)
        and (args.gender is None or combo[3] == args.gender)
    ]
    if not choices:
        place = args.place or sorted(PLACES)[0]
        move = args.move or sorted(MOVES)[0]
        clue = args.clue or sorted(CLUES)[0]
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, move, clue, gender))
    place, move, clue, gender = rng.choice(choices)
    name = args.name or rng.choice(NAMES[gender])
    companion = args.companion or rng.choice(COMPANIONS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, move, clue, name, gender, companion, trait, args.seed)


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


def samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    target = max(1, args.n)
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    attempts = 0
    while len(samples) < target and attempts < target * 20:
        seed = base_seed + i
        i += 1
        attempts += 1
        local_args = copy.copy(args)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for idx, sample in enumerate(samples, 1):
        header = ""
        if len(samples) > 1:
            header = f"=== loud_river_diary_mystery #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
