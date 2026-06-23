#!/usr/bin/env python3
"""
storyworlds/worlds/hungry_auditorium_pulley_suspense_humor_teamwork_comedy.py
==============================================================================

A standalone story world for a small comedy in an auditorium: a hungry child,
a squeaky pulley, a tense moment, and a teamwork fix that turns suspense into
laughs.

Seed premise:
- Words: hungry, auditorium, pulley
- Features: Suspense, Humor, Teamwork
- Style: Comedy

The world is built around a small rehearsal auditorium where a snack box gets
stuck on a pulley above the stage. A hungry child wants the treats, the pulley
creates suspense, and a few helpers have to work together to bring the snacks
down without making a mess.

The story is state-driven:
- hunger and anticipation rise,
- the stuck pulley introduces suspense,
- a clumsy but clever teamwork plan resolves the problem,
- the ending proves the snack box is safely down and everyone is laughing.

This file follows the Storyweavers contract:
- stdlib-only script
- imports results eagerly
- imports asp lazily in ASP helpers
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    suspended: bool = False
    helper: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    echo: str


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    crunch: str
    type: str = "snack"


@dataclass
class Rig:
    id: str
    label: str
    verb: str
    squeak: str
    rescue_phrase: str
    twist: str
    safe: bool = True


@dataclass
class StoryParams:
    setting: str
    snack: str
    rig: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.room: str = setting.place

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


SETTINGS = {
    "auditorium": Setting(
        id="auditorium",
        place="the auditorium",
        detail="The stage lights glowed softly, and the seats made a neat little sea of red.",
        echo="The big room echoed every whisper and every squeaky wheel.",
    ),
    "backstage": Setting(
        id="backstage",
        place="backstage",
        detail="Curtains hung like sleepy giants, and a prop table waited by the wall.",
        echo="Every tiny sound bounced around the wings.",
    ),
}

SNACKS = {
    "cookies": Snack(
        id="cookies",
        label="cookies",
        phrase="a tin of chocolate chip cookies",
        smell="sweet",
        crunch="crisp",
    ),
    "pretzels": Snack(
        id="pretzels",
        label="pretzels",
        phrase="a bag of pretzels",
        smell="salty",
        crunch="twisty",
    ),
    "apples": Snack(
        id="apples",
        label="apples",
        phrase="a box of apple slices",
        smell="fresh",
        crunch="juicy",
    ),
    "muffins": Snack(
        id="muffins",
        label="muffins",
        phrase="a tray of blueberry muffins",
        smell="warm",
        crunch="soft",
    ),
}

RIGS = {
    "flyrope": Rig(
        id="flyrope",
        label="the pulley rope",
        verb="pull the snack box down",
        squeak="eeek",
        rescue_phrase="carefully tugged the rope together",
        twist="The rope jumped, paused, and then slid in tiny little steps.",
        safe=True,
    ),
    "greenroom": Rig(
        id="greenroom",
        label="the greenroom lift line",
        verb="lower the basket safely",
        squeak="scree",
        rescue_phrase="held the line steady and counted together",
        twist="The basket wobbled like a jellyfish before settling down.",
        safe=True,
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Zoe", "Ava", "Ivy"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Noah", "Owen"]
TRAITS = ["curious", "cheerful", "silly", "brave", "patient", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for snack in SNACKS:
            for rig in RIGS:
                combos.append((setting, snack, rig))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _setup_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if params.rig not in RIGS:
        raise StoryError("Unknown pulley rig.")
    setting = SETTINGS[params.setting]
    snack = SNACKS[params.snack]
    rig = RIGS[params.rig]
    world = World(setting)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    box = world.add(Entity(
        id="snack_box",
        type="thing",
        label=snack.label,
        phrase=snack.phrase,
        suspended=True,
        location="above the stage",
    ))
    pulley = world.add(Entity(
        id="pulley",
        type="thing",
        label="pulley",
        phrase="a squeaky pulley",
        suspended=True,
        helper=False,
        location="high over the stage",
    ))
    world.facts = {
        "setting": setting,
        "snack": snack,
        "rig": rig,
        "hero": hero,
        "helper": helper,
        "parent": parent,
        "box": box,
        "pulley": pulley,
        "resolved": False,
        "squeak": rig.squeak,
    }
    return world


def _r_hunger(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    snack = world.facts["snack"]
    if hero.memes["hungry"] < THRESHOLD:
        return out
    sig = ("hunger_notice", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["hope"] += 0.5
    out.append(f"{hero.id}'s stomach gave a tiny grumble at the smell of {snack.smell} snacks.")
    return out


def _r_suspense(world: World) -> list[str]:
    out = []
    box = world.facts["box"]
    if box.meters["stuck"] < THRESHOLD:
        return out
    sig = ("suspense", box.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["tension"] = "high"
    out.append("The box hung there, just out of reach, and everyone held their breath.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out = []
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    box = world.facts["box"]
    pulley = world.facts["pulley"]
    if not world.facts.get("resolved"):
        return out
    sig = ("teamwork", box.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    box.meters["stuck"] = 0
    pulley.meters["moving"] += 1
    out.append("Together, they tugged the rope in the right order, and the box finally slid down.")
    return out


CAUSAL_RULES = [
    _r_hunger,
    _r_suspense,
    _r_teamwork,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_stuck(world: World) -> bool:
    sim = world.copy()
    sim.facts["box"].meters["stuck"] = 1
    propagate(sim, narrate=False)
    return sim.facts["box"].meters["stuck"] >= THRESHOLD


def tell(setting: Setting, snack: Snack, rig: Rig, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, parent_gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_gender, label="the parent"))
    box = world.add(Entity(id="snack_box", type="thing", label=snack.label, phrase=snack.phrase, suspended=True))
    pulley = world.add(Entity(id="pulley", type="thing", label="pulley", phrase="a squeaky pulley", suspended=True))
    hero.memes["hungry"] = 1
    helper.memes["curiosity"] = 1
    world.facts = {
        "setting": setting,
        "snack": snack,
        "rig": rig,
        "hero": hero,
        "helper": helper,
        "parent": parent,
        "box": box,
        "pulley": pulley,
        "resolved": False,
        "trait": trait,
    }

    world.say(f"In {setting.place}, {hero.id} and {helper.id} were getting ready for a small show.")
    world.say(setting.detail)
    world.say(f"{hero.id} was hungry, and the smell of {snack.phrase} drifted through the {setting.id}.")

    world.para()
    world.say(f"Then they noticed {rig.label} hanging high above the stage.")
    box.meters["stuck"] = 1
    pulley.meters["stuck"] = 1
    world.say(f"The {rig.label} gave a nervous little {rig.squeak}, and {rig.twist}")
    if predict_stuck(world):
        propagate(world, narrate=True)

    world.para()
    hero.memes["want"] += 1
    helper.memes["idea"] += 1
    world.say(f"{hero.id} pointed up and said, \"We could use the {rig.label} to get the snacks down!\"")
    world.say(f"{helper.id} grinned. \"Only if we do it together and do not bonk anyone on the head.\"")
    world.say(f"The parent watched, half worried and half amused, as the pulley line swayed like a lazy vine.")

    world.para()
    world.say(f"{hero.id} held one side of the rope, {helper.id} held the other, and the parent counted the pulls.")
    world.say(f"On three, they {rig.rescue_phrase}.")
    world.facts["resolved"] = True
    propagate(world, narrate=False)
    world.say(f"With one last tug, the box came down, and the whole room let out a laugh.")

    world.para()
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    box.meters["stuck"] = 0
    world.say(f"The {snack.label} box landed safely on the table, and the hungry pair shared the first bites.")
    world.say(f"The auditorium smelled sweet and warm, and even the pulley looked relieved to be finished.")
    world.facts["outcome"] = "resolved"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    rig = f["rig"]
    setting = f["setting"]
    return [
        f'Write a comedy story for a 3-to-5-year-old set in {setting.place} about a hungry child, a pulley, and a team that works together.',
        f"Tell a suspenseful-but-funny story where {hero.id} is hungry in {setting.place}, {rig.label} squeaks overhead, and {helper.id} helps bring {snack.phrase} down.",
        f'Write a short teamwork story that includes the words "hungry", "auditorium", and "pulley", and ends with everyone laughing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    snack = f["snack"]
    rig = f["rig"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Why was {hero.id} looking up in {setting.place}?",
            answer=f"{hero.id} was hungry and wanted {snack.phrase}. The snack box was hanging high up on the pulley, so the treats were not easy to reach.",
        ),
        QAItem(
            question=f"What made the moment feel suspenseful near the pulley?",
            answer=f"The snack box was stuck above the stage and the pulley kept squeaking. Everyone had to wait and watch while {hero.id} and {helper.id} figured out how to get it down safely.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They worked together and pulled the rope in the right order while the parent counted. That teamwork helped the snack box slide down without anyone getting hurt.",
        ),
    ]
    if world.facts.get("outcome") == "resolved":
        qa.append(
            QAItem(
                question=f"What changed by the end of the story?",
                answer=f"The snack box was no longer stuck, and the hungry children could share the snacks at the table. The scary squeak turned into a silly little laugh once the pulley was finished helping.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an auditorium?",
            answer="An auditorium is a big room where people sit and listen to a show, a speech, or music.",
        ),
        QAItem(
            question="What is a pulley?",
            answer="A pulley is a wheel with a rope or line that helps lift or lower something heavy or high up.",
        ),
        QAItem(
            question="What does it mean to be hungry?",
            answer="Being hungry means your body wants food and your stomach is asking for a meal or a snack.",
        ),
        QAItem(
            question="Why does teamwork help?",
            answer="Teamwork helps because different people can do different jobs together, and the job often gets done faster and safer.",
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
        if e.suspended:
            bits.append("suspended=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="auditorium", snack="cookies", rig="flyrope", hero="Mia", hero_gender="girl", helper="Leo", helper_gender="boy", parent="mother", trait="silly"),
    StoryParams(setting="auditorium", snack="pretzels", rig="greenroom", hero="Nora", hero_gender="girl", helper="Eli", helper_gender="boy", parent="father", trait="curious"),
    StoryParams(setting="backstage", snack="muffins", rig="flyrope", hero="Finn", hero_gender="boy", helper="Ava", helper_gender="girl", parent="mother", trait="bouncy"),
    StoryParams(setting="backstage", snack="apples", rig="greenroom", hero="Zoe", hero_gender="girl", helper="Noah", helper_gender="boy", parent="father", trait="cheerful"),
]


def valid_story_combo(setting: str, snack: str, rig: str) -> bool:
    return setting in SETTINGS and snack in SNACKS and rig in RIGS


def explain_rejection() -> str:
    return "(No story: the requested choices do not fit this little auditorium comedy.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: hungry auditorium pulley comedy with teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--rig", choices=RIGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.snack is None or c[1] == args.snack)
              and (args.rig is None or c[2] == args.rig)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, snack, rig = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or choose_name(rng, hero_gender)
    helper = args.helper or choose_name(rng, helper_gender)
    if helper == hero:
        helper = choose_name(rng, "boy" if helper_gender == "boy" else "girl")
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, snack=snack, rig=rig, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.snack not in SNACKS or params.rig not in RIGS:
        raise StoryError(explain_rejection())
    world = tell(SETTINGS[params.setting], SNACKS[params.snack], RIGS[params.rig], params.hero, params.hero_gender, params.helper, params.helper_gender, params.parent, params.trait)
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


ASP_RULES = r"""
stuck(B) :- box(B), suspended(B).
suspense(B) :- stuck(B), pulley(P), squeaks(P).
teamwork(H, K) :- hero(H), helper(K), resolved.
valid(S, N, R) :- setting(S), snack(N), rig(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in SNACKS:
        lines.append(asp.fact("snack", nid))
    for rid in RIGS:
        lines.append(asp.fact("rig", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos:")
        print(" only python:", sorted(py - cl))
        print(" only clingo:", sorted(cl - py))
    # smoke test ordinary generation and emit
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=True, qa=True)
    if not buf.getvalue().strip():
        ok = False
        print("Smoke test failed: no output.")
    if ok:
        print(f"OK: verify passed ({len(py)} combos, smoke test succeeded).")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (setting, snack, rig) combos:")
        for s, n, r in asp_valid_combos():
            print(f"  {s:10} {n:10} {r}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.helper}: {p.snack} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
