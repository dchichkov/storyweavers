#!/usr/bin/env python3
"""
A fairy-tale storyworld about a fuzzy little class, a repeated mistake, and a friendship that repairs it.

The seed premise:
- A child enters a converse-tion-al class in a fairy-tale school.
- A helpful friend tries to help, but repetition makes the mistake bigger.
- The pair learns to pause, speak kindly, and repeat the right words together.

This world keeps the prose child-facing and state-driven:
- physical state: fuzz, ink, bells, ribbons, and a classroom scene
- emotional state: worry, embarrassment, friendship, relief, delight
- a repeated action can spread fuzz across papers and make the class feel chaotic
- a friend can help with a calm practice that turns the repetition into a new habit
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
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "princess", "fairy"}
        male = {"boy", "father", "dad", "man", "prince", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps_with: set[str] = field(default_factory=set)
    repeats: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _tone_fairy(place: str) -> str:
    return {
        "schoolhouse": "The little schoolhouse stood like a candle in the woods.",
        "tower_room": "The tower room glowed softly behind its round window.",
        "garden_room": "The garden room was warm, with vines around the sill.",
    }.get(place, f"{place.capitalize()} waited quietly for the lesson.")


def _introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"Once upon a time, in a {world.setting.place}, there was a {hero.type} named {hero.id}. "
        f"{hero.pronoun().capitalize()} had a soft fuzz on {hero.pronoun('possessive')} sleeves and a kind heart for {friend.id}."
    )
    world.say(
        f"{friend.id} was {friend.type} who loved sitting beside {hero.id} in the converse-tion-al class."
    )


def _love_class(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    world.say(
        f"{hero.id} loved the class because every gentle question felt like a door opening in a storybook."
    )
    world.say(
        f"{friend.id} loved it too, and {friend.id} always smiled when the children practiced words together."
    )


def _show_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(
        f"One day, {hero.id}'s {prize.label} shone bright and neat, and {hero.id} wore {prize.it()} to class with pride."
    )


def _begin_lesson(world: World, hero: Entity) -> None:
    world.say(_tone_fairy(world.setting.place))
    world.say(
        f"In the class, the teacher asked everyone to speak a line, then speak it again, and again, to learn the song of words."
    )
    world.facts["repetition"] = True


def _warn(world: World, hero: Entity, prize: Entity, act: Activity) -> None:
    world.say(
        f"But {hero.id} kept trying to {act.verb}, and each time the little fuzz on {hero.pronoun('possessive')} sleeves brushed the desk."
    )
    world.say(
        f'"If you keep that up, your {prize.label} will get {act.soil}," the teacher said with a worried frown.'
    )
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.facts["warning"] = True


def _repeat_mistake(world: World, hero: Entity, prize: Entity, act: Activity) -> None:
    hero.meters[act.mess] = hero.meters.get(act.mess, 0.0) + 1
    prize.meters[act.mess] = prize.meters.get(act.mess, 0.0) + 1
    world.say(
        f"{hero.id} tried once more, and then again, and the fuzz from {hero.pronoun('possessive')} sleeves puffed into the air like a tiny cloud."
    )
    world.say(
        f"The repeated brushing left {hero.pronoun('possessive')} {prize.label} {act.soil}."
    )
    world.facts["soiled"] = True


def _friendship_turn(world: World, hero: Entity, friend: Entity, prize: Entity, fix: Fix) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1
    friend.memes["kindness"] = friend.memes.get("kindness", 0.0) + 1
    world.say(
        f"{friend.id} stepped close and said, 'We can fix this together.'"
    )
    world.say(
        f'"Let us {fix.prep}," {friend.id} said, ' +
        f'"and then we will {fix.tail}."'
    )
    world.facts["friendship"] = True


def _clean_and_practice(world: World, hero: Entity, friend: Entity, prize: Entity, act: Activity, fix: Fix) -> None:
    hero.meters[act.mess] = 0.0
    prize.meters[act.mess] = 0.0
    hero.memes["embarrassment"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    world.say(
        f"They wiped the desk clean, and {hero.id}'s heart felt lighter at once."
    )
    world.say(
        f"Then {hero.id} and {friend.id} repeated the kind words together, one slow time and then one more time, until the lesson sounded sweet."
    )
    world.say(
        f"At the end, {hero.id} kept {prize.it()} neat, and the little class felt calm as a lullaby."
    )


SETTINGS = {
    "schoolhouse": Setting(place="schoolhouse", indoor=True, affords={"class"}),
    "tower_room": Setting(place="tower_room", indoor=True, affords={"class"}),
    "garden_room": Setting(place="garden_room", indoor=True, affords={"class"}),
}

ACTIVITIES = {
    "class": Activity(
        id="class",
        verb="join the lesson too quickly",
        gerund="joining the lesson",
        rush="rush to repeat the words",
        mess="fuzzy",
        soil="fuzz-covered",
        keyword="class",
        tags={"class", "repetition", "fuzz"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a clean silver cloak", type="cloak"),
    "book": Prize(label="book", phrase="a neat little storybook", type="book"),
    "ribbon": Prize(label="ribbon", phrase="a bright ribbon", type="ribbon"),
}

FIXES = {
    "brush": Fix(
        id="brush",
        label="soft brush",
        prep="brush the fuzz away first",
        tail="say the words again with clean sleeves",
        helps_with={"fuzzy"},
        repeats=True,
    ),
    "shake": Fix(
        id="shake",
        label="gentle shake",
        prep="shake off the fuzz and sit still",
        tail="practice the line once more together",
        helps_with={"fuzzy"},
        repeats=True,
    ),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    friend: str
    parent: str
    trait: str
    seed: Optional[int] = None


NAMES = ["Mira", "Luna", "Elsa", "Nia", "Pip", "Tobin", "Rowan", "Ivo"]
FRIENDS = ["Otto", "June", "Penny", "Bram", "Iris", "Milo"]
TRAITS = ["gentle", "curious", "brave", "cheerful", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for prize_id in PRIZES:
                out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about fuzz, repetition, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father", "teacher", "aunt"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid fairy-tale classroom combination matches the given options.")
    place, activity, prize = rng.choice(combos)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=args.name or rng.choice(NAMES),
        friend=args.friend or rng.choice(FRIENDS),
        parent=args.parent or rng.choice(["mother", "father", "teacher", "aunt"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="child", traits=[params.trait]))
    friend = world.add(Entity(id=params.friend, kind="character", type="child", traits=["kind"]))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase))
    act = ACTIVITIES[params.activity]

    _introduce(world, hero, friend)
    _love_class(world, hero, friend)
    world.para()
    _show_prize(world, hero, prize)
    _begin_lesson(world, hero)
    _warn(world, hero, prize, act)
    _repeat_mistake(world, hero, prize, act)
    world.para()
    fix = FIXES["brush"]
    _friendship_turn(world, hero, friend, prize, fix)
    _clean_and_practice(world, hero, friend, prize, act, fix)

    world.facts.update(hero=hero, friend=friend, parent=parent, prize=prize, act=act, fix=fix, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a fairy-tale story about a child named {hero.id} in a converse-tion-al class where fuzz causes a small problem.",
        f"Tell a gentle story that uses the words fuzz, converse-tion-al, and class, and ends with friendship helping the lesson.",
        f"Write a short story for children about repetition in a class, where a friend helps a fuzzy mistake become a happy practice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["act"]
    return [
        QAItem(
            question=f"Where was {hero.id} when the fuzz made trouble?",
            answer=f"{hero.id} was in the {world.setting.place} during the converse-tion-al class.",
        ),
        QAItem(
            question=f"What repeated action made the problem bigger for {hero.id}?",
            answer=f"{hero.id} kept trying to {act.verb}, and the repetition made the fuzz spread more and more.",
        ),
        QAItem(
            question=f"Who helped {hero.id} after the {prize.label} got messy?",
            answer=f"{friend.id} helped {hero.id} calm down, clean up, and practice the words together.",
        ),
        QAItem(
            question=f"How did the story end for the {prize.label}?",
            answer=f"The {prize.label} stayed neat again, and the class finished in a happy, peaceful way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is fuzz?",
            answer="Fuzz is a soft, tiny fluff that can stick to clothes or float in the air.",
        ),
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing or saying something again and again.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is the kind bond between people who help, share, and care for one another.",
        ),
        QAItem(
            question="What is a class?",
            answer="A class is a time when a teacher helps children learn together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.traits:
            parts.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
valid(A,Pr) :- affords(P,A), prize(Pr).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for prize in PRIZES:
        lines.append(asp.fact("prize", prize))
    for act in ACTIVITIES:
        lines.append(asp.fact("activity", act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((a, p) for _, a, p in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python valid combos")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(place="schoolhouse", activity="class", prize="cloak", name="Mira", friend="Penny", parent="teacher", trait="curious"),
    StoryParams(place="tower_room", activity="class", prize="book", name="Luna", friend="Iris", parent="mother", trait="gentle"),
    StoryParams(place="garden_room", activity="class", prize="ribbon", name="Tobin", friend="Bram", parent="father", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.place}, {p.activity}, {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
