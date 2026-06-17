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
            "keeper": {"subject": "they", "object": "them", "possessive": "their"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    pond_line: str


@dataclass(frozen=True)
class Attempt:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    mistaken_need: str
    tags: set[str]


@dataclass(frozen=True)
class Charge:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    reveal: str
    tags: set[str]
    plural: bool = False


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
        self.active_attempt: Optional[str] = None

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

    def safeties_for(self, charge: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == charge.id]

    def protected(self, charge: Entity, risk: str) -> bool:
        return any(charge.zone in item.covers and risk in item.guards for item in self.safeties_for(charge))


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


def _r_harm_charge(world: World, narrate: bool) -> bool:
    attempt_id = world.active_attempt
    if not attempt_id:
        return False
    attempt = ATTEMPTS[attempt_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[attempt.risk] < THRESHOLD:
            continue
        for charge in [e for e in world.entities.values() if e.kind == "charge"]:
            if charge.zone not in attempt.zones or attempt.risk not in charge.guards:
                continue
            if world.protected(charge, attempt.risk):
                continue
            if not _mark(world, "harm_charge", actor.id, charge.id, attempt.risk):
                continue
            charge.meters["harmed"] += 1
            charge.meters["needs_care"] += 1
            changed = True
            if narrate:
                world.say(f"The {charge.label} was hurt before anyone understood the right problem.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    charge_id = world.facts.get("charge")
    friend_id = world.facts.get("friend")
    if not isinstance(charge_id, str) or not isinstance(friend_id, str):
        return False
    charge = world.get(charge_id)
    friend = world.get(friend_id)
    if charge.meters["needs_care"] < THRESHOLD:
        return False
    if not _mark(world, "friend_worry", charge.id, friend.id):
        return False
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{friend.label} would have to fix the mistake.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["hurry"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"{hero.label} stopped, but {hero.pronoun('possessive')} helpful hurry still tugged hard.")
    return True


CAUSAL_RULES = [
    Rule("harm_charge", _r_harm_charge),
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
    "pond_shed": Setting(
        "pond_shed",
        "the pond shed",
        "the little shed beside the icy pond",
        {"yank_door", "step_ice"},
        "The ice was pale and thin near the rusty door.",
    ),
    "reed_bank": Setting(
        "reed_bank",
        "the reed bank",
        "the reed bank behind the old boathouse",
        {"push_door", "step_ice"},
        "Reeds tapped the ice like tiny warning sticks.",
    ),
    "frost_yard": Setting(
        "frost_yard",
        "the frost yard",
        "the frost yard where animal tracks crossed the snow",
        {"yank_door", "push_door"},
        "A rusty door leaned open just enough to make everyone curious.",
    ),
}


ATTEMPTS = {
    "yank_door": Attempt(
        "yank_door",
        "yank the rusty door open",
        "yanking the rusty door open",
        "wanted to yank the rusty door open and rescue whatever was inside",
        "snap",
        {"hinge", "bank"},
        "snap the latch and frighten the animal hiding nearby",
        "a duck trapped inside",
        {"rusty_door", "animal", "moral"},
    ),
    "push_door": Attempt(
        "push_door",
        "push the rusty door with both paws",
        "pushing the rusty door with both paws",
        "wanted to push the rusty door and prove the shed was empty",
        "scrape",
        {"threshold", "hinge"},
        "scrape away the sign that explains the problem",
        "a sneaky raccoon",
        {"rusty_door", "misunderstanding", "care"},
    ),
    "step_ice": Attempt(
        "step_ice",
        "step onto the icy pond edge",
        "stepping onto the icy pond edge",
        "wanted to step onto the icy pond edge for a closer look",
        "crack",
        {"ice", "bank"},
        "crack the thin ice and scare the small animal nearby",
        "a fish knocking from below",
        {"icy_pond", "safety", "animal"},
    ),
}


CHARGES = {
    "duck_nest": Charge(
        "duck_nest",
        "duck nest",
        "warm duck nest",
        "bank",
        {"snap", "crack"},
        "It was a duck nest beside the door, not a duck trapped behind it.",
        {"duck", "nest", "animal"},
    ),
    "turtle_bell": Charge(
        "turtle_bell",
        "turtle bell",
        "tiny turtle bell",
        "hinge",
        {"snap", "scrape"},
        "It was a bell tied to the hinge so Turtle could ask for help without shouting.",
        {"turtle", "bell", "moral"},
    ),
    "paw_prints": Charge(
        "paw_prints",
        "paw prints",
        "line of paw prints",
        "threshold",
        {"scrape"},
        "The paw prints showed that the missing otter had already walked home.",
        {"prints", "misunderstanding", "animal"},
        True,
    ),
}


SAFETIES = {
    "hinge_oil": Safety(
        "hinge_oil",
        "hinge oil",
        {"hinge"},
        {"snap", "scrape"},
        "oil the hinge before moving the door",
        "oiled the hinge and moved the door slowly",
        {"rusty_door", "tool"},
    ),
    "sand_path": Safety(
        "sand_path",
        "sand path",
        {"ice", "bank"},
        {"crack"},
        "sprinkle sand and stay on the bank",
        "sprinkled sand and stayed on the bank",
        {"icy_pond", "safety"},
    ),
    "soft_marker": Safety(
        "soft_marker",
        "soft marker",
        {"threshold", "bank"},
        {"scrape", "snap"},
        "mark the spot gently before touching anything",
        "marked the spot gently before touching anything",
        {"care", "moral"},
    ),
}


NAMES = {"girl": ["Fern", "Mira", "Nell", "Tess"], "boy": ["Bram", "Eli", "Otto", "Pip"]}
FRIENDS = ["Duck", "Turtle", "Otter", "Mole"]
ELDERS = ["mother", "father", "keeper"]
TRAITS = ["helpful", "quick", "kind", "curious"]


def at_risk(attempt: Attempt, charge: Charge) -> bool:
    return charge.zone in attempt.zones and attempt.risk in charge.vulnerable


def select_safety(attempt: Attempt, charge: Charge) -> Optional[Safety]:
    for safety in SAFETIES.values():
        if charge.zone in safety.covers and attempt.risk in safety.guards:
            return safety
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for attempt_id in setting.affords:
            attempt = ATTEMPTS[attempt_id]
            for charge_id, charge in CHARGES.items():
                if at_risk(attempt, charge) and select_safety(attempt, charge) is not None:
                    for gender in GENDERS:
                        out.append((place, attempt_id, charge_id, gender))
    return sorted(out)


def explain_rejection(place: str, attempt_id: str, charge_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    attempt = ATTEMPTS.get(attempt_id)
    charge = CHARGES.get(charge_id)
    if setting is None:
        return f"Unknown place: {place}."
    if attempt is None:
        return f"Unknown attempt: {attempt_id}."
    if charge is None:
        return f"Unknown charged object: {charge_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if attempt_id not in setting.affords:
        return f"{setting.label} does not support {attempt.label}."
    if not at_risk(attempt, charge):
        return f"The {attempt.label} would not honestly threaten the {charge.label}."
    if select_safety(attempt, charge) is None:
        return f"No safety method protects the {charge.label} from that attempt."
    return "The requested options are reasonable."


def do_attempt(world: World, hero: Entity, attempt: Attempt, *, narrate: bool) -> None:
    world.active_attempt = attempt.id
    hero.meters[attempt.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {attempt.gerund}.")
    propagate(world, narrate=narrate)


def predict_harm(world: World, hero: Entity, attempt: Attempt, charge: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_attempt(sim, sim.get(hero.id), attempt, narrate=False)
    sim_charge = sim.get(charge.id)
    friend = sim.get(str(sim.facts["friend"]))
    return {
        "harmed": sim_charge.meters["harmed"] >= THRESHOLD,
        "needs_care": sim_charge.meters["needs_care"] >= THRESHOLD,
        "friend_worry": friend.memes["worry"] >= THRESHOLD,
        "warning": attempt.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} young fox named {hero.label} who lived near {world.setting.line}."
    )
    world.say(f"{world.setting.pond_line} {friend.label} had heard a squeak and looked worried.")
    world.say(f"{hero.label} thought, \"A good animal helps first and asks later.\"")
    hero.memes["helpfulness"] += 1
    friend.memes["trust"] += 1
    elder.memes["care"] += 1


def place_charge(world: World, charge_cfg: Charge) -> Entity:
    charge = world.add(
        Entity(
            charge_cfg.id,
            "charge",
            charge_cfg.label,
            zone=charge_cfg.zone,
            guards=set(charge_cfg.vulnerable),
        )
    )
    world.say(f"Near the rusty door and icy pond was a {charge_cfg.full_label}, but nobody understood it yet.")
    world.facts["charge"] = charge.id
    return charge


def misunderstand(world: World, hero: Entity, attempt: Attempt) -> None:
    world.break_para()
    world.say(f"{hero.label} thought the problem was {attempt.mistaken_need} and {attempt.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"Helping fast is the same as helping well.\"")
    hero.memes["hurry"] += 1


def warn(world: World, hero: Entity, elder: Entity, attempt: Attempt, charge: Entity) -> None:
    prediction = predict_harm(world, hero, attempt, charge)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {attempt.label}, you may {prediction["warning"]}. '
        f'The kindest help starts gently."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} looked from the rusty door to the icy pond and puffed out a worried breath.")
    world.say(f'"But I am trying to help," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_safety(world: World, hero: Entity, friend: Entity, attempt: Attempt, charge_cfg: Charge) -> Safety:
    safety = select_safety(attempt, charge_cfg)
    if safety is None:
        raise StoryError("No safety method can make this rusty-door story reasonable.")
    charge = world.get(str(world.facts["charge"]))
    world.break_para()
    world.add(
        Entity(
            safety.id,
            "safety",
            safety.label,
            covers=set(safety.covers),
            guards=set(safety.guards),
            used_on=charge.id,
            protective=True,
        )
    )
    world.say(f"{friend.label} pointed out a slower way to help.")
    world.say(f'"Let us {safety.advice}," {friend.label} said.')
    world.say(f"So {hero.label} {safety.action}.")
    hero.memes["patience"] += 1
    friend.memes["relief"] += 1
    world.facts["safety"] = safety.id
    return safety


def resolve(world: World, hero: Entity, friend: Entity, elder: Entity, attempt: Attempt, charge: Entity) -> None:
    charge_cfg = CHARGES[str(world.facts["charge"])]
    do_attempt(world, hero, attempt, narrate=False)
    if charge.meters["harmed"] < THRESHOLD:
        world.say(charge_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["lesson"] += 1
    friend.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} learned the moral: kind help should be careful help.")
    world.say(f"The icy pond stayed safe, and the rusty door did not need to be fought.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    attempt = ATTEMPTS[params.attempt]
    charge_cfg = CHARGES[params.charge]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "friend": friend.id, "elder": elder.id, "attempt": attempt.id, "place": setting.id})
    introduce(world, hero, friend, elder, params.trait)
    charge = place_charge(world, charge_cfg)
    misunderstand(world, hero, attempt)
    warn(world, hero, elder, attempt, charge)
    pause_conflict(world, hero)
    choose_safety(world, hero, friend, attempt, charge_cfg)
    resolve(world, hero, friend, elder, attempt, charge)
    return world


@dataclass
class StoryParams:
    place: str
    attempt: str
    charge: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("pond_shed", "yank_door", "duck_nest", "Fern", "girl", "Duck", "mother", "helpful", 91),
    StoryParams("reed_bank", "step_ice", "duck_nest", "Bram", "boy", "Turtle", "father", "quick", 92),
    StoryParams("frost_yard", "push_door", "paw_prints", "Mira", "girl", "Otter", "keeper", "kind", 93),
    StoryParams("pond_shed", "yank_door", "turtle_bell", "Eli", "boy", "Mole", "keeper", "curious", 94),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    attempt = ATTEMPTS[str(world.facts["attempt"])]
    charge = CHARGES[str(world.facts["charge"])]
    charge_phrase = charge.label if charge.plural else f"a {charge.label}"
    return [
        'Write an animal story that includes "rusty door" and "icy pond".',
        f"Write a moral-value story where {hero.label} misunderstands {charge_phrase}.",
        f"Write a story where {attempt.gerund} would be unsafe, so careful help solves the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    attempt = ATTEMPTS[str(world.facts["attempt"])]
    charge = world.get(str(world.facts["charge"]))
    charge_cfg = CHARGES[charge.id]
    safety = SAFETIES[str(world.facts["safety"])]
    prediction = dict(world.facts["prediction"])
    verb = "were" if charge_cfg.plural else "was"
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {attempt.gerund} could {prediction['warning']}. "
            f"The warning was predicted before the {charge.label} {verb} harmed.",
        ),
        (
            f"How did {friend.label} help?",
            f"{friend.label} suggested the {safety.label}, which let {hero.label} help more carefully. "
            f"That protected the {charge.label} and kept the icy pond safe.",
        ),
        (
            "What moral did the story teach?",
            f"The story taught that kind help should also be careful help. "
            f"{hero.label} learned to pause before forcing the rusty door or rushing near the icy pond.",
        ),
    ]


KNOWLEDGE = {
    "rusty_door": (
        "Why can a rusty door be hard to open?",
        "Rust can make hinges and latches stick. Pulling too hard can break the door or hurt something nearby.",
    ),
    "icy_pond": (
        "Why should animals be careful near an icy pond?",
        "Ice can be thin near the edge. Careful animals stay on the bank unless an adult knows it is safe.",
    ),
    "animal": (
        "What makes an animal story different?",
        "An animal story uses animal characters to show human-like choices. The lesson is often easier to see through their actions.",
    ),
    "moral": (
        "What is a moral value in a story?",
        "A moral value is a lesson about how to behave. Here, the value is that kindness should be patient and careful.",
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone reads a situation incorrectly. More careful looking can reveal the true problem.",
    ),
    "duck": (
        "Why should nests be left alone?",
        "Nests can hold eggs or young animals. Touching or shaking them can scare the animals or damage the nest.",
    ),
    "turtle": (
        "Why might a small bell help an animal?",
        "A bell can let a small animal signal for help without shouting. It should be checked gently.",
    ),
    "prints": (
        "How can paw prints solve a small mystery?",
        "Paw prints show where an animal walked. They can prove someone left safely.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    attempt = ATTEMPTS[str(world.facts["attempt"])]
    charge = CHARGES[str(world.facts["charge"])]
    safety = SAFETIES[str(world.facts["safety"])]
    tags = set(attempt.tags) | set(charge.tags) | set(safety.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Attempt,Charge) :- attempt_zone(Attempt,Zone), charge_zone(Charge,Zone), risk_of(Attempt,Risk), vulnerable(Charge,Risk).
effective(Attempt,Charge,Safety) :- at_risk(Attempt,Charge), charge_zone(Charge,Zone), covers(Safety,Zone), risk_of(Attempt,Risk), guards(Safety,Risk).
valid(Place,Attempt,Charge,Gender) :- setting(Place), affords(Place,Attempt), charge(Charge), gender(Gender), effective(Attempt,Charge,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for attempt in setting.affords:
            lines.append(asp.fact("affords", place, attempt))
    for attempt_id, attempt in ATTEMPTS.items():
        lines.append(asp.fact("attempt", attempt_id))
        lines.append(asp.fact("risk_of", attempt_id, attempt.risk))
        for zone in attempt.zones:
            lines.append(asp.fact("attempt_zone", attempt_id, zone))
    for charge_id, charge in CHARGES.items():
        lines.append(asp.fact("charge", charge_id))
        lines.append(asp.fact("charge_zone", charge_id, charge.zone))
        for risk in charge.vulnerable:
            lines.append(asp.fact("vulnerable", charge_id, risk))
    for safety_id, safety in SAFETIES.items():
        lines.append(asp.fact("safety", safety_id))
        for zone in safety.covers:
            lines.append(asp.fact("covers", safety_id, zone))
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
        print(f"OK: Python and ASP agree on {len(py)} valid rusty-door stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the rusty-door icy-pond storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--attempt", choices=sorted(ATTEMPTS))
    parser.add_argument("--charge", choices=sorted(CHARGES))
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
    if args.attempt:
        combos = [c for c in combos if c[1] == args.attempt]
    if args.charge:
        combos = [c for c in combos if c[2] == args.charge]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        attempt = args.attempt or next(iter(ATTEMPTS))
        charge = args.charge or next(iter(CHARGES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, attempt, charge, gender))
    place, attempt, charge, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIENDS)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, attempt, charge, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.attempt, params.charge, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.attempt, params.charge, params.gender))
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
        header = f"=== rusty_door_icy_pond #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
