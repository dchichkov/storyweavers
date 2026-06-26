#!/usr/bin/env python3
"""
storyworlds/worlds/folder_humor_rhyming_story.py
================================================

A small, self-contained story world for a humorous rhyming tale about a
precious folder, a rainy dash, and a clever waterproof fix.

The seed image:
---
A child has a favorite folder full of funny drawings and shiny notes.
One rainy day, they want to dash outside with it, but a grownup warns that
the rain will wrinkle the pages and make a mess. After a little wobble and
a silly protest, they find a plastic sleeve that keeps the folder dry.
---

This world is intentionally tiny and constraint-checked:
- The folder can only be endangered by the rainy dash when it is exposed.
- The compromise must actually protect the folder from the relevant mess.
- The prose is built from simulated state, not a frozen paragraph with swapped
  nouns.

Rhyming style notes:
- Short, child-facing, concrete sentences.
- Light end-rhyme / sound-play in the setup and resolution.
- Humor comes from the folder's fussiness and the child’s silly reaction.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "mom", "woman"}
        masculine = {"boy", "father", "dad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


MESS_KINDS = {"wet", "wrinkled", "torn"}
REGIONS = {"hands", "torso", "feet"}


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("wet", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] = item.meters.get("wet", 0.0) + 1
            item.meters["wrinkled"] = item.meters.get("wrinkled", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and wrinkled.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("wrinkled", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0.0) < THRESHOLD or actor.memes.get("defiance", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_soak,
    _r_workload,
    _r_grab_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
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
        "soiled": bool(prize and prize.meters.get("wrinkled", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "rain_dash": "the patter and splatter made a funny clatter",
        "paper_sort": "the shuffle and rustle made the whole room bustle",
    }.get(activity.id, "it made the day feel merry and bright")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place} was snug and still, with a table set for a frill of fun."
    if activity.weather == "rainy":
        return f"The rain made {setting.place} shine, with puddly paths and a shiny line."
    return f"{setting.place.capitalize()} looked ready for play, with room for a grin and a little sway."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a bright-eyed child who loved a folder with a snap and a snap-snap style.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] = hero.memes.get("love_play", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.verb}; "
        f"{activity_delight(activity)}, and that gave {hero.pronoun('object')} a smiley mile."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}; "
        f"{prize.label.capitalize()} felt nifty and ready, all tidy and pretty."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "went to" if not world.setting.indoor else "were in"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label} held up a hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to clean it"
    world.say(f'"{clause}," {parent.label} said. "That would be a soggy, soggy plight."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} puffed a cheek and made a tiny huff; the plan sounded rough.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label} caught {hero.pronoun('possessive')} hand and said, "
        f'"You can still want to {activity.verb}, but let\'s choose a drier strand."'
    )


def pout(world: World, hero: Entity) -> None:
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f'{hero.id} pouted and blinked. "But I really, really want my shiny thing!"')


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
        f'{hero.pronoun("possessive").capitalize()} {parent.label} smiled and said, '
        f'"How about we {gear_def.prep} and then {activity.verb}?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up like a little lamp; {hero.pronoun()} gave {hero.pronoun('possessive')} {parent.label} a hug."
    )
    world.say(
        f'"Hooray, hooray!" {hero.id} sang. "We can go that way!" '
        f"They {gear_def.tail}, and soon {hero.id} was {activity.gerund}, {prize_was_clean(hero, prize)}, feeling light as a kite."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Milo",
    hero_type: str = "boy",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            meters={},
            memes={},
        )
    )
    parent = world.add(
        Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={})
    )
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
            meters={},
            memes={},
        )
    )

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
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
        conflict=hero.memes.get("grabbed_by", 0.0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "porch": Setting(place="the porch", indoor=False, affords={"rain_dash"}),
    "yard": Setting(place="the yard", indoor=False, affords={"rain_dash"}),
    "table": Setting(place="the kitchen table", indoor=True, affords={"paper_sort"}),
    "desk": Setting(place="the desk", indoor=True, affords={"paper_sort"}),
}

ACTIVITIES = {
    "rain_dash": Activity(
        id="rain_dash",
        verb="dash in the rain",
        gerund="dashing in the rain",
        rush="run into the rain",
        mess="wet",
        soil="soaking wet",
        zone={"hands", "torso"},
        weather="rainy",
        keyword="rain",
        tags={"rain", "wet"},
    ),
    "paper_sort": Activity(
        id="paper_sort",
        verb="sort the papers",
        gerund="sorting papers",
        rush="shove the papers",
        mess="wrinkled",
        soil="all wrinkled",
        zone={"hands", "torso"},
        weather="",
        keyword="paper",
        tags={"paper", "wrinkled"},
    ),
}

GEAR = [
    Gear(
        id="sleeve",
        label="a plastic sleeve",
        covers={"hands", "torso"},
        guards={"wet"},
        prep="put the folder in a plastic sleeve first",
        tail="slipped the folder into the plastic sleeve",
    ),
    Gear(
        id="folder_box",
        label="a stiff folder box",
        covers={"hands", "torso"},
        guards={"wet", "wrinkled"},
        prep="tuck the folder into a stiff folder box",
        tail="tucked the folder into the stiff folder box",
    ),
    Gear(
        id="clip",
        label="a clip",
        covers={"hands"},
        guards={"wrinkled"},
        prep="clip the papers tight first",
        tail="clipped the papers tight",
    ),
]

PRIZES = {
    "folder": Prize(
        label="folder",
        phrase="a bright blue folder with a silly star sticker",
        type="folder",
        region="torso",
    ),
    "papers": Prize(
        label="papers",
        phrase="a neat stack of papers",
        type="papers",
        region="hands",
        plural=True,
    ),
}

GIRL_NAMES = ["Nora", "Mia", "Ella", "Luna", "Zoe"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Leo", "Max"]
TRAITS = ["cheerful", "curious", "silly", "sparkly", "brave"]


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
    "folder": [
        (
            "What is a folder?",
            "A folder is a holder for papers. It keeps loose pages together so they do not flop around.",
        )
    ],
    "rain": [
        (
            "What does rain do to paper?",
            "Rain can make paper wet, soft, and wrinkly, so the pages may bend and get messy.",
        )
    ],
    "wet": [
        (
            "Why do people cover papers in wet weather?",
            "People cover papers to keep them dry, because dry paper stays flat and easier to use.",
        )
    ],
    "wrinkled": [
        (
            "What does wrinkled mean?",
            "Wrinkled means bent into little folds or lines, like a page that got squashed or damp.",
        )
    ],
    "paper": [
        (
            "What are papers for?",
            "Papers can hold drawings, notes, school work, and other things people want to save.",
        )
    ],
}
KNOWLEDGE_ORDER = ["folder", "paper", "rain", "wet", "wrinkled"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short rhyming story for a young child about a {prize.label} and a rainy day, using the word "{kw}".',
        f"Tell a funny little story where {hero.id} wants to {act.verb} with {hero.pronoun('possessive')} {prize.label}, "
        f"but {hero.pronoun('possessive')} {parent.label} worries.",
        f"Write a child-friendly tale in which a {prize.label} stays safe after a silly weather mishap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = f["hero"].id  # intentionally unused for invariant phrasing? no
    hero_trait = next((t for t in [world.facts.get("trait", "silly")] if t), "silly")
    qa: list[QAItem] = [
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label} at {place}?",
            answer=f"{hero.id} wanted to {act.verb} with {pos} {prize.label}, even though the day was a bit splashy.",
        ),
        QAItem(
            question=f"Why did {pw} worry about the {prize.label}?",
            answer=(
                f"{pw} worried because if {hero.id} went to {act.verb}, the {prize.label} would get {act.soil}. "
                f"Then it would need cleaning or fixing, which would be a fussy, sticky job."
            ),
        ),
        QAItem(
            question=f"What did {hero.id}'s {pw} buy before the rainy outing?",
            answer=f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}.",
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", act.soil)
        why = (
            f"{pos.capitalize()} {pw} was worried because the rain would make the {prize.label} {soil}. "
            f"When {hero.id} tried to {act.rush}, {pos} {pw} held {pos} hand and reminded {obj} there was a safer way."
        )
        qa.append(
            QAItem(
                question=f"Why did {hero.id}'s {pw} grab {pos} hand?",
                answer=why,
            )
        )
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help {hero.id} {act.verb} safely?",
                answer=f"They used {gear.label} first, so {hero.id} could {act.verb} without ruining the {prize.label}.",
            )
        )
        qa.append(
            QAItem(
                question=f"How did {hero.id} feel after the plan worked?",
                answer=f"{hero.id} felt happy and hugged {pos} {pw}. In the end, {sub} was {act.gerund} and smiling.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
    StoryParams(place="porch", activity="rain_dash", prize="folder", name="Milo", gender="boy", parent="mother", trait="silly"),
    StoryParams(place="yard", activity="rain_dash", prize="folder", name="Nora", gender="girl", parent="father", trait="curious"),
    StoryParams(place="desk", activity="paper_sort", prize="papers", name="Theo", gender="boy", parent="mother", trait="cheerful"),
    StoryParams(place="table", activity="paper_sort", prize="folder", name="Ella", gender="girl", parent="mother", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} would not reach {noun} -- it {verb} in a different spot, "
            f"so there is no honest mess to warn about.)"
        )
    return f"(No story: nothing in the gear set properly protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


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
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
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
        description="Story world sketch: a folder, a rainy dash, and a funny fix."
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
        c
        for c in valid_combos()
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
    world.facts["trait"] = params.trait
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
            print(f"  {place:9} {act:10} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
