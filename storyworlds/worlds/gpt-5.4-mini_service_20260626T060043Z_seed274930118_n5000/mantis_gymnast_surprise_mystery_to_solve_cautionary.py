#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mantis_gymnast_surprise_mystery_to_solve_cautionary.py
===============================================================================================================================

A small fable-style storyworld about a gymnast and a mantis, built around a
surprise, a mystery to solve, and a cautionary turn.

The world is intentionally compact:
- one child-facing hero, a gymnast
- one surprising helper, a mantis
- one small setting
- one risky activity
- one cherished item that might be ruined
- one practical fix that makes the ending safe

The story is simulated from state, not swapped from a fixed paragraph.
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
    traits: list[str] = field(default_factory=list)
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
        for k in ["dusty", "messy", "lost", "found", "soothed", "safe", "care"]:
            self.meters.setdefault(k, 0.0)
        for k in ["surprise", "curiosity", "worry", "caution", "joy", "pride", "trust"]:
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


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    caution: str
    tags: set[str] = field(default_factory=set)


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


SETTINGS = {
    "gym": Setting(place="the little gym", indoor=True, affords={"beam", "dance"}),
    "garden": Setting(place="the garden", indoor=False, affords={"search", "dance"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"search", "beam"}),
}

ACTIVITIES = {
    "beam": Activity(
        id="beam",
        verb="walk the balance beam",
        gerund="walking the balance beam",
        risk="a slippery wobble",
        mess="dusty",
        zone={"feet", "hands"},
        keyword="beam",
        caution="A tiny warning can keep a big fall away.",
        tags={"balance", "dust"},
    ),
    "dance": Activity(
        id="dance",
        verb="practice a fast turn",
        gerund="practicing a fast turn",
        risk="a dizzy slip",
        mess="messy",
        zone={"feet", "hands", "torso"},
        keyword="turn",
        caution="Hurrying can hide the safe step.",
        tags={"movement"},
    ),
    "search": Activity(
        id="search",
        verb="look for the missing ribbon",
        gerund="looking carefully for clues",
        risk="a wrong guess",
        mess="lost",
        zone={"hands"},
        keyword="clue",
        caution="When something is missing, slow eyes find what rushing misses.",
        tags={"mystery", "clue"},
    ),
}

