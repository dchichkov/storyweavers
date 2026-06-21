#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/secondary_parentheses_tonsil_rhyme_adventure.py
===============================================================================

A small adventure storyworld built from the seed words:
secondary, parentheses, tonsil.

The domain is child-facing adventure: two kids follow a map, take a secondary
path, read a clue hidden in parentheses, and help a grumpy cave creature with a
sore tonsil. The prose leans into rhyme while still being state-driven: a trail
can be blocked, a clue can be missed, a helper can calm the danger, and the
ending proves what changed in the world.

The story world is intentionally small and constraint-checked:
- the secondary path must matter,
- the parentheses clue must be read,
- the tonsil trouble must be plausible and fixable,
- the rhyme feature is always used in the narration,
- the adventure style stays bright, concrete, and forward-moving.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
HAPPY_MEME = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    trail: str = "forest"
    clue_style: str = "parentheses"
    trouble: str = "tonsil"
    helper: str = "goat"
    tool: str = "lantern"
    hero1: str = "Mina"
    hero1_gender: str = "girl"
    hero2: str = "Theo"
    hero2_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


@dataclass
class Trail:
    id: str
    label: str
    scene: str
    side: str
    blocked_by: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    hidden_in: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    sore_phrase: str
    danger: str
    fix_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    comfort: str
    aid: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["helped"] >= THRESHOLD and ("relief", e.id) not in world.fired:
            world.fired.add(("relief", e.id))
            e.memes["relief"] += 1
            out.append("__relief__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["soothed"] >= THRESHOLD and ("calm", e.id) not in world.fired:
            world.fired.add(("calm", e.id))
            e.memes["calm"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("relief", _r_relief), Rule("calm", _r_calm)]


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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def predict_help(world: World, helper: Helper, trouble: Trouble) -> dict:
    sim = world.copy()
    _resolve_trouble(sim, sim.get("helper"), sim.get("hero1"), sim.get("hero2"), narrate=False)
    return {"helped": sim.get("helper").meters["helped"] >= THRESHOLD, "calm": sim.get("helper").memes["calm"]}


def _resolve_trouble(world: World, helper: Entity, a: Entity, b: Entity, narrate: bool = True) -> None:
    helper.meters["helped"] += 1
    a.meters["helped"] += 1
    b.meters["helped"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, a: Entity, b: Entity, trail: Trail) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright adventure day, {a.id} and {b.id} strode along the {trail.label} trail, "
        f"where the pines swayed fine and the sky shone kind."
    )
    world.say(
        f"The path was a bold road, a main-road parade, and the map kept a {trail.side} lane "
        f"that gleamed like a little secret."
    )


def blocked(world: World, trail: Trail) -> None:
    world.say(
        f"But ahead, the {trail.blocked_by} barred the brave path, so the pair had to turn to a "
        f"{trail.side} track and make a new start."
    )


def clue_scene(world: World, clue: Clue, a: Entity, b: Entity) -> None:
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"{a.id} spotted a note {clue.hidden_in}, tucked tight and bright. "
        f"{b.id} read it aloud, and the words came out light."
    )
    world.say(f'"{clue.text}"')
    world.say(f"The clue {clue.reveal}, and the two friends smiled like spring-time tiles.")


def trouble_scene(world: World, trouble: Trouble, helper: Helper, a: Entity, b: Entity) -> None:
    world.say(
        f"Deeper in the cave, a {trouble.label} sat in a hollow hall. "
        f"It was sore, and it made the cave-creature feel small."
    )
    world.say(
        f'The creature whispered, "{trouble.sore_phrase}. {trouble.danger}."'
    )
    pred = predict_help(world, helper, world.facts["trouble_cfg"])
    world.facts["pred_helped"] = pred["helped"]
    world.facts["pred_calm"] = pred["calm"]


