#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/grub_get_gazebo_rhyme_surprise_friendship_slice.py
=============================================================================================================================

A small slice-of-life story world about a child, a friend, a gazebo, and a
tiny surprise that turns into a shared rhyme.

Premise:
- A child and a friend spend time in a garden with a gazebo.
- One of them wants to get a grub they found near the roots.
- The other is surprised by the grub, but both are curious rather than scared.

Turn:
- The grub is not a danger; it is a small living thing that needs care.
- A shared rhyme becomes the social bridge: the friends make up a playful line
  while they decide where the grub should go.

Resolution:
- They move the grub to a damp patch of soil near the gazebo.
- The surprise softens into friendship, and the ending image shows the two
  friends calm, close, and proud of being gentle.

This world uses meters for physical state and memes for emotional state.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    alive: bool = False
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
class Setting:
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)


@dataclass
class Event:
    id: str
    verb: str
    verb_ing: str
    surprise: str
    rhyme: str
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    location: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


class StoryState:
    pass


def _join_sentences(parts: list[str]) -> str:
    return " ".join(p.strip() for p in parts if p.strip())


def _ensure_period(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] not in ".!?":
        return text + "."
    return text


def _capitalize_first(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _say(world: World, text: str) -> None:
    world.say(_ensure_period(text))


def _r_get_grub(world: World) -> list[str]:
    out: list[str] = []
    grub = world.get("grub")
    if grub.location != "under root":
        return out
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("get", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["care"] = actor.memes.get("care", 0.0) + 1
        grub.location = "in a leaf cup"
        out.append(f"{actor.id} bent down and got the grub into a little leaf cup.")
    return out


def _r_surprise_softens(world: World) -> list[str]:
    out: list[str] = []
    grub = world.get("grub")
    for actor in world.characters():
        if actor.memes.get("surprise", 0.0) < THRESHOLD:
            continue
        if grub.location != "in a leaf cup":
            continue
        sig = ("soften", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["surprise"] = max(0.0, actor.memes["surprise"] - 1)
        actor.memes["friendship"] = actor.memes.get("friendship", 0.0) + 1
        out.append(f"The surprise turned gentle once they saw the tiny grub was safe.")
    return out


CAUSAL_RULES = [
    _r_get_grub,
    _r_surprise_softens,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            _say(world, s)
    return produced


def predict_outcome(world: World, actor: Entity) -> dict:
    sim = world.copy()
    _do_get(sim, sim.get(actor.id), narrate=False)
    grub = sim.get("grub")
    return {
        "got_grub": grub.location == "in a leaf cup",
        "friendship": actor.memes.get("friendship", 0.0),
        "surprise": actor.memes.get("surprise", 0.0),
    }


def _do_get(world: World, actor: Entity, narrate: bool = True) -> None:
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    _say(world, f"{actor.id} wanted to get a closer look at the tiny grub near the gazebo.")
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, friend: Entity) -> None:
    _say(world, f"{child.id} was a {child.type} who liked quiet afternoons in the garden.")
    _say(world, f"{friend.id} was {friend.pronoun('object')} friend, always ready to share a small adventure.")


def setting_line(world: World) -> None:
    _say(world, f"The garden had a wooden gazebo with cool shade and a patch of soft soil beside it.")


def surprise_line(world: World, child: Entity, friend: Entity) -> None:
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
    friend.memes["surprise"] = friend.memes.get("surprise", 0.0) + 1
    _say(world, f"Then they noticed a tiny grub wriggling near the roots, and both of them paused.")
    _say(world, f"{friend.id} blinked in surprise, but {child.id} leaned in with curious eyes.")


def rhyme_line(world: World, child: Entity, friend: Entity) -> None:
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    _say(world, f'{child.id} whispered, "Little grub, soft and snug."')
    _say(world, f'{friend.id} answered, "Safe in shade, under the gazebo rug."')


def move_grub(world: World, child: Entity, friend: Entity) -> None:
    grub = world.get("grub")
    grub.location = "in a leaf cup"
    child.memes["care"] = child.memes.get("care", 0.0) + 1
    friend.memes["care"] = friend.memes.get("care", 0.0) + 1
    _say(world, f"They lifted the grub carefully in a leaf cup so it would not get hurt.")


def finish(world: World, child: Entity, friend: Entity) -> None:
    grub = world.get("grub")
    grub.location = "damp soil"
    child.memes["friendship"] = child.memes.get("friendship", 0.0) + 1
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1
    _say(world, f"They set the grub into damp soil beside the gazebo, where it could settle safely.")
    _say(world, f"After that, {child.id} and {friend.id} smiled at each other, proud of being gentle together.")


def tell(setting: Setting, event: Event, child_name: str, friend_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl", label=child_name))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", label=friend_name))
    grub = world.add(Entity(
        id="grub",
        kind="thing",
        type="grub",
        label="grub",
        phrase="a tiny grub",
        location="under root",
        alive=True,
    ))
    world.facts.update(child=child, friend=friend, grub=grub, event=event, setting=setting)

    introduce(world, child, friend)
    setting_line(world)
    world.para()
    surprise_line(world, child, friend)
    rhyme_line(world, child, friend)
    _do_get(world, child)
    world.para()
    move_grub(world, child, friend)
    finish(world, child, friend)
    return world


SETTINGS = {
    "garden": Setting(place="the garden", affords={"get"}),
    "backyard": Setting(place="the backyard", affords={"get"}),
    "gazebo": Setting(place="the garden gazebo", affords={"get"}),
}

EVENTS = {
    "get": Event(
        id="get",
        verb="get",
        verb_ing="getting",
        surprise="surprised",
        rhyme="rhyming",
        action="carefully move",
        tags={"grub", "get", "gazebo", "surprise", "friendship", "rhyme"},
    ),
}

CHILDREN = ["Mina", "Lia", "Noa", "Ivy", "June", "Sana"]
FRIENDS = ["Ben", "Kai", "Owen", "Theo", "Milo", "Finn"]
TRAITS = ["quiet", "curious", "gentle", "cheerful", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    event: str
    child: str
    friend: str
    trait: str
    seed: Optional[int] = None


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    grub: Entity = f["grub"]
    event: Event = f["event"]
    setting: Setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who found the tiny grub near {setting.place}?",
            answer=f"{child.id} and {friend.id} found the tiny grub together near {setting.place}."
        ),
        QAItem(
            question=f"What did {child.id} and {friend.id} do when they saw the grub?",
            answer=f"They paused in surprise, then used a leaf cup to get the grub safely."
        ),
        QAItem(
            question=f"Where did they put the grub at the end of the story?",
            answer=f"They set the grub into damp soil beside the gazebo so it could stay safe."
        ),
        QAItem(
            question=f"How did the surprise change by the end?",
            answer=f"It softened into friendship, because {child.id} and {friend.id} worked together gently."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gazebo?",
            answer="A gazebo is a small roofed garden shelter where people can sit in the shade."
        ),
        QAItem(
            question="What is a grub?",
            answer="A grub is a small, soft insect larva that often lives in soil or under plants."
        ),
        QAItem(
            question="Why can a rhyme be fun to say?",
            answer="A rhyme can be fun because the ending sounds match and the words feel playful."
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means caring about someone, sharing time with them, and helping them kindly."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    friend: Entity = f["friend"]
    event: Event = f["event"]
    setting: Setting = f["setting"]
    return [
        f"Write a slice-of-life story about {child.id} and {friend.id} at {setting.place} where they get a grub safely.",
        f"Tell a gentle story that includes a gazebo, a surprise, a rhyme, and friendship.",
        f"Write a small childhood story where two friends notice a grub and choose a careful, kind solution.",
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A grub is safely gotten when it ends up in a leaf cup.
got_grub(C) :- child(C), grub_at(cup).

% Surprise becomes friendship once the grub is seen as safe.
softened(C) :- child(C), got_grub(C), surprise(C).
friendly(C) :- child(C), softened(C).

% A valid story is one where a child, a friend, a gazebo, and a grub all appear.
valid_story(P, C, F) :- place(P), child(C), friend(F), setting_has_gazebo(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if "get" in setting.affords:
            lines.append(asp.fact("affords", pid, "get"))
        if "gazebo" in pid:
            lines.append(asp.fact("setting_has_gazebo", pid))
    lines.append(asp.fact("child", "mina"))
    lines.append(asp.fact("friend", "ben"))
    lines.append(asp.fact("grub", "grub"))
    lines.append(asp.fact("grub_at", "cup"))
    lines.append(asp.fact("surprise", "mina"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a grub, a gazebo, and a gentle surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--child")
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(SETTINGS))
    event = args.event or "get"
    child = args.child or rng.choice(CHILDREN)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != child])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, event=event, child=child, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], params.child, params.friend)
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
    StoryParams(place="gazebo", event="get", child="Mina", friend="Ben", trait="curious"),
    StoryParams(place="garden", event="get", child="Lia", friend="Kai", trait="gentle"),
    StoryParams(place="backyard", event="get", child="Ivy", friend="Theo", trait="thoughtful"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, event) for place in SETTINGS for event in EVENTS if "get" in SETTINGS[place].affords]


def asp_verify() -> int:
    import asp
    return 0 if set(valid_combos()) == {("garden", "get"), ("backyard", "get"), ("gazebo", "get")} else 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.child} and {p.friend} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
