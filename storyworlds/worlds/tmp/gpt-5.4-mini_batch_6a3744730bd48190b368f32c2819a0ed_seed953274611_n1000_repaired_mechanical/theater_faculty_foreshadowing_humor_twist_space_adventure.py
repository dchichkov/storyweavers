#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/theater_faculty_foreshadowing_humor_twist_space_adventure.py
===========================================================================================

A small, standalone story world about a school theater crew on a space-adventure
set. A crew of faculty and students stages a tiny play, a foreshadowed hiccup
builds, the mishap lands with humor, and a twist changes what the "problem" was
really about. The ending proves something has changed in the world, not just in
the wording.

The seed words are "theater" and "faculty"; the style leans Space Adventure,
with foreshadowing, humor, and a twist.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/theater_faculty_foreshadowing_humor_twist_space_adventure.py
    python storyworlds/worlds/gpt-5.4-mini/theater_faculty_foreshadowing_humor_twist_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4-mini/theater_faculty_foreshadowing_humor_twist_space_adventure.py --qa
    python storyworlds/worlds/gpt-5.4-mini/theater_faculty_foreshadowing_humor_twist_space_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MOOD_GOOD = 1.0


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
        female = {"girl", "mother", "woman", "actress"}
        male = {"boy", "father", "man", "actor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class CastChoice:
    id: str
    label: str
    kind: str
    type: str
    role: str
    trait: str
    clue: str
    memory: str
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
class SetChoice:
    id: str
    stage: str
    backdrop: str
    prop: str
    hazard: str
    safe_fix: str
    foreshadow: str
    humorous_detail: str
    twist_hint: str
    twist_reveal: str
    kind: str = "set"
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
class StoryParams:
    set_id: str
    captain: str
    captain_type: str
    crewmate: str
    crewmate_type: str
    faculty_id: str
    prop_on_stage: str
    hazard_id: str
    fix_id: str
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
        clone.entities = {k: Entity(**{**v.__dict__, "meters": defaultdict(float, v.meters), "memes": defaultdict(float, v.memes)}) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETS = {
    "moonstage": SetChoice(
        id="moonstage",
        stage="theater",
        backdrop="a silver moon base made of cardboard walls",
        prop="a glowing moon rock",
        hazard="a loose cable",
        safe_fix="a tape strip",
        foreshadow="a cable kept winking like it had a secret",
        humorous_detail="the captain's helmet was a salad bowl with stars drawn on it",
        twist_hint="the stage map kept pointing to the faculty lounge",
        twist_reveal="the 'alien' alarm was just the faculty calling for the missing cocoa",
    ),
    "cometdeck": SetChoice(
        id="cometdeck",
        stage="theater",
        backdrop="a spaceship deck with paper stars taped to the rafters",
        prop="a comet prism",
        hazard="a squeaky robot wheel",
        safe_fix="a wheel lock",
        foreshadow="one wheel kept squeaking in a tiny, nervous voice",
        humorous_detail="every time the robot rolled, it sounded like a duck learning opera",
        twist_hint="the big control panel had a label that said FACULTY ONLY",
        twist_reveal="the 'mystery signal' was actually the faculty lunch timer beeping under a prop crate",
    ),
    "stardock": SetChoice(
        id="stardock",
        stage="theater",
        backdrop="a dock on the edge of a cardboard galaxy",
        prop="a star compass",
        hazard="a dangling curtain cord",
        safe_fix="a clip",
        foreshadow="the curtain cord swung like it wanted to wave hello first",
        humorous_detail="the spaceship's captain kept saluting the snack table by mistake",
        twist_hint="a chalk arrow pointed from the stage to the faculty office",
        twist_reveal="the supposed space monster was only the faculty projector warming up behind the curtain",
    ),
}

FACULTY = {
    "prof_orbit": CastChoice("ProfOrbit", "Professor Orbit", "character", "woman", "faculty", "careful", "kept glancing at the cable", "had already packed tape"),
    "dr_quasar": CastChoice("DrQuasar", "Doctor Quasar", "character", "man", "faculty", "wry", "smiled at the squeaky wheel", "had a wrench in the pocket"),
    "ms_nova": CastChoice("MsNova", "Ms. Nova", "character", "woman", "faculty", "calm", "noticed the curtain cord", "had a bright little clip"),
}

KIDS = {
    "luna": CastChoice("Luna", "Luna", "character", "girl", "captain", "bold", "wanted the biggest adventure", "had sticky star stickers on her sleeves"),
    "milo": CastChoice("Milo", "Milo", "character", "boy", "crewmate", "curious", "kept asking what the buttons did", "had a toy wrench"),
    "tess": CastChoice("Tess", "Tess", "character", "girl", "crewmate", "bright", "laughed at the tiny accidents", "had glitter on her nose"),
}


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_humor(world: World) -> list[str]:
    out = []
    for e in list(world.entities.values()):
        if e.meters["amused"] >= THRESHOLD and ("humor", e.id) not in world.fired:
            world.fired.add(("humor", e.id))
            for kid in list(world.entities.values()):
                if kid.kind == "character":
                    kid.memes["joy"] += 0.5
            out.append("__humor__")
    return out


def _r_tension(world: World) -> list[str]:
    out = []
    if world.facts.get("hazard_seen") and ("tension", "stage") not in world.fired:
        world.fired.add(("tension", "stage"))
        world.get("stage").meters["risk"] += 1
        for kid in list(world.entities.values()):
            if kid.kind == "character":
                kid.memes["alert"] += 1
        out.append("__tension__")
    return out


CAUSAL_RULES = [Rule("humor", _r_humor), Rule("tension", _r_tension)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETS.items():
        for fid in FACULTY:
            for kid in KIDS:
                for fix in ("tape", "wrench", "clip"):
                    combos.append((sid, fid, kid, fix))
    return combos


def reasonableness_gate(set_id: str, faculty_id: str, prop_on_stage: str, fix_id: str) -> bool:
    s = SETS[set_id]
    return s.hazard and fix_id in {"tape", "wrench", "clip"} and prop_on_stage


def plot_sync(world: World, s: SetChoice, faculty: CastChoice, captain: CastChoice, crew: CastChoice) -> None:
    world.say(
        f"In the theater at {s.stage}, {captain.id} and {crew.id} helped build "
        f"{s.backdrop}. {s.foreshadow}."
    )
    world.say(
        f'{faculty.label} crossed the stage with a clipboard and a smile. '
        f'"Tonight we launch a tiny space story," {faculty.pronoun()} said.'
    )


def joke(world: World, s: SetChoice, captain: CastChoice, crew: CastChoice) -> None:
    captain.memes["amused"] += 1
    crew.memes["amused"] += 1
    world.say(
        f'{captain.id} posed beside {s.prop}, but {s.humorous_detail}. '
        f'{crew.id} laughed so hard {crew.pronoun()} nearly dropped the prop.'
    )


def warn(world: World, s: SetChoice, faculty: CastChoice) -> None:
    world.facts["hazard_seen"] = True
    world.say(
        f'{faculty.label} pointed at the stage and said, "Careful. That {s.hazard} '
        f'is acting like it knows something."'
    )


def twist_build(world: World, s: SetChoice, crew: CastChoice) -> None:
    world.say(
        f"{crew.id} noticed {s.twist_hint}. The arrow looked odd, almost like a joke "
        f"someone had left on purpose."
    )


def fix(world: World, s: SetChoice, faculty: CastChoice) -> None:
    stage = world.get("stage")
    stage.meters["risk"] = 0.0
    world.say(
        f'{faculty.label} used {s.safe_fix} to make the wobble stop. '
        f'The set stood straight again, and the crew could breathe.'
    )


def reveal(world: World, s: SetChoice, faculty: CastChoice, captain: CastChoice, crew: CastChoice) -> None:
    faculty.memes["pride"] += 1
    captain.memes["understanding"] += 1
    crew.memes["understanding"] += 1
    world.say(
        f'Then came the twist: {s.twist_reveal}. {faculty.label} laughed first, '
        f'and then the whole theater laughed too.'
    )
    world.say(
        f'"So the big space mystery was really a snack problem," {captain.id} said. '
        f'"The best kind," {crew.id} said, still giggling.'
    )


def ending(world: World, s: SetChoice, captain: CastChoice, crew: CastChoice, faculty: CastChoice) -> None:
    captain.memes["joy"] += 1
    crew.memes["joy"] += 1
    world.say(
        f'By the end, the theater lights glowed on the safe set, the faculty '
        f'clipboard was covered in doodles, and {captain.id} and {crew.id} '
        f'bowed like true space heroes.'
    )


def tell(params: StoryParams) -> World:
    s = SETS[params.set_id]
    faculty = FACULTY[params.faculty_id]
    captain = KIDS[params.captain]
    crew = KIDS[params.crewmate]

    world = World()
    world.add(Entity(id="stage", kind="thing", type="set", label=s.stage))
    world.add(Entity(id=s.prop, kind="thing", type="prop", label=s.prop))
    world.add(Entity(id=s.hazard, kind="thing", type="hazard", label=s.hazard))
    world.add(Entity(id=s.safe_fix, kind="thing", type="tool", label=s.safe_fix))
    world.add(Entity(id=faculty.id, kind="character", type=faculty.type, label=faculty.label, role=faculty.role))
    world.add(Entity(id=captain.id, kind="character", type=captain.type, label=captain.label, role=captain.role))
    world.add(Entity(id=crew.id, kind="character", type=crew.type, label=crew.label, role=crew.role))

    plot_sync(world, s, faculty, captain, crew)
    world.para()
    joke(world, s, captain, crew)
    warn(world, s, faculty)
    twist_build(world, s, crew)
    propagate(world, narrate=False)
    world.para()
    fix(world, s, faculty)
    reveal(world, s, faculty, captain, crew)
    ending(world, s, captain, crew, faculty)

    world.facts.update(
        set=s, faculty=faculty, captain=captain, crew=crew,
        hazard=params.hazard_id, fix=params.fix_id, prop=params.prop_on_stage,
        outcome="twist",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s = f["set"]
    return [
        f'Write a space-adventure story that includes the words "theater" and "faculty".',
        f"Tell a funny school-theater story where {f['faculty'].label} helps two kids on a space set, and a small twist turns into a laugh.",
        f"Write a short story with foreshadowing, humor, and a twist set in {s.backdrop}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    s = f["set"]
    faculty = f["faculty"]
    captain = f["captain"]
    crew = f["crew"]
    return [
        QAItem(
            question="What were the kids doing in the theater?",
            answer=f"They were building a tiny space adventure on the theater stage. They wanted the set to feel big and exciting, even though it was made from cardboard and tape."
        ),
        QAItem(
            question=f"What warning did {faculty.label} give?",
            answer=f"{faculty.label} warned them that the hazard on stage should be watched closely. The warning mattered because the story had already shown a clue that the problem was about to appear."
        ),
        QAItem(
            question="What was the twist at the end?",
            answer=f"The twist was that the scary-sounding problem was not an enemy at all. It turned out to be something ordinary from the faculty side of the theater, which made everyone laugh."
        ),
        QAItem(
            question=f"How did {captain.id} feel at the end?",
            answer=f"{captain.id} felt proud and amused, because the stage was safe again and the whole mystery had turned into a joke. The crew could bow happily instead of worrying."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is theater?",
            answer="Theater is a place where people act out stories on a stage for an audience. It can use costumes, props, and lights to make the story feel real."
        ),
        QAItem(
            question="Who are faculty?",
            answer="Faculty are the teachers and staff who work at a school or college. They help students learn and keep school events organized."
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a clue that hints something will happen later in the story. It helps readers feel a small tingle of suspense before the surprise arrives."
        ),
        QAItem(
            question="Why do stories use humor?",
            answer="Humor gives the audience a chance to smile or laugh. It can make a tense moment feel lighter and more fun."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(set_id="moonstage", captain="Luna", captain_type="girl", crewmate="Milo", crewmate_type="boy", faculty_id="prof_orbit", prop_on_stage="moon rock", hazard_id="loose cable", fix_id="tape"),
    StoryParams(set_id="cometdeck", captain="Tess", captain_type="girl", crewmate="Milo", crewmate_type="boy", faculty_id="dr_quasar", prop_on_stage="comet prism", hazard_id="squeaky wheel", fix_id="wrench"),
    StoryParams(set_id="stardock", captain="Luna", captain_type="girl", crewmate="Tess", crewmate_type="girl", faculty_id="ms_nova", prop_on_stage="star compass", hazard_id="curtain cord", fix_id="clip"),
]


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this theater setup needs a sensible stage hazard and a matching fix.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETS.items():
        lines.append(asp.fact("set", sid))
        lines.append(asp.fact("hazard", s.hazard))
        lines.append(asp.fact("fix", s.safe_fix))
    for fid in FACULTY:
        lines.append(asp.fact("faculty", fid))
    for kid in KIDS:
        lines.append(asp.fact("kid", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, F, K, X) :- set(S), faculty(F), kid(K), fix(X).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure theater storyworld with faculty, foreshadowing, humor, and twist.")
    ap.add_argument("--set", choices=SETS)
    ap.add_argument("--faculty", choices=FACULTY)
    ap.add_argument("--captain", choices=KIDS)
    ap.add_argument("--crewmate", choices=KIDS)
    ap.add_argument("--fix", choices=["tape", "wrench", "clip"])
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
    set_id = args.set or rng.choice(list(SETS))
    faculty_id = args.faculty or rng.choice(list(FACULTY))
    captain = args.captain or rng.choice(list(KIDS))
    crew = args.crewmate or rng.choice([k for k in KIDS if k != captain])
    fix_id = args.fix or rng.choice(["tape", "wrench", "clip"])
    prop_on_stage = "moon rock" if set_id == "moonstage" else ("comet prism" if set_id == "cometdeck" else "star compass")
    if not reasonableness_gate(set_id, faculty_id, prop_on_stage, fix_id):
        raise StoryError(explain_rejection(StoryParams(set_id, captain, KIDS[captain].type, crew, KIDS[crew].type, faculty_id, prop_on_stage, "hazard", fix_id)))
    return StoryParams(
        set_id=set_id,
        captain=captain,
        captain_type=KIDS[captain].type,
        crewmate=crew,
        crewmate_type=KIDS[crew].type,
        faculty_id=faculty_id,
        prop_on_stage=prop_on_stage,
        hazard_id=SETS[set_id].hazard,
        fix_id=fix_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.set_id not in SETS:
        raise StoryError("unknown set")
    if params.faculty_id not in FACULTY:
        raise StoryError("unknown faculty")
    if params.captain not in KIDS or params.crewmate not in KIDS:
        raise StoryError("unknown kid")
    if params.fix_id not in {"tape", "wrench", "clip"}:
        raise StoryError("unknown fix")
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} combos")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
