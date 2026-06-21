#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fraternity_brow_rhyme_friendship_lesson_learned_nursery.py
==========================================================================================

A tiny nursery-rhyme storyworld about a little friendship circle in a backyard,
a bumped brow, a gentle repair, and a lesson learned.

The seed words are folded into the world model:
- fraternity: a little friendship club of children
- brow: the place where a bump can show
- Rhyme, Friendship, Lesson Learned: the narration leans musical and child-facing
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
LESSON_MIN = 1.0


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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    rhyme_cue: str
    cozy_detail: str
    can_trip: bool = True


@dataclass
class Toy:
    id: str
    label: str
    mishap: str
    helps: str
    can_trip: bool = False


@dataclass
class StoryParams:
    setting: str
    toy: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    helper: str
    helper_gender: str
    lesson: str
    seed: Optional[int] = None


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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_hurt(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["tumble"] < THRESHOLD:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["hurt"] += 1
        e.memes["worry"] += 1
        out.append("__hurt__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("lesson_spoken"):
        for e in world.characters():
            if e.memes["friendship"] >= THRESHOLD and e.memes["kindness"] >= THRESHOLD:
                sig = ("lesson", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.memes["lesson"] += 1
                out.append("__lesson__")
    return out


RULES = [Rule("hurt", _r_hurt), Rule("lesson", _r_lesson)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, side by side, in a little rhyme they took a ride."


def predict_tumble(world: World, helper_id: str) -> dict:
    sim = world.copy()
    sim.get(helper_id).meters["tumble"] += 1
    propagate(sim, narrate=False)
    return {"hurt": any(e.meters["hurt"] >= THRESHOLD for e in sim.characters())}


def tell(setting: Setting, toy: Toy, f1: str, g1: str, f2: str, g2: str,
         helper: str, hg: str, lesson: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=f1, kind="character", type=g1, role="friend",
                         traits=["bright"], attrs={"club": "fraternity"}))
    b = world.add(Entity(id=f2, kind="character", type=g2, role="friend",
                         traits=["gentle"], attrs={"club": "fraternity"}))
    c = world.add(Entity(id=helper, kind="character", type=hg, role="helper",
                         traits=["kind"], attrs={"club": "fraternity"}))
    world.add(Entity(id="toy", label=toy.label))
    a.memes["friendship"] = 1
    b.memes["friendship"] = 1
    c.memes["friendship"] = 1
    c.memes["kindness"] = 1

    world.say(
        f"In the {setting.place}, under the soft and sunny sky, lived a tiny "
        f"fraternity of friends: {a.id}, {b.id}, and {c.id}."
    )
    world.say(
        f"They sang a little tune by the bench and gate, and every hop and skip "
        f"felt small and great."
    )
    world.say(
        f"{setting.cozy_detail} {rhyme_line(a.id, b.id)}"
    )
    world.para()
    world.say(
        f"But {a.id} and {b.id} both loved the same shiny toy, and their voices "
        f"grew bumpy and coy."
    )
    world.say(
        f'They rushed to pull it at once, and down went {a.id}, bumping {a.id}\'s brow.'
    )
    a.meters["tumble"] += 1
    a.meters["brow"] += 1
    a.memes["upset"] += 1
    b.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{b.id} gasped, "Oh dear, oh my, let us not fuss and let tears dry."'
    )
    world.say(
        f"{c.id} came softly with a cloth so clean, as kind as a breeze, as calm as a bean."
    )
    world.para()
    world.say(
        f'{c.id} spoke the lesson in a nursery rhyme: '
        f'"One friend waits, one friend shares, and gentle hands are always fair."'
    )
    world.facts["lesson_spoken"] = True
    world.facts["lesson"] = lesson
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    c.memes["friendship"] += 1
    a.memes["kindness"] += 1
    b.memes["kindness"] += 1
    c.memes["kindness"] += 1
    a.memes["lesson"] += 1
    b.memes["lesson"] += 1
    c.memes["lesson"] += 1
    world.say(
        f"They shared the toy by turns, and the little square grew merry again."
    )
    world.say(
        f"At sunset, {a.id}'s brow was cool, the toy was safe, and the fraternity "
        f"of friends held hands in a row."
    )
    world.say(
        f"And that was the lesson, plain as a bell: friendship grows when you share "
        f"well."
    )
    world.facts.update(instigator=a, friend=b, helper=c, setting=setting, toy=toy)
    return world


SETTINGS = {
    "garden": Setting(id="garden", place="garden path", rhyme_cue="gate", cozy_detail="Beside the daisies,"),
    "porch": Setting(id="porch", place="porch step", rhyme_cue="door", cozy_detail="Under the porch light,"),
    "meadow": Setting(id="meadow", place="meadow lane", rhyme_cue="stream", cozy_detail="Near the buttercups,"),
}

TOYS = {
    "ball": Toy(id="ball", label="bright red ball", mishap="bump", helps="share"),
    "kite": Toy(id="kite", label="striped kite string", mishap="tangle", helps="take turns"),
    "drum": Toy(id="drum", label="little drum", mishap="thump", helps="wait"),
}

NAMES = ["Mia", "Ned", "Lola", "June", "Pip", "Tess", "Ben", "Rose", "Otis", "Wren"]


def valid_combos() -> list[tuple[str, str]]:
    return sorted((s, t) for s in SETTINGS for t in TOYS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about friendship and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--friend1")
    ap.add_argument("--friend1-gender", choices=["girl", "boy"])
    ap.add_argument("--friend2")
    ap.add_argument("--friend2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--lesson", default="share and take turns")
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
              and (args.toy is None or c[1] == args.toy)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, toy = rng.choice(combos)
    f1 = args.friend1 or rng.choice(NAMES)
    f2 = args.friend2 or rng.choice([n for n in NAMES if n != f1])
    helper = args.helper or rng.choice([n for n in NAMES if n not in {f1, f2}])
    g1 = args.friend1_gender or rng.choice(["girl", "boy"])
    g2 = args.friend2_gender or ("boy" if g1 == "girl" else "girl")
    hg = args.helper_gender or rng.choice(["girl", "boy"])
    if len({f1, f2, helper}) < 3:
        raise StoryError("Need three distinct children for the friendship story.")
    return StoryParams(setting=setting, toy=toy, friend1=f1, friend1_gender=g1,
                       friend2=f2, friend2_gender=g2, helper=helper,
                       helper_gender=hg, lesson=args.lesson)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.toy not in TOYS:
        raise StoryError("Invalid setting or toy.")
    world = tell(SETTINGS[params.setting], TOYS[params.toy],
                 params.friend1, params.friend1_gender,
                 params.friend2, params.friend2_gender,
                 params.helper, params.helper_gender,
                 params.lesson)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    return [
        f'Write a nursery-rhyme story about friendship in the {f["setting"].place} that includes the word "fraternity".',
        f"Tell a short rhyming tale where {a.id} and {b.id} share a toy, bump a brow, and learn a kind lesson.",
        f'Write a gentle story that includes the word "brow" and ends with friends choosing to share.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["friend"]
    c = f["helper"]
    toy = f["toy"]
    setting = f["setting"]
    return [
        ("Who is the story about?",
         f"It is about three friends in a little fraternity: {a.id}, {b.id}, and {c.id}. They play together in {setting.place} like a tiny nursery rhyme."),
        ("What happened to the brow?",
         f"{a.id} bumped {a.id}'s brow when the toy was pulled too hard. The bump was small, but it changed the play into a careful moment."),
        ("What lesson did they learn?",
         f"They learned to share and take turns. After the bump, they used kind hands so everyone could keep playing safely."),
        ("How did the story end?",
         f"It ended with friendship growing stronger. The toy was shared, the brow was cool, and the children stood together happily."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a fraternity?",
         "In this story, fraternity means a little group of friends who belong together and look after one another."),
        ("What is a brow?",
         "A brow is the part of your face above your eyes. If you bump it, you may need a gentle cloth and a little rest."),
        ("Why is sharing important?",
         "Sharing helps friends stay kind and calm. It keeps play fair so everyone can enjoy the game."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
friend(X) :- character(X), role(X, friend).
lesson_learned(X) :- friend(X), lesson_spoken.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOYS:
        lines.append(asp.fact("toy", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show setting/1.\n#show toy/1."))
    return sorted(set(asp.atoms(model, "setting"))), sorted(set(asp.atoms(model, "toy")))


def asp_verify() -> int:
    rc = 0
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(params)
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as err:
        print(f"FAIL: smoke test crashed: {err}")
        return 1
    print("OK: smoke test generated a story.")
    return rc


CURATED = [
    StoryParams(setting="garden", toy="ball", friend1="Mia", friend1_gender="girl",
                friend2="Ned", friend2_gender="boy", helper="Lola", helper_gender="girl",
                lesson="share and take turns"),
    StoryParams(setting="porch", toy="kite", friend1="Pip", friend1_gender="boy",
                friend2="Tess", friend2_gender="girl", helper="Rose", helper_gender="girl",
                lesson="be gentle and wait"),
]


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
        print(asp_program("", "#show setting/1.\n#show toy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP twin is present; this tiny world uses a simple validity grid.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
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


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a nursery-rhyme friendship story that includes the word "fraternity".',
        'Tell a child-friendly story where a little brow gets bumped and a lesson is learned.',
        'Make the story sing with rhyme, friendship, and a kind ending.',
    ]


if __name__ == "__main__":
    main()
