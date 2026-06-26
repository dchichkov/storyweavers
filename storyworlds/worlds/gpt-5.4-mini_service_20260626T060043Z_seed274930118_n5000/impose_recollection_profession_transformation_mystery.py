#!/usr/bin/env python3
"""
A small mystery storyworld about an imposed rule, a fading recollection, and a
profession that seems to transform during the story.

The central premise:
- Someone in a small place has a profession that is important to the town.
- A rule is imposed, making the character hide or pause that profession.
- The hero has a recollection that helps them notice a strange transformation.
- The mystery resolves when the truth about the profession is uncovered.

This world is intentionally compact and classical: one setting, one mystery,
one turn, one reveal.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Setting:
    place: str
    indoors: bool = False
    detail: str = ""


@dataclass
class Profession:
    label: str
    tools: list[str]
    public_sign: str
    hidden_sign: str
    transformation_hint: str


@dataclass
class World:
    setting: Setting
    hero_name: str = ""
    hero_role: str = "child"
    profession_name: str = ""
    imposed_rule: str = ""
    recollection: str = ""
    mystery_clue: str = ""
    true_change: str = ""
    reveal: str = ""
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "harbor": Setting(place="the harbor", indoors=False, detail="The harbor smelled like salt and rope."),
    "library": Setting(place="the library", indoors=True, detail="The library was quiet, with high shelves and soft lamps."),
    "market": Setting(place="the market", indoors=False, detail="The market was busy with carts, baskets, and whispers."),
    "station": Setting(place="the station", indoors=True, detail="The station had a clock that ticked like a secret."),
}

PROFESSIONS = {
    "baker": Profession(
        label="baker",
        tools=["flour", "a wooden spoon", "a round tray"],
        public_sign="a warm smell of bread",
        hidden_sign="a dusting of flour on the cuffs",
        transformation_hint="the apron looked strangely changed, as if it had been turned inside out",
    ),
    "watchmaker": Profession(
        label="watchmaker",
        tools=["tiny screws", "a brass lens", "a ticking watch"],
        public_sign="a careful hand",
        hidden_sign="a pocket full of gears",
        transformation_hint="the watch seemed to tick backward for one second",
    ),
    "gardener": Profession(
        label="gardener",
        tools=["a tin can of seeds", "gloves", "a small trowel"],
        public_sign="fresh leaves",
        hidden_sign="mud on the hem",
        transformation_hint="the boots were suddenly covered in dew, though the floor was dry",
    ),
    "carter": Profession(
        label="carter",
        tools=["rope", "lantern", "wagon keys"],
        public_sign="a creak of wheels",
        hidden_sign="a key ring that never stayed still",
        transformation_hint="the lantern light seemed to shift into a different shape",
    ),
}

IMPOSED_RULES = [
    "keep the door shut until dusk",
    "wear the plain coat and say nothing about the work",
    "leave the tools in the drawer for one day",
    "hide the sign and wait for the bell",
]

RECOLLECTIONS = [
    "a remembered smell of warm bread from an earlier morning",
    "a recollection of hearing tiny gears click behind a wall",
    "a recollection of muddy footprints near the greenhouse",
    "a recollection of a lantern that glowed blue before the storm",
]

NAMES = ["Mina", "Eli", "June", "Noah", "Lina", "Arlo", "Tess", "Theo"]


@dataclass
class StoryParams:
    place: str
    profession: str
    name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about an imposed rule and a revealing recollection.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--profession", choices=PROFESSIONS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    profession = args.profession or rng.choice(list(PROFESSIONS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(place=place, profession=profession, name=name)


def choose_rule(rng: random.Random) -> str:
    return rng.choice(IMPOSED_RULES)


def choose_recollection(rng: random.Random) -> str:
    return rng.choice(RECOLLECTIONS)


def generate_world(params: StoryParams) -> World:
    rng = random.Random(params.seed if params.seed is not None else 0)
    setting = SETTINGS[params.place]
    prof = PROFESSIONS[params.profession]
    w = World(setting=setting, hero_name=params.name, profession_name=prof.label)
    imposed_rule = choose_rule(rng)
    recollection = choose_recollection(rng)

    w.imposed_rule = imposed_rule
    w.recollection = recollection
    w.mystery_clue = prof.transformation_hint
    w.true_change = (
        f"The {prof.label}'s work had not vanished at all; it had only transformed from a public job into a hidden one."
    )
    w.reveal = (
        f"The mystery was solved when {params.name} matched the recollection to the clue and realized the {prof.label} was still doing the same careful work."
    )

    # Setup
    w.say(f"{params.name} lived near {setting.place}.")
    w.say(f"In that place, a {prof.label} was known for {prof.public_sign}.")
    w.say(f"Everyone also knew the {prof.label} by {prof.hidden_sign}.")
    w.para()

    # Mystery / tension
    w.say(f"One day, an unusual rule was imposed: {imposed_rule}.")
    w.say(f"After that, the {prof.label} looked changed, and the town began to whisper.")
    w.say(f"{params.name} noticed one strange clue: {prof.transformation_hint}.")
    w.say(f"That night, {params.name} had {recollection}.")
    w.para()

    # Turn / reveal
    w.say(f"The recollection fit the clue like a key in a lock.")
    w.say(w.true_change)
    w.say(
        f"{params.name} realized the {prof.label} had not become someone else; the profession had only transformed in the way it was shown."
    )
    w.say(
        f"By morning, the rule was lifted, the tools came back out, and the town could see the honest work again."
    )

    w.facts.update(
        setting=setting,
        profession=prof,
        imposed_rule=imposed_rule,
        recollection=recollection,
        clue=prof.transformation_hint,
        name=params.name,
    )
    return w


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
    prof = world.facts["profession"]
    return [
        f"Write a short mystery story for children about an imposed rule and a {prof.label} whose work changes in a surprising way.",
        f"Tell a gentle story where a child remembers something important and solves a mystery about a {prof.label}.",
        f"Write a story with the words impose, recollection, and profession, ending with a reveal that explains the strange change.",
    ]


def story_qa(world: World) -> list[QAItem]:
    prof = world.facts["profession"]
    name = world.facts["name"]
    rule = world.facts["imposed_rule"]
    recollection = world.facts["recollection"]
    return [
        QAItem(
            question=f"What profession was important in the story?",
            answer=f"The important profession was the {prof.label}'s work.",
        ),
        QAItem(
            question=f"What was imposed on the town?",
            answer=f"An unusual rule was imposed: {rule}.",
        ),
        QAItem(
            question=f"What did {name} remember that helped with the mystery?",
            answer=f"{name} had {recollection}, and that recollection helped match the clue.",
        ),
        QAItem(
            question="What was the strange clue?",
            answer=f"The clue was that {prof.transformation_hint}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The mystery was solved, the work was understood again, and the profession was seen clearly instead of being hidden.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    prof = world.facts["profession"]
    return [
        QAItem(
            question="What is a profession?",
            answer="A profession is a kind of work a person does to help others or earn a living.",
        ),
        QAItem(
            question="What is a recollection?",
            answer="A recollection is a remembered thought or memory from before.",
        ),
        QAItem(
            question="What does impose mean?",
            answer="To impose something is to place a rule or requirement on someone or a place.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change in form, look, or state.",
        ),
        QAItem(
            question=f"What tool might a {prof.label} use?",
            answer=f"A {prof.label} might use {', '.join(prof.tools[:-1])}, and {prof.tools[-1]}.",
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
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    prof = world.facts.get("profession")
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    lines.append(f"hero_name: {world.hero_name}")
    if prof:
        lines.append(f"profession: {prof.label}")
    lines.append(f"imposed_rule: {world.imposed_rule}")
    lines.append(f"recollection: {world.recollection}")
    lines.append(f"clue: {world.mystery_clue}")
    lines.append(f"reveal: {world.reveal}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", profession="watchmaker", name="Mina"),
    StoryParams(place="harbor", profession="carter", name="Eli"),
    StoryParams(place="market", profession="baker", name="June"),
    StoryParams(place="station", profession="gardener", name="Theo"),
]


ASP_RULES = r"""
% The declarative twin checks that a valid mystery needs:
% - a setting
% - a profession
% - an imposed rule
% - a recollection
% - a transformation clue
valid_story(S, P) :- setting(S), profession(P), imposed_rule(_), recollection(_), transformation_clue(_).

