#!/usr/bin/env python3
"""
storyworlds/worlds/alpaca_teamwork_conflict_cautionary_nursery_rhyme.py
=======================================================================

A tiny storyworld about an alpaca, a shared job, a quarrel, and a cautious
lesson, told in a nursery-rhyme style.

The world is intentionally small:
- a child and an alpaca are trying to finish a task together;
- one choice causes a snag;
- a cautious helper warns them away from a worse path;
- the ending shows a changed physical scene.

The prose is state-driven, not a frozen paragraph with swapped nouns.
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
from pathlib import Path
from typing import Callable, Optional

# ---------------------------------------------------------------------------
# Robust bootstrap: walk upward until we find results.py, then insert that dir.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
for _parent in [_HERE.parent, *_HERE.parents]:
    if (_parent / "results.py").exists():
        sys.path.insert(0, str(_parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, object] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    scene: str
    sound: str
    surface: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    noun: str
    shared_item: str
    mess: str
    risk: str
    outcome_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    caution: str
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
        self.facts: dict[str, object] = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["tangled"] < THRESHOLD:
            continue
        sig = ("tangle", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get("helper")
        helper.memes["worry"] += 1
        world.get("child").memes["frustration"] += 1
        out.append("__tangle__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["spilled"] < THRESHOLD:
            continue
        sig = ("spill", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("ground").meters["mess"] += 1
        world.get("alpaca").memes["embarrassed"] += 1
        out.append("__spill__")
    return out


CAUSAL_RULES = [Rule("tangle", _r_tangle), Rule("spill", _r_spill)]


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


def caution_gate(task: Task, tool: Tool) -> bool:
    return task.id != "ribbon_tie" or tool.id == "spare_bow"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def severity(task: Task, delay: int) -> int:
    return 1 + delay + (1 if task.id == "hay_bale" else 0)


def contained(resp: Response, task: Task, delay: int) -> bool:
    return resp.power >= severity(task, delay)


def predict_mess(world: World, task: Task) -> dict[str, object]:
    sim = world.copy()
    sim.get("shared").meters["tangled"] += 1
    propagate(sim, narrate=False)
    return {
        "frustration": sim.get("child").memes["frustration"],
        "worry": sim.get("helper").memes["worry"],
    }


def play_setup(world: World, child: Entity, alpaca: Entity, place: Place, task: Task) -> None:
    child.memes["joy"] += 1
    alpaca.memes["joy"] += 1
    world.say(
        f"At {place.label}, under a soft little sky, {child.id} and {alpaca.id} set out to "
        f"{task.verb} {task.noun}. {place.scene}"
    )
    world.say(
        f"{alpaca.id} went clip-clop, and the day sang a tiny song: {place.sound}."
    )


def teamwork(world: World, child: Entity, alpaca: Entity, task: Task) -> None:
    child.memes["trust"] += 1
    alpaca.memes["trust"] += 1
    world.say(
        f"{child.id} held one end, and {alpaca.id} held the other; together they tried to "
        f"{task.verb} the {task.shared_item}."
    )


def conflict(world: World, child: Entity, alpaca: Entity, task: Task) -> None:
    child.memes["grumpy"] += 1
    alpaca.memes["grumpy"] += 1
    world.say(
        f"But one twist went wrong. {child.id} pulled too hard, and the {task.shared_item} "
        f"snagged and swung."
    )
    world.get("shared").meters["tangled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"\"Oh dear,\" said {alpaca.id}, and {child.id} frowned, for the little job had turned "
        f"into a knotty fuss."
    )


def warn(world: World, helper: Entity, task: Task, tool: Tool) -> None:
    pred = predict_mess(world, task)
    helper.memes["worry"] += 1
    world.facts["predicted"] = pred
    world.say(
        f"{helper.id} hopped closer and spoke in a gentle tone: \"No, no, little ones, not that way. "
        f"{task.risk}.\""
    )
    world.say(
        f"\"Use {tool.label} instead,\" {helper.id} said. \"That is the safer way to {tool.use}.\""
    )


def rescue(world: World, helper: Entity, resp: Response, task: Task) -> None:
    world.get("shared").meters["tangled"] = 0.0
    world.get("ground").meters["mess"] = 0.0
    body = resp.text.replace("{task}", task.noun)
    world.say(f"{helper.id} came at once and {body}.")
    world.say(
        f"At last the {task.shared_item} lay still again, and the little place looked neat once more."
    )


def lesson(world: World, child: Entity, alpaca: Entity, helper: Entity, tool: Tool) -> None:
    child.memes["relief"] += 1
    alpaca.memes["relief"] += 1
    world.say("Then all were quiet for a moment, and the breeze seemed kinder than before.")
    world.say(
        f"{helper.id} smiled and said, \"Teamwork is lovely, but caution is kind. "
        f"When a thing feels tricky, choose the safer plan.\""
    )
    world.say(
        f"{child.id} and {alpaca.id} nodded, and {tool.label} stayed near them like a promise."
    )


def ending(world: World, child: Entity, alpaca: Entity, place: Place, task: Task, tool: Tool) -> None:
    child.memes["joy"] += 1
    alpaca.memes["joy"] += 1
    world.say(
        f"So side by side they tried again, this time with {tool.label}, and the {task.shared_item} "
        f"{task.outcome_image}."
    )
    world.say(
        f"{place.label} shone soft and clean, and {child.id} and {alpaca.id} were glad to finish together."
    )


def tell(place: Place, task: Task, tool: Tool, response: Response, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    alpaca = world.add(Entity(id="alpaca", kind="character", type="alpaca", role="helper"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="cautioner"))
    ground = world.add(Entity(id="ground", type="place"))
    shared = world.add(Entity(id="shared", type="thing", label=task.shared_item))
    world.facts["place"] = place
    world.facts["task"] = task
    world.facts["tool"] = tool
    world.facts["response"] = response
    world.facts["delay"] = delay
    world.facts["child"] = child
    world.facts["alpaca"] = alpaca
    world.facts["helper"] = helper
    world.facts["shared"] = shared

    play_setup(world, child, alpaca, place, task)
    world.para()
    teamwork(world, child, alpaca, task)
    warn(world, helper, task, tool)
    if caution_gate(task, tool):
        conflict(world, child, alpaca, task)
    else:
        world.say(f"At once they listened, and the knot was never made.")
    world.para()
    if contained(response, task, delay):
        rescue(world, helper, response, task)
        lesson(world, child, alpaca, helper, tool)
        world.para()
        ending(world, child, alpaca, place, task, tool)
        world.facts["outcome"] = "contained"
    else:
        world.say(
            f"{helper.id} tried the kind {response.fail.replace('{task}', task.noun)}, but the trouble had grown too big."
        )
        world.say(
            f"So they lifted the {task.shared_item} down, breathed slow, and fixed it the simple way."
        )
        lesson(world, child, alpaca, helper, tool)
        world.para()
        ending(world, child, alpaca, place, task, tool)
        world.facts["outcome"] = "recovered"
    return world


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the meadow",
        scene="The grass was green and the clover was round.",
        sound="mew-mew, hoo-hoo, rustle-and-sway",
        surface="soft grass",
        tags={"meadow", "outdoor"},
    ),
    "barnyard": Place(
        id="barnyard",
        label="the barnyard",
        scene="A red barn stood bright, and the fence made tidy squares.",
        sound="clink-clop, clink-clop",
        surface="packed dirt",
        tags={"barnyard", "outdoor"},
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        scene="The beans were tall, and the stones made a little path.",
        sound="tick-tock, hum-hum",
        surface="garden path",
        tags={"garden", "outdoor"},
    ),
}

TASKS = {
    "ribbon_tie": Task(
        id="ribbon_tie",
        verb="tie",
        noun="a ribbon on the gate",
        shared_item="ribbon",
        mess="knotted",
        risk="A ribbon can snag and tug hard if it is yanked",
        outcome_image="fluttered neatly on the gate",
        tags={"ribbon", "teamwork"},
    ),
    "hay_bale": Task(
        id="hay_bale",
        verb="stack",
        noun="the hay bales",
        shared_item="hay bales",
        mess="shifted",
        risk="Hay bales wobble and can topple if pushed too fast",
        outcome_image="stood in a tidy little tower",
        tags={"hay", "teamwork"},
    ),
    "kite_string": Task(
        id="kite_string",
        verb="wind",
        noun="the kite string",
        shared_item="kite string",
        mess="tangled",
        risk="Kite string can knot up and make a sleepy snarl",
        outcome_image="coiled in a smooth bright loop",
        tags={"kite", "teamwork"},
    ),
}

TOOLS = {
    "spare_bow": Tool(
        id="spare_bow",
        label="a spare bow",
        use="make it neat",
        caution="ties gently and keeps the ribbon from tearing",
        tags={"safer"},
    ),
    "little_hook": Tool(
        id="little_hook",
        label="a little hook",
        use="steady the string",
        caution="keeps the kite string from twisting into a jumble",
        tags={"safer"},
    ),
    "flat_board": Tool(
        id="flat_board",
        label="a flat board",
        use="balance the hay",
        caution="gives the hay a broad and careful base",
        tags={"safer"},
    ),
}

RESPONSES = {
    "gentle_tie": Response(
        id="gentle_tie",
        sense=3,
        power=2,
        text="lifted the ribbon free and tied it back with patient hands",
        fail="lifted the ribbon, but the knot was too strong to fix",
        qa_text="lifted the ribbon free and tied it back with patient hands",
    ),
    "steady_board": Response(
        id="steady_board",
        sense=3,
        power=3,
        text="braced the hay with the board and set the stack straight again",
        fail="braced the hay, but the stack kept wobbling and slid apart",
        qa_text="braced the hay with the board and set the stack straight again",
    ),
    "untangle": Response(
        id="untangle",
        sense=2,
        power=2,
        text="worked the string loose and laid it down in a straight, bright line",
        fail="worked at the string, but the tangles would not let go",
        qa_text="worked the string loose and laid it down in a straight, bright line",
    ),
    "water_bucket": Response(
        id="water_bucket",
        sense=1,
        power=1,
        text="splashed water everywhere, which did not help much at all",
        fail="splashed water everywhere, which did not help much at all",
        qa_text="splashed water everywhere",
    ),
}

CHILD_NAMES = ["Lily", "Milo", "Tessa", "Pip", "Nora", "Rowan", "Ivy", "Theo"]
HELPER_NAMES = ["Mama", "Papa", "Nana", "Grandpa"]
TRAITS = ["cheerful", "curious", "gentle", "bright", "lively"]


@dataclass
class StoryParams:
    place: str
    task: str
    tool: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="meadow", task="ribbon_tie", tool="spare_bow", response="gentle_tie",
                child_name="Lily", child_gender="girl", helper_name="Mama", helper_gender="woman",
                trait="cheerful", delay=0),
    StoryParams(place="barnyard", task="hay_bale", tool="flat_board", response="steady_board",
                child_name="Milo", child_gender="boy", helper_name="Papa", helper_gender="man",
                trait="curious", delay=0),
    StoryParams(place="garden", task="kite_string", tool="little_hook", response="untangle",
                child_name="Nora", child_gender="girl", helper_name="Nana", helper_gender="woman",
                trait="gentle", delay=1),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for t in TASKS:
            for u in TOOLS:
                if caution_gate(TASKS[t], TOOLS[u]):
                    combos.append((p, t, u))
    return combos


def explain_rejection(task: Task, tool: Tool) -> str:
    return f"(No story: {tool.label} is not a cautious fit for {task.noun}. Pick the safer helper tool.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Alpaca teamwork, conflict, and caution in a nursery rhyme style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, tool = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_gender = "girl" if child_name in {"Lily", "Tessa", "Nora", "Ivy"} else "boy"
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != child_name])
    helper_gender = "woman" if helper_name in {"Mama", "Nana"} else "man"
    return StoryParams(
        place=place, task=task, tool=tool, response=response,
        child_name=child_name, child_gender=child_gender,
        helper_name=helper_name, helper_gender=helper_gender,
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    task = f["task"]
    tool = f["tool"]
    return [
        f'Write a nursery-rhyme style story about an alpaca helping a child at {place.label}, using the word "alpaca".',
        f"Tell a gentle cautionary tale where teamwork goes a little wrong while {task.verb}ing {task.noun}, then gets fixed safely.",
        f"Write a short child-friendly rhyme with conflict and a careful ending, where {tool.label} helps solve the problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    alpaca = f["alpaca"]
    helper = f["helper"]
    task = f["task"]
    place = f["place"]
    tool = f["tool"]
    resp = f["response"]
    out = f["outcome"]
    qa = [
        QAItem(
            question=f"What were {child.id} and the alpaca trying to do at {place.label}?",
            answer=f"They were trying to {task.verb} {task.noun} together. It began as teamwork, with both of them holding on and trying to help.",
        ),
        QAItem(
            question=f"What went wrong when {child.id} worked with the alpaca?",
            answer=f"The {task.shared_item} snagged and turned into a tangle. That made both of them grumpy, because the shared job stopped being smooth.",
        ),
        QAItem(
            question=f"Who gave the cautious warning in the story?",
            answer=f"{helper.id} gave the warning and pointed out the safer way. The helper noticed the trouble before it could get worse.",
        ),
    ]
    if out == "contained":
        qa.append(QAItem(
            question=f"How was the problem fixed in the end?",
            answer=f"{helper.id} used {resp.qa_text}. After that, the {task.shared_item} lay still again and the little scene looked neat.",
        ))
        qa.append(QAItem(
            question=f"What changed for {child.id} and the alpaca by the ending?",
            answer=f"They were calm and happy again, and they kept working together more carefully. The ending shows the {task.shared_item} in its finished, tidy shape.",
        ))
    return qa


KNOWLEDGE = {
    "alpaca": [("What is an alpaca?", "An alpaca is a fluffy animal with a long neck and a soft coat. Alpacas are gentle and can help carry things in a story.")],
    "teamwork": [("What is teamwork?", "Teamwork means people or animals help each other to finish one job. Everyone does a part, and the job gets easier.")],
    "conflict": [("What is a conflict in a story?", "A conflict is a problem or disagreement that makes the story tense for a little while.")],
    "cautionary": [("What does cautionary mean?", "A cautionary story gives a warning and helps children learn to choose the safer way.")],
}
KNOWLEDGE_ORDER = ["alpaca", "teamwork", "conflict", "cautionary"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags) | {"alpaca", "teamwork", "conflict", "cautionary"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,U) :- place(P), task(T), tool(U), cautious(T,U).
outcome(contained) :- chosen_task(T), chosen_response(R), power(R, P), severity(T, S), P >= S.
outcome(recovered) :- chosen_task(T), chosen_response(R), power(R, P), severity(T, S), P < S.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for u in TOOLS:
        lines.append(asp.fact("tool", u))
    for t, task in TASKS.items():
        lines.append(asp.fact("severity", t, 1 + (1 if t == "hay_bale" else 0)))
    for u in TOOLS:
        for t in TASKS:
            if caution_gate(TASKS[t], TOOLS[u]):
                lines.append(asp.fact("cautious", t, u))
    for r, resp in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("power", r, resp.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP valid combos differ from Python.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as e:
        ok = False
        print(f"MISMATCH: generate smoke test failed: {e}")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS or params.tool not in TOOLS or params.place not in PLACES:
        raise StoryError("Invalid params.")
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    if not caution_gate(task, tool):
        raise StoryError(explain_rejection(task, tool))
    world = tell(
        PLACES[params.place], task, tool, RESPONSES[params.response],
        params.child_name, params.child_gender, params.helper_name, params.helper_gender,
        delay=params.delay,
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
