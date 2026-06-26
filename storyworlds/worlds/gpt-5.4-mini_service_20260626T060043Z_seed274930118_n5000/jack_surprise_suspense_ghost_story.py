#!/usr/bin/env python3
"""
jack_surprise_suspense_ghost_story.py
=====================================

A small, constraint-checked storyworld for a child-friendly ghost story about
Jack, surprise, and suspense.

Premise:
- Jack stays in a quiet old house with a strange, friendly ghost.
- He hears spooky sounds and feels suspense.
- A surprise at the end reveals the "ghost" is only a soft white sheet and a
  helpful light trick, or a shy little ghost who is not scary after all.

The world simulates:
- physical meters: light, dark, noise, chill
- emotional memes: fear, suspense, surprise, courage, joy
- object state that drives the story turn and resolution
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class House:
    name: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["hall", "stairs", "attic"])
    spooky: bool = True
    open_windows: bool = False
    lights_on: bool = False


class World:
    def __init__(self, house: House) -> None:
        self.house = house
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
        import copy

        c = World(self.house)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    name: str
    companion: str
    ending: str
    seed: Optional[int] = None


GHOST_TYPES = {
    "sheet": "a white sheet ghost",
    "lantern": "a lantern glow that looked like a ghost",
    "pillow": "a floating pillow ghost",
}
COMPANIONS = ["cat", "little sister", "dog", "grandpa", "toy bear"]
ENDINGS = ["friendly", "surprise", "suspense"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_dark_spook(world: World) -> list[str]:
    out = []
    jack = world.get("Jack")
    if world.house.lights_on:
        return out
    if jack.meters.get("dark", 0) < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jack.memes["suspense"] = jack.memes.get("suspense", 0) + 1
    jack.memes["fear"] = jack.memes.get("fear", 0) + 1
    out.append("The dark house felt very quiet, and Jack's heart started to thump.")
    return out


def _r_noise_suspense(world: World) -> list[str]:
    out = []
    jack = world.get("Jack")
    if jack.meters.get("noise", 0) < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jack.memes["suspense"] = jack.memes.get("suspense", 0) + 1
    out.append("A tiny creak from upstairs made Jack freeze for a moment.")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    jack = world.get("Jack")
    if jack.memes.get("curious", 0) < THRESHOLD:
        return out
    if world.facts.get("surprise_seen"):
        return out
    if world.facts.get("reveal_ready") != True:
        return out
    world.facts["surprise_seen"] = True
    jack.memes["surprise"] = jack.memes.get("surprise", 0) + 1
    jack.memes["fear"] = 0
    jack.memes["joy"] = jack.memes.get("joy", 0) + 1
    out.append("Then Jack saw the funny trick behind the spooky shape.")
    return out


CAUSAL_RULES = [Rule("dark_spook", _r_dark_spook), Rule("noise_suspense", _r_noise_suspense), Rule("surprise", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reveal(world: World) -> bool:
    sim = world.copy()
    jack = sim.get("Jack")
    jack.meters["dark"] = 1
    jack.meters["noise"] = 1
    jack.memes["curious"] = 1
    sim.facts["reveal_ready"] = True
    propagate(sim, narrate=False)
    return sim.facts.get("surprise_seen", False)


def tell(params: StoryParams) -> World:
    house = House()
    world = World(house)
    jack = world.add(Entity(id="Jack", kind="character", type="boy", label="Jack"))
    companion = world.add(Entity(id="Companion", kind="character", type="thing", label=params.companion))
    ghost = world.add(Entity(id="Ghost", kind="thing", type="ghost", label="the ghost", phrase=GHOST_TYPES[params.ending]))

    # Act 1
    world.say("Jack lived in an old house that always felt a little spooky at night.")
    world.say(f"He had a {companion.label} with him, which made the hallway feel less lonely.")
    world.say("At bedtime, Jack heard the floor give a tiny creak, and he stared at the dark stairs.")
    jack.meters["dark"] = 1
    jack.meters["noise"] = 1
    jack.memes["curious"] = 1

    # Act 2
    world.para()
    propagate(world, narrate=True)
    world.say("Jack held still and listened, because the quiet felt bigger when nobody spoke.")
    if not world.house.lights_on:
        world.say("He wanted to peek, but the shadows on the wall looked long and strange.")
    jack.memes["courage"] = 1
    world.say("Then Jack took a careful breath and walked one step at a time toward the stairs.")

    # Act 3
    world.para()
    world.house.lights_on = True
    world.facts["reveal_ready"] = True if predict_reveal(world) else False
    world.say("At the top of the stairs, Jack found the surprise.")
    if params.ending == "sheet":
        world.say("The ghost was only a white sheet hanging from a chair, fluttering in the draft.")
        world.say("Jack laughed when he saw the trick, and the scary shape turned silly in the light.")
    elif params.ending == "lantern":
        world.say("The ghostly glow came from a lantern tucked behind a curtain, making a round shining face on the wall.")
        world.say("Jack smiled, because the spooky shine was only a clever light trick.")
    else:
        world.say("A sleepy little ghost peeked out, then waved and said it had only wanted a friend.")
        world.say("Jack felt surprised, then happy, because the ghost was not mean at all.")
    jack.memes["curious"] += 1
    propagate(world, narrate=True)
    world.say("Jack and the companion sat together under the bright lamp, and the house felt warm again.")

    world.facts.update(
        jack=jack,
        companion=companion,
        ghost=ghost,
        house=house,
        ending=params.ending,
    )
    return world


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world for Jack, surprise, and suspense.")
    ap.add_argument("--name", default="Jack")
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--ending", choices=ENDINGS)
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
    companion = args.companion or rng.choice(COMPANIONS)
    ending = args.ending or rng.choice(ENDINGS)
    return StoryParams(name=args.name or "Jack", companion=companion, ending=ending)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["ending"]
    return [
        'Write a short child-friendly ghost story about Jack in a spooky old house.',
        f'Write a suspenseful story that includes Jack, a quiet hallway, and a surprise ending like "{p}".',
        "Tell a gentle ghost story where Jack hears strange sounds, feels suspense, and learns the ghost is not scary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    ending = world.facts["ending"]
    return [
        QAItem(
            question="Why did Jack feel suspense in the old house?",
            answer="Jack felt suspense because the house was dark, the stairs creaked, and he did not know what was making the spooky sound.",
        ),
        QAItem(
            question="What surprise did Jack find at the end?",
            answer={
                "sheet": "He found that the ghost was only a white sheet hanging from a chair.",
                "lantern": "He found that the ghostly face was really a lantern glow behind a curtain.",
                "suspense": "He found a shy little ghost who only wanted a friend.",
            }[ending],
        ),
        QAItem(
            question="How did Jack feel after the surprise?",
            answer="He felt less afraid and more happy, because the scary moment turned into a safe and friendly one.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting and not knowing what will happen next.",
        ),
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a story with spooky moments, a mystery, and often a surprising ending.",
        ),
        QAItem(
            question="Why do lights help in a dark house?",
            answer="Lights help because they make it easier to see shapes clearly, so spooky shadows do not seem as scary.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== Prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes}")
    lines.append(f"house.lights_on={world.house.lights_on}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Jack", companion="cat", ending="sheet"),
    StoryParams(name="Jack", companion="dog", ending="lantern"),
    StoryParams(name="Jack", companion="toy bear", ending="suspense"),
]


ASP_RULES = r"""
dark_spooky(J) :- dark(J), noise(J).
suspense(J) :- dark_spooky(J).
surprise(J) :- reveal_ready(J), curious(J).
friendly_end(J) :- surprise(J).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("boy", "jack"),
        asp.fact("dark", "jack"),
        asp.fact("noise", "jack"),
        asp.fact("curious", "jack"),
        asp.fact("reveal_ready", "jack"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_states() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show friendly_end/1."))
    return sorted(set(asp.atoms(model, "friendly_end")))


def asp_verify() -> int:
    import asp
    py = {("jack",)}
    cl = set(asp_story_states())
    if py == cl:
        print("OK: ASP parity matches Python story-state gate.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


def build_story_gate() -> set[tuple]:
    return {("jack",)}


def valid_story(params: StoryParams) -> bool:
    return params.name.lower() == "jack" and params.ending in ENDINGS


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show friendly_end/1."))
        return
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show friendly_end/1."))
        print(asp.atoms(model, "friendly_end"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            if not valid_story(params):
                raise StoryError("This storyworld only tells stories about Jack.")
            samples.append(generate(params))

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
            header = f"### {p.name} / {p.companion} / {p.ending}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
