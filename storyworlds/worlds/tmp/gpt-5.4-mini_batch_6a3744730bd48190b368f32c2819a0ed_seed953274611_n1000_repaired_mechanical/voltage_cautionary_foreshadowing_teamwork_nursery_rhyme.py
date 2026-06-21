#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/voltage_cautionary_foreshadowing_teamwork_nursery_rhyme.py
==========================================================================================

A tiny storyworld built from the seed words and features:

- word: voltage
- features: cautionary, foreshadowing, teamwork
- style: nursery rhyme

Premise:
A small household rhyme-world has a curious child and a helpful friend who
find a humming lamp-house. They want to fix a dim lantern, but a warning clue
suggests the wrong wire may be too strong. Together they choose a safe, simple
repair and end with a bright, child-friendly light.

This script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py API. The ASP twin is inline, imported lazily.
"""

from __future__ import annotations

import argparse
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
VOLTAGE_DANGER = 5.0


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
    sparky: bool = False
    repairable: bool = False
    safe_tool: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    phrase: str
    rhyme: str
    dark_spot: str
    bright_spot: str
    clue: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Hazard:
    id: str
    label: str
    phrase: str
    hum: str
    warning: str
    danger: float = 5.0
    makes_spark: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class RepairTool:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    strength: float
    safe: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str = "nursery"
    hazard: str = "wall_socket"
    tool: str = "tape"
    helper: str = "Mabel"
    helper_gender: str = "girl"
    lead: str = "Robin"
    lead_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _r_warm(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["voltage"] < THRESHOLD:
            continue
        sig = ("warm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["buzz"] += 1
        out.append("__buzz__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _r_warm(world):
            changed = True
            if sent != "__buzz__":
                produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "nursery": Setting(
        id="nursery",
        phrase="a little nursery with patchwork quilts",
        rhyme="nursery",
        dark_spot="the corner by the cradle",
        bright_spot="the little lamp on the shelf",
        clue="the lamp gave a tiny warning hum",
    ),
    "kitchen": Setting(
        id="kitchen",
        phrase="a tidy kitchen with a tea-tin shelf",
        rhyme="kitchen",
        dark_spot="the nook by the sink",
        bright_spot="the lamp above the table",
        clue="the cord gave a tiny warning hum",
    ),
}

HAZARDS = {
    "wall_socket": Hazard(
        id="wall_socket",
        label="wall socket",
        phrase="a wall socket",
        hum="hum",
        warning="the socket had a tiny crackle",
        danger=6.0,
        makes_spark=True,
    ),
    "cord": Hazard(
        id="cord",
        label="cord",
        phrase="a loose cord",
        hum="buzz",
        warning="the cord felt warm and gave a tiny buzz",
        danger=4.0,
        makes_spark=True,
    ),
}

TOOLS = {
    "tape": RepairTool(
        id="tape",
        label="tape",
        phrase="a roll of cloth tape",
        action="wrap the loose cord with cloth tape",
        result="the cord held still and quiet",
        strength=4.0,
    ),
    "call_adult": RepairTool(
        id="call_adult",
        label="grown-up help",
        phrase="a grown-up helper",
        action="call for a grown-up helper",
        result="the safe helper came quickly",
        strength=10.0,
    ),
    "toy_box": RepairTool(
        id="toy_box",
        label="toy box",
        phrase="a toy box lid",
        action="put a toy box lid over it",
        result="nothing changed at all",
        strength=1.0,
    ),
}


def hazard_is_reasonable(h: Hazard) -> bool:
    return h.makes_spark and h.danger >= 4.0


def tool_is_reasonable(t: RepairTool) -> bool:
    return t.strength >= 4.0


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for hid, h in HAZARDS.items():
            if not hazard_is_reasonable(h):
                continue
            for tid, t in TOOLS.items():
                if tool_is_reasonable(t):
                    combos.append((sid, hid, tid))
    return combos


def predict(world: World, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get("hazard").meters["voltage"] += hazard.danger
    propagate(sim, narrate=False)
    return {"spark": sim.get("hazard").meters["buzz"] >= THRESHOLD}


def foreshadow(world: World, setting: Setting, hazard: Hazard) -> None:
    world.say(
        f"In {setting.phrase}, the air was quiet as a bell. "
        f"{setting.clue}, and {setting.dark_spot} looked a little shy."
    )
    world.say(
        f'Robin blinked and said, "That {hazard.label} sounds odd."'
    )


def teamwork_request(world: World, lead: Entity, helper: Entity, tool: RepairTool) -> None:
    lead.memes["hope"] += 1
    helper.memes["help"] += 1
    world.say(
        f"{lead.id} looked at {helper.id} and smiled. "
        f'"Let\'s work together," {lead.id} said, "and {tool.action}."'
    )


def caution(world: World, helper: Entity, hazard: Hazard) -> None:
    helper.memes["caution"] += 1
    world.say(
        f"{helper.id} pointed with care. "
        f'"Wait a bit," {helper.id} said. "{hazard.warning}. '
        f"Big voltage is not a game."'
    )


def do_risky(world: World, hazard: Hazard) -> None:
    world.get("hazard").meters["voltage"] += hazard.danger
    propagate(world, narrate=False)
    world.say(
        f"The {hazard.label} gave a little crackle, then a bright spark woke up."
    )


def repair(world: World, tool: RepairTool) -> None:
    if tool.id == "call_adult":
        world.get("hazard").meters["voltage"] = 0.0
        world.say(
            f"They did the wise thing and {tool.action}. "
            f"{tool.result}, and the spark was gone."
        )
        return
    if tool.strength < 4.0:
        raise StoryError("The chosen tool is too weak for this cautionary story.")
    world.get("hazard").meters["voltage"] = 0.0
    world.say(
        f"Together they {tool.action}. {tool.result}, and the little hum went soft."
    )


def ending(world: World, setting: Setting, lead: Entity, helper: Entity) -> None:
    world.say(
        f"Then the lamp in the {setting.rhyme} glowed again, "
        f"and the two friends clapped like rain on a tin pan."
    )
    world.say(
        f"They tidied the room, side by side, and the safe light shone over "
        f"{setting.bright_spot}."
    )


def tell(setting: Setting, hazard: Hazard, tool: RepairTool,
         lead_name: str, lead_gender: str,
         helper_name: str, helper_gender: str, parent: str) -> World:
    world = World(setting)
    lead = world.add(Entity(id=lead_name, kind="character", type=lead_gender, role="lead"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    adult = world.add(Entity(id="Adult", kind="character", type=parent, role="adult", label="the grown-up"))
    hz = world.add(Entity(id="hazard", kind="thing", type=hazard.id, label=hazard.label, sparky=True))
    world.facts.update(setting=setting, hazard=hazard, tool=tool, lead=lead, helper=helper, adult=adult)

    foreshadow(world, setting, hazard)
    world.para()
    teamwork_request(world, lead, helper, tool)
    caution(world, helper, hazard)

    if hazard.danger >= VOLTAGE_DANGER:
        world.say(
            f"{lead.id} nearly touched the {hazard.label}, but {helper.id} held {lead.id}'s hand."
        )
        do_risky(world, hazard)
    else:
        world.say(
            f"{lead.id} paused, remembering the little warning."
        )

    world.para()
    repair(world, tool)
    ending(world, setting, lead, helper)
    world.events.append("safe_finish")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hazard = f["hazard"]
    return [
        f'Write a nursery-rhyme style story that uses the word "{hazard.label}" and the word "voltage".',
        f"Tell a cautionary rhyme about {f['lead'].id} and {f['helper'].id} who notice a warning clue before touching {hazard.phrase}.",
        f"Write a teamwork story where two children listen for danger, notice voltage, and choose a safe fix together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hazard = f["hazard"]
    tool = f["tool"]
    lead = f["lead"]
    helper = f["helper"]
    setting = f["setting"]
    qa = [
        ("Who is the story about?",
         f"It is about {lead.id} and {helper.id}, two small friends in {setting.phrase}. They watch the room closely and help each other solve a problem."),
        ("What warning clue did they notice?",
         f"They noticed that {setting.clue}. That was a foreshadowing clue, because it hinted that something electric might be unsafe."),
        ("Why did {0} warn {1}?".format(helper.id, lead.id),
         f"{helper.id} warned {lead.id} because the {hazard.label} could carry too much voltage. A careful warning kept their teamwork safe."),
        ("What did they do together?",
         f"They used {tool.phrase} and worked side by side. Their teamwork fixed the problem without making the danger bigger."),
        ("How did the story end?",
         f"It ended with a safe, bright room. The little voltage trouble was gone, and the children could smile at the lamp again."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is voltage?",
         "Voltage is a measure of how strongly electricity pushes. If it is too high, it can be dangerous."),
        ("Why should children be careful around electricity?",
         "Electricity can give a shock or start trouble if it is handled the wrong way. Grown-ups should help with wires, sockets, and repairs."),
        ("What is teamwork?",
         "Teamwork means people help one another and do a job together. It often makes a hard task easier and safer."),
        ("What does foreshadowing mean?",
         "Foreshadowing is a little clue that hints something important may happen soon. In stories, it helps readers feel the warning before the turn."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, hazard: Hazard, tool: RepairTool) -> str:
    if not hazard_is_reasonable(hazard):
        return f"(No story: {hazard.label} is not a strong enough voltage danger for this world.)"
    if not tool_is_reasonable(tool):
        return f"(No story: {tool.label} is too weak for a safe teamwork repair.)"
    return "(No story: this combination does not make a clear cautionary tale.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and not tool_is_reasonable(TOOLS[args.tool]):
        raise StoryError(explain_rejection(SETTINGS[args.setting or "nursery"], HAZARDS[args.hazard or "wall_socket"], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, hazard, tool = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        hazard=hazard,
        tool=tool,
        helper=args.helper or rng.choice(["Mabel", "Nina", "Junie", "Pip"]),
        helper_gender=helper_gender,
        lead=args.lead or rng.choice(["Robin", "Teddy", "Benny", "Lottie"]),
        lead_gender=lead_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hazard not in HAZARDS or params.tool not in TOOLS:
        raise StoryError("Invalid params: unknown setting, hazard, or tool.")
    world = tell(
        SETTINGS[params.setting],
        HAZARDS[params.hazard],
        TOOLS[params.tool],
        params.lead,
        params.lead_gender,
        params.helper,
        params.helper_gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
    StoryParams(setting="nursery", hazard="wall_socket", tool="tape", helper="Mabel", helper_gender="girl", lead="Robin", lead_gender="boy", parent="mother"),
    StoryParams(setting="kitchen", hazard="cord", tool="call_adult", helper="Nina", helper_gender="girl", lead="Teddy", lead_gender="boy", parent="father"),
]


def valid_params_list() -> list[StoryParams]:
    return CURATED


ASP_RULES = r"""
hazard(H) :- hazard(Hid), danger(Hid, D), D >= 4.
tool_ok(T) :- tool(Tid), strength(Tid, S), S >= 4.
valid(S, H, T) :- setting(S), hazard(H), tool(T), hazard(H), tool_ok(T).
safe_finish :- chosen_tool(T), strength(T, S), S >= 4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("danger", hid, int(h.danger)))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("strength", tid, int(t.strength)))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in valid_combos:")
        print("python only:", sorted(py - cl))
        print("clingo only:", sorted(cl - py))
    else:
        print(f"OK: ASP matches Python ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        assert sample.prompts
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme cautionary storyworld about voltage, foreshadowing, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--lead")
    ap.add_argument("--lead-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(row)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
