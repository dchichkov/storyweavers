#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jimmy_filth_hydroponic_cautionary_sound_effects_fable.py
========================================================================================

A small fable-style storyworld about a child named Jimmy, a hydroponic garden,
and a cautionary lesson about filth. The domain is built to be concrete and
state-driven: clean water grows green leaves, muddy hands and dirty tools can
spoil the system, a careful helper warns in time, and the ending proves what
changed.

Seed words: jimmy, filth, hydroponic
Features: Cautionary, Sound Effects
Style: Fable
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CLEAN_MIN = 1
DIRT_MAX = 1.0


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
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    clean: bool = True
    hydroponic: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    sound: str
    dirty: bool = False
    can_clean: bool = False
    can_dirty: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Mischief:
    id: str
    label: str
    sound: str
    mess: str
    harm: str
    spread: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    sound: str
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
        self.plant_beds: dict[str, float] = {"bed": 1.0}

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
        clone.plant_beds = copy.deepcopy(self.plant_beds)
        return clone


@dataclass
class StoryParams:
    place: str
    mischief: str
    remedy: str
    jimmy_name: str = "Jimmy"
    helper_name: str = "Marta"
    helper_type: str = "girl"
    parent_name: str = "Grandma"
    seed: Optional[int] = None


PLACES = {
    "glasshouse": Place("glasshouse", "the glasshouse", True, True, {"hydroponic", "green"}),
    "nursery": Place("nursery", "the nursery room", True, True, {"hydroponic", "sprouts"}),
}

MISCHIEFS = {
    "mud": Mischief("mud", "muddy boots", "splat", "mud on the floor", "mud can clog the pump", 1, {"filth", "mud"}),
    "grease": Mischief("grease", "greasy hands", "slip", "grease on the tray", "grease can coat the roots", 2, {"filth", "grease"}),
    "dust": Mischief("dust", "dusty sleeve", "puff", "dust in the water", "dust can make the leaves droop", 1, {"filth", "dust"}),
}

REMEDIES = {
    "wipe": Remedy("wipe", "a clean cloth", "swish", 2, "wiped the tray, rinsed the pump, and set everything straight", "wiped the tray and rinsed the pump", {"clean", "cloth"}),
    "rinse": Remedy("rinse", "fresh water", "glug", 3, "poured fresh water through the pipes until the dirt was gone", "poured fresh water through the pipes", {"clean", "water"}),
    "brush": Remedy("brush", "a soft brush", "scrub", 2, "brushed the dirt away and opened the little holes again", "brushed the dirt away", {"clean", "brush"}),
}

GIRL_NAMES = ["Marta", "Lina", "Nora", "Pia", "Sana", "Ivy"]
BOY_NAMES = ["Jimmy", "Eli", "Noah", "Theo", "Ben", "Milo"]
HELPERS = ["careful", "patient", "wise", "gentle", "watchful"]


def hazard_at_risk(mischief: Mischief) -> bool:
    return True


def reasonable_remedy(remedy: Remedy) -> bool:
    return remedy.power >= CLEAN_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    if not any(reasonable_remedy(r) for r in REMEDIES.values()):
        return out
    for place in PLACES:
        for m in MISCHIEFS:
            for r in REMEDIES:
                out.append((place, m, r))
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    jimmy = world.get("Jimmy")
    if jimmy.meters["filth"] < THRESHOLD:
        return out
    sig = ("spoil", "bed")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("bed").meters["cloudy"] += 1
    world.get("bed").memes["worry"] += 1
    out.append("__spoil__")
    return out


