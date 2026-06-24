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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

FOLK_OPENERS = [
    "Once, in a small village between hills and water,",
    "Long ago, where the reeds bowed and the lanterns glowed,",
    "In a quiet valley with a stone dam and a winding path,",
]

FOLK_ENDINGS = [
    "And so the village rested, the water stayed bound, and the child went home with a steady heart.",
    "And so the evening grew soft, the dam held the river kindly, and the barrette stayed safely in place.",
    "And that is how the little lesson became a good tale for later days.",
]


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


def tell_flashback(world: World, elder: Entity) -> None:
    if world.flashback_used:
        return
    world.flashback_used = True
    world.say(
        f"Flashback: when {elder.id} once visited the eye doctor, the doctor had held up a bright chart and said, "
        f"\"Keep your eyes steady, and you will notice trouble before it slips away.\""
    )
    world.say(
        f"{elder.id} remembered that lesson now, as clearly as a candle in a dark room."
    )


def introduce(world: World, hero: Entity, elder: Entity, prize: Entity) -> None:
    opener = random.choice(FOLK_OPENERS)
    world.say(
        f"{opener} there lived a little {hero.type} named {hero.id}, who wore {hero.pronoun('possessive')} {prize.label} like a tiny bright star."
    )
    world.say(
        f"{elder.id}, {elder.phrase}, watched over the child with a patient heart."
    )


def setting_scene(world: World, activity: Activity) -> None:
    world.say(
        f"The dam stood over the river, its stones warm in the sun, while water sang softly below."
    )
    world.say(
        f"{activity.gerund.capitalize()} there looked tempting, because the breeze danced over the spillway and made the water sparkle."
    )


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb}, because the day felt as lively as a market song."
    )


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    elder.memes["fear"] = elder.memes.get("fear", 0.0) + 1
    elder.memes["memory"] = elder.memes.get("memory", 0.0) + 1
    world.say(
        f'"If you go too close," {elder.id} said, "your {prize.label} may get {activity.soil}, and the river wind may carry it off."'
    )
    return True


def flashback_memory(world: World, elder: Entity) -> None:
    tell_flashback(world, elder)


def compromise(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    if activity.id != "riverbank":
        pass
    gear = GEAR["ribbon"]
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        world.say(
            f'{elder.id} smiled and said, "Let us pin it more tightly and watch from the safe stones."'
        )
        return gear
    return None


def accept(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.say(
        f"{hero.id} let {elder.id} steady the {gear.label}, and the little {prize.label} stayed neat and snug."
    )
    world.say(
        f"Then {hero.id} watched the rushing water from the safe stones, happy and calm."
    )
    world.para()
    world.say(random.choice(FOLK_ENDINGS))


def build_story(setting: Setting, activity: Activity, prize_cfg: Prize,
                hero_name: str = "Mina", hero_type: str = "girl",
                elder_name: str = "Grandmother", elder_type: str = "elderwoman") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, phrase="a bright-eyed grandmother?"))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_type, phrase="the village grandmother"))
    prize = world.add(Entity(id="barrette", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=elder.id, region=prize_cfg.region))

    introduce(world, hero, elder, prize)
    world.para()
    setting_scene(world, activity)
    wants(world, hero, activity)
    warn(world, elder, hero, activity, prize)
    flashback_memory(world, elder)
    world.say(f"{hero.id} looked at the dam, then at {elder.id}, and listened.")
    world.para()
    gear = compromise(world, elder, hero, activity, prize)
    if gear:
        accept(world, elder, hero, activity, prize, gear)

    world.facts.update(hero=hero, elder=elder, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


SETTINGS = {
    "dam": Setting(place="the village dam", affords={"waterwatch"}),
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
    )
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
        'Write a short folk tale for a young child that includes a dam, an eye doctor memory, and a barrette.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} near {f['setting'].place}, but an elder remembers an ophthalmology visit and helps.",
        "Write a small story with a flashback, a village dam, and a barrette that stays safe by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, activity = f["hero"], f["elder"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type}, and {elder.id}, who cares for the child.",
        ),
        QAItem(
            question=f"Why did {elder.id} bring up the eye doctor?",
            answer=(
                f"{elder.id} remembered the eye doctor from earlier and used that memory to help {hero.id} notice the danger before the {prize.label} could get ruined."
            ),
        ),
        QAItem(
            question=f"What happened to the {prize.label} at the end?",
            answer=f"The {prize.label} stayed neat and snug, because {elder.id} helped pin it more tightly before they watched the water.",
        ),
        QAItem(
            question=f"What did {hero.id} do near the dam instead of running onto the wet stones?",
            answer=f"{hero.id} watched the water from the safe stones and enjoyed {activity.gerund}.",
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
    return StoryParams(
        place="dam",
        activity=args.activity or rng.choice(list(ACTIVITIES)),
        prize="barrette",
        name=args.name or rng.choice(GIRL_NAMES),
        elder=args.elder or rng.choice(ELDER_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                        hero_name=params.name, elder_name=params.elder)
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
    ap.add_argument("--activity", choices=ACTIVITIES, default="waterwatch")
    ap.add_argument("--prize", choices=PRIZES, default="barrette")
    ap.add_argument("--name")
    ap.add_argument("--elder")
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
