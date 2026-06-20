#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/test_peter_wolverine_foreshadowing_mystery.py
==============================================================================

A standalone storyworld for a small mystery with foreshadowing built around the
seed words: test, peter, wolverine.

Premise:
- Peter is getting ready for a test.
- Strange clues appear before the reveal: scratch marks, a tuft of dark fur,
  paw prints, a smell of pine and snow.

Turn:
- Peter follows the clues instead of jumping to a conclusion.
- The clues point toward a wolverine near the shed / tree line / snowy rocks.

Resolution:
- Peter finds what the wolverine took or hid, learns why it came close, and
  finishes the day with a clear proof image: the test is safe again, the clues
  make sense, and the mystery is solved.

The world is intentionally tiny and classical: one child, one helpful adult,
one mysterious animal, one missing object, one revealing trail.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/test_peter_wolverine_foreshadowing_mystery.py
    python storyworlds/worlds/gpt-5.4-mini/test_peter_wolverine_foreshadowing_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/test_peter_wolverine_foreshadowing_mystery.py --verify
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
    apply: Callable[[World], list[str]]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class StoryParams:
    place: str
    hidden: str
    object_name: str
    clue: str
    helper: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    atmosphere: str
    ending_image: str


@dataclass(frozen=True)
class Hidden:
    id: str
    label: str
    tracks: str
    sound: str
    reason: str
    clue_phrase: str


@dataclass(frozen=True)
class ObjectCfg:
    id: str
    label: str
    place_phrase: str
    missing_phrase: str
    found_phrase: str


@dataclass(frozen=True)
class Clue:
    id: str
    sign: str
    foreshadow: str
    nudge: str


@dataclass(frozen=True)
class Helper:
    id: str
    label: str
    action: str
    ending: str


SETTINGS = {
    "yard": Setting("yard", "the yard", "quiet and still", "The little trail ended by the shed"),
    "woods": Setting("woods", "the woods", "dark with pines", "The clue trail curled under the pines"),
    "bank": Setting("bank", "the creek bank", "soft and damp", "The last prints stopped by the water"),
}

HIDDENS = {
    "wolverine": Hidden("wolverine", "a wolverine", "deep claw marks", "a low growl",
                        "it wanted the shiny paper", "fresh scratches on the wood"),
}

OBJECTS = {
    "test": ObjectCfg("test", "Peter's test paper", "on the table", "missing from the table",
                      "tucked under a crate"),
    "pouch": ObjectCfg("pouch", "a red pencil pouch", "beside the chair", "gone from the chair",
                       "caught behind a log"),
}

CLUES = {
    "foreshadow": Clue("foreshadow", "scratch marks, fur, and tracks",
                       "first came a thin scratch, then a tuft of dark fur, then small tracks",
                       "the clues hinted that something wild had been here"),
    "snow": Clue("snow", "tiny wet paw prints",
                 "on the damp ground, Peter saw tiny wet paw prints",
                 "the prints pointed away from the house"),
}

