#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grave_flexible_foreshadowing_fairy_tale.py
===========================================================================

A small fairy-tale storyworld built from the seed words "grave" and
"flexible", with foreshadowing as the main narrative instrument.

Premise:
- A child and a careful elder search for a missing charm in an old graveyard
  at dusk.
- A fragile-looking path threatens to fail them.
- An earlier detail about a flexible willow rod foreshadows the solution.
- The child uses the bendy rod to safely reach the charm, and the ending image
  proves the change: the graveyard is no longer feared; it becomes a place of
  memory, lantern-light, and a safe return home.

The script follows the Storyweavers contract:
- self-contained stdlib script
- imports shared results eagerly
- lazy imports asp inside helper functions
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates three QA sets from world state
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
SENSE_MIN = 2


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
    flexible: bool = False
    grave: bool = False
    safe: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "princess"}
        male = {"boy", "father", "dad", "man", "king", "prince"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    graveyard: str
    path: str
    weather: str


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    use: str
    flexible: bool = False
    grave: bool = False
    safe: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    risk: int
    tension: int
    text: str
    fail_text: str
    solve_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_gender: str
    object_id: str
    challenge_id: str
    seed: Optional[int] = None


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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("hinted"):
        return out
    if "elder" in world.entities and "child" in world.entities and "tool" in world.entities:
        world.facts["hinted"] = True
        world.get("child").memes["curiosity"] += 1
        out.append("")
    return out


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if child and child.meters["risk"] >= THRESHOLD and ("tension", "child") not in world.fired:
        world.fired.add(("tension", "child"))
        world.get("elder").memes["worry"] += 1
        out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_r_foreshadow, _r_tension):
            before = len(world.fired)
            sents = rule(world)
            if len(world.fired) != before or sents:
                changed = True
    if narrate:
        pass


SETTINGs = {
    "moon_garden": Setting(
        id="moon_garden",
        place="the moon garden",
        mood="silver and quiet",
        graveyard="an old graveyard at the garden's far edge",
        path="a little stone path between rosemary bushes",
        weather="clear",
    ),
    "village_green": Setting(
        id="village_green",
        place="the village green",
        mood="soft and dim",
        graveyard="a small graveyard beside the chapel",
        path="a narrow path under poplar trees",
        weather="misty",
    ),
}

OBJECTS = {
    "willow_rod": ObjectCfg(
        id="willow_rod",
        label="flexible willow rod",
        phrase="a flexible willow rod",
        use="bend and reach",
        flexible=True,
        tags={"flexible", "willow"},
    ),
    "ribbon": ObjectCfg(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon",
        use="mark the trail",
        tags={"ribbon"},
    ),
    "lantern": ObjectCfg(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        use="light the way",
        safe=True,
        tags={"light"},
    ),
}

