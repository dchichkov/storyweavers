#!/usr/bin/env python3
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
GENDERS = ("girl", "boy")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    gender: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    region: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    carried_by: Optional[str] = None
    owner: Optional[str] = None
    protective: bool = False
    plural: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "keeper": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    place_line: str
    affords: set[str]
    ghost_line: str


@dataclass(frozen=True)
class Passage:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class Lamp:
    id: str
    label: str
    full_label: str
    region: str
    vulnerable: set[str]
    owner_line: str
    tags: set[str]


@dataclass(frozen=True)
class Safety:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    advice: str
    action: str
    tags: set[str]


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.fired_names: list[str] = []
        self.facts: dict[str, object] = {}
        self.active_passage: Optional[str] = None

    def copy(self) -> "World":
        return copy.deepcopy(self)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def break_para(self) -> None:
        if self.paragraphs and self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def protected(self, actor: Entity, zone: str, risk: str) -> bool:
        for item in self.carried_items(actor):
            if item.protective and zone in item.covers and risk in item.guards:
                return True
        return False


@dataclass(frozen=True)
class Rule:
    name: str
    apply: Callable[[World, bool], bool]


def _fire(world: World, name: str, *parts: object) -> bool:
    sig = (name, *parts)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    world.fired_names.append(name)
    return True


