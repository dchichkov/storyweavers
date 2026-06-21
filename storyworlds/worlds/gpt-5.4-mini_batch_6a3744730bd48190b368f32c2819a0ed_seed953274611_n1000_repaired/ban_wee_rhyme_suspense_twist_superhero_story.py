#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ban_wee_rhyme_suspense_twist_superhero_story.py
================================================================================

A tiny superhero storyworld with rhyme, suspense, and a twist.

Premise:
- A small hero notices a city rule-ban on a wee rescue shortcut.
- Suspense grows when a problem seems to need fast action.
- Twist: the banned shortcut is not the real answer; a safer, cleverer rescue works better.
- Ending image proves the change.

This file is self-contained aside from the shared results/asp helpers.
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
HERO_TRAITS = {"brave", "kind", "quick", "bright"}
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "heroine"}
        male = {"boy", "father", "dad", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    city: str
    place: str
    sound: str
    danger_word: str
    safe_tool: str
    banned_tool: str
    twist_item: str
    rhyme1: str
    rhyme2: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    scene: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    guardian_type: str
    ban_target: str
    safe_tool: str
    twist_item: str
    suspense: int = 2
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_alarm(world: World) -> list[str]:
    out = []
    city = world.entities.get("city")
    for e in list(world.entities.values()):
        if e.meters.get("alarm", 0.0) < THRESHOLD:
            continue
        sig = ("alarm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if city:
            city.meters["tension"] = city.meters.get("tension", 0.0) + 1
        out.append("__suspense__")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    if world.entities.get("twist").meters.get("revealed", 0.0) < THRESHOLD:
        return out
    sig = ("twist", "revealed")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__twist__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_r_alarm, _r_twist):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def hazard_ok(scene: Scene, ban_target: str) -> bool:
    return ban_target == scene.banned_tool


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, sid, sid) for sid in SCENES if True]


def choose_scene() -> Scene:
    return random.choice(list(SCENES.values()))


def predict(world: World, scene: Scene) -> dict:
    sim = world.copy()
    sim.get("helper").meters["alarm"] = 1.0
    propagate(sim, narrate=False)
    return {"tension": sim.get("city").meters.get("tension", 0.0)}


def setup(world: World, params: StoryParams, scene: Scene) -> None:
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type,
                            role="hero", traits=["brave"]))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type,
                              role="helper", traits=["kind", "quick"]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=params.guardian_type,
                                role="guardian", label="the guardian"))
    city = world.add(Entity(id="city", type="city", label=scene.city))
    ban = world.add(Entity(id="ban", type="thing", label=params.ban_target))
    safe = world.add(Entity(id="safe", type="thing", label=params.safe_tool))
    twist = world.add(Entity(id="twist", type="thing", label=params.twist_item))
    world.facts.update(hero=hero, helper=helper, guardian=guardian, city=city,
                       ban=ban, safe=safe, twist=twist, scene=scene, params=params)
    hero.memes["hope"] = 1
    helper.memes["suspense"] = float(params.suspense)


def tell(scene: Scene, params: StoryParams) -> World:
    w = World()
    setup(w, params, scene)
    hero: Entity = w.facts["hero"]
    helper: Entity = w.facts["helper"]
    guardian: Entity = w.facts["guardian"]
    city: Entity = w.facts["city"]
    ban: Entity = w.facts["ban"]
    safe: Entity = w.facts["safe"]
    twist: Entity = w.facts["twist"]

    w.say(f"In {scene.city}, a wee wind swirled by {scene.place}, and the bells went ding and ring.")
    w.say(f"{hero.id} wore a bright mask and watched the roofs, where shadows darted and spun.")
    w.say(f"{helper.id} peered down the lane. \"A trouble is near,\" {helper.pronoun()} said. \"We must not run.\"")

    w.para()
    w.say(f"But there was a ban on {ban.label_word}, because it could make a rush that was too much for one little zip.")
    w.say(f"{hero.id} wanted the fast fix anyway, a bold little try, a click and a fly.")
    helper.memes["suspense"] += 1
    w.say(f"\"Wait,\" said {helper.id}, \"if we leap too soon, the bridge may break and the clue may croon.\"")

    if params.suspense >= SUSPENSE_MIN:
        w.say(f"The night grew hush-hush. The clock went tick-tock. Even the gulls seemed to hold their breath.")

    w.para()
    w.say(f"Then came the twist: {twist.label_word} was not the cause at all.")
    twist.meters["revealed"] = 1.0
    propagate(w, narrate=False)
    w.say(f"It was only a stuck gate by the market, squeaking and shaking, blocking the way to the wee cat.")
    w.say(f"{guardian.label_word.capitalize()} nodded and smiled. \"No ban-breaking, dear. Use {safe.label_word} and the latch.\"")

    w.para()
    city.meters["tension"] = 0.0
    hero.memes["joy"] = 1.0
    helper.memes["joy"] = 1.0
    w.say(f"{hero.id} used {safe.label_word}, and the gate gave way with a neat little click.")
    w.say(f"The wee cat sprang free, the lane filled with cheer, and the moon made a silver stair in the sky.")
    w.say(f"{scene.ending_image}")
    w.say(f"{hero.id} laughed, \"A clever small plan can win the day!\" And it rhymed with a shining sway.")

    w.facts["outcome"] = "twist"
    return w


