#!/usr/bin/env python3
"""
storyworlds/worlds/paraphrase_seaside_promenade_suspense_magic_twist_space.py
=============================================================================

A standalone storyworld about a seaside promenade with a space-adventure feel:
a small crew, a glowing clue, a suspenseful search, a bit of magic, and a twist
that changes what the crew thought they knew.

The seed story idea:
---
On a seaside promenade at dusk, a child in a tiny space-crew game hears a
glowing shell whisper a clue. The child tries to paraphrase the whisper for a
friend, but the words sound slippery and strange. A parent worries the clue may
lead to trouble on the dark pier, where the tide is rising and the lights are
going out. After a careful search, the "mystery" turns out to be magic from a
lantern-fish in a tide pool, and the clue helps them find a lost toy starship
before the tide covers the rocks.

This world keeps typed entities with physical meters and emotional memes, a
forward-chained world model, a reasonableness gate, and an inline ASP twin.
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
class StoryParams:
    place: str = "promenade"
    clue: str = "shell"
    find: str = "starship"
    helper: str = "mother"
    child_name: str = "Mia"
    child_gender: str = "girl"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    whisper: str
    glow: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Find:
    id: str
    label: str
    phrase: str
    lost_where: str
    reveals: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_glow(world: World) -> list[str]:
    out = []
    if world.facts["clue_seen"] and not world.facts["clue_glowing"]:
        world.facts["clue_glowing"] = True
        world.get("clue").meters["magic"] += 1
        out.append("The clue began to glow.")
    return out


def _r_suspense(world: World) -> list[str]:
    out = []
    if world.facts["darkening"] and not world.facts["found"]:
        world.get("child").memes["suspense"] += 1
        world.get("helper").memes["worry"] += 1
        if ("suspense",) not in world.fired:
            world.fired.add(("suspense",))
            out.append("The dark water made the search feel urgent.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    if world.facts["twist_revealed"] and not world.facts["found"]:
        world.get("find").memes["surprise"] += 1
        if ("twist",) not in world.fired:
            world.fired.add(("twist",))
            out.append("The clue was not a warning after all.")
    return out


CAUSAL_RULES = [Rule("glow", _r_glow), Rule("suspense", _r_suspense), Rule("twist", _r_twist)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_world(params: StoryParams) -> tuple[World, Place, Clue, Find]:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    find = FINDS[params.find]
    w = World(place)
    child = w.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    helper = w.add(Entity(id="helper", kind="character", type=params.helper, label={"mother": "mom", "father": "dad"}.get(params.helper, params.helper), type=params.helper, role="helper"))
    clue_ent = w.add(Entity(id="clue", type="thing", label=clue.label, phrase=clue.whisper))
    find_ent = w.add(Entity(id="find", type="thing", label=find.label, phrase=find.phrase))
    w.facts.update(
        child=child,
        helper=helper,
        clue=clue_ent,
        find=find_ent,
        place=place,
        clue_cfg=clue,
        find_cfg=find,
        clue_seen=False,
        clue_glowing=False,
        twist_revealed=False,
        found=False,
        darkening=False,
    )
    return w, place, clue, find


def tell(params: StoryParams) -> World:
    w, place, clue, find = build_world(params)
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    helper: Entity = w.facts["helper"]  # type: ignore[assignment]
    clue_ent: Entity = w.facts["clue"]  # type: ignore[assignment]
    find_ent: Entity = w.facts["find"]  # type: ignore[assignment]

    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    helper.memes["care"] += 1

    w.say(f"{child.label} and {helper.label_word} walked along {place.label} at dusk.")
    w.say(place.detail)
    w.say(f"{child.label} found {clue.label} and heard it whisper, \"{clue.whisper}\".")
    w.facts["clue_seen"] = True
    propagate(w)

    w.para()
    child.memes["desire"] += 1
    w.say(f"{child.label} tried to paraphrase the whisper for {helper.label_word}, but the message sounded slippery.")
    w.say(f"{helper.label_word.capitalize()} pointed toward the dark rocks and said they should be careful.")
    w.facts["darkening"] = True
    propagate(w)

    w.para()
    w.say(f"Then came the twist: {clue.risk.lower()} was only part of the story.")
    w.facts["twist_revealed"] = True
    clue_ent.meters["magic"] += 1
    propagate(w)

    w.para()
    w.say(f"Under a tide pool, they found {find.phrase}, tucked near {find.lost_where}.")
    w.say(f"The little clue had led them straight to it, just before the water rose.")
    w.say(f"In the end, {clue.label} still glowed softly, and {find.label} rode home in {child.label}'s hands.")

    w.facts["found"] = True
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    find_ent.meters["safe"] += 1
    return w


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for c in CLUES:
            for f in FINDS:
                combos.append((p, c, f))
    return combos


GIRL_NAMES = ["Mia", "Nora", "Ava", "Lena", "Iris", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Theo", "Max", "Eli", "Noah"]


PLACES = {
    "promenade": Place("promenade", "the seaside promenade", "The promenade lights blinked on one by one, and the sea breathed below the rail.", {"clue", "find"}),
    "pier": Place("pier", "the old pier", "The pier creaked over the black water, and every wave sounded like a secret.", {"clue", "find"}),
    "boardwalk": Place("boardwalk", "the wooden boardwalk", "The boardwalk shone with salt, and the shops were closing their bright doors.", {"clue", "find"}),
    "lighthouse": Place("lighthouse", "the lighthouse steps", "The lighthouse beam spun over the water, making silver paths on the waves.", {"clue", "find"}),
}

CLUES = {
    "shell": Clue("shell", "a glowing shell", "Follow the silver ring.", "magic", "It might lead to trouble on the dark water.", {"magic", "suspense"}),
    "bottle": Clue("bottle", "a bottle with a blue note", "Listen for the tide song.", "magic", "It could slip away before they understood it.", {"magic", "suspense"}),
    "lantern": Clue("lantern", "a tiny brass lantern", "Take the light and trust the turning.", "magic", "It seemed too small to matter, yet it mattered a lot.", {"magic", "suspense"}),
    "kite": Clue("kite", "a star-shaped kite", "Look where the string points.", "magic", "It trembled as if it knew a hidden path.", {"magic", "suspense"}),
}

FINDS = {
    "starship": Find("starship", "a toy starship", "a little silver toy starship", "a shallow tide pool", "the crew had lost at dusk", {"space", "twist"}),
    "compass": Find("compass", "a compass", "a round compass with a cracked lid", "a pile of smooth pebbles", "the map had pointed to by mistake", {"space", "twist"}),
    "badge": Find("badge", "a space badge", "a bright tin space badge", "a patch of wet sand", "someone had hidden for a game", {"space", "twist"}),
    "robot": Find("robot", "a little robot", "a clockwork robot with one blue eye", "the sea grass near the steps", "the tide had nudged into view", {"space", "twist"}),
}

CURATED = [
    StoryParams(place="promenade", clue="shell", find="starship", helper="mother", child_name="Mia", child_gender="girl"),
    StoryParams(place="pier", clue="bottle", find="compass", helper="father", child_name="Finn", child_gender="boy"),
    StoryParams(place="boardwalk", clue="lantern", find="badge", helper="mother", child_name="Ava", child_gender="girl"),
    StoryParams(place="lighthouse", clue="kite", find="robot", helper="father", child_name="Theo", child_gender="boy"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this seaside mystery needs a clue and a find that can be linked by the magic twist.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    h = f["helper"]
    clue = f["clue_cfg"]
    find = f["find_cfg"]
    return [
        f'Write a short space-adventure story for a child at the seaside promenade that includes the word "paraphrase".',
        f"Tell a suspenseful story where {c.label} and {h.label_word} follow {clue.label}, then discover the magic twist behind it.",
        f"Write a gentle mystery with sea air, a glowing clue, and a final reveal that leads to {find.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c: Entity = f["child"]  # type: ignore[assignment]
    h: Entity = f["helper"]  # type: ignore[assignment]
    clue = f["clue_cfg"]
    find = f["find_cfg"]
    place = f["place"]
    return [
        QAItem(
            f"Who walked along {place.label} in the story?",
            f"{c.label} and {h.label_word} walked there together. They were exploring the promenade like a tiny space crew, looking for a clue.",
        ),
        QAItem(
            f"What did {c.label} do with the whisper from {clue.label}?",
            f"{c.label} tried to paraphrase it for {h.label_word}. The message was slippery, so the words came out a little strange before the twist was revealed.",
        ),
        QAItem(
            f"Why did the search feel suspenseful near the water?",
            f"The lights were fading and the tide was rising, so the search felt urgent. That made the clue seem important before anyone knew what it really meant.",
        ),
        QAItem(
            f"What was the magic twist in the story?",
            f"The clue was not a warning at all; it was a magical guide. It led them to {find.phrase} before the water covered the rocks.",
        ),
        QAItem(
            f"What did {c.label} find at the end?",
            f"{c.label} found {find.phrase}. It had been waiting near {find.lost_where}, and the clue helped bring it into the light.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "magic": [("What is magic in a story?", "Magic is something surprising and special that seems to break the normal rules. In stories, it can glow, whisper, or help characters find hidden things.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of wondering what will happen next. It makes a story feel tense and exciting.")],
    "space": [("What is a starship?", "A starship is a ship imagined for travel in space. In stories, children often use toy starships for pretend adventures.")],
    "tide": [("What is a tide?", "A tide is the sea moving in and out along the shore. When the tide comes in, water can cover rocks and sand very quickly.")],
    "promenade": [("What is a promenade?", "A promenade is a wide walkway near the water where people can stroll, watch the waves, and enjoy the view.")],
}
WORLD_KNOWLEDGE_ORDER = ["magic", "suspense", "space", "tide", "promenade"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["clue_cfg"].tags) | set(world.facts["find_cfg"].tags) | {"promenade"}
    out: list[QAItem] = []
    for key in WORLD_KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def valid_combo(params: tuple[str, str, str]) -> bool:
    return params in valid_combos()


ASP_RULES = r"""
clue_seen.
glowing :- clue_seen.
suspense :- darkening, not found.
twist :- twist_revealed.
valid(P,C,F) :- place(P), clue(C), find(F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for f in FINDS:
        lines.append(asp.fact("find", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH between ASP and Python valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, clue=None, find=None, helper=None, child_name=None, child_gender=None, seed=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test completed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Seaside promenade space-adventure storyworld with suspense, magic, and a twist.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--find", choices=FINDS)
    ap.add_argument("--helper", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.find is None or c[2] == args.find)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, find = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    return StoryParams(place=place, clue=clue, find=find, helper=helper, child_name=name, child_gender=gender)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.clue not in CLUES or params.find not in FINDS:
        raise StoryError("Invalid StoryParams.")
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print("  ", c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
