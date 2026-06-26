#!/usr/bin/env python3
"""
storyworlds/worlds/slump_shard_moral_value_friendship_rhyme_pirate.py
======================================================================

A small pirate-tale story world about a child pirate, a dangerous shard,
friendship, a moral choice, and a rhyme that lifts a slump.

The world is intentionally tiny and constraint-checked:
- a hero pirate wants to do a lively deck activity;
- a sharp shard can scrape a prized item;
- a captain/parent foresees the mess and warns;
- a friend offers a reasonable fix (protective gear or a careful plan);
- the hero chooses the kinder, safer path, and the slump ends.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py only in ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"sharp": 0.0, "dusty": 0.0, "tidy": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "trust": 0.0, "slump": 0.0, "moral": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "matey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"captain": "captain", "matey": "matey"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the ship"
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sharp(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sharp"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("sharp", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["sharp"] += 1
            item.meters["tidy"] -= 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got scraped by a shard.")
    return out


def _r_slump(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["slump"] < THRESHOLD:
            continue
        sig = ("slump", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} had a heavy slump and could not quite smile.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("sharp", "physical", _r_sharp),
    Rule("slump", "emotional", _r_slump),
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
        "soiled": bool(prize and prize.meters["sharp"] >= THRESHOLD),
        "slump": sum(e.memes["slump"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "shard": "the shard glittered like a tiny sea star",
        "rhyme": "the rhyme bounced along the deck like happy boots",
        "gale": "the wind made the ropes hum like a song",
    }.get(activity.id, "it felt lively and bright")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the ship":
        return "The deck creaked gently, and the mast swayed like a sleepy giant."
    if setting.place == "the dock":
        return "The dock smelled of salt, rope, and old sea stories."
    return f"{setting.place.capitalize()} looked salt-bright and ready for a pirate day."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    if activity.id == "rhyme":
        actor.memes["trust"] += 1
        actor.memes["slump"] = max(0.0, actor.memes["slump"] - 1)
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} pirate who liked bright ropes, brave tunes, and tidy decks.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One week, {hero.id}'s {parent.label_word} brought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["trust"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} as if it were a lucky flag."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"sunny": "One sunny day, ", "windy": "One windy day, "}.get(world.weather, "One day, ")
    go = "were on" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["slump"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label_word} held up a hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_slump"] = pred["slump"]
    world.say(
        f'"You\'ll get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label_word} said. '
        f'"Let\'s keep the ship safe."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["slump"] += 1
    world.say(f"{hero.id} felt a little slump in {hero.pronoun('possessive')} chest, but the tune still tugged at {hero.pronoun('object')}.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} took {hero.pronoun('possessive')} hand and said, "
        f'"A true pirate keeps a good heart and a safe deck."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["slump"] >= THRESHOLD:
        world.say(
            f"{hero.id} pouted for a blink, then whispered, "
            f'"I can wait if we find a clever way."'
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
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} smiled and said, "
        f'"How about we {gear_def.prep} and then {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["slump"] = 0.0
    hero.memes["moral"] += 1
    world.say(
        f"{hero.id}'s face brightened, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label_word}."
    )
    world.say(
        f'"Aye, let\'s do it!" {hero.pronoun()} sang. Then they {gear_def.tail}.'
    )
    world.say(
        f"Soon {hero.id} was {activity.gerund}, {prize_was_clean(hero, prize)}, and the deck rang with a merry rhyme."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    parent_type: str = "captain",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "playful"]),
    ))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
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
    pout(world, hero, activity)
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
        conflict=hero.memes["slump"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "ship": Setting(place="the ship", indoor=False, affords={"shard", "rhyme", "gale"}),
    "dock": Setting(place="the dock", indoor=False, affords={"shard", "rhyme"}),
    "cove": Setting(place="the cove", indoor=False, affords={"shard", "gale"}),
}

ACTIVITIES = {
    "shard": Activity(
        id="shard",
        verb="dance near the shard",
        gerund="dancing near the shard",
        rush="dash toward the shiny shard",
        mess="sharp",
        soil="scratched and snagged",
        zone={"feet", "legs"},
        weather="windy",
        keyword="shard",
        tags={"shard", "sharp"},
    ),
    "rhyme": Activity(
        id="rhyme",
        verb="sing a rhyme",
        gerund="singing a rhyme",
        rush="burst into a loud rhyme",
        mess="dusty",
        soil="dusty",
        zone={"torso"},
        weather="",
        keyword="rhyme",
        tags={"rhyme"},
    ),
    "gale": Activity(
        id="gale",
        verb="race in the gale",
        gerund="racing in the gale",
        rush="run at the windy deck",
        mess="sharp",
        soil="scratched",
        zone={"feet", "legs"},
        weather="windy",
        keyword="gale",
        tags={"gale", "sharp"},
    ),
}

GEAR = [
    Gear(
        id="boots",
        label="sea boots",
        covers={"feet"},
        guards={"sharp"},
        prep="put on sea boots first",
        tail="put on the sea boots and stepped out",
        plural=True,
    ),
    Gear(
        id="vest",
        label="a thick vest",
        covers={"torso"},
        guards={"dusty"},
        prep="put on a thick vest first",
        tail="buttoned the thick vest and went on",
    ),
]

PRIZES = {
    "boots": Prize(label="boots", phrase="new sea boots", type="boots", region="feet", plural=True),
    "cloak": Prize(label="cloak", phrase="a striped pirate cloak", type="cloak", region="torso"),
    "sash": Prize(label="sash", phrase="a bright sash", type="sash", region="legs"),
}

GIRL_NAMES = ["Mira", "Tess", "Nell", "Ruby", "Lila", "Mina"]
BOY_NAMES = ["Finn", "Jory", "Pip", "Oren", "Kai", "Toby"]
TRAITS = ["brave", "cheery", "stubborn", "lively", "kind"]


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
    "shard": [("What is a shard?", "A shard is a sharp piece broken off from something like glass, wood, or pottery.")],
    "sharp": [("Why are sharp things handled carefully?", "Sharp things can scratch skin or tear cloth, so people move them with care.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a little bit of song or verse where words sound friendly together.")],
    "pirate": [("What is a pirate?", "A pirate is a sea traveler from old stories who sails ships and looks for treasure.")],
    "boots": [("What are sea boots for?", "Boots help keep feet protected and ready for wet or rough places.")],
    "moral": [("What does it mean to do the moral thing?", "It means choosing what is kind, honest, and safe, even when something else looks fun.")],
    "friendship": [("What is friendship?", "Friendship is when people care about each other, help each other, and enjoy being together.")],
}
KNOWLEDGE_ORDER = ["pirate", "shard", "sharp", "rhyme", "boots", "moral", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.id
    return [
        f'Write a short pirate tale for a young child that includes the word "{kw}" and ends with a cheerful rhyme.',
        f"Tell a story where {hero.id}, a little pirate, wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a gentle friendship story about a pirate deck, a shiny shard, and choosing the safe and kind path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the pirate story about at {place}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do near the shard?",
            answer=f"{hero.id} wanted to {act.verb}, but the sharp shard made that feel risky until they found a safer way.",
        ),
        QAItem(
            question=f"Why did {pw} worry about {pos} {prize.label}?",
            answer=(
                f"{pos.capitalize()} {pw} worried because the shard could leave {obj} {act.soil}, "
                f"so the prize would not stay safe."
            ),
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the friend-like help keep {pos} {prize.label} safe?",
            answer=(
                f"They used {gear.label}, which covered the right place and let {hero.id} stay safe while they {act.gerund}."
            ),
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=(
                f"{hero.id} felt glad and brave again. The slump lifted after the kind plan, and {sub} finished the day smiling."
            ),
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
    StoryParams(place="ship", activity="shard", prize="boots", name="Mira", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="dock", activity="shard", prize="sash", name="Finn", gender="boy", parent="captain", trait="kind"),
    StoryParams(place="cove", activity="gale", prize="boots", name="Tess", gender="girl", parent="captain", trait="cheery"),
    StoryParams(place="ship", activity="rhyme", prize="cloak", name="Pip", gender="boy", parent="captain", trait="lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, but {noun} {verb} on the {prize.region}; "
            f"it would not get {activity.soil}, so the captain would have no real warning.)"
        )
    return (
        f"(No story: nothing in the gear catalog protects {noun} from {activity.gerund}. "
        f"The fix must actually cover the at-risk item.)"
    )


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
        description="Story world sketch: a pirate tale about a shard, a slump, "
                    "friendship, a moral choice, and a rhyme."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
