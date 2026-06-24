#!/usr/bin/env python3
"""
Space-adventure storyworld with a revolving station, a captioning task, and a
small rescue ship called Republican.

The seed tale behind this world is simple:
- A child loves watching a ring-world revolve around a planet.
- The child wants to write a caption for a photo of that view.
- A careful captain worries the drifting shuttle Republican may miss a docking
  light.
- Kindness turns the suspense into a safe, bright ending.

This script keeps the world tiny and classical: one short simulation, one turn,
one resolution, and question sets grounded in the simulated state.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"glow": 0.0, "drift": 0.0, "noise": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "kindness": 0.0, "suspense": 0.0, "worry": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "captain", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the orbit ring"
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["drift"] < THRESHOLD:
            continue
        for ship in world.entities.values():
            if ship.type != "ship" or ship.owner != actor.id:
                continue
            sig = ("drift", ship.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ship.meters["drift"] += 1
            out.append(f"{ship.label} rocked a little farther off course.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["kindness"] < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} felt braver after choosing a kind thing to do.")
    return out


CAUSAL_RULES = [
    _r_drift,
    _r_kindness,
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


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters["noise"] >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        raise StoryError("The setting cannot support that activity.")
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["suspense"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved bright space days.")


def loves_space(world: World, hero: Entity) -> None:
    hero.memes["joy"] += 1
    world.say("The orbit ring went round and round the planet, and the spinning view made every window glow.")


def show_caption(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} as if it were the most important little card in space.")


def arrive(world: World, hero: Entity, captain: Entity, ship: Entity) -> None:
    world.say(f"One night, {hero.id} and {hero.pronoun('possessive')} {captain.label_word} stood near {ship.label} at the docking bay.")
    world.say("Outside the glass, the station kept revolving in a silver circle.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["kindness"] += 0.5
    world.say(f"{hero.id} wanted to {activity.verb} and make the picture feel friendly for everyone who saw it.")


def warn(world: World, captain: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    captain.memes["worry"] += 1
    world.say(f'"If you rush now, the {prize.label} could get lost in the noise," {captain.id} said.')
    return True


def suspense(world: World, hero: Entity, ship: Entity) -> None:
    hero.memes["suspense"] += 1
    ship.meters["drift"] += 1
    world.say(f"The little ship {ship.label} gave a tiny wobble, and {hero.id} held {hero.pronoun('possessive')} breath.")


def kindness_fix(world: World, hero: Entity, captain: Entity, prize: Entity, ship: Entity) -> None:
    hero.memes["kindness"] += 1
    hero.memes["joy"] += 1
    ship.meters["drift"] = 0
    world.say(f"{hero.id} took a slow breath, steadied {ship.label}, and gave {captain.pronoun('object')} the spare light.")
    world.say(f'"Let me help," {hero.id} said. "We can keep the caption and keep {ship.label} safe too."')


def resolve(world: World, hero: Entity, captain: Entity, activity: Activity, prize: Entity, ship: Entity) -> None:
    world.say(f"Together, they watched the station revolve past the dark stars while the caption shone on the screen.")
    world.say(f"In the end, {hero.id}'s {prize.label} stayed clean, {ship.label} stayed steady, and the night felt kind instead of scary.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         captain_type: str = "captain") -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little"] + (hero_traits or ["curious", "brave"])))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="captain"))
    ship = world.add(Entity(id="Republican", kind="ship", label="Republican", type="ship", owner=hero.id))
    prize = world.add(Entity(id="caption", type=prize_cfg.type, label=prize_cfg.label,
                             phrase=prize_cfg.phrase, owner=hero.id, caretaker=captain.id,
                             region=prize_cfg.region, plural=prize_cfg.plural))

    introduce(world, hero)
    loves_space(world, hero)
    show_caption(world, hero, prize)

    world.para()
    arrive(world, hero, captain, ship)
    wants(world, hero, activity)
    warn(world, captain, hero, activity, prize)
    suspense(world, hero, ship)

    world.para()
    kindness_fix(world, hero, captain, prize, ship)
    resolve(world, hero, captain, activity, prize, ship)

    world.facts.update(hero=hero, captain=captain, ship=ship, prize=prize, activity=activity, setting=setting)
    return world


SETTINGS = {
    "orbit_ring": Setting(place="the orbit ring", affords={"revolve"}),
    "docking_bay": Setting(place="the docking bay", affords={"revolve"}),
    "window_hall": Setting(place="the window hall", affords={"revolve"}),
}

ACTIVITIES = {
    "revolve": Activity(
        id="revolve",
        verb="watch the station revolve",
        gerund="watching the station revolve",
        rush="run to the window and shout",
        mess="drift",
        soil="lost in the drift",
        zone={"view"},
        keyword="revolve",
        tags={"revolve", "space"},
    ),
}

PRIZES = {
    "caption": Prize(
        label="caption card",
        phrase="a tiny caption card",
        type="card",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="handlight",
        label="a handlight",
        covers={"hands"},
        guards={"drift"},
        prep="use a handlight first",
        tail="used the handlight and kept the card steady",
    )
]

GIRL_NAMES = ["Mira", "Luna", "Nova", "Ivy", "Zara"]
BOY_NAMES = ["Toby", "Ari", "Jett", "Milo", "Rian"]
TRAITS = ["curious", "brave", "kind", "patient", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "revolve": [
        ("What does it mean for something to revolve?", "When something revolves, it moves around and around in a circle."),
    ],
    "space": [
        ("What is a space station?", "A space station is a home and workplace in space where astronauts can live and do science."),
    ],
    "kindness": [
        ("What is kindness?", "Kindness means doing something gentle, helpful, or caring for someone else."),
    ],
    "suspense": [
        ("What is suspense in a story?", "Suspense is the feeling of waiting to see what will happen next."),
    ],
    "caption": [
        ("What is a caption?", "A caption is a short line of words that explains a picture."),
    ],
    "drift": [
        ("What does drift mean in space?", "To drift means to move slowly without a strong push or clear direction."),
    ],
    "republican": [
        ("What is the Republican in this story?", "Republican is the name of a small ship in this storyworld."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, captain, activity, prize = f["hero"], f["captain"], f["activity"], f["prize"]
    return [
        'Write a short space adventure for a child that includes the word "revolve" and a happy rescue.',
        f"Tell a gentle story where {hero.id} wants to {activity.verb} but {captain.label_word} worries about {prize.label}, and the ship Republican stays safe.",
        f'Write a simple story about a rotating space station, a caption card, and kindness in the middle of suspense.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, activity = f["hero"], f["captain"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, and {captain.label_word}, who watches over the dock.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {activity.verb}, because the revolving station looked exciting and bright.",
        ),
        QAItem(
            question=f"What did the caption card help with?",
            answer=f"The caption card helped make the space picture clear and friendly, so the story could remember the happy moment.",
        ),
        QAItem(
            question=f"Why was there suspense near Republican?",
            answer=f"There was suspense because Republican gave a tiny wobble, and everyone had to wait to see whether the plan would stay safe.",
        ),
        QAItem(
            question=f"How did kindness change the ending?",
            answer=f"Kindness helped {hero.id} slow down, steady Republican, and keep the caption card safe, so the ending felt calm and warm.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("caption")
    tags.add("kindness")
    tags.add("suspense")
    tags.add("republican")
    out: list[QAItem] = []
    for tag in ["revolve", "space", "kindness", "suspense", "caption", "drift", "republican"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbit_ring", activity="revolve", prize="caption", name="Mira", gender="girl", parent="captain", trait="kind"),
]


def explain_rejection() -> str:
    return "(No story: this world only supports the revolve-and-caption space adventure.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with revolve, caption, and republican.")
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
    if args.activity and args.activity != "revolve":
        raise StoryError(explain_rejection())
    if args.prize and args.prize != "caption":
        raise StoryError(explain_rejection())
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "revolve"
    prize = args.prize or "caption"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
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
place(orbit_ring).
place(docking_bay).
place(window_hall).

activity(revolve).
prize(caption).
gender(girl).
gender(boy).

affords(orbit_ring,revolve).
affords(docking_bay,revolve).
affords(window_hall,revolve).

worn_on(caption,hands).
splashes(revolve,view).
mess_of(revolve,drift).

gear(handlight).
guards(handlight,drift).
covers(handlight,hands).

prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), gender(G).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in SETTINGS[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in a.zone:
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
        for r in g.covers:
            lines.append(asp.fact("covers", g.id, r))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, "revolve", "caption") for p in SETTINGS}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches python ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  python:", sorted(python_set))
    print("  clingo:", sorted(clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:10} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
