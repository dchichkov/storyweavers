#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/morphodite_sharing_magic_space_adventure.py
==============================================================================================================

A standalone story world sketch for morphodite sharing magic space adventure tales.

Initial story (used to build a world model):
---
On a faraway star, a shimmering morphodite named Glimmer lived with its friend Zork.
A morphodite could change its shape and glow with magic. Zork was a small robot who
loved collecting space rocks. One day, a glowing crystal appeared on the star.
The crystal held Sharing Magic: whoever touched it could share feelings and energy.

Zork touched the crystal and felt Glimmer's joy. "We can share our magic!"
said Zork. But Zork also felt the crystal getting dimmer. "If we use too much
sharing, the magic might fade," said Glimmer. Zork wanted to share the magic
with all the star creatures, but Glimmer worried the crystal would break.

Zork kept sending out warm feelings to the moon bunnies. The crystal flickered.
Glimmer said, "We must share carefully, not too much at once." Zork nodded and
they agreed to share only a little each day. The crystal stayed bright, and the
star creatures learned to share magic gently.
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

MAGIC_KINDS = {"glow", "warm", "shape", "light"}
REGIONS = {"core", "aura", "shell"}


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
        if self.type in {"morphodite", "robot", "crystal", "moon_bunny"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label


@dataclass
class Setting:
    place: str = "the star"
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
    genders: set[str] = field(default_factory=lambda: {"morphodite", "robot", "moon_bunny"})


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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_drain(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for magic in MAGIC_KINDS:
            if actor.meters[magic] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("drain", item.id, magic)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[magic] += 1
                item.meters["dim"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"flickered and grew dim."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dim"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would sap the magic from {carer.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="drain", tag="physical", apply=_r_drain),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
        "soiled": bool(prize and prize.meters["dim"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "share": "the gentle pulse of shared feeling made the star hum with joy",
        "glow": "the bright light made the star creatures dance in wonder",
        "shape": "the morphodite twisted into fun forms and everyone laughed",
    }.get(activity.id, "it made the space feel full of friendship")


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place.removeprefix('the ')} glittered, and the crystal waited with its quiet magic."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} still glowed bright"


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
    world.say(f"{hero.id} was a {desc} on a faraway star, shimmering with magic.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That day, {hero.id}'s {parent.label_word} brought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"held {prize.it()} close, feeling its gentle hum."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One starlit evening, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} floated near the glowing crystal."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} raised a worried light."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Your {prize.label} will grow {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and the crystal will need to rest"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let us share carefully."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the urge to share was still pulling hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} glowed softly and said, "
        f'"You can want to {activity.verb}, and we can still be gentle."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} dimmed its light and crossed its feelers. '
            f'"But I want to {activity.verb}!" it said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and pulsed warmly. '
        f'"How about we {gear_def.prep} and {activity.verb} a little?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s light grew bright and it hummed with "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yes, let us do it!" it said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_clean(hero, prize)}, and the crystal shone steady above them."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Glimmer", hero_type: str = "morphodite",
         hero_traits: Optional[list[str]] = None, parent_type: str = "crystal") -> World:
    world = World(setting)
    world.weather = ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "eager"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the crystal"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
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

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "star": Setting(place="the star", affords={"share", "glow", "shape"}),
    "nebula": Setting(place="the nebula", affords={"share", "glow"}),
    "moon": Setting(place="the moon", affords={"share", "shape"}),
}

ACTIVITIES = {
    "share": Activity(
        id="share",
        verb="share magic with everyone",
        gerund="sharing warm feelings",
        rush="send out the sharing pulse",
        mess="warm",
        soil="dim and tired",
        zone={"aura", "core"},
        keyword="sharing",
        tags={"sharing", "magic"},
    ),
    "glow": Activity(
        id="glow",
        verb="glow as bright as the crystal",
        gerund="glowing with magic light",
        rush="flare up brightly",
        mess="light",
        soil="flickering and weak",
        zone={"aura", "shell"},
        keyword="glow",
        tags={"magic", "light"},
    ),
    "shape": Activity(
        id="shape",
        verb="change into funny forms",
        gerund="shifting into new shapes",
        rush="twist into a new shape",
        mess="shape",
        soil="wobbly and loose",
        zone={"shell"},
        keyword="shape",
        tags={"magic", "morphodite"},
    ),
}

GEAR = [
    Gear(
        id="shield",
        label="a gentle shield",
        covers={"aura"},
        guards={"warm", "light"},
        prep="use the gentle shield first",
        tail="pulled the gentle shield around themselves",
    ),
    Gear(
        id="wrap",
        label="a soft energy wrap",
        covers={"core", "shell"},
        guards={"warm", "light", "shape"},
        prep="wrap in a soft energy wrap",
        tail="wrapped in the soft energy cloak",
    ),
]

PRIZES = {
    "crystal_shard": Prize(
        label="crystal shard",
        phrase="a shimmering crystal shard",
        type="crystal_shard",
        region="core",
        genders={"morphodite", "robot", "moon_bunny"},
    ),
    "glowing_orb": Prize(
        label="glowing orb",
        phrase="a small glowing orb",
        type="glowing_orb",
        region="aura",
        genders={"morphodite", "robot", "moon_bunny"},
    ),
    "moon_stone": Prize(
        label="moon stone",
        phrase="a smooth moon stone",
        type="moon_stone",
        region="shell",
        genders={"morphodite", "moon_bunny"},
    ),
}

HERO_NAMES = ["Glimmer", "Zork", "Luna", "Nova", "Twinkle", "Orbit", "Stella", "Comet", "Pulse", "Flare"]
TRAITS = ["curious", "eager", "brave", "gentle", "playful", "kind"]


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
    "sharing": [("What is sharing magic?",
                 "Sharing magic is when one creature sends warm feelings or energy "
                 "to another. It makes everyone feel connected and happy.")],
    "magic": [("What is magic in space?",
               "Space magic is a gentle glow that lives in crystals and morphodites. "
               "It can change shapes, share feelings, or light up the dark.")],
    "morphodite": [("What is a morphodite?",
                    "A morphodite is a friendly space creature that can change its "
                    "shape and glow with soft magic light.")],
    "crystal": [("What does a space crystal do?",
                 "A space crystal holds magic energy. When shared gently, it lights "
                 "up the star; when used too much, it grows dim.")],
    "glow": [("Why does the morphodite glow?",
              "A morphodite glows because it is full of magic. The glow gets brighter "
              "when it is happy and share magic with friends.")],
}
KNOWLEDGE_ORDER = ["sharing", "magic", "morphodite", "crystal", "glow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short space adventure story for a young child about a morphodite '
        f'who learns about sharing magic, using the word "{kw}".',
        f"Tell a gentle tale where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize.phrase}, and they find a careful compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with friends '
        f"agreeing to share magic gently.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pw}. They go to {place}, and {hero.id} is "
                f"holding {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do on {place} before "
                f"{pw} worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund}. That urge became "
                f"tricky because {pos} {prize.label} could grow dim."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {pw} bring for the "
                f"{trait} {hero.type} before "
                f"the {act.keyword or act.mess} play at {place}?"
            ),
            answer=(
                f"{pw} brought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and held {prize.it()} close."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "dim")
        work = f.get("predicted_workload", 0)
        why = (f"{pw} was worried because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then the magic would fade. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pw} "
                f"glowed softly and reminded {obj} they could share gently.")
        qa.append(QAItem(
            question=(
                f"Why did {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb} at {place}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} {act.verb} at {place} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without dimming {pos} {prize.label}. "
                f"The plan let {obj} play while the crystal stayed bright."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} agreed to the {gear_plan} "
                f"plan for {act.keyword or act.mess} at {place}?"
            ),
            answer=(
                f"{hero.id} glowed bright and hummed happily once they agreed "
                f"on the plan for {pos} {prize.label}. At the end, {sub} was "
                f"{act.gerund} with {pw} shining nearby."
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
    StoryParams(
        place="star",
        activity="share",
        prize="crystal_shard",
        name="Glimmer",
        gender="morphodite",
        parent="crystal",
        trait="curious",
    ),
    StoryParams(
        place="nebula",
        activity="glow",
        prize="glowing_orb",
        name="Zork",
        gender="robot",
        parent="crystal",
        trait="eager",
    ),
    StoryParams(
        place="moon",
        activity="shape",
        prize="moon_stone",
        name="Luna",
        gender="moon_bunny",
        parent="crystal",
        trait="brave",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the crystal has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}.)")


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
        description="Story world sketch: a morphodite, sharing magic, space adventure. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["morphodite", "robot", "moon_bunny"])
    ap.add_argument("--parent", choices=["crystal"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))

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
    parent = args.parent or "crystal"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "eager"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
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
