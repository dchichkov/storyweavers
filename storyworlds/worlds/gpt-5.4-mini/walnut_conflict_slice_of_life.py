#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/walnut_conflict_slice_of_life.py
================================================================

A standalone tiny storyworld for a slice-of-life conflict about a walnut.

Seed idea
---------
A child wants to crack open a walnut during an ordinary afternoon. Another child
or a parent worries about the mess or about keeping the snack for later. The
conflict is small, the turn is practical, and the ending proves the room and the
people changed in a simple, believable way.

This world keeps the scale small:
- one shared kitchen or table setting
- a walnut, a simple cracking tool, and a bowl or plate
- a light conflict that turns into a compromise
- prose that reads like a complete little story, not a log

It follows the Storyweavers storyworld contract:
- self-contained stdlib script
- imports storyworlds/results.py eagerly
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --trace, --qa, --json, --asp, --verify, --show-asp, --all, -n, --seed
- includes Python and ASP reasonableness gates
- generates three QA sets from simulated world state
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
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
class Setting:
    id: str
    place: str
    cozy_detail: str
    surface: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    shell_hard: bool = True
    edible: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    works: bool
    safe: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def copy(self) -> "World":
        clone = World()
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


def _r_crumble(world: World) -> list[str]:
    out: list[str] = []
    walnut = world.get("walnut")
    if walnut.meters["cracked"] < THRESHOLD:
        return out
    if walnut.meters["pieces"] < THRESHOLD:
        sig = ("crumbled", walnut.id)
        if sig not in world.fired:
            world.fired.add(sig)
            walnut.meters["pieces"] += 1
            bowl = world.get("bowl")
            bowl.meters["filled"] += 1
            out.append("__crumbled__")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    walnut = world.get("walnut")
    if walnut.meters["pieces"] < THRESHOLD:
        return out
    for char in world.characters():
        if char.memes["annoyed"] >= THRESHOLD:
            continue
        sig = ("annoyed", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["annoyed"] += 1
        out.append(f"Walnut crumbs dotted the table.")
    return out


CAUSAL_RULES = [
    Rule("crumble", "physical", _r_crumble),
    Rule("mess", "social", _r_mess),
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


def can_open(snack: Snack, tool: Tool) -> bool:
    return snack.shell_hard and tool.works


def sensible_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= SENSE_MIN]


def best_resolution() -> Resolution:
    return max(RESOLUTIONS.values(), key=lambda r: r.sense)


def outcome_power(snack: Snack, delay: int) -> int:
    return 1 + delay


def is_settled(resolution: Resolution, snack: Snack, delay: int) -> bool:
    return resolution.power >= outcome_power(snack, delay)


def predict_conflict(world: World, snack_id: str) -> dict:
    sim = world.copy()
    _do_open(sim, sim.get(snack_id), narrate=False)
    return {
        "crumbled": sim.get(snack_id).meters["pieces"] >= THRESHOLD,
        "annoyance": sum(e.memes["annoyed"] for e in sim.characters()),
    }


def _do_open(world: World, snack: Entity, narrate: bool = True) -> None:
    snack.meters["cracked"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, other: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    other.memes["calm"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {other.id} sat at {setting.place}. "
        f"{setting.cozy_detail}"
    )
    world.say(
        f"{child.id} spotted a walnut on the table and turned it over in {child.pronoun('possessive')} hand."
    )


def want_snack(world: World, child: Entity) -> None:
    child.memes["want"] += 1
    world.say(
        f'"Can I crack it now?" {child.id} asked, smiling at the little hard shell.'
    )


def warn(world: World, other: Entity, child: Entity, snack: Snack) -> None:
    pred = predict_conflict(world, "walnut")
    other.memes["care"] += 1
    world.facts["predicted_crumbles"] = pred["crumbled"]
    world.say(
        f'"Let me help," {other.id} said. "If you rush it, the walnut shell will break '
        f"all over the table.""
    )


def insist(world: World, child: Entity, tool: Tool) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} frowned. {child.pronoun().capitalize()} wanted to use {tool.phrase} right away."
    )