HELPERS = {
    "mom": Helper("mom", "Peter's mom", "followed the trail and stayed calm", "mom smiled beside Peter"),
    "ranger": Helper("ranger", "the ranger", "helped search the path", "the ranger nodded at the solved mystery"),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava"]
BOY_NAMES = ["Peter", "Ben", "Leo", "Sam"]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for h in HIDDENS:
            for o in OBJECTS:
                for c in CLUES:
                    for he in HELPERS:
                        combos.append((s, h, o, c, he))
    return combos


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.get("clue").meters["noticed"] < THRESHOLD:
        return out
    if ("clue", "foreshadow") in world.fired:
        return out
    world.fired.add(("clue", "foreshadow"))
    out.append("__clue__")
    return out


def _r_search(world: World) -> list[str]:
    out: list[str] = []
    if world.get("peter").memes["curiosity"] < THRESHOLD:
        return out
    if ("search", "trail") in world.fired:
        return out
    world.fired.add(("search", "trail"))
    world.get("peter").memes["resolve"] += 1
    out.append("__search__")
    return out


CAUSAL_RULES = [Rule("clue", _r_clue), Rule("search", _r_search)]


def tell(setting: Setting, hidden: Hidden, object_cfg: ObjectCfg, clue: Clue, helper: Helper) -> World:
    world = World()
    peter = world.add(Entity("Peter", kind="character", type="boy", role="child", traits=["careful"]))
    adult = world.add(Entity(helper.label, kind="character", type="mother" if helper.id == "mom" else "man",
                             role="helper"))
    mystery = world.add(Entity(hidden.id, kind="thing", type="animal", label=hidden.label))
    target = world.add(Entity(object_cfg.id, kind="thing", type="paper", label=object_cfg.label))
    clue_ent = world.add(Entity("clue", kind="thing", type="sign", label=clue.sign))

    peter.memes["curiosity"] = 1
    peter.memes["worry"] = 1
    clue_ent.meters["noticed"] = 1
    world.facts["setting"] = setting
    world.facts["hidden"] = hidden
    world.facts["object"] = object_cfg
    world.facts["clue"] = clue
    world.facts["helper"] = helper

    world.say(
        f"Peter was getting ready for a test at {setting.place}. The room felt "
        f"{setting.atmosphere}, and the paper on the table looked very important."
    )
    world.say(
        f"Then Peter frowned. {object_cfg.missing_phrase.capitalize()}, and in its place "
        f"he found {clue.foreshadow}."
    )
    world.say(
        f"At first, that clue did not make sense. But Peter remembered that {clue.nudge}, "
        f"so he did not rush to guess."
    )

    world.para()
    world.say(
        f"Peter told {helper.label} what he saw. Together they followed the signs: "
        f"{hidden.tracks}, a low sound, and the smell of pine and cold air."
    )
    propagate(world, narrate=False)
    world.say(
        f"The trail led to a hidden place near the {setting.id}, where something had pushed "
        f"{object_cfg.label_word if hasattr(object_cfg, 'label_word') else object_cfg.label} aside."
    )
    world.say(
        f"Behind a crate, Peter found {hidden.label}. It had taken the paper because "
        f"{hidden.reason}."
    )

    world.para()
    world.say(
        f"{helper.action.capitalize()}, and the mystery finally made sense. Peter lifted the "
        f"{object_cfg.label} free, checked the pages, and breathed out."
    )
    world.say(
        f"{helper.ending}. Peter walked back with the test paper safe in his hands, and "
        f"the last clue now felt like a clue on purpose."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hidden: Hidden = f["hidden"]
    obj: ObjectCfg = f["object"]
    clue: Clue = f["clue"]
    return [
        f'Write a mystery story for a young child that includes the words "test", "peter", and "wolverine".',
        f"Tell a foreshadowing mystery where Peter notices {clue.sign} before he learns what happened to the test paper.",
        f"Write a child-friendly mystery in which Peter follows hints and discovers why {hidden.label} was near the missing test.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hidden: Hidden = f["hidden"]
    obj: ObjectCfg = f["object"]
    helper: Helper = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="Who is the story about?",
            answer="It is about Peter, who notices something odd about his test paper and chooses to solve the mystery calmly.",
        ),
        QAItem(
            question="What clue first caught Peter's eye?",
            answer=f"He saw {f['clue'].foreshadow}. That clue mattered because it pointed him toward the place where the missing paper had been moved.",
        ),
        QAItem(
            question="What did Peter find at the end?",
            answer=f"Peter found {hidden.label} near the hidden place, and he found the {obj.label} safe again. The clues all matched once he followed the trail all the way to the end.",
        ),
        QAItem(
            question="How did the helper help?",
            answer=f"{helper.label} followed Peter, stayed calm, and helped search the trail. That made the mystery easier to solve without panic.",
        ),
        QAItem(
            question="Where did the mystery happen?",
            answer=f"It happened at {setting.place}. The quiet place gave Peter room to notice the small clues one by one.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives small hints before the big reveal. Those hints help the reader guess what might happen later.",
        ),
        QAItem(
            question="What is a wolverine?",
            answer="A wolverine is a wild animal with strong claws and thick fur. It can make scratch marks and leave odd signs behind it.",
        ),
        QAItem(
            question="What should you do in a mystery before guessing?",
            answer="You should look carefully at the clues first. Good detectives do not guess too fast.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} role={e.role} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this mystery needs a test, Peter, and a wolverine clue trail.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small foreshadowing mystery for Peter and a wolverine.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hidden", choices=HIDDENS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
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


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HIDDENS:
        lines.append(asp.fact("hidden", h))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    for he in HELPERS:
        lines.append(asp.fact("helper", he))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,O,C,He) :- setting(S), hidden(H), object(O), clue(C), helper(He).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos_py() -> list[tuple[str, str, str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos_py()
              if (args.place is None or c[0] == args.place)
              and (args.hidden is None or c[1] == args.hidden)
              and (args.object_name is None or c[2] == args.object_name)
              and (args.clue is None or c[3] == args.clue)
              and (args.helper is None or c[4] == args.helper)]
    if not combos:
        raise StoryError(explain_rejection())
    place, hidden, obj, clue, helper = rng.choice(combos)
    return StoryParams(place, hidden, obj, clue, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], HIDDENS[params.hidden], OBJECTS[params.object_name], CLUES[params.clue], HELPERS[params.helper])
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


def asp_verify() -> int:
    py = set(valid_combos_py())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
    else:
        print("MISMATCH")
        return 1
    try:
        sample = generate(StoryParams("woods", "wolverine", "test", "foreshadow", "mom"))
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in valid_combos_py()[:5]]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
