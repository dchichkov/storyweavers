#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/natural_flashback_inner_monologue_moral_value_heartwarming.py
==============================================================================================

A small heartwarming storyworld about a child, a natural gift, a brief flashback,
an inner monologue, and a gentle moral value choice.

Premise
-------
A child is making a little gift from natural things from the garden. Something
goes wrong, they remember a kind moment from earlier, think through what matters,
and choose a caring fix. The ending should feel warm, concrete, and changed by
the choice.

This world keeps a tiny simulation:
- typed entities with physical meters and emotional memes
- a simple forward causal rule
- a reasonableness gate
- story-grounded QA, prompt QA, and world-knowledge QA
- an inline ASP twin for parity checks

The story aims for a tender, child-facing tone with a clear beginning, middle
turn, and ending image.
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
    tags: set[str] = field(default_factory=set)
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
class GardenThing:
    id: str
    label: str
    kind: str
    natural: bool = False
    fragile: bool = False
    helps: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralChoice:
    id: str
    value: str
    fix: str
    success_text: str
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    thing: str
    choice: str
    seed: Optional[int] = None


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wilt(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["damaged"] < THRESHOLD:
            continue
        sig = ("wilt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in [x for x in world.entities.values() if x.role == "child"]:
            kid.memes["worry"] += 1
        out.append("__wilt__")
    return out


CAUSAL_RULES = [Rule("wilt", "physical", _r_wilt)]


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


def valid_choice(choice: MoralChoice, thing: GardenThing) -> bool:
    return choice.id in CHOICES and thing.id in THINGS and thing.fragile


def chosen_fix(choice: MoralChoice, thing: GardenThing) -> bool:
    return choice.value in {"share", "apologize", "carefully_repair"} and thing.fragile


def tell(choice: MoralChoice, thing: GardenThing, child_name: str, child_gender: str,
         parent_name: str, parent_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    item = world.add(Entity(id=thing.id, kind="thing", type="thing", label=thing.label, tags=set(thing.tags)))
    child.memes["hope"] = 1.0
    child.memes["care"] = 1.0

    world.say(
        f"On a soft afternoon, {child.id} walked into the garden and gathered {thing.label}. "
        f"{thing.helps.capitalize()}."
    )
    world.say(
        f"{child.id} wanted to make something beautiful and natural, because small natural things "
        f"could feel like a treasure when they were picked with care."
    )

    world.para()
    world.say(
        f"Then {child.id} reached too quickly, and {thing.label} got bumped and damaged a little."
    )
    item.meters["damaged"] += 1
    propagate(world, narrate=False)

    world.say(
        f"{child.id} froze. {child.pronoun().capitalize()} looked at the broken piece and had a quiet thought."
    )
    world.say(
        f'"I should fix this," {child.id} thought. "If I hide it, the garden gift will not feel kind anymore."'
    )

    world.para()
    world.say(
        f"A flashback came back to {child.id}: earlier, {parent.id} had shown {child.pronoun("object")} how "
        f"gentle hands can help a plant grow again. {parent.id} had said that caring for natural things "
        f"was part of caring for people too."
    )
    child.memes["memory"] += 1

    if choice.value == "share":
        world.say(
            f'{child.id} listened to that memory and gave the good pieces to {parent.id}. '
            f'"I want to share," {child.id} said softly.'
        )
    elif choice.value == "apologize":
        world.say(
            f'{child.id} took a breath and walked to {parent.id}. '
            f'"I am sorry," {child.id} said. "I hurt it by accident."'
        )
    else:
        world.say(
            f'{child.id} fetched a little string and carefully lined the pieces back together. '
            f"{child.id}'s hands moved slowly, as if {child.id} were trying to help the whole garden breathe easier."
        )

    world.say(
        f"Inside, {child.id}'s inner voice kept whispering: {choice.fix}."
    )
    child.memes["resolve"] += 1

    world.para()
    if chosen_fix(choice, thing):
        parent.memes["warmth"] += 1
        child.memes["relief"] += 1
        item.meters["damaged"] = 0.0
        world.say(
            f"{parent.id} smiled, knelt beside {child.id}, and helped finish the work. "
            f"Together they made the little natural gift tidy again."
        )
        world.say(
            f"At the end, the garden looked calm and green, and {child.id} held the repaired gift with a careful grin."
        )
    else:
        item.meters["damaged"] += 1
        world.say(
            f"{parent.id} noticed the trouble and helped {child.id} fix it slowly, because a kind choice was worth more than a quick one."
        )
        world.say(
            f"By the end, {child.id} understood that natural things need gentle hands, and the room felt peaceful again."
        )

    world.facts.update(
        child=child,
        parent=parent,
        thing=item,
        thing_cfg=thing,
        choice=choice,
        outcome="fixed" if item.meters["damaged"] < THRESHOLD else "mended",
    )
    return world


THINGS = {
    "flowers": GardenThing(
        id="flowers",
        label="a small bunch of wildflowers",
        kind="bouquet",
        natural=True,
        fragile=True,
        helps="Their soft petals made the air smell sweet",
        tags={"natural", "flowers"},
    ),
    "leaves": GardenThing(
        id="leaves",
        label="a pile of bright leaves",
        kind="bundle",
        natural=True,
        fragile=True,
        helps="Their colors looked like tiny painted hands",
        tags={"natural", "leaves"},
    ),
    "shells": GardenThing(
        id="shells",
        label="a little basket of shells",
        kind="basket",
        natural=True,
        fragile=True,
        helps="Their tiny curves made a gentle clinking sound",
        tags={"natural", "shells"},
    ),
}

CHOICES = {
    "share": MoralChoice(
        id="share",
        value="share",
        fix="The kind thing is to share what we found",
        success_text="shared the natural gift and smiled",
        fail_text="tried to keep it secret, but that felt wrong",
        qa_text="shared the gentle pieces instead of hiding them",
        tags={"moral", "share"},
    ),
    "apologize": MoralChoice(
        id="apologize",
        value="apologize",
        fix="A true apology can make a broken moment softer",
        success_text="apologized and helped make it right",
        fail_text="stayed quiet and let the worry grow",
        qa_text="said sorry and helped fix the mistake",
        tags={"moral", "apologize"},
    ),
    "repair": MoralChoice(
        id="repair",
        value="carefully_repair",
        fix="Careful hands can repair what was hurt by accident",
        success_text="carefully repaired the broken piece",
        fail_text="handled it too fast and made it worse",
        qa_text="carefully repaired the natural thing",
        tags={"moral", "repair"},
    ),
}

NAMES = ["Mia", "Lena", "Noah", "Eli", "Ava", "Nina", "Theo", "Rose"]


def valid_combos() -> list[tuple[str, str]]:
    return [(t, c) for t in THINGS for c in CHOICES if THINGS[t].fragile]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story for a young child that includes the word "natural" and a gentle moral choice.',
        f"Tell a story where {f['child'].id} finds {f['thing_cfg'].label}, remembers a kind lesson, and chooses to do the right thing.",
        f"Write a soft story with a flashback and inner monologue about caring for natural things.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    thing = f["thing_cfg"]
    choice = f["choice"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {parent.id}, with a small natural thing from the garden at the center of the story."),
        ("What happened to the natural thing?",
         f"{thing.label} got bumped and damaged by accident. That created the problem that the child had to solve."),
        ("What did {0} think about before acting?".format(child.id),
         f"{child.id} remembered a kind lesson from {parent.id}, and that memory helped {child.id} decide what mattered most."),
    ]
    qa.append((
        "How did the child solve the problem?",
        f"{child.id} {choice.qa_text}. That choice matched the moral value of caring gently for natural things."
    ))
    qa.append((
        "Why was the ending heartwarming?",
        f"{parent.id} helped with patience, and {child.id} learned that kindness matters more than hiding a mistake. The final scene is calm and warm because the child chose honesty and care."
    ))
    return qa


WORLD_KNOWLEDGE = {
    "natural": [
        ("What does natural mean?",
         "Natural means something comes from nature, like plants, leaves, stones, or water, not from a machine or a toy factory.")
    ],
    "flowers": [
        ("Why should you handle flowers gently?",
         "Flowers can bend or bruise easily. Gentle hands help them stay pretty and healthy longer.")
    ],
    "leaves": [
        ("Why do leaves change color?",
         "Leaves change color when a plant gets ready for a new season, and the green part fades so other colors can show.")
    ],
    "shells": [
        ("What are shells?",
         "Shells are the hard outer homes of some sea animals. They often wash up on beaches after the animals grow or move away.")
    ],
    "apology": [
        ("Why is apologizing important?",
         "An apology tells someone you know you hurt them or made a mistake. It can help fix feelings and start trust again.")
    ],
    "share": [
        ("Why is sharing kind?",
         "Sharing lets other people enjoy something too. It shows you care about their happiness, not just your own.")
    ],
}
WORLD_ORDER = ["natural", "flowers", "leaves", "shells", "apology", "share"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["thing_cfg"].tags) | set(world.facts["choice"].tags) | {"natural"}
    out: list[tuple[str, str]] = []
    for key in WORLD_ORDER:
        if key in tags and key in WORLD_KNOWLEDGE:
            out.extend(WORLD_KNOWLEDGE[key])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(thing: GardenThing, choice: MoralChoice) -> str:
    return (
        f"(No story: the combination of {thing.label} and the choice '{choice.id}' "
        f"does not make a reasonable gentle problem to solve.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.natural:
            lines.append(asp.fact("natural", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("value", cid, c.value))
    lines.append(asp.fact("threshold", int(THRESHOLD)))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T, C) :- thing(T), choice(C), natural(T), fragile(T).
reasonably_kind(C) :- choice(C), value(C, share).
reasonably_kind(C) :- choice(C), value(C, apologize).
reasonably_kind(C) :- choice(C), value(C, carefully_repair).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable_choices() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonably_kind/1."))
    return sorted(c for (c,) in asp.atoms(model, "reasonably_kind"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP valid combos match Python ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    if set(asp_reasonable_choices()) == set(CHOICES):
        print("OK: ASP reasonable choices match.")
    else:
        rc = 1
        print("MISMATCH: ASP reasonable choices differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        _ = sample.to_json()
        print("OK: default generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"MISMATCH: generation smoke test failed: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world about a natural thing, a flashback, "
                    "an inner monologue, and a gentle moral choice."
    )
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent")
    ap.add_argument("--parent-gender", choices=["mother", "father"])
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
    thing = args.thing or rng.choice(sorted(THINGS))
    choice = args.choice or rng.choice(sorted(CHOICES))
    if thing not in THINGS or choice not in CHOICES:
        raise StoryError("Unknown thing or choice.")
    if not valid_choice(CHOICES[choice], THINGS[thing]):
        raise StoryError(explain_rejection(THINGS[thing], CHOICES[choice]))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    parent_gender = args.parent_gender or rng.choice(["mother", "father"])
    child = args.child or rng.choice(NAMES)
    parent = args.parent or rng.choice([n for n in NAMES if n != child])
    return StoryParams(
        child=child,
        child_gender=child_gender,
        parent=parent,
        parent_gender=parent_gender,
        thing=thing,
        choice=choice,
    )


def generate(params: StoryParams) -> StorySample:
    if params.child_gender not in {"girl", "boy"} or params.parent_gender not in {"mother", "father"}:
        raise StoryError("Invalid genders.")
    thing = THINGS.get(params.thing)
    choice = CHOICES.get(params.choice)
    if thing is None or choice is None:
        raise StoryError("Unknown params.")
    world = tell(choice, thing, params.child, params.child_gender, params.parent, params.parent_gender)
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


CURATED = [
    StoryParams(child="Mia", child_gender="girl", parent="Mom", parent_gender="mother", thing="flowers", choice="share"),
    StoryParams(child="Noah", child_gender="boy", parent="Dad", parent_gender="father", thing="leaves", choice="apologize"),
    StoryParams(child="Ava", child_gender="girl", parent="Mom", parent_gender="mother", thing="shells", choice="repair"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show reasonably_kind/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t, c in combos:
            print(f"  {t:10} {c}")
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
