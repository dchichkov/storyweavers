#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fix_philanthropy_cartridge_cautionary_quest_suspense_comedy.py
===============================================================================================================================

A tiny standalone storyworld about a cautious little quest to fix a printer
cartridge in time for a philanthropy event, with suspenseful comedy and a
gentle warning about being careful with messy things.

Seed premise:
- A child volunteer wants to help a community fundraiser.
- The printer's cartridge is streaky or jammed.
- A careful fix is needed before the event starts.
- The story should feel like a quest, with a little suspense and a funny,
  child-facing payoff.

The world is intentionally small and constraint-checked:
- If the chosen cartridge problem has no reasonable fix, the story is rejected.
- The ASP twin mirrors the Python reasonableness gate.
- State changes drive the prose: worry, searching, fixing, and relief all come
  from the simulated model, not from a frozen template paragraph.

This world uses the shared result containers from storyworlds/results.py.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


MESS_KINDS = {"inky", "smudged", "stuck"}


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("smudge", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got smudged.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That meant more work for {carer.label_word}.")
    return out


def _r_suspense(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["deadline"] < THRESHOLD:
            continue
        sig = ("suspense", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["suspense"] += 1
        return ["__suspense__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("smudge", "physical", _r_smudge),
    Rule("worry", "physical", _r_worry),
    Rule("suspense", "social", _r_suspense),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__suspense__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked helping people.")

def love_philanthropy(world: World, hero: Entity, place: Setting) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved philanthropy days at {place.place}, "
        f"because kind jobs could still feel like a game."
    )


def disaster_setup(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"At the start, {hero.id} wanted to {activity.verb} for the big fundraiser."
    )
    world.say(
        f"But the printer's {prize.label} was acting fussy, like it had forgotten how to be a helpful little tube of ink."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'"If we rush it," {parent.label_word} said, "that {prize.label} will get {activity.soil}."'
    )
    return True


def quest(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["quest"] += 1
    hero.memes["deadline"] += 1
    world.say(
        f"So {hero.id} set off on a tiny quest through the office, looking for a fix before the clock got louder."
    )
    world.say(
        f"{hero.pronoun().capitalize()} opened drawers like a treasure hunter and checked boxes like a detective with glue on the brain."
    )


def suspense(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["suspense"] >= THRESHOLD:
        world.say(
            f"The room felt extra suspenseful because the fundraiser was almost ready, and nobody wanted a printer that only sneezed."
        )


def fix_it(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"At last, {hero.id} found {gear_def.label} and used the little fix just right."
    )
    world.say(
        f'"That should do it," {parent.label_word} said, and {hero.id} grinned like a squirrel who had solved a math problem.'
    )
    return gear_def


def end(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["suspense"] = 0.0
    world.say(
        f"Together they {gear_def.tail}, and then the printer behaved."
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, the {prize.label} stayed clean, and the philanthropy flyers came out in a happy stack."
    )
    world.say(
        f"{hero.id} laughed, because the biggest scare had turned into a silly little victory."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Pip",
    hero_type: str = "boy",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = ""

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little"] + (hero_traits or ["helpful", "careful"]),
        )
    )
    parent = world.add(Entity(id="Helper", kind="character", type=parent_type, label="the helper"))
    prize = world.add(
        Entity(
            id="cartridge",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    introduction(world, hero)
    love_philanthropy(world, hero, setting)
    disaster_setup(world, hero, parent, prize, activity)

    world.para()
    if warn(world, parent, hero, activity, prize):
        quest(world, hero, parent, activity)
        suspense(world, hero, activity)
        gear_def = fix_it(world, parent, hero, activity, prize)
        if gear_def:
            world.para()
            end(world, hero, parent, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def if "gear_def" in locals() else None,
        conflict=hero.memes["deadline"] >= THRESHOLD,
        resolved=("gear_def" in locals() and gear_def is not None),
    )
    return world


SETTINGS = {
    "library": Setting(place="the library copy room", indoor=True, affords={"print"}),
    "school": Setting(place="the school office", indoor=True, affords={"print", "copy"}),
    "community_center": Setting(place="the community center office", indoor=True, affords={"print"}),
}

ACTIVITIES = {
    "print": Activity(
        id="print",
        verb="print the philanthropy flyers",
        gerund="printing the philanthropy flyers",
        rush="rush the printer",
        mess="inky",
        soil="inky and streaky",
        zone={"hands"},
        weather="",
        keyword="philanthropy",
        tags={"philanthropy", "ink"},
    ),
    "copy": Activity(
        id="copy",
        verb="copy the thank-you cards",
        gerund="copying the thank-you cards",
        rush="tap the copier",
        mess="smudged",
        soil="smudged and messy",
        zone={"hands"},
        weather="",
        keyword="cartridge",
        tags={"ink", "cartridge"},
    ),
}

PRIZES = {
    "cartridge": Prize(
        label="printer cartridge",
        phrase="a printer cartridge",
        type="cartridge",
        region="hands",
        plural=False,
    ),
    "toner": Prize(
        label="toner cartridge",
        phrase="a toner cartridge",
        type="cartridge",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"inky", "smudged"},
        prep="put on soft gloves first",
        tail="put on the soft gloves and tried again",
    ),
    Gear(
        id="tray",
        label="a little tray",
        covers={"hands"},
        guards={"stuck"},
        prep="set the cartridge on a little tray",
        tail="set the cartridge on a little tray and gave it one careful try",
    ),
]

GIRL_NAMES = ["Mina", "Lia", "Nora", "Zuri", "Etta"]
BOY_NAMES = ["Pip", "Jory", "Ned", "Toby", "Finn"]
TRAITS = ["helpful", "careful", "brave", "silly", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "philanthropy": [
        (
            "What is philanthropy?",
            "Philanthropy is when people give time, money, or help to do something kind for others.",
        )
    ],
    "cartridge": [
        (
            "What is a printer cartridge?",
            "A printer cartridge is a container that holds ink or toner so a printer can make words and pictures on paper.",
        )
    ],
    "ink": [
        (
            "Why can ink be messy?",
            "Ink can be messy because it can smear on paper, fingers, and clothes before it dries.",
        )
    ],
    "copy": [
        (
            "What does a copy machine do?",
            "A copy machine makes another page that looks like the one you put inside it.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short, funny story for a young child about a philanthropy day and a careful fix, using the word "{kw}".',
        f"Tell a suspenseful-but-silly story where {hero.id} tries to {act.verb} but needs a fix for the {prize.label}.",
        f'Write a gentle quest story about helping at {world.setting.place} and keeping a "{kw}" cartridge from getting messy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who went on the little quest in {place}?",
            answer=f"{hero.id}, a little {trait} {hero.type}, went on the quest with {parent.label_word} nearby.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do for the fundraiser?",
            answer=f"{hero.id} wanted to {act.verb}. That was part of helping the philanthropy day go well.",
        ),
        QAItem(
            question=f"What was the problem with the {prize.label}?",
            answer=f"The {prize.label} was acting fussy, so it needed a careful fix before it could help print the flyers.",
        ),
    ]
    if f.get("conflict"):
        qa.append(
            QAItem(
                question=f"Why was there suspense during the story?",
                answer=f"There was suspense because the fundraiser was almost ready, and if they rushed the {prize.label}, it could get {act.soil}.",
            )
        )
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did the story end after they found the fix?",
                answer=f"They used {gear.label} and the printer worked again, so the flyers were printed and the trouble turned into a funny happy ending.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", activity="print", prize="cartridge", name="Pip", gender="boy", parent="mother", trait="helpful"),
    StoryParams(place="school", activity="copy", prize="toner", name="Mina", gender="girl", parent="father", trait="careful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not put the {prize.label} at risk.)"
    return f"(No story: nothing in the gear catalog reasonably protects the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cautious philanthropy quest with a printer cartridge and a funny fix."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "stubborn"],
        params.parent,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:18} {act:8} {prize:10}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
