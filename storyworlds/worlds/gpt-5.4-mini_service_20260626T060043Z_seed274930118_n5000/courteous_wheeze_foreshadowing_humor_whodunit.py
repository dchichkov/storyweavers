#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/courteous_wheeze_foreshadowing_humor_whodunit.py
================================================================================================

A tiny whodunit storyworld about a missing object, a careful search, a few
courteous suspects, a comic wheeze, and a clue that was hiding in plain sight.

The story is intentionally small and classical:
- one setting
- one missing thing
- a handful of entities with physical meters and emotional memes
- foreshadowing that points at the culprit before the reveal
- humor that lightens the detective work
- a clean resolution that proves what changed

The generated story should feel like a child-friendly mystery: someone notices
something odd, asks polite questions, follows clues, and discovers who moved the
object and why.
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
    hidden_by: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the library"


@dataclass
class Mystery:
    missing: str
    clue_kind: str
    clue_name: str
    clue_phrase: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective: str
    suspect: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_hint(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if suspect.meters.get("noise", 0.0) < THRESHOLD:
        return out
    sig = ("hint",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] = detective.memes.get("suspicion", 0.0) + 1
    out.append(
        "The detective noticed a small wheeze from behind the curtain, and that odd sound felt like a clue wearing boots."
    )
    return out


def _r_giveaway(world: World) -> list[str]:
    out: list[str] = []
    suspect = world.get("suspect")
    missing = world.get("missing")
    if suspect.meters.get("shuffled", 0.0) < THRESHOLD:
        return out
    if missing.hidden_by != suspect.id:
        return out
    sig = ("giveaway",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(
        f"The little bundle behind {suspect.label} gave the game away; the missing {missing.label} had been tucked there all along."
    )
    return out


CAUSAL_RULES = [_r_hint, _r_giveaway]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell_story(setting: Setting, mystery: Mystery, detective_name: str, suspect_name: str, helper_name: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id="detective", kind="character", type="girl", label=detective_name, traits=["courteous", "clever"]))
    suspect = world.add(Entity(id="suspect", kind="character", type="boy", label=suspect_name, traits=["courteous", "nervous"]))
    helper = world.add(Entity(id="helper", kind="character", type="girl", label=helper_name, traits=["helpful", "gentle"]))
    missing = world.add(Entity(id="missing", type="thing", label=mystery.missing, phrase=mystery.missing, owner=detective.id))
    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue_name, phrase=mystery.clue_phrase, hidden_by=suspect.id))

    detective.memes["curiosity"] = 1
    detective.memes["hope"] = 1
    suspect.meters["shuffled"] = 1
    suspect.meters["noise"] = 1
    helper.memes["humor"] = 1

    world.say(
        f"In {setting.place}, {detective.label} found that the {missing.label} was gone, which was a very tidy little tragedy."
    )
    world.say(
        f"{detective.label} stayed courteous and asked everyone polite questions, because rude mysteries never solve themselves."
    )
    world.say(
        f"{suspect.label} answered with a small wheeze and a red face, as if even his breath had forgotten its manners."
    )

    world.para()
    world.say(
        f"{helper.label} tried to help and whispered a joke so quietly that even the bookshelf seemed to grin."
    )
    world.say(
        "That made the detective smile, but it also made the room feel more suspicious, which is exactly how a good whodunit should behave."
    )
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The detective checked the curtains, the chair, and the low table, then noticed the faint outline of {clue.label} beside {suspect.label}."
    )
    world.say(
        f"That was the foreshadowing paying off: the clue had been waiting there like a cat in a hatbox."
    )
    world.say(
        f"With another courteous question, {detective.label} asked {suspect.label} to step aside."
    )

    missing.hidden_by = suspect.id
    world.para()
    world.say(
        f"Under the cushion, the missing {missing.label} was hiding in a little bundle, snug and safe."
    )
    world.say(
        f"{suspect.label} confessed that he had borrowed it for a surprise and then laughed at himself with one more wheeze."
    )
    world.say(
        f"{detective.label} forgave him, because the surprise was for {helper.label}, and the whole room had already become a joke with a happy ending."
    )
    world.say(
        f"In the end, the {missing.label} was back where it belonged, the clue was solved, and everyone could breathe normally again."
    )

    world.facts.update(
        detective=detective,
        suspect=suspect,
        helper=helper,
        missing=missing,
        clue=clue,
        setting=setting,
        mystery=mystery,
    )
    return world


