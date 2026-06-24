#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/stable_tuvwxy_sound_effects_superhero_story.py
=================================================================================================

A standalone story world for a small superhero-style domain with sound effects.

Seed tale imagined from the prompt:
A young superhero hears a trouble at the stable, races in with a helper gadget
called tuvwxy, and saves the day with a noisy, cheerful rescue.

The simulation models a tiny causal chain:
- a noisy danger starts at a place
- the hero feels urgency and the protected prize becomes at risk
- a specific tool can neutralize the danger
- the ending proves the prize stayed safe and the place returned to stable calm

The prose stays state-driven rather than swapping nouns in a template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

STABLE_SOUND = "stable"
TUWVXY_SOUND = "tuvwxy"


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": {"f": "she", "m": "he", "n": "it"},
            "object": {"f": "her", "m": "him", "n": "it"},
            "possessive": {"f": "her", "m": "his", "n": "its"},
        }
        g = "n"
        if self.type in {"girl", "woman", "mother"}:
            g = "f"
        elif self.type in {"boy", "man", "father"}:
            g = "m"
        return mapping[case][g]


@dataclass
class Place:
    id: str
    label: str
    stable: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    label: str
    sound: str
    mess: str
    risk: str
    zone: str


@dataclass
class Tool:
    id: str
    label: str
    sound: str
    counters: set[str]
    prep: str
    finish: str


@dataclass
class StoryParams:
    place: str
    danger: str
    prize: str
    tool: str
    name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


PLACES = {
    "stable": Place(id="stable", label="the stable", stable=True, affords={"rattle", "wind"}),
    "city": Place(id="city", label="the city street", stable=False, affords={"rattle"}),
    "harbor": Place(id="harbor", label="the harbor dock", stable=False, affords={"wind", "rattle"}),
}

DANGERS = {
    "rattle": Danger(id="rattle", label="a wobbling gate", sound="CLANG", mess="scare", risk="spook", zone="door"),
    "wind": Danger(id="wind", label="a blasting gust", sound="WHOOSH", mess="blow", risk="scatter", zone="roof"),
}

TOOLS = {
    "tuwvxy": Tool(
        id="tuvwx y".replace(" ", ""),
        label="the tuvwxy clamp",
        sound="KLINK",
        counters={"rattle", "wind"},
        prep="snap the tuvwxy clamp shut",
        finish="the tuvwxy clamp held fast",
    ),
    "rope": Tool(
        id="rope",
        label="a bright rescue rope",
        sound="TWANG",
        counters={"rattle"},
        prep="loop the rescue rope around the gate",
        finish="the rescue rope held the gate steady",
    ),
}

PRIZES = {
    "pony": {"label": "the little pony", "region": "stall", "weight": "small", "type": "pony"},
    "kitten": {"label": "the kitten", "region": "crate", "weight": "tiny", "type": "kitten"},
}

NAMES = ["Nova", "Milo", "Zuri", "Finn", "Ada", "Iris"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "friend", "coach"]
TRAITS = ["brave", "quick", "kind", "steady"]


def reasonableness_gate(place: Place, danger: Danger, prize_id: str, tool: Tool) -> bool:
    return danger.id in place.affords and danger.id in tool.counters and place.stable


def select_valid_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    combos = []
    for pid, place in PLACES.items():
        for did, danger in DANGERS.items():
            for pr in PRIZES:
                for tid, tool in TOOLS.items():
                    if reasonableness_gate(place, danger, pr, tool):
                        combos.append((pid, did, pr, tid))
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.danger:
        combos = [c for c in combos if c[1] == args.danger]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if args.tool:
        combos = [c for c in combos if c[3] == args.tool]
    if not combos:
        raise StoryError("No valid superhero story matches those choices.")
    return rng.choice(sorted(combos))


def predict_rescue(world: World, danger: Danger, prize: Entity, tool: Tool) -> bool:
    return danger.id in tool.counters and world.place.stable and prize.memes.get("risk", 0) < 2


def resolve_action(world: World, hero: Entity, helper: Entity, danger: Danger, prize: Entity, tool: Tool) -> bool:
    if danger.id in world.fired:
        return False
    world.fired.add(danger.id)
    world.say(f"{danger.sound}! {danger.label} shook the air.")
    hero.memes["alarm"] = hero.memes.get("alarm", 0) + 1
    prize.memes["risk"] = prize.memes.get("risk", 0) + 1
    if predict_rescue(world, danger, prize, tool):
        world.say(f"{hero.pronoun().capitalize()} raced in and said, \"{tool.sound}!\"")
        world.say(f"{helper.label.capitalize()} nodded as {hero.id} used {tool.prep}.")
        hero.memes["courage"] = hero.memes.get("courage", 0) + 1
        prize.memes["safe"] = 1
        world.say(f"{tool.finish}, and the danger stopped at once.")
        return True
    world.say(f"{hero.id} tried to help, but the danger stayed wild.")
    return False


