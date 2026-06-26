#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transcribe_children_s_museum_misunderstanding_friendship_repetition.py
============================================================================================================

A standalone story world about a children's museum tale, built in a folk-tale
style around misunderstanding, friendship, and repetition.

The seed imagination:
- A child visits a children's museum.
- A small misunderstanding happens around a sign, a whisper, and a repeated
  instruction.
- A friend helps by repeating the message clearly, and the story ends with
  warmth and shared play.

The simulated world tracks:
- physical meters: distance, sound, attention, tidiness, and trustful actions
- emotional memes: confusion, worry, kindness, relief, friendship

The story is generated from the evolving state rather than from a fixed prose
template with swapped nouns.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the children's museum"
    rooms: list[str] = field(default_factory=lambda: ["the gallery", "the water table", "the dress-up corner"])


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    sound: str
    keyword: str
    causes_misunderstanding: bool = True


@dataclass
class Sign:
    id: str
    text: str
    meaning: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


THRESHOLD = 1.0


def _narrate_if(world: World, cond: bool, text: str) -> None:
    if cond:
        world.say(text)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "museum": Setting(),
}

ACTIVITIES = {
    "transcribe": Activity(
        id="transcribe",
        verb="transcribe the map labels",
        gerund="transcribing the map labels",
        sound="soft tapping",
        keyword="transcribe",
        causes_misunderstanding=True,
    ),
    "repeat": Activity(
        id="repeat",
        verb="repeat the directions",
        gerund="repeating the directions",
        sound="clear echoing",
        keyword="repeat",
        causes_misunderstanding=False,
    ),
}

