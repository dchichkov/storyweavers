#!/usr/bin/env python3
"""
A folk-tale storyworld about a hungry helper, a tempting salami, and the
gentle power of focus and friendship.

Seed tale premise:
A small animal promises to help a friend prepare for a village supper, but a
smell of salami keeps pulling attention away. The friend reminds the helper to
focus, they work together, and the happy ending proves that kindness and
attention can both be learned.
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
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    focus_need: str
    reward: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    help_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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


@dataclass
class Rule:
    name: str
    apply: callable


THRESHOLD = 1.0


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_distraction(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    if hero.memes.get("tempted", 0) < THRESHOLD:
        return out
    sig = ("distraction", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["focus"] = max(0.0, hero.memes.get("focus", 0.0) - 1.0)
    out.append(f"The smell of salami tugged at {hero.id}'s nose and made focus wobble.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    if hero.memes.get("focus", 0) < THRESHOLD or friend.memes.get("hope", 0) < THRESHOLD:
        return out
    sig = ("help", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["work"] = hero.meters.get("work", 0) + 1
    friend.meters["prepared"] = friend.meters.get("prepared", 0) + 1
    out.append(f"With steady eyes and a kind heart, {hero.id} finished the work beside {friend.id}.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    if hero.meters.get("work", 0) < THRESHOLD or friend.meters.get("prepared", 0) < THRESHOLD:
        return out
    sig = ("friendship", hero.id, friend.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0) + 1
    out.append(f"The two friends laughed, for the work was done and no one was left alone.")
    return out


CAUSAL_RULES = [
    Rule("distraction", _r_distraction),
    Rule("help", _r_help),
    Rule("friendship", _r_friendship),
]


def build_focus_world(world: World) -> None:
    propagate(world, narrate=False)


def reasonableness_gate(place: Place, task: Task, prize: Prize, gift: Gift) -> bool:
    if task.id not in place.affords:
        return False
    if task.keyword not in gift.tags:
        return False
    if prize.region != "torso" and task.id == "knead":
        return False
    return True


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PLACES = {
    "village_green": Place(name="the village green", indoors=False, affords={"deliver", "gather"}),
    "cottage_kitchen": Place(name="the cottage kitchen", indoors=True, affords={"slice", "share"}),
    "orchard_path": Place(name="the orchard path", indoors=False, affords={"carry", "deliver"}),
}

TASKS = {
    "deliver": Task(
        id="deliver",
        verb="deliver the supper basket",
        gerund="delivering the supper basket",
        rush="run toward the table and forget the basket",
        keyword="salami",
        focus_need="focus on the path and not the smell",
        reward="the supper would be ready on time",
        tags={"salami", "focus", "friendship"},
    ),
    "share": Task(
        id="share",
        verb="share the food fairly",
        gerund="sharing the food fairly",
        rush="snatch the best piece first",
        keyword="salami",
        focus_need="remember who needs a turn",
        reward="everyone would eat with a full heart",
        tags={"salami", "focus", "friendship"},
    ),
}

PRIZES = {
    "salami": Prize(
        id="salami",
        label="salami",
        phrase="a ring of fragrant salami",
        region="hands",
        genders={"boy", "girl"},
    ),
    "basket": Prize(
        id="basket",
        label="basket",
        phrase="a woven supper basket",
        region="hands",
        genders={"boy", "girl"},
    ),
}

GIFTS = {
    "salami_cloth": Gift(
        id="salami_cloth",
        label="a clean cloth wrap",
        phrase="a clean cloth wrap for the salami",
        help_line="wrap the salami so the smell would not wander so far",
        ending_line="the cloth wrap kept the temptation gentle and the table tidy",
        tags={"salami"},
    ),
    "focus_stone": Gift(
        id="focus_stone",
        label="a smooth focus stone",
        phrase="a smooth focus stone for keeping one promise in mind",
        help_line="hold a smooth focus stone and remember the promise",
        ending_line="the focus stone helped the helper keep a steady mind",
        tags={"focus"},
    ),
}

HEROES = [
    ("Pip", "boy", "curious"),
    ("Mara", "girl", "kind"),
    ("Tobin", "boy", "gentle"),
    ("Lina", "girl", "bright"),
]

FRIENDS = [
    ("Nell", "girl", "neighbor"),
    ("Otto", "boy", "friend"),
    ("Pera", "girl", "friend"),
    ("Jory", "boy", "friend"),
]

TRAITS = ["kind", "steady", "curious", "gentle", "brave"]


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    gift: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    friend_name: str
    friend_gender: str
    friend_trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("keyword", tid, t.keyword))
    for prid, pr in PRIZES.items():
        lines.append(asp.fact("prize", prid))
        lines.append(asp.fact("region", prid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, prid))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for tag in sorted(g.tags):
            lines.append(asp.fact("helps", gid, tag))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,T,R,G) :- affords(P,T), gift(G), task(T), prize(R),
                       keyword(T,K), helps(G,K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p, place in PLACES.items():
        for t, task in TASKS.items():
            for r, prize in PRIZES.items():
                for g, gift in GIFTS.items():
                    if reasonableness_gate(place, task, prize, gift):
                        out.append((p, t, r, g))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about salami, focus, friendship, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.task:
        combos = [c for c in combos if c[1] == args.task]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.gift:
        combos = [c for c in combos if c[3] == args.gift]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    p, t, r, g = rng.choice(sorted(combos))
    hero_name, hero_gender, hero_trait = rng.choice(HEROES)
    if args.hero_name:
        hero_name = args.hero_name
    if args.hero_gender:
        hero_gender = args.hero_gender
    friend_name, friend_gender, friend_trait = rng.choice(FRIENDS)
    if args.friend_name:
        friend_name = args.friend_name
    if args.friend_gender:
        friend_gender = args.friend_gender
    return StoryParams(
        place=p, task=t, prize=r, gift=g,
        hero_name=hero_name, hero_gender=hero_gender, hero_trait=hero_trait,
        friend_name=friend_name, friend_gender=friend_gender, friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    task = TASKS[params.task]
    prize = PRIZES[params.prize]
    gift = GIFTS[params.gift]

    if not reasonableness_gate(place, task, prize, gift):
        raise StoryError("Invalid story: the chosen gift does not fit the task and prize.")
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, meters={}, memes={}))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender, meters={}, memes={}))
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["task"] = task
    world.facts["prize"] = prize
    world.facts["gift"] = gift

    hero.memes["tempted"] = 1.0
    hero.memes["focus"] = 0.0
    friend.memes["hope"] = 1.0
    hero.meters["work"] = 0.0
    friend.meters["prepared"] = 0.0

    # Act I
    world.say(f"Once, in {place.name}, there lived {params.hero_name}, a {params.hero_trait} little {params.hero_gender} who loved to help.")
    world.say(f"{params.hero_name} was sent to {task.verb}, and {params.friend_name} asked for kindness and care.")
    world.say(f"But there was also {prize.phrase}, and its savory smell kept calling to the helper.")

    # Act II
    world.para()
    world.say(f"{params.hero_name} tried to keep {task.focus_need}, yet the scent of salami made attention drift.")
    world.say(f"{params.friend_name} smiled and said, \"{gift.help_line.capitalize()}.\"")
    hero.memes["focus"] = 1.0
    propagate(world, narrate=True)

    # Act III
    world.para()
    world.say(f"{params.hero_name} took a deep breath, chose {gift.label}, and remembered the promise to a friend.")
    hero.meters["work"] = 1.0
    friend.meters["prepared"] = 1.0
    hero.memes["focus"] = 2.0
    propagate(world, narrate=True)
    world.say(f"In the end, {gift.ending_line}, and {params.hero_name} and {params.friend_name} shared the supper with laughter.")
    world.say(f"The village folk said the little lesson was plain: a true friend helps us keep focus, and kindness brings a happy ending.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for children about {f["hero"].id}, salami, and the power of focus.',
        f"Tell a gentle friendship story where a helper is distracted by salami but learns to stay focused and finish a good deed.",
        f"Write a happy-ending tale in which a friend helps another friend keep a promise when a tempting salami smell appears.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    task = f["task"]
    prize = f["prize"]
    gift = f["gift"]
    return [
        QAItem(
            question=f"What did {hero.id} need to do in the story?",
            answer=f"{hero.id} needed to {task.verb}, even though {prize.phrase} was tempting.",
        ),
        QAItem(
            question=f"Who helped {hero.id} stay focused?",
            answer=f"{friend.id} helped by reminding {hero.id} to keep a steady mind and choose friendship over distraction.",
        ),
        QAItem(
            question=f"What good ending did the story have?",
            answer=f"{hero.id} finished the job, the friends shared the supper, and the tale ended happily with {gift.label}.",
        ),
        QAItem(
            question=f"Why was salami a problem?",
            answer="The smell of salami was so tempting that it pulled the helper's attention away from the promise.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is focus?",
            answer="Focus means keeping your mind on one task instead of letting other things pull your attention away.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone, helping them, and being kind to them when they need you.",
        ),
        QAItem(
            question="Why do people say a happy ending is nice?",
            answer="A happy ending is nice because the trouble gets solved and the characters finish in a safe, cheerful place.",
        ),
        QAItem(
            question="What is salami?",
            answer="Salami is a savory, seasoned sausage often sliced for food, and its smell can be very tempting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"place={world.place.name}")
    lines.append(f"fired={sorted(world.fired)}")
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
    StoryParams("village_green", "deliver", "basket", "focus_stone", "Pip", "boy", "curious", "Nell", "girl", "kind"),
    StoryParams("orchard_path", "deliver", "salami", "salami_cloth", "Mara", "girl", "gentle", "Otto", "boy", "friend"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
