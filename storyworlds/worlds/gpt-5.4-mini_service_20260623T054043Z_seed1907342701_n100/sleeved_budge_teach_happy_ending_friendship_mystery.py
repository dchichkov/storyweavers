#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/sleeved_budge_teach_happy_ending_friendship_mystery.py
============================================================================================================

A small storyworld about a friendship mystery that ends happily.

Seed premise:
- A child and a friend notice something puzzling.
- They look, test, and gently search.
- A helpful grown-up teaches a safe trick.
- The mystery turns out to be a simple physical snag, not anything scary.

The world is built to naturally include the words:
- sleeved
- budge
- teach

The story style leans mystery: clues, noticing, checking, and a reveal.
The ending is bright and reassuring: friendship helps solve the puzzle.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    clue: str
    mystery_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    blocked_by: str
    reveal: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    method: str
    teach_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ending:
    id: str
    label: str
    finish: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    place: Place
    mystery: Mystery
    helper: Helper
    ending: Ending
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.mystery, self.helper, self.ending)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _rule_discovery(world: World) -> list[str]:
    out = []
    if world.facts["clue_seen"] and ("discover" not in world.fired):
        world.fired.add(("discover",))
        for p in [world.get("hero"), world.get("friend")]:
            p.memes["curiosity"] = p.memes.get("curiosity", 0.0) + 1
        out.append("__discovery__")
    return out


