#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fragile_dinky_surprise_flashback_detective_story.py
===================================================================================

A small standalone storyworld for a child-friendly detective mystery with a
surprise and a flashback.

Seed words:
- fragile
- dinky

Style:
- Detective Story

Core premise:
A child detective notices a tiny, fragile clue go missing, follows a trail of
ordinary evidence, remembers an earlier flashback, and discovers a surprising
but gentle resolution.

This world is intentionally narrow: it generates a few plausible detective
stories rather than a wide grab-bag of weak mysteries.
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"spotted": 0.0, "missing": 0.0, "found": 0.0, "moved": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "worry": 0.0, "relief": 0.0, "surprise": 0.0}

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    cozy: str
    features: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    label: str
    fragile: bool = False
    dinky: bool = False
    hidden_in: str = ""
    phrase: str = ""

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Action:
    id: str
    verb: str
    method: str
    risk: str
    solve: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


PLACE = Place(
    "study",
    "a little detective study",
    "The room was cozy, with a lamp, a shelf, and a corkboard full of string.",
    ["lamp", "shelf", "board"],
)

CLUES = {
    "pebble": Clue("pebble", "a fragile glass pebble", fragile=True, dinky=True, hidden_in="the teacup", phrase="a tiny glass pebble"),
    "button": Clue("button", "a dinky brass button", fragile=False, dinky=True, hidden_in="the drawer", phrase="a tiny brass button"),
    "note": Clue("note", "a folded note", fragile=True, dinky=False, hidden_in="under the book", phrase="a folded note with a clue"),
}

