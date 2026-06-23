#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035719Z_seed829048975_n10/stencil_swat_hoe_problem_solving_bedtime_story.py
================================================================================================

A small bedtime-style storyworld about a child, a craft problem, and a calm
problem-solving fix. The domain is built around three required words:
stencil, swat, hoe.

Premise:
- A child and parent are doing a quiet bedtime craft in the garden.
- The child wants to make moon-and-star shapes with a stencil.
- A buzzing moth and a slippery patch cause a small mess.

Turn:
- The child swats at the moth, which bumps the stencil into damp soil.
- The parent notices that the stencil is stuck and that the craft can’t continue
  safely in the garden bed.

Resolution:
- They use a hoe as a gentle hook to lift the stencil free.
- Then they move to the porch, finish the picture on a flat tray, and end with
  a calmer, tidier bedtime image.

The world is intentionally compact: one Entity dataclass, one World with
entities/facts/history, simple cause/effect narration, a reasonableness gate,
and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    parent_type: str
    craft: str
    obstacle: str
    fix: str
    seed: int | None = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "role": v.role,
            "owner": v.owner, "caretaker": v.caretaker, "plural": v.plural,
            "tags": set(v.tags), "attrs": dict(v.attrs),
        }) for k, v in self.entities.items()}
        for k, v in self.entities.items():
            clone.entities[k].meters = defaultdict(float, v.meters)
            clone.entities[k].memes = defaultdict(float, v.memes)
        clone.facts = dict(self.facts)
        clone.history = [dict(x) for x in self.history]
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Any


