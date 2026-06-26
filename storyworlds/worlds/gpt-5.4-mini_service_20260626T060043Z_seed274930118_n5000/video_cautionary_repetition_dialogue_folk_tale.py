#!/usr/bin/env python3
"""
storyworlds/worlds/video_cautionary_repetition_dialogue_folk_tale.py
=====================================================================

A small storyworld built from a folk-tale seed about a child, a video, and a
careful warning. The domain keeps the tale close to a cautionary folk pattern:
a child wants to make a video, an elder warns about a real danger, the child
pushes back, and a workable protective choice lets the filming happen safely.

The world is intentionally narrow. Only a few settings, activities, and pieces
of gear are allowed, because the story should feel like a shaped tale rather
than a random swap of nouns.

Seed image:
- A child wants to make a video of a bright moment.
- The weather or place threatens the video gear.
- An elder warns, repeats the warning, and offers a safe way.
- The child accepts, and the ending proves what changed.

Narrative instruments used:
- Cautionary warning
- Repetition
- Dialogue
- Folk-tale cadence
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
MESS_KINDS = {"wet", "muddy", "dusty"}
REGIONS = {"hands", "torso", "head"}


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


def _r_soak(world: World) -> list[str]:
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
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("soak", "physical", _r_soak),
    Rule("workload", "physical", _r_workload),
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
                produced.extend(sents)
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
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "video": "the bright little screen made the moment feel like a keepsake",
        "rain": "the raindrops made a silver music on the roof",
        "mud": "the soft squish underfoot made the lane feel like a game",
        "mist": "the river mist hung like a pale shawl over the field",
    }.get(activity.id, "it made the day feel full of story")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the room was quiet and the lamp burned steady."
    if activity.weather == "rainy":
        return f"Outside, {setting.place} smelled fresh, and the air was damp with rain."
    return f"{setting.place.capitalize()} looked open and bright, with room for a small tale."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved to gather small wonders before they slipped away.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That week, {hero.id}'s {parent.label_word} bought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and kept {prize.it()} close, "
        f"as if the day itself had a heartbeat."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} "
        f"{parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Do not be careless, child."')
    return True


def repeat_warning(world: World, parent: Entity, activity: Activity) -> None:
    world.say(
        f'"Do not {activity.verb}," {parent.label_word} said. '
        f'"Do not {activity.verb} where the wet ground can reach what you love."'
    )


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to tell the story still tugged at {hero.pronoun('possessive')} sleeve.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} caught {hero.pronoun('possessive')} hand and said, "
        f'"A wise child listens before the trouble arrives."'
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
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the {prize.label}, then back at {hero.id}, and smiled. '
        f'"How about we {gear_def.prep} and {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yes, yes," {hero.pronoun()} said. "Let us do it the safe way."'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize_was_clean(hero, prize)}, "
        f"and the little video was made without harm."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the elder"))
    prize = world.add(Entity(
        id="video",
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
    repeat_warning(world, parent, activity)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    world.para()
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
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "riverbank": Setting(place="the riverbank", indoor=False, affords={"mist", "rain"}),
    "lane": Setting(place="the lane", indoor=False, affords={"mud"}),
    "porch": Setting(place="the porch", indoor=False, affords={"rain", "mist"}),
    "cottage": Setting(place="the cottage", indoor=True, affords={"video"}),
}

ACTIVITIES = {
    "video": Activity(
        id="video",
        verb="film the village dance",
        gerund="filming the village dance",
        rush="rush to film the dance in the wet grass",
        mess="wet",
        soil="soaking wet",
        zone={"hands", "torso"},
        weather="rainy",
        keyword="video",
        tags={"video", "wet"},
    ),
    "mist": Activity(
        id="mist",
        verb="film the river mist",
        gerund="filming the river mist",
        rush="run to the misty bank",
        mess="wet",
        soil="damp and ruined",
        zone={"hands", "torso", "head"},
        weather="rainy",
        keyword="video",
        tags={"video", "mist", "wet"},
    ),
    "rain": Activity(
        id="rain",
        verb="make a rain video",
        gerund="making a rain video",
        rush="dash out into the rain with the camera",
        mess="wet",
        soil="wet and heavy",
        zone={"hands", "torso", "head"},
        weather="rainy",
        keyword="video",
        tags={"video", "rain", "wet"},
    ),
    "mud": Activity(
        id="mud",
        verb="film the muddy cart path",
        gerund="filming the muddy cart path",
        rush="run to the muddy path",
        mess="muddy",
        soil="mud-spattered",
        zone={"hands", "torso"},
        weather="rainy",
        keyword="video",
        tags={"video", "muddy"},
    ),
}

PRIZES = {
    "camera": Prize(
        label="video camera",
        phrase="a little video camera with a bright blue strap",
        type="camera",
        region="hands",
        genders={"girl", "boy"},
    ),
    "tablet": Prize(
        label="video tablet",
        phrase="a small video tablet with a shiny screen",
        type="tablet",
        region="hands",
        genders={"girl", "boy"},
    ),
    "cloak": Prize(
        label="story cloak",
        phrase="a soft story cloak for special days",
        type="cloak",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="oilcloth",
        label="an oilcloth case",
        covers={"hands"},
        guards={"wet", "muddy"},
        prep="put the camera in an oilcloth case first",
        tail="walked back to the porch to keep the oilcloth case dry",
    ),
    Gear(
        id="hood",
        label="a waxed hood",
        covers={"head", "torso"},
        guards={"wet"},
        prep="draw a waxed hood over the camera first",
        tail="stood under the hood and kept the camera safe",
    ),
    Gear(
        id="wrap",
        label="a dry cloth wrap",
        covers={"hands", "torso"},
        guards={"wet", "muddy"},
        prep="wrap the camera in a dry cloth first",
        tail="kept the camera wrapped while the rain pattered by",
    ),
]

GIRL_NAMES = ["Mira", "Tessa", "Anya", "Nora", "Lina", "Ivy"]
BOY_NAMES = ["Pip", "Robin", "Milo", "Evan", "Bram", "Jory"]
TRAITS = ["curious", "stubborn", "cheerful", "quiet", "brave"]


def valid_combos() -> list[tuple[str, str]]:
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
    "video": [("What is a video?", "A video is a moving picture that records what happens so you can watch it again later.")],
    "wet": [("Why can wet things get heavier?", "Wet things can get heavier because water soaks into them and clings to them.")],
    "mud": [("What is mud?", "Mud is soft, wet dirt. It sticks to shoes, hands, and clothes.")],
    "rain": [("Where does rain come from?", "Rain falls from clouds when tiny water drops join together and become too heavy.")],
    "mist": [("What is mist?", "Mist is a thin cloud of tiny water drops that hangs near the ground.")],
    "oilcloth": [("What is an oilcloth case for?", "An oilcloth case helps keep a thing dry when the weather is wet.")],
    "cloak": [("What is a cloak?", "A cloak is a loose covering that drapes over your clothes and helps keep them safe.")],
}
KNOWLEDGE_ORDER = ["video", "wet", "rain", "mist", "mud", "oilcloth", "cloak"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or "video"
    return [
        f'Write a folk tale for a young child about a child who wants to make a "{kw}" and must listen to a warning.',
        f"Tell a short story where {hero.id} wants to {act.verb}, but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a repetition-rich tale where the phrase '{act.verb}' is repeated and the child chooses the safe way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"rainy": "rainy day", "sunny": "sunny day"}.get(world.weather, "play day")
    qa = [
        QAItem(
            question=f"Who is the tale about when {hero.id} goes to {place} to {act.verb} with the {prize.label}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. They go to {place} on a {day}, and {hero.id} is carrying the {prize.label}.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} want to do {where} before {pw} gave a warning?",
            answer=f"{trait.capitalize()} {hero.id} wanted to {act.gerund}. That idea was exciting, but it could harm {pos} {prize.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {pw} speak so carefully about the {prize.label}?",
            answer=(
                f"{pos.capitalize()} {pw} spoke carefully because if {hero.id} tried to {act.verb}, "
                f"{pos} {prize.label} would get {act.soil}. Then the {prize.label} would need cleaning or repair."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        work = f.get("predicted_workload", 0)
        why = f"{pos.capitalize()} {pw} worried because the {prize.label} would get {soil} if {hero.id} went ahead."
        if work >= THRESHOLD:
            why += f" Then {pw} would have more work."
        why += f" When {hero.id} tried to {act.rush}, {pos} {pw} held {obj}'s hand and repeated the warning."
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} stop {obj} before the {act.keyword or 'video'} was made?",
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} make the {act.keyword or 'video'} safely?",
            answer=f"They used {gear.label} first, so {hero.id} could {act.verb} without ruining {pos} {prize.label}. The safe covering kept the wet and mud away.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel when the {gear_plan} plan was chosen?",
            answer=f"{hero.id} felt happy and hugged {pos} {pw}. In the end, {sub} was {act.gerund}, and the little {act.keyword or 'video'} was finished safely.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
    StoryParams(place="riverbank", activity="mist", prize="camera", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="porch", activity="rain", prize="tablet", name="Pip", gender="boy", parent="father", trait="stubborn"),
    StoryParams(place="lane", activity="mud", prize="camera", name="Nora", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="cottage", activity="video", prize="cloak", name="Robin", gender="boy", parent="father", trait="cheerful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, but {noun} {verb} on the {prize.region} and would stay safe.)"
    return f"(No story: no gear in this tiny world truly protects {noun} from {activity.gerund}. The warning needs a real fix.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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
        description="Story world sketch: a cautionary folk tale about a video and a safe compromise."
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
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
