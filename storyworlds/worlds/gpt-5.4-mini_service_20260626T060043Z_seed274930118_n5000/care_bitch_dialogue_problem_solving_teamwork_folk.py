#!/usr/bin/env python3
"""
storyworlds/worlds/care_bitch_dialogue_problem_solving_teamwork_folk.py
========================================================================

A small folk-tale storyworld about caring for a bitch-dog, talking through a
problem, and solving it together with teamwork.

The seed premise:
---
In a little village, an old woman cared for a kind bitch named Brindle. One cold
evening, Brindle chased a fox into the thorny woods and came back with a paw full
of splinters. The old woman could not reach the splinters alone, and Brindle did
not want to stand still. So the woman called the shepherd, the miller, and the
girl with the lantern. They spoke gently, held the lamp, fetched clean water,
and worked together until Brindle could walk home again.

World model:
---
- Care can raise trust and calm.
- A paw injury can cause pain and fussing.
- Dialogue can lower fear if the helpers speak kindly.
- Problem solving succeeds only if the right tools are gathered.
- Teamwork shares the burden and restores the dog's comfort.

This file is self-contained except for the shared result containers and the
optional ASP helper used in verification modes.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wounded: bool = False
    carries_light: bool = False
    carries_water: bool = False
    carries_tools: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "shepherd", "miller"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    light_needed: bool = False
    water_needed: bool = False
    tools_needed: bool = False


@dataclass
class Problem:
    id: str
    wound: str
    pain: str
    place: str
    tools: set[str] = field(default_factory=set)
    helpers: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    type: str
    label: str
    role: str
    carries: set[str] = field(default_factory=set)
    words: tuple[str, ...] = ()


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    dog: str
    caretaker: str
    helper1: str
    helper2: str
    helper3: str
    seed: Optional[int] = None


PLACES = {
    "village_green": Place(name="the village green", kind="outdoor"),
    "forest_edge": Place(name="the edge of the forest", kind="outdoor", light_needed=True),
    "cottage_yard": Place(name="the cottage yard", kind="outdoor", water_needed=True),
}

DOGS = {
    "brindle": {
        "name": "Brindle",
        "type": "bitch",
        "label": "kind bitch",
        "phrase": "a kind bitch with a black nose and a brave tail",
    },
    "maple": {
        "name": "Maple",
        "type": "bitch",
        "label": "gentle bitch",
        "phrase": "a gentle bitch with soft ears",
    },
}

CARETAKERS = {
    "old_woman": {"name": "Nana", "type": "woman", "label": "old woman"},
    "herder": {"name": "Tobin", "type": "man", "label": "shepherd"},
}

HELPERS = {
    "lantern_girl": Helper(id="lantern_girl", type="girl", label="girl with the lantern", role="light", carries={"light"}),
    "miller": Helper(id="miller", type="man", label="miller", role="water", carries={"water"}),
    "village_boy": Helper(id="village_boy", type="boy", label="boy with the twig splint", role="tools", carries={"tools"}),
}

TRAITS = ["gentle", "steady", "patient", "brave", "kind"]


def validity_checks(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.dog not in DOGS:
        raise StoryError("Unknown dog.")
    if params.caretaker not in CARETAKERS:
        raise StoryError("Unknown caretaker.")
    for h in [params.helper1, params.helper2, params.helper3]:
        if h not in HELPERS:
            raise StoryError("Unknown helper.")


def select_helpers(problem: Problem) -> list[Helper]:
    chosen = []
    for helper in HELPERS.values():
        if problem.tools & helper.carries:
            chosen.append(helper)
    return chosen


def can_solve(place: Place, problem: Problem, helpers: list[Helper]) -> bool:
    have = set()
    for h in helpers:
        have |= h.carries
    if not problem.tools.issubset(have):
        return False
    if place.light_needed and "light" not in have:
        return False
    if place.water_needed and "water" not in have:
        return False
    if place.tools_needed and "tools" not in have:
        return False
    return True


def tell_story(place: Place, dog_cfg: dict, caretaker_cfg: dict, helper_ids: list[str]) -> World:
    world = World(place)
    dog = world.add(Entity(
        id=dog_cfg["name"],
        kind="character",
        type=dog_cfg["type"],
        label=dog_cfg["label"],
        phrase=dog_cfg["phrase"],
        owner=caretaker_cfg["name"],
        caretaker=caretaker_cfg["name"],
        meters={"pain": 2.0, "fuss": 1.0},
        memes={"trust": 1.0, "fear": 1.0},
        wounded=True,
    ))
    caretaker = world.add(Entity(
        id=caretaker_cfg["name"],
        kind="character",
        type=caretaker_cfg["type"],
        label=caretaker_cfg["label"],
        meters={"care": 2.0, "worry": 1.0},
        memes={"love": 2.0, "worry": 1.0},
    ))
    helpers = []
    for hid in helper_ids:
        hcfg = HELPERS[hid]
        helpers.append(world.add(Entity(
            id=hcfg.id,
            kind="character",
            type=hcfg.type,
            label=hcfg.label,
            meters={"help": 1.0},
            memes={"will": 1.0},
            carries_light="light" in hcfg.carries,
            carries_water="water" in hcfg.carries,
            carries_tools="tools" in hcfg.carries,
        )))

    problem = Problem(
        id="thorn_splinters",
        wound="splinters",
        pain="painful paw",
        place=place.name,
        tools={"light", "water", "tools"},
        helpers={h.id for h in helpers},
    )

    world.say(f"Long ago, in {place.name}, there lived {dog_cfg['phrase']}.")
    world.say(f"{caretaker_cfg['name']} cared for {dog.id} every day, and {dog.id} trusted {caretaker.pronoun('object')} well.")
    world.para()
    world.say(f"One dusk, {dog.id} came home limping from the thorny wood, with {problem.pain} and little splinters in a paw.")
    world.say(f"{caretaker_cfg['name']} frowned with worry, for {dog.id} could not be made well by one pair of hands alone.")
    world.para()
    world.say(f"So {caretaker_cfg['name']} called for help, and the helpers came speaking softly.")
    for h in helpers:
        if h.carries_light:
            world.say(f"The {h.label} lifted a lantern so everyone could see.")
        elif h.carries_water:
            world.say(f"The {h.label} fetched clean water in a wooden bowl.")
        elif h.carries_tools:
            world.say(f"The {h.label} brought a tiny twig splint and a clean cloth.")
    if not can_solve(place, problem, helpers):
        raise StoryError("The chosen helpers cannot solve the problem.")
    dog.meters["pain"] = 0.0
    dog.meters["rest"] = 1.0
    dog.memes["trust"] = 3.0
    caretaker.memes["worry"] = 0.0
    caretaker.meters["care"] = 3.0
    for h in helpers:
        h.memes["pride"] = 1.0
    world.say(f"They spoke in turns, washed the paw, eased out the splinters, and bound the paw with the cloth and splint.")
    world.say(f"{dog.id} stopped shaking, licked {caretaker.pronoun('object')}, and stood at last without a whine.")
    world.say(f"Then the little company walked home together beneath the evening star, with {dog.id} trotting proudly beside them.")
    world.facts.update(
        dog=dog,
        caretaker=caretaker,
        helpers=helpers,
        problem=problem,
        place=place,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    dog = f["dog"]
    caretaker = f["caretaker"]
    return [
        "Write a folk-tale style story about care, dialogue, and teamwork.",
        f"Tell a gentle village story where {caretaker.id} cares for {dog.id} and the neighbors help solve a paw problem.",
        f"Write a short story for children where a {dog.type} gets hurt, friends talk kindly, and everyone works together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dog = f["dog"]
    caretaker = f["caretaker"]
    helpers = f["helpers"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who was being cared for in the story?",
            answer=f"{dog.id} was being cared for. {caretaker.id} looked after {dog.id} with love and worry.",
        ),
        QAItem(
            question=f"What problem did {dog.id} have when coming home from the woods?",
            answer=f"{dog.id} came home limping with splinters in a paw, and that made walking painful.",
        ),
        QAItem(
            question=f"How did the village solve the problem together?",
            answer=f"They worked as a team: one held a lantern, one brought clean water, and one brought a cloth and splint. Together they washed the paw and pulled out the splinters.",
        ),
        QAItem(
            question=f"Why did {caretaker.id} call the neighbors?",
            answer=f"{caretaker.id} could not fix the painful paw alone, so calling neighbors gave {dog.id} the care and tools needed.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {dog.id} was no longer in pain and could walk home proudly beside the helpers.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people share the work and help one another reach the same goal.",
        ),
        QAItem(
            question="Why do people talk kindly when someone is hurt?",
            answer="Kind words can calm fear, help everyone think clearly, and make it easier to solve the problem together.",
        ),
        QAItem(
            question="What does care mean?",
            answer="Care means looking after someone or something gently and making sure it stays safe and healthy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.wounded:
            bits.append("wounded=True")
        out.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
% Facts:
% place(P). dog(D). caretaker(C). helper(H). carries(H, tool).
% problem_requires(T).

solves(P) :- place(P), required(T), have(T).
have(T) :- carries(H, T), helper(H).

teamwork_ok :- required(light), have(light), required(water), have(water), required(tools), have(tools).

resolved :- teamwork_ok.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did in DOGS:
        lines.append(asp.fact("dog", did))
    for cid in CARETAKERS:
        lines.append(asp.fact("caretaker", cid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for c in sorted(helper.carries):
            lines.append(asp.fact("carries", hid, c))
    for t in ["light", "water", "tools"]:
        lines.append(asp.fact("required", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show resolved/0."))
    resolved = any(sym.name == "resolved" for sym in model)
    python_ok = True
    for place in PLACES.values():
        p = Problem("p", "splinters", "painful paw", place.name, {"light", "water", "tools"}, set())
        if not can_solve(place, p, list(HELPERS.values())):
            python_ok = False
    if resolved == python_ok:
        print("OK: ASP and Python gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates differ.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale care storyworld about a wounded bitch and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--dog", choices=DOGS)
    ap.add_argument("--caretaker", choices=CARETAKERS)
    ap.add_argument("--helper1", choices=HELPERS)
    ap.add_argument("--helper2", choices=HELPERS)
    ap.add_argument("--helper3", choices=HELPERS)
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
    place = args.place or rng.choice(list(PLACES))
    dog = args.dog or rng.choice(list(DOGS))
    caretaker = args.caretaker or rng.choice(list(CARETAKERS))
    helper_ids = [args.helper1, args.helper2, args.helper3]
    if any(x is None for x in helper_ids):
        helper_ids = rng.sample(list(HELPERS), 3)
    return StoryParams(place=place, dog=dog, caretaker=caretaker, helper1=helper_ids[0], helper2=helper_ids[1], helper3=helper_ids[2])


def generate(params: StoryParams) -> StorySample:
    validity_checks(params)
    place = PLACES[params.place]
    dog = DOGS[params.dog]
    caretaker = CARETAKERS[params.caretaker]
    helper_ids = [params.helper1, params.helper2, params.helper3]
    world = tell_story(place, dog, caretaker, helper_ids)
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
    StoryParams("forest_edge", "brindle", "old_woman", "lantern_girl", "miller", "village_boy"),
    StoryParams("cottage_yard", "maple", "herder", "lantern_girl", "miller", "village_boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show resolved/0."))
        print("resolved:", any(sym.name == "resolved" for sym in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
