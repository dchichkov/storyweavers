#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
=======================================================

A tiny whodunit-style storyworld about a missing javelin, a shared plan, and a
careful reveal. The world is built from typed entities with meters and memes,
state changes drive the prose, and the ending proves what changed.

This world keeps close to a mystery tone:
- there is a suspenseful search,
- a sharing beat where clues are pooled,
- a final reveal that explains who moved the javelin and why.

The premise is intentionally small and child-facing:
A class is preparing for a field-day game. One javelin-shaped foam baton goes
missing, and two children must share clues, follow the trail, and figure out
where it went before the game starts.

The world supports:
- default run
- -n / --all / --seed
- --trace / --qa / --json
- --asp / --verify / --show-asp

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
SUSPENSE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Location:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class Javelin:
    id: str
    label: str
    material: str
    color: str
    place_hint: str
    movable: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    hint: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    setting: str
    finder: str
    finder_gender: str
    sharer: str
    sharer_gender: str
    adult: str
    javelin_name: str
    javelin_color: str
    clue1: str
    clue2: str
    mischief: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str):
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
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


@dataclass
class Theme:
    id: str
    place: str
    event: str
    search_phrase: str
    reveal_place: str
    ending_image: str


@dataclass
class Mischief:
    id: str
    source: str
    reason: str
    shadow: str


THEMES = {
    "gym": Theme(
        id="gym",
        place="the school gym",
        event="field day",
        search_phrase="the race would begin soon",
        reveal_place="the equipment closet",
        ending_image="the javelin lay back in its rack, ready for the next throw",
    ),
    "park": Theme(
        id="park",
        place="the city park",
        event="the picnic game",
        search_phrase="the long grass hid everything",
        reveal_place="the picnic table",
        ending_image="the javelin rested beside the lunch basket, safely shared",
    ),
    "hall": Theme(
        id="hall",
        place="the bright hall",
        event="the team demo",
        search_phrase="the crowd was already whispering",
        reveal_place="the stage curtain",
        ending_image="the javelin waited on the table, no longer a mystery",
    ),
}

MISCHIEF = {
    "hide": Mischief(
        id="hide",
        source="wanted to hide it as a prank",
        reason="to make everyone look in the wrong place",
        shadow="a sneaky little prank",
    ),
    "borrow": Mischief(
        id="borrow",
        source="borrowed it for a pretend game",
        reason="to use it in a make-believe quest",
        shadow="a secret pretend game",
    ),
    "practice": Mischief(
        id="practice",
        source="moved it to practice safely with a foam target",
        reason="to make room for a safe throw",
        shadow="a careful practice",
    ),
}

JAVELINS = {
    "blue": Javelin(
        id="javelin",
        label="javelin",
        material="foam",
        color="blue",
        place_hint="thin and blue like a sky ribbon",
    ),
    "red": Javelin(
        id="javelin",
        label="javelin",
        material="foam",
        color="red",
        place_hint="red and light like a toy arrow",
    ),
    "green": Javelin(
        id="javelin",
        label="javelin",
        material="foam",
        color="green",
        place_hint="green and soft like a leaf stem",
    ),
}

CLUES = {
    "chalk": Clue(id="chalk", label="a chalk smudge", place="the floor", hint="dragged along the hallway"),
    "glove": Clue(id="glove", label="one glove", place="the bench", hint="left by the game bag"),
    "note": Clue(id="note", label="a folded note", place="the notice board", hint="pointing toward the hidden place"),
    "ribbon": Clue(id="ribbon", label="a blue ribbon", place="the hook", hint="tied near the right door"),
    "dust": Clue(id="dust", label="a dust mark", place="the shelf", hint="showing something had been moved"),
}

NAMES_GIRL = ["Mia", "Nora", "Lily", "Zoe", "Ella", "Ruby", "Ava"]
NAMES_BOY = ["Leo", "Finn", "Max", "Eli", "Noah", "Theo", "Ben"]
TRAITS = ["careful", "curious", "quiet", "bold", "thoughtful", "patient"]