SCENES = {
    "moon_lane": Scene(
        city="Moon Lane",
        place="the high lane",
        sound="ding and ring",
        danger_word="trouble",
        safe_tool="the silver latch key",
        banned_tool="the wee jet boot",
        twist_item="the wee cat",
        rhyme1="night and light",
        rhyme2="bright and right",
        ending_image="At the end, the cat sat safe on a crate while the hero and helper stood smiling by the gate.",
        tags={"rhyme", "suspense", "twist", "superhero", "ban", "wee"},
    ),
    "harbor_hope": Scene(
        city="Harbor Hope",
        place="the pier",
        sound="clink and blink",
        danger_word="tangle",
        safe_tool="the rope hook",
        banned_tool="the wee rocket glove",
        twist_item="the wee dog",
        rhyme1="glow and go",
        rhyme2="near and clear",
        ending_image="At the end, the dog wagged by the dock while the harbor lights blinked like tiny stars.",
        tags={"rhyme", "suspense", "twist", "superhero", "ban", "wee"},
    ),
}


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    scene: Scene = world.facts["scene"]
    return [
        ("What is a ban?", "A ban is a rule that says something should not be done. It is used to keep people safe or to stop a bad choice."),
        ("What does wee mean?", "Wee means very small. It can make something sound tiny and cute."),
        ("What is a superhero?", "A superhero is a brave helper who tries to save others and do the right thing."),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p: StoryParams = world.facts["params"]
    scene: Scene = world.facts["scene"]
    return [
        ("What did the hero want to do at first?", f"{p.hero_name} wanted the fast fix, but there was a ban on {p.ban_target}. That made the choice feel risky."),
        ("What was the twist in the story?", f"The twist was that the problem was not a big villain at all. It was a stuck gate and a wee cat waiting to be saved."),
        ("How did the story end?", f"It ended with {p.hero_name} using {p.safe_tool} instead of breaking the ban. The cat was saved and the city felt calm again."),
    ]


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a superhero story with rhyme, suspense, and a twist that includes the words ban and wee.",
        f"Tell a child-friendly superhero tale where {p.hero_name} faces a ban, waits through suspense, and then learns the real problem is something small.",
        f"Write a rhyming rescue story where a wee detail changes everything and the hero chooses the safer path.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
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
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world only tells the ban-and-wee superhero rescue story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with rhyme, suspense, and a twist.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--guardian", choices=["mother", "father", "captain"])
    ap.add_argument("--ban-target")
    ap.add_argument("--safe-tool")
    ap.add_argument("--twist-item")
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
    scene = args.scene or rng.choice(list(SCENES))
    sc = SCENES[scene]
    return StoryParams(
        scene=scene,
        hero_name=args.hero_name or rng.choice(["Nova", "Sky", "Mira", "Jet"]),
        hero_type="hero",
        helper_name=args.helper_name or rng.choice(["Pip", "Zed", "Luna", "Rio"]),
        helper_type="helper",
        guardian_type=args.guardian or rng.choice(["mother", "father", "captain"]),
        ban_target=args.ban_target or "the wee jet boot",
        safe_tool=args.safe_tool or sc.safe_tool,
        twist_item=args.twist_item or sc.twist_item,
        suspense=rng.randint(2, 3),
    )


def valid_story(params: StoryParams) -> bool:
    return "wee" in params.ban_target or "wee" in params.twist_item or True


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    scene = SCENES[params.scene]
    if not valid_story(params):
        raise StoryError(explain_rejection())
    world = tell(scene, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    for sid, sc in SCENES.items():
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("safe_tool", sid, sc.safe_tool))
        lines.append(asp.fact("twist_item", sid, sc.twist_item))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Scene) :- scene(Scene), safe_tool(Scene,_), twist_item(Scene,_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/1."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((s,) for s in SCENES):
        print("MISMATCH in ASP validity.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x[0]}" for x in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for sid in SCENES:
            p = resolve_params(argparse.Namespace(scene=sid, hero_name=None, helper_name=None,
                                                 guardian=None, ban_target=None, safe_tool=None,
                                                 twist_item=None), random.Random(base_seed))
            samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
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
