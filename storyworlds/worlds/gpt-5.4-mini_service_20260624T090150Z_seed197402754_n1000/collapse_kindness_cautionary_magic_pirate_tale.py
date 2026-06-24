#!/usr/bin/env python3
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
    carried_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "pirate_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "pirate_boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


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
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return sorted(out)


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("collapse", 0.0) < THRESHOLD:
            continue
        for item in world.carried_items(actor) + world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("collapse", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] = item.meters.get("damage", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} got shaken by the collapse.")
    return out


def _r_caution(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("caution", 0.0) >= THRESHOLD and actor.memes.get("fear", 0.0) < THRESHOLD:
            sig = ("calm", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["steady"] = actor.memes.get("steady", 0.0) + 1
            out.append(f"{actor.id} stayed steady and looked for a safer path.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trust"] = actor.memes.get("trust", 0.0) + 1
        out.append(f"That kind choice made the sea creatures trust {actor.id}.")
    return out


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("magic", 0.0) < THRESHOLD:
            continue
        sig = ("magic", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["glow"] = actor.meters.get("glow", 0.0) + 1
        out.append(f"A little magic glow showed a safer way forward.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_collapse, _r_caution, _r_kindness, _r_magic):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_collapse(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy as _copy
    sim.entities = _copy.deepcopy(world.entities)
    sim.zone = set(activity.zone)
    sim.get(actor.id).meters["collapse"] = 1.0
    propagate(sim, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"damaged": bool(prize and prize.meters.get("damage", 0.0) >= THRESHOLD)}


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little pirate who loved tide pools, shiny things, and good surprises.")


def setting_line(world: World, activity: Activity) -> None:
    world.say(f"At {world.setting.place}, the wind hummed and the dark cave mouth waited by the water.")
    world.say(f"{activity.keyword.capitalize()} was the kind of adventure that made pirates grin and gulp at once.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_collapse(world, hero, activity, prize.id)
    if not pred["damaged"]:
        return False
    world.facts["predicted_damage"] = True
    world.say(f'"If the cave starts to collapse, your {prize.label} could get hurt," {parent.id} said.')
    world.say(f'"We should be careful first."')
    return True


def do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["collapse"] = hero.meters.get("collapse", 0.0) + 1
    propagate(world, narrate=True)


def resolve_kindness(world: World, hero: Entity, creature: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.say(f"{hero.id} paused to help the little {creature.label} back to the shore.")


def offer_magic(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["magic"] = hero.memes.get("magic", 0.0) + 1
    world.say(f"The glowing {prize.label} shimmered like a moonbeam in a bottle.")


def choose_safe_path(world: World, hero: Entity, activity: Activity, gear_def: Gear, prize: Entity) -> None:
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    world.say(f"{hero.id}'s captain nodded and said, \"Let's use the {gear_def.label} and take the safe path.\"")
    world.say(f"They {gear_def.tail}, and the cave's loud rumble stayed behind them.")


def accept_end(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} smiled, and the sea wind felt friendly again.")
    world.say(f"In the end, {hero.id} was {activity.gerund}, {prize.label} safe and bright, while the old cave collapsed far away.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira", hero_type: str = "girl", parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural, carried_by=hero.id))
    creature = world.add(Entity(id="Crab", kind="character", type="crab", label="crab"))

    intro(world, hero)
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} everywhere, because it was a magic gift from the last moon tide.")
    setting_line(world, activity)

    world.para()
    world.say(f"{hero.id} wanted to {activity.verb}, but {parent.id} lifted a hand.")
    warn(world, parent, hero, activity, prize)
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"{hero.id} heard the warning, but the cave looked exciting anyway.")
    world.say(f"{hero.id} tried to {activity.rush}, and the rocks began to shake.")

    world.para()
    do_activity(world, hero, activity)
    if hero.meters.get("collapse", 0.0) >= THRESHOLD:
        world.say(f"Then a small collapse shook dust from the ceiling.")

    resolve_kindness(world, hero, creature)
    offer_magic(world, hero, prize)
    gear_def = select_gear(activity, prize)
    if gear_def:
        gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id, protective=True, covers=set(gear_def.covers), plural=gear_def.plural))
        gear.worn_by = hero.id
        choose_safe_path(world, hero, activity, gear_def, prize)

    world.para()
    hero.memes["caution"] = hero.memes.get("caution", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["magic"] = hero.memes.get("magic", 0.0) + 1
    accept_end(world, hero, parent, activity, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, creature=creature, activity=activity, gear=gear_def, setting=setting, resolved=True)
    return world


SETTINGS = {
    "cove": Setting(place="the moonlit cove", affords={"cave"}),
    "harbor": Setting(place="the windy harbor", affords={"harbor"}),
    "reef": Setting(place="the bright reef", affords={"reef"}),
}

ACTIVITIES = {
    "cave": Activity(
        id="cave",
        verb="explore the cave",
        gerund="exploring the cave",
        rush="dash into the cave",
        mess="collapse",
        soil="battered by a collapse",
        zone={"hands", "torso"},
        keyword="collapse",
        tags={"collapse", "cautionary"},
    ),
    "reef": Activity(
        id="reef",
        verb="cross the reef",
        gerund="sailing by the reef",
        rush="race toward the reef",
        mess="wet",
        soil="soaked by spray",
        zone={"hands"},
        keyword="magic",
        tags={"magic"},
    ),
    "harbor": Activity(
        id="harbor",
        verb="haul the rope",
        gerund="hauling the rope",
        rush="yank the rope",
        mess="rough",
        soil="frayed by rough work",
        zone={"hands"},
        keyword="kindness",
        tags={"kindness"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a tiny magic lantern", type="lantern", region="hands"),
    "map": Prize(label="map", phrase="a folded star map", type="map", region="hands"),
    "shell": Prize(label="shell", phrase="a pearly shell charm", type="shell", region="torso"),
}

GEAR = [
    Gear(id="gloves", label="soft captain's gloves", covers={"hands"}, guards={"collapse", "wet", "rough"}, prep="put on the soft captain's gloves first", tail="slipped away with the gloves on"),
    Gear(id="cloak", label="an oilskin cloak", covers={"torso"}, guards={"collapse", "wet"}, prep="wrap up in an oilskin cloak", tail="moved on with the cloak fastened"),
]

GIRL_NAMES = ["Mira", "Nina", "Tala", "Ivy", "Luna", "Rosa"]
BOY_NAMES = ["Kai", "Jett", "Finn", "Tobias", "Niko", "Rowan"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "collapse": [("What is a collapse?", "A collapse is when something breaks down, falls, or comes apart suddenly.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, caring, and helpful to someone else.")],
    "magic": [("What is magic in a story?", "Magic is a special story surprise that can glow, change, or reveal things in a wonderful way.")],
    "cautionary": [("What does caution mean?", "Caution means being careful so you do not get hurt or make a bad choice.")],
    "pirate": [("What is a pirate tale?", "A pirate tale is a story about sailors who search for adventures on the sea.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short pirate tale for a young child about "{act.keyword}" and a careful choice.',
        f"Tell a story where {hero.id} wants to {act.verb} but {parent.id} worries about {prize.label} and a collapse.",
        f"Write a gentle pirate story that includes kindness, caution, and a little bit of magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        QAItem(question=f"What did {hero.id} want to do near the cave?", answer=f"{hero.id} wanted to {act.verb}, even though a collapse could make things dangerous."),
        QAItem(question=f"Why did {parent.id} warn {hero.id}?", answer=f"{parent.id} warned {hero.id} because the cave might collapse and hurt {prize.label}."),
        QAItem(question=f"How did the story end?", answer=f"It ended with {hero.id} choosing a safer way, showing kindness, and keeping {prize.label} safe."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag in ["collapse", "kindness", "cautionary", "magic", "pirate"]:
        if tag in tags or tag in {"kindness", "cautionary", "magic", "pirate"}:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE.get(tag, []))
    return out


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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cove", activity="cave", prize="lantern", name="Mira", gender="girl", parent="captain"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not threaten the {prize.label}, so there is no honest cautionary turn.)"
    return f"(No story: no gear in this world can reasonably protect the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), covers(G,R), zone(A,R), guards(G,M), mess_of(A,M).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with kindness, caution, and magic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(combos)
    p = PRIZES[prize]
    gender = args.gender or rng.choice(sorted(p.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent="captain")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
