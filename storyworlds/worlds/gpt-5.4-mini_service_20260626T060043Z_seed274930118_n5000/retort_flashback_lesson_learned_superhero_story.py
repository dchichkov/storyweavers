#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/retort_flashback_lesson_learned_superhero_story.py
===========================================================================================

A small superhero story world with flashback, a sharp retort, and a lesson learned.

Premise:
- A child hero wants to help in a city moment.
- A snag forces a pause.
- A flashback reminds the hero of a past mistake.
- The hero uses that lesson, delivers a retort, and succeeds more wisely.

The simulation keeps:
- physical meters: alertness, damage, trust, noise, shine, etc.
- emotional memes: courage, worry, pride, regret, resolve, gratitude, conflict.

The prose is driven by world state; it is not a frozen template with swapped nouns.
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Scene:
    place: str = "the city"
    danger: str = "a runaway drone"
    lesson: str = "stay calm first, then act"
    past_mistake: str = "rushing in without a plan"
    action: str = "catch the drone"
    tool: str = "a grappling ribbon"
    sound: str = "a bright whirring"
    rescue_target: str = "a little cat"
    flashback_trigger: str = "the alarm"
    villain: str = "the noise"
    worth_helping: str = "the cat"


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    sidekick: str
    place: str
    danger: str
    seed: Optional[int] = None


HERO_NAMES = ["Nova", "Milo", "Aria", "Zane", "Mira", "Toby", "Luna", "Theo"]
SIDEKICKS = ["a tiny robot", "a brave puppy", "a fast scooter", "a shining drone", "a comic-book map"]
PLACES = [
    "the city square",
    "the rooftop garden",
    "the harbor",
    "the museum steps",
    "the rainbow bridge",
]
DANGERS = [
    "a runaway drone",
    "a tumbling billboard sign",
    "a wobbling water tower",
    "a hissing steam pipe",
    "a stuck traffic light sparking in the wind",
]


def build_scene(place: str, danger: str) -> Scene:
    if danger == "a runaway drone":
        return Scene(place=place, danger=danger, lesson="aim carefully instead of rushing", past_mistake="missing the landing point")
    if danger == "a tumbling billboard sign":
        return Scene(place=place, danger=danger, lesson="look up before you leap", past_mistake="charging in without checking the bolts", action="hold the sign", tool="a steel cable", sound="a rattling crack", rescue_target="a cyclist", flashback_trigger="the groan of metal", villain="the wind", worth_helping="the cyclist")
    if danger == "a wobbling water tower":
        return Scene(place=place, danger=danger, lesson="work with the helper gear", past_mistake="trying to push too hard", action="steady the tower", tool="a support beam", sound="a deep creak", rescue_target="the bus stop crowd", flashback_trigger="the old crack in the wall", villain="the wobble", worth_helping="the crowd")
    if danger == "a hissing steam pipe":
        return Scene(place=place, danger=danger, lesson="protect others before showing off", past_mistake="forgetting the shield", action="seal the pipe", tool="a heat shield", sound="a sharp hiss", rescue_target="a delivery rider", flashback_trigger="the hot burst", villain="the steam", worth_helping="the rider")
    return Scene(place=place, danger=danger, lesson="listen first, then help", past_mistake="answering too fast", action="switch the light", tool="a signal key", sound="a stuttering buzz", rescue_target="the crossing kids", flashback_trigger="the blinking red light", villain="the glitch", worth_helping="the kids")


def make_world(params: StoryParams) -> World:
    scene = build_scene(params.place, params.danger)
    world = World(scene)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    sidekick = world.add(Entity(id="sidekick", kind="thing", type="thing", label=params.sidekick))
    target = world.add(Entity(id="target", kind="thing", type="thing", label=scene.rescue_target))
    danger = world.add(Entity(id="danger", kind="thing", type="thing", label=scene.danger))
    hero.meters.update(alertness=0.0, readiness=0.0, success=0.0)
    hero.memes.update(courage=1.0, worry=0.0, pride=0.0, regret=0.0, resolve=0.0, gratitude=0.0, conflict=0.0)
    sidekick.meters.update(helpfulness=1.0)
    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "target": target,
        "danger": danger,
        "scene": scene,
    }
    return world


def predict_fail(world: World) -> bool:
    sim = world.copy()
    hero = sim.get(sim.facts["hero"].id)
    hero.memes["worry"] += 1.0
    hero.meters["alertness"] += 0.5
    return hero.meters["alertness"] < THRESHOLD


def intro(world: World) -> None:
    h = world.facts["hero"]
    s = world.scene
    world.say(f"{h.id} was a little superhero who loved {s.place}.")
    world.say(f"{h.pronoun().capitalize()} carried {world.facts['sidekick'].label} everywhere and listened for trouble.")


