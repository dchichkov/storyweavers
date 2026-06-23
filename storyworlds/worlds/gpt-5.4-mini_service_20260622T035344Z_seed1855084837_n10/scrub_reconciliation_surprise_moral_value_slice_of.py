#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10/scrub_reconciliation_surprise_moral_value_slice_of.py
==============================================================================================================

A small slice-of-life storyworld about a shared kitchen, a surprise mess,
reconciliation, and a moral value learned through an ordinary day.

The seed prompt asks for:
- Words: scrub
- Features: Reconciliation, Surprise, Moral Value
- Style: Slice of Life

This storyworld models a tiny domestic/social domain with typed entities,
physical meters, emotional memes, a causal turn, and an ending image that
proves something changed.
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
    traits: list[str] = field(default_factory=list)
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


@dataclass
class StoryParams:
    setting: str
    mess: str
    object: str
    helper: str
    protagonist: str
    protagonist_gender: str
    helper_gender: str
    parent: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class Setting:
    label: str
    place: str
    messes: set[str]


@dataclass(frozen=True)
class Mess:
    id: str
    material: str
    action: str
    outcome: str
    zone: set[str]
    tags: set[str]


@dataclass(frozen=True)
class ObjectSpec:
    id: str
    label: str
    phrase: str
    region: str
    owner_kind: str
    tags: set[str]


@dataclass(frozen=True)
class CleanTool:
    id: str
    label: str
    phrase: str
    use: str
    tags: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, Any] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple[str, ...]] = set()
        self.history: list[dict[str, Any]] = []

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

    def event(self, kind: str, **data: Any) -> None:
        self.history.append({"kind": kind, **data})

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "traits": list(v.traits), "role": v.role,
            "owner": v.owner, "caretaker": v.caretaker, "plural": v.plural,
            "tags": set(v.tags), "attrs": dict(v.attrs),
            "meters": defaultdict(float, dict(v.meters)),
            "memes": defaultdict(float, dict(v.memes)),
        }) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.history = [dict(x) for x in self.history]
        return clone


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mess_id in setting.messes:
            for obj_id, obj in OBJECTS.items():
                if mess_id in MESS[mess_id].tags and obj.region in MESS[mess_id].zone:
                    combos.append((setting_id, mess_id, obj_id))
    return combos


def scrub_risk(mess: Mess, obj: ObjectSpec) -> bool:
    return obj.region in mess.zone


def choose_helper(mess: Mess, obj: ObjectSpec) -> Optional[CleanTool]:
    for tool in TOOLS.values():
        if mess.id in tool.tags and obj.region in tool.tags:
            return tool
    return None


def explain_rejection(setting: Setting, mess: Mess, obj: ObjectSpec) -> str:
    return f"(No story: {mess.action} in {setting.place} would not reach {obj.label}, so there is no honest mess-and-fix turn.)"


@dataclass
class Rule:
    name: str
    apply: Any


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.entities.values():
        if actor.meters["messy"] < THRESHOLD:
            continue
        for obj in world.entities.values():
            if obj.owner != actor.id:
                continue
            if obj.attrs.get("protected"):
                continue
            if obj.attrs.get("region") not in world.facts.get("zone", set()):
                continue
            sig = ("smear", actor.id, obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["dirty"] += 1
            out.append(f"{obj.label.capitalize()} got dirty.")
    return out


CAUSAL_RULES = [Rule("smear", _r_smear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def tell(setting: Setting, mess: Mess, obj: ObjectSpec, tool: CleanTool, *,
         protagonist: str = "Mina", protagonist_gender: str = "girl",
         helper: str = "Jules", helper_gender: str = "boy", parent: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=protagonist, kind="character", type=protagonist_gender, traits=["thoughtful"]))
    sidekick = world.add(Entity(id=helper, kind="character", type=helper_gender, traits=["kind"]))
    adult = world.add(Entity(id=parent, kind="character", type=parent, label=f"the {parent}"))
    thing = world.add(Entity(id="object", type="thing", label=obj.label, phrase=obj.phrase, owner=hero.id, caretaker=adult.id))
    thing.attrs["region"] = obj.region
    thing.attrs["dirty"] = 0.0

    hero.memes["care"] += 1
    sidekick.memes["care"] += 1
    world.say(f"{hero.id} and {sidekick.id} were having a quiet afternoon in {setting.place}.")
    world.say(f"{hero.id} liked how {setting.label.lower()} days made little chores feel easier.")
    world.say(f"They were proud of {thing.phrase}, which {hero.pronoun('possessive')} {parent} had helped pick out.")

    world.para()
    world.facts["zone"] = set(mess.zone)
    world.say(f"Then a surprise happened: {sidekick.id} spilled {mess.material} while trying to help.")
    hero.memes["surprise"] += 1
    sidekick.memes["shame"] += 1
    hero.meters["messy"] += 1
    sidekick.meters["messy"] += 1
    propagate(world)
    world.say(f"The {mess.material} left {obj.label} {mess.outcome}.")

    world.para()
    world.say(f"{hero.id} did not get mad.")
    hero.memes["patience"] += 1
    sidekick.memes["worry"] += 1
    world.say(f"Instead, {hero.id} handed over a sponge and said they could scrub it together.")
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, tags=set(tool.tags)))
    tool_ent.attrs["use"] = tool.use
    tool_ent.attrs["owned_by"] = hero.id
    tool_ent.attrs["target"] = thing.id
    thing.attrs["protected"] = True
    thing.meters["dirty"] = max(0.0, thing.meters["dirty"] - 1)
    sidekick.memes["relief"] += 1
    hero.memes["kindness"] += 1
    world.event("reconcile", protagonist=hero.id, helper=sidekick.id)
    world.say(f"Together they scrubbed the table until it shone again.")
    world.say(f"By the end, {sidekick.id} smiled, and {hero.id} smiled back.")

    world.para()
    world.say(f"That evening, {parent} made tea and said the best days were the ones where people fixed mistakes without fuss.")
    world.say(f"{hero.id} looked at the clean table and learned that being gentle could be stronger than being annoyed.")

    world.facts.update(
        hero=hero.id,
        helper=sidekick.id,
        adult=adult.id,
        object=obj,
        setting=setting,
        mess=mess,
        tool=tool,
        outcome="reconciled",
        dirty=float(thing.meters["dirty"]),
    )
    return world