PRIZES = {
    "ribbon": Prize(label="ribbon", phrase="a bright blue ribbon", type="ribbon", region="head"),
    "leotard": Prize(label="leotard", phrase="a clean white leotard", type="leotard", region="torso"),
    "shoes": Prize(label="shoes", phrase="soft practice shoes", type="shoes", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="wrap",
        label="a soft practice wrap",
        covers={"torso"},
        guards={"messy", "dusty"},
        prep="put on a soft practice wrap first",
        tail="went back for the soft practice wrap",
    ),
    Gear(
        id="towel",
        label="a clean towel",
        covers={"hands", "feet"},
        guards={"dusty", "messy"},
        prep="take a clean towel along",
        tail="brought the clean towel back",
    ),
    Gear(
        id="bow",
        label="a spare ribbon tie",
        covers={"head"},
        guards={"lost"},
        prep="tie on a spare ribbon tie",
        tail="used the spare ribbon tie",
    ),
]

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ada", "Iris", "Tia"]
BOY_NAMES = ["Pip", "Owen", "Theo", "Finn", "Jude", "Leo"]
TRAITS = ["careful", "brave", "curious", "patient", "spry"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone or act.id == "search":
                    combos.append((place, act_id, prize_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    actor.memes["surprise"] += 1
    if narrate:
        world.say(f"{actor.id} did not expect what {activity.keyword} would reveal.")
    propagate(world, narrate=narrate)


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("dusty", "messy"):
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["messy"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little messy.")
    return out


def _r_mystery(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    mantis = world.entities.get("Mantis")
    ribbon = world.entities.get("Prize")
    if hero and mantis and ribbon and hero.memes["curiosity"] >= THRESHOLD:
        sig = ("mystery",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["mystery_seen"] = True
            out.append("A small green mantis showed a hidden clue with its lifted front legs.")
    return out


def _r_warn(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    if not hero or hero.meters["dusty"] < THRESHOLD:
        return []
    sig = ("warn", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    return ["The little mantis seemed to say that rushing would make the trouble worse."]


def _r_resolve(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.type in {"girl", "boy"}), None)
    prize = world.entities.get("Prize")
    if not hero or not prize:
        return []
    out: list[str] = []
    if hero.memes["worry"] >= THRESHOLD and world.facts.get("gear"):
        sig = ("resolve", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            hero.memes["trust"] += 1
            out.append("The gymnast slowed down, and the small warning turned into wise help.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_soil, _r_mystery, _r_warn, _r_resolve):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or activity.id == "search"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id == "search" and gear.id == "bow":
            return gear
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


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
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
gear_fix(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), gear_fix(_,A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid_combos()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld with a gymnast and a mantis.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, prize=prize, name=name, gender=gender, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, traits=["gymnast", trait]))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=hero.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    mantis = world.add(Entity(id="Mantis", kind="character", type="mantis", label="the mantis"))
    hero.worn_by = None
    prize.worn_by = hero.id
    hero.memes["curiosity"] += 1
    world.say(f"{hero.id} was a gymnast who loved careful moves and clear landings.")
    world.say(f"One day, {hero.id} noticed {hero.pronoun('possessive')} {prize.label} and felt proud of {prize.phrase}.")
    world.para()
    world.say(f"At {setting.place}, {hero.id} went to {activity.verb}.")
    world.say(f"Then came a surprise: a small mantis stood still as if it knew a secret.")
    _do_activity(world, hero, activity, narrate=True)
    world.para()
    world.say(f"{hero.id} looked for a mystery to solve, because something did not feel quite right.")
    world.say(f"The mantis pointed toward the floor, where the clue was hidden.")
    world.say(f"It was a cautionary sign: the path was not safe enough for a quick leap.")
    gear = select_gear(activity, prize_cfg)
    if gear is not None:
        gear_ent = world.add(Entity(
            id=gear.id, type="gear", label=gear.label, protective=True,
            covers=set(gear.covers), plural=gear.plural, owner=hero.id,
        ))
        gear_ent.worn_by = hero.id
        world.facts["gear"] = gear
        world.say(f"{hero.id} listened, used {gear.label}, and chose the safer way.")
        hero.memes["caution"] += 1
        hero.memes["trust"] += 1
        hero.memes["joy"] += 1
        world.say(f"{hero.id} finished the practice without ruining {hero.pronoun('possessive')} {prize.label}.")
        world.say(f"From then on, {hero.id} remembered that a small warning can keep a big mistake away.")
    else:
        world.say(f"{hero.id} slowed down anyway, because wise feet can ignore a rush.")
    world.facts.update(hero=hero, prize=prize, mantis=mantis, activity=activity, setting=setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    act: Activity = f["activity"]
    prize: Prize = f["prize"]
    return [
        f'Write a short fable about a gymnast named {hero.id}, a mantis, and the word "{act.keyword}".',
        f"Tell a cautionary story where {hero.id} wants to {act.verb} but must protect {hero.pronoun('possessive')} {prize.label}.",
        f'Write a mystery-to-solve story for small children that includes a surprise mantis and ends safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Prize = f["prize"]
    act: Activity = f["activity"]
    gear: Optional[Gear] = f.get("gear")
    ans1 = f"It is about {hero.id}, a gymnast, and a small mantis who appears as a surprise."
    ans2 = f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} {prize.label} needed protection."
    qa = [
        QAItem(question="Who is the story about?", answer=ans1),
        QAItem(question="What did the gymnast want to do?", answer=ans2),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question="How did the gymnast stay safe?",
                answer=f"{hero.id} listened to the mantis, used {gear.label}, and chose the safer way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mantis?",
            answer="A mantis is a small insect with long legs and quick eyes. It can stay very still while it watches what is happening.",
        ),
        QAItem(
            question="What is a gymnast?",
            answer="A gymnast is a person who practices balance, jumping, stretching, and careful body moves.",
        ),
        QAItem(
            question="Why is caution helpful?",
            answer="Caution is helpful because it slows a person down just enough to notice a danger before it causes trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.trait)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:8} {act:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="gym", activity="beam", prize="leotard", name="Mina", gender="girl", trait="careful"),
            StoryParams(place="garden", activity="search", prize="ribbon", name="Leo", gender="boy", trait="curious"),
            StoryParams(place="meadow", activity="dance", prize="shoes", name="Nora", gender="girl", trait="patient"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
