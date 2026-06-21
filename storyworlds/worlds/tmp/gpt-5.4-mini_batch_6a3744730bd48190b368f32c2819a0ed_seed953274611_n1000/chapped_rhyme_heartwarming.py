#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/chapped_rhyme_heartwarming.py
==============================================================

A tiny heartwarming storyworld about a child with chapped lips, a gentle rhyme,
and a caring helper who turns a rough day into a warm one.

Premise:
- A child goes outside on a cold, windy day and their lips get chapped.
- A helper notices, offers comfort, and teaches a small rhyme about care.
- The child uses a simple balm and warm drink, then feels better.

The model is state-driven:
- physical meters track things like chappedness, warmth, and balm used
- emotional memes track worry, care, relief, and joy
- the story is not a frozen paragraph; it changes as the world changes

The story can vary by:
- setting
- child/helper names and roles
- warm remedy
- rhyme style
- whether the helper is a parent, grandparent, or older sibling

The story always includes the word "chapped" and uses a short rhyme instrument
inside the prose, while keeping the tone heartwarming.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/chapped_rhyme_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/chapped_rhyme_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4-mini/chapped_rhyme_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/chapped_rhyme_heartwarming.py --verify
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
GATE_MIN = 2


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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    weather: str
    chill: int
    detail: str


@dataclass
class ChildNeed:
    id: str
    label: str
    symptom: str
    cause: str
    soother: str
    comfort_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    warmth: int
    help_text: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rhyme:
    id: str
    couplet1: str
    couplet2: str
    coda: str
    tags: set[str] = field(default_factory=set)


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["chapped"] >= THRESHOLD and ("worry", "child") not in world.fired:
        world.fired.add(("worry", "child"))
        child.memes["worry"] += 1
        out.append("__worry__")
    return out


def _r_relief(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["balmed"] >= THRESHOLD and ("relief", "child") not in world.fired:
        world.fired.add(("relief", "child"))
        child.memes["relief"] += 1
        child.memes["joy"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("relief", _r_relief)]


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


def windy_trip(world: World, child: Entity, helper: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    world.say(
        f"On a windy day, {child.id} and {helper.id} went to {setting.place}. "
        f"{setting.detail}"
    )
    world.say(
        f"The air was {setting.weather}, and the cold made {child.id}'s lips feel tight."
    )


def notice_chapped(world: World, child: Entity, helper: Entity, need: ChildNeed) -> None:
    child.meters["chapped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.id} noticed {child.id}'s lips looked {need.symptom}. "
        f'"Your lips are chapped," {helper.id} said softly, "and that is no fun at all."'
    )


def offer_rhyme(world: World, helper: Entity, child: Entity, rhyme: Rhyme) -> None:
    helper.memes["care"] += 1
    world.say(
        f'{helper.id} smiled and said, "{rhyme.couplet1}"'
    )
    world.say(
        f'"{rhyme.couplet2}"'
    )


def soothe(world: World, helper: Entity, child: Entity, need: ChildNeed, remedy: Remedy) -> None:
    child.meters["balmed"] += 1
    child.meters["warmth"] += 1
    child.meters["chapped"] = 0.0
    helper.meters["kindness"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} brought {remedy.phrase} and {remedy.help_text}. "
        f"{child.id} used {need.soother} and took a small sip of warm tea."
    )
    world.say(
        f"The sting faded, the cold lost its bite, and {child.id}'s lips felt soft again."
    )
    world.say(f'"{rhyme_coda(remedy)}"')


def closing(world: World, child: Entity, helper: Entity, rhyme: Rhyme) -> None:
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"By bedtime, {child.id} was smiling. {helper.id} tucked {child.id} in and said "
        f"the rhyme one more time: {rhyme.coda}"
    )
    world.say(
        f"Warm, cared for, and no longer chapped, {child.id} fell asleep with a happy sigh."
    )


def rhyme_coda(remedy: Remedy) -> str:
    return f"Warm balm, calm charm, and a gentle heart -- {remedy.rhyme_word} means care from the start."


