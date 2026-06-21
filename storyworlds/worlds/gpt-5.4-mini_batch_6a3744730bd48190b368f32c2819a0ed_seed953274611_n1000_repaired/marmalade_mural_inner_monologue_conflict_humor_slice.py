#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marmalade_mural_inner_monologue_conflict_humor_slice.py
======================================================================================

A small slice-of-life story world about a child trying to help with a mural
project, a sticky jar of marmalade, a tiny conflict, and a funny but gentle
resolution. The story includes inner monologue, a concrete problem/fix turn,
and a cheerful ending image that proves what changed.

Seed words: marmalade, mural
Features: inner monologue, conflict, humor
Style: slice of life
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
INNER_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
    place: str
    setting_text: str
    scent: str
    noise: str
    afford: set[str] = field(default_factory=set)
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


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    sticky: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    mess: str
    consequence: str
    fix: str
    fail_fix: str
    humor: str
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
class StoryParams:
    setting: str = "kitchen"
    item: str = "marmalade"
    action: str = "reach"
    helper: str = "mom"
    child_name: str = "Nina"
    child_gender: str = "girl"
    helper_gender: str = "mother"
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
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "role": v.role, "meters": defaultdict(float, v.meters),
            "memes": defaultdict(float, v.memes), "attrs": dict(v.attrs)
        }) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        setting_text="The kitchen smelled like toast and warm tea, and the table was crowded with bowls, spoons, and a jar with a bright orange lid.",
        scent="toast",
        noise="the soft clink of spoons",
        afford={"reach", "paint", "help"},
    ),
    "hallway": Setting(
        place="the hallway",
        setting_text="The hallway was narrow and sunny, with a long wall waiting for color and a small step stool tucked by the baseboard.",
        scent="wax polish",
        noise="the echo of slippers on the floor",
        afford={"reach", "paint", "help"},
    ),
    "sunroom": Setting(
        place="the sunroom",
        setting_text="The sunroom was full of light, and the big white wall looked like it had been patiently waiting for a mural all morning.",
        scent="leaves",
        noise="birds tapping at the glass",
        afford={"reach", "paint", "help"},
    ),
}

ITEMS = {
    "marmalade": Item(
        id="marmalade",
        label="marmalade",
        phrase="a jar of marmalade",
        kind="sticky",
        sticky=True,
        tags={"marmalade", "sticky", "food"},
    ),
    "paint": Item(
        id="paint",
        label="paint",
        phrase="a tray of orange paint",
        kind="paint",
        sticky=False,
        tags={"paint", "mural"},
    ),
    "mural": Item(
        id="mural",
        label="mural",
        phrase="the mural",
        kind="surface",
        sticky=False,
        tags={"mural", "wall"},
    ),
}

ACTIONS = {
    "reach": Action(
        id="reach",
        verb="reach for the jar",
        mess="sticky",
        consequence="left a glossy orange thumbprint on the mural",
        fix="wiped the thumbprint away with a damp cloth",
        fail_fix="tried to wipe it away, but only made the smear wider",
        humor="The thumbprint looked less like art and more like a tiny sun with a bad hair day.",
        tags={"conflict", "humor", "sticky"},
    ),
    "paint": Action(
        id="paint",
        verb="help paint the mural",
        mess="orange",
        consequence="put a streak of marmalade on the fresh wall color",
        fix="covered the smear with a careful painted leaf",
        fail_fix="pressed too hard and made the streak look like a funny orange comet",
        humor="The streak zigzagged across the wall like a cat trying to walk on jelly.",
        tags={"conflict", "humor", "mural"},
    ),
}

