#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/scissor_happy_ending_kindness_dialogue_nursery_rhyme.py
========================================================================================

A small, self-contained storyworld for a nursery-rhyme-style tale about a child,
a pair of scissors, a little problem, kind dialogue, and a happy ending.

The tiny domain:
- A child wants to use a scissor on a craft.
- A sibling or friend worries that the scissors may snag something valuable.
- The characters talk kindly and choose a safer, helpful use.
- The scissor is used carefully to fix the craft, and the ending is bright and warm.

The story is built from simulated state:
- physical meters: snipped, tangled, fixed, neat, torn
- emotional memes: joy, worry, trust, kindness, relief
- the plot turns when state changes, not from a frozen paragraph swap.

This script supports:
    --verify, --asp, --show-asp, --all, -n, --seed, --trace, --qa, --json
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
KINDNESS_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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


@dataclass
class Setting:
    id: str
    place: str
    scene: str
    weather: str
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    use: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    phrase: str
    risk: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["torn"] < THRESHOLD or e.meters["fixed"] >= THRESHOLD:
            continue
        sig = ("repair", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["fixed"] += 1
        e.meters["neat"] += 1
        out.append("__repair__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    if any(e.meters["fixed"] >= THRESHOLD for e in world.entities.values()):
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("repair", "physical", _r_repair), Rule("relief", "social", _r_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def is_reasonable(problem: Problem, item: Item) -> bool:
    return problem.id in {"kite", "banner", "paper_chain"} and item.id == "scissor"


def choose_response() -> Response:
    return RESPONSES["careful_cut"]


def predict_fix(world: World, problem_id: str) -> dict:
    sim = world.copy()
    _apply_problem(sim, sim.get(problem_id), narrate=False)
    return {
        "torn": sim.get(problem_id).meters["torn"] >= THRESHOLD,
        "fixed": sim.get(problem_id).meters["fixed"] >= THRESHOLD,
    }


def _apply_problem(world: World, problem: Entity, narrate: bool = True) -> None:
    problem.meters["torn"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, helper: Entity, setting: Setting, item: Item, problem: Problem) -> None:
    child.memes["joy"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In {setting.place}, under {setting.scene}, {child.id} hummed a little tune. "
        f"{setting.line}"
    )
    world.say(
        f'{child.id} held {item.phrase} and smiled. "{item.use}, and then it will fly," '
        f'{child.pronoun()} said.'
    )
    world.say(
        f'{helper.id} looked up kindly. "{problem.label} is near," {helper.pronoun()} said, '
        f'"so let us be gentle."'
    )


def risk(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    helper.memes["kindness"] += 1
    pred = predict_fix(world, problem.id)
    world.facts["predicted_torn"] = pred["torn"]
    world.say(
        f'"If the {problem.label} gets caught, it may tear," {helper.id} said. '
        f'"Let us make a careful cut, not a fast one."'
    )
    if pred["torn"]:
        world.say(
            f"{child.id} paused and listened. The warning was small, but it was true."
        )


def choose(world: World, child: Entity, helper: Entity, item: Item, response: Response) -> None:
    child.memes["trust"] += 1
    child.memes["kindness"] += 1
    world.say(
        f'"You are right," {child.id} said. "Will you show me?" '
        f'"Yes," {helper.id} said, "hand me the {item.label} and we will do it together."'
    )
    world.say(
        f'{helper.id} held the paper steady while {child.id} took a slow breath.'
    )
    world.say(
        f"{item.label.capitalize()} {response.text}."
    )


def finish(world: World, child: Entity, helper: Entity, setting: Setting, item: Item, problem: Problem) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The {problem.label} was no longer torn. It curled bright and neat in the breeze."
    )
    world.say(
        f'{helper.id} laughed softly. "{problem.fix}," {helper.id} said, '
        f'and {child.id} grinned from ear to ear.'
    )
    world.say(
        f"They hung the finished craft by the window, where it danced in the light like a tiny song."
    )


def tell(setting: Setting, item: Item, problem: Problem, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Nico", helper_gender: str = "boy",
         helper_role: str = "friend") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role=helper_role))
    scissor = world.add(Entity(id="scissor", type="tool", label="scissor"))
    target = world.add(Entity(id=problem.id, type="thing", label=problem.label))
    world.facts.update(setting=setting, item=item, problem=problem, response=response, child=child, helper=helper, scissor=scissor, target=target)

    intro(world, child, helper, setting, item, problem)
    world.para()
    risk(world, child, helper, problem)
    choose(world, child, helper, item, response)
    _apply_problem(world, target)
    world.para()
    finish(world, child, helper, setting, item, problem)

    world.facts["outcome"] = "happy"
    return world


SETTINGS = {
    "window": Setting(
        id="window",
        place="the sunny window",
        scene="a quilt of clouds and blue sky",
        weather="breezy",
        line="A ribbon of morning light lay on the sill like a gold thread.",
        tags={"window", "sunny"},
    ),
    "garden": Setting(
        id="garden",
        place="the garden table",
        scene="a row of daisies and a sleepy bee",
        weather="soft",
        line="The birds were singing, and the chair legs tapped like a drum.",
        tags={"garden"},
    ),
    "porch": Setting(
        id="porch",
        place="the porch",
        scene="a little map of shadows and sunspots",
        weather="warm",
        line="A warm wind danced by the steps and twirled the leaves around.",
        tags={"porch"},
    ),
}

ITEMS = {
    "scissor": Item("scissor", "scissor", "the scissor", "snip the ribbon into a star", tags={"scissor"}),
    "string": Item("string", "string", "the string", "tie the kite tail", tags={"string"}),
}

PROBLEMS = {
    "kite": Problem(
        "kite",
        "the kite tail",
        "the kite tail",
        risk="tangle",
        fix="careful cuts make happy crafts",
        tags={"kite", "string"},
    ),
    "banner": Problem(
        "banner",
        "the paper banner",
        "the paper banner",
        risk="tear",
        fix="kind hands make neat shapes",
        tags={"banner", "paper"},
    ),
    "paper_chain": Problem(
        "paper_chain",
        "the paper chain",
        "the paper chain",
        risk="snag",
        fix="slow snips keep the links tidy",
        tags={"paper_chain", "paper"},
    ),
}

RESPONSES = {
    "careful_cut": Response(
        "careful_cut",
        sense=3,
        power=3,
        text="snipped one ribbon at a time until the loose edge was neat and even",
        fail="snipped too fast and made a bigger tangle",
        qa_text="snipped one ribbon at a time until the loose edge was neat and even",
        tags={"careful", "scissor"},
    ),
    "slow_trim": Response(
        "slow_trim",
        sense=2,
        power=2,
        text="trimmed the frayed edge slowly and set every piece aside in a tidy pile",
        fail="trimmed the wrong place and left the craft crooked",
        qa_text="trimmed the frayed edge slowly and set every piece aside in a tidy pile",
        tags={"slow", "scissor"},
    ),
}

SETUP_NAMES = ["Mina", "Lina", "Toby", "Noah", "Pia", "Ari"]
HELPER_NAMES = ["Nico", "Ruby", "Eli", "June", "Owen", "Nora"]
TRAITS = ["gentle", "bright", "cheerful", "patient", "kind"]

CURATED = [
    StoryParams("window", "scissor", "kite", "Mina", "girl", "Nico", "boy", "friend"),
    StoryParams("garden", "scissor", "banner", "Toby", "boy", "Ruby", "girl", "friend"),
    StoryParams("porch", "scissor", "paper_chain", "Pia", "girl", "Owen", "boy", "sibling"),
]


@dataclass
class StoryParams:
    setting: str
    item: str
    problem: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    helper_role: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for iid in ITEMS:
            for pid in PROBLEMS:
                if is_reasonable(ITEMS[iid], ITEMS["scissor"]) and iid == "scissor":
                    combos.append((sid, iid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about scissors, kindness, and a happy fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--helper-role", choices=["friend", "sibling"])
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
    if args.item and args.item != "scissor":
        raise StoryError("This tiny storyworld only supports the scissor as the craft tool.")
    setting = args.setting or rng.choice(list(SETTINGS))
    item = "scissor"
    problem = args.problem or rng.choice(list(PROBLEMS))
    child = args.child or rng.choice(SETUP_NAMES)
    helper = args.helper or rng.choice([n for n in HELPER_NAMES if n != child])
    helper_gender = "girl" if helper in {"Ruby", "June", "Nora"} else "boy"
    child_gender = "girl" if child in {"Mina", "Lina", "Pia"} else "boy"
    helper_role = args.helper_role or rng.choice(["friend", "sibling"])
    if not is_reasonable(ITEMS[item], ITEMS["scissor"]):
        raise StoryError("No valid scissor story could be built from the choices.")
    return StoryParams(setting, item, problem, child, child_gender, helper, helper_gender, helper_role)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story that includes the word "scissor" and ends happily.',
        f"Tell a kind dialogue story where {f['child'].id} uses a scissor carefully while a helpful {f['helper'].role} speaks gently.",
        f"Write a short story for a young child about a craft that gets better because someone is kind and patient.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    problem = f["problem"]
    resp = f["response"]
    qa = [
        ("Who is the story about?", f"It is about {child.id} and {helper.id}, who work together on a small craft."),
        ("What did they use?", "They used a scissor carefully to fix the craft and make it neat."),
        ("How did the helper speak?", "The helper spoke kindly, with calm words that helped the child slow down and listen."),
        ("What happened at the end?", f"The {problem.label} was fixed, and the craft hung bright and tidy by the window."),
    ]
    return qa


KNOWLEDGE = {
    "scissor": [("What is a scissor?", "A scissor is a tool with two sharp blades that can cut paper, ribbon, and string. It should be used carefully with a grown-up nearby.")],
    "kindness": [("What is kindness?", "Kindness means using gentle words and helpful actions so someone feels cared for.")],
    "dialogue": [("What is dialogue?", "Dialogue is when characters talk to each other in a story.")],
    "rhyme": [("What is a nursery rhyme?", "A nursery rhyme is a short, musical story or poem with a playful beat.")],
}
KNOWLEDGE_ORDER = ["scissor", "kindness", "dialogue", "rhyme"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"scissor", "kindness", "dialogue", "rhyme"}
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        ITEMS[params.item],
        PROBLEMS[params.problem],
        RESPONSES["careful_cut"],
        params.child,
        params.child_gender,
        params.helper,
        params.helper_gender,
        params.helper_role,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
reasonable_story(S, I, P) :- setting(S), item(I), problem(P), I = scissor.
#show reasonable_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable_story/3."))
    return sorted(set(asp.atoms(model, "reasonable_story")))


def asp_verify() -> int:
    rc = 0
    if set(asp_reasonable()) == set((s, "scissor", p) for s, _, p in valid_combos()):
        print("OK: ASP and Python gate match.")
    else:
        rc = 1
        print("MISMATCH in ASP/Python gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, item=None, child=None, helper=None, helper_role=None), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_reasonable())
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
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
