#!/usr/bin/env python3
"""
storyworlds/worlds/pelt_mistress_sound_effects_reconciliation_space_adventure.py
===============================================================================

A small, standalone story world in a Space Adventure style.

Seed image:
---
A little crew sails a bright ship through quiet space. The ship is pelted by
tiny rocks and noisy sparks. The mistress of the ship worries about a broken
panel, but the young space-rider wants to keep going. After a sharp moment,
they repair the damage together, swap a sorry smile, and the ship hums on.

This world models:
- physical meters: damage, drift, charge, repair
- emotional memes: worry, pride, anger, relief, trust
- sound effects as narrative instruments
- reconciliation as the ending turn

The story is fully state-driven and complete, with a beginning, middle turn,
and ending image that proves what changed.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "mistress"}
        male = {"boy", "father", "dad", "man", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
    stars: str = ""


@dataclass
class Event:
    id: str
    verb: str
    gerund: str
    sound: str
    mess: str
    damage: str
    zone: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    hero_name: str
    hero_type: str
    mistress_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: str = ""
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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = self.zone
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def sound_line(sound: str, event: Event) -> str:
    return {
        "pelt": f"pelt-pelt-pelt!",
        "clang": f"clang!",
        "whirr": f"whirr...",
        "beep": f"beep-beep!",
        "whoosh": f"whoosh!",
    }.get(sound, sound + "!")


def activity_line(event: Event) -> str:
    return {
        "pelt": "tiny rocks tapped the hull like hard rain",
        "clang": "the loose panel rang sharply when it bumped the wall",
        "whirr": "the repair tool spun softly in the quiet cabin",
        "beep": "the little scanner blinked a bright warning light",
        "whoosh": "the shield curtain slid down with a smooth swoop",
    }.get(event.sound, "the ship made a strange noise")


def prize_at_risk(event: Event, prize: Entity) -> bool:
    return prize.id in RISK_BY_EVENT[event.id]


def select_gear(event: Event, prize: Entity) -> Optional[Gear]:
    for gear in GEAR:
        if event.mess in gear.guards and prize.id in gear.covers:
            return gear
    return None


def fixpoint(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("repair", 0.0) >= THRESHOLD and actor.memes.get("reconcile", 0.0) >= THRESHOLD:
            sig = ("reconcile", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("__reconcile__")
    return out


def predict_damage(world: World, actor: Entity, event: Event, prize_id: str) -> dict:
    sim = world.copy()
    do_event(sim, sim.get(actor.id), event, narrate=False)
    prize = sim.get(prize_id)
    return {
        "damaged": prize.meters.get("damaged", 0.0) >= THRESHOLD,
        "tension": sum(e.memes.get("worry", 0.0) + e.memes.get("anger", 0.0) for e in sim.characters()),
    }


def do_event(world: World, actor: Entity, event: Event, narrate: bool = True) -> None:
    world.zone = event.zone
    actor.meters[event.mess] = actor.meters.get(event.mess, 0.0) + 1
    if event.id == "pelt":
        actor.meters["drift"] = actor.meters.get("drift", 0.0) + 1
    if narrate:
        world.say(f"{sound_line(event.sound, event)} {activity_line(event)}")


def apply_damage(world: World, actor: Entity, prize: Entity, event: Event) -> None:
    if actor.meters.get(event.mess, 0.0) < THRESHOLD:
        return
    if prize.id in RISK_BY_EVENT[event.id]:
        sig = ("damage", prize.id, event.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        prize.meters["damaged"] = prize.meters.get("damaged", 0.0) + 1
        world.say(f"The {prize.label} got scratched, and that was a worry for the ship.")
        if prize.caretaker:
            carer = world.get(prize.caretaker)
            carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1


def tell(setting: Setting, event: Event, prize_cfg: "Prize", hero_name: str, hero_type: str, mistress_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    mistress = world.add(Entity(id=mistress_name, kind="character", type="mistress", label=mistress_name))
    prize = world.add(Entity(
        id=prize_cfg.id, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=mistress.id
    ))
    hero.meters["repair"] = 0
    mistress.memes["worry"] = 0

    world.say(f"{hero.id} was a small {hero_type} who loved space, bright buttons, and big quiet views.")
    world.say(f"On the ship called {setting.place}, {hero.id} wore {hero.pronoun('possessive')} {prize.label} like treasure.")
    world.say(f"{mistress.id}, the mistress of the ship, kept a careful eye on every panel and light.")

    world.para()
    world.say(f"One drift-dark moment, the ship flew under a belt of stones.")
    do_event(world, hero, event)
    apply_damage(world, hero, prize, event)
    world.say(f"{hero.id} wanted to keep going, but {mistress.pronoun('subject')} pointed at the {prize.label}.")
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    mistress.memes["worry"] = mistress.memes.get("worry", 0.0) + 1
    world.say(f'"If we rush now, we may lose it," {mistress.id} said.')

    world.para()
    hero.memes["anger"] = hero.memes.get("anger", 0.0) + 1
    world.say(f'{hero.id} frowned. "But I can fix it myself," {hero.pronoun()} said, too fast.')
    if prize_at_risk(event, prize):
        gear = select_gear(event, prize)
    else:
        gear = None
    if gear is None:
        raise StoryError("No safe gear exists for this space problem.")
    gear_ent = world.add(Entity(
        id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=mistress.id,
        plural=gear.plural
    ))
    world.say(f"Then {mistress.id} lifted {gear.label} with a soft {sound_line('whirr', event)}.")
    world.say(f'"How about we {gear.prep} together?"')
    hero.memes["anger"] = max(0.0, hero.memes["anger"] - 1)
    hero.memes["reconcile"] = hero.memes.get("reconcile", 0.0) + 1
    hero.meters["repair"] = hero.meters.get("repair", 0.0) + 1
    if gear_ent.label:
        world.say(f"{hero.id} nodded, took a breath, and used {gear.label} the careful way.")
    world.say(fix_line(event, prize, gear))
    world.say(f"{hero.id} and {mistress.id} touched hands and smiled the same small smile.")
    apply_reconciliation(world, hero, mistress, prize, event, gear)
    world.facts.update(hero=hero, mistress=mistress, prize=prize, event=event, gear=gear, setting=setting)
    return world


def fix_line(event: Event, prize: Entity, gear: Gear) -> str:
    return {
        "pelt": f"With the shield curtain down, the pelt of stones turned into harmless taps.",
        "clang": f"With the repair glove on, the clang became a neat little work sound.",
        "whirr": f"The whirr of the tool made the broken edge smooth again.",
        "beep": f"The beep on the scanner turned green when the crack closed.",
        "whoosh": f"The whoosh of the door kept the dust from drifting in.",
    }.get(event.id, f"The gear helped the {prize.label} stay safe.")


def apply_reconciliation(world: World, hero: Entity, mistress: Entity, prize: Entity, event: Event, gear: Gear) -> None:
    hero.memes["reconcile"] = hero.memes.get("reconcile", 0.0) + 1
    mistress.memes["trust"] = mistress.memes.get("trust", 0.0) + 1
    prize.meters["repaired"] = prize.meters.get("repaired", 0.0) + 1
    world.say(
        f"{mistress.id} said sorry for sounding stern, and {hero.id} said sorry for talking too sharply."
    )
    world.say(
        f"Together they fixed the {prize.label}, and the ship answered with a happy {sound_line('beep', event)}."
    )
    world.say(
        f"After that, the {prize.label} was safe again, and the stars seemed brighter through the window."
    )


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str


SETTINGS = {
    "comet_ship": Setting(place="the comet ship", afford={"pelt"}),
    "star_port": Setting(place="the star port", afford={"clang"}),
    "moon_dock": Setting(place="the moon dock", afford={"beep"}),
}

EVENTS = {
    "pelt": Event(id="pelt", verb="fly through the pelting stones", gerund="pelting through stones", sound="pelt", mess="damage", damage="scratched", zone="hull", tags={"space", "pelt"}),
    "clang": Event(id="clang", verb="cross the rattling dock", gerund="rattling along the dock", sound="clang", mess="repair", damage="loose", zone="panel", tags={"space", "clang"}),
    "beep": Event(id="beep", verb="scan the cracked light", gerund="scanning the light", sound="beep", mess="repair", damage="cracked", zone="light", tags={"space", "beep"}),
}

PRIZES = {
    "panel": Prize(id="panel", label="panel", phrase="a silver panel", type="thing"),
    "visor": Prize(id="visor", label="visor", phrase="a round visor", type="thing"),
    "antenna": Prize(id="antenna", label="antenna", phrase="a thin antenna", type="thing"),
}

GEAR = [
    Gear(id="shield", label="a shield curtain", guards={"damage"}, covers={"panel", "visor", "antenna"}, prep="raise the shield curtain and steer gently", tail="raised the shield curtain", plural=False),
    Gear(id="tool", label="a repair tool", guards={"repair"}, covers={"panel"}, prep="use the repair tool on the broken edge", tail="used the repair tool", plural=False),
    Gear(id="helmet", label="a bubble helmet", guards={"damage"}, covers={"visor"}, prep="put on the bubble helmet first", tail="put on the bubble helmet", plural=False),
]

RISK_BY_EVENT = {
    "pelt": {"panel", "visor", "antenna"},
    "clang": {"panel"},
    "beep": {"visor"},
}

HERO_NAMES = ["Nova", "Pip", "Lio", "Tess", "Milo", "Zuri"]
MISTRESS_NAMES = ["Mara", "Luna", "Seren", "Iris", "Vela"]
TYPES = ["boy", "girl"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for eid in setting.afford:
            ev = EVENTS[eid]
            for pid, prize in PRIZES.items():
                if prize_at_risk(ev, prize) and select_gear(ev, prize):
                    out.append((place, eid, pid))
    return out


def valid_pairs() -> list[tuple[str, str]]:
    return sorted((a, b) for _, a, b in valid_combos())


@dataclass
class StoryParams:
    place: str
    event: str
    prize: str
    hero_name: str
    hero_type: str
    mistress_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world with pelt, sound effects, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--mistress")
    ap.add_argument("--gender", choices=TYPES)
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


def explain_rejection(event: Event, prize: Prize) -> str:
    return f"(No story: the {event.id} problem does not honestly endanger the {prize.label} in this world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.prize is None or c[2] == args.prize)]
    if args.event and args.prize:
        ev, pr = EVENTS[args.event], PRIZES[args.prize]
        if not (prize_at_risk(ev, pr) and select_gear(ev, pr)):
            raise StoryError(explain_rejection(ev, pr))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(TYPES)
    return StoryParams(
        place=place,
        event=event,
        prize=prize,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=gender,
        mistress_name=args.mistress or rng.choice(MISTRESS_NAMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], EVENTS[params.event], PRIZES[params.prize],
                 params.hero_name, params.hero_type, params.mistress_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story for a young child that includes the sound word "{f["event"].sound}".',
        f"Tell a gentle story about {f['hero'].id} and {f['mistress'].id} reconciling after a space problem with the {f['prize'].label}.",
        f'Write a child-facing story where a ship is "{f["event"].id}" by space debris and ends with a happy repair.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mistress = f["mistress"]
    prize = f["prize"]
    event = f["event"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about on the ship?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {mistress.id}, the mistress of the ship.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} when the ship went through the stone field?",
            answer=f"The {prize.label} got scratched, and that made {mistress.id} worry.",
        ),
        QAItem(
            question=f"What sound helped show the space problem?",
            answer=f"The story used the sound {sound_line(event.sound, event)} to make the problem feel alive.",
        ),
        QAItem(
            question=f"How did {hero.id} and {mistress.id} fix the trouble?",
            answer=f"They used {gear.label} and repaired the {prize.label} together, then they said sorry and felt better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pelt in a space story?",
            answer="A pelt is a quick stream of small things hitting something again and again, like tiny rocks tapping a ship.",
        ),
        QAItem(
            question="What does a mistress mean in this story?",
            answer="A mistress is the woman in charge of the ship, the one who keeps things safe and working well.",
        ),
        QAItem(
            question="Why do repair tools help in space?",
            answer="Repair tools help because they can fix cracks, loose parts, and broken pieces before they cause more trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(E,P) :- event(E), prize(P), risk(E,P).
has_fix(E,P) :- prize_at_risk(E,P), gear(G), guards(G,M), event_mess(E,M), covers(G,P).
valid(Place,E,P) :- setting(Place), affords(Place,E), prize_at_risk(E,P), has_fix(E,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for e in SETTINGS[sid].afford:
            lines.append(asp.fact("affords", sid, e))
    for eid, ev in EVENTS.items():
        lines.append(asp.fact("event", eid))
        lines.append(asp.fact("event_mess", eid, ev.mess))
        for p in RISK_BY_EVENT[eid]:
            lines.append(asp.fact("risk", eid, p))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in gear.guards:
            lines.append(asp.fact("guards", gear.id, g))
        for c in gear.covers:
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="comet_ship", event="pelt", prize="panel", hero_name="Nova", hero_type="girl", mistress_name="Mara"),
    StoryParams(place="star_port", event="clang", prize="panel", hero_name="Pip", hero_type="boy", mistress_name="Luna"),
    StoryParams(place="moon_dock", event="beep", prize="visor", hero_name="Tess", hero_type="girl", mistress_name="Vela"),
]


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for t in asp_valid_combos():
            print(" ", t)
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
            header = f"### {p.hero_name}: {p.event} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
