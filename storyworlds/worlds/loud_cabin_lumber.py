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
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    installed_for: Optional[str] = None
    caretaker: Optional[str] = None
    protective: bool = False

    def pronoun(self, case: str) -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
            "mother": {"subject": "she", "object": "her", "possessive": "her"},
            "father": {"subject": "he", "object": "him", "possessive": "his"},
            "aunt": {"subject": "she", "object": "her", "possessive": "her"},
            "uncle": {"subject": "he", "object": "him", "possessive": "his"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    sound_line: str


@dataclass(frozen=True)
class Work:
    id: str
    label: str
    gerund: str
    wish: str
    risk: str
    zones: set[str]
    warning: str
    tags: set[str]


@dataclass(frozen=True)
class Home:
    id: str
    label: str
    full_label: str
    zone: str
    vulnerable: set[str]
    occupant: str
    tags: set[str]


@dataclass(frozen=True)
class QuietFix:
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
        self.active_work: Optional[str] = None

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

    def fixes_for(self, home: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.installed_for == home.id]

    def protected(self, home: Entity, risk: str) -> bool:
        return any(home.zone in fix.covers and risk in fix.guards for fix in self.fixes_for(home))


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


def _r_disturb_home(world: World, narrate: bool) -> bool:
    work_id = world.active_work
    if not work_id:
        return False
    work = WORKS[work_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[work.risk] < THRESHOLD:
            continue
        for home in [e for e in world.entities.values() if e.kind == "home"]:
            if home.zone not in work.zones or work.risk not in home.guards:
                continue
            if world.protected(home, work.risk):
                continue
            if not _mark(world, "disturb_home", actor.id, home.id, work.risk):
                continue
            home.meters["disturbed"] += 1
            home.meters["needs_care"] += 1
            changed = True
            if narrate:
                world.say(f"The {home.label} shook, and its quiet was broken.")
    return changed


def _r_friend_worry(world: World, narrate: bool) -> bool:
    home_id = world.facts.get("home")
    friend_id = world.facts.get("friend")
    if not isinstance(home_id, str) or not isinstance(friend_id, str):
        return False
    home = world.get(home_id)
    friend = world.get(friend_id)
    if home.meters["needs_care"] < THRESHOLD:
        return False
    if not _mark(world, "friend_worry", home.id, friend.id):
        return False
    friend.memes["worry"] += 1
    if narrate:
        world.say(f"{friend.label} would have to calm the {home.label} again.")
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
        world.say(f"{hero.label} stopped, but {hero.pronoun('possessive')} hurry was still thumping inside.")
    return True


CAUSAL_RULES = [
    Rule("disturb_home", _r_disturb_home),
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
    "loud_cabin": Setting(
        "loud_cabin",
        "the loud cabin",
        "the loud cabin at the edge of the pine woods",
        {"saw_lumber", "drop_lumber"},
        "Every wall in that cabin answered a tap with three taps back.",
    ),
    "creek_workbench": Setting(
        "creek_workbench",
        "the creek workbench",
        "a workbench beside the creek where boards dried in the sun",
        {"saw_lumber", "drag_lumber"},
        "The creek carried every sound downstream like a silver string.",
    ),
    "hollow_stump": Setting(
        "hollow_stump",
        "the hollow stump shop",
        "a stump shop full of curled shavings and cedar smell",
        {"drop_lumber", "drag_lumber"},
        "The hollow stump made even a whisper sound round and large.",
    ),
}


WORKS = {
    "saw_lumber": Work(
        "saw_lumber",
        "saw the lumber",
        "sawing the lumber",
        "wanted to saw the lumber quickly before sunset",
        "rattle",
        {"rafters", "wall"},
        "rattle the little home until everyone inside wakes up",
        {"lumber", "noise", "cabin", "care"},
    ),
    "drop_lumber": Work(
        "drop_lumber",
        "drop the lumber stack",
        "dropping the lumber stack",
        "wanted to drop the lumber stack all at once and be done",
        "thump",
        {"floor", "wall"},
        "thump hard enough to scare the little home",
        {"lumber", "tumble", "noise", "cabin"},
    ),
    "drag_lumber": Work(
        "drag_lumber",
        "drag the lumber across the boards",
        "dragging the lumber across the boards",
        "wanted to drag the lumber straight across the floor",
        "scrape",
        {"floor"},
        "scrape so loudly that the quiet home cannot rest",
        {"lumber", "noise", "patience"},
    ),
}


HOMES = {
    "mouse_nest": Home(
        "mouse_nest",
        "mouse nest",
        "soft mouse nest",
        "wall",
        {"rattle", "thump"},
        "Mina Mouse",
        {"mouse", "nest", "animal"},
    ),
    "owl_roost": Home(
        "owl_roost",
        "owl roost",
        "sleepy owl roost",
        "rafters",
        {"rattle"},
        "Ollie Owl",
        {"owl", "roost", "animal"},
    ),
    "rabbit_bed": Home(
        "rabbit_bed",
        "rabbit bed",
        "grass-lined rabbit bed",
        "floor",
        {"thump", "scrape"},
        "Rory Rabbit",
        {"rabbit", "bed", "animal"},
    ),
}


FIXES = {
    "moss_pads": QuietFix(
        "moss_pads",
        "moss pads",
        {"floor", "wall"},
        {"thump", "scrape"},
        "put moss pads under the lumber first",
        "tucked moss pads under the lumber",
        {"moss", "quiet"},
    ),
    "cloth_saw": QuietFix(
        "cloth_saw",
        "cloth saw wrap",
        {"rafters", "wall"},
        {"rattle"},
        "wrap the saw handle and work in slow strokes",
        "wrapped the saw handle and worked in slow strokes",
        {"tool", "quiet"},
    ),
    "rope_slide": QuietFix(
        "rope_slide",
        "rope slide",
        {"floor"},
        {"scrape", "thump"},
        "slide the lumber along the rope instead",
        "slid the lumber along the rope",
        {"rope", "lumber"},
    ),
}


NAMES = {"girl": ["Bea", "Lila", "Nora", "Tilly"], "boy": ["Bram", "Milo", "Otto", "Pip"]}
FRIENDS = ["Mina", "Ollie", "Rory", "Fern"]
ELDERS = ["mother", "father", "aunt", "uncle"]
TRAITS = ["busy", "kind", "small", "careful"]


def at_risk(work: Work, home: Home) -> bool:
    return home.zone in work.zones and work.risk in home.vulnerable


def select_fix(work: Work, home: Home) -> Optional[QuietFix]:
    for fix in FIXES.values():
        if home.zone in fix.covers and work.risk in fix.guards:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for work_id in setting.affords:
            work = WORKS[work_id]
            for home_id, home in HOMES.items():
                if at_risk(work, home) and select_fix(work, home) is not None:
                    for gender in GENDERS:
                        out.append((place, work_id, home_id, gender))
    return sorted(out)


def explain_rejection(place: str, work_id: str, home_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    work = WORKS.get(work_id)
    home = HOMES.get(home_id)
    if setting is None:
        return f"Unknown place: {place}."
    if work is None:
        return f"Unknown lumber work: {work_id}."
    if home is None:
        return f"Unknown animal home: {home_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if work_id not in setting.affords:
        return f"{setting.label} does not support {work.label}."
    if not at_risk(work, home):
        return f"The {work.label} would not honestly disturb the {home.label}."
    if select_fix(work, home) is None:
        return f"No quiet fix protects the {home.label} from that lumber work."
    return "The requested options are reasonable."


def do_work(world: World, hero: Entity, work: Work, *, narrate: bool) -> None:
    world.active_work = work.id
    hero.meters[work.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {work.gerund}.")
    propagate(world, narrate=narrate)


def predict_disturbance(world: World, hero: Entity, work: Work, home: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_work(sim, sim.get(hero.id), work, narrate=False)
    sim_home = sim.get(home.id)
    friend = sim.get(str(sim.facts["friend"]))
    return {
        "disturbed": sim_home.meters["disturbed"] >= THRESHOLD,
        "needs_care": sim_home.meters["needs_care"] >= THRESHOLD,
        "friend_worry": friend.memes["worry"] >= THRESHOLD,
        "warning": work.warning,
    }


def introduce(world: World, hero: Entity, friend: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} young beaver named {hero.label} "
        f"who helped carry lumber near {world.setting.line}."
    )
    world.say(f"{world.setting.sound_line} {hero.label} thought, \"A loud cabin can still build a kind thing.\"")
    world.say(f"{friend.label} was {hero.label}'s animal friend, and quiet mattered to that friend.")
    hero.memes["kindness"] += 1
    friend.memes["trust"] += 1
    elder.memes["care"] += 1


def place_home(world: World, friend: Entity, home_cfg: Home) -> Entity:
    home = world.add(
        Entity(
            home_cfg.id,
            "home",
            home_cfg.label,
            zone=home_cfg.zone,
            guards=set(home_cfg.vulnerable),
            caretaker=friend.id,
        )
    )
    world.say(f"Nearby was a {home_cfg.full_label} where {friend.label} liked to rest.")
    world.facts["home"] = home.id
    return home


def want_work(world: World, hero: Entity, work: Work) -> None:
    world.break_para()
    world.say(f"That afternoon, {hero.label} {work.wish}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"If I finish fast, everyone will see I am helpful.\"")
    hero.memes["hurry"] += 1


def warn(world: World, hero: Entity, elder: Entity, work: Work, home: Entity) -> None:
    prediction = predict_disturbance(world, hero, work, home)
    world.facts["prediction"] = prediction
    friend = world.get(str(world.facts["friend"]))
    world.say(
        f'"Wait," said {elder.label}. "If you {work.label}, you may {prediction["warning"]}. '
        f'Then {friend.label} will have to make everything calm again."'
    )
    elder.memes["caution"] += 1


def resist(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} looked at the lumber and felt the hurry knocking in {hero.pronoun('possessive')} chest.")
    world.say(f'"I only want to help," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def compromise(world: World, hero: Entity, friend: Entity, work: Work, home_cfg: Home) -> QuietFix:
    fix = select_fix(work, home_cfg)
    if fix is None:
        raise StoryError("No quiet fix can make this lumber story reasonable.")
    home = world.get(str(world.facts["home"]))
    world.break_para()
    world.add(
        Entity(
            fix.id,
            "fix",
            fix.label,
            covers=set(fix.covers),
            guards=set(fix.guards),
            installed_for=home.id,
            protective=True,
        )
    )
    world.say(f"{friend.label} padded over with a quieter idea.")
    world.say(f'"Please {fix.advice}," {friend.label} said. "Kind work should sound kind, too."')
    world.say(f"So {hero.label} {fix.action}.")
    hero.memes["patience"] += 1
    friend.memes["kindness"] += 1
    world.facts["fix"] = fix.id
    return fix


def finish(world: World, hero: Entity, friend: Entity, elder: Entity, work: Work, home: Entity) -> None:
    do_work(world, hero, work, narrate=False)
    if home.meters["disturbed"] < THRESHOLD:
        world.say(f"The {home.label} stayed quiet while the lumber moved where it needed to go.")
    hero.memes["conflict"] = 0
    hero.memes["relief"] += 1
    friend.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} thought, \"I can be useful without being loud.\"")
    world.say(f"And in the loud cabin, that was the kindest sound of all.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    work = WORKS[params.work]
    home_cfg = HOMES[params.home]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    friend = world.add(Entity("friend", "character", params.friend, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "friend": friend.id, "elder": elder.id, "work": work.id, "place": setting.id})
    introduce(world, hero, friend, elder, params.trait)
    home = place_home(world, friend, home_cfg)
    want_work(world, hero, work)
    warn(world, hero, elder, work, home)
    resist(world, hero)
    compromise(world, hero, friend, work, home_cfg)
    finish(world, hero, friend, elder, work, home)
    return world


@dataclass
class StoryParams:
    place: str
    work: str
    home: str
    name: str
    gender: str
    friend: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("loud_cabin", "saw_lumber", "mouse_nest", "Bram", "boy", "Mina", "mother", "kind", 31),
    StoryParams("creek_workbench", "drag_lumber", "rabbit_bed", "Lila", "girl", "Rory", "father", "careful", 32),
    StoryParams("hollow_stump", "drop_lumber", "rabbit_bed", "Otto", "boy", "Fern", "aunt", "busy", 33),
    StoryParams("loud_cabin", "saw_lumber", "owl_roost", "Nora", "girl", "Ollie", "uncle", "small", 34),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    work = WORKS[str(world.facts["work"])]
    home = HOMES[str(world.facts["home"])]
    return [
        'Write an animal story that includes the words "lumber" and "loud cabin".',
        f"Write a story about {hero.label}, inner monologue, and {work.gerund} without disturbing a {home.label}.",
        "Write a story where a young animal learns that helpful work can also be quiet work.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    friend = world.get(str(world.facts["friend"]))
    elder = world.get(str(world.facts["elder"]))
    work = WORKS[str(world.facts["work"])]
    home = world.get(str(world.facts["home"]))
    fix = FIXES[str(world.facts["fix"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {work.gerund} could {prediction['warning']}. "
            f"The problem was predicted before the {home.label} was actually disturbed.",
        ),
        (
            f"How did {friend.label} help?",
            f"{friend.label} brought the {fix.label} and asked for quieter work. "
            f"That protected the {home.label} and let {hero.label} keep helping.",
        ),
        (
            "What did the young animal think by the end?",
            f"{hero.label} thought that being useful did not have to mean being loud. "
            f"That inner change resolved the conflict and kept {friend.label}'s quiet place safe.",
        ),
    ]


KNOWLEDGE = {
    "lumber": (
        "What is lumber?",
        "Lumber is wood that has been cut into boards or beams. It is often used to build cabins, bridges, shelves, and other useful things.",
    ),
    "noise": (
        "Why can loud work bother small animals?",
        "Small animals can be sensitive to sudden sounds and shaking. Loud work near a nest or bed can make them feel unsafe.",
    ),
    "cabin": (
        "Why can a cabin sound loud inside?",
        "A small wooden cabin can echo knocks and footsteps. Wood can carry sound through walls, floors, and rafters.",
    ),
    "quiet": (
        "How can workers make noisy work quieter?",
        "Workers can move slowly, add padding, use softer tools, or slide heavy things instead of dropping them. Those choices reduce sudden sound.",
    ),
    "mouse": (
        "Why does a mouse need a quiet nest?",
        "A mouse nest is a small resting place. Quiet helps the mouse feel hidden and safe.",
    ),
    "owl": (
        "Why might an owl roost during the day?",
        "Many owls are active at night and rest during the day. A quiet roost helps them sleep.",
    ),
    "rabbit": (
        "Why can thumping scare a rabbit?",
        "Rabbits notice vibrations and sudden sounds quickly. A hard thump can make a rabbit think danger is nearby.",
    ),
    "moss": (
        "Why is moss useful as padding?",
        "Moss is soft and springy. It can cushion a hard object and make movement quieter.",
    ),
    "rope": (
        "How can a rope help move lumber?",
        "A rope can guide or slide heavy lumber more smoothly. That can reduce scraping and sudden drops.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    work = WORKS[str(world.facts["work"])]
    home = HOMES[str(world.facts["home"])]
    fix = FIXES[str(world.facts["fix"])]
    tags = set(work.tags) | set(home.tags) | set(fix.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Work,Home) :- work_zone(Work,Zone), home_zone(Home,Zone), risk_of(Work,Risk), vulnerable(Home,Risk).
effective(Work,Home,Fix) :- at_risk(Work,Home), home_zone(Home,Zone), covers(Fix,Zone), risk_of(Work,Risk), guards(Fix,Risk).
valid(Place,Work,Home,Gender) :- setting(Place), affords(Place,Work), home(Home), gender(Gender), effective(Work,Home,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for work in setting.affords:
            lines.append(asp.fact("affords", place, work))
    for work_id, work in WORKS.items():
        lines.append(asp.fact("work", work_id))
        lines.append(asp.fact("risk_of", work_id, work.risk))
        for zone in work.zones:
            lines.append(asp.fact("work_zone", work_id, zone))
    for home_id, home in HOMES.items():
        lines.append(asp.fact("home", home_id))
        lines.append(asp.fact("home_zone", home_id, home.zone))
        for risk in home.vulnerable:
            lines.append(asp.fact("vulnerable", home_id, risk))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for zone in fix.covers:
            lines.append(asp.fact("covers", fix_id, zone))
        for risk in fix.guards:
            lines.append(asp.fact("guards", fix_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid lumber-cabin stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the loud-cabin lumber storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--work", choices=sorted(WORKS))
    parser.add_argument("--home", choices=sorted(HOMES))
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
    if args.work:
        combos = [c for c in combos if c[1] == args.work]
    if args.home:
        combos = [c for c in combos if c[2] == args.home]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        work = args.work or next(iter(WORKS))
        home = args.home or next(iter(HOMES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, work, home, gender))
    place, work, home, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(FRIENDS)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, work, home, name, gender, friend, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.work, params.home, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.work, params.home, params.gender))
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
        if entity.installed_for:
            parts.append(f"installed_for={entity.installed_for}")
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
        header = f"=== loud_cabin_lumber #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