def offer(world: World, other: Entity, child: Entity, snack: Snack, tool: Tool, resolution: Resolution) -> None:
    child.memes["hope"] += 1
    world.say(
        f'"How about we use {tool.phrase} together?" {other.id} asked, "
        f'"so the walnut opens without flying everywhere."'
    )


def accept(world: World, child: Entity, other: Entity, tool: Tool, snack: Snack) -> None:
    child.memes["joy"] += 1
    other.memes["joy"] += 1
    child.memes["defiance"] = 0.0
    world.say(
        f"{child.id}'s face brightened, and {child.id} nodded. Soon they were cracking the walnut carefully with {tool.phrase}."
    )


def do_open(world: World, snack: Entity, tool: Tool) -> None:
    _do_open(world, snack)
    world.say(
        f"{tool.label_word if hasattr(tool, 'label_word') else tool.label} helped crack the walnut open."
    )


def resolve_good(world: World, child: Entity, other: Entity, snack: Entity, tool: Tool, resolution: Resolution) -> None:
    snack.meters["opened"] += 1
    snack.meters["crumbled"] = 0.0
    world.say(
        f"In the end, {other.id} {resolution.text.replace('{target}', snack.label)}."
    )
    world.say(
        "The walnut split neatly, the halves landed in the bowl, and the table stayed almost clean."
    )
    world.say(
        f"{child.id} grinned at the tidy result and passed the bowl closer."
    )


def resolve_bad(world: World, child: Entity, other: Entity, snack: Entity, tool: Tool, resolution: Resolution) -> None:
    snack.meters["opened"] += 1
    world.get("table").meters["messy"] += 1
    world.say(
        f"In the end, {other.id} {resolution.fail.replace('{target}', snack.label)}."
    )
    world.say(
        "The shell burst into sharp pieces, and everyone had to pause and brush the crumbs into a napkin."
    )
    world.say(
        f"{child.id} looked sheepish, and the quiet afternoon felt a little more careful after that."
    )


