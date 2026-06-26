#!/usr/bin/env python3
"""
A standalone storyworld: privacy, extricate, and reconciliation in a nursery-rhyme-like home.

Seed tale:
---
A little child kept a tiny secret tucked in a pillow pocket: a glittery key to a music box.
A curious sibling tried to peek, and the child felt their privacy was broken. Later, a ribbon
snagged the key inside the pillow seam, and the two children had to work together to extricate it.
When the key was freed, they made up, shared a small song, and agreed that private things can stay
private, while shared joys can be shared kindly.

This world turns that premise into a small simulation with meters for physical state and memes
for feelings, plus a declarative ASP twin for reasonableness checks.
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
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    stuck_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    afford_paper_craft: bool = True
    afford_hide_and_seek: bool = True


@dataclass
class ObjectDef:
    label: str
    phrase: str
    hiding_place: str
    risk_kind: str
    secret: bool = True


@dataclass
class TensionDef:
    id: str
    trigger: str
    verb: str
    rhyme: str
    problem: str


@dataclass
class RescueGear:
    id: str
    label: str
    verb: str
    tool_kind: str
    fix_kind: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.events: list[str] = []

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
        import copy as _copy
        nw = World(self.setting)
        nw.entities = _copy.deepcopy(self.entities)
        nw.fired = set(self.fired)
        nw.paragraphs = [[]]
        nw.facts = dict(self.facts)
        return nw


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _bump_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _bump_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _clear_meme(ent: Entity, key: str) -> None:
    ent.memes[key] = 0.0


def _peek(world: World, child: Entity, secret: Entity, sibling: Entity) -> None:
    if secret.hidden_in and secret.hidden_in == "pillow pocket":
        _bump_meme(child, "privacy", 1.0)
        _bump_meme(sibling, "curiosity", 1.0)
        world.say(
            f"{sibling.id} leaned close to peek. {child.id} held their breath, "
            f"for the little secret in the pillow pocket was private."
        )


def _hide(world: World, child: Entity, secret: Entity) -> None:
    secret.hidden_in = "pillow pocket"
    _bump_meme(child, "privacy", 1.0)
    world.say(
        f"{child.id} tucked the {secret.label} deep in the pillow pocket, "
        f"where quiet dreams and small secrets often hide."
    )


def _snag(world: World, secret: Entity, ribbon: Entity) -> None:
    if secret.hidden_in == "pillow pocket":
        secret.stuck_in = "pillow seam"
        ribbon.hidden_in = "pillow seam"
        world.say(
            f"But oh dear, a ribbon twirled and tangled tight. The {secret.label} "
            f"caught in the pillow seam like a star in a kite."
        )


def _extricate(world: World, child: Entity, sibling: Entity, secret: Entity, gear: RescueGear) -> None:
    if secret.stuck_in != "pillow seam":
        return
    _bump_meme(child, "hope", 1.0)
    _bump_meme(sibling, "helpfulness", 1.0)
    secret.stuck_in = None
    secret.hidden_in = None
    world.say(
        f"{child.id} and {sibling.id} used a tiny {gear.label} to {gear.verb} the {secret.label} free. "
        f"The {gear.label} was gentle and small, just right for the seam."
    )


def _reconcile(world: World, child: Entity, sibling: Entity, secret: Entity) -> None:
    _clear_meme(child, "privacy")
    _clear_meme(child, "hurt")
    _clear_meme(sibling, "curiosity")
    _bump_meme(child, "love", 1.0)
    _bump_meme(sibling, "love", 1.0)
    _bump_meme(child, "reconciliation", 1.0)
    _bump_meme(sibling, "reconciliation", 1.0)
    world.say(
        f"Then they paused, and the room went soft and sweet. "
        f'{child.id} said, "I wanted privacy, not a fight." '
        f'{sibling.id} said, "I only wanted to see." '
        f"Together they smiled, and reconciliation came neat."
    )
    world.say(
        f"At last they shared the music box song, while still keeping some things private, "
        f"like a little lock on a treasured dream."
    )


SETTING = Setting(place="the nursery")
SECRET_OBJECTS = {
    "music_box_key": ObjectDef(
        label="music box key",
        phrase="a glittery little key",
        hiding_place="pillow pocket",
        risk_kind="privacy",
    ),
    "paper_note": ObjectDef(
        label="paper note",
        phrase="a folded secret note",
        hiding_place="pillow pocket",
        risk_kind="privacy",
    ),
}
TENSIONS = {
    "peek": TensionDef(
        id="peek",
        trigger="peek",
        verb="peek at",
        rhyme="sweet",
        problem="privacy",
    ),
}
GEAR = {
    "needle": RescueGear(
        id="needle",
        label="needle",
        verb="extricate",
        tool_kind="needle",
        fix_kind="seam",
    ),
    "twine": RescueGear(
        id="twine",
        label="twine loop",
        verb="extricate",
        tool_kind="twine",
        fix_kind="seam",
    ),
}

CHILD_NAMES = ["Mia", "Nora", "Lily", "Theo", "Ben", "Ava"]
SIBLING_NAMES = ["Pip", "Zig", "Milo", "Dot", "June", "Bea"]


@dataclass
class StoryParams:
    setting: str = "nursery"
    secret: str = "music_box_key"
    child_name: str = "Mia"
    sibling_name: str = "Pip"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about privacy, extricate, and reconciliation.")
    ap.add_argument("--setting", choices=["nursery"], default="nursery")
    ap.add_argument("--secret", choices=sorted(SECRET_OBJECTS), default=None)
    ap.add_argument("--child-name")
    ap.add_argument("--sibling-name")
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


def valid_combos() -> list[tuple[str, str]]:
    return [("nursery", sid) for sid in SECRET_OBJECTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    secret = args.secret or rng.choice(list(SECRET_OBJECTS))
    if secret not in SECRET_OBJECTS:
        raise StoryError("unknown secret object")
    child = args.child_name or rng.choice(CHILD_NAMES)
    sibling = args.sibling_name or rng.choice([n for n in SIBLING_NAMES if n != child])
    return StoryParams(setting="nursery", secret=secret, child_name=child, sibling_name=sibling)


def reasonableness_gate(params: StoryParams) -> None:
    if params.secret not in SECRET_OBJECTS:
        raise StoryError("The secret object is not part of this small nursery world.")


ASP_RULES = r"""
setting(nursery).
secret(music_box_key).
secret(paper_note).

