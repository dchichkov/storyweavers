#!/usr/bin/env python3
"""
A folk-tale storyworld about stance, kindness, and an enslaved worker who finds
a way to stand tall again.

The seed premise:
- A slave lives under a harsh master.
- The slave's stance starts low, bowed, and careful.
- A small act of kindness changes the master's heart.
- The ending is happy: freedom, gratitude, and a new upright stance.

This script keeps the world small and constraint-driven:
- physical meters: posture, fatigue, warmth, freedom, etc.
- emotional memes: fear, hope, kindness, guilt, relief, trust
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {"posture": 0.0, "fatigue": 0.0, "freedom": 0.0}
        if not self.memes:
            self.memes = {"fear": 0.0, "hope": 0.0, "kindness": 0.0, "guilt": 0.0, "relief": 0.0, "trust": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class TaleWorld:
    castle: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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

    def copy(self) -> "TaleWorld":
        clone = TaleWorld(self.castle)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    castle: str
    hero_name: str
    master_name: str
    helper_name: str
    seed: Optional[int] = None


CASTLES = {
    "old_castle": "the old castle",
    "mill_hall": "the mill hall",
    "river_keep": "the river keep",
}

HERO_NAMES = ["Marek", "Ivo", "Nera", "Suri", "Toma", "Elin"]
MASTER_NAMES = ["Lord Bran", "Lady Vesa", "Sir Orin", "Count Mara"]
HELPER_NAMES = ["Old Hana", "Bela the Baker", "Galen the Gardener", "Mira the Miller"]


def _speak(world: TaleWorld, who: Entity, text: str) -> None:
    world.say(f"{who.id} {text}")


def _applies_kindness(world: TaleWorld, slave: Entity, helper: Entity, master: Entity) -> None:
    if world.fired.__contains__(("kindness",)):
        return
    world.fired.add(("kindness",))
    slave.memes["kindness"] += 1
    slave.memes["hope"] += 1
    helper.memes["kindness"] += 1
    helper.meters["freedom"] += 0.0
    world.say(
        f"{helper.id} brought a warm loaf and spoke softly to {slave.id}, "
        f"as if a gentle word could mend a torn fence."
    )
    world.say(
        f"{slave.id} shared the loaf with {master.id}'s tired little hound, "
        f"and that small kindness loosened the master's hard heart."
    )
    master.memes["guilt"] += 1
    master.memes["trust"] += 1
    world.say(
        f"{master.id} saw the act and grew quiet, for shame can wake even in a stern heart."
    )


def _applies_release(world: TaleWorld, slave: Entity, master: Entity) -> None:
    if world.fired.__contains__(("release",)):
        return
    if master.memes["trust"] < THRESHOLD or master.memes["guilt"] < THRESHOLD:
        return
    world.fired.add(("release",))
    slave.meters["freedom"] += 1
    slave.memes["fear"] = max(0.0, slave.memes["fear"] - 1)
    slave.memes["relief"] += 1
    slave.meters["posture"] += 1
    world.say(
        f"At dawn, {master.id} opened the gate and gave {slave.id} a small key and a fair wage."
    )
    world.say(
        f'"Go in peace," said {master.id}, "for no one should live bowed when kindness can set them upright."'
    )


def propagate(world: TaleWorld, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_applies_kindness, _applies_release):
            before = len(world.fired)
            if fn is _applies_kindness:
                fn(world, world.get("slave"), world.get("helper"), world.get("master"))
            else:
                fn(world, world.get("slave"), world.get("master"))
            if len(world.fired) != before:
                changed = True
        # only narrative is written inline above
    return out


def build_world(params: StoryParams) -> TaleWorld:
    world = TaleWorld(CASTLES[params.castle])
    slave = world.add(Entity(
        id="slave",
        kind="character",
        type="person",
        label="the slave",
        phrase="a weary slave with careful eyes",
        meters={"posture": 0.0, "fatigue": 2.0, "freedom": 0.0},
        memes={"fear": 2.0, "hope": 0.0, "kindness": 0.0, "guilt": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    master = world.add(Entity(
        id="master",
        kind="character",
        type="person",
        label="the master",
        phrase="a stern master of the hall",
        meters={"posture": 1.0, "fatigue": 1.0, "freedom": 1.0},
        memes={"fear": 0.0, "hope": 0.0, "kindness": 0.0, "guilt": 0.0, "relief": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="person",
        label="the helper",
        phrase="a kind neighbor",
        meters={"posture": 1.0, "fatigue": 0.0, "freedom": 1.0},
        memes={"fear": 0.0, "hope": 1.0, "kindness": 2.0, "guilt": 0.0, "relief": 0.0, "trust": 1.0},
    ))
    world.facts["slave"] = slave
    world.facts["master"] = master
    world.facts["helper"] = helper
    return world


def tell_story(world: TaleWorld, params: StoryParams) -> None:
    slave = world.get("slave")
    master = world.get("master")
    helper = world.get("helper")

    world.say(
        f"In {world.castle}, there lived {slave.phrase}, who kept a low stance and learned to move like a shadow."
    )
    world.say(
        f"{slave.id} worked for {master.id}, while {helper.id} often passed by with a nod and a crust of bread."
    )

    world.para()
    slave.meters["posture"] = 0.2
    slave.memes["fear"] = 2.0
    world.say(
        f"Each day, {slave.id} bowed low, for a harsh word could fall like winter rain."
    )
    world.say(
        f"Still, {slave.id} never turned away from a hungry face, because kindness was the one bright thing {slave.id} owned."
    )

    world.para()
    propagate(world)
    slave.meters["fatigue"] += 0.5
    slave.meters["posture"] = 0.6
    world.say(
        f"One evening, {helper.id} slipped {slave.id} a warm loaf and whispered, 'A gentle heart can outshine a dark hall.'"
    )
    world.say(
        f"{slave.id} shared the loaf with {master.id}'s little hound, even though {slave.id} had so little to spare."
    )

    world.para()
    propagate(world)
    slave.meters["posture"] = 1.0
    world.say(
        f"The next morning, {master.id} saw the good deed and felt shame like a stone in {master.pronoun('possessive')} chest."
    )
    world.say(
        f"Then {master.id} opened the gate, gave {slave.id} freedom, and called the whole hall to witness the change of heart."
    )

    world.para()
    slave.meters["posture"] = 2.0
    slave.meters["freedom"] = 1.0
    slave.memes["fear"] = 0.0
    slave.memes["hope"] = 2.0
    slave.memes["relief"] = 2.0
    world.say(
        f"At last, {slave.id} walked outside with head high and shoulders straight, no longer bowed at all."
    )
    world.say(
        f"In the sun beyond {world.castle}, {slave.id} laughed with {helper.id}, and the happy ending stood bright as bread on a table."
    )

    world.facts.update({
        "params": params,
        "slave": slave,
        "master": master,
        "helper": helper,
        "freed": True,
    })


def generation_prompts(world: TaleWorld) -> list[str]:
    return [
        "Write a folk tale about a slave whose stance changes from bowed to upright through kindness.",
        f"Tell a gentle happy-ending story in {world.castle} where a kind helper changes a harsh master's heart.",
        "Write a short folk tale about kindness, freedom, and a small act that leads to a happy ending.",
    ]


def story_qa(world: TaleWorld) -> list[QAItem]:
    slave = world.get("slave")
    master = world.get("master")
    helper = world.get("helper")
    return [
        QAItem(
            question="Why did the slave keep a low stance at the start?",
            answer="The slave kept a low stance because life in the hall was harsh, and the slave was afraid of a hard master.",
        ),
        QAItem(
            question=f"What did {helper.id} give {slave.id} that helped change the story?",
            answer=f"{helper.id} gave {slave.id} a warm loaf and a kind word, which started the change toward hope.",
        ),
        QAItem(
            question=f"How did {master.id} change by the end?",
            answer=f"{master.id} felt shame and trust after seeing kindness, then opened the gate and gave {slave.id} freedom.",
        ),
        QAItem(
            question="What was the happy ending?",
            answer="The happy ending was that the slave was set free, stood tall, and left the hall with a lighter heart.",
        ),
    ]


def world_knowledge_qa(world: TaleWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps, shares, or speaks gently so another person feels cared for.",
        ),
        QAItem(
            question="What does a happy ending mean in a folk tale?",
            answer="A happy ending means the trouble gets solved and the characters finish in a safe, good place.",
        ),
        QAItem(
            question="What is a stance?",
            answer="A stance is the way someone stands or holds their body, like bowed, straight, or ready.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: TaleWorld) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}: {v:.1f}' for k, v in e.meters.items())}}} "
            f"memes={{{', '.join(f'{k}: {v:.1f}' for k, v in e.memes.items())}}}"
        )
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for cid in CASTLES:
        lines.append(asp.fact("castle", cid))
    lines.append(asp.fact("theme", "kindness"))
    lines.append(asp.fact("theme", "happy_ending"))
    lines.append(asp.fact("theme", "folk_tale"))
    lines.append(asp.fact("keyword", "stance"))
    lines.append(asp.fact("keyword", "slave"))
    return "\n".join(lines)


ASP_RULES = r"""
happy_ending :- theme(happy_ending), theme(kindness), theme(folk_tale).
has_keyword(stance) :- keyword(stance).
has_keyword(slave) :- keyword(slave).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/0.\n#show has_keyword/1."))
    atoms = {(s.name, len(s.arguments), tuple(a.string if a.type.name == "String" else a.name for a in s.arguments)) for s in model}
    want = {("happy_ending", 0, ()), ("has_keyword", 1, ("stance",)), ("has_keyword", 1, ("slave",))}
    if atoms == want:
        print("OK: ASP twin matches Python intent.")
        return 0
    print("MISMATCH:", sorted(atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about stance, kindness, and freedom.")
    ap.add_argument("--castle", choices=CASTLES)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--master-name", choices=MASTER_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    castle = args.castle or rng.choice(list(CASTLES))
    hero = args.hero_name or rng.choice(HERO_NAMES)
    master = args.master_name or rng.choice(MASTER_NAMES)
    helper = args.helper_name or rng.choice(HELPER_NAMES)
    if hero == master:
        raise StoryError("hero and master must be different names")
    return StoryParams(castle=castle, hero_name=hero, master_name=master, helper_name=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.get("slave").id = params.hero_name
    world.get("master").id = params.master_name
    world.get("helper").id = params.helper_name
    # keep keys stable for trace/qa
    world.entities = {
        "slave": world.entities.pop(params.hero_name),
        "master": world.entities.pop(params.master_name),
        "helper": world.entities.pop(params.helper_name),
    }
    world.entities["slave"].id = params.hero_name
    world.entities["master"].id = params.master_name
    world.entities["helper"].id = params.helper_name
    tell_story(world, params)
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
    StoryParams(castle="old_castle", hero_name="Marek", master_name="Lord Bran", helper_name="Old Hana"),
    StoryParams(castle="mill_hall", hero_name="Nera", master_name="Lady Vesa", helper_name="Bela the Baker"),
    StoryParams(castle="river_keep", hero_name="Ivo", master_name="Sir Orin", helper_name="Mira the Miller"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0.\n#show has_keyword/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show happy_ending/0.\n#show has_keyword/1."))
        print("ASP model:", sorted(str(s) for s in model))
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < args.n * 20:
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            key = (params.castle, params.hero_name, params.master_name, params.helper_name)
            if key in seen:
                continue
            seen.add(key)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
