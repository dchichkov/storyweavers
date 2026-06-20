#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py
==================================================================

A standalone story world for a small adventure tale with a moral-value twist:
children prepare a tiny spa day for a tired creature, learn that kindness and
patience matter more than winning, and then discover the "spa" was meant for
someone else all along.

The world uses typed entities with physical meters and emotional memes, a tiny
forward-chaining simulation, grounded QA generation, and an inline ASP twin for
the compatibility gate.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/spa_moral_value_twist_adventure.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    hidden: str
    twist_hint: str
    adventure_word: str


@dataclass
class SpaTool:
    id: str
    label: str
    use: str
    safe: bool = True


@dataclass
class Prize:
    id: str
    label: str
    place: str
    fragile: bool = False


@dataclass
class Challenge:
    id: str
    problem: str
    action: str
    lesson: str
    power: int
    sense: int


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["soothed"] >= THRESHOLD and ("calm", e.id) not in world.fired:
            world.fired.add(("calm", e.id))
            e.memes["calm"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def plausible_challenge(ch: Challenge) -> bool:
    return ch.sense >= SENSE_MIN and ch.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p.id, t.id, c.id) for p in PLACES.values() for t in TOOLS.values() for c in CHALLENGES.values()
            if plausible_challenge(c) and t.safe and p.id in {"garden_spa", "cliff_spa"}]


def spa_need(world: World, place: Place, hero: Entity, prize: Entity, tool: SpaTool) -> None:
    world.say(
        f"On a bright adventure morning, {hero.id} stepped into {place.scene}. "
        f"{place.label.capitalize()} smelled like warm water and mint, and the little {prize.label} was waiting nearby."
    )
    world.say(
        f"{hero.id} hoped to use the {tool.label} for a proper spa day, because {place.hidden} was hard to reach and needed care."
    )


def tempt(world: World, hero: Entity, prize: Entity, challenge: Challenge) -> None:
    hero.memes["want"] += 1
    world.say(
        f'But then {hero.id} found a shiny sign that pointed deeper into the path. "{challenge.problem}" it seemed to promise.'
    )
    world.say(
        f"{hero.id} wanted to rush ahead, even though the adventure was supposed to be gentle."
    )


def warn(world: World, helper: Entity, hero: Entity, challenge: Challenge, place: Place) -> None:
    helper.memes["moral_value"] += 1
    world.say(
        f'{helper.id} touched {hero.id}\'s sleeve. "{challenge.lesson}," {helper.pronoun()} said. '
        f'"A real adventure is not about grabbing everything first. It is about helping the thing that needs us most."'
    )
    world.say(f"{helper.id} also pointed toward {place.twist_hint}, as if the trail itself was trying to be honest.")


def choose_kindness(world: World, hero: Entity, helper: Entity, prize: Prize, challenge: Challenge, tool: SpaTool) -> None:
    hero.meters["soothed"] += 1
    helper.meters["soothed"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f"{hero.id} took a deep breath and chose the kinder path. {hero.id} used the {tool.label} to clean the {prize.label} first, slowly and carefully."
    )
    world.say(
        f"That left time for a true spa moment: warm cloth, quiet water, and a patient hand instead of a hurried grab."
    )
    propagate(world)


def reveal_twist(world: World, hero: Entity, helper: Entity, place: Place, prize: Prize) -> None:
    world.say(
        f"Then came the twist. The hidden path led not to treasure, but to {place.hidden}, where the {prize.label} belonged."
    )
    world.say(
        f"{hero.id} and {helper.id} realized the adventure had been a lesson: if they had rushed, the {prize.label} would have stayed lost and lonely."
    )


def end(world: World, hero: Entity, helper: Entity, prize: Prize, place: Place) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At the end, {hero.id} carried the {prize.label} home, and {helper.id} smiled. "
        f"The spa stayed quiet, the path stayed bright, and the adventure ended with a good deed shining like a little lantern."
    )


