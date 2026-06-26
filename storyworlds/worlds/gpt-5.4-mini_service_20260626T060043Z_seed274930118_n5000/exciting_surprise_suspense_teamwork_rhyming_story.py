#!/usr/bin/env python3
"""
storyworlds/worlds/exciting_surprise_suspense_teamwork_rhyming_story.py
=======================================================================

A small standalone story world for an exciting rhyming-style tale with
surprise, suspense, and teamwork.

Seed tale:
---
A tiny team wants to make a surprise treat for a friend.
A wobbly tray nearly spills the prize, but the helpers work together.
They steady the load, finish the surprise, and reveal it with joy.
---

World idea:
- Two friends prepare a surprise gift in a cozy place.
- Suspense comes from a risky carry or hide-and-seek moment.
- Teamwork solves the problem with a shared method.
- The ending proves the surprise stayed safe and the friends succeeded.

The prose aims for a child-facing, lightly rhyming rhythm without forcing
unreadable verse.
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
    helper: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


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
    risk: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    fragile: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


SETTINGS = {
    "kitchen": Setting(place="the cozy kitchen", indoor=True, affords={"bake", "carry"}),
    "workshop": Setting(place="the little workshop", indoor=True, affords={"build", "carry"}),
    "garden": Setting(place="the garden shed", indoor=False, affords={"carry", "hide"}),
}

ACTIVITIES = {
    "bake": Activity(
        id="bake",
        verb="bake the surprise treat",
        gerund="baking a surprise treat",
        rush="hurry to the oven",
        risk="the pan could wobble and spill",
        weather="",
        keyword="surprise",
        tags={"surprise", "suspense", "teamwork", "baking"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the surprise to the table",
        gerund="carrying the surprise together",
        rush="dash with the tray",
        risk="the tray could tilt and tumble",
        weather="",
        keyword="teamwork",
        tags={"surprise", "suspense", "teamwork", "carry"},
    ),
    "build": Activity(
        id="build",
        verb="build the surprise sign",
        gerund="building a bright surprise sign",
        rush="rush with the boards",
        risk="the sign could slip and clatter",
        weather="",
        keyword="surprise",
        tags={"surprise", "teamwork", "craft"},
    ),
    "hide": Activity(
        id="hide",
        verb="hide the surprise near the door",
        gerund="hiding the surprise by the door",
        rush="scurry to cover it",
        risk="someone could spot it too soon",
        weather="",
        keyword="surprise",
        tags={"surprise", "suspense", "teamwork", "hide"},
    ),
}

PRIZES = {
    "cake": Prize(
        label="cake",
        phrase="a sweet birthday cake",
        type="cake",
        fragile=True,
    ),
    "sign": Prize(
        label="sign",
        phrase="a bright handmade sign",
        type="sign",
        fragile=True,
    ),
    "gift": Prize(
        label="gift",
        phrase="a wrapped surprise gift",
        type="gift",
        fragile=True,
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a sturdy tray",
        prep="use a sturdy tray together",
        tail="held the tray level with careful hands",
        guards={"bake", "carry"},
    ),
    Gear(
        id="sheet",
        label="a wide baking sheet",
        prep="slide it onto a wide baking sheet",
        tail="moved in one slow, steady line",
        guards={"bake"},
    ),
    Gear(
        id="cloth",
        label="a soft cloth",
        prep="cover it with a soft cloth",
        tail="kept the surprise snug and hidden",
        guards={"hide", "carry"},
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Sam"]
TRAITS = ["brave", "bright", "cheery", "quick", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if act_id == "bake" and prize_id != "cake":
                    continue
                if act_id == "build" and prize_id != "sign":
                    continue
                if act_id == "hide" and prize_id != "gift":
                    continue
                if act_id == "carry" and prize_id not in {"cake", "gift", "sign"}:
                    continue
                combos.append((place, act_id, prize_id))
    return combos


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
    if activity.id == "bake":
        return prize.label == "cake"
    if activity.id == "build":
        return prize.label == "sign"
    if activity.id == "hide":
        return prize.label == "gift"
    if activity.id == "carry":
        return True
    return False


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.id in gear.guards:
            if activity.id == "bake" and gear.id in {"tray", "sheet"}:
                return gear
            if activity.id == "carry" and gear.id in {"tray", "cloth"}:
                return gear
            if activity.id == "build" and gear.id == "tray":
                return gear
            if activity.id == "hide" and gear.id == "cloth":
                return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} and {prize.label} do not make a reasonable pair "
        f"for this tiny world, so the surprise would not have a fair suspenseful turn.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: this {PRIZES[prize_id].label} is not a typical {gender}'s choice here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Exciting surprise suspense teamwork rhyming story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.memes["excited"] = actor.memes.get("excited", 0) + 1
    if narrate:
        world.say(f"{actor.id} set to work with a grin so bright, ready for a rhyming little flight.")


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return True if prize else False


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str,
         hero_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy" if hero_type == "girl" else "girl"))
    prize = world.add(Entity(id=prize_cfg.type, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))

    gear_def = select_gear(activity, prize_cfg)
    gear = world.add(Entity(id=gear_def.id if gear_def else "gear", type="gear", label=gear_def.label if gear_def else "gear", protective=True)) if gear_def else None

    world.say(f"{hero.id} was a {trait} little {hero_type}, quick with a smile and nimble with a style.")
    world.say(f"{helper.id} came along with a cheerful song, and together they planned something bright and strong.")
    world.say(f"They wanted {activity.verb}, a surprise that would shine, for a friend at {setting.place} in gentle design.")

    world.para()
    world.say(f"At {setting.place}, the air felt still, yet their hearts beat fast with a merry thrill.")
    world.say(f"{hero.id} and {helper.id} began to {activity.gerund}, and {activity.risk}.")
    if gear_def:
        world.say(f"So they chose {gear_def.label} and worked in tandem, with matching steps and a careful rhythm.")
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg, activity=activity, gear=gear, setting=setting)

    world.para()
    world.say(f"There came a small gasp and a suspenseful pause; the load tipped a little, as loads sometimes cause.")
    world.say(f"But teamwork came racing, no time to waste, for the surprise had to stay safe and nicely placed.")
    if gear_def:
        world.say(f"{gear_def.tail.capitalize()}, and the wobble gave way to a calmer sway.")
    world.say(f"Then with one last measure and a happy cheer, they set the surprise down neat and clear.")

    world.para()
    world.say(f"The friend came in laughing, eyes wide with delight, and the room felt cozy and sparkly and light.")
    world.say(f"It was an exciting surprise, with suspense turned to cheer; the teamwork had brought the sweet finish near.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about {f["hero"].id} and {f["helper"].id} making a surprise {f["prize"].label}.',
        f"Tell a gentle suspense story where two helpers use teamwork so their {f['activity'].verb} stays safe.",
        f'Write an exciting surprise tale in a cozy setting that ends with a happy reveal and a little rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, activity = f["hero"], f["helper"], f["prize"], f["activity"]
    setting = f["setting"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who were the two helpers in the story?",
            answer=f"The two helpers were {hero.id} and {helper.id}. They worked together from start to finish.",
        ),
        QAItem(
            question=f"What were {hero.id} and {helper.id} making at {setting.place}?",
            answer=f"They were making {prize.phrase} as a surprise, and they wanted it to stay neat until the reveal.",
        ),
        QAItem(
            question=f"What made the middle of the story suspenseful?",
            answer=f"The suspense came when the load tipped a little and everyone worried it might spill or slip.",
        ),
        QAItem(
            question=f"How did teamwork help the surprise?",
            answer=f"Teamwork helped because {hero.id} and {helper.id} shared the load, used {gear.label if gear else 'their careful hands'}, and kept the surprise safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the surprise finished, the friend smiling, and the helpers feeling proud and happy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does teamwork mean?", answer="Teamwork means people work together and help each other finish a job."),
        QAItem(question="What is a surprise?", answer="A surprise is something you do not expect until it is shown or revealed."),
        QAItem(question="What is suspense?", answer="Suspense is the feeling of wondering what will happen next."),
    ]


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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="bake", prize="cake", name="Mia", gender="girl", helper="Leo", trait="bright"),
    StoryParams(place="workshop", activity="build", prize="sign", name="Ben", gender="boy", helper="Ava", trait="gentle"),
    StoryParams(place="garden", activity="hide", prize="gift", name="Nora", gender="girl", helper="Sam", trait="cheery"),
    StoryParams(place="kitchen", activity="carry", prize="cake", name="Theo", gender="boy", helper="Lily", trait="quick"),
]


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), pair(A,P).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), fits(G,A).
valid(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
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
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        for g in sorted(PRIZES[pid].genders):
            lines.append(asp.fact("wears", g, pid))
    for a, p in [("bake", "cake"), ("build", "sign"), ("hide", "gift"), ("carry", "cake"), ("carry", "sign"), ("carry", "gift")]:
        lines.append(asp.fact("pair", a, p))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.guards):
            lines.append(asp.fact("fits", g.id, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_asp_python() -> tuple[set[tuple], set[tuple]]:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    return py, cl


def asp_verify() -> int:
    py, cl = valid_asp_python()
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.helper, params.gender, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
