#!/usr/bin/env python3
"""
storyworlds/worlds/aleck_pedicure_magic_space_adventure.py
===========================================================

A standalone storyworld for a small space-adventure tale with a magical
pedicure, built as a constraint-checked simulation.

Seed tale premise:
---
Aleck is excited for a tiny space adventure. Aleck gets a magical pedicure
before a trip to a moon garden. The magic makes the toes sparkle, but the
moon dust and space rocks could ruin the polish. A grown-up and Aleck find a
safe way to travel so the pedicure can still shine.

World model:
---
- The hero, Aleck, has a prized magical pedicure on their feet.
- Space travel and moon walks can scatter dust, scratches, and cold grit.
- Protective gear can keep the pedicure safe if it covers the right region.
- The story turns when caution becomes a clever space-ready compromise.

This script follows the Storyworld contract:
- self-contained stdlib script
- shared results containers imported eagerly
- ASP helper imported lazily
- StoryParams, registries, parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify,
  --show-asp
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

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    spacey: bool = True


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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_scuff(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("dusty", "sparkly"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("scuff", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.id}'s {item.label} got dusty.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean extra clean-up for {carer.label}.")
    return out


CAUSAL_RULES = [
    _r_scuff,
    _r_work,
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": bool(prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the launch pad":
        return "The launch pad gleamed like a silver stage under the stars."
    if setting.place == "the moon base":
        return "The moon base was quiet, with tiny lights blinking in rows."
    return "The ship hummed softly, ready for a small adventure."


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"Aleck was a little space explorer who loved shiny surprises.")


def loves_magic(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_magic"] = hero.memes.get("love_magic", 0.0) + 1
    world.say(
        f"Aleck loved the magic in the air and the idea of a tiny adventure among the stars."
    )


def gives_pedicure(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"Before the trip, {parent.label} gave Aleck a magical pedicure with glittery polish."
    )
    world.say(f"Aleck loved {prize.it()} and twirled {prize.it()} to watch the sparkle.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One day, Aleck and {parent.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"Aleck wanted to {activity.verb}, but the moon path looked dusty and rough.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_workload"] = pred["workload"]
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"You\'ll get your {prize.label} {activity.soil}," {parent.label} said. '
        f'"Let\'s choose the safe way."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"Aleck kept looking at the moon path and took one eager step forward.")
    world.say(f"Aleck tried to {activity.rush}.")


def hold_back(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held_back"] = hero.memes.get("held_back", 0.0) + 1
    world.say(f"But {parent.label} held out a hand and stopped the dash.")
    world.say(
        f'"You can still {activity.verb}," {parent.label} said, "but we need the right gear first."'
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{parent.label} smiled and said, \"How about we {gear_def.prep}?\""
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"Aleck grinned and hugged {parent.label}.")
    world.say(
        f'Then they {gear_def.tail}. Soon Aleck was {activity.gerund}, and {prize.label} stayed clean and bright.'
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Aleck", hero_type: str = "child", parent_type: str = "parent") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the grown-up"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )

    introduce(world, hero)
    loves_magic(world, hero, activity)
    gives_pedicure(world, parent, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    hold_back(world, parent, hero, activity)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear_def, setting=setting)
    return world


SETTINGS = {
    "ship": Setting(place="the ship", affords={"walk"}),
    "launch_pad": Setting(place="the launch pad", affords={"walk", "dash"}),
    "moon_base": Setting(place="the moon base", affords={"walk"}),
}

ACTIVITIES = {
    "walk": Activity(
        id="walk",
        verb="walk on the moon path",
        gerund="walking carefully across the moon path",
        rush="dash across the moon path",
        mess="dusty",
        soil="full of moon dust",
        zone={"feet"},
        keyword="moon",
        tags={"moon", "dust"},
    ),
    "dash": Activity(
        id="dash",
        verb="dash to the rover",
        gerund="dashing toward the rover",
        rush="dash to the rover",
        mess="dusty",
        soil="full of moon dust",
        zone={"feet"},
        keyword="rover",
        tags={"moon", "dust", "rover"},
    ),
}

PRIZES = {
    "pedicure": Prize(
        label="pedicure",
        phrase="a magical pedicure with glittery polish",
        type="pedicure",
        region="feet",
        genders={"girl", "boy"},
    )
}

GEAR = [
    Gear(
        id="moon_boots",
        label="moon boots",
        covers={"feet"},
        guards={"dusty"},
        prep="put on our moon boots first",
        tail="pulled on the moon boots and stepped outside again",
    ),
]


GIRL_NAMES = ["Mia", "Zoe", "Ava"]
BOY_NAMES = ["Ben", "Leo", "Noah"]
CHILD_NAMES = ["Aleck", "Alec", "Alex"]
TRAITS = ["curious", "brave", "bright"]


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


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "moon": [("What is the moon?", "The moon is a round rock in space that goes around Earth.")],
    "dust": [("What is space dust?", "Space dust is made of tiny bits floating around in space.")],
    "rover": [("What is a rover?", "A rover is a small robot or vehicle that drives across a planet or moon.")],
    "pedicure": [("What is a pedicure?", "A pedicure is when feet and toenails are cleaned, cared for, and painted.")],
    "magic": [("What is magic in a story?", "Magic in a story can be a special power that makes something sparkle or change in a surprising way.")],
    "boots": [("What are boots for?", "Boots protect your feet and help keep them safe and clean.")],
}

KNOWLEDGE_ORDER = ["moon", "dust", "rover", "pedicure", "magic", "boots"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = f["activity"]
    return [
        f'Write a short space adventure story for a young child that includes "{f["hero"].id}" and the word "{act.keyword}".',
        f"Tell a gentle story where Aleck wants to {act.verb} but must keep a magical pedicure safe.",
        f"Write a child-friendly moon trip story with a magical pedicure, a warning, and a safe compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about Aleck, a little space explorer who gets a magical pedicure before the trip.",
        ),
        QAItem(
            question=f"What did Aleck want to do on the moon path?",
            answer=f"Aleck wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the grown-up worry about Aleck's pedicure?",
            answer=f"The grown-up worried because {act.soil} could ruin the magical pedicure on Aleck's feet.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the moon boots help?",
                answer=f"The moon boots covered Aleck's feet, so Aleck could {act.verb} without getting the pedicure dusty.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add("boots")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    out.append(
        QAItem(
            question="What does magic often do in a story?",
            answer="Magic often makes something look special, sparkle, or change in a surprising way.",
        )
    )
    return out


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_base", activity="walk", prize="pedicure", name="Aleck", gender="boy", parent="parent", trait="curious"),
    StoryParams(place="launch_pad", activity="dash", prize="pedicure", name="Aleck", gender="boy", parent="parent", trait="brave"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return "(No story: the prize is not actually at risk in this activity.)"
    return "(No story: no gear in this tiny world can safely fix that combination.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this prize is not restricted by gender here; try one of {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
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
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with a magical pedicure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["parent"])
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
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    name = args.name or "Aleck"
    parent = args.parent or "parent"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(" ", combo)
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
