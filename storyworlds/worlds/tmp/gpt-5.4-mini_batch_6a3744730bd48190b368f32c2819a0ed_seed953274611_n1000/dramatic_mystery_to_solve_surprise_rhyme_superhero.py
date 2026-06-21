#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dramatic_mystery_to_solve_surprise_rhyme_superhero.py
======================================================================================

A tiny superhero storyworld about a child hero, a mystery to solve, a surprise clue,
and a rhyme that unlocks the answer.

The world is intentionally small and state-driven:
- a hero and sidekick search a room for a missing item,
- clues accumulate as physical meters and emotional memes,
- a surprise event changes the search,
- a rhyme clue reveals the hiding place,
- the ending proves what changed by showing the found item and the hero's mood.

This file follows the shared storyworld contract:
- stdlib-only script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
        return self.label or self.type


@dataclass
class Mystery:
    id: str
    label: str
    missing_phrase: str
    hiding_places: list[str]
    rhyme_clue: str
    surprise: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sidekick:
    id: str
    type: str
    label: str
    helps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trap:
    id: str
    label: str
    risk: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["panic"] >= THRESHOLD:
            sig = ("alarm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.get("hero").memes["focus"] += 1
            out.append("__alarm__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.entities["clue"].meters["hint"] >= THRESHOLD:
        sig = ("clue", "heard")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["hope"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [
    Rule("alarm", "social", _r_alarm),
    Rule("clue", "social", _r_clue),
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


def _mystery_at_risk(mystery: Mystery) -> bool:
    return bool(mystery.hiding_places)


def choose_hiding_place(mystery: Mystery, surprise: bool) -> str:
    if surprise:
        return mystery.hiding_places[0]
    return mystery.hiding_places[-1]


def solve_success(mystery: Mystery, chosen: str, rhyme_known: bool) -> bool:
    return rhyme_known and chosen in mystery.hiding_places


def predict_solution(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("clue").meters["hint"] += 1
    propagate(sim, narrate=False)
    chosen = choose_hiding_place(mystery, surprise=False)
    return {"solvable": solve_success(mystery, chosen, rhyme_known=True), "panic": sim.get("trap").meters["panic"]}


def start(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.memes["mood"] += 1
    sidekick.memes["mood"] += 1
    world.say(
        f"It was a dramatic night in Hero City. {hero.id} wore {hero.pronoun('possessive')} bright cape, "
        f"and {sidekick.id} stood ready beside {hero.pronoun('object')}."
    )
    world.say(
        f"Then the mystery began: {mystery.missing_phrase} was missing from the table, and nobody knew where it went."
    )


def search(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} searched under the sofa, behind the lamp, and around the window. "
        f"{hero.pronoun().capitalize()} wanted to solve the mystery before bedtime."
    )


def surprise_turn(world: World, sidekick: Entity, trap: Entity, mystery: Mystery) -> None:
    trap.meters["panic"] += 1
    sidekick.memes["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Suddenly, {sidekick.id} gasped. A surprise fluttered from the curtain: "
        f"a paper bat pin with {mystery.surprise} tucked underneath it."
    )
    world.say(
        f"The little surprise was not the answer, but it pointed the hero toward a safer, stranger place to look."
    )


def rhyme_hint(world: World, clue: Entity, mystery: Mystery) -> None:
    clue.meters["hint"] += 1
    propagate(world, narrate=False)
    world.say(
        f"On the card under the bat pin, {clue.label_word} read a rhyme: "
        f'"High and neat, beneath the seat; look where shoes do not meet."'
    )
    world.say(
        f"{mystery.rhyme_clue} was the last piece of the puzzle. The rhyme sounded playful, but it was really a map."
    )


def reveal(world: World, hero: Entity, mystery: Mystery, chosen: str) -> None:
    hero.memes["joy"] += 2
    hero.memes["relief"] += 1
    world.get("clue").meters["found"] += 1
    world.say(
        f"{hero.id} followed the rhyme to {chosen} and found {mystery.missing_phrase} there, safe and sound."
    )
    world.say(
        f"{hero.id} lifted it high like a trophy, and the room felt less mysterious at once."
    )


def ending(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} smiled a big superhero smile. {sidekick.id} grinned back, proud that the surprise and the rhyme had solved the case."
    )
    world.say(
        f"By the end, the missing thing was back where it belonged, and the city felt calm again."
    )


@dataclass
class StoryParams:
    mystery: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    clue_name: str
    trap_name: str
    seed: Optional[int] = None


MYSTERIES = {
    "badge": Mystery(
        id="badge",
        label="badge",
        missing_phrase="the captain's shiny badge",
        hiding_places=["bookshelf", "toy chest", "windowsill"],
        rhyme_clue="The clue led upward, then back to the place for resting feet.",
        surprise="a tiny ribbon",
        tags={"mystery", "badge", "rhyme", "surprise"},
    ),
    "ring": Mystery(
        id="ring",
        label="ring",
        missing_phrase="the mayor's silver ring",
        hiding_places=["pillow", "drawer", "basket"],
        rhyme_clue="The clue whispered about soft things and quiet corners.",
        surprise="a glitter sticker",
        tags={"mystery", "ring", "rhyme", "surprise"},
    ),
    "key": Mystery(
        id="key",
        label="key",
        missing_phrase="the museum key",
        hiding_places=["plant pot", "backpack", "bench"],
        rhyme_clue="The clue hinted at leaves, pockets, and a place just outside the door.",
        surprise="a folded note",
        tags={"mystery", "key", "rhyme", "surprise"},
    ),
}

SIDEKICKS = {
    "buddy": Sidekick(id="buddy", type="boy", label="sidekick", helps="kept watch"),
    "spark": Sidekick(id="spark", type="girl", label="sidekick", helps="noticed clues"),
}

TRAPS = {
    "flutter": Trap(id="flutter", label="fluttering trap", risk="startle"),
    "shiver": Trap(id="shiver", label="shivery trap", risk="worry"),
}

HERO_NAMES = ["Nova", "Milo", "Rae", "Jules", "Piper", "Theo", "Kai", "Mina"]
SIDE_NAMES = ["Finn", "Lena", "Bea", "Ollie", "Zara", "Maya", "Noel", "Ari"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for mid in MYSTERIES:
        for sid in SIDEKICKS:
            for tid in TRAPS:
                combos.append((mid, sid, tid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero mystery with a surprise and a rhyme.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--trap", choices=TRAPS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name")
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--clue-name", default="clue")
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
              and (args.sidekick is None or c[1] == args.sidekick)
              and (args.trap is None or c[2] == args.trap)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    sidekick = args.sidekick or rng.choice(sorted(SIDEKICKS))
    trap = args.trap or rng.choice(sorted(TRAPS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick_name or rng.choice(SIDE_NAMES)
    return StoryParams(
        mystery=mystery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        clue_name=args.clue_name,
        trap_name=trap,
    )


def tell(params: StoryParams) -> World:
    mystery = MYSTERIES[params.mystery]
    world = World()
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"))
    side = world.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_gender, role="sidekick"))
    clue = world.add(Entity(id=params.clue_name, kind="thing", type="note", label="clue"))
    trap = world.add(Entity(id=params.trap_name, kind="thing", type="trap", label=TRAPS[params.trap_name].label))

    start(world, hero, side, mystery)
    world.para()
    search(world, hero, mystery)
    surprise_turn(world, side, trap, mystery)
    world.para()
    rhyme_hint(world, clue, mystery)
    chosen = choose_hiding_place(mystery, surprise=True)
    reveal(world, hero, mystery, chosen)
    ending(world, hero, side, mystery)

    world.facts.update(
        mystery=mystery,
        hero=hero,
        sidekick=side,
        clue=clue,
        trap=trap,
        chosen=chosen,
        solved=True,
    )
    return world


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    side: Entity = f["sidekick"]
    chosen = f["chosen"]
    return [
        ("What was the mystery?", f"It was a search for {mystery.missing_phrase}. The missing thing had to be found before the night got later."),
        (f"How did {hero.id} solve it?", f"{hero.id} followed the rhyme clue and looked in {chosen}. That worked because the rhyme pointed to the hiding place."),
        ("What was the surprise?", f"The surprise was {mystery.surprise}. It was unexpected, and it helped lead the search in a new direction."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    return [
        QAItem(question=f"What does a rhyme do in a mystery?", answer="A rhyme can help people remember clues. In a story, it can point the hero toward the right place to look."),
        QAItem(question=f"Why can surprises matter in stories?", answer="A surprise can change what the characters do next. It makes the search feel dramatic and keeps the mystery exciting."),
        QAItem(question=f"What is a superhero story?", answer="A superhero story is about someone brave who helps others and solves problems. The hero uses courage, quick thinking, and heart."),
        QAItem(question=f"Why is {m.label} a mystery?", answer=f"It becomes a mystery when {m.missing_phrase} is gone and nobody knows where it is. Then the characters need clues to solve the puzzle."),
    ]


def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    hero: Entity = world.facts["hero"]
    side: Entity = world.facts["sidekick"]
    return [
        f"Write a dramatic superhero story for a child where {hero.id} and {side.id} solve a mystery with a surprise clue and a rhyme.",
        f"Tell a superhero story that includes the word 'dramatic' and ends with {m.missing_phrase} being found.",
        f"Write a mystery-solving story where a surprise leads to a rhyme that helps the hero find the missing item.",
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


ASP_RULES = r"""
mystery(M) :- mystery_id(M).
solvable(M) :- mystery(M).
surprise(S) :- surprise_id(S).
rhyme(R) :- rhyme_id(R).
valid(M,S,T) :- mystery(M), sidekick(S), trap(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_id", mid))
    for sid in SIDEKICKS:
        lines.append(asp.fact("sidekick", sid))
    for tid in TRAPS:
        lines.append(asp.fact("trap", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in ASP gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke test generate() succeeded.")
    except Exception as exc:  # pragma: no cover - defensive
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.trap_name not in TRAPS:
        raise StoryError("Unknown trap.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
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
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(mystery="badge", hero_name="Nova", hero_gender="girl", sidekick_name="Finn", sidekick_gender="boy", clue_name="clue", trap_name="flutter"),
            StoryParams(mystery="ring", hero_name="Milo", hero_gender="boy", sidekick_name="Lena", sidekick_gender="girl", clue_name="note", trap_name="shiver"),
            StoryParams(mystery="key", hero_name="Rae", hero_gender="girl", sidekick_name="Ari", sidekick_gender="boy", clue_name="card", trap_name="flutter"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
