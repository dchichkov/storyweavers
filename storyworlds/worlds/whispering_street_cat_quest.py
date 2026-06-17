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
            "grandmother": {"subject": "she", "object": "her", "possessive": "her"},
        }
        return table.get(self.gender or self.kind, table["girl"])[case]


@dataclass(frozen=True)
class Setting:
    id: str
    label: str
    line: str
    affords: set[str]
    foreshadow: str


@dataclass(frozen=True)
class QuestStep:
    id: str
    label: str
    gerund: str
    urge: str
    risk: str
    zones: set[str]
    warning: str
    quest_guess: str
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
class Aid:
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
        self.active_step: Optional[str] = None

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

    def aids_for(self, clue: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.protective and e.used_on == clue.id]

    def protected(self, clue: Entity, risk: str) -> bool:
        return any(clue.zone in aid.covers and risk in aid.guards for aid in self.aids_for(clue))


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
    step_id = world.active_step
    if not step_id:
        return False
    step = STEPS[step_id]
    changed = False
    for actor in [e for e in world.entities.values() if e.kind == "character"]:
        if actor.meters[step.risk] < THRESHOLD:
            continue
        for clue in [e for e in world.entities.values() if e.kind == "clue"]:
            if clue.zone not in step.zones or step.risk not in clue.guards:
                continue
            if world.protected(clue, step.risk):
                continue
            if not _mark(world, "spoil_clue", actor.id, clue.id, step.risk):
                continue
            clue.meters["spoiled"] += 1
            clue.meters["quest_lost"] += 1
            changed = True
            if narrate:
                world.say(f"The {clue.label} was spoiled, and the quiet quest almost lost its way.")
    return changed


def _r_cat_worry(world: World, narrate: bool) -> bool:
    clue_id = world.facts.get("clue")
    cat_id = world.facts.get("cat")
    if not isinstance(clue_id, str) or not isinstance(cat_id, str):
        return False
    clue = world.get(clue_id)
    cat = world.get(cat_id)
    if clue.meters["quest_lost"] < THRESHOLD:
        return False
    if not _mark(world, "cat_worry", clue.id, cat.id):
        return False
    cat.memes["worry"] += 1
    if narrate:
        world.say(f"{cat.label} would have no gentle clue to follow.")
    return True


def _r_conflict(world: World, narrate: bool) -> bool:
    hero_id = world.facts.get("hero")
    elder_id = world.facts.get("elder")
    if not isinstance(hero_id, str) or not isinstance(elder_id, str):
        return False
    hero = world.get(hero_id)
    elder = world.get(elder_id)
    if hero.memes["haste"] < THRESHOLD or hero.meters["stopped"] < THRESHOLD:
        return False
    if not _mark(world, "conflict", hero.id, elder.id):
        return False
    hero.memes["conflict"] += 1
    elder.memes["concern"] += 1
    if narrate:
        world.say(f"{hero.label} stopped, but the bedtime quest still tugged at {hero.pronoun('possessive')} feet.")
    return True


CAUSAL_RULES = [
    Rule("spoil_clue", _r_spoil_clue),
    Rule("cat_worry", _r_cat_worry),
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
    "lamp_corner": Setting(
        "lamp_corner",
        "the lamp corner",
        "a painted whispering street",
        {"follow_cat", "step_pond"},
        "The whispering cat blinked twice whenever the gentle path was the right path.",
    ),
    "window_rug": Setting(
        "window_rug",
        "the window rug",
        "the rug-road under the sleepy window",
        {"lift_moss", "follow_cat"},
        "Moonlight touched the fuzzy pond before the cat said a word.",
    ),
    "pillow_bridge": Setting(
        "pillow_bridge",
        "the pillow bridge",
        "the pillow bridge beside the toy houses",
        {"step_pond", "lift_moss"},
        "A silver button glimmered once, then hid, as if bedtime had secrets.",
    ),
}


