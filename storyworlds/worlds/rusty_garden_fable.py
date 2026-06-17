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
    zone: Optional[str] = None
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    used_on: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "gardener": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    fable_line: str


@dataclass(frozen=True)
class Action:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    false_lesson: str
    tags: set[str]


@dataclass(frozen=True)
class Treasure:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    reveal: str
    tags: set[str]


@dataclass(frozen=True)
class Method:
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
        self.active_action: Optional[str] = None

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

    def methods_for(self, treasure: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == treasure.id]

    def protected(self, treasure: Entity, risk: str) -> bool:
        return any(treasure.zone in method.covers and risk in method.guards for method in self.methods_for(treasure))


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


def _r_harm_treasure(world: World, narrate: bool) -> bool:
    action_id = world.active_action
    if not action_id:
        return False
    action = ACTIONS[action_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[action.risk] < THRESHOLD:
            continue
        for treasure in [e for e in world.entities.values() if e.kind == "treasure"]:
            if treasure.zone not in action.zones or action.risk not in treasure.guards:
                continue
            if world.protected(treasure, action.risk):
                continue
            if not _mark(world, "harm_treasure", actor.id, treasure.id, action.risk):
                continue
            treasure.meters["harmed"] += 1
            treasure.meters["lesson_hidden"] += 1
            changed = True
            if narrate:
                world.say(f"The {treasure.label} was harmed before the garden could teach its lesson.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    treasure_id = world.facts.get("treasure")
    friend_id = world.facts.get("friend")
    if not isinstance(treasure_id, str) or not isinstance(friend_id, str):
        return False
    treasure = world.get(treasure_id)
    friend = world.get(friend_id)
    if treasure.meters["lesson_hidden"] < THRESHOLD:
        return False
    if not _mark(world, "friend_worry", treasure.id, friend.id):
        return False
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{friend.label} would miss the surprise if the lesson vanished.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["certainty"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"{hero.label} stopped, but quick certainty still rattled like a rusty hinge.")
    return True


CAUSAL_RULES = [
    Rule("harm_treasure", _r_harm_treasure),
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
    "gate_patch": Setting(
        "gate_patch",
        "the gate patch",
        "the rusty garden by the crooked gate",
        {"scrub_gate", "pull_vine"},
        "The old gate said creak, and the sparrows said wait.",
    ),
    "shed_corner": Setting(
        "shed_corner",
        "the shed corner",
        "the rusty garden beside the tool shed",
        {"oil_lock", "scrub_gate"},
        "The watering can wore spots like a patient old turtle shell.",
    ),
    "stone_bed": Setting(
        "stone_bed",
        "the stone bed",
        "the rusty garden around the stone flower bed",
        {"pull_vine", "oil_lock"},
        "Every stone looked as if it knew a proverb and would tell it slowly.",
    ),
}


ACTIONS = {
    "scrub_gate": Action(
        "scrub_gate",
        "scrub the rusty gate hard",
        "scrubbing the rusty gate hard",
        "wanted to scrub the rusty gate until it shone",
        "scratch",
        {"gate", "paint"},
        "scratch away the mark that explains the surprise",
        "old things are only useful when shiny",
        {"rusty_garden", "fable", "lesson"},
    ),
    "pull_vine": Action(
        "pull_vine",
        "pull the vine from the garden wall",
        "pulling the vine from the garden wall",
        "wanted to pull the vine away and tidy everything at once",
        "tear",
        {"vine", "wall"},
        "tear the hidden sign before anyone could read it",
        "messy things never help",
        {"rusty_garden", "surprise", "patience"},
    ),
    "oil_lock": Action(
        "oil_lock",
        "pour oil into the rusty lock",
        "pouring oil into the rusty lock",
        "wanted to pour oil into the lock and force the box open",
        "blur",
        {"lock", "label"},
        "blur the little label that names the owner",
        "locked things must be stuck for no reason",
        {"rusty_garden", "care", "moral"},
    ),
}


TREASURES = {
    "paint_star": Treasure(
        "paint_star",
        "painted star",
        "tiny painted star",
        "paint",
        {"scratch"},
        "The star showed where Grandmother once measured the tallest sunflower.",
        {"paint", "memory", "surprise"},
    ),
    "vine_sign": Treasure(
        "vine_sign",
        "vine sign",
        "green vine sign",
        "vine",
        {"tear"},
        "The vine spelled SHARE WATER, because the dry side of the garden needed help.",
        {"vine", "lesson", "garden"},
    ),
    "name_label": Treasure(
        "name_label",
        "name label",
        "small name label",
        "label",
        {"blur"},
        "The label said it belonged to the neighbor, who had left seeds for everyone.",
        {"label", "surprise", "kindness"},
    ),
}


METHODS = {
    "soft_brush": Method(
        "soft_brush",
        "soft brush",
        {"gate", "paint"},
        {"scratch"},
        "use the soft brush and stop when a mark appears",
        "used the soft brush and stopped when a mark appeared",
        {"brush", "care"},
    ),
    "vine_frame": Method(
        "vine_frame",
        "vine frame",
        {"vine", "wall"},
        {"tear"},
        "frame the vine before pulling any part of it",
        "framed the vine and read its shape",
        {"vine", "patience"},
    ),
    "drop_oil": Method(
        "drop_oil",
        "single oil drop",
        {"lock", "label"},
        {"blur"},
        "use one oil drop and cover the label",
        "used one oil drop and covered the label",
        {"tool", "care"},
    ),
}


NAMES = {"girl": ["Ada", "Fern", "Mira", "Tess"], "boy": ["Ben", "Eli", "Jon", "Pip"]}
FRIENDS = ["Robin", "Mole", "Lark", "Turtle"]
ELDERS = ["mother", "father", "gardener"]
TRAITS = ["quick", "curious", "kind", "careful"]


def at_risk(action: Action, treasure: Treasure) -> bool:
    return treasure.zone in action.zones and action.risk in treasure.vulnerable


def select_method(action: Action, treasure: Treasure) -> Optional[Method]:
    for method in METHODS.values():
        if treasure.zone in method.covers and action.risk in method.guards:
            return method
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            action = ACTIONS[action_id]
            for treasure_id, treasure in TREASURES.items():
                if at_risk(action, treasure) and select_method(action, treasure) is not None:
                    for gender in GENDERS:
                        out.append((place, action_id, treasure_id, gender))
    return sorted(out)


def explain_rejection(place: str, action_id: str, treasure_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    action = ACTIONS.get(action_id)
    treasure = TREASURES.get(treasure_id)
    if setting is None:
        return f"Unknown place: {place}."
    if action is None:
        return f"Unknown action: {action_id}."
    if treasure is None:
        return f"Unknown treasure: {treasure_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if action_id not in setting.affords:
        return f"{setting.label} does not support {action.label}."
    if not at_risk(action, treasure):
        return f"The {action.label} would not honestly threaten the {treasure.label}."
    if select_method(action, treasure) is None:
        return f"No gentle method protects the {treasure.label} from that action."
    return "The requested options are reasonable."


def do_action(world: World, hero: Entity, action: Action, *, narrate: bool) -> None:
    world.active_action = action.id
    hero.meters[action.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {action.gerund}.")
    propagate(world, narrate=narrate)


def predict_harm(world: World, hero: Entity, action: Action, treasure: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_action(sim, sim.get(hero.id), action, narrate=False)
    sim_treasure = sim.get(treasure.id)
    friend = sim.get(str(sim.facts["friend"]))
    return {
        "harmed": sim_treasure.meters["harmed"] >= THRESHOLD,
        "lesson_hidden": sim_treasure.meters["lesson_hidden"] >= THRESHOLD,
        "friend_worry": friend.memes["worry"] >= THRESHOLD,
        "warning": action.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child named {hero.label} who visited {world.setting.line}."
    )
    world.say(f"{world.setting.fable_line} {friend.label} thought the place looked useless.")
    world.say(f"{hero.label} wanted to prove a rusty garden could become good in one afternoon.")
    hero.memes["helpfulness"] += 1
    friend.memes["doubt"] += 1
    elder.memes["care"] += 1


def place_treasure(world: World, treasure_cfg: Treasure) -> Entity:
    treasure = world.add(
        Entity(
            treasure_cfg.id,
            "treasure",
            treasure_cfg.label,
            zone=treasure_cfg.zone,
            guards=set(treasure_cfg.vulnerable),
        )
    )
    world.say(f"Hidden in the rust and leaves was a {treasure_cfg.full_label}, waiting to surprise them.")
    world.facts["treasure"] = treasure.id
    return treasure


def misunderstand(world: World, hero: Entity, action: Action) -> None:
    world.break_para()
    world.say(f"{hero.label} believed the lesson was: {action.false_lesson}.")
    world.say(f"So {hero.label} {action.urge}.")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, action: Action, treasure: Entity) -> None:
    prediction = predict_harm(world, hero, action, treasure)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {action.label}, you may {prediction["warning"]}. '
        f'A fable teaches slowly."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} frowned at the rusty garden and tried to hurry the lesson along.")
    world.say(f'"But I am helping," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_method(world: World, hero: Entity, friend: Entity, action: Action, treasure_cfg: Treasure) -> Method:
    method = select_method(action, treasure_cfg)
    if method is None:
        raise StoryError("No method can make this rusty-garden fable reasonable.")
    treasure = world.get(str(world.facts["treasure"]))
    world.break_para()
    world.add(
        Entity(
            method.id,
            "method",
            method.label,
            covers=set(method.covers),
            guards=set(method.guards),
            used_on=treasure.id,
            protective=True,
        )
    )
    world.say(f"{friend.label} suggested a slower way.")
    world.say(f'"Let us {method.advice}," {friend.label} said.')
    world.say(f"So {hero.label} {method.action}.")
    hero.memes["patience"] += 1
    friend.memes["hope"] += 1
    world.facts["method"] = method.id
    return method


def reveal(world: World, hero: Entity, friend: Entity, elder: Entity, action: Action, treasure: Entity) -> None:
    treasure_cfg = TREASURES[str(world.facts["treasure"])]
    do_action(world, hero, action, narrate=False)
    if treasure.meters["harmed"] < THRESHOLD:
        world.say(treasure_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["lesson"] += 1
    friend.memes["surprise"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} learned the fable's lesson: old things may be useful before they shine.")
    world.say(f"The surprise made the rusty garden feel wise instead of broken.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    action = ACTIONS[params.action]
    treasure_cfg = TREASURES[params.treasure]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "friend": friend.id, "elder": elder.id, "action": action.id, "place": setting.id})
    introduce(world, hero, friend, elder, params.trait)
    treasure = place_treasure(world, treasure_cfg)
    misunderstand(world, hero, action)
    warn(world, hero, elder, action, treasure)
    pause_conflict(world, hero)
    choose_method(world, hero, friend, action, treasure_cfg)
    reveal(world, hero, friend, elder, action, treasure)
    return world


@dataclass
class StoryParams:
    place: str
    action: str
    treasure: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("gate_patch", "scrub_gate", "paint_star", "Ada", "girl", "Robin", "mother", "quick", 111),
    StoryParams("stone_bed", "pull_vine", "vine_sign", "Eli", "boy", "Mole", "father", "curious", 112),
    StoryParams("shed_corner", "oil_lock", "name_label", "Mira", "girl", "Lark", "gardener", "kind", 113),
    StoryParams("gate_patch", "pull_vine", "vine_sign", "Pip", "boy", "Turtle", "gardener", "careful", 114),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    action = ACTIONS[str(world.facts["action"])]
    treasure = TREASURES[str(world.facts["treasure"])]
    return [
        'Write a fable that includes the phrase "rusty garden".',
        f"Write a surprise story where {hero.label} learns from a {treasure.label}.",
        f"Write a lesson-learned story where {action.gerund} would hide the real moral.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    action = ACTIONS[str(world.facts["action"])]
    treasure = world.get(str(world.facts["treasure"]))
    method = METHODS[str(world.facts["method"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {action.gerund} could {prediction['warning']}. "
            f"The warning was predicted before the {treasure.label} was harmed.",
        ),
        (
            f"How did {friend.label} help?",
            f"{friend.label} suggested the {method.label}, which let {hero.label} work gently. "
            f"That preserved the surprise and let the fable teach its lesson.",
        ),
        (
            "What lesson did the fable teach?",
            f"The fable taught that old things may still be useful before they shine. "
            f"{hero.label} learned to look carefully before fixing the rusty garden.",
        ),
    ]


KNOWLEDGE = {
    "rusty_garden": (
        "What could a rusty garden mean in a fable?",
        "A rusty garden can mean a place that looks old or useless but still holds value. Fables often use such places to teach patience.",
    ),
    "fable": (
        "What is a fable?",
        "A fable is a short story that teaches a moral lesson. It often uses simple actions and a clear consequence.",
    ),
    "lesson": (
        "Why should a lesson be discovered slowly?",
        "A slow discovery lets the character understand cause and effect. Rushing can hide the thing the lesson depends on.",
    ),
    "surprise": (
        "Why can a surprise help a lesson stick?",
        "A surprise changes what the character believes. That makes the lesson easier to remember.",
    ),
    "paint": (
        "Why can old paint be meaningful?",
        "Old paint can mark memories, measurements, or signs. Scrubbing too hard can erase that history.",
    ),
    "vine": (
        "How can a vine be useful in a garden?",
        "A vine can shade, mark, or spell out a natural sign. Pulling it too fast can destroy what it shows.",
    ),
    "label": (
        "Why protect a label?",
        "A label tells who owns something or what it is for. If it blurs, people may misunderstand the object.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    action = ACTIONS[str(world.facts["action"])]
    treasure = TREASURES[str(world.facts["treasure"])]
    method = METHODS[str(world.facts["method"])]
    tags = set(action.tags) | set(treasure.tags) | set(method.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Action,Treasure) :- action_zone(Action,Zone), treasure_zone(Treasure,Zone), risk_of(Action,Risk), vulnerable(Treasure,Risk).
effective(Action,Treasure,Method) :- at_risk(Action,Treasure), treasure_zone(Treasure,Zone), covers(Method,Zone), risk_of(Action,Risk), guards(Method,Risk).
valid(Place,Action,Treasure,Gender) :- setting(Place), affords(Place,Action), treasure(Treasure), gender(Gender), effective(Action,Treasure,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for action in setting.affords:
            lines.append(asp.fact("affords", place, action))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("risk_of", action_id, action.risk))
        for zone in action.zones:
            lines.append(asp.fact("action_zone", action_id, zone))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        lines.append(asp.fact("treasure_zone", treasure_id, treasure.zone))
        for risk in treasure.vulnerable:
            lines.append(asp.fact("vulnerable", treasure_id, risk))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for zone in method.covers:
            lines.append(asp.fact("covers", method_id, zone))
        for risk in method.guards:
            lines.append(asp.fact("guards", method_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid rusty-garden stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the rusty-garden fable storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--action", choices=sorted(ACTIONS))
    parser.add_argument("--treasure", choices=sorted(TREASURES))
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
    if args.action:
        combos = [c for c in combos if c[1] == args.action]
    if args.treasure:
        combos = [c for c in combos if c[2] == args.treasure]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        action = args.action or next(iter(ACTIONS))
        treasure = args.treasure or next(iter(TREASURES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, action, treasure, gender))
    place, action, treasure, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIENDS)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, action, treasure, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.action, params.treasure, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.action, params.treasure, params.gender))
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
        if entity.zone:
            parts.append(f"zone={entity.zone}")
        if entity.covers:
            parts.append(f"covers={sorted(entity.covers)}")
        if entity.guards:
            parts.append(f"guards={sorted(entity.guards)}")
        if entity.used_on:
            parts.append(f"used_on={entity.used_on}")
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
        header = f"=== rusty_garden_fable #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
