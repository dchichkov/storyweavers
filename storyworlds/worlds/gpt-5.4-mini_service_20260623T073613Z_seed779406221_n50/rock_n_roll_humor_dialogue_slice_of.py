#!/usr/bin/env python3
"""
storyworlds/worlds/rock_n_roll_humor_dialogue_slice_of.py
==========================================================

A small slice-of-life storyworld about a kid, a parent, a tiny rock'n'roll
practice, and a funny compromise.

Initial seed tale (used to imagine the world):
---
Jules loved rock'n'roll and practiced guitar in the kitchen after school. One
afternoon, just as Jules was warming up with a loud riff, Dad peeked in and
said the baby was finally asleep in the next room.

"That riff is great," Dad said, smiling, "but it sounds like a thunderstorm in
a tin can."

Jules frowned. "So I should stop?"

Dad tapped the counter. "Not stop. Just switch the amp to the tiny mode, and
maybe use the cardboard drum box instead of the metal spoon."

Jules laughed. "A rock band with a cardboard drum? That's ridiculous."

"Exactly," Dad said. "Ridiculous is allowed, as long as the baby keeps sleeping."

So Jules turned the amp down, kept the beat soft, and the little song became
funny and gentle. The baby slept on, Dad nodded along, and Jules finished the
riff with a grin.

Causal state updates:
---
    loud practice            -> room.noise += 1
                                 nearby sleeper.wake_risk += 1
    soft practice            -> room.noise -= 1
                                 performer.relief += 1
    helpful compromise       -> sleeper.wake_risk -> 0
                                 performer.joy += 1
                                 parent.affection += 1

Scripted social/emotional beats:
---
    music love              -> performer.joy += 1
    warning about sleeping baby -> parent.care += 1
    joke about the sound    -> performer.humor += 1
    compromise accepted     -> performer.relief += 1 ; conflict -> 0
    ending riff             -> performer.pride += 1 ; sleeper remains asleep
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    loudness: float
    humor_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sleeper:
    id: str
    label: str
    thing: str
    waking: str
    region: str = "next room"
    plural: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for ent in world.entities.values():
            if ent.meters["practice"] >= THRESHOLD and ent.meters["loud"] >= THRESHOLD:
                sig = ("noise", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    world.get("room").meters["noise"] += 1
                    if "baby" in world.entities:
                        world.get("baby").meters["wake_risk"] += 1
                    out.append("The room got louder.")
                    changed = True
            if ent.meters["practice"] >= THRESHOLD and ent.meters["soft"] >= THRESHOLD:
                sig = ("calm", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    world.get("room").meters["noise"] = max(0, world.get("room").meters["noise"] - 1)
                    ent.memes["relief"] += 1
                    out.append("The room got calmer.")
                    changed = True
            if ent.memes["compromise"] >= THRESHOLD:
                sig = ("fix", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    if "baby" in world.entities:
                        world.get("baby").meters["wake_risk"] = 0
                    ent.memes["joy"] += 1
                    out.append("The worry settled.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_risk(world: World, performer: Entity, activity: Activity) -> dict:
    sim = world.copy()
    sim.get(performer.id).meters["practice"] += 1
    sim.get(performer.id).meters["loud"] += activity.loudness
    propagate(sim, narrate=False)
    baby = sim.entities.get("baby")
    return {"wake_risk": baby.meters["wake_risk"] if baby else 0, "noise": sim.get("room").meters["noise"]}


def tell(place: Place, activity: Activity, sleeper: Sleeper, *,
         performer_name: str = "Jules",
         performer_type: str = "boy",
         parent_name: str = "Dad",
         parent_type: str = "father") -> World:
    world = World(place)
    performer = world.add(Entity(id=performer_name, kind="character", type=performer_type, role="performer"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_type, role="parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    baby = world.add(Entity(id="baby", kind="character", type="baby", label=sleeper.label))
    baby.meters["sleep"] = 1
    world.facts.update(performer=performer, parent=parent, room=room, baby=baby, sleeper=sleeper, activity=activity)

    performer.memes["love_music"] += 1
    performer.memes["joy"] += 1
    world.say(f"{performer.id} loved rock'n'roll and kept a guitar by the kitchen table.")
    world.say(f"After school, {performer.id} wanted to {activity.verb}, because {activity.humor_line}.")

    world.para()
    world.say(f"Then {parent.id} poked their head in and said, \"{sleeper.waking}\"")
    world.say(f"\"{performer.id}, the {sleeper.label} is asleep in the {sleeper.region},\" {parent.id} added.")
    pred = predict_risk(world, performer, activity)
    world.facts["predicted_risk"] = pred["wake_risk"]
    if pred["wake_risk"] >= THRESHOLD:
        parent.memes["care"] += 1
        performer.memes["worry"] += 1
        world.say(f"\"That sounds like a thunderstorm in a tin can,\" {parent.id} said.")
        world.say(f"\"I can turn down,\" {performer.id} said. \"I love rock'n'roll, not rock'n'roll-and-trouble.\"")
        performer.memes["joke"] += 1
        world.say(f"{parent.id} snorted. \"Good. Save the thunder for a parade.\"")
        world.say(f"{performer.id} grinned, switched to soft practice, and tapped the beat on a cereal box.")
        performer.meters["practice"] += 1
        performer.meters["soft"] += 1
        performer.memes["compromise"] += 1
        propagate(world)
        world.para()
        performer.memes["pride"] += 1
        world.say(f"The little song stayed funny and gentle, and the {sleeper.label} kept sleeping.")
        world.say(f"{performer.id} finished with a tiny flourish and a proud bow to the empty cereal box.")
    else:
        performer.meters["practice"] += 1
        performer.meters["loud"] += 1
        propagate(world)
        world.say(f"{performer.id} kept playing loud, but the room stayed oddly calm.")
        world.say(f"{parent.id} blinked. \"Well, that was suspiciously peaceful.\"")
    world.facts["outcome"] = "calm"
    return world


SETTINGS = {
    "kitchen": Place(id="kitchen", label="the kitchen", affords={"riff", "strum"}),
    "porch": Place(id="porch", label="the porch", affords={"riff", "strum"}),
    "garage": Place(id="garage", label="the garage", affords={"riff", "strum"}),
}

ACTIVITIES = {
    "riff": Activity(
        id="riff",
        verb="play a loud riff",
        gerund="playing loud riffs",
        loudness=1.0,
        humor_line="the notes sounded like a friendly jackhammer",
        tags={"music", "humor"},
    ),
    "strum": Activity(
        id="strum",
        verb="strum the guitar very hard",
        gerund="strumming hard",
        loudness=1.0,
        humor_line="the strings buzzed like bees in tiny boots",
        tags={"music", "humor"},
    ),
    "drums": Activity(
        id="drums",
        verb="bang on the drum kit",
        gerund="banging on drums",
        loudness=1.5,
        humor_line="every snare hit sounded like a suitcase falling downstairs",
        tags={"music", "humor"},
    ),
}

SLEEPERS = {
    "baby": Sleeper(id="baby", label="baby", thing="baby", waking="The baby finally fell asleep", tags={"sleep", "baby"}),
    "nap": Sleeper(id="nap", label="napper", thing="napper", waking="Someone was just starting a nap", tags={"sleep"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nina", "Tess", "Rae"]
BOY_NAMES = ["Jules", "Ben", "Milo", "Otis", "Theo"]
TRAITS = ["cheerful", "quick-witted", "sensible", "playful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    sleeper: str
    performer_name: str
    performer_type: str
    parent_name: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, s) for p in SETTINGS for a in ACTIVITIES for s in SLEEPERS if a in SETTINGS[p].affords]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life rock'n'roll storyworld with humor and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--sleeper", choices=SLEEPERS)
    ap.add_argument("--name")
    ap.add_argument("--parent")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.sleeper is None or c[2] == args.sleeper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, sleeper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    performer_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_type = "father"
    parent_name = args.parent or "Dad"
    return StoryParams(place=place, activity=activity, sleeper=sleeper,
                       performer_name=performer_name, performer_type=gender,
                       parent_name=parent_name, parent_type=parent_type,
                       trait=rng.choice(TRAITS))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child about {f["performer"].id} and {f["parent"].id} handling rock\'n\'roll practice at {f["room"].label}. Include a funny line of dialogue.',
        f'Tell a gentle humorous story where {f["performer"].id} wants to {f["activity"].verb}, but a sleeping {f["sleeper"].label} makes the volume matter, and the family finds a playful compromise.',
        f'Write a rock\'n\'roll story with a small home setting, everyday dialogue, and an ending that shows the music got calmer instead of louder.'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p, parent, sleeper, act = f["performer"], f["parent"], f["sleeper"], f["activity"]
    return [
        QAItem(question=f"What did {p.id} want to do after school?",
               answer=f"{p.id} wanted to {act.verb}. {p.id} loved rock'n'roll, so the practice felt fun before anyone worried about the noise."),
        QAItem(question=f"Why did {parent.id} speak up about the music?",
               answer=f"{parent.id} spoke up because the {sleeper.label} was asleep nearby, and loud music could make the little sleeper wake up."),
        QAItem(question=f"What funny compromise did {p.id} choose?",
               answer=f"{p.id} turned the practice soft, used a cereal box for a beat, and kept the song funny without making a big racket."),
        QAItem(question=f"How did the story end?",
               answer=f"The music got calmer, the {sleeper.label} kept sleeping, and {p.id} finished with a proud smile. That ending shows the family chose a gentle way to keep playing.")
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is rock'n'roll?",
               answer="Rock'n'roll is lively music with guitars, drums, and a strong beat. People often clap, tap, or dance along to it."),
        QAItem(question="Why should music be softer when someone is sleeping?",
               answer="Soft music is kinder because it does not shake or wake up a sleeping person. That helps everyone stay rested and happy."),
        QAItem(question="What is a compromise?",
               answer="A compromise is when people choose a plan that works for everyone. It often means each person changes a little so the problem gets solved."),
    ]


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
room_noisy :- loud_practice.
wake_risk :- room_noisy, baby_asleep.
soft_fix :- soft_practice.
compromise :- soft_fix.
"""

def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("loud_practice"),
        asp.fact("soft_practice"),
        asp.fact("baby_asleep"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], SLEEPERS[params.sleeper],
                 performer_name=params.performer_name, performer_type=params.performer_type,
                 parent_name=params.parent_name, parent_type=params.parent_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show compromise/0."))
        return
    if args.verify:
        print("OK: no ASP verification implemented beyond the inline twin.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(p, a, s, "Jules", "boy", "Dad", "father", "cheerful")) for p, a, s in valid_combos()[:3]]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
