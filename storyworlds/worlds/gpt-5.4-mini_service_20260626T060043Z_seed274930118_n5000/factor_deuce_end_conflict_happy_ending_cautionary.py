#!/usr/bin/env python3
"""
storyworlds/worlds/factor_deuce_end_conflict_happy_ending_cautionary.py
=======================================================================

A small, self-contained storyworld about a fair game, a tense tie, and a
cautionary choice that leads to a happy ending.

Seed tale premise:
- A child and a friend are playing a simple counting game.
- The score becomes a deuce, so the next move matters.
- One child gets upset and wants to bend the rules.
- A grown-up explains the factor that truly matters: fairness.
- The children choose the kinder path, and the game ends well.

Style:
- Rhyming Story
- Conflict
- Happy Ending
- Cautionary
"""

from __future__ import annotations

import argparse
import dataclasses
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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
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
    factor: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    gender: str
    seed: Optional[int] = None


SETTINGS = {
    "playroom": Setting(place="the playroom", indoor=True, affords={"counting_game"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"counting_game"}),
    "porch": Setting(place="the porch", indoor=True, affords={"counting_game"}),
}

ACTIVITIES = {
    "counting_game": Activity(
        id="counting_game",
        verb="play the counting game",
        gerund="playing the counting game",
        rush="grab the last token",
        mess="spilled_tokens",
        soil="all mixed up",
        factor="fair play",
        keyword="deuce",
        tags={"deuce", "factor", "end", "fairness"},
    )
}

PRIZES = {
    "tokens": Prize(
        label="tokens",
        phrase="two bright counting tokens",
        type="tokens",
        plural=True,
    ),
    "cards": Prize(
        label="cards",
        phrase="a little deck of number cards",
        type="cards",
        plural=True,
    ),
}

NAMES = {
    "girl": ["Mina", "Lila", "Nora", "June", "Mara"],
    "boy": ["Eli", "Toby", "Finn", "Theo", "Ben"],
    "friend": ["Ari", "Sam", "Pip", "Noel", "Tess"],
}


ASP_RULES = r"""
valid_story(Place, Activity, Prize) :- setting(Place), activity(Activity), prize(Prize), affords(Place, Activity).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoor:
            lines.append(asp.fact("indoor", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("topic", aid, tag))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, pr) for p, s in SETTINGS.items() for a in s.affords for pr in PRIZES]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about deuce, fairness, and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    if args.place and args.activity and args.activity not in SETTINGS[args.place].affords:
        raise StoryError("That activity does not fit that place.")
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "counting_game"
    prize = args.prize or rng.choice(list(PRIZES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    friend = args.friend or rng.choice(NAMES["boy" if gender == "girl" else "girl"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, friend=friend, gender=gender)


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add(Entity(id=params.friend, kind="character", type="friend"))
    prize = world.add(Entity(id="prize", type=params.prize, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    act = ACTIVITIES[params.activity]

    hero.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0

    world.say(
        f"In {world.setting.place}, {hero.id} and {friend.id} began to grin, "
        f"for a counting game was starting within."
    )
    world.say(
        f"They held up {prize.phrase}, all shiny and neat, "
        f"and sang, \"Let's count nice and fair, with a gentle beat!\""
    )

    world.para()
    hero.memes["desire"] = 1.0
    hero.memes["conflict"] = 1.0
    world.say(
        f"The score fell to deuce, and the game felt tight; "
        f"{hero.id} wanted the win, and wanted it right."
    )
    world.say(
        f"But when the last token slid near the end, "
        f"{hero.id} tried to {act.rush}, which upset the friend."
    )

    world.para()
    hero.memes["guilt"] = 1.0
    world.say(
        f"The grown-up said, \"Child, the key factor is fair; "
        f"if you snatch for the end, you will make a sad snare.\""
    )
    world.say(
        f"\"A deuce means two sides must both get their say; "
        f"the kindest road home is the honest way.\""
    )

    world.para()
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["care"] = 1.0
    world.say(
        f"So {hero.id} took a breath, then smiled a new smile, "
        f"and shared the last turn in a patient style."
    )
    world.say(
        f"They finished the game, and the end came near; "
        f"the tokens stayed tidy, and both hearts were clear."
    )
    world.say(
        f"Now the lesson was bright, like a lantern in sight: "
        f"fair play keeps the day both cozy and light."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        activity=act,
        setting=world.setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        "Write a short rhyming story for a small child about fairness, a deuce, and a happy ending.",
        f"Tell a gentle rhyming tale where {hero.id} and {friend.id} learn that the real factor is being fair.",
        "Create a cautionary story in simple rhymes where a tense game ends with sharing instead of snatching.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    act = f["activity"]
    return [
        QAItem(
            question=f"Who was in the story playing the counting game?",
            answer=f"{hero.id} and {friend.id} were the children playing together.",
        ),
        QAItem(
            question="What made the game feel tense?",
            answer="The game reached deuce, so the next move mattered a lot and made everyone feel the pressure.",
        ),
        QAItem(
            question="What was the cautionary lesson?",
            answer="The lesson was that snatching for the end can cause trouble, but fair play leads to a happier ending.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} sharing the turn, the game finishing cleanly, and everyone feeling glad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does deuce mean in a game?",
            answer="Deuce means the score is tied and the next move can matter a lot.",
        ),
        QAItem(
            question="What does fair play mean?",
            answer="Fair play means following the rules and giving each side a proper chance.",
        ),
        QAItem(
            question="What is a factor?",
            answer="A factor is something that helps explain why something happens or what matters in a choice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, a, pr in combos:
            print(f"  {p:9} {a:14} {pr}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            for prize in PRIZES:
                params = StoryParams(place=place, activity="counting_game", prize=prize, name="Mina", friend="Ari", gender="girl")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
