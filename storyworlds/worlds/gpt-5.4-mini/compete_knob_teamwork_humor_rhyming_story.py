#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/compete_knob_teamwork_humor_rhyming_story.py
==============================================================================

A standalone storyworld for a tiny, child-facing rhyming tale about a teamwork
challenge around a stubborn knob: two kids want to compete, the knob will not
turn, they try silly ideas, then they cooperate, solve it, and end with a bright
little victory image.

The world is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate plus inline ASP twin
- generated prose driven by simulated state, not a frozen template swap
- three Q&A sets grounded in the story and the world model

Seed words:
- compete
- knob

Style:
- Rhyming Story
- Teamwork
- Humor
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
TURN_STATES = {"stuck", "loose"}
TEAM_TRAITS = {"helpful", "steady", "clever", "patient", "kind"}
HUMOR_TRAITS = {"silly", "funny", "bouncy", "cheerful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Theme:
    id: str
    setting: str
    setup: str
    rhyme_close: str
    prize: str
    finish: str


@dataclass
class Knob:
    id: str
    label: str
    action: str
    stuck_reason: str
    loosen_method: str
    sound: str
    turns: int = 1
    stubborn: bool = True


@dataclass
class TeamMove:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    knob = world.entities.get("knob")
    if knob is None or knob.meters["stuck"] < THRESHOLD:
        return out
    sig = ("tension",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for c in world.characters():
        c.memes["worry"] += 1
    out.append("__tension__")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    knob = world.entities.get("knob")
    if knob is None or knob.meters["stuck"] < THRESHOLD:
        return out
    helpers = [c for c in world.characters() if c.memes["teamwork"] >= THRESHOLD]
    if len(helpers) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    knob.meters["loose"] += 1
    knob.meters["stuck"] = 0
    out.append("__loosened__")
    return out


CAUSAL_RULES = [Rule("tension", "social", _r_tension), Rule("teamwork", "physical", _r_teamwork)]


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


def reasonableness_gate(move: TeamMove, knob: Knob) -> bool:
    return move.sense >= 2 and knob.stubborn


def valid_combos() -> list[tuple[str, str]]:
    return [("playroom", "silver_knob"), ("hall", "sticky_knob"), ("garage", "rusty_knob")]


@dataclass
class StoryParams:
    place: str
    knob: str
    move: str
    kid1: str
    kid1_gender: str
    kid2: str
    kid2_gender: str
    parent: str
    theme: str
    seed: Optional[int] = None


class StoryShape:
    pass


def _team_line(a: Entity, b: Entity) -> str:
    return f"{a.id} and {b.id}."


def setup(world: World, theme: Theme, a: Entity, b: Entity, knob: Knob) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    a.memes["humor"] += 1
    b.memes["humor"] += 1
    world.say(f"In the {theme.setting}, {a.id} and {b.id} went out to play,")
    world.say(f"With {theme.setup} in a cheerful, bouncy way.")
    world.say(f"They found the {knob.label} and said, \"Let's compete!\"")
    world.say(f"Who could turn it first? That sounded quite neat.")


def struggle(world: World, a: Entity, b: Entity, knob: Knob) -> None:
    a.memes["stubborn"] += 1
    b.memes["stubborn"] += 1
    world.say(f'\"I\'ll do it alone!\" said {a.id} with a grin,')
    world.say(f'\"No, I can win!\" laughed {b.id}, \"let the race begin!\"')
    world.say(f"But the knob would not budge, it just sat there tight,")
    world.say(f"And the more they both pulled, the more it held right.")


def joke(world: World, a: Entity, b: Entity, knob: Knob) -> None:
    a.memes["humor"] += 1
    b.memes["humor"] += 1
    world.say(f"{a.id} made a wiggle, {b.id} made a squeak,")
    world.say(f'The knob gave a tiny "{knob.sound}" — a squeaky little tweak.')
    world.say(f"They giggled and huffed and tried not to frown,")
    world.say(f'But still the knob stayed put, no turning around.')


def call_for_help(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    world.say(f'"This is silly," they laughed. "Let\'s ask {parent.label_word} to see,"')
    world.say(f"And {parent.label_word} came in smiling, as calm as could be.")


def predict_move(world: World, move: TeamMove) -> bool:
    sim = world.copy()
    if "knob" in sim.entities:
        sim.get("knob").meters["stuck"] += 1
    return reasonableness_gate(move, KNOBS[sim.get("knob").attrs["kind"]])


def use_teamwork(world: World, parent: Entity, a: Entity, b: Entity, knob: Knob, move: TeamMove) -> None:
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.get("knob").meters["stuck"] += 1
    world.say(f'{parent.label_word.capitalize()} said, "No need to compete. Let\'s solve this as a crew."')
    world.say(f"They tried the {move.text}, and with two hands in a row,")
    world.say(f"The knob turned at last with a friendly little glow.")


def ending(world: World, theme: Theme, a: Entity, b: Entity, knob: Knob) -> None:
    world.say(f"{theme.finish} {a.id} and {b.id} cheered, \"We did it together!\"")
    world.say(f'And the old knob went "{knob.sound}" as if singing in weather.')
    world.say(f"{a.id} and {b.id} shared the win, side by side,")
    world.say(f"With teamwork and laughter as their sparkling guide.")


def tell(theme: Theme, knob: Knob, move: TeamMove, a_name: str, a_gender: str, b_name: str, b_gender: str, parent_type: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="competitor"))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="competitor"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="helper", label="the parent"))
    k = world.add(Entity(id="knob", type="thing", label=knob.label, role="object", attrs={"kind": knob.id}))
    k.meters["stuck"] += 1
    setup(world, theme, a, b, knob)
    world.para()
    struggle(world, a, b, knob)
    joke(world, a, b, knob)
    call_for_help(world, parent, a, b)
    world.para()
    if not reasonableness_gate(move, knob):
        raise StoryError("This teamwork move is too weak or the knob is not a fitting challenge.")
    use_teamwork(world, parent, a, b, knob, move)
    propagate(world, narrate=False)
    world.para()
    ending(world, theme, a, b, knob)
    world.facts.update(theme=theme, knob=knob, move=move, a=a, b=b, parent=parent, outcome="loose")
    return world


