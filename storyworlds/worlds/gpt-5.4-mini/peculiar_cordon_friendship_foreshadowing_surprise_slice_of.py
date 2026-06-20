#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/peculiar_cordon_friendship_foreshadowing_surprise_slice_of.py
=============================================================================================

A small slice-of-life storyworld about two friends, a peculiar neighborhood
cordon, a gentle bit of foreshadowing, and a surprise that turns out to be kind.

Seed words:
- peculiar
- cordon

Features:
- Friendship
- Foreshadowing
- Surprise

Style:
- Slice of life
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"interest": 0.0, "worry": 0.0, "warmth": 0.0, "surprise": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "care": 0.0, "joy": 0.0, "patience": 0.0}

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
class Theme:
    id: str
    place: str
    scene: str
    detail: str
    quiet_line: str
    ending_image: str
    friendship_line: str


@dataclass
class Cordon:
    id: str
    label: str
    reason: str
    peculiar_detail: str
    word: str = "cordon"


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    effect: str
    gift: str


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.get("cordon").meters["interest"] >= THRESHOLD and ("worry", "cordon") not in world.fired:
        world.fired.add(("worry", "cordon"))
        for kid in (world.get("child_a"), world.get("child_b")):
            kid.memes["curiosity"] += 1
            kid.meters["interest"] += 1
        out.append("__worry__")
    return out


def _r_warmth(world: World) -> list[str]:
    out: list[str] = []
    if world.get("surprise").meters["surprise"] >= THRESHOLD and ("warmth", "surprise") not in world.fired:
        world.fired.add(("warmth", "surprise"))
        for kid in (world.get("child_a"), world.get("child_b")):
            kid.memes["joy"] += 1
            kid.meters["warmth"] += 1
        out.append("__warmth__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("warmth", "social", _r_warmth),
]


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


def looks_peculiar(cordon: Cordon) -> bool:
    return True


def should_surprise(theme: Theme, cordon: Cordon, surprise: Surprise) -> bool:
    return looks_peculiar(cordon) and bool(theme.friendship_line) and bool(surprise.reveal)


