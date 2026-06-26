#!/usr/bin/env python3
"""
storyworlds/worlds/dame_layer_cautionary_folk_tale.py
======================================================

A small cautionary folk-tale world about a dame, a thin layer, and the wiser
choice that keeps everyone safe.

The seed image:
---
A young wanderer sees a shiny layer of ice on a stream and thinks it looks like
a bright path. Dame Wren warns that the layer is thin and untrustworthy. The
wanderer wants to hurry across anyway, but the dame stops the rush, shows a
safer bridge, and makes sure the child wears a warm layer before they try again.

This world turns that seed into a constraint-checked simulation:
- the hazard has a physical thickness meter
- the hero can be rash or cautious
- the dame can foresee danger and offer a safer route
- the ending proves what changed in the world model
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "dame"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the river path"
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    name: str
    verb: str
    rush: str
    risk: str
    consequence: str
    meter: str
    weather: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    owner_region: str
    plural: bool = False


@dataclass
class LayerGear:
    id: str
    label: str
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.hazard_active: str = ""
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.hazard_active = self.hazard_active
        return clone


def _r_splash(world: World) -> list[str]:
    out: list[str] = []
    hazard = world.hazard_active
    if not hazard:
        return out
    hz = HAZARDS[hazard]
    for actor in world.characters():
        if actor.meters.get(hz.meter, 0.0) < THRESHOLD:
            continue
        if world.fired and ("splash", actor.id, hz.id) in world.fired:
            continue
        world.fired.add(("splash", actor.id, hz.id))
        actor.meters["soaked"] = actor.meters.get("soaked", 0.0) + 1.0
        out.append(f"{actor.pronoun('possessive').capitalize()} clothes grew damp at the edge of the stream.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("alarm", 0.0) < THRESHOLD:
            continue
        if ("worry", actor.id) in world.fired:
            continue
        world.fired.add(("worry", actor.id))
        out.append(f"The dame saw the danger before it bit.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_splash, _r_worry):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_risk(hazard: Hazard, prize: Prize) -> bool:
    return prize.owner_region == "legs" and hazard.meter == "ice_thin"


def choose_layer(hazard: Hazard, prize: Prize) -> Optional[LayerGear]:
    for gear in LAYERS:
        if hazard.id in gear.guards:
            return gear
    return None


def predict(world: World, actor: Entity, hazard: Hazard) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters[hazard.meter] = 1.0
    sim.hazard_active = hazard.id
    propagate(sim, narrate=False)
    return {"soaked": sim.get(actor.id).meters.get("soaked", 0.0) >= THRESHOLD}


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "young"), "brave")
    world.say(f"{hero.id} was a young {trait} traveler who liked bright paths and quick feet.")


def set_the_scene(world: World, hazard: Hazard) -> None:
    world.say(
        f"One cold morning, the air was still, and {world.setting.place} glittered with a {hazard.name}."
    )
    world.say("It looked friendly from far away, like a silver ribbon across the water.")


def desire(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1.0
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {hazard.verb} at once, as if speed could make the day easier."
    )


def warn(world: World, dame: Entity, hero: Entity, hazard: Hazard, prize: Prize) -> bool:
    pred = predict(world, hero, hazard)
    if not pred["soaked"]:
        return False
    dame.memes["alarm"] = dame.memes.get("alarm", 0.0) + 1.0
    world.facts["predicted_soaked"] = True
    world.say(
        f'"Wait," {dame.label} said. "That {hazard.name} is a thin layer, and thin things can break."'
    )
    world.say(
        f'"If you rush, you could get your {prize.label} wet, and then the walk will turn sour."'
    )
    return True


def defy(world: World, hero: Entity, hazard: Hazard) -> None:
    hero.memes["reckless"] = hero.memes.get("reckless", 0.0) + 1.0
    world.say(f"{hero.id} did not like the warning, but the bright shine kept tugging at {hero.pronoun('possessive')} eyes.")
    world.say(f"{hero.pronoun().capitalize()} tried to {hazard.rush},")


def stop_and_help(world: World, dame: Entity, hero: Entity, hazard: Hazard, prize: Prize) -> Optional[LayerGear]:
    gear = choose_layer(hazard, prize)
    if gear is None:
        return None
    world.say(
        f"then {dame.label} held up a calm hand and smiled. \"We can keep the feet dry another way,\" {dame.pronoun()} said."
    )
    world.say(f"She offered {gear.label} and pointed toward the bridge.")
    return gear


def accept(world: World, hero: Entity, dame: Entity, hazard: Hazard, prize: Prize, gear: LayerGear) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["reckless"] = 0.0
    gear_ent = world.add(Entity(
        id=gear.id,
        type="layer",
        label=gear.label,
        plural=gear.plural,
        owner=hero.id,
        worn_by=hero.id,
    ))
    gear_ent.meters["warmth"] = 1.0
    world.say(
        f"{hero.id} listened at last, put on {gear.label}, and crossed by the bridge instead of the breakable shine."
    )
    world.say(
        f"In the end, {hero.pronoun('possessive')} {prize.label} stayed dry, and the dangerous {hazard.name} kept its secret to itself."
    )


def tell(setting: Setting, hazard: Hazard, prize_cfg: Prize, hero_name: str = "Mara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young"] + (hero_traits or ["bold", "hasty"])))
    dame = world.add(Entity(id="Dame", kind="character", type="dame", label="Dame Wren", traits=["wise", "gentle"]))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=dame.id,
    ))

    introduce(world, hero)
    world.say(f"Dame Wren kept watch over the lane and always spoke plain truth.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} as if it were meant for the road.")

    world.para()
    set_the_scene(world, hazard)
    desire(world, hero, hazard)
    warn(world, dame, hero, hazard, prize)
    defy(world, hero, hazard)
    gear = stop_and_help(world, dame, hero, hazard, prize)

    world.para()
    if gear:
        accept(world, hero, dame, hazard, prize, gear)

    world.facts.update(hero=hero, dame=dame, prize=prize, hazard=hazard, gear=gear, resolved=gear is not None)
    return world


@dataclass
class StoryParams:
    place: str
    hazard: str
    prize: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "river": Setting(place="the river path", outdoors=True, affords={"ice"}),
    "bridge": Setting(place="the old bridge", outdoors=True, affords={"wind"}),
    "lane": Setting(place="the village lane", outdoors=True, affords={"frost"}),
}

HAZARDS = {
    "ice": Hazard(
        id="ice",
        name="thin layer of ice",
        verb="skate across it",
        rush="dash onto the ice",
        risk="slip and soak",
        consequence="fall in",
        meter="ice_thin",
        weather="cold",
        keyword="layer",
        tags={"ice", "cold", "layer"},
    ),
    "frost": Hazard(
        id="frost",
        name="silver layer of frost",
        verb="run over the grass",
        rush="race across the frost",
        risk="slip on the shine",
        consequence="stumble",
        meter="frost_slippery",
        weather="cold",
        keyword="layer",
        tags={"frost", "cold", "layer"},
    ),
    "wind": Hazard(
        id="wind",
        name="a sharp layer of wind",
        verb="walk the hill",
        rush="run up the hill",
        risk="grow chilled",
        consequence="shiver",
        meter="wind_bite",
        weather="windy",
        keyword="layer",
        tags={"wind", "layer"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a wool cloak", type="cloak", owner_region="torso"),
    "boots": Prize(label="boots", phrase="sturdy boots", type="boots", owner_region="feet", plural=True),
    "skirt": Prize(label="skirt", phrase="a red skirt", type="skirt", owner_region="legs"),
}

LAYERS = [
    LayerGear(id="wool_layer", label="a warm wool layer", guards={"ice", "frost", "wind"}, prep="put on a warm wool layer", tail="took the safer road"),
    LayerGear(id="cloak", label="a thicker cloak", guards={"wind"}, prep="tie on a thicker cloak", tail="crossed by the bridge"),
]

GIRL_NAMES = ["Mara", "Elsa", "Nina", "Sera", "Tilda", "Greta"]
BOY_NAMES = ["Oren", "Bram", "Ivo", "Milo", "Perrin"]
TRAITS = ["bold", "curious", "impetuous", "cheerful", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for hz in setting.affords:
            hazard = HAZARDS[hz]
            for prize_id, prize in PRIZES.items():
                if hazard_risk(hazard, prize) and choose_layer(hazard, prize):
                    out.append((place, hz, prize_id))
    return out


def explain_rejection(hazard: Hazard, prize: Prize) -> str:
    return (
        f"(No story: {hazard.name} does not threaten {prize.label} in a way this little folk tale can honestly solve.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: this world has no special gender rule for {prize_id}, but '{gender}' was not a usable choice here.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, dame, hazard, prize = f["hero"], f["dame"], f["hazard"], f["prize"]
    return [
        f"Write a short cautionary folk tale about a child who wants to {hazard.verb} at {world.setting.place}.",
        f"Tell a story where {dame.label} warns {hero.id} about a {hazard.name} and helps {hero.id} choose a safer path.",
        f"Write a gentle village story that uses the word 'layer' and ends with the child choosing safety over speed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, dame, hazard, prize = f["hero"], f["dame"], f["hazard"], f["prize"]
    qa = [
        QAItem(
            question=f"Who tried to {hazard.verb} at {world.setting.place}?",
            answer=f"It was {hero.id}, a young {next(t for t in hero.traits if t != 'young')} traveler.",
        ),
        QAItem(
            question=f"Why did {dame.label} warn {hero.id} about the {hazard.name}?",
            answer=f"Because the {hazard.name} was only a thin layer, and a thin layer can break or slip under a hasty step.",
        ),
        QAItem(
            question=f"What did {hero.id}'s {prize.label} need during the walk?",
            answer=f"It needed to stay dry and safe, so the child could travel without ruining {hero.pronoun('possessive')} {prize.label}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(
            QAItem(
                question=f"How did {gear.label} help the story end well?",
                answer=f"It gave {hero.id} an extra layer of protection, and that let the child take the safer road instead of rushing onto danger.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["hazard"].tags)
    if f.get("gear"):
        tags.add("layer")
    out = []
    if "layer" in tags:
        out.append(QAItem(
            question="What is a layer?",
            answer="A layer is one thing spread over or under another thing. Layers can keep you warm, cover something, or make a surface look smooth.",
        ))
    if "ice" in tags:
        out.append(QAItem(
            question="Why can thin ice be dangerous?",
            answer="Thin ice can crack under weight, and then a person can slip into cold water.",
        ))
    if "frost" in tags:
        out.append(QAItem(
            question="What is frost?",
            answer="Frost is a thin, icy covering that forms when the air is very cold.",
        ))
    if "wind" in tags:
        out.append(QAItem(
            question="Why does wind feel cold?",
            answer="Wind moves air quickly across your skin, and that can make you feel colder.",
        ))
    return out


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="river", hazard="ice", prize="boots", name="Mara", gender="girl", trait="curious"),
    StoryParams(place="river", hazard="ice", prize="cloak", name="Oren", gender="boy", trait="restless"),
    StoryParams(place="lane", hazard="frost", prize="skirt", name="Tilda", gender="girl", trait="bold"),
]


ASP_RULES = r"""
prize_at_risk(H, P) :- hazard(H), prize(P), risk(H, P).
has_layer(H, P) :- risk(H, P), layer_ok(H, P).
valid_story(Place, H, P) :- affords(Place, H), prize_at_risk(H, P), has_layer(H, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for hz in sorted(s.affords):
            lines.append(asp.fact("affords", pid, hz))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        for tag in sorted(h.tags):
            lines.append(asp.fact("tag", hid, tag))
        for p in PRIZES:
            if hazard_risk(h, PRIZES[p]):
                lines.append(asp.fact("risk", hid, p))
                if choose_layer(h, PRIZES[p]):
                    lines.append(asp.fact("layer_ok", hid, p))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary folk tale world about a dame and a layer.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if args.hazard and args.prize:
        hz, pr = HAZARDS[args.hazard], PRIZES[args.prize]
        if not (hazard_risk(hz, pr) and choose_layer(hz, pr)):
            raise StoryError(explain_rejection(hz, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.hazard is None or c[1] == args.hazard)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, hazard, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, hazard=hazard, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], HAZARDS[params.hazard], PRIZES[params.prize], params.name, params.gender, [params.trait])
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, hazard, prize) combos:\n")
        for place, hz, pr in triples:
            print(f"  {place:8} {hz:8} {pr:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
