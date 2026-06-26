#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/astrology_rhyme_fairy_tale.py
===========================================================================================================

A small story world for an astrology-flavored fairy tale with gentle rhyme.

Seed tale idea:
---
A little child loves to follow the stars. One evening, the child wants to go
out in a special outfit for a moonlit wish. A kind fairy reads the sky, warns
that the night will be damp or windy, and offers a rhyme and a proper cover so
the child can still go safely.

World model:
---
The child has a desire, the sky has a sign, the sign predicts a kind of trouble,
and a fitting charm or cover can resolve the problem. The simulation keeps both
physical meters and emotional memes so the story is driven by state rather than
by a frozen paragraph with swapped names.

Narrative instruments:
---
* astrology: zodiac signs, moon phase, omen, chart-reading
* rhyme: small child-facing rhyming lines and couplets
* fairy tale: kind guide, moonlit path, wish, happy ending
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

SIGNS = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def _e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man", "wizard"}
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
    omen: str
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
        self.sky: str = ""
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


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("damp", "sparkled"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["tired"] = item.meters.get("tired", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} grew damp in the moonlit mist.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("tired", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would have made more work for {carer.label}.")
    return out


def _r_misgiving(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("doubt", 0.0) < THRESHOLD or actor.memes.get("held_back", 0.0) < THRESHOLD:
            continue
        sig = ("misgiving", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["misgiving"] = actor.memes.get("misgiving", 0.0) + 1
        return ["__misgiving__"]
    return []


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("worry", _r_worry), Rule("misgiving", _r_misgiving)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__misgiving__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_at_risk(activity: Activity, prize: Prize) -> bool:
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
    return {"soiled": bool(prize and prize.meters.get("tired", 0.0) >= THRESHOLD), "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside, the little hall was still, and the moonbeam waited on the sill."
    return {
        "meadow": "The meadow was soft, and the grass shone silver under the stars.",
        "tower_garden": "The tower garden was quiet, with roses nodding toward the sky.",
        "forest_glade": "The forest glade was deep and green, and the night air was thin and bright.",
    }.get(setting.place, f"{setting.place.capitalize()} glimmered in the hush of night.")


class _CopyWorldMixin:
    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label, "phrase": v.phrase,
            "traits": list(v.traits), "owner": v.owner, "caretaker": v.caretaker, "worn_by": v.worn_by,
            "region": v.region, "protective": v.protective, "covers": set(v.covers), "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.sky = self.sky
        clone.paragraphs = [[]]
        return clone


World.copy = _CopyWorldMixin.copy  # type: ignore


def introduces(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "gentle")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved the stars and their silver song.")


def loves_astrology(world: World, hero: Entity, activity: Activity, sign: str) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved astrology, and the sky said {sign} in a shimmering rhyme.")
    world.say(f"{activity.keyword.capitalize()} dreams felt bright at night, like a candle in a window light.")


def gives_charm(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One eve, {hero.id}'s {parent.label} gave {hero.pronoun('object')} {prize.phrase} to wear with pride.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label}, for it shone like a little moon tide.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} lifted a hand so neat.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f"\"Your {prize.label} will get {activity.soil},\" {parent.label} said, \"if we rush into the sleet.\"")
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1
    world.say(f"{hero.id} frowned a little, for the wish still twinkled bright and sweet.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def hold_back(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held_back"] = hero.memes.get("held_back", 0.0) + 1
    propagate(world, narrate=False)
    world.say(f"but {hero.pronoun('possessive')} {parent.label} held {hero.pronoun('possessive')} hand and said,")
    world.say(f"\"We can still go, but first let's do it the wiser way, by moon and rhyme.\"")


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} smiled and sang,")
    world.say(f"\"{gear_def.prep}, and then we'll {activity.verb} at the fair!\"")
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["doubt"] = 0.0
    world.say(f"{hero.id} beamed and hugged {hero.pronoun('possessive')} {parent.label}, as soft as a feather in flight.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, with {prize.label} safe and bright.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mila", hero_type: str = "girl", hero_traits: Optional[list[str]] = None, parent_type: str = "mother", sign: str = "virgo") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["gentle", "dreamy"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the fairy godmother"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural))
    world.sky = sign

    introduces(world, hero)
    loves_astrology(world, hero, activity, sign)
    gives_charm(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    hold_back(world, parent, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear_def, sign=sign, conflict=hero.memes.get("held_back", 0.0) >= THRESHOLD, resolved=gear_def is not None)
    return world


SETTINGS = {
    "meadow": Setting(place="the moon meadow", indoor=False, affords={"dewdance", "starlight"}),
    "tower_garden": Setting(place="the tower garden", indoor=False, affords={"dewdance", "cometwalk"}),
    "forest_glade": Setting(place="the forest glade", indoor=False, affords={"mistwalk", "starlight"}),
    "lantern_hall": Setting(place="the lantern hall", indoor=True, affords={"starlight"}),
}

ACTIVITIES = {
    "dewdance": Activity("dewdance", "dance in the dew", "dancing in the dew", "skip toward the wet grass", "damp", "damp and cold", {"feet", "legs"}, "a dewy night", "dew", {"dew", "night"}),
    "mistwalk": Activity("mistwalk", "walk in the mist", "walking in the mist", "stroll into the silver fog", "damp", "damp and chilly", {"torso"}, "a misty night", "mist", {"mist", "night"}),
    "starlight": Activity("starlight", "sing to the stars", "singing to the stars", "run out to the open sky", "sparkled", "sparkled and tired", {"torso", "feet"}, "a starry night", "star", {"stars", "night"}),
    "cometwalk": Activity("cometwalk", "follow the comet", "following the comet", "hurry after the bright trail", "sparkled", "sparkled and weary", {"head"}, "a comet night", "comet", {"comet", "night"}),
}

PRIZES = {
    "crown": Prize("crown", "a little silver crown", "crown", "head"),
    "cloak": Prize("cloak", "a moon-blue cloak", "cloak", "torso"),
    "slippers": Prize("slippers", "soft star slippers", "slippers", "feet", plural=True),
    "ribbon": Prize("ribbon", "a glowing ribbon", "ribbon", "head"),
}

GEAR = [
    Gear("hood", "a soft hood", {"head"}, {"sparkled", "damp"}, "put on a soft hood first", "went back for the soft hood"),
    Gear("boots", "moon boots", {"feet"}, {"damp", "sparkled"}, "wear moon boots before we roam", "returned for the moon boots", True),
    Gear("shawl", "a warm shawl", {"torso"}, {"damp", "sparkled"}, "tie on a warm shawl and glow", "went back for the warm shawl"),
]

GIRL_NAMES = ["Mila", "Nora", "Luna", "Eve", "Ruby", "Ivy", "Pippa", "Mara"]
BOY_NAMES = ["Theo", "Finn", "Robin", "Owen", "Jasper", "Nico", "Bram", "Ezra"]
TRAITS = ["curious", "gentle", "brave", "bright", "dreamy", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if activity_at_risk(act, prize) and select_gear(act, prize):
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
    sign: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "stars": [("What are stars?", "Stars are faraway suns that twinkle in the night sky.")],
    "moon": [("What is the moon?", "The moon is a bright round body in the sky that shines at night.")],
    "zodiac": [("What is the zodiac?", "The zodiac is a set of star signs people use when they talk about astrology.")],
    "dew": [("What is dew?", "Dew is tiny drops of water that gather on grass and leaves when the air is cool.")],
    "mist": [("What is mist?", "Mist is a light cloud of tiny water drops that hangs close to the ground.")],
    "comet": [("What is a comet?", "A comet is a icy space traveler with a glowing tail.")],
    "boots": [("What are boots for?", "Boots help keep feet dry and clean in wet places.")],
    "shawl": [("What is a shawl?", "A shawl is a wrap you wear around your shoulders to stay warm.")],
    "hood": [("What does a hood do?", "A hood helps cover your head from drizzle, wind, or dust.")],
}
KNOWLEDGE_ORDER = ["zodiac", "moon", "stars", "comet", "dew", "mist", "boots", "shawl", "hood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a fairy tale for a young child that includes astrology and the word "{f["sign"]}".',
        f"Tell a rhyming story where {hero.id} wants to {act.verb} at {world.setting.place} while wearing {prize.phrase}.",
        f"Write a gentle starry tale in rhyme about a child and a fairy godmother finding a safer way to play.",
        f"Make the sky feel magical, but let the ending show how the {prize.label} stayed safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to {world.setting.place} under {f['sign']} skies?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {pw}, a fairy godmother who listens to the stars.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}, because the night felt magical and full of rhyme.",
        ),
        QAItem(
            question=f"What shiny thing did {hero.id} wear?",
            answer=f"{hero.id} wore {prize.phrase}, which looked bright in the moonlight.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {pw} warn {hero.id} about the plan?",
            answer=f"{pw} warned {hero.id} because the stars said the night would bring {act.soil}, and the {prize.label} could get ruined.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id}?",
            answer=f"{gear.label.capitalize()} helped by covering the right part of {hero.id}'s outfit, so {hero.id} could still {act.verb} without harming the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave at the end, because the plan worked and the stars still shone kindly.",
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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("meadow", "dewdance", "slippers", "Mila", "girl", "mother", "gentle", "virgo"),
    StoryParams("forest_glade", "mistwalk", "cloak", "Theo", "boy", "father", "brave", "cancer"),
    StoryParams("tower_garden", "cometwalk", "crown", "Luna", "girl", "mother", "bright", "leo"),
    StoryParams("lantern_hall", "starlight", "ribbon", "Ezra", "boy", "mother", "dreamy", "pisces"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not activity_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so the {noun} would not truly be in danger.)"
    return f"(No story: no gear in this world covers {noun} on the {prize.region} in a way that also suits {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


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
    ap = argparse.ArgumentParser(description="Astrology rhyme fairy tale storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--sign", choices=SIGNS)
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
        if not (activity_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos() if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    sign = args.sign or rng.choice(SIGNS)
    return StoryParams(place, activity, prize_id, name, gender, parent, trait, sign)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "stubborn"], params.parent, params.sign)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
            print(f"  {place:12} {act:10} {prize:10}  [{', '.join(genders)}]")
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
