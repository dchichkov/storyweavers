#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/physical_decal_contaminate_forest_trail_bad_ending.py
===============================================================================================================

A small storyworld for a rhyming, child-facing forest-trail tale with a twist
and a bad ending. The premise is simple: a child on a forest trail finds a shiny
decal, treats it as a physical little treasure, and accidentally contaminates the
trail and a field guide with sticky paint. The twist is that the decal was not a
toy at all but a trail marker that must stay clean and visible; once it is peeled
and smeared, the walk goes wrong in a way the grown-up cannot fully fix.

The domain is intentionally small and constraint-checked. Every story is built
from state, not from a frozen paragraph with swapped nouns, and the ending image
proves what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CLI_CHOICES = ("trail", "damp", "glow", "path")

GIRL_NAMES = ["Mia", "Luna", "Ivy", "Zoe", "Nora"]
BOY_NAMES = ["Theo", "Finn", "Milo", "Eli", "Ben"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: str = ""
    carried_by: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    smell: str
    trail_word: str
    rhythm: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    spill: str
    contaminates: set[str]
    twist: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    kind: str
    vulnerable: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FixCfg:
    id: str
    label: str
    method: str
    can_clean: bool
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "forest_trail": Place("forest_trail", "the forest trail", "pine and moss", "trail", "soft steps", {"forest", "trail"}),
}

PROBLEMS = {
    "decal": Problem("decal", "a bright decal", "sticky paint", {"guide", "sign", "paw"}, "It was a trail marker, not a toy.", {"decal", "physical"}),
    "sticker": Problem("sticker", "a shiny sticker", "sticky paint", {"guide", "sign", "paw"}, "It was a trail marker with a job to do.", {"decal", "physical"}),
    "label": Problem("label", "a glossy label", "sticky paint", {"guide", "sign", "paw"}, "It belonged on a marker post, not in a pocket.", {"decal", "physical"}),
}

OBJECTS = {
    "guide": ObjectCfg("guide", "field guide", "a little field guide", "book", "paper pages", {"guide"}),
    "map": ObjectCfg("map", "trail map", "a folded trail map", "paper", "paper pages", {"map"}),
    "marker": ObjectCfg("marker", "trail marker", "a wooden trail marker", "sign", "painted wood", {"sign"}),
}

FIXES = {
    "cloth": FixCfg("cloth", "soft cloth", "wipe with a soft cloth", True, {"clean"}),
    "water": FixCfg("water", "water bottle", "dab with water and a cloth", True, {"clean"}),
    "leave": FixCfg("leave", "leave it alone", "leave it be", False, {"bad"}),
}

@dataclass
class StoryParams:
    place: str
    problem: str
    object: str
    fix: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}."


