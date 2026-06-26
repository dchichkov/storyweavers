#!/usr/bin/env python3
"""
shorts_suspense_dialogue_comedy.py
==================================

A compact storyworld about a child, a much-loved pair of shorts, and a comic
little moment of suspense: will the shorts survive the mess?

The world is small on purpose. The state that matters is:
- who wants to play,
- what the shorts are made for,
- what risky place or activity is tempting,
- what the parent warns about,
- whether a harmless workaround is found in time.

The prose is authored from simulated world state, not from a frozen template.
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
    kind: str = "thing"
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
        for k in ("wet", "muddy", "painted", "sandy", "dirty", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "love", "desire", "worry", "relief", "conflict", "grabbed_by"):
            self.memes.setdefault(k, 0.0)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: object


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "muddy", "painted", "sandy"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label_word}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
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
    Rule("workload", "physical", _r_workload),
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
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "puddles": "the plip-plop sounded like tiny applause",
        "mud": "the squish underfoot sounded like a silly joke",
        "paint": "the bright colors looked like a party on a table",
        "sand": "the warm sand felt like a thousand soft tickles",
        "sprinklers": "the sprinkler chatter sounded like a laughing hose",
    }.get(activity.id, "it felt like a little adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was quiet, but the shiny floor seemed ready for trouble."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} glittered after the rain."
    return f"{setting.place.capitalize()} looked bright and full of play."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), "cheerful")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved a good plan and a bigger surprise.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    where = "outside" if not world.setting.indoor else "inside"
    world.say(f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label_word} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "went to" if not world.setting.indoor else "came into"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} right away.")
    world.say(f'"Can I?" {hero.pronoun("subject").capitalize()} asked. "{activity.verb.capitalize()} now?"')


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    hero.memes["worry"] += 1
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    line = f'"If you {activity.verb}, your {prize.label} will get {activity.soil}," {parent.label_word} said.'
    world.say(line)
    world.say(f'"Then I would have to clean {prize.it()}," {parent.label_word} added, trying not to laugh too much.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} tried to stay serious, but the idea of playing was too wiggly.")
    world.say(f"{hero.pronoun().capitalize()} started to {activity.rush}.")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} gently grabbed {hero.pronoun('possessive')} hand and said, "
        f'"We can still play. We just need a smarter outfit."'
    )


def pout(world: World, hero: Entity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(f"{hero.id} pouted for exactly one dramatic second.")
        world.say(f'"But I was ready!" {hero.pronoun().capitalize()} said.')


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
    world.say(f'{parent.label_word} looked at the {prize.label}, then at {hero.id}, and smiled.')
    world.say(f'"How about we {gear_def.prep} and still {activity.verb}?" {parent.label_word} asked.')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["relief"] += 1
    world.say(f'{hero.id} grinned so hard it almost counted as a victory dance.')
    world.say(f'"Okay!" {hero.pronoun("subject").capitalize()} said, hugging {hero.pronoun("possessive")} {parent.label_word}.')
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, "
        f"and {parent.label_word} was laughing at how such a tiny plan made such a big difference."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mia",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["traits"] = hero_traits or ["curious", "silly"]
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
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
        conflict=hero.memes["conflict"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"mud", "puddles", "sprinklers"}),
    "park": Setting(place="the park", indoor=False, affords={"puddles", "sprinklers"}),
    "porch": Setting(place="the porch", indoor=False, affords={"rain", "sprinklers"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"paint"}),
}

ACTIVITIES = {
    "puddles": Activity(
        id="puddles",
        verb="jump in the puddles",
        gerund="jumping in puddles",
        rush="dash toward the puddles",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs"},
        weather="rainy",
        keyword="shorts",
        tags={"wet", "puddle"},
    ),
    "mud": Activity(
        id="mud",
        verb="play in the mud",
        gerund="splashing in the mud",
        rush="run to the mud patch",
        mess="muddy",
        soil="all muddy",
        zone={"legs"},
        weather="rainy",
        keyword="shorts",
        tags={"mud", "dirty"},
    ),
    "sprinklers": Activity(
        id="sprinklers",
        verb="run through the sprinklers",
        gerund="running through sprinklers",
        rush="sprint at the sprinkler spray",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs", "torso"},
        weather="sunny",
        keyword="shorts",
        tags={"wet"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint a poster",
        gerund="painting a poster",
        rush="grab the paint cups",
        mess="painted",
        soil="spattered with paint",
        zone={"legs"},
        weather="",
        keyword="shorts",
        tags={"paint", "dirty"},
    ),
    "rain": Activity(
        id="rain",
        verb="dance in the rain",
        gerund="dancing in the rain",
        rush="run out into the rain",
        mess="wet",
        soil="soaking wet",
        zone={"feet", "legs", "torso"},
        weather="rainy",
        keyword="shorts",
        tags={"wet", "rain"},
    ),
}

PRIZES = {
    "shorts": Prize(
        label="shorts",
        phrase="bright red shorts",
        type="shorts",
        region="legs",
        plural=True,
    ),
    "socks": Prize(
        label="socks",
        phrase="fresh white socks",
        type="socks",
        region="feet",
        plural=True,
    ),
    "shirt": Prize(
        label="shirt",
        phrase="a clean blue shirt",
        type="shirt",
        region="torso",
    ),
    "jacket": Prize(
        label="jacket",
        phrase="a soft jacket",
        type="jacket",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="playclothes",
        label="old play clothes",
        covers={"legs", "torso", "feet"},
        guards={"wet", "muddy", "painted"},
        prep="put on old play clothes first",
        tail="went back for the old play clothes",
        plural=True,
    ),
    Gear(
        id="rainboots",
        label="rain boots",
        covers={"feet"},
        guards={"wet", "muddy"},
        prep="put on rain boots first",
        tail="went back for the rain boots",
        plural=True,
    ),
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso"},
        guards={"wet"},
        prep="put on a raincoat first",
        tail="went back for the raincoat",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn"]
TRAITS = ["cheerful", "curious", "silly", "brave", "spirited"]


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
    "shorts": [("What are shorts?", "Shorts are short pants that cover the legs and help keep a person cool.")],
    "wet": [("What does wet mean?", "Wet means something has water on it or is soaked with water.")],
    "mud": [("What is mud?", "Mud is wet dirt that can stick to shoes, clothes, and hands.")],
    "rain": [("Where does rain come from?", "Rain falls from clouds when the clouds get heavy with water drops.")],
    "paint": [("Why can paint be messy?", "Paint can drip, splash, and leave bright stains on clothes and hands.")],
    "dirty": [("Why do dirty clothes need washing?", "Dirty clothes need washing so the stains and mess can come out.")],
    "rainboots": [("What are rain boots for?", "Rain boots help keep your feet dry when the ground is wet or muddy.")],
    "raincoat": [("What does a raincoat do?", "A raincoat helps keep your top dry when it rains.")],
    "playclothes": [("What are play clothes?", "Play clothes are clothes you do not mind getting messy during fun.")],
}
KNOWLEDGE_ORDER = ["shorts", "wet", "mud", "rain", "paint", "dirty", "rainboots", "raincoat", "playclothes"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short comedy story for children using the word "shorts" and a gentle suspenseful moment.',
        f"Tell a story where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a playful story with dialogue that ends with {hero.id} choosing a safer way to play.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    trait = next((t for t in hero.memes.get("traits", []) if t != "little"), hero.type)
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} wants to {act.verb} in {pos} {prize.label}?",
            answer=f"It is about {hero.id}, a little {trait} {hero.type}, and {pos} {pw}.",
        ),
        QAItem(
            question=f"Why did {pw} worry about the {prize.label}?",
            answer=f"{pos.capitalize()} {pw} worried because {hero.id} wanted to {act.verb}, and the {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question=f"What did {hero.id} love before the worry started?",
            answer=f"{hero.id} loved {act.gerund}, and {pos} mood was happy until the warning made the moment suspenseful.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"What made the moment feel tense?",
            answer=f"The moment felt tense because {hero.id} was eager to {act.verb}, but {pos} {pw} gently held {obj} back and warned about the {prize.label}.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} solve the problem?",
            answer=f"They used {gear.label} so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy, because the plan worked and the {prize.label} stayed clean.",
        ))
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
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("backyard", "mud", "shorts", "Mia", "girl", "mother", "curious"),
    StoryParams("park", "puddles", "shorts", "Leo", "boy", "father", "silly"),
    StoryParams("porch", "rain", "jacket", "Nora", "girl", "mother", "brave"),
    StoryParams("playroom", "paint", "shirt", "Ben", "boy", "father", "cheerful"),
    StoryParams("backyard", "sprinklers", "shorts", "Ella", "girl", "mother", "spirited"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, but {noun} sits on the {prize.region}, "
            f"so it would not get {activity.mess}. The parent would not have an honest warning.)"
        )
    return (
        f"(No story: nothing in the gear set protects {noun} from {activity.gerund} in a reasonable way.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
    ap = argparse.ArgumentParser(description="A tiny comedy-suspense storyworld about shorts.")
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "silly"], params.parent)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, activity, prize) combos:")
        for t in vals:
            print("  ", t)
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
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
