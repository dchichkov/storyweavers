#!/usr/bin/env python3
"""
A small superhero-style story world about literary bravery, friendship, and cautionary choices.

Seed tale:
---
Maya loved the neighborhood library because it was full of bright stories and brave heroes.
She also loved wearing her silver cape and pretending she could zip through the city like a
real superhero.

One windy afternoon, Maya and her best friend Jun found a stack of picture books wobbling
near the open reading-room window. Maya wanted to dash over and catch them with her cape,
but Jun noticed a wet patch on the floor and warned her to slow down. "If you rush, you could
slip and drop the books," he said.

Maya took a careful breath. Together they closed the window, used a sturdy cart, and carried
the books back to the shelf. Maya still felt brave, but now she knew that bravery could be
careful too.
---
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
# Core world model
# ---------------------------------------------------------------------------

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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)
    keyword: str = ""


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
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.wind: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.wind = self.wind
        clone.paragraphs = [[]]
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the neighborhood library", affords={"dash", "lift"}),
}

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash to the books",
        gerund="dashing through the aisle",
        rush="run across the slick floor",
        mess="scratched",
        soil="scuffed and messy",
        tags={"bravery", "friendship", "cautionary", "literary"},
        keyword="library",
    ),
    "lift": Activity(
        id="lift",
        verb="lift the fallen books",
        gerund="lifting the fallen books",
        rush="scoop them up too quickly",
        mess="bent",
        soil="bent and bent out of shape",
        tags={"bravery", "friendship", "cautionary", "literary"},
        keyword="books",
    ),
}

PRIZES = {
    "books": Prize(
        label="books",
        phrase="a neat stack of picture books",
        type="books",
        region="hands",
        plural=True,
    ),
    "cape": Prize(
        label="cape",
        phrase="a shiny silver cape",
        type="cape",
        region="back",
    ),
}

GEAR = [
    Gear(
        id="cart",
        label="a sturdy book cart",
        prep="use the sturdy book cart",
        tail="rolled the cart carefully to the shelf",
        covers={"hands", "back"},
        guards={"scratched", "bent"},
    ),
]

HERO_NAMES = ["Maya", "Ari", "Nina", "Omar", "Lena", "Kai"]
FRIEND_NAMES = ["Jun", "Tess", "Milo", "Pia", "Noah", "Ivy"]
TRAITS = ["brave", "curious", "bright", "spirited", "kind"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_gender: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "hands" or (activity.id == "dash" and prize.region == "back")


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for a in setting.affords:
            act = ACTIVITIES[a]
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, a, pid))
    return out


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} would not honestly threaten {prize.label}, "
        f"or the library has no helpful gear that fits the situation.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _r_slip(world: World) -> list[str]:
    out = []
    hero = world.get(world.facts["hero"].id)
    if hero.meters.get("scratched", 0) < THRESHOLD:
        return out
    if hero.memes.get("caution", 0) < THRESHOLD:
        sig = ("slip", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["scare"] = hero.memes.get("scare", 0) + 1
            out.append(f"{hero.id} nearly slipped on the wet floor.")
    return out


def _r_work(world: World) -> list[str]:
    out = []
    prize = world.get("prize")
    if prize.meters.get("dirty", 0) >= THRESHOLD and ("work", prize.id) not in world.fired:
        world.fired.add(("work", prize.id))
        world.get("friend").memes["concern"] = world.get("friend").memes.get("concern", 0) + 1
        out.append("That would make more work for the librarian.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_slip, _r_work):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, hero: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"ruined": prize.meters.get("dirty", 0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["excitement"] = actor.memes.get("excitement", 0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str,
         friend_name: str, trait: str) -> World:
    world = World(setting)
    world.wind = "windy"

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "brave"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", traits=["best friend", "careful"]))
    librarian = world.add(Entity(id="librarian", kind="character", type="woman", label="the librarian"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker="librarian"))
    prize.owner = hero.id
    prize.worn_by = hero.id if prize_cfg.region == "back" else None
    if prize_cfg.region == "back":
        prize.worn_by = hero.id

    world.facts.update(hero=hero, friend=friend, librarian=librarian, prize=prize, activity=activity, setting=setting)

    world.say(f"{hero.id} was a little {trait} {hero.type} who loved literary superhero stories.")
    world.say(f"{hero.id} also loved {prize.phrase} and wore them like treasure.")

    world.para()
    world.say(f"One windy afternoon, {hero.id} and {friend.id} went to {setting.place}.")
    world.say(f"A gust swirled near the reading room, and the {activity.keyword} trouble began.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {friend.id} noticed the wet floor and raised a hand.")
    world.say(f'"If you {activity.rush}, you might get hurt," {friend.id} said.')

    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    if predict_mess(world, hero, activity, prize.id)["ruined"]:
        world.say(f"{hero.id} understood the warning and slowed down.")
    _do_activity(world, hero, activity, narrate=False)
    if prize_cfg.region == "back":
        prize.meters[activity.mess] = prize.meters.get(activity.mess, 0) + 1
        prize.meters["dirty"] = prize.meters.get("dirty", 0) + 1

    world.para()
    gear = select_gear(activity, prize_cfg)
    if gear is None:
        raise StoryError(explain_rejection(activity, prize_cfg))
    world.say(f"{friend.id} pointed to {gear.label} and smiled.")
    world.say(f'"Let us {gear.prep} together," {friend.id} said.')
    world.say(f"{hero.id} nodded, and they {gear.tail}.")
    world.say(f"Then {hero.id} {activity.gerund}, while {prize.label} stayed safe and the library stayed calm.")
    world.say(f"{hero.id} felt brave because {friend.id} had helped in a careful way.")

    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    friend = f["friend"]
    return [
        f'Write a short literary superhero story about {hero.id}, {friend.id}, and {prize.label}.',
        f"Tell a brave but cautionary story where {hero.id} wants to {activity.verb} at {world.setting.place}.",
        f"Write a friendship story with a superhero feel that includes a careful choice and the word 'literary'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    prize = f["prize"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little brave superhero kid who loves literary stories and {prize.label}.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id}?",
            answer=f"{friend.id} warned {hero.id} because rushing to {activity.verb} on the slick floor could cause a fall and make the books messy.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {world.facts['gear'].label} and worked together carefully, so the books stayed safe.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and happy because friendship helped turn a risky moment into a safe rescue.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a superhero do?",
            answer="A superhero tries to help others, solve problems, and be brave.",
        ),
        QAItem(
            question="Why is it smart to slow down on a wet floor?",
            answer="A wet floor can be slippery, so slowing down helps you avoid falling.",
        ),
        QAItem(
            question="What is a library for?",
            answer="A library is a place where people borrow books and read quiet stories.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), risky(A,P).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), fixes(G,A,P).
valid(Place,A,P) :- setting(Place), affords(Place,A), has_fix(A,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
        if aid == "dash":
            lines.append(asp.fact("risky", aid, "books"))
            lines.append(asp.fact("risky", aid, "cape"))
        if aid == "lift":
            lines.append(asp.fact("risky", aid, "books"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("fixes", g.id, "dash", "books"))
            lines.append(asp.fact("fixes", g.id, "dash", "cape"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    import storyworlds.asp as asp
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A literary superhero story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
        act = ACTIVITIES[args.activity]
        pr = PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES if gender == "girl" else HERO_NAMES + ["Ezra", "Theo"])
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, hero_name=name, hero_gender=gender, friend_name=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.hero_name, params.hero_gender, params.friend_name, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:10} {e.type:8} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


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
    StoryParams(place="library", activity="dash", prize="books", hero_name="Maya", hero_gender="girl", friend_name="Jun", trait="brave"),
    StoryParams(place="library", activity="lift", prize="books", hero_name="Ari", hero_gender="boy", friend_name="Tess", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            header = f"### {p.hero_name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
