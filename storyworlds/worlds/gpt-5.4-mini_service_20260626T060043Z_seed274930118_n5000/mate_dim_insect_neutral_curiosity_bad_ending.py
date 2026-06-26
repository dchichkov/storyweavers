#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mate_dim_insect_neutral_curiosity_bad_ending.py
================================================================================

A small folk-tale storyworld about curiosity, a quest, a dimming lantern, and
an insect encounter that turns the ending sour.

Seed tale sketch:
---
A curious child and their mate set out on a quest to fetch a silver charm from
the old hill. A neutral gray lantern gave them light. Along the way, they saw a
strange insect with bright wings. The child grew curious, followed it off the
path, and the lantern grew dim. By the time they found their way back, the
charm was gone and the quest had failed.
---

World model:
- The hero has a curiosity meme that can rise.
- The quest advances through places; the insect can lure the hero away.
- The lantern has physical light meters; following the insect drains light.
- A neutral helper/gear can protect against a bad turn, but only if the quest
  choice actually includes it.
- The ending is intentionally a bad ending, but still complete and causal.

Style target:
- Folk-tale cadence, concrete child-facing prose, short complete story arcs.
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
    plural: bool = False
    protective: bool = False
    neutral: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"light": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "loss": 0.0, "hope": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "maiden"}
        male = {"boy", "father", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford_quest: bool
    afford_insect: bool = True


@dataclass
class Quest:
    id: str
    title: str
    verb: str
    gerund: str
    turns: str
    prize: str
    prize_phrase: str
    danger: str
    lost_reason: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    label: str
    role: str
    neutral: bool = False
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def valid_quest(setting: Setting, quest: Quest) -> bool:
    return setting.afford_quest and quest.prize != ""


def quest_at_risk(quest: Quest) -> bool:
    return True


def select_neutral_helper(quest: Quest) -> Optional[Companion]:
    for helper in HELPERS:
        if helper.neutral:
            return helper
    return None


def advance(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if actor.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("wander", actor.id, quest.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.meters["light"] = max(0.0, actor.meters["light"] - 1.0)
    actor.memes["worry"] += 1.0
    actor.memes["loss"] += 1.0
    out.append(
        f"{actor.id} followed the insect's shimmer off the path, and the lantern light grew dim."
    )
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, quest: Quest, companion: Companion,
         hero_name: str = "Mara", hero_type: str = "girl",
         mate_name: str = "Pip", mate_type: str = "boy") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        label=hero_name, meters={"light": 2.0}, memes={"curiosity": 0.0, "worry": 0.0, "loss": 0.0, "hope": 1.0}
    ))
    mate = world.add(Entity(
        id=mate_name, kind="character", type=mate_type,
        label=mate_name, meters={"light": 1.0}, memes={"curiosity": 0.0, "worry": 0.0, "loss": 0.0, "hope": 1.0}
    ))
    lantern = world.add(Entity(
        id="lantern", type="lantern", label="neutral gray lantern",
        phrase="a neutral gray lantern", caretaker=hero.id,
        neutral=True, covers={"light"}, meters={"light": 3.0}
    ))
    insect = world.add(Entity(
        id="insect", kind="character", type="insect", label="bright-winged insect",
        phrase="a bright-winged insect", plural=False, meters={"light": 0.0}
    ))
    helper = world.add(Entity(
        id=companion.id, type="companion", label=companion.label, phrase=companion.label,
        neutral=companion.neutral, plural=companion.plural
    ))

    world.say(
        f"Once in the old folk-tale days, {hero.id} and {mate.id} set out on a {quest.title} quest, "
        f"carrying {lantern.phrase} to light their way."
    )
    world.say(
        f"{hero.id} was a curious little {hero_type} who wanted to {quest.verb}, and {mate.id} "
        f"walked beside {hero.pronoun('object')} like a steady friend."
    )
    world.say(
        f"They hoped the {quest.prize} would wait at the end of the hill path."
    )

    world.para()
    world.say(
        f"At the edge of {setting.place}, the air felt still, and a strange insect drifted by the reeds."
    )
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} grew curious about {quest.danger}, even though {mate.id} said, "
        f'"Keep to the path, and keep the lantern near."'
    )
    advance(world, hero, quest)

    world.para()
    if lantern.meters["light"] < THRESHOLD:
        world.say(
            f"By the time {hero.id} came back, the lantern was dim, the path was hard to see, "
            f"and the silver {quest.prize} was nowhere in sight."
        )
    else:
        world.say(
            f"The lantern stayed only half-bright, but the insect had still led {hero.id} too far."
        )
    world.say(
        f"Their quest ended in a bad way: {quest.lost_reason}, and {mate.id} could only hold the quiet lantern."
    )
    world.say(
        f"At last, {hero.id} and {mate.id} went home with empty hands and a dim light between them."
    )

    world.facts.update(
        hero=hero,
        mate=mate,
        lantern=lantern,
        insect=insect,
        helper=helper,
        quest=quest,
        setting=setting,
        bad_ending=True,
    )
    return world


SETTINGS = {
    "hill": Setting(place="the old hill", afford_quest=True, afford_insect=True),
    "wood": Setting(place="the little wood", afford_quest=True, afford_insect=True),
    "meadow": Setting(place="the quiet meadow", afford_quest=True, afford_insect=True),
}

