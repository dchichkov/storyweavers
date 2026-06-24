#!/usr/bin/env python3
"""
storyworlds/worlds/reindeer_boon_lesson_learned_dialogue_superhero_story.py
===========================================================================

A small superhero-story world about a helpful hero, a reindeer, and a boon
that needs to be used wisely.

Seed tale concept:
- A young superhero wants to help a reindeer make a snowy delivery.
- The reindeer receives a boon: a bright helper-gift that makes the job easier.
- A mistake creates a little danger and a little worry.
- A calm dialogue leads to a lesson learned and a safer ending.

This file is self-contained and follows the Storyworld contract.
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

THRESHOLD = 1.0
MESS_KINDS = {"scuffed", "stained", "tangled"}

REGIONS = {"head", "body", "legs", "antlers"}


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
        for k in ["scuffed", "stained", "tangled", "damage", "spark", "help", "care", "joy", "worry", "pride", "lesson"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the snowy plaza"
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Boon:
    id: str
    label: str
    phrase: str
    region: str
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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["damage"] += 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damage"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That gave {carer.label} a worried look.")
    return out


def _r_lesson(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD or actor.memes["care"] < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["lesson"] += 1
        actor.memes["joy"] += 1
        return ["__lesson__"]
    return []


CAUSAL_RULES = [
    _r_soil,
    _r_worry,
    _r_lesson,
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
                produced.extend(s for s in sents if s != "__lesson__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    activity: str
    boon: str
    hero_name: str
    hero_type: str
    reindeer_name: str
    seed: Optional[int] = None


SETTINGS = {
    "plaza": Setting(place="the snowy plaza", affords={"rescue", "glide"}),
    "roof": Setting(place="the moonlit roof", affords={"rescue", "glide"}),
    "park": Setting(place="the winter park", affords={"rescue", "glide"}),
}

ACTIVITIES = {
    "rescue": Activity(
        id="rescue",
        verb="help the reindeer rescue the lost lantern",
        gerund="helping with the rescue",
        rush="dash toward the lantern",
        mess="scuffed",
        soil="scuffed up",
        zone={"legs", "body"},
        keyword="rescue",
        tags={"hero", "help", "snow"},
    ),
    "glide": Activity(
        id="glide",
        verb="glide across the snow",
        gerund="gliding across the snow",
        rush="race down the hill",
        mess="tangled",
        soil="tangled up",
        zone={"antlers", "legs"},
        keyword="glide",
        tags={"snow", "reindeer"},
    ),
}

BOONS = {
    "cape": Boon(
        id="cape",
        label="a bright cape",
        phrase="a bright cape with a silver star",
        region="body",
        covers={"body"},
        guards={"scuffed"},
        prep="put on the bright cape first",
        tail="tied on the bright cape",
    ),
    "harness": Boon(
        id="harness",
        label="a snug harness",
        phrase="a snug harness with a bell",
        region="body",
        covers={"body", "legs"},
        guards={"tangled"},
        prep="buckle on the snug harness first",
        tail="buckled on the snug harness",
    ),
    "antlerband": Boon(
        id="antlerband",
        label="an antler band",
        phrase="an antler band that shone like ice",
        region="antlers",
        covers={"antlers"},
        guards={"tangled"},
        prep="slip on the antler band first",
        tail="slipped on the antler band",
    ),
}

HERO_NAMES = ["Nova", "Spark", "Ruby", "Milo", "Ivy", "Jett"]
REINDEER_NAMES = ["Comet", "Blaze", "Tinsel", "Pip", "Star"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for boon_id, boon in BOONS.items():
                if act.zone & boon.covers:
                    combos.append((place, act_id, boon_id))
    return combos


def prize_at_risk(activity: Activity, boon: Boon) -> bool:
    return bool(activity.zone & boon.covers)


def select_boon(activity: Activity, boon: Boon) -> bool:
    return activity.mess in boon.guards and prize_at_risk(activity, boon)


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} glittered under the snow."


def predict(world: World, actor: Entity, activity: Activity, boon_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    boon = sim.entities.get(boon_id)
    return {"damaged": bool(boon and boon.meters["damage"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, reindeer: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} hero who loved snowy missions.")
    world.say(f"{reindeer.id} was a brave reindeer with fast hooves and a kind nose.")


def gift_boon(world: World, hero: Entity, reindeer: Entity, boon: Entity) -> None:
    reindeer.memes["care"] += 1
    boon.worn_by = reindeer.id
    world.say(f"One day, {hero.id} gave {reindeer.id} {boon.phrase}.")
    world.say(f'"This is a boon for your work," {hero.id} said. "{reindeer.id}, use it well."')


def arrive(world: World, hero: Entity, reindeer: Entity) -> None:
    world.say(f"Then {hero.id} and {reindeer.id} hurried to {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, hero: Entity, reindeer: Entity, activity: Activity) -> None:
    world.say(f'{reindeer.id} said, "I want to {activity.verb} right now!"')
    world.say(f'{hero.id} smiled and answered, "We can, but we should be careful."')


def warn_and_mistake(world: World, hero: Entity, reindeer: Entity, activity: Activity, boon: Entity) -> None:
    if predict(world, reindeer, activity, boon.id)["damaged"]:
        world.say(f'"If you rush, {boon.label} could get {activity.soil}," {hero.id} warned.')
    reindeer.meters[activity.mess] += 1
    reindeer.memes["stubborn"] = reindeer.memes.get("stubborn", 0.0) + 1
    world.say(f'But {reindeer.id} still tried to {activity.rush}.')
    propagate(world, narrate=True)


def dialogue_turn(world: World, hero: Entity, reindeer: Entity, boon: Entity, activity: Activity) -> None:
    world.para()
    world.say(f'"I was excited," {reindeer.id} said. "I forgot to listen."')
    world.say(f'"That happens," {hero.id} said. "A true hero learns and tries again."')
    world.say(f'"Then I will slow down," {reindeer.id} said. "Can the boon still help?"')
    world.say(f'"Yes," {hero.id} said. "We will use {boon.label} the safe way."')
    hero.memes["pride"] += 1
    reindeer.memes["lesson"] += 1
    reindeer.memes["care"] += 1


def resolve(world: World, hero: Entity, reindeer: Entity, boon: Entity, activity: Activity) -> None:
    boon.protective = True
    reindeer.memes["joy"] += 1
    world.say(f"Together, they fixed the problem and kept going.")
    world.say(f"They {boon.label if boon.label.startswith('an ') else boon.id} and finished {activity.gerund}.")
    world.say(f"At the end, {reindeer.id} felt proud because {reindeer.pronoun()} had learned to listen.")


def tell(setting: Setting, activity: Activity, boon_cfg: Boon, hero_name: str, hero_type: str, reindeer_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    reindeer = world.add(Entity(id=reindeer_name, kind="character", type="reindeer", label=reindeer_name))
    boon = world.add(Entity(
        id=boon_cfg.id,
        type="boon",
        label=boon_cfg.label,
        phrase=boon_cfg.phrase,
        owner=reindeer.id,
        caretaker=hero.id,
        region=boon_cfg.region,
        covers=set(boon_cfg.covers),
        plural=boon_cfg.plural,
    ))

    introduce(world, hero, reindeer)
    world.para()
    gift_boon(world, hero, reindeer, boon)
    arrive(world, hero, reindeer)
    wants(world, hero, reindeer, activity)
    warn_and_mistake(world, hero, reindeer, activity, boon)
    dialogue_turn(world, hero, reindeer, boon, activity)
    resolve(world, hero, reindeer, boon, activity)

    world.facts.update(
        hero=hero,
        reindeer=reindeer,
        boon=boon,
        activity=activity,
        setting=setting,
        boon_cfg=boon_cfg,
    )
    return world


KNOWLEDGE = {
    "reindeer": [
        ("What is a reindeer?", "A reindeer is a deer that lives in cold places and often has antlers."),
    ],
    "boon": [
        ("What is a boon?", "A boon is a helpful gift or advantage that makes a hard job easier."),
    ],
    "hero": [
        ("What does a superhero do?", "A superhero helps others, solves problems, and tries to keep people safe."),
    ],
    "snow": [
        ("What is snow?", "Snow is frozen water that falls from the sky in soft white flakes."),
    ],
    "lesson": [
        ("What does it mean to learn a lesson?", "It means you understand what went wrong and do better next time."),
    ],
}

KNOWLEDGE_ORDER = ["reindeer", "boon", "hero", "snow", "lesson"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the words "reindeer" and "boon".',
        f"Tell a gentle story where {f['hero'].id} gives {f['reindeer'].id} a boon and they have a dialogue about using it safely.",
        f"Write a snowy superhero story with a mistake, a calm conversation, and a lesson learned at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, reindeer, boon, activity = f["hero"], f["reindeer"], f["boon"], f["activity"]
    qa = [
        QAItem(
            question=f"Who gave {reindeer.id} the boon?",
            answer=f"{hero.id} gave {reindeer.id} the boon as a helpful gift for the snowy job.",
        ),
        QAItem(
            question=f"What did {reindeer.id} want to do after getting the boon?",
            answer=f"{reindeer.id} wanted to {activity.verb}, but needed to be careful so the boon would stay useful.",
        ),
        QAItem(
            question=f"What did the hero and the reindeer do when the mistake happened?",
            answer=f"They talked it through with dialogue, slowed down, and chose a safer way to finish the mission.",
        ),
        QAItem(
            question=f"What lesson did {reindeer.id} learn?",
            answer=f"{reindeer.id} learned to listen first, slow down, and use the boon the safe way.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("reindeer")
    tags.add("boon")
    tags.add("hero")
    tags.add("lesson")
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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


ASP_RULES = r"""
prize_at_risk(A, B) :- splashes(A, R), covers(B, R).
has_fix(A, B) :- prize_at_risk(A, B), guards(B, M), mess_of(A, M).
valid(Place, A, B) :- affords(Place, A), has_fix(A, B).
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
    for bid, b in BOONS.items():
        lines.append(asp.fact("boon", bid))
        for r in sorted(b.covers):
            lines.append(asp.fact("covers", bid, r))
        for m in sorted(b.guards):
            lines.append(asp.fact("guards", bid, m))
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


