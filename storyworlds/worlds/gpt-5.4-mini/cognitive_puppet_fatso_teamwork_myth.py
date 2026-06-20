#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py
======================================================================

A standalone story world for a tiny mythic tale about a clever child,
a puppet, and a surprisingly heavy "fatso" idol that only teamwork can move.

Premise
-------
Two villagers enter an old temple to retrieve a puppet oracle and a round
stone idol nicknamed "fatso". The idol blocks a door to a safe path home.
One helper uses a cognitive trick to notice the right lever and the other
uses teamwork to pull the puppet back to life, so they can move the idol
together and bring the village a useful lantern.

Style
-----
Mythic, but child-facing: simple, concrete, and state-driven. The story turns
on physical meters (weight, strain, light, dust) and emotional memes (hope,
fear, trust, pride). The ending proves what changed: the idol is moved, the
puppet is restored, and the village gets light.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py --all
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py --trace
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py --json
    python storyworlds/worlds/gpt-5.4-mini/cognitive_puppet_fatso_teamwork_myth.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    heavy: bool = False
    puppet: bool = False
    glowing: bool = False

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    name: str
    myth: str
    has_door: bool = True
    has_path: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    effect: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_weight(world: World) -> list[str]:
    out: list[str] = []
    idol = world.entities.get("fatso")
    if idol and idol.meters["stuck"] >= THRESHOLD and "path" in world.entities:
        sig = ("weight", idol.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("path").meters["blocked"] += 1
            out.append("__blocked__")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    if world.get("puppet").meters["restored"] >= THRESHOLD:
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("weight", "physical", _r_weight), Rule("trust", "social", _r_trust)]


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


def best_tool() -> Tool:
    return max(TOOLS.values(), key=lambda t: t.sense)


def sensible_tools() -> list[Tool]:
    return [t for t in TOOLS.values() if t.sense >= SENSE_MIN]


def valid_combo(tool: Tool, place: Place, idol: Entity) -> bool:
    return tool.sense >= SENSE_MIN and idol.heavy and place.has_door


def _do_lift(world: World, helper: Entity, tool: Tool, idol: Entity) -> None:
    helper.meters["strain"] += 1
    idol.meters["stuck"] += 1
    world.get("path").meters["blocked"] += 1
    propagate(world, narrate=False)


def predict(world: World, tool: Tool) -> dict:
    sim = world.copy()
    _do_lift(sim, sim.get("helper"), tool, sim.get("fatso"))
    return {
        "blocked": sim.get("path").meters["blocked"] >= THRESHOLD,
        "hope": sim.get("helper").memes["hope"],
    }


def opening(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["duty"] += 1
    world.say(
        f"Long ago, in {place.name}, {hero.id} and {helper.id} walked under a sky of bronze. "
        f"{place.myth}"
    )


def discover(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"They found a small puppet lying silent beside a stone idol nicknamed fatso. "
        f"The puppet's strings hung loose, and the idol blocked the door to the home path."
    )
    hero.memes["fear"] += 1
    helper.memes["fear"] += 1


def puzzle(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["cognitive"] += 1
    pred = predict(world, tool)
    world.facts["predicted_blocked"] = pred["blocked"]
    world.say(
        f"{hero.id} looked carefully at the floor and the wall, then whispered a cognitive thought. "
        f'"If we pull the rope above the idol and not the puppet itself, the door might open."'
    )
    world.say(
        f'{helper.id} nodded. "Then let us work as one."'
    )


def teamwork(world: World, hero: Entity, helper: Entity, tool: Tool) -> None:
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"They looped the rope, braced their feet, and counted together. "
        f'One, two, three.'
    )


def move_idol(world: World, hero: Entity, helper: Entity, idol: Entity, tool: Tool) -> None:
    idol.meters["stuck"] += 1
    hero.meters["strain"] += 1
    helper.meters["strain"] += 1
    world.say(
        f"The rope bit into the stone, and the heavy fatso shifted at last. Dust rolled like smoke, "
        f"and the door groaned open to the path beyond."
    )


def restore_puppet(world: World, puppet: Entity, hero: Entity, helper: Entity) -> None:
    puppet.meters["restored"] += 1
    puppet.glowing = True
    puppet.memes["joy"] += 1
    world.say(
        f"The puppet's eyes caught the lantern light, and its little painted smile looked awake again. "
        f"{hero.id} lifted it gently, and {helper.id} tied the strings with careful hands."
    )


def gift_light(world: World, hero: Entity, helper: Entity, puppet: Entity) -> None:
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"By dawn, they carried the puppet home. It glowed softly in the lantern glow, and the village "
        f"cheered because two helpers had moved a fat idol together and saved the wise little puppet."
    )


