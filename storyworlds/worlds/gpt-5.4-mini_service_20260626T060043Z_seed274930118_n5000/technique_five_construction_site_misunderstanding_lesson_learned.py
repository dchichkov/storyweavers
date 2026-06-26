#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/technique_five_construction_site_misunderstanding_lesson_learned.py
=====================================================================================================

A small standalone storyworld set at a construction site, built from a seed
about a misunderstanding, a lesson learned, and a happy ending.

The world keeps the story close to a space-adventure tone: the child and crew
speak like mission helpers, the site feels like a launch deck for a big build,
and the fix comes from careful teamwork rather than magic.

Core premise:
- A child helper hears "Technique Five" and misunderstands what it means.
- That misunderstanding creates a small problem on a construction site.
- A mentor explains the lesson.
- The child learns, adjusts, and the build ends happily.

This script follows the Storyweavers world contract:
- typed entities with physical meters and emotional memes
- a Python reasonableness gate plus inline ASP twin
- generate/emit/main plus JSON, QA, trace, verify, and ASP modes
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


# ---------------------------------------------------------------------------
# World data model
# ---------------------------------------------------------------------------
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def _init_stats(self) -> None:
        for key in ["dusty", "scratched", "heavy", "placed", "blocked"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "confusion", "worry", "trust", "joy", "pride", "lesson"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str = "the construction site"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LessonGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    mentor: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        ent._init_stats()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SITE = Site(place="the construction site", affords={"lift", "paint", "measure"})

ACTIVITIES = {
    "lift": Activity(
        id="lift",
        verb="lift the beam",
        gerund="lifting the beam",
        rush="rush to lift the beam",
        risk="crush the plan",
        mess="dusty",
        zone={"hands", "torso"},
        keyword="technique",
        tags={"construction", "dust", "technique", "five"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint the warning lines",
        gerund="painting the warning lines",
        rush="dash to the paint tray",
        risk="smudge the fresh mark",
        mess="painted",
        zone={"hands"},
        keyword="five",
        tags={"construction", "paint", "technique", "five"},
    ),
    "measure": Activity(
        id="measure",
        verb="measure the frame",
        gerund="measuring the frame",
        rush="hurry to the tape line",
        risk="mix up the numbers",
        mess="scratched",
        zone={"hands", "torso"},
        keyword="technique",
        tags={"construction", "measure", "technique"},
    ),
}

PRIZES = {
    "vest": {
        "label": "safety vest",
        "phrase": "a bright safety vest",
        "region": "torso",
        "plural": False,
        "genders": {"girl", "boy"},
    },
    "gloves": {
        "label": "work gloves",
        "phrase": "a pair of work gloves",
        "region": "hands",
        "plural": True,
        "genders": {"girl", "boy"},
    },
    "helmet": {
        "label": "hard hat",
        "phrase": "a sturdy hard hat",
        "region": "head",
        "plural": False,
        "genders": {"girl", "boy"},
    },
}

GEAR = [
    LessonGear(
        id="dust_mask",
        label="a dust mask",
        covers={"nose", "mouth"},
        guards={"dusty"},
        prep="put on a dust mask first",
        tail="slipped on the dust mask",
    ),
    LessonGear(
        id="work_gloves",
        label="work gloves",
        covers={"hands"},
        guards={"dusty", "painted", "scratched"},
        prep="pull on work gloves first",
        tail="pulled on the work gloves",
        plural=True,
    ),
    LessonGear(
        id="vest",
        label="a safety vest",
        covers={"torso"},
        guards={"dusty", "painted"},
        prep="zip up a safety vest first",
        tail="zipped up the safety vest",
    ),
]

GIRL_NAMES = ["Mia", "Nia", "Ava", "Zara", "Lina", "Iris"]
BOY_NAMES = ["Kai", "Leo", "Noah", "Milo", "Eli", "Rex"]
TRAITS = ["curious", "brave", "careful", "eager", "spirited"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: dict) -> bool:
    return prize["region"] in activity.zone


def select_gear(activity: Activity, prize: dict) -> Optional[LessonGear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize["region"] in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for act_id, act in ACTIVITIES.items():
        for prize_id, prize in PRIZES.items():
            if prize_at_risk(act, prize) and select_gear(act, prize):
                out.append((act_id, prize_id))
    return out


def explain_rejection(activity: Activity, prize: dict) -> str:
    return (
        f"(No story: {activity.gerund} does not have a compatible gear fix for "
        f"the {prize['label']}. The misunderstanding needs a real, solvable risk.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R).
fix(A,P) :- prize_at_risk(A,P), gear(G), region(P,R), covers(G,R), mess(A,M), guards(G,M).
valid(A,P) :- prize_at_risk(A,P), fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p["region"]))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


# ---------------------------------------------------------------------------
# Narrative world
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    if narrate:
        world.say(f"{actor.id} started {activity.gerund}.")


def _dust_problem(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["dusty"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("dust", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] += 1
            out.append(f"{item.label} picked up dust from the work.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _dust_problem(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_line(site: Site) -> str:
    return f"The construction site looked like a launch deck for a big mission."


def introduce(world: World, hero: Entity, mentor: Entity) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes.get('traits', ['curious']) if t)} helper "
        f"who loved missions with bolts, beams, and careful hands."
    )
    world.say(
        f"{mentor.id} said the job called for {world.facts['activity'].keyword} five, "
        f"which sounded like a secret space-code to {hero.id}."
    )


def misunderstanding(world: World, hero: Entity, mentor: Entity, activity: Activity) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} thought {mentor.id} meant to take five and stop working."
    )
    world.say(
        f"Instead of waiting for the proper step, {hero.id} tried to {activity.rush}."
    )


