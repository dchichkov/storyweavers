#!/usr/bin/env python3
"""
storyworlds/worlds/southern_specimen_sound_effects_slice_of_life.py
===================================================================

A small slice-of-life story world about a child, a southern afternoon, and the
delicate task of making sound effects without upsetting a treasured specimen.

Premise:
- A child loves making sound effects for pretend scenes.
- A grown-up worries that the noisy play could shake a fragile specimen.
- They find a gentler setup that keeps the object safe and the play lively.

The simulated world models:
- physical meters: noise, jostle, dust, calm, break_risk
- emotional memes: delight, worry, pride, patience, closeness

The story is intentionally narrow: only plausible, state-driven variants are
generated, and explicit invalid combinations raise StoryError.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grandfather"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    region: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    action: str
    gerund: str
    sound: str
    loudness: str
    mess: str
    keywords: set[str] = field(default_factory=set)


@dataclass
class Specimen:
    label: str
    phrase: str
    type: str
    fragility: float = 1.0


@dataclass
class SoundTool:
    id: str
    label: str
    phrase: str
    effect: str
    quiet: bool = False


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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _meter(obj: Entity, key: str) -> float:
    return obj.meters.get(key, 0.0)


def _mem(obj: Entity, key: str) -> float:
    return obj.memes.get(key, 0.0)


def _add_meter(obj: Entity, key: str, amt: float) -> None:
    obj.meters[key] = _meter(obj, key) + amt


def _add_mem(obj: Entity, key: str, amt: float) -> None:
    obj.memes[key] = _mem(obj, key) + amt


def _risk_world(world: World) -> None:
    child = world.get("child")
    specimen = world.get("specimen")
    if _meter(child, "noise") >= THRESHOLD:
        _add_meter(specimen, "jostle", 1.0)
        _add_meter(specimen, "break_risk", 1.0)
        _add_mem(world.get("grownup"), "worry", 1.0)
    if _meter(child, "calm") >= THRESHOLD:
        _add_mem(world.get("grownup"), "pride", 1.0)


def predict_risk(world: World, activity: Activity, tool: Optional[SoundTool]) -> dict[str, bool]:
    sim = world.copy()
    child = sim.get("child")
    specimen = sim.get("specimen")
    _add_meter(child, "noise", 1.0 if not (tool and tool.quiet) else 0.0)
    _add_meter(child, "calm", 1.0 if (tool and tool.quiet) else 0.0)
    _risk_world(sim)
    return {"risk": _meter(specimen, "break_risk") >= THRESHOLD}


def intro(world: World) -> None:
    c = world.get("child")
    g = world.get("grownup")
    world.say(
        f"{c.id} was a little {c.type} who loved turning ordinary afternoons into tiny shows."
    )
    world.say(
        f"{g.pronoun().capitalize()} kept a careful eye on the table by the window, where the specimen sat in its clear jar."
    )


def love_activity(world: World, activity: Activity) -> None:
    c = world.get("child")
    _add_mem(c, "delight", 1.0)
    world.say(
        f"{c.id} loved {activity.gerund}, because every tap, squeak, and rustle could become part of a story."
    )


def set_scene(world: World, activity: Activity) -> None:
    world.say(
        f"On a warm southern afternoon, the porch was bright and still, except for the little sounds {activity.sound} in {world.setting.place}."
    )


def wants_play(world: World, activity: Activity) -> None:
    c = world.get("child")
    _add_mem(c, "eagerness", 1.0)
    world.say(
        f"{c.id} wanted to {activity.action} right away, and {c.pronoun()} lined up a spoon, a cup, and a handful of imagination."
    )


def warn(world: World, activity: Activity, specimen: Specimen) -> None:
    g = world.get("grownup")
    c = world.get("child")
    world.say(
        f'"If the table shakes too much, that specimen could slip," {g.pronoun("possessive")} {g.label} said.'
    )
    _add_mem(g, "worry", 1.0)
    _add_mem(c, "pause", 1.0)


def try_noisy(world: World, activity: Activity) -> None:
    c = world.get("child")
    _add_meter(c, "noise", 1.0)
    _add_mem(c, "frustration", 1.0)
    world.say(f"{c.id} made one big {activity.sound}, then stopped and listened.")
    _risk_world(world)


def offer_fix(world: World, tool: SoundTool, activity: Activity, specimen: Specimen) -> None:
    c = world.get("child")
    g = world.get("grownup")
    world.say(
        f"Then {g.pronoun()} slid a soft towel closer and said, "
        f'"How about you use {tool.phrase} instead? It still sounds like {tool.effect}, just gentler."'
    )
    _add_mem(c, "patience", 1.0)
    _add_mem(g, "closeness", 1.0)


def accept_fix(world: World, tool: SoundTool, activity: Activity, specimen: Specimen) -> None:
    c = world.get("child")
    g = world.get("grownup")
    _add_meter(c, "calm", 1.0)
    _add_mem(c, "delight", 1.0)
    _add_mem(g, "pride", 1.0)
    world.say(
        f"{c.id} nodded, switched to {tool.label}, and the whole porch filled with a softer little rhythm."
    )
    world.say(
        f"By the end, {c.id} was {activity.gerund}, {specimen.label} stayed safe on the side table, and {g.id} smiled at the easy quiet they had made together."
    )


def tell(world: World, activity: Activity, specimen_cfg: Specimen, tool: SoundTool) -> World:
    child = world.add(Entity(id="child", kind="character", type="boy", label="child"))
    grownup = world.add(Entity(id="grownup", kind="character", type="grandmother", label="grandma"))
    specimen = world.add(Entity(
        id="specimen",
        type=specimen_cfg.type,
        label=specimen_cfg.label,
        phrase=specimen_cfg.phrase,
        fragile=True,
    ))
    world.facts.update(activity=activity, specimen=specimen_cfg, tool=tool, child=child, grownup=grownup)

    intro(world)
    love_activity(world, activity)
    world.para()
    set_scene(world, activity)
    wants_play(world, activity)
    warn(world, activity, specimen_cfg)
    try_noisy(world, activity)
    world.para()
    if predict_risk(world, activity, tool)["risk"]:
        offer_fix(world, tool, activity, specimen_cfg)
        accept_fix(world, tool, activity, specimen_cfg)
    else:
        world.say(
            f"In the end, the first try was already fine, and the specimen rested safely while the music of the porch went on."
        )
    return world


SETTINGS = {
    "porch": Setting(place="the porch", region="south", affords={"make_sfx"}),
    "kitchen": Setting(place="the kitchen table", region="south", affords={"make_sfx"}),
    "den": Setting(place="the den", region="south", affords={"make_sfx"}),
}

ACTIVITIES = {
    "make_sfx": Activity(
        id="make_sfx",
        action="make sound effects",
        gerund="making sound effects",
        sound="with taps and clacks",
        loudness="lively",
        mess="noise",
        keywords={"sound", "effects", "slice", "life", "southern"},
    ),
}

SPECIENS = {
    "jar": Specimen(
        label="specimen jar",
        phrase="a little glass jar with a paper label",
        type="jar",
        fragility=1.0,
    ),
    "shell": Specimen(
        label="shell display",
        phrase="a small shell display from the county fair",
        type="display",
        fragility=1.0,
    ),
    "fossil": Specimen(
        label="fossil tray",
        phrase="a shallow tray holding a tiny fossil",
        type="tray",
        fragility=1.0,
    ),
}

TOOLS = {
    "spoon": SoundTool(
        id="spoon",
        label="a wooden spoon on a mug",
        phrase="a wooden spoon on a mug",
        effect="hoofbeats in a slow scene",
    ),
    "coconut": SoundTool(
        id="coconut",
        label="two half shells on a towel",
        phrase="two half shells on a towel",
        effect="horse hooves on a dirt road",
    ),
    "paper": SoundTool(
        id="paper",
        label="a folded paper fan",
        phrase="a folded paper fan",
        effect="wind through tall grass",
        quiet=True,
    ),
}

NAMES = ["Milo", "June", "Ivy", "Beau", "Lena", "Rowan", "Nell", "Tate"]
GROWNUPS = ["grandmother", "mother", "aunt"]
TRAITS = ["curious", "gentle", "lively", "patient"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    specimen: str
    tool: str
    name: str
    grownup: str
    trait: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid, s.place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for k in sorted(a.keywords):
            lines.append(asp.fact("keyword", aid, k))
    for pid, p in SPECIENS.items():
        lines.append(asp.fact("specimen", pid))
        lines.append(asp.fact("fragile", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.quiet:
            lines.append(asp.fact("quiet", tid))
    return "\n".join(lines)


ASP_RULES = r"""
risk(S) :- specimen(S), fragile(S).
quiet_fix(T) :- tool(T), quiet(T).
valid_story(S,P,T) :- affords(S,P), risk(_), quiet_fix(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with southern sound effects and a specimen jar.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--specimen", choices=SPECIENS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=GROWNUPS)
    ap.add_argument("--trait", choices=TRAITS)
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
    activity = args.activity or rng.choice(list(ACTIVITIES))
    specimen = args.specimen or rng.choice(list(SPECIENS))
    tool = args.tool or rng.choice(list(TOOLS))
    name = args.name or rng.choice(NAMES)
    grownup = args.grownup or rng.choice(GROWNUPS)
    trait = args.trait or rng.choice(TRAITS)
    if activity != "make_sfx":
        raise StoryError("Only the sound-effects activity is valid in this world.")
    if tool == "paper" and specimen == "jar":
        return StoryParams(setting, activity, specimen, tool, name, grownup, trait)
    return StoryParams(setting, activity, specimen, tool, name, grownup, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle southern slice-of-life story about a child making sound effects near a fragile specimen.",
        f"Tell a short story where {f['child'].id} wants to make sound effects and {f['grownup'].id} worries about the {f['specimen'].label}.",
        "Write a small story about noisy play, a careful grown-up, and a softer way to keep the fun going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, g, s, t, a = f["child"], f["grownup"], f["specimen"], f["tool"], f["activity"]
    return [
        QAItem(
            question=f"What did {c.id} want to do?",
            answer=f"{c.id} wanted to {a.action} with tiny homemade noises.",
        ),
        QAItem(
            question=f"Why did {g.id} worry about the {s.label}?",
            answer=f"{g.id} worried because too much shaking could make the {s.label} slip or get damaged.",
        ),
        QAItem(
            question=f"What helped {c.id} keep playing more gently?",
            answer=f"{t.phrase} helped because it made the scene feel lively without being as loud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are made-up or chosen noises that help a story, movie, or game feel real.",
        ),
        QAItem(
            question="What does fragile mean?",
            answer="Fragile means something can break or get damaged easily, so it needs gentle handling.",
        ),
        QAItem(
            question="What is a specimen?",
            answer="A specimen is something kept to look at or study, like a shell, rock, or fossil.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    activity = ACTIVITIES[params.activity]
    specimen = SPECIENS[params.specimen]
    tool = TOOLS[params.tool]
    world = tell(world, activity, specimen, tool)
    world.facts.update(activity=activity, specimen=specimen, tool=tool)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "valid_story"))
    if atoms:
        print(f"OK: ASP produced {len(atoms)} valid story tuple(s).")
        return 0
    print("MISMATCH: ASP produced no valid stories.")
    return 1


CURATED = [
    StoryParams(setting="porch", activity="make_sfx", specimen="jar", tool="paper", name="Milo", grownup="grandmother", trait="curious"),
    StoryParams(setting="kitchen", activity="make_sfx", specimen="shell", tool="spoon", name="June", grownup="mother", trait="gentle"),
    StoryParams(setting="den", activity="make_sfx", specimen="fossil", tool="coconut", name="Beau", grownup="aunt", trait="lively"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        print("ASP mode is available; this world keeps one narrow valid pattern.")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
