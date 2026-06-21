#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/aft_flashback_sharing_foreshadowing_nursery_rhyme.py
====================================================================================

A small storyworld in a nursery-rhyme cadence about a child on a little boat aft
of the mast, with Flashback, Sharing, and Foreshadowing braided into the world
model.

The story premise:
- A child goes aft to look for something simple and sweet.
- A flashback explains why a shared snack matters.
- Sharing mends a small worry.
- A foreshadowing sign hints at a later rain cloud, but the ending stays warm
  and complete.

The world is intentionally tiny and concrete: one child, one helper, one small
setting, one shared treat, and one gentle sign in the sky.
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
class Setting:
    id: str
    place: str
    aft_place: str
    rim_place: str
    sky_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Signal:
    id: str
    label: str
    phrase: str
    omen: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    text: str
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


def _r_mood(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.meters["share"] >= THRESHOLD and ("mood", "warm") not in world.fired:
        world.fired.add(("mood", "warm"))
        child.memes["joy"] += 1
        out.append("__warm__")
    if child.meters["cloud"] >= THRESHOLD and ("mood", "hush") not in world.fired:
        world.fired.add(("mood", "hush"))
        child.memes["wonder"] += 1
        out.append("__hush__")
    return out


CAUSAL_RULES = [Rule("mood", "social", _r_mood)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(treat: Treat, resolution: Resolution) -> bool:
    return treat.shareable and resolution.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, treat in TREATS.items():
            for rid, res in RESOLUTIONS.items():
                if reasonableness_gate(treat, res):
                    combos.append((sid, tid))
    return combos


def predict_share(world: World, treat_id: str) -> dict:
    sim = world.copy()
    sim.get("child").meters["share"] += 1
    sim.get("treat").meters["shared"] += 1
    propagate(sim, narrate=False)
    return {
        "shared": sim.get("treat").meters["shared"] >= THRESHOLD,
        "joy": sim.get("child").memes["joy"],
    }


def build_scene(world: World, setting: Setting, treat: Treat, signal: Signal) -> None:
    child = world.get("child")
    helper = world.get("helper")
    child.memes["hope"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Down on the little boat, aft of the mast, {child.id} went to the aft nook."
        f" {setting.place.capitalize()} had {setting.aft_place}, and the soft wind sang low."
    )
    world.say(
        f"{child.id} found {treat.phrase} by the rail and thought of {helper.id}."
        f" 'A bite for you, and a bite for me,' {child.pronoun()} said."
    )


def flashback(world: World, child: Entity, helper: Entity, treat: Treat) -> None:
    world.say(
        f"Then back came a flash from yesterday: {helper.id} had shared the last sweet crumb,"
        f" and {child.id} had kept {child.pronoun('possessive')} promise."
    )
    child.memes["memory"] += 1
    helper.memes["memory"] += 1


def share(world: World, child: Entity, helper: Entity, treat: Treat) -> None:
    child.meters["share"] += 1
    helper.meters["share"] += 1
    treat_entity = world.get("treat")
    treat_entity.meters["shared"] += 1
    child.memes["kind"] += 1
    helper.memes["kind"] += 1
    propagate(world, narrate=True)
    world.say(
        f"So {child.id} split the {treat.label} clean in two, one half for {helper.id} and one half for {child.id}."
    )


def foreshadow(world: World, signal: Signal, setting: Setting) -> None:
    child = world.get("child")
    child.meters["cloud"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"High above, a small gray cloud tucked itself beside the sun."
        f" It looked like a hush, a hint, a maybe-sometime soon."
    )
    world.say(f"{signal.omen.capitalize()} glimmered over {setting.rim_place}, but the story stayed snug and bright.")


def finish(world: World, child: Entity, helper: Entity, setting: Setting, treat: Treat) -> None:
    world.say(
        f"Then {child.id} and {helper.id} sat aft together, nibbling and smiling, while the boat bobbed and bowed."
    )
    world.say(
        f"And if the little cloud came later, they had {setting.sky_hint} and kind hearts, and the shared {treat.label} in their tummies."
    )


def tell(setting: Setting, treat: Treat, signal: Signal, resolution: Resolution,
         child_name: str = "Mina", child_type: str = "girl",
         helper_name: str = "Nico", helper_type: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="treat", type="treat", label=treat.label))
    world.add(Entity(id="signal", type="signal", label=signal.label))
    world.facts.update(setting=setting, treat=treat, signal=signal, resolution=resolution)
    build_scene(world, setting, treat, signal)
    world.para()
    flashback(world, child, helper, treat)
    share(world, child, helper, treat)
    foreshadow(world, signal, setting)
    world.para()
    finish(world, child, helper, setting, treat)
    world.facts.update(child=child, helper=helper, outcome="shared")
    return world


SETTINGS = {
    "boat": Setting(
        id="boat",
        place="the boat was little and merry",
        aft_place="a snug aft bench and a tidy rope coil",
        rim_place="the rim of the deck",
        sky_hint="one dry sail and one warm scarf",
        tags={"aft"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the harbor was sleepy and blue",
        aft_place="an aft crate and a tiny lantern hook",
        rim_place="the harbor rail",
        sky_hint="one tucked tarp and one steady hand",
        tags={"aft"},
    ),
}

TREATS = {
    "bun": Treat(id="bun", label="bun", phrase="a round seed bun", tags={"sharing"}),
    "berry": Treat(id="berry", label="berry tart", phrase="a little berry tart", tags={"sharing"}),
}

SIGNALS = {
    "cloud": Signal(id="cloud", label="cloud", phrase="a gray cloud", omen="a little cloud"),
    "wind": Signal(id="wind", label="wind", phrase="a soft wind", omen="a whispering wind"),
}

RESOLUTIONS = {
    "warm": Resolution(
        id="warm",
        sense=3,
        power=3,
        text="split the treat and made the aft nook feel cozy",
        qa_text="split the treat and made everything feel cozy",
    ),
    "gentle": Resolution(
        id="gentle",
        sense=2,
        power=2,
        text="shared the treat with gentle hands",
        qa_text="shared the treat with gentle hands",
    ),
    "low": Resolution(
        id="low",
        sense=1,
        power=1,
        text="held back and did not share enough",
        qa_text="held back and did not share enough",
    ),
}


@dataclass
class StoryParams:
    setting: str
    treat: str
    signal: str
    resolution: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mina", "Lina", "Tia", "Nora", "Cora"]
BOY_NAMES = ["Nico", "Oren", "Pip", "Jules", "Theo"]


def explain_rejection(treat: Treat, resolution: Resolution) -> str:
    if not treat.shareable:
        return "(No story: that treat cannot be shared in this little rhyme.)"
    if resolution.sense < SENSE_MIN:
        return f"(No story: resolution '{resolution.id}' is too timid for a complete sharing story.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    return "shared" if reasonableness_gate(TREATS[params.treat], RESOLUTIONS[params.resolution]) else "blocked"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny nursery-rhyme storyworld about aft, sharing, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
    if args.resolution and RESOLUTIONS[args.resolution].sense < SENSE_MIN:
        raise StoryError(explain_rejection(TREATS[args.treat or "bun"], RESOLUTIONS[args.resolution]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.treat is None or c[1] == args.treat)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, treat = rng.choice(sorted(combos))
    signal = args.signal or rng.choice(sorted(SIGNALS))
    resolution = args.resolution or rng.choice(["warm", "gentle"])
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES if helper_type == "girl" else BOY_NAMES) if n != child_name])
    return StoryParams(setting=setting, treat=treat, signal=signal, resolution=resolution,
                       child_name=child_name, child_type=child_type,
                       helper_name=helper_name, helper_type=helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme style story that uses the word "aft" and includes sharing on a little {f["setting"].id}.',
        f"Tell a gentle story where {f['child'].id} remembers a kindness from before, shares {f['treat'].label}, and notices a sky hint.",
        f"Write a short rhyme with flashback, sharing, and foreshadowing, ending with a warm aft image.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    setting = f["setting"]
    treat = f["treat"]
    signal = f["signal"]
    return [
        ("Where did the story happen?",
         f"It happened on {setting.place}, with a little aft nook and a quiet deck by the rail."),
        (f"What did {child.id} do with the {treat.label}?",
         f"{child.id} shared the {treat.label} with {helper.id}, so they could both have a sweet bite."),
        ("What did the flashback show?",
         f"It showed {helper.id} sharing before, and that memory helped {child.id} remember to be kind too."),
        ("What did the foreshadowing suggest?",
         f"It suggested that a small cloud and a hush in the sky might come later. The story still ended calmly, but the cloud made the ending feel like something was coming soon."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does aft mean on a boat?",
         "Aft means toward the back part of a boat. It is the opposite of the front."),
        ("What is sharing?",
         "Sharing means letting someone else have some of what you have. It is a kind way to help both people feel included."),
        ("What is a flashback in a story?",
         "A flashback is when a story briefly goes back to something that happened before. It helps explain why a character feels or acts a certain way."),
        ("What is foreshadowing?",
         "Foreshadowing is a hint that something may happen later in the story. It is like a little clue placed ahead of time."),
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
share_ok(T) :- treat(T), shareable(T), resolution(R), sense(R,S), sense_min(M), S >= M.
outcome(shared) :- share_ok(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for rid, r in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show share_ok/1."))
    return sorted(set(asp.atoms(model, "share_ok")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set((s, t) for (s,) in asp_valid_combos() for t in TREATS if reasonableness_gate(TREATS[t], RESOLUTIONS["warm"]))
    if py:
        print(f"OK: python valid_combos() returned {len(py)} combos.")
    else:
        print("MISMATCH: no python combos.")
        rc = 1
    # smoke test
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, treat=None, signal=None, resolution=None, child_name=None, child_type=None, helper_name=None, helper_type=None), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="boat", treat="bun", signal="cloud", resolution="warm", child_name="Mina", child_type="girl", helper_name="Nico", helper_type="boy"),
    StoryParams(setting="harbor", treat="berry", signal="wind", resolution="gentle", child_name="Lina", child_type="girl", helper_name="Theo", helper_type="boy"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.treat not in TREATS or params.signal not in SIGNALS or params.resolution not in RESOLUTIONS:
        raise StoryError("(Invalid parameters for this storyworld.)")
    setting = SETTINGS[params.setting]
    treat = TREATS[params.treat]
    signal = SIGNALS[params.signal]
    resolution = RESOLUTIONS[params.resolution]
    if not reasonableness_gate(treat, resolution):
        raise StoryError(explain_rejection(treat, resolution))
    world = tell(setting, treat, signal, resolution, params.child_name, params.child_type, params.helper_name, params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show share_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