STEPS = {
    "follow_cat": QuestStep(
        "follow_cat",
        "chase the whispering cat down the street",
        "chasing the whispering cat down the street",
        "wanted to chase the whispering cat before it vanished",
        "startle",
        {"street", "collar"},
        "startle the guide and shake loose the true clue",
        "the cat knows where the moon button went",
        {"whispering_cat", "whispering_street", "quest"},
    ),
    "step_pond": QuestStep(
        "step_pond",
        "step onto the fuzzy pond edge",
        "stepping onto the fuzzy pond edge",
        "wanted to step onto the fuzzy pond edge for a shortcut",
        "sink",
        {"pond", "edge"},
        "sink the soft clue under the blanket water",
        "the pond is only pretend, so it must be safe",
        {"fuzzy_pond", "bedtime", "quest"},
    ),
    "lift_moss": QuestStep(
        "lift_moss",
        "lift the fuzzy moss in one handful",
        "lifting the fuzzy moss in one handful",
        "wanted to lift the fuzzy moss and finish the quest",
        "tangle",
        {"moss"},
        "tangle the hidden clue before it can point home",
        "the moss was hiding a monster crumb",
        {"fuzzy_pond", "foreshadowing", "clue"},
    ),
}


CLUES = {
    "moon_button": Clue(
        "moon_button",
        "moon button",
        "sleepy moon button",
        "pond",
        {"sink"},
        "The moon button was under the fuzzy pond edge, waiting to be sewn back on the blanket.",
        {"moon", "bedtime", "pond"},
    ),
    "collar_bell": Clue(
        "collar_bell",
        "collar bell",
        "tiny collar bell",
        "collar",
        {"startle"},
        "The collar bell rang softly toward the missing bedtime sock.",
        {"cat", "bell", "quest"},
    ),
    "thread_arrow": Clue(
        "thread_arrow",
        "thread arrow",
        "silver thread arrow",
        "moss",
        {"tangle"},
        "The thread arrow pointed to the pillow bridge and the lost goodnight star.",
        {"thread", "foreshadowing", "bedtime"},
    ),
}


AIDS = {
    "quiet_steps": Aid(
        "quiet_steps",
        "quiet steps",
        {"street", "collar"},
        {"startle"},
        "Take three quiet steps and let the cat lead",
        "took three quiet steps and let the cat lead",
        {"cat", "patience"},
    ),
    "reed_mat": Aid(
        "reed_mat",
        "reed mat",
        {"pond", "edge"},
        {"sink"},
        "Lay the reed mat on the pond edge first",
        "laid the reed mat on the pond edge",
        {"pond", "safety"},
    ),
    "moss_comb": Aid(
        "moss_comb",
        "moss comb",
        {"moss"},
        {"tangle"},
        "Comb the moss slowly instead of grabbing it",
        "combed the moss slowly",
        {"moss", "care"},
    ),
}


NAMES = {"girl": ["Ada", "Lena", "Mira", "Nell"], "boy": ["Ben", "Eli", "Jon", "Theo"]}
CAT_NAMES = ["Muffin", "Pip", "Velvet", "Nim"]
ELDERS = ["mother", "father", "grandmother"]
TRAITS = ["sleepy", "curious", "gentle", "quick"]


def at_risk(step: QuestStep, clue: Clue) -> bool:
    return clue.zone in step.zones and step.risk in clue.vulnerable


def select_aid(step: QuestStep, clue: Clue) -> Optional[Aid]:
    for aid in AIDS.values():
        if clue.zone in aid.covers and step.risk in aid.guards:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for step_id in setting.affords:
            step = STEPS[step_id]
            for clue_id, clue in CLUES.items():
                if at_risk(step, clue) and select_aid(step, clue) is not None:
                    for gender in GENDERS:
                        out.append((place, step_id, clue_id, gender))
    return sorted(out)


def explain_rejection(place: str, step_id: str, clue_id: str, gender: str) -> str:
    setting = SETTINGS.get(place)
    step = STEPS.get(step_id)
    clue = CLUES.get(clue_id)
    if setting is None:
        return f"Unknown place: {place}."
    if step is None:
        return f"Unknown quest step: {step_id}."
    if clue is None:
        return f"Unknown clue: {clue_id}."
    if gender not in GENDERS:
        return f"Unknown gender: {gender}."
    if step_id not in setting.affords:
        return f"{setting.label} does not support {step.label}."
    if not at_risk(step, clue):
        return f"The {step.label} would not honestly threaten the {clue.label}."
    if select_aid(step, clue) is None:
        return f"No gentle aid protects the {clue.label} from that quest step."
    return "The requested options are reasonable."


