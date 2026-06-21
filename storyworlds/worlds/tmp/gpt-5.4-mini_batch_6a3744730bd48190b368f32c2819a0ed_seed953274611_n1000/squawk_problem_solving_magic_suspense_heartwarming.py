#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py
====================================================================================

A small standalone storyworld for a heartwarming, suspenseful, problem-solving
magic tale that includes the word "squawk".

Premise
-------
A child hears a mysterious squawk at dusk, discovers a tiny bird in a tricky
spot, and uses careful thinking plus a little magic to help it safely.

World shape
-----------
- Typed entities with physical meters and emotional memes
- A forward-chained causal model
- A reasonableness gate for valid combinations
- A Python ASP twin for parity checks
- Three QA sets grounded in the simulated world state

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4-mini/squawk_problem_solving_magic_suspense_heartwarming.py --verify
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
class Place:
    id: str
    label: str
    dusk: str
    hiding_spot: str
    details: str
    suspense: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Bird:
    id: str
    label: str
    cry: str
    trapped_in: str
    needs: str
    small: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    glow: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    bird: str
    tool: str
    fix: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["trapped"] < THRESHOLD:
            continue
        sig = ("scare", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.entities.values():
            if ch.role in {"hero", "helper"}:
                ch.memes["worry"] += 1
        out.append("__squawk__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["freed"] < THRESHOLD:
            continue
        sig = ("relief", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ch in world.entities.values():
            if ch.role in {"hero", "helper"}:
                ch.memes["relief"] += 1
                ch.memes["love"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("scare", _r_scare), Rule("relief", _r_relief)]


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


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= 2]


def valid_combo(place: Place, bird: Bird, tool: MagicTool, fix: Fix) -> bool:
    return tool.id in place.tags and bird.id in place.tags and fix.power >= 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for pid, p in PLACES.items():
        for bid, b in BIRDS.items():
            for tid, t in TOOLS.items():
                for fid, f in FIXES.items():
                    if valid_combo(p, b, t, f):
                        combos.append((pid, bid, tid, fid))
    return combos


def predict(world: World, bird_id: str, fix_id: str) -> dict:
    sim = world.copy()
    bird = sim.get(bird_id)
    bird.meters["trapped"] += 1
    propagate(sim, narrate=False)
    fix = FIXES[fix_id]
    return {"worry": sim.get("hero").memes["worry"], "ok": fix.power >= 1}


def begin(world: World, hero: Entity, helper: Entity, place: Place, bird: Bird) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"At {place.label} near {place.dusk}, {hero.id} and {helper.id} were walking home "
        f"when a soft {bird.cry} drifted from {place.hiding_spot}."
    )
    world.say(
        f"{place.details} {hero.id} held {helper.pronoun('possessive')} hand and whispered, "
        f'"Did you hear that squawk?"'
    )


def search(world: World, hero: Entity, helper: Entity, place: Place, bird: Bird) -> None:
    hero.memes["suspense"] += 1
    world.say(
        f"They followed the sound slowly. Every step made the leaves rustle, and the little "
        f"voice came again from behind {place.hiding_spot}."
    )
    world.say(
        f"Then they saw {bird.label}, a tiny bird stuck in a prickly tangle, looking scared and tired."
    )


def try_magic(world: World, hero: Entity, tool: MagicTool, bird: Bird) -> None:
    world.say(
        f'{hero.id} lifted {tool.phrase}. It glowed {tool.glow}, and the light shivered like a moonbeam.'
    )
    world.say(
        f'"Please work," {hero.id} breathed, because {tool.helps} could show the safest way in.'
    )


def warn(world: World, helper: Entity, bird: Bird, place: Place) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} peered close and frowned. The vines were sharp, and one wrong tug could hurt {bird.label}."
    )
    world.say(
        f'"Let’s think first," {helper.id} said. "We need a gentle plan."'
    )


def solve(world: World, hero: Entity, helper: Entity, bird: Bird, tool: MagicTool, fix: Fix) -> None:
    world.say(
        f"With the glow to guide them, {hero.id} and {helper.id} used {fix.text.replace('{bird}', bird.label)}."
    )


def free_bird(world: World, bird: Bird, fix: Fix) -> None:
    bird.meters["trapped"] = 0.0
    bird.meters["freed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{fix.qa_text.replace('{bird}', bird.label)} The tangle loosened, and {bird.label} fluttered free."
    )