def warning(world: World, mentor: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"{mentor.id} pointed at the {prize.label} and said, "
        f'"That was not what I meant. Technique Five means five careful points, not a break."'
    )
    hero.memes["worry"] += 1


def lesson(world: World, mentor: Entity, hero: Entity, activity: Activity, gear: LessonGear) -> None:
    hero.memes["lesson"] += 1
    world.say(
        f"{mentor.id} showed {hero.id} the lesson: check the signal, ask if it sounds odd, "
        f"and use the safe gear before the next lift."
    )
    world.say(
        f"{hero.id} nodded and said the words back like a tiny captain learning a new star-map."
    )


def accept_fix(world: World, hero: Entity, mentor: Entity, gear: LessonGear, activity: Activity, prize: Entity) -> None:
    hero.memes["confusion"] = 0
    hero.memes["trust"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} {gear.tail}, then did {activity.gerund} the right way."
    )
    world.say(
        f"With the {gear.label} on, the {prize.label} stayed clean, the beam settled safely, "
        f"and the crew cheered the happy ending."
    )


def tell(site: Site, activity: Activity, prize_cfg: dict, hero_name: str, hero_gender: str,
         mentor_name: str, trait: str) -> World:
    world = World(site)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, memes={"traits": [trait]}))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="adult", label="the foreman"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg["label"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        region=prize_cfg["region"],
        plural=prize_cfg["plural"],
        owner=hero.id,
        caretaker=mentor.id,
    ))
    hero.worn_by = None
    prize.worn_by = hero.id

    world.say(setting_line(site))
    world.say(
        f"{hero.id} wore {prize_cfg['phrase']} and listened for commands from {mentor.id}."
    )
    world.say(
        f"{hero.id} loved the site because every beam and ladder felt like part of a grand rocket build."
    )
    world.para()
    world.say(
        f"Then {mentor.id} called out, 'Technique Five!'"
    )
    misunderstanding(world, hero, mentor, activity)
    world.say(
        f"The mistake made the work wobble, and that worried the crew."
    )
    warning(world, mentor, hero, prize, activity)
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize_cfg))
    lesson(world, mentor, hero, activity, gear)
    world.para()
    world.say(
        f"{hero.id} chose the safe tool and tried again, this time with patience instead of haste."
    )
    hero.worn_by = hero.id
    gear_ent = world.add(Entity(
        id=gear.id, kind="thing", type="gear", label=gear.label, protective=True,
        covers=set(gear.covers), plural=gear.plural, owner=hero.id
    ))
    gear_ent.worn_by = hero.id
    propagate(world, narrate=False)
    accept_fix(world, hero, mentor, gear, activity, prize)

    world.facts.update(hero=hero, mentor=mentor, prize=prize, activity=activity, gear=gear, site=site)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "construction": [
        ("What happens at a construction site?",
         "A construction site is a place where people build, measure, lift, and make new things with tools and teamwork.")
    ],
    "technique": [
        ("What is a technique?",
         "A technique is a method or a careful way of doing something so it works better or safer.")
    ],
    "five": [
        ("What does the number five look like?",
         "Five is the number after four and before six.")
    ],
    "dust": [
        ("Why do people wear a dust mask?",
         "People wear a dust mask to help keep tiny bits of dust out of their nose and mouth.")
    ],
    "vest": [
        ("What is a safety vest for?",
         "A safety vest helps people be seen more easily while they work.")
    ],
    "gloves": [
        ("Why wear work gloves?",
         "Work gloves help protect hands from rough materials, dust, and scratches.")
    ],
}

