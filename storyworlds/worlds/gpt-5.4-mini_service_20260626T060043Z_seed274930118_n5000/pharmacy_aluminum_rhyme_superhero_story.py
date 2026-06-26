#!/usr/bin/env python3
"""
storyworlds/worlds/pharmacy_aluminum_rhyme_superhero_story.py
=============================================================

A small superhero-flavored story world with a pharmacy setting, an aluminum
object, and a rhyme-based turn toward helping instead of rushing.

Premise:
- A child hero loves acting like a superhero.
- A pharmacy is full of shiny, careful things.
- A light aluminum item is at risk if the hero blasts around too hard.

Tension:
- The hero wants to swoop, stomp, and shout in rhyme.
- The caretaker warns that loud, clumsy play could knock over medicine or bend
  the aluminum item.

Turn:
- The hero learns to use a softer superhero move: a careful rhyme, a tidy
  rescue, and a gentle carry.

Resolution:
- The aluminum item stays safe, the pharmacy stays neat, and the hero still
  gets to feel brave.

This script follows the storyworld contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of storyworlds.asp inside ASP helpers
- StoryParams / registries / build_parser / resolve_params / generate / emit / main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the pharmacy"
    indoors: bool = True
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
    rhyme: str
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
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "pharmacy": Setting(place="the pharmacy", indoors=True, affords={"rhyme", "carry", "help"}),
}

ACTIVITIES = {
    "rhyme": Activity(
        id="rhyme",
        verb="speak in a brave rhyme",
        gerund="speaking in brave rhyme",
        rush="dash between the shelves",
        mess="jostled",
        soil="knocked crooked",
        zone={"hands", "torso"},
        rhyme="shine",
        keyword="rhyme",
        tags={"rhyme", "hero", "speech"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the shiny tray",
        gerund="carrying the shiny tray",
        rush="rush through the aisle",
        mess="jostled",
        soil="spilled",
        zone={"hands"},
        rhyme="glow",
        keyword="carry",
        tags={"hero", "care"},
    ),
    "help": Activity(
        id="help",
        verb="help the pharmacist sort bottles",
        gerund="helping sort bottles",
        rush="swing a cape too fast",
        mess="jostled",
        soil="tipped",
        zone={"hands", "torso"},
        rhyme="bright",
        keyword="help",
        tags={"hero", "help", "care"},
    ),
}

PRIZES = {
    "aluminum_tray": Prize(
        label="aluminum tray",
        phrase="a light aluminum tray",
        type="tray",
        region="hands",
    ),
    "aluminum_box": Prize(
        label="aluminum box",
        phrase="a small aluminum box",
        type="box",
        region="hands",
    ),
    "medicine_cart": Prize(
        label="medicine cart",
        phrase="a neat medicine cart",
        type="cart",
        region="hands",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"jostled"},
        prep="put on soft gloves first",
        tail="slipped on the soft gloves and moved like a careful hero",
        plural=True,
    ),
    Gear(
        id="apron",
        label="a tidy apron",
        covers={"torso"},
        guards={"jostled"},
        prep="tie on a tidy apron first",
        tail="tied on the tidy apron and stood straight like a true helper",
    ),
    Gear(
        id="gloves_and_apron",
        label="soft gloves and a tidy apron",
        covers={"hands", "torso"},
        guards={"jostled"},
        prep="put on soft gloves and tie on a tidy apron",
        tail="put on the soft gloves and the tidy apron and got ready to help",
        plural=True,
    ),
]

GIRL_NAMES = ["Ada", "Mina", "Luna", "Zoe", "Nina"]
BOY_NAMES = ["Max", "Kai", "Leo", "Toby", "Finn"]
TRAITS = ["brave", "bright", "spry", "quick", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.memes["bold"] = actor.memes.get("bold", 0.0) + 1
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} moved in {activity.rhyme} rhythm.")


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get(activity.mess, 0.0) >= THRESHOLD}


def hero_intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'brave')} hero who loved to "
        f"help where the shelves shone."
    )


def loves_place(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved the pharmacy because every bottle, box, "
        f"and bright sign felt like a chance to do good."
    )
    world.say(
        f"{hero.pronoun().capitalize()} also liked to {activity.verb}, and the little "
        f"rhyme made the whole day feel like a rescue."
    )


def set_up(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id} and {helper.label} came to {world.setting.place}. "
        f"{hero.id} wore a tiny cape, and {prize.phrase} gleamed on the counter."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["warned"] = True
    world.say(
        f'"Careful," {helper.label} said. "If you {activity.verb}, you may get that '
        f"{prize.label} {activity.soil}.""
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(
        f"{hero.id} still wanted to be a splashy superhero and tried to {activity.rush}."
    )


def offer_fix(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        return None
    world.say(
        f'{helper.label} smiled and said, "How about we {gear.prep} and then {activity.verb}?"'
    )
    return gear


def accept(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"{hero.id} nodded, put on the gear, and felt brave in a quieter way. "
        f'Then {hero.id} said, "{activity.rhyme}, no bump, no thump, just help with a jump!"'
    )
    world.say(
        f"At the end, {hero.id} was {activity.gerund}, {prize.label} stayed safe, and "
        f"{helper.label} laughed because the little rhyme worked."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         helper_type: str = "pharmacist", hero_trait: str = "brave") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    hero.memes["trait"] = hero_trait
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the pharmacist"))
    prize = world.add(Entity(
        id=prize_cfg.label.replace(" ", "_"),
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        region=prize_cfg.region,
        caretaker=helper.id,
        owner=helper.id,
    ))

    hero_intro(world, hero)
    loves_place(world, hero, activity)
    set_up(world, hero, helper, prize)

    world.para()
    warn(world, helper, hero, activity, prize)
    defy(world, hero, activity)

    world.para()
    gear = offer_fix(world, helper, hero, activity, prize)
    if gear:
        accept(world, hero, helper, activity, prize, gear)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=setting,
    )
    return world


KNOWLEDGE = {
    "pharmacy": [
        (
            "What is a pharmacy?",
            "A pharmacy is a place where people get medicine and talk with a pharmacist about staying well.",
        )
    ],
    "aluminum": [
        (
            "What is aluminum?",
            "Aluminum is a light, shiny metal that is often used for trays, cans, and boxes.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound the same at the end, like shine and fine, or bright and light.",
        )
    ],
    "hero": [
        (
            "What does a superhero try to do?",
            "A superhero tries to help others, solve problems, and stay brave even when the job is tricky.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, prize = f["hero"], f["helper"], f["activity"], f["prize"]
    return [
        f'Write a short superhero story for a young child that includes the word "{act.keyword}" and the word "pharmacy".',
        f"Tell a rhyme-filled story where {hero.id} wants to {act.verb} near {prize.label} but {helper.label} asks for a safer way.",
        f"Write a gentle superhero tale about an aluminum item in a pharmacy, and end with a happy helper plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who wanted to act like a superhero in the pharmacy?",
            answer=f"{hero.id} wanted to act like a superhero in the pharmacy, with {helper.label} nearby.",
        ),
        QAItem(
            question=f"What shiny thing could get damaged if {hero.id} was too rough?",
            answer=f"{prize.phrase} could get {act.soil} if {hero.id} was too rough.",
        ),
        QAItem(
            question=f"What did {helper.label} ask {hero.id} to do instead of rushing?",
            answer=f"{helper.label} asked {hero.id} to slow down, use a safer plan, and help carefully.",
        ),
    ]
    if f.get("gear") is not None:
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did the safety gear help the superhero plan?",
                answer=f"The {gear.label} helped {hero.id} move carefully so {prize.label} stayed safe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags)
    tags.add("pharmacy")
    tags.add("aluminum")
    if world.facts.get("gear"):
        tags.add("hero")
    for tag in ["pharmacy", "aluminum", "rhyme", "hero"]:
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="pharmacy", activity="rhyme", prize="aluminum_tray", name="Mina", gender="girl", helper="pharmacist", trait="brave"),
    StoryParams(place="pharmacy", activity="carry", prize="aluminum_box", name="Max", gender="boy", helper="pharmacist", trait="bright"),
    StoryParams(place="pharmacy", activity="help", prize="medicine_cart", name="Luna", gender="girl", helper="pharmacist", trait="cheerful"),
]


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), region(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), guards(G, M), mess(A, M), covers(G, R), region(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""



def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: pharmacy, aluminum, rhyme, superhero style.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", default="pharmacist")
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    helper = args.helper or "pharmacist"
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, "girl" if params.gender == "girl" else "boy", params.helper, params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in combos:
            print(f"  {place:10} {act:8} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
