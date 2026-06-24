#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/dime_fray_indoor_play_cafe_happy_ending.py
=====================================================================================================================

A small slice-of-life storyworld set in an indoor play cafe.

Premise:
- A child arrives at an indoor play cafe with a pocket dime.
- They want a small treat or game token, but a tiny fray in a soft item
  threatens the fun.
- A caregiver notices the problem, helps with a gentle fix, and the child
  learns to be careful with small things.

Story instruments:
- Happy Ending: the item is repaired and the child keeps enjoying play.
- Lesson Learned: the child remembers a careful habit for next time.
- Bad Ending: the fray wins, the dime is spent on a disappointing fix, or
  the play outing ends early.

This file follows the Storyweavers storyworld contract with a Python reasonableness
gate plus an inline ASP twin.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the indoor play cafe"
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
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    fix: str
    name: str
    gender: str
    parent: str
    trait: str
    ending: str
    seed: Optional[int] = None


SETTINGS = {
    "cafe": Setting(place="the indoor play cafe", indoor=True, affords={"snack", "craft", "tunnel"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="buy a sweet snack",
        gerund="buying a sweet snack",
        rush="rush toward the counter",
        mess="sticky",
        soil="sticky and torn",
        keyword="snack",
        tags={"food", "sticky"},
    ),
    "craft": Activity(
        id="craft",
        verb="make a paper crown",
        gerund="making paper crowns",
        rush="reach for the glitter jar",
        mess="torn",
        soil="a little torn",
        keyword="craft",
        tags={"paper", "torn"},
    ),
    "tunnel": Activity(
        id="tunnel",
        verb="crawl through the play tunnel",
        gerund="crawling through the play tunnel",
        rush="dash into the tunnel",
        mess="frayed",
        soil="frayed and tired",
        keyword="tunnel",
        tags={"soft", "fray"},
    ),
}

PRIZES = {
    "dime": Prize(label="dime", phrase="a shiny dime", type="coin"),
    "sticker": Prize(label="sticker sheet", phrase="a bright sticker sheet", type="stickers"),
    "bandana": Prize(label="bandana", phrase="a soft striped bandana", type="bandana"),
}

FIXES = [
    Fix(id="patch", label="a small patch kit", prep="use a small patch kit", tail="patched the fray carefully", helps={"frayed", "torn"}),
    Fix(id="tape", label="clear tape", prep="use clear tape", tail="smoothed the loose edge down", helps={"frayed", "torn"}),
    Fix(id="wipe", label="a damp cloth", prep="wipe the sticky spot clean", tail="made the item ready again", helps={"sticky"}),
]

GIRL_NAMES = ["Mia", "Lena", "Tia", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Kai", "Finn", "Theo", "Max"]
TRAITS = ["curious", "gentle", "cheerful", "patient", "bright"]


def reasonableness_gate(activity: Activity, prize: Prize, ending: str) -> bool:
    if ending not in {"happy", "lesson", "bad"}:
        raise StoryError("ending must be happy, lesson, or bad")
    if activity.id == "tunnel" and prize.label != "dime":
        return True
    if activity.id == "snack" and prize.label in {"dime", "sticker sheet"}:
        return True
    if activity.id == "craft" and prize.label in {"sticker sheet", "bandana"}:
        return True
    return False


def select_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mess in fx.helps:
            return fx
    return None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.helps):
            lines.append(asp.fact("helps", fx.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
possible(A,P) :- activity(A), prize(P), mess_of(A,M), not blocked(A,P).
blocked(A,P) :- activity(A), prize(P), mess_of(A,M), A = snack, P = bandana.
blocked(A,P) :- activity(A), prize(P), mess_of(A,M), A = craft, P = dime.
blocked(A,P) :- activity(A), prize(P), mess_of(A,M), A = tunnel, P = bandana.
valid(A,P) :- possible(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for aid in s.affords:
            a = ACTIVITIES[aid]
            for pid, p in PRIZES.items():
                if reasonableness_gate(a, p, "happy"):
                    out.append((place, aid, pid))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["want"] = actor.memes.get("want", 0) + 1


def tell(setting: Setting, activity: Activity, prize: Prize, fix: Optional[Fix], params: StoryParams) -> World:
    w = World(setting)
    child = w.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent))
    coin = w.add(Entity(id="dime", type="dime", label="dime", phrase="a shiny dime", owner=child.id))
    prize_e = w.add(Entity(id="prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=child.id, caretaker=parent.id))
    w.facts.update(child=child, parent=parent, coin=coin, prize=prize_e, activity=activity, fix=fix, ending=params.ending)

    w.say(f"{child.id} went with {child.pronoun('possessive')} {parent.id} to {w.setting.place}.")
    w.say(f"In the pocket, {child.id} found {child.pronoun('possessive')} little dime and smiled.")
    w.say(f"{child.pronoun().capitalize()} wanted to {activity.verb}, because {activity.gerund} sounded like a fun afternoon.")

    w.para()
    w.say(f"Then {child.id} noticed a tiny fray near the edge of {prize.label}.")
    w.say(f"If {child.id} hurried too much, the {prize.label} could turn {activity.soil}.")
    if params.ending != "bad":
        w.say(f"{parent.pronoun().capitalize()} said they should slow down and choose a careful fix.")

    w.para()
    _do_activity(w, child, activity)
    if params.ending == "bad":
        w.say(f"But the fray kept getting worse, and the dime was spent on the wrong thing.")
        w.say(f"{child.id} left the cafe quiet and disappointed, holding {prize.label} that never felt quite right.")
    else:
        if fix:
            w.say(f"Together they decided to {fix.prep}.")
            w.say(f"That small choice {fix.tail}, and the dime stayed useful instead of being wasted.")
        if params.ending == "happy":
            w.say(f"After that, {child.id} went back to play, and the cafe felt bright again.")
            w.say(f"By the end, {prize.label} was fine, the dime was still a blessing, and the day ended with a grin.")
        else:
            w.say(f"{child.id} learned that small problems are easier to fix early.")
            w.say(f"By the end, the fray was neat, and {child.id} remembered to check things gently before rushing.")

    return w


def build_story(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    prize = PRIZES[params.prize]
    fix = select_fix(activity, prize)
    if not reasonableness_gate(activity, prize, params.ending):
        raise StoryError("that activity, prize, and ending do not make a believable small story")
    world = tell(setting, activity, prize, fix, params)
    prompts = [
        f"Write a slice-of-life story set in an indoor play cafe about a child, a dime, and a fray.",
        f"Tell a gentle story where {params.name} notices a fray and uses a small dime wisely.",
        f"Write a short indoor play cafe story with a happy ending, a lesson learned, or a bad ending.",
    ]
    story_qa = [
        QAItem(question=f"Where was {params.name}?", answer=f"{params.name} was at the indoor play cafe with {params.parent}."),
        QAItem(question=f"What small thing did {params.name} have?", answer=f"{params.name} had a shiny dime."),
        QAItem(question=f"What problem showed up?", answer=f"A tiny fray showed up on the prize item."),
    ]
    if params.ending == "happy":
        story_qa.append(QAItem(question="How did the story end?", answer="It ended happily because the problem was fixed and play could continue."))
    elif params.ending == "lesson":
        story_qa.append(QAItem(question="What did the child learn?", answer="The child learned to slow down and check small things before they got worse."))
    else:
        story_qa.append(QAItem(question="How did the story end?", answer="It ended badly because the fray and the wrong choice spoiled the outing."))
    world_qa = [
        QAItem(question="What is a dime?", answer="A dime is a small coin used as money."),
        QAItem(question="What is a fray?", answer="A fray is a little worn or loose place on fabric or string."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: indoor play cafe, dime, and fray.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--ending", choices=["happy", "lesson", "bad"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = args.place or "cafe"
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    ending = args.ending or rng.choice(["happy", "lesson", "bad"])
    prize = args.prize or rng.choice(sorted(PRIZES))
    if args.gender and args.name is None:
        name = rng.choice(GIRL_NAMES if args.gender == "girl" else BOY_NAMES)
    else:
        name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, activity=activity, prize=prize, fix="", name=name, gender=gender, parent=parent, trait=trait, ending=ending)
    activity_obj = ACTIVITIES[activity]
    prize_obj = PRIZES[prize]
    if not reasonableness_gate(activity_obj, prize_obj, ending):
        raise StoryError("No valid combination matches the given options.")
    return params


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = set(asp.atoms(model, "valid"))
    py_pairs = {(a, p) for _, a, p in py}
    if py_pairs == asp_set:
        print(f"OK: ASP matches Python gate ({len(py_pairs)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    return 1


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    pairs = asp.atoms(model, "valid")
    out = []
    for a, p in pairs:
        out.append(("cafe", a, p))
    return out


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for ending in ["happy", "lesson", "bad"]:
            params = StoryParams(
                place="cafe",
                activity="tunnel",
                prize="dime",
                fix="",
                name="Mia",
                gender="girl",
                parent="mother",
                trait="curious",
                ending=ending,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
