#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/spree_reconciliation_slice_of_life.py
======================================================================

A small slice-of-life story world about a child-sized shopping spree,
a misunderstanding, and a gentle reconciliation.

The seed idea is simple: two children head out on a little spree in an everyday
neighborhood, one of them gets carried away, feelings get bent out of shape,
and then they make up in a concrete, state-driven way that proves things have
changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/spree_reconciliation_slice_of_life.py
    python storyworlds/worlds/gpt-5.4-mini/spree_reconciliation_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4-mini/spree_reconciliation_slice_of_life.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/spree_reconciliation_slice_of_life.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
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
RECONCILE_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    name: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Spree:
    id: str
    noun: str
    verb: str
    what_it_is: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misstep:
    id: str
    noun: str
    action: str
    harm: str
    apology_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)


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


def _r_rumination(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.memes["hurt"] >= THRESHOLD and e.memes["care"] < THRESHOLD:
            sig = ("hurt", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["quiet"] += 1
            out.append("__quiet__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    a = world.entities.get("kid_a")
    b = world.entities.get("kid_b")
    if not a or not b:
        return out
    if a.memes["sorry"] >= THRESHOLD and b.memes["forgive"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        a.memes["hurt"] = 0.0
        b.memes["hurt"] = 0.0
        a.memes["warmth"] += 1
        b.memes["warmth"] += 1
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("rumination", _r_rumination), Rule("reconcile", _r_reconcile)]


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


def predict_tension(world: World, kid_a: Entity, spree: Spree, misstep: Misstep) -> dict:
    sim = world.copy()
    _do_misstep(sim, sim.get("kid_a"), spree, misstep, narrate=False)
    return {
        "hurt": sim.get("kid_a").memes["hurt"],
        "hurt_other": sim.get("kid_b").memes["hurt"],
    }


def _do_spree(world: World, kid_a: Entity, kid_b: Entity, spree: Spree) -> None:
    kid_a.meters["spent"] += 1
    kid_b.meters["spent"] += 1
    kid_a.memes["joy"] += 1
    kid_b.memes["joy"] += 1
    world.say(
        f"After breakfast, {kid_a.id} and {kid_b.id} went on a little spree to the corner street."
    )
    world.say(
        f"They drifted past the bakery, the comic rack, and the window with {spree.what_it_is}."
    )


def _do_misstep(world: World, kid_a: Entity, spree: Spree, misstep: Misstep, narrate: bool = True) -> None:
    kid_a.meters["spent"] += 1
    kid_a.memes["guilt"] += 1
    kid_a.memes["hurt"] += 1
    world.get("kid_b").memes["hurt"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"{kid_a.id} reached for one more {spree.noun}, and the pile at the counter got too big."
        )
        world.say(
            f"{world.get('kid_b').id} went quiet, because {misstep.harm}."
        )


def _do_apology(world: World, kid_a: Entity, kid_b: Entity, misstep: Misstep, repair: Repair) -> None:
    kid_a.memes["sorry"] += 1
    kid_b.memes["forgive"] += 1
    kid_b.memes["hurt"] += 1
    world.say(
        f"{kid_a.id} looked at {kid_b.id} and said, \"I'm sorry. I got carried away.\""
    )
    world.say(
        f"{kid_b.id} took a breath, nodded, and said, \"I was upset, but I still want to stay with you.\""
    )
    world.say(
        f"Then they {repair.action}, and the day felt lighter again."
    )
    world.say(
        f"{repair.result.capitalize()}, and the two friends walked home side by side."
    )


def _do_mirror(world: World, kid_a: Entity, kid_b: Entity) -> None:
    kid_a.memes["warmth"] += 1
    kid_b.memes["warmth"] += 1


def tell(place: Place, spree: Spree, misstep: Misstep, repair: Repair,
         name_a: str = "Maya", gender_a: str = "girl",
         name_b: str = "Noah", gender_b: str = "boy",
         parent: str = "mother") -> World:
    world = World()
    a = world.add(Entity(id=name_a, kind="character", type=gender_a, role="instigator"))
    b = world.add(Entity(id=name_b, kind="character", type=gender_b, role="companion"))
    p = world.add(Entity(id="Parent", kind="character", type=parent, label="the parent"))

    _do_spree(world, a, b, spree)

    world.para()
    world.say(
        f"{place.detail} made it feel like a normal Saturday, with carts rolling and music from a tinny speaker."
    )
    world.say(
        f"{a.id} wanted {spree.what_it_is}, and {b.id} wanted to keep the spree small."
    )
    world.say(
        f"When the counter started to fill up, {b.id} frowned."
    )
    tension = predict_tension(world, a, spree, misstep)
    world.facts["predicted"] = tension

    _do_misstep(world, a, spree, misstep)
    world.para()
    world.say(
        f"{p.label_word.capitalize()} saw the long faces and came over without raising {p.pronoun('possessive')} voice."
    )
    world.say(
        f"\"I think we need a reset,\" {p.id} said, and asked them to step aside by the bench."
    )

    world.para()
    _do_apology(world, a, b, misstep, repair)
    _do_mirror(world, a, b)
    world.say(
        f"{b.id} smiled again, and {a.id} held the bag more carefully after that."
    )
    world.say(
        f"At the end of the day, the little spree was not about the extra things anymore."
    )

    world.facts.update(
        kid_a=a, kid_b=b, parent=p, place=place, spree=spree, misstep=misstep,
        repair=repair, reconciled=True
    )
    return world


PLACES = {
    "corner": Place(id="corner", name="corner shop", detail="The corner shop smelled like warm bread and paper receipts.", tags={"shop"}),
    "market": Place(id="market", name="market", detail="The market was busy but friendly, with flower buckets by the door.", tags={"shop"}),
    "boardwalk": Place(id="boardwalk", name="boardwalk stand", detail="The boardwalk stand had bright jars lined up in the afternoon sun.", tags={"shop"}),
}

SPREES = {
    "snacks": Spree(id="snacks", noun="snack", verb="pick snacks", what_it_is="a row of bright sweets and crackers", tags={"spree", "snack"}),
    "stickers": Spree(id="stickers", noun="sticker", verb="choose stickers", what_it_is="a page of shiny stickers", tags={"spree", "sticker"}),
    "pages": Spree(id="pages", noun="storybook", verb="choose storybooks", what_it_is="a little display of picture books", tags={"spree", "books"}),
}

MISSTEPS = {
    "extras": Misstep(id="extras", noun="extra treats", action="kept adding things", harm="one child felt left out", apology_line="I got carried away", tags={"hurt", "spend"}),
    "noise": Misstep(id="noise", noun="loud chatter", action="talked over the other child", harm="the other child felt unheard", apology_line="I wasn't listening", tags={"hurt", "talk"}),
}

REPAIRS = {
    "share": Repair(id="share", action="split the bag and choose together", result="They shared the bag and picked one thing each", tags={"reconcile", "share"}),
    "return": Repair(id="return", action="put the extra item back", result="They put the extra item back and chose one treat together", tags={"reconcile", "return"}),
}

GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Ben", "Max", "Finn"]
TRAITS = ["thoughtful", "curious", "gentle", "quiet", "patient"]


@dataclass
class StoryParams:
    place: str
    spree: str
    misstep: str
    repair: str
    name_a: str
    gender_a: str
    name_b: str
    gender_b: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SPREES:
            for m in MISSTEPS:
                for r in REPAIRS:
                    combos.append((p, s, m, r))
    return combos


def explain_rejection() -> str:
    return "(No story: this world only supports everyday sprees that can plausibly lead to a small misunderstanding and a reconciliation.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a small spree and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--spree", choices=SPREES)
    ap.add_argument("--misstep", choices=MISSTEPS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              and (args.spree is None or c[1] == args.spree)
              and (args.misstep is None or c[2] == args.misstep)
              and (args.repair is None or c[3] == args.repair)]
    if not combos:
        raise StoryError(explain_rejection())
    place, spree, misstep, repair = rng.choice(sorted(combos))
    gender_a = args.gender_a or rng.choice(["girl", "boy"])
    gender_b = args.gender_b or ("boy" if gender_a == "girl" else "girl")
    name_a = rng.choice(GIRL_NAMES if gender_a == "girl" else BOY_NAMES)
    pool_b = [n for n in (GIRL_NAMES if gender_b == "girl" else BOY_NAMES) if n != name_a]
    name_b = args.name_b if hasattr(args, "name_b") and args.name_b else rng.choice(pool_b)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        spree=spree,
        misstep=misstep,
        repair=repair,
        name_a=name_a,
        gender_a=gender_a,
        name_b=name_b,
        gender_b=gender_b,
        parent=parent,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["kid_a"], f["kid_b"]
    place, spree = f["place"], f["spree"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "spree" and ends with two children making up.',
        f"Tell a small everyday story where {a.id} and {b.id} go on a {spree.id} spree at the {place.name} and then reconcile after a hurt feeling.",
        f"Write a gentle story about a shopping spree, a misunderstanding, and an apology that makes the friends feel close again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, p = f["kid_a"], f["kid_b"], f["parent"]
    place, spree, misstep, repair = f["place"], f["spree"], f["misstep"], f["repair"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two children who went out together and then had to fix a small hurt feeling. {p.label_word.capitalize()} helped them calm down and talk it through."
        ),
        QAItem(
            question="What did they go on?",
            answer=f"They went on a little spree at the {place.name}. It was a normal errand-and-treat kind of day, not a huge adventure."
        ),
        QAItem(
            question=f"What went wrong during the spree?",
            answer=f"{a.id} got carried away and {misstep.harm}. That made {b.id} feel hurt, so the happy mood slid sideways for a moment."
        ),
        QAItem(
            question="How did they make up?",
            answer=f"{a.id} apologized, {b.id} listened, and then they used the {repair.id} repair. After that, they were able to walk home together again."
        ),
    ]
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    spree = f["spree"]
    out = {
        "What is a spree?": "A spree is a short time spent going from place to place and getting or doing a lot of one thing. It can be fun, but it can also get too much if someone forgets to share or listen.",
        "What does it mean to apologize?": "To apologize means to say you are sorry for hurting someone or making a mistake. A real apology helps the other person feel seen.",
        "Why do people reconcile?": "People reconcile so they can be close again after a disagreement. It usually takes a sorry, a calm talk, and a small change in behavior.",
    }
    if spree.id == "snacks":
        out["Why can sharing snacks matter?"] = "Sharing snacks matters because it helps everyone feel included and keeps one child from taking all the treats."
    return [QAItem(q, a) for q, a in out.items()]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== story qa =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,S,M,R) :- place(P), spree(S), misstep(M), repair(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SPREES:
        lines.append(asp.fact("spree", s))
    for m in MISSTEPS:
        lines.append(asp.fact("misstep", m))
    for r in REPAIRS:
        lines.append(asp.fact("repair", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/4."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        emit(sample, trace=True, qa=True, header="smoke")
        _ = buf
    except Exception as e:
        print(f"MISMATCH: smoke test failed: {e}")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("spree", SPREES), ("misstep", MISSTEPS), ("repair", REPAIRS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        PLACES[params.place], SPREES[params.spree], MISSTEPS[params.misstep], REPAIRS[params.repair],
        params.name_a, params.gender_a, params.name_b, params.gender_b, params.parent
    )
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


CURATED = [
    StoryParams(place="corner", spree="snacks", misstep="extras", repair="share", name_a="Maya", gender_a="girl", name_b="Noah", gender_b="boy", parent="mother"),
    StoryParams(place="market", spree="stickers", misstep="noise", repair="return", name_a="Lily", gender_a="girl", name_b="Ben", gender_b="boy", parent="father"),
    StoryParams(place="boardwalk", spree="pages", misstep="extras", repair="share", name_a="Theo", gender_a="boy", name_b="Ella", gender_b="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
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
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
