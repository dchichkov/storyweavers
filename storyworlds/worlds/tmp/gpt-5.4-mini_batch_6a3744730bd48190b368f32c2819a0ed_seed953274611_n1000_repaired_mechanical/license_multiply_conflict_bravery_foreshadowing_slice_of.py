#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/license_multiply_conflict_bravery_foreshadowing_slice_of.py
============================================================================================

A small slice-of-life storyworld about a child who wants to use a copy machine
to multiply hand-drawn flyers, but needs a grown-up license card first.

The world is intentionally tiny and grounded:
- one child, one helper, one adult
- one machine that can make many copies
- one permission rule about a license card
- a simple conflict / bravery / foreshadowing beat
- a safe resolution that ends with an everyday, concrete image

It follows the Storyweavers contract:
- self-contained stdlib script
- eager results import
- lazy ASP import inside ASP helpers
- StoryParams / build_parser / resolve_params / generate / emit / main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class CopySetting:
    id: str
    place: str
    counter: str
    machine: str
    noise: str
    detail: str
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
class LicenseItem:
    id: str
    label: str
    phrase: str
    where: str
    required: bool = True
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
class GoalItem:
    id: str
    label: str
    phrase: str
    plural: bool = False
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
class Response:
    id: str
    sense: int
    text: str
    fail: str
    qa_text: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    c = world.get("child")
    if c.memes["want"] >= THRESHOLD and c.memes["warned"] >= THRESHOLD:
        sig = ("tension",)
        if sig not in world.fired:
            world.fired.add(sig)
            c.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [Rule("tension", _r_tension)]


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


def predict_problem(world: World, goal: GoalItem) -> dict:
    sim = world.copy()
    _do_attempt(sim, narrate=False)
    child = sim.get("child")
    return {
        "needs_license": bool(goal.id == "copies"),
        "conflict": child.memes["conflict"] >= THRESHOLD,
    }


def _do_attempt(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    child.meters["attempt"] += 1
    child.memes["want"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, setting: CopySetting, child: Entity, helper: Entity, adult: Entity, license_item: LicenseItem, goal: GoalItem) -> None:
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At {setting.place}, {child.id} and {helper.id} stood by the {setting.counter}. "
        f"{setting.detail}"
    )
    world.say(
        f"They wanted to use the {setting.machine} to {goal.phrase}, so the little stack would multiply into many copies."
    )


def foreshadow(world: World, setting: CopySetting, license_item: LicenseItem) -> None:
    world.say(
        f"{setting.noise} The machine's light blinked once, and {license_item.label} sat by the slot like a small reminder."
    )
    world.say(
        f'{world.get("helper").id} frowned. "We probably need {license_item.phrase}," {world.get("helper").pronoun()} said.'
    )


def warn(world: World, adult: Entity, child: Entity, license_item: LicenseItem, goal: GoalItem) -> None:
    child.memes["warned"] += 1
    pred = predict_problem(world, goal)
    world.facts["predicted_conflict"] = pred["conflict"]
    world.say(
        f'{adult.label_word.capitalize()} looked over and said, "{license_item.label.capitalize()} is for using the machine. '
        f'Please do not start it without one."'
    )


def defy(world: World, child: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f'{child.id} took a breath. "I can do it," {child.pronoun()} said, even though the warning made {child.pronoun("possessive")} hands shaky.'
    )


def brave_honest(world: World, child: Entity, helper: Entity) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Then {child.id} surprised everyone by speaking up. \"I want to help, but I don't want to break the rule,\" {child.pronoun()} admitted."
    )
    world.say(
        f"{helper.id} nodded right away. That was the bravest part: telling the truth before anything went wrong."
    )


def resolve(world: World, adult: Entity, child: Entity, helper: Entity, goal: GoalItem, license_item: LicenseItem, response: Response) -> None:
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{adult.label_word.capitalize()} smiled and used {response.text}."
    )
    world.say(
        f"With {license_item.phrase} checked and the settings fixed, the {goal.label} came out cleanly, one copy after another."
    )


