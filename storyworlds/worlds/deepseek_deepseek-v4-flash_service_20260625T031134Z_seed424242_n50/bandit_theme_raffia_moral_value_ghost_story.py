#!/usr/bin/env python3
"""
storyworlds/worlds/bandit_theme_raffia_moral_value_ghost_story.py
==================================================================

A standalone story world for a ghost story about a bandit who steals raffia,
and a moral value about sharing or honesty that leads to a haunting resolution.
"""

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
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"torn", "stolen", "soiled"}
REGIONS = {"hands", "back", "home"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "bandit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandmother": "grandma"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the village"
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_theft_guilt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["stolen"] < THRESHOLD:
            continue
        sig = ("guilt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["guilt"] += 1
        out.append(f"{actor.pronoun('possessive').capitalize()} heart felt heavy with guilt.")
    return out


def _r_ghost_haunt(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["guilt"] < THRESHOLD:
            continue
        sig = ("haunt", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append("A ghostly whisper filled the air, reminding everyone of the stolen raffia.")
    return out


def _r_restoration(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["returned"] < THRESHOLD:
            continue
        sig = ("resolve", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["guilt"] = 0.0
        actor.memes["fear"] = 0.0
        actor.memes["peace"] += 1
        out.append("The ghost smiled and faded away as the raffia was returned.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="theft_guilt", tag="moral", apply=_r_theft_guilt),
    Rule(name="ghost_haunt", tag="supernatural", apply=_r_ghost_haunt),
    Rule(name="restoration", tag="moral", apply=_r_restoration),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "weaving": "the golden fibers made the basket grow like a secret",
        "sharing": "the raffia felt warm and soft in small hands",
    }.get(activity.id, "it felt like a game of whispers")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the raffia waited in a bundle."
    return f"{setting.place.capitalize()} lay under a pale moon, and shadows danced like fingers."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who lived at the edge of {world.setting.place}.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} {where}; "
        f"{activity_delight(activity)}."
    )


def steals(world: World, bandit: Entity, hero: Entity, prize: Entity) -> None:
    bandit.meters["stolen"] += 1
    prize.owner = bandit.id
    world.say(
        f"One night, a shadow crept through the door. A bandit with a ragged coat "
        f"took the {prize.label} and slipped away into the dark."
    )


def ghost_appears(world: World, hero: Entity, prize: Entity, ancestor: Entity) -> None:
    ancestor.memes["ghost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That night, a soft glow appeared at the foot of {hero.id}'s bed. "
        f"It was the ghost of {ancestor.label}, the one who had woven the {prize.label} "
        f"long ago."
    )
    world.say(
        f'"The raffia is gone," the ghost whispered. "The bandit took what was never his. "
        f"You must bring it back, or the village will never know peace."'
    )


def bandit_choice(world: World, bandit: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    bandit.memes["guilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} found the bandit in a hollow tree, tangled in the {prize.label}. "
        f"The bandit looked scared. A cold wind blew, and a voice from the dark said, "
        f'"Give back the raffia. Honesty is the only way to break the curse."'
    )


def return_prize(world: World, bandit: Entity, hero: Entity, prize: Entity, ancestor: Entity) -> None:
    bandit.memes["returned"] += 1
    prize.owner = hero.id
    propagate(world, narrate=True)
    world.say(
        f"The bandit trembled and handed the {prize.label} back to {hero.id}. "
        f"\"I'm sorry,\" he said. \"The raffia was never mine.\""
    )
    world.say(
        f"The ghost smiled, and the chill left the air. {hero.id} carried the "
        f"{prize.label} home, and the village felt safe again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Maya", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "grandmother") -> World:
    world = World(setting)
    world.weather = "haunted"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "kind"]),
    ))
    ancestor = world.add(Entity(
        id="Ancestor", kind="character", type="grandmother", label="Grandma Lily",
    ))
    bandit = world.add(Entity(
        id="Bandit", kind="character", type="bandit", label="the bandit",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=ancestor.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    world.say(f"{ancestor.label} had woven a beautiful {prize.label} from raffia, and everyone loved it.")
    loves_activity(world, hero, activity)

    world.para()
    steals(world, bandit, hero, prize)
    ghost_appears(world, hero, prize, ancestor)

    world.para()
    bandit_choice(world, bandit, hero, prize, activity)
    return_prize(world, bandit, hero, prize, ancestor)

    world.facts.update(hero=hero, ancestor=ancestor, bandit=bandit, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=None,
                       conflict=True, resolved=True)
    return world


SETTINGS = {
    "village": Setting(place="the village", indoor=False, affords={"weaving", "sharing"}),
    "cottage": Setting(place="the cottage", indoor=True, affords={"weaving"}),
}

ACTIVITIES = {
    "weaving": Activity(
        id="weaving",
        verb="weave the raffia",
        gerund="weaving raffia baskets",
        rush="grab the raffia fibers",
        mess="torn",
        soil="tangled and torn",
        zone={"hands"},
        weather="",
        keyword="raffia",
        tags={"raffia", "weave"},
    ),
    "sharing": Activity(
        id="sharing",
        verb="share the raffia",
        gerund="sharing raffia with friends",
        rush="run to share the raffia",
        mess="stolen",
        soil="gone",
        zone={"home"},
        weather="",
        keyword="sharing",
        tags={"sharing", "honesty"},
    ),
}

GEAR = [
    Gear(
        id="basket",
        label="a small basket",
        covers={"hands"},
        guards={"torn"},
        prep="use a small basket to carry the raffia",
        tail="fetched the small basket",
    ),
]

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a beautiful raffia basket",
        type="basket",
        region="hands",
    ),
    "doll": Prize(
        label="doll",
        phrase="a soft raffia doll",
        type="doll",
        region="hands",
    ),
}

GIRL_NAMES = ["Maya", "Lila", "Nina", "Zara", "Aria"]
BOY_NAMES = ["Kai", "Noah", "Eli", "Theo", "Luca"]
TRAITS = ["brave", "kind", "curious", "gentle", "wise"]


def valid_combos() -> list[tuple[str, str]]:
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
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "raffia": [("What is raffia?",
                "Raffia is a soft fiber from palm leaves, used to weave baskets and toys.")],
    "ghost": [("What is a ghost in stories?",
               "A ghost is the spirit of someone who has passed, often appearing to teach a lesson.")],
    "bandit": [("What is a bandit?",
                "A bandit is a person who steals things that do not belong to them.")],
    "honesty": [("Why is honesty important?",
                 "Honesty means telling the truth and not taking what is not yours; it keeps friendships strong.")],
    "sharing": [("What does sharing mean?",
                 "Sharing means letting others use or enjoy something you have, which makes everyone happy.")],
}
KNOWLEDGE_ORDER = ["raffia", "ghost", "bandit", "honesty", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, ancestor, act, prize = f["hero"], f["ancestor"], f["activity"], f["prize_cfg"]
    return [
        f'Write a ghost story for a child about a {hero.type} named {hero.id} '
        f'who learns about honesty through a stolen raffia {prize.label}.',
        f'A bandit steals a raffia {prize.label} from a village. Tell how a ghost '
        f'helps bring it back.',
        f'A story about a {hero.type} who loves {act.gerund} and must find the moral value of sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ancestor, bandit, prize, act = f["hero"], f["ancestor"], f["bandit"], f["prize"], f["activity"]
    pw = ancestor.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} lives in {world.setting.place}?"
            ),
            answer=(
                f"The story is about a little {hero.traits[1]} {hero.type} named {hero.id} "
                f"and {pos} {pw}. A bandit steals a raffia {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did the bandit take from {hero.id}'s home?"
            ),
            answer=(
                f"The bandit stole the raffia {prize.label} that {pw} {ancestor.label} had woven. "
                f"The raffia was special because it was made by hand."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"How did {hero.id} help the ghost find peace?"
            ),
            answer=(
                f"{sub.capitalize()} found the bandit and convinced {bandit.pronoun('object')} to "
                f"return the raffia {prize.label}. The ghost smiled when the raffia was given back."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What moral value did the ghost teach {hero.id}?"
            ),
            answer=(
                f"The ghost taught that honesty and sharing are important. "
                f"Taking what is not yours brings sadness, but returning it brings peace."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="village",
        activity="weaving",
        prize="basket",
        name="Maya",
        gender="girl",
        parent="grandmother",
        trait="brave",
    ),
    StoryParams(
        place="cottage",
        activity="sharing",
        prize="doll",
        name="Kai",
        gender="boy",
        parent="grandmother",
        trait="kind",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    return (f"(No story: the ghost story theme requires the raffia prize to be at risk "
            f"from {activity.gerund}. Try a prize on {sorted(activity.zone)}.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't typical for {gender}; try --gender {ok}.)")


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
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
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
    ap = argparse.ArgumentParser(
        description="Ghost story about a bandit, raffia, and a moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother"])
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

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "brave"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
