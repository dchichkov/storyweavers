#!/usr/bin/env python3
"""
A small slice-of-life storyworld set at a marina, where a curious child sets out
on a gentle quest to solve a tiny mystery involving relish.
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the marina"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    search: str
    mystery: str
    clue: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.mystery_solved = False

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.mystery_solved = self.mystery_solved
        return clone


def _do_search(world: World, actor: Entity, activity: Activity, prize: Entity) -> None:
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0) + 1
    actor.meters["searching"] = actor.meters.get("searching", 0) + 1
    if activity.keyword == "relish" and prize.location == "snack shack":
        world.mystery_solved = True
        prize.carried_by = actor.id
        world.facts["found_at"] = prize.location


def predict_outcome(world: World, actor: Entity, activity: Activity, prize: Entity) -> dict:
    sim = world.copy()
    _do_search(sim, sim.get(actor.id), activity, sim.get(prize.id))
    return {"solved": sim.mystery_solved}


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who liked quiet days at {world.setting.place}.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because every small clue felt like a story waiting to be found."
    )


def setup_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["fondness"] = hero.memes.get("fondness", 0) + 1
    prize.carried_by = hero.id
    world.say(f"That morning, {hero.id} had {hero.pronoun('possessive')} {prize.label}, which smelled bright and tangy.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}.")
    world.say(f"The docks were busy, and the gulls made the whole place feel like a tiny adventure.")


def notice_mystery(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} noticed something odd: the little {prize.label} jar was missing from the snack shelf, and {hero.pronoun()} wanted to solve the mystery."
    )
    world.say(f"{hero.id} decided to {activity.verb} and follow the clues.")


def ask_clue(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f'"Maybe the jar moved on its own?" {hero.pronoun("subject").capitalize()} asked, but {hero.pronoun("possessive")} {parent.label} smiled and said to look for a clue.'
    )


def search_and_solve(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    _do_search(world, hero, activity, prize)
    if world.mystery_solved:
        world.say(f"{hero.id} followed the smell of relish past the pier, and it led right to the snack shack.")
        world.say(f"There, tucked beside the napkins, was the missing {prize.label}.")
    else:
        world.say(f"{hero.id} looked carefully, but the clue still felt out of reach.")


def resolve(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"{hero.id} smiled and held up the found {prize.label}. {hero.pronoun().capitalize()} had solved the mystery all by being curious."
    )
    world.say(
        f"Then {hero.id} and {hero.pronoun('possessive')} {parent.label} sat by the water, sharing a snack and a quiet, happy moment at the marina."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Maya", hero_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="relish", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=parent.id, location=prize_cfg.location, plural=prize_cfg.plural))

    introduce(world, hero)
    loves(world, hero, activity)
    setup_prize(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    notice_mystery(world, hero, activity, prize)
    ask_clue(world, hero, parent, activity, prize)
    search_and_solve(world, hero, activity, prize)
    world.para()
    resolve(world, hero, parent, activity, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "marina": Setting(place="the marina", affords={"relish"}),
}

ACTIVITIES = {
    "relish": Activity(
        id="relish",
        verb="follow the relish clue",
        gerund="solving little mysteries",
        search="search for the missing relish",
        mystery="a missing jar",
        clue="a tangy smell by the pier",
        keyword="relish",
        tags={"relish", "mystery", "curiosity", "quest"},
    ),
}

PRIZES = {
    "jar": Prize(
        label="jar",
        phrase="a small relish jar",
        type="jar",
        location="snack shack",
        plural=False,
    ),
}

QUESTS = [
    QuestItem(
        id="notebook",
        label="a little notebook",
        phrase="a tiny notebook for clues",
        helps={"relish"},
        covers={"ideas"},
        prep="take a little notebook along",
        tail="went back with the notebook and a smile",
    ),
]

GIRL_NAMES = ["Maya", "Ivy", "Nina", "Lena", "Ruby"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Finn", "Miles"]
TRAITS = ["curious", "gentle", "thoughtful", "quiet", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


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


KNOWLEDGE = {
    "relish": [("What is relish?", "Relish is a tangy condiment made from chopped vegetables, often served on sandwiches or hot dogs.")],
    "mystery": [("What is a mystery?", "A mystery is something you do not know yet, so you look for clues to solve it.")],
    "curiosity": [("What is curiosity?", "Curiosity is the wish to know more and ask questions about things that seem interesting.")],
    "quest": [("What is a quest?", "A quest is a journey or search to find something or solve a problem.")],
}
KNOWLEDGE_ORDER = ["relish", "mystery", "curiosity", "quest"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, activity, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a slice-of-life story for a small child at {f["setting"].place} involving relish, curiosity, and a gentle quest.',
        f"Tell a calm story where {hero.id} notices a missing {prize.label} and uses curiosity to solve the mystery with {hero.pronoun('possessive')} {parent.label}.",
        f'Write a child-friendly mystery story that includes the word "relish" and ends with a happy discovery at the marina.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, activity = f["hero"], f["parent"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who solved the mystery at the marina?",
            answer=f"{hero.id} solved it by following the relish clue with quiet curiosity.",
        ),
        QAItem(
            question=f"What was missing from the snack shelf?",
            answer=f"The missing thing was the {prize.label} of relish.",
        ),
        QAItem(
            question=f"Why did {hero.id} go looking around the marina?",
            answer=f"{hero.id} wanted to solve the mystery, so {hero.pronoun()} searched for the smell of relish and looked for clues.",
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
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(marina).
affords(marina,relish).

activity(relish).
tags(relish,mystery).
tags(relish,curiosity).
tags(relish,quest).

prize(jar).
contains_relish(jar).

compatible_story(P,A,Pr) :- place(P), affords(P,A), activity(A), prize(Pr).
featured(A) :- activity(A), tags(A,mystery), tags(A,curiosity), tags(A,quest).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p, setting in SETTINGS.items():
        lines.append(asp.fact("place", p))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("activity", a.id))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", a.id, t))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a marina mystery, a relish clue, and a gentle quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait if hasattr(args, "trait") and args.trait else rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="marina", activity="relish", prize="jar", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="marina", activity="relish", prize="jar", name="Theo", gender="boy", parent="father", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combo(s):")
        for c in combos:
            print("  ", c)
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
