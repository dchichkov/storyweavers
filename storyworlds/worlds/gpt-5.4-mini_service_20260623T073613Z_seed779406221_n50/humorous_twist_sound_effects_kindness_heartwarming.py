#!/usr/bin/env python3
"""
storyworlds/worlds/humorous_twist_sound_effects_kindness_heartwarming.py
=======================================================================

A small standalone storyworld about a child, a funny noisy gadget, a twist,
and a kind heartwarming fix.

Initial source tale, used to build the world model:
---
Pip wanted to play the tiny music box before bedtime, because it made a silly
little "plink-plonk" sound and the spinning owl on top always made her laugh.
But the nursery was quiet, and Baby Jun was sleeping in the next room.

When Pip wound the box too hard, it gave a huge "BANG-TA-DA!" and the owl
sneezed off the lid with a comic "poof!" Pip gasped. She thought she had
ruined bedtime.

Then her big sister Mara had a funny twist: she set the music box inside a sock
drawer so the tune became a soft "mrrr-ting" instead of a clatter. She also
tucked a little blanket around Baby Jun's door, and the room grew calm again.
Pip giggled, Mara smiled, and the owl did one last tiny bow.

Causal state updates:
---
    wind toy too hard               -> toy.noise += 2 ; toy.hop += 1
    toy.noise above threshold       -> baby.sleepiness += 1 ; parent.worry += 1
    kind softening fix used         -> toy.noise -= 2 ; child.joy += 1 ; parent.worry -= 1
    blanket at doorway              -> baby.sleepiness += 1 ; noise_leak -= 1

Scripted social/emotional beats:
---
    playful setup                   -> child.joy += 1
    loud twist                       -> child.surprise += 1 ; child.humor += 1
    gentle guidance                  -> helper.kindness += 1
    fix accepted                    -> child.joy += 1 ; parent.relief += 1
    ending image                    -> everyone calm, toy still funny but soft
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    noise: int
    funny: str
    can_soothe: bool = False
    can_soften: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    effect: int
    preparation: str
    tail: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    if toy.meters["noise"] < THRESHOLD:
        return out
    if ("noise",) in world.fired:
        return out
    world.fired.add(("noise",))
    if "baby" in world.entities:
        world.get("baby").meters["sleepiness"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["worry"] += 1
    out.append("The little room felt suddenly much louder.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    if toy.meters["noise"] >= THRESHOLD and world.get("helper").meters["kindness"] >= THRESHOLD:
        sig = ("fix",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        toy.meters["noise"] = max(0.0, toy.meters["noise"] - 2)
        world.get("child").memes["joy"] += 1
        world.get("parent").memes["worry"] = max(0.0, world.get("parent").memes["worry"] - 1)
        out.append("The noise softened into a gentle little hum.")
    return out


CAUSAL_RULES = [
    Rule("noise", _r_noise),
    Rule("fix", _r_fix),
]


def child_setup(world: World, child: Entity, toy: Toy) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} loved {toy.phrase} because it made a silly {toy.funny} sound."
    )
    world.say(
        f"Every time the toy chirped, {child.id} giggled and gave it one more tiny spin."
    )


def bedtime_scene(world: World, child: Entity, helper: Entity, baby: Entity, toy: Toy) -> None:
    world.say(
        f"At bedtime, {child.id} tiptoed into {world.setting.place} with {toy.label} tucked under {child.pronoun('possessive')} arm."
    )
    world.say(
        f"Baby {baby.id} was sleeping in the next room, so {helper.id} lifted one finger and whispered, \"Let's keep it soft.\""
    )


def twist_bang(world: World, toy: Toy) -> None:
    toy.meters["noise"] += 2
    toy.meters["hop"] += 1
    world.get("child").memes["surprise"] += 1
    world.get("child").memes["humor"] += 1
    world.say(
        f"But when {toy.label} got wound too hard, it went {toy.funny.upper()} and popped its lid with a comic little poof!"
    )
    world.say("The spinning owl on top did a surprised wobble and nearly toppled over.")


def guide_kindly(world: World, helper: Entity, child: Entity, toy: Toy) -> None:
    helper.meters["kindness"] += 1
    world.say(
        f"{helper.id} did not scold {child.id}. Instead, {helper.id} smiled and said, \"That toy is very funny. Let's make it quieter.\""
    )


def blanket_door(world: World, helper: Entity, baby: Entity) -> None:
    helper.meters["kindness"] += 1
    baby.meters["sleepiness"] += 1
    world.say(
        f"{helper.id} also draped a little blanket across {baby.id}'s doorway, and the room felt snug and peaceful."
    )


def gentle_fix(world: World, helper: Entity, child: Entity, toy: Toy, fix: Fix) -> None:
    helper.meters["kindness"] += 1
    world.say(
        f"{helper.id} tried a clever twist: {fix.preparation}."
    )
    world.say(
        f"Then {helper.id} set {toy.label} inside the {fix.label}, and the clatter turned into a soft {fix.phrase}."
    )
    propagate(world)
    world.say(
        f"{fix.tail}. {child.id} grinned, because the toy was still funny, only much gentler now."
    )


def ending_image(world: World, child: Entity, helper: Entity, baby: Entity, toy: Toy) -> None:
    world.get("parent").memes["relief"] += 1
    world.say(
        f"In the end, {child.id} gave {toy.label} one last careful turn, and it answered with a sleepy little chime."
    )
    world.say(
        f"{helper.id} hugged {child.id}, {baby.id} kept sleeping, and the whole room stayed calm."
    )


SETTING = {
    "nursery": Setting("the nursery", {"windup"}),
    "bedroom": Setting("the bedroom", {"windup"}),
    "playroom": Setting("the playroom", {"windup"}),
}

TOYS = {
    "music_box": Toy(
        id="music_box",
        label="music box",
        phrase="a tiny music box",
        noise=2,
        funny="plink-plonk",
        can_soothe=True,
        can_soften=True,
        tags={"music", "sound", "twist"},
    ),
    "toy_drum": Toy(
        id="toy_drum",
        label="toy drum",
        phrase="a little toy drum",
        noise=3,
        funny="boom-biddy-boom",
        can_soothe=False,
        can_soften=True,
        tags={"drum", "sound", "twist"},
    ),
    "windup_duck": Toy(
        id="windup_duck",
        label="wind-up duck",
        phrase="a wind-up duck",
        noise=2,
        funny="quack-a-zoom",
        can_soothe=True,
        can_soften=True,
        tags={"duck", "sound", "twist"},
    ),
}

FIXES = {
    "sock_drawer": Fix(
        id="sock_drawer",
        label="sock drawer",
        phrase="mrrr-ting",
        effect=2,
        preparation="she tucked the toy into a sock drawer",
        tail="The tune became a tiny mrrr-ting, like a secret song in slippers",
        tags={"soft", "quiet"},
    ),
    "pillow_box": Fix(
        id="pillow_box",
        label="pillow box",
        phrase="fwoomp",
        effect=2,
        preparation="he lined a little box with two fluffy pillows",
        tail="The sound turned into a cozy fwoomp and then faded away",
        tags={"soft", "quiet"},
    ),
    "tea_towel": Fix(
        id="tea_towel",
        label="tea towel nest",
        phrase="mip-mip",
        effect=1,
        preparation="they wrapped the toy in a tea towel nest",
        tail="The noise shrank into a polite mip-mip that hardly woke a pebble",
        tags={"soft", "quiet"},
    ),
}

GENTLE_HELPERS = ["Mara", "Nina", "Ben", "Owen"]
CHILDREN = ["Pip", "Iris", "Jude", "Luna", "Theo"]


@dataclass
class StoryParams:
    setting: str
    toy: str
    fix: str
    child: str
    helper: str
    parent: str = "parent"
    baby: str = "Baby Jun"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTING:
        for t in TOYS:
            for f in FIXES:
                combos.append((s, t, f))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world about a humorous twist, sound effects, and kindness.")
    ap.add_argument("--setting", choices=SETTING)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    setting = args.setting or rng.choice(list(SETTING))
    toy = args.toy or rng.choice(list(TOYS))
    fix = args.fix or rng.choice(list(FIXES))
    child = args.name or rng.choice(CHILDREN)
    helper = args.helper or rng.choice([h for h in GENTLE_HELPERS if h != child])
    if helper == child:
        raise StoryError("helper and child must be different names")
    return StoryParams(setting=setting, toy=toy, fix=fix, child=child, helper=helper)


def tell(setting: Setting, toy: Toy, fix: Fix, child_name: str, helper_name: str, parent_name: str, baby_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl" if child_name in {"Pip", "Iris", "Luna"} else "boy"))
    helper = world.add(Entity(id=helper_name, kind="character", type="girl" if helper_name in {"Mara", "Nina"} else "boy"))
    parent = world.add(Entity(id=parent_name, kind="character", type="adult", label="the parent"))
    baby = world.add(Entity(id=baby_name, kind="character", type="baby", label=baby_name))
    toy_ent = world.add(Entity(id="toy", type="toy", label=toy.label, phrase=toy.phrase))
    helper_ent = world.add(Entity(id="helper", type="helper", label=helper_name))
    helper_ent.meters["kindness"] = 0.0
    world.facts.update(child=child, helper=helper, parent=parent, baby=baby, toy=toy_ent, fix=fix, setting=setting, toy_cfg=toy)
    child_setup(world, child, toy)
    world.para()
    bedtime_scene(world, child, helper, baby, toy)
    twist_bang(world, toy)
    guide_kindly(world, helper, child, toy)
    blanket_door(world, helper, baby)
    world.para()
    gentle_fix(world, helper, child, toy, fix)
    ending_image(world, child, helper, baby, toy)
    return world


ASP_RULES = r"""
valid(S,T,F) :- setting(S), toy(T), fix(F).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTING:
        lines.append(asp.fact("setting", s))
    for t in TOYS:
        lines.append(asp.fact("toy", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("Mismatch between ASP and Python combos.")
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child where {f["child"].id} hears a funny {f["toy_cfg"].funny} sound and learns a gentler way to keep playing.',
        f"Tell a kind bedtime story where {f['helper'].id} helps {f['child'].id} soften {f['toy'].label} with a clever twist.",
        f'Write a short humorous story with a soft sound effect like "{f["toy_cfg"].funny}" and a kind ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"What did {f['child'].id} love about the toy?", answer=f"{f['child'].id} loved the silly sound and the funny spinning motion. It made bedtime feel like a tiny game."),
        QAItem(question=f"How did {f['helper'].id} help?", answer=f"{f['helper'].id} did not scold anyone. Instead, {f['helper'].id} found a quieter trick and made the toy gentler."),
        QAItem(question=f"What was the twist in the story?", answer=f"The twist was that the loud toy did not have to stay loud. It could become a soft little chime and still be fun."),
        QAItem(question=f"How did the story end?", answer=f"It ended with everyone calm: {f['child'].id} smiled, {f['helper'].id} was kind, and the baby kept sleeping."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is kindness?", answer="Kindness means helping gently, using soft words, and making things better for someone else."),
        QAItem(question="What is a sound effect?", answer="A sound effect is a special noise that helps a story feel lively, like a plink or a poof."),
        QAItem(question="What is a twist in a story?", answer="A twist is a surprising turn that changes what you expect, often in a funny or clever way."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING[params.setting], TOYS[params.toy], FIXES[params.fix], params.child, params.helper, params.parent, params.baby)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        for s, t, f in asp_valid_combos():
            print(s, t, f)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams("nursery", "music_box", "sock_drawer", "Pip", "Mara"),
            StoryParams("bedroom", "toy_drum", "pillow_box", "Iris", "Ben"),
            StoryParams("playroom", "windup_duck", "tea_towel", "Luna", "Nina"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
