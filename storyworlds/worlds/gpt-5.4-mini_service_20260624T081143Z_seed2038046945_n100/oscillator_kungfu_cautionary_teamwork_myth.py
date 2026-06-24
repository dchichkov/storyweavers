#!/usr/bin/env python3
"""
storyworlds/worlds/oscillator_kungfu_cautionary_teamwork_myth.py
=================================================================

A standalone story world for a small mythic tale about a sacred oscillator,
kungfu practice, caution, and teamwork.

Premise:
- A temple keeps a humming oscillator that steadies the lanterns, the wind
  chimes, and the village bell.
- A young student wants to show kungfu moves near the device.
- The elder warns that a careless strike can knock the oscillator off-beat and
  bring trouble.
- The student begins to act rashly, then the team works together: one steadies
  the frame, another guides the breathing, and the elder shows a safer form.
- The oscillator returns to its calm rhythm, and the ending image proves the
  village is safer because the team learned caution.

This script follows the Storyweavers contract:
- self-contained stdlib script
- imports shared results eagerly
- imports shared asp lazily
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import math
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def __post_init__(self):
        for key in ("hum", "harm", "noise", "trust", "fear", "care", "courage", "joy", "focus"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father", "elder"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Device:
    id: str
    label: str
    phrase: str
    rhythm: str
    danger: str
    steadied_by: str
    has_guard: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    calm: str = ""


@dataclass
class StoryParams:
    place: str
    device: str
    tool: str
    hero: str
    helper: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.facts: dict = {}
        self.device_beats: float = 0.0
        self.risk_peak: float = 0.0

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
        w = World(self.place)
        w.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        w.fired = set(self.fired)
        w.device_beats = self.device_beats
        w.risk_peak = self.risk_peak
        return w


SETTINGS = {
    "temple": Place("temple", "the mountain temple", "ancient", {"oscillator", "kungfu"}),
    "courtyard": Place("courtyard", "the courtyard", "open", {"oscillator", "kungfu"}),
    "riverhall": Place("riverhall", "the river hall", "echoing", {"oscillator", "kungfu"}),
}

DEVICES = {
    "oscillator": Device(
        id="oscillator",
        label="oscillator",
        phrase="a brass oscillator that hummed like a sleeping dragon",
        rhythm="steady hum",
        danger="shaken off-beat",
        steadied_by="a careful hand on the base",
        has_guard=True,
    ),
}

TOOLS = {
    "mat": Tool(
        id="mat",
        label="practice mat",
        phrase="a thick practice mat",
        protects={"floor", "feet"},
        calm="softens the steps",
    ),
    "rope": Tool(
        id="rope",
        label="guide rope",
        phrase="a guide rope tied to the frame",
        protects={"hands"},
        calm="keeps the frame from wobbling",
    ),
    "fan": Tool(
        id="fan",
        label="paper fan",
        phrase="a paper fan used for counting breaths",
        protects={"mind"},
        calm="slows the rush of temper",
    ),
}

NAMES = {
    "hero": ["Tao", "Ming", "Jin", "Lian", "Bao", "Ren"],
    "helper": ["Nai", "Hui", "Pao", "Sora", "Wei"],
    "elder": ["Master Stone", "Elder Reed", "Grandmother Cloud"],
}


ASP_RULES = r"""
at_risk(D) :- device(D), danger(D).
unsafe(D) :- at_risk(D), strike_near(D).
safe_fix(D,T) :- at_risk(D), tool(T), protects(T, hands), calms(T, rush).
valid_story(P,D,T) :- place(P), device(D), tool(T), affords(P,D), affords(P,teamwork).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("danger", did))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for pr in sorted(t.protects):
            lines.append(asp.fact("protects", tid, pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, p in SETTINGS.items():
        for did in p.affords:
            for tid in TOOLS:
                if did == "oscillator" and tid in TOOLS:
                    combos.append((pid, did, tid))
    return combos


def reasonableness_gate(place: str, device: str, tool: str) -> bool:
    return place in SETTINGS and device in DEVICES and tool in TOOLS and device in SETTINGS[place].affords


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cautionary teamwork storyworld about an oscillator and kungfu.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--device", choices=DEVICES.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--elder")
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    device = args.device or "oscillator"
    tool = args.tool or rng.choice(list(TOOLS.keys()))
    if not reasonableness_gate(place, device, tool):
        raise StoryError("The chosen place, device, and tool do not make a reasonable story.")
    hero = args.hero or rng.choice(NAMES["hero"])
    helper = args.helper or rng.choice(NAMES["helper"])
    elder = args.elder or rng.choice(NAMES["elder"])
    return StoryParams(place=place, device=device, tool=tool, hero=hero, helper=helper, elder=elder)


def _beat(world: World, actor: Entity, device: Entity, risky: bool = False) -> None:
    actor.memes["focus"] += 0.2
    world.device_beats += 1
    device.meters["hum"] += 0.5
    if risky:
        device.meters["noise"] += 0.6
        world.risk_peak = max(world.risk_peak, device.meters["noise"])


def tell(place: Place, device: Device, tool: Tool, hero: str, helper: str, elder: str) -> World:
    world = World(place)
    h = world.add(Entity(id=hero, kind="character", type="student", label=hero, traits=["young", "brave"]))
    a = world.add(Entity(id=helper, kind="character", type="friend", label=helper, traits=["steady"]))
    e = world.add(Entity(id=elder, kind="character", type="elder", label=elder, traits=["wise"]))
    d = world.add(Entity(id=device.id, type="device", label=device.label, phrase=device.phrase, role="sacred"))
    t = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, role="aid"))

    world.say(f"In {place.name}, people said the {d.label} kept the village breath in one calm line.")
    world.say(f"{h.label} loved kungfu and wanted to show quick turns beside the {d.label}.")
    world.say(f"But {e.label} warned, \"Strike too near, and the {d.label} may slip from its rhythm and wake trouble.\"")
    world.para()

    h.memes["caution"] = 0.0
    h.memes["desire"] = 1.0
    _beat(world, h, d, risky=True)
    world.say(f"{h.label} lifted {h.pronoun('possessive')} hands anyway, and the brass hum grew jumpy.")
    world.say(f"The air felt sharp, as if the mountain itself were holding its breath.")
    world.say(f"{a.label} rushed in, set the {t.label} under the frame, and called for slow feet and slow hands.")
    world.para()

    h.memes["fear"] = 1.0
    h.memes["caution"] = 1.0
    a.memes["care"] = 1.0
    e.memes["joy"] = 1.0
    world.say(f"{e.label} showed a gentler kungfu form: one hand to steady, one step to listen.")
    world.say(f"{a.label} counted the breaths, and {h.label} matched each move to the {d.label}'s hum.")
    d.meters["noise"] = max(0.0, d.meters["noise"] - 0.8)
    d.meters["hum"] += 0.8
    world.say(f"At last the {d.label} settled back into its steady hum, and the lanterns stopped trembling.")
    world.say(f"By dusk, {h.label}, {a.label}, and {e.label} stood together in the warm light, wiser than before.")
    world.facts.update(hero=h, helper=a, elder=e, device=d, tool=t, place=place)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, a, e, d, t, p = f["hero"], f["helper"], f["elder"], f["device"], f["tool"], f["place"]
    return [
        QAItem(
            question=f"Who wanted to show kungfu beside the {d.label} in {p.name}?",
            answer=f"{h.label} wanted to show kungfu beside the {d.label}, but {e.label} warned that the device needed caution.",
        ),
        QAItem(
            question=f"What happened when the hands got too close to the {d.label}?",
            answer=f"The {d.label} became jumpy and its hum grew unsafe until the team steadied it.",
        ),
        QAItem(
            question=f"How did {h.label}, {a.label}, and {e.label} fix the trouble?",
            answer=f"They worked together: {a.label} placed the {t.label} to steady the frame, {e.label} taught a gentler form, and {h.label} slowed down.",
        ),
        QAItem(
            question=f"What did the ending show about the {d.label}?",
            answer=f"It ended in a calm, steady hum, which showed the village was safer after the warning was heeded.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an oscillator?",
            answer="An oscillator is a thing that moves or hums back and forth in a steady rhythm.",
        ),
        QAItem(
            question="What is kungfu?",
            answer="Kungfu is a kind of disciplined movement practice that uses careful hands, feet, and breathing.",
        ),
        QAItem(
            question="Why do teams use caution around fragile things?",
            answer="Teams use caution so they do not break something important, cause harm, or make a safe place unsafe.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a myth-like story about a child, an oscillator, and a lesson in caution.',
        f"Tell a story where {f['hero'].label} wants to do kungfu near an oscillator but learns teamwork.",
        "Write a gentle cautionary myth with a clear warning, a risky moment, and a team fixing the problem together.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role}")
    lines.append(f"  device_beats={world.device_beats:.2f} risk_peak={world.risk_peak:.2f}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DEVICES[params.device], TOOLS[params.tool], params.hero, params.helper, params.elder)
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
        print("== Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="temple", device="oscillator", tool="rope", hero="Tao", helper="Nai", elder="Master Stone"),
    StoryParams(place="courtyard", device="oscillator", tool="mat", hero="Ming", helper="Hui", elder="Elder Reed"),
    StoryParams(place="riverhall", device="oscillator", tool="fan", hero="Jin", helper="Sora", elder="Grandmother Cloud"),
]


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} valid story combos.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
