#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/scald_nil_rhyme_mystery_to_solve_adventure.py
==================================================================================================

A small adventure storyworld about a rhyme trail, a mystery to solve, and a
careful crossing near hot steam. The seed words are woven into the domain:
"scald" is the danger, and "nil" is the empty answer state the hero begins with
before the clues are found.

The world supports a child-facing story where an explorer follows a rhyme,
solves a mystery, and learns that rushing through steam can scald skin.
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    hot: bool = False


@dataclass
class Mystery:
    id: str
    clue: str
    answer: str
    danger: str
    route: list[str]
    keyword: str = "rhyme"
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    protects: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.path: list[str] = []
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.path = list(self.path)
        return clone


def _r_scald(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.kind != "character":
            continue
        if actor.meters.get("steam", 0.0) < THRESHOLD:
            continue
        sig = ("scald", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = actor.memes.get("fear", 0.0) + 1
        actor.meters["hurt"] = actor.meters.get("hurt", 0.0) + 1
        out.append(f"{actor.pronoun().capitalize()} felt a hot sting from the steam.")
    return out


def _r_nil_to_clue(world: World) -> list[str]:
    out: list[str] = []
    hero = world.facts.get("hero")
    mystery = world.facts.get("mystery")
    if not hero or not mystery:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if world.facts.get("clue_found"):
        return out
    sig = ("clue", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["clue_found"] = True
    hero.meters["clue"] = hero.meters.get("clue", 0.0) + 1
    out.append(f"{hero.id} found the first clue, and the old nil feeling was gone.")
    return out


CAUSAL_RULES = [
    _r_scald,
    _r_nil_to_clue,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_scald(world: World, hero: Entity, mystery: Mystery) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["steam"] = 1.0
    propagate(sim, narrate=False)
    return sim.get(hero.id).meters.get("hurt", 0.0) >= THRESHOLD


def select_tool(mystery: Mystery) -> Optional[Tool]:
    for tool in TOOLS:
        if mystery.answer in tool.helps and "steam" in tool.protects:
            return tool
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} explorer who loved maps, rhymes, and bold walks."
    )


def set_out(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"One morning, {hero.id} followed a rhyme trail toward {world.setting.place} to solve a mystery."
    )
    world.say(
        f"The trail began with the word {mystery.keyword}, and the last answer was still nil."
    )


def warn(world: World, hero: Entity, mystery: Mystery) -> None:
    if predict_scald(world, hero, mystery):
        world.facts["warned"] = True
        world.say(
            f'"Careful," {hero.pronoun("possessive")} guide said. '
            f'"The steam there can scald your hands."'
        )


def cross(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.meters["steam"] = hero.meters.get("steam", 0.0) + 1
    propagate(world, narrate=True)


def search(world: World, hero: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} did not rush. {hero.pronoun().capitalize()} looked for each rhyme-mark in order."
    )
    for step in mystery.route:
        world.path.append(step)
        world.say(f"At {step}, {hero.id} found a clue that pointed onward.")
    propagate(world, narrate=True)


def solve(world: World, hero: Entity, mystery: Mystery) -> None:
    tool = select_tool(mystery)
    if tool is None:
        raise StoryError("No reasonable tool fits this mystery and its steam hazard.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"With {tool.label}, {hero.id} could {tool.prep} and keep going safely."
    )
    world.say(
        f"At the end, the answer was no longer nil: the missing thing was {mystery.answer}."
    )
    world.say(
        f"{hero.id} smiled because the rhyme made sense at last, and the hot steam never got a chance to scald {hero.pronoun('object')}."
    )
    world.say(f"They {tool.tail}, and the mystery was solved.")
    world.facts["tool"] = tool
    world.facts["solved"] = True


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type="adult"))
    world.facts.update(hero=hero, guide=guide, mystery=mystery)

    introduce(world, hero)
    world.para()
    set_out(world, hero, mystery)
    warn(world, hero, mystery)
    world.para()
    search(world, hero, mystery)
    cross(world, hero, mystery)
    world.para()
    solve(world, hero, mystery)
    return world


SETTINGS = {
    "hot_springs": Setting(place="the hot springs", hot=True),
    "stone_bridge": Setting(place="the stone bridge", hot=False),
    "quiet_cave": Setting(place="the quiet cave", hot=False),
}

