#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/society_doohicky_perk_surprise_heartwarming.py
====================================================================================================

A standalone storyworld for a heartwarming surprise about a small society,
a curious doohicky, and a perk that turns out to be a gift for everyone.

Premise:
A neighborhood society is preparing for its little spring gathering. One helper
finds a strange doohicky in the hall closet and worries it is a problem, but it
turns out to be a surprise perk for the whole group: a tiny community printer
that makes name tags, picture cards, and thank-you notes.

The world is intentionally tiny:
- a small cast of typed entities
- physical meters and emotional memes
- a causal rule or two
- a predictable setup -> surprise -> warm ending
- grounded QA from world state, not from rendered English

The story includes the required words:
- society
- doohicky
- perk
- surprise
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    caretaker: str = ""
    uses: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "mother", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Society:
    place: str
    event_name: str
    gathering: str
    surprise_word: str
    perk_word: str


@dataclass
class Doohicky:
    id: str
    label: str
    phrase: str
    purpose: str
    surprise_effect: str
    safe_use: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Perk:
    id: str
    label: str
    phrase: str
    delight: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, society: Society) -> None:
        self.society = society
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
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
        c = World(self.society)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_warm_smile(world: World) -> list[str]:
    out: list[str] = []
    host = world.facts["host"]
    helper = world.facts["helper"]
    if host.memes["worry"] < THRESHOLD:
        return out
    sig = ("warm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    host.memes["worry"] = 0.0
    host.memes["joy"] += 1
    helper.memes["joy"] += 1
    out.append("The room felt warmer all at once.")
    return out


CAUSAL_RULES = [Rule("warm_smile", "social", _r_warm_smile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def surprise_available(society: Society, doohicky: Doohicky, perk: Perk) -> bool:
    return "surprise" in society.event_name.lower() and doohicky.purpose and perk.delight


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id in SOCIETIES:
        for d_id in DOOHICKIES:
            for p_id in PERKS:
                if surprise_available(SOCIETIES[s_id], DOOHICKIES[d_id], PERKS[p_id]):
                    combos.append((s_id, d_id, p_id))
    return combos


@dataclass
class StoryParams:
    society: str = ""
    doohicky: str = ""
    perk: str = ""
    host_name: str = ""
    host_type: str = "woman"
    helper_name: str = ""
    helper_type: str = "boy"
    seed: Optional[int] = None


SOCIETIES = {
    "garden_club": Society(
        place="the community hall",
        event_name="the surprise spring society night",
        gathering="a table of lemonade and paper stars",
        surprise_word="surprise",
        perk_word="perk",
    ),
    "block_group": Society(
        place="the block room",
        event_name="the surprise welcome society meeting",
        gathering="folded chairs, cookies, and name tags",
        surprise_word="surprise",
        perk_word="perk",
    ),
    "book_circle": Society(
        place="the library nook",
        event_name="the surprise story society hour",
        gathering="little pillows, bookmarks, and cocoa",
        surprise_word="surprise",
        perk_word="perk",
    ),
    "music_circle": Society(
        place="the music room",
        event_name="the surprise evening society jam",
        gathering="a basket of snacks and handmade cards",
        surprise_word="surprise",
        perk_word="perk",
    ),
}

DOOHICKIES = {
    "printer": Doohicky(
        id="printer",
        label="tiny card printer",
        phrase="a tiny card printer",
        purpose="makes name tags and thank-you cards",
        surprise_effect="prints happy cards for the whole room",
        safe_use="print the welcome notes",
        tags={"paper", "cards", "surprise"},
    ),
    "stamper": Doohicky(
        id="stamper",
        label="stamp machine",
        phrase="a friendly stamp machine",
        purpose="presses little stars onto paper",
        surprise_effect="adds stars to every invitation",
        safe_use="decorate the welcome notes",
        tags={"paper", "stars", "surprise"},
    ),
    "labeler": Doohicky(
        id="labeler",
        label="label maker",
        phrase="a cheerful label maker",
        purpose="prints neat labels for baskets and jars",
        surprise_effect="makes every shelf feel organized",
        safe_use="mark the snacks and bins",
        tags={"labels", "paper", "surprise"},
    ),
    "ribboner": Doohicky(
        id="ribboner",
        label="ribbon cutter",
        phrase="a ribbon cutter with a smiling handle",
        purpose="cuts ribbon for gifts and banners",
        surprise_effect="turns plain bundles into presents",
        safe_use="finish the welcome table",
        tags={"ribbon", "gifts", "surprise"},
    ),
}

PERKS = {
    "snacks": Perk(
        id="snacks",
        label="snack perk",
        phrase="a snack perk",
        delight="gives everyone an extra cookie and a warm drink",
        tags={"cookies", "drink", "surprise"},
    ),
    "stickers": Perk(
        id="stickers",
        label="sticker perk",
        phrase="a sticker perk",
        delight="adds a bright sticker to every thank-you card",
        tags={"stickers", "cards", "surprise"},
    ),
    "music": Perk(
        id="music",
        label="music perk",
        phrase="a music perk",
        delight="lets the group pick one favorite song together",
        tags={"music", "surprise"},
    ),
    "flowers": Perk(
        id="flowers",
        label="flower perk",
        phrase="a flower perk",
        delight="puts small flowers on the welcome table",
        tags={"flowers", "surprise"},
    ),
}

NAMES = ["Mina", "June", "Owen", "Tara", "Eli", "Nia", "Pia", "Ben"]
KINDS = {"woman", "man", "girl", "boy"}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming surprise storyworld.")
    ap.add_argument("--society", choices=SOCIETIES)
    ap.add_argument("--doohicky", choices=DOOHICKIES)
    ap.add_argument("--perk", choices=PERKS)
    ap.add_argument("--host-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--host-type", choices=sorted(KINDS))
    ap.add_argument("--helper-type", choices=sorted(KINDS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.society is None or c[0] == args.society)
              and (args.doohicky is None or c[1] == args.doohicky)
              and (args.perk is None or c[2] == args.perk)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    society, doohicky, perk = rng.choice(sorted(combos))
    host_type = args.host_type or rng.choice(sorted(KINDS))
    helper_type = args.helper_type or rng.choice(sorted(KINDS))
    host_name = args.host_name or rng.choice(NAMES)
    helper_name = args.helper_name or rng.choice([n for n in NAMES if n != host_name])
    return StoryParams(
        society=society,
        doohicky=doohicky,
        perk=perk,
        host_name=host_name,
        host_type=host_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    soc = SOCIETIES[params.society]
    doh = DOOHICKIES[params.doohicky]
    perk = PERKS[params.perk]
    w = World(soc)
    host = w.add(Entity(
        id="host", kind="character", type=params.host_type, label=params.host_name,
        meters={"care": 0.0}, memes={"worry": 0.0, "joy": 0.0},
    ))
    helper = w.add(Entity(
        id="helper", kind="character", type=params.helper_type, label=params.helper_name,
        meters={"care": 0.0}, memes={"joy": 0.0},
    ))
    w.add(Entity(id="hall", kind="thing", type="place", label=soc.place, meters={}, memes={}))
    w.facts.update(host=host, helper=helper, society=soc, doohicky=doh, perk=perk)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming surprise story that includes the words society, doohicky, and perk.',
        f"Tell a gentle story where {f['host'].label} finds a {f['doohicky'].label} at {f['society'].place} and discovers it is a surprise perk.",
        f"Write a child-friendly surprise story about a society meeting, a doohicky, and a perk that helps everyone smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    host = f["host"]
    helper = f["helper"]
    soc = f["society"]
    doh = f["doohicky"]
    perk = f["perk"]
    return [
        QAItem(
            question=f"What did {host.label} find at {soc.place}?",
            answer=f"{host.label} found {doh.phrase}. At first it looked puzzling, but it turned out to be part of a kind surprise for the group.",
        ),
        QAItem(
            question=f"Why was the {doh.label} a surprise?",
            answer=f"It was a surprise because it was tucked away for the society gathering, and nobody expected it to help so many people at once. The little machine made the room feel special.",
        ),
        QAItem(
            question=f"What perk did {helper.label} help share with everyone?",
            answer=f"{helper.label} helped share {perk.phrase}. That perk made the gathering warmer and more cheerful for everyone there.",
        ),
        QAItem(
            question=f"How did {host.label} feel when the surprise was explained?",
            answer=f"{host.label} felt relieved and happy. The doohicky was not a problem at all; it was a thoughtful surprise that helped the whole society enjoy the night.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is a society?",
            answer="A society is a group of people who meet, share plans, and do things together.",
        ),
        QAItem(
            question="What is a doohicky?",
            answer="A doohicky is a playful word for a small machine or gadget when someone is not sure what it is at first.",
        ),
        QAItem(
            question="What is a perk?",
            answer="A perk is a nice extra benefit or treat that makes something better.",
        ),
        QAItem(
            question=f"Why can a surprise feel nice?",
            answer="A surprise can feel nice because it gives people a happy moment they were not expecting. When the surprise is kind, it can make everyone smile at once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.society not in SOCIETIES or params.doohicky not in DOOHICKIES or params.perk not in PERKS:
        raise StoryError("Invalid story params.")
    world = tell(params)
    f = world.facts
    host = f["host"]
    helper = f["helper"]
    soc = f["society"]
    doh = f["doohicky"]
    perk = f["perk"]
    world.say(f"At {soc.place}, the {society_name(soc)} was busy with {soc.gathering}.")
    world.say(f"{host.label} opened a closet and found {doh.phrase}.")
    world.say(f"{host.label} blinked. The doohicky had a purpose, but nobody expected a surprise like this.")
    host.memes["worry"] += 1
    world.para()
    world.say(f"Then {helper.label} smiled and explained the surprise perk.")
    world.say(f"The perk was {perk.phrase}, and it {perk.delight}.")
    helper.memes["joy"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"Together they used the {doh.label} for its {doh.safe_use}.")
    world.say(f"By the end, the {society_name(soc)} had name tags ready, happy faces on every table, and a room that felt brighter than before.")
    world.facts["resolved"] = True
    world.facts["surprised"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def society_name(soc: Society) -> str:
    return "society"


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.label, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def valid_story_count() -> int:
    return len(valid_combos())


ASP_RULES = r"""
valid(S,D,P) :- society(S), doohicky(D), perk(P), surprise_society(S), helpful(D), nice_perk(P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SOCIETIES:
        lines.append(asp.fact("society", sid))
        lines.append(asp.fact("surprise_society", sid))
    for did in DOOHICKIES:
        lines.append(asp.fact("doohicky", did))
        lines.append(asp.fact("helpful", did))
    for pid in PERKS:
        lines.append(asp.fact("perk", pid))
        lines.append(asp.fact("nice_perk", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        return 1
    try:
        sample = generate(
            StoryParams(
                society="garden_club",
                doohicky="printer",
                perk="snacks",
                host_name="Mina",
                host_type="woman",
                helper_name="Owen",
                helper_type="boy",
            )
        )
        _ = sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as exc:  # noqa: BLE001
        print(f"Smoke test failed: {exc}")
        return 1
    print(f"OK: verify passed for {valid_story_count()} combos and smoke test.")
    return 0


CURATED = [
    StoryParams(society="garden_club", doohicky="printer", perk="snacks", host_name="Mina", host_type="woman", helper_name="Owen", helper_type="boy"),
    StoryParams(society="block_group", doohicky="stamper", perk="stickers", host_name="Tara", host_type="girl", helper_name="Ben", helper_type="boy"),
    StoryParams(society="book_circle", doohicky="labeler", perk="music", host_name="June", host_type="woman", helper_name="Nia", helper_type="girl"),
    StoryParams(society="music_circle", doohicky="ribboner", perk="flowers", host_name="Eli", host_type="boy", helper_name="Pia", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{t}" for t in asp_valid_combos()))
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