ASP_RULES = r"""
danger_at_risk(D,P) :- danger(D), prize(P), affects(D,P).
good_fix(T,D) :- tool(T), danger(D), counters(T,D).
valid_story(Place,D,P,T) :- place(Place), stable(Place), afford(Place,D), good_fix(T,D), prize(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.stable:
            lines.append(asp.fact("stable", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("afford", pid, a))
    for did, d in DANGERS.items():
        lines.append(asp.fact("danger", did))
        lines.append(asp.fact("affects", did, "prize"))
        lines.append(asp.fact("sound_of", did, d.sound))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.counters):
            lines.append(asp.fact("counters", tid, c))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show valid_story/4.")
    model = asp.one_model(prog)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for pid, place in PLACES.items():
        for did, danger in DANGERS.items():
            for pr in PRIZES:
                for tid, tool in TOOLS.items():
                    if reasonableness_gate(place, danger, pr, tool):
                        py_set.add((pid, did, pr, tid))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH:")
    print(" only asp:", sorted(asp_set - py_set))
    print(" only py:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    place, danger, prize, tool = select_valid_combo(rng, args)
    name = args.name or rng.choice(NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, danger=danger, prize=prize, tool=tool, name=name, hero_type=hero_type, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    danger = DANGERS[params.danger]
    tool = TOOLS[params.tool]
    prize_cfg = PRIZES[params.prize]
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label="the helper"))
    prize = world.add(Entity(id="prize", kind="thing", type=prize_cfg["type"], label=prize_cfg["label"], phrase=prize_cfg["label"], owner=hero.id))
    hero.memes["courage"] = 0
    prize.memes["safe"] = 0

    world.say(f"At {place.label}, {STABLE_SOUND} and bright, {hero.id} watched over {prize.label}.")
    world.say(f"Then {danger.sound}! {danger.label} made the whole place tremble.")
    world.para()
    world.say(f"{hero.id} felt the alarm in {hero.pronoun('possessive')} chest and zoomed forward.")
    world.say(f"{helper.label.capitalize()} pointed at {tool.label}. \"{tool.sound}!\" they cried.")
    resolved = resolve_action(world, hero, helper, danger, prize, tool)
    world.para()
    if resolved:
        world.say(f"In the end, {prize.label} stayed safe, and the {STABLE_SOUND} place grew calm again.")
        world.say(f"{hero.id} smiled, listening to the soft {tool.sound.lower()} of the last lock.")
    else:
        world.say(f"The danger faded only after a long, careful wait, and {prize.label} needed extra help.")
    world.facts = {
        "hero": hero,
        "helper": helper,
        "prize": prize,
        "danger": danger,
        "tool": tool,
        "place": place,
        "resolved": resolved,
    }
    prompts = [
        f"Write a superhero story for little kids set at {place.label} with the sound effects {danger.sound} and {tool.sound}.",
        f"Tell a brave rescue tale that includes {STABLE_SOUND} and {TUWVXY_SOUND} and ends with a safe prize.",
    ]
    story_qa = [
        QAItem(question=f"What happened when {danger.label} showed up at {place.label}?", answer=f"It made a loud {danger.sound} sound, and {hero.id} rushed to help."),
        QAItem(question=f"How did {hero.id} solve the problem?", answer=f"{hero.id} used {tool.label} with {helper.label} so the danger stopped."),
        QAItem(question=f"What changed at the end of the story?", answer=f"{prize.label} stayed safe and {place.label} became calm again."),
    ]
    world_qa = [
        QAItem(question="What does stable mean?", answer="Stable can mean steady and not wobbly."),
        QAItem(question="Why do heroes use tools?", answer="Heroes use tools so they can fix problems safely and help other people."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("Prompts:")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\nStory QA:")
        for q in sample.story_qa:
            print(f"Q: {q.question}\nA: {q.answer}")
        print("\nWorld QA:")
        for q in sample.world_qa:
            print(f"Q: {q.question}\nA: {q.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        atoms = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(atoms)} compatible stories")
        for atom in atoms:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(place="stable", danger="rattle", prize="pony", tool="tuwvxy", name="Nova", hero_type="girl", helper_type="mother"),
            StoryParams(place="stable", danger="wind", prize="kitten", tool="tuwvxy", name="Milo", hero_type="boy", helper_type="father"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
