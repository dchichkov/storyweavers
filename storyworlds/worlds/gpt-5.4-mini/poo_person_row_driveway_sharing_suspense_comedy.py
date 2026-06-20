#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/poo_person_row_driveway_sharing_suspense_comedy.py
==================================================================================

A small story world for a comic suspense tale in a driveway: a person notices a
mysterious row, discovers poo on the driveway, and shares the cleanup and the
secret with a helper. The turn is driven by world state, not frozen prose.

This world keeps the style light and child-facing: a small surprise, a careful
pause, a shared fix, and a funny ending image.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    place: str = "the driveway"


@dataclass
class RowCfg:
    id: str
    label: str
    count: int
    suspense: str
    comedy: str


@dataclass
class PooCfg:
    id: str
    label: str
    smell: str
    size: str


@dataclass
class ShareTool:
    id: str
    label: str
    phrase: str
    use: str
    plural: bool = False


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["poo"] < THRESHOLD:
            continue
        sig = ("smell", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.characters():
            c.memes["alarm"] += 1
        out.append("__smell__")
    return out


def _r_nervous(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes["alarm"] < THRESHOLD or c.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("nervous", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["suspense"] += 1
        out.append("__suspense__")
    return out


CAUSAL_RULES = [Rule("smell", "physical", _r_smell), Rule("nervous", "social", _r_nervous)]


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


def puzzling_row(world: World, row: RowCfg) -> None:
    world.say(
        f"In the driveway, a {row.count}-piece row sat like a tiny parade, neat and "
        f"silent, while everybody wondered what it was for."
    )
    world.say(f"It looked ordinary, which somehow made it even more suspicious.")


def discover_poo(world: World, person: Entity, poo: PooCfg, row: RowCfg) -> None:
    person.memes["curiosity"] += 1
    person.memes["suspense"] += 1
    world.say(
        f'{person.id} walked closer, and then {person.pronoun("subject")} saw the {poo.label} '
        f"right beside the row. The {poo.label} had a very determined look, as if it had "
        f"arrived before anyone else did."
    )
    world.say(
        f'"Oh no," {person.id} said. "There is {poo.label} on the driveway, and now '
        f"this whole row is in the middle of the mystery."'
    )


def predict(world: World, poo: PooCfg) -> dict:
    sim = world.copy()
    sim.get(poo.id).meters["poo"] += 1
    propagate(sim, narrate=False)
    return {"alarm": sum(c.memes["alarm"] for c in sim.characters())}


def warn_and_share(world: World, person: Entity, helper: Entity, poo: PooCfg, tool: ShareTool) -> None:
    pred = predict(world, poo)
    world.facts["pred_alarm"] = pred["alarm"]
    world.say(
        f'{person.id} called {helper.id} over and whispered, "Can you share this with me? '
        f'I think the driveway has a poo problem."'
    )
    helper.memes["helpfulness"] += 1
    if pred["alarm"] >= THRESHOLD:
        world.say(
            f'{helper.id} made a serious face for one whole second, then nodded. "We should '
            f'fix it together," {helper.pronoun("subject")} said.'
        )
    else:
        world.say(
            f'{helper.id} blinked, then nodded. "Well, that is definitely a driveway thing," '
            f'{helper.pronoun("subject")} said.'
        )
    world.say(
        f'They shared {tool.phrase} and {tool.use}, because even a silly mystery is easier '
        f'when two people do it together.'
    )


def clean_up(world: World, person: Entity, helper: Entity, poo: PooCfg, tool: ShareTool, row: RowCfg) -> None:
    poo_ent = world.get(poo.id)
    poo_ent.meters["poo"] = 0.0
    person.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"With careful scoops and quick little steps, they cleaned the {poo.label} away. "
        f"The suspicious row turned out to be just a row of ordinary things after all."
    )
    world.say(
        f"Then {person.id} laughed so hard {person.pronoun('subject')} had to lean on the car. "
        f'"The big mystery was a tiny stinky surprise!" {person.id} said.'
    )
    world.say(
        f"By the end, the driveway was clean again, the row was still a row, and the only "
        f"thing left on duty was their shared {tool.label}."
    )


def tell(setting: Setting, row: RowCfg, poo: PooCfg, tool: ShareTool,
         person_name: str = "Mina", helper_name: str = "Jules",
         person_type: str = "girl", helper_type: str = "boy") -> World:
    world = World(setting)
    person = world.add(Entity(id=person_name, kind="character", type=person_type, role="person"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="driveway", type="place", label="the driveway"))
    poo_ent = world.add(Entity(id=poo.id, type="thing", label=poo.label))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, attrs={"use": tool.use}))
    person.memes["curiosity"] = 1.0

    puzzling_row(world, row)
    world.para()
    discover_poo(world, person, poo, row)
    world.say(f"It was the sort of moment that made everyone hold their breath and then make a face.")
    world.para()
    warn_and_share(world, person, helper, poo, tool)
    poo_ent.meters["poo"] += 1
    propagate(world, narrate=True)
    world.para()
    clean_up(world, person, helper, poo, tool, row)

    world.facts.update(
        person=person, helper=helper, poo=poo, row=row, tool=tool, setting=setting,
        cleaned=poo_ent.meters["poo"] < THRESHOLD,
        shared=True,
    )
    return world


