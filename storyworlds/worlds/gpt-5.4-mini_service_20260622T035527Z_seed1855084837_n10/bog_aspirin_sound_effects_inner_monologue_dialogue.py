#!/usr/bin/env python3
"""
storyworlds/worlds/bog_aspirin_sound_effects_inner_monologue_dialogue.py
=======================================================================

A small fairy-tale storyworld about a child crossing a bog, a stubborn ache,
and a tiny aspirin that helps bring the day back to safety.

The premise is simple: the heroine goes into a misty bog to fetch a needed
herb, gets chilled and headachy, listens to a warning, and uses the medicine
she was given in a careful, grown-up way before the journey home. The story
uses sound effects, inner monologue, and dialogue, while keeping the prose
child-facing and concrete.

Words required by the seed: bog, aspirin.
Features required by the seed: Sound Effects, Inner Monologue, Dialogue.
Style required by the seed: Fairy Tale.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "sister"}
        male = {"boy", "father", "dad", "man", "king", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str
    task: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    task_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    sound: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "willow_bog": Setting(
        id="willow_bog",
        place="the willow bog",
        detail="Silver reeds swayed beside black water, and the mist curled low over the moss.",
        task_hint="moonwort",
        tags={"bog", "mist", "willow"},
    ),
    "moss_bog": Setting(
        id="moss_bog",
        place="the moss bog",
        detail="Soft moss made little islands, and round puddles shone like mirrors.",
        task_hint="starfern",
        tags={"bog", "moss", "puddle"},
    ),
}

TASKS = {
    "herb": Task(
        id="herb",
        verb="gather the moonwort",
        noun="moonwort",
        sound="squelch",
        risk="chilly and headachy",
        tags={"herb", "plant"},
    ),
    "lantern_oil": Task(
        id="lantern_oil",
        verb="carry the lantern oil home",
        noun="lantern oil",
        sound="plip",
        risk="slippery",
        tags={"oil", "carry"},
    ),
}

REMEDIES = {
    "aspirin": Remedy(
        id="aspirin",
        label="aspirin",
        phrase="a tiny aspirin",
        effect="calmed the ache",
        tags={"aspirin", "medicine"},
    )
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Rosa", "Nia", "Lily"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Jasper", "Theo", "Eli"]
TRAITS = ["brave", "gentle", "curious", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, tid) for sid in SETTINGS for tid in TASKS if sid == "willow_bog" or tid == "herb"]


@dataclass
class Rule:
    name: str
    apply: Any


class WorldRules:
    @staticmethod
    def ache(world: World) -> list[str]:
        out: list[str] = []
        hero = world.get("hero")
        if hero.memes["cold"] < THRESHOLD or hero.memes["strain"] < THRESHOLD:
            return out
        sig = ("ache", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.meters["ache"] += 1
        out.append("Her temples throbbed.")
        return out

    @staticmethod
    def relief(world: World) -> list[str]:
        out: list[str] = []
        hero = world.get("hero")
        if hero.meters["ache"] < THRESHOLD or world.facts.get("aspirin_taken") is not True:
            return out
        sig = ("relief", hero.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["relief"] += 1
        hero.meters["ache"] = 0
        out.append("The ache eased at last.")
        return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (WorldRules.ache, WorldRules.relief):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child in a bog, a bad ache, and a careful aspirin."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, name=name, gender=gender, elder=elder, trait=trait)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=[params.trait], attrs={"setting": params.setting}))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder, label=params.elder))
    remedy = world.add(Entity(id="aspirin", type="medicine", label="aspirin", phrase="a tiny aspirin", tags={"aspirin"}))
    place = SETTINGS[params.setting]
    task = TASKS[params.task]

    world.facts.update(hero=hero, elder=elder, remedy=remedy, setting=place, task=task)

    hero.memes["duty"] += 1
    world.say(f"Long ago, {hero.label} walked to {place.place}. {place.detail}")
    world.say(f'The {task.sound} of little steps matched {hero.label}\'s careful heart as {hero.label} went to {task.verb}.')
    world.say(f'In her heart, {hero.label} thought, "If I hurry, I can help before the moon goes down."')
    world.para()
    hero.memes["cold"] += 1
    hero.memes["strain"] += 1
    world.say(f"But the air was cold and wet, and soon {hero.label} felt {task.risk}.')
    world.say(f'"Oh dear," said {elder.label}. "You are shivering. Come here, my child."')
    world.say(f'{hero.label} asked, "Will I still be able to finish the work?"')
    world.say(f'"Yes," said {elder.label}. "First, rest a little, and take this {remedy.label} the proper way."')
    world.para()
    world.facts["aspirin_taken"] = True
    world.say(f"{hero.label} nodded and swallowed the aspirin with a sip of clean water. {task.sound} went the willow reeds outside, and the room grew quiet.")
    propagate(world, narrate=True)
    if hero.meters["ache"] < THRESHOLD:
        hero.memes["courage"] += 1
    world.say(f'After a while, the ache was gone, and {hero.label} could smile again.')
    world.say(f"With a lighter step, {hero.label} carried {task.noun} home while the bog glimmered behind {hero.pronoun('object')} like a dark green mirror.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child about {f["hero"].label} in a bog who must help with {f["task"].noun} and take {f["remedy"].label} carefully.',
        f'Tell a gentle story that includes the words "bog" and "aspirin", with dialogue, sound effects, and an inner thought before the ending.',
        f'Write a short fairy tale where a child crosses a {f["setting"].place} and a small medicine helps the child finish the journey safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    task = f["task"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.label} go to help?",
            answer=f"{hero.label} went to {setting.place} to {task.verb}. The bog was misty, so every step sounded like {task.sound} on soft ground.",
        ),
        QAItem(
            question=f"Why did {hero.label} need help before finishing the work?",
            answer=f"{hero.label} grew cold and headachy while walking in the bog. {elder.label.capitalize()} noticed the trouble and told {hero.label} to rest and take aspirin carefully.",
        ),
        QAItem(
            question=f"What changed after {hero.label} took the aspirin?",
            answer=f"The ache faded and {hero.label} felt brave again. After that, {hero.label} could carry {task.noun} home and leave the bog behind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bog?", "A bog is a wet, muddy place with soft ground and a lot of water in it."),
        QAItem("What is aspirin?", "Aspirin is a medicine that grown-ups use to help with pain or an ache."),
        QAItem("Why should medicine be taken carefully?", "Medicine should be taken carefully because the right amount helps, but the wrong amount can be unsafe."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, _ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T) :- setting(S), task(T), not bad_combo(S, T).
bad_combo(moss_bog, lantern_oil).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    lines.append(asp.fact("setting", "willow_bog"))
    lines.append(asp.fact("setting", "moss_bog"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        asp_set = set(asp_valid_combos())
        if py != asp_set:
            print("MISMATCH between Python and ASP.")
            print("only python:", sorted(py - asp_set))
            print("only asp:", sorted(asp_set - py))
            return 1
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: ASP and Python agree; generation smoke test passed.")
        return 0
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.task not in TASKS:
        raise StoryError("Unknown task.")
    world = tell(params)
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
    StoryParams(setting="willow_bog", task="herb", name="Lina", gender="girl", elder="grandmother", trait="careful"),
    StoryParams(setting="moss_bog", task="herb", name="Owen", gender="boy", elder="mother", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.task is None or c[1] == args.task)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, task = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, name=name, gender=gender, elder=elder, trait=trait)


def valid_combos() -> list[tuple[str, str]]:
    return [(sid, tid) for sid in SETTINGS for tid in TASKS if not (sid == "moss_bog" and tid == "lantern_oil")]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld about a bog and aspirin.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, t in asp_valid_combos():
            print(s, t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
