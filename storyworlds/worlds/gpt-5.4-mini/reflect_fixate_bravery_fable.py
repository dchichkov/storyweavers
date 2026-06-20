#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/reflect_fixate_bravery_fable.py
===============================================================

A standalone story world for a small fable-like domain about reflection,
fixation, and bravery.

Seed prompt:
- Words: reflect, fixate
- Feature: Bravery
- Style: Fable

Domain:
A young animal fixates on a shiny thing near water, a wiser companion warns
them, a brave act changes the outcome, and the ending turns the lesson into a
small fable moral.

This script follows the storyworld contract:
- stdlib only
- imports shared results eagerly
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes Python reasonableness gate and inline ASP twin
- produces state-driven prose and grounded QA from simulated world facts
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
BRAVERY_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe", "sister"}
        male = {"boy", "father", "dad", "man", "buck", "brother"}
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
    place: str
    shine: str
    dark_spot: str
    animal_role: str
    pair_role: str
    moral: str


@dataclass
class ShinyThing:
    id: str
    label: str
    phrase: str
    near: str
    gleam: str
    reflectable: bool = True
    attractive: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    danger: str
    rescue: str
    power: int
    sense: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ripple(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["trouble"] < THRESHOLD:
            continue
        sig = ("ripple", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for key in ("fear", "shame"):
            if "hero" in world.entities:
                world.get("hero").memes[key] += 1
        out.append("__rumble__")
    return out


CAUSAL_RULES = [Rule("ripple", "social", _r_ripple)]


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


def can_fixate(shiny: ShinyThing, scene: Scene) -> bool:
    return shiny.reflectable and shiny.attractive and scene.shine == "reflective"


def risk_at_hand(shiny: ShinyThing, risk: Risk) -> bool:
    return shiny.reflectable and risk.power >= 1


def sensible_risks() -> list[Risk]:
    return [r for r in RISKS.values() if r.sense >= 2]


def outcome_of(params: "StoryParams") -> str:
    if params.bravery >= BRAVERY_MIN and params.delay == 0:
        return "brave"
    if params.delay >= 2:
        return "late"
    return "warned"


def predicted_mood(world: World, risk_id: str) -> dict:
    sim = world.copy()
    _do_mistake(sim, sim.get("hero"), sim.get(risk_id), narrate=False)
    return {
        "trouble": sim.get(risk_id).meters["trouble"],
        "fear": sim.get("hero").memes["fear"],
    }


def _do_mistake(world: World, hero: Entity, risk: Entity, narrate: bool = True) -> None:
    risk.meters["trouble"] += 1
    hero.memes["fixation"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity, scene: Scene) -> None:
    world.say(
        f"At {scene.place}, a small fable began: {hero.id} and {helper.id} "
        f"stood where the water could reflect the sky like polished glass."
    )
    world.say(
        f"{hero.id} loved the shine, and {helper.id} loved the quiet path by "
        f"{scene.dark_spot}."
    )


def fixate(world: World, hero: Entity, shiny: ShinyThing) -> None:
    hero.memes["fixation"] += 1
    world.say(
        f"{hero.id} could not look away. {hero.pronoun().capitalize()} began to "
        f"fixate on {shiny.phrase}, especially when the light {shiny.gleam}."
    )
    world.say(
        f'"Look," {hero.id} whispered, "the pond can reflect it so clearly."'
    )


def warn(world: World, helper: Entity, hero: Entity, shiny: ShinyThing, risk: Risk) -> bool:
    pred = predicted_mood(world, "risk")
    if not risk_at_hand(shiny, risk):
        return False
    helper.memes["care"] += 1
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{helper.id} stepped closer. "{hero.id}, do not reach for {shiny.label}. '
        f'It is easy to slip by {risk.near}, and {risk.danger}."'
    )
    return True


def brave_choice(world: World, hero: Entity, helper: Entity, shiny: ShinyThing, risk: Risk) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id} looked at the water, then at {helper.id}, and took a brave "
        f"breath instead of another stare."
    )
    world.say(
        f"With steady paws, {hero.id} used a long reed to lift {shiny.phrase} "
        f"away from {risk.near}."
    )
    world.say(
        f"The little crowd of ripples settled, and the shine stayed on safe ground."
    )


def late_choice(world: World, hero: Entity, helper: Entity, shiny: ShinyThing, risk: Risk, rescue: Risk) -> None:
    hero.memes["bravery"] += 1
    risk_ent = world.get("risk")
    risk_ent.meters["trouble"] += 1
    world.say(
        f"{hero.id} reached too quickly and the bank gave a tiny slide. "
        f"The shiny thing tipped toward {risk.near}."
    )
    if rescue.power >= 2:
        world.say(
            f"{helper.id} was brave too. {helper.pronoun().capitalize()} held a "
            f"branch out like a hand and guided {shiny.label} back before it vanished."
        )
    else:
        world.say(
            f"{helper.id} called for help at once, and the danger passed before it grew."
        )


