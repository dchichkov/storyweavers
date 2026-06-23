#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10/bog_aspirin_sound_effects_inner_monologue_dialogue.py
==============================================================================================================================

A small fairy-tale story world about a child, a bog, and a careful remedy.
The world uses typed entities with physical meters and emotional memes, a tiny
forward-causal simulation, a reasonableness gate, inline ASP rules, and three
Q&A sets grounded in the generated world state.

The required narrative instruments are woven into the prose:
- Sound Effects
- Inner Monologue
- Dialogue

Required seed words:
- bog
- aspirin
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
SOUND_EFFECTS = {"splish", "splash", "plop", "slosh"}
MOODS = {"worry", "relief", "joy", "care"}
VALID_ACHES = {"ankle", "foot", "knee"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    name: str
    mood: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    symptom: str
    mess: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    effect: str
    safe_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    hazard: str
    remedy: str
    hero: str
    hero_type: str
    parent_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["bog"] < THRESHOLD:
        return out
    sig = ("soak", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["mud"] += 1
    hero.memes["worry"] += 1
    out.append("The bog left mud on the hero's shoes.")
    return out


def _r_ache(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["mud"] < THRESHOLD:
        return out
    sig = ("ache", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["ache"] += 1
    hero.memes["worry"] += 1
    out.append("The long, wet walk made the ankle ache.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    parent = world.get("parent")
    remedy = world.get("remedy")
    if hero.meters["ache"] < THRESHOLD or remedy.meters["taken"] < THRESHOLD:
        return out
    sig = ("relief", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["ache"] = 0.0
    hero.memes["relief"] += 1
    parent.memes["care"] += 1
    out.append("The aspirin helped the ache fade.")
    return out


CAUSAL_RULES = [Rule("soak", _r_soak), Rule("ache", _r_ache), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def bog_at_risk(hazard: Hazard, setting: Setting) -> bool:
    return "bog" in setting.affords and "bog" in hazard.requires


def remedy_fits(hazard: Hazard, remedy: Remedy) -> bool:
    return hazard.id in remedy.safe_for


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for hid, hazard in HAZARDS.items():
            if not bog_at_risk(hazard, setting):
                continue
            for rid, remedy in REMEDIES.items():
                if remedy_fits(hazard, remedy):
                    out.append((sid, hid, rid))
    return out


def explain_rejection(hazard: Hazard, remedy: Remedy) -> str:
    return f"(No story: {remedy.label} does not sensibly fit the problem of {hazard.label}.)"


def explain_setting(setting: Setting) -> str:
    return f"(No story: this setting does not include the bog needed for the tale.)"


def _do_bog(world: World, hero: Entity) -> None:
    hero.meters["bog"] += 1
    hero.memes["worry"] += 1
    propagate(world, narrate=True)


def take_remedy(world: World, hero: Entity, remedy: Entity) -> None:
    remedy.meters["taken"] += 1
    propagate(world, narrate=True)


def tell_beth(world: World, hero: Entity, parent: Entity, hazard: Hazard) -> None:
    world.say(f'The {parent.label} said, "Stay on the stones, dear one. The {hazard.label} is sticky today."')


def inner_monologue(world: World, hero: Entity, hazard: Hazard) -> None:
    world.say(f'[{hero.name if hasattr(hero, "name") else hero.id} thought: "Oh dear, the {hazard.label} is tugging at my boots."]')


def sound_effect(world: World, effect: str) -> None:
    world.say(f"[{effect.upper()}]")


def dialogue_with_helper(world: World, hero: Entity, helper: Entity, remedy: Remedy) -> None:
    world.say(f'"I have an idea," said the {helper.label}. "A little {remedy.label} may help the ache."')
    world.say(f'"Thank you," whispered {hero.id}. "I will try to be brave and careful."')


def resolve_story(world: World, hero: Entity, parent: Entity, helper: Entity, hazard: Hazard, remedy: Remedy) -> None:
    world.para()
    take_remedy(world, hero, world.get("remedy"))
    dialogue_with_helper(world, hero, helper, remedy)
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    parent.memes["care"] += 1
    world.say(f"In the end, the hero crossed the little bridge, the bog stayed behind, and the morning looked gold again.")


def tell(setting: Setting, hazard: Hazard, remedy: Remedy, hero_name: str, hero_type: str, parent_type: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="mother" if parent_type == "mother" else "father"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label="fairy doctor"))
    bog = world.add(Entity(id="bog", kind="thing", type="bog", label="the bog"))
    rem = world.add(Entity(id="remedy", kind="thing", type="remedy", label=remedy.label, phrase=remedy.phrase))
    world.facts.update(hero=hero, parent=parent, helper=helper, hazard=hazard, remedy=rem, setting=setting)

    world.say(f"Once in a fairy-tale lane, {hero.id} walked by {setting.detail}.")
    world.say(f"The air felt {setting.mood}, and the path wound toward {bog.label}.")
    world.say(f"{hero.id} wanted to cross, but the mud was deep and the reeds whispered like old lace.")
    sound_effect(world, "splish")
    inner_monologue(world, hero, hazard)
    tell_beth(world, hero, parent, hazard)

    world.para()
    _do_bog(world, hero)
    world.say(f"{hero.id}'s boot went {random.choice(sorted(SOUND_EFFECTS))}, and a little ache began in the ankle.")
    world.say(f"The helper stepped closer and nodded toward the small bottle of aspirin.")
    dialogue_with_helper(world, hero, helper, remedy)
    world.say(f"The aspirin was for the {hazard.symptom}, not for magic, and it made the ache soften at last.")

    world.para()
    resolve_story(world, hero, parent, helper, hazard, remedy)
    return world


SETTINGS = {
    "lantern_lane": Setting(name="lantern lane", mood="soft and bright", detail="a lane of mossy stones beside a sleepy bog", affords={"bog"}),
    "willow_walk": Setting(name="willow walk", mood="misty and kind", detail="a willow path that skirted the bog and glittered after rain", affords={"bog"}),
    "rose_road": Setting(name="rose road", mood="gentle and warm", detail="a little road that passed the bog and a small bridge", affords={"bog"}),
}

HAZARDS = {
    "bog_ache": Hazard(id="bog_ache", label="bog", symptom="ache", mess="mud", requires={"bog"}, tags={"bog", "mud"}),
}

REMEDIES = {
    "aspirin": Remedy(id="aspirin", label="aspirin", phrase="a tiny spoonful of aspirin", effect="ease the ache", safe_for={"bog_ache"}, tags={"aspirin", "medicine"}),
}

GIRL_NAMES = ["Ava", "Mina", "Luna", "Etta", "Nora"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Pip", "Robin"]
TRAITS = ["gentle", "curious", "brave", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a fairy tale that includes the words "bog" and "aspirin", with sound effects and a kindly ending.',
        f'Write a small fairy story about {hero.label} who gets a muddy ache in the bog and hears about aspirin.',
        f'Tell a gentle story in which a child crosses a bog, thinks aloud, and talks with a helper about aspirin.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    helper = f["helper"]
    hazard = f["hazard"]
    remedy = f["remedy"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Where did {hero.label} walk at the start of the story?",
            answer=f"{hero.label} walked beside the bog on {setting.detail}. The path was quiet at first, which made the danger easy to miss.",
        ),
        QAItem(
            question=f"What did {hero.label} think while stepping into the muddy bog?",
            answer=f"{hero.label} worried that the boots were sinking and that the walk felt too slippery. The little inner voice showed the fear before the ache grew stronger.",
        ),
        QAItem(
            question=f"Who talked about aspirin with {hero.label}?",
            answer=f"The fairy doctor talked about aspirin with {hero.label}. That helper brought calm words and a careful plan for the ache.",
        ),
    ]
    if world.get("hero").meters["ache"] < THRESHOLD:
        qa.append(QAItem(
            question=f"Why did the aspirin help {hero.label}?",
            answer=f"The aspirin helped because the bog left {hero.label} with a sore ankle. Once the medicine was taken, the ache softened and the child could walk on more easily.",
        ))
    else:
        qa.append(QAItem(
            question=f"Why did {parent.label} stay gentle when the bog walk was hard?",
            answer=f"{parent.label} stayed gentle because the mud made the child worry and ache. The parent wanted the story to end safely, with comfort instead of fuss.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bog?", answer="A bog is a wet, muddy place where the ground feels soft and slippery."),
        QAItem(question="What is aspirin?", answer="Aspirin is a medicine some grown-ups use to help ease pain or an ache."),
        QAItem(question="Why do sound effects help a story?", answer="Sound effects help you hear the action in your imagination, so the scene feels lively and close."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world knowledge q&a ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
bogged(H) :- hears(H, bog), steps_in(H, bog).
aches(H) :- bogged(H).
relieved(H) :- takes(H, aspirin), aches(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affords", sid, "bog"))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("requires", hid, "bog"))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("safe_for", rid, "bog_ache"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("MISMATCH: ASP and Python combos differ")
        if py - asp_set:
            print("  only python:", sorted(py - asp_set))
        if asp_set - py:
            print("  only asp:", sorted(asp_set - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, remedy=None, hero=None, hero_type=None, parent_type=None, helper_type=None, seed=None), random.Random(777)))
        _ = sample.story
    except Exception as err:
        ok = False
        print(f"SMOKE TEST FAILED: {err}")
    if ok:
        print(f"OK: {len(py)} valid combos and generate smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about a bog and aspirin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--helper-type", choices=["fairy", "woman", "man"])
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
              and (args.hazard is None or c[1] == args.hazard)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, remedy = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    helper_type = args.helper_type or "fairy"
    return StoryParams(setting=setting, hazard=hazard, remedy=remedy, hero=hero, hero_type=hero_type, parent_type=parent_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hazard not in HAZARDS or params.remedy not in REMEDIES:
        raise StoryError("Invalid parameters.")
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], REMEDIES[params.remedy], params.hero, params.hero_type, params.parent_type, params.helper_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting=s, hazard=h, remedy=r, hero="Ava", hero_type="girl", parent_type="mother", helper_type="fairy")) for s, h, r in valid_combos()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
