#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/festival_slumber_mountain_curiosity_rhyming_story.py
=====================================================================================

A small standalone storyworld for a curious child who follows a festival trail up a
mountain, finds a safe slumber spot, and learns to satisfy curiosity with help from
a kind guide. The prose is built from state changes, not a frozen paragraph.

This world aims for a rhyming, gentle cadence while still being a real simulation:
- a child explores a festival on a mountain,
- curiosity tempts them to wander,
- a guide predicts trouble and steers them toward a safer path,
- the ending proves what changed with a calm slumber image.

The seed words are present in the world model:
- festival
- slumber
- mountain
- curiosity
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
CURIOUS_MIN = 2.0


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


@dataclass
class Setting:
    id: str
    name: str
    height: str
    mood: str


@dataclass
class CuriosityPath:
    id: str
    clue: str
    rhyme: str
    risk: int
    shine: str


@dataclass
class SlumberSpot:
    id: str
    label: str
    phrase: str
    comfort: str
    sheltered: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Guide:
    id: str
    label: str
    calm: str
    offer: str
    rhyme: str
    power: int


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_wander(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.memes["curiosity"] < CURIOUS_MIN:
        return out
    if ("wander", child.id) in world.fired:
        return out
    world.fired.add(("wander", child.id))
    child.meters["wandering"] += 1
    child.memes["worry"] += 1
    out.append("__wander__")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    spot = world.entities.get("spot")
    if not child or not spot:
        return out
    if child.meters["slumber"] < THRESHOLD:
        return out
    if ("settle", child.id) in world.fired:
        return out
    world.fired.add(("settle", child.id))
    child.memes["peace"] += 1
    spot.meters["warmth"] += 1
    out.append("__settle__")
    return out


CAUSAL_RULES = [Rule("wander", "social", _r_wander), Rule("settle", "physical", _r_settle)]


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


def predict_path(world: World, path: CuriosityPath) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["curiosity"] += 1
    child.meters["wandering"] += path.risk
    return {
        "wanders": child.meters["wandering"] >= THRESHOLD,
        "risk": path.risk,
    }


def tell(setting: Setting, path: CuriosityPath, spot: SlumberSpot, guide: Guide,
         child_name: str, child_gender: str, guide_gender: str, parent_name: str,
         parent_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, role="curious_one",
                             traits=["curious"], attrs={"name": child_name}))
    guide_ent = world.add(Entity(id="guide", kind="character", type=guide_gender,
                                 label=guide.label, role="guide",
                                 traits=["kind", "calm"], attrs={"name": guide.label}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_gender,
                              label=parent_name, role="parent",
                              traits=["careful"], attrs={"name": parent_name}))
    world.add(Entity(id="spot", kind="thing", type="bed", label=spot.label,
                     role="slumber_spot", attrs={"comfort": spot.comfort}))
    world.add(Entity(id="path", kind="thing", type="path", label=path.id,
                     role="curiosity_path", attrs={"shine": path.shine}))

    child.memes["curiosity"] = 3.0
    guide_ent.memes["calm"] = 3.0
    parent.memes["care"] = 3.0

    world.say(
        f"At the mountain festival, {child_name} went with a grin, "
        f"where lanterns swung and bright drums spun."
    )
    world.say(
        f"The mountain was high, and the night air was clear; "
        f"the little feet felt light, but also felt fear."
    )

    world.para()
    child.memes["curiosity"] += 1
    world.say(
        f"{child_name} saw a {path.clue} and followed the gleam, "
        f"for curious hearts often chase a small dream."
    )
    pred = predict_path(world, path)
    world.facts["pred"] = pred
    world.facts["path"] = path
    world.facts["spot"] = spot
    world.facts["guide"] = guide
    world.facts["child"] = child
    world.facts["parent"] = parent

    if pred["wanders"]:
        world.say(
            f"{guide_ent.label} saw the trail and spoke soft and slow: "
            f'"When curiosity races, the safest way is to know."'
        )
        guide_ent.memes["calm"] += 1
        child.memes["worry"] += 1
        child.meters["slumber"] += 1
        world.say(
            f'{child_name} paused at the {path.shine}, then nodded with care; '
            f'they chose the warm camp and went back from the stair.'
        )
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} laid out {spot.phrase}, all soft and light, "
            f"and promised a slumber that felt snug through the night."
        )
        propagate(world, narrate=False)
        world.say(
            f"At last, by the fire, {child_name} curled down to rest; "
            f"{spot.comfort} and the blanket made the small bed the best."
        )
        child.meters["slumber"] += 1
        spot.meters["warmth"] += 1
        world.say(
            f"The festival went on in a faraway song, and the mountain held moonlight "
            f"all night long."
        )
    else:
        world.say(
            f"{child_name} had found only a harmless small spark, "
            f"so the trail ended gently and quiet and dark."
        )
        child.meters["slumber"] += 1
        world.para()
        world.say(
            f"By dawn, {child_name} still slept in the snug little place, "
            f"with a calm, tiny smile on a moon-dusted face."
        )
        propagate(world, narrate=False)

    world.facts["outcome"] = "guided"
    return world


SETTINGS = {
    "mountain_festival": Setting(id="mountain_festival", name="festival on the mountain",
                                 height="high on the mountain", mood="bright"),
}

PATHS = {
    "lantern_trail": CuriosityPath(id="lantern_trail", clue="lantern trail", rhyme="gleam",
                                   risk=1, shine="lanterns"),
    "drum_path": CuriosityPath(id="drum_path", clue="drum path", rhyme="beat",
                               risk=2, shine="drums"),
    "cave_tune": CuriosityPath(id="cave_tune", clue="cave tune", rhyme="hum",
                               risk=3, shine="echoes"),
}

