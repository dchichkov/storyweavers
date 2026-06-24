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
    location: str = ""
    loose: bool = False
    protective: bool = False
    secures: set[str] = field(default_factory=set)
    plural: bool = False
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "librarian", "aunt"}
        male = {"boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "librarian": "librarian", "mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    floor: str = "floor"


@dataclass
class CaseFile:
    id: str
    label: str
    phrase: str
    material: str
    system_name: str
    mystery_item: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Organizer:
    id: str
    label: str
    phrase: str
    secures: set[str]
    setup: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        w.trace = list(self.trace)
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    clues = world.get("clues")
    helper = world.get("helper")

    if hero.meters["air_swish"] >= THRESHOLD and clues.meters["secured"] < THRESHOLD:
        sig = ("scatter", clues.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clues.meters["scattered"] += 1
            clues.meters["order"] = 0
            hero.memes["alarm"] += 1
            helper.memes["worry"] += 1
            helper.meters["workload"] += 1
            world.trace.append("twirl_scattered_loose_clues")
            out.append(
                f"The moving air brushed the {clues.label}, and part of the clue system slipped out of order."
            )

    if clues.meters["scattered"] >= THRESHOLD:
        sig = ("harder", clues.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["frustration"] += 1
            world.trace.append("case_became_harder")
            out.append("That made the mystery harder to solve because one clue slid away from the others.")

    if clues.meters["secured"] >= THRESHOLD:
        sig = ("steady", clues.id)
        if sig not in world.fired:
            world.fired.add(sig)
            clues.meters["order"] += 1
            hero.memes["relief"] += 1
            helper.memes["calm"] += 1
            world.trace.append("clue_system_secured")
            out.append("Now the clue system stayed neat and steady.")

    if narrate:
        for s in out:
            world.say(s)
    return out


def organizer_fits(casefile: CaseFile, organizer: Organizer) -> bool:
    return casefile.material in organizer.secures


def predict_scatter(world: World) -> bool:
    sim = world.copy()
    hero = sim.get("hero")
    clues = sim.get("clues")
    hero.meters["air_swish"] += 1
    propagate(sim, narrate=False)
    return clues.meters["scattered"] >= THRESHOLD


def introduce(world: World, hero: Entity, casefile: CaseFile) -> None:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved pretending to be a detective."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a simple clue system for the {casefile.label}: rows of clues, one small pencil, and a thinking spot."
    )


def loves_case(world: World, hero: Entity, casefile: CaseFile) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"The case was about {casefile.mystery_item}, and it felt extra important because it was {hero.pronoun('possessive')} fave mystery of the week."
    )


def set_scene(world: World, hero: Entity, helper: Entity, casefile: CaseFile) -> None:
    world.say(
        f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {helper.label_word} worked in {world.setting.place}."
    )
    world.say(
        f"On the table lay {casefile.phrase}, arranged in {casefile.system_name} so every clue had a place."
    )


def spot_big_clue(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["excitement"] += 1
    world.say(
        f"Then {hero.id} noticed a strong clue and wanted to {activity.verb} right beside the table."
    )


def warn(world: World, hero: Entity, helper: Entity, activity: Activity, casefile: CaseFile) -> bool:
    if not predict_scatter(world):
        return False
    helper.memes["care"] += 1
    world.facts["predicted_danger"] = activity.danger
    world.say(
        f'"Wait," said the {helper.label_word}. "If you {activity.verb} now, {activity.danger}, and the whole system may get mixed up."'
    )
    return True


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was so excited that {hero.pronoun()} started to {activity.rush}."
    )


def do_twirl(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["air_swish"] += 1
    hero.memes["joy"] += 1
    world.trace.append("hero_twirled_near_table")
    world.say(
        f"{hero.pronoun().capitalize()} gave one quick twirl anyway."
    )
    propagate(world, narrate=True)


def react(world: World, hero: Entity, helper: Entity) -> None:
    clues = world.get("clues")
    if clues.meters["scattered"] >= THRESHOLD:
        world.say(
            f"{hero.id} froze. One clue card had slipped toward the {world.setting.floor}, and the {helper.label_word} had to catch another before it fluttered away."
        )


def rebuild_with_organizer(world: World, hero: Entity, helper: Entity, organizer: Organizer) -> None:
    tool = world.add(Entity(
        id="organizer",
        type="organizer",
        label=organizer.label,
        phrase=organizer.phrase,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        secures=set(organizer.secures),
    ))
    clues = world.get("clues")
    clues.meters["secured"] = 1
    clues.loose = False
    world.say(
        f'"A good detective uses a good system," said the {helper.label_word}. "Let us {organizer.setup}."'
    )
    propagate(world, narrate=True)
    world.say(
        f"Together they put the clues back in place with {organizer.phrase}."
    )


def safer_turn(world: World, hero: Entity, activity: Activity, organizer: Organizer, casefile: CaseFile) -> None:
    hero.memes["learning"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"After that, {hero.id} stepped away from the table and made a much smaller twirl in an open spot."
    )
    world.say(
        f"This time the clues stayed safe in {organizer.label}, and {hero.pronoun()} could think clearly again."
    )
    world.say(
        f"Soon {hero.pronoun()} solved the case of {casefile.mystery_item}. At the end, the neat clue system sat still on the table, and {hero.id} smiled at it before making one last careful detective bow."
    )


def tell(setting: Setting, activity: Activity, casefile: CaseFile, organizer: Organizer,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=["little", trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
    ))
    clues = world.add(Entity(
        id="clues",
        type="clues",
        label=casefile.label,
        phrase=casefile.phrase,
        location="table",
        loose=True,
    ))

    introduce(world, hero, casefile)
    loves_case(world, hero, casefile)

    world.para()
    set_scene(world, hero, helper, casefile)
    spot_big_clue(world, hero, activity)
    warn(world, hero, helper, activity, casefile)
    defy(world, hero, activity)
    do_twirl(world, hero, activity)
    react(world, hero, helper)

    world.para()
    rebuild_with_organizer(world, hero, helper, organizer)
    safer_turn(world, hero, activity, organizer, casefile)

    world.facts.update(
        hero=hero,
        helper=helper,
        casefile=casefile,
        organizer=organizer,
        activity=activity,
        setting=setting,
        learned=True,
        danger=world.facts.get("predicted_danger", activity.danger),
    )
    return world


SETTINGS = {
    "library": Setting(place="the library corner", affords={"cards", "notes"}, floor="rug"),
    "classroom": Setting(place="the classroom reading table", affords={"cards", "photos"}, floor="floor"),
    "hall": Setting(place="the quiet hall table", affords={"notes", "photos"}, floor="bench"),
}

CASEFILES = {
    "cards": CaseFile(
        id="cards",
        label="clue cards",
        phrase="a line of clue cards",
        material="paper",
        system_name="a little sorting system",
        mystery_item="the missing gold star sticker",
        tags={"paper", "system", "detective"},
    ),
    "notes": CaseFile(
        id="notes",
        label="sticky notes",
        phrase="several sticky notes with careful marks",
        material="sticky",
        system_name="a note-by-note clue system",
        mystery_item="the lost blue crayon",
        tags={"sticky", "system", "detective"},
    ),
    "photos": CaseFile(
        id="photos",
        label="picture clues",
        phrase="small picture clues in a row",
        material="photo",
        system_name="a picture clue system",
        mystery_item="the wandering toy train ticket",
        tags={"photo", "system", "detective"},
    ),
}

ORGANIZERS = {
    "folder": Organizer(
        id="folder",
        label="a case folder",
        phrase="a case folder with clear pockets",
        secures={"paper", "photo"},
        setup="slide the clues into the case folder first",
        ending="rested safely in the case folder",
        tags={"folder"},
    ),
    "board": Organizer(
        id="board",
        label="a clip board",
        phrase="a clip board with a strong silver clip",
        secures={"paper", "sticky"},
        setup="clip the clues onto the board first",
        ending="stayed clipped to the board",
        tags={"board"},
    ),
    "tray": Organizer(
        id="tray",
        label="a sorting tray",
        phrase="a shallow sorting tray with little walls",
        secures={"sticky", "photo"},
        setup="set the clues into the sorting tray first",
        ending="sat safely in the sorting tray",
        tags={"tray"},
    ),
}

ACTIVITIES = {
    "twirl": Activity(
        id="twirl",
        verb="do a happy twirl",
        gerund="doing a happy twirl",
        rush="lift a foot for a fast twirl",
        danger="the clues could flutter and scatter",
        keyword="twirl",
        tags={"twirl", "detective", "cautionary"},
    )
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "June"]
BOY_NAMES = ["Owen", "Max", "Eli", "Theo", "Ben", "Milo"]
TRAITS = ["careful", "bright", "eager", "curious", "quick-thinking", "proud"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for case_id in setting.affords:
            casefile = CASEFILES[case_id]
            for org_id, organizer in ORGANIZERS.items():
                if organizer_fits(casefile, organizer):
                    out.append((place, case_id, org_id))
    return sorted(out)


@dataclass
class StoryParams:
    place: str
    casefile: str
    organizer: str
    activity: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "twirl": [
        ("What is a twirl?", "A twirl is a quick turn around in a circle with your body."),
        ("Why can a twirl near papers cause trouble?", "A fast twirl can move air and bump the table, so loose papers may slide or flutter away."),
    ],
    "system": [
        ("What is a system?", "A system is a way of keeping things in order so each part has its place and job."),
    ],
    "detective": [
        ("What does a detective do?", "A detective looks for clues, notices details, and uses them to solve a mystery."),
    ],
    "folder": [
        ("What does a folder do?", "A folder keeps papers together so they do not get lost or bent."),
    ],
    "board": [
        ("What is a clip board for?", "A clip board holds papers under a clip so they stay in one place while you work."),
    ],
    "tray": [
        ("Why can a tray help with sorting?", "A tray has edges that help small things stay where you put them."),
    ],
}
KNOWLEDGE_ORDER = ["detective", "system", "twirl", "folder", "board", "tray"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    casefile = f["casefile"]
    helper = f["helper"]
    organizer = f["organizer"]
    return [
        f'Write a short cautionary detective story for ages 3 to 5 that includes the words "system", "fave", and "twirl".',
        f"Tell a gentle detective story about a child whose fave mystery uses {casefile.label}, but a twirl almost ruins the clue system until a {organizer.label} helps.",
        f"Write a simple mystery story set in {world.setting.place} where {hero.label} learns to celebrate carefully after listening to the {helper.label_word}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    casefile = f["casefile"]
    organizer = f["organizer"]
    activity = f["activity"]
    place = world.setting.place
    name = hero.label
    pos = hero.pronoun("possessive")
    obj = hero.pronoun("object")
    sub = hero.pronoun("subject")
    trait = next((t for t in hero.traits if t != "little"), "careful")

    return [
        QAItem(
            question=f"Who is the detective in the story, and what case was {obj} trying to solve in {place}?",
            answer=f"The detective is a little {trait} child named {name}. In {place}, {sub} was trying to solve the case of {casefile.mystery_item}.",
        ),
        QAItem(
            question=f"Why did the {helper.label_word} warn {name} before the happy twirl?",
            answer=f"The {helper.label_word} warned {name} because the clue system was still loose on the table. A fast twirl could make the {casefile.label} scatter and mix up the mystery.",
        ),
        QAItem(
            question=f"What went wrong when {name} twirled anyway?",
            answer=f"When {name} gave one quick twirl anyway, moving air brushed the {casefile.label}. One clue slipped out of order, so the case became harder to solve.",
        ),
        QAItem(
            question=f"How did {organizer.label} help fix the problem?",
            answer=f"They rebuilt the clue system by putting the clues into {organizer.phrase}. That kept the clues steady, so {name} could think clearly and solve the mystery.",
        ),
        QAItem(
            question=f"What did {name} learn at the end of the story?",
            answer=f"{name} learned that even a detective's happy move should wait until the clues are safe. After the system was secure, {sub} could celebrate carefully without making a mess of the case.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"system", "detective", "twirl"}
    tags.update(world.facts["organizer"].tags)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        extras = []
        if e.loose:
            extras.append("loose=True")
        if e.protective:
            extras.append(f"secures={sorted(e.secures)}")
        if meters:
            extras.append(f"meters={dict(meters)}")
        if memes:
            extras.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(extras)}")
    lines.append(f"  events={world.trace}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", casefile="cards", organizer="folder", activity="twirl", name="Mina", gender="girl", helper="librarian", trait="curious"),
    StoryParams(place="classroom", casefile="photos", organizer="tray", activity="twirl", name="Owen", gender="boy", helper="teacher", trait="eager"),
    StoryParams(place="hall", casefile="notes", organizer="board", activity="twirl", name="Lila", gender="girl", helper="teacher", trait="bright"),
]


def explain_rejection(casefile: CaseFile, organizer: Organizer) -> str:
    return (
        f"(No story: {organizer.label.capitalize()} does not really secure {casefile.label}. "
        f"The detective fix must honestly protect the clue system before the celebration.)"
    )


ASP_RULES = r"""
fits(Case, Org) :- material_of(Case, Mat), secures(Org, Mat).
valid(Place, Case, Org) :- affords(Place, Case), fits(Case, Org).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for case_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, case_id))
    for case_id, casefile in CASEFILES.items():
        lines.append(asp.fact("casefile", case_id))
        lines.append(asp.fact("material_of", case_id, casefile.material))
    for org_id, organizer in ORGANIZERS.items():
        lines.append(asp.fact("organizer", org_id))
        for material in sorted(organizer.secures):
            lines.append(asp.fact("secures", org_id, material))
    return "\n".join(lines)


def asp_program(extra_show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra_show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ap = set(asp_valid_combos())
    if py == ap:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        for params in CURATED:
            sample = generate(params)
            if not sample.story.strip():
                print("Verification failed: empty story in curated sample.")
                return 1
        print("OK: curated stories generated.")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if ap - py:
        print("  only in clingo:", sorted(ap - py))
    if py - ap:
        print("  only in python:", sorted(py - ap))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary detective storyworld about a clue system, a fave case, and one risky twirl.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--casefile", choices=CASEFILES)
    ap.add_argument("--organizer", choices=ORGANIZERS)
    ap.add_argument("--activity", choices=ACTIVITIES, default=None)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["teacher", "librarian", "mother", "father"])
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
    if args.casefile and args.organizer:
        casefile = CASEFILES[args.casefile]
        organizer = ORGANIZERS[args.organizer]
        if not organizer_fits(casefile, organizer):
            raise StoryError(explain_rejection(casefile, organizer))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.casefile is None or c[1] == args.casefile)
        and (args.organizer is None or c[2] == args.organizer)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, case_id, org_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["teacher", "librarian"])
    trait = rng.choice(TRAITS)
    activity = args.activity or "twirl"
    return StoryParams(
        place=place,
        casefile=case_id,
        organizer=org_id,
        activity=activity,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    hero_type = "girl" if params.gender == "girl" else "boy"
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        CASEFILES[params.casefile],
        ORGANIZERS[params.organizer],
        hero_name=params.name,
        hero_type=hero_type,
        helper_type=params.helper,
        trait=params.trait,
    )
    world.get("hero").label = params.name
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.name),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, casefile, organizer) combos:\n")
        for place, case_id, org_id in combos:
            print(f"  {place:10} {case_id:8} {org_id:8}")
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
            header = f"### {p.name}: {p.casefile} in {p.place} with {p.organizer}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
