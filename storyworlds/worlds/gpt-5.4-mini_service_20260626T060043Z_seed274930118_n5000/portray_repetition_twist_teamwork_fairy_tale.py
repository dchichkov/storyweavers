#!/usr/bin/env python3
"""
A fairy-tale story world about a child who wants to portray someone special,
runs into a magical twist, and succeeds through teamwork.

The premise is deliberately small and state-driven:
- A young painter wants to portray a royal friend or creature.
- A repeated task fails because the subject keeps moving, hiding, or changing.
- A twist reveals the true way to make the picture.
- Teamwork turns frustration into a finished portrait.

The world model tracks physical meters and emotional memes, and the story text is
rendered from those evolving states rather than from a frozen template.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

@dataclass
class Actor:
    id: str
    kind: str = "character"
    type: str = "person"
    label: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["tired", "paint", "found", "completed", "blocked"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "joy", "pride", "teamwork"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "princess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "prince", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the moonlit castle"
    mood: str = "fairy tale"
    supports: set[str] = field(default_factory=set)


@dataclass
class Subject:
    id: str
    label: str
    type: str
    traits: list[str] = field(default_factory=list)
    moving: bool = False
    shy: bool = False
    magical: bool = False


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    helps: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    subject: str
    tool: str
    hero_name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Actor] = {}
        self.subjects: dict[str, Subject] = {}
        self.tools: dict[str, Tool] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add_actor(self, actor: Actor) -> Actor:
        self.entities[actor.id] = actor
        return actor

    def add_subject(self, subj: Subject) -> Subject:
        self.subjects[subj.id] = subj
        return subj

    def add_tool(self, tool: Tool) -> Tool:
        self.tools[tool.id] = tool
        return tool

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "castle": Setting(place="the moonlit castle", supports={"portray"}),
    "garden": Setting(place="the rose garden", supports={"portray"}),
    "tower": Setting(place="the glass tower", supports={"portray"}),
}

SUBJECTS = {
    "princess": Subject(
        id="princess",
        label="a princess with a silver ribbon",
        type="princess",
        traits=["gentle", "bright"],
        moving=False,
        shy=False,
        magical=False,
    ),
    "sprite": Subject(
        id="sprite",
        label="a tiny sprite with sparkling wings",
        type="sprite",
        traits=["quick", "magical"],
        moving=True,
        shy=True,
        magical=True,
    ),
    "unicorn": Subject(
        id="unicorn",
        label="a white unicorn with a gold horn",
        type="unicorn",
        traits=["noble", "swift"],
        moving=True,
        shy=False,
        magical=True,
    ),
}

TOOLS = {
    "charcoal": Tool(
        id="charcoal",
        label="a stick of charcoal",
        kind="dark",
        helps={"fast", "reveal"},
    ),
    "paintbrush": Tool(
        id="paintbrush",
        label="a small paintbrush",
        kind="color",
        helps={"patience", "detail"},
    ),
    "mirror": Tool(
        id="mirror",
        label="a silver mirror",
        kind="reflection",
        helps={"twist", "reveal"},
    ),
}

NAMES = ["Mira", "Nella", "Iris", "Lina", "Orin", "Finn", "Sera", "Tobin", "June", "Elia"]
HELPERS = ["the baker", "the gardener", "the mouse", "the lantern keeper", "the kind sister"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Actor, helper: Actor, subj: Subject, tool: Tool) -> None:
    world.say(
        f"Once upon a time, in {world.setting.place}, there lived {hero.id}, "
        f"a small artist who dreamed to portray {subj.label} with {tool.label}."
    )
    hero.memes["hope"] += 1
    hero.memes["joy"] += 0.5
    helper.memes["hope"] += 0.5
    world.say(
        f"{hero.id} loved fair things and gentle lines, and {hero.pronoun()} "
        f"said the picture would be the finest in the land."
    )


def attempt(world: World, hero: Actor, subj: Subject, tool: Tool, attempt_no: int) -> str:
    hero.meters["blocked"] += 1
    hero.meters["tired"] += 1
    hero.memes["worry"] += 1

    if subj.moving:
        return (
            f"Again {hero.id} tried to portray {subj.label}, but {subj.label} "
            f"fluttered away before the last line was drawn."
        )
    return (
        f"Again {hero.id} tried to portray {subj.label}, and this time the pose "
        f"held still long enough for the first smile to appear."
    )


def twist(world: World, hero: Actor, helper: Actor, subj: Subject, tool: Tool) -> None:
    hero.memes["worry"] += 1
    helper.memes["teamwork"] += 1

    if subj.shy:
        world.say(
            f"Then came a twist: the little subject was not trying to hide the portrait; "
            f"{subj.label} was shy and only came close when someone shared the work."
        )
    elif subj.moving:
        world.say(
            f"Then came a twist: the moving one did not want to spoil the picture at all; "
            f"{subj.label} had been guiding {hero.id} toward the right place all along."
        )
    else:
        world.say(
            f"Then came a twist: the picture was not meant to show only one face; "
            f"it was meant to show the whole kind little scene around it."
        )


def teamwork(world: World, hero: Actor, helper: Actor, subj: Subject, tool: Tool) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1

    if tool.kind == "reflection":
        world.say(
            f"So {hero.id} and {helper.id} used {tool.label} together. "
            f"{helper.id} held the mirror, and {hero.id} drew the reflected pose."
        )
    elif tool.kind == "color":
        world.say(
            f"So {hero.id} and {helper.id} worked side by side with {tool.label}. "
            f"One kept the page steady while the other added the soft colors."
        )
    else:
        world.say(
            f"So {hero.id} and {helper.id} worked together with {tool.label}, "
            f"one steadying the page and the other making the quick marks."
        )

    hero.meters["completed"] += 1
    world.say(
        f"At last the portrait was done, and {subj.label} smiled to see "
        f"the picture that had caught the fairy-tale light."
    )


def tell(setting: Setting, subj: Subject, tool: Tool, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add_actor(Actor(id=hero_name, type="artist", label="young artist"))
    helper = world.add_actor(Actor(id=helper_name, type="helper", label="kind helper"))
    subject = world.add_subject(subj)
    chosen_tool = world.add_tool(tool)

    introduce(world, hero, helper, subject, chosen_tool)

    world.para()
    for i in range(3):
        world.say(attempt(world, hero, subject, chosen_tool, i + 1))
        if i == 1:
            break

    world.para()
    twist(world, hero, helper, subject, chosen_tool)
    teamwork(world, hero, helper, subject, chosen_tool)

    world.facts.update(
        hero=hero,
        helper=helper,
        subject=subject,
        tool=chosen_tool,
        setting=setting,
        repeated_attempts=2,
        resolved=True,
        twist="teamwork",
    )
    return world


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def pick_name(rng: random.Random, gender: str = "any") -> str:
    return rng.choice(NAMES)


def hero_title(name: str) -> str:
    return name


def story_prefix(subject: Subject) -> str:
    if subject.id == "princess":
        return "princess"
    if subject.id == "sprite":
        return "sprite"
    return "unicorn"


def generate_story(world: World) -> str:
    return world.render()


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story about an artist who wants to portray {f["subject"].label}.',
        f"Tell a gentle story with repetition, a twist, and teamwork in {f['setting'].place}.",
        f'Write a short child-friendly tale where "{f["tool"].label}" helps a picture get finished.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    subj = f["subject"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with {tool.label}?",
            answer=f"{hero.id} wanted to portray {subj.label} with {tool.label}.",
        ),
        QAItem(
            question=f"Why did the same try fail again and again?",
            answer=(
                f"It failed because {subj.label} was moving or shy, so the picture "
                f"needed patience and a better plan."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} finish the picture?",
            answer=f"{helper.id} helped {hero.id}, and together they used teamwork to finish the portrait.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    subj = f["subject"]
    tool = f["tool"]
    qa = [
        QAItem(
            question="What does portray mean?",
            answer=(
                "To portray something means to show it in a picture, story, or painting "
                "so others can recognize it."
            ),
        ),
        QAItem(
            question="What is teamwork?",
            answer=(
                "Teamwork means people help each other and do a job together instead of alone."
            ),
        ),
    ]
    if subj.shy:
        qa.append(
            QAItem(
                question="What does it mean when someone is shy?",
                answer=(
                    "A shy person may hide a little, speak softly, or wait until they feel safe."
                ),
            )
        )
    if tool.kind == "reflection":
        qa.append(
            QAItem(
                question="What is a mirror for?",
                answer="A mirror shows an image by reflecting light so you can see what is in front of it.",
            )
        )
    return qa


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for a in world.entities.values():
        meters = {k: round(v, 2) for k, v in a.meters.items() if v}
        memes = {k: round(v, 2) for k, v in a.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {a.id}: {' '.join(bits) if bits else '(quiet)'}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
subject_moving(S) :- moving_subject(S).
subject_shy(S) :- shy_subject(S).

repetition_needed(H, S) :- hero(H), subject(S), subject_moving(S).
repetition_needed(H, S) :- hero(H), subject(S), subject_shy(S).

twist(H, S) :- hero(H), subject(S), subject_shy(S).
twist(H, S) :- hero(H), subject(S), subject_moving(S).

teamwork(H, K, S) :- hero(H), helper(K), subject(S), tool(T), helpful(T).
resolved(H, S) :- teamwork(H, _, S), twist(H, S).

valid_story(Setting, Subject, Tool) :-
    setting(Setting), subject(Subject), tool(Tool),
    supports(Setting, portray),
    helpful(Tool).
#show valid_story/3.
#show repetition_needed/2.
#show twist/2.
#show teamwork/3.
#show resolved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for cap in sorted(s.supports):
            lines.append(asp.fact("supports", sid, cap))
    for sid, s in SUBJECTS.items():
        lines.append(asp.fact("subject", sid))
        if s.moving:
            lines.append(asp.fact("moving_subject", sid))
        if s.shy:
            lines.append(asp.fact("shy_subject", sid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "reveal" in t.helps or "detail" in t.helps or "patience" in t.helps or "twist" in t.helps:
            lines.append(asp.fact("helpful", tid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    asp_set = set(asp_valid_stories())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP parity matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(asp_set - py_set))
    print(" only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        if "portray" not in setting.supports:
            continue
        for subj_id, subj in SUBJECTS.items():
            for tool_id, tool in TOOLS.items():
                if "reveal" not in tool.helps and "detail" not in tool.helps and "patience" not in tool.helps:
                    continue
                # The story needs a real twist/repetition setup.
                if not (subj.moving or subj.shy):
                    continue
                combos.append((s_id, subj_id, tool_id))
    return combos


def explain_rejection(setting: Setting, subject: Subject, tool: Tool) -> str:
    reasons = []
    if "portray" not in setting.supports:
        reasons.append("the setting does not support a portrait scene")
    if not (subject.moving or subject.shy):
        reasons.append("the subject would not create a repetition or twist")
    if not any(x in tool.helps for x in {"reveal", "detail", "patience", "twist"}):
        reasons.append("the tool would not help the story turn")
    return "(No story: " + "; ".join(reasons) + ".)"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world: portray, repetition, twist, teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--subject", choices=SUBJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.setting and args.subject and args.tool:
        setting = SETTINGS[args.setting]
        subject = SUBJECTS[args.subject]
        tool = TOOLS[args.tool]
        if (args.setting, args.subject, args.tool) not in combos:
            raise StoryError(explain_rejection(setting, subject, tool))

    filtered = [
        c for c in combos
        if (args.setting is None or c[0] == args.setting)
        and (args.subject is None or c[1] == args.subject)
        and (args.tool is None or c[2] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, subject_id, tool_id = rng.choice(sorted(filtered))
    return StoryParams(
        setting=setting_id,
        subject=subject_id,
        tool=tool_id,
        hero_name=args.name or rng.choice(NAMES),
        helper_name=args.helper or rng.choice(HELPERS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        SUBJECTS[params.subject],
        TOOLS[params.tool],
        params.hero_name,
        params.helper_name,
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for setting_id, subject_id, tool_id in valid_combos():
            params = StoryParams(
                setting=setting_id,
                subject=subject_id,
                tool=tool_id,
                hero_name="Mira",
                helper_name="the baker",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.subject} in {p.setting} using {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
