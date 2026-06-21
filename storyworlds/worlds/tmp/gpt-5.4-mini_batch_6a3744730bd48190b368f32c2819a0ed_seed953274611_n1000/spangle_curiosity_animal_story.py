#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spangle_curiosity_animal_story.py
==================================================================

A small animal storyworld about curiosity, a shiny spangle, and the choice to
ask for help instead of sneaking into trouble.

The premise is a child-facing animal tale: a curious little animal spots a
spangle in a place that is tempting but not quite safe, explores a little too
far, gets into a tight spot, and then learns a calmer way to solve the problem.
The story is generated from world state rather than from a fixed paragraph with
swapped nouns.
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
    dark: bool = False
    narrow: bool = False
    safe_return: bool = True


@dataclass
class ShineThing:
    id: str
    label: str
    phrase: str
    sparkly: bool = True
    tiny: bool = False
    can_fall: bool = True


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str


@dataclass
class StoryParams:
    place: str
    animal1: str
    animal1_type: str
    animal2: str
    animal2_type: str
    helper: str
    helper_type: str
    shine: str
    response: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    if world.facts.get("seen_spangle") and not world.facts.get("help_called"):
        for e in world.characters():
            if e.role == "helper":
                e.memes["worry"] += 1
        if ("worry",) not in world.fired:
            world.fired.add(("worry",))
            out.append("__worry__")
    return out


