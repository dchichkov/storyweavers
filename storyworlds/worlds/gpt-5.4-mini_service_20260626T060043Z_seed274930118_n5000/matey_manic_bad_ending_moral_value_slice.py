#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/matey_manic_bad_ending_moral_value_slice.py
==============================================================================================================

A small slice-of-life storyworld about a child, a shared task, a manic rush,
and a bad ending that still leaves behind a moral value.

Premise:
- A child wants to finish a simple after-school activity right away.
- A matey helper tries to be friendly and keep things calm.
- The child becomes manic, rushes the task, and ruins the shared setup.
- Nobody gets hurt, but the finished result is bad: the treat is wasted and
  the room needs cleanup.
- The moral value is that patience and listening keep small daily life things
  from going wrong.

This world is intentionally small and constraint-checked. It supports:
- prose generation
- story QA
- world knowledge QA
- trace mode
- JSON output
- ASP parity verification
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
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
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.weather = self.weather
        return c


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


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"snack", "tea"}),
    "porch": Setting(place="the porch", indoor=False, affords={"snack"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="share the snack",
        gerund="sharing the snack",
        rush="grab the plate all at once",
        mess="crumbled",
        soil="crumbled and spilled",
        keyword="snack",
        tags={"food", "share"},
    ),
    "tea": Activity(
        id="tea",
        verb="pour the tea",
        gerund="pouring tea",
        rush="tip the cup too fast",
        mess="spilled",
        soil="spilled across the table",
        keyword="tea",
        tags={"drink", "spill"},
    ),
}

PRIZES = {
    "cookies": Prize(
        label="cookies",
        phrase="a small plate of iced cookies",
        type="cookies",
        region="table",
        plural=True,
    ),
    "juice": Prize(
        label="juice",
        phrase="a full cup of juice",
        type="juice",
        region="table",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a wide tray",
        guards={"spilled", "crumbled"},
        prep="put the snack on a wide tray first",
        tail="used the wide tray to carry everything slowly",
    ),
    Gear(
        id="napkin",
        label="a stack of napkins",
        guards={"crumbled"},
        prep="put down a stack of napkins first",
        tail="laid down the napkins and moved carefully",
    ),
]

GIRL_NAMES = ["Mina", "Lila", "Nora", "Elsie", "June", "Ada"]
BOY_NAMES = ["Toby", "Eli", "Finn", "Milo", "Owen", "Theo"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]
TRAITS = ["patient", "curious", "cheerful", "restless", "gentle"]

CURATED = [
    StoryParams(place="kitchen", activity="snack", prize="cookies", name="Mina", gender="girl", helper="mother", trait="restless"),
    StoryParams(place="kitchen", activity="tea", prize="juice", name="Theo", gender="boy", helper="father", trait="curious"),
    StoryParams(place="porch", activity="snack", prize="cookies", name="Lila", gender="girl", helper="grandmother", trait="cheerful"),
]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "table"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards:
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


def activity_detail(activity: Activity) -> str:
    return {
        "snack": "The snack smelled sweet, and the icing looked bright and shiny.",
        "tea": "The tea steamed softly, and the cup was warm in tiny hands.",
    }[activity.id]


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str,
         helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"joy": 0.0, "haste": 0.0, "moral": 0.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}", meters={}, memes={"calm": 1.0}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=helper.id))
    gear_def = select_gear(activity, prize_cfg)
    if gear_def is None:
        raise StoryError("No reasonable gear exists for this combination.")

    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id))
    gear.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} little {gender} who liked quiet after-school moments.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} with {hero.pronoun('possessive')} {prize.label}.")
    world.say(f"{helper.label} was being {gear_def.label if False else 'matey'} and tried to help without making a fuss.")
    world.say(activity_detail(activity))
    world.para()

    world.say(f"One afternoon, {hero.id} and {helper.label} sat down in {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} hands moved in a manic hurry.")
    hero.memes["haste"] += 1.0
    hero.memes["moral"] += 0.0
    world.say(f'"Wait," said {helper.label}, "let\'s {gear_def.prep}."')
    world.say(f'But {hero.id} tried to {activity.rush}, and the {prize.label} got {activity.soil}.')
    prize.meters["dirty"] = 1.0
    hero.meters[activity.mess] = 1.0
    world.para()

    world.say(f"{helper.label} sighed and started cleaning the mess while the snack sat ruined.")
    helper.meters["cleanup"] = 1.0
    hero.memes["sad"] = 1.0
    hero.memes["moral"] = 1.0
    world.say(f"{hero.id} looked at the broken little scene and learned that patience matters more than a fast finish.")
    world.say(f"The bad ending was simple: the snack was wasted, the room was messy, and the moment was gone.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        trait=trait,
        bad_ending=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, prize = f["hero"], f["helper"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story for young children that uses the words "matey" and "manic".',
        f"Tell a gentle but bad-ending story where {hero.id} tries to {act.verb} with {prize.label} and {helper.label} tries to help.",
        f"Write a small everyday story that ends with a moral about patience after a messy mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {f['trait']} {hero.type}, and {helper.label}, who tried to help.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {prize.label}?",
            answer=f"{hero.id} wanted to {act.verb}, but {hero.pronoun('possessive')} hurry turned manic and caused trouble.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer="The snack was ruined, the room got messy, and everyone had to clean up instead of enjoying the treat.",
        ),
        QAItem(
            question=f"What moral value does the story leave behind?",
            answer="The story shows that patience and listening are important when you are doing small everyday tasks.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does patience mean?",
            answer="Patience means waiting calmly and not rushing when something takes a little time.",
        ),
        QAItem(
            question="What does messy food need after it spills?",
            answer="Messy food needs to be cleaned up so the table and floor are safe and neat again.",
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: this combination does not create a believable mess for the {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not set up for {gender} in this world.)"


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


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P).
has_fix(A,P) :- prize_at_risk(A,P), activity(A), prize(P), gear(G), guards(G,M), mess_of(A,M).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""

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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a bad ending and a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.helper, params.trait)
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
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:8} {prize:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
