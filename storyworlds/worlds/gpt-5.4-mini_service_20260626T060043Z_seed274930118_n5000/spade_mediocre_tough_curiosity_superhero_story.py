#!/usr/bin/env python3
"""
storyworlds/worlds/spade_mediocre_tough_curiosity_superhero_story.py
====================================================================

A small superhero-style storyworld about Curiosity, a sturdy tool, and the
good kind of clever problem-solving.

Premise:
- A young hero named Curiosity wants to use a spade for a helpful mission.
- The mission is a little rough and messy, so a prized outfit/item is at risk.
- A tougher piece of gear can solve the problem without stopping the hero.

The story is intentionally compact and classical:
setup -> warning -> stubborn try -> safer compromise -> happy ending.
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

    def __post_init__(self):
        if not self.meters:
            self.meters = {"muddy": 0.0, "dusty": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "worry": 0.0, "defiance": 0.0, "pride": 0.0, "conflict": 0.0}

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


@dataclass
class Setting:
    place: str
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
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["muddy"] < THRESHOLD and actor.meters["dusty"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["muddy"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got muddy.")
    return out


def _r_tired(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["muddy"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("tired", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get(item.caretaker).meters["tired"] += 1
        out.append("That would mean extra cleanup afterward.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_soil,
    _r_tired,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    pending: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                pending.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in pending:
            world.say(s)


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
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters["muddy"] >= THRESHOLD, "tired": sum(e.meters["tired"] for e in sim.characters())}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"This setting cannot host {activity.id}.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
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

    hero.memes["pride"] += 1
    world.say(f"{hero.id} was a little {trait} superhero who noticed tiny problems before they grew big.")
    world.say(f"{hero.id} loved the {activity.keyword} mission and carried a spade that looked sturdy and tough.")
    world.say(f"One day {hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} on every outing.")

    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {activity.verb}.")
    if hero_name.lower() == "curiosity":
        world.say("Curiosity made the plan feel exciting, even a little reckless.")
    world.say(f"{hero.id} said, \"This will be a mighty little rescue!\"")

    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f"\"You'll get your {prize.label} {activity.soil},\" {parent.label} warned.")
        world.say(f"{hero.id} still tried to {activity.rush}.")
        hero.memes["defiance"] += 1
        propagate(world, narrate=True)
        world.say(f"{hero.id} paused when {hero.pronoun('possessive')} {parent.label} gently blocked the way.")
        gear_def = select_gear(activity, prize)
        if gear_def is None:
            raise StoryError("No reasonable gear can protect the prize in this story.")
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
            raise StoryError("The gear did not solve the problem.")
        world.para()
        world.say(f"{parent.label.capitalize()} smiled and said, \"How about we {gear_def.prep} and then try again?\"")
        hero.memes["joy"] += 1
        hero.memes["defiance"] = 0.0
        world.say(f"{hero.id}'s face lit up. \"Yes!\" {hero.pronoun()} said, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label}.")
        world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the little rescue ended in a proud grin.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, resolved=True, conflict=True)
    else:
        world.say(f"{hero.id} could go ahead safely, and the day stayed bright.")
        world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=None, resolved=True, conflict=False)
    return world


SETTINGS = {
    "community_garden": Setting("the community garden", {"dig"}),
    "moonyard": Setting("the moonyard beside the museum", {"dig"}),
    "rooftop_plot": Setting("the rooftop plot", {"dig", "rescue"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig",
        verb="dig under the broken stones",
        gerund="digging under the broken stones",
        rush="rush to the stones",
        mess="muddy",
        soil="muddy",
        zone={"feet", "legs", "torso"},
        keyword="spade",
        tags={"spade", "tough", "curiosity"},
    ),
    "rescue": Activity(
        id="rescue",
        verb="lift the fallen box from the dirt",
        gerund="lifting fallen boxes",
        rush="dash to the box",
        mess="dusty",
        soil="dusty",
        zone={"torso"},
        keyword="spade",
        tags={"spade", "curiosity"},
    ),
}

PRIZES = {
    "cape": Prize("cape", "a bright hero cape", "cape", "torso"),
    "boots": Prize("boots", "tough little boots", "boots", "feet", plural=True),
    "shirt": Prize("shirt", "a clean blue shirt", "shirt", "torso"),
}

GEAR = [
    Gear("tough_apron", "a tough apron", {"torso"}, {"muddy", "dusty"}, "put on a tough apron first", "went back for the tough apron"),
    Gear("tough_boots", "tough boots", {"feet"}, {"muddy", "dusty"}, "put on tough boots first", "went back for the tough boots", plural=True),
    Gear("shield_cloak", "a shield cloak", {"torso"}, {"dusty"}, "wear a shield cloak first", "went back for the shield cloak"),
]

CURATED = [
    ("community_garden", "dig", "cape", "Curiosity", "girl", "mother", "curious"),
    ("moonyard", "dig", "shirt", "Nova", "girl", "father", "brave"),
    ("rooftop_plot", "rescue", "cape", "Bolt", "boy", "mother", "tough"),
]


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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


KNOWLEDGE = {
    "spade": [("What is a spade?", "A spade is a tool with a flat blade for digging into dirt and soil.")],
    "tough": [("What does tough mean?", "Tough means strong and not easy to damage or break.")],
    "curiosity": [("What is curiosity?", "Curiosity is the wish to learn, notice, and ask about new things.")],
    "muddy": [("What makes mud muddy?", "Mud is muddy because it mixes dirt with water and turns soft and sticky.")],
}
KNOWLEDGE_ORDER = ["spade", "tough", "curiosity", "muddy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short superhero story for a child named {hero.id} who carries a spade and loves curiosity.',
        f"Tell a story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a brave little story that includes the words spade, mediocre, and tough, and ends with a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {hero.id}, a little superhero who leads with curiosity.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id}?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because {hero.pronoun('possessive')} {prize.label} would get {act.soil} if the mission went ahead without protection.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} at {world.setting.place}.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"What problem made the story tense?",
            answer=f"The tense part was that {hero.id} still wanted to {act.verb} even after the warning, so the {prize.label} was in danger.",
        ))
    if gear:
        qa.append(QAItem(
            question=f"How was the problem fixed?",
            answer=f"They used {gear.label} so {hero.id} could keep going without ruining {hero.pronoun('possessive')} {prize.label}.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} feeling proud, {prize.label} staying clean, and the family smiling after the safer plan worked.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("tough")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
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
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero storyworld about Curiosity, a spade, and a tough compromise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or ("Curiosity" if rng.random() < 0.6 else rng.choice(["Nova", "Mira", "Bolt", "Spark"]))
    parent = args.parent or rng.choice(["mother", "father"])
    trait = "curious"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=z, name="Curiosity", gender="girl", parent="mother", trait="curious")) for p, a, z in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
