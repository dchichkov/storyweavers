#!/usr/bin/env python3
"""
Storyworld: bedtime dab-and-giggle.

A small bedtime-style story domain about a child who wants one more tiny dab of
fun before sleep, while a grownup remembers a flashback about what helps the
night go smoothly. The conflict is gentle, the compromise is concrete, and the
ending proves the change in the world state.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "cozy": 0.0, "sleepy": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "giggle": 0.0, "comfort": 0.0, "memory": 0.0}

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
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)
    cozy: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    flashback: str
    bedtime: str
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
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            if actor.meters["mess"] < THRESHOLD:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up a little mess.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["comfort"] < THRESHOLD or actor.memes["worry"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        out.append(f"The worry melted away.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soil, _r_comfort):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, activity: Activity, prize: Prize) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {"messy": sim.get(prize.id).meters["mess"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["mess"] += 1
    actor.memes["giggle"] += 1
    propagate(world, narrate=narrate)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def bedtime_greeting(world: World, hero: Entity, parent: Entity) -> None:
    world.say(
        f"It was bedtime in {world.setting.place}, and {hero.id} was still wide awake."
    )
    world.say(
        f"{hero.id} curled up with a sleepy smile while {parent.label} tucked the blanket high."
    )


def desire(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} whispered, "Can I have one tiny {activity.keyword}?" '
        f'{hero.pronoun().capitalize()} wanted to {activity.verb}, '
        f"but {hero.pronoun('possessive')} {prize.label} was already on."
    )


def flashback(world: World, parent: Entity, activity: Activity, prize: Entity) -> None:
    parent.memes["memory"] += 1
    world.say(
        f'{parent.label} smiled. "I remember," {parent.pronoun()} said softly. '
        f'"Last night, when {hero_name(world)} tried to {activity.rush}, '
        f"{prize.label} got {activity.mess}.""
    )


def hero_name(world: World) -> str:
    return world.facts["hero"].id


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize)
    if not pred["messy"]:
        return False
    world.say(
        f'"If you {activity.verb}, your {prize.label} will get messy," {parent.label} said. '
        f'"Let’s choose a gentler way."'
    )
    return True


def giggle_dialogue(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["giggle"] += 1
    world.say(
        f'{hero.id} gave a little giggle. "What if I just dab?" {hero.pronoun()} asked.'
    )
    world.say(
        f'{parent.label} laughed too. "A dab is perfect," {parent.pronoun()} said. '
        f'"We can keep the bedtime picture neat."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural
    ))
    gear.worn_by = hero.id
    if predict(world, hero, activity, prize)["messy"]:
        del world.entities[gear.id]
        return None
    world.say(
        f'{parent.label} brought out {gear.label}. "{gear_def.prep}," {parent.pronoun()} said.'
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["comfort"] += 1
    world.say(
        f'{hero.id} nodded and did a tiny {activity.keyword} dab instead of a big splash. '
        f'Then {hero.id} giggled, because the moon picture looked just right.'
    )
    world.say(
        f"They settled under the blanket, and {hero.id}'s {prize.label} stayed clean. "
        f"{parent.label} kissed the top of {hero.id}'s head, and the room grew quiet and cozy."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name_: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name_, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity)

    bedtime_greeting(world, hero, parent)
    world.para()
    desire(world, hero, activity, prize)
    flashback(world, parent, activity, prize)
    warn(world, parent, hero, activity, prize)
    giggle_dialogue(world, hero, parent)
    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        resolve(world, hero, parent, activity, prize, gear_def)
    world.facts["gear"] = gear_def
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"dab"}),
    "nursery": Setting(place="the nursery", affords={"dab"}),
}

ACTIVITIES = {
    "dab": Activity(
        id="dab",
        verb="dab tiny stars on the blanket",
        gerund="dabbing tiny stars on the blanket",
        rush="dab the stars too fast",
        mess="smudged",
        zone={"blanket"},
        keyword="dab",
        flashback="a little dab of paint on the pillowcase",
        bedtime="bedtime",
        tags={"dab", "giggle", "bedtime"},
    )
}

PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="a soft white blanket",
        type="blanket",
        region="blanket",
    )
}

GEAR = [
    Gear(
        id="tiny_pad",
        label="a tiny paper pad",
        prep="let's use a tiny paper pad for the stars",
        tail="used the tiny paper pad",
        covers={"blanket"},
        guards={"smudged"},
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Ben"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for activity in setting.affords:
            for prize in PRIZES:
                if select_gear(ACTIVITIES[activity], PRIZES[prize]):
                    combos.append((place, activity, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a bedtime story with the words "dab" and "giggle".',
        f'Tell a gentle dialogue where {hero.id} wants to {act.verb}, but a parent remembers a flashback and helps instead.',
        f'Write a short cozy story in which a child chooses a safer way to {act.keyword} at bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at bedtime?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry?",
            answer=f"{parent.label} worried because the {prize.label} could get {act.mess}.",
        ),
        QAItem(
            question=f"What did the flashback remind {parent.label} about?",
            answer=f"The flashback reminded {parent.label} of the last time {hero.id} rushed and made a little mess.",
        ),
        QAItem(
            question=f"How did they keep the {prize.label} clean?",
            answer=f"They used {gear.label} and chose a tiny {act.keyword} dab instead of a big splat.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dab mean?",
            answer="A dab is a tiny gentle touch, like a small dot or brush of paint.",
        ),
        QAItem(
            question="What is a giggle?",
            answer="A giggle is a small happy laugh that sounds light and bubbly.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short memory scene that shows something from before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy bedtime story world about dab, giggle, dialogue, and flashback.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), guards(G, M), mess_of(A, M), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), protects(_, A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=p, activity=a, prize=r, name="Mina", gender="girl", parent="mother")) for p, a, r in valid_combos()]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
