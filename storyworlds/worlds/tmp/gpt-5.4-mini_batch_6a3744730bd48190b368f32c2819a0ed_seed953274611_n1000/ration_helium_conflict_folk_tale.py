#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ration_helium_conflict_folk_tale.py
===================================================================

A standalone storyworld about a small folk-tale conflict over a ration of helium:
a village needs enough of the rare gas to lift a festival lantern, but the supply
is limited, tempers rise, and a wise helper finds a fair, practical ending.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal model
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in world state

Seed words: ration, helium
Style: Folk Tale
Feature: Conflict
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Vessel:
    id: str
    label: str
    purpose: str
    capacity: int
    bursty: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Resource:
    id: str
    label: str
    unit: str
    scant: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class HelperPlan:
    id: str
    label: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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
class StoryParams:
    village: str
    vessel: str
    resource: str
    helper_plan: str
    hero: str
    hero_gender: str
    rival: str
    rival_gender: str
    elder: str
    elder_gender: str
    seed: Optional[int] = None
    ration_need: int = 2
    supply: int = 1
    delay: int = 0
    hero_age: int = 7
    rival_age: int = 6
    relation: str = "siblings"


VILLAGES = {
    "hill": "the hill village",
    "river": "the river village",
    "orchard": "the orchard village",
}

VESSELS = {
    "lantern": Vessel("lantern", "sky lantern", "to carry a blessing", 2, False, {"light", "sky"}),
    "kite": Vessel("kite", "festival kite", "to send a ribbon message", 3, True, {"sky", "festival"}),
    "belloon": Vessel("balloon", "cloth balloon", "to lift a little banner", 2, True, {"sky", "festival"}),
}

RESOURCES = {
    "helium": Resource("helium", "helium", "bottle", True, {"helium", "gas"}),
    "ration": Resource("ration", "ration", "measure", True, {"ration", "share"}),
}

PLANS = {
    "patch": HelperPlan("patch", "patch the leak and share fairly", 3, 3,
                        "patched the leak with wax, split the remaining helium fairly, and sent up the lantern",
                        "tried to patch the leak, but the gas was already too low",
                        "patched the leak and shared the helium fairly",
                        {"repair", "share"}),
    "swap": HelperPlan("swap", "swap to a smaller vessel", 3, 2,
                       "chose a smaller vessel that needed less helium and still floated",
                       "picked a smaller vessel, but it still would not lift",
                       "chose a smaller vessel that needed less helium",
                       {"change", "share"}),
    "stitch": HelperPlan("stitch", "stitch the torn cloth and save the rest", 2, 1,
                         "stitched the torn cloth and saved the rest of the helium for another night",
                         "stitched too slowly, and the festival hour passed",
                         "stitched the cloth and saved the helium",
                         {"repair"}),
    "overfill": HelperPlan("overfill", "stuff it full at once", 1, 1,
                           "stuffed the vessel full, and it strained and sagged under the pressure",
                           "stuffed it full, but the vessel sagged and drifted nowhere",
                           "stuffed it full",
                           {"greedy"}),
}

HERO_NAMES = ["Mira", "Jory", "Nell", "Toma", "Sela", "Bram"]
RIVAL_NAMES = ["Pip", "Anka", "Roan", "Luma", "Hale", "Etta"]
ELDER_NAMES = ["Grandmother Reed", "Old Mara", "Aunt Wren", "Uncle Bran"]