def reunion(world: World, hero: Entity, helper: Entity, bird: Bird, place: Place) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{bird.label} landed on {helper.id}'s sleeve and gave one last {bird.cry}, this time bright and happy."
    )
    world.say(
        f"{hero.id} smiled so hard it felt like the whole path lit up. They carried the bird to the edge of the garden, "
        f"where it hopped once, looked back, and flew into the dusk."
    )
    world.say(
        "The quiet after that felt warm, like a blanket tucked around everyone’s heart."
    )


def tell(params: StoryParams) -> World:
    world = World()
    place = PLACES[params.place]
    bird = BIRDS[params.bird]
    tool = TOOLS[params.tool]
    fix = FIXES[params.fix]
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    trapped = world.add(Entity(id="bird", type="bird", label=bird.label, role="problem"))
    world.facts["parent"] = parent
    world.facts["place"] = place
    world.facts["bird_cfg"] = bird
    world.facts["tool_cfg"] = tool
    world.facts["fix_cfg"] = fix

    begin(world, hero, helper, place, bird)
    world.para()
    search(world, hero, helper, place, bird)
    warn(world, helper, bird, place)
    try_magic(world, hero, tool, bird)
    trapped.meters["trapped"] += 1
    world.say(
        f"The glow showed a tiny loop of vine wrapped around {bird.label}'s wing. There was a pause, and nobody pulled too hard."
    )
    world.para()
    solve(world, hero, helper, bird, tool, fix)
    free_bird(world, trapped, fix)
    reunion(world, hero, helper, bird, place)
    world.say(
        f"When {parent.label_word if parent.label_word else 'the parent'} arrived, they knelt beside the children and smiled. "
        f'"You both used your heads," they said softly. "That was brave."'
    )
    world.facts.update(
        hero=hero, helper=helper, parent=parent, bird=bird, place=place,
        tool=tool, fix=fix, outcome="rescued", trapped=trapped.meters["trapped"] >= THRESHOLD
    )
    return world


PLACES = {
    "garden": Place(id="garden", label="the garden gate", dusk="the rose-gray evening", hiding_spot="the hedge",
                    details="The lanterns had just started blinking on, and the air smelled like rain.",
                    tags={"garden", "bird", "magic"}),
    "orchard": Place(id="orchard", label="the orchard path", dusk="the blue hour", hiding_spot="the apple tree roots",
                     details="The trees made a soft roof overhead, and the last sunlight looked golden and thin.",
                     tags={"orchard", "bird", "magic"}),
    "courtyard": Place(id="courtyard", label="the courtyard", dusk="the starry dusk", hiding_spot="the fountain fern",
                       details="A little fountain whispered nearby, and the stones held the day’s warm last light.",
                       tags={"courtyard", "bird", "magic"}),
}

BIRDS = {
    "sparrow": Bird(id="sparrow", label="a sparrow", cry="squawk", trapped_in="twigs", needs="gentle hands",
                    tags={"bird"}),
    "bluejay": Bird(id="bluejay", label="a blue jay chick", cry="squawk", trapped_in="vines", needs="careful fingers",
                    tags={"bird"}),
    "wren": Bird(id="wren", label="a wren", cry="squawk", trapped_in="brambles", needs="patient hands",
                 tags={"bird"}),
}

TOOLS = {
    "lantern": MagicTool(id="lantern", label="a tiny moon lantern", phrase="a tiny moon lantern", glow="soft and silver",
                         helps="the lantern could shine into the dark without scaring the bird", tags={"magic"}),
    "ribbon": MagicTool(id="ribbon", label="a charm ribbon", phrase="a charm ribbon", glow="pink and gold",
                        helps="the ribbon could point toward the safest opening", tags={"magic"}),
    "stone": MagicTool(id="stone", label="a glow stone", phrase="a glow stone", glow="warm and gold",
                       helps="the stone could light the tangle so they could untie it gently", tags={"magic"}),
}

