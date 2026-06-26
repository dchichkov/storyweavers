#!/usr/bin/env python3
"""
storyworlds/worlds/literary_cheerio_slate_conflict_myth.py
===========================================================

A small mythic storyworld about a young keeper of words, a sacred slate, and a
bowl of cheerios that threatens to turn a careful rite into a conflict.

Seed tale distilled:
- A child apprentice studies old words by firelight.
- The child treasures a slate for writing signs and omens.
- During a quiet rite, a bowl of cheerios is brought close to the slate.
- Crumbs, pride, and a stubborn wish to keep both breakfast and prophecy
  together cause conflict.
- A wiser helper shows how to separate the meal from the message, and the
  story ends with the slate clean, the bowl safe, and the words still shining.

The world is intentionally small and constraint-checked: only plausible
combinations of setting, action, and treasured object are generated.
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
    kind: str = "thing"  # character | thing
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "crumbs", "mess", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["love", "joy", "desire", "defiance", "conflict", "worry", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "daughter", "oracle"}
        male = {"boy", "father", "dad", "man", "son", "scribe"}
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
    indoor: bool = False
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
    weather: str = ""
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["crumbs"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["crumbs"] += 1
            item.meters["mess"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} caught crumbs and looked dusty.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["mess"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] += 1
        caretaker.meters["workload"] += 1
        out.append(f"That would mean more work for {caretaker.label_word}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("soil", "physical", _r_soil),
    Rule("worry", "physical", _r_worry),
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
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["mess"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("This setting cannot host that rite.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the fire was low and the stones held the hush of old names."
    return f"Outside {setting.place}, the sky was wide and the wind sounded like a hymn."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "young")
    world.say(
        f"{hero.id} was a young {trait} {hero.type} who listened for stories in every crack of stone."
    )


def loves_study(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, and each mark felt like part of an ancient song."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One dawn, {hero.id}'s {parent.label_word} brought {hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label}, and carried {prize.it()} like a vow."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"sunny": "On a bright morning, ", "stormy": "On a stormy morning, "}.get(world.weather, "One morning, ")
    go = "walked to" if not world.setting.indoor else "came to"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, as if the day had been waiting for that one sign.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," '
        f"{hero.pronoun('possessive')} {parent.label_word} said. "
        f'"Then I will have work to do, and the slate will need scrubbing."'
    )
    hero.memes["worry"] += 1
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But {hero.id} still felt the pull of the rite and tried to {activity.rush}, cradling the bowl too close.")


def conflict(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["conflict"] += 1
    world.say(
        f"{parent.label_word} reached out and steadied {hero.pronoun('possessive')} hands. "
        f'"The sign must stay clear," {parent.pronoun()} said. "A prophecy and a breakfast are not the same thing."'
    )


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
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"At last, {hero.pronoun('possessive')} {parent.label_word} offered a wiser way: {gear_def.prep}."
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id} agreed, and the tightness in {hero.pronoun('possessive')} chest loosened like a knot in rain.")
    world.say(
        f"They {gear_def.tail}. Then {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the old words shone on."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Ari", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "father") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young"] + (hero_traits or ["curious", "stubborn"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the elder"))
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
    loves_study(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    conflict(world, hero, parent)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def, resolved=gear_def is not None)
    return world


SETTINGS = {
    "archive": Setting(place="the sunlit archive", indoor=True, affords={"scribe"}),
    "courtyard": Setting(place="the temple courtyard", indoor=False, affords={"scribe"}),
    "hearth": Setting(place="the hall of embers", indoor=True, affords={"scribe"}),
}

ACTIVITIES = {
    "scribe": Activity(
        id="scribe",
        verb="copy the old omen onto the slate",
        gerund="copying old omens",
        rush="hurry to the slate with the bowl in hand",
        mess="crumbs",
        soil="full of crumbs",
        zone={"hands", "torso"},
        weather="",
        keyword="literary",
        tags={"literary", "slate"},
    ),
}

PRIZES = {
    "slate": Prize(
        label="slate",
        phrase="a smooth sacred slate",
        type="slate",
        region="hands",
    ),
    "tablet": Prize(
        label="tablet",
        phrase="a dark stone tablet",
        type="tablet",
        region="hands",
    ),
    "scroll": Prize(
        label="scroll",
        phrase="a rolled hymn scroll",
        type="scroll",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="cloth",
        label="a soft cloth",
        covers={"hands"},
        guards={"crumbs"},
        prep="set the cheerio bowl aside and wrap the slate in a soft cloth",
        tail="set the bowl aside and wrapped the slate in a soft cloth",
    ),
    Gear(
        id="tray",
        label="a carved tray",
        covers={"hands", "torso"},
        guards={"crumbs"},
        prep="place the bowl on a carved tray away from the slate",
        tail="placed the bowl on a carved tray away from the slate",
    ),
]

HERO_NAMES = ["Ari", "Nina", "Talo", "Mira", "Orin", "Sera"]
TRAITS = ["wise", "curious", "bold", "patient", "bright", "earnest"]


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
    "literary": [(
        "What does literary mean?",
        "Literary means having to do with books, stories, poems, and the art of words."
    )],
    "cheerio": [(
        "What is a cheerio?",
        "A cheerio is a small round breakfast cereal, often eaten with milk."
    )],
    "slate": [(
        "What is a slate?",
        "A slate is a flat piece of stone used for writing or drawing with chalk."
    )],
    "crumbs": [(
        "Why should crumbs be kept away from writing tools?",
        "Crumbs can make a writing surface messy, and a clean surface helps the marks stay clear."
    )],
}

KNOWLEDGE_ORDER = ["literary", "cheerio", "slate", "crumbs"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        'Write a myth-like story about a child, a sacred slate, and a bowl of cheerios.',
        f"Tell a gentle myth where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} fears the {prize.label} will be ruined.",
        f"Write a short story that uses the words literary, cheerio, and slate, and ends with a wiser choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "young"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to {world.setting.place} with the {prize.label}?",
            answer=f"It is about a young {trait} {hero.type} named {hero.id} and {hero.pronoun('possessive')} {parent.label_word}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the slate in the story?",
            answer=f"{hero.id} wanted to {act.verb}. The marks were meant to be careful and important, like an old myth being copied by hand.",
        ),
        QAItem(
            question=f"Why did {hero.pronoun('possessive')} {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried that if the bowl came too close, the {prize.label} would get {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the helper solve the conflict in the end?",
            answer=f"They used {gear.label} and kept the bowl away from the slate, so the words could stay clear and the breakfast could stay safe.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel after the wiser plan?",
            answer=f"{hero.id} felt calm and happy. The conflict faded, and the story ended with a clean slate and a peaceful heart.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("prize"):
        tags.add(world.facts["prize"].label)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="archive", activity="scribe", prize="slate", name="Ari", gender="boy", parent="father", trait="curious"),
    StoryParams(place="courtyard", activity="scribe", prize="tablet", name="Mira", gender="girl", parent="mother", trait="earnest"),
    StoryParams(place="hearth", activity="scribe", prize="scroll", name="Talo", gender="boy", parent="father", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not truly endanger {noun} here.)"
    return f"(No story: no gear in this small world can honestly guard {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not restricted to {gender} here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
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
    ap = argparse.ArgumentParser(description="A mythic story world about a slate, cheerios, and a conflict.")
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
