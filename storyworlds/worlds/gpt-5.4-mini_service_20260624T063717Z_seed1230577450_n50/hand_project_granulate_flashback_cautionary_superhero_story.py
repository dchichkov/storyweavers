#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/hand_project_granulate_flashback_cautionary_superhero_story.py
=============================================================================================================

A small, standalone storyworld with a superhero-story flavor.

Premise:
- A young hero is helping with a neighborhood project in a workshop.
- The project uses granulate, which can scatter into the air and make a mess.
- A flashback teaches why the hero's mentor is cautious about leaving the hand unprotected.
- The resolution is a safer way to finish the project without ruining the hero's suit or the workshop.

The story is intentionally compact and state-driven:
- physical meters track dust, mess, cover, and project progress;
- emotional memes track excitement, caution, worry, and pride;
- the ending proves what changed.

The domain is child-facing, concrete, and written in a superhero-story style.
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


THRESHOLD = 1.0
SAFE_MATERIALS = {"glue", "beads", "paper", "buttons"}
DUSTY_MATERIALS = {"granulate"}
SETTINGS = {
    "workshop": {"place": "the workshop", "indoors": True},
    "garage": {"place": "the garage", "indoors": True},
    "roof": {"place": "the rooftop", "indoors": False},
    "basement": {"place": "the basement room", "indoors": True},
}

PROJECTS = {
    "model_city": {
        "label": "model city project",
        "verb": "build a model city",
        "gerund": "building the model city",
        "finish": "the tiny towers stood upright",
        "tag": "city",
    },
    "signal_beacon": {
        "label": "signal beacon project",
        "verb": "assemble a signal beacon",
        "gerund": "assembling the signal beacon",
        "finish": "the beacon light blinked bright and steady",
        "tag": "light",
    },
    "rescue_kite": {
        "label": "rescue kite project",
        "verb": "make a rescue kite",
        "gerund": "making the rescue kite",
        "finish": "the kite stayed strong and ready",
        "tag": "kite",
    },
}

MATERIALS = {
    "granulate": {
        "label": "granulate",
        "phrase": "a bag of granulate",
        "mess": "dusty",
        "soil": "dusty",
        "risk": "it could puff into the air and cling to everything",
    },
    "glitter": {
        "label": "glitter",
        "phrase": "a jar of glitter",
        "mess": "sparkly",
        "soil": "sparkly",
        "risk": "it could scatter all over the floor",
    },
    "paint_powder": {
        "label": "paint powder",
        "phrase": "a cup of paint powder",
        "mess": "colored",
        "soil": "colored",
        "risk": "it could streak the hands and table",
    },
}

GEAR = {
    "gloves": {
        "label": "work gloves",
        "covers": {"hand"},
        "guards": {"dusty", "sparkly", "colored"},
        "prep": "put on work gloves first",
        "tail": "pulled on the work gloves",
    },
    "mask": {
        "label": "a dust mask",
        "covers": {"face"},
        "guards": {"dusty"},
        "prep": "wear a dust mask",
        "tail": "buckled on the dust mask",
    },
    "apron": {
        "label": "an apron",
        "covers": {"torso"},
        "guards": {"sparkly", "colored", "dusty"},
        "prep": "tie on an apron",
        "tail": "tied on the apron",
    },
}

NAMES = ["Nova", "Milo", "Zuri", "Theo", "Rae", "Ivy", "Kai", "Aria"]
HELPERS = ["mentor", "captain", "guardian"]



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self):
        for k in ["dust", "mess", "project", "cover"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "caution", "worry", "pride", "flashback"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    project: str
    material: str
    hero: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self, setting: dict):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self):
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def safe_project(material_id: str, project_id: str) -> bool:
    return material_id in DUSTY_MATERIALS and project_id in PROJECTS


def choose_gear(material_id: str, project_id: str) -> Optional[str]:
    if material_id == "granulate":
        return "gloves"
    if material_id == "glitter":
        return "apron"
    if material_id == "paint_powder":
        return "apron"
    return None


