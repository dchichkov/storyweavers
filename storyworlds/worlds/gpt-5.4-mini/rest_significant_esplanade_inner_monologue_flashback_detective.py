#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rest_significant_esplanade_inner_monologue_flashback_detective.py
=================================================================================================

A standalone storyworld for a small detective tale set on an esplanade.

Seeded premise:
- A child detective takes a quiet rest on an esplanade.
- An inner monologue and a flashback help them notice a significant clue.
- The clue explains a small mystery and the child returns the lost thing.

This world keeps the prose concrete and state-driven:
- typed entities with meters and memes
- a forward rule engine
- a reasonableness gate
- an inline ASP twin
- three Q&A sets derived from world state, not by parsing rendered text

Run:
    python storyworlds/worlds/gpt-5.4-mini/rest_significant_esplanade_inner_monologue_flashback_detective.py
    python storyworlds/worlds/gpt-5.4-mini/rest_significant_esplanade_inner_monologue_flashback_detective.py --qa
    python storyworlds/worlds/gpt-5.4-mini/rest_significant_esplanade_inner_monologue_flashback_detective.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: str = ""
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


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


@dataclass
class Place:
    id: str
    label: str
    rest_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    object_name: str
    lost_place: str
    clue_name: str
    clue_place: str
    clue_significant: str
    solved_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    detective_name: str
    detective_gender: str
    companion_name: str
    companion_gender: str
    seed: Optional[int] = None


class DetectiveReasonGate:
    @staticmethod
    def valid_combo(place: Place, mystery: Mystery) -> bool:
        return place.id == "esplanade" and "rest" in place.tags and "significant" in mystery.tags


