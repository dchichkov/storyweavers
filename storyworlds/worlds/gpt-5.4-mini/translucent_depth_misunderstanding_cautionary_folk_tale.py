#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/translucent_depth_misunderstanding_cautionary_folk_tale.py
==========================================================================================

A standalone story world for a small folk-tale cautionary misunderstanding:
a child mistakes a translucent thing for shallow water, ignores a warning
about depth, gets into a risky situation, and a calm helper resolves it with
a safer choice and a lesson.

The world is intentionally narrow: it generates a few constraint-checked
variations around the same premise so the story stays authored, causal, and
child-facing.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "grandmother": "grandmother",
                "grandfather": "grandfather"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    depth_word: str
    warning_image: str
    safe_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    bait: str
    claim: str
    risky_action: str
    mistake: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    method: str
    effect: str
    lesson: str
    qa_text: str
    power: int
    sense: int
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    water = world.get("water")
    if water.meters["rippled"] < THRESHOLD:
        return out
    sig = ("alarm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.entities.values():
        if kid.role in {"child", "helper"}:
            kid.memes["fear"] += 1
    out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def shallow_enough(place: Place, misunderstanding: Misunderstanding) -> bool:
    return "shallow" in misunderstanding.tags and "deep" not in place.tags


def reasonableness_ok(place: Place, misunderstanding: Misunderstanding) -> bool:
    return place.id in PLACES and misunderstanding.id in MISUNDERSTANDINGS


def predict_risk(world: World, place: Place, misunderstanding: Misunderstanding) -> dict:
    sim = world.copy()
    _do_misunderstanding(sim, sim.get("child"), place, misunderstanding, narrate=False)
    return {
        "rippled": sim.get("water").meters["rippled"] >= THRESHOLD,
        "fear": sum(e.memes["fear"] for e in sim.entities.values()),
    }


def _do_misunderstanding(world: World, child: Entity, place: Place,
                         misunderstanding: Misunderstanding, narrate: bool = True) -> None:
    world.get("water").meters["rippled"] += 1
    child.memes["boldness"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, helper: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Long ago, in a small village by the woods, {child.id} and {helper.id} "
        f"went to {place.name} where the water looked calm and still."
    )
    world.say(
        f"The old folk in the village called it a place of {place.depth_word}, "
        f"and its surface was {place.warning_image}."
    )


def wonder(world: World, child: Entity, place: Place, misunderstanding: Misunderstanding) -> None:
    world.say(
        f"{child.id} leaned over the edge and saw the {place.warning_image}. "
        f"Through it, the bottom seemed near enough to touch."
    )
    world.say(
        f'"{misunderstanding.claim}" {child.id} said, and pointed toward the middle.'
    )


def warn(world: World, helper: Entity, child: Entity, place: Place,
         misunderstanding: Misunderstanding) -> None:
    pred = predict_risk(world, place, misunderstanding)
    helper.memes["warning"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'"Child," {helper.id} said, "do not trust every clear thing. '
        f'That water is {place.depth_word}, though it looks {place.warning_image}. '
        f'{misunderstanding.mistake}"'
    )


def defy(world: World, child: Entity, misunderstanding: Misunderstanding) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the child believed {child.pronoun('possessive')} own eyes more than "
        f"the warning, and {misunderstanding.risky_action}."
    )


def mishap(world: World, child: Entity, place: Place, misunderstanding: Misunderstanding) -> None:
    _do_misunderstanding(world, child, place, misunderstanding)
    world.say(
        f"The surface stirred at once, and the clear place gave way to a deeper "
        f"stretch than {child.id} had guessed."
    )
    world.say(
        f"The water rose cold around {child.pronoun('possessive')} knees, and the "
        f"child's smile vanished."
    )


def rescue(world: World, helper: Entity, resolution: Resolution, child: Entity,
           place: Place) -> None:
    world.get("water").meters["rippled"] = 0.0
    helper.memes["calm"] += 1
    body = resolution.effect
    world.say(
        f"{helper.id} came quickly and {body}. "
        f"{resolution.qa_text}."
    )
    world.say(
        f"When the water settled, the village path looked gentle again."
    )


def lesson(world: World, helper: Entity, child: Entity, place: Place,
           misunderstanding: Misunderstanding, resolution: Resolution) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] = 0.0
    world.say("For a little while, nobody spoke.")
    world.say(
        f"Then {helper.id} knelt down beside {child.id} and said, "
        f'"A translucent thing can hide depth. Never step into a place just because '
        f'it looks friendly."'
    )
    world.say(
        f"{child.id} nodded, small and serious, and promised to remember the warning."
    )
    world.say(resolution.lesson)


def ending(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"By sunset, {child.id} was walking home beside {helper.id}, "
        f"and the water behind them shone {place.safe_image} in the last light."
    )


