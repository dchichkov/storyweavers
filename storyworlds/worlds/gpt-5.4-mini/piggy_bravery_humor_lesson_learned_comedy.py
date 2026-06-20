#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/piggy_bravery_humor_lesson_learned_comedy.py
=============================================================================

A small standalone story world for a comic, child-facing piggy story with
bravery, humor, and a lesson learned.

Premise:
- Piggy wants to do something brave in a small comedy setting.
- A little problem makes piggy nervous.
- A funny helper and a brave choice turn the moment around.
- The ending proves the lesson learned.

This file is self-contained and uses only the standard library plus the shared
storyworlds/results.py containers.
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Joke:
    id: str
    setup: str
    punch: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    scene: str
    worry: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    pig = world.get("piggy")
    if pig.meters["splat"] < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    sidekick = world.get("pal")
    pig.memes["humor"] += 1
    sidekick.memes["humor"] += 1
    out.append("__laugh__")
    return out


def _r_brave(world: World) -> list[str]:
    pig = world.get("piggy")
    if pig.memes["courage"] < THRESHOLD:
        return []
    sig = ("brave",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pig.meters["action"] += 1
    pig.memes["confidence"] += 1
    return ["__brave__"]


def _r_lesson(world: World) -> list[str]:
    pig = world.get("piggy")
    if pig.memes["confidence"] < THRESHOLD:
        return []
    sig = ("lesson",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pig.memes["lesson"] += 1
    return []


RULES = [Rule("laugh", "social", _r_laugh), Rule("brave", "social", _r_brave), Rule("lesson", "social", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_success(world: World, challenge: Challenge, joke: Joke) -> dict:
    sim = world.copy()
    _do_challenge(sim, narrate=False)
    _tell_joke(sim, joke, narrate=False)
    return {
        "brave": sim.get("piggy").memes["confidence"] >= THRESHOLD,
        "lesson": sim.get("piggy").memes["lesson"] >= THRESHOLD,
    }


def _do_challenge(world: World, narrate: bool = True) -> None:
    pig = world.get("piggy")
    pig.meters["splat"] += 1
    pig.memes["wobble"] += 1
    propagate(world, narrate=narrate)


def _tell_joke(world: World, joke: Joke, narrate: bool = True) -> None:
    pig = world.get("piggy")
    pal = world.get("pal")
    pig.memes["humor"] += 1
    pal.memes["humor"] += 1
    world.facts["joke_effect"] = joke.effect
    if narrate:
        world.say(
            f'{pal.id} grinned and said, "{joke.setup} {joke.punch}" '
            f'That silly line made everyone snort.'
        )


def intro(world: World, pig: Entity, pal: Entity, challenge: Challenge) -> None:
    world.say(
        f"{pig.id} was a small piggy with a big wish: to try something brave at "
        f"the silly little show in {challenge.scene}."
    )
    world.say(
        f"{pig.id} loved the applause, the popcorn smell, and the idea of making "
        f"everyone laugh without tripping over {challenge.risk}."
    )


def problem(world: World, pig: Entity, challenge: Challenge) -> None:
    pig.memes["nervous"] += 1
    world.say(
        f"But when {challenge.worry} happened, {pig.id} froze. "
        f"{pig.id} stared at {challenge.risk} and whispered, "
        f'"Oh no. What if I mess this up?"'
    )


def humor_beat(world: World, joke: Joke, pal: Entity) -> None:
    world.say(
        f"Then {pal.id} tried a joke: {joke.setup} {joke.punch} {joke.effect}."
    )
    world.say(
        f"{pal.id} snorted first, then {piggy_name(world)} did too, and the room "
        f"felt lighter right away."
    )


def piggy_name(world: World) -> str:
    return world.get("piggy").id


def brave_turn(world: World, pig: Entity, challenge: Challenge) -> None:
    pig.memes["courage"] += 1
    world.say(
        f"{pig.id} took one deep breath, wiggled {pig.pronoun('possessive')} "
        f"little hooves, and stepped forward anyway."
    )
    world.say(
        f"Instead of hiding from {challenge.risk}, {pig.id} looked at it like a "
        f"mischievous game."
    )


def resolve(world: World, comfort: Comfort, pig: Entity, pal: Entity) -> None:
    pig.memes["confidence"] += 1
    pig.memes["lesson"] += 1
    pal.memes["joy"] += 1
    world.say(
        f"With a grin, {pig.id} used {comfort.phrase} {comfort.effect}."
    )
    world.say(
        f"The crowd laughed in the happy kind of way, {pal.id} clapped, and "
        f"{pig.id} finished the act standing taller than before."
    )
    world.say(
        f"That night, {pig.id} learned that bravery does not mean being perfect; "
        f"it means trying, smiling, and keeping going even when the wobble shows up."
    )


def tell(challenge: Challenge, joke: Joke, comfort: Comfort, seed_name: str) -> World:
    world = World()
    pig = world.add(Entity(id=seed_name, kind="character", type="pig", label="piggy", role="hero"))
    pal = world.add(Entity(id="pal", kind="character", type="mouse", label="best pal", role="helper"))
    stage = world.add(Entity(id="stage", kind="thing", type="stage", label="stage"))

    pig.memes["bravery"] = 0.0
    pal.memes["humor"] = 0.0
    world.facts["challenge"] = challenge
    world.facts["joke"] = joke
    world.facts["comfort"] = comfort
    world.facts["stage"] = stage

    intro(world, pig, pal, challenge)
    world.para()
    problem(world, pig, challenge)
    humor_beat(world, joke, pal)
    _do_challenge(world)
    brave_turn(world, pig, challenge)
    world.para()
    resolve(world, comfort, pig, pal)
    return world


CHALLENGES = {
    "stage": Challenge("stage", "the little stage", "the curtain wiggled open and everyone looked over", "the shiny microphone"),
    "board": Challenge("board", "the kitchen table", "the chair scooted with a squeak", "the stack of tall plates"),
    "parade": Challenge("parade", "the village path", "the banner flipped in the wind", "the wobbling cart"),
}

JOKES = {
    "banana": Joke("banana", "What did the banana say to the slide?", "Wheee, peel the speed!", "The joke bounced like a rubber ball.", {"humor"}),
    "hat": Joke("hat", "Why did the hat sit still?", "Because it did not want to lose its top!", "That was so silly the piggy snorted.", {"humor"}),
    "pickle": Joke("pickle", "What do you call a pickle who sings?", "A dill-lightful star!", "The punch line made the room giggle.", {"humor"}),
}

COMFORTS = {
    "spray": Comfort("spray", "tiny spray bottle", "a tiny spray bottle", "to make the stage shine like a joke turned into a sparkle", {"bravery", "lesson"}),
    "ribbon": Comfort("ribbon", "red ribbon", "a red ribbon", "to give the act a brave little bow at the end", {"bravery", "lesson"}),
    "trick": Comfort("trick", "trick cup", "a trick cup", "to turn the final wobble into a funny little flourish", {"bravery", "lesson"}),
}

PIG_NAMES = ["Piggy", "Pippa", "Porky", "Penny", "Percy", "Peaches"]
PAL_NAMES = ["Milo", "Mina", "Moppet", "Mabel"]

@dataclass
class StoryParams:
    challenge: str
    joke: str
    comfort: str
    pig_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(c, j, k) for c in CHALLENGES for j in JOKES for k in COMFORTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A piggy comedy story world with bravery, humor, and a lesson learned.")
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--joke", choices=JOKES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name", choices=PIG_NAMES)
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
              if (args.challenge is None or c[0] == args.challenge)
              and (args.joke is None or c[1] == args.joke)
              and (args.comfort is None or c[2] == args.comfort)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    challenge, joke, comfort = rng.choice(sorted(combos))
    pig_name = args.name or rng.choice(PIG_NAMES)
    return StoryParams(challenge, joke, comfort, pig_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny piggy story for a young child that includes the word "piggy" and a brave ending.',
        f"Tell a comedy story where {f['comfort'].label} helps {f['challenge'].risk} turn from scary to silly.",
        f"Write a short story about {f['pig'].id} being nervous at {f['challenge'].scene}, then finding courage with a joke.",
    ]


def story_qa(world: World) -> list[QAItem]:
    pig = world.get("piggy")
    challenge: Challenge = world.facts["challenge"]
    joke: Joke = world.facts["joke"]
    comfort: Comfort = world.facts["comfort"]
    return [
        QAItem(
            question="What was piggy trying to do?",
            answer=f"{pig.id} was trying to be brave at {challenge.scene}. {pig.id} wanted to keep going even after feeling nervous.",
        ),
        QAItem(
            question="What made the story funny?",
            answer=f"{world.get('pal').id} told a joke about bananas / hats / pickles, and the silly line made everyone laugh. The humor helped the fear shrink a little.",
        ),
        QAItem(
            question="What lesson did piggy learn?",
            answer=f"{pig.id} learned that bravery means trying again even when things wobble. The funny helper and the brave step forward turned the scary moment into a lesson learned.",
        ),
        QAItem(
            question="How did the ending change piggy?",
            answer=f"At the end, {pig.id} stood taller and felt more confident. The little comedy moment became a memory about courage, not embarrassment.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is bravery?", "Bravery means doing something hard or scary anyway. It does not mean you never feel nervous."),
        QAItem("Why can humor help?", "Humor can make a person relax and feel lighter. A joke can turn a scary mood into a friendlier one."),
        QAItem("What is a lesson learned?", "A lesson learned is something you understand better after an experience. It helps you do a wiser thing next time."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(C, J, K) :- challenge(C), joke(J), comfort(K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for c in CHALLENGES:
        lines.append(asp.fact("challenge", c))
    for j in JOKES:
        lines.append(asp.fact("joke", j))
    for k in COMFORTS:
        lines.append(asp.fact("comfort", k))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp  # noqa: F401
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(challenge=None, joke=None, comfort=None, name=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(CHALLENGES[params.challenge], JOKES[params.joke], COMFORTS[params.comfort], params.pig_name)
    world.facts.update(
        pig=world.get("piggy"),
        pal=world.get("pal"),
        challenge=CHALLENGES[params.challenge],
        joke=JOKES[params.joke],
        comfort=COMFORTS[params.comfort],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(c, j, k, "Piggy")) for c, j, k in valid_combos()[:5]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
