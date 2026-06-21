#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/gonk_lawner_chaff_bad_ending_whodunit.py
========================================================================

A small whodunit-style storyworld about a dusty shed, a puzzling stolen key,
and a bad ending where the mystery is solved too late to help anyone.

The required seed words are included as world nouns:
- gonk
- lawner
- chaff

The world is intentionally tiny: a helper, a keeper, a suspect, a clue, and one
ending where the truth arrives after the damage is done.
"""

from __future__ import annotations

import argparse
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    hiding_place: str


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    meaning: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    alibi: str
    risk: int = 0


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    keeper: str
    helper: str
    seed: Optional[int] = None


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
        import copy as _copy

        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "barn": Setting(
        id="barn",
        place="the old barn",
        detail="Dust lay on the floorboards, and a narrow loft cast a dark shadow.",
        hiding_place="behind a stack of hay bales",
    ),
    "shed": Setting(
        id="shed",
        place="the tool shed",
        detail="Rakes hung on the wall, and a little window let in a thin stripe of light.",
        hiding_place="under a workbench",
    ),
}

CLUES = {
    "chaff": Clue(
        id="chaff",
        label="chaff",
        detail="a scrap of chaff caught on a nail",
        meaning="someone had brushed past the hay stack very recently",
    ),
    "button": Clue(
        id="button",
        label="button",
        detail="a blue coat button",
        meaning="someone in a blue coat had been here",
    ),
    "mud": Clue(
        id="mud",
        label="mud",
        detail="a muddy footprint",
        meaning="the suspect had walked in from the yard",
    ),
}

SUSPECTS = {
    "gonk": Suspect(
        id="gonk",
        label="gonk",
        type="thing",
        motive="it liked shiny objects and liked to hide them",
        alibi="it had rolled quietly near the hay and then gone still",
        risk=2,
    ),
    "lawner": Suspect(
        id="lawner",
        label="lawner",
        type="man",
        motive="he wanted the key to the seed room before dawn",
        alibi="he said he was trimming the far hedge",
        risk=6,
    ),
    "crow": Suspect(
        id="crow",
        label="crow",
        type="thing",
        motive="it liked bright things for its nest",
        alibi="it was perched high on the rafters",
        risk=1,
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CLUES:
            for sus in SUSPECTS:
                if sid == "barn" and cid == "chaff" and sus in {"gonk", "lawner"}:
                    combos.append((sid, cid, sus))
                if sid == "shed" and cid in {"button", "mud"} and sus == "lawner":
                    combos.append((sid, cid, sus))
    return combos


def explain_rejection(setting: str, clue: str, suspect: str) -> str:
    if clue == "chaff" and suspect == "crow":
        return "(No story: chaff points to the hay and the barn, but the crow has no clear path into this mystery.)"
    return "(No story: this combination does not create a clean whodunit clue trail.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit-style storyworld with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--keeper", choices=["keeper", "farmer", "watcher"])
    ap.add_argument("--helper", choices=["child", "cat", "dog"])
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
    if args.setting and args.clue and args.suspect:
        if (args.setting, args.clue, args.suspect) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.clue, args.suspect))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        keeper=args.keeper or rng.choice(["keeper", "farmer", "watcher"]),
        helper=args.helper or rng.choice(["child", "cat", "dog"]),
    )


def _r_discover(world: World) -> list[str]:
    out = []
    if world.get("clue").meters["found"] >= THRESHOLD and ("discover",) not in world.fired:
        world.fired.add(("discover",))
        world.get("keeper").memes["worry"] += 1
        out.append("__discover__")
    return out


def _r_too_late(world: World) -> list[str]:
    if world.get("suspect").meters["escape"] >= THRESHOLD and ("late",) not in world.fired:
        world.fired.add(("late",))
        world.get("keeper").memes["sad"] += 1
        return ["__late__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_discover, _r_too_late):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, clue: Clue, suspect: Suspect, keeper: str, helper: str) -> World:
    w = World()
    k = w.add(Entity(id=keeper, kind="character", type="person", role="keeper", label=f"the {keeper}"))
    h = w.add(Entity(id=helper, kind="character", type="thing", role="helper", label=f"the {helper}"))
    s = w.add(Entity(id=suspect.id, kind="character", type=suspect.type, role="suspect", label=suspect.label))
    c = w.add(Entity(id=clue.id, kind="thing", type="clue", label=clue.label))

    k.memes["care"] += 1
    h.memes["alert"] += 1

    w.say(
        f"At {setting.place}, {setting.detail} {keeper} and {helper} were the only ones awake."
    )
    w.say(
        f"Then {keeper} noticed {clue.detail}. The little scrap seemed to say that {clue.meaning}."
    )
    w.para()
    w.say(
        f"That was enough to start the question: who had gone into the hiding place {setting.hiding_place}?"
    )
    w.say(
        f"{keeper} looked at {suspect.label} and thought of {suspect.motive}, but {suspect.alibi}."
    )

    # Investigation turn
    c.meters["found"] += 1
    propagate(w, narrate=False)
    w.para()

    if suspect.id == "lawner":
        w.say(
            f"The {helper} nosed at the dust, and a second mark appeared by the door. "
            f"It looked like the lawner had been there after all."
        )
        w.say(
            f"{keeper} followed the trail at last, but the seed room key was already gone."
        )
        s.meters["escape"] += 1
        propagate(w, narrate=False)
        w.para()
        w.say(
            f"By the time the truth was clear, the lawner was far down the lane, and the barn was quiet again."
        )
        w.say(
            f"{keeper} had solved the mystery too late, and the chaff clue only proved who had passed through."
        )
    else:
        w.say(
            f"The clue led to the gonk. It had tucked the key behind the hay, then rolled away."
        )
        w.say(
            f"{keeper} caught the gonk at the edge of the yard, but the key had already been lost in the mud."
        )
        s.meters["escape"] += 1
        propagate(w, narrate=False)
        w.para()
        w.say(
            f"So the mystery was answered, but the ending stayed bad: the missing key never came back."
        )

    w.facts.update(setting=setting, clue=clue, suspect=suspect, keeper=k, helper=h, culprit=s,
                   outcome="bad", clue_found=True, key_lost=True)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a young child that includes the words "{f["suspect"].label}", "{f["clue"].label}", and "{f["setting"].id}".',
        f"Tell a mystery story where {f['keeper'].label_word} follows a clue about {f['clue'].label} but learns the truth too late.",
        "Write a bad-ending mystery with a small clue trail, a suspect, and a lost key.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s: Suspect = f["suspect"]
    c: Clue = f["clue"]
    k: Entity = f["keeper"]
    if s.id == "lawner":
        answers = [
            QAItem(
                question="What was the clue?",
                answer=f"The clue was {c.detail}. It pointed to the hay and made {k.label_word} think someone had passed by there recently.",
            ),
            QAItem(
                question="Who was the mystery about?",
                answer=f"It was about the lawner. {k.label_word} suspected him because the clue and the dust both fit his path.",
            ),
            QAItem(
                question="How did the story end?",
                answer="It ended badly. The truth was found too late, and the missing key was still gone by the time anyone understood what happened.",
            ),
        ]
    else:
        answers = [
            QAItem(
                question="What was the clue?",
                answer=f"The clue was {c.detail}. It showed that someone had brushed the hay pile recently.",
            ),
            QAItem(
                question="Who was the mystery about?",
                answer="It was about the gonk. The clue fit the gonk's hiding place, but it was already too late to fix the loss.",
            ),
            QAItem(
                question="How did the story end?",
                answer="It ended badly. Even after the mystery was solved, the key stayed lost and the barn felt empty.",
            ),
        ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is chaff?", "Chaff is light, dry plant bits that can stick to hay and dust. It is often a sign that something brushed by recently."),
        QAItem("What does a lawner do?", "A lawner keeps grass, hedges, and yard edges tidy. In a mystery, a lawner might be near the garden or the lane."),
        QAItem("What is a gonk?", "A gonk is a small odd little creature or toy-like figure. In stories it can be sneaky, harmless, or just hard to understand."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Q&A =="]
    for item in sample.prompts:
        out.append(item)
    out.append("")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(setting="barn", clue="chaff", suspect="lawner", keeper="keeper", helper="child"),
        StoryParams(setting="barn", clue="chaff", suspect="gonk", keeper="watcher", helper="cat"),
    ]


CURATED = [
    StoryParams(setting="barn", clue="chaff", suspect="lawner", keeper="keeper", helper="child"),
    StoryParams(setting="barn", clue="chaff", suspect="gonk", keeper="watcher", helper="cat"),
]


ASP_RULES = r"""
valid(S,C,U) :- setting(S), clue(C), suspect(U), S = barn, C = chaff, U = lawner.
valid(S,C,U) :- setting(S), clue(C), suspect(U), S = barn, C = chaff, U = gonk.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for uid in SUSPECTS:
        lines.append(asp.fact("suspect", uid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        ok = False
        print("MISMATCH in gate.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: story generation smoke test passed.")
    except Exception as ex:
        ok = False
        print(f"SMOKE TEST FAILED: {ex}")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    for k in ("setting", "clue", "suspect"):
        if getattr(params, k) not in globals()[k.upper() + "S"]:
            raise StoryError(f"Unknown {k}: {getattr(params, k)}")
    world = tell(
        SETTINGS[params.setting],
        CLUES[params.clue],
        SUSPECTS[params.suspect],
        params.keeper,
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, suspect = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        suspect=suspect,
        keeper=args.keeper or rng.choice(["keeper", "farmer", "watcher"]),
        helper=args.helper or rng.choice(["child", "cat", "dog"]),
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
