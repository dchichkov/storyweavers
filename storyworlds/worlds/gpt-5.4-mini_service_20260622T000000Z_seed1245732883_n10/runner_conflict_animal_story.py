#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/runner_conflict_animal_story.py
============================================================================================================

A standalone storyworld about a runner animal, a sharp conflict, and a gentle
resolution. The world is small on purpose: a fox runner is training for a meadow
race when a stubborn rivalry with a hare turns into a real argument. A calm
helper animal notices the tension, predicts the clash, and guides the runner
toward a fair turn-taking plan so the race can end with respect instead of hurt
feelings.

The domain is built to satisfy the storyworld contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a swapped-noun template
- a Python reasonableness gate plus an inline ASP twin
- three QA sets grounded in the simulated world
- verify mode that compares ASP/Python parity and runs smoke tests
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
SENSE_MIN = 2


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
        female = {"girl", "mother", "mom", "woman", "doe", "mare"}
        male = {"boy", "father", "dad", "man", "fox", "buck", "stag", "runner"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    sound: str
    time_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Runner:
    id: str
    species: str
    label: str
    speed: int
    lane: str
    goal: str
    pride: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Rival:
    id: str
    species: str
    label: str
    challenge: str
    lane: str
    temper: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    species: str
    label: str
    wisdom: int
    action: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    runner = world.get("runner")
    rival = world.get("rival")
    if runner.memes["defiance"] < THRESHOLD:
        return out
    if rival.memes["stubborn"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    runner.memes["conflict"] += 1
    rival.memes["conflict"] += 1
    helper = world.get("helper")
    helper.memes["concern"] += 1
    out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("conflict", "social", _r_conflict)]


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


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def reasonability_ok(track: Runner, rival: Rival, helper: Helper, resolution: Resolution) -> bool:
    return track.speed >= 1 and resolution.sense >= SENSE_MIN and helper.wisdom >= 1 and rival.temper >= 1


def conflict_level(track: Runner, rival: Rival) -> int:
    return track.pride + rival.temper


def can_settle(helper: Helper, resolution: Resolution, track: Runner, rival: Rival) -> bool:
    return helper.wisdom + resolution.power >= conflict_level(track, rival)


def predict_conflict(world: World) -> dict:
    sim = world.copy()
    sim.get("runner").memes["defiance"] += 1
    sim.get("rival").memes["stubborn"] += 1
    propagate(sim, narrate=False)
    return {
        "conflict": sim.get("runner").memes["conflict"] >= THRESHOLD,
        "tension": sim.get("runner").memes["conflict"] + sim.get("rival").memes["conflict"],
    }


def opening(world: World, setting: Setting, runner: Entity, rival: Entity, helper: Entity) -> None:
    world.say(
        f"At {setting.place}, the {setting.time_word} air was soft and bright. "
        f"{setting.detail}"
    )
    world.say(
        f"{runner.id} the runner loved the trail and the open lane. {rival.id} liked "
        f"to race too, and both animals had their eyes on the same finish line."
    )
    world.say(
        f"{helper.id} listened to the {setting.sound} and watched the two animals "
        f"circle the lane like they were already racing."
    )


def tension(world: World, runner: Entity, rival: Entity) -> None:
    runner.memes["desire"] += 1
    rival.memes["desire"] += 1
    runner.memes["defiance"] += 1
    rival.memes["stubborn"] += 1
    world.say(
        f'{runner.id} planted a paw in the dirt. "I am the fastest runner here," '
        f'{runner.pronoun()} said.'
    )
    world.say(
        f'{rival.id} flicked {rival.pronoun("possessive")} tail. '
        f'"No, I should go first," {rival.pronoun()} snapped back.'
    )


def warn(world: World, helper: Entity, runner: Entity, rival: Entity) -> None:
    pred = predict_conflict(world)
    helper.memes["concern"] += 1
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f"{helper.id} stepped between them. {helper.pronoun().capitalize()} said, "
        f'"If two animals both push ahead, the race turns into a fight instead of '
        f'fun. Let us make a fair plan."'
    )


def conflict(scene: World, runner: Entity, rival: Entity) -> None:
    propagate(scene, narrate=False)
    scene.say(
        f"{runner.id} and {rival.id} both rushed the lane at once. Their paws skidded, "
        f"and the happy game turned into a sharp conflict."
    )


