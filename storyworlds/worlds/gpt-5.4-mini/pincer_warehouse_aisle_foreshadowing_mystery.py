#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pincer_warehouse_aisle_foreshadowing_mystery.py
================================================================================

A standalone storyworld for a small warehouse-aisle mystery with foreshadowing.

Premise:
- A child hears a strange scrape in a warehouse aisle.
- They notice small clues that hint at a hidden problem.
- A calm worker follows those clues, finds a stuck pincer tool, and solves the mystery.
- The ending shows the aisle safe and the clue re-read in a new light.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib-only script
- shared result containers imported eagerly
- lazy ASP import inside helper functions only
- StoryParams, parser, resolver, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python and ASP reasonableness gate plus parity check
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
SENSE_MIN = 2


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
class Setting:
    id: str
    place: str
    mood: str
    places: list[str] = field(default_factory=list)


@dataclass
class MysteryObject:
    id: str
    label: str
    phrase: str
    hint: str
    hidden: bool = False
    broken: bool = False
    causes_noise: bool = False
    metal: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    foreshadows: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_scare(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["uneasy"] < THRESHOLD:
            continue
        sig = ("scare", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["alert"] += 1
        out.append("__scare__")
    return out


CAUSAL_RULES = [Rule("scare", "social", _r_scare)]


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


def reasonableness_ok(params: "StoryParams") -> bool:
    return params.pincer.kind == "tool" and params.aisle.kind == "aisle" and params.response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PINCERS:
            for aid in AISLES:
                if pincer_at_risk(PINCERS[pid], AISLES[aid]):
                    combos.append((sid, pid, aid))
    return combos


def pincer_at_risk(pincer: MysteryObject, aisle: MysteryObject) -> bool:
    return pincer.hidden and aisle.hidden


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_solved(response: Response, pincer: MysteryObject, delay: int) -> bool:
    return response.power >= (1 + delay) and pincer.hidden


def predict(world: World, pincer_id: str) -> dict:
    sim = world.copy()
    _hide_pincer(sim, sim.get(pincer_id), narrate=False)
    return {"uneasy": sim.get("child").meters["uneasy"], "noise": sim.facts.get("noise", 0)}


def _hide_pincer(world: World, target_ent: Entity, narrate: bool = True) -> None:
    target_ent.meters["stuck"] += 1
    target_ent.meters["hidden"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, worker: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} walked with {worker.label_word} into "
        f"{setting.place}. The aisle seemed ordinary at first, with tall shelves, "
        f"cardboard boxes, and one narrow path between them."
    )
    world.say(
        f"{child.id} noticed how {setting.mood} it looked and kept glancing at the "
        f"same shelf, as if the shelves were hiding a secret."
    )


def foreshadow(world: World, child: Entity, clue: Clue) -> None:
    child.meters["uneasy"] += 1
    world.say(
        f"Then {child.id} spotted {clue.text}. It felt like a clue, small but not "
        f"forgotten."
    )
    world.say(
        f"{clue.foreshadows}. {child.id} remembered the shape of it and looked "
        f"back at the aisle."
    )


def investigate(world: World, child: Entity, worker: Entity, pincer: MysteryObject) -> None:
    child.memes["attention"] += 1
    world.say(
        f"{child.id} whispered that something had scraped behind the boxes. "
        f"{worker.label_word.capitalize()} listened instead of laughing."
    )
    world.say(
        f'The sound came from {pincer.phrase}, tucked deep in the shelf where no one '
        f'could see it.'
    )


def warn(world: World, worker: Entity, child: Entity, pincer: MysteryObject) -> None:
    pred = predict(world, "pincer")
    world.facts["predicted_uneasy"] = pred["uneasy"]
    world.say(
        f'"Do you hear that?" {worker.id} said softly. "A metal tool can snag and '
        f'keep making trouble."'
    )
    world.say(
        f"{child.id} nodded. The clue made sense now: the tiny scrape had been a "
        f"hint that {pincer.label} was stuck."
    )


def solve(world: World, worker: Entity, pincer: MysteryObject, response: Response) -> None:
    pincer.hidden = False
    pincer.broken = False
    world.say(
        f"{worker.label_word.capitalize()} came closer, took a careful look, and "
        f"{response.text}."
    )
    world.say(
        f"The {pincer.label} slid free at last. The shelf went still, and the odd "
        f"little scrape was gone."
    )


def ending(world: World, child: Entity, worker: Entity, pincer: MysteryObject, clue: Clue) -> None:
    child.memes["relief"] += 1
    worker.memes["relief"] += 1
    world.say(
        f"{child.id} smiled at the aisle that had seemed so strange before. "
        f"Now the clue looked different: it had been a warning all along."
    )
    world.say(
        f"With the pincer found and the path clear, {child.id} and {worker.id} "
        f"walked on past the shelves, and the warehouse aisle felt safe again."
    )


def tell(setting: Setting, pincer_cfg: MysteryObject, clue: Clue, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         worker_name: str = "Mr. Vale", worker_gender: str = "man",
         delay: int = 0) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    worker = world.add(Entity(id=worker_name, kind="character", type=worker_gender, role="worker", label="the worker"))
    pincer = world.add(Entity(id="pincer", type="tool", label=pincer_cfg.label, attrs={"kind": "pincer"}))
    pincer.meters["stuck"] = 0
    pincer.meters["hidden"] = 1
    child.meters["uneasy"] = 0
    world.facts["noise"] = 1 + delay

    setup(world, child, worker, setting)
    world.para()
    foreshadow(world, child, clue)
    investigate(world, child, worker, pincer_cfg)
    warn(world, worker, child, pincer_cfg)
    world.para()
    solve(world, worker, pincer_cfg, response)
    ending(world, child, worker, pincer_cfg, clue)

    world.facts.update(
        child=child, worker=worker, pincer=pincer_cfg, clue=clue, response=response,
        setting=setting, delay=delay, outcome="solved", solved=True,
    )
    return world


SETTINGS = {
    "warehouse": Setting("warehouse", "a warehouse aisle", "dim and echoing", ["aisle"]),
    "stockroom": Setting("stockroom", "a back stockroom aisle", "quiet and crowded", ["aisle"]),
}

AISLES = {
    "warehouse": MysteryObject("warehouse", "warehouse aisle", "the warehouse aisle", "the aisle hidden between tall shelves", hidden=True, tags={"warehouse", "aisle"}),
    "stockroom": MysteryObject("stockroom", "stockroom aisle", "the stockroom aisle", "the aisle beside stacked cartons", hidden=True, tags={"stockroom", "aisle"}),
}

PINCERS = {
    "pincer": MysteryObject("pincer", "pincer tool", "the pincer tool", "a small metal pincer caught on a crate strap", hidden=True, causes_noise=True, metal=True, tags={"pincer", "metal"}),
}

CLUES = {
    "scrape": Clue("scrape", "a tiny scrape mark on the floor", "It made the child think something metal had been dragged there.", {"scrape", "foreshadow"}),
    "glint": Clue("glint", "a faint silver glint under a box", "It hinted that a tool was tucked out of sight.", {"glint", "foreshadow"}),
}

RESPONSES = {
    "careful": Response("careful", 3, 3, "pulled the strap loose and lifted the tool without a sudden yank", "tried to tug at it too fast and only made the scraping worse", "pulled the strap loose and lifted the tool without a sudden yank", {"careful", "tool"}),
    "steady": Response("steady", 2, 2, "used both hands and eased the pincer free one slow inch at a time", "tried to hurry and the pincer stayed wedged in place", "used both hands and eased the pincer free one slow inch at a time", {"steady", "tool"}),
}

TRAITS = ["curious", "careful", "quiet", "patient"]
CHILD_NAMES = ["Mia", "Leo", "Nora", "Theo", "Zoe", "Finn"]
WORKER_NAMES = ["Mr. Vale", "Ms. Reed", "Mr. Kline", "Ms. Park"]


@dataclass
class StoryParams:
    setting: str
    aisle: str
    pincer: str
    clue: str
    response: str
    child_name: str
    child_gender: str
    worker_name: str
    worker_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly mystery story set in {f["setting"].place} that includes the word "pincer" and a small foreshadowing clue.',
        f"Tell a warehouse-aisle mystery where {f['child'].id} notices a hint, follows it, and finds a pincer tool that needs help.",
        f"Write a short story with foreshadowing, a quiet discovery, and a safe ending in a warehouse aisle.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, worker, pincer, clue = f["child"], f["worker"], f["pincer"], f["clue"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {worker.label_word}, who are moving through a warehouse aisle and looking closely at a small mystery."),
        ("What clue foreshadowed the problem?",
         f"{clue.text}. It foreshadowed the problem by hinting that something metal was hidden nearby before anyone saw the pincer tool."),
        ("What was making the strange sound?",
         f"It was {pincer.label}. The sound came from the tool being stuck where it did not belong."),
        ("How did the story end?",
         f"It ended safely. {worker.label_word.capitalize()} freed the pincer, the aisle went quiet, and {child.id} understood the clue had been warning them all along."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a warehouse aisle?",
         "A warehouse aisle is a narrow path between tall shelves or stacks of boxes. People use it to walk, carry things, and find stored items."),
        ("What is a pincer?",
         "A pincer is a tool or part with two gripping sides that can hold, pinch, or pull something. It is usually a metal tool, not a toy."),
        ("What is foreshadowing?",
         "Foreshadowing is when a story gives a small clue that hints at something important that will happen later. It helps the reader notice the mystery before the answer arrives."),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("warehouse", "warehouse", "pincer", "scrape", "careful", "Mia", "girl", "Mr. Vale", "man", "curious", 0),
    StoryParams("stockroom", "stockroom", "pincer", "glint", "steady", "Leo", "boy", "Ms. Reed", "woman", "patient", 1),
]