def tell(place: Place, misunderstanding: Misunderstanding, resolution: Resolution,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Grandmother", helper_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    water = world.add(Entity(id="water", label=place.name, type="thing"))
    world.add(Entity(id="bank", label="the bank", type="thing"))

    setup(world, child, helper, place)
    world.para()
    wonder(world, child, place, misunderstanding)
    warn(world, helper, child, place, misunderstanding)
    defy(world, child, misunderstanding)
    world.para()
    mishap(world, child, place, misunderstanding)
    world.para()
    rescue(world, helper, resolution, child, place)
    lesson(world, helper, child, place, misunderstanding, resolution)
    world.para()
    ending(world, child, helper, place)

    world.facts.update(
        child=child, helper=helper, place=place, misunderstanding=misunderstanding,
        resolution=resolution, water=water, outcome="cautionary",
        risk=child.memes["defiance"] >= THRESHOLD, saved=True
    )
    return world


def narrate_prompt(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    return [
        f'Write a cautionary folk tale for a child that uses the words "{place.id}" '
        f'and "translucent" and teaches that clear appearances can hide depth.',
        f"Tell a gentle village story where {f['child'].id} mistakes something "
        f"translucent for something shallow, but a wise elder warns them in time.",
        f"Write a folk-tale-style warning story about depth, with a child who "
        f"learns not to trust a translucent surface too quickly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, place, misunderstanding, resolution = (
        f["child"], f["helper"], f["place"], f["misunderstanding"], f["resolution"]
    )
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who went to the village water and "
         f"had to face a misunderstanding about how deep it was."),
        ("What did the child think at first?",
         f"{child.id} thought the water was shallow because it looked translucent and "
         f"clear. That was the mistake that made the warning matter."),
        ("Why did the helper warn the child?",
         f"{helper.id} knew that a translucent surface can hide depth, so the water "
         f"could be deeper than it looked. The warning was meant to keep the child safe."),
        ("What happened after the child ignored the warning?",
         f"The water rippled and felt suddenly deeper, so {child.id} had to stop and "
         f"listen. The scare showed why the first guess was wrong."),
        ("How did the story end?",
         f"It ended safely, with {child.id} walking home beside {helper.id} after the "
         f"lesson. The ending proves the child learned to respect depth even when the "
         f"surface looked gentle."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place: Place = f["place"]
    return [
        ("What does translucent mean?",
         "Translucent means you can see light or shapes through something, but not "
         "every detail clearly. It can still hide what is really behind it."),
        ("What is depth?",
         "Depth tells you how far down something goes. A place can look flat and still "
         "be much deeper than it appears."),
        ("Why should people be careful around water that looks clear?",
         "Clear water can still be deep, cold, or dangerous in hidden ways. It is wise "
         "to listen to a warning before stepping in."),
        (f"What kind of place was {place.name}?",
         f"It was a village water place that looked {place.warning_image} but was "
         f"known for its {place.depth_word}.")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "pond": Place("pond", "the pond", "old depth", "translucent as glass", "silver",
                  tags={"water", "depth"}),
    "river": Place("river", "the river", "deep current", "translucent and moving", "bright",
                   tags={"water", "depth"}),
    "well": Place("well", "the well", "great depth", "translucent at the rim", "dark",
                  tags={"water", "depth"}),
}

MISUNDERSTANDINGS = {
    "shallow_guess": Misunderstanding(
        "shallow_guess",
        bait="the clear look",
        claim="It looks shallow enough to step into.",
        risky_action="stepped forward toward the middle",
        mistake="Clear water can still hide real depth.",
        tags={"translucent", "depth", "shallow"},
    ),
    "glass_guess": Misunderstanding(
        "glass_guess",
        bait="the glassy shine",
        claim="It looks like a glass floor.",
        risky_action="leaned out to test it with one foot",
        mistake="A smooth shine does not promise a safe bottom.",
        tags={"translucent", "depth", "glass"},
    ),
}

RESOLUTIONS = {
    "sturdy_pole": Resolution(
        "sturdy_pole",
        method="held out a sturdy pole and guided the child back",
        effect="held the child steady and led them to the bank",
        lesson="After that, the child used a stick to test the edge before any step.",
        qa_text="The helper used a sturdy pole and guided the child back to firm ground",
        power=3,
        sense=3,
        tags={"safe"},
    ),
    "rope_walk": Resolution(
        "rope_walk",
        method="tied a rope to a willow tree and helped the child climb back",
        effect="kept the child from slipping while they returned to shore",
        lesson="After that, the child waited for a grown-up before going near deep water.",
        qa_text="The helper tied a rope to a willow tree and helped the child climb back",
        power=2,
        sense=3,
        tags={"safe"},
    ),
}

CURATED = [
    StoryParams("pond", "shallow_guess", "sturdy_pole", "Mina", "girl", "Grandmother"),
    StoryParams("river", "glass_guess", "rope_walk", "Oren", "boy", "Grandfather"),
]


@dataclass
class StoryParams:
    place: str
    misunderstanding: str
    resolution: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str = "grandmother"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, m in MISUNDERSTANDINGS.items():
            for rid, r in RESOLUTIONS.items():
                if place.id and "translucent" in m.tags and "depth" in place.tags and r.sense >= 2:
                    combos.append((pid, mid, rid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary folk tale about translucent depth and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
              and (args.misunderstanding is None or c[1] == args.misunderstanding)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, misunderstanding, resolution = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        misunderstanding=misunderstanding,
        resolution=resolution,
        child_name=args.child_name or rng.choice(["Mina", "Oren", "Nia", "Pavel", "Lina"]),
        child_gender="girl" if (args.child_name or "").lower() in {"mina", "nia", "lina"} else rng.choice(["girl", "boy"]),
        helper_name=args.helper_name or rng.choice(["Grandmother", "Grandfather", "Aunt", "Uncle"]),
        helper_gender="grandmother" if "Grandmother" in (args.helper_name or "Grandmother") else "grandfather",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MISUNDERSTANDINGS[params.misunderstanding],
        RESOLUTIONS[params.resolution],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=narrate_prompt(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
valid(P, M, R) :- place(P), misunderstanding(M), resolution(R),
                  translucent(M), depth_place(P), safe_resolution(R).
outcome(cautionary) :- valid(_, _, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("depth_place", pid))
    for mid in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("translucent", mid))
    for rid in RESOLUTIONS:
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("safe_resolution", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, misunderstanding, resolution) combos:\n")
        for p, m, r in combos:
            print(f"  {p:8} {m:18} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.place} / {p.misunderstanding} / {p.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
