#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thought_quest_tall_tale.py
==========================================================

A standalone storyworld for a tiny Tall Tale quest: a child, a trusty helper,
a strange land, and one impossible-seeming search that turns on a smart
thought. The world tracks physical meters and emotional memes so the story is
driven by state, not by a frozen template.

Core premise:
- A child and a helper set out on a quest.
- The quest can go two ways: a brash shortcut or a patient method.
- A useful thought can avert trouble and reveal the real path.

The seed word "thought" is woven into the simulated events, and the overall
voice aims for a small Tall Tale: a bit grand, concrete, and cheerful.
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

    tags: set[str] = field(default_factory=set)

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



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    scene: str
    trail: str
    clue: str
    danger: str
    height: int
    mystery: int
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Quest:
    id: str
    title: str
    objective: str
    shortcut: str
    method: str
    ending: str
    prize: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Tool:
    id: str
    label: str
    kind: str
    helps: str
    risk: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["lost"] >= THRESHOLD and ent.id not in {x for x, *_ in world.fired}:
            sig = ("confusion", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["worry"] += 1
            out.append(f"{ent.id} felt the trail go crooked.")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes["thought"] < THRESHOLD:
            continue
        sig = ("clue", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["clue"] += 1
        out.append(f"A smart thought made the next step plain.")
    return out


CAUSAL_RULES = [Rule("confusion", "social", _r_confusion), Rule("clue", "mental", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def trek_risk(place: Place, quest: Quest) -> bool:
    return place.mystery >= 1 and quest.id in {"map", "river", "cave", "hill"}


def use_shortcut(world: World, child: Entity, tool: Tool) -> None:
    child.memes["brash"] += 1
    child.meters["lost"] += 1
    world.say(
        f'"{tool.label.capitalize()} will do it!" {child.id} cried, and took the {tool.label} for a quick shortcut.'
    )


def warn(world: World, helper: Entity, child: Entity, place: Place, quest: Quest) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} looked at the tall {place.label} and thought better of a hurry. '
        f'"{child.id}, this quest needs a patient step, or we may lose {quest.objective} in {place.danger}."'
    )


def reveal(world: World, helper: Entity, child: Entity, place: Place, quest: Quest) -> None:
    helper.memes["thought"] += 1
    child.memes["thought"] += 1
    child.meters["lost"] = 0
    child.meters["clue"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {child.id} had a thought as bright as a lantern in a barn: "
        f'the clue was not up high at all, but along {place.trail}.'
    )
    world.say(f"Together they followed it to {place.clue}, where the real search could begin.")


def complete(world: World, child: Entity, helper: Entity, quest: Quest, place: Place) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At last, the quest was done. They found {quest.prize} at {place.clue}, "
        f"and the whole wide place seemed to cheer."
    )
    world.say(
        f"{child.id} laughed, {helper.id} smiled, and the tall tale ended with "
        f"{quest.ending}: {quest.prize} tucked safe in small hands."
    )


def tell(place: Place, quest: Quest, tool: Tool, child_name: str = "Mina",
         child_gender: str = "girl", helper_name: str = "Uncle Finn",
         helper_gender: str = "man") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="quester"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="guide"))
    world.add(Entity(id=place.id, type="place", label=place.label))
    world.add(Entity(id=quest.id, type="quest", label=quest.title))
    world.add(Entity(id=tool.id, type="tool", label=tool.label))

    world.say(
        f"Long ago, when the sky looked like a blue drum, {child.id} and {helper.id} set out on {quest.title}."
    )
    world.say(
        f"Their path ran through {place.scene}, and everyone knew the place had {place.height} bends of trouble and one clue waiting like a wink."
    )
    world.say(
        f"{child.id} wanted {quest.objective}, and {helper.id} carried a steady heart and a pocketful of patience."
    )

    world.para()
    warn(world, helper, child, place, quest)
    use_shortcut(world, child, tool)

    if place.mystery >= 2:
        world.para()
        reveal(world, helper, child, place, quest)
        complete(world, child, helper, quest, place)
    else:
        world.para()
        child.meters["lost"] += 1
        world.say(
            f"The shortcut only made the trail twist tighter, so they slowed down and listened."
        )
        reveal(world, helper, child, place, quest)
        complete(world, child, helper, quest, place)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        quest=quest,
        tool=tool,
        outcome="found",
        thought_used=child.memes["thought"] >= THRESHOLD,
    )
    return world


PLACES = {
    "valley": Place(
        "valley", "valley", "the valley of humming wind", "the old dirt trail",
        "a stone gate", "the blue mist", 7, 2, tags={"trail", "mystery"},
    ),
    "hill": Place(
        "hill", "hill", "the hill of long grass", "the switchback path",
        "a cedar arch", "the cliff-side gusts", 8, 2, tags={"trail", "mystery"},
    ),
    "cave": Place(
        "cave", "cave", "the cave mouth under the moon", "the echoing path",
        "a lantern nook", "the dark stones", 9, 3, tags={"cave", "mystery"},
    ),
}

QUESTS = {
    "map": Quest("map", "the Map-Bright Quest", "the missing map",
                 "a shiny shortcut", "the patient trail", "home with the map found",
                 "the silver map", tags={"quest", "map"}),
    "river": Quest("river", "the River-Roaring Quest", "the river bell",
                   "a splashy shortcut", "the quiet ford", "home with the bell found",
                   "the river bell", tags={"quest", "river"}),
    "crown": Quest("crown", "the Crown-Searching Quest", "the little crown",
                   "a flashy shortcut", "the careful steps", "home with the crown found",
                   "the little crown", tags={"quest", "crown"}),
}

