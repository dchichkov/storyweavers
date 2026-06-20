#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/zoom_tilt_living_room_magic_inner_monologue.py
===============================================================================

A small superhero-story world set in a living room, built from the seed words
"zoom" and "tilt" plus two narrative instruments: magic and inner monologue.

Premise
-------
A kid with a magic costume rehearses a living-room rescue. A tiny mistake
tilts the pretend scene out of balance, then a thoughtful inner monologue helps
them steady the spell, save the day, and end with a brighter, safer room.

This script is self-contained and stdlib-only. It follows the shared storyworld
contract: typed entities with physical meters and emotional memes, a Python
reasonableness gate, an inline ASP twin, three QA sets, trace support, JSON
output, and verification that compares ASP parity and exercises generation.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

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
        return self.label or self.type


@dataclass
class Prop:
    id: str
    label: str
    magic: bool = False
    tilts: bool = False
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    cause: str
    effect: str
    kind: str = "accident"
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_zoom(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    scene = world.get("room")
    if hero.meters["zoomed"] < THRESHOLD:
        return out
    sig = ("zoom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scene.meters["motion"] += 1
    hero.memes["focus"] += 1
    out.append("__zoom__")
    return out


def _r_tilt(world: World) -> list[str]:
    out: list[str] = []
    scene = world.get("room")
    hat = world.get("cape")
    if scene.meters["tilt"] < THRESHOLD:
        return out
    sig = ("tilt",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hat.meters["rattled"] += 1
    scene.meters["wobble"] += 1
    out.append("__tilt__")
    return out


def _r_spill_magic(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    hero = world.get("hero")
    wand = world.get("wand")
    if wand.meters["spark"] < THRESHOLD or room.meters["wobble"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["glow"] += 1
    hero.memes["worry"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("zoom", "motion", _r_zoom), Rule("tilt", "motion", _r_tilt), Rule("spill", "magic", _r_spill_magic)]


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


def reasonableness_ok(plan: str, prop: Prop) -> bool:
    return plan in {"zoom", "tilt"} and (prop.magic or prop.safe)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for plan in PLANS:
        for prop_id, prop in PROPS.items():
            if reasonableness_ok(plan, prop):
                combos.append((plan, prop_id))
    return combos


def is_success(plan: str, prop: Prop, delay: int) -> bool:
    if plan == "zoom":
        return True
    return prop.magic and delay <= 1


@dataclass
class StoryParams:
    plan: str
    prop: str
    sidekick: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero-style living-room story world with zoom and tilt.")
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.plan is None or c[0] == args.plan)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    plan, prop = rng.choice(sorted(combos))
    if args.prop and not reasonableness_ok(plan, PROPS[args.prop]):
        raise StoryError("(This prop does not make a sensible superhero story here.)")
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(plan, prop, sidekick, parent, delay)


def tell(params: StoryParams) -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type="boy", role="hero", traits=["brave", "thoughtful"]))
    sidekick = world.add(Entity("sidekick", kind="character", type="girl", role="sidekick", label=params.sidekick))
    parent = world.add(Entity("parent", kind="character", type=params.parent, role="parent", label="the parent"))
    room = world.add(Entity("room", type="room", label="the living room"))
    wand = world.add(Entity("wand", type="tool", label="glimmer wand", attrs={"kind": "magic"}))
    cape = world.add(Entity("cape", type="costume", label="red cape"))
    prop = world.add(Entity("prop", type="thing", label=PROPS[params.prop].label))

    hero.memes["hope"] += 1
    hero.meters["zoomed"] += 1 if params.plan == "zoom" else 0
    room.meters["tilt"] += 1 if params.plan == "tilt" else 0
    wand.meters["spark"] += 1

    world.say(
        f"In the living room, {hero.id} wore {cape.label} and held {wand.label}. "
        f"{sidekick.id} watched beside the couch while the little room waited like a stage."
    )
    world.say(
        f'"Watch this," {hero.id} whispered. "I can {params.plan} around the room '
        f'and keep the mission safe."'
    )
    world.say(f"Inside {hero.pronoun('possessive')} head, a quiet inner monologue answered: "
              f'"Stay calm, notice the wobble, and do the smart superhero thing."')

    world.para()
    if params.plan == "zoom":
        world.say(f"{hero.id} chose the quick {params.plan}, and the toy drone began to {params.plan} past the lamp.")
        hero.meters["zoomed"] += 1
    else:
        world.say(f"{hero.id} tried to {params.plan} the pretend rescue, but the rug edge made the scene tilt.")
        room.meters["tilt"] += 1
        prop.meters["tipped"] += 1

    propagate(world, narrate=False)

    if params.plan == "tilt":
        world.say(
            f"The tilt sent the magic spark hopping toward the prop, and the room filled with a nervous shimmer."
        )
        world.say(
            f"{sidekick.id} gasped, and {hero.id} felt {hero.pronoun('possessive')} heart thump hard."
        )
        if is_success(params.plan, PROPS[params.prop], params.delay):
            world.para()
            hero.meters["focus"] += 1
            room.meters["glow"] += 1
            world.say(
                f"Then the inner monologue steadied {hero.id}: 'Use the wand gently, lower the cape, and fix it before it falls.'"
            )
            world.say(
                f"{hero.id} tilted the prop back into place and guided the spark into a safe bright circle."
            )
            world.say(
                f"The living room stopped wobbling. The cape swung straight again, and the little glow sat neatly on the table."
            )
        else:
            world.para()
            hero.memes["worry"] += 1
            room.meters["glow"] += 1
            world.say(
                f"{hero.id} tried to calm the magic, but the wobble was too big and the spark scattered across the rug."
            )
            world.say(
                f"{parent.label_word.capitalize()} came in, and together they switched the magic off before anything broke."
            )
            world.say(
                f"After that, the cape lay still, the wand rested on the shelf, and the room was quiet again."
            )
    else:
        world.say(
            f"The zoom rushed past the sofa like a bright blue streak, and {sidekick.id} cheered because the trick stayed smooth."
        )
        world.para()
        world.say(
            f"{hero.id} listened to {hero.pronoun('possessive')} inner monologue, slowed down, and set the prop down exactly where it belonged."
        )
        world.say(
            f"The cape fluttered, the wand glowed softly, and the living room looked ready for the next heroic game."
        )

    world.facts.update(
        hero=hero, sidekick=sidekick, parent=parent, room=room, wand=wand, cape=cape, prop=prop,
        params=params, outcome="safe" if is_success(params.plan, PROPS[params.prop], params.delay) else "messy",
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a superhero story in a living room that includes the words "zoom" and "tilt".',
        f"Tell a child-friendly magic story where {f['hero'].id} must choose between zooming too fast or tilting the scene carefully.",
        f'Write a short story with inner monologue and magic where {f["sidekick"].id} helps keep a living-room rescue safe.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, sidekick, parent, prop = f["hero"], f["sidekick"], f["parent"], f["prop"]
    params: StoryParams = f["params"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id}, a small superhero-in-training, and {sidekick.id}, who helps watch the magic from the side."),
        ("What words from the story are especially important?",
         f'The important words are "zoom" and "tilt". They describe the two ways the hero can move the magic in the living room.'),
        ("What did the inner monologue help the hero do?",
         f"It helped {hero.id} stay calm and choose the smart move. That made the magic behave and kept the living room safe."),
    ]
    if params.plan == "tilt":
        if f["outcome"] == "safe":
            qa.append((
                "How did the hero fix the tilted scene?",
                f"{hero.id} listened to {hero.pronoun('possessive')} own inner monologue, lowered the cape, and guided the spark back into a safe bright circle. "
                f"That steadied the room and kept {prop.label} from being ruined."
            ))
        else:
            qa.append((
                "What happened when the tilt went wrong?",
                f"The wobble scattered the spark and made the room messy. Then {parent.label_word} came in and helped switch the magic off before anything broke."
            ))
    else:
        qa.append((
            "How did the zoom scene end?",
            f"{hero.id} zoomed past the sofa, slowed down, and set the prop down neatly. "
            f"The ending showed that the hero could move fast and still be careful."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["prop"].tags)
    tags |= {"zoom", "tilt", "magic", "inner_monologue", "superhero"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLANS = ["zoom", "tilt"]

PROPS = {
    "drone": Prop("drone", "toy drone", magic=False, tilts=False, safe=True, tags={"superhero"}),
    "orb": Prop("orb", "glimmer orb", magic=True, tilts=True, safe=False, tags={"magic"}),
    "cape": Prop("cape", "bright cape", magic=True, tilts=True, safe=True, tags={"magic", "superhero"}),
    "lamp": Prop("lamp", "little lamp", magic=False, tilts=False, safe=True, tags={"living_room"}),
}

SIDEKICKS = ["Mina", "Jules", "Nia", "Pip"]

KNOWLEDGE = {
    "zoom": [("What does zoom mean?", "Zoom means to move very fast or quickly across a space.")],
    "tilt": [("What does tilt mean?", "Tilt means to lean or slant to one side instead of standing straight.")],
    "magic": [("What is magic in a story?", "Magic in a story is a special pretend power that can make unusual things happen.")],
    "inner_monologue": [("What is an inner monologue?", "An inner monologue is the little voice in a character's head that thinks and talks quietly.")],
    "superhero": [("What is a superhero?", "A superhero is a brave character who helps others and tries to do the right thing.")],
}
KNOWLEDGE_ORDER = ["zoom", "tilt", "magic", "inner_monologue", "superhero"]


def valid_story_params() -> list[StoryParams]:
    out = []
    for plan, prop in valid_combos():
        out.append(StoryParams(plan=plan, prop=prop, sidekick=SIDEKICKS[0], parent="mother", delay=0))
    return out


def explain_rejection(plan: str, prop: Prop) -> str:
    return f"(No story: the plan '{plan}' does not fit this prop in a sensible superhero scene.)"


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLANS:
        lines.append(asp.fact("plan", p))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        if prop.magic:
            lines.append(asp.fact("magic_prop", pid))
        if prop.safe:
            lines.append(asp.fact("safe_prop", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, G) :- plan(P), prop(G), (magic_prop(G); safe_prop(G)).
safe_outcome(P) :- plan(P), P = zoom.
safe_outcome(P) :- plan(P), P = tilt.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a != b:
        rc = 1
        print("MISMATCH in valid combos:")
        print(" only in asp:", sorted(a - b))
        print(" only in python:", sorted(b - a))
    else:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(plan=None, prop=None, sidekick=None, parent=None, delay=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"FAILED: generate() smoke test crashed: {exc}")
    return rc


def resolve_params_from_defaults(rng: random.Random) -> StoryParams:
    args = argparse.Namespace(plan=None, prop=None, sidekick=None, parent=None, delay=None)
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.plan is None or c[0] == args.plan)
              and (args.prop is None or c[1] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    plan, prop = rng.choice(sorted(combos))
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(plan, prop, sidekick, parent, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for plan in PLANS:
        for prop_id, prop in PROPS.items():
            if reasonableness_ok(plan, prop):
                combos.append((plan, prop_id))
    return combos


CURATED = [
    StoryParams("zoom", "drone", "Mina", "mother", 0),
    StoryParams("tilt", "cape", "Jules", "father", 0),
    StoryParams("tilt", "orb", "Nia", "mother", 1),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for p, g in asp_valid_combos():
            print(f"  {p:5} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
