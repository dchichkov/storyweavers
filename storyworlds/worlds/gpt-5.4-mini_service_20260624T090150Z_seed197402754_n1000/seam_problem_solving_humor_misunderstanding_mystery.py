#!/usr/bin/env python3
"""
A small mystery-like story world about a mysterious seam, a funny misunderstanding,
and a gentle problem-solving fix.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little repair shop"
    detail: str = "a bright lamp, a spool rack, and a tiny table"


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    hidden_in: str
    causes: str
    misread_as: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    tool: str
    effect: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return out
    if child.memes.get("worry", 0) < THRESHOLD:
        return out
    sig = ("worry", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["noticed"] = clue.meters.get("noticed", 0) + 1
    out.append("Something about it looked important, and that made the room feel quieter.")
    return out


def _r_misunderstand(world: World) -> list[str]:
    out = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("curiosity", 0) < THRESHOLD:
        return out
    sig = ("misunderstand", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["confused"] = child.memes.get("confused", 0) + 1
    out.append("The clue looked stranger the longer they stared at it.")
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    clue = world.entities.get("clue")
    fix = world.entities.get("fix")
    child = world.entities.get("child")
    if not clue or not fix or not child:
        return out
    if child.memes.get("solving", 0) < THRESHOLD:
        return out
    if clue.meters.get("torn", 0) < THRESHOLD:
        return out
    sig = ("fix", clue.id, fix.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["repaired"] = 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    out.append("Careful hands made the tear small again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_worry, _r_misunderstand, _r_fix):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    clue: str
    fix: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "shop": Setting(place="the little repair shop", detail="a bright lamp, a spool rack, and a tiny table"),
    "attic": Setting(place="the quiet attic", detail="a dusty trunk, a window beam, and a folded chair"),
    "kitchen": Setting(place="the kitchen corner", detail="a chair, a sewing tin, and a bowl of thread"),
}

CLUES = {
    "coat_seam": Clue(
        id="coat_seam",
        label="coat seam",
        phrase="a crooked seam on a coat",
        kind="seam",
        hidden_in="a pile of laundry",
        causes="the coat was tugged too hard",
        misread_as="a secret note",
        tags={"seam", "cloth", "mystery"},
    ),
    "toy_seam": Clue(
        id="toy_seam",
        label="stuffed-toy seam",
        phrase="a tiny loose seam on a stuffed rabbit",
        kind="seam",
        hidden_in="under a chair",
        causes="the rabbit was hugged and tossed all day",
        misread_as="a smile line",
        tags={"seam", "toy", "mystery"},
    ),
    "bag_seam": Clue(
        id="bag_seam",
        label="bag seam",
        phrase="a split seam on a school bag",
        kind="seam",
        hidden_in="inside a backpack pocket",
        causes="the bag carried too many books",
        misread_as="a zipper problem",
        tags={"seam", "bag", "mystery"},
    ),
}

FIXES = {
    "thread": Fix(
        id="thread",
        label="thread and a needle",
        phrase="thread and a needle",
        tool="needle",
        effect="stitch the seam closed",
        guards={"seam"},
    ),
    "patch": Fix(
        id="patch",
        label="a tiny patch",
        phrase="a tiny patch of cloth",
        tool="patch",
        effect="cover the weak place",
        guards={"seam"},
    ),
    "knot": Fix(
        id="knot",
        label="a careful knot",
        phrase="a careful knot of thread",
        tool="thread",
        effect="hold the seam together for now",
        guards={"seam"},
    ),
}

CHILD_NAMES = ["Mina", "Toby", "Nia", "Eli", "Pia", "Noah"]
HELPER_NAMES = ["Grandma", "Uncle Ray", "Aunt Jo", "Dad", "Mom", "Mr. Finn"]
TRAITS = ["curious", "gentle", "brave", "silly", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, f) for s in SETTINGS for c in CLUES for f in FIXES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A seam mystery with humor, misunderstanding, and a fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    fix = args.fix or rng.choice(list(FIXES))
    if clue not in CLUES or fix not in FIXES:
        raise StoryError("Unknown clue or fix.")
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    name = args.name or rng.choice(CHILD_NAMES)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, clue=clue, fix=fix, child_name=name, child_gender=gender,
                       helper_name=helper, helper_gender=helper_gender, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    child_type = params.child_gender
    helper_type = params.helper_gender
    child = world.add(Entity(id="child", kind="character", type=child_type, label=params.child_name, traits=[params.trait]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=params.helper_name))
    clue_cfg = CLUES[params.clue]
    fix_cfg = FIXES[params.fix]
    clue = world.add(Entity(id="clue", label=clue_cfg.label, phrase=clue_cfg.phrase))
    fix = world.add(Entity(id="fix", label=fix_cfg.label, phrase=fix_cfg.phrase))

    child.memes["curiosity"] = 1
    child.memes["worry"] = 1

    world.say(f"{child.label} went into {world.setting.place} with {helper.label}.")
    world.say(f"Under {world.setting.detail.split(',')[0]}, they found {clue.phrase}.")
    world.say(f"It was a mystery because {clue_cfg.misread_as} at first.")
    world.para()
    world.say(f"{child.label} squinted and said, \"Why is this seam acting so sneaky?\"")
    world.say(f"{helper.label} chuckled. \"Maybe it is hiding a tiny story,\" {helper.label.lower()} said.")
    world.say(f"But the clue came from {clue_cfg.causes}, so it really was a problem, not a prank.")
    child.memes["solving"] = 1
    clue.meters["torn"] = 1
    propagate(world)
    world.para()
    world.say(f"{child.label} fetched {fix.phrase} and worked carefully.")
    world.say(f"Together they used the fix to {fix_cfg.effect}.")
    propagate(world)
    world.say(f"In the end, the seam was neat again, and the funny mystery was solved.")
    world.say(f"{child.label} laughed because the clue had looked like one thing and turned out to be another.")
    world.facts.update(
        child=child,
        helper=helper,
        clue=clue,
        fix=fix,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f"Write a short mystery story for a small child about a {CLUES[p.clue].label} in {world.setting.place}.",
        f"Tell a gentle story where {p.child_name} misunderstands a seam, then solves the problem with help.",
        f"Write a funny, child-friendly mystery about {CLUES[p.clue].phrase} and a careful fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    clue: Entity = f["clue"]
    fix: Entity = f["fix"]
    return [
        QAItem(
            question=f"Where did {child.label} find the strange seam?",
            answer=f"{child.label} found it in {world.setting.place}, with {helper.label} nearby.",
        ),
        QAItem(
            question=f"Why did the seam seem mysterious at first?",
            answer=f"It seemed mysterious because it looked like {CLUES[p.clue].misread_as}, even though it really came from {CLUES[p.clue].causes}.",
        ),
        QAItem(
            question=f"What did {child.label} use to fix the seam?",
            answer=f"{child.label} used {fix.phrase} and worked carefully with {helper.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The seam was neat again, the problem was solved, and {child.label} laughed because the mystery had a funny misunderstanding in it.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seam?",
            answer="A seam is the line where pieces of cloth are joined together.",
        ),
        QAItem(
            question="Why can a seam be important?",
            answer="A seam is important because it helps hold clothing, bags, and stuffed toys together.",
        ),
        QAItem(
            question="What does it mean to solve a problem carefully?",
            answer="It means looking closely, choosing a good fix, and doing the repair step by step.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:8} ({e.kind:8}) {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
clue(C) :- clue_id(C).
fix(F) :- fix_id(F).

mystery(C) :- clue(C), seam(C).
misunderstood(C) :- clue(C), misread_as(C, _).
solvable(C, F) :- clue(C), fix(F), guards(F, seam).

% One story is valid when it has a seam clue, a misunderstanding, and a fix.
valid_story(S, C, F) :- setting(S), clue(C), fix(F), seam(C), misunderstood(C), solvable(C, F).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_id", cid))
        lines.append(asp.fact("seam", cid))
        lines.append(asp.fact("misread_as", cid, c.misread_as))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix_id", fid))
        for g in f.guards:
            lines.append(asp.fact("guards", fid, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    model = asp.one_model(asp_program("#show valid_story/3."))
    cl = set(asp.atoms(model, "valid_story"))
    # Normalize to (setting, clue, fix)
    cl_norm = set(cl)
    if py == cl_norm:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo:", sorted(cl_norm))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="shop", clue="coat_seam", fix="thread", child_name="Mina", child_gender="girl",
                helper_name="Grandma", helper_gender="girl", trait="curious"),
    StoryParams(setting="attic", clue="toy_seam", fix="patch", child_name="Toby", child_gender="boy",
                helper_name="Uncle Ray", helper_gender="boy", trait="silly"),
    StoryParams(setting="kitchen", clue="bag_seam", fix="knot", child_name="Nia", child_gender="girl",
                helper_name="Mom", helper_gender="girl", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} valid story triples:")
        for t in triples:
            print(" ", t)
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
            params = resolve_params(args, random.Random(seed))
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.clue} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
