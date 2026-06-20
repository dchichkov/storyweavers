#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rectangular_suspense_lesson_learned_transformation_fable.py
==========================================================================================

A tiny fable-like storyworld about a child-sized woodland domain: a fox,
a crow, a rectangular seed bed, a locked garden gate, and a slow transformation
that teaches a lesson.  The tale begins with a suspenseful need, turns through a
careful choice, and ends with a visible transformation in the world.

The story premise is intentionally small and classical:
- a rectangular bed of soil holds a special seed,
- something threatens the seed during a tense moment,
- a helper character solves the problem with a sensible act,
- the ending proves a transformation happened.

This world is built to satisfy the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- StoryParams/build_parser/resolve_params/generate/emit/main
- QA generated from simulated world state
- inline ASP rules with a Python reasonableness gate
- --verify checks ASP/Python parity and runs smoke generation
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
LESSON_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "growth": 0.0, "wet": 0.0, "joy": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "hope": 0.0, "lesson": 0.0, "calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "fox", "crow", "owl"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    weather: str
    scent: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Creature:
    id: str
    type: str
    label: str
    role: str
    voice: str
    plan: str
    cautious: bool = False
    traits: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Thing:
    id: str
    label: str
    phrase: str
    rectangular: bool = False
    fragile: bool = False
    living: bool = False
    transforms_to: str = ""
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Action:
    id: str
    urge: str
    effect: str
    suspense: str
    remedy: str
    power: int
    sense: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    if seed.meters["wet"] < THRESHOLD:
        sig = ("risk", "seed")
        if sig not in world.fired:
            world.fired.add(sig)
            seed.memes["worry"] += 1
            out.append("The little seed felt the dark coming closer.")
    return out