def moral(world: World, helper: Entity, hero: Entity, shiny: ShinyThing, scene: Scene) -> None:
    hero.memes["peace"] += 1
    helper.memes["peace"] += 1
    world.say("For a moment they were both very still.")
    world.say(
        f"Then {helper.id} said, \"Bravery is not staring longest at the shiny thing. "
        f"Bravery is choosing the wise step when your heart wants to fixate.\""
    )
    world.say(
        f"{hero.id} nodded. By the time the sun slipped low, the water still "
        f"reflect the last gold light, but {hero.id} was looking at the path ahead."
    )
    world.say(f"And so the fable ended with a small lesson: {scene.moral}.")


def tell(scene: Scene, shiny: ShinyThing, risk: Risk, rescue: Risk,
         hero_name: str = "Robin", hero_type: str = "rabbit",
         helper_name: str = "Tess", helper_type: str = "tortoise",
         bravery: int = 2, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    world.add(Entity(id="risk", type="thing", label=risk.label))
    world.facts["scene"] = scene
    world.facts["shiny"] = shiny
    world.facts["risk_cfg"] = risk
    world.facts["rescue_cfg"] = rescue
    world.facts["bravery"] = bravery
    world.facts["delay"] = delay

    hero.memes["bravery"] = float(bravery)

    introduce(world, hero, helper, scene)
    world.para()
    fixate(world, hero, shiny)
    warn(world, helper, hero, shiny, risk)

    if bravery >= BRAVERY_MIN and delay == 0:
        brave_choice(world, hero, helper, shiny, risk)
        world.facts["outcome"] = "brave"
    else:
        _do_mistake(world, hero, world.get("risk"))
        world.para()
        late_choice(world, hero, helper, shiny, risk, rescue)
        world.facts["outcome"] = "late" if delay >= 2 else "warned"
    world.para()
    moral(world, helper, hero, shiny, scene)

    world.facts.update(hero=hero, helper=helper, risk=world.get("risk"))
    return world


SCENES = {
    "pond": Scene("pond", "the pond", "reflective", "the mossy bank", "a rabbit", "a tortoise", "Look twice, choose once."),
    "well": Scene("well", "the old well", "reflective", "the stone lip", "a fox", "a hen", "A brave heart listens first."),
    "stream": Scene("stream", "the stream", "reflective", "the muddy edge", "a lamb", "a goat", "Courage can be quiet."),
}

SHINY = {
    "coin": ShinyThing("coin", "coin", "a bright coin", "the water", "glittered", tags={"shine", "reflect"}),
    "bell": ShinyThing("bell", "bell", "a little brass bell", "the bank", "sparkled", tags={"shine", "reflect"}),
    "feather": ShinyThing("feather", "feather", "a white feather", "the reeds", "shimmered", tags={"shine", "reflect"}),
}

RISKS = {
    "slip": Risk("slip", "slip", "the bank can make you tumble into the water", "a long reed", 1, 2, tags={"water"}),
    "drop": Risk("drop", "drop", "the thing might sink out of reach", "a branch", 1, 2, tags={"water"}),
    "spill": Risk("spill", "spill", "the shiny thing might be lost in the mud", "steady paws", 1, 1, tags={"mud"}),
}

GENTLE_HELP = {
    "reed": Risk("reed", "reed", "a long reed can reach what paws cannot", "a long reed", 2, 3, tags={"help"}),
    "branch": Risk("branch", "branch", "a branch can hook a small thing back safely", "a branch", 2, 3, tags={"help"}),
}

GIRL_NAMES = ["Tess", "Mina", "Nora", "Lena", "Ivy"]
BOY_NAMES = ["Robin", "Pip", "Finn", "Milo", "Otis"]


@dataclass
class StoryParams:
    scene: str
    shiny: str
    risk: str
    rescue: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    bravery: int
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, scene in SCENES.items():
        for shy in SHINY:
            for rid, risk in RISKS.items():
                if can_fixate(SHINY[shy], scene) and risk_at_hand(SHINY[shy], risk):
                    combos.append((sid, shy, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like reflection and bravery storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--shiny", choices=SHINY)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--rescue", choices=GENTLE_HELP)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--bravery", type=int, choices=[0, 1, 2, 3])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.scene and args.shiny and not can_fixate(SHINY[args.shiny], SCENES[args.scene]):
        raise StoryError("That shiny thing would not plausibly hold the hero's attention there.")
    if args.risk and args.shiny and not risk_at_hand(SHINY[args.shiny], RISKS[args.risk]):
        raise StoryError("That risk would not fit the shiny thing and the place together.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.shiny is None or c[1] == args.shiny)
              and (args.risk is None or c[2] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, shiny, risk = rng.choice(sorted(combos))
    rescue = args.rescue or rng.choice(sorted(GENTLE_HELP))
    bravery = args.bravery if args.bravery is not None else rng.choice([1, 2, 3])
    hero_type = rng.choice(["rabbit", "fox", "lamb"])
    helper_type = rng.choice(["tortoise", "hen", "goat"])
    hero_name = args.hero_name or rng.choice(BOY_NAMES + GIRL_NAMES)
    helper_name = args.helper_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(scene, shiny, risk, rescue, hero_name, hero_type, helper_name, helper_type, bravery, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a small fable that includes the words "reflect" and "fixate".',
        f"Tell a bravery story where {f['hero'].label_word if False else f['hero'].label} "
        f"starts to fixate on something shiny by {f['scene'].place}, but a wise helper guides "
        f"the choice toward safety.",
        f"Write a child-friendly fable about a shiny thing near water, a warning, and a brave decision.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    scene = f["scene"]
    shiny = f["shiny"]
    risk = f["risk"]
    out = f["outcome"]
    answers = [
        QAItem("Who is the story about?", f"It is about {hero.label} and {helper.label}, two small animals in a fable-like scene. {hero.label} is the one who starts to fixate, and {helper.label} is the wiser friend."),
        QAItem("What did the hero fixate on?", f"{hero.label} fixate on {shiny.phrase}. The shine looked lovely because the water could reflect it back like a second little light."),
    ]
    if out == "brave":
        answers.append(QAItem(
            "How was the hero brave?",
            f"{hero.label} was brave by choosing not to grab the shiny thing too fast. {hero.label} listened, used a reed, and moved it away from the risky edge instead."
        ))
        answers.append(QAItem(
            "What changed by the end?",
            f"The shiny thing was safe on dry ground, and the hero was looking ahead instead of staring at it. The lesson of the fable was to choose the wise step when something beautiful tries to fixate your eyes."
        ))
    else:
        answers.append(QAItem(
            "What happened when the hero moved too quickly?",
            f"The bank gave a little slip and the shiny thing nearly went toward {risk.near}. The helper had to act fast so the trouble would not grow."
        ))
        answers.append(QAItem(
            "What did the helper do?",
            f"{helper.label} used a steady rescue and kept the danger small. That made the ending safe, even though the hero had started by fixating too long."
        ))
    answers.append(QAItem(
        "What is the moral of the story?",
        f"{scene.moral} In this world, bravery means you do not only look; you think, listen, and choose the safe way."
    ))
    return answers


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["shiny"].tags)
    tags |= set(world.facts["risk_cfg"].tags)
    out = []
    if "reflect" in tags:
        out.append(QAItem("What does it mean when water reflects something?", "It means the water shows a picture of the thing on its surface, like a soft mirror. That is why shiny things can look extra bright near a pond or stream."))
    out.append(QAItem("What is fixating?", "Fixating means staring at one thing so much that you forget to notice anything else. It can make a small problem feel bigger because your attention gets stuck."))
    out.append(QAItem("What is bravery?", "Bravery is doing the careful thing even when you feel drawn toward the risky thing. It is a calm kind of courage, not a noisy one."))
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_scene(S) :- scene(S).
valid_combo(S, Y, R) :- scene(S), shiny(Y), risk(R), can_fixate(Y, S), risk_at_hand(Y, R).
outcome(brave) :- bravery(B), bravery_min(M), B >= M, delay(0).
outcome(warned) :- bravery(B), bravery_min(M), B < M, delay(1).
outcome(late) :- delay(2).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for yid in SHINY:
        lines.append(asp.fact("shiny", yid))
    for rid in RISKS:
        lines.append(asp.fact("risk", rid))
    for gid in GENTLE_HELP:
        lines.append(asp.fact("rescue", gid))
    lines.append(asp.fact("bravery_min", BRAVERY_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("bravery", params.bravery), asp.fact("delay", params.delay)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    sample = generate(CURATED[0])
    if not sample.story:
        rc = 1
        print("MISMATCH: generation failed")
    try:
        _ = generate(resolve_params(argparse.Namespace(scene=None, shiny=None, risk=None, rescue=None, hero_name=None, helper_name=None, bravery=None, delay=None), random.Random(7)))
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    if rc == 0:
        print("OK: verification passed.")
    return rc


CURATED = [
    StoryParams("pond", "coin", "slip", "reed", "Robin", "rabbit", "Tess", "tortoise", 3, 0),
    StoryParams("well", "bell", "drop", "branch", "Pip", "fox", "Mina", "hen", 2, 1),
    StoryParams("stream", "feather", "spill", "branch", "Milo", "lamb", "Ivy", "goat", 1, 2),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SCENES[params.scene],
        SHINY[params.shiny],
        RISKS[params.risk],
        GENTLE_HELP[params.rescue],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        params.bravery,
        params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show valid_combo/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
