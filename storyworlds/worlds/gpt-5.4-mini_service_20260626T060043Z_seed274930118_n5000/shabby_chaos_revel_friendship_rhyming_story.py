#!/usr/bin/env python3
"""
storyworlds/worlds/shabby_chaos_revel_friendship_rhyming_story.py
=================================================================

A small rhyming storyworld about shabby spaces, a touch of chaos, and a bright
revel saved by friendship.

Seed tale:
---
Two little friends, Pip and Nia, found an old shabby shed behind a garden gate.
It was full of dusty boxes, a wobbly table, and a torn red ribbon. Pip wanted to
hold a tiny revel there anyway, because friends could make almost any place feel
sparkly. But when the wind blew in, the ribbons tangled, the lantern toppled,
and chaos made the room feel much less merry.

Nia did not laugh at the mess. She fetched a broom, straightened the table, and
helped Pip hang the lantern up high. Together they swept the floor, patched the
banner, and turned the shabby shed into a cheerful corner for a little revel.
Soon the friends were smiling, the lantern glowed, and the night felt warm and
bright again.

Narrative instruments:
---
- shabby -> worn, dusty, patched, needing care
- chaos  -> a sudden mess that can topple, tangle, or scatter decorations
- revel  -> a small, happy celebration with music, snacks, and dancing
- friendship -> the helper bond that turns trouble into shared joy

This script keeps the story child-facing, concrete, and state-driven, with
rhyming lines and a simple simulated world model.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"shabby": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0}

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
    chaos: str
    tidy_fix: str
    zone: set[str]
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
        return any(region in g.covers for g in self.worn_items(actor))

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_chaos(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("chaos", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind == "character":
                continue
            if item.worn_by == actor.id or item.region not in world.zone:
                continue
            if item.meters.get("shabby", 0.0) >= THRESHOLD:
                continue
            sig = ("chaos", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["shabby"] = item.meters.get("shabby", 0.0) + 1
            item.memes["stressed"] = item.memes.get("stressed", 0.0) + 1
            out.append(f"The {item.label} got bumped in the whirl of chaos.")
    return out


def _r_friction(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("shabby", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("fix", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get(item.caretaker)
        helper.memes["care"] = helper.memes.get("care", 0.0) + 1
        out.append(f"That made more work for {helper.label}.")
    return out


def _r_friendship(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("asked_help", 0.0) < THRESHOLD or actor.memes.get("kind_help", 0.0) < THRESHOLD:
            continue
        sig = ("friendship", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
        actor.memes["friendship"] = actor.memes.get("friendship", 0.0) + 1
        out.append(f"Friendship made the air feel light again.")
    return out


CAUSAL_RULES = [
    Rule("chaos", "physical", _r_chaos),
    Rule("friction", "physical", _r_friction),
    Rule("friendship", "social", _r_friendship),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.chaos in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"shabby": bool(prize and prize.meters.get("shabby", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["chaos"] = actor.meters.get("chaos", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, friend: Entity) -> None:
    mood = "shabby but sweet"
    world.say(
        f"{hero.id} and {friend.id} were two small friends, bright and neat, "
        f"who found a {mood} place to meet."
    )


def setting_line(world: World, act: Activity) -> None:
    if world.setting.indoor:
        world.say(f"In {world.setting.place}, the lanterns glowed, and the floor was ready to go.")
    else:
        world.say(f"At {world.setting.place}, the breeze was mild, and the night felt soft and wild.")
    world.say(f"They planned a little revel, with rhythm, ribbons, and a playful level.")


def wants_revel(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {act.verb}, and make the evening sweet and clever.")


def warning(world: World, friend: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, act, prize.id)
    if not pred["shabby"]:
        return False
    world.facts["predicted_shabby"] = True
    world.say(
        f'"If we rush to the revel now," {friend.id} said with a careful grin, '
        f'"the {prize.label} may get shabby from the wind and spin."'
    )
    return True


def chaos_spike(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["asked_help"] = hero.memes.get("asked_help", 0.0) + 1
    world.say(f"But a gust came quick, a twisty trick, and the room turned toppy-tumbly fast.")
    world.say(f"{hero.id} tried to {act.rush}, and the ribbons flew past.")


def friend_help(world: World, friend: Entity, hero: Entity, act: Activity, prize: Entity) -> Optional[Gear]:
    gear = select_gear(act, prize)
    if gear is None:
        return None
    helper = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=friend.id,
        worn_by=hero.id,
        plural=gear.plural,
    ))
    if predict(world, hero, act, prize.id)["shabby"]:
        del world.entities[helper.id]
        return None
    friend.memes["kind_help"] = friend.memes.get("kind_help", 0.0) + 1
    world.say(
        f"{friend.id} fetched {gear.label} with a hop and a pop, "
        f"then said, \"Let's make this little revel stop the flop.\""
    )
    return gear


def resolve(world: World, hero: Entity, friend: Entity, act: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1
    hero.memes["asked_help"] = 0.0
    world.say(
        f"{hero.id} smiled, then held {hero.pronoun('possessive')} friend's hand, "
        f"and together they made the plan look grand."
    )
    world.say(
        f"They used {gear.label} and joined the tune; soon the {prize.label} shone bright as the moon."
    )
    world.say(
        f"So the shabby room grew merry and smart, and the revel warmed every heart."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pip", friend_name: str = "Nia",
         hero_type: str = "boy", friend_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0

    intro(world, hero, friend)
    setting_line(world, activity)
    wants_revel(world, hero, activity)
    warning(world, friend, hero, activity, prize)
    world.para()
    chaos_spike(world, hero, activity)
    gear = friend_help(world, friend, hero, activity, prize)
    if gear:
        resolve(world, hero, friend, activity, prize, gear)
    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, setting=setting, gear=gear)
    return world


SETTINGS = {
    "shed": Setting(place="the shabby shed", indoor=True, affords={"revel", "dance"}),
    "hall": Setting(place="the little hall", indoor=True, affords={"revel", "dance"}),
    "garden": Setting(place="the garden nook", indoor=False, affords={"revel", "picnic"}),
}

ACTIVITIES = {
    "revel": Activity(
        id="revel",
        verb="host a little revel",
        gerund="dancing in a revel",
        rush="twirl toward the ribbons",
        chaos="tangle",
        tidy_fix="straighten the streamers",
        zone={"torso"},
        keyword="revel",
        tags={"revel", "friendship"},
    ),
    "dance": Activity(
        id="dance",
        verb="dance in a swirl",
        gerund="dancing in a swirl",
        rush="spin toward the music",
        chaos="scatter",
        tidy_fix="sweep the floor",
        zone={"torso"},
        keyword="dance",
        tags={"dance", "friendship"},
    ),
    "picnic": Activity(
        id="picnic",
        verb="share a picnic",
        gerund="sharing a picnic",
        rush="dash toward the blanket",
        chaos="spill",
        tidy_fix="wipe the crumbs",
        zone={"torso"},
        keyword="picnic",
        tags={"picnic", "friendship"},
    ),
}

PRIZES = {
    "banner": Prize("banner", "a bright paper banner", "banner", "torso"),
    "lantern": Prize("lantern", "a little lantern", "lantern", "torso"),
    "tablecloth": Prize("tablecloth", "a striped tablecloth", "tablecloth", "torso"),
}

GEAR = [
    Gear("hooks", "two strong hooks", {"torso"}, {"tangle", "scatter"}, "hang the ribbons high", "hung the ribbons high", plural=True),
    Gear("cloth", "a clean cloth", {"torso"}, {"spill", "tangle"}, "cover the table", "covered the table", plural=False),
    Gear("broom", "a tiny broom", {"torso"}, {"scatter", "spill", "tangle"}, "sweep the floor first", "swept the floor first"),
]

GIRL_NAMES = ["Nia", "Mina", "Luna", "Tess", "Rosa"]
BOY_NAMES = ["Pip", "Bo", "Finn", "Max", "Jai"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "revel": [("What is a revel?", "A revel is a joyful celebration with dancing, music, and happy fun.")],
    "shabby": [("What does shabby mean?", "Shabby means worn, old, or a little messy and in need of care.")],
    "chaos": [("What is chaos?", "Chaos is a big jumble where things get mixed up and hard to control.")],
    "friendship": [("What is friendship?", "Friendship is the warm bond between people who care for each other and help each other.")],
    "lantern": [("What does a lantern do?", "A lantern gives off light so people can see in the dark.")],
    "banner": [("What is a banner?", "A banner is a long sign or decoration that can hang up at a party.")],
}
KNOWLEDGE_ORDER = ["revel", "shabby", "chaos", "friendship", "lantern", "banner"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child about {f["hero"].id} and {f["friend"].id}, '
        f"a shabby place, and a tiny {f['activity'].keyword}.",
        f"Tell a gentle story where friendship turns chaos into a happy revel.",
        f"Write a simple rhyming tale that includes the words shabby, chaos, and revel.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {hero.id} and {friend.id}, two friends who wanted to share a happy time together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {act.verb} there and make the evening feel like a little revel.",
        ),
        QAItem(
            question=f"What was a little shabby in the story?",
            answer=f"The {prize.label} and the place were a bit shabby at first, so the friends had to care for them.",
        ),
        QAItem(
            question=f"How did the friends fix the chaos?",
            answer=f"They worked together, used {f['gear'].label if f.get('gear') else 'helpful tools'}, and turned the mess into a neat, merry scene.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("friendship")
    if world.facts.get("gear"):
        tags.update({"lantern", "banner"})
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("shed", "revel", "banner", "Pip", "Nia", "boy", "girl"),
    StoryParams("hall", "dance", "lantern", "Milo", "Rae", "boy", "girl"),
    StoryParams("garden", "picnic", "tablecloth", "Luna", "Bo", "girl", "boy"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.label}, so there is no honest worry to solve.)"
    return f"(No story: no gear in this world safely covers the {prize.label} from {activity.chaos}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("chaos_of", aid, a.chaos))
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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), chaos_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world about shabby chaos and revel friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend-type", choices=["boy", "girl"])
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
    combos = valid_combos()
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in combos if (args.place is None or c[0] == args.place) and (args.activity is None or c[1] == args.activity) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    friend_type = args.friend_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.name or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_type == "girl" else BOY_NAMES)
    return StoryParams(place, activity, prize, hero_name, friend_name, hero_type, friend_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.hero_name, params.friend_name, params.hero_type, params.friend_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(row)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
