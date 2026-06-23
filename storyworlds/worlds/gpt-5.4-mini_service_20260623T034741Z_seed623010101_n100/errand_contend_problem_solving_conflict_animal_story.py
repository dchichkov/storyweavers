#!/usr/bin/env python3
"""
storyworlds/worlds/errand_contend_problem_solving_conflict_animal_story.py
==========================================================================

A small animal-story world about an errand that turns into a contest over how
to solve a problem. The child-facing tale stays concrete: an animal helper gets
sent on a task, hits a snag, contends with another animal's idea, and ends with
a practical fix that changes the world state.

Seed tale used to shape the model:
---
A little fox was sent on an errand to bring berries home for supper. On the way,
the fox and a crow contended over who should carry the basket across a shaky
log bridge. The basket slipped, berries rolled into the grass, and the fox grew
worried.

Then a calm badger noticed the problem. The badger suggested tying a vine loop
to the basket handle and passing it under the log. Together they pulled the
basket through one careful step at a time. The berries stayed safe, and the fox
went home proud to finish the errand.

World model:
---
- Typed entities with meters and memes.
- A simple forward causal step: slipping can spill berries, which raises worry.
- Social beats: errand begins, contention over the method, helper proposes a
  fix, and the task resolves.
- The final image proves what changed: the basket is secure, the errand is done,
  and the animal team has a better plan.

This file is standalone and uses only the stdlib plus the shared storyworld
results API; ASP support is imported lazily.
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
    role: str = ""
    owner: str = ""
    tags: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "bear", "badger", "rabbit", "cat", "crow"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Errand:
    id: str
    verb: str
    noun: str
    burden: str
    snag: str
    contend_verb: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route_secure: bool = False
        self.spilled: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.route_secure = self.route_secure
        c.spilled = self.spilled
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class StoryParams:
    place: str = ""
    errand: str = ""
    hero: str = ""
    hero_type: str = ""
    rival: str = ""
    rival_type: str = ""
    helper: str = ""
    helper_type: str = ""
    tool: str = ""
    seed: Optional[int] = None


PLACES = {
    "meadow": Place(id="meadow", label="the meadow trail", supports={"berries", "rope"}),
    "orchard": Place(id="orchard", label="the orchard path", supports={"apples", "rope"}),
    "pond": Place(id="pond", label="the pond bank", supports={"fish", "rope"}),
}

ERRANDS = {
    "berries": Errand(
        id="berries",
        verb="bring berries home",
        noun="berries",
        burden="basket",
        snag="the basket slid on the log bridge",
        contend_verb="contend",
        fix_hint="a vine loop under the handle",
        tags={"berries", "basket", "bridge"},
    ),
    "apples": Errand(
        id="apples",
        verb="carry apples to grandma",
        noun="apples",
        burden="crate",
        snag="the crate bumped and tipped on the narrow bridge",
        contend_verb="contend",
        fix_hint="a rope sling under the crate",
        tags={"apples", "crate", "bridge"},
    ),
    "fish": Errand(
        id="fish",
        verb="take fish to the den",
        noun="fish",
        burden="pail",
        snag="the pail wobbled on the wet stones",
        contend_verb="contend",
        fix_hint="a steady stick through the pail handle",
        tags={"fish", "pail", "stones"},
    ),
}

TOOLS = {
    "vine": Tool(id="vine", label="vine loop", phrase="a vine loop", helps={"berries", "basket", "bridge"}, tags={"vine"}),
    "rope": Tool(id="rope", label="rope sling", phrase="a rope sling", helps={"apples", "crate", "bridge"}, tags={"rope"}),
    "stick": Tool(id="stick", label="steady stick", phrase="a steady stick", helps={"fish", "pail", "stones"}, tags={"stick"}),
}

ANIMAL_NAMES = ["Pip", "Milo", "Mina", "Toby", "Luna", "Fern", "Bram", "Coco", "Nell", "Otis"]
ANIMAL_TYPES = ["fox", "rabbit", "crow", "badger", "mouse", "squirrel"]
HELPER_TYPES = ["badger", "otter", "hedgehog", "beaver", "rabbit"]
TRAITS = ["curious", "careful", "brave", "quick", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for err_id, err in ERRANDS.items():
            for tool_id, tool in TOOLS.items():
                if err.id in tool.helps:
                    combos.append((place_id, err_id, tool_id))
    return combos


def errand_at_risk(errand: Errand, tool: Tool) -> bool:
    return errand.id in tool.helps


def choose_tool(errand: Errand, tool: Tool) -> bool:
    return errand_at_risk(errand, tool)


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    basket = world.get("cargo")
    if hero.meters["jostle"] < THRESHOLD:
        return out
    sig = ("spill", basket.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    basket.meters["spilled"] += 1
    hero.memes["worry"] += 1
    world.spilled = True
    out.append("The load slipped and the berries rolled into the grass.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _r_spill(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_spill(world: World) -> bool:
    sim = world.copy()
    sim.get("hero").meters["jostle"] += 1
    propagate(sim, narrate=False)
    return sim.get("cargo").meters["spilled"] >= THRESHOLD


def tell(place: Place, errand: Errand, hero_name: str, hero_type: str,
         rival_name: str, rival_type: str, helper_name: str, helper_type: str,
         tool: Tool, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    rival = world.add(Entity(id="rival", kind="character", type=rival_type, label=rival_name, role="rival"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    cargo = world.add(Entity(id="cargo", kind="thing", type=errand.burden, label=errand.burden, phrase=errand.noun, owner="hero"))
    tool_ent = world.add(Entity(id="tool", kind="thing", type=tool.id, label=tool.label, phrase=tool.phrase))
    route = world.add(Entity(id="route", kind="thing", type="route", label=place.label))

    hero.memes["duty"] += 1
    rival.memes["pride"] += 1
    helper.memes["calm"] += 1
    world.facts["errand"] = errand
    world.facts["tool"] = tool
    world.facts["trait"] = trait
    world.facts["place"] = place
    world.facts["hero_name"] = hero_name
    world.facts["rival_name"] = rival_name
    world.facts["helper_name"] = helper_name
    world.facts["route"] = route
    world.facts["cargo"] = cargo

    world.say(f"{hero_name} the {hero_type} had an errand to {errand.verb}.")
    world.say(f"{hero_name} carried a {errand.burden} full of {errand.noun} along {place.label}.")
    world.para()
    world.say(f"At the bridge, {rival_name} the {rival_type} tried to {errand.contend_verb} with {hero_name} about the best way across.")
    world.say(f"{rival_name} wanted to rush, but {hero_name} knew the load could slip.")

    if predict_spill(world):
        world.say(f"{hero_name} noticed the danger and asked for help instead of arguing louder.")
        world.para()
        world.say(f"{helper_name} the {helper_type} listened and offered {tool.phrase} as a fix.")
        world.say(f"They used {tool.phrase} to steady the {errand.burden} and cross one careful step at a time.")
        hero.memes["relief"] += 1
        helper.memes["pride"] += 1
        world.route_secure = True
    else:
        world.say(f"They crossed easily, and the errand stayed simple.")
        world.route_secure = True

    cargo.meters["safe"] += 1
    if world.route_secure:
        world.say(f"In the end, the {errand.burden} stayed full, {hero_name} finished the errand, and everyone walked home proud.")

    world.facts.update(hero=hero, rival=rival, helper=helper, cargo=cargo, tool_ent=tool_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    err: Errand = f["errand"]
    tool: Tool = f["tool"]
    return [
        f'Write a short animal story for a young child that includes the words "errand" and "contend".',
        f"Tell a gentle animal story where a little helper must finish an errand, contends with another animal over the plan, and solves the problem with {tool.phrase}.",
        f"Write a problem-solving animal story about {err.verb} where the animals contend a little, then choose a careful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    err: Errand = f["errand"]
    tool: Tool = f["tool"]
    hero = f["hero"]
    rival = f["rival"]
    helper = f["helper"]
    cargo = f["cargo"]
    qa = [
        QAItem(
            question=f"What errand did {hero.label} have to do?",
            answer=f"{hero.label} had an errand to {err.verb}. It was a small job, but it mattered because the {err.burden} needed to get home safely.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {rival.label} contend at the bridge?",
            answer=f"They contended because they each wanted a different way across. The load was wobbly, so their disagreement made the problem harder until they slowed down and looked for a safer idea.",
        ),
        QAItem(
            question=f"How did {helper.label} solve the problem?",
            answer=f"{helper.label} suggested {tool.phrase} and the animals used it to steady the load. That made the crossing careful instead of rushed, so the errand could be finished.",
        ),
    ]
    if world.spilled:
        qa.append(QAItem(
            question=f"What happened when the load slipped?",
            answer=f"The berries rolled into the grass, so {hero.label} had to worry for a moment. After that, the animals stopped contending and fixed the problem together.",
        ))
    else:
        qa.append(QAItem(
            question=f"Did the load stay safe on the way home?",
            answer=f"Yes. The {err.burden} stayed safe, and the errand ended with everyone walking home proud.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    err: Errand = f["errand"]
    tool: Tool = f["tool"]
    place: Place = f["place"]
    items = {
        "errand": [
            ("What is an errand?", "An errand is a small job or task someone goes out to do."),
        ],
        "bridge": [
            ("What is a bridge for?", "A bridge helps people or animals cross over water, mud, or a gap."),
        ],
        "problem-solving": [
            ("What does it mean to solve a problem?", "It means finding a way to make a hard thing easier or safer."),
        ],
        "rope": [
            ("What can rope do?", "Rope can tie, hold, or steady things so they do not slip."),
        ],
        "vine": [
            ("What is a vine?", "A vine is a long plant that can grow like a rope and twist around things."),
        ],
    }
    tags = set(err.tags) | set(tool.tags) | {place.id}
    out: list[QAItem] = []
    for key in ["errand", "bridge", "problem-solving", "rope", "vine"]:
        if key in items and (key in tags or key in {"errand", "problem-solving", "bridge"}):
            out.extend(QAItem(q, a) for q, a in items[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", errand="berries", hero="Pip", hero_type="fox", rival="Crow", rival_type="crow", helper="Bram", helper_type="badger", tool="vine"),
    StoryParams(place="orchard", errand="apples", hero="Mina", hero_type="rabbit", rival="Moth", rival_type="mouse", helper="Nell", helper_type="beaver", tool="rope"),
    StoryParams(place="pond", errand="fish", hero="Toby", hero_type="otter", rival="Jay", rival_type="crow", helper="Fern", helper_type="hedgehog", tool="stick"),
]


def valid_world_params(params: StoryParams) -> bool:
    return params.place in PLACES and params.errand in ERRANDS and params.tool in TOOLS and choose_tool(ERRANDS[params.errand], TOOLS[params.tool])


def explain_rejection(errand: Errand, tool: Tool) -> str:
    return f"(No story: {tool.phrase} does not help with {errand.noun} in this little animal world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: an errand, a contest, and a problem-solving fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (args.errand is None or c[1] == args.errand)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, errand, tool = rng.choice(list(combos))
    hero = rng.choice(ANIMAL_NAMES)
    rival = rng.choice([n for n in ANIMAL_NAMES if n != hero])
    helper = rng.choice([n for n in ANIMAL_NAMES if n not in {hero, rival}])
    return StoryParams(place=place, errand=errand, hero=hero, hero_type=rng.choice(ANIMAL_TYPES), rival=rival, rival_type=rng.choice(ANIMAL_TYPES), helper=helper, helper_type=rng.choice(HELPER_TYPES), tool=tool, seed=None)


def generate(params: StoryParams) -> StorySample:
    if not valid_world_params(params):
        raise StoryError(explain_rejection(ERRANDS[params.errand], TOOLS[params.tool]))
    world = tell(PLACES[params.place], ERRANDS[params.errand], params.hero, params.hero_type, params.rival, params.rival_type, params.helper, params.helper_type, TOOLS[params.tool], "careful")
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P,E,T) :- place(P), errand(E), tool(T), helps(T,E).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for errand_id, errand in ERRANDS.items():
        lines.append(asp.fact("errand", errand_id))
        for tag in sorted(errand.tags):
            lines.append(asp.fact("err_tag", errand_id, tag))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for help_tag in sorted(tool.helps):
            lines.append(asp.fact("helps", tool_id, help_tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py_set = set(valid_combos())
    try:
        asp_set = set(asp_valid_combos())
    except Exception as exc:
        print(f"ERROR: {exc}")
        return 1
    if py_set != asp_set:
        print("MISMATCH between ASP and Python combos")
        print("only in python:", sorted(py_set - asp_set))
        print("only in asp:", sorted(asp_set - py_set))
        return 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("ERROR: smoke test failed")
        return 1
    print(f"OK: ASP matches Python for {len(py_set)} combos and story generation works.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in valid_combos():
            print(row)
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
