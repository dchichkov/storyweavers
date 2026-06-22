#!/usr/bin/env python3
"""
storyworlds/worlds/referent_surprise_heartwarming.py
====================================================

A small storyworld about a heartwarming surprise: a child tries to keep a gift
secret, mislabels the clue as a "referent", and then the family helps the right
person feel seen.

The world is built from a tiny family-and-surprise domain:
- a planner prepares a surprise
- a helper notices a wrong clue or misunderstood referent
- a kind grown-up or sibling gently fixes the mix-up
- the ending image shows the surprise delivered warmly

The word "referent" appears in the story in a child-friendly way as "the person
the clue refers to".
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
from pathlib import Path
from typing import Callable, Optional

def _bootstrap_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists():
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            return
    raise RuntimeError("Could not locate storyworlds/results.py for imports")

_bootstrap_path()

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SURPRISE_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    cozy_detail: str
    surprise_spot: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    surprise_kind: str
    emotion: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mixup:
    id: str
    clue: str
    mistaken_for: str
    fix_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["surprise"] < THRESHOLD:
            continue
        sig = ("surprise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.entities.values():
            if kid.role in {"planner", "helper"}:
                kid.memes["warmth"] += 1
        out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("surprise", "social", _r_surprise)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def sensible_moves() -> list[HelperMove]:
    return [m for m in HELPER_MOVES.values() if m.sense >= SENSE_MIN]


def move_ok(move: HelperMove, mixup: Mixup) -> bool:
    return move.sense >= SENSE_MIN and move.power >= 1 and mixup.fix_word in {"tag", "name", "note"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES:
        for gift in GIFTS:
            for mixup in MIXUPS:
                if mixup.id in {"tag", "name"} and place != "kitchen":
                    combos.append((place, gift, mixup.id))
                elif mixup.id == "note":
                    combos.append((place, gift, mixup.id))
    return combos


@dataclass
class StoryParams:
    place: str
    gift: str
    mixup: str
    planner_name: str
    planner_gender: str
    helper_name: str
    helper_gender: str
    grownup_name: str
    grownup_gender: str
    move: str
    seed: Optional[int] = None


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", "warm cookies cooling on the counter", "the blue napkin", {"home"}),
    "bedroom": Place("bedroom", "the bedroom", "a small ribbon box on the desk", "the pillow", {"home"}),
    "garden": Place("garden", "the garden", "paper stars on the bench", "the watering can", {"outdoors"}),
}

GIFTS = {
    "cookies": Gift("cookies", "cookies", "a plate of cookies", "snack", "happy", {"sweet"}),
    "drawing": Gift("drawing", "drawing", "a folded drawing", "picture", "proud", {"paper"}),
    "flower": Gift("flower", "flower", "a small flower pot", "plant", "gentle", {"plant"}),
}

MIXUPS = {
    "tag": Mixup("tag", "a name tag", "a grocery label", "label", {"paper"}),
    "name": Mixup("name", "a name card", "a place card", "tag", {"paper"}),
    "note": Mixup("note", "a note", "a shopping list", "note", {"paper"}),
}

HELPER_MOVES = {
    "whisper": HelperMove("whisper", 2, 1, "whispered the right name to the planner", "whispered, but the clue stayed mixed up", "whispered the right name to the planner", {"gentle"}),
    "erase": HelperMove("erase", 3, 2, "erased the old clue and wrote the right name", "tried to erase it, but the mark would not come off", "erased the old clue and wrote the right name", {"fix"}),
    "show": HelperMove("show", 2, 1, "showed the planner the person the clue referred to", "showed the clue, but it still did not make sense", "showed the planner the person the clue referred to", {"referent"}),
}

GIRL_NAMES = ["Lily", "Maya", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Noah", "Sam", "Theo"]
TRAITS = ["careful", "kind", "gentle", "thoughtful", "brave"]


def explain_rejection(move: HelperMove) -> str:
    return f"(No story: the helper move '{move.id}' is too weak or unclear for this mix-up.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for g in GIFTS:
        lines.append(asp.fact("gift", g))
    for m in MIXUPS:
        lines.append(asp.fact("mixup", m))
    for h in HELPER_MOVES:
        lines.append(asp.fact("move", h))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(P,G,M) :- place(P), gift(G), mixup(M).
good_move(M) :- move(M), sense_min(S), helper_sense(M, H), H >= S.
outcome(surprise) :- good_move(M), compatible(P,G,X).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    ok = a == b
    if ok:
        print(f"OK: ASP parity matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH between ASP and Python valid_combos().")
        if a - b:
            print("  only in ASP:", sorted(a - b))
        if b - a:
            print("  only in Python:", sorted(b - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    return 0 if ok else 1


def tell(place: Place, gift: Gift, mixup: Mixup, planner_name: str, planner_gender: str,
         helper_name: str, helper_gender: str, grownup_name: str, grownup_gender: str,
         move: HelperMove) -> World:
    world = World()
    planner = world.add(Entity(id=planner_name, kind="character", type=planner_gender, role="planner", traits=["sweet"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["kind"]))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_gender, role="grownup", label="the grown-up"))
    gift_ent = world.add(Entity(id=gift.id, type="gift", label=gift.label))
    clue_ent = world.add(Entity(id="clue", type="clue", label=mixup.clue))
    world.facts["place"] = place
    world.facts["gift"] = gift
    world.facts["mixup"] = mixup
    world.facts["planner"] = planner
    world.facts["helper"] = helper
    world.facts["grownup"] = grownup
    world.facts["move"] = move

    planner.memes["hope"] = 1.0
    helper.memes["care"] = 1.0
    world.say(f"It was {place.label}, and {planner.id} was getting ready for a surprise.")
    world.say(f"{planner.id} wrapped {gift.phrase} and tucked it near {place.surprise_spot}.")
    world.say(f"{planner.id} wrote {mixup.clue} because {planner.pronoun('subject')} wanted the right person to feel special.")

    world.para()
    helper.memes["wonder"] = 1.0
    world.say(f"{helper.id} peered at the clue and frowned a little.")
    world.say(f'"Who is this for?" {helper.id} asked. "I think this clue needs its referent."')
    world.say(f"{helper.id} meant the person the clue referred to, not just the paper itself.")

    world.para()
    if move.id == "show":
        clue_ent.meters["surprise"] += 1
        propagate(world, narrate=False)
        world.say(f"{helper.id} {move.text}.")
        world.say(f"{grownup.label_word.capitalize()} smiled and helped them understand.")
    elif move.id == "whisper":
        clue_ent.meters["surprise"] += 1
        world.say(f"{helper.id} {move.text}, and then {planner.id} nodded slowly.")
        world.say(f"{grownup.label_word.capitalize()} waited beside them until the right name felt clear.")
    else:
        clue_ent.meters["surprise"] += 1
        world.say(f"{helper.id} {move.text}.")
        world.say(f"{grownup.label_word.capitalize()} came over with a soft laugh and fixed the clue.")

    world.para()
    planner.memes["joy"] += 1
    helper.memes["joy"] += 1
    grownup.memes["warmth"] += 1
    world.say(f"At last, the surprise was ready for {gift.label} to be given to the right person.")
    world.say(f"{planner.id} held out {gift.phrase}, and the room felt bright and kind.")
    world.say(f"{gift.phrase.capitalize()} glowed with the happy feeling of being seen.")

    world.facts["outcome"] = "surprise"
    return world


def prompt_set(world: World) -> list[str]:
    f = world.facts
    p = f["planner"]
    g = f["gift"]
    m = f["mixup"]
    return [
        f"Write a heartwarming story about a surprise in {f['place'].label} that uses the word 'referent'.",
        f"Tell a gentle story where {p.id} makes a surprise for someone, and a helper notices the clue and fixes the referent.",
        f"Write a short child-friendly story about a surprise gift, a mixed-up clue, and a warm happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["planner"]
    h = f["helper"]
    g = f["gift"]
    m = f["mixup"]
    place = f["place"]
    move = f["move"]
    return [
        QAItem(
            question=f"What was {p.id} making in {place.label}?",
            answer=f"{p.id} was making a surprise for someone special. {p.pronoun('subject').capitalize()} wrapped {g.phrase} and kept the clue quiet so the gift would feel special.",
        ),
        QAItem(
            question=f"Why did {h.id} talk about the referent?",
            answer=f"{h.id} wanted to be sure the clue pointed to the right person. The referent is the person the clue refers to, so the surprise would go to the right hands.",
        ),
        QAItem(
            question=f"What did {move.text if False else h.id} do to help?",
            answer=f"{h.id} {move.qa_text}. That gentle help cleared up the mix-up and kept the surprise warm instead of confusing.",
        ),
        QAItem(
            question=f"How did the story end after the clue was fixed?",
            answer=f"The surprise was delivered to the right person, and everyone felt happy and close. The final image is {g.phrase} being handed over with smiles all around.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a referent?",
            answer="A referent is the person or thing a word or clue points to. In a surprise story, it is the one the note is really meant for.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something kept secret for a little while so the moment of finding out feels extra happy.",
        ),
        QAItem(
            question="Why do people make gifts into surprises?",
            answer="People do that to make someone feel cared for and special. The waiting and the reveal can make the moment warm and memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    parts.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("gift", GIFTS), ("mixup", MIXUPS), ("move", HELPER_MOVES)]:
        if getattr(params, key) not in table:
            raise StoryError(f"invalid {key}: {getattr(params, key)}")
    world = tell(
        PLACES[params.place],
        GIFTS[params.gift],
        MIXUPS[params.mixup],
        params.planner_name,
        params.planner_gender,
        params.helper_name,
        params.helper_gender,
        params.grownup_name,
        params.grownup_gender,
        HELPER_MOVES[params.move],
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompt_set(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming surprise storyworld with a referent clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--mixup", choices=MIXUPS)
    ap.add_argument("--move", choices=HELPER_MOVES)
    ap.add_argument("--planner-name")
    ap.add_argument("--planner-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup-name")
    ap.add_argument("--grownup-gender", choices=["woman", "man", "mother", "father"])
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
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.gift is None or c[1] == args.gift) and (args.mixup is None or c[2] == args.mixup)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, gift, mixup = rng.choice(sorted(combos))
    move = args.move or rng.choice(sorted(HELPER_MOVES))
    planner_gender = args.planner_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    grownup_gender = args.grownup_gender or rng.choice(["woman", "man", "mother", "father"])
    planner_name = args.planner_name or rng.choice(GIRL_NAMES if planner_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != planner_name])
    grownup_name = args.grownup_name or rng.choice(["Aunt June", "Mom", "Dad", "Grandma Kim", "Uncle Ray"])
    return StoryParams(
        place=place,
        gift=gift,
        mixup=mixup,
        planner_name=planner_name,
        planner_gender=planner_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        grownup_name=grownup_name,
        grownup_gender=grownup_gender,
        move=move,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(e.id, e.type, meters, memes, e.role)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        print(sorted(set(asp.atoms(model, "compatible"))))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="kitchen", gift="cookies", mixup="tag", planner_name="Mia", planner_gender="girl", helper_name="Ben", helper_gender="boy", grownup_name="Mom", grownup_gender="mother", move="show"),
            StoryParams(place="bedroom", gift="drawing", mixup="name", planner_name="Leo", planner_gender="boy", helper_name="Nora", helper_gender="girl", grownup_name="Dad", grownup_gender="father", move="erase"),
            StoryParams(place="garden", gift="flower", mixup="note", planner_name="Lily", planner_gender="girl", helper_name="Theo", helper_gender="boy", grownup_name="Grandma Kim", grownup_gender="woman", move="whisper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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


if __name__ == "__main__":
    main()
