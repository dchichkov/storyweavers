#!/usr/bin/env python3
"""
storyworlds/worlds/scrub_reconciliation_surprise_moral_value_slice_of.py
=======================================================================

A small slice-of-life story world about a shared cleanup, a surprise, and a
kind reconciliation.

Premise:
- Two people share a cozy kitchen or porch workspace.
- One of them makes a mess while trying to help or make something nice.
- The other is disappointed, but the two repair things by scrubbing together.
- A small surprise reveals the moral value of apologizing, sharing work, and
  making amends.

The prose is built from world state, not from a frozen template. The same state
also drives QA and a tiny ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
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
    role: str = ""
    owner: str | None = None
    caretaker: str | None = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.history: list[dict[str, Any]] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, str]] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, sentence: str) -> None:
        if sentence:
            self.paragraphs[-1].append(sentence)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = copy.deepcopy(self.facts)
        clone.history = copy.deepcopy(self.history)
        clone.paragraphs = copy.deepcopy(self.paragraphs)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    pair: str
    mess: str
    surprise: str
    moral: str
    seed: int | None = None


@dataclass
class PairConfig:
    id: str
    a_name: str
    a_gender: str
    b_name: str
    b_gender: str
    relation: str
    pair_label: str
    shared_place: str


@dataclass
class MessConfig:
    id: str
    label: str
    phrase: str
    verb: str
    outcome: str
    cleaner: str
    meter: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseConfig:
    id: str
    label: str
    phrase: str
    reveal: str
    gift: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralConfig:
    id: str
    lesson: str
    tags: set[str] = field(default_factory=set)


PAIRS = {
    "sisters": PairConfig("sisters", "Mina", "girl", "June", "girl", "sisters", "two sisters", "the kitchen"),
    "brothers": PairConfig("brothers", "Theo", "boy", "Nico", "boy", "brothers", "two brothers", "the porch"),
    "friends": PairConfig("friends", "Lena", "girl", "Parker", "boy", "friends", "two friends", "the kitchen"),
}

MESSES = {
    "flour": MessConfig("flour", "flour", "a trail of flour", "scooped flour", "floury", "sponge and warm water", "mess", "table", {"flour", "scrub"}),
    "paint": MessConfig("paint", "paint", "bright paint marks", "brushed paint", "painty", "soap and cloth", "stain", "table", {"paint", "scrub"}),
    "juice": MessConfig("juice", "juice", "sticky juice puddles", "spilled juice", "sticky", "scrub brush and soap", "spill", "floor", {"juice", "scrub"}),
}

SURPRISES = {
    "cookies": SurpriseConfig("cookies", "cookies", "a plate of cookies", "brought out a small plate of cookies", "cookies", {"cookies", "surprise"}),
    "note": SurpriseConfig("note", "note", "a tucked note", "found a kind note under the dish towel", "note", {"note", "surprise"}),
    "flowers": SurpriseConfig("flowers", "flowers", "a tiny vase of flowers", "set out a tiny vase of flowers", "flowers", {"flowers", "surprise"}),
}

MORALS = {
    "apology": MoralConfig("apology", "saying sorry matters", {"apology", "moral"}),
    "help": MoralConfig("help", "helping to clean up matters", {"help", "moral"}),
    "share": MoralConfig("share", "sharing the work matters", {"share", "moral"}),
}

PLACES = {
    "kitchen": "the kitchen",
    "porch": "the porch",
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in PLACES:
        for pair_id, pair in PAIRS.items():
            if pair.shared_place != PLACES[place_id]:
                continue
            for mess_id in MESSES:
                for surprise_id in SURPRISES:
                    combos.append((place_id, pair_id, mess_id, surprise_id))
    return combos


def explain_rejection() -> str:
    return "(No story: the requested options do not fit this small slice-of-life world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a mess, a scrub, and a reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--pair", choices=PAIRS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.pair is None or c[1] == args.pair)
              and (args.mess is None or c[2] == args.mess)
              and (args.surprise is None or c[3] == args.surprise)]
    if not combos:
        raise StoryError(explain_rejection())
    place, pair, mess, surprise = rng.choice(sorted(combos))
    moral = args.moral or rng.choice(sorted(MORALS))
    return StoryParams(place=place, pair=pair, mess=mess, surprise=surprise, moral=moral)


def _add_pair(world: World, cfg: PairConfig) -> tuple[Entity, Entity]:
    a = world.add(Entity(id=cfg.a_name, kind="character", type=cfg.a_gender, role="first", traits=["careful"]))
    b = world.add(Entity(id=cfg.b_name, kind="character", type=cfg.b_gender, role="second", traits=["busy"]))
    return a, b


def _spill(world: World, actor: Entity, mess: MessConfig, place: str) -> None:
    actor.meters[mess.meter] += 1
    actor.memes["guilt"] += 1
    world.facts["mess_meter"] = mess.meter
    world.facts["mess_zone"] = mess.zone
    world.facts["mess_phrase"] = mess.phrase
    world.event("mess", actor=actor.id, mess=mess.id, place=place)


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    if world.facts.get("cleaning_started") and world.facts.get("mess_meter"):
        sig = ("clean", world.facts["mess_meter"])
        if sig not in world.fired:
            world.fired.add(sig)
            for ent in world.entities.values():
                if ent.kind == "character":
                    ent.memes["calm"] += 1
            out.append("The two of them worked until the table was neat again.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(place: str, pair: PairConfig, mess: MessConfig, surprise: SurpriseConfig, moral: MoralConfig) -> World:
    world = World()
    a, b = _add_pair(world, pair)
    table = world.add(Entity(id="table", type="table", label="the table"))
    soap = world.add(Entity(id="soap", type="soap", label=mess.cleaner, tags={"scrub"}))
    world.facts.update(place=place, pair=pair, mess=mess, surprise=surprise, moral=moral,
                       a=a.id, b=b.id, table=table.id, soap=soap.id,
                       reconciled=False, surprised=False)

    world.say(f"That afternoon, {a.id} and {b.id} were at {PLACES[place]}.")
    world.say(f"They were trying to make the room look nice, but {a.id} tipped over {mess.phrase}.")
    _spill(world, a, mess, place)
    world.say(f"{b.id} frowned at the {mess.label}, and for a moment the room felt quiet.")
    world.para()
    world.say(f"Then {a.id} looked up and apologized right away.")
    world.say(f"{b.id} nodded, and the two of them started to scrub together with {mess.cleaner}.")
    world.facts["cleaning_started"] = True
    propagate(world)
    world.para()
    world.say(f"When the floor was dry, {b.id} made a small surprise: {surprise.phrase}.")
    world.say(f"The surprise turned the long cleanup into a soft smile between them.")
    world.say(f"In the end, {moral.lesson.capitalize()}, and the {mess.label} was gone.")
    a.memes["warmth"] += 1
    b.memes["warmth"] += 1
    world.facts["reconciled"] = True
    world.facts["surprised"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child about a {f["mess"].label} mess, a scrub, and a surprise at {PLACES[f["place"]]}.',
        f"Tell a gentle story where {f['a']} and {f['b']} make a mess, scrub it up together, and end with {f['surprise'].label}.",
        f'Write a simple story that includes the word "scrub" and shows how {f["moral"].lesson}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = world.get(f["a"])
    b = world.get(f["b"])
    mess: MessConfig = f["mess"]
    surprise: SurpriseConfig = f["surprise"]
    moral: MoralConfig = f["moral"]
    place = PLACES[f["place"]]
    qa = [
        QAItem(
            question=f"What happened first at {place}?",
            answer=f"First, {a.id} tipped over {mess.phrase}. That made the table or floor messy and started the problem the two of them had to fix.",
        ),
        QAItem(
            question=f"How did {a.id} and {b.id} fix the mess?",
            answer=f"They apologized and scrubbed together with {mess.cleaner}. Working side by side helped the room become neat again.",
        ),
        QAItem(
            question=f"What surprise did {b.id} give after the cleanup?",
            answer=f"{b.id} brought out {surprise.phrase}. The surprise made the end feel warm instead of tense.",
        ),
        QAItem(
            question=f"What moral value does the story show?",
            answer=f"It shows that {moral.lesson}. The apology, the shared cleaning, and the surprise all point to that lesson.",
        ),
    ]
    if f.get("reconciled"):
        qa.append(QAItem(
            question=f"Why did the mood change after the argument?",
            answer=f"The mood changed because {a.id} said sorry and {b.id} accepted it. Once they scrubbed together, the hurt feelings softened into reconciliation.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does scrub mean?",
            answer="Scrub means to clean something by rubbing it hard, usually with soap, water, or a brush.",
        ),
        QAItem(
            question="Why do people apologize?",
            answer="People apologize to show they know they hurt someone or made a mistake. It helps repair feelings and makes it easier to be friends again.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected. It can be a treat, a note, or a kind action that someone did not know was coming.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Pair, Mess, Surprise, Moral) :- pair(Pair), mess(Mess), surprise(Surprise), moral(Moral), place_for(Pair, Place), place(Place).
reconciled :- apology, scrub.
surprise_ending :- surprise.
moral_value :- moral.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for pid, cfg in PAIRS.items():
        lines.append(asp.fact("pair", pid))
        lines.append(asp.fact("place_for", pid, cfg.shared_place))
    for mid in MESSES:
        lines.append(asp.fact("mess", mid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    lines.append(asp.fact("apology"))
    lines.append(asp.fact("scrub"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH: ASP and Python valid combos differ.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: verify passed with {len(py)} combos.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.pair not in PAIRS or params.mess not in MESSES or params.surprise not in SURPRISES or params.moral not in MORALS:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], PAIRS[params.pair], MESSES[params.mess], SURPRISES[params.surprise], MORALS[params.moral])
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
        print("--- trace ---")
        print(json.dumps(sample.world.history, indent=2, ensure_ascii=False))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", pair="sisters", mess="flour", surprise="cookies", moral="apology"),
    StoryParams(place="porch", pair="brothers", mess="juice", surprise="note", moral="share"),
    StoryParams(place="kitchen", pair="friends", mess="paint", surprise="flowers", moral="help"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
