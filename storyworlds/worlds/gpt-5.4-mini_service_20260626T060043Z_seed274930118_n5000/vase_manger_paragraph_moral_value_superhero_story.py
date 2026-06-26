#!/usr/bin/env python3
"""
storyworlds/worlds/vase_manger_paragraph_moral_value_superhero_story.py
======================================================================

A small superhero-flavored story world with a clear moral value:
a young hero learns that real strength can be careful, kind, and honest.

Seed imagery used to build the world:
- a vase that can tip and break
- a manger in a barn-like place
- a paragraph that needs to be delivered or posted

The story premise:
A tiny superhero wants to rush through a place with something fragile nearby.
A mentor warns that speed and showing off can cause harm.
The hero chooses a gentler plan, protects the fragile things, and finishes
the task with pride and kindness.

This script is self-contained and follows the Storyweavers world contract.
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
    kind: str = "thing"  # "character" | "thing"
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
    traits: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"danger": 0.0, "mess": 0.0, "steady": 0.0}
        if not self.memes:
            self.memes = {"pride": 0.0, "worry": 0.0, "calm": 0.0, "gratitude": 0.0}

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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FragileThing:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False
    protective: bool = True


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


def _r_bump(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["danger"] < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind == "thing" and item.region in world.zone and not item.protective:
                sig = ("bump", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["danger"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} rushing made {item.label} wobble.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.kind != "thing" or item.meters["danger"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would worry {carer.label}.")
    return out


CAUSAL_RULES = [_r_bump, _r_worry]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: FragileThing) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: FragileThing) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"danger": prize.meters["danger"] >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["danger"] += 1
    actor.meters["steady"] += 1
    propagate(world, narrate=narrate)


def tell(world_setting: Setting, activity: Activity, prize_cfg: FragileThing,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(world_setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "brave"]))
    parent = world.add(Entity(id="Mentor", kind="character", type=parent_type, label="Captain Bright"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    hero.memes["pride"] += 1
    world.say(f"{hero.id} was a small superhero who loved helping everyone in {world_setting.place}.")
    world.say(f"{hero.id} also loved {activity.gerund}; it made the day feel fast and bright.")
    world.say(f"Near the path stood {prize.phrase}, and beside it was a quiet manger in the corner.")

    world.para()
    world.say(f"One day, {hero.id} spotted a paragraph that needed to be posted before sunset.")
    world.say(f"{hero.id} wanted to {activity.verb} right through the room to finish quickly.")
    if prize_at_risk(activity, prize_cfg):
        world.say(f"But {parent.label} saw the danger and said, \"Careful speed can still be superhero speed.\"")
    else:
        world.say(f"But {parent.label} still reminded {hero.id} to move gently around the fragile things.")

    world.para()
    hero.meters["danger"] += 1
    if prize_at_risk(activity, prize_cfg):
        world.say(f"{hero.id} took a step toward the paragraph, then heard the vase tremble softly.")
        world.say(f"That was enough to make {hero.id} slow down and look again.")
    _do_activity(world, hero, activity, narrate=True)

    world.para()
    gear_def = select_gear(activity, prize_cfg)
    if gear_def is not None:
        gear = world.add(Entity(
            id=gear_def.id,
            kind="thing",
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            protective=True,
            covers=set(gear_def.covers),
        ))
        gear.worn_by = hero.id
        hero.memes["calm"] += 1
        world.say(f"{parent.label} showed {hero.id} {gear_def.label} and said, \"Try the careful way.\"")
        world.say(f"{hero.id} wore {gear_def.label} first, then moved in a steadier line.")
        world.say(f"With that plan, {hero.id} could {activity.verb} without knocking the vase or bumping the manger.")
        world.say(f"{hero.id} posted the paragraph, and the room stayed peaceful.")
        hero.memes["gratitude"] += 1
        hero.memes["pride"] += 1
        world.say(f"{hero.id} smiled, because being careful had turned out to be a real heroic power.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=gear_def,
        setting=world_setting,
    )
    return world


SETTINGS = {
    "barn": Setting(place="the barn", indoor=False, affords={"dash", "glide"}),
    "hall": Setting(place="the hall", indoor=True, affords={"dash", "glide"}),
    "museum": Setting(place="the museum lobby", indoor=True, affords={"dash", "glide"}),
}

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash past the display",
        gerund="dashing past displays",
        rush="dash through the room",
        danger="bumping fragile things",
        zone={"floor", "shelf"},
        keyword="dash",
        tags={"speed"},
    ),
    "glide": Activity(
        id="glide",
        verb="glide across the floor",
        gerund="gliding across the floor",
        rush="glide down the hallway",
        danger="slipping near fragile things",
        zone={"floor"},
        keyword="glide",
        tags={"speed"},
    ),
}

FRAGILES = {
    "vase": FragileThing(
        id="vase",
        label="a blue vase",
        phrase="a blue vase on a narrow shelf",
        region="shelf",
    ),
    "manger": FragileThing(
        id="manger",
        label="the manger",
        phrase="the manger where a tiny lamb slept",
        region="floor",
    ),
    "paragraph": FragileThing(
        id="paragraph",
        label="the paragraph page",
        phrase="a paragraph page on a low stand",
        region="shelf",
    ),
}

GEAR = [
    Gear(
        id="slow_steps",
        label="slow boots",
        covers={"floor"},
        prep="put on slow boots first",
        tail="walked with slow boots on",
    ),
    Gear(
        id="carry_board",
        label="a carry board",
        covers={"shelf"},
        prep="use a carry board first",
        tail="carried the page on a carry board",
    ),
]

GIRL_NAMES = ["Nova", "Mira", "Ivy", "Zara", "Tess"]
BOY_NAMES = ["Ace", "Jett", "Leo", "Kai", "Finn"]
TRAITS = ["kind", "quick", "bright", "brave", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    fragile: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for frag_id, frag in FRAGILES.items():
                if prize_at_risk(act, frag) and select_gear(act, frag):
                    combos.append((place, act_id, frag_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short superhero story for a young child that includes the words vase, manger, and paragraph.",
        f"Tell a gentle hero story where {f['hero'].id} wants to {f['activity'].verb} but learns to move carefully around {f['prize'].label}.",
        f"Write a moral-value story about a superhero who chooses careful action over rushing and still finishes the job.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    activity = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, a small {hero.type} who wants to do the right thing and help the day go well.",
        ),
        QAItem(
            question=f"Why did {parent.label} tell {hero.id} to slow down?",
            answer=f"{parent.label} worried that rushing would bump {prize.label} and disturb the manger, so {hero.id} was told to choose a careful way.",
        ),
        QAItem(
            question=f"What did {hero.id} do with the paragraph?",
            answer=f"{hero.id} posted the paragraph after choosing a steadier plan, so the page got finished without making trouble.",
        ),
        QAItem(
            question=f"How did {gear.label} help {hero.id}?",
            answer=f"{gear.label} helped {hero.id} move more carefully, which kept the fragile things safe while {hero.id} finished the job.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vase?",
            answer="A vase is a container, often made of glass or ceramic, that people use for flowers or decoration.",
        ),
        QAItem(
            question="What is a manger?",
            answer="A manger is a box or trough where farm animals eat hay or food.",
        ),
        QAItem(
            question="What is a paragraph?",
            answer="A paragraph is a small group of sentences that go together in a piece of writing.",
        ),
        QAItem(
            question="What is a moral value in a story?",
            answer="A moral value is the helpful lesson a story teaches, like being careful, kind, or honest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), fragile(P), splashes(A, R), region(P, R).
has_fix(A, P) :- prize_at_risk(A, P), gear(G), covers(G, R), region(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for fid, f in FRAGILES.items():
        lines.append(asp.fact("fragile", fid))
        lines.append(asp.fact("region", fid, f.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
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
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(activity: Activity, fragile: FragileThing) -> str:
    if not prize_at_risk(activity, fragile):
        return f"(No story: {fragile.label} is not at risk in that scene.)"
    return f"(No story: no gear in this world can safely protect {fragile.label} from that action.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero moral-value story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--fragile", choices=FRAGILES)
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
    if args.activity and args.fragile:
        act = ACTIVITIES[args.activity]
        frag = FRAGILES[args.fragile]
        if not (prize_at_risk(act, frag) and select_gear(act, frag)):
            raise StoryError(explain_rejection(act, frag))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.fragile is None or c[2] == args.fragile)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, fragile = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, fragile=fragile, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], FRAGILES[params.fragile],
                 params.name, params.gender, params.parent, params.trait)
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
    StoryParams(place="barn", activity="dash", fragile="vase", name="Nova", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="hall", activity="glide", fragile="paragraph", name="Ace", gender="boy", parent="father", trait="kind"),
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
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
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