class Reasoner:
    @staticmethod
    def suspicious(world: World) -> bool:
        return world.get("mystery").meters.get("uncertainty", 0.0) >= SUSPENSE_MIN

    @staticmethod
    def shared_clues(world: World) -> bool:
        a = world.get("finder")
        b = world.get("sharer")
        return a.memes.get("trust", 0.0) >= 1.0 and b.memes.get("helpful", 0.0) >= 1.0

    @staticmethod
    def revealed(world: World) -> bool:
        return world.get("javelin").attrs.get("found", False)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for mid in MISCHIEF:
        lines.append(asp.fact("mischief", mid))
    for jid, j in JAVELINS.items():
        lines.append(asp.fact("javelin", jid))
        lines.append(asp.fact("material", jid, j.material))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    lines.append(asp.fact("suspense_min", int(SUSPENSE_MIN)))
    return "\n".join(lines)


ASP_RULES = r"""
suspicious :- uncertainty(U), suspense_min(M), U >= M.
shared_clues :- trust(T), helpful(H), T >= 1, H >= 1.
found :- moved_to(hidden_place).
reveal :- suspicious, shared_clues, found.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def _pick_name(rng: random.Random, gender: str) -> str:
    pool = NAMES_GIRL if gender == "girl" else NAMES_BOY
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in THEMES:
        raise StoryError("Unknown setting.")
    setting = args.setting or rng.choice(sorted(THEMES))
    finder_gender = rng.choice(["girl", "boy"])
    sharer_gender = "boy" if finder_gender == "girl" else "girl" if rng.random() < 0.6 else finder_gender
    finder = args.finder or _pick_name(rng, finder_gender)
    sharer = args.sharer or _pick_name(rng, sharer_gender)
    if sharer == finder:
        sharer = _pick_name(rng, "girl" if finder_gender == "boy" else "boy")
    adult = args.adult or rng.choice(["teacher", "coach", "parent"])
    javelin_name = args.javelin or rng.choice(sorted(JAVELINS))
    clue1, clue2 = rng.sample(sorted(CLUES), 2)
    mischief = args.mischief or rng.choice(sorted(MISCHIEF))
    return StoryParams(
        setting=setting,
        finder=finder,
        finder_gender=finder_gender,
        sharer=sharer,
        sharer_gender=sharer_gender,
        adult=adult,
        javelin_name=javelin_name,
        javelin_color=JAVELINS[javelin_name].color,
        clue1=clue1,
        clue2=clue2,
        mischief=mischief,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful sharing whodunit about a missing javelin.")
    ap.add_argument("--setting", choices=sorted(THEMES))
    ap.add_argument("--finder")
    ap.add_argument("--sharer")
    ap.add_argument("--adult")
    ap.add_argument("--javelin", choices=sorted(JAVELINS))
    ap.add_argument("--mischief", choices=sorted(MISCHIEF))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World()
    theme = THEMES[params.setting]
    mystery = world.add(Location(id="mystery", label="the mystery table", meters={"uncertainty": 2.0}, memes={"suspense": 1.0}))
    finder = world.add(Entity(id="finder", kind="character", type=params.finder_gender, role="finder", label=params.finder, memes={"curiosity": 1.0, "trust": 0.0}))
    sharer = world.add(Entity(id="sharer", kind="character", type=params.sharer_gender, role="sharer", label=params.sharer, memes={"helpful": 1.0, "trust": 1.0}))
    adult = world.add(Entity(id="adult", kind="character", type="adult", role="adult", label=params.adult, memes={"calm": 1.0}))
    javelin = world.add(Javelin(id="javelin", label="javelin", material="foam", color=params.javelin_color, place_hint=""))
    clue_a = world.add(Clue(id="clue1", label=CLUES[params.clue1].label, place=CLUES[params.clue1].place, hint=CLUES[params.clue1].hint))
    clue_b = world.add(Clue(id="clue2", label=CLUES[params.clue2].label, place=CLUES[params.clue2].place, hint=CLUES[params.clue2].hint))
    world.facts.update(theme=theme, params=params, finder=finder, sharer=sharer, adult=adult, javelin=javelin, clue1=clue_a, clue2=clue_b)
    return world


def suspect_moment(world: World, params: StoryParams) -> None:
    theme = world.facts["theme"]
    finder = world.get("finder")
    sharer = world.get("sharer")
    javelin = world.get("javelin")
    finder.memes["worry"] = finder.memes.get("worry", 0.0) + 1.0
    world.get("mystery").meters["uncertainty"] = 2.0
    world.say(f"At {theme.place}, {finder.label} stopped short. The foam javelin was gone, and {theme.search_phrase}.")
    world.say(f'"Where did it go?" {finder.label} whispered, looking at the empty hook where the blue slot should have been.')
    world.say(f"{sharer.label} leaned closer. {sharer.label_word.capitalize()} did not answer right away, which made the room feel even quieter.")


def share_clues(world: World, params: StoryParams) -> None:
    finder = world.get("finder")
    sharer = world.get("sharer")
    c1 = world.get("clue1")
    c2 = world.get("clue2")
    finder.memes["trust"] = finder.memes.get("trust", 0.0) + 1.0
    sharer.memes["helpful"] = sharer.memes.get("helpful", 0.0) + 1.0
    world.say(f"{finder.label} found {c1.label} near {c1.place}, and {sharer.label} found {c2.label} near {c2.place}.")
    world.say(f'They shared the clues. "{c1.hint}," said {finder.label}. "{c2.hint}," said {sharer.label}.')
    world.say("Together the little clues started to fit, like puzzle pieces clicking into place.")
    world.get("mystery").meters["uncertainty"] = 1.0


def reveal(world: World, params: StoryParams) -> None:
    theme = world.facts["theme"]
    finder = world.get("finder")
    sharer = world.get("sharer")
    adult = world.get("adult")
    javelin = world.get("javelin")
    mis = MISCHIEF[params.mischief]
    javelin.attrs["found"] = True
    javelin.attrs["hidden_place"] = theme.reveal_place
    world.say(f"They hurried to {theme.reveal_place}, where the last clue pointed.")
    world.say(f"There, behind the curtain and under a folded mat, the javelin was waiting.")
    world.say(f"It had not been lost at all; someone had {mis.source}, and that made the whole search feel suspicious.")
    world.say(f"{adult.label_word.capitalize()} came over, listened to both children, and nodded. “Now we know the whole story,” {adult.pronoun()} said.")
    world.say(f"{adult.label_word.capitalize()} praised them for sharing clues instead of guessing alone.")


def ending(world: World, params: StoryParams) -> None:
    theme = world.facts["theme"]
    finder = world.get("finder")
    sharer = world.get("sharer")
    adult = world.get("adult")
    world.say(f"The mystery was solved, and the field-day game could begin.")
    world.say(f"{finder.label} and {sharer.label} carried the javelin together, one on each side, so nobody had to worry about dropping it.")
    world.say(theme.ending_image)


def generate_story(world: World, params: StoryParams) -> None:
    suspect_moment(world, params)
    world.para()
    share_clues(world, params)
    world.para()
    reveal(world, params)
    world.para()
    ending(world, params)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    generate_story(world, params)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    theme = world.facts["theme"]
    return [
        f"Write a whodunit-style story about a missing javelin at {theme.place}. Include suspense, clue-sharing, and a clear reveal.",
        f"Tell a child-facing mystery where {p.finder} and {p.sharer} share clues to find the foam javelin before {theme.event} starts.",
        f"Make the story feel like a small detective puzzle: someone moved the javelin, the children compare clues, and the ending explains what happened.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    theme = world.facts["theme"]
    mis = MISCHIEF[p.mischief]
    return [
        QAItem(
            question=f"What went missing in the story?",
            answer="The foam javelin went missing, which started the whole mystery.",
        ),
        QAItem(
            question=f"Why did the room feel tense at the start?",
            answer=f"Because the javelin was gone and {theme.search_phrase}, so the children did not know what had happened.",
        ),
        QAItem(
            question=f"What did {p.finder} and {p.sharer} do with the clues?",
            answer="They shared the clues with each other, compared them, and used them together instead of solving the mystery alone.",
        ),
        QAItem(
            question=f"Where did the search lead them?",
            answer=f"It led them to {theme.reveal_place}, where the javelin had been hidden.",
        ),
        QAItem(
            question="Who explained the mystery at the end?",
            answer=f"The {p.adult} listened and explained that someone had {mis.source}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a javelin in this world?", answer="It is a foam sports baton used for a child-sized field-day game."),
        QAItem(question="What does it mean to share clues?", answer="It means telling each other what you found so the mystery can be solved together."),
        QAItem(question="Why is suspense useful in a mystery?", answer="It keeps the reader wondering what happened until the clues are put together."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if getattr(e, "meters", None):
            shown = {k: v for k, v in e.meters.items() if v}
            if shown:
                bits.append(f"meters={shown}")
        if getattr(e, "memes", None):
            shown = {k: v for k, v in e.memes.items() if v}
            if shown:
                bits.append(f"memes={shown}")
        if getattr(e, "attrs", None):
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful sharing whodunit about a missing javelin.")
    ap.add_argument("--setting", choices=sorted(THEMES))
    ap.add_argument("--finder")
    ap.add_argument("--sharer")
    ap.add_argument("--adult")
    ap.add_argument("--javelin", choices=sorted(JAVELINS))
    ap.add_argument("--mischief", choices=sorted(MISCHIEF))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _rng_name(rng: random.Random, gender: str) -> str:
    return rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(sorted(THEMES))
    finder_gender = rng.choice(["girl", "boy"])
    sharer_gender = rng.choice(["girl", "boy"])
    finder = args.finder or _rng_name(rng, finder_gender)
    sharer = args.sharer or _rng_name(rng, sharer_gender)
    if sharer == finder:
        sharer = _rng_name(rng, "girl" if finder_gender == "boy" else "boy")
    adult = args.adult or rng.choice(["teacher", "coach", "parent"])
    javelin_name = args.javelin or rng.choice(sorted(JAVELINS))
    clue1, clue2 = rng.sample(sorted(CLUES), 2)
    mischief = args.mischief or rng.choice(sorted(MISCHIEF))
    return StoryParams(
        setting=setting,
        finder=finder,
        finder_gender=finder_gender,
        sharer=sharer,
        sharer_gender=sharer_gender,
        adult=adult,
        javelin_name=javelin_name,
        javelin_color=JAVELINS[javelin_name].color,
        clue1=clue1,
        clue2=clue2,
        mischief=mischief,
    )


CURATED = [
    StoryParams("gym", "Mia", "girl", "Leo", "boy", "teacher", "blue", "chalk", "note", "hide", None),
    StoryParams("park", "Nora", "girl", "Finn", "boy", "coach", "green", "glove", "ribbon", "borrow", None),
    StoryParams("hall", "Max", "boy", "Ava", "girl", "parent", "red", "dust", "note", "practice", None),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, m, j) for t in THEMES for m in MISCHIEF for j in JAVELINS]


def outcome_of(params: StoryParams) -> str:
    return "revealed"


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    prog = asp_program("", "#show suspicious/0.\n#show shared_clues/0.\n#show reveal/0.")
    model = asp.one_model(prog)
    atoms = {sym.name for sym in model}
    if {"suspicious", "shared_clues", "reveal"} <= atoms:
        print("OK: ASP twin produces the expected atoms.")
    else:
        rc = 1
        print("MISMATCH: ASP twin did not produce the expected atoms.")
    samples = [generate(p) for p in CURATED]
    if all("javelin" in s.story for s in samples):
        print("OK: generated stories exercise the domain.")
    else:
        rc = 1
        print("MISMATCH: generated stories do not exercise the domain.")
    return rc


def asp_sanity() -> str:
    import storyworlds.asp as asp
    return asp_program("", "#show suspicious/0.\n#show shared_clues/0.\n#show reveal/0.")


def asp_list() -> list[str]:
    return [f"{t} {m} {j}" for t, m, j in valid_combos()]


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
        print(asp_sanity())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_list()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
            header = f"### {p.setting}: {p.finder} and {p.sharer}, {p.mischief} the javelin"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
