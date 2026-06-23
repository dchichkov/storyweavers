#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/flush_jerk_chocolate_sharing_rhyming_story.py
===============================================================================================================

A standalone storyworld for a tiny rhyming-sharing tale about chocolate,
a rude jerk, and a calming flush of feeling.

Initial story seed:
- A child has chocolate to share.
- A rude jerk wants too much and spoils the mood.
- A grown-up or friend helps turn it into fair sharing.
- The word "flush" appears naturally in the ending image.

This file follows the Storyweavers world contract:
- stdlib only
- eager import of storyworlds.results
- lazy import of storyworlds.asp inside ASP helpers
- StoryParams, build_parser, resolve_params, generate, emit, main
- three QA sets
- inline ASP twin and Python validity gate
- --verify performs parity checks and a smoke test
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: str = ""
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class SharingMove:
    id: str
    verb: str
    rhyme: str
    turn: str
    ending: str
    shares: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Chocolate:
    id: str
    label: str
    phrase: str
    pieces: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    line: str
    fix: str
    tags: set[str] = field(default_factory=set)


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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_flush(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes["embarrassed"] < THRESHOLD:
            continue
        sig = ("flush", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] += 1
        out.append(f"{e.id}'s cheeks went flush, and the room grew quieter.")
    return out


CAUSAL_RULES = [Rule("flush", _r_flush)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def share_risk(move: SharingMove, choc: Chocolate) -> bool:
    return move.shares < choc.pieces and choc.pieces > 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for move_id, move in MOVES.items():
            for choc_id, choc in CHOCOLATES.items():
                if setting in SETTINGS and share_risk(move, choc):
                    combos.append((setting, move_id, choc_id))
    return combos


def prefer_helper(move: SharingMove) -> Helper:
    return HELPERS[move.id]


def tell(setting: Setting, move: SharingMove, choc: Chocolate,
         hero_name: str, hero_type: str, helper_type: str, helper_name: str,
         jerk_name: str, jerk_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["kind", "careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, traits=["gentle"]))
    jerk = world.add(Entity(id=jerk_name, kind="character", type=jerk_type, traits=["greedy", "rude"]))
    treat = world.add(Entity(id="chocolate", kind="thing", type="thing", label=choc.label, plural=choc.pieces > 1))
    world.facts.update(hero=hero, helper=helper, jerk=jerk, treat=treat, move=move, choc_cfg=choc, setting=setting)

    hero.memes["want_to_share"] += 1
    helper.memes["kindness"] += 1
    jerk.memes["greed"] += 1

    world.say(
        f"In {setting.place}, {hero.id} found {choc.phrase} and smiled with delight."
    )
    world.say(
        f"{hero.id} wanted to share, for sharing can spark a sweet little light."
    )

    world.para()
    world.say(
        f"But {jerk.id}, that silly jerk, leaned close and wanted the whole sweet heap,"
    )
    world.say(
        f"so {hero.id} felt a tiny sting while {hero.pronoun('possessive')} hopes did sleep."
    )

    helper_obj = prefer_helper(move)
    helper = world.get(helper_name)
    hero.memes["embarrassed"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then {helper.id} said, '{helper_obj.line}', and showed a fairer way to play."
    )
    world.say(
        f"{helper_obj.fix}, and {hero.id} could share {choc.it()} without delay."
    )
    hero.meters["shared"] += 1
    helper.meters["helped"] += 1
    jerk.memes["apology"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{hero.id} passed out neat pieces, and even {jerk.id} had one at last."
    )
    world.say(
        f"The chocolate went around the room, and the grumpy moment passed."
    )

    world.para()
    world.say(
        f"At the end, the plate was bare, the wrappers sat in a tidy row,"
    )
    world.say(
        f"and {hero.id} stood with a flush of cheer, because sharing made the whole day glow."
    )
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", mood="bright", affords={"share"}),
    "picnic": Setting(place="the picnic blanket", mood="sunny", affords={"share"}),
    "classroom": Setting(place="the classroom circle", mood="cozy", affords={"share"}),
}

MOVES = {
    "spoons": SharingMove(
        id="spoons",
        verb="pass spoonfuls",
        rhyme="loonfuls",
        turn="share the spoons",
        ending="passed them around in turns",
        shares=3,
        tags={"share", "chocolate"},
    ),
    "squares": SharingMove(
        id="squares",
        verb="break into squares",
        rhyme="careful squares",
        turn="share the squares",
        ending="broke it into even bits",
        shares=4,
        tags={"share", "chocolate"},
    ),
    "cups": SharingMove(
        id="cups",
        verb="scoop into cups",
        rhyme="happy cups",
        turn="share the cups",
        ending="divvied it into little cups",
        shares=3,
        tags={"share", "chocolate"},
    ),
}

CHOCOLATES = {
    "bar": Chocolate(id="bar", label="chocolate bar", phrase="a chocolate bar", pieces=4, tags={"chocolate", "sweet"}),
    "mousse": Chocolate(id="mousse", label="chocolate mousse", phrase="a bowl of chocolate mousse", pieces=3, tags={"chocolate", "sweet"}),
    "cookies": Chocolate(id="cookies", label="chocolate cookies", phrase="a plate of chocolate cookies", pieces=6, tags={"chocolate", "sweet"}),
}

HELPERS = {
    "spoons": Helper(id="helper1", label="the helper", line="Let's not rush; let's share with care", fix="They took turns with little spoons"),
    "squares": Helper(id="helper2", label="the helper", line="A fair cut is the kindest route", fix="They broke the bar into even squares"),
    "cups": Helper(id="helper3", label="the helper", line="A cup for you, a cup for me", fix="They spooned the chocolate into small cups"),
}


@dataclass
class StoryParams:
    setting: str = "kitchen"
    move: str = "squares"
    chocolate: str = "bar"
    hero_name: str = "Nina"
    hero_type: str = "girl"
    helper_name: str = "Omar"
    helper_type: str = "boy"
    jerk_name: str = "Rex"
    jerk_type: str = "boy"
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, jerk, move, choc = f["hero"], f["jerk"], f["move"], f["choc_cfg"]
    return [
        f'Write a rhyming story for a small child about sharing {choc.phrase} and staying kind even when a jerk is greedy.',
        f"Tell a gentle story where {hero.id} wants to {move.verb} and {jerk.id} acts like a jerk, but everyone ends up sharing.",
        f'Write a short rhyming tale that includes the words "chocolate", "jerk", and "flush" and ends with fair sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, jerk, move, choc = f["hero"], f["helper"], f["jerk"], f["move"], f["choc_cfg"]
    return [
        QAItem(
            f"Who wanted to share the {choc.label}?",
            f"{hero.id} wanted to share the {choc.label}. {hero.id} was kind and wanted everyone to have a sweet part.",
        ),
        QAItem(
            f"Why did {hero.id} feel upset when {jerk.id} acted like a jerk?",
            f"{jerk.id} wanted too much and made the moment feel unfair. That was hard for {hero.id}, because sharing only feels sweet when everyone gets a turn.",
        ),
        QAItem(
            f"How did {helper.id} help make the sharing fair?",
            f"{helper.id} gave a calm idea and showed a fair way to split the {choc.label}. That helped {hero.id} turn the treat into equal pieces.",
        ),
        QAItem(
            f"What changed at the end of the story?",
            f"The plate went from crowded and tense to neat and fair. In the end, {hero.id} shared the {choc.label}, and even {jerk.id} got one piece instead of all of it.",
        ),
        QAItem(
            f"Why did {hero.id}'s cheeks go flush at the end?",
            f"{hero.id}'s cheeks went flush because the rude moment had passed and the room felt calmer. The flush was a little sign that the worry had turned into happy pride.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does sharing mean?", "Sharing means giving some of what you have to someone else too, so everyone can enjoy it."),
        QAItem("What is chocolate?", "Chocolate is a sweet food made from cocoa. People often share it as a treat."),
        QAItem("What does flush mean in this story?", "Here, flush means a warm red color in the cheeks, like when someone feels shy, proud, or relieved."),
        QAItem("What is a jerk?", "A jerk is a rude person who acts selfishly or meanly."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", move="squares", chocolate="bar", hero_name="Nina", hero_type="girl", helper_name="Omar", helper_type="boy", jerk_name="Rex", jerk_type="boy"),
    StoryParams(setting="picnic", move="cups", chocolate="mousse", hero_name="Mina", hero_type="girl", helper_name="Luca", helper_type="boy", jerk_name="Tess", jerk_type="girl"),
    StoryParams(setting="classroom", move="spoons", chocolate="cookies", hero_name="Eli", hero_type="boy", helper_name="June", helper_type="girl", jerk_name="Max", jerk_type="boy"),
    StoryParams(setting="kitchen", move="cups", chocolate="cookies", hero_name="Ava", hero_type="girl", helper_name="Theo", helper_type="boy", jerk_name="Pip", jerk_type="boy"),
]


def explain_rejection(setting: str, move: str, chocolate: str) -> str:
    return f"(No story: {move} and {chocolate} do not make a fair sharing story in {setting}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        for a in s.affords:
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("shares", mid, m.shares))
    for cid, c in CHOCOLATES.items():
        lines.append(asp.fact("chocolate", cid))
        lines.append(asp.fact("pieces", cid, c.pieces))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Setting,Move,Chocolate) :- setting(Setting), move(Move), chocolate(Chocolate), affords(Setting, share), shares(Move, S), pieces(Chocolate, P), S < P.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    ok = True
    if clingo_set != python_set:
        ok = False
        print("MISMATCH between clingo and valid_combos():")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, move=None, chocolate=None, hero_name=None, hero_type=None, helper_name=None, helper_type=None, jerk_name=None, jerk_type=None, seed=None), random.Random(777)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if ok:
        print(f"OK: ASP parity and smoke test passed ({len(clingo_set)} combos).")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming sharing storyworld with chocolate, a jerk, and a flush of feeling.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--chocolate", choices=CHOCOLATES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
    ap.add_argument("--jerk-name")
    ap.add_argument("--jerk-type", choices=["girl", "boy"])
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
              and (args.move is None or c[1] == args.move)
              and (args.chocolate is None or c[2] == args.chocolate)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, move, chocolate = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if hero_type == "girl" else "girl")
    jerk_type = args.jerk_type or rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        move=move,
        chocolate=chocolate,
        hero_name=args.hero_name or rng.choice(["Nina", "Mia", "Lily", "Ava", "Eli", "Noah"]),
        hero_type=hero_type,
        helper_name=args.helper_name or rng.choice(["Omar", "June", "Theo", "Luca", "Zoe", "Finn"]),
        helper_type=helper_type,
        jerk_name=args.jerk_name or rng.choice(["Rex", "Pip", "Max", "Tess", "Jeb", "Milo"]),
        jerk_type=jerk_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.move not in MOVES or params.chocolate not in CHOCOLATES:
        raise StoryError("Invalid story params.")
    world = tell(
        SETTINGS[params.setting],
        MOVES[params.move],
        CHOCOLATES[params.chocolate],
        params.hero_name,
        params.hero_type,
        params.helper_type,
        params.helper_name,
        params.jerk_name,
        params.jerk_type,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, move, chocolate) combos:")
        for row in combos:
            print("  ", row)
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
