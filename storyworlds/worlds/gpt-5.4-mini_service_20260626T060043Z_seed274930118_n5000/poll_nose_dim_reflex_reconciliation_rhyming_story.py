#!/usr/bin/env python3
"""
A small storyworld about a class poll, a dim little nose-light, a reflex,
and a rhyming reconciliation.

The seed words are built into the domain:
- poll: a count of votes for a choice
- nose-dim: a tiny nose lantern that can grow dim when worried
- reflex: a quick flinch or tap that happens before thinking
- reconciliation: making up after a disagreement

The stories are meant to sound lightly rhyming and child-facing, with a clear
setup, a tense middle, and a gentle ending image.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("glow", "polish", "wear", "mess"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "hurt", "pride", "warmth", "awkward", "reconcile"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class PollChoice:
    id: str
    label: str
    rhyme: str
    glow_kind: str = "glow"


@dataclass
class StoryParams:
    setting: str
    choice: str
    child: str
    gender: str
    friend: str
    seed: Optional[int] = None


SETTINGS = {
    "classroom": Setting(place="the classroom", indoors=True),
    "hall": Setting(place="the school hall", indoors=True),
    "library": Setting(place="the library corner", indoors=True),
}

CHOICES = {
    "blue_banner": PollChoice(id="blue_banner", label="blue banner", rhyme="blue hue"),
    "gold_star": PollChoice(id="gold_star", label="gold star", rhyme="sunny star"),
    "red_balloon": PollChoice(id="red balloon", label="red balloon", rhyme="bright soon"),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Sam"]
FRIENDS = ["Pip", "June", "Kai", "Tess", "Owen", "Ruby"]


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def _r_reflex(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["awkward"] < THRESHOLD:
        return out
    sig = ("reflex",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["wear"] += 0.3
    child.memes["hurt"] += 0.4
    out.append("A quick reflex made the little room go still.")
    return out


def _r_nosedim(world: World) -> list[str]:
    out: list[str] = []
    nose = world.get("nose")
    child = world.get("child")
    if child.memes["worry"] < THRESHOLD:
        return out
    sig = ("nosedim",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    nose.meters["glow"] = max(0.0, nose.meters["glow"] - 1.0)
    out.append("The nose-light grew dim, like dusk on a hill.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    friend = world.get("friend")
    if child.memes["hurt"] < THRESHOLD or friend.memes["pride"] < THRESHOLD:
        return out
    if child.memes["warmth"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["reconcile"] += 1
    friend.memes["reconcile"] += 1
    child.memes["hurt"] = 0.0
    friend.memes["pride"] = max(0.0, friend.memes["pride"] - 1.0)
    out.append("Then came reconciliation, soft as a lullaby.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_reflex, _r_nosedim, _r_reconcile):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_outcome(world: World, child: Entity, friend: Entity) -> dict:
    sim = world.copy()
    sim.get("child").memes["awkward"] += 1
    sim.get("child").memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "dim": sim.get("nose").meters["glow"] < 1.0,
        "reconciled": sim.get("child").memes["reconcile"] >= 1.0,
    }


def tell(setting: Setting, choice: PollChoice, child_name: str, child_gender: str, friend_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=friend_name))
    nose = world.add(Entity(id="nose", type="thing", label="nose-light", phrase="a tiny nose-light"))
    banner = world.add(Entity(id="banner", type="thing", label=choice.label, phrase=f"the {choice.label}"))
    world.facts["choice"] = choice
    world.facts["child"] = child
    world.facts["friend"] = friend
    world.facts["nose"] = nose
    world.facts["banner"] = banner

    child.memes["joy"] += 1
    nose.meters["glow"] = 1.0

    world.say(f"In {setting.place}, {child_name} came in with a grin so bright,")
    world.say(f"for the class held a poll to pick a banner for the night.")
    world.say(f"{child_name} loved the {choice.label}, with its {choice.rhyme} kind of glow,")
    world.say(f"and {friend_name} liked a different one, which made the votes run slow.")

    world.para()
    world.say(f"The poll began in {setting.place}, neat as a paper row.")
    child.memes["worry"] += 1
    child.memes["awkward"] += 1
    friend.memes["pride"] += 1
    world.say(f"One quick reflex made {child_name} tap the desk before they knew,")
    world.say("and the nose-light dimmed to a sleepy little blue.")

    propagate(world, narrate=True)

    world.para()
    outcome = predict_outcome(world, child, friend)
    if outcome["dim"]:
        world.say(f"{child_name} saw the dim nose and felt a prickly ache inside,")
        world.say(f"so {child_name} took a breath and let the sharp words slide.")
    world.say(f"{child_name} said, “I was too quick. I want us both to shine.”")
    child.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    friend.memes["pride"] = max(0.0, friend.memes["pride"] - 0.5)
    child.memes["hurt"] += 1
    child.memes["worry"] += 0.5
    propagate(world, narrate=True)

    world.para()
    if world.facts["child"].memes["reconcile"] < 1.0:
        child.memes["warmth"] += 1
        friend.memes["warmth"] += 1
        child.memes["hurt"] = 0.0
        friend.memes["pride"] = max(0.0, friend.memes["pride"] - 0.3)
        world.say(f"Then {child_name} and {friend_name} made up with a friendly nod,")
        world.say(f"and the poll turned kind again, like flowers after a frost gone odd.")
        child.memes["reconcile"] += 1
        friend.memes["reconcile"] += 1
        nose.meters["glow"] = 1.0

    world.say(f"At last the class chose {choice.label}, and the nose-light glowed just right,")
    world.say(f"with reconciliation warm, and the room all soft and bright.")
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(s, c) for s in SETTINGS for c in CHOICES]


@dataclass
class RegisterItem:
    id: str
    label: str
    attrs: dict[str, str] = field(default_factory=dict)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("label", cid, c.label))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C) :- setting(S), choice(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    setting: str
    choice: str
    child: str
    gender: str
    friend: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about a poll, a nose-light, a reflex, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--child")
    ap.add_argument("--friend")
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
    choice = args.choice or rng.choice(list(CHOICES))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in FRIENDS if n != child])
    if (args.setting and args.choice) and (args.setting, args.choice) not in valid_combos():
        raise StoryError("The poll choice does not fit this setting.")
    return StoryParams(setting=setting, choice=choice, child=child, gender=gender, friend=friend)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    choice = f["choice"]
    return [
        QAItem(
            question=f"Why did {child.label} feel worried during the poll?",
            answer=f"{child.label} felt worried because a quick reflex made the moment awkward, and the nose-light dimmed when the feelings got heavy.",
        ),
        QAItem(
            question=f"What helped {child.label} and {friend.label} make up?",
            answer=f"They talked gently, apologized, and chose reconciliation instead of staying upset.",
        ),
        QAItem(
            question=f"What won the class poll?",
            answer=f"The class chose the {choice.label}, and the room ended warm and happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a poll?",
            answer="A poll is a count of choices or votes so a group can pick one option together.",
        ),
        QAItem(
            question="What is a reflex?",
            answer="A reflex is a quick action your body does before you have time to think, like a flinch or a tap.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people make up after a disagreement and feel friendly again.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child named {f["child"].label} about a school poll and a dim nose-light.',
        f"Tell a gentle rhyming tale where a quick reflex makes things awkward, but reconciliation brings the friends back together.",
        f"Write a child-friendly story that includes the words poll, nose-dim, and reflex, and ends with a happy vote.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHOICES[params.choice], params.child, params.gender, params.friend)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for s, c in asp_valid_combos():
            print(s, c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting in SETTINGS:
            for choice in CHOICES:
                p = StoryParams(setting=setting, choice=choice, child="Mia", gender="girl", friend="Pip")
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