FIXES = {
    "unwind": Fix(id="unwind", label="unwind", sense=3, power=2,
                  text="slowly unwound the vine while keeping one hand ready if the bird flinched",
                  fail="tried to pull the vine loose, but the knots stayed tight",
                  qa_text="They slowly unwound the vine while keeping one hand ready if the bird flinched.",
                  tags={"problem_solving"}),
    "cut": Fix(id="cut", label="cut", sense=3, power=2,
               text="used a little pocket scissors to cut only the smallest thorny loops",
               fail="snipped in the wrong place and made the tangle worse",
               qa_text="They used a little pocket scissors to cut only the smallest thorny loops.",
               tags={"problem_solving"}),
    "guide": Fix(id="guide", label="guide", sense=2, power=1,
                 text="held the lantern low and guided the bird toward a clear opening in the hedge",
                 fail="guided the bird the wrong way and it fluttered back into the brambles",
                 qa_text="They held the lantern low and guided the bird toward a clear opening in the hedge.",
                 tags={"problem_solving"}),
}

GIRL_NAMES = ["Lina", "Maya", "Nora", "Ivy", "Rose", "Ada"]
BOY_NAMES = ["Theo", "Finn", "Milo", "Eli", "Sam", "Nico"]
HELPER_NAMES = ["June", "Piper", "Kai", "Owen", "Mina", "Bea"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the word "squawk" and a child solving a small mystery with magic.',
        f"Tell a suspenseful but gentle story where {f['hero'].id} hears a squawk, finds a trapped bird, and uses a magical tool to help.",
        f"Write a short story about problem solving, magic, and a bird in trouble that ends with everyone feeling warm and relieved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, helper, parent = f["hero"], f["helper"], f["parent"]
    place, bird, tool, fix = f["place"], f["bird_cfg"], f["tool_cfg"], f["fix_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {helper.id}, who heard a squawk near {place.label}. {parent.label_word.capitalize()} also appears at the end to smile at what they did."),
        ("What was the problem?",
         f"A tiny bird was trapped in the hedge, and its scared squawk showed that it needed help. The tricky part was that the vines were tight, so the children had to be careful."),
        ("How did they solve it?",
         f"They used {tool.phrase} to see clearly, then {fix.qa_text.lower()}. That careful plan solved the problem without hurting the bird."),
        ("How did the children feel at the end?",
         f"They felt happy and relieved. The bird was safe, so the suspense turned into a warm, proud feeling."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["place"].tags) | set(world.facts["bird_cfg"].tags) | set(world.facts["tool_cfg"].tags) | set(world.facts["fix_cfg"].tags)
    out = []
    if "bird" in tags:
        out.append(("Why do birds make warning sounds?",
                    "Birds can make warning sounds when they are scared, stuck, or trying to tell others to stay away. A sound like squawk can mean a bird needs help."))
    if "magic" in tags:
        out.append(("What can magic do in a story?",
                    "In stories, magic can make a light glow, point the way, or help someone solve a problem in a special way. It is often used to make the moment feel wondrous."))
    if "problem_solving" in tags:
        out.append(("What does problem solving mean?",
                    "Problem solving means thinking carefully about a trouble and choosing a good way to fix it. It often means looking, testing, and being gentle."))
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: that combination does not give the bird, the magic tool, and the careful fix a real problem to solve.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for b in BIRDS:
        lines.append(asp.fact("bird", b))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,B,T,F) :- place(P), bird(B), tool(T), fix(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid-combo logic.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming magic suspense storyworld with squawk.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bird", choices=BIRDS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bird is None or c[1] == args.bird)
              and (args.tool is None or c[2] == args.tool)
              and (args.fix is None or c[3] == args.fix)]
    if not combos:
        raise StoryError(explain_rejection())
    place, bird, tool, fix = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, bird=bird, tool=tool, fix=fix, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.bird not in BIRDS or params.tool not in TOOLS or params.fix not in FIXES:
        raise StoryError("Invalid params.")
    world = tell(params)
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
    StoryParams(place="garden", bird="sparrow", tool="lantern", fix="unwind", hero="Lina", hero_gender="girl", helper="Owen", helper_gender="boy", parent="mother"),
    StoryParams(place="orchard", bird="wren", tool="ribbon", fix="guide", hero="Theo", hero_gender="boy", helper="Bea", helper_gender="girl", parent="father"),
    StoryParams(place="courtyard", bird="bluejay", tool="stone", fix="cut", hero="Maya", hero_gender="girl", helper="Kai", helper_gender="boy", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (place, bird, tool, fix) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