def _r_growth(world: World) -> list[str]:
    out: list[str] = []
    seed = world.get("seed")
    if seed.meters["growth"] >= THRESHOLD and "seed" not in world.fired:
        world.fired.add(("growth", "seed"))
        seed.label = "sprouted seed"
        out.append("By morning, the seed had become a green sprout.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    sprout = world.get("seed")
    if sprout.meters["growth"] >= 2.0 and ("transform", "seed") not in world.fired:
        world.fired.add(("transform", "seed"))
        sprout.label = "young plant"
        sprout.type = "plant"
        sprout.memes["hope"] += 1
        out.append("The sprout stretched into a young plant.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("crow")
    seed = world.get("seed")
    if helper.memes["calm"] >= THRESHOLD and seed.meters["wet"] >= THRESHOLD:
        sig = ("calm", "crow")
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["lesson"] += 1
            out.append("The crow remembered the careful way and stayed patient.")
    return out


CAUSAL_RULES = [
    Rule("risk", _r_risk),
    Rule("calm", _r_calm),
    Rule("growth", _r_growth),
    Rule("transformation", _r_transformation),
]


def reasonableness_gate(setting: Setting, bed: Thing, action: Action) -> bool:
    return bed.rectangular and action.power >= 1 and action.sense >= 2 and "seed" in action.tags and setting.place


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for aid, action in ACTIONS.items():
            for tid, thing in THINGS.items():
                if reasonableness_gate(setting, thing, action):
                    combos.append((sid, aid, tid))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.action == "storm":
        return "suspense"
    if params.action == "water":
        return "contained"
    return "transformed"


def _do_action(world: World, action: Action) -> None:
    seed = world.get("seed")
    helper = world.get("crow")
    if action.id == "water":
        seed.meters["wet"] += 1
        helper.memes["calm"] += 1
        seed.meters["growth"] += 1
    elif action.id == "shade":
        helper.memes["calm"] += 1
        seed.meters["growth"] += 2
    elif action.id == "storm":
        seed.meters["wet"] += 2
        seed.memes["worry"] += 1
        helper.memes["worry"] += 1
    propagate(world, narrate=False)


def tell(setting: Setting, creature: Creature, seed_thing: Thing, action: Action) -> World:
    world = World()
    fox = world.add(Entity(id="fox", kind="character", type="fox", label=creature.label, role="seeker", traits=["quick", "curious"]))
    crow = world.add(Entity(id="crow", kind="character", type="crow", label="the crow", role="helper", traits=["watchful", "patient"]))
    bed = world.add(Entity(id="bed", kind="thing", type="thing", label="the rectangular bed", attrs={"shape": "rectangular"}))
    seed = world.add(Entity(id="seed", kind="thing", type="thing", label=seed_thing.label, attrs={"shape": "rectangular", "living": True}))
    world.facts["setting"] = setting
    world.facts["creature"] = creature
    world.facts["action"] = action
    world.facts["seed_thing"] = seed_thing

    world.say(f"At {setting.place}, under a sky that smelled of {setting.scent}, a fox named {fox.label} watched a {bed.label} of soil.")
    world.say(f"In that bed lay {seed_thing.phrase}, small enough to fit inside one careful breath.")
    world.say(f"The crow hopped near and warned, \"Tonight may turn strange; {action.suspense}\"")
    world.para()
    world.say(f"{fox.label.capitalize()} wanted to {action.urge}, because the whole little garden felt full of waiting.")
    if action.id == "storm":
        fox.memes["worry"] += 1
        crow.memes["worry"] += 1
        world.say("Clouds stacked up like dark stones, and the wind tapped the gate.")
    elif action.id == "water":
        world.say("So the fox brought a small cup of water and gave the bed a gentle drink.")
    else:
        world.say("So the fox pulled a leaf-cloth over the bed and kept watch with the crow.")
    _do_action(world, action)

    world.para()
    if seed.meters["wet"] >= THRESHOLD and action.id != "storm":
        world.say("Nothing rushed. The bed stayed safe, and the fox learned that patience can be brave.")
    if seed.meters["growth"] >= 1.0:
        world.say("Soon a green point pushed up through the soil, and the old worry began to change.")
    if seed.meters["growth"] >= 2.0:
        world.say("By the end, the seed had changed into a young plant, and the rectangular bed held a new little life.")

    world.facts.update(
        fox=fox,
        crow=crow,
        bed=bed,
        seed=seed,
        outcome=outcome_of(StoryParams(setting.id, action.id, seed_thing.id)),
        transformed=seed.meters["growth"] >= 2.0,
        lesson=crow.memes["lesson"] >= LESSON_MIN,
    )
    return world


SETTINGS = {
    "garden": Setting("garden", "the garden", "damp rain", "wet earth"),
    "orchard": Setting("orchard", "the orchard", "cool drizzle", "apple blossoms"),
    "field": Setting("field", "the field", "heavy clouds", "fresh grass"),
}

CREATURES = {
    "fox": Creature("fox", "fox", "a clever fox", "seeker", "quick voice", "find the safe way", cautious=False),
    "hare": Creature("hare", "hare", "a small hare", "seeker", "bright voice", "find the safe way", cautious=True),
}

THINGS = {
    "seed": Thing("seed", "seed", "a tiny seed", rectangular=True, fragile=True, living=True, transforms_to="sprout", tags={"seed", "rectangular"}),
    "egg": Thing("egg", "egg", "a bright egg", rectangular=False, fragile=True, living=True, transforms_to="hatchling", tags={"egg"}),
    "stone": Thing("stone", "stone", "a smooth stone", rectangular=False, fragile=False, living=False, tags={"stone"}),
}

ACTIONS = {
    "water": Action("water", "water the bed until it could wake", "the seed woke", "the night might still go wrong", "gentle water", 1, 3, tags={"seed", "water"}),
    "shade": Action("shade", "cover the bed and wait", "the seed gathered itself", "the wind kept teasing the gate", "patient shade", 2, 3, tags={"seed", "shade"}),
    "storm": Action("storm", "rush to the gate during the storm", "the seed shivered", "the thunder got nearer", "no remedy", 2, 2, tags={"seed", "storm"}),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    creature: str
    seed_thing: str
    action: str
    name: str = "Fox"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


KNOWLEDGE = {
    "rectangular": [("What is a rectangular shape?", "A rectangular shape has four sides and four corners, with opposite sides the same length.")],
    "seed": [("What is a seed?", "A seed is a tiny living thing that can grow into a plant when it has water, soil, and time.")],
    "growth": [("What helps a seed grow?", "A seed grows when it has the right kind of water, warmth, and care.")],
    "patience": [("Why is patience helpful?", "Patience helps you wait for the right moment, which can keep a problem small and safe.")],
    "storm": [("Why can a storm be scary?", "A storm can bring strong wind, dark clouds, and sudden rain, so it can make things feel hard to control.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is something you understand better after seeing what happens.")],
    "transformation": [("What is transformation?", "A transformation is when something changes into a new form or state.")],
}
KNOWLEDGE_ORDER = ["rectangular", "seed", "growth", "patience", "storm", "lesson", "transformation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    action = f["action"]
    return [
        f'Write a fable for a young child that includes the word "rectangular" and ends with a transformation in {setting.place}.',
        f"Tell a suspenseful animal story about a fox, a crow, and a rectangular seed bed, where {action.suspense}.",
        f"Write a lesson-learned fable in which a small creature chooses a careful action and a seed changes by the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    fox = f["fox"]
    action = f["action"]
    seed = f["seed"]
    qa = [
        QAItem("Who is the story about?", f"It is about {fox.label} and the crow watching a rectangular seed bed."),
        QAItem("What made the night feel tense?", f"The crow warned that {action.suspense}. That made the fox stop and think before acting."),
        QAItem("What choice did the fox make?", f"The fox chose to {action.urge}. That careful choice helped protect the seed instead of rushing past the problem."),
    ]
    if f.get("lesson"):
        qa.append(QAItem("What lesson was learned?", "The story teaches that patience can be brave. A careful choice can protect something small until it is ready to change."))
    if f.get("transformed"):
        qa.append(QAItem("What changed by the end?", "The tiny seed became a young plant. The rectangular bed that held only waiting at the start now held new life."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"rectangular", "seed", "growth", "lesson", "transformation"}
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def explain_rejection(thing: Thing, action: Action) -> str:
    return f"(No story: {thing.label} is not a reasonable focus for {action.id}; the fable needs a rectangular living thing that can transform.)"


def explain_action(action_id: str) -> str:
    return f"(Refusing action '{action_id}': it is not a common-sense fable turn.)"


ASP_RULES = r"""
valid(S, A, T) :- setting(S), action(A), thing(T), rectangular(T), seedish(T), sensible(A).
suspense :- chosen_action(storm).
lesson :- chosen_action(A), sensible(A).
transformation :- growth(Seed, G), G >= 2.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.rectangular:
            lines.append(asp.fact("rectangular", tid))
        if t.living:
            lines.append(asp.fact("seedish", tid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if a.sense >= 2:
            lines.append(asp.fact("sensible", aid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    smoke = generate(resolve_params(argparse.Namespace(setting=None, creature=None, seed_thing=None, action=None, name=None, seed=None), random.Random(7)))
    if not smoke.story.strip():
        rc = 1
        print("MISMATCH: smoke story was empty.")
    else:
        print("OK: smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld with suspense, lesson learned, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--seed-thing", choices=THINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.seed_thing is None or c[2] == args.seed_thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, seed_thing = rng.choice(sorted(combos))
    return StoryParams(setting=setting, creature=args.creature or rng.choice(sorted(CREATURES)), seed_thing=seed_thing, action=action, name=args.name or rng.choice(["Ash", "Finn", "Pip", "Moss"]))


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CREATURES[params.creature], THINGS[params.seed_thing], ACTIONS[params.action])
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
    StoryParams("garden", "fox", "seed", "water", "Ash"),
    StoryParams("orchard", "hare", "seed", "shade", "Pip"),
    StoryParams("field", "fox", "seed", "storm", "Finn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                p = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
