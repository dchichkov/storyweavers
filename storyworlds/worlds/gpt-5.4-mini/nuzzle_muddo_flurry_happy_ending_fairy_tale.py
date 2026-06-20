#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nuzzle_muddo_flurry_happy_ending_fairy_tale.py
===============================================================================

A standalone story world for a tiny fairy-tale domain built from the seed words
"nuzzle", "muddo", and "flurry".

Premise
-------
A small child in a fairy-tale meadow loves a little game by the brook. A soft
rain-flurry can turn the path muddy, but a wise grown-up and a gentle animal
find a safe, happy way through it.

This world is intentionally small and constraint-checked:
- the muddo path can muddy a cloak, boots, or basket
- the warning is grounded in what the world model predicts
- the ending is always kind and complete, with a bright proof of change

The story aims to read like a short fairy tale rather than an event log.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "queen": "queen", "king": "king"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    outdoor: bool = True
    detail: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["muddo"] < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id or item.protective:
                continue
            if item.region not in world.zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["muddy"] += 1
            item.meters["soiled"] += 1
            out.append(f"{actor.id}'s {item.label} got muddy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["soiled"] < THRESHOLD:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if item.owner and item.owner in world.entities:
            parent = world.get(item.owner)
            parent.memes["worry"] += 1
            out.append(f"That would trouble {parent.id}.")
    return out


CAUSAL_RULES = [Rule("soil", _r_soil), Rule("worry", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def mud_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def sensible_gears() -> list[Gear]:
    return [g for g in GEAR if g.id != "basket_lid"]


def predict_soil(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["soiled"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting_affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setting_line(world: World, activity: Activity) -> str:
    if activity.id == "flurry":
        return "A silver flurry drifted over the meadow, and the brook sang under the willow branches."
    return f"{world.setting.place.capitalize()} looked bright and ready for a little fairy-tale game."


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"Once upon a morning, {hero.id} and {helper.id} wandered to {world.setting.place}. "
        f"They were as merry as birds in spring."
    )
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {hero.traits[0]} cloak, and {helper.id} loved to {helper.pronoun().capitalize()} and sing."
    )


def desire(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} wanted to {activity.verb}, for {activity.gerund} felt like a little dance. "
        f"But {hero.pronoun('possessive')} {prize.label} was too lovely to spoil."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_soil(world, hero, activity, prize.id)
    helper.memes["care"] += 1
    if pred["soiled"]:
        world.say(
            f'"Dear {hero.id}," {helper.id} said, "if you go now, {prize.label} will get muddy. '
            f"Let us think of another way."
        )
    else:
        world.say(
            f'"Dear {hero.id}," {helper.id} said, "the path looks soft, but we may still be careful."'
        )


def nuzzle(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["love"] += 1
    hero.memes["love"] += 1
    world.say(
        f"{helper.id} gave {hero.id} a gentle nuzzle on the cheek, and {hero.id} smiled through the worry."
    )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But the wish to play was strong, so {hero.id} stepped ahead toward the {activity.id} path.")


def accept(world: World, hero: Entity, helper: Entity, gear_def: Gear, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and {helper.id} smiled. " 
        f'"How about we {gear_def.prep}?" {helper.id} asked.'
    )
    world.say(
        f"Then they {gear_def.tail}, and soon {hero.id} could {activity.verb} without ruining {hero.pronoun('possessive')} {prize.label}."
    )


def muddle(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} took one little step, and the {activity.keyword} path turned into {activity.keyword} in a flurry of splashes."
    )


def resolve_happy(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"By the end, the sun peeped out, the mud dried to a soft brown, and {hero.id}'s {prize.label} stayed bright and clean."
    )
    world.say(
        f"{helper.id} and {hero.id} walked home hand in hand, happy as if the meadow itself had blessed them."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Ella", hero_type: str = "girl",
         helper_name: str = "Bran", helper_type: str = "boy",
         parent_type: str = "queen") -> World:
    world = World(setting)
    world.setting_affords = set(setting_affords[setting.id])
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", traits=["small", "brave"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["gentle", "wise"]))
    parent = world.add(Entity(id="Mother", kind="character", type=parent_type, role="parent", label="the queen"))
    prize = world.add(Entity(id="prize", type=prize_cfg.id, label=prize_cfg.label, region=prize_cfg.region, owner=parent.id))
    hero.traits.insert(0, "muddo")
    introduce(world, hero, helper)
    world.para()
    world.say(setting_line(world, activity))
    desire(world, hero, activity, prize)
    warn(world, helper, hero, activity, prize)
    nuzzle(world, helper, hero)
    if mud_risk(activity, prize):
        defy(world, hero, activity)
        world.para()
        muddle(world, hero, activity)
        gear_def = select_gear(activity, prize)
        if gear_def is None:
            raise StoryError("No reasonable gear for this tale.")
        accept(world, hero, helper, gear_def, activity, prize)
        resolve_happy(world, hero, helper, prize)
    else:
        world.say("Nothing was spoiled, and the day stayed sweet.")
    world.facts.update(hero=hero, helper=helper, parent=parent, activity=activity, prize=prize, setting=setting)
    return world


SETTINGS = {
    "brook": Setting("brook", "the brook meadow", True),
    "orchard": Setting("orchard", "the orchard lane", True),
    "castle_garden": Setting("castle_garden", "the castle garden", True),
}

ACTIVITIES = {
    "flurry": Activity("flurry", "dance in the flurry", "dancing in a flurry", "run through the flurry", "muddo", {"feet", "legs"}, "flurry", {"rain", "mud"}),
    "muddo": Activity("muddo", "skip the muddo path", "skipping the muddo path", "dash across the muddo", "muddo", {"feet", "legs", "torso"}, "muddo", {"mud"}),
}

PRIZES = {
    "cloak": Prize("cloak", "velvet cloak", "a velvet cloak", "torso"),
    "boots": Prize("boots", "golden boots", "golden boots", "feet", plural=True),
    "basket": Prize("basket", "flower basket", "flower basket", "torso"),
}

GEAR = [
    Gear("rain_cape", "a rain cape", {"torso"}, {"muddo", "muddy"}, "put on a rain cape first", "went home to fetch the rain cape"),
    Gear("boot_wrappings", "boot wrappings", {"feet"}, {"muddo", "muddy"}, "wrap up their boots", "tied the boot wrappings on"),
    Gear("basket_lid", "a basket lid", {"torso"}, {"muddo", "muddy"}, "cover the basket", "covered the basket", False),
]

setting_affords = {
    "brook": {"flurry", "muddo"},
    "orchard": {"muddo"},
    "castle_garden": {"flurry", "muddo"},
}

GIRL_NAMES = ["Ella", "Mira", "Lina", "Rose", "Nora"]
BOY_NAMES = ["Bran", "Finn", "Lio", "Pip", "Tobin"]



@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    StoryParams("brook", "flurry", "cloak", "Ella", "girl", "Bran", "boy", "queen"),
    StoryParams("castle_garden", "muddo", "boots", "Mira", "girl", "Finn", "boy", "queen"),
]



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting_affords[sid]:
            act = ACTIVITIES[aid]
            for pid, prize in PRIZES.items():
                if mud_risk(act, prize) and select_gear(act, prize):
                    combos.append((sid, aid, pid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about {f["hero"].id} and a {f["activity"].keyword} path, and include the word "nuzzle".',
        f"Tell a happy-ending story where {f['hero'].id} wants to {f['activity'].verb}, but a gentle helper keeps {f['prize'].label} safe.",
        f'Write a short fairy tale using the words "nuzzle", "muddo", and "flurry".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, activity = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {hero.id} and {helper.id}, two gentle travelers in a fairy-tale meadow. The queen watched over them, and the little adventure stayed kind and bright."
        ),
        QAItem(
            question=f"Why did {helper.id} warn {hero.id}?",
            answer=f"{helper.id} warned {hero.id} because the world model showed that going onto the {activity.keyword} path would make the {prize.label} muddy. That would have spoiled the lovely thing they were trying to protect."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. They chose safe gear, the {prize.label} stayed clean, and the meadow looked peaceful at the end."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does a nuzzle mean?", "A nuzzle is a soft, affectionate rub, like a gentle touch from a face or nose. It shows kindness and closeness."),
        QAItem("What is muddy?", "Mud is wet earth, and when something gets muddy it becomes covered with brown soil. Mud can make clothes and boots messy."),
        QAItem("What is a flurry?", "A flurry is a quick little burst, often of wind, snow, or rain. It can make a path slippery and lively."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
mud_risk(A, P) :- zone(A, R), prize_region(P, R).
gear_ok(G, A, P) :- guards(G, M), activity_mess(A, M),
                    covers(G, R), prize_region(P, R).
valid(S, A, P) :- setting(S), activity(A), prize(P), mud_risk(A, P), gear_ok(G, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    rc = 0
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in gate:")
        print(" only in asp:", sorted(a - p))
        print(" only in py:", sorted(p - a))
        rc = 1

    # smoke test: ordinary generation must not crash
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        print(f"FAILED: generation smoke test crashed: {exc}")
        return 1 if rc == 0 else rc
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale storyworld with nuzzle, muddo, and flurry.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--parent", choices=["queen", "king"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, prize = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    parent = args.parent or rng.choice(["queen", "king"])
    return StoryParams(setting, activity, prize, hero, "girl" if hero in GIRL_NAMES else "boy",
                       helper, "girl" if helper in GIRL_NAMES else "boy", parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.hero, params.hero_gender, params.helper, params.helper_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, activity, prize) combos:\n")
        for s, a, p in combos:
            print(f"  {s:14} {a:10} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
