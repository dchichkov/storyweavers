#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/shack_slate_cautionary_nursery_rhyme.py
========================================================================

A small, self-contained story world for a cautionary nursery-rhyme style tale
about a child near a shack, a slate, and a risky choice that gets corrected.

Premise
-------
A child uses a slate as a toy near a little shack. The slate is fine for writing,
but not for climbing, throwing, or propping things open. A careless choice can
scrape, crack, or startle, and a wiser helper turns the moment into a calm,
cautionary lesson. The ending should feel like a nursery rhyme: simple rhythm,
repetition, concrete images, and a clear "don't do that" turn.

The world simulates:
- two children or a child and a caregiver
- a shack, a slate, and a nearby surface or shelf
- a risky action with tangible physical consequences
- an adult-safe correction or, for a few curated variants, a mild mishap

The prose is state-driven: meters and memes accumulate, helpers react to danger,
and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/shack_slate_cautionary_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4-mini/shack_slate_cautionary_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4-mini/shack_slate_cautionary_nursery_rhyme.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/shack_slate_cautionary_nursery_rhyme.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    low: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Slate:
    id: str
    label: str
    phrase: str
    can_crack: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Risk:
    id: str
    label: str
    danger: int
    fix_power: int
    caution: str
    fail_caution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child", "helper"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    slate: str
    risk: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    tone: str = "nursery"
    outcome: str = "safe"  # safe | scrape | crack
    seed: Optional[int] = None


PLACES = {
    "shack": Place(id="shack", label="the shack", low=True, tags={"shack"}),
    "yard": Place(id="yard", label="the yard", low=True, tags={"yard"}),
    "porch": Place(id="porch", label="the porch", low=True, tags={"porch"}),
}

SLATES = {
    "school_slate": Slate(id="school_slate", label="slate", phrase="a little slate", can_crack=True, tags={"slate"}),
    "writing_slate": Slate(id="writing_slate", label="slate board", phrase="a flat writing slate", can_crack=True, tags={"slate"}),
}

RISKS = {
    "throw": Risk(id="throw", label="throw it", danger=2, fix_power=3,
                  caution="A slate can chip and fly from your hand.",
                  fail_caution="A thrown slate can crack and scrape a finger.",
                  tags={"slate", "throw"}),
    "lean": Risk(id="lean", label="lean it", danger=1, fix_power=2,
                 caution="A slate can slide if it leans against a door.",
                 fail_caution="A leaning slate can bump and fall.",
                 tags={"slate", "lean"}),
    "climb": Risk(id="climb", label="climb with it", danger=3, fix_power=4,
                  caution="A slate is no stepping stone.",
                  fail_caution="A slate under a foot can slip and crack.",
                  tags={"slate", "climb"}),
}

CHILD_NAMES = ["Mina", "Lina", "Toby", "Pippa", "Nell", "Benny", "Milo", "Cora"]
HELPER_NAMES = ["Mum", "Dad", "Gran", "Pa", "Aunt May"]


def hazard_at_risk(place: Place, risk: Risk, slate: Slate) -> bool:
    return place.low and slate.can_crack and risk.danger >= 1


def sensible_risks() -> list[Risk]:
    return list(RISKS.values())


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid in PLACES:
        for sid in SLATES:
            for rid in RISKS:
                if hazard_at_risk(PLACES[pid], RISKS[rid], SLATES[sid]):
                    out.append((pid, sid, rid))
    return out


def would_avert(params: StoryParams) -> bool:
    return params.outcome == "safe"


def should_crack(params: StoryParams) -> bool:
    return params.outcome == "crack"