def do_step(world: World, hero: Entity, step: QuestStep, *, narrate: bool) -> None:
    world.active_step = step.id
    hero.meters[step.risk] += 1
    if narrate:
        world.say(f"{hero.label} started {step.gerund}.")
    propagate(world, narrate=narrate)


def predict_spoil(world: World, hero: Entity, step: QuestStep, clue: Entity) -> dict[str, object]:
    sim = world.copy()
    sim.paragraphs = [[]]
    do_step(sim, sim.get(hero.id), step, narrate=False)
    sim_clue = sim.get(clue.id)
    cat = sim.get(str(sim.facts["cat"]))
    return {
        "spoiled": sim_clue.meters["spoiled"] >= THRESHOLD,
        "quest_lost": sim_clue.meters["quest_lost"] >= THRESHOLD,
        "cat_worry": cat.memes["worry"] >= THRESHOLD,
        "warning": step.warning,
    }


def introduce(world: World, hero: Entity, cat: Entity, elder: Entity, trait: str) -> None:
    world.say(
        f"Once upon a time, there was a {trait} child named {hero.label} who was almost ready for bed."
    )
    world.say(f"On the rug was {world.setting.line}, and beside it waited a fuzzy pond.")
    world.say(f"{world.setting.foreshadow} Then the whispering cat named {cat.label} said, \"Quest, quest, softly best.\"")
    hero.memes["wonder"] += 1
    cat.memes["guidance"] += 1
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
    world.say(f"Somewhere in the bedtime map was a {clue_cfg.full_label}, but the quest had not found it yet.")
    world.facts["clue"] = clue.id
    return clue


def want_quest(world: World, hero: Entity, step: QuestStep) -> None:
    world.break_para()
    world.say(f"{hero.label} believed that {step.quest_guess} and {step.urge}.")
    world.say(f"Inside, {hero.pronoun('subject')} thought, \"A quest is quicker if I hurry.\"")
    hero.memes["haste"] += 1


def warn(world: World, hero: Entity, elder: Entity, step: QuestStep, clue: Entity) -> None:
    prediction = predict_spoil(world, hero, step, clue)
    world.facts["prediction"] = prediction
    world.say(
        f'"Wait," said {elder.label}. "If you {step.label}, you may {prediction["warning"]}. '
        f'Bedtime quests like gentle feet."'
    )
    elder.memes["caution"] += 1


def pause_conflict(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} looked from the whispering street to the fuzzy pond and held still.")
    world.say(f'"But the whispering cat is waiting," {hero.pronoun("subject")} said.')
    hero.meters["stopped"] += 1
    propagate(world, narrate=True)


def choose_aid(world: World, hero: Entity, cat: Entity, step: QuestStep, clue_cfg: Clue) -> Aid:
    aid = select_aid(step, clue_cfg)
    if aid is None:
        raise StoryError("No aid can make this bedtime quest reasonable.")
    clue = world.get(str(world.facts["clue"]))
    world.break_para()
    world.add(
        Entity(
            aid.id,
            "aid",
            aid.label,
            covers=set(aid.covers),
            guards=set(aid.guards),
            used_on=clue.id,
            protective=True,
        )
    )
    world.say(f"{cat.label} curled {cat.pronoun('possessive')} tail around a better idea.")
    world.say(f'"{aid.advice}," whispered {cat.label}.')
    world.say(f"So {hero.label} {aid.action}.")
    hero.memes["patience"] += 1
    cat.memes["trust"] += 1
    world.facts["aid"] = aid.id
    return aid


def finish(world: World, hero: Entity, cat: Entity, elder: Entity, step: QuestStep, clue: Entity) -> None:
    clue_cfg = CLUES[str(world.facts["clue"])]
    do_step(world, hero, step, narrate=False)
    if clue.meters["spoiled"] < THRESHOLD:
        world.say(clue_cfg.reveal)
    hero.memes["conflict"] = 0
    hero.memes["sleepy_joy"] += 1
    cat.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.say(f"{hero.label} yawned, and {cat.label} purred, \"Quest, quest, softly best.\"")
    world.say(f"The whispering street grew quiet, the fuzzy pond lay still, and bedtime was ready.")
    world.facts["resolved"] = True