TRAITS = ["kind", "proud", "patient", "quick", "gentle", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for village in VILLAGES:
        for vessel in VESSELS:
            for resource in RESOURCES:
                if vessel != "lantern" or resource == "helium":
                    combos.append((village, vessel, resource))
    return combos


def explain_rejection(vessel: Vessel, resource: Resource) -> str:
    if resource.id != "helium":
        return f"(No story: this tale needs helium, but got {resource.label}.)"
    if vessel.id not in {"lantern", "kite", "balloon"}:
        return "(No story: the village vessel does not make sense for this folk tale.)"
    return "(No story: that combination has no useful conflict.)"


def reasonableness_gate(vessel: Vessel, resource: Resource) -> bool:
    return resource.id == "helium"


def _r_pressure(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("spilled"):
        for c in world.characters():
            c.memes["worry"] += 1
        out.append("__tension__")
    return out


CAUSAL_RULES = [Callable[[World], list[str]]]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


CAUSAL_RULES: list[Rule] = [
    Rule("pressure", _r_pressure),
]


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


def predict_spill(world: World, amount: int) -> dict:
    sim = world.copy()
    sim.facts["spilled"] = amount > sim.facts.get("supply", 0)
    propagate(sim, narrate=False)
    return {"worry": sum(c.memes["worry"] for c in sim.characters()), "spilled": sim.facts["spilled"]}


def opening(world: World, hero: Entity, rival: Entity, village: str, vessel: Vessel) -> None:
    world.say(
        f"In {village}, {hero.id} and {rival.id} were raised on bread, bells, and stories by the fire. "
        f"One spring evening they were sent to ready the {vessel.label} for the lantern feast."
    )
    world.say(
        f'The old box held only a little {world.facts["resource"].label}, and everyone called it the village {world.facts["resource"].label} because it had to be shared carefully.'
    )


def conflict(world: World, hero: Entity, rival: Entity, elder: Entity, vessel: Vessel) -> None:
    hero.memes["want"] += 1
    rival.memes["want"] += 1
    world.say(
        f'"I should carry the {vessel.label}," said {hero.id}, while {rival.id} answered, '
        f'"No, I am the one who tied the ribbon."'
    )
    world.say(
        f"Their voices rose like crows over a field, and the elder listened from the doorway."
    )


def warn(world: World, elder: Entity, hero: Entity, rival: Entity, amount: int) -> None:
    pred = predict_spill(world, amount)
    world.facts["predicted_worry"] = pred["worry"]
    if amount > world.facts["supply"]:
        world.say(
            f'{elder.id} put a hand on the box. "{hero.id}, {rival.id}, if you pull too hard, the helium will be gone before the lantern can rise."'
        )
    else:
        world.say(
            f'{elder.id} put a hand on the box. "A ration is a promise," {elder.id} said. '
            f'"Measure it, do not grab it."'
        )


def quarrel(world: World, hero: Entity, rival: Entity) -> None:
    hero.memes["anger"] += 1
    rival.memes["anger"] += 1
    world.facts["spilled"] = True
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} reached first, {rival.id} reached back, and the rope snagged. "
        f"With a small hiss, some helium slipped away into the night air."
    )


def settle(world: World, elder: Entity, plan: HelperPlan, vessel: Vessel, resource: Resource) -> None:
    body = plan.text
    if body:
        world.say(
            f"{elder.id} smiled, took the rope from both hands, and {body}."
        )
    world.say(
        f"The children went quiet, because the old {resource.label} was not a thing for winning. It was a thing for sharing."
    )


def ending(world: World, hero: Entity, rival: Entity, vessel: Vessel, resource: Resource) -> None:
    hero.memes["joy"] += 1
    rival.memes["joy"] += 1
    world.say(
        f"At last the {vessel.label} rose over the roof tiles, shining like a lantern moon, while the last of the {resource.label} gleamed safely inside."
    )
    world.say(
        f"{hero.id} and {rival.id} stood shoulder to shoulder in the meadow, watching it bob above the cottages, their quarrel softened into a shared smile."
    )


