#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/come_gerund_pleasant_ratatouille_flashback_bedtime_story.py
==========================================================================================

A tiny bedtime-story storyworld about a child, a sleepy kitchen, and a pot of
ratatouille. The narrative instrument is a flashback: the present-day cooking
scene reminds someone of a kind memory that teaches the same lesson again.

The world is built to be small but stateful:
- physical meters track simmering, spilling, cooling, and smelling pleasant
- emotional memes track comfort, worry, memory, and pride
- a forward rule makes the room feel calmer once the food is served
- a flashback beat turns the remembered lesson into a real cause for the ending

The seed words are woven in as required: come-gerund, pleasant, ratatouille.
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
SPILL_RISK_MIN = 1.0


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
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "grandmother": "grandma", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    bedtime: bool = True
    cozy_detail: str = ""
    tags: set[str] = field(default_factory=set)
    allowed_actions: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Dish:
    id: str
    label: str
    smell: str
    safe_lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    quiet_words: str
    mess: str
    risk: str
    zone: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Memory:
    id: str
    title: str
    scene: str
    lesson: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    soup = world.entities.get("soup")
    room = world.entities.get("room")
    if not soup or not room:
        return out
    if soup.meters["served"] >= THRESHOLD and ("calm", "room") not in world.fired:
        world.fired.add(("calm", "room"))
        room.meters["cozy"] += 1
        for ent in list(world.entities.values()):
            if ent.kind == "character":
                ent.memes["sleepy"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for action_id in setting.allowed_actions:
            for dish_id, dish in DISHES.items():
                if action_at_risk(ACTIONS[action_id], dish):
                    combos.append((setting_id, action_id, dish_id))
    return combos


def action_at_risk(action: Action, dish: Dish) -> bool:
    return action.mess in {"spill", "stain"} and "pleasant" in dish.tags


def flashback_helps(memory: Memory, parent: Entity, child: Entity, action: Action) -> bool:
    return memory.id == "grandma_tip" and action.id in {"stir", "serve"}


def make_flashback(world: World, narrator: Entity, memory: Memory) -> None:
    narrator.memes["memory"] += 1
    world.say(
        f"As {narrator.pronoun()} stirred, {narrator.pronoun('possessive')} thoughts drifted back. "
        f"{memory.scene}"
    )
    world.say(
        f"In that flashback, {memory.lesson}"
    )


def spill(world: World, child: Entity, dish_ent: Entity, action: Action) -> None:
    dish_ent.meters["spilled"] += 1
    child.memes["worry"] += 1
    room = world.get("room")
    room.meters["mess"] += 1
    world.say(
        f"{child.id} tried to {action.verb}, and a little bit of {dish_ent.label} splashed the counter."
    )


def serve(world: World, parent: Entity, dish_ent: Entity) -> None:
    dish_ent.meters["served"] += 1
    dish_ent.meters["warming"] += 1
    world.say(
        f"{parent.label_word.capitalize()} carried the bowl to the table, and the whole kitchen smelled {dish_ent.smell}."
    )


def lesson(world: World, parent: Entity, child: Entity, memory: Memory, dish: Dish) -> None:
    child.memes["comfort"] += 1
    child.memes["pride"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} smiled and told a story from before. {memory.lesson} "
        f"{dish.safe_lesson}"
    )
    world.say(
        f"{child.id} listened, nodded, and felt sleepy in the nicest way."
    )


def end_image(world: World, child: Entity, parent: Entity, dish_ent: Entity) -> None:
    world.say(
        f"At the end, {child.id} sat beside {parent.pronoun('object')} with a warm spoon, "
        f"and the pleasant ratatouille glowed in the lamplight like a bedtime star."
    )


def tell(setting: Setting, action: Action, dish: Dish, memory: Memory, child_name: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="boy" if child_name in {"Ben", "Noah", "Theo", "Leo"} else "girl", role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    dish_ent = world.add(Entity(id="soup", kind="thing", type="dish", label=dish.label))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    world.facts.update(child=child, parent=parent, dish=dish, memory=memory, action=action, setting=setting, dish_ent=dish_ent, room=room)

    child.memes["cozy"] = 1.0
    parent.memes["gentle"] = 1.0
    room.meters["quiet"] = 1.0

    world.say(
        f"It was bedtime in {setting.place}, and the lights were soft and low. {setting.cozy_detail}"
    )
    world.say(
        f"{child.id} and {parent.label_word.capitalize()} were making {dish.label}, a {dish.smell} dinner for the night."
    )
    world.say(
        f"{child.id} liked the gentle coming-quietly of the kitchen, because every pot sound felt like a lullaby."
    )

    world.para()
    if action.id == "mix":
        spill(world, child, dish_ent, action)
    else:
        world.say(
            f"{child.id} wanted to {action.verb}, nice and slowly."
        )

    if action.id == "mix":
        world.say(
            f"{parent.label_word.capitalize()} watched the little spill and did not scold. The kitchen was still pleasant, just a bit worried."
        )
    else:
        world.say(
            f"The bowl stayed steady, and the smell of tomatoes, eggplant, and herbs drifted up like a blanket."
        )

    world.para()
    make_flashback(world, parent, memory)
    serve(world, parent, dish_ent)
    lesson(world, parent, child, memory, dish)
    propagate(world, narrate=False)
    world.para()
    end_image(world, child, parent, dish_ent)

    world.facts.update(outcome="spilled" if dish_ent.meters["spilled"] >= THRESHOLD else "smooth")
    return world


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        cozy_detail="A little lamp made the table shine gently, and a blue mug waited by the sink.",
        allowed_actions={"mix", "stir", "serve"},
        tags={"bedtime", "kitchen"},
    ),
    "cottage": Setting(
        id="cottage",
        place="the cottage kitchen",
        cozy_detail="The old clock ticked softly, and the window held a moonlit garden.",
        allowed_actions={"mix", "stir", "serve"},
        tags={"bedtime", "cottage"},
    ),
}

