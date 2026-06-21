#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hash_transcript_vague_teamwork_humor_detective_story.py
======================================================================================

A tiny detective-story world about a clue trail, a messy transcript, and two
helpers who solve a case together with a little humor.

Seed words: hash, transcript, vague
Features: Teamwork, Humor
Style: Detective Story

The domain is intentionally small: a child detective and a partner investigate a
lost-stamp mystery in a library. The case begins with a vague transcript from a
robot recorder, turns when a hash-marked page reveals a hidden pattern, and ends
with the team solving the mystery together.
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
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Device:
    id: str
    label: str
    kind: str
    can_be_vague: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Outcome:
    id: str
    label: str
    humor: int
    teamwork: int
    text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    if world.get("transcript").meters["vague"] < THRESHOLD:
        return out
    if ("confusion", "detective") in world.fired:
        return out
    world.fired.add(("confusion", "detective"))
    for eid in ("detective", "partner"):
        world.get(eid).memes["puzzled"] += 1
    out.append("__confusion__")
    return out


def _r_hash(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hash_page").meters["seen"] < THRESHOLD:
        return out
    if ("hash", "clue") in world.fired:
        return out
    world.fired.add(("hash", "clue"))
    world.get("hash_page").meters["clue"] += 1
    world.get("detective").memes["hope"] += 1
    out.append("The hash marks looked like little stairs.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("partner").memes["helped"] < THRESHOLD:
        return out
    if ("teamwork", "solved") in world.fired:
        return out
    if world.get("hash_page").meters["clue"] < THRESHOLD:
        return out
    world.fired.add(("teamwork", "solved"))
    world.get("case").meters["solved"] += 1
    world.get("detective").memes["pride"] += 1
    world.get("partner").memes["pride"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule("confusion", "social", _r_confusion),
    Rule("hash", "clue", _r_hash),
    Rule("teamwork", "ending", _r_teamwork),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def predict_solution(world: World) -> dict:
    sim = world.copy()
    sim.get("transcript").meters["vague"] += 1
    propagate(sim, narrate=False)
    return {
        "confused": sim.get("detective").memes["puzzled"] >= THRESHOLD,
        "solved": sim.get("case").meters["solved"] >= THRESHOLD,
    }


def introduce(world: World, detective: Entity, partner: Entity) -> None:
    world.say(
        f"{detective.id} was a small detective with a sharp notebook and a very serious hat. "
        f"{partner.id} was {partner.pronoun('possessive')} partner, and together they liked to solve puzzles."
    )
    world.say(
        f"On a windy afternoon, they arrived at the library where the lost stamp case had grown unusually funny."
    )


def clue_scene(world: World, clue: Clue, device: Device) -> None:
    world.say(
        f"The only record was a {device.kind}: a {device.label_word if hasattr(device, 'label_word') else device.label} "
        f"called the transcript recorder. Its voice was vague, and every sentence sounded like a shrug."
    )
    world.say(
        f'One line said, "The stamp was near the {clue.label}, or maybe under it, or maybe beside something else."'
    )


def odd_little_joke(world: World, detective: Entity, partner: Entity) -> None:
    detective.memes["humor"] += 1
    partner.memes["humor"] += 1
    world.say(
        f'{partner.id} frowned at the paper. "This transcript is so vague it could be a cloud wearing shoes," '
        f'{partner.pronoun()} said.'
    )
    world.say(
        f'{detective.id} snorted. "Then let us do the walking before the cloud steals the stamp."'
    )


def search_together(world: World, detective: Entity, partner: Entity, clue: Clue, device: Device) -> None:
    partner.memes["helped"] += 1
    world.say(
        f"{detective.id} and {partner.id} split the work: one read the transcript, the other checked the shelves."
    )
    world.say(
        f"At the back of the library, they found a page marked with a hash of black lines. "
        f"It was folded into the catalog like a secret ladder."
    )
    world.get("hash_page").meters["seen"] += 1
    propagate(world, narrate=True)


def solve(world: World, detective: Entity, partner: Entity, outcome: Outcome) -> None:
    world.say(
        f"{detective.id} tapped the hash-marked page and grinned. "
        f'"The stamp is hidden in the checkout drawer," {detective.pronoun()} said. '
        f'"The transcript was vague, but the clue was not."'
    )
    world.say(
        f"{partner.id} opened the drawer, found the missing stamp, and held it up like a tiny treasure."
    )
    world.say(outcome.text)


def tell(detective_name: str, partner_name: str, clue: Clue, device: Device, outcome: Outcome) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type="girl", role="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type="boy", role="partner"))
    transcript = world.add(Entity(id="transcript", type="recording", label="transcript"))
    hash_page = world.add(Entity(id="hash_page", type="clue", label="hash-marked page"))
    case = world.add(Entity(id="case", type="case", label="missing stamp case"))

    transcript.meters["vague"] = 1.0
    transcript.memes["oddity"] = 1.0

    introduce(world, detective, partner)
    world.para()
    clue_scene(world, clue, device)
    odd_little_joke(world, detective, partner)
    world.para()
    search_together(world, detective, partner, clue, device)
    world.para()
    solve(world, detective, partner, outcome)

    world.facts.update(
        detective=detective,
        partner=partner,
        clue=clue,
        device=device,
        outcome=outcome,
        transcript=transcript,
        hash_page=hash_page,
        case=case,
        solved=case.meters["solved"] >= THRESHOLD,
        humor=detective.memes["humor"] + partner.memes["humor"],
        teamwork=partner.memes["helped"] >= THRESHOLD,
    )
    return world


CLUES = {
    "stamp": Clue(id="stamp", label="stamp tray", kind="object", tags={"library", "stamp"}),
    "cart": Clue(id="cart", label="return cart", kind="object", tags={"library", "cart"}),
    "shelf": Clue(id="shelf", label="tall shelf", kind="object", tags={"library", "shelf"}),
}

DEVICES = {
    "recorder": Device(id="recorder", label="recorder", kind="transcript recorder", can_be_vague=True, tags={"transcript", "vague"}),
    "notebook": Device(id="notebook", label="notebook", kind="notebook", can_be_vague=False, tags={"notes"}),
}

OUTCOMES = {
    "found": Outcome(id="found", label="found the stamp", humor=2, teamwork=2,
                     text="The case ended with a giggle, a high-five, and a very relieved librarian.",
                     tags={"teamwork", "humor"}),
    "quiet": Outcome(id="quiet", label="found the stamp quietly", humor=1, teamwork=2,
                     text="They closed the drawer gently and smiled like the best detectives in town.",
                     tags={"teamwork"}),
}

GIRL_NAMES = ["Mina", "Clara", "Nina", "Ruby", "Ivy", "Tess"]
BOY_NAMES = ["Owen", "Eli", "Max", "Finn", "Noah", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(c, d, o) for c in CLUES for d in DEVICES for o in OUTCOMES if DEVICES[d].can_be_vague]


@dataclass
class StoryParams:
    clue: str
    device: str
    outcome: str
    detective: str
    partner: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "transcript": [("What is a transcript?",
                    "A transcript is a written copy of words that were spoken out loud. It helps people read what someone said." )],
    "vague": [("What does vague mean?",
               "Vague means not clear or not exact. If something is vague, you may need more clues to understand it." )],
    "hash": [("What is a hash mark?",
              "A hash mark is a little mark made of crossing lines. People use hash marks to group or count things.")],
    "teamwork": [("What is teamwork?",
                  "Teamwork is when people help each other to finish a job. Working together can solve problems faster.")],
    "humor": [("Why do jokes help in a hard job?",
                "A little joke can make people relax and keep going. It can help a team stay cheerful while they work.")],
}

KNOWLEDGE_ORDER = ["transcript", "vague", "hash", "teamwork", "humor"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a small detective story for children that includes the words "hash", "transcript", and "vague".',
        f"Tell a funny mystery where {f['detective'].id} and {f['partner'].id} solve a library case by working together.",
        "Write a detective story where a vague transcript causes trouble, but a hash-marked clue and teamwork solve it.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    d, p = f["detective"], f["partner"]
    clue, device, outcome = f["clue"], f["device"], f["outcome"]
    qa = [
        ("Who are the detectives?",
         f"The detectives are {d.id} and {p.id}. They worked as a team and kept each other smiling."),
        ("What made the case hard at first?",
         f"The transcript was vague, so the clue did not sound clear. That made the missing stamp hard to find until they looked for a better hint."),
        ("What clue helped them solve the case?",
         f"The hash-marked page helped them solve it. It pointed them toward the checkout drawer and turned the vague clue into something useful."),
    ]
    if f["solved"]:
        qa.append((
            "How did teamwork help?",
            f"{d.id} read the transcript while {p.id} searched the shelves. They shared the work, found the hash-marked page, and solved the case together."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the missing stamp found, a laugh, and a high-five. The team solved the mystery and the librarian could breathe again."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].tags) | set(world.facts["device"].tags) | set(world.facts["outcome"].tags)
    out: list[tuple[str, str]] = []
    for k in KNOWLEDGE_ORDER:
        if k in tags:
            out.extend(KNOWLEDGE[k])
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(clue="stamp", device="recorder", outcome="found", detective="Mina", partner="Owen"),
    StoryParams(clue="cart", device="recorder", outcome="quiet", detective="Clara", partner="Eli"),
]


def explain_rejection(device: Device) -> str:
    return f"(No story: {device.kind} is not vague enough for this detective tale. Pick the transcript recorder.)"


def asp_facts() -> str:
    import asp
    lines = []
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
    for did, d in DEVICES.items():
        lines.append(asp.fact("device", did))
        if d.can_be_vague:
            lines.append(asp.fact("can_be_vague", did))
    for oid, o in OUTCOMES.items():
        lines.append(asp.fact("outcome_kind", oid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(C,D,O) :- clue(C), device(D), outcome_kind(O), can_be_vague(D).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between clingo and python valid_combos()")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"generate smoke test failed: {exc}")
    else:
        print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with a hash clue, a transcript, and a vague hint.")
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--outcome", choices=OUTCOMES)
    ap.add_argument("--detective")
    ap.add_argument("--partner")
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
    if args.device and not DEVICES[args.device].can_be_vague:
        raise StoryError(explain_rejection(DEVICES[args.device]))
    clue = args.clue or rng.choice(list(CLUES))
    device = args.device or "recorder"
    outcome = args.outcome or rng.choice(list(OUTCOMES))
    detective = args.detective or rng.choice(GIRL_NAMES)
    partner = args.partner or rng.choice([n for n in BOY_NAMES if n != detective])
    return StoryParams(clue=clue, device=device, outcome=outcome, detective=detective, partner=partner)


def generate(params: StoryParams) -> StorySample:
    if params.clue not in CLUES or params.device not in DEVICES or params.outcome not in OUTCOMES:
        raise StoryError("invalid parameters for detective story")
    if not DEVICES[params.device].can_be_vague:
        raise StoryError(explain_rejection(DEVICES[params.device]))
    world = tell(params.detective, params.partner, CLUES[params.clue], DEVICES[params.device], OUTCOMES[params.outcome])
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