QUESTS = {
    "charm": Quest(
        id="charm",
        title="silver-charm",
        verb="find the silver charm",
        gerund="finding the silver charm",
        turns="turns toward the bright thing",
        prize="charm",
        prize_phrase="a silver charm",
        danger="the insect's bright wings",
        lost_reason="the charm had been taken by shadow and thorn",
        tags={"quest", "curiosity", "insect", "dim", "neutral"},
    ),
    "ring": Quest(
        id="ring",
        title="ring-finding",
        verb="bring back the lost ring",
        gerund="bringing back the lost ring",
        turns="turns toward the fluttering light",
        prize="ring",
        prize_phrase="a small iron ring",
        danger="the insect's glittering flight",
        lost_reason="the ring slipped under roots and could not be found again",
        tags={"quest", "curiosity", "insect", "dim", "neutral"},
    ),
    "seed": Quest(
        id="seed",
        title="seed-seeking",
        verb="seek the moon seed",
        gerund="seeking the moon seed",
        turns="turns toward the wingbeat",
        prize="seed",
        prize_phrase="a pale moon seed",
        danger="the insect's glow in the grass",
        lost_reason="the moon seed was lost in the dark grass before they could reach it",
        tags={"quest", "curiosity", "insect", "dim", "neutral"},
    ),
}

HELPERS = [
    Companion(id="companion", label="neutral friend", role="companion", neutral=True),
    Companion(id="mate", label="mate", role="mate", neutral=False),
]

GIRL_NAMES = ["Mara", "Nia", "Lina", "Tessa", "Ivy"]
BOY_NAMES = ["Pip", "Milo", "Jory", "Owen", "Tobin"]
TRAITS = ["curious", "gentle", "bright-eyed", "stubborn", "quick"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    gender: str
    mate_name: str
    mate_gender: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    return [
        f'Write a folk-tale story about a curious {hero.type} named {hero.id} on a {quest.title} quest.',
        f'Tell a short story where an insect makes a child leave the path and the lantern grows dim.',
        f'Write a gentle but bad-ending quest story that uses the words "mate", "insect", and "neutral".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    quest = f["quest"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who went on the quest at {setting.place}?",
            answer=f"{hero.id} and {mate.id} went together on the quest at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the journey?",
            answer=f"{hero.id} wanted to {quest.verb}, but curiosity about the insect pulled {hero.pronoun('object')} off the path.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly: the lantern went dim, the {quest.prize} was lost, and {hero.id} and {mate.id} returned home empty-handed.",
        ),
    ]
    if f.get("bad_ending"):
        qa.append(
            QAItem(
                question=f"Why did the lantern matter on the road?",
                answer="The lantern mattered because it gave them light on the path, and when it grew dim, the way back became hard to see.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an insect?",
            answer="An insect is a tiny animal with six legs. Many insects can fly or crawl, and some have bright wings.",
        ),
        QAItem(
            question="What does dim mean?",
            answer="Dim means not very bright. A dim lantern gives only a little light.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find something, do a task, or reach a goal.",
        ),
        QAItem(
            question="What does neutral mean here?",
            answer="Neutral means calm and not picking a side. A neutral object does not help one choice over another by itself.",
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.neutral:
            bits.append("neutral=True")
        out.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(out)


def explain_rejection(setting: Setting, quest: Quest) -> str:
    return f"(No story: the {quest.title} quest does not fit {setting.place}.)"


CURATED = [
    StoryParams(place="hill", quest="charm", name="Mara", gender="girl", mate_name="Pip", mate_gender="boy", trait="curious"),
    StoryParams(place="wood", quest="ring", name="Ivy", gender="girl", mate_name="Milo", mate_gender="boy", trait="bright-eyed"),
    StoryParams(place="meadow", quest="seed", name="Tessa", gender="girl", mate_name="Jory", mate_gender="boy", trait="stubborn"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest:
        if not valid_quest(SETTINGS[args.place], QUESTS[args.quest]):
            raise StoryError(explain_rejection(SETTINGS[args.place], QUESTS[args.quest]))
    places = [k for k, v in SETTINGS.items() if args.place is None or k == args.place]
    quests = [k for k in QUESTS if args.quest is None or k == args.quest]
    if not places or not quests:
        raise StoryError("No valid combination matches the given options.")
    place = rng.choice(places)
    quest = rng.choice(quests)
    gender = args.gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mate_name = args.mate_name or rng.choice(GIRL_NAMES if mate_gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, gender=gender, mate_name=mate_name, mate_gender=mate_gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], QUESTS[params.quest], HELPERS[0],
                 hero_name=params.name, hero_type=params.gender,
                 mate_name=params.mate_name, mate_type=params.mate_gender)
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
quest_place(P,Q) :- setting(P), quest(Q), afford_quest(P,Q).
curious_turn(Q) :- quest(Q).
bad_ending(P,Q) :- quest_place(P,Q), curious_turn(Q).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_quest:
            lines.append(asp.fact("afford_quest", sid))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("quest_title", qid, q.title))
        lines.append(asp.fact("quest_tag", qid, "curiosity"))
        lines.append(asp.fact("quest_tag", qid, "insect"))
        lines.append(asp.fact("quest_tag", qid, "dim"))
        lines.append(asp.fact("quest_tag", qid, "neutral"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_place/2."))
    return sorted(set(asp.atoms(model, "quest_place")))


def asp_verify() -> int:
    py = {(p, q) for p, s in SETTINGS.items() for q, qu in QUESTS.items() if valid_quest(s, qu)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale quest world with curiosity and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--mate-name")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show quest_place/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible quest settings:\n")
        for p, q in combos:
            print(f"  {p:10} {q}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