def tell(params: "StoryParams") -> World:
    setting = SETTINGS[params.place]
    step = STEPS[params.step]
    clue_cfg = CLUES[params.clue]
    world = World(setting)
    hero = world.add(Entity("hero", "character", params.name, gender=params.gender))
    cat = world.add(Entity("cat", "cat", params.cat, gender="cat"))
    elder = world.add(Entity("elder", "character", params.elder.title(), gender=params.elder))
    world.facts.update({"hero": hero.id, "cat": cat.id, "elder": elder.id, "step": step.id, "place": setting.id})
    introduce(world, hero, cat, elder, params.trait)
    clue = place_clue(world, clue_cfg)
    want_quest(world, hero, step)
    warn(world, hero, elder, step, clue)
    pause_conflict(world, hero)
    choose_aid(world, hero, cat, step, clue_cfg)
    finish(world, hero, cat, elder, step, clue)
    return world


@dataclass
class StoryParams:
    place: str
    step: str
    clue: str
    name: str
    gender: str
    cat: str
    elder: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams("lamp_corner", "follow_cat", "collar_bell", "Ada", "girl", "Muffin", "mother", "sleepy", 121),
    StoryParams("window_rug", "lift_moss", "thread_arrow", "Eli", "boy", "Pip", "father", "curious", 122),
    StoryParams("pillow_bridge", "step_pond", "moon_button", "Mira", "girl", "Velvet", "grandmother", "gentle", 123),
    StoryParams("lamp_corner", "step_pond", "moon_button", "Theo", "boy", "Nim", "mother", "quick", 124),
]