private(Secret) :- secret(Secret).
can_reconcile(Secret) :- private(Secret).
valid_story(S, Secret) :- setting(S), secret(Secret), can_reconcile(Secret).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", "nursery")]
    for sid in SECRET_OBJECTS:
        lines.append(asp.fact("secret", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == {(a, b) for a, b in cl}:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("python:", sorted(py))
    print("clingo :", sorted(cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(SETTING)
    child = world.add(Entity(id=params.child_name, kind="character", type="girl"))
    sibling = world.add(Entity(id=params.sibling_name, kind="character", type="boy"))
    secret_def = SECRET_OBJECTS[params.secret]
    secret = world.add(Entity(id="secret", type=secret_def.label, label=secret_def.label, phrase=secret_def.phrase))
    ribbon = world.add(Entity(id="ribbon", type="ribbon", label="ribbon"))
    gear = GEAR["needle"]

    world.say(
        f"In the nursery bright and round, {child.id} kept a secret safe and sound."
    )
    _hide(world, child, secret)
    world.para()
    world.say(
        f"{sibling.id} came tiptoe, curious and light, and tried to peek where the secret might."
    )
    _peek(world, child, secret, sibling)
    world.para()
    _snag(world, secret, ribbon)
    _extricate(world, child, sibling, secret, gear)
    world.para()
    _reconcile(world, child, sibling, secret)

    world.facts.update(
        child=child,
        sibling=sibling,
        secret=secret,
        ribbon=ribbon,
        gear=gear,
        resolved=True,
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short nursery-rhyme story about privacy, a stuck secret, and reconciliation.',
        f"Tell a gentle story where {f['child'].id} wants privacy, {f['sibling'].id} gets curious, and they extricate a {f['secret'].label}.",
        "Write a rhyming, child-friendly story that ends with friends making up after a small misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    sibling = f["sibling"]
    secret = f["secret"]
    return [
        QAItem(
            question=f"Why did {child.id} feel upset when {sibling.id} tried to peek?",
            answer=f"{child.id} wanted privacy for the {secret.label}, so peeking felt unkind and too nosy.",
        ),
        QAItem(
            question=f"What got stuck before the children could extricate it?",
            answer=f"The {secret.label} got caught in the pillow seam and had to be extricated carefully.",
        ),
        QAItem(
            question=f"How did {child.id} and {sibling.id} finish the story?",
            answer=f"They talked kindly, shared the music-box song, and reached reconciliation after the little trouble.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What does privacy mean?",
        answer="Privacy means having a quiet space or a secret that others should not stare at or touch without permission.",
    ),
    QAItem(
        question="What does extricate mean?",
        answer="To extricate something means to free it carefully when it is caught or stuck.",
    ),
    QAItem(
        question="What is reconciliation?",
        answer="Reconciliation means making up after a disagreement so people can be kind again.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.stuck_in:
            bits.append(f"stuck_in={e.stuck_in}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


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
    StoryParams(setting="nursery", secret="music_box_key", child_name="Mia", sibling_name="Pip"),
    StoryParams(setting="nursery", secret="paper_note", child_name="Nora", sibling_name="Dot"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid stories:")
        for c in combos:
            print(" ", c)
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = rng.randrange(2**31)
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
