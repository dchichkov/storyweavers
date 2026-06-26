#!/usr/bin/env python3
"""
Standalone storyworld: a pooch, proximity, repetition, and gentle problem solving.

A small slice-of-life domain in which a child and a beloved pooch keep trying to
stay close, but the world keeps introducing a tiny distance problem: a gate, a
leash loop, a blanket edge, a porch step, or a bench. The story is driven by a
live world model with physical meters and emotional memes.
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
    caretaker: Optional[str] = None
    tethered_to: Optional[str] = None
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
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    features: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    name: str
    tension: str
    repetition_verb: str
    fix_hint: str
    zone: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    for_zones: set[str]
    prep: str
    result: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_near(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    pooch = world.facts.get("pooch")
    if not child or not pooch:
        return out
    if child.meters.get("distance", 0.0) <= 1.0:
        sig = ("near",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["ease"] = child.memes.get("ease", 0.0) + 1
            pooch.memes["ease"] = pooch.memes.get("ease", 0.0) + 1
            out.append("They were near enough to smile at each other.")
    return out


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts.get("child")
    pooch = world.facts.get("pooch")
    if not child or not pooch:
        return out
    if child.memes.get("trying", 0.0) >= 2 and child.memes.get("worry", 0.0) >= 1:
        sig = ("repeat",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["resolve"] = child.memes.get("resolve", 0.0) + 1
            out.append("Trying again helped them notice the small change that worked.")
    return out


CAUSAL_RULES = [_r_near, _r_repeat]


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
            world.say(s)
    return produced


def close_enough(child: Entity, pooch: Entity, limit: float = 1.0) -> bool:
    return child.meters.get("distance", 99.0) <= limit


def can_solve(challenge: Challenge, tool: Tool) -> bool:
    return challenge.id in tool.solves and challenge.zone in tool.for_zones


def choose_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS:
        if can_solve(challenge, tool):
            return tool
    return None


def simulate_try(world: World, child: Entity, challenge: Challenge) -> dict:
    sim = world.copy()
    sim_child = sim.get(child.id)
    sim_child.meters["distance"] = challenge_failure_distance(challenge)
    propagate(sim, narrate=False)
    return {
        "near": close_enough(sim_child, sim.get("Pooch")),
        "repeat": sim_child.memes.get("resolve", 0.0) >= THRESHOLD,
    }


def challenge_failure_distance(challenge: Challenge) -> float:
    return {"gate": 3.0, "leash": 2.0, "blanket": 2.5, "step": 2.0, "bench": 1.5}.get(challenge.id, 2.0)


def intro(world: World, child: Entity, pooch: Entity) -> None:
    world.say(
        f"{child.id} lived a quiet little day with {pooch.label}, "
        f"a pooch who always wanted to stay close."
    )
    world.say(
        f"They liked the same patch of shade, the same squeaky toy, and the same soft spot near the door."
    )


def set_scene(world: World, setting: Setting, challenge: Challenge) -> None:
    world.say(
        f"At {setting.place}, the tiny problem showed up again: {challenge.tension}."
    )
    world.say(
        f"{challenge.name.capitalize()} made the space feel just a little farther apart than they wanted."
    )


def first_try(world: World, child: Entity, pooch: Entity, challenge: Challenge) -> None:
    child.memes["trying"] = child.memes.get("trying", 0.0) + 1
    child.meters["distance"] = challenge_failure_distance(challenge)
    world.say(
        f"{child.id} tried to fix it by {challenge.repetition_verb}, but {pooch.label} still stayed on the other side."
    )
    world.say(
        f"{child.id} frowned, because being that far away from {pooch.label} did not feel right."
    )


def second_try(world: World, child: Entity, pooch: Entity, challenge: Challenge) -> None:
    child.memes["trying"] = child.memes.get("trying", 0.0) + 1
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    world.say(
        f"So {child.id} tried again, slower this time, watching the space between them."
    )
    world.say(
        f"{child.id} noticed that the problem was not big; it was just about proximity."
    )


def offer_tool(world: World, child: Entity, tool: Tool, challenge: Challenge) -> None:
    world.say(
        f"Then {child.id} found {tool.phrase} and used it to solve the little problem."
    )
    world.say(
        f"{tool.prep.capitalize()}, and soon the distance shrank to something comfortable."
    )
    child.meters["distance"] = 0.5
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    child.memes["resolve"] = child.memes.get("resolve", 0.0) + 1
    pooch = world.facts["pooch"]
    pooch.meters["distance"] = 0.5
    propagate(world, narrate=True)


def ending(world: World, child: Entity, pooch: Entity, tool: Tool, challenge: Challenge) -> None:
    world.say(
        f"In the end, {child.id} and {pooch.label} were close enough to share the same happy little moment."
    )
    world.say(
        f"{tool.result.capitalize()}, and the day felt peaceful again."
    )


SETTING_REGISTRY = {
    "front_yard": Setting("the front yard", {"open_space", "shade"}),
    "porch": Setting("the porch", {"step", "shade"}),
    "garden_path": Setting("the garden path", {"gate", "open_space"}),
    "living_room": Setting("the living room", {"blanket", "indoor"}),
    "sidewalk": Setting("the sidewalk", {"bench", "open_space"}),
}

CHALLENGES = {
    "gate": Challenge(
        id="gate",
        name="the gate was half closed",
        tension="the gate left them apart",
        repetition_verb="pushing the gate again and again",
        fix_hint="open the gate all the way",
        zone="gate",
        keyword="gate",
        tags={"proximity", "problem_solving"},
    ),
    "leash": Challenge(
        id="leash",
        name="the leash loop was too short",
        tension="the leash kept them just out of reach",
        repetition_verb="sliding one loop, then another",
        fix_hint="make the leash longer",
        zone="open_space",
        keyword="leash",
        tags={"proximity", "problem_solving"},
    ),
    "blanket": Challenge(
        id="blanket",
        name="the blanket edge kept slipping",
        tension="the blanket made a tiny border between them",
        repetition_verb="tucking the blanket back in",
        fix_hint="smooth the blanket flat",
        zone="blanket",
        keyword="blanket",
        tags={"slice_of_life", "repetition"},
    ),
    "step": Challenge(
        id="step",
        name="the porch step felt too high",
        tension="the step made the porch feel far away",
        repetition_verb="trying the step once more",
        fix_hint="move carefully and climb together",
        zone="step",
        keyword="step",
        tags={"slice_of_life", "problem_solving"},
    ),
    "bench": Challenge(
        id="bench",
        name="the bench was just a little too far",
        tension="the bench made their seats feel separate",
        repetition_verb="shuffling the bench a little closer",
        fix_hint="pull the bench nearer",
        zone="bench",
        keyword="bench",
        tags={"proximity", "slice_of_life"},
    ),
}

TOOLS = [
    Tool(
        id="open_gate",
        label="the latch",
        phrase="the latch by the gate",
        solves={"gate"},
        for_zones={"gate"},
        prep="she opened the gate wide with one careful pull",
        result="the gate stopped keeping them apart",
    ),
    Tool(
        id="long_leash",
        label="a longer leash",
        phrase="a longer leash from the hook",
        solves={"leash"},
        for_zones={"open_space"},
        prep="he swapped in a longer leash and gave it a gentle tug",
        result="the leash had room for closeness now",
    ),
    Tool(
        id="smooth_blanket",
        label="the blanket corners",
        phrase="the neat blanket corners",
        solves={"blanket"},
        for_zones={"blanket"},
        prep="she smoothed the blanket corners flat with both hands",
        result="the blanket became one soft shared place",
    ),
    Tool(
        id="careful_step",
        label="the railing",
        phrase="the railing beside the porch",
        solves={"step"},
        for_zones={"step"},
        prep="they held the railing and climbed slowly together",
        result="the step felt smaller when they did it side by side",
    ),
    Tool(
        id="move_bench",
        label="the bench",
        phrase="the bench legs",
        solves={"bench"},
        for_zones={"bench"},
        prep="they slid the bench a little closer, just enough to matter",
        result="the seat gap turned into a comfortable little gap",
    ),
]

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Nina", "Ella", "Ruby", "Sana"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Finn", "Arlo", "Ben", "Jude"]
PLACES = list(SETTING_REGISTRY.keys())
POOCH_NAMES = ["Pip", "Mochi", "Scout", "Taco", "Biscuit", "Pebble"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    pooch_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about pooch proximity and repetition.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--pooch-name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, ch_id, "pooch") for place in PLACES for ch_id in CHALLENGES]


def explain_rejection(place: str, challenge: Challenge) -> str:
    return f"(No story: {challenge.name} does not fit well at {place}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTING_REGISTRY.items():
        lines.append(asp.fact("place", place))
        for feat in sorted(setting.features):
            lines.append(asp.fact("feature", place, feat))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("zone", cid, ch.zone))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for s in sorted(t.solves):
            lines.append(asp.fact("solves", t.id, s))
        for z in sorted(t.for_zones):
            lines.append(asp.fact("for_zone", t.id, z))
    return "\n".join(lines)


ASP_RULES = r"""
can_use(T,C) :- tool(T), challenge(C), solves(T,C), zone(C,Z), for_zone(T,Z).
valid(Place,C) :- place(Place), challenge(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set((p, c) for (p, c, _) in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.challenge:
        pass
    combos = valid_combos()
    combos = [c for c in combos if args.place is None or c[0] == args.place]
    combos = [c for c in combos if args.challenge is None or c[1] == args.challenge]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, challenge, _ = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    pooch_name = args.pooch_name or rng.choice(POOCH_NAMES)
    return StoryParams(place=place, challenge=challenge, name=name, gender=gender, pooch_name=pooch_name)


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    pooch = world.add(Entity(id="Pooch", kind="character", type="pooch", label=params.pooch_name))
    world.facts["child"] = child
    world.facts["pooch"] = pooch
    challenge = CHALLENGES[params.challenge]
    tool = choose_tool(challenge)

    intro(world, child, pooch)
    world.para()
    set_scene(world, world.setting, challenge)
    first_try(world, child, pooch, challenge)
    propagate(world)
    world.para()
    second_try(world, child, pooch, challenge)
    if tool is None:
        raise StoryError(explain_rejection(params.place, challenge))
    offer_tool(world, child, tool, challenge)
    world.para()
    ending(world, child, pooch, tool, challenge)

    world.facts["challenge"] = challenge
    world.facts["tool"] = tool
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pooch = f["pooch"]
    ch = f["challenge"]
    return [
        f"Write a slice-of-life story about {child.id} and the pooch {pooch.label} when {ch.name}.",
        f"Tell a gentle story in which a child solves a small proximity problem by trying again.",
        f"Write a short story where repetition helps {child.id} and {pooch.label} get close again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    pooch = f["pooch"]
    ch = f["challenge"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What small problem did {child.id} face with {pooch.label}?",
            answer=f"{child.id} faced a proximity problem because {ch.tension}.",
        ),
        QAItem(
            question=f"What did {child.id} do when the first try did not work?",
            answer=f"{child.id} tried again and paid closer attention to the space between them.",
        ),
        QAItem(
            question=f"How did {child.id} solve the problem?",
            answer=f"{child.id} used {tool.phrase} and made the distance comfortable again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does proximity mean?",
            answer="Proximity means how close two things are to each other.",
        ),
        QAItem(
            question="Why can trying again help?",
            answer="Trying again can help because a second look or a slower try can reveal a small fix you missed before.",
        ),
        QAItem(
            question="What is a pooch?",
            answer="A pooch is a friendly word for a dog.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="front_yard", challenge="gate", name="Mia", gender="girl", pooch_name="Pip"),
    StoryParams(place="porch", challenge="step", name="Owen", gender="boy", pooch_name="Scout"),
    StoryParams(place="living_room", challenge="blanket", name="Luna", gender="girl", pooch_name="Mochi"),
    StoryParams(place="sidewalk", challenge="bench", name="Theo", gender="boy", pooch_name="Biscuit"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:\n")
        for p, c in vals:
            print(f"  {p:12} {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name} at {p.place} ({p.challenge})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
