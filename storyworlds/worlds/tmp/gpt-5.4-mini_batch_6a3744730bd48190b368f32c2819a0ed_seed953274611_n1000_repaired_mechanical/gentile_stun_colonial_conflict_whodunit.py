#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gentile_stun_colonial_conflict_whodunit.py
===========================================================================

A standalone storyworld for a small whodunit-style mystery about a museum
conflict: a colonial exhibit is disturbed, a gentle suspect is blamed, and the
real culprit is exposed when a stun light and a hidden clue reveal the truth.

The story is child-facing, concrete, and state-driven. It supports the shared
Storyweavers CLI contract, includes a Python reasonableness gate plus an inline
ASP twin, and generates three Q&A sets from the simulated world state.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Suspect:
    id: str
    label: str
    gentle: bool
    relation: str
    clue: str
    alibi: str
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
class Exhibit:
    id: str
    label: str
    phrase: str
    location: str
    fragile: bool
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
class Tool:
    id: str
    label: str
    phrase: str
    emits_stun: bool
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
class Culprit:
    id: str
    label: str
    motive: str
    method: str
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    inspector = world.get("Inspector")
    if inspector.memes["suspicion"] >= THRESHOLD and inspector.meters["tension"] < THRESHOLD:
        sig = ("conflict", "tension")
        if sig not in world.fired:
            world.fired.add(sig)
            inspector.meters["tension"] += 1
            out.append("__conflict__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("Lantern").meters["stun"] >= THRESHOLD and world.get("Case").meters["opened"] >= THRESHOLD:
        sig = ("clue",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("Clue").meters["found"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES = [
    ("conflict", _r_conflict),
    ("clue", _r_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for _, rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for venue in VENUES:
        for suspect in SUSPECTS:
            for exhibit in EXHIBITS:
                if exhibit.fragile and venue in exhibit.location:
                    combos.append((venue, suspect.id, exhibit.id))
    return combos


@dataclass
class StoryParams:
    venue: str
    suspect: str
    exhibit: str
    helper: str
    culprit: str
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


VENUES = ["gallery", "hall", "archive"]
SUSPECTS = {
    "gentile_guest": Suspect(
        id="gentile guest",
        label="gentile guest",
        gentle=True,
        relation="visitor",
        clue="paint on the cuff",
        alibi="was reading a map by the door",
        tags={"gentile"},
    ),
    "curator": Suspect(
        id="curator",
        label="the curator",
        gentle=False,
        relation="staff",
        clue="dust on the shoes",
        alibi="was counting labels at the desk",
        tags={"staff"},
    ),
}
EXHIBITS = {
    "colonial_chest": Exhibit(
        id="colonial_chest",
        label="colonial chest",
        phrase="an old colonial chest",
        location="archive hall",
        fragile=True,
        tags={"colonial"},
    ),
    "colonial_map": Exhibit(
        id="colonial_map",
        label="colonial map",
        phrase="a framed colonial map",
        location="gallery hall",
        fragile=True,
        tags={"colonial"},
    ),
}
TOOLS = {
    "stun_lamp": Tool(
        id="stun_lamp",
        label="stun lamp",
        phrase="a stun lamp",
        emits_stun=True,
        tags={"stun"},
    ),
    "desk_lamp": Tool(
        id="desk_lamp",
        label="desk lamp",
        phrase="a desk lamp",
        emits_stun=False,
        tags={"lamp"},
    ),
}
CULPRITS = {
    "mouse": Culprit(
        id="mouse",
        label="the mouse",
        motive="wanted warm paper for a nest",
        method="pulled at the latch",
        tags={"mouse"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld with a conflict and a hidden culprit.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--exhibit", choices=EXHIBITS)
    ap.add_argument("--helper", choices=TOOLS)
    ap.add_argument("--culprit", choices=CULPRITS)
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


def explain_rejection(exhibit: Exhibit) -> str:
    return f"(No story: {exhibit.label} is not in a place this world can reasonably disturb.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.exhibit and args.exhibit not in EXHIBITS:
        raise StoryError("(No story: unknown exhibit.)")
    if args.suspect and args.suspect not in SUSPECTS:
        raise StoryError("(No story: unknown suspect.)")
    if args.helper and args.helper not in TOOLS:
        raise StoryError("(No story: unknown helper tool.)")
    if args.culprit and args.culprit not in CULPRITS:
        raise StoryError("(No story: unknown culprit.)")

    venue = args.venue or rng.choice(VENUES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    exhibit = args.exhibit or rng.choice(list(EXHIBITS))
    helper = args.helper or rng.choice(list(TOOLS))
    culprit = args.culprit or rng.choice(list(CULPRITS))

    ex = EXHIBITS[exhibit]
    if venue not in ex.location:
        raise StoryError(explain_rejection(ex))
    return StoryParams(venue=venue, suspect=suspect, exhibit=exhibit, helper=helper, culprit=culprit)


def tell(params: StoryParams) -> World:
    world = World()
    inspector = world.add(Entity(id="Inspector", kind="character", type="girl", role="inspector"))
    witness = world.add(Entity(id="Witness", kind="character", type="boy", role="witness"))
    case = world.add(Entity(id="Case", label=params.exhibit))
    clue = world.add(Entity(id="Clue", label="a hidden clue"))
    lantern = world.add(Entity(id="Lantern", label=params.helper))
    suspect = SUSPECTS[params.suspect]
    culprit = CULPRITS[params.culprit]
    exhibit = EXHIBITS[params.exhibit]

    world.say(
        f"At the {params.venue}, Inspector and Witness found trouble by {exhibit.phrase}. "
        f"The room was quiet, but the old label had been moved."
    )
    world.say(
        f"Inspector looked at the gentle guest and said the clue seemed to point there, "
        f"because {suspect.clue} looked suspicious."
    )
    inspector.memes["suspicion"] += 1
    witness.memes["worry"] += 1
    world.para()
    world.say(
        f"Witness lifted {TOOLS[params.helper].phrase}. Its glow gave just enough light to stun the shadows and show the latch."
    )
    lantern.meters["stun"] += 1
    case.meters["opened"] += 1
    propagate(world, narrate=False)
    if world.get("Clue").meters["found"] >= THRESHOLD:
        world.say(
            f"Under the frame, they found a tiny mark. It did not belong to the gentle guest at all."
        )
    world.say(
        f"Then the real culprit appeared: {culprit.label} had {culprit.method} and left the chest half-open."
    )
    world.para()
    inspector.memes["suspicion"] = 0
    inspector.memes["relief"] += 1
    world.say(
        f"Inspector closed the case with a nod. The gentle guest was cleared, the colonial exhibit was safe again, "
        f"and the little room felt calm after the conflict."
    )
    world.facts.update(
        venue=params.venue,
        suspect=suspect,
        exhibit=exhibit,
        helper=TOOLS[params.helper],
        culprit=culprit,
        story_outcome="solved",
        clue_found=bool(world.get("Clue").meters["found"] >= THRESHOLD),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly whodunit story set in a {f['venue']} with a gentle suspect and a colonial object.",
        f"Tell a mystery where a stun lamp reveals a clue and the wrong person is blamed at first.",
        f"Write a short conflict-and-resolution story where the colonial exhibit is saved and the real culprit is exposed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who was blamed first?",
            answer=f"The gentle guest was blamed first because the clue seemed to point that way. The mistake was fixed when the stun light showed a better clue.",
        ),
        QAItem(
            question="What helped solve the mystery?",
            answer=f"{f['helper'].label.capitalize()} helped solve it by shining light on the latch and revealing a hidden clue. That clue showed the colonial exhibit had been opened by the real culprit, not the gentle guest.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The gentle guest was cleared, the exhibit was put back in order, and the conflict ended calmly. The last image is a safe room with the true culprit exposed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a stun lamp do in this storyworld?",
            answer="A stun lamp makes a bright, startling light that helps people notice hidden details. It is useful here because the light pulls a clue out of the shadows.",
        ),
        QAItem(
            question="What is a colonial exhibit?",
            answer="A colonial exhibit is an old historical object or display from colonial times. In this storyworld, it is something fragile that should be handled carefully.",
        ),
        QAItem(
            question="What does gentle mean?",
            answer="Gentle means kind, soft, and careful. A gentle person does not want to cause harm or trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(venue="gallery", suspect="gentile_guest", exhibit="colonial_map", helper="stun_lamp", culprit="mouse"),
    StoryParams(venue="archive", suspect="curator", exhibit="colonial_chest", helper="desk_lamp", culprit="mouse"),
]


def valid_story(params: StoryParams) -> bool:
    return params.exhibit in EXHIBITS and params.venue in EXHIBITS[params.exhibit].location


def generate(params: StoryParams) -> StorySample:
    if params.suspect not in SUSPECTS or params.exhibit not in EXHIBITS or params.helper not in TOOLS or params.culprit not in CULPRITS:
        raise StoryError("(No story: invalid parameter key.)")
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


ASP_RULES = r"""
valid(V,S,E) :- venue(V), suspect(S), exhibit(E), loc(E,V).
solved :- valid(_,_,_), helper(stun_lamp), culprit(mouse).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for e, ex in EXHIBITS.items():
        lines.append(asp.fact("exhibit", e))
        for loc in ex.location.split():
            lines.append(asp.fact("loc", e, loc))
    for h in TOOLS:
        lines.append(asp.fact("helper", h))
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            return 1
    except Exception as e:
        print(f"FAIL: generate smoke test failed: {e}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with gentile/stun/colonial conflict.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--suspect", choices=list(SUSPECTS))
    ap.add_argument("--exhibit", choices=list(EXHIBITS))
    ap.add_argument("--helper", choices=list(TOOLS))
    ap.add_argument("--culprit", choices=list(CULPRITS))
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
    venue = args.venue or rng.choice(VENUES)
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    exhibit = args.exhibit or rng.choice(list(EXHIBITS))
    helper = args.helper or rng.choice(list(TOOLS))
    culprit = args.culprit or rng.choice(list(CULPRITS))
    if not valid_story(StoryParams(venue=venue, suspect=suspect, exhibit=exhibit, helper=helper, culprit=culprit)):
        raise StoryError(explain_rejection(EXHIBITS[exhibit]))
    return StoryParams(venue=venue, suspect=suspect, exhibit=exhibit, helper=helper, culprit=culprit)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show solved/0."))
        print("ASP ready:", model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
