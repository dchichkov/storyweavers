#!/usr/bin/env python3
"""
storyworlds/worlds/skirt_payment_reconciliation_quest_nursery_rhyme.py
======================================================================

A small, standalone storyworld about a missing skirt payment, a little quest,
and a reconciliation that ends in a nursery-rhyme-like scene.

The world is intentionally compact: one child makes a promise, a helper seeks a
missing payment, tension grows when a skirt is delayed, and a gentle ending
restores trust. The prose is state-driven, with physical meters and emotional
memes changing the story as it unfolds.

Includes:
- skirt
- payment
- Reconciliation
- Quest
- nursery-rhyme style rhythm

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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carrier: Optional[str] = None
    promised_for: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "tailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    fancy: bool = False
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    errand: str
    trail: str
    return_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Payment:
    id: str
    label: str
    phrase: str
    amount: int
    owed_to: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def children(self) -> list[Entity]:
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        child = world.facts["child"]
        tailor = world.facts["tailor"]
        skirt = world.facts["skirt"]
        pay = world.facts["payment"]
        if child.memes["worry"] >= THRESHOLD and pay.meters["missing"] >= THRESHOLD:
            sig = ("dull", "tension")
            if sig not in world.fired:
                world.fired.add(sig)
                child.memes["sadness"] += 1
                tailor.memes["guilt"] += 1
                out.append("The little bell grew sad and small.")
                changed = True
        if pay.meters["found"] >= THRESHOLD and child.memes["worry"] >= THRESHOLD:
            sig = ("mend", "reconcile")
            if sig not in world.fired:
                world.fired.add(sig)
                child.memes["trust"] += 1
                tailor.memes["love"] += 1
                child.memes["worry"] = 0
                out.append("The worry unknotted like yarn.")
                changed = True
        if skirt.meters["ready"] >= THRESHOLD and pay.meters["found"] >= THRESHOLD:
            sig = ("bright", "finish")
            if sig not in world.fired:
                world.fired.add(sig)
                skirt.meters["worn"] += 1
                out.append("The skirt was ready to twirl.")
                changed = True
    if narrate:
        for line in out:
            world.say(line)
    return out


SETTINGS = {
    "market": Setting(place="the little market", indoors=False, weather="breezy", affords={"quest"}),
    "porch": Setting(place="the porch by the lanes", indoors=False, weather="soft rain", affords={"quest"}),
    "parlor": Setting(place="the warm parlor", indoors=True, weather="still", affords={"quest"}),
}

QUESTS = {
    "find_payment": Quest(
        id="find_payment",
        goal="find the missing payment",
        errand="follow the penny trail",
        trail="a trail of buttons and breadcrumbs",
        return_line="bring the payment home",
        tags={"quest", "payment"},
    ),
    "mend_trade": Quest(
        id="mend_trade",
        goal="make peace with the seamstress",
        errand="carry a note and a ribbon",
        trail="a path past the well and the willow",
        return_line="say sorry and settle the bill",
        tags={"quest", "reconciliation", "payment"},
    ),
}

SKIRTS = {
    "red": Item("red", "a red skirt", "a red skirt", "waist", fancy=True, tags={"skirt"}),
    "blue": Item("blue", "a blue skirt", "a blue skirt", "waist", fancy=False, tags={"skirt"}),
    "striped": Item("striped", "a striped skirt", "a striped skirt", "waist", fancy=True, tags={"skirt"}),
}

PAYMENTS = {
    "coin_pouch": Payment("coin_pouch", "a coin pouch", "a small coin pouch", 3, "tailor", tags={"payment"}),
    "silver_token": Payment("silver_token", "a silver token", "a silver token", 1, "tailor", tags={"payment"}),
    "ribbon_due": Payment("ribbon_due", "a ribbon due", "a ribbon payment", 2, "tailor", tags={"payment"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Tess", "Mabel", "June"]
TAILOR_NAMES = ["Mrs. Bell", "Mr. Finch", "Aunt Rose"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    skirt: str
    payment: str
    child_name: str
    tailor_name: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for quest in QUESTS:
            for skirt in SKIRTS:
                for payment in PAYMENTS:
                    combos.append((setting, quest, skirt, payment))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld of a skirt, a payment, and a quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--skirt", choices=SKIRTS)
    ap.add_argument("--payment", choices=PAYMENTS)
    ap.add_argument("--name")
    ap.add_argument("--tailor-name")
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
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.skirt is None or c[2] == args.skirt)
              and (args.payment is None or c[3] == args.payment)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, skirt, payment = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        skirt=skirt,
        payment=payment,
        child_name=args.name or rng.choice(GIRL_NAMES),
        tailor_name=args.tailor_name or rng.choice(TAILOR_NAMES),
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS.get(params.setting)
    quest = QUESTS.get(params.quest)
    skirt = SKIRTS.get(params.skirt)
    payment = PAYMENTS.get(params.payment)
    if setting is None or quest is None or skirt is None or payment is None:
        raise StoryError("Unknown story parameter.")
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type="girl", label=params.child_name))
    tailor = world.add(Entity(id="tailor", kind="character", type="tailor", label=params.tailor_name))
    skirt_e = world.add(Entity(id="skirt", type="garment", label=skirt.label, phrase=skirt.phrase, plural=skirt.plural))
    pay_e = world.add(Entity(id="payment", type="payment", label=payment.label, phrase=payment.phrase))
    world.facts["child"] = child
    world.facts["tailor"] = tailor
    world.facts["skirt"] = skirt_e
    world.facts["payment"] = pay_e
    world.facts["quest"] = quest
    world.facts["setting"] = setting
    child.memes["hope"] = 1
    child.memes["worry"] = 0
    tailor.memes["care"] = 1
    pay_e.meters["missing"] = 1
    skirt_e.meters["ready"] = 0
    world.say(f"{params.child_name} lived by the {setting.place}, with a skirt to wear and a payment to pay.")
    world.say(f"Little {params.child_name} went on a quest to {quest.goal}, treading a light and merry way.")
    world.para()
    child.memes["worry"] += 1
    world.say(f"But the {payment.label} went missing, and the skirt was waiting still.")
    world.say(f"{params.child_name} followed {quest.errand}, through {quest.trail}, up and over the hill.")
    world.para()
    pay_e.meters["found"] += 1
    pay_e.meters["missing"] = 0
    skirt_e.meters["ready"] += 1
    world.say(f"At last the payment was found, and the little skirt could settle and twirl.")
    if quest.id == "mend_trade":
        child.memes["worry"] += 1
        world.say(f"{params.child_name} took the note to {params.tailor_name}, and asked for peace with a curl.")
    propagate(world, narrate=True)
    world.para()
    child.memes["joy"] += 1
    tailor.memes["love"] += 1
    world.say(f"{params.child_name} and {params.tailor_name} smiled, and the day went bright as pearl.")
    world.say(f"The skirt stayed neat, the payment was made, and the whole little quest came full circle.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["child"]
    q = f["quest"]
    return [
        f"Write a nursery-rhyme story about {p.label} who must {q.goal} and keep a skirt ready.",
        f"Tell a gentle quest tale where a payment goes missing, then comes back, and the skirt can be worn.",
        f"Write a short rhyme about a child, a tailor, a payment, and a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    tailor = f["tailor"]
    quest = f["quest"]
    skirt = f["skirt"]
    payment = f["payment"]
    return [
        QAItem(
            question=f"What was {child.label} trying to do in the story?",
            answer=f"{child.label} was trying to {quest.goal}. The quest mattered because the skirt and the payment were part of the same little errand.",
        ),
        QAItem(
            question=f"Why did the story feel tense when the payment went missing?",
            answer=f"The payment was needed to settle the matter, so its loss made {child.label} worry. That worry also made the skirt feel delayed, like a promise waiting to be kept.",
        ),
        QAItem(
            question=f"How did {child.label} and {tailor.label} make things right?",
            answer=f"They found the payment and spoke kindly, so they could reconcile. That peaceful talk let the skirt be ready at the end, and the trouble came unstuck.",
        ),
        QAItem(
            question=f"What changed about the skirt by the end?",
            answer=f"The skirt was ready and neat, not waiting anymore. It became part of the happy ending because the payment had been found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a skirt?",
            answer="A skirt is a piece of clothing that hangs from the waist and can swish when someone walks or twirls.",
        ),
        QAItem(
            question="What is a payment?",
            answer="A payment is money or something given to settle what is owed. It helps make a promise complete.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after trouble. People listen, forgive, and try to be friends once more.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a little journey with a goal. Someone goes out to find, fix, or bring something back.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
ready(skirt) :- skirt_ready.
missing(payment) :- payment_missing.
reconcile(child, tailor) :- found(payment), said_sorry(child), said_sorry(tailor).
quest_done(child) :- found(payment), ready(skirt), reconcile(child, tailor).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for sid in SKIRTS:
        lines.append(asp.fact("skirt", sid))
    for pid in PAYMENTS:
        lines.append(asp.fact("payment", pid))
    lines.append(asp.fact("skirt_ready"))
    lines.append(asp.fact("payment_missing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show quest_done/1."))
    facts = set(asp.atoms(model, "quest_done"))
    if facts == {("child",)}:
        print("OK: ASP twin is alive.")
    else:
        print("MISMATCH: ASP twin did not derive the expected ending.")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, quest=None, skirt=None, payment=None, name=None, tailor_name=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"FAIL: generate smoke test crashed: {err}")
        return 1
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def build_sample(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
    StoryParams(setting="market", quest="find_payment", skirt="red", payment="coin_pouch", child_name="Mina", tailor_name="Mrs. Bell"),
    StoryParams(setting="porch", quest="mend_trade", skirt="blue", payment="silver_token", child_name="Lily", tailor_name="Aunt Rose"),
    StoryParams(setting="parlor", quest="find_payment", skirt="striped", payment="ribbon_due", child_name="Nora", tailor_name="Mr. Finch"),
]


def resolve_filters(args: argparse.Namespace) -> dict[str, Optional[str]]:
    return {
        "setting": args.setting,
        "quest": args.quest,
        "skirt": args.skirt,
        "payment": args.payment,
    }


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)
              and (args.skirt is None or c[2] == args.skirt)
              and (args.payment is None or c[3] == args.payment)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, quest, skirt, payment = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        quest=quest,
        skirt=skirt,
        payment=payment,
        child_name=args.name or rng.choice(GIRL_NAMES),
        tailor_name=args.tailor_name or rng.choice(TAILOR_NAMES),
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (s, q, sk, p)
        for s in SETTINGS
        for q in QUESTS
        for sk in SKIRTS
        for p in PAYMENTS
    ]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Storyworld: skirt, payment, quest, reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--skirt", choices=SKIRTS)
    ap.add_argument("--payment", choices=PAYMENTS)
    ap.add_argument("--name")
    ap.add_argument("--tailor-name")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest_done/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(f"{x}" for x in asp_valid_combos()))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
