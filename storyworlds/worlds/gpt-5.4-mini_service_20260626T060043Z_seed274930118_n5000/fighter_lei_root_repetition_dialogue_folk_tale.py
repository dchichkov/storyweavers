#!/usr/bin/env python3
"""
storyworlds/worlds/fighter_lei_root_repetition_dialogue_folk_tale.py
====================================================================

A small folk-tale storyworld about a fighter named Lei, a stubborn root, and
a patient way through a problem.

Seed tale shape:
- Lei is a young fighter who wants to prove strength.
- A great root blocks a spring in the village grove.
- Lei first wants to strike the root at once.
- An elder warns that force alone may split the ground.
- Through repeated tries, dialogue, and a gentler method, Lei frees the spring
  and learns that strength can be soft, too.

This world emphasizes repetition and dialogue in a folk-tale style.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"woman", "girl", "mother", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "boy", "father", "fighter"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old grove"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    method: str
    mess: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    prep: str = ""


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trail: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trail.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
SETTINGS = {
    "grove": Setting(place="the old grove", affords={"pull", "cut", "loosen"}),
}

ACTIONS = {
    "pull": Action(
        id="pull",
        verb="pull the root free",
        gerund="pulling at the root",
        rush="heave with all his might",
        method="pull",
        mess="earth-splitting force",
        risk="the root might snap and leave half of it buried",
        tags={"root", "force"},
    ),
    "cut": Action(
        id="cut",
        verb="cut the root away",
        gerund="cutting at the root",
        rush="raise his blade again and again",
        method="cut",
        mess="sharp harm",
        risk="the root might tear the soil and scare the spring deeper down",
        tags={"root", "blade"},
    ),
    "loosen": Action(
        id="loosen",
        verb="loosen the root slowly",
        gerund="loosening the root",
        rush="work the soil with patient hands",
        method="loosen",
        mess="gentle mud",
        risk="the root might hold fast unless the earth was softened first",
        tags={"root", "patient"},
    ),
}

TOOLS = {
    "spade": Tool(
        id="spade",
        label="a small spade",
        phrase="a small spade with a wooden handle",
        helps={"loosen"},
        prep="dig around the root first",
    ),
    "bucket": Tool(
        id="bucket",
        label="a bucket of water",
        phrase="a bucket of clear water",
        helps={"loosen"},
        prep="pour water around the root",
    ),
    "blade": Tool(
        id="blade",
        label="a bright blade",
        phrase="a bright blade",
        helps={"cut"},
        prep="strike the root with a sharp edge",
    ),
}

CURATED = ["pull", "loosen"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "grove"
    action: str = "loosen"
    tool: Optional[str] = None
    name: str = "Lei"
    title: str = "fighter"
    elder: str = "grandmother"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def reasonableness_gate(action: Action, tool: Optional[Tool]) -> bool:
    if action.id in {"pull", "cut"} and tool is None:
        return False
    if action.id == "cut" and tool and tool.id != "blade":
        return False
    if action.id == "pull" and tool and tool.id != "spade":
        return False
    if action.id == "loosen" and tool and tool.id not in {"spade", "bucket"}:
        return False
    return True


def explain_rejection(action: Action) -> str:
    if action.id == "pull":
        return "(No story: pulling a root bare-handed would be too blunt for this folk tale; the root needs a tool or a gentler plan.)"
    if action.id == "cut":
        return "(No story: cutting the root without the bright blade would not make sense here.)"
    return "(No story: this root story needs a gentle tool plan, not an unrelated object.)"


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------
def tell(setting: Setting, action: Action, tool: Optional[Tool], params: StoryParams) -> World:
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.title, label=params.name))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label=params.elder))
    root = world.add(Entity(id="root", type="root", label="the root", phrase="a thick old root"))
    spring = world.add(Entity(id="spring", type="thing", label="the spring", phrase="a hidden spring"))
    if tool:
        tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    else:
        tool_ent = None

    hero.memes["resolve"] = 1.0
    root.meters["buried"] = 1.0
    spring.meters["blocked"] = 1.0
    spring.meters["dry"] = 1.0

    # Act I: folk-tale opening
    world.say(f"Long ago in {setting.place}, there lived a young {hero.type} named {hero.id}.")
    world.say(f"{hero.id} was a brave {params.title}, and the villagers said, 'Strong arms, strong heart.'")
    world.say(f"Each dawn, {hero.id} walked to the grove and looked at {root.phrase} that had wound itself over {spring.label}.")

    world.para()

    # Act II: repetition and warning
    world.say(f"\"I will {action.verb},\" said {hero.id}.")
    world.say(f"\"I will {action.verb},\" {hero.id} said again, because the root looked stubborn and old.")
    if tool_ent:
        world.say(f"{hero.id} held {tool.label} and tried to be proud of it.")
    else:
        world.say(f"{hero.id} had only bare hands and a loud wish.")

    hero.memes["desire"] = 1.0
    hero.memes["stubborn"] = 1.0
    root.meters["stubborn"] = 1.0

    if action.id in {"pull", "cut"}:
        world.say(f"{hero.id} tried to {action.rush}, but {action.risk}.")
    else:
        world.say(f"{hero.id} tried to {action.rush}, but {action.risk}.")

    world.say(f"Then the elder came and said, \"Do not be hasty, Lei. The root is old, and old things listen slowly.\"")
    world.say(f"\"Slowly, then,\" said {hero.id}. \"Slowly, then,\" the elder answered.")

    world.para()

    # Act III: turn and resolution
    if action.id == "loosen":
        hero.memes["patience"] = 1.0
        root.meters["buried"] = 0.0
        spring.meters["blocked"] = 0.0
        spring.meters["dry"] = 0.0
        hero.memes["joy"] = 1.0
        world.say(f"So {hero.id} did not strike first. {hero.id} dug around the root with care.")
        if tool_ent and tool_ent.id == "bucket":
            world.say(f"{hero.id} poured water around the roots again and again, and the earth softened.")
        elif tool_ent and tool_ent.id == "spade":
            world.say(f"With {tool.label}, {hero.id} opened little paths in the soil, and the root began to loosen.")
        else:
            world.say(f"With patient hands, {hero.id} worked the dark earth until the root began to move.")
        world.say(f"At last the root slid aside, and the spring sang up bright water.")
        world.say(f"The elder smiled. \"Strong hands are good,\" she said, \"but a patient heart is stronger.\"")
        world.say(f"{hero.id} laughed and said, \"Slowly, then.\"")
        world.say(f"And from that day on, the grove kept its water, and Lei kept his lesson.")
    elif action.id == "pull":
        hero.memes["frustration"] = 1.0
        root.meters["buried"] = 0.5
        spring.meters["blocked"] = 0.5
        world.say(f"So {hero.id} pulled and pulled until the earth groaned.")
        world.say(f"The root moved a little, but it would not come cleanly free.")
        world.say(f"The elder shook her head and said, \"A root is not a stone. Listen before you lift.\"")
        world.say(f"{hero.id} took a breath, knelt down, and promised to try again more gently.")
        world.say(f"Then the root loosened, the spring whispered, and the grove was not thirsty anymore.")
        world.say(f"Lei bowed his head and said, \"I hear you now, root.\"")
    else:
        hero.memes["patience"] = 1.0
        root.meters["buried"] = 0.0
        spring.meters["blocked"] = 0.0
        spring.meters["dry"] = 0.0
        hero.memes["joy"] = 1.0
        world.say(f"So {hero.id} waited, and waited, and waited.")
        world.say(f"The elder said, \"Good. Roots wake up when the earth softens.\"")
        world.say(f"The ground sighed open, the root loosened, and the spring brightened at last.")
        world.say(f"{hero.id} smiled and said, \"Slowly, then,\" and the elder laughed beside {hero.id}.")

    world.facts.update(
        hero=hero,
        elder=elder,
        root=root,
        spring=spring,
        tool=tool_ent,
        action=action,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    return [
        f'Write a short folk tale about a {hero.type} named {hero.id} who must {action.verb} without rushing.',
        f"Tell a gentle story with repeated words like 'slowly, then' and a dialogue between {hero.id} and an elder.",
        f'Write a child-friendly story where a stubborn root blocks a spring and a fighter learns patience.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    action = f["action"]
    root = f["root"]
    spring = f["spring"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who is the folk tale about?",
            answer=f"It is about {hero.id}, a young {hero.type}, and the old lesson that came from the grove.",
        ),
        QAItem(
            question=f"What was blocking {spring.label}?",
            answer=f"{root.phrase} was blocking {spring.label}, so the water could not come up at first.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the start?",
            answer=f"{hero.id} wanted to {action.verb}, because the root looked too stubborn to wait for.",
        ),
        QAItem(
            question=f"Who warned {hero.id} not to be hasty?",
            answer=f"The elder warned {hero.id} and said that old things listen slowly.",
        ),
    ]
    if tool:
        qa.append(
            QAItem(
                question=f"Which tool helped {hero.id} in the end?",
                answer=f"{tool.label} helped {hero.id}, because it fit the gentle plan better than a hard blow.",
            )
        )
    qa.append(
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The root moved aside, the spring sang with water again, and {hero.id} learned to be patient.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a root?",
            answer="A root is the part of a plant that grows under the ground and holds the plant in place while drinking water from the soil.",
        ),
        QAItem(
            question="Why can water matter in dry ground?",
            answer="Water can soften dry ground, making it easier for plants and roots to move or grow.",
        ),
        QAItem(
            question="What is patience?",
            answer="Patience is the calm ability to wait and keep trying without rushing too hard.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/2.
#show valid_story/3.

valid(Action, Tool) :- action(Action), tool(Tool), compatible(Action, Tool).
valid(Action, none) :- action(Action), no_tool_ok(Action).

valid_story(Place, Action, Tool) :- setting(Place), valid(Action, Tool), affords(Place, Action).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("compatible", h, tid))
    lines.append(asp.fact("no_tool_ok", "loosen"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for a in ACTIONS.values():
        for t in TOOLS.values():
            if reasonableness_gate(a, t):
                py.add((a.id, t.id))
        if reasonableness_gate(a, None):
            py.add((a.id, "none"))
    asp_set = set(asp_valid())
    if asp_set == py:
        print(f"OK: clingo gate matches python gate ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(asp_set - py))
    print("  only in python:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk tale storyworld: fighter Lei, a root, and a lesson in patience.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", default="Lei")
    ap.add_argument("--title", choices=["fighter"], default="fighter")
    ap.add_argument("--elder", default="grandmother")
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
    action_id = args.action or rng.choice(list(ACTIONS))
    action = ACTIONS[action_id]

    tool_id = args.tool
    if tool_id is None:
        if action_id == "loosen":
            tool_id = rng.choice(["spade", "bucket"])
        elif action_id == "pull":
            tool_id = "spade"
        else:
            tool_id = "blade"
    tool = TOOLS.get(tool_id) if tool_id else None

    if not reasonableness_gate(action, tool):
        raise StoryError(explain_rejection(action))

    return StoryParams(
        place=args.place or "grove",
        action=action_id,
        tool=tool_id,
        name=args.name or "Lei",
        title=args.title,
        elder=args.elder or "grandmother",
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    action = ACTIONS[params.action]
    tool = TOOLS.get(params.tool) if params.tool else None
    world = tell(setting, action, tool, params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(str(x) for x in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible action/tool combinations:")
        for action, tool in combos:
            print(f"  {action:8} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for idx, action_id in enumerate(CURATED):
            params = StoryParams(action=action_id, tool="spade" if action_id != "cut" else "blade", seed=base_seed + idx)
            samples.append(generate(params))
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