SLEEP_SPOTS = {
    "tent": SlumberSpot(id="tent", label="a little tent", phrase="a little tent",
                        comfort="soft and snug", tags={"slumber", "sleep"}),
    "blanket_nook": SlumberSpot(id="blanket_nook", label="a blanket nook",
                                phrase="a blanket nook", comfort="warm and tucked",
                                tags={"slumber", "sleep"}),
}

GUIDES = {
    "lantern_keeper": Guide(id="lantern_keeper", label="lantern keeper",
                            calm="soft", offer="back to camp", rhyme="gleam", power=2),
}

@dataclass
class StoryParams:
    setting: str
    path: str
    spot: str
    guide: str
    child_name: str
    child_gender: str
    guide_gender: str
    parent_name: str
    parent_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="mountain_festival", path="lantern_trail", spot="tent",
                guide="lantern_keeper", child_name="Mina", child_gender="girl",
                guide_gender="woman", parent_name="Mama", parent_gender="woman"),
    StoryParams(setting="mountain_festival", path="drum_path", spot="blanket_nook",
                guide="lantern_keeper", child_name="Noah", child_gender="boy",
                guide_gender="woman", parent_name="Papa", parent_gender="man"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, path in PATHS.items():
            for spot_id, spot in SLEEP_SPOTS.items():
                if "slumber" in spot.tags and path.risk <= 3:
                    combos.append((sid, pid, spot_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    path = f["path"]
    spot = f["spot"]
    return [
        f'Write a rhyming story with the words "festival", "mountain", and "slumber".',
        f"Tell a gentle rhyming tale about {child.label} at a mountain festival, where curiosity follows {path.clue} and the child ends in {spot.label}.",
        f"Write a kid-friendly rhyming story about curiosity on a mountain, with a safe slumber ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    path = f["path"]
    spot = f["spot"]
    pred = f["pred"]
    return [
        QAItem(
            question=f"What made {child.label} wander?",
            answer=f"{child.label} wandered because curiosity pulled them toward the {path.clue}. The shining trail looked inviting, so they followed it until the guide helped them choose a safer path."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a calm slumber near {spot.label}. The mountain festival kept singing in the distance, but the child was safe, warm, and ready for sleep."
        ),
        QAItem(
            question="Why did the guide speak up?",
            answer=f"The guide spoke up because the path looked risky and curiosity was leading the child away from camp. The warning kept the child from wandering too far on the mountain."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a festival?",
            answer="A festival is a happy event with music, lights, and people celebrating together."
        ),
        QAItem(
            question="What is a mountain?",
            answer="A mountain is a very high hill of rock and earth that rises above the land."
        ),
        QAItem(
            question="What is slumber?",
            answer="Slumber means sleep. It is a gentle word for resting with your eyes closed."
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, look closer, and ask what is there."
        ),
    ]


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
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
curious(C) :- child(C), curiosity(Cu), Cu >= 2.
wanders(C) :- curious(C), risk_path(P), child_path(C, P).
guided(C) :- wanders(C), guide(G), calm(G).
slumbering(C) :- guided(C), slumber_spot(S).
#show curious/1.
#show wanders/1.
#show guided/1.
#show slumbering/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("risk_path", pid))
    for sid in SLEEP_SPOTS:
        lines.append(asp.fact("slumber_spot", sid))
    for gid in GUIDES:
        lines.append(asp.fact("guide", gid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("curiosity", "child", 3))
    lines.append(asp.fact("child_path", "child", "lantern_trail"))
    lines.append(asp.fact("calm", "lantern_keeper"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    shown = set((sym.name, tuple(arg.name if hasattr(arg, "name") else getattr(arg, "string", None) or getattr(arg, "number", None) for arg in sym.arguments)) for sym in model)
    ok = any(name == "guided" for name, _ in shown)
    if ok and validate_generate_smoke():
        print("OK: ASP twin and story generation smoke test passed.")
        return 0
    print("MISMATCH or smoke test failure.")
    return 1


def validate_generate_smoke() -> bool:
    try:
        sample = generate(CURATED[0])
        return bool(sample.story and sample.prompts and sample.story_qa and sample.world_qa)
    except Exception:
        return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld of festival, mountain, slumber, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--spot", choices=SLEEP_SPOTS)
    ap.add_argument("--guide", choices=GUIDES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guide-gender", choices=["woman", "man"])
    ap.add_argument("--parent-name")
    ap.add_argument("--parent-gender", choices=["woman", "man"])
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
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.path is None or c[1] == args.path)
              and (args.spot is None or c[2] == args.spot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, path, spot = rng.choice(sorted(combos))
    guide = args.guide or "lantern_keeper"
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    guide_gender = args.guide_gender or "woman"
    parent_gender = args.parent_gender or rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(["Mina", "Noah", "Luna", "Ivy", "Theo"])
    parent_name = args.parent_name or rng.choice(["Mama", "Papa", "Auntie", "Uncle"])
    return StoryParams(setting=setting, path=path, spot=spot, guide=guide,
                       child_name=child_name, child_gender=child_gender,
                       guide_gender=guide_gender, parent_name=parent_name,
                       parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        path = PATHS[params.path]
        spot = SLEEP_SPOTS[params.spot]
        guide = GUIDES[params.guide]
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc}") from exc
    world = tell(setting, path, spot, guide, params.child_name, params.child_gender,
                 params.guide_gender, params.parent_name, params.parent_gender)
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:", " ".join(sorted(str(a) for a in model)))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {idx + 1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
