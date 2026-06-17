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
    caretaker: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "grandpa": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    flashback: str


@dataclass(frozen=True)
class Probe:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    false_guess: str
    tags: set[str]


@dataclass(frozen=True)
class Secret:
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
        self.active_probe: Optional[str] = None

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

    def methods_for(self, secret: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == secret.id]

    def protected(self, secret: Entity, risk: str) -> bool:
        return any(secret.zone in method.covers and risk in method.guards for method in self.methods_for(secret))


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


def _r_spoil_secret(world: World, narrate: bool) -> bool:
    probe_id = world.active_probe
    if not probe_id:
        return False
    probe = PROBES[probe_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[probe.risk] < THRESHOLD:
            continue
        for secret in [e for e in world.entities.values() if e.kind == "secret"]:
            if secret.zone not in probe.zones or probe.risk not in secret.guards:
                continue
            if world.protected(secret, probe.risk):
                continue
            if not _mark(world, "spoil_secret", actor.id, secret.id, probe.risk):
                continue
            secret.meters["spoiled"] += 1
            secret.meters["needs_fix"] += 1
            changed = True
            if narrate:
                world.say(f"The {secret.label} was spoiled before the whisper was understood.")
    return changed


def _r_caretaker_worry(world: World, narrate: bool) -> bool:
    secret_id = world.facts.get("secret")
    helper_id = world.facts.get("helper")
    if not isinstance(secret_id, str) or not isinstance(helper_id, str):
        return False
    secret = world.get(secret_id)
    helper = world.get(helper_id)
    if secret.meters["needs_fix"] < THRESHOLD:
        return False
    if not _mark(world, "helper_worry", secret.id, helper.id):
        return False
    helper.memes["worry"] += 1
    if narrate:
        world.say(f"{helper.label} would have to fix the joke before anyone laughed.")
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
        world.say(f"{hero.label} stopped, but the funny theory was still wobbling in {hero.pronoun('possessive')} head.")
    return True


CAUSAL_RULES = [
    Rule("spoil_secret", _r_spoil_secret),
    Rule("helper_worry", _r_caretaker_worry),
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
    "riverbank": Setting(
        "riverbank",
        "the riverbank",
        "the riverbank where lunch baskets leaned in the grass",
        {"press_moss", "step_stone"},
        "Last week, a loose sandwich had slid down the bank like a tiny sled.",
    ),
    "ferry_bend": Setting(
        "ferry_bend",
        "the ferry bend",
        "the ferry bend where wet stones clicked under shoes",
        {"step_stone", "pull_reeds"},
        "Yesterday, the ferry rope squeaked so loudly that everyone blamed the ducks on a calendar.",
    ),
    "willow_bank": Setting(
        "willow_bank",
        "the willow bank",
        "the willow bank where the grass met the slow brown water",
        {"press_moss", "pull_reeds"},
        "That morning, Grandpa had said, very seriously, that breakfast toast could echo if it tried hard.",
    ),
}


PROBES = {
    "press_moss": Probe(
        "press_moss",
        "press the whispering moss flat",
        "pressing the whispering moss flat",
        "wanted to press the whispering moss flat and stop the noise",
        "squash",
        {"moss", "bank"},
        "squash the real message under the moss",
        "a talking sandwich",
        {"whispering_moss", "misunderstanding", "comedy"},
    ),
    "step_stone": Probe(
        "step_stone",
        "step on the wobbly stone",
        "stepping on the wobbly stone",
        "wanted to step on the wobbly stone for a better look",
        "slip",
        {"stone", "bank"},
        "slip and smear the hidden clue",
        "a riverbank ghost with hiccups",
        {"wobbly", "riverbank", "safety"},
    ),
    "pull_reeds": Probe(
        "pull_reeds",
        "pull aside the reeds",
        "pulling aside the reeds",
        "wanted to pull aside the reeds and catch the whisper",
        "scatter",
        {"reeds"},
        "scatter the small parts before the joke makes sense",
        "a secret flute",
        {"reeds", "misunderstanding", "flashback"},
    ),
}


SECRETS = {
    "riddle_card": Secret(
        "riddle_card",
        "riddle card",
        "folded riddle card",
        "moss",
        {"squash"},
        "It was a riddle card hidden under the moss, and the answer was: lunch.",
        {"riddle", "paper", "joke"},
    ),
    "paper_boat": Secret(
        "paper_boat",
        "paper boat",
        "tiny paper boat",
        "bank",
        {"squash", "slip"},
        "It was a tiny paper boat with a note inside: Paddle slower, laugh faster.",
        {"paper", "riverbank", "twist"},
    ),
    "pebble_letters": Secret(
        "pebble_letters",
        "pebble letters",
        "line of pebble letters",
        "reeds",
        {"scatter"},
        "It was a line of pebbles spelling HELLO, which was a very quiet kind of shouting.",
        {"pebbles", "joke", "twist"},
    ),
}


METHODS = {
    "listening_cup": Method(
        "listening_cup",
        "listening cup",
        {"moss", "bank"},
        {"squash", "slip"},
        "listen with the cup before touching anything",
        "held the listening cup near the moss",
        {"listening", "patience"},
    ),
    "steady_board": Method(
        "steady_board",
        "steady board",
        {"stone", "bank"},
        {"slip"},
        "put the steady board down before stepping closer",
        "set the steady board across the soft bank",
        {"wobbly", "safety"},
    ),
    "reed_comb": Method(
        "reed_comb",
        "reed comb",
        {"reeds"},
        {"scatter"},
        "comb the reeds apart slowly",
        "combed the reeds apart slowly",
        {"reeds", "care"},
    ),
}


NAMES = {"girl": ["Mira", "Nell", "Poppy", "Tess"], "boy": ["Ben", "Eli", "Jon", "Otto"]}
HELPERS = ["Rae", "Pip", "Lena", "Max"]
ELDERS = ["mother", "father", "grandpa"]
TRAITS = ["curious", "quick", "cheerful", "careful"]


def at_risk(probe: Probe, secret: Secret) -> bool:
    return secret.zone in probe.zones and probe.risk in secret.vulnerable


def select_method(probe: Probe, secret: Secret) -> Optional[Method]:
    for method in METHODS.values():
        if secret.zone in method.covers and probe.risk in method.guards:
            return method
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for probe_id in setting.affords:
            probe = PROBES[probe_id]
            for secret_id, secret in SECRETS.items():
                if at_risk(probe, secret) and select_method(probe, secret) is not None:
                    for gender in GENDERS:
                        out.append((place, probe_id, secret_id, gender))
    return sorted(out)


def explain_rejection(place: str, probe_id: str, secret_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    probe = PROBES.get(probe_id)
    secret = SECRETS.get(secret_id)
    if setting is None:
        return f"Unknown place: {place}."
    if probe is None:
        return f"Unknown probe: {probe_id}."
    if secret is None:
        return f"Unknown secret: {secret_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if probe_id not in setting.affords:
        return f"{setting.label} does not support {probe.label}."
    if not at_risk(probe, secret):
        return f"The {probe.label} would not honestly threaten the {secret.label}."
    if select_method(probe, secret) is None:
        return f"No gentle method protects the {secret.label} from that probe."
    return "The requested options are reasonable."


def do_probe(world: World, hero: Entity, probe: Probe, *, narrate: bool) -> None:
    world.active_probe = probe.id
    hero.meters[probe.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {probe.gerund}.")
    propagate(world, narrate=narrate)


def predict_spoil(world: World, hero: Entity, probe: Probe, secret: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_probe(sim, sim.get(hero.id), probe, narrate=False)
    sim_secret = sim.get(secret.id)
    helper = sim.get(str(sim.facts["helper"]))
    return {
        "spoiled": sim_secret.meters["spoiled"] >= THRESHOLD,
        "needs_fix": sim_secret.meters["needs_fix"] >= THRESHOLD,
        "helper_worry": helper.memes["worry"] >= THRESHOLD,
        "warning": probe.warning,
    }


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child named {hero.label} who sat on {world.setting.line}."
    )
    world.say(f"{world.setting.flashback} {hero.label} remembered this and tried not to laugh.")
    world.say(f"Then the whispering moss went psst, psst, psst beside the riverbank.")
    world.say(f"{helper.label} whispered back, which did not help the investigation at all.")
    hero.memes["curiosity"] += 1
    helper.memes["mischief"] += 1
    elder.memes["care"] += 1


def place_secret(world: World, secret_cfg: Secret) -> Entity:
    secret = world.add(
        Entity(
            secret_cfg.id,
            "secret",
            secret_cfg.label,
            zone=secret_cfg.zone,
            guards=set(secret_cfg.vulnerable),
            caretaker=str(world.facts["helper"]),
        )
    )
    world.say(f"Hidden nearby was a {secret_cfg.full_label}, though the moss kept that part quiet.")
    world.facts["secret"] = secret.id
    return secret


def misunderstand(world: World, hero: Entity, probe: Probe) -> None:
    world.break_para()
    world.say(f"{hero.label} decided the sound must be {probe.false_guess} and {probe.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"This is probably science, unless it is lunch.\"")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, probe: Probe, secret: Entity) -> None:
    prediction = predict_spoil(world, hero, probe, secret)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {probe.label}, you may {prediction["warning"]}. '
        f'The whisper might be hiding a joke, not danger."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} looked at the wobbly riverbank and tried to look official.")
    world.say(f'"I was being careful loudly," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_method(world: World, hero: Entity, helper: Entity, probe: Probe, secret_cfg: Secret) -> Method:
    method = select_method(probe, secret_cfg)
    if method is None:
        raise StoryError("No gentle method can make this whispering-moss story reasonable.")
    secret = world.get(str(world.facts["secret"]))
    world.break_para()
    world.add(
        Entity(
            method.id,
            "method",
            method.label,
            covers=set(method.covers),
            guards=set(method.guards),
            used_on=secret.id,
            protective=True,
        )
    )
    world.say(f"{helper.label} produced a better plan with the seriousness of a person holding a spoon upside down.")
    world.say(f'"Let us {method.advice}," {helper.label} said.')
    world.say(f"So {hero.label} {method.action}.")
    hero.memes["patience"] += 1
    helper.memes["helpfulness"] += 1
    world.facts["method"] = method.id
    return method


def reveal(world: World, hero: Entity, helper: Entity, elder: Entity, probe: Probe, secret: Entity) -> None:
    secret_cfg = SECRETS[str(world.facts["secret"])]
    do_probe(world, hero, probe, narrate=False)
    if secret.meters["spoiled"] < THRESHOLD:
        world.say(secret_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["surprise"] += 1
    helper.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} laughed so hard that the riverbank looked less wobbly.")
    world.say(f"The whispering moss had not been mysterious. It had only been very good at comedy.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    probe = PROBES[params.probe]
    secret_cfg = SECRETS[params.secret]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    helper = world.add(Entity("helper", "character", params.helper, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "helper": helper.id, "elder": elder.id, "probe": probe.id, "place": setting.id})
    introduce(world, hero, helper, elder, params.trait)
    secret = place_secret(world, secret_cfg)
    misunderstand(world, hero, probe)
    warn(world, hero, elder, probe, secret)
    pause_conflict(world, hero)
    choose_method(world, hero, helper, probe, secret_cfg)
    reveal(world, hero, helper, elder, probe, secret)
    return world


@dataclass
class StoryParams:
    place: str
    probe: str
    secret: str
    name: str
    gender: str
    helper: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("riverbank", "press_moss", "riddle_card", "Mira", "girl", "Rae", "mother", "curious", 61),
    StoryParams("ferry_bend", "step_stone", "paper_boat", "Eli", "boy", "Pip", "father", "quick", 62),
    StoryParams("willow_bank", "pull_reeds", "pebble_letters", "Nell", "girl", "Lena", "grandpa", "cheerful", 63),
    StoryParams("riverbank", "press_moss", "paper_boat", "Otto", "boy", "Max", "grandpa", "careful", 64),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    probe = PROBES[str(world.facts["probe"])]
    secret = SECRETS[str(world.facts["secret"])]
    secret_phrase = secret.label if secret.id == "pebble_letters" else f"a {secret.label}"
    return [
        'Write a comedy story that includes "wobbly", "whispering moss", and "riverbank".',
        f"Write a story where {hero.label} misunderstands {secret_phrase} while {probe.gerund}.",
        "Write a story with a flashback and a funny twist about solving a harmless mystery.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    helper = world.get(str(world.facts["helper"]))
    elder = world.get(str(world.facts["elder"]))
    probe = PROBES[str(world.facts["probe"])]
    secret = world.get(str(world.facts["secret"]))
    method = METHODS[str(world.facts["method"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because the rough plan could cause this problem: {prediction['warning']}. "
            f"The warning was predicted before the {secret.label} was spoiled.",
        ),
        (
            "What was the misunderstanding?",
            f"{hero.label} thought the whisper was {probe.false_guess}. "
            f"It was really connected to the {secret.label}, so the rough solution would have missed the joke.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label} suggested the {method.label}, which let everyone investigate gently. "
            f"That preserved the hidden joke and turned the mystery into a comedy.",
        ),
    ]


KNOWLEDGE = {
    "whispering_moss": (
        "Why might moss seem to whisper?",
        "Moss can hold water, leaves, or small hidden objects. Wind or moving water nearby can make soft sounds seem to come from it.",
    ),
    "riverbank": (
        "Why can a riverbank be wobbly or slippery?",
        "A riverbank can be soft because water loosens soil. Careful steps keep a person from slipping or smearing things near the edge.",
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone explains a situation the wrong way at first. More careful checking can reveal the real answer.",
    ),
    "comedy": (
        "How can a misunderstanding make a comedy story?",
        "Comedy often comes from a serious guess turning out to be harmless or silly. The surprise makes the characters and readers laugh.",
    ),
    "paper": (
        "Why should paper near water be handled carefully?",
        "Paper can tear, smear, or get soggy near water. Gentle handling keeps writing and folds readable.",
    ),
    "pebbles": (
        "How can pebbles become a message?",
        "Pebbles can be arranged into letters, arrows, or shapes. If they are scattered, the message disappears.",
    ),
    "patience": (
        "Why does patience help with small mysteries?",
        "Patience gives people time to observe before acting. It can protect clues that a rushed action would damage.",
    ),
    "wobbly": (
        "What does wobbly mean?",
        "Wobbly means unsteady or likely to tip. A wobbly stone or bank needs a slower, safer approach.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    probe = PROBES[str(world.facts["probe"])]
    secret = SECRETS[str(world.facts["secret"])]
    method = METHODS[str(world.facts["method"])]
    tags = set(probe.tags) | set(secret.tags) | set(method.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Probe,Secret) :- probe_zone(Probe,Zone), secret_zone(Secret,Zone), risk_of(Probe,Risk), vulnerable(Secret,Risk).
effective(Probe,Secret,Method) :- at_risk(Probe,Secret), secret_zone(Secret,Zone), covers(Method,Zone), risk_of(Probe,Risk), guards(Method,Risk).
valid(Place,Probe,Secret,Gender) :- setting(Place), affords(Place,Probe), secret(Secret), gender(Gender), effective(Probe,Secret,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for probe in setting.affords:
            lines.append(asp.fact("affords", place, probe))
    for probe_id, probe in PROBES.items():
        lines.append(asp.fact("probe", probe_id))
        lines.append(asp.fact("risk_of", probe_id, probe.risk))
        for zone in probe.zones:
            lines.append(asp.fact("probe_zone", probe_id, zone))
    for secret_id, secret in SECRETS.items():
        lines.append(asp.fact("secret", secret_id))
        lines.append(asp.fact("secret_zone", secret_id, secret.zone))
        for risk in secret.vulnerable:
            lines.append(asp.fact("vulnerable", secret_id, risk))
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
        print(f"OK: Python and ASP agree on {len(py)} valid whispering-moss stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the whispering-moss riverbank storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--probe", choices=sorted(PROBES))
    parser.add_argument("--secret", choices=sorted(SECRETS))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--helper", choices=HELPERS)
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
    if args.probe:
        combos = [c for c in combos if c[1] == args.probe]
    if args.secret:
        combos = [c for c in combos if c[2] == args.secret]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        probe = args.probe or next(iter(PROBES))
        secret = args.secret or next(iter(SECRETS))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, probe, secret, gender))
    place, probe, secret, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, probe, secret, name, gender, helper, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.probe, params.secret, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.probe, params.secret, params.gender))
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
        header = f"=== whispering_moss_riverbank #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