% A story is especially mystery-shaped if the clue mentions change.
mystery_story(S, P) :- valid_story(S, P), transformation_clue(C), clue_mentions_change(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for pid, p in PROFESSIONS.items():
        lines.append(asp.fact("profession", pid))
        for t in p.tools:
            lines.append(asp.fact("tool", pid, t))
        lines.append(asp.fact("public_sign", pid, p.public_sign))
        lines.append(asp.fact("hidden_sign", pid, p.hidden_sign))
        lines.append(asp.fact("transformation_clue", pid, p.transformation_hint))
        lines.append(asp.fact("clue_mentions_change", pid))
    for rule in IMPOSED_RULES:
        lines.append(asp.fact("imposed_rule", rule))
    for rec in RECOLLECTIONS:
        lines.append(asp.fact("recollection", rec))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    expected = {(s, p) for s in SETTINGS for p in PROFESSIONS}
    if atoms == expected:
        print(f"OK: clingo gate matches expected valid_story set ({len(atoms)} pairs).")
        return 0
    print("MISMATCH between clingo and Python expectation:")
    print("only in clingo:", sorted(atoms - expected))
    print("only in python:", sorted(expected - atoms))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-sized mystery storyworld about impose, recollection, profession, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--profession", choices=PROFESSIONS)
    ap.add_argument("--name")
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        pairs = sorted(set(asp.atoms(model, "valid_story")))
        for s, p in pairs:
            print(f"{s}: {p}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} at {p.place} ({p.profession})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