def _r_scare(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["scrape"] >= THRESHOLD or child.meters["crack"] >= THRESHOLD:
        sig = ("scare",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["fear"] += 1
        out.append("__scare__")
    return out


CAUSAL_RULES = [("scare", _r_scare)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, risk: Risk) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["scrape"] += 1 if risk.danger >= 1 else 0
    if risk.danger >= 3:
        child.meters["crack"] += 1
    propagate(sim, narrate=False)
    return {"scrape": child.meters["scrape"] >= THRESHOLD, "crack": child.meters["crack"] >= THRESHOLD}


def setup(world: World, child: Entity, helper: Entity, place: Place, slate: Slate) -> None:
    child.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{child.id} sat by {place.label}, tapping the {slate.label} in a nursery-rhyme way. "
        f"{child.id} hummed a soft little song."
    )
    world.say(
        f"{helper.id} watched with a gentle eye, for near the shack, the day was small and still."
    )


def warning(world: World, child: Entity, helper: Entity, risk: Risk, slate: Slate) -> None:
    child.memes["want"] += 1
    pred = predict(world, risk)
    world.facts["pred"] = pred
    if pred["crack"]:
        world.say(
            f'"Dear {child.id}, dear {child.id}," said {helper.id}, '
            f'"do not {risk.label}. {risk.caution} Keep your feet on the ground and your hands held tight."'
        )
    else:
        world.say(
            f'"Dear {child.id}, dear {child.id}," said {helper.id}, '
            f'"do not play rough with the {slate.label}. {risk.caution}"'
        )


def choose(world: World, child: Entity, risk: Risk, helper: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But {child.id} said, \"I can do it quick, I can do it neat,\" and reached for the {risk.label}."
    )


def accident(world: World, child: Entity, risk: Risk, slate: Slate) -> None:
    if risk.danger >= 2:
        child.meters["scrape"] += 1
    if risk.danger >= 3:
        child.meters["crack"] += 1
    propagate(world, narrate=False)
    if should_crack(world.facts["params"]):
        world.say(
            f"The {slate.label} slipped with a click and a clack, and one tiny corner cracked."
        )
    else:
        world.say(
            f"The {slate.label} skidded and scratched a little line, but no worse was done."
        )


def fix(world: World, helper: Entity, child: Entity, risk: Risk, slate: Slate) -> None:
    helper.memes["relief"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{helper.id} came close and picked up the {slate.label} with care. "
        f'\"A slate is for drawing and saying words, not for {risk.label},\" {helper.id} said.'
    )
    world.say(
        f"Then {helper.id} placed it flat on the table, safe as a still moon."
    )


def ending(world: World, child: Entity, helper: Entity, slate: Slate, place: Place) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} nodded and tucked both hands behind the back. "
        f"The {slate.label} stayed still, and the little shack was quiet again."
    )
    world.say(
        f"So near the shack, by the soft gray slate, {child.id} learned to be careful and slow."
    )


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    place = PLACES[params.place]
    slate = SLATES[params.slate]
    risk = RISKS[params.risk]
    world.facts["params"] = params

    setup(world, child, helper, place, slate)
    world.para()
    warning(world, child, helper, risk, slate)
    if would_avert(params):
        world.say(
            f"{child.id} listened at once, and set the {slate.label} down before any trouble could start."
        )
        ending(world, child, helper, slate, place)
    else:
        choose(world, child, risk, helper)
        world.para()
        accident(world, child, risk, slate)
        world.say(
            f"{helper.id} opened the palm and checked the spot, then breathed out a steady sigh."
        )
        fix(world, helper, child, risk, slate)
        ending(world, child, helper, slate, place)
    world.facts.update(child=child, helper=helper, place=place, slate=slate, risk=risk)
    return world


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a gentle cautionary nursery rhyme about {p.child} near a shack and a slate.",
        f"Tell a small story in rhyme where {p.helper} warns {p.child} not to {RISKS[p.risk].label} with the slate.",
        f"Write a child-facing cautionary tale that includes the words shack and slate, and ends safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    risk = world.facts["risk"]
    child = world.facts["child"]
    helper = world.facts["helper"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.id} by the shack, with a slate in hand, and {helper.id} watching kindly nearby. The little scene turned into a cautionary lesson about using the slate the right way.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id}?",
            answer=f"{helper.id} warned {child.id} because {RISKS[p.risk].caution} That made the slate risky to handle rough, so the warning came before trouble could grow.",
        ),
    ]
    if p.outcome == "safe":
        qa.append(QAItem(
            question="How did the story end?",
            answer=f"{child.id} listened, put the slate down, and stayed safe beside the shack. The ending image shows the slate still and the child calm, which proves the warning worked.",
        ))
    else:
        qa.append(QAItem(
            question="What happened after the child ignored the warning?",
            answer=f"The slate slipped and made a small scrape or crack, but {helper.id} fixed the moment right away. The child learned the caution in a gentle way and kept the slate on the table after that.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slate?",
            answer="A slate is a flat board or stone used for writing or drawing. It is useful when handled gently, but it can crack if it is dropped or thrown.",
        ),
        QAItem(
            question="What should you do if something seems risky to hold near a little shack?",
            answer="Stop and listen to a grown-up or helper right away. Careful hands keep the day safe, and that is the bravest choice in a cautionary tale.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    parts.append(f"  fired rules: {sorted(n for n, _ in CAUSAL_RULES)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(place="shack", slate="school_slate", risk="throw", child="Mina", child_gender="girl", helper="Mum", helper_gender="woman", outcome="safe"),
    StoryParams(place="yard", slate="writing_slate", risk="lean", child="Toby", child_gender="boy", helper="Dad", helper_gender="man", outcome="scrape"),
    StoryParams(place="porch", slate="school_slate", risk="climb", child="Cora", child_gender="girl", helper="Gran", helper_gender="woman", outcome="crack"),
]


def explain_rejection() -> str:
    return "(No story: this small world only tells cautionary tales when the slate and place make a real, gentle risk.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid in SLATES:
        lines.append(asp.fact("slate", sid))
        lines.append(asp.fact("can_crack", sid))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("danger", rid, r.danger))
    lines.append(asp.fact("low_place", "shack"))
    lines.append(asp.fact("low_place", "yard"))
    lines.append(asp.fact("low_place", "porch"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, S, R) :- place(P), slate(S), risk(R), low_place(P), can_crack(S), danger(R, D), D >= 1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python-only:", sorted(py - cl))
        print("clingo-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, slate=None, risk=None, child=None, child_gender=None, helper=None, helper_gender=None, tone=None, outcome=None, seed=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary nursery-rhyme story world about a shack and a slate.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--slate", choices=SLATES)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", dest="helper_gender", choices=["woman", "man"])
    ap.add_argument("--tone", choices=["nursery"], default="nursery")
    ap.add_argument("--outcome", choices=["safe", "scrape", "crack"])
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
    place = args.place or rng.choice(list(PLACES))
    slate = args.slate or rng.choice(list(SLATES))
    risk = args.risk or rng.choice(list(RISKS))
    if not hazard_at_risk(PLACES[place], RISKS[risk], SLATES[slate]):
        raise StoryError(explain_rejection())
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("woman" if child_gender == "girl" else "man")
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    outcome = args.outcome or rng.choice(["safe", "scrape", "crack"])
    return StoryParams(place=place, slate=slate, risk=risk, child=child, child_gender=child_gender, helper=helper, helper_gender=helper_gender, tone="nursery", outcome=outcome)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.slate not in SLATES or params.risk not in RISKS:
        raise StoryError("Invalid StoryParams keys.")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, slate, risk) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
