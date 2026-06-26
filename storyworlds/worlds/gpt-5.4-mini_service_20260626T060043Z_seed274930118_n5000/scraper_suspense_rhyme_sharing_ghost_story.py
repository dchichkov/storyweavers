#!/usr/bin/env python3
"""
A small ghost-story world with a scraper, suspense, rhyme, and sharing.

The seed idea:
- A child hears a soft scrape in an old house at night.
- A ghost wants to clean a moon-fogged window with a scraper.
- The scraping feels spooky, but the child and ghost share the tool and work together.
- A little rhyme helps them be brave until the window shines.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


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
    weather: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        return any(region in g.region for g in self.worn_items(actor) if g.label == "blanket")

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
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: callable


def _r_scrape(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("scrape", 0.0) < THRESHOLD:
            continue
        for prize in [e for e in world.entities.values() if e.id == "prize"]:
            if prize.region not in world.zone:
                continue
            sig = ("scrape", actor.id, prize.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
            prize.meters["scratched"] = prize.meters.get("scratched", 0.0) + 1
            out.append(f"The {prize.label} got scratched and dusty.")
    return out


def _r_owl_silence(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("suspense", 0) >= 1 and ("owl",) not in world.fired:
        world.fired.add(("owl",))
        out.append("An owl hooted in the dark, and the room went very still.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    child = world.entities.get("child")
    tool = world.entities.get("scraper")
    if not ghost or not child or not tool:
        return out
    if world.facts.get("shared", False) and tool.worn_by in {"ghost", "child"}:
        sig = ("sharing",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1
        child.memes["brave"] = child.memes.get("brave", 0.0) + 1
        out.append("They shared the scraper, and the spooky feeling became smaller.")
    return out


CAUSAL_RULES = [
    Rule("scrape", "physical", _r_scrape),
    Rule("owl", "mood", _r_owl_silence),
    Rule("sharing", "social", _r_sharing),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters[activity.mess] = sim.get(actor.id).meters.get(activity.mess, 0.0) + 1
    sim.zone = set(activity.zone)
    prize = sim.get(prize_id)
    prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    prize.meters["scratched"] = prize.meters.get("scratched", 0.0) + 1
    return {"ruined": prize.meters["scratched"] >= THRESHOLD}


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} who liked brave stories but still liked a warm lamp best.")


def setting_detail(setting: Setting) -> str:
    if setting.place == "the old house":
        return "The old house had loose boards, dim corners, and one tall window that glimmered like a sleepy eye."
    return f"{setting.place.capitalize()} was quiet and waiting for night-time whispers."


def loves_activity(world: World, child: Entity, activity: Activity) -> None:
    world.say(f"{child.pronoun().capitalize()} loved {activity.gerund}, because every tiny sound seemed to hold a secret.")


def warn(world: World, ghost: Entity, child: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, child, activity, prize.id)
    if pred["ruined"]:
        world.facts["suspense"] = 1
        world.say(f'"Careful," {ghost.pronoun("subject")} whispered, "that {prize.label} can get scratched if we scrape too fast."')


def rhyme_line() -> str:
    return "Scrape with care, share with me, and let the moonlight set us free."


def invite_sharing(world: World, ghost: Entity, child: Entity) -> None:
    world.facts["shared"] = True
    world.say(f"{ghost.id} nudged the scraper toward {child.id} and said, \"You hold one side, I hold the other.\"")
    world.say(f"They murmured a rhyme to stay calm: “{rhyme_line()}”")


def resolve(world: World, ghost: Entity, child: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    child.memes["brave"] = child.memes.get("brave", 0.0) + 1
    ghost.memes["trust"] = ghost.memes.get("trust", 0.0) + 1
    prize.meters["dirty"] = 0.0
    prize.meters["scratched"] = 0.0
    world.say(
        f"At last, {child.id} and {ghost.id} used the {gear.label} the gentle way, and the {prize.label} shone clean again."
    )
    world.say(
        f"The soft moon came through the glass, and the house did not feel scary anymore."
    )


SETTINGS = {
    "old_house": Setting(place="the old house", indoor=True, affords={"scrape"}),
    "attic": Setting(place="the attic", indoor=True, affords={"scrape"}),
}

ACTIVITIES = {
    "scrape": Activity(
        id="scrape",
        verb="scrape the window clean",
        gerund="scraping the window clean",
        rush="scrape too fast",
        mess="scrape",
        soil="scratched",
        zone={"window"},
        weather="night",
        keyword="scraper",
        tags={"scraper", "window", "suspense", "rhyme", "sharing", "ghost"},
    )
}

PRIZES = {
    "window": Prize(
        label="window",
        phrase="a tall old window",
        type="window",
        region="window",
    )
}

GEAR = [
    Gear(
        id="soft_scraper",
        label="soft scraper",
        covers={"window"},
        guards={"scrape"},
        prep="share the soft scraper",
        tail="worked side by side until the glass gleamed",
    )
]

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy"]
BOY_NAMES = ["Theo", "Eli", "Finn", "Owen"]
TRAITS = ["curious", "quiet", "brave", "gentle"]


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
    return [("old_house", "scrape", "window"), ("attic", "scrape", "window")]


KNOWLEDGE = {
    "scraper": [("What is a scraper?", "A scraper is a tool with a flat edge that can lift off stuck bits from a surface.")],
    "window": [("What does a window do?", "A window lets in light and lets people look outside.")],
    "ghost": [("What is a ghost in a story?", "A ghost in a story is a spooky-looking character who may be friendly, lonely, or mysterious.")],
    "sharing": [("Why is sharing kind?", "Sharing is kind because it lets two people use something together and helps them both.")],
    "rhyme": [("What is a rhyme?", "A rhyme is a pair of words or lines that sound alike at the end.")],
    "suspense": [("What is suspense?", "Suspense is the feeling of wondering what will happen next.")],
}


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), covers(G, R), worn_on(P, R), guards(G, M), splashes(A, R), activity(A).
valid(Place, A, P) :- setting(Place), activity(A), prize(P), prize_at_risk(A, P), protects(_, A, P).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with suspense, rhyme, and sharing.")
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
        if (args.place or "old_house", args.activity, args.prize) not in valid_combos():
            raise StoryError("That combination does not make a good ghost-story scene.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid story matches the given options.")
    place, activity, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="child", kind="character", type=hero_type, traits=hero_traits))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", traits=["soft", "spooky"]))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=hero.id))
    scraper = world.add(Entity(id="scraper", type="tool", label="scraper", phrase="a little scraper"))
    scraper.worn_by = None
    world.weather = activity.weather

    introduce(world, hero)
    loves_activity(world, hero, activity)
    world.say(setting_detail(setting))
    world.para()
    world.say(f"That night, {hero_name} and the ghost stood beneath the {prize.label}.")
    warn(world, ghost, hero, activity, prize)
    world.say(f"{hero_name} listened, and the room felt full of suspense.")
    world.para()
    invite_sharing(world, ghost, hero)
    scraper.worn_by = ghost.id
    hero.meters["scrape"] = 1.0
    world.zone = set(activity.zone)
    propagate(world, narrate=True)
    world.para()
    resolve(world, ghost, hero, activity, prize, GEAR[0])
    world.facts.update(hero=hero, ghost=ghost, prize=prize, activity=activity, setting=setting, gear=GEAR[0])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a gentle ghost story about a child and a friendly ghost who share a scraper.',
        f"Tell a suspenseful bedtime story where {hero.id} learns a rhyme before cleaning an old window.",
        "Write a short story with a spooky room, a shared tool, and a happy ending in moonlight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ghost, prize, act = f["hero"], f["ghost"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What were {hero.id} and the ghost trying to do with the scraper?",
            answer=f"They were trying to {act.verb} so the {prize.label} would shine again.",
        ),
        QAItem(
            question=f"Why did the scene feel suspenseful before they shared the scraper?",
            answer="It felt suspenseful because the old house was dark, an owl hooted, and everyone worried the window might get scratched.",
        ),
        QAItem(
            question="What rhyme did they say to feel brave?",
            answer=rhyme_line(),
        ),
        QAItem(
            question=f"How did sharing help {hero.id} and the ghost?",
            answer="Sharing helped because they each held part of the scraper and worked together carefully.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_valid_combos() -> list[tuple]:
    return valid_combos()


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="old_house", activity="scrape", prize="window", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="attic", activity="scrape", prize="window", name="Theo", gender="boy", parent="father", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