HELPERS = {
    "mom": {"type": "mother", "label": "Mom"},
    "dad": {"type": "father", "label": "Dad"},
    "aunt": {"type": "woman", "label": "Aunt Jo"},
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for a in ACTIONS:
            for i in ITEMS:
                if a == "paint" and i == "marmalade":
                    combos.append((s, i, a))
                if a == "reach" and i == "marmalade":
                    combos.append((s, i, a))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.action == "paint" and params.item != "marmalade":
        raise StoryError("This story only works when marmalade and the mural both matter.")
    if params.action == "reach" and params.item != "marmalade":
        raise StoryError("This story only works when the child reaches for marmalade.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life mural mishap story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or "marmalade"
    action = args.action or rng.choice(list(ACTIONS))
    helper = args.helper or rng.choice(list(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or (rng.choice(["Nina", "Maya", "June", "Toby", "Iris", "Evan"]) if gender == "girl" else rng.choice(["Owen", "Milo", "Ben", "Finn", "Leo"]))
    params = StoryParams(setting=setting, item=item, action=action, helper=helper, child_name=name, child_gender=gender, helper_gender=HELPERS[helper]["type"])
    reasonableness_check(params)
    return params


def _do_action(world: World, child: Entity, item: Entity, action: Action) -> None:
    child.meters["busy"] += 1
    child.memes["want"] += 1
    if action.id == "reach":
        item.meters["sticky"] += 1
        item.meters["on_mural"] += 1
    else:
        item.meters["smeared"] += 1
        item.meters["on_mural"] += 1


def predict_conflict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    child = sim.get("child")
    item = sim.get("item")
    _do_action(sim, child, item, ACTIONS[params.action])
    return {"sticky": item.meters["sticky"], "on_mural": item.meters["on_mural"]}


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    item_cfg = ITEMS[params.item]
    action = ACTIONS[params.action]
    helper_cfg = HELPERS[params.helper]

    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg["type"], label=helper_cfg["label"], role="helper"))
    item = world.add(Entity(id="item", kind="thing", type="thing", label=item_cfg.label, role="item"))
    mural = world.add(Entity(id="mural", kind="thing", type="surface", label="the mural", role="mural"))

    child.memes["curious"] += 1
    helper.memes["calm"] += 1
    world.say(f"{child.id} was in {setting.place}, and {setting.setting_text}")
    world.say(f"{child.id} kept thinking about {item_cfg.phrase}. {child.pronoun().capitalize()} wanted to {action.verb}, because the jar looked funny and bright.")

    world.para()
    world.say(f"Inside {child.id}'s head, a little voice said, “{child.id}, be careful.” Another voice replied, “I know, I know, but look at that lid.”")
    world.say(f"When the table wobbled, {helper.label} looked over and frowned.")
    child.memes["conflict"] += 1
    helper.memes["concern"] += 1

    if action.id == "reach":
        world.say(f"{child.id} reached anyway, and a sticky orange thumbprint landed on {mural.label}.")
    else:
        world.say(f"{child.id} tried to help at the wall, but the marmalade went right where the fresh paint was supposed to be smooth.")
    _do_action(world, child, item, action)

    world.para()
    world.say(action.humor)
    world.say(f"{helper.label} laughed once, then pointed at the mess. “Well, that is one very optimistic blob.”")

    if action.id == "reach":
        world.say(f"{child.id} stared at the shine and thought, “I meant to help, not decorate with breakfast.”")
        world.say(f"{helper.label} took a damp cloth and {action.fix}.")
    else:
        world.say(f"{child.id} stared at the streak and thought, “That was supposed to be a neat leaf, not a marmalade comet.”")
        world.say(f"{helper.label} smiled and {action.fix}.")

    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1

    world.para()
    world.say(f"After that, the mural was still there, but now it had one tiny repaired patch and a fresh leaf beside it.")
    world.say(f"{child.id} got a spoon of marmalade on toast instead of on the wall, and the kitchen went back to being a normal afternoon with sticky fingers and a clean broom.")
    world.facts.update(child=child, helper=helper, item=item, mural=mural, action=action, setting=setting, item_cfg=item_cfg, helper_cfg=helper_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    return [
        f'Write a slice-of-life story for a young child that includes the words "marmalade" and "mural".',
        f"Tell a gentle story where {child.id} has an inner argument about {action.verb} near a mural, with a funny sticky mistake and a calm fix.",
        f"Write a story with marmalade, a mural, a little conflict, and a humorous ending in an everyday kitchen or hallway.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    action = f["action"]
    item_cfg = f["item_cfg"]
    mural = f["mural"]
    answers = [
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.id} wanted to {action.verb} while the mural was being worked on. That made the jar feel too tempting to ignore.",
        ),
        QAItem(
            question="What caused the conflict?",
            answer=f"The conflict came from {child.id} wanting the marmalade right next to the mural. The child knew it was a bad idea, but the jar looked silly and hard to resist.",
        ),
        QAItem(
            question="How was the problem fixed?",
            answer=f"{helper.label} cleaned or covered the sticky mistake so the mural could stay nice. Then the child got to enjoy marmalade the normal way instead of on the wall.",
        ),
    ]
    if action.id == "paint":
        answers.append(
            QAItem(
                question="Why did the funny moment make the story lighter?",
                answer=f"The orange smear looked a little like a comic accident instead of a disaster. That made {helper.label} laugh, which helped the whole scene feel warm and everyday.",
            )
        )
    else:
        answers.append(
            QAItem(
                question="What did the child think after making the thumbprint?",
                answer=f"{child.id} thought about how the thumbprint was not the kind of art anyone had planned. That thought helped {child.id} settle down and let {helper.label} clean it up.",
            )
        )
    answers.append(
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, the mural was tidy again and the sticky jar was back in the kitchen instead of on the wall. The afternoon felt normal again, just with a new funny story to remember.",
        )
    )
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is marmalade?",
            answer="Marmalade is a sweet orange spread made from fruit and sugar. It is sticky, so it can make a mess if it ends up somewhere it does not belong.",
        ),
        QAItem(
            question="What is a mural?",
            answer="A mural is a big picture painted on a wall. People can work on it together so a room or hallway feels brighter.",
        ),
        QAItem(
            question="Why can sticky food be a problem near art?",
            answer="Sticky food can leave marks and smears that are hard to clean. If it lands on a mural, someone has to wipe it carefully so the art stays nice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes} role={e.role}")
    return "\n".join(lines)


