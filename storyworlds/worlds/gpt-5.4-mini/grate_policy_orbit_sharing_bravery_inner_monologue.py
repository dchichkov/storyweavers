#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grate_policy_orbit_sharing_bravery_inner_monologue.py
======================================================================================

A standalone storyworld for a tiny Folk Tale domain: two children find a bright
little treasure, worry over the village policy, and gather the bravery to share.
The story uses physical meters and emotional memes, with a state-driven turn,
an inner monologue beat, and a gentle ending image that proves what changed.

Seed words: grate, policy, orbit
Features: Sharing, Bravery, Inner Monologue
Style: Folk Tale
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
class Setting:
    id: str
    place: str
    folk_detail: str
    policy: str
    has_grate: bool = True


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    orbit_word: str
    can_split: bool = False


@dataclass
class Choice:
    id: str
    sense: int
    share_gain: int
    text: str
    fail: str
    qa_text: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    prize: str
    choice: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None


SETTINGS = {
    "mill": Setting("mill", "the old mill", "a stone grate warmed by the hearth", "the village policy said found treasures must be shared"),
    "orchard": Setting("orchard", "the apple orchard", "a mossy grate by the cookfire", "the orchard policy said no one should hide a found wonder"),
    "brook": Setting("brook", "the brookside cottage", "a black grate by the fire", "the cottage policy said a prize found by children should be shared with care"),
}

PRIZES = {
    "silver_orbit": Prize("silver_orbit", "silver orbit", "a little silver orbit toy", "orbit"),
    "gold_rattle": Prize("gold_rattle", "gold rattle", "a bright gold rattle", "orbit"),
    "moon_ring": Prize("moon_ring", "moon ring", "a round moon ring", "orbit"),
}

CHOICES = {
    "share": Choice("share", 3, 2,
                    "smiled, held the treasure out, and shared turns by the grate",
                    "stared at the treasure and would not share at all",
                    "shared the treasure and took turns by the grate"),
    "hide": Choice("hide", 1, 0,
                   "hid the treasure in a sleeve and kept it close",
                   "hid the treasure and refused to let anyone near",
                   "hid the treasure"),
}

NAMES = ["Mira", "Tobin", "Lena", "Ivo", "Anya", "Pip", "Milo", "Rhea"]
TRAITS = ["steady", "bright", "gentle", "bold", "careful", "kind"]


def reasonableness_gate(choice: Choice) -> bool:
    return choice.sense >= 2


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid in PRIZES:
            if reasonableness_gate(CHOICES["share"]):
                combos.append((sid, pid))
    return combos


def _monologue(world: World, child: Entity, prize: Prize) -> str:
    if child.memes["fear"] >= THRESHOLD:
        return f'{child.id} thought, "If I share, maybe the others will laugh."'
    return f'{child.id} thought, "If I share, the whole room may grow warmer."'


