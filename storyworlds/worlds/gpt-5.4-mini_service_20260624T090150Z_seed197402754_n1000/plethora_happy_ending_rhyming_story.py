#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/plethora_happy_ending_rhyming_story.py
===============================================================================================================

A tiny storyworld for a rhyming, happy-ending tale about a child who meets a
plethora of something small and lovely, then learns a safer way to carry it.

The world model tracks:
- physical meters: fullness, spilled, tidy, and carried
- emotional memes: joy, worry, pride, and calm

The narrative is intentionally authored in a rhyming, child-facing style, while
still being driven by simulated state changes.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["fullness", "spilled", "tidy", "carried"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "calm", "disappointment"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    lighting: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    spill: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    plural: bool = False
    gets_full: str = "full"
    caretaker_need: str = "tidy"


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    protects: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.entities.values():
        if hero.kind != "character":
            continue
        for act in ACTIVITIES.values():
            if hero.meters[act.id] < THRESHOLD:
                continue
            prize = world.facts.get("prize")
            if not prize:
                continue
            if ("spill", hero.id, act.id) in world.fired:
                continue
            world.fired.add(("spill", hero.id, act.id))
            prize.meters["spilled"] += 1
            prize.memes["worry"] += 1
            out.append(f"The {prize.label} almost slipped with a little flip and flip.")
    return out


def _r_tidy(world: World) -> list[str]:
    out: list[str] = []
    prize = world.facts.get("prize")
    caretaker = world.facts.get("caretaker")
    if not prize or not caretaker:
        return out
    if prize.meters["spilled"] < THRESHOLD:
        return out
    if ("tidy", prize.id) in world.fired:
        return out
    world.fired.add(("tidy", prize.id))
    carer = world.get(caretaker.id)
    carer.meters["tidy"] += 1
    carer.memes["worry"] += 1
    out.append("That meant more tidy-up work for the grown-up nearby.")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_tidy,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return bool(activity.zone)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.id in g.guards and prize.id in g.protects:
            return g
    return None


def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    pr = sim.facts["prize"]
    return {"spilled": pr.meters["spilled"] >= THRESHOLD}


def rhyme_opening(hero: Entity, setting: Setting, activity: Activity, prize: Prize) -> None:
    world = CURRENT_WORLD
    world.say(
        f"Little {hero.id} by the {setting.place} side, "
        f"liked {activity.gerund} with a grin so wide."
    )
    world.say(
        f"{hero.id} had a {prize.phrase}, bright and neat, "
        f"and kept it close with careful feet."
    )


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError(f"This setting does not afford {activity.id}.")
    hero.meters[activity.id] += 1
    hero.meters["carried"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=narrate)


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One bright day with a sunny sway, {hero.id} and {parent.label} went out to play."
    )
    world.say(
        f"{hero.id} wanted to {activity.verb}, quick as a song, "
        f"but {parent.label} worried the load might go wrong."
    )


def warn(world: World, parent: Entity, hero: Entity, prize: Prize, activity: Activity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["spilled"]:
        return False
    world.facts["predicted_spill"] = True
    world.say(
        f"\"Careful, dear heart, that {prize.label} may flop,\" "
        f"said {parent.label}, \"and make quite a drop.\""
    )
    parent.memes["worry"] += 1
    hero.memes["worry"] += 1
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    hero.memes["disappointment"] += 1
    world.say(
        f"{hero.id} pouted a bit, then made a quick dash, "
        f"trying to {activity.rush} in a joyful splash."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Prize) -> Optional[Gear]:
    gear = select_gear(activity, prize)
    if gear is None:
        return None
    if predict_mess(world, hero, activity, prize.id)["spilled"]:
        return None
    g = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        protective=True,
        plural=gear.plural,
        owner=hero.id,
        caretaker=parent.id,
        covers=set(gear.protects),
    ))
    g.worn_by = hero.id
    world.say(
        f"Then {parent.label} smiled with a gentle spark, "
        f"and offered {gear.prep}, bright in the dark."
    )
    return gear


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Prize, gear: Gear) -> None:
    hero.memes["joy"] += 2
    hero.memes["calm"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} cheered, then hugged {parent.pronoun('object')} so tight, "
        f"\"That plan feels lovely! That plan feels right!\""
    )
    world.say(
        f"They {gear.tail}, and soon the day "
        f"was merry and safe in a rhyming way."
    )
    world.say(
        f"At story's end, the {prize.label} stayed neat, "
        f"and {hero.id} danced home with light little feet."
    )


SETTING = Setting(place="meadow", lighting="sunny", affords={"berries", "apples", "pearls"})
ACTIVITIES = {
    "berries": Activity(
        id="berries",
        verb="pick the berries",
        gerund="picking berries",
        rush="run to the berry patch",
        spill="spilled",
        zone={"hands", "basket"},
        keyword="berries",
        tags={"berries", "red"},
    ),
    "apples": Activity(
        id="apples",
        verb="gather apples",
        gerund="gathering apples",
        rush="dash to the apple tree",
        spill="spilled",
        zone={"hands", "basket"},
        keyword="apples",
        tags={"apples", "fruit"},
    ),
    "pearls": Activity(
        id="pearls",
        verb="sort the pearls",
        gerund="sorting pearls",
        rush="hurry to the shell pile",
        spill="spilled",
        zone={"hands", "basket"},
        keyword="pearls",
        tags={"pearls", "shiny"},
    ),
}

