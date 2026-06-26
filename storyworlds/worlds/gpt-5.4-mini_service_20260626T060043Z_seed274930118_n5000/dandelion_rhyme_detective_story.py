#!/usr/bin/env python3
"""
Standalone storyworld: a tiny Detective Story built around a dandelion and rhyme clues.

Premise:
A small detective follows a rhyming trail through a garden to find who scattered
pollen from a dandelion and restore the missing note.

The world simulation tracks physical meters and emotional memes:
- physical evidence can be collected, hidden, or revealed
- emotional tension rises when clues are confusing
- rhyme helps the detective connect clues and solve the case
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the garden"
    detail: str = "beds of flowers and a windy path"
    afford_rhyme: bool = True


@dataclass
class Clue:
    id: str
    phrase: str
    rhyme_tail: str
    value: str
    reveal: str


@dataclass
class StoryParams:
    setting: str
    detective_name: str
    detective_type: str
    partner_name: str
    partner_type: str
    clue: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", detail="a gate, a path, and a row of daisies"),
    "greenhouse": Setting(place="the greenhouse", detail="glass walls, warm soil, and little pots"),
    "lane": Setting(place="the quiet lane", detail="brick fences, wet stones, and a narrow curb"),
}

CLUES = {
    "dandelion": Clue(
        id="dandelion",
        phrase="a bright dandelion puff",
        rhyme_tail="glow / show",
        value="pollen",
        reveal="a trail of pale pollen dust",
    ),
    "button": Clue(
        id="button",
        phrase="a lost red button",
        rhyme_tail="round / found",
        value="button",
        reveal="a tiny red button under a leaf",
    ),
    "lantern": Clue(
        id="lantern",
        phrase="a little lantern charm",
        rhyme_tail="light / night",
        value="charm",
        reveal="a lantern charm hanging from a twig",
    ),
}

GIRL_NAMES = ["Mina", "Ivy", "Nora", "Lila", "Pia", "Mara"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Ezra", "Noah", "Jasper"]
TRAITS = ["careful", "curious", "brave", "patient", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def rhyme_match(clue: Clue, observed_tail: str) -> bool:
    return observed_tail == clue.rhyme_tail


def detective_storybeats(world: World, detective: Entity, partner: Entity, clue: Clue) -> None:
    add_meme(detective, "curiosity", 1)
    add_meme(detective, "resolve", 1)
    world.say(
        f"{detective.id} was a little {detective.type} detective who loved looking for clues. "
        f"{partner.id} kept close, ready with a notebook and a pencil."
    )
    world.say(
        f"One morning at {world.setting.place}, they found {clue.phrase}. "
        f"It seemed ordinary, but {detective.id} knew small things could whisper big secrets."
    )


def investigate(world: World, detective: Entity, clue: Clue) -> None:
    add_meter(detective, "search", 1)
    add_meme(detective, "puzzle", 1)
    world.say(
        f"{detective.id} bent low and studied the ground. "
        f"Near the flower bed, the signs of the case were tidy at first, then tricky."
    )
    world.say(
        f"A soft rhyme came to mind: {clue.rhyme_tail.replace(' / ', ' and ')}. "
        f"The little rhyme helped {detective.id} think of the right kind of clue."
    )


def follow_trail(world: World, detective: Entity, partner: Entity, clue: Clue) -> None:
    add_meter(detective, "trail", 1)
    add_meter(partner, "notes", 1)
    add_meme(partner, "hope", 1)
    world.say(
        f"They followed the faint trail with care. {partner.id} wrote down every step, "
        f"while {detective.id} watched for anything that matched the rhyme."
    )
    world.say(
        f"At last, the trail pointed to {clue.reveal}. "
        f"It fit the rhyme so neatly that the mystery started to smile."
    )


def solve(world: World, detective: Entity, partner: Entity, clue: Clue) -> None:
    add_meme(detective, "joy", 1)
    add_meme(partner, "joy", 1)
    add_meter(detective, "solve", 1)
    world.say(
        f"{detective.id} laughed a small happy laugh. "
        f"The clue was not a trick after all; it was the missing piece."
    )
    world.say(
        f"They brought back the {clue.value} and left the {clue.phrase} where it belonged. "
        f"By the end, the garden felt calm again, and the whole case was closed."
    )


def tell(setting: Setting, clue: Clue, detective_name: str, detective_type: str,
         partner_name: str, partner_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, label="detective"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, label="partner"))
    world.facts.update(detective=detective, partner=partner, clue=clue)

    detective_storybeats(world, detective, partner, clue)
    world.para()
    investigate(world, detective, clue)
    world.para()
    follow_trail(world, detective, partner, clue)
    world.para()
    solve(world, detective, partner, clue)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    clue: Clue = world.facts["clue"]
    detective: Entity = world.facts["detective"]
    return [
        f"Write a short detective story for a young child that includes the word '{clue.id}'.",
        f"Tell a gentle mystery where {detective.id} solves a case using a rhyme clue.",
        f"Write a small story about a detective, a dandelion, and a trail that leads to the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    partner: Entity = world.facts["partner"]
    clue: Clue = world.facts["clue"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {detective.id}, a little detective, and {partner.id}, who helps with the case.",
        ),
        QAItem(
            question=f"What clue did they find in the garden?",
            answer=f"They found {clue.phrase}, which led them to {clue.reveal}.",
        ),
        QAItem(
            question=f"How did the rhyme help {detective.id}?",
            answer=f"The rhyme '{clue.rhyme_tail}' helped {detective.id} notice what kind of clue to look for.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"They solved the mystery, brought back the {clue.value}, and the garden became peaceful again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dandelion?",
            answer="A dandelion is a yellow flower that later turns into a fluffy white puff of seeds.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like glow and show.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues and thinks carefully to solve a mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {', '.join(bits) if bits else 'quiet'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(garden). setting(greenhouse). setting(lane).
clue(dandelion). clue(button). clue(lantern).

rhyme(dandelion, "glow / show").
rhyme(button, "round / found").
rhyme(lantern, "light / night").

mystery(C) :- clue(C), rhyme(C, _).
solvable(C) :- mystery(C).

#show solvable/1.
#show rhyme/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("rhyme", cid, CLUES[cid].rhyme_tail))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/1."))
    return sorted(set(asp.atoms(model, "solvable")))


def python_solvable() -> list[tuple]:
    return [(cid,) for cid in CLUES]


def asp_verify() -> int:
    a = set(asp_solvable())
    p = set(python_solvable())
    if a == p:
        print(f"OK: ASP parity verified for {len(a)} clues.")
        return 0
    print("MISMATCH between ASP and Python:")
    if a - p:
        print("  only in ASP:", sorted(a - p))
    if p - a:
        print("  only in Python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Generation / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with rhyme and a dandelion clue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    detective_type = rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    partner_type = "girl" if detective_type == "boy" else "boy"
    partner_name = args.partner or rng.choice(GIRL_NAMES if partner_type == "girl" else BOY_NAMES)
    return StoryParams(
        setting=setting,
        detective_name=detective_name,
        detective_type=detective_type,
        partner_name=partner_name,
        partner_type=partner_type,
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        params.detective_name,
        params.detective_type,
        params.partner_name,
        params.partner_type,
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
        print(asp_program("#show solvable/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solvable/1."))
        print(f"{len(asp.atoms(model, 'solvable'))} solvable clue options.")
        for cid, in sorted(set(asp.atoms(model, "solvable"))):
            print(cid)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(s, c) for s in SETTINGS for c in CLUES]
        for i, (s, c) in enumerate(combos):
            p = StoryParams(
                setting=s,
                clue=c,
                detective_name=GIRL_NAMES[i % len(GIRL_NAMES)],
                detective_type="girl",
                partner_name=BOY_NAMES[i % len(BOY_NAMES)],
                partner_type="boy",
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.setting} / {p.clue} / {p.detective_name}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