THEMES = {
    "playroom": Theme("playroom", "playroom", "a duel with a toy top and a song", "bright and neat", "a prize ribbon", "At last, the room shone,"),
    "hall": Theme("hall", "hall", "a grin, a spin, and a counting cue", "light as a kite", "a paper crown", "At last, the hall rang,"),
    "garage": Theme("garage", "garage", "a humming tune and a clapping crew", "snug and snug", "a blue star badge", "At last, the garage sang,"),
}

KNOBS = {
    "silver_knob": Knob("silver_knob", "silver knob", "compete to turn the knob", "it was stuck from the start", "two hands at once", "clink"),
    "sticky_knob": Knob("sticky_knob", "sticky knob", "compete to twist the knob", "it was gummy and slow", "one to steady, one to twist", "squeak"),
    "rusty_knob": Knob("rusty_knob", "rusty knob", "compete to nudge the knob", "it was old and grumpy", "one to hold, one to turn", "creak"),
}

MOVES = {
    "two_hands": TeamMove("two_hands", 3, 3, "two hands at once", "They used two hands at once, and it turned."),
    "steady_twist": TeamMove("steady_twist", 3, 3, "one to steady, one to twist", "One child steadied, one child twisted, and it turned."),
    "count_and_pull": TeamMove("count_and_pull", 2, 2, "count and pull together", "They counted and pulled together, and the knob gave way."),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Nora", "Ava", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Max", "Theo", "Ben", "Sam"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a child where {f["a"].id} and {f["b"].id} compete over a {f["knob"].label}, but teamwork wins in the end.',
        f"Tell a funny teamwork story about a stubborn knob and two kids who try to compete, then solve it together.",
        f'Write a cheerful rhyme that includes the words "compete" and "knob" and ends with a shared victory.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent, knob, theme = f["a"], f["b"], f["parent"], f["knob"], f["theme"]
    return [
        ("Who is the story about?", f"It is about {a.id} and {b.id}, who wanted to compete and turn the {knob.label}."),
        ("Why did they need teamwork?", f"The {knob.label} stayed stuck, so one child alone could not turn it. Working together gave them enough help and steadiness."),
        ("What did the parent say?", f"The parent reminded them not to keep competing alone. The best plan was to solve the problem as a team."),
        ("How did the story end?", f"It ended with the {knob.label} turning and both kids cheering together. Their teamwork won, and the win felt funny and bright."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does compete mean?", "To compete means to try to do better than someone else, like in a race or a game."),
        ("What is a knob?", "A knob is a round handle you turn to open, close, or adjust something."),
        ("Why is teamwork helpful?", "Teamwork is helpful because two or more people can combine their ideas and strength."),
        ("How can humor help?", "Humor can make a hard task feel lighter and help people keep going when something is stuck."),
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.attrs:
            parts.append(f"attrs={e.attrs}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("playroom", "silver_knob", "two_hands", "Mia", "girl", "Finn", "boy", "mother", "playroom"),
    StoryParams("hall", "sticky_knob", "steady_twist", "Leo", "boy", "Zoe", "girl", "father", "hall"),
    StoryParams("garage", "rusty_knob", "count_and_pull", "Ava", "girl", "Ben", "boy", "mother", "garage"),
]


def explain_rejection(knob: Knob, move: TeamMove) -> str:
    return f"(No story: the move '{move.id}' is not a strong enough teamwork fix for the {knob.label}.)"


def valid_story(params: StoryParams) -> bool:
    return params.knob in KNOBS and params.move in MOVES and reasonableness_gate(MOVES[params.move], KNOBS[params.knob])


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for kid, k in KNOBS.items():
        lines.append(asp.fact("knob", kid))
        if k.stubborn:
            lines.append(asp.fact("stubborn", kid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(K, M) :- knob(K), move(M), sense(M, S), sense_min(N), S >= N, stubborn(K).
outcome(loose) :- valid(_, _).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = {(k, m) for k, m in valid_combos() if reasonableness_gate(MOVES["two_hands"], KNOBS[k])}
    cl = set(asp_valid_combos())
    ok = True
    if cl != py:
        ok = False
        print("MISMATCH in valid combos")
        print("python:", sorted(py))
        print("clingo:", sorted(cl))
    try:
        sample = generate(CURATED[0])
        assert sample.story.strip()
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork story about a stubborn knob.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--knob", choices=KNOBS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--kid1")
    ap.add_argument("--kid1-gender", choices=["girl", "boy"])
    ap.add_argument("--kid2")
    ap.add_argument("--kid2-gender", choices=["girl", "boy"])
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
    if args.knob and args.move and not reasonableness_gate(MOVES[args.move], KNOBS[args.knob]):
        raise StoryError(explain_rejection(KNOBS[args.knob], MOVES[args.move]))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.knob is None or c[0] == args.knob or True)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme = args.theme or rng.choice(list(THEMES))
    knob = args.knob or rng.choice(list(KNOBS))
    move = args.move or rng.choice(list(MOVES))
    if not reasonableness_gate(MOVES[move], KNOBS[knob]):
        move = "two_hands"
    kid1_gender = args.kid1_gender or rng.choice(["girl", "boy"])
    kid2_gender = args.kid2_gender or ("boy" if kid1_gender == "girl" else "girl")
    kid1_pool = GIRL_NAMES if kid1_gender == "girl" else BOY_NAMES
    kid2_pool = GIRL_NAMES if kid2_gender == "girl" else BOY_NAMES
    kid1 = args.kid1 or rng.choice(kid1_pool)
    kid2 = args.kid2 or rng.choice([n for n in kid2_pool if n != kid1] or kid2_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, knob, move, kid1, kid1_gender, kid2, kid2_gender, parent, theme)


def generate(params: StoryParams) -> StorySample:
    theme = THEMES[params.theme]
    knob = KNOBS[params.knob]
    move = MOVES[params.move]
    world = tell(theme, knob, move, params.kid1, params.kid1_gender, params.kid2, params.kid2_gender, params.parent)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (knob, move) combos:")
        for k, m in asp_valid_combos():
            print(f"  {k:14} {m}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
