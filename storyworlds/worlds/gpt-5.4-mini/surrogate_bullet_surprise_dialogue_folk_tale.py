#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/surrogate_bullet_surprise_dialogue_folk_tale.py
================================================================================

A standalone storyworld for a small folk-tale domain about a child, a surprise,
and a dialogue-driven choice between a real bullet and a safer surrogate.

Seed premise:
- Words: surrogate, bullet
- Features: Surprise, Dialogue
- Style: Folk Tale

The world is a tiny village folk tale: a child finds a bullet in a keepsake box
and wants to use it in a sling to help with crows, but an elder offers a
surrogate bullet made of clay instead. A surprise in the story reveals the real
value of the day: the bullet is not for harm, but for unlocking a hidden bell
that calls the village together. The story stays child-facing and concrete.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    detail: str
    season: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    safe: bool = False
    loud: bool = False
    surrogate_for: str = ""
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    phrase: str
    effect: str
    danger: int
    power: int
    safe_alt: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["alarm"] < THRESHOLD:
            continue
        sig = ("alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "village" in world.entities:
            world.get("village").meters["buzz"] += 1
        out.append("__alarm__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["relief"] < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["peace"] += 1
        out.append("__peace__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm), Rule("relief", "social", _r_relief)]


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


@dataclass
@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    elder: str
    elder_gender: str
    tool: str
    item: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "village_green": Setting("village_green", "the village green",
                             "The green sat beside a round stone well and a row of apple trees.",
                             "spring", tags={"village", "green"}),
    "orchard": Setting("orchard", "the apple orchard",
                       "The orchard held old trees, a mossy wall, and a warm bread smell.",
                       "autumn", tags={"village", "orchard"}),
}

ITEMS = {
    "bullet": Item("bullet", "bullet", "a small bullet", "metal", safe=False, loud=False,
                   surrogate_for="", tags={"bullet", "metal"}),
    "surrogate_bullet": Item("surrogate_bullet", "surrogate bullet", "a clay surrogate bullet",
                             "clay", safe=True, surrogate_for="bullet", tags={"surrogate", "clay"}),
    "bell_key": Item("bell_key", "bell key", "a brass bell key", "key", safe=True,
                     tags={"key", "bell"}),
    "charm": Item("charm", "charm", "a little charm", "token", safe=True,
                  tags={"charm", "token"}),
}

TOOLS = {
    "sling": Tool("sling", "sling", "a sling", "casts", danger=3, power=2,
                  safe_alt="surrogate bullet", tags={"sling", "bullet"}),
    "bell_rope": Tool("bell_rope", "bell rope", "the bell rope", "rings", danger=0, power=0,
                      safe_alt="", tags={"bell"}),
}

NAMES_GIRL = ["Mira", "Lina", "Bess", "Nora", "Elin", "Wren"]
NAMES_BOY = ["Tomas", "Jory", "Pavel", "Oren", "Bram", "Kian"]
ELDERS = ["Grandma", "Grandpa"]
TRAITS = ["curious", "careful", "dreamy", "bold", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for tid, tool in TOOLS.items():
            for iid, item in ITEMS.items():
                if tool.id == "sling" and item.id in {"bullet", "surrogate_bullet"}:
                    combos.append((sid, tid, iid))
    return combos


def reasonableness_gate(tool: Tool, item: Item) -> bool:
    return tool.id == "sling" and item.id in {"bullet", "surrogate_bullet"}


def predict(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["alarm"] += 1
    propagate(sim, narrate=False)
    return {"buzz": sim.get("village").meters["buzz"]}


def use_surrogate(world: World, child: Entity, elder: Entity, tool: Tool, item: Item) -> None:
    child.memes["hope"] += 1
    world.say(
        f"{child.id} lifted the {tool.label} and whispered, \"What if I use the {item.label}?"
    )
    world.say(
        f'{elder.label_word} smiled. "That would be a {item.label_word if hasattr(item, "label_word") else item.label} '
        f'only in name. Here, take this surrogate bullet instead."'
    )


def surprise(world: World, child: Entity, elder: Entity, tool: Tool, item: Item) -> None:
    world.say(
        f"The child turned the little {item.label} over and over, expecting a simple game."
    )
    world.say(
        f"Then the {tool.label} clicked against an old stone plaque, and a hidden slot opened in the well wall."
    )
    world.say(
        "Inside was a brass bell key, waiting all these years for a careful hand."
    )


def dialogue_turn(world: World, child: Entity, elder: Entity, item: Item) -> None:
    world.say(
        f'"It is only a surrogate," {elder.id} said. "It can help you practice without harm."'
    )
    world.say(
        f'"And the bullet?" {child.id} asked.'
    )
    world.say(
        f'"That one belongs in a story, not a sling," {elder.id} said gently. "Come, let us see what the hill is hiding."'
    )


def ending(world: World, child: Entity, elder: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["wonder"] += 1
    elder.memes["warmth"] += 1
    world.say(
        f"At last the bell key turned, and the village bell sang across the green."
    )
    world.say(
        f"Everyone came smiling to hear the news, and {child.id} went home with the surrogate bullet in {child.pronoun('possessive')} pocket and the real surprise in {child.pronoun('possessive')} heart."
    )


def tell(setting: Setting, child_name: str, child_gender: str, elder_name: str, elder_gender: str,
         tool: Tool, item: Item, trait: str = "curious") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", traits=[trait]))
    elder = world.add(Entity(id=elder_name, kind="character", type=elder_gender,
                             role="elder", traits=["wise"]))
    village = world.add(Entity(id="village", kind="thing", type="place", label=setting.place))
    bell = world.add(Entity(id="bell", kind="thing", type="thing", label="the village bell"))
    world.facts["setting"] = setting
    world.facts["tool"] = tool
    world.facts["item"] = item

    world.say(
        f"Long ago, in {setting.place}, {child.id} found {item.phrase} in an old box by the well."
    )
    world.say(
        f'{child.id} said, "I could use it with my {tool.label} and frighten the crows."'
    )
    dialogue_turn(world, child, elder, item)
    world.para()
    use_surrogate(world, child, elder, tool, item)
    surprise(world, child, elder, tool, item)
    world.para()
    ending(world, child, elder)

    world.facts.update(
        child=child, elder=elder, village=village, bell=bell,
        resolved=True, surprise=True, dialogue=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item"]
    return [
        f'Write a folk-tale style story for a young child that includes the words "surrogate" and "{item.label}".',
        f'Tell a dialogue-heavy surprise story about {child.id} and {elder.id} in a village, where a surrogate is offered instead of a {item.label}.',
        f'Write a gentle folk tale with a hidden surprise and short dialogue, ending with a village bell ringing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item"]
    return [
        QAItem(
            question=f"Who found the bullet?",
            answer=f"{child.id} found the bullet near the well, and {elder.id} talked with them about it."
        ),
        QAItem(
            question=f"What did {elder.id} offer instead?",
            answer=f"{elder.id} offered a surrogate bullet made of clay. It was a safer practice piece, not the real bullet."
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer="The surprise was that the old stone by the well opened and revealed a hidden bell key. The child expected an ordinary game, but the village had been waiting for that key."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a surrogate?",
            answer="A surrogate is something that stands in for another thing. In stories, it can be a safe substitute when the real thing is not the right choice."
        ),
        QAItem(
            question="What is a bullet?",
            answer="A bullet is a small hard piece used with a gun, and it is not a toy. Children should not play with real bullets."
        ),
        QAItem(
            question="What does a bell do?",
            answer="A bell makes a ringing sound when it is struck or when its rope or key is used. People can hear it from far away."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("\n== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, T, I) :- setting(S), tool(T), item(I), sling(T), bullet_like(I).
bullet_like(bullet).
bullet_like(surrogate_bullet).

surprise_story(S, T, I) :- valid(S, T, I), bullet_like(I).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if tid == "sling":
            lines.append(asp.fact("sling", tid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
        if iid in {"bullet", "surrogate_bullet"}:
            lines.append(asp.fact("bullet_like", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested normal generate path.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld with a surrogate bullet and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man"])
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.tool and args.item and not reasonableness_gate(TOOLS[args.tool], ITEMS[args.item]):
        raise StoryError("No story: that tool and item do not make a good folk-tale problem.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.tool is None or c[1] == args.tool)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, tool, item = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    elder = args.elder or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, child, child_gender, elder, elder_gender, tool, item, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.child, params.child_gender,
                 params.elder, params.elder_gender, TOOLS[params.tool], ITEMS[params.item],
                 params.trait)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams("village_green", "Mira", "girl", "Grandma", "woman", "sling", "bullet", "curious"),
            StoryParams("orchard", "Bram", "boy", "Grandpa", "man", "sling", "surrogate_bullet", "thoughtful"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
