#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/plumber_commentary_mystery_to_solve_rhyme_adventure.py
===============================================================================================================================

A small Adventure-style storyworld about a plumber solving a household mystery
with a child narrator adding commentary in rhymes.

Premise:
- A leaky sound or blocked drain appears in an adventurous setting.
- The hero plumber follows clues, tests parts, and finds the hidden cause.
- Another character adds commentary in short rhymes, keeping the tone playful.
- The story resolves with a fixed pipe, a revealed culprit, and a clean ending.

This file is self-contained and uses only the stdlib plus the shared Storyweavers
result containers. ASP support is inline and imported lazily.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

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
    setting: str
    clue: str
    affordance: str
    leak_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    symptom: str
    hidden_cause: str
    culprit_kind: str
    fix: str
    rhyme_seed: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    action: str
    helps: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def rhyme_line(seed: str) -> str:
    return {
        "drip": "A drip in the pipe made a tip-top trite,",
        "clank": "A clank in the wall felt wrong, not right,",
        "gurgle": "A gurgle below made the lantern sway,",
        "tick": "A tick in the tap meant trouble was near,",
    }.get(seed, "A small clue sparkled in the damp, dark light,")


def maybe_rhyme(commentator: Entity, line: str) -> str:
    return f'{commentator.id} said, "{line}"'


def leak_score(world: World) -> float:
    sink = world.get("sink")
    pipe = world.get("pipe")
    return sink.meters.get("wet", 0.0) + pipe.meters.get("leak", 0.0)


def _r_water_spread(world: World) -> list[str]:
    out = []
    if world.get("pipe").meters.get("leak", 0.0) >= THRESHOLD:
        sig = ("spread", "sink")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("sink").meters["wet"] += 1
            world.get("floor").meters["wet"] += 1
            out.append("Water spread from the pipe to the sink and floor.")
    return out


CAUSAL_RULES = [_r_water_spread]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                for b in bits:
                    world.say(b)


def clue_from_place(place: Place) -> str:
    return place.clue


def select_tool(mystery: Mystery) -> Tool:
    return TOOLS[mystery.fix]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if mystery.fix == tid and place.affordance in {"sink", "pipe", "basement", "dock"}:
                    combos.append((pid, mid, tid))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    mystery: str = ""
    tool: str = ""
    hero_name: str = ""
    hero_gender: str = ""
    commentator_name: str = ""
    commentator_gender: str = ""
    seed: Optional[int] = None


PLACES = {
    "harbor_house": Place(
        id="harbor_house",
        label="the harbor house",
        setting="an old house by the docks",
        clue="salt on the floorboards and a wet trail near the sink",
        affordance="sink",
        leak_kind="drip",
        tags={"water", "house", "dock"},
    ),
    "workshop": Place(
        id="workshop",
        label="the tool workshop",
        setting="a bright workshop with a deep basin",
        clue="a muddy ring under the pipe and a puddle by the drain",
        affordance="pipe",
        leak_kind="clank",
        tags={"water", "workshop"},
    ),
    "cellar": Place(
        id="cellar",
        label="the cellar",
        setting="a quiet cellar under the inn",
        clue="echoes, a trickle, and a shiny path to the valve",
        affordance="basement",
        leak_kind="gurgle",
        tags={"water", "basement"},
    ),
}

MYSTERIES = {
    "leaky_pipe": Mystery(
        id="leaky_pipe",
        symptom="a drip behind the wall",
        hidden_cause="a loose pipe joint",
        culprit_kind="pipe",
        fix="wrench",
        rhyme_seed="drip",
        tags={"pipe", "leak"},
    ),
    "stuck_valve": Mystery(
        id="stuck_valve",
        symptom="a stubborn trickle at the valve",
        hidden_cause="a valve that would not turn cleanly",
        culprit_kind="valve",
        fix="oil_can",
        rhyme_seed="clank",
        tags={"valve", "leak"},
    ),
    "blocked_drain": Mystery(
        id="blocked_drain",
        symptom="water that backed up and sighed",
        hidden_cause="a clog of leaves and string",
        culprit_kind="drain",
        fix="snake",
        rhyme_seed="gurgle",
        tags={"drain", "clog"},
    ),
}

TOOLS = {
    "wrench": Tool(id="wrench", label="wrench", action="tighten the joint", helps="tighten", tags={"pipe"}),
    "oil_can": Tool(id="oil_can", label="oil can", action="loosen the valve", helps="oil", tags={"valve"}),
    "snake": Tool(id="snake", label="drain snake", action="pull out the clog", helps="clear", tags={"drain"}),
}

