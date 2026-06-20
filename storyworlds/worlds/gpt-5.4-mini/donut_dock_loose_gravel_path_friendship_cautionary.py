#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/donut_dock_loose_gravel_path_friendship_cautionary.py
====================================================================================

A small, self-contained storyworld about two friends walking along a loose
gravel path near a dock, sharing a donut, facing a careful warning, and learning
a simple lesson about staying safe while helping each other.

The domain is slice-of-life: a brief walk, a tempting shortcut, a risky wobble,
a cautious friend speaks up, and the ending proves what changed.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Scene:
    id: str
    setting: str
    dock: str
    path: str
    walk: str
    safe_spot: str
    snack: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    label: str
    action: str
    warning: str
    safe_alt: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    power: int
    sense: int
    success: str
    failure: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("wobble", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for friend in world.entities.values():
            if friend.role in {"friend", "cautioner"}:
                friend.memes["concern"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble)]


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


def hazard(choice: Choice) -> bool:
    return choice.id in {"dash_to_dock_edge", "step_on_loose_gravel"}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for choice in CHOICES:
            for response in RESPONSES:
                if hazard(CHOICES[choice]):
                    combos.append((scene, choice, response))
    return combos


def predict(world: World, choice_id: str) -> dict:
    sim = world.copy()
    _do_choice(sim, sim.get("hero"), CHOICES[choice_id], narrate=False)
    return {"wobble": sim.get("path").meters["wobble"]}


def _do_choice(world: World, hero: Entity, choice: Choice, narrate: bool = True) -> None:
    hero.meters["wobble"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, scene: Scene) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {friend.id} walked along a loose gravel path near the dock. "
        f"{scene.setting}."
    )
    world.say(
        f"They had a paper bag with a warm donut inside, and the walk felt easy until the gravel started shifting under their shoes."
    )


def tempt(world: World, hero: Entity, choice: Choice) -> None:
    hero.memes["want"] += 1
    world.say(
        f'{hero.id} smiled at the donut and said, "I can get there faster if I {choice.action}."'
    )
    world.say("For a moment, the shortcut sounded fun.")


def warn(world: World, friend: Entity, hero: Entity, choice: Choice) -> None:
    pred = predict(world, choice.id)
    friend.memes["caution"] += 1
    world.facts["predicted_wobble"] = pred["wobble"]
    world.say(
        f'{friend.id} looked at the shifting stones and shook {friend.pronoun("possessive")} head. '
        f'"Careful," {friend.id} said. "{choice.warning}"'
    )


def proceed(world: World, hero: Entity, friend: Entity, choice: Choice) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} slowed down, listened, and stopped before the loose gravel got worse."
        if choice.id == "slow_down"
        else f"{hero.id} tried the shortcut anyway, and the stones skittered underfoot."
    )


def stumble(world: World, hero: Entity, path: Entity) -> None:
    path.meters["wobble"] += 1
    hero.meters["stumble"] += 1
    world.say(
        f"The path shifted with a tiny scrape, and {hero.id} had to steady {hero.pronoun('object')} self."
    )


def lesson(world: World, hero: Entity, friend: Entity, scene: Scene) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say(
        f"Then {friend.id} pointed to the safer side of the path, and {hero.id} nodded. "
        f"They stayed near the steady boards by the dock, where the ground was firm."
    )
    world.say(
        f"{hero.id} broke the donut in half and shared it with {friend.id}. "
        f"That small stop made the walk feel peaceful again."
    )
    world.say(
        f"By the end, the donut was shared, the dock stayed in the distance, and both friends remembered {scene.lesson}."
    )


def rescue(world: World, response: Response) -> None:
    world.say(response.success)


def rescue_fail(world: World, response: Response) -> None:
    world.say(response.failure)


SCENES = {
    "dock_walk": Scene(
        "dock_walk",
        "the water glimmered beside them",
        "the dock",
        "the loose gravel path",
        "the path",
        "the wooden boards near the dock",
        "a donut from the bakery",
        "stay with the steady ground",
        tags={"dock", "path", "slice_of_life"},
    )
}

CHOICES = {
    "dash_to_dock_edge": Choice(
        "dash_to_dock_edge",
        "dash",
        "dash to the dock edge",
        "That gravel can slide, and the dock edge is close.",
        "walk slowly on the packed side",
        3,
        tags={"dock", "path"},
    ),
    "step_on_loose_gravel": Choice(
        "step_on_loose_gravel",
        "step on loose stones",
        "step on the loose gravel",
        "The loose stones can roll under your feet.",
        "keep to the flat boards",
        3,
        tags={"path"},
    ),
    "slow_down": Choice(
        "slow_down",
        "slow down",
        "slow down and keep to the safe edge",
        "keep to the steady boards",
        4,
        tags={"path", "lesson"},
    ),
}

