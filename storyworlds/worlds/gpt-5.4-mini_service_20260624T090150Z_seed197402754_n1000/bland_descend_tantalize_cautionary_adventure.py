#!/usr/bin/env python3
"""
Storyworld: a cautious adventure about descending a path while resisting a
tantalizing but bland shortcut.

A small child and a helper set out on an adventure trail. The child wants to
descend to a lower lookout, but a tempting snack or route is bland, unhelpful,
or unsafe in the wrong moment. A warning, a small pause, and a better choice
turn the moment into a careful adventure.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    descent: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    bland: bool
    risky: bool
    effect: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone = World(self.setting)
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ridge": Setting(place="the ridge path", descent="the steep steps", affords={"trail", "steps"}),
    "cave": Setting(place="the cave trail", descent="the narrow descent", affords={"trail"}),
    "garden": Setting(place="the garden stairs", descent="the stone steps", affords={"steps"}),
}

TEMPTATIONS = {
    "snack": Temptation(
        id="snack",
        label="a bland snack",
        phrase="a bland snack in a crinkly bag",
        bland=True,
        risky=False,
        effect="it would not make the walk safer",
        keyword="bland",
        tags={"bland", "snack"},
    ),
    "shortcut": Temptation(
        id="shortcut",
        label="a tempting shortcut",
        phrase="a shortcut that looked fast but steep",
        bland=False,
        risky=True,
        effect="it could send someone sliding down too quickly",
        keyword="descend",
        tags={"descend", "risky"},
    ),
    "spice": Temptation(
        id="spice",
        label="a tantalizing spice jar",
        phrase="a tantalizing little spice jar",
        bland=False,
        risky=False,
        effect="it would only distract from the trail",
        keyword="tantalize",
        tags={"tantalize", "taste"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="a sturdy rope",
        phrase="a sturdy rope for the steps",
        covers={"steps"},
        helps={"risky"},
        prep="tie in the rope first",
        tail="carefully descended with the rope",
    ),
    "boots": Aid(
        id="boots",
        label="grippy boots",
        phrase="grippy boots with deep soles",
        covers={"trail", "steps"},
        helps={"risky"},
        prep="put on the grippy boots first",
        tail="walked down with the grippy boots",
    ),
    "pack": Aid(
        id="pack",
        label="a small day pack",
        phrase="a small day pack with water",
        covers={"trail"},
        helps={"snack", "taste"},
        prep="pack water and the day pack",
        tail="went on with the day pack",
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ivy", "Zoe", "Ava", "Lily"]
BOY_NAMES = ["Leo", "Finn", "Toby", "Eli", "Noah", "Max", "Ben"]
TRAITS = ["brave", "curious", "careful", "adventurous", "spirited"]


@dataclass
class StoryParams:
    place: str
    temptation: str
    aid: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin + Python gate
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A temptation is relevant if it matches the setting and the chosen scene.
relevant(T) :- temptation(T).

% The risky temptation is the shortcut, because it affects descent.
at_risk(T) :- temptation(T), risky_temptation(T).

% An aid is compatible if it helps the relevant risk and fits the setting.
compatible(A, T) :- aid(A), at_risk(T), helps_risk(A), setting_place_ok(A).

valid_story(Place, T, A) :- setting(Place), temptation(T), aid(A),
                            scene_ok(Place, T, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place_name", sid, s.place))
        lines.append(asp.fact("descent", sid, s.descent))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        if t.risky:
            lines.append(asp.fact("risky_temptation", tid))
        if t.bland:
            lines.append(asp.fact("bland", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for aid, a in AIDS.items():
        lines.append(asp.fact("aid", aid))
        for h in sorted(a.helps):
            lines.append(asp.fact("helps_risk", aid))
        for c in sorted(a.covers):
            lines.append(asp.fact("setting_place_ok", aid))
    for sid in SETTINGS:
        for tid in TEMPTATIONS:
            for aid in AIDS:
                if valid_combo_python(sid, tid, aid):
                    lines.append(asp.fact("scene_ok", sid, tid, aid))
    return "\n".join(lines)


def valid_combo_python(place: str, temptation: str, aid: str) -> bool:
    s = SETTINGS[place]
    t = TEMPTATIONS[temptation]
    a = AIDS[aid]
    if place not in SETTINGS:
        return False
    if temptation not in TEMPTATIONS or aid not in AIDS:
        return False
    if temptation == "shortcut":
        return True and ("steps" in a.covers or "trail" in a.covers) and s.affords
    if temptation == "snack":
        return "trail" in s.affords
    if temptation == "spice":
        return "trail" in s.affords
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in SETTINGS:
        for t in TEMPTATIONS:
            for a in AIDS:
                if valid_combo_python(p, t, a):
                    combos.append((p, t, a))
    return combos


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def reason_rejection(temptation: Temptation, aid: Aid) -> str:
    if temptation.id == "shortcut" and "risky" in aid.helps:
        return ""
    return "(No story: the chosen aid does not fit this adventure.)"


def predict(world: World, child: Entity, temptation: Temptation) -> dict[str, object]:
    sim = world.copy()
    apply_temptation(sim, sim.get(child.id), temptation, narrate=False)
    return {
        "slip": bool(sim.facts.get("slip")),
        "mood": sim.get(child.id).memes.get("worry", 0.0),
    }


def apply_temptation(world: World, child: Entity, temptation: Temptation, narrate: bool = True) -> None:
    if temptation.id == "shortcut":
        child.memes["want"] = child.memes.get("want", 0.0) + 1
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.facts["slip"] = True
        if narrate:
            world.say(f"The shortcut looked quick, but it was too steep for a safe descent.")
    elif temptation.id == "snack":
        child.memes["want"] = child.memes.get("want", 0.0) + 1
        if narrate:
            world.say(f"The snack was bland, so it was not the right reward for an adventure pause.")
    else:
        child.memes["want"] = child.memes.get("want", 0.0) + 1
        if narrate:
            world.say(f"The little jar was tantalizing, but the trail needed attention first.")


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    temptation = TEMPTATIONS[params.temptation]
    aid = AIDS[params.aid]
    world.facts.update(hero=hero, parent=parent, temptation=temptation, aid=aid, setting=world.setting)

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who loved adventure.")
    world.say(f"{hero.id} and {parent.label} came to {world.setting.place}, where {world.setting.descent} waited below.")

    world.para()
    world.say(f"At the top, {hero.id} noticed {temptation.phrase}.")
    if temptation.bland:
        world.say(f"It looked bland, and that made it even less useful for the climb.")
    else:
        world.say(f"It was tantalizing, and that made the child pause.")
    apply_temptation(world, hero, temptation)

    if temptation.id == "shortcut":
        world.say(f"{parent.label} said, \"That path would be hard to descend safely.\"")
        world.say(f"{hero.id} wanted to hurry, but {hero.pronoun('possessive')} {parent.label} held up a steady hand.")
    elif temptation.id == "snack":
        world.say(f"{parent.label} smiled and said, \"A bland snack can wait until we reach the bottom.\"")
    else:
        world.say(f"{parent.label} said, \"Let's leave the tantalizing jar for later and keep our eyes on the trail.\"")

    world.para()
    if temptation.id == "shortcut":
        world.say(f"Then they chose {aid.phrase}.")
        world.say(f"They agreed to {aid.prep}, and {hero.id} felt safer right away.")
        hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        world.say(f"Together they {aid.tail}, and the child stayed steady all the way down.")
    elif temptation.id == "snack":
        world.say(f"Then they chose to save the snack and keep walking.")
        world.say(f"The child tucked away the bland treat and looked for better sights instead.")
        world.say(f"They {aid.tail}, enjoying the view more than the crumbs.")
    else:
        world.say(f"Then they chose {aid.phrase} and kept their pace.")
        world.say(f"The child stopped staring at the tantalizing jar and watched the stones underfoot.")
        world.say(f"They {aid.tail}, and the trail felt like a proper adventure again.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    temptation = f["temptation"]
    aid = f["aid"]
    return [
        f'Write a short cautionary adventure story for a young child that includes the word "{temptation.keyword}".',
        f"Tell a gentle story where {hero.id} must descend a path, resist a tempting choice, and choose {aid.label}.",
        f'Write an adventure story that uses the words "bland", "descend", and "tantalize" in a child-friendly way.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    parent: Entity = f["parent"]  # type: ignore[assignment]
    temptation: Temptation = f["temptation"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    setting: Setting = f["setting"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who went on the adventure at {setting.place}?",
            answer=f"{hero.id} went on the adventure with {parent.label}.",
        ),
        QAItem(
            question=f"What was waiting below on the path?",
            answer=f"{setting.descent} was waiting below, so they had to descend carefully.",
        ),
        QAItem(
            question=f"What did {hero.id} notice at the top?",
            answer=f"{hero.id} noticed {temptation.phrase}, which was a tempting but not very helpful choice.",
        ),
        QAItem(
            question=f"What did they use to make the descent safer?",
            answer=f"They used {aid.phrase} so {hero.id} could move down more safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    temptation: Temptation = f["temptation"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    out = [
        QAItem(
            question="What does bland mean?",
            answer="Bland means plain and not very exciting in taste or feeling.",
        ),
        QAItem(
            question="What does descend mean?",
            answer="Descend means to go down from a higher place to a lower one.",
        ),
        QAItem(
            question="What does tantalize mean?",
            answer="Tantalize means to tease someone by making something seem tempting but not easy to have.",
        ),
    ]
    if temptation.id == "shortcut":
        out.append(QAItem(
            question="Why can a steep shortcut be risky?",
            answer="A steep shortcut can be risky because it may make someone slip or hurry in an unsafe way.",
        ))
    if aid.id == "boots":
        out.append(QAItem(
            question="What are grippy boots for?",
            answer="Grippy boots help keep feet steady on rocks, stairs, or muddy ground.",
        ))
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="ridge", temptation="shortcut", aid="boots", name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="cave", temptation="spice", aid="pack", name="Leo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="garden", temptation="snack", aid="boots", name="Nora", gender="girl", parent="mother", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.temptation and args.temptation not in TEMPTATIONS:
        raise StoryError("Unknown temptation.")
    if args.aid and args.aid not in AIDS:
        raise StoryError("Unknown aid.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.temptation is None or c[1] == args.temptation)
        and (args.aid is None or c[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, temptation, aid = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or choose_name(gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, temptation=temptation, aid=aid, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary adventure storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp.atoms(model, 'valid_story'))} compatible stories.")
        for x in sorted(set(asp.atoms(model, "valid_story"))):
            print(x)
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
            except StoryError as e:
                print(e)
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


if __name__ == "__main__":
    main()
