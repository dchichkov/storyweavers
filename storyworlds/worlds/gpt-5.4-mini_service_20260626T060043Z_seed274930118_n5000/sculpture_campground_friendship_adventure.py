#!/usr/bin/env python3
"""
A standalone storyworld for a campground adventure about friendship and sculpture.

Seed-inspired premise:
Two friends at a campground want to build a sculpture from found materials.
One friend wants a risky, adventurous build; the other worries about the sculpture
toppling before the campfire night. They work together, find better materials,
and finish with a proud campground landmark.

The world model tracks:
- physical meters: stacked height, balance, polish, mess, stability, distance
- emotional memes: excitement, worry, trust, pride, friendship, frustration

The story is intentionally small and classical: setup, tension, turn, resolution.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Setting:
    place: str = "the campground"
    features: tuple[str, ...] = ("forest path", "picnic table", "fire ring", "stream")


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    role: str
    gender: str


@dataclass(frozen=True)
class Material:
    id: str
    label: str
    found_at: str
    sturdy: bool
    smooth: bool
    good_for: tuple[str, ...]


@dataclass(frozen=True)
class SculpturePlan:
    id: str
    shape: str
    name: str
    height: int
    needed: tuple[str, ...]
    risky: bool
    theme: str


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    helps: tuple[str, ...]
    method: str


SETTINGS = {
    "campground": Setting(),
}

CHARACTERS = [
    CharacterSpec("Maya", "girl", "girl"),
    CharacterSpec("Leo", "boy", "boy"),
    CharacterSpec("Nora", "girl", "girl"),
    CharacterSpec("Toby", "boy", "boy"),
    CharacterSpec("Ivy", "girl", "girl"),
    CharacterSpec("Finn", "boy", "boy"),
]

MATERIALS = {
    "pinecones": Material("pinecones", "pinecones", "the pine needles", False, True, ("texture",)),
    "flat_stones": Material("flat_stones", "flat stones", "the stream bank", True, True, ("base", "stacking")),
    "sticks": Material("sticks", "sticks", "the trail edge", True, False, ("frame", "stacking")),
    "bark": Material("bark", "bark strips", "the fallen log", False, False, ("wrap", "texture")),
    "feathers": Material("feathers", "feathers", "the brush near the path", False, very_smooth := True, ("topper", "texture")),
    "twine": Material("twine", "twine", "the camp supply box", True, False, ("binding", "stability")),
    "shells": Material("shells", "shells", "the lakeshore bucket", True, True, ("decorate", "texture")),
}

PLANS = {
    "tower": SculpturePlan("tower", "tower", "camp tower", 5, ("base", "stacking", "stability"), True, "adventure"),
    "totem": SculpturePlan("totem", "totem", "trail totem", 4, ("base", "stacking", "decorate"), False, "friendship"),
    "bird": SculpturePlan("bird", "bird", "forest bird", 3, ("frame", "texture", "topper"), False, "adventure"),
    "bridge": SculpturePlan("bridge", "bridge", "tiny bridge sculpture", 4, ("base", "frame", "stability"), True, "adventure"),
}

TOOLS = {
    "gloves": Tool("gloves", "work gloves", ("handling", "rough"), "wear work gloves"),
    "cloth": Tool("cloth", "soft cloth", ("polish",), "wipe it with a soft cloth"),
    "twine_tie": Tool("twine_tie", "twine ties", ("stability", "binding"), "bind the pieces with twine"),
}

GIRL_NAMES = [c.name for c in CHARACTERS if c.gender == "girl"]
BOY_NAMES = [c.name for c in CHARACTERS if c.gender == "boy"]
ALL_NAMES = [c.name for c in CHARACTERS]


# ---------------------------------------------------------------------------
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    owner: Optional[str] = None
    partner: Optional[str] = None
    worn_by: Optional[str] = None
    tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def __post_init__(self):
        for k in ["height", "balance", "polish", "mess", "stability", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["excitement", "worry", "trust", "pride", "friendship", "frustration"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.id_gender()
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def id_gender(self) -> str:
        return "girl" if self.id in GIRL_NAMES else "boy" if self.id in BOY_NAMES else "neutral"


@dataclass
class World:
    setting: Setting
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        return World(
            setting=self.setting,
            paragraphs=[[]],
            entities=copy.deepcopy(self.entities),
            facts=copy.deepcopy(self.facts),
            fired=set(self.fired),
        )


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_wobble(world: World) -> list[str]:
    out = []
    sculpture = world.entities.get("sculpture")
    if not sculpture:
        return out
    if sculpture.meters["height"] >= 4 and sculpture.meters["stability"] < 2:
        sig = ("wobble",)
        if sig not in world.fired:
            world.fired.add(sig)
            sculpture.meters["balance"] += 1
            out.append("The sculpture started to wobble in the breeze.")
    return out


def _r_pride(world: World) -> list[str]:
    out = []
    for pid in ("kid1", "kid2"):
        p = world.entities.get(pid)
        if not p:
            continue
        if p.meters["distance"] >= 1 and p.memes["trust"] >= 1 and p.meters["stability"] >= 1:
            sig = ("pride", pid)
            if sig not in world.fired:
                world.fired.add(sig)
                p.memes["pride"] += 1
                p.memes["friendship"] += 1
                out.append(f"{p.id} felt proud of what they were making together.")
    return out


def _r_fix(world: World) -> list[str]:
    out = []
    sculpture = world.entities.get("sculpture")
    if sculpture and sculpture.meters["stability"] >= 2 and sculpture.meters["balance"] >= 1:
        sig = ("resolve",)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The sculpture held steady.")
    return out


RULES = [_r_wobble, _r_pride, _r_fix]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _make_story(world: World, hero1: Entity, hero2: Entity, plan: SculpturePlan, tool: Tool) -> None:
    sculpture = world.add(Entity("sculpture", kind="thing", label=plan.name))
    materials = world.facts["materials"]

    world.say(
        f"At the campground, {hero1.id} and {hero2.id} found a sunny clearing near the picnic table."
    )
    world.say(
        f"They wanted to build a {plan.shape} sculpture called the {plan.name} for the evening campfire."
    )
    world.say(
        f"{hero1.id} loved the big adventure of making something tall, while {hero2.id} loved doing it together."
    )

    # Setup state
    sculpture.meters["height"] = 1
    sculpture.meters["stability"] = 0
    hero1.memes["excitement"] += 1
    hero2.memes["friendship"] += 1
    hero1.meters["distance"] += 1
    hero2.meters["distance"] += 1

    world.para()
    world.say(
        f"They started with {materials[0].label} from {materials[0].found_at} and {materials[1].label} from {materials[1].found_at}."
    )
    sculpture.meters["height"] += 2
    sculpture.meters["stability"] += 1
    hero1.meters["stability"] += 1
    hero2.memes["trust"] += 1

    if plan.risky:
        world.say(
            f"{hero1.id} wanted to stack even faster, but the shape grew top-heavy and looked shaky."
        )
        sculpture.meters["height"] += 2
        sculpture.meters["balance"] += 1
        hero2.memes["worry"] += 1
        world.say(
            f"{hero2.id} pointed to the breeze and said they should slow down before the sculpture tipped."
        )
        hero1.memes["frustration"] += 1
        hero1.memes["trust"] += 1
        world.say(
            f"{hero1.id} listened, because a good adventure at the campground was better with a friend beside them."
        )
        sculpture.meters["stability"] += 1

    world.para()
    world.say(
        f"They used {tool.label} to {tool.method} and then added {materials[2].label} as a careful base."
    )
    sculpture.meters["stability"] += 2
    sculpture.meters["height"] += 1
    sculpture.meters["balance"] += 1
    hero2.memes["trust"] += 1
    hero1.memes["friendship"] += 1

    if "decorate" in plan.needed:
        world.say(
            f"{hero2.id} tucked {materials[3].label} and {materials[-1].label} into the sides so the sculpture looked brave and bright."
        )
        sculpture.meters["polish"] += 1

    propagate(world, narrate=True)

    world.para()
    world.say(
        f"By sunset, the {plan.name} stood near the camp chairs like a little landmark, and both friends laughed to see it still standing."
    )
    hero1.memes["pride"] += 1
    hero2.memes["pride"] += 1
    hero1.memes["friendship"] += 1
    hero2.memes["friendship"] += 1
    sculpture.meters["stability"] += 1
    world.facts.update(
        hero1=hero1,
        hero2=hero2,
        sculpture=sculpture,
        plan=plan,
        tool=tool,
        materials=materials,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a short adventure story for a young child about two friends at a campground who build a sculpture together.",
        f"Tell a gentle friendship adventure where {f['hero1'].id} and {f['hero2'].id} make a {f['plan'].shape} sculpture at the campground.",
        "Write a story that includes a campground, a sculpture, and a better idea when the first plan looks too risky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero1 = f["hero1"]
    hero2 = f["hero2"]
    plan = f["plan"]
    sculpture = f["sculpture"]
    return [
        QAItem(
            question=f"Who worked together to make the {plan.name} at the campground?",
            answer=f"{hero1.id} and {hero2.id} worked together. They were friends, and they built the {plan.name} as a shared adventure.",
        ),
        QAItem(
            question=f"What kind of sculpture did they try to build?",
            answer=f"They tried to build a {plan.shape} sculpture called the {plan.name}.",
        ),
        QAItem(
            question=f"What made the first plan a little tricky?",
            answer=f"The sculpture got tall before it got steady, so it looked shaky in the breeze and needed a better base.",
        ),
        QAItem(
            question=f"How did they make the sculpture safer?",
            answer=f"They slowed down, used {f['tool'].label}, added a stronger base, and kept building together until it stood steady.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the sculpture was standing proudly near the camp chairs, and both friends felt proud and closer together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sculpture?",
            answer="A sculpture is a piece of art made by shaping, stacking, carving, or arranging materials into a form.",
        ),
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people stay outdoors, usually with tents, trails, fire rings, and spaces for camping.",
        ),
        QAItem(
            question="Why is friendship helpful on an adventure?",
            answer="Friendship helps because friends can share ideas, watch out for each other, and solve problems together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(campground).
character(kid1).
character(kid2).
friendship_theme(campground_friendship_adventure).

is_risky(Plan) :- sculpture_plan(Plan), risky_plan(Plan).
good_fix(Plan) :- sculpture_plan(Plan), not risky_plan(Plan).

compatible_story(Place, Plan) :- setting(Place), sculpture_plan(Plan), safe_or_fixed(Plan).
safe_or_fixed(Plan) :- not risky_plan(Plan).
safe_or_fixed(Plan) :- risky_plan(Plan), has_solution(Plan).

has_solution(tower).
has_solution(bridge).

#show compatible_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "campground")]
    for c in CHARACTERS:
        lines.append(asp.fact("character", c.name))
        lines.append(asp.fact("gender", c.name, c.gender))
    for mid, m in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        for g in m.good_for:
            lines.append(asp.fact("good_for", mid, g))
    for pid, p in PLANS.items():
        lines.append(asp.fact("sculpture_plan", pid))
        if p.risky:
            lines.append(asp.fact("risky_plan", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/2."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = set(("campground", pid) for pid, p in PLANS.items() if not p.risky or p.id in {"tower", "bridge"})
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP parity matches python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for plan_id, plan in PLANS.items():
            if plan_id in {"tower", "bridge", "totem", "bird"}:
                out.append((place, plan_id))
    return out


def explain_rejection(plan: SculpturePlan) -> str:
    return (
        f"(No story: the {plan.name} plan does not have a reasonable way to finish "
        f"at the campground. Choose a plan with a steadier shape or a safer material set.)"
    )


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "campground"
    plan: str = "totem"
    hero1: str = "Maya"
    hero2: str = "Leo"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Campground sculpture friendship adventure.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
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
    plan_id = args.plan or rng.choice(list(PLANS))
    plan = PLANS[plan_id]
    if plan.risky and plan_id == "bridge":
        raise StoryError(explain_rejection(plan))
    place = args.place or "campground"
    hero1 = args.hero1 or rng.choice(GIRL_NAMES)
    hero2 = args.hero2 or rng.choice([n for n in ALL_NAMES if n != hero1])
    if hero2 == hero1:
        raise StoryError("The two friends need to be different characters.")
    return StoryParams(place=place, plan=plan_id, hero1=hero1, hero2=hero2)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero1 = world.add(Entity(params.hero1, kind="character"))
    hero2 = world.add(Entity(params.hero2, kind="character"))
    plan = PLANS[params.plan]
    tool = TOOLS["twine_tie"]
    world.facts["materials"] = [MATERIALS["flat_stones"], MATERIALS["sticks"], MATERIALS["twine"], MATERIALS["shells"], MATERIALS["feathers"]]
    world.facts["hero1"] = hero1
    world.facts["hero2"] = hero2
    world.facts["plan"] = plan
    world.facts["tool"] = tool
    _make_story(world, hero1, hero2, plan, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
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


CURATED = [
    StoryParams(place="campground", plan="totem", hero1="Maya", hero2="Leo"),
    StoryParams(place="campground", plan="bird", hero1="Nora", hero2="Toby"),
    StoryParams(place="campground", plan="tower", hero1="Ivy", hero2="Finn"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible_story/2."))
        print(f"{len(asp.atoms(model, 'compatible_story'))} compatible stories")
        for place, plan in asp.atoms(model, "compatible_story"):
            print(place, plan)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
