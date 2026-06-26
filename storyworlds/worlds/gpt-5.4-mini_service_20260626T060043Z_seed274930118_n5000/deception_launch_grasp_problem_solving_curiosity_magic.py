#!/usr/bin/env python3
"""
Standalone story world: a rhyming tale about deception, launch, grasp,
curiosity, magic, and problem solving.

A small child discovers a magical launch toy, learns that a tricky shortcut
doesn't work, and solves the problem by being honest and careful.
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "spark": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "joy": 0.0, "deceit": 0.0, "trust": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    allow_launch: bool = False


@dataclass
class Trick:
    id: str
    label: str
    phrase: str
    lie: str
    truth: str
    launch_word: str
    grasp_word: str
    fix_word: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_notes: list[str] = []

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
        clone.facts = dict(self.facts)
        return clone


def _line(*parts: str) -> str:
    return " ".join(parts).replace("  ", " ").strip()


def _r_launch(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("launch_ready", 0.0) >= THRESHOLD and ("launch", ent.id) not in world.fired:
            world.fired.add(("launch", ent.id))
            ent.meters["distance"] += 1.0
            ent.meters["spark"] += 1.0
            out.append(f"{ent.label or ent.id} soared with a glow and a graceful grace.")
    return out


def _r_grasp(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meters.get("slippery", 0.0) >= THRESHOLD and ("grasp", ent.id) not in world.fired:
            world.fired.add(("grasp", ent.id))
            ent.meters["risk"] += 1.0
            out.append(f"A careful grasp was needed, or the treasure would slip right past.")
    return out


def _r_truth(world: World) -> list[str]:
    hero = next((e for e in world.entities.values() if e.kind == "character"), None)
    if hero and hero.memes.get("deceit", 0.0) >= THRESHOLD and ("truth", hero.id) not in world.fired:
        world.fired.add(("truth", hero.id))
        hero.memes["trust"] += 1.0
        hero.memes["relief"] += 1.0
        return [f"Being honest made the room feel lighter, like moonbeams in lace."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_launch, _r_grasp, _r_truth):
            s = rule(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"launch"}),
    "workshop": Setting(place="the little workshop", indoor=True, affords={"launch"}),
    "hill": Setting(place="the windy hill", indoor=False, affords={"launch"}),
}

ARTIFACTS = {
    "kite": Artifact(
        id="kite",
        label="kite",
        phrase="a ribboned kite",
        region="hands",
        mess="wind-tossed",
        allow_launch=True,
    ),
    "rocket": Artifact(
        id="rocket",
        label="rocket",
        phrase="a shiny toy rocket",
        region="hands",
        mess="smudged",
        allow_launch=True,
    ),
    "lantern": Artifact(
        id="lantern",
        label="lantern",
        phrase="a tiny star lantern",
        region="hands",
        mess="dimmed",
        allow_launch=True,
    ),
}

TRICKS = {
    "moonshine": Trick(
        id="moonshine",
        label="moonshine trick",
        phrase="a glittery moonshine trick",
        lie="It will launch itself if you whisper a fib.",
        truth="It only works if you aim it well and hold it tight.",
        launch_word="launch",
        grasp_word="grasp",
        fix_word="solve",
        keyword="magic",
        tags={"magic", "curiosity", "problem_solving", "deception", "launch", "grasp"},
    ),
}

NAMES = ["Mina", "Leo", "Nori", "Ari", "Zoe", "Milo", "Tess", "Finn"]
TYPES = {"girl": ["Mina", "Nori", "Zoe", "Tess"], "boy": ["Leo", "Ari", "Milo", "Finn"]}


@dataclass
class StoryParams:
    place: str
    artifact: str
    trick: str
    name: str
    gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: deception, launch, grasp, curiosity, magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--trick", choices=TRICKS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def reasonableness_gate(place: str, artifact: str, trick: str) -> None:
    if place not in SETTINGS:
        raise StoryError("Unknown setting.")
    if artifact not in ARTIFACTS:
        raise StoryError("Unknown artifact.")
    if trick not in TRICKS:
        raise StoryError("Unknown trick.")
    if not ARTIFACTS[artifact].allow_launch:
        raise StoryError("That object cannot be launched in this story.")
    if "launch" not in SETTINGS[place].affords:
        raise StoryError("That setting cannot support a launch story.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    artifact = args.artifact or rng.choice(list(ARTIFACTS))
    trick = args.trick or rng.choice(list(TRICKS))
    reasonableness_gate(place, artifact, trick)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(TYPES[gender])
    if name not in NAMES:
        name = rng.choice(TYPES[gender])
    return StoryParams(place=place, artifact=artifact, trick=trick, name=name, gender=gender)


def _intro_line(hero: Entity, trick: Trick, artifact: Artifact) -> str:
    return f"{hero.id} was a curious child with a heart like a bright little spark."


def _second_line(hero: Entity, trick: Trick, artifact: Artifact) -> str:
    return f"{hero.pronoun().capitalize()} loved to ask, to look, and to learn, with wonder in every part."


def tell(setting: Setting, artifact_cfg: Artifact, trick_cfg: Trick, name: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    artifact = world.add(Entity(
        id=artifact_cfg.id,
        type=artifact_cfg.id,
        label=artifact_cfg.label,
        phrase=artifact_cfg.phrase,
        owner=hero.id,
        region=artifact_cfg.region,
    ))
    villain = world.add(Entity(id="trick", kind="thing", type="spell", label=trick_cfg.label))
    world.facts.update(hero=hero, artifact=artifact, trick=trick_cfg, setting=setting)

    world.say(_intro_line(hero, trick_cfg, artifact_cfg))
    world.say(_second_line(hero, trick_cfg, artifact_cfg))
    world.say(f"One night in {setting.place}, {hero.id} found {artifact.phrase}, soft as a song.")
    world.say(f"It glittered with magic, and curiosity said, “Come on, let's see what is wrong and what is strong.”")

    world.para()
    world.say(f"{hero.id} tried a little deception and whispered, “I already know the way.”")
    world.say(f"But the trick only twinkled and tumbled; it would not help the launch at play.")
    hero.memes["deceit"] += 1.0
    hero.memes["curiosity"] += 1.0
    artifact.meters["slippery"] += 1.0
    artifact.meters["launch_ready"] += 1.0
    propagate(world, narrate=False)

    world.say(f"Then {hero.id} made a careful grasp, with both hands snug and true.")
    world.say(f"{hero.id} paused to problem-solve, asking, “What should I do?”")
    world.say(f"{hero.id} noticed the lie was a flimsy disguise; the honest way would do.")
    world.say(f"So {hero.id} said, “I was wrong,” and the magic began to brew.")

    world.para()
    hero.memes["deceit"] = 0.0
    hero.memes["trust"] += 1.0
    hero.memes["joy"] += 1.0
    hero.memes["relief"] += 1.0
    artifact.meters["launch_ready"] = 1.0
    artifact.meters["slippery"] = 0.0
    propagate(world, narrate=False)

    world.say(f"With an honest grasp and a clever plan, {hero.id} gave the toy a spin.")
    world.say(f"It launched in a shining arc through the air, and the whole room wore a grin.")
    world.say(f"{hero.id} laughed, “Curiosity helped me see; problem solving helped me win.”")
    world.say(f"And magic, once wobbly, danced like a star, as bright as a jewel in tin.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    artifact = f["artifact"]
    trick = f["trick"]
    return [
        f'Write a short rhyming story for children about {hero.id}, a magical {artifact.label}, and a tricky {trick.keyword} problem.',
        f"Tell a gentle rhyme where a child learns that deception does not help a launch, but a careful grasp and honest thinking do.",
        f"Write a simple magical story with curiosity, problem solving, and a happy ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    artifact: Entity = f["artifact"]
    trick: Trick = f["trick"]
    return [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {artifact.phrase}, and it sparkled with magic.",
        ),
        QAItem(
            question=f"What problem did {hero.id} face with the {artifact.label}?",
            answer=f"The trick was that the toy would not truly launch when {hero.id} used deception instead of a real plan.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} stopped pretending, told the truth, used a careful grasp, and then the launch worked.",
        ),
        QAItem(
            question=f"Which feelings helped the story move forward?",
            answer="Curiosity helped the child ask questions, and problem solving helped find the honest fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions, explore, and learn new things.",
        ),
        QAItem(
            question="What is a grasp?",
            answer="A grasp is a firm hold with your hand or hands.",
        ),
        QAItem(
            question="What is a launch?",
            answer="A launch is when something is sent out or sent up, like a toy rocket flying away.",
        ),
        QAItem(
            question="What is deception?",
            answer="Deception is trying to make someone believe something that is not true.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully to find a way to fix a hard situation.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is a special made-up force that can make surprising and wonderful things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% Inline declarative twin of the reasonableness gate.
launch_story(P,A,T) :- setting(P), artifact(A), trick(T), affords(P,launch), launchable(A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        if a.allow_launch:
            lines.append(asp.fact("launchable", aid))
    for tid in TRICKS:
        lines.append(asp.fact("trick", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show launch_story/3."))
    clingo_set = set(asp.atoms(model, "launch_story"))
    python_set = set((p, a, t) for p in SETTINGS for a in ARTIFACTS for t in TRICKS if "launch" in SETTINGS[p].affords and ARTIFACTS[a].allow_launch)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show launch_story/3."))
    return sorted(set(asp.atoms(model, "launch_story")))


CURATED = [
    StoryParams(place="garden", artifact="kite", trick="moonshine", name="Mina", gender="girl"),
    StoryParams(place="workshop", artifact="rocket", trick="moonshine", name="Leo", gender="boy"),
    StoryParams(place="hill", artifact="lantern", trick="moonshine", name="Nori", gender="girl"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ARTIFACTS[params.artifact], TRICKS[params.trick], params.name, params.gender)
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
        print(asp_program("#show launch_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} launch-compatible combos:\n")
        for c in combos:
            print(" ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.artifact} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
