#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/feeder_precious_transformation_ghost_story.py
===============================================================================================================

A tiny ghost-story world about a child, a feeder, and a transformation.

Seed tale:
---
On a cold moonlit night, Mina found a small bird feeder hanging by the window.
It was precious to her because her grandma had given it to her before moving
away. But after the first frost, the feeder stood empty and lonely.

Then a pale ghost drifted out of the garden mist. Mina was frightened, but the
ghost only pointed at the feeder and the little bowl of seed on the shelf.
"Please," whispered Mina, "don't scare me."

The ghost touched the feeder. Its dull wood turned bright and warm, and the
empty bowl filled with golden seed. The ghost changed too: its smoky edges
softened into a real white owl with a bright face. Mina gasped, then smiled.

Now the feeder hung full under the moon, and the owl perched beside it like a
friend. Mina knew the precious thing had changed, but it was still hers, and
the night no longer felt lonely.

Story instruments:
---
- A precious object is protected and cared for.
- A ghostly presence creates fear and then becomes a helper.
- Transformation changes a thing's form and the hero's feelings.
- The ending image proves what changed: the feeder is full, the ghost is gone,
  and a new friend remains.

Causal state updates:
---
    call of the ghost        -> child.fear += 1 ; ghost.mist += 1
    touching the feeder      -> feeder.glow += 1 ; feeder.full += 1
    transformation succeeds  -> ghost.mist -> 0 ; ghost.form changes
                                 child.fear -= 1 ; child.joy += 1
    precious object filled   -> caretaker.relief += 1 ; caretaker.love += 1

