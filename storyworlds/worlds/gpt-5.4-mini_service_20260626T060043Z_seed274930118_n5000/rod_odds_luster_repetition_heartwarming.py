#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rod_odds_luster_repetition_heartwarming.py
===============================================================================================================

A small heartwarming story world about a child, a worn rod, and the repeated
try-again effort it takes to bring back its luster.

Premise:
- A child treasures an old rod that once belonged to a grandparent.
- The rod has lost its luster and looks dull.
- The child keeps trying, with help, to clean and polish it.
- The repeated care matters: each pass makes a little difference, and the
  emotional arc is gentle, patient, and warm.

This world is intentionally tiny and constraint-checked. It models:
- typed entities with physical meters and emotional memes,
- repeated actions that gradually improve a physical object,
- a warm social turn where help and persistence win over discouragement,
- child-facing prose grounded in the simulated state,
- a Python reasonableness gate mirrored by inline ASP rules.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

LUSTER_GAIN_PER_POLISH = 0.45
DULL_START = 0.15
BRIGHT_THRESHOLD = 0.80
MAX_POLISH_TRIES = 4

PLACES = {
    "shed": {"place": "the shed", "indoor": True},
    "porch": {"place": "the porch", "indoor": False},
    "workbench": {"place": "the kitchen table", "indoor": True},
    "garage": {"place": "the garage", "indoor": True},
}

ACTIVITIES = {
    "polish": {
        "label": "polish the rod",
        "verb": "polish the rod",
        "gerund": "polishing the rod",
        "repeat": "polish it again",
        "tool": "a soft cloth",
        "result": "brighter",
    },
    "rub": {
        "label": "rub the rod smooth",
        "verb": "rub the rod smooth",
        "gerund": "rubbing the rod smooth",
        "repeat": "rub it again",
        "tool": "a little cloth",
        "result": "shinier",
    },
}

TOOLS = {
    "cloth": {"label": "soft cloth", "kind": "cloth"},
    "towel": {"label": "clean towel", "kind": "towel"},
    "polish": {"label": "tiny tin of polish", "kind": "polish"},
}

NAMES = ["Maya", "Noah", "Lila", "Ben", "Iris", "Theo", "Nina", "Owen"]
PARENT_NAMES = ["Grandma", "Grandpa", "Mom", "Dad", "Aunt Jo", "Uncle Ray"]
TRAITS = ["patient", "gentle", "careful", "kind", "hopeful"]


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True


@dataclass
class Activity:
    id: str
    label: str
    verb: str
    gerund: str
    repeat: str
    tool: str
    result: str


@dataclass
class Rod:
    label: str = "old rod"
    phrase: str = "an old fishing rod with a dull finish"
    material: str = "metal"
    luster: float = DULL_START
    cleaned: int = 0
    treasured: bool = True


@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.rod = Rod()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def brighten(world: World, actor: Entity, act: Activity) -> list[str]:
    out: list[str] = []
    if world.rod.luster >= BRIGHT_THRESHOLD:
        return out
    sig = ("polish", world.rod.cleaned)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.rod.cleaned += 1
    world.rod.luster = min(1.0, world.rod.luster + LUSTER_GAIN_PER_POLISH)
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 0.5
    out.append(f"The rod looked a little {act.result} after another careful pass.")
    return out


def worry_to_hope(world: World, child: Entity) -> None:
    if world.rod.luster < BRIGHT_THRESHOLD:
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1.0
    else:
        child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0


def tell(setting: Setting, activity: Activity, params: StoryParams) -> World:
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=params.parent))
    cloth = world.add(Entity(id="Cloth", kind="thing", type="cloth", label="soft cloth"))
    polish = world.add(Entity(id="Polish", kind="thing", type="polish", label="tiny tin of polish"))

    child.memes["care"] = 1.0
    parent.memes["care"] = 1.0
    world.facts.update(child=child, parent=parent, cloth=cloth, polish=polish, activity=activity)

    world.say(
        f"{child.id} found an old rod that once belonged to {parent.label}. "
        f"It had lost its luster and looked tired and dull."
    )
    world.say(
        f"{child.id} did not want to leave it that way, because the rod was treasured."
    )

    world.para()
    world.say(
        f"At {setting.place}, {child.id} set out {activity.gerund} with {cloth.label} and polish."
    )
    world.say(
        f"{child.id} tried once, then {activity.repeat}, then tried again."
    )

    for _ in range(MAX_POLISH_TRIES):
        bright = brighten(world, child, activity)
        if bright:
            world.say(bright[0])
        if world.rod.luster >= BRIGHT_THRESHOLD:
            break
        world.say(
            f"It was not shiny yet, so {child.id} took a breath and kept going."
        )

    world.para()
    worry_to_hope(world, child)
    if world.rod.luster >= BRIGHT_THRESHOLD:
        world.say(
            f"At last, the rod caught the light with a soft glow, and {child.id} smiled."
        )
        world.say(
            f"{parent.label} came close, touched the smooth rod, and smiled too."
        )
        world.say(
            f"Together they set it in the light, where its new luster looked warm and proud."
        )
    else:
        world.say(
            f"Even after all that care, the rod was only a little brighter, but {child.id} felt proud for trying."
        )

    world.facts["resolved"] = world.rod.luster >= BRIGHT_THRESHOLD
    world.facts["tries"] = world.rod.cleaned
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(place: str, activity: str) -> bool:
    return place in PLACES and activity in ACTIVITIES


