#!/usr/bin/env python3
"""
storyworlds/worlds/woolen_malleable_mystery_to_solve_happy_ending.py
====================================================================

A small detective-style storyworld about a child detective solving a cozy
mystery with a happy ending.

Premise:
- A beloved woolen item goes missing or becomes unusable.
- The mystery is solved by noticing a malleable material that can be shaped.
- The ending is warm, concrete, and child-friendly.

The world stays small on purpose: one detective, one helper, one missing object,
a few clues, and a tidy resolution.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = True
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing: str
    clue_word: str
    culprit: str
    reveal: str
    solution_action: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    useful_for: set[str]
    tags: set[str] = field(default_factory=set)


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


def _norm(s: str) -> str:
    return s.strip().lower()


def choose_article(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


# Content registries
SETTINGS = {
    "study": Setting(place="the study", indoors=True, afford={"investigate"}),
    "workshop": Setting(place="the workshop", indoors=True, afford={"investigate"}),
    "bedroom": Setting(place="the bedroom", indoors=True, afford={"investigate"}),
    "attic": Setting(place="the attic", indoors=True, afford={"investigate"}),
}

MYSTERIES = {
    "hat": Mystery(
        id="hat",
        missing="woolen hat",
        clue_word="wool",
        culprit="mice",
        reveal="The mice had only used it to make a soft nest, and they left it clean.",
        solution_action="carefully lift the basket and let the mice scamper away",
        end_image="the woolen hat, fluffed up and warm, sat right back on the shelf",
        tags={"woolen", "cozy", "small"},
    ),
    "scarf": Mystery(
        id="scarf",
        missing="woolen scarf",
        clue_word="thread",
        culprit="wind",
        reveal="A gust had blown it behind a chest, where it waited like a shy ribbon.",
        solution_action="pull the chest aside and follow the breezy clue",
        end_image="the woolen scarf was wrapped neatly around the detective's neck",
        tags={"woolen", "wind", "cozy"},
    ),
    "sweater": Mystery(
        id="sweater",
        missing="woolen sweater",
        clue_word="button",
        culprit="a puppy",
        reveal="The puppy had tugged it into a basket, then curled up beside it.",
        solution_action="check the basket and calm the sleepy puppy",
        end_image="the woolen sweater was folded softly on the chair",
        tags={"woolen", "pet", "cozy"},
    ),
    "mittens": Mystery(
        id="mittens",
        missing="woolen mittens",
        clue_word="crumb",
        culprit="the lunch table",
        reveal="The mittens had been left under a plate, where they stayed safe and snug.",
        solution_action="look under the plate and smile at the obvious clue",
        end_image="the woolen mittens were back by the door, ready for cold hands",
        tags={"woolen", "winter", "cozy"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a little magnifying glass",
        useful_for={"thread", "button", "crumb", "wool"},
        tags={"detective"},
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a small notebook",
        useful_for={"thread", "button", "crumb", "wool"},
        tags={"detective"},
    ),
    "clamp": Tool(
        id="clamp",
        label="malleable clamp",
        phrase="a malleable clamp made of bendy metal",
        useful_for={"button", "crumb", "wool"},
        tags={"malleable"},
    ),
    "putty": Tool(
        id="putty",
        label="putty",
        phrase="a soft malleable putty",
        useful_for={"thread", "crumb"},
        tags={"malleable"},
    ),
}

HERO_NAMES = ["Mira", "Toby", "Nina", "Leo", "Eli", "Ava"]
HELPER_NAMES = ["Ms. Finch", "Mr. Hale", "Aunt June", "Grandpa Ben"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    tool: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id, m in MYSTERIES.items():
            for tool_id, t in TOOLS.items():
                if m.clue_word in t.useful_for:
                    out.append((setting_id, mystery_id, tool_id))
    return out


def explain_rejection(mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: the clue in this mystery is about {mystery.clue_word}, "
        f"but {tool.label} would not help solve it in a believable way. "
        f"Pick a tool that can plausibly follow that clue.)"
    )


def story_intro(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a little detective with sharp eyes and a calm notebook."
    )
    world.say(
        f"{hero.pronoun().capitalize()} and {helper.id} were already thinking about "
        f"{mystery.missing} and the tiny clue about {mystery.clue_word}."
    )
    world.say(
        f"On the table sat {choose_article(tool.phrase)} {tool.phrase}, ready for the case."
    )


def build_case(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0) + 1
    helper.memes["calm"] = helper.memes.get("calm", 0) + 1
    world.say(
        f"They went into {world.setting.place} to investigate."
    )
    world.say(
        f"{hero.id} looked under a chair, beside a trunk, and near the window."
    )
    world.say(
        f"{hero.pronoun().capitalize()} noticed {mystery.clue_word} marks where something soft had brushed by."
    )
    world.say(
        f"{helper.id} said, \"Good eyes. Let's use the {tool.label} and think about the clue.\""
    )


def solve_case(world: World, hero: Entity, helper: Entity, mystery: Mystery, tool: Tool) -> None:
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    world.say(
        f"{hero.id} followed the clue to a hidden spot."
    )
    if "malleable" in tool.tags:
        world.say(
            f"The {tool.label} was malleable, so it bent just enough to slip into the tight place."
        )
    world.say(
        f"Then they found the answer: {mystery.reveal}"
    )
    world.say(
        f"{hero.id} used the {tool.label} to {mystery.solution_action}."
    )
    world.say(
        f"At last, the mystery was solved, and everyone could smile."
    )
    world.say(
        f"In the end, {mystery.end_image}."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str, hero_type: str,
         helper_name: str, helper_type: str, tool: Tool) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.clue_word))
    prize = world.add(Entity(id="missing", type="object", label=mystery.missing))
    world.facts.update(hero=hero, helper=helper, clue=clue, prize=prize, mystery=mystery, tool=tool)
    story_intro(world, hero, helper, mystery, tool)
    world.para()
    build_case(world, hero, helper, mystery, tool)
    world.para()
    solve_case(world, hero, helper, mystery, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m: Mystery = f["mystery"]
    t: Tool = f["tool"]
    return [
        f'Write a short detective story for a child that includes the words "{m.missing}" and "{t.label}".',
        f"Tell a cozy mystery where a child detective uses {t.phrase} to solve a case about {m.missing}.",
        f"Write a gentle story with a clue about {m.clue_word}, a malleable tool, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    mystery: Mystery = f["mystery"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who was the detective in the story?",
            answer=f"{hero.id} was the little detective who looked for {mystery.missing}.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"The clue about {mystery.clue_word} helped them find {mystery.missing}.",
        ),
        QAItem(
            question=f"What tool did they use to help with the case?",
            answer=f"They used {tool.phrase} to help solve the mystery.",
        ),
        QAItem(
            question=f"Who helped {hero.id} during the search?",
            answer=f"{helper.id} helped by staying calm and pointing out the clue.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"The mystery was solved and the story ended happily with {mystery.end_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tool: Tool = f["tool"]
    mystery: Mystery = f["mystery"]
    out: list[QAItem] = [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and uses them to solve a problem.",
        ),
        QAItem(
            question="What does malleable mean?",
            answer="Malleable means something can be bent or shaped without breaking right away.",
        ),
    ]
    if "woolen" in mystery.tags:
        out.append(
            QAItem(
                question="What is woolen clothing like?",
                answer="Woolen clothing is soft and warm, so people often wear it in chilly weather.",
            )
        )
    if "malleable" in tool.tags:
        out.append(
            QAItem(
                question="Why can a malleable tool be useful?",
                answer="A malleable tool can bend a little and fit into a tight place while someone works.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when the clue word is something the tool can help with.
valid_combo(S, M, T) :- setting(S), mystery(M), tool(T),
                        clue_word(M, C), useful_for(T, C).

% Malleable tools are special helpers in the detective story.
malleable_tool(T) :- tool(T), tags(T, malleable).

% The story is especially strong when the mystery is woolen and the tool is malleable.
good_story(S, M, T) :- valid_combo(S, M, T),
                       mystery_tag(M, woolen),
                       malleable_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue_word", mid, m.clue_word))
        lines.append(asp.fact("culprit", mid, m.culprit))
        for tag in sorted(m.tags):
            lines.append(asp.fact("mystery_tag", mid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("label", tid, t.label))
        for u in sorted(t.useful_for):
            lines.append(asp.fact("useful_for", tid, u))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tags", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy detective storyworld with a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle", "woman", "man"])
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
    if args.mystery and args.tool:
        m = MYSTERIES[args.mystery]
        t = TOOLS[args.tool]
        if m.clue_word not in t.useful_for:
            raise StoryError(explain_rejection(m, t))
    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, mystery_id, tool_id = rng.choice(sorted(filtered))
    mystery = MYSTERIES[mystery_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle", "woman", "man"])
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        tool=tool_id,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
        TOOLS[params.tool],
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
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:")
        for s, m, t in combos:
            print(f"  {s:10} {m:10} {t:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for setting_id, mystery_id, tool_id in valid_combos():
            p = StoryParams(
                setting=setting_id,
                mystery=mystery_id,
                hero_name=HERO_NAMES[0],
                hero_type="girl",
                helper_name=HELPER_NAMES[0],
                helper_type="woman",
                tool=tool_id,
                seed=base_seed,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
