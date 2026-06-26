#!/usr/bin/env python3
"""
storyworlds/worlds/popular_base_commit_misunderstanding_quest_dialogue_comedy.py
==============================================================================

A small story world about a child, a playful misunderstanding, and a tiny quest
at a computer desk. The comedy comes from a word mix-up: "base" sounds like a
place, "commit" sounds like a promise, and "popular" sounds like everyone is
about to show up.

The world is intentionally narrow: the hero wants to finish a first project
commit for a club game, but the grown-up hears the words in the wrong way at
first. The solution is not a random miracle; it is a careful, state-driven
repair: they clarify the plan, make a backup, and complete the commit without
losing anything important.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    risk_area: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


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
    "clubroom": Setting("the clubroom", True, {"commit", "quest"}),
    "library": Setting("the library corner", True, {"commit", "quest"}),
    "bedroom": Setting("the bedroom desk", True, {"commit"}),
    "kitchen": Setting("the kitchen table", True, {"commit", "quest"}),
}

ACTIVITIES = {
    "commit": Activity(
        id="commit",
        verb="make the first commit",
        gerund="making the first commit",
        rush="hit send before the moment got away",
        risk="lose the draft",
        keyword="commit",
        tags={"commit", "popular"},
    ),
    "quest": Activity(
        id="quest",
        verb="start the quest",
        gerund="going on the quest",
        rush="dash off on the quest",
        risk="lose the map",
        keyword="quest",
        tags={"quest"},
    ),
}

PRIZES = {
    "base": Prize(
        label="base",
        phrase="a neat base page",
        type="base",
        risk_area="desk",
    ),
    "poster": Prize(
        label="poster",
        phrase="a bright poster draft",
        type="poster",
        risk_area="desk",
    ),
    "notebook": Prize(
        label="notebook",
        phrase="a tidy notebook page",
        type="notebook",
        risk_area="desk",
    ),
    "sticker_sheet": Prize(
        label="sticker sheet",
        phrase="a sheet of funny stickers",
        type="stickers",
        risk_area="desk",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="backup",
        label="a backup copy",
        covers={"desk"},
        prep="make a backup copy first",
        tail="kept the backup copy open",
    ),
    Gear(
        id="tabs",
        label="sticky note tabs",
        covers={"desk"},
        prep="put sticky note tabs on the pages first",
        tail="lined the pages with sticky note tabs",
        plural=True,
    ),
]

GIRL_NAMES = ["Mia", "Zoe", "Nora", "Luna", "Ivy", "Ava"]
BOY_NAMES = ["Leo", "Max", "Ben", "Noah", "Eli", "Finn"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["curious", "cheerful", "sly", "brave", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                if act_id == "commit" and prize.risk_area == "desk":
                    out.append((place, act_id, prize_id))
                if act_id == "quest" and prize_id in {"base", "poster", "notebook"}:
                    out.append((place, act_id, prize_id))
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.id == "commit" and prize.risk_area == "desk"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    if not prize_at_risk(activity, prize):
        return None
    return GEAR[0]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} does not make sense with {prize.label} here.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} is not a typical {gender}'s item in this world.)"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id == "commit":
        actor.memes["nervous"] = actor.memes.get("nervous", 0.0) + 1.0
        actor.meters["finished"] = actor.meters.get("finished", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.id} clicked the button and the tiny project step was ready.")
    elif activity.id == "quest":
        actor.meters["searched"] = actor.meters.get("searched", 0.0) + 1.0
        if narrate:
            world.say(f"{actor.id} looked from one clue to the next until the path felt clearer.")


def predict_state(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "lost": bool(prize.meters.get("scuffed", 0.0) >= THRESHOLD),
        "safe": True,
    }


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={"hope": 1.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id="Prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=helper.id,
        owner=hero.id,
        plural=prize_cfg.plural,
        meters={},
        memes={},
    ))

    hero.memes["popular"] = 1.0
    hero.memes["confusion"] = 0.0

    world.say(f"{hero.id} was a {trait} {hero.type} who loved simple plans and silly jokes.")
    world.say(f"{hero.id} wanted to {activity.verb} for a popular little club idea called the base.")
    world.say(f"{hero.id} also wanted the quest to feel tidy, because nobody likes a messy desk.")

    world.para()
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {helper_type} sat at {setting.place}.")
    world.say(f"{hero.id} pointed at {prize.phrase} and said, \"We need the base before we can {activity.verb}.\"")
    world.say(f"That made {helper.id} blink twice, because {helper.id} heard \"base\" and thought of a ball game.")

    hero.memes["confusion"] += 1.0
    helper.memes["confusion"] = helper.memes.get("confusion", 0.0) + 1.0
    world.say(f"\"Do you mean a baseball base?\" {helper.id} asked.")
    world.say(f"\"No,\" {hero.id} said, laughing. \"I mean the first page. The base of the project.\"")

    world.para()
    world.say(f"Then {hero.id} said the word commit, and {helper.id} gasped.")
    world.say(f"\"You want to commit what?\" {helper.id} asked. \"Are we in trouble?\"")
    world.say(f"{hero.id} grinned. \"Just the file. Not a crime. A tiny click.\"")
    world.say(f"That joke made the whole table feel less serious at once.")

    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1.0

    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError("No safe gear for this story.")

    world.para()
    world.say(f"{helper.id} still looked worried, so {hero.id} made a backup copy first.")
    world.say(f"\"Now it is a safe quest,\" {hero.id} said. \"If anything goes wrong, we still have the copy.\"")
    world.say(f"{helper.id} smiled and set {gear.label} beside the keyboard.")
    world.say(f"\"That sounds much better than a surprise disaster,\" {helper.id} said.")

    world.para()
    _do_activity(world, hero, activity, narrate=False)
    world.say(f"{hero.id} took a breath, checked the page, and {activity.rush}.")
    world.say(f"Then {hero.id} pressed the key to {activity.verb}, and nothing got lost.")
    world.say(f"{gear.tail}, and the base page stayed neat.")
    world.say(f"{prize_cfg.label.capitalize()} remained clean on the desk while the little project finally had its start.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=True,
        confusion=hero.memes["confusion"] > 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    act = f["activity"]
    return [
        f'Write a short comedy for a child about {hero.id}, a base, and a commit.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {helper.id} misunderstands the word base.",
        f'Write a small quest story with dialogue in which the word "{act.keyword}" matters and the first plan needs a backup copy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do for the club idea?",
            answer=f"{hero.id} wanted to {act.verb}, and the plan was supposed to begin with {prize.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} first get confused about the base?",
            answer=f"{helper.id} thought base meant a baseball base, but {hero.id} meant the first page of the project.",
        ),
        QAItem(
            question=f"What did {hero.id} do before making the commit?",
            answer=f"{hero.id} made a backup copy first, so the story stayed safe and nothing important was lost.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The base page stayed neat, the commit was finished, and {hero.id} and {helper.id} laughed together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a backup copy for?",
            answer="A backup copy is a second version kept safe in case the first one gets lost or changed by mistake.",
        ),
        QAItem(
            question="Why do people smile when a misunderstanding is cleared up?",
            answer="People smile because the mix-up is over, everyone understands each other, and the worry goes away.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small adventure where someone looks for something, solves a problem, or tries to reach a goal.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("clubroom", "commit", "base", "Mina", "girl", "mother", "cheerful"),
    StoryParams("library", "commit", "poster", "Leo", "boy", "father", "curious"),
    StoryParams("kitchen", "quest", "notebook", "Nora", "girl", "grandma", "bouncy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy storyworld about a misunderstanding, a quest, and a commit.")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not prize_at_risk(act, pr):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = rng.choice(TRAITS)
    return StoryParams(place, activity, prize_id, name, gender, helper, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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


ASP_RULES = r"""
place(P) :- setting(P).
activity(A) :- acts(A).
prize(P) :- thing(P).

valid(P, A, R) :- setting(P), acts(A), thing(R), risk_area(R, desk), A = commit.
valid_story(P, A, R, G) :- valid(P, A, R), wears(G, R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("acts", aid))
    for rid, pr in PRIZES.items():
        lines.append(asp.fact("thing", rid))
        lines.append(asp.fact("risk_area", rid, pr.risk_area))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
            print(f"  {place:10} {act:8} {prize:12}  [{', '.join(genders)}]")
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