def tell(setting: Setting, prize: Prize, choice: Choice,
         a: Entity, b: Entity, elder: Entity) -> World:
    world = World(setting)
    child_a = world.add(a)
    child_b = world.add(b)
    old = world.add(elder)
    treasure = world.add(Entity(id="treasure", type="thing", label=prize.label))

    child_a.memes["want"] = 1
    child_a.memes["bravery"] = 0
    child_b.memes["worry"] = 1
    old.memes["care"] = 1

    world.say(
        f"In {setting.place}, where {setting.folk_detail}, {child_a.id} and {child_b.id} found {prize.phrase} near the {prize.orbit_word} wheel."
    )
    world.say(
        f"{setting.policy.capitalize()}, and the old {old.label_word} nodded at the rule."
    )

    world.para()
    world.say(
        f"{child_a.id} wanted to keep it, for it shone like a small moon, but {child_b.id} lifted a worried brow."
    )
    world.say(_monologue(world, child_a, prize))

    if choice.id == "hide":
        child_a.memes["fear"] += 1
        child_b.memes["hurt"] += 1
        world.say(
            f"{child_a.id} hid the treasure, and the day turned heavy and quiet."
        )
        world.say(
            f"Then {old.id} found the hidden prize, reminded them of the policy, and asked for a kinder path."
        )
        world.para()
        world.say(
            f"At last {child_a.id} took a breath, gave the treasure back, and let {child_b.id} hold it too."
        )
    else:
        child_a.memes["bravery"] += 2
        child_b.memes["joy"] += 1
        treasure.meters["shared"] += 1
        treasure.meters["passed"] += 1
        world.say(
            f"{child_a.id} remembered the policy, gathered {child_a.pronoun('possessive')} bravery, and said, 'Let us share it properly.'"
        )
        world.say(
            f"So the two children took turns, one after the other, while the treasure rested by the grate between them."
        )
        world.say(
            f"Each turn made the room softer, and {child_b.id} smiled because no one was left out."
        )

    world.para()
    world.say(
        f"By evening, the treasure had gone round and round like a friendly orbit, and both children sat side by side near the warm grate."
    )

    world.facts.update(
        setting=setting,
        prize=prize,
        choice=choice,
        child_a=child_a,
        child_b=child_b,
        elder=old,
        treasure=treasure,
        shared=choice.id == "share",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting, prize, choice = f["setting"], f["prize"], f["choice"]
    return [
        f'Write a Folk Tale for a young child that includes the words "grate", "policy", and "orbit".',
        f"Tell a gentle story in {setting.place} where two children find {prize.phrase} and have to follow the village policy.",
        f"Write a story about bravery and sharing, where a child has an inner monologue before choosing whether to share a found treasure.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, old = f["child_a"], f["child_b"], f["elder"]
    prize, setting = f["prize"], f["setting"]
    choice = f["choice"]
    qa = [
        ("Who found the treasure?",
         f"{a.id} and {b.id} found {prize.phrase} in {setting.place}. They noticed it near the old village work and treated it like something special."),
        ("What did the village policy say?",
         f"It said found treasures must be shared. That rule gave the children a clear and fair way to decide what to do."),
        ("What did the brave child think?",
         f"{a.id} thought about whether to share and felt a little afraid at first. Then {a.id} gathered enough bravery to do the right thing."),
    ]
    if choice.id == "share":
        qa.append((
            "How did the children solve the problem?",
            f"They shared the treasure and took turns with it. Because they listened to the policy, nobody was left out and the treasure felt friendly again."
        ))
    else:
        qa.append((
            "How did the children solve the problem?",
            f"They first hid the treasure, but that did not feel right. In the end they listened to {old.id} and shared it after all."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with both children sitting together near the grate while the treasure went round and round like an orbit. The ending shows that sharing made the day peaceful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a grate?",
         "A grate is a metal or stone opening that lets heat, air, or water pass through. In stories, it can be a warm place near a fire."),
        ("What does policy mean?",
         "A policy is a rule or a plan that tells people what they should do. It helps everyone know the fair way to act."),
        ("What does orbit mean?",
         "To orbit means to go around something in a circle. The moon orbits the Earth, and a wheel can seem to orbit around and around."),
        ("What is sharing?",
         "Sharing means letting other people use or enjoy something too. It is a kind way to make sure nobody is left out."),
        ("What is bravery?",
         "Bravery means doing the right thing even when you feel shy or scared. A brave child may still feel worried, but keeps going anyway."),
        ("What is an inner monologue?",
         "An inner monologue is the little voice in your head that says what you are thinking. It can help a person sort out a hard choice."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
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


ASP_RULES = r"""
valid(S,P) :- setting(S), prize(P).
shared :- choice(share).
story_ok(S,P) :- valid(S,P), shared.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _random
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAILED smoke test: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A Folk Tale world about sharing, bravery, and an inner monologue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.choice and not reasonableness_gate(CHOICES[args.choice]):
        raise StoryError("That choice is too weak to make a proper story.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.prize is None or c[1] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize = rng.choice(sorted(combos))
    choice = args.choice or "share"
    a_name = args.name or rng.choice(NAMES)
    b_name = rng.choice([n for n in NAMES if n != a_name])
    elder_name = rng.choice([n for n in NAMES if n not in {a_name, b_name}])
    a_gender = rng.choice(["girl", "boy"])
    b_gender = "boy" if a_gender == "girl" else "girl"
    elder_gender = rng.choice(["girl", "boy"])
    return StoryParams(setting, prize, choice, a_name, a_gender, b_name, b_gender, elder_name, elder_gender)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    prize = PRIZES[params.prize]
    choice = CHOICES[params.choice]
    world = tell(
        setting, prize, choice,
        Entity(id=params.child_a, kind="character", type=params.child_a_gender, role="child"),
        Entity(id=params.child_b, kind="character", type=params.child_b_gender, role="child"),
        Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"),
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("mill", "silver_orbit", "share", "Mira", "girl", "Tobin", "boy", "Edda", "girl"),
    StoryParams("orchard", "gold_rattle", "share", "Lena", "girl", "Ivo", "boy", "Marta", "girl"),
    StoryParams("brook", "moon_ring", "share", "Pip", "boy", "Rhea", "girl", "Nessa", "woman"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, prize) combos:\n")
        for s, p in asp_valid_combos():
            print(f"  {s:10} {p}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
