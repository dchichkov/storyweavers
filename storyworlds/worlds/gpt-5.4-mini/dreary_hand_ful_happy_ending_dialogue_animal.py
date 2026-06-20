#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dreary_hand_ful_happy_ending_dialogue_animal.py
================================================================================

A small standalone storyworld about animals on a dreary day, a hand-ful of
something needed to solve a problem, and a happy ending reached through dialogue.

The tiny domain:
- a little animal wants something for the day
- the weather is dreary
- another animal warns / helps through dialogue
- a hand-ful of useful bits is gathered
- the animals solve the problem together
- the ending proves the change with a bright, safe image

This script follows the Storyweavers storyworld contract:
- uses typed entities with physical meters and emotional memes
- state drives the prose
- has prompt, story QA, and world QA
- includes a Python reasonableness gate and inline ASP twin
- supports --verify, --asp, --show-asp, --json, --qa, --trace, -n, --all, --seed
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
    attrs: dict = field(default_factory=dict)
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


@dataclass
class Place:
    id: str
    label: str
    dreary: bool = False
    windy: bool = False
    shelter: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    kind: str
    quantity: int
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    dialogue: str
    action: str
    succeeds: bool = True
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dreary(world: World) -> list[str]:
    out: list[str] = []
    if "sky" in world.entities:
        sky = world.get("sky")
        if sky.meters["drear"] >= THRESHOLD and ("dreary", "mood") not in world.fired:
            world.fired.add(("dreary", "mood"))
            for ch in world.characters():
                ch.memes["slump"] += 1
            out.append("__dreary__")
    return out


def _r_helpful_handful(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("needed") and world.facts.get("collected") >= world.facts["needed"].quantity:
        sig = ("cheered", world.facts["need"].id)
        if sig not in world.fired:
            world.fired.add(sig)
            for ch in world.characters():
                ch.memes["hope"] += 1
            out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("dreary", "weather", _r_dreary), Rule("hope", "social", _r_helpful_handful)]


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


def enough_handful(need: Need, count: int) -> bool:
    return count >= need.quantity


def action_plan(need: Need, helper: Helper) -> bool:
    return helper.succeeds and need.kind in helper.tags


def predict_help(world: World, need_id: str, helper_id: str) -> bool:
    sim = world.copy()
    need = sim.facts["need"]
    helper = sim.facts["helper"]
    return action_plan(need, helper) and enough_handful(need, sim.facts["collected"])


def setup(world: World, hero: Entity, friend: Entity, place: Place, need: Need) -> None:
    hero.memes["want"] += 1
    friend.memes["care"] += 1
    world.say(
        f"On a dreary morning, {hero.id} and {friend.id} were outside by {place.label}. "
        f"The clouds hung low, and the world felt gray and quiet."
    )
    world.say(
        f'{hero.id} peered at the ground. "{need.phrase} would help," {hero.id} said. '
        f'"I wish we had some."'
    )


def dialogue(world: World, friend: Entity, hero: Entity, helper: Helper, need: Need) -> None:
    friend.memes["hope"] += 1
    world.say(
        f'"{hero.id}," {friend.id} said softly, "let\'s look together. '
        f'I think a {helper.label} might be enough if we can gather a hand-ful."'
    )
    world.say(
        f'"A hand-ful?" {hero.id} asked.'
    )
    world.say(
        f'"Yes," {friend.id} said. "{helper.dialogue}"'
    )


def gather(world: World, hero: Entity, helper: Helper, need: Need) -> None:
    world.facts["collected"] = need.quantity
    hero.meters["held"] += need.quantity
    hero.memes["pride"] += 1
    world.say(
        f'Together they found a hand-ful of {need.label}. {hero.id} tucked them into '
        f'{hero.pronoun("possessive")} paw as carefully as could be.'
    )
    world.say(
        f"Then {hero.id} used the {helper.label} exactly as {helper.action}, and the little job was done."
    )
    propagate(world, narrate=False)


def ending(world: World, hero: Entity, friend: Entity, place: Place, need: Need) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After that, the dreary day did not feel dreary anymore. {place.label} looked "
        f"brighter, and {hero.id} gave {friend.id} a happy nuzzle."
    )
    world.say(
        f'The two friends sat under {place.shelter}, warm and safe, while the last gray clouds drifted away.'
    )


