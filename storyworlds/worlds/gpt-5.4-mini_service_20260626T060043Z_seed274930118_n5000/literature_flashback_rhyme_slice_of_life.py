#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/literature_flashback_rhyme_slice_of_life.py
==========================================================================================

A small slice-of-life story world about literature, flashbacks, and rhyme.

Premise:
- A child loves a special storybook and wants to read aloud in a cozy place.
- A parent remembers a past spill that bent the pages, so they worry.
- The child and parent pause, recall that earlier moment, and choose a safer reading setup.
- The ending proves the change: the book stays clean, the poem gets read, and the room feels calm.

The world is intentionally small and constraint-driven:
- physical state tracks things like wetness and creases;
- emotional state tracks joy, worry, nostalgia, and closeness;
- a flashback can make a current worry feel grounded;
- rhyme appears as a gentle, child-facing turn of phrase in the story.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "creased", "dirty", "neat", "held", "used"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "love", "nostalgia", "calm", "closeness", "alarm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
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
    weather: str = ""
    keyword: str = ""
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "library": Setting(place="the library", indoor=True, affords={"read_aloud", "write_poem"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"read_aloud", "write_poem"}),
    "porch": Setting(place="the porch", indoor=False, affords={"read_aloud"}),
}

ACTIVITIES = {
    "read_aloud": Activity(
        id="read_aloud",
        verb="read the story aloud",
        gerund="reading aloud",
        rush="hurry outside with the book",
        mess="wet",
        soil="damp and wrinkled",
        zone={"hands", "pages"},
        weather="drizzly",
        keyword="rhyme",
        tags={"literature", "rhyme", "flashback"},
    ),
    "write_poem": Activity(
        id="write_poem",
        verb="write a little rhyme",
        gerund="writing tiny rhymes",
        rush="dash to the table with the notebook",
        mess="creased",
        soil="creased and smudged",
        zone={"hands", "paper"},
        weather="",
        keyword="literature",
        tags={"literature", "rhyme"},
    ),
}

PRIZES = {
    "storybook": Prize(
        label="storybook",
        phrase="a favorite storybook with gold stars on the cover",
        type="storybook",
        region="pages",
    ),
    "notebook": Prize(
        label="notebook",
        phrase="a fresh notebook for poems and little lists",
        type="notebook",
        region="paper",
    ),
}

GEAR = [
    Gear(
        id="book_cover",
        label="a cloth book cover",
        covers={"pages"},
        guards={"wet"},
        prep="wrap the storybook in a cloth cover first",
        tail="wrapped the storybook in the cloth cover",
    ),
    Gear(
        id="tray",
        label="a little tray",
        covers={"paper", "pages"},
        guards={"wet", "creased"},
        prep="set up a little tray and keep the cup far away",
        tail="set up the little tray and kept the cup far away",
    ),
    Gear(
        id="blanket",
        label="a dry blanket",
        covers={"pages", "paper"},
        guards={"wet"},
        prep="spread a dry blanket on the chair",
        tail="spread the dry blanket on the chair",
    ),
]

