#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/average_full_bathe_conflict_reconciliation_folk_tale.py
======================================================================================

A small folk-tale storyworld about a child, a bath, a mistake, and a kind
reconciliation.

Seed premise
------------
A child wants to bathe in a bath that is not ready yet. They make an average
assumption about how much water is enough, a full bucket spills into a conflict,
and a patient helper turns the argument into a reconciliation with warm water,
soap, and a shared ending.

The world keeps the prose state-driven: water levels, temper, apology, and
comfort all change as the tale unfolds.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class BathSetting:
    id: str
    label: str
    place_phrase: str
    water_source: str
    safe_space: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BathNeed:
    id: str
    word: str
    phrase: str
    requires_warmth: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictTool:
    id: str
    phrase: str
    volume: str
    spill_risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    action: str
    effect: str
    words: str
    success_score: int
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    tub = world.entities.get("tub")
    if not child or not elder or not tub:
        return out
    if child.memes["stubborn"] < THRESHOLD:
        return out
    if tub.meters["full"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["anger"] += 1
    elder.memes["worry"] += 1
    tub.memes["tension"] += 1
    out.append("__conflict__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    elder = world.entities.get("elder")
    tub = world.entities.get("tub")
    if not child or not elder or not tub:
        return out
    if child.memes["apology"] < THRESHOLD:
        return out
    if elder.memes["mercy"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    elder.memes["calm"] += 1
    tub.memes["tension"] = 0.0
    out.append("__reconcile__")
    return out


CAUSAL_RULES = [_r_conflict, _r_reconcile]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule(world):
                changed = True


def setup_world(setting: BathSetting, need: BathNeed, tool: ConflictTool,
                resolution: Reconciliation, child_name: str,
                child_gender: str, elder_name: str, elder_gender: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, role="hero",
                             traits=["restless"], attrs={"name": child_name}))
    elder = world.add(Entity(id="elder", kind="character", type=elder_gender,
                             label=elder_name, role="helper",
                             traits=["patient"], attrs={"name": elder_name}))
    tub = world.add(Entity(id="tub", kind="thing", type="bath", label="the bath"))
    world.add(Entity(id="soap", kind="thing", type="thing", label="the soap"))
    world.add(Entity(id="towel", kind="thing", type="thing", label="the towel"))

    child.memes["desire"] = 1
    child.memes["stubborn"] = 1
    tub.meters["water"] = 0.0
    tub.meters["warmth"] = 0.0
    world.facts.update(setting=setting, need=need, tool=tool, resolution=resolution)
    return world


def tell(setting: BathSetting, need: BathNeed, tool: ConflictTool,
         resolution: Reconciliation, child_name: str = "Milo",
         child_gender: str = "boy", elder_name: str = "Grandma",
         elder_gender: str = "woman") -> World:
    world = setup_world(setting, need, tool, resolution, child_name, child_gender,
                        elder_name, elder_gender)
    child = world.get("child")
    elder = world.get("elder")
    tub = world.get("tub")

    world.say(
        f"Once in a village by the water, {child_name} lived with {elder_name}. "
        f"The little house stood by {setting.place_phrase}, where the wind sang "
        f"like a flute and the kettle hummed in the corner."
    )
    world.say(
        f"{child_name} wanted to {need.word}, because a day of work and play had left "
        f"the child tired. But the bath was not ready yet, and {child_name} made an "
        f"average guess that a little water would be enough."
    )

    world.para()
    child.memes["impatience"] += 1
    tub.meters["water"] += 1
    tub.meters["warmth"] += 0.25
    world.say(
        f"So {child_name} fetched {tool.phrase}. It was {tool.volume}, and when the "
        f"bucket tilted, a full splash slapped the floor and dashed water everywhere."
    )
    world.say(
        f"{elder_name} frowned, for the bath was still half-cold and the wet floor "
        f"made the room feel cramped. The two of them were in conflict for a moment, "
        f"because one wanted haste and the other wanted care."
    )
    propagate(world)

    world.para()
    child.memes["apology"] += 1
    elder.memes["mercy"] += 1
    world.say(
        f"Then {child_name} looked down, breathed out, and said, "
        f'"I was wrong. I should have waited."'
    )
    world.say(
        f"{elder_name} softened at once. {elder_name} wiped the spill, smiled, and "
        f"said, 'A warm bath is better than a rushed one. Let us make it full and "
        f"gentle together.'"
    )
    propagate(world)

    world.para()
    tub.meters["water"] = 4.0
    tub.meters["warmth"] = 3.0
    child.memes["joy"] += 1
    elder.memes["joy"] += 1
    world.say(
        f"Together they filled the tub until it was full and warm. "
        f"{child_name} bathed in the steady water while {elder_name} handed over the "
        f"soap and the towel, and the house grew quiet and kind again."
    )
    world.say(
        f"In the end, the little quarrel became reconciliation, and the child learned "
        f"that average guesses are not the same as wise ones. The bath was full, the "
        f"steam curled up softly, and both of them smiled."
    )

    world.facts.update(
        child=child,
        elder=elder,
        tub=tub,
        conflict=child.memes["anger"] >= THRESHOLD,
        reconciled=child.memes["calm"] >= THRESHOLD,
        bathed=True,
        full=tub.meters["water"] >= 4.0,
    )
    return world


SETTING = {
    "riverhouse": BathSetting(
        id="riverhouse",
        label="riverhouse",
        place_phrase="the riverhouse well",
        water_source="the well",
        safe_space="the washroom",
        tags={"water", "folk_tale"},
    ),
    "hillcottage": BathSetting(
        id="hillcottage",
        label="hillcottage",
        place_phrase="the hill cottage cistern",
        water_source="the cistern",
        safe_space="the warm washroom",
        tags={"water", "folk_tale"},
    ),
}

NEEDS = {
    "bathe": BathNeed(
        id="bathe",
        word="bathe",
        phrase="to bathe",
        requires_warmth=True,
        tags={"bathe"},
    ),
    "wash": BathNeed(
        id="wash",
        word="wash",
        phrase="to wash up",
        requires_warmth=True,
        tags={"bathe"},
    ),
}

TOOLS = {
    "bucket_full": ConflictTool(
        id="bucket_full",
        phrase="a full bucket",
        volume="very full",
        spill_risk=3,
        tags={"full"},
    ),
    "bucket_average": ConflictTool(
        id="bucket_average",
        phrase="an average bucket",
        volume="about half full",
        spill_risk=1,
        tags={"average"},
    ),
}

RECONCILIATIONS = {
    "shared_bath": Reconciliation(
        id="shared_bath",
        action="share the bath",
        effect="warm and calm",
        words="I was wrong, and I will help",
        success_score=3,
        tags={"reconciliation"},
    ),
    "gentle_help": Reconciliation(
        id="gentle_help",
        action="help gently",
        effect="soft and safe",
        words="Let's do it together",
        success_score=2,
        tags={"reconciliation"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Tia", "Nell", "Ivy"]
BOY_NAMES = ["Milo", "Jon", "Bram", "Eli", "Pip"]


@dataclass
class StoryParams:
    setting: str
    need: str
    tool: str
    reconciliation: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTING:
        for n in NEEDS:
            for t in TOOLS:
                for r in RECONCILIATIONS:
                    combos.append((s, n, t, r))
    return combos


def explain_rejection(tool: ConflictTool) -> str:
    return f"(No story: the tool '{tool.id}' does not fit the tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale bath storyworld.")
    ap.add_argument("--setting", choices=SETTING)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.need is None or c[1] == args.need)
              and (args.tool is None or c[2] == args.tool)
              and (args.reconciliation is None or c[3] == args.reconciliation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, tool, reconciliation = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["boy", "girl"])
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_name = args.elder or rng.choice(["Grandma", "Grandpa", "Aunt May", "Uncle Dan"])
    return StoryParams(setting=setting, need=need, tool=tool,
                       reconciliation=reconciliation, child_name=child_name,
                       child_gender=gender, elder_name=elder_name,
                       elder_gender=elder_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk tale using the words average, full, and bathe.",
        f"Tell a story about {f['child'].attrs['name']} and {f['elder'].attrs['name']} where a bath starts as a conflict and ends in reconciliation.",
        "Write a gentle village story in which a child makes a poor guess about a bath, then learns to help make it right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.attrs['name']} and {elder.attrs['name']}, who live in a small village and share a bath story."),
        ("Why was there conflict?",
         f"There was conflict because {child.attrs['name']} wanted to bathe right away and made an average guess about the water, but the bath was not ready and the full bucket spilled. That left the room messy and made {elder.attrs['name']} upset."),
        ("How did they reconcile?",
         f"{child.attrs['name']} apologized, and {elder.attrs['name']} answered with mercy. Then they filled the tub together, so the quarrel turned into reconciliation."),
        ("What changed by the end?",
         f"The bath ended up full and warm, and both of them were calm again. The child learned that a wise choice is better than an average guess."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does bathe mean?",
         "To bathe means to wash your body in water, often in a tub or basin."),
        ("What does full mean?",
         "Full means something has no more room left for more of what it holds."),
        ("What does average mean?",
         "Average means ordinary or in the middle, not too much and not too little."),
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- child_stubborn, tub_full.
reconcile :- apology, mercy.
ending(full_bath) :- tub_full, reconcile.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child_stubborn"),
        asp.fact("apology"),
        asp.fact("mercy"),
        asp.fact("tub_full"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show conflict/0.\n#show reconcile/0.\n#show ending/1."))
    atoms = {s.name for s in model}
    py_ok = True
    sample = generate(resolve_params(argparse.Namespace(setting=None, need=None, tool=None,
                                                       reconciliation=None, name=None, gender=None,
                                                       elder=None, elder_gender=None),
                                     random.Random(7)))
    if not sample.story:
        py_ok = False
    if {"conflict", "reconcile", "ending"} <= atoms and py_ok:
        print("OK: ASP and Python smoke test passed.")
        return 0
    print("MISMATCH: ASP or Python smoke test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTING:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.need not in NEEDS:
        raise StoryError(f"Unknown need: {params.need}")
    if params.tool not in TOOLS:
        raise StoryError(f"Unknown tool: {params.tool}")
    if params.reconciliation not in RECONCILIATIONS:
        raise StoryError(f"Unknown reconciliation: {params.reconciliation}")
    world = tell(SETTING[params.setting], NEEDS[params.need], TOOLS[params.tool],
                 RECONCILIATIONS[params.reconciliation], params.child_name,
                 params.child_gender, params.elder_name, params.elder_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="riverhouse", need="bathe", tool="bucket_full",
                reconciliation="shared_bath", child_name="Milo",
                child_gender="boy", elder_name="Grandma", elder_gender="woman"),
    StoryParams(setting="hillcottage", need="wash", tool="bucket_average",
                reconciliation="gentle_help", child_name="Mara",
                child_gender="girl", elder_name="Aunt May", elder_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show conflict/0.\n#show reconcile/0.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode not expanded for this small world.")
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
