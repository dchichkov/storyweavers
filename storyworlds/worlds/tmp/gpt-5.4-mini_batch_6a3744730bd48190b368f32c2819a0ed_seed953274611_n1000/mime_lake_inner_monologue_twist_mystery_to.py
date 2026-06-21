#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mime_lake_inner_monologue_twist_mystery_to.py
===============================================================================

A small fable-like storyworld about a mime, a lake, a mystery to solve, and an
inner-monologue twist: the silent mime suspects the wrong thing, then discovers
the real cause, and the village learns a kinder lesson.

The world is built around a simple simulated premise:
- a mime is hired to "help" at a lake festival,
- a strange silence and a missing bell create a mystery,
- the mime's inner monologue points toward one suspect,
- the twist reveals a harmless cause,
- the truth turns the mood from suspicion to understanding.

This script follows the Storyweavers contract:
- stdlib-only
- typed entities with meters and memes
- state-driven prose
- QA from world state, not from rendered English
- Python reasonableness gate plus an inline ASP twin
- verify mode checks ASP parity and a normal generate smoke test
"""

from __future__ import annotations

import argparse
import copy
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"presence": 0.0}
        if not self.memes:
            self.memes = {"calm": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    lake_detail: str
    law: str


@dataclass
class Mystery:
    id: str
    missing: str
    suspect: str
    clue: str
    true_cause: str
    twist: str
    lesson: str


@dataclass
class Counterpart:
    id: str
    label: str
    role: str
    makes_noise: bool = False
    harmless: bool = False


@dataclass
class StoryParams:
    setting: str
    mystery: str
    mime_name: str
    mime_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_worry(world: World) -> list[str]:
    out = []
    if world.get("mime").memes.get("suspicion", 0.0) >= THRESHOLD:
        if "fear" not in world.fired:
            world.fired.add(("fear",))
            world.get("mime").memes["fear"] = world.get("mime").memes.get("fear", 0.0) + 1
            out.append("__fear__")
    return out


def _r_calm(world: World) -> list[str]:
    out = []
    if world.get("helper").memes.get("truth", 0.0) >= THRESHOLD and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        world.get("mime").memes["calm"] = world.get("mime").memes.get("calm", 0.0) + 1
        out.append("__calm__")
    return out


def _r_community(world: World) -> list[str]:
    out = []
    if world.get("mime").memes.get("clarity", 0.0) >= THRESHOLD and ("community",) not in world.fired:
        world.fired.add(("community",))
        world.get("villagers").memes["trust"] = world.get("villagers").memes.get("trust", 0.0) + 1
        out.append("__trust__")
    return out


CAUSAL_RULES = [_r_worry, _r_calm, _r_community]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for t in produced:
            world.say(t)
    return produced


def mystery_is_reasonable(setting: Setting, mystery: Mystery) -> bool:
    return "lake" in setting.place and bool(mystery.suspect) and bool(mystery.true_cause)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if mystery_is_reasonable(setting, mystery):
                combos.append((sid, mid))
    return combos


def predict(world: World, mystery: Mystery) -> dict:
    sim = world.copy()
    sim.get("mime").memes["suspicion"] = 1.0
    if mystery.suspect == "water":
        sim.get("mime").memes["clarity"] = 0.0
    return {"fear": sim.get("mime").memes.get("fear", 0.0), "trust": sim.get("villagers").memes.get("trust", 0.0)}


def setup(world: World, mime: Entity, helper: Entity, mystery: Mystery) -> None:
    mime.memes["curiosity"] = 1.0
    mime.memes["suspicion"] = 0.0
    helper.memes["worry"] = 1.0
    world.say(
        f"At {world.setting.place}, where the {world.setting.lake_detail}, "
        f"{mime.id} the mime came with {helper.id} to help the village."
    )
    world.say(
        f"The villagers had a small mystery to solve: {mystery.missing} had gone missing before the lake feast."
    )


def suspect(world: World, mime: Entity, mystery: Mystery) -> None:
    mime.memes["suspicion"] += 1.0
    world.say(
        f"{mime.id} looked at the quiet water and felt an inner thought begin: "
        f'"If {mystery.missing} is gone, then the lake must have taken it."'
    )
    world.say(
        f"{mime.id} held that worry in silence, because mimes speak with their hands and with their hearts."
    )


def clue(world: World, helper: Entity, mystery: Mystery) -> None:
    helper.memes["truth"] += 1.0
    world.say(
        f"Then {helper.id} pointed to {mystery.clue}, and the villagers noticed a simple thing."
    )


def twist(world: World, mime: Entity, mystery: Mystery) -> None:
    mime.memes["clarity"] += 1.0
    world.say(
        f"The twist came softly: {mystery.twist}"
    )
    world.say(
        f"{mime.id}'s inner monologue changed at once. The lake had not stolen anything; {mystery.true_cause}."
    )


def resolve(world: World, mime: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(
        f"{mime.id} did not accuse the lake. Instead {mime.id} bowed, pointed kindly toward the clue, "
        f"and the village solved the mystery together."
    )
    world.say(
        f"By evening, {mystery.missing} was found, and the feast shone brighter because everyone had learned {mystery.lesson}."
    )
    mime.memes["peace"] = 1.0
    helper.memes["relief"] = 1.0


def tell(setting: Setting, mystery: Mystery, mime_name: str, mime_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    mime = world.add(Entity(id="mime", kind="character", type=mime_gender, label=mime_name, role="mime"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    villagers = world.add(Entity(id="villagers", kind="character", type="thing", label="the villagers", role="group"))
    bell = world.add(Entity(id="bell", kind="thing", type="thing", label=mystery.missing, role="object"))

    setup(world, mime, helper, mystery)
    world.para()
    suspect(world, mime, mystery)
    clue(world, helper, mystery)
    world.para()
    twist(world, mime, mystery)
    resolve(world, mime, helper, mystery)

    world.facts.update(
        mime=mime,
        helper=helper,
        villagers=villagers,
        bell=bell,
        setting=setting,
        mystery=mystery,
        outcome="solved",
    )
    return world


SETTINGS = {
    "moonlit_lake": Setting(
        id="moonlit_lake",
        place="the moonlit lake",
        mood="quiet",
        lake_detail="water looked like silver cloth",
        law="be gentle near the reeds",
    ),
    "green_lake": Setting(
        id="green_lake",
        place="the green lake",
        mood="soft",
        lake_detail="water slept under the lilies",
        law="listen before guessing",
    ),
    "farm_lake": Setting(
        id="farm_lake",
        place="the farm lake",
        mood="calm",
        lake_detail="ducks drifted like commas",
        law="a quiet eye sees more than a loud one",
    ),
}

MYSTERIES = {
    "missing_bell": Mystery(
        id="missing_bell",
        missing="the brass bell",
        suspect="the lake",
        clue="a trail of wet footprints leading to the dock",
        true_cause="a duck had nudged the bell into the grass",
        twist="the bell was not lost to the lake at all; it had only rolled under a reed basket",
        lesson="one should look twice before blaming the deep water",
    ),
    "missing_ribbon": Mystery(
        id="missing_ribbon",
        missing="the red ribbon",
        suspect="the wind",
        clue="a ribbon tail caught on a basket handle",
        true_cause="a child had borrowed the ribbon for a game",
        twist="the ribbon was tied neatly around a lantern, where no one first thought to look",
        lesson="the smallest clue can tell the truest story",
    ),
    "missing_spoon": Mystery(
        id="missing_spoon",
        missing="the silver spoon",
        suspect="the reeds",
        clue="a bright shine under a pie cloth",
        true_cause="the cook had set it beside the bread",
        twist="the spoon waited in plain sight, sleeping under a napkin",
        lesson="quick blame makes a fool of the wise",
    ),
}

MIME_NAMES = ["Nico", "Iris", "Tala", "Milo", "Pia", "Soren"]
HELPER_NAMES = ["Ada", "Bram", "Lina", "Jon", "Mara", "Oren"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    m = f["mystery"]
    return [
        f'Write a fable about a mime at a lake who solves {m.missing} by following a clue and an inner thought.',
        f"Tell a gentle mystery story with a mime, a lake, and a twist that shows the first suspect was wrong.",
        f'Write a child-friendly fable where a mime quietly thinks through a mystery to solve beside the lake.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question="What mystery did the village need to solve?",
            answer=f"The village needed to solve the mystery of {m.missing}. The story starts with it gone before the lake feast, so everyone wonders where it went.",
        ),
        QAItem(
            question="What did the mime first think had happened?",
            answer=f"The mime first thought {m.suspect} had taken it. That was the inner-monologue twist: the quiet water looked guilty, but the thought was only a guess.",
        ),
        QAItem(
            question="What solved the mystery in the end?",
            answer=f"The clue and the twist solved it together. Once {m.clue} was noticed, the truth became clear and everyone saw that {m.true_cause}.",
        ),
        QAItem(
            question="How did the ending change the village's feelings?",
            answer="The ending turned worry into relief. The mime stopped blaming the lake, and the village learned to look carefully before deciding.",
        ),
        QAItem(
            question="Where did the story happen?",
            answer=f"It happened at {setting.place}. The lake setting matters because the water and reeds make the mystery feel quiet and a little watchful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mime?",
            answer="A mime is a performer who tells a story without many words, often by using hands, face, and movement.",
        ),
        QAItem(
            question="Why can a lake feel mysterious in a story?",
            answer="A lake can feel mysterious because its water hides things and reflects the sky. That makes it a good place for a quiet guessing game.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery. It can be a footprint, a shine, or something left in the wrong place.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find the real answer instead of the first guess. The truth makes the confusing parts fit together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="moonlit_lake",
        mystery="missing_bell",
        mime_name="Nico",
        mime_gender="boy",
        helper_name="Ada",
        helper_gender="girl",
    ),
    StoryParams(
        setting="green_lake",
        mystery="missing_ribbon",
        mime_name="Iris",
        mime_gender="girl",
        helper_name="Bram",
        helper_gender="boy",
    ),
    StoryParams(
        setting="farm_lake",
        mystery="missing_spoon",
        mime_name="Tala",
        mime_gender="girl",
        helper_name="Jon",
        helper_gender="boy",
    ),
]


def explain_rejection() -> str:
    return "(No story: this world needs a lake setting and a solvable mystery.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
    return "\n".join(lines)


ASP_RULES = r"""
solvable(S, M) :- setting(S), mystery(M).
#show solvable/2.
"""


def asp_program(extra: str = "", show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    else:
        print(f"OK: ASP parity ({len(py)} combos).")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mime-and-lake fable world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--mime-name", choices=MIME_NAMES)
    ap.add_argument("--helper-name", choices=HELPER_NAMES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, mystery = rng.choice(sorted(combos))
    mime_name = args.mime_name or rng.choice(MIME_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != mime_name])
    mime_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    return StoryParams(
        setting=setting,
        mystery=mystery,
        mime_name=mime_name,
        mime_gender=mime_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES:
        raise StoryError("Invalid story parameters.")
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = tell(setting, mystery, params.mime_name, params.mime_gender, params.helper_name, params.helper_gender)
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
        print(f"{len(asp_valid_combos())} compatible (setting, mystery) combos:")
        for s, m in asp_valid_combos():
            print(f"  {s:14} {m}")
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
            header = f"### {p.mime_name} at {p.setting} ({p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
