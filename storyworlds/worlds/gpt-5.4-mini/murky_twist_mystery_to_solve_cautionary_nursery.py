#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py
===================================================================================

A tiny storyworld in a nursery-rhyme mood: a child, a murky place, a mystery to
solve, and a cautionary turn that teaches a safe choice. The world is built from
simulated state: a little game begins in rhyme, a clue goes missing in the murky
place, a tempting shortcut causes trouble, and a careful helper solves it with a
calm, child-safe ending.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py
    python storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py --all
    python storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/murky_twist_mystery_to_solve_cautionary_nursery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters or {})
        self.memes = dict(self.memes or {})

    def m(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def e(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
@dataclass
class StoryParams:
    setting: str
    lost_thing: str
    murky_place: str
    twist: str
    clue: str
    safe_tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
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


@dataclass
class Setting:
    id: str
    scene: str
    rhyme_open: str
    murk: str
    ending_image: str

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
class LostThing:
    id: str
    label: str
    color: str
    size: str
    precious: str

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
class Twist:
    id: str
    danger_move: str
    caution: str
    fix: str
    ending: str

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
class Tool:
    id: str
    label: str
    shine: str
    safe: bool = True

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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


SETTINGS = {
    "garden": Setting("garden", "a garden with daisies and a little gate",
                      "In the garden bright and neat, the children skipped with tiny feet.",
                      "Then came a murky patch below, where weeds and reeds would softly grow.",
                      "At the end, the pond was calm, and the moon sat like a silver balm."),
    "brook": Setting("brook", "a brook with stones and ferny shade",
                    "By the brook so cool and slow, the dragonflies were seen to go.",
                    "But in the murky water's bend, the little reeds began to wend.",
                    "At the end, the brook flashed clear, and every clue was easy here."),
    "yard": Setting("yard", "a yard with a swing and a berry bush",
                   "In the yard with hop and skip, the children gave a cheerful trip.",
                   "Then under leaves, in murky green, a hidden sparkle could be seen.",
                   "At the end, the yard grew bright, with one small clue set safe and right."),
}

LOST_THINGS = {
    "bell": LostThing("bell", "a tiny silver bell", "silver", "tiny", "sweet"),
    "kite": LostThing("kite", "a bright red kite", "red", "small", "bold"),
    "pebble": LostThing("pebble", "a smooth blue pebble", "blue", "small", "special"),
}

TWISTS = {
    "duck": Twist("duck", "wade into the murky place for a look", "The murky water hides the bottom, so little feet should not wander in alone.", "call for a grown-up with a long stick", "The duck was only a decoy; the real clue waited near the bank."),
    "tadpole": Twist("tadpole", "reach farther and farther with wet sleeves", "Leaning too close to the murky water can make a child slip.", "use a lantern and a net from the shore", "The tadpole was not the lost thing at all, but it pointed to it."),
    "shadow": Twist("shadow", "rush at the dark shape with a splash", "A splash in murky water can hide stones and make a fall.", "slow down and ask what the shape could be", "The shadow was only a leaf, and the true clue gleamed nearby."),
}

TOOLS = {
    "lantern": Tool("lantern", "a little lantern", "glowing like a star"),
    "net": Tool("net", "a small net", "held steady in kind hands"),
    "stick": Tool("stick", "a long stick", "reached out from the bank"),
    "magnifier": Tool("magnifier", "a round magnifier", "made tiny glimmers large"),
}

CHILD_NAMES = ["Lily", "Mina", "Nora", "Pip", "Tessa", "Will", "Eli", "Milo"]
HELPER_NAMES = ["Mama", "Papa", "Aunt Joy", "Uncle Ben", "Gran", "Dad"]
GENTLE_TRAITS = ["careful", "curious", "patient", "thoughtful", "cautious"]


def rhyming_opening(setting: Setting, child: Entity, helper: Entity) -> str:
    return f"{setting.rhyme_open} {child.id} and {helper.id} went walking by."


def predict_misstep(world: World, child: Entity, twist: Twist) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["impulse"] = 1.0
    simulate_misstep(sim, child, twist, narrate=False)
    return {
        "fall_risk": sim.get(child.id).meters.get("soggy", 0.0) >= THRESHOLD,
        "fear": sim.get(child.id).memes.get("fear", 0.0),
    }


def simulate_misstep(world: World, child: Entity, twist: Twist, narrate: bool = True) -> None:
    child.meters["soggy"] = child.meters.get("soggy", 0.0) + 1.0
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1.0
    world.get("murk").meters["disturbed"] = world.get("murk").meters.get("disturbed", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} leaned too far and made a tiny splash.")


def simulate_solution(world: World, child: Entity, helper: Entity, tool: Tool, lost: LostThing) -> None:
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    helper.memes["care"] = helper.memes.get("care", 0.0) + 1.0
    world.say(f"{helper.id} used {tool.label}, and {tool.shine}.")
    world.say(f"Together they found {lost.label} and lifted it dry from the bank.")


def tell(setting: Setting, lost: LostThing, twist: Twist, tool: Tool,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    murk = world.add(Entity(id="murk", type="place", label="the murky place"))
    clue = world.add(Entity(id="clue", type="thing", label=lost.label))
    world.facts.update(setting=setting, lost=lost, twist=twist, tool=tool, child=child, helper=helper, murk=murk, clue=clue)

    world.say(rhyming_opening(setting, child, helper))
    world.say(f"They searched the {setting.scene}, for {lost.precious} things were shy.")
    world.para()
    world.say(f"But there, by the murky place, a mystery began to lie.")
    world.say(f"A {lost.color} glint was spotted near the reeds, and {child.id} wanted to {twist.danger_move}.")
    pred = predict_misstep(world, child, twist)
    child.memes["want"] = 1.0
    if pred["fall_risk"]:
        world.say(f"{helper.id} warned softly: \"{twist.caution}\"")
        world.say(f"\"Let's not be rash,\" {helper.id} said. \"A safe way will solve the task.\"")
    world.para()
    child.memes["impulse"] = 1.0
    simulate_misstep(world, child, twist, narrate=True)
    world.say(f"{child.id} froze, because the splash hid the shiny thing from sight.")
    world.para()
    world.say(f"Then {helper.id} showed {tool.label}, {twist.fix}, and the searching grew slow.")
    simulate_solution(world, child, helper, tool, lost)
    world.para()
    world.say(f"{twist.ending} {setting.ending_image}")
    world.say(f"{child.id} smiled small and bright, and promised to stay on dry ground in sight.")

    world.facts.update(outcome="solved", warned=True, predicted=pred["fall_risk"], disturbed=world.get("murk").meters.get("disturbed", 0.0) > 0)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style mystery story that includes the word "murky" and ends safely.',
        f"Tell a cautionary little rhyme where {f['child'].id} and {f['helper'].id} search for {f['lost'].label} near a murky place, but choose a safe tool instead of a risky shortcut.",
        f"Write a child-friendly mystery to solve with a twist: something shiny is seen in the murky place, a warning is given, and the ending shows the clue found in a safe way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, lost, twist, tool = f["child"], f["helper"], f["lost"], f["twist"], f["tool"]
    return [
        QAItem(
            question="What was the mystery in the story?",
            answer=f"They were trying to find {lost.label}, and the shiny clue was hiding near the murky place. The mystery mattered because the child wanted to hurry, but the helper chose a careful way.",
        ),
        QAItem(
            question="Why did the helper warn the child?",
            answer=f"{twist.caution} The helper knew a splash could make the search slippery, so the warning kept the child safe before anything worse could happen.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{helper.id} used {tool.label} and the search stayed on dry ground. That careful method found {lost.label} without anyone falling in the murky place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does murky mean?", "Murky means dark, cloudy, or hard to see through. Water or a place can be murky when the bottom is not easy to see."),
        QAItem("Why is it safer not to wade into muddy water?", "Muddy water can hide slippery stones, holes, or deep spots. Staying on the bank helps a child avoid a fall."),
        QAItem("What is a lantern for?", "A lantern gives light in a gentle, safe way. It helps people look around without needing to go into danger."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme murky mystery storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--lost-thing", choices=LOST_THINGS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--safe-tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["mother", "father", "girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for l in LOST_THINGS:
            for t in TWISTS:
                for tool in TOOLS:
                    combos.append((s, l, t, tool))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for l in LOST_THINGS:
        lines.append(asp.fact("lost", l))
    for t in TWISTS:
        lines.append(asp.fact("twist", t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,L,T,U) :- setting(S), lost(L), twist(T), tool(U).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if not combos:
        raise StoryError("No valid story combinations.")
    setting = args.setting or rng.choice(list(SETTINGS))
    lost = args.lost_thing or rng.choice(list(LOST_THINGS))
    twist = args.twist or rng.choice(list(TWISTS))
    tool = args.safe_tool or rng.choice(list(TOOLS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(setting, lost, setting, twist, tool, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], LOST_THINGS[params.lost_thing], TWISTS[params.twist], TOOLS[params.safe_tool], params.child, params.child_gender, params.helper, params.helper_gender)
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
    StoryParams("garden", "bell", "duck", "lantern", "Lily", "girl", "Mama", "mother"),
    StoryParams("brook", "kite", "shadow", "stick", "Pip", "boy", "Gran", "mother"),
    StoryParams("yard", "pebble", "tadpole", "net", "Mina", "girl", "Aunt Joy", "father"),
]


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        ok = False
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = False
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        return
    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(CURATED[i % len(CURATED)]) for i in range(len(CURATED))] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(rng_base + i))
            p.seed = rng_base + i
            s = generate(p)
            if s.story not in seen:
                samples.append(s)
                seen.add(s.story)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