ASP_RULES = r"""
risk(material(granulate), hand) :- granulate(granulate).
compatible(gloves, hand, granulate) :- guard(gloves, hand), handles(gloves, granulate).
valid_story(S, P, M) :- setting(S), project(P), material(M), risk(material(M), hand), compatible(gloves, hand, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s["indoors"]:
            lines.append(asp.fact("indoors", sid))
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    lines.append(asp.fact("granulate", "granulate"))
    lines.append(asp.fact("guard", "gloves", "hand"))
    lines.append(asp.fact("handles", "gloves", "granulate"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo = set(asp.atoms(model, "valid_story"))
    python = {(s, p, m) for s in SETTINGS for p in PROJECTS for m in MATERIALS if safe_project(m, p)}
    if clingo == python:
        print(f"OK: clingo gate matches Python ({len(clingo)} combos).")
        return 0
    print("MISMATCH between clingo and Python")
    print("only clingo:", sorted(clingo - python))
    print("only python:", sorted(python - clingo))
    return 1


def _flashback(world: World, hero: Entity, helper: Entity, material: str) -> None:
    hero.memes["flashback"] += 1
    hero.memes["caution"] += 1
    world.say(
        f"Flashback: once, {helper.id} let {material} pour across the bench, and "
        f"{hero.id}'s hand came away gray and itchy."
    )
    world.say(
        f"That memory made {helper.id} lift a warning finger and tell {hero.id} to slow down."
    )


def _apply_risk(world: World, hero: Entity, material_id: str) -> None:
    material = _safe_lookup(MATERIALS, material_id)
    if hero.meters["cover"] >= THRESHOLD:
        return
    hero.meters["dust"] += 1
    hero.meters["mess"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"The {material['label']} puffed up around {hero.id}'s hand and left a dusty ring on the table."
    )


def _finish_project(world: World, hero: Entity, project: dict, gear_label: str) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"With the {gear_label} on, {hero.id} kept the {project['label']} neat, and {project['finish']}."
    )


def tell(setting_id: str, project_id: str, material_id: str, hero_name: str, helper_role: str) -> World:
    setting = _safe_lookup(SETTINGS, setting_id)
    project = _safe_lookup(PROJECTS, project_id)
    material = _safe_lookup(MATERIALS, material_id)
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero", label=hero_name))
    helper = world.add(Entity(id=helper_role, kind="character", type=helper_role, label=f"the {helper_role}"))

    gear_id = choose_gear(material_id, project_id)
    if gear_id is None:
        pass
    gear_cfg = GEAR[gear_id]
    gear = world.add(Entity(
        id=gear_id,
        type="gear",
        label=gear_cfg["label"],
        protective=True,
        covers=set(gear_cfg["covers"]),
        owner=hero.id,
        worn_by=hero.id,
    ))
    hero.meters["cover"] += 1

    world.say(f"{hero.id} was a young hero who loved every brave {project['label']}.")
    world.say(f"One day, {hero.id} and {helper.id} gathered at {setting['place']} to {project['verb']}.")
    world.say(f"The work needed {material['phrase']}, but {material['risk']}.")
    _flashback(world, hero, helper, material['label'])
    world.say(
        f"{helper.id} said, \"Before we touch the project, let's {gear_cfg['prep']} so the hand stays safe.\""
    )
    world.say(f"{hero.id} nodded and {gear_cfg['tail']}.")
    _finish_project(world, hero, project, gear_cfg["label"])
    world.say(
        f"In the end, {hero.id}'s hand stayed clean, the {project['label']} was done, and the workshop stayed calm."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        setting_id=setting_id,
        project_id=project_id,
        material_id=material_id,
        gear_id=gear_id,
        project=project,
        material=material,
        gear=gear,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child where {f["hero"].id} helps with a {f["project"]["label"]} and uses the word "granulate".',
        f"Tell a cautionary flashback story in which {f['helper'].id} reminds {f['hero'].id} to protect a hand before using granulate.",
        f'Write a gentle superhero story that ends with a safe project and includes the words "flashback" and "cautionary".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    project = f["project"]
    material = f["material"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting['place']}?",
            answer=f"{hero.id} wanted to {project['verb']}.",
        ),
        QAItem(
            question=f"Why was {helper.id} cautious about the granulate?",
            answer=f"{helper.id} was cautious because the granulate could puff into the air and cling to the hand and the table.",
        ),
        QAItem(
            question=f"What flashed back into {hero.id}'s memory?",
            answer=f"{hero.id} remembered a time when the granulate spilled across the bench and left the hand gray and itchy.",
        ),
        QAItem(
            question=f"How did the heroes keep the project safe?",
            answer=f"They used {f['gear'].label} first, so {hero.id} could work on the {project['label']} without getting the hand dusty.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is granulate like?",
            answer="Granulate is a tiny grainy material that can scatter into dust if it is poured too fast.",
        ),
        QAItem(
            question="Why do heroes wear work gloves?",
            answer="Heroes wear work gloves to protect their hands from dust, sharp bits, and messy materials.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a memory from earlier that the story shows again because it matters now.",
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it gives a warning and helps someone avoid a mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld with flashback and cautionary beats.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--project", choices=PROJECTS.keys())
    ap.add_argument("--material", choices=MATERIALS.keys())
    ap.add_argument("--hero", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    project = getattr(args, "project", None) or rng.choice(list(PROJECTS))
    material = getattr(args, "material", None) or rng.choice(list(MATERIALS))
    if material == "granulate" and project not in PROJECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not safe_project(material, project):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(setting=setting, project=project, material=material, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.setting, params.project, params.material, params.hero, params.helper)
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


def asp_story_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for mid in MATERIALS:
        lines.append(asp.fact("material", mid))
    lines.append(asp.fact("granulate", "granulate"))
    lines.append(asp.fact("guard", "gloves", "hand"))
    lines.append(asp.fact("handles", "gloves", "granulate"))
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(f"{asp_story_facts()}\n{ASP_RULES}\n#show valid_story/3.\n")
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_cli() -> None:
    combos = asp_valid_combos()
    for s, p, m in combos:
        print(s, p, m)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, p, m) for s in SETTINGS for p in PROJECTS for m in MATERIALS if safe_project(m, p)]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(f"{asp_story_facts()}\n{ASP_RULES}")
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        asp_cli()
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for s in SETTINGS:
            for p in PROJECTS:
                for m in MATERIALS:
                    try:
                        params = StoryParams(setting=s, project=p, material=m, hero=_safe_lookup(NAMES, 0), helper=_safe_lookup(HELPERS, 0))
                        if safe_project(m, p):
                            samples.append(generate(params))
                    except StoryError:
                        pass
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
