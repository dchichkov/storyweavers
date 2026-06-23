#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/tyrannosaurus_surprise_sharing_mystery.py
================================================================================

A small storyworld about a child-friendly mystery: a tyrannosaurus surprise,
a shared discovery, and the moment the clues add up.

The seed tale behind this world:
---
Mira and Jun were in the museum garden when they found tiny muddy prints beside
the fountain. A gardener said a surprise had been hiding there all morning. The
children followed the clues past a cedar tree, behind a sign, and under a bench.
There they found a paper crate with a note: "For the two detectives."

Inside was a toy tyrannosaurus, two berry buns, and one brass key. Mira wanted
the toy, Jun wanted the key, and both wanted the mystery to make sense. Instead
of grabbing, they shared the crate, compared the clues, and discovered the key
opened the little garden gate. Behind it was a surprise picnic from the keeper,
set out for both of them. The tyrannosaurus sat in the middle like a silly
guard, and the children laughed.

World model:
- typed entities with meters and memes
- clue-following and reveal beats drive the prose
- surprise is something hidden becoming visible
- sharing is a state change: one finding becomes two happy participants
- mystery means the solution is assembled from clues, not narrated as a static
  paragraph with swapped names

The storyworld supports:
- default generation, -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp
- a Python reasonableness gate and an inline ASP twin
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
    owner: str = ""
    caretaker: str = ""
    hidden: bool = False
    collectible: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    outdoors: bool = True
    features: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    phrase: str
    reveals: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    hidden_where: str
    hidden_reason: str
    reveal_word: str = "surprise"
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    splits_into: int
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_reveal(world: World) -> list[str]:
    out: list[str] = []
    for clue in world.entities.values():
        if clue.kind != "clue":
            continue
        if clue.meters["seen"] < THRESHOLD:
            continue
        sig = ("reveal", clue.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if clue.attrs.get("unlocks"):
            key = clue.attrs["unlocks"]
            if key in world.entities:
                world.get(key).meters["understood"] += 1
        out.append(clue.reveals)
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.entities.get("shareitem")
    if not treasure or treasure.meters["shared"] < THRESHOLD:
        return out
    sig = ("share", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    out.append("__shared__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    s = world.entities.get("surprise")
    if not s or s.meters["found"] < THRESHOLD:
        return out
    sig = ("surprise", s.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["surprise"] += 1
    out.append("__surprise__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_reveal, _r_surprise, _r_share):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(setting: Setting, surprise: Surprise, share: ShareItem) -> bool:
    return "mystery" in setting.features and "sharing" in setting.features and "surprise" in setting.features


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, st in SETTINGS.items():
        for x in SURPRISES:
            for sh in SHARES:
                if valid_combo(st, SURPRISES[x], SHARES[sh]):
                    combos.append((sid, x, sh))
    return combos


@dataclass
class StoryParams:
    setting: str = "garden"
    surprise: str = "crate"
    share: str = "berries"
    child1: str = "Mira"
    child1_gender: str = "girl"
    child2: str = "Jun"
    child2_gender: str = "boy"
    helper: str = "gardener"
    seed: Optional[int] = None


SETTINGS = {
    "garden": Setting(place="the museum garden", outdoors=True, features={"mystery", "sharing", "surprise"}),
    "courtyard": Setting(place="the quiet courtyard", outdoors=True, features={"mystery", "sharing", "surprise"}),
    "greenhouse": Setting(place="the greenhouse path", outdoors=False, features={"mystery", "sharing", "surprise"}),
}

SURPRISES = {
    "crate": Surprise(
        id="surprise",
        label="paper crate",
        phrase="a paper crate tucked behind the fountain",
        hidden_where="behind the fountain",
        hidden_reason="it was waiting for the right detectives",
        reveal_word="surprise",
        tags={"surprise", "mystery"},
    ),
    "benchbox": Surprise(
        id="surprise",
        label="wooden box",
        phrase="a wooden box under the bench",
        hidden_where="under the bench",
        hidden_reason="it was set out to be found",
        reveal_word="surprise",
        tags={"surprise", "mystery"},
    ),
}

SHARES = {
    "berries": ShareItem(id="shareitem", label="berry buns", phrase="two berry buns", splits_into=2, tags={"sharing"}),
    "cookies": ShareItem(id="shareitem", label="lemon cookies", phrase="two lemon cookies", splits_into=2, tags={"sharing"}),
}

NAMES = ["Mira", "Jun", "Tali", "Noa", "Pico", "Iris", "Luca", "Sana"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a mystery surprise and a shared ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--child1")
    ap.add_argument("--child2")
    ap.add_argument("--helper")
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
              and (args.surprise is None or c[1] == args.surprise)
              and (args.share is None or c[2] == args.share)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, surprise, share = rng.choice(sorted(combos))
    child1 = args.child1 or rng.choice(NAMES)
    child2 = args.child2 or rng.choice([n for n in NAMES if n != child1])
    helper = args.helper or rng.choice(["gardener", "keeper", "guide"])
    return StoryParams(setting=setting, surprise=surprise, share=share, child1=child1, child2=child2, helper=helper)


def tell(setting: Setting, surprise: Surprise, share: ShareItem, child1: str, child1_gender: str,
         child2: str, child2_gender: str, helper: str) -> World:
    world = World(setting)
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, label=child1))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, label=child2))
    h = world.add(Entity(id="helper", kind="character", type="adult", label=f"the {helper}"))
    crate = world.add(Entity(id="surprise", kind="thing", type="crate", label=surprise.label, phrase=surprise.phrase, hidden=True, collectible=True, tags=surprise.tags))
    item = world.add(Entity(id="shareitem", kind="thing", type="treat", label=share.label, phrase=share.phrase, collectible=True, plural=True, tags=share.tags))
    world.facts.update(child1=a, child2=b, helper=h, surprise=crate, share=item, setting=setting)

    world.say(f"{a.id} and {b.id} were walking through {setting.place} when they noticed a clue trail.")
    world.say(f"First they found a muddy mark near the fountain, then another clue {surprise.hidden_where}.")
    world.para()
    a.meters["curiosity"] += 1
    b.meters["curiosity"] += 1
    world.say(f"They followed the clues carefully because it felt like a mystery, not a race.")
    world.say(f"The last clue pointed to {surprise.phrase}, and that was a real {surprise.reveal_word}.")
    crate.meters["found"] += 1
    crate.hidden = False
    propagate(world, narrate=True)
    world.para()
    world.say(f"Inside was {share.phrase}, but only one bundle could not stay one bundle for long.")
    share_ent = world.get("shareitem")
    share_ent.meters["shared"] += 1
    a.meters["shares"] += 1
    b.meters["shares"] += 1
    world.say(f"{a.id} and {b.id} chose to share it, so each child got one part and one smile.")
    world.say(f"{helper} laughed, because the tiny mystery had turned into a kind ending.")
    world.say(f"Beside the crate sat a toy tyrannosaurus, as if it had been guarding the secret all morning.")
    for kid in (a, b):
        kid.memes["satisfaction"] += 1
    world.facts["resolved"] = True
    return world


KNOWLEDGE = {
    "surprise": [("What is a surprise?", "A surprise is something you did not expect. It feels exciting when it is finally found.")],
    "sharing": [("What does sharing mean?", "Sharing means letting more than one person enjoy the same thing. It helps everyone feel included.")],
    "mystery": [("What is a mystery?", "A mystery is something puzzling that you solve by following clues.")],
    "tyrannosaurus": [("What is a tyrannosaurus?", "A tyrannosaurus was a very big meat-eating dinosaur. Stories often use toy tyrannosaurus figures because they are exciting but safe.")],
}


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, h, s, sh = f["child1"], f["child2"], f["helper"], f["surprise"], f["share"]
    return [
        QAItem(
            f"Who found the clue trail in {world.setting.place}?",
            f"{a.id} and {b.id} found it together, and they kept going because they were solving a mystery. The clues mattered more than rushing, so both children stayed with the search.",
        ),
        QAItem(
            f"What was the surprise hiding behind the clues?",
            f"It was {s.phrase}. That was the hidden thing the children had to uncover before the story could turn into sharing.",
        ),
        QAItem(
            f"What did the children do when they found {sh.phrase}?",
            f"They shared it. That meant each child got part of it, and both of them could enjoy the treat without anyone being left out.",
        ),
        QAItem(
            f"Why did the toy tyrannosaurus matter at the end?",
            f"It made the ending feel playful and surprising. It sat beside the crate like a goofy guard, proving the mystery had been solved and the prize had been found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    for e in world.entities.values():
        tags |= set(e.tags)
    tags.add("tyrannosaurus")
    out: list[QAItem] = []
    for key in ["mystery", "surprise", "sharing", "tyrannosaurus"]:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[key])
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["child1"], f["child2"]
    return [
        'Write a short mystery story for a young child that includes a tyrannosaurus, a surprise, and sharing.',
        f"Tell a gentle mystery where {a.id} and {b.id} follow clues, discover a hidden surprise, and share what they find.",
        "Write a child-friendly detective story where the ending proves the clue trail was solved by sharing.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, X, H) :- setting(S), surprise(X), share(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for x in SURPRISES:
        lines.append(asp.fact("surprise", x))
    for h in SHARES:
        lines.append(asp.fact("share", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import tempfile
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid_combos().")
        ok = False
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        ok = False
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise: {params.surprise}")
    if params.share not in SHARES:
        raise StoryError(f"Unknown share item: {params.share}")
    world = tell(
        SETTINGS[params.setting],
        SURPRISES[params.surprise],
        SHARES[params.share],
        params.child1,
        params.child1_gender,
        params.child2,
        params.child2_gender,
        params.helper,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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
    StoryParams(setting="garden", surprise="crate", share="berries", child1="Mira", child1_gender="girl", child2="Jun", child2_gender="boy", helper="gardener"),
    StoryParams(setting="courtyard", surprise="benchbox", share="cookies", child1="Tali", child1_gender="girl", child2="Noa", child2_gender="boy", helper="guide"),
    StoryParams(setting="greenhouse", surprise="crate", share="cookies", child1="Iris", child1_gender="girl", child2="Luca", child2_gender="boy", helper="keeper"),
]


def build_parser_extra() -> argparse.ArgumentParser:
    return build_parser()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