def explain_rejection() -> str:
    return "(No story: this mystery needs a hidden pincer and a place where the clue can foreshadow a real find.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in AISLES:
        lines.append(asp.fact("aisle", aid))
        lines.append(asp.fact("hidden", aid))
    for pid in PINCERS:
        lines.append(asp.fact("pincer", pid))
        lines.append(asp.fact("hidden", pid))
        lines.append(asp.fact("metal", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_valid(S, A, P) :- setting(S), aisle(A), pincer(P), hidden(A), hidden(P), metal(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/3."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x[0] for x in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    rc = 0
    c_set, p_set = set(asp_valid_combos()), set(valid_combos())
    if c_set != p_set:
        rc = 1
        print("MISMATCH in valid_combos()")
    else:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    if set(asp_sensible()) != {r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN}:
        rc = 1
        print("MISMATCH in sensible responses")
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small warehouse-aisle mystery with foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--aisle", choices=AISLES)
    ap.add_argument("--pincer", choices=PINCERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--worker-name")
    ap.add_argument("--worker-gender", choices=["woman", "man"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("Response is too implausible for this mystery.")
    setting = args.setting or rng.choice(list(SETTINGS))
    aisle = args.aisle or rng.choice(list(AISLES))
    pincer = args.pincer or "pincer"
    clue = args.clue or rng.choice(list(CLUES))
    response = args.response or rng.choice([r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN])
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    worker_gender = args.worker_gender or rng.choice(["woman", "man"])
    worker_name = args.worker_name or rng.choice(WORKER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(setting, aisle, pincer, clue, response, child_name, child_gender, worker_name, worker_gender, trait, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        PINCERS[params.pincer],
        CLUES[params.clue],
        RESPONSES[params.response],
        params.child_name,
        params.child_gender,
        params.worker_name,
        params.worker_gender,
        params.delay,
    )
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
        print(asp_program("#show reasonably_valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for item in combos:
            print(" ", item)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: pincer mystery in the {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