ACTIONS = {
    "tap": Action("tap", "tap", "a careful tap", "might crack", "set it on a soft cloth", tags={"fragile"}),
    "search": Action("search", "search", "a slow search", "might miss", "look in the right place", tags={"dinky"}),
    "warm": Action("warm", "warm", "a gentle warmth", "might curl", "keep it safe", tags={"flashback"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Tom", "Eli", "Noah", "Ben", "Max"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for clue_id, clue in CLUES.items():
        for action_id, action in ACTIONS.items():
            if clue.fragile and "fragile" in action.tags:
                combos.append((PLACE.id, clue_id, action_id))
            elif clue.dinky and "dinky" in action.tags:
                combos.append((PLACE.id, clue_id, action_id))
    return sorted(set(combos))


@dataclass
@dataclass
class StoryParams:
    place: str
    clue: str
    action: str
    detective: str
    gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Child-friendly detective story world.")
    ap.add_argument("--place", choices=[PLACE.id], default=None)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--detective", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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


def explain_rejection(clue: Clue, action: Action) -> str:
    return f"(No story: {action.verb} is not a good fit for {clue.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.clue and args.action:
        clue, action = CLUES[args.clue], ACTIONS[args.action]
        if (PLACE.id, args.clue, args.action) not in combos:
            raise StoryError(explain_rejection(clue, action))

    if args.gender and args.detective:
        pass

    filtered = [c for c in combos if (args.clue is None or c[1] == args.clue) and (args.action is None or c[2] == args.action)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    _, clue_id, action_id = rng.choice(filtered)
    detective = args.detective or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if detective in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != detective])
    helper_gender = args.helper_gender or ("girl" if helper in GIRL_NAMES else "boy")
    return StoryParams(PLACE.id, clue_id, action_id, detective, gender, helper, helper_gender)


def _flashback_line(world: World, detective: Entity, clue: Clue) -> None:
    detective.memes["surprise"] += 1
    world.say(
        f"Then {detective.id} had a flashback: earlier that morning, {detective.pronoun('subject')} had seen {clue.label} near the tea set."
    )


def tell(place: Place, clue: Clue, action: Action, detective_name: str, detective_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    suspect = world.add(Entity(id="Suspect", kind="character", type="woman", role="suspect", label="the kind neighbor"))

    clue_ent = world.add(Entity(id="clue", type="thing", label=clue.label, traits=["fragile" if clue.fragile else "dinky"]))
    clue_ent.attrs["hidden_in"] = clue.hidden_in

    detective.memes["curiosity"] += 1
    helper.memes["curiosity"] += 1
    world.say(f"{place.cozy} {detective.id} was a small detective with sharp eyes, and {helper.id} was always ready to help.")
    world.say(f"That day, a case began with {clue.label}: it looked fragile, and it felt dinky enough to lose in a blink.")
    world.say(f"The clue should have been {clue.hidden_in}, but now it was missing from its spot.")

    world.para()
    detective.meters["missing"] += 1
    detective.memes["worry"] += 1
    world.say(f'{detective.id} frowned. "{clue.label} is gone," {detective.pronoun()} said. "I need to {action.method} the trail."')
    world.say(f"{helper.id} pointed at the room. Together they began to {action.verb} around the shelves and the lamp.")

    _flashback_line(world, detective, clue)
    world.para()

    clue_ent.meters["found"] += 1
    clue_ent.meters["moved"] += 1
    detective.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(f"The surprise was simple: {suspect.label_word} had only moved {clue.label} so it would not get crushed.")
    world.say(f"She had tucked it somewhere safer, and {helper.id} found it right where the flashback said it would be.")

    world.para()
    detective.meters["spotted"] += 1
    detective.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(f"{detective.id} smiled and wrapped {detective.pronoun('possessive')} hands around the tiny clue.")
    world.say(f"It was fragile, but safe now, and the case ended with the board finally showing the truth in one neat line.")

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        clue=clue,
        action=action,
        place=place,
        outcome="found",
        flashback=True,
        surprise=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue"]
    action = f["action"]
    detective = f["detective"]
    return [
        f'Write a short detective story for a young child that includes the words "fragile" and "dinky".',
        f"Tell a mystery story where {detective.id} follows a tiny clue, remembers a flashback, and gets a surprise at the end.",
        f"Write a gentle detective story where a {clue.label} goes missing, but the case is solved without any danger.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    clue = f["clue"]
    qas = [
        QAItem(
            question="Who solved the mystery?",
            answer=f"{detective.id} solved it with help from {helper.id}. {detective.id} followed the clue, remembered the flashback, and found the truth."
        ),
        QAItem(
            question="Why was the clue important?",
            answer=f"The clue was important because it was tiny and easy to lose. It helped point the detective toward where the missing thing had been moved."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that nobody had stolen {clue.label}; it had only been moved to a safer spot. That made the ending calm instead of scary."
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does fragile mean?",
            answer="Fragile means something can break or get damaged easily, so it should be handled with care."
        ),
        QAItem(
            question="What does dinky mean?",
            answer="Dinky means very small or tiny. A dinky thing is easy to overlook."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story jumps back to something that happened earlier. It helps explain a clue or a memory."
        ),
        QAItem(
            question="What makes a detective story fun?",
            answer="A detective story is fun because a character looks for clues, asks questions, and solves a problem."
        ),
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
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, A) :- place(P), clue(C), action(A), fragile(C), fragile_action(A).
valid(P, C, A) :- place(P), clue(C), action(A), dinky(C), dinky_action(A).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", PLACE.id))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.fragile:
            lines.append(asp.fact("fragile", cid))
        if clue.dinky:
            lines.append(asp.fact("dinky", cid))
    for aid, action in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if "fragile" in action.tags:
            lines.append(asp.fact("fragile_action", aid))
        if "dinky" in action.tags:
            lines.append(asp.fact("dinky_action", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo lists.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def valid_combo_filter(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    return [c for c in combos if (args.clue is None or c[1] == args.clue) and (args.action is None or c[2] == args.action)]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.action and (PLACE.id, args.clue, args.action) not in valid_combos():
        raise StoryError(explain_rejection(CLUES[args.clue], ACTIONS[args.action]))
    combos = valid_combo_filter(args)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    _, clue_id, action_id = rng.choice(combos)
    detective = args.detective or rng.choice(GIRL_NAMES + BOY_NAMES)
    gender = args.gender or ("girl" if detective in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != detective])
    helper_gender = args.helper_gender or ("girl" if helper in GIRL_NAMES else "boy")
    return StoryParams(PLACE.id, clue_id, action_id, detective, gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACE, CLUES[params.clue], ACTIONS[params.action], params.detective, params.gender, params.helper, params.helper_gender)
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


CURATED = [
    StoryParams(PLACE.id, "pebble", "tap", "Mia", "girl", "Tom", "boy"),
    StoryParams(PLACE.id, "button", "search", "Noah", "boy", "Ava", "girl"),
    StoryParams(PLACE.id, "note", "warm", "Lily", "girl", "Ben", "boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for p, c, a in combos:
            print(f"  {p:6} {c:8} {a}")
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