CHALLENGES = {
    "gate_key": Challenge(
        id="gate_key",
        risk=2,
        tension=3,
        text="the iron gate key had slipped into the graveyard grass",
        fail_text="the key was too far to reach by hand",
        solve_text="the key came loose and gleamed in the lantern light",
        tags={"grave", "key"},
    ),
    "rose_branch": Challenge(
        id="rose_branch",
        risk=2,
        tension=2,
        text="a silver rose clasp had caught in the thorn hedge near the grave stones",
        fail_text="the hedge prickled every bare hand that reached for it",
        solve_text="the clasp slid free without a scratch",
        tags={"grave", "rose"},
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lina", "Ivy", "Tessa", "Alia"]
BOY_NAMES = ["Theo", "Finn", "Arlo", "Oren", "Perry", "Bram"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGs:
        for oid, obj in OBJECTS.items():
            if not obj.flexible:
                continue
            for cid in CHALLENGES:
                combos.append((sid, oid, cid))
    return combos


def sensible_objects() -> list[ObjectCfg]:
    return [o for o in OBJECTS.values() if o.flexible or o.safe]


def best_object() -> ObjectCfg:
    return OBJECTS["willow_rod"]


def is_reasonable(obj: ObjectCfg, challenge: Challenge) -> bool:
    return obj.flexible and challenge.risk <= 3


def outcome_of(params: StoryParams) -> str:
    return "resolved" if is_reasonable(OBJECTS[params.object_id], CHALLENGES[params.challenge_id]) else "failed"


def foreshadow_line(setting: Setting, obj: ObjectCfg) -> str:
    return f"Earlier, {setting.place} had shown the child a small thing: {obj.phrase}, bending in the wind without breaking."


def tell(params: StoryParams) -> World:
    setting = SETTINGs[params.setting]
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=params.elder_gender, label=params.elder_name, role="elder"))
    tool = world.add(Entity(id="tool", kind="thing", label=OBJECTS[params.object_id].label, flexible=OBJECTS[params.object_id].flexible, safe=OBJECTS[params.object_id].safe))
    challenge = world.add(Entity(id="challenge", kind="thing", label=CHALLENGES[params.challenge_id].text, grave=True))
    child.memes["hope"] += 1
    elder.memes["care"] += 1
    world.say(f"Once, in {setting.mood} {setting.place}, {child.label} walked with {elder.label} along {setting.path}.")
    world.say(f"They were going to {setting.graveyard}, where the lanterns made the stones look gentle instead of grim.")
    world.say(foreshadow_line(setting, OBJECTS[params.object_id]))
    world.para()
    world.say(f"At the graveyard edge, they found that {CHALLENGES[params.challenge_id].text}.")
    world.say(f"{elder.label} grew grave, and whispered that a careless tug might only make things worse.")
    child.memes["curiosity"] += 1
    child.meters["risk"] += CHALLENGES[params.challenge_id].risk
    world.para()
    if is_reasonable(OBJECTS[params.object_id], CHALLENGES[params.challenge_id]):
        world.say(f"Then {child.label} remembered the flexible rod.")
        world.say(f"With a careful bend, the rod could {OBJECTS[params.object_id].use}, just as it had seemed it could earlier.")
        world.say(f"{child.label} used {OBJECTS[params.object_id].phrase} to slip under the clasp and lift it free.")
        world.say(f"The challenge answered at once: {CHALLENGES[params.challenge_id].solve_text}.")
        child.memes["relief"] += 2
        elder.memes["relief"] += 2
        world.para()
        world.say(f"They left the graveyard by lantern-light, the flexible rod tucked under one arm and the rescued charm safe in the elder's palm.")
        world.say(f"By the gate, even the old stones seemed kinder, because the child had learned that a gentle bend can do what a hard pull cannot.")
        outcome = "resolved"
    else:
        world.say(f"{child.label} tried anyway, but {CHALLENGES[params.challenge_id].fail_text}.")
        world.say(f"The graveyard stayed silent, and the pair went home to fetch a better plan.")
        outcome = "failed"
    world.facts.update(
        setting=setting,
        child=child,
        elder=elder,
        tool=tool,
        challenge=challenge,
        outcome=outcome,
    )
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story that uses the words "grave" and "flexible" and includes a little foreshadowing.',
        f"Tell a gentle story where {f['child'].label} and {f['elder'].label} visit {f['setting'].graveyard} and solve a problem with something flexible.",
        f"Write a child-friendly tale with lantern-light, a graveyard, and an earlier hint that later pays off.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    obj = OBJECTS[f["tool"].label_word.replace('flexible ', 'willow_rod')] if False else OBJECTS["willow_rod"]
    qa = [
        QAItem(
            question="Who went to the graveyard?",
            answer=f"{child.label} went with {elder.label}. They walked together through the moonlit garden and the story stayed gentle even at the graveyard gate.",
        ),
        QAItem(
            question="What was foreshadowed earlier in the story?",
            answer=f"An earlier detail about the flexible willow rod was foreshadowed. It bent in the wind without breaking, which hinted that it would help later.",
        ),
    ]
    if f["outcome"] == "resolved":
        qa.append(QAItem(
            question="How did they solve the problem?",
            answer=f"{child.label} used the flexible willow rod to reach the charm safely. The gentle bend let them do the job without tugging hard at the graveyard grass.",
        ))
        qa.append(QAItem(
            question="What changed by the end?",
            answer=f"The graveyard felt less scary by the end. They left with the rescued charm, a safe lantern, and the flexible rod still whole in their hands.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flexible mean?",
            answer="Flexible means something can bend without snapping. A flexible thing can move and still stay whole.",
        ),
        QAItem(
            question="Why can a grave be a grave subject in a story?",
            answer="A grave is a serious, quiet place, so it can make a tale feel solemn and old. In a fairy tale, that feeling can help the story sound mysterious instead of scary.",
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
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.flexible:
            bits.append("flexible=True")
        if e.grave:
            bits.append("grave=True")
        if e.safe:
            bits.append("safe=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
flexible_obj(O) :- object(O), flexible(O).
reasonable(S,O,C) :- setting(S), flexible_obj(O), challenge(C).
resolved(O,C) :- flexible(O), challenge(C), risk(C,R), R <= 3.
outcome(resolved) :- chosen_object(O), chosen_challenge(C), resolved(O,C).
outcome(failed) :- chosen_object(O), chosen_challenge(C), not resolved(O,C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGs:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.flexible:
            lines.append(asp.fact("flexible", oid))
        if o.safe:
            lines.append(asp.fact("safe", oid))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("risk", cid, c.risk))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_object", params.object_id),
        asp.fact("chosen_challenge", params.challenge_id),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos")
    sample = StoryParams(setting="moon_garden", child_name="Mira", child_gender="girl", elder_name="Grandma", elder_gender="woman", object_id="willow_rod", challenge_id="gate_key")
    if asp_outcome(sample) == outcome_of(sample):
        print("OK: ASP outcome matches Python outcome.")
    else:
        rc = 1
        print("MISMATCH in outcome model.")
    try:
        s = generate(sample)
        _ = s.story
    except Exception as exc:
        rc = 1
        print(f"FAIL: generate smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale world of a graveyard, a flexible helper, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGs)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--child-name")
    ap.add_argument("--elder-name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGs))
    object_id = args.object_id or "willow_rod"
    challenge_id = args.challenge or rng.choice(list(CHALLENGES))
    if object_id not in OBJECTS or challenge_id not in CHALLENGES:
        raise StoryError("Unknown object or challenge.")
    if not is_reasonable(OBJECTS[object_id], CHALLENGES[challenge_id]):
        raise StoryError("No story: this flexible helper does not fit the challenge.")
    child_gender = rng.choice(["girl", "boy"])
    elder_gender = rng.choice(["woman", "man"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_name = args.elder_name or rng.choice(["Grandma", "Grandpa", "Aunt Willow", "Uncle Rowan"])
    return StoryParams(setting=setting, child_name=child_name, child_gender=child_gender, elder_name=elder_name, elder_gender=elder_gender, object_id=object_id, challenge_id=challenge_id)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGs or params.object_id not in OBJECTS or params.challenge_id not in CHALLENGES:
        raise StoryError("Invalid params.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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


CURATED = [
    StoryParams(setting="moon_garden", child_name="Mira", child_gender="girl", elder_name="Grandma", elder_gender="woman", object_id="willow_rod", challenge_id="gate_key"),
    StoryParams(setting="village_green", child_name="Theo", child_gender="boy", elder_name="Grandpa", elder_gender="man", object_id="willow_rod", challenge_id="rose_branch"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show reasonable/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show reasonable/3."))
        print(f"{len(asp.atoms(model, 'reasonable'))} reasonable combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