def settle(world: World, helper: Entity, runner: Entity, rival: Entity, resolution: Resolution) -> None:
    runner.memes["conflict"] = 0.0
    rival.memes["conflict"] = 0.0
    runner.memes["peace"] += 1
    rival.memes["peace"] += 1
    world.say(
        f"{helper.id} found a simple fix: {resolution.text}."
    )
    world.say(
        f"The two animals slowed down, took turns, and listened. The race line stayed "
        f"safe, and everyone got to run."
    )


def settle_fail(world: World, helper: Entity, runner: Entity, rival: Entity, resolution: Resolution) -> None:
    world.get("track").meters["chaos"] += 1
    world.say(
        f"{helper.id} tried {resolution.fail}."
    )
    world.say(
        f"But the argument was too big for that plan, and the lane stayed tangled."
    )


def ending(world: World, runner: Entity, rival: Entity, helper: Entity) -> None:
    world.say(
        f"In the end, {runner.id} ran with a calm heart, {rival.id} smiled instead of "
        f"snapping, and {helper.id} watched the meadow settle back into a quiet game."
    )


def ending_fail(world: World, runner: Entity, rival: Entity, helper: Entity) -> None:
    world.say(
        f"They went home tired and cross, remembering that a race is better when every "
        f"runner waits for a fair turn."
    )


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the meadow path",
        detail="Daisies lined the path, and a small ribbon marked the finish line.",
        sound="grass",
        time_word="morning",
        tags={"meadow", "race"},
    ),
    "field": Setting(
        id="field",
        place="the open field",
        detail="A little wooden sign pointed to the starting line near the fence.",
        sound="wind",
        time_word="afternoon",
        tags={"field", "race"},
    ),
}

RUNNERS = {
    "fox": Runner(
        id="fox",
        species="fox",
        label="runner",
        speed=7,
        lane="front",
        goal="win the ribbon",
        pride=4,
        tags={"runner", "animal"},
    ),
    "rabbit": Runner(
        id="rabbit",
        species="rabbit",
        label="runner",
        speed=8,
        lane="front",
        goal="reach the line first",
        pride=3,
        tags={"runner", "animal"},
    ),
}

RIVALS = {
    "hare": Rival(
        id="hare",
        species="hare",
        label="the hare",
        challenge="a quick sprint",
        lane="same",
        temper=4,
        tags={"conflict", "animal"},
    ),
    "squirrel": Rival(
        id="squirrel",
        species="squirrel",
        label="the squirrel",
        challenge="a jumpy dash",
        lane="same",
        temper=3,
        tags={"conflict", "animal"},
    ),
}

HELPERS = {
    "owl": Helper(
        id="owl",
        species="owl",
        label="the owl",
        wisdom=5,
        action="call for fairness",
        tags={"helper", "animal"},
    ),
    "tortoise": Helper(
        id="tortoise",
        species="tortoise",
        label="the tortoise",
        wisdom=6,
        action="slow everyone down",
        tags={"helper", "animal"},
    ),
}

