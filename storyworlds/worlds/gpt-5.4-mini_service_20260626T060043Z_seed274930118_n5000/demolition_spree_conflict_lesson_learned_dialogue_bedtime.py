#!/usr/bin/env python3
"""
A bedtime-story world about a small demolition spree, a warm conflict, and a
lesson learned before sleep.

The seed tale behind this world:
- A child builds a little fort of pillows and blocks.
- The child gets excited and starts a demolition spree, knocking things over.
- A parent worries about the mess and about bedtime.
- There is a conflict, then a dialogue, then a lesson learned.
- The ending proves the room is calm and ready for sleep.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"block_spree", "pillow_spree"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"block_spree", "pillow_spree"}),
}

ACTIVITIES = {
    "block_spree": Activity(
        id="block_spree",
        verb="knock down the block tower",
        gerund="knocking down block towers",
        rush="topple the blocks even faster",
        mess="scattered",
        soil="all over the floor",
        zone={"floor"},
        keyword="demolition",
        tags={"demolition", "blocks"},
    ),
    "pillow_spree": Activity(
        id="pillow_spree",
        verb="tear apart the pillow fort",
        gerund="tearing apart pillow forts",
        rush="fling the pillows everywhere",
        mess="scattered",
        soil="all over the bed",
        zone={"bed"},
        keyword="spree",
        tags={"spree", "pillow"},
    ),
}

PRIZES = {
    "fort": Prize(label="fort", phrase="a cozy pillow fort", type="fort", region="bed"),
    "tower": Prize(label="tower", phrase="a tall block tower", type="tower", region="floor"),
}

GEAR = [
    Gear(
        id="basket",
        label="a toy basket",
        covers={"floor", "bed"},
        guards={"scattered"},
        prep="put the toys back in a basket first",
        tail="put the blocks and pillows back where they belonged",
    ),
]

CHILD_NAMES = ["Milo", "Nina", "Luna", "Eli", "Ruby", "Owen", "Ivy", "Theo"]
PARENT_NAMES = ["mom", "dad"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for prize in PRIZES:
                if act == "block_spree" and prize == "tower":
                    combos.append((place, act, prize))
                if act == "pillow_spree" and prize == "fort":
                    combos.append((place, act, prize))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: demolition, spree, conflict, and lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=PARENT_NAMES)
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
            raise StoryError("That activity and prize do not make a sensible bedtime conflict.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid bedtime demolition story matches those options.")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(CHILD_NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, parent=parent)


def _demo(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    world.zone = set(activity.zone)
    for item in world.worn_items(actor):
        item.meters["messy"] = item.meters.get("messy", 0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0) + 1
    if narrate:
        world.say(f"{actor.id} made the room feel full of motion.")


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _demo(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"messy": bool(prize.meters.get("dirty", 0) >= THRESHOLD)}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", label=hero_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=parent.id, region=prize_cfg.region))
    basket = world.add(Entity(id="basket", type="basket", label="basket", phrase="a toy basket"))

    world.say(f"At bedtime, {hero.id} was in {setting.place}, where the lamp glowed softly and the blankets made a quiet little hill.")
    world.say(f"{hero.id} loved {activity.gerund}, especially around {prize.phrase}.")
    prize.worn_by = None

    world.para()
    world.say(f"{hero.id} started a small demolition spree and wanted to {activity.verb}.")
    if predict(world, hero, activity, prize.id)["messy"]:
        world.say(f'"Careful," {parent.id} said. "If you keep going, {prize.label} will end up {activity.soil}."')
    _demo(world, hero, activity)
    world.say(f"But {hero.id} kept going, and soon the little room looked {activity.soil}.")
    world.say(f"That made {parent.id} frown, because bedtime was getting later and later.")

    world.para()
    world.say(f"{hero.id} crossed their arms. " + '"I am not done," they said.')
    world.say(f'"I know," said {parent.id}, "and I know you are having fun. But now the room needs help."')
    world.say(f'They had a gentle dialogue by the bed: "{hero.id}, can you help me clean up?" "Maybe," {hero.id} whispered.')

    world.para()
    gear = select_gear(activity, prize)
    if gear:
        world.say(f'{parent.id} showed the toy basket and said, "First we can {gear.prep}."')
        world.say(f'{hero.id} nodded. Together they {gear.tail}.')
    actor = world.get(hero.id)
    actor.memes["conflict"] = 0
    actor.memes["lesson"] = 1
    world.say(f'{hero.id} learned a bedtime lesson: fun is nicer when everyone helps put things back.')
    world.say(f"At the end, the lamp still glowed, {prize.label} was safe, and the room was ready for sleep.")

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short bedtime story about demolition and a small spree, with a calm ending.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb}, but bedtime and a worried {f['parent'].label} create a conflict.",
        f"Write a child-friendly dialogue story that ends with a lesson learned about cleaning up {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb} during the bedtime story.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the {prize.label}?",
            answer=f"{parent.id} worried because {prize.label} could end up {act.soil} during the demolition spree.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn at the end?",
            answer=f"{hero.id} learned that fun is better when everyone helps put things back before sleep.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is demolition?",
            answer="Demolition is the act of taking something apart or knocking it down.",
        ),
        QAItem(
            question="What is a spree?",
            answer="A spree is a short burst of doing something with lots of energy, often all at once.",
        ),
        QAItem(
            question="Why do bedtime stories end calmly?",
            answer="Bedtime stories end calmly so a child can settle down, feel safe, and get ready to sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p, s in SETTINGS.items():
        lines.append(asp.fact("setting", p))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", p, a))
    for a, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("mess_of", a, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", a, r))
    for p, pr in PRIZES.items():
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, pr.region))
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


CURATED = [
    StoryParams(place="bedroom", activity="pillow_spree", prize="fort", name="Milo", parent="mom"),
    StoryParams(place="playroom", activity="block_spree", prize="tower", name="Nina", parent="dad"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
