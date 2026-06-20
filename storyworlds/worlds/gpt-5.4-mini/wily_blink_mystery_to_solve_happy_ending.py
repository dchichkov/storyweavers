#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/wily_blink_mystery_to_solve_happy_ending.py
============================================================================

A standalone story world for a tiny pirate-style mystery: a curious child,
a wily clue, a blink of light, a small puzzle to solve, and a happy ending.

The world stays small and classical:
- typed entities with meters and memes
- world state drives prose
- a reasonableness gate that rejects weak combinations
- a Python/ASP twin for the key constraints
- three Q&A sets grounded in simulated state

Seed words: wily, blink
Seed features: Mystery to Solve, Happy Ending, Curiosity
Style note: close to a pirate tale, but fresh content.
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
REQUIRED_WORDS = ("wily", "blink")


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    clues: list[str] = field(default_factory=list)

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
    scene: str
    hidey: str
    beacon: str
    send_off: str


@dataclass
class Mystery:
    id: str
    mystery: str
    clue: str
    clue_site: str
    clue_reveal: str
    answer: str
    on_seeing: str


@dataclass
class Tool:
    id: str
    label: str
    shine: str
    plural: bool = False
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_joy(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.role == "child" and e.memes["curiosity"] >= THRESHOLD and e.meters["progress"] >= THRESHOLD:
            sig = ("joy", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["joy"] += 1
            out.append("__joy__")
    return out


CAUSAL_RULES = [Rule("joy", _r_joy)]


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


SETTINGS = {
    "deck": Setting("deck", "the ship's deck", "The deck was bright with ropes, barrels, and a mast that creaked softly.", "below the hatch", "the lantern rail", "sailed on with a grin"),
    "cove": Setting("cove", "the secret cove", "The cove was quiet, with tide pools, gulls, and a cave mouth that looked sleepy.", "behind the rock arch", "the torch stand", "rowed home smiling"),
}

MYSTERIES = {
    "missing_map": Mystery(
        "missing_map",
        "a missing map",
        "a wet corner with a tiny salt mark",
        "the captain's crate",
        "the corner of the crate was damp",
        "the map had slipped under a loose board",
        "a loose board gave the answer a little wiggle",
    ),
    "singing_key": Mystery(
        "singing_key",
        "a singing key",
        "a faint jingle by the rope basket",
        "the rope basket",
        "the basket had a shiny key tucked in its weave",
        "the key had fallen into the basket",
        "a shiny tangle gave the secret away",
    ),
    "blink_lantern": Mystery(
        "blink_lantern",
        "a blinking lantern",
        "a blink of light in the dark hatch",
        "the dark hatch",
        "the lantern blinked once more when the child leaned close",
        "the lantern needed a new wick",
        "a tiny blink was the clue all along",
    ),
}

TOOLS = {
    "lantern": Tool("lantern", "a little lantern", "glowed warm and steady", tags={"light"}),
    "spyglass": Tool("spyglass", "a spyglass", "caught the far-off shine", tags={"look"}),
    "glowstone": Tool("glowstone", "a glowstone", "gave off a soft green gleam", tags={"light"}),
}

CHILD_NAMES = ["Mira", "Toby", "Nia", "Finn", "Lula", "Owen", "Pia", "Jude"]
PARENT_NAMES = ["Mom", "Dad"]


def reasonableness_ok(setting: Setting, mystery: Mystery, tool: Tool) -> bool:
    return True if tool.id in {"lantern", "spyglass", "glowstone"} else False


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, m, t) for s in SETTINGS for m in MYSTERIES for t in TOOLS if reasonableness_ok(SETTINGS[s], MYSTERIES[m], TOOLS[t])]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate-style mystery story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
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
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M, T) :- setting(S), mystery(M), tool(T), tool_ok(T).
tool_ok(lantern).
tool_ok(spyglass).
tool_ok(glowstone).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(valid_combos()) == set(asp_valid_combos())
    if ok:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in gate.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mystery=None, tool=None, child=None, child_gender=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in CHILD_NAMES if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    child = args.child or rng.choice(CHILD_NAMES)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting, mystery, tool, child, child_gender, parent)


def tell(params: StoryParams) -> World:
    w = World()
    s = SETTINGS[params.setting]
    m = MYSTERIES[params.mystery]
    t = TOOLS[params.tool]
    child = w.add(Entity(params.child, kind="character", type=params.child_gender, role="child", traits=["curious", "wily"]))
    parent = w.add(Entity(params.parent, kind="character", type="mother" if params.parent == "Mom" else "father", role="parent"))
    clue = w.add(Entity("clue", label=m.clue, attrs={"site": m.clue_site}))
    tool = w.add(Entity(t.id, label=t.label, attrs={"shine": t.shine}))
    child.memes["curiosity"] = 1.0
    w.say(f"On a bright day, {child.id} and {params.parent} roamed the {s.place}. {s.scene}")
    w.say(f'"{child.id} was feeling wily," {child.id} whispered, because {child.pronoun()} wanted to solve {m.mystery}.')
    w.para()
    w.say(f"{child.id} blinked and peered at {m.clue_site}. {m.on_seeing}.")
    w.say(f"Then {child.id} and {params.parent} used {t.label} and a careful look to search.")
    child.meters["progress"] += 1
    child.clues.append(m.clue)
    child.clues.append(m.clue_reveal)
    if params.mystery == "blink_lantern":
        child.meters["progress"] += 1
    propagate(w, narrate=False)
    w.para()
    w.say(f"At last, {m.clue_reveal}. {params.parent} smiled and {m.on_seeing}.")
    child.memes["joy"] += 1
    child.meters["done"] += 1
    w.say(f"The mystery was solved, and {child.id} left with a happy heart. {s.send_off}.")
    w.facts.update(setting=s, mystery=m, tool=t, child=child, parent=parent, clue=clue, outcome="happy", solved=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate-style mystery for a young child that includes the words "{REQUIRED_WORDS[0]}" and "{REQUIRED_WORDS[1]}".',
        f"Tell a curious little story where {f['child'].id} uses {f['tool'].label} to solve {f['mystery'].mystery}.",
        f"Write a happy-ending mystery about a child on {f['setting'].place} who spots a clue and solves it with a grown-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    m = f["mystery"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {child.id} and {parent.id}, who went looking for a mystery together. The child stayed curious the whole time."),
        QAItem(question="What mystery did they solve?", answer=f"They solved {m.mystery}. They followed a clue and found the answer at the end."),
        QAItem(question="How did the child feel at the end?", answer=f"{child.id} felt happy and proud. Solving the mystery turned the curious search into a joyful ending."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does wily mean?", answer="Wily means clever in a sneaky or tricky way. A wily child notices small clues and thinks carefully."),
        QAItem(question="What does blink mean?", answer="To blink means to close and open your eyes quickly. A blink can also be a tiny flash of light."),
        QAItem(question="Why is curiosity helpful in a mystery?", answer="Curiosity makes you keep looking and asking questions. That helps you notice clues and solve the mystery."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.clues:
            bits.append(f"clues={e.clues}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("deck", "missing_map", "lantern", "Mira", "girl", "Mom"),
    StoryParams("cove", "singing_key", "spyglass", "Toby", "boy", "Dad"),
    StoryParams("deck", "blink_lantern", "glowstone", "Nia", "girl", "Mom"),
]


def generate(params: StoryParams) -> StorySample:
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