def _r_notice(world: World) -> list[str]:
    out = []
    if world.get("detective").meters["thinking"] >= THRESHOLD and world.get("clue").meters["noticed"] < THRESHOLD:
        sig = ("notice",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("clue").meters["noticed"] += 1
            out.append("__notice__")
    return out


def _r_solve(world: World) -> list[str]:
    out = []
    if world.get("clue").meters["noticed"] >= THRESHOLD and world.get("lost").meters["found"] < THRESHOLD:
        sig = ("solve",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("lost").meters["found"] += 1
            out.append("__solve__")
    return out


CAUSAL_RULES = [Rule("notice", "mind", _r_notice), Rule("solve", "plot", _r_solve)]


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


def flashback(world: World, detective: Entity, clue: Entity, mystery: Mystery) -> None:
    world.say(
        f"As {detective.pronoun()} sat down to rest on the {world.facts['place'].label}, "
        f"{detective.pronoun('possessive')} mind drifted back to earlier."
    )
    world.say(
        f"Earlier, {detective.id} had seen {mystery.clue_name} near the {mystery.clue_place}, "
        f"and the little detail kept tugging at {detective.pronoun('possessive')} thoughts."
    )
    clue.meters["hint"] += 1


def inner_monologue(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["curiosity"] += 1
    detective.meters["thinking"] += 1
    world.say(
        f'"If I rest for a moment," {detective.pronoun()} thought, '
        f'"maybe the answer will come to me."'
    )
    world.say(
        f'{detective.id} looked over the esplanade and thought about the {mystery.clue_name}. '
        f'It felt significant, like a pebble that might turn into a key.'
    )


def observe_clue(world: World, detective: Entity, clue: Entity, mystery: Mystery) -> None:
    clue.meters["seen"] += 1
    detective.memes["focus"] += 1
    world.say(
        f"Then {detective.id} noticed {mystery.clue_name} again. It matched the mark "
        f"from the flashback, and that made the clue feel significant."
    )


def solve_case(world: World, detective: Entity, companion: Entity, mystery: Mystery) -> None:
    world.say(
        f"{detective.id} followed the clue to {mystery.lost_place} and found {mystery.object_name} there."
    )
    world.say(
        f"{mystery.solved_text} {companion.id} smiled and said the day could finally rest."
    )
    detective.memes["pride"] += 1
    companion.memes["relief"] += 1


def tell(place: Place, mystery: Mystery, detective_name: str, detective_gender: str,
         companion_name: str, companion_gender: str) -> World:
    w = World()
    detective = w.add(Entity(detective_name, "character", detective_gender, role="detective"))
    companion = w.add(Entity(companion_name, "character", companion_gender, role="friend"))
    spot = w.add(Entity("esplanade", "place", label=place.label))
    clue = w.add(Entity("clue", "thing", label=mystery.clue_name))
    lost = w.add(Entity("lost", "thing", label=mystery.object_name))
    w.facts.update(place=place, mystery=mystery, detective=detective, companion=companion, clue=clue, lost=lost)

    detective.meters["rested"] += 1
    companion.memes["patient"] += 1
    w.say(
        f"On a bright esplanade by the water, {detective.id} and {companion.id} slowed down to rest."
    )
    w.say(
        f"The long path was calm, with benches, sea air, and gulls above the rail."
    )
    flashback(w, detective, clue, mystery)
    w.para()
    inner_monologue(w, detective, mystery)
    observe_clue(w, detective, clue, mystery)
    propagate(w)
    w.para()
    if lost.meters["found"] >= THRESHOLD:
        solve_case(w, detective, companion, mystery)
    return w


PLACES = {
    "esplanade": Place("esplanade", "the esplanade", "a place for a quiet rest", {"rest"}),
}

MYSTERIES = {
    "lost_ticket": Mystery(
        "lost_ticket",
        "a museum ticket",
        "the stone bench",
        "a paper ticket with a blue star",
        "the railing by the steps",
        "That was the significant clue: the blue star matched the ticket stub in the detective's pocket.",
        "The detective tucked the ticket away and the esplanade felt peaceful again.",
        {"significant", "clue"},
    ),
    "lost_key": Mystery(
        "lost_key",
        "a little brass key",
        "the cafe door",
        "a brass key with red thread",
        "the flower box",
        "That red thread was significant because it matched the ribbon tied to the missing keyring.",
        "The detective set the key on the counter and the owner thanked them warmly.",
        {"significant", "clue"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ivy", "June", "Maya"]
BOY_NAMES = ["Noel", "Owen", "Eli", "Theo", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES.values():
        for m in MYSTERIES.values():
            if DetectiveReasonGate.valid_combo(p, m):
                combos.append((p.id, m.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world on an esplanade.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
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
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery = rng.choice(combos)
    dg = args.detective_gender or rng.choice(["girl", "boy"])
    cg = args.companion_gender or ("boy" if dg == "girl" else "girl")
    dn = args.detective_name or rng.choice(GIRL_NAMES if dg == "girl" else BOY_NAMES)
    cn = args.companion_name or rng.choice(BOY_NAMES if cg == "boy" else GIRL_NAMES)
    return StoryParams(place, mystery, dn, dg, cn, cg)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a detective story that includes the words "rest", "significant", and "esplanade".',
        f"Tell a child-friendly mystery where {f['detective'].id} takes a rest on an esplanade, remembers a clue in a flashback, and solves a small loss.",
        f"Write a detective story with an inner monologue and a flashback that makes one clue feel significant.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    companion = f["companion"]
    mystery = f["mystery"]
    return [
        QAItem(
            question="Where did the detective rest?",
            answer=f"{detective.id} rested on the esplanade, where the air was calm and the path was wide. That quiet place gave {detective.pronoun('object')} time to think."
        ),
        QAItem(
            question="What made the clue significant?",
            answer=f"The clue was significant because it matched the flashback exactly. That match told {detective.id} where the lost thing had been left."
        ),
        QAItem(
            question="What happened at the end?",
            answer=f"{detective.id} found {mystery.object_name} and brought the case to a gentle close. {companion.id} could rest too, because the small mystery was solved."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is an esplanade?", "An esplanade is a wide open walkway, often near water, where people can stroll and rest."),
        QAItem("What is a flashback in a story?", "A flashback is when the story briefly remembers something from earlier. It helps explain why a clue matters now."),
        QAItem("What is an inner monologue?", "An inner monologue is a character's private thoughts. It lets you hear what the detective is puzzling over."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(P, M) :- place(P), mystery(M), rest_place(P), significant_mystery(M).
noticed :- think, clue_seen.
solved :- noticed.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "rest" in p.tags:
            lines.append(asp.fact("rest_place", pid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        if "significant" in m.tags:
            lines.append(asp.fact("significant_mystery", mid))
    lines.append(asp.fact("think", "t"))
    lines.append(asp.fact("clue_seen", "c"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/2."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python gate differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        MYSTERIES[params.mystery],
        params.detective_name,
        params.detective_gender,
        params.companion_name,
        params.companion_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams("esplanade", "lost_ticket", "Mina", "girl", "Noel", "boy"),
    StoryParams("esplanade", "lost_key", "Eli", "boy", "Ivy", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b}" for a, b in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