def explain_rejection(place: str, activity: str) -> str:
    if place not in PLACES:
        return "(No story: that place is not part of this little world.)"
    if activity not in ACTIVITIES:
        return "(No story: that activity is not part of this little world.)"
    return "(No story: the choices do not make a reasonable story here.)"


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    key: Setting(place=val["place"], indoor=val["indoor"]) for key, val in PLACES.items()
}

ACTIVITY_REGISTRY = {
    key: Activity(
        id=key,
        label=val["label"],
        verb=val["verb"],
        gerund=val["gerund"],
        repeat=val["repeat"],
        tool=val["tool"],
        result=val["result"],
    )
    for key, val in ACTIVITIES.items()
}


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    act = f["activity"]
    return [
        f'Write a heartwarming story for a small child about {child.id} and an old rod that has lost its luster.',
        f"Tell a gentle story where {child.id} keeps {act.gerund} again and again until the rod shines.",
        f'Write a short, comforting story that includes the words "rod", "odds", and "luster".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    act = f["activity"]
    tries = f["tries"]
    resolved = f["resolved"]
    qa = [
        QAItem(
            question=f"What did {child.id} keep trying to do with the rod?",
            answer=f"{child.id} kept trying to {act.verb} so the old rod could get its luster back.",
        ),
        QAItem(
            question=f"Why did {child.id} not give up when the rod still looked dull?",
            answer=f"{child.id} cared about the rod and felt hopeful, so {child.pronoun('subject')} kept going even when the odds seemed slow.",
        ),
        QAItem(
            question=f"How many careful tries did it take before the rod was bright enough?",
            answer=f"It took {tries} careful tries before the rod looked bright and warm again.",
        ),
    ]
    if resolved:
        qa.append(
            QAItem(
                question=f"How did {parent.label} feel at the end?",
                answer=f"{parent.label} felt happy and proud, because the child's patience brought the rod's luster back.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"How did {child.id} feel at the end?",
                answer=f"{child.id} felt proud for trying so hard, even though the rod was only a little brighter.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is luster?",
            answer="Luster is the soft shine a surface gives off when it catches the light.",
        ),
        QAItem(
            question="What are odds?",
            answer="Odds are a way of talking about how likely something is to happen.",
        ),
        QAItem(
            question="Why can repeated care help an old object?",
            answer="Repeated care can slowly clean away dullness and make the object look brighter again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is reasonable when the selected place and activity exist.
valid_story(P, A) :- place(P), activity(A).

% Repetition helps: more tries increase luster.
more_luster_after_try(T1, T2) :- try(T1), try(T2), T2 = T1 + 1.

% If enough tries happen, the rod becomes bright.
bright_rod :- try(1), try(2), try(3), try(4).

% A heartwarming ending is one where care and patience resolve the dullness.
heartwarming_end :- bright_rod.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for aid in ACTIVITY_REGISTRY:
        lines.append(asp.fact("activity", aid))
    for i in range(1, MAX_POLISH_TRIES + 1):
        lines.append(asp.fact("try", i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/2. #show bright_rod/0. #show heartwarming_end/0."))
    symbols = set((sym.name, tuple(getattr(a, "number", getattr(a, "name", None)) for a in sym.arguments)) for sym in model)
    python_ok = all(valid_combo(p, a) for p in SETTINGS for a in ACTIVITY_REGISTRY)
    if python_ok and any(name == "bright_rod" for name, _ in symbols):
        print("OK: ASP rules are present and Python reasonableness gate is satisfied.")
        return 0
    print("MISMATCH or insufficient ASP evidence.")
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A heartwarming little world about repeated care, luster, and an old rod."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITY_REGISTRY))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
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
    place = args.place or rng.choice(sorted(SETTINGS))
    activity = args.activity or rng.choice(sorted(ACTIVITY_REGISTRY))
    if not valid_combo(place, activity):
        raise StoryError(explain_rejection(place, activity))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITY_REGISTRY[params.activity], params)
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
    lines.append(f"rod.luster={world.rod.luster:.2f}")
    lines.append(f"rod.cleaned={world.rod.cleaned}")
    for e in world.entities.values():
        lines.append(f"{e.id}: memes={dict(e.memes)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2. #show bright_rod/0. #show heartwarming_end/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(f"valid stories: {asp.atoms(model, 'valid_story')}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place=place, activity=activity, name=name, gender=gender, parent=parent, trait=trait)
            for place in sorted(SETTINGS)
            for activity in sorted(ACTIVITY_REGISTRY)
            for gender in ["girl", "boy"]
            for name in [NAMES[(hash(place + activity + gender) % len(NAMES))]]
            for parent in [PARENT_NAMES[(hash(activity + place) % len(PARENT_NAMES))]]
            for trait in [TRAITS[(hash(name + activity) % len(TRAITS))]]
        ]
        params_list = [p for p in params_list if valid_combo(p.place, p.activity)]
        samples = [generate(p) for p in params_list[: max(1, args.n)]]
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