def generation_prompts(world: World) -> list[str]:
    hero = world.get(str(world.facts["hero"]))
    step = STEPS[str(world.facts["step"])]
    clue = CLUES[str(world.facts["clue"])]
    return [
        'Write a bedtime story that includes "whispering street", "whispering cat", and "fuzzy pond".',
        f"Write a quest story where {hero.label} follows a cat and protects a {clue.label}.",
        f"Write a story with foreshadowing where {step.gerund} would lose the clue.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.get(str(world.facts["hero"]))
    cat = world.get(str(world.facts["cat"]))
    elder = world.get(str(world.facts["elder"]))
    step = STEPS[str(world.facts["step"])]
    clue = world.get(str(world.facts["clue"]))
    aid = AIDS[str(world.facts["aid"])]
    prediction = dict(world.facts["prediction"])
    return [
        (
            f"Why did {elder.label} stop {hero.label}?",
            f"{elder.label} stopped {hero.label} because {step.gerund} could {prediction['warning']}. "
            f"The warning was predicted before the {clue.label} was spoiled.",
        ),
        (
            f"How did {cat.label} help?",
            f"{cat.label} suggested the {aid.label}, which let {hero.label} continue the quest gently. "
            f"That kept the clue usable and fulfilled the earlier foreshadowing.",
        ),
        (
            "What line was repeated in the bedtime quest?",
            f"The repeated line was 'Quest, quest, softly best.' "
            f"It reminded {hero.label} that the quest should be solved gently.",
        ),
    ]


KNOWLEDGE = {
    "whispering_street": (
        "What could a whispering street mean in a bedtime story?",
        "A whispering street can be an imaginary path that feels quiet and magical. It invites the child into a gentle quest.",
    ),
    "whispering_cat": (
        "Why might a cat guide a bedtime quest?",
        "Cats are quiet and careful walkers. In a bedtime story, a cat can model moving slowly and noticing small clues.",
    ),
    "fuzzy_pond": (
        "Why might a pond be called fuzzy?",
        "A pretend pond can be made from a blanket, rug, moss, or soft fabric. Calling it fuzzy makes it feel safe but still delicate.",
    ),
    "quest": (
        "What is a quest?",
        "A quest is a journey to find or fix something. Even a small bedtime quest can have rules and clues.",
    ),
    "foreshadowing": (
        "What is foreshadowing?",
        "Foreshadowing is an early hint about what will matter later. Here, the cat's gentle rule prepares the solution.",
    ),
    "bedtime": (
        "Why should bedtime stories stay gentle?",
        "Gentle stories help a child settle down. Soft repetition and calm endings make sleep feel closer.",
    ),
    "thread": (
        "How can thread be a clue?",
        "Thread can point like an arrow or match a missing object. It should be handled carefully so it does not tangle.",
    ),
    "cat": (
        "Why do cats move quietly?",
        "Cats step softly by nature. Their quiet movement makes them useful guides in a story about gentle action.",
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    step = STEPS[str(world.facts["step"])]
    clue = CLUES[str(world.facts["clue"])]
    aid = AIDS[str(world.facts["aid"])]
    tags = set(step.tags) | set(clue.tags) | set(aid.tags)
    return [KNOWLEDGE[tag] for tag in sorted(tags) if tag in KNOWLEDGE][:4]


ASP_RULES = r"""
at_risk(Step,Clue) :- step_zone(Step,Zone), clue_zone(Clue,Zone), risk_of(Step,Risk), vulnerable(Clue,Risk).
effective(Step,Clue,Aid) :- at_risk(Step,Clue), clue_zone(Clue,Zone), covers(Aid,Zone), risk_of(Step,Risk), guards(Aid,Risk).
valid(Place,Step,Clue,Gender) :- setting(Place), affords(Place,Step), clue(Clue), gender(Gender), effective(Step,Clue,_).
#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for gender in GENDERS:
        lines.append(asp.fact("gender", gender))
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for step in setting.affords:
            lines.append(asp.fact("affords", place, step))
    for step_id, step in STEPS.items():
        lines.append(asp.fact("step", step_id))
        lines.append(asp.fact("risk_of", step_id, step.risk))
        for zone in step.zones:
            lines.append(asp.fact("step_zone", step_id, zone))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_zone", clue_id, clue.zone))
        for risk in clue.vulnerable:
            lines.append(asp.fact("vulnerable", clue_id, risk))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for zone in aid.covers:
            lines.append(asp.fact("covers", aid_id, zone))
        for risk in aid.guards:
            lines.append(asp.fact("guards", aid_id, risk))
    return "\n".join(lines) + "\n"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    import asp

    model = asp.one_model(asp_facts() + ASP_RULES)
    return sorted(asp.atoms(model, "valid"))


def asp_verify() -> int:
    py = set(valid_combos())
    lp = set(asp_valid_combos())
    if py == lp:
        print(f"OK: Python and ASP agree on {len(py)} valid whispering-street stories.")
        return 0
    print("Mismatch between Python and ASP valid story sets.")
    print("Only Python:", sorted(py - lp))
    print("Only ASP:", sorted(lp - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the whispering-street cat quest storyworld.")
    parser.add_argument("--place", choices=sorted(SETTINGS))
    parser.add_argument("--step", choices=sorted(STEPS))
    parser.add_argument("--clue", choices=sorted(CLUES))
    parser.add_argument("--gender", choices=list(GENDERS))
    parser.add_argument("--name")
    parser.add_argument("--cat", choices=CAT_NAMES)
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
    if args.step:
        combos = [c for c in combos if c[1] == args.step]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if args.gender:
        combos = [c for c in combos if c[3] == args.gender]
    if not combos:
        place = args.place or next(iter(SETTINGS))
        step = args.step or next(iter(STEPS))
        clue = args.clue or next(iter(CLUES))
        gender = args.gender or GENDERS[0]
        raise StoryError(explain_rejection(place, step, clue, gender))
    place, step, clue, gender = rng.choice(combos)
    name = args.name or rng.choice(NAMES[gender])
    cat = args.cat or rng.choice(CAT_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place, step, clue, name, gender, cat, elder, trait, args.seed)


def generate(params: StoryParams) -> StorySample:
    if (params.place, params.step, params.clue, params.gender) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.step, params.clue, params.gender))
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
        header = f"=== whispering_street_cat_quest #{i} seed={sample.params.seed} ===" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i != len(samples):
            print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