def _rule_resolve(world: World) -> list[str]:
    out = []
    if world.facts["taught"] and world.facts["mystery_opened"] and ("resolve",) not in world.fired:
        world.fired.add(("resolve",))
        world.facts["solved"] = True
        world.get("mystery").meters["stuck"] = 0.0
        out.append("__resolve__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_rule_discovery, _rule_resolve):
            msgs = rule(world)
            if msgs:
                changed = True
                produced.extend(m for m in msgs if not m.startswith("__"))
    if narrate:
        for msg in produced:
            world.say(msg)


def valid_combos() -> list[tuple[str, str, str, str]]:
    rows = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for helper in HELPERS:
                for ending in ENDINGS:
                    if mystery.reveal and ending.id == "happy":
                        rows.append((place, mystery, helper, ending))
    return rows


@dataclass
class StoryParams:
    place: str = "library"
    mystery: str = "blue_bell"
    helper: str = "kind_teacher"
    ending: str = "happy"
    hero_name: str = "Maya"
    hero_gender: str = "girl"
    friend_name: str = "Jesse"
    friend_gender: str = "boy"
    adult_name: str = "Ms. Park"
    adult_gender: str = "woman"
    seed: Optional[int] = None


PLACES = {
    "library": Place("library", "the library corner", "a bell keeps going quiet", "stuck ring", {"quiet", "books"}),
    "garden": Place("garden", "the garden shed", "a gate will not open", "stuck latch", {"outdoors", "metal"}),
    "music_room": Place("music_room", "the music room", "a box will not open", "stuck lid", {"music", "wood"}),
    "classroom": Place("classroom", "the classroom shelf", "a ribbon will not move", "stuck ribbon", {"school", "cloth"}),
}

MYSTERIES = {
    "blue_bell": Mystery("blue_bell", "the blue bell mystery", "a sleeve", "the bell was caught on a sleeve", "free the bell from the sleeve", {"bell", "sleeve", "cloth"}),
    "jammed_box": Mystery("jammed_box", "the jammed box mystery", "a paper clip", "the lid was wedged by a paper clip", "lift the lid and slip out the clip", {"box", "clip", "metal"}),
    "stuck_gate": Mystery("stuck_gate", "the stuck gate mystery", "a vine", "the gate was held by a vine", "move the vine away from the latch", {"gate", "vine", "outdoors"}),
}

HELPERS = {
    "kind_teacher": Helper("kind_teacher", "a kind teacher", "tap the hidden catch", "The teacher said, 'Let me teach you a tiny trick: look close, then try the small part that can move.'", {"teacher", "teach"}),
    "neighbor": Helper("neighbor", "a friendly neighbor", "nudge the latch", "The neighbor smiled and said, 'I can teach you to check for a tiny snag before you pull hard.'", {"neighbor", "teach"}),
    "librarian": Helper("librarian", "the librarian", "slide the sleeve aside", "The librarian said, 'I can teach you to use gentle hands and look for the thing that is stuck.'", {"librarian", "teach"}),
}

ENDINGS = {
    "happy": Ending("happy", "a happy ending", "everything works again", {"happy"}),
}

GIRL_NAMES = ["Maya", "Lena", "Ivy", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Jesse", "Theo", "Eli", "Noah", "Finn", "Leo"]


def reason_ok(place: Place, mystery: Mystery, helper: Helper, ending: Ending) -> bool:
    return mystery.id in {"blue_bell", "jammed_box", "stuck_gate"} and ending.id == "happy"


def explain_rejection() -> str:
    return "(No story: this world only keeps mystery puzzles that can end happily.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship mystery storyworld with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--adult")
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
    combos = [(p, m, h, e) for p, m, h, e in valid_combos()
              if (args.place is None or p == args.place)
              and (args.mystery is None or m == args.mystery)
              and (args.helper is None or h == args.helper)
              and (args.ending is None or e == args.ending)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mystery, helper, ending = rng.choice(sorted(combos))
    hero_gender = "girl"
    friend_gender = "boy"
    hero_name = args.name or rng.choice(GIRL_NAMES)
    friend_name = args.friend or rng.choice([n for n in BOY_NAMES if n != hero_name])
    adult_name = args.adult or "Ms. Park"
    return StoryParams(place=place, mystery=mystery, helper=helper, ending=ending,
                       hero_name=hero_name, hero_gender=hero_gender,
                       friend_name=friend_name, friend_gender=friend_gender,
                       adult_name=adult_name)


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]
    ending = ENDINGS[params.ending]
    world = World(place, mystery, helper, ending)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero_name, role="hero", meters={"hope": 0.0}, memes={"curiosity": 0.0, "friendship": 1.0, "worry": 0.0}))
    friend = world.add(Entity(id="friend", kind="character", type=params.friend_gender, label=params.friend_name, role="friend", meters={"hope": 0.0}, memes={"curiosity": 0.0, "friendship": 1.0, "worry": 0.0}))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_gender, label=params.adult_name, role="adult", meters={"help": 0.0}, memes={"calm": 1.0}))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.blocked_by, phrase=mystery.blocked_by, tags=set(mystery.tags), meters={"stuck": 1.0}))
    world.facts.update(hero=hero, friend=friend, adult=adult, clue=clue, place=place, mystery=mystery, helper=helper, ending=ending, clue_seen=False, mystery_opened=False, taught=False, solved=False)
    world.say(f"{hero.label} and {friend.label} found a little mystery at {place.label}.")
    world.say(f"{place.clue.capitalize()}! They looked closer and saw {mystery.blocked_by}.")
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)
    world.para()
    world.say(f"{friend.label} tried to budge it, but it would not budge at all.")
    world.say(f"{hero.label} touched the spot where the clue was stuck, and {helper.teach_line}")
    world.facts["taught"] = True
    world.facts["mystery_opened"] = True
    world.say(f"{adult.label} helped {helper.method}, and the stuck thing finally moved.")
    propagate(world, narrate=False)
    world.para()
    if world.facts["solved"]:
        hero.memes["friendship"] += 1
        friend.memes["friendship"] += 1
        hero.meters["hope"] += 1
        friend.meters["hope"] += 1
        world.say(f"Under the sleeve, they found the answer: {mystery.reveal}.")
        world.say(f"They laughed, because the mystery was only a small snag, and {adult.label} had taught them a safe way to check it.")
        world.say(f"By the end, {mystery.fix}, and {ending.finish}.")
    world.facts["resolved"] = world.facts["solved"]
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child that uses the words "sleeved", "budge", and "teach" and ends happily.',
        f"Tell a friendship mystery set in {f['place'].label} where {f['hero'].label} and {f['friend'].label} notice something stuck, ask a grown-up for help, and solve it together.",
        f"Write a gentle story about friends who think a puzzle is big and scary at first, but learn it was only a small snag.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    adult = f["adult"]
    mystery = f["mystery"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who found the mystery at {place.label}?",
            answer=f"{hero.label} and {friend.label} found it together. They were friends, so they looked side by side and shared the puzzle."
        ),
        QAItem(
            question=f"Why would not the stuck thing budge?",
            answer=f"It would not budge because {mystery.blocked_by} was holding it in place. That made the mystery look bigger until the grown-up showed a gentle way to move it."
        ),
        QAItem(
            question=f"What did {adult.label} teach them to do?",
            answer=f"{adult.label} taught them to use a tiny, careful move instead of pulling hard. That helped them open the mystery without breaking anything."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily. The puzzle was only a small snag, and {hero.label} and {friend.label} got to smile together when they saw the answer."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does budge mean?", "If something budges, it moves a little. If it will not budge, it stays stuck in place."),
        QAItem("What does teach mean?", "To teach means to show someone how to do something or explain it in a helpful way."),
        QAItem("What is a mystery?", "A mystery is something puzzling that you have to look at closely to understand."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,M,H,E) :- place(P), mystery(M), helper(H), ending(E), happy(E), reveal(M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m, obj in MYSTERIES.items():
        lines.append(asp.fact("mystery", m))
        lines.append(asp.fact("reveal", m))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for e in ENDINGS:
        lines.append(asp.fact("ending", e))
        lines.append(asp.fact("happy", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    ok = set(asp_valid_combos()) == set(valid_combos())
    smoke = True
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, helper=None, ending=None, name=None, friend=None, adult=None), random.Random(0)))
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception:
        smoke = False
    if ok and smoke:
        print("OK: ASP parity and story smoke test passed.")
        return 0
    if not ok:
        print("MISMATCH: ASP and Python valid combos differ.")
    if not smoke:
        print("MISMATCH: story generation smoke test failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.mystery not in MYSTERIES or params.helper not in HELPERS or params.ending not in ENDINGS:
        raise StoryError("Invalid story params.")
    world = tell(params)
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
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  facts={world.facts}")
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
    StoryParams(place="library", mystery="blue_bell", helper="kind_teacher", ending="happy", hero_name="Maya", hero_gender="girl", friend_name="Jesse", friend_gender="boy", adult_name="Ms. Park"),
    StoryParams(place="music_room", mystery="jammed_box", helper="librarian", ending="happy", hero_name="Ivy", hero_gender="girl", friend_name="Noah", friend_gender="boy", adult_name="Mr. Lin"),
    StoryParams(place="garden", mystery="stuck_gate", helper="neighbor", ending="happy", hero_name="Lena", hero_gender="girl", friend_name="Leo", friend_gender="boy", adult_name="Mrs. Bell"),
    StoryParams(place="classroom", mystery="blue_bell", helper="kind_teacher", ending="happy", hero_name="Ava", hero_gender="girl", friend_name="Finn", friend_gender="boy", adult_name="Ms. Park"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship mystery storyworld with a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ending", choices=ENDINGS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--adult")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
    for i, s in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(s, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