def finish(world: World, child: Entity, helper: Entity, goal: GoalItem, license_item: LicenseItem) -> None:
    world.say(
        f"By the end, {child.id} was gathering the fresh pages into a neat pile while {helper.id} stacked the extras. "
        f"The {goal.label} had multiplied, and the {license_item.label} stayed right where it belonged."
    )
    child.memes["joy"] += 1
    helper.memes["joy"] += 1


def tell(setting: CopySetting, license_item: LicenseItem, goal: GoalItem, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         helper_name: str = "Noah", helper_gender: str = "boy",
         adult_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", role="adult"))

    setup(world, setting, child, helper, adult, license_item, goal)
    world.para()
    foreshadow(world, setting, license_item)
    warn(world, adult, child, license_item, goal)

    if child.id and helper.id:
        if child.memes["warned"] >= THRESHOLD:
            brave_honest(world, child, helper)
        else:
            defy(world, child)

    world.para()
    resolve(world, adult, child, helper, goal, license_item, response)
    finish(world, child, helper, goal, license_item)

    world.facts.update(
        child=child,
        helper=helper,
        adult=adult,
        setting=setting,
        license_item=license_item,
        goal=goal,
        response=response,
        outcome="resolved",
    )
    return world


SETTINGS = {
    "library": CopySetting(
        id="library",
        place="the little town library",
        counter="front counter",
        machine="copy machine",
        noise="Bip-bip.",
        detail="The room smelled like paper and warm dust, and the copier waited under a bright lamp.",
    ),
    "community_center": CopySetting(
        id="community_center",
        place="the community center",
        counter="craft table",
        machine="copy machine",
        noise="Whirr.",
        detail="Children's drawings were pinned on the wall, and the copier blinked beside a basket of markers.",
    ),
}

LICENSES = {
    "copy_card": LicenseItem(
        id="copy_card",
        label="license card",
        phrase="the license card",
        where="in the slot by the machine",
        required=True,
        tags={"license"},
    ),
}

GOALS = {
    "flyers": GoalItem(
        id="copies",
        label="flyers",
        phrase="make the flyers",
        plural=True,
        tags={"multiply"},
    ),
}

RESPONSES = {
    "pause_and_ask": Response(
        id="pause_and_ask",
        sense=3,
        text="paused the machine and asked the adult to check the license card first",
        fail="tried to use the machine too soon, but the pages only jammed and curled",
        qa_text="paused the machine and asked the adult to check the license card first",
        tags={"license"},
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Tara", "Nina", "Sofia"]
BOY_NAMES = ["Noah", "Eli", "Milo", "Finn", "Owen"]


@dataclass
class StoryParams:
    setting: str
    license_item: str
    goal: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    adult_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for lid in LICENSES:
            for gid in GOALS:
                combos.append((sid, lid, gid))
    return combos


def explain_rejection(setting: CopySetting, license_item: LicenseItem, goal: GoalItem) -> str:
    return "(No story: this simple world expects a license card, a copy machine, and a goal that can actually multiply into pages.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a slice-of-life copying story about a license and multiplying pages.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--license-item", choices=LICENSES, dest="license_item")
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("(Unknown setting.)")
    if args.license_item and args.license_item not in LICENSES:
        raise StoryError("(Unknown license item.)")
    if args.goal and args.goal not in GOALS:
        raise StoryError("(Unknown goal.)")
    if args.response and args.response not in RESPONSES:
        raise StoryError("(Unknown response.)")
    setting = args.setting or rng.choice(list(SETTINGS))
    license_item = args.license_item or rng.choice(list(LICENSES))
    goal = args.goal or rng.choice(list(GOALS))
    response = args.response or rng.choice(list(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if child_gender == "girl" else "girl")
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != child_name])
    adult = args.adult or rng.choice(["mother", "father"])
    if (setting, license_item, goal) not in valid_combos():
        raise StoryError(explain_rejection(SETTINGS[setting], LICENSES[license_item], GOALS[goal]))
    return StoryParams(
        setting=setting,
        license_item=license_item,
        goal=goal,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        adult_type=adult,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a small child where a {f["setting"].place} scene includes the word "license" and the child wants to {f["goal"].phrase}.',
        f'Write a gentle everyday story where {f["child"].pronoun("subject").capitalize()} wants to multiply the pages, but a grown-up reminds them about the license card first.',
        f'Tell a simple conflict-and-bravery story about a copy machine, a license card, and making many copies safely.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    adult = f["adult"]
    setting = f["setting"]
    lic = f["license_item"]
    goal = f["goal"]
    return [
        QAItem(
            question="What kind of place was the story set in?",
            answer=f"It was set at {setting.place}. The room felt ordinary and busy, like a normal afternoon where someone might need to make copies.",
        ),
        QAItem(
            question="What did the child want to do?",
            answer=f"{child.label} wanted to {goal.phrase} so the pages would multiply into a whole stack. That was the plan that made the little conflict begin.",
        ),
        QAItem(
            question="Why did the grown-up mention the license card?",
            answer=f"The license card was needed before using the machine. The adult saw the rule clearly and wanted the child to stay safe and follow it.",
        ),
        QAItem(
            question=f"How did {child.label} show bravery?",
            answer=f"{child.label} showed bravery by speaking up and admitting the rule mattered. That was brave because it was easier to rush ahead than to pause and ask for help.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"They used the machine the right way, with the license card checked first, and the flyers came out in a neat stack. The ending image proves the pages multiplied without turning into a problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a license?",
            answer="A license is permission or official approval to do something. It tells people they are allowed to use a tool or drive a vehicle in a safe, legal way.",
        ),
        QAItem(
            question="What does multiply mean?",
            answer="Multiply means to make more of something or to make a number become bigger by repeating it. In the story, it means making many copies of the flyers.",
        ),
        QAItem(
            question="What does a copy machine do?",
            answer="A copy machine makes extra pages that look like the original. It helps people share the same paper with many people at once.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: type={e.type} label={e.label} meters={dict(meters)} memes={dict(memes)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for lid in LICENSES:
        lines.append(asp.fact("license_item", lid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    for rid in RESPONSES:
        lines.append(asp.fact("response", rid))
    lines.append(asp.fact("needs_license", "copies"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, L, G) :- setting(S), license_item(L), goal(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH: ASP gate differs from valid_combos().")
        rc = 1
    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(777))
        sample = generate(params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(
        setting="library",
        license_item="copy_card",
        goal="flyers",
        response="pause_and_ask",
        child_name="Mina",
        child_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        setting="community_center",
        license_item="copy_card",
        goal="flyers",
        response="pause_and_ask",
        child_name="Eli",
        child_gender="boy",
        helper_name="Lia",
        helper_gender="girl",
        adult_type="father",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.license_item not in LICENSES or params.goal not in GOALS or params.response not in RESPONSES:
        raise StoryError("(Invalid params.)")
    world = tell(
        SETTINGS[params.setting],
        LICENSES[params.license_item],
        GOALS[params.goal],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        adult_type=params.adult_type,
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


def build_storyworld_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        return [generate(p) for p in CURATED]
    samples: list[StorySample] = []
    seen: set[str] = set()
    i = 0
    while len(samples) < args.n and i < max(args.n * 20, 20):
        seed = base_seed + i
        i += 1
        try:
            params = resolve_params(args, random.Random(seed))
        except StoryError as err:
            print(err)
            return []
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, l, g in combos:
            print(f"  {s:18} {l:12} {g}")
        return

    samples = build_storyworld_samples(args)
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
            header = f"### {p.child_name}: {p.setting} / {p.goal} / {p.license_item}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