RESPONSES = {
    "hold_hand": Response(
        "hold_hand",
        2,
        3,
        "They held hands, stepped onto the steady edge of the path, and the little wobble passed.",
        "They tried to steady themselves, but the gravel kept sliding.",
        tags={"friendship", "cautionary"},
    ),
    "sit_and_share": Response(
        "sit_and_share",
        2,
        3,
        "They sat on a bench by the dock, shared the donut, and waited until the path felt calm again.",
        "They sat down, but the gravel kept crunching under their shoes.",
        tags={"friendship", "lesson"},
    ),
    "ask_for_help": Response(
        "ask_for_help",
        3,
        4,
        "A nearby grown-up helped them along the firm boards, and soon the walk felt easy again.",
        "They called out for help, but nobody heard them over the wind.",
        tags={"cautionary", "lesson"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Noa", "Ivy", "Tessa", "Eli"]
BOY_NAMES = ["Nico", "Owen", "Milo", "Theo", "Ben", "Arlo"]


@dataclass
class StoryParams:
    scene: str
    choice: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        "Write a slice-of-life friendship story about two kids on a loose gravel path near a dock, with a donut and a careful warning.",
        f"Tell a gentle cautionary story where {hero.id} wants to rush forward, but {friend.id} notices the loose gravel and helps them choose the safer way.",
        "Write a story that ends with a lesson learned: friendship matters, and slowing down can keep everyone safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    scene = f["scene"]
    response = f["response"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id} and {friend.id}, two friends walking together near the dock."),
        ("Why did the friend warn them?",
         f"{friend.id} saw the loose gravel path shifting underfoot and knew a quick move could make someone wobble. That is why {friend.id} spoke up right away."),
        ("What did they do at the end?",
         f"They slowed down, shared the donut, and stayed on the steady side of the path. The ending shows that {scene.lesson}."),
        ("How did the caution help?",
         f"The warning kept {hero.id} from rushing onto the worst part of the gravel. Because they listened, the walk stayed calm instead of turning into a tumble."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dock?",
            answer="A dock is a wooden place by the water where people can walk, stand, or tie up boats."
        ),
        QAItem(
            question="What is loose gravel?",
            answer="Loose gravel is a bunch of small stones that can slide and roll under your feet."
        ),
        QAItem(
            question="Why should you be careful on a loose gravel path?",
            answer="Because the stones can move, it is easier to slip or wobble, so walking slowly is safer."
        ),
        QAItem(
            question="What is a donut?",
            answer="A donut is a sweet round snack, often soft and covered with sugar or glaze."
        ),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def tell(scene: Scene, choice: Choice, response: Response, hero_name: str, hero_gender: str, friend_name: str, friend_gender: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    path = world.add(Entity(id="path", kind="thing", type="path", label="the loose gravel path"))
    world.add(Entity(id="dock", kind="thing", type="dock", label="the dock"))

    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["scene"] = scene
    world.facts["choice"] = choice
    world.facts["response"] = response

    setup(world, hero, friend, scene)
    world.para()
    tempt(world, hero, choice)
    warn(world, friend, hero, choice)
    proceed(world, hero, friend, choice)
    stumble(world, hero, path)
    world.para()
    rescue(world, response)
    lesson(world, hero, friend, scene)

    world.facts["outcome"] = "lesson"
    return world


THEME_COMBOS = [("dock_walk", "dash_to_dock_edge", "hold_hand"), ("dock_walk", "step_on_loose_gravel", "sit_and_share"), ("dock_walk", "slow_down", "ask_for_help")]


def valid_choice(choice: Choice) -> bool:
    return choice.id in {"dash_to_dock_edge", "step_on_loose_gravel", "slow_down"}


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, c.sense))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense_r", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- scene(S), choice(C), response(R), sense(C,SC), SC >= 2, sense_r(R,SR), SR >= 2.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, choice=None, response=None, hero=None, hero_gender=None, friend=None, friend_gender=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life cautionary friendship storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.choice and not valid_choice(CHOICES[args.choice]):
        raise StoryError("That choice is not reasonable for this storyworld.")
    scene = args.scene or rng.choice(list(SCENES))
    choice = args.choice or rng.choice(list(CHOICES))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero_pool = GIRL_NAMES if hero_gender == "girl" else BOY_NAMES
    friend_pool = GIRL_NAMES if friend_gender == "girl" else BOY_NAMES
    hero = args.hero or rng.choice(hero_pool)
    friend = args.friend or rng.choice([n for n in friend_pool if n != hero] or friend_pool)
    return StoryParams(scene, choice, response, hero, hero_gender, friend, friend_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], CHOICES[params.choice], RESPONSES[params.response],
                 params.hero, params.hero_gender, params.friend, params.friend_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, c, r in asp_valid_combos():
            print(s, c, r)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("dock_walk", "dash_to_dock_edge", "hold_hand", "Mina", "girl", "Nico", "boy"),
            StoryParams("dock_walk", "step_on_loose_gravel", "sit_and_share", "Theo", "boy", "Lia", "girl"),
            StoryParams("dock_walk", "slow_down", "ask_for_help", "Ivy", "girl", "Ben", "boy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
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
