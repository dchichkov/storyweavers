#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/giant_wacko_mystery_to_solve_sound_effects.py
==============================================================================

A tiny space-adventure storyworld about a giant, wacko mystery that can only be
solved by listening carefully to sound effects.

Seed idea:
- Space adventure tone
- Words: giant, wacko
- Features: Mystery to Solve, Sound Effects

Premise:
A small crew explores a drifting space station. A giant, wacko clank keeps
echoing through the halls. The mystery is not a monster fight; it is a puzzle of
where the sound comes from, what it means, and how to fix the noisy thing before
it scares the station animals and hides the way home.

The world model tracks:
- typed entities with physical meters and emotional memes
- sound sources, rooms, clues, and tools
- a forward-chained causal story engine
- a simple reasonableness gate
- a Python/ASP twin for parity checks
- three QA sets generated from world state

This script is standalone stdlib Python.
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
CLUE_THRESHOLD = 1.0
NOISE_THRESHOLD = 1.0


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "engineer"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    echo: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    source_label: str
    effect: str
    danger: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
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


def _r_noise_spreads(world: World) -> list[str]:
    out: list[str] = []
    mystery = world.facts["mystery"]
    for ent in world.entities.values():
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.id == mystery.source_label:
            ent.memes["panic"] += 1
        out.append("__noise__")
    return out