GIRL_NAMES = ["Mina", "Tess", "Nora", "Pia", "Lena", "Ivy"]
BOY_NAMES = ["Arlo", "Finn", "Noah", "Otis", "Leo", "Eli"]
TRAITS = ["curious", "brave", "cheerful", "careful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a child that includes the words "plumber" and "commentary".',
        f"Tell a mystery story where {f['hero'].id} works as a plumber, follows clues in {f['place'].label}, and the commentator speaks in rhymes.",
        f"Write a gentle adventure where a plumber solves {f['mystery'].symptom} by using {f['tool'].label}, with a child adding playful commentary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    commentator: Entity = f["commentator"]  # type: ignore[assignment]
    place: Place = f["place"]  # type: ignore[assignment]
    mystery: Mystery = f["mystery"]  # type: ignore[assignment]
    tool: Tool = f["tool"]  # type: ignore[assignment]
    ending = "fixed" if f["fixed"] else "not fixed"
    return [
        QAItem(
            question=f"Who solved the mystery at {place.label}?",
            answer=f"The plumber, {hero.id}, solved it by following the clues in {place.label}. {hero.pronoun('subject').capitalize()} found the hidden cause and made the leak stop.",
        ),
        QAItem(
            question=f"What did {commentator.id} add to the adventure?",
            answer=f"{commentator.id} added commentary in short rhymes. The rhymes pointed at the clue and kept the mystery playful while {hero.id} worked.",
        ),
        QAItem(
            question=f"What tool helped with {mystery.symptom}?",
            answer=f"The {tool.label} helped {hero.id} {tool.action}. That was the right tool because the hidden cause was {mystery.hidden_cause}.",
        ),
        QAItem(
            question=f"How did the story end in {place.label}?",
            answer=f"It ended with the pipe {ending} and the floor dry again. The mystery was solved, so the adventurous place felt safe and calm at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["tool"].tags) | {"plumber", "commentary"}
    out = []
    if "plumber" in tags:
        out.append(QAItem("What does a plumber do?", "A plumber fixes pipes, sinks, drains, and water problems in homes and other places."))
    if "commentary" in tags:
        out.append(QAItem("What is commentary?", "Commentary is talk that explains what is happening or adds lively remarks to a story or event."))
    if "pipe" in tags:
        out.append(QAItem("What is a pipe?", "A pipe carries water, and if it loosens or breaks, it can start to leak."))
    if "drain" in tags:
        out.append(QAItem("What does a drain do?", "A drain lets water flow away, so sinks and tubs do not fill up."))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(place: Place, mystery: Mystery, tool: Tool, hero_name: str, hero_gender: str, commentator_name: str, commentator_gender: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="plumber", meters={"skill": 1.0}, memes={"curiosity": 1.0}, attrs={"trait": trait}))
    commentator = world.add(Entity(id=commentator_name, kind="character", type=commentator_gender, role="commentator", memes={"mischief": 1.0}))
    sink = world.add(Entity(id="sink", type="fixture", label="the sink", meters={"wet": 0.0}))
    pipe = world.add(Entity(id="pipe", type="pipe", label="the pipe", meters={"leak": 0.0}))
    floor = world.add(Entity(id="floor", type="floor", label="the floor", meters={"wet": 0.0}))

    world.facts.update(hero=hero, commentator=commentator, place=place, mystery=mystery, tool=tool)

    world.say(f"At {place.label}, {hero.id} was a plumber with a knack for adventure.")
    world.say(f"{place.clue.capitalize()}. {commentator.id} offered commentary: \"{rhyme_line(mystery.rhyme_seed)}\"")
    world.para()
    world.say(f"{hero.id} followed the clue to {place.affordance} and listened close.")
    world.say(f"{commentator.id} chirped, \"{rhyme_line(mystery.rhyme_seed)}\"")

    pipe.meters["leak"] += 1.0
    propagate(world)

    world.para()
    world.say(f"{hero.id} found {mystery.hidden_cause} and used the {tool.label} to {tool.action}.")
    pipe.meters["leak"] = 0.0
    sink.meters["wet"] = 0.0
    floor.meters["wet"] = 0.0
    world.say(f"The water stopped, and the mystery was solved.")
    world.say(f"{commentator.id} gave one last bit of commentary: \"No more drip, no more slip!\"")

    world.facts["fixed"] = True
    return world


def explain_rejection() -> str:
    return "(No story: this combination does not make a coherent plumber mystery.)"


def valid_for(place: Place, mystery: Mystery, tool: Tool) -> bool:
    return mystery.fix == tool.id and place.affordance in {"sink", "pipe", "basement"}


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.tool:
        m, t = MYSTERIES[args.mystery], TOOLS[args.tool]
        if not valid_for(PLACES[args.place] if args.place else next(iter(PLACES.values())), m, t):
            raise StoryError(explain_rejection())
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, mystery_id, tool_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    commentator_gender = rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    commentator_name = args.commentator_name or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero_name])
    return StoryParams(
        place=place_id,
        mystery=mystery_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        commentator_name=commentator_name,
        commentator_gender=commentator_gender,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        raise StoryError("Invalid StoryParams.")
    if not valid_for(PLACES[params.place], MYSTERIES[params.mystery], TOOLS[params.tool]):
        raise StoryError(explain_rejection())
    trait = "curious"
    world = tell(PLACES[params.place], MYSTERIES[params.mystery], TOOLS[params.tool], params.hero_name, params.hero_gender, params.commentator_name, params.commentator_gender, trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    ap = argparse.ArgumentParser(description="Adventure plumber mystery with rhyming commentary.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--commentator-name")
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


CURATED = [
    StoryParams(place="harbor_house", mystery="leaky_pipe", tool="wrench", hero_name="Mina", hero_gender="girl", commentator_name="Otis", commentator_gender="boy", seed=1),
    StoryParams(place="workshop", mystery="stuck_valve", tool="oil_can", hero_name="Arlo", hero_gender="boy", commentator_name="Ivy", commentator_gender="girl", seed=2),
    StoryParams(place="cellar", mystery="blocked_drain", tool="snake", hero_name="Nora", hero_gender="girl", commentator_name="Eli", commentator_gender="boy", seed=3),
]


ASP_RULES = r"""
valid(Place, Mystery, Tool) :- place(Place), mystery(Mystery), tool(Tool), fix_of(Mystery, Tool), affordance(Place, Aff).
valid(Place, Mystery, Tool) :- place(Place), mystery(Mystery), tool(Tool), fix_of(Mystery, Tool), place_affords(Place, Aff), needs(Mystery, Aff).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_affords", pid, p.affordance))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("fix_of", mid, m.fix))
        for tag in sorted(m.tags):
            lines.append(asp.fact("needs", mid, tag))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return
    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
