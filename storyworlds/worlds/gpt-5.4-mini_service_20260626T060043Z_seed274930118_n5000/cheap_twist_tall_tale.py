#!/usr/bin/env python3
"""
storyworlds/worlds/cheap_twist_tall_tale.py
==========================================

A small Storyweavers world built from a tall-tale seed about something cheap,
a surprising twist, and a big windy trouble that gets solved in a child-facing
way.

The premise is simple: a child loves a bargain prize, but the world gives it a
wild, larger-than-life test. The parent foresees the trouble, the child resists
the warning, and the twist in the tale turns the flimsy thing into a sturdy
wonder.

This world is intentionally narrow and constraint-checked: only stories with a
real risk, a real warning, and a real fix are allowed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["cost", "sturdy", "torn", "dirty", "danger"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "resolve", "wonder", "conflict", "surprise"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandpa", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_wind: bool = False
    afford_fly: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    hazard_kind: str
    zone: set[str]
    weather: str
    keyword: str
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["torn"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} looked worse for wear.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["torn"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would make extra work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["warned"] < THRESHOLD or actor.memes["stubborn"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("damage", "physical", _r_damage),
    Rule("worry", "social", _r_worry),
    Rule("conflict", "social", _r_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.hazard_kind in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "torn": bool(prize and prize.meters["torn"] >= THRESHOLD),
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.afford_fly:
        return
    world.zone = set(activity.zone)
    actor.meters["danger"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "brave")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a good bargain and a bigger adventure.")


def loves_thing(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["wonder"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, even though it was so cheap it seemed to wink at the whole world."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One market day, {hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase} for a handful of coins."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One blustery day, "
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}."
    )
    world.say(
        f"The wind was strong enough to tickle fence posts and comb the grass sideways."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["resolve"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}, grinning at the sky.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["torn"]:
        return False
    world.facts["predicted_worry"] = pred["worry"]
    hero.memes["warned"] += 1
    clause = f"You'll get your {prize.label} {activity.hazard}"
    if pred["worry"] >= THRESHOLD:
        clause += ", and I'll have extra trouble fixing it"
    world.say(f'"{clause}," {parent.label} said. "That wind has sharp little elbows today."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] += 1
    world.say(f"{hero.id} did not back down.")
    world.say(f"{hero.pronoun().capitalize()} kept after the kite anyway.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held"] = hero.memes.get("held", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"But {hero.pronoun('possessive')} {parent.label} caught {hero.pronoun('possessive')} hand and said, "
        f'"There is a smarter twist to this tale."'
    )


def pout(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted and stared at the dust, wishing the sky would listen to {hero.pronoun('object')}.")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["torn"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label.capitalize()} smiled and said, "How about we {gear_def.prep}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(
        f"Together they {gear_def.tail}. Then the cheap little prize took the wind, and the twist in it turned into a clever strength."
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, {prize.it()} stayed safe, and the whole sky looked a little more impressed."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mabel",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["cheerful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    buys(world, parent, hero, prize)
    loves_thing(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
    pout(world, hero)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["held"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "hill": Setting(place="the windy hill", afford_wind=True, afford_fly=True),
    "field": Setting(place="the open field", afford_wind=True, afford_fly=True),
    "fair": Setting(place="the county fairground", afford_wind=True, afford_fly=True),
    "farmyard": Setting(place="the farmyard", afford_wind=True, afford_fly=True),
}

ACTIVITIES = {
    "kite": Activity(
        id="kite",
        verb="fly the kite",
        gerund="flying the kite",
        rush="run uphill with the kite",
        hazard="it could get tangled and torn",
        hazard_kind="tangle",
        zone={"hands", "tail", "paper"},
        weather="windy",
        keyword="twist",
        tags={"wind", "kite", "twist"},
    ),
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a cheap kite with a long tail",
        type="kite",
        region="paper",
    ),
}

GEAR = [
    Gear(
        id="twist_tail",
        label="a twisted tail line",
        covers={"tail", "paper"},
        guards={"tangle"},
        prep="twist the tail line into a smart spiral first",
        tail="twisted the tail line into a spiral and let it sail again",
    ),
    Gear(
        id="string_loop",
        label="a loop of string",
        covers={"hands", "tail"},
        guards={"tangle"},
        prep="tie a loop of string through the tail",
        tail="tied the loop of string and gave the kite a steadier dance",
    ),
]

GIRL_NAMES = ["Mabel", "June", "Nell", "Poppy", "Sadie", "Ivy", "Lena", "Ruby"]
BOY_NAMES = ["Otis", "Cal", "Bennett", "Wes", "Hank", "Eli", "Rudy", "Finn"]
TRAITS = ["brave", "curious", "cheerful", "stubborn", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in ACTIVITIES:
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(ACTIVITIES[act_id], prize) and select_gear(ACTIVITIES[act_id], prize):
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
    "wind": [("What is wind?", "Wind is moving air. It can feel like a push on your face, hair, and clothes.")],
    "kite": [("What is a kite?", "A kite is a light toy that can fly in the air when you hold its string on a windy day.")],
    "twist": [("What does twist mean?", "To twist means to turn something around and around, like winding a string into a spiral.")],
    "cheap": [("What does cheap mean?", "Cheap means something costs only a little money. It is easy to buy, even if it is small or simple.")],
    "tangle": [("What is a tangle?", "A tangle is a mess of things twisted together so they are hard to pull apart.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short tall-tale story for a child about a cheap {prize.label} and a twist in the wind.',
        f"Tell a story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries the cheap {prize.label} will get tangled.",
        f'Write a playful story that uses the word "cheap" and ends with a twist that helps the child keep playing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} wants to {act.verb} with the cheap {prize.label}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {hero.pronoun('possessive')} {parent.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} love before the windy trouble began?",
            answer=f"{hero.id} loved {hero.pronoun('possessive')} cheap {prize.label}, even though it looked simple.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label} warn {hero.id} about the {act.keyword} at {world.setting.place}?",
            answer=(
                f"{parent.label.capitalize()} warned {hero.id} because the wind could twist the {prize.label} up, tangle it, and tear it."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"What happened when {hero.id} tried to {act.rush} anyway?",
            answer=(
                f"{hero.id} got stubborn, but {hero.pronoun('possessive')} {parent.label} held {hero.pronoun('possessive')} hand and helped {hero.pronoun('object')} choose a safer twist."
            ),
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help the cheap {prize.label} stay safe?",
            answer=(
                f"They used {gear.label} first, and that twist kept the {prize.label} from tangling and tearing in the wind."
            ),
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt happy and proud, because the bargain toy became strong enough for the big wind and the story ended in a cheerful whirl."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | {"cheap"}
    if world.facts.get("gear"):
        tags.add("twist")
    out: list[QAItem] = []
    for tag in ["cheap", "kite", "wind", "twist", "tangle"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
    StoryParams(place="hill", activity="kite", prize="kite", name="Mabel", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="field", activity="kite", prize="kite", name="Otis", gender="boy", parent="father", trait="brave"),
    StoryParams(place="fair", activity="kite", prize="kite", name="Ruby", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="farmyard", activity="kite", prize="kite", name="Finn", gender="boy", parent="father", trait="lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the prize is not in the wind's path, so there is no honest trouble to solve.)"
    return "(No story: there is no reasonable twist that protects this prize in this activity.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), hazard_kind(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.afford_fly:
            lines.append(asp.fact("affords", pid, "kite"))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("hazard_kind", aid, a.hazard_kind))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
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
    ap = argparse.ArgumentParser(description="A cheap thing, a twist, and a tall tale in the wind.")
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

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
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
            print(f"  {place:10} {act:8} {prize:8}  [{', '.join(genders)}]")
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
