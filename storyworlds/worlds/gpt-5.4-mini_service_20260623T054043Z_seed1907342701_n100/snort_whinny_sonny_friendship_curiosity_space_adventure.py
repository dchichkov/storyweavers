#!/usr/bin/env python3
"""
storyworlds/worlds/snort_whinny_sonny_friendship_curiosity_space_adventure.py
==============================================================================

A standalone storyworld for a tiny Space Adventure about friendship and
curiosity, centered on the words snort, whinny, and sonny.

Seed premise:
- Sonny, Snort, and Whinny are small space explorers.
- Their friendship helps them stay together.
- Curiosity can pull one of them toward a strange place or object.
- A helpful rescue device turns the problem into a safe discovery.

The world keeps typed entities with physical meters and emotional memes, uses a
small forward-chained rule system, and includes an inline ASP twin for parity.
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper_to: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)
    risky: set[str] = field(default_factory=set)


@dataclass
class Curiosity:
    id: str
    label: str
    phrase: str
    at_risk: str
    risk_word: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    curiosity: str
    aid: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_drifts(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes["curiosity"] < THRESHOLD:
            continue
        if world.facts.get("problem_seen"):
            continue
        if ("drift", e.id) in world.fired:
            continue
        world.fired.add(("drift", e.id))
        e.meters["drift"] += 1
        e.memes["worry"] += 1
        out.append("__drift__")
    return out


def _r_scatter(world: World) -> list[str]:
    out = []
    if world.facts.get("problem_seen") and not world.facts.get("aid_used"):
        for e in world.characters():
            e.memes["worry"] += 1
        if ("scatter",) not in world.fired:
            world.fired.add(("scatter",))
            out.append("__scatter__")
    return out


CAUSAL_RULES = [Rule("drift", _r_drifts), Rule("scatter", _r_scatter)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule.apply(world)
            if parts:
                changed = True
                out.extend(p for p in parts if not p.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


PLACES = {
    "moonbase": Place("moonbase", "the moon base", "a bright dome on the moon", {"walk", "window"}, {"dust"}),
    "orbit_garden": Place("orbit_garden", "the orbit garden", "a little garden ringed by stars", {"walk", "seed"}, {"sparkle"}),
    "comet_harbor": Place("comet_harbor", "the comet harbor", "a dock beside a tail of glittering ice", {"dock", "scan"}, {"glint"}),
    "red_crater": Place("red_crater", "the red crater", "a round red pit with shiny stones", {"climb", "scan"}, {"stone"}),
}

CURIOSITIES = {
    "glowstone": Curiosity("glowstone", "a glowstone", "the glowstone", "glowstone", "glow", "side tunnel", {"glow", "stone"}),
    "star_map": Curiosity("star_map", "a star map", "the star map", "star map", "map", "chart table", {"map", "chart"}),
    "whisper_well": Curiosity("whisper_well", "a whisper well", "the whisper well", "whisper well", "whisper", "quiet pit", {"whisper", "pit"}),
    "silver_seed": Curiosity("silver_seed", "a silver seed", "the silver seed", "silver seed", "seed", "garden bed", {"seed", "silver"}),
}

AIDS = {
    "tether": Aid("tether", "a rescue tether", "the rescue tether", "hook and pull", "They clipped the tether to the rover and reeled the explorer back", {"tether", "rope"}),
    "beacon": Aid("beacon", "a little beacon lamp", "the little beacon lamp", "shine and guide", "The beacon lamp showed the safe path home", {"beacon", "light"}),
    "rover": Aid("rover", "the rover", "the rover", "roll and lift", "The rover carried everyone back to the dome", {"rover", "lift"}),
}

GIRL_NAMES = ["Whinny", "Mina", "Pia", "Luna"]
BOY_NAMES = ["Sonny", "Ronan", "Milo", "Toby"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CURIOSITIES:
            for a in AIDS:
                combos.append((p, c, a))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested choices do not form a believable space adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about friendship and curiosity.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--aid", choices=AIDS)
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
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError(explain_rejection())
    p, c, a = rng.choice(sorted(combos))
    return StoryParams(place=p, curiosity=c, aid=a)


def tell(params: StoryParams) -> World:
    place = PLACES.get(params.place)
    cur = CURIOSITIES.get(params.curiosity)
    aid = AIDS.get(params.aid)
    if not place or not cur or not aid:
        raise StoryError("Invalid story parameters.")
    world = World(place)
    sunny = world.add(Entity(id="Sunny", kind="character", type="boy", role="lead"))
    snort = world.add(Entity(id="Snort", kind="character", type="pony", role="friend"))
    whinny = world.add(Entity(id="Whinny", kind="character", type="pony", role="friend"))

    world.facts.update(place=place, curiosity=cur, aid=aid, sunny=sunny, snort=snort, whinny=whinny)
    sunny.memes["friendship"] = 2
    snort.memes["friendship"] = 2
    whinny.memes["friendship"] = 2
    sunny.memes["curiosity"] = 1
    snort.memes["curiosity"] = 1
    whinny.memes["curiosity"] = 1

    world.say(f"Sunny, Snort, and Whinny floated into {place.label}.")
    world.say(f"They were happy to be together, and even the air felt new and bright.")

    world.para()
    world.say(f"Then {sunny.id} spotted {cur.phrase} near {cur.zone}.")
    world.say(f"{snort.id} gave a friendly snort, and {whinny.id} answered with a soft whinny.")
    sunny.memes["curiosity"] += 1
    world.facts["problem_seen"] = True
    propagate(world, narrate=False)

    world.say(f"{sunny.id} leaned closer, because {cur.label} looked too interesting to ignore.")
    world.say(f"But {whinny.id} stayed beside {sunny.id} and pointed at the warning lights on the wall.")

    world.para()
    world.say(f"Together they used {aid.phrase}.")
    world.facts["aid_used"] = True
    sunny.meters["drift"] = 0
    world.say(f"{aid.ending}, and {snort.id} bumped the console with a happy snort.")
    world.say(f"{whinny.id} let out one bright whinny, and the little crew laughed as {place.detail} glowed around them.")
    world.say(f"In the end, Sunny tucked the curious thing safely away and the three friends looked out at the stars together.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child about {f["sunny"].id}, {f["snort"].id}, and {f["whinny"].id} exploring {f["place"].label}.',
        f'Include the words "snort", "whinny", and "sonny" in a friendly story where curiosity leads to a small problem and friendship fixes it.',
        f'Tell a simple story about three friends in space who discover {f["curiosity"].label} and then use {f["aid"].label} to stay safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    sunny, snort, whinny, place, cur, aid = f["sunny"], f["snort"], f["whinny"], f["place"], f["curiosity"], f["aid"]
    return [
        QAItem(question=f"Who went on the space adventure in {place.label}?", answer=f"Sunny, Snort, and Whinny went together. They stayed close because they were friends."),
        QAItem(question=f"What made Sunny curious near {place.label}?", answer=f"{cur.phrase} made Sunny curious. It looked unusual, so Sunny wanted a closer look."),
        QAItem(question=f"How did the friends stay safe when the curious thing looked risky?", answer=f"They used {aid.label}. That helped them solve the problem without drifting too far away."),
        QAItem(question=f"Why were Snort and Whinny important in the story?", answer=f"They helped Sunny with friendship. Snort and Whinny stayed nearby and helped turn the problem into a safe moment."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?", answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new."),
        QAItem(question="What is friendship?", answer="Friendship means caring about each other, helping each other, and having fun together."),
        QAItem(question="Why do explorers carry rescue tools?", answer="Explorers carry rescue tools so they can stay safe if they get stuck or drift away from the path."),
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,A) :- place(P), curiosity(C), aid(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CURIOSITIES:
        lines.append(asp.fact("curiosity", c))
    for a in AIDS:
        lines.append(asp.fact("aid", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH:", sorted(py ^ cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, curiosity=None, aid=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0 if ok else 1


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
    StoryParams(place="moonbase", curiosity="glowstone", aid="tether"),
    StoryParams(place="orbit_garden", curiosity="star_map", aid="beacon"),
    StoryParams(place="comet_harbor", curiosity="whisper_well", aid="rover"),
    StoryParams(place="red_crater", curiosity="silver_seed", aid="tether"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
