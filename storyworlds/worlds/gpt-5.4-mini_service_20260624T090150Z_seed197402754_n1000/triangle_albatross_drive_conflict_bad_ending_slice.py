#!/usr/bin/env python3
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

SETTING_NAME = "the driveway"
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = SETTING_NAME
    indoors: bool = False
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("defiance", 0.0) < THRESHOLD or actor.memes.get("stopped", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1.0
        out.append("__conflict__")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("speed", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["bent"] = item.meters.get("bent", 0.0) + 1.0
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got bent and dirty.")
    return out


def _r_bird_fright(world: World) -> list[str]:
    out: list[str] = []
    bird = world.entities.get("alby")
    if not bird:
        return out
    if bird.memes.get("startled", 0.0) < THRESHOLD:
        return out
    sig = ("fright", bird.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bird.memes["fear"] = bird.memes.get("fear", 0.0) + 1.0
    out.append("The albatross flapped away in a hurry.")
    return out


CAUSAL_RULES = [
    _r_conflict,
    _r_damage,
    _r_bird_fright,
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_setting() -> Setting:
    return Setting(place=SETTING_NAME, indoors=False, affords={"drive"})


ACTIVITY = Activity(
    id="drive",
    verb="drive the little wagon",
    gerund="driving the little wagon",
    rush="roll the wagon down the driveway",
    mess="scuffed",
    soil="scuffed up",
    zone={"path"},
    keyword="drive",
    tags={"drive", "wheel"},
)

PRIZE = Prize(
    label="triangle sign",
    phrase="a bright triangle sign",
    type="sign",
    region="path",
)

GIRL_NAMES = ["Mina", "Lina", "Pia", "Mara", "Tia"]
BOY_NAMES = ["Owen", "Nate", "Toby", "Theo", "Jude"]
TRAITS = ["quiet", "curious", "cheerful", "stubborn", "gentle"]


def predict_bad(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "dirty": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "bent": bool(prize and prize.meters.get("bent", 0.0) >= THRESHOLD),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters["speed"] = actor.meters.get("speed", 0.0) + 1.0
    propagate(world, narrate=narrate)


def tell(name: str, gender: str, parent_kind: str, trait: str) -> World:
    world = World(build_setting())
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_kind, label="mom" if parent_kind == "mother" else "dad"))
    alby = world.add(Entity(id="alby", kind="character", type="bird", label="albatross", plural=False, meters={}, memes={}))
    sign = world.add(Entity(
        id="triangle",
        type="sign",
        label="triangle sign",
        phrase="a bright triangle sign",
        owner=hero.id,
        caretaker=parent.id,
        region="path",
        meters={"dirty": 0.0, "bent": 0.0},
        memes={},
    ))

    hero.memes["love"] = 1.0
    world.say(f"{hero.id} was a {trait} child who liked the little things in a normal day.")
    world.say(f"{hero.id} loved the driveway, the tidy path, and the bright triangle sign near the flower pot.")
    world.say(f"One morning, {hero.id}'s {parent.label_word} brought out the wagon, and the albatross watched from the fence.")
    world.para()
    world.say(f"{hero.id} wanted to {ACTIVITY.verb}, but the albatross stood near the triangle sign.")
    bad = predict_bad(world, hero, ACTIVITY, sign.id)
    if bad["dirty"] or bad["bent"]:
        world.say(f"\"Not now,\" {parent.label_word} said. \"If you hurry, the wagon could bump the triangle sign.\"")
    hero.memes["defiance"] = 1.0
    hero.memes["stopped"] = 1.0
    world.say(f"{hero.id} frowned and tried to {ACTIVITY.rush}, even though the warning was plain.")
    _do_activity(world, hero, ACTIVITY, narrate=True)
    sign.meters["dirty"] = sign.meters.get("dirty", 0.0) + 1.0
    sign.meters["bent"] = sign.meters.get("bent", 0.0) + 1.0
    alby.memes["startled"] = 1.0
    propagate(world, narrate=True)
    world.para()
    world.say(f"The wagon stopped crooked on the driveway.")
    world.say(f"The triangle sign was scuffed, the albatross had flown off, and {parent.label_word} had to clean up the mess.")
    world.say(f"{hero.id} felt small and quiet, because the little drive had turned into a bad ending.")
    world.facts.update(hero=hero, parent=parent, bird=alby, prize=sign, activity=ACTIVITY, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    act = f["activity"]
    return [
        f"Write a slice-of-life story about {hero.id}, an albatross, and a triangle sign on a driveway.",
        f"Tell a gentle but unhappy story where {hero.id} wants to {act.verb} and {parent.label_word} worries.",
        f"Write a short story that uses the words triangle, albatross, and drive, and ends with a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Who wanted to drive the little wagon?",
            answer=f"{hero.id} wanted to drive the little wagon on the driveway.",
        ),
        QAItem(
            question=f"What did the {parent.label_word} worry would happen to the triangle sign?",
            answer=f"{parent.label_word.capitalize()} worried the wagon would bump and scuff the triangle sign.",
        ),
        QAItem(
            question=f"What made the day turn into a bad ending?",
            answer=f"The conflict happened when {hero.id} ignored the warning, the wagon hit the triangle sign, and the albatross flew away frightened.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a triangle?",
            answer="A triangle is a shape with three straight sides and three corners.",
        ),
        QAItem(
            question="What is an albatross?",
            answer="An albatross is a very large seabird with long wings.",
        ),
        QAItem(
            question="What is a driveway for?",
            answer="A driveway is the path where cars or wagons can move from the street to a home.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: triangle, albatross, drive; conflict and a bad ending.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["mother", "father"], default=None)
    ap.add_argument("--trait", choices=TRAITS, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.trait)
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


ASP_RULES = r"""
activity(drive).
setting(driveway).
prize(triangle).
a_wants_drive(hero) :- hero(hero).
conflict(hero) :- wants(hero,drive), warned(hero), ignored(hero).
bad_ending(hero) :- conflict(hero), damage(triangle), bird_fright(albatross).
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("wants", "hero", "drive"),
        asp.fact("warned", "hero"),
        asp.fact("ignored", "hero"),
        asp.fact("damage", "triangle"),
        asp.fact("bird_fright", "albatross"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/1. #show bad_ending/1."))
    atoms = set((a.name, tuple(str(x) for x in a.arguments)) for a in model)
    expected = {("conflict", ("hero",)), ("bad_ending", ("hero",))}
    if atoms == expected:
        print("OK: ASP matches Python reasonableness.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/1. #show bad_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    for i in range(args.n if not args.all else 1):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