def warn_and_offer(world: World, helper: Helper, tool: Tool, a: Entity, b: Entity) -> None:
    world.say(
        f"{a.id} held up the {tool.label}, and {b.id} nodded slow and low. "
        f'"A little light can lead the night," they said, "and a soft voice can help the ache let go."'
    )
    world.say(
        f"The {helper.label} leaned near, not fierce, not curt, and gave a calm, warm murmur in return."
    )


def resolve(world: World, helper: Helper, trouble: Trouble, tool: Tool, a: Entity, b: Entity) -> None:
    _resolve_trouble(world, world.get("helper"), a, b, narrate=False)
    helper.memes["trust"] += 1
    helper.memes["calm"] += 1
    world.get("helper").meters["soothed"] += 1
    world.say(
        f"Then the {helper.label} took the helpful {tool.label} glow, and the sore {trouble.id} stopped its sting."
    )
    world.say(
        f"The cave-creature could swallow, smile, and sing, and the echo went ding-dong-ding."
    )


def ending(world: World, trail: Trail, a: Entity, b: Entity, helper: Helper) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"At last they walked back by the {trail.side} path, not lost, not blue. "
        f"The map had a secret, the cave had a cure, and the trio felt true."
    )
    world.say(
        f"{a.id} and {b.id} waved goodbye, with boots full of dust and hearts full of cheer. "
        f"The secondary road was the right road after all, and their rhyme rang clear."
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TRAILS:
        for c in CLUES:
            for tr in TROUBLES:
                if c.id != "parentheses":
                    continue
                if tr.id != "tonsil":
                    continue
                combos.append((t.id, c.id, tr.id))
    return combos


TRAILS = {
    "forest": Trail(
        id="forest",
        label="forest",
        scene="a winding adventure lane",
        side="secondary trail",
        blocked_by="fallen logs",
        rhyme_a="pine",
        rhyme_b="fine",
        tags={"adventure", "secondary"},
    ),
    "canyon": Trail(
        id="canyon",
        label="canyon",
        scene="a rocky adventure lane",
        side="secondary path",
        blocked_by="a tumble of stones",
        rhyme_a="stone",
        rhyme_b="home",
        tags={"adventure", "secondary"},
    ),
    "island": Trail(
        id="island",
        label="island",
        scene="a sandy adventure lane",
        side="secondary route",
        blocked_by="a tide pool maze",
        rhyme_a="shore",
        rhyme_b="more",
        tags={"adventure", "secondary"},
    ),
}

CLUES = {
    "parentheses": Clue(
        id="parentheses",
        text="Take the side path (the one with the silver moss)",
        hidden_in="inside parentheses",
        reveal="pointed to the safer road",
        tags={"parentheses", "clue"},
    )
}

TROUBLES = {
    "tonsil": Trouble(
        id="tonsil",
        label="tonsil trouble",
        sore_phrase="my tonsil hurts like a pebble in my throat",
        danger="I can't sing or swallow my supper",
        fix_need="gentle care",
        tags={"tonsil", "help"},
    )
}

HELPERS = {
    "goat": Helper(
        id="goat",
        label="goat guide",
        kind="goat",
        comfort="a kind bleat",
        aid="helps with a soft, silly smile",
        tags={"helper", "adventure"},
    ),
    "rabbit": Helper(
        id="rabbit",
        label="rabbit healer",
        kind="rabbit",
        comfort="a fluffy nod",
        aid="offers a warm cup and a calm pat",
        tags={"helper", "adventure"},
    ),
}

TOOLS = {
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a lantern",
        glow="glowed gold",
        tags={"light", "adventure"},
    ),
    "torch": Tool(
        id="torch",
        label="torch",
        phrase="a torch",
        glow="shone bright",
        tags={"light", "adventure"},
    ),
}


