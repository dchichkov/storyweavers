#!/usr/bin/env python3
"""
A small storyworld about a comic mishap in a cathedral, a surfboard, and an
auburn lesson learned. The story uses foreshadowing and reconciliation in a
light, child-facing style.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("splash", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters.get("shielded", 0.0) >= THRESHOLD:
                continue
            if item.id.startswith("cape"):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["messy"] = item.meters.get("messy", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{item.label.capitalize()} got messy from the splash.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("awkward", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("laughing", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["awkward"] = 0.0
        actor.memes["peace"] = actor.memes.get("peace", 0.0) + 1
        out.append(f"The awkward feeling faded.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soil, _r_reconcile):
            sents = rule(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_fix(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.zone = set(activity.zone)
    actor2 = sim.get(actor.id)
    actor2.meters["splash"] = actor2.meters.get("splash", 0.0) + 1
    propagate(sim, narrate=False)
    return any(e.meters.get("dirty", 0.0) >= THRESHOLD for e in sim.entities.values())


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: cathedral, surf, auburn.")
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


SETTINGS = {
    "cathedral": Setting(place="the cathedral", indoors=True, affords={"surf", "lesson"}),
}

ACTIVITIES = {
    "surf": Activity(
        id="surf",
        verb="surf in the hall",
        gerund="surfing through the hall",
        rush="rush down the aisle on the board",
        mess="spray",
        soil="all damp and silly",
        zone={"floor", "torso"},
        keyword="surf",
        tags={"surf", "water", "comedy"},
    ),
    "lesson": Activity(
        id="lesson",
        verb="take a lesson",
        gerund="learning the lesson",
        rush="dash off without listening",
        mess="chalk",
        soil="smudged with chalk",
        zone={"hands", "torso"},
        keyword="lesson",
        tags={"lesson", "learning", "comedy"},
    ),
}

PRIZES = {
    "robe": Prize(label="robe", phrase="a shiny auburn robe", type="robe", region="torso"),
    "shoes": Prize(label="shoes", phrase="auburn shoes", type="shoes", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="towel",
        label="a big towel",
        covers={"torso"},
        guards={"spray"},
        prep="wrap up in a big towel",
        tail="walked back to the side aisle with the towel",
    ),
    Gear(
        id="slippers",
        label="soft slippers",
        covers={"feet"},
        guards={"spray", "chalk"},
        prep="put on soft slippers",
        tail="returned with soft slippers",
        plural=True,
    ),
]

GIRL_NAMES = ["Aubrey", "Mina", "Lila", "Zara", "Nina"]
BOY_NAMES = ["Milo", "Ezra", "Theo", "Owen", "Arlo"]
TRAITS = ["funny", "curious", "bouncy", "brave", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            activity = ACTIVITIES[act]
            for prize_id, prize in PRIZES.items():
                if can_fix(activity, prize) and select_gear(activity, prize):
                    combos.append((place, act, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (can_fix(act, prize) and select_gear(act, prize)):
            raise StoryError("No honest story: that activity does not endanger that prize in a fixable way.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("No honest story: that prize doesn't fit that gender choice here.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"joy": 0.0, "awkward": 0.0, "laughing": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    prize.worn_by = hero.id
    gear_def = select_gear(activity, prize_cfg)
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, plural=gear_def.plural, owner=hero.id)) if gear_def else None
    if gear:
        gear.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} little {gender} who loved the cathedral because it was so big it almost felt like a joke.")
    world.say(f"{hero.pronoun().capitalize()} admired {hero.pronoun('possessive')} {prize.label}, which was especially auburn in the bright light.")
    world.para()
    world.say(f"One day at {setting.place}, {hero.id} wanted to {activity.verb}.")
    world.say(f"That was funny enough to make the pigeons look interested.")
    if activity.id == "surf":
        world.say("A tiny plank had been wheeled in for a lesson, and it made a very suspicious squeak.")
    else:
        world.say("A little sign about the lesson leaned nearby, as if it knew trouble was coming.")
    world.say(f"{parent.label} raised a hand and warned, 'If you do that, the {prize.label} may end up {activity.soil}.'")
    hero.memes["awkward"] += 1
    world.say(f"{hero.id} giggled, because the warning sounded too much like a fish trying to be a choir singer.")
    world.say(f"{hero.id} tried to {activity.rush}.")
    hero.meters["splash"] = hero.meters.get("splash", 0.0) + 1
    propagate(world, narrate=True)
    world.para()
    if gear and predict(world, hero, activity):
        world.say(f"{parent.label} frowned, then smiled, and said, 'Let's use {gear.label} first.'")
        world.say(f"They chose to {gear_def.prep} and try again more carefully.")
        hero.memes["laughing"] += 1
        hero.memes["awkward"] += 1
        world.zone = set(activity.zone)
        hero.meters["splash"] += 1
        gear.meters["shielded"] = 1.0
        propagate(world, narrate=True)
        world.say(f"{hero.id} learned that a good joke is funnier when nobody has to mop it up.")
        world.say(f"At the end, {hero.id} was {activity.gerund}, {prize.label} safe, and everyone was laughing in the cathedral's echo.")
        hero.memes["laughing"] += 1
    else:
        world.say(f"{hero.id} stopped, looked at the mess, and learned the lesson before anyone could slip.")
        world.say(f"{parent.label} and {hero.id} reconciled with a grin and a promise to try the safer way.")
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg, activity=activity, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short funny story for a child about a cathedral, {act.keyword}, and an auburn {prize.label}.',
        f"Tell a light comedy where {hero.id} wants to {act.verb} but {parent.label} worries about the {prize.label}.",
        f"Write a story with foreshadowing and reconciliation in a cathedral, ending with a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the cathedral?",
            answer=f"{hero.id} wanted to {activity.verb}, which was the silliest idea in the tall, echoing cathedral.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {prize.label}?",
            answer=f"{parent.label} warned {hero.id} because the {prize.label} could get {activity.soil} if the splashy plan went ahead.",
        ),
        QAItem(
            question=f"What did {hero.id} learn by the end?",
            answer=f"{hero.id} learned that it is better to choose a safer way before a funny idea turns into a slippery mess.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cathedral?",
            answer="A cathedral is a very large church with tall walls, big windows, and lots of echoing space.",
        ),
        QAItem(
            question="What does surf mean?",
            answer="Surfing means riding on a board over moving water, usually with balance and a lot of wobble.",
        ),
        QAItem(
            question="What is auburn?",
            answer="Auburn is a reddish-brown color, like some leaves, wood, or shiny hair.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
fixable(A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R), splashes(A,R).
valid(Place,A,P) :- affords(Place,A), fixable(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
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


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    left, right = set(valid_combos()), set(valid_asp())
    if left == right:
        print(f"OK: ASP matches Python gate ({len(left)} combos).")
        return 0
    print("MISMATCH:")
    print("python only:", sorted(left - right))
    print("asp only:", sorted(right - left))
    return 1


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


CURATED = [
    StoryParams(place="cathedral", activity="surf", prize="robe", name="Aubrey", gender="girl", parent="mother", trait="funny"),
    StoryParams(place="cathedral", activity="lesson", prize="shoes", name="Milo", gender="boy", parent="father", trait="curious"),
]


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
        print(f"{len(asp.atoms(model, 'valid'))} compatible combos")
        for t in sorted(set(asp.atoms(model, "valid"))):
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        a, p = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (can_fix(a, p) and select_gear(a, p)):
            raise StoryError("No honest story: that activity and prize do not form a fixable problem.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("No honest story: the requested gender does not fit this prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


if __name__ == "__main__":
    main()