def tell(setting: Setting, need: ChildNeed, remedy: Remedy, rhyme: Rhyme,
         child_name: str = "Milo", child_gender: str = "boy",
         helper_name: str = "Grandma", helper_gender: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        label="the child",
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        label="the helper",
    ))
    world.add(Entity(id="setting", type="setting", label=setting.place))

    windy_trip(world, child, helper, setting)
    world.para()
    notice_chapped(world, child, helper, need)
    offer_rhyme(world, helper, child, rhyme)
    world.para()
    soothe(world, helper, child, need, remedy)
    closing(world, child, helper, rhyme)

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        need=need,
        remedy=remedy,
        rhyme=rhyme,
        chapped=child.meters["chapped"] >= THRESHOLD,
        soothed=child.meters["balmed"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "winter_walk": Setting(
        id="winter_walk",
        place="the park by the frozen pond",
        weather="cold and breezy",
        chill=3,
        detail="Bare branches tapped the air, and the path sparkled with old snow.",
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        weather="crisp and windy",
        chill=2,
        detail="A cozy house sat behind them, with a warm light glowing in the window.",
    ),
    "bus_stop": Setting(
        id="bus_stop",
        place="the corner bus stop",
        weather="sharp and chilly",
        chill=3,
        detail="A little roof kept off the sky, but the wind still found their cheeks.",
    ),
}

NEEDS = {
    "chapped_lips": ChildNeed(
        id="chapped_lips",
        label="chapped lips",
        symptom="red and sore",
        cause="cold wind",
        soother="lip balm",
        comfort_line="A little balm can make sore lips feel better.",
        tags={"chapped", "cold"},
    ),
    "dry_cheeks": ChildNeed(
        id="dry_cheeks",
        label="dry cheeks",
        symptom="dry and prickly",
        cause="winter air",
        soother="cream",
        comfort_line="A little cream can make dry skin feel softer.",
        tags={"dry", "cold"},
    ),
}

REMEDIES = {
    "balm": Remedy(
        id="balm",
        label="lip balm",
        phrase="a tiny tin of lip balm",
        warmth=2,
        help_text="rubbed it on carefully",
        rhyme_word="balm",
        tags={"balm", "care"},
    ),
    "honey_tea": Remedy(
        id="honey_tea",
        label="warm honey tea",
        phrase="a mug of warm honey tea",
        warmth=3,
        help_text="held the mug with both hands and sipped slowly",
        rhyme_word="tea",
        tags={"tea", "care"},
    ),
    "scarf_warmth": Remedy(
        id="scarf_warmth",
        label="a warm scarf",
        phrase="a soft scarf that smelled like sunshine",
        warmth=1,
        help_text="wrapped it around the chilly cheeks",
        rhyme_word="warm",
        tags={"scarf", "care"},
    ),
}

RHYMES = {
    "balm_rhyme": Rhyme(
        id="balm_rhyme",
        couplet1="When the wind is nippy, and your lips feel dry,",
        couplet2="A little balm and a loving hand can help the tears pass by.",
        coda="Warm balm, calm charm, and a gentle heart.",
        tags={"rhyme", "balm"},
    ),
    "tea_rhyme": Rhyme(
        id="tea_rhyme",
        couplet1="When the wind is chilly and your cheeks feel tight,",
        couplet2="Warm tea and kind words can make the whole day bright.",
        coda="Warm tea, happy me, and a smile from start to start.",
        tags={"rhyme", "tea"},
    ),
    "scarf_rhyme": Rhyme(
        id="scarf_rhyme",
        couplet1="When the air is sharp and the cold comes through,",
        couplet2="A soft warm scarf and a hug can help you through.",
        coda="Warm scarf, soft heart, and a cozy little start.",
        tags={"rhyme", "scarf"},
    ),
}

CHILD_NAMES = ["Milo", "Nora", "Lena", "Eli", "Ava", "Owen", "Ivy", "Theo"]
HELPERS = [
    ("Grandma", "grandmother"),
    ("Grandpa", "grandfather"),
    ("Mom", "mother"),
    ("Dad", "father"),
]


@dataclass
class StoryParams:
    setting: str
    need: str
    remedy: str
    rhyme: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for nid, need in NEEDS.items():
            if need.id == "chapped_lips" and setting.chill >= 2:
                for rid, remedy in REMEDIES.items():
                    for rhid, rhyme in RHYMES.items():
                        if "rhyme" in rhyme.tags:
                            combos.append((sid, nid, rid, rhid))
    return combos