def _r_slowdown(world: World) -> list[str]:
    out = []
    if world.facts.get("in_tight_spot") and not world.facts.get("help_called"):
        for e in world.characters():
            if e.role in {"curious", "helper"}:
                e.meters["stuck"] += 1
        if ("slowdown",) not in world.fired:
            world.fired.add(("slowdown",))
            out.append("__tight__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("slowdown", _r_slowdown)]


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


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if not place.dark:
            continue
        for shine_id, shine in SHINES.items():
            if not shine.sparkly:
                continue
            for response in RESPONSES.values():
                if response.sense >= 2:
                    combos.append((place_id, shine_id, response.id))
    return combos


def story_problem(place: Place, shine: ShineThing) -> bool:
    return place.dark and shine.sparkly and shine.can_fall


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def predict(world: World, shine_id: str) -> dict:
    sim = world.copy()
    sim.facts["seen_spangle"] = True
    sim.facts["in_tight_spot"] = True
    propagate(sim, narrate=False)
    return {"stuck": any(e.meters["stuck"] >= THRESHOLD for e in sim.characters())}


def tell(place: Place, a: Entity, b: Entity, helper: Entity, shine: ShineThing,
         response: Response, delay: int = 0) -> World:
    world = World()
    world.add(Entity(id=a.id, kind="character", type=a.type, role="curious"))
    world.add(Entity(id=b.id, kind="character", type=b.type, role="friend"))
    world.add(Entity(id=helper.id, kind="character", type=helper.type, role="helper"))
    world.add(Entity(id=place.id, type="place", label=place.label))
    world.add(Entity(id=shine.id, type="thing", label=shine.label))
    a = world.get(a.id)
    b = world.get(b.id)
    helper = world.get(helper.id)

    a.memes["curiosity"] = 2.0
    b.memes["calm"] = 1.0
    helper.memes["kindness"] = 2.0

    world.say(
        f"One evening, {a.id} and {b.id} were exploring near {place.label}. "
        f"They noticed a {shine.label} that looked like a little star on the ground."
    )
    world.say(
        f'{a.id} tilted {a.pronoun("possessive")} head. "What is that shiny spangle?" '
        f"{a.pronoun()} asked, and {b.id} stepped closer to look."
    )
    world.facts["seen_spangle"] = True
    world.facts["helper"] = helper.id
    world.facts["shine"] = shine.id
    world.facts["place"] = place.id

    world.para()
    world.say(
        f"But {place.label} was {'' if not place.narrow else 'narrow and '}dark, "
        f"and the little path led around a spot where the floor dipped down."
    )
    world.say(
        f"{b.id} frowned. \"Let's be careful,\" {b.pronoun()} said, because curious paws "
        f"can slip when they reach too fast."
    )

    world.facts["in_tight_spot"] = True
    propagate(world, narrate=False)
    a.meters["near_edge"] += 1

    if response.id == "call":
        world.para()
        world.say(
            f"{a.id} reached, then stopped and called for {helper.id} instead."
        )
        world.facts["help_called"] = True
        helper.memes["pride"] += 1
        world.say(
            f"{helper.id} came right over, lifted the spangle with a twig, and "
            f"set it in {a.id}'s paw so nobody had to climb into the dip."
        )
        world.say(
            f"That made {a.id} feel brave in a new way, because asking for help kept "
            f"the night calm."
        )
    else:
        world.para()
        world.say(
            f"{a.id} tried to grab the spangle first. It slipped, rolled toward the dip, "
            f"and {a.id} had to scoot after it."
        )
        world.facts["help_called"] = False
        if is_contained(response, delay):
            world.say(
                f"Then {helper.id} rushed over and {response.text.replace('{shine}', shine.label)}."
            )
            world.say(
                f"The shiny thing was safe again, and the little animals could go home "
                f"with dusty paws and relieved hearts."
            )
        else:
            world.say(
                f"{helper.id} hurried over, but {response.fail.replace('{shine}', shine.label)}."
            )
            world.say(
                f"The spangle skittered too far into the dark little dip, so {a.id} and {b.id} "
                f"had to back away and wait for a grown-up animal to help."
            )

    if response.id == "call":
        ending = (
            f"After that, {a.id} kept the spangle as a treasure and used careful eyes "
            f"the next time curiosity tugged at {a.pronoun('possessive')} nose."
        )
    elif is_contained(response, delay):
        ending = (
            f"After that, the friends sat together in the warm grass, watching the "
            f"spangle gleam safely in {helper.id}'s paw."
        )
    else:
        ending = (
            f"After that, they stayed close to {helper.id} and promised to call for help "
            f"before the next curious leap."
        )
    world.para()
    world.say(ending)

    world.facts.update(
        place=place,
        curious=a,
        friend=b,
        helper=helper,
        shine_cfg=shine,
        response=response,
        delay=delay,
        outcome="safe" if response.id == "call" or is_contained(response, delay) else "wait",
        help_called=world.facts.get("help_called", False),
        in_tight_spot=True,
    )
    return world


PLACES = {
    "barn": Place(id="barn", label="the old barn", dark=True, narrow=True),
    "cave": Place(id="cave", label="the small cave", dark=True, narrow=True),
    "hedge": Place(id="hedge", label="the hedge tunnel", dark=True, narrow=True),
}

SHINES = {
    "spangle": ShineThing(id="spangle", label="spangle", phrase="a tiny spangle"),
    "disc": ShineThing(id="disc", label="silver disc", phrase="a silver disc"),
    "button": ShineThing(id="button", label="glittery button", phrase="a glittery button"),
}

RESPONSES = {
    "call": Response(
        id="call",
        sense=3,
        power=3,
        text="helped pick up the spangle with a long twig and a soft paw",
        fail="could not reach the spangle safely",
        qa_text="called for help and waited for a careful helper to lift the spangle",
    ),
    "reach": Response(
        id="reach",
        sense=1,
        power=1,
        text="caught the spangle and pulled it back",
        fail="could not reach the spangle safely",
        qa_text="reached carefully and pulled the spangle back",
    ),
    "twig": Response(
        id="twig",
        sense=2,
        power=2,
        text="nudged the spangle back with a twig",
        fail="nudged at the spangle, but it kept rolling",
        qa_text="nudged the spangle back with a twig",
    ),
}

ANIMALS = [
    ("Milo", "kitten"),
    ("Pip", "puppy"),
    ("Nina", "foal"),
    ("Toby", "duckling"),
    ("Kiki", "goat"),
    ("Sage", "rabbit"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about curiosity and a spangle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shine", choices=SHINES)
    ap.add_argument("--response", choices=RESPONSES)
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(No story: that response is too timid or careless for this animal tale.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.shine is None or c[1] == args.shine)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, shine, response = rng.choice(sorted(combos))
    a_name, a_type = rng.choice(ANIMALS)
    b_name, b_type = rng.choice([x for x in ANIMALS if x[0] != a_name])
    h_name, h_type = rng.choice([x for x in ANIMALS if x[0] not in {a_name, b_name}])
    delay = 0 if response == "call" else rng.randint(0, 1)
    return StoryParams(
        place=place,
        animal1=a_name,
        animal1_type=a_type,
        animal2=b_name,
        animal2_type=b_type,
        helper=h_name,
        helper_type=h_type,
        shine=shine,
        response=response,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.shine not in SHINES or params.response not in RESPONSES:
        raise StoryError("(Invalid params for this animal story.)")
    if params.response == "call":
        delay = 0
    else:
        delay = params.delay
    world = tell(
        PLACES[params.place],
        Entity(id=params.animal1, type=params.animal1_type, kind="character"),
        Entity(id=params.animal2, type=params.animal2_type, kind="character"),
        Entity(id=params.helper, type=params.helper_type, kind="character"),
        SHINES[params.shine],
        RESPONSES[params.response],
        delay=delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for a young child that includes the word "spangle" and shows curiosity leading to a small problem.',
        f"Tell a gentle story about {f['curious'].id} and {f['friend'].id} seeing a shiny spangle near {f['place'].label}.",
        f"Write a short animal adventure where curiosity makes the animals want to touch a spangle, but they choose a careful ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c = f["curious"]
    h = f["helper"]
    shine = f["shine_cfg"]
    resp = f["response"]
    qs = [
        ("What shiny thing did the animals notice?",
         f"They noticed a {shine.label}. It looked tiny, bright, and tempting in the dark place."),
        ("Why did the curious animal reach for it?",
         f"{c.id} was curious and wanted to know what the shiny thing was. Curiosity pushed {c.id} to look closer than was safe."),
    ]
    if f.get("help_called"):
        qs.append((
            "What did the curious animal do instead of getting into trouble?",
            f"{c.id} called for {h.id} and waited. That was the calm choice, so the spangle could be picked up safely."
        ))
    elif resp.id == "twig":
        qs.append((
            "How was the problem solved?",
            f"{h.id} used a twig to nudge the spangle back. That kept paws away from the dip and stopped the little problem from growing."
        ))
    else:
        qs.append((
            "What happened when help arrived?",
            f"{h.id} helped lift the spangle back into view. The animals could leave without anyone getting stuck."
        ))
    return qs


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does curiosity mean?",
         "Curiosity is the wish to look, ask, and learn about something new. It can be good, but it still needs careful behavior."),
        ("What is a spangle?",
         "A spangle is a tiny shiny piece that glitters like a little star. It can catch the eye very quickly."),
        ("Why should animals be careful in a dark narrow place?",
         "Dark narrow places can hide dips, bumps, or edges. Being careful helps keep paws and feet safe."),
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SHINES:
        lines.append(asp.fact("shine", sid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    for pid, p in PLACES.items():
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.narrow:
            lines.append(asp.fact("narrow", pid))
    for sid, s in SHINES.items():
        if s.sparkly:
            lines.append(asp.fact("sparkly", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,R) :- place(P), shine(S), response(R), dark(P), sparkly(S), sense(R, X), sense_min(M), X >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and Python valid_combos().")
        return 1
    print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, shine=None, response=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"FAILED: generate smoke test crashed: {e}")
        rc = 1
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        print("OK: emit() smoke test passed.")
    except Exception as e:
        print(f"FAILED: emit smoke test crashed: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(place="barn", animal1="Milo", animal1_type="kitten", animal2="Pip", animal2_type="puppy",
                helper="Sage", helper_type="rabbit", shine="spangle", response="call", delay=0),
    StoryParams(place="cave", animal1="Nina", animal1_type="foal", animal2="Toby", animal2_type="duckling",
                helper="Kiki", helper_type="goat", shine="disc", response="twig", delay=0),
    StoryParams(place="hedge", animal1="Pip", animal1_type="puppy", animal2="Sage", animal2_type="rabbit",
                helper="Milo", helper_type="kitten", shine="button", response="reach", delay=1),
]


def world_knowledge_tags() -> list[str]:
    return []


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld about curiosity and a spangle.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--shine", choices=SHINES)
    ap.add_argument("--response", choices=RESPONSES)
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
        for combo in combos:
            print("  ", combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