PRIZES = {
    "basket": Prize(
        id="basket",
        label="basket",
        phrase="woven basket",
        type="basket",
        plural=False,
    ),
    "jar": Prize(
        id="jar",
        label="jar",
        phrase="little glass jar",
        type="jar",
        plural=False,
    ),
    "pouch": Prize(
        id="pouch",
        label="pouch",
        phrase="tiny cloth pouch",
        type="pouch",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a sturdy tray",
        prep="put the berries in a sturdy tray first",
        tail="walked home with the tray held tight",
        guards={"berries", "apples"},
        protects={"basket", "jar"},
    ),
    Gear(
        id="cloth",
        label="a soft cloth",
        prep="spread a soft cloth first",
        tail="returned with the cloth held near",
        guards={"pearls"},
        protects={"pouch", "jar"},
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ella", "Zoe", "Ruby"]
BOY_NAMES = ["Finn", "Leo", "Toby", "Owen", "Max", "Noah"]
TRAITS = ["cheerful", "curious", "brave", "lively"]


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


CURRENT_WORLD: World


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld with a happy ending and a plethora of small delights.")
    ap.add_argument("--place", choices=[SETTING.place])
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
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
    combos = []
    for act in sorted(ACTIVITIES):
        for pr in sorted(PRIZES):
            if prize_at_risk(ACTIVITIES[act], PRIZES[pr]) and select_gear(ACTIVITIES[act], PRIZES[pr]):
                combos.append((SETTING.place, act, pr))
    if args.activity and args.prize:
        if (args.place or SETTING.place) != SETTING.place:
            raise StoryError("Only the meadow setting is available in this storyworld.")
        if not (prize_at_risk(ACTIVITIES[args.activity], PRIZES[args.prize]) and select_gear(ACTIVITIES[args.activity], PRIZES[args.prize])):
            raise StoryError("That activity and prize do not make a reasonable problem-and-fix pair.")
    filtered = [c for c in combos
                if (args.activity is None or c[1] == args.activity)
                and (args.prize is None or c[2] == args.prize)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    _, activity, prize = rng.choice(filtered)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=SETTING.place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    global CURRENT_WORLD
    world = World(SETTING)
    CURRENT_WORLD = world
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="grown-up"))
    prize = world.add(Entity(id="Prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=parent.id, plural=False))
    world.facts["hero"] = hero
    world.facts["caretaker"] = parent
    world.facts["prize"] = prize
    world.facts["activity"] = ACTIVITIES[params.activity]
    world.facts["params"] = params

    rhyme_opening(hero, SETTING, ACTIVITIES[params.activity], prize)
    world.para()
    arrive(world, hero, parent, ACTIVITIES[params.activity])
    warn(world, parent, hero, prize, ACTIVITIES[params.activity])
    defy(world, hero, ACTIVITIES[params.activity])
    gear = compromise(world, parent, hero, ACTIVITIES[params.activity], prize)
    if gear is None:
        raise StoryError("Expected a valid compromise gear but none was found.")
    resolve(world, hero, parent, ACTIVITIES[params.activity], prize, gear)

    world.facts["gear"] = gear
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    act = world.facts["activity"]
    prize = world.facts["prize"]
    return [
        f'Write a short rhyming story for a small child about a {p.gender} named {p.name} and a {prize.label}, with a happy ending.',
        f'Tell a gentle rhyme where {p.name} wants to {act.verb} but a grown-up worries about a {prize.phrase}.',
        f'Write a sunny story using the word "plethora" and ending with a safe, cheerful compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    act = world.facts["activity"]
    prize = world.facts["prize"]
    parent = world.facts["caretaker"]
    gear = world.facts["gear"]
    return [
        QAItem(
            question=f"What did {p.name} want to do at the meadow?",
            answer=f"{p.name} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the grown-up worry about the {prize.label}?",
            answer=f"The grown-up worried because the {prize.label} could spill and get messy if {p.name} rushed off too fast.",
        ),
        QAItem(
            question=f"How did the story end happily?",
            answer=f"They used {gear.label} first, so {p.name} could enjoy the day and the {prize.label} stayed neat.",
        ),
        QAItem(
            question=f"Who stayed calm at the end?",
            answer=f"{p.name} and the grown-up both stayed calm once they found the safe plan.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does the word plethora mean?",
            answer="A plethora means a very large amount of something, like having lots and lots of tiny treasures.",
        ),
        QAItem(
            question="What is a compromise?",
            answer="A compromise is a solution where people make a careful plan that helps everyone.",
        ),
        QAItem(
            question="Why can a tray help with berries or apples?",
            answer="A tray can help because it keeps little things from slipping away while someone carries them.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.type} meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), zones(A,_).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,A), protects(G,P).
valid_story(A,P) :- prize_at_risk(A,P), has_fix(A,P).
"""


def asp_facts() -> str:
    import asp

    lines = []
    lines.append(asp.fact("setting", SETTING.place))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zones", aid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for a in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, a))
        for p in sorted(g.protects):
            lines.append(asp.fact("protects", g.id, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = sorted((a, p) for _, a, p in [(SETTING.place, act, pr) for act in ACTIVITIES for pr in PRIZES if prize_at_risk(ACTIVITIES[act], PRIZES[pr]) and select_gear(ACTIVITIES[act], PRIZES[pr])])
    cl = asp_valid_stories()
    if cl:
        print("OK: ASP produced valid story pairs.")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


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
    StoryParams(place="meadow", activity="berries", prize="basket", name="Mia", gender="girl", parent="mother", trait="cheerful"),
    StoryParams(place="meadow", activity="apples", prize="jar", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="meadow", activity="pearls", prize="pouch", name="Nora", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.asp:
        for pair in asp_valid_stories():
            print(pair)
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
            if sample.story not in seen:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
