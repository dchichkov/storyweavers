#!/usr/bin/env python3
"""A fable storyworld about a loud sign, a bench, and a twinkling ship.

Seed:
    Words: loud sign, bench, twinkling ship
    Features: Misunderstanding
    Style: Fable

A small animal misunderstands a loud sign near a bench and a twinkling ship.
Trying to fix the mistake too quickly would spoil the clue, so an elder predicts
the consequence on a copied world. A careful response preserves the physical clue
and lets the moral emerge from the corrected state.
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
class FablePlace:
    id: str
    label: str
    scene: str
    affords: set[str]
    omen: str
    tags: set[str]


@dataclass(frozen=True)
class MistakeMove:
    id: str
    label: str
    belief: str
    urge: str
    gerund: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class LessonClue:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    truth: str
    moral_piece: str
    tags: set[str]


@dataclass(frozen=True)
class CarefulAct:
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
    meters: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: defaultdict[str, float] = field(default_factory=lambda: defaultdict(float))
    zone: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False


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

    def protected(self, clue: Entity, risk: str) -> bool:
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


def _r_clue_spoiled(world: World, narrate: bool) -> bool:
    if not world.active_move or not world.active_clue:
        return False
    move = MOVES[world.active_move]
    actor = world.get("hero")
    clue = world.get(world.active_clue)
    if actor.meters[move.risk] < THRESHOLD:
        return False
    if clue.zone not in move.zones or move.risk not in clue.guards:
        return False
    if world.protected(clue, move.risk):
        return False
    if not _mark(world, "clue_spoiled", actor.id, clue.id, move.risk):
        return False
    clue.meters["spoiled"] += 1
    clue.meters["truth_hidden"] += 1
    if narrate:
        world.say(f"The {clue.label} was spoiled, and the misunderstanding grew twice as tall.")
    return True


def _r_elder_concern(world: World, narrate: bool) -> bool:
    elder_id = world.facts.get("elder")
    clue_id = world.active_clue
    if not isinstance(elder_id, str) or not isinstance(clue_id, str):
        return False
    elder = world.get(elder_id)
    clue = world.get(clue_id)
    if clue.meters["truth_hidden"] < THRESHOLD:
        return False
    if not _mark(world, "elder_concern", elder.id, clue.id):
        return False
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"{elder.label} saw that the fable would lose its lesson if the clue vanished.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero = world.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(elder_id, str):
        return False
    elder = world.get(elder_id)
    if hero.memes["mistaken"] < THRESHOLD or hero.meters["paused"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["embarrassment"] += 1
    elder.memes["patience"] += 1
    if narrate:
        move_id = world.facts.get("move")
        if move_id == "chase_ship":
            reason = "the twinkling ship was escaping with the answer"
        elif move_id == "shout_answer":
            reason = "the bench needed a loud defender"
        else:
            reason = "the loud sign had insulted someone"
        world.say(f"{hero.label} paused by the bench, still sure {reason}.")
    return True


CAUSAL_RULES = [
    Rule("clue_spoiled", _r_clue_spoiled),
    Rule("elder_concern", _r_elder_concern),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


PLACES = {
    "pond_bench": FablePlace(
        "pond_bench",
        "the pond bench",
        "a bench beside a pond where a twinkling ship bobbed",
        {"pull_sign", "chase_ship"},
        "Beside the bench stood a loud sign painted in very large letters.",
        {"bench", "pond", "ship"},
    ),
    "market_bench": FablePlace(
        "market_bench",
        "the market bench",
        "a bench at the market fountain where a twinkling ship turned in circles",
        {"shout_answer", "pull_sign"},
        "The loud sign clacked whenever the fountain breeze pushed it.",
        {"bench", "market", "sign"},
    ),
    "harbor_bench": FablePlace(
        "harbor_bench",
        "the harbor bench",
        "a bench near the toy harbor where a twinkling ship flashed blue and gold",
        {"chase_ship", "shout_answer"},
        "The loud sign seemed to point at everyone and no one.",
        {"bench", "harbor", "ship"},
    ),
}


MOVES = {
    "pull_sign": MistakeMove(
        "pull_sign",
        "pull down the loud sign",
        "the loud sign was bossing the bench and must be removed",
        "wanted to pull down the loud sign before it shouted again",
        "pulling down the loud sign",
        "topple",
        {"signpost", "bench"},
        "topple the sign before its small arrow can be read",
        {"sign", "bench", "misunderstanding"},
    ),
    "chase_ship": MistakeMove(
        "chase_ship",
        "chase the twinkling ship",
        "the twinkling ship was sailing away with the answer",
        "wanted to chase the twinkling ship across the water",
        "chasing the twinkling ship",
        "splash",
        {"water", "ship"},
        "splash over the clue painted on the tiny sail",
        {"ship", "water", "haste"},
    ),
    "shout_answer": MistakeMove(
        "shout_answer",
        "shout from the bench",
        "the bench was being blamed and needed a defender",
        "wanted to shout the answer from the bench",
        "shouting from the bench",
        "startle",
        {"bench", "ship"},
        "startle the quiet clue before it can be read",
        {"bench", "voice", "conflict"},
    ),
}


CLUES = {
    "arrow_mark": LessonClue(
        "arrow_mark",
        "arrow mark",
        "small arrow mark under the loud sign",
        "signpost",
        {"topple"},
        "The arrow showed that the sign meant, 'Wait for your turn on the bench.'",
        "look twice before judging a loud sign",
        {"sign", "arrow", "lesson"},
    ),
    "sail_word": LessonClue(
        "sail_word",
        "sail word",
        "silver word on the twinkling ship's sail",
        "ship",
        {"splash", "startle"},
        "The sail word was 'share,' not 'shoo.'",
        "listen before deciding someone is rude",
        {"ship", "word", "share"},
    ),
    "bench_note": LessonClue(
        "bench_note",
        "bench note",
        "folded note tucked under the bench",
        "bench",
        {"topple", "startle"},
        "The bench note asked friends to sit two at a time, not to send anyone away.",
        "ask before defending the wrong side",
        {"bench", "note", "friendship"},
    ),
    "ripple_star": LessonClue(
        "ripple_star",
        "ripple star",
        "twinkling star reflected beside the ship",
        "water",
        {"splash"},
        "The ripple star pointed to the quiet side of the pond, where the words were easy to read.",
        "calm water makes truth clearer",
        {"water", "star", "calm"},
    ),
}


ACTS = {
    "read_twice": CarefulAct(
        "read_twice",
        "read-twice pause",
        {"signpost", "bench"},
        {"topple"},
        "Read the loud sign twice before touching it",
        "read the loud sign twice before touching it",
        {"sign", "patience", "bench"},
    ),
    "quiet_cup": CarefulAct(
        "quiet_cup",
        "quiet cup",
        {"bench", "ship"},
        {"startle"},
        "Cup your paws and speak softly",
        "cupped both paws and spoke softly",
        {"voice", "ship", "gentle"},
    ),
    "leaf_paddle": CarefulAct(
        "leaf_paddle",
        "leaf paddle",
        {"water", "ship"},
        {"splash"},
        "Guide the ship with a leaf instead of chasing it",
        "guided the ship with a leaf instead of chasing it",
        {"ship", "leaf", "care"},
    ),
}


METHODS = {
    "read_twice": "reading the loud sign twice before touching it",
    "quiet_cup": "cupping both paws and speaking softly",
    "leaf_paddle": "guiding the ship with a leaf instead of chasing it",
}


ANIMALS = ["Fox", "Hare", "Mouse", "Badger", "Squirrel"]
ELDERS = ["Turtle", "Owl", "Goat", "Heron"]
TRAITS = ["quick", "proud", "kind", "fussy"]


def at_risk(move: MistakeMove, clue: LessonClue) -> bool:
    return clue.zone in move.zones and move.risk in clue.vulnerable


def choose_act(move: MistakeMove, clue: LessonClue) -> Optional[CarefulAct]:
    for act in ACTS.values():
        if clue.zone in act.covers and move.risk in act.guards:
            return act
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
                if choose_act(move, clue) is None:
                    continue
                for animal in ANIMALS:
                    combos.append((place.id, move.id, clue.id, animal))
    return sorted(combos)


def explain_rejection(place_id: str, move_id: str, clue_id: str, animal: str) -> str:
    if place_id not in PLACES:
        return f"Unknown fable place {place_id!r}."
    if move_id not in MOVES:
        return f"Unknown mistake move {move_id!r}."
    if clue_id not in CLUES:
        return f"Unknown lesson clue {clue_id!r}."
    if animal not in ANIMALS:
        return f"Unknown animal {animal!r}."
    place = PLACES[place_id]
    move = MOVES[move_id]
    clue = CLUES[clue_id]
    if move.id not in place.affords:
        return f"{place.label} does not plausibly support {move.label}."
    if not at_risk(move, clue):
        return f"{move.label} would not honestly spoil the {clue.label}."
    if choose_act(move, clue) is None:
        return f"No careful act protects the {clue.label} from {move.risk}."
    return "The requested loud-sign fable is not in the valid set."


def introduce(world: World, place: FablePlace, hero: Entity, elder: Entity, clue_cfg: LessonClue) -> Entity:
    clue = world.add(
        Entity(
            clue_cfg.id,
            "clue",
            clue_cfg.label,
            zone=clue_cfg.zone,
            guards=set(clue_cfg.vulnerable),
        )
    )
    world.add(Entity("bench", "object", "bench", zone="bench"))
    world.add(Entity("sign", "object", "loud sign", zone="signpost"))
    world.add(Entity("ship", "object", "twinkling ship", zone="ship"))
    world.say(f"Once, {hero.label}, a {world.params.trait} animal, came to {place.scene}.")
    world.say(place.omen)
    world.say(f"{elder.label} sat nearby, polishing an acorn and saying nothing yet.")
    world.say(f"The hidden lesson rested in the {clue_cfg.full_label}.")
    hero.memes["curiosity"] += 1
    elder.memes["watchfulness"] += 1
    world.facts["hero"] = hero.id
    world.facts["elder"] = elder.id
    world.facts["clue"] = clue.id
    return clue


def misunderstand(world: World, hero: Entity, move: MistakeMove) -> None:
    world.break_para()
    world.say(f"{hero.label} decided that {move.belief}.")
    world.say(f"So {hero.label} {move.urge}.")
    world.facts["move"] = move.id
    hero.memes["mistaken"] += 1
    hero.memes["certainty"] += 1


def risky_try(world: World, move: MistakeMove, clue: Entity) -> None:
    world.active_move = move.id
    world.active_clue = clue.id
    hero = world.get("hero")
    hero.meters[move.risk] += 1
    propagate(world, narrate=False)


def predict_spoil(world: World, move: MistakeMove, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    risky_try(sim, MOVES[move.id], sim.get(clue.id))
    sim_clue = sim.get(clue.id)
    return {
        "risk": move.risk,
        "spoiled": sim_clue.meters["spoiled"] >= THRESHOLD,
        "warning": move.warning,
        "fired": list(sim.fired_names),
    }


def warn(world: World, hero: Entity, elder: Entity, move: MistakeMove, clue: Entity) -> None:
    prediction = predict_spoil(world, move, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you try {move.gerund}, you may '
        f'{prediction["warning"]}. A loud sign is not always an angry sign."'
    )
    elder.memes["caution"] += 1


def conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} bristled from whisker to tail.")
    world.say('"Then why is it so loud?" asked the small animal.')
    hero.meters["paused"] += 1
    propagate(world, narrate=True)


def careful_act(world: World, hero: Entity, elder: Entity, move: MistakeMove, clue: Entity) -> CarefulAct:
    clue_cfg = CLUES[clue.id]
    act = choose_act(move, clue_cfg)
    if act is None:
        raise StoryError("No careful act can preserve this fable clue.")
    world.break_para()
    world.add(
        Entity(
            act.id,
            "careful_act",
            act.label,
            covers=set(act.covers),
            guards=set(act.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{elder.label} tapped the bench with one patient claw.")
    world.say(f'"{act.advice}," said {elder.label}.')
    world.say(f"So {hero.label} {act.action}.")
    hero.memes["humility"] += 1
    elder.memes["relief"] += 1
    world.facts["act"] = act.id
    return act


def reveal(world: World, hero: Entity, elder: Entity, clue: Entity) -> None:
    clue_cfg = CLUES[clue.id]
    world.say(clue_cfg.truth)
    world.say(f"{hero.label} understood the misunderstanding at last.")
    world.say(f"The moral was simple: {clue_cfg.moral_piece}.")
    clue.memes["meaning"] += 1
    hero.memes["lesson"] += 1
    elder.memes["satisfaction"] += 1


def tell(world: World) -> str:
    params = world.params
    place = PLACES[params.place]
    move = MOVES[params.move]
    clue_cfg = CLUES[params.clue]
    hero = world.add(Entity("hero", "animal", params.animal))
    elder = world.add(Entity("elder", "animal", params.elder))
    clue = introduce(world, place, hero, elder, clue_cfg)
    misunderstand(world, hero, move)
    warn(world, hero, elder, move, clue)
    conflict(world, hero)
    careful_act(world, hero, elder, move, clue)
    reveal(world, hero, elder, clue)
    return world.render()


@dataclass(frozen=True)
class StoryParams:
    place: str
    move: str
    clue: str
    animal: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("pond_bench", "pull_sign", "arrow_mark", "Fox", "Turtle", "quick", 191),
    StoryParams("harbor_bench", "chase_ship", "sail_word", "Hare", "Owl", "proud", 192),
    StoryParams("market_bench", "shout_answer", "bench_note", "Mouse", "Goat", "kind", 193),
    StoryParams("pond_bench", "chase_ship", "ripple_star", "Badger", "Heron", "fussy", 194),
]


def generation_prompts(params: StoryParams) -> list[str]:
    return [
        'Write a fable that includes "loud sign", "bench", and "twinkling ship".',
        f"Write a misunderstanding story where {params.animal} learns from {params.elder}.",
        "Write a fable where a loud-looking sign is understood only after the clue is protected.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    move = MOVES[params.move]
    clue = CLUES[params.clue]
    act = ACTS[str(world.facts["act"])]
    return [
        QAItem(
            f"What did {params.animal} misunderstand?",
            f"{params.animal} thought that {move.belief}. The truth was different because the {clue.label} had not been read carefully yet.",
        ),
        QAItem(
            f"Why did {params.elder} stop {params.animal}?",
            f"{params.elder} stopped {params.animal} because {move.gerund} could {move.warning}. "
            "That consequence was predicted before the clue was actually spoiled.",
        ),
        QAItem(
            "What lesson did the fable teach?",
            f"The fable taught this lesson: {clue.moral_piece}. "
            f"{params.animal} learned it by {METHODS[act.id]}.",
        ),
    ]


KNOWLEDGE = {
    "sign": QAItem(
        "Why should signs be read carefully?",
        "Signs can be short, loud-looking, or easy to misunderstand. Reading twice helps reveal what they actually mean.",
    ),
    "bench": QAItem(
        "What is a bench for?",
        "A bench is a shared place to sit and rest. People and animals may need to take turns using it.",
    ),
    "ship": QAItem(
        "Why can a toy ship carry a clue?",
        "A toy ship can have writing, marks, or a tiny sail. If it is splashed away, the clue may be lost.",
    ),
    "misunderstanding": QAItem(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone guesses the wrong meaning. Asking and checking can fix it.",
    ),
    "water": QAItem(
        "Why does calm water help reading?",
        "Calm water makes reflections and floating objects easier to see. Splashing can hide small marks.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    move = MOVES[params.move]
    clue = CLUES[params.clue]
    act = ACTS[choose_act(move, clue).id]  # type: ignore[union-attr]
    tags = set().union(move.tags, clue.tags, act.tags, {"misunderstanding", "sign", "bench", "ship"})
    return [item for key, item in KNOWLEDGE.items() if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    combo = (params.place, params.move, params.clue, params.animal)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, params.move, params.clue, params.animal))
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
effective(M,C,A) :- at_risk(M,C), clue_zone(C,Z), risk(M,R), covers(A,Z), guards(A,R).
valid(P,M,C,Ani) :- place(P), affords(P,M), clue(C), animal(Ani), effective(M,C,_).
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
    for act in ACTS.values():
        facts.append(asp.fact("act", act.id))
        for zone in act.covers:
            facts.append(asp.fact("covers", act.id, zone))
        for risk in act.guards:
            facts.append(asp.fact("guards", act.id, risk))
    for animal in ANIMALS:
        facts.append(asp.fact("animal", animal))
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
    print(f"OK: Python and ASP agree on {len(py)} valid loud-sign fables.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--move", choices=sorted(MOVES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--animal", choices=ANIMALS)
    parser.add_argument("--elder", choices=ELDERS)
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
        and (args.animal is None or combo[3] == args.animal)
    ]
    if not choices:
        place = args.place or sorted(PLACES)[0]
        move = args.move or sorted(MOVES)[0]
        clue = args.clue or sorted(CLUES)[0]
        animal = args.animal or ANIMALS[0]
        raise StoryError(explain_rejection(place, move, clue, animal))
    place, move, clue, animal = rng.choice(choices)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, move, clue, animal, elder, trait, args.seed)


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
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
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
            header = f"=== loud_sign_bench_fable #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