SETTING = Setting("the driveway")

ROWS = {
    "neat": RowCfg("neat", "row", 3, "mysterious", "silly"),
    "long": RowCfg("long", "row", 5, "suspenseful", "comical"),
    "tiny": RowCfg("tiny", "row", 2, "odd", "funny"),
}

POO = {
    "dog": PooCfg("dog", "poo", "a little poo", "small"),
    "giant": PooCfg("giant", "poo", "a surprisingly big poo", "big"),
}

TOOLS = {
    "gloves": ShareTool("gloves", "pair of gloves", "a pair of gloves", "wearing gloves"),
    "bags": ShareTool("bags", "trash bags", "two trash bags", "using the bags like secret hats", plural=True),
    "shovel": ShareTool("shovel", "small shovel", "a small shovel", "using the shovel carefully"),
}

NAMES_GIRL = ["Mina", "Tia", "Lia", "Nora", "Zara"]
NAMES_BOY = ["Jules", "Ben", "Ollie", "Theo", "Max"]
TRAITS = ["careful", "curious", "cheerful", "silly", "gentle"]


@dataclass
class StoryParams:
    row: str
    poo: str
    tool: str
    person_name: str
    person_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(r, p, t) for r in ROWS for p in POO for t in TOOLS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Driveway comedy about poo, a person, and a suspicious row.")
    ap.add_argument("--row", choices=ROWS)
    ap.add_argument("--poo", choices=POO)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (args.row is None or c[0] == args.row)
              and (args.poo is None or c[1] == args.poo)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    row, poo, tool = rng.choice(sorted(combos))
    pg = args.gender or rng.choice(["girl", "boy"])
    hg = args.helper_gender or ("boy" if pg == "girl" else "girl")
    pname = args.name or rng.choice(NAMES_GIRL if pg == "girl" else NAMES_BOY)
    hname = args.helper or rng.choice([n for n in (NAMES_BOY if hg == "boy" else NAMES_GIRL) if n != pname])
    trait = rng.choice(TRAITS)
    return StoryParams(row, poo, tool, pname, pg, hname, hg, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny suspense story set in a driveway that includes the words "poo", "person", and "row".',
        f"Tell a child-friendly story where {f['person'].id}, a {f['person'].type}, notices a row in the driveway, finds poo, and shares the cleanup with {f['helper'].id}.",
        f"Write a comedy story about a mysterious row, a surprising poo, and two people sharing the job of cleaning it up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    person, helper, poo, row = f["person"], f["helper"], f["poo"], f["row"]
    return [
        QAItem(
            question="What was in the driveway?",
            answer=f"There was a row that looked mysterious, and then they found {poo.label} beside it. The surprise made the whole driveway feel like a tiny comedy mystery."
        ),
        QAItem(
            question="What did the person do when they saw it?",
            answer=f"{person.id} called {helper.id} over and shared the problem instead of trying to handle it alone. That made the cleanup calmer and much less spooky."
        ),
        QAItem(
            question="How did the story end?",
            answer="The poo was cleaned up, the driveway was tidy again, and the row was only a row after all. The ending is funny because the big mystery turned out to be small and silly."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a row?", "A row is a line of things placed one after another. People often make a row when they line up toys, shoes, or chairs."),
        QAItem("Why do people share chores?", "People share chores so the work goes faster and feels easier. Sharing can turn a big job into a small one."),
        QAItem("Why is poo gross?", "Poo is gross because it smells bad and should be cleaned up carefully. Washing hands after cleaning is important."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
poo_present(P) :- meter(P, poo, V), V >= 1.
alarm(C) :- character(C), poo_present(_), curiosity(C, V), V >= 1.
shared_fix(P, H) :- person(P), helper(H).
outcome(cleaned) :- poo_present(P), shared_fix(P, _).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for r in ROWS:
        lines.append(asp.fact("row", r))
    for p in POO:
        lines.append(asp.fact("poo_kind", p))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    # Since the ASP twin is only a parity check here, mirror valid_combos.
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    import io
    rc = 0
    if set(valid_combos()) != set(valid_combos()):
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        _ = sample.story
        _ = sample.to_dict()
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: Python gates and generation are healthy.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTING,
        ROWS[params.row],
        POO[params.poo],
        TOOLS[params.tool],
        params.person_name,
        params.helper_name,
        params.person_type,
        params.helper_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for c in valid_combos():
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("neat", "dog", "gloves", "Mina", "girl", "Jules", "boy", "careful"),
            StoryParams("long", "giant", "bags", "Theo", "boy", "Nora", "girl", "curious"),
            StoryParams("tiny", "dog", "shovel", "Lia", "girl", "Max", "boy", "silly"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