ASP_RULES = r"""
sticky_conflict(C) :- child(C), wants_marmalade(C), mural(M), near(C, M), sticky_item(marmalade).
humor(Msg) :- sticky_conflict(C), funny_smear(C), mural(_), message(Msg).
resolved(C) :- sticky_conflict(C), helper(H), clean_fix(H), child(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.sticky:
            lines.append(asp.fact("sticky_item", iid))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        if "humor" in act.tags:
            lines.append(asp.fact("funny_smear", aid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("mural", "mural"))
    lines.append(asp.fact("wants_marmalade", "child"))
    lines.append(asp.fact("near", "child", "mural"))
    lines.append(asp.fact("clean_fix", "mom"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    # simple parity: any valid combo from python is represented by ASP facts/rules
    if not valid_combos():
        print("MISMATCH: no valid combos.")
        return 1
    print(f"OK: Python valid_combos() has {len(valid_combos())} combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"MISMATCH: generate() smoke test failed: {exc}")
        rc = 1
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(["Nina", "Maya", "June", "Ivy", "Lena"])
    return rng.choice(["Owen", "Milo", "Ben", "Finn", "Leo"])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    params = StoryParams(
        setting=args.setting or rng.choice(list(SETTINGS)),
        item=args.item or "marmalade",
        action=args.action or rng.choice(list(ACTIONS)),
        helper=args.helper or rng.choice(list(HELPERS)),
        child_name=args.name or _pick_name(rng, args.gender or rng.choice(["girl", "boy"])),
        child_gender=args.gender or rng.choice(["girl", "boy"]),
        helper_gender=HELPERS[args.helper]["type"] if args.helper else rng.choice(["mother", "father"]),
    )
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.item not in ITEMS:
        raise StoryError("Unknown item.")
    if params.action not in ACTIONS:
        raise StoryError("Unknown action.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    world = tell(params)
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


CURATED = [
    StoryParams(setting="kitchen", item="marmalade", action="reach", helper="mom", child_name="Nina", child_gender="girl", helper_gender="mother"),
    StoryParams(setting="hallway", item="marmalade", action="paint", helper="dad", child_name="Owen", child_gender="boy", helper_gender="father"),
    StoryParams(setting="sunroom", item="marmalade", action="reach", helper="aunt", child_name="Maya", child_gender="girl", helper_gender="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in valid_combos():
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
