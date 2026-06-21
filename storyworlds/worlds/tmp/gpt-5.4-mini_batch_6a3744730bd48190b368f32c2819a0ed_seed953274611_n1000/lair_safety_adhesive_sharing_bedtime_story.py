#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lair_safety_adhesive_sharing_bedtime_story.py
=============================================================================

A tiny bedtime storyworld about a child discovering a cozy secret lair, learning
about safety, and sharing a sticky adhesive fix with a friend or sibling.

Seed words: lair, safety, adhesive
Feature: Sharing
Style: Bedtime Story

This world is intentionally small and classical:
- A child builds or finds a little lair.
- A loose flap, toy hinge, or paper cut-out needs a safe repair.
- The child has a safe adhesive fix, but it is shared carefully with another kid.
- The ending proves what changed in the world: the lair is snug, tidy, and safe.

The script follows the shared Storyweavers contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify, --show-asp

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
class Lair:
    id: str
    scene: str
    hidey_word: str
    cozy_detail: str
    dark_detail: str
    shared_nest: str


@dataclass
class LooseThing:
    id: str
    label: str
    needs_fix: str
    near: str
    dangerous: bool = False


@dataclass
class Adhesive:
    id: str
    label: str
    phrase: str
    safe_note: str
    strength: int
    shared_ok: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Companion:
    id: str
    type: str
    label: str
    role: str
    traits: list[str] = field(default_factory=list)


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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_safe(world: World) -> list[str]:
    out: list[str] = []
    lair = world.get("lair")
    for thing in world.entities.values():
        if thing.meters["wobbly"] < THRESHOLD:
            continue
        sig = ("safe", thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        lair.meters["at_risk"] += 1
        out.append("__safety__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    if not helper or not child:
        return out
    if child.memes["sharing"] < THRESHOLD:
        return out
    sig = ("share", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] += 1
    child.memes["warmth"] += 1
    out.append("__sharing__")
    return out


CAUSAL_RULES = [
    Rule("safe", "physical", _r_safe),
    Rule("share", "social", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(x for x in items if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sharing_possible(shared: bool, adhesive: Adhesive, companion_role: str) -> bool:
    return shared and adhesive.shared_ok and companion_role in {"sibling", "friend"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for lid, lair in LAIRS.items():
        for tid, thing in LOOSENED.items():
            if thing.dangerous:
                for aid, adh in ADHESIVES.items():
                    if adh.strength >= 1:
                        combos.append((lid, tid, aid))
    return combos


@dataclass
class StoryParams:
    lair: str
    thing: str
    adhesive: str
    child: str
    child_gender: str
    companion: str
    companion_gender: str
    relation: str
    seed: Optional[int] = None


LAIRS = {
    "blanket_fort": Lair(
        id="blanket_fort",
        scene="a sleepy blanket fort",
        hidey_word="lair",
        cozy_detail="pillows made the floor soft and the lamp glowed gold",
        dark_detail="one corner sagged in the dark",
        shared_nest="the little fort felt like a shared nest",
    ),
    "treehouse": Lair(
        id="treehouse",
        scene="a tiny bedtime treehouse",
        hidey_word="lair",
        cozy_detail="a quilt and a lantern made the wood look warm",
        dark_detail="the back wall had a sleepy shadow",
        shared_nest="the little treehouse felt like a shared nest",
    ),
    "cubby": Lair(
        id="cubby",
        scene="a quiet reading cubby",
        hidey_word="lair",
        cozy_detail="stuffed animals guarded the books and the rug was round and soft",
        dark_detail="a side flap kept fluttering open",
        shared_nest="the cubby felt like a shared nest",
    ),
}

LOOSENED = {
    "paper_flap": LooseThing("paper_flap", "paper flap", "stays shut", "near the pillow wall", True),
    "tiny_sign": LooseThing("tiny_sign", "tiny sign", "does not droop", "on the front of the lair", True),
    "ribbon_tie": LooseThing("ribbon_tie", "ribbon tie", "stays tied", "by the curtain loop", False),
}

ADHESIVES = {
    "soft_tape": Adhesive("soft_tape", "soft tape", "a strip of soft tape", "gentle on fingers and easy to peel", 2, tags={"adhesive"}),
    "stickers": Adhesive("stickers", "star stickers", "two star stickers", "bright and safe for little hands", 1, tags={"adhesive"}),
    "glue_dots": Adhesive("glue_dots", "glue dots", "a little pack of glue dots", "just right for a quick repair", 3, tags={"adhesive"}),
}

CHILD_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Eli", "Noah", "Finn"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about a lair, safety, adhesive, and sharing.")
    ap.add_argument("--lair", choices=LAIRS)
    ap.add_argument("--thing", choices=LOOSENED)
    ap.add_argument("--adhesive", choices=ADHESIVES)
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=GENDERS)
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=GENDERS)
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


def explain_rejection(thing: LooseThing, adhesive: Adhesive) -> str:
    return f"(No story: {thing.label} needs a safe fix, but {adhesive.label} does not fit this little bedtime repair.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.adhesive:
        if args.thing not in LOOSENED or args.adhesive not in ADHESIVES:
            raise StoryError("(No story: unknown lair-safety ingredients.)")
        if not valid_combos():
            raise StoryError("(No story: nothing reasonable can happen here.)")
    combos = [c for c in valid_combos()
              if (args.lair is None or c[0] == args.lair)
              and (args.thing is None or c[1] == args.thing)
              and (args.adhesive is None or c[2] == args.adhesive)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    lair, thing, adhesive = rng.choice(sorted(combos))
    gender = args.child_gender or rng.choice(GENDERS)
    child = args.child or rng.choice([n for n in CHILD_NAMES if n != (args.companion or "")])
    companion_gender = args.companion_gender or ("boy" if gender == "girl" else "girl")
    companion = args.companion or rng.choice([n for n in CHILD_NAMES if n != child])
    relation = args.relation or rng.choice(["siblings", "friends"])
    return StoryParams(lair=lair, thing=thing, adhesive=adhesive, child=child, child_gender=gender,
                       companion=companion, companion_gender=companion_gender, relation=relation)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child, role="main"))
    helper = world.add(Entity(id="helper", kind="character", type=params.companion_gender, label=params.companion, role="helper"))
    lair = world.add(Entity(id="lair", type="place", label=LAIRS[params.lair].scene))
    thing = world.add(Entity(id="thing", type="thing", label=LOOSENED[params.thing].label))
    adhesive = world.add(Entity(id="adhesive", type="thing", label=ADHESIVES[params.adhesive].label))

    child.memes["curious"] += 1
    child.memes["sharing"] += 1
    helper.memes["trust"] += 1

    world.say(
        f"At bedtime, {child.label} found {LAIRS[params.lair].scene} tucked behind the blankets. "
        f"{LAIRS[params.lair].cozy_detail}."
    )
    world.say(f"It was a secret {LAIRS[params.lair].hidey_word}, and {LAIRS[params.lair].dark_detail}.")

    world.para()
    world.say(
        f"{child.label} noticed that the {thing.label} did not stay shut. "
        f'"We need safety," {child.label} whispered, "so the little lair can rest."'
    )
    world.say(
        f"{helper.label} nodded, and the two children shared {ADHESIVES[params.adhesive].phrase} '
        f"and {ADHESIVES[params.adhesive].safe_note}."
    )

    thing.meters["wobbly"] += 1
    child.memes["sharing"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(
        f"Together they smoothed the {thing.label} down, pressed the {ADHESIVES[params.adhesive].label} in place, "
        f"and held their breath for a tiny moment."
    )
    thing.meters["fixed"] += 1
    child.memes["safe"] += 1
    helper.memes["safe"] += 1
    world.say(
        f"The repair held. The little {LAIRS[params.lair].hidey_word} stayed neat, "
        f"and {LAIRS[params.lair].shared_nest}."
    )

    world.facts.update(
        child=child,
        helper=helper,
        lair_cfg=LAIRS[params.lair],
        thing_cfg=LOOSENED[params.thing],
        adhesive_cfg=ADHESIVES[params.adhesive],
        repaired=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child that includes the words "lair", "safety", and "adhesive".',
        f"Tell a gentle sharing story where {f['child'].label} and {f['helper'].label} fix a small lair together using adhesive and learn about safety.",
        f"Write a cozy nighttime story about a secret lair, a safe repair, and two children sharing supplies.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    thing = f["thing_cfg"]
    adhesive = f["adhesive_cfg"]
    lair_cfg = f["lair_cfg"]
    return [
        QAItem(
            question="What kind of place did the child find?",
            answer=f"{child.label} found a cozy little lair. It was quiet and secret, like a nest made for bedtime.",
        ),
        QAItem(
            question="Why did they use adhesive?",
            answer=f"They used adhesive to fix the loose {thing.label} so the lair would stay safe. The repair mattered because the little place needed to stay tidy and secure.",
        ),
        QAItem(
            question="How did the children solve the problem together?",
            answer=f"{child.label} and {helper.label} shared {adhesive.phrase} and pressed the loose part into place together. They worked as a team, so the lair became neat again.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {lair_cfg.shared_nest}. The lair stayed snug, the repair held, and both children could rest happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a lair?", "A lair is a hidden place where someone or something likes to rest or hide. In a bedtime story, it can be a cozy secret nest."),
        QAItem("What does safety mean?", "Safety means being careful so nobody gets hurt. It helps a place stay calm, snug, and okay."),
        QAItem("What is adhesive?", "Adhesive is something sticky that helps hold things together. People use it to make small repairs."),
        QAItem("What does sharing mean?", "Sharing means letting someone else use something too. It is kind and helpful when two people solve a problem together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== world questions ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
share_ok(C,H) :- child(C), helper(H), sharing(C), shared_ok(adhesive(A)).
safe_fix(L,T,A) :- lair(L), thing(T), adhesive(A), wobbly(T), share_ok(C,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid in LAIRS:
        lines.append(asp.fact("lair", lid))
    for tid, t in LOOSENED.items():
        lines.append(asp.fact("thing", tid))
        if t.dangerous:
            lines.append(asp.fact("dangerous", tid))
    for aid, a in ADHESIVES.items():
        lines.append(asp.fact("adhesive", aid))
        if a.shared_ok:
            lines.append(asp.fact("shared_ok", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show safe_fix/3.")
    model = asp.one_model(prog)
    return 0 if model is not None else 1


def build_parser_for_asp() -> argparse.ArgumentParser:
    return build_parser()


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def generate(params: StoryParams) -> StorySample:
    if params.lair not in LAIRS or params.thing not in LOOSENED or params.adhesive not in ADHESIVES:
        raise StoryError("(No story: invalid parameters.)")
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


CURATED = [
    StoryParams(lair="blanket_fort", thing="paper_flap", adhesive="soft_tape", child="Mia", child_gender="girl", companion="Noah", companion_gender="boy", relation="friends"),
    StoryParams(lair="treehouse", thing="tiny_sign", adhesive="glue_dots", child="Eli", child_gender="boy", companion="Lily", companion_gender="girl", relation="siblings"),
    StoryParams(lair="cubby", thing="ribbon_tie", adhesive="stickers", child="Ava", child_gender="girl", companion="Finn", companion_gender="boy", relation="friends"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_fix/3."))
        return
    if args.verify:
        # smoke test
        sample = generate(CURATED[0])
        if not sample.story:
            raise SystemExit(1)
        rc = asp_verify()
        sys.exit(rc)
    if args.asp:
        print("\n".join(f"{a} {b} {c}" for a, b, c in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