@dataclass
class StoryParams:
    trail: str = "forest"
    clue_style: str = "parentheses"
    trouble: str = "tonsil"
    helper: str = "goat"
    tool: str = "lantern"
    hero1: str = "Mina"
    hero1_gender: str = "girl"
    hero2: str = "Theo"
    hero2_gender: str = "boy"
    parent: str = "mother"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure rhyme storyworld with a secondary trail, parentheses clue, and tonsil trouble.")
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--clue-style", choices=CLUES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero1")
    ap.add_argument("--hero2")
    ap.add_argument("--parent", choices=["mother", "father"])
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


def explain_rejection() -> str:
    return "(No story: this world only tells the secondary-path parentheses clue and tonsil-help adventure.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue_style and args.clue_style != "parentheses":
        raise StoryError(explain_rejection())
    if args.trouble and args.trouble != "tonsil":
        raise StoryError(explain_rejection())
    trail = args.trail or rng.choice(list(TRAILS))
    clue = args.clue_style or "parentheses"
    trouble = args.trouble or "tonsil"
    helper = args.helper or rng.choice(list(HELPERS))
    tool = args.tool or rng.choice(list(TOOLS))
    hero1 = args.hero1 or rng.choice(["Mina", "Nora", "Lena", "Pia"])
    hero2 = args.hero2 or rng.choice(["Theo", "Owen", "Milo", "Finn"])
    if hero1 == hero2:
        hero2 += "n"
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        trail=trail,
        clue_style=clue,
        trouble=trouble,
        helper=helper,
        tool=tool,
        hero1=hero1,
        hero1_gender="girl" if hero1 in {"Mina", "Nora", "Lena", "Pia"} else "boy",
        hero2=hero2,
        hero2_gender="boy" if hero2 not in {"Mina", "Nora", "Lena", "Pia"} else "girl",
        parent=parent,
    )