def _r_leaves(world: World) -> list[str]:
    out: list[str] = []
    if world.get("bed").meters["cloudy"] < THRESHOLD:
        return out
    sig = ("leaves",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("garden").meters["sad"] += 1
    out.append("__leaves__")
    return out


CAUSAL_RULES = [  # small, classical chain
    type("Rule", (), {"name": "spoil", "tag": "physical", "apply": _r_spoil}),
    type("Rule", (), {"name": "leaves", "tag": "physical", "apply": _r_leaves}),
]


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


def predict_spoil(world: World, mischief: Mischief) -> dict:
    sim = world.copy()
    sim.get("Jimmy").meters["filth"] += 1
    sim.get("Jimmy").memes["impulse"] += 1
    propagate(sim, narrate=False)
    return {"cloudy": sim.get("bed").meters["cloudy"] >= THRESHOLD}


def introduce(world: World, jimmy: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Once there was a small hydroponic garden called {place.label}, where green leaves drank from neat tubes and bright water hissed softly."
    )
    world.say(
        f"Jimmy and {helper.id} tended it together, and the old family rule was simple: keep the hydroponic water clean."
    )


def sound_detail(mischief: Mischief, remedy: Remedy) -> str:
    return f"{mischief.sound}! {remedy.sound}!"


def tempt(world: World, jimmy: Entity, mischief: Mischief, helper: Entity) -> None:
    jimmy.memes["curious"] += 1
    world.say(
        f"One afternoon Jimmy came in with {mischief.label}. {sound_detail(mischief, REMEDIES['wipe'])}"
    )
    world.say(
        f'{helper.id} lifted a brow. "That kind of filth can trouble the pipes," {helper.pronoun()} said.'
    )


def warn(world: World, helper: Entity, jimmy: Entity, mischief: Mischief) -> None:
    pred = predict_spoil(world, mischief)
    if pred["cloudy"]:
        world.facts["predicted_cloudy"] = True
        world.say(
            f'"If the filth falls into the tray, the roots will choke," {helper.id} warned. "Then the leaves may droop."'
        )


def defy(world: World, jimmy: Entity, mischief: Mischief) -> None:
    jimmy.memes["defiance"] += 1
    world.say(f'Jimmy frowned. "It is only a little filth," he said, and took one careless step closer.')


def spill(world: World, jimmy: Entity, mischief: Mischief) -> None:
    jimmy.meters["filth"] += 1
    jimmy.meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{mischief.sound}! The {mischief.label} slipped from Jimmy's hands and splashed into the watering tray."
    )
    world.say(
        "The water turned cloudy at once, and the little pump began to cough and gurgle."
    )


def alarm(world: World, helper: Entity, parent: Entity, mischief: Mischief) -> None:
    world.say(f'"{parent.id}!" {helper.id} called. "Come quickly -- the hydroponic bed has filth in it!"')


def rescue(world: World, parent: Entity, remedy: Remedy, place: Place) -> None:
    world.get("bed").meters["cloudy"] = 0.0
    world.get("garden").meters["sad"] = 0.0
    world.say(
        f"{parent.id} hurried in. With a quick {remedy.sound}, {remedy.text}."
    )
    world.say(
        f"The water cleared, and the leaves lifted back toward the lamp with a soft green shine."
    )


def lesson(world: World, parent: Entity, jimmy: Entity, helper: Entity, mischief: Mischief) -> None:
    jimmy.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.id} knelt beside Jimmy and said, 'A hydroponic garden lives by clean water. Filth is small at first, but it can grow into trouble fast.'"
    )
    world.say(f'Jimmy nodded. "{mischief.label} stays away from the tray," he promised.')


def ending(world: World, helper: Entity, jimmy: Entity, remedy: Remedy) -> None:
    jimmy.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The next morning {sound_detail(REMEDIES['rinse'], remedy)} the garden glowed again."
    )
    world.say(
        f"Jimmy wiped his shoes at the door, {helper.id} smiled, and the hydroponic leaves stood tall above the clean water."
    )