GIRL_NAMES = ["Maya", "Nina", "Lina", "Ivy", "Rose", "Mila"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Finn", "Leo", "Sam"]
TRAITS = ["quiet", "curious", "gentle", "cheerful", "dreamy", "patient"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    if narrate:
        propagate(world)


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD and actor.meters["creased"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            if ("soak", item.id, actor.meters["wet"], actor.meters["creased"]) in world.fired:
                continue
            world.fired.add(("soak", item.id, actor.meters["wet"], actor.meters["creased"]))
            if actor.meters["wet"] >= THRESHOLD:
                item.meters["wet"] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got damp.")
            if actor.meters["creased"] >= THRESHOLD:
                item.meters["creased"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} picked up a crease.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for item in world.entities.values():
        if item.meters["wet"] < THRESHOLD and item.meters["creased"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        carer.memes["alarm"] += 1
        out.append(f"That made {carer.label} worry.")
    return out


CAUSAL_RULES = [
    ("soak", _r_soak),
    ("worry", _r_worry),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
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
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["wet"] >= THRESHOLD or prize.meters["creased"] >= THRESHOLD}


def choose_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    return select_gear(activity, prize)


def flashback_line(hero: Entity, parent: Entity, prize: Entity) -> str:
    return (
        f"Yesterday, {hero.id} had knocked a spoonful of tea near {hero.pronoun('possessive')} "
        f"{prize.label}, and {parent.label_word} had spent the whole evening drying the pages."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather if not setting.indoor else ""
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["gentle"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    hero.memes["love"] += 1
    world.say(f"{hero.id} was a little {hero.traits[-1]} {hero.type} who loved books and rhymes.")
    world.say(f"{hero.id} kept {hero.pronoun('possessive')} {prize.label} close, because its pages felt like a tiny treasure.")
    world.say(f"{hero.pronoun().capitalize()} liked to whisper, 'Page by page and rhyme by rhyme, stories shine in little time.'")

    world.para()
    world.say(f"One {activity.weather or 'ordinary'} afternoon, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {setting.place}.")
    world.say(f"{hero.id} wanted to {activity.verb}, and the words felt warm in {hero.pronoun('possessive')} mouth.")

    if not setting.indoor:
        world.say("The air smelled fresh, but the sky looked ready to drop a few drops.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f"{parent.label_word.capitalize()} remembered the earlier spill.")
        world.say(flashback_line(hero, parent, prize))
        world.say(f"So {parent.label_word} said, \"Let's be careful with {prize.label}.\"")
        hero.memes["nostalgia"] += 1
        hero.memes["worry"] += 0.5

    hero.meters[activity.mess] += 1
    if activity.id == "write_poem":
        hero.meters["creased"] += 1
    propagate(world)

    world.say(f"{hero.id} tried to {activity.rush}, but {parent.label_word} lifted a hand and slowed the moment down.")
    gear = choose_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable protective gear exists for this story.")

    # Use the gear and verify it actually helps.
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        item = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, caretaker=parent.id,
                                protective=True, covers=set(gear.covers), plural=gear.plural))
        item.worn_by = hero.id
        world.say(f"{parent.label_word.capitalize()} offered {gear.label} and smiled.")
        world.say(f'"How about we {gear.prep} and then {activity.verb} together?"')
        hero.memes["calm"] += 1
        hero.memes["closeness"] += 1
        hero.memes["worry"] = 0.0
        hero.memes["joy"] += 1
        world.say(f"{hero.id} nodded, and soon they {gear.tail}.")
    else:
        raise StoryError("Unexpectedly, the activity would not have harmed the prize.")

    # Finish the action after the compromise.
    world.para()
    world.say(f"{hero.id} settled in and {activity.gerund} while the protected {prize.label} stayed neat.")
    if activity.id == "read_aloud":
        world.say(f"{hero.id} read a soft little rhyme, and the last line bounced like a pebble in a pond.")
    else:
        world.say(f"{hero.id} wrote a rhyme about raindrops, book spines, and the warm comfort of home.")
    world.say(f"In the end, {prize.label} was still clean, and {parent.label_word} sat close enough to hear every sweet line.")

    world.facts.update(
        hero=hero, parent=parent, prize=prize, activity=activity, setting=setting,
        gear=gear, conflict=True, resolved=True, flashback=True
    )
    return world


KNOWLEDGE = {
    "literature": [
        ("What is literature?",
         "Literature is writing like stories, poems, and books that people read for fun, learning, or feeling."ിന"),
    ],
    "rhyme": [
        ("What is a rhyme?",
         "A rhyme is a sound pattern where words end in a similar way, like cat and hat."),
    ],
    "flashback": [
        ("What is a flashback in a story?",
         "A flashback is a quick look back at something that happened earlier, so the reader understands why a character feels a certain way."),
    ],
    "wet": [
        ("Why can wet paper get damaged?",
         "Wet paper can wrinkle and tear more easily because the fibers soften when they soak up water."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short slice-of-life story about literature that includes a flashback and a rhyme.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} with {hero.pronoun('possessive')} {prize.label}, but {parent.label_word} remembers an earlier spill.",
        f'Write a calm child-friendly story set at {world.setting.place} where a rhyme helps a child and parent choose a safer way to read.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} with {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} pause when {hero.id} reached for the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} remembered an earlier spill that had left the {prize.label} damp and wrinkled, so {parent.label_word} wanted to keep it safe.",
        ),
        QAItem(
            question="What helped turn the problem into a calm plan?",
            answer=f"They used {f['gear'].label} and then sat together so {hero.id} could keep reading without harming the {prize.label}.",
        ),
        QAItem(
            question="What kind of little line did the child say?",
            answer="The child said a tiny rhyme about pages and time, which made the story feel warm and playful.",
        ),
    ]
    if f.get("flashback"):
        qa.append(QAItem(
            question=f"What earlier moment did the story remember?",
            answer=f"It remembered the time a spoonful of tea had nearly splashed the {prize.label}, which is why {parent.label_word} was careful now.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags)
    tags.add("wet")
    if world.facts.get("flashback"):
        tags.add("flashback")
    for tag in ["literature", "rhyme", "flashback", "wet"]:
        if tag in tags and tag in KNOWLEDGE:
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life literature storyworld with flashback and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
            raise StoryError("That activity and prize do not make a reasonable story.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if args.gender:
        combos = [c for c in combos if args.gender in PRIZES[c[2]].genders]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait], params.parent)
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
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="library", activity="read_aloud", prize="storybook", name="Maya", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="sunroom", activity="write_poem", prize="notebook", name="Eli", gender="boy", parent="father", trait="gentle"),
    StoryParams(place="porch", activity="read_aloud", prize="storybook", name="Rose", gender="girl", parent="mother", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, act, prize in combos:
            print(f"  {place:8} {act:11} {prize}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
