#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bark_batter_exam_transformation_inner_monologue_myth.py
======================================================================================

A standalone storyworld for a tiny myth-like tale: a young seeker faces an exam,
struggles with a strange battering task, hears an inner monologue, and undergoes
a transformation that proves wisdom has changed them.

The world is deliberately small and classical:
- a named seeker and a mentor
- a sacred place with bark, batter, and an exam
- a transformation triggered by courage, truth, and listening inward

The story samples are generated from state, not swapped templates. The world tracks
physical meters and emotional memes, and the prose reflects those changes.
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
WISDOM_TARGET = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "daughter"}
        male = {"boy", "man", "king", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"elder": "elder", "mentor": "mentor", "oracle": "oracle"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Setting:
    id: str
    place: str
    sacred: str
    trial: str
    bark_phrase: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    use: str
    transforms: bool = False
    flammable: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Transformation:
    id: str
    new_form: str
    signs: str
    gift: str
    cost: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_wisdom(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    if seeker.memes["doubt"] >= THRESHOLD and seeker.memes["inner_voice"] >= THRESHOLD:
        sig = ("wisdom",)
        if sig not in world.fired:
            world.fired.add(sig)
            seeker.memes["wisdom"] += 1
            out.append("__wisdom__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    seeker = world.get("seeker")
    if seeker.memes["wisdom"] < WISDOM_TARGET:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seeker.meters["transformed"] += 1
    seeker.memes["calm"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [Rule("wisdom", "inner", _r_wisdom), Rule("transform", "myth", _r_transform)]


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


def story_can_happen(setting: Setting, batter: Artifact, trial: Artifact) -> bool:
    return "exam" in trial.label and batter.use == "offer" and trial.transforms


def _do_exam(world: World, seeker: Entity, trial: Artifact, narrate: bool = True) -> None:
    seeker.meters["examined"] += 1
    seeker.memes["doubt"] += 1
    seeker.memes["inner_voice"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, seeker: Entity, mentor: Entity, setting: Setting, trial: Artifact, batter: Artifact) -> None:
    seeker.memes["curiosity"] += 1
    mentor.memes["patience"] += 1
    world.say(
        f"In the old {setting.place}, beneath {setting.bark_phrase}, {seeker.id} came to "
        f"{setting.sacred} for the {trial.label}."
    )
    world.say(
        f"{mentor.id} had set out {batter.phrase}, a strange offering for the road ahead."
    )


def fear(world: World, seeker: Entity, setting: Setting, trial: Artifact) -> None:
    seeker.memes["fear"] += 1
    world.say(
        f"The {setting.trial} felt larger than a mountain. {seeker.id} looked at the "
        f"{trial.label} and wondered if {seeker.pronoun()} could pass."
    )


def inner_monologue(world: World, seeker: Entity, setting: Setting, trial: Artifact) -> None:
    seeker.memes["inner_voice"] += 1
    seeker.memes["doubt"] += 1
    world.say(
        f"In {seeker.pronoun('possessive')} heart, {seeker.id} heard a small voice: "
        f'"If you fail the {trial.label}, you will return home empty, but if you stand '
        f'still and listen, the old place may answer."'
    )


def choose_listen(world: World, seeker: Entity, mentor: Entity, batter: Artifact, trial: Artifact) -> None:
    seeker.memes["resolve"] += 1
    world.say(
        f"{seeker.id} breathed in, touched the {batter.label}, and chose to listen "
        f"before acting."
    )
    world.say(
        f'{mentor.id} nodded, as if {seeker.id} had finally heard the hidden rule of the '
        f"{trial.label}."
    )


def transform(world: World, seeker: Entity, trans: Transformation, setting: Setting) -> None:
    seeker.meters["transformed"] += 1
    seeker.memes["wisdom"] += 1
    seeker.memes["calm"] += 1
    world.say(
        f"Then the change came. {seeker.id}'s hands grew steady, {seeker.pronoun('possessive')} "
        f"voice grew clear, and {seeker.pronoun('possessive')} eyes shone with {trans.gift}."
    )
    world.say(
        f"{seeker.id} became {trans.new_form}, {trans.signs}. The {setting.bark_phrase} "
        f"seemed to bow, as though it had known this ending all along."
    )


def resolution(world: World, seeker: Entity, mentor: Entity, trial: Artifact) -> None:
    world.say(
        f"{mentor.id} smiled. {seeker.id} had passed the {trial.label}, not by force, "
        f"but by hearing the true voice within."
    )
    world.say(
        f"At dawn, {seeker.id} stepped away from {trial.label} as someone changed, "
        f"carrying {seeker.pronoun('possessive')} new calm like a lantern."
    )


def tell(setting: Setting, seeker_name: str, seeker_type: str, mentor_name: str,
         mentor_type: str, batter: Artifact, trial: Artifact, trans: Transformation) -> World:
    world = World(setting)
    seeker = world.add(Entity(id=seeker_name, kind="character", type=seeker_type, role="seeker"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=mentor_type, role="mentor"))
    world.add(Entity(id="batter", type="thing", label=batter.label))
    world.add(Entity(id="trial", type="thing", label=trial.label))

    setup(world, seeker, mentor, setting, trial, batter)
    world.para()
    fear(world, seeker, setting, trial)
    inner_monologue(world, seeker, setting, trial)
    choose_listen(world, seeker, mentor, batter, trial)
    _do_exam(world, seeker, trial, narrate=False)
    world.para()
    transform(world, seeker, trans, setting)
    resolution(world, seeker, mentor, trial)

    world.facts.update(
        seeker=seeker,
        mentor=mentor,
        setting=setting,
        batter=batter,
        trial=trial,
        trans=trans,
        outcome="transformed",
        wisdom=seeker.memes["wisdom"],
    )
    return world


SETTINGS = {
    "forest": Setting("forest", "the forest temple", "the hollow stone circle", "exam", "the bark of the ancient tree"),
    "grove": Setting("grove", "the moonlit grove", "the listening arch", "exam", "the bark of the silver oak"),
    "mountain": Setting("mountain", "the mountain shrine", "the wind-carved court", "exam", "the bark of the high pine"),
}

BATTERS = {
    "batter": Artifact("batter", "batter", "a bowl of batter for the sacred cakes", "food", "offer", transforms=False),
    "bark": Artifact("bark", "bark", "a strip of bark wrapped in cloth", "offering", "offer", transforms=False),
    "exam": Artifact("exam", "exam", "the exam itself, sealed in a gold leaf", "trial", "face", transforms=True),
}

TRANSFORMS = {
    "deer": Transformation("deer", "a deer with bright antlers", "its footsteps became soft and sure", "a quiet courage", "the fear of being small"),
    "owl": Transformation("owl", "an owl with gold-feathered wings", "its gaze became deep and wise", "an old wisdom", "the need to rush"),
    "river": Transformation("river", "a river-spirit with silver hands", "its breath became cool and steady", "a clear heart", "the hunger to prove itself"),
}

SEEKER_NAMES = ["Arin", "Mira", "Seth", "Lina", "Ivo", "Nora", "Tavi", "Kora"]
MENTOR_NAMES = ["Elder Rowan", "Aunt Sel", "Old Nera", "Master Iden"]
GENDERS = {"Arin": "boy", "Mira": "girl", "Seth": "boy", "Lina": "girl", "Ivo": "boy", "Nora": "girl", "Tavi": "boy", "Kora": "girl"}



def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for bid, batter in BATTERS.items():
            for tid, trial in BATTERS.items():
                if story_can_happen(setting, batter, trial):
                    combos.append((sid, bid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    batter: str
    trial: str
    seeker: str
    seeker_gender: str
    mentor: str
    mentor_gender: str
    transform: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

CURATED = [
    ("forest", "batter", "exam", "Arin", "owl"),
    ("grove", "bark", "exam", "Mira", "deer"),
    ("mountain", "batter", "exam", "Nora", "river"),
]



def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic story for a young child that includes the words "{f["batter"].label}", "{f["trial"].label}", and "bark".',
        f"Tell a small myth where {f['seeker'].id} faces an {f['trial'].label}, hears an inner monologue, and changes into {f['trans'].new_form}.",
        f'Write a calm legend about {f["mentor"].id} guiding {f["seeker"].id} through the {f["setting"].place} by listening inward.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seeker = f["seeker"]
    mentor = f["mentor"]
    trans = f["trans"]
    trial = f["trial"]
    batter = f["batter"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {seeker.id}, who came to the {setting.place} to face the {trial.label}. {mentor.id} guides {seeker.id} through the mythic test."
        ),
        QAItem(
            question=f"What did {seeker.id} hear inside?",
            answer=f"{seeker.id} heard a small inner monologue that said to listen, stay still, and trust the old place. That quiet voice gave {seeker.id} the courage to continue."
        ),
        QAItem(
            question=f"What changed when {seeker.id} passed the exam?",
            answer=f"{seeker.id} transformed into {trans.new_form}. The change showed that wisdom had grown stronger than fear."
        ),
        QAItem(
            question=f"What were the bark and batter doing in the story?",
            answer=f"The bark marked the ancient setting, and the batter was a strange offering waiting near the test. Together they made the scene feel like an old myth."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is bark?", "Bark is the hard outer skin of a tree. It protects the tree the way a shell protects a seed."),
        QAItem("What is batter?", "Batter is a soft mixture made from flour and liquid. People often cook it into cakes or pancakes."),
        QAItem("What is an exam?", "An exam is a test. It asks someone to show what they know or can do."),
        QAItem("What is a transformation?", "A transformation is a change from one form into another. In myths, it can show a big inner change too."),
        QAItem("What is an inner monologue?", "An inner monologue is the voice of a character's thoughts. It lets us hear what they are telling themselves."),
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
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(out)


def explain_rejection(setting: Setting, batter: Artifact, trial: Artifact) -> str:
    return (
        f"(No story: this myth needs a real turning point. The combination "
        f"of {batter.label} and {trial.label} does not create a meaningful exam, "
        f"so there is no honest transformation to tell.)"
    )


def explain_missing() -> str:
    return "(No story: please choose a setting, a batter, a trial, and a transformation.)"


def outcome_of(params: StoryParams) -> str:
    return "transformed"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BATTERS:
        lines.append(asp.fact("artifact", bid))
    for tid in BATTERS:
        lines.append(asp.fact("trial", tid))
    for tid in TRANSFORMS:
        lines.append(asp.fact("transform", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, B, T) :- setting(S), artifact(B), trial(T), T = "exam".
transformed(T) :- transform(T).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if a - p:
            print("  only in asp:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke-tested normal story generation.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: bark, batter, exam, and transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--batter", choices=BATTERS)
    ap.add_argument("--trial", choices=BATTERS)
    ap.add_argument("--seeker")
    ap.add_argument("--seeker-gender", choices=["boy", "girl"])
    ap.add_argument("--mentor")
    ap.add_argument("--mentor-gender", choices=["boy", "girl"])
    ap.add_argument("--transform", choices=TRANSFORMS)
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
    if args.setting and args.batter and args.trial:
        if args.trial != "exam":
            raise StoryError("(No story: the myth needs an exam as the trial.)")
        if not story_can_happen(SETTINGS[args.setting], BATTERS[args.batter], BATTERS[args.trial]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], BATTERS[args.batter], BATTERS[args.trial]))
    combos = [c for c in valid_combos() if (args.setting is None or c[0] == args.setting) and (args.batter is None or c[1] == args.batter) and (args.trial is None or c[2] == args.trial)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, batter, trial = rng.choice(sorted(combos))
    seeker = args.seeker or rng.choice(SEEKER_NAMES)
    seeker_gender = args.seeker_gender or GENDERS[seeker]
    mentor = args.mentor or rng.choice(MENTOR_NAMES)
    mentor_gender = args.mentor_gender or rng.choice(["boy", "girl"])
    transform = args.transform or rng.choice(list(TRANSFORMS))
    return StoryParams(setting, batter, trial, seeker, seeker_gender, mentor, mentor_gender, transform)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        params.seeker,
        params.seeker_gender,
        params.mentor,
        params.mentor_gender,
        BATTERS[params.batter],
        BATTERS[params.trial],
        TRANSFORMS[params.transform],
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combinations:")
        for item in asp_valid_combos():
            print("  ", item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(s, b, t, seeker, GENDERS[seeker], mentor, "boy", tr))
                   for (s, b, t), (seeker, mentor, tr) in zip(CURATED, [("Arin", "Elder Rowan", "owl"), ("Mira", "Old Nera", "deer"), ("Nora", "Master Iden", "river")])]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
