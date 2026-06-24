#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a wan child, a mistaken wish, a lesson
learned, and a reconciliation that ends happily.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "fairy"}
        male = {"boy", "prince", "king", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    name: str
    place: str
    mood: str


@dataclass
class Wish:
    id: str
    verb: str
    effect: str
    risk: str
    outcome: str
    keyword: str = "wan"


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    soothing: str


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_sadness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("hurt", 0.0) < THRESHOLD:
        return out
    if ("sadness",) in world.fired:
        return out
    world.fired.add(("sadness",))
    child.memes["sad"] = child.memes.get("sad", 0.0) + 1
    out.append("The little one grew quiet and sad.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    fairy = world.entities.get("fairy")
    if not child or not fairy:
        return out
    if child.memes.get("apology", 0.0) < THRESHOLD or fairy.memes.get("forgiven", 0.0) >= THRESHOLD:
        return out
    if ("reconcile",) in world.fired:
        return out
    world.fired.add(("reconcile",))
    fairy.memes["forgiven"] = 1.0
    child.memes["peace"] = 1.0
    child.memes["hurt"] = 0.0
    out.append("The fairy forgave the child, and their hearts felt light again.")
    return out


CAUSAL_RULES = [_r_sadness, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def simulate(world: World, child: Entity, fairy: Entity, wish: Wish, gift: Gift) -> None:
    world.say(
        f"Once in a tiny kingdom, there lived a wan little {child.type} named {child.id}. "
        f"{child.pronoun().capitalize()} had a soft voice and a kind heart, but {child.pronoun('possessive')} face often looked pale in the moonlight."
    )
    world.say(
        f"Near the castle garden lived a gentle {fairy.type} named {fairy.id}. "
        f"{fairy.pronoun().capitalize()} watched over the roses and listened to wishes."
    )
    world.say(
        f"Every evening, {child.id} loved to {wish.verb}, because {wish.effect}. "
        f"But one day, the wish brought trouble: {wish.risk}."
    )

    world.para()
    world.say(
        f"In the {world.setting.mood} garden, {child.id} tried again, and the wish turned wrong. "
        f"{wish.outcome}."
    )
    child.memes["hurt"] = 1.0
    fairy.memes["concern"] = 1.0
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {child.id} lowered {child.pronoun('possessive')} head and said sorry. "
        f'{child.pronoun().capitalize()} explained, "I was wrong to rush ahead."'
    )
    child.memes["apology"] = 1.0
    world.say(
        f"{fairy.id} listened kindly and held out {gift.phrase}. "
        f"{gift.soothing}"
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.id} accepted the gift, and {child.pronoun('possessive')} eyes brightened. "
        f"{child.id} learned that a wish is best when it is gentle and shared."
    )
    world.say(
        f"By nightfall, the garden was calm again, and {child.id} and {fairy.id} were friends once more, smiling under the stars."
    )


SETTINGS = {
    "moon_garden": Setting(name="moon garden", place="the moonlit garden", mood="moonlit"),
    "rose_courtyard": Setting(name="rose courtyard", place="the rose courtyard", mood="rose-sweet"),
    "bramble_path": Setting(name="bramble path", place="the bramble path", mood="softly glowing"),
}

WISHES = {
    "sing": Wish(
        id="sing",
        verb="sing to the roses",
        effect="the flowers opened a little wider",
        risk="the song woke a sleeping sparrow too early",
        outcome="the sparrow fluttered into the rose bush, and a thorn pricked the child’s finger",
        keyword="wan",
    ),
    "touch_star": Wish(
        id="touch_star",
        verb="reach for a star-shaped bloom",
        effect="it seemed to shine just for the child",
        risk="the bloom sat high on a thorny branch",
        outcome="the child slipped and got a scratch on the wrist",
        keyword="wan",
    ),
    "wake_bloom": Wish(
        id="wake_bloom",
        verb="wake the sleepy lily with a whisper",
        effect="the lily’s petals trembled like silver",
        risk="the whisper was too hurried and too loud",
        outcome="the lily closed again and the child felt foolish",
        keyword="wan",
    ),
}

GIFTS = {
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a little lantern with a golden handle",
        soothing="It glowed softly, showing that slow hands make kinder magic.",
    ),
    "shawl": Gift(
        id="shawl",
        label="shawl",
        phrase="a warm shawl made of blue thread",
        soothing="It wrapped the child in comfort and reminded them to be patient.",
    ),
    "petal_book": Gift(
        id="petal_book",
        label="book",
        phrase="a tiny book of petal poems",
        soothing="Its pages said that gentle words can mend a tender heart.",
    ),
}


