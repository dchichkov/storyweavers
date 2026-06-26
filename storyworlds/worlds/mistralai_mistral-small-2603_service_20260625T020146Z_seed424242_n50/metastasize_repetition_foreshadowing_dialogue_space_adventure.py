#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.2

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "item"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        it = {"gem": "it", "crystal": "it", "bot": "it", "captain": "he", "scientist": "she"}.get(self.type, "it")
        return {"subject": it, "object": it, "possessive": it}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

@dataclass
class Setting:
    place: str = "space station"
    role: str = "research lab"
    quadrant: str = "upper ring"
    indoor: bool = True

@dataclass
class Hazard:
    id: str
    verb: str
    gerund: str
    rush: str
    onset: str
    spread: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)

@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False

class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.glances: list[str] = []
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities.get(eid)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def items(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "thing"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def glance(self, text: str) -> None:
        self.glances.append(text)

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_grow(world: World) -> list[str]:
    out: list[str] = []
    for item in world.items():
        if "growth" not in item.meters:
            continue
        if world.zone and item.worn_by is None:
            item.meters["growth"] *= 1.5
            out.append(f"The {item.label} pulsed softly under the station lights.")
    return out

def _r_contagion(world: World) -> list[str]:
    out: list[str] = []
    danger = sum(m for e in world.entities.values() for m in e.meters.values() if m >= THRESHOLD)
    if danger < 1:
        return out
    for actor in world.characters():
        for item in world.items():
            if item.meters.get("growth", 0) < THRESHOLD:
                continue
            sig = ("contagion", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["contagion"] += 0.8
            item.meters["spread"] += 0.35
            part = "surface" if item.plural else "edge"
            out.append(f"{actor.pronoun('subject').capitalize()} {actor.id} stared as the strange {item.label} {part} began to pulse brighter.")
    return out

def _r_critical_failure(world: World) -> list[str]:
    if any(m >= THRESHOLD * 2.2 for e in world.entities.values() for m in {"growth","spread"}.intersection(map(str,e.meters.keys())) if "vital" in e.id):
        return ["__alarm__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="growth_accel", tag="hazard", apply=_r_grow),
    Rule(name="contagion", tag="hazard", apply=_r_contagion),
    Rule(name="alarm", tag="failure", apply=_r_critical_failure),
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
                produced.extend(s for s in sents if s != "__alarm__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "junior"), "")
    role = "captain" if hero.type == "captain" else "lead scientist"
    world.say(f"Commander {hero.id} was a {trait} {role} stationed in {world.setting.quadrant}.")

def notices_anomaly(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["observe"] += 1
    world.say(f"{hero.id} noticed the {item.label} looked different that morning and made a note in the science log.")

def check_growth(world: World) -> float:
    return sum(item.meters.get("growth",0) for item in world.items() if "growth" in item.meters)

def urgent_warning(world: World, hero: Entity, parent_type: str) -> None:
    hero.memes["dread"] += 0.9
    owner = "their" if parent_type == "lead scientist" else "her"
    world.say(f'"This is getting worse," {hero.id} said into the comm. "The {parent_type.lower()} stared at the data screen, voice tight. "We have to act before the crystals metastasize any further."')

def defies_protocol(world: World, hero: Entity, authority_type: str) -> None:
    hero.memes["defiance"] += 1
    auth = "Dr " if authority_type == "lead scientist" else "Captain "
    world.say(f'{auth}{hero.id.split()[-1]} heard the warning but turned back to the {world.setting.role}. "Not yet," {hero.pronoun("subject")} said quietly, "we can still fix this."')

def grab_arm(world: World, captain: Entity, hero: Entity, item: Entity) -> None:
    hero.memes["grabbed_by"] += 0.8
    item.meters["quarantine"] = 1.0
    propagate(world, narrate=False)
    auth = "Dr " if captain.type == "scientist" else ""
    world.say(f'"Stop!" {auth}{captain.id.split()[-1]} grabbed {hero.pronoun("object")} arm before {hero.pronoun("object")} fingers brushed the {item.label}. "It is not safe."')

def compromised_planning(world: World, hero: Entity) -> None:
    if hero.memes["contagion"] >= 0.7:
        world.say(f'{hero.id} swallowed hard as the readings flared across every screen. "It is metastasizing faster than we predicted," {hero.pronoun("subject")} muttered, "and the life support is next."')

def evacuate_dialogue(world: World, lead: Entity, hero: Entity) -> None:
    auth = "Dr" if lead.type == "scientist" else "Captain"
    world.say(f'"Evacuate section twelve," {auth} {lead.id} ordered into the comm. "Seal bulkheads and reroute power to {world.setting.role}."')
    if hero.memes["dread"] < 0.5:
        hero.memes["dread"] *= 1.3

def stabilize_plan(world: World, scientist: Entity, gear: Entity) -> Optional[Gear]:
    gear.worn_by = scientist.id
    gear.caretaker = None
    world.say(f'"We can use the {gear.label} to contain it," {scientist.id} said, adjusting the frequency knobs. "Activate the harmonic stabilizers and we might slow the growth."')
    return gear

def aftermath(world: World, captain: Entity, scientist: Entity) -> None:
    captain.memes["resolve"] += 1
    scientist.memes["success"] += 1
    operator = "d" if scientist.pronoun() == "she" else ""
    world.say(f'Later in the observation deck, {captain.pronoun("subject")} {captain.id} watched {scientist.id}{operator} work. "We stopped the growth from metastasizing further," {captain.pronoun("subject")} said quietly. "The station is safe once more."')
    world.say(f'Outside the viewport the cosmos glittered cold and quiet. Whatever had tried to take root here was pushed back—{world.setting.role} glowing steady once again.')

def tell(setting: Setting, hazard: Hazard, scientist_name: str = "Quinn", lead_name: str = "Rena") -> World:
    world = World(setting)
    scientist = world.add(Entity(id=scientist_name, kind="character", type="scientist", traits=["patient","keeneyed"], label="Dr Quinn", region="labs"))
    captain = world.add(Entity(id=lead_name, kind="character", type="captain", traits=["firm","calm"], label="Captain Rena", region="bridge"))

    vital_system = world.add(Entity(id="life_support_vital", kind="thing", type="system", phrase="a vital life-support crystal cluster in section twelve", region="core"))
    anomaly = world.add(Entity(id="anomaly_growth", kind="thing", type="crystal_hazard", phrase="strange blue growth budding on the storage hull", region="cargo"))
    stabilizer = world.add(Entity(id="harmonic_stabilizer", kind="thing", type="gear", phrase="a harmonic stabilizer module from storage", region="deck", covers={"core"}, protective=True))

    vital_system.meters["vital"] = 1.0
    anomaly.meters["growth"] = 0.3
    stabilizer.covers.update(["section twelve","core"])
    vital_system.caretaker = captain.id
    anomaly.owner = scientist.id
    stabilizer.owner = scientist.id

    world.para()
    introduce(world, captain)
    introduce(world, scientist)
    notices_anomaly(world, scientist, anomaly)

    world.para()
    world.say(f'"Ambient readings jumped again," {scientist.id} told the comm, voice calm but focused. "Blue crystals growing faster than crystalline analogues predict."')
    check = check_growth(world)
    if check >= 0.8:
        urgent_warning(world, captain, scientist.type)

    world.para()
    defies_protocol(world, scientist, scientist.type)
    grab_arm(world, captain, scientist, anomaly)

    world.para()
    compromised_planning(world, scientist)
    evacuate_dialogue(world, captain, scientist)

    world.para()
    gear = stabilize_plan(world, scientist, stabilizer)
    if gear:
        aftermath(world, captain, scientist)

    world.facts.update(captain=captain, scientist=scientist, vital=vital_system, growth=anomaly, stabilizer=gear, contagion=scientist.memes.get("contagion",0)>=0.4, resolved=gear is not None)
    return world

SETTINGS = {
    "upper": Setting(place="star station", quadrant="upper ring sector"),
    "hab": Setting(place="habitat ring", quadrant="central tier"),
}

HAZARDS = {
    "crystal": Hazard(
        id="crystal",
        verb="enter the contaminated cargo bay",
        gerund="examining the crystal bud",
        rush="dash toward the growth",
        onset="blue crystals spreading across the hull",
        spread="metastasizing through the deck plating",
        zone={"cargo","deck"},
        keyword="crystal",
        tags={"contagion","hazard","space"},
    ),
}

GEAR = [
    Gear(
        id="harmonic",
        label="harmonic stabilizer",
        covers={"cargo","deck"},
        guards={"contagion"},
        prep="power it up and place the stabilizer near the growth",
        tail="the two teammates positioned the module exactly where the crystals pulsed brightest",
    ),
]

STABILIZERS = {"harmonic"}

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cap, sci = f["captain"], f["scientist"]
    kw = f["growth"].keywords()
    return [
        f'Tell a short space-adventure story for ages 5–7 where astronauts face an alien crystal that starts to metastasize. Include the word "{kw[0]}".',
        f'Write a child’s tale set on a research station where Dr {sci.id.split()[-1]} must convince Captain {cap.id.split()[-1]} to let {sci.pronoun("object")} investigate the strange growth before it metastasizes any further.',
        f'Write a gentle space story that uses the noun "{kw[0]}" and features two teammates arguing about safety vs discovery.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap, sci, vital, growth = f["captain"], f["scientist"], f["vital"], f["growth"]
    sub, obj, pos = sci.pronoun("subject"), sci.pronoun("object"), sci.pronoun("possessive")
    kw = growth.keyword
    qa: list[QAItem] = [
        QAItem(
            question="Who are the two crew members in this story?",
            answer=f"The commander, Captain {cap.id}, and the lead scientist, Dr {sci.id}. Together they watched the strange {kw} start to metastasize on their station.",
        ),
        QAItem(
            question="What did Dr Quinn see that made {pos} bring the matter to Captain Rena’s attention?",
            answer=f"Dr Quinn noticed the {kw} pulsing brighter in the cargo hold and recorded higher ambient readings in {pos} science log.",
        ),
        QAItem(
            question=f"What happened when the crystals started to {growth.verb} harmful levels?",
            answer=f'Captain Rena called for evacuation of section twelve as soon as the vital system crystal read danger. "The growth is metastasizing too fast," {cap.pronoun("subject")} warned everyone over the comm.',
        ),
    ]
    if f.get("contagion"):
        qa.append(QAItem(
            question="Why did Dr Quinn have to be stopped from touching the {kw}?",
            answer=f"The crystals pulsed too brightly at that moment and were spreading. Captain Rena grabbed {obj} arm: harmful {kw} growth had to be contained first before {obj} could continue analyzing it.",
        ))
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did Dr Quinn and Captain Rena finally stop the dangerous {kw}?",
            answer=f'They powered up the harmonic stabilizer from storage and positioned it beside the {kw}. With precise knob adjustments Dr Quinn stabilized the harmonic frequencies and the {kw} stopped metastasizing any further.',
        ))
    return qa

KNOWLEDGE = {
    "crystal": [("What is a space crystal?",
                 "A space crystal is a glowing lump that grows on the walls of space ships when energy mixes with metal dust.")],
    "metastasize": [("What does metastasize mean?",
                     "Metastasize means something spreads quickly and dangerously from one spot to others, like a cold that turns into a fever.")],
    "harmonic": [("What is a harmonic stabilizer?",
                  "A harmonic stabilizer is a machine that sends out waves to calm down vibrating or growing things so they won’t break other parts around them.")],
}

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(["crystal", "harmonic"])
    out: list[QAItem] = []
    for tag in ["crystal","metastasize","harmonic"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out

def dump_trace(world: World) -> str:
    lines = ["--- world state trace ---"]
    for e in world.entities.values():
        meters = {k:round(v,2) for k,v in e.meters.items() if v}
        memes = {k:round(v,2) for k,v in e.memes.items() if v}
        parts = []
        if meters: parts.append(f"meters={meters}")
        if memes: parts.append(f"memes={memes}")
        if e.protective: parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:15} {e.type:10} {', '.join(parts)}" if parts else "")
    lines.append(f"  triggered: {sorted(set(n for n,*_ in world.fired))}")
    return "\n".join(lines)

ASP_RULES = r"""
% A containment breach occurs when growth reaches a vital system.
at_risk(System,Crew) :- vital(System), growth(G), station(S),
                       covers(G, Section), region(System, Section),
                       crew_meme(Crew, contagion, Risk), Risk >= 1.

% Stabilizer works when placed in the same section as the growth.
stabilized :- stabilizer(Stab), growth(Gr), same_section(Gr,Stab),
              guards(Stab, contagion), place(Stab, Sec), place(Gr, Sec).

% A story is valid if the crew acts before the vital system is compromised.
valid_story :- crew(C), at_risk(vital, C), stabilize_plan(C), resolved.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, s in SETTINGS.items():
        lines.append(asp.fact("station", key))
        lines.append(asp.fact("quadrant", key, s.quadrant))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("keyword", hid, h.keyword))
        for z in sorted(h.zone):
            lines.append(asp.fact("zone", hid, z))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    for sid in STABILIZERS:
        lines.append(asp.fact("stabilizer", sid))
        lines.append(asp.fact("guard", sid, "contagion"))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

@dataclass
class StoryParams:
    place: str
    hazard: str
    stabilizer: str
    scientist_name: str
    lead_name: str

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure micro world: drifting crystals on a research station.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--stabilizer", choices=STABILIZERS)
    ap.add_argument("--scientist_name")
    ap.add_argument("--lead_name")
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
    valid = [(p,h,g) for p in SETTINGS for h in HAZARDS for g in STABILIZERS]
    if not valid:
        raise StoryError("(No valid story configuration exists.)")
    place,hazard,stabilizer = rng.choice(valid)
    return StoryParams(
        place=place,
        hazard=hazard,
        stabilizer=stabilizer,
        scientist_name=rng.choice(["Quinn","Jax","Tess","Mira","Nori"]),
        lead_name=rng.choice(["Rena","Kira","Taro","Dax","Vega"]),
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], HAZARDS[params.hazard], params.scientist_name, params.lead_name)
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
        from results import QAItem
        lines = ["\n== Story reasoning =="]
        for item in sample.story_qa:
            lines.append(f"Q: {item.question}\nA: {item.answer}")
        lines.append("\n== Small-space world facts ==")
        for item in sample.world_qa:
            lines.append(f"Q: {item.question}\nA: {item.answer}")
        print("\n".join(lines))

def asp_verify() -> int:
    try:
        import asp
        pc = set((p,h,g) for p in SETTINGS for h in HAZARDS for g in STABILIZERS)
        ac = set(asp.atoms(asp.one_model(asp_program("#show valid_story/0.")), "valid_story"))
        if pc != ac:
            print("Mismatch between Python and ASP compilers.")
            return 1
        print("OK: both Python and ASP compilers produce the same valid stories.")
        return 0
    except Exception as e:
        print(f"ASP verification error: {e}")
        return 2

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import asp
            print("ASP-valid configurations:")
            print(asp.one_model(asp_program("#show valid_story/0.")))
            return
        except Exception as e:
            print(f"ASP run failed: {e}")
            return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        pairs = [("upper","crystal","harmonic"),("hab","crystal","harmonic")]
        samples = [generate(StoryParams(p,h,g,"Quinn","Rena")) for p,h,g in pairs]
    else:
        seen = set()
        for i in range(max(args.n*10,20)):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
                if len(samples) >= args.n:
                    break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i,s in enumerate(samples):
        header = f"### Mission log #{i+1}: Dr {s.params.scientist_name.split()[-1]} vs metastasizing crystals"
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples)-1:
            print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    main()
