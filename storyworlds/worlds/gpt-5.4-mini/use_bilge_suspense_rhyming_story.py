#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/use_bilge_suspense_rhyming_story.py
====================================================================

A standalone storyworld for a small suspenseful rhyming tale on a little boat:
a child notices the bilge filling with water, finds a safe way to use a tool,
calls for help, and the boat is saved before the night tide can win.

The world is tiny on purpose:
- one boat
- one bilge
- one leak
- one careful child
- one helpful grown-up
- one simple rescue tool

The prose is built from world state, not from a frozen paragraph template.
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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    sky: str
    sound: str


@dataclass
class Leak:
    id: str
    label: str
    phrase: str
    cause: str
    danger: str
    spread: int = 1
    leak_rate: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use_text: str
    power: int
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Rescue:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.leak_active: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.leak_active = self.leak_active
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_flood(world: World) -> list[str]:
    out: list[str] = []
    bilge = world.get("bilge")
    if bilge.meters["water"] < THRESHOLD:
        return out
    sig = ("flood",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("boat").meters["risk"] += 1
    for eid in ("child", "adult"):
        world.get(eid).memes["worry"] += 1
    out.append("__suspense__")
    return out


CAUSAL_RULES = [Rule("flood", _r_flood)]


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


def leak_bilge(world: World) -> None:
    if world.leak_active:
        return
    world.leak_active = True
    world.get("bilge").meters["water"] += 1
    world.get("bilge").meters["leak"] += 1
    propagate(world, narrate=False)


def find_tool(world: World, tool: Tool) -> None:
    world.say(
        f"On a moonlit night aboard the little boat, {world.get('child').id} heard a soft drip-drip sound."
    )
    world.say(
        f"The wind was cold, the waves were sly, and the bilge sat below, hidden from the sky."
    )
    world.say(
        f"{world.get('child').id} peered down and saw the bilge begin to fill. "
        f"It looked small at first, but it felt quite still and chill."
    )
    world.say(
        f'"We must {tool.use_text}," {world.get("child").id} said. "If we wait, the boat may tilt."'
    )


def predict_outcome(world: World, tool: Tool) -> dict:
    sim = world.copy()
    leak_bilge(sim)
    apply_tool(sim, sim.get("child"), tool, narrate=False)
    return {
        "saved": sim.get("bilge").meters["water"] < THRESHOLD,
        "risk": sim.get("boat").meters["risk"],
    }


def use_tool(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    actor.memes["courage"] += 1
    world.get("bilge").meters["water"] = max(0.0, world.get("bilge").meters["water"] - tool.power)
    world.get("bilge").meters["used"] += 1
    if world.get("bilge").meters["water"] < THRESHOLD:
        world.get("boat").meters["risk"] = 0
    if narrate:
        world.say(
            f'{actor.id} did not frown or fuss; {actor.pronoun()} chose to {tool.use_text}. '
            f'With a quick, brave push, {tool.label} helped the water go less high.'
        )


def apply_tool(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    use_tool(world, actor, tool, narrate=narrate)
    propagate(world, narrate=False)


def call_help(world: World) -> None:
    adult = world.get("adult")
    child = world.get("child")
    if world.get("bilge").meters["water"] >= THRESHOLD:
        world.say(f"{child.id} called, \"{adult.label_word.capitalize()}! The bilge is getting full!\"")
    else:
        world.say(f"{child.id} called, \"{adult.label_word.capitalize()}! We fixed it in time!\"")


def rescue(world: World, adult: Entity, rescue_tool: Rescue, tool: Tool) -> None:
    bilge = world.get("bilge")
    boat = world.get("boat")
    if rescue_tool.power >= bilge.meters["water"] + 1:
        bilge.meters["water"] = 0
        boat.meters["risk"] = 0
        adult.memes["relief"] += 1
        world.say(
            f"{adult.label_word.capitalize()} came fast as a flash and {rescue_tool.success.replace('{tool}', tool.label)}."
        )
        world.say("The water slipped away, and the boat rose calm upon the spray.")
    else:
        boat.meters["risk"] += 1
        world.say(
            f"{adult.label_word.capitalize()} came fast as a flash, but {rescue_tool.fail.replace('{tool}', tool.label)}."
        )
        world.say("The bilge still swished with water, and the little boat gave a nervous sway.")


def ending(world: World) -> None:
    child = world.get("child")
    bilge = world.get("bilge")
    if bilge.meters["water"] <= 0:
        child.memes["joy"] += 1
        world.say(
            "Then the stars shone bright and clear, and the boat stayed steady in the tide. "
            f"{child.id} smiled, dry and proud, with a safe ship to guide."
        )
    else:
        child.memes["worry"] += 1
        world.say(
            "Then the stars stayed far and dim, and the boat rocked soft and slow. "
            f"But help had come, and that was good, for now they knew what to do."
        )


def tell(setting: Setting, leak: Leak, tool: Tool, rescue_tool: Rescue,
         child_name: str = "Nia", child_gender: str = "girl",
         adult_gender: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_gender, role="adult", label="the adult"))
    world.add(Entity(id="boat", type="boat", label="the little boat"))
    world.add(Entity(id="bilge", type="bilge", label="the bilge"))

    child.memes["curious"] = 1
    child.memes["brave"] = 1

    world.say(f"The {setting.place} rocked gently while {setting.sky} glowed above the sea.")
    world.say(f"{child.id} loved the {setting.sound}, like a tune in a rhyme.")
    world.say(f"Below deck hid the bilge, where boats keep water out of the way, every time.")

    world.para()
    find_tool(world, tool)
    leak_bilge(world)
    world.say(f"A tiny leak from {leak.cause} made the bilge begin to rise with a little gray shine.")
    world.say(f"It was not a joke, not a game, for {leak.danger} can turn a trip into frightful time.")

    world.para()
    pred = predict_outcome(world, tool)
    world.facts["predicted_risk"] = pred["risk"]
    if pred["saved"]:
        world.say(f"{child.id} knew the answer at once and chose to use {tool.label} right away.")
        apply_tool(world, child, tool, narrate=True)
        call_help(world)
        rescue(world, adult, rescue_tool, tool)
        ending(world)
        outcome = "saved"
    else:
        world.say(f"{child.id} tried to use {tool.label}, but the bilge stayed wet and the water would not sway.")
        call_help(world)
        rescue(world, adult, rescue_tool, tool)
        ending(world)
        outcome = "at_risk"

    world.facts.update(
        child=child,
        adult=adult,
        leak=leak,
        tool=tool,
        rescue_tool=rescue_tool,
        setting=setting,
        outcome=outcome,
        saved=(outcome == "saved"),
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "harbor", "silver moon", "hush of waves"),
    "bay": Setting("bay", "bay", "pink evening sky", "soft splash of water"),
    "dock": Setting("dock", "dock", "dark clouds", "creak of ropes"),
}

LEAKS = {
    "seam": Leak("seam", "seam leak", "a seam in the hull", "the old seam in the hull", "the boat could sink", spread=1, leak_rate=1.0, tags={"water", "boat"}),
    "plug": Leak("plug", "loose plug", "a loose plug below deck", "a loose plug by the floorboards", "the bilge could flood", spread=1, leak_rate=1.0, tags={"water", "boat"}),
}

TOOLS = {
    "bucket": Tool("bucket", "bucket", "a little bucket", "bail out the bilge", power=2, tags={"water", "bucket"}),
    "pump": Tool("pump", "pump", "a hand pump", "pump the bilge dry", power=3, tags={"water", "pump"}),
}

RESCUES = {
    "patch": Rescue("patch", 3, 3, "patched the leak and pumped fast with {tool}", "patched the leak, but the bilge was too full for {tool}", "patched the leak and pumped fast with {tool}", tags={"repair"}),
    "bail": Rescue("bail", 2, 2, "bailed and bailed until the bilge went dry with {tool}", "bailed with {tool}, but the water kept rising", "bailed and bailed until the bilge went dry with {tool}", tags={"repair"}),
}

GIRL_NAMES = ["Nia", "Luna", "Mira", "Sia", "Mona", "Rosa"]
BOY_NAMES = ["Finn", "Theo", "Milo", "Nico", "Leo", "Jude"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for lid in LEAKS:
            for tid in TOOLS:
                if TOOLS[tid].power >= 2:
                    combos.append((sid, lid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    leak: str
    tool: str
    rescue: str
    child: str
    child_gender: str
    adult_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful rhyming bilge storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--leak", choices=LEAKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--rescue", choices=RESCUES)
    ap.add_argument("--child")
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--adult", dest="adult_gender", choices=["mother", "father"])
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid in LEAKS:
        lines.append(asp.fact("leak", lid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("power", tid, t.power))
    for rid in RESCUES:
        lines.append(asp.fact("rescue", rid))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, L, T) :- setting(S), leak(L), tool(T), power(T, P), P >= 2.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.tool and TOOLS[args.tool].power < 2:
        raise StoryError("That tool is too weak to make a sensible rescue story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.leak is None or c[1] == args.leak)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, leak, tool = rng.choice(sorted(combos))
    rescue = args.rescue or rng.choice(sorted(RESCUES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    return StoryParams(setting, leak, tool, rescue, child, child_gender, adult_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a suspenseful rhyming story for a small child that includes the word "bilge".',
        f"Tell a rhyming boat story where {f['child'].id} notices water in the bilge and uses {f['tool'].label} to help before the boat gets in trouble.",
        f'Write a gentle suspense story with a child, a leaky bilge, and a safe rescue tool, ending with the boat steady again.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    tool = f["tool"]
    rescue = f["rescue_tool"]
    leak = f["leak"]
    qa = [
        ("What did the child notice?",
         f"{child.id} noticed water in the bilge below deck. That meant the boat needed help before the night tide could rise higher."),
        ("What did the child use?",
         f"{child.id} used {tool.label} to help with the water. The tool was safe and strong enough to change the bilge from scary to steady."),
        ("Who came to help at the end?",
         f"{adult.label_word.capitalize()} came to help after the child called. {rescue.qa_text.replace('{tool}', tool.label).capitalize()}."),
    ]
    if f["saved"]:
        qa.append(("How did the story end?",
                   f"It ended safely, with the bilge dry and the boat calm again. The child chose a careful action, and that brave choice kept the trip from sinking into trouble."))
    else:
        qa.append(("How did the story end?",
                   f"It ended with the bilge still in trouble, though help arrived. The child had tried hard, but the water was too much for that moment."))
    qa.append(("Why was the bilge a worry?",
                f"The bilge mattered because if water keeps rising there, the boat can tilt or sink. That is why {leak.danger} made everyone feel suspenseful."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bilge?",
         "The bilge is the lowest inside part of a boat. Water gathers there, so people keep it dry."),
        ("Why is water in a boat dangerous?",
         "Water in a boat can make it heavy and unsteady. If too much gets in, the boat may sink."),
        ("What does it mean to use something?",
         "To use something means to do an action with it to help solve a problem or get a job done."),
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "seam", "bucket", "patch", "Nia", "girl", "mother"),
    StoryParams("bay", "plug", "pump", "bail", "Milo", "boy", "father"),
]


def explain_rejection(tool: Tool) -> str:
    return f"(No story: {tool.label} is too weak for this bilge suspense tale.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        LEAKS[params.leak],
        TOOLS[params.tool],
        RESCUES[params.rescue],
        params.child,
        params.child_gender,
        params.adult_gender,
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


def asp_verify() -> int:
    import asp
    ok = set(asp_valid_combos()) == set(valid_combos())
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Generated story was empty.")
    if ok:
        print("OK: ASP parity and story generation smoke test passed.")
        return 0
    print("MISMATCH: ASP parity failed.")
    return 1


def resolve_choices(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.leak is None or c[1] == args.leak)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, leak, tool = rng.choice(sorted(combos))
    rescue = args.rescue or rng.choice(sorted(RESCUES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    adult_gender = args.adult_gender or rng.choice(["mother", "father"])
    return StoryParams(setting, leak, tool, rescue, child, child_gender, adult_gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, leak, tool) combos:")
        for s, l, t in asp_valid_combos():
            print(f"  {s:8} {l:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
                params = resolve_choices(args, random.Random(seed))
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
