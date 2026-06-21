#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/slender_certificate_parentheses_conflict_bad_ending_slice.py
==============================================================================================

A tiny slice-of-life storyworld about a small office errand: a child helps a
grown-up sort a certificate, a misunderstanding grows around a note in
parentheses, and the day can end either with a calm fix or with a bad ending.

This world is intentionally narrow. It models a few typed entities with physical
meters and emotional memes, and it lets simulated state drive the prose instead
of swapping nouns into a frozen paragraph.

The seed words are woven into the world:
- slender
- certificate
- parentheses

The narrative instruments are:
- conflict
- bad ending

The style is slice of life: everyday, concrete, and small-scale.
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
class Setting:
    id: str
    place: str
    details: str
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


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    slender: bool = False
    usable: bool = False
    paper: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class ConflictBeat:
    id: str
    text: str
    trouble: int
    resolve_power: int
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_conflict(world: World) -> list[str]:
    out = []
    clerk = world.entities.get("Clerk")
    child = world.entities.get("Child")
    if not clerk or not child:
        return out
    if child.memes["worry"] < THRESHOLD or clerk.memes["worry"] < THRESHOLD:
        return out
    sig = ("conflict",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clerk.memes["hurt"] += 1
    child.memes["hurt"] += 1
    out.append("__conflict__")
    return out


def _r_bad_ending(world: World) -> list[str]:
    out = []
    cert = world.entities.get("certificate")
    if not cert or cert.meters["creased"] < THRESHOLD:
        return out
    sig = ("bad_ending",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["quiet"] += 1
    out.append("__bad__")
    return out


CAUSAL_RULES = [Rule("conflict", _r_conflict), Rule("bad_ending", _r_bad_ending)]


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


def reasonableness_ok(note: ObjectCfg, certificate: ObjectCfg, beat: ConflictBeat) -> bool:
    return note.usable and certificate.paper and beat.trouble >= beat.resolve_power


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for nid, note in NOTES.items():
            for cid, cert in CERTIFICATES.items():
                if reasonableness_ok(note, cert, CONFLICTS["parentheses"]):
                    combos.append((sid, nid, cid))
    return combos


def build_story_state(setting: Setting, note: ObjectCfg, certificate: ObjectCfg,
                      beat: ConflictBeat, parent_name: str, child_name: str) -> World:
    world = World()
    parent = world.add(Entity(id="Parent", kind="character", type="mother", label=parent_name, role="parent"))
    child = world.add(Entity(id="Child", kind="character", type="boy", label=child_name, role="child"))
    clerk = world.add(Entity(id="Clerk", kind="character", type="woman", label="the clerk", role="helper"))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    note_ent = world.add(Entity(id="note", type="thing", label=note.label))
    cert_ent = world.add(Entity(id="certificate", type="thing", label=certificate.label))

    child.memes["curiosity"] = 1
    child.memes["worry"] = 0
    clerk.memes["worry"] = 0
    parent.memes["worry"] = 0

    world.say(
        f"On a plain afternoon, {parent.label_word} and {child.label} went to {setting.place}. "
        f"{setting.details}"
    )
    world.say(
        f"{child.label} carried a slim envelope and kept looking at the slender certificate inside it."
    )
    world.say(
        f'There was a note written in parentheses: "{beat.text}"'
    )
    world.para()
    child.memes["worry"] += 1
    clerk.memes["worry"] += 1
    world.say(
        f"{child.label} frowned and asked what the parentheses meant. "
        f"{clerk.label} thought the note was about the certificate itself, and the room went tense."
    )
    propagate(world, narrate=False)

    world.para()
    if beat.resolve_power < beat.trouble:
        child.meters["creased"] += 1
        cert_ent.meters["creased"] += 1
        world.say(
            f"{child.label} tugged the paper too hard, and the certificate bent with a sharp crease."
        )
        world.say(
            f"{parent.label_word.capitalize()} tried to explain, but the damage was already done."
        )
        world.say(
            f"The clerk stamped the form flat again, yet the day felt smaller and heavier after that."
        )
        world.say(
            f"By the time they left, the slender certificate was still there, but the happy part of the errand was gone."
        )
    else:
        world.say(
            f"{clerk.label} took the time to read the parentheses aloud and smiled at the simple mistake."
        )
        world.say(
            f"{parent.label_word.capitalize()} laughed too, and the certificate stayed smooth in the folder."
        )
        world.say(
            f"Before they left, {child.label} carried the papers carefully, proud to help."
        )

    world.facts.update(
        setting=setting,
        note=note,
        certificate=certificate,
        beat=beat,
        parent=parent,
        child=child,
        clerk=clerk,
        room=room,
        outcome="bad" if beat.resolve_power < beat.trouble else "good",
    )
    return world


def tell(setting: Setting, note: ObjectCfg, certificate: ObjectCfg, beat: ConflictBeat,
         parent_name: str = "Mom", child_name: str = "Ben") -> World:
    return build_story_state(setting, note, certificate, beat, parent_name, child_name)


SETTINGS = {
    "office": Setting(
        id="office",
        place="the small office",
        details="A fan hummed softly near the window, and the desk held a stamp pad, a pen, and a stack of forms.",
    ),
    "hall": Setting(
        id="hall",
        place="the front hall",
        details="A row of chairs sat against the wall, and a bulletin board covered the far side with tidy notices.",
    ),
}

NOTES = {
    "slender_note": ObjectCfg(
        id="slender_note",
        label="slender note",
        phrase="a slender note",
        slender=True,
        usable=True,
        tags={"slender"},
    ),
    "receipt_note": ObjectCfg(
        id="receipt_note",
        label="receipt",
        phrase="a folded receipt",
        usable=True,
        tags={"paper"},
    ),
}

CERTIFICATES = {
    "certificate": ObjectCfg(
        id="certificate",
        label="certificate",
        phrase="a certificate",
        paper=True,
        tags={"certificate"},
    ),
    "warranty": ObjectCfg(
        id="warranty",
        label="warranty paper",
        phrase="a warranty paper",
        paper=True,
        tags={"certificate"},
    ),
}

CONFLICTS = {
    "parentheses": ConflictBeat(
        id="parentheses",
        text="Please ignore the parentheses.",
        trouble=3,
        resolve_power=1,
        tags={"parentheses", "conflict", "bad_ending"},
    )
}


@dataclass
class StoryParams:
    setting: str
    note: str
    certificate: str
    conflict: str
    parent_name: str = "Mom"
    child_name: str = "Ben"
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


CURATED = [
    StoryParams(
        setting="office",
        note="slender_note",
        certificate="certificate",
        conflict="parentheses",
        parent_name="Mom",
        child_name="Ben",
    ),
    StoryParams(
        setting="hall",
        note="receipt_note",
        certificate="warranty",
        conflict="parentheses",
        parent_name="Dad",
        child_name="Ivy",
    ),
]


def explain_rejection(note: ObjectCfg, certificate: ObjectCfg, beat: ConflictBeat) -> str:
    if not note.usable:
        return f"(No story: {note.label} does not create a usable slice-of-life conflict.)"
    if not certificate.paper:
        return f"(No story: {certificate.label} is not a certificate-like paper item.)"
    return "(No story: this combination does not produce the needed small conflict.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.note and args.certificate:
        note = NOTES[args.note]
        cert = CERTIFICATES[args.certificate]
        if not reasonableness_ok(note, cert, CONFLICTS["parentheses"]):
            raise StoryError(explain_rejection(note, cert, CONFLICTS["parentheses"]))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.note is None or c[1] == args.note)
        and (args.certificate is None or c[2] == args.certificate)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, note, certificate = rng.choice(sorted(combos))
    parent_name = args.parent_name or rng.choice(["Mom", "Dad"])
    child_name = args.child_name or rng.choice(["Ben", "Ivy", "Lia", "Noah"])
    return StoryParams(
        setting=setting,
        note=note,
        certificate=certificate,
        conflict="parentheses",
        parent_name=parent_name,
        child_name=child_name,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "{f["note"].label}", '
        f'"certificate", and "parentheses".',
        f"Tell a small everyday story where {f['child'].label} misreads parentheses "
        f"while helping with a certificate, and the day ends badly.",
        f"Write a quiet conflict story about a slender piece of paper and a certificate "
        f"in an office, with a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    note = f["note"]
    cert = f["certificate"]
    items = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.label} helping {parent.label_word} with a certificate at the office. "
                   f"The trouble came from a note in parentheses that nobody read the same way.",
        ),
        QAItem(
            question="Why did the conflict start?",
            answer=f"The conflict started because {child.label} and the clerk misunderstood the parentheses on the note. "
                   f"That small mistake made the certificate feel suddenly fragile and important.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended badly. The certificate got creased, and the errand lost its easy, neat feeling.",
        ),
    ]
    if world.facts.get("outcome") == "bad":
        items.append(
            QAItem(
                question=f"What happened to the {cert.label}?",
                answer=f"The {cert.label} bent and got a sharp crease when {child.label} tugged too hard. "
                       f"That left the page looking worn instead of tidy.",
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are parentheses?",
            answer="Parentheses are curved marks used to add a little extra note inside a sentence. "
                   "They can be easy to misread if someone is rushed.",
        ),
        QAItem(
            question="What is a certificate?",
            answer="A certificate is a paper that shows proof of something important. "
                   "People usually want to keep it neat and flat.",
        ),
        QAItem(
            question="What does slender mean?",
            answer="Slender means long, narrow, and thin. It is often used to describe something delicate-looking.",
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
conflict :- worry(child), worry(clerk).
bad_ending :- creased(certificate), conflict.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "office"),
        asp.fact("setting", "hall"),
        asp.fact("note", "slender_note"),
        asp.fact("note", "receipt_note"),
        asp.fact("certificate", "certificate"),
        asp.fact("certificate", "warranty"),
        asp.fact("conflict_beat", "parentheses"),
        asp.fact("usable", "slender_note"),
        asp.fact("usable", "receipt_note"),
        asp.fact("paper", "certificate"),
        asp.fact("paper", "warranty"),
        asp.fact("worry_trigger", "parentheses"),
    ]
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    # smoke test a normal generation
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Slice-of-life storyworld with a slender note, a certificate, and parentheses."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--note", choices=NOTES)
    ap.add_argument("--certificate", choices=CERTIFICATES)
    ap.add_argument("--parent-name")
    ap.add_argument("--child-name")
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.note not in NOTES:
        raise StoryError("Invalid note.")
    if params.certificate not in CERTIFICATES:
        raise StoryError("Invalid certificate.")
    setting = SETTINGS[params.setting]
    note = NOTES[params.note]
    cert = CERTIFICATES[params.certificate]
    beat = CONFLICTS[params.conflict]
    world = tell(setting, note, cert, beat, params.parent_name, params.child_name)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
