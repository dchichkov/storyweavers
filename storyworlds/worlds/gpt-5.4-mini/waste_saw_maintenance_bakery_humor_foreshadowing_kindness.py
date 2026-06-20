#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/waste_saw_maintenance_bakery_humor_foreshadowing_kindness.py
==============================================================================================

A standalone story world sketch for a small bakery folk tale about waste,
a saw, maintenance, humor, foreshadowing, and kindness.

Premise:
- A bakery needs a simple repair and some cleanup.
- One character notices waste and a wobbly saw.
- The wrong choice would make the kitchen clumsy and unsafe.
- A kind helper uses maintenance, humor, and foresight to solve the problem.
- The ending proves the bakery is tidier, safer, and warm with shared bread.

This file is self-contained and only uses the Python standard library plus the
shared result containers from storyworlds/results.py.
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "baker"}
        male = {"boy", "father", "dad", "man", "baker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    smell: str
    has_oven: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class WasteItem:
    id: str
    label: str
    phrase: str
    kind: str
    smelly: bool = False
    edible: bool = False
    wasteful: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SawTool:
    id: str
    label: str
    phrase: str
    noisy: bool = True
    sharp: bool = True
    safe_when_maintained: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class MaintenanceFix:
    id: str
    label: str
    text: str
    power: int
    humor: int
    kind: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["waste"] < THRESHOLD:
            continue
        sig = ("spoil", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("bakery").meters["mess"] += 1
        world.get("baker").memes["worry"] += 1
        out.append("__waste__")
    return out


def _r_sound(world: World) -> list[str]:
    out: list[str] = []
    saw = world.get("saw")
    if saw.meters["used"] >= THRESHOLD and saw.meters["maintained"] < THRESHOLD:
        sig = ("sound", saw.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("bakery").memes["alarm"] += 1
        out.append("__saw__")
    return out


CAUSAL_RULES = [Rule("spoil", "physical", _r_spoil), Rule("sound", "physical", _r_sound)]


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


def maintenance_needed(tool: SawTool, waste: WasteItem) -> bool:
    return tool.sharp and waste.wasteful


def can_fix(fix: MaintenanceFix) -> bool:
    return fix.power >= 1 and fix.kind >= 1


def predict(world: World, tool: SawTool, waste: WasteItem) -> dict:
    sim = world.copy()
    _do_messy(sim, sim.get("baker"), tool, waste, narrate=False)
    return {
        "mess": sim.get("bakery").meters["mess"],
        "worry": sim.get("baker").memes["worry"],
    }


def _do_messy(world: World, baker: Entity, tool: SawTool, waste: WasteItem, narrate: bool = True) -> None:
    baker.memes["humor"] += 1
    baker.meters["attempt"] += 1
    world.get("saw").meters["used"] += 1
    world.get("waste").meters["waste"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, baker: Entity, helper: Entity, place: Place, waste: WasteItem, tool: SawTool) -> None:
    world.say(
        f"In the little bakery, where the air smelled of warm sugar and yeast, {baker.id} "
        f"kept the shelves neat and the ovens busy."
    )
    world.say(
        f"One morning {helper.id} found a pile of {waste.label} that should have been "
        f"saved for the pigs, but had been left to waste."
    )
    world.say(
        f"Beside the flour bin sat {tool.phrase}, humming like a sleepy hornet."
    )


def foreshadow(world: World, helper: Entity, tool: SawTool, waste: WasteItem) -> None:
    world.say(
        f'{helper.id} squinted at the tool and said, "That saw sings a funny song. '
        f'If it keeps singing, the bread boards may begin to dance."'
    )
    world.say(
        f"Everyone laughed, but {helper.id} tucked the {waste.label} aside, as if to say "
        f"the day would need careful hands."
    )


def use_bad_choice(world: World, baker: Entity, tool: SawTool, waste: WasteItem) -> None:
    baker.memes["curiosity"] += 1
    world.say(
        f'{baker.id} gave the saw a try anyway, thinking a quick cut would save time.'
    )
    _do_messy(world, baker, tool, waste)
    world.say(
        f"The saw bumped, the flour puffed up like a sneeze, and crumbs went everywhere."
    )


def warn(world: World, helper: Entity, baker: Entity, waste: WasteItem, tool: SawTool) -> None:
    pred = predict(world, tool, waste)
    world.facts["predicted_mess"] = pred["mess"]
    world.say(
        f'{helper.id} put a gentle hand on the bench and said, "If we hurry, we make '
        f"more waste, not less. A bakery can laugh, but it should not waste its bread."
    )


def kindness_turn(world: World, helper: Entity, baker: Entity, fix: MaintenanceFix, waste: WasteItem) -> None:
    helper.memes["kindness"] += 1
    helper.memes["humor"] += 1
    world.say(
        f'{helper.id} winked and said, "Let us do the sensible thing before the oven '
        f"starts scolding us."
    )
    world.say(
        f"Then {helper.id} took out {fix.text}, and the whole room felt steadier at once."
    )


def repair(world: World, helper: Entity, fix: MaintenanceFix, tool: SawTool) -> None:
    tool.meters["maintained"] += 1
    world.get("bakery").meters["mess"] = 0.0
    helper.memes["pride"] += 1
    world.say(
        f"The saw got its maintenance at last: a careful clean, a tiny turn of the screw, "
        f"and a bright dab of oil."
    )
    world.say(
        f"After that, the tool cut straight, and it sounded less like a hornet and more like a song."
    )


def ending(world: World, baker: Entity, helper: Entity, place: Place) -> None:
    baker.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By afternoon the bakery was tidy again, the extra waste had been carried out, "
        f"and the fresh loaves cooled in peace."
    )
    world.say(
        f"{baker.id} and {helper.id} shared a crust of bread, and even the saw rested quietly in its box."
    )


def tell(place: Place, waste: WasteItem, tool: SawTool, fix: MaintenanceFix,
         baker_name: str = "Mara", baker_gender: str = "girl",
         helper_name: str = "Old Pipp", helper_gender: str = "boy") -> World:
    world = World(place)
    baker = world.add(Entity(id=baker_name, kind="character", type=baker_gender, role="baker"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    bakery = world.add(Entity(id="bakery", type="place", label=place.label))
    waste_ent = world.add(Entity(id="waste", type="thing", label=waste.label))
    saw_ent = world.add(Entity(id="saw", type="tool", label=tool.label))

    setup(world, baker, helper, place, waste, tool)
    world.para()
    foreshadow(world, helper, tool, waste)
    warn(world, helper, baker, waste, tool)
    world.para()
    use_bad_choice(world, baker, tool, waste)
    world.para()
    kindness_turn(world, helper, baker, fix, waste)
    repair(world, helper, fix, tool)
    world.para()
    ending(world, baker, helper, place)

    world.facts.update(
        baker=baker, helper=helper, bakery=bakery, waste=waste_ent, saw=saw_ent,
        place=place, waste_cfg=waste, tool_cfg=tool, fix=fix,
        cleaned=True, maintained=True,
    )
    return world


BAKERY = Place("bakery", "the bakery", "warm bread and sugar")
WASTES = {
    "crumbs": WasteItem("crumbs", "crumbs", "crumbs from yesterday's buns", "crumbs", smelly=False, edible=True, tags={"waste", "crumbs"}),
    "sacks": WasteItem("sacks", "old flour sacks", "old flour sacks by the door", "sacks", smelly=True, edible=False, tags={"waste", "sacks"}),
    "peels": WasteItem("peels", "apple peels", "apple peels in a tin bowl", "peels", smelly=True, edible=True, tags={"waste", "peels"}),
}
SAWS = {
    "hand_saw": SawTool("hand_saw", "hand saw", "a small hand saw", noisy=True, sharp=True, tags={"saw"}),
    "dull_saw": SawTool("dull_saw", "dull saw", "a dull saw with a loose handle", noisy=True, sharp=False, tags={"saw"}),
}
FIXES = {
    "oil": MaintenanceFix("oil", "oil and a rag", "oil and a clean rag", power=2, humor=1, kind=2, tags={"maintenance"}),
    "screw": MaintenanceFix("screw", "a tiny screwdriver", "a tiny screwdriver and a patient twist", power=2, humor=1, kind=2, tags={"maintenance"}),
}
NAMES = ["Mara", "Nell", "Tamsin", "Anya", "Pip", "Gwen", "Hugh", "Robin"]


@dataclass
@dataclass
class StoryParams:
    waste: str
    saw: str
    maintenance: str
    baker: str
    baker_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for waste in WASTES:
        for saw in SAWS:
            for fix in FIXES:
                combos.append((waste, saw, fix))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style bakery story that includes the words "waste", "saw", and "maintenance".',
        f"Tell a warm bakery story where {f['baker'].id} and {f['helper'].id} notice waste, worry about a saw, and fix the problem kindly.",
        f"Write a child-friendly folk tale in a bakery with humor and foreshadowing, ending with the bakery made neat again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    baker, helper = f["baker"], f["helper"]
    waste, tool, fix = f["waste_cfg"], f["tool_cfg"], f["fix"]
    qa = [
        ("What problem did they notice first?",
         f"They noticed waste left in the bakery and a saw that looked ready to act up. That made the room feel less tidy and set up the trouble that followed."),
        ("What did the helper say before the repair?",
         f'{helper.id} warned that if they hurried, they would make more waste, not less. That was the foreshadowing: the story hinted that haste would only add mess.'),
        ("How did they solve the problem?",
         f"They used {fix.text} and gave the saw proper maintenance. After that, the bakery became tidy again and the work could go on safely."),
        ("How did the story end?",
         f"It ended with clean counters, quiet tools, and fresh loaves cooling in peace. The kind choice turned the noisy trouble into a calm afternoon."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is waste?",
         "Waste is something left over or thrown away. In a bakery, waste should be sorted, saved, or cleaned up so the place stays neat."),
        ("What is a saw?",
         "A saw is a tool with teeth that cuts wood or other materials. It needs careful handling and maintenance so it can work well."),
        ("What is maintenance?",
         "Maintenance means taking care of a tool or place so it stays in good working order. Cleaning, oiling, and tightening parts are common maintenance jobs."),
        ("Why can humor help in a hard moment?",
         "Humor can help people stay calm and work together. A small joke can make a tricky job feel lighter without ignoring the problem."),
        ("What is kindness?",
         "Kindness means helping gently, thinking of others, and doing what will truly help. In a story, kindness can turn a bad moment into a better one."),
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
    for e in list(world.entities.values()):
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
    StoryParams("crumbs", "hand_saw", "oil", "Mara", "girl", "Pip", "boy"),
    StoryParams("sacks", "hand_saw", "screw", "Nell", "girl", "Hugh", "boy"),
    StoryParams("peels", "hand_saw", "oil", "Anya", "girl", "Robin", "boy"),
]


def explain_rejection() -> str:
    return "(No story: this bakery tale needs waste, a saw, and maintenance together."


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", BAKERY.id)]
    for wid in WASTES:
        lines.append(asp.fact("waste", wid))
    for sid in SAWS:
        lines.append(asp.fact("saw", sid))
    for fid in FIXES:
        lines.append(asp.fact("maintenance", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(W, S, M) :- waste(W), saw(S), maintenance(M).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bakery folk tale about waste, a saw, maintenance, humor, foreshadowing, and kindness.")
    ap.add_argument("--waste", choices=WASTES)
    ap.add_argument("--saw", choices=SAWS)
    ap.add_argument("--maintenance", choices=FIXES)
    ap.add_argument("--baker")
    ap.add_argument("--baker-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    waste = args.waste or rng.choice(sorted(WASTES))
    saw = args.saw or rng.choice(sorted(SAWS))
    maintenance = args.maintenance or rng.choice(sorted(FIXES))
    baker_gender = args.baker_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if baker_gender == "girl" else "girl")
    baker = args.baker or rng.choice(NAMES)
    helper_choices = [n for n in NAMES if n != baker]
    helper = args.helper or rng.choice(helper_choices)
    return StoryParams(waste, saw, maintenance, baker, baker_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(BAKERY, WASTES[params.waste], SAWS[params.saw], FIXES[params.maintenance],
                 params.baker, params.baker_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for triple in asp_valid_combos():
            print("  ", triple)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.baker} and {p.helper}: waste, saw, maintenance"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
