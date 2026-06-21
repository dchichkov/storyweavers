#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/except_escalator_bravery_nursery_rhyme.py
===========================================================================

A tiny storyworld about a brave child on an escalator, with a nursery-rhyme
cadence and a small twist around the word "except".

Premise:
- A child rides an escalator with a caregiver.
- The child is brave enough to keep moving, but one step ahead is a little
  shadow of worry: the child has forgotten one tiny thing except a bright idea.
- The turn comes when a dropped toy rolls toward the moving steps.
- Bravery means asking for help, staying calm, and doing the sensible thing.
- The ending image shows a safer, cheerful ride and a remembered rule.

This file is self-contained and uses only the standard library plus the shared
storyworld result containers. ASP support is included inline via a rule twin.
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
BRAVERY_INIT = 3.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
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

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    moving: bool = True
    narrow: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class CareRule:
    id: str
    label: str
    sense: int
    effect: int
    text: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    caregiver: str
    bravery: int = 4
    delay: int = 0
    seed: Optional[int] = None


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


PLACES = {
    "escalator": Place(id="escalator", label="the escalator", moving=True, narrow=True, tags={"escalator"}),
}

CARE_RULES = {
    "wait": CareRule(
        id="wait",
        label="wait for the step",
        sense=3,
        effect=2,
        text="waited for the moving step to carry the little feet safely down",
        fail="waited, but the rush had already carried things too close",
        tags={"safety", "wait"},
    ),
    "hold_rail": CareRule(
        id="hold_rail",
        label="hold the rail",
        sense=4,
        effect=3,
        text="held the rail and stood still while the steps kept their rhyme",
        fail="held the rail, but the toy still skittered along the edge",
        tags={"safety", "rail"},
    ),
    "call_adult": CareRule(
        id="call_adult",
        label="call for a grown-up",
        sense=5,
        effect=5,
        text="called a grown-up right away and kept everyone calm",
        fail="called for help, and the grown-up came just in time",
        tags={"safety", "adult"},
    ),
    "chase_toy": CareRule(
        id="chase_toy",
        label="chase the toy",
        sense=1,
        effect=0,
        text="chased the toy, which was not the wise thing to do",
        fail="chased the toy, and the steps got even trickier",
        tags={"unsafe", "toy"},
    ),
}

THING_NAMES = {
    "ball": "a red ball",
    "teddy": "a little teddy",
    "book": "a picture book",
}

HELPFUL_OBJECT = "ball"
NURSERY_OPENERS = [
    "Up went the steps and down went the day",
    "Tickety-tick the escalator swayed",
    "Step by step and song by song",
]

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Max", "Noah"]


def reasonable_place(place: Place) -> bool:
    return place.moving and place.narrow


def sensible_rules() -> list[CareRule]:
    return [r for r in CARE_RULES.values() if r.sense >= 3]


def best_rule() -> CareRule:
    return max(CARE_RULES.values(), key=lambda r: r.sense)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, r) for p in PLACES for r in CARE_RULES if reasonable_place(PLACES[p]) and CARE_RULES[r].sense >= 3]


def outcome_of(params: StoryParams) -> str:
    if params.bravery >= BRAVERY_INIT and params.delay == 0:
        return "brave"
    return "cautious"


def initial_resistance(bravery: int) -> float:
    return float(bravery) + 1.0


