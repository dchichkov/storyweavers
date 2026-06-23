#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/chitlin_garland_sharing_moral_value_cautionary_detective.py
==============================================================================================================================

A small detective-style storyworld about sharing a party table with chitlins
and a garland. The world keeps physical state in meters and social state in
memes, then turns those facts into a short cautionary mystery with a moral.

Seed premise:
- A child detective notices a shared table.
- The precious items are a bowl of chitlins and a bright garland.
- A tension beat appears when somebody tries to take more than their share.
- The detective traces the clues, warns about the risk, and restores sharing.

This file is standalone and uses only the stdlib plus the shared Storyweavers
result container API.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
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
class Place:
    id: str
    label: str
    scene: str
    clue: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    noun: str
    kind: str
    risky_meter: str
    share_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    method: str
    ending: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["grabbed"] < THRESHOLD:
            continue
        prize = world.facts["prize_ent"]
        if prize.meters["shared"] >= THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        prize.meters["spill"] += 1
        ent.memes["worry"] += 1
        out.append(f"The table looked messy, and the clue pointed right at the {prize.label}.")
    return out


def _r_restore(world: World) -> list[str]:
    prize = world.facts["prize_ent"]
    helper = world.facts["helper"]
    if prize.meters["shared"] < THRESHOLD or helper.memes["resolve"] < THRESHOLD:
        return []
    sig = ("restore", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["spill"] = 0
    helper.memes["pride"] += 1
    return [f"The clue fit: sharing fixed the trouble before anyone lost the {prize.label}." ]


RULES = [Rule("spill", _r_spill), Rule("restore", _r_restore)]


def setting_sentence(place: Place, prize: Prize) -> str:
    return f"At {place.label}, {place.scene} and {place.clue}."


def tell(place: Place, prize: Prize, fix: Fix, detective: Entity, helper: Entity, bystander: Entity) -> World:
    world = World()
    detective = world.add(detective)
    helper = world.add(helper)
    bystander = world.add(bystander)
    place_ent = world.add(Entity(id="place", type="place", label=place.label, tags=set(place.affords)))
    prize_ent = world.add(Entity(id=prize.id, type=prize.kind, label=prize.label, tags=set(prize.tags)))
    board = world.add(Entity(id="board", type="thing", label="clue board"))
    _ = (place_ent, board)

    world.facts["place"] = place
    world.facts["prize"] = prize
    world.facts["fix"] = fix
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["bystander"] = bystander
    world.facts["prize_ent"] = prize_ent
    world.facts["shared"] = False

    detective.memes["curiosity"] += 1
    helper.memes["greed"] += 1
    bystander.memes["patience"] += 1

    world.say(f"{detective.id} was a little detective who noticed every clue.")
    world.say(f"{helper.id} loved the party table, especially the {prize.label}.")
    world.say(setting_sentence(place, prize))
    world.say(f"{detective.id} spotted the {prize.label} and thought something was off.")

    world.para()
    if prize.id == "chitlin":
        world.say(f"One bowl of {prize.noun} sat under a bright garland, ready for everyone.")
    else:
        world.say(f"A bright {prize.label} hung above the food, waiting to be shared with care.")

    helper.meters["grabbed"] += 1
    world.say(f"Then {helper.id} reached for more than {helper.pronoun('possessive')} share.")
    propagate(world, narrate=True)

    world.para()
    detective.memes["resolve"] += 1
    world.say(f'{detective.id} followed the clue and said, "We can all enjoy it if we share it."')
    if prize.id == "chitlin":
        world.say(f'{detective.id} passed the bowl around so each plate got a little bit.')
    else:
        world.say(f'{detective.id} helped hang the garland evenly so it stayed bright for the whole room.')
    prize_ent.meters["shared"] = 1
    helper.meters["grabbed"] = 0
    propagate(world, narrate=True)

    world.para()
    world.say(f"{helper.id} nodded, gave back the extra, and smiled at the fair share.")
    world.say(f"By the end, the {prize.label} was safe, the clue was solved, and everyone had enough.")
    world.facts["shared"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a 3-to-5-year-old about {f["detective"].id} solving a sharing clue with a {f["prize"].label}.',
        f'Write a cautionary story where someone takes too much {f["prize"].label}, then learns to share after a small detective warning.',
        f'Write a simple story that uses the words "chitlin" and "garland" and ends with sharing that makes the room feel right again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    helper = f["helper"]
    prize: Prize = f["prize"]
    place: Place = f["place"]
    fix: Fix = f["fix"]
    qa = [
        QAItem(
            question=f"What kind of story is this when {det.id} notices the clue at {place.label}?",
            answer=f"It is a detective story about spotting a clue and solving a sharing problem. {det.id} pays attention, then helps everyone use the {prize.label} the fair way.",
        ),
        QAItem(
            question=f"Why did {helper.id} get in trouble with the {prize.label}?",
            answer=f"{helper.id} tried to take more than a fair share, so the {prize.label} stopped being neat and started to cause a problem. The detective noticed the change right away.",
        ),
        QAItem(
            question=f"How did {det['id'] if isinstance(det, dict) else det.id} fix the problem?",
            answer=f"{det.id} used {fix.label} by {fix.method}. That helped everyone share, and the ending showed the {prize.label} calm and tidy again.",
        ),
    ]
    if prize.id == "chitlin":
        qa.append(QAItem(
            question="Why did the bowl matter to everyone?",
            answer="The bowl mattered because it held food for the whole group. Once the detective showed how to share it, everyone could eat a little and nobody was left out.",
        ))
    else:
        qa.append(QAItem(
            question="Why did the garland matter to the room?",
            answer="The garland mattered because it made the room look bright and festive. When it was shared carefully, it stayed pretty for everyone to enjoy.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    prize: Prize = world.facts["prize"]
    if prize.id == "chitlin":
        return [
            QAItem("What is sharing?", "Sharing means giving some of what you have so other people can enjoy it too."),
            QAItem("Why should people take turns with food?", "Taking turns helps everyone get a fair amount and keeps people from fighting over the same bowl."),
        ]
    return [
        QAItem("What is a garland?", "A garland is a decoration made of flowers, paper, or leaves that you hang up to make a place look festive."),
        QAItem("Why should decorations be handled carefully?", "Careful hands keep decorations from getting torn, bent, or dropped."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "kitchen": Place(
        id="kitchen",
        label="the kitchen table",
        scene="a warm table with a bowl and a bright garland",
        clue="the crumbs showed someone had been reaching too fast",
        affords={"chitlin", "garland"},
    ),
    "porch": Place(
        id="porch",
        label="the front porch",
        scene="a picnic table waited beside hanging streamers",
        clue="the ribbon ends pointed toward the same plate",
        affords={"chitlin", "garland"},
    ),
    "hall": Place(
        id="hall",
        label="the bright hall",
        scene="a long sideboard held party snacks and decorations",
        clue="the shiny floor showed a small trail of dropped bits",
        affords={"chitlin", "garland"},
    ),
}

OBJECTS = {
    "chitlin": Prize(
        id="chitlin",
        label="chitlin",
        noun="chitlin",
        kind="food",
        risky_meter="spill",
        share_need="servings",
        tags={"food", "share"},
    ),
    "garland": Prize(
        id="garland",
        label="garland",
        noun="garland",
        kind="decoration",
        risky_meter="tug",
        share_need="space",
        tags={"decor", "share"},
    ),
}

FIXES = {
    "plate": Fix(id="plate", label="small plates", method="passing them around one by one", ending="the plates circled the table", tags={"share"}),
    "clip": Fix(id="clip", label="little clips", method="spacing the garland evenly", ending="the garland hung straight and bright", tags={"share"}),
}

DETECTIVE_NAMES = ["Mina", "Jo", "Rae", "Ivy", "Nina", "Toby", "Owen", "Pia"]
HELPER_NAMES = ["Sam", "Nia", "Leo", "June", "Moe", "Ellie", "Ben", "Tia"]
CURIOUS_TRAITS = ["careful", "curious", "sharp-eyed", "patient"]


@dataclass
class StoryParams:
    place: str = "kitchen"
    object: str = "chitlin"
    fix: str = "plate"
    detective: str = "Mina"
    helper: str = "Sam"
    bystander: str = "Jo"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for obj in OBJECTS:
            for fix in FIXES:
                if obj == "chitlin" and fix == "plate":
                    combos.append((place, obj, fix))
                if obj == "garland" and fix == "clip":
                    combos.append((place, obj, fix))
    return combos


def explain_rejection(obj: Prize, fix: Fix) -> str:
    return f"(No story: {fix.label} does not solve the sharing problem for {obj.label}. Try the matching fix.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about sharing a chitlin or a garland.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--bystander")
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
              if (args.place is None or c[0] == args.place)
              and (args.object is None or c[1] == args.object)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, obj, fix = rng.choice(sorted(combos))
    detective = args.name or rng.choice(DETECTIVE_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != detective])
    bystander = args.bystander or rng.choice([n for n in DETECTIVE_NAMES + HELPER_NAMES if n not in {detective, helper}])
    return StoryParams(place=place, object=obj, fix=fix, detective=detective, helper=helper, bystander=bystander)


def generate(params: StoryParams) -> StorySample:
    place = SETTINGS.get(params.place)
    prize = OBJECTS.get(params.object)
    fix = FIXES.get(params.fix)
    if not place or not prize or not fix:
        raise StoryError("Invalid StoryParams values.")
    if (params.place, params.object, params.fix) not in valid_combos():
        raise StoryError(explain_rejection(prize, fix))
    detective = Entity(id=params.detective, kind="character", type="girl" if params.detective in {"Mina", "Ivy", "Nina", "Pia", "Jo", "Rae", "June", "Tia"} else "boy", role="detective")
    helper = Entity(id=params.helper, kind="character", type="boy" if params.helper in {"Leo", "Owen", "Moe", "Ben", "Toby", "Sam"} else "girl", role="helper")
    bystander = Entity(id=params.bystander, kind="character", type="girl" if params.bystander in {"Mina", "Ivy", "Nina", "Pia", "Jo", "Rae", "June", "Tia"} else "boy", role="bystander")
    world = tell(place, prize, fix, detective, helper, bystander)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,O,F) :- place(P), object(O), fix(F), (O="chitlin", F="plate"; O="garland", F="clip").
shared(O) :- chosen(O), fix_ok(O).
moral_value(O) :- shared(O).
cautionary(O) :- chosen(O), not shared(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        assert sample.story
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


CURATED = [
    StoryParams(place="kitchen", object="chitlin", fix="plate", detective="Mina", helper="Sam", bystander="Jo"),
    StoryParams(place="porch", object="garland", fix="clip", detective="Ivy", helper="Leo", bystander="Nina"),
    StoryParams(place="hall", object="chitlin", fix="plate", detective="Rae", helper="June", bystander="Toby"),
    StoryParams(place="kitchen", object="garland", fix="clip", detective="Pia", helper="Ben", bystander="Moe"),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
