#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/aspirate_mooshy_basement_stairs_teamwork_slice_of.py
====================================================================================================================================

A standalone story world sketch for a Slice‑of‑Life tale about two children
working together to move a heavy, waterlogged rug up the basement stairs.
They must first aspirate the soggy mess (vacuum the water) and then cooperate
to carry the load – a small lesson in teamwork.

Domain elements:
- Settings: basement (stairs, downstairs floor), upstairs hallway.
- Activities: aspirate (wet‑vac), carry (team lift).
- Prize: the heavy wet rug (mooshy).
- Mess kinds: wet, muddy.
- Gear: wet/dry vacuum (“the shop vac”), teamwork (the lifting count).
- Characters: Lily (girl, older), Max (boy, younger), Mom (parent).
- Central tension: one child cannot lift it alone; teamwork solves it.

Seed words: aspirate, mooshy.  Setting: basement stairs.  Features: Teamwork.
Style: Slice of Life.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"wet", "muddy"}
REGIONS = {"hands", "back", "arms"}


# ---------------------------------------------------------------------------
# typed entity
# ---------------------------------------------------------------------------
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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


# ---------------------------------------------------------------------------
# parameter registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the basement"
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
    weather: str = ""
    keyword: str = ""
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


# ---------------------------------------------------------------------------
# world
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    """Both children need to carry together to avoid strain."""
    out: list[str] = []
    lifts = [e for e in world.entities.values() if e.memes.get("lifting", 0) >= THRESHOLD]
    if len(lifts) < 2 and any(e.memes.get("lifting", 0) >= THRESHOLD for e in world.characters()):
        # one child trying alone → strain
        for e in world.characters():
            if e.memes["lifting"] >= THRESHOLD:
                sig = ("alone_strain", e.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    e.memes["strain"] += 1
                    out.append(f"{e.id} grunted and felt a strain in {e.pronoun('possessive')} back.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="teamwork", tag="social", apply=_r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# prediction helper
# ---------------------------------------------------------------------------
def can_lift_alone(rug_weight: float) -> bool:
    return rug_weight < 2.0  # threshold: one child cannot lift if weight >= 2.0


# ---------------------------------------------------------------------------
# gear selection
# ---------------------------------------------------------------------------
def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# story beats
# ---------------------------------------------------------------------------
SETTINGS = {
    "basement": Setting(place="the basement", indoor=True, affords={"aspirate", "carry"}),
}

ACTIVITIES = {
    "aspirate": Activity(
        id="aspirate",
        verb="vacuum the water out of the rug",
        gerund="vacuuming the wet rug",
        rush="grab the shop vac",
        mess="wet",
        soil="mooshy and heavy",
        zone={"hands", "arms"},
        weather="",
        keyword="vacuum",
        tags={"wet", "vacuum"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the heavy rug up the stairs",
        gerund="carrying the soggy rug",
        rush="lift the rug alone",
        mess="muddy",
        soil="drenched and filthy",
        zone={"back", "arms"},
        weather="",
        keyword="teamwork",
        tags={"heavy", "carry"},
    ),
}

GEAR = [
    Gear(
        id="vacuum",
        label="the shop vac",
        covers={"hands", "arms"},
        guards={"wet"},
        prep="first aspirate the rug with the shop vac",
        tail="fetched the shop vac and sucked out the water",
    ),
    Gear(
        id="team",
        label="the two‑person carry",
        covers={"back"},
        guards={"heavy"},
        prep="ask your brother to help you carry it together",
        tail="called Max over and they each took a corner of the rug",
    ),
]

PRIZES = {
    "rug": Prize(
        label="rug",
        phrase="a huge, mooshy rug",
        type="rug",
        region="back",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe"]
BOY_NAMES = ["Max", "Ben", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    sibling: str
    sibling_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# generation prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f.get("hero")
    sibling = f.get("sibling")
    act = f.get("activity")
    return [
        f'Write a short slice‑of‑life story for children about teamwork, '
        f'including the words "aspirate" and "mooshy".',
        f"Tell a story where {hero.id} and {sibling.id} work together to "
        f"move a heavy wet rug up the basement stairs.",
        f"A story about a soggy rug, a shop vac, and two siblings who learn "
        f"that some jobs need two pairs of hands.",
    ]


# ---------------------------------------------------------------------------
# story QA
# ---------------------------------------------------------------------------
def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f.get("hero")
    sibling = f.get("sibling")
    act = f.get("activity")
    prize = f.get("prize")
    return [
        QAItem(
            question=f"Why could {hero.id} not carry the {prize.label} alone?",
            answer=f"Because the rug was still heavy and mooshy after the water soak. "
                   f"{hero.id} would have strained {hero.pronoun('possessive')} back."
        ),
        QAItem(
            question=f"What did {hero.id} and {sibling.id} do before carrying the rug upstairs?",
            answer=f"They first used the shop vac to aspirate the water out of the rug."
        ),
        QAItem(
            question=f"How did {hero.id} and {sibling.id} manage to get the rug upstairs?",
            answer=f"They each took a corner and carried it together – teamwork."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does 'aspirate' mean in this story?",
            answer="Aspirate means to suck out the water with a vacuum cleaner."
        ),
        QAItem(
            question="Why is teamwork important?",
            answer="Some tasks are too heavy or big for one person; working together makes them possible."
        ),
        QAItem(
            question="What makes a rug 'mooshy'?",
            answer="A mooshy rug is very wet and soft, like a sponge after a flood."
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
    lines.append("== (3) World‑knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# tell – generate the story
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity_id: str, prize_cfg: Prize,
         hero_name: str, hero_gender: str, sibling_name: str,
         sibling_gender: str) -> World:
    world = World(setting)
    act = ACTIVITIES[activity_id]

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_gender,
        traits=["helpful"],
    ))
    sibling = world.add(Entity(
        id=sibling_name, kind="character", type=sibling_gender,
        traits=["curious"],
    ))
    mom = world.add(Entity(id="Mom", kind="character", type="mother", label="the parent"))
    prize = world.add(Entity(
        id=prize_cfg.label, type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=mom.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 – discovery
    world.say(f"{hero_name} and {sibling_name} were in the basement when they saw the rug – "
              f"heavy, mooshy, and dripping from the broken pipe.")
    world.say(f"Mom called down: 'That rug needs to go upstairs, but it's too wet to move alone.'")

    world.para()
    # Act 2 – first try
    world.say(f"{hero_name} decided to try first.")
    world.say(f"{hero_name} grabbed one corner and pulled. The rug barely budged.")
    # simulate lifting alone -> strain
    hero.memes["lifting"] += 1
    propagate(world, narrate=True)

    world.para()
    # Act 3 – find the vacuum (aspirate)
    world.say(f"'{sibling_name}, get the shop vac!' {hero_name} called.")
    world.say(f"They worked together: {sibling_name} held the hose while {hero_name} "
              f"aspirated the water. Soon the rug was no longer mooshy.")
    # decrease wetness
    prize.meters["wet"] = 0.0
    prize.meters["dirty"] = 0.0

    world.para()
    # Act 4 – teamwork lift
    world.say(f"Now lighter, but still heavy, they each took a corner.")
    hero.memes["teamwork"] += 1
    sibling.memes["teamwork"] += 1
    world.say(f"'{hero_name}, on three. One, two, three!'")
    world.say(f"Together they lifted the rug and carried it up the basement stairs.")
    world.say(f"At the top, Mom smiled: 'You two make a great team.'")

    world.facts.update(hero=hero, sibling=sibling, prize=prize, prize_cfg=prize_cfg,
                       activity=act, setting=setting, mom=mom)
    return world


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
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
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="basement",
        activity="carry",
        prize="rug",
        name="Lily",
        gender="girl",
        sibling="Max",
        sibling_gender="boy",
    ),
    StoryParams(
        place="basement",
        activity="aspirate",
        prize="rug",
        name="Max",
        gender="boy",
        sibling="Zoe",
        sibling_gender="girl",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (f"(No story: the {prize.label} wouldn't get wet from {activity.gerund}.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% gear compatibility
compatible(G, A, P) :- gear(G), mess_of(A, M), guards(G, M),
                       covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), worn_on(P, R), splashes(A, R), compatible(_, A, P).
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
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print(" only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print(" only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice of Life: two siblings move a mooshy rug up the basement stairs.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
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
    # simplified: always basement, rug, one activity
    activity_id = args.activity if args.activity else rng.choice(["aspirate", "carry"])
    prize_id = args.prize if args.prize else "rug"
    gender = args.gender if args.gender else rng.choice(["girl", "boy"])
    name = args.name if args.name else rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling_gender = "boy" if gender == "girl" else "girl"
    sibling = args.sibling if args.sibling else rng.choice(BOY_NAMES if sibling_gender == "boy" else GIRL_NAMES)
    return StoryParams(
        place="basement",
        activity=activity_id,
        prize=prize_id,
        name=name,
        gender=gender,
        sibling=sibling,
        sibling_gender=sibling_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.activity, PRIZES[params.prize],
                 params.name, params.gender, params.sibling, params.sibling_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_combos()
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(f"  {t[0]:9} {t[1]:8} {t[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name} & {p.sibling}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
```
