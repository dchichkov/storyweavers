#!/usr/bin/env python3
"""
storyworlds/worlds/mouth_scratch_dim_toast_repetition_sound_effects.py
======================================================================

A small fable-like storyworld about a mouth, a scratch-dim sound, and toast.

Premise:
A hungry little animal wants toast now. A helper warns that the toast is not
ready yet, because the heat is still scratch-dim: too dim to safely touch. The
child keeps repeating the same wish, the toaster keeps making sound effects,
and the helper must decide whether to wait, cool, or risk a burnt snack.

The world models:
- typed entities with physical meters and emotional memes
- repetition as an emotional pressure that can amplify desire or worry
- sound effects as narrative beats that prove an action happened
- a small resolution turn where waiting changes the toast and the mood

The domain is intentionally tiny and classical: one hungry child, one helper,
one toaster, and one slice of toast. The prose is authored from state, not a
frozen paragraph with swapped nouns.
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
SOUND_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    warm: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ToastOption:
    id: str
    label: str
    phrase: str
    crunch: str
    smell: str
    color: str
    edible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ToastMoment:
    id: str
    effect: str
    onomatopoeia: str
    intensity: float = 1.0
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_lines: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    toast = world.entities.get("toast")
    if not child or not toast:
        return out
    if child.memes["repeat_wish"] < THRESHOLD:
        return out
    sig = ("repeat",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["desire"] += 1
    child.memes["impatience"] += 1
    toast.memes["pressure"] += 1
    out.append(f"{child.id} said it again and again.")
    return out


def _r_sound_effect(world: World) -> list[str]:
    out: list[str] = []
    toaster = world.entities.get("toaster")
    toast = world.entities.get("toast")
    if not toaster or not toast:
        return out
    if toaster.meters["cycle"] < THRESHOLD:
        return out
    sig = ("sound", int(toaster.meters["cycle"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toast.memes["hearing"] += 1
    out.append(f"{toaster.attrs.get('sound', 'Click')}, went the toaster.")
    return out


def _r_browns(world: World) -> list[str]:
    out: list[str] = []
    toaster = world.entities.get("toaster")
    toast = world.entities.get("toast")
    if not toaster or not toast:
        return out
    if toaster.meters["heat"] < THRESHOLD:
        return out
    sig = ("brown",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    toast.meters["warm"] += 1
    if toaster.meters["heat"] >= 2:
        toast.meters["browned"] += 1
        out.append("At last, the toast turned golden at the edges.")
    else:
        out.append("The toast only warmed a little.")
    return out


RULES = [Rule(name="repetition", apply=_r_repetition), Rule(name="sound_effect", apply=_r_sound_effect), Rule(name="brown", apply=_r_browns)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                produced.extend(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str]]:
    return [("kitchen", "plain"), ("kitchen", "jam"), ("table", "plain")]


@dataclass
class StoryParams:
    setting: str
    toast: str
    child_name: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="kitchen", toast="plain", child_name="Mina", helper_name="Papa", helper_type="father"),
    StoryParams(setting="kitchen", toast="jam", child_name="Toby", helper_name="Mama", helper_type="mother"),
    StoryParams(setting="table", toast="plain", child_name="Lina", helper_name="Grandma", helper_type="woman"),
]


SETTINGS = {
    "kitchen": Place(id="kitchen", label="the kitchen", warm=True, affords={"toast"}),
    "table": Place(id="table", label="the table", warm=True, affords={"toast"}),
}

TOASTS = {
    "plain": ToastOption(id="plain", label="toast", phrase="a slice of toast", crunch="crisp", smell="warm", color="golden"),
    "jam": ToastOption(id="jam", label="jam toast", phrase="a jam-smeared slice of toast", crunch="sticky-crisp", smell="sweet", color="amber"),
}

SOUNDS = {
    "plain": ToastMoment(id="plain", effect="ready", onomatopoeia="Ding", intensity=1.0),
    "jam": ToastMoment(id="jam", effect="slow", onomatopoeia="Click-clack", intensity=2.0),
}

NAMES = ["Mina", "Toby", "Lina", "Nora", "Eli", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like storyworld about toast, repetition, and sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toast", dest="toast_kind", choices=TOASTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "woman", "man"])
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
              and (args.toast_kind is None or c[1] == args.toast_kind)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, toast_kind = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(NAMES)
    helper_name = args.helper or rng.choice([n for n in NAMES if n != child_name] + ["Papa", "Mama", "Grandma"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "woman", "man"])
    return StoryParams(setting=setting, toast=toast_kind, child_name=child_name, helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    place = SETTINGS[params.setting]
    toast_cfg = TOASTS[params.toast]
    sound = SOUNDS[params.toast]
    world = World(place)

    child = world.add(Entity(id="child", kind="character", type="boy", label=params.child_name, traits=["hungry", "patient"], attrs={"role": "child"}))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name, traits=["kind", "wise"], attrs={"role": "helper"}))
    toaster = world.add(Entity(id="toaster", kind="thing", type="toaster", label="toaster", attrs={"sound": sound.onomatopoeia}))
    toast = world.add(Entity(id="toast", kind="thing", type="toast", label=toast_cfg.label, traits=[toast_cfg.crunch, toast_cfg.smell], tags=set(toast_cfg.tags)))

    child.memes["repeat_wish"] = 1.0
    child.memes["impatience"] = 0.0
    child.memes["joy"] = 0.0
    helper.memes["calm"] = 1.0
    toast.meters["heat"] = 0.0
    toast.meters["warm"] = 0.0
    toast.meters["browned"] = 0.0
    toaster.meters["cycle"] = 0.0
    toaster.meters["heat"] = 1.0

    world.say(f"At {place.label}, {child.label} watched the toaster with a hungry mouth.")
    world.say(f'"Toast now, toast now," {child.label} said, because the wish was small but repeated.')
    world.say(f"{helper.label} smiled and pointed to the toaster. \"Wait for the sound,\" {helper.pronoun()} said.")
    world.para()

    toaster.meters["cycle"] += 1
    propagate(world, narrate=True)
    world.say(f"{sound.onomatopoeia}! went the toaster again, and the room filled with a warm smell.")
    world.para()

    if params.toast == "jam":
        child.memes["repeat_wish"] += 1
        child.memes["impatience"] += 1
        world.say(f'"Toast now," {child.label} said again, but {helper.label} kept the patience of a tree.')
        toaster.meters["heat"] += 1
        toaster.meters["cycle"] += 1
        propagate(world, narrate=True)
        world.say("The second sound was slower, and the toast grew more golden.")
    else:
        toaster.meters["heat"] += 1
        propagate(world, narrate=True)
        world.say(f"Then the toast was ready at once, bright as a little sun.")

    world.para()
    if toast.meters["browned"] >= 1:
        child.memes["joy"] += 1
        helper.memes["pride"] += 1
        world.say(f"{helper.label} lifted the toast with a cloth, and the mouth that had been asking could now nibble and smile.")
        world.say(f"The child shared the toast, and the helper shared the quiet lesson: good things come safely when you wait.")
    else:
        child.memes["joy"] += 0.5
        world.say(f"{helper.label} let the toast cool first, so no tongue was hurt and the snack stayed kind.")
        world.say("Waiting had turned the first wanting into a better ending.")

    world.facts.update(child=child, helper=helper, toaster=toaster, toast=toast, place=place, toast_cfg=toast_cfg, sound=sound)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    toast = f["toast"]
    place = f["place"]
    toast_cfg = f["toast_cfg"]
    return [
        QAItem(
            question=f"Who wanted toast at {place.label}?",
            answer=f"{child.label} wanted toast, and {child.label}'s mouth kept saying the same wish again and again.",
        ),
        QAItem(
            question="What did the helper ask the child to do?",
            answer=f"{helper.label} asked {child.label} to wait for the toaster sound, because the toast was not ready yet.",
        ),
        QAItem(
            question="What sound did the toaster make?",
            answer=f"It made {f['sound'].onomatopoeia} and other little sound effects that showed the toast was changing.",
        ),
        QAItem(
            question=f"What happened to the toast?",
            answer=f"It became {toast_cfg.color} and {toast_cfg.crunch}, and its smell turned {toast_cfg.smell}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is toast?", answer="Toast is bread that has been heated until it is crisp and warm."),
        QAItem(question="Why do people wait for toast?", answer="People wait so the bread can turn golden and be safe to eat without burning their mouths."),
        QAItem(question="What is a sound effect?", answer="A sound effect is a little sound that helps show what is happening, like click, ding, or sizzle."),
        QAItem(question="What does repeating a wish do?", answer="Repeating a wish can show strong wanting, and it may make a helper remind everyone to wait calmly."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    toast_cfg = f["toast_cfg"]
    return [
        f"Write a short fable about {child.label} who keeps asking for {toast_cfg.label} and learns to wait.",
        f"Tell a child-friendly story with sound effects where {helper.label} helps {child.label} make {toast_cfg.label} safely.",
        f"Write a gentle repetition story about a hungry mouth, a toaster, and a happy ending.",
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
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
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


ASP_RULES = r"""
valid(setting(kitchen),toast(plain)).
valid(setting(kitchen),toast(jam)).
valid(setting(table),toast(plain)).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [asp.fact("setting", sid) for sid in SETTINGS] +
        [asp.fact("toast", tid) for tid in TOASTS]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((s, t) for s, t in valid_combos())
    asp_set = set(tuple(x) for x in asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python combos.")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


def build_parser2():
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} / {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos_from_seed() -> list[tuple[str, str]]:
    return valid_combos()


if __name__ == "__main__":
    main()
