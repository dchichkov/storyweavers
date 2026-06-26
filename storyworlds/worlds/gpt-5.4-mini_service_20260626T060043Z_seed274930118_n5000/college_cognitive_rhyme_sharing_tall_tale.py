#!/usr/bin/env python3
"""
A standalone storyworld for a tall-tale college rhyme-sharing domain.

Seed premise:
A clever college kid gets tangled in a campus rhyme-sharing contest that turns
cognitive pride into a lesson about listening, memory, and generous teamwork.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "professor"}
        male = {"boy", "man", "father", "professor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the college commons"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
        self.zone: set[str] = set()
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


THRESHOLD = 1.0
MESS_KINDS = {"rhyme-ink", "chalk-dust", "brain-buzz"}


def _r_spill_rhyme(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.worn_by != actor.id:
                    continue
                if item.region not in world.zone:
                    continue
                if item.id == "quill":  # a prop, not wearable
                    continue
                sig = ("mess", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["tarnished"] = item.meters.get("tarnished", 0.0) + 1
                out.append(f"{item.label.capitalize()} got a smear of {mess}.")
    return out


def _r_shared_good(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("sharing", 0.0) < THRESHOLD:
            continue
        sig = ("share", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["warmth"] = actor.memes.get("warmth", 0.0) + 1
        out.append(f"{actor.id} felt bigger-hearted after sharing the verse.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("jealousy", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    _r_spill_rhyme,
    _r_shared_good,
    _r_conflict,
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonability_gate(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def compatible_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None


def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"tarnished": prize.meters.get("tarnished", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def tell(sett: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str) -> World:
    world = World(sett)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the dean"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        plural=prize_cfg.plural,
    ))

    hero.memes["love_rhyme"] = 1
    world.say(f"{hero.id} was a bright college kid who could rhyme with the wind and the windows.")
    world.say(f"{hero.pronoun().capitalize()} loved cognitive games, quick verses, and sharing a tune with friends.")
    world.say(f"{parent.label.capitalize()} had given {hero.pronoun('object')} {prize.phrase}, and {hero.id} wore {prize.it()} like a little banner.")

    world.para()
    world.say(f"One afternoon at {world.setting.place}, the campus crowd gathered for a rhyme-sharing contest.")
    world.say(f"{hero.id} wanted to {activity.verb}, but the contest was known for flying {activity.keyword}.")
    risk = predict_risk(world, hero, activity, prize.id)
    if risk["tarnished"]:
        world.say(f'"If you go bounding in, your {prize.label} will get smudged," the dean warned.')
    hero.memes["jealousy"] = 1
    world.say(f"{hero.id} tried to {activity.rush}, pretending the warning was smaller than a flea on a parade drum.")
    _do_activity(world, hero, activity, narrate=True)
    world.say(f"The crowd gasped when the verse leapt high and the air filled with {activity.keyword}.")
    hero.memes["sharing"] = 1

    world.para()
    gear = compatible_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable compromise exists for this story.")
    safe = world.add(Entity(id=gear.id, type="gear", label=gear.label, owner=hero.id, plural=gear.plural))
    safe.worn_by = hero.id
    if predict_risk(world, hero, activity, prize.id)["tarnished"]:
        del world.entities[safe.id]
        raise StoryError("The suggested gear did not actually protect the prize.")

    world.say(f"Then {parent.label} smiled and said, \"How about we {gear.prep}?\"")
    world.say(f"{hero.id} blinked, grinned, and said the whole line twice, once for pride and once for peace.")
    world.say(f"They {gear.tail}, and soon {hero.id} was {activity.gerund} while {prize.label} stayed bright.")
    world.say(f"The dean laughed so hard the chalk dust jumped off the tables like barn cats at noon.")

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=sett,
        resolved=True,
        conflict=True,
        predicted_tarnish=True,
    )
    return world


SETTINGS = {
    "commons": Setting(place="the college commons", affords={"rhyme_duel", "chalk_circle", "echo_clap"}),
    "quad": Setting(place="the windy college quad", affords={"rhyme_duel", "chalk_circle"}),
    "library_steps": Setting(place="the library steps", affords={"echo_clap", "chalk_circle"}),
}

ACTIVITIES = {
    "rhyme_duel": Activity(
        id="rhyme_duel",
        verb="enter the rhyme duel",
        gerund="rhyme-dueling",
        rush="dash into the rhyme duel",
        mess="rhyme-ink",
        zone={"torso", "hands"},
        keyword="rhyme",
        tags={"rhyme", "sharing"},
    ),
    "chalk_circle": Activity(
        id="chalk_circle",
        verb="draw a chalk circle of lines",
        gerund="drawing chalk circles",
        rush="race to the chalk circle",
        mess="chalk-dust",
        zone={"hands", "torso"},
        keyword="chalk",
        tags={"rhyme", "cognitive"},
    ),
    "echo_clap": Activity(
        id="echo_clap",
        verb="clap out a brainy beat",
        gerund="clapping out beats",
        rush="rush to the echo game",
        mess="brain-buzz",
        zone={"hands", "torso"},
        keyword="echo",
        tags={"sharing", "cognitive"},
    ),
}

PRIZES = {
    "vest": Prize(label="vest", phrase="a bright varsity vest", type="vest", region="torso"),
    "cap": Prize(label="cap", phrase="a tidy college cap", type="cap", region="torso"),
    "scarf": Prize(label="scarf", phrase="a fine blue scarf", type="scarf", region="torso", genders={"girl"}),
}

GEAR = [
    Gear(id="smock", label="a wide paint smock", covers={"torso"}, guards={"chalk-dust", "rhyme-ink"}, prep="put on a wide paint smock first", tail="went to fetch the smock"),
    Gear(id="gloves", label="thinking gloves", covers={"hands"}, guards={"brain-buzz", "chalk-dust"}, prep="slip on the thinking gloves", tail="snapped on the thinking gloves"),
]

NAMES_GIRL = ["Mira", "Nora", "Ada", "Tess", "Luna"]
NAMES_BOY = ["Alden", "Rowan", "Miles", "Eli", "Theo"]
TRAITS = ["clever", "curious", "spirited", "bold", "bright"]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if reasonability_gate(act, prize) and compatible_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale college rhyme-sharing storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["dean", "professor"])
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
        if not (reasonability_gate(act, pr) and compatible_gear(act, pr)):
            raise StoryError("That activity and prize do not make a believable tall-tale problem.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("That prize is not a natural fit for the chosen gender in this storyworld.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["dean", "professor"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a tall-tale story for a young child about a {hero.type} named {hero.id} at {world.setting.place} and the word "{act.keyword}".',
        f"Tell a funny college story where {hero.id} wants to {act.verb} but worries about {hero.pronoun('possessive')} {prize.label}, then finds a kinder way.",
        f'Write a rhyme-sharing adventure with a cognitive twist, using the word "{act.keyword}" and ending in a cheerful compromise.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who was the story about at {world.setting.place}?",
            answer=f"It was about {hero.id}, a {hero.type} who loved rhyme, sharing, and clever thinking at {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do before {parent.label} gave advice?",
            answer=f"{hero.id} wanted to {act.verb}, but that could smear {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"What helped {hero.id} keep {prize.label} safe?",
            answer=f"{gear.label} helped, because it covered the right part and kept the mess away from the prize.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} {act.gerund} and smiling, while the {prize.label} stayed bright and the grown-up laughed nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is college?",
            answer="College is a place where older students learn new things, practice big ideas, and grow their skills.",
        ),
        QAItem(
            question="What does cognitive mean?",
            answer="Cognitive means using the brain to think, remember, notice, and solve problems.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use, hear, or enjoy something together with you.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
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
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
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
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_params() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid/3.")), "valid"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="commons", activity="rhyme_duel", prize="vest", name="Mira", gender="girl", parent="dean", trait="bright"),
    StoryParams(place="quad", activity="chalk_circle", prize="cap", name="Alden", gender="boy", parent="professor", trait="curious"),
    StoryParams(place="library_steps", activity="echo_clap", prize="vest", name="Nora", gender="girl", parent="dean", trait="spirited"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not reasonability_gate(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.label}.)"
    return f"(No story: no gear in this world protects the {prize.label} from {activity.keyword}.)"


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
        import asp
        combos = valid_story_params()
        print(f"{len(combos)} compatible stories:")
        for item in combos:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.activity} at {p.place} ({p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