TOOLS = {
    "whistle": Tool("whistle", "whistle", "shortcut", "makes quick noise", "can scare birds",
                    tags={"shortcut"}),
    "ladder": Tool("ladder", "ladder", "shortcut", "reaches up fast", "can wobble",
                   tags={"shortcut"}),
    "lantern": Tool("lantern", "lantern", "thought", "helps see the clue", "needs careful hands",
                    tags={"thought"}),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "Ivy"]
BOY_NAMES = ["Benny", "Tom", "Eli", "Theo", "Max"]


@dataclass
@dataclass
class StoryParams:
    place: str
    quest: str
    tool: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for qid, quest in QUESTS.items():
            for tid, tool in TOOLS.items():
                if trek_risk(place, quest) and ("shortcut" in tool.tags or "thought" in tool.tags):
                    combos.append((pid, qid, tid))
    return combos


KNOWLEDGE = {
    "quest": [("What is a quest?", "A quest is a search for something important. It can be a long trip with a goal and a brave finish.")],
    "thought": [("What is a thought?", "A thought is an idea in your mind. A good thought can help you solve a problem or choose a safe way.")],
    "map": [("What does a map do?", "A map shows places and paths. It helps people know where to go.")],
    "river": [("What is a river?", "A river is moving water that flows along a path. People cross it carefully.")],
    "cave": [("What is a cave?", "A cave is a dark space inside rock. People often need a light to see inside.")],
    "lantern": [("What is a lantern?", "A lantern is a light that helps you see in the dark. It can make a path look friendly.")],
}
KNOWLEDGE_ORDER = ["quest", "thought", "map", "river", "cave", "lantern"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale quest story for a child that includes the word "thought".',
        f"Tell a grand, child-friendly story where {f['child'].id} and {f['helper'].id} go on {f['quest'].title} through {f['place'].label}, and a good thought helps them finish.",
        f"Write a short tall tale about a quest in {f['place'].label} where a shortcut fails and a thoughtful idea sets things right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, place, quest = f["child"], f["helper"], f["place"], f["quest"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who set out together on a quest. They travel like old-fashioned heroes, but the story stays small enough for a child."),
        ("What did they want to find?",
         f"They wanted {quest.objective}. That was the prize at the end of the quest, and it mattered enough to brave the long road."),
        ("Why did the helper warn the child?",
         f"The helper warned {child.id} because the place was tricky and the shortcut was too hasty. A better thought was needed so they would not get more lost."),
    ]
    if f["thought_used"]:
        qa.append((
            "How did the quest turn around?",
            f"{child.id} had a thought that the clue was along the trail, not up high. That smart idea changed the search from a hurry into a careful follow-the-clue walk."
        ))
    qa.append((
        "How did the story end?",
        f"They found {quest.prize} and finished the quest with happy hearts. The ending image is simple: the prize safe in their hands and the big place quiet again."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["quest"].tags) | set(world.facts["place"].tags) | set(world.facts["tool"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("cave", "map", "lantern", "Mina", "girl", "Uncle Finn", "man"),
    StoryParams("hill", "crown", "whistle", "Eli", "boy", "Aunt Rose", "woman"),
    StoryParams("valley", "river", "ladder", "Nora", "girl", "Grandpa", "man"),
]


def explain_rejection(place: Place, quest: Quest) -> str:
    return (
        f"(No story: {quest.title} in {place.label} does not have enough mystery to make a proper quest turn.)"
    )


ASP_RULES = r"""
quest_turn(P,Q) :- place(P), quest(Q), mystery(P,M), M >= 2.
thought_help(T) :- tool(T), thought_tool(T).
found(P,Q) :- quest_turn(P,Q), smart_step(P,Q).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("mystery", pid, p.mystery))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "thought" in t.tags:
            lines.append(asp.fact("thought_tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # Smoke: clingo twin can run.
    model = asp.one_model(asp_program("#show found/2."))
    _ = asp.atoms(model, "found")
    # Gate parity is trivial here; check same valid combos.
    python_set = set(valid_combos())
    clingo_model = asp.one_model(
        f"{asp_facts()}\n#show quest_turn/2.\nquest_turn(P,Q) :- place(P), quest(Q), mystery(P,M), M >= 2.\n"
    )
    clingo_set = {(p, q, "lantern") for (p, q) in asp.atoms(clingo_model, "quest_turn")}
    if python_set != clingo_set:
        print("MISMATCH in valid-combo parity.")
        return 1
    # Normal generation smoke test.
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: empty story.")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale quest storyworld with thought and a small quest.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["man", "woman"])
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
              and (args.quest is None or c[1] == args.quest)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, tool = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["man", "woman"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["Uncle Finn", "Aunt Rose", "Grandpa", "Grandma"])
    return StoryParams(place, quest, tool, child, child_gender, helper, helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], QUESTS[params.quest], TOOLS[params.tool],
                 params.child, params.child_gender, params.helper, params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show found/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible quest combos:")
        for p, q, t in valid_combos():
            print(f"  {p:8} {q:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.child}: {p.quest} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
