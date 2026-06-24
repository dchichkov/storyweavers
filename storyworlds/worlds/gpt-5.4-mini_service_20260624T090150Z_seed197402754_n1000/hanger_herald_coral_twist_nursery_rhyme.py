#!/usr/bin/env python3
"""
Story world: hanger, herald, coral, and a tiny Twist in a nursery-rhyme mood.

This script is self-contained and follows the Storyweavers world contract:
- StoryParams plus registries
- build_parser / resolve_params / generate / emit / main
- prose engine with meters and memes
- inline ASP twin with a Python reasonableness gate
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in getattr(g, "covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


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
    "nursery": Setting(place="the nursery", indoor=True, affords={"twist"}),
}

ACTIVITIES = {
    "twist": Activity(
        id="twist",
        verb="twirl and twist",
        gerund="twirling and twisting",
        rush="whirl too fast",
        mess="rumpled",
        soil="all rumpled",
        zone={"torso"},
        keyword="Twist",
        tags={"twist", "coral"},
    ),
}

PRIZES = {
    "coral": Prize(
        label="coral ribbon",
        phrase="a bright coral ribbon",
        type="ribbon",
        region="torso",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="clip",
        label="a little cloth clip",
        covers={"torso"},
        guards={"rumpled"},
        prep="pin up the ribbon with a little cloth clip",
        tail="tiptoed back to the nursery and pinned the ribbon neatly",
    ),
]

GIRL_NAMES = ["Mia", "Nina", "Luna", "Tia", "Pippa", "Rose"]
BOY_NAMES = ["Noah", "Theo", "Benny", "Milo", "Ezra", "Finn"]
TRAITS = ["tiny", "cheerful", "curious", "spry", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    out.append((place, act_id, prize_id))
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world: hanger, herald, coral, and Twist.")
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
            raise StoryError("No story: Twist would wrinkle the coral ribbon, but there is no proper fix.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{
        **vars(v),
        "meters": dict(v.meters),
        "memes": dict(v.memes),
    }) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    a = sim.get(actor.id)
    a.meters = dict(actor.meters)
    _do_activity(sim, a, activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get(activity.mess, 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    _add_meter(actor, activity.mess, 1.0)
    _add_meme(actor, "joy", 1.0)
    if narrate:
        world.say(f"{actor.id} began to {activity.gerund}.")


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rumpled", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.label != "coral ribbon":
                continue
            sig = ("rumple", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            _add_meter(item, "rumpled", 1.0)
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got rumpled.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    hanger = world.add(Entity(id="hanger", type="thing", label="hanger"))
    herald = world.add(Entity(id="herald", type="thing", label="herald", phrase="a tiny herald bell"))
    prize = world.add(Entity(
        id="coral", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, worn_by=hero.id, meters={"clean": 1.0}, memes={}
    ))
    world.facts.update(hero=hero, parent=parent, hanger=hanger, herald=herald, prize=prize, activity=activity, prize_cfg=prize_cfg)
    world.say(f"In {setting.place}, little {trait} {hero.type} {hero.id} kept a {prize_cfg.label} on a hanger.")
    world.say(f"A herald chimed, \"Hear, hear!\" and the nursery felt bright as a berry.")
    world.para()
    world.say(f"{hero.id} loved to {activity.verb} beside the cradle and the quilt.")
    world.say(f"But {hero.pronoun('possessive')} {parent.pronoun('subject').capitalize()} said, \"Dear one, don't whirl too hard, or the coral ribbon will come to harm.\"")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 0.5
    world.para()
    world.say(f"{hero.id} tried to {activity.rush}, and the little room began to spin.")
    _do_activity(world, hero, activity, narrate=False)
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        _add_meme(parent, "concern", 1.0)
        world.say(f"\"Hush now,\" said {parent.id}, and {parent.pronoun('subject')} reached for the hanger.")
        world.say(f"The parent chose a kinder way: {GEAR[0].prep}.")
        gear = world.add(Entity(id=GEAR[0].id, type="gear", label=GEAR[0].label, protective=True))
        gear.worn_by = hero.id
        gear.covers = set(GEAR[0].covers)
        propagate(world, narrate=True)
        _add_meme(hero, "joy", 1.0)
        _add_meme(hero, "love", 1.0)
        world.say(f"Then {hero.id} could {activity.gerund}, and the coral ribbon stayed neat on the hanger.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a nursery-rhyme story about a child named {hero.id}, a {prize.label}, and the word "{act.keyword}".',
        f"Tell a gentle rhyme-like tale where {hero.id} wants to {act.verb} but {parent.id} worries about the {prize.label}.",
        f"Write a short child-friendly story that includes hanger, herald, coral, and a happy compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the nursery?",
            answer=f"{hero.id} wanted to {act.verb}, because the little room made {hero.pronoun('object')} want to spin and play.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the coral ribbon?",
            answer=f"{parent.id} worried because {hero.id}'s {act.gerund} could rumple the coral ribbon on the hanger.",
        ),
        QAItem(
            question=f"What helped keep the coral ribbon neat?",
            answer=f"A little cloth clip helped keep the coral ribbon neat while {hero.id} kept on playing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} still {act.gerund}, while the coral ribbon stayed neat on the hanger and everyone felt glad.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "twist": [
        ("What does it mean to twist something?", "To twist something is to turn it around and around so it changes shape or direction."),
    ],
    "coral": [
        ("What is coral?", "Coral is a colorful sea animal that can grow in big reefs under the ocean."),
    ],
    "hanger": [
        ("What is a hanger for?", "A hanger helps hold clothes up so they stay neat and easy to find."),
    ],
    "herald": [
        ("What is a herald?", "A herald is someone or something that gives an announcement or a little warning."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for tag in ("twist", "coral", "hanger", "herald") for q, a in KNOWLEDGE[tag]]


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
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", activity="twist", prize="coral", name="Mia", gender="girl", parent="mother", trait="tiny"),
    StoryParams(place="nursery", activity="twist", prize="coral", name="Noah", gender="boy", parent="father", trait="curious"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), guards(G,M), mess_of(A,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
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
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for row in vals:
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