def tell(setting: Setting, snack: Snack, tool: Tool, resolution: Resolution,
         child_name: str = "Mia", child_gender: str = "girl",
         other_name: str = "Mom", other_gender: str = "mother",
         delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    other = world.add(Entity(id=other_name, kind="character", type=other_gender, role="other"))
    table = world.add(Entity(id="table", type="table", label="the table"))
    bowl = world.add(Entity(id="bowl", type="bowl", label="the bowl"))
    walnut = world.add(Entity(id="walnut", type="walnut", label="the walnut"))
    world.add(table)
    world.add(bowl)
    world.add(walnut)

    intro(world, child, other, setting)
    world.para()
    want_snack(world, child)
    warn(world, other, child, snack)
    insist(world, child, tool)
    offer(world, other, child, snack, tool, resolution)

    world.para()
    if is_settled(resolution, snack, delay):
        accept(world, child, other, tool, snack)
        do_open(world, walnut, tool)
        resolve_good(world, child, other, walnut, tool, resolution)
        outcome = "settled"
    else:
        do_open(world, walnut, tool)
        resolve_bad(world, child, other, walnut, tool, resolution)
        outcome = "messy"

    world.facts.update(
        child=child, other=other, table=table, bowl=bowl, walnut=walnut,
        setting=setting, snack=snack, tool=tool, resolution=resolution,
        outcome=outcome, delay=delay,
    )
    return world


SETTINGS = {
    "kitchen": Setting("kitchen", "the kitchen table", "A small blue mug sat nearby, and the afternoon smelled faintly of tea.", "table"),
    "porch": Setting("porch", "the porch step", "A breeze moved through the screen door, and the light was soft.", "step"),
    "living_room": Setting("living room", "the low coffee table", "A blanket was folded on the armchair, and a lamp made a warm circle on the rug.", "table"),
}

SNACKS = {
    "walnut": Snack("walnut", "walnut", "a walnut", shell_hard=True, edible=True, tags={"walnut", "snack", "shell"}),
    "pecan": Snack("pecan", "pecan", "a pecan", shell_hard=True, edible=True, tags={"pecan", "snack", "shell"}),
    "almond": Snack("almond", "almond", "a shelled almond", shell_hard=False, edible=True, tags={"almond", "snack"}),
}

TOOLS = {
    "nutcracker": Tool("nutcracker", "nutcracker", "the nutcracker", works=True, safe=True, tags={"walnut", "tool"}),
    "spoon": Tool("spoon", "spoon", "a spoon", works=False, safe=True, tags={"tool"}),
    "mug": Tool("mug", "mug", "a mug edge", works=False, safe=False, tags={"tool"}),
}

RESOLUTIONS = {
    "nutcracker": Resolution(
        "nutcracker", 3, 3,
        "used the nutcracker carefully and opened {target} cleanly",
        "tried to use the nutcracker, but the shell shattered into a mess",
        "used the nutcracker carefully and opened the walnut cleanly",
        tags={"walnut", "tool"},
    ),
    "bowl_hold": Resolution(
        "bowl_hold", 2, 2,
        "held the bowl under the shell and cracked {target} slowly over it",
        "pressed too hard and sent pieces skittering everywhere",
        "held the bowl under the walnut and cracked it slowly over it",
        tags={"walnut", "bowl"},
    ),
    "napkin_wrap": Resolution(
        "napkin_wrap", 2, 2,
        "wrapped {target} in a napkin and tapped it open with patience",
        "hit the shell too sharply and made a little crunching mess",
        "wrapped the walnut in a napkin and tapped it open with patience",
        tags={"walnut", "napkin"},
    ),
    "spoon": Resolution(
        "spoon", 1, 1,
        "used the spoon and hoped the shell would give way",
        "used the spoon, but it only made the shell fly apart",
        "used the spoon and hoped the shell would give way",
        tags={"walnut", "tool"},
    ),
}

NAME_PAIRS = [
    ("Mia", "mom", "mother"),
    ("Eli", "dad", "father"),
    ("Nora", "grandma", "mother"),
    ("Theo", "uncle", "father"),
]

TRAITS = ["patient", "curious", "gentle", "careful", "quiet", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for snack_id, snack in SNACKS.items():
            for tool_id, tool in TOOLS.items():
                if snack.shell_hard and tool.works:
                    combos.append((sid, snack_id, tool_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    snack: str
    tool: str
    resolution: str
    child: str
    child_gender: str
    other: str
    other_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    snack = f["snack"]
    setting = f["setting"]
    return [
        f'Write a slice-of-life story for a small child that includes the word "{snack.label}" and a small family conflict.',
        f"Tell a calm everyday story where {child.id} wants to open {snack.phrase} at {setting.place}, but a grown-up worries about the mess.",
        f"Write a gentle kitchen-or-porch story about a walnut and a disagreement that ends in a practical compromise.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, other, snack, tool = f["child"], f["other"], f["snack"], f["tool"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {other.id}, who shared a quiet everyday moment around a snack."),
        ("Why was there a conflict?",
         f"{child.id} wanted to open the {snack.label} right away, but {other.id} worried the shell would make a mess on the table. The disagreement was small, but it mattered because they both cared about keeping the room tidy."),
        ("What changed in the end?",
         f"They chose a careful way to open the {snack.label}, so the snack could be shared without making a big mess. The ending shows them settling down together instead of arguing."),
    ]
    if f["outcome"] == "settled":
        qa.append((
            "How did they solve the problem?",
            f"They used {tool.phrase} and took their time, which let them open the walnut cleanly. Because the tool worked, they did not have to stop and clean crumbs from the table."
        ))
    else:
        qa.append((
            "How did the attempt go?",
            f"Their first try was too rough, so the shell broke into crumbs and everyone had to clean up. That made the afternoon feel a little more serious before it calmed down again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["snack"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    if "walnut" in tags:
        out.append(("What is a walnut?",
                     "A walnut is a hard-shelled nut. People crack it open to reach the soft part inside."))
    if "tool" in tags:
        out.append(("Why use the right tool for a hard shell?",
                     "The right tool helps open a hard shell more neatly and with less mess. It also makes the job easier and safer."))
    if "shell" in tags:
        out.append(("What is a shell on a nut?",
                     "A shell is the hard outer part that protects the nut inside."))
    return out


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "walnut", "nutcracker", "nutcracker", "Mia", "girl", "mom", "mother", "patient", 0),
    StoryParams("living_room", "walnut", "nutcracker", "bowl_hold", "Eli", "boy", "dad", "father", "careful", 0),
    StoryParams("porch", "pecan", "nutcracker", "napkin_wrap", "Nora", "girl", "grandma", "mother", "gentle", 1),
]


def explain_rejection(snack: Snack, tool: Tool) -> str:
    if not snack.shell_hard:
        return "(No story: that snack does not need cracking, so there is no real conflict.)"
    if not tool.works:
        return f"(No story: {tool.label} will not open a hard shell in a believable way.)"
    return "(No story: this combination does not create a reasonable slice-of-life conflict.)"


def outcome_of(params: StoryParams) -> str:
    if is_settled(RESOLUTIONS[params.resolution], SNACKS[params.snack], params.delay):
        return "settled"
    return "messy"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sn in SNACKS.values():
        lines.append(asp.fact("snack", sn.id))
        if sn.shell_hard:
            lines.append(asp.fact("shell_hard", sn.id))
    for tl in TOOLS.values():
        lines.append(asp.fact("tool", tl.id))
        if tl.works:
            lines.append(asp.fact("works", tl.id))
        if tl.safe:
            lines.append(asp.fact("safe", tl.id))
    for rid, res in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", rid))
        lines.append(asp.fact("sense", rid, res.sense))
        lines.append(asp.fact("power", rid, res.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, N, T) :- setting(S), snack(N), tool(T), shell_hard(N), works(T).
sensible(R) :- resolution(R), sense(R, S), sense_min(M), S >= M.
settled(R, N, D) :- resolution(R), power(R, P), shell_hard(N), delay(D), P >= 1 + D.
outcome(settled) :- chosen(R), chosen_snack(N), chosen_delay(D), settled(R, N, D).
outcome(messy) :- chosen(R), chosen_snack(N), chosen_delay(D), not settled(R, N, D).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen", params.resolution),
        asp.fact("chosen_snack", params.snack),
        asp.fact("chosen_delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        rc = 1
    if set(asp_sensible()) == set(RESOLUTIONS):
        print("OK: sensible resolutions match.")
    else:
        print("MISMATCH in sensible resolutions.")
        rc = 1
    samples = [CURATED[0]]
    for p in samples:
        if asp_outcome(p) != outcome_of(p):
            print("MISMATCH in outcome model.")
            rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life walnut conflict storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--other")
    ap.add_argument("--other-gender", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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
    if args.snack and args.tool and not (SNACKS[args.snack].shell_hard and TOOLS[args.tool].works):
        raise StoryError(explain_rejection(SNACKS[args.snack], TOOLS[args.tool]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, snack, tool = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(RESOLUTIONS))
    child = args.child or rng.choice(["Mia", "Eli", "Nora", "Theo"])
    child_gender = args.child_gender or ("girl" if child in {"Mia", "Nora"} else "boy")
    other = args.other or rng.choice(["Mom", "Dad", "Grandma", "Uncle"])
    other_gender = args.other_gender or ("mother" if other in {"Mom", "Grandma"} else "father")
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(setting, snack, tool, resolution, child, child_gender, other, other_gender, trait, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SNACKS[params.snack],
        TOOLS[params.tool],
        RESOLUTIONS[params.resolution],
        params.child,
        params.child_gender,
        params.other,
        params.other_gender,
        params.delay,
    )
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for s, n, t in combos:
            print(f"  {s:12} {n:8} {t}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and {p.other}: {p.snack} / {p.resolution} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