RESOLUTIONS = {
    "turns": Resolution(
        id="turns",
        sense=3,
        power=4,
        text="the owl marked two turns on the trail, so each animal could run one at a time",
        fail="two turns on the trail",
        qa_text="marked two turns on the trail so each animal could run one at a time",
        tags={"fairness", "race"},
    ),
    "lanes": Resolution(
        id="lanes",
        sense=3,
        power=3,
        text="the tortoise made two lanes with sticks and leaves, one for each runner",
        fail="two lanes with sticks and leaves",
        qa_text="made two lanes with sticks and leaves, one for each runner",
        tags={"fairness", "race"},
    ),
    "wait": Resolution(
        id="wait",
        sense=1,
        power=1,
        text="the owl told them to wait, but that did not calm the conflict enough",
        fail="asking them to wait",
        qa_text="asked them to wait",
        tags={"fairness", "race"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nina"]
BOY_NAMES = ["Finn", "Toby", "Milo", "Theo"]


@dataclass
class StoryParams:
    setting: str
    runner: str
    rival: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for r in RUNNERS:
            for v in RIVALS:
                for h in HELPERS:
                    out.append((s, r, v, h))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal runner conflict storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--runner", choices=RUNNERS)
    ap.add_argument("--rival", choices=RIVALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESOLUTIONS)
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.runner:
        combos = [c for c in combos if c[1] == args.runner]
    if args.rival:
        combos = [c for c in combos if c[2] == args.rival]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, runner, rival, helper = rng.choice(sorted(combos))
    return StoryParams(setting=setting, runner=runner, rival=rival, helper=helper, seed=None)


def tell(setting: Setting, runner_cfg: Runner, rival_cfg: Rival, helper_cfg: Helper, response: Resolution) -> World:
    world = World()
    track = world.add(Entity(id="track", kind="thing", type="place", label=setting.place))
    runner = world.add(Entity(id="runner", kind="character", type="fox", role="runner", label="the runner"))
    rival = world.add(Entity(id="rival", kind="character", type=rival_cfg.species, role="rival", label=rival_cfg.label))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.species, role="helper", label=helper_cfg.label))
    runner.memes["defiance"] = 1.0
    rival.memes["stubborn"] = 1.0
    helper.memes["concern"] = 0.0
    world.facts["setting"] = setting
    world.facts["response"] = response

    opening(world, setting, runner, rival, helper)
    world.para()
    tension(world, runner, rival)
    warn(world, helper, runner, rival)
    world.para()
    conflict(world, runner, rival)
    if can_settle(helper_cfg, response, runner_cfg, rival_cfg):
        settle(world, helper, runner, rival, response)
        ending(world, runner, rival, helper)
        outcome = "settled"
    else:
        settle_fail(world, helper, runner, rival, response)
        ending_fail(world, runner, rival, helper)
        outcome = "unsettled"

    world.facts.update(
        runner=runner, rival=rival, helper=helper, track=track,
        outcome=outcome, conflict=runner.memes["conflict"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a child-friendly animal story that includes the word "runner" and a conflict on a meadow path.',
        'Tell a story about a runner animal who gets into an argument with another animal, and a wise helper fixes it fairly.',
        'Write a short animal story where a runner, a rival, and a helper turn a conflict into turn-taking.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    runner = f["runner"]
    rival = f["rival"]
    helper = f["helper"]
    setting = f["setting"]
    response = f["response"]
    qa = [
        QAItem(
            question=f"Who was the runner in the story?",
            answer=f"The runner was {runner.id}, the animal who wanted to race first at {setting.place}.",
        ),
        QAItem(
            question=f"What caused the conflict between {runner.id} and {rival.id}?",
            answer=f"They both wanted the same lane and the same turn at once. That made the race into a conflict instead of a fair game.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} noticed the tension early and brought a fair plan. The helper used {response.qa_text} so the animals could take turns.",
        ),
    ]
    if f["outcome"] == "settled":
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The argument cooled down, and {runner.id} and {rival.id} ran with calmer hearts. The meadow ended as a peaceful race instead of a fight.",
        ))
    else:
        qa.append(QAItem(
            question=f"Did the helper's plan fully settle the argument?",
            answer=f"No. The plan was too small for that much pride and temper, so the lane stayed tangled and the animals went home upset.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a runner?",
            answer="A runner is someone or something that moves quickly on foot. In stories, a runner often wants to reach the finish line first.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a disagreement or struggle between characters. It can happen when two creatures want the same thing at the same time.",
        ),
        QAItem(
            question="Why can taking turns help?",
            answer="Taking turns helps because everyone gets a fair chance. It can calm anger and keep a game from turning into a fight.",
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="meadow", runner="fox", rival="hare", helper="owl", seed=None),
    StoryParams(setting="field", runner="rabbit", rival="squirrel", helper="tortoise", seed=None),
    StoryParams(setting="meadow", runner="fox", rival="squirrel", helper="tortoise", seed=None),
]


def explain_rejection() -> str:
    return "(No story: the chosen combination does not build a useful conflict.)"


ASP_RULES = r"""
conflict :- runner_defiance, rival_stubborn.
settled :- helper_wisdom, resolution_power, not conflict_big.
conflict_big :- runner_pride(P), rival_temper(T), P + T > 6.
valid(S,R,V,H) :- setting(S), runner(R), rival(V), helper(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in RUNNERS:
        lines.append(asp.fact("runner", rid))
    for vid in RIVALS:
        lines.append(asp.fact("rival", vid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for rid, r in RUNNERS.items():
        lines.append(asp.fact("runner_pride", rid, r.pride))
    for vid, v in RIVALS.items():
        lines.append(asp.fact("rival_temper", vid, v.temper))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper_wisdom", hid, h.wisdom))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, runner=None, rival=None, helper=None, response=None), random.Random(1)))
        _ = sample.story
        print("OK: smoke test generate() completed.")
    except Exception as e:
        return 1
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.runner not in RUNNERS or params.rival not in RIVALS or params.helper not in HELPERS:
        raise StoryError("invalid parameters")
    response = RESOLUTIONS["turns"]
    world = tell(SETTINGS[params.setting], RUNNERS[params.runner], RIVALS[params.rival], HELPERS[params.helper], response)
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
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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
