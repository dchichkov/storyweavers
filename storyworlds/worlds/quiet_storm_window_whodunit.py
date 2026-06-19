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
    storm_line: str


@dataclass(frozen=True)
class Search:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    suspect: str
    tags: set[str]


@dataclass(frozen=True)
class Clue:
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
        self.active_search: Optional[str] = None

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

    def methods_for(self, clue: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == clue.id]

    def protected(self, clue: Entity, risk: str) -> bool:
        return any(clue.zone in method.covers and risk in method.guards for method in self.methods_for(clue))


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


def _r_spoil_clue(world: World, narrate: bool) -> bool:
    search_id = world.active_search
    if not search_id:
        return False
    search = SEARCHES[search_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[search.risk] < THRESHOLD:
            continue
        for clue in [e for e in world.entities.values() if e.kind == "clue"]:
            if clue.zone not in search.zones or search.risk not in clue.guards:
                continue
            if world.protected(clue, search.risk):
                continue
            if not _mark(world, "spoil_clue", actor.id, clue.id, search.risk):
                continue
            clue.meters["spoiled"] += 1
            clue.meters["case_lost"] += 1
            changed = True
            if narrate:
                world.say(f"The {clue.label} blurred, and the whodunit grew less fair.")
    return changed


def _r_worry(world: World, narrate: bool) -> bool:
    clue_id = world.facts.get("clue")
    helper_id = world.facts.get("helper")
    if not isinstance(clue_id, str) or not isinstance(helper_id, str):
        return False
    clue = world.get(clue_id)
    helper = world.get(helper_id)
    if clue.meters["case_lost"] < THRESHOLD:
        return False
    if not _mark(world, "helper_worry", clue.id, helper.id):
        return False
    helper.memes["worry"] += 1
    if narrate:
        world.say(f"{helper.label} would still be blamed if the clue disappeared.")
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
        world.say(f"{hero.label} stopped, but the silent window still looked guilty.")
    return True


CAUSAL_RULES = [
    Rule("spoil_clue", _r_spoil_clue),
    Rule("helper_worry", _r_worry),
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
    "attic_room": Setting(
        "attic_room",
        "the attic room",
        "the attic room above the stairs",
        {"wipe_glass", "open_latch"},
        "Outside, a quiet storm flashed without thunder.",
    ),
    "library_nook": Setting(
        "library_nook",
        "the library nook",
        "the library nook beside the tall shelves",
        {"open_latch", "tap_pane"},
        "Rain slid down the glass as silently as a librarian's finger.",
    ),
    "back_hall": Setting(
        "back_hall",
        "the back hall",
        "the back hall where coats hung in a crooked row",
        {"wipe_glass", "tap_pane"},
        "The storm outside was so quiet that every shoe squeak sounded suspicious.",
    ),
}


SEARCHES = {
    "wipe_glass": Search(
        "wipe_glass",
        "wipe the silent window clean",
        "wiping the silent window clean",
        "wanted to wipe the silent window and catch the culprit in the reflection",
        "smear",
        {"glass", "reflection"},
        "smear the magical print before it could answer the case",
        "the candle keeper",
        {"silent_window", "magic", "whodunit"},
    ),
    "open_latch": Search(
        "open_latch",
        "open the window latch",
        "opening the window latch",
        "wanted to open the latch and prove someone slipped outside",
        "scatter",
        {"sill"},
        "scatter the dust clue into the quiet storm",
        "a runaway shadow",
        {"quiet_storm", "misunderstanding", "clue"},
    ),
    "tap_pane": Search(
        "tap_pane",
        "tap the window pane three times",
        "tapping the window pane three times",
        "wanted to tap the pane until the magic confessed",
        "crack",
        {"glass"},
        "crack the hidden spell mark before it speaks",
        "the window itself",
        {"silent_window", "magic", "mystery"},
    ),
}


CLUES = {
    "moon_print": Clue(
        "moon_print",
        "moon print",
        "silver moon print",
        "glass",
        {"smear", "crack"},
        "The moon print showed two tiny mitten marks, not a thief.",
        {"magic", "glass", "misunderstanding"},
    ),
    "dust_arrow": Clue(
        "dust_arrow",
        "dust arrow",
        "thin dust arrow",
        "sill",
        {"scatter"},
        "The dust arrow pointed to a fallen bookmark under the sill.",
        {"dust", "clue", "quiet_storm"},
    ),
    "mirror_note": Clue(
        "mirror_note",
        "mirror note",
        "backward mirror note",
        "reflection",
        {"smear"},
        "The mirror note said, I borrowed the lantern for the hallway.",
        {"reflection", "note", "whodunit"},
    ),
}


METHODS = {
    "breath_ring": Method(
        "breath_ring",
        "breath ring",
        {"glass", "reflection"},
        {"smear", "crack"},
        "breathe a ring around the clue instead of touching it",
        "breathed a careful ring around the clue",
        {"glass", "patience"},
    ),
    "sill_card": Method(
        "sill_card",
        "sill card",
        {"sill"},
        {"scatter"},
        "slide the sill card under the dust before opening anything",
        "slid the sill card under the dust",
        {"dust", "tool"},
    ),
    "soft_knuckle": Method(
        "soft_knuckle",
        "soft-knuckle tap",
        {"glass"},
        {"crack"},
        "tap beside the mark with one soft knuckle",
        "tapped beside the mark with one soft knuckle",
        {"magic", "care"},
    ),
}


NAMES = {"girl": ["Ivy", "Mina", "Nell", "Vera"], "boy": ["Eli", "Jon", "Milo", "Theo"]}
HELPERS = ["Pip", "Rae", "Lena", "Max"]
ELDERS = ["mother", "father", "keeper"]
TRAITS = ["curious", "careful", "bold", "patient"]


def at_risk(search: Search, clue: Clue) -> bool:
    return clue.zone in search.zones and search.risk in clue.vulnerable


def select_method(search: Search, clue: Clue) -> Optional[Method]:
    for method in METHODS.values():
        if clue.zone in method.covers and search.risk in method.guards:
            return method
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for search_id in setting.affords:
            search = SEARCHES[search_id]
            for clue_id, clue in CLUES.items():
                if at_risk(search, clue) and select_method(search, clue) is not None:
                    for gender in GENDERS:
                        out.append((place, search_id, clue_id, gender))
    return sorted(out)


def explain_rejection(place: str, search_id: str, clue_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    search = SEARCHES.get(search_id)
    clue = CLUES.get(clue_id)
    if setting is None:
        return f"Unknown place: {place}."
    if search is None:
        return f"Unknown search: {search_id}."
    if clue is None:
        return f"Unknown clue: {clue_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if search_id not in setting.affords:
        return f"{setting.label} does not support {search.label}."
    if not at_risk(search, clue):
        return f"The {search.label} would not honestly threaten the {clue.label}."
    if select_method(search, clue) is None:
        return f"No observation method protects the {clue.label} from that search."
    return "The requested options are reasonable."


def do_search(world: World, hero: Entity, search: Search, *, narrate: bool) -> None:
    world.active_search = search.id
    hero.meters[search.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {search.gerund}.")
    propagate(world, narrate=narrate)


def predict_spoil(world: World, hero: Entity, search: Search, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_search(sim, sim.get(hero.id), search, narrate=False)
    sim_clue = sim.get(clue.id)
    helper = sim.get(str(sim.facts["helper"]))
    return {
        "spoiled": sim_clue.meters["spoiled"] >= THRESHOLD,
        "case_lost": sim_clue.meters["case_lost"] >= THRESHOLD,
        "helper_worry": helper.memes["worry"] >= THRESHOLD,
        "warning": search.warning,
    }


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child detective named {hero.label}, "
        f"and a quiet storm had carried a whodunit into {world.setting.line}."
    )
    world.say(f"{world.setting.storm_line} The silent window held one bright mark and no explanation.")
    world.say(f"{helper.label} had been blamed for the missing lantern, and {hero.label} wanted the truth.")
    hero.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    elder.memes["care"] += 1


def place_clue(world: World, clue_cfg: Clue) -> Entity:
    clue = world.add(
        Entity(
            clue_cfg.id,
            "clue",
            clue_cfg.label,
            zone=clue_cfg.zone,
            guards=set(clue_cfg.vulnerable),
        )
    )
    world.say(f"On the silent window was a {clue_cfg.full_label}, small and magical enough to be missed.")
    world.facts["clue"] = clue.id
    return clue


def suspect(world: World, hero: Entity, search: Search) -> None:
    world.break_para()
    world.say(f"{hero.label} suspected {search.suspect} and {search.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"A whodunit needs a who, but it needs the clue even more.\"")
    hero.memes["certainty"] += 1


def warn(world: World, hero: Entity, elder: Entity, search: Search, clue: Entity) -> None:
    prediction = predict_spoil(world, hero, search, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {search.label}, you may {prediction["warning"]}. '
        f'Magic clues need gentle questions."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} stared at the quiet storm and tried to keep the theory from running away.")
    world.say(f'"But the window is acting suspicious," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_method(world: World, hero: Entity, helper: Entity, search: Search, clue_cfg: Clue) -> Method:
    method = select_method(search, clue_cfg)
    if method is None:
        raise StoryError("No method can make this silent-window story reasonable.")
    clue = world.get(str(world.facts["clue"]))
    world.break_para()
    world.add(
        Entity(
            method.id,
            "method",
            method.label,
            covers=set(method.covers),
            guards=set(method.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{helper.label} pointed at the clue and offered a calmer method.")
    world.say(f'"Try this: {method.advice}," {helper.label} said.')
    world.say(f"So {hero.label} {method.action}.")
    hero.memes["patience"] += 1
    helper.memes["hope"] += 1
    world.facts["method"] = method.id
    return method


def solve(world: World, hero: Entity, helper: Entity, elder: Entity, search: Search, clue: Entity) -> None:
    clue_cfg = CLUES[str(world.facts["clue"])]
    do_search(world, hero, search, narrate=False)
    if clue.meters["spoiled"] < THRESHOLD:
        world.say(clue_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["relief"] += 1
    helper.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"The misunderstanding cleared: {helper.label} had not taken the lantern at all.")
    world.say(f"{hero.label} closed the case while the quiet storm bowed against the silent window and left the clue shining.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    search = SEARCHES[params.search]
    clue_cfg = CLUES[params.clue]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    helper = world.add(Entity("helper", "character", params.helper, gender="girl"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "helper": helper.id, "elder": elder.id, "search": search.id, "place": setting.id})
    introduce(world, hero, helper, elder, params.trait)
    clue = place_clue(world, clue_cfg)
    suspect(world, hero, search)
    warn(world, hero, elder, search, clue)
    pause_conflict(world, hero)
    choose_method(world, hero, helper, search, clue_cfg)
    solve(world, hero, helper, elder, search, clue)
    return world


@dataclass
class StoryParams:
    place: str
    search: str
    clue: str
    name: str
    gender: str
    helper: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("attic_room", "wipe_glass", "moon_print", "Ivy", "girl", "Pip", "mother", "curious", 81),
    StoryParams("library_nook", "open_latch", "dust_arrow", "Eli", "boy", "Rae", "father", "careful", 82),
    StoryParams("back_hall", "tap_pane", "moon_print", "Nell", "girl", "Lena", "keeper", "bold", 83),
    StoryParams("attic_room", "wipe_glass", "mirror_note", "Theo", "boy", "Max", "keeper", "patient", 84),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    search = SEARCHES[str(world.facts["search"])]
    clue = CLUES[str(world.facts["clue"])]
    return [
        'Write a whodunit story that includes "quiet storm" and "silent window".',
        f"Write a magical misunderstanding story where {hero.label} investigates a {clue.label}.",
        f"Write a story where {search.gerund} would spoil the clue, so the answer comes from gentle observation.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    helper = world.get(str(world.facts["helper"]))
    elder = world.get(str(world.facts["elder"]))
    search = SEARCHES[str(world.facts["search"])]
    clue = world.get(str(world.facts["clue"]))
    method = METHODS[str(world.facts["method"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {search.gerund} could {prediction['warning']}. "
            f"That warning protected the {clue.label} before the case lost its fairest evidence.",
        ),
        (
            f"How did {helper.label} help?",
            f"{helper.label} suggested the {method.label}, which let {hero.label} question the clue gently. "
            f"That kept the magical evidence intact.",
        ),
        (
            "What was the misunderstanding?",
            f"{hero.label} thought the case pointed to {search.suspect}. "
            f"The preserved clue showed a different explanation, so {helper.label} was no longer blamed for the lantern.",
        ),
    ]


KNOWLEDGE = {
    "quiet_storm": (
        "What could a quiet storm mean in a magical story?",
        "A quiet storm can mean a storm with light, rain, or wind but little sound. In a magical story, that silence can make small clues feel important.",
    ),
    "silent_window": (
        "Why is a window useful in a mystery?",
        "A window can hold fingerprints, reflections, dust, or marks. It can show what happened without speaking.",
    ),
    "magic": (
        "Why should magical clues be handled gently?",
        "Magical clues may change when touched or rushed. Careful observation keeps the clue stable enough to understand.",
    ),
    "misunderstanding": (
        "What is a misunderstanding?",
        "A misunderstanding happens when someone explains the facts the wrong way. More evidence can correct the first guess.",
    ),
    "whodunit": (
        "What is a whodunit?",
        "A whodunit is a mystery focused on discovering who caused a problem. The solution should come from clues, not guessing.",
    ),
    "glass": (
        "Why can glass clues smear?",
        "Marks on glass can smear when wiped or touched. Looking from an angle can protect them.",
    ),
    "dust": (
        "Why can dust be a clue?",
        "Dust can show arrows, footprints, or where something moved. It is easy to scatter, so it needs careful handling.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    search = SEARCHES[str(world.facts["search"])]
    clue = CLUES[str(world.facts["clue"])]
    method = METHODS[str(world.facts["method"])]
    tags = set(search.tags) | set(clue.tags) | set(method.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Search,Clue) :- search_zone(Search,Zone), clue_zone(Clue,Zone), risk_of(Search,Risk), vulnerable(Clue,Risk).
effective(Search,Clue,Method) :- at_risk(Search,Clue), clue_zone(Clue,Zone), covers(Method,Zone), risk_of(Search,Risk), guards(Method,Risk).
valid(Place,Search,Clue,Gender) :- setting(Place), affords(Place,Search), clue(Clue), gender(Gender), effective(Search,Clue,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for search in setting.affords:
            lines.append(asp.fact("affords", place, search))
    for search_id, search in SEARCHES.items():
        lines.append(asp.fact("search", search_id))
        lines.append(asp.fact("risk_of", search_id, search.risk))
        for zone in search.zones:
            lines.append(asp.fact("search_zone", search_id, zone))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_zone", clue_id, clue.zone))
        for risk in clue.vulnerable:
            lines.append(asp.fact("vulnerable", clue_id, risk))
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
        print(f"OK: Python and ASP agree on {len(py)} valid quiet-storm stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the quiet-storm window whodunit storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--search", choices=sorted(SEARCHES))
    parser.add_argument("--clue", choices=sorted(CLUES))
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
    if args.search:
        combos = [c for c in combos if c[1] == args.search]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        search = args.search or next(iter(SEARCHES))
        clue = args.clue or next(iter(CLUES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, search, clue, gender))
    place, search, clue, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice([h for h in HELPERS if h != name])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, search, clue, name, gender, helper, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.search, params.clue, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.search, params.clue, params.gender))
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
        header = f"=== quiet_storm_window_whodunit #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