def tell(place: Place, tool: Tool, hero_name: str, helper_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper"))
    puppet = world.add(Entity(id="puppet", type="toy", label="puppet", puppet=True, movable=False))
    idol = world.add(Entity(id="fatso", type="idol", label="fatso", heavy=True, movable=False))
    path = world.add(Entity(id="path", type="path", label="the home path"))
    lamp = world.add(Entity(id="lantern", type="thing", label="lantern", glowing=True))

    opening(world, hero, helper, place)
    world.para()
    discover(world, hero, helper)
    puzzle(world, hero, helper, tool)
    teamwork(world, hero, helper, tool)
    move_idol(world, hero, helper, idol, tool)
    world.para()
    restore_puppet(world, puppet, hero, helper)
    gift_light(world, hero, helper, puppet)

    world.facts.update(
        hero=hero, helper=helper, puppet=puppet, idol=idol, path=path, lamp=lamp,
        tool=tool, place=place, outcome="moved", restored=True
    )
    return world


PLACES = {
    "temple": Place(
        "temple",
        "the old temple",
        "A wind sang through the pillars, and the shadows waited like sleeping kings.",
    ),
    "cave": Place(
        "cave",
        "the moon cave",
        "Water dripped from the stone, and the dark floor shone like a mirror.",
    ),
    "ruins": Place(
        "ruins",
        "the sunken ruins",
        "Broken arches leaned together as if they were listening to an old song.",
    ),
}

TOOLS = {
    "rope": Tool("rope", "rope", "a long rope", "pull", 3, 3, {"pull"}),
    "lever": Tool("lever", "lever", "a wooden lever", "pry", 3, 4, {"pry"}),
    "teamwork": Tool("teamwork", "teamwork", "their teamwork", "move", 4, 5, {"team"}),
}

GIRL_NAMES = ["Mira", "Lina", "Zoe", "Nia", "Ada"]
BOY_NAMES = ["Arin", "Theo", "Milo", "Jude", "Oren"]


@dataclass
class StoryParams:
    place: str
    tool: str
    hero: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("temple", "rope", "Arin", "Mira"),
    ("cave", "lever", "Theo", "Nia"),
    ("ruins", "teamwork", "Milo", "Ada"),
]



def valid_combos() -> list[tuple[str, str]]:
    return [(p, t) for p in PLACES for t in TOOLS if valid_combo(TOOLS[t], PLACES[p], Entity(id="fatso", heavy=True))]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic teamwork story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
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
    combos = [(p, t) for p in PLACES for t in TOOLS if valid_combo(TOOLS[t], PLACES[p], Entity(id="fatso", heavy=True))]
    if args.place and args.tool and not valid_combo(TOOLS[args.tool], PLACES[args.place], Entity(id="fatso", heavy=True)):
        raise StoryError("That tool cannot reasonably move the heavy idol in that place.")
    if not combos:
        raise StoryError("No reasonable story can be made.")
    place, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(BOY_NAMES)
    helper = args.helper or rng.choice(GIRL_NAMES)
    if helper == hero:
        helper = rng.choice([n for n in GIRL_NAMES if n != hero])
    return StoryParams(args.place or place, args.tool or tool, hero, helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic teamwork story for a young child that includes the words "cognitive", "puppet", and "fatso".',
        f"Tell a gentle myth where {f['hero'].id} and {f['helper'].id} use cognitive thinking and teamwork to move fatso and save the puppet.",
        f"Write a child-facing legend about a puppet, a heavy stone called fatso, and a clever plan that only works when two helpers act together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper = f["hero"], f["helper"]
    return [
        QAItem(
            question="Who worked together in the story?",
            answer=f"{hero.id} and {helper.id} worked together. They used teamwork to move the heavy stone and help the puppet.",
        ),
        QAItem(
            question="Why did the heavy stone matter?",
            answer="The stone nicknamed fatso blocked the door. Because it was heavy, one child could not move it alone, so teamwork was needed.",
        ),
        QAItem(
            question="What did the cognitive idea do?",
            answer="The cognitive idea helped them choose the right rope and the right place to pull. That smart choice kept them from tugging the puppet and let them open the path instead.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work as one. It makes hard jobs easier to finish.",
        ),
        QAItem(
            question="What does cognitive mean?",
            answer="Cognitive means thinking with care and using your mind to solve a problem. It is a smart way to choose what to do.",
        ),
        QAItem(
            question="What is a puppet?",
            answer="A puppet is a little figure that can be moved or made to act like it is alive. People often use strings or hands to move it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.heavy:
            bits.append("heavy")
        if e.puppet:
            bits.append("puppet")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
sensible(T) :- tool(T), sense(T,S), sense_min(M), S >= M.
valid(P, T) :- place(P), tool(T), heavy(idol), sensible(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TOOLS.values():
        lines.append(asp.fact("tool", t.id))
        lines.append(asp.fact("sense", t.id, t.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("heavy", "idol"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP valid combos differ from Python.")
        rc = 1
    if set(asp_sensible()) != {t.id for t in sensible_tools()}:
        print("MISMATCH: ASP sensible tools differ from Python.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def explain_rejection(tool: Tool) -> str:
    return f"(No story: {tool.label} is too weak for this mythic task; choose a sturdier tool.)"


def explore(world: World, params: StoryParams) -> None:
    pass


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    tool = TOOLS[params.tool]
    world = tell(place, tool, params.hero, params.helper)
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
        print(asp_program(show="#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(f"{p}/{t}" for p, t in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(p, t, h, l)) for p, t, h, l in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
