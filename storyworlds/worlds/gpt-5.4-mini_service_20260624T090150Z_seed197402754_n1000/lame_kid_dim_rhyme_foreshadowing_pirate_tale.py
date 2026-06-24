#!/usr/bin/env python3
"""
A standalone story world for a tiny Pirate Tale: a kid-sized cabin deck,
a lame old leg, a rhyme, and a foreshadowed turn toward courage.

Seed image:
A small pirate kid with a sore, lame leg wants to join the ship's fun.
The crew notices the wobble, warns of a risky climb, and a clever helper
brings a safer way to cross the deck. The story should feel like a playful
pirate rhyme, with a little foreshadowing before the turn.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Harbor:
    place: str = "the little pirate ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    eases: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Harbor) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    goal: str
    aid: str
    name: str
    gender: str
    mate: str
    trait: str
    seed: Optional[int] = None


PLACES = {
    "deck": Harbor(place="the little pirate ship", affords={"sail", "dance"}),
    "dock": Harbor(place="the dock", affords={"sail", "dance"}),
    "cove": Harbor(place="the cove", affords={"sail", "dance"}),
}

GOALS = {
    "sail": Goal(
        id="sail",
        verb="climb the rigging",
        gerund="climbing the rigging",
        rush="scramble up the rope ladder",
        risk="tangled and sore",
        zone={"legs", "feet"},
        keyword="rigging",
        tags={"rope", "sea"},
    ),
    "dance": Goal(
        id="dance",
        verb="dance on the deck",
        gerund="dancing on the deck",
        rush="spin and hop aboard",
        risk="wobbly and bruised",
        zone={"legs"},
        keyword="deck",
        tags={"music", "sea"},
    ),
}

AIDS = {
    "crutch": Aid(
        id="crutch",
        label="a sturdy crutch",
        prep="take a sturdy crutch",
        tail="tapped along with the crutch",
        covers={"legs"},
        eases={"sore"},
    ),
    "boot": Aid(
        id="boot",
        label="a high boot brace",
        prep="strap on a high boot brace",
        tail="marched carefully with the boot brace",
        covers={"feet", "legs"},
        eases={"wobbly"},
    ),
    "rail": Aid(
        id="rail",
        label="the rail rope",
        prep="hold the rail rope",
        tail="held the rail rope and stepped slow",
        covers={"legs"},
        eases={"tangled"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Ria", "Tess", "Luna", "Pip", "Saila"]
BOY_NAMES = ["Finn", "Jack", "Bo", "Ned", "Kip", "Rory", "Toby"]
TRAITS = ["brave", "small", "bright-eyed", "cheeky", "determined"]


def rhyme_line(goal: Goal) -> str:
    return {
        "sail": "A sailor can wobble, but still reach the high; one step at a time, and he’ll touch the sky.",
        "dance": "A dancer can shuffle with toes in a row; a careful small shuffle is still quite a show.",
    }.get(goal.id, "A pirate can try, and a pirate can learn; a little safe step is a treasure to earn.")


def foreshadow_line(hero: Entity, goal: Goal) -> str:
    return {
        "sail": f"Even so, {hero.id}'s bad leg gave a tiny creak as the rope ladder swayed.",
        "dance": f"Even so, {hero.id}'s lame leg gave a tiny wobble when the deck went bump-bump-bump.",
    }.get(goal.id, f"Even so, {hero.id}'s sore leg gave a tiny hint that the deck might be tricky.")


def _risk(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["want"] = hero.memes.get("want", 0) + 1
    hero.memes["foreshadow"] = hero.memes.get("foreshadow", 0) + 1
    world.say(f"{hero.id} loved to {goal.verb}, and the whole crew knew it.")
    world.say(f"{rhyme_line(goal)}")
    world.say(foreshadow_line(hero, goal))


def _warn(world: World, mate: Entity, hero: Entity, goal: Goal) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    world.say(
        f'"Hold, mate," said {mate.id}, "that climb may end with a thud; '
        f'your {goal.risk} if you rush through the mud."'
    )


def _wistful(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["impatience"] = hero.memes.get("impatience", 0) + 1
    world.say(f"{hero.id} looked up anyway and tried to {goal.rush}.")
    world.say(f"But {hero.pronoun('possessive')} lame leg made the first step feel like a snail on a plank.")


def _offer_aid(world: World, mate: Entity, hero: Entity, goal: Goal) -> Optional[Aid]:
    for aid in AIDS.values():
        if goal.zone & aid.covers:
            world.say(
                f"{mate.id} smiled and said, "
                f'"{aid.prep}, and we’ll still {goal.verb} together."'
            )
            return aid
    return None


def _accept(world: World, hero: Entity, mate: Entity, goal: Goal, aid: Aid) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["calm"] = 1.0
    hero.memes["caution"] = 0.0
    world.say(f"{hero.id}'s face lit up, and {hero.pronoun()} grinned at {hero.pronoun('possessive')} mate.")
    world.say(
        f'They {aid.tail}. Soon {hero.id} was {goal.gerund}, '
        f"and the ship seemed to sing under their feet."
    )
    world.say(
        f"By sunset, {hero.id} could still feel the lame leg, but it was no longer the boss of the day."
    )


def tell(setting: Harbor, goal: Goal, hero_name: str, hero_type: str, mate_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait, "pirate", "lame"],
    ))
    mate = world.add(Entity(
        id="Mate",
        kind="character",
        type=mate_type,
        traits=["crew", "kind"],
    ))

    world.say(
        f"{hero.id} was a little pirate with a lame leg, small as a cabin cat and quick as a coin."
    )
    world.say(
        f"{hero.id} still wanted to {goal.verb} more than anything on the salt-blue sea."
    )
    world.say(
        f"{mate.id} watched over the deck and knew when a brave wish needed a gentler way."
    )

    world.para()
    world.say(f"One bright day aboard {setting.place}, the wind made the ropes hum.")
    _risk(world, hero, goal)
    _warn(world, mate, hero, goal)
    _wistful(world, hero, goal)

    world.para()
    aid = _offer_aid(world, mate, hero, goal)
    if aid is None:
        raise StoryError("No reasonable pirate aid fits this goal.")
    _accept(world, hero, mate, goal, aid)

    world.facts.update(
        hero=hero,
        mate=mate,
        goal=goal,
        aid=aid,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = PLACES
ACTIONS = GOALS
GADGETS = AIDS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for goal_id in setting.affords:
            goal = ACTIONS[goal_id]
            for aid_id, aid in GADGETS.items():
                if goal.zone & aid.covers:
                    combos.append((place, goal_id, aid_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with rhyme and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--prize", choices=GADGETS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mate", "captain"])
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
        raise StoryError("(No valid pirate story matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "mate"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, goal=activity, aid=prize, name=name, gender=gender, mate=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, goal = f["hero"], f["goal"]
    return [
        f'Write a short pirate tale for a young child about {hero.id}, a little pirate with a lame leg, who wants to {goal.verb}.',
        f'Write a rhyme-tinged story where {hero.id} faces a tricky sea-deck moment and a kind mate helps with a safer way.',
        f'Write a small story with foreshadowing about a pirate kid whose sore leg makes climbing hard, but who still finds courage.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, goal, aid = f["hero"], f["mate"], f["goal"], f["aid"]
    qa = [
        QAItem(
            question=f"Who is the pirate story about?",
            answer=f"It's about {hero.id}, a little pirate with a lame leg who still wanted to {goal.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the ship?",
            answer=f"{hero.id} wanted to {goal.verb}, and that wish carried the whole story.",
        ),
        QAItem(
            question=f"Why did {mate.id} speak up before {hero.id} rushed ahead?",
            answer=f"{mate.id} spoke up because {hero.id}'s lame leg and the swaying deck made the climb risky.",
        ),
        QAItem(
            question=f"What helped {hero.id} after the warning?",
            answer=f"{aid.label} helped {hero.id} move safely while still getting to {goal.verb}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {goal.gerund} and smiling because the safer plan worked.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "rope": [
        QAItem(
            question="What is a rope ladder?",
            answer="A rope ladder is a ladder made from rope, and pirates use it to climb up or down safely.",
        )
    ],
    "sea": [
        QAItem(
            question="Why do ships rock on the sea?",
            answer="Ships rock because water moves under them, so they tip and sway a little as they float.",
        )
    ],
    "music": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like ship and flip or sea and wee.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["goal"].tags)
    out: list[QAItem] = []
    for tag in ["rope", "sea", "music"]:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
goal_risky(G) :- goal(G), zone(G,R), aid(A), covers(A,R).
valid(Place,G,A) :- affords(Place,G), goal_risky(G), zone(G,R), covers(A,R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for g in sorted(p.affords):
            lines.append(asp.fact("affords", pid, g))
    for gid, g in ACTIONS.items():
        lines.append(asp.fact("goal", gid))
        for r in sorted(g.zone):
            lines.append(asp.fact("zone", gid, r))
    for aid, a in GADGETS.items():
        lines.append(asp.fact("aid", aid))
        for r in sorted(a.covers):
            lines.append(asp.fact("covers", aid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH:")
    if a - b:
        print(" only in asp:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.goal], params.name, params.gender, params.mate, params.trait)
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
    StoryParams(place="deck", goal="sail", aid="boot", name="Mira", gender="girl", mate="mate", trait="brave"),
    StoryParams(place="dock", goal="dance", aid="crutch", name="Finn", gender="boy", mate="mate", trait="cheeky"),
    StoryParams(place="cove", goal="sail", aid="rail", name="Nell", gender="girl", mate="mate", trait="determined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