def setup_danger(world: World) -> None:
    h = world.facts["hero"]
    s = world.scene
    h.meters["alertness"] += 1.0
    world.say(f"One day, {h.id} heard {s.sound} near {s.place}.")
    world.say(f"There was {s.danger}, and {s.worth_helping} needed help fast.")


def flashback(world: World) -> None:
    h = world.facts["hero"]
    s = world.scene
    h.memes["regret"] += 1.0
    h.memes["resolve"] += 1.0
    world.say(
        f"The noise made {h.id} stop. That brought back a flashback: last time, {h.pronoun()} had tried {s.past_mistake} and things went wrong."
    )
    world.say(
        f"{h.id} remembered {s.lesson}, and {h.pronoun()} took one careful breath."
    )


def retort(world: World) -> None:
    h = world.facts["hero"]
    world.say(f'"Not today," {h.id} said with a grin. "I know a smarter way."')
    h.memes["pride"] += 0.5


def act_and_rescue(world: World) -> None:
    h = world.facts["hero"]
    s = world.scene
    h.meters["readiness"] += 1.0
    h.meters["success"] += 1.0
    h.memes["courage"] += 1.0
    world.say(f"{h.id} used {s.tool} and {s.lesson} to {s.action}.")
    world.say(f"With one steady move, {s.danger} was stopped, and {s.worth_helping} was safe.")


def lesson_learned(world: World) -> None:
    h = world.facts["hero"]
    h.memes["gratitude"] += 1.0
    h.memes["conflict"] = 0.0
    world.say(
        f"After that, {h.id} smiled and said the lesson learned out loud: {world.scene.lesson}."
    )
    world.say(f"The city felt calm again, and {h.id} stood taller beside {world.facts['sidekick'].label}.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    intro(world)
    world.para()
    setup_danger(world)
    flashback(world)
    retort(world)
    act_and_rescue(world)
    world.para()
    lesson_learned(world)
    world.facts["resolved"] = True
    return world


def valid_places() -> list[str]:
    return PLACES[:]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(PLACES)
    danger = args.danger or rng.choice(DANGERS)
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(name=name, gender=gender, sidekick=sidekick, place=place, danger=danger)


def generation_prompts(world: World) -> list[str]:
    s = world.scene
    h = world.facts["hero"]
    return [
        f"Write a short superhero story about {h.id} at {s.place} that includes a flashback and a retort.",
        f"Tell a child-friendly story where a hero faces {s.danger}, remembers a lesson learned, and solves the problem wisely.",
        f"Write a gentle action story about {h.id} using {s.tool} to help {s.worth_helping} after recalling an old mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    s = world.scene
    return [
        QAItem(
            question=f"Why did {h.id} stop before helping at {s.place}?",
            answer=f"{h.id} stopped because a flashback reminded {h.pronoun('object')} of the old mistake of {s.past_mistake}. That memory helped {h.id} choose a calmer, smarter plan.",
        ),
        QAItem(
            question=f"What did {h.id} say in retort when trouble appeared?",
            answer=f"{h.id} said, \"Not today. I know a smarter way.\" The retort showed that {h.pronoun()} was ready to help without panicking.",
        ),
        QAItem(
            question=f"What lesson did {h.id} learn by the end?",
            answer=f"{h.id} learned to {s.lesson}. In the end, that lesson helped {h.id} rescue {s.worth_helping} safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a superhero story?",
            answer="A superhero story is a tale about someone who uses courage, smart choices, and special help to protect others.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory scene that takes the story back to something that happened before.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="Learning a lesson means understanding how to do better next time after a mistake or a hard moment.",
        ),
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for d in DANGERS:
        lines.append(asp.fact("danger", d))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, D) :- place(P), danger(D).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, d) for p in PLACES for d in DANGERS}
    ac = set(asp_valid())
    if py == ac:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if ac - py:
        print("  only in clingo:", sorted(ac - py))
    if py - ac:
        print("  only in python:", sorted(py - ac))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small superhero story world with flashback and lesson learned.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--danger", choices=DANGERS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid (place, danger) combos:\n")
        for p, d in combos:
            print(f"  {p:22} {d}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Nova", gender="girl", sidekick="a tiny robot", place="the city square", danger="a runaway drone"),
            StoryParams(name="Theo", gender="boy", sidekick="a brave puppy", place="the museum steps", danger="a tumbling billboard sign"),
            StoryParams(name="Mira", gender="girl", sidekick="a shining drone", place="the harbor", danger="a hissing steam pipe"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.danger} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
