#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/elevator_divert_flashback_bad_ending_humor_comedy.py
====================================================================================

A tiny storyworld about a child riding an elevator, trying to divert attention,
remembering an old funny flashback, and ending up in a bad-but-safe comedy beat.

Core seed words: elevator, divert
Style: comedy
Features: flashback, humor, bad ending

The world models a small apartment-building elevator scene. A child wants to make
a quick trip playful, but the elevator slows, the child tries to divert the mood
with a joke or button pressing, a flashback explains why they are nervous, and
the ending is "bad" in the comedy sense: the joke backfires, the child gets
embarrassed, and the ride becomes awkward, but nobody is harmed. The story ends
with a concrete image proving what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Building:
    id: str
    label: str
    floors: int
    has_lobby: bool = True
    has_elevator: bool = True
    elevator_speed: int = 1
    old_sign: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Gadget:
    id: str
    label: str
    action: str
    harmless: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Flashback:
    id: str
    trigger: str
    memory: str
    lesson: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    building: Building
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        return World(self.building, copy.deepcopy(self.entities), copy.deepcopy(self.facts), [[]], set(self.fired))

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: callable

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_embarrass(world: World) -> list[str]:
    out = []
    kid = world.get("kid")
    if kid.meters.get("embarrassed", 0.0) < THRESHOLD:
        return out
    sig = ("embarrass",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid.memes["awkward"] = kid.memes.get("awkward", 0.0) + 1
    out.append("__awkward__")
    return out


CAUSAL_RULES = [Rule("embarrass", _r_embarrass)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy elevator storyworld with a flashback and a bad ending.")
    ap.add_argument("--building", choices=BUILDINGS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--gadget", choices=GADGETS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for b in BUILDINGS:
        for f in FLASHBACKS:
            for g in GADGETS:
                if BUILDINGS[b].has_elevator and GADGETS[g].harmless:
                    combos.append((b, f, g))
    return combos


@dataclass
@dataclass
class StoryParams:
    building: str
    flashback: str
    gadget: str
    name: str
    gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


BUILDINGS = {
    "apartment": Building("apartment", "the apartment building", 8, old_sign="Do not hold the door too long."),
    "hotel": Building("hotel", "the hotel", 12, old_sign="Please let the elevator close."),
    "school": Building("school", "the school", 4, old_sign="No silly button games."),
}

FLASHBACKS = {
    "stuck": Flashback("stuck", "the doors blinked", "last summer the doors had been slow and everyone had groaned", "slow doors are not dangerous, just annoying"),
    "prank": Flashback("prank", "the button lit up", "the child once pressed every button and the elevator sang and stopped at every floor", "jokes can make a ride longer"),
    "banana": Flashback("banana", "the bell pinged", "an old banana peel joke had made a grown-up laugh so hard they snorted", "humor is fun, but timing matters"),
}

GADGETS = {
    "joke": Gadget("joke", "a joke", "divert the mood with a joke"),
    "button": Gadget("button", "the open button", "divert the ride by pressing the wrong button"),
    "face": Gadget("face", "a funny face", "divert attention with a funny face"),
}

NAMES_GIRL = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
NAMES_BOY = ["Max", "Leo", "Finn", "Noah", "Theo", "Jack"]


def asp_facts() -> str:
    import asp
    lines = []
    for bid in BUILDINGS:
        lines.append(asp.fact("building", bid))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        if g.harmless:
            lines.append(asp.fact("harmless", gid))
    lines.append(asp.fact("has_elevator", "building"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(B, F, G) :- building(B), flashback(F), gadget(G), harmless(G).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p, c = set(valid_combos()), set(asp_valid_combos())
    if p == c:
        print(f"OK: ASP matches valid_combos() ({len(p)} combos).")
        ok = 0
    else:
        print("MISMATCH:")
        print("only python:", sorted(p - c))
        print("only asp:", sorted(c - p))
        ok = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = 1
    return ok


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.building and args.building not in BUILDINGS:
        raise StoryError("Unknown building.")
    if args.flashback and args.flashback not in FLASHBACKS:
        raise StoryError("Unknown flashback.")
    if args.gadget and args.gadget not in GADGETS:
        raise StoryError("Unknown gadget.")
    if args.gadget and not GADGETS[args.gadget].harmless:
        raise StoryError("That gadget would make the scene unsafe.")
    combos = [c for c in valid_combos()
              if (args.building is None or c[0] == args.building)
              and (args.flashback is None or c[1] == args.flashback)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    building, flashback, gadget = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(building, flashback, gadget, name, gender)


def tell(params: StoryParams) -> World:
    b = BUILDINGS[params.building]
    fb = FLASHBACKS[params.flashback]
    gd = GADGETS[params.gadget]
    w = World(b)
    kid = w.add(Entity("kid", "character", params.gender, params.name, ["funny", "restless"], "hero"))
    guard = w.add(Entity("guard", "character", "adult", "the guard", role="helper"))
    elevator = w.add(Entity("elevator", "thing", "elevator", "the elevator"))
    kid.memes["giddy"] = 1
    kid.memes["humor"] = 1

    w.say(f"{kid.id} rode the elevator in {b.label} and tried to {gd.action}.")
    w.say(f"It was meant to be funny, because {kid.id} liked making the ride feel less boring.")
    w.para()
    w.say(f"Then {fb.trigger}, and {kid.id} had a flashback: {fb.memory}.")
    w.say(f"That old memory made {kid.id} grin and wince at the same time, because {fb.lesson}.")
    w.para()
    if gd.id == "button":
        kid.meters["embarrassed"] = 1
        w.say(f"{kid.id} pressed the wrong button, and the elevator sighed, slowed, and stopped for a moment.")
        w.say(f"{kid.id} tried to divert attention with a laugh, but the joke landed with a tiny thud.")
        w.say("The guard coughed politely, and the whole car became very quiet.")
    elif gd.id == "face":
        kid.meters["embarrassed"] = 1
        w.say(f"{kid.id} made a silly face in the mirrored wall to divert the mood.")
        w.say(f"Unfortunately, the face looked more surprised than funny, so even {kid.id} snorted at it.")
        w.say("A neighbor smiled once, then looked down at their shoes to hide a laugh.")
    else:
        kid.meters["embarrassed"] = 1
        w.say(f"{kid.id} told a joke to divert the mood, but the punch line arrived too late and sounded even sillier than planned.")
        w.say(f"The guard blinked, and then the guard laughed so hard that {kid.id} turned bright red.")
        w.say("The elevator dinged at the next floor, but the joke had already escaped into the air and could not be taken back.")
    propagate(w, narrate=False)
    w.para()
    w.say(f"At last the doors opened, and {kid.id} stepped out with a red face and a small, nervous smile.")
    w.say("The bad part was that the joke failed, but the funny part was that everyone remembered it anyway.")
    w.facts.update(kid=kid, guard=guard, elevator=elevator, building=b, flashback=fb, gadget=gd, outcome="bad")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child that includes the words "elevator" and "divert".',
        f"Tell a comedy story where {f['kid'].id} rides an elevator, tries to divert attention, and remembers an old flashback.",
        f"Write a short bad-ending comedy about a child in an elevator who uses humor, but the joke backfires.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    gd = f["gadget"]
    fb = f["flashback"]
    qa = [
        ("What is the story about?",
         f"It is about {kid.id} riding an elevator and trying to make the ride feel funny. The story follows a small problem, a flashback, and an awkward ending."),
        ("Why did {0} try to be funny?".format(kid.id),
         f"{kid.id} wanted to divert attention and make the elevator ride less boring. The humor was supposed to help, but it did not work very well."),
        ("What was the flashback about?",
         f"The flashback was about {fb.memory}. It came back because {fb.trigger} inside the elevator."),
        ("What happened at the end?",
         f"{kid.id} stepped out with a red face after the joke failed. The ending is bad in a comedy way, because the joke backfired instead of saving the moment."),
    ]
    if gd.id == "button":
        qa.append(("How did the child try to divert the ride?",
                   f"{kid.id} pressed the wrong button to divert the ride. That made the elevator pause and made the moment even more awkward."))
    elif gd.id == "face":
        qa.append(("How did the child try to divert the mood?",
                   f"{kid.id} made a funny face to divert the mood. The face was more awkward than hilarious, so it only made the child blush."))
    else:
        qa.append(("How did the child try to divert attention?",
                   f"{kid.id} told a joke to divert attention. The joke landed poorly, which is why the ending feels funny and bad at the same time."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {world.facts["building"].id, world.facts["flashback"].id, world.facts["gadget"].id, "elevator", "humor", "flashback"}
    out = []
    if "elevator" in tags:
        out.append(("What is an elevator?", "An elevator is a box that moves people up and down between floors in a building. It saves climbing stairs."))

    out.extend([
        ("What does divert mean?", "To divert means to turn attention or a path away from where it was going. A funny joke can divert a person's attention for a moment."),
        ("What is a flashback?", "A flashback is a memory scene that comes back into a character's mind. It helps explain why the character feels a certain way now."),
        ("Why can humor be tricky?", "Humor can be tricky because a joke might land well, or it might make things more awkward if people are not expecting it."),
    ])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("\n== (3) World knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("apartment", "prank", "joke", "Mia", "girl"),
    StoryParams("hotel", "stuck", "face", "Noah", "boy"),
    StoryParams("school", "banana", "button", "Lily", "girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
              if (args.building is None or c[0] == args.building)
              and (args.flashback is None or c[1] == args.flashback)
              and (args.gadget is None or c[2] == args.gadget)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    building, flashback, gadget = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    return StoryParams(building, flashback, gadget, name, gender)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for b, f, g in asp_valid_combos():
            print(f"  {b:10} {f:8} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