def tell(place: Place, tool: SpaTool, prize: Prize, challenge: Challenge,
         hero_name: str = "Mia", helper_name: str = "Ben") -> World:
    w = World()
    hero = w.add(Entity(hero_name, "character", "girl", role="hero"))
    helper = w.add(Entity(helper_name, "character", "boy", role="helper"))
    prize_ent = w.add(Entity("prize", "thing", prize.id, label=prize.label))
    w.facts.update(hero=hero, helper=helper, prize=prize_ent, place=place, tool=tool, challenge=challenge)
    spa_need(w, place, hero, prize_ent, tool)
    w.para()
    tempt(w, hero, prize_ent, challenge)
    warn(w, helper, hero, challenge, place)
    w.para()
    choose_kindness(w, hero, helper, prize, challenge, tool)
    reveal_twist(w, hero, helper, place, prize)
    w.para()
    end(w, hero, helper, prize, place)
    w.facts["kindness"] = hero.memes["kindness"] >= THRESHOLD
    w.facts["resolved"] = True
    return w


PLACES = {
    "garden_spa": Place("garden_spa", "the garden spa", "a tiny garden spa with warm stones and a bubbling tub",
                        "the old lily pond behind the hedge", "the path bent toward the willow tree", "adventure"),
    "cove_spa": Place("cove_spa", "the cove spa", "a shell-lined cove spa with salty steam and smooth pebbles",
                      "the cave where the lost crab hid", "the tide whispered from the dark rocks", "adventure"),
}

TOOLS = {
    "brush": SpaTool("brush", "soft brush", "gently scrub"),
    "towel": SpaTool("towel", "warm towel", "dry carefully"),
    "scent": SpaTool("scent", "minty scent", "make the spa feel fresh"),
}

PRIZES = {
    "turtle": Prize("turtle", "little turtle", "pond", fragile=True),
    "crab": Prize("crab", "tiny crab", "rocks", fragile=False),
}

CHALLENGES = {
    "rushed": Challenge("rushed", "the quickest way is the best way", "race ahead", "Sometimes the kindest choice is the slower one.", 2, 3),
    "grabby": Challenge("grabby", "there might be treasure if we hurry", "snatch first", "It is wiser to help than to snatch.", 2, 3),
}

GOLDEN = [
    ("garden_spa", "brush", "turtle"),
    ("cove_spa", "towel", "crab"),
]


@dataclass
class StoryParams:
    place: str
    tool: str
    prize: str
    challenge: str
    hero: str
    helper: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the word "spa" and shows a kind choice.',
        f"Tell a short story where {f['hero'].id} wants to hurry through a spa-like adventure, but {f['helper'].id} teaches patience and care.",
        f"Write a twist-ending story about a spa day where being kind matters more than getting treasure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, place, challenge = f["hero"], f["helper"], f["prize"], f["place"], f["challenge"]
    return [
        QAItem(
            question="What did the children want to do at the spa?",
            answer=f"They wanted to care for the {prize.label} and make the spa feel calm and clean. They also wanted to have an adventure without hurting anyone or anything."
        ),
        QAItem(
            question="What lesson did the helper teach?",
            answer=f"{helper.id} taught that a real adventure should be kind and patient. That mattered because rushing would have left the {prize.label} lonely and uncared for."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the path did not lead to treasure at all. It led to the place where the {prize.label} belonged, so the best reward was doing the right thing."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a spa?", "A spa is a place where people relax, wash, and feel refreshed. It is usually calm and quiet."),
        QAItem("What does kindness mean?", "Kindness means helping, caring, and choosing to do something gentle. Kind actions can make another creature feel safe."),
        QAItem("What is a twist in a story?", "A twist is a surprising turn that changes what you expected. It can make the story feel exciting."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, T, C) :- place(P), tool(T), challenge(C), tool_safe(T), challenge_sense(C, S), S >= sense_min.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if tool.safe:
            lines.append(asp.fact("tool_safe", t))
    for c, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", c))
        lines.append(asp.fact("challenge_sense", c, ch.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, tool=None, prize=None, challenge=None, hero=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Spa adventure storyworld with a moral-value twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
              and (args.tool is None or c[1] == args.tool)
              and (args.challenge is None or c[2] == args.challenge)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, challenge = rng.choice(sorted(combos))
    prize = args.prize or rng.choice(sorted(PRIZES))
    hero = args.hero or rng.choice(["Mia", "Ava", "Leo", "Noah"])
    helper = args.helper or rng.choice(["Ben", "Zoe", "Lily", "Theo"])
    return StoryParams(place, tool, prize, challenge, hero, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], PRIZES[params.prize], CHALLENGES[params.challenge], params.hero, params.helper)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p, t, pr, c, "Mia", "Ben")) for p, t, pr in GOLDEN for c in CHALLENGES][:3]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx+1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
