#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thigh_twist_sound_effects_bad_ending_adventure.py
==================================================================================

A small Adventure-flavored story world about a child on a quest, a dangerous
twist, loud sound effects, and a bad ending that still feels complete and
child-facing.

Premise:
- A child and a helper follow an adventurous trail to reach a hidden prize.
- The trail is narrow, rocky, and fun to imagine, but one risky step can hurt.
- A twist at the wrong moment causes a thigh injury, an alarm, and a bad ending.

This file is standalone and uses only the stdlib plus the shared Storyweavers
result containers. It also includes an inline ASP twin for the basic reason-
ableness gate and ending model.

Run:
    python storyworlds/worlds/gpt-5.4-mini/thigh_twist_sound_effects_bad_ending_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/thigh_twist_sound_effects_bad_ending_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/thigh_twist_sound_effects_bad_ending_adventure.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/thigh_twist_sound_effects_bad_ending_adventure.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Route:
    id: str
    scene: str
    trail: str
    prize: str
    twist_spot: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    title: str
    sound: str
    step: str
    risk: str
    effect: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Cure:
    id: str
    title: str
    sound: str
    method: str
    power: int
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
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_pain(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["twisted_thigh"] < THRESHOLD:
        return out
    sig = ("pain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["hurt"] += 1
    out.append("__pain__")
    return out


def _r_stop(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if hero.meters["twisted_thigh"] < THRESHOLD:
        return out
    sig = ("stop",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["alarm"] += 1
    out.append("__stop__")
    return out


CAUSAL_RULES = [Rule("pain", _r_pain), Rule("stop", _r_stop)]


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


def reasonableness(action: Action, route: Route) -> bool:
    return action.power >= 1 and "adventure" in route.tags


def predict_twist(world: World, action: Action) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["twisted_thigh"] += 1
    propagate(sim, narrate=False)
    return {"injured": sim.get("hero").meters["twisted_thigh"] >= THRESHOLD}


def story_setup(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    hero.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {helper.id} set out on an adventure. "
        f"{route.scene}"
    )
    world.say(
        f"They followed {route.trail} and hunted for {route.prize}, laughing each time "
        f"the path made a new turn."
    )


def approach_twist(world: World, hero: Entity, route: Route) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"Near {route.twist_spot}, {hero.id} slowed down. The stones were slick, and "
        f"the trail bent in a tricky twist."
    )


def sound_effect(world: World, action: Action) -> None:
    world.say(action.sound)
    world.say(
        f"{action.step}, but the trail gave a nasty little twist. {action.effect}"
    )


def injure(world: World, hero: Entity) -> None:
    hero.meters["twisted_thigh"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} yelped and clutched {hero.pronoun('possessive')} thigh. "
        f"The twist had hit hard."
    )


def alarm(world: World, helper: Entity, hero: Entity) -> None:
    world.say(
        f'"{hero.id}!" {helper.id} shouted. "{helper.label_word.capitalize()} says stop!"'
    )
    world.say("Tap-tap-tap went quick feet on the rocks as the adventure froze in place.")
    world.say("They listened to the echo and knew something had gone wrong.")


def bad_ending(world: World, hero: Entity, helper: Entity, route: Route) -> None:
    hero.memes["sad"] += 1
    helper.memes["sad"] += 1
    world.say(
        f"No treasure was worth another step. The day ended with {hero.id} sitting "
        f"on a stone and {helper.id} holding {hero.id}'s hand."
    )
    world.say(
        f"The path to {route.prize} stayed hidden, and the last thing they heard was "
        f"the wind whispering through the rocks."
    )
    world.say(route.ending_image)


def tell(route: Route, action: Action, cure: Cure, hero_name: str, helper_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl", role="helper", label="the guide"))
    world.add(Entity(id="trail", type="place", label=route.trail))
    story_setup(world, hero, helper, route)
    world.para()
    approach_twist(world, hero, route)

    pred = predict_twist(world, action)
    world.facts["predicted_injury"] = pred["injured"]

    world.para()
    sound_effect(world, action)
    injure(world, hero)
    alarm(world, helper, hero)

    world.para()
    world.say(
        f"{helper.id} tried the {cure.title}, but it was too late to undo the twist."
    )
    world.say(f"{cure.sound} {cure.method}.")
    bad_ending(world, hero, helper, route)

    world.facts.update(hero=hero, helper=helper, route=route, action=action, cure=cure)
    return world


ROUTES = {
    "canyon": Route(
        id="canyon",
        scene="The canyon walls glowed gold, and the old trail looked like a secret map.",
        trail="a narrow ridge above the creek",
        prize="the blue cave shell",
        twist_spot="the crook in the ridge",
        ending_image="By sunset, the ridge was empty, and the shell still waited in the dark cave.",
        tags={"adventure", "canyon"},
    ),
    "forest": Route(
        id="forest",
        scene="Tall pines leaned over the path, and every branch seemed to point forward.",
        trail="a mossy lane between roots",
        prize="the silver key",
        twist_spot="the root knot by the ravine",
        ending_image="When evening came, the key stayed hidden, and only the owls kept watch.",
        tags={"adventure", "forest"},
    ),
    "island": Route(
        id="island",
        scene="The tide flashed at the shore, and a windy trail led toward a lonely hill.",
        trail="a shell-strewn cliff path",
        prize="the red flag",
        twist_spot="the steep bend above the surf",
        ending_image="At dusk, the surf kept rolling, and the flag was never reached.",
        tags={"adventure", "island"},
    ),
}

ACTIONS = {
    "twist": Action(
        id="twist",
        title="twist",
        sound="CRACK!",
        step="One step slipped, then another",
        risk="A quick twist can hurt a leg if the body turns the wrong way",
        effect="The hero's thigh jerked and the whole leg went numb for a breath",
        power=1,
        tags={"twist", "sound_effects"},
    ),
    "snap": Action(
        id="snap",
        title="snap",
        sound="SNAP!",
        step="The foot caught on a root",
        risk="A snap in the trail can make the body wrench sideways",
        effect="The hero's thigh felt like it had been pinched by the mountain itself",
        power=1,
        tags={"twist", "sound_effects"},
    ),
}

CURES = {
    "bandage": Cure(
        id="bandage",
        title="bandage",
        sound="Rustle!",
        method="She wrapped the thigh with cloth and steadied the hero against a rock",
        power=1,
        tags={"bad_ending"},
    ),
    "rest": Cure(
        id="rest",
        title="rest",
        sound="Hush!",
        method="He sat still and breathed carefully, but the ache still stayed",
        power=1,
        tags={"bad_ending"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Finn", "Theo", "Ben", "Max", "Eli"]


@dataclass
class StoryParams:
    route: str
    action: str
    cure: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rid in ROUTES:
        for aid in ACTIONS:
            for cid in CURES:
                if reasonableness(ACTIONS[aid], ROUTES[rid]):
                    combos.append((rid, aid, cid))
    return combos


KNOWLEDGE = {
    "twist": [("What is a twist?", "A twist is a quick turning motion. In a story, a bad twist can make someone stumble or get hurt.")],
    "thigh": [("Where is your thigh?", "Your thigh is the upper part of your leg, between your hip and your knee.")],
    "sound_effects": [("What are sound effects?", "Sound effects are words that imitate noises, like CRACK or SNAP, so a story feels lively.")],
    "adventure": [("What makes a story an adventure?", "An adventure has a journey, a goal, and a little danger or surprise along the way.")],
    "bad_ending": [("What is a bad ending?", "A bad ending is when the problem does not get fixed and the story ends sadly or with a loss.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route: Route = f["route"]
    action: Action = f["action"]
    return [
        f'Write an adventure story that includes the word "{world.get("hero").id}"? No, include the word "thigh" and a loud twist sound like {action.sound}.',
        f"Tell a child-sized adventure where a tricky twist on {route.trail} hurts a thigh and the ending stays bad.",
        f'Write a story with sound effects, a twist, and a bad ending set near {route.prize}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    route: Route = f["route"]
    action: Action = f["action"]
    cure: Cure = f["cure"]
    return [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} and {helper.id} went together. They followed the trail as a team and hoped to find {route.prize}.",
        ),
        QAItem(
            question="What went wrong?",
            answer=f"A twist on the trail hurt {hero.id}'s thigh. The path was narrow and the turn came at the worst moment.",
        ),
        QAItem(
            question="Why did the story end badly?",
            answer=f"The injury stopped the quest before they could reach {route.prize}. Even though {cure.title} was tried, it was too late to turn the ending around.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["route"].tags) | set(world.facts["action"].tags) | set(world.facts["cure"].tags)
    out: list[QAItem] = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            for q, a in items:
                out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="canyon", action="twist", cure="bandage", hero_name="Finn", helper_name="Mina"),
    StoryParams(route="forest", action="snap", cure="rest", hero_name="Theo", helper_name="Lila"),
    StoryParams(route="island", action="twist", cure="bandage", hero_name="Ben", helper_name="Ava"),
]


def explain_rejection(route: Route, action: Action) -> str:
    return f"(No story: the route {route.id} is not adventurous enough for the action {action.id}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROUTES:
        lines.append(asp.fact("route", rid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("power", aid, a.power))
    for cid in CURES:
        lines.append(asp.fact("cure", cid))
    lines.append(asp.fact("threshold", THRESHOLD))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,A,C) :- route(R), action(A), cure(C), power(A,P), threshold(T), P >= T.
injured :- chosen_action(A), power(A,P), P >= 1.
bad_ending :- injured.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP and Python gate match.")
    else:
        print("MISMATCH: ASP and Python gate differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(route=None, action=None, cure=None, seed=None), random.Random(1)))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure story world with a twist, sound effects, and a bad ending.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--cure", choices=CURES)
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
              if (args.route is None or c[0] == args.route)
              and (args.action is None or c[1] == args.action)
              and (args.cure is None or c[2] == args.cure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    route, action, cure = rng.choice(sorted(combos))
    hero_name = rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_name = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    return StoryParams(route=route, action=action, cure=cure, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES or params.action not in ACTIONS or params.cure not in CURES:
        raise StoryError("Invalid parameters for this story world.")
    world = tell(ROUTES[params.route], ACTIONS[params.action], CURES[params.cure], params.hero_name, params.helper_name)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
            try:
                params = resolve_params(args, random.Random(base_seed + i))
                params.seed = base_seed + i
                sample = generate(params)
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