def tell(theme: Theme, cordon: Cordon, surprise: Surprise,
         a_name: str = "Mina", a_gender: str = "girl",
         b_name: str = "Jules", b_gender: str = "boy",
         parent_type: str = "mother",
         seed_note: str = "") -> World:
    if not should_surprise(theme, cordon, surprise):
        raise StoryError("This combination does not support a believable foreshadowing surprise.")

    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_gender, role="friend", traits=["kind", "patient"]))
    b = world.add(Entity(id=b_name, kind="character", type=b_gender, role="friend", traits=["kind", "curious"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    c = world.add(Entity(id="cordon", kind="thing", type="thing", label=cordon.label))
    s = world.add(Entity(id="surprise", kind="thing", type="thing", label=surprise.label))

    c.meters["interest"] = 1.0
    s.meters["surprise"] = 1.0
    world.facts["seed_note"] = seed_note

    world.say(
        f"On an ordinary afternoon, {a.id} and {b.id} walked down {theme.place}. "
        f"{theme.scene} {theme.detail}"
    )
    world.say(
        f"They noticed a {cordon.label} that looked {cordon.peculiar_detail}, and that made the day feel a little peculiar."
    )
    world.say(
        f"{a.id} and {b.id} slowed down beside it. {theme.quiet_line}"
    )

    world.para()
    a.memes["patience"] += 1
    b.memes["patience"] += 1
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f'{a.id} whispered, "Why is there a {cordon.word} here?" '
        f'{b.id} shrugged, but {b.id} smiled instead of worrying.'
    )
    world.say(
        f"{theme.friendship_line} They decided to wait and see, because waiting together felt easier than guessing alone."
    )

    world.para()
    propagate(world, narrate=False)
    if seed_note:
        world.say(f"Later, {seed_note} floated back to them like a clue.")
    if c.meters["interest"] >= THRESHOLD:
        world.say(
            f"The {cordon.word} turned out not to be a warning at all, but a neat little way to keep people out while someone worked."
        )
    else:
        world.say(
            f"The {cordon.word} stayed quiet, and the friends stayed quiet with it."
        )

    world.para()
    if surprise.reveal:
        s.meters["surprise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {parent.label_word.capitalize()} came over with a smile and lifted the cover. "
        f"The surprise was {surprise.reveal}."
    )
    world.say(
        f"{surprise.effect.capitalize()} {surprise.gift} made both children laugh, and even the {cordon.word} seemed less strange now."
    )
    world.say(
        f"In the end, {a.id} and {b.id} walked home side by side with the warm feeling that comes from sharing a secret and a snack."
    )
    world.say(
        f"{theme.ending_image.capitalize()} {theme.scene.lower()}, and the whole day felt gentle and bright."
    )

    world.facts.update(
        a=a, b=b, parent=parent, theme=theme, cordon=cordon, surprise=surprise,
        outcome="surprised", peculiar=True, cordon_seen=True
    )
    return world


THEMES = {
    "sidewalk": Theme(
        "sidewalk",
        "the sidewalk",
        "It was a calm little street, with bicycle bells far away and a baker's window full of bread.",
        "A breeze moved the leaves, and the afternoon felt unhurried.",
        "They could hear a radio humming from an open kitchen window.",
        "The sunset left a pale gold stripe on the pavement.",
        "Friendship made the waiting feel shorter."
    ),
    "market": Theme(
        "market",
        "the small market lane",
        "It was a busy little lane, with fruit boxes stacked near the doors and neighbors saying hello.",
        "A cat slept on a crate, and the warm air smelled like oranges.",
        "They watched people carry flowers and paper bags past them.",
        "Lantern light winked on in the shop windows.",
        "Friendship made the waiting feel shorter."
    ),
    "parkpath": Theme(
        "parkpath",
        "the park path",
        "It was a green path beside the swings, with ducks at the pond and kids calling from the hill.",
        "A stroller rolled by slowly, and the grass looked freshly watered.",
        "They could hear sneakers scuffing on the path behind them.",
        "The last sun made the pond shine like a coin.",
        "Friendship made the waiting feel shorter."
    ),
}

CORDONS = {
    "flowers": Cordon(
        "flowers",
        "a cordon of flower pots",
        "someone was keeping a fresh planting safe",
        "made of bright clay pots and a tiny painted sign"
    ),
    "cones": Cordon(
        "cones",
        "a cordon of orange cones",
        "someone had just cleaned the path",
        "made of small cones and a strip of ribbon"
    ),
    "rope": Cordon(
        "rope",
        "a cordon of rope and posts",
        "someone was fixing the ground nearby",
        "made of rope that bobbed between short wooden posts"
    ),
}

SURPRISES = {
    "cookies": Surprise(
        "cookies",
        "a tin of lemon cookies",
        "it was not danger at all, only a treat waiting for the neighbors",
        "The smell of lemon and sugar drifted out",
    ),
    "kittens": Surprise(
        "kittens",
        "two sleepy kittens",
        "it was a tiny hiding place for the neighbor's new kittens",
        "Two soft mews answered from inside",
    ),
    "cards": Surprise(
        "cards",
        "a stack of thank-you cards",
        "it was a surprise from the corner shopkeeper for everyone who helped",
        "The paper edges flashed with bright ribbon",
    ),
}

GIRL_NAMES = ["Mina", "Lina", "Tess", "Nora", "Lumi", "Rae", "Ivy", "Zuri"]
BOY_NAMES = ["Jules", "Owen", "Pax", "Noel", "Eli", "Finn", "Theo", "Milo"]


@dataclass
class StoryParams:
    theme: str
    cordon: str
    surprise: str
    child_a: str
    child_a_gender: str
    child_b: str
    child_b_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for c in CORDONS:
            for s in SURPRISES:
                if should_surprise(THEMES[t], CORDONS[c], SURPRISES[s]):
                    combos.append((t, c, s))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with friendship, foreshadowing, and surprise.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--cordon", choices=CORDONS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
              if (args.theme is None or c[0] == args.theme)
              and (args.cordon is None or c[1] == args.cordon)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, cordon, surprise = rng.choice(sorted(combos))
    name_a = args.name_a or rng.choice(GIRL_NAMES)
    name_b = args.name_b or rng.choice([n for n in BOY_NAMES if n != name_a])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(theme, cordon, surprise, name_a, "girl", name_b, "boy", parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a young child that includes the word "peculiar" and the word "{f["cordon"].word}".',
        f"Tell a gentle friendship story where {f['a'].id} and {f['b'].id} notice a peculiar {f['cordon'].label}, wait together, and get a kind surprise.",
        f"Write a small everyday story about two friends, a strange-looking cordon, and a surprise that turns out to be nice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    cordon = f["cordon"]
    surprise = f["surprise"]
    theme = f["theme"]
    items = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {a.id} and {b.id}, two friends who were walking together. They noticed something peculiar and stayed curious side by side."
        ),
        QAItem(
            question="What did the children notice?",
            answer=f"They noticed {cordon.label}. It looked {cordon.peculiar_detail}, so it felt peculiar even before anyone explained it."
        ),
        QAItem(
            question="Why did they wait instead of leaving right away?",
            answer=f"They waited because they were friends and wanted to figure it out together. Waiting let them share the guessing and keep calm."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {surprise.reveal}. It turned the strange little cordon into something friendly and ordinary."
        ),
    ]
    items.append(
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a warm, ordinary walk home after the surprise. The friends felt closer, and the peculiar cordon no longer seemed puzzling."
        )
    )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does peculiar mean?",
            answer="Peculiar means unusual or a little strange. It is the kind of word you use when something does not look ordinary."
        ),
        QAItem(
            question="What is a cordon?",
            answer="A cordon is a line or barrier that keeps people from going past a certain spot. People sometimes make one with cones, rope, or pots."
        ),
        QAItem(
            question="Why do friends wait together?",
            answer="Friends wait together so neither one feels alone. Sharing the wait can make a surprise feel more fun and less scary."
        ),
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("sidewalk", "flowers", "cookies", "Mina", "girl", "Jules", "boy", "mother"),
    StoryParams("market", "cones", "cards", "Lina", "girl", "Owen", "boy", "father"),
    StoryParams("parkpath", "rope", "kittens", "Tess", "girl", "Eli", "boy", "mother"),
]


ASP_RULES = r"""
valid(T, C, S) :- theme(T), cordon(C), surprise(S), surprising(C, S).
surprising(C, S) :- cordon(C), surprise(S), peculiar_cordon(C), friendly_reveal(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid in CORDONS:
        lines.append(asp.fact("cordon", cid))
        lines.append(asp.fact("peculiar_cordon", cid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("friendly_reveal", sid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos")
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, cordon=None, surprise=None, parent=None, name_a=None, name_b=None), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], CORDONS[params.cordon], SURPRISES[params.surprise],
                 params.child_a, params.child_a_gender, params.child_b, params.child_b_gender,
                 params.parent)
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t, c, s in asp_valid_combos():
            print(f"  {t:10} {c:10} {s}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_a} & {p.child_b}: {p.cordon} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