MYSTERIES = {
    "lost_rhyme": Mystery(
        id="lost_rhyme",
        clue="a line of chalk words on warm stone",
        answer="a tiny silver bell",
        danger="steam",
        route=["the first arch", "the mossy ledge", "the warm pool"],
        tags={"rhyme", "mystery", "adventure", "steam"},
    ),
    "missing_key": Mystery(
        id="missing_key",
        clue="a tune scratched into a map edge",
        answer="a brass key",
        danger="steam",
        route=["the echo hall", "the lantern nook", "the spring step"],
        tags={"rhyme", "mystery", "adventure", "steam"},
    ),
}

TOOLS = [
    Tool(
        id="cloth_wrap",
        label="a cloth wrap",
        helps={"a tiny silver bell"},
        protects={"steam"},
        prep="cross the hot path with the cloth wrap over your hands",
        tail="went home with the bell jingling softly",
    ),
    Tool(
        id="long_tongs",
        label="long tongs",
        helps={"a brass key"},
        protects={"steam"},
        prep="pick up the clue from far away",
        tail="carried the key back without touching the hot stone",
    ),
]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Mira", "Lina", "Tess", "Nora", "Ivy"]
BOY_NAMES = ["Arlo", "Finn", "Theo", "Ezra", "Owen"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_id in SETTINGS:
        for m_id in MYSTERIES:
            if select_tool(MYSTERIES[m_id]) is not None:
                combos.append((s_id, m_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write an adventure story for a small child about {hero.id} following a rhyme to solve a mystery.',
        f"Tell a story where {hero.id} travels to {world.setting.place} and avoids a scalding mistake while solving {mystery.id}.",
        f'Write a short, child-friendly adventure that begins with nil, adds a rhyme, and ends with a solved mystery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to solve the mystery by following the rhyme trail.",
        ),
        QAItem(
            question="What was the answer at the start of the story?",
            answer="At the start, the answer was nil, which means there was nothing found yet.",
        ),
        QAItem(
            question=f"What danger did the guide warn about near {world.setting.place}?",
            answer=f"The guide warned that the steam could scald hands on the hot path.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} solve the mystery safely?",
            answer=f"{tool.label} helped {hero.id} solve it without touching the hot stone.",
        ),
        QAItem(
            question=f"What was the missing thing in the end?",
            answer=f"The missing thing was {mystery.answer}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does scald mean?",
            answer="Scald means to burn or hurt skin with something very hot, like steam or boiling water.",
        ),
        QAItem(
            question="What does nil mean?",
            answer="Nil means nothing or zero; it is the empty amount.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like hill and bill.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not known yet and needs clues to solve.",
        ),
        QAItem(
            question="What is an adventure?",
            answer="An adventure is an exciting trip or challenge where someone explores and faces problems.",
        ),
    ]


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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  path: {world.path}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is solvable when it has a tool and the hero follows the route.
solvable(M) :- mystery(M), tool_for(M, T), helps(T, M).

% A route is dangerous when steam is present and the story warns about scalding.
dangerous(M) :- mystery(M), hazard(M, steam).

% A story is valid only if the mystery is solvable and the scald risk exists.
valid_story(S, M) :- setting(S), mystery(M), solvable(M), dangerous(M).

% A valid combo matches a setting and mystery in the generated world.
valid(S, M) :- valid_story(S, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("hazard", mid, "steam"))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
        for p in sorted(tool.protects):
            lines.append(asp.fact("protects", tool.id, p))
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
    ap = argparse.ArgumentParser(
        description="Adventure storyworld: rhyme, mystery, and the scalding hot path."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in combos:
            raise StoryError("No valid combination matches the given options.")
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
    ]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, mystery=mystery, hero_name=name, hero_type=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.hero_name, params.hero_type)
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


CURATED = [
    StoryParams(setting="hot_springs", mystery="lost_rhyme", hero_name="Mira", hero_type="girl"),
    StoryParams(setting="stone_bridge", mystery="missing_key", hero_name="Arlo", hero_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} valid setting/mystery combos:\n")
        for s, m in triples:
            print(f"  {s:12} {m}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
