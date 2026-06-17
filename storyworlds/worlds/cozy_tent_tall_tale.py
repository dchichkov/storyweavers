#!/usr/bin/env python3
"""A tall-tale storyworld about teamwork in a cozy tent.

Seed:
    Words: cozy tent
    Features: Suspense, Teamwork, Humor
    Style: Tall Tale

The cozy tent seems to hide an enormous mystery. A rash move would ruin the
evidence or the tent, so a teammate predicts the consequence on a copied world
and the group uses a coordinated plan to reveal a harmless, funny cause.
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
class Camp:
    id: str
    label: str
    scene: str
    affords: set[str]
    omen: str
    tags: set[str]


@dataclass(frozen=True)
class ScareMove:
    id: str
    label: str
    urge: str
    gerund: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class TentClue:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    reveal: str
    mystery: str
    tags: set[str]


@dataclass(frozen=True)
class TeamPlan:
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

    def protected(self, clue: Entity, risk: str) -> bool:
        for ent in self.entities.values():
            if not ent.protective or ent.used_on != clue.id:
                continue
            if clue.zone in ent.covers and risk in ent.guards:
                return True
        return False

    def trace(self) -> str:
        lines = [
            f"camp: {self.params.camp}",
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
    hero = world.get("hero")
    clue = world.get(world.active_clue)
    if hero.meters[move.risk] < THRESHOLD:
        return False
    if clue.zone not in move.zones or move.risk not in clue.guards:
        return False
    if world.protected(clue, move.risk):
        return False
    if not _mark(world, "clue_spoiled", hero.id, clue.id, move.risk):
        return False
    clue.meters["spoiled"] += 1
    clue.meters["mystery_muddled"] += 1
    if narrate:
        world.say(f"The {clue.label} got muddled before anyone could learn what was really in the tent.")
    return True


def _r_teammate_worry(world: World, narrate: bool) -> bool:
    clue_id = world.active_clue
    teammate_id = world.facts.get("teammate")
    if not isinstance(clue_id, str) or not isinstance(teammate_id, str):
        return False
    clue = world.get(clue_id)
    teammate = world.get(teammate_id)
    if clue.meters["mystery_muddled"] < THRESHOLD:
        return False
    if not _mark(world, "teammate_worry", clue.id, teammate.id):
        return False
    teammate.memes["worry"] += 1
    if narrate:
        world.say(f"{teammate.label} knew the suspense needed a careful ending, not a squashed clue.")
    return True


def _r_suspense_squeeze(world: World, narrate: bool) -> bool:
    hero = world.get("hero")
    teammate_id = world.facts.get("teammate")
    if not isinstance(teammate_id, str):
        return False
    teammate = world.get(teammate_id)
    if hero.memes["bravado"] < THRESHOLD or hero.meters["paused"] < THRESHOLD:
        return False
    if not _mark(world, "suspense_squeeze", hero.id, teammate.id):
        return False
    hero.memes["jitters"] += 1
    teammate.memes["steady"] += 1
    if narrate:
        world.say(f"{hero.label} froze in front of the cozy tent, trying to look brave enough for three giants.")
    return True


CAUSAL_RULES = [
    Rule("clue_spoiled", _r_clue_spoiled),
    Rule("teammate_worry", _r_teammate_worry),
    Rule("suspense_squeeze", _r_suspense_squeeze),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


CAMPS = {
    "backyard": Camp(
        "backyard",
        "the backyard camp",
        "a cozy tent pitched between two tomato cages",
        {"yank_flap", "poke_shadow"},
        "The tent wall puffed out as if it had swallowed a bear with hiccups.",
        {"tent", "backyard", "humor"},
    ),
    "meadow": Camp(
        "meadow",
        "the moonlit meadow",
        "a cozy tent glowing beside the tall grass",
        {"listen_rumble", "poke_shadow"},
        "The grass bent away from the tent like it had heard a secret.",
        {"tent", "meadow", "suspense"},
    ),
    "creek": Camp(
        "creek",
        "the creekside camp",
        "a cozy tent beside a creek that gurgled like soup",
        {"yank_flap", "listen_rumble"},
        "Something inside the tent made a noise like a dragon clearing its tiny throat.",
        {"tent", "creek", "tall_tale"},
    ),
}


MOVES = {
    "yank_flap": ScareMove(
        "yank_flap",
        "yank the tent flap open",
        "wanted to yank the tent flap open before the monster escaped",
        "yanking the tent flap open",
        "rip",
        {"flap", "floor"},
        "rip the clue loose from the tent flap",
        {"tent", "flap", "haste"},
    ),
    "poke_shadow": ScareMove(
        "poke_shadow",
        "poke the giant shadow",
        "wanted to poke the giant shadow with a marshmallow stick",
        "poking the giant shadow",
        "squash",
        {"wall", "corner"},
        "squash the shape before anyone can see what made it",
        {"shadow", "stick", "suspense"},
    ),
    "listen_rumble": ScareMove(
        "listen_rumble",
        "charge at the rumble",
        "wanted to charge at the rumble like a famous tent knight",
        "charging at the rumble",
        "scatter",
        {"floor", "corner"},
        "scatter the tiny tracks across the blanket floor",
        {"rumble", "tracks", "adventure"},
    ),
}


CLUES = {
    "button_print": TentClue(
        "button_print",
        "button print",
        "round button print on the flap",
        "flap",
        {"rip"},
        "The button print matched Dad's pajama button, because he had crawled in to hide the snacks.",
        "who was making the flap bump",
        {"button", "flap", "tent"},
    ),
    "moth_shadow": TentClue(
        "moth_shadow",
        "moth shadow",
        "huge moth shadow on the tent wall",
        "wall",
        {"squash"},
        "The giant shadow belonged to one moth, two socks, and a lantern that exaggerated everything.",
        "what made the giant shadow",
        {"moth", "shadow", "lantern"},
    ),
    "crumb_tracks": TentClue(
        "crumb_tracks",
        "crumb tracks",
        "crumb tracks across the tent floor",
        "floor",
        {"rip", "scatter"},
        "The crumb tracks led to a chipmunk wearing a noodle ring like a crown.",
        "what stole the camp snacks",
        {"crumbs", "tracks", "snacks"},
    ),
    "snore_echo": TentClue(
        "snore_echo",
        "snore echo",
        "snore echo in the tent corner",
        "corner",
        {"squash", "scatter"},
        "The snore echo came from a frog sleeping in a tin cup.",
        "what sounded like a pocket-sized dragon",
        {"snore", "frog", "humor"},
    ),
}


PLANS = {
    "two_hand_flap": TeamPlan(
        "two_hand_flap",
        "two-hand flap check",
        {"flap", "floor"},
        {"rip"},
        "We open the flap together, one hand each",
        "opened the flap together, one hand each",
        {"teamwork", "tent", "flap"},
    ),
    "lantern_count": TeamPlan(
        "lantern_count",
        "lantern count",
        {"wall", "corner"},
        {"squash"},
        "Hold the lantern still and count the shadow first",
        "held the lantern still and counted the shadow first",
        {"teamwork", "shadow", "lantern"},
    ),
    "blanket_grid": TeamPlan(
        "blanket_grid",
        "blanket grid",
        {"floor", "corner"},
        {"scatter"},
        "Lift the blanket by corners so the tracks stay put",
        "lifted the blanket by corners so the tracks stayed put",
        {"teamwork", "tracks", "blanket"},
    ),
}


METHODS = {
    "two_hand_flap": "opening the flap together, one hand each",
    "lantern_count": "holding the lantern still and counting the shadow first",
    "blanket_grid": "lifting the blanket by corners so the tracks stayed put",
}


NAMES = {
    "girl": ["Mabel", "Tess", "Nina", "June"],
    "boy": ["Otto", "Finn", "Gus", "Leo"],
    "child": ["Riley", "Ari", "Quinn", "Rowan"],
}
TEAMMATES = ["Pip", "Nora", "Uncle Bo", "Mina"]
TRAITS = ["brave", "sleepy", "dramatic", "curious"]
GENDERS = ["girl", "boy", "child"]


def article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def at_risk(move: ScareMove, clue: TentClue) -> bool:
    return clue.zone in move.zones and move.risk in clue.vulnerable


def choose_plan(move: ScareMove, clue: TentClue) -> Optional[TeamPlan]:
    for plan in PLANS.values():
        if clue.zone in plan.covers and move.risk in plan.guards:
            return plan
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for camp in CAMPS.values():
        for move in MOVES.values():
            if move.id not in camp.affords:
                continue
            for clue in CLUES.values():
                if not at_risk(move, clue):
                    continue
                if choose_plan(move, clue) is None:
                    continue
                for gender in GENDERS:
                    combos.append((camp.id, move.id, clue.id, gender))
    return sorted(combos)


def explain_rejection(camp_id: str, move_id: str, clue_id: str, gender: str) -> str:
    if camp_id not in CAMPS:
        return f"Unknown camp {camp_id!r}."
    if move_id not in MOVES:
        return f"Unknown scare move {move_id!r}."
    if clue_id not in CLUES:
        return f"Unknown tent clue {clue_id!r}."
    if gender not in GENDERS:
        return f"Unknown gender {gender!r}."
    camp = CAMPS[camp_id]
    move = MOVES[move_id]
    clue = CLUES[clue_id]
    if move.id not in camp.affords:
        return f"{camp.label} does not plausibly support {move.label}."
    if not at_risk(move, clue):
        return f"{move.label} would not honestly spoil the {clue.label}."
    if choose_plan(move, clue) is None:
        return f"No team plan protects the {clue.label} from {move.risk}."
    return "The requested cozy tent tall tale is not in the valid set."


def introduce(world: World, camp: Camp, hero: Entity, teammate: Entity, clue_cfg: TentClue) -> Entity:
    tent = world.add(Entity("tent", "place", "cozy tent"))
    clue = world.add(
        Entity(
            clue_cfg.id,
            "clue",
            clue_cfg.label,
            zone=clue_cfg.zone,
            guards=set(clue_cfg.vulnerable),
        )
    )
    world.say(f"One evening, {hero.label} and {teammate.label} guarded {camp.scene}.")
    world.say("It was the coziest tent in the county, or maybe the coziest tent in three counties if you believed Uncle Bo.")
    world.say(camp.omen)
    world.say(f"Their mystery was {clue_cfg.mystery}.")
    tent.memes["cozy"] += 1
    hero.memes["wonder"] += 1
    teammate.memes["team_spirit"] += 1
    world.facts["hero"] = hero.id
    world.facts["teammate"] = teammate.id
    world.facts["clue"] = clue.id
    return clue


def build_suspense(world: World, hero: Entity, move: ScareMove) -> None:
    world.break_para()
    world.say(f"{hero.label} {move.urge}.")
    world.say(f"Outside, the stars leaned closer, probably to see if {hero.pronoun('subject')} would squeak.")
    hero.memes["bravado"] += 1
    hero.memes["suspense"] += 1


def risky_try(world: World, move: ScareMove, clue: Entity) -> None:
    world.active_move = move.id
    world.active_clue = clue.id
    hero = world.get("hero")
    hero.meters[move.risk] += 1
    propagate(world, narrate=False)


def predict_spoil(world: World, move: ScareMove, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    risky_try(sim, MOVES[move.id], sim.get(clue.id))
    sim_clue = sim.get(clue.id)
    return {
        "risk": move.risk,
        "spoiled": sim_clue.meters["spoiled"] >= THRESHOLD,
        "warning": move.warning,
        "fired": list(sim.fired_names),
    }


def warn(world: World, hero: Entity, teammate: Entity, move: ScareMove, clue: Entity) -> None:
    prediction = predict_spoil(world, move, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Hold your heroic horses," said {teammate.label}. "If you try {move.gerund}, '
        f'you may {prediction["warning"]}. Suspense is better when the clue survives."'
    )
    teammate.memes["caution"] += 1


def pause(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} lifted one foot, lowered it, and tried not to gulp too loudly.")
    world.say(f'"Fine," {hero.pronoun("subject")} whispered, "but if it is a bear, I am blaming the marshmallows."')
    hero.meters["paused"] += 1
    propagate(world, narrate=True)


def use_team_plan(world: World, hero: Entity, teammate: Entity, move: ScareMove, clue: Entity) -> TeamPlan:
    clue_cfg = CLUES[clue.id]
    plan = choose_plan(move, clue_cfg)
    if plan is None:
        raise StoryError("No teamwork plan can protect this clue.")
    world.break_para()
    world.add(
        Entity(
            plan.id,
            "team_plan",
            plan.label,
            covers=set(plan.covers),
            guards=set(plan.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{teammate.label} made a plan so serious that even the crickets saluted.")
    world.say(f'"{plan.advice}," {teammate.label} said.')
    world.say(f"So {hero.label} and {teammate.label} {plan.action}.")
    hero.memes["teamwork"] += 1
    teammate.memes["teamwork"] += 1
    world.facts["plan"] = plan.id
    return plan


def reveal(world: World, hero: Entity, teammate: Entity, clue: Entity) -> None:
    clue_cfg = CLUES[clue.id]
    world.say(clue_cfg.reveal)
    world.say(f"{hero.label} and {teammate.label} solved the mystery of {clue_cfg.mystery}.")
    world.say("Then everybody laughed so hard that the cozy tent almost asked for a nap.")
    clue.memes["meaning"] += 1
    hero.memes["relief"] += 1
    teammate.memes["relief"] += 1


def tell(world: World) -> str:
    params = world.params
    camp = CAMPS[params.camp]
    move = MOVES[params.move]
    clue_cfg = CLUES[params.clue]
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    teammate = world.add(Entity("teammate", "character", params.teammate))
    clue = introduce(world, camp, hero, teammate, clue_cfg)
    build_suspense(world, hero, move)
    warn(world, hero, teammate, move, clue)
    pause(world, hero)
    use_team_plan(world, hero, teammate, move, clue)
    reveal(world, hero, teammate, clue)
    return world.render()


@dataclass(frozen=True)
class StoryParams:
    camp: str
    move: str
    clue: str
    name: str
    gender: str
    teammate: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("backyard", "yank_flap", "button_print", "Mabel", "girl", "Uncle Bo", "dramatic", 171),
    StoryParams("meadow", "poke_shadow", "moth_shadow", "Leo", "boy", "Pip", "brave", 172),
    StoryParams("creek", "listen_rumble", "crumb_tracks", "Riley", "child", "Mina", "curious", 173),
    StoryParams("backyard", "poke_shadow", "snore_echo", "Nina", "girl", "Nora", "sleepy", 174),
]


def generation_prompts(params: StoryParams) -> list[str]:
    clue = CLUES[params.clue]
    return [
        'Write a tall tale that includes "cozy tent".',
        f"Write a suspenseful but funny teamwork story where {params.name} protects the {clue.label}.",
        "Write a humorous mystery in a tent where the scary thing turns out harmless.",
    ]


def story_qa(params: StoryParams, world: World) -> list[QAItem]:
    move = MOVES[params.move]
    clue = CLUES[params.clue]
    plan = PLANS[str(world.facts["plan"])]
    return [
        QAItem(
            f"Why did {params.teammate} stop {params.name}?",
            f"{params.teammate} stopped {params.name} because {move.gerund} could {move.warning}. "
            "That danger was predicted before the clue was actually spoiled.",
        ),
        QAItem(
            "How did teamwork solve the problem?",
            f"The team used the {plan.label} by {METHODS[plan.id]}. "
            f"That protected the {clue.label} and let the mystery stay answerable.",
        ),
        QAItem(
            "What was funny about the ending?",
            f"The scary mystery was {clue.mystery}, but the answer was harmless. {clue.reveal}",
        ),
    ]


KNOWLEDGE = {
    "tent": QAItem(
        "Why can a tent make shadows look scary?",
        "Tent fabric turns small things into big shapes when light shines behind them. A sock or moth can look huge on a tent wall.",
    ),
    "teamwork": QAItem(
        "Why does teamwork help with a mystery?",
        "One person can pause while another watches the clue. Working together keeps people from rushing and spoiling evidence.",
    ),
    "shadow": QAItem(
        "What makes shadows change size?",
        "A shadow looks bigger when the object is close to the light. Moving the light or object changes the shape.",
    ),
    "tracks": QAItem(
        "Why are tracks useful clues?",
        "Tracks show where something moved. If they are scattered or stepped on, they become harder to read.",
    ),
    "humor": QAItem(
        "Why can suspense become funny?",
        "Suspense feels serious while nobody knows the answer. It becomes funny when the answer is much smaller than expected.",
    ),
}


def world_qa(params: StoryParams) -> list[QAItem]:
    clue = CLUES[params.clue]
    move = MOVES[params.move]
    plan = PLANS[choose_plan(move, clue).id]  # type: ignore[union-attr]
    tags = set().union(clue.tags, move.tags, plan.tags, {"tent", "teamwork", "humor"})
    return [item for key, item in KNOWLEDGE.items() if key in tags][:4]


def generate(params: StoryParams) -> StorySample:
    combo = (params.camp, params.move, params.clue, params.gender)
    if combo not in set(valid_combos()):
        raise StoryError(explain_rejection(params.camp, params.move, params.clue, params.gender))
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
effective(M,C,P) :- at_risk(M,C), clue_zone(C,Z), risk(M,R), covers(P,Z), guards(P,R).
valid(Camp,M,C,G) :- camp(Camp), affords(Camp,M), clue(C), gender(G), effective(M,C,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for camp in CAMPS.values():
        facts.append(asp.fact("camp", camp.id))
        for move_id in camp.affords:
            facts.append(asp.fact("affords", camp.id, move_id))
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
    for plan in PLANS.values():
        facts.append(asp.fact("plan", plan.id))
        for zone in plan.covers:
            facts.append(asp.fact("covers", plan.id, zone))
        for risk in plan.guards:
            facts.append(asp.fact("guards", plan.id, risk))
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
    print(f"OK: Python and ASP agree on {len(py)} valid cozy-tent tall tales.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camp", choices=sorted(CAMPS))
    parser.add_argument("--move", choices=sorted(MOVES))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--gender", choices=GENDERS)
    parser.add_argument("--name")
    parser.add_argument("--teammate", choices=TEAMMATES)
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
        if (args.camp is None or combo[0] == args.camp)
        and (args.move is None or combo[1] == args.move)
        and (args.clue is None or combo[2] == args.clue)
        and (args.gender is None or combo[3] == args.gender)
    ]
    if not choices:
        camp = args.camp or sorted(CAMPS)[0]
        move = args.move or sorted(MOVES)[0]
        clue = args.clue or sorted(CLUES)[0]
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(camp, move, clue, gender))
    camp, move, clue, gender = rng.choice(choices)
    name = args.name or rng.choice(NAMES[gender])
    teammate = args.teammate or rng.choice(TEAMMATES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(camp, move, clue, name, gender, teammate, trait, args.seed)


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
            header = f"=== cozy_tent_tall_tale #{idx} seed={sample.params.seed} ==="
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
