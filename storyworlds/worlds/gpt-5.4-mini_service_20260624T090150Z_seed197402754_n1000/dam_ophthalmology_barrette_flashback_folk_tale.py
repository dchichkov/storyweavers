#!/usr/bin/env python3
"""
storyworlds/worlds/dam_ophthalmology_barrette_flashback_folk_tale.py
====================================================================

A small folk-tale storyworld about a village dam, an eye doctor, and a lost
barrette, told with a brief flashback and a gentle resolution.

Premise:
- A child admires a bright barrette and wants to use it.
- A careful elder remembers a past lesson from an ophthalmology visit.
- A village dam and its spillway become the setting for the child's bright idea.

Tension:
- The child wants to play near water and breeze, but the barrette could slip
  away or muddy the child's hair.
- The elder fears the child will not see the trouble in time, recalling the
  earlier eye checkup as a flashback.

Turn:
- The elder suggests a safer place and a steadier way to wear the barrette.
- A small helper ritual from the eye clinic becomes part of the solution.

Resolution:
- The child keeps the barrette, sees the water from a safe spot, and the tale
  ends with the dam standing calm under evening light.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

FOLK_OPENERS = [
    "Once, in a small village between hills and water,",
    "Long ago, where the reeds bowed and the lanterns glowed,",
    "In a quiet valley with a stone dam and a winding path,",
    "In the days when every river was said to carry a song,",
    "Once beside a dam of gray stones and silver water,",
]

SCENES = [
    "Swallows skimmed above the quiet pool while the spillway hummed below.",
    "Reeds nodded at the water's edge, and sunlight flashed on every ripple.",
    "The dam keeper's bell gave one soft clang as the afternoon breeze arrived.",
    "Cloud shadows crossed the reservoir while the old stones shone after rain.",
]

EVENTS = {
    "spray": {
        "warning": "a silver fan of spray can leap over the rail without warning",
        "event": "Just then, a burst of spray flew over the rail and freckled the stones.",
        "clue": "dark spots spreading across the pale rock",
        "effect": "wet",
        "danger": "the slick edge",
    },
    "gust": {
        "warning": "a strong gust can tug at loose things near the spillway",
        "event": "Just then, a gust rushed up the dam and snapped the ends of the ribbon like little flags.",
        "clue": "the reeds bending all at once",
        "effect": "windblown",
        "danger": "the windy path",
    },
    "glare": {
        "warning": "the bright water can hide the wet line on the stones",
        "event": "Just then, the sun slipped from a cloud and laid a dazzling path across the water.",
        "clue": "a dull, safe stone beside the bright glare",
        "effect": "glare",
        "danger": "the shining wet stones",
    },
}

LESSONS = {
    "steady": {
        "memory": "Look at one steady thing before you take your next step.",
        "action": "fixed her eyes on the iron rail, then looked carefully at the path beside it",
    },
    "near_far": {
        "memory": "When a bright view confuses you, look near, then far, and near once more.",
        "action": "looked at her own shoes, across the reservoir, and back to the stones",
    },
    "shade": {
        "memory": "Shade your eyes from a hard glare, and give them a moment to see clearly.",
        "action": "shaded her eyes with one hand and waited until the edges of the path became clear",
    },
}

ENDING_IMAGES = {
    "lanterns": "That evening, two lanterns glowed on the safe lookout while the blue shell in the barrette held one tiny spark of light.",
    "swallow": "As they walked home, a swallow crossed the copper sky, and the barrette sat firm above a dry, smiling face.",
    "reflection": "Below them, the dam's calm pool held the first star, and the barrette answered with a small blue gleam.",
    "bell": "Behind them, the dam keeper's bell rang once, and the secured barrette did not stir in the evening breeze.",
}


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elderwoman", "aunt"}
        male = {"boy", "father", "man", "elderman", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the village dam"
    inside: bool = False
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}
        self.flashback_used = False

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
        return any(region in g.meters.get("covers", []) for g in self.worn_items(actor))

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
        clone.facts = copy.deepcopy(self.facts)
        clone.flashback_used = self.flashback_used
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"wet", "muddy", "windblown"}


@dataclass
class Rule:
    name: str
    apply: callable


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"The wind and spray worried {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) >= THRESHOLD and actor.memes.get("memory", 0.0) >= THRESHOLD:
            sig = ("worry", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
            out.append(f"{actor.id} worried because an old lesson had returned to mind.")
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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0.0) for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell_flashback(world: World, elder: Entity, lesson: dict[str, str]) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    world.say(
        f"Years before, {elder.id} had visited the village eye doctor. The doctor had lowered a bright chart and said, "
        f"\"{lesson['memory']}\""
    )
    world.say(
        f"Now that old visit returned to {elder.id}'s mind as clearly as a candle in a dark room."
    )
    world.say(f'"That is what the eye doctor taught me," {elder.id} told the child.')


def introduce(world: World, hero: Entity, elder: Entity, prize: Entity, opener: str) -> None:
    world.say(
        f"{opener} there lived a little {hero.type} named {hero.id}. For the village's river-light festival, "
        f"{hero.pronoun('subject')} wore {prize.phrase} above one ear."
    )
    world.say(
        f"{elder.id}, {elder.phrase}, had promised to show the child the dam before the lanterns were lit."
    )


def setting_scene(world: World, activity: Activity, scene: str) -> None:
    world.say(
        f"The dam stood broad and strong above the river, holding the deep reservoir on one side and guiding water through the spillway on the other."
    )
    world.say(scene)


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, because the day felt as lively as a market song."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity,
         event: dict[str, str]) -> bool:
    elder.memes["fear"] = elder.memes.get("fear", 0.0) + 1
    elder.memes["memory"] = elder.memes.get("memory", 0.0) + 1
    world.say(
        f'"Wait by me," {elder.id} said. "{event["warning"].capitalize()}, and your {prize.label} could slip away."'
    )
    return True


def flashback_memory(world: World, elder: Entity, lesson: dict[str, str]) -> None:
    tell_flashback(world, elder, lesson)


def meet_turn(world: World, hero: Entity, activity: Activity, event: dict[str, str],
              lesson: dict[str, str], prize: Entity) -> None:
    world.say(event["event"])
    world.zone = {"head"}
    hero.meters[event["effect"]] = hero.meters.get(event["effect"], 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    propagate(world, narrate=False)
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(
        f"Instead of hurrying forward, {hero.id} remembered the doctor's words and {lesson['action']}. "
        f"That was how {hero.pronoun('subject')} noticed {event['clue']} before reaching {event['danger']}."
    )
    if prize.meters.get("dirty", 0.0):
        if event["effect"] == "windblown":
            world.say(f"The clip had shifted a little, but the {prize.label} was still safely in {hero.id}'s hair.")
        else:
            world.say(f"A few drops had touched the {prize.label}, but it was still safely in {hero.id}'s hair.")


def compromise(world: World, elder: Entity, hero: Entity, prize: Entity, solution_id: str) -> Gear:
    gear = GEAR[solution_id]
    if solution_id == "ribbon":
        world.say(f"{elder.id} tied a soft ribbon through the clip so the barrette could not shake loose.")
        prize.worn_by = hero.id
    elif solution_id == "pouch":
        world.say(
            f"{hero.id} chose to tuck the barrette into {elder.id}'s buttoned cloth pouch until they left the water."
        )
        prize.worn_by = None
        prize.caretaker = elder.id
    else:
        if prize.meters.get("wet", 0.0):
            care = "dried the barrette and fastened it"
        elif prize.meters.get("windblown", 0.0):
            care = "smoothed the child's hair and secured the barrette"
        else:
            care = "checked the clasp and secured the barrette"
        world.say(f"Together they moved to the railed lookout, where {elder.id} {care} with a second clip.")
        prize.worn_by = hero.id
    prize.meters["dirty"] = 0.0
    prize.meters["wet"] = 0.0
    prize.meters["windblown"] = 0.0
    return gear


def accept(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear: Gear, ending: str) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    if gear.id == "pouch":
        world.say(
            f"From behind the rail, {hero.id} could {activity.verb} with both hands free. When it was time to go, "
            f"{elder.id} returned the clean barrette and fastened it snugly."
        )
    else:
        world.say(
            f"From behind the rail, {hero.id} could {activity.verb} while the clean barrette stayed snug and safe."
        )
    world.say(
        f'"Seeing clearly also means choosing carefully," {hero.id} said. {elder.id} squeezed {hero.pronoun("possessive")} hand.'
    )
    world.para()
    world.say(ending)


def build_story(setting: Setting, activity: Activity, prize_cfg: Prize,
                hero_name: str = "Mina", hero_type: str = "girl",
                elder_name: str = "Grandmother", elder_type: str = "elderwoman",
                event_id: str = "spray", lesson_id: str = "steady",
                solution_id: str = "ribbon", opener: str = FOLK_OPENERS[0],
                scene: str = SCENES[0], ending_id: str = "lanterns") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, phrase=f"a curious young {hero_type}"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, phrase="the child's careful elder"))
    prize = world.add(Entity(id="barrette", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=elder.id, worn_by=hero.id, region=prize_cfg.region))
    event = EVENTS[event_id]
    lesson = LESSONS[lesson_id]
    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, setting=setting,
                       event_id=event_id, event=event, lesson_id=lesson_id, lesson=lesson,
                       solution_id=solution_id, ending_id=ending_id, opener=opener,
                       scene=scene, ending=ENDING_IMAGES[ending_id])

    introduce(world, hero, elder, prize, opener)
    world.para()
    setting_scene(world, activity, scene)
    wants(world, hero, activity)
    warn(world, elder, hero, activity, prize, event)
    flashback_memory(world, elder, lesson)
    world.para()
    meet_turn(world, hero, activity, event, lesson, prize)
    gear = compromise(world, elder, hero, prize, solution_id)
    accept(world, elder, hero, activity, prize, gear, ENDING_IMAGES[ending_id])

    world.facts["gear"] = gear
    return world


SETTINGS = {
    "dam": Setting(place="the village dam", affords={"waterwatch", "breeze"}),
}

ACTIVITIES = {
    "waterwatch": Activity(
        id="waterwatch",
        verb="watch the water rush over the spillway",
        gerund="watching the water shimmer at the dam",
        rush="run along the wet stones",
        mess="wet",
        soil="wet and tangled",
        zone={"torso", "head"},
        keyword="dam",
        tags={"dam", "water"},
    ),
    "breeze": Activity(
        id="breeze",
        verb="spin in the breeze by the dam",
        gerund="spinning in the evening breeze",
        rush="dash onto the windy path",
        mess="windblown",
        soil="wind-tossed and messy",
        zone={"head"},
        keyword="breeze",
        tags={"dam", "wind"},
    ),
}

PRIZES = {
    "barrette": Prize(
        label="barrette",
        phrase="a pearl barrette with a blue shell",
        type="barrette",
        region="head",
    )
}

GEAR = {
    "ribbon": Gear(
        id="ribbon",
        label="ribbon",
        covers={"head"},
        guards={"wet", "windblown"},
        prep="pin the barrette with a ribbon",
        tail="pinned the barrette with a ribbon and stood on the safe stones",
    ),
    "pouch": Gear(
        id="pouch",
        label="buttoned cloth pouch",
        covers={"head"},
        guards={"wet", "windblown"},
        prep="store the barrette in a buttoned cloth pouch",
        tail="kept the barrette dry until it was safe to wear again",
    ),
    "lookout": Gear(
        id="lookout",
        label="second clip",
        covers={"head"},
        guards={"wet", "windblown"},
        prep="move behind the lookout rail and add a second clip",
        tail="secured the barrette from behind the lookout rail",
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy"]
ELDER_NAMES = ["Grandmother", "Auntie", "Old Mara"]


@dataclass
class StoryParams:
    place: str = "dam"
    activity: str = "waterwatch"
    prize: str = "barrette"
    name: str = "Mina"
    elder: str = "Grandmother"
    event: str = "spray"
    lesson: str = "steady"
    solution: str = "ribbon"
    ending: str = "lanterns"
    seed: Optional[int] = None


KNOWLEDGE = {
    "dam": [("What is a dam?",
             "A dam is a strong wall built across water to help hold it back or guide it safely.")],
    "ophthalmology": [("What does an eye doctor do?",
                       "An eye doctor checks how eyes see and helps people keep their vision healthy.")],
    "barrette": [("What is a barrette?",
                  "A barrette is a little hair clip that helps hold hair in place.")],
    "flashback": [("What is a flashback in a story?",
                    "A flashback is when the story briefly remembers something that happened earlier.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale for a young child about {f['hero'].id} and {f['elder'].id} at {f['setting'].place}. "
        f"The child wants to {f['activity'].verb}, and the trouble begins when {f['event']['warning']}.",
        f"Tell a gentle dam story with a flashback to an eye doctor who taught this lesson: {f['lesson']['memory']} "
        f"Use a {f['gear'].label} to help keep a blue-shell barrette safe.",
        f"Write a complete folk tale about a barrette, a village dam, and careful seeing. End with this image: {f['ending']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, activity = f["hero"], f["elder"], f["prize"], f["activity"]
    event, lesson, gear = f["event"], f["lesson"], f["gear"]
    event_text = event["event"].removeprefix("Just then, ").rstrip(".")
    return [
        QAItem(
            question="Who visited the dam, and what was happening around them?",
            answer=(
                f"{hero.id}, a little {hero.type}, visited with {elder.id}, the child's careful elder. "
                f"{f['scene']} {hero.id} hoped to {activity.verb}. The tale ends this way: {f['ending']}"
            ),
        ),
        QAItem(
            question=f"Which eye-doctor lesson helped {hero.id} when {event_text}?",
            answer=(
                f"{elder.id} remembered the eye doctor's advice: \"{lesson['memory']}\" "
                f"That advice helped {hero.id} notice {event['clue']} before reaching {event['danger']}, "
                f"and afterward they used the {gear.label}."
            ),
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.id} protect the {prize.label} after noticing {event['clue']}?",
            answer=(
                f"They used the {gear.label} before {hero.id} stayed behind the rail to {activity.verb}. "
                f"At the close, the barrette was clean and snug in {hero.id}'s hair. {f['ending']}"
            ),
        ),
        QAItem(
            question=f"What did {hero.id} do instead of hurrying toward {event['danger']}?",
            answer=(
                f"{hero.id} {lesson['action']}, so she noticed {event['clue']}. The child then used the {gear.label} "
                f"and stayed behind the rail to {activity.verb}. Around them, {f['scene'][0].lower() + f['scene'][1:]}"
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for topic in ["dam", "ophthalmology", "barrette", "flashback"] for q, a in KNOWLEDGE[topic]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    activity = args.activity or rng.choice(list(ACTIVITIES))
    compatible_events = ["spray", "glare"] if activity == "waterwatch" else ["gust", "glare"]
    return StoryParams(
        place="dam",
        activity=activity,
        prize="barrette",
        name=args.name or rng.choice(GIRL_NAMES),
        elder=args.elder or rng.choice(ELDER_NAMES),
        event=args.event or rng.choice(compatible_events),
        lesson=args.lesson or rng.choice(list(LESSONS)),
        solution=args.solution or rng.choice(list(GEAR)),
        ending=args.ending or rng.choice(list(ENDING_IMAGES)),
    )


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    world = build_story(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                        hero_name=params.name, elder_name=params.elder,
                        event_id=params.event, lesson_id=params.lesson,
                        solution_id=params.solution, opener=rng.choice(FOLK_OPENERS),
                        scene=rng.choice(SCENES), ending_id=params.ending)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small folk-tale storyworld with a dam, ophthalmology memory, and a barrette.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES, default="barrette")
    ap.add_argument("--name")
    ap.add_argument("--elder")
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--solution", choices=GEAR)
    ap.add_argument("--ending", choices=ENDING_IMAGES)
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


ASP_RULES = r"""
setting(dam).
activity(waterwatch).
activity(breeze).
prize(barrette).
worn_on(barrette, head).

splashes(waterwatch, head).
splashes(waterwatch, torso).
splashes(breeze, head).

guards(ribbon, wet).
guards(ribbon, windblown).
covers(ribbon, head).

prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), guards(G, M), activity_mess(A, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid_story(Place, A, P) :- setting(Place), activity(A), prize(P), prize_at_risk(A, P), has_fix(A, P).

activity_mess(waterwatch, wet).
activity_mess(breeze, windblown).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "dam"),
        asp.fact("activity", "waterwatch"),
        asp.fact("activity", "breeze"),
        asp.fact("prize", "barrette"),
        asp.fact("worn_on", "barrette", "head"),
        asp.fact("splashes", "waterwatch", "head"),
        asp.fact("splashes", "waterwatch", "torso"),
        asp.fact("splashes", "breeze", "head"),
        asp.fact("guards", "ribbon", "wet"),
        asp.fact("guards", "ribbon", "windblown"),
        asp.fact("covers", "ribbon", "head"),
        asp.fact("activity_mess", "waterwatch", "wet"),
        asp.fact("activity_mess", "breeze", "windblown"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("dam", "waterwatch", "barrette"), ("dam", "breeze", "barrette")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(StoryParams(name="Mina", elder="Grandmother"))]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