def explain_rejection(setting: Setting, need: ChildNeed) -> str:
    if need.id != "chapped_lips":
        return "(No story: this world is built around chapped lips, not a different problem.)"
    return "(No story: the setting is too warm for a chapped-lips story. Pick a chillier place.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: chapped lips, a rhyme, and a heartwarming fix."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
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
    if args.need and args.need not in NEEDS:
        raise StoryError("(Invalid need.)")
    if args.setting and args.need:
        if SETTINGS[args.setting].chill < 2 and args.need == "chapped_lips":
            raise StoryError(explain_rejection(SETTINGS[args.setting], NEEDS[args.need]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.need is None or c[1] == args.need)
              and (args.remedy is None or c[2] == args.remedy)
              and (args.rhyme is None or c[3] == args.rhyme)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, need, remedy, rhyme = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    child_gender = rng.choice(["boy", "girl"])
    helper_name, helper_gender = rng.choice(HELPERS)
    return StoryParams(
        setting=setting,
        need=need,
        remedy=remedy,
        rhyme=rhyme,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story for a small child that includes the word "chapped" and a short rhyme.',
        f"Tell a gentle story where {f['child'].id} has chapped lips in {f['setting'].place} and {f['helper'].id} helps with a soothing remedy.",
        f"Write a cozy story with a rhyme about {f['remedy'].label} that ends with comfort, care, and a warm smile.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, need, remedy, rhyme = f["child"], f["helper"], f["need"], f["remedy"], f["rhyme"]
    return [
        QAItem(
            question="What was wrong at the start of the story?",
            answer=f"{child.id} had {need.label}, and the cold wind made them sting. That is why the helper noticed something was wrong right away.",
        ),
        QAItem(
            question="What did the helper do to make things better?",
            answer=f"{helper.id} brought {remedy.phrase} and spoke in a calm rhyme. The warm help soothed the chapped feeling and turned the moment gentle.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {child.id} feeling warm, safe, and cared for. The chapped feeling was gone, and bedtime came with a happy smile.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does chapped mean?",
            answer="Chapped means the skin has become dry, sore, or cracked, often because of wind or cold air.",
        ),
        QAItem(
            question="Why can cold wind make lips feel bad?",
            answer="Cold wind can dry out lips and make them feel tight or sore. A little care, like balm or warm drinks, can help them feel better.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little piece of language where words sound alike at the end. Rhymes can be fun to hear and easy to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes} role={e.role}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="winter_walk",
        need="chapped_lips",
        remedy="balm",
        rhyme="balm_rhyme",
        child_name="Milo",
        child_gender="boy",
        helper_name="Grandma",
        helper_gender="grandmother",
    ),
    StoryParams(
        setting="porch",
        need="chapped_lips",
        remedy="tea",
        rhyme="tea_rhyme",
        child_name="Nora",
        child_gender="girl",
        helper_name="Mom",
        helper_gender="mother",
    ),
    StoryParams(
        setting="bus_stop",
        need="chapped_lips",
        remedy="scarf",
        rhyme="scarf_rhyme",
        child_name="Eli",
        child_gender="boy",
        helper_name="Grandpa",
        helper_gender="grandfather",
    ),
]


def tell(setting: Setting, need: ChildNeed, remedy: Remedy, rhyme: Rhyme, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    return _tell(setting, need, remedy, rhyme, child_name, child_gender, helper_name, helper_gender)


def _tell(setting: Setting, need: ChildNeed, remedy: Remedy, rhyme: Rhyme, child_name: str, child_gender: str, helper_name: str, helper_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    world.add(Entity(id="place", type="setting", label=setting.place))
    windy_trip(world, child, helper, setting)
    world.para()
    notice_chapped(world, child, helper, need)
    offer_rhyme(world, helper, child, rhyme)
    world.para()
    soothe(world, helper, child, need, remedy)
    closing(world, child, helper, rhyme)
    world.facts.update(child=child, helper=helper, setting=setting, need=need, remedy=remedy, rhyme=rhyme)
    return world


def generate(params: StoryParams) -> StorySample:
    try:
        world = _tell(
            SETTINGS[params.setting],
            NEEDS[params.need],
            REMEDIES[params.remedy],
            RHYMES[params.rhyme],
            params.child_name,
            params.child_gender,
            params.helper_name,
            params.helper_gender,
        )
    except KeyError as exc:
        raise StoryError(f"Invalid parameter: {exc}") from exc
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
chapped(child) :- need(chapped_lips).
warm_help(remedy) :- remedy(remedy), warmth(remedy, W), W >= 2.
heartwarming :- chapped(child), warm_help(remedy), rhyme(rhyme).
valid(setting, need, remedy, rhyme) :- setting(setting), need(need), remedy(remedy), rhyme(rhyme).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for nid in NEEDS:
        lines.append(asp.fact("need", nid))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("warmth", rid, r.warmth))
    for rhid in RHYMES:
        lines.append(asp.fact("rhyme", rhid))
    lines.append(asp.fact("need", "chapped_lips"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP valid combos differ from Python.")
    else:
        print(f"OK: ASP and Python agree on {len(valid_combos())} valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story or "chapped" not in sample.story:
            raise RuntimeError("generated story missing required word")
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_response(rid: str) -> str:
    return f"(No story: response '{rid}' is not part of this gentle rhyme world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("valid combos:")
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
