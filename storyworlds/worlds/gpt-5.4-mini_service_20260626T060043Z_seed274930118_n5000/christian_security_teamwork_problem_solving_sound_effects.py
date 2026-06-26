#!/usr/bin/env python3
"""
Standalone storyworld: Christian, security, teamwork, problem solving, and sound effects.

A small fairy-tale domain where a kind child named Christian helps a security team
quiet a noisy gate and keep the lantern hall safe for a feast night.
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


@dataclass
class Thing:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.id.lower() == "christian":
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
            if self.id.lower() in {"mira", "lina", "rose"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    echo: str
    safe_word: str
    sound_sensitive: bool = True


@dataclass
class StoryParams:
    place: str
    noise: str
    tool: str
    helper: str
    seed: Optional[int] = None


PLACES = {
    "lantern_hall": Place("the lantern hall", "a soft echo", "safe"),
    "rose_gate": Place("the rose gate", "a hollow creak", "quiet"),
    "courtyard": Place("the courtyard", "a bright ring", "calm"),
}

NOISES = {
    "squeak": {
        "label": "squeak",
        "noun": "a squeaky gate",
        "verb": "squeak and shriek",
        "effect": "squeaking",
        "sound": "squeeeak-squeeeak",
        "problem": "the sound might wake the sleeping birds",
        "fix": "oiled the hinges",
    },
    "clatter": {
        "label": "clatter",
        "noun": "a clattering latch",
        "verb": "clatter and rattle",
        "effect": "clattering",
        "sound": "clack-clack-clink",
        "problem": "the sound might startle the little lanterns",
        "fix": "tied the latch with a ribbon",
    },
    "whistle": {
        "label": "whistle",
        "noun": "a whistling window",
        "verb": "whistle and sing",
        "effect": "whistling",
        "sound": "fiuuu-fiuuu",
        "problem": "the sound might carry across the courtyard",
        "fix": "sealed the crack with wax",
    },
}

TOOLS = {
    "oil": {"label": "a tiny bottle of oil", "kind": "tool", "use": "drip oil onto the hinges"},
    "ribbon": {"label": "a red ribbon", "kind": "tool", "use": "tie the latch gently"},
    "wax": {"label": "a little lump of wax", "kind": "tool", "use": "press wax into the crack"},
}

HELPERS = [
    ("mira", "a brave castle helper"),
    ("lina", "a lantern keeper"),
    ("owen", "a watchful gate helper"),
]


@dataclass
class World:
    place: Place
    noise: dict
    tool: dict
    helper: Thing
    christian: Thing
    gate: Thing
    plan: list[str] = field(default_factory=list)
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return "\n\n".join(self.plan)


def _say(world: World, text: str) -> None:
    world.plan.append(text)


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    noise = NOISES[params.noise]
    tool = TOOLS[params.tool]
    christian = Thing(id="Christian", kind="character", label="Christian", phrase="a kind child")
    helper_id, helper_phrase = params.helper, dict(HELPERS)[params.helper]
    helper = Thing(id=helper_id, kind="character", label=helper_id.capitalize(), phrase=helper_phrase)
    gate = Thing(id="gate", kind="thing", label="gate", phrase=noise["noun"])
    return World(place=place, noise=noise, tool=tool, helper=helper, christian=christian, gate=gate)


def narrate(world: World) -> None:
    christian = world.christian
    helper = world.helper
    place = world.place
    noise = world.noise
    tool = world.tool

    _say(world, f"Once upon a time, in {place.name}, there lived a kind child named Christian.")
    _say(world, f"{christian.pronoun().capitalize()} loved listening to bells, birds, and the gentle hush of the halls.")
    _say(world, f"One evening, {world.gate.label} began to {noise['verb']}. It went, '{noise['sound']}'")
    _say(world, f"The old noise was so loud that {noise['problem']}.")

    _say(world, f"Christian hurried to {helper.label}, and together they made a small plan.")
    _say(world, f"{helper.label} said, 'We can solve this if we work as a team.'")
    _say(world, f"Christian nodded and brought {tool['label']}.")
    _say(world, f"First, {helper.label.lower()} held the gate still, and then Christian used {tool['use']}.")
    _say(world, f"The helper listened carefully, because good problem solving needs patient ears and steady hands.")

    _say(world, f"At last, the gate gave one last tiny '{place.echo}', and then it became quiet.")
    _say(world, f"The lanterns stayed bright, the birds slept on, and Christian smiled at the peaceful hall.")
    _say(world, f"From that night on, everyone remembered how teamwork can turn a noisy trouble into a safe and happy ending.")

    world.facts.update(
        christian=christian,
        helper=helper,
        place=place,
        noise=noise,
        tool=tool,
        gate=world.gate,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a fairy-tale story about Christian helping a security team solve a noisy {world.noise['label']} problem.",
        f"Tell a child-friendly story where teamwork and problem solving keep {world.place.name} safe and quiet.",
        f"Write a short story with sound effects, a helper, and a happy ending at {world.place.name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["christian"]
    h = f["helper"]
    p = f["place"]
    n = f["noise"]
    t = f["tool"]
    return [
        QAItem(
            question=f"Who helped solve the noisy problem in {p.name}?",
            answer=f"Christian helped {h.label.lower()} solve it with teamwork and careful problem solving.",
        ),
        QAItem(
            question=f"What sound did the problem make before it was fixed?",
            answer=f"It went '{n['sound']}' before Christian and {h.label.lower()} quieted it.",
        ),
        QAItem(
            question=f"What did Christian bring to fix the trouble?",
            answer=f"Christian brought {t['label']} and used it to help make the place quiet again.",
        ),
        QAItem(
            question=f"How did Christian feel at the end?",
            answer=f"{c.label} felt happy and proud because the plan worked and {p.name} became peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people work together and help each other do something well.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means looking carefully at a trouble and finding a good way to fix it.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are little words that help a story sound real, like squeak, clink, or whoosh.",
        ),
        QAItem(
            question="What does a security helper do?",
            answer="A security helper watches over a place and helps keep it safe and calm.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return "\n".join(
        [
            "--- world model state ---",
            f"place={world.place.name}",
            f"noise={world.noise['label']}",
            f"tool={world.tool['label']}",
            f"helper={world.helper.label}",
            f"christian={world.christian.label}",
            f"solved={world.facts.get('solved', False)}",
        ]
    )


CURATED = [
    StoryParams(place="lantern_hall", noise="squeak", tool="oil", helper="mira"),
    StoryParams(place="rose_gate", noise="clatter", tool="ribbon", helper="lina"),
    StoryParams(place="courtyard", noise="whistle", tool="wax", helper="owen"),
]


def explain_invalid(params: StoryParams) -> str:
    return "This tale needs a place, a sound problem, and a matching tool that can fix it."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about Christian, security, teamwork, and sound effects.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--helper", choices=sorted(dict(HELPERS)))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(PLACES))
    noise = args.noise or rng.choice(sorted(NOISES))
    tool = args.tool or {"squeak": "oil", "clatter": "ribbon", "whistle": "wax"}[noise]
    helper = args.helper or rng.choice(sorted(dict(HELPERS)))
    if noise == "squeak" and tool != "oil":
        raise StoryError(explain_invalid(StoryParams(place, noise, tool, helper)))
    if noise == "clatter" and tool != "ribbon":
        raise StoryError(explain_invalid(StoryParams(place, noise, tool, helper)))
    if noise == "whistle" and tool != "wax":
        raise StoryError(explain_invalid(StoryParams(place, noise, tool, helper)))
    return StoryParams(place=place, noise=noise, tool=tool, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
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


ASP_RULES = r"""
place(lantern_hall). place(rose_gate). place(courtyard).
noise(squeak). noise(clatter). noise(whistle).
tool(oil). tool(ribbon). tool(wax).

matches(squeak,oil).
matches(clatter,ribbon).
matches(whistle,wax).

valid(P,N,T) :- place(P), noise(N), tool(T), matches(N,T).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for n in NOISES:
        lines.append(asp.fact("noise", n))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    lines.append(asp.fact("matches", "squeak", "oil"))
    lines.append(asp.fact("matches", "clatter", "ribbon"))
    lines.append(asp.fact("matches", "whistle", "wax"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = {
        (p, n, {"squeak": "oil", "clatter": "ribbon", "whistle": "wax"}[n])
        for p in PLACES for n in NOISES
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place-noise-tool combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