SETTINGS = {
    "kitchen": Setting(label="kitchen", place="the kitchen", messes={"tea", "flour", "sauce"}),
    "laundry": Setting(label="laundry room", place="the laundry room", messes={"soap", "dust"}),
    "porch": Setting(label="porch", place="the porch", messes={"mud", "pollen"}),
}

MESS = {
    "tea": Mess(id="tea", material="tea", action="spill tea", outcome="sticky", zone={"torso", "legs"}, tags={"drink", "wet", "sticky"}),
    "flour": Mess(id="flour", material="flour", action="drop flour", outcome="white and dusty", zone={"torso", "legs"}, tags={"powder", "dry"}),
    "mud": Mess(id="mud", material="mud", action="track mud", outcome="muddy", zone={"feet", "legs"}, tags={"wet", "dirty"}),
    "soap": Mess(id="soap", material="soap bubbles", action="splash soap", outcome="slippery", zone={"torso", "hands"}, tags={"wet", "clean"}),
    "pollen": Mess(id="pollen", material="yellow pollen", action="scatter pollen", outcome="speckled", zone={"torso", "hands"}, tags={"dry", "yellow"}),
    "sauce": Mess(id="sauce", material="tomato sauce", action="spill sauce", outcome="red-stained", zone={"torso", "legs"}, tags={"wet", "sticky"}),
}

OBJECTS = {
    "table": ObjectSpec(id="table", label="table", phrase="the little table", region="torso", owner_kind="house", tags={"table"}),
    "rug": ObjectSpec(id="rug", label="rug", phrase="the woven rug", region="legs", owner_kind="house", tags={"rug"}),
    "floor": ObjectSpec(id="floor", label="floor mat", phrase="the floor mat", region="feet", owner_kind="house", tags={"floor"}),
}

TOOLS = {
    "sponge": CleanTool(id="sponge", label="sponge", phrase="a soft sponge", use="scrub", tags={"tea", "flour", "sauce", "torso", "legs"}),
    "cloth": CleanTool(id="cloth", label="cloth", phrase="a warm dishcloth", use="wipe", tags={"tea", "sauce", "torso"}),
    "brush": CleanTool(id="brush", label="brush", phrase="a small scrub brush", use="scrub", tags={"mud", "pollen", "feet", "legs"}),
}

