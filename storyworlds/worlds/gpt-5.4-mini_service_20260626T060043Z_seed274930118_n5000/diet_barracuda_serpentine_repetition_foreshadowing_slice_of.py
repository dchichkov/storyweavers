#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/diet_barracuda_serpentine_repetition_foreshadowing_slice_of.py
===============================================================================================================

A small slice-of-life storyworld about a child helping care for a barracuda
on a careful diet. The world leans on repetition, foreshadowing, and a gentle
home-and-care routine rather than big adventure.

Seed-tale premise:
- A child loves visiting the tank.
- A barracuda must stay on a diet after getting too many treats.
- The child notices repeated small signs that too much food will make the fish sluggish.
- A caregiver offers a measured, serpentine feeding wand so the child can help safely.

This script models:
- the fish's hunger, fullness, and cheer
- the child's curiosity, patience, and worry
- the caregiver's workload and concern
- a simple turn from "more treats" to "careful portioning"

It also provides an inline ASP twin for the reasonableness gate: only stories
where the barracuda is actually at risk from overeating are considered valid.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    risk: str
    result: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _build_text(ent: Entity, noun: str) -> str:
    return f"{ent.id}'s {noun}"


def _do_feed(world: World, child: Entity, fish: Entity, activity: Activity, narrate: bool = True) -> None:
    child.meters["effort"] = child.meters.get("effort", 0) + 1
    fish.meters["fed"] = fish.meters.get("fed", 0) + 1
    fish.meters["hunger"] = max(0.0, fish.meters.get("hunger", 0.0) - 1.0)
    fish.meters["fullness"] = fish.meters.get("fullness", 0.0) + 1.0
    child.memes["care"] = child.memes.get("care", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} fed {fish.id} one careful bite at a time.")