def tell(place: Place, mischief: Mischief, remedy: Remedy,
         jimmy_name: str = "Jimmy", helper_name: str = "Marta", helper_type: str = "girl",
         parent_name: str = "Grandma") -> World:
    world = World()
    jimmy = world.add(Entity(id=jimmy_name, kind="character", type="boy", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper", traits=["careful"]))
    parent = world.add(Entity(id=parent_name, kind="character", type="woman", role="parent"))
    world.add(Entity(id="garden", type="place", label=place.label))
    world.add(Entity(id="bed", type="bed", label="the hydroponic tray"))
    world.facts["place"] = place
    world.facts["mischief"] = mischief
    world.facts["remedy"] = remedy
    world.facts["jimmy"] = jimmy
    world.facts["helper"] = helper
    world.facts["parent"] = parent

    introduce(world, jimmy, helper, place)
    world.para()
    tempt(world, jimmy, mischief, helper)
    warn(world, helper, jimmy, mischief)
    defy(world, jimmy, mischief)
    spill(world, jimmy, mischief)
    alarm(world, helper, parent, mischief)
    world.para()
    rescue(world, parent, remedy, place)
    lesson(world, parent, jimmy, helper, mischief)
    world.para()
    ending(world, helper, jimmy, remedy)
    world.facts["outcome"] = "cleaned"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a cautionary fable for a young child about jimmy, filth, and a hydroponic garden, with a few playful sound effects.',
        f"Tell a short fable where Jimmy nearly brings {f['mischief'].label} into a hydroponic bed, but a careful helper warns him and a grown-up fixes it.",
        f'Write a story that uses the words "jimmy", "filth", and "hydroponic" and ends with a clean garden and a learned lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mischief: Mischief = f["mischief"]
    remedy: Remedy = f["remedy"]
    qa = [
        QAItem(
            question="What was special about the garden?",
            answer="It was a hydroponic garden, so the plants grew in clean water instead of ordinary dirt. That means the water had to stay clear for the roots and tubes to work well."
        ),
        QAItem(
            question="Why did the helper warn Jimmy?",
            answer=f"{f['helper'].id} warned him because {mischief.label} could make the hydroponic water cloudy and trouble the pump. If the water gets dirty, the leaves can droop and the plants can suffer."
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{f['parent'].id} came quickly and {remedy.qa_text}. That cleared the tray and let the garden recover."
        ),
        QAItem(
            question="How did Jimmy change by the end?",
            answer="He became more careful. He learned that a small careless choice can make a big mess, so he kept filth away from the tray after that."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hydroponic mean?",
            answer="Hydroponic means plants grow in water with help from a tray or tubes instead of in ordinary soil."
        ),
        QAItem(
            question="Why can filth be a problem in a garden?",
            answer="Filth can clog water pipes, cover roots, and make plants harder to care for. A clean setup helps the plants stay healthy."
        ),
        QAItem(
            question="What should you do if you make a mess near something delicate?",
            answer="Stop right away, tell a grown-up, and help clean it carefully. Quick honesty is the safest choice."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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


CURATED = [
    StoryParams("glasshouse", "mud", "wipe"),
    StoryParams("nursery", "grease", "rinse"),
    StoryParams("glasshouse", "dust", "brush"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mischief and args.remedy and not reasonable_remedy(REMEDIES[args.remedy]):
        raise StoryError("Chosen remedy is not reasonable.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mischief is None or c[1] == args.mischief)
              and (args.remedy is None or c[2] == args.remedy)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mischief, remedy = rng.choice(sorted(combos))
    return StoryParams(place, mischief, remedy)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MISCHIEFS[params.mischief], REMEDIES[params.remedy],
                 params.jimmy_name, params.helper_name, params.helper_type, params.parent_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary hydroponic fable for young readers.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mischief", choices=MISCHIEFS)
    ap.add_argument("--remedy", choices=REMEDIES)
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


ASP_RULES = r"""
valid(P, M, R) :- place(P), mischief(M), remedy(R), remedy_power(R, Pow), Pow >= 1.
cloudy :- filth_event.
clean_after :- cloudy, remedy_power(R, Pow), Pow >= 2.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for mid, m in MISCHIEFS.items():
        lines.append(asp.fact("mischief", mid))
        lines.append(asp.fact("mischief_spread", mid, m.spread))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_power", rid, r.power))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    c = set(asp_valid_combos())
    p = set(valid_combos())
    if c != p:
        print("MISMATCH in valid_combos()")
        if c - p:
            print(" only in clingo:", sorted(c - p))
        if p - c:
            print(" only in python:", sorted(p - c))
        return 1
    print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