GIRL_NAMES = ["Mina", "Ivy", "Nina", "Lena", "Rosa", "Tia"]
BOY_NAMES = ["Jules", "Theo", "Arun", "Noah", "Evan", "Sami"]
PARENT_NAMES = ["mother", "father"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short slice-of-life story for a child that includes the word "scrub" and shows {f["helper"]} and {f["hero"]} making up after a small mess.',
        f"Tell an ordinary home story where {f['helper']} causes a surprise spill in {f['setting'].place}, then {f['hero']} helps scrub it up and they feel better.",
        f"Write a gentle reconciliation story with a surprise, a little cleanup, and a moral value about kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.get(f["hero"])
    helper = world.get(f["helper"])
    setting: Setting = f["setting"]
    mess: Mess = f["mess"]
    obj: ObjectSpec = f["object"]
    tool: CleanTool = f["tool"]
    return [
        QAItem(
            question=f"What surprise happened while {hero.id} and {helper.id} were in {setting.place}?",
            answer=f"{helper.id} spilled {mess.material} by accident. It was a small surprise, but it made {obj.label} get {mess.outcome}.",
        ),
        QAItem(
            question=f"How did {hero.id} respond when the mess happened?",
            answer=f"{hero.id} stayed calm and chose to help instead of scolding {helper.id}. {hero.id} said they could scrub it together, and that turned the mistake into teamwork.",
        ),
        QAItem(
            question=f"What did they use to clean {obj.label}?",
            answer=f"They used {tool.phrase}. It was the right tool for the job, so the mess could be scrubbed away without anyone feeling worse.",
        ),
        QAItem(
            question=f"Why did the story end with both children smiling?",
            answer=f"They made up after the spill and fixed the problem side by side. The cleanup showed that kindness can repair an ordinary bad moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mess: Mess = f["mess"]
    tool: CleanTool = f["tool"]
    obj: ObjectSpec = f["object"]
    return [
        QAItem(question="What does it mean to scrub something?", answer="To scrub something means to rub it with a cloth, sponge, or brush to help clean off dirt or stains."),
        QAItem(question=f"Why can {mess.material} make a mess?", answer=f"{mess.material.capitalize()} can spread quickly and stick to things, so it leaves a visible mess that needs cleaning."),
        QAItem(question=f"What is {tool.label} for?", answer=f"A {tool.label} helps clean by rubbing away dirt or stains, which is useful after a spill."),
        QAItem(question=f"What kind of thing is {obj.label} in a home?", answer=f"A {obj.label} is a shared household thing. People use it every day, so keeping it clean helps the room feel nice."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if n:
            bits.append(f"memes={dict(n)}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id}: {e.type} {(' '.join(bits))}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S, M, O) :- setting(S), mess(M), object(O), risk(M, O).
reconciled_story(S, M, O) :- valid_combo(S, M, O).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.messes):
            lines.append(asp.fact("allowed_mess", sid, m))
    for mid, m in MESS.items():
        lines.append(asp.fact("mess", mid))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for sid in SETTINGS:
        for mid in MESS:
            for oid in OBJECTS:
                if scrub_risk(MESS[mid], OBJECTS[oid]):
                    lines.append(asp.fact("risk", sid, mid, oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP combo gates.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity matched and story smoke test passed ({len(py)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a surprise mess, reconciliation, and learning a moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mess", choices=MESS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--helper", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--protagonist", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--protagonist-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_NAMES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _rand_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mess is None or c[1] == args.mess)
              and (args.object is None or c[2] == args.object)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mess, obj = rng.choice(sorted(combos))
    protagonist_gender = args.protagonist_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or ("boy" if protagonist_gender == "girl" and rng.random() < 0.5 else "girl")
    protagonist = args.protagonist or _rand_name(rng, protagonist_gender)
    helper = args.helper or _rand_name(rng, helper_gender, avoid=protagonist)
    parent = args.parent or rng.choice(PARENT_NAMES)
    return StoryParams(setting=setting, mess=mess, object=obj, helper=helper, protagonist=protagonist, protagonist_gender=protagonist_gender, helper_gender=helper_gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mess not in MESS or params.object not in OBJECTS:
        raise StoryError("Invalid params.")
    setting = SETTINGS[params.setting]
    mess = MESS[params.mess]
    obj = OBJECTS[params.object]
    tool = choose_helper(mess, obj)
    if tool is None:
        raise StoryError(explain_rejection(setting, mess, obj))
    world = tell(setting, mess, obj, tool, protagonist=params.protagonist, protagonist_gender=params.protagonist_gender, helper=params.helper, helper_gender=params.helper_gender, parent=params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="kitchen", mess="tea", object="table", helper="Jules", protagonist="Mina", protagonist_gender="girl", helper_gender="boy", parent="mother"),
    StoryParams(setting="porch", mess="mud", object="floor", helper="Ivy", protagonist="Theo", protagonist_gender="boy", helper_gender="girl", parent="father"),
    StoryParams(setting="laundry", mess="soap", object="rug", helper="Rosa", protagonist="Noah", protagonist_gender="boy", helper_gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:")
        for t in combos:
            print("  ", t)
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
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = seed
            sample.params = params
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