def tell(params: StoryParams) -> World:
    if params.village not in VILLAGES or params.vessel not in VESSELS or params.resource not in RESOURCES or params.helper_plan not in PLANS:
        raise StoryError("Invalid story parameters.")
    vessel = VESSELS[params.vessel]
    resource = RESOURCES[params.resource]
    plan = PLANS[params.helper_plan]
    if not reasonableness_gate(vessel, resource):
        raise StoryError(explain_rejection(vessel, resource))

    world = World()
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    rival = world.add(Entity(id=params.rival, kind="character", type=params.rival_gender, role="rival"))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder_gender, role="elder"))
    world.facts.update(village=VILLAGES[params.village], vessel=vessel, resource=resource, plan=plan,
                       supply=params.supply, ration_need=params.ration_need, delay=params.delay)

    opening(world, hero, rival, VILLAGES[params.village], vessel)
    world.para()
    conflict(world, hero, rival, elder, vessel)
    warn(world, elder, hero, rival, params.ration_need)
    quarrel(world, hero, rival)
    world.para()
    settle(world, elder, plan, vessel, resource)
    ending(world, hero, rival, vessel, resource)
    world.facts.update(hero=hero, rival=rival, elder=elder, outcome="resolved")
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale style story that includes the words "ration" and "helium" and ends with a calm village night.',
        f"Tell a small conflict story where {f['hero'].id} and {f['rival'].id} argue over a ration of helium, but an elder finds a fair way forward.",
        f'Write a child-friendly folk tale about sharing helium carefully, with a quarrel, a warning, and a bright ending.'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    rival: Entity = f["rival"]
    elder: Entity = f["elder"]
    vessel: Vessel = f["vessel"]
    resource: Resource = f["resource"]
    return [
        QAItem(
            question=f"Why did {hero.id} and {rival.id} start arguing?",
            answer=f"They both wanted to guide the {vessel.label}, but there was only a small ration of {resource.label}. That made them fear there would not be enough unless someone decided fairly."
        ),
        QAItem(
            question=f"How did {elder.id} end the conflict?",
            answer=f"{elder.id} stepped in, took the rope, and chose a fair plan instead of letting the children pull and spill the gas. That calm choice turned the fight into sharing."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The {vessel.label} rose at last, and the village saw it glow above the roofs. The quarrel ended with both children standing together, watching the bright little shape drift safely in the night."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is helium?",
            answer="Helium is a very light gas. People use it to fill balloons, lanterns, and other things that need to float."
        ),
        QAItem(
            question="What is a ration?",
            answer="A ration is a small measured share of something. It means each person gets only a careful amount so it lasts."
        ),
        QAItem(
            question="Why should people share a scarce supply carefully?",
            answer="When a supply is scarce, wasting it can leave everyone with nothing. Careful sharing helps the group finish the job and keeps the peace."
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(village="hill", vessel="lantern", resource="helium", helper_plan="patch",
                hero="Mira", hero_gender="girl", rival="Pip", rival_gender="boy",
                elder="Grandmother Reed", elder_gender="woman", ration_need=2, supply=1),
    StoryParams(village="river", vessel="kite", resource="helium", helper_plan="swap",
                hero="Jory", hero_gender="boy", rival="Anka", rival_gender="girl",
                elder="Old Mara", elder_gender="woman", ration_need=3, supply=2),
    StoryParams(village="orchard", vessel="balloon", resource="helium", helper_plan="stitch",
                hero="Nell", hero_gender="girl", rival="Roan", rival_gender="boy",
                elder="Aunt Wren", elder_gender="woman", ration_need=2, supply=1),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world about rationed helium and village conflict.")
    ap.add_argument("--village", choices=VILLAGES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--resource", choices=RESOURCES)
    ap.add_argument("--helper-plan", choices=PLANS, dest="helper_plan")
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"], dest="hero_gender")
    ap.add_argument("--rival")
    ap.add_argument("--rival-gender", choices=["girl", "boy", "woman", "man"], dest="rival_gender")
    ap.add_argument("--elder")
    ap.add_argument("--elder-gender", choices=["woman", "man", "girl", "boy"], dest="elder_gender")
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
    if args.resource and args.resource != "helium":
        raise StoryError("This tale needs helium.")
    combos = [c for c in valid_combos()
              if (args.village is None or c[0] == args.village)
              and (args.vessel is None or c[1] == args.vessel)
              and (args.resource is None or c[2] == args.resource)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    village, vessel, resource = rng.choice(sorted(combos))
    helper_plan = args.helper_plan or rng.choice(sorted(PLANS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    rival_gender = args.rival_gender or ("boy" if hero_gender == "girl" else "girl")
    elder_gender = args.elder_gender or rng.choice(["woman", "man"])
    hero = args.hero or rng.choice(HERO_NAMES)
    rival = args.rival or rng.choice([n for n in RIVAL_NAMES if n != hero])
    elder = args.elder or rng.choice(ELDER_NAMES)
    return StoryParams(
        village=village,
        vessel=vessel,
        resource=resource,
        helper_plan=helper_plan,
        hero=hero,
        hero_gender=hero_gender,
        rival=rival,
        rival_gender=rival_gender,
        elder=elder,
        elder_gender=elder_gender,
        ration_need=rng.choice([1, 2, 3]),
        supply=rng.choice([1, 1, 2]),
        delay=0,
        hero_age=rng.randint(6, 9),
        rival_age=rng.randint(5, 8),
        relation=rng.choice(["siblings", "friends"]),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        world = tell(params)
    except StoryError:
        raise
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


ASP_RULES = r"""
valid(V, Ve, R) :- village(V), vessel(Ve), resource(R), helium(R).
conflict(H, Ri) :- hero(H), rival(Ri).
resolved :- elder(E), choose(E), ration(R), helium(G), share(R, G).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for v in VILLAGES:
        lines.append(asp.fact("village", v))
    for vid in VESSELS:
        lines.append(asp.fact("vessel", vid))
    for rid in RESOURCES:
        lines.append(asp.fact("resource", rid))
        if rid == "helium":
            lines.append(asp.fact("helium", rid))
    for pid in PLANS:
        lines.append(asp.fact("plan", pid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp as _asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate/emit smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos.")
        for c in asp_valid_combos():
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