def valid_combos() -> list[tuple[str, str, str, str]]:
    rows = []
    for place in PLACES:
        for problem in PROBLEMS:
            for obj in OBJECTS:
                for fix in FIXES:
                    if problem in {"decal", "sticker", "label"} and fix != "leave":
                        rows.append((place, problem, obj, fix))
    return rows


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming forest-trail storyworld with a bad ending and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "ranger"])
    ap.add_argument("--name")
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
    if args.fix and FIXES[args.fix].can_clean is False:
        raise StoryError("That fix would not make a real story; it leaves the mess in place.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.object is None or c[2] == args.object)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, obj, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "ranger"])
    return StoryParams(place=place, problem=problem, object=obj, fix=fix, name=name, gender=gender, helper=helper)


def _entity_story(world: World, p: StoryParams) -> dict[str, Entity]:
    child = world.add(Entity(id="child", kind="character", type=p.gender, label=p.name))
    helper = world.add(Entity(id="helper", kind="character", type=p.helper if p.helper in {"mother", "father"} else "woman", label=p.helper))
    obj = world.add(Entity(id="object", kind="thing", type="thing", label=OBJECTS[p.object].label))
    problem = world.add(Entity(id="problem", kind="thing", type="thing", label=PROBLEMS[p.problem].label))
    sign = world.add(Entity(id="sign", kind="thing", type="thing", label="trail marker"))
    guide = world.add(Entity(id="guide", kind="thing", type="thing", label="field guide"))
    for e in (child, helper, obj, problem, sign, guide):
        e.meters.setdefault("dirty", 0.0)
        e.meters.setdefault("lost", 0.0)
        e.memes.setdefault("worry", 0.0)
        e.memes.setdefault("joy", 0.0)
    return {"child": child, "helper": helper, "object": obj, "problem": problem, "sign": sign, "guide": guide}


def tell(p: StoryParams) -> World:
    world = World(PLACES[p.place])
    ents = _entity_story(world, p)
    child, helper, sign, guide = ents["child"], ents["helper"], ents["sign"], ents["guide"]
    problem = PROBLEMS[p.problem]
    obj = OBJECTS[p.object]
    fix = FIXES[p.fix]
    world.facts.update(params=p, place=world.place, child=child, helper=helper, problem=problem, object_cfg=obj, fix=fix, twist_used=False, ruined=False)

    world.say(f"{p.name} walked the {world.place.label}, light on feet, with the woods all green and bright.")
    world.say(f"{child.pronoun().capitalize()} saw {problem.label} and smiled at the shine, a tiny round gleam in the pine.")
    world.para()
    world.say(f"{child.pronoun().capitalize()} tucked it close with a childish grin; the trail was calm, the day felt thin.")
    world.say(f"But the twist was this: {problem.twist}")

    # contaminate
    world.para()
    child.memes["worry"] += 1
    sign.meters["dirty"] += 1
    guide.meters["dirty"] += 1
    child.meters["dirty"] += 1
    child.meters["lost"] += 1
    world.facts["twist_used"] = True
    world.say(f"With sticky fingers, {child.label} smeared the {problem.label}, and the glossy mess began to spread.")
    world.say(f"The {obj.label} got contaminated too, with {problem.spill} on every page and thread.")
    world.say(f"The trail marker lost its spark and turned dull and gray; the neat little path looked wrong that day.")

    # bad ending
    world.para()
    world.say(f"{helper.label.capitalize()} came at once with a worried face, and used {fix.method} to clean the place.")
    if fix.can_clean:
        world.say(f"But the stain stayed stuck like a stubborn rhyme, and the marker stayed blurred for a long, long time.")
        world.say(f"They left with a torn-up map and a muddy guide, and the forest trail still hid its way inside.")
        world.facts["ruined"] = True
    return world


def story_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a rhyming story set on {world.place.label} about {p.name} finding {PROBLEMS[p.problem].label} and making a sticky mess.",
        f"Tell a child-sized rhyming tale where a trail marker gets contaminated and the ending takes a sad twist.",
        f"Write a forest-trail rhyme using the words physical, decal, and contaminate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    child: Entity = world.facts["child"]
    helper: Entity = world.facts["helper"]
    obj: ObjectCfg = world.facts["object_cfg"]
    problem: Problem = world.facts["problem"]
    qa = [
        QAItem(
            question=f"What did {p.name} find on the forest trail?",
            answer=f"{p.name} found {problem.label} on the forest trail. It looked like a tiny physical treasure, but it was really part of the trail and should have stayed where it was.",
        ),
        QAItem(
            question=f"Why did the {obj.label} get messy?",
            answer=f"It got messy because {child.label} smeared the sticky decal on it. The paint contaminated the pages, so the guide no longer stayed neat and easy to use.",
        ),
        QAItem(
            question=f"Who tried to clean things up at the end?",
            answer=f"{helper.label} tried to clean up with {world.facts['fix'].label}, but the stain would not fully go away. That is why the ending stayed bad instead of turning all the way happy.",
        ),
    ]
    if world.facts.get("twist_used"):
        qa.append(QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the shiny decal was not a toy at all. It was a trail marker, so taking it made the path harder to follow and made the trouble feel much worse.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does physical mean?", "Physical means something you can touch or hold with your hands. A decal or a sticky patch on a trail is physical because it is a real thing, not just a thought."),
        QAItem("What is a decal?", "A decal is a picture or sticker that can be stuck onto a surface. Decals are often shiny and smooth, so they can peel off or smear if they get wet or dirty."),
        QAItem("What does contaminate mean?", "To contaminate something means to make it dirty or mixed with something unwanted. Sticky paint can contaminate a trail marker or a page by leaving a messy mark behind."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    for key in (params.place, params.problem, params.object, params.fix):
        if key not in {"forest_trail", "decal", "sticker", "label", "guide", "map", "marker", "cloth", "water", "leave"}:
            raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=story_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
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


ASP_RULES = r"""
valid(P, PR, O, F) :- place(P), problem(PR), object(O), fix(F), contaminates(PR, O), fix_ok(F).
twist(PR) :- problem(PR), has_twist(PR).
bad_ending(PR) :- problem(PR), twist(PR).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pr_id, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", pr_id))
        if pr.twist:
            lines.append(asp.fact("has_twist", pr_id))
        for tag in pr.contaminates:
            lines.append(asp.fact("contaminates", pr_id, tag))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for f_id, f in FIXES.items():
        lines.append(asp.fact("fix", f_id))
        if f.can_clean:
            lines.append(asp.fact("fix_ok", f_id))
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = 0
    if py != cl:
        print("MISMATCH in valid_combos parity")
        ok = 1
    # smoke test normal generate/emit
    try:
        sample = generate(StoryParams(place="forest_trail", problem="decal", object="guide", fix="cloth", name="Mia", gender="girl", helper="mother"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample)
        if not buf.getvalue().strip():
            print("MISMATCH: emit produced no story")
            ok = 1
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = 1
    if ok == 0:
        print("OK: verification passed.")
    return ok


def asp_valid() -> list[tuple]:
    return asp_valid_combos()


def explain_rejection() -> str:
    return "(No story: this world needs a shiny trail decal, a nearby object to contaminate, and a fix that cannot fully save the day.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.problem is None or c[1] == args.problem)
              and (args.object is None or c[2] == args.object)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, problem, obj, fix = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "ranger"])
    return StoryParams(place=place, problem=problem, object=obj, fix=fix, name=name, gender=gender, helper=helper)


def valid_combos() -> list[tuple[str, str, str, str]]:
    rows = []
    for place in PLACES:
        for problem in PROBLEMS:
            for obj in OBJECTS:
                for fix in FIXES:
                    if FIXES[fix].can_clean:
                        rows.append((place, problem, obj, fix))
    return rows


CURATED = [
    StoryParams(place="forest_trail", problem="decal", object="guide", fix="cloth", name="Mia", gender="girl", helper="ranger"),
    StoryParams(place="forest_trail", problem="sticker", object="map", fix="water", name="Theo", gender="boy", helper="mother"),
    StoryParams(place="forest_trail", problem="label", object="marker", fix="cloth", name="Nora", gender="girl", helper="father"),
    StoryParams(place="forest_trail", problem="decal", object="marker", fix="water", name="Eli", gender="boy", helper="ranger"),
]


def generation_prompts(sample: StorySample) -> list[str]:
    return sample.prompts


def generate_storysample(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid())} compatible combos:\n")
        for row in asp_valid():
            print("  ", row)
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
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
