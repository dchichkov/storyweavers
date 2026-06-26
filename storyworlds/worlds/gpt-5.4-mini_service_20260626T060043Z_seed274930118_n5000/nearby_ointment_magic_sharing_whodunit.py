#!/usr/bin/env python3
"""
storyworlds/worlds/nearby_ointment_magic_sharing_whodunit.py
=============================================================

A small whodunit-style story world about a missing magical ointment, nearby
clues, and a sharing-based resolution.

Premise:
- A tiny cast gathers at a cozy place.
- A magical ointment can soothe itchy skin and brighten a sore mood.
- Someone used it nearby, and everyone has a reason to have touched it.
- The detective must observe clues, question suspects, and decide who shared
  the jar, who borrowed it, and who finally returned it.

The simulation is state-driven:
- characters have meters (physical state) and memes (emotional/social state)
- the ointment can be nearby, opened, moved, used, shared, or hidden
- clues accumulate from proximity, residue, and testimony
- the solution depends on the actual world state, not a frozen template

The world keeps the prose child-facing, concrete, and causal.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carrier: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    label: str
    indoor: bool = True
    nearby_spots: list[str] = field(default_factory=list)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    near_spots: set[str]
    smells: str
    magic: bool = False


@dataclass
class SuspectProfile:
    id: str
    role: str
    type: str
    name: str
    can_share: bool = True
    likes_magic: bool = False


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _nearby(world: World, actor: Entity, item: Entity) -> bool:
    return actor.meters.get("nearby", 0.0) >= THRESHOLD and item.meters.get("nearby", 0.0) >= THRESHOLD


def _used_magic(world: World, actor: Entity, ointment: Entity) -> bool:
    return actor.meters.get("smeared", 0.0) >= THRESHOLD and ointment.owner == actor.id


def _share_clue(world: World) -> list[str]:
    out: list[str] = []
    ointment = world.get("ointment")
    for actor in world.characters():
        if actor.meters.get("shared", 0.0) < THRESHOLD:
            continue
        sig = ("share", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} had shared the ointment with someone nearby.")
    return out


def _powder_clue(world: World) -> list[str]:
    out: list[str] = []
    ointment = world.get("ointment")
    for actor in world.characters():
        if actor.meters.get("ointment_smear", 0.0) < THRESHOLD:
            continue
        sig = ("smear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["clue"] = actor.meters.get("clue", 0.0) + 1
        out.append(f"Some shiny ointment was left on {actor.id}'s sleeve.")
    return out


def _jealousy_clue(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("jealous", 0.0) < THRESHOLD:
            continue
        sig = ("jealous", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} had wanted the magic ointment for {actor.pronoun('possessive')}self.")
    return out


CAUSAL_RULES = [_share_clue, _powder_clue, _jealousy_clue]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


@dataclass
class StoryParams:
    place: str
    detective: str
    suspect1: str
    suspect2: str
    culprit: str
    seed: Optional[int] = None


PLACES = {
    "bathroom": Place(label="the bathroom", indoor=True, nearby_spots=["sink", "counter", "towel rack"]),
    "kitchen": Place(label="the kitchen", indoor=True, nearby_spots=["table", "shelf", "window"]),
    "nursery": Place(label="the nursery", indoor=True, nearby_spots=["crib", "chair", "drawer"]),
}

CHARACTERS = {
    "Mira": Entity(id="Mira", kind="character", type="girl", traits=["curious", "careful"]),
    "Noah": Entity(id="Noah", kind="character", type="boy", traits=["gentle", "quiet"]),
    "Ada": Entity(id="Ada", kind="character", type="girl", traits=["brave", "thoughtful"]),
    "Ben": Entity(id="Ben", kind="character", type="boy", traits=["kind", "messy"]),
    "Nia": Entity(id="Nia", kind="character", type="girl", traits=["bright", "patient"]),
}

ITEMS = {
    "ointment": Item(
        id="ointment",
        label="magic ointment",
        phrase="a little jar of magic ointment",
        near_spots={"counter", "table", "drawer"},
        smells="sweet and minty",
        magic=True,
    ),
    "gloves": Item(
        id="gloves",
        label="gloves",
        phrase="soft gloves",
        near_spots={"sink", "drawer"},
        smells="plain",
    ),
    "spoon": Item(
        id="spoon",
        label="spoon",
        phrase="a tiny spoon",
        near_spots={"counter", "table"},
        smells="plain",
    ),
}

ROLES = [
    "detective",
    "helper",
    "guest",
    "caregiver",
    "visitor",
]

GIRL_NAMES = ["Mira", "Ada", "Nia"]
BOY_NAMES = ["Noah", "Ben"]
ALL_NAMES = GIRL_NAMES + BOY_NAMES


def valid_triples() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for d in ALL_NAMES:
            for s1 in ALL_NAMES:
                for s2 in ALL_NAMES:
                    if len({d, s1, s2}) < 3:
                        continue
                    combos.append((place, d, s1))
    return combos


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    detective = world.add(copy.deepcopy(CHARACTERS[params.detective]))
    suspect1 = world.add(copy.deepcopy(CHARACTERS[params.suspect1]))
    suspect2 = world.add(copy.deepcopy(CHARACTERS[params.suspect2]))
    culprit = world.get(params.culprit)

    ointment = world.add(Entity(
        id="ointment",
        kind="thing",
        type="jar",
        label="magic ointment",
        phrase="a little jar of magic ointment",
        owner=culprit.id,
        carrier=culprit.id,
    ))
    gloves = world.add(Entity(
        id="gloves",
        kind="thing",
        type="gloves",
        label="gloves",
        phrase="soft gloves",
    ))
    spoon = world.add(Entity(
        id="spoon",
        kind="thing",
        type="spoon",
        label="spoon",
        phrase="a tiny spoon",
    ))

    detective.meters["nearby"] = 1
    suspect1.meters["nearby"] = 1
    suspect2.meters["nearby"] = 1
    culprit.meters["nearby"] = 1
    ointment.meters["nearby"] = 1
    gloves.meters["nearby"] = 1
    spoon.meters["nearby"] = 1

    detective.memes["curious"] = 1
    suspect1.memes["nervous"] = 0.5
    suspect2.memes["nervous"] = 0.5
    culprit.memes["jealous"] = 1.0

    # The culprit used the ointment and shared it with one nearby person.
    culprit.meters["smeared"] = 1.0
    culprit.meters["shared"] = 1.0
    suspect1.meters["ointment_smear"] = 1.0

    propagate(world, narrate=False)

    world.facts = {
        "detective": detective,
        "suspect1": suspect1,
        "suspect2": suspect2,
        "culprit": culprit,
        "ointment": ointment,
        "gloves": gloves,
        "spoon": spoon,
    }
    return world


def tell(world: World) -> None:
    f = world.facts
    d: Entity = f["detective"]
    s1: Entity = f["suspect1"]
    s2: Entity = f["suspect2"]
    c: Entity = f["culprit"]
    ointment: Entity = f["ointment"]

    world.say(
        f"At {world.place.label}, {d.id} noticed a small problem: the magic ointment was nearby, but nobody could agree on who had used it."
    )
    world.say(
        f"The jar smelled sweet and minty, and {d.id} could see that {s1.id}'s sleeve had a shiny streak."
    )
    world.para()
    world.say(
        f"{d.id} asked the others one by one, because a good detective knows that a calm question can reveal a hidden truth."
    )
    world.say(
        f"{s2.id} shook {s2.pronoun('possessive')} head and said {s2.pronoun()} only saw the jar near the counter."
    )
    world.say(
        f"{c.id} looked uneasy, and {c.id} kept glancing at the spoon that sat nearby."
    )
    world.para()

    if c.meters.get("shared", 0.0) >= THRESHOLD:
        world.say(
            f"Then the clues fit together: {c.id} had used the magic ointment first and shared it with {s1.id}, which explained the shiny sleeve."
        )
        world.say(
            f"{d.id} smiled, because the mystery was not theft at all. It was a small act of sharing that had simply made a mess."
        )
    else:
        world.say(
            f"The clues did not line up at first, so {d.id} looked again at the nearby jar, the spoon, and the sleeve."
        )
        world.say(
            f"In the end, the answer was simple: someone had shared the ointment and then forgotten to close the lid."
        )

    world.para()
    world.say(
        f"{c.id} apologized and offered to share the ointment properly, using the spoon so everyone could take only a little."
    )
    world.say(
        f"Soon the jar was closed, the sleeve was wiped clean, and {d.id} left with a neat little case solved."
    )

    world.facts["resolved"] = True
    world.facts["shared_by"] = c.id
    world.facts["shine_on"] = s1.id


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit story for a young child about a magic ointment that is nearby.',
        f"Tell a gentle mystery where {f['detective'].id} figures out who used the ointment and why it was shared.",
        f"Write a simple detective story set at {world.place.label} with a shiny clue on a sleeve and a small act of sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]
    s1: Entity = f["suspect1"]
    s2: Entity = f["suspect2"]
    c: Entity = f["culprit"]
    qa = [
        QAItem(
            question=f"Who solved the mystery at {world.place.label}?",
            answer=f"{d.id} solved it by noticing the nearby clues and asking calm questions.",
        ),
        QAItem(
            question=f"What was special about the jar?",
            answer="It was a magic ointment jar, so everyone cared about where it was and who had touched it.",
        ),
        QAItem(
            question=f"What clue showed that {s1.id} had been near the ointment?",
            answer=f"{s1.id}'s sleeve had a shiny streak of ointment on it, which told {d.id} that the jar had been shared nearby.",
        ),
        QAItem(
            question=f"Why did the mystery turn out to be about sharing instead of stealing?",
            answer=f"Because {c.id} had used the magic ointment and shared it with {s1.id}, so the clue was from borrowing, not taking it away.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="The jar was closed again, the sleeve was cleaned, and the detective left with the mystery solved.",
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "magic": [
        QAItem(
            question="What does magic mean in a story?",
            answer="Magic means something surprising and special can happen that feels beyond ordinary everyday life.",
        )
    ],
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something for a little while, often by taking turns.",
        )
    ],
    "ointment": [
        QAItem(
            question="What is ointment?",
            answer="Ointment is a soft cream or salve that people put on skin to help it feel better.",
        )
    ],
    "nearby": [
        QAItem(
            question="What does nearby mean?",
            answer="Nearby means close to you, like something you can reach or see without going far away.",
        )
    ],
    "whodunit": [
        QAItem(
            question="What is a whodunit story?",
            answer="A whodunit is a mystery story where the reader tries to figure out who caused the problem.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"magic", "sharing", "ointment", "nearby", "whodunit"}
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE[tag])
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
nearby(E) :- entity(E), has_meter(E, nearby).
shared(O) :- thing(O), has_meter(O, shared).
smeared(E) :- entity(E), has_meter(E, smeared).
culprit(E) :- entity(E), has_meter(E, shared), has_meter(E, smeared).
clue(E) :- entity(E), has_meter(E, ointment_smear).
mystery_solved :- culprit(_), shared(_), clue(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for spot in p.nearby_spots:
            lines.append(asp.fact("spot", pid, spot))
    for eid, ent in CHARACTERS.items():
        lines.append(asp.fact("entity", eid))
        lines.append(asp.fact("character", eid))
        for t in ent.traits:
            lines.append(asp.fact("trait", eid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("entity", iid))
        lines.append(asp.fact("thing", iid))
        if item.magic:
            lines.append(asp.fact("magic_item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: nearby magic ointment and a sharing mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--detective", choices=ALL_NAMES)
    ap.add_argument("--suspect1", choices=ALL_NAMES)
    ap.add_argument("--suspect2", choices=ALL_NAMES)
    ap.add_argument("--culprit", choices=ALL_NAMES)
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
    place = args.place or rng.choice(list(PLACES))
    names = ALL_NAMES[:]
    detective = args.detective or rng.choice(names)
    names.remove(detective)
    suspect1 = args.suspect1 or rng.choice(names)
    if suspect1 in names:
        names.remove(suspect1)
    suspect2 = args.suspect2 or rng.choice(names)
    if suspect2 == suspect1 or suspect2 == detective:
        raise StoryError("The three roles must be filled by three different characters.")
    if args.culprit:
        culprit = args.culprit
    else:
        culprit = rng.choice([detective, suspect1, suspect2])
    if len({detective, suspect1, suspect2, culprit}) < 3:
        raise StoryError("The detective, suspects, and culprit need enough variety for a whodunit.")
    return StoryParams(place=place, detective=detective, suspect1=suspect1, suspect2=suspect2, culprit=culprit)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for d in ALL_NAMES:
            for s1 in ALL_NAMES:
                for s2 in ALL_NAMES:
                    if len({d, s1, s2}) == 3:
                        combos.append((place, d, s1))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_solved/0."))
    return sorted(set(asp.atoms(model, "mystery_solved")))


def asp_verify() -> int:
    import asp
    _ = asp.one_model(asp_program("#show mystery_solved/0."))
    print("OK: ASP program loaded and solved.")
    return 0


CURATED = [
    StoryParams(place="bathroom", detective="Mira", suspect1="Noah", suspect2="Ada", culprit="Ada"),
    StoryParams(place="kitchen", detective="Nia", suspect1="Ben", suspect2="Mira", culprit="Ben"),
    StoryParams(place="nursery", detective="Noah", suspect1="Ada", suspect2="Nia", culprit="Nia"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_solved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show mystery_solved/0."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective}: {p.place} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