def _r_overfull(world: World) -> list[str]:
    out: list[str] = []
    fish = world.entities.get("barracuda")
    if not fish:
        return out
    if fish.meters.get("fullness", 0.0) < THRESHOLD:
        return out
    sig = ("overfull", fish.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fish.memes["sluggish"] = fish.memes.get("sluggish", 0.0) + 1.0
    out.append("The barracuda looked sluggish from too many treats.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    fish = world.entities.get("barracuda")
    keeper = world.entities.get("caregiver")
    if not fish or not keeper:
        return out
    if fish.memes.get("sluggish", 0.0) < THRESHOLD:
        return out
    sig = ("workload", fish.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keeper.meters["worry"] = keeper.meters.get("worry", 0.0) + 1.0
    out.append("That would mean more care for the caregiver.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_overfull, _r_workload):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_overfeed(world: World, child: Entity, fish: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_feed(sim, child=sim.get(child.id), fish=sim.get(fish.id), activity=activity, narrate=False)
    propagate(sim, narrate=False)
    return sim.get(fish.id).memes.get("sluggish", 0.0) >= THRESHOLD


def select_gear(activity: Activity) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards:
            return gear
    return None


SETTINGS = {
    "tank room": Setting(place="the tank room", affords={"feed"}),
    "quiet kitchen": Setting(place="the quiet kitchen", affords={"feed"}),
    "sunny porch": Setting(place="the sunny porch", affords={"feed"}),
}

ACTIVITIES = {
    "feed": Activity(
        id="feed",
        verb="feed the barracuda",
        gerund="feeding the barracuda",
        rush="reach for another treat",
        risk="too many treats",
        result="sluggish",
        keyword="diet",
        tags={"diet", "barracuda"},
    ),
}

GEAR = [
    Gear(
        id="measure_cup",
        label="a small measuring cup",
        prep="use a small measuring cup first",
        tail="kept using the measuring cup",
        guards={"diet"},
    ),
    Gear(
        id="serpentine_wand",
        label="a long serpentine feeding wand",
        prep="use the long serpentine feeding wand",
        tail="followed the serpentine curve of the wand",
        guards={"diet"},
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Milo", "Ben"]
TRAITS = ["curious", "patient", "gentle", "careful", "quiet"]


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [(place, act_id) for place, s in SETTINGS.items() for act_id in s.affords]


def explain_rejection(activity: Activity) -> str:
    return f"(No story: the barracuda is not at real risk here, so there is no honest diet problem to solve.)"


def tell(setting: Setting, activity: Activity, hero_name: str, gender: str, caregiver_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["little", trait]))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=caregiver_type, label=caregiver_type))
    fish = world.add(Entity(id="barracuda", kind="character", type="fish", label="barracuda"))
    fish.meters["hunger"] = 1.0
    fish.meters["fullness"] = 0.0
    fish.memes["restless"] = 1.0

    world.say(f"{child.id} liked visiting {setting.place} after school.")
    world.say(f"Every day, {child.id} watched the barracuda glide in a smooth, serpentine line through the water.")
    world.say(f"{child.id} also knew the barracuda was on a diet, so the treats had to stay tiny.")

    world.para()
    world.say(f"At {setting.place}, {child.id} wanted to {activity.verb}, but {child.pronoun('possessive')} {caregiver.label} held up a hand.")
    world.say(f'"One more snack is how a diet gets broken," {caregiver.id} said, and {child.id} heard the warning.')

    if predict_overfeed(world, child, fish, activity):
        fish.meters["fullness"] += 1.0
        propagate(world, narrate=True)
        world.say(f"{child.id} reached for another treat, then paused when the barracuda slowed and turned in a lazy arc.")
    else:
        world.say(f"{child.id} noticed the barracuda nudging the glass again and again, as if it were already asking for too much.")
        world.say(f"That little warning made the room feel serious for a moment.")

    world.para()
    gear = select_gear(activity)
    if not gear:
        raise StoryError("(No reasonable gear for this story.)")
    world.say(f"Then {caregiver.id} showed {child.id} {gear.label} and said, \"{gear.prep}.\"")
    world.say(f"{child.id} counted slowly, one, two, three, and {gear.tail}.")
    _do_feed(world, child, fish, activity, narrate=False)
    fish.meters["fullness"] = 0.0
    fish.memes["sluggish"] = 0.0
    fish.memes["calm"] = fish.memes.get("calm", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    world.say(f"The barracuda took the measured bites and then glided off cleanly, bright and alert again.")
    world.say(f"By the end, {child.id} was smiling at the tank, and the careful diet had stayed on track.")

    world.facts.update(
        child=child,
        caregiver=caregiver,
        fish=fish,
        setting=setting,
        activity=activity,
        gear=gear,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    return [
        'Write a slice-of-life story about a child helping care for a barracuda on a diet, with repetition and foreshadowing.',
        f"Tell a gentle story where {child.id} wants to feed a barracuda but {caregiver.label} worries about the diet.",
        "Write a small home-and-care story with a serpentine feeding tool and a careful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    fish = f["fish"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was helping the barracuda stay on its diet?",
            answer=f"{child.id} was helping, with {caregiver.id} keeping the treats measured.",
        ),
        QAItem(
            question=f"Why did {caregiver.id} stop {child.id} from adding more food?",
            answer="Because the barracuda was already on a diet, and too many treats would make it sluggish.",
        ),
        QAItem(
            question=f"What did the serpentine feeding tool help them do?",
            answer=f"It helped {child.id} give the barracuda a careful portion instead of a big extra snack.",
        ),
        QAItem(
            question=f"How did the story end for the barracuda?",
            answer="The barracuda got the right amount to eat and glided away bright and alert.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a diet?",
            answer="A diet is the food and drink a person or animal usually gets, especially when the amount has to be watched carefully.",
        ),
        QAItem(
            question="What is a barracuda?",
            answer="A barracuda is a fast, long fish with a pointed face and sharp teeth.",
        ),
        QAItem(
            question="What does serpentine mean?",
            answer="Serpentine means winding like a snake, with a curving path or shape.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="tank room", activity="feed", name="Mina", gender="girl", caregiver="aunt", trait="curious"),
    StoryParams(place="quiet kitchen", activity="feed", name="Theo", gender="boy", caregiver="uncle", trait="careful"),
    StoryParams(place="sunny porch", activity="feed", name="Ivy", gender="girl", caregiver="mother", trait="patient"),
]


ASP_RULES = r"""
risk(feed) :- keyword(feed, diet).
valid_story(P, A) :- affords(P, A), risk(A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set((p, a) for p, a in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a barracuda on a diet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--caregiver", choices=["aunt", "uncle", "mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
              and (args.activity is None or c[1] == args.activity)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["aunt", "uncle", "mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, caregiver=caregiver, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], params.name, params.gender, params.caregiver, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, act in combos:
            print(f"  {place:12} {act}")
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
