#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/downward_curvature_scout_repetition_nursery_rhyme.py
=====================================================================================

A small nursery-rhyme storyworld about a little scout on a curving hill path.

Premise
-------
A child scout walks a path with a gentle downward curvature to deliver a lost
thing home. The path repeats in little steps, the scout repeats a helpful line,
and the ending proves the journey changed the world state: the lost thing is
found, the fear settles, and the hill path becomes a safe return.

This world is deliberately tiny and classical:
- typed entities with meters and memes
- state-driven narration
- a repetition feature
- a reasonableness gate
- a Python/ASP twin
- story-grounded and world-knowledge QA
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.meters == {}:
            self.meters = {}
        if self.memes == {}:
            self.memes = {}

    def m(self, key: str) -> float:
        return float(self.meters.get(key, 0.0))

    def e(self, key: str) -> float:
        return float(self.memes.get(key, 0.0))

    def add_m(self, key: str, value: float) -> None:
        self.meters[key] = self.m(key) + value

    def add_e(self, key: str, value: float) -> None:
        self.memes[key] = self.e(key) + value

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Route:
    id: str
    scene: str
    rhyme1: str
    rhyme2: str
    repeat: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ScoutKit:
    id: str
    label: str
    glow: str
    tags: set[str] = field(default_factory=set)


@dataclass
class LostThing:
    id: str
    label: str
    phrase: str
    on_path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelpAction:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    route: str
    kit: str
    lost: str
    action: str
    scout_name: str
    scout_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


ROUTES = {
    "hill_path": Route(
        "hill_path",
        "a hill path",
        "Down, down, down the curving path,",
        "softly, slowly, step by step,",
        "Down, down, down she went again,",
        "the path smiled wide and brought her home.",
        {"downward", "curvature", "repetition"},
    ),
    "bridge_path": Route(
        "bridge_path",
        "a bridge walk",
        "Down, down, down the winding bridge,",
        "tap, tap, tap, the little feet,",
        "Down, down, down she looked once more,",
        "the bridge carried every brave return.",
        {"downward", "curvature", "repetition"},
    ),
}

KITS = {
    "lantern": ScoutKit("lantern", "a lantern", "glowed like a moon", {"light"}),
    "bell": ScoutKit("bell", "a little bell", "rang bright and clear", {"sound"}),
    "map": ScoutKit("map", "a paper map", "showed the way", {"map"}),
}

LOST = {
    "lamb": LostThing("lamb", "lamb", "the little lamb", "near the lower gate", {"animal"}),
    "button": LostThing("button", "button", "the bright red button", "beside the path stones", {"small_object"}),
    "shoe": LostThing("shoe", "shoe", "the tiny shoe", "under the hedge by the slope", {"clothing"}),
}

ACTIONS = {
    "carry_down": HelpAction(
        "carry_down", 3, 3,
        "picked it up carefully and carried it downward in her hands",
        "tried to hurry it along, but it slipped away again",
        "picked it up carefully and carried it downward in her hands",
        {"care", "downward"},
    ),
    "guide_home": HelpAction(
        "guide_home", 2, 2,
        "held it gently and guided it home along the curve",
        "guided it, but the way was too steep and it slipped",
        "held it gently and guided it home along the curve",
        {"care", "curvature"},
    ),
    "call_help": HelpAction(
        "call_help", 3, 4,
        "called softly, and a grown-up came to help carry it down",
        "called softly, but the lost thing stayed hidden",
        "called softly, and a grown-up came to help carry it down",
        {"care", "help"},
    ),
}

SCOUT_NAMES = ["Mina", "Lily", "Nora", "Tess", "Ivy", "Mabel"]
HELPER_NAMES = ["Mama", "Papa", "Nana", "Dada"]