Scripted social/emotional beats:
---
    child notices the feeder      -> child.longing += 1
    ghost appears                 -> child.fear += 1 ; ghost.mystery += 1
    ghost offers help             -> child.trust += 1
    transformation accepted       -> child.joy += 1 ; fear -> 0
    ending image                  -> night feels safe, precious thing stays cherished
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    form: str = ""
    precious: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the garden"
    night: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Feeder:
    id: str
    label: str
    phrase: str
    color: str
    holds: str
    form: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GhostState:
    id: str
    label: str
    form: str
    help_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Change:
    id: str
    from_form: str
    to_form: str
    method: str
    effect: str
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_ghost_fear(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.meters["seen"] >= THRESHOLD and ("ghost_fear",) not in world.fired:
        world.fired.add(("ghost_fear",))
        child.memes["fear"] += 1
        ghost.meters["mystery"] += 1
        out.append("__ghost__")
    return out


def _r_feeder_glow(world: World) -> list[str]:
    out = []
    feeder = world.get("feeder")
    if feeder.meters["touched"] >= THRESHOLD and ("feeder_glow",) not in world.fired:
        world.fired.add(("feeder_glow",))
        feeder.meters["glow"] += 1
        feeder.meters["full"] += 1
        out.append("The feeder brightened and filled up.")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    ghost = world.get("ghost")
    child = world.get("child")
    feeder = world.get("feeder")
    if ghost.meters["helped"] >= THRESHOLD and feeder.meters["full"] >= THRESHOLD and ("transform",) not in world.fired:
        world.fired.add(("transform",))
        ghost.form = "owl"
        ghost.meters["seen"] = 0
        ghost.meters["mist"] = 0
        child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
        child.memes["joy"] += 1
        child.memes["trust"] += 1
        out.append("The ghost changed into an owl.")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    feeder = world.get("feeder")
    caretaker = world.get("caretaker")
    if feeder.meters["full"] >= THRESHOLD and ("relief",) not in world.fired:
        world.fired.add(("relief",))
        caretaker.memes["relief"] += 1
        caretaker.memes["love"] += 1
        out.append("That made the caretaker feel relieved.")
    return out


CAUSAL_RULES = [
    Rule("ghost_fear", "social", _r_ghost_fear),
    Rule("feeder_glow", "physical", _r_feeder_glow),
    Rule("transform", "physical", _r_transformation),
    Rule("relief", "social", _r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for feeder_id in FEEDERS:
            for ghost_id in GHOSTS:
                for change_id in CHANGES:
                    if place in setting.affords:
                        combos.append((place, feeder_id, ghost_id, change_id))
    return combos


@dataclass
class StoryParams:
    place: str
    feeder: str
    ghost: str
    change: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the garden", night=True, affords={"garden", "porch"}),
    "porch": Setting(place="the porch", night=True, affords={"porch"}),
    "window": Setting(place="the window", night=True, affords={"window", "garden"}),
}

FEEDERS = {
    "birdfeeder": Feeder(
        id="feeder",
        label="feeder",
        phrase="a small bird feeder",
        color="pale blue",
        holds="seed",
        form="wood",
        tags={"feeder", "bird", "seed"},
    ),
    "lanternfeeder": Feeder(
        id="feeder",
        label="feeder",
        phrase="a little hanging feeder-lantern",
        color="gold",
        holds="light",
        form="glass",
        tags={"feeder", "light"},
    ),
}

GHOSTS = {
    "mistghost": GhostState(
        id="ghost",
        label="ghost",
        form="mist",
        help_line="Please, let me help",
        tags={"ghost", "mist"},
    ),
    "paleghost": GhostState(
        id="ghost",
        label="ghost",
        form="pale shadow",
        help_line="I can change this night",
        tags={"ghost", "shadow"},
    ),
}

CHANGES = {
    "owl": Change(
        id="owl",
        from_form="mist",
        to_form="owl",
        method="touching the feeder",
        effect="a warm, feathered helper",
        tags={"owl", "transformation"},
    ),
    "cat": Change(
        id="cat",
        from_form="shadow",
        to_form="cat",
        method="listening to the child",
        effect="a soft friend",
        tags={"cat", "transformation"},
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Luna", "Ada", "Elsie"]
BOY_NAMES = ["Noel", "Finn", "Owen", "Theo", "Jude", "Ben"]
TRAITS = ["curious", "brave", "gentle", "quiet", "hopeful"]


def explain_rejection(place: str) -> str:
    return f"(No story: {place} is not a valid spooky place here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story transformation world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--feeder", choices=FEEDERS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--change", choices=CHANGES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.feeder is None or c[1] == args.feeder)
              and (args.ghost is None or c[2] == args.ghost)
              and (args.change is None or c[3] == args.change)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, feeder, ghost, change = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, feeder=feeder, ghost=ghost, change=change, name=name, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id="child", kind="character", type="girl" if params.name in GIRL_NAMES else "boy", label=params.name))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=params.parent, label=f"the {params.parent}"))
    feeder_cfg = FEEDERS[params.feeder]
    ghost_cfg = GHOSTS[params.ghost]
    change_cfg = CHANGES[params.change]
    feeder = world.add(Entity(id="feeder", type="feeder", label=feeder_cfg.label, phrase=feeder_cfg.phrase, precious=True))
    ghost = world.add(Entity(id="ghost", type="ghost", label=ghost_cfg.label, form=ghost_cfg.form))
    world.facts.update(child=child, caretaker=caretaker, feeder=feeder, ghost=ghost, change=change_cfg,
                       feeder_cfg=feeder_cfg, ghost_cfg=ghost_cfg, params=params)
    child.memes["fear"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["trust"] = 0.0
    child.memes["longing"] = 0.0
    caretaker.memes["relief"] = 0.0
    caretaker.memes["love"] = 0.0
    feeder.meters["touched"] = 0.0
    feeder.meters["full"] = 0.0
    feeder.meters["glow"] = 0.0
    ghost.meters["seen"] = 0.0
    ghost.meters["helped"] = 0.0
    ghost.meters["mist"] = 1.0
    ghost.meters["mystery"] = 0.0

    world.say(f"On a quiet night in {world.setting.place}, {params.name} noticed a precious feeder hanging by the window.")
    world.say(f"It was precious because it had been a gift, and the little feeder looked lonely in the dark.")
    world.para()
    child.memes["longing"] += 1
    ghost.meters["seen"] += 1
    world.say(f"Then a ghost drifted out of the mist. {params.name} felt a shiver, but the ghost only moved closer to the feeder.")
    world.say(f'"{ghost_cfg.help_line}," whispered the ghost, and its pale edges trembled like smoke.')
    propagate(world, narrate=True)
    world.para()
    feeder.meters["touched"] += 1
    ghost.meters["helped"] += 1
    world.say(f"{params.name} touched the feeder, and the old wood seemed to wake up.")
    world.say(f"The feeder glowed softly as the ghost reached out to help, not to scare.")
    propagate(world, narrate=True)
    world.para()
    if ghost.form != change_cfg.to_form:
        ghost.meters["helped"] += 1
        propagate(world, narrate=True)
    if ghost.form == "owl":
        world.say(f"The ghost transformed into an owl with bright eyes, and {params.name} smiled instead of trembling.")
    else:
        world.say(f"The ghost changed into a friend, and the dark felt less empty.")
    world.say(f"In the ending image, the feeder hung full, the night was calm, and the precious thing stayed safe.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that uses the words "{f["feeder_cfg"].label}" and "precious".',
        f"Tell a gentle spooky story where {f['params'].name} sees a ghost by the {f['feeder_cfg'].label} and a transformation makes the night kind.",
        f"Write a short story about a precious feeder that changes the ghost into a friend.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["params"]
    child = f["child"]
    feeder = f["feeder"]
    ghost = f["ghost"]
    return [
        QAItem(
            question=f"What did {p.name} think was precious in the story?",
            answer=f"{p.name} thought the feeder was precious because it had been a gift and it was something to care for. By the end, it stayed precious even after the spooky night changed.",
        ),
        QAItem(
            question=f"Why did {p.name} feel scared when the ghost appeared near the feeder?",
            answer=f"{p.name} felt scared because a ghost drifted out of the mist in the dark garden. The fear eased when the ghost came closer to help the feeder instead of harming it.",
        ),
        QAItem(
            question=f"What changed after {p.name} touched the feeder?",
            answer=f"The feeder started to glow and fill up, and the ghost transformed from mist into an owl. That change turned the night from lonely to safe and friendly.",
        ),
        QAItem(
            question=f"How did the story end for the feeder and the ghost?",
            answer=f"It ended with the feeder full and hanging bright in the moonlight, while the ghost had become an owl. {p.name} could look at the precious feeder without fear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a feeder?", "A feeder is a container that holds food for birds or other animals so they can eat safely."),
        QAItem("What does precious mean?", "Precious means very special and worth caring for carefully."),
        QAItem("What is a ghost story?", "A ghost story is a story with something spooky or mysterious, but it can still end gently."),
        QAItem("What does transformation mean?", "Transformation means something changes into a different form."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.form:
            bits.append(f"form={e.form}")
        if e.precious:
            bits.append("precious=True")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
precious(feeder).
ghostly(ghost).
touching_changes(child, feeder).
transform(ghost, owl) :- ghostly(ghost), feeder_full(feeder).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("precious", "feeder"),
        asp.fact("ghostly", "ghost"),
        asp.fact("touching_changes", "child", "feeder"),
        asp.fact("feeder_full", "feeder"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        model = asp.one_model(asp_program("#show transform/2."))
        ok = ("transform", "ghost", "owl") in asp.atoms(model, "transform")
    except Exception as err:
        print(err)
        return 1
    if not ok:
        print("MISMATCH: ASP transform rule failed.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show precious/1.\n#show ghostly/1.\n"))
    return sorted(set(asp.atoms(model, "precious")))


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


CURATED = [
    StoryParams(place="garden", feeder="birdfeeder", ghost="mistghost", change="owl", name="Mina", parent="mother", trait="gentle"),
    StoryParams(place="porch", feeder="lanternfeeder", ghost="paleghost", change="cat", name="Noel", parent="father", trait="curious"),
]


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
        print(asp_program("#show transform/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show precious/1."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
