#!/usr/bin/env python3
"""
A tiny storyworld about a brave bookstore errand where kindness resolves a
small conflict and turns the outing into an adventure.

Seed premise:
A child goes into a bookstore looking for the fifteenth adventure book. A
wobbly stack and a rude grab cause a conflict, but a kind bookseller helps the
child slow down, ask politely, and find the right book safely.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    on_shelf: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the bookstore"
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
    risky: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    id: str
    label: str
    prep: str
    tail: str
    kindness_boost: float = 1.0


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


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
    "bookstore": Setting(place="the bookstore", affords={"search", "reach"}),
}

ACTIVITIES = {
    "search": Activity(
        id="search",
        verb="find the fifteenth adventure book",
        gerund="searching for the fifteenth adventure book",
        rush="dash toward the tall shelf",
        mess="jostled",
        soil="mixed up",
        keyword="fifteenth",
        tags={"adventure", "fifteenth"},
    ),
    "reach": Activity(
        id="reach",
        verb="reach the top shelf",
        gerund="reaching up for the top shelf",
        rush="stretch over the stack",
        mess="toppled",
        soil="tipped",
        keyword="flit",
        tags={"flit", "adventure"},
    ),
}

PRIZES = {
    "book": Prize(
        label="book",
        phrase="the fifteenth adventure book",
        type="book",
        risky=True,
        genders={"girl", "boy"},
    ),
    "map": Prize(
        label="map",
        phrase="a bright treasure map book",
        type="book",
        risky=True,
        genders={"girl", "boy"},
    ),
}

HELPERS = {
    "bookseller": Helper(
        id="bookseller",
        label="the bookseller",
        prep="slow down and ask nicely",
        tail="showed the child the right shelf",
        kindness_boost=1.0,
    ),
    "parent": Helper(
        id="parent",
        label="the parent",
        prep="take a breath and ask kindly",
        tail="helped the child carry the book safely",
        kindness_boost=1.0,
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Sam"]
TRAITS = ["curious", "brave", "gentle", "bold", "patient"]


def is_reasonable(activity: Activity, prize: Prize) -> bool:
    return activity.id in {"search", "reach"} and prize.risky


def valid_combos() -> list[tuple[str, str, str]]:
    return [("bookstore", a, p) for a in ACTIVITIES for p in PRIZES if is_reasonable(ACTIVITIES[a], PRIZES[p])]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not honestly put {prize.label} at risk in the bookstore.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: try --gender {ok} for this {PRIZES[prize_id].label}.)"


def predict(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {
        "tipped": bool(prize.meters.get("tipped", 0) >= THRESHOLD),
        "kindness": sim.get("helper").memes.get("kindness", 0),
    }


def _do_activity(world: World, hero: Entity, activity: Activity, narrate: bool = True) -> None:
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    hero.memes["excitement"] = hero.memes.get("excitement", 0) + 1
    if hero.meters[activity.mess] >= THRESHOLD:
        world.fired.add((activity.id, hero.id))
        if narrate:
            world.say(f"{hero.id} {activity.gerund}, and a little trouble started to gather.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_id: str, hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "brave"]),
    ))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=HELPERS[helper_id].label))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        on_shelf=True,
    ))
    shelf = world.add(Entity(id="shelf", type="shelf", label="the tall shelf"))
    flit = world.add(Entity(id="flit", type="bird", label="a tiny paper bird", phrase="a tiny paper bird"))
    helper.memes["kindness"] = 1.0

    world.say(
        f"{hero.id} was a little {next(t for t in hero.traits if t != 'little')} {hero.type} who loved adventure stories."
    )
    world.say(
        f"One day, {hero.id} went to {setting.place} with a wish to {activity.verb}, and {flit.label} seemed to flit between the shelves."
    )
    world.say(
        f"At the front of the aisle, {hero.id} hoped to find {prize.phrase}."
    )

    world.para()
    world.say(
        f"{hero.id} hurried over, because the {prize.label} was supposed to be the fifteenth book on the shelf."
    )
    world.say(
        f"But {hero.id} {activity.rush}, and the books beside {shelf.label} began to wobble."
    )
    predict(world, hero, activity, prize.id)
    hero.memes["conflict"] = 1.0
    world.say(
        f"{helper.label} noticed the wobble right away and worried that the shelf might tip."
    )
    world.say(
        f'"Please {HELPERS[helper_id].prep}," {helper.label} said kindly.'
    )

    world.para()
    hero.memes["conflict"] = 0.0
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    hero.meters["careful"] = hero.meters.get("careful", 0) + 1
    world.say(
        f"{hero.id} stopped, took a breath, and smiled back."
    )
    world.say(
        f"{hero.id} answered with kindness, and the two of them looked for the right book together."
    )
    world.say(
        f"{HELPERS[helper_id].tail}. In the end, {hero.id} held {prize.phrase}, and the adventure felt bigger because it was shared safely."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        flit=flit,
        conflict=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short adventure story for a child named {hero.id} in a bookstore, and include the word "flit".',
        f"Tell a gentle bookstore adventure where {hero.id} wants to {act.verb} and needs kindness to handle a conflict.",
        f'Write a story that uses "fifteenth" and ends with a child finding the right book after a small conflict.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the bookstore?",
            answer=f"{hero.id} wanted to {act.verb} and find {prize.phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the shelf started to wobble?",
            answer=f"{helper.label} helped {hero.id} stay calm and choose a safer way.",
        ),
        QAItem(
            question=f"Why did the moment become a conflict?",
            answer=f"The books wobbled when {hero.id} rushed at the shelf, so everyone had to slow down and be careful.",
        ),
        QAItem(
            question=f"What number book was {hero.id} looking for?",
            answer="The child was looking for the fifteenth adventure book.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"{hero.id} found the right book, and kindness turned the problem into a happy adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bookstore?",
            answer="A bookstore is a place where people can find and buy books.",
        ),
        QAItem(
            question="What does kindness do during a problem?",
            answer="Kindness helps people stay calm, listen, and work together to solve the problem.",
        ),
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a part where characters want different things or run into trouble.",
        ),
        QAItem(
            question="What is an adventure story?",
            answer="An adventure story is a story about exciting events, brave choices, and a big goal.",
        ),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bookstore", activity="search", prize="book", name="Mia", gender="girl", helper="bookseller", trait="curious"),
    StoryParams(place="bookstore", activity="reach", prize="map", name="Leo", gender="boy", helper="parent", trait="brave"),
]


ASP_RULES = r"""
at_risk(A,P) :- activity(A), prize(P), risky(P).
compatible(A,P) :- at_risk(A,P), seeks_kindness(A), prize(P).
valid_story(Place,A,P,G) :- setting(Place), at_risk(A,P), compatible(A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("seeks_kindness", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.risky:
            lines.append(asp.fact("risky", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/2.\n#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = {(a, p) for _, a, p in valid_combos()}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small bookstore adventure storyworld.")
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
        if not is_reasonable(act, pr):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(sorted(PRIZES[prize].genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(list(HELPERS))
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.helper, [params.trait])
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
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a},{p}" for a, p in asp_valid_combos()))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
