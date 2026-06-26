#!/usr/bin/env python3
"""
A fable-style story world about a hymn, a dye station, and teamwork.

Seed premise:
- A small animal wants to sing a hymn while helping at a dye station.
- The dye is bright and messy, and a treasured hymnbook must stay clean.
- A warning is foreshadowed by a leaky basin.
- The fix comes through repetition, careful planning, and teamwork.

The world model keeps physical meters and emotional memes in motion so the
story is driven by state rather than by a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
MESS_KINDS = {"dye", "wet"}
REGIONS = {"hands", "torso", "feet"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "hen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "rooster"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


SETTING = Setting(place="the station square", indoors=False, affords={"dye"})
ACTIVITY = Activity(
    id="dye",
    verb="mix dye for the cloth",
    gerund="mixing dye",
    rush="run to the dye vats",
    mess="dye",
    soil="stained and spotted",
    zone={"hands", "torso"},
    keyword="dye",
    tags={"dye", "station", "repetition", "foreshadowing", "teamwork"},
)
PRIZES = {
    "hymnbook": Prize(
        label="hymnbook",
        phrase="a thin white hymnbook with gold corners",
        type="book",
        region="torso",
    ),
    "apron": Prize(
        label="apron",
        phrase="a clean apron for the dye station",
        type="apron",
        region="torso",
    ),
}
GEAR = [
    Gear(
        id="smock",
        label="a blue smock",
        covers={"torso"},
        guards={"dye"},
        prep="put on a blue smock first",
        tail="went back for the blue smock",
    ),
    Gear(
        id="gloves",
        label="gloves",
        covers={"hands"},
        guards={"dye"},
        prep="pull on gloves first",
        tail="ran back for the gloves",
        plural=True,
    ),
]

HERO_NAMES = ["Mina", "Pip", "Tavi", "Lula", "Nico", "Bram"]
HERO_TYPES = ["mule", "fox", "sparrow", "rabbit", "badger"]
HELPER_NAMES = ["Aunt Reed", "Old Finch", "Moss", "Wren", "Father Thorn"]
TRAITS = ["steady", "kind", "clever", "patient", "brave"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    hero_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(SETTING.place, "dye", prize_id) for prize_id in PRIZES]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the treasured item would not actually be in the dye's splash zone.)"
    return "(No story: there is no honest way to protect that item from dye with the available gear.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a hymn, dye, and teamwork at a station.")
    ap.add_argument("--place", choices=[SETTING.place], default=None)
    ap.add_argument("--activity", choices=["dye"], default=None)
    ap.add_argument("--prize", choices=list(PRIZES), default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--parent", choices=["helper"], default=None)
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
    prize = args.prize or rng.choice(list(PRIZES))
    if args.activity and args.prize:
        act = ACTIVITY
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    return StoryParams(
        place=SETTING.place,
        activity="dye",
        prize=prize,
        name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.gender and ("fox" if args.gender == "boy" else "rabbit") or rng.choice(HERO_TYPES),
        helper="Old Finch",
        trait=rng.choice(TRAITS),
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} set to work at the dye station.")


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dye"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dye"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} caught dye.")
    return out


def _workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get(item.caretaker)
        helper.meters["workload"] += 1
        out.append(f"That would mean more work for {helper.label}.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_soak, _workload):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), ACTIVITY, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": bool(prize.meters["dirty"] >= THRESHOLD)}


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type="hen", label=params.helper))
    prize = world.add(Entity(
        id=params.prize, type="book" if params.prize == "hymnbook" else "apron",
        label=params.prize, phrase=PRIZES[params.prize].phrase, owner=hero.id,
        caretaker=helper.id, region=PRIZES[params.prize].region,
    ))
    hero.memes["love"] += 1
    world.say(f"At {world.setting.place}, {hero.id} was known for a calm heart and a careful step.")
    world.say(f"{hero.id} loved the hymn, and {hero.pronoun()} sang it softly while helping at the dye station.")
    world.say(f"One old basin had a little crack, and that crack foreshadowed trouble, for it liked to drip.")
    world.say(f"{helper.label} gave {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"\"Keep it clean,\" {helper.label} said. \"Dye is lively stuff.\"")
    world.para()
    world.say(f"{hero.id} began to {ACTIVITY.verb}, and {hero.pronoun()} sang the hymn again and again: \"Sing slow, work slow, stay bright.\"")
    world.say(f"Sing slow, work slow, stay bright. Sing slow, work slow, stay bright.")
    world.say(f"Then the cracked basin tipped, just as the dripping had warned.")
    world.say(f"The dye rushed toward the {prize.label}.")
    world.say(f"{hero.id} gasped and tried to {ACTIVITY.rush}, but {hero.pronoun('possessive')} {helper.label.lower()} saw the spill too.")
    if predict_mess(world, hero, prize.id)["soiled"]:
        world.say(f"\"Teamwork,\" said {helper.label}. \"Two hands are better than one.\"")
        gear = select_gear(ACTIVITY, prize)
        if gear is None:
            raise StoryError(explain_rejection(ACTIVITY, prize))
        g = world.add(Entity(
            id=gear.id, type="gear", label=gear.label, owner=hero.id,
            caretaker=helper.id, protective=True, covers=set(gear.covers), plural=gear.plural
        ))
        g.worn_by = hero.id
        world.say(f"{hero.id} and {helper.label} worked together. First they {gear.prep}, then they lifted the basin with care.")
        world.say(f"They said the hymn line again and again: \"Sing slow, work slow, stay bright.\"")
        world.say(f"With the smock in place, the dye missed the {prize.label}.")
        hero.memes["joy"] += 1
        hero.memes["trust"] += 1
        hero.memes["conflict"] = 0
        world.say(f"At last {hero.id} finished the work, and the {prize.label} stayed clean.")
        world.say(f"The station square looked brighter for it, and the hymn sounded sweeter in the evening air.")
    propagate(world, narrate=True)
    world.facts.update(hero=hero, helper=helper, prize=prize, gear=gear if "gear" in locals() else None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, prize = f["hero"], f["prize"]
    return [
        f"Write a short fable for children about {hero.id}, a hymn, and a dye station.",
        f"Tell a story where a careful helper warns that a {prize.label} could be stained by dye.",
        f"Use repetition and teamwork in a simple story set at the station square.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} love to sing while working at the station?",
            answer=f"{hero.id} loved to sing a hymn while helping at the dye station.",
        ),
        QAItem(
            question=f"Why was {helper.label} worried about the {prize.label}?",
            answer=f"{helper.label} was worried because dye can stain, and the {prize.label} needed to stay clean.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} fix the problem?",
            answer=f"They used teamwork, put on the protective smock, and lifted the basin carefully so the dye would not reach the {prize.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is dye?",
            answer="Dye is a colored liquid or powder used to change the color of cloth or thread.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do a job.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is when a story gives a small clue that something important may happen later.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition is when a word, phrase, or line is used again to help it stand out or sound memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
    out = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id}: meters={meters} memes={memes}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- place(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", SETTING.place), asp.fact("affords", SETTING.place, "dye")]
    lines.append(asp.fact("activity", "dye"))
    lines.append(asp.fact("mess_of", "dye", ACTIVITY.mess))
    for r in sorted(ACTIVITY.zone):
        lines.append(asp.fact("splashes", "dye", r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place=SETTING.place, activity="dye", prize="hymnbook", name="Mina", hero_type="rabbit", helper="Old Finch", trait="steady"),
    StoryParams(place=SETTING.place, activity="dye", prize="apron", name="Pip", hero_type="fox", helper="Aunt Reed", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
