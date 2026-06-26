#!/usr/bin/env python3
"""
A tiny bedtime-story world about a child, a lie, and reconciliation.

Seed inspiration:
- A child tells a lie to avoid trouble.
- The lie is classified as a lie when the parent notices the facts.
- The child feels sorry, tells the truth, and reconciliation follows.
- The ending should feel gentle and safe, like a bedtime story.

This script models a small simulated family scene with physical meters and
emotional memes, then turns the state change into prose and QA.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    child: str
    parent: str
    object: str
    lie: str
    seed: Optional[int] = None


@dataclass
class Setting:
    name: str
    bedtime_detail: str


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    kind: str
    easy_to_spot: bool = True


SETTINGS = {
    "bedroom": Setting(name="the bedroom", bedtime_detail="The lamp made a warm little circle on the wall."),
    "hallway": Setting(name="the hallway", bedtime_detail="The hallway was quiet, with sleepy shadows on the rug."),
    "nursery": Setting(name="the nursery", bedtime_detail="The nursery smelled like clean blankets and sleepy air."),
}

OBJECTS = {
    "cookie": ObjectCfg(label="cookie", phrase="a crumbly cookie on the table", kind="snack"),
    "cup": ObjectCfg(label="cup", phrase="a blue cup with milk in it", kind="dish"),
    "book": ObjectCfg(label="book", phrase="a picture book with a torn page", kind="book"),
}

CHILDREN = ["Mia", "Noah", "Lily", "Ben", "Zoe", "Theo"]
PARENTS = ["mom", "dad"]
LIE_WORDS = {
    "cookie": "I did not take the cookie",
    "cup": "The cup was already broken",
    "book": "I never opened the book",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class WorldError(StoryError):
    pass


def classify_claim(world: World, child: Entity, obj: Entity, claimed_truth: bool) -> str:
    """
    Classify the child's statement as truthful or lying based on the world facts.
    """
    world.facts["claim_classification"] = "truth" if claimed_truth else "lie"
    if claimed_truth:
        child.memes["relief"] = child.memes.get("relief", 0) + 1
        return f"{child.id}'s words matched the facts, so the parent classified them as true."
    child.memes["fear"] = child.memes.get("fear", 0) + 1
    child.memes["guilt"] = child.memes.get("guilt", 0) + 1
    return f"{child.id}'s words did not match the facts, so the parent classified them as a lie."


def reconciliation(world: World, child: Entity, parent: Entity, obj: Entity) -> None:
    child.memes["guilt"] = max(0.0, child.memes.get("guilt", 0) - 1)
    child.memes["love"] = child.memes.get("love", 0) + 1
    parent.memes["softness"] = parent.memes.get("softness", 0) + 1
    world.facts["reconciled"] = True
    world.say(
        f"{child.id} whispered sorry, and {parent.pronoun('subject').capitalize()} "
        f"sat beside {child.pronoun('object')} on the bed."
    )
    world.say(
        f"Together they cleaned the {obj.label}, and the room felt calm again."
    )
    world.say(
        f"At last, {child.id} and {parent.pronoun('subject')} had reconciliation, "
        f"like a blanket pulled gently up to the chin."
    )


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise WorldError(f"Unknown setting: {params.setting}")
    if params.object not in OBJECTS:
        raise WorldError(f"Unknown object: {params.object}")

    setting = SETTINGS[params.setting]
    obj_cfg = OBJECTS[params.object]

    world = World(setting=setting.name)
    child = world.add(Entity(id=params.child, kind="character", type="girl" if params.child in {"Mia", "Lily", "Zoe"} else "boy"))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent))
    obj = world.add(Entity(id="object", type=obj_cfg.kind, label=obj_cfg.label, phrase=obj_cfg.phrase, caretaker=parent.id))

    # physical / emotional baseline
    child.meters["sleepy"] = 1.0
    child.memes["nervous"] = 1.0
    parent.memes["care"] = 1.0

    # Story beat 1: bedtime setup
    world.say(f"It was bedtime in {setting.name}.")
    world.say(setting.bedtime_detail)
    world.say(f"{child.id} was small and sleepy, but {child.id} had a secret.")

    # Story beat 2: lie and classification
    world.para()
    world.say(f"When {parent.id} asked about the {obj.label}, {child.id} said, “{params.lie}.”")
    world.say(
        f"But the {obj.label} was right there in the room, so the parent could classify the sentence as a lie."
    )
    classify_claim(world, child, obj, claimed_truth=False)

    # Story beat 3: turn toward reconciliation
    world.para()
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"{child.id}'s cheeks felt hot. The lie made the room feel heavy, and sleep would not come."
    )
    world.say(f"Then {child.id} took a deep breath and told the truth about the {obj.label}.")
    world.say(f"{parent.id} did not shout. {parent.id} only opened {parent.pronoun('possessive')} arms.")

    # Story beat 4: reconciliation
    world.para()
    reconciliation(world, child, parent, obj)

    world.facts.update(
        child=child,
        parent=parent,
        obj=obj,
        lie_text=params.lie,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a gentle bedtime story about a child who tells a lie and then finds reconciliation.',
        f"Tell a short story set in {f['setting'].name} where {f['child'].id} lies about a {f['obj'].label}, then tells the truth.",
        f"Write a child-friendly story using the words 'classify', 'liar', and 'reconciliation'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    obj: Entity = f["obj"]
    return [
        QAItem(
            question=f"What did {child.id} lie about at bedtime?",
            answer=f"{child.id} lied about the {obj.label}. The {obj.label} was still in the room, so the lie could be noticed."
        ),
        QAItem(
            question=f"How did the parent classify {child.id}'s statement?",
            answer=f"The parent classified it as a lie because the facts in the room did not match {child.id}'s words."
        ),
        QAItem(
            question=f"What changed after {child.id} told the truth?",
            answer=f"The heavy feeling went away, and {child.id} and {parent.id} reached reconciliation by cleaning up and sitting together."
        ),
        QAItem(
            question=f"Why did the story end quietly?",
            answer=f"It ended quietly because bedtime was near, the truth was told, and reconciliation made the room calm again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and feel close after the problem is fixed."
        ),
        QAItem(
            question="What is a liar?",
            answer="A liar is a person who says something that is not true."
        ),
        QAItem(
            question="What does classify mean?",
            answer="To classify means to sort or name something by what it is, like calling a statement a truth or a lie."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/3.
#show claim_classification/1.

valid_story(S, O, C) :- setting(S), object(O), child(C).
claim_classification(lie) :- liar_word.
claim_classification(truth) :- truthful_word.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for cname in CHILDREN:
        lines.append(asp.fact("child", cname))
    for p in PARENTS:
        lines.append(asp.fact("parent", p))
    lines.append(asp.fact("liar_word"))
    lines.append(asp.fact("truthful_word"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    triples = set(asp.atoms(model, "valid_story"))
    expected = {(s, o, c) for s in SETTINGS for o in OBJECTS for c in CHILDREN}
    if triples == expected:
        print(f"OK: ASP valid_story matches Python registry ({len(triples)} stories).")
        return 0
    print("MISMATCH between ASP and Python registries.")
    print("only in ASP:", sorted(triples - expected))
    print("only in Python:", sorted(expected - triples))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, o) for s in SETTINGS for c in CHILDREN for o in OBJECTS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime-story world about lies, truth, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--lie", choices=list(LIE_WORDS.values()))
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
    setting = args.setting or rng.choice(list(SETTINGS))
    child = args.child or rng.choice(CHILDREN)
    parent = args.parent or rng.choice(PARENTS)
    obj = args.object or rng.choice(list(OBJECTS))
    lie = args.lie or LIE_WORDS[obj]
    if args.lie and args.object and args.lie != LIE_WORDS[args.object]:
        raise StoryError("The chosen lie does not fit the chosen object.")
    return StoryParams(setting=setting, child=child, parent=parent, object=obj, lie=lie)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible stories")
        for t in triples[:20]:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(StoryParams(setting=s, child=c, parent=p, object=o, lie=LIE_WORDS[o]))
                   for s, c, o in valid_combos()
                   for p in PARENTS[:1]]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        for i in range(max(args.n * 40, 40)):
            if len(samples) >= args.n:
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
