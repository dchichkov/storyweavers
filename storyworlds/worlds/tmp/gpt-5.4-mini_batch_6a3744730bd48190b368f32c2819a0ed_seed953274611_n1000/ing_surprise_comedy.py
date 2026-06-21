#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ing_surprise_comedy.py
======================================================

A tiny standalone storyworld about a child planning a comic surprise.

Premise
-------
A child prepares a small surprise for someone they love. A little mistake or
unexpected helper makes the plan wobble, but the surprise still lands in a funny,
warm way. The prose leans playful and concrete, and the word "ing" naturally
shows up in the story through action words like "singing," "running," or
"ringing."

This world models:
- typed entities with meters and memes
- a small causal simulation
- a reasonableness gate
- a Python/ASP twin
- prompts, story QA, and world-knowledge QA from world state

It is intentionally self-contained and stdlib-only, except for the shared
Storyweavers result containers and the optional ASP helper.
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
SURPRISE_MIN = 2.0
COMEDY_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    hidden: bool = False
    edible: bool = False
    fragile: bool = False

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "broken": 0.0, "surprise": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "amusement": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Plan:
    id: str
    activity: str
    surprise: str
    cover: str
    tell: str
    reveal: str
    setup: str
    surprise_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    kind: str
    cause: str
    joke: str
    fix: str
    risk: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    hidden_in: str
    reveal_line: str
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("kid")
    if not kid or kid.meters.get("mess", 0.0) < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper = world.entities.get("helper")
    if helper:
        helper.memes["amusement"] += 1
    out.append("__mess__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    plan = world.entities.get("plan")
    gift = world.entities.get("gift")
    if not plan or not gift:
        return out
    if plan.meters.get("surprise", 0.0) < SURPRISE_MIN:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kid = world.entities.get("kid")
    host = world.entities.get("host")
    if kid:
        kid.memes["joy"] += 1
    if host:
        host.memes["joy"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [Rule("mess", "comedy", _r_mess), Rule("surprise", "social", _r_surprise)]


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


def reasonableness(plan: Plan, mishap: Mishap, gift: Gift) -> bool:
    return plan.surprise_kind == "comedy" and mishap.risk >= 1 and bool(gift.hidden_in)


def predict_mishap(world: World, mishap: Mishap) -> bool:
    sim = world.copy()
    sim.get("kid").meters["mess"] += mishap.risk
    propagate(sim, narrate=False)
    return sim.get("kid").meters["mess"] >= THRESHOLD


def do_setup(world: World, kid: Entity, host: Entity, plan: Plan, gift: Gift) -> None:
    kid.memes["pride"] += 1
    host.memes["worry"] += 1
    world.say(
        f"On a bright afternoon, {kid.id} was cooking up a surprise for {host.id}. "
        f"{plan.setup}"
    )
    world.say(
        f'{kid.id} grinned. "{plan.tell} We are planning something {plan.surprise}."'
    )


def do_mishap(world: World, kid: Entity, mishap: Mishap) -> None:
    kid.meters["mess"] += float(mishap.risk)
    kid.memes["amusement"] += 1
    if mishap.kind == "noise":
        world.say(
            f"Right then, {mishap.cause} went {mishap.joke}, and the whole room echoed like a squeaky spoon."
        )
    elif mishap.kind == "mixup":
        world.say(
            f"Then {mishap.cause} made a tiny mix-up, and the plan wobbled like jelly on a plate."
        )
    else:
        world.say(
            f"At the worst possible moment, {mishap.cause} happened, and everybody blinked at once."
        )


def do_warning(world: World, host: Entity, kid: Entity, mishap: Mishap, gift: Gift) -> None:
    if predict_mishap(world, mishap):
        host.memes["worry"] += 1
        world.say(
            f"{host.id} peered over and said, \"If we keep going like this, the surprise might get very funny in a sticky way.\""
        )
        world.say(
            f'Then {host.id} winked and added, "{mishap.fix} before the big reveal."'
        )


def do_reveal(world: World, kid: Entity, host: Entity, plan: Plan, gift: Gift) -> None:
    world.get("plan").meters["surprise"] = 2.0
    world.say(
        f"After the detour, {kid.id} lifted the lid and {gift.reveal_line}."
    )
    world.say(
        f'{host.id} gasped, then laughed so hard {host.pronoun()} almost spilled the tea.'
    )
    world.say(
        f'"A surprise!" {kid.id} said. "And it only got a little sillier on the way."'
    )


def do_end(world: World, kid: Entity, host: Entity, gift: Gift, plan: Plan) -> None:
    kid.memes["joy"] += 1
    host.memes["joy"] += 1
    world.say(
        f"In the end, the table held {gift.phrase}, {kid.id} was smiling, and {host.id} was still laughing at the {plan.activity} part."
    )
    world.say("The surprise arrived late, but it arrived with a giggle.")


def tell(plan: Plan, mishap: Mishap, gift: Gift, kid_name: str = "Mina",
         kid_type: str = "girl", host_name: str = "Auntie", host_type: str = "woman") -> World:
    world = World()
    kid = world.add(Entity(id="kid", kind="character", type=kid_type, label=kid_name))
    host = world.add(Entity(id="host", kind="character", type=host_type, label=host_name))
    plan_ent = world.add(Entity(id="plan", type="plan", label=plan.id, hidden=True))
    gift_ent = world.add(Entity(id="gift", type="gift", label=gift.label, hidden=True))
    helper = world.add(Entity(id="helper", kind="character", type="cat", label="the cat"))
    helper.memes["amusement"] += 0.5

    do_setup(world, kid, host, plan, gift)
    world.para()
    do_mishap(world, kid, mishap)
    do_warning(world, host, kid, mishap, gift)
    if mishap.kind == "noise":
        world.say('A tiny pause hung in the air, and then the cat sneezed like a trumpet.')
    world.para()
    do_reveal(world, kid, host, plan, gift)
    do_end(world, kid, host, gift, plan)

    world.facts.update(kid=kid, host=host, plan=plan_ent, gift=gift_ent, helper=helper,
                       mishap=mishap, gift_cfg=gift, outcome="surprise")
    return world


PLANS = {
    "birthday": Plan(
        id="birthday",
        activity="baking",
        surprise="comic",
        cover="tea towel",
        tell="Shh",
        reveal="surprise",
        setup="A paper hat, a lopsided cake, and one very serious spoon were lined up on the counter.",
        surprise_kind="comedy",
        tags={"cake", "comic", "birthday"},
    ),
    "welcome": Plan(
        id="welcome",
        activity="crafting",
        surprise="friendly",
        cover="box",
        tell="Quietly",
        reveal="ta-da",
        setup="There were crayons, ribbons, and a crooked sign that said WELCOME in sparkly letters.",
        surprise_kind="comedy",
        tags={"craft", "welcome"},
    ),
}

MISHAPS = {
    "cat": Mishap(
        id="cat",
        kind="noise",
        cause="the cat leaping onto the chair",
        joke="meow",
        fix="move the chair away from the cat",
        risk=1,
        tags={"cat", "noise"},
    ),
    "frosting": Mishap(
        id="frosting",
        kind="mixup",
        cause="the frosting bowl tipping",
        joke="plop",
        fix="set the bowl down carefully",
        risk=2,
        tags={"cake", "mess"},
    ),
    "balloon": Mishap(
        id="balloon",
        kind="noise",
        cause="the balloon rubbing the wall",
        joke="ping",
        fix="hold the balloon with two hands",
        risk=1,
        tags={"balloon", "noise"},
    ),
}

GIFTS = {
    "cake": Gift(
        id="cake",
        label="cake",
        phrase="a lopsided chocolate cake",
        hidden_in="the oven",
        reveal_line="there was the cake, tilted proudly on a plate with a wobbling candle on top",
        tags={"cake"},
    ),
    "sign": Gift(
        id="sign",
        label="sign",
        phrase="a sparkly welcome sign",
        hidden_in="the hall closet",
        reveal_line="there was the sign, glittering from ear to ear on the wall",
        tags={"welcome"},
    ),
}

CURATED = [
    StoryParams(plan="birthday", mishap="frosting", gift="cake", kid_name="Mina", kid_type="girl",
                host_name="Auntie", host_type="woman", seed=None),
    StoryParams(plan="welcome", mishap="cat", gift="sign", kid_name="Theo", kid_type="boy",
                host_name="Grandpa", host_type="man", seed=None),
]


@dataclass
class StoryParams:
    plan: str
    mishap: str
    gift: str
    kid_name: str
    kid_type: str
    host_name: str
    host_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLANS:
        for m in MISHAPS:
            for g in GIFTS:
                combos.append((p, m, g))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy surprise storyworld.")
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--kid-name")
    ap.add_argument("--kid-type", choices=["girl", "boy"])
    ap.add_argument("--host-name")
    ap.add_argument("--host-type", choices=["woman", "man"])
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
              if (args.plan is None or c[0] == args.plan)
              and (args.mishap is None or c[1] == args.mishap)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    plan, mishap, gift = rng.choice(sorted(combos))
    return StoryParams(
        plan=plan,
        mishap=mishap,
        gift=gift,
        kid_name=args.kid_name or rng.choice(["Mina", "Theo", "Ruby", "Finn"]),
        kid_type=args.kid_type or rng.choice(["girl", "boy"]),
        host_name=args.host_name or rng.choice(["Auntie", "Grandpa", "Uncle Pat", "Mom"]),
        host_type=args.host_type or rng.choice(["woman", "man"]),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    plan = f["plan"].label
    mishap = f["mishap"].id
    gift = f["gift_cfg"].label
    return [
        f"Write a funny surprise story that includes a {plan} plan and the word 'ing'.",
        f"Tell a comedy where {f['kid'].id} prepares a surprise, gets interrupted by {mishap}, and still reveals {gift}.",
        "Write a child-friendly story with a warm surprise, a small mishap, and a laugh at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid, host, mishap, gift = f["kid"], f["host"], f["mishap"], f["gift_cfg"]
    return [
        (
            "Who was the surprise for?",
            f"It was for {host.label_word}. The whole plan was meant to make {host.label_word} laugh and feel loved.",
        ),
        (
            "What went wrong?",
            f"{mishap.cause} interrupted the plan. It made the room noisier or messier for a moment, which turned the scene into a comedy.",
        ),
        (
            "How did the story end?",
            f"The surprise was still revealed, and {gift.phrase} was the big finish. The mix-up became part of the joke instead of ruining the day.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a surprise?",
            "A surprise is something hidden until the right moment, so someone can feel excited when it is revealed.",
        ),
        (
            "Why can a small mistake be funny in a story?",
            "A small mistake can be funny when nobody gets hurt and the characters laugh together afterward.",
        ),
        (
            "What does a helper cat add to a comedy story?",
            "A helper cat can make a scene sillier by showing up at the wrong time, which adds a playful twist.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
combo(P,M,G) :- plan(P), mishap(M), gift(G).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for p in PLANS:
        lines.append(asp.fact("plan", p))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in ASP gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    plan = PLANS[params.plan]
    mishap = MISHAPS[params.mishap]
    gift = GIFTS[params.gift]
    world = tell(plan, mishap, gift, params.kid_name, params.kid_type, params.host_name, params.host_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for p, m, g in asp_valid_combos():
            print(f"  {p} {m} {g}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