def _r_clue_emerges(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["found"] < CLUE_THRESHOLD:
        return out
    sig = ("clue", "found")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crew").memes["hope"] += 1
    out.append("A useful clue turned up.")
    return out


def _r_solution(world: World) -> list[str]:
    out: list[str] = []
    if world.get("tool").meters["used"] < THRESHOLD:
        return out
    sig = ("solve", "mystery")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("station").meters["quiet"] += 1
    world.get("mystery").meters["solved"] += 1
    out.append("__solve__")
    return out


CAUSAL_RULES = [
    Rule("noise_spreads", "sound", _r_noise_spreads),
    Rule("clue_emerges", "mystery", _r_clue_emerges),
    Rule("solution", "resolve", _r_solution),
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


def mystery_is_reasonable(mystery: Mystery, tool: Tool) -> bool:
    return bool(mystery.effect and mystery.clue and tool.fix)


def loud_enough(mystery: Mystery) -> bool:
    return "giant" in mystery.effect and "wacko" in mystery.effect


def story_can_solve(mystery: Mystery, tool: Tool) -> bool:
    return mystery_is_reasonable(mystery, tool) and tool.use in {"listen", "scan", "tighten"}


def predict_noise(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("mystery").meters["noise"] += 1
    propagate(sim, narrate=False)
    return {
        "noise": sim.get("station").meters["noise"],
        "solved": sim.get("mystery").meters["solved"] >= THRESHOLD,
    }


def setup(world: World, crew: Entity, place: Place, mystery: Mystery) -> None:
    crew.memes["curiosity"] += 1
    world.say(
        f"On a drifting space station, {crew.id} floated through {place.label}. "
        f"{place.echo}"
    )
    world.say(
        f"Then came a giant, wacko sound -- {mystery.effect} -- booming down the hall."
    )


def search(world: World, crew: Entity, mystery: Mystery) -> None:
    crew.memes["curiosity"] += 1
    crew.meters["searching"] += 1
    world.say(
        f"{crew.id} held still and listened. The crew heard {mystery.effect}, "
        f"then a softer {mystery.clue} hiding behind the metal walls."
    )


def warn(world: World, crew: Entity, mystery: Mystery, place: Place) -> None:
    pred = predict_noise(world, mystery)
    world.facts["predicted_noise"] = pred["noise"]
    world.say(
        f'"That sound is getting bigger," said {crew.id}. "If we rush, the giant '
        f'wacko noise could bounce through {place.label} and scare everyone."'
    )


def investigate(world: World, crew: Entity, mystery: Mystery) -> None:
    crew.memes["bravery"] += 1
    mystery_ent = world.get("mystery")
    mystery_ent.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{crew.id} followed the clank, the clunk, and the whirrrr until the trail "
        f"led to the machine room."
    )


def find_clue(world: World, clue: Entity, mystery: Mystery) -> None:
    clue.meters["found"] += 1
    world.get("crew").memes["hope"] += 1
    world.say(
        f"Beside the blinking panel, {clue.label_word} flashed under a loose bolt. "
        f"It pointed straight to {mystery.source_label}."
    )


def use_tool(world: World, tool: Entity, mystery: Mystery) -> None:
    tool.meters["used"] += 1
    world.get("crew").memes["relief"] += 1
    world.say(
        f"{tool.label_word.capitalize()} time. {world.get('crew').id} used the {tool.label} "
        f"to {tool.attrs['action']} the panel."
    )


def solve(world: World, mystery: Mystery, place: Place) -> None:
    mystery.meters["solved"] += 1
    world.get("station").meters["quiet"] += 1
    world.say(
        f"The giant, wacko clatter stopped at last. The mystery was only a loose "
        f"panel in {place.label}, and the whole station grew calm again."
    )
    world.say(
        "The crew smiled at the quiet hum, like the stars themselves had breathed out."
    )


def finish(world: World, crew: Entity) -> None:
    crew.memes["pride"] += 1
    world.say(
        f"{crew.id} drifted home with a grin. They had solved the mystery by "
        f"listening closely, and the station sounded safe again."
    )


def tell(place: Place, mystery: Mystery, tool_cfg: Tool,
         crew_name: str = "Mina", crew_type: str = "girl",
         helper_name: str = "Orin", helper_type: str = "boy") -> World:
    world = World()
    crew = world.add(Entity(id=crew_name, kind="character", type=crew_type, role="crew"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    station = world.add(Entity(id="station", type="station", label="the station"))
    clue = world.add(Entity(id="clue", type="thing", label="the clue"))
    tool = world.add(Entity(id="tool", type="thing", label=tool_cfg.label, attrs={"action": tool_cfg.fix}))
    mystery_ent = world.add(Entity(id="mystery", type="mystery", label=mystery.label, attrs={"source": mystery.source_label}))

    world.facts["place"] = place
    world.facts["mystery"] = mystery
    world.facts["tool_cfg"] = tool_cfg
    world.facts["crew"] = crew
    world.facts["helper"] = helper
    world.facts["station"] = station
    world.facts["clue"] = clue
    world.facts["tool"] = tool

    setup(world, crew, place, mystery)
    world.para()
    search(world, crew, mystery)
    warn(world, crew, mystery, place)
    investigate(world, crew, mystery)
    find_clue(world, clue, mystery)
    world.para()
    use_tool(world, tool, mystery)
    solve(world, mystery_ent, place)
    finish(world, crew)
    world.facts["solved"] = mystery_ent.meters["solved"] >= THRESHOLD
    return world


PLACES = {
    "airlock": Place("airlock", "the airlock", "It went clank, clank, clank by the seals."),
    "hall": Place("hall", "the long hall", "It echoed like a giant spoon in a giant cup."),
    "engine_room": Place("engine_room", "the engine room", "It hummed and rattled with a wacko little beat."),
}

MYSTERIES = {
    "panel_clank": Mystery(
        "panel_clank",
        "a giant, wacko clank",
        "the loose panel",
        "clank-clank-CLONK",
        "a tiny piece could fall loose",
        "a bent sticker shaped like a star",
        tags={"giant", "wacko", "mystery", "sound_effects"},
    ),
    "pipe_whirr": Mystery(
        "pipe_whirr",
        "a giant, wacko whirr",
        "the pipe",
        "whirrrrr-THUMP",
        "steam could puff into the room",
        "a sticker on the valve",
        tags={"giant", "wacko", "mystery", "sound_effects"},
    ),
    "bell_bong": Mystery(
        "bell_bong",
        "a giant, wacko bong",
        "the old bell",
        "BONG... bong... BONG",
        "the bell might ring too loudly",
        "a ribbon tied to the rope",
        tags={"giant", "wacko", "mystery", "sound_effects"},
    ),
}

TOOLS = {
    "listen": Tool("listen", "listening scanner", "listen", "tighten", tags={"sound", "mystery"}),
    "scan": Tool("scan", "sonar wand", "scan", "trace", tags={"sound", "mystery"}),
    "tighten": Tool("tighten", "repair wrench", "tighten", "tighten", tags={"mystery", "repair"}),
}

GIRL_NAMES = ["Mina", "Luna", "Nia", "Tia", "Zara", "Aya"]
BOY_NAMES = ["Orin", "Pax", "Ravi", "Eli", "Nico", "Jett"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    crew_name: str
    crew_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for m in MYSTERIES:
            for t in TOOLS:
                if story_can_solve(MYSTERIES[m], TOOLS[t]):
                    combos.append((p, m, t))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, tool = rng.choice(sorted(combos))
    crew_type = rng.choice(["girl", "boy"])
    helper_type = "boy" if crew_type == "girl" else "girl"
    crew_name = args.name or rng.choice(GIRL_NAMES if crew_type == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(BOY_NAMES if helper_type == "boy" else GIRL_NAMES)
    return StoryParams(place, mystery, tool, crew_name, crew_type, helper_name, helper_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a space-adventure story for a 3-to-5-year-old about a giant, wacko mystery in {f["place"].label}.',
        f"Tell a story where {f['crew'].id} solves a strange sound by following clues and listening for sound effects.",
        f'Write a gentle mystery story that includes the words "giant" and "wacko" and ends with the station sounding calm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = f["mystery"]
    crew = f["crew"]
    place = f["place"]
    tool_cfg = f["tool_cfg"]
    return [
        QAItem(
            question="What was the mystery?",
            answer=f"It was {mystery.label}, a giant, wacko sound coming from {mystery.source_label}. The sound turned out to be a clue, not a monster."
        ),
        QAItem(
            question="How did the crew solve it?",
            answer=f"{crew.id} listened carefully, found the clue, and used the {tool_cfg.label} to fix the problem. That stopped the noise and made the station quiet again."
        ),
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened in {place.label} on a drifting space station. The echoes there made the sound seem bigger and stranger."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an echo?", "An echo is a sound that bounces off walls and comes back to your ears."),
        QAItem("Why do space stations make mystery sounds?", "Machines and metal walls can make clanks, hums, and whirs that echo through the halls."),
        QAItem("What should you do when you hear a strange sound?", "Stop, listen, and look for a safe clue instead of rushing in."),
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
    out.append("== (3) World knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("airlock", "panel_clank", "listen", "Mina", "girl", "Orin", "boy"),
    StoryParams("hall", "pipe_whirr", "scan", "Orin", "boy", "Luna", "girl"),
    StoryParams("engine_room", "bell_bong", "tighten", "Nia", "girl", "Pax", "boy"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, mm in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("effect", m, mm.effect))
        lines.append(asp.fact("source", m, mm.source_label))
    for t, tt in TOOLS.items():
        lines.append(asp.fact("tool", t))
        lines.append(asp.fact("use", t, tt.use))
        lines.append(asp.fact("fix", t, tt.fix))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, M, T) :- place(P), mystery(M), tool(T), use(T, U), U = listen.
valid(P, M, T) :- place(P), mystery(M), tool(T), use(T, U), U = scan.
valid(P, M, T) :- place(P), mystery(M), tool(T), use(T, U), U = tighten.
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
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, tool=None, name=None, helper=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], TOOLS[params.tool],
                 params.crew_name, params.crew_type, params.helper_name, params.helper_type)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
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
