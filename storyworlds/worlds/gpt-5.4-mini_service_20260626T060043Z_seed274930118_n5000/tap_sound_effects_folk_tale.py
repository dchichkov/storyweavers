#!/usr/bin/env python3
"""
storyworlds/worlds/tap_sound_effects_folk_tale.py
==================================================

A small folk-tale storyworld about tapping sounds: one little tap can be a
signal, a greeting, a warning, or a mystery in the lane.

Seed premise:
---
A child hears a tap-tap from the old village gate and goes to find out who is
there. The sound seems spooky at first, but it turns out to be a shy helper
sending a message in rhythm. The child learns to answer with a gentler tap, and
the village ends in warmth instead of fear.

World model:
---
- The tap sound has a strength meter and a meaning meme.
- People and objects can be loud, shy, worried, or relieved.
- A risky tap can startle sleepers or make a keeper worried.
- A softening cloth or a quieter surface can resolve the tension.

This script follows the shared Storyworld contract:
- stdlib-only prose engine
- lazy ASP import through the shared helper
- standalone generate/emit/main interface
- child-facing story plus grounded Q&A
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

TAP_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("sound", "fear", "joy", "worry", "relief", "curiosity", "sleep", "care"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    indoors: bool = False
    echoes: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    resonance: str
    loudness: float
    place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    soften: float
    keep_kind: str
    place: str = ""
    plural: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_kind: str
    elder: str
    surface: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "gate": Place("the old village gate", indoors=False, echoes=True, affords={"tap"}),
    "well": Place("the stone well", indoors=False, echoes=True, affords={"tap"}),
    "porch": Place("the cottage porch", indoors=False, echoes=False, affords={"tap"}),
    "hall": Place("the long hall", indoors=True, echoes=False, affords={"tap"}),
}

SURFACES = {
    "gate": Surface("gate", "gate", "the old gate", "wooden", 1.0, "gate", {"folk", "wood"}),
    "well": Surface("well", "well lid", "the round well lid", "stone", 1.2, "well", {"folk", "stone"}),
    "door": Surface("door", "door", "the cottage door", "wooden", 0.8, "porch", {"folk", "wood"}),
    "table": Surface("table", "table", "the long table", "hollow", 0.6, "hall", {"folk"}),
}

TOOLS = {
    "bare": Tool("bare", "bare hands", "bare hands", soften=0.0, keep_kind="none"),
    "cloth": Tool("cloth", "a folded cloth", "a folded cloth", soften=0.7, keep_kind="soft"),
    "stick": Tool("stick", "a tapping stick", "a tapping stick", soften=0.2, keep_kind="signal"),
    "bell": Tool("bell", "a little bell", "a little bell", soften=0.5, keep_kind="signal"),
}

HEROES = {
    "girl": ["Mira", "Lena", "Anya", "Tessa", "Sera"],
    "boy": ["Pavel", "Jon", "Milo", "Ravi", "Tobin"],
}

ELDERS = ["grandmother", "grandfather", "aunt", "uncle"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    if not world.place.echoes:
        return out
    for hero in world.characters():
        if hero.meters["sound"] < TAP_THRESHOLD:
            continue
        sig = ("echo", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] += 0.2
        out.append("The sound bounced around and came back again.")
    return out


def _r_startle(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("softened", False):
        return out
    for hero in world.characters():
        if hero.meters["sound"] < TAP_THRESHOLD:
            continue
        sig = ("startle", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for ent in world.characters():
            if ent.id != hero.id:
                ent.memes["fear"] += 0.5
        out.append("The tapping sounded sharp enough to make the village hush.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("softened", False):
        return out
    sig = ("relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.characters():
        ent.memes["relief"] += 0.6
        ent.memes["fear"] = 0.0
    out.append("Once the cloth softened the tap, the fear melted away.")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("startle", _r_startle), Rule("relief", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, hero: Entity, surface: Surface, tool: Tool) -> dict:
    sim = world.copy()
    do_tap(sim, hero.id, surface.id, tool.id, narrate=False)
    return {
        "fear": sum(e.memes["fear"] for e in sim.characters()),
        "relief": sum(e.memes["relief"] for e in sim.characters()),
        "softened": sim.facts.get("softened", False),
    }


def do_tap(world: World, hero_id: str, surface_id: str, tool_id: str, narrate: bool = True) -> None:
    hero = world.get(hero_id)
    surface = SURFACES[surface_id]
    tool = TOOLS[tool_id]
    if surface.place != world.place.name.split()[-1] and surface.place not in world.place.name:
        pass
    strength = surface.loudness - tool.soften
    if strength < 0:
        strength = 0.0
    hero.meters["sound"] += strength
    hero.memes["curiosity"] += 0.3
    if tool.keep_kind == "soft":
        world.facts["softened"] = True
    if narrate:
        world.say(f"{hero.id} made a tap-tap on {surface.phrase} with {tool.label}.")
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who listened hard to the village sounds.")


def sound_world(world: World, hero: Entity, surface: Surface) -> None:
    if world.place.echoes:
        world.say(f"At {world.place.name}, every tap could come back like a small reply from the stones.")
    else:
        world.say(f"At {world.place.name}, the air was softer, and even a tap sounded kind.")


def stumble(world: World, elder: Entity, hero: Entity, surface: Surface) -> None:
    elder.memes["worry"] += 0.6
    world.say(
        f"{hero.id} heard a tap-tap-tap from {surface.phrase} and tiptoed closer. "
        f"{elder.id} frowned and said the sound might wake the sleeping ones."
    )


def answer(world: World, hero: Entity, elder: Entity, surface: Surface) -> None:
    hero.memes["joy"] += 0.4
    world.say(
        f"{hero.id} answered with a tiny tap, then another, as if asking a careful question."
    )


def soften_plan(world: World, elder: Entity, hero: Entity, surface: Surface, tool: Tool) -> None:
    world.say(
        f"{elder.id} laid out {tool.phrase} and said, "
        f'"If we must tap, let us tap soft and wise, like rain on new leaves."'
    )
    hero.memes["worry"] += 0.1


def ending(world: World, hero: Entity, elder: Entity, surface: Surface, tool: Tool) -> None:
    world.say(
        f"So {hero.id} tapped again through {tool.phrase}, and the sound turned gentle. "
        f"The old place kept its secret, and the last little tap felt more like a blessing than a knock."
    )


def build_story(world: World, hero: Entity, elder: Entity, surface: Surface, tool: Tool) -> None:
    intro(world, hero)
    world.para()
    sound_world(world, hero, surface)
    stumble(world, elder, hero, surface)
    answer(world, hero, elder, surface)
    world.para()
    soften_plan(world, elder, hero, surface, tool)
    do_tap(world, hero.id, surface.id, tool.id)
    ending(world, hero, elder, surface, tool)
    world.facts.update(hero=hero, elder=elder, surface=surface, tool=tool)


def choose_name(kind: str, rng: random.Random) -> str:
    return rng.choice(HEROES[kind])


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for surf_id, surface in SURFACES.items():
            if surface.place != place_id:
                continue
            for tool_id, tool in TOOLS.items():
                if tool.soften < 0:
                    continue
                combos.append((place_id, surf_id, tool_id))
    return combos


def explain_rejection(place: str, surface: str, tool: str) -> str:
    return "(No story: the chosen tap does not fit this small folk-tale place.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld of taps and careful sound.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--hero")
    ap.add_argument("--elder", choices=ELDERS)
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
              and (args.surface is None or c[1] == args.surface)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid tap story matches those choices.)")
    place, surface, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or choose_name(gender, rng)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, hero=hero, hero_kind=gender, elder=elder, surface=surface, tool=tool)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_kind, traits=["little", "curious", "careful"]))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder, traits=["wise"]))
    surface = SURFACES[params.surface]
    tool = TOOLS[params.tool]
    world.facts["place"] = place
    build_story(world, hero, elder, surface, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short folk tale for a young child about a tap-tap sound that first seems strange and then becomes kind.',
        f'Tell a gentle story where {f["hero"].id} hears a tap on {f["surface"].phrase} at {world.place.name} and learns what it means.',
        'Write a simple story with sound effects like tap-tap-tap, and end with the sound becoming soft and safe.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    surface = f["surface"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who hears the tap at {world.place.name}?",
            answer=f"{hero.id} hears the tap at {world.place.name}, and {elder.id} worries at first.",
        ),
        QAItem(
            question=f"Why did the tap sound scary at first on {surface.label}?",
            answer=f"It sounded sharp on {surface.phrase}, so it felt like it might wake the sleeping ones or make the village uneasy.",
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.id} make the sound gentle?",
            answer=f"They used {tool.phrase} and kept the tapping soft, so the final tap sounded warm instead of startling.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, the tap was still there, but it had become a careful, friendly signal instead of a frightening noise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tap?",
            answer="A tap is a quick little sound made by touching something lightly, often more than once in a row.",
        ),
        QAItem(
            question="Why can tap-tap-tap sound like a message?",
            answer="When taps are made in a pattern, they can work like a tiny code that carries a message from one person to another.",
        ),
        QAItem(
            question="Why do soft sounds matter in a folk tale?",
            answer="Soft sounds can mean kindness, care, and wisdom, especially when a story wants to show a gentle choice.",
        ),
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
elder(E) :- elder_name(E).
place(P) :- place_name(P).
surface(S) :- surface_name(S).
tool(T) :- tool_name(T).

risky(P,S) :- place(P), surface_in(S,P), sharp(S).
soft(T) :- tool(T), softening(T, V), V >= 1.

compatible(P,S,T) :- risky(P,S), soft(T).
valid_story(P,S,T) :- compatible(P,S,T).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place_name", pid))
    for sid, s in SURFACES.items():
        lines.append(asp.fact("surface_name", sid))
        lines.append(asp.fact("surface_in", sid, s.place))
        if s.loudness >= 1.0:
            lines.append(asp.fact("sharp", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_name", tid))
        lines.append(asp.fact("softening", tid, int(t.soften * 10)))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl_simple = {(p, s, t) for (p, s, t) in cl}
    if py == cl_simple:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  only in ASP:", sorted(cl_simple - py))
    print("  only in Python:", sorted(py - cl_simple))
    return 1


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible tap stories:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place_id, surf_id, tool_id in valid_combos():
            params = StoryParams(place=place_id, hero="Mira", hero_kind="girl", elder="grandmother", surface=surf_id, tool=tool_id)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
