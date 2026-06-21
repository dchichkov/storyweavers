#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ups_suspense_happy_ending_flashback_detective_story.py
======================================================================================

A small detective-style storyworld about a missing package, a tense clue trail,
a flashback that reveals what really happened, and a happy ending where the
right delivery is found.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a causal state machine that drives prose
- a reasonableness gate for valid combinations
- an inline ASP twin for parity checks
- three Q&A sets grounded in simulated world state
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

CITY_NAMES = ["Briar", "Maple", "Willow", "Cedar"]
CHARACTER_NAMES = ["Mina", "Toby", "Iris", "Noah", "Nina", "Eli", "Pia", "Owen"]
SUSPECT_NAMES = ["Mr. Reed", "Ms. Lane", "Dr. Bell", "Mrs. Vale"]
SETTING_NAMES = ["the quiet street", "the old station", "the tiny office", "the front porch"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Scene:
    town: str
    place: str
    clue_spot: str
    sound: str
    flashback_trigger: str
    ending_image: str


@dataclass
class Mystery:
    id: str
    object_name: str
    label: str
    located_at: str
    innocent: str
    suspicious: str
    flashback: str
    clue_word: str = "ups"
    safe_resolution: str = "The package was never lost at all; it had gone to the wrong desk"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    mystery: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    suspect_name: str
    suspect_gender: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_anxiety(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["tension"] >= THRESHOLD and ("anxiety", e.id) not in world.fired:
            world.fired.add(("anxiety", e.id))
            e.memes["worry"] += 1
            out.append("")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    if world.facts.get("flashback_seen") and ("flashback",) not in world.fired:
        world.fired.add(("flashback",))
        out.append("")
    return out


CAUSAL_RULES = [Rule("anxiety", _r_anxiety), Rule("flashback", _r_flashback)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced:
                changed = True


def valid_combos() -> list[tuple[str, str]]:
    return [(scene, mystery) for scene in SCENES for mystery in MYSTERIES]


def sensible_mysteries() -> list[Mystery]:
    return list(MYSTERIES.values())


def clue_is_plausible(mystery: Mystery) -> bool:
    return bool(mystery.object_name) and bool(mystery.located_at)


def scene_by_name(scene_id: str) -> Scene:
    if scene_id not in SCENES:
        raise StoryError(f"Unknown scene '{scene_id}'.")
    return SCENES[scene_id]


def mystery_by_name(mystery_id: str) -> Mystery:
    if mystery_id not in MYSTERIES:
        raise StoryError(f"Unknown mystery '{mystery_id}'.")
    return MYSTERIES[mystery_id]


def tell(scene: Scene, mystery: Mystery, detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str, suspect_name: str, suspect_gender: str) -> World:
    world = World()
    d = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    h = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    s = world.add(Entity(id=suspect_name, kind="character", type=suspect_gender, role="suspect"))
    pkg = world.add(Entity(id="package", kind="thing", type="package", label=mystery.object_name))
    desk = world.add(Entity(id="desk", kind="thing", type="desk", label=mystery.located_at))
    office = world.add(Entity(id="office", kind="thing", type="place", label=scene.place))
    world.facts["scene"] = scene
    world.facts["mystery"] = mystery
    world.facts["detective"] = d
    world.facts["helper"] = h
    world.facts["suspect"] = s
    world.facts["package"] = pkg
    world.facts["desk"] = desk
    world.facts["office"] = office

    d.memes["curiosity"] += 1
    h.memes["trust"] += 1
    s.memes["nervous"] += 0.5

    world.say(f"In {scene.town}, {detective_name} was the kind of detective who noticed small things.")
    world.say(f"One afternoon, {detective_name} and {helper_name} were at {scene.place}, where a {mystery.label} was supposed to be waiting.")
    world.say(f"Then someone whispered about {mystery.clue_word}, and the room suddenly felt smaller.")

    world.para()
    d.meters["tension"] += 1
    world.say(f"{detective_name} looked at the empty spot near the {desk.label_word} and frowned.")
    world.say(f'"If the {mystery.object_name} is gone," {detective_name} said, "then the case is not as simple as it seems."')
    world.say(f"{helper_name} noticed a narrow trail and pointed toward the {scene.clue_spot}.")

    world.para()
    world.say(f"At first, {suspect_name} seemed suspicious, because {mystery.suspicious}.")
    world.say(f"But then came a flashback: {mystery.flashback}.")
    world.facts["flashback_seen"] = True
    propagate(world)

    world.para()
    world.say(f"That memory changed everything. {detective_name} hurried back to the right place and checked the labels again.")
    world.say(f"In the end, {mystery.safe_resolution.lower()}, and the clue about {mystery.clue_word} made sense after all.")
    world.say(f"{scene.ending_image}.")
    world.say(f"{detective_name} smiled, because the mystery had a happy ending.")

    world.facts["outcome"] = "happy"
    return world


def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    s = world.facts["scene"]
    return [
        f"Write a detective story with suspense, a flashback, and a happy ending that includes the word '{m.clue_word}'.",
        f"Tell a child-friendly mystery set at {s.place} where a detective follows a clue, gets nervous, remembers a flashback, and solves the case.",
        f"Write a short detective story about a missing {m.object_name} that turns out to be safe after a flashback reveals the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    d = world.facts["detective"]
    h = world.facts["helper"]
    s = world.facts["suspect"]
    return [
        QAItem(
            question="What was the mystery about?",
            answer=f"It was about a missing {m.object_name}. The case felt mysterious at first, but the clues led to the truth."
        ),
        QAItem(
            question=f"Why did {d.id} feel suspense?",
            answer=f"{d.id} saw an empty spot and heard about {m.clue_word}, so the case seemed uncertain. The feeling changed when the flashback showed what really happened."
        ),
        QAItem(
            question="What did the flashback do?",
            answer=f"It explained that {m.flashback}. That made the suspicious-looking part of the story make sense."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily because the {m.object_name} was found in the right place and nobody had done anything wrong. The detective solved the mystery calmly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a detective?", answer="A detective is a person who looks for clues and tries to solve mysteries."),
        QAItem(question="What is a flashback?", answer="A flashback is a part of the story that shows something that happened earlier."),
        QAItem(question="Why can suspense feel exciting?", answer="Suspense makes you wonder what will happen next, and that waiting can feel exciting."),
        QAItem(question="What is a happy ending?", answer="A happy ending is when the problem gets solved and things turn out well."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


SCENES = {
    "street": Scene(town="Briar", place="the quiet street", clue_spot="front steps", sound="soft footsteps", flashback_trigger="a memory of the delivery cart", ending_image="The box rested safely on the right porch at last"),
    "station": Scene(town="Maple", place="the old station", clue_spot="ticket window", sound="a train whistle", flashback_trigger="a memory of the sorting shelf", ending_image="The package sat behind the right sign, neat and found"),
    "office": Scene(town="Willow", place="the tiny office", clue_spot="mail shelf", sound="a page rustling", flashback_trigger="a memory of the clerk's label", ending_image="The desk was tidy again, and the package was on the correct shelf"),
}

MYSTERIES = {
    "ups_box": Mystery(id="ups_box", object_name="UPS box", label="UPS package", located_at="the mail shelf", innocent="it had the right address", suspicious="it was sitting near the wrong desk", flashback="the clerk had set it aside while answering the phone", clue_word="ups", tags={"ups", "package"}),
    "brown_parcel": Mystery(id="brown_parcel", object_name="brown parcel", label="brown parcel", located_at="the front porch", innocent="it matched the neighbor's note", suspicious="it looked abandoned for a moment", flashback="the courier had hidden it behind a planter to keep it dry", clue_word="ups", tags={"ups", "parcel"}),
}

CURATED = [
    StoryParams(scene="street", mystery="ups_box", detective_name="Mina", detective_gender="girl", helper_name="Toby", helper_gender="boy", suspect_name="Mr. Reed", suspect_gender="boy"),
    StoryParams(scene="station", mystery="brown_parcel", detective_name="Iris", detective_gender="girl", helper_name="Owen", helper_gender="boy", suspect_name="Ms. Lane", suspect_gender="girl"),
]


def explain_rejection(scene_id: str, mystery_id: str) -> str:
    return f"(No story: {scene_id} and {mystery_id} do not form a valid detective mystery here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with suspense, flashback, and a happy ending.")
    ap.add_argument("--scene", choices=SCENES.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--suspect")
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
    if args.scene and args.mystery and (args.scene, args.mystery) not in combos:
        raise StoryError(explain_rejection(args.scene, args.mystery))
    if args.scene:
        scene = args.scene
    else:
        scene = rng.choice(sorted(SCENES))
    if args.mystery:
        mystery = args.mystery
    else:
        mystery = rng.choice(sorted(MYSTERIES))
    return StoryParams(
        scene=scene,
        mystery=mystery,
        detective_name=args.name or rng.choice(CHARACTER_NAMES),
        detective_gender="girl" if (args.name or "").endswith(("a", "i")) else rng.choice(["girl", "boy"]),
        helper_name=args.helper or rng.choice(CHARACTER_NAMES),
        helper_gender=rng.choice(["girl", "boy"]),
        suspect_name=args.suspect or rng.choice(SUSPECT_NAMES),
        suspect_gender=rng.choice(["girl", "boy"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"Unknown scene '{params.scene}'.")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery '{params.mystery}'.")
    scene = scene_by_name(params.scene)
    mystery = mystery_by_name(params.mystery)
    world = tell(scene, mystery, params.detective_name, params.detective_gender, params.helper_name, params.helper_gender, params.suspect_name, params.suspect_gender)
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("has_clue", mid, "ups"))
    lines.append(asp.fact("happy_ending", 1))
    lines.append(asp.fact("flashback", 1))
    lines.append(asp.fact("suspense", 1))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- scene(S), mystery(M), has_clue(M, ups).
story_feature(suspense) :- suspense(1).
story_feature(flashback) :- flashback(1).
story_feature(happy_ending) :- happy_ending(1).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        ok = False
        print("MISMATCH in valid combos:")
        print("  only in asp:", sorted(a - p))
        print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, mystery=None, name=None, helper=None, suspect=None), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2.\n#show story_feature/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, m in asp_valid_combos():
            print(f"{s} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