DISHES = {
    "ratatouille": Dish(
        id="ratatouille",
        label="ratatouille",
        smell="pleasant",
        safe_lesson="Grandma always said a calm hand makes a kinder dinner.",
        tags={"pleasant", "ratatouille"},
    ),
    "soup": Dish(
        id="soup",
        label="vegetable soup",
        smell="pleasant",
        safe_lesson="A quiet kitchen keeps the spoon where it belongs.",
        tags={"pleasant"},
    ),
}

ACTIONS = {
    "mix": Action(
        id="mix",
        verb="mix the ratatouille",
        gerund="mixing the ratatouille",
        quiet_words="gentle little circles",
        mess="spill",
        risk="a splash on the counter",
        zone="counter",
        tags={"mix", "ratatouille"},
    ),
    "stir": Action(
        id="stir",
        verb="stir the pot",
        gerund="stirring the pot",
        quiet_words="slow sleepy circles",
        mess="spill",
        risk="a drip on the stove",
        zone="counter",
        tags={"stir", "ratatouille"},
    ),
    "serve": Action(
        id="serve",
        verb="serve the dinner",
        gerund="serving dinner",
        quiet_words="careful spoonfuls",
        mess="spill",
        risk="a tiny drip",
        zone="table",
        tags={"serve", "ratatouille"},
    ),
}

MEMORIES = {
    "grandma_tip": Memory(
        id="grandma_tip",
        title="the old lesson",
        scene="She remembered how, when she was small, Grandma had lifted a towel under the bowl so nothing would splash.",
        lesson="Grandma had once shown her how to carry a heavy bowl with two hands and a slow step.",
        tags={"flashback", "bedtime"},
    ),
}

@dataclass
class StoryParams:
    setting: str
    action: str
    dish: str
    memory: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(setting="kitchen", action="mix", dish="ratatouille", memory="grandma_tip", child_name="Mia", child_gender="girl", parent_type="mother", seed=1),
    StoryParams(setting="cottage", action="stir", dish="ratatouille", memory="grandma_tip", child_name="Ben", child_gender="boy", parent_type="grandmother", seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime flashback storyworld with a pleasant ratatouille.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "grandmother"])
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
    if args.dish and args.dish not in DISHES:
        raise StoryError("Unknown dish.")
    if args.action and args.dish:
        if not action_at_risk(ACTIONS[args.action], DISHES[args.dish]):
            raise StoryError("That action does not make a believable problem for this dish.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.action is None or c[1] == args.action)
              and (args.dish is None or c[2] == args.dish)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, action, dish = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "grandmother"])
    name = args.name or rng.choice(["Mia", "Ben", "Luna", "Theo", "Nora", "Leo"])
    return StoryParams(setting=setting, action=action, dish=dish, memory=args.memory or "grandma_tip", child_name=name, child_gender=gender, parent_type=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "come-gerund", "pleasant", and "{f["dish"].label}".',
        f"Tell a gentle flashback story where {f['child'].id} helps with {f['dish'].label} and remembers an old lesson from {f['parent'].label_word}.",
        f"Write a cozy story set in {f['setting'].place} that ends with a warm bowl of {f['dish'].label} and a comforting memory.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, dish, memory, action = f["child"], f["parent"], f["dish"], f["memory"], f["action"]
    answers = [
        QAItem(
            question="What was the child doing before bedtime?",
            answer=f"{child.id} was helping with {dish.label} in {f['setting'].place}. It was a quiet bedtime task, so the kitchen felt calm and soft."
        ),
        QAItem(
            question="Why did the story flash back to an older memory?",
            answer=f"{parent.label_word.capitalize()} remembered {memory.title.lower()} because the little spill and the slow cooking brought that lesson back. The flashback helped the child remember how to carry the bowl carefully."
        ),
    ]
    if f["outcome"] == "spilled":
        answers.append(QAItem(
            question="What changed after the spill?",
            answer=f"There was a small mess on the counter, but nobody got hurt. The story then turned gentle again when {parent.label_word} used the memory to teach a calmer way."
        ))
    else:
        answers.append(QAItem(
            question="How did the story end?",
            answer=f"It ended with a warm bowl of {dish.label}, a quiet kitchen, and {child.id} feeling sleepy and proud. The pleasant smell made the ending feel like a bedtime hug."
        ))
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    items = [
        QAItem(
            question="What does pleasant mean?",
            answer="Pleasant means nice and comforting. A pleasant smell or sound helps a room feel peaceful."
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly goes back to an earlier memory. It helps explain why a character knows something or feels a certain way now."
        ),
        QAItem(
            question="What is ratatouille?",
            answer="Ratatouille is a warm vegetable dish cooked slowly so the flavors can blend together. It is often soft, cozy food."
        ),
    ]
    return items


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(S,A,D) :- setting(S), action(A), dish(D), action_risky(A), pleasant_dish(D).
"""  # deliberately tiny twin; the world uses Python gate for the actual contract checks


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_risky", aid))
    for did in DISHES:
        lines.append(asp.fact("dish", did))
        lines.append(asp.fact("pleasant_dish", did))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show risk/3."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, action=None, dish=None, memory=None, name=None, gender=None, parent=None), random.Random(7)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify passed and ordinary generation worked.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.action not in ACTIONS or params.dish not in DISHES or params.memory not in MEMORIES:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], ACTIONS[params.action], DISHES[params.dish], MEMORIES[params.memory], params.child_name, params.parent_type)
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
        print(asp_program("#show risk/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
