#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about a little team, a wonky noggin, a pair of
binoculars, and a footie ball that rolls away until everyone works together and
makes up.
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
# Core entities
# ---------------------------------------------------------------------------
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Params and registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    hero: str
    friend: str
    prize: str
    seed: Optional[int] = None


SETTINGS = {
    "nursery": "the nursery",
    "meadow": "the meadow",
    "playroom": "the playroom",
}

HEROES = {
    "noggin": {
        "type": "girl",
        "label": "Noggin",
        "phrase": "a little girl with a brave smile and a wobbly noggin",
        "traits": ["small", "gentle", "cheery"],
    },
    "pip": {
        "type": "boy",
        "label": "Pip",
        "phrase": "a little boy with quick feet and a bouncy grin",
        "traits": ["small", "lively", "kind"],
    },
    "moss": {
        "type": "girl",
        "label": "Moss",
        "phrase": "a little girl with soft curls and a warm heart",
        "traits": ["small", "curious", "kind"],
    },
}

FRIENDS = {
    "binocular": {
        "type": "owl",
        "label": "Binocular",
        "phrase": "a wise little owl with bright binocular eyes",
    },
    "pocket": {
        "type": "rabbit",
        "label": "Pocket",
        "phrase": "a busy little rabbit with a tidy pocket apron",
    },
    "lark": {
        "type": "bird",
        "label": "Lark",
        "phrase": "a singing little bird with a silver wing",
    },
}

PRIZES = {
    "footie": {
        "type": "ball",
        "label": "footie",
        "phrase": "a round footie ball striped in red and blue",
    },
    "kite": {
        "type": "kite",
        "label": "kite",
        "phrase": "a paper kite with a long green tail",
    },
    "hoop": {
        "type": "hoop",
        "label": "hoop",
        "phrase": "a shiny hoop with a ribbon on it",
    },
}

FEATURES = {
    "reconciliation": "reconciliation",
    "teamwork": "teamwork",
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.hero not in HEROES:
        raise StoryError("Unknown hero.")
    if params.friend not in FRIENDS:
        raise StoryError("Unknown friend.")
    if params.prize not in PRIZES:
        raise StoryError("Unknown prize.")

    world = World(setting=SETTINGS[params.setting])

    hero_cfg = HEROES[params.hero]
    friend_cfg = FRIENDS[params.friend]
    prize_cfg = PRIZES[params.prize]

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_cfg["type"],
        label=hero_cfg["label"],
        phrase=hero_cfg["phrase"],
        meters={"bounce": 1.0},
        memes={"hope": 1.0, "worry": 0.0, "hurt": 0.0, "kindness": 1.0},
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_cfg["type"],
        label=friend_cfg["label"],
        phrase=friend_cfg["phrase"],
        meters={"attention": 1.0},
        memes={"pride": 1.0, "worry": 0.0, "hurt": 0.0, "kindness": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg["type"],
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        owner=hero.id,
        caretaker=friend.id,
        meters={"rolling": 1.0, "dust": 0.0},
        memes={"shine": 1.0},
    ))

    world.facts.update(hero=hero, friend=friend, prize=prize, params=params)
    return world