def tell(place: Place, need: Need, helper: Helper, hero_name: str = "Milo",
         friend_name: str = "Pip") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="animal", role="hero", traits=["small", "curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="animal", role="friend", traits=["kind", "steady"]))
    sky = world.add(Entity(id="sky", type="weather", label="the sky"))
    sky.meters["drear"] = 1.0 if place.dreary else 0.0

    world.facts.update(place=place, need=need, helper=helper, needed=need, collected=0)
    setup(world, hero, friend, place, need)
    world.para()
    dialogue(world, friend, hero, helper, need)
    world.para()
    if predict_help(world, need.id, helper.id):
        gather(world, hero, helper, need)
        ending(world, hero, friend, place, need)
    else:
        raise StoryError("The chosen helper cannot actually solve the need in this little world.")
    world.facts.update(hero=hero, friend=friend, sky=sky, outcome="happy")
    return world


PLACES = {
    "orchard": Place("orchard", "the orchard", dreary=True, shelter="the old shed", tags={"outdoor"}),
    "pond": Place("pond", "the pond", dreary=True, shelter="the reed hut", tags={"outdoor"}),
    "barnyard": Place("barnyard", "the barnyard", dreary=True, shelter="the hayloft", tags={"outdoor"}),
}

NEEDS = {
    "feed": Need("feed", "feed", "a hand-ful of seeds", "seed", 5, "spread them under the warm branch", tags={"seed"}),
    "straw": Need("straw", "straw", "a hand-ful of straw", "nest", 4, "line the nest with it", tags={"nest"}),
    "berries": Need("berries", "berries", "a hand-ful of berries", "snack", 3, "share them one by one", tags={"snack"}),
}

HELPERS = {
    "cup": Helper("cup", "little cup", "a little cup", "we can scoop them up one by one", "scooping them into the cup", tags={"seed", "nest", "snack"}),
    "basket": Helper("basket", "woven basket", "a woven basket", "we can carry a hand-ful at a time", "carrying them in the basket", tags={"seed", "nest", "snack"}),
}

NAMES = ["Milo", "Pip", "Toby", "Nora", "Luna", "Hazel", "Roo", "Benny"]


@dataclass
class StoryParams:
    place: str
    need: str
    helper: str
    hero: str
    friend: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for pid, place in PLACES.items():
        for nid, need in NEEDS.items():
            for hid, helper in HELPERS.items():
                if enough_handful(need, need.quantity) and action_plan(need, helper):
                    combos.append((pid, nid, hid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small animal storyworld about a dreary day and a hand-ful solution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
              and (args.need is None or c[1] == args.need)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, need, helper = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    return StoryParams(place, need, helper, hero, friend)


ASP_RULES = r"""
helpful(H, N) :- helper(H), need(N), need_kind(N, K), helper_kind(H, K).
enough(N) :- need(N), collected(N, C), quantity(N, Q), C >= Q.
valid(P, N, H) :- place(P), need(N), helper(H), helpful(H, N).
outcome(happy) :- valid(_, N, H), enough(N), helpful(H, N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        lines.append(asp.fact("need_kind", nid, n.kind))
        lines.append(asp.fact("quantity", nid, n.quantity))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for t in sorted(h.tags):
            lines.append(asp.fact("helper_kind", hid, t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos()")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, need=None, helper=None, hero=None, friend=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print("SMOKE TEST FAILED:", e)
        traceback.print_exc()
    else:
        print("OK: verify smoke test passed.")
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place: Place = f["place"]
    need: Need = f["need"]
    helper: Helper = f["helper"]
    return [
        f'Write an animal story for a young child that includes the word "dreary" and the phrase "hand-ful".',
        f"Tell a gentle story about {f['hero'].id} and {f['friend'].id} at {place.label} on a dreary day, where dialogue helps them solve a problem.",
        f"Write a happy-ending animal story in which the animals gather {need.phrase} and use a {helper.label} together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    place: Place = f["place"]
    need: Need = f["need"]
    helper: Helper = f["helper"]
    return [
        ("Who is the story about?", f"It is about {hero.id} and {friend.id}, two small animals who spend a dreary day together."),
        ("Why was the day dreary?", f"The sky was gray and the place felt quiet and damp. That dreary feeling is what made the animals want to fix their little problem together."),
        ("What did they need?", f"They needed {need.phrase}, which came in a hand-ful and would help solve the problem."),
        ("How did they solve it?", f"They listened to each other, gathered the hand-ful, and used {helper.phrase}. Their dialogue turned the problem into an easy plan."),
        ("How did the story end?", f"It ended happily. The animals were warm and safe under {place.shelter}, and the gray day stopped feeling sad."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does dreary mean?", "Dreary means gray, dull, and a little sad-looking, like a day with low clouds and no sunshine."),
        ("What does hand-ful mean?", "A hand-ful is the amount you can hold in one hand at once. It is a small pile, not a big one."),
        ("What is dialogue?", "Dialogue is when characters talk to each other in a story."),
        ("What makes a happy ending?", "A happy ending is when the problem gets solved and the characters end the story feeling safe or joyful."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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


CURATED = [
    StoryParams("orchard", "feed", "cup", "Milo", "Pip"),
    StoryParams("pond", "straw", "basket", "Luna", "Toby"),
    StoryParams("barnyard", "berries", "basket", "Roo", "Nora"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], NEEDS[params.need], HELPERS[params.helper], params.hero, params.friend)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def asp_sensible() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, n, h in asp_valid_combos():
            print(f"  {p:10} {n:8} {h}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
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
