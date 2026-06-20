#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/friday_toxic_humor_conflict_folk_tale.py
=======================================================================

A standalone story world for a tiny folk-tale domain about a Friday market,
a funny but toxic joke, a hurt feeling, and a wiser way to laugh together.

The world is built to make small, complete stories with:
- a clear setup at the village on Friday,
- a tension beat where humor turns toxic and causes conflict,
- a turn where a careful elder changes the joke's shape,
- an ending image that proves the mood changed.

The story always includes the words "friday" and "toxic" in child-facing prose.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa", "mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Humor:
    id: str
    setup: str
    punchline: str
    kind: str = "gentle"
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    kind: str
    heat: int
    cause: str
    fallout: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    kind: str
    strength: int
    action: str
    ending: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["hurt"] < THRESHOLD or e.id in {"grandma"}:
            continue
        sig = ("hurt", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["sad"] += 1
        e.memes["distance"] += 1
        out.append("__hurt__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("toxic_spoken") and not world.facts.get("mended"):
        for kid in ("mina", "pavel"):
            ent = world.get(kid)
            ent.memes["conflict"] += 1
            ent.meters["hurt"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("fear", "social", _r_fear), Rule("conflict", "social", _r_conflict)]


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


def friday_market(world: World, child_a: Entity, child_b: Entity) -> None:
    child_a.memes["joy"] += 1
    child_b.memes["joy"] += 1
    world.say(
        f"On friday, the village market filled the square with apples, ribbons, and warm bread. "
        f"{child_a.id} and {child_b.id} skipped between the carts while the crows watched from the fence."
    )
    world.say(
        f'The two children loved the little crowd because every stall had a joke, a song, or a story.'
    )


def tempting_joke(world: World, joker: Entity, other: Entity, humor: Humor) -> None:
    joker.memes["playful"] += 1
    world.say(
        f'{joker.id} grinned and said, "{humor.setup}" '
        f'The punchline was so silly that even the fishmonger snorted.'
    )


def toxic_turn(world: World, joker: Entity, other: Entity, conflict: Conflict) -> None:
    joker.meters["toxic"] += 1
    world.facts["toxic_spoken"] = True
    world.say(
        f"But then the joke turned toxic. {joker.id} added, \"{conflict.cause}\" "
        f'and the smile on {other.id}\'s face faded right away.'
    )
    propagate(world, narrate=False)


def hurt_reaction(world: World, hurt_child: Entity, joker: Entity, conflict: Conflict) -> None:
    hurt_child.memes["anger"] += 1
    hurt_child.memes["hurt"] += 1
    world.say(
        f'{hurt_child.id} crossed {hurt_child.pronoun("possessive")} arms. '
        f'"That was not funny," {hurt_child.pronoun()} said. '
        f'{conflict.fallout.capitalize()}'
    )


def grandma_steps_in(world: World, grandma: Entity, a: Entity, b: Entity, humor: Humor, remedy: Remedy) -> None:
    world.say(
        f"Then {grandma.label_word} came from the porch with a basket of plums. "
        f'"A joke can be a feather," {grandma.pronoun()} said, '
        f'"or it can be a thorn if it pricks a friend."'
    )
    world.say(
        f'{grandma.id} listened to both children, then showed them {remedy.action}. '
        f'The new version kept the same funny shape, but it no longer stung.'
    )
    world.facts["mended"] = True


def make_right(world: World, grandma: Entity, a: Entity, b: Entity, remedy: Remedy) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.meters["hurt"] = 0.0
    b.meters["hurt"] = 0.0
    world.say(
        f'{a.id} tried the new joke first, and {b.id} laughed without flinching. '
        f'{remedy.ending.capitalize()}'
    )
    world.say(
        f"By the end, the market sounded bright again: hooves clipped, bread crackled, "
        f"and the children shared apples instead of sharp words."
    )


def tell(humor: Humor, conflict: Conflict, remedy: Remedy, a_name: str = "Mina", b_name: str = "Pavel") -> World:
    world = World()
    mina = world.add(Entity(id=a_name, kind="character", type="girl", role="jester", traits=["quick", "bright"]))
    pavel = world.add(Entity(id=b_name, kind="character", type="boy", role="listener", traits=["sensitive", "kind"]))
    grandma = world.add(Entity(id="grandma", kind="character", type="grandmother", role="elder", label="grandma"))

    friday_market(world, mina, pavel)
    world.para()
    tempting_joke(world, mina, pavel, humor)
    toxic_turn(world, mina, pavel, conflict)
    hurt_reaction(world, pavel, mina, conflict)
    world.para()
    grandma_steps_in(world, grandma, mina, pavel, humor, remedy)
    make_right(world, grandma, mina, pavel, remedy)

    world.facts.update(
        mina=mina, pavel=pavel, grandma=grandma,
        humor=humor, conflict=conflict, remedy=remedy,
        ending="mended",
    )
    return world


HUMORS = {
    "goose": Humor(
        "goose",
        "Why did the goose wear a bell?",
        "So the pond would know it was coming!",
        tags={"humor", "folk"},
    ),
    "boots": Humor(
        "boots",
        "Why did the boot go dancing?",
        "Because it had a sole to spare!",
        tags={"humor", "folk"},
    ),
    "turnip": Humor(
        "turnip",
        "Why did the turnip sit in the cart?",
        "It wanted to be a little root of fun!",
        tags={"humor", "folk"},
    ),
}

CONFLICTS = {
    "tease": Conflict(
        "tease",
        "tease",
        1,
        "you laugh like a chicken with a cold",
        "Pavel felt the words sting like nettles.",
        tags={"conflict", "toxic"},
    ),
    "mud": Conflict(
        "mud",
        "mud-splash tease",
        1,
        "your face looks like a muddy onion",
        "The children went quiet as if a cloud had passed over the sun.",
        tags={"conflict", "toxic"},
    ),
    "crooked": Conflict(
        "crooked",
        "crooked-teeth tease",
        1,
        "your smile is crooked like a broken fence",
        "Pavel blinked fast and looked at the ground.",
        tags={"conflict", "toxic"},
    ),
}

REMEDIES = {
    "kind": Remedy(
        "kind",
        "kind joke",
        2,
        "turn the joke toward a clumsy goose and a runaway turnip",
        "That sounded funny to both children, and neither one felt poked.",
        tags={"humor", "kind"},
    ),
    "rhyme": Remedy(
        "rhyme",
        "riddle rhyme",
        2,
        "change the sharp tease into a rhyming riddle about boots and beans",
        "It ended in a rhyme that everyone could repeat together.",
        tags={"humor", "kind"},
    ),
    "absurd": Remedy(
        "absurd",
        "silly absurdity",
        2,
        "replace the sting with a story about a hat chasing three pancakes",
        "Soon the whole market was giggling at the ridiculous picture.",
        tags={"humor", "kind"},
    ),
}

CURATED = [
    ("goose", "tease", "kind"),
    ("boots", "mud", "rhyme"),
    ("turnip", "crooked", "absurd"),
]

GIRL_NAMES = ["Mina", "Anya", "Lila", "Ira", "Nina", "Sana", "Tilda", "Mara"]
BOY_NAMES = ["Pavel", "Ivo", "Daro", "Milo", "Soren", "Boris", "Niko", "Luca"]


@dataclass
class StoryParams:
    humor: str
    conflict: str
    remedy: str
    child_a: str = "Mina"
    child_b: str = "Pavel"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    return [(h, c, r) for h in HUMORS for c in CONFLICTS for r in REMEDIES]


def explain_rejection() -> str:
    return "(No story: the chosen pieces do not make a plausible folk-tale joke conflict.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny folk tale about Friday humor and conflict.")
    ap.add_argument("--humor", choices=HUMORS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--remedy", choices=REMEDIES)
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
    combos = valid_combos()
    if not combos:
        raise StoryError(explain_rejection())
    if args.humor:
        combos = [c for c in combos if c[0] == args.humor]
    if args.conflict:
        combos = [c for c in combos if c[1] == args.conflict]
    if args.remedy:
        combos = [c for c in combos if c[2] == args.remedy]
    if not combos:
        raise StoryError(explain_rejection())
    humor, conflict, remedy = rng.choice(sorted(combos))
    return StoryParams(humor, conflict, remedy)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a folk-tale story for a young child that takes place on friday, '
        'includes a funny joke that becomes toxic, and ends with a kinder laugh.',
        f"Tell a small village story where {f['mina'].id} makes a joke, {f['pavel'].id} feels hurt, "
        f"and grandma changes the humor so the conflict ends well.",
        'Write a gentle story with the words friday and toxic, plus a wise elder who helps two children make up.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mina = f["mina"]
    pavel = f["pavel"]
    grandma = f["grandma"]
    humor = f["humor"]
    conflict = f["conflict"]
    remedy = f["remedy"]
    return [
        QAItem(
            question="What happened on friday?",
            answer=f"On friday, Mina and Pavel went to the village market and listened to jokes by the stalls. It began as a cheerful day, but one joke turned toxic and caused a hurt feeling.",
        ),
        QAItem(
            question="Why did Pavel get upset?",
            answer=f"Pavel got upset because Mina used a tease from the {humor.id} joke that sounded unkind. The words were not just silly anymore; they carried {conflict.kind} and made Pavel feel stung.",
        ),
        QAItem(
            question="How did grandma help?",
            answer=f"Grandma listened, then changed the joke into {remedy.kind}. She kept the laughter but removed the sharp part, so both children could smile again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The market sounded cheerful again, and the children shared apples instead of sharp words. The ending showed that humor can stay funny without being toxic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old kind of story that is told from person to person. It often has a village, a wise helper, and a lesson about how to live kindly.",
        ),
        QAItem(
            question="Why can a joke be harmful?",
            answer="A joke can be harmful if it makes fun of someone or uses words that sting. Funny words are best when they are safe for everyone in the room.",
        ),
        QAItem(
            question="What does toxic mean in this story world?",
            answer="Toxic means the humor became hurtful instead of playful. It is the kind of talk that leaves someone feeling smaller instead of included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:11}) {' '.join(bits)}")
    out.append(f"  facts={world.facts}")
    return "\n".join(out)


ASP_RULES = r"""
valid(H, C, R) :- humor(H), conflict(C), remedy(R).
toxic_turn(C) :- conflict(C).
mended :- remedy(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid in HUMORS:
        lines.append(asp.fact("humor", hid))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        world = tell(HUMORS["goose"], CONFLICTS["tease"], REMEDIES["kind"])
        _ = world.render()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        return 1
    print("OK: smoke test and ASP parity passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(HUMORS[params.humor], CONFLICTS[params.conflict], REMEDIES[params.remedy], params.child_a, params.child_b)
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
        print(f"{len(combos)} compatible triples:")
        for h, c, r in combos:
            print(f"  {h:8} {c:10} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(h, c, r)) for h, c, r in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
            header = f"### {p.humor} / {p.conflict} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