SETTINGS = {
    "library": Setting(place="the library"),
    "classroom": Setting(place="the classroom"),
    "kitchen": Setting(place="the kitchen"),
}

MYSTERIES = {
    "bell": Mystery(
        missing="silver bell",
        clue_kind="shine",
        clue_name="tiny shine",
        clue_phrase="a tiny shine under the chair",
    ),
    "cookie": Mystery(
        missing="cookie tin",
        clue_kind="crumb",
        clue_name="crumb trail",
        clue_phrase="a crumb trail near the curtain",
    ),
    "book": Mystery(
        missing="picture book",
        clue_kind="page",
        clue_name="dog-eared page",
        clue_phrase="a dog-eared page on the rug",
    ),
}

NAMES = ["Maya", "Lena", "Iris", "Nora", "June", "Eli", "Owen", "Theo", "Pia", "Ada"]


@dataclass
class StoryContext:
    world: World


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: {setting} and {mystery} do not make a reasonable mystery here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny courteous whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--detective")
    ap.add_argument("--suspect")
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
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in valid_combos():
            raise StoryError(explain_rejection(args.setting, args.mystery))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(combos)
    detective = args.detective or rng.choice(NAMES)
    suspect = args.suspect or rng.choice([n for n in NAMES if n != detective])
    helper = args.helper or rng.choice([n for n in NAMES if n not in {detective, suspect}])
    return StoryParams(setting=setting, mystery=mystery, detective=detective, suspect=suspect, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.setting], MYSTERIES[params.mystery], params.detective, params.suspect, params.helper)
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
        f'Write a child-friendly whodunit set in {f["setting"].place} about a missing {f["missing"].label}.',
        f"Tell a short mystery where {f['detective'].label} stays courteous while asking about a vanished {f['missing'].label}.",
        f"Write a humorous detective story with a wheezy suspect, a small clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d, s, h, m, c = f["detective"], f["suspect"], f["helper"], f["missing"], f["clue"]
    return [
        QAItem(
            question=f"What was missing in {f['setting'].place}?",
            answer=f"The missing thing was the {m.label}, and everyone noticed when it was gone.",
        ),
        QAItem(
            question=f"Who stayed courteous while asking questions?",
            answer=f"{d.label} stayed courteous and asked polite questions instead of making a scene.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The {c.label} helped solve it, because it pointed toward {s.label}.",
        ),
        QAItem(
            question=f"Why did {s.label} seem suspicious at first?",
            answer=f"{s.label} seemed suspicious because he made a wheezy sound and had been near the hiding place.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the {m.label} returned, the surprise explained, and everyone laughing gently.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to figure out who did something or where something went.",
        ),
        QAItem(
            question="What does courteous mean?",
            answer="Courteous means polite and kind, especially when talking to other people.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small hint about something important before it happens.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when there is a setting and a missing object and a clue.
valid(S, M) :- setting(S), mystery(M).

% The clue is suggestive when it belongs to the missing object's hiding place.
suggestive(C, M) :- clue(C), missing(M).

% A whodunit is interesting when there is a polite detective and a noisy suspect.
interesting(S, M) :- valid(S, M), courteous_detective, wheezy_suspect.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    lines.append(asp.fact("courteous_detective"))
    lines.append(asp.fact("wheezy_suspect"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


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
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="library", mystery="bell", detective="Maya", suspect="Owen", helper="Pia"),
    StoryParams(setting="classroom", mystery="cookie", detective="Lena", suspect="Theo", helper="Ada"),
    StoryParams(setting="kitchen", mystery="book", detective="Nora", suspect="Eli", helper="June"),
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid mystery combos")
        for s, m in asp_valid_combos():
            print(s, m)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