def _r_tense(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    toy = world.get("toy")
    if toy.meters["rolling"] >= THRESHOLD and ("tense", toy.id) not in world.fired:
        world.fired.add(("tense", toy.id))
        child.memes["worry"] += 1
        out.append("The little toy rolled and made the child’s heart wobble.")
    return out


CAUSAL_RULES = [Rule("tense", _r_tense)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def predict_event(world: World) -> dict:
    sim = world.copy()
    sim.get("toy").meters["rolling"] += 1
    propagate(sim, narrate=False)
    return {"worry": sim.get("child").memes["worry"], "rolling": sim.get("toy").meters["rolling"]}


def start(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(f"{NURSERY_OPENERS[0]}, and {child.id} rode {place.label} with {helper.id}.")
    world.say(
        f"{child.id} was brave, bright-eyed, and quick with a grin, except for one tiny worry tucked in {child.pronoun('possessive')} pocket."
    )


def want(world: World, child: Entity, helper: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'“I can do this,” said {child.id}. “I can ride the steps all by myself, except I still want {helper.id} near.”'
    )
    world.say(f"{helper.id} nodded, and the escalator sang its steady little song.")


def drop_toy(world: World, child: Entity) -> None:
    toy = world.get("toy")
    toy.meters["rolling"] += 1
    world.say(
        f"Then oops and off it went: {thing_phrase(toy.id)} slipped from {child.id}'s hand and rolled toward the moving teeth of the stair."
    )
    propagate(world, narrate=False)


def warn(world: World, helper: Entity, child: Entity) -> None:
    pred = predict_event(world)
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f'{helper.id} took a breath and said, “Hold still, {child.id}. A rolling thing on an escalator can turn scary in a blink.”'
    )


def brave_choice(world: World, child: Entity, helper: Entity, rule: CareRule) -> None:
    world.say(f"{child.id} felt the wobble in {child.pronoun('possessive')} knees, but bravery meant listening.")
    if rule.id == "call_adult":
        world.say(f'{child.id} shouted, “Help, please!” and {helper.id} reached the emergency button for a grown-up.')
    elif rule.id == "hold_rail":
        world.say(f"{child.id} held the rail with both hands while {helper.id} bent carefully to catch the toy.")
    else:
        world.say(f"{child.id} waited on the step, as still as a paper crown, while {helper.id} handled the rest.")


def resolve(world: World, child: Entity, helper: Entity) -> None:
    toy = world.get("toy")
    toy.meters["rolling"] = 0
    child.memes["worry"] = 0
    child.memes["joy"] += 1
    helper.memes["calm"] += 1
    world.say(
        f"The little ball was caught, the steps kept turning, and the day went safe again."
    )
    world.say(
        f"At the top of the ride, {child.id} laughed and tucked {thing_phrase(toy.id)} under {child.pronoun('possessive')} arm, remembering the rhyme: brave feet, steady hands, no chasing on the stairs."
    )


def thing_phrase(tid: str) -> str:
    return THING_NAMES.get(tid, "a small toy")


def tell(place: Place, rule: CareRule, params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=params.caregiver, role="caregiver", label="the caregiver"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label="toy"))
    child.memes["bravery"] = float(params.bravery)
    helper.memes["calm"] = 1.0
    world.add(Entity(id=place.id, kind="thing", type="place", label=place.label))
    start(world, child, helper, place)
    world.para()
    want(world, child, helper)
    warn(world, helper, child)
    world.para()
    drop_toy(world, child)
    brave_choice(world, child, helper, rule)
    resolve(world, child, helper)
    world.facts.update(
        child=child,
        helper=helper,
        caregiver=caregiver,
        toy=toy,
        place=place,
        rule=rule,
        outcome=outcome_of(params),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, helper, rule = f["child"], f["helper"], f["rule"]
    return [
        f'Write a short nursery-rhyme-style story for a small child on an escalator that includes the word "except".',
        f"Tell a gentle bravery story where {child.id} rides an escalator, a toy slips, and {helper.id} helps with a calm, safe choice.",
        f'Write a child-facing rhyme about being brave on an escalator, but remembering that {rule.label} is the wiser thing to do.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, toy = f["child"], f["helper"], f["toy"]
    return [
        QAItem(
            question=f"What was {child.id} doing?",
            answer=f"{child.id} was riding the escalator with {helper.id}. The ride started like a little rhyme, except the child needed a brave choice when the toy rolled away."
        ),
        QAItem(
            question="What went wrong?",
            answer=f"{thing_phrase(toy.id)} slipped and rolled toward the moving steps. That made the moment feel scary, because an escalator keeps moving and a rolling toy can be hard to reach."
        ),
        QAItem(
            question="How did bravery help?",
            answer=f"{child.id} stayed calm, listened to {helper.id}, and chose the safe thing instead of panicking. Bravery here meant asking for help and holding still until the toy was caught."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an escalator?",
            answer="An escalator is a moving staircase that carries people up or down. It is helpful, but children should keep hands, feet, and toys steady on it."
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel a little scared. It can look like staying calm, listening, and asking for help."
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="escalator", child_name="Mia", child_gender="girl", helper_name="Ben", helper_gender="boy", caregiver="mother", bravery=4, delay=0, seed=1),
    StoryParams(place="escalator", child_name="Leo", child_gender="boy", helper_name="Nora", helper_gender="girl", caregiver="father", bravery=5, delay=0, seed=2),
]


def explain_rejection(place: Place, rule: CareRule) -> str:
    if not reasonable_place(place):
        return "(No story: this setting does not make a moving-stairs scene.)"
    if rule.sense < 3:
        return f"(No story: the choice '{rule.id}' is not a sensible bravery move.)"
    return "(No story: this combination is not reasonable.)"


def valid_story_rules() -> list[str]:
    return [r.id for r in sensible_rules()]


ASP_RULES = r"""
reasonable_place(P) :- place(P), moving(P), narrow(P).
sensible_rule(R) :- rule(R), sense(R,S), sense_min(M), S >= M.
valid_story(P,R) :- reasonable_place(P), sensible_rule(R).

brave(C) :- bravery(C, B), bravery_init(I), B >= I.
dropped_toy(T) :- toy(T), rolling(T, N), N >= 1.
worry(C) :- dropped_toy(_), child(C), brave(C).

outcome(brave) :- brave(_), not late(_).
outcome(cautious) :- not outcome(brave).

#show valid_story/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.moving:
            lines.append(asp.fact("moving", pid))
        if p.narrow:
            lines.append(asp.fact("narrow", pid))
    for rid, r in CARE_RULES.items():
        lines.append(asp.fact("rule", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", 3))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set((p, r) for p, r in valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP does not match valid_combos().")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: default story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme escalator bravery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rule", choices=CARE_RULES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--bravery", type=int, choices=[3, 4, 5, 6])
    ap.add_argument("--delay", type=int, choices=[0, 1])
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
    place = args.place or "escalator"
    if place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if args.rule and CARE_RULES[args.rule].sense < 3:
        raise StoryError(explain_rejection(PLACES[place], CARE_RULES[args.rule]))
    rule = args.rule or rng.choice(valid_story_rules())
    bravery = args.bravery if args.bravery is not None else rng.choice([3, 4, 5, 6])
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if child_gender == "girl" else "girl"
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        caregiver=caregiver,
        bravery=bravery,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("(No story: invalid place.)")
    if params.delay not in (0, 1):
        raise StoryError("(No story: invalid delay.)")
    place = PLACES[params.place]
    rule = CARE_RULES[valid_story_rules()[0]] if params.bravery >= 3 else CARE_RULES["wait"]
    for r in CARE_RULES.values():
        if r.id == "call_adult":
            rule = r if params.delay else rule
    world = tell(place, rule, params)
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
        print(asp_program("", "#show valid_story/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, r in combos:
            print(f"  {p} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