def _nesting_rhyme(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(
        f"In {world.setting}, when morning was mild, {hero.phrase} came in with a smile."
    )
    world.say(
        f"By {hero.pronoun('possessive')} ear rode {friend.phrase}, and in {friend.pronoun('possessive')} paw sat the {prize.label} so spry and so dialed."
    )


def _scene_turn(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    hero.memes["worry"] += 1.0
    friend.memes["pride"] += 1.0
    prize.meters["rolling"] += 1.0
    world.say(
        f"But the {prize.label} rolled under a bench with a flip, and {hero.label} said, "
        f"\"Oh dear, my noggin feels wrong on this trip.\""
    )
    world.say(
        f"{friend.label} peered through {friend.label.lower()}'s binoculars and frowned at the shade, "
        f"for the ball had rolled where the daylight had swayed."
    )
    world.say(
        f"{hero.label} wanted it back at once, with a dash, but {friend.label} said, "
        f"\"Wait now, let's not make a bash.\""
    )
    hero.memes["hurt"] += 1.0
    friend.memes["hurt"] += 1.0


def _reconcile(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    hero.memes["kindness"] += 1.0
    friend.memes["kindness"] += 1.0
    hero.memes["hurt"] = 0.0
    friend.memes["hurt"] = 0.0
    world.say(
        f"Then {hero.label} took a breath, soft and slow, and said, \"I was cross.\""
    )
    world.say(
        f"{friend.label} blinked at the bump in the moss, then said, \"I was hasty. Let's not let us toss.\""
    )
    world.say(
        f"They touched paws and smiled, making peace on the spot, and the moon of their friendship grew round and quite hot."
    )


def _teamwork(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    hero.meters["reach"] = 1.0
    friend.meters["lift"] = 1.0
    prize.meters["rolling"] = 0.0
    prize.meters["dust"] = 0.0
    prize.worn_by = None
    world.say(
        f"{hero.label} held the bench tight while {friend.label} peered with care, "
        f"and together they lifted the ball from its lair."
    )
    world.say(
        f"{hero.label} rolled it to sunlight; {friend.label} gave a cheer. "
        f"With teamwork and laughter, the prize reappeared."
    )
    world.say(
        f"Then {hero.label} and {friend.label} shared the {prize.label} and the day, "
        f"and the worry went skipping far, far away."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = world.get("hero")
    friend = world.get("friend")
    prize = world.get("prize")
    _nesting_rhyme(world, hero, friend, prize)
    world.para()
    _scene_turn(world, hero, friend, prize)
    world.para()
    _reconcile(world, hero, friend, prize)
    _teamwork(world, hero, friend, prize)
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    return [
        'Write a short nursery-rhyme story about a child, a lost footie, and a peaceful making-up.',
        f"Tell a gentle rhyme where {hero.label} and {friend.label} must use teamwork to rescue the {prize.label}.",
        f"Write a tiny story in a sing-song style that includes the words noggin, binocular, and footie.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    return [
        QAItem(
            question=f"Who was the story mainly about?",
            answer=f"The story was about {hero.label}, and {friend.label} helped too.",
        ),
        QAItem(
            question=f"What got stuck under the bench?",
            answer=f"The {prize.label} got stuck under the bench.",
        ),
        QAItem(
            question=f"What did {friend.label} use to look for the ball?",
            answer=f"{friend.label} used binoculars to look for the ball.",
        ),
        QAItem(
            question="How did the two friends fix the problem?",
            answer="They made up, worked together, and lifted the ball back into the sunlight.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are binoculars for?",
            answer="Binoculars are for looking at faraway things more closely.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together to do a job.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace after a disagreement and becoming friends again.",
        ),
        QAItem(
            question="What is a footie?",
            answer="A footie is a ball that children can kick, roll, or chase during play.",
        ),
        QAItem(
            question="What is a noggin?",
            answer="A noggin is a playful word for a head.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(hero).
friend(friend).
prize(prize).

feature(reconciliation).
feature(teamwork).

place(nursery).
place(meadow).
place(playroom).

can_happen(Place, hero, friend, prize) :- place(Place).
needs(hero, prize).
helps(friend, prize).
resolved(Place, hero, friend, prize) :- can_happen(Place, hero, friend, prize),
                                        feature(reconciliation),
                                        feature(teamwork).
#show resolved/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("place", k))
    for k in FEATURES:
        lines.append(asp.fact("feature", k))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("friend", "friend"))
    lines.append(asp.fact("prize", "prize"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_resolved() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/4."))
    return sorted(set(asp.atoms(model, "resolved")))


def python_resolved() -> list[tuple]:
    return [("nursery", "hero", "friend", "prize"),
            ("meadow", "hero", "friend", "prize"),
            ("playroom", "hero", "friend", "prize")]


def asp_verify() -> int:
    a = set(asp_resolved())
    p = set(python_resolved())
    if a == p:
        print(f"OK: ASP matches Python ({len(a)} resolved stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: noggin, binocular, footie.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--prize", choices=PRIZES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or "noggin"
    friend = args.friend or "binocular"
    prize = args.prize or "footie"
    return StoryParams(setting=setting, hero=hero, friend=friend, prize=prize)


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


CURATED = [
    StoryParams(setting="nursery", hero="noggin", friend="binocular", prize="footie"),
    StoryParams(setting="meadow", hero="noggin", friend="pocket", prize="footie"),
    StoryParams(setting="playroom", hero="moss", friend="lark", prize="kite"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_resolved()
        print(f"{len(triples)} resolved story patterns:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