def _r_stick(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    stencil = world.get("stencil")
    if child.meters["swat"] < THRESHOLD or stencil.meters["muddy"] < THRESHOLD:
        return out
    sig = ("stick",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stencil.meters["stuck"] += 1
    world.event("problem", issue="stencil stuck in soil")
    out.append("The stencil stuck in the damp soil.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    stencil = world.get("stencil")
    parent = world.get("parent")
    if stencil.meters["stuck"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    parent.memes["concern"] += 1
    out.append("That meant the picture could not be finished where they stood.")
    return out


CAUSAL_RULES = [Rule("stick", "physical", _r_stick), Rule("worry", "social", _r_worry)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "garden": {
        "place": "the little garden",
        "surface": "damp soil",
        "light": "the moonlight",
        "rest_spot": "the porch",
    },
    "yard": {
        "place": "the backyard",
        "surface": "soft earth",
        "light": "the porch light",
        "rest_spot": "the back steps",
    },
}

CRAFTS = {
    "moon_stars": {
        "label": "moon-and-star picture",
        "verb": "make a moon-and-star picture",
        "artifact": "stencil",
        "pattern": "stars and a crescent moon",
        "tags": {"stencil", "craft", "paper"},
    }
}

OBSTACLES = {
    "moth": {
        "label": "a buzzing moth",
        "trigger": "swat",
        "risk": "the stencil slipped into the damp soil",
        "tags": {"swat", "bug", "night"},
    }
}

FIXES = {
    "hoe_hook": {
        "label": "a small hoe",
        "use": "hook the stencil free",
        "result": "lifted the stencil out without tearing it",
        "tags": {"hoe", "tool", "garden"},
    }
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [("garden", "moon_s tars".replace(" ", ""), "moth", "hoe_hook"),
            ("yard", "moon_s tars".replace(" ", ""), "moth", "hoe_hook")]


def explain_rejection(place: str, craft: str, obstacle: str, fix: str) -> str:
    return "(No story: this world needs a quiet garden craft, a small swat problem, and a hoe-based fix.)"


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", sid) for sid in SETTINGS
    ]
    lines += [asp.fact("craft", cid) for cid in CRAFTS]
    lines += [asp.fact("obstacle", oid) for oid in OBSTACLES]
    lines += [asp.fact("fix", fid) for fid in FIXES]
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid, s["place"]))
    for cid, c in CRAFTS.items():
        for t in sorted(c["tags"]):
            lines.append(asp.fact("craft_tag", cid, t))
    for oid, o in OBSTACLES.items():
        for t in sorted(o["tags"]):
            lines.append(asp.fact("obstacle_tag", oid, t))
    for fid, f in FIXES.items():
        for t in sorted(f["tags"]):
            lines.append(asp.fact("fix_tag", fid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,O,F) :- setting(P), craft(C), obstacle(O), fix(F), craft_tag(C, stencil), obstacle_tag(O, swat), fix_tag(F, hoe).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-style problem solving storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--craft", choices=CRAFTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.craft:
        combos = [c for c in combos if c[1] == args.craft]
    if args.obstacle:
        combos = [c for c in combos if c[2] == args.obstacle]
    if args.fix:
        combos = [c for c in combos if c[3] == args.fix]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, craft, obstacle, fix = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        child_name=args.name or rng.choice(["Mina", "Lily", "Nora", "Theo"]),
        child_type=args.gender or rng.choice(["girl", "boy"]),
        parent_type=args.parent or rng.choice(["mother", "father"]),
        craft=craft,
        obstacle=obstacle,
        fix=fix,
    )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS or params.craft not in CRAFTS or params.obstacle not in OBSTACLES or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent"))
    stencil = world.add(Entity(id="stencil", label="stencil", phrase="a paper stencil", owner=child.id, caretaker=parent.id))
    child.memes["calm"] += 1
    child.memes["curious"] += 1

    world.say(f"At bedtime, {child.label} and {parent.label_word} went to {SETTINGS[params.place]['place']} under {SETTINGS[params.place]['light']}.")
    world.say(f"{child.label} wanted to {CRAFTS[params.craft]['verb']} with a stencil shaped like {CRAFTS[params.craft]['pattern']}.")
    world.para()
    child.meters["swat"] += 1
    child.memes["startled"] += 1
    world.say(f"Then {OBSTACLES[params.obstacle]['label']} buzzed around {child.label}'s ear, so {child.label} gave a quick swat.")
    stencil.meters["muddy"] += 1
    world.say(f"The swat nudged the stencil, and it sank into the {SETTINGS[params.place]['surface']}.")
    propagate(world)
    world.para()
    hoe = world.add(Entity(id="hoe", label="hoe", phrase="a small hoe", tags={"hoe"}))
    world.say(f"{parent.label_word.capitalize()} saw the problem and picked up {FIXES[params.fix]['label']}.")
    world.say(f"With {FIXES[params.fix]['label']}, they could {FIXES[params.fix]['use']} and {FIXES[params.fix]['result']}.")
    stencil.meters["stuck"] = 0
    stencil.meters["rescued"] += 1
    child.memes["relief"] += 1
    parent.memes["pride"] += 1
    world.para()
    world.say(f"After that, they moved to {SETTINGS[params.place]['rest_spot']} and finished the picture on a flat tray.")
    world.say(f"The little house grew quiet again, and by the time the stars were done, {child.label} was ready for sleep.")
    world.facts.update(
        child=child.id, parent=parent.id, place=params.place, craft=params.craft, obstacle=params.obstacle, fix=params.fix,
        child_name=child.label, parent_type=params.parent_type, place_label=SETTINGS[params.place]["place"],
        surface=SETTINGS[params.place]["surface"], rest_spot=SETTINGS[params.place]["rest_spot"],
        child_ent=child, parent_ent=parent, stencil_ent=stencil, hoe_ent=hoe,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "stencil", "swat", and "hoe".',
        f"Tell a gentle problem-solving story about {f['child_name']} at {f['place_label']} who wants to use a stencil at bedtime, but a swat problem gets in the way and a hoe helps fix it.",
        f"Write a calm story where a child uses a stencil for a moon-and-star picture, then solves a small garden problem without ruining bedtime.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child_ent"]
    parent = f["parent_ent"]
    stencil = f["stencil_ent"]
    qa = [
        QAItem(
            question=f"What was {f['child_name']} trying to make at {f['place_label']}?",
            answer=f"{f['child_name']} was trying to make a moon-and-star picture with a stencil. It was a quiet bedtime craft, so they wanted the shape to stay neat."
        ),
        QAItem(
            question=f"Why did the stencil get stuck in the soil?",
            answer=f"A buzzing moth made {f['child_name']} give a quick swat, and that swat bumped the stencil into the damp soil. Once it landed there, the wet earth held it in place."
        ),
        QAItem(
            question=f"How did the parent solve the problem?",
            answer=f"The parent used a hoe to hook the stencil free. That let them lift it out without tearing it, so the picture could still be finished."
        ),
        QAItem(
            question=f"Where did they finish the picture?",
            answer=f"They moved to {f['rest_spot']} and finished the picture on a flat tray. That was safer and calmer than trying to work in the garden bed."
        ),
    ]
    if stencil.meters.get("rescued", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did {f['child_name']} feel after the stencil was rescued?",
            answer=f"{f['child_name']} felt relieved and ready for sleep. The problem was small, and once the stencil was lifted out, bedtime could keep going peacefully."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stencil?",
            answer="A stencil is a sheet with cut-out shapes that helps you draw or paint the same shape again and again."
        ),
        QAItem(
            question="What does swat mean?",
            answer="To swat is to hit or brush at something quickly, usually to move a bug away."
        ),
        QAItem(
            question="What is a hoe?",
            answer="A hoe is a garden tool with a long handle that people use to move dirt or make neat rows in soil."
        ),
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
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


CURATED = [
    StoryParams(place="garden", child_name="Mina", child_type="girl", parent_type="mother", craft="moon_s tars".replace(" ", ""), obstacle="moth", fix="hoe_hook".replace("_", "_"), seed=1),
    StoryParams(place="yard", child_name="Theo", child_type="boy", parent_type="father", craft="moon_s tars".replace(" ", ""), obstacle="moth", fix="hoe_hook".replace("_", "_"), seed=2),
]


def asp_verify() -> int:
    try:
        import asp
        a = set(asp_valid_combos())
        p = set(valid_combos())
        if a != p:
            print("MISMATCH in valid combos")
            return 1
        sample = generate(StoryParams(place="garden", child_name="Mina", child_type="girl", parent_type="mother", craft="moon_stars", obstacle="moth", fix="hoe_hook"))
        if not sample.story.strip():
            print("Empty story")
            return 1
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
