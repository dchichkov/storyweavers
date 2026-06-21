#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/suede_prick_harpoon_suspense_heartwarming.py
=============================================================================

A small storyworld about a quiet seaside repair shed, a tense little rescue, and
a warm ending. The seed words are woven into the domain: suede, prick, harpoon.
The story stays child-facing, suspenseful, and heartwarming.

The premise:
- A child helps an older helper sort a seaside shed.
- A sharp prickly problem creates suspense.
- An old harpoon becomes part of a careful rescue.
- A suede glove matters because it protects a hand at the right moment.

The world is intentionally compact: fewer variants, all state-driven.
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
SUSPENSE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class StoryParams:
    setting: str
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    suede_item: str
    prick_item: str
    harpoon_item: str
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


@dataclass
class SettingCfg:
    id: str
    place: str
    detail: str
    weather: str
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


@dataclass
class SuedeCfg:
    id: str
    label: str
    phrase: str
    use: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class PrickCfg:
    id: str
    label: str
    phrase: str
    danger: str
    small: bool = True
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class HarpoonCfg:
    id: str
    label: str
    phrase: str
    purpose: str
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["worry"] >= THRESHOLD and ("suspense",) not in world.fired:
        world.fired.add(("suspense",))
        world.get("scene").meters["tension"] += 1
        out.append("__tension__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("helper").memes["comfort"] >= THRESHOLD and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        world.get("scene").meters["warmth"] += 1
        out.append("__warmth__")
    return out


CAUSAL_RULES = [Rule("suspense", _r_suspense), Rule("calm", _r_calm)]


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


def predict_hazard(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["worry"] += 1
    propagate(sim, narrate=False)
    return {
        "tension": sim.get("scene").meters["tension"],
        "warmth": sim.get("scene").meters["warmth"],
    }


def start(world: World, child: Entity, helper: Entity, setting: SettingCfg) -> None:
    world.say(
        f"On a gray morning at {setting.place}, {child.id} helped {helper.id} sort old things in the little shed. "
        f"{setting.detail}"
    )
    world.say(
        f"{child.id} found a soft suede {world.facts['suede'].label} and held it up. "
        f"It felt smooth and safe in {child.pronoun('possessive')} hand."
    )


def prick(world: World, child: Entity, prick_cfg: PrickCfg) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Then {child.id} saw {prick_cfg.phrase}. One tiny prick could turn the work into trouble, and that made the room feel very still."
    )


def notice_harpoon(world: World, helper: Entity, harpoon_cfg: HarpoonCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Near the back wall, {helper.id} lifted an old {harpoon_cfg.phrase}. "
        f"{helper.id} said it was not for playing, only for a careful job that needed reach."
    )


def explain_plan(world: World, child: Entity, helper: Entity, setting: SettingCfg) -> None:
    pred = predict_hazard(world)
    world.facts["predicted_tension"] = pred["tension"]
    world.say(
        f'{helper.id} looked at {child.id} and the sharp little {world.facts["prick"].label}. '
        f'"If we rush, we could get hurt," {helper.id} said softly. "Let’s slow down and do this the safe way."'
    )
    if pred["tension"] >= THRESHOLD:
        world.say(
            f"{child.id} swallowed hard. The quiet warning was enough to make the suspense real."
        )


def choose_glove(world: World, child: Entity, suede_cfg: SuedeCfg) -> None:
    child.memes["courage"] += 1
    world.say(
        f"{child.id} pulled on the suede {suede_cfg.label}. "
        f"It fit snugly, and {child.id} felt braver knowing {suede_cfg.use}."
    )


def rescue(world: World, child: Entity, helper: Entity, harpoon_cfg: HarpoonCfg, prick_cfg: PrickCfg) -> None:
    helper.memes["comfort"] += 1
    world.get("scene").meters["tension"] = 0.0
    world.get("scene").meters["warmth"] += 1
    world.say(
        f"Together they used the long reach of the {harpoon_cfg.label} to hook the snagged rope and pull it free. "
        f"The prickly tangle stopped threatening their hands."
    )
    world.say(
        f"When the last {prick_cfg.label} rolled away, {child.id} smiled up at {helper.id}, and the whole shed felt calmer."
    )


def ending(world: World, child: Entity, helper: Entity, suede_cfg: SuedeCfg, setting: SettingCfg) -> None:
    child.memes["relief"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By the end, the suede glove was dusty but still good, the old harpoon was back on its hook, and {child.id} helped close the shed door. "
        f"At {setting.place}, the morning was still gray, but inside the little place there was a warm, safe feeling."
    )
    world.say(
        f"{child.id} leaned against {helper.id} and laughed quietly, glad the scare had turned into a good deed."
    )


SETTINGS = {
    "harbor": SettingCfg(
        id="harbor",
        place="the harbor shed",
        detail="Outside, the tide tapped the dock, and gulls cried over the water.",
        weather="gray",
    ),
    "beach": SettingCfg(
        id="beach",
        place="the beach hut",
        detail="Outside, the waves kept whispering and the sand smelled like salt.",
        weather="breezy",
    ),
    "pier": SettingCfg(
        id="pier",
        place="the pier workshop",
        detail="Outside, the boards creaked gently under the wind off the sea.",
        weather="misty",
    ),
}

SUEDE = {
    "glove": SuedeCfg(
        id="glove",
        label="glove",
        phrase="a suede glove",
        use="it could keep a hand safe from a prick",
    ),
    "pouch": SuedeCfg(
        id="pouch",
        label="pouch",
        phrase="a suede pouch",
        use="it was soft enough to carry something sharp without scraping skin",
    ),
}

PRICKS = {
    "urchin": PrickCfg(
        id="urchin",
        label="sea urchin",
        phrase="a tiny sea urchin shell",
        danger="its prickly spines could poke skin",
    ),
    "thorn": PrickCfg(
        id="thorn",
        label="thorn",
        phrase="a thorny bit of driftwood",
        danger="its points could prick a finger",
    ),
}

HARPOONS = {
    "harpoon": HarpoonCfg(
        id="harpoon",
        label="harpoon",
        phrase="harpoon",
        purpose="to reach a snag far away",
    ),
    "boat_hook": HarpoonCfg(
        id="boat_hook",
        label="boat hook",
        phrase="boat hook",
        purpose="to pull a rope from high up",
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lena", "Owen", "Ava", "Theo", "Nora", "Eli"]
HELPER_NAMES = ["Grandpa", "Grandma", "Aunt June", "Uncle Ben", "Mr. Kai", "Mrs. Sol"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PRICKS:
            for h in HARPOONS:
                combos.append((s, p, h))
    return combos


def story_skeleton_params() -> list[StoryParams]:
    return [
        StoryParams(setting="harbor", child="Mia", child_gender="girl", helper="Grandpa", helper_gender="man",
                    suede_item="glove", prick_item="urchin", harpoon_item="harpoon"),
        StoryParams(setting="beach", child="Noah", child_gender="boy", helper="Mrs. Sol", helper_gender="woman",
                    suede_item="pouch", prick_item="thorn", harpoon_item="boat_hook"),
        StoryParams(setting="pier", child="Lena", child_gender="girl", helper="Aunt June", helper_gender="woman",
                    suede_item="glove", prick_item="urchin", harpoon_item="boat_hook"),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming suspense story for a child that includes the words "{f["suede"].label}", "{f["prick"].label}", and "{f["harpoon"].label}".',
        f"Tell a gentle seaside rescue story where {f['child'].id} uses a suede item to stay safe from a prickly problem, and an old harpoon helps fix it.",
        f"Write a short story with a tense middle and a warm ending about a helper, a child, and something sharp near the water.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    suede = f["suede"]
    prick = f["prick"]
    harpoon = f["harpoon"]
    return [
        QAItem(
            question="What made the story feel tense?",
            answer=f"The tense part came when {child.id} noticed the prickly {prick.label}. It felt important because a rushed move could have caused a painful poke.",
        ),
        QAItem(
            question="Why did the suede item matter?",
            answer=f"The suede {suede.label} mattered because it protected {child.id}'s hand. That meant the child could help without getting a prick.",
        ),
        QAItem(
            question="How did the harpoon help?",
            answer=f"The harpoon gave {helper.id} a long reach for the rescue. It let them pull the snag free without putting their hands too close to the sharp part.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended warmly, with the danger gone and everyone calm again. {child.id} and {helper.id} finished the task together and felt proud of the safe choice they made.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What is suede?",
            answer="Suede is a soft kind of leather. It feels smooth to touch and is often used for gloves or small pouches.",
        ),
        QAItem(
            question="Why can a prickly thing be dangerous?",
            answer=f"A prickly thing can poke skin and hurt. If you are careful and use the right tool, you can stay safe around it.",
        ),
        QAItem(
            question="What is a harpoon used for?",
            answer=f"A harpoon is a tool with a long reach. In this storyworld it helps {f['helper'].id} reach something snagged without leaning in too close.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
suspense :- worry(child), tension(scene), tension_min(M), M =< 1.
warmth :- comfort(helper), warmth(scene).
valid(S,P,H) :- setting(S), prick(P), harpoon(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for p in SUEDE:
        lines.append(asp.fact("suede", p))
    for p in PRICKS:
        lines.append(asp.fact("prick", p))
    for h in HARPOONS:
        lines.append(asp.fact("harpoon", h))
    lines.append(asp.fact("tension_min", int(SUSPENSE_MIN)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    rc = 0
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate.")
        print("python:", sorted(python_set - clingo_set))
        print("clingo:", sorted(clingo_set - python_set))
    try:
        sample = generate(story_skeleton_params()[0])
        _ = sample.story
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"FAILED: generate smoke test: {exc}")
    return rc


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.suede_item not in SUEDE:
        raise StoryError("Unknown suede item.")
    if params.prick_item not in PRICKS:
        raise StoryError("Unknown prick item.")
    if params.harpoon_item not in HARPOONS:
        raise StoryError("Unknown harpoon item.")

    world = World()
    setting = SETTINGS[params.setting]
    suede = SUEDE[params.suede_item]
    prick_cfg = PRICKS[params.prick_item]
    harpoon_cfg = HARPOONS[params.harpoon_item]

    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    scene = world.add(Entity(id="scene", type="scene", label=setting.place))
    world.facts.update(child=child, helper=helper, suede=suede, prick=prick_cfg, harpoon=harpoon_cfg)

    start(world, child, helper, setting)
    world.para()
    prick(world, child, prick_cfg)
    notice_harpoon(world, helper, harpoon_cfg)
    explain_plan(world, child, helper, setting)
    choose_glove(world, child, suede)
    world.para()
    rescue(world, child, helper, harpoon_cfg, prick_cfg)
    ending(world, child, helper, suede, setting)
    world.facts["scene"] = scene
    return world


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def explain_rejection(params: StoryParams) -> str:
    return "(No story: invalid parameter combination.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming suspense storyworld with suede, prick, and harpoon.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["woman", "man"])
    ap.add_argument("--suede-item", choices=SUEDE)
    ap.add_argument("--prick-item", choices=PRICKS)
    ap.add_argument("--harpoon-item", choices=HARPOONS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    suede_item = args.suede_item or rng.choice(list(SUEDE))
    prick_item = args.prick_item or rng.choice(list(PRICKS))
    harpoon_item = args.harpoon_item or rng.choice(list(HARPOONS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(CHILD_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting,
        child=child,
        child_gender=child_gender,
        helper=helper,
        helper_gender=helper_gender,
        suede_item=suede_item,
        prick_item=prick_item,
        harpoon_item=harpoon_item,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except KeyError as exc:
        raise StoryError(str(exc)) from exc
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, p, h in combos:
            print(f"  {s:8} {p:8} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in story_skeleton_params()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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


if __name__ == "__main__":
    main()
