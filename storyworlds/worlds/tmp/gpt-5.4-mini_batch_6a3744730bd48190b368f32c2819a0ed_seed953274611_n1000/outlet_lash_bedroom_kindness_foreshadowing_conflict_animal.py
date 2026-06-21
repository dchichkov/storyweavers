#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/outlet_lash_bedroom_kindness_foreshadowing_conflict_animal.py
=============================================================================================

A small animal story world set in a bedroom.

Premise:
- A curious pet or stuffed-animal-like creature plays in a bedroom.
- An outlet is an unsafe thing to poke near.
- A lash (tail lash / whisker lash / strap lash) can nudge trouble closer.
- Kindness, foreshadowing, and conflict shape the turn and ending.

The world is intentionally tiny and classical: a few typed entities, stateful
meters/memes, a forward causal turn, and a gentle resolution.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "animal"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    dark_corner: str
    has_outlet: bool = True


@dataclass
class Animal:
    id: str
    species: str
    label: str
    personality: str
    noise: str
    tail_motion: str
    type: str = "animal"
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Lash:
    id: str
    label: str
    kind: str
    motion: str
    brushes: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    touch: str
    spark: str
    danger: str
    can_shock: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    action: str
    comfort: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_warn(world: World) -> list[str]:
    out: list[str] = []
    animal = world.entities.get("animal")
    lash = world.entities.get("lash")
    risk = world.entities.get("risk")
    if not animal or not lash or not risk:
        return out
    if animal.meters["near_outlet"] >= THRESHOLD and lash.meters["swish"] >= THRESHOLD:
        sig = ("warn",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("risk").meters["sparked"] += 1
        world.get("animal").memes["unease"] += 1
        out.append("A tiny spark of trouble seemed ready to happen.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.get("animal").memes["stubborn"] < THRESHOLD:
        return out
    if world.get("helper").memes["kindness"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("animal").memes["conflict"] += 1
    world.get("helper").memes["conflict"] += 1
    out.append("__conflict__")
    return out


RULES = [Rule("warn", _r_warn), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def outlet_risk(animal: Animal, lash: Lash, risk: Risk) -> bool:
    return animal.id == "animal" and lash.id == "lash" and risk.can_shock


def gentle_fix(helper: Helper, risk: Risk) -> bool:
    return helper.kindness_power >= 2 and risk.can_shock


def predict(world: World) -> dict:
    sim = world.copy()
    sim.get("animal").meters["near_outlet"] += 1
    sim.get("lash").meters["swish"] += 1
    propagate(sim, narrate=False)
    return {
        "sparked": sim.get("risk").meters["sparked"] >= THRESHOLD,
        "conflict": sim.get("animal").memes["conflict"] >= THRESHOLD,
    }


def start_scene(world: World, animal: Animal, helper: Helper, setting: Setting) -> None:
    animal.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"In the {setting.place}, {animal.id} padded around the bedroom and "
        f"{animal.noise.lower()}-ed at the soft, sleepy room."
    )
    world.say(
        f"{animal.id} liked the bed, the rug, and the warm corner by the window."
    )


def foreshadow(world: World, animal: Animal, risk: Risk, lash: Lash) -> None:
    animal.memes["curiosity"] += 1
    world.say(
        f"Near the wall, the outlet sat quietly by the floor. "
        f"{lash.label.capitalize()} kept brushing close, and {animal.id} noticed "
        f"that the corner did not like being crowded."
    )
    world.say(
        f"{animal.id}'s {animal.tail_motion} made the air feel busy, as if the room "
        f"was waiting to cough a warning."
    )


def conflict(world: World, animal: Animal, helper: Helper, lash: Lash, risk: Risk) -> None:
    animal.meters["near_outlet"] += 1
    lash.meters["swish"] += 1
    animal.memes["stubborn"] += 1
    helper.memes["care"] += 1
    world.say(
        f'"I want to play here," {animal.id} said, lashing {animal.pronoun("possessive")} '
        f'tail again beside the outlet.'
    )
    world.say(
        f'"No, little one," {helper.id} said softly. "That spot can bite with a shock."'
    )
    propagate(world, narrate=True)


def kindness_turn(world: World, animal: Animal, helper: Helper, safe: Helper) -> None:
    animal.memes["conflict"] = 0
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} did not scold. Instead, {helper.id} scooped up the toy and "
        f"moved it to the bed."
    )
    world.say(
        f'"Come here," {helper.id} said gently. "We can play somewhere safe."'
    )
    world.say(
        f"{animal.id} blinked, then curled up close and let the worried feeling fade."
    )


def ending(world: World, animal: Animal, helper: Helper, safe: Helper) -> None:
    animal.memes["relief"] += 1
    animal.memes["joy"] += 1
    world.say(
        f"At last, {animal.id} played on the rug with {safe.label}, "
        f"far from the outlet."
    )
    world.say(
        f"{helper.id} laughed, and {animal.id}'s {animal.tail_motion} now looked playful "
        f"instead of risky."
    )
    world.say(
        f"The bedroom stayed calm, and the little animal learned that kindness could "
        f"move a game away from danger."
    )


def tell(setting: Setting, animal_cfg: Animal, lash: Lash, risk: Risk, helper_cfg: Helper) -> World:
    world = World(setting)
    animal = world.add(Entity(id="animal", kind="character", type=animal_cfg.species, label=animal_cfg.label, role="main"))
    helper = world.add(Entity(id="helper", kind="character", type="cat" if helper_cfg.kind == "cat" else "animal", label=helper_cfg.label, role="helper"))
    safe = world.add(Entity(id="safe", kind="thing", type="toy", label=helper_cfg.action))
    risk_ent = world.add(Entity(id="risk", kind="thing", type="outlet", label=risk.label))
    lash_ent = world.add(Entity(id="lash", kind="thing", type="lash", label=lash.label))
    animal.memes["stubborn"] = 1
    helper.memes["kindness"] = helper_cfg.kindness_power
    world.facts["animal"] = animal
    world.facts["helper"] = helper
    world.facts["lash"] = lash_ent
    world.facts["risk"] = risk_ent
    world.facts["safe"] = safe
    start_scene(world, animal_cfg, helper_cfg, setting)
    world.para()
    foreshadow(world, animal_cfg, risk, lash)
    world.para()
    if not outlet_risk(animal_cfg, lash, risk):
        raise StoryError("This scene needs a real outlet-risk pair.")
    pred = predict(world)
    world.facts["predicted"] = pred
    conflict(world, animal_cfg, helper_cfg, lash, risk)
    world.para()
    kindness_turn(world, animal_cfg, helper_cfg, safe)
    world.para()
    ending(world, animal_cfg, helper_cfg, safe)
    world.facts["outcome"] = "resolved"
    return world


SETTINGS = {
    "bedroom": Setting(id="bedroom", place="the bedroom", dark_corner="the outlet by the bed"),
}

ANIMALS = {
    "kitten": Animal(id="kitten", species="cat", label="kitten", personality="curious", noise="Purr"),
    "puppy": Animal(id="puppy", species="dog", label="puppy", personality="bouncy", noise="Woof"),
    "bunny": Animal(id="bunny", species="rabbit", label="bunny", personality="gentle", noise="Hop"),
}

LASHES = {
    "tail": Lash(id="tail", label="tail", kind="tail", motion="tail lash", brushes="lashes"),
    "whisker": Lash(id="whisker", label="whiskers", kind="whisker", motion="whisker twitch", brushes="twitch"),
    "strap": Lash(id="strap", label="a dangling strap", kind="strap", motion="strap lash", brushes="swings"),
}

RISKS = {
    "outlet": Risk(id="outlet", label="outlet", touch="touch", spark="spark", danger="shock"),
}

HELPERS = {
    "kind_cat": Helper(id="kind_cat", label="a kind cat", kind="cat", action="soft ball", comfort="safe play", tags={"kindness"}),
    "gentle_bird": Helper(id="gentle_bird", label="a gentle bird", kind="bird", action="feather toy", comfort="safe play", tags={"kindness"}),
}

HELPERS["kind_cat"].kindness_power = 2  # type: ignore[attr-defined]
HELPERS["gentle_bird"].kindness_power = 2  # type: ignore[attr-defined]


@dataclass
class StoryParams:
    setting: str
    animal: str
    lash: str
    risk: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ANIMALS:
            for l in LASHES:
                for r in RISKS:
                    if outlet_risk(ANIMALS[a], LASHES[l], RISKS[r]):
                        combos.append((s, a, l, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world in a bedroom with an outlet, a lash, kindness, foreshadowing, and conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--lash", choices=LASHES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
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
              and (args.animal is None or c[1] == args.animal)
              and (args.lash is None or c[2] == args.lash)
              and (args.risk is None or c[3] == args.risk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, animal, lash, risk = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, animal=animal, lash=lash, risk=risk, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story set in a bedroom that includes the words "outlet" and "lash".',
        f"Tell a bedtime-style animal story where {f['animal'].id} gets too close to the outlet, but kindness helps move the play away.",
        f"Write a small story with foreshadowing, conflict, and kindness in a bedroom, centered on an outlet and a lash.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["animal"]
    h = world.facts["helper"]
    return [
        QAItem(question=f"What room is the story set in?", answer="It is set in a bedroom, where the outlet is part of the room's furniture and wiring."),
        QAItem(question=f"What warning did the helper give {a.id}?", answer=f"{h.id} warned that the outlet could give a shock. That is why the helper moved the game away instead of letting the animal keep lashing near it."),
        QAItem(question="How did the problem get solved?", answer="The helper responded with kindness and moved the play to a safer spot. That changed the conflict into a calm ending, and the bedroom stayed peaceful."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is an outlet?", answer="An outlet is a place on the wall where electricity comes out for cords and plugs. People should keep fingers and toys away from it."),
        QAItem(question="What does kindness mean in a story?", answer="Kindness means helping gently, without being mean or scary. In a story, it often helps someone calm down and choose a safer way."),
        QAItem(question="What is foreshadowing?", answer="Foreshadowing is a little hint that trouble may come later. It makes the reader notice a warning before the big moment arrives."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(setting,animal,lash,risk) :- setting(setting), animal(animal), lash(lash), risk(risk), outlet_risk(animal,lash,risk).
resolved :- valid(setting,animal,lash,risk).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for l in LASHES:
        lines.append(asp.fact("lash", l))
    for r in RISKS:
        lines.append(asp.fact("risk", r))
        lines.append(asp.fact("outlet_risk", "kitten", "tail", "outlet"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and python valid_combos()")
        return 1
    try:
        p = StoryParams(setting="bedroom", animal="kitten", lash="tail", risk="outlet", helper="kind_cat")
        with redirect_stdout(io.StringIO()):
            sample = generate(p)
            emit(sample)
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: ASP parity and story-generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    for table, key in [(SETTINGS, params.setting), (ANIMALS, params.animal), (LASHES, params.lash), (RISKS, params.risk), (HELPERS, params.helper)]:
        if key not in table:
            raise StoryError(f"Unknown choice: {key}")
    setting = SETTINGS[params.setting]
    animal_cfg = ANIMALS[params.animal]
    lash = LASHES[params.lash]
    risk = RISKS[params.risk]
    helper = HELPERS[params.helper]
    if not outlet_risk(animal_cfg, lash, risk):
        raise StoryError("This story needs a real outlet-and-lash risk.")
    world = tell(setting, animal_cfg, lash, risk, helper)
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
    StoryParams(setting="bedroom", animal="kitten", lash="tail", risk="outlet", helper="kind_cat"),
    StoryParams(setting="bedroom", animal="puppy", lash="whisker", risk="outlet", helper="gentle_bird"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
