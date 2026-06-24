#!/usr/bin/env python3
"""
storyworlds/worlds/scatter_injection_rhyme_detective_story.py
=============================================================

A small detective-story world where a careful sleuth follows scattered clues,
spots a sneaky injection of a false hint, and uses rhyme to keep the trail
memorable.

Premise:
- A child detective notices clues scattered around a quiet place.
- Someone has injected one misleading clue into the pattern.
- The detective uses a rhyming clue-chain to sort truth from trickery.

World model:
- Physical meters track clue scatter, mess, and evidence completeness.
- Emotional memes track curiosity, doubt, confidence, and relief.
- State changes drive the prose: discovery, suspicion, testing, and reveal.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool = True
    rhyme_hint: str = ""


@dataclass
class Mystery:
    id: str
    clue: str
    rhyme: str
    scatter: str
    injection: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}"


def add_mem(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def _r_notice_scatter(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    mystery = world.facts["mystery"]
    if detective.meters.get("scatter_seen", 0.0) < THRESHOLD:
        return out
    sig = ("notice_scatter", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"The clues were scattered like crumbs along the floor.")
    return out


def _r_spot_injection(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    mystery = world.facts["mystery"]
    if detective.meters.get("false_note", 0.0) < THRESHOLD:
        return out
    sig = ("spot_injection", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["doubt"] = detective.memes.get("doubt", 0.0) + 1
    out.append("One clue did not fit; it felt like an injection in a neat row of notes.")
    return out


def _r_rhyme_focus(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    if detective.memes.get("doubt", 0.0) < THRESHOLD:
        return out
    sig = ("rhyme_focus",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 1
    out.append("So the detective said a rhyme to keep the truth in line.")
    return out


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    mystery = world.facts["mystery"]
    tool = world.facts["tool"]
    if detective.meters.get("proof", 0.0) < THRESHOLD:
        return out
    sig = ("reveal", mystery.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] = detective.memes.get("relief", 0.0) + 1
    out.append(f"The last clue matched {tool.label}, and the trick was plain at a glance.")
    return out


RULES = [_r_notice_scatter, _r_spot_injection, _r_rhyme_focus, _r_reveal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


SETTING = Setting(place="the library", quiet=True, rhyme_hint="time")
MYSTERIES = {
    "lost_page": Mystery(
        id="lost_page",
        clue="a page",
        rhyme="page / sage",
        scatter="scattered between shelves",
        injection="a false note slipped into the stack",
        reveal="the page had been tucked in a rhyme book",
        tags={"paper", "rhyme"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a key",
        rhyme="key / see",
        scatter="scattered near the reading nook",
        injection="a shiny hint planted beside the lamp",
        reveal="the key was under a rhyming card",
        tags={"metal", "rhyme"},
    ),
    "stolen_stamp": Mystery(
        id="stolen_stamp",
        clue="a stamp",
        rhyme="stamp / lamp",
        scatter="scattered by the desk",
        injection="an ink mark injected into the record",
        reveal="the stamp was hiding in the drawer",
        tags={"ink", "rhyme"},
    ),
}

TOOLS = {
    "notebook": Tool(id="notebook", label="the notebook", phrase="a tidy notebook", helps={"paper", "rhyme"}, covers={"notes"}),
    "magnifier": Tool(id="magnifier", label="the magnifier", phrase="a little magnifier", helps={"metal", "ink"}, covers={"details"}),
    "rhyme_card": Tool(id="rhyme_card", label="the rhyme card", phrase="a bright rhyme card", helps={"rhyme"}, covers={"memory"}),
}


@dataclass
class StoryParams:
    mystery: str
    tool: str
    name: str
    gender: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mia", "Nora", "Zoe", "Lena", "Ivy", "Ava"]
BOY_NAMES = ["Leo", "Finn", "Milo", "Theo", "Ben", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for mid, mystery in MYSTERIES.items():
        for tid, tool in TOOLS.items():
            if mystery.tags & tool.helps:
                combos.append((mid, tid))
    return combos


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} would not really help with {mystery.clue}. "
        f"The detective needs a tool that matches the clue type or the rhyme trail.)"
    )


ASP_RULES = r"""
valid(M, T) :- mystery(M), tool(T), helps(T, K), need(M, K).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("need", mid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for k in sorted(t.helps):
            lines.append(asp.fact("helps", tid, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world with rhyme and a scattered clue trail.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
              if (args.mystery is None or c[0] == args.mystery)
              and (args.tool is None or c[1] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(mystery=mystery_id, tool=tool_id, name=name, gender=gender)


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    detective = world.add(Entity(id="Detective", kind="character", type=params.gender, label=params.name))
    witness = world.add(Entity(id="Witness", kind="character", type="girl", label="the librarian"))
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    world.add(Entity(id="Clue", type="thing", label=mystery.clue, phrase=mystery.clue, owner="Detective"))
    world.add(Entity(id="Tool", type="thing", label=tool.label, phrase=tool.phrase, owner="Detective"))
    world.facts.update(detective=detective, witness=witness, mystery=mystery, tool=tool)
    return world


def tell(world: World) -> None:
    detective = world.facts["detective"]
    mystery = world.facts["mystery"]
    tool = world.facts["tool"]
    witness = world.facts["witness"]

    world.say(f"{detective.label} was a young detective in {world.setting.place}, with a keen eye and a quiet pace.")
    world.say(f"One case was about {mystery.clue}, and the trail was {mystery.scatter}.")
    world.say(f"But one hint had been injected into the row of clues, and it did not belong.")
    detective.meters["scatter_seen"] = 1.0
    detective.meters["false_note"] = 1.0
    world.para()
    world.say(f"{witness.label} said, \"Look sharp, and keep it simple.\"")
    world.say(f"{detective.label} opened {tool.label} and began to sort the notes.")
    propagate(world)
    world.say(f"{detective.label} tried the clue again, then again, and said a little rhyme: \"{mystery.rhyme}.\"")
    detective.meters["proof"] = 1.0
    propagate(world)
    world.para()
    world.say(f"At last, the clue made sense: {mystery.reveal}.")
    world.say(f"The false lead was set aside, and {detective.label} walked home with a clear mind and a steady smile.")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = f["mystery"]
    t = f["tool"]
    d = f["detective"]
    return [
        f'Write a short detective story for a child that includes the words "scatter" and "injection".',
        f"Tell a gentle mystery about {d.label} finding a scattered clue and using {t.label} to spot an injected false lead.",
        f"Write a rhyming detective story where the clue trail is about {m.clue} and the hero keeps the case in line.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    m = f["mystery"]
    t = f["tool"]
    return [
        QAItem(
            question=f"What kind of story is this about {d.label}?",
            answer=f"It is a detective story about {d.label} following a clue trail and solving a mystery.",
        ),
        QAItem(
            question=f"What was scattered in the story?",
            answer=f"The clues were scattered, so {d.label} had to look carefully to find the right one.",
        ),
        QAItem(
            question=f"What did the injected false clue do?",
            answer=f"The injected false clue tried to trick {d.label}, but {t.label} helped sort the truth from the fake hint.",
        ),
        QAItem(
            question=f"How did rhyme help in the case of {m.clue}?",
            answer=f"{d.label} used a rhyme to stay focused, and that made the true clue easier to remember.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and uses them to solve a mystery.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or sounds that end in a similar way, like time and rhyme.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_combos()
        print(f"{len(pairs)} compatible (mystery, tool) combos:\n")
        for m, t in pairs:
            print(f"  {m:14} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("lost_page", "notebook", "Mia", "girl"),
            StoryParams("missing_key", "magnifier", "Leo", "boy"),
            StoryParams("stolen_stamp", "rhyme_card", "Nora", "girl"),
        ]
        samples = [generate(p) for p in curated]
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