KNOWLEDGE_ORDER = ["construction", "technique", "five", "dust", "vest", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short story for a young child about a construction site, the phrase "Technique Five", and a misunderstanding that turns into a lesson learned.',
        f"Tell a space-adventure style story where {f['hero'].id} misunderstands a command at the construction site, then learns the safe way to help.",
        f'Write a happy-ending story that includes the words "technique" and "five" and shows how a helper fixes a mistake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mentor: Entity = f["mentor"]
    prize: Entity = f["prize"]
    activity: Activity = f["activity"]
    gear: LessonGear = f["gear"]

    return [
        QAItem(
            question=f"Why did {hero.id} make the wrong choice when {mentor.id} said Technique Five?",
            answer=f"{hero.id} misunderstood the words and thought {mentor.id} meant to take five and stop working, instead of using the careful five-step technique.",
        ),
        QAItem(
            question=f"What lesson did {mentor.id} teach {hero.id} at the construction site?",
            answer=f"{mentor.id} taught {hero.id} to check the signal, ask when a command sounds odd, and use the safe gear before trying again.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {prize.label}?",
            answer=f"It ended happily. {hero.id} used {gear.label}, did {activity.gerund} the right way, and the {prize.label} stayed clean while the crew cheered.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        memes = {k: v for k, v in e.memes.items() if v and k != "traits"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id]["genders"]))
    return f"(No story: a {PRIZES[prize_id]['label']} isn't a typical {gender}'s item here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A construction-site storyworld about Technique Five, misunderstanding, and a happy lesson learned."
    )
    ap.add_argument("--place", choices=["site"], help="story location pin")
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=["foreman", "builder"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize]["genders"]:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        (a, p)
        for a, p in valid_combos()
        if (args.activity is None or a == args.activity)
        and (args.prize is None or p == args.prize)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or "foreman"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place="site",
        activity=activity,
        prize=prize,
        name=name,
        gender=gender,
        mentor=mentor,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SITE, ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, "the foreman", params.trait)
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
    StoryParams(place="site", activity="lift", prize="vest", name="Nia", gender="girl", mentor="foreman", trait="curious"),
    StoryParams(place="site", activity="paint", prize="gloves", name="Kai", gender="boy", mentor="foreman", trait="careful"),
    StoryParams(place="site", activity="measure", prize="helmet", name="Mia", gender="girl", mentor="foreman", trait="spirited"),
]


def asp_verify_report() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify_report())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible combos:")
        for a, p in sorted(set(asp.atoms(model, "valid"))):
            print(f"  {a:8} {p}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at the site (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
