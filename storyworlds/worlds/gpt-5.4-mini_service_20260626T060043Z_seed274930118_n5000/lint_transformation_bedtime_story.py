#!/usr/bin/env python3
"""
storyworlds/worlds/lint_transformation_bedtime_story.py
=======================================================

A small bedtime-story world about lint, soft things, and a gentle transformation.

Seed premise:
- A sleepy child loves a cozy bedtime item.
- Lint makes the cozy item not quite ready for sleep.
- A parent notices the problem and offers a calm, safe fix.
- The lint gets gathered and transformed into something neat and useful.

The world is intentionally small, classical, and state-driven:
physical meters track fluff, itch, and tidiness;
emotional memes track sleepiness, worry, and comfort.

The story shape stays close to a bedtime story:
setup -> soft trouble -> soothing turn -> settled ending image.
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
    held_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["lint", "itch", "tidy", "sleepiness", "worry", "comfort", "joy", "care"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


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
    zone: set[str]
    keyword: str
    turn: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    fix: str
    guards: set[str]
    covers: set[str]
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

    def held_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_lint(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["lint"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("lint", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["lint"] += 1
            item.meters["tidy"] -= 0.5
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up little lint.")
    return out


def _r_itch(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["lint"] < THRESHOLD:
            continue
        if actor.memes["sleepiness"] < THRESHOLD:
            continue
        sig = ("itch", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["itch"] += 1
        actor.memes["worry"] += 0.5
        out.append(f"The fuzz made {actor.id}'s nose feel a tiny bit itchy.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for lint_ball in list(world.entities.values()):
        if lint_ball.type != "lint" or lint_ball.meters["lint"] < THRESHOLD:
            continue
        sig = ("transform", lint_ball.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        lint_ball.type = "star"
        lint_ball.label = "little star"
        lint_ball.phrase = "a tiny stitched star"
        lint_ball.protective = True
        lint_ball.meters["lint"] = 0
        lint_ball.meters["tidy"] += 1
        lint_ball.memes["comfort"] += 1
        out.append("The lint gathered together and turned into a tiny soft star.")
    return out


CAUSAL_RULES = [
    ("lint", _r_lint),
    ("itch", _r_itch),
    ("transformation", _r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return f"The {setting.place} was quiet, and the lamp made a warm little circle of light."


def predict_lint(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "linted": prize.meters["lint"] >= THRESHOLD,
        "itch": actor.meters["itch"] + (1 if actor.meters["lint"] >= THRESHOLD else 0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["lint"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved bedtime and quiet stories.")


def loves_item(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["comfort"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} because it felt soft and safe.")


def evening_arrives(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} came to {world.setting.place}.")
    world.say(setting_detail(world.setting))
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {prize.label} was not quite ready.")


def warn(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    pred = predict_lint(world, hero, activity, prize.id)
    if pred["linted"]:
        world.facts["predicted_lint"] = True
        world.say(f"\"If you do that now, your {prize.label} will get linty,\" {parent.label_word} said softly.")
        world.say(f"\"Then we would need to clean it before sleep.\"")


def hesitation(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} looked at the {activity.keyword} and frowned just a little.")
    world.say(f"{hero.id} tried to {activity.rush}, but then paused.")


def offer_fix(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity, gear_def: Gear) -> Entity:
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        phrase=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(f"{parent.label_word} smiled and held up {gear_def.label}.")
    world.say(f"\"We can use the {gear_def.label} first, and then everything can feel tidy again,\" {parent.label_word} said.")
    return gear


def accept_fix(world: World, hero: Entity, parent: Entity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["worry"] = max(0, hero.memes["worry"] - 1)
    hero.memes["comfort"] += 1
    hero.memes["joy"] += 1
    world.say(f"{hero.id} nodded and let {hero.pronoun('possessive')} {parent.label_word} help.")
    world.say(f"They used the {gear_def.label}, and the lint turned into {gear_def.fix}.")
    world.say(f"At last, {hero.id}'s {prize.label} was clean, and the tiny soft {gear_def.fix} sat by the pillow like a bedtime treasure.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl", parent_type: str = "mother") -> World:
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
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_item(world, hero, prize)

    world.para()
    evening_arrives(world, hero, parent, prize, activity)
    warn(world, parent, hero, prize, activity)
    hesitation(world, hero, activity)

    gear_def = GEAR[activity.id]
    offer_fix(world, parent, hero, prize, activity, gear_def)
    _do_activity(world, hero, activity, narrate=True)
    accept_fix(world, hero, parent, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, setting=setting)
    return world


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"brush"}),
    "nursery": Setting(place="the nursery", affords={"brush"}),
    "hall": Setting(place="the hallway", affords={"brush"}),
}

ACTIVITIES = {
    "brush": Activity(
        id="brush",
        verb="brush the blanket",
        gerund="brushing the blanket",
        rush="reach for the blanket",
        mess="lint",
        zone={"torso"},
        keyword="lint",
        turn="transformation",
    ),
}

PRIZES = {
    "blanket": Prize(label="blanket", phrase="a fluffy bedtime blanket", type="blanket", region="torso"),
    "pajamas": Prize(label="pajamas", phrase="soft striped pajamas", type="pajamas", region="torso", plural=True),
    "pillow": Prize(label="pillow", phrase="a round pillow", type="pillow", region="torso"),
}

GEAR = {
    "brush": Gear(
        id="lint_roller",
        label="a lint roller",
        fix="a tiny soft star",
        guards={"lint"},
        covers={"torso"},
        tail="rolled the fuzz into a little star",
    )
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Noah", "Finn", "Theo", "Owen", "Eli"]

TRAITS = ["gentle", "sleepy", "curious", "cheerful"]


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
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        f'Write a bedtime story for a small child about "{activity.keyword}" and a gentle surprise.',
        f"Tell a cozy story where {hero.id} wants to {activity.verb} but {parent.label_word} notices the {prize.label} needs help.",
        f'Write a soft story that includes the word "{activity.keyword}" and ends with something tidy by the bed.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who loved bedtime and {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because the {prize.label} could pick up lint and stop feeling cozy.",
        ),
        QAItem(
            question=f"What happened when they used the {f['gear'].label}?",
            answer=f"The lint gathered together and turned into {f['gear'].fix}, so the bedtime item ended up neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is lint?",
            answer="Lint is soft fuzz that can come off cloth and collect on blankets, clothes, and pillows.",
        ),
        QAItem(
            question="What is a lint roller for?",
            answer="A lint roller is used to pick up fuzz and little bits from fabric so it looks tidy again.",
        ),
        QAItem(
            question="Why do bedtime stories feel calm?",
            answer="Bedtime stories feel calm because they are slow, gentle, and full of safe, cozy things.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append("protective=True")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A, P) :- activity(A), prize(P), zone(A, R), region(P, R).
needs_fix(A, P) :- at_risk(A, P), gear(G), guards(G, lint), covers(G, R), region(P, R).
valid_story(Place, A, P) :- affords(Place, A), at_risk(A, P), needs_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in setting.affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("zone", aid, "torso"))
        lines.append(asp.fact("mess", aid, act.mess))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in gear.guards:
            lines.append(asp.fact("guards", gid, m))
        for r in gear.covers:
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about lint and transformation.")
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
    prize_obj = PRIZES[prize]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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
    StoryParams(place="bedroom", activity="brush", prize="blanket", name="Mina", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="nursery", activity="brush", prize="pajamas", name="Noah", gender="boy", parent="father", trait="sleepy"),
    StoryParams(place="hall", activity="brush", prize="pillow", name="Lily", gender="girl", parent="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for p, a, pr in combos:
            print(f"  {p:8} {a:8} {pr:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
