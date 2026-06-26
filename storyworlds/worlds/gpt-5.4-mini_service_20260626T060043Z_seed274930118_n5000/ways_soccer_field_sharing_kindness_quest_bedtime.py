#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ways_soccer_field_sharing_kindness_quest_bedtime.py
=================================================================================================

A small bedtime-style storyworld set on a soccer field, built around ways of
sharing, kindness, and a little quest to make the evening feel fair.

The seed premise:
- A child arrives at the soccer field at bedtime.
- There is one favorite ball and one gentle wish to keep playing.
- Another child wants a turn.
- The first child must find a kind way to share before the lights come on and the
  evening gets sleepy.

This world is intentionally tiny and classical:
- physical state is tracked in meters
- emotional state is tracked in memes
- the story is driven by simulation, not by a frozen template
- the ending proves what changed

The featured narrative instrument is "ways":
- there are multiple ways to share
- the quest is to choose a good way
- the bedtime tone keeps the story soft and child-facing
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the soccer field"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class ShareWay:
    id: str
    label: str
    action: str
    ending: str
    boost: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


SETTINGS = {
    "soccer_field": Setting(place="the soccer field", affordances={"play_ball", "share_ball", "quest_kindness"}),
}

ACTIVITIES = {
    "play_ball": Activity(
        id="play_ball",
        verb="play with the ball",
        gerund="kicking the ball",
        rush="run toward the goal",
        keyword="ways",
        tags={"ball", "play", "ways"},
    ),
    "share_ball": Activity(
        id="share_ball",
        verb="share the ball",
        gerund="passing the ball",
        rush="keep the ball all to themselves",
        keyword="ways",
        tags={"sharing", "kindness", "ways"},
    ),
    "quest_kindness": Activity(
        id="quest_kindness",
        verb="find a kind way",
        gerund="looking for kind ways",
        rush="rush ahead without listening",
        keyword="ways",
        tags={"sharing", "kindness", "quest", "ways"},
    ),
}

PRIZES = {
    "ball": Prize(label="ball", phrase="a bright red soccer ball", type="ball", region="hands"),
    "lantern": Prize(label="lantern", phrase="a little bedtime lantern", type="lantern", region="hands"),
}