def _r_lamp_damage(world: World, narrate: bool) -> bool:
    passage_id = world.active_passage
    if not passage_id:
        return False
    passage = PASSAGES[passage_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[passage.risk] < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            if item.kind != "lamp" or item.region not in passage.zones:
                continue
            if passage.risk not in item.guards:
                continue
            if world.protected(actor, item.region, passage.risk):
                continue
            if not _fire(world, "lamp_damage", actor.id, item.id, passage.risk):
                continue
            item.meters["dimmed"] += 1
            item.meters["needs_mending"] += 1
            changed = True
            if narrate:
                world.say(f"The {item.label} jolted and went dim.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    lamp_id = world.facts.get("lamp")
    friend_id = world.facts.get("friend")
    if not isinstance(lamp_id, str) or not isinstance(friend_id, str):
        return False
    lamp = world.get(lamp_id)
    friend = world.get(friend_id)
    if lamp.meters["needs_mending"] < THRESHOLD:
        return False
    if not _fire(world, "friend_worry", lamp.id, friend.id):
        return False
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{friend.label} would be sad if the lamp could not guide them home.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["impatience"] < THRESHOLD or hero.meters["held_back"] < THRESHOLD:
        return False
    if not _fire(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"For one breath, {hero.label}'s hurry pulled against {elder.label}'s care.")
    return True


CAUSAL_RULES = [
    Rule("lamp_damage", _r_lamp_damage),
    Rule("friend_worry", _r_friend_worry),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, *, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world, narrate):
                changed = True


SETTINGS = {
    "silent_gate": Setting(
        "silent_gate",
        "the silent gate",
        "a black garden gate that never creaked, even when the wind leaned on it",
        {"dash_gate", "climb_step"},
        "Every house on the lane kept its curtains still when that gate was near.",
    ),
    "misty_path": Setting(
        "misty_path",
        "the misty path",
        "a path where moonlight lay in pale strips",
        {"dash_gate", "cross_stones"},
        "The mist looked like old breath, but it was only cold air over the grass.",
    ),
    "hollow_porch": Setting(
        "hollow_porch",
        "the hollow porch",
        "a porch with boards that answered footsteps with tiny sighs",
        {"climb_step", "cross_stones"},
        "The porch seemed empty enough to remember every whisper.",
    ),
}


PASSAGES = {
    "dash_gate": Passage(
        "dash_gate",
        "dash through the silent gate",
        "dashing through the silent gate",
        "wanted to dash through the silent gate before the shadow touched the latch",
        "tumble",
        {"base", "handle"},
        "tumble and knock the lamp dim",
        {"silent_gate", "tumble", "lamp", "kindness"},
    ),
    "climb_step": Passage(
        "climb_step",
        "climb the narrow step with the lamp",
        "climbing the narrow step with the lamp",
        "wanted to climb the narrow step while holding the wobbly lamp high",
        "wobble",
        {"handle"},
        "wobble until the flame shakes out",
        {"wobbly_lamp", "lamp", "caution", "kindness"},
    ),
    "cross_stones": Passage(
        "cross_stones",
        "cross the slick stepping stones",
        "crossing the slick stepping stones",
        "wanted to cross the slick stepping stones with the wobbly lamp",
        "tumble",
        {"base"},
        "tumble and crack the lamp base",
        {"tumble", "lamp", "path", "kindness"},
    ),
}


LAMPS = {
    "glass_lamp": Lamp(
        "glass_lamp",
        "glass lamp",
        "wobbly glass lamp",
        "base",
        {"tumble"},
        "It belonged to the friend who was waiting on the far side.",
        {"wobbly_lamp", "glass", "lamp"},
    ),
    "tin_lamp": Lamp(
        "tin_lamp",
        "tin lamp",
        "wobbly tin lamp",
        "handle",
        {"wobble", "tumble"},
        "It was the only lamp bright enough for two children to share.",
        {"wobbly_lamp", "tin", "lamp"},
    ),
    "blue_lamp": Lamp(
        "blue_lamp",
        "blue lamp",
        "wobbly blue lamp",
        "base",
        {"tumble"},
        "It was promised for the walk home.",
        {"wobbly_lamp", "lamp", "friendship"},
    ),
}


SAFETIES = {
    "steady_tray": Safety(
        "steady_tray",
        "steady tray",
        {"base"},
        {"tumble"},
        "Set the lamp on the steady tray and walk slowly",
        "set the wobbly lamp on the steady tray",
        {"tray", "lamp"},
    ),
    "handle_loop": Safety(
        "handle_loop",
        "soft handle loop",
        {"handle"},
        {"wobble", "tumble"},
        "Slip the soft loop over the handle before you climb",
        "slipped the soft loop over the lamp handle",
        {"handle", "lamp"},
    ),
    "two_hand_carry": Safety(
        "two_hand_carry",
        "two-hand carry cloth",
        {"base", "handle"},
        {"wobble", "tumble"},
        "Carry it together with the cloth between both hands",
        "held the cloth with both hands around the lamp",
        {"kindness", "lamp"},
    ),
}


NAMES = {
    "girl": ["Ivy", "Mara", "Tess", "Nina"],
    "boy": ["Eli", "Noah", "Sam", "Milo"],
}
FRIENDS = ["Rue", "Ada", "Leo", "June"]
ELDERS = ["mother", "father", "keeper"]
TRAITS = ["kind", "thoughtful", "brave", "quiet"]


def at_risk(passage: Passage, lamp: Lamp) -> bool:
    return lamp.region in passage.zones and passage.risk in lamp.vulnerable


def select_safety(passage: Passage, lamp: Lamp) -> Optional[Safety]:
    for safety in SAFETIES.values():
        if lamp.region in safety.covers and passage.risk in safety.guards:
            return safety
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for passage_id in setting.affords:
            passage = PASSAGES[passage_id]
            for lamp_id, lamp in LAMPS.items():
                if not at_risk(passage, lamp):
                    continue
                if select_safety(passage, lamp) is None:
                    continue
                for gender in GENDERS:
                    combos.append((place_id, passage_id, lamp_id, gender))
    return sorted(combos)


def explain_rejection(place: str, passage_id: str, lamp_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    passage = PASSAGES.get(passage_id)
    lamp = LAMPS.get(lamp_id)
    if setting is None:
        return f"Unknown place: {place}."
    if passage is None:
        return f"Unknown passage: {passage_id}."
    if lamp is None:
        return f"Unknown lamp: {lamp_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if passage_id not in setting.affords:
        return f"{setting.label} does not support {passage.label}."
    if not at_risk(passage, lamp):
        return f"The {passage.label} would not honestly threaten the {lamp.label}."
    if select_safety(passage, lamp) is None:
        return f"No available safety item fixes the risk to the {lamp.label}."
    return "The requested options are reasonable."


def _attempt_passage(world: World, hero: Entity, passage: Passage, *, narrate: bool) -> None:
    world.active_passage = passage.id
    hero.meters[passage.risk] += 1
    if narrate:
        world.say(f"{hero.label} began {passage.gerund}.")
    propagate(world, narrate=narrate)


def predict_outcome(world: World, hero: Entity, passage: Passage, lamp: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    _attempt_passage(sim, sim.get(hero.id), passage, narrate=False)
    sim_lamp = sim.get(lamp.id)
    friend_id = sim.facts.get("friend")
    worry = False
    if isinstance(friend_id, str):
        worry = sim.get(friend_id).memes["worry"] >= THRESHOLD
    return {
        "lamp_dimmed": sim_lamp.meters["dimmed"] >= THRESHOLD,
        "needs_mending": sim_lamp.meters["needs_mending"] >= THRESHOLD,
        "friend_worry": worry,
        "warning": passage.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a little {trait} {hero.gender} named {hero.label} "
        f"who lived beside {world.setting.place_line}."
    )
    world.say(f"{world.setting.ghost_line} {hero.label} was not sure if that made the place haunted or just lonely.")
    world.say(
        f"{hero.label} thought, \"If {friend.label} is waiting in the dark, kindness means I should not be slow.\""
    )
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    elder.memes["care"] += 1


def give_lamp(world: World, hero: Entity, friend: Entity, lamp_cfg: Lamp) -> Entity:
    lamp = world.add(
        Entity(
            lamp_cfg.id,
            "lamp",
            lamp_cfg.label,
            region=lamp_cfg.region,
            guards=set(lamp_cfg.vulnerable),
            carried_by=hero.id,
            owner=friend.id,
        )
    )
    world.say(
        f"{hero.label} carried a {lamp_cfg.full_label}. {lamp_cfg.owner_line} "
        f"The lamp leaned left, then right, as if it had its own worried thoughts."
    )
    hero.memes["responsibility"] += 1
    world.facts["lamp"] = lamp.id
    return lamp


def want_to_help(world: World, hero: Entity, passage: Passage) -> None:
    world.break_para()
    world.say(f"When the lane grew quiet, {hero.label} {passage.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"I can be kind faster than I can be careful.\"")
    hero.memes["impatience"] += 1


def warn(world: World, hero: Entity, elder: Entity, passage: Passage, lamp: Entity) -> None:
    prediction = predict_outcome(world, hero, passage, lamp)
    world.facts["prediction"] = prediction
    friend = world.get(str(world.facts["friend"]))
    world.say(
        f'"Wait," said {elder.label}. "If you {passage.label}, you may {prediction["warning"]}. '
        f'Then {friend.label} will have no light for the way home."'
    )
    elder.memes["caution"] += 1


def resist(world: World, hero: Entity, elder: Entity) -> None:
    world.say(f"{hero.label} looked at the silent gate and wished bravery felt less loud inside.")
    world.say(f'"I only want to help," {hero.pronoun("subject")} said.')
    hero.meters["held_back"] += 1
    propagate(world, narrate=True)


def compromise(world: World, hero: Entity, friend: Entity, passage: Passage, lamp_cfg: Lamp) -> Safety:
    safety = select_safety(passage, lamp_cfg)
    if safety is None:
        raise StoryError("No safety item can make this silent-gate story reasonable.")
    world.break_para()
    world.add(
        Entity(
            safety.id,
            "safety",
            safety.label,
            covers=set(safety.covers),
            guards=set(safety.guards),
            carried_by=hero.id,
            protective=True,
        )
    )
    world.say(f"{friend.label} stepped out from the mist and held up a small helper's tool.")
    world.say(f'"{safety.advice}," {friend.label} whispered. "Kindness can wait three careful breaths."')
    world.say(f"So {hero.label} {safety.action}.")
    hero.memes["patience"] += 1
    friend.memes["kindness"] += 1
    world.facts["safety"] = safety.id
    return safety


def finish(world: World, hero: Entity, friend: Entity, elder: Entity, passage: Passage, lamp: Entity) -> None:
    _attempt_passage(world, hero, passage, narrate=False)
    if lamp.meters["dimmed"] < THRESHOLD:
        world.say(
            f"The {lamp.label} stayed bright, and the silent gate opened without a sound."
        )
    hero.memes["conflict"] = 0
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(
        f"{hero.label} gave {friend.label} the light, and thought that kindness was strongest "
        f"when it did not make more trouble."
    )
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    passage = PASSAGES[params.passage]
    lamp_cfg = LAMPS[params.lamp]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update(
        {
            "hero": hero.id,
            "friend": friend.id,
            "elder": elder.id,
            "place": setting.id,
            "passage": passage.id,
            "resolved": False,
        }
    )
    introduce(world, hero, friend, elder, params.trait)
    lamp = give_lamp(world, hero, friend, lamp_cfg)
    want_to_help(world, hero, passage)
    warn(world, hero, elder, passage, lamp)
    resist(world, hero, elder)
    compromise(world, hero, friend, passage, lamp_cfg)
    finish(world, hero, friend, elder, passage, lamp)
    return world


@dataclass
class StoryParams:
    place: str
    passage: str
    lamp: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("silent_gate", "dash_gate", "glass_lamp", "Ivy", "girl", "Rue", "mother", "kind", 21),
    StoryParams("hollow_porch", "climb_step", "tin_lamp", "Eli", "boy", "Ada", "father", "thoughtful", 22),
    StoryParams("misty_path", "cross_stones", "blue_lamp", "Mara", "girl", "Leo", "keeper", "brave", 23),
    StoryParams("silent_gate", "dash_gate", "tin_lamp", "Noah", "boy", "June", "keeper", "quiet", 24),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    passage = PASSAGES[str(world.facts["passage"])]
    lamp = LAMPS[str(world.facts["lamp"])]
    return [
        'Write a gentle ghost story that includes "silent gate", "tumble", and "wobbly lamp".',
        f"Write a story about {hero.label}, kindness, and {passage.gerund} while carrying a {lamp.full_label}.",
        "Write a story where a child's inner monologue changes from hurry to careful kindness.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    passage = PASSAGES[str(world.facts["passage"])]
    lamp = world.get(str(world.facts["lamp"]))
    safety = SAFETIES[str(world.facts["safety"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} warn {hero.label}?",
            f"{elder.label} warned {hero.label} because {passage.gerund} could make {hero.pronoun('object')} {prediction['warning']}. "
            f"The warning was predicted before the {lamp.label} was actually damaged.",
        ),
        (
            f"How did {friend.label} show kindness?",
            f"{friend.label} brought the {safety.label} and suggested a safer way to move. "
            f"That helped {hero.label} protect the lamp instead of turning kindness into a new problem.",
        ),
        (
            "What did the child learn?",
            f"{hero.label} learned that helping quickly is not always the same as helping well. "
            f"By slowing down, {hero.pronoun('subject')} kept the lamp bright and still helped {friend.label}.",
        ),
    ]


KNOWLEDGE = {
    "silent_gate": (
        "Why might a silent gate feel spooky in a story?",
        "A silent gate can feel spooky because readers expect old gates to creak. The missing sound makes the place feel still and mysterious.",
    ),
    "tumble": (
        "What does it mean to tumble?",
        "To tumble means to trip, roll, or fall suddenly. If someone is carrying something fragile, a tumble can damage it.",
    ),
    "wobbly_lamp": (
        "Why should someone be careful with a wobbly lamp?",
        "A wobbly lamp can tip over or go out if it is carried too fast. Holding it steady keeps the light useful.",
    ),
    "kindness": (
        "What is careful kindness?",
        "Careful kindness means helping in a way that does not create another problem. It pays attention to the person and the object being protected.",
    ),
    "lamp": (
        "Why is light important on a dark path?",
        "Light helps people see where to step. It can also make a dark place feel safer.",
    ),
    "handle": (
        "Why does a handle help with carrying?",
        "A handle gives the hand a steady place to hold. A loop or wrap can make that hold safer.",
    ),
    "path": (
        "Why can stepping stones be slippery?",
        "Stepping stones can be slippery when they are wet, icy, or covered in mist. Slow steps reduce the chance of falling.",
    ),
    "tray": (
        "How can a tray help carry a lamp?",
        "A tray supports the base of the lamp. It spreads the weight and helps keep the lamp upright.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    passage = PASSAGES[str(world.facts["passage"])]
    lamp = LAMPS[str(world.facts["lamp"])]
    safety = SAFETIES[str(world.facts["safety"])]
    tags = set(passage.tags) | set(lamp.tags) | set(safety.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Passage,Lamp) :- zone(Passage,Region), lamp_region(Lamp,Region), risk_of(Passage,Risk), vulnerable(Lamp,Risk).
effective(Passage,Lamp,Safety) :- at_risk(Passage,Lamp), lamp_region(Lamp,Region), covers(Safety,Region), risk_of(Passage,Risk), guards(Safety,Risk).
valid(Place,Passage,Lamp,Gender) :- setting(Place), affords(Place,Passage), lamp(Lamp), gender(Gender), effective(Passage,Lamp,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for passage in setting.affords:
            lines.append(asp.fact("affords", place, passage))
    for passage_id, passage in PASSAGES.items():
        lines.append(asp.fact("passage", passage_id))
        lines.append(asp.fact("risk_of", passage_id, passage.risk))
        for zone in passage.zones:
            lines.append(asp.fact("zone", passage_id, zone))
    for lamp_id, lamp in LAMPS.items():
        lines.append(asp.fact("lamp", lamp_id))
        lines.append(asp.fact("lamp_region", lamp_id, lamp.region))
        for risk in lamp.vulnerable:
            lines.append(asp.fact("vulnerable", lamp_id, risk))
    for safety_id, safety in SAFETIES.items():
        lines.append(asp.fact("safety", safety_id))
        for region in safety.covers:
            lines.append(asp.fact("covers", safety_id, region))
        for risk in safety.guards:
            lines.append(asp.fact("guards", safety_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid silent-gate stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the silent-gate lamp storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--passage", choices=sorted(PASSAGES))
    parser.add_argument("--lamp", choices=sorted(LAMPS))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--elder", choices=ELDERS)
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.passage:
        combos = [c for c in combos if c[1] == args.passage]
    if args.lamp:
        combos = [c for c in combos if c[2] == args.lamp]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        passage = args.passage or next(iter(PASSAGES))
        lamp = args.lamp or next(iter(LAMPS))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, passage, lamp, gender))
    place, passage, lamp, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice([f for f in FRIENDS if f != name])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, passage, lamp, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.passage, params.lamp, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.passage, params.lamp, params.gender))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def dump_trace(world: World) -> None:
    print("\nTRACE")
    print(f"setting: {world.setting.id}")
    print("fired rules:", ", ".join(world.fired_names) or "(none)")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        parts = [entity.id, entity.kind, entity.label]
        if entity.region:
            parts.append(f"region={entity.region}")
        if entity.covers:
            parts.append(f"covers={sorted(entity.covers)}")
        if entity.guards:
            parts.append(f"guards={sorted(entity.guards)}")
        if entity.carried_by:
            parts.append(f"carried_by={entity.carried_by}")
        print("  " + " | ".join(parts))
        if meters:
            print(f"    meters={meters}")
        if memes:
            print(f"    memes={memes}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if qa:
        print("\nPROMPTS")
        for prompt in sample.prompts:
            print(f"- {prompt}")
        print("\nSTORY QA")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\nWORLD KNOWLEDGE QA")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
    if trace and sample.world is not None:
        dump_trace(sample.world)


def _samples_from_args(args) -> list[StorySample]:
    if args.all:
        return [generate(params) for params in CURATED]
    base_seed = args.seed if args.seed is not None else random.randrange(1, 10_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempts = 0
    while len(samples) < args.n and attempts < max(20, args.n * 20):
        seed = base_seed + attempts
        rng = random.Random(seed)
        local_args = copy.copy(args)
        local_args.seed = seed
        params = resolve_params(local_args, rng)
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            samples.append(sample)
            seen.add(sample.story)
        attempts += 1
    if len(samples) < args.n:
        raise StoryError(f"Only generated {len(samples)} distinct stories after {attempts} attempts.")
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
            print(combo)
        return 0
    try:
        samples = _samples_from_args(args)
    except StoryError as exc:
        parser.error(str(exc))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return 0
    for i, sample in enumerate(samples, 1):
        header = f"=== silent_gate_lamp #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