KNOWLEDGE = {
    "downward": [("What does downward mean?",
                  "Downward means going to a lower place or moving toward the ground.")],
    "curvature": [("What is curvature?",
                   "Curvature is the shape of something that bends instead of staying straight.")],
    "scout": [("What is a scout?",
                "A scout is someone who looks carefully, notices clues, and helps lead the way.")],
    "lantern": [("What does a lantern do?",
                 "A lantern gives light so you can see when it is dim.")],
    "bell": [("What does a bell do?",
              "A bell makes a clear ring that people can hear from far away.")],
    "map": [("What is a map?",
                "A map shows where things are and helps you find your way.")],
}
KNOWLEDGE_ORDER = ["scout", "downward", "curvature", "lantern", "bell", "map"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid in ROUTES:
        for kid in KITS:
            for lid in LOST:
                combos.append((rid, kid, lid))
    return combos


def reasonableness_gate(route: Route, lost: LostThing) -> bool:
    return "downward" in route.tags and "curvature" in route.tags and lost.label


def outcome_of(params: StoryParams) -> str:
    return "found"


def build_world(params: StoryParams) -> World:
    route = ROUTES[params.route]
    kit = KITS[params.kit]
    lost = LOST[params.lost]
    action = ACTIONS[params.action]
    world = World()
    scout = world.add(Entity(id=params.scout_name, kind="character", type=params.scout_type, role="scout"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    path = world.add(Entity(id="path", type="place", label=route.scene, tags=set(route.tags)))
    thing = world.add(Entity(id="lost", type="thing", label=lost.label, tags=set(lost.tags)))
    world.facts.update(route=route, kit=kit, lost=lost, action=action, scout=scout, helper=helper, path=path, thing=thing)

    scout.add_e("hope", 1)
    scout.add_e("focus", 1)
    if kit.id == "lantern":
        scout.add_e("confidence", 1)

    world.say(f"{scout.id} was a little scout on {route.scene}.")
    world.say(f"{scout.id} carried {kit.label}, and {kit.glow}.")
    world.say(f"{route.rhyme1} {route.rhyme2}")
    world.say(f"{scout.id} looked and listened, for {lost.phrase} was nowhere near.")
    world.para()

    world.say(f"Then {scout.id} heard a tiny clue by the stones.")
    world.say(f"{scout.id} said, 'Down, down, down,' and repeated it once more.")
    world.say(f"{scout.id} said, 'Down, down, down,' and followed the bend again.")
    world.say(f"The path was a gentle { 'curvature' }, and the clue pointed low.")
    world.say(f"At last {lost.phrase} waited {lost.on_path}.")
    world.para()

    if action.id == "call_help":
        world.say(f"{scout.id} lifted {lost.label} carefully, but {scout.pronoun()} knew the slope was steep.")
        world.say(f"{helper.id} came close and smiled, and together they {action.text}.")
        thing.add_m("found", 1)
        thing.add_e("safe", 1)
    elif action.id == "guide_home":
        world.say(f"{scout.id} held {lost.label} gently and {action.text}.")
        thing.add_m("found", 1)
        thing.add_e("safe", 1)
    else:
        world.say(f"{scout.id} {action.text}.")
        thing.add_m("found", 1)
        thing.add_e("safe", 1)

    scout.add_e("joy", 2)
    helper.add_e("pride", 1)
    world.say(f"{route.repeat} {lost.phrase} came home again.")
    world.say(f"{route.end_image}")

    world.facts["outcome"] = "found"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route, lost, kit = f["route"], f["lost"], f["kit"]
    return [
        f'Write a nursery-rhyme story that includes the words "downward", "curvature", and "scout".',
        f"Tell a gentle repeated story about a scout with {kit.label} looking for {lost.phrase} on {route.scene}.",
        f'Write a short rhyme where a little scout goes downward along a curving path and finds {lost.phrase}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    route, lost, scout, helper = f["route"], f["lost"], f["scout"], f["helper"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {scout.id}, a little scout, and {helper.id}, who helps at the end. The scout follows a curving path and keeps looking until the lost thing is found.",
        ),
        QAItem(
            question="What was the scout looking for?",
            answer=f"{scout.id} was looking for {lost.phrase}. It was waiting lower down on the path, so the scout had to keep going downward.",
        ),
        QAItem(
            question="How did the repeated words help the story?",
            answer=f"The repeated line, 'Down, down, down,' matched the path and kept the journey feeling steady. It also showed the scout trying again and again until the clue made sense.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["route"].tags) | set(world.facts["kit"].tags) | set(world.facts["lost"].tags)
    items: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            items.append(QAItem(q, a))
    return items


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("downward", rid))
        lines.append(asp.fact("curvature", rid))
    for kid in KITS:
        lines.append(asp.fact("kit", kid))
    for lid in LOST:
        lines.append(asp.fact("lost", lid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, K, L) :- route(R), kit(K), lost(L), downward(R), curvature(R).
outcome(found) :- valid(_, _, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    model = asp.one_model(asp_program(extra="", show="#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(route=None, kit=None, lost=None, action=None, scout_name=None, scout_type=None, helper_name=None, helper_type=None), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test story generation works.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: a scout on a curving downward path.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--lost", choices=LOST)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--scout-name", dest="scout_name")
    ap.add_argument("--scout-type", dest="scout_type", choices=["girl", "boy"])
    ap.add_argument("--helper-name", dest="helper_name")
    ap.add_argument("--helper-type", dest="helper_type", choices=["mother", "father"])
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
    combos = valid_combos()
    route = args.route or rng.choice(sorted(ROUTES))
    kit = args.kit or rng.choice(sorted(KITS))
    lost = args.lost or rng.choice(sorted(LOST))
    action = args.action or rng.choice(sorted(ACTIONS))
    scout_name = args.scout_name or rng.choice(SCOUT_NAMES)
    scout_type = args.scout_type or rng.choice(["girl", "boy"])
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    if (route, kit, lost) not in combos:
        raise StoryError("No valid combination matches the given options.")
    return StoryParams(route, kit, lost, action, scout_name, scout_type, helper_name, helper_type)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    StoryParams("hill_path", "lantern", "lamb", "guide_home", "Mina", "girl", "Mama", "mother"),
    StoryParams("bridge_path", "bell", "button", "carry_down", "Lily", "girl", "Nana", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