WAYS = [
    ShareWay(
        id="pass",
        label="passing turns",
        action="pass the ball back and forth",
        ending="They took turns kicking it, one gentle tap at a time",
        boost="turns",
    ),
    ShareWay(
        id="count",
        label="counting to three",
        action="count to three before each kick",
        ending="They counted to three and let the ball roll between them like a round moon",
        boost="patience",
    ),
    ShareWay(
        id="goal",
        label="sharing the goal",
        action="take turns aiming at the same goal",
        ending="They shared the goal and cheered for each other when the ball rolled true",
        boost="joy",
    ),
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Leo", "Ben", "Noah", "Eli", "Theo"]
TRAITS = ["gentle", "curious", "brave", "quiet", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: sharing, kindness, and a quest on a soccer field.")
    ap.add_argument("--place", choices=SETTINGS.keys(), default="soccer_field")
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affordances:
            for prize_id in PRIZES:
                if act_id in {"play_ball", "share_ball", "quest_kindness"} and prize_id == "ball":
                    combos.append((place, act_id, prize_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def choose_way(world: World, hero: Entity, friend: Entity, prize: Entity) -> ShareWay:
    if hero.memes.get("kindness", 0.0) < THRESHOLD:
        return WAYS[0]
    if friend.memes.get("waiting", 0.0) >= THRESHOLD:
        return WAYS[1]
    return WAYS[2]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={"wish": 1.0}))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.gender == "boy" else "boy", meters={}, memes={"hope": 1.0}))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="the parent", meters={}, memes={"sleepiness": 0.4}))
    prize = world.add(Entity(id="ball", type="ball", label="ball", phrase="a bright red soccer ball", owner=hero.id, caretaker=parent.id))

    hero.memes["love_play"] = 1.0
    hero.memes["kindness"] = 0.0
    hero.memes["tug"] = 1.0
    friend.memes["waiting"] = 1.0

    world.say(f"At the soccer field, {hero.id} loved the ball and the cool evening air.")
    world.say(f"{hero.pronoun().capitalize()} had a small bedtime wish to play just a little longer, because the night felt soft and calm.")
    world.say(f"{hero.id} and {friend.id} both noticed the same bright ball, and that made the moment feel important.")

    world.para()
    activity = ACTIVITIES[params.activity]
    world.say(f"{hero.id} wanted to {activity.verb}, but {friend.id} was waiting nearby with hopeful eyes.")
    if activity.id == "play_ball":
        world.say(f"The field lights were glowing, and there were many ways to play, but not every way was kind.")
    elif activity.id == "share_ball":
        world.say(f"The best way to keep the game gentle was to share, yet {hero.id} still had to choose it.")
    else:
        world.say(f"This was a little quest for kindness: the answer was not speed, but a thoughtful way.")
    hero.memes["worry"] = 1.0
    parent.memes["sleepiness"] = 0.8
    world.say(f"The parent watched the two children and whispered that bedtime stories are nicest when everyone gets a turn.")

    world.para()
    chosen = choose_way(world, hero, friend, prize)
    hero.memes["kindness"] += 1.0
    friend.memes["waiting"] = 0.0
    friend.memes["joy"] = 1.0
    hero.memes["joy"] = 1.0
    hero.memes["tug"] = 0.0

    world.say(f"{hero.id} found a kind way to share: {chosen.action}.")
    world.say(f"{chosen.ending}, and {friend.id} smiled as the ball moved between them.")
    world.say(f"Their little quest for kindness made the evening feel bigger and gentler at the same time.")

    world.para()
    parent.memes["sleepiness"] = 1.0
    world.say(f"At last, the parent called them in for bedtime, and {hero.id} felt warm inside from doing the kind thing.")
    world.say(f"The ball rested by the fence, the field grew quiet, and {hero.id} knew there were always more ways to share tomorrow.")

    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, activity=activity, way=chosen)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    return [
        f"Write a bedtime story about {hero.id} and {friend.id} finding ways to share a ball at the soccer field.",
        f"Tell a gentle story where a child wants to {activity.verb} but learns a kind way before bedtime.",
        f"Write a short bedtime tale that includes the word 'ways' and ends with sharing and kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    activity = f["activity"]
    way = f["way"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, who wanted to play at the soccer field before bedtime.",
        ),
        QAItem(
            question=f"What did {hero.id} need to learn about the ball?",
            answer=f"{hero.id} needed to learn a kind way to share the ball with {friend.id}.",
        ),
        QAItem(
            question=f"What was the little quest in the story?",
            answer=f"The little quest was to find a kind way to share, and the chosen way was {way.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} sharing the ball calmly while bedtime got near.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a soccer field for?", answer="A soccer field is a place where people run, kick a ball, and play soccer."),
        QAItem(question="What does kindness mean?", answer="Kindness means being gentle, helpful, and caring about other people."),
        QAItem(question="What does sharing mean?", answer="Sharing means letting someone else use something too, so everyone can have a turn."),
        QAItem(question="What is bedtime?", answer="Bedtime is the time when children get ready to rest and sleep."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), needs_sharing(A), ball(P).
valid_story(Place,A,P) :- afford(Place,A), prize_at_risk(A,P), usable_way(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("afford", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
        if "sharing" in act.tags:
            lines.append(asp.fact("needs_sharing", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
        if pid == "ball":
            lines.append(asp.fact("ball", pid))
    lines.append(asp.fact("usable_way", "share_ball"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("python-only:", sorted(python_set - asp_set))
    print("asp-only:", sorted(asp_set - python_set))
    return 1


CURATED = [
    StoryParams(place="soccer_field", activity="share_ball", prize="ball", name="Mia", gender="girl", friend="Leo", trait="gentle"),
    StoryParams(place="soccer_field", activity="quest_kindness", prize="ball", name="Noah", gender="boy", friend="Ava", trait="thoughtful"),
    StoryParams(place="soccer_field", activity="play_ball", prize="ball", name="Lily", gender="girl", friend="Ben", trait="curious"),
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, friend=friend, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
