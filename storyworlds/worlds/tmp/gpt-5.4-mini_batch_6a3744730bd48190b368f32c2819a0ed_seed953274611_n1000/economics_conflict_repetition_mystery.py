#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/economics_conflict_repetition_mystery.py
=========================================================================

A small storyworld about a puzzling missing-coin mystery in a child-sized
economics setting.

Premise:
- A child and a helper keep noticing the same strange pattern in a coin jar,
  market stall, or ticket desk.
- The pattern creates a conflict: someone wants to spend or swap something now,
  while someone else wants to wait and solve the mystery first.
- Repetition matters: the same clue appears more than once, making the solution
  possible.
- The ending proves the change in the world state: the missing money is found,
  the trade is made fairly, or the broken counting pattern is fixed.

The prose is child-facing, concrete, and driven by a simulated world model with
physical meters and emotional memes.
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
MOODS = ("curious", "nervous", "proud", "patient", "grumpy")


@dataclass
class StoryParams:
    setting: str
    mystery: str
    repeated_clue: str
    conflict: str
    resolution: str
    child: str
    helper: str
    helper_role: str
    market_item: str
    missing_amount: int = 1
    seed: Optional[int] = None


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
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    clue = world.facts.get("repeated_clue", "")
    if not clue:
        return out
    for ent in world.entities.values():
        if ent.role != "helper":
            continue
        if ent.memes["observation"] < THRESHOLD:
            continue
        sig = ("repeat", clue)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["certainty"] += 1
        out.append(f"{ent.id} noticed the same clue again.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["want_spend"] < THRESHOLD or helper.memes["want_wait"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["annoyed"] += 1
    helper.memes["tension"] += 1
    out.append("__conflict__")
    return out


def _r_resolution(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("solved"):
        sig = ("resolved",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("child").memes["pride"] += 1
        world.get("helper").memes["relief"] += 1
        out.append("__resolved__")
    return out


CAUSAL_RULES = [Rule("repeat", _r_repeat), Rule("conflict", _r_conflict), Rule("resolution", _r_resolution)]


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
    "market": {
        "scene": "the little market lane",
        "place": "market stall",
        "economics": "economics",
        "reason": "the prices on the sign kept changing",
    },
    "bakery": {
        "scene": "the bakery counter",
        "place": "bread shelf",
        "economics": "economics",
        "reason": "the coin tin was lighter than it should have been",
    },
    "ticket_booth": {
        "scene": "the bus stop booth",
        "place": "ticket desk",
        "economics": "economics",
        "reason": "the ticket book had one page torn out",
    },
}

CLUES = {
    "coin_twice": "the same shiny coin with a scratch on it",
    "receipt_twice": "the same tiny receipt folded in half",
    "footprints_twice": "the same muddy shoe print near the box",
}

CONFLICTS = {
    "spend_now": "wanted to buy a sweet bun right away",
    "wait_count": "wanted to count the money again before buying anything",
    "share_price": "wanted to set a fair price for the apples",
}

RESOLUTIONS = {
    "hide_under_table": "found the missing coin under the table leg and counted it twice",
    "misread_sign": "realized the sign was copied twice by mistake, so the price was never wrong",
    "coin_return": "noticed the spare coin stuck to the helper's pocket and returned it to the jar",
}

CHILD_NAMES = ["Mia", "Leo", "Nia", "Tom", "Ava", "Ben"]
HELPERS = [
    ("mother", "mother", "adult helper"),
    ("father", "father", "adult helper"),
    ("shopkeeper", "person", "shopkeeper"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            for r in RESOLUTIONS:
                combos.append((s, c, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Economics mystery storyworld with conflict and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, resolution = rng.choice(sorted(combos))
    child = rng.choice(CHILD_NAMES)
    helper_name, helper_type, helper_role = rng.choice(HELPERS)
    if helper_name == child:
        helper_name = rng.choice([n for n in CHILD_NAMES if n != child])
    conflict = rng.choice(list(CONFLICTS))
    return StoryParams(
        setting=setting,
        mystery=SETTINGS[setting]["economics"],
        repeated_clue=CLUES[clue],
        conflict=CONFLICTS[conflict],
        resolution=RESOLUTIONS[resolution],
        child=child,
        helper=helper_name.title(),
        helper_role=helper_role,
        market_item="apples",
    )


def _do_mystery(world: World, clue: str) -> None:
    world.facts["solved"] = True
    world.get("child").meters["search"] += 1
    world.get("helper").meters["search"] += 1
    world.get("helper").memes["observation"] += 1
    world.get("child").memes["curious"] += 1
    world.say(f"They looked for the clue, and the clue turned up again.")
    propagate(world)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type="child", role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="adult", role="helper"))
    stall = world.add(Entity(id="stall", type="place", label=SETTINGS[params.setting]["place"]))
    jar = world.add(Entity(id="jar", type="thing", label="coin jar"))
    child.memes["want_spend"] = 1
    helper.memes["want_wait"] = 1
    helper.memes["observation"] = 1
    child.memes["curious"] = 1

    world.say(
        f"{child.id} and {helper.id} walked through {SETTINGS[params.setting]['scene']}. "
        f"It was a small {params.mystery} problem, the kind that made people whisper."
    )
    world.say(
        f"At the {stall.label_word}, {helper.id} kept noticing {params.repeated_clue}. "
        f"That was the first clue."
    )
    world.para()
    world.say(
        f"{child.id} heard the story and felt the conflict at once. "
        f"{child.id} {params.conflict}, but {helper.id} said it was better to wait."
    )
    world.say(
        f"Again and again, they saw {params.repeated_clue}. "
        f"The repeated clue made the mystery harder to ignore."
    )
    world.get("child").memes["want_spend"] += 1
    world.get("helper").memes["want_wait"] += 1
    propagate(world, narrate=False)
    world.para()
    _do_mystery(world, params.repeated_clue)
    world.say(
        f"In the end, {params.resolution}. "
        f"That fixed the {params.mystery} question and turned the worry into a fair answer."
    )
    world.say(
        f"{child.id} smiled at the {jar.label_word}, and {helper.id} tucked the clue away "
        f"like a puzzle piece that finally fit."
    )
    world.facts.update(
        child=child, helper=helper, stall=stall, jar=jar, params=params,
        repeated_clue=params.repeated_clue, setting=params.setting,
        resolution=params.resolution, solved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a short mystery story for a child that includes the word "economics" and the same clue repeated more than once.',
        f"Tell a story where {p.child} and a helper keep noticing {p.repeated_clue}, disagree about money, and solve the puzzle at the end.",
        f"Write a child-friendly mystery with conflict and repetition where a small economics problem gets solved fairly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    return [
        QAItem(
            question="What was the story about?",
            answer=f"It was about a small economics mystery in {p.setting}. The repeated clue kept showing up until the answer became clear."
        ),
        QAItem(
            question="Why was there conflict?",
            answer=f"{p.child} wanted to act right away, but the helper wanted to wait and count carefully. That conflict mattered because money had to be handled fairly."
        ),
        QAItem(
            question="How did the repeated clue help?",
            answer=f"{p.repeated_clue} appeared again and again, so everyone could compare it and notice the pattern. That repetition led them to the right answer."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {p.resolution}. The mystery was solved, and the money problem stopped causing trouble."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is economics?",
            answer="Economics is about money, prices, buying, selling, and choosing how to share things fairly."
        ),
        QAItem(
            question="Why do people count money more than once?",
            answer="People count money again to make sure it is correct. Repeating the count helps catch mistakes."
        ),
        QAItem(
            question="What is a fair price?",
            answer="A fair price is a price that feels honest for both the buyer and the seller. It helps people trade without arguing."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} role={e.role} meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,R) :- setting(S), clue(C), resolution(R).
solve :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for r in RESOLUTIONS:
        lines.append(asp.fact("resolution", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, clue=None, resolution=None), random.Random(1)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams(setting="market", mystery="economics", repeated_clue=CLUES["coin_twice"], conflict=CONFLICTS["wait_count"], resolution=RESOLUTIONS["hide_under_table"], child="Mia", helper="Aunt June", helper_role="helper", market_item="apples"),
    StoryParams(setting="bakery", mystery="economics", repeated_clue=CLUES["receipt_twice"], conflict=CONFLICTS["spend_now"], resolution=RESOLUTIONS["coin_return"], child="Leo", helper="Mr. Reed", helper_role="shopkeeper", market_item="bread"),
    StoryParams(setting="ticket_booth", mystery="economics", repeated_clue=CLUES["footprints_twice"], conflict=CONFLICTS["share_price"], resolution=RESOLUTIONS["misread_sign"], child="Ava", helper="Dad", helper_role="adult helper", market_item="tickets"),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.repeated_clue not in CLUES.values() or params.resolution not in RESOLUTIONS.values():
        raise StoryError("(Invalid params for this world.)")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.resolution is None or c[2] == args.resolution)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, resolution = rng.choice(sorted(combos))
    helper_name, helper_type, helper_role = rng.choice(HELPERS)
    child = rng.choice(CHILD_NAMES)
    if helper_name == child:
        helper_name = "Aunt June"
    conflict = rng.choice(list(CONFLICTS))
    return StoryParams(
        setting=setting,
        mystery="economics",
        repeated_clue=CLUES[clue],
        conflict=CONFLICTS[conflict],
        resolution=RESOLUTIONS[resolution],
        child=child,
        helper=helper_name.title(),
        helper_role=helper_role,
        market_item="apples",
    )


def build_args() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