def explain_rejection(activity: Activity, boon: Boon) -> str:
    return (
        f"(No story: {activity.gerund} does not match the boon '{boon.label}' in a way "
        f"that makes a real mistake-and-fix story. Pick a pairing where the boon can "
        f"actually help after the warning.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with a reindeer, a boon, dialogue, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--boon", choices=BOONS)
    ap.add_argument("--name")
    ap.add_argument("--reindeer")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.activity and args.boon:
        if not select_boon(ACTIVITIES[args.activity], BOONS[args.boon]):
            raise StoryError(explain_rejection(ACTIVITIES[args.activity], BOONS[args.boon]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.boon is None or c[2] == args.boon)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, boon_id = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    reindeer_name = args.reindeer or rng.choice(REINDEER_NAMES)
    hero_type = args.gender or rng.choice(["girl", "boy"])
    return StoryParams(place=place, activity=activity, boon=boon_id, hero_name=hero_name, hero_type=hero_type, reindeer_name=reindeer_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], BOONS[params.boon], params.hero_name, params.hero_type, params.reindeer_name)
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


CURATED = [
    StoryParams(place="plaza", activity="rescue", boon="cape", hero_name="Nova", hero_type="girl", reindeer_name="Comet"),
    StoryParams(place="roof", activity="glide", boon="antlerband", hero_name="Spark", hero_type="boy", reindeer_name="Tinsel"),
    StoryParams(place="park", activity="rescue", boon="harness", hero_name="Ivy", hero_type="girl", reindeer_name="Star"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for place, act, boon in triples:
            print(f"  {place:6} {act:7} {boon}")
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
            header = f"### {p.hero_name}: {p.activity} at {p.place} (boon: {p.boon})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