def _build_world(params: StoryParams) -> World:
    if params.trail not in TRAILS:
        raise StoryError("Unknown trail.")
    if params.clue_style not in CLUES:
        raise StoryError("Unknown clue style.")
    if params.trouble not in TROUBLES:
        raise StoryError("Unknown trouble.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")

    world = World()
    a = world.add(Entity(id=params.hero1, kind="character", type=params.hero1_gender, role="hero"))
    b = world.add(Entity(id=params.hero2, kind="character", type=params.hero2_gender, role="sidekick"))
    p = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    helper = world.add(Entity(id="helper", kind="character", type=HELPERS[params.helper].kind, label=HELPERS[params.helper].label))
    world.add(Entity(id="trail", label=TRAILS[params.trail].label))
    world.add(Entity(id="clue", label=CLUES[params.clue_style].text))
    world.add(Entity(id="trouble", label=TROUBLES[params.trouble].label))
    world.add(Entity(id="tool", label=TOOLS[params.tool].label))
    world.facts.update(
        trail_cfg=TRAILS[params.trail],
        clue_cfg=CLUES[params.clue_style],
        trouble_cfg=TROUBLES[params.trouble],
        helper_cfg=HELPERS[params.helper],
        tool_cfg=TOOLS[params.tool],
        hero1=a,
        hero2=b,
        parent=p,
        helper=helper,
    )
    opening(world, a, b, TRAILS[params.trail])
    world.para()
    blocked(world, TRAILS[params.trail])
    clue_scene(world, CLUES[params.clue_style], a, b)
    world.para()
    trouble_scene(world, TROUBLES[params.trouble], HELPER=params.helper if False else world.facts["helper_cfg"], a=a, b=b)  # type: ignore[arg-type]
    warn_and_offer(world, helper, TOOLS[params.tool], a, b)
    resolve(world, helper, TROUBLES[params.trouble], TOOLS[params.tool], a, b)
    world.para()
    ending(world, TRAILS[params.trail], a, b, helper)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure rhyme story that includes the words "secondary", "parentheses", and "tonsil".',
        f"Tell a child-friendly adventure where the heroes take a secondary path, read a clue in parentheses, and help a creature with a tonsil ache.",
        f"Write a rhyming quest story with a hidden parentheses clue and a helpful ending in a cave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trail: Trail = f["trail_cfg"]
    clue: Clue = f["clue_cfg"]
    trouble: Trouble = f["trouble_cfg"]
    helper: Helper = f["helper_cfg"]
    a: Entity = f["hero1"]
    b: Entity = f["hero2"]
    qa = [
        ("What kind of path did they take?",
         f"They took a {trail.side}, not the main road. That side path mattered because the big route was blocked."),
        ("What did the clue use?",
         f"It was hidden in {clue.hidden_in}. The parentheses made the clue feel secret and easy to spot once they looked closely."),
        ("What was wrong in the cave?",
         f"The cave creature had {trouble.sore_phrase}. It was a tonsil problem, so the creature needed gentle help."),
        ("Who helped them?",
         f"The {helper.label} helped them stay calm and choose the right next step. That made the adventure safer and kinder."),
        ("How did the story end?",
         f"They solved the problem and returned by the {trail.side}. The ending proves the side path and the clue both mattered."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does parentheses mean?",
         "Parentheses are curved marks that hold extra words inside a sentence. They can hide a little clue or aside."),
        ("What is a secondary path?",
         "A secondary path is a smaller side road, not the main route. Adventurers may use it when the big road is blocked."),
        ("What is a tonsil?",
         "Tonsils are small soft parts at the back of the throat. If they hurt, swallowing can feel uncomfortable."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(trail, parentheses, tonsil).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("trail", k) for k in TRAILS
    ] + [
        asp.fact("clue", k) for k in CLUES
    ] + [
        asp.fact("trouble", k) for k in TROUBLES
    ] + [
        asp.fact("helper", k) for k in HELPERS
    ] + [
        asp.fact("tool", k) for k in TOOLS
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    else:
        print("OK: ASP and Python valid_combos match.")
    try:
        sample = generate(StoryParams())
        assert sample.story
        print("OK: default generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


CURATED = [
    StoryParams(trail="forest", clue_style="parentheses", trouble="tonsil", helper="goat", tool="lantern", hero1="Mina", hero1_gender="girl", hero2="Theo", hero2_gender="boy", parent="mother"),
    StoryParams(trail="canyon", clue_style="parentheses", trouble="tonsil", helper="rabbit", tool="torch", hero1="Nora", hero1_gender="girl", hero2="Owen", hero2_gender="boy", parent="father"),
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combo(s):")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def valid_combos_stub() -> list[tuple[str, str, str]]:
    return valid_combos()


def _normalize_story(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What do parentheses do in writing?",
         "Parentheses hold extra words or a small aside inside a sentence. They can make a hidden clue feel playful."),
        ("What is a secondary trail?",
         "A secondary trail is a side route that is not the main path. Adventurers use it when the bigger road is blocked or too busy."),
        ("Why can tonsil pain make swallowing hard?",
         "Tonsils sit in the throat, so when they hurt, the throat can feel sore and tight. That makes swallowing uncomfortable."),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    trail: Trail = f["trail_cfg"]
    helper: Helper = f["helper_cfg"]
    return [
        ("Which path did they choose?",
         f"They chose the {trail.side}. That choice mattered because the main road was blocked."),
        ("What clue did they find?",
         "They found a clue written inside parentheses. The note helped them notice the safer way forward."),
        ("What kind of trouble did the cave creature have?",
         "It had tonsil trouble. The sore throat made it hard to sing or swallow until help arrived."),
        ("What changed by the end?",
         f"They returned by the {trail.side} with the cave creature feeling better. The helper's calm care turned the scary part into a safe ending."),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        'Write an adventure story that includes the words "secondary", "parentheses", and "tonsil".',
        "Tell a rhyming quest where a side path, a note in parentheses, and a sore throat all matter.",
        "Write a child-friendly adventure with a hidden clue and a helpful ending.",
    ]


if __name__ == "__main__":
    main()
