#!/usr/bin/env python3
"""
storyworlds/worlds/page_strain_rascal_hair_salon_friendship_suspense.py
=======================================================================

A standalone story world for a small hair-salon tale with friendship, suspense,
and a twist.

Premise:
- A child and a friend go to a hair salon.
- A beloved page from a book or magazine is at risk of getting strained, torn,
  or bent during the visit.
- A mischievous rascal makes the moment suspenseful.
- The ending twist turns the salon visit into a friendly rescue rather than a
  disaster.

The domain is intentionally compact and classical: a small cast, a few pieces of
gear, and one state-driven turn that resolves through a helpful friendship.
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
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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
    place: str = "the hair salon"
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
    fragile: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
    worn_label: str = ""


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind != "character"]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_strain_page(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("rustle", 0.0) < THRESHOLD:
            continue
        for item in world.items():
            if item.type != "page":
                continue
            if item.carried_by != actor.id:
                continue
            sig = ("strain", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["strain"] = item.meters.get("strain", 0.0) + 1
            item.memes["worry"] = item.memes.get("worry", 0.0) + 1
            out.append(f"{item.label} bent at the corner.")
    return out


def _r_friendship_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("Hero")
    friend = world.entities.get("Friend")
    if not hero or not friend:
        return out
    if hero.memes.get("trust", 0.0) < THRESHOLD:
        return out
    if friend.meters.get("steady", 0.0) < THRESHOLD:
        return out
    page = world.entities.get("Page")
    if not page:
        return out
    if page.meters.get("strain", 0.0) < THRESHOLD:
        return out
    sig = ("friendship_fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    page.meters["strain"] = 0.0
    page.meters["saved"] = 1.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0.0) + 1
    out.append("__twist__")
    return out


CAUSAL_RULES = [
    Rule("strain_page", _r_strain_page),
    Rule("friendship_help", _r_friendship_help),
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
                produced.extend(s for s in sents if s != "__twist__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTING = Setting(place="the hair salon", affords={"wash", "dry", "brush", "braid"})
ACTIVITIES = {
    "wash": Activity(
        id="wash",
        verb="get a wash and trim",
        gerund="getting a wash and trim",
        rush="reach for the dripping towel",
        mess="rustle",
        soil="bent and wrinkled",
        keyword="wash",
        tags={"hair", "water"},
    ),
    "dry": Activity(
        id="dry",
        verb="sit under the dryer",
        gerund="sitting under the dryer",
        rush="duck under the warm hood",
        mess="rustle",
        soil="bent and wrinkled",
        keyword="dry",
        tags={"hair", "warmth"},
    ),
    "braid": Activity(
        id="braid",
        verb="get a braid",
        gerund="getting a braid",
        rush="lean closer for the mirror",
        mess="rustle",
        soil="bent and wrinkled",
        keyword="braid",
        tags={"hair", "style"},
    ),
}

PRIZES = {
    "page": Prize(
        label="page",
        phrase="a bright page from a space adventure book",
        type="page",
        fragile=True,
    ),
    "magazine_page": Prize(
        label="page",
        phrase="a shiny magazine page with rocket pictures",
        type="page",
        fragile=True,
    ),
}

GEAR = [
    Gear(
        id="clip",
        label="a big clip",
        guards={"rustle"},
        prep="use a big clip to hold the page flat",
        tail="used the clip to keep the page smooth",
        worn_label="clip",
    ),
    Gear(
        id="folder",
        label="a stiff folder",
        guards={"rustle"},
        prep="slide the page into a stiff folder",
        tail="slid the page into the folder",
        worn_label="folder",
    ),
]

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "Zoe", "Ivy"]
BOY_NAMES = ["Theo", "Leo", "Max", "Finn", "Noah", "Ben"]
TRAITS = ["brave", "curious", "cheerful", "spirited", "gentle"]

ASP_RULES = r"""
prize_at_risk(A, P) :- activity(A), page(P), rustles(A).
needs_fix(P) :- prize_at_risk(_, P).
compatible(G, A, P) :- prize_at_risk(A, P), gear(G), guards(G, rustle).
valid_story(A, P) :- prize_at_risk(A, P), compatible(_, A, P).
"""


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    friend_name: str
    rascal_name: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    return [("hair_salon", a, p) for a in ACTIVITIES for p in PRIZES if a in SETTING.affords]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "hair_salon"))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("rustles", a))
    for p in PRIZES:
        lines.append(asp.fact("page", p))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(a, p) for _, a, p in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def reasonableness_gate(activity: Activity, prize: Prize) -> bool:
    return prize.fragile and activity.mess == "rustle"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hair-salon story world with friendship, suspense, and a twist.")
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--rascal-name")
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
        if not reasonableness_gate(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No story: this activity would not strain this prize in a believable way.")
    combos = [c for c in valid_combos()
              if (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    _, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != name])
    rascal_name = args.rascal_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n not in {name, friend_name}])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, friend_name=friend_name, rascal_name=rascal_name, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id="Hero", kind="character", type=params.gender, label=params.name, traits=["little", params.trait]))
    friend = world.add(Entity(id="Friend", kind="character", type="child", label=params.friend_name, traits=["helpful", "steady"]))
    rascal = world.add(Entity(id="Rascal", kind="character", type="child", label=params.rascal_name, traits=["mischievous"]))
    page = world.add(Entity(id="Page", type="page", label="the page", phrase=PRIZES[params.prize].phrase, owner=hero.id, caretaker=friend.id, carried_by=hero.id))
    gear = world.add(Entity(id="Clip", type="gear", label="the big clip", owner=friend.id))
    gear2 = world.add(Entity(id="Folder", type="gear", label="the stiff folder", owner=friend.id))

    hero.memes["curiosity"] = 1
    friend.memes["trust"] = 1
    rascal.memes["sneaky"] = 1

    world.say(f"{hero.label} and {friend.label} rolled into the hair salon like it was a tiny rocket bay.")
    world.say(f"{hero.label} carried {page.label}, and {page.phrase} flashed with space pictures.")
    world.say(f"{hero.label} wanted to {ACTIVITIES[params.activity].verb}, but {rascal.label} kept bobbing near the page with a grin.")
    world.para()
    world.say(f"The dryers hummed softly overhead. Then {rascal.label} made a quick little swipe, and the page began to crinkle at the edge.")
    hero.meters["rustle"] = 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"{friend.label} noticed the bend first. {friend.label} held up {gear.label} like a shield and whispered, 'I know a safer way.'")
    friend.meters["steady"] = 1
    hero.memes["trust"] = 1
    if page.meters.get("strain", 0.0) >= THRESHOLD:
        page.meters["strain"] = 1.0
    propagate(world, narrate=True)
    if page.meters.get("saved", 0.0) >= THRESHOLD:
        world.say(f"Twist: the rascal was not trying to ruin the page at all. {rascal.label} was chasing a loose sticker that had blown under the chair.")
        world.say(f"Once the sticker was found, {friend.label} slid the page into {gear2.label}, and everyone laughed at the near-miss.")
        page.meters["saved"] = 1.0
    world.facts.update(hero=hero, friend=friend, rascal=rascal, page=page, activity=ACTIVITIES[params.activity], prize=PRIZES[params.prize], gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short hair-salon story for a young child that includes a page, a rascal, and a twist.',
        f"Tell a gentle suspense story where {f['hero'].label} brings a page to the hair salon and a helpful friend saves it.",
        f'Write a story set in a hair salon where a page almost gets strained, but friendship turns the ending around.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    rascal = f["rascal"]
    page = f["page"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who brought the page to the hair salon?",
            answer=f"{hero.label} brought the page to the hair salon, and {hero.pronoun('possessive')} friend, {friend.label}, stayed close by.",
        ),
        QAItem(
            question=f"What made the story feel suspenseful?",
            answer=f"It felt suspenseful when {rascal.label} swiped near the page and the corner began to crinkle during the salon visit.",
        ),
        QAItem(
            question=f"What was the twist at the end?",
            answer=f"The twist was that {rascal.label} was chasing a loose sticker, not trying to ruin the page, and {friend.label} saved the page with a stiff folder.",
        ),
        QAItem(
            question=f"How did friendship help in the story?",
            answer=f"Friendship helped because {friend.label} stayed steady, spotted the danger, and protected {page.label} so {hero.label} could relax.",
        ),
        QAItem(
            question=f"What did {hero.label} want to do in the salon?",
            answer=f"{hero.label} wanted to {act.verb}, but first {hero.pronoun('possessive')} page had to stay safe from getting bent.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hair salon?",
            answer="A hair salon is a place where people wash, cut, brush, and style hair.",
        ),
        QAItem(
            question="What does a clip do?",
            answer="A clip holds something still so it does not slip, bend, or fall.",
        ),
        QAItem(
            question="Why can a page get strained?",
            answer="A page can get strained if it gets bent, crumpled, or pulled too hard.",
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
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(activity="wash", prize="page", name="Mia", gender="girl", friend_name="Theo", rascal_name="Leo", trait="curious"),
    StoryParams(activity="dry", prize="magazine_page", name="Noah", gender="boy", friend_name="Ivy", rascal_name="Zoe", trait="brave"),
    StoryParams(activity="braid", prize="page", name="Ava", gender="girl", friend_name="Ben", rascal_name="Max", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.name}: {p.activity} at the hair salon"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