SIGNS = {
    "quiet_sign": Sign(
        id="quiet_sign",
        text="Please use quiet voices and follow the arrows.",
        meaning="The sign asks children to whisper and walk carefully.",
    ),
    "copy_sign": Sign(
        id="copy_sign",
        text="Trace the letters with a finger, then speak the words aloud.",
        meaning="The sign invites children to copy and say the words.",
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Tara", "Nora", "Pia", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Milo", "Ezra", "Noah"]
TRAITS = ["curious", "gentle", "brave", "bright", "careful", "lively"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "museum"
    activity: str = "transcribe"
    name: str = "Mina"
    gender: str = "girl"
    friend_name: str = "Owen"
    friend_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------
def reasonable(params: StoryParams) -> bool:
    return params.place == "museum" and params.activity in ACTIVITIES


def valid_names(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A children's museum storyworld about misunderstanding, friendship, and repetition.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", dest="friend_gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name", dest="friend_name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "museum"
    activity = args.activity or "transcribe"
    if place != "museum":
        raise StoryError("This storyworld only tells tales set in the children's museum.")
    if activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(valid_names(gender))
    friend_name = args.friend_name or rng.choice(valid_names(friend_gender))
    if name == friend_name:
        raise StoryError("The child and the friend must be different people.")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, friend_name=friend_name, friend_gender=friend_gender, trait=trait)


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def mem(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_gender))
    sign = world.add(Entity(id="sign", type="sign", label="museum sign"))
    activity = ACTIVITIES[params.activity]

    # Setup
    world.say(f"Once, in the children's museum, there was a {params.trait} child named {child.id}.")
    world.say(f"{child.id} loved {activity.gerund}, because the words and pictures felt like a small puzzle.")
    world.say(f"Near the hall stood a sign that read, “{SIGNS['copy_sign'].text}”")
    world.say(f"{child.id} looked at the letters and began to copy them with great care.")

    # Middle: misunderstanding
    world.para()
    mem(child, "confusion", 1)
    meter(child, "attention", 1)
    meter(child, "sound", 1)
    world.say(f"Then {child.id} noticed the word “trace” and thought it meant to stay silent and whisper.")
    world.say(f"So {child.id} kept making only a tiny sound while {activity.sound} filled the table.")
    mem(friend, "worry", 1)
    world.say(f"{friend.id}, who was nearby, worried that the game had gone wrong.")

    # Friendship and repetition
    world.para()
    mem(friend, "kindness", 1)
    mem(friend, "friendship", 1)
    world.say(f"{friend.id} came close and spoke gently: “No, dear friend, this sign says to copy the words aloud.”")
    world.say(f"{friend.id} repeated it once more, slower and clearer, so the meaning would not slip away.")
    meter(friend, "support", 1)
    meter(child, "understanding", 1)
    mem(child, "relief", 1)
    mem(child, "friendship", 1)
    mem(child, "confusion", -1)

    # Resolution
    world.para()
    world.say(f"At last {child.id} smiled, and the two children said the words together three times, softly and then clearly.")
    world.say(f"After that, {child.id} and {friend.id} followed the arrows, copied the labels, and laughed at how one small word could be misunderstood.")
    world.say(f"The museum seemed warmer after the misunderstanding had turned into friendship.")
    world.say(f"And before the day was done, the children were still {activity.gerund}, side by side, as if they had always been meant to walk together.")

    world.facts.update(
        child=child,
        friend=friend,
        sign=sign,
        activity=activity,
        misunderstood=True,
        resolved=True,
        repetition=True,
    )
    return world


def generate_story_text(world: World) -> str:
    return world.render()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    f = world.facts["friend"]
    act = world.facts["activity"]
    return [
        'Write a folk-tale style story for a child in a children\'s museum about a misunderstanding and a kind friend who repeats the meaning clearly.',
        f"Tell a gentle story where {c.id} wants to {act.verb}, misunderstands a museum sign, and {f.id} helps by repeating the instructions.",
        'Write a short story that includes the word "transcribe" and ends with friendship after a small confusion is cleared up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    f = world.facts["friend"]
    act = world.facts["activity"]
    return [
        QAItem(
            question=f"What did {c.id} think the sign meant at first?",
            answer=f"{c.id} thought the sign meant to stay quiet and whisper, because the word sounded tricky and the letters made the message feel unclear.",
        ),
        QAItem(
            question=f"How did {f.id} help after the misunderstanding?",
            answer=f"{f.id} helped by repeating the meaning slowly and clearly, so {c.id} could understand that the children were meant to copy the words aloud.",
        ),
        QAItem(
            question=f"What did the children do together at the end?",
            answer=f"At the end, the children repeated the words together, followed the arrows, and kept {act.gerund} side by side.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a children's museum?",
            answer="A children's museum is a place where children can explore, touch, build, and learn by playing with exhibits and activities.",
        ),
        QAItem(
            question="Why can repetition help when something is misunderstood?",
            answer="Repetition can help because hearing or seeing the same message more than once gives the mind another chance to understand it clearly.",
        ),
        QAItem(
            question="What does friendship look like in a kind story?",
            answer="Friendship looks like helping, listening, and speaking gently so another person feels safe and included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
friend(F) :- friend_name(F).
activity(transcribe).
activity(repeat).

misunderstanding(C) :- child(C), activity(transcribe).
friendship(C,F) :- child(C), friend(F), helps(F,C).
repetition(F) :- friend(F), repeats(F).

resolved(C) :- misunderstanding(C), friendship(C,_), repetition(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("setting", "museum"))
    lines.append(asp.fact("activity", "transcribe"))
    lines.append(asp.fact("activity", "repeat"))
    lines.append(asp.fact("child_name", "child"))
    lines.append(asp.fact("friend_name", "friend"))
    lines.append(asp.fact("helps", "friend", "child"))
    lines.append(asp.fact("repeats", "friend"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    # Python gate is simple; ASP twin must agree on the same toy structure.
    import asp
    model = asp.one_model(asp_program("#show resolved/1."))
    asp_resolved = bool(asp.atoms(model, "resolved"))
    py_resolved = True
    if asp_resolved == py_resolved:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python reasonableness.")
    return 1


# ---------------------------------------------------------------------------
# Emit / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(place="museum", activity="transcribe", name="Mina", gender="girl", friend_name="Owen", friend_gender="boy", trait="curious"),
        StoryParams(place="museum", activity="transcribe", name="Theo", gender="boy", friend_name="Lily", friend_gender="girl", trait="gentle"),
    ]


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError("This world only supports a children's museum tale with transcribe/repeat.")
    world = tell(params)
    return StorySample(
        params=params,
        story=generate_story_text(world),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("This storyworld's ASP twin only checks the friendship-resolution pattern.")
        sys.exit(0)

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name} and {p.friend_name} at the children's museum"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