@dataclass
class StoryParams:
    setting: str
    wish: str
    gift: str
    name: str
    role: str
    seed: Optional[int] = None


NAMES = ["Elara", "Nico", "Mira", "Tobin", "Luna", "Oren"]
ROLES = ["girl", "boy", "princess", "prince"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about wanness, loss, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--wish", choices=WISHES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    wish = args.wish or rng.choice(list(WISHES))
    gift = args.gift or rng.choice(list(GIFTS))
    if args.wish and args.gift == "shawl" and args.wish == "touch_star":
        raise StoryError("The shawl is not a good remedy for a thorny star-branch mishap.")
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(setting=setting, wish=wish, gift=gift, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    child = world.add(Entity(id="child", kind="character", type=params.role, label=params.name))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label="the fairy"))
    wish = WISHES[params.wish]
    gift = GIFTS[params.gift]
    world.facts.update(child=child, fairy=fairy, wish=wish, gift=gift, params=params)

    simulate(world, child, fairy, wish, gift)

    prompts = [
        f'Write a fairy tale for young children about a wan {params.role} named {params.name}, a mistake, and a kind forgiveness.',
        f'Tell a short story in which a child tries to {wish.verb} in a magical garden, learns a lesson, and makes peace with a fairy.',
        f'Write a happy ending story where the word "{wish.keyword}" appears and the hero learns to be gentle.',
    ]
    story_qa = [
        QAItem(
            question=f"Why did {params.name} feel sad in the garden?",
            answer=f"{params.name} felt sad because the wish went wrong and the child got hurt. After that, {params.name} apologized and learned to be more gentle.",
        ),
        QAItem(
            question=f"How did the fairy help {params.name} feel better?",
            answer=f"The fairy forgave {params.name} and offered {gift.phrase}. That kind gift helped turn the mistake into a lesson learned.",
        ),
        QAItem(
            question=f"What did {params.name} learn by the end of the story?",
            answer=f"{params.name} learned that magic works best when it is careful, patient, and shared with others.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a fairy in stories?",
            answer="A fairy is a tiny magical helper who often lives in gardens or forests and can guide people kindly.",
        ),
        QAItem(
            question="What does it mean to apologize?",
            answer="To apologize means to say you are sorry after you have hurt someone or made a mistake.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is a good idea or truth that someone understands after an experience.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for (n,) in world.fired)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
% A wish is risky when it produces a thorn, scratch, or hurt.
risky(W) :- wish(W), risk(W, _).
lesson_learned(W) :- risky(W).
happy_ending(W) :- lesson_learned(W), gift(W, _).
reconciliation(W) :- hurt(W), apology(W), forgiven(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for wid, w in WISHES.items():
        lines.append(asp.fact("wish", wid))
        lines.append(asp.fact("risk", wid, "thorn"))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid, "kind"))
    lines.append(asp.fact("hurt", "sing"))
    lines.append(asp.fact("apology", "sing"))
    lines.append(asp.fact("forgiven", "sing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show risky/1.\n#show lesson_learned/1.\n#show happy_ending/1.\n#show reconciliation/1."))
    atoms = set((a.name, tuple(arg.string if arg.type == 1 else arg.number for arg in a.arguments)) for a in model)
    expected = {
        ("risky", ("sing",)),
        ("lesson_learned", ("sing",)),
        ("happy_ending", ("sing",)),
        ("reconciliation", ("sing",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


CURATED = [
    StoryParams(setting="moon_garden", wish="sing", gift="lantern", name="Elara", role="girl"),
    StoryParams(setting="rose_courtyard", wish="touch_star", gift="shawl", name="Nico", role="boy"),
    StoryParams(setting="bramble_path", wish="wake_bloom", gift="petal_book", name="Mira", role="princess"),
]


def build_storyworld(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show risky/1.\n#show lesson_learned/1.\n#show happy_ending/1.\n#show reconciliation/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.wish} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
