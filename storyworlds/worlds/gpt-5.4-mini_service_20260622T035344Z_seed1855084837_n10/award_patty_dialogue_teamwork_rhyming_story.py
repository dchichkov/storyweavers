#!/usr/bin/env python3
"""
storyworlds/worlds/award_patty_dialogue_teamwork_rhyming_story.py
=================================================================

A tiny rhyming storyworld about teamwork, a patty, and an award.

Seed premise:
- A small team wants to make a patty for a contest.
- They need to work together, talk in dialogue, and keep the story rhyming.
- The finish should show how teamwork helped them win an award.

The world model tracks physical state in meters and emotional state in memes.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Cook:
    id: str
    verb: str
    gerund: str
    risk: str
    fix: str
    place_word: str
    rhyme_a: str
    rhyme_b: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    label: str
    place_phrase: str
    affords: set[str] = field(default_factory=set)


@dataclass
class TeamItem:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    cook: str
    award: str
    patty: str
    name1: str
    type1: str
    name2: str
    type2: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            role=v.role, owner=v.owner, caretaker=v.caretaker, plural=v.plural,
            tags=set(v.tags), attrs=dict(v.attrs), meters=defaultdict(float, v.meters),
            memes=defaultdict(float, v.memes),
        ) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "kitchen": Setting(id="kitchen", label="the kitchen", place_phrase="in the kitchen", affords={"cook"}),
    "yard": Setting(id="yard", label="the yard", place_phrase="in the yard", affords={"cook"}),
    "fair": Setting(id="fair", label="the fair booth", place_phrase="at the fair booth", affords={"cook"}),
}

COOKS = {
    "grill": Cook(id="grill", verb="grill a patty", gerund="grilling patties", risk="burn", fix="cool it with care", place_word="grill", rhyme_a="bright", rhyme_b="night", tags={"heat", "patty"}),
    "pan": Cook(id="pan", verb="flip a patty", gerund="flipping patties", risk="drop", fix="steady it with care", place_word="pan", rhyme_a="glow", rhyme_b="show", tags={"patty", "teamwork"}),
    "stove": Cook(id="stove", verb="cook a patty", gerund="cooking patties", risk="spill", fix="share the job", place_word="stove", rhyme_a="tune", rhyme_b="moon", tags={"patty"}),
}

AWARDS = {
    "blue_ribbon": TeamItem(id="blue_ribbon", label="blue ribbon", phrase="a blue ribbon award", tags={"award"}),
    "gold_star": TeamItem(id="gold_star", label="gold star", phrase="a gold star award", tags={"award"}),
}

PATTIES = {
    "pea_patty": TeamItem(id="pea_patty", label="patty", phrase="a pea patty", covers={"hand"}, guards={"burn", "drop", "spill"}, tags={"patty"}),
    "bean_patty": TeamItem(id="bean_patty", label="patty", phrase="a bean patty", covers={"hand"}, guards={"burn", "drop", "spill"}, tags={"patty"}),
}

TOOLS = {
    "spatula": TeamItem(id="spatula", label="spatula", phrase="a wide spatula", covers={"hand"}, guards={"drop"}, tags={"teamwork"}),
    "oven_mitt": TeamItem(id="oven_mitt", label="oven mitt", phrase="an oven mitt", covers={"hand"}, guards={"burn"}, tags={"teamwork"}),
    "towel": TeamItem(id="towel", label="towel", phrase="a clean towel", covers={"hand"}, guards={"spill"}, tags={"teamwork"}),
}

NAME_PAIRS = [("Mia", "girl", "Noah", "boy"), ("Ava", "girl", "Zoe", "girl"), ("Ben", "boy", "Leo", "boy"), ("Maya", "girl", "Eli", "boy")]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for c in COOKS:
            for a in AWARDS:
                out.append((s, c, a))
    return out


def rhyme_end(cook: Cook, award: TeamItem) -> str:
    return f"{cook.rhyme_a} and {cook.rhyme_b}"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork story about a patty and an award.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cook", choices=COOKS)
    ap.add_argument("--award", choices=AWARDS)
    ap.add_argument("--patty", choices=PATTIES)
    ap.add_argument("--name1")
    ap.add_argument("--type1", choices=["girl", "boy"])
    ap.add_argument("--name2")
    ap.add_argument("--type2", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=TOOLS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.cook is None or c[1] == args.cook)
              and (args.award is None or c[2] == args.award)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, cook, award = rng.choice(sorted(combos))
    patty = args.patty or rng.choice(sorted(PATTIES))
    helper = args.helper or rng.choice(sorted(TOOLS))
    name1, type1, name2, type2 = args.name1, args.type1, args.name2, args.type2
    if not name1 or not type1 or not name2 or not type2:
        name1, type1, name2, type2 = rng.choice(NAME_PAIRS)
    if name1 == name2:
        raise StoryError("The two teammates must have different names.")
    return StoryParams(setting=setting, cook=cook, award=award, patty=patty, name1=name1, type1=type1, name2=name2, type2=type2, helper=helper)


def team_count(world: World) -> int:
    return sum(1 for e in world.characters() if e.role in {"teammate", "helper"})


def apply_teamwork(world: World) -> None:
    cook = world.get("cook")
    patty = world.get("patty")
    helper = world.get("helper")
    if cook.memes["focus"] >= THRESHOLD and helper.memes["helping"] >= THRESHOLD:
        patty.meters["done"] += 1
        cook.memes["joy"] += 1
        helper.memes["joy"] += 1
        world.facts["teamwork_success"] = True
        world.say("Together they kept the rhythm, and the patty came out just right.")
    else:
        world.facts["teamwork_success"] = False


def tell(setting: Setting, cook_cfg: Cook, award_cfg: TeamItem, patty_cfg: TeamItem, helper_cfg: TeamItem,
         name1: str, type1: str, name2: str, type2: str) -> World:
    world = World(setting)
    cook = world.add(Entity(id="cook", kind="character", type=type1, label=name1, role="teammate"))
    teammate = world.add(Entity(id="mate", kind="character", type=type2, label=name2, role="teammate"))
    helper = world.add(Entity(id="helper", kind="thing", type="thing", label=helper_cfg.label, phrase=helper_cfg.phrase, role="helper", tags=set(helper_cfg.tags), plural=helper_cfg.plural))
    patty = world.add(Entity(id="patty", kind="thing", type="thing", label=patty_cfg.label, phrase=patty_cfg.phrase, role="goal", tags=set(patty_cfg.tags)))
    award = world.add(Entity(id="award", kind="thing", type="thing", label=award_cfg.label, phrase=award_cfg.phrase, role="prize", tags=set(award_cfg.tags)))
    world.add(Entity(id="stove", kind="thing", type="thing", label=cook_cfg.place_word, phrase=cook_cfg.place_word))
    world.facts.update(cook=cook, mate=teammate, helper=helper, patty=patty, award=award, cook_cfg=cook_cfg, setting=setting)

    cook.memes["want"] += 1
    teammate.memes["want"] += 1
    helper.memes["helping"] += 1
    cook.memes["focus"] += 1
    teammate.memes["focus"] += 1

    world.say(f"{name1} said, \"Let's make a patty, and make it look neat.\"")
    world.say(f"{name2} said, \"We'll share the work; we'll keep the beat.\"")
    world.para()
    world.say(f"{setting.place_phrase}, they started with care and cheer.")
    world.say(f"They mixed and they shaped, and they cheered, \"We're near!\"")

    if cook_cfg.id == "grill":
        world.say(f"{name1} said, \"The grill is hot, but I won't feel fright.\"")
        world.say(f"{name2} said, \"I'll hand you the spatula; I'll hold it tight.\"")
    elif cook_cfg.id == "pan":
        world.say(f"{name1} said, \"The pan is slick, so let's not race.\"")
        world.say(f"{name2} said, \"I'll steady the pan and give it space.\"")
    else:
        world.say(f"{name1} said, \"The stove is warm, and the patty will sing.\"")
        world.say(f"{name2} said, \"I'll watch the edges and do my thing.\"")

    world.para()
    world.say(f"{name1} and {name2} worked side by side, a happy pair.")
    world.say(f"{helper_cfg.phrase} helped them move with care.")

    apply_teamwork(world)

    world.para()
    if world.facts.get("teamwork_success"):
        award.meters["won"] += 1
        award.memes["pride"] += 1
        world.say(f"The patty came out golden and good, with a round little sheen.")
        world.say(f"The judges smiled wide and called it supreme.")
        world.say(f"They won {award_cfg.phrase}, and they gave a loud cheer.")
        world.say(f"\"Teamwork makes the dream work!\" they sang bright and clear.")
    else:
        world.say("The patty needed more help, but they did not pout.")
        world.say("They tried again together, and soon it worked out.")
    world.facts["rhyming_cue"] = rhyme_end(cook_cfg, award_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about {f["cook"].label} making {f["patty"].phrase} with teamwork and a dialogue-filled plan.',
        f'Tell a gentle teamwork story that includes the words "award" and "patty" and ends with a happy prize.',
        f'Write a simple rhyming story where two teammates talk, share the job, and win an {f["award"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cook = f["cook"]
    mate = f["mate"]
    helper = f["helper"]
    award = f["award"]
    patty = f["patty"]
    setting = f["setting"]
    cfg = f["cook_cfg"]
    qa = [
        QAItem(
            question=f"What did {cook.label} and {mate.label} try to make {setting.place_phrase}?",
            answer=f"They tried to make {patty.phrase}. They worked together and kept talking so the job could stay smooth and neat.",
        ),
        QAItem(
            question=f"How did {helper.label} help the team?",
            answer=f"{helper.phrase} helped them move with care. That made it easier for {cook.label} and {mate.label} to finish the patty without rushing.",
        ),
        QAItem(
            question=f"What did the children say when they worked together?",
            answer=f"They said they would share the work and keep the beat. Their dialogue showed teamwork, and the teamwork made the cooking go well.",
        ),
    ]
    if f.get("teamwork_success"):
        qa.append(QAItem(
            question=f"What happened at the end when the patty was done?",
            answer=f"They won {award.phrase}. The judges liked the neat patty and the happy teamwork, so the story ended with a bright award.",
        ))
        qa.append(QAItem(
            question=f"Why did the team get the {award.label}?",
            answer=f"They got it because they worked together and did not give up. Each teammate helped, so the patty turned out good enough to earn the award.",
        ))
    else:
        qa.append(QAItem(
            question="What did they do when the patty needed more help?",
            answer="They tried again together instead of pouting. That teamwork helped them finish the job on the next try.",
        ))
    qa.append(QAItem(
        question=f"What kind of cooking did the story use with {cfg.place_word}?",
        answer=f"The story used {cfg.gerund}. It was a warm, careful job that needed steady hands and good teamwork.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people share the job and help one another. When a team works well, the work can feel easier and the result can be better.",
        ),
        QAItem(
            question="What is an award?",
            answer="An award is a prize you get for doing something well. It can be a ribbon, a star, or another special sign of praise.",
        ),
        QAItem(
            question="What is a patty?",
            answer="A patty is a small flat piece of food. People can cook or shape it before serving it hot and tasty.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen", cook="pan", award="blue_ribbon", patty="pea_patty", name1="Mia", type1="girl", name2="Noah", type2="boy", helper="spatula"),
    StoryParams(setting="fair", cook="stove", award="gold_star", patty="bean_patty", name1="Ava", type1="girl", name2="Zoe", type2="girl", helper="towel"),
    StoryParams(setting="yard", cook="grill", award="blue_ribbon", patty="pea_patty", name1="Ben", type1="boy", name2="Leo", type2="boy", helper="oven_mitt"),
]


def explain_rejection() -> str:
    return "(No story: the requested combination is not reasonable for this tiny world.)"


ASP_RULES = r"""
combo(S,C,A) :- setting(S), cook(C), award(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in COOKS:
        lines.append(asp.fact("cook", c))
    for a in AWARDS:
        lines.append(asp.fact("award", a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = py == cl
    try:
        sample = generate(CURATED[0])
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        print(f"SMOKE FAIL: {exc}")
        return 1
    if ok:
        print(f"OK: ASP parity matched {len(py)} combos.")
        return 0
    print("MISMATCH between ASP and Python combo sets.")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.cook not in COOKS or params.award not in AWARDS or params.patty not in PATTIES or params.helper not in TOOLS:
        raise StoryError("Invalid story parameters.")
    world = tell(SETTINGS[params.setting], COOKS[params.cook], AWARDS[params.award], PATTIES[params.patty], TOOLS[params.helper], params.name1, params.type1, params.name2, params.type2)
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
        print(asp_program("#show combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for c in combos:
            print(c)
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
