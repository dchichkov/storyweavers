#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/tweezers_twist_repetition_nursery_rhyme.py
======================================================================================================================

A standalone storyworld for a tiny nursery-rhyme-style domain about tweezers,
twists, and repeated careful motion.

Seed premise:
- A child wants to free a small shiny charm from a twist of ribbon.
- Tweezers are the careful tool that can help.
- The story keeps a gentle rhyme-like cadence and repeats key motions.
- A small turn changes the plan: the child learns to turn, pinch, and tug
  softly instead of yanking.

The world model tracks a few typed entities with physical meters and emotional
memes, and it renders state-driven prose rather than a frozen paragraph.
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

_HERE = os.path.abspath(os.path.dirname(__file__))
_ROOT = _HERE
while True:
    if os.path.exists(os.path.join(_ROOT, "results.py")):
        break
    parent = os.path.dirname(_ROOT)
    if parent == _ROOT:
        break
    _ROOT = parent
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: str = ""
    material: str = ""
    color: str = ""
    plural: bool = False
    careful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str
    light: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    twisty: str
    risk: str
    tricky: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    outcome: str
    sense: int
    power: int
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
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
        clone = World(self.scene)
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
    tag: str
    apply: Callable[[World], list[str]]


def _r_pinch(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    hazard = world.entities.get("hazard")
    if not child or not hazard:
        return out
    if child.meters["trying"] < THRESHOLD or hazard.meters["twisted"] < THRESHOLD:
        return out
    sig = ("pinch",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hazard.meters["snagged"] += 1
    child.memes["worry"] += 1
    out.append("The ribbon gave a tiny twist and would not come loose.")
    return out


CAUSAL_RULES = [Rule("pinch", "physical", _r_pinch)]


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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(hazard: Hazard, prize: Entity) -> bool:
    return "twist" in hazard.tags and prize.type in {"charm", "ribbon", "bow", "string"}


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for scene in SCENES:
        for hazard in HAZARDS:
            for prize in PRIZES:
                if hazard_at_risk(HAZARDS[hazard], PRIZES[prize]):
                    out.append((scene, hazard, prize))
    return out


def turn_count(hazard: Hazard, prize: Entity) -> int:
    return 2 if prize.type == "bow" else 1


def can_fix(fix: Fix, hazard: Hazard, prize: Entity) -> bool:
    return hazard.id in fix.tags and hazard_at_risk(hazard, prize)


def choose_fix(hazard: Hazard, prize: Entity) -> Optional[Fix]:
    for fix in FIXES.values():
        if can_fix(fix, hazard, prize):
            return fix
    return None


def predict(world: World, hazard: Hazard, prize_id: str) -> dict[str, bool]:
    sim = world.copy()
    child = sim.get("child")
    prize = sim.get(prize_id)
    child.meters["trying"] += 1
    prize.meters["twisted"] += 1
    propagate(sim, narrate=False)
    return {"snagged": prize.meters["snagged"] >= THRESHOLD}


@dataclass
class StoryParams:
    scene: str
    hazard: str
    prize: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


SCENES = {
    "nursery": Scene(place="the nursery", light="soft lamplight", afford={"twist"}),
    "window_seat": Scene(place="the window seat", light="morning light", afford={"twist"}),
    "playroom": Scene(place="the playroom", light="bright daylight", afford={"twist"}),
}

HAZARDS = {
    "ribbon_knot": Hazard(
        id="ribbon_knot",
        label="twisted ribbon",
        phrase="a twisted ribbon",
        twisty="twist and twine",
        risk="snagged and tangled",
        tricky="tight little loops",
        tags={"twist", "ribbon"},
    ),
    "button_loop": Hazard(
        id="button_loop",
        label="button loop",
        phrase="a button loop",
        twisty="loop and lean",
        risk="snagged and knotted",
        tricky="small stitched loops",
        tags={"twist", "button"},
    ),
}

PRIZES = {
    "charm": Entity(id="charm", kind="thing", type="charm", label="tiny star charm", phrase="a tiny star charm", material="metal", color="gold"),
    "bow": Entity(id="bow", kind="thing", type="bow", label="blue hair bow", phrase="a blue hair bow", material="cloth", color="blue", plural=False),
    "string": Entity(id="string", kind="thing", type="string", label="red string", phrase="a red string", material="thread", color="red"),
}

FIXES = {
    "tweezers": Fix(
        id="tweezers",
        label="tweezers",
        phrase="the tweezers",
        method="pinch, twist, and pull the loop free",
        outcome="freed the little snag one careful tug at a time",
        sense=3,
        power=3,
        tags={"ribbon_knot", "button_loop", "twist"},
    ),
    "fingers": Fix(
        id="fingers",
        label="fingers",
        phrase="bare fingers",
        method="pull hard and hope",
        outcome="pulled too fast and made the knot worse",
        sense=1,
        power=1,
        tags={"twist"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ada", "Ivy", "June"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Finn", "Theo", "Max"]
HELPER_NAMES = ["Mama", "Papa", "Grandma", "Grandpa"]


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about {f["child_name"]} and the {f["prize_phrase"]} that uses the word "tweezers".',
        f"Tell a gentle story where {f['child_name']} tries to fix {f['hazard_phrase']} in {f['scene_place']} and learns a careful twist-and-pinch rhythm.",
        f'Write a repeating, sing-song story where "twist and turn" and "pinch and pull" help free {f["prize_label"]}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child_name"]
    helper = f["helper_name"]
    place = f["scene_place"]
    hazard = f["hazard_phrase"]
    prize = f["prize_phrase"]
    fix = f["fix_label"]
    out: list[QAItem] = [
        QAItem(
            question=f"What was {child} trying to free in {place}?",
            answer=f"{child} was trying to free {prize} from {hazard} in {place}. The little twist made the ribbon feel stuck, so the child had to work carefully.",
        ),
        QAItem(
            question=f"Why did {helper} tell {child} to use {fix}?",
            answer=f"{helper} told {child} to use {fix} because the loops were too tight for a fast yank. The careful tool could pinch the twist and help the charm come loose without breaking anything.",
        ),
    ]
    if f.get("snagged"):
        out.append(QAItem(
            question=f"What happened when {child} tried to pull the twist too hard?",
            answer=f"The ribbon stayed snagged and gave a little twist back. That showed {child} why slow, repeated moves worked better than a hard pull.",
        ))
    if f.get("resolved"):
        out.append(QAItem(
            question=f"How did the story end after {fix} was used?",
            answer=f"{fix.capitalize()} helped free the snag one careful tug at a time. In the end, {prize} was loose and shining, and {child} could smile at the tidy little ribbon again.",
        ))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["hazard_tags"])
    if world.facts.get("resolved"):
        tags.add("tweezers")
    out: list[QAItem] = []
    if "tweezers" in tags:
        out.append(QAItem(
            question="What are tweezers for?",
            answer="Tweezers are a small tool for pinching and picking up little things. People use them when something is tiny, stuck, or needs a careful touch.",
        ))
    if "twist" in tags:
        out.append(QAItem(
            question="What does it mean when something twists?",
            answer="When something twists, it turns around and around. A twist can make a ribbon, string, or loop turn into a little knot.",
        ))
    if "ribbon" in tags:
        out.append(QAItem(
            question="What is a ribbon?",
            answer="A ribbon is a thin strip of cloth. It can be tied, twisted, or used to make a pretty bow.",
        ))
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


def tell(scene: Scene, hazard: Hazard, prize_cfg: Entity, fix: Fix, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World(scene)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    prize = world.add(copy.deepcopy(prize_cfg))
    hazard_ent = world.add(Entity(id="hazard", kind="thing", type="twist", label=hazard.label, phrase=hazard.phrase, attrs={"twisty": hazard.twisty}))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=fix.label, phrase=fix.phrase, careful=True))
    _ = tool

    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    prize.meters["twisted"] += 1
    hazard_ent.meters["twisted"] += 1

    world.say(f"{child_name} was in {scene.place}, under {scene.light}, and the little {prize.label} was caught in {hazard.phrase}.")
    world.say(f"Twist and turn, twist and twine, the tiny loops would not align.")
    world.para()
    child.meters["trying"] += 1
    child.memes["hope"] += 1
    world.say(f'"Oh my," said {helper_name}, "not a yank, not a yank; we need {fix.label} and a gentle rank."')
    if predict(world, hazard, prize.id)["snagged"]:
        child.memes["worry"] += 1
        world.say(f"{child_name} tried a little tug, but the ribbon only sang, 'twist and twirl,' and stayed snug.")
    world.para()
    chosen = choose_fix(hazard, prize)
    if chosen is None:
        raise StoryError("No sensible fix exists for this twist.")
    child.meters["careful"] += 1
    prize.meters["twisted"] += 1
    if chosen.id == "tweezers":
        world.say(f"{helper_name} held up {fix.label} and said, 'Pinch and pull, pinch and pull, till the little loops are full no more.'")
        world.say(f"{child_name} turned the tweezers just so, and the knot began to go.")
        world.say(f"{chosen.outcome.capitalize()}. Soon {prize.label} was free, bright as a bead in the morning breeze.")
        world.say(f"Twist and turn, then smile again; the stuck little charm was loose at last.")
        child.memes["joy"] += 2
        child.memes["relief"] += 1
        world.facts["resolved"] = True
    else:
        raise StoryError("This world expects tweezers as the sensible fix.")

    world.facts.update(
        child_name=child_name,
        helper_name=helper_name,
        scene_place=scene.place,
        hazard_phrase=hazard.phrase,
        hazard_tags=sorted(hazard.tags),
        prize_phrase=prize.phrase,
        prize_label=prize.label,
        fix_label=fix.label,
        snagged=bool(prize.meters["twisted"] >= THRESHOLD),
    )
    return world


ASP_RULES = r"""
hazard_at_risk(H, P) :- twisty(H), prize_like(P).
sensible_fix(tweezers) :- fix(tweezers), sense(tweezers,S), sense_min(M), S >= M.
valid(Scene, H, P) :- scene(Scene), hazard(H), prize_like(P), hazard_at_risk(H, P), sensible_fix(tweezers).
resolved :- chosen_fix(tweezers).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for hid, hz in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("twisty", hid))
        for tag in sorted(hz.tags):
            lines.append(asp.fact("tagged", hid, tag))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize_like", pid))
    for fid, fx in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fx.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between clingo and valid_combos()")
        print("only in clingo:", sorted(clingo_set - python_set))
        print("only in python:", sorted(python_set - clingo_set))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: verify passed ({len(clingo_set)} combos) and smoke story generated.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about tweezers and twists.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.scene is None or c[0] == args.scene)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, hazard, prize = rng.choice(sorted(combos))
    fix = args.fix or "tweezers"
    if fix != "tweezers":
        raise StoryError("This world is built around tweezers as the sensible fix.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != child_name])
    return StoryParams(scene=scene, hazard=hazard, prize=prize, fix=fix, child_name=child_name, child_gender=child_gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    if params.fix != "tweezers":
        raise StoryError("Only tweezers are supported in this seed world.")
    scene = SCENES[params.scene]
    hazard = HAZARDS[params.hazard]
    prize = PRIZES[params.prize]
    fix = FIXES[params.fix]
    world = tell(scene, hazard, prize, fix, params.child_name, params.child_gender, params.helper_name, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.careful:
            bits.append("careful=True")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def _sample_to_obj(sample: StorySample) -> object:
    if hasattr(sample, "to_dict"):
        return sample.to_dict()
    return {
        "params": sample.params.__dict__ if hasattr(sample.params, "__dict__") else sample.params,
        "story": sample.story,
        "prompts": sample.prompts,
        "story_qa": [item.__dict__ for item in sample.story_qa],
        "world_qa": [item.__dict__ for item in sample.world_qa],
    }


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (scene, hazard, prize) combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(scene="nursery", hazard="ribbon_knot", prize="charm", fix="tweezers", child_name="Mina", child_gender="girl", helper_name="Grandma", helper_gender="girl"),
            StoryParams(scene="window_seat", hazard="button_loop", prize="bow", fix="tweezers", child_name="Owen", child_gender="boy", helper_name="Mama", helper_gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            print(json.dumps(_sample_to_obj(samples[0]), indent=2, ensure_ascii=False, default=str))
        else:
            print(json.dumps([_sample_to_obj(s) for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for idx, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
